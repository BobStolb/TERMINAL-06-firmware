#!/usr/bin/env python3
"""TERMINAL-06 extended view set - the angles the hero and the GA sheet miss.

render.py  gives one 3/4 hero and a dimensioned GA.
render2.py gives the lit 1:1 elevation, the rear panel and a tube macro.
render3.py gives the night 3/4 and the night rear 3/4.

This adds the six that were still missing, all lit, all from the same
millimetre constants:

  n-terminal-left.svg      left three-quarter - the side the hero hides
  n-terminal-profile.svg   right profile - the 12 deg rake and how proud the glass sits
  n-terminal-plan.svg      top-down - plinth inset, tube pitch, the two gaps
  n-terminal-exploded.svg  four layers pulled apart on the vertical
  n-terminal-fascia.svg    fascia detail at x2.6 - dial, levers, buttons
  n-terminal-scale.svg     beside a phone and a mug, 1:1

Run: python3 render4.py
"""
import math, os

import tubes as T
from render import (Scene, raked, proj, mix, disc, SHADE, STROKE,
                    CASE_T, ACC_T, GLOW_T,
                    T_W, T_H, T_D, T_LEAN, T_PW, T_PH, T_PD, T_PX, T_PZ,
                    T_DECK, T_TUBES)
from render3 import frag_on_face, night_defs


def screen_label(sc, pt, txt, dx=8.0, dy=0.0, size=5.6, col="#8B939C",
                 anchor="start", family="IBM Plex Mono, monospace"):
    """Plain screen-space text anchored to a projected world point.

    text_on_face() maps type onto a *surface*, which is right for a wordmark
    silkscreened on a panel and wrong for a caption: on a horizontal plane it
    foreshortens into an unreadable smear. Captions want to face the reader.
    """
    x, y, _ = sc.p2(pt)
    tx, ty = x + dx, y + dy
    # Scene sizes its viewBox from sc.pts, which only ever sees geometry - so a
    # caption silently hangs off the edge. Register its far end as a point too.
    run = len(txt) * size * 0.56
    sc.pts.append((tx + (run if anchor == "start" else -run), ty))
    sc.pts.append((tx, ty - size))
    sc.items.append((-1e7, '<text x="%.2f" y="%.2f" font-family="%s" font-size="%.2f" '
                     'fill="%s" text-anchor="%s" letter-spacing=".4">%s</text>'
                     % (tx, ty, family, size, col, anchor, txt)))

OUT = os.path.dirname(os.path.abspath(__file__))

WARM, DEEP, HOT = GLOW_T, "#FF5A08", "#FFE0BC"
Z0 = T_PZ + T_PD / 2.0 - 7.0          # tube front face, shared by every view
MONO = "IBM Plex Mono, monospace"
COND = "IBM Plex Sans Condensed, Arial Narrow, sans-serif"

# Studio lighting: brighter than render3's night, matched to render.py's hero
# so this set and the existing plates sit together on one page.
STUDIO = {"top": 1.06, "front": .82, "right": .60, "left": .46,
          "back": .40, "bottom": .30}


def shell(sc, faces, base, mult=1.0, skip=("bottom",), sw=.7):
    for name, pts in faces.items():
        if name in skip:
            continue
        sc.poly(pts, mix(base, STUDIO[name] * mult), STROKE, sw)


def tube_stack(sc, pid, only=None, dim=1.0, faces=True):
    """Every tube on the deck, cans plus glass. `only` filters by index."""
    for i, (cx, w, h, ch) in enumerate(T_TUBES):
        if only is not None and i not in only:
            continue
        x0 = cx - w / 2.0
        can = raked(x0, T_DECK, Z0, w, h, 14.0)
        for name, pts in can.items():
            if name in ("bottom",) or (faces and name == "front"):
                continue
            sc.poly(pts, mix("#39434B", STUDIO[name]), STROKE, .55)
        if not faces:
            continue
        glyphs = "0123456789" if ch.isdigit() else ch
        frag = T.tube_face(pid, w, h, ch, ghosts=ch.isdigit(), glyphset=glyphs,
                           warm=WARM, hot=HOT, deep=DEEP, dim=dim,
                           digit_frac=.68, ghost_op=.07, spec_op=.7, mesh_op=.34)
        frag_on_face(sc, (x0, T_DECK + h, Z0 - .35), frag, depth_bias=-9)


