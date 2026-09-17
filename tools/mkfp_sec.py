#!/usr/bin/env python3
"""Generate the TS06-SEC footprints.

Separate from mkfp.py on purpose: mkfp.py rewrites every panel footprint with fresh UUIDs
each run, and nothing about the fascia parts changes here. UUIDs below are derived from
the footprint name and element index (uuid5), so re-running this file reproduces the same
files byte for byte.

LAND PATTERNS ARE NOT INVENTED HERE. Every pad and courtyard number is KiCad 10's own
library value (JEDEC / manufacturer drawings), read out of the installed footprints on
15.09.26: SOT-23_Handsoldering, SOIC-28W_7.5x17.9mm_P1.27mm, R_0805/C_0805/R_1206/C_1206
..._HandSolder, R_2512_6332Metric_Pad1.40x3.35mm_HandSolder, SMDIP-4_W9.53mm,
JST_VH_S2P-VH_1x02_P3.96mm_Horizontal, JST_XH_S8B-XH-A_1x08_P2.50mm_Horizontal,
IDC-Header_2x05_P2.54mm_Horizontal and LED_D3.0mm. Only the origin moves: every part here
is centred on its pin field, which is what the board generator places against.

BACK-SIDE PARTS are authored the way the fascia's are: geometry MIRRORED IN X (a part on
the back, seen from the front, is its own mirror image), graphics on B.* layers, text with
(justify mirror), header layer left at F.Cu for the board generator to set.

ROTATION: this repo never places a footprint with an angle (tools/checkpcb.py reads only a
bare "at x y"), so each orientation is its own footprint. _R90 means turned 90 deg
counter-clockwise as seen from the FRONT in KiCad's view - (x, y) -> (y, -x) in KiCad's
Y-down coordinates. For a back part the mirror is applied first, then the turn.

Regenerate with:  python3 tools/mkfp_sec.py
"""
import os, uuid

VER, GEN, GENV = 20260206, "pcbnew", "10.0"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "PCB", "lib", "TS06.pretty")
NS = uuid.UUID("5ec06000-7506-4000-8000-000000000000")


