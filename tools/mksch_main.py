#!/usr/bin/env python3
"""Generate the TS06-MAIN symbol library and the schematic of either build.

    python3 tools/mksch_main.py          # PCB/TS06-MAIN/TS06-MAIN.kicad_sch (surface-mount build)
    python3 tools/mksch_main.py --tht    # PCB/TS06-MAIN-THT/TS06-MAIN-THT.kicad_sch

The netlist is tools/ts06main.py; this file only draws it. Every part is placed unrotated
and every connected pin gets a short wire stub ending in a local label with the net's name,
so the drawing is a labelled netlist grouped by function rather than a hand-routed circuit
diagram: with ~150 parts that is what stays readable, and it is what tools/checksch.py and
tools/checkmatch.py check. Unconnected pins carry a no-connect flag.

Symbols live in their own library, PCB/lib/TS06M.kicad_sym (nickname TS06M), so that
tools/mksch.py, which rewrites TS06.kicad_sym on every run, never touches them. Pin numbers
are the footprint pad names (see ts06main.py).

Format tokens as in tools/mksch.py, from a real KiCad 10.0 save.
"""
import os, re, sys, uuid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ts06main as N

SV, GV = 20260306, "10.0"
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
LIBNAME = "TS06M"
LIB = os.path.join(ROOT, "PCB", "lib", LIBNAME + ".kicad_sym")
BUILD = "tht" if "--tht" in sys.argv else "smd"
BOARD = "TS06-MAIN-THT" if BUILD == "tht" else "TS06-MAIN"
SCH = os.path.join(ROOT, "PCB", BOARD, BOARD + ".kicad_sch")
NSPACE = uuid.UUID("7506a1a0-0000-4000-8000-00000000ba5e")
SHEET_UUID = str(uuid.uuid5(NSPACE, "sheet " + BOARD))
_n = [0]


def U():
    _n[0] += 1
    return str(uuid.uuid5(NSPACE, f"{BOARD}/{_n[0]}"))


def f(v):
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def eff(sz=1.27, hide=False, just=None):
    j = f"\n(justify {just})" if just else ""
    return f"(effects\n(font\n(size {sz} {sz})\n){j}\n)"


def prop(k, v, x, y, hide=False, just=None):
    # KiCad 9+ keeps (hide yes) on the property itself, not inside its effects. With it
    # inside the effects, KiCad 10 refused to load the generated file at all (18.09.26).
    h = "\n(hide yes)" if hide else ""
    return f'(property "{k}" "{v}"\n(at {f(x)} {f(y)} 0){h}\n{eff(1.27, hide, just)}\n)'


def pin(typ, x, y, rot, ln, name, num):
    return (f'(pin {typ} line\n(at {f(x)} {f(y)} {rot})\n(length {f(ln)})\n'
            f'(name "{name}"\n{eff(1.27)}\n)\n(number "{num}"\n{eff(1.27)}\n)\n)')


def rect(x1, y1, x2, y2, fill="none"):
    return (f'(rectangle\n(start {f(x1)} {f(y1)})\n(end {f(x2)} {f(y2)})\n'
            f'(stroke\n(width 0.254)\n(type default)\n)\n(fill\n(type {fill})\n)\n)')


def poly(pts, w=0.254, fill="none"):
    p = "\n".join(f"(xy {f(a)} {f(b)})" for a, b in pts)
    return (f'(polyline\n(pts\n{p}\n)\n(stroke\n(width {f(w)})\n(type default)\n)\n'
            f'(fill\n(type {fill})\n)\n)')


def circ(x, y, r, w=0.254, fill="none"):
    return (f'(circle\n(center {f(x)} {f(y)})\n(radius {f(r)})\n(stroke\n(width {f(w)})\n'
            f'(type default)\n)\n(fill\n(type {fill})\n)\n)')


