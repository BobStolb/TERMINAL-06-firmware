#!/usr/bin/env python3
"""TS06-DRV placement search: let an optimiser propose the layout, then route the best candidates.

    python3 tools/placesearch.py --baseline                  # score tools/mkpcb_drv.py's placement
    python3 tools/placesearch.py --runs 8 --iters 60000      # anneal 8 restarts on every CPU
    python3 tools/placesearch.py --show cand.json            # score one saved candidate, draw it

WHAT IT MOVES. The driver board is split into RIGID BLOCKS, each a small fixed arrangement of parts
(the converter's power loop, its control block, the power inlet, the Nano, each decoder with its
decoupling capacitor, the expander stacked on its LED network, one cell per anode channel, the RTC
with its pull-ups, J1 with the fascia filters, the two MPSA42 switches, and a few loose parts). A
block may translate, turn in 90 degree steps and "mirror" (its parts' positions reflected, each
part turned to the reflected orientation - an alternative internal arrangement, never a mirrored
footprint, which through-hole parts do not have). The strips, the display standoffs, the corner
holes and the outline are fixed. Three firmware-only remaps ride along as moves too: which Nano pin
drives which anode channel, which RN1 element / port-B bit feeds which LED, and which port-A nibble
feeds which ИН-15 decoder.

WHAT IT PRICES. Wirelength alone does not say whether a two-layer board routes with ZERO vias: on a
through-hole board a net may change face only at one of its own pads, so every place two nets must
cross is paid for somewhere. The cost is, per candidate:
  * mst       the sum over nets of the Euclidean MST (GND at 0.3: it is poured);
  * cross     each crossing between two different nets' MST edges, a heavy price, discounted to a
              third within 3 mm of a pad of either net (a face change is available there);
  * frustr    the crossings a greedy two-colouring of the MST edges cannot put on opposite faces:
              two crossing edges on different faces cost nothing, but an odd cycle of crossings
              has no zero-via solution without a detour through a pad - the heavier price;
  * padhit    MST edges running over another net's pad (blocked on BOTH faces: a detour);
  * hv        185 V pads within 4 mm of 5 V logic pads of another block;
  * edge      the Nano's USB and the 12 V jack mouth at a board edge (USB may stand 2.4 mm proud);
  * overlap   courtyard overlap per face, courtyards outside the board, parts on the strips, the
              standoffs, the corner holes, and J1 (back face) under the display board.
The same function scores the baseline (tools/mkpcb_drv.py, imported, its own remaps) so the numbers
are calibrated against a board known to route: --baseline prints its breakdown.

HOW IT SEARCHES. Simulated annealing over block poses and the remaps (translate with a step that
shrinks with the temperature, turn, mirror, swap two blocks of the same kind, swap two remap
entries), several random restarts in parallel (multiprocessing, one per CPU). Only the nets that
touch a moved block get their MST recomputed; the crossing tests are numpy over all edges.

OUTPUT. Each restart writes PCB/TS06-DRV-search/cands/cand_<seed>.json (every part's pose, the
remaps, the cost breakdown) and a placement PNG; tools/mkpcb_drv_search.py --cand <file> builds and
routes one. It does not route anything itself: the cost is a prediction, and the router's struggle
on the chosen candidates is the test of it (PCB/TS06-DRV-search/REPORT.md).
"""
import json, math, os, random, sys, time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbkit as K
import ts06pair as P

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUTDIR = os.path.join(ROOT, "PCB", "TS06-DRV-search", "cands")
W, H, Y0, DW = 176.0, 100.0, 26.0, 176.0
DISP_BOTTOM = Y0 + 44.0                     # the display board's lower edge, DRV frame
PT = P.parts(P.DRV)
R_V = "TS06_R_Axial_DIN0207_P2.54mm_Vertical"

# ------------------------------------------------------------------ weights (mm-equivalent)
WT = dict(mst=1.0, gnd=0.3, cross=6.0, cross_near=2.0, frustr=25.0, padhit=3.0, hv=6.0, edge=40.0, overlap=40.0)
FRUSTR_ALL = os.environ.get("FRUSTR_ALL", "1") == "1"
HV_NETS = None                               # filled from the board's classes below

# ------------------------------------------------------------------ fixed things
DISP_STRIP = {"11": (1.6, 4.4, True), "12": (99.57, 2.2, False), "21": (11.94, 41.3, False),
              "22": (47.99, 41.3, False), "23": (69.28, 41.3, False), "24": (107.335, 41.3, False),
              "25": (139.15, 41.3, False)}
DISP_HOLES = [(172.5, 40.5), (3.5, 40.5), (DW - 50.535, 3.3), (3.5, 7.5)]
CORNER_HOLES = [(3.5, 3.5), (172.5, 3.5), (3.5, 96.5), (172.5, 96.5)]


def fixed_parts():
    """[(ref, fp, x, y, rot, back)] in the DRV frame: the strips and the display standoffs."""
    out = []
    for k, (x, y, vert) in DISP_STRIP.items():
        out.append((f"XS{k}", PT[f"XS{k}"].fp, DW - x, y + Y0, 0 if vert else 90, True))
    return out


def fixed_holes():
    return [(x, y + Y0) for x, y in DISP_HOLES]


