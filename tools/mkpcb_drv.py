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
side - the clock seen from behind - so a display x becomes 176 - x here, and y is the display's
y. This board's top edge is Y0 = 26 mm above the display's (pl() adds it). check_mate() proves
every socket pin lands on its header pin and every display standoff has its hole.

THE THREE BANDS, 176 x 100 in all:
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
so the board regenerates exactly without re-routing.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbkit as K
import ts06pair as P

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
NAME = "TS06-DRV"
OUT = os.environ.get("TS06_OUT") or os.path.join(ROOT, "PCB", NAME, NAME + ".kicad_pcb")
PLACE_ONLY = "--place" in sys.argv

W, H = 176.0, 100.0
DW = 176.0                                  # the display board's width: x here = DW - x there
Y0 = 26.0                                   # this board's top edge is 26 mm above the display's
YT, YB = 2.2 + Y0, 41.3 + Y0                # the strip rows, shared with TS06-DISP
CLASSES = [("HV", 0.6, 0.4, P.HV_PATTERNS),
           ("CATH", 0.25, 0.25, P.CATH_PATTERNS),
           ("PWR", 0.25, 0.5, ["+5V", "+12V", "VIN_J", "VIN_F", "GATE_D", "GATE"])]
B = K.Board(NAME, W, H, P.parts(P.DRV), CLASSES, default=("Default", 0.2, 0.25))
PT = P.parts(P.DRV)


def pl(ref, x, y, rot=0, back=False, fp=None):
    """Place a part at (x, y) in the DISPLAY board's frame (y shared with TS06-DISP, which
    starts Y0 below this board's top edge), on the footprint the netlist names."""
    return B.place(ref, fp or PT[ref].fp, x, y + Y0, rot, back)


LOW_W = {"GND": 0.15, "+5V": 0.3, "+12V": 0.5}   # rails are everywhere: they guide placement weakly


def near(ref, x0, y0, x1, y1, rots=(0, 90, 180, 270), keepout=()):
    """Place a small part in the free spot of a region (display frame) nearest its copper."""
    ko = [(a, b + Y0, c, d + Y0) for a, b, c, d in keepout]
    r = K.place_near(B, ref, PT[ref].fp, (x0, y0 + Y0, x1, y1 + Y0), rots, keepout=ko, weight=LOW_W)
    assert r is not None, f"no room for {ref} in ({x0}, {y0})-({x1}, {y1})"
    return r


# ======================================================================== the strips (back face)
DISP_STRIP = {"11": (1.6, 4.4, True), "12": (99.57, 2.2, False), "21": (11.94, 41.3, False),
              "22": (47.99, 41.3, False), "23": (69.28, 41.3, False), "24": (107.335, 41.3, False),
              "25": (139.15, 41.3, False)}


def socket(k):
    x, y, vertical = DISP_STRIP[k]
    n = len(P.HEADERS[k])
    pl(f"XS{k}", DW - x, y, rot=0 if vertical else 90, back=True)
    return [B.P(f"XS{k}", i + 1) for i in range(n)]


XS = {k: socket(k) for k in DISP_STRIP}

# Standoffs: the display's four, mirrored; two more at the bottom corners and two along the top.
HOLES = [(172.5, 40.5), (3.5, 40.5), (DW - 50.535, 3.3), (3.5, 5.5),
         (3.5, 70.5), (172.5, 70.5), (3.5, -22.5), (172.5, -3.5)]
for i, (hx, hy) in enumerate(HOLES):
    B.place(f"H{i + 1}", "TS06_MountingHole_M3", hx, hy + Y0)
    B.holes.append((hx, hy + Y0, 3.2))

# ======================================================================== the tube band
# The decoders under the top strip, pins 16..9 facing it; U2 turned over beside XS11.
DEC_Y = 15.62 + Y0
pl("U16", 12.93, 15.62, rot=90)
pl("U15", 35.25, 15.62, rot=90)
pl("U17", 58.65, 15.62, rot=90)
pl("U2", 166.2, 27.26, rot=180)

# The anode channel cells. Each pair of anode pins gets its two series resistors lying one above
# the other, each ending straight over its pin, and its two optos standing above them, emitter
# pin over the resistor it feeds; the 185 V feed runs between the optos and the resistors.
Y_U, Y_L, Y3 = 33.8, 37.6, 30.3


