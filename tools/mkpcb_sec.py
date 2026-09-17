#!/usr/bin/env python3
"""Generate TS06-SEC, the seconds / AM-PM module - surface-mount build.

Every part is placed before any copper exists, so no section's routing can occupy space
another section turns out to need; the board is then routed in two stages (ROUTING below).

WHAT IT CARRIES: 2x IN-17 (seconds) and their two TLP627 anode drivers; 2x IN-15
(V9 = IN-15B for AM, V10 = IN-15A for PM) switched per cathode by two MCP23017s and
eighteen MMBTA42s; the colon's switch (the colon board itself is done and arrives on XS4);
two amber backlight LEDs for the IN-17s and the "m" LED HL3.

WHERE THE TUBES ARE is not a layout choice. Their centres come from the reviewed 8-tube
FreeCAD assembly (3d/Clock.FCStd): IN-17s at world X 104.605 / 117.605 (13.0 mm pitch),
IN-15s at X 135 / 156 (21.0 mm pitch), IN-17 centres 5.375 mm below the IN-15 centres, and
the IN-15 centres at the real IN-12 height - 20.066 mm above the Gyver tube board's bottom
edge (world Y 40.10), from the Gyver drill file. Board local (x, y) = (world X - 99.6,
83.0 - world Y): the left edge sits 0.54 mm right of the Gyver tube board (which ends at
X 99.06).

WHY THE BOARD IS 67.0 x 55.0 mm AND NOT THE SPEC'S 46 x 34: tube glass covers nearly the
whole front - the IN-15s sit flush on it, so no joint may land under them - and the four
tubes span 66 mm. Everything else therefore mounts on the BACK, and every through-hole
joint (connectors, LEDs) lands on the front only where the fascia hides it. Upward, the
board runs to world Y 83.0 (2.2 mm past the Gyver driver board's top) so both SOIC-28
expanders fit above the tubes; downward to world Y 28.0 so the connectors sit behind the
fascia, which clears the fascia's original control row. The compressed 40 mm fascia moves
its buttons and levers into that space; per the owner (15.09.26) SEC takes priority and
the fascia is redesigned around it. The last 0.6 mm of width is the strip right of V10
that holds three of its cathode transistors.

CHANNEL PLACEMENT: each cathode transistor sits next to its own tube pad - inside the pin
ring, between the rings, or in the strip beside V10 - turned (pre-rotated variant) so its
collector faces that pad. Collector runs are the high-voltage copper, so they are the ones
kept short; base resistors sit where the 5 V side has room.

IN-15 PIN MAP (datasheet pin d sits on footprint pad ((7 - d) mod 12) + 1, see
TS06_IN12_Socket; pinouts from tec.org.ru and rudatasheet.ru, which agree):
  V9  IN-15B: pad 1 V, 2 H, 3 Hz, 4 NC, 5 F, 6 W, 7 anode, 8 NC, 9 A, 10 Ohm, 11 NC, 12 S
  V10 IN-15A: pad 1 M, 2 m, 3 +, 4 -, 5 P, 6 mu, 7 anode, 8 NC, 9 n, 10 %, 11 Pi, 12 K
Eighteen channels, one per real cathode. The four NC pads get no transistor.

ROUTING (tools/pcbroute.py), two stages; --route N emits stages 1..N:
  1. The high-voltage locals - cathode collectors, anode chains, colon return - laid first
     and never moved: they are short, and their 0.6 mm halos set the ground everything
     else has to find its way through.
  2. Everything else, negotiated at once in the manner of PathFinder: the IN-17 bus (each
     net grown from its XS2 pin), the 185 V feed, the 5 V signals, +5V, and GND as a track
     tree grown from XS3. Laid one after another the nets fenced each other in - the bus,
     fixed first, boxed in the backlight LEDs - and a GND carried by pours alone was left
     with pads in pockets that signals had closed on both faces. GND is still POURED on both
     faces, over whatever the tracks leave, joined through the tree's vias and pins.
A full run takes about five minutes.

Regenerate with:  python3 tools/mkpcb_sec.py
"""
import os, re, uuid

