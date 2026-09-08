#!/usr/bin/env python3
"""Night heroes + rear three-quarter views for the -06 family.

Third script in the toolkit. Where render.py draws the daylight axonometric
(case reads as an object, tubes are a hint) this one inverts the lighting:
the tubes are the only light source in the room, everything else is what
they happen to fall on.

Two things make these different from render.py's heroes:

  1. The tubes are real `tubes.tube_face()` renders - glass, anode mesh,
     unlit ghost cathodes, four-layer glow - mapped onto the axonometric
     face with the same matrix trick text_on_face uses, instead of a flat
     text glyph. Elevation quality, in 3/4.
  2. Light is propagated by hand: a warm pool on the table, spill on every
     horizontal surface near the tubes, and a cool rim on the top edges so
     the case doesn't dissolve into the background.

Run: python3 render3.py    ->  n-*.svg
"""
import math, os

import tubes as T
from render import (Scene, raked, proj, mix, disc, glow_defs, F57,
                    STROKE,
                    CASE_T, ACC_T, GLOW_T, CASE_M, ACC_M, GLOW_M, VFD_M,
                    CASE_Q, ACC_Q, GLOW_Q, CASE_S, ACC_S, GLOW_S,
                    T_W, T_H, T_D, T_LEAN, T_PW, T_PH, T_PD, T_PX, T_PZ,
                    T_DECK, T_TUBES,
                    M_W, M_H, M_D, M_LEAN, M_PW, M_PH, M_PD, M_PX, M_PZ,
                    M_DECK, M_TUBES,
                    Q_W, Q_H, Q_D, Q_LEAN, Q_PITCH_X, Q_PITCH_Y,
                    Q_FACE_W, Q_FACE_H, Q_CX, Q_CY, Q_DIGITS,
                    S_W, S_H, S_D, S_BEZEL_CY, S_BEZEL_R)

OUT = os.path.dirname(os.path.abspath(__file__))

# In a dark room the case is lit only by the tubes, so every surface colour
# is the daylight colour knocked down hard and warmed slightly toward the
# glow. NIGHT is the multiplier; WARMTH is how much glow bleeds into it.
NIGHT = 0.30


def night(col, k=1.0, warm=None, warmth=0.0):
    """Darken `col` to night level, optionally bleeding `warm` into it."""
    base = mix(col, NIGHT * k)
    if not warm or warmth <= 0:
        return base
    a = base.lstrip("#"); b = warm.lstrip("#")
    out = []
    for i in (0, 2, 4):
        ca, cb = int(a[i:i + 2], 16), int(b[i:i + 2], 16)
        out.append(min(255, int(ca * (1 - warmth) + cb * warmth)))
    return "#%02x%02x%02x" % tuple(out)


# ------------------------------------------------------------------ helpers
def frag_on_face(sc, origin, frag, depth_bias=-8, sx=1.0, sy=1.0):
    """Drop a y-down local-mm fragment onto a front-facing plane.

    `origin` is the world point the fragment's top-left corner lands on.
    Local +x runs world +X, local +y runs world -Y, both 1 mm per unit,
    which is exactly the frame tubes.tube_face() is authored in.

    The -sy is load-bearing: the world is y-up and every tube_face()
    fragment is y-down. Feed face_matrix a +y vector here and every glyph
    comes out vertically mirrored - A renders as a passable upside-down A
    and it is not obvious until you look at a 4.
    """
    m, dz = sc.face_matrix(origin, (sx, 0, 0), (0, -sy, 0))
    sc.items.append((dz + depth_bias, '<g transform="%s">%s</g>' % (m, frag)))


def spill(sc, face, warm, op=0.20, pid="n", bias=-2.0):
    """Warm light falling on a horizontal surface."""
    sc.poly(list(face), warm, extra=' opacity="%.2f" filter="url(#%s-blur8)"' % (op, pid),
            bias=bias)


def rim(sc, face, col="#8FA8BD", op=0.30, sw=0.6, bias=-1.0):
    """Cool edge highlight so the silhouette survives the darkness."""
    sc.poly(list(face), "none", col, sw, extra=' opacity="%.2f"' % op, bias=bias)