def cell_left(xl, r_up, r_lo, o_up, o_lo):
    xr = xl + 2.54
    pl(r_up, xr - 12.7, Y_U)
    pl(r_lo, xl - 12.7, Y_L)
    pl(o_up, xr - 12.7 + 2.54, Y3 - 7.62, rot=270)
    pl(o_lo, xr - 15.9, Y3 - 7.62, rot=270)


def cell_right(xl, r_up, r_lo, o_up, o_lo):
    pl(r_up, xl + 12.7, Y_U, rot=180)
    pl(r_lo, xl + 2.54 + 12.7, Y_L, rot=180)
    pl(o_up, xl + 15.24, Y3 - 7.62, rot=270)
    pl(o_lo, xl + 21.04, Y3 - 7.62, rot=270)


cell_left(63.585, "R31", "R32", "U9", "U10")         # S10 / S1
cell_right(101.64, "R30", "R29", "U8", "U7")         # M1 / M10
cell_left(156.44, "R27", "R28", "U5", "U6")          # H10 / H1

# The colon: one ballast per lamp standing over its pin, the return switch beside them.
pl("R59", 126.5, 24.6, rot=270)                      # COLON_L
pl("R58", 130.5, 24.6, rot=270)                      # COLON_U
pl("VT1", 121.0, 33.0, rot=270)

# The AM/PM static anode resistors, over their pins.
pl("R56", 34.31, 37.0, rot=180)
pl("R57", 26.69, 33.2, rot=180)

# ======================================================================== the top band
# The Nano lies across the top right corner, its digital row facing down into the board and its
# USB 2.4 mm proud of the right edge (the clock's left side, seen from the front).
pl("U1", 136.24, -8.73, rot=90)

# The 12 V inlet at the top left, jack mouth through the left edge, then fuse, polarity diode
# and the 5 V regulator, in the order the current takes them.
pl("XS1", 14.0, -13.50)
pl("F1", 24.0, -23.30)
pl("VD2", 36.24, -17.00, rot=180)
pl("U14", 21.5, -6.50)
pl("C8", 40.5, -22.20)

# The 185 V converter: inductor, switch, catch diode, reservoir in one tight loop; the gate
# driver beside the switch; the comparator, divider and trimmer beside the driver.
pl("L1", 47.5, -12.50)
pl("VT21", 59.0, -7.00)
pl("VD1", 67.8, -16.00, rot=180)
pl("C7", 72.5, -20.00)
pl("U11", 81.0, -5.30, rot=180)
pl("R67", 69.0, -12.40, rot=180)
# The control block, laid out by hand: the divider comes down from the 185 V side on the left
# (R62), turns at FB_MID (R63 standing), and FB meets the comparator's input pin, the 15k and
# the trimmer on the right; the 2.5 V reference divider and the output pull-down stand in a row
# on the left, beside the driver input they feed.
pl("U12", 104.0, -8.0, rot=180)
pl("R62", 96.0, -23.7)
pl("R63", 111.6, -23.7, rot=270)
pl("R64", 114.5, -14.0)
pl("RP1", 124.5, -8.0)
pl("R69", 84.8, -11.0, rot=90)
pl("R70", 88.3, -11.0, rot=90)
pl("R71", 91.8, -11.0, rot=90)
pl("R65", 114.5, -22.0)
pl("C14", 96.5, -20.3)

# ======================================================================== where lines change face
# A through-hole pad is copper on both faces, so a series resistor is the one "via" a zero-via
# board has. The Nano's lines are placed so that each one changes face at its own resistor, where
# it has to cross something:
#  * the four lines that come down the corridor beside the Nano (D9 the converter's PWM, D10 the
#    colon, D12 the "m" LED, D13 an anode) end in four standing resistors at the corridor's exit,
#    and what leaves them (PWM_G north to the control block, the rest south) is on the front face;
#  * the minutes' and S10's anode resistors stand under the Nano's west end, where D2-D4 come
#    west to them; their outputs drop down that side and run west in lanes under the resistors
#    at the corridor's exit;
#  * the hours' anode resistors lie straight above their optos, D5 and D6 coming west to them.
HOP_Y = 41.9                                # pad 1 of the corridor-exit resistors (DRV frame)
for ref, x in (("R66", 126.0), ("R1", 122.5), ("R53", 119.0), ("R26", 115.5)):
    pl(ref, x, HOP_Y - Y0, rot=270)
