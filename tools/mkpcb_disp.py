#!/usr/bin/env python3
"""TS06-DISP: the display board of the through-hole pair - tubes, colon, backlight, headers.

    python3 tools/mkpcb_disp.py            # PCB/TS06-DISP/TS06-DISP.kicad_pcb (+ .kicad_pro, .kicad_dru, copper.png)

Nothing on this board is placed by a packer or routed by a router. Every coordinate below is
chosen, and the reason is written beside it; tools/pcbkit.py only writes what this file says.
It exits 1 if any of its checks - pcbkit's, and the ones at the end of this file - finds a
problem (the files are still written, to be looked at).

GEOMETRY. The board stands vertical with the tubes on its front, in the plane the inherited
tube board occupied. Tube positions are the reviewed assembly's (3d/Clock.FCStd), exactly as
tools/mkpcb_main.py carried them: board x = world X, board y = TOP - world Y. The board is the
tube band and no more - 191.4 x 44 mm, like AlexGyver's 99 x 34 mm tube half. It was 176 wide
until the ИН-17 pair was found 13 mm apart where their Ø20 stems need 20.5 (29.09.26): the
ИН-12s and the colon kept the Gyver pitch, the seconds pair was re-spaced and the ИН-15 pair
moved 15.4 mm right with it.

WHAT IS ON IT: 4 x ИН-12 (H10 H1 M10 M1), 2 x ИН-17 (S10 S1), 2 x ИН-15 (AM PM), the two
ИНС-1 of the colon, nine 3 mm LEDs, and the male strips that plug into TS06-DRV behind it.

THE COPPER, and why there is no via on it:
  * THE ИН-12 BUS is ten strands threaded through the four sockets on the BACK face, the way
    the Gyver tube half does it. Every strand touches its pad in each ring and passes between
    the others through the ring's interior, above or below the pip hole. The order of the
    strands, top to bottom, is fixed by the rings themselves - 6 5 7 4 8 3 9 2 0 1 - because
    the left column of an ИН-12 reads 5 4 3 2 1 downwards and the right column 7 8 9 0. With
    that order every strand rises ~2.25 mm across a ring and falls ~2.25 mm between rings, so
    the whole bus is ten parallel zig-zags. It enters H10 straight from XP11, a vertical strip
    at the left edge (Gyver's P1/P3 are end strips for the same reason: a 2.54 mm pin pitch
    is close to the 2.25 mm pad pitch, so each strand runs nearly level into the socket).
  * THE ИН-17 PAIR cannot join that bus on one face: their pads run round the ring the other
    way (digits fall clockwise where an ИН-12's rise), and the anode sits mid-way down the
    right column, so no strand can pass an ИН-17 on the anode side. So each ИН-17 is the END
    of its own bundle, and both bundles start on the same ten pins of XP12 above them: S10's
    on the back face, S1's on the front. A through-hole pin is copper on both faces - it is
    the layer change. Both bundles wrap their tube from above, and one pin order serves both
    (7 6 5 4 3 2 1 0 9 8), because the two tubes are identical.
  * THE ИН-15 PAIR is wrapped from above on the back face, from the far end of the same strip:
    XP12 is one 31-pin strip, pins 1-10 the ИН-17 bundle, 11-13 spare, 14-21 ИН-15Б and
    22-31 ИН-15А. Each anode leaves downward through the gap the wrap leaves at the bottom.
  * ANODES AND LEDs go straight down to five short bottom strips.
  * THE FRONT FACE is one pour, BL_K, the LEDs' common cathode - there is no ground on this
    board, so the front is the LED return and nothing else, and it reads as one uniform black
    field around the tubes. Only five things cross it: the three colon lines (the colon
    sits inside the ИН-12 bus), S10's anode and S1's cathode bundle.

CLEARANCES (rev B, 30.09.26, from the electrical grill):
  * a bare 185 V pad keeps 0.8 mm from copper of any other net - IPC-2221B table 6-1, A6, for
    uncoated terminations at 171-250 V. TS06-DISP.kicad_dru, written here, makes KiCad's DRC
    and its pour fill hold it; copper_problems() below holds it for tracks, and for a bare
    cathode pad beside a 185 V track as well;
  * a cathode pad keeps 0.5 mm from other nets' strands, not only the class's 0.25;
  * no copper, on either face, within 3.8 mm of a standoff hole's centre (the metal standoff
    and screw head): a KiCad rule area round each hole. It is why no strand crosses the colon
    column above the upper lamp any more.

SILKSCREEN (rev B): white on black mask, drawn to the fab's minimums. What goes on which face,
and why, is at the silkscreen section below.
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbkit as K
import sexp as S
import ts06pair as P

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
NAME = "TS06-DISP"
OUT = os.environ.get("TS06_OUT") or os.path.join(ROOT, "PCB", NAME, NAME + ".kicad_pcb")

W, H = 191.4, 44.0                          # 176 + 15.4: the seconds pair at 20.5, see IN17_X
TOP = 78.0                                  # world Y of the top edge: 1 mm above the ИН-15 glass courtyards
IN12_WY = 40.10 + 20.066                    # the inherited board's tube centre height, world Y
Y12 = round(TOP - IN12_WY, 4)               # 17.834: ИН-12 and ИН-15 centres
Y17 = round(Y12 + 5.375, 4)                 # ИН-17 centres sit 5.375 below
IN12_X = [13.21, 36.57, 63.99, 87.37]
# The seconds pair: centres 20.5 apart, as concept Rev F set them off the ИН-17's Ø20 stem
# (knowledge/TERMINAL-06-measurements-IN17 Rev 5; 13.0, as TS06-MAIN had it, puts the stems 7 mm
# into each other). Each stem also clears the ИН-12 / ИН-15 glass beside it (Ø19.47) by 2.2 mm,
# 21.265 from M1 in x - a spacing picked so the ИН-15 pair moves exactly three strip pitches more
# than the ИН-17 group, and XP12 stays one strip with three spare pins (see XP12).
IN17_X = [108.635, 129.135]
IN15_X = [150.4, 171.4]                     # 15.4 right of where they were, pitch 21.0 as before
COLON_X = 50.535
COLON_Y = [TOP - 66.5, TOP - 52.5]          # lamp centres (FreeCAD)
LED_Y = round(TOP - (IN12_WY - 17.67), 4)   # 35.504, as TS06-MAIN had it
LED17_Y = round(TOP - (IN12_WY - 5.375 - 13.3), 4)
M_X = 160.9                                 # the "m" LED, beneath the AM/PM pair (midway)
YT = 2.2                                    # top strips
YB = 41.3                                   # bottom strips
LV = 0.25                                   # cathode-line width and clearance

CLASSES = [("HV", 0.6, 0.3, ["ANODE_*", "COLON_*"]),
           ("CATH", 0.25, 0.25, ["K0", "K1", "K2", "K3", "K4", "K5", "K6", "K7", "K8", "K9", "KS*", "CAT_*"])]
B = K.Board(NAME, W, H, P.parts(P.DISP), CLASSES, default=("Default", 0.2, 0.3))
PT = P.parts(P.DISP)

# ======================================================================== placement
for i, x in enumerate(IN12_X):
    B.place(f"V{i + 1}", "TS06_IN12_Socket", x, Y12)
for i, x in enumerate(IN17_X):
    B.place(f"V{i + 5}", "TS06_IN17_Socket", x, Y17)
B.place("V7", "TS06_INS1_Lamp", COLON_X, COLON_Y[0])
B.place("V8", "TS06_INS1_Lamp", COLON_X, COLON_Y[1])
B.place("V9", "TS06_IN12_Socket", IN15_X[0], Y12)
B.place("V10", "TS06_IN12_Socket", IN15_X[1], Y12)
for i, x in enumerate(IN12_X + IN17_X + IN15_X):
    B.place(f"HL{i + 1}", "TS06_LED_D3.0mm", x, LED17_Y if 4 <= i <= 5 else LED_Y)
B.place("HL9", "TS06_LED_D3.0mm", M_X, LED_Y)


def strip(ref, x0, y, vertical=False):
    """A male strip on the back, pin 1 at (x0, y), pins running +x (or +y if vertical)."""
    n = len(P.HEADERS[ref[2:]])
    if vertical:
        B.place(ref, f"TS06_PinHeader_1x{n:02d}", x0, y, rot=0, back=True)
    else:
        B.place(ref, f"TS06_PinHeader_1x{n:02d}", x0, y, rot=270, back=True)
    return [B.P(ref, k + 1) for k in range(n)]


# XP11 down the left edge, one pin per strand, level with the strand's entry into H10.
XP11 = strip("XP11", 1.6, 4.4, vertical=True)
# XP12 along the top: ten pins centred over the ИН-17 pair, three spare, eight over ИН-15Б, ten
# over ИН-15А. The spares are the 7.62 mm the ИН-15 pair moved beyond the ИН-17 group.
_XP12 = strip("XP12", 107.35, YT)          # 99.57 + 7.78: the ИН-15 group then moves exactly 15.4
# its three groups: pins 1-10 the ИН-17 bundle, 14-21 ИН-15Б (AM), 22-31 ИН-15А (PM)
XP12_S, XP12_AM, XP12_PM = _XP12[:10], _XP12[13:21], _XP12[21:]
# The bottom strips, under the tubes they serve (see the routing of each).
LX = lambda i: IN12_X[i] + 1.27
XP21 = strip("XP21", 11.94, YB)                         # BL_K under HL1's cathode, BL_A1 under its anode, then H10's anode...
XP22 = strip("XP22", 47.99, YB)                         # the colon, F.Cu
XP23 = strip("XP23", 69.28, YB)                         # M10 / M1
XP24 = strip("XP24", round((IN17_X[0] + IN17_X[1]) / 2 - 3.77, 3), YB)   # S10 / S1, centred under the pair
XP25 = strip("XP25", M_X - 6.35, YB)                    # AM, m, PM: HL9 sits exactly over pins 3 and 4

# Standoff holes (M3), where nothing else is: the two bottom corners, the top right corner, and
# the top of the colon column - between the H1 and M10 glass, where a screw head clears both.
# The top right one sits 7.5 mm down, not 5.5: the standoff shares the gap between the boards
# with XP12's body, and at 5.5 a hex spacer's corner came within 0.5 mm of the strip's end.
for i, (hx, hy) in enumerate(((3.5, 40.5), (W - 3.5, 40.5), (COLON_X, 3.3), (W - 3.5, 7.5))):
    B.place(f"H{i + 1}", "TS06_MountingHole_M3", hx, hy)
    B.holes.append((hx, hy, 3.2))
# Each standoff is metal, and so is the screw head on the front: no copper within 3.8 mm of a
# hole's centre, on either face. A 7 mm washer reaches 3.5 and a 5.5 mm hex spacer's corner 3.18.
# KiCad holds it as a rule area (no tracks, no vias, no pour) written beside each hole.
HOLE_KEEPOUT = 3.8


# ======================================================================== the ИН-12 bus
def ring_pad(ref, pad):
    return B.P(ref, pad)


def rel(cx, cy, pts):
    return [(cx + a, cy + b) for a, b in pts]


# A strand's route through one ИН-12, relative to the ring centre, entering on the left and
# leaving on the right. "T" marks the pad the strand touches. Lanes inside the ring: 5 7 4 8 3
# above the pip hole, 9 2 0 1 below it, one millimetre apart. Every number here was checked
# by B.check() against its neighbours; the comments say what each one clears.
G = lambda a, b: ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
PADREL = {1: (-3.981, -8.002), 2: (0.0, -8.990), 3: (3.987, -8.002), 4: (5.741, -4.494),
          5: (5.741, 0.0), 6: (5.741, 4.495), 7: (3.987, 8.0), 8: (0.0, 8.991), 9: (-3.981, 8.0),
          10: (-5.742, 4.495), 11: (-5.742, 0.0), 12: (-5.742, -4.494)}
DPAD = {"5": 1, "6": 2, "7": 3, "8": 4, "9": 5, "0": 6, "1": 9, "2": 10, "3": 11, "4": 12}
PR = {d: PADREL[p] for d, p in DPAD.items()}
gL1, gL2, gL3, gL4 = G(PADREL[1], PADREL[12]), G(PADREL[12], PADREL[11]), G(PADREL[11], PADREL[10]), G(PADREL[10], PADREL[9])
gR1, gR2, gR3 = G(PADREL[3], PADREL[4]), G(PADREL[4], PADREL[5]), G(PADREL[5], PADREL[6])
# Two clearances decide the rest (grill, 30.09.26). A bare 185 V pad keeps 0.8 mm from copper
# of any other net (IPC-2221B table 6-1, A6; the board's .kicad_dru makes KiCad hold it), and a
# cathode pad keeps 0.5 mm from its neighbours' strands, not just the class's 0.25.
T15 = math.tan(math.radians(15))
# K1 leaves between R-low (K0) and LR (the anode) at 15 degrees down, the one direction in which
# a strand keeps both at once: its ring lane runs at 6.0, 2.0 below the anode's centre, and turns
# at x 4.543, so the line passes 2.08 from the anode's centre and 1.76 from R-low's.
K1_TURN = (4.543, 6.00)
K1_OUT = (K1_TURN[0] + (PADREL[9][1] - K1_TURN[1]) / T15, PADREL[9][1])    # level with the next LL

ENTRY = {"6": (-3.981, -9.80), "5": PR["5"], "7": gL1, "4": PR["4"], "8": gL2, "3": PR["3"],
         "9": gL3, "2": PR["2"], "0": gL4, "1": PR["1"]}
EXIT = {"6": (3.987, -10.35), "5": (3.987, -9.80), "7": PR["7"], "4": gR1, "8": PR["8"], "3": gR2,
        "9": PR["9"], "2": gR3, "0": PR["0"], "1": K1_OUT}
INSIDE = {
    "6": [PR["6"], (1.36, -10.35)],                        # over UL, down onto T, 45 degrees up over UR
    # under T, then 45 degrees up between T and UR (UR is K7: 1.69 from its centre) and over it
    "5": [(-1.0, -7.30), (0.9, -7.30), (3.4, -9.80)],
    "7": [(-1.0, -6.30), (1.2, -6.30)],
    "4": [(-1.0, -5.30), (1.6, -5.30)],
    "8": [(-1.2, -4.25), (1.6, -4.25)],
    "3": [(-1.5, -3.20), (1.5, -3.20)],                    # 0.575 above the pip hole's clearance
    "9": [(-1.5, 3.20), (1.5, 3.20)],
    "2": [(-1.2, 4.25), (1.6, 4.25)],
    "0": [(-1.0, 5.30), (1.6, 5.30)],
    "1": [(-1.0, K1_TURN[1]), K1_TURN],
}
INSIDE_LAST = {"6": [PR["6"]]}                              # M1 ends the bus on its top pad
# Between two rings a strand runs straight from one ring's exit to the next ring's entry, except
# where that line would pass a cathode pad closer than 0.5: K4 leaving between UR and R-high
# first runs level past R-high (K8), and K0 leaving R-low runs 15 degrees down, parallel to K1,
# and level into the next ring's gap under L-low (K2).
LEAVE = {"4": [(PADREL[4][0] + 0.3, gR1[1]), (PADREL[4][0] + 0.3 + (PADREL[12][1] - gR1[1]) / T15, PADREL[12][1])],
         "0": [(PADREL[6][0] + (gL4[1] - PADREL[6][1]) / T15, gL4[1])]}
ORDER = ["6", "5", "7", "4", "8", "3", "9", "2", "0", "1"]

# The crossing of the colon column between H1 and M10, on the back. The four lamp pads are 185 V,
# so a strand keeps 0.8 from each: two lanes fit between the upper lamp's pads, six between the
# lamps and two between the lower lamp's pads, and none above the upper lamp, where the standoff
# H3's keep-out (see the holes below) meets the lamp's clearance with no room left. Lanes are set
# from the lamp pads, each group centred in its gap.
_u1, _u2, _l1, _l2 = (COLON_Y[0] - 2.5, COLON_Y[0] + 2.5, COLON_Y[1] - 2.5, COLON_Y[1] + 2.5)
LANE = {"6": (_u1 + _u2) / 2 - 0.275, "5": (_u1 + _u2) / 2 + 0.275}
for k, d in enumerate(("7", "4", "8", "3", "9", "2")):
    LANE[d] = (_u2 + _l1) / 2 + 0.9 * (k - 2.5)
LANE["0"], LANE["1"] = Y12 + 7.25, Y12 + PADREL[9][1]      # K1 runs level into M10's LL
# West of the lamps each strand drops at 45 degrees. The diagonals are parallel, 0.9 apart
# measured down the page (0.64 square to them), and the six of the middle gap all reach their
# lanes at XE, which keeps K7's diagonal 0.92 from the upper lamp's lower pad. East of the lamps
# they climb back at 45 degrees from COLON_X + 2.4 (K5 0.5 later, to keep 0.74 from K6) and run
# level into M10. K0 drops at 45 degrees to 0.65 above K1's 15-degree line; K1 needs neither.
XE = COLON_X - 0.785
XW, XR = COLON_X + 2.4, {"5": COLON_X + 2.9}
_c = {d: LANE[d] - XE for d in ("7", "4", "8", "3", "9", "2")}
_c["5"], _c["6"] = _c["7"] - 0.9, _c["7"] - 1.8


def colon_crossing(d, exit_pt, entry_pt):
    """The points between H1's exit and M10's entry for strand d, both ends excluded."""
    ey, ny = exit_pt[1], entry_pt[1]
    if d == "1":
        return []
    if d == "0":
        xe = COLON_X - 2.235
        west = [(xe - (LANE[d] - ey), ey), (xe, LANE[d])]
    else:
        west = [(ey - _c[d], ey), (LANE[d] - _c[d], LANE[d])]
    x0 = XR.get(d, XW)
    east = [(x0, LANE[d]), (x0 + abs(ny - LANE[d]), ny)]
    return west + east


rings = [(f"V{i + 1}", x, Y12) for i, x in enumerate(IN12_X)]
for d in ORDER:
    net = "K" + d
    pts = []
    # from XP11 straight into H10
    pin = XP11[ORDER.index(d)]
    pts.append(pin)
    for ri, (ref, cx, cy) in enumerate(rings):
        e = (cx + ENTRY[d][0], cy + ENTRY[d][1])
        if ri == 2:
            pts += colon_crossing(d, pts[-1], e)
        pts.append(e)
        last = ri == len(rings) - 1
        inner = rel(cx, cy, (INSIDE_LAST.get(d) if last else None) or INSIDE[d])
        pts += inner
        if last:
            # M1 ends the bus: stop at the pad instead of leaving the ring
            tp = (cx + PR[d][0], cy + PR[d][1])
            if pts[-1] != tp:
                # strands that touch a left pad already passed it; trim the interior run back
                if PR[d] in (ENTRY[d],):
                    pts = pts[:len(pts) - len(inner)]
                else:
                    pts.append(tp)
            break
        pts.append((cx + EXIT[d][0], cy + EXIT[d][1]))
        if ri != 1:                                         # H1's strands leave into the colon crossing
            pts += rel(cx, cy, LEAVE.get(d, []))
    B.track(net, "B.Cu", pts, LV)


# ======================================================================== the ИН-17 bundles (XP12)
def wrap(net, layer, pin, lane_x, pad, turn_y=3.6, approach="down"):
    """From a top pin, 45 degrees to a vertical lane, down it, then into the pad. A lane that
    ends within 0.05 of the pad's centre stops there, inside the pad, with no jog."""
    px, py = pin
    tx, ty = pad
    dx = lane_x - px
    pts = [(px, py), (px, turn_y)]
    pts.append((lane_x, turn_y + abs(dx)))
    if approach == "down":
        pts.append((lane_x, ty))
        if abs(lane_x - tx) > 0.05:
            pts.append((tx, ty))
    B.track(net, layer, pts, LV)