VER, GEN, GENV = 20260206, "pcbnew", "10.0"
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PRETTY = os.path.join(ROOT, "PCB", "lib", "TS06.pretty")
OUT = os.path.join(ROOT, "PCB", "TS06-SEC", "TS06-SEC.kicad_pcb")
NS = uuid.UUID("5ec06000-7506-4000-8000-00000000b0a2")

W, H = 67.0, 55.0
WX0, WY0 = 99.6, 83.0                      # world coordinates of the board's top-left corner


def local(wx, wy):
    return round(wx - WX0, 4), round(WY0 - wy, 4)


IN15_WY = 40.10 + 20.066                   # the Gyver board's real tube height
V5_XY = local(104.605, IN15_WY - 5.375)
V6_XY = local(117.605, IN15_WY - 5.375)
V9_XY = local(135.0, IN15_WY)
V10_XY = local(156.0, IN15_WY)

K = [f"K{d}" for d in range(10)]           # the multiplexed cathode bus, one net per IN-17 digit
# XS2 carries the bus in the order the tubes can reach it without crossing. Both IN-17s
# sit above XS2 with the same pin order round their rings; cut each ring at the top and
# lay its cathodes out left to right as they fall below it, and both give 2 3 4 5 6 7 8 9
# 0 1. Pins 1..10 follow that order, so each tube fans out to XS2 on its own layer.
XS2_ORDER = [2, 3, 4, 5, 6, 7, 8, 9, 0, 1]
SOT, R805 = "TS06_SOT-23_Std_Back", "TS06_R_0805_Back_R90"

# channel: transistor, resistor, tube, pad, cathode net, GPIO pin, GPIO net,
#          transistor footprint + (x, y), resistor (x, y)
CH = [
    ("VT2", "R2", "V9", "1", "CAT_B_VOLT", "21", "U3_GPA0", SOT + "_R90", (31.4, 10.4), (31.4, 6.0)),
    ("VT3", "R3", "V9", "2", "CAT_B_HENRY", "22", "U3_GPA1", SOT + "_R90", (35.4, 10.4), (35.4, 6.0)),
    ("VT4", "R4", "V9", "3", "CAT_B_HERTZ", "23", "U3_GPA2", SOT + "_R90", (39.4, 10.4), (39.4, 6.0)),
    ("VT5", "R5", "V9", "5", "CAT_B_FARAD", "24", "U3_GPA3", SOT + "_R180", (37.6, 18.3), (21.5, 2.8)),
    ("VT6", "R6", "V9", "6", "CAT_B_WATT", "25", "U3_GPA4", SOT + "_R180", (37.6, 27.4), (23.7, 2.8)),
    ("VT7", "R7", "V9", "9", "CAT_B_AMP", "26", "U3_GPA5", SOT + "_R270", (31.4, 34.2), (25.9, 2.8)),
    ("VT8", "R8", "V9", "10", "CAT_B_OHM", "27", "U3_GPA6", SOT, (33.2, 27.4), (21.5, 7.0)),
    ("VT9", "R9", "V9", "12", "CAT_B_SIEMENS", "28", "U3_GPA7", SOT, (33.2, 18.3), (23.7, 7.0)),
    ("VT10", "R10", "V10", "1", "CAT_A_MEGA", "21", "U4_GPA0", SOT + "_R270", (54.3, 18.1), (44.0, 15.0)),
    ("VT11", "R11", "V10", "2", "CAT_A_MILLI", "22", "U4_GPA1", SOT + "_R270", (58.5, 18.1), (63.3, 3.0)),
    ("VT12", "R12", "V10", "3", "CAT_A_PLUS", "23", "U4_GPA2", SOT + "_R90", (65.0, 14.6), (65.3, 10.8)),
    ("VT13", "R13", "V10", "4", "CAT_A_MINUS", "24", "U4_GPA3", SOT + "_R90", (65.0, 18.7), (63.3, 10.8)),
    ("VT14", "R14", "V10", "5", "CAT_A_P", "25", "U4_GPA4", SOT + "_R90", (65.0, 22.8), (65.3, 7.0)),
    ("VT15", "R15", "V10", "6", "CAT_A_MICRO", "26", "U4_GPA5", SOT + "_R180", (58.5, 27.4), (63.3, 7.0)),
    ("VT16", "R16", "V10", "9", "CAT_A_NANO", "27", "U4_GPA6", SOT + "_R90", (54.3, 27.6), (44.0, 31.4)),
    ("VT17", "R17", "V10", "10", "CAT_A_PCT", "28", "U4_GPA7", SOT + "_R180", (47.5, 27.3), (44.0, 27.3)),
    ("VT18", "R18", "V10", "11", "CAT_A_PI", "1", "U4_GPB0", SOT + "_R180", (47.5, 22.8), (44.0, 23.2)),
    ("VT19", "R19", "V10", "12", "CAT_A_KILO", "2", "U4_GPB1", SOT + "_R180", (47.5, 18.3), (44.0, 19.1)),
]

