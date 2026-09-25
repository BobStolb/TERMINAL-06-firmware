#!/usr/bin/env python3
"""TS06-DISP + TS06-DRV: the through-hole clock as two boards, the way the AlexGyver board is.

    python3 tools/ts06pair.py          # prints both boards' parts, nets and the checks below

THE SPLIT (owner, 24.09.26). The display board carries the tubes, the colon neons, the
backlight LEDs and the board-to-board headers - NOTHING ELSE. Every driver lives on the
driver board behind it. That is AlexGyver's NixieClock v2 exactly: "two boards: lower (all
control electronics) and upper (lamps and LED backlight)", single-sided, through-hole, joined
by pin headers (рейка штыревая + гнёзда на плату). Why it is right here as well:
  * the display board is the one the customer looks at and the one with the hard geometry -
    eight pin fields at positions fixed by the case. With nothing on it but tubes, its copper
    can be designed the way the Gyver tube half was: the ten-line cathode bus threaded through
    the sockets on ONE face, zero vias, and a front face that is black mask and pads only;
  * the driver board has no tube fields at all, so its parts go in functional blocks behind
    the tubes they drive, and every net can be laid on one face or the other deliberately;
  * the previous attempt put the drivers on the display side (tools/ts06split.py, cut "B"):
    ~80 through-hole parts beside the pin fields, joints showing on the face, and the board
    that would not route (Claude outputs/TS06-routing-study.md).

TWO CIRCUIT CHANGES, both the owner's (24.09.26), both against the one-board netlist
tools/ts06main.py:
  1. The ИН-15 pair is driven by one К155ИД1 each, fed a nibble apiece from ONE MCP23017's
     port A. A symbol tube lights one glyph at a time, so a decoder does the whole job, idle
     animation included; it replaces eighteen MPSA42s, eighteen base resistors and the second
     expander - 37 parts and ~110 joints. The AM/PM firmware is not written yet, so nothing is
     rewritten: it writes a code 0-9 per tube, and 10-15 blanks it, exactly like the digits.
  2. Every backlight LED is ADDRESSABLE, so a lit LED can say which tube's setting is being
     changed. The eight LEDs are sourced one each from the MCP23017's port B through their own
     resistor; their cathodes stay common (BL_K) behind the one MPSA42 on D11, so D11 is still
     the global brightness PWM. The "m" LED joins BL_K too, so it dims with the backlight.
The Nano pin map is unchanged (firmware/nixieClock_TS06): D2..D6, D13 anodes, D7/D8 buttons,
D9 HV clock, D10 colon, D11 backlight PWM, D12 "m", A0..A3 decoder, A4/A5 I2C, A6/A7 fascia.

THE HEADERS are a specification shared by the two boards, like the fascia cable. DISP carries
male strips (XP) on its back, DRV the mating female strips (XS) on the face towards it; pin n of
XPk mates pin n of XSk. The order of every strip below is the order the display board's copper
arrives in - it was designed, not left to the router - so it must not be edited without
re-laying tools/mkpcb_disp.py.
  cathode lines only (<= 60 V, the К155ИД1 clamps them):
    XP11  left edge, 10     the ИН-12 bus, one pin per strand, level with its entry into H10
    XP12  top edge, 28      pins 1-10 the ИН-17 bundle - one pin group feeds BOTH ИН-17s, S10 on
                            the back face and S1 on the front, the pin being the layer change;
                            11-18 ИН-15Б and 19-28 ИН-15А, each tube wrapped from above
  bottom row, anodes, colon and LEDs:
    XP21  BL_K + H10/H1     XP22 colon     XP23 M10/M1     XP24 S10/S1     XP25 AM/PM + m + BL_K
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ts06main as M

DISP, DRV = "disp", "drv"


class Part:
    __slots__ = ("ref", "value", "fp", "pins", "board", "group", "note", "rot")

    def __init__(self, ref, value, fp, pins, board, group="", note=""):
        self.ref, self.value, self.fp, self.board = ref, value, fp, board
        self.pins = {str(k): v for k, v in pins.items()}
        self.group, self.note = group, note


PARTS = []


def part(ref, value, fp, pins, board, group="", note=""):
    assert not any(p.ref == ref for p in PARTS), ref
    p = Part(ref, value, fp, pins, board, group, note)
    PARTS.append(p)
    return p


def R(ref, value, a, b, fp="TS06_R_Axial_DIN0207_P10.16mm", group="", note=""):
    return part(ref, value, fp, {1: a, 2: b}, DRV, group, note)


def C(ref, value, a, b, fp="TS06_C_Disc_P5.00mm", group="", note=""):
    return part(ref, value, fp, {1: a, 2: b}, DRV, group, note)


R_HV = "TS06_R_Axial_DIN0309_P12.70mm"      # 0.5 W, 350 V: anode, ballast, divider
R_V = "TS06_R_Axial_DIN0207_P2.54mm_Vertical"   # standing 0.25 W: the DNP bleeds
CP = "TS06_CP_Radial_D6.3mm_P2.50mm"
NPN = "TS06_TO-92_Inline_Wide"              # MPSA42 E-B-C on a 2.54 mm pitch: 0.94 mm between pads
DIP16, DIP8, DIP4, DIP28 = ("TS06_DIP-16_W7.62mm_Socket", "TS06_DIP-8_W7.62mm_Socket",
                            "TS06_DIP-4_W7.62mm_Socket", "TS06_DIP-28_W7.62mm_Socket")


def mpsa42(ref, base, coll, group, note=""):
    # TO-92 as the datasheet numbers it: 1 emitter, 2 base, 3 collector, flat face towards you.
    return part(ref, "MPSA42", NPN, {1: "GND", 2: base, 3: coll}, DRV, group, note or "300 V NPN, E-B-C.")


# ======================================================================== DISPLAY BOARD
TUBES = M.TUBES                                                   # H10 H1 M10 M1 S10 S1
for i, nm in enumerate(["H10", "H1", "M10", "M1"]):
    pins = {pad: (None if f is None else ("ANODE_" + nm if f == "A" else "K" + f)) for pad, f in M.IN12_PAD.items()}
    part(f"V{i + 1}", "IN-12A", "TS06_IN12_Socket", pins, DISP, "digits", f"{nm}; pad 7 anode, pad 8 no pin.")
for i, nm in enumerate(["S10", "S1"]):
    pins = {str(d): f"KS{d}" for d in range(10)}
    pins["A"] = "ANODE_" + nm
    part(f"V{i + 5}", "IN-17", "TS06_IN17_Socket", pins, DISP, "digits", f"{nm}; wire-ended, >= 6.4 mm off the board.")
part("V7", "INS-1", "TS06_INS1_Lamp", {1: "COLON_U", 2: "COLON_RET"}, DISP, "colon", "Upper colon neon.")
part("V8", "INS-1", "TS06_INS1_Lamp", {1: "COLON_L", 2: "COLON_RET"}, DISP, "colon", "Lower colon neon.")
for ref, val, pmap, anode, tag in (("V9", "IN-15B", M.IN15B_PAD, "ANODE_AM", "B"), ("V10", "IN-15A", M.IN15A_PAD, "ANODE_PM", "A")):
    pins = {pad: (None if g is None else (anode if g == "A" else f"CAT_{tag}_{g}")) for pad, g in pmap.items()}
    part(ref, val, "TS06_IN12_Socket", pins, DISP, "ampm", f"{val} on the ИН-12 socket; glyph map per bench gate 4.")
for i in range(8):
    part(f"HL{i + 1}", "amber 3mm", "TS06_LED_D3.0mm", {1: "BL_K", 2: f"BL_A{i + 1}"}, DISP, "backlight",
         "Backlight, addressable: anode from its own MCP23017 port-B pin, cathode on the common BL_K.")
part("HL9", "amber 3mm", "TS06_LED_D3.0mm", {1: "BL_K", 2: "M_A"}, DISP, "backlight",
     "The m of AM/PM behind its stencil: anode from D12, cathode on BL_K so it dims with the backlight.")

IN15B = {g: f"CAT_B_{g}" for g in M.IN15B_PAD.values() if g not in (None, "A")}
IN15A = {g: f"CAT_A_{g}" for g in M.IN15A_PAD.values() if g not in (None, "A")}

HEADERS = {
    # the left edge: the ИН-12 bus, one pin per strand, top to bottom in strand order
    "11": ["K6", "K5", "K7", "K4", "K8", "K3", "K9", "K2", "K0", "K1"],
    # the top edge, one 28-pin strip: the ИН-17 bundle, then ИН-15Б, then ИН-15А - every line on
    # it is a cathode line (<= 60 V: the К155ИД1 outputs clamp there)
    "12": ["KS7", "KS6", "KS5", "KS4", "KS3", "KS2", "KS1", "KS0", "KS9", "KS8"]
          + [IN15B[g] for g in ("AMP", "OHM", "SIEMENS", "VOLT", "HENRY", "HERTZ", "FARAD", "WATT")]
          + [IN15A[g] for g in ("NANO", "PCT", "PI", "KILO", "MEGA", "MILLI", "PLUS", "MINUS", "P", "MICRO")],
    # the bottom edge: anodes, LEDs and the colon, one short strip per pair of tubes
    "21": ["BL_K", "BL_A1", "ANODE_H10", "ANODE_H1", "BL_A2"],
    "22": ["COLON_U", "COLON_L", "COLON_RET"],
    "23": ["BL_A3", "ANODE_M10", "ANODE_M1", "BL_A4"],
    "24": ["BL_A5", "ANODE_S10", "ANODE_S1", "BL_A6"],
    # pin 3 sits under the "m" LED's cathode and is mechanical only: BL_K crosses on XS21 pin 1,
    # and a second BL_K pin would need its own 130 mm run on the driver board to be a connection
    "25": ["BL_A7", "ANODE_AM", None, "M_A", "ANODE_PM", "BL_A8"],
}
# On the display board the ИН-17 bundle is its own ten nets, KS0..KS9: it is not joined to the
# ИН-12 bus there, and naming it K0..K9 would leave KiCad reporting ten unrouted connections.
# The driver board carries K0..K9 to both strips from the one decoder.
def disp_net(k, n):
    return n


for k, pins in HEADERS.items():
    n = len(pins)
    part(f"XP{k}", f"PLS-{n} male 2.54", f"TS06_PinHeader_1x{n:02d}", {i + 1: disp_net(k, v) for i, v in enumerate(pins)}, DISP,
         "stack", "Board-to-board plug on the display board's back; mates XS%s." % k)
    part(f"XS{k}", f"PBS-{n} female 2.54", f"TS06_PinSocket_1x{n:02d}", {i + 1: v for i, v in enumerate(pins)}, DRV,
         "stack", "Board-to-board socket on the driver board's face towards the display; mates XP%s." % k)

# ======================================================================== DRIVER BOARD
# ---- power entry, 12 V
part("XS1", "DC 5.5x2.1", "TS06_BarrelJack_Horizontal", {1: "VIN_J", 2: "GND", 3: "GND"}, DRV, "power",
     "12 V barrel jack, centre positive. Pin 3 is the switch contact, grounded.")
part("F1", "PTC 1.1A", "TS06_Fuse_PTC_MF-RG1100", {1: "VIN_J", 2: "VIN_F"}, DRV, "power", "Resettable fuse.")
part("VD2", "1N5822", "TS06_D_DO-201AD_P15.24mm", {1: "+12V", 2: "VIN_F"}, DRV, "power",
     "Reverse-polarity protection, 3 A Schottky: 1 cathode, 2 anode.")
C("C8", "100u 25V", "+12V", "GND", CP, "power", "12 V bulk: the boost draws 1.3 A pulses at 31 kHz.")
C("C9", "1u 50V", "+12V", "GND", group="power")
part("U14", "R-78E5.0-1.0", "TS06_R-78E_SIP3", {1: "+12V", 2: "GND", 3: "+5V"}, DRV, "power",
     "Switching 5 V regulator, 78xx pinout. Feeds the whole 5 V rail, the Nano through its 5V pin.")
C("C10", "10u 25V", "+12V", "GND", group="power")
C("C11", "10u", "+5V", "GND", group="power")
C("C3", "10u", "+5V", "GND", group="power", note="5 V bulk by the Nano and the decoders.")

# ---- MCU
part("U1", "Arduino Nano", "TS06_Arduino_Nano", M.NANO, DRV, "mcu",
     "On two 1x15 female strips. Pin map is the firmware's (see the module docstring).")

# ---- the digit decoders: one for the ИН-12 bus (XS11), one for the ИН-17 pair (XS12 pins 1-10)
# WHY TWO. The display board delivers the two cathode groups in orders its tubes impose: the ИН-12
# bus arrives 6 5 7 4 8 3 9 2 0 1 down XS11, the ИН-17 bundle 7 6 5 4 3 2 1 0 9 8 along XS12.
# Feeding both from one К155ИД1 means a ten-line permutation between two strips, which two copper
# layers cannot make without vias. Two decoders on the same A0..A3 lines each fan out cleanly; the
# К155ИД1 is built to drive exactly this, and its inputs are two TTL loads per Nano pin (3.2 mA).
# THE DIGIT MAP is the board's, not the inherited one: code c lights output Q_c, and output Q_c is
# wired to digit DIGIT_Q.index(c). It is chosen so that U17's outputs rise straight into XS12 and
# U2's reach XS11 in two clean groups, one per face. The firmware carries it as BOARD_TYPE 4:
#     digitMask[] = {1, 0, 5, 4, 6, 7, 3, 2, 9, 8}      (digit d -> code)
DIGIT_MASK4 = [1, 0, 5, 4, 6, 7, 3, 2, 9, 8]
Q_TO_DIGIT4 = {c: DIGIT_MASK4.index(c) for c in range(10)}


def digit_decoder(ref, prefix, note):
    pins = {}
    for pin, fn in M.K155.items():
        if fn.startswith("Q"):
            pins[pin] = f"{prefix}{Q_TO_DIGIT4[int(fn[1])]}"
        elif fn == "VCC":
            pins[pin] = "+5V"
        elif fn == "GND":
            pins[pin] = "GND"
        else:
            pins[pin] = M.K155_INPUT[fn]
    return part(ref, "K155ID1", DIP16, pins, DRV, "decoder", note)


digit_decoder("U2", "K", "ИН-12 bus decoder -> XS11. Digit map BOARD_TYPE 4 (see DIGIT_MASK4).")
digit_decoder("U17", "KS", "ИН-17 pair decoder -> XS12 pins 1-10, same inputs and digit map as U2.")
C("C4", "100n", "+5V", "GND", group="decoder")
C("C17", "100n", "+5V", "GND", group="decoder")

# ---- the six anode channels
# Which Nano pin drives which anode is the pair's own, and the firmware's opts[] table for
# BOARD_TYPE 4 follows it ({KEY3, KEY2, KEY1, KEY0, KEY4, KEY5}, the order BOARD_TYPE 1 and 2
# already use). The Nano's digital row leaves the module D2..D11 west to east; with the hours'
# optos nearest the module and the minutes' and seconds' further west, the eastern pins must
# drive the nearer tubes or the lines cross on the one face they have (tools/mkpcb_drv.py).
TUBE_PIN4 = {"H10": "D6", "H1": "D5", "M10": "D4", "M1": "D3", "S10": "D2", "S1": "D13"}
for i, nm in enumerate(TUBES):
    u = f"U{i + 5}"
    part(u, "TLP627", DIP4, {1: "OPT_" + nm, 2: "GND", 3: "EMIT_" + nm, 4: "HV185"}, DRV, "anodes",
         f"Anode switch for {nm}: 1 LED anode, 2 LED cathode, 3 emitter, 4 collector.")
    R(f"R{21 + i}", "470R", TUBE_PIN4[nm], "OPT_" + nm, R_V if nm in ("M10", "M1", "S10", "S1") else
      "TS06_R_Axial_DIN0207_P10.16mm", group="anodes", note="Opto LED, ~8 mA.")
    R(f"R{27 + i}", M.ANODE_R[nm], "EMIT_" + nm, "ANODE_" + nm, R_HV, "anodes",
      "Anode series resistor, one per tube; TBC values wait for bench gate 2.")
    R(f"R{33 + 2 * i}", "510k DNP", "ANODE_" + nm, "BLEED_" + nm, R_V, "anodes",
      "Bleed pair, DNP unless the bench asks; ~92 V each, standing to keep the channel compact.")
    R(f"R{34 + 2 * i}", "510k DNP", "BLEED_" + nm, "GND", R_V, "anodes")

# Which LED each port-B bit lights - free for the firmware, chosen so the eight lines leave the
# network in the order the strips want them (tools/mkpcb_drv.py). GPBk lights HL{BL_OF_GPB[k]}.
BL_OF_GPB = [1, 2, 3, 4, 5, 6, 7, 8]

# ---- AM/PM: one expander, two decoders
MCP = {9: "+5V", 10: "GND", 11: None, 12: "SCL", 13: "SDA", 14: None, 15: "GND", 16: "GND", 17: "GND",
       18: "+5V", 19: None, 20: None}
for k in range(8):
    MCP[21 + k] = f"XA{k}"                  # GPA0..7: the two decoder nibbles
    MCP[1 + k] = f"XB{k}"                   # GPB0..7: the eight backlight LEDs
part("U3", "MCP23017-E/SP", DIP28, MCP, DRV, "ampm",
     "I2C expander at 0x20 (A0-A2 grounded), 300-mil SPDIP. GPA3..0 -> U15 (ИН-15Б), GPA7..4 -> U16 (ИН-15А), "
     "GPB0-7 -> backlight LEDs through RN1.")
C("C1", "100n", "+5V", "GND", group="ampm")
# The decoders' ten outputs are free to map to glyphs (the firmware keeps the table), so the map
# below is whatever lets the driver board's copper leave each decoder in the order the display
# board's header wants it. tools/mkpcb_drv.py sets GLYPH_Q; defaults here are output order.
GLYPH_Q = {   # output Q0..Q9 -> glyph; the firmware keeps the inverse table
    "U15": ["WATT", "FARAD", "AMP", "OHM", "HENRY", "HERTZ", "VOLT", "SIEMENS", None, None],
    "U16": ["MINUS", "PLUS", "NANO", "PCT", "MEGA", "MILLI", "KILO", "PI", "P", "MICRO"],
}
# Which MCP23017 port-A bit feeds which decoder input, again chosen for the copper:
# U16 (ИН-15А) takes GPA7..4 as A D B C, U15 (ИН-15Б) takes GPA3..0 as A D B C.
XA_IN = {"U16": {"A1": 7, "D8": 6, "B2": 5, "C4": 4}, "U15": {"A1": 3, "D8": 2, "B2": 1, "C4": 0}}


def _decoder(ref, nib, tag, table):
    pins = {}
    for pin, fn in M.K155.items():
        if fn.startswith("Q"):
            g = table[int(fn[1])]
            pins[pin] = f"CAT_{tag}_{g}" if g else None
        elif fn == "VCC":
            pins[pin] = "+5V"
        elif fn == "GND":
            pins[pin] = "GND"
        else:
            pins[pin] = f"XA{XA_IN[ref][fn]}"
    return pins


part("U15", "K155ID1", DIP16, _decoder("U15", 0, "B", GLYPH_Q["U15"]), DRV, "ampm",
     "ИН-15Б decoder, nibble on GPA3..0 per XA_IN. Codes 10-15 blank the tube.")
part("U16", "K155ID1", DIP16, _decoder("U16", 4, "A", GLYPH_Q["U16"]), DRV, "ampm",
     "ИН-15А decoder, nibble on GPA7..4 per XA_IN.")
C("C15", "100n", "+5V", "GND", group="ampm")
C("C16", "100n", "+5V", "GND", group="ampm")
R("R56", "8k2", "ANODE_AM", "HV185", R_HV, "ampm", "Static anode resistor, ИН-15Б (bench gate 2 checks it).")
R("R57", "8k2", "ANODE_PM", "HV185", R_HV, "ampm", "Static anode resistor, ИН-15А.")
R("R54", "4k7", "+5V", "SDA", R_V, group="ampm", note="I2C pull-ups.")
R("R55", "4k7", "+5V", "SCL", R_V, group="ampm")

# ---- backlight: eight addressable LEDs, one switch for brightness
# The eight current-limiting resistors are ONE part: an isolated 8 x 220R network in DIP-16
# (Bourns 4116R-1-221 class), resistor k between pins k and 17-k. It sits directly under the
# expander's port B, pin for pin, and is one placement instead of eight.
RN = {}
for k in range(8):
    RN[8 - k] = f"XB{k}"                    # the expander side: GPBk lands on pin 8-k, directly above it
    RN[9 + k] = f"BL_A{BL_OF_GPB[k]}"       # the LED side, pin 9+k, the other end of the same resistor
part("RN1", "8x220R isolated DIP-16", DIP16, RN, DRV, "backlight",
     "Isolated resistor network, 8 x 220R (4116R-1-221 class): GPBk -> pin 8-k, resistor to pin 9+k -> its LED.")
mpsa42("VT20", "B20", "BL_K", "backlight", "Common-cathode switch for all nine LEDs: D11's PWM is the brightness.")
R("R20", "470R", "D11", "B20", R_V, group="backlight")
R("R53", "220R", "D12", "M_A", R_V, group="backlight", note="The m LED, from D12. Standing: one of the four series resistors where the Nano's corridor lines end and change face (tools/mkpcb_drv.py).")

# ---- colon
R("R58", "220k", "HV185", "COLON_U", R_HV, "colon", "Own ballast per lamp, never shared (spec §3).")
R("R59", "220k", "HV185", "COLON_L", R_HV, "colon")
mpsa42("VT1", "B1", "COLON_RET", "colon", "Low-side switch for both lamps, PWM-faded from D10.")
R("R1", "10k", "D10", "B1", R_V, group="colon")

# ---- fascia and RTC
# J1's pin order is the fascia specification (1 +5V, 2 GND, 3 rotary ladder, 4 levers, 5 button -, 6 button +).
# On this board the rotary ladder (pin 3) reaches the Nano's A7 and the levers (pin 4) its A6: the two
# lines leave the Nano A7 west of A6 and arrive at J1 in that order, on a face they share with nothing
# they could cross. The firmware reads A6 and A7 for nothing yet; BOARD_TYPE 4 names the swap.
part("J1", "PH 6 vertical", "TS06_JST_PH_B6B-PH-K_Vertical", {1: "+5V", 2: "GND", 3: "A7", 4: "A6", 5: "D7", 6: "D8"},
     DRV, "fascia", "The panel cable; pin order is the specification both fascia builds share. Top entry, "
     "so the cable leaves towards the fascia.")
C("C5", "100n", "A6", "GND", group="fascia", note="Ladder filters at the board end (spec §2).")
C("C6", "100n", "A7", "GND", group="fascia")
part("U13", "DS3231 mini", "TS06_PinSocket_1x05", {1: "GND", 2: None, 3: "SCL", 4: "SDA", 5: "+5V"}, DRV, "rtc",
     "The small DS3231 module plugs in here, pin order - NC C D + as the stock board's RTC MINI header.")

# ---- 185 V converter, regulated (tools/ts06main.py has the reasoning)
part("L1", "220u 2A", "TS06_L_Radial_D12.0mm_P5.00mm", {1: "+12V", 2: "SW"}, DRV, "hv",
     "220 uH, Isat >= 1.8 A (1.3 A peaks at 12 V in, 23.8 us on).")
part("VT21", "IRF840", "TS06_TO-220-3_Vertical_HV", {1: "GATE", 2: "SW", 3: "GND"}, DRV, "hv",
     "500 V switch, G-D-S, standing. Pads narrowed for 0.94 mm drain clearance.")
part("VD1", "HER106 / UF4007", "TS06_D_DO-41_P10.16mm", {1: "HV185", 2: "SW"}, DRV, "hv", "Fast 600 V rectifier: 1 cathode, 2 anode.")
C("C7", "4u7 400V", "HV185", "GND", "TS06_CP_Radial_D10.0mm_P5.00mm", "hv", "The reservoir, 400 V.")
R("R60", "470k", "HV185", "BLEED_HV", R_HV, "hv", "Bleeder: the reservoir is safe ~10 s after power-off.")
R("R61", "470k", "BLEED_HV", "GND", R_HV, "hv")
R("R62", "750k 1%", "HV185", "FB_MID", R_HV, "hv", "Divider top, two in series, each under 100 V.")
R("R63", "750k 1%", "FB_MID", "FB", R_HV, "hv")
R("R64", "15k 1%", "FB", "FB_LOW", group="hv")
part("RP1", "10k", "TS06_Trimmer_3296W", {1: "FB_LOW", 2: "GND", 3: "GND"}, DRV, "hv",
     "Rail set-point 152-252 V; wiper on the grounded end, so an open wiper lowers the rail.")
part("U12", "LM393", DIP8, {1: "PWM_G", 2: "FB", 3: "VREF", 4: "GND", 5: "VREF", 6: "GND", 7: None, 8: "+5V"}, DRV, "hv",
     "Comparator: FB above VREF holds the driver input low. Second half parked.")
R("R69", "10k 1%", "+5V", "VREF", group="hv", note="2.5 V reference.")
R("R70", "10k 1%", "VREF", "GND", group="hv")
C("C14", "100n", "VREF", "GND", group="hv")
R("R65", "1M", "PWM_G", "VREF", group="hv", note="Hysteresis, about 1 V of rail.")
C("C13", "100n", "+5V", "GND", group="hv")
R("R66", "2k2", "D9", "PWM_G", R_V, group="hv")
R("R71", "10k", "PWM_G", "GND", group="hv")
part("U11", "TC4420", DIP8, {1: "+12V", 2: "PWM_G", 3: None, 4: "GND", 5: "GND", 6: "GATE_D", 7: "GATE_D", 8: "+12V"}, DRV, "hv",
     "Non-inverting MOSFET driver, 12 V out. MCP1407 is a drop-in.")
C("C12", "1u 50V", "+12V", "GND", group="hv")
R("R67", "10R", "GATE_D", "GATE", group="hv")
R("R68", "10k", "GATE", "GND", group="hv")

# ======================================================================== views
HV_PATTERNS = ["HV185", "SW", "BLEED_*", "FB_MID", "COLON_*", "ANODE_*", "EMIT_*"]
CATH_PATTERNS = ["KS*", "K0", "K1", "K2", "K3", "K4", "K5", "K6", "K7", "K8", "K9", "CAT_*"]


def parts(board):
    return {p.ref: p for p in PARTS if p.board == board}


def nets(board):
    out = {}
    for p in PARTS:
        if p.board != board:
            continue
        for pin, n in p.pins.items():
            if n:
                out.setdefault(n, []).append(f"{p.ref}.{pin}")
    return out


def check():
    bad = []
    for b in (DISP, DRV):
        for n, pads in nets(b).items():
            if len(pads) < 2:
                bad.append(f"{b}: net {n} has one pad ({pads[0]})")
    # every net that exists on both boards must cross on the headers, and nothing else may
    both = set(nets(DISP)) & set(nets(DRV))
    carried = {n for pins in HEADERS.values() for n in pins if n}
    for k, pins in HEADERS.items():         # the two halves of every strip carry the same signal
        for i, n in enumerate(pins):
            a, b = parts(DISP)[f"XP{k}"].pins[str(i + 1)], parts(DRV)[f"XS{k}"].pins[str(i + 1)]
            if a != disp_net(k, b):
                bad.append(f"XP{k}.{i + 1} is {a} but XS{k}.{i + 1} is {b}")
    for n in sorted(both - carried):
        bad.append(f"net {n} is on both boards but on no header pin")
    return bad


if __name__ == "__main__":
    for b in (DISP, DRV):
        ps, ns = parts(b), nets(b)
        print(f"{b}: {len(ps)} parts, {len(ns)} nets, {sum(len(v) for v in ns.values())} connected pins")
    print("header pins:", sum(len(v) for v in HEADERS.values()),
          " left + top", sum(len(HEADERS[k]) for k in ("11", "12")),
          " bottom", sum(len(HEADERS[k]) for k in ("21", "22", "23", "24", "25")))
    bad = check()
    print("\n".join("  [PAIR] " + x for x in bad) if bad else "netlist consistent")
    sys.exit(1 if bad else 0)