def symbol(name, ref, val, descr, graphics, pins, ref_y=2.54, val_y=-2.54):
    g = "\n".join(graphics)
    p = "\n".join(pins)
    return (f'(symbol "{name}"\n(pin_names\n(offset 0.254)\n)\n(exclude_from_sim no)\n'
            f'(in_bom yes)\n(on_board yes)\n'
            f'{prop("Reference", ref, 0, ref_y)}\n{prop("Value", val, 0, val_y)}\n'
            f'{prop("Footprint", "", 0, 0, hide=True)}\n'
            f'{prop("Datasheet", "", 0, 0, hide=True)}\n'
            f'{prop("Description", descr, 0, 0, hide=True)}\n'
            f'(symbol "{name}_0_1"\n{g}\n)\n(symbol "{name}_1_1"\n{p}\n)\n)')


# ---------------------------------------------------------------- symbols
# Each entry: (symbol text, {pin number: (x, y, rot)} in symbol space, envelope (w, h))
SYMS, PINS, ENV = {}, {}, {}


def two_pin(name, ref, val, descr, graphics, top="1", bot="2"):
    SYMS[name] = symbol(name, ref, val, descr, graphics,
                        [pin("passive", 0, 3.81, 270, 1.27, "~", top), pin("passive", 0, -3.81, 90, 1.27, "~", bot)])
    PINS[name] = {top: (0, 3.81, 270), bot: (0, -3.81, 90)}
    ENV[name] = (17.78, 33.02)


two_pin("R", "R", "R", "Resistor", [rect(-1.016, -2.54, 1.016, 2.54)])
two_pin("C", "C", "C", "Capacitor", [poly([(-1.905, 0.635), (1.905, 0.635)], 0.508),
                                     poly([(-1.905, -0.635), (1.905, -0.635)], 0.508),
                                     poly([(0, 2.54), (0, 0.635)]), poly([(0, -0.635), (0, -2.54)])])
two_pin("CP", "C", "CP", "Polarised capacitor, pin 1 positive",
        [poly([(-1.905, 0.635), (1.905, 0.635)], 0.508), rect(-1.905, -1.27, 1.905, -0.635, "outline"),
         poly([(0, 2.54), (0, 0.635)]), poly([(0, -1.27), (0, -2.54)]),
         poly([(2.794, 1.905), (3.81, 1.905)]), poly([(3.302, 2.413), (3.302, 1.397)])])
two_pin("L", "L", "L", "Inductor", [circ(0, 1.905, 0.635), circ(0, 0.635, 0.635), circ(0, -0.635, 0.635), circ(0, -1.905, 0.635)])
two_pin("Fuse", "F", "F", "Fuse", [rect(-1.016, -2.54, 1.016, 2.54), poly([(0, 2.54), (0, -2.54)])])
two_pin("Lamp_Neon", "V", "INS-1", "Neon lamp, two wire leads", [circ(0, 0, 2.286), poly([(-1.5, 1.0), (1.5, 1.0)]), poly([(-1.5, -1.0), (1.5, -1.0)])])
two_pin("Battery", "BT", "CR2032", "Coin cell: pin 1 positive", [poly([(-2.54, 0.635), (2.54, 0.635)], 0.508), poly([(-1.27, -0.635), (1.27, -0.635)], 0.508),
                                                                  poly([(0, 2.54), (0, 0.635)]), poly([(0, -0.635), (0, -2.54)])])


def diode(name, ref, val, descr, extra=()):
    g = [poly([(-1.27, 1.27), (1.27, 0), (-1.27, -1.27), (-1.27, 1.27)]), poly([(1.27, 1.27), (1.27, -1.27)], 0.508),
         poly([(-2.54, 0), (-1.27, 0)]), poly([(1.27, 0), (2.54, 0)])] + list(extra)
    SYMS[name] = symbol(name, ref, val, descr, g,
                        [pin("passive", 3.81, 0, 180, 1.27, "K", "1"), pin("passive", -3.81, 0, 0, 1.27, "A", "2")], 3.81, -3.81)
    PINS[name] = {"1": (3.81, 0, 180), "2": (-3.81, 0, 0)}
    ENV[name] = (35.56, 15.24)


