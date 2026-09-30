#!/usr/bin/env python3
"""TS06-DRV: the driver board of the through-hole pair - everything that is not the display.

    python3 tools/mkpcb_drv.py             # PCB/TS06-DRV/TS06-DRV.kicad_pcb (+ .kicad_pro, copper.png)
    python3 tools/mkpcb_drv.py --route     # the same, routing afresh (tools/netroute.py) first
    python3 tools/mkpcb_drv.py --place     # placement only: PCB/TS06-DRV/placement.png

WHERE IT SITS. Behind TS06-DISP, parallel to it, on 11 mm standoffs: the display's male strips
(PLS, on its back) plug straight into this board's female strips (PBS) - no wires, the way
AlexGyver joins the two halves of his clock. The strips are on this board's BACK face, towards
the display; every other part is on the FRONT face, towards the back of the case, so nothing
taller than the strips lives in the 11 mm between the boards.

THE FRAME. Coordinates below are the DISPLAY board's frame seen from this board's component
side - the clock seen from behind - so a display x becomes 191.4 - x here, and y is the display's
y. This board's top edge is Y0 = 26 mm above the display's (pl() adds it). check_mate() proves
every socket pin lands on its header pin and every display standoff has its hole.

THE THREE BANDS, 191.4 x 100 in all:
  * the TOP BAND, above the display, carries what switches and what plugs in: the Nano across
    the top right corner, digital row facing down into the board and USB proud of the right
    edge (the clock's left side); the 12 V jack through the left edge; the fuse, the polarity
    diode and the 5 V regulator; the 185 V converter in one tight loop - inductor, switch,
    catch diode, reservoir - with its driver, comparator, divider and trimmer beside it; and
    the fascia connector next to the Nano pins it carries.
  * the TUBE BAND, behind the display: the four К155ИД1 under the top strip, their fans laid
    by hand; U2 beside the left strip; the six anode channels as three identical cells over
    the bottom strips (two stacked anode resistors ending straight over their pins, their
    optos standing above them, the 185 V feed running between); the colon ballasts; the AM/PM
    anode resistors.
  * the BOTTOM BAND, below the display: the MCP23017 with the LED resistor network stacked on
    its port B, so the eight addressable LED lines rise straight into a ribbon under the
    bottom strips.

ZERO VIAS, AND HOW. A through-hole pad is copper on both faces, so it is the only place a net
may change face; every other stretch of every net is on one face. The decoder fans are laid
by hand, one face each where they interleave; everything else is routed one net at a time by
tools/netroute.py, which never places a via, and its result is saved in mkpcb_drv_routes.json
so the board regenerates exactly without re-routing. The saved route is the source of truth:
--route pins PYTHONHASHSEED so a fresh route is repeatable, and TS06_ROUTES / TS06_OUT send a
trial route and board to scratch. --hand checks the hand-laid copper alone against the rules.
The generator exits non-zero if check() or check_mate() finds anything.

REV B (30.09.26), from the grills of rev A:
  * an over-voltage clamp independent of U12 and of the divider (VD5-VD7, R75, R76, VT2);
    a Schottky across U14 (VD3), a TVS after the fuse (VD4), the A6 pull-down and the button
    lines' RC at J1 (R72-R74, C18, C19);
  * IPC-2221B A6: every HV pad 0.8 mm from all other copper, pours included (Board.pad_rules,
    the router, TS06-DRV.kicad_dru); cathode pads 0.5 mm where routable (Board.soft_pad_rules);
  * 3.8 mm copper keep-outs round the eight standoff holes, as KiCad rule areas;
  * the 0.5 W resistors drawn for МЛТ-0,5 (15.24 mm, 1.1 mm holes, rows 5.0 mm apart), L1 the
    Bourns 5900-221-RC lying, VT21's holes 1.2 mm, J1's 0.85 mm, U13 on a male PLS-5;
  * the silkscreen legends (legends()), at the fab's 1.0 mm / 0.15 mm floor.
"""
import json, math, os, sys
if __name__ == "__main__" and "--route" in sys.argv and os.environ.get("PYTHONHASHSEED") != "0":
    # the router must give the same copper on every run: pin Python's string hashing, the one
    # thing that could reorder anything it iterates (red-team F6); the saved route stays the truth
    os.execvpe(sys.executable, [sys.executable] + sys.argv, dict(os.environ, PYTHONHASHSEED="0"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbkit as K
import ts06pair as P

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
NAME = "TS06-DRV"
OUT = os.environ.get("TS06_OUT") or os.path.join(ROOT, "PCB", NAME, NAME + ".kicad_pcb")
PLACE_ONLY = "--place" in sys.argv
REV, DATE = "B", "30.09.26"

W, H = 191.4, 100.0
DW = 191.4                                  # the display board's width: x here = DW - x there
# The tube row was re-spaced on 29.09.26: the ИН-17 pair from 13.0 to 20.5 apart (their Ø20 stems),
# the ИН-15 pair 15.4 mm right, the ИН-12s and the colon where they were. This board is the mirror
# image, so what sits behind the ИН-15 pair stays put, what sits behind the ИН-17 group moved SB
# and what sits behind the ИН-12s - with the Nano, U2 and the lines between them - moved SC.
SB, SC = 7.62, 15.4
Y0 = 26.0                                   # this board's top edge is 26 mm above the display's
YT, YB = 2.2 + Y0, 41.3 + Y0                # the strip rows, shared with TS06-DISP
CLASSES = [("HV", 0.6, 0.4, P.HV_PATTERNS_DRV),
           ("CATH", 0.25, 0.25, P.CATH_PATTERNS),
           ("PWR", 0.25, 0.5, ["+5V", "+12V", "VIN_J", "VIN_F", "GATE_D", "GATE"])]
B = K.Board(NAME, W, H, P.parts(P.DRV), CLASSES, default=("Default", 0.2, 0.25))
PT = P.parts(P.DRV)
# Rev B rules (grill E3, E10, F12):
#  * a bare HV pad keeps 0.8 mm (IPC-2221B table 6-1, A6, 171-250 V) from every other net's copper:
#    tracks, pads and the pours, both faces. Board.check() and the router hold it, and the project's
#    .kicad_dru gives it to KiCad's DRC and zone filler;
#  * a cathode pad (up to ~60 V off the К155ИД1) keeps 0.5 mm from other nets where the copper can
#    be routed so: the router holds it, check() reports what it could not (hand-laid entries);
#  * no copper, tracks or pour, within 3.8 mm of a standoff hole's centre: a 7 mm M3 washer reaches
#    3.5 mm and a 5.5 mm hex spacer's corners 3.18. Rule areas in the board make KiCad hold it too.
B.pad_rules = {"HV": 0.8}
B.soft_pad_rules = {"CATH": 0.5}
B.hole_ko = 3.8
B.min_text = (1.0, 0.15)                    # the fab's floor: 1.0 mm text, 0.15 mm stroke
B.dnp = {r for r, p in PT.items() if "DNP" in p.value}


def pl(ref, x, y, rot=0, back=False, fp=None):
    """Place a part at (x, y) in the DISPLAY board's frame (y shared with TS06-DISP, which
    starts Y0 below this board's top edge), on the footprint the netlist names."""
    return B.place(ref, fp or PT[ref].fp, x, y + Y0, rot, back)


LOW_W = {"GND": 0.15, "+5V": 0.3, "+12V": 0.5}   # rails are everywhere: they guide placement weakly


def near(ref, x0, y0, x1, y1, rots=(0, 90, 180, 270), keepout=()):
    """Place a small part in the free spot of a region (display frame) nearest its copper."""
    ko = [(a, b + Y0, c, d + Y0) for a, b, c, d in keepout]
    r = K.place_near(B, ref, PT[ref].fp, (x0, y0 + Y0, x1, y1 + Y0), rots, keepout=ko, weight=LOW_W)
    if r is None and os.environ.get("TS06_LOOSE"):         # exploring a placement: say so and go on
        print(f"  no room for {ref} in ({x0}, {y0})-({x1}, {y1})")
        return None
    assert r is not None, f"no room for {ref} in ({x0}, {y0})-({x1}, {y1})"
    return r


# ======================================================================== the strips (back face)
DISP_STRIP = {"11": (1.6, 4.4, True), "12": (107.35, 2.2, False), "21": (11.94, 41.3, False),
              "22": (47.99, 41.3, False), "23": (69.28, 41.3, False), "24": (115.115, 41.3, False),
              "25": (154.55, 41.3, False)}


def socket(k):
    x, y, vertical = DISP_STRIP[k]
    n = len(P.HEADERS[k])
    pl(f"XS{k}", DW - x, y, rot=0 if vertical else 90, back=True)
    return [B.P(f"XS{k}", i + 1) for i in range(n)]


XS = {k: socket(k) for k in DISP_STRIP}

# Standoffs: the display's four, mirrored; two more at the bottom corners and two along the top.
HOLES = [(W - 3.5, 40.5), (3.5, 40.5), (DW - 50.535, 3.3), (3.5, 7.5),
         (3.5, 70.5), (W - 3.5, 70.5), (3.5, -22.5), (W - 3.5, -3.5)]
for i, (hx, hy) in enumerate(HOLES):
    B.place(f"H{i + 1}", "TS06_MountingHole_M3", hx, hy + Y0)
    B.holes.append((hx, hy + Y0, 3.2))
    # the keep-out as a KiCad rule area on both faces: no track and no pour within 3.8 mm (pads are
    # checked by Board.check(): an area that forbids pads would forbid the hole itself)
    # (a 32-gon circumscribing the circle, so the circle is inside it)
    rk = B.hole_ko / math.cos(math.pi / 32)
    B.rule_areas.append(dict(name=f"H{i + 1} keep-out", pads=True,
                             poly=[(round(hx + rk * math.cos(k * math.pi / 16), 3), round(hy + Y0 + rk * math.sin(k * math.pi / 16), 3))
                                   for k in range(32)]))

# ======================================================================== the tube band
# The decoders under the top strip, pins 16..9 facing it; U2 turned over beside XS11.
DEC_Y = 15.62 + Y0
pl("U16", 12.93, 15.62, rot=90)
pl("U15", 35.25, 15.62, rot=90)
pl("U17", 58.65 + SB, 15.62, rot=90)
pl("U2", 166.2 + SC, 27.26, rot=180)

# The anode channel cells. Each pair of anode pins gets its two series resistors, each ending
# straight over its pin, and its two optos standing above them, emitter pin over the resistor it
# feeds; the 185 V feed runs between the optos and the resistors.
# Rev B: the resistors are drawn for МЛТ-0,5 (Ø4.2 x 10.8 mm, 15.24 mm between holes). The seconds'
# cell, with room on both sides, lays its two resistors in ONE row, back to back from their two
# pins; the minutes' and hours' cells keep two rows, now 5.0 mm apart, both running west, and their
# optos rise 1.4 mm to make that room. The minutes' cell leaves the room east of it to the colon.
Y_R, Y3 = 37.6, 30.3                        # a one-row cell: its resistors, its optos' output row
Y_U, Y_L, Y3H = 32.9, 37.9, 28.9            # a two-row cell's rows and its optos' output row
RP = 15.24                                  # the resistors' pitch


def cell_row(xl, r_left, r_right, o_left, o_right):
    """One row: the resistor on the left pin runs left, the one on the right pin runs right, and
    each one's opto stands over its far end, emitter (pin 3) straight above the pad it feeds."""
    xr = xl + 2.54
    pl(r_left, xl - RP, Y_R)                # pad 1 (emitter) RP west, pad 2 (anode) on the left pin
    pl(r_right, xr + RP, Y_R, rot=180)      # pad 1 RP east, pad 2 on the right pin
    pl(o_left, xl - RP + 2.54, Y3 - 7.62, rot=270)
    pl(o_right, xr + RP + 2.54, Y3 - 7.62, rot=270)


def cell_stack(xl, r_up, r_lo, o_up, o_lo, ox_up, ox_lo):
    """Two rows, both resistors running left from their pins, the upper row 5.0 mm above."""
    xr = xl + 2.54
    pl(r_up, xr - RP, Y_U)
    pl(r_lo, xl - RP, Y_L)
    pl(o_up, ox_up, Y3H - 7.62, rot=270)
    pl(o_lo, ox_lo, Y3H - 7.62, rot=270)


cell_row(63.585 + SB, "R32", "R31", "U10", "U9")         # S1 (left pin) / S10 (right pin)
XM = 101.64 + SC + 2.54                     # the minutes' right pin (M10)
cell_stack(101.64 + SC, "R29", "R30", "U7", "U8", XM - 12.7, XM - 18.5)            # M10 / M1
# the hours' optos stay where the Nano's D5 / D6 resistors stand over them
cell_stack(156.44 + SC, "R27", "R28", "U5", "U6", 174.38 - 10.16, 174.38 - 15.9)   # H10 / H1

# The colon: one ballast per lamp standing over its pin, 5.0 mm apart, the return switch beside
# them and the reservoir's bleeder (R60 / R61) above it, in the room the minutes' cell leaves.
XC = DW - 47.99                             # XS22 pin 1 (COLON_U); pin 2 is 2.54 west
pl("R59", XC - 3.54, 22.0, rot=270)                      # COLON_L, over XS22.2 (1 mm west: the column's room)
pl("R58", XC + 1.46, 22.0, rot=270)                      # COLON_U
pl("VT1", XC - 8.71, 33.0, rot=270)
pl("R60", XC - 22.51, 23.1)
pl("R61", XC - 22.51, 28.1)

# The AM/PM static anode resistors: each from its pin east, in two rows 5.0 mm apart.
pl("R56", 34.31, Y_L)
pl("R57", 26.69, Y_U)

# ======================================================================== the top band
# The Nano lies across the top right corner, its digital row facing down into the board and its
# USB 2.4 mm proud of the right edge (the clock's left side, seen from the front).
pl("U1", 136.24 + SC, -8.73, rot=90)

# The 12 V inlet at the top left, jack mouth through the left edge, then fuse, polarity diode
# and the 5 V regulator, in the order the current takes them.
pl("XS1", 14.0, -13.50)
pl("F1", 24.0, -23.30)
pl("VD2", 36.24, -17.00, rot=180)
pl("U14", 21.5, -6.50)
pl("C8", 40.5, -22.20)
# Rev B: the Schottky across U14 (E5), under it, anode straight below its output pin; and the
# TVS after the fuse (E8), along the band's foot beside it, cathode (VIN_F) towards the fuse.
pl("VD3", 26.58 - 10.16, -2.5)
pl("VD4", 36.5, -2.3)

# The 185 V converter: inductor, switch, catch diode, reservoir in one tight loop; the gate
# driver beside the switch; the comparator, divider and trimmer beside the driver.
# Rev B: L1 is the Bourns 5900 axial choke, lying along the top edge; the switch stands under
# its SW end with the driver to its left, and the diode and reservoir close the loop to its right.
pl("L1", 46.5, -19.6)
pl("VT21", 71.9, -9.5)
pl("VD1", 86.5, -4.5, rot=180)
pl("C7", 87.5, -12.5, rot=180)
pl("U11", 57.0, -11.2)
# The control block, laid out by hand: the divider comes down from the 185 V side on the left
# (R62), turns at FB_MID (R63 standing), and FB meets the comparator's input pin, the 18k and
# the trimmer on the right; the 2.5 V reference divider and the output pull-down stand beside the
# comparator, and the independent over-voltage clamp (rev B) stands in its own block to the east.
pl("U12", 107.0, -3.5, rot=180)
pl("R62", 92.0, -23.4)
pl("R63", 111.0, -23.4, rot=270)
pl("R64", 111.0, -4.0)
pl("RP1", 124.5, -8.3)
# The clamp: the zener string zig-zags down from the 185 V end, then the base resistor, the
# transistor and its base-emitter resistor next to where PWM_G passes on its way to the driver.
ZX = 128.2
pl("VD5", ZX, -23.2)
pl("VD6", ZX + 10.16, -19.2, rot=180)
pl("VD7", ZX, -15.2)
pl("R75", ZX + 10.16, -11.2, rot=180)

# ======================================================================== where lines change face
# A through-hole pad is copper on both faces, so a series resistor is the one "via" a zero-via
# board has. The Nano's lines are placed so that each one changes face at its own resistor, where
# it has to cross something:
#  * the four lines that come down the corridor beside the Nano (D9 the converter's PWM, D10 the
#    colon, D12 the "m" LED, D13 the S1 opto) end in four standing resistors at the corridor's exit,
#    and what leaves them (PWM_G north to the control block, the rest south) is on the front face;
#  * the minutes' and S10's opto resistors stand under the Nano's west end, where D2-D4 come
#    west to them; their outputs drop down that side and run west in lanes under the resistors
#    at the corridor's exit;
#  * the hours' opto resistors lie straight above their optos, D5 and D6 coming west to them.
HOP_Y = 41.9                                # pad 1 of the corridor-exit resistors (DRV frame)
for ref, x in (("R66", 126.0), ("R1", 122.5), ("R53", 119.0), ("R26", 115.5)):
    pl(ref, x + SC, HOP_Y - Y0, rot=270)
for ref, x, y in (("R25", 134.6, 24.0), ("R24", 137.6, 24.0), ("R23", 140.6, 24.0)):
    pl(ref, x + SC, y - Y0, rot=270)
pl("R22", 143.1 + SC, 34.0 - Y0, rot=270)        # H1 (rev B: 1.3 mm up with the hours' optos)
pl("R21", 148.8 + SC, 34.0 - Y0, rot=270)        # H10

# ======================================================================== the bottom band
# The expander and the LED network, stacked: port B straight up into the network, the network
# straight up into the LED corridor under the bottom strips; port A leaves downwards and runs
# up the left edge to the two ИН-15 decoders.
pl("U3", 44.5, 60.0, rot=270)
pl("RN1", 26.72, 56.0, rot=90)
# The fascia cable plugs in at the bottom edge on the face towards the display, which is the
# face the fascia sits in front of: the cable goes straight forward, not round the stack.
pl("J1", 122.0 + SC, 69.0, rot=180, back=True)
# The fascia's ladder filters and the I2C pull-ups in one column between the colon's ballasts and the
# hours' cell. A7, A6, SCL and SDA come west through the hours' optos on the front face, in that
# order top to bottom, and each ends in its own part in the same order; they leave on the back face,
# the filters' lines down the column's right side to J1, the pull-ups' lines west to the clock module.
HOP_X = 136.4 + SC                          # the column's signal pads; rev B: 1 mm west, so that two lines
# pass down its east side and still keep 0.8 mm from U6's emitter pin (IPC A6)
pl("C6", HOP_X, 48.0 - Y0, rot=180)         # A7: pad 1, the signal, on the right
pl("C5", HOP_X, 50.5 - Y0, rot=180)         # A6
pl("R55", HOP_X - 2.54, 53.1 - Y0)          # SCL: pad 2, the signal, on the right
pl("R54", HOP_X - 2.54, 56.1 - Y0)          # SDA
# The clock module, turned so that SCL is above SDA as the two lines arrive from the column.
pl("U13", 115.83 + SC, 74.27 - Y0, rot=270)
# U2's decoupling capacitor beside the chip's left column, fed from its 5 V pin through the gap above
# pin 12, below where the A0-A3 lines reach U2 and clear of the lines going down the gap.
pl("C4", 155.5 + SC, 48.5 - Y0, rot=270)

# ======================================================================== the small parts
# Each goes to the free spot of its region nearest the pads it connects to (pcbkit.place_near).
FANS = (5.0, -0.6, 80.5 + SB, 17.3)             # the hand-laid decoder fans: no part over them
XALANES = (5.0, 17.0, 51.8, 21.3)          # port A's lanes under the two ИН-15 decoders
XALEFT = (4.5, 17.0, 11.2, 74.0)           # ... up the left edge
XABOT = (5.0, 68.4, 46.5, 74.0)            # ... and under the expander
BLRIB = (20.0, 42.0, 166.0 + SC, 45.9)          # the LED ribbon under the bottom strips
GAP = (150.0 + SC, -1.0, 157.5 + SC, 30.0)           # between the hours' cell and U2: the Nano's lines go south
PLAZA = (132.5 + SC, -5.0, 157.5 + SC, 21.0)         # under the Nano: its lines fan out here
OPTLANES = (52.0 + SB, 19.2, 136.0 + SC, 21.6)       # D2-D4's anode lines run west under the corridor's exit
XAFAN = (5.0, 17.0, 52.0, 30.5)            # port A's lines rise up the left edge into U16 / U15
NECK = (78.0 + SB, -1.0, 157.5 + SC, 21.0)           # the Nano's lines come down through here
for r in ("C9", "C10", "C11"):
    near(r, 14.0, -25.5, 56.0, -0.8)
for r in ("R67", "R68", "C12"):             # the gate resistors and the driver's decoupling
    near(r, 30.0, -13.2, 79.0, -0.8)
for r in ("VT2", "R76"):                    # the clamp's transistor
    near(r, 108.0, -25.5, 143.0, -1.0)
for r in ("R69", "R70", "C14", "R71", "R65", "C13"):     # reference, hysteresis, pull-down
    near(r, 88.5, -21.2, 126.0, -1.0)
near("C3", 88.5, -25.5, 143.0, -1.0)             # 5 V bulk, towards the Nano
for r in ("C15", "C16"):
    near(r, 8.0, 21.4, 46.0, 25.5, rots=(0,), keepout=(XALANES,))
near("C17", 58.0 + SB, 21.7, 80.0 + SB, 26.5, rots=(0,), keepout=(OPTLANES,))
for r in ("VT20", "R20"):                    # the backlight switch, under U2 beside XS21's BL_K pin
    near(r, 161.0 + SC, 28.8, 170.5 + SC, 40.2, keepout=(BLRIB,))
for r in ("R33", "R34", "R35", "R36"):
    near(r, 152.0 + SC, 44.0, 176.0 + SC, 74.0, keepout=(BLRIB,))
for r in ("R37", "R38", "R39", "R40", "R41", "R42", "R43", "R44"):
    near(r, 45.0, 17.4, 157.0 + SC, 40.0, keepout=(XAFAN, NECK, GAP, PLAZA, OPTLANES))
near("C1", 10.0, 44.5, 26.0, 57.5, keepout=(XALEFT, XABOT, BLRIB))   # the expander's own decoupling
# Rev B (E11): the A6 pull-down and the button lines' 1k + 10 nF, between the strips and J1, each part
# on its own net's way into J1 and none across another's (recovered/drv-revb/OPTIONS.md: placed by
# near(), they fenced the funnel into J1 and the route stalled). Every line from the column or the
# gap crosses the strip band on the back face (the LED ribbon's BL_A1/BL_A2 hold the front), then
# fans into J1 in its pin order, A6 A7 D7_J D8_J west to east:
#  * D7 and D8 come down the gap east of the funnel into R73 and R74, lying east-west, one above the
#    other; D7_J and D8_J leave their west pads, past C18 and C19 standing below them, for J1's two
#    east pins;
#  * R72 lies east-west under the corridor, its A6 pad on A6's way down to J1 and its ground pad
#    west of the funnel, towards the clock module's ground pin.
pl("R73", 167.0, 80.0 - Y0, rot=180)        # pad 1 (D7) east, pad 2 (D7_J) 10.16 west
pl("R74", 169.5, 83.0 - Y0, rot=180)        # D8 passes east of R73's pad 1
pl("C18", 156.84, 83.0 - Y0, rot=270)       # pad 1 (D7_J) under R73's pad 2, ground below it
pl("C19", 159.34, 86.0 - Y0, rot=270)       # pad 1 (D8_J) under R74's pad 2
pl("R72", 148.0, 74.0 - Y0, rot=180)        # pad 1 (A6) east, pad 2 (GND) west

# ======================================================================== hand-laid copper
# The decoder fans, laid the way a person lays them: every line a straight rise, a 45 degree
# shift of one or two pitches, or a wrap round the end of the chip.
LV = 0.25                                   # cathode-line width


def T(net, layer, *pts, w=LV):
    B.track(net, layer, list(pts), w)


def rise(net, layer, pad, x_to, y_top=YT, bend=None, end=0.0):
    """From a decoder's top-row pad straight up, then 45 degrees across to the strip pin (landing
    `end` mm short of it and going in straight, where the pin beside is a square pad)."""
    x, y = pad
    dx = x_to - x
    if abs(dx) < 1e-6:
        T(net, layer, (x, y), (x, y_top))
        return
    if bend is not None:
        T(net, layer, (x, y), (x, bend), (x_to, y_top))
        return
    yb = y_top + end + abs(dx)
    T(net, layer, (x, y), (x, yb), (x_to, yb - abs(dx)), (x_to, y_top))


def P_(ref, pin):
    return B.P(ref, pin)


XS12 = {n: B.P("XS12", int(k)) for k, n in PT["XS12"].pins.items() if n}      # pins 11-13 are spare

# U16 (ИН-15А), back face.
for pin in (16, 15, 14, 13, 11, 10, 9):
    n = PT["U16"].pins[str(pin)]
    rise(n, "B.Cu", P_("U16", pin), XS12[n][0])
T("CAT_A_NANO", "B.Cu", P_("U16", 8), (32.0, DEC_Y - 1.29), (32.0, YT + 1.29), XS12["CAT_A_NANO"])
T("CAT_A_P", "B.Cu", P_("U16", 1), (10.39, DEC_Y - 2.54), XS12["CAT_A_P"])
# rev B: the wraps round pin 1 of U16 and U17 pass 1.43 below the row (was 1.27): 0.5 mm from the pin (E10)
T("CAT_A_MICRO", "B.Cu", P_("U16", 2), (14.04, DEC_Y + 1.43), (9.28, DEC_Y + 1.43), (7.85, DEC_Y), XS12["CAT_A_MICRO"])

# U15 (ИН-15Б), front face; AMP wraps the chip's right end.
for pin in (16, 15, 14, 13):
    n = PT["U15"].pins[str(pin)]
    rise(n, "F.Cu", P_("U15", pin), XS12[n][0], bend=YT + 2.0)
for pin in (11, 10, 9):
    n = PT["U15"].pins[str(pin)]
    rise(n, "F.Cu", P_("U15", pin), XS12[n][0])
T("CAT_B_AMP", "F.Cu", P_("U15", 8), (55.0, DEC_Y), (55.0, YT + 4.0), XS12["CAT_B_AMP"])

# U17 (ИН-17 pair), back face except KS0, which crosses KS1 on the front, and KS7, which wraps the
# chip's right end on the front so that the A0-A3 bus can enter between its rows on the back.
for pin in (14, 13, 11, 10, 9, 16):
    n = PT["U17"].pins[str(pin)]
    rise(n, "B.Cu", P_("U17", pin), XS12[n][0], end=0.35 if n == "KS6" else 0.0)   # KS6 passes XS12.1's square pad
rise("KS0", "F.Cu", P_("U17", 15), XS12["KS0"][0])
T("KS7", "F.Cu", P_("U17", 8), (78.97 + SB, DEC_Y - 2.54), (78.97 + SB, YT + 2.54), XS12["KS7"])
T("KS9", "B.Cu", P_("U17", 1), (56.11 + SB, DEC_Y - 2.54), XS12["KS9"])
T("KS8", "B.Cu", P_("U17", 2), (59.76 + SB, DEC_Y + 1.43), (54.9 + SB, DEC_Y + 1.43), (54.9 + SB, YT + 1.33), XS12["KS8"])

# U2 (ИН-12 bus), beside XS11. The column facing the strip (K7 K8 K9) goes straight across on the
# front; the far column threads through the chip on the back, each line through the gap above
# its own pin, and lands on the strip in order.
XS11 = {PT["XS11"].pins[str(i + 1)]: B.P("XS11", i + 1) for i in range(10)}
T("K7", "F.Cu", P_("U2", 8), XS11["K7"])
T("K8", "F.Cu", P_("U2", 2), (169.3 + SC, P_("U2", 2)[1]), (169.3 + SC, XS11["K3"][1]), (171.84 + SC, XS11["K8"][1]), XS11["K8"])
T("K9", "F.Cu", P_("U2", 1), (171.8 + SC, P_("U2", 1)[1]), (171.8 + SC, XS11["K2"][1] + 0.06), XS11["K9"])
X_DIAG = 172.6 + SC                         # where each back-face line finishes its 45 degree run
for pin in (9, 10, 11, 13, 14, 15, 16):
    n = PT["U2"].pins[str(pin)]
    px, py = P_("U2", pin)
    tx, ty = XS11[n]
    if pin == 9:                            # K6 passes over the top of the facing column
        gy = P_("U2", 8)[1] - 1.52
        T(n, "B.Cu", (px, py), (px + py - gy, gy), (X_DIAG - abs(ty - gy), gy), (X_DIAG, ty), (tx, ty))
    else:                                   # the rest through the gap above their own pin
        gy = py - 1.27
        T(n, "B.Cu", (px, py), (px + 1.27, gy), (X_DIAG - abs(ty - gy), gy), (X_DIAG, ty), (tx, ty))

# The Nano's escape. Its far row (the analogue side: A0-A3, I2C, A6/A7, 5 V) drops through the
# gaps of its near row on the FRONT face; its near row (the digital pins) drops on the BACK face.
# The lines that head left - the U17 branch of A0-A3, D12, D13 - run in lanes under the module on
# the back face and leave past its end. The same A0-A3 pads are where the bus splits in two
# (front to U2, back to U17): a through-hole pad is the layer change. The router starts from the
# ends of these stubs; the module area itself is kept out of its reach.
yA, yB = P_("U1", 1)[1], P_("U1", 30)[1]
Y_END = yA + 3.5
X_EXIT = P_("U1", 1)[0] - 3.0
W_RAIL = 0.3
for pin in (29, 27, 22, 21, 20, 19):
    n = PT["U1"].pins[str(pin)]
    x, y = P_("U1", pin)
    T(n, "F.Cu", (x, y), (x + 1.27, y + 1.27), (x + 1.27, Y_END), w=W_RAIL if n in ("GND", "+5V") else LV)
x, y = P_("U1", 4)                          # the digital row's GND joins the analogue row's on the front
xg = P_("U1", 29)[0] + 1.27
T("GND", "F.Cu", (x, y), (x, y + 2.0), (xg, y + 2.0), w=W_RAIL)

# The digital row fans out on the back face in lanes just below the module, each line on its own
# level, the westernmost pin on the top lane: D2-D4 west to the minutes' and S10's resistors standing
# under the module's end, D5 and D6 to the hours' resistors above their optos, D7, D8 and D11 down
# the gap between the hours' cell and U2 (D7 and D8 to J1, D11 to the backlight switch under U2).
def fan(n, x, y, lane, x_to, y_to, jog=None):
    pts = [(x, y)]
    if jog:                                 # step west under the next pin first (a standoff below)
        pts += [(x, y + jog[1]), (x - jog[0], y + jog[1])]
        x -= jog[0]
    T(n, "B.Cu", *pts, (x, lane - 0.5), (x - 0.5, lane), (x_to + 0.5, lane), (x_to, lane + 0.5), (x_to, y_to))


for pin, lane, ref in ((5, 21.6, "R25"), (6, 22.25, "R24"), (7, 22.9, "R23"), (8, 24.1, "R22"), (9, 24.75, "R21")):
    n = PT["U1"].pins[str(pin)]
    x, y = P_("U1", pin)
    fan(n, x, y, lane, *P_(ref, 1))
GAP_X, GAP_Y = 152.4 + SC, 44.0                  # the gap's first line (D7) and where the router takes over
for k, (pin, lane) in enumerate(((10, 25.9), (11, 26.55), (14, 27.2))):
    n = PT["U1"].pins[str(pin)]
    x, y = P_("U1", pin)
    # D11's pin is over H8's keep-out (rev B, F12): it steps west under D10's pin before it drops
    fan(n, x, y, lane, GAP_X + 0.6 * k, GAP_Y, jog=(3.2, 1.2) if n == "D11" else None)

# The analogue row's A6, A7, SCL and SDA drop through the digital row's gaps on the front face, close
# up into four lanes down the same gap, and turn west through the hours' optos - between each opto's
# two rows of pins - to the column of their filters and pull-ups (HOP_X), where they change face.
F_GAP = tuple(x + SC for x in (149.95, 150.55, 151.15, 151.75))    # A7 A6 SCL SDA down the gap
F_LANE = (50.5, 51.1, 51.7, 52.3)           # ... and west between the optos' pin rows
for k, (pin, jog) in enumerate(((26, 26.0), (25, 25.0), (24, 25.5), (23, 24.5))):
    n = PT["U1"].pins[str(pin)]
    x, y = P_("U1", pin)
    xs, xg, yl = x + 1.27, F_GAP[k], F_LANE[k]
    dx = xg - xs
    pts = [(x, y), (xs, y + 1.27), (xs, jog), (xg, jog + abs(dx)), (xg, yl - 0.6), (xg - 0.6, yl)]
    pad = P_({"A7": "C6", "A6": "C5", "SCL": "R55", "SDA": "R54"}[n], 1 if n in ("A7", "A6") else 2)
    if n == "A7":                           # up to the column's top part
        pts += [(pad[0] + (yl - pad[1]), yl), pad]
    elif n == "A6":
        pts += [(pad[0] + 0.6 + (yl - pad[1]), yl), (pad[0] + 0.6, pad[1]), pad]
    elif n == "SCL":
        pts += [(pad[0] + 0.8, yl), (pad[0], yl + 0.8), pad]      # rev B: a short 45, clear of SDA's turn
    else:                                   # SDA, the lowest, turns down first
        xt = HOP_X + 1.4                    # rev B: 0.8 mm from U6's emitter pin (IPC A6)
        pts += [(xt, yl), (xt, pad[1] - (xt - pad[0])), pad]
    T(n, "F.Cu", *pts)

# The U17 branch of A0-A3, with D13, D12, D10 and D9 beside it, leaves under the module, turns down the
# corridor between the module and the control block, and runs west to U17, entering the chip
# between its rows from the right: every line then drops into its own input pin from above,
# and the order the Nano's pins give the bus is exactly the order U17's pins want - which is
# why this bus goes INTO the chip rather than under it (from below it would arrive mirrored).
# D9, D10, D12 and D13 come down the corridor on the bus's outside and end in their series resistors
# at its exit (HOP), where they change face.
HOP = {"D9": "R66", "D10": "R1", "D12": "R53", "D13": "R26"}   # where the corridor's other lines end
X_COR = 129.5 + SC                          # the corridor's first line (A3); rev B: east of H3's 3.8 mm keep-out
PITCH = 0.5                                 # rev B: 0.5 (0.25 mm gaps), so the eight lines still clear R25
Y_RUN = 36.5                                # A3's lane between U17's rows
for k, (pin, dy) in enumerate(((22, 1.9), (21, 2.5), (20, 3.1), (19, 3.7), (16, 4.3))):
    n = PT["U1"].pins[str(pin)]
    x, y = P_("U1", pin)
    xc, yl = X_COR + k * PITCH, y + dy
    if n == "D13":                          # down the corridor and west, outside the A0-A3 bus
        yw = Y_RUN + k * PITCH
        hx, hy = P_(HOP[n], 1)
        T(n, "B.Cu", (x, y), (x, yl), (xc + 1.0, yl), (xc, yl + 1.0), (xc, yw - 1.0), (xc - 1.0, yw),
          (hx + 0.5, yw), (hx, yw + 0.5), (hx, hy))
        continue
    yw = Y_RUN + k * PITCH
    xd, yd = P_("U17", {"A0": 7, "A1": 6, "A2": 4, "A3": 3}[n])
    T(n, "B.Cu", (x, y), (x, yl), (xc + 1.0, yl), (xc, yl + 1.0), (xc, yw - 1.0), (xc - 1.0, yw),
      (xd + 0.5, yw), (xd, yw + 0.5), (xd, yd))
for k, (pin, dy) in ((5, (15, 3.2)), (6, (13, 2.65)), (7, (12, 2.1))):   # D12, D10, D9 from the near row
    n = PT["U1"].pins[str(pin)]
    x, y = P_("U1", pin)
    xc, yl, yw = X_COR + k * PITCH, y - dy, Y_RUN + k * PITCH
    hx, hy = P_(HOP[n], 1)
    T(n, "B.Cu", (x, y), (x, yl), (xc + 1.0, yl), (xc, yl + 1.0), (xc, yw - 1.0), (xc - 1.0, yw),
      (hx + 0.5, yw), (hx, yw + 0.5), (hx, hy))
B.keepouts.append((X_EXIT + 0.5, 0.0, W, Y_END - 0.3, "*"))

# U2's inputs thread the chip on the front face to its far side; its 5 V leaves the far side on the
# back face through the gap above pin 12 and runs down beside the chip into C4.
x_l = P_("U2", 16)[0]
for pin in (7, 6, 4, 3):
    n = PT["U2"].pins[str(pin)]
    x, y = P_("U2", pin)
    T(n, "F.Cu", (x, y), (x - 1.27, y - 1.27), (x_l - 1.58, y - 1.27))
x, y = P_("U2", 5)
c1 = P_("C4", 1)
T("+5V", "B.Cu", (x, y), (x - 1.27, y - 1.27), (c1[0] + 0.55, y - 1.27), (c1[0], y - 0.72), c1, w=W_RAIL)
c = B.court("U2")
B.keepouts.append((x_l + 0.2, c[1], W, c[3], "*"))           # U2's body and its channel to XS11

# Port A of the expander to the two ИН-15 decoders: out of the bottom of U3, west under it, up the
# left edge and east under the decoders, eight lines side by side on the back face. In every bend
# the inner line is the one that turns first, so the bus never crosses itself, and it arrives in
# the order the decoder pins want. The decoders' 5 V pins cross it on the front face.
XA_DEST = {7: ("U16", 3), 6: ("U16", 4), 5: ("U16", 6), 4: ("U16", 7),
           3: ("U15", 3), 2: ("U15", 4), 1: ("U15", 6), 0: ("U15", 7)}
XA_P, XA_BOT, XA_LEFT, XA_TOP = 0.41, 95.0, 10.3, 43.6    # rev B: the bus 1.3 mm in and 0.28 mm tighter,
# clear of H2 and H5's 3.8 mm keep-outs on the left and of U3's end pins on the right
BUS_W = 0.2                                 # 0.41 pitch leaves 0.21 mm
for i in range(8):
    x, y = P_("U3", 21 + i)
    yb, xl, yt = XA_BOT + i * XA_P, XA_LEFT - i * XA_P, XA_TOP + (7 - i) * XA_P
    xd, yd = P_(*XA_DEST[i])
    T(f"XA{i}", "B.Cu", (x, y), (x, yb - 0.5), (x - 0.5, yb), (xl + 1.0, yb), (xl, yb - 1.0),
      (xl, yt + 1.0), (xl + 1.0, yt), (xd - 0.5, yt), (xd, yt - 0.5), (xd, yd), w=BUS_W)

# Port B straight up into the LED network.
for i in range(8):
    T(f"XB{i}", "B.Cu", P_("U3", 1 + i), P_("RN1", 8 - i))

# The LED ribbon: from the network's far row up into lanes under the bottom strips and along them
# each line peeling off up into its strip pin - the nearest pin on the top lane.
# BL_A8 is a short diagonal to its pin beside the network; BL_A7 crosses the ribbon on the front.
BL_DEST = {1: ("XS21", 2), 2: ("XS21", 5), 3: ("XS23", 1), 4: ("XS23", 4), 5: ("XS24", 1), 6: ("XS24", 4)}
BL_Y = 69.1                                 # rev B: 0.1 mm lower, 0.8 mm from the anode pins above (IPC A6)
for k, i in enumerate((6, 5, 4, 3, 2, 1)):
    x, y = P_("RN1", 8 + i)
    yl = BL_Y + k * XA_P
    xd, yd = P_(*BL_DEST[i])
    # the two lines that reach the hours' strip run on the front face, so that east of the minutes'
    # strip the back face under the strips is free for the lines that must cross down to J1
    T(f"BL_A{i}", "F.Cu" if i in (1, 2) else "B.Cu", (x, y), (x, yl + 0.5), (x + 0.5, yl), (xd - 0.5, yl),
      (xd, yl - 0.5), (xd, yd), w=BUS_W)
x, y = P_("RN1", 16)
xd, yd = P_("XS25", 6)
T("BL_A8", "B.Cu", (x, y), (x, yd + (x - xd)), (xd, yd), w=BUS_W)
x, y = P_("RN1", 15)
xd, yd = P_("XS25", 1)
T("BL_A7", "F.Cu", (x, y), (x + 2.1, y - 2.1), (xd - 2.3, y - 2.1), (xd, y - 4.4), (xd, yd), w=BUS_W)

# ======================================================================== references on the silk
def place_refs(board, skip=("H",)):
    """Every reference on the silkscreen of its part's face, for the person with the BOM and a
    soldering iron: on the part's body where it fits (between a resistor's pads, inside a
    socket's rows), else just outside its courtyard, never over a pad or another reference."""
    boxes = list(LEGEND_BOXES)                  # placed text boxes (x0, y0, x1, y1, back): the legends first
    pads = [(p.x - max(p.w, p.h) / 2, p.y - max(p.w, p.h) / 2, p.x + max(p.w, p.h) / 2,
             p.y + max(p.w, p.h) / 2) for p in board.pads]
    holes = [(hx - hd / 2, hy - hd / 2, hx + hd / 2, hy + hd / 2) for hx, hy, hd in board.holes]
    silk = {}                                   # (layer, 1 mm cell) -> printed outline points, every part's own included
    for r in board.placed:
        for sx, sy, ly in board.silk_points(r):
            silk.setdefault((ly, int(sx // 1), int(sy // 1)), []).append((sx, sy))
    for kind, ly, d in board.gfx:               # and the legends' own lines
        if kind == "line":
            n = max(1, int(math.hypot(d[2] - d[0], d[3] - d[1]) / 0.2))
            for i in range(n + 1):
                sx, sy = d[0] + (d[2] - d[0]) * i / n, d[1] + (d[3] - d[1]) * i / n
                silk.setdefault((ly, int(sx // 1), int(sy // 1)), []).append((sx, sy))

    def free(bx, back):
        m = 0.2
        if bx[0] < 0.6 or bx[1] < 0.6 or bx[2] > board.W - 0.6 or bx[3] > board.H - 0.6:
            return False
        for q in pads + holes:
            if bx[0] - m < q[2] and q[0] < bx[2] + m and bx[1] - m < q[3] and q[1] < bx[3] + m:
                return False
        ly, g = ("B.SilkS" if back else "F.SilkS"), 0.15 + 0.06
        for i in range(int((bx[0] - g) // 1), int((bx[2] + g) // 1) + 1):
            for j in range(int((bx[1] - g) // 1), int((bx[3] + g) // 1) + 1):
                for sx, sy in silk.get((ly, i, j), ()):
                    if bx[0] - g < sx < bx[2] + g and bx[1] - g < sy < bx[3] + g:
                        return False
        for q in boxes:
            if q[4] == back and bx[0] - m < q[2] and q[0] < bx[2] + m and bx[1] - m < q[3] and q[1] < bx[3] + m:
                return False
        return True

    for ref in sorted(board.placed, key=K._refkey):
        if ref.startswith(skip) and ref[len(skip[0]):].isdigit():
            continue
        f, x, y = board.placed[ref]
        c = board.court(ref)
        cx, cy = (c[0] + c[2]) / 2, (c[1] + c[3]) / 2
        wide = (c[2] - c[0]) >= (c[3] - c[1])
        cands = []
        for size in (1.0,):                   # the fab's floor: 1.0 mm text, 0.15 mm stroke
            tw, th = len(ref) * 0.8 * size + 0.1, size
            for rot in ((0, 90) if wide else (90, 0)):
                bw, bh = (tw, th) if rot == 0 else (th, tw)
                cands.append((cx, cy, rot, size, bw, bh))
                for o in (0.25, 1.0):
                    cands += [(cx, c[1] - bh / 2 - o, rot, size, bw, bh), (cx, c[3] + bh / 2 + o, rot, size, bw, bh),
                              (c[0] - bw / 2 - o, cy, rot, size, bw, bh), (c[2] + bw / 2 + o, cy, rot, size, bw, bh),
                              (c[0] + bw / 2, c[1] - bh / 2 - o, rot, size, bw, bh), (c[2] - bw / 2, c[1] - bh / 2 - o, rot, size, bw, bh),
                              (c[0] + bw / 2, c[3] + bh / 2 + o, rot, size, bw, bh), (c[2] - bw / 2, c[3] + bh / 2 + o, rot, size, bw, bh)]
        for tx, ty, rot, size, bw, bh in cands:
            bx = (tx - bw / 2, ty - bh / 2, tx + bw / 2, ty + bh / 2)
            if free(bx, f.back):
                boxes.append(bx + (f.back,))
                board.ref_at[ref] = (round(tx - x, 3), round(ty - y, 3), rot, size)
                break
        else:
            tx, ty, rot, size, bw, bh = cands[0]
            boxes.append((tx - bw / 2, ty - bh / 2, tx + bw / 2, ty + bh / 2, f.back))
            board.ref_at[ref] = (round(tx - x, 3), round(ty - y, 3), rot, 1.0)
            print(f"  reference {ref}: no clear spot, left on the body")


# ======================================================================== the legends (rev B)
# The boards are ordered in black mask with white silk. The fab floor (Rezonit and JLC): lines at
# least 0.15 mm, text at least 1.0 mm tall with a 0.15 mm stroke, nothing printed on a pad.
LEGEND_BOXES = []                           # (x0, y0, x1, y1, back): the legends' text, kept clear by the references
LEGEND_MISSED = []
TEXT_W = 1.0                                # a character's advance in text heights, generously: KiCad's own
TEXT_H = 1.3                                # extents (its DRC's silk checks) run to ~0.9 x and ~1.2 x the height


def _tbox(t, x, y, size, rot=0):
    w, h = len(t) * TEXT_W * size + 0.1, TEXT_H * size
    if rot in (90, 270):
        w, h = h, w
    return (x - w / 2, y - h / 2, x + w / 2, y + h / 2)


class _Silk:
    """What a legend keeps clear of on its face: pads and holes (0.25 mm), the board edge (0.6 mm),
    every part's printed outline, the legends already down and - for a block label, which belongs
    on bare board - every courtyard on that face."""

    def __init__(self, board):
        self.b = board
        self.pads = [(p.x - max(p.w, p.h) / 2, p.y - max(p.w, p.h) / 2, p.x + max(p.w, p.h) / 2,
                      p.y + max(p.w, p.h) / 2) for p in board.pads]
        self.pads += [(hx - hd / 2, hy - hd / 2, hx + hd / 2, hy + hd / 2) for hx, hy, hd in board.holes]
        self.silk = {}
        for r in board.placed:
            for sx, sy, ly in board.silk_points(r):
                self.silk.setdefault((ly, int(sx // 1), int(sy // 1)), []).append((sx, sy))
        self.courts = [(board.court(r), board.placed[r][0].back) for r in board.placed if not r.startswith("H")]
        # the footprints' own printed marks (a diode's "K", say): (x0, y0, x1, y1, layer)
        self.marks = []
        for r, (f, x, y) in board.placed.items():
            for n in K.S.walk(f.tree):
                if not (isinstance(n, list) and n and n[0] == "fp_text" and len(n) > 2 and K.S.unq(n[1]) == "user"):
                    continue
                t, ly, at = K.S.unq(n[2]), K.S.find(n, "layer"), K.S.find(n, "at")
                if t.startswith("${") or not ly or not K.S.unq(ly[1]).endswith("SilkS") or not at:
                    continue
                sz = K.S.find(K.S.find(K.S.find(n, "effects") or [], "font") or [], "size")
                h = float(sz[1]) if sz else 1.0
                half = max(len(t) * TEXT_W * h, TEXT_H * h) / 2       # either way round: the part may be turned
                cx, cy = x + float(at[1]), y + float(at[2])
                self.marks.append((cx - half, cy - half, cx + half, cy + half, K.S.unq(ly[1])))

    def near_print(self, x, y, ly, d):
        """Is (x, y) within d of a part's printed outline or mark on face `ly`?"""
        for i in (int(x // 1) - 1, int(x // 1), int(x // 1) + 1):
            for j in (int(y // 1) - 1, int(y // 1), int(y // 1) + 1):
                for sx, sy in self.silk.get((ly, i, j), ()):
                    if math.hypot(sx - x, sy - y) < d:
                        return True
        return any(m[4] == ly and m[0] - d < x < m[2] + d and m[1] - d < y < m[3] + d for m in self.marks)

    def free(self, bx, back, courts):
        m, g = 0.25, 0.25
        if bx[0] < 0.6 or bx[1] < 0.6 or bx[2] > self.b.W - 0.6 or bx[3] > self.b.H - 0.6:
            return False
        for q in self.pads:
            if bx[0] - m < q[2] and q[0] < bx[2] + m and bx[1] - m < q[3] and q[1] < bx[3] + m:
                return False
        ly = "B.SilkS" if back else "F.SilkS"
        for i in range(int((bx[0] - g) // 1), int((bx[2] + g) // 1) + 1):
            for j in range(int((bx[1] - g) // 1), int((bx[3] + g) // 1) + 1):
                for sx, sy in self.silk.get((ly, i, j), ()):
                    if bx[0] - g < sx < bx[2] + g and bx[1] - g < sy < bx[3] + g:
                        return False
        for q in LEGEND_BOXES:
            if q[4] == back and bx[0] - m < q[2] and q[0] < bx[2] + m and bx[1] - m < q[3] and q[1] < bx[3] + m:
                return False
        if courts:
            for c, cb in self.courts:
                if cb == back and bx[0] < c[2] and c[0] < bx[2] and bx[1] < c[3] and c[1] < bx[3]:
                    return False
        return True

    def mark(self, pts, ly):
        for sx, sy in pts:
            self.silk.setdefault((ly, int(sx // 1), int(sy // 1)), []).append((sx, sy))


def legends(board):
    """Rev B's silkscreen: block labels, the 185 V area fenced and marked, the connectors' pinouts,
    the strips' names and pin 1, the trimmer, the fitting order, the USB warning and the title."""
    S_ = _Silk(board)

    def put(t, x, y, size=1.0, back=False, rot=0, reach=6.0, courts=True, thick=None):
        """The text at the free spot nearest (x, y), within `reach` mm."""
        cands = [(0.0, 0.0)]
        k = 1
        while k * 0.25 <= reach:
            r = k * 0.25
            for i in range(-k, k + 1):
                cands += [(i * 0.25, -r), (i * 0.25, r)]
            for j in range(-k + 1, k):
                cands += [(-r, j * 0.25), (r, j * 0.25)]
            k += 1
        for dx, dy in cands:
            bx = _tbox(t, x + dx, y + dy, size, rot)
            if S_.free(bx, back, courts):
                board.text(t, x + dx, y + dy, "B.SilkS" if back else "F.SilkS", size, thick=thick or max(0.15, round(size * 0.15, 3)), rot=rot)
                LEGEND_BOXES.append(bx + (back,))
                return (x + dx, y + dy)
        LEGEND_MISSED.append(f"legend '{t}' found no free spot within {reach} mm of ({x}, {y})")
        return None

    def fence(poly, width=0.2, label_at=()):
        """A closed outline, broken wherever it would print on a pad or a hole, or cross a part's own
        printed outline or mark (KiCad's DRC reports silk on silk)."""
        pads = [(p.x, p.y, max(p.w, p.h) / 2) for p in board.pads] + [(hx, hy, hd / 2) for hx, hy, hd in board.holes]
        pts = list(poly) + [poly[0]]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            n = max(1, int(math.hypot(x1 - x0, y1 - y0) / 0.1))
            run = []
            for i in range(n + 1):
                x, y = x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n
                ok = (all(math.hypot(x - px, y - py) > pr + 0.25 + width / 2 for px, py, pr in pads)
                      and not S_.near_print(x, y, "F.SilkS", width / 2 + 0.6))   # 0.3 past a sampled arc's chord
                if ok:
                    run.append((x, y))
                if (not ok or i == n) and len(run) > 1:
                    board.line(round(run[0][0], 3), round(run[0][1], 3), round(run[-1][0], 3), round(run[-1][1], 3), "F.SilkS", width)
                    S_.mark(run, "F.SilkS")
                if not ok:
                    run = []

    # the 185 V areas: the converter with its control and clamp, and the anode cells over the strips
    y_top = 0.9
    fence([(64.5, y_top), (141.6, y_top), (141.6, 25.9), (64.5, 25.9)])
    fence([(19.0, 44.6), (177.0, 44.6), (177.0, 69.7), (19.0, 69.7)])
    put("DANGER 185 V", 100.0, 26.6 - 1.2, 1.5, courts=True, reach=10.0)
    put("DANGER 185 V", 97.0, 45.9 + 0.6, 1.5, courts=True, reach=12.0)
    # block labels, on bare board
    put("POWER 12 V", 10.0, 24.5, 1.2, reach=6.0)
    put("12 V DC, centre +", 8.0, 26.1, 1.0, reach=4.0)
    put("HV CLAMP", 134.0, 25.5, 1.0, reach=6.0)
    put("DECODERS", 59.5, 38.0, 1.2, reach=8.0)
    put("ANODES", 95.0, 60.0, 1.2, reach=10.0)
    put("AM/PM", 20.0, 52.5, 1.2, reach=8.0)
    put("COLON", 143.4, 45.6, 1.0, reach=6.0)
    put("BACKLIGHT", 30.0, 71.5, 1.2, reach=10.0)
    put("RTC", 118.0, 79.0, 1.2, reach=8.0)
    put("FASCIA", 137.0, 86.0, 1.2, reach=8.0)
    put("LOGIC", 160.0, 20.8, 1.2, reach=8.0)
    put("USB only with 12 V on", 168.0, 20.6, 1.0, reach=6.0, courts=False)
    # the fitting order and the trimmer
    x, y = B.P("RP1", 2)
    put("HV SET", x, y + 2.9, 1.0, reach=4.0, courts=False)
    x, y = B.P("U11", 4)
    put("fit U12 before U11", x + 6.0, y + 2.4, 1.0, reach=10.0, courts=False)
    # the RTC module's pins, one label over each pad: pad 1 GND ... pad 5 +
    for pin, t in ((1, "-"), (2, "NC"), (3, "C"), (4, "D"), (5, "+")):
        x, y = B.P("U13", pin)
        put(t, x, y - 2.0, 1.0, reach=1.2, courts=False)
    # the TO-92 transistors: E by pin 1
    for ref in ("VT1", "VT2", "VT20"):
        x, y = B.P(ref, 1)
        put("E", x, y, 1.0, reach=2.6, courts=False)
    # on the face towards the display: J1's pinout and every strip's pin 1. Seen from that face J1's
    # pin 1 is on the right, so the pinout reads 6 to 1, each name over its own end of the row.
    x0, y0 = B.P("J1", 1)
    x6, y6 = B.P("J1", 6)
    put("6 D8 5 D7 4 A7 3 A6 2 GND 1 +5V", (x0 + x6) / 2, y0 - 3.0, 1.0, back=True, reach=6.0, courts=False)
    for k in DISP_STRIP:
        x, y = B.P(f"XS{k}", 1)
        x2, y2 = B.P(f"XS{k}", 2)
        dx, dy = x - x2, y - y2
        put("1", x + dx * 0.75, y + dy * 0.75, 1.0, back=True, reach=1.5, courts=False)
    # the title
    put(f"TERMINAL-06  TS06-DRV rev {REV}  {DATE}", 88.0, 88.0, 1.5, reach=12.0)


def silk_check(board):
    """Every legend line and text at the fab's floor and off every pad."""
    bad = list(LEGEND_MISSED)
    pads = [(p.x, p.y, max(p.w, p.h) / 2, p.ref, p.name) for p in board.pads]
    for kind, ly, d in board.gfx:
        if kind == "line":
            x0, y0, x1, y1, w = d
            if w < 0.15 - 1e-9:
                bad.append(f"silk line {d} thinner than 0.15 mm")
            for px, py, pr, ref, nm in pads:
                if K.pt_seg((px, py), (x0, y0), (x1, y1)) < pr + 0.15 + w / 2 - 1e-6:
                    bad.append(f"silk line {d} on pad {ref}.{nm}")
        elif kind == "text":
            t, x, y, size, th, mirror, rot, just = d
            if size < 1.0 - 1e-9 or th < 0.15 - 1e-9:
                bad.append(f"silk text '{t}' {size} mm / {th} mm, under the fab's 1.0 / 0.15")
            bx = _tbox(t, x, y, size, rot)
            for px, py, pr, ref, nm in pads:
                if bx[0] - 0.15 < px + pr and px - pr < bx[2] + 0.15 and bx[1] - 0.15 < py + pr and py - pr < bx[3] + 0.15:
                    bad.append(f"silk text '{t}' on pad {ref}.{nm}")
    for ref, (dx, dy, rot, size) in board.ref_at.items():
        if size < 1.0 - 1e-9:
            bad.append(f"reference {ref} at {size} mm")
    return bad


# ======================================================================== the two boards mate
def check_mate():
    """Every XS pin here must sit exactly behind its XP pin on TS06-DISP (x mirrored, y offset by Y0),
    carry the same signal, and every display standoff must have its hole here."""
    import mkpcb_disp as DISP
    bad = []
    for k in P.HEADERS:
        n = len(P.HEADERS[k])
        for i in range(1, n + 1):
            xp, xs = DISP.B.pad(f"XP{k}", i), B.pad(f"XS{k}", i)
            if abs((DW - xp.x) - xs.x) > 1e-3 or abs(xp.y + Y0 - xs.y) > 1e-3:
                bad.append(f"XS{k}.{i} at ({xs.x}, {xs.y}) but XP{k}.{i} lands at ({DW - xp.x}, {xp.y + Y0})")
            if xp.net != xs.net:
                bad.append(f"XS{k}.{i} carries {xs.net} but XP{k}.{i} carries {xp.net}")
    mine = {(round(x, 3), round(y, 3)) for x, y, d in B.holes}
    for x, y, d in DISP.B.holes:
        if (round(DW - x, 3), round(y + Y0, 3)) not in mine:
            bad.append(f"display standoff at ({x}, {y}) has no hole here at ({DW - x}, {y + Y0})")
    return bad


# ======================================================================== the routed copper
# The router (tools/netroute.py) is run with --route and its tracks saved beside this file, so
# the board regenerates exactly - and without a C compiler - from the saved routes. Everything
# above this line is the source of truth for WHERE things are; the route file only records the
# copper the router found for that placement, and it is thrown away and re-found whenever the
# placement changes.
# The saved route is the source of truth for the routed copper: a fresh --route is deterministic
# (PYTHONHASHSEED is pinned above) but is only ever a proposal until it is saved here.
ROUTES = os.environ.get("TS06_ROUTES") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "mkpcb_drv_routes.json")
FIXED = set(B.tracks)                          # every hand-laid track: kept, never ripped
LOCKED = {t[0] for t in B.tracks if t[0].startswith(("K", "CAT_", "XA", "XB", "BL_A"))} | {"D2", "D3", "D4", "D5", "D6", "D9"}
WIDTHS = {"+12V": 0.8, "VIN_J": 0.8, "VIN_F": 0.8, "SW": 0.8, "+5V": 0.4, "GND": 0.4}


def route_order():
    """The most constrained first: the A0-A3 bus (two decoders from one set of pads), port A up the
    left edge, the LED ribbon, I2C and the Nano's digital lines; then the 185 V nets, the rails,
    everything else, and ground last."""
    nets = sorted({p.net for p in B.pads if p.net})
    hv = [n for n in nets if B.cls(n) == "HV"]
    order = ([f"A{i}" for i in range(4)] + [f"XA{i}" for i in range(8)] + [f"XB{i}" for i in range(8)] +
             [f"BL_A{i}" for i in range(1, 9)] + ["SDA", "SCL", "A6", "A7"] + [f"D{i}" for i in range(2, 14)] +
             ["SW", "HV185"] + [n for n in hv if n not in ("SW", "HV185")] +
             ["+12V", "VIN_J", "VIN_F", "GATE_D", "GATE", "+5V"])
    order += [n for n in nets if n not in order and n != "GND" and n not in LOCKED]
    return [n for n in order if n in nets] + ["GND"]


def route():
    """Negotiated routing (netroute.Negotiator) of everything not laid by hand, then a polish pass
    that re-routes each net alone with the rest in place. A diagonal step is priced above two
    straight ones and every 45 degrees of turn costs 0.6 mm, so long runs come out straight and
    square with a 45 degree chamfer at each corner, the way the hand-laid buses are drawn."""
    import netroute as NR
    R = NR.NetRouter(B, turn45=6.0)
    R.locked = set(LOCKED)
    R.fixed = set(FIXED)
    R.dirmul = {ly: [1.0, 1.5, 1.0, 1.5, 1.0, 1.5, 1.0, 1.5] for ly in ("F.Cu", "B.Cu")}
    N = NR.Negotiator(R, route_order(), widths=WIDTHS)
    # the state after every round (TS06_STATE, or beside a trial route file), so a stopped run loses nothing
    state = os.environ.get("TS06_STATE") or (ROUTES + ".state" if os.environ.get("TS06_ROUTES") else None)
    failed = N.run(rounds=60, state=state)
    if not failed:
        R.polish([n for n in route_order() if n not in LOCKED], widths=WIDTHS, verbose=True)
    with open(ROUTES, "w") as fh:
        json.dump([[n, ly, [list(a), list(b)], w] for n, ly, a, b, w in B.tracks if (n, ly, a, b, w) not in FIXED], fh, indent=0)
    return failed


def load_routes():
    with open(ROUTES) as fh:
        for n, ly, (a, b), w in json.load(fh):
            B.tracks.append((n, ly, tuple(a), tuple(b), w))


def trim_stubs():
    """A hand-laid stub ends where the drawing says; the router, on its 0.1 mm grid, joins it a little
    short, on the stub itself. Cut each stub back to the joint, so no track ends in the air (KiCad
    reports a dangling end even where the copper overlaps). A stub segment the router joined at its
    far end goes altogether, and the one before it is looked at again."""
    def loose(t, e):
        n, ly = t[0], t[1]
        if any(u is not t and u[0] == n and u[1] == ly and e in (u[2], u[3]) for u in B.tracks):
            return False
        return not any(q.net == n and abs(q.x - e[0]) <= q.w / 2 and abs(q.y - e[1]) <= q.h / 2 for q in B.pads)

    changed = True
    while changed:
        changed = False
        for i, t in enumerate(B.tracks):
            if t not in FIXED:
                continue
            n, ly, a, b, w = t
            for e, o in ((a, b), (b, a)):
                if not loose(t, e):
                    continue
                L = math.hypot(o[0] - e[0], o[1] - e[1])
                best = None
                for u in B.tracks:
                    if u in FIXED or u[0] != n or u[1] != ly:
                        continue
                    for p in (u[2], u[3]):
                        d = math.hypot(p[0] - e[0], p[1] - e[1])
                        off = abs((o[0] - e[0]) * (p[1] - e[1]) - (o[1] - e[1]) * (p[0] - e[0])) / L if L else 1
                        if 0 < d <= L + 1e-6 and off < 1e-3 and (best is None or d < best[0]):
                            best = (d, p)
                if best is None:
                    continue
                if best[0] >= L - 1e-6:                     # joined at the far end: the whole segment is loose
                    del B.tracks[i]
                    FIXED.discard(t)
                else:
                    nt = (n, ly, best[1], o, w) if e == a else (n, ly, o, best[1], w)
                    B.tracks[i] = nt
                    FIXED.discard(t); FIXED.add(nt)
                changed = True
                break
            if changed:
                break


if __name__ == "__main__":
    placed = set(B.placed)
    missing = sorted(set(PT) - placed, key=K._refkey)
    assert not missing, "not placed: " + " ".join(missing)
    wrong = [r for r in PT if B.placed[r][0].name != PT[r].fp]
    assert not wrong, "placed on a footprint the netlist does not name: " + " ".join(wrong)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    if PLACE_ONLY:
        K.plot_placement(B, os.path.join(os.path.dirname(OUT), "placement.png"), ppm=7)
        refs = list(B.placed)
        for i, a in enumerate(refs):
            ca = B.court(a)
            for b in refs[i + 1:]:
                cb = B.court(b)
                if ca[0] < cb[2] and cb[0] < ca[2] and ca[1] < cb[3] and cb[1] < ca[3]:
                    if B.placed[a][0].back == B.placed[b][0].back:
                        print(f"  overlap {a} / {b}")
        sys.exit(0)
    if "--hand" in sys.argv:                # the hand-laid copper alone against the rules, before a route
        bad = [b for b in B.check(verbose=False) if "pieces:" not in b and "lands on nothing" not in b]
        for b in bad:
            print("  [HAND]", b)
        for s in B.soft:
            print("  [SOFT]", s)
        sys.exit(1 if bad else 0)
    if "--route" in sys.argv or not os.path.exists(ROUTES):
        failed = route()
        print("unrouted:", " ".join(failed) if failed else "none")
    else:
        load_routes()
    trim_stubs()
    # ground on both faces around everything else; the routed ground tree already joins every
    # ground pad, so the pours only add area and shielding - they carry no connection of their own
    B.zone("GND", "F.Cu", clearance=0.5, min_th=0.3, gap=0.5, bridge=0.5)
    B.zone("GND", "B.Cu", clearance=0.5, min_th=0.3, gap=0.5, bridge=0.5)
    # ground pads that sit where the back pour is only a sliver fenced in by tracks: a thermal
    # into it reaches nothing (KiCad: "starved thermal"). They are joined by their tracks, so the
    # pours leave them alone and the slivers, touching no pad, are removed as islands. KiCad's DRC
    # names them after each re-route; the list keeps every one it has named.
    B.no_zone |= {("C5", "2"), ("U1", "4"), ("U15", "12"), ("C16", "2"), ("U5", "2"), ("U16", "12"), ("U3", "15"),
                  ("R71", "2")}
    B.hide_refs = True
    legends(B)
    place_refs(B)
    bad = B.check() + silk_check(B)
    print(f"check: {len(bad)} problem(s)")
    for b in bad:
        print("  [CHECK]", b)
    print(f"cathode pads under 0.5 mm (soft, E10): {len(B.soft)}")
    for s in B.soft:
        print("  [SOFT]", s)
    mate = check_mate()
    print("mate:", "every strip pin and standoff lines up" if not mate else "")
    for m in mate:
        print("  [MATE]", m)
    n = B.write(OUT, title=NAME, rev=REV, date=DATE, comment="TERMINAL-06 driver board, THT pair with TS06-DISP")
    B.write_project(OUT.replace(".kicad_pcb", ".kicad_pro"))
    B.write_rules(OUT.replace(".kicad_pcb", ".kicad_dru"), [B.HV_PAD_RULE])
    B.write_library()
    vias = 0
    print(f"wrote {os.path.relpath(OUT, ROOT)}: {len(B.placed)} parts, {n} nets, {len(B.tracks)} segments, {vias} vias")
    png = os.path.join(os.path.dirname(OUT), "copper.png")
    B.plot(png, ppm=8, color=lambda n: ((255, 90, 90) if B.cls(n) == "HV" else None))
    sys.exit(1 if bad or mate else 0)