def table(sc, cx, cz, rx, rz, pid, warm, glow_x=None, glow_r=1.0):
    """Ground plane: contact shadow + the pool of light the tubes throw."""
    gx = cx if glow_x is None else glow_x
    # contact shadow, tight and dark
    n = 26
    pts = [(cx + math.cos(2 * math.pi * i / n) * rx * .62,
            0.0,
            cz + math.sin(2 * math.pi * i / n) * rz * .62) for i in range(n)]
    sc.poly(pts, "#000000", extra=' opacity=".55" filter="url(#%s-blur8)"' % pid, bias=6000)
    # warm pool, wide and soft
    pts = [(gx + math.cos(2 * math.pi * i / n) * rx * glow_r,
            0.0,
            cz + math.sin(2 * math.pi * i / n) * rz * glow_r) for i in range(n)]
    sc.poly(pts, "url(#%s-pool)" % pid,
            extra=' filter="url(#%s-blur8)"' % pid, bias=6200)


def night_defs(pid, warm, deep, cool="#6FA0C8"):
    return ('<defs>' + T.tube_defs(pid, warm=warm, deep=deep) + f'''
<radialGradient id="{pid}-pool" cx=".5" cy=".5" r=".5">
  <stop offset="0"   stop-color="{warm}" stop-opacity=".38"/>
  <stop offset=".40" stop-color="{deep}" stop-opacity=".16"/>
  <stop offset="1"   stop-color="{deep}" stop-opacity="0"/>
</radialGradient>
<radialGradient id="{pid}-air" cx=".5" cy=".5" r=".5">
  <stop offset="0"   stop-color="{warm}" stop-opacity=".13"/>
  <stop offset=".55" stop-color="{warm}" stop-opacity=".04"/>
  <stop offset="1"   stop-color="{warm}" stop-opacity="0"/>
</radialGradient>
<linearGradient id="{pid}-rim" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="{cool}" stop-opacity=".05"/>
  <stop offset=".5" stop-color="{cool}" stop-opacity=".40"/>
  <stop offset="1" stop-color="{cool}" stop-opacity=".05"/>
</linearGradient>
</defs>''')


