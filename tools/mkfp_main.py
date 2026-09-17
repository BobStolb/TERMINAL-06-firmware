#!/usr/bin/env python3
"""Generate the footprints TS06-MAIN adds to PCB/lib/TS06.pretty.

Same rules as tools/mkfp_sec.py, whose helpers are repeated here so that importing this
file never regenerates SEC's footprints:

  * LAND PATTERNS ARE NOT INVENTED. Every pad and courtyard number is KiCad 10's own library
    value, read out of the footprints installed with it on 17.09.26 - the KiCad name is in
    each description. Only the origin moves: every part is centred on its pin field.
  * BACK-SIDE PARTS are authored mirrored in X with graphics on B.* layers. That holds for
    the through-hole parts too: the whole board is populated from the back, so a DIP seen
    from the front is its own mirror image and its pin 1 sits where the mirror puts it.
  * NO ROTATION TOKENS: each orientation is its own footprint, _R90 = 90 deg counter-
    clockwise as seen from the front.
  * UUIDs are uuid5 of name and index: re-running reproduces every file byte for byte.

Pin numbering follows tools/ts06main.py: TO-92 pads are numbered by function (1 B, 2 E,
3 C) so that a transistor's schematic symbol serves both builds.

Regenerate with:  python3 tools/mkfp_main.py
"""
import os, uuid

