#!/usr/bin/env python3
"""TS06-DRV: the driver board of the through-hole pair - everything that is not the display.

    python3 tools/mkpcb_drv.py             # PCB/TS06-DRV/TS06-DRV.kicad_pcb (+ .kicad_pro, copper.png)
    python3 tools/mkpcb_drv.py --place     # placement only: PCB/TS06-DRV/placement.png
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbkit as K
import ts06pair as P

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
NAME = "TS06-DRV"
OUT = os.environ.get("TS06_OUT") or os.path.join(ROOT, "PCB", NAME, NAME + ".kicad_pcb")
PLACE_ONLY = "--place" in sys.argv

W, H = 176.0, 74.0
DW = 176.0                                  # the display board's width: x here = DW - x there
YT, YB = 2.2, 41.3                          # the strip rows, shared with TS06-DISP
CLASSES = [("HV", 0.6, 0.4, P.HV_PATTERNS),
           ("CATH", 0.25, 0.25, P.CATH_PATTERNS),
           ("PWR", 0.25, 0.5, ["+5V", "+12V", "VIN_J", "VIN_F", "GATE_D", "GATE"])]
B = K.Board(NAME, W, H, P.parts(P.DRV), CLASSES, default=("Default", 0.2, 0.25))
PT = P.parts(P.DRV)

# ======================================================================== the strips (back face)
DISP_STRIP = {"11": (1.6, 4.4, True), "12": (99.57, YT, False), "21": (11.94, YB, False),
              "22": (47.99, YB, False), "23": (69.28, YB, False), "24": (107.335, YB, False),
              "25": (139.15, YB, False)}


def socket(k):
    x, y, vertical = DISP_STRIP[k]
    n = len(P.HEADERS[k])
    B.place(f"XS{k}", f"TS06_PinSocket_1x{n:02d}", DW - x, y, rot=0 if vertical else 90, back=True)
    return [B.P(f"XS{k}", i + 1) for i in range(n)]


XS = {k: socket(k) for k in DISP_STRIP}

HOLES = [(172.5, 40.5), (3.5, 40.5), (DW - 50.535, 3.3), (3.5, 5.5), (3.5, 70.5), (172.5, 70.5)]
for i, (hx, hy) in enumerate(HOLES):
    B.place(f"H{i + 1}", "TS06_MountingHole_M3", hx, hy)
    B.holes.append((hx, hy, 3.2))

DEC_Y = 15.62
B.place("U16", "TS06_DIP-16_W7.62mm_Socket", 12.93, DEC_Y, rot=90)
B.place("U15", "TS06_DIP-16_W7.62mm_Socket", 35.25, DEC_Y, rot=90)
B.place("U17", "TS06_DIP-16_W7.62mm_Socket", 58.65, DEC_Y, rot=90)
B.place("U2", "TS06_DIP-16_W7.62mm_Socket", 166.2, 27.26, rot=180)
B.place("C4", "TS06_C_Disc_P5.00mm", 158.6, 4.6)

# ---- the Nano, standing in the gap between the seconds strip and the minutes strip
NX, NY = 76.0, 34.2
B.place("U1", "TS06_Arduino_Nano", NX, NY)

# ---- anode channel cells. Each pair of anode pins gets its two series resistors lying one
# above the other, each ending straight over its pin, and its two optos standing above them,
# emitter pin over the resistor it feeds.
Y_U, Y_L, Y3 = 33.8, 37.6, 30.3
R = "TS06_R_Axial_DIN0309_P12.70mm"
OPTO = "TS06_DIP-4_W7.62mm_Socket"


def cell_left(xl, r_up, r_lo, o_up, o_lo):
    xr = xl + 2.54
    B.place(r_up, R, xr - 12.7, Y_U)
    B.place(r_lo, R, xl - 12.7, Y_L)
    B.place(o_up, OPTO, xr - 12.7 + 2.54, Y3 - 7.62, rot=270)
    B.place(o_lo, OPTO, xr - 15.9, Y3 - 7.62, rot=270)


def cell_right(xl, r_up, r_lo, o_up, o_lo):
    B.place(r_up, R, xl + 12.7, Y_U, rot=180)
    B.place(r_lo, R, xl + 2.54 + 12.7, Y_L, rot=180)
    B.place(o_up, OPTO, xl + 15.24, Y3 - 7.62, rot=270)
    B.place(o_lo, OPTO, xl + 21.04, Y3 - 7.62, rot=270)


cell_left(63.585, "R31", "R32", "U9", "U10")         # S10 / S1
cell_right(101.64, "R30", "R29", "U8", "U7")         # M1 / M10
cell_left(156.44, "R27", "R28", "U5", "U6")          # H10 / H1

# ---- colon: one ballast per lamp standing over its pin, the return switch beside them
B.place("R59", R, 126.5, 24.6, rot=270)              # COLON_L
B.place("R58", R, 130.5, 24.6, rot=270)              # COLON_U
B.place("VT1", "TS06_TO-92_Inline_Wide", 121.0, 33.0, rot=270)

# ---- AM/PM static anode resistors, over their pins
B.place("R56", R, 34.31, 37.0, rot=180)
B.place("R57", R, 26.69, 33.2, rot=180)

# ---- AM/PM expander and the LED network
B.place("U3", "TS06_DIP-28_W7.62mm_Socket", 44.5, 60.0, rot=270)
B.place("RN1", "TS06_DIP-16_W7.62mm_Socket", 26.72, 56.0, rot=90)
B.place("C1", "TS06_C_Disc_P5.00mm", 17.0, 53.5)
B.place("R54", "TS06_R_Axial_DIN0207_P10.16mm", 11.0, 46.0)
B.place("R55", "TS06_R_Axial_DIN0207_P10.16mm", 11.0, 49.1)
B.place("U13", "TS06_PinSocket_1x05", 6.5, 53.5)

# ---- 12 V inlet, polarity, fuse, 5 V: the bottom row, in the order the current takes it
B.place("XS1", "TS06_BarrelJack_Horizontal", 98.5, 60.0, rot=90)      # mouth through the bottom edge
B.place("F1", "TS06_Fuse_PTC_MF-RG1100", 107.9, 58.0, rot=270)
B.place("VD2", "TS06_D_DO-201AD_P15.24mm", 113.0, 72.1, rot=90)
B.place("U14", "TS06_R-78E_SIP3", 96.5, 55.5)
B.place("C10", "TS06_C_Disc_P5.00mm", 94.5, 45.8)
B.place("C11", "TS06_C_Disc_P5.00mm", 101.7, 45.8)
B.place("C9", "TS06_C_Disc_P5.00mm", 109.0, 45.8)

# ---- the converter's power stage beside the inlet: inductor, switch, catch diode, reservoir
B.place("C8", "TS06_CP_Radial_D6.3mm_P2.50mm", 118.1, 69.5)
B.place("C12", "TS06_C_Disc_P5.00mm", 121.7, 51.0, rot=90)
B.place("U11", "TS06_DIP-8_W7.62mm_Socket", 125.5, 45.0)
B.place("L1", "TS06_L_Radial_D12.0mm_P5.00mm", 126.5, 62.0)
B.place("VT21", "TS06_TO-220-3_Vertical_HV", 140.0, 71.7)
B.place("R67", "TS06_R_Axial_DIN0207_P10.16mm", 137.0, 47.5, rot=270)
B.place("R68", "TS06_R_Axial_DIN0207_P10.16mm", 124.84, 72.0)
B.place("VD1", "TS06_D_DO-41_P10.16mm", 141.0, 48.0, rot=270)
B.place("C7", "TS06_CP_Radial_D10.0mm_P5.00mm", 147.0, 60.0)
B.place("R60", R, 144.2, 51.0)
B.place("R61", R, 153.5, 68.5)
B.place("R1", "TS06_R_Axial_DIN0207_P10.16mm", 108.8, 50.0)

# ---- the converter's control, in the upper band where the 185 V rail is distributed anyway
B.place("R62", R, 81.0, 5.5)
B.place("R63", R, 81.0, 9.3)
B.place("R64", "TS06_R_Axial_DIN0207_P10.16mm", 81.0, 13.0)
B.place("RP1", "TS06_Trimmer_3296W", 99.8, 13.9)
B.place("U12", "TS06_DIP-8_W7.62mm_Socket", 105.0, 5.5)
B.place("C14", "TS06_C_Disc_P5.00mm", 81.0, 16.2)
B.place("R69", "TS06_R_Axial_DIN0207_P10.16mm", 117.0, 9.5)
B.place("R70", "TS06_R_Axial_DIN0207_P10.16mm", 117.0, 12.5)
B.place("R65", "TS06_R_Axial_DIN0207_P10.16mm", 117.0, 15.5)
B.place("C13", "TS06_C_Disc_P5.00mm", 129.5, 9.5)
B.place("R71", "TS06_R_Axial_DIN0207_P10.16mm", 129.5, 12.5)
B.place("R66", "TS06_R_Axial_DIN0207_P10.16mm", 129.5, 15.5)

B.place("C3", "TS06_C_Disc_P5.00mm", 87.6, 23.0)        # 5 V bulk, between the Nano and the decoders

# ---- the opto LED resistors, beside the cell they drive
B.place("R25", "TS06_R_Axial_DIN0207_P10.16mm", 69.3, 30.0, rot=90)
B.place("R26", "TS06_R_Axial_DIN0207_P10.16mm", 72.5, 30.0, rot=90)
B.place("R23", "TS06_R_Axial_DIN0207_P10.16mm", 81.5, 29.0, rot=90)
B.place("R24", "TS06_R_Axial_DIN0207_P10.16mm", 85.0, 29.0, rot=90)
B.place("R21", "TS06_R_Axial_DIN0207_P10.16mm", 133.85, 31.5, rot=90)
B.place("R22", "TS06_R_Axial_DIN0207_P10.16mm", 137.4, 31.5, rot=90)

# ---- the DNP bleed pairs, standing, beside each pair of anode pins
RV = "TS06_R_Axial_DIN0207_P2.54mm_Vertical"


def bleed(r1, r2, x, y):
    B.place(r1, RV, x, y, rot=270)
    B.place(r2, RV, x, y + 5.2, rot=270)


bleed("R43", "R44", 61.0, 45.5)          # S1
bleed("R41", "R42", 67.0, 45.5)          # S10
bleed("R37", "R38", 94.5, 28.5)          # M10
bleed("R39", "R40", 97.9, 28.5)          # M1
bleed("R33", "R34", 163.0, 30.4)         # H10
bleed("R35", "R36", 166.3, 30.4)         # H1

# ---- the rest of the lower band: fascia, clock, the m LED, backlight switch
B.place("J1", "TS06_JST_PH_S6B-PH-K_Horizontal", 56.0, 67.2)
B.place("C5", "TS06_C_Disc_P5.00mm", 50.0, 61.0)
B.place("C6", "TS06_C_Disc_P5.00mm", 50.0, 58.0)
B.place("R53", "TS06_R_Axial_DIN0207_P10.16mm", 48.0, 49.0)
B.place("VT20", "TS06_TO-92_Inline_Wide", 164.06, 51.5, rot=90)
B.place("R20", "TS06_R_Axial_DIN0207_P10.16mm", 159.5, 45.0, rot=270)
B.place("C15", "TS06_C_Disc_P5.00mm", 38.0, 19.5)
B.place("C16", "TS06_C_Disc_P5.00mm", 16.0, 19.5)
B.place("C17", "TS06_C_Disc_P5.00mm", 61.0, 19.5)

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
T("CAT_B_AMP", "F.Cu", P_("U15", 8), (55.0, DEC_Y), (55.0, 6.2), XS12["CAT_B_AMP"])

# U17 (ИН-17 pair), back face except KS0, which crosses KS1 on the front.
for pin in (14, 13, 11, 10, 9, 16):
    n = PT["U17"].pins[str(pin)]
    rise(n, "B.Cu", P_("U17", pin), XS12[n][0])
rise("KS0", "F.Cu", P_("U17", 15), XS12["KS0"][0])
T("KS7", "B.Cu", P_("U17", 8), (78.97, DEC_Y - 2.54), (78.97, YT + 2.54), XS12["KS7"])
T("KS9", "B.Cu", P_("U17", 1), (56.11, DEC_Y - 2.54), XS12["KS9"])
T("KS8", "B.Cu", P_("U17", 2), (59.92, DEC_Y + 1.27), (54.9, DEC_Y + 1.27), (54.9, YT + 1.33), XS12["KS8"])

# U2 (ИН-12 bus), beside XS11. The column facing the strip (K7 K8 K9) goes straight across on the
# front; the far column threads through the chip on the back, each line through the gap above
# its own pin, and lands on the strip in order.
XS11 = {PT["XS11"].pins[str(i + 1)]: B.P("XS11", i + 1) for i in range(10)}
T("K7", "F.Cu", P_("U2", 8), XS11["K7"])
T("K8", "F.Cu", P_("U2", 2), (169.3, P_("U2", 2)[1]), (169.3, 17.1), (171.84, 14.56), XS11["K8"])
T("K9", "F.Cu", P_("U2", 1), (171.8, P_("U2", 1)[1]), (171.8, 22.24), XS11["K9"])
X_DIAG = 172.6                              # where each back-face line finishes its 45 degree run
for pin in (9, 10, 11, 13, 14, 15, 16):
    n = PT["U2"].pins[str(pin)]
    px, py = P_("U2", pin)
    tx, ty = XS11[n]
    if pin == 9:                            # K6 passes over the top of the facing column
        gy = 7.96
        T(n, "B.Cu", (px, py), (px + py - gy, gy), (X_DIAG - abs(ty - gy), gy), (X_DIAG, ty), (tx, ty))
    else:                                   # the rest through the gap above their own pin
        gy = py - 1.27
        T(n, "B.Cu", (px, py), (px + 1.27, gy), (X_DIAG - abs(ty - gy), gy), (X_DIAG, ty), (tx, ty))

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
    """Every XS pin here must sit exactly behind its XP pin on TS06-DISP (x mirrored, y shared),
    carry the same signal, and every display standoff must have its hole here."""
    import mkpcb_disp as DISP
    bad = []
    for k in P.HEADERS:
        n = len(P.HEADERS[k])
        for i in range(1, n + 1):
            xp, xs = DISP.B.pad(f"XP{k}", i), B.pad(f"XS{k}", i)
            if abs((DW - xp.x) - xs.x) > 1e-3 or abs(xp.y - xs.y) > 1e-3:
                bad.append(f"XS{k}.{i} at ({xs.x}, {xs.y}) but XP{k}.{i} lands at ({DW - xp.x}, {xp.y})")
            if xp.net != xs.net:
                bad.append(f"XS{k}.{i} carries {xs.net} but XP{k}.{i} carries {xp.net}")
    mine = {(round(x, 3), round(y, 3)) for x, y, d in B.holes}
    for x, y, d in DISP.B.holes:
        if (round(DW - x, 3), round(y, 3)) not in mine:
            bad.append(f"display standoff at ({x}, {y}) has no hole here at ({DW - x}, {y})")
    return bad


# ======================================================================== the routed copper
# The router (tools/netroute.py) is run with --route and its tracks saved beside this file, so
# the board regenerates exactly - and without a C compiler - from the saved routes. Everything
# above this line is the source of truth for WHERE things are; the route file only records the
# copper the router found for that placement, and it is thrown away and re-found whenever the
# placement changes.
ROUTES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mkpcb_drv_routes.json")
LOCKED = {t[0] for t in B.tracks}              # the hand-laid fans
WIDTHS = {"+12V": 0.8, "VIN_J": 0.8, "VIN_F": 0.8, "SW": 0.8, "+5V": 0.4, "GND": 0.4}


def route_order():
    nets = sorted({p.net for p in B.pads if p.net})
    hv = [n for n in nets if B.cls(n) == "HV"]
    order = (["SW", "HV185"] + [n for n in hv if n not in ("SW", "HV185")] +
             ["+12V", "VIN_J", "VIN_F", "GATE_D", "GATE", "+5V"] +
             [f"A{i}" for i in range(4)] + [f"XA{i}" for i in range(8)] + [f"XB{i}" for i in range(8)] +
             [f"BL_A{i}" for i in range(1, 9)] + ["SDA", "SCL"])
    order += [n for n in nets if n not in order and n != "GND" and n not in LOCKED]
    return order + ["GND"]


def route():
    import netroute as NR
    R = NR.NetRouter(B)
    R.locked = set(LOCKED)
    failed = R.route_all(route_order(), widths=WIDTHS)
    with open(ROUTES, "w") as fh:
        json.dump([[n, ly, [list(a), list(b)], w] for n, ly, a, b, w in B.tracks if n not in LOCKED], fh, indent=0)
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
