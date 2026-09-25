#!/usr/bin/env python3
"""pcbkit: place parts, draw copper deliberately, write a KiCad 10 board, check it.

WHY THIS EXISTS. Every board before TS06-DISP / TS06-DRV (THT pair) was laid by a row packer
and routed by an A* grid router (tools/pcbroute.py). The router found legal copper and never
good copper: 476 vias on the first TS06-MAIN, 177 on the through-hole one, a ground pour in
hundreds of islands and no grain at all (Claude outputs/TS06-routing-study.md). The lesson of
that study was that the placement decides the wiring, and the lesson of the inherited
AlexGyver board is what a board looks like when a person decides both: its tube half carries
the ten-line cathode bus threaded through four sockets on ONE copper layer, no vias at all.

So this kit does not route. It gives a generator the means to say exactly where copper goes:

  * parts are placed by coordinate, pre-rotated in 90 degree steps and optionally flipped to
    the back, from the project library (PCB/lib/TS06.pretty) - no rotation token is ever
    written, which is what tools/checkpcb.py and tools/checkcopper.py expect;
  * copper is drawn as polylines, net and layer stated; a through-hole pad is copper on both
    faces, so a net may change face at any of its OWN pads - that, and only that, is how a
    board built with this kit changes layer. write() refuses to emit a via;
  * check() measures clearance between every pair of copper items on each face with the
    clearance class of the two nets, and proves every net is one connected piece; the
    generator runs it before writing, and KiCad's own DRC runs after;
  * plot() draws the copper of both faces as a PNG, the thing a person actually looks at.

Coordinates are KiCad's: millimetres, x right, y DOWN, seen from the front.
"""
import math, os, uuid, zlib, struct
import sexp as S

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PRETTY = os.path.join(ROOT, "PCB", "lib", "TS06.pretty")
VER, GEN, GENV = 20260206, "pcbnew", "10.0"

FLIP = {"F.Cu": "B.Cu", "F.SilkS": "B.SilkS", "F.Mask": "B.Mask", "F.Paste": "B.Paste",
        "F.Fab": "B.Fab", "F.CrtYd": "B.CrtYd", "F.Adhes": "B.Adhes"}
FLIP.update({v: k for k, v in list(FLIP.items())})


# ======================================================================== footprints
def _rot(x, y, r):
    """Rotate (x, y) by r degrees counter-clockwise as seen on screen (y down)."""
    r %= 360
    if r == 0:
        return x, y
    if r == 90:
        return y, -x
    if r == 180:
        return -x, -y
    if r == 270:
        return -y, x
    a = math.radians(r)
    return x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a)


class Pad:
    __slots__ = ("name", "kind", "shape", "x", "y", "w", "h", "drill", "layers", "net", "ref", "rr")

    def __init__(self, **k):
        for a in self.__slots__:
            setattr(self, a, k.get(a))

    @property
    def thru(self):
        return self.kind == "thru_hole"

    def on(self, layer):
        if self.kind == "np_thru_hole":
            return False
        return any(l in ("*.Cu", "F&B.Cu") or l == layer for l in self.layers)

    def geom(self):
        """(points, radius): the pad as a convex point set grown by a radius. A circle is one
        point, an oval a segment, a rectangle four corners, a rounded rectangle the inset
        rectangle grown by its corner radius - exact for every shape used here."""
        hw, hh = self.w / 2, self.h / 2
        if self.shape == "circle":
            return [(self.x, self.y)], hw
        if self.shape == "oval":
            if hw >= hh:
                d = hw - hh
                return [(self.x - d, self.y), (self.x + d, self.y)], hh
            d = hh - hw
            return [(self.x, self.y - d), (self.x, self.y + d)], hw
        r = min(hw, hh) * 2 * (self.rr or 0) if self.shape == "roundrect" else 0.0
        return [(self.x - hw + r, self.y - hh + r), (self.x + hw - r, self.y - hh + r),
                (self.x + hw - r, self.y + hh - r), (self.x - hw + r, self.y + hh - r)], r


class Footprint:
    """A library footprint, rotated and optionally flipped to the back, as a tree ready to be
    written into a board, plus the geometry the kit needs: pads and the courtyard box."""

    def __init__(self, name, rot=0, back=False, lib=PRETTY):
        self.name, self.rot, self.back = name, rot % 360, back
        t = S.parse(open(os.path.join(lib, name + ".kicad_mod"), encoding="utf8").read())
        self.tree = self._transform(t)
        self.pads, self.court = [], None
        xs, ys = [], []
        for n in S.walk(self.tree):
            if n[0] == "pad":
                at, sz = S.find(n, "at"), S.find(n, "size")
                dr = S.find(n, "drill")
                drill = None
                if dr:
                    v = [a for a in dr[1:] if not isinstance(a, list) and a != "oval"]
                    drill = float(v[0]) if v else None
                ly = S.find(n, "layers")
                rr = S.find(n, "roundrect_rratio")
                self.pads.append(Pad(name=S.unq(n[1]), kind=n[2], shape=n[3], x=float(at[1]), y=float(at[2]),
                                     w=float(sz[1]), h=float(sz[2]), drill=drill,
                                     layers=[S.unq(a) for a in ly[1:]] if ly else [],
                                     rr=float(rr[1]) if rr else None))
            elif n[0] in ("fp_line", "fp_rect", "fp_circle", "fp_poly"):
                ly = S.find(n, "layer")
                if ly and S.unq(ly[1]).endswith("CrtYd"):
                    if n[0] == "fp_circle":
                        c, e = S.find(n, "center"), S.find(n, "end")
                        r = math.hypot(float(e[1]) - float(c[1]), float(e[2]) - float(c[2]))
                        xs += [float(c[1]) - r, float(c[1]) + r]
                        ys += [float(c[2]) - r, float(c[2]) + r]
                    else:
                        for k in ("start", "end"):
                            p = S.find(n, k)
                            if p:
                                xs.append(float(p[1]))
                                ys.append(float(p[2]))
                        pts = S.find(n, "pts")
                        if pts:
                            for xy in S.find_all(pts, "xy"):
                                xs.append(float(xy[1]))
                                ys.append(float(xy[2]))
        if xs:
            self.court = (min(xs), min(ys), max(xs), max(ys))
        else:
            e = [(p.x - p.w / 2, p.y - p.h / 2, p.x + p.w / 2, p.y + p.h / 2) for p in self.pads]
            self.court = (min(a[0] for a in e) - 0.25, min(a[1] for a in e) - 0.25,
                          max(a[2] for a in e) + 0.25, max(a[3] for a in e) + 0.25)

    # ------------------------------------------------------------------ transform
    def _pt(self, x, y):
        x, y = _rot(x, y, self.rot)
        if self.back:
            x = -x
        return x, y

    def _transform(self, t):
        rot, back = self.rot, self.back

        def fix_xy(n, i=1):
            x, y = self._pt(float(n[i]), float(n[i + 1]))
            n[i], n[i + 1] = S.num(x), S.num(y)

        def visit(n, ctx):
            head = n[0] if n and not isinstance(n[0], list) else None
            if head == "pad":
                at = S.find(n, "at")
                a = float(at[3]) if len(at) > 3 else 0.0
                fix_xy(at)
                a = (a + rot) % 360
                if back:
                    a = (-a) % 360
                shape = n[3]
                sz = S.find(n, "size")
                dr = S.find(n, "drill")
                if a % 90 == 0 and shape in ("circle", "rect", "oval", "roundrect"):
                    if a % 180 == 90:
                        sz[1], sz[2] = sz[2], sz[1]
                        if dr and "oval" in dr:
                            i = dr.index("oval")
                            dr[i + 1], dr[i + 2] = dr[i + 2], dr[i + 1]
                    del at[3:]
                else:
                    del at[3:]
                    at.append(S.num(a))
                for c in n:
                    if isinstance(c, list):
                        if c[0] in ("layers",) and back:
                            c[1:] = [S.q(FLIP.get(S.unq(l), S.unq(l))) for l in c[1:]]
                        elif c[0] == "offset":          # drill offset
                            fix_xy(c)
                        elif c[0] == "primitives":
                            visit(c, "prim")
                return
            if head in ("at",) and ctx in ("text",):
                fix_xy(n)
                return
            if head in ("start", "end", "center", "mid") and ctx in ("gfx", "prim"):
                fix_xy(n)
                return
            if head == "xy" and ctx in ("gfx", "prim"):
                fix_xy(n)
                return
            if head in ("layer",) and back and len(n) > 1:
                n[1] = S.q(FLIP.get(S.unq(n[1]), S.unq(n[1])))
                return
            if head == "layers" and back:
                n[1:] = [S.q(FLIP.get(S.unq(l), S.unq(l))) for l in n[1:]]
                return
            if head == "model":
                off = S.find(n, "offset")
                if off:
                    xyz = S.find(off, "xyz")
                    x, y = _rot(float(xyz[1]), float(xyz[2]), rot)
                    xyz[1], xyz[2] = S.num(x), S.num(y)
                ro = S.find(n, "rotate")
                if ro:
                    xyz = S.find(ro, "xyz")
                    xyz[3] = S.num((float(xyz[3]) - rot) % 360)
                return
            sub = ctx
            if head in ("fp_line", "fp_rect", "fp_circle", "fp_arc", "fp_poly", "fp_curve"):
                sub = "gfx"
            elif head in ("property", "fp_text", "fp_text_box"):
                sub = "text"
                if back:
                    eff = S.find(n, "effects")
                    if eff is not None and S.find(eff, "justify") is None:
                        eff.append(["justify", "mirror"])
                    elif eff is not None:
                        j = S.find(eff, "justify")
                        if "mirror" not in j:
                            j.append("mirror")
            for c in n:
                if isinstance(c, list):
                    visit(c, sub)

        for c in t:
            if isinstance(c, list):
                if c[0] == "layer" and back:
                    c[1] = S.q(FLIP.get(S.unq(c[1]), S.unq(c[1])))
                else:
                    visit(c, "top")
        return t