# ================================================================= TERMINAL
def terminal_night():
    pid = "nt"
    sc = Scene(yaw=34, pitch=7, scale=2.9)
    warm, deep, hot = GLOW_T, "#FF5A08", "#FFE0BC"

    table(sc, T_W / 2, T_D / 2, T_W * .70, T_D * .85, pid, warm,
          glow_x=T_W / 2, glow_r=1.05)

    body = raked(0, 0, 0, T_W, T_H, T_D, T_LEAN)
    for name, pts in body.items():
        if name == "bottom":
            continue
        k = {"top": 1.20, "front": .78, "right": .52, "left": .38, "back": .30}[name]
        w = .22 if name == "top" else (.10 if name == "front" else .04)
        sc.poly(pts, night(CASE_T, k, warm, w), night(STROKE, 1.6), 0.7)
    rim(sc, body["top"], "url(#%s-rim)" % pid, .55, .8, bias=-1)

    # fascia: almost entirely dark, only the selected detent and the wordmark
    def fpt(xx, yy):
        return (xx, yy, T_LEAN * (yy / T_H))
    sc.begin_group()
    sc.poly([fpt(2, 2), fpt(T_W - 2, 2), fpt(T_W - 2, 54), fpt(2, 54)],
            "#0B0D10", "#242A31", 0.7, bias=-3)
    kx, ky = 46.0, 28.0
    for i in range(6):
        a = math.radians(-80 + i * 32)
        p1, p2 = fpt(kx + math.sin(a) * 15.0, ky + math.cos(a) * 15.0), \
                 fpt(kx + math.sin(a) * 19.0, ky + math.cos(a) * 19.0)
        sc.poly([p1, p2, (p2[0] + 1.4, p2[1], p2[2]), (p1[0] + 1.4, p1[1], p1[2])],
                ACC_T if i == 0 else "#3A3F45",
                extra=' filter="url(#%s-softglow)"' % pid if i == 0 else "", bias=-7)
    disc(sc, fpt, kx, ky, 9.5, "#1A1E23", "#3C434B", 0.7)
    sc.poly([fpt(kx - .9, ky + 2), fpt(kx + .9, ky + 2), fpt(kx + .9, ky + 8), fpt(kx - .9, ky + 8)],
            ACC_T, bias=-9)
    sc.text_on_face((T_W - 12, 6, T_LEAN * (6 / T_H) - .4), (1, 0, 0), (0, 1, 0),
                    "TERMINAL·06", 7.5, "#4A5058", anchor="end", weight="600",
                    family="IBM Plex Mono, monospace", depth_bias=-4)
    for lx in (134, 154):
        sc.poly([fpt(lx - 2.2, ky - 7), fpt(lx + 2.2, ky - 7),
                 fpt(lx + 2.2, ky + 7), fpt(lx - 2.2, ky + 7)],
                "#1A1E23", "#3C434B", 0.6, bias=-7)
    for bx in (194, 214):
        disc(sc, fpt, bx, ky, 4.4, "#1A1E23", "#3C434B", 0.6)
    sc.end_group(-1e6)

    # plinth, with the tubes' light pooling on its top surface
    pl = raked(T_PX, T_H, T_PZ, T_PW, T_PH, T_PD)
    for name, pts in pl.items():
        if name in ("bottom", "back"):
            continue
        k = {"top": 1.15, "front": .66, "right": .44, "left": .32}[name]
        w = .16 if name == "top" else .06
        sc.poly(pts, night(CASE_T, k, warm, w), night(STROKE, 1.6), 0.7)
    spill(sc, pl["top"], warm, .46, pid, bias=-2)

    # the tubes themselves
    z0 = T_PZ + T_PD / 2.0 - 7.0
    for (cx, w, h, ch) in T_TUBES:
        x0 = cx - w / 2.0
        can = raked(x0, T_DECK, z0, w, h, 14.0)
        for name, pts in can.items():
            if name in ("bottom", "front"):
                continue
            k = {"top": .62, "right": .34, "left": .26, "back": .20}[name]
            sc.poly(pts, night("#39434B", k, warm, .07), night(STROKE, 1.9), 0.5)
        # airglow around the envelope
        sc.poly([(x0 - 7, T_DECK - 3, z0 + .6), (x0 + w + 7, T_DECK - 3, z0 + .6),
                 (x0 + w + 7, T_DECK + h + 7, z0 + .6), (x0 - 7, T_DECK + h + 7, z0 + .6)],
                "url(#%s-air)" % pid,
                extra=' filter="url(#%s-blur8)"' % pid, bias=2.5)
        glyphs = "0123456789" if ch.isdigit() else ch
        frag = T.tube_face(pid, w, h, ch, ghosts=ch.isdigit(), glyphset=glyphs,
                           warm=warm, hot=hot, deep=deep,
                           digit_frac=.68, ghost_op=.055, spec_op=.55, mesh_op=.30)
        frag_on_face(sc, (x0, T_DECK + h, z0 - .35), frag, depth_bias=-9)

    # colon
    for yy in (T_DECK + 8, T_DECK + 15):
        m, dz = sc.face_matrix((63.5, yy + 3.4, z0 - .6), (1, 0, 0), (0, -1, 0))
        sc.items.append((dz - 9, '<g transform="%s">%s</g>'
                         % (m, T.neon_dot(pid, 2.0, 1.7, 1.7, True, deep, warm))))
    # "m" stencil, backlit on the deck front edge
    sc.text_on_face((201, T_H + 5, T_PZ - 0.4), (1, 0, 0), (0, 1, 0), "m", 9, warm,
                    weight="600", extra=' filter="url(#%s-softglow)"' % pid, depth_bias=-8)
    return sc.render(defs=night_defs(pid, warm, deep), pad=44)


