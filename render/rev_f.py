#!/usr/bin/env python3
"""TERMINAL-06 Rev F — the complete drawing set.

EVERY dimension traces to a source, and the source is named in DIMS below.
Nothing in this file is a remembered number.

The three corrections Rev F is built on:
  1. ИН-12А is 19.47 x 28.86 x 25.50 with 12 pins out the REAR      (IN12.FCStd)
  2. ИН-15 is identical in form to ИН-12                            (stated 05.09.26)
  3. ИН-17 is an END-VIEW, WIRE-ENDED tube with a round Ø20 stem flattened
     to a 14-wide face: 14 x 20 x 22, digit 9 x 5.5   (factory outline drawing)

(3) is the correction that finally closed the row. The ИН-17 face is narrow —
14, not the 17.58 that a mid-body caliper reading suggested — but its STEM is
the full Ø20, so the seconds pair is spaced off the stems and not the faces.
Face 14, stem 20, pair gap 6.5 -> 204.3 overall.

Architecture: two cheeks, five boards, no moulded body. The HV compartment
behind the tube board is closed on every face — see hv().

Run: python3 rev_f.py
"""
import math, os

import tubes as T
from render import Scene, raked, proj, mix, disc, STROKE, CASE_T, ACC_T, GLOW_T
from render3 import frag_on_face, night_defs, night

OUT = os.path.dirname(os.path.abspath(__file__))
MONO = "IBM Plex Mono, monospace"
COND = "IBM Plex Sans Condensed, Arial Narrow, sans-serif"
WARM, DEEP, HOT = GLOW_T, "#FF5A08", "#FFE0BC"
ACC = ACC_T
PCB, PCB_E, COP = "#141A1E", "#39474E", "#B08A4A"
DIMC, INK, MUTE = "#8FA4B2", "#E4E1DA", "#6B737B"
CASE = "#252A30"

# ======================================================== dimensions + source
DIMS = {
    # ИН-12А / ИН-15 — 3d/IN12.FCStd spreadsheet, read 05.09.26
    "EW": (19.47, "IN12.FCStd envW"),
    "EH": (28.86, "IN12.FCStd envH"),
    "ED": (25.50, "IN12.FCStd envD"),
    "PIN_D": (0.92, "IN12.FCStd pinD"),
    "PIN_L": (6.25, "IN12.FCStd pinFreeL"),
    "PIN_FIELD_W": (12.40, "IN12.FCStd ClosestPinTotal"),
    "PIN_FIELD_H": (17.00, "IN12.FCStd FarthestPinTotal"),
    "DIGIT_12": (18.63, "caliper 27.08, reading 4"),
    # ИН-17 — from the factory outline drawing, 09.09.26. NOT a flat tube.
    # A round Ø20 stem flattened toward the display end: the face is a narrow
    # lens, the base is full Ø20. End-view, wire-ended, 35 mm free leads.
    # The 17.5 caliper reading was taken mid-body, part way down the flatten —
    # it is neither the face nor the base, which is why it fitted nothing.
    "SW": (14.00, "outline drawing · soviet-tubes 22×20×14 · swissnixie ≈15×20"),
    "SH": (20.00, "outline drawing Ø20 · caliper 19.30/19.20 across the stem"),
    "SD": (22.00, "outline drawing, glass only — leads are a further 35"),
    "S_BASE": (20.00, "outline drawing Ø20 — the stem is round"),
    "S_LEAD": (35.00, "outline drawing, free lead length"),
    "DIGIT_17": (9.00, "rudatasheet.ru высота цифр 9 мм"),
    "DIGIT_17_W": (5.50, "soviet-tubes digit 9 × 5.5 (H, W)"),
    # build
    "BT": (1.60, "assumed board stock"),
}
EW, EH, ED = DIMS["EW"][0], DIMS["EH"][0], DIMS["ED"][0]
SW, SH, SD = DIMS["SW"][0], DIMS["SH"][0], DIMS["SD"][0]
S_BASE, S_LEAD = DIMS["S_BASE"][0], DIMS["S_LEAD"][0]
DIGIT_17_W = DIMS["DIGIT_17_W"][0]
BT = DIMS["BT"][0]
DIGIT_12, DIGIT_17 = DIMS["DIGIT_12"][0], DIMS["DIGIT_17"][0]

# ======================================================== the row, computed
MARGIN = 8.0
PAIR_GAP, COLON_GAP, SEC_GAP, ANNEX_GAP = 3.0, 8.0, 8.0, 12.0
# The ИН-17 stems are Ø20 but the faces are 14 wide, so a face gap of 3 would
# put the two stems 17 apart and they would touch. The seconds pair is spaced
# off the STEMS, not the faces: 20 + 0.5 clearance = 20.5 centres = 6.5 faces.
SEC_PAIR_GAP = round(S_BASE + 0.5 - SW, 2)
_W = [EW, EW, EW, EW, SW, SW, EW, EW]
_G = [PAIR_GAP, COLON_GAP, PAIR_GAP, SEC_GAP, SEC_PAIR_GAP, ANNEX_GAP, PAIR_GAP]
_GL = ["2", "3", "1", "9", "0", "4", "A", "Р"]
_KIND = ["12", "12", "12", "12", "17", "17", "15", "15"]

CENTRES, _x = [], MARGIN
for _i, _w in enumerate(_W):
    if _i:
        _x += _G[_i - 1]
    CENTRES.append(_x + _w / 2.0)
    _x += _w
FACE_W = round(_x + MARGIN, 1)                       # 204.3
COLON_X = (CENTRES[1] + CENTRES[2]) / 2.0

# ======================================================== the object
CH_T, CH_D, CH_H = 6.0, 44.0, 62.0
TZ = 2.0                                              # every glass face
TY_12 = 30.0                                          # ИН-12 bottom
DIGIT_CY = TY_12 + EH / 2.0                           # 44.43 — the digit line
TY_17 = DIGIT_CY - SH / 2.0                           # ИН-17 centred on it
BZ = TZ + ED                                          # tube board front, 27.5
FASCIA_H = TY_12                                      # fascia meets the tubes
REAR_Z = CH_D - BT

# cheek profile (z, y). The long diagonal is also the line of the rear panel.
CHEEK = [(0, 4), (4, 0), (40, 0), (44, 4), (44, 16),
         (BZ, CH_H), (10, CH_H), (0, 52)]

SCREENS = ["RUN", "TIME", "DISP", "AMB", "INFO", "DATE"]
STUDIO = {"top": 1.06, "front": .82, "right": .60, "left": .46,
          "back": .40, "bottom": .30}