def fascia_furniture(sc, fpt, label=True):
    """Dial arc, knob, levers, buttons - the Rev E front panel."""
    kx, ky = 46.0, 28.0
    for i in range(6):
        a = math.radians(-80 + i * 32)        # 32 deg/detent, measured
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


# ============================================================ LEFT 3/4
def terminal_left():
    pid = "lt"
    sc = Scene(yaw=-34, pitch=11, scale=2.75)
    shell(sc, raked(0, 0, 0, T_W, T_H, T_D, T_LEAN), CASE_T)

    def fpt(xx, yy):
        return (xx, yy, T_LEAN * (yy / T_H))
    sc.begin_group()
    sc.poly([fpt(2, 2), fpt(T_W - 2, 2), fpt(T_W - 2, 54), fpt(2, 54)],
            "#191D21", "#4E545C", .9, bias=-3)
    fascia_furniture(sc, fpt)
    sc.text_on_face((T_W - 12, 6, T_LEAN * (6 / T_H) - .4), (1, 0, 0), (0, 1, 0),
                    "TERMINAL·06", 7.5, "#8E948C", anchor="end", weight="600",
                    family=MONO, depth_bias=-4)
    sc.end_group(-1e6)

    shell(sc, raked(T_PX, T_H, T_PZ, T_PW, T_PH, T_PD), CASE_T,
          skip=("bottom", "back"))
    tube_stack(sc, pid)
    for yy in (T_DECK + 8, T_DECK + 15):
        m, dz = sc.face_matrix((63.5, yy + 3.4, Z0 - .6), (1, 0, 0), (0, -1, 0))
        sc.items.append((dz - 9, '<g transform="%s">%s</g>'
                         % (m, T.neon_dot(pid, 2.0, 1.7, 1.7, True, DEEP, WARM))))
    return sc.render(defs=night_defs(pid, WARM, DEEP), pad=34)