diode("D_Fast", "VD", "D", "Fast rectifier: 1 cathode, 2 anode")
diode("D_Schottky", "VD", "D", "Schottky: 1 cathode, 2 anode", [poly([(1.27, 1.27), (0.762, 1.27)]), poly([(1.27, -1.27), (1.778, -1.27)])])
diode("LED", "HL", "LED", "LED: 1 cathode, 2 anode", [poly([(-0.5, 2.0), (0.5, 3.2)]), poly([(0.5, 2.0), (1.5, 3.2)])])


def three_pin(name, ref, val, descr, graphics, pins3, env=(30.48, 30.48)):
    SYMS[name] = symbol(name, ref, val, descr, graphics, [pin("passive", x, y, r, 2.54, nm, num) for num, nm, x, y, r in pins3], 6.35, -6.35)
    PINS[name] = {num: (x, y, r) for num, nm, x, y, r in pins3}
    ENV[name] = env


three_pin("Q_NPN_BEC", "VT", "NPN", "NPN, 300 V class: 1 base, 2 emitter, 3 collector",
          [poly([(0, 2.54), (0, -2.54)], 0.508), poly([(-2.54, 0), (0, 0)]), poly([(0, 1.27), (2.54, 2.54)]), poly([(0, -1.27), (2.54, -2.54)]),
           poly([(1.5, -2.2), (2.54, -2.54), (2.2, -1.5)])],
          [("1", "B", -5.08, 0, 0), ("2", "E", 2.54, -5.08, 90), ("3", "C", 2.54, 5.08, 270)])
three_pin("Q_NMOS_GDS", "VT", "NMOS", "N-channel MOSFET: 1 gate, 2 drain, 3 source",
          [poly([(-0.762, 2.54), (-0.762, -2.54)], 0.508), poly([(0, 2.286), (0, 1.0)], 0.508), poly([(0, 0.6), (0, -0.6)], 0.508),
           poly([(0, -1.0), (0, -2.286)], 0.508), poly([(-2.54, 0), (-0.762, 0)]), poly([(0, 1.65), (2.54, 1.65), (2.54, 2.54)]),
           poly([(0, -1.65), (2.54, -1.65), (2.54, -2.54)]), poly([(0, 0), (2.54, 0), (2.54, -1.65)])],
          [("1", "G", -5.08, 0, 0), ("2", "D", 2.54, 5.08, 270), ("3", "S", 2.54, -5.08, 90)])
three_pin("Reg_SIP3", "U", "R-78E5.0", "Switching regulator module, 78xx pinout: 1 in, 2 GND, 3 out",
          [rect(-5.08, -3.81, 5.08, 3.81)],
          [("1", "IN", -7.62, 1.27, 0), ("2", "GND", 0, -6.35, 90), ("3", "OUT", 7.62, 1.27, 180)], (40.64, 33.02))
three_pin("Trimmer", "RP", "RP", "Trimmer potentiometer: 1 and 3 the ends, 2 the wiper",
          [rect(-1.016, -3.81, 1.016, 3.81), poly([(2.54, 0), (1.016, 0)]), poly([(1.016, 0), (1.8, 0.6), (1.8, -0.6), (1.016, 0)])],
          [("1", "1", 0, 6.35, 270), ("3", "3", 0, -6.35, 90), ("2", "W", 5.08, 0, 180)], (30.48, 38.1))
three_pin("Jack_DC", "XS", "DC", "Barrel jack: 1 centre pin, 2 sleeve, 3 the sleeve's break contact",
          [rect(-5.08, -5.08, 5.08, 5.08), poly([(-3.81, 1.27), (-1.27, 1.27)], 0.508), poly([(-3.81, -1.27), (-1.27, -1.27)], 0.508), circ(-2.54, 0, 0.6)],
          [("1", "+", 7.62, 2.54, 180), ("2", "-", 7.62, 0, 180), ("3", "SW", 7.62, -2.54, 180)], (43.18, 33.02))


