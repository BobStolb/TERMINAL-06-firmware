#!/usr/bin/env python3
"""Generate the TS06-FASCIA symbol library and schematic for KiCad 10.

Regenerate with:  python3 tools/mksch.py
Format tokens captured from a real KiCad 10.0 save, 08.09.26:
  .kicad_sym / .kicad_sch = version 20260306, generator_version "10.0"

DESIGN NOTE - why there are no power symbols in here.
This board has no power source. Every net leaves through J1. So +5V and GND are
ordinary local labels, not power ports: there is nothing on the panel for a power
flag to describe, and it keeps ERC honest instead of decorative.
"""
import os, sys, uuid

SV, GV = 20260306, "10.0"
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
LIB  = os.path.join(ROOT, "PCB", "lib", "TS06.kicad_sym")
# One netlist, two builds. "--tht" writes the same schematic against the through-hole
# footprints, so the two boards can never drift apart in what they connect - only in
# how they are made.
THT  = "--tht" in sys.argv
BOARD = "TS06-FASCIA-THT" if THT else "TS06-FASCIA"
SCH  = os.path.join(ROOT, "PCB", BOARD, BOARD + ".kicad_sch")
SHEET_UUID = "d3920db2-8aa4-4b4d-8e8a-771392dad286"   # from KiCad's own skeleton save

def U(): return str(uuid.uuid4())
def eff(sz=1.27, hide=False, just=None):
    j = f"\n(justify {just})" if just else ""
    h = "\n(hide yes)" if hide else ""
    return f"(effects\n(font\n(size {sz} {sz})\n){j}{h}\n)"

def prop(k, v, x, y, hide=False, just=None):
    return f'(property "{k}" "{v}"\n(at {x} {y} 0)\n{eff(1.27, hide, just)}\n)'

def pin(typ, x, y, rot, ln, name, num):
    return (f'(pin {typ} line\n(at {x} {y} {rot})\n(length {ln})\n'
            f'(name "{name}"\n{eff(1.27)}\n)\n(number "{num}"\n{eff(1.27)}\n)\n)')

def rect(x1, y1, x2, y2, fill="none"):
    return (f'(rectangle\n(start {x1} {y1})\n(end {x2} {y2})\n'
            f'(stroke\n(width 0.254)\n(type default)\n)\n(fill\n(type {fill})\n)\n)')

def poly(pts, w=0.254, fill="none"):
    p = "\n".join(f"(xy {a} {b})" for a, b in pts)
    return (f'(polyline\n(pts\n{p}\n)\n(stroke\n(width {w})\n(type default)\n)\n'
            f'(fill\n(type {fill})\n)\n)')

def circ(x, y, r, w=0.254, fill="none"):
    return (f'(circle\n(center {x} {y})\n(radius {r})\n(stroke\n(width {w})\n'
            f'(type default)\n)\n(fill\n(type {fill})\n)\n)')

def symbol(name, ref, val, fp, descr, graphics, pins, ref_y=2.54, val_y=-2.54):
    g = "\n".join(graphics); p = "\n".join(pins)
    return (f'(symbol "{name}"\n(pin_names\n(offset 0.254)\n)\n(exclude_from_sim no)\n'
            f'(in_bom yes)\n(on_board yes)\n'
            f'{prop("Reference", ref, 0, ref_y)}\n{prop("Value", val, 0, val_y)}\n'
            f'{prop("Footprint", fp, 0, 0, hide=True)}\n'
            f'{prop("Datasheet", "", 0, 0, hide=True)}\n'
            f'{prop("Description", descr, 0, 0, hide=True)}\n'
            f'(symbol "{name}_0_1"\n{g}\n)\n(symbol "{name}_1_1"\n{p}\n)\n)')

# ------------------------------------------------------------------ symbols
SYMS = {}

SYMS["R"] = symbol("R", "R", "R",
    "TS06:TS06_R_1206_HandSolder",
    "Resistor",
    [rect(-1.016, -2.54, 1.016, 2.54)],
    [pin("passive", 0, 3.81, 270, 1.27, "~", "1"),
     pin("passive", 0, -3.81, 90, 1.27, "~", "2")])