for ref, x, y in (("R25", 134.6, 24.0), ("R24", 137.6, 24.0), ("R23", 140.6, 24.0)):
    pl(ref, x, y - Y0, rot=270)
pl("R22", 143.1, 35.3 - Y0, rot=270)        # H1
pl("R21", 148.8, 35.3 - Y0, rot=270)        # H10

# ======================================================================== the bottom band
# The expander and the LED network, stacked: port B straight up into the network, the network
# straight up into the LED corridor under the bottom strips; port A leaves downwards and runs
# up the left edge to the two ИН-15 decoders.
pl("U3", 44.5, 60.0, rot=270)
pl("RN1", 26.72, 56.0, rot=90)
# The fascia cable plugs in at the bottom edge on the face towards the display, which is the
# face the fascia sits in front of: the cable goes straight forward, not round the stack.
pl("J1", 122.0, 69.0, rot=180, back=True)
# The fascia's ladder filters and the I2C pull-ups in one column between the colon's ballasts and the
# hours' cell. A7, A6, SCL and SDA come west through the hours' optos on the front face, in that
# order top to bottom, and each ends in its own part in the same order; they leave on the back face,
# the filters' lines down the column's right side to J1, the pull-ups' lines west to the clock module.
HOP_X = 137.4                               # the column's signal pads
pl("C6", HOP_X, 48.0 - Y0, rot=180)         # A7: pad 1, the signal, on the right
pl("C5", HOP_X, 50.5 - Y0, rot=180)         # A6
pl("R55", HOP_X - 2.54, 53.1 - Y0)          # SCL: pad 2, the signal, on the right
pl("R54", HOP_X - 2.54, 56.1 - Y0)          # SDA
# The clock module, turned so that SCL is above SDA as the two lines arrive from the column.
pl("U13", 115.83, 74.27 - Y0, rot=270)
# U2's decoupling capacitor beside the chip's left column, fed from its 5 V pin through the gap above
# pin 12, below where the A0-A3 lines reach U2 and clear of the lines going down the gap.
pl("C4", 155.5, 48.5 - Y0, rot=270)

# ======================================================================== the small parts
# Each goes to the free spot of its region nearest the pads it connects to (pcbkit.place_near).
FANS = (5.0, -0.6, 80.5, 17.3)             # the hand-laid decoder fans: no part over them
XALANES = (5.0, 17.0, 51.8, 21.3)          # port A's lanes under the two ИН-15 decoders
XALEFT = (4.5, 17.0, 10.0, 74.0)           # ... up the left edge
XABOT = (5.0, 68.4, 46.5, 74.0)            # ... and under the expander
BLRIB = (20.0, 42.0, 166.0, 45.9)          # the LED ribbon under the bottom strips
GAP = (150.0, -1.0, 157.5, 30.0)           # between the hours' cell and U2: the Nano's lines go south
PLAZA = (132.5, -5.0, 157.5, 21.0)         # under the Nano: its lines fan out here
OPTLANES = (52.0, 19.2, 136.0, 21.6)       # D2-D4's anode lines run west under the corridor's exit
XAFAN = (5.0, 17.0, 52.0, 30.5)            # port A's lines rise up the left edge into U16 / U15
NECK = (78.0, -1.0, 157.5, 21.0)           # the Nano's lines come down through here
for r in ("C9", "C10", "C11"):
    near(r, 17.0, -25.5, 45.0, -4.6)
for r in ("C12", "R68", "C13", "C3"):
    near(r, 38.0, -25.5, 127.0, -4.6)
for r in ("R60", "R61"):                    # the reservoir's bleeder, on the 185 V feed between cells
    near(r, 67.0, 29.0, 100.5, 39.4, keepout=(OPTLANES,))
for r in ("C15", "C16"):
    near(r, 8.0, 21.4, 46.0, 25.5, rots=(0,), keepout=(XALANES,))
near("C17", 58.0, 21.7, 80.0, 26.5, rots=(0,), keepout=(OPTLANES,))
for r in ("VT20", "R20"):                    # the backlight switch, under U2 beside XS21's BL_K pin
    near(r, 161.0, 28.8, 170.5, 40.2, keepout=(BLRIB,))
for r in ("R33", "R34", "R35", "R36"):
    near(r, 152.0, 44.0, 176.0, 74.0, keepout=(BLRIB,))