def top_down(net, layer, pin, pad, turn_y=3.6, lane_x=None):
    """From a top pin, 45 degrees across, then straight down onto a pad."""
    wrap(net, layer, pin, pad[0] if lane_x is None else lane_x, pad, turn_y)


S10, S1 = ("V5", IN17_X[0], Y17), ("V6", IN17_X[1], Y17)
KB = dict(zip(P.HEADERS["12"][:10], XP12_S))
# Every lane is set from its own tube's centre, so the bundles follow the tubes. The pins sit
# centred between the two tubes; each bundle leaves them at 45 degrees and keeps its order, so
# no line crosses another on its face.
# S10 on the back: 7 6 5 4 down its left side, 3 2 1 0 from above, 9 8 down its right side
# past the anode, which is 185 V: K9's lane keeps 0.85 from the anode pad (A6, 0.8).
# S1 on the front: the same pins, mirrored logic - 7 6 5 4 come down between the tubes, right of
# S10's anode line; 3 2 1 0 from above; 9 8 down S1's right side. Both tubes use the same lanes.
# Cathode pads keep 0.5 from other strands: K4's lane 0.50 from pad 3, and the lanes of 3 and 0
# stand 0.02 outside their pads' centres, so each passes the top pad beside it (2, 1) at 0.51.
s10, s1 = IN17_X
for ref, layer, cx in (("V5", "B.Cu", s10), ("V6", "F.Cu", s1)):
    for d, lane in (("7", -5.705), ("6", -5.205), ("5", -4.705), ("4", -4.205)):
        wrap("KS" + d, layer, KB["KS" + d], cx + lane, B.P(ref, d))
    for d, lane in (("3", -2.80), ("2", None), ("1", None), ("0", 2.80)):
        top_down("KS" + d, layer, KB["KS" + d], B.P(ref, d), lane_x=None if lane is None else cx + lane)
    for d, lane in (("9", 4.55), ("8", 5.05)):
        wrap("KS" + d, layer, KB["KS" + d], cx + lane, B.P(ref, d))