P = []


def part(ref, fp, val, xy, back, nets):
    P.append((ref, fp, val, xy[0], xy[1], back, nets))


part("V5", "TS06_IN17_Socket", "IN-17", V5_XY, False, {"A": "ANODE_S10", **{str(d): K[d] for d in range(10)}})
part("V6", "TS06_IN17_Socket", "IN-17", V6_XY, False, {"A": "ANODE_S1", **{str(d): K[d] for d in range(10)}})
part("V9", "TS06_IN12_Socket", "IN-15B", V9_XY, False, {"7": "ANODE_AM", **{c[3]: c[4] for c in CH if c[2] == "V9"}})
part("V10", "TS06_IN12_Socket", "IN-15A", V10_XY, False, {"7": "ANODE_PM", **{c[3]: c[4] for c in CH if c[2] == "V10"}})

MCP = {"9": "+5V", "10": "GND", "12": "SCL", "13": "SDA", "16": "GND", "17": "GND", "18": "+5V"}
part("U3", "TS06_SOIC-28W_Back_R270", "MCP23017-E/SO", (10.0, 6.45), True,
     {**MCP, "15": "GND", **{c[5]: c[6] for c in CH if c[2] == "V9"}})
part("U4", "TS06_SOIC-28W_Back_R90", "MCP23017-E/SO", (51.0, 6.5), True,
     {**MCP, "15": "+5V", **{c[5]: c[6] for c in CH if c[2] == "V10"}})
part("C1", "TS06_C_0805_Back", "100n", (7.46, 13.4), True, {"1": "+5V", "2": "GND"})
part("C2", "TS06_C_0805_Back_R90", "100n", (61.2, 3.0), True, {"1": "+5V", "2": "GND"})
part("C3", "TS06_C_1206_Back", "10u", (44.0, 46.3), True, {"1": "+5V", "2": "GND"})
part("R32", "TS06_R_0805_Back", "4k7 DNP", (2.6, 13.4), True, {"1": "+5V", "2": "SDA"})
part("R33", "TS06_R_0805_Back", "4k7 DNP", (16.2, 13.4), True, {"1": "+5V", "2": "SCL"})
for vt, r, tube, pad, cat, gpin, gname, tfp, txy, rxy in CH:
    part(vt, tfp, "MMBTA42", txy, True, {"1": "B" + vt[2:], "2": "GND", "3": cat})
    part(r, R805, "10k", rxy, True, {"1": gname, "2": "B" + vt[2:]})

