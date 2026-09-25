#!/usr/bin/env python3
"""A router that never places a via: every net is grown as a tree, one connection at a time,
each connection on ONE copper face.

WHY IT CAN WORK WITHOUT VIAS. On a through-hole board every pad is copper on both faces. So a
net may change face at any of its own pads - and nowhere else. The router therefore never
changes face inside a connection: it joins the net's pieces one by one, each join a single-face
path from one piece's copper to another's, and chooses per join the face that is cheaper. A
three-pad net can run pad A to pad B on the front and pad B to pad C on the back, and the pad
in the middle is the layer change the previous boards spent a via on.

HOW IT DECIDES WHERE COPPER MAY GO. Not from a raster of the copper: for every cell of the
search window the exact distance to every nearby item of every other net is taken (pads as the
shapes they are, tracks as capsules), and a cell is open only if the track centred on it keeps
the class clearance - 0.6 mm to anything high-voltage, the class value otherwise. Board.check()
and KiCad's DRC then re-verify the result independently.

HOW IT SEARCHES. Octilinear A* in C (tools/astar.c, built on first use), with a price per 45
degrees of turn and no turn sharper than 90 degrees, from every cell of the growing piece to
every cell of the others - so a join can leave from the middle of an existing track, which is
where a person would tee in. A small extra price near other copper keeps tracks off each other
when there is room. If no C compiler is available the same search runs in Python, slowly.

    R = NetRouter(board)
    R.route("SDA", layers=("B.Cu",))        # returns [] when done, else the pieces left over
"""
import ctypes, heapq, os, subprocess, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbkit as K

HERE = os.path.dirname(os.path.abspath(__file__))
LAYERS = ("F.Cu", "B.Cu")