# Rotary: 6 taps spaced 12.7 to sit directly opposite the ladder nodes.
tapy = [-31.75, -19.05, -6.35, 6.35, 19.05, 31.75]      # T1 (0V) at bottom -> T6 (5V) at top
g = [rect(-5.08, -38.1, 5.08, 38.1)]
g += [circ(4.318, y, 0.508) for y in tapy]              # tap contacts
g += [circ(-4.318, 0, 0.508)]                           # wiper hub
g += [poly([(-4.318, 0), (3.556, 25.4)], 0.254)]        # wiper arm, drawn on T5
pins = [pin("passive", 10.16, y, 180, 5.08, f"T{i+1}", str(i + 1)) for i, y in enumerate(tapy)]
pins += [pin("passive", -10.16, 0, 0, 5.08, "COM", "7")]
SYMS["SW_Rotary_6P1W"] = symbol("SW_Rotary_6P1W", "SW", "SR25 6P",
    "TS06:TS06_Rotary_SR25_PanelMount",
    "SR25-style 6-position galette rotary, one pole of two. 12 taps on D19.99 at 30deg; "
    "only pole 1 (COM + T1..T6) is wired. Pole 2 is spare.",
    g, pins, 41.91, -41.91)

# MT1 lever, used as SPST: 2 of its 3 lugs.
g = [circ(-2.54, 0, 0.508), circ(2.54, 0, 0.508), poly([(-2.286, 0.762), (2.794, 3.302)], 0.254)]
SYMS["SW_Lever_MT1"] = symbol("SW_Lever_MT1", "SW", "MT1",
    "TS06:TS06_MT1_Lever_PanelMount",
    "MT1/TV1-2 toggle lever wired as SPST - 2 of its 3 lugs used.",
    g, [pin("passive", -7.62, 0, 0, 5.08, "A", "1"),
        pin("passive", 7.62, 0, 180, 5.08, "B", "2")], 5.08, -5.08)

# KMD1 momentary button, normally open.
g = [circ(-2.54, 0, 0.508), circ(2.54, 0, 0.508),
     poly([(-2.54, 1.27), (2.54, 1.27)], 0.254), poly([(0, 1.27), (0, 3.302)], 0.254),
     poly([(-1.524, 3.302), (1.524, 3.302)], 0.254)]
SYMS["SW_Button_KMD1"] = symbol("SW_Button_KMD1", "SW", "KMD1",
    "TS06:TS06_KMD1_Button_PanelMount",
    "KMD1-1 momentary pushbutton, normally open. Shorts to GND; the Nano supplies "
    "the pull-up (GyverButton INPUT_PULLUP).",
    g, [pin("passive", -7.62, 0, 0, 5.08, "1", "1"),
        pin("passive", 7.62, 0, 180, 5.08, "2", "2")], 6.35, -3.81)

# 6-pin panel connector. ONE pin order for both builds of this board, so one harness
# fits either: 1 +5V, 2 GND, 3 A6, 4 A7, 5 D7, 6 D8 - power first, then the four MCU
# pins in their own order. It replaces the order the surface-mount routing happened to
# want (D8, D7, GND, A7, +5V, A6), which was an artefact of one layout and would have
# made the two variants need different cables.
NM = ["+5V", "GND", "A6", "A7", "D7", "D8"]
g = [rect(-2.54, -13.97, 2.54, 3.81)]
g += [rect(1.27, -1.27 - 2.54 * i + 0.635, 2.54, -1.27 - 2.54 * i - 0.635) for i in range(6)]
pins = [pin("passive", 7.62, -1.27 - 2.54 * i, 180, 5.08, NM[i], str(i + 1)) for i in range(6)]
SYMS["Conn_JST_PH_6"] = symbol("Conn_JST_PH_6", "J", "PH 6 SMT",
    "TS06:TS06_JST_PH_S6B-PH-SM4-TB_Back",
    "Panel cable to the main board. Pin order follows the PCB: D8, D7, GND, A7, +5V, A6 - each net on the pin nearest where it arrives from.",
    g, pins, 6.35, -16.51)

def qualify(txt, name):
    """Inside a .kicad_sch, lib_symbols entries are named with the FULL lib_id
    ("TS06:R"), while a .kicad_sym file names them bare ("R"). Getting this wrong
    makes KiCad draw every part as a red "??" placeholder - it cannot match the
    instance's lib_id to any cached definition."""
    for suffix in ('"', '_0_1"', '_1_1"'):
        txt = txt.replace(f'(symbol "{name}{suffix}', f'(symbol "TS06:{name}{suffix}')
    return txt

SYMS_SCH = {n: qualify(t, n) for n, t in SYMS.items()}

open(LIB, "w", encoding="utf8").write(
    f'(kicad_symbol_lib\n(version {SV})\n(generator "kicad_symbol_editor")\n'
    f'(generator_version "{GV}")\n' + "\n".join(SYMS.values()) + "\n)\n")
print("wrote", os.path.relpath(LIB, ROOT))

# ------------------------------------------------------------------ schematic
items, insts = [], []

