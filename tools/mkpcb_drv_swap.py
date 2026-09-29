#!/usr/bin/env python3
"""TS06-DRV, the SWAP layout: logic on top, power at the bottom. An alternative to
tools/mkpcb_drv.py for the same circuit, the same strips and the same standoffs.

    python3 tools/mkpcb_drv_swap.py             # PCB/TS06-DRV-swap/TS06-DRV-swap.kicad_pcb (+ .kicad_pro, copper.png)
    python3 tools/mkpcb_drv_swap.py --route     # the same, routing afresh (tools/netroute.py) first
    python3 tools/mkpcb_drv_swap.py --place     # placement only: PCB/TS06-DRV-swap/placement.png

THE IDEA. The baseline puts what switches (the 185 V converter, the 12 V inlet) in the top band and
the expander in the bottom band, so the Nano's lines and the expander's port A lap the board. Here
the bands are turned round:
  * the TOP BAND carries only logic: the Nano standing on end right of the top strip, USB out of
    the TOP edge; the clock module and the I2C pull-ups beside it;
  * the TUBE BAND keeps the decoders under the top strip and U2 beside the left strip (their fans
    are the baseline's, line for line), and adds the MCP23017 straight under the two ИН-15 decoders,
    so port A is eight 45-degree lines ~10 mm long; the six anode cells stand over the bottom strips;
  * the BOTTOM BAND carries the power: 12 V jack through the right edge, fuse, polarity diode,
    5 V regulator, the 185 V converter and its control, the AM/PM anode resistors, J1 (bottom edge,
    on the face towards the display, as in the baseline) and the backlight switch.

The frame is the baseline's (tools/mkpcb_drv.py docstring): x as seen from this board's component
side, y from this board's top edge, which is Y0 = 26 mm above the display's.
"""
import json, os, sys
os.environ["TS06_DRV_VARIANT"] = "swap"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbkit as K
import ts06pair as P

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
NAME = "TS06-DRV-swap"
OUT = os.environ.get("TS06_OUT") or os.path.join(ROOT, "PCB", NAME, NAME + ".kicad_pcb")
PLACE_ONLY = "--place" in sys.argv

W, H = 176.0, 100.0
DW = 176.0
Y0 = 26.0
YT, YB = 2.2 + Y0, 41.3 + Y0                # the strip rows (this board's frame)
CLASSES = [("HV", 0.6, 0.4, P.HV_PATTERNS),
           ("CATH", 0.25, 0.25, P.CATH_PATTERNS),
           ("PWR", 0.25, 0.5, ["+5V", "+12V", "VIN_J", "VIN_F", "GATE_D", "GATE"])]
B = K.Board(NAME, W, H, P.parts(P.DRV), CLASSES, default=("Default", 0.2, 0.25))
PT = P.parts(P.DRV)


def pd(ref, x, y, rot=0, back=False):
    """Place a part at (x, y) in THIS board's frame (y from its top edge)."""
    return B.place(ref, PT[ref].fp, x, y, rot, back)


LOW_W = {"GND": 0.15, "+5V": 0.3, "+12V": 0.5}


def near(ref, x0, y0, x1, y1, rots=(0, 90, 180, 270), keepout=()):
    r = K.place_near(B, ref, PT[ref].fp, (x0, y0, x1, y1), rots, keepout=keepout, weight=LOW_W)
    if r is None:
        print(f"  no room for {ref} in ({x0}, {y0})-({x1}, {y1})")
    return r


# ======================================================================== the strips and standoffs
DISP_STRIP = {"11": (1.6, 4.4, True), "12": (99.57, 2.2, False), "21": (11.94, 41.3, False),
              "22": (47.99, 41.3, False), "23": (69.28, 41.3, False), "24": (107.335, 41.3, False),
              "25": (139.15, 41.3, False)}
for k, (x, y, vertical) in DISP_STRIP.items():
    pd(f"XS{k}", DW - x, y + Y0, rot=0 if vertical else 90, back=True)

# the display's four standoffs (fixed), then four of this board's own: two at the bottom corners,
# one in the top-left corner below the D12 run, one in the top-right corner
HOLES = [(172.5, 66.5), (3.5, 66.5), (DW - 50.535, 29.3), (3.5, 33.5),
         (3.5, 96.5), (172.5, 96.5), (3.5, 14.0), (172.5, 3.5)]
