#!/usr/bin/env python3
"""TS06-MAIN: the netlist, shared by mksch_main.py (schematic) and mkpcb_main.py (board).

One board for the whole clock, replacing the inherited AlexGyver board + TS06-SEC +
TS06-COLON, in two builds - "smd" and "tht" - that differ only in how a part is made and,
in two places, in what the part is (the RTC and the MOSFET package). Everything below is
what the two builds have in common: every part, every pin, every net. The generators
import it; tools/checkmatch.py then proves each build's board against its own schematic.

Where the numbers come from:
  * the inherited board's copper - TERMINAL-06-measurements-PCB-GYVER-NETLIST.md: the
    К155ИД1 wiring (A0..A3 -> C B D A, outputs -> cathode digits), the ИН-12 pad functions,
    the Nano's role, the converter topology;
  * TS06-SEC (tools/mkpcb_sec.py): the AM/PM section, the colon switch, the ИН-17 chains;
  * the 17.09.26 decisions (PCB/README.md): 12 V in, Nano in both builds, six opto
    singles, one anode resistor per digit tube plus DNP bleeds, eight backlight LEDs, the
    "m" LED on D12, bare DS3231 in the SMD build and the mini module in the THT build;
  * the bench gates (knowledge/TERMINAL-06-measurements-TS06-MAIN-gates.txt): the anode
    resistor values marked TBC are design values until gate 2 is measured, and the ИН-17 /
    ИН-15 pad maps hold until gates 3 and 4 are lit.

PIN NUMBERS ARE PAD NAMES. A part's pins are keyed by the pad name of its footprint, and
the schematic symbols use the same numbers, so "U2.7" means the same physical pin in both
files. TO-92 transistors are numbered by function (1 B, 2 E, 3 C) to match SOT-23, and the
footprint is drawn to suit.

NET NAMES: GND, +5V, +12V; HV185 the rail; K0..K9 the cathode bus BY DIGIT (K3 lights a 3
on every multiplexed tube); ANODE_/EMIT_/BLEED_ + H10 H1 M10 M1 S10 S1 for the six digit
tubes; CAT_B_*/CAT_A_* the ИН-15 cathodes as SEC named them; D2..D13, A0..A7, SDA, SCL the
Nano pins by their Arduino names.
"""

# ---------------------------------------------------------------- the display chain
# Inherited board: the firmware shows digit d with code digitMask[d] (BOARD_TYPE 0), the
# К155ИД1 pulls output Q_code low, and the copper takes that output to the cathode of
# digit d. Keeping BOARD_TYPE 0 means keeping this map: output c -> cathode digit.
DIGIT_MASK0 = [7, 3, 6, 4, 1, 9, 8, 0, 5, 2]
Q_TO_DIGIT = {c: DIGIT_MASK0.index(c) for c in range(10)}         # Q0->7, Q1->4, ... Q9->5
# К155ИД1 / SN74141 DIP-16 pinout, confirmed on the inherited copper (VCC 5, GND 12, the
# four inputs) and through the 10/10 digit check (the ten outputs).
K155 = {1: "Q8", 2: "Q9", 3: "A1", 4: "D8", 5: "VCC", 6: "B2", 7: "C4", 8: "Q2",
        9: "Q3", 10: "Q7", 11: "Q6", 12: "GND", 13: "Q4", 14: "Q5", 15: "Q1", 16: "Q0"}
# The inherited board wires Nano A0->C(4), A1->B(2), A2->D(8), A3->A(1); the firmware's
# decoderNibble() assumes exactly that (1_setup.ino). Keep it.
K155_INPUT = {"A1": "A3", "B2": "A1", "C4": "A0", "D8": "A2"}
# ИН-12А on TS06_IN12_Socket: pad -> cathode digit / anode / no pin (datasheet pin d on pad
# ((7 - d) mod 12) + 1, checked against the copper).
IN12_PAD = {1: "5", 2: "6", 3: "7", 4: "8", 5: "9", 6: "0", 7: "A", 8: None, 9: "1", 10: "2", 11: "3", 12: "4"}
# ИН-15Б (V9, "A" = AM) and ИН-15А (V10, "P" = PM) on the same socket, as SEC mapped them
# from tec.org.ru / rudatasheet.ru (bench gate 4). pad -> glyph.
IN15B_PAD = {1: "VOLT", 2: "HENRY", 3: "HERTZ", 4: None, 5: "FARAD", 6: "WATT", 7: "A", 8: None,
             9: "AMP", 10: "OHM", 11: None, 12: "SIEMENS"}