def num(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def xform(x, y, back, rot):
    if back:
        x = -x
    for _ in range(rot // 90):
        x, y = y, -x
    return x, y


def write(name, descr, tags, prims, back=False, rot=0, attr="smd"):
    """prims are in the stock library's own front-view orientation, centred on the pin field:
       ("pad", num, type, shape, x, y, w, h, drill, rratio)
       ("rect", x1, y1, x2, y2, layerkind, width)      layerkind: CrtYd / Fab / SilkS
       ("line", x1, y1, x2, y2, layerkind, width)
       ("circle", cx, cy, r, layerkind, width)"""
    n = [0]

    def U():
        n[0] += 1
        return f'(uuid "{uuid.uuid5(NS, name + "/" + str(n[0]))}")'

    side = "B." if back else "F."
    mirror = "\n\t\t\t(justify mirror)" if back else ""
    T = lambda x, y: xform(x, y, back, rot)
    ys = []
    body = []
    for p in prims:
        if p[0] == "pad":
            _, pn, typ, shape, x, y, w, h, drill, rr = p
            X, Y = T(x, y)
            if rot in (90, 270):
                w, h = h, w
            if typ == "smd":
                lay = f'"{side}Cu" "{side}Mask" "{side}Paste"'
                extra = f"\n\t\t(layers {lay})"
            else:
                extra = f"\n\t\t(drill {num(drill)})\n\t\t(layers \"*.Cu\" \"*.Mask\")"
            if shape == "roundrect":
                extra += f"\n\t\t(roundrect_rratio {rr})"
            body.append(f'\t(pad "{pn}" {typ} {shape}\n\t\t(at {num(X)} {num(Y)})\n'
                        f'\t\t(size {num(w)} {num(h)}){extra}\n\t\t{U()}\n\t)')
        elif p[0] in ("rect", "line"):
            _, x1, y1, x2, y2, lk, wd = p
            segs = ([(x1, y1, x2, y1), (x2, y1, x2, y2), (x2, y2, x1, y2), (x1, y2, x1, y1)]
                    if p[0] == "rect" else [(x1, y1, x2, y2)])
            for a, b, c, d in segs:
                A, B = T(a, b)
                C, D = T(c, d)
                if lk == "CrtYd":
                    ys += [B, D]
                body.append(f'\t(fp_line\n\t\t(start {num(A)} {num(B)})\n\t\t(end {num(C)} {num(D)})\n'
                            f'\t\t(stroke\n\t\t\t(width {wd})\n\t\t\t(type solid)\n\t\t)\n'
                            f'\t\t(layer "{side}{lk}")\n\t\t{U()}\n\t)')
        elif p[0] == "circle":
            _, cx, cy, r, lk, wd = p
            CX, CY = T(cx, cy)
            body.append(f'\t(fp_circle\n\t\t(center {num(CX)} {num(CY)})\n\t\t(end {num(CX + r)} {num(CY)})\n'
                        f'\t\t(stroke\n\t\t\t(width {wd})\n\t\t\t(type solid)\n\t\t)\n\t\t(fill no)\n'
                        f'\t\t(layer "{side}{lk}")\n\t\t{U()}\n\t)')
    top = min(ys) - 0.8 if ys else -1.5
    bot = max(ys) + 0.8 if ys else 1.5

    def prop(kind, val, y, hide):
        h = " (hide yes)" if hide else ""
        return (f'\t(property "{kind}" "{val}"\n\t\t(at 0 {num(y)} 0)\n\t\t(layer "{side}Fab")\n'
                f'\t\t{U()}{h}\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 0.8 0.8)\n'
                f'\t\t\t\t(thickness 0.12)\n\t\t\t){mirror}\n\t\t)\n\t)')

    parts = [f'(footprint "{name}"', f'\t(version {VER})', f'\t(generator "{GEN}")',
             f'\t(generator_version "{GENV}")', '\t(layer "F.Cu")', f'\t(descr "{descr}")',
             f'\t(tags "{tags}")', f'\t(attr {attr})',
             prop("Reference", "REF**", top, False), prop("Value", name, bot, True),
             prop("Footprint", "", 0, True), prop("Datasheet", "", 0, True),
             prop("Description", "", 0, True)]
    parts += body
    parts += ['\t(embedded_fonts no)', ')']
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name + ".kicad_mod"), "w", encoding="utf8", newline="\n") as fh:
        fh.write("\n".join(parts) + "\n")
    return name


def rotations(base, descr, tags, prims, back, attr="smd", rots=(0, 90, 180, 270)):
    made = []
    for r in rots:
        nm = base if r == 0 else f"{base}_R{r}"
        d = descr + ("" if r == 0 else f" Pre-rotated {r} deg counter-clockwise (front view), per this repo's no-rotation-token convention.")
        made.append(write(nm, d, tags, prims, back=back, rot=r, attr=attr))
    return made


def two_pad(px, w, h, rr, cx, cy, fx, fy):
    return [("pad", "1", "smd", "roundrect", -px, 0, w, h, None, rr),
            ("pad", "2", "smd", "roundrect", px, 0, w, h, None, rr),
            ("rect", -cx, -cy, cx, cy, "CrtYd", 0.05), ("rect", -fx, -fy, fx, fy, "Fab", 0.1)]


made = []
BACK = ("Mounted on the BACK: geometry mirrored in X from the KiCad library original, "
        "graphics on B.* layers.")