for i, (hx, hy) in enumerate(HOLES):
    B.place(f"H{i + 1}", "TS06_MountingHole_M3", hx, hy)
    B.holes.append((hx, hy, 3.2))

# ======================================================================== the tube band
DEC_Y = 15.62 + Y0
pd("U16", 12.93, DEC_Y, rot=90)
pd("U15", 35.25, DEC_Y, rot=90)
pd("U17", 58.65, DEC_Y, rot=90)
pd("U2", 166.2, 27.26 + Y0, rot=180)

# The expander straight under the two ИН-15 decoders, port A (its top row) facing their inputs.
U3_X, U3_Y = 25.4, 59.0                     # pin 1; the top row (GPA7..GPA0, left to right) is 7.62 above
pd("U3", U3_X, U3_Y, rot=90)
# The LED network standing at the left edge, left of the AM/PM strip: port B reaches it in lanes
# under the expander, and its right column feeds the LED ribbon under the bottom strips.
RN_X, RN_Y = 9.0, 65.0                      # the top of its left column (pin 9); notch down, as U2's
pd("RN1", RN_X + 7.62, RN_Y + 17.78, rot=180)

# The anode cells over the bottom strips (the baseline's cells): two stacked anode resistors ending
# straight over their pins, the two optos standing above them, 185 V between.
Y_U, Y_L, Y3 = 33.8 + Y0, 37.6 + Y0, 30.3 + Y0


def cell_left(xl, r_up, r_lo, o_up, o_lo):
    xr = xl + 2.54
    pd(r_up, xr - 12.7, Y_U)
    pd(r_lo, xl - 12.7, Y_L)
    pd(o_up, xr - 12.7 + 2.54, Y3 - 7.62, rot=270)
    pd(o_lo, xr - 15.9, Y3 - 7.62, rot=270)


def cell_right(xl, r_up, r_lo, o_up, o_lo):
    pd(r_up, xl + 12.7, Y_U, rot=180)
    pd(r_lo, xl + 2.54 + 12.7, Y_L, rot=180)
    pd(o_up, xl + 15.24, Y3 - 7.62, rot=270)
    pd(o_lo, xl + 21.04, Y3 - 7.62, rot=270)


cell_right(63.59, "R32", "R31", "U10", "U9")         # S1 / S10
cell_right(101.64, "R30", "R29", "U8", "U7")         # M1 / M10
cell_left(156.44, "R27", "R28", "U5", "U6")          # H10 / H1

# The colon: one ballast per lamp standing over its pin, the return switch beside them.
pd("R59", 126.5, 24.6 + Y0, rot=270)                 # COLON_L
pd("R58", 130.5, 24.6 + Y0, rot=270)                 # COLON_U
pd("VT1", 121.0, 33.0 + Y0, rot=270)

# ======================================================================== the top band
# The Nano stands on end right of the top strip, USB 1.6 mm proud of the TOP edge, analogue column
# on the left (towards U17), digital column on the right. Its pin 1 end is placed so that the two
# idle pins' gaps (TX-RX, RX-RST) are level with the gaps U2's A0 and A1 enter by.
NANO_X, NANO_Y = 101.24, 40.56
pd("U1", NANO_X, NANO_Y, rot=180)
XL = NANO_X - 15.24                         # the analogue column
# The clock module and the pull-ups left of the Nano, on the short I2C.
pd("U13", 70.0, 8.0)