IN15A_PAD = {1: "MEGA", 2: "MILLI", 3: "PLUS", 4: "MINUS", 5: "P", 6: "MICRO", 7: "A", 8: None,
             9: "NANO", 10: "PCT", 11: "PI", 12: "KILO"}

TUBES = ["H10", "H1", "M10", "M1", "S10", "S1"]                    # hours tens ... seconds units
TUBE_PIN = {"H10": "D3", "H1": "D4", "M10": "D5", "M1": "D6", "S10": "D2", "S1": "D13"}  # anode drive
ANODE_R = {"H10": "6k8 TBC", "H1": "6k8 TBC", "M10": "6k8 TBC", "M1": "6k8 TBC", "S10": "12k", "S1": "12k"}

# ---------------------------------------------------------------- footprints per build
FP = {
    # passives
    "R":      {"smd": "TS06_R_0805_Back",            "tht": "TS06_R_Axial_L6.3mm_P2.54mm_Vertical_Back"},
    "R_HV":   {"smd": "TS06_R_1206_Back",            "tht": "TS06_R_Axial_L6.3mm_P2.54mm_Vertical_Back"},   # <100 V across it
    "R_PWR":  {"smd": "TS06_R_2512_Back",            "tht": "TS06_R_Axial_L9.9mm_P5.08mm_Vertical_Back"},    # anode / ballast, 0.5 W
    "C":      {"smd": "TS06_C_0805_Back",            "tht": "TS06_C_Disc_P2.50mm_Back"},
    "C_BIG":  {"smd": "TS06_C_1206_Back",            "tht": "TS06_C_Disc_P5.00mm_Back"},     # 1u / 10u ceramic
    "CP":     {"smd": "TS06_CP_Elec_8x10.5_Back",    "tht": "TS06_CP_Radial_D6.3mm_P2.50mm_Back"},
    "CP_HV":  {"smd": "TS06_CP_Elec_10x10.5_Back",   "tht": "TS06_CP_Radial_D8.0mm_P3.50mm_Back"},
    "L":      {"smd": "TS06_L_12x12mm_Back",         "tht": "TS06_L_Radial_D10.0mm_P5.00mm_Back"},
    "D_HV":   {"smd": "TS06_D_SMA_Back",             "tht": "TS06_D_DO-41_P10.16mm_Back"},
    "D_IN":   {"smd": "TS06_D_SMA_Back",             "tht": "TS06_D_DO-201_P15.24mm_Back"},
    "F":      {"smd": "TS06_Fuse_1812_Back",         "tht": "TS06_Fuse_Radial_MF-R_Back"},
    "RP":     {"smd": "TS06_Trimmer_3224W_Back",     "tht": "TS06_Trimmer_3296W_Back"},
    # semiconductors
    "NPN":    {"smd": "TS06_SOT-23_Std_Back",        "tht": "TS06_TO-92_Back"},
    "NMOS":   {"smd": "TS06_TO-263-2_Back",          "tht": "TS06_TO-220_Horizontal_Back"},
    "OPTO":   {"smd": "TS06_SMDIP-4_Back",           "tht": "TS06_DIP-4_Back"},
    "DIP8":   {"smd": "TS06_SOIC-8_Back",            "tht": "TS06_DIP-8_Back"},
    "MCP":    {"smd": "TS06_SOIC-28W_Back",          "tht": "TS06_DIP-28W_Back"},
    # through-hole in both builds: mechanical parts, the decoder, the Nano, the regulator
    "DIP16":  {"smd": "TS06_DIP-16_Back",            "tht": "TS06_DIP-16_Back"},
    "NANO":   {"smd": "TS06_Arduino_Nano_Back",      "tht": "TS06_Arduino_Nano_Back"},
    "REG":    {"smd": "TS06_R78E_SIP3_Back",         "tht": "TS06_R78E_SIP3_Back"},
    "JACK":   {"smd": "TS06_BarrelJack_Back",        "tht": "TS06_BarrelJack_Back"},
    "PH6":    {"smd": "TS06_JST_PH_S6B-PH-SM4-TB_Back", "tht": "TS06_JST_PH_S6B-PH-K-S_Back"},
    "LED":    {"smd": "TS06_LED_D3.0mm",             "tht": "TS06_LED_D3.0mm"},
    "INS1":   {"smd": "TS06_INS1_Lamp",              "tht": "TS06_INS1_Lamp"},
    "IN12":   {"smd": "TS06_IN12_Socket",            "tht": "TS06_IN12_Socket"},
    "IN17":   {"smd": "TS06_IN17_Socket",            "tht": "TS06_IN17_Socket"},
    # the RTC differs by build
    "RTC":    {"smd": "TS06_SOIC-16W_Back",          "tht": "TS06_PinHeader_1x05_Back"},
    "BATT":   {"smd": "TS06_BatteryHolder_3034_Back", "tht": None},
}
FRONT = {"LED", "INS1", "IN12", "IN17"}                 # everything else mounts on the back