VER, GEN, GENV = 20260206, "pcbnew", "10.0"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "PCB", "lib", "TS06.pretty")
NS = uuid.UUID("5ec06000-7506-4000-8000-00000000ba5e")


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
    """prims, in the library's own front-view orientation, centred on the pin field:
       ("pad", num, type, shape, x, y, w, h, drill, rratio)   drill: number, or (a, b) for oval
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
    ys, body = [], []
    for p in prims:
        if p[0] == "pad":
            _, pn, typ, shape, x, y, w, h, drill, rr = p
            X, Y = T(x, y)
            if rot in (90, 270):
                w, h = h, w
                if isinstance(drill, tuple):
                    drill = (drill[1], drill[0])
            if typ == "smd":
                extra = f'\n\t\t(layers "{side}Cu" "{side}Mask" "{side}Paste")'
            else:
                d = f"oval {num(drill[0])} {num(drill[1])}" if isinstance(drill, tuple) else num(drill)
                extra = f'\n\t\t(drill {d})\n\t\t(layers "*.Cu" "*.Mask")'
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
            if lk == "CrtYd":
                ys += [CY - r, CY + r]
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
    parts += body + ['\t(embedded_fonts no)', ')']
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name + ".kicad_mod"), "w", encoding="utf8", newline="\n") as fh:
        fh.write("\n".join(parts) + "\n")
    return name


def rotations(base, descr, tags, prims, back=True, attr="smd", rots=(0, 90, 180, 270)):
    made = []
    for r in rots:
        nm = base if r == 0 else f"{base}_R{r}"
        d = descr + ("" if r == 0 else f" Pre-rotated {r} deg counter-clockwise (front view), per this repo's no-rotation-token convention.")
        made.append(write(nm, d, tags, prims, back=back, rot=r, attr=attr))
    return made


BACK = ("Mounted on the BACK: geometry mirrored in X from the KiCad library original, graphics on B.* layers.")
THT = "through_hole"
made = []


def dip(n, pitch_x, name, kicad, extra_descr, body_half_w):
    """DIP-n with rows 2*pitch_x apart: pin 1 top-left, down the left row, up the right."""
    half = n // 2
    top = 1.27 * (half - 1)
    prims = []
    for k in range(half):
        y = -top + 2.54 * k
        prims.append(("pad", str(k + 1), "thru_hole", "roundrect" if k == 0 else "circle", -pitch_x, y, 1.6, 1.6, 0.8, 0.25 if k == 0 else None))
        prims.append(("pad", str(n - k), "thru_hole", "circle", pitch_x, y, 1.6, 1.6, 0.8, None))
    prims += [("rect", -pitch_x - 1.05, -top - 1.52, pitch_x + 1.05, top + 1.52, "CrtYd", 0.05),
              ("rect", -body_half_w, -top - 1.27, body_half_w, top + 1.27, "Fab", 0.1),
              ("line", -pitch_x - 0.8, -top - 1.3, -pitch_x + 0.8, -top - 1.3, "SilkS", 0.12)]
    return rotations(name, f"DIP-{n}, {2 * pitch_x:.2f} mm row spacing (KiCad {kicad}), pin field centred; pin 1 top-left "
                     f"in the library's front view, the silk bar marks it. {extra_descr} " + BACK,
                     f"DIP-{n} THT back TERMINAL-06", prims, attr=THT)


# ---------------------------------------------------------------- through-hole, both builds or the THT build
made += dip(16, 3.81, "TS06_DIP-16_Back", "DIP-16_W7.62mm", "For the К155ИД1 (both builds): 5 VCC, 12 GND, inputs 3 6 7 4 (A B C D), outputs 16 15 8 9 13 14 11 10 1 2 (Q0..Q9).", 3.175)
made += dip(4, 3.81, "TS06_DIP-4_Back", "DIP-4_W7.62mm", "For TLP627: 1 LED anode, 2 LED cathode, 3 emitter, 4 collector.", 3.175)
made += dip(8, 3.81, "TS06_DIP-8_Back", "DIP-8_W7.62mm", "For TC4420 (1/8 VDD, 2 IN, 4/5 GND, 6/7 OUT) and LM393.", 3.175)
made += dip(28, 7.62, "TS06_DIP-28W_Back", "DIP-28_W15.24mm", "For MCP23017-E/SP.", 6.985)

# TO-92, pads numbered by function to match SOT-23: E B C left to right in the library's front view.
to92 = [("pad", "2", "thru_hole", "rect", -1.27, 0, 1.05, 1.5, 0.75, None),
        ("pad", "1", "thru_hole", "oval", 0, 0, 1.05, 1.5, 0.75, None),
        ("pad", "3", "thru_hole", "oval", 1.27, 0, 1.05, 1.5, 0.75, None),
        ("rect", -2.73, -2.73, 2.73, 2.01, "CrtYd", 0.05), ("circle", 0, -0.36, 2.3, "Fab", 0.1),
        ("line", -1.9, 1.65, 1.9, 1.65, "Fab", 0.1), ("line", -2.0, 2.2, 2.0, 2.2, "SilkS", 0.12)]
made += rotations("TS06_TO-92_Back", "TO-92 in line (KiCad TO-92_Inline), centred on the middle lead, the flat face at +y "
                  "(silk bar). Pads numbered BY FUNCTION for MPSA42's E-B-C lead order: pad 2 emitter (square), pad 1 base "
                  "(middle), pad 3 collector - the same numbers as the SOT-23 MMBTA42, so one symbol serves both builds. " + BACK,
                  "TO-92 MPSA42 THT back TERMINAL-06", to92, attr=THT)

# TO-220 lying flat, tab down, leads bent 90 deg into the board; the tab's screw hole is a plain hole.
to220 = [("pad", "1", "thru_hole", "rect", -2.54, 0, 1.905, 2.0, 1.1, None),
         ("pad", "2", "thru_hole", "oval", 0, 0, 1.905, 2.0, 1.1, None),
         ("pad", "3", "thru_hole", "oval", 2.54, 0, 1.905, 2.0, 1.1, None),
         ("pad", "", "np_thru_hole", "circle", 0, -16.66, 3.5, 3.5, 3.5, None),
         ("rect", -5.25, -19.71, 5.25, 1.25, "CrtYd", 0.05), ("rect", -5.08, -19.2, 5.08, -3.3, "Fab", 0.1),
         ("line", -5.08, -3.3, -5.08, 0, "Fab", 0.1), ("line", 5.08, -3.3, 5.08, 0, "Fab", 0.1),
         ("line", -5.3, 1.2, -3.5, 1.2, "SilkS", 0.12)]
made += rotations("TS06_TO-220_Horizontal_Back", "TO-220 lying flat, tab down (KiCad TO-220-3_Horizontal_TabDown), centred on the "
                  "middle lead; the body runs toward -y and the 3.5 mm tab hole is unplated. For IRF840: 1 gate (square), 2 drain, "
                  "3 source. " + BACK, "TO-220 IRF840 THT back TERMINAL-06", to220, attr=THT)

# axial resistor, 12.7 mm pitch, for 0.5 W bodies
rax = [("pad", "1", "thru_hole", "rect", -6.35, 0, 2.0, 2.0, 1.0, None), ("pad", "2", "thru_hole", "circle", 6.35, 0, 2.0, 2.0, 1.0, None),
       ("rect", -7.4, -2.05, 7.4, 2.05, "CrtYd", 0.05), ("rect", -4.95, -1.8, 4.95, 1.8, "Fab", 0.1),
       ("line", -6.35, 0, -4.95, 0, "Fab", 0.1), ("line", 4.95, 0, 6.35, 0, "Fab", 0.1)]
made += rotations("TS06_R_Axial_P12.7mm_Back", "Axial resistor, 12.70 mm pitch, 0.5 W body (KiCad R_Axial_DIN0411_L9.9mm_D3.6mm_P12.70mm_Horizontal), "
                  "pin field centred. Anode series resistors, colon ballasts, the bleeder. " + BACK,
                  "resistor axial 12.7 THT back TERMINAL-06", rax, attr=THT, rots=(0, 90))

# axial resistor, 10.16 mm pitch, the 0.25 W body: the fascia's TS06_R_Axial_P10.16mm_Back has no
# rotated variants and is front-authored, so the main board gets its own family
rax10 = [("pad", "1", "thru_hole", "rect", -5.08, 0, 1.8, 1.8, 0.9, None), ("pad", "2", "thru_hole", "circle", 5.08, 0, 1.8, 1.8, 0.9, None),
         ("rect", -6.1, -1.6, 6.1, 1.6, "CrtYd", 0.05), ("rect", -3.3, -1.25, 3.3, 1.25, "Fab", 0.1),
         ("line", -5.08, 0, -3.3, 0, "Fab", 0.1), ("line", 3.3, 0, 5.08, 0, "Fab", 0.1)]
made += rotations("TS06_R_Axial_L6.3mm_P10.16mm_Back", "Axial resistor, 10.16 mm pitch, 0.25 W body 6.3 x 2.5 mm (KiCad "
                  "R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal), pin field centred, pad 1 square; same pads as the fascia's "
                  "TS06_R_Axial_P10.16mm_Back. " + BACK, "resistor axial 10.16 THT back TERMINAL-06", rax10, attr=THT, rots=(0, 90))

# upright axial resistors: the through-hole build has sixty-odd resistors and no room to lay
# them flat; standing up, a 0.25 W part takes 5.1 x 3.0 mm (KiCad R_Axial_DIN0207_L6.3mm_D2.5mm_P2.54mm_Vertical),
# a 0.5 W part 8.6 x 4.1 mm (R_Axial_DIN0411_L9.9mm_D3.6mm_P5.08mm_Vertical). Pad 1 is the body end (square).
rv25 = [("pad", "1", "thru_hole", "rect", -1.27, 0, 1.6, 1.6, 0.8, None), ("pad", "2", "thru_hole", "circle", 1.27, 0, 1.6, 1.6, 0.8, None),
        ("rect", -2.77, -1.5, 2.32, 1.5, "CrtYd", 0.05), ("circle", -1.27, 0, 1.25, "Fab", 0.1), ("line", -0.02, 0, 1.27, 0, "Fab", 0.1)]
made += rotations("TS06_R_Axial_L6.3mm_P2.54mm_Vertical_Back", "Axial 0.25 W resistor standing on end, 2.54 mm pitch (KiCad "
                  "R_Axial_DIN0207_L6.3mm_D2.5mm_P2.54mm_Vertical), pin field centred; pad 1 (square) is under the body. " + BACK,
                  "resistor axial vertical THT back TERMINAL-06", rv25, attr=THT, rots=(0, 90))
rv50 = [("pad", "1", "thru_hole", "rect", -2.54, 0, 2.4, 2.4, 1.2, None), ("pad", "2", "thru_hole", "circle", 2.54, 0, 2.4, 2.4, 1.2, None),
        ("rect", -4.59, -2.05, 3.99, 2.05, "CrtYd", 0.05), ("circle", -2.54, 0, 1.8, "Fab", 0.1), ("line", -0.74, 0, 2.54, 0, "Fab", 0.1)]
made += rotations("TS06_R_Axial_L9.9mm_P5.08mm_Vertical_Back", "Axial 0.5 W resistor standing on end, 5.08 mm pitch (KiCad "
                  "R_Axial_DIN0411_L9.9mm_D3.6mm_P5.08mm_Vertical), pin field centred; pad 1 (square) is under the body. Anode "
                  "series resistors, colon ballasts. " + BACK, "resistor axial vertical THT back TERMINAL-06", rv50, attr=THT, rots=(0, 90))

# ceramic discs
for pitch, cy, name, kicad in ((2.5, (2.3, 1.05, 1.5, 0.8), "TS06_C_Disc_P2.50mm_Back", "C_Disc_D3.0mm_W1.6mm_P2.50mm"),
                               (5.0, (3.55, 1.5, 2.5, 1.25), "TS06_C_Disc_P5.00mm_Back", "C_Disc_D5.0mm_W2.5mm_P5.00mm")):
    prims = [("pad", "1", "thru_hole", "circle", -pitch / 2, 0, 1.6, 1.6, 0.8, None), ("pad", "2", "thru_hole", "circle", pitch / 2, 0, 1.6, 1.6, 0.8, None),
             ("rect", -cy[0], -cy[1], cy[0], cy[1], "CrtYd", 0.05), ("rect", -cy[2], -cy[3], cy[2], cy[3], "Fab", 0.1)]
    made += rotations(name, f"Radial ceramic capacitor, {pitch:.2f} mm pitch (KiCad {kicad}), pin field centred. " + BACK,
                      "capacitor disc THT back TERMINAL-06", prims, attr=THT, rots=(0, 90))

# radial electrolytics: pad 1 positive (square)
for pitch, r, name, kicad, use in ((2.5, 3.3, "TS06_CP_Radial_D6.3mm_P2.50mm_Back", "CP_Radial_D6.3mm_P2.50mm", "100u 25V and 10u 50V"),
                                   (3.5, 4.15, "TS06_CP_Radial_D8.0mm_P3.50mm_Back", "CP_Radial_D8.0mm_P3.50mm", "the 4.7u 400V reservoir")):
    prims = [("pad", "1", "thru_hole", "roundrect", -pitch / 2, 0, 1.6, 1.6, 0.8, 0.25), ("pad", "2", "thru_hole", "circle", pitch / 2, 0, 1.6, 1.6, 0.8, None),
             ("circle", 0, 0, r, "CrtYd", 0.05), ("circle", 0, 0, r - 0.15, "Fab", 0.1),
             ("line", -r + 0.6, -r + 1.2, -r + 1.6, -r + 1.2, "SilkS", 0.12), ("line", -r + 1.1, -r + 0.7, -r + 1.1, -r + 1.7, "SilkS", 0.12)]
    made += rotations(name, f"Radial electrolytic, {pitch:.2f} mm pitch (KiCad {kicad}), centred; pad 1 positive (square), the silk "
                      f"+ marks it. For {use}. " + BACK, "capacitor electrolytic THT back TERMINAL-06", prims, attr=THT)

# radial inductor
lrad = [("pad", "1", "thru_hole", "circle", -2.5, 0, 2.6, 2.6, 1.3, None), ("pad", "2", "thru_hole", "circle", 2.5, 0, 2.6, 2.6, 1.3, None),
        ("circle", 0, 0, 5.15, "CrtYd", 0.05), ("circle", 0, 0, 5.0, "Fab", 0.1)]
made += rotations("TS06_L_Radial_D10.0mm_P5.00mm_Back", "Radial power choke, 10 mm body, 5.00 mm pitch (KiCad L_Radial_D10.0mm_P5.00mm_Fastron_07P), "
                  "centred. 220 uH, Isat 1.8 A or better. " + BACK, "inductor radial THT back TERMINAL-06", lrad, attr=THT, rots=(0, 90))

# axial diodes, pad 1 cathode (square), band at the cathode end
for pitch, pad, drill, cy, body, name, kicad, use in (
        (10.16, 2.2, 1.1, (6.45, 1.6), (2.6, 1.35), "TS06_D_DO-41_P10.16mm_Back", "D_DO-41_SOD81_P10.16mm_Horizontal", "HER106, the 185 V rectifier"),
        (15.24, 3.2, 1.6, (9.5, 2.85), (4.8, 2.65), "TS06_D_DO-201_P15.24mm_Back", "D_DO-201AD_P15.24mm_Horizontal", "1N5822, reverse-polarity protection")):
    prims = [("pad", "1", "thru_hole", "roundrect", -pitch / 2, 0, pad, pad, drill, 0.25), ("pad", "2", "thru_hole", "circle", pitch / 2, 0, pad, pad, drill, None),
             ("rect", -cy[0], -cy[1], cy[0], cy[1], "CrtYd", 0.05), ("rect", -body[0], -body[1], body[0], body[1], "Fab", 0.1),
             ("line", -body[0] + 0.7, -body[1], -body[0] + 0.7, body[1], "Fab", 0.15),
             ("line", -pitch / 2, 0, -body[0], 0, "Fab", 0.1), ("line", body[0], 0, pitch / 2, 0, "Fab", 0.1),
             ("line", -body[0] + 0.7, -body[1] - 0.3, -body[0] + 0.7, body[1] + 0.3, "SilkS", 0.2)]
    made += rotations(name, f"Axial diode, {pitch:.2f} mm pitch (KiCad {kicad}), centred; pad 1 cathode (square), the band. For {use}. " + BACK,
                      "diode axial THT back TERMINAL-06", prims, attr=THT)

# radial PTC fuse, Bourns MF-R pattern (the leads sit 5.1 mm apart and 1.2 mm staggered)
fuse = [("pad", "1", "thru_hole", "circle", -2.55, -0.6, 2.01, 2.01, 1.01, None), ("pad", "2", "thru_hole", "circle", 2.55, 0.6, 2.01, 2.01, 1.01, None),
        ("rect", -4.0, -2.9, 4.0, 2.9, "CrtYd", 0.05), ("rect", -3.7, -1.5, 3.7, 1.5, "Fab", 0.1)]
made += rotations("TS06_Fuse_Radial_MF-R_Back", "Radial PTC resettable fuse, Bourns MF-R lead pattern (KiCad Fuse_Bourns_MF-RHT300 holes), "
                  "centred. MF-R110 or similar, 1.1 A hold. " + BACK, "fuse PTC THT back TERMINAL-06", fuse, attr=THT, rots=(0, 90))

# Bourns 3296W multi-turn trimmer, pins in line
trim = [("pad", "1", "thru_hole", "rect", 2.54, 0, 1.6, 1.6, 0.8, None), ("pad", "2", "thru_hole", "circle", 0, 0, 1.6, 1.6, 0.8, None),
        ("pad", "3", "thru_hole", "circle", -2.54, 0, 1.6, 1.6, 0.8, None),
        ("rect", -5.02, -2.67, 5.02, 2.67, "CrtYd", 0.05), ("rect", -4.8, -2.4, 4.8, 2.4, "Fab", 0.1),
        ("line", 3.4, -2.9, 4.8, -2.9, "SilkS", 0.12)]
made += rotations("TS06_Trimmer_3296W_Back", "Bourns 3296W 25-turn trimmer (KiCad Potentiometer_Bourns_3296W_Vertical), centred; pin 1 square, "
                  "pin 2 the wiper. " + BACK, "trimmer 3296W THT back TERMINAL-06", trim, attr=THT)

# 5-way 2.54 header for the DS3231 mini module
hdr = [("pad", str(k + 1), "thru_hole", "rect" if k == 0 else "circle", 0, -5.08 + 2.54 * k, 1.7, 1.7, 1.0, None) for k in range(5)]
hdr += [("rect", -1.77, -6.85, 1.77, 6.85, "CrtYd", 0.05), ("rect", -1.27, -6.35, 1.27, 6.35, "Fab", 0.1), ("line", -1.9, -6.9, -1.9, -4.5, "SilkS", 0.12)]
made += rotations("TS06_PinHeader_1x05_Back", "1x05 2.54 mm header (KiCad PinHeader_1x05_P2.54mm_Vertical), centred; pin 1 square. The DS3231 "
                  "mini module plugs on here: 1 -, 2 NC, 3 C, 4 D, 5 +. " + BACK, "header 1x05 THT back TERMINAL-06", hdr, attr=THT, rots=(0, 90))

# Arduino Nano on two 15-way rows 15.24 mm apart; the USB connector overhangs the +y end
nano = []
for k in range(15):
    nano.append(("pad", str(k + 1), "thru_hole", "rect" if k == 0 else "oval", -7.62, -17.78 + 2.54 * k, 1.6, 1.6, 1.0, None))
    nano.append(("pad", str(30 - k), "thru_hole", "oval", 7.62, -17.78 + 2.54 * k, 1.6, 1.6, 1.0, None))
nano += [("rect", -9.14, -21.84, 9.14, 24.38, "CrtYd", 0.05), ("rect", -8.9, -21.6, 8.9, 21.6, "Fab", 0.1),
         ("rect", -3.8, 20.0, 3.8, 24.1, "Fab", 0.1), ("line", -9.3, -21.8, -9.3, -19.0, "SilkS", 0.12), ("line", -4.0, 24.3, 4.0, 24.3, "SilkS", 0.12)]
made += rotations("TS06_Arduino_Nano_Back", "Arduino Nano on headers (KiCad Module:Arduino_Nano), centred on the pin field: pads 1-15 down one "
                  "row (D1/TX, D0/RX, RESET, GND, D2..D12), 16-30 up the other (D13, 3V3, AREF, A0..A7, +5V, RESET, GND, VIN). Pin 1 square. "
                  "The USB connector is at the +y end, past pads 15/16, and must reach a case opening. " + BACK,
                  "Arduino Nano module THT back TERMINAL-06", nano, attr=THT)

# Recom R-78E SIP-3
reg = [("pad", "1", "thru_hole", "rect", -2.54, 0, 1.5, 2.3, 1.0, None), ("pad", "2", "thru_hole", "oval", 0, 0, 1.5, 2.3, 1.0, None),
       ("pad", "3", "thru_hole", "oval", 2.54, 0, 1.5, 2.3, 1.0, None),
       ("rect", -6.11, -6.75, 6.0, 2.25, "CrtYd", 0.05), ("rect", -5.8, -6.5, 5.8, 2.0, "Fab", 0.1), ("line", -3.5, 2.5, -1.6, 2.5, "SilkS", 0.12)]
made += rotations("TS06_R78E_SIP3_Back", "Recom R-78E5.0-1.0 switching regulator, SIP-3 (KiCad Converter_DCDC_RECOM_R-78E-0.5_THT), centred: "
                  "1 Vin (square), 2 GND, 3 Vout; the body stands toward -y. " + BACK, "regulator R-78E SIP-3 THT back TERMINAL-06", reg, attr=THT)

# DC barrel jack, 5.5 x 2.1 mm (DC-005 class): the plug enters from -x in the library's front view
jack = [("pad", "1", "thru_hole", "rect", 3.0, 0, 3.5, 3.5, (1.0, 3.0), None),
        ("pad", "2", "thru_hole", "roundrect", -3.0, 0, 3.0, 3.5, (1.0, 3.0), 0.25),
        ("pad", "3", "thru_hole", "roundrect", 0, 4.7, 3.5, 3.5, (3.0, 1.0), 0.25),
        ("rect", -11.0, -4.75, 5.0, 6.75, "CrtYd", 0.05), ("rect", -10.5, -4.5, 4.5, 4.5, "Fab", 0.1),
        ("line", -10.5, -4.5, -10.5, 4.5, "Fab", 0.3), ("line", 3.5, -4.9, 5.2, -4.9, "SilkS", 0.12)]
made += rotations("TS06_BarrelJack_Back", "DC barrel jack 5.5 x 2.1 mm, horizontal (KiCad BarrelJack_Horizontal), centred between pins 1 and 2: "
                  "1 centre pin (square), 2 sleeve, 3 the sleeve's break contact. The plug enters from -x in the library's front view "
                  "(the thick Fab line is the mouth); after mirroring it enters from +x. " + BACK,
                  "connector barrel jack DC THT back TERMINAL-06", jack, attr=THT)

# ---------------------------------------------------------------- surface-mount, the SMD build
def so(name, kicad, n, px, py0, pw, cy, body, use):
    half = n // 2
    prims = [("pad", str(k + 1), "smd", "roundrect", -px, py0 + 1.27 * k, pw, 0.6, None, 0.25) for k in range(half)]
    prims += [("pad", str(n - k), "smd", "roundrect", px, py0 + 1.27 * k, pw, 0.6, None, 0.25) for k in range(half)]
    prims += [("rect", -cy[0], -cy[1], cy[0], cy[1], "CrtYd", 0.05), ("rect", -body[0], -body[1], body[0], body[1], "Fab", 0.1),
              ("line", -px - pw / 2, py0 - 0.9, -body[0] - 0.2, py0 - 0.9, "SilkS", 0.12)]
    return rotations(name, f"{kicad}, pin field centred, pin 1 top-left in the front view (silk bar). {use} " + BACK,
                     f"SOIC SMD back TERMINAL-06", prims)


made += so("TS06_SOIC-8_Back", "SOIC-8 3.9 x 4.9 mm (KiCad SOIC-8_3.9x4.9mm_P1.27mm)", 8, 2.475, -1.905, 1.95, (3.7, 2.7), (1.95, 2.45),
           "For TC4420 and LM393.")
made += so("TS06_SOIC-16W_Back", "SOIC-16 wide 7.5 x 10.3 mm (KiCad SOIC-16W_7.5x10.3mm_P1.27mm)", 16, 4.65, -4.445, 2.05, (5.93, 5.4), (3.75, 5.15),
           "For DS3231SN: 2 VCC, 13 GND, 14 VBAT, 15 SDA, 16 SCL.")

d2pak = [("pad", "1", "smd", "roundrect", -7.65, -2.54, 4.6, 1.1, None, 0.25), ("pad", "2", "smd", "roundrect", 1.5, 0, 9.4, 10.8, None, 0.05),
         ("pad", "3", "smd", "roundrect", -7.65, 2.54, 4.6, 1.1, None, 0.25),
         ("rect", -10.2, -5.65, 6.45, 5.65, "CrtYd", 0.05), ("rect", -3.2, -4.95, 6.2, 4.95, "Fab", 0.1), ("line", -10.0, -3.4, -8.0, -3.4, "SilkS", 0.12)]
made += rotations("TS06_TO-263-2_Back", "D2PAK / TO-263-2 (KiCad TO-263-2), the tab pad on the +x side: 1 gate, 2 drain (tab), 3 source. "
                  "For IRF840S. " + BACK, "TO-263 D2PAK MOSFET SMD back TERMINAL-06", d2pak)

sma = [("pad", "1", "smd", "roundrect", -2.0, 0, 2.5, 1.8, None, 0.25), ("pad", "2", "smd", "roundrect", 2.0, 0, 2.5, 1.8, None, 0.25),
       ("rect", -3.5, -1.75, 3.5, 1.75, "CrtYd", 0.05), ("rect", -2.3, -1.4, 2.3, 1.4, "Fab", 0.1),
       ("line", -1.6, -1.4, -1.6, 1.4, "Fab", 0.15), ("line", -3.4, -1.55, -3.4, 1.55, "SilkS", 0.2)]
made += rotations("TS06_D_SMA_Back", "SMA / DO-214AC diode (KiCad D_SMA), centred; pad 1 cathode, the band. For US1J (185 V rectifier) and "
                  "SS34 (input protection). " + BACK, "diode SMA SMD back TERMINAL-06", sma)

for px, cy, body, name, kicad, use in ((3.7, (6.15, 4.5), 4.15, "TS06_CP_Elec_8x10.5_Back", "CP_Elec_8x10.5", "100u 25V and 10u 50V"),
                                       (4.2, (6.65, 5.5), 5.15, "TS06_CP_Elec_10x10.5_Back", "CP_Elec_10x10.5", "the 4.7u 400V reservoir")):
    prims = [("pad", "1", "smd", "roundrect", -px, 0, 4.4, 2.5, None, 0.25), ("pad", "2", "smd", "roundrect", px, 0, 4.4, 2.5, None, 0.25),
             ("rect", -cy[0], -cy[1], cy[0], cy[1], "CrtYd", 0.05), ("rect", -body, -body, body, body, "Fab", 0.1), ("circle", 0, 0, body - 0.2, "Fab", 0.1),
             ("line", -body - 0.8, -body + 0.6, -body - 0.8, -body + 1.6, "SilkS", 0.12), ("line", -body - 1.3, -body + 1.1, -body - 0.3, -body + 1.1, "SilkS", 0.12)]
    made += rotations(name, f"SMD aluminium electrolytic, {kicad} (KiCad {kicad}), centred; pad 1 positive, the silk + marks it. For {use}. " + BACK,
                      "capacitor electrolytic SMD back TERMINAL-06", prims)

l12 = [("pad", "1", "smd", "rect", -4.95, 0, 2.9, 5.4, None, None), ("pad", "2", "smd", "rect", 4.95, 0, 2.9, 5.4, None, None),
       ("rect", -6.86, -6.6, 6.86, 6.6, "CrtYd", 0.05), ("rect", -6.0, -6.0, 6.0, 6.0, "Fab", 0.1)]
made += rotations("TS06_L_12x12mm_Back", "12 x 12 mm shielded power inductor (KiCad L_12x12mm_H8mm), centred. 220 uH, Isat 1.8 A or better "
                  "(Bourns SRR1280-221 class). " + BACK, "inductor 12x12 SMD back TERMINAL-06", l12, rots=(0, 90))

f1812 = [("pad", "1", "smd", "roundrect", -2.1375, 0, 1.125, 3.4, None, 0.25), ("pad", "2", "smd", "roundrect", 2.1375, 0, 1.125, 3.4, None, 0.25),
         ("rect", -2.95, -1.95, 2.95, 1.95, "CrtYd", 0.05), ("rect", -2.25, -1.6, 2.25, 1.6, "Fab", 0.1)]
made += rotations("TS06_Fuse_1812_Back", "1812 PTC resettable fuse (KiCad Fuse_1812_4532Metric), centred. 1.1 A hold. " + BACK,
                  "fuse PTC 1812 SMD back TERMINAL-06", f1812, rots=(0, 90))

t3224 = [("pad", "1", "smd", "roundrect", 1.25, -1.45, 1.3, 1.6, None, 0.25), ("pad", "2", "smd", "roundrect", 0, 1.45, 2.0, 1.6, None, 0.25),
         ("pad", "3", "smd", "roundrect", -1.25, -1.45, 1.3, 1.6, None, 0.25),
         ("rect", -2.65, -2.5, 2.65, 2.5, "CrtYd", 0.05), ("rect", -2.4, -2.25, 2.4, 2.25, "Fab", 0.1), ("line", 1.0, -2.7, 2.2, -2.7, "SilkS", 0.12)]
made += rotations("TS06_Trimmer_3224W_Back", "Bourns 3224W SMD multi-turn trimmer (KiCad Potentiometer_Bourns_3224W_Vertical), centred; "
                  "pins 1 and 3 the ends, 2 the wiper. " + BACK, "trimmer 3224W SMD back TERMINAL-06", t3224)

batt = [("pad", "1", "smd", "rect", -10.985, 0, 1.27, 5.08, None, None), ("pad", "1", "smd", "rect", 10.985, 0, 1.27, 5.08, None, None),
        ("pad", "2", "smd", "circle", 0, 0, 17.8, 17.8, None, None),
        ("rect", -11.87, -7.64, 11.87, 7.64, "CrtYd", 0.05), ("circle", 0, 0, 10.0, "Fab", 0.1), ("rect", -11.6, -2.6, 11.6, 2.6, "Fab", 0.1)]
made += rotations("TS06_BatteryHolder_3034_Back", "Keystone 3034 SMD holder for a 20 mm coin cell (KiCad BatteryHolder_Keystone_3034_1x20mm), "
                  "centred: the two side tabs are pad 1, positive; the centre disc pad 2, negative. CR2032 for the DS3231. " + BACK,
                  "battery holder CR2032 SMD back TERMINAL-06", batt, rots=(0, 90))

print("wrote %d footprints:" % len(made))
print("  " + "\n  ".join(made))