# ============================================================ RIGHT PROFILE
def terminal_profile():
    """Right side elevation, 1:1, orthographic.

    Deliberately NOT an axonometric: Scene's depth term is y*sin(pitch)+..., so
    at a steep camera angle "higher up" sorts as "further away" and the drawing
    inverts. A profile is a drawing anyway - this is the sheet that settles the
    case argument, because you can measure how far the glass stands clear.
    """
    pid = "pt"
    W, H = 268.0, 168.0
    OX, OY = 30.0, 116.0                 # origin: z=0 at OX, y=0 at OY (y up)

    def X(z): return OX + z
    def Y(y): return OY - y

    o = []
    o.append(f'<text x="{OX+T_D/2:.1f}" y="18" font-family="{COND}" font-size="7" '
             f'fill="#E4E1DA" text-anchor="middle" font-weight="700" '
             f'letter-spacing=".5">RIGHT PROFILE</text>')

    # base: front face leans back T_LEAN at the top
    o.append(f'<polygon points="{X(0):.1f},{Y(0):.1f} {X(T_D):.1f},{Y(0):.1f} '
             f'{X(T_D):.1f},{Y(T_H):.1f} {X(T_LEAN):.1f},{Y(T_H):.1f}" '
             f'fill="#23282E" stroke="#4A5058" stroke-width=".8"/>')
    # plinth
    o.append(f'<rect x="{X(T_PZ):.1f}" y="{Y(T_H+T_PH):.1f}" width="{T_PD}" '
             f'height="{T_PH}" fill="#2A2E34" stroke="#4A5058" stroke-width=".7"/>')
    # tubes, edge on - one silhouette, the row is all at the same z
    o.append(f'<rect x="{X(Z0):.1f}" y="{Y(T_DECK+24):.1f}" width="14" height="24" '
             f'fill="#39434B" stroke="#5C6771" stroke-width=".7" rx=".8"/>')
    o.append(f'<rect x="{X(Z0)+1.6:.1f}" y="{Y(T_DECK+22):.1f}" width="10.8" height="20" '
             f'fill="url(#{pid}-cavity)" opacity=".9" rx=".6"/>')
    o.append(f'<ellipse cx="{X(Z0)+7:.1f}" cy="{Y(T_DECK+12):.1f}" rx="16" ry="15" '
             f'fill="url(#{pid}-halo)" opacity=".55"/>')
    # seconds tube, 20 tall, shown ghosted behind to make the height split legible
    o.append(f'<rect x="{X(Z0):.1f}" y="{Y(T_DECK+20):.1f}" width="14" height="20" '
             f'fill="none" stroke="#5C6771" stroke-width=".5" stroke-dasharray="2.5 2" rx=".8"/>')

    def dimh(z1, z2, y, txt, side=1):
        yy = Y(y)
        o.append(f'<line x1="{X(z1):.1f}" y1="{yy:.1f}" x2="{X(z2):.1f}" y2="{yy:.1f}" '
                 f'stroke="#5E646C" stroke-width=".6"/>')
        for zz in (z1, z2):
            o.append(f'<line x1="{X(zz):.1f}" y1="{yy-3:.1f}" x2="{X(zz):.1f}" '
                     f'y2="{yy+3:.1f}" stroke="#5E646C" stroke-width=".6"/>')
        o.append(f'<text x="{X((z1+z2)/2):.1f}" y="{yy-2.6 if side>0 else yy+6:.1f}" '
                 f'font-family="{MONO}" font-size="5" fill="#8FA4B2" '
                 f'text-anchor="middle">{txt}</text>')

    def dimv(y1, y2, z, txt, anchor="start", dx=3.4):
        xx = X(z)
        o.append(f'<line x1="{xx:.1f}" y1="{Y(y1):.1f}" x2="{xx:.1f}" y2="{Y(y2):.1f}" '
                 f'stroke="#5E646C" stroke-width=".6"/>')
        for yy in (y1, y2):
            o.append(f'<line x1="{xx-3:.1f}" y1="{Y(yy):.1f}" x2="{xx+3:.1f}" '
                     f'y2="{Y(yy):.1f}" stroke="#5E646C" stroke-width=".6"/>')
        o.append(f'<text x="{xx+dx:.1f}" y="{Y((y1+y2)/2)+1.8:.1f}" font-family="{MONO}" '
                 f'font-size="5" fill="#8FA4B2" text-anchor="{anchor}">{txt}</text>')

    dimh(0, T_D, -10, "104 DEEP", side=-1)
    dimh(0, T_PZ, T_H + 24, "30 SETBACK")
    dimv(0, T_H, T_D + 14, "56")
    dimv(T_H, T_DECK, T_D + 14, "16")
    dimv(T_DECK, T_DECK + 24, T_D + 14, "24")
    dimv(0, T_DECK + 24, T_D + 44, "96 OVERALL")

    # the rake, called out where it actually is
    o.append(f'<line x1="{X(0):.1f}" y1="{Y(0):.1f}" x2="{X(0):.1f}" y2="{Y(T_H)-6:.1f}" '
             f'stroke="#5E646C" stroke-width=".5" stroke-dasharray="3 3"/>')
    o.append(f'<path d="M{X(0):.1f} {Y(T_H)-2:.1f} A 14 14 0 0 1 {X(T_LEAN)-.5:.1f} '
             f'{Y(T_H)-1:.1f}" fill="none" stroke="{ACC_T}" stroke-width=".7"/>')
    o.append(f'<text x="{X(0)-3:.1f}" y="{Y(T_H)-8:.1f}" font-family="{MONO}" font-size="5" '
             f'fill="{ACC_T}" text-anchor="end">12° RAKE</text>')

    # Tube legend lives in the empty bottom-left corner. Beside the tube it
    # collided with the height dimension stack, which is the one thing on this
    # sheet that must stay readable.
    LX, LY = 12.0, 148.0
    o.append(f'<rect x="{LX:.1f}" y="{LY-4.4:.1f}" width="8" height="4" fill="#39434B" '
             f'stroke="#5C6771" stroke-width=".6"/>')
    o.append(f'<text x="{LX+12:.1f}" y="{LY-1.1:.1f}" font-family="{MONO}" font-size="4.4" '
             f'fill="#8FA4B2">ИН-12А — 24 tall · hours and minutes</text>')
    o.append(f'<rect x="{LX:.1f}" y="{LY+3.4:.1f}" width="8" height="4" fill="none" '
             f'stroke="#5C6771" stroke-width=".5" stroke-dasharray="2 1.6"/>')
    o.append(f'<text x="{LX+12:.1f}" y="{LY+6.7:.1f}" font-family="{MONO}" font-size="4.4" '
             f'fill="#7E858D">ИН-17 — 20 tall · seconds, same 14 mm depth</text>')
    o.append(f'<line x1="{X(0)-6:.1f}" y1="{Y(0):.1f}" x2="{X(T_D)+52:.1f}" y2="{Y(0):.1f}" '
             f'stroke="#3A4149" stroke-width=".6"/>')

    body = "\n".join(o)
    defs = '<defs>' + T.tube_defs(pid, warm=WARM, deep=DEEP) + '</defs>'
    return ('<svg preserveAspectRatio="xMidYMid meet" viewBox="0 0 %.1f %.1f" '
            'xmlns="http://www.w3.org/2000/svg" role="img">%s\n%s</svg>'
            % (W, H, defs, body))