def tube_at(i):
    """(centre_x, w, h, d, ybot, digit_frac, glyph) for tube i."""
    k = _KIND[i]
    if k == "17":
        return (CENTRES[i], SW, SH, SD, TY_17, DIGIT_17 / SH, _GL[i])
    return (CENTRES[i], EW, EH, ED, TY_12, DIGIT_12 / EH, _GL[i])


# ============================================================ svg utilities
def txt(x, y, s, size=3.0, fill=DIMC, anchor="middle", family=MONO,
        weight="400", ls=".4", op=1.0):
    return (f'<text x="{x:.2f}" y="{y:.2f}" font-family="{family}" '
            f'font-size="{size:.2f}" fill="{fill}" text-anchor="{anchor}" '
            f'font-weight="{weight}" letter-spacing="{ls}" opacity="{op}">{s}</text>')


def dimh(o, x1, x2, y, lab, col=DIMC, size=3.0, below=True):
    o.append(f'<line x1="{x1:.2f}" y1="{y:.2f}" x2="{x2:.2f}" y2="{y:.2f}" '
             f'stroke="{col}" stroke-width=".4"/>')
    for x in (x1, x2):
        o.append(f'<line x1="{x:.2f}" y1="{y-2:.2f}" x2="{x:.2f}" y2="{y+2:.2f}" '
                 f'stroke="{col}" stroke-width=".4"/>')
    o.append(txt((x1 + x2) / 2, y + (5.0 if below else -2.4), lab, size, col))


def dimv(o, y1, y2, x, lab, col=DIMC, size=3.0, right=True):
    o.append(f'<line x1="{x:.2f}" y1="{y1:.2f}" x2="{x:.2f}" y2="{y2:.2f}" '
             f'stroke="{col}" stroke-width=".4"/>')
    for y in (y1, y2):
        o.append(f'<line x1="{x-2:.2f}" y1="{y:.2f}" x2="{x+2:.2f}" y2="{y:.2f}" '
                 f'stroke="{col}" stroke-width=".4"/>')
    o.append(txt(x + (2.8 if right else -2.8), (y1 + y2) / 2 + 1.1, lab, size, col,
                 anchor="start" if right else "end"))


def sheet(w, h, title, sub, body, pid, defs_extra=""):
    o = [f'<rect x="0" y="0" width="{w}" height="{h}" fill="#0B0D10"/>']
    o.append(txt(w / 2, 13, title, 6.6, INK, family=COND, weight="700", ls=".5"))
    if sub:
        o.append(txt(w / 2, 19.4, sub, 3.0, MUTE))
    o.append(body)
    d = '<defs>' + T.tube_defs(pid, warm=WARM, deep=DEEP) + defs_extra + '</defs>'
    return ('<svg preserveAspectRatio="xMidYMid meet" viewBox="0 0 %.1f %.1f" '
            'xmlns="http://www.w3.org/2000/svg" role="img">%s\n%s</svg>'
            % (w, h, d, "\n".join(o)))


# ============================================================ 3d primitives
def plate_x(sc, x0, y0, z0, w, h, d, base, n=None):
    """Thin plate as x-slices — one polygon sorts at one depth and would land
    wholly in front of or behind the tube row."""
    n = n or max(2, int(w / 6.0))
    step = w / n
    for i in range(n):
        seg = raked(x0 + i * step, y0, z0, step * 1.08, h, d)
        for name, pts in seg.items():
            if name in ("bottom", "left", "right"):
                continue
            sc.poly(pts, mix(base, STUDIO[name]), None)


def prism_x(sc, prof, x0, t, base, sw=.5, stroke=STROKE):
    """Extrude a (z, y) profile along x. raked() only makes boxes."""
    outer = [(x0, y, z) for (z, y) in prof]
    inner = [(x0 + t, y, z) for (z, y) in prof]
    n = len(prof)
    for i in range(n):
        j = (i + 1) % n
        sc.poly([outer[i], outer[j], inner[j], inner[i]],
                mix(base, STUDIO["right"]), stroke, sw * .8)
    sc.poly(inner, mix(base, STUDIO["left"]), stroke, sw)
    sc.poly(outer, mix(base, STUDIO["front"]), stroke, sw)


def sloped_panel(sc, x0, w, base, n=None):
    """The rear/top closure — one flat board lying on the cheek's diagonal."""
    z1, y1 = BZ, CH_H
    z2, y2 = 44.0, 16.0
    n = n or max(2, int(w / 6.0))
    step = w / n
    for i in range(n):
        xa = x0 + i * step
        xb = xa + step * 1.08
        sc.poly([(xa, y1, z1), (xb, y1, z1), (xb, y2, z2), (xa, y2, z2)],
                mix(base, STUDIO["top"]), None)


def row3d(sc, pid, dim=1.0):
    for i in range(8):
        cx, w, h, d, yb, df, ch = tube_at(i)
        x0 = cx - w / 2.0
        can = raked(x0, yb, TZ, w, h, d)
        for name, pts in can.items():
            if name in ("bottom", "front"):
                continue
            sc.poly(pts, mix("#39434B", STUDIO[name]), STROKE, .45)
        frag = T.tube_face(pid, w, h, ch, ghosts=ch.isdigit(),
                           glyphset="0123456789" if ch.isdigit() else ch,
                           warm=WARM, hot=HOT, deep=DEEP, dim=dim,
                           digit_frac=df, ghost_op=.07, spec_op=.7,
                           mesh_op=.34, socket=False)
        frag_on_face(sc, (x0, yb + h, TZ - .3), frag, depth_bias=-9)
    for yy in (DIGIT_CY - 6.5, DIGIT_CY + 0.5):
        m, dz = sc.face_matrix((COLON_X, yy + 3.4, TZ - .6), (1, 0, 0), (0, -1, 0))
        sc.items.append((dz - 9, '<g transform="%s">%s</g>'
                         % (m, T.neon_dot(pid, 2.0, 1.7, 1.7, True, DEEP, WARM))))


