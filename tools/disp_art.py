#!/usr/bin/env python3
"""TS06-DISP silkscreen art: three directions for the owner to choose between.

The owner's verdict on rev B's silkscreen (30.09.26): "good but expand on it with artwork and
visual decorative design". `tools/mkpcb_disp.py --art NAME --out FILE` draws one direction on top of
rev B's silkscreen into a board of its own; without --art the board is rev B, byte for byte, and
this file is not even imported.

    engraving       a Soviet instrument panel, engraved: graduated scales, ruled rules and dials,
                    a nameplate
    constructivist  a constructivist geometric band: bars, wedges, a circle, hatched fields, type
                    set square and upright
    circuit         the circuit itself as ornament: the bus behind the board drawn where it runs,
                    the digit stacks, every socket's pinout

WHERE ART GOES. On the FRONT only where the finished clock shows the board head-on. That was
computed (30.09.26) from the case model, 3d/case-pair/case_pair.py: the trench window between the
sill and the brow's soffit and between the trench walls, less the valance behind the ИН-17 pair,
the trench's end blocks, and what stands on the board - the tube envelopes (their electrodes and
sockets hide the board behind the glass), the colon lamps, the LEDs and H3's screw head. `seen()`
below is that projection, from the case model's numbers. It leaves four fields:
    A  the bottom band under the tubes, y 32.3-39.0 (the sill hides the rest)
    B  the colon column between H1 and M10, x 46.3-54.3
    C  the seconds field over the ИН-17 pair, x 97.1-140.7, y 4.0-13.2: the one still seen from
       10 degrees up, down, left or right
    D  the slots between H10 and H1 and between M10 and M1, 3.9 mm wide
The BACK faces TS06-DRV 11 mm away and never shows in the finished clock; the builder sees it on
the bench. Art goes there anywhere free.

THE RULES every stroke keeps. The engine clips each line to them and drops a text that does not fit
whole (and says so):
  * lines 0.15 mm or more; text 1.0 mm or more with a 0.15 mm stroke (the fab's minimums);
  * 0.3 mm from any pad's copper (this board has no mask expansion, so the mask opening is the pad;
    0.3 is twice the fab's 0.15), and nothing within 3.8 mm of a standoff hole (the washer, the
    screw head, the hex spacer - mkpcb_disp.HOLE_KEEPOUT);
  * 2.0 mm from the 185 V warnings, 1.2 mm from the K and A marks and the connector names, 0.8 mm
    from rev B's other labels, 0.3 mm from the footprints' own outlines;
  * 0.5 mm from the board edge.
"""
import math
from collections import defaultdict

import sexp as S

NAMES = ("engraving", "constructivist", "circuit")

W_MIN = 0.15                    # the fab's thinnest silk line
PAD_CLR = 0.3                   # stroke edge to pad copper
HOLE_R = 3.8                    # no art within this of a standoff hole's centre (both faces)
FP_CLR = 0.3                    # stroke edge to a footprint's own silk stroke edge
EDGE = 0.5                      # stroke edge to the board edge
WARN_CLR, MARK_CLR, LABEL_CLR = 2.0, 1.2, 0.8   # to rev B's 185 V warnings / K, A and XP names / the rest
ART_TEXT_CLR = 0.4              # a line of art to a text of art
SAMPLE = 0.05                   # along a line, the step at which clearance is tested
SAFE = 0.03                     # what a step can miss between two samples, and a hair more
MIN_RUN = 0.3                   # a clipped piece shorter than this is dropped (no specks)
CELL = 1.0                      # the obstacle grid
REACH = 0.8                     # the widest half-stroke used here, plus margin, on every grid entry

WARN_TEXTS = ("185 V", "unplug,", "wait 15 s", "!")
MARK_PREFIX = ("K", "A", "XP", "LED", "ИНС-1")


