#!/usr/bin/env python3
"""Draw the schematics of the through-hole pair, TS06-DRV and TS06-DISP, from tools/ts06pair.py.

    python3 tools/mksch_pair.py                     # both boards, the symbol library, the sym-lib-tables
    python3 tools/mksch_pair.py --compare NET PCB   # a netlist KiCad exported vs a board, pad by pad

WHAT IT WRITES
  PCB/lib/TS06_pair.kicad_sym                       the symbols (library nickname TS06_pair)
  PCB/TS06-DRV/TS06-DRV.kicad_sch                   root: one sheet box per section
  PCB/TS06-DRV/TS06-DRV-<nn>-<section>.kicad_sch    one sheet per section
  PCB/TS06-DISP/... the same for the display board
  PCB/TS06-{DRV,DISP}/sym-lib-table

THE NETLIST IS tools/ts06pair.py; this file only draws it. The sections are the part groups of
ts06pair.py (SECTIONS below), in the order a reader follows the signal. Each sheet is laid out by
hand in signal-flow order: parts are placed by coordinates, wired where the drawing reads better
with a wire, and every pin that is not wired gets a short stub and a label. Net names come only
from ts06pair.py, never from this file.

NET NAMES ARE THE BOARD'S, EXACTLY. KiCad names a net held only by a local label "/sheet/NAME",
and "Update PCB from schematic" would then rename every net on the boards - which would also
break the net classes in the .kicad_pro, whose patterns (HV185, ANODE_*, K0 ...) match the bare
names. So every net is named by a global label (or by a power symbol, for GND, +5V and +12V),
including nets that live on one sheet; those carry a small flag label on their wire.

WHY IT SURVIVES NETLIST CHANGES. The layout code never names a net itself: a wire between two
pins is drawn only when ts06pair.py puts both on the same net, and every label takes its text
from the pin it hangs on. A part that the layout does not know is placed in a row at the foot of
its section's sheet with a labelled stub on every pin. After drawing, each sheet is traced like
KiCad traces it (wire ends, T-points, labels, power symbols) and compared with ts06pair.py pin by
pin; a sheet that fails is redrawn as a plain labelled netlist and a warning is printed, so the
output is correct even when the hand layout has gone stale.

FOOTPRINTS AND VALUES are read back from the board files, so "Update PCB from schematic" finds
nothing to change: the boards carry rotated footprint variants (TS06_R_..._R90) that ts06pair.py
does not name. A part not yet on its board falls back to "TS06:" + its ts06pair footprint.

UUIDs are uuid5 of stable keys (board, sheet, reference, pin, or the drawn geometry), so a re-run
rewrites identical files.

Format tokens as tools/mksch.py and tools/mksch_main.py: schematic 20260306, library 20251024,
from a real KiCad 10.0 save.
"""
import json, math, os, re, sys, textwrap, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ts06pair as TP                       # noqa: E402
import sexp                                 # noqa: E402

SV, GV = 20260306, "10.0"
LV = 20251024
ROOT = os.path.normpath(os.path.join(HERE, ".."))
LIBNICK = "TS06_pair"
LIBFILE = os.path.join(ROOT, "PCB", "lib", "TS06_pair.kicad_sym")
NS = uuid.UUID("7506a1a0-5c4e-4a70-8a1f-00000000bea2")
G = 2.54
POWER_NETS = ("GND", "+5V", "+12V")
BOARDS = {"drv": ("TS06-DRV", TP.DRV), "disp": ("TS06-DISP", TP.DISP)}


def uid(*key):
    return str(uuid.uuid5(NS, "/".join(str(k) for k in key)))