def terminal_rear34():
    """Back three-quarter. This is the view that actually answers the case
    question - how far the tubes stand clear of the deck, and how little of
    the glass the body hides now the plinth is inboard."""
    pid = "rt"
    sc = Scene(yaw=-148, pitch=14, scale=2.7)
    warm, deep, hot = GLOW_T, "#FF5A08", "#FFE0BC"

    table(sc, T_W / 2, T_D / 2, T_W * .68, T_D * .84, pid, warm, glow_r=1.0)

    body = raked(0, 0, 0, T_W, T_H, T_D, T_LEAN)
    for name, pts in body.items():
        if name == "bottom":
            continue
        k = {"top": 1.25, "back": .80, "left": .58, "right": .40, "front": .30}[name]
        sc.poly(pts, night(CASE_T, k, warm, .06), night(STROKE, 1.6), 0.7)
    rim(sc, body["top"], "url(#%s-rim)" % pid, .50, .8, bias=-1)

    # rear panel furniture, on the back face (z = T_D)
    def bpt(xx, yy):
        return (T_W - xx, yy, T_D + .35)
    sc.begin_group()
    sc.poly([bpt(6, 4), bpt(T_W - 6, 4), bpt(T_W - 6, T_H - 4), bpt(6, T_H - 4)],
            "#101317", "#2B3138", 0.7, bias=-3)
    # DC inlet
    disc(sc, bpt, 30, 28, 7.0, "#080A0C", "#3E454D", 0.8)
    disc(sc, bpt, 30, 28, 2.6, "#22282E", "#4A525B", 0.5)
    sc.text_on_face((T_W - 30, 41, T_D + .5), (-1, 0, 0), (0, 1, 0), "24 V", 4.0,
                    "#5A626B", family="IBM Plex Mono, monospace", depth_bias=-6)
    # service USB
    sc.poly([bpt(62, 25), bpt(78, 25), bpt(78, 31), bpt(62, 31)],
            "#080A0C", "#3E454D", 0.6, bias=-5)
    sc.text_on_face((T_W - 70, 41, T_D + .5), (-1, 0, 0), (0, 1, 0), "SERVICE", 4.0,
                    "#5A626B", family="IBM Plex Mono, monospace", depth_bias=-6)
    # vent slots
    for i in range(9):
        x = 104 + i * 6.4
        sc.poly([bpt(x, 16), bpt(x + 3.2, 16), bpt(x + 3.2, 40), bpt(x, 40)],
                "#070909", bias=-5)
    # HV warning triangle - apex UP; the world is y-up, so the apex vertex
    # is the one with the LARGER y
    tx, ty = 198.0, 30.0
    sc.poly([bpt(tx, ty + 8), bpt(tx + 7.5, ty - 5), bpt(tx - 7.5, ty - 5)],
            "#171B1F", ACC_T, 0.9, bias=-6)
    sc.text_on_face((T_W - tx, ty + 1.0, T_D + .5), (-1, 0, 0), (0, 1, 0), "!", 7.0,
                    ACC_T, weight="700", depth_bias=-8)
    sc.text_on_face((T_W - tx, ty - 9.5, T_D + .5), (-1, 0, 0), (0, 1, 0), "185 V ⎓", 4.0,
                    ACC_T, family="IBM Plex Mono, monospace", depth_bias=-6)
    # serial plate, bottom left of the panel as seen by the reader
    sc.text_on_face((T_W - 22, 11.5, T_D + .5), (-1, 0, 0), (0, 1, 0),
                    "TS06 · UNIT 001", 3.8, "#454C54", anchor="start",
                    family="IBM Plex Mono, monospace", depth_bias=-6)
    sc.end_group(-1e6)

    pl = raked(T_PX, T_H, T_PZ, T_PW, T_PH, T_PD)
    for name, pts in pl.items():
        if name in ("bottom", "front"):
            continue
        k = {"top": 1.15, "back": .66, "left": .46, "right": .34}[name]
        sc.poly(pts, night(CASE_T, k, warm, .10), night(STROKE, 1.6), 0.7)
    spill(sc, pl["top"], warm, .40, pid, bias=-2)

    # tubes from behind: cans and their back-lit haze, no glyph faces
    z0 = T_PZ + T_PD / 2.0 - 7.0
    for (cx, w, h, ch) in T_TUBES:
        x0 = cx - w / 2.0
        can = raked(x0, T_DECK, z0, w, h, 14.0)
        for name, pts in can.items():
            if name in ("bottom", "front"):
                continue
            k = {"top": .50, "back": .34, "right": .24, "left": .20}[name]
            sc.poly(pts, night("#39434B", k, warm, .05), night(STROKE, 1.9), 0.5)
        # light leaking around the tube from the far side
        sc.poly([(x0 - 8, T_DECK - 4, z0 - 1.0), (x0 + w + 8, T_DECK - 4, z0 - 1.0),
                 (x0 + w + 8, T_DECK + h + 9, z0 - 1.0), (x0 - 8, T_DECK + h + 9, z0 - 1.0)],
                "url(#%s-air)" % pid,
                extra=' opacity="1.5" filter="url(#%s-blur8)"' % pid, bias=-1.5)
    return sc.render(defs=night_defs(pid, warm, deep), pad=44)


