#!/usr/bin/env python3
"""Generate TERMINAL-06 project-local footprints for KiCad 10.

Every panel part on TS06-FASCIA is Soviet solder-lug hardware with no stock KiCad
equivalent. Regenerate with:  python3 tools/mkfp.py
Format tokens captured from a real KiCad 10.0 save on 08.09.26.

DIMENSION SOURCE: the parametric FreeCAD models in 3d/ are AUTHORITATIVE. They were
built by the owner and every dimension re-calipered (09.09.26) after the first pass
used bad technique. Numbers here are read straight out of the STEP B-reps, not typed.

GEOMETRY FINDING that shapes all three footprints: on every one of these parts the
solder lugs sit BEHIND the body, which itself sits behind the panel. The rotary is the
clearest case - bushing spans z 11.30..18.30, body z 0..11.30, lugs z 0..-10. The
fascia lives inside the bushing span, so the lugs are >=11.3 mm behind its rear face
and point further away. NO panel part can be board-mounted onto the fascia. Every one
is hand-wired to landing pads. This is what spec section 6 already concluded.
"""
import os, uuid, math

VER, GEN, GENV = 20260206, "pcbnew", "10.0"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "PCB", "lib", "TS06.pretty")

def U(): return f'(uuid "{uuid.uuid4()}")'

def txt(kind, val, y, layer, hide=False):
    h = " (hide yes)" if hide else ""
    return (f'\t(property "{kind}" "{val}"\n\t\t(at 0 {y} 0)\n\t\t(layer "{layer}")\n'
            f'\t\t{U()}{h}\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1 1)\n'
            f'\t\t\t\t(thickness 0.15)\n\t\t\t)\n\t\t)\n\t)')

def circle(r, layer, w=0.12, fill="no"):
    return (f'\t(fp_circle\n\t\t(center 0 0)\n\t\t(end {r} 0)\n\t\t(stroke\n\t\t\t(width {w})\n'
            f'\t\t\t(type solid)\n\t\t)\n\t\t(fill {fill})\n\t\t(layer "{layer}")\n\t\t{U()}\n\t)')

def line(x1, y1, x2, y2, layer, w=0.12):
    return (f'\t(fp_line\n\t\t(start {x1:.4f} {y1:.4f})\n\t\t(end {x2:.4f} {y2:.4f})\n'
            f'\t\t(stroke\n\t\t\t(width {w})\n\t\t\t(type solid)\n\t\t)\n'
            f'\t\t(layer "{layer}")\n\t\t{U()}\n\t)')

def npth(d, x=0, y=0):
    return (f'\t(pad "" np_thru_hole circle\n\t\t(at {x:.4f} {y:.4f})\n\t\t(size {d} {d})\n'
            f'\t\t(drill {d})\n\t\t(layers "F&B.Cu" "*.Mask")\n\t\t{U()}\n\t)')

def spad(n, x, y, w=2.2, h=1.5):
    """Back-side wire-landing pad. SMD on B.Cu deliberately: this board's front face is
    the product's face, so nothing punches a hole through it. The switch lugs are behind
    the panel anyway, so the wire has no reason to cross to the front."""
    return (f'\t(pad "{n}" smd rect\n\t\t(at {x:.4f} {y:.4f})\n\t\t(size {w} {h})\n'
            f'\t\t(layers "B.Cu" "B.Mask")\n\t\t{U()}\n\t)')

def rrpad(n, x, y, w, h, paste=True):
    """SMD roundrect land on the back, with paste. Used for the JST connector, whose
    geometry is not ours to invent - see the note on its footprint below."""
    lay = '"B.Cu" "B.Mask" "B.Paste"' if paste else '"B.Cu" "B.Mask"'
    return (f'\t(pad "{n}" smd roundrect\n\t\t(at {x:.4f} {y:.4f})\n\t\t(size {w} {h})\n'
            f'\t\t(layers {lay})\n\t\t(roundrect_rratio 0.25)\n\t\t{U()}\n\t)')

def pad(n, x, y, drill=1.0, size=1.9, shape="circle"):
    return (f'\t(pad "{n}" thru_hole {shape}\n\t\t(at {x:.4f} {y:.4f})\n\t\t(size {size} {size})\n'
            f'\t\t(drill {drill})\n\t\t(layers "*.Cu" "*.Mask")\n\t\t{U()}\n\t)')

