#!/usr/bin/env python3
"""B vs C, developed — three-quarter and front for each.

Both are built on the corrected part (19.47 x 28.86 x 25.50, rear pins) and
the tightened row, which brings the face from 237 to 195.

The thing that actually separates them is where the controls live:

  B  SILL    a low raked ledge across the front carries the rotary, levers and
             buttons. There is still a moulded body, it is just small.
  C  CHEEKS  no body at all. The fascia becomes a fourth BOARD standing
             between two end plates, black mask, legend in silkscreen. Every
             structural element is either a PCB or one of the two cheeks.

Run: python3 render8.py  ->  b-sill-34.svg, b-sill-front.svg,
                             c-cheek-34.svg, c-cheek-front.svg
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

# ---------------------------------------------------- the part, from FCStd
EW, EH, ED = 19.47, 28.86, 25.50
S17_W, S17_H, S17_D = 15.0, 20.0, 20.0
BT = 1.60

# ---------------------------------------------------- the tightened row
FACE_W = 195.0
ROW = [(20.0, EW, EH, ED, "2"), (43.0, EW, EH, ED, "3"),
       (66.0, EW, EH, ED, "1"), (89.0, EW, EH, ED, "9"),
       (107.0, S17_W, S17_H, S17_D, "0"), (125.0, S17_W, S17_H, S17_D, "4"),
       (152.0, EW, EH, ED, "A"), (175.0, EW, EH, ED, "Р")]
COLON_X = 54.5
SCREENS = ["RUN", "TIME", "DISP", "AMB", "INFO", "DATE"]

STUDIO = {"top": 1.06, "front": .82, "right": .60, "left": .46,
          "back": .40, "bottom": .30}


def shell(sc, faces, base, skip=("bottom",), sw=.6, stroke=STROKE):
    for name, pts in faces.items():
        if name in skip:
            continue
        sc.poly(pts, mix(base, STUDIO[name]), stroke, sw)


def plate_x(sc, x0, y0, z0, w, h, d, base, stroke=None, sw=.35, n=None):
    """Wide thin plate as x-slices, so it depth-sorts correctly per segment.

    Slicing is unavoidable — one polygon sorts at one depth and would land
    wholly in front of or behind the tube row. But the slices must NOT be
    stroked: an outline on every segment draws the seams and the board comes
    out looking like a picket fence. Overlap them slightly and let the face
    shading carry the form instead.
    """
    n = n or max(2, int(w / 6.0))
    step = w / n
    for i in range(n):
        seg = raked(x0 + i * step, y0, z0, step * 1.08, h, d)
        for name, pts in seg.items():
            if name in ("bottom", "left", "right"):
                continue
            sc.poly(pts, mix(base, STUDIO[name]), stroke, sw)


def row(sc, pid, ybot, zfront, zboard):
    for (cx, w, h, d, ch) in ROW:
        x0 = cx - w / 2.0
        can = raked(x0, ybot, zfront, w, h, d)
        for name, pts in can.items():
            if name in ("bottom", "front"):
                continue
            sc.poly(pts, mix("#39434B", STUDIO[name]), STROKE, .45)
        glyphs = "0123456789" if ch.isdigit() else ch
        frag = T.tube_face(pid, w, h, ch, ghosts=ch.isdigit(), glyphset=glyphs,
                           warm=WARM, hot=HOT, deep=DEEP,
                           digit_frac=18.63 / EH if w == EW else .70,
                           ghost_op=.07, spec_op=.7, mesh_op=.34, socket=False)
        frag_on_face(sc, (x0, ybot + h, zfront - .3), frag, depth_bias=-9)
    for yy in (ybot + EH * .34, ybot + EH * .58):
        m, dz = sc.face_matrix((COLON_X, yy + 3.4, zfront - .6), (1, 0, 0), (0, -1, 0))
        sc.items.append((dz - 9, '<g transform="%s">%s</g>'
                         % (m, T.neon_dot(pid, 2.0, 1.7, 1.7, True, DEEP, WARM))))


def cap(sc, pt, s, dx=8.0, dy=0.0, size=5.0, col="#8B939C", anchor="start"):
    x, y, _ = sc.p2(pt)
    tx, ty = x + dx, y + dy
    run = len(s) * size * 0.56
    sc.pts.append((tx + (run if anchor == "start" else -run), ty))
    sc.pts.append((tx, ty - size))
    sc.items.append((-1e7, '<text x="%.2f" y="%.2f" font-family="%s" font-size="%.2f" '
                     'fill="%s" text-anchor="%s" letter-spacing=".4">%s</text>'
                     % (tx, ty, MONO, size, col, anchor, s)))


# ================================================================= B — SILL
SILL_H, SILL_D, SILL_LEAN = 26.0, 46.0, 10.0
B_TY = SILL_H                      # tubes sit on the sill
B_TZ = 5.0                         # glass recessed 5 behind the sill nose
B_BZ = B_TZ + ED


def b_controls(sc):
    """Rotary, levers and buttons on the raked sill face."""
    def fpt(xx, yy):
        return (xx, yy, SILL_LEAN * (yy / SILL_H))
    sc.begin_group()
    sc.poly([fpt(2, 1.5), fpt(FACE_W - 2, 1.5), fpt(FACE_W - 2, SILL_H - 1.5),
             fpt(2, SILL_H - 1.5)], "#191D21", "#4E545C", .7, bias=-3)
    kx, ky = 30.0, 13.0
    for i in range(6):
        a = math.radians(-80 + i * 32)
        p1 = fpt(kx + math.sin(a) * 8.0, ky + math.cos(a) * 8.0)
        p2 = fpt(kx + math.sin(a) * 10.4, ky + math.cos(a) * 10.4)
        sc.poly([p1, p2, (p2[0] + .9, p2[1], p2[2]), (p1[0] + .9, p1[1], p1[2])],
                ACC if i == 0 else "#BFB9AE", bias=-7)
    disc(sc, fpt, kx, ky, 5.4, "#343A42", "#79818B", .7)
    sc.poly([fpt(kx - .6, ky + 1.2), fpt(kx + .6, ky + 1.2),
             fpt(kx + .6, ky + 4.6), fpt(kx - .6, ky + 4.6)], ACC, bias=-9)
    for lx in (104, 118):
        sc.poly([fpt(lx - 1.6, ky - 4.4), fpt(lx + 1.6, ky - 4.4),
                 fpt(lx + 1.6, ky + 4.4), fpt(lx - 1.6, ky + 4.4)],
                "#343A42", "#79818B", .6, bias=-7)
    for bx in (148, 162):
        disc(sc, fpt, bx, ky, 3.0, "#343A42", "#79818B", .6)
    sc.text_on_face((FACE_W - 8, 4, SILL_LEAN * (4 / SILL_H) - .4), (1, 0, 0), (0, 1, 0),
                    "TERMINAL·06", 5.0, "#8E948C", anchor="end", weight="600",
                    family=MONO, depth_bias=-4)
    sc.end_group(-1e6)


def b_sill_34():
    pid = "bs"
    sc = Scene(yaw=32, pitch=11, scale=3.3)
    shell(sc, raked(0, 0, 0, FACE_W, SILL_H, SILL_D, SILL_LEAN), CASE_T)
    b_controls(sc)
    # tube board rises out of the sill
    plate_x(sc, 6.0, SILL_H - 6.0, B_BZ, FACE_W - 12.0, EH + 10.0, BT, PCB)
    # main board, vertical, behind the tube board
    plate_x(sc, 40.0, 4.0, SILL_D - 8.0, 115.0, 34.0, BT, PCB)
    row(sc, pid, B_TY, B_TZ, B_BZ)
    cap(sc, (FACE_W, SILL_H + EH + 4, B_BZ + BT), "tube board — black mask, on show",
        col="#9FB0A6")
    cap(sc, (FACE_W, SILL_H, 0), "sill 26 tall — the only moulded part", dy=9)
    return sc.render(defs=night_defs(pid, WARM, DEEP), pad=36)


# =============================================================== C — CHEEKS
CH_T, CH_H, CH_D = 6.0, 62.0, 44.0
C_FZ = 2.0                          # control board front face
C_TY = 30.0                         # tube bottom
C_TZ = 2.0
C_BZ = C_TZ + ED


def c_cheek_34():
    pid = "cc"
    sc = Scene(yaw=32, pitch=11, scale=3.3)
    # two end plates, tapered to the front
    for cx in (0.0, FACE_W - CH_T):
        shell(sc, raked(cx, 0, 0, CH_T, CH_H, CH_D), CASE_T, sw=.55)
    # the fascia is a BOARD, not a moulding
    plate_x(sc, CH_T, 0.0, C_FZ, FACE_W - 2 * CH_T, 26.0, BT, PCB)
    # tube board
    plate_x(sc, CH_T, 22.0, C_BZ, FACE_W - 2 * CH_T, EH + 12.0, BT, PCB)
    # main board, horizontal, low
    plate_x(sc, CH_T + 30, 5.0, 10.0, 115.0, BT, 30.0, PCB)
    row(sc, pid, C_TY, C_TZ, C_BZ)

    # the dial, silkscreened on the fascia board
    def fpt(xx, yy):
        return (xx, yy, C_FZ - .35)
    sc.begin_group()
    kx, ky = 30.0, 13.0
    for i in range(6):
        a = math.radians(-80 + i * 32)
        p1 = fpt(kx + math.sin(a) * 8.0, ky + math.cos(a) * 8.0)
        p2 = fpt(kx + math.sin(a) * 10.4, ky + math.cos(a) * 10.4)
        sc.poly([p1, p2, (p2[0] + .9, p2[1], p2[2]), (p1[0] + .9, p1[1], p1[2])],
                ACC if i == 0 else COP, bias=-7)
    disc(sc, fpt, kx, ky, 5.4, "#2A3138", "#6E7883", .6)
    sc.poly([fpt(kx - .6, ky + 1.2), fpt(kx + .6, ky + 1.2),
             fpt(kx + .6, ky + 4.6), fpt(kx - .6, ky + 4.6)], ACC, bias=-9)
    for lx in (104, 118):
        sc.poly([fpt(lx - 1.6, ky - 4.4), fpt(lx + 1.6, ky - 4.4),
                 fpt(lx + 1.6, ky + 4.4), fpt(lx - 1.6, ky + 4.4)],
                "#2A3138", "#6E7883", .55, bias=-7)
    for bx in (148, 162):
        disc(sc, fpt, bx, ky, 3.0, "#2A3138", "#6E7883", .55)
    sc.text_on_face((FACE_W - 12, 3.5, C_FZ - .5), (1, 0, 0), (0, 1, 0),
                    "TERMINAL·06", 4.6, COP, anchor="end", weight="600",
                    family=MONO, depth_bias=-6)
    sc.end_group(-1e6)

    cap(sc, (FACE_W, C_TY + EH + 6, C_BZ + BT), "tube board", col="#9FB0A6")
    cap(sc, (FACE_W, 26.0, C_FZ), "fascia is a BOARD — legend in silkscreen",
        dy=8, col=COP)
    cap(sc, (FACE_W, 0, CH_D), "cheek, 6 thick", dy=16)
    return sc.render(defs=night_defs(pid, WARM, DEEP), pad=36)


# ================================================================== FRONTS
def front(kind):
    """Orthographic front elevation, 1:1."""
    pid = "f" + kind
    pad = 16.0
    H = (SILL_H + EH + 10 if kind == "b" else CH_H) + 58
    W = FACE_W + 2 * pad
    GY = H - 32.0
    o = [f'<rect x="0" y="0" width="{W}" height="{H}" fill="#0B0D10"/>']
    title = "B · SILL — FRONT, 1:1" if kind == "b" else "C · CHEEKS — FRONT, 1:1"
    o.append(f'<text x="{W/2:.1f}" y="14" font-family="{COND}" font-size="7" '
             f'fill="#E4E1DA" text-anchor="middle" font-weight="700" '
             f'letter-spacing=".5">{title}</text>')

    def Y(y):
        return GY - y

    if kind == "b":
        o.append(f'<rect x="{pad:.1f}" y="{Y(SILL_H):.1f}" width="{FACE_W}" '
                 f'height="{SILL_H}" rx="1.5" fill="#23282E" stroke="#4A5058" '
                 f'stroke-width=".6"/>')
        o.append(f'<rect x="{pad+2:.1f}" y="{Y(SILL_H-1.5):.1f}" width="{FACE_W-4}" '
                 f'height="{SILL_H-3}" fill="#191D21" stroke="#4E545C" stroke-width=".4"/>')
        ty, tz = SILL_H, "#8B939C"
        # tube board edge peeking above the row
        o.append(f'<rect x="{pad+6:.1f}" y="{Y(SILL_H+EH+4):.1f}" width="{FACE_W-12}" '
                 f'height="4" fill="{PCB}" stroke="{PCB_E}" stroke-width=".4"/>')
        note = "sill carries the controls · tube board edge shows above the row"
    else:
        for cx in (0.0, FACE_W - CH_T):
            o.append(f'<rect x="{pad+cx:.1f}" y="{Y(CH_H):.1f}" width="{CH_T}" '
                     f'height="{CH_H}" rx="1.2" fill="#23282E" stroke="#4A5058" '
                     f'stroke-width=".6"/>')
        o.append(f'<rect x="{pad+CH_T:.1f}" y="{Y(26.0):.1f}" '
                 f'width="{FACE_W-2*CH_T}" height="26" fill="{PCB}" '
                 f'stroke="{PCB_E}" stroke-width=".5"/>')
        for i in range(6):
            xx = pad + CH_T + 66 + i * 20
            o.append(f'<path d="M{xx:.1f} {Y(23):.1f} h10 v-3 h6" fill="none" '
                     f'stroke="{COP}" stroke-width=".5" opacity=".55"/>')
        o.append(f'<rect x="{pad+CH_T:.1f}" y="{Y(C_TY+EH+8):.1f}" '
                 f'width="{FACE_W-2*CH_T}" height="8" fill="{PCB}" '
                 f'stroke="{PCB_E}" stroke-width=".4"/>')
        ty = C_TY
        note = "fascia is a black board · legend in silkscreen · cheeks 6 thick"

    for (cx, w, h, d, ch) in ROW:
        frag = T.tube_face(pid, w, h, ch, ghosts=ch.isdigit(),
                           glyphset="0123456789" if ch.isdigit() else ch,
                           warm=WARM, hot=HOT, deep=DEEP,
                           digit_frac=18.63 / EH if w == EW else .70,
                           ghost_op=.07, spec_op=.7, mesh_op=.34, socket=False)
        o.append(f'<g transform="translate({pad+cx-w/2:.2f} {Y(ty+h):.2f})">{frag}</g>')
    for yy in (ty + EH * .34, ty + EH * .58):
        o.append(f'<circle cx="{pad+COLON_X:.1f}" cy="{Y(yy):.1f}" r="1.7" '
                 f'fill="{WARM}" opacity=".85"/>')

    # controls
    kx, ky = pad + 30.0, Y(13.0)
    for i in range(6):
        a = math.radians(-80 + i * 32)
        s_, c_ = math.sin(a), -math.cos(a)
        o.append(f'<line x1="{kx+s_*6.6:.2f}" y1="{ky+c_*6.6:.2f}" x2="{kx+s_*8.6:.2f}" '
                 f'y2="{ky+c_*8.6:.2f}" stroke="{ACC if i==0 else (COP if kind=="c" else "#BFB9AE")}" '
                 f'stroke-width=".9" stroke-linecap="round"/>')
        lx, ly = kx + s_ * 11.2, ky + c_ * 11.2
        anc = "middle" if abs(s_) < .12 else ("start" if s_ > 0 else "end")
        o.append(f'<text x="{lx:.1f}" y="{ly+.9:.1f}" font-family="{MONO}" '
                 f'font-size="2.3" fill="{"#E4E1DA" if i==0 else "#6B737B"}" '
                 f'text-anchor="{anc}">{SCREENS[i]}</text>')
    o.append(f'<circle cx="{kx:.1f}" cy="{ky:.1f}" r="4.4" fill="#343A42" '
             f'stroke="#79818B" stroke-width=".6"/>')
    a0 = math.radians(-80)
    o.append(f'<line x1="{kx+math.sin(a0)*1.4:.2f}" y1="{ky-math.cos(a0)*1.4:.2f}" '
             f'x2="{kx+math.sin(a0)*3.8:.2f}" y2="{ky-math.cos(a0)*3.8:.2f}" '
             f'stroke="{ACC}" stroke-width="1.1" stroke-linecap="round"/>')
    for lx in (104, 118):
        o.append(f'<rect x="{pad+lx-1.6:.1f}" y="{Y(17.4):.1f}" width="3.2" height="8.8" '
                 f'rx="1" fill="#343A42" stroke="#79818B" stroke-width=".45"/>')
    for bx in (148, 162):
        o.append(f'<circle cx="{pad+bx:.1f}" cy="{ky:.1f}" r="3.0" fill="#343A42" '
                 f'stroke="#79818B" stroke-width=".45"/>')
    o.append(f'<text x="{pad+FACE_W-8:.1f}" y="{Y(3.0):.1f}" font-family="{MONO}" '
             f'font-size="4.2" fill="{COP if kind=="c" else "#8E948C"}" '
             f'text-anchor="end" font-weight="600">TERMINAL·06</text>')

    o.append(f'<line x1="{pad:.1f}" y1="{GY+4:.1f}" x2="{pad+FACE_W:.1f}" '
             f'y2="{GY+4:.1f}" stroke="#5E646C" stroke-width=".5"/>')
    for xx in (pad, pad + FACE_W):
        o.append(f'<line x1="{xx:.1f}" y1="{GY+2:.1f}" x2="{xx:.1f}" y2="{GY+6:.1f}" '
                 f'stroke="#5E646C" stroke-width=".5"/>')
    o.append(f'<text x="{W/2:.1f}" y="{GY+11:.1f}" font-family="{MONO}" font-size="3.4" '
             f'fill="#8FA4B2" text-anchor="middle">{FACE_W:g} — was 237</text>')
    o.append(f'<text x="{W/2:.1f}" y="{GY+18:.1f}" font-family="{MONO}" font-size="2.9" '
             f'fill="#6B737B" text-anchor="middle">{note}</text>')

    defs = '<defs>' + T.tube_defs(pid, warm=WARM, deep=DEEP) + '</defs>'
    return ('<svg preserveAspectRatio="xMidYMid meet" viewBox="0 0 %.1f %.1f" '
            'xmlns="http://www.w3.org/2000/svg" role="img">%s\n%s</svg>'
            % (W, H, defs, "\n".join(o)))


def main():
    for name, s in (("b-sill-34.svg", b_sill_34()),
                    ("b-sill-front.svg", front("b")),
                    ("c-cheek-34.svg", c_cheek_34()),
                    ("c-cheek-front.svg", front("c"))):
        with open(os.path.join(OUT, name), "w") as f:
            f.write(s)
        print(name, len(s))


if __name__ == "__main__":
    main()