# ===================================================================== MIMI
def mimi_night():
    pid = "nm"
    sc = Scene(yaw=33, pitch=8, scale=2.15)
    warm, deep, hot = GLOW_M, "#FF6A10", "#FFE0BC"

    table(sc, M_W / 2, M_D / 2, M_W * .74, M_D * .86, pid, VFD_M, glow_r=1.02)

    body = raked(0, 0, 0, M_W, M_H, M_D, M_LEAN)
    for name, pts in body.items():
        if name == "bottom":
            continue
        k = {"top": 1.15, "front": .80, "right": .52, "left": .38, "back": .30}[name]
        w = .07 if name == "front" else .025
        sc.poly(pts, night(CASE_M, k, VFD_M, w), night(STROKE, 1.6), 0.7)
    rim(sc, body["top"], "url(#%s-rim)" % pid, .50, .8, bias=-1)

    def fpt(xx, yy):
        return (xx, yy, M_LEAN * (yy / M_H))
    sc.begin_group()
    # VFD window - the dominant light source on this product
    sc.poly([fpt(13, 68), fpt(163, 68), fpt(163, 94), fpt(13, 94)],
            "#03060A", "#16292C", 0.7, bias=-3)
    sc.poly([fpt(11, 66), fpt(165, 66), fpt(165, 96), fpt(11, 96)], VFD_M,
            extra=' opacity=".07" filter="url(#%s-blur8)"' % pid, bias=-2)
    MSG = "(^_^)  20:47 SUN"[:16].ljust(16)
    for i, ch in enumerate(MSG):
        g = F57.get(ch, F57[" "])
        for col in range(5):
            for row in range(7):
                on = (g[col] >> row) & 1
                x = 15.6 + i * 9.35 + col * 1.72
                y = 90.2 - row * 2.72
                q = [fpt(x, y), fpt(x + 1.45, y), fpt(x + 1.45, y + 1.45), fpt(x, y + 1.45)]
                if on:
                    sc.poly(q, VFD_M, extra=' opacity=".55" filter="url(#%s-midglow)"' % pid, bias=-6)
                    sc.poly(q, "#E4FFFA", extra=' opacity=".92"', bias=-7)
                else:
                    sc.poly(q, VFD_M, extra=' opacity=".045"', bias=-6)
    # lower fascia
    sc.poly([fpt(2, 6), fpt(M_W - 2, 6), fpt(M_W - 2, 58), fpt(2, 58)],
            "#0A0A12", "#221F30", 0.7, bias=-3)
    kx, ky = 42.0, 32.0
    disc(sc, fpt, kx, ky, 9.5, "#15141E", "#332F45", 0.7)
    sc.poly([fpt(kx - .9, ky + 2), fpt(kx + .9, ky + 2), fpt(kx + .9, ky + 8), fpt(kx - .9, ky + 8)],
            ACC_M, extra=' filter="url(#%s-softglow)"' % pid, bias=-9)
    for lx in (100, 120):
        sc.poly([fpt(lx - 2, ky - 7), fpt(lx + 2, ky - 7), fpt(lx + 2, ky + 7), fpt(lx - 2, ky + 7)],
                "#15141E", "#332F45", 0.6, bias=-7)
    for bx in (146, 164):
        disc(sc, fpt, bx, ky, 4.4, "#15141E", "#332F45", 0.6)
    sc.end_group(-1e6)

    pl = raked(M_PX, M_H, M_PZ, M_PW, M_PH, M_PD)
    for name, pts in pl.items():
        if name in ("bottom", "back"):
            continue
        k = {"top": 1.15, "front": .68, "right": .44, "left": .32}[name]
        sc.poly(pts, night(CASE_M, k, warm, .15 if name == "top" else .06),
                night(STROKE, 1.6), 0.7)
    spill(sc, pl["top"], warm, .46, pid, bias=-2)

    # cyberpunk ears, edge-lit magenta
    for ex in (0.0, M_W - 15.0):
        ez = M_PZ + M_PD - 16
        ear = raked(ex, M_H, ez, 15, 44, 20)
        for name, pts in ear.items():
            if name == "bottom":
                continue
            k = {"top": 1.0, "front": .60, "right": .42, "left": .32, "back": .26}[name]
            sc.poly(pts, night("#332F45", k, ACC_M, .10), night(STROKE, 1.6), 0.6)
        sc.poly([(ex + 4.5, M_H + 8, ez - 0.35), (ex + 7.5, M_H + 8, ez - 0.35),
                 (ex + 7.5, M_H + 40, ez - 0.35), (ex + 4.5, M_H + 40, ez - 0.35)],
                ACC_M, extra=' filter="url(#%s-softglow)"' % pid, bias=-30)
        sc.poly([(ex + 1, M_H + 4, ez - 0.5), (ex + 11, M_H + 4, ez - 0.5),
                 (ex + 11, M_H + 44, ez - 0.5), (ex + 1, M_H + 44, ez - 0.5)],
                ACC_M, extra=' opacity=".22" filter="url(#%s-blur8)"' % pid, bias=-28)

    z0 = M_PZ + M_PD / 2.0 - 7.0
    for (cx, w, h, ch) in M_TUBES:
        x0 = cx - w / 2.0
        can = raked(x0, M_DECK, z0, w, h, 14.0)
        for name, pts in can.items():
            if name in ("bottom", "front"):
                continue
            k = {"top": .62, "right": .34, "left": .26, "back": .20}[name]
            sc.poly(pts, night("#39434B", k, warm, .07), night(STROKE, 1.9), 0.5)
        sc.poly([(x0 - 7, M_DECK - 3, z0 + .6), (x0 + w + 7, M_DECK - 3, z0 + .6),
                 (x0 + w + 7, M_DECK + h + 7, z0 + .6), (x0 - 7, M_DECK + h + 7, z0 + .6)],
                "url(#%s-air)" % pid,
                extra=' filter="url(#%s-blur8)"' % pid, bias=2.5)
        frag = T.tube_face(pid, w, h, ch, ghosts=True,
                           warm=warm, hot=hot, deep=deep,
                           digit_frac=.68, ghost_op=.055, spec_op=.55, mesh_op=.30)
        frag_on_face(sc, (x0, M_DECK + h, z0 - .35), frag, depth_bias=-9)
    return sc.render(defs=night_defs(pid, warm, deep, cool=VFD_M), pad=44)


