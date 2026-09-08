#!/usr/bin/env python3
"""Rev F — TERMINAL-06 on the cheeks architecture.

Settled 05.09.26. Two end plates and five boards; no moulded body. Every
dimension is from 3d/IN12.FCStd or from the row recomputed against it.

The cheek is now the only part in the object that is not a PCB, so it gets
a real profile rather than a block: full height at the front where it carries
the fascia and the tubes, tapering back to 16 mm where there is only the main
board to hold. That taper is the side view, and the side view is what was
wrong with every previous revision.

Choosing an open frame has one consequence that has to be designed in, not
noticed later: THE REAR OF THE TUBE BOARD CARRIES 185 V ON EXPOSED PINS.
A rear closure is not optional here.

Run: python3 render9.py
"""
import math, os

import tubes as T
from render import Scene, raked, proj, mix, disc, STROKE, CASE_T, ACC_T, GLOW_T
from render3 import frag_on_face, night_defs

OUT = os.path.dirname(os.path.abspath(__file__))
MONO = "IBM Plex Mono, monospace"
COND = "IBM Plex Sans Condensed, Arial Narrow, sans-serif"
WARM, DEEP, HOT = GLOW_T, "#FF5A08", "#FFE0BC"
ACC = ACC_T
PCB, PCB_E, COP = "#141A1E", "#39474E", "#B08A4A"
DIM = "#8FA4B2"

# ------------------------------------------------------------- the part
EW, EH, ED = 19.47, 28.86, 25.50
S17_W, S17_H, S17_D = 15.0, 20.0, 20.0
BT = 1.60

# ------------------------------------------------------------- the object
FACE_W, CH_T, CH_D, CH_H = 195.0, 6.0, 44.0, 62.0
FASCIA_H = 26.0
FZ = 2.0                       # fascia front face
TY, TZ = 30.0, 2.0             # tube bottom, tube glass front
BZ = TZ + ED                   # tube board front face = 27.5
REAR_Z = CH_D - BT             # rear closure

ROW = [(20.0, EW, EH, ED, "2"), (43.0, EW, EH, ED, "3"),
       (66.0, EW, EH, ED, "1"), (89.0, EW, EH, ED, "9"),
       (107.0, S17_W, S17_H, S17_D, "0"), (125.0, S17_W, S17_H, S17_D, "4"),
       (152.0, EW, EH, ED, "A"), (175.0, EW, EH, ED, "Р")]
COLON_X = 54.5
SCREENS = ["RUN", "TIME", "DISP", "AMB", "INFO", "DATE"]

# cheek profile in (z, y), front at z=0 — the shape that is the side view
CHEEK = [(0, 4), (4, 0), (40, 0), (44, 4), (44, 16),
         (30, 60), (27, 62), (10, 62), (0, 52)]

STUDIO = {"top": 1.06, "front": .82, "right": .60, "left": .46,
          "back": .40, "bottom": .30}


def plate_x(sc, x0, y0, z0, w, h, d, base, n=None):
    n = n or max(2, int(w / 6.0))
    step = w / n
    for i in range(n):
        seg = raked(x0 + i * step, y0, z0, step * 1.08, h, d)
        for name, pts in seg.items():
            if name in ("bottom", "left", "right"):
                continue
            sc.poly(pts, mix(base, STUDIO[name]), None)


def prism_x(sc, prof, x0, t, base, sw=.5):
    """Extrude a (z, y) profile along x — the cheek.

    raked() only makes boxes, so an arbitrary side profile needs its own
    solid: two end faces plus one quad per profile edge.
    """
    n = len(prof)
    outer = [(x0, y, z) for (z, y) in prof]
    inner = [(x0 + t, y, z) for (z, y) in prof]
    for i in range(n):
        j = (i + 1) % n
        sc.poly([outer[i], outer[j], inner[j], inner[i]],
                mix(base, STUDIO["right"]), STROKE, sw * .8)
    sc.poly(inner, mix(base, STUDIO["left"]), STROKE, sw)
    sc.poly(outer, mix(base, STUDIO["front"]), STROKE, sw)