# ---------------------------------------------------------------- SOT-23, MMBTA42
# SOT-23_Handsoldering: pads (-1.5,-0.95) (-1.5,0.95) (1.5,0), 1.90 x 0.80, courtyard +-2.70 x +-1.75.
# MMBTA42 pinout (KiCad symbol Q_NPN_BEC): 1 base, 2 emitter, 3 collector.
sot = [("pad", "1", "smd", "roundrect", -1.5, -0.95, 1.9, 0.8, None, 0.25),
       ("pad", "2", "smd", "roundrect", -1.5, 0.95, 1.9, 0.8, None, 0.25),
       ("pad", "3", "smd", "roundrect", 1.5, 0, 1.9, 0.8, None, 0.25),
       ("rect", -2.7, -1.75, 2.7, 1.75, "CrtYd", 0.05), ("rect", -0.7, -1.52, 0.7, 1.52, "Fab", 0.1),
       ("line", -2.45, -1.6, -0.6, -1.6, "SilkS", 0.12)]
made += rotations("TS06_SOT-23_Back",
                  "SOT-23, hand-solder land pattern (KiCad SOT-23_Handsoldering). For MMBTA42: pad 1 base, "
                  "2 emitter, 3 collector - the SOT-23 twin of MPSA42, same 300 V rating. The silk bar "
                  "marks pad 1. " + BACK, "SOT-23 MMBTA42 transistor SMD back TERMINAL-06", sot, True)

# ---------------------------------------------------------------- SOIC-28W, MCP23017-E/SO
# SOIC-28W_7.5x17.9mm_P1.27mm: pads 1-14 at x -4.65, 15-28 at x +4.65, 1.27 pitch from
# y -8.255, 2.05 x 0.60; courtyard +-5.93 x +-9.20; body 7.5 x 17.9.
soic = [("pad", str(k + 1), "smd", "roundrect", -4.65, -8.255 + 1.27 * k, 2.05, 0.6, None, 0.25) for k in range(14)]
soic += [("pad", str(k + 15), "smd", "roundrect", 4.65, 8.255 - 1.27 * k, 2.05, 0.6, None, 0.25) for k in range(14)]
soic += [("rect", -5.93, -9.2, 5.93, 9.2, "CrtYd", 0.05), ("rect", -3.75, -8.95, 3.75, 8.95, "Fab", 0.1),
         ("line", -5.675, -8.95, -3.6, -8.95, "SilkS", 0.12)]
made += rotations("TS06_SOIC-28W_Back",
                  "SOIC-28 wide body 7.5 x 17.9 mm, 1.27 mm pitch (KiCad SOIC-28W_7.5x17.9mm_P1.27mm). For "
                  "MCP23017-E/SO: 1-8 GPB0-7, 9 VDD, 10 VSS, 11 NC, 12 SCL, 13 SDA, 14 NC, 15-17 A0-A2, "
                  "18 RESET, 19 INTB, 20 INTA, 21-28 GPA0-7. The silk bar marks pin 1. " + BACK,
                  "SOIC-28W MCP23017 SMD back TERMINAL-06", soic, True)

# ---------------------------------------------------------------- chip resistors and capacitors
made += rotations("TS06_R_0805_Back", "0805 chip resistor, hand-solder lands (KiCad R_0805_2012Metric_Pad1.20x1.40mm_HandSolder). " + BACK,
                  "resistor 0805 SMD back TERMINAL-06", two_pad(1.0, 1.2, 1.4, 0.208333, 1.85, 0.95, 1.0, 0.625), True, rots=(0, 90))
made += rotations("TS06_C_0805_Back", "0805 chip capacitor, hand-solder lands (KiCad C_0805_2012Metric_Pad1.18x1.45mm_HandSolder). " + BACK,
                  "capacitor 0805 SMD back TERMINAL-06", two_pad(1.0375, 1.175, 1.45, 0.212766, 1.88, 0.98, 1.0, 0.625), True, rots=(0, 90))
made += rotations("TS06_R_1206_Back", "1206 chip resistor, hand-solder lands (KiCad R_1206_3216Metric_Pad1.30x1.75mm_HandSolder). "
                  "Used in series pairs on the HV anode bleed so no single part sees more than about 100 V. " + BACK,
                  "resistor 1206 SMD back TERMINAL-06", two_pad(1.55, 1.3, 1.75, 0.192308, 2.45, 1.13, 1.6, 0.8), True, rots=(0, 90))
