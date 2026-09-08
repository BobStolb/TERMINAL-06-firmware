#!/usr/bin/env python3
"""Generate TERMINAL-06 project-local footprints for KiCad 10.

Every panel part on TS06-FASCIA is Soviet solder-lug hardware with no stock KiCad
equivalent. Regenerate with:  python3 tools/mkfp.py
Format tokens captured from a real KiCad 10.0 save on 08.09.26.
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
# Bushing 7.85 mm MEASURED (27.08.26). Hole = 8.0 mm (+0.15 fit clearance).
# Solder lugs NOT measured -> no lug pads. Three wire-landing pads instead,
# placed clear of the bushing, on a 2.54 mm pitch below the hole.
b = [npth(8.0)]
b += [circle(5.6, "F.SilkS"), circle(6.2, "F.CrtYd", 0.05), circle(4.0, "F.Fab", 0.1)]
b += [pad(i + 1, (i - 1) * 2.54, 8.0) for i in range(3)]
b += [fab("MT1 lever - bushing 7.85 MEASURED", 7.0),
      fab("lugs unmeasured: hand-wire to pads 1-3", 8.2)]
write("TS06_MT1_Lever_PanelMount",
      "MT1/TV1-2 Soviet toggle lever, panel mount. 8.0mm bushing clearance hole "
      "(bushing 7.85mm measured 27.08.26). Solder lugs are unmeasured, so this "
      "footprint carries wire-landing pads, not lug pads.",
      "MT1 TV1-2 toggle lever panel-mount soviet TERMINAL-06", b, -7.6, 10.6)

# ---------------------------------------------------------------- KMD1 button
# Bushing ~7.85 mm, eye-corroborated against MT1 (27.08.26), NOT independently calipered.
b = [npth(8.0)]
b += [circle(5.6, "F.SilkS"), circle(6.2, "F.CrtYd", 0.05), circle(4.0, "F.Fab", 0.1)]
b += [pad(i + 1, (i - 1) * 2.54, 8.0) for i in range(2)]
b += [fab("KMD1-1 button - bushing ~7.85 EYE-CORROBORATED", 7.0),
      fab("verify with calipers before the batch order", 8.2)]
write("TS06_KMD1_Button_PanelMount",
      "KMD1-1 Soviet pushbutton, panel mount. 8.0mm bushing clearance hole. "
      "WARNING: bushing diameter carried over from MT1 by eye, never calipered "
      "on this part - see TERMINAL-06-measurements-KMD1.md.",
      "KMD1 button panel-mount soviet TERMINAL-06", b, -7.6, 10.6)

# ---------------------------------------------------------------- Rotary, panel-mount
# Bushing 8.62 mm is CAD-MODEL-DERIVED and unverified. Hole 8.8 mm (+0.18).
# Body 26.94 mm MEASURED - it sits BEHIND the fascia, so it is a keepout, not a hole.
b = [npth(8.8)]
b += [circle(6.4, "F.SilkS"), circle(7.0, "F.CrtYd", 0.05)]
b += [circle(13.47, "F.Fab", 0.1)]           # measured body radius, keepout behind panel
b += [circle(9.995, "User.1", 0.1)]          # CAD outer tap ring, for the board-mount option
for i in range(12):                          # CAD tap positions, documentation only
    a = math.radians(15 + 30 * i)
    b.append(line(9.995 * math.cos(a), 9.995 * math.sin(a),
                  10.5 * math.cos(a), 10.5 * math.sin(a), "User.1", 0.1))
b += [pad(i + 1, -7.62 + i * 2.54, 17.5) for i in range(7)]   # COM + 6 taps, wire-landed
b += [fab("SR25 rotary - bushing 8.62 UNVERIFIED (CAD only)", 15.0),
      fab("body 26.94 MEASURED = keepout behind panel", 16.2),
      fab("User.1 ring = CAD tap positions, 30deg, D19.99", -15.5)]
write("TS06_Rotary_SR25_PanelMount",
      "SR25-style 6-position 2-pole galette rotary, panel mount. Bushing hole 8.8mm "
      "from a CAD-MODEL bushing of 8.62mm - UNVERIFIED, caliper before ordering panels. "
      "F.Fab circle is the MEASURED 26.94mm body, a keepout behind the panel. User.1 "
      "shows the CAD tap ring (D19.99, 30deg pitch) for the board-mount option.",
      "SR25 rotary galette 6-position panel-mount soviet TERMINAL-06", b, -8.4, 20.0)