def fascia3d(sc, warmth=0.0):
    def fpt(xx, yy):
        return (xx, yy, TZ - .35)
    kx, ky = 30.0, 15.0
    sc.begin_group()
    for i in range(6):
        a = math.radians(-80 + i * 32)
        p1 = fpt(kx + math.sin(a) * 7.4, ky + math.cos(a) * 7.4)
        p2 = fpt(kx + math.sin(a) * 9.6, ky + math.cos(a) * 9.6)
        sc.poly([p1, p2, (p2[0] + .8, p2[1], p2[2]), (p1[0] + .8, p1[1], p1[2])],
                ACC if i == 0 else COP, bias=-7)
    disc(sc, fpt, kx, ky, 5.0, "#2A3138", "#6E7883", .55)
    sc.poly([fpt(kx - .55, ky + 1.2), fpt(kx + .55, ky + 1.2),
             fpt(kx + .55, ky + 4.2), fpt(kx - .55, ky + 4.2)], ACC, bias=-9)
    for lx in (112, 127):
        sc.poly([fpt(lx - 1.7, ky - 5.0), fpt(lx + 1.7, ky - 5.0),
                 fpt(lx + 1.7, ky + 5.0), fpt(lx - 1.7, ky + 5.0)],
                "#2A3138", "#6E7883", .5, bias=-7)
    for bx in (158, 173):
        disc(sc, fpt, bx, ky, 3.2, "#2A3138", "#6E7883", .5)
    for i in range(4):
        xx = 84 + i * 22
        sc.poly([fpt(xx, 25.0), fpt(xx + 11, 25.0), fpt(xx + 11, 25.7), fpt(xx, 25.7)],
                COP, extra=' opacity=".45"', bias=-6)
    sc.text_on_face((FACE_W - 12, 4.2, TZ - .5), (1, 0, 0), (0, 1, 0),
                    "TERMINAL·06", 5.0, COP, anchor="end", weight="600",
                    family=MONO, depth_bias=-6)
    sc.end_group(-1e6)


def cap(sc, pt, s, dx=8.0, dy=0.0, size=5.0, col="#8B939C", anchor="start"):
    x, y, _ = sc.p2(pt)
    tx, ty = x + dx, y + dy
    run = len(s) * size * 0.56
    sc.pts.append((tx + (run if anchor == "start" else -run), ty))
    sc.pts.append((tx, ty - size))
    sc.items.append((-1e7, '<path d="M%.2f %.2f L%.2f %.2f L%.2f %.2f" fill="none" '
                     'stroke="%s" stroke-width=".7" opacity=".55"/>'
                     % (x, y, tx - 3.4, ty - size * .34, tx - 1.2, ty - size * .34,
                        col)))
    sc.items.append((-1e7, '<circle cx="%.2f" cy="%.2f" r="1.3" fill="%s" '
                     'opacity=".8"/>' % (x, y, col)))
    sc.items.append((-1e7, '<text x="%.2f" y="%.2f" font-family="%s" font-size="%.2f" '
                     'fill="%s" text-anchor="%s" letter-spacing=".4">%s</text>'
                     % (tx, ty, MONO, size, col, anchor, s)))


def assemble(sc, base_case=CASE, base_pcb=PCB, rear="#101519"):
    for cx in (0.0, FACE_W - CH_T):
        prism_x(sc, CHEEK, cx, CH_T, base_case)
    W = FACE_W - 2 * CH_T
    sloped_panel(sc, CH_T, W, rear)                                  # rear/top
    plate_x(sc, CH_T, 4.0, 44.0 - BT, W, 12.0, BT, rear)             # rear strip
    plate_x(sc, CH_T, 0.0, 4.0, W, BT, 38.0, rear)                   # bottom
    plate_x(sc, CH_T, 4.0, 8.0, W, BT, 32.0, base_pcb)               # main board
    plate_x(sc, CH_T, 24.0, BZ, W, CH_H - 24.0, BT, base_pcb)        # tube board
    plate_x(sc, CH_T, 0.0, TZ, W, FASCIA_H, BT, base_pcb)            # fascia


# ==================================================================== HERO
def hero():
    pid = "fh"
    sc = Scene(yaw=31, pitch=10, scale=3.2)
    assemble(sc)
    fascia3d(sc)
    row3d(sc, pid)
    cap(sc, (FACE_W, CH_H, BZ), "tube board", col="#9FB0A6")
    cap(sc, (FACE_W, FASCIA_H, TZ), "fascia — black mask, legend in silkscreen",
        dy=9, col=COP)
    cap(sc, (FACE_W, 0, CH_D), "cheek 6 — the only part that is not a board", dy=18)
    return sc.render(defs=night_defs(pid, WARM, DEEP), pad=38)


def night_hero():
    pid = "fn"
    sc = Scene(yaw=34, pitch=7, scale=3.2)
    n = lambda c, k=1.0, w=.04: night(c, k, WARM, w)
    for cx in (0.0, FACE_W - CH_T):
        prism_x(sc, CHEEK, cx, CH_T, n(CASE, 1.1, .05), stroke=n(STROKE, 1.8))
    W = FACE_W - 2 * CH_T
    sloped_panel(sc, CH_T, W, n("#101519", .9))
    plate_x(sc, CH_T, 4.0, 44.0 - BT, W, 12.0, BT, n("#101519", .8))
    plate_x(sc, CH_T, 0.0, 4.0, W, BT, 38.0, n("#101519", .8))
    plate_x(sc, CH_T, 4.0, 8.0, W, BT, 32.0, n(PCB, 1.0))
    plate_x(sc, CH_T, 24.0, BZ, W, CH_H - 24.0, BT, n(PCB, 1.3, .09))
    plate_x(sc, CH_T, 0.0, TZ, W, FASCIA_H, BT, n(PCB, 1.2, .07))

    def fpt(xx, yy):
        return (xx, yy, TZ - .35)
    sc.begin_group()
    kx, ky = 30.0, 15.0
    for i in range(6):
        a = math.radians(-80 + i * 32)
        p1 = fpt(kx + math.sin(a) * 7.4, ky + math.cos(a) * 7.4)
        p2 = fpt(kx + math.sin(a) * 9.6, ky + math.cos(a) * 9.6)
        sc.poly([p1, p2, (p2[0] + .8, p2[1], p2[2]), (p1[0] + .8, p1[1], p1[2])],
                ACC if i == 0 else "#3A3226", bias=-7)
    disc(sc, fpt, kx, ky, 5.0, "#1A1F24", "#39424A", .5)
    sc.poly([fpt(kx - .55, ky + 1.2), fpt(kx + .55, ky + 1.2),
             fpt(kx + .55, ky + 4.2), fpt(kx - .55, ky + 4.2)], ACC, bias=-9)
    sc.text_on_face((FACE_W - 12, 4.2, TZ - .5), (1, 0, 0), (0, 1, 0),
                    "TERMINAL·06", 5.0, "#4A4030", anchor="end", weight="600",
                    family=MONO, depth_bias=-6)
    sc.end_group(-1e6)
    row3d(sc, pid)
    # light on the table
    npts = 26
    pts = [(FACE_W / 2 + math.cos(2 * math.pi * i / npts) * FACE_W * .62, 0.0,
            CH_D / 2 + math.sin(2 * math.pi * i / npts) * CH_D * 1.5) for i in range(npts)]
    sc.poly(pts, "url(#%s-pool)" % pid, extra=' filter="url(#%s-blur8)"' % pid,
            bias=6200)
    return sc.render(defs=night_defs(pid, WARM, DEEP), pad=40)