# ======================================================================== the ИН-15 pair (XP12 pins 14-31)
AM = dict(zip(P.HEADERS["12"][13:21], XP12_AM))
PM = dict(zip(P.HEADERS["12"][21:], XP12_PM))
b15, a15 = IN15_X                           # the lanes below are set from each tube's centre
pad_of = lambda ref, net: next(B.P(ref, k) for k, v in PT[ref].pins.items() if v == net)
for net, lane in ((P.IN15B["AMP"], b15 - 8.1), (P.IN15B["OHM"], b15 - 7.6), (P.IN15B["SIEMENS"], b15 - 7.1)):
    wrap(net, "B.Cu", AM[net], lane, pad_of("V9", net))
for g in ("VOLT", "HENRY", "HERTZ"):
    top_down(P.IN15B[g], "B.Cu", AM[P.IN15B[g]], pad_of("V9", P.IN15B[g]))
for net, lane in ((P.IN15B["FARAD"], b15 + 7.2), (P.IN15B["WATT"], b15 + 7.7)):
    wrap(net, "B.Cu", AM[net], lane, pad_of("V9", net))
for net, lane in ((P.IN15A["NANO"], a15 - 8.7), (P.IN15A["PCT"], a15 - 8.2), (P.IN15A["PI"], a15 - 7.7), (P.IN15A["KILO"], a15 - 7.15)):
    wrap(net, "B.Cu", PM[net], lane, pad_of("V10", net))