# ======================================================================== the bottom band
# The 12 V inlet at the bottom right, jack mouth through the right edge, then the fuse, the
# polarity diode along the bottom edge and the 5 V regulator, in the order the current takes them.
pd("XS1", 162.0, 88.0, rot=180)
pd("F1", 148.0, 90.0)
pd("VD2", 141.0, 96.5)
pd("U14", 137.5, 84.0)
# The 185 V converter in one loop: inductor, switch, catch diode, reservoir; the driver beside it.
pd("C7", 106.0, 78.5, rot=270)
pd("L1", 126.0, 80.5, rot=180)
pd("VD1", 107.0, 89.0)
pd("VT21", 115.5, 95.5)
pd("U11", 125.6, 97.8, rot=90)
# The control block west of J1: bleeder and divider along the bottom edge, comparator above them.
pd("R60", 40.0, 96.5)
pd("R61", 52.7, 92.5, rot=180)
pd("R62", 58.0, 96.5)
pd("R63", 74.0, 96.5, rot=90)
pd("U12", 57.0, 86.0, rot=90)
pd("RP1", 69.5, 91.4)
# AM/PM anode resistors, lying up from the bottom band into their strip pins.
pd("R57", 26.69, 75.5, rot=270)             # ANODE_PM (XS25.5)
pd("R56", 34.31, 75.5, rot=270)             # ANODE_AM (XS25.2)
# The fascia cable at the bottom edge, on the face towards the display.
pd("J1", 100.0, 96.5, back=True)
# A6 and A7 change face at their ladder filters, just above J1, to cross D7 and D8 into their pins.
pd("C6", 86.5, 84.0, rot=270)
pd("C5", 89.5, 84.0, rot=270)

# ======================================================================== the hops
# A 470R in series with an opto LED is where its line changes face.
pd("R25", 90.0, 48.6, rot=270)              # D13 -> S10: D13 comes down inside the module
pd("R26", 97.4, 52.0, rot=270)              # D3 -> S1, its OPT line under S10's

# ======================================================================== keepouts for small parts
PORTA = (15.0, 41.0, 53.0, 51.5)            # port A's fan
PORTB = (10.0, 58.0, 45.0, 64.5)            # port B's lanes and the descent into RN1
RIBBON = (7.0, 67.8, 165.0, 73.2)           # the LED ribbon under the strips
NANO_IN = (79.0, -1.0, 101.3, 48.0)         # the Nano, its escape and the A0-A3 split
ABUS = (101.0, 32.0, 158.0, 36.0)           # A0-A3 east to U2
ABUS2 = (148.0, 32.0, 158.0, 48.0)
ALANES = (60.0, 42.0, 83.0, 48.5)           # A0-A3 west under U17
DLEFT = (3.0, 1.5, 101.0, 5.0)              # D12 west along the top edge ...
DLEFT2 = (3.0, 1.5, 8.0, 99.0)              # ... and down the left edge
KO = (PORTA, PORTB, RIBBON, NANO_IN, ABUS, ABUS2, ALANES, DLEFT, DLEFT2)

near("R23", 102.0, 36.5, 112.0, 46.0, keepout=KO)   # D2 -> M10
near("R24", 102.0, 36.5, 116.0, 46.0, keepout=KO)   # D4 -> M1
near("R21", 104.0, 36.5, 124.0, 46.0, keepout=KO)   # D6 -> H10
near("R22", 104.0, 36.5, 124.0, 46.0, keepout=KO)   # D5 -> H1
near("R1", 110.0, 44.0, 136.0, 66.0, keepout=KO)    # D10 -> the colon switch
for r in ("R54", "R55"):
    near(r, 60.0, 17.0, 78.0, 26.5, keepout=KO)
near("C3", 60.0, 1.0, 84.0, 26.5, keepout=KO)
near("C15", 7.8, 43.0, 12.5, 58.0, rots=(90, 270), keepout=(DLEFT2,))
pd("C16", 56.2, 48.1)
near("C17", 60.0, 46.5, 64.5, 58.5, rots=(90, 270))
near("C1", 44.0, 59.5, 62.0, 66.0, keepout=KO)
pd("C4", 155.5, 48.5, rot=270)             # U2's decoupling, fed through the gap above its pin 12
near("R53", 8.0, 85.5, 24.0, 99.5)
for r in ("VT20", "R20"):
    near(r, 158.0, 73.8, 176.0, 84.0, keepout=KO)
for r in ("C8", "C9", "C10", "C11"):
    near(r, 128.0, 73.8, 160.0, 99.5, keepout=KO)
for r in ("C12", "R68", "R67"):
    near(r, 100.5, 73.8, 160.0, 99.5, keepout=KO)