# ======================================================================== the engine
class Obstacles:
    """What silk must keep clear of on one face, on a grid for quick lookup. Each item is a
    shape - a disc, a capsule, a box - and the clearance its neighbours keep from it."""

    def __init__(self):
        self.items = []
        self.cells = defaultdict(list)

    def _add(self, kind, data, clr, bbox):
        k = len(self.items)
        self.items.append((kind, data, clr))
        g = clr + REACH
        x0, y0, x1, y1 = bbox
        for i in range(int(math.floor((x0 - g) / CELL)), int(math.floor((x1 + g) / CELL)) + 1):
            for j in range(int(math.floor((y0 - g) / CELL)), int(math.floor((y1 + g) / CELL)) + 1):
                self.cells[(i, j)].append(k)

    def disc(self, x, y, r, clr):
        self._add("d", (x, y, r), clr, (x - r, y - r, x + r, y + r))

    def capsule(self, a, b, r, clr):
        self._add("c", (a[0], a[1], b[0], b[1], r), clr,
                  (min(a[0], b[0]) - r, min(a[1], b[1]) - r, max(a[0], b[0]) + r, max(a[1], b[1]) + r))

    def box(self, x0, y0, x1, y1, clr):
        self._add("b", (x0, y0, x1, y1), clr, (x0, y0, x1, y1))

    def clear(self, x, y, hw):
        for k in self.cells.get((int(math.floor(x / CELL)), int(math.floor(y / CELL))), ()):
            kind, d, clr = self.items[k]
            need = clr + hw + SAFE
            if kind == "d":
                if math.hypot(x - d[0], y - d[1]) - d[2] < need:
                    return False
            elif kind == "c":
                ax, ay, bx, by, r = d
                dx, dy = bx - ax, by - ay
                L2 = dx * dx + dy * dy
                t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / L2))
                if math.hypot(x - ax - t * dx, y - ay - t * dy) - r < need:
                    return False
            else:
                x0, y0, x1, y1 = d
                if math.hypot(max(x0 - x, 0.0, x - x1), max(y0 - y, 0.0, y - y1)) < need:
                    return False
        return True