# ================================================================= QUADRANT
def quadrant_night():
    pid = "nq"
    sc = Scene(yaw=35, pitch=10, scale=4.7)
    warm, deep, hot = GLOW_Q, "#FF6A10", "#FFE0BC"

    table(sc, Q_W / 2, Q_D / 2, Q_W * .82, Q_D * .9, pid, warm, glow_r=1.15)

    body = raked(0, 0, 0, Q_W, Q_H, Q_D, Q_LEAN)
    for name, pts in body.items():
        if name == "bottom":
            continue
        k = {"top": 1.20, "front": .82, "right": .52, "left": .38, "back": .30}[name]
        sc.poly(pts, night(CASE_Q, k, warm, .14 if name == "front" else .05),
                night(STROKE, 1.6), 0.7)
    rim(sc, body["top"], "url(#%s-rim)" % pid, .55, .8, bias=-1)

    def fpt(xx, yy):
        return (xx, yy, Q_LEAN * (yy / Q_H) - 0.2)
    sc.begin_group()
    ww, wh = Q_PITCH_X + Q_FACE_W + 6, Q_PITCH_Y + Q_FACE_H + 6
    sc.poly([fpt(Q_CX - ww / 2, Q_CY - wh / 2), fpt(Q_CX + ww / 2, Q_CY - wh / 2),
             fpt(Q_CX + ww / 2, Q_CY + wh / 2), fpt(Q_CX - ww / 2, Q_CY + wh / 2)],
            "#03050A", "#333B43", 0.5, bias=-3)
    # the window throws light back onto the bezel around it
    sc.poly([fpt(Q_CX - ww / 2 - 6, Q_CY - wh / 2 - 6), fpt(Q_CX + ww / 2 + 6, Q_CY - wh / 2 - 6),
             fpt(Q_CX + ww / 2 + 6, Q_CY + wh / 2 + 6), fpt(Q_CX - ww / 2 - 6, Q_CY + wh / 2 + 6)],
            warm, extra=' opacity=".11" filter="url(#%s-blur8)"' % pid, bias=-2)
    k = 0
    for ry in (1, -1):
        for rx in (-1, 1):
            cx = Q_CX + rx * Q_PITCH_X / 2.0
            cy = Q_CY + ry * Q_PITCH_Y / 2.0
            frag = T.tube_face(pid, Q_FACE_W, Q_FACE_H, Q_DIGITS[k], ghosts=True,
                               warm=warm, hot=hot, deep=deep,
                               digit_frac=.74, ghost_op=.05, spec_op=.5,
                               mesh_op=.26, socket=False)
            zf = Q_LEAN * ((cy + Q_FACE_H / 2) / Q_H) - 0.75
            frag_on_face(sc, (cx - Q_FACE_W / 2, cy + Q_FACE_H / 2, zf), frag, depth_bias=-9)
            k += 1
    for dy in (-2.4, 2.4):
        disc(sc, fpt, Q_CX, Q_CY + dy, 1.15, warm,
             extra=' filter="url(#%s-softglow)"' % pid, n=12, bias=-9)
    sc.end_group(-1e6)

    sc.poly([(14, Q_H + .2, Q_LEAN + 14), (26, Q_H + .2, Q_LEAN + 14),
             (26, Q_H + .2, Q_LEAN + 26), (14, Q_H + .2, Q_LEAN + 26)],
            "#0F1215", "#2E343B", 0.5)
    sc.poly([(52, Q_H + .2, Q_LEAN + 17), (60, Q_H + .2, Q_LEAN + 17),
             (60, Q_H + .2, Q_LEAN + 25), (52, Q_H + .2, Q_LEAN + 25)],
            "#0F1215", ACC_Q, 0.5)
    return sc.render(defs=night_defs(pid, warm, deep, cool=ACC_Q), pad=40)


