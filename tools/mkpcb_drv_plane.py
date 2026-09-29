#!/usr/bin/env python3
"""TS06-DRV-plane: the driver board laid out around an unbroken ground plane on the back face.

    python3 tools/mkpcb_drv_plane.py            # PCB/TS06-DRV-plane/TS06-DRV-plane.kicad_pcb (+ .kicad_pro, copper.png)
    python3 tools/mkpcb_drv_plane.py --route    # the same, routing afresh first (saved to mkpcb_drv_plane_routes.json)
    python3 tools/mkpcb_drv_plane.py --place    # placement only: PCB/TS06-DRV-plane/placement.png
    python3 tools/planecheck.py PCB/TS06-DRV-plane/TS06-DRV-plane.kicad_pcb     # the plane's integrity

THE CONCEPT. The back face (B.Cu, towards the display) is a GND pour, and every other net is laid
on the front face (F.Cu). Ground is never routed at all: every ground pad is through-hole, so the
plane joins them. Where two front-face nets must cross, one of them passes BETWEEN THE PADS OF A
PART THAT IS IN SERIES WITH THE OTHER: a lying resistor, a DIP's channel between its rows, an
opto's channel between its LED side and its output side. Where no such part exists, the net drops
to the back face for a short hop, and every hop is a slot in the plane; the router is made to pay
for back-face copper (HOP_COST per cell on top of the normal price), so it uses the back face only
where the placement leaves no front-face way through, and tools/planecheck.py reports what that
costs the plane.

THE PLACEMENT, in the order the planar graph asks for it:
  * THE BRIDGE ROW. Every Nano output that has a series resistor - the six opto resistors, the
    converter's gate-drive resistor R66, the colon's base resistor R1, the backlight's R20 and the
    m LED's R53 - lies in one row of vertical 10.16 mm resistors directly under the Nano's digital
    row. Their top pads take the pins; between their top and bottom pads runs a horizontal
    STREET, and the Nano's analogue side (A0-A3, I2C, A6/A7, 5 V) runs along it under all the
    digital lines without touching one. This is the one structural idea of the board: ten lines
    that would each cross nine others are crossed by the parts they need anyway.
  * THE DECODERS stay under the top strip and beside the left strip (the display fixes those).
  * THE ANODE CELLS stay over the bottom strips: optos standing, LED row up, output row down, the
    two anode resistors lying under them over their strip pins. The 185 V feed runs between the
    optos' rows, so it never meets a 5 V line: the opto is the bridge between the two.
  * THE LED RIBBON runs below the bottom strips from RN1, as on the baseline, so the strip row
    itself separates LED lines (from below) from anode lines (from above).
  * THE FASCIA CONNECTOR J1 sits in a pocket above the ribbon, reached through the gap between
    XS22 and XS21, so that D7/D8/A6/A7 (which have no series part to bridge with) meet no LED line.

Everything else follows mkpcb_drv.py (the frame, the strips, check_mate, the references).
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbkit as K
import ts06pair as P

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
NAME = "TS06-DRV-plane"
OUT = os.environ.get("TS06_OUT") or os.path.join(ROOT, "PCB", NAME, NAME + ".kicad_pcb")
PLACE_ONLY = "--place" in sys.argv

W, H = 176.0, 100.0
DW = 176.0
Y0 = 26.0
CLASSES = [("HV", 0.6, 0.4, P.HV_PATTERNS),
           ("CATH", 0.25, 0.25, P.CATH_PATTERNS),
           ("PWR", 0.25, 0.5, ["+5V", "+12V", "VIN_J", "VIN_F", "GATE_D", "GATE"])]
PT = P.parts(P.DRV)
# Footprint choices of this board (the circuit is untouched): the bridge-row resistors lie flat on
# 10.16 mm so that a street of lines can pass between their pads.
R_LY = "TS06_R_Axial_DIN0207_P10.16mm"
BRIDGE = ["R25", "R24", "R23", "R22", "R21", "R66", "R1", "R20", "R53", "R26"]
FP = {r: R_LY for r in BRIDGE}
for r in FP:
    PT[r].fp = FP[r]
B = K.Board(NAME, W, H, PT, CLASSES, default=("Default", 0.2, 0.25))


def pl(ref, x, y, rot=0, back=False):
    """Place a part at (x, y) in the DRV frame (y = display y + Y0)."""
    return B.place(ref, PT[ref].fp, x, y, rot, back)


LOW_W = {"GND": 0.0, "+5V": 0.3, "+12V": 0.5}


def near(ref, x0, y0, x1, y1, rots=(0, 90, 180, 270), keepout=()):
    r = K.place_near(B, ref, PT[ref].fp, (x0, y0, x1, y1), rots, keepout=list(keepout), weight=LOW_W)
    assert r is not None, f"no room for {ref} in ({x0}, {y0})-({x1}, {y1})"
    return r


# ======================================================================== the strips (back face)
DISP_STRIP = {"11": (1.6, 4.4, True), "12": (99.57, 2.2, False), "21": (11.94, 41.3, False),
              "22": (47.99, 41.3, False), "23": (69.28, 41.3, False), "24": (107.335, 41.3, False),
              "25": (139.15, 41.3, False)}
for k, (x, y, vertical) in DISP_STRIP.items():
    pl(f"XS{k}", DW - x, y + Y0, rot=0 if vertical else 90, back=True)

# the display's four standoffs (fixed), and four corner holes for the case
HOLES = [(172.5, 66.5), (3.5, 66.5), (125.465, 29.3), (3.5, 33.5),
         (3.5, 96.5), (172.5, 96.5), (3.5, 3.5), (172.5, 22.5)]
for i, (hx, hy) in enumerate(HOLES):
    B.place(f"H{i + 1}", "TS06_MountingHole_M3", hx, hy)
    B.holes.append((hx, hy, 3.2))

# ======================================================================== the tube band
# The decoders exactly where the display wants them (as the baseline): near row up to XS12.
pl("U16", 12.93, 41.62, rot=90)
pl("U15", 35.25, 41.62, rot=90)
pl("U17", 58.65, 41.62, rot=90)
pl("U2", 166.2, 53.26, rot=180)

# The anode cells (the baseline's geometry): the two anode resistors of a pair lie one above the
# other, each ending straight over its strip pin; the two optos stand above them.
Y_U, Y_L, Y3 = 33.8 + Y0, 37.6 + Y0, 30.3 + Y0


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

pl("R59", 126.5, 24.6 + Y0, rot=270)                 # colon ballasts over their pins
pl("R58", 130.5, 24.6 + Y0, rot=270)
pl("VT1", 121.0, 33.0 + Y0, rot=270)
pl("R56", 34.31, 37.0 + Y0, rot=180)                 # AM/PM anode resistors over their pins
pl("R57", 26.69, 33.2 + Y0, rot=180)

# ======================================================================== the top band
pl("U1", 136.24, 17.27, rot=90)                      # the Nano, USB out of the right edge
pl("XS1", 14.0, 12.50)                               # 12 V in through the left edge
pl("F1", 24.0, 2.70)
pl("VD2", 36.24, 9.00, rot=180)
pl("U14", 21.5, 19.50)
pl("C8", 40.5, 3.80)
pl("L1", 47.5, 13.50)                                # the converter, one tight loop
pl("VT21", 59.0, 19.00)
pl("VD1", 67.8, 10.00, rot=180)
pl("C7", 72.5, 6.00)
pl("U11", 81.0, 20.70, rot=180)
pl("R67", 69.0, 13.60, rot=180)
pl("U12", 104.0, 18.0, rot=180)
pl("R62", 96.0, 2.3)
pl("R63", 111.6, 2.3, rot=270)
pl("R64", 114.5, 12.0)
pl("RP1", 117.5, 20.5)
pl("R69", 84.8, 15.0, rot=90)
pl("R70", 88.3, 15.0, rot=90)
pl("R71", 91.8, 15.0, rot=90)
pl("R65", 114.5, 4.0)
pl("C14", 96.5, 5.7)

# THE BRIDGE ROW: one lying resistor per Nano output with a series part, pad 1 up on the Nano's
# side. Between y BR_TOP and BR_TOP + 10.16 the analogue side's lines pass under all of them.
BR_TOP = 21.2
BR_X = [134.5, 138.4, 142.3, 146.2, 150.1, 154.0, 157.9, 161.8, 165.7, 169.6]
for ref, x in zip(BRIDGE, BR_X):
    pl(ref, x, BR_TOP, rot=270)

# The clock module beside the Nano's analogue end, turned so SCL and SDA face the street.
pl("U13", 128.0, 11.0, rot=0)

# ======================================================================== the bottom band
pl("U3", 44.5, 86.0, rot=270)
pl("RN1", 26.72, 82.0, rot=90)
# the fascia connector on the display-facing side, in the pocket between XS22 and XS21, above the
# LED ribbon: the lines that reach it come down through the strip gap and never meet an LED line
pl("J1", 136.0, 74.5, rot=180, back=True)
pl("C4", 152.5, 38.5, rot=270)

JACK = B.court("J1")
RIB = (20.0, 68.4, 166.0, 72.5)                      # the LED ribbon, kept free of small parts
for r in ("C9", "C10", "C11"):
    near(r, 17.0, 0.5, 45.0, 21.4)
for r in ("C12", "R68", "C13", "C3"):
    near(r, 38.0, 0.5, 127.0, 25.0)
for r in ("R60", "R61"):
    near(r, 67.0, 55.0, 100.5, 65.4)
for r in ("C15", "C16"):
    near(r, 8.0, 47.4, 46.0, 53.0, rots=(0,))
near("C17", 58.0, 47.7, 80.0, 53.0, rots=(0,))
for r in ("VT20",):
    near(r, 161.0, 55.0, 170.5, 66.0)
# the DNP bleeds hang off the anode lines above the strips (below them they would cut the ribbon)
for r in ("R33", "R34", "R35", "R36"):
    near(r, 140.0, 44.0, 172.0, 66.0)
for r in ("R37", "R38", "R39", "R40", "R41", "R42", "R43", "R44"):
    near(r, 45.0, 44.0, 120.0, 66.0)
for r in ("R54", "R55"):
    near(r, 110.0, 0.5, 132.0, 20.0)
for r in ("C5", "C6"):
    near(r, 128.0, 72.5, 150.0, 82.0, keepout=(RIB, JACK))
near("C1", 10.0, 72.5, 26.0, 83.5, keepout=(RIB,))


# ======================================================================== references on the silk
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
ROUTES = os.environ.get("TS06_ROUTES") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "mkpcb_drv_plane_routes.json")
FIXED = set(B.tracks)
WIDTHS = {"+12V": 0.8, "VIN_J": 0.8, "VIN_F": 0.8, "SW": 0.8, "+5V": 0.4}
HOP_COST = float(os.environ.get("HOP_COST", "3.0"))   # extra price per 0.1 mm cell of back-face copper
ROUNDS = int(os.environ.get("ROUNDS", "60"))


def route_order():
    """The most constrained first; GND is not routed at all - it is the back-face plane."""
    nets = sorted({p.net for p in B.pads if p.net})
    hv = [n for n in nets if B.cls(n) == "HV"]
    order = ([f"A{i}" for i in range(4)] + [f"XA{i}" for i in range(8)] + [f"XB{i}" for i in range(8)] +
             [f"BL_A{i}" for i in range(1, 9)] + ["SDA", "SCL", "A6", "A7"] + [f"D{i}" for i in range(2, 14)] +
             ["SW", "HV185"] + [n for n in hv if n not in ("SW", "HV185")] +
             ["+12V", "VIN_J", "VIN_F", "GATE_D", "GATE", "+5V"])
    order += [n for n in nets if n not in order and n != "GND"]
    return [n for n in order if n in nets]


def route():
    import netroute as NR
    R = NR.NetRouter(B, turn45=6.0)
    R.fixed = set(FIXED)
    R.dirmul = {ly: [1.0, 1.5] * 4 for ly in ("F.Cu", "B.Cu")}
    order = route_order()
    N = NR.Negotiator(R, order, widths=WIDTHS)
    N.hist["B.Cu"] += HOP_COST                  # the plane's price: back-face copper only where it must
    failed = N.run(rounds=ROUNDS)
    if not failed:
        R.polish(order, widths=WIDTHS, verbose=True)
    with open(ROUTES, "w") as fh:
        json.dump([[n, ly, [list(a), list(b)], w] for n, ly, a, b, w in B.tracks if (n, ly, a, b, w) not in FIXED], fh, indent=0)
    return failed


def load_routes():
    with open(ROUTES) as fh:
        for n, ly, (a, b), w in json.load(fh):
            B.tracks.append((n, ly, tuple(a), tuple(b), w))


if __name__ == "__main__":
    missing = sorted(set(PT) - set(B.placed), key=K._refkey)
    assert not missing, "not placed: " + " ".join(missing)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    refs = list(B.placed)
    for i, a in enumerate(refs):
        ca = B.court(a)
        for b in refs[i + 1:]:
            cb = B.court(b)
            if ca[0] < cb[2] and cb[0] < ca[2] and ca[1] < cb[3] and cb[1] < ca[3]:
                if B.placed[a][0].back == B.placed[b][0].back and not (a[0] == "H" or b[0] == "H"):
                    print(f"  overlap {a} / {b}")
    if PLACE_ONLY:
        K.plot_placement(B, os.path.join(os.path.dirname(OUT), "placement.png"), ppm=7)
        print("mate:", check_mate() or "ok")
        sys.exit(0)
    if "--route" in sys.argv or not os.path.exists(ROUTES):
        failed = route()
        print("unrouted:", " ".join(failed) if failed else "none")
    else:
        load_routes()
    # the plane: GND on the back face only, poured round everything else; it is the only ground
    # connection on the board, so tools/planecheck.py proves it reaches every ground pad
    B.zone("GND", "B.Cu", clearance=0.25, min_th=0.25, gap=0.5, bridge=0.5)
    B.hide_refs = True
    place_refs(B)
    B.text("TS06-DRV-plane rev A", 90.0, 97.0, "F.SilkS", 1.0)
    bad = B.check()
    print(f"check: {len(bad)} problem(s)")
    mate = check_mate()
    print("mate:", "every strip pin and standoff lines up" if not mate else "")
    for m in mate:
        print("  [MATE]", m)
    n = B.write(OUT, title=NAME, comment="TERMINAL-06 driver board, plane variant, THT pair with TS06-DISP")
    B.write_project(OUT.replace(".kicad_pcb", ".kicad_pro"))
    B.write_library()
    print(f"wrote {os.path.relpath(OUT, ROOT)}: {len(B.placed)} parts, {n} nets, {len(B.tracks)} segments, 0 vias")
    B.plot(os.path.join(os.path.dirname(OUT), "copper.png"), ppm=8, color=lambda n: ((255, 90, 90) if B.cls(n) == "HV" else None))