# ------------------------------------------------------------------ the blocks
# Each block: name, [(ref, dx, dy, rot, back)], optional flags. The arrangements of the converter,
# the power inlet, the control block and U3 + RN1 are the baseline's own (tools/mkpcb_drv.py),
# relative to their first part; the rest are drawn here.
def _rel(parts):
    x0, y0 = parts[0][1], parts[0][2]
    return [(r, round(x - x0, 3), round(y - y0, 3), rot, back) for r, x, y, rot, back in parts]


def cell(u, r470, ranode, rb1, rb2):
    """One anode channel: the opto flat, the standing 470R left of its LED anode, the anode resistor
    lying under it back towards the left, the two standing bleeds under that."""
    return [(u, 0.0, 0.0, 0, False), (r470, -6.1, 0.0, 0, False), (ranode, 7.62, 6.6, 180, False),
            (rb1, -5.08, 10.5, 0, False), (rb2, 1.0, 10.5, 0, False)]


BLOCKS = [
    ("NANO", [("U1", 0, 0, 0, False)]),
    ("PWR", _rel([("XS1", 14.0, 12.5, 0, False), ("F1", 24.0, 2.7, 0, False), ("VD2", 36.24, 9.0, 180, False),
                  ("U14", 21.5, 19.5, 0, False), ("C8", 40.5, 3.8, 0, False), ("C9", 40.09, 8.54, 270, False),
                  ("C10", 36.28, 13.62, 270, False), ("C11", 31.84, 19.89, 90, False)])),
    ("CONV", _rel([("L1", 47.5, 13.5, 0, False), ("VT21", 59.0, 19.0, 0, False), ("VD1", 67.8, 10.0, 180, False),
                   ("C7", 72.5, 6.0, 0, False), ("U11", 81.0, 20.7, 180, False), ("R67", 69.0, 13.6, 180, False),
                   ("R68", 58.1, 6.45, 0, False), ("C12", 84.14, 19.78, 0, False)])),
    ("CTRL", _rel([("U12", 104.0, 18.0, 180, False), ("R62", 96.0, 2.3, 0, False), ("R63", 111.6, 2.3, 270, False),
                   ("R64", 114.5, 12.0, 0, False), ("RP1", 124.5, 18.0, 0, False), ("R69", 84.8, 15.0, 90, False),
                   ("R70", 88.3, 15.0, 90, False), ("R71", 91.8, 15.0, 90, False), ("R65", 114.5, 4.0, 0, False),
                   ("C14", 96.5, 5.7, 0, False), ("C13", 107.44, 16.71, 90, False)])),
    ("U2", [("U2", 0, 0, 0, False), ("C4", 7.62, -3.6, 180, False)]),
    ("U17", [("U17", 0, 0, 0, False), ("C17", 7.62, -3.6, 180, False)]),
    ("U1516", [("U16", 0, 0, 90, False), ("C16", -3.6, -2.6, 90, False),
               ("U15", 25.5, 0, 90, False), ("C15", 21.9, -2.6, 90, False)]),
    ("U3RN", _rel([("U3", 44.5, 86.0, 270, False), ("RN1", 26.72, 82.0, 90, False), ("C1", 23.67, 81.53, 180, False)])),
    ("RTC", [("U13", 0, 0, 0, False), ("R55", 6.84, 5.08, 180, False), ("R54", 6.84, 8.62, 180, False)]),
    ("J1", [("J1", 0, 0, 0, True), ("C5", 4.0, 5.0, 0, False), ("C6", 4.0, 7.5, 0, False)]),
    ("BL", [("VT20", 0, 0, 0, False), ("R20", 2.54, 7.4, 90, False)]),
    ("COL", [("VT1", 0, 0, 0, False), ("R1", 2.54, 7.4, 90, False)]),
    ("COLB", [("R59", 0, 0, 0, False), ("R58", 0, 4.0, 0, False)]),
    ("AMPMR", [("R56", 0, 0, 0, False), ("R57", 0, 4.0, 0, False)]),
    ("BLEED", [("R60", 0, 0, 0, False), ("R61", 15.2, 0, 0, False)]),
    ("C3", [("C3", 0, 0, 0, False)]),
    ("R53", [("R53", 0, 0, 0, False)]),
    ("R66", [("R66", 0, 0, 0, False)]),
]
for i in range(6):
    BLOCKS.append((f"CELL{i}", cell(f"U{5 + i}", f"R{21 + i}", f"R{27 + i}", f"R{33 + 2 * i}", f"R{34 + 2 * i}")))
KIND = {b: ("CELL" if b.startswith("CELL") else b) for b, _ in BLOCKS}

# every opto LED resistor stands (the baseline laid the hours' two): the cells are identical
FP_OVERRIDE = {f"R{21 + i}": R_V for i in range(6)}


def fp_of(ref):
    return FP_OVERRIDE.get(ref, PT[ref].fp)


# ------------------------------------------------------------------ remaps (firmware-only)
TUBES = ["H10", "H1", "M10", "M1", "S10", "S1"]
ANODE_PINS = ["D6", "D5", "D4", "D3", "D2", "D13"]          # the baseline's TUBE_PIN4, tube order
REMAP0 = dict(opto=list(ANODE_PINS), bl=[1, 2, 3, 4, 5, 6, 7, 8], xaswap=False)