def row(sc, pid):
    for (cx, w, h, d, ch) in ROW:
        x0 = cx - w / 2.0
        can = raked(x0, TY, TZ, w, h, d)
        for name, pts in can.items():
            if name in ("bottom", "front"):
                continue
            sc.poly(pts, mix("#39434B", STUDIO[name]), STROKE, .45)
        frag = T.tube_face(pid, w, h, ch, ghosts=ch.isdigit(),
                           glyphset="0123456789" if ch.isdigit() else ch,
                           warm=WARM, hot=HOT, deep=DEEP,
                           digit_frac=18.63 / EH if w == EW else .70,
                           ghost_op=.07, spec_op=.7, mesh_op=.34, socket=False)
        frag_on_face(sc, (x0, TY + h, TZ - .3), frag, depth_bias=-9)
    for yy in (TY + EH * .34, TY + EH * .58):
        m, dz = sc.face_matrix((COLON_X, yy + 3.4, TZ - .6), (1, 0, 0), (0, -1, 0))
        sc.items.append((dz - 9, '<g transform="%s">%s</g>'
                         % (m, T.neon_dot(pid, 2.0, 1.7, 1.7, True, DEEP, WARM))))


def fascia_face(sc):
    def fpt(xx, yy):
        return (xx, yy, FZ - .35)
    sc.begin_group()
    kx, ky = 30.0, 13.0
    for i in range(6):
        a = math.radians(-80 + i * 32)
        p1 = fpt(kx + math.sin(a) * 6.6, ky + math.cos(a) * 6.6)
        p2 = fpt(kx + math.sin(a) * 8.6, ky + math.cos(a) * 8.6)
        sc.poly([p1, p2, (p2[0] + .8, p2[1], p2[2]), (p1[0] + .8, p1[1], p1[2])],
                ACC if i == 0 else COP, bias=-7)
    disc(sc, fpt, kx, ky, 4.4, "#2A3138", "#6E7883", .55)
    sc.poly([fpt(kx - .55, ky + 1.0), fpt(kx + .55, ky + 1.0),
             fpt(kx + .55, ky + 3.8), fpt(kx - .55, ky + 3.8)], ACC, bias=-9)
    for lx in (104, 118):
        sc.poly([fpt(lx - 1.6, ky - 4.4), fpt(lx + 1.6, ky - 4.4),
                 fpt(lx + 1.6, ky + 4.4), fpt(lx - 1.6, ky + 4.4)],
                "#2A3138", "#6E7883", .5, bias=-7)
    for bx in (148, 162):
        disc(sc, fpt, bx, ky, 3.0, "#2A3138", "#6E7883", .5)
    # copper ornament, kept off the control zone
    for i in range(5):
        xx = 76 + i * 20
        sc.poly([fpt(xx, 21.4), fpt(xx + 9, 21.4), fpt(xx + 9, 22.0), fpt(xx, 22.0)],
                COP, extra=' opacity=".5"', bias=-6)
    sc.text_on_face((FACE_W - 12, 3.5, FZ - .5), (1, 0, 0), (0, 1, 0),
                    "TERMINAL·06", 4.6, COP, anchor="end", weight="600",
                    family=MONO, depth_bias=-6)
    sc.end_group(-1e6)


def cap(sc, pt, s, dx=8.0, dy=0.0, size=5.0, col="#8B939C", anchor="start"):
    x, y, _ = sc.p2(pt)
    tx, ty = x + dx, y + dy
    run = len(s) * size * 0.56
    sc.pts.append((tx + (run if anchor == "start" else -run), ty))
    sc.pts.append((tx, ty - size))
    sc.items.append((-1e7, '<text x="%.2f" y="%.2f" font-family="%s" font-size="%.2f" '
                     'fill="%s" text-anchor="%s" letter-spacing=".4">%s</text>'
                     % (tx, ty, MONO, size, col, anchor, s)))


# ==================================================================== HERO
def hero():
    pid = "rf"
    sc = Scene(yaw=31, pitch=10, scale=3.4)
    for cx in (0.0, FACE_W - CH_T):
        prism_x(sc, CHEEK, cx, CH_T, CASE_T)
    plate_x(sc, CH_T, 0.0, REAR_Z, FACE_W - 2 * CH_T, CH_H, BT, "#101519")   # rear
    plate_x(sc, CH_T, 4.0, 8.0, FACE_W - 2 * CH_T, BT, 32.0, PCB)            # main
    plate_x(sc, CH_T, 22.0, BZ, FACE_W - 2 * CH_T, CH_H - 22.0, BT, PCB)     # tube
    plate_x(sc, CH_T, 0.0, FZ, FACE_W - 2 * CH_T, FASCIA_H, BT, PCB)         # fascia
    fascia_face(sc)
    row(sc, pid)
    cap(sc, (FACE_W, CH_H, BZ), "tube board", col="#9FB0A6")
    cap(sc, (FACE_W, FASCIA_H, FZ), "fascia — black mask, legend in silkscreen",
        dy=9, col=COP)
    cap(sc, (FACE_W, 0, CH_D), "cheek 6 thick — the only non-PCB part", dy=18)
    return sc.render(defs=night_defs(pid, WARM, DEEP), pad=38)


