#!/usr/bin/env python3
"""Axonometric + orthographic SVG renders for the -06 product family.

Everything is driven from real millimetre dimensions. Camera is a yaw/pitch
axonometric (no perspective) so the drawings stay measurable.
"""
import math, os

OUT = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- projection
def proj(p, yaw, pitch):
    x, y, z = p
    cy, sy = math.cos(yaw), math.sin(yaw)
    x1 = x * cy + z * sy
    z1 = -x * sy + z * cy
    cp, sp = math.cos(pitch), math.sin(pitch)
    y2 = y * cp - z1 * sp
    z2 = y * sp + z1 * cp
    return (x1, -y2, z2)


def raked(x, y, z, w, h, d, lean=0.0):
    """Solid whose front face (low z) leans back by `lean` at the top."""
    A = (x,     y,     z)
    B = (x + w, y,     z)
    C = (x + w, y,     z + d)
    D = (x,     y,     z + d)
    E = (x,     y + h, z + lean)
    F = (x + w, y + h, z + lean)
    G = (x + w, y + h, z + d)
    H = (x,     y + h, z + d)
    return {
        "bottom": [A, B, C, D],
        "top":    [E, F, G, H],
        "front":  [A, B, F, E],
        "back":   [D, C, G, H],
        "left":   [A, E, H, D],
        "right":  [B, C, G, F],
    }


SHADE = {"top": 1.00, "front": 0.78, "right": 0.58, "left": 0.44,
         "back": 0.40, "bottom": 0.30}


def mix(hexcol, k):
    h = hexcol.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return "#%02x%02x%02x" % (min(255, int(r * k)), min(255, int(g * k)), min(255, int(b * k)))


class Scene:
    def __init__(self, yaw=30, pitch=18, scale=2.2):
        self.yaw = math.radians(yaw)
        self.pitch = math.radians(pitch)
        self.s = scale
        self.items = []          # (depth, svg string)
        self.pts = []

    def p2(self, p):
        sx, sy, dz = proj(p, self.yaw, self.pitch)
        self.pts.append((sx * self.s, sy * self.s))
        return (sx * self.s, sy * self.s, dz)

    def poly(self, pts3, fill, stroke=None, sw=0.8, extra="", bias=0.0):
        pts = [self.p2(p) for p in pts3]
        depth = sum(p[2] for p in pts) / len(pts) + bias
        d = " ".join("%.2f,%.2f" % (p[0], p[1]) for p in pts)
        st = ' stroke="%s" stroke-width="%.2f" stroke-linejoin="round"' % (stroke, sw) if stroke else ""
        self.items.append((depth, '<polygon points="%s" fill="%s"%s%s/>' % (d, fill, st, extra)))
        return depth

    def solid(self, faces, base, stroke, skip=()):
        for name, pts in faces.items():
            if name in skip:
                continue
            self.poly(pts, mix(base, SHADE[name]), stroke)

    def face_matrix(self, origin, u, v):
        """Affine matrix mapping local 2D (u right, v up) onto a projected face."""
        o = self.p2(origin)
        pu = self.p2((origin[0] + u[0], origin[1] + u[1], origin[2] + u[2]))
        pv = self.p2((origin[0] + v[0], origin[1] + v[1], origin[2] + v[2]))
        a, b = pu[0] - o[0], pu[1] - o[1]
        c, dd = pv[0] - o[0], pv[1] - o[1]
        return "matrix(%.4f %.4f %.4f %.4f %.3f %.3f)" % (a, b, c, dd, o[0], o[1]), o[2]

    def text_on_face(self, origin, u, v, txt, size, fill, anchor="middle",
                     family="IBM Plex Sans Condensed, Arial Narrow, sans-serif",
                     weight="400", extra="", depth_bias=-6):
        m, dz = self.face_matrix(origin, u, (-v[0], -v[1], -v[2]))
        s = ('<g transform="%s"><text x="0" y="0" font-family="%s" font-size="%.2f" '
             'font-weight="%s" fill="%s" text-anchor="%s"%s>%s</text></g>'
             % (m, family, size, weight, fill, anchor, extra, txt))
        self.items.append((dz + depth_bias, s))

    def begin_group(self):
        self._saved = self.items
        self.items = []

    def end_group(self, depth):
        frags = [f for _, f in self.items]
        self.items = self._saved
        self.items.append((depth, "<g>" + "\n".join(frags) + "</g>"))

    def render(self, defs="", pad=26, extra_head=""):
        self.items.sort(key=lambda t: -t[0])
        xs = [p[0] for p in self.pts]
        ys = [p[1] for p in self.pts]
        x0, x1 = min(xs) - pad, max(xs) + pad
        y0, y1 = min(ys) - pad, max(ys) + pad
        body = "\n".join(i[1] for i in self.items)
        return ('<svg viewBox="%.1f %.1f %.1f %.1f" xmlns="http://www.w3.org/2000/svg" '
                'role="img">%s%s\n%s</svg>' % (x0, y0, x1 - x0, y1 - y0, defs, extra_head, body))


def disc(sc, fpt, cx, cy, r, fill, stroke=None, sw=0.8, n=22, bias=0.0, extra=""):
    pts = [fpt(cx + math.cos(2 * math.pi * i / n) * r, cy + math.sin(2 * math.pi * i / n) * r)
           for i in range(n)]
    sc.poly(pts, fill, stroke, sw, extra, bias=bias)


# 5x7 column font, bit0 = top row — the glyphs MIMI's VFD actually writes
F57 = {
    " ": [0, 0, 0, 0, 0], "(": [0, 0x1C, 0x22, 0x41, 0], ")": [0, 0x41, 0x22, 0x1C, 0],
    "^": [4, 2, 1, 2, 4], "_": [0x40, 0x40, 0x40, 0x40, 0x40], ":": [0, 0x36, 0x36, 0, 0],
    "0": [0x3E, 0x51, 0x49, 0x45, 0x3E], "2": [0x42, 0x61, 0x51, 0x49, 0x46],
    "4": [0x18, 0x14, 0x12, 0x7F, 0x10], "7": [1, 0x71, 9, 5, 3],
    "S": [0x46, 0x49, 0x49, 0x49, 0x31], "U": [0x3F, 0x40, 0x40, 0x40, 0x3F],
    "N": [0x7F, 4, 8, 0x10, 0x7F],
}