# IN-17 anode drivers: TLP627 collector on 185 V, emitter -> 12k -> tube anode, 2x510k bleed to GND
part("U5", "TS06_SMDIP-4_Back", "TLP627", (6.8, 18.1), True, {"1": "LED_A0", "2": "GND", "3": "EMIT_S10", "4": "HV185"})
part("U6", "TS06_SMDIP-4_Back", "TLP627", (20.0, 18.1), True, {"1": "LED_A1", "2": "GND", "3": "EMIT_S1", "4": "HV185"})
part("R21", "TS06_R_0805_Back", "100R", (11.8, 13.4), True, {"1": "SEC_A0", "2": "LED_A0"})
part("R22", "TS06_R_0805_Back", "100R", (24.2, 13.4), True, {"1": "SEC_A1", "2": "LED_A1"})
part("R23", "TS06_R_2512_Back_R90", "12k", (11.45, 25.6), True, {"1": "EMIT_S10", "2": "ANODE_S10"})
part("R28", "TS06_R_1206_Back", "510k", (11.45, 31.0), True, {"1": "ANODE_S10", "2": "BLEED_S10"})
part("R29", "TS06_R_1206_Back", "510k", (11.45, 33.6), True, {"1": "BLEED_S10", "2": "GND"})
part("R24", "TS06_R_2512_Back_R90", "12k", (24.8, 25.6), True, {"1": "EMIT_S1", "2": "ANODE_S1"})
part("R30", "TS06_R_1206_Back", "510k", (24.8, 31.0), True, {"1": "ANODE_S1", "2": "BLEED_S1"})
part("R31", "TS06_R_1206_Back", "510k", (24.8, 33.6), True, {"1": "BLEED_S1", "2": "GND"})

# IN-15 anode resistors, one per tube, pad 1 up against the tube's anode pad
part("R38", "TS06_R_2512_Back_R90", "8k2", (39.4, 35.8), True, {"1": "ANODE_AM", "2": "HV185"})
part("R39", "TS06_R_2512_Back_R90", "8k2", (60.4, 35.6), True, {"1": "ANODE_PM", "2": "HV185"})

# colon switch (XS4 pin 2 is the colon's switched return) and the backlight switch
part("VT1", SOT, "MMBTA42", (56.0, 42.0), True, {"1": "B1", "2": "GND", "3": "COLON_RET"})
part("R1", "TS06_R_0805_Back", "10k", (60.2, 43.2), True, {"1": "DOT", "2": "B1"})
part("VT20", SOT, "MMBTA42", (27.5, 44.0), True, {"1": "B20", "2": "GND", "3": "BL_K"})
part("R20", "TS06_R_0805_Back", "1k", (27.5, 47.0), True, {"1": "BACKL", "2": "B20"})

# LEDs on the front, in the strip the fascia hides
part("HL1", "TS06_LED_D3.0mm", "amber 3mm", (V5_XY[0], 40.6), False, {"1": "BL_K", "2": "BL_A1"})
part("HL2", "TS06_LED_D3.0mm", "amber 3mm", (V6_XY[0], 40.6), False, {"1": "BL_K", "2": "BL_A2"})
part("HL3", "TS06_LED_D3.0mm", "amber 3mm", (48.0, 40.6), False, {"1": "GND", "2": "M_A"})
part("R25", "TS06_R_0805_Back_R90", "150R", (1.4, 42.5), True, {"1": "+5V", "2": "BL_A1"})
part("R27", "TS06_R_0805_Back_R90", "150R", (21.2, 43.1), True, {"1": "+5V", "2": "BL_A2"})
part("R26", "TS06_R_0805_Back", "220R", (48.0, 44.0), True, {"1": "+5V", "2": "M_A"})

# connectors, top entry, bodies on the back, joints behind the fascia
part("XS3", "TS06_JST_XH_B8B-XH-A_Back", "B8B-XH-A", (37.5, 51.1), True,
     {"1": "GND", "2": "+5V", "3": "BACKL", "4": "DOT", "5": "SEC_A0", "6": "SEC_A1", "7": "SDA", "8": "SCL"})
part("XS2", "TS06_IDC_2x05_Vertical_Back_R90", "IDC 2x5", (13.0, 50.0), True,
     {str(i + 1): K[XS2_ORDER[i]] for i in range(10)})
