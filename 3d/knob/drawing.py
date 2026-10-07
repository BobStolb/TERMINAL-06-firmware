#!/usr/bin/env python3
"""Dimensioned drawing of knob C (turned) for a turner or a CNC service to quote from.

    python3 -I drawing.py        # writes knob_C-drawing.svg (vector, for the turner) and knob_C-drawing.png (the same, for a look)

The numbers are knob.scad's (part C, shaft sawn to 12.0 above the fascia face). Heights are from the knob's own underside
rim (datum A), not from the fascia. Nothing here was sent to a maker and no quote was asked for.
"""
import math, os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
S = 38.0                      # px per mm in the views
W, H = 2400, 1400

# ---- the part (mm), from knob.scad part C; z from the underside rim ------------------------------------------------
Z_RIM = 2.6                   # knob.scad's rim height above the fascia face: subtracted so that datum A = 0 at the rim
D        = 18.0               # skirt
GRIP     = 14.0
POCKET_D = 14.0
POCKET_H = 5.5 - Z_RIM        # 2.9
SKIRT_H  = 6.8 - Z_RIM        # 4.2
TOP      = 14.3 - Z_RIM       # 11.7 overall
BORE_D   = 6.00
BORE_H   = 6.8                # from the pocket ceiling
SCREW_Z  = POCKET_H + 3.5     # M3 axis above the rim: 6.4
LINE_W, LINE_DP = 0.8, 0.4
CH_RIM, CH_SKIRT, CH_GRIP_BASE, CH_TOP = 0.3, 0.4, 0.3, 0.8

ops = []                       # (kind, args) recorded once, drawn twice


def line(p, q, w=2, c="#000000", dash=None):
    ops.append(("line", p, q, w, c, dash))

def poly(pts, fill=None, outline="#000000", w=3):
    ops.append(("poly", pts, fill, outline, w))

def circ(c, r, w=2, col="#000000", fill=None, dash=None):
    ops.append(("circ", c, r, w, col, fill, dash))

def text(p, s, size=22, col="#000000", anchor="la"):
    ops.append(("text", p, s, size, col, anchor))


def arrow(p, q, c="#003a8c"):
    line(p, q, 2, c)
    for a, b in ((p, q), (q, p)):
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = math.hypot(dx, dy)
        ux, uy = dx / n, dy / n
        poly([a, (a[0] + 14 * ux - 4.5 * uy, a[1] + 14 * uy + 4.5 * ux), (a[0] + 14 * ux + 4.5 * uy, a[1] + 14 * uy - 4.5 * ux)], c, c, 1)


def dim_h(x1, x2, y, label, ext_from=None, c="#003a8c", above=True):
    """horizontal dimension between x1 and x2 (px) on the line y, with extension lines down to ext_from (px)."""
    if ext_from is not None:
        for x in (x1, x2):
            line((x, ext_from), (x, y + (-8 if ext_from > y else 8)), 1, c)
    arrow((x1, y), (x2, y), c)
    text(((x1 + x2) / 2, y - 6), label, 22, c, "ms")


def dim_v(y1, y2, x, label, ext_from=None, c="#003a8c"):
    if ext_from is not None:
        for y in (y1, y2):
            line((ext_from, y), (x + (8 if ext_from < x else -8), y), 1, c)
    arrow((x, y1), (x, y2), c)
    text((x - 8, (y1 + y2) / 2), label, 22, c, "rm")


# ---- half section, left: axis at x = AX, datum A at y = YA (the rim), z up --------------------------------------------
AX, YA = 760, 1000
def sec(r, z): return (AX + r * S, YA - z * S)

# the solid, right half, as a polygon (outer profile, then back along the pocket and the bore)
outer = [(POCKET_D / 2, 0), (D / 2 - CH_RIM, 0), (D / 2, CH_RIM), (D / 2, SKIRT_H - CH_SKIRT), (D / 2 - CH_SKIRT, SKIRT_H),
         (GRIP / 2 + CH_GRIP_BASE, SKIRT_H), (GRIP / 2, SKIRT_H + CH_GRIP_BASE), (GRIP / 2, TOP - CH_TOP), (GRIP / 2 - CH_TOP, TOP),
         (0, TOP), (0, POCKET_H + BORE_H), (BORE_D / 2, POCKET_H + BORE_H), (BORE_D / 2, POCKET_H), (POCKET_D / 2, POCKET_H)]
poly([sec(*p) for p in outer], "#d9dde3", "#000000", 3)
# the left half, mirrored, drawn lighter (the part is round; the half section shows the right side only in hatch)
poly([sec(-p[0], p[1]) for p in outer], "#eef0f3", "#000000", 2)
# M3 hole on the left (the tapped hole opposite the pointer), dashed on the right half would be hidden
line(sec(-BORE_D / 2, SCREW_Z - 1.25), sec(-GRIP / 2 - 0.2, SCREW_Z - 1.25), 2, "#000000", (10, 6))
line(sec(-BORE_D / 2, SCREW_Z + 1.25), sec(-GRIP / 2 - 0.2, SCREW_Z + 1.25), 2, "#000000", (10, 6))
# centre line
line((AX, YA + 40), (AX, YA - TOP * S - 40), 1, "#c04000", (24, 6, 4, 6))
# pointer line groove, seen in section at the top of the right half
poly([sec(0, TOP), sec(GRIP / 2 - CH_TOP, TOP), sec(GRIP / 2 - CH_TOP, TOP - LINE_DP), sec(0, TOP - LINE_DP)], "#ffffff", "#c04000", 2)