def pin_net(ref, pin, remap):
    """The net on ref.pin with the remaps applied."""
    if ref in ("R21", "R22", "R23", "R24", "R25", "R26") and pin == "1":
        return remap["opto"][int(ref[1:]) - 21]
    if ref == "RN1" and int(pin) >= 9:
        k = int(pin) - 9                     # element k: GPBk side is pin 8-k
        return f"BL_A{remap['bl'][k]}"
    n = PT[ref].pins.get(pin)
    if remap["xaswap"] and ref in ("U15", "U16") and n and n.startswith("XA"):
        i = int(n[2:])
        return f"XA{(i + 4) % 8}"
    return n


# ------------------------------------------------------------------ geometry precompute
_FPC = {}


def fpgeo(fp, rot, back):
    key = (fp, rot % 360, back)
    if key not in _FPC:
        f = K.Footprint(fp, rot % 360, back)
        _FPC[key] = ([(p.name, p.x, p.y, p.kind) for p in f.pads], tuple(f.court))
    return _FPC[key]


def _centroid(fp, rot, back):
    pads = [p for p in fpgeo(fp, rot, back)[0] if p[3] != "np_thru_hole"] or [("", 0.0, 0.0, "")]
    return sum(p[1] for p in pads) / len(pads), sum(p[2] for p in pads) / len(pads)


def xform(dx, dy, rot, r, m, fp=None, back=False):
    """A part's (dx, dy, rot) inside a block, after the block's mirror m and turn r. A mirror
    reflects each part's pad centroid (not its origin) and turns the part to the reflected
    orientation, so the parts keep their places and their spacing."""
    if m:
        cx0, cy0 = _centroid(fp, rot, back)
        rot = (180 - rot) % 360
        cx1, cy1 = _centroid(fp, rot, back)
        dx, dy = -(dx + cx0) - cx1, dy + cy0 - cy1
    x, y = K._rot(dx, dy, r)
    return x, y, (rot + r) % 360


def usb_dir(rot):
    return K._rot(0.0, 1.0, rot)             # the Nano's USB end is +y of its footprint at rot 0


def jack_dir(rot):
    return K._rot(-1.0, 0.0, rot)            # the barrel jack's mouth is -x at rot 0


class Model:
    def __init__(self):
        self.board_cls = K.Board("x", W, H, PT, [("HV", 0.6, 0.4, P.HV_PATTERNS)])
        self.blocks = [b for b, _ in BLOCKS]
        self.bparts = {b: ps for b, ps in BLOCKS}
        # variants: per block, per (r, m) -> list of (ref, x, y, rot, back) and pad records
        self.var = {}
        for b, ps in BLOCKS:
            for r in (0, 90, 180, 270):
                for m in (0, 1):
                    parts = []
                    for ref, dx, dy, rot, back in ps:
                        x, y, rr = xform(dx, dy, rot, r, m, fp_of(ref), back)
                        parts.append((ref, x, y, rr, back))
                    self.var[(b, r, m)] = parts
        # the global pad list: fixed pads first, then each block's pads in a fixed order
        self.pad_ref, self.pad_pin, self.pad_blk = [], [], []
        fx, fy = [], []
        for ref, fp, x, y, rot, back in fixed_parts():
            for name, px, py, kind in fpgeo(fp, rot, back)[0]:
                self.pad_ref.append(ref), self.pad_pin.append(name), self.pad_blk.append(-1)
                fx.append(x + px), fy.append(y + py)
        self.nfixed = len(fx)
        self.fixed_xy = np.array([fx, fy]).T
        self.bslice = {}
        for bi, (b, ps) in enumerate(BLOCKS):
            s = len(self.pad_ref)
            for ref, dx, dy, rot, back in ps:
                for name, px, py, kind in fpgeo(fp_of(ref), rot, back)[0]:
                    if kind == "np_thru_hole":
                        continue
                    self.pad_ref.append(ref), self.pad_pin.append(name), self.pad_blk.append(bi)
            self.bslice[b] = (s, len(self.pad_ref))
        self.NP = len(self.pad_ref)
        self.pad_blk = np.array(self.pad_blk)
        refid = {}
        self.pad_part = np.array([refid.setdefault(r, len(refid)) for r in self.pad_ref])
        self.other_part = self.pad_part[:, None] != self.pad_part[None, :]
        # per block variant: pad offsets (in the block's pad order) and courtyards
        self.voff, self.vcourt = {}, {}
        for b, ps in BLOCKS:
            for r in (0, 90, 180, 270):
                for m in (0, 1):
                    offs, courts = [], []
                    for (ref, x, y, rot, back) in self.var[(b, r, m)]:
                        pads, c = fpgeo(fp_of(ref), rot, back)
                        for name, px, py, kind in pads:
                            if kind == "np_thru_hole":
                                continue
                            offs.append((x + px, y + py))
                        courts.append((ref, back, x + c[0], y + c[1], x + c[2], y + c[3]))
                    self.voff[(b, r, m)] = np.array(offs)
                    self.vcourt[(b, r, m)] = courts
        self.fixed_courts = []
        for ref, fp, x, y, rot, back in fixed_parts():
            c = fpgeo(fp, rot, back)[1]
            self.fixed_courts.append((x + c[0], y + c[1], x + c[2], y + c[3]))
        for hx, hy in fixed_holes():
            self.fixed_courts.append((hx - 3.45, hy - 3.45, hx + 3.45, hy + 3.45))
        self.fixed_courts = np.array(self.fixed_courts)

    # -------------------------------------------------------------- nets under a remap
    def nets(self, remap):
        ids, names = [], {}
        for ref, pin in zip(self.pad_ref, self.pad_pin):
            n = pin_net(ref, pin, remap) if ref in PT else None
            if ref.startswith("XS") and ref[2:] in P.HEADERS:
                n = PT[ref].pins.get(pin)
            ids.append(names.setdefault(n, len(names)) if n else -1)
        return np.array(ids), {v: k for k, v in names.items()}