part("XS1", "TS06_JST_VH_B2P-VH_Back", "B2P-VH", (54.2, 49.5), True, {"1": "HV185", "2": "GND"})
part("XS4", "TS06_XS4_JST_XH_2p_RA", "B2B-XH-A", (63.0, 51.0), True, {"1": "HV185", "2": "COLON_RET"})

HOLES = [(24.8, 39.2), (65.2, 41.2)]
# HL3's GND pin joins the pour solid: tracks leave the pour around it too narrow for the two
# thermal spokes KiCad's DRC asks for, and a 3 mm LED lead draws little heat from the iron.
SOLID = {("HL3", "1")}       # M2.5; screw head clear of glass, standoff clear of parts

# ---------------------------------------------------------------- emit
NETS = [""] + sorted({n for *_, nets in P for n in nets.values()},
                     key=lambda s: (s not in ("GND", "+5V", "HV185"), s))
NI = {n: i for i, n in enumerate(NETS)}
out = []


def U(key):
    return str(uuid.uuid5(NS, key))


def place(ref, fp, val, x, y, back, nets):
    t = open(os.path.join(PRETTY, fp + ".kicad_mod"), encoding="utf8").read().rstrip()
    assert t.startswith("(footprint") and t.endswith(")")
    t = t[:-1].rstrip()
    if back and "B.CrtYd" not in t:        # a front-authored part mounted on the back
        for a, b in (('"F.SilkS"', '"B.SilkS"'), ('"F.Fab"', '"B.Fab"'), ('"F.CrtYd"', '"B.CrtYd"')):
            t = t.replace(a, b)
        t = t.replace("\n\t\t\t)\n\t\t)", "\n\t\t\t)\n\t\t\t(justify mirror)\n\t\t)")
    lay = '(layer "F.Cu")'
    t = t.replace(lay, ('(layer "B.Cu")' if back else lay) + f'\n\t(uuid "{U(ref)}")\n\t(at {x:.4f} {y:.4f})', 1)
    t = t.replace('(property "Reference" "REF**"', f'(property "Reference" "{ref}"', 1)
    t = re.sub(r'\(property "Value" "[^"]*"', f'(property "Value" "{val}"', t, count=1)
    k = [0]

    def fresh(m):
        k[0] += 1
        return f'(uuid "{U(ref + "/" + str(k[0]))}")'
    t = re.sub(r'\(uuid "[^"]*"\)', fresh, t)

    def netify(m):
        pn = m.group(1)
        if pn not in nets:
            return m.group(0)
        n = nets[pn]
        solid = "\n\t\t(zone_connect 2)" if (ref, pn) in SOLID else ""
        return re.sub(r'\(layers [^)]*\)', lambda L: L.group(0) + f'\n\t\t(net {NI[n]} "{n}")' + solid,
                      m.group(0), count=1)
    t = re.sub(r'\(pad "([^"]*)"[\s\S]*?\n\t\)', netify, t)
    missing = set(nets) - set(re.findall(r'\(pad "([^"]*)"', t))
    assert not missing, (ref, fp, missing)
    out.append(t + "\n)")


add = out.append
add(f'\t(gr_rect\n\t\t(start 0 0)\n\t\t(end {W} {H})\n\t\t(stroke\n\t\t\t(width 0.05)\n\t\t\t(type default)\n'
    f'\t\t)\n\t\t(fill none)\n\t\t(layer "Edge.Cuts")\n\t\t(uuid "{U("outline")}")\n\t)')
for p in P:
    place(*p)
for i, (hx, hy) in enumerate(HOLES):
    add(f'\t(footprint "MountingHole_2.7mm"\n\t\t(version {VER})\n\t\t(generator "{GEN}")\n'
        f'\t\t(generator_version "{GENV}")\n\t\t(layer "F.Cu")\n\t\t(uuid "{U("H" + str(i))}")\n'
        f'\t\t(at {hx} {hy})\n\t\t(descr "M2.5 clearance, non-plated")\n'
        f'\t\t(attr exclude_from_pos_files exclude_from_bom)\n'
        f'\t\t(pad "" np_thru_hole circle\n\t\t\t(at 0 0)\n\t\t\t(size 2.7 2.7)\n'
        f'\t\t\t(drill 2.7)\n\t\t\t(layers "F&B.Cu" "*.Mask")\n\t\t\t(uuid "{U("H" + str(i) + "p")}")\n\t\t)\n'
        f'\t\t(embedded_fonts no)\n\t)')