# dimensions of the section
dim_h(sec(-D / 2, 0)[0], sec(D / 2, 0)[0], YA + 120, "D 18.0 (+0 / -0.1)", YA)
dim_h(sec(-GRIP / 2, 0)[0], sec(GRIP / 2, 0)[0], YA - TOP * S - 70, "14.0 ±0.1 knurled grip", YA - TOP * S)
dim_h(sec(-POCKET_D / 2, 0)[0], sec(POCKET_D / 2, 0)[0], YA + 60, "pocket 14.0 +0.1 / 0", YA)
dim_h(sec(-BORE_D / 2, 0)[0] + 0, sec(BORE_D / 2, 0)[0], YA - (POCKET_H + BORE_H) * S - 28, "bore 6.00 +0.05 / 0", YA - (POCKET_H + BORE_H) * S)
dim_v(YA, YA - TOP * S, sec(D / 2, 0)[0] + 100, "11.7 overall", sec(D / 2, 0)[0] + 4)
dim_v(YA, YA - SKIRT_H * S, sec(D / 2, 0)[0] + 180, "4.2 skirt", sec(D / 2, 0)[0] + 4)
dim_v(YA, YA - POCKET_H * S, sec(-D / 2, 0)[0] - 100, "pocket 2.9", sec(-D / 2, 0)[0] - 4)
dim_v(YA - POCKET_H * S, YA - (POCKET_H + BORE_H) * S, sec(-D / 2, 0)[0] - 180, "bore 6.8 deep", sec(-D / 2, 0)[0] - 4)
dim_v(YA - POCKET_H * S, YA - SCREW_Z * S, sec(-GRIP / 2, 0)[0] - 90, "M3 axis 3.5", sec(-GRIP / 2, 0)[0] - 4)
text((sec(-GRIP / 2, 0)[0] - 8, YA - SCREW_Z * S - 36), "M3 tapped, radial (dashed)", 20, "#000000", "rm")
text((AX, 70), "SECTION (half), datum A = the underside rim", 26, "#000000", "ma")
text((AX, 104), "chamfers: rim 0.3, skirt top 0.4, grip base 0.3, grip top 0.8 (45 deg)", 20, "#444444", "ma")

# ---- top view, right: pointer straight up ------------------------------------------------------------------------------
TX, TY = 1900, 560
def top(x, y): return (TX + x * S, TY - y * S)
circ((TX, TY), D / 2 * S, 3)
circ((TX, TY), (D / 2 - CH_SKIRT) * S, 1, "#777777")
circ((TX, TY), GRIP / 2 * S, 3)
circ((TX, TY), (GRIP / 2 - CH_TOP) * S, 1, "#777777")
for i in range(44):                                   # the knurl: 44 straight flutes (the turner's pitch may differ)
    a = math.radians(i * 360 / 44)
    line((TX + math.cos(a) * (GRIP / 2 - 0.35) * S, TY - math.sin(a) * (GRIP / 2 - 0.35) * S),
         (TX + math.cos(a) * (GRIP / 2) * S, TY - math.sin(a) * (GRIP / 2) * S), 1, "#999999")
# the pointer line, up: a 0.8 mm bright line from the centre of the top, down the flank, across the skirt to the rim
poly([top(-LINE_W / 2, 0), top(LINE_W / 2, 0), top(LINE_W / 2, D / 2 + 0.05), top(-LINE_W / 2, D / 2 + 0.05)], "#ffffff", "#c04000", 2)
line((TX, TY + 20), (TX, TY - D / 2 * S - 40), 1, "#c04000", (24, 6, 4, 6))
line((TX - D / 2 * S - 40, TY), (TX + D / 2 * S + 40, TY), 1, "#c04000", (24, 6, 4, 6))
text((TX + 18, TY - D / 2 * S - 52), "pointer line 0.8 wide x 0.4 deep,", 20, "#c04000")
text((TX + 18, TY - D / 2 * S - 28), "cut through the anodise: bright metal", 20, "#c04000")
text((TX, TY + D / 2 * S + 40), "TOP VIEW (pointer shown up)", 26, "#000000", "ma")
# the set screw on the opposite side
circ((TX, TY + (GRIP / 2) * S), 5, 2, "#000000")
text((TX + 14, TY + GRIP / 2 * S + 14), "M3", 20, "#000000")