class Part:
    __slots__ = ("ref", "value", "sym", "kind", "pins", "group", "note", "builds")

    def __init__(self, ref, value, sym, kind, pins, group, note="", builds=("smd", "tht")):
        self.ref, self.value, self.sym, self.kind = ref, value, sym, kind
        self.pins = {str(k): v for k, v in pins.items()}     # pad name -> net name or None
        self.group, self.note, self.builds = group, note, builds

    def fp(self, build):
        return FP[self.kind][build]

    @property
    def front(self):
        return self.kind in FRONT


PARTS = []


def part(*a, **k):
    p = Part(*a, **k)
    assert not any(q.ref == p.ref and set(q.builds) & set(p.builds) for q in PARTS), p.ref
    PARTS.append(p)
    return p


def R(ref, value, a, b, kind="R", group="", note="", **k):
    return part(ref, value, "R", kind, {1: a, 2: b}, group, note, **k)


def C(ref, value, a, b, kind="C", group="", note="", **k):
    return part(ref, value, "C", kind, {1: a, 2: b}, group, note, **k)


# ================================================================ power entry, 12 V
part("XS1", "DC 5.5x2.1", "Jack_DC", "JACK", {1: "VIN_J", 2: "GND", 3: None}, "power",
     "12 V barrel jack, centre positive, the same style of jack the stock board takes 5 V on.")
part("F1", "PTC 1.1A", "Fuse", "F", {1: "VIN_J", 2: "VIN_F"}, "power", "Resettable fuse in the 12 V feed.")
part("VD2", "SS34 / 1N5822", "D_Schottky", "D_IN", {1: "+12V", 2: "VIN_F"}, "power",
     "Reverse-polarity protection: pin 1 cathode to +12V, pin 2 anode from the fuse.")
C("C8", "100u 25V", "+12V", "GND", "CP", "power", "12 V bulk: the boost draws 1.3 A pulses at 31 kHz.")
C("C9", "1u 50V", "+12V", "GND", "C_BIG", "power")
part("U14", "R-78E5.0-1.0", "Reg_SIP3", "REG", {1: "+12V", 2: "GND", 3: "+5V"}, "power",
     "Switching 5 V regulator, 78xx pinout: 1 in, 2 GND, 3 out. Feeds the whole 5 V rail, Nano included "
     "(its 5V pin, VIN left open). USB alone also feeds the rail through the Nano's own diode.")
C("C10", "10u 25V", "+12V", "GND", "C_BIG", "power")
C("C11", "10u", "+5V", "GND", "C_BIG", "power")
C("C3", "10u", "+5V", "GND", "C_BIG", "power", "5 V bulk by the Nano and the decoder.")