for g in ("MEGA", "MILLI", "PLUS"):
    top_down(P.IN15A[g], "B.Cu", PM[P.IN15A[g]], pad_of("V10", P.IN15A[g]))
for net, lane in ((P.IN15A["MINUS"], a15 + 7.1), (P.IN15A["P"], a15 + 7.6), (P.IN15A["MICRO"], a15 + 8.1)):
    wrap(net, "B.Cu", PM[net], lane, pad_of("V10", net))

# ======================================================================== anodes, LEDs, colon
RUN_A, RUN_L = 31.4, 38.4                   # the anode runs and the LED runs, below the rings / LEDs


def down_to(net, layer, src, pin, run_y, width=None):
    """Down from src to run_y, across to the pin's column, down onto the pin."""
    pts = [src, (src[0], run_y), (pin[0], run_y), pin] if abs(src[0] - pin[0]) > 1e-6 else [src, pin]
    B.track(net, layer, pts, width)


X21 = dict(zip(P.HEADERS["21"], XP21))
X23 = dict(zip(P.HEADERS["23"], XP23))
X24 = dict(zip(P.HEADERS["24"], XP24))
X25 = dict(zip(P.HEADERS["25"], XP25))
for i, (refV, tube) in enumerate((("V1", "H10"), ("V2", "H1"), ("V3", "M10"), ("V4", "M1"))):
    hub = X21 if i < 2 else X23
    down_to("ANODE_" + tube, "B.Cu", B.P(refV, 7), hub["ANODE_" + tube], RUN_A)
    down_to(f"BL_A{i + 1}", "B.Cu", B.P(f"HL{i + 1}", 2), hub[f"BL_A{i + 1}"], RUN_L)