# ---------------------------------------------------------------- routing
# Staged, so each stage can be checked before the next one exists:
#     python3 tools/mkpcb_sec.py --route N      routes stages 1..N (default: all)
# Every run re-routes from the same placement, so stage 1 is identical whether it is
# emitted alone or under stages 2-5. Tracks are written with a bare net code, (net N):
# segment and via elements do not accept the (net N "NAME") form a pad does.
import sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pcbroute import Router, VIA_D, VIA_DRILL

STAGE = int(sys.argv[sys.argv.index("--route") + 1]) if "--route" in sys.argv else 99
BUS = lambda n: bool(re.fullmatch(r"K\d", n))
# High voltage, for clearance: the 185 V feed and everything that can stand near it - tube
# anodes, TLP627 emitters, bleed mid-points, IN-15 cathodes (a transistor that is off lets
# its cathode rise toward the anode) and the colon return. The IN-17 cathode bus K0-K9 is
# NOT in the class: the K155ID1 outputs it hangs from clamp near 60 V, and the tube's own
# pins sit 0.9 mm apart, so a 0.6 mm halo would forbid threading one track between two.
HV_NETS = sorted(n for n in NETS if n and (n in ("HV185", "COLON_RET")
                                           or n.startswith(("CAT_", "ANODE_", "EMIT_", "BLEED_"))))
PADS = []
for blk in out:
    if not blk.startswith("(footprint"):
        continue
    at = re.search(r'\n\t\(at ([\d.-]+) ([\d.-]+)\)', blk)
    ox, oy = float(at.group(1)), float(at.group(2))
    ref = re.search(r'\(property "Reference" "([^"]*)"', blk).group(1)
    for m in re.finditer(r'\(pad "([^"]*)" (\w+) (\w+)\n\t\t\(at ([\d.-]+) ([\d.-]+)\)\n'
                         r'\t\t\(size ([\d.]+) ([\d.]+)\)([\s\S]*?)\n\t\)', blk):
        px_, py_, pw, ph = ox + float(m.group(4)), oy + float(m.group(5)), float(m.group(6)), float(m.group(7))
        body = m.group(8)
        lay = re.search(r'\(layers ([^)]*)\)', body).group(1)
        drill = re.search(r'\(drill ([\d.]+)\)', body)
        net = re.search(r'\(net \d+ "([^"]*)"\)', body)
        PADS.append({"ref": ref, "pad": m.group(1), "type": m.group(2), "net": net.group(1) if net else None, "x": px_, "y": py_,
                     "layers": (0, 1) if "*.Cu" in lay else ((0,) if "F.Cu" in lay else (1,)),
                     "shape": ("circle", px_, py_, pw / 2) if m.group(3) == "circle" else ("rect", px_, py_, pw, ph),
                     "drill": float(drill.group(1)) if drill else None})
rt = Router(W, H, HV_NETS)
for p in PADS:
    if p["type"] == "np_thru_hole":
        rt.hole(p["x"], p["y"], p["drill"])
    else:
        rt.paint(p["net"], p["layers"], p["shape"])
        if p["type"] == "thru_hole":
            rt.drill(p["x"], p["y"], p["drill"])
        else:                               # no via in or against an SMD land: solder would wick down it
            rt.novia(p["shape"], VIA_D / 2 + 0.1)
for hx, hy in HOLES:
    rt.hole(hx, hy, 2.7)
pads_of, hub_pad = {}, {}
for p in PADS:
    if p["net"]:
        t = (p["x"], p["y"], p["layers"], p["shape"])
        pads_of.setdefault(p["net"], []).append(t)
        if p["ref"] == "XS2" or (p["ref"], p["pad"]) == ("XS3", "1"):    # bus nets from XS2, GND from XS3
            hub_pad[p["net"]] = t