# ============================================================ EXPLODED
def exploded():
    """Exploded SECTION, not a three-quarter.

    Every element here is a thin plane stacked front-to-back. In an
    axonometric they pile up behind one another and read as one dark mass —
    tried twice, failed twice. On a section they read at a glance.
    """
    pid = "fx"
    W, H = 320.0, 168.0
    GY = 118.0
    o = []

    def Y(y): return GY - y

    def board(sx, y0, h, col=PCB, w=BT):
        o.append(f'<rect x="{sx-w/2:.2f}" y="{Y(y0+h):.2f}" width="{w}" '
                 f'height="{h:.2f}" fill="{col}" stroke="{PCB_E}" stroke-width=".4"/>')

    def label(sx, name, z, col):
        o.append(txt(sx, Y(-10), name, 3.2, col, weight="600"))
        o.append(txt(sx, Y(-15), z, 2.7, "#5A6169"))

    # 1 — fascia
    sx = 34.0
    board(sx, 0, FASCIA_H)
    o.append(f'<circle cx="{sx:.1f}" cy="{Y(15):.1f}" r="5.0" fill="#2A3138" '
             f'stroke="#6E7883" stroke-width=".5"/>')
    label(sx, "FASCIA", "z 2.0 · 30 tall", COP)

    # 2 — tubes
    sx = 92.0
    o.append(f'<rect x="{sx-ED/2:.2f}" y="{Y(TY_12+EH):.2f}" width="{ED}" '
             f'height="{EH}" rx="1.2" fill="#1B2026" stroke="#5C6771" stroke-width=".55"/>')
    o.append(f'<rect x="{sx-ED/2:.2f}" y="{Y(TY_12+EH):.2f}" width="2.2" height="{EH}" '
             f'fill="{WARM}" opacity=".34"/>')
    o.append(f'<rect x="{sx-ED/2:.2f}" y="{Y(TY_17+SH):.2f}" width="{SD}" height="{SH}" '
             f'rx="1" fill="none" stroke="#5C6771" stroke-width=".45" '
             f'stroke-dasharray="2.2 1.6"/>')
    for i in range(5):
        yy = Y(DIGIT_CY) - 8 + i * 4
        o.append(f'<line x1="{sx+ED/2:.2f}" y1="{yy:.2f}" x2="{sx+ED/2+4.65:.2f}" '
                 f'y2="{yy:.2f}" stroke="#9AA6B0" stroke-width=".45"/>')
    label(sx, "8 TUBES", "z 2.0 → 27.5 · direct-solder", "#C8B49A")

    # 3 — tube board
    sx = 150.0
    board(sx, 24, CH_H - 24)
    label(sx, "TUBE BOARD", "z 27.5", "#9FB0A6")

    # 4 — main board
    sx = 205.0
    o.append(f'<rect x="{sx-16:.1f}" y="{Y(6):.1f}" width="32" height="{BT}" '
             f'fill="{PCB}" stroke="{PCB_E}" stroke-width=".4"/>')
    label(sx, "MAIN BOARD", "y 4 · z 8 → 40", "#8FBFA4")

    # 5 — the three closures, shown assembled
    sx = 272.0
    o.append(f'<line x1="{sx-8:.2f}" y1="{Y(CH_H):.2f}" x2="{sx+8:.2f}" '
             f'y2="{Y(16):.2f}" stroke="#101519" stroke-width="2.2" stroke-linecap="round"/>')
    o.append(f'<line x1="{sx-8:.2f}" y1="{Y(CH_H):.2f}" x2="{sx+8:.2f}" '
             f'y2="{Y(16):.2f}" stroke="{ACC}" stroke-width=".5" opacity=".9"/>')
    for i in range(5):
        t = .18 + i * .16
        o.append(f'<line x1="{sx-8+16*t-1.4:.2f}" y1="{Y(CH_H-(CH_H-16)*t)+1.2:.2f}" '
                 f'x2="{sx-8+16*t+1.4:.2f}" y2="{Y(CH_H-(CH_H-16)*t)-1.2:.2f}" '
                 f'stroke="#0B0D10" stroke-width="1.1"/>')
    board(sx + 8, 4, 12, "#101519")
    o.append(f'<rect x="{sx-14:.1f}" y="{Y(BT):.1f}" width="26" height="{BT}" '
             f'fill="#101519" stroke="{PCB_E}" stroke-width=".4"/>')
    label(sx, "CLOSURES", "sloped · strip · bottom", ACC)
    o.append(txt(sx, Y(-20), "vented on the slope", 2.6, MUTE))

    o.append(f'<line x1="56" y1="{Y(DIGIT_CY):.2f}" x2="{W-16:.1f}" '
             f'y2="{Y(DIGIT_CY):.2f}" stroke="#3C444C" stroke-width=".4" '
             f'stroke-dasharray="4 4"/>')
    o.append(txt(20, Y(DIGIT_CY) - 2.4, "digit line 44.43", 2.7, "#5A6169",
                 anchor="start"))
    o.append(f'<line x1="16" y1="{GY:.2f}" x2="{W-16:.1f}" y2="{GY:.2f}" '
             f'stroke="#3A4149" stroke-width=".5"/>')
    o.append(txt(W / 2, H - 9, "two cheeks and six boards — nothing here is moulded "
                 "except the cheeks", 3.0, MUTE))
    return sheet(W, H, "THE STACK — EXPLODED SECTION",
                 "front to back, at true height · true z under each name",
                 "\n".join(o), pid)


