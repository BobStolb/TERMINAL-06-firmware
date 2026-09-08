#!/usr/bin/env python3
"""Rev F variant study — how the ИН-12 tube board resolves.

Rear-exit pins mean the tubes hang off a vertical board. That board is now a
visible design element, and there are two candidates worth drawing:

  A  RAIL      one narrow board the full width of the row, its height matched
               to the pin field so the tubes themselves hide it. Reads as
               floating glass.
  B  SPINES    four short boards, one per tube group, so the colon / seconds /
               annex gaps become real voids. This is what the prototype's two
               hand-decorated daughterboards already are.

Both are direct-solder: the ten boards in hand have holes sized for tube pins,
too small to accept sockets. Sockets are a future-board goal, and would add an
uncharacterised seat height to every depth figure here.

Geometry from 3d/IN12.FCStd. Run: python3 render6.py
"""
import math, os

import tubes as T
from render import Scene, raked, proj, mix, disc, STROKE, CASE_T, ACC_T, GLOW_T
from render3 import frag_on_face, night_defs

OUT = os.path.dirname(os.path.abspath(__file__))
MONO = "IBM Plex Mono, monospace"
COND = "IBM Plex Sans Condensed, Arial Narrow, sans-serif"
WARM, DEEP, HOT = GLOW_T, "#FF5A08", "#FFE0BC"
PCB, PCB_HI = "#17462C", "#26663F"   # green here so the board reads as a board;
                                     # black mask is the likely production choice

# ----------------------------------------------------- the part, from FCStd
ENV_W, ENV_H, ENV_D = 19.47, 28.86, 25.50
PIN_FIELD_H = 17.00                       # FarthestPinTotal
BOARD_T = 1.60

# ----------------------------------------------------- the object
FACE_W = 237.0
BASE_H, BASE_D, LEAN = 56.0, 104.0, 12.0
GAP = 6.0                                  # air under the tubes
TY = BASE_H + GAP                          # tube bottom
TZ = 0.0                                   # glass front face
BZ = TZ + ENV_D                            # board front face
FIELD_CY = TY + ENV_H / 2.0                # pin field centre

# ИН-17 is NOT modelled — envelope stays the single-sample caliper reading
S17_W, S17_H, S17_D = 15.0, 20.0, 20.0

TUBES = [(24.5, ENV_W, ENV_H, "2"), (49.5, ENV_W, ENV_H, "3"),
         (81.5, ENV_W, ENV_H, "1"), (106.5, ENV_W, ENV_H, "9"),
         (137.0, S17_W, S17_H, "0"), (155.0, S17_W, S17_H, "4"),
         (189.5, ENV_W, ENV_H, "A"), (212.5, ENV_W, ENV_H, "Р")]

# four groups, and the spine that would carry each
GROUPS = [(12.0, 62.0), (69.0, 119.0), (127.0, 165.0), (178.0, 224.0)]

STUDIO = {"top": 1.06, "front": .82, "right": .60, "left": .46,
          "back": .40, "bottom": .30}


def plate_x(sc, x0, y0, z0, w, h, d, base, n=None, sw=.4, stroke="#123D26"):
    """A wide thin plate, emitted as vertical slices.

    The painter's algorithm sorts one polygon by ONE depth, so a board that
    spans the whole row averages to a single value and lands in front of the
    tubes at one end of it. Slicing along x gives every segment its own depth
    and the ordering comes out right from any camera.
    """
    n = n or max(2, int(w / 6.0))
    step = w / n
    for i in range(n):
        seg = raked(x0 + i * step, y0, z0, step * 1.02, h, d)
        for name, pts in seg.items():
            if name in ("bottom", "left", "right"):
                continue
            sc.poly(pts, mix(base, STUDIO[name]), stroke, sw)


def shell(sc, faces, base, skip=("bottom",), sw=.7, mult=1.0):
    for name, pts in faces.items():
        if name in skip:
            continue
        sc.poly(pts, mix(base, STUDIO[name] * mult), STROKE, sw)