# ======================================================================== geometry
def seg_seg(a, b, c, d):
    """Distance between segments ab and cd."""
    if _intersect(a, b, c, d):
        return 0.0
    return min(pt_seg(a, c, d), pt_seg(b, c, d), pt_seg(c, a, b), pt_seg(d, a, b))


def pt_seg(p, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    if L == 0:
        return math.hypot(p[0] - ax, p[1] - ay)
    t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L))
    return math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy)


def _orient(a, b, c):
    v = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    return 0 if abs(v) < 1e-12 else (1 if v > 0 else -1)


def _intersect(a, b, c, d):
    o1, o2, o3, o4 = _orient(a, b, c), _orient(a, b, d), _orient(c, d, a), _orient(c, d, b)
    return o1 != o2 and o3 != o4 and o1 != 0 and o2 != 0 and o3 != 0 and o4 != 0


def _inside(p, poly):
    if len(poly) < 3:
        return False
    s = None
    for i in range(len(poly)):
        o = _orient(poly[i], poly[(i + 1) % len(poly)], p)
        if o == 0:
            continue
        if s is None:
            s = o
        elif o != s:
            return False
    return True


def dist(ga, gb):
    """Distance between two (points, radius) shapes, 0 if they overlap."""
    pa, ra = ga
    pb, rb = gb
    ea = [(pa[i], pa[(i + 1) % len(pa)]) for i in range(len(pa))] if len(pa) > 1 else [(pa[0], pa[0])]
    eb = [(pb[i], pb[(i + 1) % len(pb)]) for i in range(len(pb))] if len(pb) > 1 else [(pb[0], pb[0])]
    if len(pa) > 2 and _inside(pb[0], pa) or len(pb) > 2 and _inside(pa[0], pb):
        return 0.0
    m = min(seg_seg(a, b, c, d) for a, b in ea for c, d in eb)
    return max(0.0, m - ra - rb)