# ================================================================ MCU
NANO = {1: None, 2: None, 3: None, 4: "GND", 5: "D2", 6: "D3", 7: "D4", 8: "D5", 9: "D6", 10: "D7",
        11: "D8", 12: "D9", 13: "D10", 14: "D11", 15: "D12", 16: "D13", 17: None, 18: None,
        19: "A0", 20: "A1", 21: "A2", 22: "A3", 23: "SDA", 24: "SCL", 25: "A6", 26: "A7",
        27: "+5V", 28: None, 29: "GND", 30: None}
part("U1", "Arduino Nano", "Arduino_Nano", "NANO", NANO, "mcu",
     "KiCad Module:Arduino_Nano numbering: 1 TX, 2 RX, 3 RST, 4 GND, 5-16 D2..D13, 17 3V3, 18 AREF, "
     "19-26 A0..A7, 27 +5V, 28 RST, 29 GND, 30 VIN. The pin map is the firmware's: D2 S10 anode, D3-D6 "
     "H10 H1 M10 M1 anodes, D7/D8 buttons, D9 HV clock, D10 colon, D11 backlight, D12 the m LED, D13 S1 "
     "anode, A0-A3 decoder, A4/A5 I2C, A6 rotary, A7 levers. USB at the bottom edge, reachable.")

# ================================================================ decoder and the cathode bus
K155_PINS = {}
for pin, fn in K155.items():
    if fn.startswith("Q"):
        K155_PINS[pin] = f"K{Q_TO_DIGIT[int(fn[1])]}"
    elif fn == "VCC":
        K155_PINS[pin] = "+5V"
    elif fn == "GND":
        K155_PINS[pin] = "GND"
    else:
        K155_PINS[pin] = K155_INPUT[fn]
part("U2", "K155ID1", "K155ID1", "DIP16", K155_PINS, "decoder",
     "The one decoder for all six digit tubes. Output Q_c drives cathode digit d with digitMask[d] = c, "
     "exactly as the inherited board, so BOARD_TYPE 0 stays valid.")
C("C4", "100n", "+5V", "GND", "C", "decoder")

# ================================================================ the six digit tubes and their anode chains
for i, nm in enumerate(["H10", "H1", "M10", "M1"]):
    pins = {}
    for pad, f in IN12_PAD.items():
        pins[pad] = None if f is None else ("ANODE_" + nm if f == "A" else "K" + f)
    part(f"V{i + 1}", "IN-12A", "Tube_IN12", "IN12", pins, "digits",
         f"{nm}: pad 7 anode, pad 8 no pin, the rest the cathode bus by digit (IN12_PAD).")
for i, nm in enumerate(["S10", "S1"]):
    pins = {str(d): f"K{d}" for d in range(10)}
    pins["A"] = "ANODE_" + nm
    part(f"V{i + 5}", "IN-17", "Tube_IN17", "IN17", pins, "digits",
         f"{nm}: pad names are the cathode digits per judge2005's IN-17 (bench gate 3).")
for i, nm in enumerate(TUBES):
    u = f"U{i + 5}"
    part(u, "TLP627", "TLP627", "OPTO", {1: "OPT_" + nm, 2: "GND", 3: "EMIT_" + nm, 4: "HV185"}, "anodes",
         f"Anode switch for {nm}, LED from {TUBE_PIN[nm]}: 1 LED anode, 2 LED cathode, 3 emitter, 4 collector.")
    R(f"R{21 + i}", "470R", TUBE_PIN[nm], "OPT_" + nm, "R", "anodes",
      "LED series resistor, one per channel: 8 mA, the current the stock board ran its optos at.")
    R(f"R{27 + i}", ANODE_R[nm], "EMIT_" + nm, "ANODE_" + nm, "R_PWR", "anodes",
      "Anode series resistor, one per tube. TBC values wait for bench gate 2 (sustaining voltage).")
    R(f"R{33 + 2 * i}", "510k DNP", "ANODE_" + nm, "BLEED_" + nm, "R_HV", "anodes",
      "Bleed pair, fitted only if the bench says so (anode driver study).")
    R(f"R{34 + 2 * i}", "510k DNP", "BLEED_" + nm, "GND", "R_HV", "anodes")