def fab(s, y, size=0.8):
    return (f'\t(fp_text user "{s}"\n\t\t(at 0 {y} 0)\n\t\t(layer "F.Fab")\n\t\t{U()}\n'
            f'\t\t(effects\n\t\t\t(font\n\t\t\t\t(size {size} {size})\n\t\t\t\t(thickness 0.12)\n'
            f'\t\t\t)\n\t\t)\n\t)')

def write(name, descr, tags, body, ref_y=-2.0, val_y=2.0, hide_val=False):
    parts = [f'(footprint "{name}"', f'\t(version {VER})', f'\t(generator "{GEN}")',
             f'\t(generator_version "{GENV}")', '\t(layer "F.Cu")', f'\t(descr "{descr}")',
             f'\t(tags "{tags}")', '\t(attr through_hole)',
             txt("Reference", "REF**", ref_y, "F.SilkS"),
             txt("Value", name, val_y, "F.Fab", hide=hide_val),
             txt("Footprint", "", 0, "F.Fab", hide=True),
             txt("Datasheet", "", 0, "F.Fab", hide=True),
             txt("Description", "", 0, "F.Fab", hide=True)]
    parts += body
    parts.append('\t(embedded_fonts no)')
    parts.append(')')
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, name + ".kicad_mod")
    open(p, "w", encoding="utf8").write("\n".join(parts) + "\n")
    print("wrote", os.path.relpath(p, os.path.join(os.path.dirname(OUT), "..", "..")))

# ---------------------------------------------------------------- MT1 lever
# Bushing 7.82 mm from 3d/MT1.step (cylinder R 3.910 at z 13.75). Hole = 8.0 mm.
# Supersedes the 7.85 mm hand reading - same number to within 0.03 mm, so the hole
# is unchanged; the CAD value is simply the better-sourced one.
# Lugs are modelled but sit behind the body, unreachable from this board (see header).
b = [npth(8.0)]
b += [circle(5.6, "F.SilkS"), circle(6.2, "F.CrtYd", 0.05), circle(4.0, "F.Fab", 0.1)]
b += [spad(i + 1, (i - 0.5) * 3.2, 9.5) for i in range(2)]
write("TS06_MT1_Lever_PanelMount",
      "MT1/TV1-2 Soviet toggle lever, panel mount. 8.0mm bushing clearance hole "
      "(bushing 7.82mm from the calipered FreeCAD model, 3d/MT1.step). Lugs sit "
      "behind the body and cannot reach this board, so it carries wire-landing "
      "pads rather than lug pads.",
      "MT1 TV1-2 toggle lever panel-mount soviet TERMINAL-06", b, -7.6, 10.6, hide_val=True)

# ---------------------------------------------------------------- KMD1 button
# Bushing 7.82 mm from 3d/KMD1.step (cylinder R 3.910 at z 12.40); plunger 6.00 mm
# (R 3.000 at z 12.28). This CLOSES the old "carried over from MT1 by eye" gap - the
# button now has its own independent value, and it agrees with MT1 exactly.
b = [npth(8.0)]
b += [circle(5.6, "F.SilkS"), circle(6.2, "F.CrtYd", 0.05), circle(4.0, "F.Fab", 0.1)]
b += [spad(i + 1, (i - 0.5) * 3.2, 9.5) for i in range(2)]
write("TS06_KMD1_Button_PanelMount",
      "KMD1-1 Soviet pushbutton, panel mount. 8.0mm bushing clearance hole from the "
      "calipered FreeCAD model (3d/KMD1.step): bushing 7.82mm, plunger 6.00mm. "
      "Independently sourced - no longer carried over from MT1 by eye.",
      "KMD1 button panel-mount soviet TERMINAL-06", b, -7.6, 10.6, hide_val=True)