def box(name, ref, val, descr, left, right, width=15.24):
    n = max(len(left), len(right))
    top = (n + 1) * 1.27
    g = [rect(-width / 2, -top, width / 2, top)]
    ps, pm = [], {}
    for i, (num, nm) in enumerate(left):
        x, y = -width / 2 - 5.08, top - 2.54 * (i + 1)
        ps.append(pin("passive", x, y, 0, 5.08, nm, num))
        pm[str(num)] = (x, y, 0)
    for i, (num, nm) in enumerate(right):
        x, y = width / 2 + 5.08, top - 2.54 * (i + 1)
        ps.append(pin("passive", x, y, 180, 5.08, nm, num))
        pm[str(num)] = (x, y, 180)
    SYMS[name] = symbol(name, ref, val, descr, g, ps, top + 2.54, -top - 2.54)
    PINS[name] = pm
    ENV[name] = (width + 2 * (5.08 + 5.08 + 15.24), 2 * top + 12.7)


box("TLP627", "U", "TLP627", "Darlington optocoupler DIP-4: 1 LED anode, 2 LED cathode, 3 emitter, 4 collector",
    [(1, "A"), (2, "K")], [(4, "C"), (3, "E")], 12.7)
box("K155ID1", "U", "K155ID1", "BCD to decimal nixie driver, DIP-16 (SN74141 pinout, confirmed on the inherited copper)",
    [(3, "A 1"), (6, "B 2"), (7, "C 4"), (4, "D 8"), (5, "VCC"), (12, "GND")],
    [(16, "Q0"), (15, "Q1"), (8, "Q2"), (9, "Q3"), (13, "Q4"), (14, "Q5"), (11, "Q6"), (10, "Q7"), (1, "Q8"), (2, "Q9")])
box("MCP23017", "U", "MCP23017", "16-bit I2C port expander",
    [(9, "VDD"), (10, "VSS"), (12, "SCL"), (13, "SDA"), (15, "A0"), (16, "A1"), (17, "A2"), (18, "RESET"), (19, "INTB"), (20, "INTA"), (11, "NC"), (14, "NC")],
    [(21 + k, f"GPA{k}") for k in range(8)] + [(1 + k, f"GPB{k}") for k in range(8)], 17.78)
box("Arduino_Nano", "U", "Nano", "Arduino Nano v3 on headers, KiCad Module:Arduino_Nano numbering",
    [(1, "D1/TX"), (2, "D0/RX"), (3, "RESET"), (4, "GND"), (5, "D2"), (6, "D3"), (7, "D4"), (8, "D5"), (9, "D6"), (10, "D7"),
     (11, "D8"), (12, "D9"), (13, "D10"), (14, "D11"), (15, "D12")],
    [(30, "VIN"), (29, "GND"), (28, "RESET"), (27, "+5V"), (26, "A7"), (25, "A6"), (24, "A5/SCL"), (23, "A4/SDA"), (22, "A3"),
     (21, "A2"), (20, "A1"), (19, "A0"), (18, "AREF"), (17, "3V3"), (16, "D13")], 20.32)
box("LM393", "U", "LM393", "Dual comparator, open collector",
    [(2, "IN1-"), (3, "IN1+"), (6, "IN2-"), (5, "IN2+"), (8, "V+"), (4, "GND")], [(1, "OUT1"), (7, "OUT2")])
box("TC4420", "U", "TC4420", "Low-side MOSFET driver, non-inverting",
    [(2, "IN"), (1, "VDD"), (8, "VDD"), (4, "GND"), (5, "GND"), (3, "NC")], [(6, "OUT"), (7, "OUT")])