# ---------------------------------------------------------------- glow defs
def glow_defs(idp, col, col2=None):
    col2 = col2 or col
    return f'''<defs>
<linearGradient id="g{idp}" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="{col}" stop-opacity=".95"/>
  <stop offset="1" stop-color="{col2}" stop-opacity=".55"/>
</linearGradient>
<filter id="b{idp}" x="-120%" y="-120%" width="340%" height="340%">
  <feGaussianBlur stdDeviation="5"/>
</filter>
<filter id="bs{idp}" x="-120%" y="-120%" width="340%" height="340%">
  <feGaussianBlur stdDeviation="2"/>
</filter>
</defs>'''


# ================================================================ PRODUCTS
# Each product returns (hero_svg, ga_svg)

CASE_T = "#2A2E34"; ACC_T = "#F25610"; GLOW_T = "#FF9E36"
CASE_M = "#2A2838"; ACC_M = "#FF2E88"; GLOW_M = "#FF9E36"; VFD_M = "#7CF5DC"
CASE_Q = "#343A41"; ACC_Q = "#6E9AC4"; GLOW_Q = "#FF9E36"
CASE_S = "#2C362F"; ACC_S = "#A98BFF"; GLOW_S = "#FF9E36"

STROKE = "#0A0B0C"


# ---------------------------------------------------------------- TERMINAL
# base 237 x 56 x 104, front raked 12deg (lean 12)
# plinth 190 x 16 x 46, inset 23.5 each side, set back 30 from front bottom edge
# tubes 24 tall on plinth top (y = 72)
T_W, T_H, T_D, T_LEAN = 237.0, 56.0, 104.0, 12.0
T_PW, T_PH, T_PD, T_PX, T_PZ = 213.0, 16.0, 46.0, 12.0, 30.0
T_DECK = T_H + T_PH                      # 72
T_TUBES = [
    (24.5, 22, 24, "2"), (49.5, 22, 24, "3"),
    (81.5, 22, 24, "1"), (106.5, 22, 24, "9"),
    (137.0, 15, 20, "0"), (155.0, 15, 20, "4"),
    (189.5, 22, 24, "A"), (212.5, 22, 24, "Р"),
]


def terminal_hero():
    sc = Scene(yaw=29, pitch=10, scale=2.75)
    # base
    sc.solid(raked(0, 0, 0, T_W, T_H, T_D, T_LEAN), CASE_T, STROKE, skip=("bottom",))
    # fascia recessed into the raked front face
    fy0, fy1 = 2.0, 54.0
    sc.begin_group()
    def fpt(xx, yy):
        return (xx, yy, T_LEAN * (yy / T_H))
    sc.poly([fpt(2, fy0), fpt(T_W - 2, fy0), fpt(T_W - 2, fy1), fpt(2, fy1)],
            "#191D21", "#4E545C", 0.9, bias=-3)
    # dial arc on the fascia
    kx, ky = 46.0, 28.0
    for i in range(6):
        a = math.radians(-80 + i * 32)
        r1, r2 = 15.0, 19.0
        p1 = fpt(kx + math.sin(a) * r1, ky + math.cos(a) * r1)
        p2 = fpt(kx + math.sin(a) * r2, ky + math.cos(a) * r2)
        sc.poly([p1, p2, (p2[0] + 1.4, p2[1], p2[2]), (p1[0] + 1.4, p1[1], p1[2])],
                ACC_T if i == 0 else "#BFB9AE", bias=-7)
    disc(sc, fpt, kx, ky, 9.5, "#343A42", "#79818B", 0.9)
    sc.poly([fpt(kx - .9, ky + 2), fpt(kx + .9, ky + 2), fpt(kx + .9, ky + 8), fpt(kx - .9, ky + 8)],
            ACC_T, bias=-9)
    sc.text_on_face((T_W - 12, 6, T_LEAN * (6 / T_H) - .4), (1, 0, 0), (0, 1, 0),
                    "TERMINAL·06", 7.5, "#8E948C", anchor="end", weight="600",
                    family="IBM Plex Mono, monospace", depth_bias=-4)
    # levers + buttons
    for lx in (134, 154):
        sc.poly([fpt(lx - 2.2, ky - 7), fpt(lx + 2.2, ky - 7), fpt(lx + 2.2, ky + 7), fpt(lx - 2.2, ky + 7)],
                "#343A42", "#79818B", 0.8, bias=-7)
    for bx in (194, 214):
        disc(sc, fpt, bx, ky, 4.4, "#343A42", "#79818B", 0.8)
    sc.end_group(-1e6)
    # plinth
    sc.solid(raked(T_PX, T_H, T_PZ, T_PW, T_PH, T_PD), CASE_T, STROKE,
             skip=("bottom", "back"))
    # tubes
    d = glow_defs("t", GLOW_T, "#FF6A10")
    for (cx, w, h, ch) in T_TUBES:
        x0 = cx - w / 2.0
        z0 = T_PZ + T_PD / 2.0 - 7.0
        sc.solid(raked(x0, T_DECK, z0, w, h, 14.0), "#39434B", STROKE, skip=("bottom",))
        sc.begin_group()
        # glowing front face
        sc.poly([(x0 - 2, T_DECK - .1, z0 - 4), (x0 + w + 2, T_DECK - .1, z0 - 4),
                 (x0 + w + 2, T_DECK - .1, z0 + 18), (x0 - 2, T_DECK - .1, z0 + 18)],
                GLOW_T, extra=' opacity=".26" filter="url(#bt)"', bias=-1)
        sc.poly([(x0 + 1, T_DECK + 1, z0 - .3), (x0 + w - 1, T_DECK + 1, z0 - .3),
                 (x0 + w - 1, T_DECK + h - 1, z0 - .3), (x0 + 1, T_DECK + h - 1, z0 - .3)],
                "#141C23", "#9BB0BE", 0.7, bias=-2)
        sc.text_on_face((x0 + w / 2.0, T_DECK + h * 0.20, z0 - 1.0), (1, 0, 0), (0, 1, 0),
                        ch, h * 0.80, GLOW_T,
                        extra=' filter="url(#bst)" opacity=".9"', depth_bias=-9)
        sc.text_on_face((x0 + w / 2.0, T_DECK + h * 0.20, z0 - 1.2), (1, 0, 0), (0, 1, 0),
                        ch, h * 0.80, GLOW_T, depth_bias=-10)
        sc.end_group(proj((cx, T_DECK + h / 2, z0), sc.yaw, sc.pitch)[2] - 1.0)
    # colon
    for yy in (T_DECK + 8, T_DECK + 15):
        sc.poly([(63.5, yy, T_PZ + T_PD / 2 - 7.4), (67.5, yy, T_PZ + T_PD / 2 - 7.4),
                 (67.5, yy + 3.4, T_PZ + T_PD / 2 - 7.4), (63.5, yy + 3.4, T_PZ + T_PD / 2 - 7.4)],
                GLOW_T, extra=' filter="url(#bst)"')
    # "m" stencil on the deck front edge
    sc.text_on_face((201, T_H + 5, T_PZ - 0.4), (1, 0, 0), (0, 1, 0), "m", 9, GLOW_T,
                    weight="600", depth_bias=-8)
    return sc.render(defs=d)