for r in ("R37", "R38", "R39", "R40", "R41", "R42", "R43", "R44"):
    near(r, 45.0, 17.4, 157.0, 40.0, keepout=(XAFAN, NECK, GAP, PLAZA, OPTLANES))
near("C1", 10.0, 44.5, 26.0, 57.5, keepout=(XALEFT, XABOT, BLRIB))   # the expander's own decoupling
JACK = tuple(v - (Y0 if i % 2 else 0) for i, v in enumerate(B.court("J1")))   # nothing under J1's housing

# ======================================================================== hand-laid copper
# The decoder fans, laid the way a person lays them: every line a straight rise, a 45 degree
# shift of one or two pitches, or a wrap round the end of the chip.
LV = 0.25                                   # cathode-line width


def T(net, layer, *pts, w=LV):
    B.track(net, layer, list(pts), w)


def rise(net, layer, pad, x_to, y_top=YT, bend=None):
    """From a decoder's top-row pad straight up, then 45 degrees across to the strip pin."""
    x, y = pad
    dx = x_to - x
    if abs(dx) < 1e-6:
        T(net, layer, (x, y), (x, y_top))
        return
    yb = y_top + abs(dx) if bend is None else bend
    T(net, layer, (x, y), (x, yb), (x_to, y_top))


def P_(ref, pin):
    return B.P(ref, pin)


XS12 = {PT["XS12"].pins[str(i + 1)]: B.P("XS12", i + 1) for i in range(28)}

# U16 (ИН-15А), back face.
for pin in (16, 15, 14, 13, 11, 10, 9):
    n = PT["U16"].pins[str(pin)]
    rise(n, "B.Cu", P_("U16", pin), XS12[n][0])
T("CAT_A_NANO", "B.Cu", P_("U16", 8), (32.0, DEC_Y - 1.29), (32.0, YT + 1.29), XS12["CAT_A_NANO"])
T("CAT_A_P", "B.Cu", P_("U16", 1), (10.39, DEC_Y - 2.54), XS12["CAT_A_P"])
T("CAT_A_MICRO", "B.Cu", P_("U16", 2), (14.2, DEC_Y + 1.27), (9.12, DEC_Y + 1.27), (7.85, DEC_Y), XS12["CAT_A_MICRO"])

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
    rise(n, "B.Cu", P_("U17", pin), XS12[n][0])
rise("KS0", "F.Cu", P_("U17", 15), XS12["KS0"][0])
T("KS7", "F.Cu", P_("U17", 8), (78.97, DEC_Y - 2.54), (78.97, YT + 2.54), XS12["KS7"])
T("KS9", "B.Cu", P_("U17", 1), (56.11, DEC_Y - 2.54), XS12["KS9"])
T("KS8", "B.Cu", P_("U17", 2), (59.92, DEC_Y + 1.27), (54.9, DEC_Y + 1.27), (54.9, YT + 1.33), XS12["KS8"])

# U2 (ИН-12 bus), beside XS11. The column facing the strip (K7 K8 K9) goes straight across on the
# front; the far column threads through the chip on the back, each line through the gap above
# its own pin, and lands on the strip in order.
XS11 = {PT["XS11"].pins[str(i + 1)]: B.P("XS11", i + 1) for i in range(10)}
T("K7", "F.Cu", P_("U2", 8), XS11["K7"])
T("K8", "F.Cu", P_("U2", 2), (169.3, P_("U2", 2)[1]), (169.3, XS11["K3"][1]), (171.84, XS11["K8"][1]), XS11["K8"])
T("K9", "F.Cu", P_("U2", 1), (171.8, P_("U2", 1)[1]), (171.8, XS11["K2"][1] + 0.06), XS11["K9"])
X_DIAG = 172.6                              # where each back-face line finishes its 45 degree run
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

# The digital row fans out on the back face in lanes just below the module, each line on its own
# level, the westernmost pin on the top lane: D2-D4 west to the minutes' and S10's resistors standing
# under the module's end, D5 and D6 to the hours' resistors above their optos, D7, D8 and D11 down
# the gap between the hours' cell and U2 (D7 and D8 to J1, D11 to the backlight switch under U2).
def fan(n, x, y, lane, x_to, y_to):
    T(n, "B.Cu", (x, y), (x, lane - 0.5), (x - 0.5, lane), (x_to + 0.5, lane), (x_to, lane + 0.5), (x_to, y_to))