# ============================================================ PLAN
def terminal_plan():
    """Top-down, 1:1, orthographic. Plinth inset, tube pitch, and the two gaps
    that give the row its rhythm."""
    pid = "tp"
    W, H = 300.0, 190.0
    OX, OY = 30.0, 44.0                  # x=0 at OX, z=0 at OY (z runs down)

    def X(x): return OX + x
    def Z(z): return OY + z

    o = []
    o.append(f'<text x="{X(T_W/2):.1f}" y="20" font-family="{COND}" font-size="7" '
             f'fill="#E4E1DA" text-anchor="middle" font-weight="700" '
             f'letter-spacing=".5">PLAN</text>')
    o.append(f'<rect x="{X(0):.1f}" y="{Z(0):.1f}" width="{T_W}" height="{T_D}" '
             f'fill="#1A1F25" stroke="#3A4149" stroke-width=".8"/>')
    o.append(f'<rect x="{X(T_PX):.1f}" y="{Z(T_PZ):.1f}" width="{T_PW}" height="{T_PD}" '
             f'fill="#23282E" stroke="#4A5058" stroke-width=".7"/>')

    for (cx, w, h, ch) in T_TUBES:
        x0 = cx - w / 2.0
        o.append(f'<rect x="{X(x0):.1f}" y="{Z(Z0):.1f}" width="{w}" height="14" '
                 f'fill="#141C23" stroke="#8FA4B2" stroke-width=".5" rx=".6"/>')
        o.append(f'<rect x="{X(x0)+2:.1f}" y="{Z(Z0)+2:.1f}" width="{w-4}" height="4.5" '
                 f'fill="{WARM}" opacity=".5" filter="url(#{pid}-midglow)"/>')
    # colon
    for zz in (Z0 + 4, Z0 + 9):
        o.append(f'<circle cx="{X(65.5):.1f}" cy="{Z(zz):.1f}" r="1.7" fill="{WARM}" '
                 f'opacity=".8" filter="url(#{pid}-softglow)"/>')

    def dimh(x1, x2, z, txt):
        zz = Z(z)
        o.append(f'<line x1="{X(x1):.1f}" y1="{zz:.1f}" x2="{X(x2):.1f}" y2="{zz:.1f}" '
                 f'stroke="#5E646C" stroke-width=".6"/>')
        for xx in (x1, x2):
            o.append(f'<line x1="{X(xx):.1f}" y1="{zz-3:.1f}" x2="{X(xx):.1f}" '
                     f'y2="{zz+3:.1f}" stroke="#5E646C" stroke-width=".6"/>')
        o.append(f'<text x="{X((x1+x2)/2):.1f}" y="{zz-2.8:.1f}" font-family="{MONO}" '
                 f'font-size="5" fill="#8FA4B2" text-anchor="middle">{txt}</text>')

    dimh(0, T_W, -14, "237")
    dimh(T_PX, T_PX + T_PW, T_D + 22, "213 PLINTH")
    dimh(0, T_PX, T_D + 22, "12")
    dimh(T_PX + T_PW, T_W, T_D + 22, "12")
    dimh(24.5, 49.5, -4, "25 PITCH")
    dimh(122.5, 145.5, -4, "16 GAP")
    dimh(163.0, 189.5, -4, "AM/PM")

    o.append(f'<text x="{X(T_W/2):.1f}" y="{Z(T_D)+40:.1f}" font-family="{MONO}" '
             f'font-size="4.6" fill="#5A6169" text-anchor="middle" letter-spacing=".4">'
             f'TUBE ROW SPANS 13.5 → 223.5 · PLINTH SPANS 12 → 225 · NO OVERHANG</text>')

    body = "\n".join(o)
    defs = '<defs>' + T.tube_defs(pid, warm=WARM, deep=DEEP) + '</defs>'
    return ('<svg preserveAspectRatio="xMidYMid meet" viewBox="0 0 %.1f %.1f" '
            'xmlns="http://www.w3.org/2000/svg" role="img">%s\n%s</svg>'
            % (W, H, defs, body))


