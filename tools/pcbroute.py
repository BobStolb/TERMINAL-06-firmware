#!/usr/bin/env python3
"""A small two-layer grid maze router for this repo's board generators.

WHY IT EXISTS: TS06-SEC carries ~90 nets around four tube pin fields. Routing that the way
TS06-COLON was routed - every segment typed as a coordinate - is not tractable. The router
is deterministic (same placement in, same copper out), so a generator that calls it still
emits the whole board from source, like every other board here.

WHAT IT DOES: A* over a 0.1 mm grid on F.Cu and B.Cu, eight directions, with a small cost
for turning and a large one for a via. Other nets' copper is kept out by inflating it on
raster maps - 0.2 mm around low-voltage copper, 0.6 mm wherever a high-voltage net is
involved on either side (the same rule tools/checkcopper.py --hv checks). IPC-2221B Table
6-1 asks, for 151-250 V, 0.4 mm between conductors under solder mask (B4) and 0.8 mm
between bare component terminations (A6): 0.6 mm keeps every masked track 50% over B4,
and bare pad pairs between parts are checked on their own against A6.

The maps are kept once for each size of thing that can be centred on a free cell - a
0.2 mm track, a track up to 0.35 mm, a via - so every test is exact at the cell centre and
a thin track can take a gap a wide one could not. A path runs along cell centres and meets
each pad, via or track it starts or ends on through a stub that stays inside that copper.
No via lands within KiCad's hole-to-hole distance of a drill already on the board, nor
anywhere a generator has marked with novia().

NEGOTIATION: laid one after another, nets fence each other in - whichever arrives first takes
the corridor, and a net that could have gone round stands in the way of one that could not.
negotiate() routes a group of nets the way the PathFinder algorithm does: each is laid
against the others at a price instead of being stopped by them, the price of a shared cell
rises every round, and cells that stay contested get dearer for good, until no two overlap.
A negotiated net is a tree: each new pad is wired to the nearest copper the net already has.
Whatever still overlaps when the rounds run out is taken out and reported, never left in.

WHAT IT DOES NOT DO: fill pours (KiCad fills a zone; pour_reach() only predicts where one
joins up), length matching. A connection it cannot find is reported in .failed and never
faked; tools/checkcopper.py, tools/audit.py and KiCad's own DRC get the last word.
"""
import heapq, math, time
from array import array
import numpy as np

G = 0.1                            # grid pitch, mm
VIA_D, VIA_DRILL = 0.8, 0.4        # same via as tools/mkpcb_colon.py's via()
LV_CLR, HV_CLR, EDGE_CLR, HOLE_CLR, DRILL_GAP = 0.2, 0.6, 0.5, 0.25, 0.25
SNAP = 0.03                        # a diagonal step sags a few um toward a corner it was checked
                                   # clear of at both ends; the halos carry that and float slack
CLASSES = {"narrow": 0.1, "wide": 0.175, "via": VIA_D / 2}   # radius of what sits on a free cell
REACH = HV_CLR + max(CLASSES.values()) + SNAP                 # the widest halo any copper casts
COMPACT_DIL = 5                    # cells (0.5 mm) each way that count as 'beside something'
BUNDLE = 0.55                      # how near a net has to be to count as following its bus:
                                   # a 0.2 mm track beside a 0.2 mm track at 0.2 mm clearance
                                   # has its centreline 0.4 mm away, so 0.55 takes the next
                                   # lane over and not the one after it
KEEP = VIA_DRILL / 2 + DRILL_GAP + SNAP                       # a new via centre from a drill's edge
DIRS = [(1, 0, 10), (-1, 0, 10), (0, 1, 10), (0, -1, 10), (1, 1, 14), (1, -1, 14), (-1, 1, 14), (-1, -1, 14)]
LAYER = ("F.Cu", "B.Cu")
# GRAIN, in halves of the bias: F.Cu runs east-west, B.Cu north-south, and a step across a
# face grain costs `bias` more than one along it, a diagonal half of that. WHY: without it
# every net finds its own private geodesic and they cross each other everywhere instead of
# crossing between faces, which is the whole point of having two. The first TS06-MAIN was
# routed with no grain at all and its ground pour filled as 292 islands (18.09.26).
GRAIN = ((0, 0, 2, 2, 1, 1, 1, 1), (2, 2, 0, 0, 1, 1, 1, 1))


def track_class(width):
    assert width <= 2 * CLASSES["wide"] + 1e-9, width
    return "narrow" if width <= 2 * CLASSES["narrow"] + 1e-9 else "wide"


def seg_len(segs):
    return sum(math.hypot(bx - ax, by - ay) for _, ax, ay, bx, by, _ in segs)


def seg_foot(shape, x, y):
    """The point of a segment's centreline nearest (x, y)."""
    _, ax, ay, bx, by, _ = shape
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / L))
    return ax + t * dx, ay + t * dy


