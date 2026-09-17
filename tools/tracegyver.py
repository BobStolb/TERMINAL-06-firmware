#!/usr/bin/env python3
"""Trace the nets of the inherited AlexGyver "IN-12_norm" board from its Gerbers.

WHY: the board was never drawn as a schematic - alexgyver.ru/nixieclock_v2 says so in as
many words ("у проекта нет и никогда не было схемы, сразу разводилась печатная плата") -
and it is the only electrical record of the 185 V converter and of which К155ИД1 output
reaches which ИН-12 socket hole. TS06-MAIN has to reproduce both, so this tool reads them
off the fabrication data in PCB/IN-12_norm/, the same files the physical boards were made
from. The result is written up in TERMINAL-06-measurements-PCB-GYVER-NETLIST.md.

WHAT IT DOES: rasterises both copper layers (regions, draws, flashes; %LPC clears erased),
labels the connected copper on each, joins the two through the plated holes, and prints
which holes share a net. Every hole is named from geometry alone: the four 12-hole socket
stadiums use the pad numbers of TS06_IN12_Socket, and every other part is a hard-coded
position that this tool asserts is really a drilled hole - so if a hole moves, the tool
fails rather than mislabels. The names follow the silkscreen render in AlexGyver's repo
(schemes/IN-12_norm.jpg): U1 Nano, D1 К155ИД1, U2..U5 TLP627, P1..P4 the mating headers.

It then checks the whole display chain for consistency: К155ИД1 pinout (datasheet) ->
copper -> ИН-12А cathode order (datasheet) against the firmware's digitMask for
BOARD_TYPE 0, which was confirmed on the bench. Ten of ten agreeing is the evidence
that no meter session is needed for the ИН-12 hole-to-digit map.

    python3 tools/tracegyver.py          # the net table and the chain check
    python3 tools/tracegyver.py --png    # also PCB/IN-12_norm/gyver_copper.png (both layers)

Numpy only, deterministic. Coordinates in mm from the Gerber origin (board bottom-left),
Y up, i.e. the panel as drawn, seen from the component side.
"""
import os, re, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "PCB", "IN-12_norm")
G = 0.05                                    # raster pitch, mm
IN = 25.4
W, H = 99.06, 80.77                         # the panel


# ------------------------------------------------------------------ Gerber (RS-274X) reader
def read_gerber(path):
    """Return (regions, draws, flashes): regions = [(polarity, [(x,y),...])], draws =
    [(polarity, ap, (x0,y0), (x1,y1))], flashes = [(polarity, ap, (x,y))]; ap = ('C', d) or
    ('R', w, h) in mm."""
    txt = open(path, "rb").read().decode("ascii", "replace").replace("\r", "")
    aps, regions, draws, flashes = {}, [], [], []
    pol, ap, x, y = "D", None, 0.0, 0.0
    in_region, contour = False, None
    fmt_dec = 4
    for raw in txt.split("\n"):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("%"):
            body = line.strip("%").rstrip("*")
            if body.startswith("FSLA"):
                fmt_dec = int(re.match(r"FSLAX(\d)(\d)", body).group(2))
            elif body.startswith("ADD"):
                m = re.match(r"ADD(\d+)([CR]),([\d.]+)(?:X([\d.]+))?", body)
                n, kind = int(m.group(1)), m.group(2)
                aps[n] = ("C", float(m.group(3)) * IN) if kind == "C" else \
                         ("R", float(m.group(3)) * IN, float(m.group(4)) * IN)
            elif body.startswith("LP"):
                pol = body[2]
            continue
        line = line.rstrip("*")
        if line.startswith("G04"):
            continue
        if line == "G36":
            in_region, contour = True, None
            continue
        if line == "G37":
            if contour and len(contour) >= 3:
                regions.append((pol, contour))
            in_region, contour = False, None
            continue
        m = re.fullmatch(r"(?:G54)?(?:G0[123])?D(\d+)", line)
        if m:
            if int(m.group(1)) >= 10:
                ap = aps[int(m.group(1))]
            continue
        m = re.fullmatch(r"(?:G0[123])?(?:X(-?\d+))?(?:Y(-?\d+))?(?:I-?\d+)?(?:J-?\d+)?D0([123])", line)
        if not m:
            continue                        # G70, G90, M02 and friends
        nx = int(m.group(1)) / 10 ** fmt_dec * IN if m.group(1) is not None else x
        ny = int(m.group(2)) / 10 ** fmt_dec * IN if m.group(2) is not None else y
        op = m.group(3)
        if in_region:
            if op == "2":
                if contour and len(contour) >= 3:
                    regions.append((pol, contour))
                contour = [(nx, ny)]
            elif op == "1":
                contour.append((nx, ny))
        elif op == "1":
            draws.append((pol, ap, (x, y), (nx, ny)))
        elif op == "3":
            flashes.append((pol, ap, (nx, ny)))
        x, y = nx, ny
    return regions, draws, flashes