# ============================================================ EXPLODED
def terminal_exploded():
    """Four layers on the vertical. Deliberately not a service drawing - it is
    there so a buyer can see there is a real machine inside the box."""
    pid = "et"
    sc = Scene(yaw=30, pitch=15, scale=2.35)
    LIFT_TUBE, LIFT_PL, LIFT_PCB = 118.0, 74.0, 40.0

    # base shell, in place
    shell(sc, raked(0, 0, 0, T_W, T_H, T_D, T_LEAN), CASE_T)

    def fpt(xx, yy):
        return (xx, yy, T_LEAN * (yy / T_H))
    sc.begin_group()
    sc.poly([fpt(2, 2), fpt(T_W - 2, 2), fpt(T_W - 2, 54), fpt(2, 54)],
            "#191D21", "#4E545C", .9, bias=-3)
    fascia_furniture(sc, fpt)
    sc.end_group(-1e6)

    # main board
    pcb = raked(14, T_H + LIFT_PCB, 22, 209, 1.6, 62)
    shell(sc, pcb, "#1E5B3A", mult=1.0, skip=("bottom",), sw=.4)
    for (bx, bz, bw, bd, col) in ((26, 30, 42, 18, "#20262C"),   # Nano
                                  (78, 32, 20, 14, "#2B3138"),   # DS3231
                                  (108, 30, 26, 22, "#3A2F1E"),  # boost
                                  (148, 32, 46, 16, "#20262C")): # opto row
        sc.poly([(bx, T_H + LIFT_PCB + 1.7, bz), (bx + bw, T_H + LIFT_PCB + 1.7, bz),
                 (bx + bw, T_H + LIFT_PCB + 1.7, bz + bd), (bx, T_H + LIFT_PCB + 1.7, bz + bd)],
                col, "#0A0B0C", .35, bias=-3)
    screen_label(sc, (T_W, T_H + LIFT_PCB + 1, 52),
                 "MAIN BOARD — NANO · DS3231 · К155ИД1 · 4× TLP627", col="#8FBFA4")

    # plinth
    shell(sc, raked(T_PX, T_H + LIFT_PL, T_PZ, T_PW, T_PH, T_PD), CASE_T,
          skip=("bottom",))
    screen_label(sc, (T_W, T_H + LIFT_PL + T_PH, T_PZ + T_PD),
                 "PLINTH — 213 × 46, INSET 12 EACH SIDE")

    # tube deck
    for (cx, w, h, ch) in T_TUBES:
        x0 = cx - w / 2.0
        yb = T_DECK + LIFT_TUBE
        can = raked(x0, yb, Z0, w, h, 14.0)
        for name, pts in can.items():
            if name in ("bottom", "front"):
                continue
            sc.poly(pts, mix("#39434B", STUDIO[name]), STROKE, .55)
        glyphs = "0123456789" if ch.isdigit() else ch
        frag = T.tube_face(pid, w, h, ch, ghosts=ch.isdigit(), glyphset=glyphs,
                           warm=WARM, hot=HOT, deep=DEEP,
                           digit_frac=.68, ghost_op=.07, spec_op=.7, mesh_op=.34)
        frag_on_face(sc, (x0, yb + h, Z0 - .35), frag, depth_bias=-9)
    screen_label(sc, (T_W, T_DECK + LIFT_TUBE + 12, Z0 + 14),
                 "TUBE ROW — 4× ИН-12А · 2× ИН-17 · 2× ИН-15", col="#C8B49A")
    screen_label(sc, (T_W, 30, T_D), "BASE SHELL — 237 × 56 × 104, RAKED 12°")

    # dashed assembly axes
    for ax in (34.0, T_W - 34.0):
        sc.poly([(ax, T_H + 2, T_PZ + 20), (ax, T_DECK + LIFT_TUBE + 6, T_PZ + 20)],
                "none", "#4A5058", .5,
                extra=' stroke-dasharray="4 4"', bias=4000)
    return sc.render(defs=night_defs(pid, WARM, DEEP), pad=40)


