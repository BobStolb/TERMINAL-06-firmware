#!/usr/bin/env python3
"""Draw a board's COPPER as a PNG, one panel per face, coloured by what each net carries.

WHY IT EXISTS: tools/render.py draws the board as a customer sees it - mask, silk, gold - which
is the right picture for checking a fascia and the wrong one for checking a route. Under a black
mask every track looks the same, so the thing that is actually wrong with a route is invisible.

It exists mainly because of how the first TS06-MAIN route was caught. Every checker in this repo
passed it: tools/audit.py found two things, tools/checkcopper.py one, tools/checkmatch.py agreed,
KiCad's own DRC was quiet. The board was nevertheless badly routed - 476 vias, no grain at all,
a ground pour in 292 islands - and what caught it was the owner looking at a 3D render and saying
so. One glance beat six hours of passing tests, because every test asked whether the copper was
LEGAL and none asked whether it was any GOOD (18.09.26). tools/audit.py now measures that; this
draws it, because a number tells you a board is bad and a picture tells you where.

Usage:  python3 tools/plotcu.py PCB/TS06-MAIN/TS06-MAIN.kicad_pcb out.png [px-per-mm]
"""
import re, sys, zlib, struct
import numpy as np

SRC = open(sys.argv[1], encoding="utf8").read()
OUT = sys.argv[2] if len(sys.argv) > 2 else "copper.png"
PPM = float(sys.argv[3]) if len(sys.argv) > 3 else 8.0
GAP = 16                                        # blank rows between the two panels

NETNAME = {int(a): b for a, b in re.findall(r'^\t\(net (\d+) "([^"]*)"', SRC, re.M)}

# What a net is FOR, which is what makes the picture readable. The high voltage wants to be seen
# on its own (it carries a 0.6 mm halo and must never be near anything), and the cathode lines
# want to be seen as bundles, because ten of them run side by side to each tube and whether they
# actually do is the single clearest sign of whether the route has any structure.
COL = {"hv":   (255, 77, 77),      # anodes, the 185 V trunk: everything with the wide halo
       "cath": (77, 166, 255),     # the К155ИД1 cathode lines and the tube pins
       "gnd":  (110, 115, 120),
       "pwr":  (255, 200, 60),
       "bl":   (176, 107, 255),    # backlight
       "sig":  (87, 217, 121)}


def group(n):
    if n.startswith(("HV", "185", "ANODE", "AN_", "A_")) or n in ("VHV", "V185"):
        return "hv"
    if n.startswith(("CAT", "K_", "SEG")) or re.fullmatch(r"[KQ]\d+", n):
        return "cath"
    if n == "GND":
        return "gnd"
    if n in ("+5V", "+12V", "VCC", "VIN", "VBAT"):
        return "pwr"
    if n.startswith("BL_"):
        return "bl"
    return "sig"


seg = {"F.Cu": [], "B.Cu": []}
for m in re.finditer(r'\(segment\s*\(start ([-\d.]+) ([-\d.]+)\)\s*\(end ([-\d.]+) ([-\d.]+)\)'
                     r'\s*\(width ([-\d.]+)\)\s*\(layer "([^"]+)"\)\s*\(net (?:(\d+)|"([^"]*)")\)', SRC):
    ax, ay, bx, by, w, ly, code, name = m.groups()
    if ly in seg:
        nm = name if name else NETNAME.get(int(code) if code else -1, "")
        seg[ly].append((float(ax), float(ay), float(bx), float(by), float(w), COL[group(nm or "")]))

vias = [(float(a), float(b), float(c)) for a, b, c in
        re.findall(r'\(via\s*\(at ([-\d.]+) ([-\d.]+)\)\s*\(size ([-\d.]+)\)', SRC)]

xs =[v for L in seg.values() for t in L for v in (t[0], t[2])]
ys = [v for L in seg.values() for t in L for v in (t[1], t[3])]
if not xs:
    sys.exit("no copper in " + sys.argv[1])
x0, x1 = min(xs) - 2, max(xs) + 2
y0, y1 = min(ys) - 2, max(ys) + 2
W, H = int((x1 - x0) * PPM), int((y1 - y0) * PPM)

img = np.full((2 * H + GAP, W, 3), 14, np.uint8)
img[:H] = (22, 32, 42)
img[H + GAP:] = (22, 32, 42)


def stroke(base, ax, ay, bx, by, r, col, ring=False):
    """A round-capped line, or a ring when ring is set. Drawn by distance rather than by
    Bresenham so a 0.2 mm track at 8 px/mm is still visible and diagonals do not alias away."""
    lo_x, hi_x = int(max(min(ax, bx) - r - 2, 0)), int(min(max(ax, bx) + r + 3, W))
    lo_y, hi_y = int(max(min(ay, by) - r - 2, 0)), int(min(max(ay, by) + r + 3, H))
    if hi_x <= lo_x or hi_y <= lo_y:
        return
    gy, gx = np.mgrid[lo_y:hi_y, lo_x:hi_x]
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = np.clip(((gx - ax) * dx + (gy - ay) * dy) / L, 0, 1) if L > 0 else 0
    d = np.hypot(gx - (ax + t * dx), gy - (ay + t * dy))
    hit = (d <= r) & (d >= r - 1.4) if ring else (d <= r)
    img[base + lo_y:base + hi_y, lo_x:hi_x][hit] = col


for panel, ly in enumerate(("F.Cu", "B.Cu")):
    base = 0 if panel == 0 else H + GAP
    for ax, ay, bx, by, w, col in seg[ly]:
        stroke(base, (ax - x0) * PPM, (ay - y0) * PPM, (bx - x0) * PPM, (by - y0) * PPM,
               max(w * PPM / 2, 0.9), col)
    for vx, vy, vs in vias:                      # a via belongs to both faces
        cx, cy = (vx - x0) * PPM, (vy - y0) * PPM
        stroke(base, cx, cy, cx, cy, vs * PPM / 2, (255, 210, 77), ring=True)

h, w, _ = img.shape
raw = b"".join(bytes([0]) + img[r].tobytes() for r in range(h))


def chunk(tag, data):
    c = struct.pack(">I", len(data)) + tag + data
    return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


png = bytes([137, 80, 78, 71, 13, 10, 26, 10])
png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
png += chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b"")
open(OUT, "wb").write(png)
print(f"{OUT}  {w}x{h} px, front {len(seg['F.Cu'])} / back {len(seg['B.Cu'])} segments, "
      f"{len(vias)} vias.  red high voltage, blue cathodes, yellow power, grey ground, "
      f"violet backlight, green signal")