# ------------------------------------------------------------------ the state and its cost
class State:
    def __init__(self, M, poses, remap):
        self.M, self.poses, self.remap = M, dict(poses), {k: (list(v) if isinstance(v, list) else v) for k, v in remap.items()}
        self.xy = np.zeros((M.NP, 2))
        self.xy[:M.nfixed] = M.fixed_xy
        for b in M.blocks:
            self._place(b)
        self.set_nets()

    def _place(self, b):
        x, y, r, m = self.poses[b]
        s, e = self.M.bslice[b]
        self.xy[s:e] = self.M.voff[(b, r, m)] + (x, y)

    def set_nets(self):
        self.nid, self.nname = self.M.nets(self.remap)
        self.hvmask = np.array([self.nid[i] >= 0 and self.M.board_cls.cls(self.nname[self.nid[i]]) == "HV"
                                for i in range(self.M.NP)])
        logic = set()
        for i in range(self.M.NP):
            n = self.nname.get(self.nid[i])
            if n and self.M.board_cls.cls(n) != "HV" and n not in ("GND", "+12V", "VIN_J", "VIN_F", "GATE", "GATE_D") \
                    and not n.startswith(("K", "CAT_", "OPT_")):
                logic.add(i)
        self.logicmask = np.zeros(self.M.NP, bool)
        self.logicmask[list(logic)] = True
        self.netpads = {}
        for i, n in enumerate(self.nid):
            if n >= 0:
                self.netpads.setdefault(n, []).append(i)
        self.netpads = {n: np.array(v) for n, v in self.netpads.items() if len(v) > 1}
        self.blknets = {}
        for n, idx in self.netpads.items():
            for bi in set(self.M.pad_blk[idx].tolist()):
                self.blknets.setdefault(bi, set()).add(n)
        self.mst = {n: self._mst(n) for n in self.netpads}

    def _mst(self, n):
        idx = self.netpads[n]
        p = self.xy[idx]
        k = len(idx)
        if k == 2:
            return [(idx[0], idx[1])], float(np.hypot(*(p[0] - p[1])))
        d = np.hypot(p[:, None, 0] - p[None, :, 0], p[:, None, 1] - p[None, :, 1])
        intree = np.zeros(k, bool)
        intree[0] = True
        best = d[0].copy()
        parent = np.zeros(k, int)
        edges, L = [], 0.0
        for _ in range(k - 1):
            bb = np.where(intree, np.inf, best)
            j = int(np.argmin(bb))
            edges.append((idx[parent[j]], idx[j]))
            L += bb[j]
            intree[j] = True
            upd = d[j] < best
            best = np.where(upd, d[j], best)
            parent = np.where(upd, j, parent)
        return edges, L

    def update_blocks(self, blocks):
        nets = set()
        for b in blocks:
            self._place(b)
            nets |= self.blknets.get(self.M.blocks.index(b), set())
        for n in nets:
            self.mst[n] = self._mst(n)

    # -------------------------------------------------------------- the cost
    def cost(self, detail=False):
        M = self.M
        c = {}
        gnd = [k for k, v in self.nname.items() if v == "GND"]
        gnd = gnd[0] if gnd else -99
        c["mst"] = sum(L for n, (e, L) in self.mst.items() if n != gnd) * WT["mst"]
        c["gnd"] = self.mst[gnd][1] * WT["gnd"] if gnd in self.mst else 0.0
        # the MST edges of every net but ground
        E, EN = [], []
        for n, (edges, L) in self.mst.items():
            if n == gnd:
                continue
            for a, b in edges:
                E.append((a, b))
                EN.append(n)
        E = np.array(E)
        EN = np.array(EN)
        A, B = self.xy[E[:, 0]], self.xy[E[:, 1]]
        ncross, nnear, frus, cross_pairs = self._crossings(A, B, EN, E)
        c["cross"] = (ncross - nnear) * WT["cross"] + nnear * WT["cross_near"]
        c["frustr"] = frus * WT["frustr"]
        c["padhit"] = self._padhits(A, B, EN) * WT["padhit"]
        c["hv"] = self._hv() * WT["hv"]
        c["edge"] = self._edges() * WT["edge"]
        c["overlap"] = self._overlap() * WT["overlap"]
        tot = sum(c.values())
        if detail:
            c["n_cross"], c["n_cross_near"], c["n_frustr"] = int(ncross), int(nnear), int(frus)
            c["mst_mm"] = round(c["mst"] / WT["mst"], 1)
            c["total"] = tot
            return c
        return tot

    def _crossings(self, A, B, EN, E):
        m = len(A)
        d = B - A
        # proper intersection of segment i and j
        ax, ay, dx, dy = A[:, 0], A[:, 1], d[:, 0], d[:, 1]
        # bounding-box prefilter
        x0, x1 = np.minimum(A[:, 0], B[:, 0]), np.maximum(A[:, 0], B[:, 0])
        y0, y1 = np.minimum(A[:, 1], B[:, 1]), np.maximum(A[:, 1], B[:, 1])
        ov = (x0[:, None] < x1[None, :]) & (x0[None, :] < x1[:, None]) & (y0[:, None] < y1[None, :]) & (y0[None, :] < y1[:, None])
        ov &= EN[:, None] != EN[None, :]
        ov = np.triu(ov, 1)
        I, J = np.nonzero(ov)
        if len(I) == 0:
            return 0, 0, 0, []
        den = dx[I] * dy[J] - dy[I] * dx[J]
        ok = np.abs(den) > 1e-9
        I, J, den = I[ok], J[ok], den[ok]
        ex, ey = ax[J] - ax[I], ay[J] - ay[I]
        t = (ex * dy[J] - ey * dx[J]) / den
        u = (ex * dy[I] - ey * dx[I]) / den
        eps = 0.02
        hit = (t > eps) & (t < 1 - eps) & (u > eps) & (u < 1 - eps)
        I, J, t = I[hit], J[hit], t[hit]
        if len(I) == 0:
            return 0, 0, 0, []
        px, py = ax[I] + t * dx[I], ay[I] + t * dy[I]
        # near a pad of either net: a face change is available
        Q, qn = self.xy, self.nid
        d2 = (Q[None, :, 0] - px[:, None]) ** 2 + (Q[None, :, 1] - py[:, None]) ** 2
        mine = (qn[None, :] == EN[I][:, None]) | (qn[None, :] == EN[J][:, None])
        near = ((d2 < 9.0) & mine).any(1)
        # frustration: greedy two-colouring of the edges over the far (hard) crossings
        # FRUSTR_ALL (default since the first routing runs): colour over EVERY crossing. The near-pad
        # discount is right for the plain crossing count but wrong here: an MST edge is one track on one
        # face whatever pads its net has, so a decoder's ten two-pad lines crossing a strip's pin order
        # are an odd cycle right beside the pads - the first runs' last stuck pairs (K2/K9) were exactly that.
        hard = [(int(i), int(j)) for i, j, nr in zip(I, J, near) if FRUSTR_ALL or not nr]
        adj = {}
        for i, j in hard:
            adj.setdefault(i, []).append(j)
            adj.setdefault(j, []).append(i)
        col = {}
        frus = 0
        for s in adj:
            if s in col:
                continue
            col[s] = 0
            stack = [s]
            while stack:
                v = stack.pop()
                for w in adj[v]:
                    if w not in col:
                        col[w] = 1 - col[v]
                        stack.append(w)
        for i, j in hard:
            if col[i] == col[j]:
                frus += 1
        return len(I), int(near.sum()), frus, list(zip(I.tolist(), J.tolist()))

    def _padhits(self, A, B, EN):
        """MST edges passing within 1.0 mm of a pad of another net (both faces blocked there)."""
        Q = self.xy
        qn = self.nid
        d = B - A
        L2 = (d ** 2).sum(1) + 1e-9
        t = ((Q[None, :, 0] - A[:, None, 0]) * d[:, None, 0] + (Q[None, :, 1] - A[:, None, 1]) * d[:, None, 1]) / L2[:, None]
        t = np.clip(t, 0, 1)
        cx = A[:, None, 0] + t * d[:, None, 0]
        cy = A[:, None, 1] + t * d[:, None, 1]
        dist2 = (cx - Q[None, :, 0]) ** 2 + (cy - Q[None, :, 1]) ** 2
        hit = (dist2 < 1.0) & (qn[None, :] != EN[:, None])
        return float(hit.sum())

    def _hv(self):
        M = self.M
        h, l = np.nonzero(self.hvmask)[0], np.nonzero(self.logicmask)[0]
        if not len(h) or not len(l):
            return 0.0
        dd = np.hypot(self.xy[h, None, 0] - self.xy[None, l, 0], self.xy[h, None, 1] - self.xy[None, l, 1])
        diff = M.pad_blk[h][:, None] != M.pad_blk[l][None, :]
        return float((np.clip(4.0 - dd, 0, None) * diff).sum())

    def _edges(self):
        pen = 0.0
        x, y, r, m = self.poses["NANO"]
        _, _, rot = self.M.var[("NANO", r, m)][0][:4] if False else (0, 0, self.M.var[("NANO", r, m)][0][3])
        pen += self._edge_pen("NANO", "U1", usb_dir(rot), 2.4)
        rotj = [p for p in self.M.var[("PWR", *self.poses["PWR"][2:])] if p[0] == "XS1"][0][3]
        pen += self._edge_pen("PWR", "XS1", jack_dir(rotj), 0.0)
        return pen

    def _edge_pen(self, b, ref, dvec, proud):
        """The courtyard side the connector faces must sit `proud` mm beyond that board edge."""
        c = self.court_of(b, ref)
        dx, dy = round(dvec[0]), round(dvec[1])
        if dx == 1:
            return abs(c[2] - (W + proud))
        if dx == -1:
            return abs(c[0] - (0 - proud))
        if dy == 1:
            return abs(c[3] - (H + proud))
        return abs(c[1] - (0 - proud))

    def court_of(self, b, ref):
        x, y, r, m = self.poses[b]
        for cref, back, a, bb, cc, dd in self.M.vcourt[(b, r, m)]:
            if cref == ref:
                return (a + x, bb + y, cc + x, dd + y)

    def courts(self):
        out = []
        for b in self.M.blocks:
            x, y, r, m = self.poses[b]
            for cref, back, a, bb, cc, dd in self.M.vcourt[(b, r, m)]:
                out.append((cref, back, a + x, bb + y, cc + x, dd + y, b))
        return out

    def _overlap(self):
        cs = self.courts()
        arr = np.array([c[2:6] for c in cs])
        back = np.array([c[1] for c in cs])
        blk = [c[6] for c in cs]
        refs = [c[0] for c in cs]
        m = 0.0
        a0, b0, a1, b1 = arr[:, 0] - m, arr[:, 1] - m, arr[:, 2] + m, arr[:, 3] + m
        ox = np.clip(np.minimum(a1[:, None], a1[None, :]) - np.maximum(a0[:, None], a0[None, :]), 0, None)
        oy = np.clip(np.minimum(b1[:, None], b1[None, :]) - np.maximum(b0[:, None], b0[None, :]), 0, None)
        area = ox * oy
        same = back[:, None] == back[None, :]
        pen = float(np.triu(area * same, 1).sum())
        # pads: a through-hole pad on both faces must not meet a pad of a part on the other face
        # (cheap proxy: J1 is the only back-face part besides the strips; its courtyard vs front pads)
        F = self.M.fixed_courts
        fx = np.clip(np.minimum(a1[:, None], F[None, :, 2]) - np.maximum(a0[:, None], F[None, :, 0]), 0, None)
        fy = np.clip(np.minimum(b1[:, None], F[None, :, 3]) - np.maximum(b0[:, None], F[None, :, 1]), 0, None)
        pen += float((fx * fy).sum())
        # outside the board (the connectors' own proud sides are exempt: the edge term holds them)
        for i, (cref, bk, a, bb, cc, dd, b) in enumerate(cs):
            lo_x, hi_x, lo_y, hi_y = 0.5, W - 0.5, 0.5, H - 0.5
            if cref in ("U1", "XS1"):
                lo_x, hi_x, lo_y, hi_y = -3, W + 3, -3, H + 3
            pen += max(0, lo_x - a) * (dd - bb) + max(0, cc - hi_x) * (dd - bb) + max(0, lo_y - bb) * (cc - a) + max(0, dd - hi_y) * (cc - a)
            if cref == "J1":                  # the plug must clear the display board
                pen += max(0.0, DISP_BOTTOM + 1.0 - bb) * (cc - a)
        # through-hole pads of different parts closer than 2 mm (either face: they go through the board)
        Q = self.xy
        dd = np.hypot(Q[:, None, 0] - Q[None, :, 0], Q[:, None, 1] - Q[None, :, 1])
        pen += 2.0 * float(np.triu(np.clip(2.0 - dd, 0, None) * self.M.other_part, 1).sum())
        return pen

    def export(self):
        parts = []
        for b in self.M.blocks:
            x, y, r, m = self.poses[b]
            for ref, dx, dy, rot, back in self.M.var[(b, r, m)]:
                parts.append((ref, fp_of(ref), round(x + dx, 3), round(y + dy, 3), rot, back))
        return parts