# S10: anode on the FRONT (the back is S10's own wrap), a jog right past pad 9, then down. The
# jog is 1.85, so the line keeps 0.9 from pad 9's bare copper (A6, 0.8).
a = B.P("V5", "A")
xa, pa = a[0] + 1.85, X24["ANODE_S10"]
B.track("ANODE_S10", "F.Cu", [a, (xa, a[1] + 1.85), (xa, YB - 3.6 - abs(pa[0] - xa)), (pa[0], YB - 3.6), pa])
down_to("BL_A5", "B.Cu", B.P("HL5", 2), X24["BL_A5"], RUN_L)
# S1: anode on the back, out to the right, down, and back under the tube
a = B.P("V6", "A")
B.track("ANODE_S1", "B.Cu", [a, (a[0] + 2.2, a[1]), (a[0] + 2.2, RUN_A), (X24["ANODE_S1"][0], RUN_A), X24["ANODE_S1"]])
down_to("BL_A6", "B.Cu", B.P("HL6", 2), X24["BL_A6"], RUN_L)
# AM / PM and the m
down_to("ANODE_AM", "B.Cu", B.P("V9", 7), X25["ANODE_AM"], RUN_A)
down_to("ANODE_PM", "B.Cu", B.P("V10", 7), X25["ANODE_PM"], RUN_A)
down_to("BL_A7", "B.Cu", B.P("HL7", 2), X25["BL_A7"], RUN_L)
down_to("BL_A8", "B.Cu", B.P("HL8", 2), X25["BL_A8"], RUN_L)
B.track("M_A", "B.Cu", [B.P("HL9", 2), X25["M_A"]])
# the colon, on the front: it sits inside the ИН-12 bus, so its lines cannot cross the back
X22 = dict(zip(P.HEADERS["22"], XP22))
u1, u2, l1, l2 = B.P("V7", 1), B.P("V7", 2), B.P("V8", 1), B.P("V8", 2)
# COLON_U leaves the top lamp to the left and runs down outermost; COLON_L leaves the lower lamp
# to the left inside it; the return joins the two lamps on the right and drops to its pin. Each
# passes the other lamp's bare pads at 0.85 (A6, 0.8), and COLON_U keeps 0.7 from COLON_L.
xu, xl, xr = COLON_X - 3.1, COLON_X - 2.1, COLON_X + 2.1
B.track("COLON_U", "F.Cu", [u1, (xu, u1[1]), (xu, YB - 3.4), X22["COLON_U"]])
B.track("COLON_L", "F.Cu", [l1, (xl, l1[1]), (xl, YB - 3.9), (X22["COLON_L"][0], YB - 2.5), X22["COLON_L"]])
B.track("COLON_RET", "F.Cu", [u2, (xr, u2[1]), (xr, l2[1]), l2])
B.track("COLON_RET", "F.Cu", [(xr, l2[1]), (xr, YB - 5.3), (X22["COLON_RET"][0], YB - 3.84), X22["COLON_RET"]])

# ======================================================================== the front pour
B.zone("BL_K", "F.Cu", clearance=0.5, min_th=0.3, gap=0.5, bridge=0.6)

# ======================================================================== silkscreen
# White on black mask (the owner's order, and his working unit's). The fab's minimums, Rezonit's
# and JLC's alike: lines 0.15 mm, text 1.0 mm tall with a 0.15 mm stroke, nothing on a pad.
# pcbkit strokes text at 0.15 x its height, so 1.0 mm is the smallest size used here.
#
# WHO SEES WHICH FACE, AND WHEN:
#   * the FRONT is where the tubes, the lamps and the LEDs go in, and the clock's owner sees it
#     between the tubes for years. So it carries only what fitting a part needs, and almost all
#     of it is where the part itself will cover it: each tube's name inside its ring, the
#     ИН-12's anode ring (its key), the ИН-17's gap ring, the lamps' dot-and-A, the LEDs' K.
#     The two conventions and the 185 V mark go in the bottom band, behind the fascia.
#   * the BACK is where every joint is soldered, and it faces TS06-DRV - the words go here:
#     the title, the strips (names beside pin 1, the footprint's corner mark on pin 1), the
#     conventions again, the standoffs, the high voltage, the tube names for the solderer.
F_SILK, B_SILK = "F.SilkS", "B.SilkS"
SILK_W = 0.15


def warn_triangle(x, top, side, layer, width):
    """An equilateral warning triangle, apex at (x, top), with a '!' in it - the stroke font has
    no warning sign, so it is drawn."""
    h = side * math.sqrt(3) / 2
    for a, b in (((x, top), (x - side / 2, top + h)), ((x - side / 2, top + h), (x + side / 2, top + h)),
                 ((x + side / 2, top + h), (x, top))):
        B.line(round(a[0], 4), round(a[1], 4), round(b[0], 4), round(b[1], 4), layer, width)
    sz = round(side * 0.36, 2)
    B.text("!", x, round(top + h * 0.62, 3), layer, sz)


# --- the front
TUBE_NAMES = {"V1": "H10", "V2": "H1", "V3": "M10", "V4": "M1", "V5": "S10", "V6": "S1"}
for ref in ("V1", "V2", "V3", "V4"):                  # above the pip hole, inside the socket's outline
    f, x, y = B.placed[ref]
    B.text(TUBE_NAMES[ref], x, y - 5.0, F_SILK, 1.5)
for ref in ("V5", "V6"):                              # between the ИН-17's pad columns, above the anode
    f, x, y = B.placed[ref]
    B.text(TUBE_NAMES[ref], x, y - 1.3, F_SILK, 1.2)
for ref, kind, name in (("V9", "ИН-15Б", "AM"), ("V10", "ИН-15А", "PM")):   # two different tubes: say which
    f, x, y = B.placed[ref]
    B.text(kind, x, y - 4.3, F_SILK, 1.2)
    B.text(name, x, y + 5.0, F_SILK, 1.5)
# the bottom band, behind the fascia: which way round the square pad is, and the anode voltage
# on the strip joints
B.text("LED: □ pad = K", 35.0, 40.5, F_SILK, 1.0)
B.text("ИНС-1: □ pad = A •", 35.0, 42.3, F_SILK, 1.0)
warn_triangle(93.0, 39.3, 3.8, F_SILK, SILK_W)
B.text("185 V", 99.6, 41.0, F_SILK, 1.5)

# --- the back (the stroke font mirrors it, so it reads from the back)
B.text("TERMINAL-06 TS06-DISP rev B", 27.0, 1.9, B_SILK, 1.5)
B.text("30.09.26 · this face to TS06-DRV", 27.0, 4.3, B_SILK, 1.0)
for k, t in enumerate(("LED HL1-HL9: □ pad = K (cathode)",
                       "ИНС-1 V7 V8: □ pad = A (anode, the dot)",
                       "solder XP11-XP25 plugged into TS06-DRV")):
    B.text(t, 79.0, 1.3 + 2.0 * k, B_SILK, 1.0)