# ============================================================== ELEVATIONS
def front(lit=True):
    pid = "ff"
    pad = 20.0
    W, H = FACE_W + 2 * pad, CH_H + 74
    GY = H - 40.0
    o = []

    def Y(y):
        return GY - y

    for cx in (0.0, FACE_W - CH_T):
        o.append(f'<rect x="{pad+cx:.2f}" y="{Y(CH_H):.2f}" width="{CH_T}" '
                 f'height="{CH_H}" rx="1.4" fill="{CASE}" stroke="#4A5058" '
                 f'stroke-width=".6"/>')
    IW = FACE_W - 2 * CH_T
    # tube board edge, above the row
    o.append(f'<rect x="{pad+CH_T:.2f}" y="{Y(CH_H):.2f}" width="{IW}" '
             f'height="{CH_H-TY_12-EH:.2f}" fill="{PCB}" stroke="{PCB_E}" stroke-width=".4"/>')
    # fascia
    o.append(f'<rect x="{pad+CH_T:.2f}" y="{Y(FASCIA_H):.2f}" width="{IW}" '
             f'height="{FASCIA_H}" fill="{PCB}" stroke="{PCB_E}" stroke-width=".5"/>')
    for i in range(4):
        xx = pad + CH_T + 78 + i * 22
        o.append(f'<path d="M{xx:.1f} {Y(25):.1f} h11 v-2.4 h6" fill="none" '
                 f'stroke="{COP}" stroke-width=".5" opacity=".45"/>')
    # tubes
    for i in range(8):
        cx, w, h, d, yb, df, ch = tube_at(i)
        frag = T.tube_face(pid, w, h, ch, ghosts=ch.isdigit(),
                           glyphset="0123456789" if ch.isdigit() else ch,
                           warm=WARM, hot=HOT, deep=DEEP, dim=1.0 if lit else 0.0,
                           digit_frac=df, ghost_op=.08, spec_op=.75,
                           mesh_op=.36, socket=False)
        o.append(f'<g transform="translate({pad+cx-w/2:.2f} {Y(yb+h):.2f})">{frag}</g>')
    for yy in (DIGIT_CY - 5.0, DIGIT_CY + 2.0):
        o.append(f'<circle cx="{pad+COLON_X:.2f}" cy="{Y(yy):.2f}" r="1.8" fill="{WARM}" '
                 f'opacity=".9"/>')
        o.append(f'<circle cx="{pad+COLON_X:.2f}" cy="{Y(yy):.2f}" r="3.4" fill="{DEEP}" '
                 f'opacity=".3" filter="url(#{pid}-midglow)"/>')
    # controls
    kx, ky = pad + 30.0, Y(15.0)
    for i in range(6):
        a = math.radians(-80 + i * 32)
        s_, c_ = math.sin(a), -math.cos(a)
        o.append(f'<line x1="{kx+s_*7.4:.2f}" y1="{ky+c_*7.4:.2f}" '
                 f'x2="{kx+s_*9.6:.2f}" y2="{ky+c_*9.6:.2f}" '
                 f'stroke="{ACC if i==0 else COP}" stroke-width=".9" stroke-linecap="round"/>')
        lx, ly = kx + s_ * 12.4, ky + c_ * 12.4
        anc = "middle" if abs(s_) < .12 else ("start" if s_ > 0 else "end")
        o.append(f'<text x="{lx:.1f}" y="{ly+.9:.1f}" font-family="{MONO}" font-size="2.4" '
                 f'fill="{INK if i==0 else MUTE}" text-anchor="{anc}">{SCREENS[i]}</text>')
    o.append(f'<circle cx="{kx:.1f}" cy="{ky:.1f}" r="5.0" fill="#343A42" '
             f'stroke="#79818B" stroke-width=".6"/>')
    a0 = math.radians(-80)
    o.append(f'<line x1="{kx+math.sin(a0)*1.6:.2f}" y1="{ky-math.cos(a0)*1.6:.2f}" '
             f'x2="{kx+math.sin(a0)*4.2:.2f}" y2="{ky-math.cos(a0)*4.2:.2f}" '
             f'stroke="{ACC}" stroke-width="1.2" stroke-linecap="round"/>')
    for lx, nm in ((112, "SET"), (127, "ADJ")):
        o.append(f'<rect x="{pad+lx-1.7:.1f}" y="{Y(20.0):.1f}" width="3.4" height="10" '
                 f'rx="1.1" fill="#343A42" stroke="#79818B" stroke-width=".45"/>')
        o.append(f'<text x="{pad+lx:.1f}" y="{Y(6.4):.1f}" font-family="{MONO}" '
                 f'font-size="2.4" fill="{MUTE}" text-anchor="middle">{nm}</text>')
    for bx, nm in ((158, "▲"), (173, "▼")):
        o.append(f'<circle cx="{pad+bx:.1f}" cy="{ky:.1f}" r="3.2" fill="#343A42" '
                 f'stroke="#79818B" stroke-width=".45"/>')
        o.append(f'<text x="{pad+bx:.1f}" y="{ky+1.1:.1f}" font-family="{COND}" '
                 f'font-size="3.0" fill="#9AA1A8" text-anchor="middle">{nm}</text>')
    o.append(txt(pad + FACE_W - 12, Y(4.2), "TERMINAL·06", 5.0, COP, anchor="end",
                 weight="600"))

    dimh(o, pad, pad + FACE_W, GY + 10, f"{FACE_W:g}")
    dimv(o, Y(CH_H), Y(0), pad - 8, f"{CH_H:g}", right=False)
    dimh(o, pad + CENTRES[0], pad + CENTRES[1], Y(CH_H) - 8,
         f"{CENTRES[1]-CENTRES[0]:.1f}", size=2.7, below=False)
    dimh(o, pad + CENTRES[5], pad + CENTRES[6], Y(CH_H) - 8,
         f"{CENTRES[6]-CENTRES[5]:.1f} annex", size=2.7, below=False)
    o.append(txt(W / 2, GY + 20, "ИН-15 is ИН-12 · ИН-17 face is 14 × 20 with a 9 mm digit — half the glass, on the same digit line at 44.43", 2.9, MUTE))
    return sheet(W, H, "FRONT ELEVATION — 1:1",
                 f"{FACE_W:g} × {CH_H:g} × {CH_D:g} · every glass face coplanar at z = {TZ:g}",
                 "\n".join(o), pid)


