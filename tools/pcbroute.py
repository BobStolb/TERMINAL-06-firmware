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
KEEP = VIA_DRILL / 2 + DRILL_GAP + SNAP                       # a new via centre from a drill's edge
DIRS = [(1, 0, 10), (-1, 0, 10), (0, 1, 10), (0, -1, 10), (1, 1, 14), (1, -1, 14), (-1, 1, 14), (-1, -1, 14)]
LAYER = ("F.Cu", "B.Cu")


def track_class(width):
    assert width <= 2 * CLASSES["wide"] + 1e-9, width
    return "narrow" if width <= 2 * CLASSES["narrow"] + 1e-9 else "wide"


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

    def connect(self, name, width, src, dst, via_cost=1500, turn=15, margin=6.0, allow=(0, 1), to_layer=None,
                reach=None):
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
            path = self._astar(net, hv, c, box, src, dst, targets, via_cost, turn, allow, to_layer, reach)
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
               soft=None, vsoft=None, nokeep=()):
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
        steps = [(dx + dy * w, dx, dy * w, dx, dy, cst, d) for d, (dx, dy, cst) in enumerate(DIRS)]
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
            for off, ox, oy, dx, dy, cst, d in steps:
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
    def _stamp(self, name, segs, vias, sign):
        """Add (+1) or take away (-1) one negotiated net's halos in the overlap counts."""
        keys = (("hvL", HV_CLR),) if name in self.hv else (("lvS", LV_CLR), ("lvL", HV_CLR))
        union = {}
        shapes = [((L,), ("seg", ax, ay, bx, by, w)) for L, ax, ay, bx, by, w in segs] + \
                 [((0, 1), ("circle", x, y, VIA_D / 2)) for x, y in vias]
        for layers, shape in shapes:
            win = self._dist(shape, REACH)
            if not win:
                continue
            j0, j1, i0, i1, D = win
            for c, r in CLASSES.items():
                for key, clr in keys:
                    m = D <= clr + r + SNAP
                    for L in layers:
                        u = union.get((c, key, L))
                        if u is None:
                            u = union[c, key, L] = np.zeros((self.ny, self.nx), bool)
                        u[j0:j1, i0:i1] |= m
        for (c, key, L), u in union.items():
            self.use[c, key][L] += sign * u.astype(np.int16)
        if vias:
            u = np.zeros((self.ny, self.nx), bool)
            for x, y in vias:
                j0, j1, i0, i1, D = self._dist(("circle", x, y, VIA_DRILL / 2), KEEP)
                u[j0:j1, i0:i1] |= D <= KEEP
            self.vuse += sign * u.astype(np.int16)

    def _soft(self, hv, c, box, price, layer_cost=(0, 0)):
        i0, i1, j0, j1 = box
        a, b = ("hvL", "lvL") if hv else ("lvS", "hvL")
        cnt = self.use[c, a][:, j0:j1, i0:i1].astype(np.int64) + self.use[c, b][:, j0:j1, i0:i1]
        vcnt = (self.use["via", a][:, j0:j1, i0:i1].astype(np.int64)
                + self.use["via", b][:, j0:j1, i0:i1]).max(0) + self.vuse[j0:j1, i0:i1]
        # history multiplies the present price (PathFinder): a cell shared round after round
        # becomes dearer than fresh ground, so two nets stuck on one spot are pushed apart
        # instead of keeping the cheapest overlap for ever
        hist = self.hist[:, j0:j1, i0:i1].astype(np.int64)
        vhist = hist.max(0)
        cap = 1 << 30                      # stays an int32 inside the search however high the price climbs
        lc = np.array(layer_cost, np.int64)[:, None, None]
        return (np.minimum(price * cnt * (1 + hist) + 10 * hist + lc, cap),
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

    def _route_tree(self, name, width, pads, price, layer_cost=(0, 0), via_cost=1500, turn=15, allow=(0, 1)):
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
                soft, vsoft = self._soft(hv, c, box, price, layer_cost)
                path = self._astar(net, hv, c, box, src, near, targets, via_cost, turn, allow,
                                   soft=soft, vsoft=vsoft, nokeep=vias)
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

    def negotiate(self, jobs, rounds=60, price=3, rise=1.4, scar=1, layer_cost=(0, 0), log=None):
        """jobs: [(name, width, pads, opts)], routed together against everything already laid.
        layer_cost: extra cost of each step on F.Cu and on B.Cu (a plain step costs 10) - how a
        face kept for a pour is made the second choice rather than forbidden."""
        self.use = {k: np.zeros(v.shape, np.int16) for k, v in self.maps.items()}
        self.vuse = np.zeros((self.ny, self.nx), np.int16)
        self.hist = np.zeros((2, self.ny, self.nx), np.int32)
        job = {j[0]: j for j in jobs}
        routes, todo, t0 = {}, [j[0] for j in jobs], time.time()
        stall, last = 0, None
        for rnd in range(rounds):
            for n in todo:
                if n in routes:
                    self._stamp(n, routes[n][0], routes[n][1], -1)
                _, width, pads, opts = job[n]
                routes[n] = self._route_tree(n, width, pads, price, layer_cost=layer_cost, **opts)
                self._stamp(n, routes[n][0], routes[n][1], +1)
            bad = [n for n, r in routes.items() if self._overlaps(n, job[n][1], r[2], r[3], scar)]
            if log:
                log(f"    round {rnd + 1}: {len(todo)} net(s) routed, {len(bad)} overlap, price {price}, "
                    f"{time.time() - t0:.0f} s")
            if not bad:
                break
            stall = stall + 1 if bad == last else 0
            last = bad
            if stall >= 12:                # the same nets, round after round: no price will part them
                break
            price = int(price * rise) + 1
            todo = [j[0] for j in jobs if j[0] in bad]
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
        for n, (segs, vias, cells, vcells, failed) in routes.items():
            self.failed += failed
            self._lay(n, segs, vias)
        self.use = None