B.text("standoffs", 98.5, 33.2, B_SILK, 1.0)
B.text("4 × M3, 11 mm", 98.5, 35.0, B_SILK, 1.0)
# the strips: each name beside its pin 1, 0.25 clear of the strip's outline
for ref, pins in (("XP21", XP21), ("XP22", XP22), ("XP23", XP23), ("XP24", XP24), ("XP25", XP25)):
    B.text(ref, pins[0][0] - 3.6, YB, B_SILK, 1.0)
B.text("XP11", 2.45, XP11[-1][1] + 2.35, B_SILK, 1.0)                           # under its last pin
B.text("XP12", _XP12[0][0] - 3.6, YT, B_SILK, 1.0)
# the tubes, for the one soldering their pins: under each ИН-12 ring (its inside carries the bus),
# inside the other rings, whose insides are clear on this face
for ref in ("V1", "V2", "V3", "V4"):
    f, x, y = B.placed[ref]
    B.text(TUBE_NAMES[ref], x - 2.0, 29.8, B_SILK, 1.5)
for ref in ("V5", "V6"):
    f, x, y = B.placed[ref]
    B.text(TUBE_NAMES[ref], x, y - 1.3, B_SILK, 1.2)
for ref, kind, name in (("V9", "ИН-15Б", "AM"), ("V10", "ИН-15А", "PM")):
    f, x, y = B.placed[ref]
    B.text(kind, x, y - 4.3, B_SILK, 1.2)
    B.text(name, x, y + 5.0, B_SILK, 1.5)
# the LEDs' cathodes and the lamps' anodes, beside the square pads
for i in range(9):
    f, x, y = B.placed[f"HL{i + 1}"]
    B.text("K", x - 3.0, y, B_SILK, 1.0)
for ref in ("V7", "V8"):
    x, y = B.P(ref, 1)
    B.text("A", x - 2.55, y, B_SILK, 1.0)
# the standoffs' seats, and the voltage on the tube pins
STANDOFF_MARK = 2.6
for hx, hy, hd in B.holes:
    B.circle(hx, hy, STANDOFF_MARK, B_SILK, SILK_W)
warn_triangle(140.8, 24.5, 5.5, B_SILK, 0.2)
B.text("185 V", 140.8, 32.0, B_SILK, 2.0)
B.text("unplug,", 140.8, 35.2, B_SILK, 1.0)
B.text("wait 15 s", 140.8, 36.9, B_SILK, 1.0)


def widen_silk(tree):
    """Every silkscreen stroke of a footprint to at least SILK_W: the strips come from KiCad's
    stock headers, drawn at 0.12."""
    for n in S.walk(tree):
        if n[0] in ("fp_line", "fp_arc", "fp_circle", "fp_rect", "fp_poly"):
            ly, st = S.find(n, "layer"), S.find(n, "stroke")
            w = S.find(st, "width") if st else None
            if ly and S.unq(ly[1]).endswith("SilkS") and w and float(w[1]) < SILK_W:
                w[1] = S.num(SILK_W)
    return tree


for ref, (f, x, y) in B.placed.items():
    widen_silk(f.tree)


# ======================================================================== the checks this file adds
HV_PREFIX = ("ANODE_", "COLON_")
is_hv = lambda n: bool(n) and n.startswith(HV_PREFIX)
is_cath = lambda n: bool(n) and (B.cls(n) == "CATH")


def copper_problems():
    """IPC-2221B A6 and the cathode margin, measured on the generator's own geometry. KiCad holds
    the first too (TS06-DISP.kicad_dru), for the pour as well; these catch a track before then.
      * a bare pad and copper of another net, either of them 185 V: 0.8
      * a cathode pad and another net's copper: 0.5
      * no copper within HOLE_KEEPOUT of a standoff hole's centre, on either face"""
    bad = []
    for layer in ("F.Cu", "B.Cu"):
        its = B.items(layer)
        for i, (ni, gi, ki, li) in enumerate(its):
            if ki != "pad":
                continue
            for j, (nj, gj, kj, lj) in enumerate(its):
                if i == j or ni == nj or (kj == "pad" and j < i):
                    continue
                need = 0.8 if (is_hv(ni) or is_hv(nj)) else 0.5 if (is_cath(ni) or (kj == "pad" and is_cath(nj))) else 0
                if need and K.dist(gi, gj) < need - 1e-6:
                    bad.append(f"[{layer}] pad {li} ({ni}) is {K.dist(gi, gj):.3f} from {lj} ({nj}), wants {need}")
    for hx, hy, hd in B.holes:
        for layer in ("F.Cu", "B.Cu"):
            for n, g, k, lab in B.items(layer):
                d = K.dist(([(hx, hy)], 0), g)
                if d < HOLE_KEEPOUT - 1e-6:
                    bad.append(f"[{layer}] {lab} is {d:.3f} from the standoff hole at ({hx}, {hy}), inside its keep-out")
    return bad


def text_box(t, x, y, size, rot=0):
    """A text's box. KiCad 10's stroke font, measured on this board: 0.82-0.93 x the height per
    Latin character, 0.99 for Cyrillic, 1.15-1.7 x the height tall with the stroke (brackets and
    descenders the most). tools/audit.py's box (0.78 per character) is smaller, so a pass here is
    a pass there."""
    w, h = max(len(t), 1) * size * 0.93 + size * 0.15, size * 1.5
    return (x - w / 2, y - h / 2, x + w / 2, y + h / 2) if round(rot) % 180 == 0 else (x - h / 2, y - w / 2, x + h / 2, y + w / 2)