# ------------------------------------------------------------ ortho helpers
def ortho_head(w, h, pad=40):
    return None


class Ortho:
    """Simple 2-D orthographic sheet in mm, y up, converted to SVG y-down."""
    def __init__(self, scale=1.0):
        self.s = scale
        self.body = []
        self.pts = []

    def P(self, x, y):
        p = (x * self.s, -y * self.s)
        self.pts.append(p)
        return p

    def rect(self, x, y, w, h, fill, stroke=None, sw=0.9, rx=0, extra=""):
        p = self.P(x, y + h)
        self.P(x + w, y)
        st = ' stroke="%s" stroke-width="%.2f"' % (stroke, sw) if stroke else ""
        r = ' rx="%.1f"' % rx if rx else ""
        self.body.append('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="%s"%s%s%s/>'
                         % (p[0], p[1], w * self.s, h * self.s, fill, st, r, extra))

    def poly(self, pts, fill, stroke=None, sw=0.9):
        pp = [self.P(*p) for p in pts]
        st = ' stroke="%s" stroke-width="%.2f" stroke-linejoin="round"' % (stroke, sw) if stroke else ""
        self.body.append('<polygon points="%s" fill="%s"%s/>'
                         % (" ".join("%.2f,%.2f" % q for q in pp), fill, st))

    def circle(self, x, y, r, fill, stroke=None, sw=0.9, extra=""):
        p = self.P(x, y)
        self.P(x + r, y + r); self.P(x - r, y - r)
        st = ' stroke="%s" stroke-width="%.2f"' % (stroke, sw) if stroke else ""
        self.body.append('<circle cx="%.2f" cy="%.2f" r="%.2f" fill="%s"%s%s/>'
                         % (p[0], p[1], r * self.s, fill, st, extra))

    def line(self, x1, y1, x2, y2, stroke, sw=0.7, dash=None):
        a, b = self.P(x1, y1), self.P(x2, y2)
        dl = ' stroke-dasharray="%s"' % dash if dash else ""
        self.body.append('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="%s" '
                         'stroke-width="%.2f"%s/>' % (a[0], a[1], b[0], b[1], stroke, sw, dl))

    def label(self, x, y, txt, fill="#8A8F97", size=9, anchor="middle", family="mono", weight="400"):
        p = self.P(x, y)
        fam = ("IBM Plex Mono, monospace" if family == "mono"
               else "IBM Plex Sans Condensed, Arial Narrow, sans-serif")
        self.body.append('<text x="%.2f" y="%.2f" font-family="%s" font-size="%.1f" '
                         'fill="%s" text-anchor="%s" font-weight="%s" letter-spacing=".5">%s</text>'
                         % (p[0], p[1], fam, size, fill, anchor, weight, txt))

    def dim_h(self, x1, x2, y, txt, col="#5E646C", off=0):
        self.line(x1, y, x2, y, col, 0.7)
        for xx in (x1, x2):
            self.line(xx, y - 2.2, xx, y + 2.2, col, 0.7)
        self.label((x1 + x2) / 2.0, y + 3.4 + off, txt, col, 8.6)

    def dim_v(self, y1, y2, x, txt, col="#5E646C"):
        self.line(x, y1, x, y2, col, 0.7)
        for yy in (y1, y2):
            self.line(x - 2.2, yy, x + 2.2, yy, col, 0.7)
        p = self.P(x - 3.2, (y1 + y2) / 2.0)
        self.body.append('<text x="%.2f" y="%.2f" font-family="IBM Plex Mono, monospace" '
                         'font-size="8.6" fill="%s" text-anchor="middle" '
                         'transform="rotate(-90 %.2f %.2f)">%s</text>'
                         % (p[0], p[1], col, p[0], p[1], txt))

    def render(self, pad=16, defs=""):
        xs = [p[0] for p in self.pts]; ys = [p[1] for p in self.pts]
        x0, x1 = min(xs) - pad, max(xs) + pad
        y0, y1 = min(ys) - pad, max(ys) + pad
        return ('<svg viewBox="%.1f %.1f %.1f %.1f" xmlns="http://www.w3.org/2000/svg" role="img">'
                '%s\n%s</svg>' % (x0, y0, x1 - x0, y1 - y0, defs, "\n".join(self.body)))