def read_drill(path):
    txt = open(path, "rb").read().decode("ascii", "replace").replace("\r", "")
    tools, holes, cur, dec = {}, [], None, 4
    for raw in txt.split("\n"):
        line = raw.strip()
        m = re.match(r"INCH,LZ,(\d+)\.(\d+)", line)
        if m:
            dec = len(m.group(2))
        m = re.match(r"T(\d+)C([\d.]+)", line)
        if m:
            tools[m.group(1)] = float(m.group(2)) * IN
            continue
        m = re.fullmatch(r"T(\d+)", line)
        if m:
            cur = m.group(1)
            continue
        m = re.match(r"X([+-]?\d+)Y([+-]?\d+)", line)
        if m and cur:
            holes.append((tools[cur], int(m.group(1)) / 10 ** dec * IN, int(m.group(2)) / 10 ** dec * IN))
    return holes


# ------------------------------------------------------------------ raster
class Raster:
    def __init__(self, w, h):
        self.nx, self.ny = int(round(w / G)) + 2, int(round(h / G)) + 2
        self.a = np.zeros((self.ny, self.nx), dtype=bool)
        self.xs = (np.arange(self.nx) + 0.5) * G
        self.ys = (np.arange(self.ny) + 0.5) * G

    def polygon(self, pts, value):
        """Even-odd scanline fill at cell centres."""
        P = np.asarray(pts, dtype=float)
        x0, y0 = P[:, 0], P[:, 1]
        x1, y1 = np.roll(x0, -1), np.roll(y0, -1)
        ylo, yhi = np.minimum(y0, y1), np.maximum(y0, y1)
        r0 = max(0, int(np.floor(ylo.min() / G - 0.5)))
        r1 = min(self.ny - 1, int(np.ceil(yhi.max() / G + 0.5)))
        for r in range(r0, r1 + 1):
            yc = self.ys[r]
            sel = (ylo <= yc) & (yc < yhi)
            if not sel.any():
                continue
            t = (yc - y0[sel]) / (y1[sel] - y0[sel])
            xi = np.sort(x0[sel] + t * (x1[sel] - x0[sel]))
            for a, b in zip(xi[0::2], xi[1::2]):
                c0 = max(0, int(np.ceil(a / G - 0.5)))
                c1 = min(self.nx - 1, int(np.floor(b / G - 0.5)))
                if c1 >= c0:
                    self.a[r, c0:c1 + 1] = value

    def capsule(self, p0, p1, r, value):
        (ax, ay), (bx, by) = p0, p1
        c0 = max(0, int((min(ax, bx) - r) / G) - 1)
        c1 = min(self.nx - 1, int((max(ax, bx) + r) / G) + 1)
        r0 = max(0, int((min(ay, by) - r) / G) - 1)
        r1 = min(self.ny - 1, int((max(ay, by) + r) / G) + 1)
        if c1 < c0 or r1 < r0:
            return
        X, Y = np.meshgrid(self.xs[c0:c1 + 1], self.ys[r0:r1 + 1])
        dx, dy = bx - ax, by - ay
        L = dx * dx + dy * dy
        t = 0.0 if L == 0 else np.clip(((X - ax) * dx + (Y - ay) * dy) / L, 0.0, 1.0)
        d2 = (X - (ax + t * dx)) ** 2 + (Y - (ay + t * dy)) ** 2
        self.a[r0:r1 + 1, c0:c1 + 1][d2 <= r * r] = value

    def rect(self, cx, cy, w, h, value):
        c0, c1 = max(0, int((cx - w / 2) / G)), min(self.nx - 1, int((cx + w / 2) / G))
        r0, r1 = max(0, int((cy - h / 2) / G)), min(self.ny - 1, int((cy + h / 2) / G))
        self.a[r0:r1 + 1, c0:c1 + 1] = value

    def label(self):
        """Connected components, 4-connected, run-length union-find. Returns int32 array."""
        a = self.a
        lab = np.zeros(a.shape, dtype=np.int32)
        parent = [0]
        prev_runs = []
        for r in range(self.ny):
            row = a[r]
            if not row.any():
                prev_runs = []
                continue
            d = np.diff(np.concatenate(([0], row.astype(np.int8), [0])))
            starts, ends = np.nonzero(d == 1)[0], np.nonzero(d == -1)[0] - 1
            runs = []
            for c0, c1 in zip(starts, ends):
                rid = None
                for p0, p1, pid in prev_runs:
                    if p0 <= c1 and c0 <= p1:
                        pr = find(parent, pid)
                        if rid is None:
                            rid = pr
                        elif pr != rid:
                            parent[pr] = rid
                if rid is None:
                    parent.append(len(parent))
                    rid = len(parent) - 1
                runs.append((c0, c1, rid))
                lab[r, c0:c1 + 1] = rid
            prev_runs = runs
        roots = np.array([find(parent, i) for i in range(len(parent))], dtype=np.int32)
        uniq = {v: i for i, v in enumerate(sorted(set(roots.tolist())))}
        return np.array([uniq[v] for v in roots], dtype=np.int32)[lab]