made += rotations("TS06_C_1206_Back", "1206 chip capacitor, hand-solder lands (KiCad C_1206_3216Metric_Pad1.33x1.80mm_HandSolder). " + BACK,
                  "capacitor 1206 SMD back TERMINAL-06", two_pad(1.5625, 1.325, 1.8, 0.188679, 2.48, 1.15, 1.6, 0.8), True, rots=(0, 90))
made += rotations("TS06_R_2512_Back", "2512 chip resistor, hand-solder lands (KiCad R_2512_6332Metric_Pad1.40x3.35mm_HandSolder). "
                  "For the tube anode series resistors: 1 W body, and in normal running they drop well under 100 V. " + BACK,
                  "resistor 2512 SMD back TERMINAL-06", two_pad(3.05, 1.4, 3.35, 0.178571, 4.0, 1.93, 3.15, 1.6), True, rots=(0, 90))

# ---------------------------------------------------------------- TLP627, surface-mount lead form
# SMDIP-4_W9.53mm: pads 1 (-4.765,-1.27) 2 (-4.765,1.27) 3 (4.765,1.27) 4 (4.765,-1.27), 2.00 x 1.78;
# courtyard +-6.02 x +-2.79. TLP627 (KiCad symbol): 1 LED anode, 2 LED cathode, 3 emitter, 4 collector.
smdip = [("pad", "1", "smd", "roundrect", -4.765, -1.27, 2.0, 1.78, None, 0.140449),
         ("pad", "2", "smd", "roundrect", -4.765, 1.27, 2.0, 1.78, None, 0.140449),
         ("pad", "3", "smd", "roundrect", 4.765, 1.27, 2.0, 1.78, None, 0.140449),
         ("pad", "4", "smd", "roundrect", 4.765, -1.27, 2.0, 1.78, None, 0.140449),
         ("rect", -6.02, -2.79, 6.02, 2.79, "CrtYd", 0.05), ("rect", -3.17, -2.54, 3.17, 2.54, "Fab", 0.1),
         ("line", -5.765, -2.55, -3.9, -2.55, "SilkS", 0.12)]
made += rotations("TS06_SMDIP-4_Back",
                  "DIP-4 with surface-mount lead form, 9.53 mm row spacing (KiCad SMDIP-4_W9.53mm). For TLP627: "
                  "1 LED anode, 2 LED cathode, 3 emitter, 4 collector - the same part as the main board's "
                  "four optos; a through-hole TLP627 lands here with its leads splayed flat. The silk bar marks pin 1. " + BACK,
                  "DIP-4 SMD TLP627 optocoupler back TERMINAL-06", smdip, True)

# ---------------------------------------------------------------- cable connectors, side entry, bodies on the back
# Through-hole pins, housing on the back; the joints land on the front in the strip behind
# the fascia. Library originals have pin 1 at the origin; here the pin field is centred.
vh = [("pad", "1", "thru_hole", "roundrect", -1.98, 0, 2.7, 2.7, 1.7, 0.092593),
      ("pad", "2", "thru_hole", "circle", 1.98, 0, 2.7, 2.7, 1.7, None),
      ("rect", -4.43, -2.5, 4.43, 13.9, "CrtYd", 0.05), ("rect", -3.93, -2.0, 3.93, 13.4, "Fab", 0.1)]
made += rotations("TS06_JST_VH_S2P-VH_Back",
                  "JST VH S2P-VH: 2-way, 3.96 mm pitch, side entry, through-hole (KiCad JST_VH_S2P-VH_1x02_P3.96mm_Horizontal), "
                  "pin field centred. XS1, the 185 V feed: VH so it cannot mate with any 5 V XH plug. The housing and "
                  "cable run toward +Y in the unrotated part. " + BACK,
                  "connector JST VH side-entry HV back TERMINAL-06", vh, True, attr="through_hole")