class Art:
    """Draws on a mkpcb_disp board. Every line goes through line(), which clips it to where silk
    may go; every text goes through text(), which places it whole or not at all."""

    def __init__(self, M):
        self.M, self.B = M, M.B
        self.W, self.H = M.W, M.H
        self.ob = {"F": Obstacles(), "B": Obstacles()}
        self.pad_c = {f: [(p.x, p.y, (p.drill if p.kind == "np_thru_hole" else max(p.w, p.h)) / 2 + 0.15) for p in M.B.pads
                          if p.kind == "np_thru_hole" or p.on(f + ".Cu")] for f in "FB"}
        self.skipped = []
        self.n0 = len(self.B.gfx)
        self._seen_consts()
        self._obstacles()

    # ------------------------------------------------------------------ where the front is seen
    def _seen_consts(self):
        """The finished clock's view of the front, head-on, in board coordinates (y down). Case
        numbers are 3d/case-pair/case_pair.py's dims() and derive() as of 30.09.26; the board's are
        mkpcb_disp's own, so the tubes follow the board."""
        M = self.M
        in12_w, in12_h, allow = 19.47, 28.86, 0.4            # IN12_W, IN12_H (3d/IN12.FCStd), GLASS_ALLOW
        self.win = (3.0,                                     # TRENCH_L_X: the left wall hides XP11
                    round(M.IN15_X[1] + in12_w / 2 + allow + 0.5, 3),       # TRENCH_R_X
                    M.TOP - round(M.TOP - M.Y12 + in12_h / 2 + 0.8, 2),     # the soffit, BROW_CLR over the glass
                    M.TOP - 39.0)                            # SILL_TOP_Y
        self.valance = (round(M.IN12_X[3] + in12_w / 2 + allow, 3), round(M.IN15_X[0] - in12_w / 2 - allow, 3),
                        M.TOP - 74.0)                        # VALANCE_Y0: the brow covers the top 4 mm there
        self.blocks = (-0.5 + 8.0, M.W + 0.5 - 8.0,          # END_BLOCK wide from each cheek's inner face
                       M.TOP - (M.TOP - M.Y12 - in12_h / 2 - 1.0))   # WALL_BLK_Y1: 1.0 under the glass
        self.tube12 = [(x, M.Y12) for x in M.IN12_X + M.IN15_X]
        self.half12 = (in12_w / 2, in12_h / 2)
        self.tube17 = [(x, M.Y17) for x in M.IN17_X]         # face 14 x 20, stem Ø20 (ИН-17 outline drawing)
        self.lamps = [(M.COLON_X, y) for y in M.COLON_Y]     # ИНС-1 Ø6.97
        self.leds = [(x, y) for ref, (f, x, y) in self.B.placed.items() if ref.startswith("HL")]   # flange Ø3.8
        h3 = self.B.holes[2]
        self.screw = (h3[0], h3[1])                          # M3 low head Ø5.5 on the front

    def seen(self, x, y):
        """True where the finished clock shows the front head-on."""
        x0, x1, y0, y1 = self.win
        if not (x0 <= x <= x1 and y0 <= y <= y1):
            return False
        vx0, vx1, vy = self.valance
        if vx0 <= x <= vx1 and y < vy:
            return False
        bx0, bx1, by = self.blocks
        if (x <= bx0 or x >= bx1) and y >= by:
            return False
        hw, hh = self.half12
        for tx, ty in self.tube12:
            if abs(x - tx) <= hw and abs(y - ty) <= hh:
                return False
        for tx, ty in self.tube17:
            dx, dy = x - tx, y - ty
            if (abs(dx) <= 7.0 and abs(dy) <= 10.0) or dx * dx + dy * dy <= 100.0:
                return False
        for cx, cy, r in [(a, b, 3.485) for a, b in self.lamps] + [(a, b, 1.9) for a, b in self.leds] + \
                         [(self.screw[0], self.screw[1], 2.75)]:
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                return False
        return True

    # ------------------------------------------------------------------ what art keeps clear of
    def _obstacles(self):
        B, M = self.B, self.M
        for face in "FB":
            ob = self.ob[face]
            cu, silk = face + ".Cu", face + ".SilkS"
            for p in B.pads:
                if p.kind == "np_thru_hole":
                    ob.disc(p.x, p.y, p.drill / 2, PAD_CLR)
                    continue
                if not p.on(cu):
                    continue
                pts, r = p.geom()
                if len(pts) == 1:
                    ob.disc(pts[0][0], pts[0][1], r, PAD_CLR)
                elif len(pts) == 2:
                    ob.capsule(pts[0], pts[1], r, PAD_CLR)
                else:
                    xs, ys = [q[0] for q in pts], [q[1] for q in pts]
                    ob.box(min(xs) - r, min(ys) - r, max(xs) + r, max(ys) + r, PAD_CLR)
            for hx, hy, hd in B.holes:
                ob.disc(hx, hy, 0.0, HOLE_R)
            for ref, (f, x0, y0) in B.placed.items():
                for x, y, ly in M.fp_silk_points(ref, step=0.1):
                    if ly == silk:
                        ob.disc(x, y, M.SILK_W / 2, FP_CLR)
                for n in f.tree:                              # the footprints' own marks: K, A
                    if not (isinstance(n, list) and n and n[0] == "fp_text"):
                        continue
                    ly = S.find(n, "layer")
                    if not ly or S.unq(ly[1]) != silk or S.find(n, "hide") is not None or "hide" in n:
                        continue
                    at = S.find(n, "at")
                    sz = S.find(S.find(S.find(n, "effects") or [], "font") or [], "size")
                    ob.box(*M.text_box(S.unq(n[2]), x0 + float(at[1]), y0 + float(at[2]), float(sz[1]) if sz else 1.0),
                           MARK_CLR)
            for kind, ly, d in B.gfx:                         # rev B's own silkscreen
                if ly != silk:
                    continue
                if kind == "text":
                    t, x, y, size = d[:4]
                    clr = WARN_CLR if t in WARN_TEXTS else MARK_CLR if t.startswith(MARK_PREFIX) else LABEL_CLR
                    ob.box(*M.text_box(t, x, y, size, d[6]), clr)
                elif kind == "line":                          # rev B draws lines only for the warning triangles
                    ob.capsule((d[0], d[1]), (d[2], d[3]), d[4] / 2, WARN_CLR)
                elif kind == "circle":                        # the standoff seats, inside HOLE_R anyway
                    ob.disc(d[0], d[1], d[2] + d[3] / 2, LABEL_CLR)

    # ------------------------------------------------------------------ drawing
    def ok(self, face, x, y, hw, vis=True):
        return (EDGE + hw <= x <= self.W - EDGE - hw and EDGE + hw <= y <= self.H - EDGE - hw
                and self.ob[face].clear(x, y, hw) and (face == "B" or not vis or self.seen(x, y)))

    def line(self, face, a, b, w=W_MIN, vis=True):
        """a-b as silk on face "F" or "B", in the pieces that keep every rule (on the front, only
        where the clock shows the board, unless vis is False). Returns the number drawn."""
        w = max(w, W_MIN)
        hw = w / 2
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if L < 1e-6:
            return 0
        n = max(1, int(math.ceil(L / SAMPLE)))
        good = [self.ok(face, a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n, hw, vis) for i in range(n + 1)]
        drawn, i = 0, 0
        while i <= n:
            if not good[i]:
                i += 1
                continue
            j = i
            while j < n and good[j + 1]:
                j += 1
            if (j - i) / n * L >= max(MIN_RUN, w):
                p = (a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n)
                q = (a[0] + (b[0] - a[0]) * j / n, a[1] + (b[1] - a[1]) * j / n)
                self.B.line(round(p[0], 4), round(p[1], 4), round(q[0], 4), round(q[1], 4), face + ".SilkS", round(w, 3))
                drawn += 1
            i = j + 1
        return drawn

    def path(self, face, pts, w=W_MIN, closed=False, vis=True):
        pts = list(pts)
        if closed:
            pts.append(pts[0])
        return sum(self.line(face, p, q, w, vis) for p, q in zip(pts, pts[1:]))

    @staticmethod
    def arc_pts(cx, cy, rx, ry, a0, a1, chord=0.4):
        """Points on an ellipse from angle a0 to a1 (degrees; y is down, so +90 is straight down)."""
        sweep = math.radians(a1 - a0)
        n = max(4, int(math.ceil(abs(sweep) * max(rx, ry) / chord)))
        return [(cx + rx * math.cos(math.radians(a0) + sweep * k / n), cy + ry * math.sin(math.radians(a0) + sweep * k / n))
                for k in range(n + 1)]

    def arc(self, face, cx, cy, r, a0, a1, w=W_MIN, vis=True):
        return self.path(face, self.arc_pts(cx, cy, r, r, a0, a1), w, vis=vis)

    def circle(self, face, cx, cy, r, w=W_MIN, vis=True):
        return self.arc(face, cx, cy, r, 0, 360, w, vis)

    def hatch(self, face, poly, angle, pitch, w=W_MIN, vis=True, phase=0.5):
        """Parallel lines at angle (degrees) and pitch, inside the polygon."""
        c, s = math.cos(math.radians(angle)), math.sin(math.radians(angle))
        rot = [(x * c + y * s, -x * s + y * c) for x, y in poly]          # the lines run along u
        v0, v1 = min(p[1] for p in rot), max(p[1] for p in rot)
        n = 0
        v = v0 + pitch * phase
        while v < v1:
            xs = []
            for k in range(len(rot)):
                (u0, w0), (u1, w1) = rot[k - 1], rot[k]
                if (w0 <= v < w1) or (w1 <= v < w0):
                    xs.append(u0 + (v - w0) * (u1 - u0) / (w1 - w0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                p = (xs[k] * c - v * s, xs[k] * s + v * c)
                q = (xs[k + 1] * c - v * s, xs[k + 1] * s + v * c)
                n += self.line(face, p, q, w, vis)
            v += pitch
        return n

    def solid(self, face, poly, w=0.3, angle=0.0, vis=True):
        """A filled shape: strokes that overlap (pitch 0.8 of the width), so the print is solid."""
        return self.hatch(face, poly, angle, w * 0.8, w, vis, phase=0.5)

    def text(self, face, t, x, y, size=1.0, thick=None, rot=0, vis=True, log=True):
        """t centred at (x, y), whole or not at all. Its box then keeps art lines ART_TEXT_CLR away."""
        size = max(size, 1.0)
        thick = max(thick or round(size * 0.15, 3), W_MIN)
        x0, y0, x1, y1 = self.M.text_box(t, x, y, size, rot)
        g = thick - size * 0.15                               # a bolder stroke than the box assumes
        x0, y0, x1, y1 = x0 - g, y0 - g, x1 + g, y1 + g
        steps = 0.1
        # mkpcb_disp.silk_problems() holds texts to a box rule of its own; keep it too
        fits = not any(x0 - r < px < x1 + r and y0 - r < py < y1 + r for px, py, r in self.pad_c[face])
        yy = y0
        while yy <= y1 + 1e-9 and fits:
            xx = x0
            while xx <= x1 + 1e-9:
                if not self.ok(face, xx, yy, 0.0, vis):
                    fits = False
                    break
                xx += steps
            yy += steps
        if not fits:
            if log:
                self.skipped.append(f'"{t}" at ({x:.2f}, {y:.2f}) on {face}.SilkS')
            return False
        self.B.text(t, round(x, 4), round(y, 4), face + ".SilkS", size, thick=round(thick, 3), rot=rot)
        self.ob[face].box(x0, y0, x1, y1, ART_TEXT_CLR)
        return True

    def keep(self, face, x0, y0, x1, y1, clr=0.0):
        """Reserve a box: later art keeps clear of it (a knocked-out field)."""
        self.ob[face].box(x0, y0, x1, y1, clr)

    def glyph(self, face, ch, x, y, h, w=W_MIN, vis=True, slant=0.0):
        """One nixie numeral as drawn wire, h tall, top-left at (x, y)."""
        n = 0
        for stroke in GLYPHS[ch]:
            n += self.path(face, [(x + (u + slant * (1 - v)) * h, y + v * h) for u, v in stroke], w, vis=vis)
        return n

    def summary(self):
        new = self.B.gfx[self.n0:]
        lines = sum(1 for k, l, d in new if k == "line")
        texts = sum(1 for k, l, d in new if k == "text")
        by = {f: sum(1 for k, l, d in new if l == f + ".SilkS") for f in "FB"}
        return lines, texts, by


# ======================================================================== the nixie numerals
def _e(cx, cy, rx, ry, a0, a1, n=20):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * k / n)), cy + ry * math.sin(math.radians(a0 + (a1 - a0) * k / n)))
            for k in range(n + 1)]