def terminal_ga():
    o = Ortho(scale=1.9)
    GX = 0.0
    # ---- FRONT ELEVATION -------------------------------------------------
    o.label(T_W / 2, T_DECK + 42, "FRONT ELEVATION", "#DCD8D0", 11, family="disp", weight="700")
    o.rect(0, 0, T_W, T_H, "#1B1E22", "#3A3E44")
    o.rect(2, 2, T_W - 4, 52, "#101215", "#2E3238", 0.8)
    o.rect(T_PX, T_H, T_PW, T_PH, "#22262B", "#3A3E44")
    for (cx, w, h, ch) in T_TUBES:
        o.rect(cx - w / 2, T_DECK, w, h, "#141B20", "#8FA4B2", 0.8)
        o.rect(cx - w / 2 + 2, T_DECK + 2, w - 4, h - 5, "#2A1B0C")
        o.label(cx, T_DECK + h * 0.32, ch, GLOW_T, h * 0.62, family="disp")
    for yy in (T_DECK + 8, T_DECK + 15):
        o.circle(65.5, yy + 1.6, 1.9, GLOW_T)
    o.label(201, T_H + 6, "m", GLOW_T, 8, family="disp", weight="600")
    # dial
    kx, ky = 46.0, 28.0
    o.circle(kx, ky, 13.5, "#1C1F23", "#4A5058", 0.9)
    for i in range(6):
        a = math.radians(-80 + i * 32)
        o.line(kx + math.sin(a) * 15.5, ky + math.cos(a) * 15.5,
               kx + math.sin(a) * 19.5, ky + math.cos(a) * 19.5, ACC_T, 1.1)
    for lx in (134, 154):
        o.rect(lx - 2, ky - 7, 4, 14, "#1C1F23", "#4A5058", 0.7)
    for bx in (194, 214):
        o.circle(bx, ky, 4.2, "#1C1F23", "#4A5058", 0.7)
    o.dim_h(0, T_W, -9, "237")
    o.dim_h(0, 24.5, -20, "24.5"); o.dim_h(155, 189.5, -20, "16 gap")
    o.dim_v(T_DECK, T_DECK + 24, -8, "24")
    o.dim_v(0, T_H, -20, "56")
    # ---- RIGHT PROFILE ---------------------------------------------------
    SX = T_W + 58
    o.label(SX + 52, T_DECK + 42, "RIGHT PROFILE", "#DCD8D0", 11, family="disp", weight="700")
    o.poly([(SX, 0), (SX + T_D, 0), (SX + T_D, T_H), (SX + T_LEAN, T_H)], "#1B1E22", "#3A3E44")
    o.rect(SX + T_PZ, T_H, T_PD, T_PH, "#22262B", "#3A3E44")
    o.rect(SX + T_PZ + T_PD / 2 - 7, T_DECK, 14, 24, "#141B20", "#8FA4B2", 0.8)
    o.rect(SX + T_PZ + T_PD / 2 - 5, T_DECK + 2, 10, 19, "#2A1B0C")
    # sightline that used to be blocked
    o.line(SX + T_PZ + T_PD / 2, T_DECK + 18, SX - 30, T_DECK + 32, ACC_T, 0.9, "4 3")
    o.label(SX - 32, T_DECK + 26, "eye at 30° — nothing in the way", ACC_T, 8.4, anchor="start")
    o.dim_h(SX, SX + T_D, -9, "104")
    o.dim_h(SX, SX + T_PZ, -20, "30 set back")
    o.dim_v(0, T_H, SX - 8, "56")
    o.dim_v(T_H, T_DECK, SX - 20, "16")
    o.label(SX + T_D / 2, -32, "front face raked 12°", "#5E646C", 8.4)
    # ---- PLAN ------------------------------------------------------------
    PY = -96.0
    o.label(T_W / 2, PY + 8, "PLAN — THE OFFSET", "#DCD8D0", 11, family="disp", weight="700")
    o.rect(0, PY - T_D, T_W, T_D, "#16191D", "#3A3E44")
    o.rect(T_PX, PY - T_PZ - T_PD, T_PW, T_PD, "#22262B", ACC_T, 1.1)
    for (cx, w, h, ch) in T_TUBES:
        o.rect(cx - w / 2, PY - T_PZ - T_PD / 2 - 7, w, 14, "#141B20", "#8FA4B2", 0.8)
    o.circle(65.5, PY - T_PZ - T_PD / 2, 3.4, "#141B20", "#8FA4B2", 0.8)
    o.dim_h(0, T_PX, PY - T_D - 10, "12 inset")
    o.dim_h(T_PX + T_PW, T_W, PY - T_D - 10, "12 inset")
    o.label(T_W / 2, PY - T_D - 24, "PLINTH 213 WIDE, INSET 12 EACH SIDE, SET BACK 30 — NOTHING OVERHANGS THE GLASS",
            ACC_T, 8.6)
    return o.render()


# ---------------------------------------------------------------- MIMI
M_W, M_H, M_D, M_LEAN = 176.0, 112.0, 96.0, 16.0
M_PW, M_PH, M_PD, M_PX, M_PZ = 154.0, 14.0, 44.0, 11.0, 26.0
M_DECK = M_H + M_PH
M_TUBES = [(24.5, 22, 24, "2"), (49.5, 22, 24, "3"), (81.5, 22, 24, "1"),
           (106.5, 22, 24, "9"), (137.0, 15, 20, "0"), (155.0, 15, 20, "4")]