def find(parent, i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]
        i = parent[i]
    return i


def paint(ras, regions, draws, flashes):
    for pol, pts in regions:
        ras.polygon(pts, pol == "D")
    for pol, ap, p0, p1 in draws:
        if ap is None:
            continue
        w = ap[1] if ap[0] == "C" else min(ap[1], ap[2])
        ras.capsule(p0, p1, w / 2, pol == "D")
    for pol, ap, (x, y) in flashes:
        if ap[0] == "C":
            ras.capsule((x, y), (x, y), ap[1] / 2, pol == "D")
        else:
            ras.rect(x, y, ap[1], ap[2], pol == "D")


def write_png(path, rgb):
    """8-bit RGB PNG from a (h, w, 3) uint8 array, standard library only."""
    import zlib, struct
    h, w, _ = rgb.shape
    raw = b"".join(bytes([0]) + rgb[r].tobytes() for r in range(h))

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    png = bytes([137, 80, 78, 71, 13, 10, 26, 10])
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b"")
    open(path, "wb").write(png)


# ------------------------------------------------------------------ what the holes are
# Socket pad offsets of TS06_IN12_Socket (KiCad, y down) -> Gerber (y up): y negated.
SOCKET_X = [13.21, 36.57, 63.99, 87.37]
SOCKET_Y = 20.07
SOCKET_PADS = {1: (-3.981, 8.002), 2: (0.0, 8.99), 3: (3.987, 8.002), 4: (5.74, 4.49), 5: (5.74, 0.0),
               6: (5.74, -4.5), 7: (3.987, -8.0), 8: (0.0, -8.99), 9: (-3.99, -8.01), 10: (-5.74, -4.5),
               11: (-5.74, 0.0), 12: (-5.74, 4.49)}