# In a box 0.62 wide and 1 tall, y down: thin-wire numerals like the cathodes of an ИН-12
GLYPHS = {
    "0": [_e(0.31, 0.5, 0.31, 0.5, 0, 360, 32)],
    "1": [[(0.20, 0.16), (0.36, 0.0), (0.36, 1.0)]],
    "2": [_e(0.31, 0.29, 0.29, 0.29, 180, 385) + [(0.02, 1.0), (0.62, 1.0)]],
    "3": [_e(0.31, 0.26, 0.27, 0.26, 200, 450), _e(0.31, 0.75, 0.30, 0.25, 270, 520)],
    "4": [[(0.47, 1.0), (0.47, 0.0), (0.0, 0.68), (0.62, 0.68)]],
    "5": [[(0.58, 0.0), (0.10, 0.0), (0.06, 0.46)] + _e(0.31, 0.70, 0.30, 0.30, 212, 520)],
    "6": [_e(0.66, 0.66, 0.64, 0.66, 245, 180, 10) + _e(0.31, 0.72, 0.29, 0.28, 180, 540, 28)],
    "7": [[(0.0, 0.0), (0.62, 0.0), (0.18, 1.0)]],
    "8": [_e(0.31, 0.24, 0.24, 0.24, 90, 450, 24), _e(0.31, 0.74, 0.30, 0.26, 270, 630, 24)],
    "9": [_e(0.31, 0.28, 0.29, 0.28, 0, 360, 28), _e(-0.04, 0.34, 0.65, 0.64, 0, 68, 10)],
}


