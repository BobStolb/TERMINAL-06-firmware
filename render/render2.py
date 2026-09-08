#!/usr/bin/env python3
"""Photographic front elevations, rear panels and macros for the -06 family.

Orthographic, in millimetres, y DOWN from the top of the object. Every view is
built from the shared primitives in tubes.py so a tube looks the same wherever
it appears.
"""
import math, os
import tubes as T
from render import Scene, raked, proj, mix

OUT = os.path.dirname(os.path.abspath(__file__))
MONO, COND = T.MONO, T.COND


class Sheet:
    """A millimetre canvas. y increases downward from the top of the object."""

    def __init__(self, pid, defs=""):
        self.p = pid
        self.defs = [defs]
        self.body = []
        self.xs, self.ys = [], []

    def d(self, s):
        self.defs.append(s)

    def add(self, s):
        self.body.append(s)

    def bound(self, x0, y0, x1, y1):
        self.xs += [x0, x1]
        self.ys += [y0, y1]

    def rect(self, x, y, w, h, fill, stroke=None, sw=.3, rx=0, extra=""):
        self.bound(x, y, x + w, y + h)
        st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
        r = f' rx="{rx}"' if rx else ""
        self.add(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" '
                 f'fill="{fill}"{st}{r}{extra}/>')

    def line(self, x1, y1, x2, y2, stroke, sw=.3, dash=None, op=1.0):
        self.bound(min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
        dl = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
                 f'stroke="{stroke}" stroke-width="{sw}"{dl} opacity="{op}"/>')

    def circle(self, cx, cy, r, fill, stroke=None, sw=.3, extra=""):
        self.bound(cx - r, cy - r, cx + r, cy + r)
        st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
        self.add(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="{fill}"{st}{extra}/>')

    def txt(self, *a, **k):
        self.add(T.text(*a, **k))

    def raw(self, s):
        self.add(s)

    def group(self, transform, inner):
        self.add(f'<g transform="{transform}">{inner}</g>')

    def render(self, pad=9, scale=4.0, aspect_pad_y=None):
        x0, x1 = min(self.xs) - pad, max(self.xs) + pad
        y0, y1 = min(self.ys) - pad, max(self.ys) + (aspect_pad_y or pad)
        return (f'<svg viewBox="{x0:.1f} {y0:.1f} {x1-x0:.1f} {y1-y0:.1f}" '
                f'xmlns="http://www.w3.org/2000/svg" role="img">'
                f'<defs>{"".join(self.defs)}</defs>\n' + "\n".join(self.body) + '</svg>')


def dim_h(s, x1, x2, y, label, col="#5E646C", size=2.4):
    s.line(x1, y, x2, y, col, .22)
    for x in (x1, x2):
        s.line(x, y - .9, x, y + .9, col, .22)
    s.txt((x1 + x2) / 2, y + 2.7, label, col, size)


def dim_v(s, y1, y2, x, label, col="#5E646C", size=2.4):
    s.line(x, y1, x, y2, col, .22)
    for y in (y1, y2):
        s.line(x - .9, y, x + .9, y, col, .22)
    s.add(f'<text x="{x-1.3:.2f}" y="{(y1+y2)/2:.2f}" font-family="{MONO}" font-size="{size}" '
          f'fill="{col}" text-anchor="middle" transform="rotate(-90 {x-1.3:.2f} {(y1+y2)/2:.2f})">'
          f'{label}</text>')


def reflection(s, pid, y_base, height, opacity=.20):
    """Mirror everything drawn so far below the baseline, faded with a mask so the
    page background stays visible through it."""
    inner = "\n".join(s.body)
    x0, x1 = min(s.xs) - 24, max(s.xs) + 24
    s.d(f'<linearGradient id="{pid}-fade" x1="0" y1="{y_base}" x2="0" y2="{y_base+height}" '
        f'gradientUnits="userSpaceOnUse">'
        f'<stop offset="0" stop-color="#fff" stop-opacity=".9"/>'
        f'<stop offset=".45" stop-color="#fff" stop-opacity=".28"/>'
        f'<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        f'<mask id="{pid}-refmask"><rect x="{x0}" y="{y_base}" width="{x1-x0}" '
        f'height="{height}" fill="url(#{pid}-fade)"/></mask>')
    s.add(f'<g transform="translate(0 {2*y_base:.2f}) scale(1 -1)" opacity="{opacity}" '
          f'mask="url(#{pid}-refmask)" filter="url(#{pid}-blur3)">{inner}</g>')
    s.bound(x0, y_base, x1, y_base + height)


# =============================================================== TERMINAL-06
TW, TBASE_H, TPL_H, TTUBE_H = 237.0, 56.0, 16.0, 24.0
T_DECK = TTUBE_H                      # y of the plinth top
T_BASE_Y = TTUBE_H + TPL_H            # 40
T_BOT = T_BASE_Y + TBASE_H            # 96
T_PX, T_PW = 12.0, 213.0
TUBES = [(24.5, 22, 24, "2"), (49.5, 22, 24, "0"),
         (81.5, 22, 24, "4"), (106.5, 22, 24, "7"),
         (137.0, 15, 20, "3"), (155.0, 15, 20, "1"),
         (189.5, 22, 24, "A"), (212.5, 22, 24, "P")]
ACC_T, GLOW_T = "#F25610", "#FF9E36"
SCREENS = ["RUN", "TIME", "DISP", "AMB", "INFO", "DATE"]


def t_defs(p):
    return (T.tube_defs(p) + T.panel_defs(p, ACC_T) + f'''
<linearGradient id="{p}-deck" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#333a41"/><stop offset=".18" stop-color="#242a30"/>
  <stop offset="1" stop-color="#171b20"/>
</linearGradient>
<radialGradient id="{p}-pool" cx=".5" cy="0" r=".9">
  <stop offset="0" stop-color="{GLOW_T}" stop-opacity=".42"/>
  <stop offset="1" stop-color="{GLOW_T}" stop-opacity="0"/>
</radialGradient>
<linearGradient id="{p}-inlay" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#ff8a3c"/><stop offset=".5" stop-color="{ACC_T}"/>
  <stop offset="1" stop-color="#a8330a"/>
</linearGradient>''')


def terminal_front(lit=True):
    p = "tf"
    s = Sheet(p, t_defs(p))

    # ---- base slab -------------------------------------------------------
    s.rect(0, T_BASE_Y, TW, TBASE_H, f"url(#{p}-case)", "#3d444c", .4, rx=1.6)
    s.line(1, T_BASE_Y + .35, TW - 1, T_BASE_Y + .35, "#59626b", .3, op=.7)
    # fascia recess
    s.rect(2, T_BASE_Y + 2, TW - 4, 52, f"url(#{p}-fascia)", "#0b0d10", .5, rx=.8)
    s.rect(2.5, T_BASE_Y + 2.5, TW - 5, 51, "none", "#454d55", .22, rx=.6)

    fy = T_BASE_Y + 2                    # fascia top
    cy = fy + 28                         # control centreline

    # zone dividers + labels
    for x in (102, 178):
        s.line(x, fy + 4, x, fy + 40, "#39414a", .3)
    s.txt(46, fy + 45.5, "SCREEN", "#7d858e", 2.4, ls=1.9)
    s.txt(140, fy + 8.0, "FIELD", "#7d858e", 2.4, ls=1.9)
    s.txt(206, fy + 8.0, "VALUE", "#7d858e", 2.4, ls=1.9)

    # ---- dial ------------------------------------------------------------
    kx = 46.0
    for i, nm in enumerate(SCREENS):
        a = math.radians(-80 + i * 32)
        r1, r2 = 15.4, 18.2
        s.line(kx + math.sin(a) * r1, cy - math.cos(a) * r1,
               kx + math.sin(a) * r2, cy - math.cos(a) * r2,
               ACC_T if i == 0 else "#aeb5bc", .55)
        lx, ly = kx + math.sin(a) * 22.6, cy - math.cos(a) * 22.6
        an = "middle" if abs(math.sin(a)) < .12 else ("start" if math.sin(a) > 0 else "end")
        s.txt(lx, ly + .9, nm, ACC_T if i == 0 else "#98a0a8", 2.9, anchor=an, ls=.6)
    s.raw(T.knob(p, kx, cy, 11.5, ACC_T, pointer_deg=-80))
    s.bound(kx - 26, cy - 26, kx + 26, cy + 26)

    # ---- levers ----------------------------------------------------------
    for lx, lab, tilt in ((134, "A", 1), (154, "B", -1)):
        s.raw(T.lever(p, lx, cy, 7.2, tilt))
        s.txt(lx, cy + 13.5, lab, "#aeb5bc", 3.2, family=COND, weight="600")
        s.bound(lx - 6, cy - 10, lx + 6, cy + 15)

    # ---- buttons ---------------------------------------------------------
    for bx, lab in ((194, "&#8722;"), (214, "+")):
        s.raw(T.button(p, bx, cy, 4.6))
        s.txt(bx, cy + 13.5, lab, "#aeb5bc", 3.6, family=COND, weight="600")
        s.bound(bx - 6, cy - 6, bx + 6, cy + 15)

    # ---- wordmark and serial --------------------------------------------
    wy = fy + 46
    s.raw(T.hexmark(116, wy - 1.1, 3.0, "#8b9299"))
    s.txt(122, wy, "TERMINAL · 06", "#9aa1a8", 3.3, anchor="start", family=COND,
          weight="600", ls=1.6)
    s.txt(232, wy, "SER 003 / 010", "#5e666e", 2.3, anchor="end", ls=.8)

    # ---- plinth ----------------------------------------------------------
    s.rect(T_PX, T_DECK, T_PW, TPL_H, f"url(#{p}-deck)", "#3d444c", .4)
    # SIGNAL inlay — the accent the deleted brow left homeless
    s.rect(T_PX + 8, T_DECK + TPL_H - 4.4, T_PW - 16, 1.3, f"url(#{p}-inlay)", rx=.4)
    s.rect(T_PX + 8, T_DECK + TPL_H - 4.4, T_PW - 16, 1.3, f"url(#{p}-inlay)",
           extra=f' filter="url(#{p}-blur3)" opacity=".28"')
    # glow pool spilling onto the deck
    if lit:
        s.rect(T_PX, T_DECK, T_PW, 9, f"url(#{p}-pool)")

    # ---- tubes -----------------------------------------------------------
    for cx, w, h, ch in TUBES:
        x0, y0 = cx - w / 2, TTUBE_H - h
        glyphs = "0123456789" if ch.isdigit() else ("AWFHVS" if ch == "A" else "PMKnm%")
        s.group(f"translate({x0:.2f} {y0:.2f})",
                T.tube_face(p, w, h, ch if lit else None, glyphset=glyphs,
                            digit_frac=.72 if ch.isdigit() else .60))
        s.bound(x0 - 2, y0 - 2, x0 + w + 2, y0 + h + 2)

    # colon
    for dy in (8.5, 15.5):
        s.raw(T.neon_dot(p, 65.5, dy, 1.5, on=lit))
    s.bound(62, 6, 69, 18)

    # "m" stencil on the plinth face
    s.txt(201, T_DECK + 7.4, "m", GLOW_T if lit else "#4a4038", 5.0, family=COND, weight="600")
    if lit:
        s.txt(201, T_DECK + 7.4, "m", GLOW_T, 5.0, family=COND, weight="600", op=.55)

    reflection(s, p, T_BOT, 26)
    return s.render(pad=14, aspect_pad_y=30)


def terminal_rear():
    p = "tr"
    s = Sheet(p, T.panel_defs(p, ACC_T))
    H = T_BOT
    s.rect(0, 0, TW, H, f"url(#{p}-case)", "#3d444c", .4, rx=1.6)
    s.rect(3, 3, TW - 6, H - 6, "none", "#2b3239", .3, rx=1)

    # vent slots
    for i in range(5):
        s.rect(150 + i * 11, 22, 5.5, 46, "#0a0d10", "#333a41", .25, rx=1.4)
    s.txt(177, 76, "CONVERTER VENT", "#5e666e", 2.4, ls=1.4)

    # DC jack
    s.circle(34, 34, 6.2, "#12161a", "#4a525b", .5)
    s.circle(34, 34, 3.0, "#05070a", "#333a41", .35)
    s.txt(34, 46, "DC IN  12 V  2 A", "#98a0a8", 2.7, ls=.7)
    s.txt(34, 51, "CENTRE POSITIVE", "#5e666e", 2.2, ls=.6)

    # USB service slot
    s.rect(72, 30, 16, 8, "#0a0d10", "#4a525b", .45, rx=1)
    s.txt(80, 46, "USB · FIRMWARE", "#98a0a8", 2.7, ls=.7)
    s.txt(80, 51, "D0 / D1 SERIAL", "#5e666e", 2.2, ls=.6)

    # HV warning
    s.raw(f'<polygon points="112,26 121,42 103,42" fill="none" stroke="{ACC_T}" '
          f'stroke-width=".8" stroke-linejoin="round"/>')
    s.txt(112, 39.5, "!", ACC_T, 5.0, family=COND, weight="700")
    s.txt(112, 48, "185 V DC INSIDE", ACC_T, 2.6, ls=.7)
    s.txt(112, 53, "BLEED BEFORE OPENING", "#98a0a8", 2.2, ls=.6)
    s.bound(100, 22, 124, 55)

    # always-on note + wordmark
    s.txt(34, 62, "ALWAYS ON · NO SWITCH", "#5e666e", 2.4, ls=.7)
    s.raw(T.hexmark(16, 84, 3.4, "#8b9299"))
    s.txt(23, 85.4, "TERMINAL · 06", "#9aa1a8", 3.4, anchor="start", family=COND,
          weight="600", ls=1.6)
    s.txt(233, 85.4, "SER 003 / 010   MADE BY HAND", "#5e666e", 2.4, anchor="end", ls=.8)
    s.txt(233, 90.5, "LIMITED RUN OF TEN", "#4a525b", 2.2, anchor="end", ls=.8)

    # feet
    for fx in (18, TW - 18):
        s.rect(fx - 9, H - 3.2, 18, 3.2, "#0e1114", rx=1)
    return s.render(pad=12)


def terminal_macro():
    """One ИН-12А, large — the shot the trench made impossible."""
    p = "tm"
    s = Sheet(p, T.tube_defs(p) + T.panel_defs(p, ACC_T))
    SC = 5.0
    W, H = 22.0 * SC, 24.0 * SC          # drawn at size so the mesh stays fine
    s.raw(T.tube_face(p, W, H, "4", digit_frac=.72, ghost_op=.16, spec_op=.45,
                      mesh_op=.30, socket=False))
    s.bound(-4, -4, W + 4, H + 4)
    # socket + pins
    s.rect(W * .12, H, W * .76, 5, "#141a1f", "#333c44", .5, rx=1)
    for i in range(12):
        x = W * .16 + i * (W * .68 / 11)
        s.line(x, H + 5, x, H + 14, "#59626b", .9)
    s.bound(0, 0, W, H + 18)
    cx = W + 14
    for frac_from, frac_to, col, txt in (
            (.16, .05, "#7d858e", "MESH ANODE — SHARED, ONE PER TUBE"),
            (.42, .29, "#98a0a8", "LIT CATHODE — WIRE-FORMED, ONE PER GLYPH"),
            (.68, .57, "#7d858e", "NINE UNLIT CATHODES, STACKED IN DEPTH"),
            (.88, .80, "#7d858e", "GLASS ENVELOPE 22 × 24 × 14")):
        s.line(W * .55, H * frac_from, cx - 4, H * frac_to, "#5E646C", .5, "3 2")
        s.txt(cx, H * frac_to + 1.2, txt, col, 3.4, anchor="start", ls=.6)
    s.line(W * .5, H + 10, cx - 4, H + 7, "#5E646C", .5, "3 2")
    s.txt(cx, H + 8.2, "12 LEADS · ПЛ31 SOCKET", "#7d858e", 3.4, anchor="start", ls=.6)
    s.bound(cx, 0, cx + 120, H + 18)
    return s.render(pad=10)


# ---------------------------------------------------------------- MIMI-06
MW, M_BASE_H, M_PL_H = 176.0, 112.0, 14.0
M_DECK, M_BASE_Y = 24.0, 38.0
M_BOT = M_BASE_Y + M_BASE_H           # 150
M_PX, M_PW = 11.0, 154.0
MTUBES = [(24.5, 22, 24, "2"), (49.5, 22, 24, "0"), (81.5, 22, 24, "4"),
          (106.5, 22, 24, "7"), (137.0, 15, 20, "3"), (155.0, 15, 20, "1")]
ACC_M, VFD_M = "#FF2E88", "#7CF5DC"

F57 = {" ": [0,0,0,0,0], "(": [0,0x1C,0x22,0x41,0], ")": [0,0x41,0x22,0x1C,0],
       "^": [4,2,1,2,4], "_": [0x40]*5, ":": [0,0x36,0x36,0,0],
       "0": [0x3E,0x51,0x49,0x45,0x3E], "2": [0x42,0x61,0x51,0x49,0x46],
       "4": [0x18,0x14,0x12,0x7F,0x10], "7": [1,0x71,9,5,3],
       "S": [0x46,0x49,0x49,0x49,0x31], "U": [0x3F,0x40,0x40,0x40,0x3F],
       "N": [0x7F,4,8,0x10,0x7F]}


def mimi_front():
    p = "mf"
    s = Sheet(p, T.tube_defs(p) + T.panel_defs(p, ACC_M) + f'''
<linearGradient id="{p}-shell" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#2b2939"/><stop offset=".45" stop-color="#1c1b28"/>
  <stop offset="1" stop-color="#12111b"/>
</linearGradient>
<radialGradient id="{p}-vpool" cx=".5" cy=".5" r=".62">
  <stop offset="0" stop-color="{VFD_M}" stop-opacity=".20"/>
  <stop offset="1" stop-color="{VFD_M}" stop-opacity="0"/>
</radialGradient>
<radialGradient id="{p}-pool" cx=".5" cy="0" r=".9">
  <stop offset="0" stop-color="#FF9E36" stop-opacity=".38"/>
  <stop offset="1" stop-color="#FF9E36" stop-opacity="0"/>
</radialGradient>''')

    # ear fins
    for ex in (-2.0, MW - 12.0):
        s.raw(f'<path d="M{ex:.1f} {M_BASE_Y+10:.1f} L{ex+14:.1f} {M_BASE_Y+10:.1f} '
              f'L{ex+11:.1f} {M_DECK-6:.1f} L{ex+3:.1f} {M_DECK-6:.1f} Z" '
              f'fill="url(#{p}-shell)" stroke="#3a3850" stroke-width=".4"/>')
        s.rect(ex + 5.5, M_DECK - 2, 3, M_BASE_Y + 8 - (M_DECK - 2), ACC_M, rx=1)
        s.bound(ex - 2, M_DECK - 8, ex + 16, M_BASE_Y + 12)

    s.rect(0, M_BASE_Y, MW, M_BASE_H, f"url(#{p}-shell)", "#3a3850", .4, rx=2)
    s.line(1, M_BASE_Y + .35, MW - 1, M_BASE_Y + .35, "#5d5a78", .3, op=.6)

    # VFD window
    vy = M_BASE_Y + 12
    s.rect(13, vy, 150, 26, "#04070a", "#223336", .6, rx=.8)
    s.rect(11, vy - 2, 154, 30, "none", "#3a3850", .35, rx=1.2)
    s.rect(13, vy, 150, 26, f"url(#{p}-vpool)")
    MSG = "(^_^)  20:47 SUN"
    for i, ch in enumerate(MSG[:16]):
        g = F57.get(ch, F57[" "])
        for col in range(5):
            for row in range(7):
                on = (g[col] >> row) & 1
                x = 16.5 + i * 9.3 + col * 1.62
                y = vy + 3.4 + row * 2.86
                if on:
                    s.add(f'<rect x="{x:.2f}" y="{y:.2f}" width="1.34" height="1.34" rx=".3" '
                          f'fill="{VFD_M}" opacity=".95"/>')
                    s.add(f'<rect x="{x-.4:.2f}" y="{y-.4:.2f}" width="2.14" height="2.14" rx=".5" '
                          f'fill="{VFD_M}" opacity=".35" filter="url(#{p}-softglow)"/>')
                else:
                    s.add(f'<rect x="{x:.2f}" y="{y:.2f}" width="1.34" height="1.34" rx=".3" '
                          f'fill="{VFD_M}" opacity=".05"/>')
    s.txt(163, vy + 30.5, "FUTABA 16 × 5 × 7", "#615c78", 2.2, anchor="end", ls=.9)

    # fascia
    fy = vy + 34
    s.rect(4, fy, MW - 8, 52, f"url(#{p}-fascia)", "#0b0a12", .5, rx=.8)
    cy = fy + 26
    for x in (76, 132):
        s.line(x, fy + 4, x, fy + 38, "#33314a", .3)
    s.txt(42, fy + 44.5, "screen", "#8a85a3", 2.4, ls=1.7)
    s.txt(104, fy + 8.0, "field", "#8a85a3", 2.4, ls=1.7)
    s.txt(155, fy + 8.0, "value", "#8a85a3", 2.4, ls=1.7)
    for i, nm in enumerate(["run", "time", "glow", "amb", "info", "date"]):
        a = math.radians(-80 + i * 32)
        s.line(42 + math.sin(a) * 14.2, cy - math.cos(a) * 14.2,
               42 + math.sin(a) * 16.6, cy - math.cos(a) * 16.6,
               ACC_M if i == 0 else "#9d98b5", .5)
        an = "middle" if abs(math.sin(a)) < .12 else ("start" if math.sin(a) > 0 else "end")
        s.txt(42 + math.sin(a) * 20.4, cy - math.cos(a) * 20.4 + .9, nm,
              ACC_M if i == 0 else "#8a85a3", 2.8, anchor=an, ls=.5)
    s.raw(T.knob(p, 42, cy, 10.5, ACC_M, pointer_deg=-80))
    s.bound(16, cy - 24, 68, cy + 24)
    for lx, lab, tl in ((100, "a", 1), (120, "b", -1)):
        s.raw(T.lever(p, lx, cy, 6.6, tl))
        s.txt(lx, cy + 12.4, lab, "#9d98b5", 3.0, family=COND, weight="600")
    for bx, lab in ((146, "&#8722;"), (164, "+")):
        s.raw(T.button(p, bx, cy, 4.2))
        s.txt(bx, cy + 12.4, lab, "#9d98b5", 3.4, family=COND, weight="600")
    s.txt(122, fy + 46, "MIMI·06 «KURO»", "#8a85a3", 3.0,
          family=COND, weight="600", ls=1.4)

    # plinth + tubes
    s.rect(M_PX, M_DECK, M_PW, M_PL_H, f"url(#{p}-shell)", "#3a3850", .4)
    s.rect(M_PX, M_DECK, M_PW, 8, f"url(#{p}-pool)")
    for cx, w, h, ch in MTUBES:
        x0, y0 = cx - w / 2, M_DECK - h
        s.group(f"translate({x0:.2f} {y0:.2f})", T.tube_face(p, w, h, ch, digit_frac=.72))
        s.bound(x0 - 2, y0 - 2, x0 + w + 2, y0 + h + 2)
    for dy in (8.5, 15.5):
        s.raw(T.neon_dot(p, 65.5, dy, 1.5))

    reflection(s, p, M_BOT, 26)
    return s.render(pad=15, aspect_pad_y=30)


# ---------------------------------------------------------------- QUADRANT-D
QW, QH = 74.0, 82.0
Q_PX, Q_PY = 26.0, 27.0
Q_FW, Q_FH = 20.0, 15.0
Q_CX, Q_CY = QW / 2, 34.0
ACC_Q = "#6E9AC4"


def quadrant_front():
    p = "qf"
    s = Sheet(p, T.tube_defs(p) + T.panel_defs(p, ACC_Q) + f'''
<linearGradient id="{p}-body" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#333a41"/><stop offset=".4" stop-color="#22272d"/>
  <stop offset="1" stop-color="#15181c"/>
</linearGradient>''')
    s.rect(0, 0, QW, QH, f"url(#{p}-body)", "#454d55", .4, rx=2.4)
    s.line(1.4, .4, QW - 1.4, .4, "#6a737c", .3, op=.7)

    ww, wh = Q_PX + Q_FW + 7, Q_PY + Q_FH + 7
    s.rect(Q_CX - ww / 2, Q_CY - wh / 2, ww, wh, "#05070a", "#4a525b", .5, rx=1.2)
    s.rect(Q_CX - ww / 2 + .8, Q_CY - wh / 2 + .8, ww - 1.6, wh - 1.6, "none", "#22282e", .3, rx=.9)

    digits = ["1", "9", "4", "7"]
    k = 0
    for ry in (-1, 1):
        for rx in (-1, 1):
            cx = Q_CX + rx * Q_PX / 2
            cy = Q_CY + ry * Q_PY / 2
            s.group(f"translate({cx-Q_FW/2:.2f} {cy-Q_FH/2:.2f})",
                    T.tube_face(p, Q_FW, Q_FH, digits[k], digit_frac=.76, socket=False))
            k += 1
    for dy in (-2.6, 2.6):
        s.raw(T.neon_dot(p, Q_CX, Q_CY + dy, 1.0))

    # top-deck controls, seen edge-on in elevation
    s.rect(14, -2.6, 12, 2.6, "#2b3138", "#59626b", .3, rx=.8)
    s.rect(52, -2.2, 8, 2.2, "#2b3138", ACC_Q, .3, rx=.7)
    s.bound(10, -5, QW - 10, QH)

    s.txt(Q_CX, QH - 6.5, "QUADRANT", "#9aa1a8", 3.2, family=COND, weight="600", ls=2.0)
    s.txt(Q_CX, QH - 2.8, "ИН-17×4 · HH:MM AT ONCE", "#5e666e", 2.1, ls=.7)
    s.raw(T.hexmark(10, QH - 7.4, 2.6, "#7d858e"))

    reflection(s, p, QH, 20)
    return s.render(pad=12, aspect_pad_y=24)


# ---------------------------------------------------------------- SCALER-06
SW, SH = 150.0, 190.0
ACC_S, VIO = "#A98BFF", "#7B5CFF"
S_MODES = ["BKG", "ENT", "MAINS", "AUDIO", "EXT", "OFF"]


def scaler_front():
    p = "sf"
    s = Sheet(p, T.tube_defs(p) + T.panel_defs(p, ACC_S) + f'''
<linearGradient id="{p}-panel" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#2a342d"/><stop offset=".4" stop-color="#1e2722"/>
  <stop offset="1" stop-color="#161d19"/>
</linearGradient>
<radialGradient id="{p}-bez" cx=".34" cy=".26" r=".9">
  <stop offset="0" stop-color="#4b574e"/><stop offset=".62" stop-color="#2b342e"/>
  <stop offset="1" stop-color="#171e1a"/>
</radialGradient>
<radialGradient id="{p}-vglow" cx=".5" cy=".5" r=".5">
  <stop offset="0" stop-color="{VIO}" stop-opacity=".55"/>
  <stop offset="1" stop-color="{VIO}" stop-opacity="0"/>
</radialGradient>''')
    s.rect(0, 0, SW, SH, f"url(#{p}-panel)", "#3d4a41", .4, rx=1.6)
    s.rect(2.6, 2.6, SW - 5.2, SH - 5.2, "none", "#2b342e", .3, rx=1)
    for sx in (7, SW - 7):
        for sy in (7, SH - 7):
            s.circle(sx, sy, 2.4, "#39443c", "#242c26", .3)
            s.line(sx - 1.4, sy, sx + 1.4, sy, "#1c221e", .4)

    # ---- bezel + decatron ring ------------------------------------------
    bcy, br = 58.0, 27.0
    s.circle(SW / 2, bcy, br, f"url(#{p}-bez)", "#4d5a50", .6)
    s.circle(SW / 2, bcy, br - 5.4, "#05060a", "#2a2740", .5)
    s.circle(SW / 2, bcy, br - 5.4, f"url(#{p}-vglow)", extra=' opacity=".22"')
    for i in range(10):
        a = math.radians(i * 36 - 90)
        gx = SW / 2 + math.cos(a) * (br - 11.5)
        gy = bcy + math.sin(a) * (br - 11.5)
        lit = (i == 3)
        if lit:
            s.circle(gx, gy, 6.4, VIO, extra=f' opacity=".55" filter="url(#{p}-bigglow)"')
            s.circle(gx, gy, 2.9, "#C9B4FF", extra=f' filter="url(#{p}-midglow)"')
            s.circle(gx, gy, 1.7, "#EFE7FF")
        else:
            s.circle(gx, gy, 2.1, "#251f3c", "#2f2848", .18)
        # guide cathodes
        for gsub in (12, 24):
            ga = math.radians(i * 36 - 90 + gsub)
            s.circle(SW / 2 + math.cos(ga) * (br - 11.5), bcy + math.sin(ga) * (br - 11.5),
                     .85, "#2a2340")
        s.txt(SW / 2 + math.cos(a) * (br - 2.6), bcy + math.sin(a) * (br - 2.6) + .8,
              str(i), ACC_S if lit else "#4e4770", 2.3)
    s.txt(SW / 2, bcy + br + 5.4, "ОГ-3 SELF-SCANNING RING", "#6d786f", 2.3, ls=1.4)

    # ---- nixie rate strip ------------------------------------------------
    ry = 98.0
    s.rect(18, ry, 114, 30, "#0d1210", "#334036", .5, rx=.8)
    for i, ch in enumerate("0024"):
        x = 24 + i * 19
        s.group(f"translate({x:.2f} {ry+3:.2f})", T.tube_face(p, 14, 24, ch, digit_frac=.74))
    s.group(f"translate({100:.2f} {ry+3:.2f})",
            T.tube_face(p, 14, 24, "K", glyphset="mMKn%", digit_frac=.62))
    s.txt(122, ry + 20, "CPM", "#6d786f", 2.6, ls=.8)
    s.txt(75, ry + 35, "COUNTS PER MINUTE · 60 s ROLLING", "#6d786f", 2.2, ls=1.3)

    # ---- mode selector ---------------------------------------------------
    kx, ky = 40.0, 152.0
    for i, nm in enumerate(S_MODES):
        a = math.radians(-80 + i * 32)
        s.line(kx + math.sin(a) * 12.6, ky - math.cos(a) * 12.6,
               kx + math.sin(a) * 15.0, ky - math.cos(a) * 15.0,
               ACC_S if i == 0 else "#a9b3ab", .5)
        an = "middle" if abs(math.sin(a)) < .12 else ("start" if math.sin(a) > 0 else "end")
        s.txt(kx + math.sin(a) * 18.8, ky - math.cos(a) * 18.8 + .9, nm,
              ACC_S if i == 0 else "#8e988f", 2.5, anchor=an, ls=.5)
    s.raw(T.knob(p, kx, ky, 9.4, ACC_S, pointer_deg=-80))
    s.bound(kx - 24, ky - 22, kx + 24, ky + 22)

    # ---- jacks + mic ------------------------------------------------------
    for jx, lab in ((104, ""), (122, "")):
        s.circle(jx, 150, 4.6, "#0f140f", "#4d5a50", .5)
        s.circle(jx, 150, 2.2, "#05070a")
    s.txt(113, 141, "EXT PULSE", "#8e988f", 2.4, ls=.7)
    s.txt(104, 159.5, "IN", "#6d786f", 2.1)
    s.txt(122, 159.5, "GND", "#6d786f", 2.1)
    s.circle(83, 150, 2.4, "#0f140f", "#4d5a50", .4)
    for i in range(6):
        s.circle(83, 150, 1.4 - i * .18, "#05070a" if i % 2 else "#0f140f")
    s.txt(83, 141, "MIC", "#8e988f", 2.4, ls=.7)

    # ---- wordmark + safety ------------------------------------------------
    s.raw(T.hexmark(14, 175, 3.0, "#8e988f"))
    s.txt(20, 176.4, "SCALER · 06", "#a9b3ab", 3.4, anchor="start", family=COND,
          weight="600", ls=1.5)
    s.txt(136, 172, "400 V", ACC_S, 2.6, anchor="end", ls=.8)
    s.txt(136, 177, "NOT A DOSIMETER", "#8e988f", 2.2, anchor="end", ls=.6)
    s.txt(136, 182, "SER 001 / 010", "#5b655d", 2.1, anchor="end", ls=.6)

    reflection(s, p, SH, 26)
    return s.render(pad=13, aspect_pad_y=30)


# ---------------------------------------------------------------- hero swap-in
def hero_with_tubes(which):
    """Axonometric hero using the shared tube face on each tube's front plane."""
    import render as R
    if which == "t":
        sc = Scene(yaw=29, pitch=10, scale=2.75)
        base = R.terminal_hero
    return None


def main():
    files = {
        "v-terminal-front.svg": terminal_front(),
        "v-terminal-rear.svg": terminal_rear(),
        "v-terminal-macro.svg": terminal_macro(),
        "v-mimi-front.svg": mimi_front(),
        "v-quadrant-front.svg": quadrant_front(),
        "v-scaler-front.svg": scaler_front(),
    }
    for n, s in files.items():
        open(os.path.join(OUT, n), "w").write(s)
        print(n, len(s))


if __name__ == "__main__":
    main()