def place(lib, ref, val, x, y, rot=0, fp=None, extra=None):
    npins = {"R": 2, "SW_Rotary_6P1W": 7, "SW_Lever_MT1": 2,
             "SW_Button_KMD1": 2, "Conn_JST_PH_6": 6}[lib]
    fpline = f'{prop("Footprint", fp, x, y, hide=True)}\n' if fp else ""
    ex = ("\n".join(prop(k, v, x, y, hide=True) for k, v in (extra or {}).items()) + "\n") if extra else ""
    pn = "\n".join(f'(pin "{i+1}"\n(uuid "{U()}")\n)' for i in range(npins))
    items.append(
        f'(symbol\n(lib_id "TS06:{lib}")\n(at {x} {y} {rot})\n(unit 1)\n'
        f'(exclude_from_sim no)\n(in_bom yes)\n(on_board yes)\n(dnp no)\n'
        f'(fields_autoplaced yes)\n(uuid "{U()}")\n'
        f'{prop("Reference", ref, x + 3.81, y - 1.27, just="left")}\n'
        f'{prop("Value", val, x + 3.81, y + 1.27, just="left")}\n{fpline}{ex}'
        f'{pn}\n(instances\n(project "TS06-FASCIA"\n(path "/{SHEET_UUID}"\n'
        f'(reference "{ref}")\n(unit 1)\n)\n)\n)\n)')

def wire(x1, y1, x2, y2):
    items.append(f'(wire\n(pts\n(xy {x1} {y1})\n(xy {x2} {y2})\n)\n'
                 f'(stroke\n(width 0)\n(type default)\n)\n(uuid "{U()}")\n)')

def junc(x, y):
    items.append(f'(junction\n(at {x} {y})\n(diameter 0)\n(color 0 0 0 0)\n(uuid "{U()}")\n)')

def label(t, x, y, rot=0, just="left bottom"):
    items.append(f'(label "{t}"\n(at {x} {y} {rot})\n(fields_autoplaced yes)\n'
                 f'{eff(1.27, just=just)}\n(uuid "{U()}")\n)')

def note(t, x, y, sz=1.27):
    items.append(f'(text "{t}"\n(exclude_from_sim no)\n(at {x} {y} 0)\n{eff(sz)}\n(uuid "{U()}")\n)')

LX = 88.9                                   # ladder column
NY = [139.7, 127.0, 114.3, 101.6, 88.9, 76.2]   # T1 (GND) .. T6 (+5V)

# --- A6: rotary + tapped divider -------------------------------------------
if THT:
    FP = {"SW1": "TS06:TS06_Rotary_SR25_THT",
          "SW2": "TS06:TS06_MT1_Lever_THT", "SW3": "TS06:TS06_MT1_Lever_THT",
          "SW4": "TS06:TS06_KMD1_Button_THT", "SW5": "TS06:TS06_KMD1_Button_THT",
          "J1": "TS06:TS06_JST_PH_S6B-PH-K-S_Back"}
    for _r in range(1, 6): FP[f"R{_r}"] = "TS06:TS06_R_Axial_P10.16mm_Front"
    for _r in range(6, 9): FP[f"R{_r}"] = "TS06:TS06_R_Axial_P10.16mm_Back"
else:
    FP = {"SW1": "TS06:TS06_Rotary_SR25_PanelMount",
          "SW2": "TS06:TS06_MT1_Lever_PanelMount", "SW3": "TS06:TS06_MT1_Lever_PanelMount",
          "SW4": "TS06:TS06_KMD1_Button_PanelMount", "SW5": "TS06:TS06_KMD1_Button_PanelMount",
          "J1": "TS06:TS06_JST_PH_S6B-PH-SM4-TB_Back"}
    for _r in range(1, 9): FP[f"R{_r}"] = "TS06:TS06_R_1206_HandSolder"

place("SW_Rotary_6P1W", "SW1", "SR25 6-pos", 63.5, 107.95, fp=FP["SW1"])
for i in range(5):                          # R1..R5, 4.7k 1%, between adjacent nodes
    cy = (NY[i] + NY[i + 1]) / 2
    place("R", f"R{i+1}", "4.7k 1%", LX, cy, fp=FP[f"R{i+1}"])
    wire(LX, NY[i], LX, cy + 3.81)
    wire(LX, cy - 3.81, LX, NY[i + 1])
for i, y in enumerate(NY):                  # taps out to the switch
    wire(73.66, y, LX, y)
    if 0 < i < 5:
        junc(LX, y)
for _t in range(1, 5):
    label(f"TAP{_t+1}", 81.0, NY[_t], 0, "left bottom")
wire(53.34, 107.95, 45.72, 107.95); label("A6", 45.72, 107.95, 180, "right bottom")
wire(LX, NY[0], LX, 146.05); label("GND", LX, 146.05, 270, "left bottom")
wire(LX, NY[5], LX, 69.85);  label("+5V", LX, 69.85, 90, "left bottom")