# ---- notes and title block -------------------------------------------------------------------------------------------------
NX, NY = 60, 1130
text((NX, NY), "TS06 MODE knob C, turned: one piece, round, black with a bright pointer line.  Datum A = the underside rim.  Scale: views 1:1 at 38 px/mm.", 24)
notes = [
    "Material: aluminium 6082-T6 or 6061-T6 (black anodising), or brass CuZn39Pb3 (CW614N, free-cutting; black chemical finish or left bright).",
    "Finish (aluminium): black dyed anodising, type II, 10 to 15 um, sealed.  The pointer line is cut or laser-engraved AFTER anodising so the metal shows.",
    "Grip: straight knurl on the 14.0 mm band, about 1.0 mm pitch (44 flutes drawn; the turner's knurl may differ), finished diameter 14.0 +/-0.2.",
    "Bore 6.00 +0.05 / 0 mm, a slide fit on the SR25's 6 mm shaft; concentric with the 18.0 outside to 0.05 TIR; square to the underside rim within 0.05.",
    "M3 radial hole at 180 deg from the pointer line, 3.5 above the pocket ceiling (6.4 above the rim): tapped M3, thread through the whole grip wall, burr-free into the bore.",
    "Pocket (underneath) 14.0 +0.1 / 0 mm by 2.9 deep: it clears the shaft nut (across corners up to 13.3 mm, INFERRED: measure the nut and say if it is wider).",
    "General tolerance +/-0.1 mm; edges broken 0.1; no sharp burrs; surface Ra 1.6 on the skirt top and grip.  The 18.0 mm skirt diameter is one parameter of knob.scad (D).",
    "Shaft form of the SR25 (plain, D-flat or knurled) is NOT confirmed: the set screw works on all three, so no flat is cut in the bore.",
    "Quantity: 1 prototype, then 10 or 20.  Do not copy a maker name or number onto the part.",
]
for i, n in enumerate(notes):
    text((NX, NY + 36 + i * 26), n, 20, "#222222")


# ---- render ----------------------------------------------------------------------------------------------------------------
def font(size):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/freefont/FreeSans.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def to_png(path):
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    for op in ops:
        k = op[0]
        if k == "line":
            _, p, q, w, c, dash = op
            if not dash:
                d.line([p, q], fill=c, width=int(w))
            else:
                L = math.hypot(q[0] - p[0], q[1] - p[1])
                if L == 0:
                    continue
                ux, uy = (q[0] - p[0]) / L, (q[1] - p[1]) / L
                t, i, on = 0.0, 0, True
                while t < L:
                    seg = dash[i % len(dash)]
                    t2 = min(L, t + seg)
                    if on:
                        d.line([(p[0] + ux * t, p[1] + uy * t), (p[0] + ux * t2, p[1] + uy * t2)], fill=c, width=int(w))
                    t, i, on = t2, i + 1, not on
        elif k == "poly":
            _, pts, fill, outline, w = op
            d.polygon(pts, fill=fill)
            d.line(list(pts) + [pts[0]], fill=outline, width=int(w), joint="curve")
        elif k == "circ":
            _, c, r, w, col, fill, dash = op
            d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], outline=col, width=int(w), fill=fill)
        elif k == "text":
            _, p, s, size, col, anchor = op
            d.text(p, s, fill=col, font=font(size), anchor=anchor)
    im.save(path)


def to_svg(path):
    o = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" font-family="DejaVu Sans, Arial, sans-serif">' % (W, H, W, H),
         '<rect width="100%" height="100%" fill="white"/>']
    for op in ops:
        k = op[0]
        if k == "line":
            _, p, q, w, c, dash = op
            da = ' stroke-dasharray="%s"' % ",".join(str(x) for x in dash) if dash else ""
            o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="%s"%s/>' % (p[0], p[1], q[0], q[1], c, w, da))
        elif k == "poly":
            _, pts, fill, outline, w = op
            o.append('<polygon points="%s" fill="%s" stroke="%s" stroke-width="%s"/>' % (" ".join("%.1f,%.1f" % p for p in pts), fill or "none", outline, w))
        elif k == "circ":
            _, c, r, w, col, fill, dash = op
            o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" stroke="%s" stroke-width="%s"/>' % (c[0], c[1], r, fill or "none", col, w))
        elif k == "text":
            _, p, s, size, col, anchor = op
            ta = {"l": "start", "m": "middle", "r": "end"}[anchor[0]]
            dy = {"a": size * 0.8, "m": size * 0.35, "s": 0}[anchor[1]]
            s = s.replace("&", "&amp;").replace("<", "&lt;")
            o.append('<text x="%.1f" y="%.1f" font-size="%d" fill="%s" text-anchor="%s">%s</text>' % (p[0], p[1] + dy, size, col, ta, s))
    o.append("</svg>")
    open(path, "w").write("\n".join(o))


if __name__ == "__main__":
    to_png(os.path.join(HERE, "knob_C-drawing.png"))
    to_svg(os.path.join(HERE, "knob_C-drawing.svg"))
    print("wrote knob_C-drawing.png and .svg")