def mimi_hero():
    sc = Scene(yaw=31, pitch=11, scale=2.05)
    sc.solid(raked(0, 0, 0, M_W, M_H, M_D, M_LEAN), CASE_M, STROKE, skip=("bottom",))

    def fpt(xx, yy):
        return (xx, yy, M_LEAN * (yy / M_H))
    sc.begin_group()
    # VFD window (upper) and fascia (lower)
    sc.poly([fpt(13, 68), fpt(163, 68), fpt(163, 94), fpt(13, 94)], "#05070A", "#223336", 0.8, bias=-3)
    MSG = "(^_^)  20:47 SUN"[:16].ljust(16)
    for i, ch in enumerate(MSG):
        g = F57.get(ch, F57[" "])
        for col in range(5):
            for row in range(7):
                on = (g[col] >> row) & 1
                x = 15.6 + i * 9.35 + col * 1.72
                y = 90.2 - row * 2.72
                sc.poly([fpt(x, y), fpt(x + 1.45, y), fpt(x + 1.45, y + 1.45), fpt(x, y + 1.45)],
                        VFD_M, extra=' opacity="%.2f"' % (0.95 if on else 0.055), bias=-6)
    sc.poly([fpt(2, 6), fpt(M_W - 2, 6), fpt(M_W - 2, 58), fpt(2, 58)], "#14141F", "#3A3850", 0.9, bias=-3)
    kx, ky = 42.0, 32.0
    disc(sc, fpt, kx, ky, 9.5, "#2A2839", "#5D5A78", 0.9)
    sc.poly([fpt(kx - .9, ky + 2), fpt(kx + .9, ky + 2), fpt(kx + .9, ky + 8), fpt(kx - .9, ky + 8)],
            ACC_M, bias=-9)
    for lx in (100, 120):
        sc.poly([fpt(lx - 2, ky - 7), fpt(lx + 2, ky - 7), fpt(lx + 2, ky + 7), fpt(lx - 2, ky + 7)],
                "#2A2839", "#5D5A78", 0.8, bias=-7)
    for bx in (146, 164):
        disc(sc, fpt, bx, ky, 4.4, "#2A2839", "#5D5A78", 0.8)
    sc.end_group(-1e6)
    # plinth
    sc.solid(raked(M_PX, M_H, M_PZ, M_PW, M_PH, M_PD), CASE_M, STROKE, skip=("bottom", "back"))
    # ears — skewed fins at the rear top corners
    for ex in (0.0, M_W - 15.0):
        ez = M_PZ + M_PD - 16
        sc.solid(raked(ex, M_H, ez, 15, 44, 20), "#332F45", STROKE, skip=("bottom",))
        sc.poly([(ex + 4.5, M_H + 8, ez - 0.35), (ex + 7.5, M_H + 8, ez - 0.35),
                 (ex + 7.5, M_H + 40, ez - 0.35), (ex + 4.5, M_H + 40, ez - 0.35)],
                ACC_M, extra=' opacity=".8"', bias=-30)
    d = glow_defs("m", GLOW_M, "#FF6A10")
    for (cx, w, h, ch) in M_TUBES:
        x0 = cx - w / 2.0
        z0 = M_PZ + M_PD / 2.0 - 7.0
        sc.solid(raked(x0, M_DECK, z0, w, h, 14.0), "#39434B", STROKE, skip=("bottom",))
        sc.begin_group()
        sc.poly([(x0 + 1, M_DECK + 1, z0 - .3), (x0 + w - 1, M_DECK + 1, z0 - .3),
                 (x0 + w - 1, M_DECK + h - 1, z0 - .3), (x0 + 1, M_DECK + h - 1, z0 - .3)],
                "#141C23", "#9BB0BE", 0.7, bias=-2)
        sc.text_on_face((x0 + w / 2.0, M_DECK + h * 0.20, z0 - 1.1), (1, 0, 0), (0, 1, 0),
                        ch, h * 0.80, GLOW_M, depth_bias=-10)
        sc.end_group(proj((cx, M_DECK + h / 2, z0), sc.yaw, sc.pitch)[2] - 1.0)
    for yy in (M_DECK + 8, M_DECK + 15):
        sc.poly([(63.5, yy, M_PZ + M_PD / 2 - 7.4), (67.5, yy, M_PZ + M_PD / 2 - 7.4),
                 (67.5, yy + 3.4, M_PZ + M_PD / 2 - 7.4), (63.5, yy + 3.4, M_PZ + M_PD / 2 - 7.4)],
                GLOW_M, extra=' filter="url(#bsm)"')
    return sc.render(defs=d)