def profile():
    pid = "fp"
    pad, GY = 44.0, 96.0
    W, H = 208.0, 142.0
    o = []

    def X(z): return pad + z
    def Y(y): return GY - y

    pts = " ".join(f"{X(z):.2f},{Y(y):.2f}" for (z, y) in CHEEK)
    o.append(f'<polygon points="{pts}" fill="{CASE}" stroke="#5C6771" stroke-width=".7"/>')
    # boards
    def bd(z, y0, h, col=PCB):
        o.append(f'<rect x="{X(z):.2f}" y="{Y(y0+h):.2f}" width="{BT}" height="{h:.2f}" '
                 f'fill="{col}" stroke="{PCB_E}" stroke-width=".35"/>')
    bd(TZ, 0, FASCIA_H)
    bd(BZ, 24, CH_H - 24)
    o.append(f'<rect x="{X(8):.2f}" y="{Y(4+BT):.2f}" width="32" height="{BT}" '
             f'fill="{PCB}" stroke="{PCB_E}" stroke-width=".35"/>')
    bd(44 - BT, 4, 12, "#101519")
    o.append(f'<rect x="{X(4):.2f}" y="{Y(BT):.2f}" width="38" height="{BT}" '
             f'fill="#101519" stroke="{PCB_E}" stroke-width=".35"/>')
    o.append(f'<line x1="{X(BZ):.2f}" y1="{Y(CH_H):.2f}" x2="{X(44):.2f}" '
             f'y2="{Y(16):.2f}" stroke="#101519" stroke-width="1.6" stroke-linecap="round"/>')
    o.append(f'<line x1="{X(BZ):.2f}" y1="{Y(CH_H):.2f}" x2="{X(44):.2f}" '
             f'y2="{Y(16):.2f}" stroke="{PCB_E}" stroke-width=".35"/>')
    # tubes: ИН-12 solid, ИН-17 dashed behind it
    o.append(f'<rect x="{X(TZ):.2f}" y="{Y(TY_12+EH):.2f}" width="{ED}" height="{EH}" '
             f'rx="1.2" fill="#1B2026" stroke="#5C6771" stroke-width=".55"/>')
    o.append(f'<rect x="{X(TZ):.2f}" y="{Y(TY_12+EH):.2f}" width="2.2" height="{EH}" '
             f'fill="{WARM}" opacity=".34"/>')
    o.append(f'<rect x="{X(TZ):.2f}" y="{Y(TY_17+SH):.2f}" width="{SD}" height="{SH}" '
             f'rx="4" fill="none" stroke="#5C6771" stroke-width=".5" '
             f'stroke-dasharray="2.4 1.8"/>')
    for i in range(5):
        yy = Y(DIGIT_CY) - 8 + i * 4
        o.append(f'<line x1="{X(BZ):.2f}" y1="{yy:.2f}" x2="{X(BZ)+4.65:.2f}" '
                 f'y2="{yy:.2f}" stroke="#9AA6B0" stroke-width=".45"/>')

    for (zz, yy, s, col) in ((TZ, 24, "fascia board", DIMC),
                             (BZ, 52, "tube board", DIMC),
                             (34, 40, "rear / top closure — HV barrier", ACC),
                             (8, 8, "main board", DIMC),
                             (24, -6, "bottom closure — HV barrier", ACC)):
        o.append(f'<line x1="{X(zz)+2:.2f}" y1="{Y(yy):.2f}" x2="{X(56):.2f}" '
                 f'y2="{Y(yy):.2f}" stroke="#3C444C" stroke-width=".35"/>')
        o.append(txt(X(58), Y(yy) + 1.1, s, 3.0, col, anchor="start"))
    o.append(f'<line x1="{X(24)+2:.2f}" y1="{Y(BT):.2f}" x2="{X(24)+2:.2f}" '
             f'y2="{Y(-6):.2f}" stroke="#3C444C" stroke-width=".35"/>')

    dimh(o, X(0), X(CH_D), GY + 18, f"{CH_D:g} deep")
    dimv(o, Y(CH_H), Y(0), X(-9), f"{CH_H:g}", right=False)
    dimv(o, Y(TY_12 + EH), Y(TY_12), X(-22), f"{EH}", right=False)
    o.append(txt(X(45.6), Y(12.6), "16", 2.9, MUTE, anchor="start"))
    o.append(f'<line x1="{pad-24:.1f}" y1="{GY:.2f}" x2="{W-12:.1f}" y2="{GY:.2f}" '
             f'stroke="#3A4149" stroke-width=".5"/>')
    o.append(txt(W / 2, H - 14, "ИН-12 solid · ИН-17 dashed behind it — 22 deep, 20 tall, so it clears the same board", 2.9, MUTE))
    o.append(txt(W / 2, H - 8, "the cheek diagonal IS the rear panel — no separate back, no moulding", 2.9, MUTE))
    return sheet(W, H, "RIGHT PROFILE — 1:1",
                 "the cheek, and everything it carries", "\n".join(o), pid)


def plan():
    pid = "fl"
    pad = 22.0
    W, H = FACE_W + 2 * pad, CH_D + 106
    OY = 44.0
    o = []

    def X(x): return pad + x
    def Z(z): return OY + z

    o.append(f'<rect x="{X(0):.2f}" y="{Z(0):.2f}" width="{FACE_W}" height="{CH_D}" '
             f'fill="#141A1F" stroke="#3A4149" stroke-width=".7"/>')
    for cx in (0.0, FACE_W - CH_T):
        o.append(f'<rect x="{X(cx):.2f}" y="{Z(0):.2f}" width="{CH_T}" height="{CH_D}" '
                 f'fill="{CASE}" stroke="#4A5058" stroke-width=".5"/>')
    o.append(f'<rect x="{X(CH_T):.2f}" y="{Z(TZ):.2f}" width="{FACE_W-2*CH_T}" '
             f'height="{BT}" fill="{PCB}" stroke="{PCB_E}" stroke-width=".4"/>')
    o.append(f'<rect x="{X(CH_T):.2f}" y="{Z(BZ):.2f}" width="{FACE_W-2*CH_T}" '
             f'height="{BT}" fill="{PCB}" stroke="{PCB_E}" stroke-width=".4"/>')
    o.append(f'<rect x="{X(CH_T):.2f}" y="{Z(44-BT):.2f}" width="{FACE_W-2*CH_T}" '
             f'height="{BT}" fill="#101519" stroke="{PCB_E}" stroke-width=".4"/>')
    for i in range(8):
        cx, w, h, d, yb, df, ch = tube_at(i)
        if _KIND[i] == "17":
            # round stem, flattened toward the face: 14 at z=2, Ø20 at the base
            hw, hb = w / 2.0, S_BASE / 2.0
            zf, zk, zb = Z(TZ), Z(TZ + 9), Z(TZ + d)
            o.append(f'<path d="M{X(cx-hw):.2f} {zf:.2f} '
                     f'C{X(cx-hw):.2f} {zk:.2f} {X(cx-hb):.2f} {zk:.2f} '
                     f'{X(cx-hb):.2f} {zb-3:.2f} L{X(cx-hb):.2f} {zb:.2f} '
                     f'L{X(cx+hb):.2f} {zb:.2f} L{X(cx+hb):.2f} {zb-3:.2f} '
                     f'C{X(cx+hb):.2f} {zk:.2f} {X(cx+hw):.2f} {zk:.2f} '
                     f'{X(cx+hw):.2f} {zf:.2f} Z" '
                     f'fill="#141C23" stroke="#8FA4B2" stroke-width=".45"/>')
            o.append(f'<line x1="{X(cx-hb):.2f}" y1="{zb:.2f}" x2="{X(cx+hb):.2f}" '
                     f'y2="{zb:.2f}" stroke="{COP}" stroke-width=".8" opacity=".7"/>')
        else:
            o.append(f'<rect x="{X(cx-w/2):.2f}" y="{Z(TZ):.2f}" width="{w}" height="{d}" '
                     f'rx=".8" fill="#141C23" stroke="#8FA4B2" stroke-width=".45"/>')
        o.append(f'<rect x="{X(cx-w/2)+2:.2f}" y="{Z(TZ)+2:.2f}" width="{w-4:.2f}" '
                 f'height="4.5" fill="{WARM}" opacity=".5" filter="url(#{pid}-midglow)"/>')
    o.append(f'<circle cx="{X(COLON_X):.2f}" cy="{Z(TZ+4):.2f}" r="1.6" fill="{WARM}" '
             f'opacity=".8"/>')

    dimh(o, X(0), X(FACE_W), Z(-16), f"{FACE_W:g}", below=False)
    dimh(o, X(CENTRES[3]), X(CENTRES[4]), Z(-6), f"{CENTRES[4]-CENTRES[3]:.1f}",
         size=2.6, below=False)
    dimh(o, X(CENTRES[5]), X(CENTRES[6]), Z(-6), f"{CENTRES[6]-CENTRES[5]:.1f}",
         size=2.6, below=False)
    dimv(o, Z(0), Z(CH_D), X(-10), f"{CH_D:g}", right=False)
    dimh(o, X(CENTRES[4]), X(CENTRES[5]), Z(CH_D) + 7,
         f"{CENTRES[5]-CENTRES[4]:.1f}", col=ACC, size=2.6)
    o.append(txt(X(FACE_W / 2), Z(CH_D) + 17,
                 "the ИН-17 stems are Ø20 though the faces are only 14 —", 2.9, ACC))
    o.append(txt(X(FACE_W / 2), Z(CH_D) + 22,
                 "the seconds pair is spaced off the STEMS (20 + 0.5), not the faces",
                 2.9, ACC))
    o.append(txt(X(FACE_W / 2), Z(CH_D) + 29,
                 "ИН-12 barrel 25.5 · ИН-17 glass 22 — faces coplanar, so the ИН-17 "
                 "leads reach 3.5 mm further to the same board", 2.9, MUTE))
    o.append(txt(X(FACE_W / 2), Z(CH_D) + 34,
                 "ИН-17 is wire-ended: 35 mm of flexible lead, trimmed and dressed "
                 "through a comb — not pins in a pattern", 2.9, MUTE))
    return sheet(W, H, "PLAN — 1:1", "row spacing and the three board planes",
                 "\n".join(o), pid)