# ======================================================================== shared layout
def _free_spans(x0, x1, blocked, gap):
    """[x0, x1] less the intervals (a - gap, b + gap) of `blocked`, as a list of spans."""
    spans = [(x0, x1)]
    for a, b in sorted(blocked):
        a, b = a - gap, b + gap
        out = []
        for s, e in spans:
            if b <= s or a >= e:
                out.append((s, e))
            else:
                if a > s:
                    out.append((s, a))
                if b < e:
                    out.append((b, e))
        spans = out
    return spans


# ======================================================================== 1. ENGRAVING
def engraving(a):
    """A Soviet instrument panel, engraved. Borrowed: the faceplates of panel meters and bench
    instruments - a graduated scale with long, middle and short ticks and figures at the long ones,
    ruled double lines, dials, and the maker's nameplate with notched corners."""
    M = a.M
    F, Bk = "F", "B"
    # ---- A: the bottom band is a tuning scale, as on a radio's dial: a ruled line just above the
    # sill (where the band is seen from above as well), graduated in millimetres of the board - long
    # ticks every 10, middle every 5 - and between each pair's LEDs the pair's name, the way a dial
    # names its wavebands
    yb = 38.35
    a.line(F, (a.blocks[0] + 0.4, 38.75), (a.win[1] - 0.4, 38.75), 0.15)
    a.line(F, (a.blocks[0] + 0.4, yb), (a.win[1] - 0.4, yb), 0.25)
    for k in range(int(a.blocks[0]) + 1, int(a.win[1])):
        ln = 2.0 if k % 10 == 0 else 1.3 if k % 5 == 0 else 0.75
        a.line(F, (k, yb - 0.2), (k, yb - 0.2 - ln), 0.2 if k % 10 == 0 else 0.15)
    for name, (l, r) in (("ЧАСЫ", M.IN12_X[:2]), ("МИНУТЫ", M.IN12_X[2:]), ("СЕКУНДЫ", M.IN17_X)):
        ty = 34.25 if name == "СЕКУНДЫ" else 34.0
        a.text(F, name, (l + r) / 2 - 1.15, ty, 1.2)
    # ---- B: the colon column: a small engraved rosette between the lamps, a rule under them
    cx, cy = M.COLON_X, (M.COLON_Y[0] + M.COLON_Y[1]) / 2
    a.circle(F, cx, cy, 2.55, 0.2)
    a.circle(F, cx, cy, 1.95, 0.15)
    for k in range(24):
        ang = math.radians(k * 15)
        r1 = 1.95 if k % 2 else 1.5
        a.line(F, (cx + r1 * math.cos(ang), cy + r1 * math.sin(ang)), (cx + 2.55 * math.cos(ang), cy + 2.55 * math.sin(ang)), 0.15)
    a.circle(F, cx, cy, 0.35, 0.2)
    yl = M.COLON_Y[1] + 3.485 + 1.9
    a.line(F, (cx - 3.4, yl), (cx + 3.4, yl), 0.15)
    a.path(F, [(cx - 0.8, yl), (cx, yl - 0.8), (cx + 0.8, yl), (cx, yl + 0.8)], 0.15, closed=True)
    # ---- D: a vertical gauge in each slot between two ИН-12s, graduated every millimetre
    for xl, xr in ((M.IN12_X[0] + 9.735, M.IN12_X[1] - 9.735), (M.IN12_X[2] + 9.735, M.IN12_X[3] - 9.735)):
        xc = (xl + xr) / 2
        sp = xc - 1.0
        a.line(F, (sp, 4.0), (sp, 31.6), 0.2)
        a.line(F, (xc + 1.25, 4.0), (xc + 1.25, 31.6), 0.15)
        for k in range(28):
            y = 4.2 + k
            ln = 1.9 if k % 10 == 0 else 1.3 if k % 5 == 0 else 0.7
            a.line(F, (sp, y), (sp + ln, y), 0.15)
    # ---- C: the nameplate over the ИН-17 pair: a ruled double frame with notched corners
    x0, y0, x1, y1 = 98.9, 4.9, 138.9, 12.6
    for inset, w in ((0.0, 0.25), (0.55, 0.15)):
        _notched(a, F, x0 + inset, y0 + inset, x1 - inset, y1 - inset, 1.3 - inset * 0.5, w)
    a.text(F, "ТЕРМИНАЛ-06", (x0 + x1) / 2, 7.55, 2.0, thick=0.3)
    a.line(F, ((x0 + x1) / 2 - 15.5, 9.35), ((x0 + x1) / 2 + 15.5, 9.35), 0.15)
    a.text(F, "ЧАСЫ НА ГАЗОРАЗРЯДНЫХ ИНДИКАТОРАХ", (x0 + x1) / 2, 10.75, 1.0)

    # ---- the back: the whole face ruled like a panel, a dial round every socket, a millimetre rule
    _frame(a, Bk, 0.85, 0.25)
    _frame(a, Bk, 1.35, 0.15)
    for x, y in [(x, M.Y12) for x in M.IN12_X + M.IN15_X]:
        _dial(a, Bk, x, y, 10.45, 60, 5, (0.55, 0.95))
    for x in M.IN17_X:
        _dial(a, Bk, x, M.Y17, 7.25, 60, 5, (0.5, 0.85))
    # the millimetre rule along the bottom edge, read from the back: 0 at the back's left
    ybr = M.H - 1.35
    for k in range(0, 192):
        x = M.W - k
        ln = 1.5 if k % 10 == 0 else 1.0 if k % 5 == 0 else 0.55
        a.line(Bk, (x, ybr - 0.1), (x, ybr - 0.1 - ln), 0.15)
        if k % 10 == 0 and 0 < k < 190:
            a.text(Bk, str(k), x, ybr - 2.55, 1.0, log=False)


