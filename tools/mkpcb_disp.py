#!/usr/bin/env python3
"""TS06-DISP: the display board of the through-hole pair - tubes, colon, backlight, headers.

    python3 tools/mkpcb_disp.py            # PCB/TS06-DISP/TS06-DISP.kicad_pcb (+ .kicad_pro, copper.png)

Nothing on this board is placed by a packer or routed by a router. Every coordinate below is
chosen, and the reason is written beside it; tools/pcbkit.py only writes what this file says.

GEOMETRY. The board stands vertical with the tubes on its front, in the plane the inherited
tube board occupied. Tube positions are the reviewed assembly's (3d/Clock.FCStd), exactly as
tools/mkpcb_main.py carried them: board x = world X, board y = TOP - world Y. The board is the
tube band and no more - 176 x 43 mm, like AlexGyver's 99 x 34 mm tube half.

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
  * THE ИН-15 PAIR is wrapped from above by XP13 / XP14 on the back face; the anode leaves
    downward through the gap the wrap leaves at the bottom.
  * ANODES AND LEDs go straight down to five short bottom strips.
  * THE FRONT FACE is one pour, BL_K, the LEDs' common cathode - there is no ground on this
    board, so the front is the LED return and nothing else, and it reads as one uniform black
    field around the tubes. Only five things cross it: the three colon lines (the colon
    sits inside the ИН-12 bus), S10's anode and S1's cathode bundle.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbkit as K
import ts06pair as P

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
NAME = "TS06-DISP"
OUT = os.environ.get("TS06_OUT") or os.path.join(ROOT, "PCB", NAME, NAME + ".kicad_pcb")

W, H = 176.0, 44.0
TOP = 78.0                                  # world Y of the top edge: 1 mm above the ИН-15 glass courtyards
IN12_WY = 40.10 + 20.066                    # the inherited board's tube centre height, world Y
Y12 = round(TOP - IN12_WY, 4)               # 16.834: ИН-12 and ИН-15 centres
Y17 = round(Y12 + 5.375, 4)                 # ИН-17 centres sit 5.375 below
IN12_X = [13.21, 36.57, 63.99, 87.37]
IN17_X = [104.605, 117.605]
IN15_X = [135.0, 156.0]
COLON_X = 50.535
COLON_Y = [TOP - 66.5, TOP - 52.5]          # lamp centres (FreeCAD)
LED_Y = round(TOP - (IN12_WY - 17.67), 4)   # 34.504, as TS06-MAIN had it
LED17_Y = round(TOP - (IN12_WY - 5.375 - 13.3), 4)
M_X = 145.5                                 # the "m" LED, beneath the AM/PM pair
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
# XP12 along the top: ten pins over the ИН-17 pair, eight over ИН-15Б, ten over ИН-15А.
_XP12 = strip("XP12", 99.57, YT)
XP12, XP13, XP14 = _XP12[:10], _XP12[10:18], _XP12[18:]
# The bottom strips, under the tubes they serve (see the routing of each).
LX = lambda i: IN12_X[i] + 1.27
XP21 = strip("XP21", 11.94, YB)                         # BL_K under HL1's cathode, BL_A1 under its anode, then H10's anode...
XP22 = strip("XP22", 47.99, YB)                         # the colon, F.Cu
XP23 = strip("XP23", 69.28, YB)                         # M10 / M1
XP24 = strip("XP24", 107.335, YB)                       # S10 / S1
XP25 = strip("XP25", M_X - 6.35, YB)                    # AM, m, PM: HL9 sits exactly over pins 3 and 4

# Standoff holes (M3), where nothing else is: the two bottom corners, the top right corner, and
# the top of the colon column - between the H1 and M10 glass, where a screw head clears both.
for i, (hx, hy) in enumerate(((3.5, 40.5), (172.5, 40.5), (COLON_X, 3.3), (172.5, 5.5))):
    B.place(f"H{i + 1}", "TS06_MountingHole_M3", hx, hy)
    B.holes.append((hx, hy, 3.2))


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
# between R-low (K0) and LR (the anode, 185 V): 1.7 mm from R-low's centre, 2.2 from the anode's
_u = ((PADREL[7][0] - PADREL[6][0]) / 3.919, (PADREL[7][1] - PADREL[6][1]) / 3.919)
gR4 = (PADREL[6][0] + 1.7 * _u[0], PADREL[6][1] + 1.7 * _u[1])

ENTRY = {"6": (-3.981, -9.80), "5": PR["5"], "7": gL1, "4": PR["4"], "8": gL2, "3": PR["3"],
         "9": gL3, "2": PR["2"], "0": gL4, "1": PR["1"]}
EXIT = {"6": (3.987, -10.35), "5": (3.987, -9.70), "7": PR["7"], "4": gR1, "8": PR["8"], "3": gR2,
        "9": PR["9"], "2": gR3, "0": PR["0"], "1": gR4}
INSIDE = {
    "6": [PR["6"]],                                         # over UL, down onto T, up over UR
    "5": [(-1.0, -7.30), (1.0, -7.30), G(PADREL[2], PADREL[3])],   # under T, out between T and UR
    "7": [(-1.0, -6.30), (1.2, -6.30)],
    "4": [(-1.0, -5.30), (1.6, -5.30)],
    "8": [(-1.2, -4.25), (1.6, -4.25)],
    "3": [(-1.5, -3.20), (1.5, -3.20)],                    # 0.575 above the pip hole's clearance
    "9": [(-1.5, 3.20), (1.5, 3.20)],
    "2": [(-1.2, 4.25), (1.6, 4.25)],
    "0": [(-1.0, 5.30), (1.6, 5.30)],
    "1": [(-1.0, 6.30), (1.5, 6.30)],
}
ORDER = ["6", "5", "7", "4", "8", "3", "9", "2", "0", "1"]
# Where each strand crosses the colon column between H1 and M10: in the gaps between the four
# lamp pads, which are 185 V and want 1.825 mm centre-to-strand. Relative to the ring line.
COLON_LANE = {"6": -12.00, "5": -11.40, "7": -6.34, "4": -1.50, "8": -0.50, "3": 0.50, "9": 1.50,
              "2": 2.50, "0": 7.25, "1": 7.95}

rings = [(f"V{i + 1}", x, Y12) for i, x in enumerate(IN12_X)]
for d in ORDER:
    net = "K" + d
    pts = []
    # from XP11 straight into H10
    pin = XP11[ORDER.index(d)]
    pts.append(pin)
    for ri, (ref, cx, cy) in enumerate(rings):
        e = (cx + ENTRY[d][0], cy + ENTRY[d][1])
        if ri == 0:
            pts.append(e)
        elif ri == 2:
            # through the colon column, between H1 and M10: clear H1's right column first, run
            # level past the four lamp pads, then drop into M10
            px = rings[1][1]
            last_exit = pts[-1]
            pts[-1:] = [last_exit, (px + 7.3, last_exit[1])]
            pts.append((COLON_X - 2.4, cy + COLON_LANE[d]))
            pts.append((COLON_X + 2.4, cy + COLON_LANE[d]))
            pts.append(e)
        else:
            pts.append(e)
        inner = rel(cx, cy, INSIDE[d])
        last = ri == len(rings) - 1
        if d in ("6",):
            pts += inner
        else:
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
    B.track(net, "B.Cu", pts, LV)


# ======================================================================== the ИН-17 bundles (XP12)
def wrap(net, layer, pin, lane_x, pad, turn_y=3.6, approach="down"):
    """From a top pin, 45 degrees to a vertical lane, down it, then into the pad."""
    px, py = pin
    tx, ty = pad
    dx = lane_x - px
    pts = [(px, py), (px, turn_y)]
    pts.append((lane_x, turn_y + abs(dx)))
    if approach == "down":
        pts.append((lane_x, ty))
        if abs(lane_x - tx) > 1e-6:
            pts.append((tx, ty))
    B.track(net, layer, pts, LV)


def top_down(net, layer, pin, pad, turn_y=3.6):
    """From a top pin, 45 degrees across, then straight down onto a pad."""
    wrap(net, layer, pin, pad[0], pad, turn_y)


S10, S1 = ("V5", IN17_X[0], Y17), ("V6", IN17_X[1], Y17)
KB = dict(zip(P.HEADERS["12"][:10], XP12))
# S10 on the back: 7 6 5 4 down its left side, 3 2 1 0 from above, 9 8 down its right side
# past the anode, which is 185 V and gets 0.6 mm.
for d, lane in (("7", 99.0), ("6", 99.5), ("5", 100.0), ("4", 100.5)):
    wrap("KS" + d, "B.Cu", KB["KS" + d], lane, B.P("V5", d))
for d in ("3", "2", "1", "0"):
    top_down("KS" + d, "B.Cu", KB["KS" + d], B.P("V5", d))
for d, lane in (("9", 109.0), ("8", 109.5)):
    wrap("KS" + d, "B.Cu", KB["KS" + d], lane, B.P("V5", d))
# S1 on the front: the same pins, mirrored logic - 7 6 5 4 come down between the tubes, right of
# S10's anode line; 3 2 1 0 from above; 9 8 down S1's right side.
for d, lane in (("7", 111.9), ("6", 112.4), ("5", 112.9), ("4", 113.4)):
    wrap("KS" + d, "F.Cu", KB["KS" + d], lane, B.P("V6", d))
for d in ("3", "2", "1", "0"):
    top_down("KS" + d, "F.Cu", KB["KS" + d], B.P("V6", d))
for d, lane in (("9", 122.0), ("8", 122.5)):
    wrap("KS" + d, "F.Cu", KB["KS" + d], lane, B.P("V6", d))

# ======================================================================== the ИН-15 pair (XP13, XP14)
AM = dict(zip(P.HEADERS["12"][10:18], XP13))
PM = dict(zip(P.HEADERS["12"][18:], XP14))
pad_of = lambda ref, net: next(B.P(ref, k) for k, v in PT[ref].pins.items() if v == net)
for net, lane in ((P.IN15B["AMP"], 126.9), (P.IN15B["OHM"], 127.4), (P.IN15B["SIEMENS"], 127.9)):
    wrap(net, "B.Cu", AM[net], lane, pad_of("V9", net))
for g in ("VOLT", "HENRY", "HERTZ"):
    top_down(P.IN15B[g], "B.Cu", AM[P.IN15B[g]], pad_of("V9", P.IN15B[g]))
for net, lane in ((P.IN15B["FARAD"], 142.2), (P.IN15B["WATT"], 142.7)):
    wrap(net, "B.Cu", AM[net], lane, pad_of("V9", net))
for net, lane in ((P.IN15A["NANO"], 147.3), (P.IN15A["PCT"], 147.8), (P.IN15A["PI"], 148.3), (P.IN15A["KILO"], 148.85)):
    wrap(net, "B.Cu", PM[net], lane, pad_of("V10", net))
for g in ("MEGA", "MILLI", "PLUS"):
    top_down(P.IN15A[g], "B.Cu", PM[P.IN15A[g]], pad_of("V10", P.IN15A[g]))
for net, lane in ((P.IN15A["MINUS"], 163.1), (P.IN15A["P"], 163.6), (P.IN15A["MICRO"], 164.1)):
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
# S10: anode on the FRONT (the back is S10's own wrap), a jog right past pad 9, then down
a = B.P("V5", "A")
B.track("ANODE_S10", "F.Cu", [a, (a[0] + 1.6, a[1] + 1.6), (a[0] + 1.6, YB - 5.1), (X24["ANODE_S10"][0], YB - 4.1), X24["ANODE_S10"]])
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
# to the left inside it; the return joins the two lamps on the right and drops to its pin.
xu, xl, xr = COLON_X - 2.94, COLON_X - 1.94, COLON_X + 1.94
B.track("COLON_U", "F.Cu", [u1, (xu, u1[1]), (xu, YB - 3.4), X22["COLON_U"]])
B.track("COLON_L", "F.Cu", [l1, (xl, l1[1]), (xl, YB - 3.9), (X22["COLON_L"][0], YB - 2.5), X22["COLON_L"]])
B.track("COLON_RET", "F.Cu", [u2, (xr, u2[1]), (xr, l2[1]), l2])
B.track("COLON_RET", "F.Cu", [(xr, l2[1]), (xr, YB - 5.3), (X22["COLON_RET"][0], YB - 3.84), X22["COLON_RET"]])

# ======================================================================== the front pour
B.zone("BL_K", "F.Cu", clearance=0.5, min_th=0.3, gap=0.5, bridge=0.6)

# ======================================================================== silkscreen
# The back is where the board is assembled and where it plugs in, so that is where the words go:
# the name, and each strip's reference beside its pin 1. The front carries the tube and LED
# outlines from the footprints and nothing else - it is the face the customer looks past.
B.text("TS06-DISP rev A", 35.0, H - 2.3, "B.SilkS", 1.0)
B.text("TERMINAL-06  display", 35.0, H - 0.9, "B.SilkS", 0.8)
for ref, pins in (("XP21", XP21), ("XP22", XP22), ("XP23", XP23), ("XP24", XP24), ("XP25", XP25)):
    B.text(ref, pins[0][0] - 3.1, YB, "B.SilkS", 0.8)                          # beside pin 1, clear of the outline
B.text("XP11", XP11[-1][0] + 0.3, XP11[-1][1] + 2.3, "B.SilkS", 0.8)
B.text("XP12", XP12[0][0] + 27 * 2.54 + 3.15, YT, "B.SilkS", 0.8)              # past its pin 28

if __name__ == "__main__":
    bad = B.check()
    n = B.write(OUT, title="TS06-DISP", comment="TERMINAL-06 display board, THT pair with TS06-DRV")
    B.write_project(OUT.replace(".kicad_pcb", ".kicad_pro"))
    B.write_library()
    png = os.path.join(os.path.dirname(OUT), "copper.png")
    B.plot(png, ppm=8, color=lambda n: ((255, 90, 90) if n.startswith(("ANODE", "COLON")) else
                                         (80, 170, 255) if n.startswith(("K", "CAT")) else
                                         (180, 110, 255) if n.startswith(("BL", "M_A")) else (90, 220, 120)))
    print(f"wrote {os.path.relpath(OUT, ROOT)}: {len(B.placed)} parts, {n} nets, {len(B.tracks)} segments, 0 vias")
    print(f"check: {len(bad)} problem(s)")