def base_block(sc):
    shell(sc, raked(0, 0, 0, FACE_W, BASE_H, BASE_D, LEAN), CASE_T)

    def fpt(xx, yy):
        return (xx, yy, LEAN * (yy / BASE_H))
    sc.begin_group()
    sc.poly([fpt(2, 2), fpt(FACE_W - 2, 2), fpt(FACE_W - 2, 54), fpt(2, 54)],
            "#191D21", "#4E545C", .9, bias=-3)
    kx, ky = 46.0, 28.0
    for i in range(6):
        a = math.radians(-80 + i * 32)
        p1 = fpt(kx + math.sin(a) * 15.0, ky + math.cos(a) * 15.0)
        p2 = fpt(kx + math.sin(a) * 19.0, ky + math.cos(a) * 19.0)
        sc.poly([p1, p2, (p2[0] + 1.4, p2[1], p2[2]), (p1[0] + 1.4, p1[1], p1[2])],
                ACC_T if i == 0 else "#BFB9AE", bias=-7)
    disc(sc, fpt, kx, ky, 9.5, "#343A42", "#79818B", .9)
    sc.poly([fpt(kx - .9, ky + 2), fpt(kx + .9, ky + 2),
             fpt(kx + .9, ky + 8), fpt(kx - .9, ky + 8)], ACC_T, bias=-9)
    for lx in (134, 154):
        sc.poly([fpt(lx - 2.2, ky - 7), fpt(lx + 2.2, ky - 7),
                 fpt(lx + 2.2, ky + 7), fpt(lx - 2.2, ky + 7)],
                "#343A42", "#79818B", .8, bias=-7)
    for bx in (194, 214):
        disc(sc, fpt, bx, ky, 4.4, "#343A42", "#79818B", .8)
    sc.text_on_face((FACE_W - 12, 6, LEAN * (6 / BASE_H) - .4), (1, 0, 0), (0, 1, 0),
                    "TERMINAL·06", 7.5, "#8E948C", anchor="end", weight="600",
                    family=MONO, depth_bias=-4)
    sc.end_group(-1e6)


def tube_row(sc, pid):
    """Every tube, glass forward, hanging in space — the board holds it."""
    for (cx, w, h, ch) in TUBES:
        x0 = cx - w / 2.0
        d = ENV_D if w == ENV_W else S17_D
        can = raked(x0, TY, TZ, w, h, d)
        for name, pts in can.items():
            if name in ("bottom", "front"):
                continue
            sc.poly(pts, mix("#39434B", STUDIO[name]), STROKE, .5)
        glyphs = "0123456789" if ch.isdigit() else ch
        frag = T.tube_face(pid, w, h, ch, ghosts=ch.isdigit(), glyphset=glyphs,
                           warm=WARM, hot=HOT, deep=DEEP,
                           digit_frac=18.63 / ENV_H if w == ENV_W else .70,
                           ghost_op=.07, spec_op=.7, mesh_op=.34, socket=False)
        frag_on_face(sc, (x0, TY + h, TZ - .3), frag, depth_bias=-9)
    # colon
    for yy in (FIELD_CY - 5.5, FIELD_CY + 1.5):
        m, dz = sc.face_matrix((63.5, yy + 3.4, TZ - .6), (1, 0, 0), (0, -1, 0))
        sc.items.append((dz - 9, '<g transform="%s">%s</g>'
                         % (m, T.neon_dot(pid, 2.0, 1.7, 1.7, True, DEEP, WARM))))


def caption(sc, pt, txt, dx=8.0, dy=0.0, size=5.4, col="#8B939C", anchor="start"):
    x, y, _ = sc.p2(pt)
    tx, ty = x + dx, y + dy
    run = len(txt) * size * 0.56
    sc.pts.append((tx + (run if anchor == "start" else -run), ty))
    sc.pts.append((tx, ty - size))
    sc.items.append((-1e7, '<text x="%.2f" y="%.2f" font-family="%s" font-size="%.2f" '
                     'fill="%s" text-anchor="%s" letter-spacing=".4">%s</text>'
                     % (tx, ty, MONO, size, col, anchor, txt)))