def _notched(a, face, x0, y0, x1, y1, r, w):
    """A rectangle whose corners are cut by quarter circles bowed inwards: the nameplate."""
    pts = []
    for (cx, cy, a0, a1) in ((x0, y0, 90, 0), (x1, y0, 180, 90), (x1, y1, 270, 180), (x0, y1, 360, 270)):
        pts += a.arc_pts(cx, cy, r, r, a0, a1, 0.2)
    return a.path(face, pts, w, closed=True)


def _frame(a, face, inset, w):
    """A rule round the face, bowed round each standoff hole it meets (a corner notch)."""
    W, H, M = a.W, a.H, a.M
    R = HOLE_R + 0.45 + w / 2
    pts = []
    for p, q in (((inset, inset), (W - inset, inset)), ((W - inset, inset), (W - inset, H - inset)),
                 ((W - inset, H - inset), (inset, H - inset)), ((inset, H - inset), (inset, inset))):
        L = math.hypot(q[0] - p[0], q[1] - p[1])
        n = int(L / 0.2)
        for k in range(n):
            x, y = p[0] + (q[0] - p[0]) * k / n, p[1] + (q[1] - p[1]) * k / n
            for hx, hy, hd in a.B.holes:
                d = math.hypot(x - hx, y - hy)
                if d < R:                         # push the rule round the hole, on the board's side
                    ux, uy = W / 2 - hx, H / 2 - hy
                    # the side of the hole the board lies on: project onto the circle, away from the edge
                    if d < 1e-6:
                        x, y = hx + R * ux / math.hypot(ux, uy), hy + R * uy / math.hypot(ux, uy)
                    else:
                        nx, ny = (x - hx) / d, (y - hy) / d
                        if nx * ux + ny * uy < 0:     # on the edge side: mirror across the line to the centre
                            k2 = (nx * ux + ny * uy) / (ux * ux + uy * uy)
                            nx, ny = nx - 2 * k2 * ux, ny - 2 * k2 * uy
                        x, y = hx + R * nx, hy + R * ny
            pts.append((x, y))
    return a.path(face, pts, w, closed=True)


def _dial(a, face, cx, cy, r, n, major, lens, w=0.15):
    """A dial ring of radius r with n ticks outwards, every `major`th the longer."""
    a.circle(face, cx, cy, r, w)
    for k in range(n):
        ang = math.radians(k * 360 / n - 90)
        ln = lens[1] if k % major == 0 else lens[0]
        a.line(face, (cx + (r + 0.1) * math.cos(ang), cy + (r + 0.1) * math.sin(ang)),
               (cx + (r + 0.1 + ln) * math.cos(ang), cy + (r + 0.1 + ln) * math.sin(ang)), 0.2 if k % major == 0 else 0.15)