# ------------------------------------------------------------------ the search
def random_poses(M, rng):
    poses = {}
    for b in M.blocks:
        poses[b] = (rng.uniform(10, W - 10), rng.uniform(10, H - 10), rng.choice((0, 90, 180, 270)), rng.choice((0, 1)))
    return poses


def snap_connectors(S):
    """Put the Nano and the jack on an edge straight away: their edge term is a hard constraint."""
    for b, ref, fn, proud in (("NANO", "U1", usb_dir, 2.4), ("PWR", "XS1", jack_dir, 0.0)):
        x, y, r, m = S.poses[b]
        rot = [p for p in S.M.var[(b, r, m)] if p[0] == ref][0][3]
        c = S.court_of(b, ref)
        dx, dy = round(fn(rot)[0]), round(fn(rot)[1])
        if dx == 1:
            x += (W + proud) - c[2]
        elif dx == -1:
            x += (0 - proud) - c[0]
        elif dy == 1:
            y += (H + proud) - c[3]
        else:
            y += (0 - proud) - c[1]
        S.poses[b] = (x, y, r, m)
        S.update_blocks([b])


def anneal(seed, iters=60000, T0=300.0, T1=0.3, init=None, verbose=False):
    rng = random.Random(seed)
    M = Model()
    poses = init["poses"] if init else random_poses(M, rng)
    remap = init["remap"] if init else dict(opto=rng.sample(ANODE_PINS, 6), bl=rng.sample(range(1, 9), 8), xaswap=rng.random() < 0.5)
    S = State(M, poses, remap)
    snap_connectors(S)
    cur = S.cost()
    best, best_state = cur, (dict(S.poses), json.loads(json.dumps(S.remap)))
    kinds = {}
    for b in M.blocks:
        kinds.setdefault(KIND[b], []).append(b)
    t0 = time.time()
    for it in range(iters):
        T = T0 * (T1 / T0) ** (it / iters)
        step = max(0.3, 25.0 * (T / T0) ** 0.5)
        mv = rng.random()
        undo_poses, undo_remap, touched = None, None, []
        if mv < 0.70:
            b = rng.choice(M.blocks)
            x, y, r, m = S.poses[b]
            undo_poses = {b: S.poses[b]}
            S.poses[b] = (x + rng.gauss(0, step), y + rng.gauss(0, step), r, m)
            touched = [b]
        elif mv < 0.82:
            b = rng.choice(M.blocks)
            x, y, r, m = S.poses[b]
            undo_poses = {b: S.poses[b]}
            if rng.random() < 0.7:
                S.poses[b] = (x, y, (r + rng.choice((90, 180, 270))) % 360, m)
            else:
                S.poses[b] = (x, y, r, 1 - m)
            touched = [b]
        elif mv < 0.90:
            b1 = rng.choice(M.blocks)
            same = [b for b in kinds[KIND[b1]] if b != b1]
            b2 = rng.choice(same) if same and rng.random() < 0.7 else rng.choice(M.blocks)
            if b2 == b1:
                continue
            undo_poses = {b1: S.poses[b1], b2: S.poses[b2]}
            (x1, y1, r1, m1), (x2, y2, r2, m2) = S.poses[b1], S.poses[b2]
            S.poses[b1], S.poses[b2] = (x2, y2, r1, m1), (x1, y1, r2, m2)
            touched = [b1, b2]
        else:
            undo_remap = json.loads(json.dumps(S.remap))
            k = rng.random()
            if k < 0.45:
                i, j = rng.sample(range(6), 2)
                S.remap["opto"][i], S.remap["opto"][j] = S.remap["opto"][j], S.remap["opto"][i]
            elif k < 0.9:
                i, j = rng.sample(range(8), 2)
                S.remap["bl"][i], S.remap["bl"][j] = S.remap["bl"][j], S.remap["bl"][i]
            else:
                S.remap["xaswap"] = not S.remap["xaswap"]
        if touched:
            if "NANO" in touched or "PWR" in touched:
                snap_connectors(S)
            S.update_blocks(touched)
        else:
            S.set_nets()
        new = S.cost()
        if new <= cur or rng.random() < math.exp((cur - new) / T):
            cur = new
            if new < best:
                best, best_state = new, (dict(S.poses), json.loads(json.dumps(S.remap)))
        else:
            if undo_poses:
                S.poses.update(undo_poses)
                S.update_blocks(list(undo_poses))
            if undo_remap:
                S.remap = undo_remap
                S.set_nets()
        if verbose and it % 5000 == 0:
            print(f"  seed {seed} it {it} T {T:.2f} cur {cur:.0f} best {best:.0f} {time.time() - t0:.0f}s", flush=True)
    S = State(M, best_state[0], best_state[1])
    return dict(seed=seed, cost=S.cost(detail=True), poses=S.poses, remap=S.remap, parts=S.export())