def dist_pt(shape, x, y):
    """Distance from a point to a shape, 0 inside it."""
    if shape[0] == "circle":
        return max(math.hypot(x - shape[1], y - shape[2]) - shape[3], 0.0)
    if shape[0] == "rect":
        _, cx, cy, w, h = shape
        return math.hypot(max(abs(x - cx) - w / 2, 0.0), max(abs(y - cy) - h / 2, 0.0))
    px, py = seg_foot(shape, x, y)
    return max(math.hypot(x - px, y - py) - shape[5] / 2, 0.0)


class Router:
    def __init__(self, W, H, hv_nets):
        self.W, self.H = W, H
        self.nx, self.ny = int(round(W / G)) + 1, int(round(H / G)) + 1
        self.hv = set(hv_nets)
        # per class: lvS = 5 V copper with a 0.2 mm halo, lvL = 5 V copper with a 0.6 mm halo
        # (what a high-voltage net sees), hvL = high-voltage copper with a 0.6 mm halo
        self.maps = {}
        for c, r in CLASSES.items():
            e = int(math.ceil((EDGE_CLR + r + SNAP) / G))
            for key in ("lvS", "lvL", "hvL"):
                m = np.full((2, self.ny, self.nx), -1, np.int32)
                m[:, :e, :] = -2
                m[:, -e:, :] = -2
                m[:, :, :e] = -2
                m[:, :, -e:] = -2
                self.maps[c, key] = m
        self.viakeep = np.zeros((self.ny, self.nx), bool)
        self.ids, self.names = {}, []
        self.grp, self.bgrp = {}, {}         # net -> bus name, bus name -> where its copper is
        self.segments, self.vias, self.failed = [], [], []
        self.use = None                    # overlap counts, only while negotiate() runs

    def nid(self, name):
        if name not in self.ids:
            self.ids[name] = len(self.names)
            self.names.append(name)
        return self.ids[name]

    def snapshot(self):
        return ({k: v.copy() for k, v in self.maps.items()}, self.viakeep.copy(), list(self.segments),
                list(self.vias), list(self.failed), dict(self.ids), list(self.names))

    def restore(self, s):
        self.maps = {k: v.copy() for k, v in s[0].items()}
        self.viakeep = s[1].copy()
        self.segments, self.vias, self.failed = list(s[2]), list(s[3]), list(s[4])
        self.ids, self.names = dict(s[5]), list(s[6])

    # ------------------------------------------------------------ rasterising
    def _dist(self, shape, reach):
        """Distance from each cell centre within reach of shape to the shape, 0 inside it."""
        kind = shape[0]
        if kind == "circle":
            _, x, y, r = shape
            x0, x1, y0, y1 = x - r, x + r, y - r, y + r
        elif kind == "rect":
            _, x, y, w, h = shape
            x0, x1, y0, y1 = x - w / 2, x + w / 2, y - h / 2, y + h / 2
        else:
            _, ax, ay, bx, by, w = shape
            r = w / 2
            x0, x1, y0, y1 = min(ax, bx) - r, max(ax, bx) + r, min(ay, by) - r, max(ay, by) + r
        i0, i1 = max(int(math.floor((x0 - reach) / G)), 0), min(int(math.ceil((x1 + reach) / G)) + 1, self.nx)
        j0, j1 = max(int(math.floor((y0 - reach) / G)), 0), min(int(math.ceil((y1 + reach) / G)) + 1, self.ny)
        if i1 <= i0 or j1 <= j0:
            return None
        PX, PY = np.meshgrid(np.arange(i0, i1) * G, np.arange(j0, j1) * G)
        if kind == "circle":
            D = np.maximum(np.hypot(PX - x, PY - y) - r, 0)
        elif kind == "rect":
            D = np.hypot(np.maximum(np.abs(PX - x) - w / 2, 0), np.maximum(np.abs(PY - y) - h / 2, 0))
        else:
            dx, dy = bx - ax, by - ay
            L = dx * dx + dy * dy
            t = np.zeros_like(PX) if L == 0 else np.clip(((PX - ax) * dx + (PY - ay) * dy) / L, 0, 1)
            D = np.maximum(np.hypot(PX - (ax + t * dx), PY - (ay + t * dy)) - r, 0)
        return j0, j1, i0, i1, D

    @staticmethod
    def _sub(win, box):
        """The part of a _dist window inside box: (row slice, column slice) of the box and of D."""
        pj0, pj1, pi0, pi1, D = win
        i0, i1, j0, j1 = box
        a0, a1, b0, b1 = max(pj0, j0), min(pj1, j1), max(pi0, i0), min(pi1, i1)
        if a1 <= a0 or b1 <= b0:
            return None
        return slice(a0 - j0, a1 - j0), slice(b0 - i0, b1 - i0), D[a0 - pj0:a1 - pj0, b0 - pi0:b1 - pi0]

    def paint(self, name, layers, shape):
        """Copper that exists: a pad, a track, a via. name None = copper on no net."""
        net = self.nid(name) if name else -3
        keys = (("hvL", HV_CLR),) if name in self.hv else (("lvS", LV_CLR), ("lvL", HV_CLR))
        win = self._dist(shape, REACH)
        if not win:
            return
        j0, j1, i0, i1, D = win
        for c, r in CLASSES.items():
            for key, clr in keys:
                m = D <= clr + r + SNAP
                for L in layers:
                    sub = self.maps[c, key][L, j0:j1, i0:i1]
                    clash = m & (sub != -1) & (sub != net)
                    sub[m & (sub == -1)] = net
                    sub[clash] = -2

    def novia(self, shape, infl):
        """No via centre within infl of shape."""
        win = self._dist(shape, infl)
        if win:
            j0, j1, i0, i1, D = win
            self.viakeep[j0:j1, i0:i1] |= D <= infl

    def drill(self, x, y, d):
        """A drill that exists (a plated pad's, a via's): no new via within DRILL_GAP of its edge."""
        self.novia(("circle", x, y, d / 2), KEEP)

    def hole(self, x, y, d):
        """An unplated hole: nothing of any net within HOLE_CLR of its edge, on either face."""
        win = self._dist(("circle", x, y, d / 2), HOLE_CLR + max(CLASSES.values()) + SNAP)
        if win:
            j0, j1, i0, i1, D = win
            for (c, _), arr in self.maps.items():
                arr[:, j0:j1, i0:i1][:, D <= HOLE_CLR + CLASSES[c] + SNAP] = -2
        self.drill(x, y, d)

    def pour_reach(self, name, layers, seeds, portals=()):
        """{layer: cells} that a pour of net name on those layers fills and joins to a seed point.
        Other copper is held off by its 0.6 mm map, whose extra narrow-track half width stands in
        for the zone's min_thickness. portals - the net's vias and through-hole pads - join the
        pours of both faces where they stand."""
        net = self.nid(name)
        free, reach = {}, {}
        for L in layers:
            a, b = self.maps["narrow", "lvL"][L], self.maps["narrow", "hvL"][L]
            free[L] = ((a == -1) | (a == net)) & ((b == -1) | (b == net))
            reach[L] = np.zeros_like(free[L])
            for x, y in seeds:
                reach[L][int(round(y / G)), int(round(x / G))] = True
            reach[L] &= free[L]
        cells = [(int(round(y / G)), int(round(x / G))) for x, y in portals]
        while True:
            before = sum(int(r.sum()) for r in reach.values())
            for L in layers:
                r = reach[L]
                for _ in range(32):
                    g = r.copy()
                    g[1:, :] |= r[:-1, :]
                    g[:-1, :] |= r[1:, :]
                    g[:, 1:] |= r[:, :-1]
                    g[:, :-1] |= r[:, 1:]
                    r = g & free[L]
                reach[L] = r
            for j, i in cells:
                if any(reach[L][j, i] for L in layers):
                    for L in layers:
                        reach[L][j, i] = free[L][j, i]
            if sum(int(r.sum()) for r in reach.values()) == before:
                return reach

    # ------------------------------------------------------------ searching
    def _box(self, ends, grow):
        x0, x1 = max(min(e[0] for e in ends) - grow, 0.0), min(max(e[0] for e in ends) + grow, self.W)
        y0, y1 = max(min(e[1] for e in ends) - grow, 0.0), min(max(e[1] for e in ends) + grow, self.H)
        return (int(x0 / G), min(int(math.ceil(x1 / G)) + 1, self.nx),
                int(y0 / G), min(int(math.ceil(y1 / G)) + 1, self.ny))

    def _blocked(self, net, hv, box, c):
        i0, i1, j0, j1 = box
        out = []
        for L in (0, 1):
            if hv:
                a, b = self.maps[c, "hvL"][L, j0:j1, i0:i1], self.maps[c, "lvL"][L, j0:j1, i0:i1]
            else:
                a, b = self.maps[c, "lvS"][L, j0:j1, i0:i1], self.maps[c, "hvL"][L, j0:j1, i0:i1]
            out.append(((a != -1) & (a != net)) | ((b != -1) & (b != net)))
        return np.stack(out)

    def connect(self, name, width, src, dst, via_cost=1500, turn=15, bias=0, margin=6.0, allow=(0, 1),
                to_layer=None, reach=None):
        """src, dst: pads as (x, y, layers, shape). allow: the layers this net may use.
        A via costs as much as 15 mm of extra track by default, so a same-layer detour of up to
        that length always wins - the repo's standing preference. With dst None and to_layer
        set, the path ends on the first free cell of that layer: at the nearest legal via.
        Returns True if copper was laid."""
        net, hv, c = self.nid(name), name in self.hv, track_class(width)
        targets = [("pad", dst[2], dst[3])] if dst else []
        path = None
        for grow in (margin, margin * 3, 1e6):
            box = self._box((src, dst) if dst else (src,), grow)
            path = self._astar(net, hv, c, box, src, dst, targets, via_cost, turn, allow, to_layer, reach,
                               bias=bias)
            if path or box == (0, self.nx, 0, self.ny):
                break
        if not path:
            self.failed.append((name, (round(src[0], 2), round(src[1], 2)),
                                (round(dst[0], 2), round(dst[1], 2)) if dst else LAYER[to_layer]))
            return False
        segs, vias, _, _ = self._geometry(path, src, targets, width)
        self._lay(name, segs, vias)
        return True

    def fanout(self, name, width, src, layer, reach=None, **kw):
        """src pad wired to a via onto layer, for a net that is poured on that layer. reach
        (from pour_reach) limits the via to cells the pour joins up; KiCad's fill and
        tools/audit.py still have the last word on whether it does."""
        return self.connect(name, width, src, None, margin=3.0, to_layer=layer, reach=reach, **kw)

    def _astar(self, net, hv, c, box, src, goal, targets, via_cost, turn, allow, to_layer=None, reach=None,
               soft=None, vsoft=None, nokeep=(), bias=0):
        """targets: (kind, layers, shape) copper the path may end in. soft, vsoft: extra cost of
        stepping onto a cell and of a via there, while negotiating. nokeep: vias of this net."""
        i0, i1, j0, j1 = box
        w, h = i1 - i0, j1 - j0
        blk = self._blocked(net, hv, box, c)
        for L in (0, 1):
            if L not in allow:
                blk[L] = True
        tgt = np.zeros_like(blk)
        for kind, layers, shape, is_tgt in [("pad", src[2], src[3], False)] + [t + (True,) for t in targets]:
            win = self._dist(shape, 0.0)
            part = win and self._sub(win, box)
            if not part:
                continue
            rs, cs, D = part
            m = D <= 1e-9
            for L in layers:
                if L in allow:
                    blk[L, rs, cs][m] = False
                    if is_tgt:
                        tgt[L, rs, cs][m] = True
        blk[:, 0, :] = True                # a blocked frame: no bounds tests in the inner loop
        blk[:, -1, :] = True
        blk[:, :, 0] = True
        blk[:, :, -1] = True
        if to_layer is not None:
            if isinstance(reach, dict):    # {layer: cells}: end in whichever pour region comes first
                for L, r in reach.items():
                    if L in allow:
                        tgt[L] = ~blk[L] & r[j0:j1, i0:i1]
            else:
                tgt[to_layer] = ~blk[to_layer] if reach is None else ~blk[to_layer] & reach[j0:j1, i0:i1]
        if len(allow) == 2:
            vb = self._blocked(net, hv, box, "via")
            via_ok = ~(vb[0] | vb[1]) & ~self.viakeep[j0:j1, i0:i1]
            for x, y in nokeep:
                part = self._sub(self._dist(("circle", x, y, VIA_DRILL / 2), KEEP) or (0, 0, 0, 0, None), box)
                if part:
                    rs, cs, D = part
                    via_ok[rs, cs] &= D > KEEP
        else:
            via_ok = np.zeros((h, w), bool)
        N = w * h
        free = np.logical_not(blk).astype(np.uint8).tobytes()      # index L*N + j*w + i
        tg = tgt.astype(np.uint8).tobytes()
        vok = via_ok.astype(np.uint8).tobytes()
        sf = array("i", soft.astype(np.int32).tobytes()) if soft is not None else bytes(2 * N)
        vs = array("i", vsoft.astype(np.int32).tobytes()) if vsoft is not None else bytes(N)
        si, sj = int(round(src[0] / G)) - i0, int(round(src[1] / G)) - j0
        if goal:
            ti, tj, hk = int(round(goal[0] / G)) - i0, int(round(goal[1] / G)) - j0, 12
        else:
            ti, tj, hk = si, sj, 0                 # no single goal: plain Dijkstra
        INF = 1 << 62
        gcost = [INF] * (2 * N)
        came = [-1] * (2 * N)
        cdir = bytearray([255]) * (2 * N)
        heap = []
        if 0 < si < w - 1 and 0 < sj < h - 1:
            for L in src[2]:
                k = L * N + sj * w + si
                if L in allow and free[k]:
                    gcost[k] = 0
                    heap.append((0, 0, k))
        heapq.heapify(heap)
        # one step table per face, the grain already priced in. The heuristic below is weighted
        # by 1.2 and so was never admissible; a bias only raises real costs, which can only
        # bring it closer to admissible, so nothing else has to change.
        stepL = [[(dx + dy * w, dx, dy * w, dx, dy, cst + bias * GRAIN[L][d] // 2, d)
                  for d, (dx, dy, cst) in enumerate(DIRS)] for L in (0, 1)]
        pop, push = heapq.heappop, heapq.heappush
        while heap:
            _, g, k = pop(heap)
            if g != gcost[k]:
                continue                           # superseded by a cheaper route to this state
            if tg[k]:
                out = []
                while k != -1:
                    L = 1 if k >= N else 0
                    j, i = divmod(k - L * N, w)
                    out.append((L, j + j0, i + i0))
                    k = came[k]
                return out[::-1]
            upper = k >= N
            rem = k - N if upper else k
            j, i = divmod(rem, w)
            d0 = cdir[k]
            for off, ox, oy, dx, dy, cst, d in stepL[1 if upper else 0]:
                nk = k + off
                if not free[nk]:
                    continue
                if ox and oy and not (free[k + ox] and free[k + oy]):
                    continue                       # no corner cutting between two halos
                ng = g + cst + sf[nk] + (0 if (d0 == 255 or d0 == d) else turn)
                if ng < gcost[nk]:
                    gcost[nk], came[nk], cdir[nk] = ng, k, d
                    ax, ay = abs(i + dx - ti), abs(j + dy - tj)
                    push(heap, (ng + (hk * (10 * max(ax, ay) + 4 * min(ax, ay))) // 10, ng, nk))
            if vok[rem]:
                nk = k - N if upper else k + N
                ng = g + via_cost + vs[rem]
                if free[nk] and ng < gcost[nk]:
                    gcost[nk], came[nk], cdir[nk] = ng, k, 255
                    ax, ay = abs(i - ti), abs(j - tj)
                    push(heap, (ng + (hk * (10 * max(ax, ay) + 4 * min(ax, ay))) // 10, ng, nk))
        return None

    # ------------------------------------------------------------ geometry
    def _geometry(self, path, src, targets, width):
        """Cells to copper: merged segments, a via at each change of layer, a stub from the
        source pad's centre and one onto whatever target the path ended in. Also returns the
        path's cells outside the net's own copper, and its via cells, for the overlap count."""
        pts = [(L, i, j) for L, j, i in path]      # grid units, so collinearity is exact
        runs, cur, vias = [], [pts[0]], []
        for p in pts[1:]:
            if p[0] != cur[-1][0]:
                vias.append((p[1] * G, p[2] * G))
                runs.append(cur)
                cur = [p]
            else:
                cur.append(p)
        runs.append(cur)
        segs = []
        for run in runs:
            keep = [run[0]]
            for a, b in zip(run[1:], run[2:]):
                p = keep[-1]
                d1 = (a[1] - p[1], a[2] - p[2])
                d2 = (b[1] - a[1], b[2] - a[2])
                if d1[0] * d2[1] - d1[1] * d2[0] or d1[0] * d2[0] + d1[1] * d2[1] <= 0:
                    keep.append(a)
            keep.append(run[-1])
            for a, b in zip(keep, keep[1:]):
                if a[1:] != b[1:]:
                    segs.append((a[0], a[1] * G, a[2] * G, b[1] * G, b[2] * G, width))
        s0, s1 = pts[0], pts[-1]
        if math.hypot(src[0] - s0[1] * G, src[1] - s0[2] * G) > 1e-6:
            segs.insert(0, (s0[0], src[0], src[1], s0[1] * G, s0[2] * G, width))
        ex, ey = s1[1] * G, s1[2] * G
        for kind, layers, shape in targets:        # a pad or via is met at its centre, a track
            if s1[0] in layers and dist_pt(shape, ex, ey) <= 1e-9:     # on its centreline
                ax, ay = seg_foot(shape, ex, ey) if kind == "seg" else (shape[1], shape[2])
                if math.hypot(ax - ex, ay - ey) > 1e-6:
                    segs.append((s1[0], ex, ey, ax, ay, width))
                break
        own = [(src[2], src[3])] + [(t[1], t[2]) for t in targets]
        cells = [(L, j, i) for L, j, i in path
                 if not any(L in lay and dist_pt(sh, i * G, j * G) <= 1e-9 for lay, sh in own)]
        return segs, vias, cells, [(int(round(y / G)), int(round(x / G))) for x, y in vias]

    def _lay(self, name, segs, vias):
        for L, ax, ay, bx, by, w in segs:
            self.segments.append((round(ax, 4), round(ay, 4), round(bx, 4), round(by, 4), w, LAYER[L], name))
            self.paint(name, (L,), ("seg", ax, ay, bx, by, w))
        for x, y in vias:
            self.vias.append((round(x, 4), round(y, 4), name))
            self.paint(name, (0, 1), ("circle", x, y, VIA_D / 2))
            self.drill(x, y, VIA_DRILL)

    def route_net(self, name, width, pads, **kw):
        """pads: list of (x, y, layers, shape). Prim's tree on straight-line distance."""
        if len(pads) < 2:
            return 0
        done, todo, fails = [pads[0]], list(pads[1:]), 0
        while todo:
            _, ia, ib = min(((math.hypot(a[0] - b[0], a[1] - b[1]), ia, ib)
                             for ia, a in enumerate(done) for ib, b in enumerate(todo)))
            if not self.connect(name, width, todo[ib], done[ia], **kw):
                fails += 1
            done.append(todo.pop(ib))
        return fails

    def route_star(self, name, width, hub, pads, **kw):
        """Every pad in pads wired straight to hub, nearest first."""
        fails = 0
        for p in sorted(pads, key=lambda p: math.hypot(p[0] - hub[0], p[1] - hub[1])):
            if not self.connect(name, width, p, hub, **kw):
                fails += 1
        return fails

    # ------------------------------------------------------------ negotiation
    def _stamp(self, name, segs, vias, sign, group=None):
        """Add (+1) or take away (-1) one negotiated net's halos in the overlap counts, and in
        its bus's bundle map if it belongs to one."""
        if group is None:
            group = self.grp.get(name)
        keys = (("hvL", HV_CLR),) if name in self.hv else (("lvS", LV_CLR), ("lvL", HV_CLR))
        union = {}
        shapes = [((L,), ("seg", ax, ay, bx, by, w)) for L, ax, ay, bx, by, w in segs] + \
                 [((0, 1), ("circle", x, y, VIA_D / 2)) for x, y in vias]
        for layers, shape in shapes:
            win = self._dist(shape, REACH)
            if not win:
                continue
            j0, j1, i0, i1, D = win
            if group is not None:
                for L in layers:
                    u = union.get(("bundle", group, L))
                    if u is None:
                        u = union["bundle", group, L] = np.zeros((self.ny, self.nx), bool)
                    u[j0:j1, i0:i1] |= D <= BUNDLE
            for c, r in CLASSES.items():
                for key, clr in keys:
                    m = D <= clr + r + SNAP
                    for L in layers:
                        u = union.get((c, key, L))
                        if u is None:
                            u = union[c, key, L] = np.zeros((self.ny, self.nx), bool)
                        u[j0:j1, i0:i1] |= m
        for k, u in union.items():
            if k[0] == "bundle":
                b = self.bgrp.get(k[1])
                if b is None:
                    b = self.bgrp[k[1]] = np.zeros((2, self.ny, self.nx), np.int16)
                b[k[2]] += sign * u.astype(np.int16)
            else:
                self.use[k[0], k[1]][k[2]] += sign * u.astype(np.int16)
        if vias:
            u = np.zeros((self.ny, self.nx), bool)
            for x, y in vias:
                j0, j1, i0, i1, D = self._dist(("circle", x, y, VIA_DRILL / 2), KEEP)
                u[j0:j1, i0:i1] |= D <= KEEP
            self.vuse += sign * u.astype(np.int16)

    def _soft(self, hv, c, box, price, layer_cost=(0, 0), group=None, bundle=0, compact=0):
        i0, i1, j0, j1 = box
        a, b = ("hvL", "lvL") if hv else ("lvS", "hvL")
        cnt = self.use[c, a][:, j0:j1, i0:i1].astype(np.int64) + self.use[c, b][:, j0:j1, i0:i1]
        vcnt = (self.use["via", a][:, j0:j1, i0:i1].astype(np.int64)
                + self.use["via", b][:, j0:j1, i0:i1]).max(0) + self.vuse[j0:j1, i0:i1]
        # history multiplies the present price (PathFinder): a cell shared round after round
        # becomes dearer than fresh ground, so two nets stuck on one spot are pushed apart
        # instead of keeping the cheapest overlap for ever
        hist = self.hist[:, j0:j1, i0:i1]
        vhist = hist.max(0)
        cap = 1 << 30                      # stays an int32 inside the search however high the price climbs
        lc = np.array(layer_cost, np.int64)[:, None, None]
        soft = price * cnt * (1 + hist) + 10 * hist + lc
        # BUNDLE AFFINITY. Ten cathode lines run from one К155ИД1 to one tube and ought to go as a
        # ribbon; nothing in a plain negotiation makes them, because each net finds its own
        # geodesic and they only meet at the ends. So a step NOT beside its own bus costs extra -
        # a discount for following it, written as a surcharge for leaving it, because A* wants
        # every edge non-negative. A bus in one channel also leaves the pour one region instead
        # of ten slices.
        if group is not None and bundle:
            near = self.bgrp.get(group)
            if near is not None:
                soft = soft + bundle * (near[:, j0:j1, i0:i1] == 0)
        # COMPACTION, the same idea with no regard for whose copper it is: a step that is not
        # beside SOMETHING costs extra, so tracks gather into channels and leave the space
        # between them whole. WHY: a pour is cut by tracks, not by vias - 8647 mm of 0.2 mm
        # track with its clearance covers about 41% of this board against 3% for 356 vias - so
        # what decides whether the pour is a plane or confetti is whether the tracks run
        # together or spread out. Aligning vias to a lattice was considered first and dropped
        # on that arithmetic (18.09.26).
        if compact:
            near = cnt > 0
            d = near.copy()
            for k in range(1, COMPACT_DIL + 1):
                d[:, k:, :] |= near[:, :-k, :]
                d[:, :-k, :] |= near[:, k:, :]
                d[:, :, k:] |= near[:, :, :-k]
                d[:, :, :-k] |= near[:, :, k:]
            soft = soft + compact * ~d
        return (np.minimum(soft, cap),
                np.minimum(10 * price * vcnt * (1 + vhist) + 10 * vhist, cap))

    def _overlaps(self, name, width, cells, vcells, scar=0, where=None):
        """Cells where this net's path stands in another negotiated net's halo; scar > 0 also
        makes them dearer for every later round, and a list passed as where collects them."""
        c = track_class(width)
        a, b = ("hvL", "lvL") if name in self.hv else ("lvS", "hvL")
        n = 0
        if cells:
            L, j, i = (np.array(t) for t in zip(*cells))
            hit = (self.use[c, a][L, j, i].astype(np.int32) - 1 + self.use[c, b][L, j, i]) > 0
            n += int(hit.sum())
            if scar:
                np.add.at(self.hist, (L[hit], j[hit], i[hit]), scar)
            if where is not None:
                where += [(LAYER[int(l)], round(float(ii) * G, 1), round(float(jj) * G, 1))
                          for l, jj, ii in zip(L[hit], j[hit], i[hit])]
        if vcells:
            j, i = (np.array(t) for t in zip(*vcells))
            hit = self.vuse[j, i] > 1
            for L in (0, 1):
                hit |= (self.use["via", a][L, j, i].astype(np.int32) - 1 + self.use["via", b][L, j, i]) > 0
            n += int(hit.sum())
            if scar:
                for L in (0, 1):
                    np.add.at(self.hist, (np.full(int(hit.sum()), L), j[hit], i[hit]), scar)
            if where is not None:
                where += [("via", round(float(ii) * G, 1), round(float(jj) * G, 1)) for jj, ii in zip(j[hit], i[hit])]
        return n

    def _route_tree(self, name, width, pads, price, layer_cost=(0, 0), via_cost=1500, turn=15, allow=(0, 1),
                    bias=0, group=None, bundle=0, compact=0):
        net, hv, c = self.nid(name), name in self.hv, track_class(width)
        targets, inside, todo = [("pad", pads[0][2], pads[0][3])], [pads[0]], list(pads[1:])
        segs, vias, cells, vcells, failed = [], [], [], [], []
        while todo:
            _, ib, near = min((math.hypot(p[0] - q[0], p[1] - q[1]), ib, q)
                              for ib, p in enumerate(todo) for q in inside)
            src = todo.pop(ib)
            path = None
            for grow in (6.0, 18.0, 1e6):
                box = self._box((src, near), grow)
                soft, vsoft = self._soft(hv, c, box, price, layer_cost, group, bundle, compact)
                path = self._astar(net, hv, c, box, src, near, targets, via_cost, turn, allow,
                                   soft=soft, vsoft=vsoft, nokeep=vias, bias=bias)
                if path or box == (0, self.nx, 0, self.ny):
                    break
            if not path:
                failed.append((name, (round(src[0], 2), round(src[1], 2)), (round(near[0], 2), round(near[1], 2))))
                continue
            s, v, ce, vc = self._geometry(path, src, targets, width)
            segs += s
            vias += v
            cells += ce
            vcells += vc
            inside.append(src)
            targets += [("pad", src[2], src[3])] + [("seg", (L,), ("seg", ax, ay, bx, by, w))
                                                    for L, ax, ay, bx, by, w in s] + \
                       [("via", (0, 1), ("circle", x, y, VIA_D / 2)) for x, y in v]
        return segs, vias, cells, vcells, failed

    def negotiate(self, jobs, rounds=60, price=3, rise=1.4, scar=1, layer_cost=(0, 0), bias=0,
                  turn=15, decay=1.0, tighten=0, relax=0, groups=None, bundle=0, compact=0, log=None):
        """jobs: [(name, width, pads, opts)], routed together against everything already laid.
        layer_cost: extra cost of each step on F.Cu and on B.Cu (a plain step costs 10) - how a
        face kept for a pour is made the second choice rather than forbidden.
        bias: extra cost of a step across the face grain, see GRAIN.
        decay: what a history scar is worth a round later. At 1.0 it never fades, which is how
        PathFinder is usually written and is wrong for a board this full: a cell contested in
        round three is still dear in round twenty, so late nets detour round congestion that
        has long since moved elsewhere.
        tighten: passes of rip-up-and-reroute for length once nothing overlaps.
        relax: rounds of failure after which a net is let off the grain and the dear via
        altogether. The grain is a PREFERENCE, not a law, and the difference matters: at
        bias 8 twelve nets were still overlapping when the rounds ran out and at bias 0 only
        six, so obedience was costing six nets (18.09.26). The few that cannot obey are
        exactly the ones that have to cross the grain, and they are cheaper let off.
        groups: net -> bus name. bundle: what a step away from its own bus costs a net.
        compact: what a step away from any other net's copper costs, which gathers the tracks
        into channels and leaves the pour between them in one piece."""
        self.grp, self.bgrp = dict(groups or {}), {}
        self.use = {k: np.zeros(v.shape, np.int16) for k, v in self.maps.items()}
        self.vuse = np.zeros((self.ny, self.nx), np.int16)
        self.hist = np.zeros((2, self.ny, self.nx), np.float64)   # float: a scar may fade by a fraction
        job = {j[0]: (j[0], j[1], j[2], dict(j[3], bias=bias, turn=turn, compact=compact,
                      group=self.grp.get(j[0]), bundle=bundle)) for j in jobs}
        routes, todo, t0 = {}, [j[0] for j in jobs], time.time()
        stall, last, best, since, bad = 0, None, None, 0, []
        stuck = {j[0]: 0 for j in jobs}          # consecutive rounds this net has overlapped
        for rnd in range(rounds):
            if decay < 1.0:
                self.hist *= decay
            for n in todo:
                if n in routes:
                    self._stamp(n, routes[n][0], routes[n][1], -1)
                _, width, pads, opts = job[n]
                if relax and stuck[n]:
                    ease = min(stuck[n], relax) / float(relax)
                    opts = dict(opts, bias=int(round(opts.get('bias', 0) * (1 - ease))),
                                via_cost=max(150, int(opts['via_cost'] * (1 - 0.8 * ease))))
                routes[n] = self._route_tree(n, width, pads, price, layer_cost=layer_cost, **opts)
                self._stamp(n, routes[n][0], routes[n][1], +1)
            bad = [n for n, r in routes.items() if self._overlaps(n, job[n][1], r[2], r[3], scar)]
            for n in routes:
                stuck[n] = stuck[n] + 1 if n in bad else 0
            if log:
                log(f"    round {rnd + 1}: {len(todo)} net(s) routed, {len(bad)} overlap, price {price}, "
                    f"{time.time() - t0:.0f} s")
            if best is None or len(bad) < len(best[1]):
                best, since = (dict(routes), list(bad)), 0
            else:
                since += 1
            if not bad:
                break
            stall = stall + 1 if bad == last else 0
            last = bad
            if stall >= 12:                # the same nets, round after round: no price will part them
                break
            if since >= 8:                 # see the note below: the landscape has gone flat
                break
            price = int(price * rise) + 1
            todo = [j[0] for j in jobs if j[0] in bad]
        # KEEP THE BEST ROUND, NOT THE LAST. price * cnt * (1 + hist) saturates the int32 cap
        # once the price has climbed far enough, and from there every contested cell costs the
        # same: the search can no longer tell a busy corridor from a quiet one and the count
        # wanders instead of falling (TS06-MAIN went 11, 11, 11, 12, 13, 13, 17 over rounds
        # 16-22 while the price ran from 70 thousand to 1.2 million, 18.09.26). Eight rounds
        # without beating the best is taken as that, and the best round is what gets laid.
        if best is not None and len(best[1]) < len(bad):
            for n, r in routes.items():
                self._stamp(n, r[0], r[1], -1)
            routes = best[0]
            for n, r in routes.items():
                self._stamp(n, r[0], r[1], +1)
            if log:
                log(f"    kept the best round: {len(best[1])} overlap, not the last round's {len(bad)}")
        while True:                        # what still overlaps is taken out, worst first
            bad = {n: k for n, r in routes.items() for k in [self._overlaps(n, job[n][1], r[2], r[3])] if k}
            if not bad:
                break
            worst = max(bad, key=lambda n: (bad[n], n))
            spots = []
            self._overlaps(worst, job[worst][1], routes[worst][2], routes[worst][3], where=spots)
            self._stamp(worst, routes[worst][0], routes[worst][1], -1)
            self.failed.append((worst, "still overlapping another net when negotiation ended, e.g. at", spots[:3]))
            del routes[worst]
        if tighten:
            self._tighten(job, routes, tighten, log)
        for n, (segs, vias, cells, vcells, failed) in routes.items():
            self.failed += failed
            self._lay(n, segs, vias)
        self.use = None
        self.grp, self.bgrp = {}, {}

    def _tighten(self, job, routes, passes, log=None, price=10 ** 6, via_cost=2000):
        """Once nothing overlaps, the negotiation is finished but the copper is not. Each net is
        taken out of the overlap counts and routed again on its own, at a price no overlap can
        afford and with a via priced at 20 mm of track, and the new route is kept only if it is
        shorter - counting each via at its price - and still overlaps nothing.

        WHY: negotiate() stops the moment nothing overlaps, and has no opinion at all about the
        copper after that. A detour taken in round three round a net that moved away in round
        nine is otherwise frozen into the board for good. Ripping up is cheap here because a
        negotiated net lives in self.use rather than in the maps, so _stamp() undoes it exactly.
        """
        self.hist[:] = 0.0                 # scars are a device for parting nets, not for judging length
        worth = via_cost / 100.0           # what a via is worth in mm, for scoring
        def score(r):
            return seg_len(r[0]) + worth * len(r[1])
        for p in range(passes):
            gain, moved, dv, t0 = 0.0, 0, 0, time.time()
            for n in sorted(routes, key=lambda k: -score(routes[k])):
                old = routes[n]
                if old[4]:                 # a net that never fully routed is left alone
                    continue
                _, width, pads, opts = job[n]
                self._stamp(n, old[0], old[1], -1)
                new = self._route_tree(n, width, pads, price, **dict(opts, via_cost=via_cost))
                self._stamp(n, new[0], new[1], +1)
                keep = (not new[4] and self._overlaps(n, width, new[2], new[3]) == 0
                        and score(new) < score(old) - 0.05)
                if keep:
                    gain += score(old) - score(new)
                    dv += len(old[1]) - len(new[1])
                    moved += 1
                    routes[n] = new
                else:
                    self._stamp(n, new[0], new[1], -1)
                    self._stamp(n, old[0], old[1], +1)
            if log:
                log(f"    tighten pass {p + 1}: {moved} net(s) shortened, {gain:.0f} mm and "
                    f"{dv} via(s) saved, {time.time() - t0:.0f} s")
            if not moved:
                break