# ================================================================ AM/PM: two MCP23017, eighteen switches
MCP_COMMON = {9: "+5V", 10: "GND", 11: None, 12: "SCL", 13: "SDA", 14: None, 16: "GND", 17: "GND",
              18: "+5V", 19: None, 20: None}
CH = []                                                     # (VT, R, tube, pad, cathode net, expander pin, gpio net)
n = 2
for tube, pmap, u, gp in (("V9", IN15B_PAD, "U3", None), ("V10", IN15A_PAD, "U4", None)):
    k = 0
    for pad, glyph in pmap.items():
        if glyph in (None, "A"):
            continue
        pin = 21 + k if k < 8 else 1 + (k - 8)                # GPA0..7 then GPB0..1
        gname = f"{u}_GP{'A' if k < 8 else 'B'}{k if k < 8 else k - 8}"
        CH.append((f"VT{n}", f"R{n}", tube, pad, f"CAT_{'B' if tube == 'V9' else 'A'}_{glyph}", u, pin, gname))
        n += 1
        k += 1
for u, addr_a0 in (("U3", "GND"), ("U4", "+5V")):
    pins = dict(MCP_COMMON)
    pins[15] = addr_a0
    for p in list(range(1, 9)) + list(range(21, 29)):
        pins[p] = None
    for vt, r, tube, pad, cat, uu, pin, gname in CH:
        if uu == u:
            pins[pin] = gname
    part(u, "MCP23017", "MCP23017", "MCP", pins, "ampm",
         f"I2C expander at 0x2{0 if u == 'U3' else 1} (A0 = {addr_a0}), one per ИН-15: "
         "9 VDD, 10 VSS, 12 SCL, 13 SDA, 15-17 A0-A2, 18 RESET high, 21-28 GPA0-7, 1-8 GPB0-7.")
C("C1", "100n", "+5V", "GND", "C", "ampm")
C("C2", "100n", "+5V", "GND", "C", "ampm")
for vt, r, tube, pad, cat, u, pin, gname in CH:
    b = "B" + vt[2:]
    part(vt, "MPSA42", "Q_NPN_BEC", "NPN", {1: b, 2: "GND", 3: cat}, "ampm",
         "300 V low-side cathode switch: 1 base, 2 emitter, 3 collector.")
    R(r, "10k", gname, b, "R", "ampm")
for ref, val, pmap, anode in (("V9", "IN-15B", IN15B_PAD, "ANODE_AM"), ("V10", "IN-15A", IN15A_PAD, "ANODE_PM")):
    pins = {}
    for pad, glyph in pmap.items():
        pins[pad] = None if glyph is None else (anode if glyph == "A" else f"CAT_{'B' if ref == 'V9' else 'A'}_{glyph}")
    part(ref, val, "Tube_IN12", "IN12", pins, "ampm",
         f"{val} on the ИН-12 socket pattern; pad 7 anode, pads per SEC's map (bench gate 4).")
R("R56", "8k2", "ANODE_AM", "HV185", "R_PWR", "ampm", "Static anode resistor, one per ИН-15 (spec §3; gate 2 checks the current).")
R("R57", "8k2", "ANODE_PM", "HV185", "R_PWR", "ampm")
R("R54", "4k7", "+5V", "SDA", "R", "ampm", "I2C pull-ups. The DS3231 mini module may carry its own; two in parallel is still fine.")
R("R55", "4k7", "+5V", "SCL", "R", "ampm")