def mimi_ga():
    o = Ortho(scale=1.9)
    o.label(M_W / 2, M_DECK + 44, "FRONT ELEVATION", "#E7E4F0", 11, family="disp", weight="700")
    o.rect(0, 0, M_W, M_H, "#191823", "#2C2B3D")
    o.rect(2, 6, M_W - 4, 52, "#0F0F18", "#2C2B3D", 0.8)
    o.rect(13, 68, 150, 26, "#05070A", "#1D2A2C", 0.8)
    for i in range(16):
        for r in range(3):
            o.rect(16 + i * 9.1, 74 + r * 6, 5.6, 3, VFD_M,
                   extra=' opacity="%.2f"' % (0.85 if (i + r) % 3 else 0.18))
    o.rect(M_PX, M_H, M_PW, M_PH, "#22212F", "#2C2B3D")
    for (cx, w, h, ch) in M_TUBES:
        o.rect(cx - w / 2, M_DECK, w, h, "#141B20", "#8FA4B2", 0.8)
        o.label(cx, M_DECK + h * 0.32, ch, GLOW_M, h * 0.62, family="disp")
    for yy in (M_DECK + 8, M_DECK + 15):
        o.circle(65.5, yy + 1.6, 1.9, GLOW_M)
    for ex in (6, M_W - 22):
        o.poly([(ex, M_H), (ex + 16, M_H), (ex + 12, M_H + 30), (ex + 4, M_H + 30)],
               "#191823", "#2C2B3D")
    kx, ky = 42.0, 32.0
    o.circle(kx, ky, 13.5, "#1C1B27", "#3A3850", 0.9)
    o.line(kx, ky + 4, kx, ky + 12, ACC_M, 1.4)
    for lx in (100, 120):
        o.rect(lx - 2, ky - 7, 4, 14, "#1C1B27", "#3A3850", 0.7)
    for bx in (146, 164):
        o.circle(bx, ky, 4.2, "#1C1B27", "#3A3850", 0.7)
    o.dim_h(0, M_W, -9, "176")
    o.dim_h(13, 163, 62, "150 VFD")
    o.dim_v(0, M_H, -9, "112")
    o.dim_v(M_DECK, M_DECK + 24, -20, "24")

    SX = M_W + 56
    o.label(SX + 48, M_DECK + 44, "RIGHT PROFILE", "#E7E4F0", 11, family="disp", weight="700")
    o.poly([(SX, 0), (SX + M_D, 0), (SX + M_D, M_H), (SX + M_LEAN, M_H)], "#191823", "#2C2B3D")
    o.rect(SX + M_PZ, M_H, M_PD, M_PH, "#22212F", "#2C2B3D")
    o.rect(SX + M_PZ + M_PD / 2 - 7, M_DECK, 14, 24, "#141B20", "#8FA4B2", 0.8)
    o.poly([(SX + M_D - 26, M_H), (SX + M_D - 4, M_H), (SX + M_D - 8, M_H + 30), (SX + M_D - 22, M_H + 30)],
           "#191823", "#2C2B3D")
    o.dim_h(SX, SX + M_D, -9, "96")
    o.dim_v(0, M_H, SX - 8, "112")
    o.label(SX + M_D / 2, -22, "front face raked 8°", "#615C78", 8.4)

    PY = -70.0
    o.label(M_W / 2, PY + 8, "PLAN — THE OFFSET", "#E7E4F0", 11, family="disp", weight="700")
    o.rect(0, PY - M_D, M_W, M_D, "#131320", "#2C2B3D")
    o.rect(M_PX, PY - M_PZ - M_PD, M_PW, M_PD, "#22212F", ACC_M, 1.1)
    for (cx, w, h, ch) in M_TUBES:
        o.rect(cx - w / 2, PY - M_PZ - M_PD / 2 - 7, w, 14, "#141B20", "#8FA4B2", 0.8)
    for ex in (6, M_W - 22):
        o.rect(ex, PY - M_D + 4, 16, 22, "#191823", "#2C2B3D")
    o.dim_h(0, M_PX, PY - M_D - 10, "11 inset")
    o.label(M_W / 2, PY - M_D - 24, "EAR FINS AT THE REAR CORNERS · PLINTH 154 WIDE, INSET 11 · SET BACK 26",
            ACC_M, 8.6)
    return o.render()


# ---------------------------------------------------------------- QUADRANT-D
# desk miniature: 74 x 82 x 78, front raked 15 (lean 22), 4x IN-17 behind a window
Q_W, Q_H, Q_D, Q_LEAN = 74.0, 82.0, 78.0, 22.0
Q_PITCH_X, Q_PITCH_Y = 26.0, 27.0
Q_FACE_W, Q_FACE_H = 20.0, 15.0
Q_CX, Q_CY = Q_W / 2.0, 48.0
Q_DIGITS = ["1", "9", "4", "7"]


def quadrant_hero():
    sc = Scene(yaw=33, pitch=13, scale=4.5)
    sc.solid(raked(0, 0, 0, Q_W, Q_H, Q_D, Q_LEAN), CASE_Q, STROKE, skip=("bottom",))

    def fpt(xx, yy):
        return (xx, yy, Q_LEAN * (yy / Q_H) - 0.2)
    sc.begin_group()
    # recessed window
    ww, wh = Q_PITCH_X + Q_FACE_W + 6, Q_PITCH_Y + Q_FACE_H + 6
    sc.poly([fpt(Q_CX - ww / 2, Q_CY - wh / 2), fpt(Q_CX + ww / 2, Q_CY - wh / 2),
             fpt(Q_CX + ww / 2, Q_CY + wh / 2), fpt(Q_CX - ww / 2, Q_CY + wh / 2)],
            "#05070A", "#5A626B", 0.6, bias=-3)
    d = glow_defs("q", GLOW_Q, "#FF6A10")
    k = 0
    for ry in (1, -1):
        for rx in (-1, 1):
            cx = Q_CX + rx * Q_PITCH_X / 2.0
            cy = Q_CY + ry * Q_PITCH_Y / 2.0
            sc.poly([fpt(cx - Q_FACE_W / 2, cy - Q_FACE_H / 2), fpt(cx + Q_FACE_W / 2, cy - Q_FACE_H / 2),
                     fpt(cx + Q_FACE_W / 2, cy + Q_FACE_H / 2), fpt(cx - Q_FACE_W / 2, cy + Q_FACE_H / 2)],
                    "#141C23", "#9BB0BE", 0.5, bias=-6)
            m, dz = sc.face_matrix((cx, cy - Q_FACE_H * 0.34, Q_LEAN * (cy / Q_H) - 0.6),
                                   (1, 0, 0), (0, -1, 0))
            sc.items.append((dz - 9, '<g transform="%s"><text x="0" y="0" '
                             'font-family="IBM Plex Sans Condensed, Arial Narrow, sans-serif" '
                             'font-size="%.2f" fill="%s" text-anchor="middle">%s</text></g>'
                             % (m, Q_FACE_H * 0.92, GLOW_Q, Q_DIGITS[k])))
            k += 1
    # colon dots between rows, left of centre
    for dy in (-2.4, 2.4):
        disc(sc, fpt, Q_CX, Q_CY + dy, 1.15, GLOW_Q, extra=' filter="url(#bsq)"', n=12)
    sc.end_group(-1e6)
    # knob + button on the top deck
    sc.poly([(14, Q_H + .2, Q_LEAN + 14), (26, Q_H + .2, Q_LEAN + 14),
             (26, Q_H + .2, Q_LEAN + 26), (14, Q_H + .2, Q_LEAN + 26)],
            "#1C1F23", "#4A5058", 0.5)
    sc.poly([(52, Q_H + .2, Q_LEAN + 17), (60, Q_H + .2, Q_LEAN + 17),
             (60, Q_H + .2, Q_LEAN + 25), (52, Q_H + .2, Q_LEAN + 25)],
            "#1C1F23", ACC_Q, 0.5)
    return sc.render(defs=d)