# D9 comes down east of J1's lines on the back face and ends in its series resistor there: PWM_G
# crosses J1's lines on the front face to the comparator.
near("R66", 96.5, 73.8, 135.0, 99.5, keepout=KO)
for r in ("R71", "R65", "R69", "R70", "C14", "C13", "R64"):
    near(r, 38.0, 73.8, 85.0, 99.5, keepout=KO)
for r in ("R33", "R34", "R35", "R36", "R37", "R38", "R39", "R40", "R41", "R42", "R43", "R44"):
    near(r, 60.0, 47.0, 157.0, 66.0, keepout=KO)


# ======================================================================== hand-laid copper
LV = 0.25


def T(net, layer, *pts, w=LV):
    B.track(net, layer, list(pts), w)


def rise(net, layer, pad, x_to, y_top=YT, bend=None):
    x, y = pad
    dx = x_to - x
    if abs(dx) < 1e-6:
        T(net, layer, (x, y), (x, y_top))
        return
    yb = y_top + abs(dx) if bend is None else bend
    T(net, layer, (x, y), (x, yb), (x_to, y_top))


def P_(ref, pin):
    return B.P(ref, pin)


if True:
    XS12 = {PT["XS12"].pins[str(i + 1)]: B.P("XS12", i + 1) for i in range(28)}
    # ---- the decoder fans, the baseline's line for line (tools/mkpcb_drv.py)
    for pin in (16, 15, 14, 13, 11, 10, 9):
        n = PT["U16"].pins[str(pin)]
        rise(n, "B.Cu", P_("U16", pin), XS12[n][0])
    T("CAT_A_NANO", "B.Cu", P_("U16", 8), (32.0, DEC_Y - 1.29), (32.0, YT + 1.29), XS12["CAT_A_NANO"])
    T("CAT_A_P", "B.Cu", P_("U16", 1), (10.39, DEC_Y - 2.54), XS12["CAT_A_P"])
    T("CAT_A_MICRO", "B.Cu", P_("U16", 2), (14.2, DEC_Y + 1.27), (9.12, DEC_Y + 1.27), (7.85, DEC_Y), XS12["CAT_A_MICRO"])
    for pin in (16, 15, 14, 13):
        n = PT["U15"].pins[str(pin)]
        rise(n, "F.Cu", P_("U15", pin), XS12[n][0], bend=YT + 2.0)
    for pin in (11, 10, 9):
        n = PT["U15"].pins[str(pin)]
        rise(n, "F.Cu", P_("U15", pin), XS12[n][0])
    T("CAT_B_AMP", "F.Cu", P_("U15", 8), (55.0, DEC_Y), (55.0, YT + 4.0), XS12["CAT_B_AMP"])
    for pin in (14, 13, 11, 10, 9, 16):
        n = PT["U17"].pins[str(pin)]
        rise(n, "B.Cu", P_("U17", pin), XS12[n][0])
    rise("KS0", "F.Cu", P_("U17", 15), XS12["KS0"][0])
    T("KS7", "F.Cu", P_("U17", 8), (78.97, DEC_Y - 2.54), (78.97, YT + 2.54), XS12["KS7"])
    T("KS9", "B.Cu", P_("U17", 1), (56.11, DEC_Y - 2.54), XS12["KS9"])
    T("KS8", "B.Cu", P_("U17", 2), (59.92, DEC_Y + 1.27), (54.9, DEC_Y + 1.27), (54.9, YT + 1.33), XS12["KS8"])

    XS11 = {PT["XS11"].pins[str(i + 1)]: B.P("XS11", i + 1) for i in range(10)}
    T("K7", "F.Cu", P_("U2", 8), XS11["K7"])
    T("K8", "F.Cu", P_("U2", 2), (169.3, P_("U2", 2)[1]), (169.3, XS11["K3"][1]), (171.84, XS11["K8"][1]), XS11["K8"])
    T("K9", "F.Cu", P_("U2", 1), (171.8, P_("U2", 1)[1]), (171.8, XS11["K2"][1] + 0.06), XS11["K9"])
    X_DIAG = 172.6
    for pin in (9, 10, 11, 13, 14, 15, 16):
        n = PT["U2"].pins[str(pin)]
        px, py = P_("U2", pin)
        tx, ty = XS11[n]
        if pin == 9:
            gy = P_("U2", 8)[1] - 1.52
            T(n, "B.Cu", (px, py), (px + py - gy, gy), (X_DIAG - abs(ty - gy), gy), (X_DIAG, ty), (tx, ty))
        else:
            gy = py - 1.27
            T(n, "B.Cu", (px, py), (px + 1.27, gy), (X_DIAG - abs(ty - gy), gy), (X_DIAG, ty), (tx, ty))
    # U2's inputs thread the chip on the front face to its far side (the baseline's stubs); its 5 V
    # leaves on the back face through the gap above pin 12 into C4.
    x_l = P_("U2", 16)[0]
    U2_IN = {}
    for pin in (7, 6, 4, 3):
        n = PT["U2"].pins[str(pin)]
        x, y = P_("U2", pin)
        U2_IN[n] = (x_l - 1.58, y - 1.27)
        T(n, "F.Cu", (x, y), (x - 1.27, y - 1.27), U2_IN[n])
    x, y = P_("U2", 5)
    c1 = P_("C4", 1)
    T("+5V", "B.Cu", (x, y), (x - 1.27, y - 1.27), (c1[0] + 0.55, y - 1.27), (c1[0], y - 0.72), c1, w=0.3)
    c = B.court("U2")
    B.keepouts.append((x_l + 0.2, c[1], W, c[3], "*"))

    # ---- port A: eight 45-degree lines from the expander's top row up into the decoders' inputs
    # (GPA7..GPA0 left to right, U16 then U15, pins 3 4 6 7 each), all on the back face.
    XA_DEST = {7: ("U16", 3), 6: ("U16", 4), 5: ("U16", 6), 4: ("U16", 7),
               3: ("U15", 3), 2: ("U15", 4), 1: ("U15", 6), 0: ("U15", 7)}
    Y_FAN = U3_Y - 7.62 - 1.18              # where each line leaves its pad's vertical
    for i in range(8):
        x, y = P_("U3", 21 + i)
        xd, yd = P_(*XA_DEST[i])
        T(f"XA{i}", "B.Cu", (x, y), (x, Y_FAN), (xd, Y_FAN - abs(xd - x)), (xd, yd))

    # ---- port B: down out of the expander's bottom row into lanes under it, west to the network,
    # down between its two columns and into its left column, GPB0 at the top.
    XB_LANE, XB_P = U3_Y + 1.3, 0.5
    XB_DESC = RN_X + 1.3                    # the leftmost descent, between the network's columns
    for k in range(8):
        x, y = P_("U3", 1 + k)
        yl = XB_LANE + k * XB_P
        xd = XB_DESC + k * XB_P
        px, py = P_("RN1", 9 + k)
        T(f"XB{k}", "B.Cu", (x, y), (x, yl - 0.5), (x - 0.5, yl), (xd + 0.5, yl), (xd, yl + 0.5),
          (xd, py - (xd - px)), (px, py))

    # ---- the LED ribbon: out of the network's right column east, into lanes under the bottom
    # strips on the front face, each line peeling up into its pin, the nearest pin on the top lane.
    BL_DEST = {8: ("XS25", 6), 7: ("XS25", 1), 6: ("XS24", 4), 5: ("XS24", 1),
               4: ("XS23", 4), 3: ("XS23", 1), 2: ("XS21", 5), 1: ("XS21", 2)}
    BL_Y, BL_P = 68.6, 0.5
    TURN = {8: 18.6, 7: 18.1, 6: 19.1, 5: 19.6, 4: 20.1, 3: 20.6, 2: 21.1, 1: 21.6}
    for j in range(8):                      # lane j, top first: BL_A8, BL_A7 ... BL_A1
        pin = 8 - j
        n = PT["RN1"].pins[str(pin)]
        x, y = P_("RN1", pin)
        yl = BL_Y + j * BL_P
        xd, yd = P_(*BL_DEST[int(n[4:])])
        T(n, "F.Cu", (x, y), (TURN[pin], y), (TURN[pin], yl), (xd - 0.5, yl), (xd, yl - 0.5), (xd, yd))

    # ---- A0-A3: split at the Nano's analogue pads. West on the back face, down the gap between U17
    # and the module and into U17's inputs from below; east on the front face, inside the module and
    # out through its idle pins' gaps (A0, A1) or under its end (A2, A3), along under the standoff
    # H3, and down into U2's input gaps.
    A_PIN = {"A0": 19, "A1": 20, "A2": 21, "A3": 22}
    U17_IN = {"A0": 7, "A1": 6, "A2": 4, "A3": 3}
    for k, n in enumerate(("A0", "A1", "A2", "A3")):
        x, y = P_("U1", A_PIN[n])
        xc = 79.9 + k * 0.6                 # descent west of the module, A0 outermost (west)
        yl = 43.6 + k * 0.6                 # lanes under U17, A0 on top
        xd, yd = P_("U17", U17_IN[n])
        T(n, "B.Cu", (x, y), (xc + 0.6, y), (xc, y + 0.6), (xc, yl - 0.6), (xc - 0.6, yl), (xd + 0.6, yl),
          (xd, yl - 0.6), (xd, yd))
    AE_EXIT = {"A0": 36.75, "A1": 39.29, "A2": 44.37, "A3": 46.91}
    AE_LANE = {"A0": 32.9, "A1": 33.5, "A2": 34.1, "A3": 34.7}
    for k, n in enumerate(("A0", "A1", "A2", "A3")):
        x, y = P_("U1", A_PIN[n])
        xi = 96.5 - k * 1.0                 # descent inside the module, A0 easternmost
        ye = AE_EXIT[n]
        xr = 103.2 + k * 0.6                # the climb east of the module, A0 westernmost
        yl = AE_LANE[n]
        xg = 151.0 + (3 - k) * 0.6          # the drop to U2, A0 easternmost
        ex, ey = U2_IN[n]
        T(n, "F.Cu", (x, y), (xi - 0.6, y), (xi, y + 0.6), (xi, ye - 0.6), (xi + 0.6, ye), (xr - 0.6, ye),
          (xr, ye - 0.6), (xr, yl + 0.6), (xr + 0.6, yl), (xg - 0.6, yl), (xg, yl + 0.6), (xg, ey - 0.6),
          (xg + 0.6, ey), (ex, ey))

    # ---- the Nano's lines that leave by the module's south end, on the back face inside it:
    # from the analogue column A7, A6 and D13 (lowest pad westernmost), from the digital column D8,
    # D7 and D3 (lowest pad easternmost). The router takes them on from below the module.
    Y_OUT = NANO_Y + 3.6
    for pin, xd in ((26, 87.6), (25, 88.2), (16, 90.0)):
        n = PT["U1"].pins[str(pin)]
        x, y = P_("U1", pin)
        yy = y if pin != 16 else y + 1.27
        pts = [(x, y)] if pin != 16 else [(x, y), (x + 1.27, yy)]
        T(n, "B.Cu", *pts, (xd - 0.5, yy), (xd, yy + 0.5), (xd, Y_OUT))
    T("D13", "B.Cu", (90.0, Y_OUT), P_("R25", 1))
    for pin, xd in ((11, 94.7), (10, 95.3), (6, 97.4)):
        n = PT["U1"].pins[str(pin)]
        x, y = P_("U1", pin)
        T(n, "B.Cu", (x, y), (xd + 0.5, y), (xd, y + 0.5), (xd, Y_OUT))
    T("D3", "B.Cu", (97.4, Y_OUT), P_("R26", 1))
    # D12 over the module's USB end and west along the top edge, down the left edge to R53.
    x, y = P_("U1", 15)
    T("D12", "B.Cu", (x, y), (x, 2.4), (6.3, 2.4), (5.7, 3.0), (5.7, 84.0))
    B.keepouts.append((XL + 0.9, -1.0, NANO_X - 0.9, NANO_Y + 3.3, "*"))    # inside the module: its escape