# ================================================================ colon
part("V7", "INS-1", "Lamp_Neon", "INS1", {1: "COLON_U", 2: "COLON_RET"}, "colon", "Upper colon neon, own 220k ballast.")
part("V8", "INS-1", "Lamp_Neon", "INS1", {1: "COLON_L", 2: "COLON_RET"}, "colon", "Lower colon neon, own 220k ballast.")
R("R58", "220k", "HV185", "COLON_U", "R_PWR", "colon", "Never shared between the two lamps (spec §3).")
R("R59", "220k", "HV185", "COLON_L", "R_PWR", "colon")
part("VT1", "MPSA42", "Q_NPN_BEC", "NPN", {1: "B1", 2: "GND", 3: "COLON_RET"}, "colon",
     "Low-side switch for both lamps, PWM-faded from D10.")
R("R1", "10k", "D10", "B1", "R", "colon")

# ================================================================ backlight and the "m" LED
for i in range(8):
    part(f"HL{i + 1}", "amber 3mm", "LED", "LED", {1: "BL_K", 2: f"BL_A{i + 1}"}, "backlight",
         "Backlight, one under each tube: 1 cathode (square), 2 anode.")
    R(f"R{45 + i}", "220R", "+5V", f"BL_A{i + 1}", "R", "backlight")
part("VT20", "MPSA42", "Q_NPN_BEC", "NPN", {1: "B20", 2: "GND", 3: "BL_K"}, "backlight",
     "Backlight switch, ~110 mA: 470R base resistor keeps it saturated.")
R("R20", "470R", "D11", "B20", "R", "backlight")
part("HL9", "amber 3mm", "LED", "LED", {1: "GND", 2: "M_A"}, "backlight",
     "The m of AM/PM, behind its printed stencil, driven straight from D12 so firmware decides when.")
R("R53", "220R", "D12", "M_A", "R", "backlight")

# ================================================================ fascia
part("J1", "PH 6", "Conn_PH6", "PH6", {1: "+5V", 2: "GND", 3: "A6", 4: "A7", 5: "D7", 6: "D8"}, "fascia",
     "The panel cable. Pin order is a specification shared with both fascia builds.")
C("C5", "100n", "A6", "GND", "C", "fascia", "Ladder filters at the board end (spec §2).")
C("C6", "100n", "A7", "GND", "C", "fascia")

# ================================================================ RTC - the one section that differs by build
DS3231 = {1: None, 2: "+5V", 3: None, 4: None, 5: None, 6: None, 7: None, 8: None, 9: None, 10: None,
          11: None, 12: None, 13: "GND", 14: "VBAT", 15: "SDA", 16: "SCL"}
part("U13", "DS3231SN", "DS3231", "RTC", DS3231, "rtc",
     "SO-16: 1 32K, 2 VCC, 3 INT/SQW, 4 RST, 13 GND, 14 VBAT, 15 SDA, 16 SCL. Integrated crystal.", builds=("smd",))
part("BT1", "CR2032", "Battery", "BATT", {1: "VBAT", 2: "GND"}, "rtc", "Keystone 3034 holder: 1 +, 2 -.", builds=("smd",))
C("C15", "100n", "+5V", "GND", "C", "rtc", builds=("smd",))
part("U13", "DS3231 mini", "RTC_mini", "RTC", {1: "GND", 2: None, 3: "SCL", 4: "SDA", 5: "+5V"}, "rtc",
     "The small DS3231 module on a 5-way header, pin order - NC C D + as the stock board's own RTC MINI "
     "header has it.", builds=("tht",))

# ================================================================ 185 V converter, regulated
part("L1", "220u 2A", "L", "L", {1: "+12V", 2: "SW"}, "hv",
     "220 uH, Isat >= 1.8 A: 1.3 A peaks at 12 V in, 23.8 us on (DUTY 190 at 31 kHz).")
part("VT21", "IRF840", "Q_NMOS_GDS", "NMOS", {1: "GATE", 2: "SW", 3: "GND"}, "hv",
     "500 V switch, driven to 12 V by U11. TO-220 lying flat in the THT build, D2PAK (IRF840S) in SMD.")