def _run(args):
    seed, iters = args
    r = anneal(seed, iters, verbose=True)
    os.makedirs(OUTDIR, exist_ok=True)
    fn = os.path.join(OUTDIR, f"cand_{seed}.json")
    with open(fn, "w") as fh:
        json.dump(r, fh, indent=1, default=float)
    print(f"seed {seed}: total {r['cost']['total']:.0f}  {json.dumps({k: round(v, 1) for k, v in r['cost'].items()})}", flush=True)
    return fn


# ------------------------------------------------------------------ the baseline under the same cost
def baseline_state():
    """tools/mkpcb_drv.py's placement, scored by this cost: its parts, its remaps, its footprints."""
    import mkpcb_drv as D
    M = Model()
    # build a state whose pads are the baseline's own pads: one pseudo-block per part
    parts = [(r, D.B.placed[r][0].name, D.B.placed[r][1], D.B.placed[r][2], D.B.placed[r][0].rot, D.B.placed[r][0].back)
             for r in D.B.placed if r in PT and not r.startswith("XS") or r == "XS1"]
    return parts, D


def score_parts(parts, remap):
    """Score an arbitrary list of placed parts [(ref, fp, x, y, rot, back)] under the same cost."""
    global BLOCKS, FP_OVERRIDE
    saveB, saveF = BLOCKS, FP_OVERRIDE
    BLOCKS = [("P_" + r, [(r, 0, 0, rot, back)]) for r, fp, x, y, rot, back in parts]
    BLOCKS.insert(0, ("NANO", [p for p in BLOCKS if p[1][0][0] == "U1"][0][1]))
    BLOCKS = [b for b in BLOCKS if b[0] != "P_U1"]
    pw = [b for b in BLOCKS if b[1][0][0] == "XS1"][0]
    BLOCKS = [("PWR", pw[1]) if b is pw else b for b in BLOCKS]
    FP_OVERRIDE = {r: fp for r, fp, x, y, rot, back in parts}
    try:
        M = Model()
        poses = {}
        for r, fp, x, y, rot, back in parts:
            b = "NANO" if r == "U1" else "PWR" if r == "XS1" else "P_" + r
            poses[b] = (x, y, 0, 0)
        S = State(M, poses, remap)
        return S, S.cost(detail=True)
    finally:
        BLOCKS, FP_OVERRIDE = saveB, saveF