# ИН-12А datasheet: pin 1 anode, pins 2..11 cathodes 0 9 8 7 6 5 4 3 2 1, pin 12 n/c (comma on
# ИН-12Б). Pin d sits on socket pad ((7 - d) mod 12) + 1 (footprint description, confirmed by
# the anode: d = 1 -> pad 7, the one hole whose copper is unique per tube).
IN12_PIN_FUNC = {1: "A", 2: "0", 3: "9", 4: "8", 5: "7", 6: "6", 7: "5", 8: "4", 9: "3", 10: "2", 11: "1", 12: "NC"}
IN12_PAD_FUNC = {((7 - d) % 12) + 1: f for d, f in IN12_PIN_FUNC.items()}
# К155ИД1 / SN74141, DIP-16 (datasheet): the inputs and outputs are not in numeric order.
K155 = {1: "Q8", 2: "Q9", 3: "A1", 4: "D8", 5: "VCC", 6: "B2", 7: "C4", 8: "Q2",
        9: "Q3", 10: "Q7", 11: "Q6", 12: "GND", 13: "Q4", 14: "Q5", 15: "Q1", 16: "Q0"}
# firmware: digit d is shown by writing code digitMask[d] (BOARD_TYPE 0, confirmed on the bench)
DIGIT_MASK0 = [7, 3, 6, 4, 1, 9, 8, 0, 5, 2]
NANO_LEFT = ["TX1", "RX1", "RST_L", "GND_L", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10", "D11", "D12"]
NANO_RIGHT = ["VIN", "GND", "RST", "5V", "A7", "A6", "A5", "A4", "A3", "A2", "A1", "A0", "REF", "3V3", "D13"]
OPTO_PIN = {(0, 0): "1 LED+", (0, 1): "2 LED-", (1, 1): "3 E", (1, 0): "4 C"}   # (column, upper?)
# TLP627 DIP-4: 1 LED anode, 2 LED cathode, 3 emitter, 4 collector. Pins 1 and 4 share an end.


def named_positions():
    """{name: (x, y)} for every hole this tool knows. Every entry must be a real drilled hole."""
    N = {}
    for k, cx in enumerate(SOCKET_X):
        for pad, (dx, dy) in SOCKET_PADS.items():
            N[f"V{k + 1}.{pad}:{IN12_PAD_FUNC[pad]}"] = (cx + dx, SOCKET_Y + dy)
    for i, nm in enumerate(NANO_LEFT):
        N[f"U1.{nm}"] = (54.35, 76.45 - 2.54 * i if nm != "D12" else 40.64)
    for i, nm in enumerate(NANO_RIGHT):
        N[f"U1.{nm}"] = (69.59, 76.45 - 2.54 * i)
    for p in range(1, 9):
        N[f"D1.{p}:{K155[p]}"] = (78.23, 70.36 - 2.54 * (p - 1))
        N[f"D1.{p + 8}:{K155[p + 8]}"] = (85.85, 52.58 + 2.54 * (p - 1))
    for u, y0 in ((2, 51.81), (3, 57.91), (4, 64.01), (5, 70.10)):
        for (col, up), pin in OPTO_PIN.items():
            N[f"U{u}.{pin}"] = (43.69 if col == 0 else 36.07, y0 + 2.54 * up)
    for k in range(7):
        N[f"P1.{k + 1}"] = (3.55, 9.91 + 2.54 * k)
        N[f"P2.{k + 1}"] = (3.55, 50.04 + 2.54 * k)
    for k in range(10):
        N[f"P3.{k + 1}"] = (96.52, 7.37 + 2.54 * k)
        N[f"P4.{k + 1}"] = (96.52, 47.50 + 2.54 * k)
    for i, nm in enumerate(["-", "NC", "C", "D", "+"]):
        N[f"RTCmini.{nm}"] = (78.48 + 2.54 * i, 37.85)
    for i, nm in enumerate(["32K", "SQW", "SCL", "SDA", "VCC", "GND"]):
        N[f"RTCzs042.{nm}"] = (75.94 + 2.54 * i, 41.66)
    N.update({"PWR.GND": (74.67, 77.47), "PWR.5V": (74.67, 74.93),
              "C470u.-": (81.53, 77.47), "C470u.+": (81.53, 74.93),
              "Ccer.1": (78.56, 49.02), "Ccer.2": (83.56, 49.02),
              "VT1_IRF840.S": (19.33, 60.20), "VT1_IRF840.D": (21.87, 60.20), "VT1_IRF840.G": (24.41, 60.20),
              "L1_220u.1": (17.02, 65.28), "L1_220u.2": (24.64, 65.28),
              "VD1_HER106.A": (14.73, 65.28), "VD1_HER106.K": (6.98, 65.28),
              "C1_4u7_350V.+": (5.84, 69.60), "C1_4u7_350V.-": (5.84, 74.68),
              "Rgate_100.1": (39.62, 48.51), "Rgate_100.2": (49.78, 48.51),
              "Ranode_10k.1": (13.97, 61.97), "Ranode_10k.2": (13.97, 51.81),
              "RP1_470k.a": (26.41, 75.44), "RP1_470k.b": (28.95, 77.98), "RP1_470k.c": (31.49, 75.44),
              "Rled_470.1": (34.29, 76.96), "Rled_470.2": (41.91, 76.96),
              "Rdot_150.1": (7.11, 61.47), "Rdot_150.2": (7.11, 51.31),
              "Rbackl_100.1": (39.88, 43.43), "Rbackl_100.2": (47.50, 43.43),
              "Rbuz_100.1": (51.05, 66.04), "Rbuz_100.2": (51.05, 76.20),
              "BUZ.-": (45.72, 75.95), "BUZ.+": (48.26, 75.95)})
    for s, x0 in ((1, 15.34), (2, 28.04), (3, 40.74)):
        N[f"S{s}.1"], N[f"S{s}.2"] = (x0, 36.07), (x0 + 6.5, 36.07)
        N[f"S{s}.3"], N[f"S{s}.4"] = (x0, 40.57), (x0 + 6.5, 40.57)
    for k, x0 in enumerate((12.19, 35.56, 62.99, 86.10)):
        N[f"HL{k + 1}.1"], N[f"HL{k + 1}.2"] = (x0, 4.06), (x0 + 2.54, 4.06)
    N["HL5dot.1"], N["HL5dot.2"] = (48.51, 2.79), (51.05, 2.79)
    return N


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    layers = {lay: read_gerber(os.path.join(SRC, fn))
              for lay, fn in (("B", "Gerber_BottomLayer.GBL"), ("F", "Gerber_TopLayer.GTL"))}
    holes = read_drill(os.path.join(SRC, "Gerber_Drill_PTH.DRL"))
    npth = read_drill(os.path.join(SRC, "Gerber_Drill_NPTH.DRL"))
    lab, rasters = {}, {}
    for lay, (regions, draws, flashes) in layers.items():
        ras = Raster(W, H)
        paint(ras, regions, draws, flashes)
        lab[lay], rasters[lay] = ras.label(), ras
        print(f"layer {lay}: {len(regions)} regions, {len(draws)} draws, {len(flashes)} flashes, "
              f"{ras.a.sum() * G * G:.0f} mm2 copper, {lab[lay].max()} islands", file=sys.stderr)
    if "--png" in sys.argv:
        out = os.path.join(SRC, "gyver_copper.png")
        b, f = rasters["B"].a[::-1], rasters["F"].a[::-1]
        rgb = np.zeros(b.shape + (3,), dtype=np.uint8) + 24
        rgb[b], rgb[f], rgb[b & f] = (40, 90, 220), (220, 60, 40), (200, 60, 200)
        for d, x, y in holes + npth:
            r, c, k = rgb.shape[0] - 1 - int(y / G), int(x / G), max(1, int(d / G / 2))
            rgb[max(0, r - k):r + k + 1, max(0, c - k):c + k + 1] = 255
        write_png(out, rgb)
        print(f"wrote {out}", file=sys.stderr)

    # one net id per hole: the islands it touches on both layers, unioned
    parent = {}

    def f(k):
        parent.setdefault(k, k)
        while parent[k] != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k

    ids_of = {}
    for d, x, y in holes:
        r, c = int(y / G), int(x / G)
        ids = []
        for lay in ("B", "F"):
            win = lab[lay][max(0, r - 3):r + 4, max(0, c - 3):c + 4]
            ids += [(lay, int(v)) for v in np.unique(win) if v != 0]
        for a in ids[1:]:
            parent[f(ids[0])] = f(a)
        ids_of[(x, y)] = ids[0] if ids else None

    # name every hole; assert the hard-coded positions are real holes
    names, pts = {}, np.array([(x, y) for _, x, y in holes])
    for nm, (x, y) in named_positions().items():
        d = np.hypot(pts[:, 0] - x, pts[:, 1] - y)
        i = int(np.argmin(d))
        assert d[i] < 0.3, f"{nm} expected at ({x}, {y}), nearest hole {d[i]:.2f} mm away"
        key = (holes[i][1], holes[i][2])
        assert key not in names, f"{nm} collides with {names[key]}"
        names[key] = nm
    unnamed = [(x, y) for _, x, y in holes if (x, y) not in names]
    assert not unnamed, f"unnamed holes: {unnamed}"

    by_net = {}
    for (x, y), k in ids_of.items():
        by_net.setdefault(f(k) if k else None, []).append(names[(x, y)])
    print(f"{len(holes)} plated holes, {len(npth)} unplated, {len(by_net)} nets touching holes\n")
    for n, items in sorted(by_net.items(), key=lambda kv: (-len(kv[1]), sorted(kv[1]))):
        items.sort()
        if len(items) > 1:
            print(f"{len(items):3d}  " + "  ".join(items))
    singles = sorted(i[0] for i in by_net.values() if len(i) == 1)
    print("\nno connection: " + "  ".join(singles))
    print("\nunplated: " + "  ".join(f"({x:.2f},{y:.2f}) d{d:.1f}" for d, x, y in npth))

    # ---- the display chain: К155ИД1 output -> P4 -> P3 -> socket pad -> ИН-12А cathode
    net_of = {nm: f(ids_of[xy]) for xy, nm in names.items() if ids_of[xy]}
    print("\nК155ИД1 output -> header pin -> socket pad (all four tubes) -> ИН-12А cathode, "
          "against firmware digitMask (BOARD_TYPE 0):")
    ok = 0
    for out in range(10):
        pin = next(p for p, fn in K155.items() if fn == f"Q{out}")
        net = net_of[f"D1.{pin}:Q{out}"]
        p4 = next(k for k in range(1, 11) if net_of[f"P4.{k}"] == net)
        tube_net = net_of[f"P3.{p4}"]
        pads = sorted({nm.split(".")[1] for nm, n in net_of.items() if n == tube_net and nm.startswith("V")})
        assert len(pads) == 1, pads
        pad, func = pads[0].split(":")
        digit = DIGIT_MASK0.index(out)          # the digit the firmware shows with this code
        mark = "ok" if func == str(digit) else "MISMATCH"
        ok += mark == "ok"
        print(f"  Q{out} pin {pin:2d} -> P4.{p4:<2d} = P3.{p4:<2d} -> pad {pad:>2s} = cathode {func}"
              f"   firmware shows digit {digit} with code {out}: {mark}")
    print(f"  {ok}/10 agree")


if __name__ == "__main__":
    main()