for pin, lane, ref in ((5, 21.6, "R25"), (6, 22.25, "R24"), (7, 22.9, "R23"), (8, 24.1, "R22"), (9, 24.75, "R21")):
    n = PT["U1"].pins[str(pin)]
    x, y = P_("U1", pin)
    fan(n, x, y, lane, *P_(ref, 1))
GAP_X, GAP_Y = 152.4, 44.0                  # the gap's first line (D7) and where the router takes over
for k, (pin, lane) in enumerate(((10, 25.9), (11, 26.55), (14, 27.2))):
    n = PT["U1"].pins[str(pin)]
    x, y = P_("U1", pin)
    fan(n, x, y, lane, GAP_X + 0.6 * k, GAP_Y)

# The analogue row's A6, A7, SCL and SDA drop through the digital row's gaps on the front face, close
# up into four lanes down the same gap, and turn west through the hours' optos - between each opto's
# two rows of pins - to the column of their filters and pull-ups (HOP_X), where they change face.
F_GAP = (149.95, 150.55, 151.15, 151.75)    # A7 A6 SCL SDA down the gap
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
        pts += [(pad[0] + (pad[1] - yl), yl), pad]
    else:                                   # SDA, the lowest, turns down first
        xt = 139.15
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
X_COR = 128.0                               # the corridor's first line (A3)
PITCH = 0.6
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
XA_P, XA_BOT, XA_LEFT, XA_TOP = 0.45, 95.0, 9.0, 43.5
for i in range(8):
    x, y = P_("U3", 21 + i)
    yb, xl, yt = XA_BOT + i * XA_P, XA_LEFT - i * XA_P, XA_TOP + (7 - i) * XA_P
    xd, yd = P_(*XA_DEST[i])
    T(f"XA{i}", "B.Cu", (x, y), (x, yb - 0.5), (x - 0.5, yb), (xl + 1.0, yb), (xl, yb - 1.0),
      (xl, yt + 1.0), (xl + 1.0, yt), (xd - 0.5, yt), (xd, yt - 0.5), (xd, yd))

# Port B straight up into the LED network.
for i in range(8):
    T(f"XB{i}", "B.Cu", P_("U3", 1 + i), P_("RN1", 8 - i))

# The LED ribbon: from the network's far row up into lanes under the bottom strips and along them
# each line peeling off up into its strip pin - the nearest pin on the top lane.
# BL_A8 is a short diagonal to its pin beside the network; BL_A7 crosses the ribbon on the front.
BL_DEST = {1: ("XS21", 2), 2: ("XS21", 5), 3: ("XS23", 1), 4: ("XS23", 4), 5: ("XS24", 1), 6: ("XS24", 4)}
BL_Y = 69.0
for k, i in enumerate((6, 5, 4, 3, 2, 1)):
    x, y = P_("RN1", 8 + i)
    yl = BL_Y + k * XA_P
    xd, yd = P_(*BL_DEST[i])
    # the two lines that reach the hours' strip run on the front face, so that east of the minutes'
    # strip the back face under the strips is free for the lines that must cross down to J1
    T(f"BL_A{i}", "F.Cu" if i in (1, 2) else "B.Cu", (x, y), (x, yl + 0.5), (x + 0.5, yl), (xd - 0.5, yl),
      (xd, yl - 0.5), (xd, yd))
x, y = P_("RN1", 16)
xd, yd = P_("XS25", 6)
T("BL_A8", "B.Cu", (x, y), (x, yd + (x - xd)), (xd, yd))
x, y = P_("RN1", 15)
xd, yd = P_("XS25", 1)
T("BL_A7", "F.Cu", (x, y), (x + 2.1, y - 2.1), (xd - 2.3, y - 2.1), (xd, y - 4.4), (xd, yd))