part("VD1", "US1J / HER106", "D_Fast", "D_HV", {1: "HV185", 2: "SW"}, "hv", "Fast 600 V rectifier: 1 cathode, 2 anode.")
C("C7", "4u7 400V", "HV185", "GND", "CP_HV", "hv", "The reservoir. 400 V, not the stock 350 V.")
R("R60", "470k", "HV185", "BLEED_HV", "R_HV", "hv", "Bleeder pair: the reservoir is safe to touch ~10 s after power-off.")
R("R61", "470k", "BLEED_HV", "GND", "R_HV", "hv")
# feedback: 185 V / (1.5 M + 20.5 k) * 20.5 k = 2.5 V; trimmer as a rheostat gives 152..252 V
R("R62", "750k 1%", "HV185", "FB_MID", "R_HV", "hv", "Divider top, two in series so each sees under 100 V.")
R("R63", "750k 1%", "FB_MID", "FB", "R_HV", "hv")
R("R64", "15k 1%", "FB", "FB_LOW", "R", "hv", "Divider bottom, fixed part.")
part("RP1", "10k", "Trimmer", "RP", {1: "FB_LOW", 2: "GND", 3: "GND"}, "hv",
     "Rail set-point, 152-252 V. Wiper tied to the grounded end: an open wiper lowers the rail, never raises it.")
part("U12", "LM393", "LM393", "DIP8", {1: "PWM_G", 2: "FB", 3: "VREF", 4: "GND", 5: "VREF", 6: "GND", 7: None, 8: "+5V"}, "hv",
     "Comparator: when FB rises above VREF its open collector holds the driver input low and the switch stays "
     "off until the rail sags back. Bang-bang regulation clocked by D9. Second half parked.")
R("R69", "10k 1%", "+5V", "VREF", "R", "hv", "2.5 V reference from the regulated 5 V rail.")
R("R70", "10k 1%", "VREF", "GND", "R", "hv")
C("C14", "100n", "VREF", "GND", "C", "hv")
R("R65", "1M", "PWM_G", "VREF", "R", "hv", "A little hysteresis, about 1 V of rail.")
C("C13", "100n", "+5V", "GND", "C", "hv", "LM393 decoupling.")
R("R66", "2k2", "D9", "PWM_G", "R", "hv", "The Nano's 31 kHz clock into the gating node; the comparator can pull it down.")
R("R71", "10k", "PWM_G", "GND", "R", "hv", "Defined low when the Nano is not driving D9.")
part("U11", "TC4420", "TC4420", "DIP8", {1: "+12V", 2: "PWM_G", 3: None, 4: "GND", 5: "GND", 6: "GATE_D", 7: "GATE_D", 8: "+12V"}, "hv",
     "Non-inverting MOSFET driver, TTL input, 12 V out: 1/8 VDD, 2 IN, 4/5 GND, 6/7 OUT. MCP1407 is a drop-in.")
C("C12", "1u 50V", "+12V", "GND", "C_BIG", "hv", "Driver decoupling, right at pins 1 and 4.")
R("R67", "10R", "GATE_D", "GATE", "R", "hv")
R("R68", "10k", "GATE", "GND", "R", "hv", "Gate held off while the driver is unpowered.")

# ---------------------------------------------------------------- derived views
HV_NETS = sorted({n for p in PARTS for n in p.pins.values() if n and (
    n in ("HV185", "SW", "BLEED_HV", "FB_MID", "COLON_RET", "COLON_U", "COLON_L")
    or n.startswith(("ANODE_", "EMIT_", "BLEED_", "CAT_")))})


def parts(build):
    return [p for p in PARTS if build in p.builds]


def nets(build):
    out = {}
    for p in parts(build):
        for pin, n in p.pins.items():
            if n:
                out.setdefault(n, []).append(f"{p.ref}.{pin}")
    return out


if __name__ == "__main__":
    for b in ("smd", "tht"):
        ns = nets(b)
        single = [n for n, m in ns.items() if len(m) < 2]
        print(f"{b}: {len(parts(b))} parts, {len(ns)} nets, {sum(len(m) for m in ns.values())} connected pins;"
              f" single-pin nets: {single}")
    print("HV class:", " ".join(HV_NETS))