# --- A7: two levers, binary weighted ---------------------------------------
AX, AY = 152.4, 107.95
place("R", "R6", "10k", AX, 95.25, fp=FP["R6"])          # pull-up
wire(AX, AY, AX, 99.06); wire(AX, 91.44, AX, 83.82)
label("+5V", AX, 83.82, 90, "left bottom")
wire(139.7, AY, 175.26, AY); junc(AX, AY)
label("A7", 175.26, AY, 0, "left bottom")
SWC, RC = 118.11, 130.81          # lever centre, resistor centre
SW_HALF, R_HALF = 7.62, 3.81      # pin reach from centre - different parts, different reach
for x, sw, rn, rv, nm in ((139.7, "SW2", "R7", "20k", "LEVER A"),
                          (165.1, "SW3", "R8", "10k", "LEVER B")):
    place("SW_Lever_MT1", sw, nm, x, SWC, 90, fp=FP[sw])
    place("R", rn, rv, x, RC, fp=FP[rn])
    wire(x, AY, x, SWC - SW_HALF)                 # A7 node down to the lever
    wire(x, SWC + SW_HALF, x, RC - R_HALF)        # lever down to its resistor
    label("LEVA" if sw == "SW2" else "LEVB", x, (SWC + SW_HALF + RC - R_HALF) / 2,
          0, "left bottom")
    wire(x, RC + R_HALF, x, 139.7)                # resistor down to ground
    label("GND", x, 139.7, 270, "left bottom")
junc(165.1, AY)

# --- Buttons ----------------------------------------------------------------
for x, sw, net, nm in ((201.93, "SW4", "D7", "MINUS"), (227.33, "SW5", "D8", "PLUS")):
    place("SW_Button_KMD1", sw, nm, x, 107.95, 90, fp=FP[sw])
    wire(x, 100.33, x, 93.98); label(net, x, 93.98, 90, "left bottom")
    wire(x, 115.57, x, 121.92); label("GND", x, 121.92, 270, "left bottom")

# --- Connector --------------------------------------------------------------
JX, JY = 238.76, 80.01
place("Conn_JST_PH_6", "J1", "PH 6 THT" if THT else "PH 6 SMT", JX, JY, fp=FP["J1"])
for i, n in enumerate(NM):
    y = JY + 1.27 + 2.54 * i        # symbol pin i is at symbol-y -(1.27 + 2.54i)
    wire(JX + 7.62, y, JX + 17.78, y)
    label(n, JX + 17.78, y, 0, "left bottom")

note("TS06-FASCIA  -  control panel and product face", 25.4, 33.02, 2.54)
note("Five controls, six wires. The ladder is why.", 25.4, 38.1, 1.27)
note("A6: five 4.7k 1% across +5V/GND, wiper picks a node. 23.5k string, 213uA,\\n"
     "worst source Z 5.64k (ADC wants <10k). Taps land on 0/1/2/3/4/5 V ->\\n"
     "ADC 0/205/409/614/818/1023, worst gap 204 codes.", 25.4, 45.72)
note("A7: 10k pull-up, 20k and 10k to ground. Four states at ADC\\n"
     "1023 / 682 / 512 / 409, worst gap 103 codes.", 25.4, 58.42)
note("NOT on this board: the two 100nF filter caps. They go at the MAIN BOARD end\\n"
     "of the cable, where they hold the last value if a non-shorting wiper floats\\n"
     "and filter what the cable picks up passing a converter switching 185V at 31kHz.", 152.4, 45.72)
note("Every switch is panel-mount with solder lugs sitting >=11.3mm BEHIND this\\n"
     "board, pointing away. Nothing here is board-mounted; all are hand-wired to\\n"
     "landing pads. Pole 2 of the rotary is spare and unwired.", 152.4, 58.42)

open(SCH, "w", encoding="utf8").write(
    f'(kicad_sch\n(version {SV})\n(generator "eeschema")\n(generator_version "{GV}")\n'
    f'(uuid "{SHEET_UUID}")\n(paper "A4")\n'
    f'(title_block\n(title "TS06-FASCIA - control panel and product face")\n'
    f'(date "2026-09-08")\n(rev "A")\n(company "TERMINAL-06")\n'
    f'(comment 1 "Five controls, six wires. Generated by tools/mksch.py")\n'
    f'(comment 2 "Dimensions from the calipered FreeCAD models in 3d/")\n)\n'
    f'(lib_symbols\n'
    + "\n".join(SYMS_SCH.values()) + "\n)\n" + "\n".join(items)
    + f'\n(sheet_instances\n(path "/"\n(page "1")\n)\n)\n(embedded_fonts no)\n)\n')
print("wrote", os.path.relpath(SCH, ROOT))