box("DS3231", "U", "DS3231SN", "RTC with integrated TCXO, SO-16",
    [(2, "VCC"), (14, "VBAT"), (13, "GND"), (1, "32K"), (3, "INT/SQW"), (4, "RST")],
    [(15, "SDA"), (16, "SCL")] + [(k, "NC") for k in range(5, 13)])
box("RTC_mini", "U", "DS3231 mini", "The small DS3231 module on a 5-way header: - NC C D +",
    [(1, "-"), (2, "NC"), (3, "C"), (4, "D"), (5, "+")], [], 12.7)
box("Tube_IN12", "V", "IN-12A", "12-pin stadium socket, TS06_IN12_Socket pad numbers; the value says which tube and the notes which pad is what",
    [(k, str(k)) for k in range(1, 7)], [(k, str(k)) for k in range(7, 13)], 12.7)
box("Tube_IN17", "V", "IN-17", "Wire-ended IN-17, pads named by cathode digit and A for the anode",
    [(k, str(k)) for k in range(0, 5)] + [("A", "A")], [(k, str(k)) for k in range(5, 10)], 12.7)
box("Conn_PH6", "J", "PH 6", "Panel cable: 1 +5V, 2 GND, 3 A6, 4 A7, 5 D7, 6 D8", [], [(k, str(k)) for k in range(1, 7)], 10.16)


def qualify(txt, name):
    """Inside a .kicad_sch the lib_symbols entry carries the full lib_id ("TS06M:R"), but its
    unit sub-symbols stay bare ("R_0_1", "R_1_1"): that is how KiCad writes them, and with
    the prefix on the units KiCad 10 refuses to load the file (found 18.09.26)."""
    return txt.replace(f'(symbol "{name}"', f'(symbol "{LIBNAME}:{name}"', 1)


# ---------------------------------------------------------------- schematic
items = []


def wire(x1, y1, x2, y2):
    items.append(f'(wire\n(pts\n(xy {f(x1)} {f(y1)})\n(xy {f(x2)} {f(y2)})\n)\n(stroke\n(width 0)\n(type default)\n)\n(uuid "{U()}")\n)')


def label(t, x, y, rot, just):
    items.append(f'(label "{t}"\n(at {f(x)} {f(y)} {rot})\n(fields_autoplaced yes)\n{eff(1.27, just=just)}\n(uuid "{U()}")\n)')


def noconn(x, y):
    items.append(f'(no_connect\n(at {f(x)} {f(y)})\n(uuid "{U()}")\n)')


def note(t, x, y, sz=1.27):
    t = t.replace(chr(10), chr(92) + "n")      # KiCad wants an escaped newline inside the string
    items.append(f'(text "{t}"\n(exclude_from_sim no)\n(at {f(x)} {f(y)} 0)\n{eff(sz)}\n(uuid "{U()}")\n)')


STUB = 5.08
DIR = {0: (-1, 0, 180, "right bottom"), 180: (1, 0, 0, "left bottom"), 90: (0, 1, 270, "left bottom"), 270: (0, -1, 90, "left bottom")}


def value_for(p):
    v = p.value
    return v.split(" / ")[0 if BUILD == "smd" else 1] if " / " in v else v


def place(p, x, y):
    """One part at sheet (x, y), unrotated: symbol, stubs, labels, no-connects."""
    sym = p.sym
    fp = f"TS06:{p.fp(BUILD)}"
    pn = "\n".join(f'(pin "{num}"\n(uuid "{U()}")\n)' for num in PINS[sym])
    w = ENV[sym][0]
    items.append(
        f'(symbol\n(lib_id "{LIBNAME}:{sym}")\n(at {f(x)} {f(y)} 0)\n(unit 1)\n'
        f'(exclude_from_sim no)\n(in_bom yes)\n(on_board yes)\n(dnp {"yes" if "DNP" in p.value else "no"})\n'
        f'(fields_autoplaced yes)\n(uuid "{U()}")\n'
        f'{prop("Reference", p.ref, x - w / 2 + 2.54, y - ENV[sym][1] / 2 + 1.27, just="left")}\n'
        f'{prop("Value", value_for(p), x - w / 2 + 2.54, y - ENV[sym][1] / 2 + 3.81, just="left")}\n'
        f'{prop("Footprint", fp, x, y, hide=True)}\n'
        f'{pn}\n(instances\n(project "{BOARD}"\n(path "/{SHEET_UUID}"\n'
        f'(reference "{p.ref}")\n(unit 1)\n)\n)\n)\n)')
    for num, (px, py, rot) in PINS[sym].items():
        sx, sy = x + px, y - py
        net = p.pins.get(num)
        if net is None:
            noconn(sx, sy)
            continue
        dx, dy, lrot, just = DIR[rot]
        ex, ey = sx + dx * STUB, sy + dy * STUB
        wire(sx, sy, ex, ey)
        label(net, ex, ey, lrot, just)