def fp_silk_points(ref, step=0.1):
    """Points along a placed footprint's silkscreen, arcs followed round their circle (pcbkit's
    silk_points joins an arc's three points with chords, which cut inside a tube's outline)."""
    f, x0, y0 = B.placed[ref]
    out = []
    P2 = lambda n, k: (float(S.find(n, k)[1]), float(S.find(n, k)[2]))

    def run(a, b, ly):
        k = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step))
        out.extend((x0 + a[0] + (b[0] - a[0]) * i / k, y0 + a[1] + (b[1] - a[1]) * i / k, ly) for i in range(k + 1))

    for n in f.tree:
        if not isinstance(n, list) or not n or n[0] not in ("fp_line", "fp_rect", "fp_circle", "fp_arc", "fp_poly"):
            continue
        lyn = S.find(n, "layer")
        if not lyn or not S.unq(lyn[1]).endswith("SilkS") or K.Board._silk_on_pad(n, f):
            continue
        ly = S.unq(lyn[1])
        if n[0] == "fp_line":
            run(P2(n, "start"), P2(n, "end"), ly)
        elif n[0] == "fp_rect":
            a, b = P2(n, "start"), P2(n, "end")
            for p, q in ((a, (b[0], a[1])), ((b[0], a[1]), b), (b, (a[0], b[1])), ((a[0], b[1]), a)):
                run(p, q, ly)
        elif n[0] == "fp_poly":
            xy = [(float(q[1]), float(q[2])) for q in S.find_all(S.find(n, "pts"), "xy")]
            for p, q in zip(xy, xy[1:] + xy[:1]):
                run(p, q, ly)
        else:
            if n[0] == "fp_circle":
                (ux, uy), e = P2(n, "center"), P2(n, "end")
                r, a0, sweep = math.hypot(e[0] - ux, e[1] - uy), 0.0, math.tau
            else:                                      # the circle through start, mid and end
                (ax, ay), (mx, my), (bx, by) = P2(n, "start"), P2(n, "mid"), P2(n, "end")
                d = 2 * (ax * (my - by) + mx * (by - ay) + bx * (ay - my))
                ux = ((ax * ax + ay * ay) * (my - by) + (mx * mx + my * my) * (by - ay) + (bx * bx + by * by) * (ay - my)) / d
                uy = ((ax * ax + ay * ay) * (bx - mx) + (mx * mx + my * my) * (ax - bx) + (bx * bx + by * by) * (mx - ax)) / d
                r = math.hypot(ax - ux, ay - uy)
                a0, am, a1 = (math.atan2(p[1] - uy, p[0] - ux) for p in ((ax, ay), (mx, my), (bx, by)))
                sweep = (a1 - a0) % math.tau
                if (am - a0) % math.tau > sweep:      # the arc runs the other way round
                    sweep -= math.tau
            k = max(8, int(abs(sweep) * r / step))
            out += [(x0 + ux + r * math.cos(a0 + sweep * i / k), y0 + uy + r * math.sin(a0 + sweep * i / k), ly)
                    for i in range(k + 1)]
    return out


def silk_problems():
    """The fab's minimums and the legibility of what this file prints: every text 1.0 mm or more
    with a 0.15 mm stroke, every line 0.15 mm or more; no text on a pad, a hole, another text or
    a footprint's outline; nothing within 0.3 of the edge."""
    bad = []
    texts, marks = [], []
    for kind, ly, d in B.gfx:
        if kind == "text":
            t, x, y, size, th, mirror, rot, just = d
            if size < 1.0 - 1e-9 or th < SILK_W - 1e-9:
                bad.append(f'"{t}" on {ly}: {size} mm text, {th} mm stroke, under the fab minimum')
            texts.append((t, ly, text_box(t, x, y, size, rot)))
        elif kind == "line":
            if d[4] < SILK_W - 1e-9:
                bad.append(f"line on {ly} is {d[4]} mm")
            marks.append((ly, [(d[0], d[1]), (d[2], d[3])], d[4] / 2))
        elif kind == "circle":
            x, y, r, w = d
            if w < SILK_W - 1e-9:
                bad.append(f"circle on {ly} is {w} mm")
            marks.append((ly, [(x + r * math.cos(a * math.tau / 72), y + r * math.sin(a * math.tau / 72)) for a in range(73)], w / 2))
    outline = {F_SILK: [], B_SILK: []}
    for ref in B.placed:
        for x, y, ly in fp_silk_points(ref):
            outline[ly].append((x, y))
    hit = lambda bx, px, py, m: bx[0] - m <= px <= bx[2] + m and bx[1] - m <= py <= bx[3] + m
    for i, (t, ly, bx) in enumerate(texts):
        cu = ly[0] + ".Cu"
        if bx[0] < 0.3 or bx[1] < 0.3 or bx[2] > W - 0.3 or bx[3] > H - 0.3:
            bad.append(f'"{t}" on {ly} is within 0.3 of the board edge')
        for p in B.pads:
            if p.kind == "np_thru_hole" or p.on(cu):
                r = (p.drill if p.kind == "np_thru_hole" else max(p.w, p.h)) / 2 + 0.15
                if bx[0] - r < p.x < bx[2] + r and bx[1] - r < p.y < bx[3] + r:
                    bad.append(f'"{t}" on {ly} is on or beside pad {p.ref}.{p.name}')
        for hx, hy, hd in B.holes:
            if bx[0] - hd / 2 - 0.3 < hx < bx[2] + hd / 2 + 0.3 and bx[1] - hd / 2 - 0.3 < hy < bx[3] + hd / 2 + 0.3:
                bad.append(f'"{t}" on {ly} is on a standoff hole')
        for t2, ly2, bx2 in texts[i + 1:]:
            if ly2 == ly and bx[0] < bx2[2] and bx2[0] < bx[2] and bx[1] < bx2[3] and bx2[1] < bx[3]:
                bad.append(f'"{t}" and "{t2}" overlap on {ly}')
        if any(hit(bx, px, py, 0.1) for px, py in outline[ly]):
            bad.append(f'"{t}" on {ly} runs into a footprint outline')
        for ly2, pts, r in marks:
            if ly2 == ly and t != "!" and any(hit(bx, px, py, r + 0.1) for px, py in pts):
                bad.append(f'"{t}" on {ly} runs into a line or circle')
    for ly, pts, r in marks:
        cu = ly[0] + ".Cu"
        for p in B.pads:
            if p.kind != "np_thru_hole" and p.on(cu) and min(K.dist(([q], r), p.geom()) for q in pts) < 0.15:
                bad.append(f"a silk mark on {ly} runs within 0.15 of pad {p.ref}.{p.name}")
        if any(px < r + 0.3 or py < r + 0.3 or px > W - r - 0.3 or py > H - r - 0.3 for px, py in pts):
            bad.append(f"a silk mark on {ly} is within 0.3 of the board edge")
    return bad