# ============================================================ CHEEK, 1:1
def cheek_sheet():
    W, H = 250.0, 148.0
    pad, GY = 42.0, 104.0
    o = [f'<rect x="0" y="0" width="{W}" height="{H}" fill="#0B0D10"/>']
    o.append(f'<text x="{W/2:.1f}" y="13" font-family="{COND}" font-size="6.6" '
             f'fill="#E4E1DA" text-anchor="middle" font-weight="700" '
             f'letter-spacing=".5">THE CHEEK — 1:1, AND WHAT IT CARRIES</text>')
    o.append(f'<text x="{W/2:.1f}" y="19.5" font-family="{MONO}" font-size="3.0" '
             f'fill="#6B737B" text-anchor="middle">full height at the front, '
             f'tapering to 16 at the back — this profile is the side view</text>')

    def X(z): return pad + z
    def Y(y): return GY - y

    pts = " ".join(f"{X(z):.1f},{Y(y):.1f}" for (z, y) in CHEEK)
    o.append(f'<polygon points="{pts}" fill="#252A30" stroke="#5C6771" stroke-width=".7"/>')

    # what it holds, ghosted in
    def ghost(z, y, w, h, col, label, ly=None):
        o.append(f'<rect x="{X(z):.1f}" y="{Y(y+h):.1f}" width="{w:.1f}" '
                 f'height="{h:.1f}" fill="{col}" opacity=".85" stroke="{PCB_E}" '
                 f'stroke-width=".35"/>')
        if label:
            o.append(f'<text x="{X(z)+w+3:.1f}" y="{Y(ly or (y+h/2)):.1f}" '
                     f'font-family="{MONO}" font-size="2.8" fill="#8FA4B2">{label}</text>')

    ghost(FZ, 0, BT, FASCIA_H, PCB, None)
    ghost(BZ, 22, BT, CH_H - 22, PCB, None)
    ghost(REAR_Z, 0, BT, CH_H, "#101519", None)
    o.append(f'<rect x="{X(8):.1f}" y="{Y(4+BT):.1f}" width="32" height="{BT}" '
             f'fill="{PCB}" stroke="{PCB_E}" stroke-width=".35"/>')
    # the tube
    o.append(f'<rect x="{X(TZ):.1f}" y="{Y(TY+EH):.1f}" width="{ED}" height="{EH}" '
             f'rx="1.2" fill="#1B2026" stroke="#5C6771" stroke-width=".55"/>')
    o.append(f'<rect x="{X(TZ):.1f}" y="{Y(TY+EH):.1f}" width="2" height="{EH}" '
             f'fill="{WARM}" opacity=".34"/>')
    for i in range(5):
        yy = Y(TY + EH / 2) - 8 + i * 4
        o.append(f'<line x1="{X(BZ):.1f}" y1="{yy:.1f}" x2="{X(BZ)+4.6:.1f}" '
                 f'y2="{yy:.1f}" stroke="#9AA6B0" stroke-width=".45"/>')

    # callouts to the right
    for (zz, yy, s) in ((FZ, 20, "fascia board"), (BZ, 50, "tube board"),
                        (REAR_Z, 40, "rear closure — HV barrier"),
                        (8, 6, "main board")):
        o.append(f'<line x1="{X(zz)+2:.1f}" y1="{Y(yy):.1f}" x2="{X(58):.1f}" '
                 f'y2="{Y(yy):.1f}" stroke="#3C444C" stroke-width=".35"/>')
        o.append(f'<text x="{X(60):.1f}" y="{Y(yy)+1:.1f}" font-family="{MONO}" '
                 f'font-size="3.0" fill="{ACC if "HV" in s else "#8FA4B2"}">{s}</text>')

    def dimh(x1, x2, y, lab):
        o.append(f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{x2:.1f}" y2="{y:.1f}" '
                 f'stroke="#5E646C" stroke-width=".45"/>')
        for x in (x1, x2):
            o.append(f'<line x1="{x:.1f}" y1="{y-2:.1f}" x2="{x:.1f}" y2="{y+2:.1f}" '
                     f'stroke="#5E646C" stroke-width=".45"/>')
        o.append(f'<text x="{(x1+x2)/2:.1f}" y="{y+6:.1f}" font-family="{MONO}" '
                 f'font-size="3.2" fill="#8FA4B2" text-anchor="middle">{lab}</text>')

    dimh(X(0), X(CH_D), GY + 8, "44 deep")
    o.append(f'<line x1="{X(-8):.1f}" y1="{Y(0):.1f}" x2="{X(-8):.1f}" y2="{Y(CH_H):.1f}" '
             f'stroke="#5E646C" stroke-width=".45"/>')
    o.append(f'<text x="{X(-11):.1f}" y="{Y(CH_H/2):.1f}" font-family="{MONO}" '
             f'font-size="3.2" fill="#8FA4B2" text-anchor="end">62</text>')
    o.append(f'<text x="{X(44):.1f}" y="{Y(10):.1f}" font-family="{MONO}" font-size="3.0" '
             f'fill="#6B737B" text-anchor="start"> 16 at the back</text>')
    o.append(f'<line x1="{pad-14:.1f}" y1="{GY:.1f}" x2="{W-14:.1f}" y2="{GY:.1f}" '
             f'stroke="#3A4149" stroke-width=".5"/>')

    o.append(f'<rect x="14" y="{H-24:.1f}" width="{W-28:.1f}" height="17" '
             f'fill="#14100C" stroke="{ACC}" stroke-width=".5"/>')
    o.append(f'<text x="19" y="{H-18:.1f}" font-family="{MONO}" font-size="3.0" '
             f'fill="{ACC}" font-weight="600">THE OPEN FRAME COSTS A REAR CLOSURE</text>')
    o.append(f'<text x="19" y="{H-13:.1f}" font-family="{MONO}" font-size="2.7" '
             f'fill="#8B939C">Tube pins protrude 4.65 mm behind the tube board and sit '
             f'at 185 V. With no body there is nothing else between them</text>')
    o.append(f'<text x="19" y="{H-9:.1f}" font-family="{MONO}" font-size="2.7" '
             f'fill="#8B939C">and a finger. The rear board is a barrier first and a '
             f'graphics panel second. A bottom closure is needed for the same reason.</text>')

    defs = '<defs>' + T.tube_defs("ck", warm=WARM, deep=DEEP) + '</defs>'
    return ('<svg preserveAspectRatio="xMidYMid meet" viewBox="0 0 %.1f %.1f" '
            'xmlns="http://www.w3.org/2000/svg" role="img">%s\n%s</svg>'
            % (W, H, defs, "\n".join(o)))