class Flow:
    """Lay parts left to right in rows inside [x0, x1], starting at y0."""

    def __init__(self, x0, y0, x1):
        self.x0, self.x1, self.x, self.y, self.rowh = x0, x1, x0, y0, 0

    def add(self, p):
        w, h = ENV[p.sym]
        if self.x + w > self.x1 and self.x > self.x0:
            self.x, self.y, self.rowh = self.x0, self.y + self.rowh, 0
        cx, cy = self.x + w / 2, self.y + h / 2
        cx, cy = round(cx / 1.27) * 1.27, round(cy / 1.27) * 1.27
        place(p, cx, cy)
        self.x += w
        self.rowh = max(self.rowh, h)

    @property
    def bottom(self):
        return self.y + self.rowh


BY = {p.ref: p for p in N.parts(BUILD)}
GROUPS = [
    ("power", "12 V IN. Barrel jack, PTC fuse, reverse-polarity Schottky, then an R-78E switching regulator makes the\n"
              "5 V rail for everything, Nano included (its 5V pin; VIN open). A PC on the Nano's USB with no adapter plugged\n"
              "in runs the logic with the tubes dark - the boost has no 12 V."),
    ("hv", "185 V RAIL, regulated this time. D9's 31 kHz clock reaches the MOSFET through a proper 12 V driver; a comparator\n"
           "watches the rail through a 1.5 M / 20.5 k divider and holds the driver input low whenever FB is above VREF, so the\n"
           "stage skips cycles until the rail sags back. The trimmer is a rheostat in the divider's foot: 152 to 252 V. The\n"
           "inherited stage had none of this - it was an energy-limited 1 W source with a bleed trimmer (netlist sheet §2)."),
    ("mcu", "NANO. Pin map is the firmware's and is not renumbered."),
    ("decoder", "ONE DECODER for six digit tubes. A0..A3 -> C B D A as on the inherited board; output Q_c goes to the cathode\n"
                "of digit d where digitMask[d] = c (BOARD_TYPE 0), so K7 hangs off Q0, K4 off Q1 ... K5 off Q9."),
    ("digits", "SIX DIGIT TUBES on the shared cathode bus K0..K9 (named by digit). IN-12A pads per the inherited copper:\n"
               "pad 7 anode, pad 8 no pin. IN-17 pads named by digit from judge2005's footprint - bench gate 3."),
    ("anodes", "ANODE CHAINS, one per digit tube: Nano pin -> 470 R -> TLP627 LED; collector on HV185, emitter -> series R\n"
               "-> anode. Bleed pairs are DNP unless the bench asks for them. 6k8 for the IN-12s is TBC (gate 2)."),
    ("ampm", "AM/PM: two MCP23017 on the same I2C wires as the RTC, eighteen 300 V low-side switches, one per real\n"
             "cathode. V9 IN-15B shows A, V10 IN-15A shows P. Anode resistors one per tube. Pad maps: bench gate 4."),
    ("colon", "COLON: two INS-1 neons, each with its own 220 k ballast, one low-side MPSA42 on D10."),
    ("backlight", "BACKLIGHT: eight amber LEDs, one under each tube, series 220 R from +5V, switched low-side from D11.\n"
                  "The 'm' of AM/PM is HL9 straight off D12: firmware decides always-on or 12-hour-only."),
    ("fascia", "FASCIA CABLE J1, pin order fixed for both fascia builds: +5V GND A6 A7 D7 D8. The 100 nF ladder filters\n"
               "sit here, at the board end."),
    ("rtc", "RTC. SMD build: DS3231SN with a CR2032 holder. THT build: the DS3231 mini module on a 5-way header (- NC C D +)."),
]
XL, XR, Y = 20.32, 820.42, 40.64
for gname, text in GROUPS:
    note(text, XL, Y + 2.54)
    fl = Flow(XL, Y + 12.7, XR)
    for p in sorted((q for q in N.parts(BUILD) if q.group == gname), key=lambda q: (re.match(r'[A-Z]+', q.ref).group(0), int(re.search(r'\d+', q.ref).group(0)))):
        fl.add(p)
    Y = fl.bottom + 7.62