# ============================================================ FASCIA MACRO
def terminal_fascia():
    """Flat detail of the left half of the fascia at x2.6. The rotary is drawn
    at the measured 32 deg/detent, 6 positions across ~160 deg."""
    S = 2.6
    W, H = 175.0, 80.0
    o = []
    o.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#12161A"/>')
    o.append(f'<rect x="3" y="3" width="{W-6}" height="{H-6}" fill="#191D21" '
             f'stroke="#4E545C" stroke-width=".6" rx="1.5"/>')
    kx, ky = 42.0, 34.0

    # detents + legend
    SCREENS = ["RUN", "TIME", "DISP", "AMB", "INFO", "DATE"]
    for i, nm in enumerate(SCREENS):
        a = math.radians(-80 + i * 32)
        s_, c_ = math.sin(a), -math.cos(a)          # y down on this sheet
        x1, y1 = kx + s_ * 15.0, ky + c_ * 15.0
        x2, y2 = kx + s_ * 19.0, ky + c_ * 19.0
        col = ACC_T if i == 0 else "#BFB9AE"
        o.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
                 f'stroke="{col}" stroke-width="1.3" stroke-linecap="round"/>')
        lx, ly = kx + s_ * 24.0, ky + c_ * 24.0
        anc = "middle" if abs(s_) < .12 else ("start" if s_ > 0 else "end")
        o.append(f'<text x="{lx:.2f}" y="{ly+1.1:.2f}" font-family="{MONO}" '
                 f'font-size="3.1" fill="{"#E4E1DA" if i==0 else "#7E858D"}" '
                 f'text-anchor="{anc}" letter-spacing=".4">{nm}</text>')
    o.append(f'<circle cx="{kx}" cy="{ky}" r="9.5" fill="#343A42" stroke="#79818B" stroke-width=".8"/>')
    o.append(f'<circle cx="{kx}" cy="{ky}" r="6.4" fill="none" stroke="#20252B" stroke-width=".5"/>')
    a0 = math.radians(-80)
    o.append(f'<line x1="{kx+math.sin(a0)*2.4:.2f}" y1="{ky-math.cos(a0)*2.4:.2f}" '
             f'x2="{kx+math.sin(a0)*8.4:.2f}" y2="{ky-math.cos(a0)*8.4:.2f}" '
             f'stroke="{ACC_T}" stroke-width="1.5" stroke-linecap="round"/>')
    o.append(f'<text x="{kx:.2f}" y="{ky+31:.2f}" font-family="{MONO}" font-size="2.9" '
             f'fill="#6B737B" text-anchor="middle" letter-spacing=".5">SR25 · 6 POS · 32°/STEP · ⌀26.94</text>')

    # levers
    for i, (lx, nm) in enumerate(((104, "SET"), (124, "ADJ"))):
        o.append(f'<rect x="{lx-4.6:.1f}" y="{ky-11:.1f}" width="9.2" height="22" rx="1.2" '
                 f'fill="#20252B" stroke="#79818B" stroke-width=".55"/>')
        o.append(f'<rect x="{lx-2.2:.1f}" y="{ky-9+(0 if i==0 else 10):.1f}" width="4.4" height="11" rx="1.6" '
                 f'fill="#59626B" stroke="#8E959D" stroke-width=".4"/>')
        o.append(f'<text x="{lx:.1f}" y="{ky+16:.1f}" font-family="{MONO}" font-size="2.9" '
                 f'fill="#7E858D" text-anchor="middle" letter-spacing=".4">{nm}</text>')
        o.append(f'<text x="{lx:.1f}" y="{ky-13.5:.1f}" font-family="{MONO}" font-size="2.4" '
                 f'fill="#5A6169" text-anchor="middle">МТ1</text>')
    # buttons
    for bx, nm in ((148, "▲"), (166, "▼")):
        o.append(f'<circle cx="{bx}" cy="{ky}" r="5.6" fill="#20252B" stroke="#79818B" stroke-width=".55"/>')
        o.append(f'<circle cx="{bx}" cy="{ky}" r="3.9" fill="url(#fc-btn)"/>')
        o.append(f'<text x="{bx}" y="{ky+1.2:.1f}" font-family="{COND}" font-size="3.4" '
                 f'fill="#9AA1A8" text-anchor="middle">{nm}</text>')
        o.append(f'<text x="{bx}" y="{ky+11:.1f}" font-family="{MONO}" font-size="2.4" '
                 f'fill="#5A6169" text-anchor="middle">КМД1</text>')
    o.append(f'<text x="8" y="{H-7:.1f}" font-family="{MONO}" font-size="3.0" fill="#5A6169" '
             f'letter-spacing=".4">FASCIA DETAIL — ×2.6 · МТ1 AND КМД1 BUSHINGS BOTH ⌀7.85</text>')

    body = "\n".join(o)
    defs = ('<defs>' + T.tube_defs("fc", warm=WARM, deep=DEEP) +
            '<radialGradient id="fc-btn" cx=".38" cy=".32" r=".8">'
            '<stop offset="0" stop-color="#4A525B"/><stop offset=".6" stop-color="#242A30"/>'
            '<stop offset="1" stop-color="#171B1F"/></radialGradient></defs>')
    return ('<svg preserveAspectRatio="xMidYMid meet" viewBox="0 0 %.1f %.1f" '
            'xmlns="http://www.w3.org/2000/svg" role="img">%s\n%s</svg>'
            % (W, H, defs, body))