# ======================================================================== references on the silk
def place_refs(board, skip=("H",)):
    """Every reference on the silkscreen of its part's face, for the person with the BOM and a
    soldering iron: on the part's body where it fits (between a resistor's pads, inside a
    socket's rows), else just outside its courtyard, never over a pad or another reference."""
    boxes = []                                  # placed text boxes (x0, y0, x1, y1, back)
    pads = [(p.x - max(p.w, p.h) / 2, p.y - max(p.w, p.h) / 2, p.x + max(p.w, p.h) / 2,
             p.y + max(p.w, p.h) / 2) for p in board.pads]
    holes = [(hx - hd / 2, hy - hd / 2, hx + hd / 2, hy + hd / 2) for hx, hy, hd in board.holes]

    def free(bx, back):
        m = 0.2
        if bx[0] < 0.6 or bx[1] < 0.6 or bx[2] > board.W - 0.6 or bx[3] > board.H - 0.6:
            return False
        for q in pads + holes:
            if bx[0] - m < q[2] and q[0] < bx[2] + m and bx[1] - m < q[3] and q[1] < bx[3] + m:
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
        for size in (1.0, 0.8):
            tw, th = len(ref) * 0.8 * size + 0.1, size
            for rot in ((0, 90) if wide else (90, 0)):
                bw, bh = (tw, th) if rot == 0 else (th, tw)
                cands.append((cx, cy, rot, size, bw, bh))
                cands += [(cx, c[1] - bh / 2 - 0.25, rot, size, bw, bh), (cx, c[3] + bh / 2 + 0.25, rot, size, bw, bh),
                          (c[0] - bw / 2 - 0.25, cy, rot, size, bw, bh), (c[2] + bw / 2 + 0.25, cy, rot, size, bw, bh)]
        for tx, ty, rot, size, bw, bh in cands:
            bx = (tx - bw / 2, ty - bh / 2, tx + bw / 2, ty + bh / 2)
            if free(bx, f.back):
                boxes.append(bx + (f.back,))
                board.ref_at[ref] = (round(tx - x, 3), round(ty - y, 3), rot, size)
                break
        else:
            tx, ty, rot, size, bw, bh = cands[0]
            boxes.append((tx - bw / 2, ty - bh / 2, tx + bw / 2, ty + bh / 2, f.back))
            board.ref_at[ref] = (round(tx - x, 3), round(ty - y, 3), rot, 0.8)
            print(f"  reference {ref}: no clear spot, left on the body")


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
ROUTES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mkpcb_drv_routes.json")
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
    failed = N.run(rounds=60)
    if not failed:
        R.polish([n for n in route_order() if n not in LOCKED], widths=WIDTHS, verbose=True)
    with open(ROUTES, "w") as fh:
        json.dump([[n, ly, [list(a), list(b)], w] for n, ly, a, b, w in B.tracks if (n, ly, a, b, w) not in FIXED], fh, indent=0)
    return failed


def load_routes():
    with open(ROUTES) as fh:
        for n, ly, (a, b), w in json.load(fh):
            B.tracks.append((n, ly, tuple(a), tuple(b), w))


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
    if "--route" in sys.argv or not os.path.exists(ROUTES):
        failed = route()
        print("unrouted:", " ".join(failed) if failed else "none")
    else:
        load_routes()
    # ground on both faces around everything else; the routed ground tree already joins every
    # ground pad, so the pours only add area and shielding - they carry no connection of their own
    B.zone("GND", "F.Cu", clearance=0.5, min_th=0.3, gap=0.5, bridge=0.5)
    B.zone("GND", "B.Cu", clearance=0.5, min_th=0.3, gap=0.5, bridge=0.5)
    B.hide_refs = True
    place_refs(B)
    B.text("TS06-DRV rev A", 30.0, 72.3, "F.SilkS", 1.0)
    B.text("TERMINAL-06  driver", 30.0, 70.8, "F.SilkS", 0.8)
    bad = B.check()
    print(f"check: {len(bad)} problem(s)")
    mate = check_mate()
    print("mate:", "every strip pin and standoff lines up" if not mate else "")
    for m in mate:
        print("  [MATE]", m)
    n = B.write(OUT, title=NAME, comment="TERMINAL-06 driver board, THT pair with TS06-DISP")
    B.write_project(OUT.replace(".kicad_pcb", ".kicad_pro"))
    B.write_library()
    vias = 0
    print(f"wrote {os.path.relpath(OUT, ROOT)}: {len(B.placed)} parts, {n} nets, {len(B.tracks)} segments, {vias} vias")
    png = os.path.join(os.path.dirname(OUT), "copper.png")
    B.plot(png, ppm=8, color=lambda n: ((255, 90, 90) if B.cls(n) == "HV" else None))