# ---------------------------------------------------------------- write
os.makedirs(os.path.dirname(SCH), exist_ok=True)
with open(LIB, "w", encoding="utf8", newline="\n") as fh:
    fh.write(f'(kicad_symbol_lib\n(version {SV})\n(generator "kicad_symbol_editor")\n(generator_version "{GV}")\n'
             + "\n".join(SYMS.values()) + "\n)\n")
print("wrote", os.path.relpath(LIB, ROOT))
lib_sch = "\n".join(qualify(t, n) for n, t in SYMS.items())
paper = "A0" if Y > 580 else "A1"
with open(SCH, "w", encoding="utf8", newline="\n") as fh:
    fh.write(
        f'(kicad_sch\n(version {SV})\n(generator "eeschema")\n(generator_version "{GV}")\n'
        f'(uuid "{SHEET_UUID}")\n(paper "{paper}")\n'
        f'(title_block\n(title "{BOARD} - the whole clock on one board, {"surface-mount" if BUILD == "smd" else "through-hole"} build")\n'
        f'(date "2026-09-17")\n(rev "A")\n(company "TERMINAL-06")\n'
        f'(comment 1 "Generated by tools/mksch_main.py from tools/ts06main.py - edit those, not this")\n'
        f'(comment 2 "Netlist sources: TERMINAL-06-measurements-PCB-GYVER-NETLIST.md, TS06-SEC, the 17.09.26 decisions")\n)\n'
        f'(lib_symbols\n{lib_sch}\n)\n' + "\n".join(items)
        + f'\n(sheet_instances\n(path "/"\n(page "1")\n)\n)\n(embedded_fonts no)\n)\n')
print("wrote", os.path.relpath(SCH, ROOT), f"({paper}, {len(N.parts(BUILD))} parts, sheet height used {Y:.0f} mm)")
for tbl, name in ((["(name \"TS06\")(type \"KiCad\")(uri \"${KIPRJMOD}/../lib/TS06.kicad_sym\")(options \"\")(descr \"TERMINAL-06 project symbols\")",
                    f"(name \"{LIBNAME}\")(type \"KiCad\")(uri \"${{KIPRJMOD}}/../lib/{LIBNAME}.kicad_sym\")(options \"\")(descr \"TS06-MAIN symbols\")"], "sym-lib-table"),
                  (["(name \"TS06\")(type \"KiCad\")(uri \"${KIPRJMOD}/../lib/TS06.pretty\")(options \"\")(descr \"TERMINAL-06 project footprints\")"], "fp-lib-table")):
    kind = "sym_lib_table" if name.startswith("sym") else "fp_lib_table"
    with open(os.path.join(os.path.dirname(SCH), name), "w", encoding="utf8", newline="\n") as fh:
        fh.write(f"({kind}\n  (version 7)\n" + "".join(f"  (lib {t})\n" for t in tbl) + ")\n")