xh8 = [("pad", str(k + 1), "thru_hole", "roundrect" if k == 0 else "oval", -8.75 + 2.5 * k, 0, 1.7, 1.95, 0.95,
        0.147059 if k == 0 else None) for k in range(8)]
xh8 += [("rect", -11.7, -2.81, 11.7, 9.7, "CrtYd", 0.05), ("rect", -11.2, -2.3, 11.2, 9.2, "Fab", 0.1)]
made += rotations("TS06_JST_XH_S8B-XH-A_Back",
                  "JST XH S8B-XH-A: 8-way, 2.50 mm pitch, side entry, through-hole (KiCad JST_XH_S8B-XH-A_1x08_P2.50mm_Horizontal), "
                  "pin field centred. XS3, the logic connector. The housing and cable run toward +Y in the unrotated part. " + BACK,
                  "connector JST XH side-entry 8way back TERMINAL-06", xh8, True, attr="through_hole")
idc = []
for j in range(5):
    idc.append(("pad", str(2 * j + 1), "thru_hole", "roundrect" if j == 0 else "circle", -1.27, -5.08 + 2.54 * j, 1.7, 1.7, 1.0,
                0.147059 if j == 0 else None))
    idc.append(("pad", str(2 * j + 2), "thru_hole", "circle", 1.27, -5.08 + 2.54 * j, 1.7, 1.7, 1.0, None))
idc += [("rect", -2.62, -10.68, 12.51, 10.68, "CrtYd", 0.05), ("rect", -1.59, -10.18, 12.01, 10.18, "Fab", 0.1)]
made += rotations("TS06_IDC_2x05_Horizontal_Back",
                  "IDC box header 2x05, 2.54 mm pitch, right-angle, through-hole (KiCad IDC-Header_2x05_P2.54mm_Horizontal), "
                  "pin field centred; odd pins in one row, even in the other. XS2, the ten-line cathode bus. The shroud and "
                  "ribbon run toward +X in the unrotated part. " + BACK,
                  "connector IDC 2x05 right-angle back TERMINAL-06", idc, True, attr="through_hole")

# ---------------------------------------------------------------- SOT-23, standard lands
# KiCad SOT-23: pads (-0.9375,-0.95) (-0.9375,0.95) (0.9375,0), 1.475 x 0.60; courtyard
# +-1.93 x +-1.70. Still hand-solderable with a fine tip, and it is the pattern that fits
# two abreast inside an IN-15 pin ring.
sot_std = [("pad", "1", "smd", "roundrect", -0.9375, -0.95, 1.475, 0.6, None, 0.25),
           ("pad", "2", "smd", "roundrect", -0.9375, 0.95, 1.475, 0.6, None, 0.25),
           ("pad", "3", "smd", "roundrect", 0.9375, 0, 1.475, 0.6, None, 0.25),
           ("rect", -1.93, -1.7, 1.93, 1.7, "CrtYd", 0.05), ("rect", -0.65, -1.45, 0.65, 1.45, "Fab", 0.1),
           ("line", -1.675, -1.55, -0.2, -1.55, "SilkS", 0.12)]
made += rotations("TS06_SOT-23_Std_Back",
                  "SOT-23, standard land pattern (KiCad SOT-23). For MMBTA42: pad 1 base, 2 emitter, 3 collector. "
                  "The silk bar marks pad 1. " + BACK, "SOT-23 MMBTA42 transistor SMD back TERMINAL-06", sot_std, True)

# ---------------------------------------------------------------- cable connectors, top entry, bodies on the back
# The mated plug points straight back from the board, so nothing hangs past an edge.
vhv = [("pad", "1", "thru_hole", "roundrect", -1.98, 0, 2.7, 2.7, 1.7, 0.092593),
       ("pad", "2", "thru_hole", "circle", 1.98, 0, 2.7, 2.7, 1.7, None),
       ("rect", -4.43, -4.2, 4.43, 5.3, "CrtYd", 0.05), ("rect", -3.93, -3.7, 3.93, 4.8, "Fab", 0.1)]