def baseline_remap():
    """The baseline's own maps, as tools/mkpcb_drv.py was drawn for (fixed here: this branch's
    ts06pair.py carries the search board's remaps)."""
    return dict(opto=list(ANODE_PINS), bl=[1, 2, 3, 4, 5, 6, 7, 8], xaswap=False)


def plot(S, path, title=""):
    from PIL import Image, ImageDraw
    s = 6
    im = Image.new("RGB", (int(W * s) + 20, int(H * s) + 20), (20, 20, 24))
    d = ImageDraw.Draw(im)
    o = 10
    d.rectangle([o, o, o + W * s, o + H * s], outline=(200, 200, 200))
    d.rectangle([o, o + Y0 * s, o + W * s, o + DISP_BOTTOM * s], outline=(70, 70, 90))
    for a, b, c, dd in S.M.fixed_courts:
        d.rectangle([o + a * s, o + b * s, o + c * s, o + dd * s], outline=(90, 90, 160))
    for ref, back, a, b, c, dd, blk in S.courts():
        col = (230, 170, 60) if back else (120, 200, 120)
        d.rectangle([o + a * s, o + b * s, o + c * s, o + dd * s], outline=col)
        d.text((o + a * s + 2, o + b * s + 1), ref, fill=col)
    gnd = [k for k, v in S.nname.items() if v == "GND"]
    for n, (edges, L) in S.mst.items():
        if gnd and n == gnd[0]:
            continue
        hv = S.M.board_cls.cls(S.nname[n]) == "HV"
        for a, b in edges:
            (x1, y1), (x2, y2) = S.xy[a], S.xy[b]
            d.line([o + x1 * s, o + y1 * s, o + x2 * s, o + y2 * s], fill=(255, 90, 90) if hv else (90, 160, 255))
    d.text((o + 4, o + H * s - 12), title, fill=(255, 255, 255))
    im.save(path)