# ================================================================ EXPLODED
def exploded():
    """Exploded SIDE ELEVATION, not an axonometric.

    The five elements are stacked front-to-back, so exploding them along z in
    a three-quarter view just piles them up behind one another and reads as a
    dark smear. Pulled apart on a section they read at a glance.
    """
    W, H = 300.0, 150.0
    GY, TOP = 108.0, 30.0
    o = [f'<rect x="0" y="0" width="{W}" height="{H}" fill="#0B0D10"/>']
    o.append(f'<text x="{W/2:.1f}" y="13" font-family="{COND}" font-size="6.6" '
             f'fill="#E4E1DA" text-anchor="middle" font-weight="700" '
             f'letter-spacing=".5">THE STACK — EXPLODED SECTION</text>')
    o.append(f'<text x="{W/2:.1f}" y="19.5" font-family="{MONO}" font-size="3.0" '
             f'fill="#6B737B" text-anchor="middle">five elements between two cheeks · '
             f'true z in brackets · nothing here is moulded except the cheeks</text>')

    def Y(y): return GY - y

    # exploded slot, true z, drawer
    def slot(sx, truez, label, col, draw):
        draw(sx)
        o.append(f'<text x="{sx:.1f}" y="{Y(-8):.1f}" font-family="{MONO}" '
                 f'font-size="3.0" fill="{col}" text-anchor="middle">{label}</text>')
        o.append(f'<text x="{sx:.1f}" y="{Y(-13):.1f}" font-family="{MONO}" '
                 f'font-size="2.6" fill="#5A6169" text-anchor="middle">z {truez}</text>')

    def board(sx, y0, h, col=PCB):
        o.append(f'<rect x="{sx-BT/2:.2f}" y="{Y(y0+h):.1f}" width="{BT}" '
                 f'height="{h:.1f}" fill="{col}" stroke="{PCB_E}" stroke-width=".4"/>')

    slot(40.0, "2.0", "FASCIA", COP,
         lambda sx: (board(sx, 0, FASCIA_H),
                     o.append(f'<circle cx="{sx:.1f}" cy="{Y(13):.1f}" r="4.4" '
                              f'fill="#2A3138" stroke="#6E7883" stroke-width=".5"/>')))
    def tubes(sx):
        o.append(f'<rect x="{sx-ED/2:.1f}" y="{Y(TY+EH):.1f}" width="{ED}" '
                 f'height="{EH}" rx="1.2" fill="#1B2026" stroke="#5C6771" stroke-width=".55"/>')
        o.append(f'<rect x="{sx-ED/2:.1f}" y="{Y(TY+EH):.1f}" width="2" height="{EH}" '
                 f'fill="{WARM}" opacity=".34"/>')
        for i in range(5):
            yy = Y(TY + EH / 2) - 8 + i * 4
            o.append(f'<line x1="{sx+ED/2:.1f}" y1="{yy:.1f}" x2="{sx+ED/2+4.6:.1f}" '
                     f'y2="{yy:.1f}" stroke="#9AA6B0" stroke-width=".45"/>')
    slot(95.0, "2.0 → 27.5", "8 TUBES", "#C8B49A", tubes)
    slot(150.0, "27.5", "TUBE BOARD", "#9FB0A6", lambda sx: board(sx, 22, CH_H - 22))
    slot(200.0, "8 → 40", "MAIN BOARD", "#8FBFA4",
         lambda sx: o.append(f'<rect x="{sx-16:.1f}" y="{Y(6):.1f}" width="32" '
                             f'height="{BT}" fill="{PCB}" stroke="{PCB_E}" stroke-width=".4"/>'))
    slot(255.0, "42.4", "REAR CLOSURE", ACC,
         lambda sx: board(sx, 0, CH_H, "#101519"))

    # assembly axis
    o.append(f'<line x1="24" y1="{Y(TY+EH/2):.1f}" x2="{W-24:.1f}" y2="{Y(TY+EH/2):.1f}" '
             f'stroke="#3C444C" stroke-width=".4" stroke-dasharray="4 4"/>')
    o.append(f'<line x1="24" y1="{GY:.1f}" x2="{W-24:.1f}" y2="{GY:.1f}" '
             f'stroke="#3A4149" stroke-width=".5"/>')

    o.append(f'<rect x="14" y="{H-26:.1f}" width="{W-28:.1f}" height="19" '
             f'fill="#14100C" stroke="{ACC}" stroke-width=".5"/>')
    o.append(f'<text x="19" y="{H-20:.1f}" font-family="{MONO}" font-size="3.0" '
             f'fill="{ACC}" font-weight="600">THE OPEN FRAME COSTS A REAR CLOSURE, '
             f'AND A BOTTOM ONE</text>')
    o.append(f'<text x="19" y="{H-15:.1f}" font-family="{MONO}" font-size="2.7" '
             f'fill="#8B939C">Pins protrude 4.65 behind the tube board at 185 V. With no '
             f'body, the rear board is the only thing between them and a finger —</text>')
    o.append(f'<text x="19" y="{H-10.5:.1f}" font-family="{MONO}" font-size="2.7" '
             f'fill="#8B939C">a barrier first, a graphics panel second. The main board '
             f'needs the same treatment underneath. Per-unit QC check, not an assumption.</text>')

    defs = '<defs>' + T.tube_defs("xp", warm=WARM, deep=DEEP) + '</defs>'
    return ('<svg preserveAspectRatio="xMidYMid meet" viewBox="0 0 %.1f %.1f" '
            'xmlns="http://www.w3.org/2000/svg" role="img">%s\n%s</svg>'
            % (W, H, defs, "\n".join(o)))


def main():
    for name, s in (("f-hero.svg", hero()),
                    ("f-cheek.svg", cheek_sheet()),
                    ("f-exploded.svg", exploded())):
        with open(os.path.join(OUT, name), "w") as f:
            f.write(s)
        print(name, len(s))


if __name__ == "__main__":
    main()