def quadrant_ga():
    o = Ortho(scale=4.4)
    o.label(Q_W / 2, Q_H + 16, "FRONT ELEVATION", "#E4E1DA", 8, family="disp", weight="700")
    o.rect(0, 0, Q_W, Q_H, "#23282E", "#3A4149")
    ww, wh = Q_PITCH_X + Q_FACE_W + 6, Q_PITCH_Y + Q_FACE_H + 6
    o.rect(Q_CX - ww / 2, Q_CY - wh / 2, ww, wh, "#05070A", "#4A5058", 0.6)
    k = 0
    for ry in (1, -1):
        for rx in (-1, 1):
            cx = Q_CX + rx * Q_PITCH_X / 2.0
            cy = Q_CY + ry * Q_PITCH_Y / 2.0
            o.rect(cx - Q_FACE_W / 2, cy - Q_FACE_H / 2, Q_FACE_W, Q_FACE_H,
                   "#141B20", "#8FA4B2", 0.6)
            o.label(cx, cy - Q_FACE_H * 0.30, Q_DIGITS[k], GLOW_Q, Q_FACE_H * 0.8, family="disp")
            k += 1
    for dy in (-2.6, 2.6):
        o.circle(Q_CX - ww / 2 - 3.8, Q_CY + dy, 1.1, GLOW_Q)
    o.circle(20, Q_H - 66, 5.5, "#1C1F23", "#4A5058", 0.6)
    o.dim_h(0, Q_W, -5, "74")
    o.dim_h(Q_CX - Q_PITCH_X / 2, Q_CX + Q_PITCH_X / 2, Q_CY - wh / 2 - 6, "26")
    o.dim_v(0, Q_H, -5, "82")

    SX = Q_W + 34
    o.label(SX + Q_D / 2, Q_H + 16, "RIGHT PROFILE", "#E4E1DA", 8, family="disp", weight="700")
    o.poly([(SX, 0), (SX + Q_D, 0), (SX + Q_D, Q_H), (SX + Q_LEAN, Q_H)], "#23282E", "#3A4149")
    # the tube barrel lying along the depth axis — the whole point
    o.rect(SX + Q_LEAN * 0.55 + 2, Q_CY - 7, 24, 14, "#141B20", "#8FA4B2", 0.7)
    o.label(SX + Q_LEAN * 0.55 + 14, Q_CY + 9, "ИН-17, 22 DEEP", "#8B939C", 5.6)
    o.line(SX + Q_LEAN * 0.55 + 2, Q_CY, SX - 16, Q_CY + 12, ACC_Q, 0.7, "3 2")
    o.label(SX - 15, Q_CY + 15, "viewed down this axis only", ACC_Q, 5.6, anchor="start")
    o.dim_h(SX, SX + Q_D, -5, "78")
    o.label(SX + Q_D / 2, -14, "face raked back 15°", "#5A6169", 6)

    PY = -34.0
    o.label(Q_W / 2, PY + 6, "PLAN", "#E4E1DA", 8, family="disp", weight="700")
    o.rect(0, PY - Q_D, Q_W, Q_D, "#1A1F25", "#3A4149")
    for rx in (-1, 1):
        cx = Q_CX + rx * Q_PITCH_X / 2.0
        o.rect(cx - Q_FACE_W / 2, PY - Q_D + 30, Q_FACE_W, 24, "#141B20", "#8FA4B2", 0.6)
    o.label(Q_W / 2, PY - Q_D - 8, "TWO ROWS OF TWO, BARRELS RUNNING BACK INTO THE BODY",
            ACC_Q, 6)
    return o.render()


# ---------------------------------------------------------------- SCALER
S_W, S_H, S_D = 150.0, 190.0, 120.0
S_BEZEL_CY, S_BEZEL_R = 128.0, 27.0


def scaler_hero():
    sc = Scene(yaw=28, pitch=11, scale=2.15)
    sc.solid(raked(0, 0, 0, S_W, S_H, S_D, 0.0), CASE_S, STROKE, skip=("bottom",))
    z = -0.3
    sc.begin_group()

    def poly_circle(cx, cy, r, n, fill, stroke=None, sw=0.5, extra="", bias=-4.0):
        pts = [(cx + math.cos(2 * math.pi * i / n) * r, cy + math.sin(2 * math.pi * i / n) * r, z)
               for i in range(n)]
        sc.poly(pts, fill, stroke, sw, extra, bias=bias)
    # bezel + window
    poly_circle(S_W / 2, S_BEZEL_CY, S_BEZEL_R, 40, "#3A453D", "#4A564C", 0.9, bias=-3)
    poly_circle(S_W / 2, S_BEZEL_CY, S_BEZEL_R - 5, 40, "#05060A", "#2A2740", 0.7, bias=-5)
    # decatron ring
    for i in range(10):
        a = math.radians(i * 36 - 90)
        cx = S_W / 2 + math.cos(a) * (S_BEZEL_R - 11)
        cy = S_BEZEL_CY - math.sin(a) * (S_BEZEL_R - 11)
        lit = (i == 3)
        poly_circle(cx, cy, 2.4 if not lit else 3.1, 12,
                    ACC_S if lit else "#241F3A",
                    extra=' filter="url(#bss)"' if lit else "", bias=-8)
    # nixie rate strip
    sc.poly([(20, 84, z), (130, 84, z), (130, 108, z), (20, 108, z)], "#0E1310", "#334036", 0.8, bias=-3)
    for i, ch in enumerate("0024"):
        x = 26 + i * 17
        sc.poly([(x, 87, z - .2), (x + 12, 87, z - .2), (x + 12, 105, z - .2), (x, 105, z - .2)],
                "#141C23", "#9BB0BE", 0.6, bias=-6)
        sc.text_on_face((x + 6, 90, z - 1.0), (1, 0, 0), (0, 1, 0), ch, 15, GLOW_S, depth_bias=-9)
    sc.poly([(96, 87, z - .2), (108, 87, z - .2), (108, 105, z - .2), (96, 105, z - .2)],
            "#141C23", "#9BB0BE", 0.6, bias=-6)
    sc.text_on_face((102, 90, z - 1.0), (1, 0, 0), (0, 1, 0), "K", 13, GLOW_S, depth_bias=-9)
    # six-position mode selector
    kx, ky = 40.0, 44.0
    poly_circle(kx, ky, 11, 24, "#232C26", "#4E5A50", 0.9, bias=-6)
    for i in range(6):
        a = math.radians(-80 + i * 32)
        r1, r2 = 13.0, 17.0
        sc.poly([(kx + math.sin(a) * r1, ky + math.cos(a) * r1, z),
                 (kx + math.sin(a) * r2, ky + math.cos(a) * r2, z),
                 (kx + math.sin(a) * r2 + .7, ky + math.cos(a) * r2, z),
                 (kx + math.sin(a) * r1 + .9, ky + math.cos(a) * r1, z)], ACC_S, bias=-7)
    # banana jacks + mic port
    for jx in (108, 124):
        poly_circle(jx, 44, 4.2, 16, "#12160F", "#3B463E", 0.6)
    poly_circle(88, 44, 2.4, 12, "#12160F", "#3B463E", 0.5)
    # screws
    for sxp in (7, S_W - 7):
        for syp in (7, S_H - 7):
            poly_circle(sxp, syp, 2.6, 10, "#3A443C", "#2A322C", 0.4)
    sc.end_group(-1e6)
    return sc.render(defs=glow_defs("s", ACC_S, "#7B5CFF"))