# ======================================================================== 2. CONSTRUCTIVIST
def constructivist(a):
    """A constructivist band. Borrowed: the posters and book covers of the 1920s - Lissitzky's wedge
    and circle, Rodchenko's diagonals and bars, type set square to the edges and upright. Here in
    one colour, white on black: solid shapes are strokes laid edge to edge, grey ones hatched."""
    M = a.M
    F, Bk = "F", "B"
    # ---- A: one solid bar along the band, and over it a march of slanted bars between the LEDs,
    # rising and falling like a beat; a wedge points from the hours into the minutes at the colon
    a.solid(F, [(a.blocks[0] + 0.5, 37.95), (a.win[1] - 0.5, 37.95), (a.win[1] - 0.5, 38.7), (a.blocks[0] + 0.5, 38.7)], 0.3)
    leds = [(x - 2.6, x + 2.6) for x, y in a.leds]
    k = 0
    for s, e in _free_spans(a.blocks[0] + 0.6, a.win[1] - 0.6, leds, 0.0):
        x = s + 0.4
        while x + 1.9 < e:
            hgt = (1.2, 2.4, 3.6, 4.6, 3.6, 2.4)[k % 6]
            top = 37.6 - hgt
            a.solid(F, [(x, 37.6), (x + 0.9, 37.6), (x + 0.9 + hgt * 0.36, top), (x + hgt * 0.36, top)], 0.3)
            x += 2.2
            k += 1
    # ---- B: the colon column: Lissitzky's circle between the lamps, pierced by a bar
    cx, cy = M.COLON_X, (M.COLON_Y[0] + M.COLON_Y[1]) / 2
    a.solid(F, a.arc_pts(cx, cy, 2.3, 2.3, 0, 360, 0.2), 0.3)
    a.line(F, (cx - 3.6, cy + 3.0), (cx + 3.6, cy - 3.0), 0.5)
    yl = M.COLON_Y[1] + 3.485 + 0.9
    a.solid(F, [(cx - 3.3, yl), (cx + 3.3, yl), (cx, yl + 2.2)], 0.3)
    # ---- D: in each slot, a tower of bars under a hatched shaft
    for xl, xr in ((M.IN12_X[0] + 9.735, M.IN12_X[1] - 9.735), (M.IN12_X[2] + 9.735, M.IN12_X[3] - 9.735)):
        a.hatch(F, [(xl, 3.0), (xr, 3.0), (xr, 22.0), (xl, 22.0)], 45, 0.6, 0.15)
        for k in range(4):
            y = 23.4 + k * 2.1
            a.solid(F, [(xl + 0.4 + k * 0.35, y), (xr - 0.4, y), (xr - 0.4, y + 1.0), (xl + 0.4 + k * 0.35, y + 1.0)], 0.3)
    # ---- C: the seconds field: a black circle rolling onto a white wedge, the name upright
    x0, x1 = a.valance[0] + 0.3, a.valance[1] - 0.3
    a.text(F, "ТЕРМИНАЛ", 121.5, 6.0, 1.6, thick=0.32)
    a.text(F, "06", 133.8, 9.2, 3.4, thick=0.55)
    a.solid(F, a.arc_pts(102.9, 8.6, 3.4, 3.4, 0, 360, 0.2), 0.3)
    a.hatch(F, [(107.2, 12.6), (128.8, 7.8), (128.8, 12.6)], 30, 0.45, 0.15)
    a.line(F, (106.4, 12.4), (129.6, 7.4), 0.45)
    a.solid(F, [(x0, 12.75), (x1, 12.75), (x1, 13.1), (x0, 13.1)], 0.3)

    # ---- the back: one diagonal band across the whole face, hatched; bars along the bottom
    # between the strips; the name upright at the right-hand end; a circle and a wedge
    W, H = a.W, a.H
    band = [(-4.0, H + 2.0), (8.0, H + 2.0), (W + 4.0, -2.0), (W - 8.0, -2.0)]
    a.hatch(Bk, band, math.degrees(math.atan2(-(H + 4.0), W - 8.0)), 0.55, 0.15)
    a.line(Bk, (-4.0, H + 2.0), (W - 8.0, -2.0), 0.6)
    a.line(Bk, (8.0, H + 2.0), (W + 4.0, -2.0), 0.6)
    a.text(Bk, "ТЕРМИНАЛ-06", M.W - 5.6, 23.9, 2.0, thick=0.4, rot=90)
    for s, e in _free_spans(1.5, W - 1.5, [(x - 1.3, x + 1.3) for x in _strip_xs(a)], 0.6):
        y = H - 1.35
        if e - s > 2.0:
            a.solid(Bk, [(s, y - 0.45), (e, y - 0.45), (e, y + 0.35), (s, y + 0.35)], 0.3)
    a.solid(Bk, a.arc_pts(118.9, 17.0, 3.0, 3.0, 0, 360, 0.2), 0.3)
    a.circle(Bk, 118.9, 17.0, 5.2, 0.5)