# ==================================================== A — the rail
def variant_rail():
    pid = "va"
    sc = Scene(yaw=32, pitch=9, scale=2.75)
    base_block(sc)

    rail_h = PIN_FIELD_H + 3.0                     # 20, just covers the field
    ry = FIELD_CY - rail_h / 2.0
    # two end brackets carry it off the base
    for bx in (6.0, FACE_W - 6.0 - 5.0):
        shell(sc, raked(bx, BASE_H, BZ - 4.0, 5.0, ry + rail_h - BASE_H, 26.0),
              CASE_T, skip=("bottom",), sw=.5)
    # the rail itself, sliced so it sorts behind every tube
    plate_x(sc, 4.0, ry, BZ, FACE_W - 8.0, rail_h, BOARD_T, PCB)
    tube_row(sc, pid)

    caption(sc, (FACE_W, ry + rail_h, BZ + BOARD_T),
            "RAIL — one board, %g × %g, hidden behind the glass" % (FACE_W - 8, rail_h),
            col="#8FBFA4")
    caption(sc, (FACE_W, TY, TZ), "%g mm of air under the row" % GAP, dy=8)
    return sc.render(defs=night_defs(pid, WARM, DEEP), pad=40)


# ==================================================== B — spines
def variant_spines():
    pid = "vb"
    sc = Scene(yaw=32, pitch=9, scale=2.75)
    base_block(sc)

    top = TY + ENV_H + 3.0
    for (gx0, gx1) in GROUPS:
        plate_x(sc, gx0, BASE_H, BZ, gx1 - gx0, top - BASE_H, BOARD_T, PCB)
        # a foot into the base so it is obviously carried, not floating
        shell(sc, raked((gx0 + gx1) / 2 - 6, BASE_H - 1, BZ - 3.0, 12.0, 3.0, 8.0),
              CASE_T, skip=("bottom",), sw=.4)
    tube_row(sc, pid)

    caption(sc, (FACE_W, top, BZ + BOARD_T),
            "SPINES — four boards, one per group", col="#8FBFA4")
    caption(sc, (FACE_W, TY, TZ), "the gaps become real voids", dy=8)
    return sc.render(defs=night_defs(pid, WARM, DEEP), pad=40)