# ======================================================================== silk references
def place_refs(board, skip=("H",)):
    boxes = []
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


# ======================================================================== routing
ROUTES = os.environ.get("TS06_ROUTES") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "mkpcb_drv_swap_routes.json")
FIXED = set(B.tracks)
LOCKED = {t[0] for t in B.tracks if t[0].startswith(("K", "CAT_", "XA", "XB", "BL_A"))} | {"A0", "A1", "A2", "A3", "D13", "D3"}
WIDTHS = {"+12V": 0.8, "VIN_J": 0.8, "VIN_F": 0.8, "SW": 0.8, "+5V": 0.4, "GND": 0.4}


def route_order():
    nets = sorted({p.net for p in B.pads if p.net})
    hv = [n for n in nets if B.cls(n) == "HV"]
    head = (["SDA", "SCL", "A6", "A7"] + [f"D{i}" for i in range(2, 14)] + [f"OPT_{t}" for t in P.TUBES])
    power = (["SW", "HV185"] + [n for n in hv if n not in ("SW", "HV185")] +
             ["+12V", "VIN_J", "VIN_F", "GATE_D", "GATE", "+5V"])
    order = power + head if os.environ.get("TS06_ORDER") == "power" else head + power
    order += [n for n in nets if n not in order and n != "GND" and n not in LOCKED]
    return [n for n in order if n in nets and n not in LOCKED] + ["GND"]