def _strip_xs(a):
    return [p.x for p in a.B.pads if p.ref.startswith("XP2")]


# ======================================================================== 3. THE CIRCUIT
def circuit(a):
    """The circuit itself as ornament. Borrowed: the board's own copper and the tubes' insides -
    the ten-strand bus that threads the ИН-12 sockets on the back, the ten numerals every tube
    stacks one behind another, and each socket's pinout."""
    M, B = a.M, a.B
    F, Bk = "F", "B"
    # ---- the bus behind the board, drawn on the front wherever the clock shows it: in the slots
    # D, the colon column B and the seconds field C, each copper strand of the back traced in silk
    # exactly over itself (the ИН-12 bus K0-K9, and S10's bundle over the ИН-17s)
    for net, ly, p, q, w in B.tracks:
        if ly == "B.Cu" and net[:1] == "K":                  # K0-K9 and KS0-KS9
            a.line(F, p, q, 0.15)
    # ---- A: either side of every LED, the tube's digit stack - its ten numerals one behind
    # another, as a cold tube shows them
    for tx, ty, gh in [(x, 32.9, 3.3) for x in M.IN12_X + M.IN15_X] + [(x, 33.7, 2.6) for x in M.IN17_X]:
        for side in (-1, 1):
            _stack(a, F, tx + side * 5.9 - 1.0, ty, gh)
    # ---- C: one large stack in front of the ИН-12's anode mesh (the mesh knocked out round it)
    gx, gy, gh = 114.8, 5.0, 7.4
    _stack(a, F, gx, gy, gh)
    a.keep(F, gx - 1.0, gy - 0.6, gx + 0.62 * gh + 9 * 0.28 + 1.0, gy + gh + 1.2)
    mesh = [(a.valance[0] + 0.4, 4.2), (a.valance[1] - 0.4, 4.2), (a.valance[1] - 0.4, 12.9), (a.valance[0] + 0.4, 12.9)]
    a.hatch(F, mesh, 60, 0.9, 0.15)
    a.hatch(F, mesh, -60, 0.9, 0.15)

    # ---- the back: each socket's pinout round its ring (the digit, symbol or anode each pin
    # carries), the bus order beside XP11, and the order of XP12's pins beneath them
    for ref, (f, x0, y0) in B.placed.items():
        if not ref.startswith("V") or ref in ("V7", "V8"):
            continue
        for p in B.pads:
            if p.ref != ref or p.kind == "np_thru_hole":
                continue
            lab = _pin_label(a, ref, p.name)
            if not lab:
                continue
            dx, dy = p.x - x0, p.y - y0
            d = math.hypot(dx, dy) or 1.0
            r = p.w / 2 + 0.3 + 0.95
            for extra in (0.0, 0.3, 0.6):
                if a.text(Bk, lab, p.x + dx / d * (r + extra), p.y + dy / d * (r + extra), 1.0, log=extra == 0.6):
                    break
    for pin, net in zip(M.XP11, M.P.HEADERS["11"]):
        a.text(Bk, net[1:], pin[0] + 2.3, pin[1], 1.0)
    for pin, net in zip(M._XP12, M.P.HEADERS["12"]):
        lab = _net_label(net)
        if lab:
            a.text(Bk, lab, pin[0], pin[1] + 2.6, 1.0)


def _stack(a, face, x, y, h):
    """Ten numerals one behind another, each set a little up and to the right: a digit stack."""
    for k, ch in enumerate("0123456789"):
        a.glyph(face, ch, x + k * 0.28, y + 0.5 - k * 0.05, h, 0.15)


IN15_SYM = {"VOLT": "V", "HENRY": "H", "HERTZ": "Hz", "FARAD": "F", "WATT": "W", "AMP": "A", "OHM": "Ω", "SIEMENS": "S",
            "MEGA": "M", "MILLI": "m", "PLUS": "+", "MINUS": "−", "P": "P", "MICRO": "µ", "NANO": "n", "PCT": "%",
            "PI": "π", "KILO": "k"}


def _net_label(net):
    if not net:
        return None
    if net.startswith("KS"):
        return net[2:]
    if net.startswith("K") and net[1:].isdigit():
        return net[1:]
    if net.startswith("CAT_"):
        return IN15_SYM.get(net.split("_", 2)[2])
    return None


def _pin_label(a, ref, pad):
    net = a.M.PT[ref].pins.get(pad)
    if not net:
        return None
    if net.startswith("ANODE"):
        return "A"
    return _net_label(net)


DRAW = {"engraving": engraving, "constructivist": constructivist, "circuit": circuit}


def draw(name, M):
    """Draw direction `name` on mkpcb_disp's board. Returns the Art, for its summary and skips."""
    a = Art(M)
    DRAW[name](a)
    return a