# ==================================================== the section, both
def variant_section():
    W, H = 300.0, 150.0
    o = [f'<rect x="0" y="0" width="{W}" height="{H}" fill="#0B0D10"/>']
    o.append(f'<text x="{W/2:.1f}" y="12" font-family="{COND}" font-size="6.4" '
             f'fill="#E4E1DA" text-anchor="middle" font-weight="700" '
             f'letter-spacing=".6">RIGHT SECTION — BOTH VARIANTS, 1:1</text>')
    o.append(f'<text x="{W/2:.1f}" y="18.5" font-family="{MONO}" font-size="3.2" '
             f'fill="#6B737B" text-anchor="middle">direct-solder · board front face '
             f'{ENV_D} behind the glass · no socket seat in this stack</text>')

    def block(ox, title, sub, rail):
        GY = 122.0
        p = []
        p.append(f'<text x="{ox+52:.1f}" y="30" font-family="{COND}" font-size="4.4" '
                 f'fill="#8FBFA4" text-anchor="middle" font-weight="700">{title}</text>')
        # base, raked front
        p.append(f'<polygon points="{ox:.1f},{GY:.1f} {ox+BASE_D:.1f},{GY:.1f} '
                 f'{ox+BASE_D:.1f},{GY-BASE_H:.1f} {ox+LEAN:.1f},{GY-BASE_H:.1f}" '
                 f'fill="#20242A" stroke="#3C444C" stroke-width=".6"/>')
        ty = GY - TY - ENV_H
        # tube
        p.append(f'<rect x="{ox:.1f}" y="{ty:.1f}" width="{ENV_D}" height="{ENV_H}" '
                 f'rx="1.2" fill="#1B2026" stroke="#5C6771" stroke-width=".6"/>')
        p.append(f'<rect x="{ox:.1f}" y="{ty:.1f}" width="2" height="{ENV_H}" '
                 f'fill="{WARM}" opacity=".3"/>')
        bxx = ox + ENV_D
        if rail:
            rh = PIN_FIELD_H + 3.0
            p.append(f'<rect x="{bxx:.1f}" y="{GY-FIELD_CY-rh/2:.1f}" '
                     f'width="{BOARD_T}" height="{rh}" fill="{PCB}" stroke="{PCB_HI}" '
                     f'stroke-width=".4"/>')
            p.append(f'<rect x="{bxx+BOARD_T:.1f}" y="{GY-FIELD_CY-rh/2:.1f}" width="4" '
                     f'height="{GY-BASE_H-(GY-FIELD_CY-rh/2):.1f}" fill="#262B31" '
                     f'stroke="#3C444C" stroke-width=".4" opacity=".8"/>')
            p.append(f'<text x="{bxx+7:.1f}" y="{GY-FIELD_CY:.1f}" font-family="{MONO}" '
                     f'font-size="3.0" fill="#8FBFA4">rail, {rh:g} tall</text>')
            p.append(f'<text x="{bxx+7:.1f}" y="{GY-FIELD_CY+4:.1f}" font-family="{MONO}" '
                     f'font-size="2.7" fill="#5A6169">end brackets carry it</text>')
        else:
            p.append(f'<rect x="{bxx:.1f}" y="{ty-3:.1f}" width="{BOARD_T}" '
                     f'height="{ENV_H+3+GAP:.1f}" fill="{PCB}" stroke="{PCB_HI}" '
                     f'stroke-width=".4"/>')
            p.append(f'<text x="{bxx+7:.1f}" y="{ty+8:.1f}" font-family="{MONO}" '
                     f'font-size="3.0" fill="#8FBFA4">spine, full height</text>')
            p.append(f'<text x="{bxx+7:.1f}" y="{ty+12:.1f}" font-family="{MONO}" '
                     f'font-size="2.7" fill="#5A6169">stands on the base</text>')
        # pins
        for i in range(5):
            yy = GY - FIELD_CY - 8 + i * 4
            p.append(f'<line x1="{bxx-0.3:.1f}" y1="{yy:.1f}" x2="{bxx+BOARD_T:.1f}" '
                     f'y2="{yy:.1f}" stroke="#9AA6B0" stroke-width=".45"/>')
        p.append(f'<text x="{ox+52:.1f}" y="{GY+9:.1f}" font-family="{MONO}" '
                 f'font-size="3.0" fill="#8B939C" text-anchor="middle">{sub}</text>')
        p.append(f'<line x1="{ox-4:.1f}" y1="{GY:.1f}" x2="{ox+110:.1f}" y2="{GY:.1f}" '
                 f'stroke="#3A4149" stroke-width=".5"/>')
        return p

    o += block(20.0, "A — RAIL", "tubes hide the board", True)
    o += block(168.0, "B — SPINES", "board reads as structure", False)
    o.append(f'<text x="{W/2:.1f}" y="{144:.1f}" font-family="{MONO}" font-size="3.0" '
             f'fill="#DFBB5E" text-anchor="middle">ИН-17 is not modelled — its 15 × 20 '
             f'envelope is still a single-sample caliper reading</text>')

    defs = '<defs>' + T.tube_defs("vs", warm=WARM, deep=DEEP) + '</defs>'
    return ('<svg preserveAspectRatio="xMidYMid meet" viewBox="0 0 %.1f %.1f" '
            'xmlns="http://www.w3.org/2000/svg" role="img">%s\n%s</svg>'
            % (W, H, defs, "\n".join(o)))


def main():
    for name, s in (("v-rail.svg", variant_rail()),
                    ("v-spines.svg", variant_spines()),
                    ("v-section.svg", variant_section())):
        with open(os.path.join(OUT, name), "w") as f:
            f.write(s)
        print(name, len(s))


if __name__ == "__main__":
    main()
