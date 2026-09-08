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

def pad(n, x, y, drill=1.0, size=1.9, shape="circle"):
    return (f'\t(pad "{n}" thru_hole {shape}\n\t\t(at {x:.4f} {y:.4f})\n\t\t(size {size} {size})\n'
            f'\t\t(drill {drill})\n\t\t(layers "*.Cu" "*.Mask")\n\t\t{U()}\n\t)')

def fab(s, y, size=0.8):
    return (f'\t(fp_text user "{s}"\n\t\t(at 0 {y} 0)\n\t\t(layer "F.Fab")\n\t\t{U()}\n'
            f'\t\t(effects\n\t\t\t(font\n\t\t\t\t(size {size} {size})\n\t\t\t\t(thickness 0.12)\n'
            f'\t\t\t)\n\t\t)\n\t)')

def write(name, descr, tags, body, ref_y=-2.0, val_y=2.0):
    parts = [f'(footprint "{name}"', f'\t(version {VER})', f'\t(generator "{GEN}")',
             f'\t(generator_version "{GENV}")', '\t(layer "F.Cu")', f'\t(descr "{descr}")',
             f'\t(tags "{tags}")', '\t(attr through_hole)',
             txt("Reference", "REF**", ref_y, "F.SilkS"),
             txt("Value", name, val_y, "F.Fab"),
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
b += [fab("MT1 lever - bushing 7.82 (CAD, calipered)", 7.0),
      fab("lugs sit behind body: hand-wire to pads 1-3", 8.2)]
write("TS06_MT1_Lever_PanelMount",
      "MT1/TV1-2 Soviet toggle lever, panel mount. 8.0mm bushing clearance hole "
      "(bushing 7.82mm from the calipered FreeCAD model, 3d/MT1.step). Lugs sit "
      "behind the body and cannot reach this board, so it carries wire-landing "
      "pads rather than lug pads.",
      "MT1 TV1-2 toggle lever panel-mount soviet TERMINAL-06", b, -7.6, 10.6)

# ---------------------------------------------------------------- KMD1 button
# Bushing 7.82 mm from 3d/KMD1.step (cylinder R 3.910 at z 12.40); plunger 6.00 mm
# (R 3.000 at z 12.28). This CLOSES the old "carried over from MT1 by eye" gap - the
# button now has its own independent value, and it agrees with MT1 exactly.
b = [npth(8.0)]
b += [circle(5.6, "F.SilkS"), circle(6.2, "F.CrtYd", 0.05), circle(4.0, "F.Fab", 0.1)]
b += [spad(i + 1, (i - 0.5) * 3.2, 9.5) for i in range(2)]
b += [fab("KMD1-1 button - bushing 7.82 (CAD, calipered)", 7.0),
      fab("plunger 6.00 - keep silk clear of the cap", 8.2)]
write("TS06_KMD1_Button_PanelMount",
      "KMD1-1 Soviet pushbutton, panel mount. 8.0mm bushing clearance hole from the "
      "calipered FreeCAD model (3d/KMD1.step): bushing 7.82mm, plunger 6.00mm. "
      "Independently sourced - no longer carried over from MT1 by eye.",
      "KMD1 button panel-mount soviet TERMINAL-06", b, -7.6, 10.6)

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
b += [spad(i + 1, -10.8 + i * 3.6, 17.5) for i in range(7)]   # T1..T6 then COM, wire-landed
b += [fab("SR25 rotary - bushing 8.62 x 7.00 usable (CAD, calipered)", 15.0),
      fab("body 25.00 = keepout BEHIND panel, not a hole", 16.2),
      fab("nut+washer+recess must fit the 5.00 left of the bushing", 17.4),
      fab("User.1 lug ring D19.99 30.00deg (12 detents): lugs 11.3 BEHIND", -15.5),
      fab("board - unreachable, hand-wire to pads 1-7", -16.7)]
write("TS06_Rotary_SR25_PanelMount",
      "SR25-style 6-position 2-pole galette rotary, panel mount. All dimensions from the "
      "calipered FreeCAD model 3d/SR25.step: bushing 8.62mm x 7.00mm usable (hole 8.8mm), "
      "shaft 6.00mm, body 25.00mm, 12 taps on D19.99 at exactly 30deg + 2 wiper commons "
      "on D10.90. F.Fab circle is the body keepout BEHIND the panel. User.1 shows the lug "
      "ring for reference only - the lugs sit 11.3mm behind this board and cannot land "
      "on it.",
      "SR25 rotary galette 6-position panel-mount soviet TERMINAL-06", b, -8.4, 20.0)

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

# ---------------------------------------------------------------- JST-XH 6 way
b = [pad(1, -6.25, 0, 1.0, 1.7, "rect")] + [pad(i + 2, -6.25 + (i + 1) * 2.5, 0) for i in range(5)]
b += [line(-8.15, -2.4, 8.15, -2.4, "F.SilkS"), line(-8.15, 3.4, 8.15, 3.4, "F.SilkS"),
      line(-8.15, -2.4, -8.15, 3.4, "F.SilkS"), line(8.15, -2.4, 8.15, 3.4, "F.SilkS")]
b += [line(-8.6, -2.9, 8.6, -2.9, "F.CrtYd", 0.05), line(-8.6, 3.9, 8.6, 3.9, "F.CrtYd", 0.05),
      line(-8.6, -2.9, -8.6, 3.9, "F.CrtYd", 0.05), line(8.6, -2.9, 8.6, 3.9, "F.CrtYd", 0.05)]
b += [fab("1", -4.4)]
write("TS06_JST_XH_6",
      "JST-XH 6-way vertical header, 2.5 mm pitch. Pin 1 square. Panel cable: "
      "GND, +5V, A6, A7, D7, D8.",
      "connector JST XH 6 panel TERMINAL-06", b, -4.6, 5.9)