# ======================================================================== the board
class Board:
    def __init__(self, name, w, h, parts, classes, default=("Default", 0.2, 0.25), ns=None):
        """parts: {ref: Part-like with .pins {pad: net}, .value}. classes: [(name, clearance,
        width, [net patterns])] - a trailing * in a pattern matches a prefix."""
        self.name, self.W, self.H = name, w, h
        self.parts = parts
        self.classes = [default] + [c[:3] for c in classes]
        self._cls_pat = [(c[0], c[3]) for c in classes]
        self.NS = uuid.UUID(ns) if ns else uuid.uuid5(uuid.NAMESPACE_URL, "ts06/" + name)
        self.placed = {}            # ref -> (Footprint, x, y)
        self.pads = []              # every copper pad, absolute
        self.tracks = []            # (net, layer, (x1,y1), (x2,y2), width)
        self.zones = []
        self.holes = []             # (x, y, d)  unplated
        self.gfx = []               # (kind, layer, data)
        self.outline = [(0, 0), (w, 0), (w, h), (0, h)]
        self.keepouts = []
        self.hide_refs = True       # references are placed by hand, as text, where they fit
        self.ref_at = {}            # ref -> (dx, dy, angle, size): a reference shown on the silk
        self.thickness = 1.6

    # ------------------------------------------------------------------ nets and classes
    def cls(self, net):
        for name, pats in self._cls_pat:
            for p in pats:
                if net == p or (p.endswith("*") and net and net.startswith(p[:-1])):
                    return name
        return self.classes[0][0]

    def clearance(self, n1, n2):
        c = {k: v for k, v, _ in self.classes}
        return max(c[self.cls(n1)], c[self.cls(n2)])

    def width(self, net):
        return {k: w for k, _, w in self.classes}[self.cls(net)]

    # ------------------------------------------------------------------ placement
    def place(self, ref, fp, x, y, rot=0, back=False):
        f = Footprint(fp, rot, back)
        self.placed[ref] = (f, round(x, 4), round(y, 4))
        part = self.parts.get(ref)
        for p in f.pads:
            net = part.pins.get(p.name) if part is not None else None
            self.pads.append(Pad(name=p.name, kind=p.kind, shape=p.shape, x=round(x + p.x, 4), y=round(y + p.y, 4),
                                 w=p.w, h=p.h, drill=p.drill, layers=p.layers, net=net, ref=ref, rr=p.rr))
        return f

    def pad(self, ref, name):
        for p in self.pads:
            if p.ref == ref and p.name == str(name):
                return p
        raise KeyError(f"{ref}.{name}")

    def P(self, ref, name):
        p = self.pad(ref, name)
        return (p.x, p.y)

    def court(self, ref):
        f, x, y = self.placed[ref]
        c = f.court
        return (x + c[0], y + c[1], x + c[2], y + c[3])

    # ------------------------------------------------------------------ copper
    def track(self, net, layer, pts, width=None):
        w = width or self.width(net)
        pts = [(round(a, 4), round(b, 4)) for a, b in pts]
        for a, b in zip(pts, pts[1:]):
            if a != b:
                self.tracks.append((net, layer, a, b, w))

    def zone(self, net, layer, poly=None, clearance=0.5, min_th=0.25, gap=0.5, bridge=0.5,
             priority=0, pads="thru_hole_only", keep_islands=False):
        self.zones.append(dict(net=net, layer=layer, poly=poly or [(0.5, 0.5), (self.W - 0.5, 0.5),
                               (self.W - 0.5, self.H - 0.5), (0.5, self.H - 0.5)],
                               clearance=clearance, min_th=min_th, gap=gap, bridge=bridge,
                               priority=priority, pads=pads, keep=keep_islands))

    def hole(self, x, y, d=3.2):
        self.holes.append((x, y, d))

    def text(self, t, x, y, layer, size=1.0, thick=None, mirror=None, rot=0, justify=None):
        if mirror is None:
            mirror = layer.startswith("B.")
        self.gfx.append(("text", layer, (t, x, y, size, thick or round(size * 0.15, 3), mirror, rot, justify)))

    def line(self, x0, y0, x1, y1, layer, width=0.15):
        self.gfx.append(("line", layer, (x0, y0, x1, y1, width)))

    def rect(self, x0, y0, x1, y1, layer, width=0.15):
        for a, b, c, d in ((x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)):
            self.line(a, b, c, d, layer, width)

    def circle(self, x, y, r, layer, width=0.15):
        self.gfx.append(("circle", layer, (x, y, r, width)))

    # ------------------------------------------------------------------ checking
    def items(self, layer):
        """Every copper item on a face: (net, geom, kind, label)."""
        out = []
        for p in self.pads:
            if p.on(layer):
                out.append((p.net or f"NC:{p.ref}.{p.name}", p.geom(), "pad", f"{p.ref}.{p.name}"))
        for net, ly, a, b, w in self.tracks:
            if ly == layer:
                out.append((net, ([a, b], w / 2), "trk", f"{net} {a}->{b}"))
        return out

    def check(self, pad_hv=0.8, hv_class="HV", hole_clr=0.3, edge_clr=0.5, verbose=True):
        """Clearance on each face, hole and edge clearance, and one-piece connectivity of every
        net that is not carried by a zone. Returns a list of problems."""
        bad = []
        for layer in ("F.Cu", "B.Cu"):
            its = self.items(layer)
            grid = {}
            G = 4.0
            boxes = []
            for i, (net, (pts, r), kind, lab) in enumerate(its):
                x0 = min(p[0] for p in pts) - r
                x1 = max(p[0] for p in pts) + r
                y0 = min(p[1] for p in pts) - r
                y1 = max(p[1] for p in pts) + r
                boxes.append((x0, y0, x1, y1))
                for gx in range(int(x0 // G) - 1, int(x1 // G) + 2):
                    for gy in range(int(y0 // G) - 1, int(y1 // G) + 2):
                        grid.setdefault((gx, gy), []).append(i)
            seen = set()
            for cell in grid.values():
                for ii in range(len(cell)):
                    for jj in range(ii + 1, len(cell)):
                        i, j = cell[ii], cell[jj]
                        if (i, j) in seen:
                            continue
                        seen.add((i, j))
                        ni, gi, ki, li = its[i]
                        nj, gj, kj, lj = its[j]
                        if ni == nj:
                            continue
                        need = self.clearance(ni, nj)
                        if ki == "pad" and kj == "pad" and (self.cls(ni) == hv_class or self.cls(nj) == hv_class):
                            if li.split(".")[0] != lj.split(".")[0]:
                                need = max(need, pad_hv)
                        bi, bj = boxes[i], boxes[j]
                        if bi[0] - need > bj[2] or bj[0] - need > bi[2] or bi[1] - need > bj[3] or bj[1] - need > bi[3]:
                            continue
                        d = dist(gi, gj)
                        if d < need - 1e-6:
                            bad.append(f"[{layer}] {li}  vs  {lj}: {d:.3f} < {need}")
            # tracks against unplated holes and the board edge
            for net, (pts, r), kind, lab in its:
                if kind != "trk":
                    continue
                for hx, hy, hd in self.holes + [(p.x, p.y, p.drill) for p in self.pads if p.kind == "np_thru_hole"]:
                    if pt_seg((hx, hy), pts[0], pts[1]) - r - hd / 2 < hole_clr - 1e-6:
                        bad.append(f"[{layer}] {lab} too close to hole at ({hx},{hy})")
                for (ax, ay), (bx, by) in zip(self.outline, self.outline[1:] + self.outline[:1]):
                    for p in pts:
                        if pt_seg(p, (ax, ay), (bx, by)) - r < edge_clr - 1e-6:
                            bad.append(f"[{layer}] {lab} within {edge_clr} of the edge")
                            break
        bad += self.connectivity()
        if verbose:
            for b in bad[:80]:
                print("  [CHECK]", b)
            if len(bad) > 80:
                print(f"  ... and {len(bad) - 80} more")
        return bad

    def connectivity(self):
        """Every net that has pads and no zone must be ONE piece of copper: pads and tracks
        joined where they touch on a common face, and a through-hole pad joining both faces."""
        zoned = {z["net"] for z in self.zones}
        items = []                              # (net, layer set, geom)
        for p in self.pads:
            if p.net and p.kind != "np_thru_hole":
                ls = {"F.Cu", "B.Cu"} if p.thru else {l for l in ("F.Cu", "B.Cu") if p.on(l)}
                items.append((p.net, ls, p.geom(), f"{p.ref}.{p.name}"))
        for net, ly, a, b, w in self.tracks:
            items.append((net, {ly}, ([a, b], w / 2), None))
        par = list(range(len(items)))

        def f(i):
            while par[i] != i:
                par[i] = par[par[i]]
                i = par[i]
            return i
        bynet = {}
        for i, it in enumerate(items):
            bynet.setdefault(it[0], []).append(i)
        bad = []
        for net, idx in bynet.items():
            for a in range(len(idx)):
                for b in range(a + 1, len(idx)):
                    i, j = idx[a], idx[b]
                    if items[i][1] & items[j][1] and dist(items[i][2], items[j][2]) <= 1e-4:
                        par[f(i)] = f(j)
            if net in zoned:
                continue
            roots = {f(i) for i in idx}
            if len(roots) > 1:
                pieces = {}
                for i in idx:
                    if items[i][3]:
                        pieces.setdefault(f(i), []).append(items[i][3])
                desc = " | ".join(" ".join(sorted(v)) for v in pieces.values())
                bad.append(f"net {net} is in {len(roots)} pieces: {desc}")
        # a track end must land on something of its own net
        for net, ly, a, b, w in self.tracks:
            for e in (a, b):
                ok = False
                for p in self.pads:
                    if p.net == net and p.on(ly) and dist(([e], 0), p.geom()) <= 1e-4:
                        ok = True
                        break
                if not ok:
                    for n2, l2, c, d, w2 in self.tracks:
                        if n2 == net and l2 == ly and (c, d) != (a, b) and pt_seg(e, c, d) <= 1e-4:
                            ok = True
                            break
                if not ok:
                    bad.append(f"[{ly}] {net}: track end {e} lands on nothing")
        return bad

    # ------------------------------------------------------------------ writing
    @staticmethod
    def _silk_on_pad(node, f, clr=0.15):
        """True for a library silkscreen line, arc or circle that runs within clr of one of its
        own pads. The fab clips such silk anyway; dropping it here keeps KiCad's DRC honest."""
        if not isinstance(node, list) or node[0] not in ("fp_line", "fp_circle", "fp_arc", "fp_rect"):
            return False
        ly = S.find(node, "layer")
        if not ly or not S.unq(ly[1]).endswith("SilkS"):
            return False
        pts = []
        if node[0] in ("fp_line", "fp_rect"):
            a, b = S.find(node, "start"), S.find(node, "end")
            a, b = (float(a[1]), float(a[2])), (float(b[1]), float(b[2]))
            corners = [a, b] if node[0] == "fp_line" else [a, (b[0], a[1]), b, (a[0], b[1]), a]
            for p0, p1 in zip(corners, corners[1:]):
                n = max(2, int(math.hypot(p1[0] - p0[0], p1[1] - p0[1]) / 0.1))
                pts += [(p0[0] + (p1[0] - p0[0]) * i / n, p0[1] + (p1[1] - p0[1]) * i / n) for i in range(n + 1)]
        elif node[0] == "fp_circle":
            c, e = S.find(node, "center"), S.find(node, "end")
            cx, cy = float(c[1]), float(c[2])
            r = math.hypot(float(e[1]) - cx, float(e[2]) - cy)
            pts = [(cx + r * math.cos(t / 60 * math.tau), cy + r * math.sin(t / 60 * math.tau)) for t in range(60)]
        else:
            for k in ("start", "mid", "end"):
                q = S.find(node, k)
                pts.append((float(q[1]), float(q[2])))
        st = S.find(node, "stroke")
        w = float(S.find(st, "width")[1]) / 2 if st and S.find(st, "width") else 0.06
        for p in f.pads:
            if p.kind == "np_thru_hole":
                continue
            g = p.geom()
            for q in pts:
                if dist(([q], w), g) < clr:
                    return True
        return False

    def U(self, s):
        return str(uuid.uuid5(self.NS, s))

    def nets(self):
        ns = set()
        for p in self.pads:
            if p.net:
                ns.add(p.net)
        for t in self.tracks:
            ns.add(t[0])
        for z in self.zones:
            ns.add(z["net"])
        return [""] + sorted(ns)

    def write(self, path, title=None, rev="A", date=None, comment=None):
        nets = self.nets()
        NI = {n: i for i, n in enumerate(nets)}
        out = []
        o = out.append
        o(f'(kicad_pcb\n\t(version {VER})\n\t(generator "{GEN}")\n\t(generator_version "{GENV}")')
        o(f'\t(general\n\t\t(thickness {S.num(self.thickness)})\n\t\t(legacy_teardrops no)\n\t)')
        o('\t(paper "A4")')
        tb = [f'\t\t(title {S.q(title or self.name)})', f'\t\t(rev {S.q(rev)})']
        if date:
            tb.append(f'\t\t(date {S.q(date)})')
        tb.append('\t\t(company "TERMINAL-06")')
        if comment:
            tb.append(f'\t\t(comment 1 {S.q(comment)})')
        o('\t(title_block\n' + "\n".join(tb) + '\n\t)')
        o('\n'.join(['\t(layers', '\t\t(0 "F.Cu" signal)', '\t\t(2 "B.Cu" signal)',
                     '\t\t(9 "F.Adhes" user "F.Adhesive")', '\t\t(11 "B.Adhes" user "B.Adhesive")',
                     '\t\t(13 "F.Paste" user)', '\t\t(15 "B.Paste" user)',
                     '\t\t(5 "F.SilkS" user "F.Silkscreen")', '\t\t(7 "B.SilkS" user "B.Silkscreen")',
                     '\t\t(1 "F.Mask" user)', '\t\t(3 "B.Mask" user)',
                     '\t\t(17 "Dwgs.User" user "User.Drawings")', '\t\t(19 "Cmts.User" user "User.Comments")',
                     '\t\t(21 "Eco1.User" user "User.Eco1")', '\t\t(23 "Eco2.User" user "User.Eco2")',
                     '\t\t(25 "Edge.Cuts" user)', '\t\t(27 "Margin" user)',
                     '\t\t(31 "F.CrtYd" user "F.Courtyard")', '\t\t(29 "B.CrtYd" user "B.Courtyard")',
                     '\t\t(35 "F.Fab" user)', '\t\t(33 "B.Fab" user)', '\t)']))
        stack = ['(stackup',
                 '(layer "F.SilkS" (type "Top Silk Screen") (color "White"))',
                 '(layer "F.Mask" (type "Top Solder Mask") (color "Black") (thickness 0.01))',
                 '(layer "F.Cu" (type "copper") (thickness 0.035))',
                 '(layer "dielectric 1" (type "core") (thickness %s) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))' % S.num(self.thickness - 0.09),
                 '(layer "B.Cu" (type "copper") (thickness 0.035))',
                 '(layer "B.Mask" (type "Bottom Solder Mask") (color "Black") (thickness 0.01))',
                 '(layer "B.SilkS" (type "Bottom Silk Screen") (color "White"))',
                 '(copper_finish "ENIG")', '(dielectric_constraints no))']
        o('\t(setup\n' + S.dump(S.parse(" ".join(stack)), 2) + '\n\t\t(pad_to_mask_clearance 0)\n\t\t(allow_soldermask_bridges_in_footprints no)\n'
          '\t\t(tenting\n\t\t\t(front yes)\n\t\t\t(back yes)\n\t\t)\n\t)')
        for i, n in enumerate(nets):
            o(f'\t(net {i} {S.q(n)})')
        # footprints
        for ref in sorted(self.placed, key=_refkey):
            f, x, y = self.placed[ref]
            part = self.parts.get(ref)
            t = [c for c in f.tree if not self._silk_on_pad(c, f)]
            body = []
            layer = "B.Cu" if f.back else "F.Cu"
            for c in t[2:]:
                if not isinstance(c, list):
                    continue
                if c[0] in ("version", "generator", "generator_version", "layer"):
                    continue
                if c[0] == "property":
                    c = [x_ for x_ in c]
                    key = S.unq(c[1])
                    if key == "Reference":
                        c[2] = S.q(ref)
                        if ref in self.ref_at:
                            # placed by the generator: on the silkscreen of the part's own face,
                            # at a chosen offset, size and angle
                            dx, dy, rot, size = self.ref_at[ref]
                            silk = "B.SilkS" if f.back else "F.SilkS"
                            th = round(size * 0.15, 3)
                            eff = ["effects", ["font", ["size", S.num(size), S.num(size)], ["thickness", S.num(th)]]]
                            if f.back:
                                eff.append(["justify", "mirror"])
                            c = ["property", c[1], c[2], ["at", S.num(dx), S.num(dy), S.num(rot)],
                                 ["layer", S.q(silk)], ["uuid", '""'], eff]
                        elif self.hide_refs and S.find(c, "hide") is None:
                            c.insert(4, ["hide", "yes"])
                    elif key == "Value":
                        c[2] = S.q(part.value if part is not None else f.name)
                    c = _with_uuid(c, self.U(ref + "prop" + key))
                elif c[0] == "pad":
                    c = [x_ for x_ in c]
                    nm = S.unq(c[1])
                    net = part.pins.get(nm) if part is not None else None
                    c = [x_ for x_ in c if not (isinstance(x_, list) and x_[0] in ("net", "uuid"))]
                    if net:
                        # insert the net right after (layers ...), where KiCad writes it
                        k = next(i for i, x_ in enumerate(c) if isinstance(x_, list) and x_[0] == "layers") + 1
                        c.insert(k, ["net", str(NI[net]), S.q(net)])
                    c.append(["uuid", S.q(self.U(f"{ref}.pad.{nm}.{len(body)}"))])
                elif isinstance(c, list) and S.find(c, "uuid") is not None:
                    c = _with_uuid([x_ for x_ in c], self.U(f"{ref}.{c[0]}.{len(body)}"))
                body.append(c)
            node = ["footprint", S.q("TS06:" + self.libname(f)), ["layer", S.q(layer)], ["uuid", S.q(self.U("fp" + ref))],
                    ["at", S.num(x), S.num(y)]] + body
            o(S.dump(node, 1))
        # holes as footprints, as KiCad's own MountingHole does
        placed_holes = {(x, y) for f, x, y in self.placed.values() if "MountingHole" in f.name}
        for i, (hx, hy, hd) in enumerate(self.holes):
            if (round(hx, 4), round(hy, 4)) in placed_holes:
                continue
            o(S.dump(["footprint", '"TS06:MountingHole"', ["layer", '"F.Cu"'], ["uuid", S.q(self.U(f"hole{i}"))],
                      ["at", S.num(hx), S.num(hy)],
                      ["property", '"Reference"', S.q(f"H{i + 1}"), ["at", "0", S.num(-hd / 2 - 1)],
                       ["layer", '"F.Fab"'], ["hide", "yes"], ["uuid", S.q(self.U(f"hole{i}ref"))],
                       ["effects", ["font", ["size", "0.8", "0.8"], ["thickness", "0.12"]]]],
                      ["attr", "exclude_from_pos_files", "exclude_from_bom"],
                      ["pad", '""', "np_thru_hole", "circle", ["at", "0", "0"], ["size", S.num(hd), S.num(hd)],
                       ["drill", S.num(hd)], ["layers", '"F&B.Cu"', '"*.Mask"'], ["uuid", S.q(self.U(f"hole{i}pad"))]],
                      ["fp_circle", ["center", "0", "0"], ["end", S.num(hd / 2 + 1.85), "0"],
                       ["stroke", ["width", "0.05"], ["type", "solid"]], ["fill", "no"], ["layer", '"F.CrtYd"'],
                       ["uuid", S.q(self.U(f"hole{i}crt"))]]], 1))
        # outline
        ol = self.outline
        for i in range(len(ol)):
            (x0, y0), (x1, y1) = ol[i], ol[(i + 1) % len(ol)]
            o(S.dump(["gr_line", ["start", S.num(x0), S.num(y0)], ["end", S.num(x1), S.num(y1)],
                      ["stroke", ["width", "0.1"], ["type", "solid"]], ["layer", '"Edge.Cuts"'],
                      ["uuid", S.q(self.U(f"edge{i}"))]], 1))
        for k, (kind, layer, d) in enumerate(self.gfx):
            if kind == "line":
                x0, y0, x1, y1, w = d
                o(S.dump(["gr_line", ["start", S.num(x0), S.num(y0)], ["end", S.num(x1), S.num(y1)],
                          ["stroke", ["width", S.num(w)], ["type", "solid"]], ["layer", S.q(layer)],
                          ["uuid", S.q(self.U(f"gl{k}"))]], 1))
            elif kind == "circle":
                x, y, r, w = d
                o(S.dump(["gr_circle", ["center", S.num(x), S.num(y)], ["end", S.num(x + r), S.num(y)],
                          ["stroke", ["width", S.num(w)], ["type", "solid"]], ["fill", "no"], ["layer", S.q(layer)],
                          ["uuid", S.q(self.U(f"gc{k}"))]], 1))
            elif kind == "text":
                t, x, y, size, th, mirror, rot, just = d
                eff = ["effects", ["font", ["size", S.num(size), S.num(size)], ["thickness", S.num(th)]]]
                js = []
                if just:
                    js.append(just)
                if mirror:
                    js.append("mirror")
                if js:
                    eff.append(["justify"] + js)
                o(S.dump(["gr_text", S.q(t), ["at", S.num(x), S.num(y), S.num(rot)], ["layer", S.q(layer)],
                          ["uuid", S.q(self.U(f"gt{k}{t}"))], eff], 1))
        for k, (net, layer, a, b, w) in enumerate(self.tracks):
            o(f'\t(segment\n\t\t(start {S.num(a[0])} {S.num(a[1])})\n\t\t(end {S.num(b[0])} {S.num(b[1])})\n'
              f'\t\t(width {S.num(w)})\n\t\t(layer "{layer}")\n\t\t(net {NI[net]})\n\t\t(uuid "{self.U("seg%d" % k)}")\n\t)')
        for k, z in enumerate(self.zones):
            pts = "\n".join("\t\t\t\t(xy %s %s)" % (S.num(x), S.num(y)) for x, y in z["poly"])
            o(f'\t(zone\n\t\t(net {NI[z["net"]]})\n\t\t(net_name {S.q(z["net"])})\n\t\t(layers "{z["layer"]}")\n'
              f'\t\t(uuid "{self.U("zone%d" % k)}")\n\t\t(name {S.q(z["net"])})\n\t\t(hatch edge 0.5)\n'
              + (f'\t\t(priority {z["priority"]})\n' if z["priority"] else "")
              + f'\t\t(connect_pads {z["pads"]}\n\t\t\t(clearance {S.num(z["clearance"])})\n\t\t)\n'
              f'\t\t(min_thickness {S.num(z["min_th"])})\n\t\t(filled_areas_thickness no)\n'
              f'\t\t(fill\n\t\t\t(thermal_gap {S.num(z["gap"])})\n\t\t\t(thermal_bridge_width {S.num(z["bridge"])})\n'
              f'\t\t\t(island_removal_mode {1 if z["keep"] else 0})\n\t\t)\n'
              f'\t\t(polygon\n\t\t\t(pts\n{pts}\n\t\t\t)\n\t\t)\n\t)')
        text = "\n".join(out) + "\n\t(embedded_fonts no)\n)\n"
        assert "(via" not in text, "this kit never writes a via"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf8", newline="\n") as fh:
            fh.write(text)
        return len(nets) - 1

    def write_library(self):
        """Write every rotated variant this board uses into the project library, as the repo has
        always done (_R90 and friends), so KiCad can match each placed footprint to a library
        footprint. A back-side part is stored as its FRONT variant: KiCad flips a library
        footprint onto the back itself, and compares by flipping it back."""
        done = set()
        for ref, (f, x, y) in self.placed.items():
            r = self.librot(f)
            if r == 0 or (f.name, r) in done:
                continue
            done.add((f.name, r))
            v = Footprint(f.name, r, False)
            t = v.tree
            t[1] = S.q(f"{f.name}_R{r}")
            d = S.find(t, "descr")
            if d:
                d[1] = S.q(S.unq(d[1]) + f" Rotated {r} degrees, written by tools/pcbkit.py.")
            with open(os.path.join(PRETTY, f"{f.name}_R{r}.kicad_mod"), "w", encoding="utf8", newline="\n") as fh:
                fh.write(S.dump(t) + "\n")

    @staticmethod
    def librot(f):
        """The library variant a placed footprint is a copy of. KiCad stores a flipped footprint
        as its library geometry mirrored TOP-TO-BOTTOM and turned 180 degrees; this kit mirrors
        LEFT-TO-RIGHT at 0 degrees, which is the same copper and the same library footprint
        turned a further 180 degrees - so that is the variant a back-side part names."""
        return (f.rot + 180) % 360 if f.back else f.rot

    def libname(self, f):
        r = self.librot(f)
        return f.name if r == 0 else f"{f.name}_R{r}"

    def write_project(self, path, extra_classes=True):
        """A .kicad_pro carrying the net classes, so KiCad's own DRC holds the high-voltage
        clearance too - the previous boards' projects had only Default at 0.2 mm, which meant
        the 0.6 mm rule was enforced by tools/checkcopper.py and by nothing KiCad ran."""
        import json
        classes = []
        for i, (n, c, w) in enumerate(self.classes):
            classes.append({"bus_width": 12, "clearance": c, "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25,
                            "diff_pair_width": 0.2, "line_style": 0, "microvia_diameter": 0.3, "microvia_drill": 0.1,
                            "name": n, "pcb_color": "rgba(0, 0, 0, 0.000)",
                            "priority": 2147483647 if n == "Default" else i,
                            "schematic_color": "rgba(0, 0, 0, 0.000)", "track_width": w, "tuning_profile": "",
                            "via_diameter": 0.6, "via_drill": 0.3, "wire_width": 6})
        pats = [{"netclass": n, "pattern": p} for n, ps in self._cls_pat for p in ps]
        pro = {"board": {"design_settings": {"defaults": {}, "rules": {
            "min_clearance": 0.2, "min_copper_edge_clearance": 0.5, "min_hole_clearance": 0.25,
            "min_hole_to_hole": 0.25, "min_track_width": 0.2, "min_through_hole_diameter": 0.3,
            "min_via_diameter": 0.5, "min_via_annular_width": 0.1, "min_silk_clearance": 0.0,
            "min_text_height": 0.8, "min_text_thickness": 0.08, "min_resolved_spokes": 2}}},
            "meta": {"filename": os.path.basename(path), "version": 3},
            "net_settings": {"classes": classes, "meta": {"version": 5}, "net_colors": None,
                             "netclass_assignments": None, "netclass_patterns": pats}}
        with open(path, "w", encoding="utf8", newline="\n") as fh:
            json.dump(pro, fh, indent=2)
        d = os.path.dirname(path)
        with open(os.path.join(d, "fp-lib-table"), "w", encoding="utf8", newline="\n") as fh:
            fh.write('(fp_lib_table\n  (version 7)\n  (lib (name "TS06")(type "KiCad")(uri "${KIPRJMOD}/../lib/TS06.pretty")'
                     '(options "")(descr "TERMINAL-06 project footprints"))\n)\n')

    # ------------------------------------------------------------------ looking
    def plot(self, path, ppm=8, color=None):
        """Copper of both faces, front above and back below, the back seen THROUGH the board
        (not mirrored) so a track can be followed from one panel to the other."""
        W, H = int(self.W * ppm) + 1, int(self.H * ppm) + 1
        gap = 12
        img = [[(20, 24, 30)] * W for _ in range(2 * H + gap)]
        color = color or (lambda n: (87, 217, 121))

        def disc(ox, x, y, r, c):
            cx, cy, rr = x * ppm, y * ppm + ox, r * ppm
            for yy in range(int(cy - rr) - 1, int(cy + rr) + 2):
                for xx in range(int(cx - rr) - 1, int(cx + rr) + 2):
                    if 0 <= xx < W and 0 <= yy < len(img) and (xx - cx) ** 2 + (yy - cy) ** 2 <= rr * rr:
                        img[yy][xx] = c

        def seg(ox, a, b, r, c):
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            n = max(1, int(L * ppm / max(1.0, r * ppm * 0.7)))
            for i in range(n + 1):
                t = i / n
                disc(ox, a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, r, c)
        for k, layer in enumerate(("F.Cu", "B.Cu")):
            ox = k * (H + gap)
            for net, ly, a, b, w in self.tracks:
                if ly == layer:
                    seg(ox, a, b, w / 2, color(net))
            for p in self.pads:
                if p.kind == "np_thru_hole" or not p.on(layer):
                    continue
                pts, r = p.geom()
                c = (230, 200, 90) if p.net else (120, 110, 90)
                if len(pts) == 1:
                    disc(ox, pts[0][0], pts[0][1], r, c)
                elif len(pts) == 2:
                    seg(ox, pts[0], pts[1], r, c)
                else:
                    x0, y0 = min(q[0] for q in pts) - r, min(q[1] for q in pts) - r
                    x1, y1 = max(q[0] for q in pts) + r, max(q[1] for q in pts) + r
                    for yy in range(int(y0 * ppm + ox), int(y1 * ppm + ox) + 1):
                        for xx in range(int(x0 * ppm), int(x1 * ppm) + 1):
                            if 0 <= xx < W and 0 <= yy < len(img):
                                img[yy][xx] = c
                if p.drill:
                    disc(ox, p.x, p.y, p.drill / 2, (10, 10, 10))
            for p in self.pads:
                if p.kind == "np_thru_hole":
                    disc(ox, p.x, p.y, p.drill / 2, (0, 0, 0))
            for hx, hy, hd in self.holes:
                disc(ox, hx, hy, hd / 2, (0, 0, 0))
            for (x0, y0), (x1, y1) in zip(self.outline, self.outline[1:] + self.outline[:1]):
                seg(ox, (x0, y0), (x1, y1), 0.1, (200, 200, 200))
        raw = b"".join(b"\x00" + bytes(v for px in row for v in px) for row in img)

        def chunk(t, d):
            return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
        with open(path, "wb") as fh:
            fh.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", W, len(img), 8, 2, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def _with_uuid(node, u):
    node = [c for c in node if not (isinstance(c, list) and c[0] == "uuid")]
    node.append(["uuid", S.q(u)])
    return node


def _refkey(r):
    import re
    m = re.match(r"([A-Z]+)(\d+)", r)
    return (m.group(1), int(m.group(2))) if m else (r, 0)


# ======================================================================== drawing helpers
def octi(a, b, first="h"):
    """The two-segment octilinear path from a to b: a straight run then a 45 degree run
    ("h" / "v" says which straight comes first), the shape a person draws by hand."""
    (x0, y0), (x1, y1) = a, b
    dx, dy = x1 - x0, y1 - y0
    if abs(abs(dx) - abs(dy)) < 1e-9 or dx == 0 or dy == 0:
        return [a, b]
    sx, sy = (1 if dx > 0 else -1), (1 if dy > 0 else -1)
    if abs(dx) > abs(dy):
        run = abs(dx) - abs(dy)
        m = (x0 + sx * run, y0) if first == "h" else (x0 + sx * abs(dy), y1)
    else:
        run = abs(dy) - abs(dx)
        m = (x0, y0 + sy * run) if first == "v" else (x1, y0 + sy * abs(dx))
    return [a, m, b]


# ======================================================================== one-face router
class Router:
    """Routes ONE net on ONE face, around everything already on that face.

    This is not the grid router the earlier boards used. It never changes face and never
    places a via: the generator says which face every net lives on, and a net may only change
    face at one of its own through-hole pads - the router is only asked to find a tidy path
    inside that decision. Cost is length plus a price per bend, octilinear moves only, so what
    comes out is a straight run or an L with a 45 degree corner, the shapes drawn by hand.

    Clearance is kept on a 0.1 mm raster through a distance transform of every other net's
    copper: 0.6 mm from anything high-voltage, the class clearance from anything else, plus
    half the track width, plus a small margin for the raster itself. Board.check() and KiCad's
    DRC then verify the result exactly."""

    G = 0.1

    def __init__(self, board, hv_class="HV", margin=0.06):
        import numpy as np
        self.np, self.B = np, board
        self.nx, self.ny = int(board.W / self.G) + 1, int(board.H / self.G) + 1
        self.hv_class, self.margin = hv_class, margin
        self.ids = {}

    def nid(self, net):
        if net not in self.ids:
            self.ids[net] = len(self.ids) + 1
        return self.ids[net]

    def _raster(self, layer, exclude):
        """(other-net copper mask, of which high-voltage, own-net mask) for one face."""
        np, G = self.np, self.G
        other = np.zeros((self.ny, self.nx), bool)
        hv = np.zeros((self.ny, self.nx), bool)
        own = np.zeros((self.ny, self.nx), bool)
        ys, xs = np.mgrid[0:self.ny, 0:self.nx]
        for net, (pts, r), kind, lab in self.B.items(layer):
            x0 = min(p[0] for p in pts) - r
            x1 = max(p[0] for p in pts) + r
            y0 = min(p[1] for p in pts) - r
            y1 = max(p[1] for p in pts) + r
            i0, i1 = max(0, int(x0 / G) - 1), min(self.nx, int(x1 / G) + 2)
            j0, j1 = max(0, int(y0 / G) - 1), min(self.ny, int(y1 / G) + 2)
            if i0 >= i1 or j0 >= j1:
                continue
            X = xs[j0:j1, i0:i1] * G
            Y = ys[j0:j1, i0:i1] * G
            d = _dist_field(np, X, Y, pts)
            m = d <= r
            if net == exclude:
                own[j0:j1, i0:i1] |= m
            else:
                other[j0:j1, i0:i1] |= m
                if self.B.cls(net) == self.hv_class:
                    hv[j0:j1, i0:i1] |= m
        return other, hv, own

    def blocked(self, net, layer, width):
        from scipy.ndimage import distance_transform_edt as edt
        np, G = self.np, self.G
        other, hv, own = self._raster(layer, net)
        half = width / 2 + self.margin
        mine = self.B.cls(net)
        clr = {k: c for k, c, _ in self.B.classes}
        lv = max(v for k, v in clr.items() if k != self.hv_class)
        hvc = clr.get(self.hv_class, lv)
        d_other = edt(~other) * G
        d_hv = edt(~hv) * G
        if mine == self.hv_class:
            blk = d_other < hvc + half
        else:
            blk = (d_other < max(lv, clr[mine]) + half) | (d_hv < hvc + half)
        # the edge, unplated holes
        ys, xs = np.mgrid[0:self.ny, 0:self.nx]
        e = 0.5 + half
        blk |= (xs * G < e) | (ys * G < e) | (xs * G > self.B.W - e) | (ys * G > self.B.H - e)
        for hx, hy, hd in self.B.holes + [(p.x, p.y, p.drill) for p in self.B.pads if p.kind == "np_thru_hole"]:
            blk |= (xs * G - hx) ** 2 + (ys * G - hy) ** 2 < (hd / 2 + 0.3 + half) ** 2
        for (x0, y0, x1, y1, lay) in self.B.keepouts:
            if lay in (layer, "*"):
                blk |= (xs * G > x0 - half) & (xs * G < x1 + half) & (ys * G > y0 - half) & (ys * G < y1 + half)
        return blk & ~own, own

    def route(self, net, layer, a, b=None, width=None, turn=1.5, window=14.0, avoid=None, bias=None):
        """Route net from point a to point b (or to the nearest copper of the same net on
        this face when b is None). Adds the track and returns its points, or None."""
        import heapq
        np, G = self.np, self.G
        w = width or self.B.width(net)
        blk, own = self.blocked(net, layer, w)
        if avoid is not None:
            blk |= avoid
        ai, aj = int(round(a[0] / G)), int(round(a[1] / G))
        if b is not None:
            goal = np.zeros_like(own)
            bi, bj = int(round(b[0] / G)), int(round(b[1] / G))
            goal[bj, bi] = True
            gx0, gy0, gx1, gy1 = min(ai, bi), min(aj, bj), max(ai, bi), max(aj, bj)
        else:
            # the rest of this net's copper, minus the pad we start from
            goal = own.copy()
            ys, xs = np.mgrid[0:self.ny, 0:self.nx]
            start_pad = min((p for p in self.B.pads if p.net == net and p.on(layer)),
                            key=lambda p: (p.x - a[0]) ** 2 + (p.y - a[1]) ** 2)
            gp, gr = start_pad.geom()
            goal &= ~(_dist_field(np, xs * G, ys * G, gp) <= gr + 0.05)
            jj, ii = np.nonzero(goal)
            if len(ii) == 0:
                return None
            k = np.argmin((ii - ai) ** 2 + (jj - aj) ** 2)
            bi, bj = ii[k], jj[k]
            gx0, gy0, gx1, gy1 = min(ai, bi), min(aj, bj), max(ai, bi), max(aj, bj)
        m = int(window / G)
        X0, Y0 = max(0, gx0 - m), max(0, gy0 - m)
        X1, Y1 = min(self.nx - 1, gx1 + m), min(self.ny - 1, gy1 + m)
        blk[aj, ai] = False
        goal_set = goal
        DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
        tp = turn / G
        h = lambda i, j: max(abs(i - bi), abs(j - bj)) + 0.414 * min(abs(i - bi), abs(j - bj))
        start = (ai, aj, -1)
        best = {start: 0.0}
        prev = {}
        pq = [(h(ai, aj), 0.0, start)]
        found = None
        while pq:
            f, g, s = heapq.heappop(pq)
            i, j, d = s
            if g > best.get(s, 1e18):
                continue
            if goal_set[j, i] and (i, j) != (ai, aj):
                found = s
                break
            for k, (di, dj) in enumerate(DIRS):
                if d >= 0:
                    dd = min((k - d) % 8, (d - k) % 8)
                    if dd > 2:
                        continue                   # no sharper than a right angle
                    pen = tp * dd * 0.5
                else:
                    pen = 0.0
                ni, nj = i + di, j + dj
                if ni < X0 or ni > X1 or nj < Y0 or nj > Y1 or blk[nj, ni]:
                    continue
                if di and dj and (blk[j, ni] or blk[nj, i]):
                    continue
                step = 1.414 if di and dj else 1.0
                if bias is not None:
                    step *= bias(k)
                ng = g + step + pen
                ns = (ni, nj, k)
                if ng < best.get(ns, 1e18):
                    best[ns] = ng
                    prev[ns] = s
                    heapq.heappush(pq, (ng + h(ni, nj), ng, ns))
        if found is None:
            return None
        cells = []
        s = found
        while s in prev:
            cells.append((s[0], s[1]))
            s = prev[s]
        cells.append((ai, aj))
        cells.reverse()
        pts = [(c[0] * G, c[1] * G) for c in cells]
        # keep the corners only
        out = [pts[0]]
        for p0, p1, p2 in zip(pts, pts[1:], pts[2:]):
            if (round((p1[0] - p0[0]) / G), round((p1[1] - p0[1]) / G)) != (round((p2[0] - p1[0]) / G), round((p2[1] - p1[1]) / G)):
                out.append(p1)
        out.append(pts[-1])
        out[0] = a
        if b is not None:
            out[-1] = b
        self.B.track(net, layer, out, w)
        return out


def _dist_field(np, X, Y, pts):
    """Distance from every (X, Y) to a convex point set (a point, a segment or a polygon)."""
    if len(pts) == 1:
        return np.hypot(X - pts[0][0], Y - pts[0][1])
    if len(pts) == 2:
        (ax, ay), (bx, by) = pts
        dx, dy = bx - ax, by - ay
        L = dx * dx + dy * dy or 1e-12
        t = np.clip(((X - ax) * dx + (Y - ay) * dy) / L, 0, 1)
        return np.hypot(X - ax - t * dx, Y - ay - t * dy)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    ddx = np.maximum(np.maximum(x0 - X, X - x1), 0)
    ddy = np.maximum(np.maximum(y0 - Y, Y - y1), 0)
    return np.hypot(ddx, ddy)


def plot_placement(board, path, ppm=6, labels=True):
    """Courtyards (front green, back blue), pads, holes and the outline, for looking at a
    placement before any copper exists. PIL only."""
    from PIL import Image, ImageDraw
    W, H = int(board.W * ppm) + 1, int(board.H * ppm) + 1
    im = Image.new("RGB", (W, H), (22, 26, 32))
    d = ImageDraw.Draw(im)
    P = lambda x, y: (x * ppm, y * ppm)
    for ref, (f, x, y) in board.placed.items():
        c = f.court
        col = (70, 140, 230) if f.back else (80, 200, 120)
        d.rectangle([P(x + c[0], y + c[1]), P(x + c[2], y + c[3])], outline=col)
        if labels:
            d.text(P(x + c[0] + 0.3, y + c[1] + 0.2), ref, fill=col)
    for p in board.pads:
        if p.kind == "np_thru_hole":
            continue
        r = max(p.w, p.h) / 2
        d.ellipse([P(p.x - r, p.y - r), P(p.x + r, p.y + r)], fill=(220, 190, 80) if p.net else (120, 110, 90))
    for hx, hy, hd in board.holes:
        d.ellipse([P(hx - hd / 2, hy - hd / 2), P(hx + hd / 2, hy + hd / 2)], outline=(255, 255, 255))
    for net, layer, a, b, w in board.tracks:
        d.line([P(*a), P(*b)], fill=(230, 90, 90) if layer == "F.Cu" else (90, 150, 255), width=max(1, int(w * ppm)))
    d.rectangle([P(0, 0), P(board.W, board.H)], outline=(200, 200, 200))
    im.save(path)


# ======================================================================== placing the small parts
def place_near(board, ref, fp, region, rots=(0, 90, 180, 270), grid=0.635, margin=0.25, keepout=(),
               back=False, weight=None):
    """Put one part in the free spot of `region` (x0, y0, x1, y1) nearest the copper it connects
    to: for every candidate position and rotation, the sum over its pads of the distance to the
    nearest pad already placed on the same net (weight[net] scales a net). Courtyards may not
    overlap (by `margin`) any part on the same face, nor any `keepout` rectangle. Deterministic:
    ties go to the first candidate in scan order. Returns (x, y, rot) or None."""
    part = board.parts.get(ref)
    weight = weight or {}
    placed = [(board.court(r), board.placed[r][0].back) for r in board.placed]
    best = None
    for rot in rots:
        f = Footprint(fp, rot, back)
        c = f.court
        pins = [(p.x, p.y, part.pins.get(p.name)) for p in f.pads] if part else []
        targets = {}
        for _, _, n in pins:
            if n and n not in targets:
                targets[n] = [(q.x, q.y) for q in board.pads if q.net == n]
        x0, y0, x1, y1 = region
        nx = int((x1 - x0 - (c[2] - c[0])) / grid) + 1
        ny = int((y1 - y0 - (c[3] - c[1])) / grid) + 1
        for j in range(max(ny, 0)):
            for i in range(max(nx, 0)):
                ox = round(x0 - c[0] + i * grid, 3)
                oy = round(y0 - c[1] + j * grid, 3)
                bx = (ox + c[0] - margin, oy + c[1] - margin, ox + c[2] + margin, oy + c[3] + margin)
                bad = False
                for (a, b, cc, d), bk in placed:
                    if bk == back and bx[0] < cc and a < bx[2] and bx[1] < d and b < bx[3]:
                        bad = True
                        break
                if bad:
                    continue
                for (a, b, cc, d) in keepout:
                    if bx[0] < cc and a < bx[2] and bx[1] < d and b < bx[3]:
                        bad = True
                        break
                if bad:
                    continue
                s = 0.0
                for px, py, n in pins:
                    if n and targets.get(n):
                        s += weight.get(n, 1.0) * min(((ox + px - tx) ** 2 + (oy + py - ty) ** 2) ** 0.5
                                                      for tx, ty in targets[n])
                if best is None or s < best[0] - 1e-9:
                    best = (s, ox, oy, rot)
    if best is None:
        return None
    board.place(ref, fp, best[1], best[2], best[3], back)
    return best[1:]