def written_silk_problems(text):
    """The written board, read back: every silkscreen stroke and every visible silkscreen text,
    the footprints' included, at the fab's minimums."""
    bad = []
    tree = S.parse(text)
    for n in S.walk(tree):
        if not n or n[0] not in ("fp_line", "fp_arc", "fp_circle", "fp_rect", "fp_poly", "gr_line", "gr_arc", "gr_circle",
                                 "gr_rect", "gr_poly", "fp_text", "gr_text", "property"):
            continue
        ly = S.find(n, "layer")
        if not ly or not S.unq(ly[1]).endswith("SilkS"):
            continue
        if n[0] in ("fp_text", "gr_text", "property"):
            if S.find(n, "hide") is not None or "hide" in n:
                continue
            font = S.find(S.find(n, "effects") or [], "font") or []
            sz, th = S.find(font, "size"), S.find(font, "thickness")
            if not sz or float(sz[2]) < 1.0 - 1e-9 or not th or float(th[1]) < SILK_W - 1e-9:
                bad.append(f"text {n[1]} on {S.unq(ly[1])} under 1.0 mm / 0.15 mm")
        else:
            st = S.find(n, "stroke")
            w = S.find(st, "width") if st else None
            if not w or float(w[1]) < SILK_W - 1e-9:
                bad.append(f"{n[0]} on {S.unq(ly[1])} is {w[1] if w else '?'} mm")
    return bad


# ======================================================================== what KiCad is told
# The rule the pair's two boards share, word for word. KiCad 10 wants a unit on the number: given
# "(min 0.8)" its parser stops with "Missing units for '0.8'", and kicad-cli's DRC and zone fill
# then drop the whole file WITHOUT a word and run on the net classes alone (30.09.26: the pour
# came out 0.6 from every anode pad, and a track 0.70 from one passed).
DRU = """(version 1)
(rule "HV pad clearance, IPC-2221B A6"
  (condition "A.Type == 'Pad' && A.hasNetclass('HV') && A.Net != B.Net")
  (constraint clearance (min 0.8mm)))
"""


def keepouts():
    """A KiCad rule area round each standoff hole, both faces, no tracks, no vias and no pour: a
    polygon drawn OUTSIDE the HOLE_KEEPOUT circle (so the circle is kept everywhere), clipped to
    the board outline."""
    n = 48
    rr = HOLE_KEEPOUT / math.cos(math.pi / n)
    out = []
    for i, (hx, hy, hd) in enumerate(B.holes):
        poly = [(hx + rr * math.cos(k * math.tau / n), hy + rr * math.sin(k * math.tau / n)) for k in range(n)]
        for axis, lim, keep_below in ((0, 0.0, False), (0, W, True), (1, 0.0, False), (1, H, True)):
            clipped = []
            for k in range(len(poly)):
                a, b = poly[k - 1], poly[k]
                ina = a[axis] <= lim if keep_below else a[axis] >= lim
                inb = b[axis] <= lim if keep_below else b[axis] >= lim
                if ina != inb:
                    t = (lim - a[axis]) / (b[axis] - a[axis])
                    clipped.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
                if inb:
                    clipped.append(b)
            poly = clipped
        pts = " ".join("(xy %s %s)" % (S.num(round(x, 4)), S.num(round(y, 4))) for x, y in poly)
        out.append(f'\t(zone\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(uuid "{B.U("keepout%d" % i)}")\n'
                   f'\t\t(name "H{i + 1} standoff keep-out")\n\t\t(hatch edge 0.5)\n\t\t(connect_pads\n\t\t\t(clearance 0)\n\t\t)\n'
                   f'\t\t(min_thickness 0.25)\n\t\t(keepout\n\t\t\t(tracks not_allowed)\n\t\t\t(vias not_allowed)\n'
                   f'\t\t\t(pads allowed)\n\t\t\t(copperpour not_allowed)\n\t\t\t(footprints allowed)\n\t\t)\n'
                   f'\t\t(placement\n\t\t\t(enabled no)\n\t\t\t(sheetname "")\n\t\t)\n'
                   f'\t\t(fill\n\t\t\t(thermal_gap 0.5)\n\t\t\t(thermal_bridge_width 0.5)\n\t\t\t(island_removal_mode 0)\n\t\t)\n'
                   f'\t\t(polygon\n\t\t\t(pts\n\t\t\t\t{pts}\n\t\t\t)\n\t\t)\n\t)')
    return "\n".join(out) + "\n"


def write_all(out):
    n = B.write(out, title="TS06-DISP", rev="B", date="2026-09-30",
                comment="TERMINAL-06 display board, THT pair with TS06-DRV")
    with open(out, encoding="utf8") as fh:
        text = fh.read()
    tail = "\t(embedded_fonts no)\n)\n"
    assert text.endswith(tail)
    text = text[:-len(tail)] + keepouts() + tail
    with open(out, "w", encoding="utf8", newline="\n") as fh:
        fh.write(text)
    pro = out.replace(".kicad_pcb", ".kicad_pro")
    B.write_project(pro)
    # the fab's text minimum, so KiCad's DRC holds it as well
    with open(pro, encoding="utf8") as fh:
        js = json.load(fh)
    js["board"]["design_settings"]["rules"].update({"min_text_height": 1.0, "min_text_thickness": SILK_W})
    with open(pro, "w", encoding="utf8", newline="\n") as fh:
        json.dump(js, fh, indent=2)
    with open(out.replace(".kicad_pcb", ".kicad_dru"), "w", encoding="utf8", newline="\n") as fh:
        fh.write(DRU)
    # the strips' rotated variants, with their silkscreen widened as on the board
    B.write_library()
    for ref, (f, x, y) in B.placed.items():
        r = B.librot(f)
        if r and f.name.startswith("TS06_PinHeader_"):
            name = B.libname(f)
            p = os.path.join(K.PRETTY, name + ".kicad_mod")
            with open(p, encoding="utf8") as fh:
                t = widen_silk(S.parse(fh.read()))
            with open(p, "w", encoding="utf8", newline="\n") as fh:
                fh.write(S.dump(t) + "\n")
    return n, text


if __name__ == "__main__":
    bad = B.check()
    mine = copper_problems() + silk_problems()
    for b in mine:
        print("  [CHECK]", b)
    n, text = write_all(OUT)
    late = written_silk_problems(text)
    for b in late:
        print("  [CHECK]", b)
    png = os.path.join(os.path.dirname(OUT), "copper.png")
    B.plot(png, ppm=8, color=lambda n: ((255, 90, 90) if n.startswith(("ANODE", "COLON")) else
                                         (80, 170, 255) if n.startswith(("K", "CAT")) else
                                         (180, 110, 255) if n.startswith(("BL", "M_A")) else (90, 220, 120)))
    print(f"wrote {os.path.relpath(OUT, ROOT)}: {len(B.placed)} parts, {n} nets, {len(B.tracks)} segments, 0 vias")
    total = len(bad) + len(mine) + len(late)
    print(f"check: {total} problem(s)")
    sys.exit(1 if total else 0)