def f(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def esc(s):
    return str(s).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def snap(v):
    return round(round(v / 1.27) * 1.27, 4)


def eff(sz=1.27, just=None, bold=False, hide=False):
    b = "\n(bold yes)" if bold else ""
    j = f"\n(justify {just})" if just else ""
    h = "\n(hide yes)" if hide else ""
    return f"(effects\n(font\n(size {f(sz)} {f(sz)})\n{b.strip()}\n){j}{h}\n)".replace("\n\n", "\n")


def prop(k, v, x, y, ang=0, hide=False, just=None, sz=1.27):
    # KiCad 9+ keeps (hide yes) on the property itself, not inside its effects (tools/mksch.py).
    h = "\n(hide yes)" if hide else ""
    return f'(property "{k}" "{esc(v)}"\n(at {f(x)} {f(y)} {ang}){h}\n{eff(sz, just)}\n)'


# ==================================================================== symbols
def g_rect(x1, y1, x2, y2, fill="none", w=0.254):
    return (f"(rectangle\n(start {f(x1)} {f(y1)})\n(end {f(x2)} {f(y2)})\n"
            f"(stroke\n(width {f(w)})\n(type default)\n)\n(fill\n(type {fill})\n)\n)")


def g_poly(pts, w=0.254, fill="none"):
    p = " ".join(f"(xy {f(a)} {f(b)})" for a, b in pts)
    return f"(polyline\n(pts\n{p}\n)\n(stroke\n(width {f(w)})\n(type default)\n)\n(fill\n(type {fill})\n)\n)"


def g_circ(x, y, r, w=0.254, fill="none"):
    return (f"(circle\n(center {f(x)} {f(y)})\n(radius {f(r)})\n(stroke\n(width {f(w)})\n(type default)\n)\n"
            f"(fill\n(type {fill})\n)\n)")


def g_arc(s, m, e, w=0.254):
    return (f"(arc\n(start {f(s[0])} {f(s[1])})\n(mid {f(m[0])} {f(m[1])})\n(end {f(e[0])} {f(e[1])})\n"
            f"(stroke\n(width {f(w)})\n(type default)\n)\n(fill\n(type none)\n)\n)")


def g_text(t, x, y, sz=1.27, ang=0):
    return f'(text "{esc(t)}"\n(at {f(x)} {f(y)} {ang})\n{eff(sz)}\n)'


class Sym:
    """One library symbol. pins: number -> (x, y, rot, length, etype, name), symbol space (y up)."""

    def __init__(self, name, ref, descr, graphics, pins, *, power=False, names=True, numbers=True,
                 offset=0.508, in_bom=True, on_board=True, ref_at=(0, 5.08), val_at=(0, -5.08)):
        self.name, self.ref, self.descr = name, ref, descr
        self.graphics, self.power = graphics, power
        self.pins = {str(p[6]): p[:6] for p in pins}
        self.order = [str(p[6]) for p in pins]
        self.names, self.numbers, self.offset = names, numbers, offset
        self.in_bom, self.on_board = in_bom, on_board
        self.ref_at, self.val_at = ref_at, val_at
        xs = [0.0]
        ys = [0.0]
        for (x, y, r, ln, *_rest) in self.pins.values():
            xs.append(x)
            ys.append(y)
        for gtxt in graphics:
            for a, b in re.findall(r"\((?:xy|start|end|center|mid) (-?[\d.]+) (-?[\d.]+)\)", gtxt):
                xs.append(float(a))
                ys.append(float(b))
            m = re.search(r"\(center (-?[\d.]+) (-?[\d.]+)\)\n\(radius ([\d.]+)\)", gtxt)
            if m:
                cx, cy, r = map(float, m.groups())
                xs += [cx - r, cx + r]
                ys += [cy - r, cy + r]
        self.bbox = (min(xs), min(ys), max(xs), max(ys))        # symbol space, pins included

    def text(self, qualified=False):
        nm = f"{LIBNICK}:{self.name}" if qualified else self.name
        pw = "(power global)\n" if self.power else ""
        pn = "(pin_numbers\n(hide yes)\n)\n" if not self.numbers else ""
        pnames = f"(pin_names\n(offset {f(self.offset)})\n{'(hide yes)' if not self.names else ''}\n)".replace("\n\n", "\n")
        pins = []
        for num in self.order:
            x, y, rot, ln, et, pname = self.pins[num]
            pins.append(f"(pin {et} line\n(at {f(x)} {f(y)} {rot})\n(length {f(ln)})\n"
                        f'(name "{esc(pname)}"\n{eff(1.27)}\n)\n(number "{esc(num)}"\n{eff(1.27)}\n)\n)')
        ref_hide = self.power
        return (f'(symbol "{nm}"\n{pw}{pn}{pnames}\n(exclude_from_sim no)\n'
                f'(in_bom {"yes" if self.in_bom else "no"})\n(on_board {"yes" if self.on_board else "no"})\n'
                f'{prop("Reference", self.ref, self.ref_at[0], self.ref_at[1], hide=ref_hide)}\n'
                f'{prop("Value", self.name if not self.power else self.name, self.val_at[0], self.val_at[1])}\n'
                f'{prop("Footprint", "", 0, 0, hide=True)}\n{prop("Datasheet", "", 0, 0, hide=True)}\n'
                f'{prop("Description", self.descr, 0, 0, hide=True)}\n'
                f'(symbol "{self.name}_0_1"\n' + "\n".join(self.graphics) + "\n)\n"
                f'(symbol "{self.name}_1_1"\n' + "\n".join(pins) + "\n)\n(embedded_fonts no)\n)")


SYMS = {}


def add(sym):
    SYMS[sym.name] = sym
    return sym


def P(x, y, rot, ln, et, name, num):
    return (x, y, rot, ln, et, name, num)


# ---- passives: two pins, vertical, pin 1 on top
def two(name, ref, descr, graphics, top="1", bot="2", et="passive"):
    return add(Sym(name, ref, descr, graphics,
                   [P(0, 3.81, 270, 1.27 if name not in ("C", "CP") else 2.794, et, "~", top),
                    P(0, -3.81, 90, 1.27 if name not in ("C", "CP") else 2.794, et, "~", bot)],
                   names=False, numbers=False, ref_at=(2.54, 1.27), val_at=(2.54, -1.27)))


two("R", "R", "Resistor", [g_rect(-1.016, -2.54, 1.016, 2.54)])
two("C", "C", "Capacitor, unpolarised", [g_poly([(-2.032, 0.762), (2.032, 0.762)], 0.508),
                                         g_poly([(-2.032, -0.762), (2.032, -0.762)], 0.508)])
two("CP", "C", "Polarised capacitor, pin 1 positive",
    [g_rect(-2.032, 0.508, 2.032, 1.016), g_rect(-2.032, -0.508, 2.032, -1.016, "outline"),
     g_poly([(-1.778, 2.286), (-0.762, 2.286)]), g_poly([(-1.27, 2.794), (-1.27, 1.778)])])
two("L", "L", "Inductor", [g_arc((0, 2.54 - 1.27 * i), (0.635, 1.905 - 1.27 * i), (0, 1.27 - 1.27 * i)) for i in range(4)])
two("Polyfuse", "F", "Resettable PTC fuse",
    [g_rect(-0.762, -2.54, 0.762, 2.54), g_poly([(-1.524, -2.54), (-1.524, -1.778), (1.524, 1.778), (1.524, 2.54)])])


def diode(name, ref, descr, extra=(), bar=None):
    g = [g_poly([(-1.27, 1.27), (1.27, 0), (-1.27, -1.27), (-1.27, 1.27)]),
         g_poly(bar or [(1.27, 1.27), (1.27, -1.27)]),
         g_poly([(-2.54, 0), (2.54, 0)])] + list(extra)
    return add(Sym(name, ref, descr, g, [P(3.81, 0, 180, 1.27, "passive", "K", "1"), P(-3.81, 0, 0, 1.27, "passive", "A", "2")],
                   names=False, numbers=False, ref_at=(0, 2.54), val_at=(0, -2.54)))


diode("D", "VD", "Diode: 1 cathode, 2 anode")
diode("D_Schottky", "VD", "Schottky diode: 1 cathode, 2 anode",
      bar=[(1.905, 0.762), (1.905, 1.27), (1.27, 1.27), (1.27, -1.27), (0.635, -1.27), (0.635, -0.762)])
diode("D_Zener", "VD", "Zener or TVS diode: 1 cathode, 2 anode", bar=[(0.762, 1.778), (1.27, 1.27), (1.27, -1.27), (1.778, -1.778)])
diode("LED", "HL", "LED: 1 cathode, 2 anode",
      extra=[g_poly([(-0.508, 1.778), (0.508, 2.794)]), g_poly([(0.508, 2.794), (0.0, 2.667), (0.381, 2.286), (0.508, 2.794)], fill="outline"),
             g_poly([(0.635, 1.778), (1.651, 2.794)]), g_poly([(1.651, 2.794), (1.143, 2.667), (1.524, 2.286), (1.651, 2.794)], fill="outline")])

add(Sym("Q_NPN_EBC", "VT", "NPN transistor, TO-92 E-B-C: 1 emitter, 2 base, 3 collector",
        [g_circ(1.27, 0, 2.794), g_poly([(0.635, 1.905), (0.635, -1.905)], 0.508), g_poly([(-0.635, 0), (0.635, 0)]),
         g_poly([(0.635, 0.635), (2.54, 2.54)]), g_poly([(0.635, -0.635), (2.54, -2.54)]),
         g_poly([(2.286, -2.286), (1.968, -1.332), (1.332, -1.968), (2.286, -2.286)], fill="outline")],
        [P(2.54, -5.08, 90, 2.54, "passive", "E", "1"), P(-5.08, 0, 0, 4.445, "passive", "B", "2"),
         P(2.54, 5.08, 270, 2.54, "passive", "C", "3")], names=False, numbers=False, ref_at=(5.08, 1.27), val_at=(5.08, -1.27)))
add(Sym("Q_NMOS_GDS", "VT", "N-channel MOSFET, TO-220 G-D-S: 1 gate, 2 drain, 3 source",
        [g_circ(1.524, 0, 2.794), g_poly([(-0.254, 1.905), (-0.254, -1.905)]),
         g_poly([(0.508, 2.286), (0.508, 1.27)], 0.508), g_poly([(0.508, 0.508), (0.508, -0.508)], 0.508),
         g_poly([(0.508, -1.27), (0.508, -2.286)], 0.508), g_poly([(0.508, 1.778), (2.54, 1.778), (2.54, 2.54)]),
         g_poly([(0.508, -1.778), (2.54, -1.778), (2.54, -2.54)]), g_poly([(0.508, 0), (2.54, 0), (2.54, -1.778)]),
         g_poly([(0.762, 0), (1.778, 0.381), (1.778, -0.381), (0.762, 0)], fill="outline")],
        [P(-5.08, 0, 0, 4.826, "input", "G", "1"), P(2.54, 5.08, 270, 2.54, "passive", "D", "2"),
         P(2.54, -5.08, 90, 2.54, "passive", "S", "3")], names=False, numbers=False, ref_at=(5.08, 1.27), val_at=(5.08, -1.27)))
add(Sym("Trimmer", "RP", "Trimmer, 3296W: 1 and 3 the track ends, 2 the wiper",
        [g_rect(-1.016, -2.54, 1.016, 2.54), g_poly([(2.54, 0), (1.524, 0)]),
         g_poly([(1.143, 0), (1.905, 0.508), (1.905, -0.508), (1.143, 0)], fill="outline")],
        [P(0, 3.81, 270, 1.27, "passive", "1", "1"), P(0, -3.81, 90, 1.27, "passive", "3", "3"),
         P(3.81, 0, 180, 1.27, "passive", "W", "2")], names=False, numbers=False, ref_at=(-2.54, 1.27), val_at=(-2.54, -1.27)))
add(Sym("Barrel_Jack_Switch", "XS", "DC barrel jack: 1 centre pin, 2 sleeve, 3 the sleeve's switch contact",
        [g_rect(-7.62, -3.81, 2.54, 3.81), g_rect(-6.35, 1.905, -1.27, 3.175, "outline"),
         g_poly([(-1.27, 2.54), (2.54, 2.54)]), g_poly([(2.54, -2.54), (-3.81, -2.54), (-4.572, -1.524), (-5.334, -2.54)]),
         g_poly([(2.54, 0), (-0.762, 0), (-1.27, -0.762), (-1.778, 0)])],
        [P(5.08, 2.54, 180, 2.54, "passive", "+", "1"), P(5.08, 0, 180, 2.54, "passive", "SW", "3"),
         P(5.08, -2.54, 180, 2.54, "passive", "-", "2")], names=False, numbers=True, ref_at=(-2.54, 5.08), val_at=(-2.54, -5.08)))
add(Sym("MountingHole", "H", "M3 standoff hole, no pad", [g_circ(0, 0, 1.778, 0.508)], [],
        names=False, numbers=False, in_bom=False, ref_at=(2.54, 0.635), val_at=(2.54, -1.27)))


def conn(n, female):
    name = f"Conn_1x{n:02d}_{'Socket' if female else 'Pin'}"
    rows = [((n - 1) / 2 - i) * G for i in range(n)]
    g = [g_rect(-1.27, rows[0] + 1.27, 1.27, rows[-1] - 1.27)]
    for y in rows:
        if female:
            g.append(g_arc((0.508, y + 0.508), (-0.0, y), (0.508, y - 0.508)))
        else:
            g.append(g_rect(-0.254, y + 0.254, 0.762, y - 0.254, "outline"))
    pins = [P(-5.08, y, 0, 3.81, "passive", f"{i + 1}", str(i + 1)) for i, y in enumerate(rows)]
    return add(Sym(name, "X", f"1x{n} {'female socket' if female else 'male pin'} strip, 2.54 mm", g, pins,
                   names=False, numbers=True, ref_at=(0, rows[0] + 3.81), val_at=(0, rows[-1] - 3.81)))


def dip(name, ref, descr, names, types, w, glyph=()):
    """A DIP package drawn as its datasheet draws it: pins 1..n/2 down the left, n..n/2+1 down the right."""
    n = len(names)
    rows = n // 2
    top = (rows - 1) / 2 * G
    g = [g_rect(-w / 2, top + G, w / 2, top - rows * G), g_arc((-1.27, top + G), (0, top + G - 1.27), (1.27, top + G))] + list(glyph)
    pins = []
    for k in range(1, n + 1):
        if k <= rows:
            x, y, rot = -w / 2 - G, top - (k - 1) * G, 0
        else:
            x, y, rot = w / 2 + G, top - (n - k) * G, 180
        pins.append(P(x, y, rot, G, types[k - 1], names[k - 1], str(k)))
    return add(Sym(name, ref, descr, g, pins, names=True, numbers=True,
                   ref_at=(-w / 2, top + G + 1.27), val_at=(-w / 2, top - rows * G - 1.27)))


dip("K155ID1", "U", "К155ИД1: BCD to decimal nixie driver, open-collector outputs. SN74141 pinout, DIP-16.",
    ["Q8", "Q9", "A", "D", "VCC", "B", "C", "Q2", "Q3", "Q7", "Q6", "GND", "Q4", "Q5", "Q1", "Q0"],
    ["open_collector"] * 2 + ["input"] * 2 + ["power_in"] + ["input"] * 2 + ["open_collector"] * 4 + ["power_in"] + ["open_collector"] * 4,
    15.24)
dip("MCP23017", "U", "MCP23017-E/SP: 16-bit I2C port expander, 300-mil SPDIP-28, datasheet pin order.",
    [f"GPB{k}" for k in range(8)] + ["VDD", "VSS", "NC", "SCL", "SDA", "NC", "A0", "A1", "A2", "~{RESET}", "INTB", "INTA"]
    + [f"GPA{k}" for k in range(8)],
    ["bidirectional"] * 8 + ["power_in", "power_in", "no_connect", "input", "bidirectional", "no_connect",
                             "input", "input", "input", "input", "output", "output"] + ["bidirectional"] * 8,
    20.32)
dip("LM393", "U", "LM393: dual comparator, open-collector outputs, DIP-8.",
    ["OUT1", "IN1-", "IN1+", "GND", "IN2+", "IN2-", "OUT2", "V+"],
    ["open_collector", "input", "input", "power_in", "input", "input", "open_collector", "power_in"], 12.7)
dip("TC4420", "U", "TC4420: 6 A non-inverting MOSFET driver, DIP-8. Pins 6 and 7 are the one output, doubled; "
    "pin 7 is typed passive so the pair does not read as two outputs fighting.",
    ["VDD", "IN", "NC", "GND", "GND", "OUT", "OUT", "VDD"],
    ["power_in", "input", "no_connect", "power_in", "power_in", "output", "passive", "power_in"], 12.7)
dip("TLP627", "U", "TLP627: Darlington optocoupler, 300 V, DIP-4: 1 LED anode, 2 LED cathode, 3 emitter, 4 collector.",
    ["A", "K", "E", "C"], ["passive", "passive", "passive", "passive"], 12.7,
    glyph=[g_poly([(-3.81, 0.762), (-2.794, -0.508), (-4.826, -0.508), (-3.81, 0.762)]),
           g_poly([(-4.826, 0.762), (-2.794, 0.762)]),
           g_poly([(-1.524, 0.254), (0.254, 0.254)]), g_poly([(-1.524, -0.508), (0.254, -0.508)]),
           g_poly([(1.524, 1.27), (1.524, -1.778)], 0.508), g_poly([(1.524, 0), (3.302, 1.27)]),
           g_poly([(1.524, -0.508), (3.302, -1.778)])])
dip("RN_Isolated_8", "RN", "Isolated resistor network, 8 resistors in DIP-16: resistor k between pin k and pin 17-k.",
    [""] * 16, ["passive"] * 16, 10.16,
    glyph=[g for k in range(8) for g in (g_rect(-2.54, 3.5 * G - k * G + 0.508, 2.54, 3.5 * G - k * G - 0.508),
                                         g_poly([(-5.08, 3.5 * G - k * G), (-2.54, 3.5 * G - k * G)]),
                                         g_poly([(2.54, 3.5 * G - k * G), (5.08, 3.5 * G - k * G)]))])
dip("Arduino_Nano", "U", "Arduino Nano v3 on two 1x15 sockets, KiCad Module:Arduino_Nano numbering, "
    "drawn as the module's two rows: 1 D1/TX .. 15 D12 down one side, 30 VIN .. 16 D13 down the other.",
    ["D1/TX", "D0/RX", "~{RESET}", "GND", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10", "D11", "D12",
     "D13", "3V3", "AREF", "A0", "A1", "A2", "A3", "A4/SDA", "A5/SCL", "A6", "A7", "+5V", "~{RESET}", "GND", "VIN"],
    ["bidirectional", "bidirectional", "input", "power_in"] + ["bidirectional"] * 12
    + ["power_out", "passive"] + ["bidirectional"] * 6 + ["input", "input", "power_in", "input", "power_in", "power_in"],
    20.32)
add(Sym("R-78E", "U", "R-78E switching regulator module, 78xx pinout: 1 +Vin, 2 GND, 3 +Vout",
        [g_rect(-7.62, -3.81, 7.62, 3.81)],
        [P(-10.16, 1.27, 0, 2.54, "power_in", "+Vin", "1"), P(0, -6.35, 90, 2.54, "power_in", "GND", "2"),
         P(10.16, 1.27, 180, 2.54, "power_out", "+Vout", "3")], ref_at=(-7.62, 5.08), val_at=(2.54, -5.08)))
add(Sym("DS3231_Module", "U", "DS3231 mini RTC module on a 5-way header, as the stock board's RTC MINI: - NC C D +",
        [g_rect(-5.08, -7.62, 7.62, 7.62)],
        [P(-7.62, 5.08, 0, 2.54, "power_in", "-", "1"), P(-7.62, 2.54, 0, 2.54, "no_connect", "NC", "2"),
         P(-7.62, 0, 0, 2.54, "input", "C/SCL", "3"), P(-7.62, -2.54, 0, 2.54, "bidirectional", "D/SDA", "4"),
         P(-7.62, -5.08, 0, 2.54, "power_in", "+", "5")], ref_at=(-5.08, 8.89), val_at=(-5.08, -8.89)))


def tube(name, descr, anode_pad, cathodes, h, w=None):
    """A tube drawn with its anode on top and its leads along the foot in the datasheet's order.
    cathodes: [(pad, name)] in lead order; a None name is a pad with no lead (no_connect)."""
    n = len(cathodes)
    w = w or (n + 1) * G
    top, bot = h / 2, -h / 2
    g = [g_rect(-w / 2, bot, w / 2, top)]
    pins = [P(0, top + G, 270, G, "passive", "A", anode_pad)]
    for i, (pad, nm) in enumerate(cathodes):
        x = (i - (n - 1) / 2) * G
        pins.append(P(x, bot - G, 90, G, "passive" if nm else "no_connect", nm or "NC", pad))
    return add(Sym(name, "V", descr, g, pins, names=True, numbers=True, offset=0.762,
                   ref_at=(w / 2 + 1.27, top), val_at=(w / 2 + 1.27, top - 2.54)))


def _socket_order():
    # ИН-12/ИН-15 datasheet pin d sits on socket pad ((7 - d) mod 12) + 1 (tools/ts06main.py IN12_PAD)
    return [str(((7 - d) % 12) + 1) for d in range(1, 13)]


_ORD = _socket_order()          # datasheet pins 1..12 -> pads: 7 6 5 4 3 2 1 12 11 10 9 8
import ts06main as _M           # noqa: E402  (the pad maps only)
tube("IN-12A", "ИН-12А digit tube on TS06_IN12_Socket. Pins are socket pads; drawn in the datasheet's order: "
     "pin 1 the anode, then 0 9 8 7 6 5 4 3 2 1, pin 12 no lead.",
     _ORD[0], [(p, _M.IN12_PAD[int(p)]) for p in _ORD[1:]], 7.62)
tube("IN-15A", "ИН-15А symbol tube (m, k, M, P, %, +, -, n, u, Pi) on the ИН-12 socket, datasheet order, anode pin 1.",
     _ORD[0], [(p, _M.IN15A_PAD[int(p)]) for p in _ORD[1:]], 17.78)
tube("IN-15B", "ИН-15Б symbol tube (W, F, Hz, H, V, S, A, Ohm) on the ИН-12 socket, datasheet order, anode pin 1.",
     _ORD[0], [(p, _M.IN15B_PAD[int(p)]) for p in _ORD[1:]], 17.78)
tube("IN-17", "ИН-17 digit tube, wire-ended. Leads in their order round the base as TS06_IN17_Socket places them: "
     "the anode, then 0 1 2 3 4 5 6 7 8 9.", "A", [(str(d), str(d)) for d in range(10)], 7.62)
add(Sym("INS-1", "V", "ИНС-1 neon lamp: pin 1 takes the ballast (anode side), pin 2 the return (cathode side).",
        [g_rect(-2.54, -2.54, 2.54, 2.54), g_circ(0, 0, 1.778), g_poly([(-1.016, 0.635), (1.016, 0.635)]),
         g_poly([(-1.016, -0.635), (1.016, -0.635)])],
        [P(0, 5.08, 270, 2.54, "passive", "A", "1"), P(0, -5.08, 90, 2.54, "passive", "K", "2")],
        names=False, numbers=True, ref_at=(3.81, 1.27), val_at=(3.81, -1.27)))


def power_sym(name, graphics, pin_rot, et="power_in", val_at=(0, 3.556), ref="#PWR"):
    return add(Sym(name, ref, f'Power symbol, the global net "{name}"' if et == "power_in" else
                   "Tells ERC where the power on a net really comes from", graphics,
                   [P(0, 0, pin_rot, 0, et, "", "1")], power=True, names=False, numbers=False, offset=0,
                   ref_at=(0, -3.81), val_at=val_at))


power_sym("GND", [g_poly([(0, 0), (0, -1.27), (1.27, -1.27), (0, -2.54), (-1.27, -1.27), (0, -1.27)], 0)], 270, val_at=(0, -3.81))
power_sym("+5V", [g_poly([(-0.762, 1.27), (0, 2.54)], 0), g_poly([(0, 2.54), (0.762, 1.27)], 0), g_poly([(0, 0), (0, 2.54)], 0)], 90)
power_sym("+12V", [g_poly([(-0.762, 1.27), (0, 2.54)], 0), g_poly([(0, 2.54), (0.762, 1.27)], 0), g_poly([(0, 0), (0, 2.54)], 0)], 90)
power_sym("PWR_FLAG", [g_poly([(0, 0), (0, 1.27), (-1.016, 1.905), (0, 2.54), (1.016, 1.905), (0, 1.27)], 0)], 90,
          et="power_out", val_at=(0, 3.81), ref="#FLG")


def symbol_for(p):
    """The symbol a ts06pair.py part is drawn with, from its value and footprint."""
    v, fp, ref = p.value.upper(), p.fp.upper(), p.ref
    if ref.startswith("XP"):
        return conn_sym(len(p.pins), False)
    if ref.startswith("XS") and "PINSOCKET" in fp:
        return conn_sym(len(p.pins), True)
    table = [("K155ID1", "K155ID1"), ("MCP23017", "MCP23017"), ("LM393", "LM393"), ("TC4420", "TC4420"),
             ("MCP1407", "TC4420"), ("TLP627", "TLP627"), ("R-78E", "R-78E"), ("ARDUINO NANO", "Arduino_Nano"),
             ("DS3231", "DS3231_Module"), ("IN-12", "IN-12A"), ("IN-15A", "IN-15A"), ("IN-15B", "IN-15B"),
             ("IN-17", "IN-17"), ("INS-1", "INS-1"), ("MPSA42", "Q_NPN_EBC"), ("IRF", "Q_NMOS_GDS"),
             ("PTC", "Polyfuse"), ("DC 5.5", "Barrel_Jack_Switch"), ("8X220R", "RN_Isolated_8")]
    for key, sym in table:
        if key in v:
            return sym
    if "BARRELJACK" in fp:
        return "Barrel_Jack_Switch"
    if "JST_PH" in fp or "PINHEADER" in fp or "PINSOCKET" in fp:
        return conn_sym(len(p.pins), "SOCKET" in fp)
    if "TRIMMER" in fp:
        return "Trimmer"
    if fp.startswith("TS06_LED"):
        return "LED"
    if "TO-92" in fp:
        return "Q_NPN_EBC"
    if "TO-220" in fp:
        return "Q_NMOS_GDS"
    if fp.startswith("TS06_D_") or ref.startswith("VD"):
        if "582" in v or "SCHOTTKY" in v or "SS1" in v or "SR" == v[:2]:
            return "D_Schottky"
        if "TVS" in v or "ZENER" in v or "BZX" in v or "P6KE" in v or "SMBJ" in v or "1.5KE" in v or "1N47" in v:
            return "D_Zener"
        return "D"
    if fp.startswith("TS06_CP_"):
        return "CP"
    if fp.startswith("TS06_C_") or ref.startswith("C"):
        return "C"
    if fp.startswith("TS06_L_") or ref.startswith("L"):
        return "L"
    if ref.startswith("RN"):
        return "RN_Isolated_8"
    if ref.startswith("R") and len(p.pins) == 2:
        return "R"
    if ref.startswith("F"):
        return "Polyfuse"
    return conn_sym(len(p.pins), False, generic=True)


def conn_sym(n, female, generic=False):
    name = f"Conn_1x{n:02d}_{'Socket' if female else 'Pin'}"
    if name not in SYMS:
        conn(n, female)
    return name


# ==================================================================== the board files
def board_footprints(board):
    """ref -> {lib, value, attrs, pads{pad: net}} as the board file has them, or {} if it is missing."""
    proj = BOARDS[board][0]
    path = os.path.join(ROOT, "PCB", proj, proj + ".kicad_pcb")
    if not os.path.exists(path):
        return {}
    tree = sexp.parse(open(path, encoding="utf8").read())
    out = {}
    for fp in sexp.find_all(tree, "footprint"):
        props = {sexp.unq(p[1]): sexp.unq(p[2]) for p in sexp.find_all(fp, "property")}
        attr = sexp.find(fp, "attr")
        pads = {}
        for pd in sexp.find_all(fp, "pad"):
            nt = sexp.find(pd, "net")
            if sexp.unq(pd[1]):
                pads[sexp.unq(pd[1])] = sexp.unq(nt[-1]) if nt else None
        out[props["Reference"]] = dict(lib=sexp.unq(fp[1]), value=props.get("Value", ""),
                                       attrs=set(attr[1:]) if attr else set(), pads=pads)
    return out


# ==================================================================== one sheet
DIRS = {"right": (1, 0), "left": (-1, 0), "up": (0, -1), "down": (0, 1)}


def dir_name(d):
    return {(1, 0): "right", (-1, 0): "left", (0, -1): "up", (0, 1): "down"}[tuple(d)]


def to_sheet(px, py, X, Y, rot):
    a = math.radians(rot)
    sx = px * math.cos(a) - py * math.sin(a)
    sy = px * math.sin(a) + py * math.cos(a)
    return round(X + sx, 4), round(Y - sy, 4)


def vec(ang):
    a = math.radians(ang)
    return (int(round(math.cos(a))), int(-round(math.sin(a))))


def text_w(t, sz=1.27):
    return len(t) * sz * 0.9


class Sheet:
    PAPER = {"A4": (297, 210), "A3": (420, 297), "A2": (594, 420)}

    def __init__(self, board, sec, page, paper="A3"):
        self.board, self.sec, self.page = board, sec, page
        self.proj, self.bconst = BOARDS[board]
        self.paper = paper
        self.W, self.H = self.PAPER[paper]
        self.parts = {}
        self.pins = {}
        self.segs, self.labels, self.powers, self.flags, self.ncs, self.texts, self.tables = [], [], [], [], [], [], []
        self.junctions = []
        self.done = set()
        self.skipped = []
        self.bparts = TP.parts(self.bconst)
        self.holes = []                 # pinless symbols read from the board (mounting holes)
        self.labels_only = False

    # ---------------------------------------------------------------- nets
    def net(self, pr):
        ref, pin = self.res(pr).split(".", 1)
        return self.bparts[ref].pins.get(pin)

    def res(self, pr):
        """'R64.2' is a pin by number; 'R64:FB' is whichever pin of R64 carries FB (or 'R64.?')."""
        if isinstance(pr, str) and ":" in pr:
            ref, net = pr.split(":", 1)
            p = self.bparts.get(ref)
            if p:
                for k, v in p.pins.items():
                    if v == net:
                        return f"{ref}.{k}"
            return f"{ref}.?"
        return pr

    def pt(self, a):
        return self.pins[self.res(a)][:2] if isinstance(a, str) else (snap(a[0]), snap(a[1]))

    def pinnum(self, ref, net, default):
        r = self.res(f"{ref}:{net}")
        return r.split(".")[1] if not r.endswith(".?") else default

    def h2(self, ref, x, y, left):
        """A two-pin part lying across (x, y)..(x + 7.62, y), the pin carrying `left` on the left."""
        if ref not in self.bparts:
            return
        sym = symbol_for(self.bparts[ref])
        l = self.pinnum(ref, left, "1" if sym not in HORIZ else "2")
        if sym in HORIZ:
            self.put(ref, x + 3.81, y, 0 if l == "2" else 180)
        else:
            self.put(ref, x + 3.81, y, 90 if l == "1" else 270)

    def v2(self, ref, x, y, top):
        """A two-pin part standing on (x, y)..(x, y + 7.62), the pin carrying `top` on top."""
        if ref not in self.bparts:
            return
        sym = symbol_for(self.bparts[ref])
        t = self.pinnum(ref, top, "1" if sym not in HORIZ else "2")
        if sym in HORIZ:
            self.put(ref, x, y + 3.81, 270 if t == "2" else 90)
        elif sym == "Trimmer":
            self.put(ref, x, y + 3.81, 0 if t == "1" else 180)
        else:
            self.put(ref, x, y + 3.81, 0 if t == "1" else 180)

    def shunt(self, ref, x, y, top, drop=G):
        """A part hanging from the rail point (x, y): wired to it, its other end tagged below."""
        if ref not in self.bparts:
            return
        self.v2(ref, x, y + drop, top)
        self.link((x, y), f"{ref}:{top}")
        for pr in [k for k in self.pins if k.startswith(ref + ".")]:
            self.tag(pr)

    def P(self, pr):
        return self.pins[pr][:2]

    def X(self, pr):
        return self.pins[pr][0]

    def Y(self, pr):
        return self.pins[pr][1]

    # ---------------------------------------------------------------- placing
    def put(self, ref, x, y, rot=0, sym=None, fields=None):
        if ref not in self.bparts or ref in self.parts:
            return False
        p = self.bparts[ref]
        sym = sym or symbol_for(p)
        S = SYMS[sym]
        x, y = snap(x), snap(y)
        self.parts[ref] = dict(sym=sym, x=x, y=y, rot=rot, fields=fields)
        for num, (px, py, prot, ln, et, nm) in S.pins.items():
            sx, sy = to_sheet(px, py, x, y, rot)
            self.pins[f"{ref}.{num}"] = (sx, sy, vec(prot + 180 + rot))
        return True

    def wire(self, *pts):
        if self.labels_only:
            return
        pts = [self.pt(p) for p in pts]
        for a, b in zip(pts, pts[1:]):
            if a == b:
                continue
            assert a[0] == b[0] or a[1] == b[1], ("diagonal wire", a, b)
            self.segs.append((a, b))

    def link(self, a, b, *via, mode="hv"):
        """Wire two pins (or a pin and a point) - only if ts06pair.py puts them on one net."""
        if self.labels_only:
            return False
        a, b = (self.res(x) if isinstance(x, str) else x for x in (a, b))
        via = tuple(self.res(v) if isinstance(v, str) else v for v in via)
        if any(isinstance(x, str) and x not in self.pins for x in (a, b)):
            if any(isinstance(x, str) and x.split(".")[0] in self.parts for x in (a, b)):
                self.skipped.append((a, b))     # a placed part no longer has a pin on that net
            return False
        nets = {self.net(x) for x in (a, b) if isinstance(x, str)}
        if None in nets or len(nets) > 1:
            self.skipped.append((a, b))
            return False
        pa, pb = self.pt(a), self.pt(b)
        if via:
            path = [pa] + [self.pt(v) for v in via] + [pb]
        elif pa[0] == pb[0] or pa[1] == pb[1]:
            path = [pa, pb]
        elif mode == "hv":
            path = [pa, (pb[0], pa[1]), pb]
        else:
            path = [pa, (pa[0], pb[1]), pb]
        self.wire(*path)
        for x in (a, b):
            if isinstance(x, str):
                self.done.add(x)
        return True

    def glabel(self, x, y, net, d="right", bold=None, shape="passive"):
        rot, just = {"right": (0, "left"), "left": (180, "right"), "up": (90, "left"), "down": (270, "right")}[d]
        bold = (net == "HV185") if bold is None else bold
        self.labels.append(dict(net=net, x=snap(x), y=snap(y), rot=rot, just=just, bold=bold, shape=shape, d=d))

    def power(self, x, y, net, d=None):
        """GND points down, the supplies up, unless d says otherwise."""
        d = d or ("down" if net == "GND" else "up")
        if net == "GND":
            r = {"down": 0, "up": 180, "left": 270, "right": 90}[d]
        else:
            r = {"up": 0, "down": 180, "left": 90, "right": 270}[d]
        self.powers.append(dict(net=net, x=snap(x), y=snap(y), rot=r))

    def pflag(self, x, y, d="up"):
        self.flags.append(dict(x=snap(x), y=snap(y), rot={"up": 0, "down": 180, "left": 90, "right": 270}[d]))

    def tag(self, pr, length=G, d=None, text_d=None, pw_d=None):
        """A stub out of a pin and its net's label or power symbol; a no-connect flag if it has none."""
        pr = self.res(pr)
        if pr not in self.pins or pr in self.done:
            return
        x, y, out = self.pins[pr]
        net = self.net(pr)
        self.done.add(pr)
        if net is None:
            self.ncs.append((x, y))
            return
        dv = DIRS[d] if d else out
        ex, ey = snap(x + dv[0] * length), snap(y + dv[1] * length)
        self.segs.append(((x, y), (ex, ey)))
        if net in POWER_NETS:
            if pw_d is None:
                if net == "GND":
                    pw_d = "up" if dv == (0, -1) else "down"
                else:
                    pw_d = "down" if dv == (0, 1) else "up"
            self.power(ex, ey, net, pw_d)
        else:
            self.glabel(ex, ey, net, text_d or dir_name(dv))

    def name(self, at, pr, d="up", length=G, text_d=None):
        """A flag label on a wire: a short stub off the point `at`, the label on its end."""
        pr = self.res(pr)
        if self.labels_only or pr not in self.pins:
            return
        net = self.net(pr)
        if net is None:
            return
        x, y = self.pt(at)
        dv = DIRS[d]
        ex, ey = snap(x + dv[0] * length), snap(y + dv[1] * length)
        self.wire((x, y), (ex, ey))
        if net in POWER_NETS:
            self.power(ex, ey, net)
        else:
            self.glabel(ex, ey, net, text_d or ("right" if d in ("up", "down") else d))

    def route_tag(self, pr, *pts, d=None, pw_d=None):
        """Like tag, but the stub follows pts and the label or power symbol sits on the last one."""
        pr = self.res(pr)
        if self.labels_only or pr not in self.pins or pr in self.done:
            return
        net = self.net(pr)
        self.done.add(pr)
        if net is None:
            self.ncs.append(self.pins[pr][:2])
            return
        path = [self.pins[pr][:2]] + [self.pt(p) for p in pts]
        self.wire(*path)
        (ax, ay), (bx, by) = path[-2], path[-1]
        last = dir_name(((bx > ax) - (bx < ax), (by > ay) - (by < ay)))
        if net in POWER_NETS:
            self.power(bx, by, net, pw_d)
        else:
            self.glabel(bx, by, net, d or last)

    def end_label(self, at, pr, d):
        """The label of pr's net on a wire end drawn by hand (nothing if the pin is gone)."""
        pr = self.res(pr)
        if self.labels_only or pr not in self.pins or self.net(pr) is None:
            return
        x, y = self.pt(at)
        if self.net(pr) in POWER_NETS:
            self.power(x, y, self.net(pr), d)
        else:
            self.glabel(x, y, self.net(pr), d)

    def pwr_at(self, at, pr, d=None):
        """A power symbol straight on a wire point, if the pin's net is a supply."""
        pr = self.res(pr)
        if self.labels_only or pr not in self.pins:
            return
        net = self.net(pr)
        if net in POWER_NETS:
            x, y = self.pt(at)
            self.power(x, y, net, d)

    def note(self, t, x, y, sz=1.27, bold=False, width=None):
        if width:
            t = "\n".join(textwrap.fill(par, width) if par else "" for par in t.split("\n"))
        self.texts.append(dict(t=t, x=snap(x), y=snap(y), sz=sz, bold=bold))
        return y + (t.count("\n") + 1) * sz * 1.7

    def table(self, x, y, colw, rows, sz=1.27):
        rh = 2.54 * sz / 1.27 + 1.27
        self.tables.append(dict(x=snap(x), y=snap(y), colw=colw, rows=rows, sz=sz, rh=rh))
        return y + len(rows) * rh

    # ---------------------------------------------------------------- the rest of the parts
    def auto_place(self, refs, x0, y0, x1):
        """Parts the layout does not know: rows from (x0, y0), every pin a stub and a label."""
        x, y, rowh = x0, y0, 0
        for ref in refs:
            S = SYMS[symbol_for(self.bparts[ref])]
            bx0, by0, bx1, by1 = S.bbox
            lw = max([text_w(n or "") for n in self.bparts[ref].pins.values() if n] + [0]) + 3 * G
            w = (bx1 - bx0) + 2 * lw
            h = (by1 - by0) + 3 * lw / 2 + 6
            if x + w > x1 and x > x0:
                x, y, rowh = x0, y + rowh, 0
            self.put(ref, x + lw - bx0, y + by1 + lw / 2 + 3)
            for pr in [k for k in list(self.pins) if k.startswith(ref + ".")]:
                self.tag(pr, length=2 * G)
            x += w
            rowh = max(rowh, h)
        return y + rowh

    # ---------------------------------------------------------------- tidy and trace
    def top(self, skip_texts=2):
        """The highest point drawn below the heading (the first skip_texts texts)."""
        ys = []
        for ref, pi in self.parts.items():
            S = SYMS[pi["sym"]]
            x0, y0, x1, y1 = S.bbox
            for px, py in ((x0, y0), (x0, y1), (x1, y0), (x1, y1)):
                ys.append(to_sheet(px, py, pi["x"], pi["y"], pi["rot"])[1] - 3.2)
        ys += [l["y"] - (text_w(l["net"]) + 3 if l["d"] == "up" else 1.6) for l in self.labels]
        ys += [p["y"] - 4.5 for p in self.powers] + [p["y"] - 4.5 for p in self.flags]
        ys += [a[1] for a, b in self.segs] + [b[1] for a, b in self.segs]
        ys += [t["y"] for t in self.texts[skip_texts:]] + [t["y"] for t in self.tables]
        ys += [h["y"] - 3 for h in self.holes if h.get("x")]
        return min(ys) if ys else None

    def bottom(self):
        ys = []
        for ref, pi in self.parts.items():
            S = SYMS[pi["sym"]]
            x0, y0, x1, y1 = S.bbox
            for px, py in ((x0, y0), (x0, y1), (x1, y0), (x1, y1)):
                ys.append(to_sheet(px, py, pi["x"], pi["y"], pi["rot"])[1] + 3.2)
        ys += [l["y"] + (text_w(l["net"]) + 3 if l["d"] == "down" else 1.6) for l in self.labels]
        ys += [p["y"] + 4.5 for p in self.powers]
        ys += [a[1] for a, b in self.segs] + [b[1] for a, b in self.segs]
        ys += [t["y"] + (t["t"].count("\n") + 1) * t["sz"] * 1.7 for t in self.texts[2:]]
        ys += [t["y"] + len(t["rows"]) * t["rh"] for t in self.tables]
        ys += [h["y"] + 3 for h in self.holes if h.get("x")]
        return max(ys) if ys else 40.0

    def shift(self, dy):
        """Move everything but the heading up or down by dy (a whole number of 2.54 mm steps)."""
        for pi in self.parts.values():
            pi["y"] = snap(pi["y"] + dy)
        self.pins = {k: (x, snap(y + dy), o) for k, (x, y, o) in self.pins.items()}
        self.segs = [((a[0], snap(a[1] + dy)), (b[0], snap(b[1] + dy))) for a, b in self.segs]
        for coll in (self.labels, self.powers, self.flags, self.tables, self.texts[2:], [h for h in self.holes if h.get("x")]):
            for it in coll:
                it["y"] = snap(it["y"] + dy)
        self.ncs = [(x, snap(y + dy)) for x, y in self.ncs]
        self.foot += dy
        if self.notes_at:
            self.notes_at = (self.notes_at[0], snap(self.notes_at[1] + dy), self.notes_at[2])

    def tag_rest(self):
        for pr in list(self.pins):
            self.tag(pr)

    def points(self):
        pts = set()
        for a, b in self.segs:
            pts.update((a, b))
        pts.update((x, y) for x, y, _ in self.pins.values())
        pts.update((l["x"], l["y"]) for l in self.labels)
        pts.update((p["x"], p["y"]) for p in self.powers)
        pts.update((p["x"], p["y"]) for p in self.flags)
        return pts

    def normalise(self):
        """Break every wire at each connection point lying inside it, as KiCad does on save, and
        drop duplicates; then put a junction dot wherever three or more connections meet."""
        for _ in range(4):
            pts = self.points()
            out = set()
            for a, b in self.segs:
                inner = sorted((p for p in pts if p != a and p != b and _on(p, a, b)),
                               key=lambda p: abs(p[0] - a[0]) + abs(p[1] - a[1]))
                chain = [a] + inner + [b]
                for u, v in zip(chain, chain[1:]):
                    out.add((u, v) if u <= v else (v, u))
            if out == set(self.segs):
                break
            self.segs = sorted(out)
        count = {}
        for a, b in self.segs:
            count[a] = count.get(a, 0) + 1
            count[b] = count.get(b, 0) + 1
        for x, y, _ in self.pins.values():
            if (x, y) in count:
                count[(x, y)] += 1
        self.junctions = sorted(p for p, n in count.items() if n >= 3)

    def trace(self):
        """Connectivity as KiCad reads it. Returns (problems, {net name: set of ref.pin})."""
        par = {}

        def find(x):
            par.setdefault(x, x)
            while par[x] != x:
                par[x] = par[par[x]]
                x = par[x]
            return x

        for a, b in self.segs:
            par[find(a)] = find(b)
        ends = {}
        for a, b in self.segs:
            ends[a] = ends.get(a, 0) + 1
            ends[b] = ends.get(b, 0) + 1
        pinat = {}
        for pr, (x, y, _) in self.pins.items():
            pinat.setdefault((x, y), []).append(pr)
        names = {}
        for l in self.labels:
            names.setdefault((l["x"], l["y"]), set()).add(l["net"])
        for p in self.powers:
            names.setdefault((p["x"], p["y"]), set()).add(p["net"])
        bad = []
        ncs = set(self.ncs)
        for pt, n in ends.items():
            if n == 1 and pt not in pinat and pt not in names and pt not in {(f_["x"], f_["y"]) for f_ in self.flags}:
                bad.append(f"dangling wire end at {pt}")
        for pt in list(names) + [(f_["x"], f_["y"]) for f_ in self.flags]:
            if pt not in ends and pt not in pinat:
                bad.append(f"label or power symbol on nothing at {pt}")
        comp = {}
        for pt, prs in pinat.items():
            for pr in prs:
                net = self.net(pr)
                if net is None:
                    if pt not in ncs or pt in ends or len(prs) > 1:
                        bad.append(f"{pr} has no net but is not flagged no-connect, or is wired")
                    continue
                if pt in ncs:
                    bad.append(f"{pr} carries {net} but has a no-connect flag")
                if pt not in ends and pt not in names and len(prs) == 1:
                    bad.append(f"{pr} ({net}) is dangling")
                comp.setdefault(find(pt), {"pins": set(), "names": set()})["pins"].add(pr)
        for pt, nm in names.items():
            comp.setdefault(find(pt), {"pins": set(), "names": set()})["names"].update(nm)
        bynet = {}
        for c in comp.values():
            nets = {self.net(pr) for pr in c["pins"]}
            if len(nets) > 1:
                bad.append(f"one wire joins {sorted(c['pins'])} of nets {sorted(nets)}")
            if c["names"] and nets and c["names"] != nets:
                bad.append(f"{sorted(c['pins'])} ({sorted(nets)}) is labelled {sorted(c['names'])}")
            if not c["names"]:
                bad.append(f"{sorted(c['pins'])} ({sorted(nets)}) has no label: KiCad would invent its name")
            for nm in c["names"]:
                bynet.setdefault(nm, set()).update(c["pins"])
        return bad, bynet


def _on(p, a, b):
    """p strictly inside the axis-parallel segment a-b."""
    if a[0] == b[0] == p[0]:
        return min(a[1], b[1]) < p[1] < max(a[1], b[1])
    if a[1] == b[1] == p[1]:
        return min(a[0], b[0]) < p[0] < max(a[0], b[0])
    return False


# ==================================================================== writing a sheet
TWO_PIN = {"R", "C", "CP", "L", "Polyfuse"}
HORIZ = {"D", "D_Schottky", "D_Zener", "LED"}


def field_pos(sym, x, y, rot):
    """Where a placed symbol's reference and value go, in sheet coordinates: (x, y, justify)."""
    S = SYMS[sym]
    if sym in TWO_PIN or sym in ("Trimmer",):
        if rot in (0, 180):
            side = -1 if sym == "Trimmer" else 1
            j = "left" if side > 0 else "right"
            return (x + side * 2.54, y - 1.27, j), (x + side * 2.54, y + 1.27, j)
        dy = 3.175 if sym == "Polyfuse" else 2.54
        return (x, y - dy, None), (x, y + dy, None)
    if sym in HORIZ:
        dy = 3.81 if sym == "LED" else 2.54
        if rot in (0, 180):
            return (x, y - dy, None), (x, y + dy, None)
        return (x + 2.54, y - 1.27, "left"), (x + 2.54, y + 1.27, "left")
    rx, ry = to_sheet(S.ref_at[0], S.ref_at[1], x, y, rot)
    vx, vy = to_sheet(S.val_at[0], S.val_at[1], x, y, rot)
    return (rx, ry, "left"), (vx, vy, "left")


def fprop(k, v, x, y, just, hide=False, sz=1.27, rot=0):
    """A field that reads horizontally with the given visual justification, whatever the symbol's
    rotation. KiCad turns a field with its symbol and then flips it to stay readable, which also
    flips its justification (found by plotting all four rotations, 30.09.26)."""
    h = "\n(hide yes)" if hide else ""
    ang = 90 if rot in (90, 270) else 0
    if just and rot in (90, 180):
        just = {"left": "right", "right": "left"}[just]
    j = f"\n(justify {just})" if just else ""
    return (f'(property "{k}" "{esc(v)}"\n(at {f(x)} {f(y)} {ang}){h}\n(effects\n(font\n(size {f(sz)} {f(sz)})\n){j}\n)\n)')


def sheet_body(s, path, fpinfo, pwr_counter):
    """Every item of one sheet as KiCad text; path is the sheet's instance path."""
    out = []
    B, sid = s.board, s.sec["id"]
    for x, y in s.junctions:
        out.append(f'(junction\n(at {f(x)} {f(y)})\n(diameter 0)\n(color 0 0 0 0)\n(uuid "{uid(B, sid, "j", x, y)}")\n)')
    for x, y in sorted(set(s.ncs)):
        out.append(f'(no_connect\n(at {f(x)} {f(y)})\n(uuid "{uid(B, sid, "nc", x, y)}")\n)')
    for a, b in s.segs:
        out.append(f'(wire\n(pts\n(xy {f(a[0])} {f(a[1])}) (xy {f(b[0])} {f(b[1])})\n)\n(stroke\n(width 0)\n(type default)\n)\n'
                   f'(uuid "{uid(B, sid, "w", a, b)}")\n)')
    for l in sorted(s.labels, key=lambda l: (l["net"], l["x"], l["y"])):
        sz = 1.524 if l["bold"] else 1.27
        bold = "\n(bold yes)" if l["bold"] else ""
        out.append(f'(global_label "{esc(l["net"])}"\n(shape {l["shape"]})\n(at {f(l["x"])} {f(l["y"])} {l["rot"]})\n'
                   f'(fields_autoplaced yes)\n(effects\n(font\n(size {f(sz)} {f(sz)}){bold}\n)\n(justify {l["just"]})\n)\n'
                   f'(uuid "{uid(B, sid, "l", l["net"], l["x"], l["y"])}")\n'
                   f'(property "Intersheetrefs" "${{INTERSHEET_REFS}}"\n(at {f(l["x"])} {f(l["y"])} 0)\n(hide yes)\n'
                   f'(effects\n(font\n(size 1.27 1.27)\n)\n(justify {l["just"]})\n)\n)\n)')
    for i, t in enumerate(s.texts):
        bold = "\n(bold yes)" if t["bold"] else ""
        out.append(f'(text "{esc(t["t"])}"\n(exclude_from_sim no)\n(at {f(t["x"])} {f(t["y"])} 0)\n'
                   f'(effects\n(font\n(size {f(t["sz"])} {f(t["sz"])}){bold}\n)\n(justify left top)\n)\n'
                   f'(uuid "{uid(B, sid, "t", i)}")\n)')
    for i, tb in enumerate(s.tables):
        ncol = len(tb["colw"])
        cells = []
        y = tb["y"]
        for r, row in enumerate(tb["rows"]):
            x = tb["x"]
            for c in range(ncol):
                txt = row[c] if c < len(row) else ""
                cells.append(f'(table_cell "{esc(txt)}"\n(exclude_from_sim no)\n(at {f(x)} {f(y)} 0)\n'
                             f'(size {f(tb["colw"][c])} {f(tb["rh"])})\n(margins 0.9525 0.9525 0.9525 0.9525)\n(span 1 1)\n'
                             f'(fill\n(type none)\n)\n(effects\n(font\n(size {f(tb["sz"])} {f(tb["sz"])}){chr(10) + "(bold yes)" if r == 0 else ""}\n)\n'
                             f'(justify left top)\n)\n(uuid "{uid(B, sid, "tab", i, r, c)}")\n)')
                x += tb["colw"][c]
            y += tb["rh"]
        out.append(f'(table\n(column_count {ncol})\n(border\n(external yes)\n(header yes)\n(stroke\n(width 0)\n(type solid)\n)\n)\n'
                   f'(separators\n(rows yes)\n(cols yes)\n(stroke\n(width 0)\n(type solid)\n)\n)\n'
                   f'(column_widths {" ".join(f(w) for w in tb["colw"])})\n(row_heights {" ".join(f(tb["rh"]) for _ in tb["rows"])})\n'
                   f'(cells\n' + "\n".join(cells) + "\n)\n)")
    for ref in sorted(s.parts, key=refkey):
        pi = s.parts[ref]
        p = s.bparts[ref]
        S = SYMS[pi["sym"]]
        x, y, rot = pi["x"], pi["y"], pi["rot"]
        (rx, ry, rj), (vx, vy, vj) = field_pos(pi["sym"], x, y, rot)
        if pi["fields"]:
            fr, fv = pi["fields"]
            if fr:
                rx, ry, rj = x + fr[0], y + fr[1], fr[2]
            if fv:
                vx, vy, vj = x + fv[0], y + fv[1], fv[2]
        bf = fpinfo.get(ref)
        fp = bf["lib"] if bf else "TS06:" + p.fp
        attrs = bf["attrs"] if bf else set()
        pins = "\n".join(f'(pin "{esc(n)}"\n(uuid "{uid(B, "pin", ref, n)}")\n)' for n in S.order)
        out.append(
            f'(symbol\n(lib_id "{LIBNICK}:{pi["sym"]}")\n(at {f(x)} {f(y)} {rot})\n(unit 1)\n(exclude_from_sim no)\n'
            f'(in_bom {"no" if "exclude_from_bom" in attrs else "yes"})\n(on_board yes)\n'
            f'(in_pos_files {"no" if "exclude_from_pos_files" in attrs else "yes"})\n'
            f'(dnp {"yes" if "dnp" in attrs else "no"})\n(uuid "{uid(B, "sym", ref)}")\n'
            f'{fprop("Reference", ref, rx, ry, rj, rot=rot)}\n{fprop("Value", p.value, vx, vy, vj, rot=rot)}\n'
            f'{fprop("Footprint", fp, x, y, None, hide=True)}\n{fprop("Datasheet", "", x, y, None, hide=True)}\n'
            f'{fprop("Description", "", x, y, None, hide=True)}\n{pins}\n'
            f'(instances\n(project "{s.proj}"\n(path "{path}"\n(reference "{ref}")\n(unit 1)\n)\n)\n)\n)')
    for h in s.holes:
        ref, x, y = h["ref"], h["x"], h["y"]
        bf = fpinfo[ref]
        out.append(
            f'(symbol\n(lib_id "{LIBNICK}:MountingHole")\n(at {f(x)} {f(y)} 0)\n(unit 1)\n(exclude_from_sim no)\n'
            f'(in_bom {"no" if "exclude_from_bom" in bf["attrs"] else "yes"})\n(on_board yes)\n'
            f'(in_pos_files {"no" if "exclude_from_pos_files" in bf["attrs"] else "yes"})\n(dnp no)\n'
            f'(uuid "{uid(B, "sym", ref)}")\n'
            f'{fprop("Reference", ref, x + 2.54, y - 0.635, "left")}\n{fprop("Value", bf["value"], x + 2.54, y + 1.27, "left", hide=True)}\n'
            f'{fprop("Footprint", bf["lib"], x, y, None, hide=True)}\n{fprop("Datasheet", "", x, y, None, hide=True)}\n'
            f'{fprop("Description", "", x, y, None, hide=True)}\n'
            f'(instances\n(project "{s.proj}"\n(path "{path}"\n(reference "{ref}")\n(unit 1)\n)\n)\n)\n)')
    for kind, items in (("pwr", s.powers), ("flg", s.flags)):
        for it in sorted(items, key=lambda d: (d.get("net", ""), d["x"], d["y"])):
            x, y, rot = it["x"], it["y"], it["rot"]
            net = it.get("net", "PWR_FLAG")
            pwr_counter[kind] += 1
            ref = f"#PWR{pwr_counter[kind]:03d}" if kind == "pwr" else f"#FLG{pwr_counter[kind]:02d}"
            S = SYMS[net]
            vx, vy = to_sheet(S.val_at[0], S.val_at[1], x, y, rot)
            vj = None
            tip = to_sheet(0, -2.54 if net == "GND" else 2.54, x, y, rot)
            if tip[1] == y:                             # lying on its side: the text beyond the tip
                vj = "left" if tip[0] > x else "right"
                vx, vy = tip[0] + (0.762 if tip[0] > x else -0.762), y
            out.append(
                f'(symbol\n(lib_id "{LIBNICK}:{net}")\n(at {f(x)} {f(y)} {rot})\n(unit 1)\n(exclude_from_sim no)\n'
                f'(in_bom yes)\n(on_board yes)\n(dnp no)\n(uuid "{uid(B, sid, kind, net, x, y)}")\n'
                f'{fprop("Reference", ref, x, y, None, hide=True)}\n{fprop("Value", net, vx, vy, vj, rot=rot)}\n'
                f'{fprop("Footprint", "", x, y, None, hide=True)}\n{fprop("Datasheet", "", x, y, None, hide=True)}\n'
                f'{fprop("Description", "", x, y, None, hide=True)}\n'
                f'(pin "1"\n(uuid "{uid(B, sid, kind, "pin", net, x, y)}")\n)\n'
                f'(instances\n(project "{s.proj}"\n(path "{path}"\n(reference "{ref}")\n(unit 1)\n)\n)\n)\n)')
    return out


def refkey(r):
    m = re.match(r"([A-Z#]+)(\d+)", r)
    return (m.group(1), int(m.group(2))) if m else (r, 0)


def used_syms(s):
    names = {pi["sym"] for pi in s.parts.values()}
    names |= {p["net"] for p in s.powers}
    if s.flags:
        names.add("PWR_FLAG")
    if s.holes:
        names.add("MountingHole")
    return sorted(names)


# ==================================================================== the sections
# In the order a reader follows the signal. `groups` are ts06pair.py part groups; `refs` pulls single
# parts into a section from another group. A group no section names gets a section of its own.
SECTIONS = [
    dict(id="power-in", title="Power in", groups=["power"],
         summary="12 V arrives on a 5.5 x 2.1 mm barrel jack, centre positive; its switch contact is grounded. "
                 "A 1.1 A resettable fuse and a 3 A Schottky (1N5822) guard against overload and reverse polarity. "
                 "A 100 uF bulk capacitor feeds the boost converter's 1.3 A pulses at 31 kHz."),
    dict(id="5v", title="5 V rail", refs=["U14", "C10", "C11", "C3"],
         summary="An R-78E5.0 switching regulator (78xx pinout) makes 5 V from the 12 V rail. "
                 "It feeds the whole 5 V rail, the Nano through its 5V pin. "
                 "10 uF sits on either side of it, and a 10 uF bulk capacitor by the Nano and the decoders."),
    dict(id="hv", title="185 V converter", groups=["hv"],
         summary="L1, the IRF840 and a fast 600 V rectifier boost 12 V to the 185 V anode rail, HV185, held in a "
                 "4.7 uF 400 V reservoir whose bleeder makes it safe about 10 s after power-off. "
                 "D9's clock reaches the MOSFET through a TC4420 driver, and an LM393 holds the driver's input low "
                 "while the divided rail is above a 2.5 V reference. "
                 "The 5k trimmer sets 165-210 V; its wiper is on the grounded end, so an open wiper lowers the rail."),
    dict(id="mcu", title="MCU and I2C", manifest_title="MCU and I²C", groups=["mcu"], refs=["R54", "R55"],
         summary="An Arduino Nano on two 1x15 female strips runs the clock, with the firmware's BOARD_TYPE 4 pin map. "
                 "A4 and A5 carry the I2C bus to the MCP23017 and the RTC module, pulled up to 5 V through 4k7."),
    dict(id="decoders", title="Digit decoders", groups=["decoder"],
         summary="Two К155ИД1 (SN74141 pinout) share the Nano's A0-A3. "
                 "U2 drives the ИН-12 cathode bus through XS11, U17 the ИН-17 pair through XS12 pins 1-10, "
                 "both with the board's own digit map (BOARD_TYPE 4)."),
    dict(id="anodes", title="Anode drivers", groups=["anodes"],
         summary="Six identical channels, one per digit tube. A Nano pin lights a TLP627's LED through 470 R, "
                 "and the opto's 300 V Darlington connects HV185 to the tube's anode through its series resistor. "
                 "The 510k bleed pairs are fitted only if the bench asks for them."),
    dict(id="colon", title="Colon", groups=["colon"],
         summary="Each ИНС-1 colon lamp has its own 220k ballast from HV185, never shared. "
                 "One MPSA42 switches both lamps' common return, PWM-faded from D10."),
    dict(id="ampm", title="AM-PM", manifest_title="AM/PM", groups=["ampm"],
         summary="One MCP23017 at I2C address 0x20 drives two К155ИД1: GPA3..0 pick the ИН-15Б glyph and GPA7..4 "
                 "the ИН-15А glyph; codes 10-15 blank a tube. Each ИН-15 is lit continuously through an 18k anode "
                 "resistor, about 2.5 mA. The expander's port B drives the backlight LEDs."),
    dict(id="rtc", title="RTC", groups=["rtc"],
         summary="The small DS3231 module plugs into a 5-way socket, pin order - NC C D + as the stock board's "
                 "RTC MINI header. It shares the I2C bus with the expander."),
    dict(id="backlight", title="Backlight", groups=["backlight"],
         summary="Eight amber LEDs behind the tubes are each sourced from their own MCP23017 port-B pin through an "
                 "isolated 8 x 220R network; the 'm' LED of AM/PM runs from D12 through 220R. "
                 "All nine cathodes share BL_K behind one MPSA42, so D11's PWM sets the brightness of them all."),
    dict(id="fascia", title="Fascia link", groups=["fascia"],
         summary="The panel cable leaves on a top-entry 6-way JST PH: +5V, GND, A6, A7, D7, D8, the pin order both "
                 "fascia builds share. The 100 nF ladder filters on A6 and A7 sit at this end of the cable."),
    dict(id="stack", title="Board link", groups=["stack"],
         summary="The display board carries male strips (XP) on its back and the driver board the mating female "
                 "strips (XS); pin n of XPk mates pin n of XSk. XP11 carries the ИН-12 cathode bus, XP12 the ИН-17 "
                 "bundle and both ИН-15, and XP21-XP25 the anodes, the colon and the LEDs."),
    dict(id="tubes", title="Tubes", groups=["digits"],
         summary="Four ИН-12А share the cathode bus K0-K9 and the two ИН-17 their own bus KS0-KS9; every tube has "
                 "its own anode line. The display board carries nothing but tubes, lamps, LEDs and the strips."),
]
SEC_BY_ID = {s["id"]: s for s in SECTIONS}


def section_of(p):
    for s in SECTIONS:
        if p.ref in s.get("refs", ()):
            return s["id"]
    for s in SECTIONS:
        if p.group in s.get("groups", ()):
            return s["id"]
    gid = p.group or "misc"
    if gid not in SEC_BY_ID:
        s = dict(id=gid, title=gid.capitalize(), groups=[p.group], summary="")
        SECTIONS.insert(len(SECTIONS) - 2, s)
        SEC_BY_ID[gid] = s
    return gid


def sections_for(board):
    """[(section, [refs])] for one board, in reading order; mounting holes go to the board link."""
    const = BOARDS[board][1]
    refs = {}
    for p in TP.PARTS:
        if p.board == const:
            refs.setdefault(section_of(p), []).append(p.ref)
    out = []
    for s in SECTIONS:
        if s["id"] in refs:
            out.append((s, sorted(refs[s["id"]], key=refkey)))
    return out


_TOKEN = re.compile(r"\b(?:X[PS]\d\d|H10|H1|M10|M1|S10|S1)\b")


def notes_for(board, refs):
    """The ts06pair.py notes of a section's parts, one line each. Notes that differ only in the
    tube or strip they name are merged into one line ('... for H10, H1, M10 in turn ...')."""
    const = BOARDS[board][1]
    by, order = {}, []
    for r in refs:
        n = TP.parts(const)[r].note
        if not n:
            continue
        toks = _TOKEN.findall(n)
        key = _TOKEN.sub("\u00a4", n) if len(toks) == 1 else n
        if key not in by:
            order.append(key)
        by.setdefault(key, []).append((r, toks[0] if len(toks) == 1 else None, n))
    out = []
    for key in order:
        grp = by[key]
        refs_ = [g[0] for g in grp]
        who = ", ".join(refs_) if len(refs_) < 4 else f"{refs_[0]}..{refs_[-1]}"
        if len(grp) == 1 or "\u00a4" not in key:
            out.append((who, grp[0][2]))
        else:
            out.append((who, key.replace("\u00a4", ", ".join(g[1] for g in grp) + " in turn")))
    return out


def ref_ranges(refs):
    """['HL1', 'HL2', 'HL3', 'HL5'] -> 'HL1-HL3/HL5'."""
    out, run = [], []
    for r in sorted(refs, key=refkey):
        if run and refkey(r)[0] == refkey(run[-1])[0] and refkey(r)[1] == refkey(run[-1])[1] + 1:
            run.append(r)
            continue
        if run:
            out.append(run)
        run = [r]
    if run:
        out.append(run)
    return "/".join(f"{g[0]}-{g[-1]}" if len(g) > 2 else "/".join(g) for g in out)


LAYOUTS = {}


def layout(sid, board, paper="A3"):
    def deco(fn):
        LAYOUTS[(sid, board)] = (fn, paper)
        return fn
    return deco


# ==================================================================== the hand layouts
# Millimetres on KiCad's 1.27 mm grid, y down. A wire is drawn only through Sheet.link, which asks
# ts06pair.py first; a label takes its text from the pin it hangs on. Parts are named by reference
# and pins by the net they carry ("R64:FB"), so a pin renumbering in ts06pair.py redraws correctly.

@layout("power-in", "drv", "A4")
def _power_in(s):
    y = 71.12
    flagged = set()
    s.put("XS1", 33.02, y + 2.54)                       # pins 1 / 3 / 2 at x 38.1, y 71.12 / 73.66 / 76.2
    s.h2("F1", 53.34, y, "VIN_J")
    if s.link("XS1:VIN_J", "F1:VIN_J"):
        s.name((45.72, y), "F1:VIN_J")
    s.h2("VD2", 73.66, y, "VIN_F")
    if s.link("F1:VIN_F", "VD2:VIN_F"):
        s.name((67.31, y), "F1:VIN_F")
    # the 12 V rail, from the flag where the jack's 12 V arrives through VD2, past the bulk capacitors
    if s.net("C8:+12V") == "+12V" or s.net("C9:+12V") == "+12V":
        s.wire((88.9, y), (137.16, y))
        s.power(137.16, y, "+12V")
        s.pflag(88.9, y)
        flagged.add("+12V")
        s.link("VD2:+12V", (88.9, y))
        s.shunt("C8", 101.6, y, "+12V")
        s.shunt("C9", 116.84, y, "+12V")
    if s.link("XS1.3", "XS1.2", (43.18, y + 2.54), (43.18, y + 5.08)) and s.net("XS1.2") == "GND":
        s.wire((43.18, y + 5.08), (43.18, y + 10.16))
        s.pwr_at((43.18, y + 10.16), "XS1.2")
        s.wire((43.18, y + 7.62), (50.8, y + 7.62))
        s.pflag(50.8, y + 7.62)                         # ...and ground comes from the sleeve
        flagged.add("GND")
    for i, net in enumerate(sorted({"+12V", "GND"} - flagged)):
        x0 = 160.02 + i * 12.7                          # the drawing above could not carry this flag
        s.wire((x0, y), (x0, y + 5.08))
        if net == "GND":
            s.pflag(x0, y)
            s.power(x0, y + 5.08, net)
        else:
            s.power(x0, y, net)
            s.pflag(x0, y + 5.08, "down")
    s.foot = 92
    s.notes_at = (20.32, 100.33, 115)


@layout("5v", "drv", "A4")
def _five(s):
    y = 71.12
    s.put("U14", 81.28, y + 1.27)                       # +Vin (71.12, y), +Vout (91.44, y), GND below
    if s.link((40.64, y), "U14:+12V"):
        s.pwr_at((40.64, y), "U14:+12V")
        s.shunt("C10", 55.88, y, "+12V")
    s.tag("U14:GND")
    if s.link("U14:+5V", (137.16, y)):
        s.pwr_at((137.16, y), "U14:+5V")
        s.shunt("C11", 104.14, y, "+5V")
        s.shunt("C3", 119.38, y, "+5V")
    s.foot = 92
    s.notes_at = (20.32, 100.33, 115)


@layout("hv", "drv", "A3")
def _hv(s):
    y1, y2 = 71.12, 104.14
    # ---- the power stage: +12V -> L1 -> SW -> VD1 -> HV185
    s.h2("L1", 114.3, y1, "+12V")
    if s.link((106.68, y1), "L1:+12V"):
        s.pwr_at((106.68, y1), "L1:+12V")
    s.h2("VD1", 142.24, y1, "SW")
    if s.link("L1:SW", "VD1:SW"):
        s.name((137.16, y1), "VD1:SW")
    s.put("VT21", 129.54, y2)                           # D (132.08, 99.06), S (132.08, 109.22), G (124.46, y2)
    s.link("VT21:SW", (132.08, y1))
    s.tag("VT21:GND")
    x_end = 246.38
    if s.link("VD1:HV185", (x_end, y1)):
        s.end_label((x_end, y1), "VD1:HV185", "right")
        s.shunt("C7", 162.56, y1, "HV185")
        # the bleeder
        s.v2("R60", 177.8, 73.66, "HV185")
        s.link((177.8, y1), "R60:HV185")
        s.v2("R61", 177.8, 86.36, "BLEED_HV")
        if s.link("R60:BLEED_HV", "R61:BLEED_HV"):
            s.name((177.8, 83.82), "R61:BLEED_HV", "right")
        s.tag("R61:GND")
        # the divider: two 750k, 18k, the trimmer
        x = 205.74
        s.v2("R62", x, 73.66, "HV185")
        s.link((x, y1), "R62:HV185")
        s.v2("R63", x, 86.36, "FB_MID")
        if s.link("R62:FB_MID", "R63:FB_MID"):
            s.name((x, 83.82), "R63:FB_MID", "right")
        s.v2("R64", x, 99.06, "FB")
        if s.link("R63:FB", "R64:FB"):
            s.name((x, 96.52), "R64:FB", "left", length=5.08)
        s.v2("RP1", x, 111.76, "FB_LOW")
        if s.link("R64:FB_LOW", "RP1:FB_LOW"):
            s.name((x, 109.22), "RP1:FB_LOW", "right")
        s.tag("RP1.2")
        s.tag("RP1.3")
    # ---- the gate drive: D9 -> R66 -> PWM_G -> U11 -> GATE_D -> R67 -> GATE
    s.h2("R67", 104.14, y2, "GATE_D")
    if s.link("R67:GATE", "VT21:GATE"):
        s.name((114.3, y2), "VT21:GATE")
        s.shunt("R68", 116.84, y2, "GATE")
    s.put("U11", 78.74, y2)                             # left pins x 69.85, right x 87.63
    if s.link("U11.7", "U11.6", (91.44, 102.87), (91.44, 105.41)) and s.link((91.44, y2), "R67:GATE_D"):
        s.name((93.98, y2), "R67:GATE_D", "down")
    s.tag("U11.8")
    s.tag("U11.5")
    s.tag("U11.1")
    s.tag("U11.4")
    s.h2("R66", 33.02, 102.87, "D9")
    if s.link("R66:PWM_G", "U11:PWM_G"):
        s.name((53.34, 102.87), "U11:PWM_G", "down")
        s.shunt("R71", 45.72, 102.87, "PWM_G")
        s.v2("R65", 58.42, 92.71, "VREF")
        s.link("R65:PWM_G", (58.42, 102.87))
        s.tag("R65:VREF")
    s.v2("C12", 96.52, 116.84, "+12V")
    # ---- regulation: the divided rail against a 2.5 V reference
    s.put("U12", 101.6, 152.4)                          # left pins x 92.71, right x 110.49
    xv = 66.04
    s.v2("R69", xv, 143.51, "+5V")
    s.v2("R70", xv, 156.21, "VREF")
    if s.link("R69:VREF", "R70:VREF") and s.link((xv, 153.67), "U12.3"):
        s.name((68.58, 153.67), "U12.3")
        s.shunt("C14", 78.74, 153.67, "VREF")
    s.tag("U12.1")
    s.tag("U12.2")
    s.tag("U12.4")
    s.tag("U12.8")
    s.tag("U12.6", length=5.08)
    s.route_tag("U12.5", (113.03, 156.21), (113.03, 160.02), d="down")
    s.v2("C13", 127.0, 148.59, "+5V")
    s.foot = 172
    s.notes_at = (20.32, 178, 165)


@layout("mcu", "drv", "A3")
def _mcu(s):
    s.put("U1", 160.02, 105.41)                         # left pins x 147.32, right x 172.72
    for pr in ("U1.4", "U1.29"):
        s.tag(pr, pw_d="left" if pr == "U1.4" else "right")
    s.tag("U1.27", pw_d="right")
    # the I2C pull-ups
    s.v2("R55", 40.64, 91.44, "+5V")
    s.v2("R54", 55.88, 91.44, "+5V")
    s.tag("R55:+5V")
    s.tag("R54:+5V")
    s.route_tag("R55:SCL", (40.64, 109.22), (68.58, 109.22), d="right")
    s.route_tag("R54:SDA", (55.88, 104.14), (68.58, 104.14), d="right")
    s.note("I2C bus: pulled up here; on it U3, the MCP23017 at 0x20 (AM/PM),\nand U13, the DS3231 module (RTC).",
           30.48, 116.84, 1.27)
    # the Nano's pin map, where each line goes
    rows = [["Pin", "Name", "Net", "Does", "Goes to"]]
    S = SYMS["Arduino_Nano"]
    anode_of = {v: k for k, v in TP.TUBE_PIN4.items()}
    for num in S.order:
        net = s.net(f"U1.{num}")
        if not net or net in POWER_NETS:
            continue
        far = [p for p in TP.PARTS if p.board == s.bconst and p.ref != "U1" and net in p.pins.values()]
        secs = []
        for p in far:
            t = SEC_BY_ID[section_of(p)]["title"]
            if t not in secs:
                secs.append(t)
        role = (f"{anode_of[net]} anode" if net in anode_of else
                "I2C" if net in ("SDA", "SCL") else " + ".join(secs))
        rows.append([num, S.pins[num][5].replace("~{RESET}", "RESET"), net, role, goes_to(s.bconst, net, {"U1"})])
    s.table(215.9, 50.8, [10.16, 17.78, 12.7, 38.1, 55.88], rows)
    s.foot = 140
    s.notes_at = (20.32, 150, 110)


@layout("decoders", "drv", "A3")
def _decoders(s):
    for ref, x, cap in (("U2", 88.9, "C4"), ("U17", 203.2, "C17")):
        if not s.put(ref, x, 101.6):
            continue
        for num in SYMS["K155ID1"].order:
            nm = SYMS["K155ID1"].pins[num][5]
            s.tag(f"{ref}.{num}", pw_d={"VCC": "left", "GND": "right"}.get(nm))
        s.v2(cap, x, 124.46, "+5V")
    rows = [["BCD code", "К155ИД1 output", "U2 drives", "U17 drives"]]
    K = SYMS["K155ID1"]
    for c in range(10):
        num = next(n for n in K.order if K.pins[n][5] == f"Q{c}")
        rows.append([str(c), f"Q{c} (pin {num})", s.net(f"U2.{num}") or "-", s.net(f"U17.{num}") or "-"])
    s.table(38.1, 142.24, [22.86, 30.48, 25.4, 25.4], rows)
    s.note("Inputs: A0 -> C, A1 -> B, A2 -> D, A3 -> A on both chips, the wiring the firmware's decoderNibble()\n"
           "assumes. Firmware digit map BOARD_TYPE 4: digitMask[] = {%s} (digit d -> code)."
           % ", ".join(str(v) for v in TP.DIGIT_MASK4), 152.4, 142.24, 1.27)
    s.foot = 190
    s.notes_at = (152.4, 160.02, 105)


@layout("anodes", "drv", "A3")
def _anodes(s):
    for i, nm in enumerate(TP.TUBES):
        cx = 22.86 + (i % 3) * 127.0
        cy = 58.42 + (i // 3) * 58.42
        u, ro, ra, rb1, rb2 = f"U{5 + i}", f"R{21 + i}", f"R{27 + i}", f"R{33 + 2 * i}", f"R{34 + 2 * i}"
        if u not in s.bparts:
            continue
        s.note(f"{nm}", cx - 7.62, cy - 10.16, 2.0, bold=True)
        opt, emit, anode, bleed = "OPT_" + nm, "EMIT_" + nm, "ANODE_" + nm, "BLEED_" + nm
        s.h2(ro, cx, cy, TP.TUBE_PIN4[nm])
        s.tag(f"{ro}:{TP.TUBE_PIN4[nm]}")
        s.put(u, cx + 30.48, cy + 1.27)                 # 1 A (cx+21.59, cy), 2 K below; 4 C (cx+39.37, cy), 3 E below
        if s.link(f"{ro}:{opt}", f"{u}:{opt}"):
            s.name((cx + 12.7, cy), f"{u}:{opt}")
        s.tag(f"{u}.2")
        s.tag(f"{u}.4")
        s.v2(ra, cx + 46.99, cy + 6.35, emit)
        if s.link(f"{u}:{emit}", f"{ra}:{emit}", (cx + 46.99, cy + 2.54)):
            s.name((cx + 46.99, cy + 3.81), f"{ra}:{emit}", "right")
        s.route_tag(f"{ra}:{anode}", (cx + 46.99, cy + 16.51), (cx + 72.39, cy + 16.51), d="right")
        s.v2(rb1, cx + 59.69, cy + 19.05, anode)
        s.link((cx + 59.69, cy + 16.51), f"{rb1}:{anode}")
        s.v2(rb2, cx + 59.69, cy + 29.21, bleed)
        if s.link(f"{rb1}:{bleed}", f"{rb2}:{bleed}"):
            s.name((cx + 59.69, cy + 27.94), f"{rb2}:{bleed}", "right")
        s.tag(f"{rb2}:GND")
    s.foot = 160
    s.notes_at = (20.32, 170.18, 170)


@layout("colon", "drv", "A4")
def _colon(s):
    s.h2("R58", 55.88, 60.96, "HV185")
    s.h2("R59", 55.88, 71.12, "HV185")
    if s.link((45.72, 60.96), "R58:HV185"):
        s.end_label((45.72, 60.96), "R58:HV185", "left")
        s.link((50.8, 60.96), "R59:HV185", (50.8, 71.12))
    s.tag("R58:COLON_U")
    s.tag("R59:COLON_L")
    s.put("VT1", 73.66, 96.52)                          # B (68.58, 96.52), C (76.2, 91.44), E (76.2, 101.6)
    s.tag("VT1:COLON_RET", length=5.08)
    s.tag("VT1:GND")
    s.h2("R1", 50.8, 96.52, "D10")
    if s.link("R1:B1", "VT1:B1"):
        s.name((63.5, 96.52), "VT1:B1")
    s.tag("R1:D10")
    s.note("The lamps are on the display board: V7 upper, V8 lower (XS22 carries COLON_U, COLON_L and COLON_RET).",
           40.64, 112.0, 1.27)
    s.foot = 118
    s.notes_at = (20.32, 125, 115)


@layout("ampm", "drv", "A3")
def _ampm(s):
    if s.put("U3", 76.2, 106.68):                      # left pins x 63.5, right x 88.9
        S = SYMS["MCP23017"]
        for num in S.order:
            nm = S.pins[num][5]
            if nm in ("A0", "A1", "A2"):
                continue
            s.tag(f"U3.{num}", pw_d={"VDD": "left", "VSS": "left", "~{RESET}": "right"}.get(nm))
        if s.link("U3.17", "U3.16", (91.44, 118.11), (91.44, 120.65)) and s.link("U3.16", "U3.15", (91.44, 120.65), (91.44, 123.19)):
            s.wire((91.44, 123.19), (91.44, 125.73))
            s.pwr_at((91.44, 125.73), "U3.15")
        s.v2("C1", 76.2, 137.16, "+5V")
    K = SYMS["K155ID1"]
    for ref, y, cap in (("U16", 96.52, "C16"), ("U15", 132.08, "C15")):
        if not s.put(ref, 177.8, y):
            continue
        for num in K.order:
            s.tag(f"{ref}.{num}", pw_d={"VCC": "left", "GND": "right"}.get(K.pins[num][5]))
        s.v2(cap, 223.52, y - 6.35, "+5V")
    for ref, y in (("R56", 60.96), ("R57", 71.12)):
        s.h2(ref, 279.4, y, "HV185")
        for pr in [k for k in s.pins if k.startswith(ref + ".")]:
            s.tag(pr)
    rows = [["Output", "U15 (ИН-15Б) lights", "U16 (ИН-15А) lights"]]
    for c in range(10):
        num = next(n for n in K.order if K.pins[n][5] == f"Q{c}")
        rows.append([f"Q{c}", s.net(f"U15.{num}") or "- (blank)", s.net(f"U16.{num}") or "- (blank)"])
    s.table(254.0, 96.52, [17.78, 38.1, 38.1], rows)
    s.note("Codes 10-15 light nothing: the tube is blank. The firmware keeps the inverse of this table.", 254.0, 142.24, 1.27)
    s.foot = 160
    s.notes_at = (20.32, 165.1, 165)


@layout("rtc", "drv", "A4")
def _rtc(s):
    s.put("U13", 76.2, 76.2)                            # pins down the left at x 68.58
    s.tag("U13.1", pw_d="left")
    s.tag("U13.5", pw_d="left")
    s.foot = 92
    s.notes_at = (20.32, 100.33, 115)


@layout("backlight", "drv", "A3")
def _backlight(s):
    if s.put("RN1", 101.6, 101.6):
        for pr in [k for k in s.pins if k.startswith("RN1.")]:
            s.tag(pr)
    s.put("VT20", 177.8, 101.6)                         # B (172.72, 101.6), C (180.34, 96.52), E (180.34, 106.68)
    s.tag("VT20:BL_K", length=5.08)
    s.tag("VT20:GND")
    s.h2("R20", 152.4, 101.6, "D11")
    if s.link("R20:B20", "VT20:B20"):
        s.name((165.1, 101.6), "VT20:B20")
    s.tag("R20:D11")
    s.h2("R53", 152.4, 124.46, "D12")
    s.tag("R53:D12")
    s.tag("R53:M_A")
    s.note("On the display board: BL_A1..BL_A8 feed the anodes of HL1..HL8, M_A the anode of HL9 (the 'm'),\n"
           "and BL_K is all nine cathodes. GPBk of U3 lights HL(k+1): tools/ts06pair.py BL_OF_GPB.",
           40.64, 132.08, 1.27)
    s.foot = 142
    s.notes_at = (20.32, 150, 150)


@layout("fascia", "drv", "A4")
def _fascia(s):
    if not s.put("J1", 127.0, 76.2):                    # pins 1..6 down the left, x 121.92, y 69.85 .. 82.55
        return
    s.tag("J1:+5V")
    s.tag("J1:GND", pw_d="left")
    if s.link("J1:A6", (86.36, 74.93)):
        s.end_label((86.36, 74.93), "J1:A6", "left")
        s.shunt("C5", 91.44, 74.93, "A6")
    if s.link("J1:A7", (101.6, 77.47)):
        s.end_label((101.6, 77.47), "J1:A7", "left")
        s.shunt("C6", 106.68, 77.47, "A7")
    s.tag("J1:D7", length=5.08)
    s.tag("J1:D8", length=5.08)
    s.note("To the fascia: JST PH, 6 ways, top entry.", 116.84, 88.9, 1.27)
    s.foot = 100
    s.notes_at = (20.32, 105, 115)


def strip_table(s, ref, x, y):
    """One board-to-board strip: its symbol, a label on every pin, and a pin table level with the pins."""
    p = s.bparts[ref]
    n = len(p.pins)
    top = (n - 1) / 2 * G
    if not s.put(ref, x, y + top, fields=((-2.54, -top - 3.81, "right"), (-2.54, top + 3.81, "right"))):
        return y
    for k in range(1, n + 1):
        s.tag(f"{ref}.{k}")
    mate = ("XS" if ref.startswith("XP") else "XP") + ref[2:]
    s.note(f"{ref}  ({p.value}, mates {mate})", x - 17.78, y - 6.35, 1.524, bold=True)
    rows = [["Pin", "Net", "On the display board", "On the driver board"]]
    for k in range(1, n + 1):
        net = p.pins[str(k)]
        rows.append([str(k), net or "-", goes_to(TP.DISP, net, {"XP" + ref[2:]}) if net else "",
                     goes_to(TP.DRV, net, {"XS" + ref[2:]}) if net else ""])
    s.tables.append(dict(x=snap(x + 3.81), y=snap(y - G - 1.27), colw=[7.62, 24.13, 50.8, 40.64], rows=rows,
                         sz=1.1, rh=G))
    return y + n * G + 12.7


@layout("stack", "drv", "A3")
def _stack_drv(s):
    stack_sheet(s, "XS")


@layout("stack", "disp", "A3")
def _stack_disp(s):
    stack_sheet(s, "XP")


def stack_sheet(s, pre):
    y = strip_table(s, pre + "12", 40.64, 55.88)
    y2 = 55.88
    for k in ("11", "21", "22", "23", "24", "25"):
        y2 = strip_table(s, pre + k, 205.74, y2)
    s.note("Pin n of XPk (display board, male, on its back) mates pin n of XSk (driver board, female, on its face).\n"
           "The order of every strip is the order the display board's copper arrives in (tools/ts06pair.py HEADERS).",
           50.8, 38.1, 1.27)
    hy = max(y, y2) + 5.08
    s.note("Standoff holes (M3): mechanical, no pad", 50.8, hy, 1.27, bold=True)
    for i, h in enumerate(s.holes):
        h["x"], h["y"] = snap(55.88 + i * 17.78), snap(hy + 7.62)
    s.foot = hy + 12.7
    s.notes_at = (50.8, hy + 17.78, 150)


@layout("tubes", "disp", "A3")
def _tubes(s):
    """The ИН-12 cathode bus and the ИН-17 bus, drawn as buses: each tube's cathode drops onto its line."""
    groups = [(["V1", "V2", "V3", "V4"], 50.8, 33.02), (["V5", "V6"], 241.3, 223.52)]
    for refs, x0, xl in groups:
        refs = [r for r in refs if r in s.bparts]
        if not refs:
            continue
        ybus = {}
        xs = {}
        for i, r in enumerate(refs):
            x = x0 + i * 40.64
            s.put(r, x, 76.2)
            nm = s.bparts[r].note.split(";")[0]
            s.note(nm, x + 16.51 if s.parts[r]["sym"] == "IN-12A" else x + 15.24, 68.58, 2.0, bold=True)
            s.tag(f"{r}.{SYMS[s.parts[r]['sym']].order[0]}", length=5.08)          # the anode
            S = SYMS[s.parts[r]["sym"]]
            for num in S.order[1:]:
                pname = S.pins[num][5]
                if not pname.isdigit():
                    continue
                d = int(pname)
                net = s.net(f"{r}.{num}")
                bus = ybus.setdefault(d, (snap(90.17 + d * G), net))
                if net and net == bus[1]:
                    s.link(f"{r}.{num}", (s.X(f"{r}.{num}"), bus[0]))
                    xs.setdefault(d, []).append(s.X(f"{r}.{num}"))
        for d, (yb, net) in sorted(ybus.items()):
            if d in xs:
                s.wire((xl, yb), (max(xs[d]), yb))
                s.glabel(xl, yb, net, "left")
    s.foot = 122
    s.notes_at = (20.32, 130, 170)


@layout("colon", "disp", "A4")
def _colon_disp(s):
    s.put("V7", 76.2, 76.2)
    s.put("V8", 101.6, 76.2)
    s.tag("V7.1")
    s.tag("V8.1")
    if s.link("V7.2", "V8.2", (76.2, 86.36), (101.6, 86.36)) and s.link((101.6, 86.36), (111.76, 86.36)):
        s.end_label((111.76, 86.36), "V8.2", "right")
    s.note("V7 upper, V8 lower. Each has its own 220k ballast on the driver board; the MPSA42 there switches COLON_RET.",
           40.64, 96.52, 1.27)
    s.foot = 104
    s.notes_at = (20.32, 110, 115)


@layout("ampm", "disp", "A3")
def _ampm_disp(s):
    for r, x in (("V9", 101.6), ("V10", 203.2)):
        if not s.put(r, x, 88.9):
            continue
        S = SYMS[s.parts[r]["sym"]]
        s.tag(f"{r}.{S.order[0]}", length=5.08)
        for num in S.order[1:]:
            s.tag(f"{r}.{num}", length=5.08)
        s.note(f"{r}: {s.bparts[r].value}", x - 43.18, 86.36, 2.0, bold=True)
    s.foot = 128
    s.notes_at = (20.32, 135, 150)


@layout("backlight", "disp", "A3")
def _backlight_disp(s):
    refs = [f"HL{i}" for i in range(1, 10) if f"HL{i}" in s.bparts]
    xs = []
    for i, r in enumerate(refs):
        x = 50.8 + i * 22.86
        s.v2(r, x, 71.12, "BL_K")
        if s.link(f"{r}:BL_K", (x, 66.04)):
            xs.append(x)
        s.tag(f"{r}.2", length=5.08)
        s.tag(f"{r}.1")
    if xs:
        s.wire((38.1, 66.04), (max(xs), 66.04))
        s.end_label((38.1, 66.04), f"{refs[0]}:BL_K", "left")
    s.foot = 96
    s.notes_at = (20.32, 104.14, 150)


def goes_to(const, net, skip):
    """The far ends of a net on one board, for the pin tables: 'V1-V4 cathode 6', 'U2 Q3', 'R27, R33'."""
    if not net:
        return ""
    by = {}
    for p in TP.PARTS:
        if p.board != const or p.ref in skip:
            continue
        sym = symbol_for(p)
        S = SYMS.get(sym)
        for pin, n in p.pins.items():
            if n != net:
                continue
            pn = (S.pins[pin][5] if S and pin in S.pins else pin).replace("~{RESET}", "RESET")
            if sym.startswith("IN-") and sym != "INS-1":
                pn = "anode" if pn == "A" else f"cathode {pn}"
            elif sym.startswith("Conn_") or sym.startswith("RN_"):
                pn = f"pin {pin}"
            elif sym in TWO_PIN or pn in ("~", ""):
                pn = ""
            by.setdefault(pn, []).append(p.ref)
    return ", ".join((ref_ranges(v) + (" " + k if k else "")) for k, v in by.items())


def draw(board, sec, refs, page, holes=(), labels_only=False):
    fn, paper = LAYOUTS.get((sec["id"], board), (None, "A3"))
    if labels_only or not fn:
        paper = "A3" if len(refs) < 40 else "A2"
    s = Sheet(board, sec, page, paper)
    s.labels_only = labels_only
    s.refs = refs
    y = s.note(f'{BOARDS[board][0]}  ·  {sec["title"]}', 20.32, 12.7, 3.0, bold=True)
    s.note(sec.get("summary", ""), 20.32, y + 1.27, 1.524, width=150 if paper != "A4" else 110)
    s.foot = 60.0
    s.notes_at = None
    for h in holes:
        s.holes.append(h)
    if fn and not labels_only:
        fn(s)
        head = s.texts[1]
        head_bottom = head["y"] + (head["t"].count("\n") + 1) * head["sz"] * 1.7
        t = s.top()
        if t is not None:
            dy = math.floor((head_bottom + 7.62 - t) / G) * G
            if dy < 0:
                s.shift(dy)
    rest = [r for r in refs if r not in s.parts]
    if rest:
        y0 = s.foot + 6
        s.note("Drawn as a labelled netlist: this sheet's hand layout no longer matches tools/ts06pair.py."
               if labels_only and fn else
               "Parts this sheet's layout does not know yet (added to tools/ts06pair.py since): labelled, not wired.",
               20.32, y0, 1.27, bold=True)
        s.foot = s.auto_place(rest, 20.32, y0 + 5.08, s.W - 25)
    s.tag_rest()
    nts = notes_for(board, refs)
    if nts:
        nx, ny, nw = s.notes_at or (20.32, s.foot + 6, 150)
        ny = snap(s.bottom() + 7.62)
        y = s.note("Notes from tools/ts06pair.py", nx, ny, 1.524, bold=True)
        s.note("\n".join(f"{r}: {n}" for r, n in nts), nx, y, 1.27, width=nw)
    s.normalise()
    bad, bynet = s.trace()
    if fn and not labels_only and not bad and (s.skipped or rest):
        print(f"  note {BOARDS[board][0]} / {sec['title']}: layout partly stale - {len(s.skipped)} wire(s) not drawn "
              f"(the nets differ now), labelled instead; parts added below the drawing: {' '.join(rest) or 'none'}")
    if bad and not labels_only:
        print(f"  WARNING {BOARDS[board][0]} / {sec['title']}: the hand layout no longer matches ts06pair.py "
              f"({len(bad)} problems, first: {bad[0]}); drawn as a labelled netlist instead - update its layout.")
        return draw(board, sec, refs, page, holes, labels_only=True)
    if bad:
        raise SystemExit(f"{BOARDS[board][0]} / {sec['title']}: " + "; ".join(bad[:10]))
    s.bynet = bynet
    return s


def sheet_file(board, s):
    proj = BOARDS[board][0]
    slug = re.sub(r"[^a-z0-9]+", "-", s.sec["id"].lower()).strip("-")
    return f"{proj}-{s.page - 1:02d}-{slug}.kicad_sch"


def header(proj, file_uuid, paper, title, c2):
    return (f'(kicad_sch\n(version {SV})\n(generator "eeschema")\n(generator_version "{GV}")\n'
            f'(uuid "{file_uuid}")\n(paper "{paper}")\n'
            f'(title_block\n(title "{esc(title)}")\n(date "{DATE}")\n(rev "A")\n(company "TERMINAL-06")\n'
            f'(comment 1 "Generated by tools/mksch_pair.py from tools/ts06pair.py - edit those, not this")\n'
            f'(comment 2 "{esc(c2)}")\n)\n')


DATE = "2026-09-30"


def build(board):
    proj, const = BOARDS[board]
    fpinfo = board_footprints(board)
    known = {p.ref for p in TP.PARTS if p.board == const}
    holes = sorted((r for r, v in fpinfo.items() if r not in known and not any(v["pads"].values())), key=refkey)
    stray = sorted(r for r, v in fpinfo.items() if r not in known and any(v["pads"].values()))
    if stray:
        print(f"  WARNING {proj}: footprints with nets that ts06pair.py does not have: {stray}")
    secs = sections_for(board)
    sheets = []
    for page, (sec, refs) in enumerate(secs, start=2):
        hl = []
        if sec["id"] == "stack":
            for i, r in enumerate(holes):
                hl.append(dict(ref=r, x=0, y=0, i=i))
        s = draw(board, sec, refs, page, hl)
        for h in s.holes:
            if not h["x"]:
                h["x"], h["y"] = snap(s.W - 150 + (h["i"] % 4) * 20.32), snap(35.56 + (h["i"] // 4) * 7.62)
        sheets.append(s)
    # the whole board, traced across its sheets, against ts06pair.py
    got = {}
    for s in sheets:
        for n, prs in s.bynet.items():
            got.setdefault(n, set()).update(prs)
    want = {n: set(v) for n, v in TP.nets(const).items()}
    diff = [n for n in sorted(set(got) | set(want)) if got.get(n) != want.get(n)]
    if diff:
        raise SystemExit(f"{proj}: drawn nets differ from ts06pair.py: " + ", ".join(diff[:10]))
    root_uuid = uid(board, "root")
    d = os.path.join(ROOT, "PCB", proj)
    counter = {"pwr": 0, "flg": 0}
    boxes = []
    for s in sheets:
        suuid = uid(board, "sheet", s.sec["id"])
        body = sheet_body(s, f"/{root_uuid}/{suuid}", fpinfo, counter)
        libs = "\n".join(SYMS[n].text(True) for n in used_syms(s))
        txt = (header(proj, uid(board, "file", s.sec["id"]), s.paper, f'{proj} - {s.sec["title"]}',
                      f'Section {s.page - 1} of {len(sheets)}; parts: ' + " ".join(sorted(s.refs, key=refkey)))
               + f"(lib_symbols\n{libs}\n)\n" + "\n".join(body) + "\n)\n")
        with open(os.path.join(d, sheet_file(board, s)), "w", encoding="utf8", newline="\n") as fh:
            fh.write(txt)
        boxes.append((s, suuid))
    write_root(board, boxes, root_uuid)
    keep = {sheet_file(board, s) for s in sheets}       # a section that moved or went away leaves no file behind
    for fn in sorted(os.listdir(d)):
        if re.match(re.escape(proj) + r"-\d\d-[a-z0-9-]+\.kicad_sch$", fn) and fn not in keep:
            os.remove(os.path.join(d, fn))
            print(f"  removed PCB/{proj}/{fn}: no section draws it now")
    with open(os.path.join(d, "sym-lib-table"), "w", encoding="utf8", newline="\n") as fh:
        fh.write('(sym_lib_table\n  (version 7)\n  (lib (name "TS06_pair")(type "KiCad")(uri "${KIPRJMOD}/../lib/TS06_pair.kicad_sym")'
                 '(options "")(descr "TERMINAL-06 THT pair symbols, written by tools/mksch_pair.py"))\n)\n')
    nparts = sum(len(s.parts) for s in sheets)
    print(f"wrote PCB/{proj}/{proj}.kicad_sch + {len(sheets)} sheets ({nparts} parts, {len(holes)} holes, "
          f"{len(got)} nets, {counter['pwr']} power symbols, {counter['flg']} PWR_FLAG)")
    return sheets


def write_root(board, boxes, root_uuid):
    proj = BOARDS[board][0]
    items = []
    y = 20.32
    items.append(f'(text "{esc(proj + " - the through-hole pair, " + ("driver board" if board == "drv" else "display board"))}"\n'
                 f'(exclude_from_sim no)\n(at 20.32 {f(y)} 0)\n(effects\n(font\n(size 3 3)\n(bold yes)\n)\n(justify left top)\n)\n'
                 f'(uuid "{uid(board, "root", "title")}")\n)')
    intro = ROOT_INTRO[board]
    items.append(f'(text "{esc(intro)}"\n(exclude_from_sim no)\n(at 20.32 30.48 0)\n(effects\n(font\n(size 1.524 1.524)\n)\n'
                 f'(justify left top)\n)\n(uuid "{uid(board, "root", "intro")}")\n)')
    cols, bw, bh, gx, gy = 3, 88.9, 25.4, 127.0, 38.1
    y0 = 30.48 + (intro.count("\n") + 1) * 2.6 + 12.7
    for i, (s, suuid) in enumerate(boxes):
        x = snap(20.32 + (i % cols) * gx)
        yy = snap(y0 + (i // cols) * gy)
        nm = f"{s.page - 1:02d} {s.sec['title']}"
        items.append(
            f'(sheet\n(at {f(x)} {f(yy)})\n(size {f(bw)} {f(bh)})\n(exclude_from_sim no)\n(in_bom yes)\n(on_board yes)\n'
            f'(dnp no)\n(fields_autoplaced yes)\n(stroke\n(width 0.1524)\n(type solid)\n)\n(fill\n(color 0 0 0 0.0000)\n)\n'
            f'(uuid "{suuid}")\n'
            f'(property "Sheetname" "{esc(nm)}"\n(at {f(x)} {f(yy - 0.7116)} 0)\n(effects\n(font\n(size 1.524 1.524)\n)\n(justify left bottom)\n)\n)\n'
            f'(property "Sheetfile" "{sheet_file(board, s)}"\n(at {f(x)} {f(yy + bh + 0.5846)} 0)\n(effects\n(font\n(size 1.27 1.27)\n)\n'
            f'(justify left top)\n)\n)\n'
            f'(instances\n(project "{proj}"\n(path "/{root_uuid}"\n(page "{s.page}")\n)\n)\n)\n)')
        first = re.split(r"(?<=\.) ", s.sec.get("summary", ""))[0]
        short = textwrap.fill(" ".join(sorted(s.refs, key=refkey)), 66) + "\n\n" + textwrap.fill(first, 66)
        items.append(f'(text "{esc(short)}"\n(exclude_from_sim no)\n(at {f(x + 1.27)} {f(yy + 1.27)} 0)\n(effects\n(font\n(size 1.27 1.27)\n)\n'
                     f'(justify left top)\n)\n(uuid "{uid(board, "root", "refs", s.sec["id"])}")\n)')
    txt = (header(proj, root_uuid, "A3", f"{proj} - the through-hole pair",
                  "Netlist: tools/ts06pair.py. Boards: tools/mkpcb_disp.py, tools/mkpcb_drv.py")
           + "(lib_symbols\n)\n" + "\n".join(items)
           + '\n(sheet_instances\n(path "/"\n(page "1")\n)\n)\n(embedded_fonts no)\n)\n')
    with open(os.path.join(ROOT, "PCB", proj, proj + ".kicad_sch"), "w", encoding="utf8", newline="\n") as fh:
        fh.write(txt)


ROOT_INTRO = {
    "drv": "Everything but the tubes: power, the 185 V converter, the Nano, the decoders, the anode switches, the AM/PM\n"
           "expander, the RTC and the backlight. Its seven socket strips (XS) take the display board's pin strips.\n"
           "Every net is named as on the board: HV185 is the 185 V anode rail; GND, +5V and +12V are power symbols.",
    "disp": "The display board: four ИН-12А, two ИН-17, two ИН-15, two ИНС-1 and nine LEDs - and nothing else.\n"
            "Every line reaches it from the driver board through the pin strips XP11, XP12 and XP21-XP25.\n"
            "Every net is named as on the board.",
}


def write_lib():
    with open(LIBFILE, "w", encoding="utf8", newline="\n") as fh:
        fh.write(f'(kicad_symbol_lib\n(version {LV})\n(generator "kicad_symbol_editor")\n(generator_version "{GV}")\n'
                 + "\n".join(SYMS[n].text() for n in sorted(SYMS)) + "\n)\n")
    print("wrote", os.path.relpath(LIBFILE, ROOT), f"({len(SYMS)} symbols)")


def sheet_svgs(board):
    """[(the SVG name kicad-cli gives a sheet, the name the viewer gets, section id or None)]."""
    proj = BOARDS[board][0]
    out = [(f"{proj}.svg", f"sch-{board}-00-index.svg", None)]
    for page, (sec, refs) in enumerate(sections_for(board), start=2):
        nm = f"{page - 1:02d} {sec['title']}".replace("/", "_")
        out.append((f"{proj}-{nm}.svg", f"sch-{board}-{page - 1:02d}-{sec['id']}.svg", sec["id"]))
    return out


def _num(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    s = "0" if s in ("-0", "") else s
    return s.replace("0.", ".", 1) if s.startswith("0.") else s.replace("-0.", "-.", 1)


_PURE = re.compile(r"(\s*[ML]\s*-?[\d.]+[ ,]\s*-?[\d.]+)+\s*")


def _rel(d):
    """'M x y L x y M x y L ...' as absolute moves and relative lines, in whole 0.01 mm steps, so the
    rounding never accumulates."""
    if not _PURE.fullmatch(d):
        return d
    toks = re.findall(r"[ML]|-?[\d.]+", d)
    out, cx, cy, i = [], 0, 0, 0
    while i < len(toks):
        c = toks[i]
        x, y = round(float(toks[i + 1]) * 100), round(float(toks[i + 2]) * 100)
        if c == "M":
            out.append(f"M{_num(x / 100)} {_num(y / 100)}")
        else:
            dx, dy = _num((x - cx) / 100), _num((y - cy) / 100)
            out.append(f"l{dx}{'' if dy.startswith('-') else ' '}{dy}")
        cx, cy = x, y
        i += 3
    return "".join(out)


def tidy_svg(src, dst, margin=6.0):
    """A kicad-cli SVG made fit for a web page: cropped to what is drawn, on a white ground, every
    run of stroked segments in one path, coordinates to 0.01 mm. The drawing is unchanged."""
    s = open(src, encoding="utf8").read()
    s = re.sub(r"<desc>[^<]*</desc>", "", s)

    def short(m):                               # coordinates only: 12.7000 -> 12.7, 0.4572 -> 0.46
        return re.sub(r"-?\d+\.\d+", lambda n: f"{float(n.group(0)):.2f}".rstrip("0").rstrip("."), m.group(0))
    s = re.sub(r'\b(?:d|cx|cy|r|x|y|width|height|textLength|font-size)="[^"]*"', short, s)
    # what is drawn: segment ends, circles, rects (not the page), invisible text anchors
    xs, ys = [], []
    for d in re.findall(r' d="([^"]*)"', s):
        for a, b in re.findall(r"[ML]\s*(-?[\d.]+)[ ,](-?[\d.]+)", d):
            xs.append(float(a))
            ys.append(float(b))
    for cx, cy, r in re.findall(r'<circle cx="([-\d.]+)" cy="([-\d.]+)" r="([-\d.]+)"', s):
        xs += [float(cx) - float(r), float(cx) + float(r)]
        ys += [float(cy) - float(r), float(cy) + float(r)]
    for x, y, w, h in re.findall(r'<rect x="([-\d.]+)" y="([-\d.]+)" width="([-\d.]+)" height="([-\d.]+)"', s):
        if float(x) == 0 and float(y) == 0:
            continue
        xs += [float(x), float(x) + float(w)]
        ys += [float(y), float(y) + float(h)]
    # merge consecutive paths inside unfilled groups
    out, stack, run = [], [False], []
    for m in re.finditer(r'<path d="([^"]*)"\s*/>\s*|<g\b[^>]*>|</g>|<[^>]+>|[^<]+', s):
        t = m.group(0)
        if m.group(1) is not None and stack[-1] and _PURE.fullmatch(m.group(1)):
            run.append(" ".join(m.group(1).split()))
            continue
        if run:
            out.append(f'<path d="{_rel(" ".join(run))}"/>\n')
            run = []
        if t.startswith("<g"):
            st = re.search(r'style="([^"]*)"', t)
            stack.append(("fill:none" in st.group(1)) if st else stack[-1])
        elif t.startswith("</g"):
            stack.pop()
        out.append(t)
    s = "".join(out)
    x0, y0 = min(xs) - margin, min(ys) - margin
    w, h = max(xs) - min(xs) + 2 * margin, max(ys) - min(ys) + 2 * margin
    s = re.sub(r'width="[\d.]+mm" height="[\d.]+mm" viewBox="[^"]*"',
               f'width="{w:.1f}mm" height="{h:.1f}mm" viewBox="{x0:.2f} {y0:.2f} {w:.2f} {h:.2f}"', s, 1)
    s = re.sub(r"(<desc>[^<]*</desc>|</title>)", r'\1\n<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="#FFFFFF"/>'
               % (x0, y0, w, h), s, 1)
    with open(dst, "w", encoding="utf8") as fh:
        fh.write(s)
    return os.path.getsize(src), os.path.getsize(dst)


def main():
    if "--compare" in sys.argv:
        i = sys.argv.index("--compare")
        sys.exit(compare(sys.argv[i + 1], sys.argv[i + 2]))
    if "--svg-out" in sys.argv:
        i = sys.argv.index("--svg-out")
        raw, dst = sys.argv[i + 1], sys.argv[i + 2]
        for b in ("drv", "disp"):
            for kname, vname, sid in sheet_svgs(b):
                a, z = tidy_svg(os.path.join(raw, kname), os.path.join(dst, vname))
                print(f"  {vname:34s} {a // 1024:5d} kB -> {z // 1024:4d} kB")
        return
    for p in TP.PARTS:                  # every strip width in use, before the library is written
        symbol_for(p)
    for b in ("drv", "disp"):
        build(b)
    write_lib()


def compare(netfile, pcbfile):
    """A netlist KiCad exported from these schematics against a board: every pad's net, every
    footprint and value. What 'Update PCB from schematic' would change, checked from outside."""
    t = sexp.parse(open(netfile, encoding="utf8").read())
    comps = {}
    for c in sexp.find_all(sexp.find(t, "components"), "comp"):
        comps[sexp.unq(sexp.find(c, "ref")[1])] = (sexp.unq(sexp.find(c, "value")[1]),
                                                   sexp.unq((sexp.find(c, "footprint") or ["", '""'])[1]))
    sch = {}
    for n in sexp.find_all(sexp.find(t, "nets"), "net"):
        nm = sexp.unq(sexp.find(n, "name")[1])
        for nd in sexp.find_all(n, "node"):
            sch[(sexp.unq(sexp.find(nd, "ref")[1]), sexp.unq(sexp.find(nd, "pin")[1]))] = nm
    board = os.path.splitext(os.path.basename(pcbfile))[0]
    key = [k for k, v in BOARDS.items() if v[0] == board][0]
    fps = board_footprints(key)
    bad = []
    for ref, v in sorted(fps.items(), key=lambda kv: refkey(kv[0])):
        if ref not in comps:
            bad.append(f"{ref}: on the board, not in the schematic")
            continue
        val, fp = comps[ref]
        if fp != v["lib"]:
            bad.append(f"{ref}: footprint {fp} in the schematic, {v['lib']} on the board")
        if val != v["value"]:
            bad.append(f"{ref}: value {val!r} in the schematic, {v['value']!r} on the board")
        for pad, net in v["pads"].items():
            s = sch.get((ref, pad))
            if (net or None) != (s if s and not s.startswith("unconnected-") else None):
                bad.append(f"{ref}.{pad}: net {s} in the schematic, {net} on the board")
    for ref in sorted(set(comps) - set(fps), key=refkey):
        bad.append(f"{ref}: in the schematic, not on the board")
    nets_s = {v for v in sch.values() if not v.startswith("unconnected-")}
    print(f"{len(comps)} symbols and {len(nets_s)} nets in the netlist; {len(fps)} footprints on {board}")
    for b in bad:
        print("  " + b)
    print(f"\n{len(bad)} difference(s)" if bad else "\nno differences: 'Update PCB from schematic' has nothing to change")
    return 1 if bad else 0


if __name__ == "__main__":
    main()