STAGES = [
    ("high voltage, local: cathode channels, anode chains, colon return",
     lambda n: n in HV_NETS and n != "HV185" and not BUS(n), 0.25),
    ("the rest, negotiated together: IN-17 bus, 185 V feed, low-voltage signals, +5V, GND",
     lambda n: n == "HV185" or n not in HV_NETS,
     lambda n: 0.35 if n in ("HV185", "+5V") else 0.2),
]


def span(n):
    xs, ys = [p[0] for p in pads_of[n]], [p[1] for p in pads_of[n]]
    return (max(xs) - min(xs)) + (max(ys) - min(ys))


# The bus goes inside-out: the nets on XS2's middle pins take the direct lines first and
# the outer ones wrap round them, the one order in which a fan-out stays planar.
RANK = {K[d]: abs(i - 4.5) for i, d in enumerate(XS2_ORDER)}

t0 = time.time()
for si, (label, pick, width) in enumerate(STAGES[:STAGE]):
    order = sorted((n for n in pads_of if pick(n)), key=lambda n: (RANK.get(n, 0), span(n), n))
    nf0 = len(rt.failed)
    if si == 0:
        # Laid one net at a time. The router is greedy - whichever net goes first takes the
        # corridor - so when connections go unfound the stage is rolled back and re-run with its
        # failed nets moved to the front, and the attempt with the fewest failures is kept.
        # Deterministic: the same failures always give the same next order.
        base, best = rt.snapshot(), None
        for attempt in range(8):
            rt.restore(base)
            for n in order:
                rt.route_net(n, width, pads_of[n])
            lost = list(dict.fromkeys(f[0] for f in rt.failed[nf0:]))
            if best is None or len(rt.failed) < best[1]:
                best = (attempt, len(rt.failed), rt.snapshot())
            again = lost + [n for n in order if n not in lost]
            if not lost or again == order:
                break
            order = again
        rt.restore(best[2])
        print(f"stage 1 ({label}): {len(order)} nets, {len(rt.failed) - nf0} connection(s) "
              f"not found (kept attempt {best[0] + 1}), {time.time() - t0:.0f} s", flush=True)
    else:
        # Negotiated. A bus net grows from its XS2 pin, so each tube is wired toward the
        # connector; GND grows from XS3 like any other net - pours alone left pads in pockets
        # that signals had closed on both faces - and neither face is kept clear for it.
        rt.negotiate([(n, width(n), sorted(pads_of[n], key=lambda q: q is not hub_pad.get(n)), {})
                      for n in order], log=lambda m: print(m, flush=True))
        print(f"stage 2 ({label}): {len(order)} nets, {len(rt.failed) - nf0} not routed, "
              f"{time.time() - t0:.0f} s", flush=True)
for f in rt.failed:
    print("  NOT ROUTED", f)
for k, (x1, y1, x2, y2, w, lay, n) in enumerate(rt.segments):
    add(f'\t(segment\n\t\t(start {x1:.4f} {y1:.4f})\n\t\t(end {x2:.4f} {y2:.4f})\n\t\t(width {w})\n'
        f'\t\t(layer "{lay}")\n\t\t(net {NI[n]})\n\t\t(uuid "{U("seg" + str(k))}")\n\t)')
for k, (x, y, n) in enumerate(rt.vias):
    add(f'\t(via\n\t\t(at {x:.4f} {y:.4f})\n\t\t(size {VIA_D})\n\t\t(drill {VIA_DRILL})\n'
        f'\t\t(layers "F.Cu" "B.Cu")\n\t\t(net {NI[n]})\n\t\t(uuid "{U("via" + str(k))}")\n\t)')