# ---------------------------------------------------------------- Rotary, panel-mount
# All from 3d/SR25.step, calipered: bushing 8.62, usable 7.00, shaft 6.00,
# body 25.00, lug ring D19.99 at 30deg pitch (12 detents counted 08.09.26 ->
# 360/12 = exactly 30.00deg per step, 6 positions spanning 150deg). Hole 8.8 mm (+0.18 fit clearance).
# Body 25.00 sits BEHIND the fascia -> keepout, not a hole.
# The 26.94 mm body figure from 28.08.26 is WITHDRAWN: bad caliper technique, since
# re-measured. It has propagated into spec sections 2/6 and prototype plan P1/P8 and
# must be corrected there too.
# Bushing usable length is 7.00 mm and the fascia is 2.0 mm FR4 recessed into the
# chassis - so nut + washer + recess depth must all fit in the remaining 5.00 mm.
b = [npth(8.8)]
b += [circle(6.4, "F.SilkS"), circle(7.0, "F.CrtYd", 0.05)]
b += [circle(12.50, "F.Fab", 0.1)]           # body radius 25.00/2, keepout behind panel
b += [circle(9.995, "User.1", 0.1)]          # lug ring, DOCUMENTATION ONLY - see below
for i in range(12):                          # 12 taps = 6 positions x 2 poles
    a = math.radians(15 + 30 * i)
    b.append(line(9.995 * math.cos(a), 9.995 * math.sin(a),
                  10.5 * math.cos(a), 10.5 * math.sin(a), "User.1", 0.1))
# Landing pads at 8 mm pitch and in DESCENDING voltage order (+5V leftmost, GND, then
# COM on the right nearest the connector). Two reasons, both about routing rather than
# looks: the wide pitch leaves room to sit a 1206 between every adjacent pair, and the
# descending order means each resistor's pad 1 (its higher node) faces left toward the
# switch pad it belongs to. The ladder then routes as ten short diagonals that cannot
# cross each other. Ascending order forces every one of them to cross its neighbour.
b += [spad(n, -24.0 + i * 8.0, 17.5) for i, n in enumerate([6, 5, 4, 3, 2, 1, 7])]
write("TS06_Rotary_SR25_PanelMount",
      "SR25-style 6-position 2-pole galette rotary, panel mount. All dimensions from the "
      "calipered FreeCAD model 3d/SR25.step: bushing 8.62mm x 7.00mm usable (hole 8.8mm), "
      "shaft 6.00mm, body 25.00mm, 12 taps on D19.99 at exactly 30deg + 2 wiper commons "
      "on D10.90. F.Fab circle is the body keepout BEHIND the panel. User.1 shows the lug "
      "ring for reference only - the lugs sit 11.3mm behind this board and cannot land "
      "on it.",
      "SR25 rotary galette 6-position panel-mount soviet TERMINAL-06", b, -8.4, 20.0, hide_val=True)

# ---------------------------------------------------------------- 1206 resistor
# SMD, hand-solder land pattern, authored on the BACK layers. Through-hole axials were
# the first choice and were wrong: their leads would punch eight pairs of holes through
# the product's face. 1206 is still comfortably hand-solderable.
b = [spad(1, -1.85, 0, 2.0, 1.7), spad(2, 1.85, 0, 2.0, 1.7)]
b += [line(-1.6, -1.05, 1.6, -1.05, "B.SilkS", 0.1),
      line(-1.6, 1.05, 1.6, 1.05, "B.SilkS", 0.1)]
b += [line(-3.2, -1.3, 3.2, -1.3, "B.CrtYd", 0.05), line(-3.2, 1.3, 3.2, 1.3, "B.CrtYd", 0.05),
      line(-3.2, -1.3, -3.2, 1.3, "B.CrtYd", 0.05), line(3.2, -1.3, 3.2, 1.3, "B.CrtYd", 0.05)]
write("TS06_R_1206_HandSolder",
      "1206 chip resistor, hand-solder lands, authored on the back layers. The fascia's "
      "front is the product face, so no passive puts a hole through it.",
      "resistor 1206 SMD TERMINAL-06", b, -2.2, 2.2)

# ---------------------------------------------------------------- cable solder pads
# Six SMD lands on the back, cable soldered directly. A JST-XH is through-hole only, so
# keeping it here would have put six holes through the face - the one thing this board
# is not allowed to do. The XH connector keeps its job at the MAIN BOARD end, where the
# cable still unplugs for service; only the fascia end is permanent, and the fascia is
# not a serviceable part.
# Strain relief is the chassis's job: nothing here resists a pulled cable.
b = [spad(i + 1, -7.5 + i * 3.0, 0, 3.2, 1.8) for i in range(6)]
b += [line(-9.6, -1.6, -9.6, 1.6, "B.SilkS", 0.12),
      line(-9.6, -1.6, -8.2, 0, "B.SilkS", 0.12),
      line(-9.6, 1.6, -8.2, 0, "B.SilkS", 0.12)]