# =================================================================== SCALER
def scaler_night():
    pid = "ns"
    sc = Scene(yaw=30, pitch=8, scale=2.25)
    warm, deep = ACC_S, "#7B5CFF"
    nixwarm, nixdeep, nixhot = GLOW_S, "#FF6A10", "#FFE0BC"

    table(sc, S_W / 2, S_D / 2, S_W * .78, S_D * .86, pid, warm, glow_r=1.05)

    body = raked(0, 0, 0, S_W, S_H, S_D, 0.0)
    for name, pts in body.items():
        if name == "bottom":
            continue
        k = {"top": 1.10, "front": .82, "right": .50, "left": .36, "back": .28}[name]
        sc.poly(pts, night(CASE_S, k, warm, .05 if name == "front" else .02),
                night(STROKE, 1.6), 0.7)
    rim(sc, body["top"], "url(#%s-rim)" % pid, .45, .8, bias=-1)

    z = -0.3
    sc.begin_group()

    def pc(cx, cy, r, n, fill, stroke=None, sw=0.5, extra="", bias=-4.0):
        pts = [(cx + math.cos(2 * math.pi * i / n) * r,
                cy + math.sin(2 * math.pi * i / n) * r, z) for i in range(n)]
        sc.poly(pts, fill, stroke, sw, extra, bias=bias)

    # decatron: the glow ring is the whole character of this product at night
    pc(S_W / 2, S_BEZEL_CY, S_BEZEL_R + 9, 40, warm,
       extra=' opacity=".20" filter="url(#%s-blur8)"' % pid, bias=-2)
    pc(S_W / 2, S_BEZEL_CY, S_BEZEL_R, 40, night("#3A453D", 1.0, warm, .18), "#39424C", 0.8, bias=-3)
    pc(S_W / 2, S_BEZEL_CY, S_BEZEL_R - 5, 40, "#03040A", "#241F3A", 0.6, bias=-5)
    for i in range(10):
        a = math.radians(i * 36 - 90)
        cx = S_W / 2 + math.cos(a) * (S_BEZEL_R - 11)
        cy = S_BEZEL_CY - math.sin(a) * (S_BEZEL_R - 11)
        lit = (i == 3)
        trail = (i in (2, 1))          # the two cathodes it just came off
        if lit:
            pc(cx, cy, 5.4, 14, warm, extra=' opacity=".55" filter="url(#%s-bigglow)"' % pid, bias=-7)
            pc(cx, cy, 3.1, 14, warm, extra=' filter="url(#%s-midglow)"' % pid, bias=-8)
            pc(cx, cy, 1.5, 12, "#EDE6FF", extra=' opacity=".95"', bias=-9)
        elif trail:
            op = .30 if i == 2 else .12
            pc(cx, cy, 2.6, 12, warm,
               extra=' opacity="%.2f" filter="url(#%s-midglow)"' % (op, pid), bias=-8)
        else:
            pc(cx, cy, 2.4, 12, "#1A1630", bias=-8)

    # nixie rate strip - real tube faces
    sc.poly([(20, 70, z), (116, 70, z), (116, 94, z), (20, 94, z)],
            "#070B08", "#1E2822", 0.7, bias=-3)
    for i, ch in enumerate("0024"):
        x = 26 + i * 17
        frag = T.tube_face(pid, 12, 18, ch, ghosts=True,
                           warm=nixwarm, hot=nixhot, deep=nixdeep,
                           digit_frac=.72, ghost_op=.05, spec_op=.5, mesh_op=.26)
        frag_on_face(sc, (x, 91, z - .5), frag, depth_bias=-9)
        sc.poly([(x - 4, 69, z - .4), (x + 16, 69, z - .4),
                 (x + 16, 95, z - .4), (x - 4, 95, z - .4)],
                nixwarm, extra=' opacity=".14" filter="url(#%s-blur8)"' % pid, bias=-4)
    frag = T.tube_face(pid, 12, 18, "K", ghosts=False, glyphset="K",
                       warm=nixwarm, hot=nixhot, deep=nixdeep,
                       digit_frac=.68, spec_op=.5, mesh_op=.26)
    frag_on_face(sc, (96, 91, z - .5), frag, depth_bias=-9)

    # six-position mode selector, ENT selected
    kx, ky = 40.0, 38.0
    pc(kx, ky, 11, 24, "#141A16", "#333C36", 0.7, bias=-6)
    for i in range(6):
        a = math.radians(-80 + i * 32)
        r1, r2 = 13.0, 17.0
        sel = (i == 1)
        sc.poly([(kx + math.sin(a) * r1, ky + math.cos(a) * r1, z),
                 (kx + math.sin(a) * r2, ky + math.cos(a) * r2, z),
                 (kx + math.sin(a) * r2 + .7, ky + math.cos(a) * r2, z),
                 (kx + math.sin(a) * r1 + .9, ky + math.cos(a) * r1, z)],
                warm if sel else "#2A3330",
                extra=' filter="url(#%s-softglow)"' % pid if sel else "", bias=-7)
    # pointer at ENT
    ap = math.radians(-80 + 1 * 32)
    sc.poly([(kx + math.sin(ap) * 2, ky + math.cos(ap) * 2, z - .2),
             (kx + math.sin(ap) * 9.5, ky + math.cos(ap) * 9.5, z - .2),
             (kx + math.sin(ap) * 9.5 + .9, ky + math.cos(ap) * 9.5, z - .2),
             (kx + math.sin(ap) * 2 + .9, ky + math.cos(ap) * 2, z - .2)],
            warm, bias=-8)

    for jx in (108, 124):
        pc(jx, 38, 4.2, 16, "#0A0D08", "#2B342E", 0.5)
    pc(88, 38, 2.4, 12, "#0A0D08", "#2B342E", 0.4)
    for sxp in (7, S_W - 7):
        for syp in (7, S_H - 7):
            pc(sxp, syp, 2.6, 10, "#161B17", "#0E120F", 0.3)
    sc.end_group(-1e6)
    return sc.render(defs=night_defs(pid, warm, deep, cool=ACC_S), pad=44)


# ===================================================================== write
def main():
    files = {
        "n-terminal-night.svg": terminal_night(),
        "n-terminal-rear34.svg": terminal_rear34(),
        "n-mimi-night.svg": mimi_night(),
        "n-quadrant-night.svg": quadrant_night(),
        "n-scaler-night.svg": scaler_night(),
    }
    for name, s in files.items():
        with open(os.path.join(OUT, name), "w") as f:
            f.write(s)
        print(name, len(s))


if __name__ == "__main__":
    main()