# ================================================================= HV SHEET
def hv():
    pid = "fv"
    S = 1.45                       # the section is only 44 x 62 — draw it larger
    pad, GY = 20.0, 120.0
    W, H = 340.0, 136.0
    o = []

    def X(z): return pad + z * S

    def Y(y): return GY - y * S

    lp = " ".join(f"{X(z):.2f},{Y(y):.2f}" for (z, y) in
                  [(BZ, CH_H), (44, 16), (44, 4), (BZ, 4)])
    o.append(f'<polygon points="{lp}" fill="{ACC}" opacity=".14"/>')
    pts = " ".join(f"{X(z):.2f},{Y(y):.2f}" for (z, y) in CHEEK)
    o.append(f'<polygon points="{pts}" fill="none" stroke="#3C444C" stroke-width=".6"/>')
    o.append(f'<rect x="{X(TZ):.2f}" y="{Y(FASCIA_H):.2f}" width="{BT*S:.2f}" '
             f'height="{FASCIA_H*S:.2f}" fill="{PCB}" stroke="{PCB_E}" stroke-width=".35"/>')
    o.append(f'<rect x="{X(8):.2f}" y="{Y(4+BT):.2f}" width="{32*S:.2f}" '
             f'height="{BT*S:.2f}" fill="{PCB}" stroke="{PCB_E}" stroke-width=".35"/>')
    o.append(f'<rect x="{X(TZ):.2f}" y="{Y(TY_12+EH):.2f}" width="{ED*S:.2f}" '
             f'height="{EH*S:.2f}" rx="1.6" fill="#151A20" stroke="#4A5058" '
             f'stroke-width=".45"/>')

    def barrier(x1, y1, x2, y2):
        o.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
                 f'stroke="{ACC}" stroke-width="1.7" stroke-linecap="round"/>')
    barrier(X(BZ), Y(CH_H), X(44), Y(16))
    barrier(X(44), Y(16), X(44), Y(4))
    barrier(X(4), Y(0), X(42), Y(0))
    barrier(X(BZ), Y(CH_H), X(BZ), Y(24))
    o.append(txt(X(1), Y(CH_H) - 4.0, "live compartment: z 27.5 → 44, y 4 → 62",
                 2.8, MUTE, anchor="start"))

    for i in range(5):
        yy = Y(DIGIT_CY) - 11 + i * 5.5
        o.append(f'<line x1="{X(BZ):.2f}" y1="{yy:.2f}" x2="{X(BZ+4.65):.2f}" '
                 f'y2="{yy:.2f}" stroke="{ACC}" stroke-width=".6"/>')
    o.append(f'<circle cx="{X(BZ+2.3):.2f}" cy="{Y(DIGIT_CY):.2f}" r="13" fill="none" '
             f'stroke="{ACC}" stroke-width=".4" stroke-dasharray="2 2"/>')
    o.append(txt(X(35.5), Y(13.5), "LIVE", 4.6, ACC, weight="700"))
    o.append(txt(X(35.5), Y(8.4), "185 V", 3.0, ACC))
    o.append(f'<line x1="{X(BZ+2.3)+13:.2f}" y1="{Y(DIGIT_CY):.2f}" '
             f'x2="{X(46):.2f}" y2="{Y(DIGIT_CY):.2f}" stroke="{ACC}" stroke-width=".4"/>')
    o.append(txt(X(47), Y(DIGIT_CY) - 1.6, "pins protrude 4.65 mm", 3.0, ACC,
                 anchor="start"))
    o.append(txt(X(47), Y(DIGIT_CY) + 3.2, "into the live space, at 185 V", 3.0, ACC,
                 anchor="start"))
    o.append(f'<line x1="{pad-6:.1f}" y1="{GY:.2f}" x2="{X(50):.1f}" y2="{GY:.2f}" '
             f'stroke="#3A4149" stroke-width=".5"/>')

    rows = [
        ("Rear / top", "one sloped board on the cheek diagonal", "CLOSED"),
        ("Back", "12 mm strip below the diagonal", "CLOSED"),
        ("Bottom", "board under the main board, z 4 → 42", "CLOSED"),
        ("Ends", "the two cheeks", "CLOSED"),
        ("Front, below 30", "the fascia board", "CLOSED"),
        ("Front, 30 → 58.9", "the tube glass itself", "CLOSED"),
        ("Between tubes", "3 mm gaps onto the tube board face", "MASK ONLY"),
        ("Above 58.9", "tube board top edge, 3.1 mm", "KEEPOUT"),
    ]
    tx0, ty = 156.0, 40.0
    o.append(txt(tx0, ty, "EVERY FACE OF THE LIVE COMPARTMENT", 3.6, INK,
                 anchor="start", family=COND, weight="700"))
    o.append(f'<line x1="{tx0:.1f}" y1="{ty+2.6:.1f}" x2="{W-18:.1f}" '
             f'y2="{ty+2.6:.1f}" stroke="#2A3138" stroke-width=".4"/>')
    for i, (a_, b_, c_) in enumerate(rows):
        yy = ty + 9 + i * 5.0
        col = ACC if c_ in ("MASK ONLY", "KEEPOUT") else "#7FBF9A"
        o.append(txt(tx0, yy, a_, 2.9, DIMC, anchor="start"))
        o.append(txt(tx0 + 36, yy, b_, 2.9, MUTE, anchor="start"))
        o.append(txt(W - 18, yy, c_, 2.9, col, anchor="end"))
    ny = ty + 9 + len(rows) * 5.0 + 6
    o.append(f'<rect x="{tx0:.1f}" y="{ny-4:.1f}" width="{W-18-tx0:.1f}" height="26" '
             f'fill="#14100C" stroke="{ACC}" stroke-width=".4"/>')
    o.append(txt(tx0 + 4, ny + 1.5, "THE LAST TWO ARE DESIGN RULES, NOT PARTS", 2.9, ACC,
                 anchor="start", weight="600"))
    for i, ln in enumerate([
            "No exposed conductor anywhere on the tube board's front face outside",
            "a tube footprint — mask-covered traces only. HV keepout along its top",
            "edge. Both are per-unit QC checks, not design assumptions.",
            "3 mm between tubes is below finger reach; mask is the barrier there."]):
        o.append(txt(tx0 + 4, ny + 6.5 + i * 4.0, ln, 2.7, "#8B939C", anchor="start"))
    return sheet(W, H, "HV CONTAINMENT",
                 "there is no body, so every barrier is named and drawn",
                 "\n".join(o), pid)