made += rotations("TS06_JST_VH_B2P-VH_Back",
                  "JST VH B2P-VH: 2-way, 3.96 mm pitch, top entry, through-hole (KiCad JST_VH_B2P-VH_1x02_P3.96mm_Vertical), "
                  "pin field centred. XS1, the 185 V feed: VH so it cannot mate with any 5 V XH plug. " + BACK,
                  "connector JST VH vertical HV back TERMINAL-06", vhv, True, attr="through_hole", rots=(0, 90))
xhv = [("pad", str(k + 1), "thru_hole", "roundrect" if k == 0 else "oval", -8.75 + 2.5 * k, 0, 1.7, 1.95, 0.95,
        0.147059 if k == 0 else None) for k in range(8)]
xhv += [("rect", -11.7, -2.85, 11.7, 3.9, "CrtYd", 0.05), ("rect", -11.2, -2.35, 11.2, 3.4, "Fab", 0.1)]
made += rotations("TS06_JST_XH_B8B-XH-A_Back",
                  "JST XH B8B-XH-A: 8-way, 2.50 mm pitch, top entry, through-hole (KiCad JST_XH_B8B-XH-A_1x08_P2.50mm_Vertical), "
                  "pin field centred. XS3, the logic connector. " + BACK,
                  "connector JST XH vertical 8way back TERMINAL-06", xhv, True, attr="through_hole", rots=(0, 90))
idcv = []
for j in range(5):
    idcv.append(("pad", str(2 * j + 1), "thru_hole", "roundrect" if j == 0 else "circle", -1.27, -5.08 + 2.54 * j, 1.7, 1.7, 1.0,
                 0.147059 if j == 0 else None))
    idcv.append(("pad", str(2 * j + 2), "thru_hole", "circle", 1.27, -5.08 + 2.54 * j, 1.7, 1.7, 1.0, None))
idcv += [("rect", -4.95, -10.68, 4.95, 10.68, "CrtYd", 0.05), ("rect", -4.45, -10.18, 4.45, 10.18, "Fab", 0.1)]
made += rotations("TS06_IDC_2x05_Vertical_Back",
                  "IDC box header 2x05, 2.54 mm pitch, top entry, through-hole (KiCad IDC-Header_2x05_P2.54mm_Vertical), "
                  "pin field centred; odd pins in one row, even in the other. XS2, the ten-line cathode bus. " + BACK,
                  "connector IDC 2x05 vertical back TERMINAL-06", idcv, True, attr="through_hole", rots=(0, 90))

# ---------------------------------------------------------------- 3 mm LED, front
# LED_D3.0mm: pad 1 (cathode) rect 1.8 at 0, pad 2 (anode) round 1.8 at 2.54, drill 0.9;
# courtyard -1.15..3.69 x +-2.21. Centred between the leads.
led = [("pad", "1", "thru_hole", "rect", -1.27, 0, 1.8, 1.8, 0.9, None),
       ("pad", "2", "thru_hole", "circle", 1.27, 0, 1.8, 1.8, 0.9, None),
       ("rect", -2.42, -2.21, 2.42, 2.21, "CrtYd", 0.05), ("circle", 0, 0, 1.5, "Fab", 0.1),
       ("line", -2.2, -1.2, -2.2, 1.2, "Fab", 0.1)]
made += rotations("TS06_LED_D3.0mm",
                  "3 mm through-hole LED (KiCad LED_D3.0mm), pads centred on the body: pad 1 cathode (square), pad 2 "
                  "anode. A 5 mm LED drops into the same holes; 3 mm is drawn because a 5.3 mm-tall body is what "
                  "clears the back of the fascia from this board's face.",
                  "LED 3mm THT front TERMINAL-06", led, False, attr="through_hole", rots=(0,))

print("wrote %d footprints:" % len(made))
print("  " + "\n  ".join(made))