if __name__ == "__main__":
    A = sys.argv[1:]
    if "--baseline" in A:
        parts, D = baseline_state()
        S, c = score_parts(parts, baseline_remap())
        print("baseline:", json.dumps({k: round(v, 1) for k, v in c.items()}))
        os.makedirs(OUTDIR, exist_ok=True)
        plot(S, os.path.join(OUTDIR, "baseline_mst.png"), "baseline " + str(round(c["total"])))
        sys.exit(0)
    if "--refine" in A:                     # a cold anneal from a saved candidate, overlaps priced x5
        fn = A[A.index("--refine") + 1]
        r = json.load(open(fn))
        WT["overlap"] *= 5
        init = dict(poses={b: tuple(v) for b, v in r["poses"].items()}, remap=r["remap"])
        out = anneal(r["seed"], int(A[A.index("--iters") + 1]) if "--iters" in A else 15000, T0=15.0, T1=0.1, init=init)
        WT["overlap"] /= 5
        M = Model()
        S = State(M, out["poses"], out["remap"])
        out["cost"] = S.cost(detail=True)
        fo = fn.replace(".json", "r.json")
        json.dump(out, open(fo, "w"), indent=1, default=float)
        plot(S, fo.replace(".json", ".png"), os.path.basename(fo) + " " + str(round(out["cost"]["total"])))
        print(json.dumps({k: round(v, 1) for k, v in out["cost"].items()}))
        sys.exit(0)
    if "--show" in A:
        fn = A[A.index("--show") + 1]
        r = json.load(open(fn))
        M = Model()
        S = State(M, {b: tuple(v) for b, v in r["poses"].items()}, r["remap"])
        c = S.cost(detail=True)
        print(json.dumps({k: round(v, 1) for k, v in c.items()}))
        plot(S, fn.replace(".json", ".png"), os.path.basename(fn) + " " + str(round(c["total"])))
        sys.exit(0)
    runs = int(A[A.index("--runs") + 1]) if "--runs" in A else 4
    iters = int(A[A.index("--iters") + 1]) if "--iters" in A else 60000
    seed0 = int(A[A.index("--seed") + 1]) if "--seed" in A else 1
    procs = int(A[A.index("--procs") + 1]) if "--procs" in A else os.cpu_count()
    from multiprocessing import Pool
    with Pool(procs) as pool:
        fns = pool.map(_run, [(seed0 + i, iters) for i in range(runs)])
    for fn in fns:
        r = json.load(open(fn))
        M = Model()
        S = State(M, {b: tuple(v) for b, v in r["poses"].items()}, r["remap"])
        plot(S, fn.replace(".json", ".png"), os.path.basename(fn) + " " + str(round(r["cost"]["total"])))