# =================================================================== SCALE
def scale():
    pid = "fs"
    W, H = 470.0, 208.0
    GY = 180.0
    o = []
    o.append(f'<line x1="10" y1="{GY:.1f}" x2="{W-10:.1f}" y2="{GY:.1f}" '
             f'stroke="#3A4149" stroke-width=".6"/>')
    cx0 = 18.0
    for cx in (0.0, FACE_W - CH_T):
        o.append(f'<rect x="{cx0+cx:.2f}" y="{GY-CH_H:.2f}" width="{CH_T}" '
                 f'height="{CH_H}" rx="1.4" fill="{CASE}" stroke="#4A5058" stroke-width=".55"/>')
    o.append(f'<rect x="{cx0+CH_T:.2f}" y="{GY-FASCIA_H:.2f}" '
             f'width="{FACE_W-2*CH_T}" height="{FASCIA_H}" fill="{PCB}" '
             f'stroke="{PCB_E}" stroke-width=".45"/>')
    o.append(f'<rect x="{cx0+CH_T:.2f}" y="{GY-CH_H:.2f}" width="{FACE_W-2*CH_T}" '
             f'height="{CH_H-TY_12-EH:.2f}" fill="{PCB}" stroke="{PCB_E}" stroke-width=".35"/>')
    for i in range(8):
        cx, w, h, d, yb, df, ch = tube_at(i)
        frag = T.tube_face(pid, w, h, ch, ghosts=ch.isdigit(),
                           glyphset="0123456789" if ch.isdigit() else ch,
                           warm=WARM, hot=HOT, deep=DEEP, digit_frac=df,
                           ghost_op=.07, spec_op=.7, mesh_op=.34, socket=False)
        o.append(f'<g transform="translate({cx0+cx-w/2:.2f} {GY-yb-h:.2f})">{frag}</g>')
    o.append(f'<circle cx="{cx0+30:.1f}" cy="{GY-15:.1f}" r="5.0" fill="#343A42" '
             f'stroke="#79818B" stroke-width=".5"/>')
    o.append(txt(cx0 + FACE_W - 12, GY - 4.2, "TERMINAL·06", 4.4, COP, anchor="end",
                 weight="600"))
    o.append(txt(cx0 + FACE_W / 2, GY + 10,
                 f"TERMINAL·06 — {FACE_W:g} × {CH_H:g} × {CH_D:g}", 4.4, INK))

    px = 262.0
    o.append(f'<rect x="{px}" y="{GY-146}" width="71" height="146" rx="9" fill="#1A1E23" '
             f'stroke="#4A5058" stroke-width=".7"/>')
    o.append(f'<rect x="{px+3}" y="{GY-143}" width="65" height="140" rx="7" fill="#0D1013" '
             f'stroke="#2A3138" stroke-width=".4"/>')
    o.append(f'<rect x="{px+26}" y="{GY-141}" width="19" height="3.4" rx="1.7" fill="#20262C"/>')
    o.append(txt(px + 35.5, GY + 10, "PHONE — 146 × 71", 4.4, MUTE))

    mx = 356.0
    o.append(f'<path d="M{mx} {GY-95} L{mx} {GY-6} Q{mx} {GY} {mx+6} {GY} '
             f'L{mx+74} {GY} Q{mx+80} {GY} {mx+80} {GY-6} L{mx+80} {GY-95} Z" '
             f'fill="#1E2329" stroke="#4A5058" stroke-width=".7"/>')
    o.append(f'<ellipse cx="{mx+40}" cy="{GY-95}" rx="40" ry="7" fill="#141A1F" '
             f'stroke="#4A5058" stroke-width=".7"/>')
    o.append(f'<path d="M{mx+80} {GY-78} q26 0 26 21 t-26 21" fill="none" '
             f'stroke="#4A5058" stroke-width="4.6" stroke-linecap="round"/>')
    o.append(txt(mx + 40, GY + 10, "MUG — ⌀80 × 95", 4.4, MUTE))
    o.append(txt(W / 2, H - 8, "Rev E was 237 × 96 × 104. Rev F is lower than a mug "
                 "and shallower than a phone is long.", 3.0, MUTE))
    return sheet(W, H, "SCALE — 1:1", "against two things everyone owns",
                 "\n".join(o), pid)


# ==================================================================== write
def main():
    files = {
        "rf-hero.svg": hero(),
        "rf-night.svg": night_hero(),
        "rf-front.svg": front(),
        "rf-profile.svg": profile(),
        "rf-plan.svg": plan(),
        "rf-exploded.svg": exploded(),
        "rf-hv.svg": hv(),
        "rf-scale.svg": scale(),
    }
    for name, s in files.items():
        with open(os.path.join(OUT, name), "w") as f:
            f.write(s)
        print("%-18s %7d" % (name, len(s)))
    print("\nface %.1f   centres %s" % (FACE_W, [round(c, 2) for c in CENTRES]))
    print("digit line y=%.2f   ИН-17 bottom y=%.2f" % (DIGIT_CY, TY_17))


if __name__ == "__main__":
    main()