def route():
    import netroute as NR
    if os.environ.get("TS06_HVKO"):         # keep the 185 V off the strip between the logic and the cells
        others = sorted({p.net for p in B.pads if p.net and B.cls(p.net) != "HV"})
        B.keepouts.append((60.0, 42.0, 157.0, 49.3, "*", others))
    R = NR.NetRouter(B, turn45=6.0)
    R.locked = set(LOCKED)
    R.fixed = set(FIXED)
    R.dirmul = {ly: [1.0, 1.5, 1.0, 1.5, 1.0, 1.5, 1.0, 1.5] for ly in ("F.Cu", "B.Cu")}
    N = NR.Negotiator(R, route_order(), widths=WIDTHS)
    conflicts = N.conflicts

    def watched():                          # each round: save the copper so far, for inspection
        c = conflicts()
        with open(ROUTES + ".partial", "w") as fh:
            json.dump([[n, ly, [list(a), list(b)], w] for n, ly, a, b, w in B.tracks if (n, ly, a, b, w) not in FIXED], fh)
        return c
    N.conflicts = watched
    failed = N.run(rounds=int(os.environ.get("TS06_ROUNDS", "60")))
    with open(ROUTES, "w") as fh:
        json.dump([[n, ly, [list(a), list(b)], w] for n, ly, a, b, w in B.tracks if (n, ly, a, b, w) not in FIXED], fh, indent=0)
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
    assert PLACE_ONLY or not missing, "not placed: " + " ".join(missing)
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
        bad = B.check(verbose=False)
        for b in bad:
            if "not connected" not in b and "pieces" not in b:
                print("  [HAND]", b)
        sys.exit(0)
    if "--route" in sys.argv or not os.path.exists(ROUTES):
        failed = route()
        print("unrouted:", " ".join(failed) if failed else "none")
    else:
        load_routes()
    B.zone("GND", "F.Cu", clearance=0.5, min_th=0.3, gap=0.5, bridge=0.5)
    B.zone("GND", "B.Cu", clearance=0.5, min_th=0.3, gap=0.5, bridge=0.5)
    B.hide_refs = True
    place_refs(B)
    B.text("TS06-DRV-swap rev A", 45.0, 99.0, "F.SilkS", 1.0)
    bad = B.check()
    print(f"check: {len(bad)} problem(s)")
    mate = check_mate()
    print("mate:", "every strip pin and standoff lines up" if not mate else "")
    for m in mate:
        print("  [MATE]", m)
    n = B.write(OUT, title=NAME, comment="TERMINAL-06 driver board, swap layout (logic top, power bottom)")
    B.write_project(OUT.replace(".kicad_pcb", ".kicad_pro"))
    B.write_library()
    print(f"wrote {os.path.relpath(OUT, ROOT)}: {len(B.placed)} parts, {n} nets, {len(B.tracks)} segments, 0 vias")
    png = os.path.join(os.path.dirname(OUT), "copper.png")
    B.plot(png, ppm=8, color=lambda n: ((255, 90, 90) if B.cls(n) == "HV" else (87, 217, 121)))