def _load_c():
    import hashlib
    src = os.path.join(HERE, "astar.c")
    tag = hashlib.sha1(open(src, "rb").read()).hexdigest()[:10]
    out = os.path.join(HERE, "__pycache__", f"astar_{tag}.so")     # one file per source version
    try:
        if not os.path.exists(out):
            os.makedirs(os.path.dirname(out), exist_ok=True)
            subprocess.run(["cc", "-O2", "-shared", "-fPIC", "-o", out, src], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        lib = ctypes.CDLL(out)
        lib.astar.restype = ctypes.c_int
        P = np.ctypeslib.ndpointer
        lib.astar.argtypes = [ctypes.c_int, ctypes.c_int, P(np.float32, flags="C"), P(np.uint8, flags="C"),
                              P(np.uint8, flags="C"), P(np.float32, flags="C"), ctypes.c_int, ctypes.c_int,
                              ctypes.c_int, ctypes.c_int, ctypes.c_float, P(np.float32, flags="C"),
                              P(np.int32, flags="C"), ctypes.c_int]
        return lib
    except Exception:
        return None


_C = _load_c()
DX = [1, 1, 0, -1, -1, -1, 0, 1]
DY = [0, 1, 1, 1, 0, -1, -1, -1]


def _astar_py(nx, ny, cost, src, goal, hgrid, x0, y0, x1, y1, turn45, dirmul):
    """The C search, line for line, for machines without a compiler."""
    best, prev, pq = {}, {}, []
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            c = y * nx + x
            if src[c]:
                best[(c, 8)] = 0.0
                prev[(c, 8)] = None
                heapq.heappush(pq, (hgrid[c], 0.0, c, 8))
    closed = set()
    while pq:
        f, g, c, d = heapq.heappop(pq)
        if (c, d) in closed:
            continue
        closed.add((c, d))
        if goal[c] and not src[c]:
            path, s = [], (c, d)
            while s is not None:
                path.append(s[0])
                s = prev[s]
            return path[::-1]
        x, y = c % nx, c // nx
        for k in range(8):
            pen = 0.0
            if d < 8:
                dd = abs(k - d)
                dd = 8 - dd if dd > 4 else dd
                if dd > 2:
                    continue
                pen = turn45 * dd
            X, Y = x + DX[k], y + DY[k]
            if X < x0 or X > x1 or Y < y0 or Y > y1:
                continue
            C = Y * nx + X
            if cost[C] < 0:
                continue
            if DX[k] and DY[k] and (cost[y * nx + X] < 0 or cost[Y * nx + x] < 0):
                continue
            step = (1.41421356 if DX[k] and DY[k] else 1.0) * dirmul[k]
            ng = g + step * (1.0 + cost[C]) + pen
            if ng < best.get((C, k), 1e30):
                best[(C, k)] = ng
                prev[(C, k)] = (c, d)
                heapq.heappush(pq, (ng + hgrid[C], ng, C, k))
    return []


def _heuristic(gmask, dmul):
    """A* lower bound: the distance to the nearest goal cell. When a diagonal step costs at least
    two straight ones, the taxicab distance is still a lower bound and a far tighter one than the
    straight line, so the search expands a fraction of the cells."""
    from scipy.ndimage import distance_transform_edt as edt, distance_transform_cdt as cdt
    if min(dmul[1::2]) * 1.41421356 >= 2.0 - 1e-6 and min(dmul[0::2]) >= 1.0:
        return cdt(~gmask, metric="taxicab").astype(np.float32)
    return edt(~gmask).astype(np.float32)


class NetRouter:
    G = 0.1

    def __init__(self, board, hv_class="HV", margin=0.012, near=0.35, near_cost=0.6, turn45=2.0,
                 edge=0.5, hole_clr=0.3):
        self.B = board
        self.nx, self.ny = int(round(board.W / self.G)) + 1, int(round(board.H / self.G)) + 1
        self.hv, self.margin, self.near, self.near_cost = hv_class, margin, near, near_cost
        self.turn45, self.edge, self.hole_clr = turn45, edge, hole_clr
        self.clr = {k: c for k, c, _ in board.classes}
        self.log = []
        self.locked = set()                 # nets whose copper is never ripped up
        self.fixed = set()                  # hand-laid tracks: never ripped, always hard
        self.pen0 = 40.0                    # price per cell of passing over a rippable net
        self.dirmul = {}                    # layer -> 8 step-cost multipliers (E SE S SW W NW N NE)

    # ------------------------------------------------------------------ geometry
    def _items(self, layer):
        """Every copper item on a face: (net, pts, radius, kind, obj)."""
        out = []
        for p in self.B.pads:
            if p.kind == "np_thru_hole" or not p.on(layer):
                continue
            pts, r = p.geom()
            out.append((p.net or f"NC:{p.ref}.{p.name}", pts, r, "pad", p))
        for t in self.B.tracks:
            net, ly, a, b, w = t
            if ly == layer:
                out.append((net, [a, b], w / 2, "trk", t))
        return out

    def need(self, n1, n2):
        c1, c2 = self.B.cls(n1), self.B.cls(n2)
        if self.hv in (c1, c2):
            return self.clr[self.hv]
        return max(self.clr[c1], self.clr[c2])

    def slack(self, net, layer, w, win, soft_pen=None, fixed_only=False):
        """For every cell of the window: how far a track of width w centred there is from
        violating a clearance (negative = blocked), capped at `near`. With soft_pen, the tracks
        of nets that are not locked do not block: they add soft_pen[net] to a second array,
        the price of ripping that net up to pass there."""
        i0, j0, i1, j1 = win
        G = self.G
        X = (np.arange(i0, i1 + 1) * G)[None, :]
        Y = (np.arange(j0, j1 + 1) * G)[:, None]
        s = np.full((j1 - j0 + 1, i1 - i0 + 1), self.near, np.float32)
        soft = np.zeros_like(s) if soft_pen is not None else None
        half = w / 2
        for n, pts, r, kind, obj in self._items(layer):
            if n == net:
                continue
            if fixed_only and kind == "trk" and obj not in self.fixed:
                continue
            is_soft = soft is not None and kind == "trk" and n not in self.locked and obj not in self.fixed
            reach = r + self.need(net, n) + half + self.margin + self.near
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            a0 = max(i0, int((min(xs) - reach) / G))
            a1 = min(i1, int((max(xs) + reach) / G) + 1)
            b0 = max(j0, int((min(ys) - reach) / G))
            b1 = min(j1, int((max(ys) + reach) / G) + 1)
            if a0 > a1 or b0 > b1:
                continue
            xx = X[:, a0 - i0:a1 - i0 + 1]
            yy = Y[b0 - j0:b1 - j0 + 1, :]
            d = K._dist_field(np, np.broadcast_to(xx, (yy.shape[0], xx.shape[1])),
                              np.broadcast_to(yy, (yy.shape[0], xx.shape[1])), pts) - r
            v = d - (self.need(net, n) + half + self.margin)
            if is_soft:
                sub = soft[b0 - j0:b1 - j0 + 1, a0 - i0:a1 - i0 + 1]
                sub[v < 0] = np.maximum(sub[v < 0], soft_pen.get(n, self.pen0))
                continue
            sub = s[b0 - j0:b1 - j0 + 1, a0 - i0:a1 - i0 + 1]
            np.minimum(sub, v, out=sub)
        # the board edge, holes, keep-outs
        e = self.edge + half + self.margin
        s = np.minimum(s, np.minimum(np.minimum(X - e, self.B.W - e - X), np.minimum(Y - e, self.B.H - e - Y)).astype(np.float32))
        for hx, hy, hd in self.B.holes + [(p.x, p.y, p.drill) for p in self.B.pads if p.kind == "np_thru_hole"]:
            v = np.hypot(X - hx, Y - hy) - (hd / 2 + self.hole_clr + half + self.margin)
            np.minimum(s, v, out=s)
        for ko in self.B.keepouts:
            x0, y0, x1, y1, ly = ko[:5]
            nets = ko[5] if len(ko) > 5 else None          # nets the keep-out lets through
            if ly in (layer, "*") and (nets is None or net not in nets):
                inside = (X > x0 - half) & (X < x1 + half) & (Y > y0 - half) & (Y < y1 + half)
                s[inside] = -1
        return (s, soft) if soft_pen is not None else s

    def own(self, net, layer, win, members):
        """Mask of the window covered by the given items of this net on this face."""
        i0, j0, i1, j1 = win
        G = self.G
        X = (np.arange(i0, i1 + 1) * G)[None, :]
        Y = (np.arange(j0, j1 + 1) * G)[:, None]
        m = np.zeros((j1 - j0 + 1, i1 - i0 + 1), bool)
        for pts, r in members:
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            a0 = max(i0, int((min(xs) - r) / G) - 1)
            a1 = min(i1, int((max(xs) + r) / G) + 1)
            b0 = max(j0, int((min(ys) - r) / G) - 1)
            b1 = min(j1, int((max(ys) + r) / G) + 1)
            if a0 > a1 or b0 > b1:
                continue
            xx = X[:, a0 - i0:a1 - i0 + 1]
            yy = Y[b0 - j0:b1 - j0 + 1, :]
            d = K._dist_field(np, np.broadcast_to(xx, (yy.shape[0], xx.shape[1])),
                              np.broadcast_to(yy, (yy.shape[0], xx.shape[1])), pts)
            m[b0 - j0:b1 - j0 + 1, a0 - i0:a1 - i0 + 1] |= d <= max(r - 0.05, 0.0)
        return m

    # ------------------------------------------------------------------ pieces of a net
    def pieces(self, net):
        """The net's copper grouped into connected pieces: [(set of pad keys, [items])]."""
        items = []
        for p in self.B.pads:
            if p.net == net and p.kind != "np_thru_hole":
                ls = {"F.Cu", "B.Cu"} if p.thru else {l for l in LAYERS if p.on(l)}
                items.append((ls, p.geom(), ("pad", p.ref, p.name)))
        for t in self.B.tracks:
            if t[0] == net:
                items.append(({t[1]}, ([t[2], t[3]], t[4] / 2), ("trk", t)))
        n = len(items)
        par = list(range(n))

        def f(i):
            while par[i] != i:
                par[i] = par[par[i]]
                i = par[i]
            return i
        for i in range(n):
            for j in range(i + 1, n):
                if items[i][0] & items[j][0] and K.dist(items[i][1], items[j][1]) <= 1e-3:
                    par[f(i)] = f(j)
        groups = {}
        for i in range(n):
            groups.setdefault(f(i), []).append(items[i])
        return sorted(groups.values(), key=lambda g: -len(g))

    # ------------------------------------------------------------------ one join
    def join(self, net, src, dst, layer, width=None, window=10.0, avoid=None, soft_pen=None):
        """Route one single-face path from any copper of piece src to any copper of the pieces
        in dst. Returns (cost, points) without adding it, or None."""
        G = self.G
        w = width or self.B.width(net)
        sm = [it[1] for it in src if layer in it[0]]
        dm = [it[1] for d in dst for it in d if layer in it[0]]
        if not sm or not dm:
            return None
        allp = [p for g in sm + dm for p in g[0]]
        i0 = max(0, int((min(p[0] for p in allp) - window) / G))
        i1 = min(self.nx - 1, int((max(p[0] for p in allp) + window) / G) + 1)
        j0 = max(0, int((min(p[1] for p in allp) - window) / G))
        j1 = min(self.ny - 1, int((max(p[1] for p in allp) + window) / G) + 1)
        win = (i0, j0, i1, j1)
        if soft_pen is not None:
            s, soft = self.slack(net, layer, w, win, soft_pen)
        else:
            s, soft = self.slack(net, layer, w, win), None
        smask = self.own(net, layer, win, sm)
        gmask = self.own(net, layer, win, dm)
        cost = np.where(s < 0, -1.0, self.near_cost * np.clip(1.0 - s / self.near, 0, 1)).astype(np.float32)
        if soft is not None:
            cost = np.where(cost < 0, cost, cost + soft).astype(np.float32)
        if avoid is not None:
            cost[avoid[j0:j1 + 1, i0:i1 + 1]] = -1
        # a join may start and end inside its own copper, whatever the clearance field says there
        cost[smask | gmask] = np.maximum(cost[smask | gmask], 0)
        from scipy.ndimage import distance_transform_edt as edt
        h = _heuristic(gmask, self.dirmul.get(layer, [1.0] * 8))
        wx, wy = i1 - i0 + 1, j1 - j0 + 1
        cst = np.ascontiguousarray(cost.reshape(-1))
        sr = np.ascontiguousarray(smask.reshape(-1).astype(np.uint8))
        gl = np.ascontiguousarray(gmask.reshape(-1).astype(np.uint8))
        hg = np.ascontiguousarray(h.reshape(-1))
        dm = np.ascontiguousarray(np.array(self.dirmul.get(layer, [1.0] * 8), np.float32))
        if _C is not None:
            out = np.zeros(wx * wy, np.int32)
            n = _C.astar(wx, wy, cst, sr, gl, hg, 0, 0, wx - 1, wy - 1, self.turn45, dm, out, len(out))
            cells = list(out[:n]) if n > 0 else []
        else:
            cells = _astar_py(wx, wy, cst, sr, gl, hg, 0, 0, wx - 1, wy - 1, self.turn45, dm)
        if not cells:
            return None
        pts = [((c % wx + i0) * G, (c // wx + j0) * G) for c in cells]
        tot = sum(1.0 + cst[c] for c in cells)
        return tot, self._corners(pts), (sm, dm)

    @staticmethod
    def _corners(pts):
        out = [pts[0]]
        for a, b, c in zip(pts, pts[1:], pts[2:]):
            d1 = (round((b[0] - a[0]) * 10), round((b[1] - a[1]) * 10))
            d2 = (round((c[0] - b[0]) * 10), round((c[1] - b[1]) * 10))
            if d1 != d2:
                out.append(b)
        out.append(pts[-1])
        return [(round(x, 4), round(y, 4)) for x, y in out]

    def _end_on(self, net, layer, e, nxt):
        """Where a path ending at e (coming from nxt) should really end: the centre of the pad
        it is inside, or the point on the centre line of the track it has run into."""
        for p in self.B.pads:
            if p.net == net and p.on(layer) and K.dist(([e], 0), p.geom()) <= 1e-6:
                return (p.x, p.y), True
        best = None
        for t in self.B.tracks:
            if t[0] != net or t[1] != layer:
                continue
            a, b, w = t[2], t[3], t[4]
            if K.pt_seg(e, a, b) > w / 2 + 1e-6:
                continue
            # run on along the path's own direction until the centre line is reached
            dx, dy = e[0] - nxt[0], e[1] - nxt[1]
            L = (dx * dx + dy * dy) ** 0.5 or 1.0
            dx, dy = dx / L, dy / L
            ex, ey = b[0] - a[0], b[1] - a[1]
            den = dx * ey - dy * ex
            if abs(den) > 1e-9:
                t_ = ((a[0] - e[0]) * ey - (a[1] - e[1]) * ex) / den
                u_ = ((a[0] - e[0]) * dy - (a[1] - e[1]) * dx) / den
                if -w <= t_ <= w and -1e-9 <= u_ <= 1 + 1e-9:
                    q = (round(e[0] + dx * t_, 4), round(e[1] + dy * t_, 4))
                    if best is None or abs(t_) < best[1]:
                        best = (q, abs(t_))
                    continue
            # parallel, or the run misses the segment: the nearest point of it
            L2 = ex * ex + ey * ey or 1e-12
            u = max(0.0, min(1.0, ((e[0] - a[0]) * ex + (e[1] - a[1]) * ey) / L2))
            q = (round(a[0] + u * ex, 4), round(a[1] + u * ey, 4))
            dd = ((q[0] - e[0]) ** 2 + (q[1] - e[1]) ** 2) ** 0.5
            if best is None or dd < best[1]:
                best = (q, dd)
        return (best[0] if best else e), False

    def _snap(self, net, layer, pts):
        if len(pts) < 2:
            return pts
        s, pad_s = self._end_on(net, layer, pts[0], pts[1])
        e, pad_e = self._end_on(net, layer, pts[-1], pts[-2])
        pts = list(pts)
        if pad_s:
            pts = [s] + pts
        else:
            pts[0] = s
        if pad_e:
            pts = pts + [e]
        else:
            pts[-1] = e
        out = [pts[0]]
        for p in pts[1:]:
            if abs(p[0] - out[-1][0]) > 1e-6 or abs(p[1] - out[-1][1]) > 1e-6:
                out.append(p)
        return out

    def victims(self, net, layer, pts, w):
        """The nets whose tracks a new path would come too close to."""
        out = set()
        segs = list(zip(pts, pts[1:]))
        for t in self.B.tracks:
            n2, ly, a, b, w2 = t
            if ly != layer or n2 == net or t in self.fixed:
                continue
            need = self.need(net, n2) + w / 2 + w2 / 2 - 1e-6
            for c, d in segs:
                if K.dist(([c, d], 0), ([a, b], 0)) < need:
                    out.add(n2)
                    break
        return out

    # ------------------------------------------------------------------ a whole net
    def _best_join(self, net, ps, layers, width, window, avoid, soft_pen):
        src, dst = ps[0], ps[1:]
        best = None
        for ly in layers:
            for win in (window, window * 3):
                r = self.join(net, src, dst, ly, width, win, avoid, soft_pen)
                if r is not None:
                    if best is None or r[0] < best[0]:
                        best = (r[0], ly, r[1])
                    break
        if best is None:
            for k in range(1, len(ps)):
                src2, dst2 = ps[k], ps[:k] + ps[k + 1:]
                for ly in layers:
                    r = self.join(net, src2, dst2, ly, width, window * 3, avoid, soft_pen)
                    if r is not None and (best is None or r[0] < best[0]):
                        best = (r[0], ly, r[1])
                if best is not None:
                    break
        return best

    def route(self, net, layers=LAYERS, width=None, window=10.0, avoid=None, max_joins=200, soft_pen=None):
        """Join the net's pieces until it is one piece. Returns (pieces left, nets ripped up)."""
        ripped = set()
        w = width or self.B.width(net)
        for _ in range(max_joins):
            ps = self.pieces(net)
            if len(ps) <= 1:
                return [], ripped
            best = self._best_join(net, ps, layers, width, window, avoid, None)
            if best is None and soft_pen is not None:
                best = self._best_join(net, ps, layers, width, window, avoid, soft_pen)
                if best is not None:
                    pts = self._snap(net, best[1], best[2])
                    vs = self.victims(net, best[1], pts, w) - self.locked
                    for v in vs:
                        self.unroute(v)
                    ripped |= vs
            if best is None:
                self.log.append(f"{net}: {len(ps)} pieces left")
                return ps, ripped
            pts = self._snap(net, best[1], best[2])
            self.B.track(net, best[1], pts, width)
        return self.pieces(net), ripped

    def unroute(self, net):
        self.B.tracks = [t for t in self.B.tracks if t[0] != net or t in self.fixed]

    def route_all(self, order, layers=None, widths=None, max_rips=400, verbose=True):
        """Route every net in order; a net that will not go through tears up whichever nets
        are in its way (never a locked one), and those go to the back of the queue. The price
        of tearing a net up grows each time it happens, so two nets cannot keep evicting each
        other for ever."""
        from collections import deque, Counter
        layers = layers or {}
        widths = widths or {}
        q = deque(order)
        rips = Counter()
        pen = {}
        failed = []
        total = 0
        while q:
            n = q.popleft()
            left, ripped = self.route(n, layers.get(n, LAYERS), widths.get(n), soft_pen=pen)
            for v in ripped:
                rips[v] += 1
                total += 1
                pen[v] = self.pen0 * (1 + 2 * rips[v])
                if v not in q:
                    q.append(v)
            if verbose and ripped:
                print(f"  {n}: ripped up {' '.join(sorted(ripped))}", flush=True)
            if left:
                failed.append(n)
                if verbose:
                    print(f"  {n}: {len(left)} pieces left", flush=True)
            if total > max_rips:
                failed += list(q)
                break
        return [n for n in failed if len(self.pieces(n)) > 1]

    def polish(self, nets, layers=None, widths=None, passes=1, verbose=False):
        """Tidy what route_all found: take each net up and route it again with everything else
        in place. The new copper can only be as long or shorter, since the old path is still
        free for it, and the detours the first, greedy pass took around nets that are no longer
        there straighten out. A net that will not go back is restored as it was."""
        layers = layers or {}
        widths = widths or {}
        for _ in range(passes):
            better = 0
            for n in nets:
                old = [t for t in self.B.tracks if t[0] == n]
                if not old:
                    continue
                L0 = sum(((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5 for _, _, a, b, _ in old)
                self.unroute(n)
                left, _ = self.route(n, layers.get(n, LAYERS), widths.get(n))
                new = [t for t in self.B.tracks if t[0] == n]
                L1 = sum(((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5 for _, _, a, b, _ in new)
                if left or L1 > L0 + 1e-6:
                    self.unroute(n)
                    self.B.tracks += old
                elif L1 < L0 - 0.05:
                    better += 1
                    if verbose:
                        print(f"  {n}: {L0:.1f} -> {L1:.1f} mm", flush=True)
            if verbose:
                print(f"polish pass: {better} nets shorter", flush=True)


class Negotiator:
    """Negotiated-congestion routing (PathFinder, McMurchie & Ebeling 1995) on top of NetRouter.

    The greedy rip-up in NetRouter.route_all evicts whole nets and can cycle for ever when a few
    nets compete for the same gaps. Here every net is routed every round and may overlap other
    nets' copper, at a price: `pres` for sharing now (raised every round) plus a history cost
    that grows wherever sharing persists. Nets spread out until nothing is shared. Only what
    never moves is a hard obstacle - pads, hand-laid copper, holes, the edge, keep-outs - and that
    is computed once per net and face and cached, so a round costs little more than the searches.
    Clearance between routed nets is negotiated on a raster; the final result is checked exactly
    (conflicts()), and Board.check / KiCad's DRC verify it again."""

    def __init__(self, router, order, widths=None, layers=None):
        self.R, self.B = router, router.B
        self.order = list(order)
        self.widths = widths or {}
        self.layers = layers or {}
        ny, nx = router.ny, router.nx
        self.hist = {ly: np.zeros((ny, nx), np.float32) for ly in LAYERS}
        self.cu = {(ly, g): np.zeros((ny, nx), np.int16) for ly in LAYERS for g in ("std", "hv")}
        self.cache = {}
        self.pres = 0.6
        self.hist_step = 1.0

    def w(self, net):
        return self.widths.get(net) or self.B.width(net)

    def group(self, net):
        return "hv" if self.B.cls(net) == self.R.hv else "std"

    # -------------------------------------------------------------- static obstacles
    def hard(self, net, layer):
        key = (net, layer)
        if key not in self.cache:
            R = self.R
            s = R.slack(net, layer, self.w(net), (0, 0, R.nx - 1, R.ny - 1), fixed_only=True)
            self.cache[key] = (np.packbits(s < 0, axis=None), np.packbits(s < R.near / 2, axis=None))
        pb, pn = self.cache[key]
        shape, count = (self.R.ny, self.R.nx), self.R.ny * self.R.nx
        blocked = np.unpackbits(pb, count=count).reshape(shape).astype(bool)
        near = np.unpackbits(pn, count=count).reshape(shape).astype(np.float32) * (self.R.near_cost * 0.5)
        return blocked, near

    # -------------------------------------------------------------- routed copper on the raster
    def paint(self, net, sign):
        G = self.R.G
        g = self.group(net)
        for t in self.B.tracks:
            n, ly, a, b, w = t
            if n != net or t in self.R.fixed:
                continue
            r = w / 2
            i0, i1 = int((min(a[0], b[0]) - r) / G) - 1, int((max(a[0], b[0]) + r) / G) + 2
            j0, j1 = int((min(a[1], b[1]) - r) / G) - 1, int((max(a[1], b[1]) + r) / G) + 2
            i0, j0 = max(i0, 0), max(j0, 0)
            i1, j1 = min(i1, self.R.nx), min(j1, self.R.ny)
            X = (np.arange(i0, i1) * G)[None, :]
            Y = (np.arange(j0, j1) * G)[:, None]
            d = K._dist_field(np, np.broadcast_to(X, (j1 - j0, i1 - i0)), np.broadcast_to(Y, (j1 - j0, i1 - i0)), [a, b])
            self.cu[(ly, g)][j0:j1, i0:i1] += (d <= r + 0.05).astype(np.int16) * sign

    def unroute(self, net):
        self.paint(net, -1)
        self.R.unroute(net)

    # -------------------------------------------------------------- one net
    def join(self, net, src, dst, layer, window):
        from scipy.ndimage import distance_transform_edt as edt
        R, G = self.R, self.R.G
        w = self.w(net)
        sm = [it[1] for it in src if layer in it[0]]
        dm = [it[1] for d in dst for it in d if layer in it[0]]
        if not sm or not dm:
            return None
        allp = [p for gg in sm + dm for p in gg[0]]
        i0 = max(0, int((min(p[0] for p in allp) - window) / G))
        i1 = min(R.nx - 1, int((max(p[0] for p in allp) + window) / G) + 1)
        j0 = max(0, int((min(p[1] for p in allp) - window) / G))
        j1 = min(R.ny - 1, int((max(p[1] for p in allp) + window) / G) + 1)
        win = (i0, j0, i1, j1)
        blocked, near = self.hard(net, layer)
        blocked = blocked[j0:j1 + 1, i0:i1 + 1]
        cost = near[j0:j1 + 1, i0:i1 + 1].astype(np.float32) + self.hist[layer][j0:j1 + 1, i0:i1 + 1]
        # sharing with other routed nets: within clearance of their copper
        mine = self.group(net)
        c_std = max(R.clr[self.B.cls(net)], max(c for k, c, _ in self.B.classes if k != R.hv)) if mine == "std" else R.clr[R.hv]
        for g, clr in (("std", c_std), ("hv", R.clr[R.hv])):
            occ = self.cu[(layer, g)][j0:j1 + 1, i0:i1 + 1] > 0
            if occ.any():
                d = edt(~occ) * G
                cost += self.pres * (d < w / 2 + clr + R.margin + G * 0.75)
        cost[blocked] = -1
        smask = R.own(net, layer, win, sm)
        gmask = R.own(net, layer, win, dm)
        cost[smask | gmask] = np.maximum(cost[smask | gmask], 0)
        h = _heuristic(gmask, R.dirmul.get(layer, [1.0] * 8))
        wx, wy = i1 - i0 + 1, j1 - j0 + 1
        cst = np.ascontiguousarray(cost.reshape(-1).astype(np.float32))
        sr = np.ascontiguousarray(smask.reshape(-1).astype(np.uint8))
        gl = np.ascontiguousarray(gmask.reshape(-1).astype(np.uint8))
        hg = np.ascontiguousarray(h.reshape(-1))
        dmul = np.ascontiguousarray(np.array(R.dirmul.get(layer, [1.0] * 8), np.float32))
        if _C is not None:
            out = np.zeros(wx * wy, np.int32)
            n = _C.astar(wx, wy, cst, sr, gl, hg, 0, 0, wx - 1, wy - 1, R.turn45, dmul, out, len(out))
            cells = list(out[:n]) if n > 0 else []
        else:
            cells = _astar_py(wx, wy, cst, sr, gl, hg, 0, 0, wx - 1, wy - 1, R.turn45, dmul)
        if not cells:
            return None
        pts = [((c % wx + i0) * G, (c // wx + j0) * G) for c in cells]
        tot = sum(1.0 + cst[c] for c in cells)
        return tot, R._corners(pts)

    def route(self, net, window=10.0):
        R = self.R
        self.unroute(net)
        layers = self.layers.get(net, LAYERS)
        for _ in range(300):
            ps = R.pieces(net)
            if len(ps) <= 1:
                break
            best = None
            for k in range(len(ps)):
                src, dst = ps[k], ps[:k] + ps[k + 1:]
                for ly in layers:
                    for win in (window, window * 3, 400.0):
                        r = self.join(net, src, dst, ly, win)
                        if r is not None:
                            if best is None or r[0] < best[0]:
                                best = (r[0], ly, r[1])
                            break
                if best is not None:
                    break
            if best is None:
                break
            pts = R._snap(net, best[1], best[2])
            self.B.track(net, best[1], pts, self.widths.get(net))
        self.paint(net, +1)
        return len(R.pieces(net)) <= 1

    # -------------------------------------------------------------- what is still shared
    def conflicts(self):
        """Exact clearance conflicts between routed tracks of different nets: {net: [segments]}."""
        out = {}
        R = self.R
        Gb = 3.0
        for ly in LAYERS:
            segs = [t for t in self.B.tracks if t[1] == ly]
            grid = {}
            for idx, (n, _, a, b, w) in enumerate(segs):
                for gx in range(int(min(a[0], b[0]) // Gb) - 1, int(max(a[0], b[0]) // Gb) + 2):
                    for gy in range(int(min(a[1], b[1]) // Gb) - 1, int(max(a[1], b[1]) // Gb) + 2):
                        grid.setdefault((gx, gy), []).append(idx)
            seen = set()
            for cell in grid.values():
                for x in range(len(cell)):
                    for y in range(x + 1, len(cell)):
                        i, j = cell[x], cell[y]
                        if (i, j) in seen:
                            continue
                        seen.add((i, j))
                        ti, tj = segs[i], segs[j]
                        if ti[0] == tj[0] or (ti in R.fixed and tj in R.fixed):
                            continue
                        need = R.need(ti[0], tj[0]) + ti[4] / 2 + tj[4] / 2 - 1e-6
                        if K.dist(([ti[2], ti[3]], 0), ([tj[2], tj[3]], 0)) < need:
                            for t in (ti, tj):
                                if t not in R.fixed:
                                    out.setdefault(t[0], []).append(t)
        return out

    def run(self, rounds=60, verbose=True):
        import time
        t0 = time.time()
        for n in self.order:
            self.route(n)
        for k in range(rounds):
            con = self.conflicts()
            unrouted = [n for n in self.order if len(self.R.pieces(n)) > 1]
            if verbose:
                print(f"round {k}: {len(con)} nets sharing, {len(unrouted)} unrouted, pres {self.pres:.1f}, "
                      f"{time.time() - t0:.0f}s", flush=True)
            if not con and not unrouted:
                return []
            # history where sharing persists
            G = self.R.G
            for n, ts in con.items():
                for (_, ly, a, b, w) in ts:
                    L = max(abs(b[0] - a[0]), abs(b[1] - a[1]))
                    steps = max(1, int(L / G))
                    for s_ in range(steps + 1):
                        x = a[0] + (b[0] - a[0]) * s_ / steps
                        y = a[1] + (b[1] - a[1]) * s_ / steps
                        i, j = int(round(x / G)), int(round(y / G))
                        self.hist[ly][max(0, j - 3):j + 4, max(0, i - 3):i + 4] += self.hist_step
            self.pres *= 1.5
            for n in self.order:
                if n in con or n in unrouted:
                    self.route(n)
        return sorted(set(self.conflicts()) | {n for n in self.order if len(self.R.pieces(n)) > 1})