def scaler_ga():
    o = Ortho(scale=2.1)
    o.label(S_W / 2, S_H + 14, "PANEL ELEVATION", "#D9D5C6", 11, family="disp", weight="700")
    o.rect(0, 0, S_W, S_H, "#212A24", "#313D35")
    o.circle(S_W / 2, S_BEZEL_CY, S_BEZEL_R, "#333D36", "#3B463E", 1.0)
    o.circle(S_W / 2, S_BEZEL_CY, S_BEZEL_R - 5, "#05060A", "#2A2740", 0.8)
    for i in range(10):
        a = math.radians(i * 36 - 90)
        o.circle(S_W / 2 + math.cos(a) * (S_BEZEL_R - 11), S_BEZEL_CY + math.sin(a) * (S_BEZEL_R - 11),
                 3.0 if i == 3 else 2.3, ACC_S if i == 3 else "#241F3A")
    o.rect(20, 84, 110, 24, "#0E1310", "#2b352e", 0.8)
    for i, ch in enumerate("0024"):
        x = 26 + i * 17
        o.rect(x, 87, 12, 18, "#141B20", "#8FA4B2", 0.6)
        o.label(x + 6, 91, ch, GLOW_S, 13, family="disp")
    o.rect(96, 87, 12, 18, "#141B20", "#8FA4B2", 0.6)
    o.label(102, 91, "K", GLOW_S, 11, family="disp")
    kx, ky = 40.0, 44.0
    o.circle(kx, ky, 11, "#1A211D", "#3B463E", 0.9)
    MODES = ["BKG", "ENT", "MAINS", "AUDIO", "EXT", "OFF"]
    for i in range(6):
        a = math.radians(-80 + i * 32)
        o.line(kx + math.sin(a) * 13, ky + math.cos(a) * 13,
               kx + math.sin(a) * 17, ky + math.cos(a) * 17, ACC_S, 1.1)
        o.label(kx + math.sin(a) * 23, ky + math.cos(a) * 23 - 1, MODES[i], "#8B958D", 5.6)
    for jx in (108, 124):
        o.circle(jx, 44, 4.2, "#12160F", "#3B463E", 0.7)
    o.label(116, 30, "EXT PULSE", "#8B958D", 5.6)
    o.circle(88, 44, 2.4, "#12160F", "#3B463E", 0.6)
    o.label(88, 34, "MIC", "#8B958D", 5.6)
    for sxp in (7, S_W - 7):
        for syp in (7, S_H - 7):
            o.circle(sxp, syp, 2.6, "#3A443C", "#2A322C", 0.5)
    o.label(S_W / 2, 165, "SCALER-06", "#D9D5C6", 9, family="disp", weight="700")
    o.dim_h(0, S_W, -8, "150")
    o.dim_v(0, S_H, -8, "190")

    SX = S_W + 46
    o.label(SX + S_D / 2, S_H + 14, "RIGHT PROFILE", "#D9D5C6", 11, family="disp", weight="700")
    o.rect(SX, 0, S_D, S_H, "#212A24", "#313D35")
    o.rect(SX + 4, S_BEZEL_CY - 22, 44, 44, "#1A211D", "#3B463E", 0.8)
    o.label(SX + 26, S_BEZEL_CY - 2, "ОГ-3 DOME", "#8B958D", 6)
    o.rect(SX + 60, 40, 52, 96, "#171E1A", "#3B463E", 0.7)
    o.label(SX + 86, 84, "400 V + LOGIC", "#8B958D", 6)
    o.dim_h(SX, SX + S_D, -8, "120")
    return o.render()


# ---------------------------------------------------------------- write
def main():
    files = {
        "svg-terminal-hero.svg": terminal_hero(),
        "svg-terminal-ga.svg": terminal_ga(),
        "svg-mimi-hero.svg": mimi_hero(),
        "svg-mimi-ga.svg": mimi_ga(),
        "svg-quadrant-hero.svg": quadrant_hero(),
        "svg-quadrant-ga.svg": quadrant_ga(),
        "svg-scaler-hero.svg": scaler_hero(),
        "svg-scaler-ga.svg": scaler_ga(),
    }
    for name, s in files.items():
        with open(os.path.join(OUT, name), "w") as f:
            f.write(s)
        print(name, len(s))


if __name__ == "__main__":
    main()