b += [line(-9.9, -2.6, 9.9, -2.6, "B.CrtYd", 0.05), line(-9.9, 2.6, 9.9, 2.6, "B.CrtYd", 0.05),
      line(-9.9, -2.6, -9.9, 2.6, "B.CrtYd", 0.05), line(9.9, -2.6, 9.9, 2.6, "B.CrtYd", 0.05)]
write("TS06_CablePads_6",
      "Six back-side solder lands for the panel cable: 1 GND, 2 +5V, 3 A6, 4 A7, "
      "5 D7, 6 D8. Pad 1 marked by a silk arrow. Direct-solder rather than a "
      "connector, because JST-XH is through-hole and this board puts no hole through "
      "its front face. Strain relief is provided by the chassis, not the board.",
      "cable pads panel solder TERMINAL-06", b, -3.4, 3.4)

# ------------------------------------------------- JST PH S6B-PH-SM4-TB, side entry SMT
# Land pattern taken from KiCad's own Connector_JST library, which draws it from JST's
# manufacturer drawing. NOT invented here, and not scaled off a marketplace photo.
#
# Cross-checked against JST's published PH dimension table before use: the library body
# width is 15.9 mm, and JST gives B = A + 5.9 with A = 2.0 x (n-1); at n=6 that is
# 10.0 + 5.9 = 15.9. Their table's endpoints agree too (n=2 -> 7.9, n=16 -> 35.95).
# Two independent sources, same number.
#
# MIRRORED IN X from the library original, because this part mounts on the BACK. That
# puts pin 1 at +5 rather than -5, so the numbering runs right to left in board
# coordinates. A single-row connector is symmetric, so this is a valid part orientation,
# not a workaround - but the pin-1 marker matters, so it is mirrored with everything else.
#
# The two MP pads are the metal retention tabs. They are what actually holds the
# connector down; the signal pads are not structural. Never omit them.
PH_PADS = [("1", 5.0), ("2", 3.0), ("3", 1.0), ("4", -1.0), ("5", -3.0), ("6", -5.0)]
b = [rrpad(n, x, -2.85, 1.0, 3.5) for n, x in PH_PADS]
b += [rrpad("MP", 7.35, 2.9, 1.5, 3.4), rrpad("MP", -7.35, 2.9, 1.5, 3.4)]
for x1, y1, x2, y2 in [(7.95,-3.2,7.15,-3.2), (7.15,-3.2,7.15,-1.6), (7.15,-1.6,-7.15,-1.6),
                       (-7.15,-1.6,-7.15,-3.2), (-7.15,-3.2,-7.95,-3.2),
                       (7.95,4.4,-7.95,4.4), (7.95,-3.2,7.95,4.4), (-7.95,-3.2,-7.95,4.4),
                       (5.5,-1.6,5.0,-0.892893), (5.0,-0.892893,4.5,-1.6)]:
    b.append(line(x1, y1, x2, y2, "B.Fab", 0.1))
for x1, y1, x2, y2 in [(8.06,0.94,8.06,-3.31), (8.06,-3.31,7.04,-3.31), (7.04,-3.31,7.04,-1.71),
                       (7.04,-1.71,5.76,-1.71), (5.76,-1.71,5.76,-4.6),
                       (-8.06,0.94,-8.06,-3.31), (-8.06,-3.31,-7.04,-3.31),
                       (-7.04,-3.31,-7.04,-1.71), (-7.04,-1.71,-5.76,-1.71),
                       (6.34,4.51,-6.34,4.51)]:
    b.append(line(x1, y1, x2, y2, "B.SilkS", 0.12))
for x1, y1, x2, y2 in [(-8.6,-5.1,-8.6,5.1), (-8.6,5.1,8.6,5.1),
                       (8.6,5.1,8.6,-5.1), (8.6,-5.1,-8.6,-5.1)]:
    b.append(line(x1, y1, x2, y2, "B.CrtYd", 0.05))
write("TS06_JST_PH_S6B-PH-SM4-TB_Back",
      "JST PH S6B-PH-SM4-TB: 6-way, 2.0 mm pitch, side entry, surface mount, 2 A / 100 V. "
      "Land pattern from KiCad's Connector_JST library (JST manufacturer drawing), "
      "mirrored in X for back-side mounting. Pads 7/8 are the retention tabs and carry "
      "the mechanical load - the signal pads do not. Cable exits toward +Y.",
      "connector JST PH SMT 6way panel TERMINAL-06", b, -6.2, 6.6, hide_val=True)