# GND is also a pour on both faces, over whatever the tracks leave, joined through the GND
# tree's vias and pins. Each zone keeps 0.6 mm from all other copper, so high-voltage pads
# need no rule of their own. Through-hole pads keep thermal spokes for the iron; surface-
# mount pads join solid, since a land squeezed between tracks cannot always fit the two
# spokes KiCad's DRC asks for. Islands joined to nothing are removed.
if STAGE >= 2:
    for zl in ("F.Cu", "B.Cu"):
        add('\t(zone\n\t\t(net %d)\n\t\t(net_name "GND")\n\t\t(layers "%s")\n\t\t(uuid "%s")\n'
            '\t\t(name "GND")\n\t\t(hatch edge 0.5)\n\t\t(connect_pads thru_hole_only\n\t\t\t(clearance 0.6)\n\t\t)\n'
            '\t\t(min_thickness 0.25)\n\t\t(filled_areas_thickness no)\n'
            '\t\t(fill\n\t\t\t(thermal_gap 0.5)\n\t\t\t(thermal_bridge_width 0.5)\n\t\t\t(island_removal_mode 0)\n\t\t)\n'
            '\t\t(polygon\n\t\t\t(pts\n%s\n\t\t\t)\n\t\t)\n\t)'
            % (NI["GND"], zl, U("zone GND " + zl), "\n".join("\t\t\t\t(xy %.2f %.2f)" % pt for pt in
               ((0.5, 0.5), (W - 0.5, 0.5), (W - 0.5, H - 0.5), (0.5, H - 0.5)))))
print(f"{len(rt.segments)} tracks, {len(rt.vias)} vias")

head = [f'(kicad_pcb\n\t(version {VER})\n\t(generator "{GEN}")\n\t(generator_version "{GENV}")',
        '\t(general\n\t\t(thickness 1.6)\n\t\t(legacy_teardrops no)\n\t)', '\t(paper "A4")']
layers = ['\t(layers', '\t\t(0 "F.Cu" signal)', '\t\t(2 "B.Cu" signal)',
          '\t\t(9 "F.Adhes" user "F.Adhesive")', '\t\t(11 "B.Adhes" user "B.Adhesive")',
          '\t\t(13 "F.Paste" user)', '\t\t(15 "B.Paste" user)',
          '\t\t(5 "F.SilkS" user "F.Silkscreen")', '\t\t(7 "B.SilkS" user "B.Silkscreen")',
          '\t\t(1 "F.Mask" user)', '\t\t(3 "B.Mask" user)',
          '\t\t(17 "Dwgs.User" user "User.Drawings")', '\t\t(19 "Cmts.User" user "User.Comments")',
          '\t\t(21 "Eco1.User" user "User.Eco1")', '\t\t(23 "Eco2.User" user "User.Eco2")',
          '\t\t(25 "Edge.Cuts" user)', '\t\t(27 "Margin" user)',
          '\t\t(31 "F.CrtYd" user "F.Courtyard")', '\t\t(29 "B.CrtYd" user "B.Courtyard")',
          '\t\t(35 "F.Fab" user)', '\t\t(33 "B.Fab" user)',
          '\t\t(39 "User.1" user "Keepouts")', '\t\t(41 "User.2" user)',
          '\t\t(43 "User.3" user)', '\t\t(45 "User.4" user)', '\t)']
setup = ['\t(setup', '\t\t(pad_to_mask_clearance 0)', '\t\t(allow_soldermask_bridges_in_footprints no)',
         '\t\t(tenting\n\t\t\t(front yes)\n\t\t\t(back yes)\n\t\t)', '\t)']
nets = ['\t(net %d "%s")' % (i, n) for i, n in enumerate(NETS)]
if "--out" in sys.argv:                    # an experiment written elsewhere, not over the board
    OUT = os.path.abspath(sys.argv[sys.argv.index("--out") + 1])
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf8", newline="\n") as fh:
    fh.write("\n".join(head + layers + setup + nets + out) + "\n\t(embedded_fonts no)\n)\n")
print("wrote", os.path.relpath(OUT, ROOT))
print(f"board {W} x {H} mm, {len(P)} parts, {len(NETS) - 1} nets, {len(HOLES)} holes")