# ============================================================ SCALE
def terminal_scale():
    """1:1 elevation beside two things everyone owns. For the listing - the
    single most asked question about a desk object is how big it is."""
    pid = "sc"
    W, H = 500.0, 194.0
    GY = 170.0                                   # ground line
    o = []
    o.append(f'<line x1="6" y1="{GY}" x2="{W-6}" y2="{GY}" stroke="#3A4149" stroke-width=".7"/>')

    # --- the clock, 237 x 96 overall
    cx0 = 14.0
    o.append(f'<rect x="{cx0}" y="{GY-56}" width="237" height="56" fill="#23282E" '
             f'stroke="#3A4149" stroke-width=".8" rx="1"/>')
    o.append(f'<rect x="{cx0+2}" y="{GY-54}" width="233" height="52" fill="#191D21" '
             f'stroke="#4E545C" stroke-width=".5"/>')
    o.append(f'<rect x="{cx0+T_PX}" y="{GY-72}" width="213" height="16" fill="#2A2E34" '
             f'stroke="#3A4149" stroke-width=".7"/>')
    for (tcx, tw, th, ch) in T_TUBES:
        x0 = cx0 + tcx - tw / 2.0
        frag = T.tube_face(pid, tw, th, ch, ghosts=ch.isdigit(),
                           glyphset="0123456789" if ch.isdigit() else ch,
                           warm=WARM, hot=HOT, deep=DEEP,
                           digit_frac=.68, ghost_op=.07, spec_op=.7, mesh_op=.34)
        o.append(f'<g transform="translate({x0:.2f} {GY-72-th:.2f})">{frag}</g>')
    # fascia furniture, so the silhouette reads as the product and not a slab
    fkx, fky = cx0 + 46.0, GY - 28.0
    for i in range(6):
        a = math.radians(-80 + i * 32)
        s_, c_ = math.sin(a), -math.cos(a)
        o.append(f'<line x1="{fkx+s_*15:.2f}" y1="{fky+c_*15:.2f}" '
                 f'x2="{fkx+s_*19:.2f}" y2="{fky+c_*19:.2f}" '
                 f'stroke="{ACC_T if i==0 else "#8B939C"}" stroke-width="1.2" stroke-linecap="round"/>')
    o.append(f'<circle cx="{fkx:.1f}" cy="{fky:.1f}" r="9.5" fill="#343A42" stroke="#79818B" stroke-width=".7"/>')
    a0 = math.radians(-80)
    o.append(f'<line x1="{fkx+math.sin(a0)*2:.2f}" y1="{fky-math.cos(a0)*2:.2f}" '
             f'x2="{fkx+math.sin(a0)*8:.2f}" y2="{fky-math.cos(a0)*8:.2f}" '
             f'stroke="{ACC_T}" stroke-width="1.4" stroke-linecap="round"/>')
    for lx in (134, 154):
        o.append(f'<rect x="{cx0+lx-2.2:.1f}" y="{fky-7:.1f}" width="4.4" height="14" rx="1.2" '
                 f'fill="#343A42" stroke="#79818B" stroke-width=".5"/>')
    for bx in (194, 214):
        o.append(f'<circle cx="{cx0+bx:.1f}" cy="{fky:.1f}" r="4.4" fill="#343A42" '
                 f'stroke="#79818B" stroke-width=".5"/>')
    o.append(f'<text x="{cx0+225:.1f}" y="{GY-48:.1f}" font-family="{MONO}" font-size="4.2" '
             f'fill="#6B737B" text-anchor="end" letter-spacing=".4">TERMINAL·06</text>')
    o.append(f'<text x="{cx0+118.5:.1f}" y="{GY+9:.1f}" font-family="{MONO}" font-size="4.4" '
             f'fill="#E4E1DA" text-anchor="middle" letter-spacing=".5">TERMINAL·06 — 237 × 96 × 104</text>')

    # --- phone, 146 x 71, stood on its long edge
    px = 282.0
    o.append(f'<rect x="{px}" y="{GY-146}" width="71" height="146" rx="9" fill="#1A1E23" '
             f'stroke="#4A5058" stroke-width=".8"/>')
    o.append(f'<rect x="{px+3}" y="{GY-143}" width="65" height="140" rx="7" fill="#0D1013" '
             f'stroke="#2A3138" stroke-width=".4"/>')
    o.append(f'<rect x="{px+26}" y="{GY-141}" width="19" height="3.4" rx="1.7" fill="#20262C"/>')
    o.append(f'<text x="{px+35.5:.1f}" y="{GY+9:.1f}" font-family="{MONO}" font-size="4.4" '
             f'fill="#7E858D" text-anchor="middle" letter-spacing=".5">PHONE — 146 × 71</text>')

    # --- mug, 80 dia x 95
    mx = 372.0
    o.append(f'<path d="M{mx} {GY-95} L{mx} {GY-6} Q{mx} {GY} {mx+6} {GY} '
             f'L{mx+74} {GY} Q{mx+80} {GY} {mx+80} {GY-6} L{mx+80} {GY-95} Z" '
             f'fill="#1E2329" stroke="#4A5058" stroke-width=".8"/>')
    o.append(f'<ellipse cx="{mx+40}" cy="{GY-95}" rx="40" ry="7" fill="#141A1F" '
             f'stroke="#4A5058" stroke-width=".8"/>')
    o.append(f'<path d="M{mx+80} {GY-78} q26 0 26 21 t-26 21" fill="none" '
             f'stroke="#4A5058" stroke-width="4.6" stroke-linecap="round"/>')
    o.append(f'<text x="{mx+40:.1f}" y="{GY+9:.1f}" font-family="{MONO}" font-size="4.4" '
             f'fill="#7E858D" text-anchor="middle" letter-spacing=".5">MUG — ⌀80 × 95</text>')

    o.append(f'<text x="14" y="16" font-family="{MONO}" font-size="5.4" fill="#7E858D" '
             f'text-anchor="start" letter-spacing=".5">1:1 — ALL THREE DRAWN AT THE SAME SCALE</text>')

    body = "\n".join(o)
    defs = '<defs>' + T.tube_defs(pid, warm=WARM, deep=DEEP) + '</defs>'
    return ('<svg preserveAspectRatio="xMidYMid meet" viewBox="0 0 %.1f %.1f" '
            'xmlns="http://www.w3.org/2000/svg" role="img">%s\n%s</svg>'
            % (W, H, defs, body))


def main():
    files = {
        "n-terminal-left.svg": terminal_left(),
        "n-terminal-profile.svg": terminal_profile(),
        "n-terminal-plan.svg": terminal_plan(),
        "n-terminal-exploded.svg": terminal_exploded(),
        "n-terminal-fascia.svg": terminal_fascia(),
        "n-terminal-scale.svg": terminal_scale(),
    }
    for name, s in files.items():
        with open(os.path.join(OUT, name), "w") as f:
            f.write(s)
        print(name, len(s))


if __name__ == "__main__":
    main()
