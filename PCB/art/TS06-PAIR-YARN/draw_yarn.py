#!/usr/bin/env python3
"""TS06 pair YARN: one fascia face and one display light layout, drawn as one object.

    python3 PCB/art/TS06-PAIR-YARN/draw_yarn.py            # all pictures and all measures
    python3 PCB/art/TS06-PAIR-YARN/draw_yarn.py fascia     # only the fascia's pictures
    python3 PCB/art/TS06-PAIR-YARN/draw_yarn.py disp       # only the display's picture

Run it from the repo root. It reads the two board files (yarn_boards.py) and two firmware files (the
card band's data), writes PNG pictures and measures.txt beside itself, and edits nothing else. The
pictures are SVG inside HTML, turned into PNG by a headless browser and ImageMagick (yarn_kit.render);
the intermediate files go to a temporary folder.

The board is the cloth, the LED filaments are the thread. One thread runs from the spool (the MODE
dial) through both boards and ends in a needle. Where it lies on the cloth it is a lit filament; where
it runs under, a row of white dots.

Sources of the fixed numbers:
  boards        PCB/TS06-FASCIA-rhythm (fascia R rev B), PCB/TS06-DISP: outline, holes, parts, pads,
                tracks, texts (read by script)
  light base    PCB/TS06-routing-plan.md section 2.3 and 2.4 (BASE and J2 below, typed in from its tables)
  rings, marks  PCB/art/TS06-FRONT-merge.md section 6 (the "rings-and-dots" base)
  display lines PCB/art/TS06-DISP-final-3.md and its grill (disp-3-4's slots and holes)
  name widths   tools/fascia_art.py FONT (KiCad's stroke font, measured there with pcbnew)
  card data     firmware/nixieClock_TS06/ts06pair.ino, firmware/ts06_bringup/ts06_bringup.ino
"""
import math, os, re, sys, tempfile
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import yarn_boards as yb
from yarn_kit import (P, arc, length, rounded, resample, mirror_x, rrect, text_strokes, Mask, edt, gap, edge_inset,
                      clip_run, d_of, d_segs, esc, render)

PX = 11.5                    # pixels per mm in the sheets
RES = 20                     # pixels per mm in the checks (0.05 mm)
OUT = HERE
LOG = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    LOG.append(s)


# ------------------------------------------------------------------------------------ inks and rules (mm)
W_WHITE, W_GOLD = 0.18, 0.24             # weave lines (the fab's floor for white is 0.15; the brief says draw at 0.16 or more)
WG = 0.22                                # white to gold, edge to edge, at every crossing of the weave
DOT_R, DOT_PITCH = 0.20, 0.95            # the thread under the cloth
C_LEGEND = 0.85                          # weave to a legend (rule 0.75)
C_WINDOW = 0.45                          # any ink to a bare-FR4 window (rule 0.35)
C_GOLD = 0.45                            # gold island to other copper (rule 0.35)
C_WHITE_GOLD = 0.32                      # feature white to gold (rule 0.15)
EDGE_WHITE, EDGE_GOLD = 0.40, 1.45       # to the board edge (gold: pass 4's checker, 1.4)
SCREW_HEAD, SCREW_GOLD = 2.25, 3.0       # M2.5 head radius; gold keeps 3.0 from the hole's centre
KICAD_INK = {"NORMAL": (0.304, 5.571, 6.005), "SET TIME": (0.256, 6.286, 6.767), "DISPLAY": (0.304, 5.619, 6.052),
             "AMBIENT": (0.161, 6.000, 6.290), "FORMAT/DATE": (0.304, 9.810, 10.338), "INFO": (0.304, 3.000, 3.529),
             "MODE": (0.304, 3.667, 4.195), "FIELD": (0.304, 3.619, 4.148), "SUB": (0.256, 2.619, 3.100),
             "1": (0.256, 0.571, 1.052), "2": (0.209, 0.619, 1.052), "3": (0.209, 0.619, 1.052),
             "4": (0.256, 0.619, 1.052), "5": (0.256, 0.571, 1.052), "6": (0.256, 0.571, 1.052)}

# the common light base, PCB/TS06-routing-plan.md section 2.3: place: (source, anode pad, cathode pad, pad size, channel)
BASE = {
    "M":   ("38 flex",    (12.29, 5.26),   (15.76, 29.01),  (1.5, 1.5), "CH1"),
    "FU":  ("18.5 rigid", (52.74, 5.91),   (74.0, 8.0),     (1.5, 1.5), "CH2"),
    "FD":  ("18.5 rigid", (52.74, 26.11),  (74.0, 28.2),    (1.5, 1.5), "CH2"),
    "SU":  ("18.5 rigid", (98.66, 5.91),   (77.4, 8.0),     (1.5, 1.5), "CH3"),
    "SD":  ("18.5 rigid", (98.64, 25.06),  (77.4, 28.2),    (1.5, 1.5), "CH3"),
    "KM":  ("38 flex",    (145.61, 27.69), (144.39, 5.26),  (1.5, 1.5), "CH4"),
    "KP":  ("38 flex",    (173.99, 27.79), (177.39, 5.26),  (1.5, 1.5), "CH4"),
    "S1":  ("18.5 rigid", (110.15, 11.6),  (129.0, 10.5),   (1.2, 1.5), "CH5"),
    "T":   ("18.5 rigid", (109.3, 24.5),   (109.3, 6.0),    (1.2, 1.2), "CH5"),
    "SCR": ("18.5 rigid", (107.59, 34.96), (130.14, 34.96), (1.5, 1.5), "CH5"),
    "P":   ("18.5 rigid", (149.73, 6.3),   (172.07, 6.3),   (1.0, 1.5), "CH6"),
    "BP":  ("18.5 rigid", (129.4, 23.8),   (129.4, 6.5),    (1.5, 1.2), "CH6"),
}
BARS = {"FU": ((54.74, 5.9), (73.24, 5.9)), "FD": ((54.74, 26.1), (73.24, 26.1)), "SU": ((78.12, 5.9), (96.62, 5.9)),
        "SD": ((78.12, 26.1), (96.62, 26.1)), "S1": ((109.64, 8.35), (128.13, 8.35)), "T": ((107.3, 5.8), (107.3, 24.3)),
        "SCR": ((109.6, 35.8), (128.1, 35.8)), "P": ((151.65, 6.3), (170.15, 6.3)), "BP": ((131.36, 5.9), (131.36, 24.4))}
J2 = (110.3, 12.6, 129.7, 21.1)          # courtyard on the back, routing plan section 2.4 (d)
RING_R = 7.9                             # FIELD's and SUB's gold rings (front-merge section 6)
WARM, PINK, BLUE, GREEN, WHITE = "warm", "pink", "blue", "green", "white"
TINT = {WARM: ("#ff8a1c", "#ffd9a2"), PINK: ("#ff3f9a", "#ffc2de"), BLUE: ("#2f7bff", "#bcd6ff"),
        GREEN: ("#22d15a", "#c4f7cf"), WHITE: ("#cfdcff", "#ffffff")}


class Art:
    """Everything drawn on one board, by ink. Lines are (points, width); dots are (x, y, r)."""

    def __init__(self, board, w, h, corner, edge_white=EDGE_WHITE, edge_gold=EDGE_GOLD):
        self.B, self.w, self.h, self.corner = board, w, h, corner
        self.white, self.wdots, self.gold, self.gdots, self.gpoly = [], [], [], [], []
        self.wbutt, self.gbutt = [], []             # the weave: straight dashes with square ends, (a, b)
        self.legend_w, self.legend_g = [], []       # the fixed names (white) and signs (gold): (points, width)
        self.base_gold, self.base_gdots = [], []    # fixed gold of the base
        self.windows = []                           # bare-FR4 windows: (points, width, light name)
        self.lights = []                            # dict(name, part, place, pts, w, lit, dye, ch, note)
        self.thread = []                            # ("lit" | "under" | "hid", points) in the thread's order
        self.kw = Mask(w, h, RES)                   # keep-outs for the weave's white, its gold, and the thread's dots
        self.kg = Mask(w, h, RES)
        self.kt = Mask(w, h, RES)
        self.kw.a |= edge_inset(w, h, corner, RES, edge_white + W_WHITE / 2)
        self.kg.a |= edge_inset(w, h, corner, RES, edge_gold + W_GOLD / 2)
        self.kt.a |= edge_inset(w, h, corner, RES, 0.3 + DOT_R)

    def keep(self, pts, half, cw, cg, ct):
        """Grow a stroked shape by its clearances into the three keep-out masks."""
        if cw is not None:
            self.kw.line(pts, half + cw + W_WHITE / 2)
        if cg is not None:
            self.kg.line(pts, half + cg + W_GOLD / 2)
        if ct is not None:
            self.kt.line(pts, half + ct + DOT_R)

    def add_white(self, pts, w, weave_clear=0.40):
        self.white.append((pts, w))
        self.keep(pts, w / 2, weave_clear, C_WHITE_GOLD, None)

    def add_gold(self, pts, w, base=False):
        (self.base_gold if base else self.gold).append((pts, w))
        self.keep(pts, w / 2, C_WHITE_GOLD, C_GOLD, C_WHITE_GOLD)

    def add_window(self, pts, w, name):
        self.windows.append((pts, w, name))
        self.keep(pts, w / 2, C_WINDOW, C_WINDOW, C_WINDOW)

    def dots(self, pts, pitch=DOT_PITCH, r=DOT_R, first=None):
        """White dots along a path, dropped where the thread's keep-out says so. Returns how many were set."""
        if first is None:                           # fit the pitch to the path, so a path and its mirror image
            L = length(pts)                         # (or the same path walked backwards) get the same dots
            n_fit = max(1, int(round(L / pitch)))
            pitch = L / n_fit
        cand = resample(pts, pitch * (1 - 1e-9), first)
        if not cand:
            return 0
        bad = self.kt.at([p[0] for p in cand], [p[1] for p in cand])
        n = 0
        for p, b in zip(cand, bad):
            if not b:
                self.wdots.append((p[0], p[1], r))
                self.kw.disc(p, r + 0.45 + W_WHITE / 2)
                self.kg.disc(p, r + 0.30 + W_GOLD / 2)
                n += 1
        return n


# ------------------------------------------------------------------------------------ the weave
def twill(i, j):
    return (i + j) % 4 < 2


def plain(i, j):
    return (i + j) % 2 == 0


def diamond(centres):
    def f(i, j):
        return (min(abs(i - c) for c in centres) + abs(j)) % 4 < 2
    return f


def weave(A, zones, rows, y0, seam=0.9):
    """Gold warp (plumb) and white weft (level) with true over and under. zones: (x0, x1, pitch, anchor x, draft);
    draft(i, j) is True where the warp lies on top; i counts warps from the anchor, j counts wefts from y0."""
    eg, ew = W_WHITE / 2 + WG, W_GOLD / 2 + WG
    js = [int(round((y - y0))) for y in rows]
    nw = ng = 0
    for (x0, x1, px, xa, draft) in zones:
        lo, hi = x0 + (seam if x0 > 0 else 0), x1 - (seam if x1 < A.w else 0)
        i_min, i_max = int(math.ceil((lo + 0.3 - xa) / px)), int(math.floor((hi - 0.3 - xa) / px))
        for i in range(i_min, i_max + 1):                       # the warps
            x, run = xa + i * px, None
            for k, j in enumerate(js + [None]):
                over = j is not None and draft(i, j)
                if over and run is None:
                    run = k
                if not over and run is not None:
                    ya = (rows[run - 1] + eg) if run > 0 else 0.0
                    yb_ = (rows[k] - eg) if k < len(rows) else A.h
                    for a, b in clip_run((x, ya), (x, yb_), A.kg, least=0.5):
                        A.gbutt.append((a, b))
                        ng += 1
                    run = None
        for k, j in enumerate(js):                              # the wefts
            y, run = rows[k], None
            for i in list(range(i_min, i_max + 1)) + [None]:
                under = i is not None and not draft(i, j)
                if under and run is None:
                    run = i
                if not under and run is not None:
                    xa_ = (xa + (run - 1) * px + ew) if run > i_min else lo
                    xb_ = (xa + i * px - ew) if i is not None else hi
                    for a, b in clip_run((xa_, y), (xb_, y), A.kw, least=0.4):
                        A.wbutt.append((a, b))
                        nw += 1
                    run = None
    return nw, ng


def draft_mismatch(draft, i_axis2, n_i, n_j):
    """Cells of a draft that differ from their mirror image about the warp axis i = i_axis2 / 2 (0 = exactly symmetric)."""
    bad = 0
    for i in range(-n_i, n_i + 1):
        for j in range(-n_j, n_j + 1):
            if draft(i, j) != draft(i_axis2 - i, j) or draft(i, j) != draft(i, -j):
                bad += 1
    return bad


# ------------------------------------------------------------------------------------ the card band's data
def card_data():
    """The ladder codes, read from the firmware: six MODE positions on A6, four lever states on A7."""
    fw = os.path.join(yb.ROOT, "firmware")
    a = open(os.path.join(fw, "nixieClock_TS06", "ts06pair.ino"), encoding="utf-8", errors="replace").read()
    b = open(os.path.join(fw, "ts06_bringup", "ts06_bringup.ino"), encoding="utf-8", errors="replace").read()
    m = re.search(r"ADC\s+(\d+(?:/\d+){5})", a)
    mode = [int(v) for v in m.group(1).split("/")]
    f = re.search(r"\(analogRead\(ROTARY\)\s*\+\s*(\d+)\)\s*/\s*(\d+)\s*\+\s*1", a)
    half, step = int(f.group(1)), int(f.group(2))
    assert [(c + half) // step + 1 for c in mode] == [1, 2, 3, 4, 5, 6], "the firmware's rounding does not give 1..6"
    lv = re.search(r"LV\[4\]\s*=\s*\{([^}]*)\}", b)
    lever = [int(v) for v in lv.group(1).split(",")]
    return mode, lever, (half, step)


# ------------------------------------------------------------------------------------ the fascia
def fascia():
    B = yb.load(yb.FASCIA)
    x0, y0, x1, y1 = B["box"]
    A = Art(B, x1 - x0, y1 - y0, 1.5)
    part = {p["ref"]: p for p in B["parts"]}
    DIAL, FIELD, SUB = [(part[r]["x"], part[r]["y"]) for r in ("SW1", "SW2", "SW3")]
    KMc, KPc = [(part[r]["x"], part[r]["y"]) for r in ("SW4", "SW5")]
    A.ctl = dict(DIAL=DIAL, FIELD=FIELD, SUB=SUB, KM=KMc, KP=KPc)
    A.screws = [(p["x"], p["y"]) for p in B["parts"] if p["ref"].startswith("H")]
    A.part_r = {"SW1": 9.6, "SW2": 6.0, "SW3": 6.0, "SW4": 6.8, "SW5": 6.8}        # what stands on the face (assumed)
    yc = FIELD[1]                                                                   # the controls' line, y 16
    pair_x = (FIELD[0] + SUB[0]) / 2                                                # 75.68
    keys_x = (KMc[0] + KPc[0]) / 2                                                  # 160.9
    sec_x = (BARS["S1"][0][0] + BARS["S1"][1][0]) / 2                               # 118.885, the S bar's middle
    A.axes = dict(pair=pair_x, keys=keys_x, sec=sec_x)

    # ---- fixed: holes, parts, names, the index (from the file)
    for ref, r in A.part_r.items():
        c = (part[ref]["x"], part[ref]["y"])
        for m in (A.kw, A.kg, A.kt):
            m.disc(c, r + 0.3)
    for c in A.screws:
        A.kw.disc(c, SCREW_HEAD + 0.3 + W_WHITE / 2)
        A.kt.disc(c, SCREW_HEAD + 0.3 + DOT_R)
        A.kg.disc(c, SCREW_GOLD + 0.07 + W_GOLD / 2)
    A.boxes = {}
    for t in B["texts"]:
        if t["layer"] not in ("F.SilkS", "F.Cu"):
            continue
        ink = KICAD_INK.get(t["s"])
        st, box = text_strokes(t["s"], t["x"], t["y"], t["h"], t["just"], ink=(ink[0], ink[1]) if ink else None,
                               advance=ink[2] if ink else None)
        A.boxes[t["s"]] = box
        for line in st:
            (A.legend_w if t["layer"] == "F.SilkS" else A.legend_g).append((line, t["t"]))
            A.keep(line, t["t"] / 2, C_LEGEND, C_LEGEND, 0.5)
    for g in B["graphics"]:                    # rev B's own gold: the dial's index arc and ticks stay (0.65 wide);
        if g["layer"] == "F.Cu" and abs(g["w"] - 0.65) < 0.01:   # the SUB box and its runs (0.6) are replaced by the base's rings
            A.add_gold(g["pts"], g["w"], base=True)
    A.dropped_gold = sum(1 for g in B["graphics"] if g["layer"] == "F.Cu" and abs(g["w"] - 0.6) < 0.01)

    # ---- the base's rings, link and marks (front-merge section 6): the two hoops
    for c in (FIELD, SUB):
        A.add_gold(arc(c, RING_R, 0, 360), 0.6, base=True)
    A.add_gold([(FIELD[0] + RING_R, yc), (SUB[0] - RING_R, yc)], 0.6, base=True)
    A.base_gdots.append((pair_x, yc, 0.55))                                          # the GND tie on the link
    A.base_gdots.append((FIELD[0], yc - RING_R, 0.75))                               # SET TIME: a filled dot, ring top
    A.marks = [(56.55, 13.36), (56.55, 18.64), (FIELD[0], yc + RING_R)]              # DISPLAY, AMBIENT, FORMAT/DATE: circles
    for mk in A.marks:
        A.add_gold(arc(mk, 0.80, 0, 360), 0.30, base=True)
    A.keep([(FIELD[0], yc - RING_R)], 0.75, C_WHITE_GOLD, C_GOLD, C_WHITE_GOLD)

    # ---- the windows (mine) on the base's sources: every one is a stitch of the one thread
    def light(name, place, pts, w, dye, note=""):
        A.add_window(pts, w, name)
        A.lights.append(dict(name=name, win=name, part=BASE[place][0], place=place, pts=pts, w=w, dye=dye, ch=BASE[place][4], note=note))
    m_arc = arc(DIAL, 14.2, 230, 130)                                                # the thread on the spool, top end first
    light("MODE turn", "M", m_arc, 1.3, WARM)
    st = 5.5                                                                         # half a lever stitch
    yu, yd = yc - 9.8, yc + 9.8                                                      # 6.2 and 25.8: inside the bars' 2.0 bodies
    fd = [(FIELD[0] - st, yd), (FIELD[0] + st, yd)]
    sd = [(SUB[0] - st, yd), (SUB[0] + st, yd)]
    su = [(SUB[0] + st, yu), (SUB[0] - st, yu)]
    fu = [(FIELD[0] + st, yu), (FIELD[0] - st, yu)]
    light("FIELD down", "FD", fd, 1.2, GREEN)
    light("SUB down", "SD", sd, 1.2, GREEN)
    light("SUB up", "SU", su, 1.2, GREEN)
    light("FIELD up", "FU", fu, 1.2, GREEN)
    kp_arc = arc(KPc, 10.0, -75, 75)
    km_arc = arc(KMc, 10.0, 105, 255)
    light("key + turn", "KP", kp_arc, 1.3, WHITE)
    pr = [(keys_x + 1.5, 5.85), (keys_x + 7.0, 6.75)]                                # P: two stitches that meet at noon
    pl = [(keys_x - 7.0, 6.75), (keys_x - 1.5, 5.85)]
    A.add_window(pr, 1.2, "P")
    A.add_window(pl, 1.2, "P")
    A.lights.append(dict(name="P, the noon stitch", win="P", part=BASE["P"][0], place="P", pts=pr + pl, w=1.2, dye=PINK, ch="CH6",
                         note="two stitches, one each side of the thread to the display"))
    light("key - turn", "KM", km_arc, 1.3, WHITE)
    sy = BARS["S1"][0][1]                                                            # 8.35, the S1 bar's axis
    A.s_slits = []
    for k in range(13):                                                              # S: thirteen turns on the bobbin = 0 to 60 s
        x = sec_x + (k - 6) * 1.2
        hh = 1.05 if k % 3 == 0 else 0.65
        A.s_slits.append([(x, sy - hh), (x, sy + hh)])
        A.add_window(A.s_slits[-1], 0.5, "S")
    A.lights.append(dict(name="S, the bobbin", win="S", part=BASE["S1"][0], place="S1", pts=[(sec_x - 7.2, sy), (sec_x + 7.2, sy)], w=0.5,
                         dye=BLUE, ch="CH5", note="13 slits 0.5 wide, 1.2 apart: every 5 s of a minute, the 15 s ones tall"))

    # ---- the spool, the hoops' inner edge, the shuttle, the card
    for r, a0 in ((12.3, 250), (16.1, 228)):                                         # the turns beside the lit one
        A.dots(arc(DIAL, r, a0, 360 - a0), pitch=0.8, r=0.16)
    for c in (FIELD, SUB):
        A.dots(arc(c, 6.85, 0, 360), pitch=0.86, r=0.15, first=0.0)
    tipL, tipR, hb = (sec_x - 15.5, sy), (sec_x + 15.5, sy), 3.5
    R_boat = 15.5 ** 2 / (2 * hb) + hb / 2
    a_half = math.degrees(math.asin(15.5 / R_boat))
    top = arc((sec_x, sy - hb + R_boat), R_boat, 270 - a_half, 270 + a_half)
    bot = arc((sec_x, sy + hb - R_boat), R_boat, 90 + a_half, 90 - a_half)
    A.shuttle = top + bot[::-1]
    a_in = math.degrees(math.asin(12.35 / R_boat))                                   # the wood stops where the metal tips start
    A.add_white(arc((sec_x, sy - hb + R_boat), R_boat, 270 - a_in, 270 + a_in), 0.22)
    A.add_white(arc((sec_x, sy + hb - R_boat), R_boat, 90 + a_in, 90 - a_in), 0.22)
    A.kw.poly(A.shuttle, grow=0.5)
    A.kg.poly(A.shuttle, grow=0.5)
    A.kt.poly(A.shuttle, grow=0.2)
    cav = rrect(sec_x - 8.4, sy - 2.05, sec_x + 8.4, sy + 2.05, 1.0)
    A.add_gold(cav, 0.24)
    for sgn in (-1, 1):                                                              # the shuttle's two metal tips
        h_tip = math.sqrt(R_boat ** 2 - 12.9 ** 2) - (R_boat - hb)
        tip = [(sec_x + sgn * 15.5, sy), (sec_x + sgn * 12.9, sy - h_tip), (sec_x + sgn * 12.9, sy + h_tip)]
        A.gpoly.append(tip)
        A.keep(tip + [tip[0]], 0.0, C_WHITE_GOLD, C_GOLD, C_WHITE_GOLD)
        for k in range(4):                                                           # the thread inside the shuttle
            A.wdots.append((sec_x + sgn * (9.25 + 0.95 * k), sy, DOT_R))
    mode, lever, rounding = card_data()
    A.card = dict(mode=mode, lever=lever, rounding=rounding, rows=[])
    bx = [sec_x + (b - 4.5) * 1.45 for b in range(10)]                               # bit 9 (512) at the left
    ys = [15.0 + 1.5 * r for r in range(6)] + [24.6 + 1.5 * r for r in range(4)]
    for (ya, yb_) in ((ys[0] - 1.0, ys[5] + 1.0), (ys[6] - 1.0, ys[9] + 1.0)):       # two laced cards
        xa, xb = bx[0] - 2.9, bx[9] + 2.9
        card = [(xa + 0.8, ya), (xb - 0.8, ya), (xb, ya + 0.8), (xb, yb_), (xa, yb_), (xa, ya + 0.8), (xa + 0.8, ya)]
        A.add_white(card, 0.18)
        A.kw.poly(card, grow=0.5)
        A.kg.poly(card, grow=0.5)
    for y, code in zip(ys, mode + lever):
        bits = [(code >> (9 - b)) & 1 for b in range(10)]
        A.card["rows"].append((y, code, bits))
        for x, bit in zip(bx, bits):
            if bit:
                A.gdots.append((x, y, 0.42))
            else:
                A.wdots.append((x, y, 0.13))
        for x in (bx[0] - 1.75, bx[9] + 1.75):                                       # the lacing holes
            A.white.append((arc((x, y), 0.36, 0, 360), 0.14))
    for x in (bx[0] - 1.75, bx[9] + 1.75):                                           # the lace between the two cards
        for y in (ys[5] + 0.75, ys[5] + 1.05, ys[5] + 1.35):
            A.wdots.append((x, y, 0.11))

    # ---- the thread, in order. "lit" pieces are the windows above; "under" pieces are dotted. Between zones it
    # runs on one low line (y 31.6); inside the levers' and the shuttle's zones its path is its own mirror image.
    low, ybot = 31.6, 33.4
    T = A.thread
    xi1, xi2, lx, rx = FIELD[0] + 10.6, SUB[0] - 10.6, FIELD[0] - 10.6, SUB[0] + 10.6
    xl = 101.2
    xr = 2 * sec_x - xl
    T.append(("lit", m_arc))
    T.append(("under", rounded([m_arc[-1], (21.6, low), (40.0, low)], 2.6) + rounded([(40.0, low), (53.0, low), (57.6, yd), fd[0]], 1.4)[1:]))
    T.append(("lit", fd))
    T.append(("under", rounded([fd[1], (xi1, yd), (xi1, yu), fu[0]], 4.8)))            # a turn round FIELD's hoop
    T.append(("lit", fu))
    T.append(("under", rounded([fu[1], (lx, yu), (lx, ybot), (rx, ybot), (rx, yu), su[0]], 4.8)))   # under both hoops
    T.append(("lit", su))
    T.append(("under", rounded([su[1], (xi2, yu), (xi2, yd), sd[0]], 4.8)))            # a turn round SUB's hoop
    T.append(("lit", sd))
    T.append(("under", rounded([sd[1], (2 * pair_x - 57.6, yd), (2 * pair_x - 53.0, low), (xl, low), (xl, sy), tipL], 1.4)))
    T.append(("lit", [(sec_x - 7.2, sy), (sec_x + 7.2, sy)]))
    T.append(("under", rounded([tipR, (xr, sy), (xr, low), (keys_x, low), (keys_x, pr[0][1] + 1.3)], 1.4)))
    T.append(("lit", pr))
    T.append(("under", [pr[1], kp_arc[0]]))
    T.append(("lit", kp_arc))                                                         # one turn round both keys
    T.append(("under", arc(KPc, 10.0, 75, 90) + [(KPc[0], yc + 10.0), (KMc[0], yc + 10.0)] + arc(KMc, 10.0, 90, 105)))
    T.append(("lit", km_arc))
    T.append(("under", [km_arc[-1], pl[0]]))
    T.append(("lit", pl))
    A.exit_x = keys_x
    T.append(("under", [(keys_x, pl[1][1] - 1.3), (keys_x, 0.0)]))
    cuts = (51.8, 2 * pair_x - 51.8, 2 * sec_x - (2 * pair_x - 51.8))                 # the seams the thread crosses on the low line

    def split(pts):
        out, cur = [], [pts[0]]
        for a, b in zip(pts, pts[1:]):
            for cx in cuts:
                if (a[0] - cx) * (b[0] - cx) < 0 and abs(a[1] - low) < 0.01 and abs(b[1] - low) < 0.01:
                    cur.append((cx, low))
                    out.append(cur)
                    cur = [(cx, low)]
            cur.append(b)
        return out + [cur]
    A.n_dots = sum(A.dots(part_) for kind, pts in T if kind == "under" for part_ in split(pts))

    # ---- eyelets round the screws, herringbone seams between the zones
    for c in A.screws:                                                               # white, because gold may not come within 1.4 of the edge
        A.dots(arc(c, 3.2, 0, 360), pitch=2 * math.pi * 3.2 / 24, r=0.16, first=0.0)
    half = pair_x - 51.8
    A.seams = [7.8, 51.8, pair_x + half, 2 * sec_x - (pair_x + half), 2 * keys_x - (2 * sec_x - (pair_x + half))]
    rows = [float(y) for y in range(1, 40)]
    for xs in A.seams:
        for y in rows:
            v = [(xs - 0.55, y + 0.3), (xs, y - 0.3), (xs + 0.55, y + 0.3)]
            for a, b in zip(v, v[1:]):
                for p, q in clip_run(a, b, A.kw, least=0.3):
                    A.white.append(([p, q], 0.18))
    for xs in A.seams:
        A.kw.rect(xs - 0.9, 0, xs + 0.9, A.h)
        A.kg.rect(xs - 0.9, 0, xs + 0.9, A.h)

    # ---- the ground: one cloth, six zones
    p_lev, p_key = (SUB[0] - FIELD[0]) / 24.0, (KPc[0] - KMc[0]) / 22.0
    d_lev, d_key = diamond((0, 24)), diamond((0, 22))
    A.zones = [(0.0, A.seams[0], 1.0, 4.5, plain, "left selvedge, plain"),
               (A.seams[0], A.seams[1], 1.0, DIAL[0], twill, "MODE, 2/2 twill, one way"),
               (A.seams[1], A.seams[2], p_lev, FIELD[0], d_lev, "levers, diamond twill on FIELD and SUB"),
               (A.seams[2], A.seams[3], 1.0, sec_x, plain, "shuttle, plain"),
               (A.seams[3], A.seams[4], p_key, KMc[0], d_key, "keys, diamond twill on - and +"),
               (A.seams[4], A.w, 1.0, 186.9, plain, "right selvedge, plain")]
    A.n_white, A.n_gold = weave(A, [z[:5] for z in A.zones], rows, yc)
    A.draft_bad = dict(levers=draft_mismatch(d_lev, 24, 30, 20), keys=draft_mismatch(d_key, 22, 30, 20))
    return A


# ------------------------------------------------------------------------------------ rasters of a finished board
def inks(A, ox=0.0, w=None):
    """The inks as rasters. "white" is all my white; "weave_w" only the weave's wefts; "feature" the rest of the white."""
    M = {k: Mask(w or A.w, A.h, RES, ox) for k in ("white", "weave_w", "weave_g", "feature", "gold", "legend", "window", "basegold")}
    for pts, wd in A.white:
        M["feature"].line(pts, wd / 2)
    for a, b in A.wbutt:
        M["weave_w"].butt(a, b, W_WHITE / 2)
    for x, y, r in A.wdots:
        M["feature"].disc((x, y), r)
    M["white"].a = M["weave_w"].a | M["feature"].a
    for x, y, r in A.base_gdots:
        M["basegold"].disc((x, y), r)
    for pts, w in A.gold:
        M["gold"].line(pts, w / 2)
    for a, b in A.gbutt:
        M["gold"].butt(a, b, W_GOLD / 2)
        M["weave_g"].butt(a, b, W_GOLD / 2)
    for x, y, r in A.gdots:
        M["gold"].disc((x, y), r)
    for poly in A.gpoly:
        M["gold"].poly(poly)
    for pts, w in A.base_gold:
        M["basegold"].line(pts, w / 2)
    for pts, w in A.legend_w + A.legend_g:
        M["legend"].line(pts, w / 2)
    for pts, w, name in A.windows:
        M["window"].line(pts, w / 2)
    return M


def check_fascia(A):
    say("== fascia R rev B, face YARN: measures (raster %d px per mm; a gap is the centre distance less one pixel)" % RES)
    B, M = A.B, inks(A)
    res = RES
    allgold = M["gold"].a | M["basegold"].a
    d_leg, d_win = edt(M["legend"].a, res, 3.0), edt(M["window"].a, res, 3.0)
    d_gold, d_bg = edt(allgold, res, 3.0), edt(M["basegold"].a, res, 3.0)
    out = {}

    def row(label, rule, got):
        out[label] = got
        say("   %-58s rule %-5s measured %s" % (label, rule, "none in reach" if got is None else "%.2f at (%.1f, %.1f)" % (got[0], got[1][0], got[1][1])))
    row("the weave's white to a legend (names, 1-6, - and +)", "0.75", gap(d_leg, M["weave_w"].a, res))
    row("the weave's gold to a legend", "0.75", gap(d_leg, M["gold"].a, res))
    row("the thread's dots and other white to a legend", "0.48", gap(d_leg, M["feature"].a, res))
    row("white to a window", "0.35", gap(d_win, M["white"].a, res))
    row("gold (mine and the base's) to a window", "0.30", gap(d_win, allgold, res))
    row("white to gold", "0.15", gap(d_gold, M["white"].a, res))
    row("my gold to the base's gold (rings, link, marks, index)", "0.35", gap(d_bg, M["gold"].a, res))
    row("a window to a legend", "0.30", gap(d_leg, M["window"].a, res))
    # holes, edge, screws
    hole = Mask(A.w, A.h, res)
    for p in B["pads"]:
        if p["drill"] and not p["ref"].startswith("H"):
            hole.disc((p["x"], p["y"]), p["drill"][0] / 2)
    d_hole = edt(hole.a, res, 6.0)
    row("a window to a control's hole", "-", gap(d_hole, M["window"].a, res))
    edge = Mask(A.w, A.h, res)
    edge.a |= edge_inset(A.w, A.h, A.corner, res, 0.0001)
    edge.a[0, :] = edge.a[-1, :] = True
    edge.a[:, 0] = edge.a[:, -1] = True
    d_edge = edt(edge.a, res, 3.0)
    g = gap(d_edge, M["gold"].a, res)
    row("gold to the board edge", "1.40", (g[0] + 0.5 / res, g[1]))
    g = gap(d_edge, M["white"].a, res)
    row("white to the board edge", "0.30", (g[0] + 0.5 / res, g[1]))
    scr = Mask(A.w, A.h, res)
    for c in A.screws:
        scr.disc(c, 0.03)
    d_scr = edt(scr.a, res, 5.0)
    g = gap(d_scr, allgold, res)
    row("gold to a screw's centre (head r 2.25)", "3.00", g)
    # the back: the light base's pads, J2, rev B's own back copper
    pads = Mask(A.w, A.h, res)
    for nm, (src, an, ca, size, ch) in BASE.items():
        for (x, y) in (an, ca):
            pads.rect(x - size[0] / 2, y - size[1] / 2, x + size[0] / 2, y + size[1] / 2)
    row("a window to a pad of the light base (all 24, back)", "0.35", gap(edt(pads.a, res, 4.0), M["window"].a, res))
    j2 = Mask(A.w, A.h, res)
    j2.rect(*J2)
    row("a window to J2's courtyard (back)", "0.30", gap(edt(j2.a, res, 4.0), M["window"].a, res))
    say("   rev B's own back copper under a window (the board as ordered; rev C moves these, routing plan 4.1):")
    hits = {}
    for p in B["pads"]:
        if "B.Cu" in p["layers"] or "*.Cu" in p["layers"]:
            if p["drill"] and p["kind"] == "np_thru_hole":
                continue
            m = Mask(A.w, A.h, res)
            m.rect(p["x"] - p["sx"] / 2, p["y"] - p["sy"] / 2, p["x"] + p["sx"] / 2, p["y"] + p["sy"] / 2)
            if (m.a & M["window"].a).any():
                hits["%s pad %s (%s)" % (p["ref"], p["num"], p["net"])] = 1
    for t in B["tracks"]:
        if t["layer"] == "B.Cu":
            m = Mask(A.w, A.h, res)
            m.seg(t["a"], t["b"], t["w"] / 2)
            if (m.a & M["window"].a).any():
                hits["track %s" % t["net"]] = hits.get("track %s" % t["net"], 0) + 1
    say("      " + ("; ".join(sorted(hits)) if hits else "none"))
    out["revB_hits"] = sorted(hits)
    # each window behind its own source: the part of the window outside the 2.0 mm body
    say("   each window against its own source's body (2.0 wide; a bar lights about 15.5 of its 18.5):")
    for L in A.lights:
        if L["place"] in BARS:
            a, b = BARS[L["place"]]
            body = Mask(A.w, A.h, res)
            body.butt(a, b, 1.0)
            wm = Mask(A.w, A.h, res)
            for pts, w, name in A.windows:
                if name == L["win"]:
                    wm.line(pts, w / 2)
            tot, outside = int(wm.a.sum()), int((wm.a & ~body.a).sum())
            xs = np.where(wm.a.any(axis=0))[0]
            ys = np.where(wm.a.any(axis=1))[0]
            say("      %-20s on %-3s window x %.2f to %.2f, y %.2f to %.2f; %.0f %% of it over the body; ends %.2f and %.2f inside the bar's ends"
                % (L["name"], L["place"], xs[0] / res, (xs[-1] + 1) / res, ys[0] / res, (ys[-1] + 1) / res, 100.0 * (tot - outside) / max(tot, 1),
                   xs[0] / res - min(a[0], b[0]), max(a[0], b[0]) - (xs[-1] + 1) / res))
    # cover
    ink = M["white"].a | allgold | M["legend"].a | M["window"].a
    free = ~edge_inset(A.w, A.h, A.corner, res, 0.0)
    part = {p["ref"]: p for p in B["parts"]}
    solid = Mask(A.w, A.h, res)
    for ref, r in A.part_r.items():
        solid.disc((part[ref]["x"], part[ref]["y"]), r)
    for c in A.screws:
        solid.disc(c, SCREW_HEAD)
    free &= ~solid.a
    d_ink = edt(ink | solid.a, res, 3.0)
    far = np.where(free, d_ink, 0)
    j, i = np.unravel_index(np.argmax(far), far.shape)
    out["cover"] = 100.0 * float((far <= 1.2).sum() - (~free).sum()) / float(free.sum())
    say("   free board within 1.2 mm of some ink: %.1f %%; the largest empty spot has radius %.2f at (%.1f, %.1f)"
        % (100.0 * float(((d_ink <= 1.2) & free).sum()) / float(free.sum()), far[j, i], (i + 0.5) / res, (j + 0.5) / res))
    out["empty"] = (float(far[j, i]), ((i + 0.5) / res, (j + 0.5) / res))
    out["cover"] = 100.0 * float(((d_ink <= 1.2) & free).sum()) / float(free.sum())
    # symmetry per zone
    say("   symmetry, per zone (1.000 = the same pixels after the mirror):")
    yc = A.ctl["FIELD"][1]

    def mirror_dev(xa, x0, x1, ya=None):
        """Largest distance (mm) from a window's mirrored end point to the nearest end point of a window of the same width."""
        ends = [(p, w) for pts, w, nm in A.windows for p in (pts[0], pts[-1]) if x0 <= p[0] <= x1]
        worst = 0.0
        for (p, w) in ends:
            q = (2 * xa - p[0], p[1]) if ya is None else (p[0], 2 * ya - p[1])
            worst = max(worst, min(math.hypot(q[0] - e[0], q[1] - e[1]) for e, w2 in ends if abs(w2 - w) < 1e-6))
        return worst
    for name, xa, hw in (("levers", A.axes["pair"], A.axes["pair"] - A.seams[1]), ("shuttle", A.axes["sec"], A.axes["sec"] - A.seams[2]),
                         ("keys", A.axes["keys"], A.seams[4] - A.axes["keys"])):
        span = math.ceil(hw) + 1.0
        Z = inks(A, ox=xa - span, w=2 * span)                    # a raster with the zone's axis exactly on a pixel edge
        i0, n = int(round((span - hw + 1.0) * res)), int(round(2 * span * res))
        both = (Z["white"].a | Z["gold"].a)[:, i0:n - i0]
        wv = (Z["weave_w"].a | Z["weave_g"].a)[:, i0:n - i0]
        v_all = float((both & both[:, ::-1]).sum()) / float((both | both[:, ::-1]).sum())
        v_wv = float((wv & wv[:, ::-1]).sum()) / float((wv | wv[:, ::-1]).sum())
        dev = mirror_dev(xa, xa - hw, xa + hw)
        say("      %-8s axis x %.3f, half width %.2f: the lights' ends are off their mirror image by %.3f mm at most; pixels kept by the mirror: "
            "the weave %.3f, all my ink (the thread's dots, the card's data, the shuttle) %.3f" % (name, xa, hw, dev, v_wv, v_all))
        out["sym_" + name] = (dev, v_wv, v_all)
    say("      levers, up and down about y %.1f: the lights' ends off by %.3f mm at most" % (yc, mirror_dev(0, A.seams[1], A.seams[2], ya=yc)))
    say("      the weave's drafts: cells that differ from their mirror image, levers %d, keys %d (0 = exact)" % (A.draft_bad["levers"], A.draft_bad["keys"]))
    say("      MODE zone: plainly directional (a one-way 2/2 twill); the thread itself is directional everywhere")
    say("   the weave: %d white dashes, %d gold dashes, %d thread dots; white %.2f, gold %.2f wide; warp pitch %.3f (levers), %.3f (keys), 1.000 elsewhere; weft pitch 1.000"
        % (A.n_white, A.n_gold, A.n_dots, W_WHITE, W_GOLD, A.zones[2][2], A.zones[4][2]))
    say("   the thread leaves the fascia's top edge at x %.3f" % A.exit_x)
    say("   rev B's front gold not kept: %d items 0.6 wide (the SUB box and its runs; the base's rings and link take their place)" % A.dropped_gold)
    c = A.card
    say("   the card: MODE codes %s (firmware rounding (a + %d) / %d + 1), lever codes %s" % (c["mode"], c["rounding"][0], c["rounding"][1], c["lever"]))
    for y, code, bits in c["rows"]:
        say("      row y %.1f  code %4d  %s" % (y, code, "".join("O" if b else "." for b in bits)))
    say("   lights on the fascia:")
    for L in A.lights:
        say("      %-20s %-10s place %-3s %s  drawn length %.1f  dyed %s" % (L["name"], L["part"], L["place"], L["ch"], length(L["pts"]), L["dye"]))
    return out, M


# ------------------------------------------------------------------------------------ drawing a board (SVG, mm units)
GOLD_INK, WHITE_INK, MASK_INK, FR4 = "#d8a23a", "#ecebe4", "#0c0c0f", "#6e5a2c"
DEFS = """<defs>
<filter id="g1" x="-30%" y="-30%" width="160%" height="160%" filterUnits="userSpaceOnUse" color-interpolation-filters="sRGB"><feGaussianBlur stdDeviation="0.45"/></filter>
<filter id="g2" x="-30%" y="-30%" width="160%" height="160%" filterUnits="userSpaceOnUse" color-interpolation-filters="sRGB"><feGaussianBlur stdDeviation="1.5"/></filter>
<filter id="g3" x="-30%" y="-30%" width="160%" height="160%" filterUnits="userSpaceOnUse" color-interpolation-filters="sRGB"><feGaussianBlur stdDeviation="3.2"/></filter>
<radialGradient id="knob" cx="40%" cy="35%" r="75%"><stop offset="0" stop-color="#3a3a40"/><stop offset="1" stop-color="#101013"/></radialGradient>
<radialGradient id="steel" cx="40%" cy="35%" r="75%"><stop offset="0" stop-color="#b9bcc4"/><stop offset="1" stop-color="#55585f"/></radialGradient>
</defs>"""


def flt(fid, w, h):
    return ' filter="url(#%s)"' % fid


def svg_inks(A, dim=1.0):
    """White, gold and the legends of a board."""
    s = []
    op = "" if dim == 1.0 else ' opacity="%.2f"' % dim
    s.append('<g%s fill="none" stroke="%s" stroke-linecap="butt">' % (op, GOLD_INK))
    s.append('<path d="%s" stroke-width="%.3f"/>' % (d_segs(A.gbutt), W_GOLD))
    by = {}
    for pts, w in A.gold + A.base_gold + A.legend_g:
        by.setdefault(w, []).append(pts)
    for w, lines in by.items():
        s.append('<path d="%s" stroke-width="%.3f" stroke-linecap="round" stroke-linejoin="round"/>' % ("".join(d_of(p) for p in lines), w))
    s.append("</g>")
    s.append('<g%s fill="%s">' % (op, GOLD_INK))
    s.append("".join('<circle cx="%.3f" cy="%.3f" r="%.3f"/>' % d for d in A.gdots + A.base_gdots))
    s.append("".join('<path d="%s"/>' % d_of(p, True) for p in A.gpoly))
    s.append("</g>")
    s.append('<g%s fill="none" stroke="%s" stroke-linecap="butt">' % (op, WHITE_INK))
    s.append('<path d="%s" stroke-width="%.3f"/>' % (d_segs(A.wbutt), W_WHITE))
    by = {}
    for pts, w in A.white + A.legend_w:
        by.setdefault(w, []).append(pts)
    for w, lines in by.items():
        s.append('<path d="%s" stroke-width="%.3f" stroke-linecap="round" stroke-linejoin="round"/>' % ("".join(d_of(p) for p in lines), w))
    s.append("</g>")
    s.append('<g%s fill="%s">%s</g>' % (op, WHITE_INK, "".join('<circle cx="%.3f" cy="%.3f" r="%.3f"/>' % d for d in A.wdots)))
    return "".join(s)


def svg_fascia(A, dye=False, lit=True):
    s = ['<rect x="0" y="0" width="%.2f" height="%.2f" rx="%.2f" fill="%s"/>' % (A.w, A.h, A.corner, MASK_INK)]
    for pts, w, name in A.windows:                                       # bare FR4
        s.append('<path d="%s" fill="none" stroke="%s" stroke-width="%.3f" stroke-linecap="round"/>' % (d_of(pts), FR4, w))
    s.append(svg_inks(A))
    if lit:
        col = {}
        for L in A.lights:
            col[L["name"]] = L["dye"] if dye else WARM
        tint = {"S": col["S, the bobbin"], "P": col["P, the noon stitch"]}
        for layer in (3, 2, 1, 0):
            for pts, w, name in A.windows:
                glow, core = TINT[tint.get(name, col.get(name, WARM))]
                d = d_of(pts)
                if layer == 3:
                    s.append('<path d="%s" fill="none" stroke="%s" stroke-width="%.2f" stroke-linecap="round" opacity="0.30"%s/>' % (d, glow, w + 2.4, flt("g3", 0, 0)))
                elif layer == 2:
                    s.append('<path d="%s" fill="none" stroke="%s" stroke-width="%.2f" stroke-linecap="round" opacity="0.55"%s/>' % (d, glow, w + 0.9, flt("g2", 0, 0)))
                elif layer == 1:
                    s.append('<path d="%s" fill="none" stroke="%s" stroke-width="%.2f" stroke-linecap="round"/>' % (d, glow, w))
                else:
                    s.append('<path d="%s" fill="none" stroke="%s" stroke-width="%.2f" stroke-linecap="round" opacity="0.92"%s/>' % (d, core, w * 0.62, flt("g1", 0, 0)))
    # what stands on the face (sizes assumed): knob, two toggles, two keys, four screws
    part = {p["ref"]: p for p in A.B["parts"]}
    x, y = part["SW1"]["x"], part["SW1"]["y"]
    s.append('<circle cx="%.2f" cy="%.2f" r="9.6" fill="#050506"/><circle cx="%.2f" cy="%.2f" r="9.0" fill="url(#knob)" stroke="#2c2c31" stroke-width="0.2"/>' % (x, y, x, y))
    a, b = P((x, y), 3.5, -75), P((x, y), 8.4, -75)
    s.append('<path d="%s" stroke="#e9e7df" stroke-width="0.7" stroke-linecap="round"/>' % d_of([a, b]))
    for ref in ("SW2", "SW3"):
        x, y = part[ref]["x"], part[ref]["y"]
        hexa = [P((x, y), 5.6, 30 + 60 * k) for k in range(6)]
        s.append('<circle cx="%.2f" cy="%.2f" r="6.0" fill="#050506"/><path d="%s" fill="url(#steel)" opacity="0.85"/><circle cx="%.2f" cy="%.2f" r="3.0" fill="#1a1a1e"/>' % (x, y, d_of(hexa, True), x, y))
        s.append('<path d="M%.2f %.2f L%.2f %.2f" stroke="url(#steel)" stroke-width="2.6" stroke-linecap="round"/>' % (x, y, x, y - 3.4))
    for ref in ("SW4", "SW5"):
        x, y = part[ref]["x"], part[ref]["y"]
        s.append('<circle cx="%.2f" cy="%.2f" r="6.8" fill="#050506"/><circle cx="%.2f" cy="%.2f" r="6.2" fill="url(#steel)" opacity="0.8"/><circle cx="%.2f" cy="%.2f" r="4.4" fill="url(#knob)"/>' % (x, y, x, y, x, y))
    for (x, y) in A.screws:
        s.append('<circle cx="%.2f" cy="%.2f" r="2.25" fill="url(#steel)"/><path d="M%.2f %.2f L%.2f %.2f" stroke="#2a2a2e" stroke-width="0.45"/>' % (x, y, x - 1.3, y - 0.8, x + 1.3, y + 0.8))
    return "".join(s)


# ------------------------------------------------------------------------------------ sheets
CSS = """html,body{margin:0;background:#16161a;color:#e6e6e2;font-family:'DejaVu Sans',sans-serif}
.page{padding:26px 34px 30px 34px;width:%dpx;box-sizing:border-box}
h1{font-size:25px;margin:0 0 6px 0;font-weight:700}
p.sub{font-size:15px;color:#a9a9a4;margin:0 0 14px 0;line-height:1.35}
p.cap{font-size:13.5px;color:#8f8f8a;margin:14px 0 5px 2px;font-weight:700}
.notes{margin-top:14px;font-size:15px;line-height:1.42;color:#d6d6d0}
.notes p{margin:0 0 7px 0}.notes b{color:#fff}
svg{display:block}"""


def board_svg(inner, w, h, px=PX, extra=""):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %.3f %.3f">%s<g>%s</g>%s</svg>'
            % (round(w * px), round(h * px), w, h, DEFS, inner, extra))


def sheet(name, title, sub, blocks, notes, width):
    html = ['<!doctype html><html><head><meta charset="utf-8"><style>%s</style></head><body><div class="page">' % (CSS % width)]
    html.append("<h1>%s</h1><p class=\"sub\">%s</p>" % (esc(title), esc(sub)))
    for cap, svg in blocks:
        if cap:
            html.append('<p class="cap">%s</p>' % esc(cap))
        html.append(svg)
    if notes:
        html.append('<div class="notes">%s</div>' % "".join("<p>%s</p>" % n for n in notes))
    html.append("</div></body></html>")
    tmp = os.path.join(TMP, name + ".html")
    open(tmp, "w", encoding="utf-8").write("".join(html))
    ok = render(tmp, os.path.join(OUT, name + ".png"), width)
    say("   wrote %s.png" % name if ok else "   NOT rendered: %s" % name)


def label(x, y, s, size=1.5, fill="#e6e6e2", anchor="start", bold=False):
    return ('<text x="%.2f" y="%.2f" font-family="DejaVu Sans" font-size="%.2f" fill="%s" text-anchor="%s"%s>%s</text>'
            % (x, y, size, fill, anchor, ' font-weight="700"' if bold else "", esc(s)))


def sheet_fascia(A, F):
    notes = [
        "<b>The idea.</b> The board is the cloth and the lights are the thread. The thread starts as the lit turn on the spool (MODE), runs "
        "under the cloth as white dots, makes one turn round each hoop (FIELD, SUB: four straight stitches), passes through the shuttle, makes one "
        "turn round the two keys and leaves the top edge at x %.1f, between the two P stitches. The display takes it up at the same x." % A.exit_x,
        "<b>Lights (the common base's sources, no new place):</b> MODE turn (38 flex, CH1); FIELD up and down, SUB up and down (18.5 rigid, straight "
        "stitches on the bars' own chords, CH2 and CH3); key turns (38 flex, CH4); <b>S</b>, the bobbin: 13 lit turns = a 60 s rule, every 5 s, the "
        "15 s marks tall (S1 bar, CH5); <b>P</b>, the noon stitch: two stitches, before and after, parted by the thread that goes up between the AM and "
        "PM tubes (P bar, CH6). All warm here.",
        "<b>Ground:</b> gold warp %.2f and white weft %.2f, true over and under, weft pitch 1.0. Zones: plain selvedges; MODE a one-way 2/2 twill; "
        "levers and keys a diamond twill centred on each control; the shuttle's zone plain. Herringbone seams between zones. %d white and %d gold dashes."
        % (W_GOLD, W_WHITE, A.n_white, A.n_gold),
        "<b>The card band</b> under the shuttle is true data from the firmware: six rows = the MODE positions' ADC codes on A6 (%s), four rows = the "
        "lever states on A7 (%s). Ten columns = bits 512 to 1. A gold dot is a 1, a white prick is a 0." % (", ".join(str(v) for v in A.card["mode"]), ", ".join(str(v) for v in A.card["lever"])),
        "<b>Measured (0.05 mm raster):</b> weave to a legend %.2f / %.2f (white / gold); ink to a window %.2f / %.2f; white to gold %.2f; gold to the edge %.2f; "
        "windows to the base's pads %.2f; within 1.2 mm of ink: %.1f %% of the free board. Knob, toggles, keys and screw heads are drawn at assumed sizes."
        % (F["the weave's white to a legend (names, 1-6, - and +)"][0], F["the weave's gold to a legend"][0], F["white to a window"][0], F["gold (mine and the base's) to a window"][0],
           F["white to gold"][0], F["gold to the board edge"][0], F["a window to a pad of the light base (all 24, back)"][0], F["cover"]),
        "<b>Buildable?</b> Needs the routing plan's rev C back (the base's pads, J2, the pour cut per window) and the fab's yes on bare-FR4 windows. "
        "Nothing new in copper beyond the base; the S bar and the P bar are the base's own places.",
    ]
    m = 3.0
    svg = board_svg('<g transform="translate(%.2f %.2f)">%s</g>' % (m, m, svg_fascia(A)), A.w + 2 * m, A.h + 2 * m)
    sheet("yarn-fascia", "YARN, the fascia: the cloth, the spool, two hoops, a shuttle, one thread",
          "fascia R rev B (191.4 x 40), outline, holes, parts and names from the board file; the light base from the routing plan; 11.5 px per mm; lights on, all warm",
          [("", svg)], notes, int(round((A.w + 2 * m) * PX)) + 68)


def sheet_back(A, F):
    """The fascia's back, seen through the board from the front (x as on the face)."""
    B = A.B
    s = ['<rect x="0" y="0" width="%.2f" height="%.2f" rx="1.5" fill="#101418" stroke="#5a6470" stroke-width="0.15"/>' % (A.w, A.h)]
    part = {p["ref"]: p for p in B["parts"]}
    for ref, r in (("SW1", 12.5),):
        s.append('<circle cx="%.2f" cy="%.2f" r="%.2f" fill="none" stroke="#3d4650" stroke-width="0.2" stroke-dasharray="0.8 0.5"/>' % (part[ref]["x"], part[ref]["y"], r))
    for ref in ("SW2", "SW3"):
        x, y = part[ref]["x"], part[ref]["y"]
        s.append('<rect x="%.2f" y="%.2f" width="11.92" height="11.92" fill="none" stroke="#3d4650" stroke-width="0.2" stroke-dasharray="0.8 0.5"/>' % (x - 5.96, y - 5.96))
    for (bx0, bx1) in ((141.95, 158.85), (162.95, 179.85)):
        s.append('<rect x="%.2f" y="9.1" width="%.2f" height="13.8" fill="none" stroke="#3d4650" stroke-width="0.2" stroke-dasharray="0.8 0.5"/>' % (bx0, bx1 - bx0))
    for p in B["pads"]:
        if p["drill"]:
            s.append('<circle cx="%.2f" cy="%.2f" r="%.2f" fill="#000" stroke="#5a6470" stroke-width="0.12"/>' % (p["x"], p["y"], p["drill"][0] / 2))
    for t in B["tracks"]:                                                # rev B as ordered
        if t["layer"] == "B.Cu":
            s.append('<path d="%s" stroke="#7a4a2a" stroke-width="%.2f" stroke-linecap="round" opacity="0.8"/>' % (d_of([t["a"], t["b"]]), t["w"]))
    for p in B["pads"]:
        if not p["drill"] and "B.Cu" in p["layers"]:
            s.append('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="#a8683a" opacity="0.85"/>' % (p["x"] - p["sx"] / 2, p["y"] - p["sy"] / 2, p["sx"], p["sy"]))
    s.append('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="#1d2b3a" stroke="#6fb1ff" stroke-width="0.2"/>' % (J2[0], J2[1], J2[2] - J2[0], J2[3] - J2[1]))
    s.append(label((J2[0] + J2[2]) / 2, (J2[1] + J2[3]) / 2 + 0.5, "J2, 7-way", 1.5, "#9fd0ff", "middle"))
    used = {L["place"] for L in A.lights}
    for nm, (src, an, ca, size, ch) in BASE.items():
        on = nm in used
        col = "#ffb347" if on else "#59616b"
        if nm in BARS:
            a, b = BARS[nm]
            x0_, y0_ = min(a[0], b[0]) - (1.0 if a[0] == b[0] else 0), min(a[1], b[1]) - (1.0 if a[1] == b[1] else 0)
            w_, h_ = abs(b[0] - a[0]) + (2.0 if a[0] == b[0] else 0), abs(b[1] - a[1]) + (2.0 if a[1] == b[1] else 0)
            s.append('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" rx="1" fill="%s" opacity="%s" stroke="%s" stroke-width="0.15"%s/>'
                     % (x0_, y0_, w_, h_, "#5b3b12" if on else "none", "0.9", col, "" if on else ' stroke-dasharray="0.7 0.5"'))
        for (x, y), sign in ((an, "+"), (ca, "")):
            s.append('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="%s"/>' % (x - size[0] / 2, y - size[1] / 2, size[0], size[1], col))
            if sign:
                s.append(label(x, y + 0.45, "+", 1.3, "#101418", "middle", True))
    for nm, c, a0, a1 in (("M", A.ctl["DIAL"], 230, 130), ("KM", A.ctl["KM"], 255, 105), ("KP", A.ctl["KP"], 75, -75)):
        r = 14.2 if nm == "M" else 10.0
        s.append('<path d="%s" fill="none" stroke="#5b3b12" stroke-width="2.0" stroke-linecap="butt"/>' % d_of(arc(c, r, a0, a1)))
        s.append('<path d="%s" fill="none" stroke="#ffb347" stroke-width="0.15"/>' % d_of(arc(c, r + 1.0, a0, a1) + arc(c, r - 1.0, a1, a0), True))
    for pts, w, name in A.windows:                                       # the windows and their pour cuts (outline + 0.1)
        s.append('<path d="%s" fill="none" stroke="#fff3c4" stroke-width="%.2f" stroke-linecap="round" opacity="0.95"/>' % (d_of(pts), w))
    lab = [("M", 2.0, 14.0, "start"), ("FU", 59.0, 3.9, "start"), ("FD", 59.0, 29.6, "start"), ("SU", 82.5, 3.9, "start"), ("SD", 82.5, 29.6, "start"),
           ("S1", 113.0, 5.3, "start"), ("P", 157.0, 3.9, "start"), ("KM", 130.6, 31.0, "start"), ("KP", 183.2, 28.0, "start"),
           ("T (not fitted)", 100.4, 3.3, "start"), ("SCR (not fitted)", 112.3, 38.3, "start"), ("BP (not fitted)", 126.0, 3.3, "start")]
    for t, x, y, an in lab:
        k = t.split(" ")[0]
        s.append(label(x, y, "%s %s" % (t, BASE[k][4]) if "not" not in t else t, 1.45, "#ffd28a" if "not" not in t else "#8a929c", an))
    for ref in ("J1", "R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"):
        p = part[ref]
        s.append(label(p["x"], p["y"] + {"J1": 5.6, "R6": -2.0}.get(ref, 3.0), ref, 1.25, "#c98a5c", "middle"))
    m = 3.0
    svg = board_svg('<g transform="translate(%.2f %.2f)">%s</g>' % (m, m, "".join(s)), A.w + 2 * m, A.h + 2 * m)
    notes = [
        "<b>Seen through the board from the front</b> (x as on the face). Pale: my windows. Amber: the common light base's sources that this face fits, "
        "their bodies 2.0 wide and their pads (+ = anode, routed; the other pad sits in the ground pour). Grey, dashed: the base's places this face leaves empty "
        "(T, SCR, BP). Blue: J2 behind the shuttle. Brown: rev B's back copper and parts as ordered. Dashed outlines: the control bodies.",
        "<b>Against the base:</b> no pad, bar or connector moves. The four lever windows are straight, 11.0 x 1.2, on the bars' own chords (y 6.2 and 25.8, "
        "inside the 2.0 bodies at y 5.9 and 26.1): a straight bar behind a straight stitch, so the base's curved-window fault (0.5 mm missed) is gone. "
        "S: 13 slits over the S1 bar. P: two stitches over the P bar. The pour is cut per window, outline + 0.1.",
        "<b>Measured:</b> windows to the base's pads %.2f (rule 0.35), to J2 %.2f. Rev B's own back copper under my windows: %s. "
        "Rev C moves those (routing plan 4.1, items 1 to 5); on rev B as ordered the face cannot be lit."
        % (F["a window to a pad of the light base (all 24, back)"][0], F["a window to J2's courtyard (back)"][0], "; ".join(F["revB_hits"]) or "none"),
    ]
    sheet("lights-back", "YARN, the fascia's back: pads, bars, windows",
          "fascia R rev B with the routing plan's light base (section 2.3) drawn on it; nothing is routed", [("", svg)], notes,
          int(round((A.w + 2 * m) * PX)) + 68)


# ------------------------------------------------------------------------------------ the display
# disp-3-4's slots and holes (PCB/art/TS06-DISP-final-3.md section 5 and 6; its grill, finding 1), typed in:
D_SLOT = {"H": ((39.48, 30.40), (39.48, 5.27)), "M": ((61.10, 30.40), (61.10, 5.27)), "P": ((151.86, 30.40), (138.40, 5.27)),
          "F": ((181.81, 34.0), (2.80, 34.0)), "S": ((139.57, 18.92), (98.20, 18.92)), "S2": ((100.60, 22.69), (137.17, 22.69))}   # driven, return
D_HOLE = {"CF": ((58.285, 31.60), (42.785, 31.60)), "N": ((101.385, 6.60), (136.385, 6.60))}      # driven, return (the needle: the plan's swap)
Q_X, Q_Y = (46.05, 55.02), (6.0, 29.0)                   # the colon bars, in the shim
GLASS12, GLASS17, LAMP_D = (19.47, 28.86, 8.0), (14.0, 20.0, 3.0), 6.97   # tools/disp_art.py; the corner radii are assumed
CASE_WIN, VALANCE_Y = (3.0, 2.6, 182.0, 39.0), 4.0       # tools/disp_art.py: the case's window on the board, the brow over the seconds
HL9_DOWN = 3.0                                            # V3b: the "m" lamp 3.0 lower
HOLE_KEEP = 3.8                                           # standoff holes (tools/disp_art.py)
HV_GOLD = 1.0                                             # the brief: new copper 1.0 or more from the 185 V nets


def pad_gap(B, x, y, r):
    """Nearest copper of another net to a round pad of radius r at (x, y): (gap, name), and the nearest 185 V copper.
    The board as in the file, less what the plan removes: HL1 to HL8, every BL_A track, M_A; HL9 3.0 lower."""
    best, besthv = (9e9, ""), (9e9, "")
    for pd in B["pads"]:
        if (pd["ref"].startswith("HL") and pd["ref"] != "HL9") or pd["net"] == "BL_K":
            continue
        px, py = pd["x"], pd["y"] + (HL9_DOWN if pd["ref"] == "HL9" else 0.0)
        if pd["shape"] == "circle":
            d = math.hypot(x - px, y - py) - pd["sx"] / 2 - r
        else:
            d = math.hypot(max(abs(x - px) - pd["sx"] / 2, 0), max(abs(y - py) - pd["sy"] / 2, 0)) - r
        nm = "%s.%s %s" % (pd["ref"], pd["num"], pd["net"] or "no net")
        if d < best[0]:
            best = (d, nm)
        if yb.hv(pd["net"]) and d < besthv[0]:
            besthv = (d, nm)
    for t in B["tracks"]:
        if t["net"].startswith("BL_A") or t["net"] in ("BL_K", "M_A"):
            continue
        (ax, ay), (bx, by) = t["a"], t["b"]
        dx, dy = bx - ax, by - ay
        L = dx * dx + dy * dy
        u = 0 if L == 0 else max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / L))
        d = math.hypot(x - ax - u * dx, y - ay - u * dy) - t["w"] / 2 - r
        nm = "track %s %s" % (t["net"], t["layer"])
        if d < best[0]:
            best = (d, nm)
        if yb.hv(t["net"]) and d < besthv[0]:
            besthv = (d, nm)
    return best, besthv


def display():
    B = yb.load(yb.DISP)
    x0, y0, x1, y1 = B["box"]
    A = Art(B, x1 - x0, y1 - y0, 0.0, edge_white=0.5, edge_gold=1.0)
    part = {p["ref"]: p for p in B["parts"]}
    A.t12 = [(part[r]["x"], part[r]["y"]) for r in ("V1", "V2", "V3", "V4", "V9", "V10")]
    A.t17 = [(part[r]["x"], part[r]["y"]) for r in ("V5", "V6")]
    A.lamps = [(part[r]["x"], part[r]["y"]) for r in ("V7", "V8")]
    A.screws = [(p["x"], p["y"]) for p in B["parts"] if p["ref"].startswith("H") and not p["ref"].startswith("HL")]
    A.bead = (part["HL9"]["x"], part["HL9"]["y"] + HL9_DOWN)
    hx, mx = (A.t12[0][0] + A.t12[1][0]) / 2, (A.t12[2][0] + A.t12[3][0]) / 2          # 24.89, 75.68
    sx, px_ = (A.t17[0][0] + A.t17[1][0]) / 2, (A.t12[4][0] + A.t12[5][0]) / 2          # 118.885, 160.9
    cx, ty = A.lamps[0][0], A.t12[0][1]                                                  # 50.535, 17.834
    A.axes = dict(hours=hx, minutes=mx, seconds=sx, ampm=px_, colon=cx, tubes=(hx + mx) / 2, frame=(2.80 + 181.81) / 2)
    row_y = 36.4

    # ---- the lights: disp-3-4's known lines, re-read as stitches; three new bars under the patches
    def light(name, part_, pts, dye, ch, held, place, new=False):
        A.lights.append(dict(name=name, part=part_, pts=pts, w=2.0, dye=dye, ch=ch, held=held, place=place, new=new))
    F_ = [D_SLOT["F"][0], D_SLOT["F"][1]]
    H_ = rounded([D_SLOT["H"][1], (4.97, 5.27), (4.97, 30.40), D_SLOT["H"][0]], 5.0)
    M_ = rounded([D_SLOT["M"][0], (95.61, 30.40), (95.61, 5.27), D_SLOT["M"][1]], 5.0)
    P_ = rounded([D_SLOT["P"][0], (179.64, 30.40), (179.64, 5.27), D_SLOT["P"][1]], 5.0)
    S_ = rounded([D_SLOT["S"][1], (98.20, 9.0), (139.57, 9.0), D_SLOT["S"][0]], 8.4)
    S2_ = rounded([D_SLOT["S2"][1], (137.17, 11.4), (100.60, 11.4), D_SLOT["S2"][0]], 6.0)
    Q1_ = [(Q_X[0], Q_Y[1]), (Q_X[0], Q_Y[0])]
    Q2_ = [(Q_X[1], Q_Y[0]), (Q_X[1], Q_Y[1])]
    CF_ = [(D_HOLE["CF"][1][0] - 0.5, 31.6), (D_HOLE["CF"][0][0] + 0.5, 31.6)]
    N_ = [(D_HOLE["N"][1][0] + 0.5, 6.6), (D_HOLE["N"][0][0] - 0.5, 6.6)]                # from the eye (right) to the point (left)
    A.new_holes = {}
    bars = {}
    for nm, ax in (("Bh", hx), ("Bm", mx), ("Bs", sx)):                                   # 38 rigid: holes 35.0 apart (assumed, as the lintel's)
        A.new_holes[nm] = ((ax - 17.5, row_y), (ax + 17.5, row_y))
        bars[nm] = [(ax - 18.0, row_y), (ax + 18.0, row_y)]
    light("F, the hem", "185 flex", F_, WARM, "ch 3, BL_A8", "slots", "y 34.0, x 2.80 to 181.81")
    light("Bh, row stitch", "38 rigid", bars["Bh"], GREEN, "ch 6, BL_A2", "2 holes", "y 36.4, holes x %.2f and %.2f" % (hx - 17.5, hx + 17.5), True)
    light("Q1, colon", "26 rigid", Q1_, PINK, "ch 5, harness", "the shim", "x 46.05, y 6.0 to 29.0")
    light("H, hours patch", "95 flex", H_, WARM, "ch 0, BL_A1", "slots, shim", "slots (39.48, 5.27) and (39.48, 30.40)")
    light("CF, colon foot", "18.5 rigid", CF_, PINK, "ch 10, BL_A12", "2 holes", "y 31.6, holes x 42.785 and 58.285")
    light("M, minutes patch", "95 flex", M_, WARM, "ch 1, BL_A3", "slots, shim", "slots (61.10, 30.40) and (61.10, 5.27)")
    light("Q2, colon", "26 rigid", Q2_, PINK, "ch 5, harness", "the shim", "x 55.02, y 6.0 to 29.0")
    light("Bm, row stitch", "38 rigid", bars["Bm"], GREEN, "ch 8, BL_A4", "2 holes", "y 36.4, holes x %.2f and %.2f" % (mx - 17.5, mx + 17.5), True)
    light("S, seconds patch", "60 flex", S_, WARM, "ch 4, BL_A6", "slots", "slots (98.20, 18.92) and (139.57, 18.92), crown y 9.0")
    light("S2, back stitch", "60 flex", S2_, BLUE, "ch 11, BL_A5", "slots", "slots (137.17, 22.69) and (100.60, 22.69), crown y 11.4")
    light("Bs, row stitch", "38 rigid", bars["Bs"], GREEN, "ch 7, BL_A9", "2 holes", "y 36.4, holes x %.3f and %.3f" % (sx - 17.5, sx + 17.5), True)
    light("P, AM/PM patch", "95 flex", P_, WARM, "ch 2, BL_A7", "slots, shim", "slots (151.86, 30.40) and (138.40, 5.27)")
    light("N, the needle", "38 rigid", N_, WHITE, "ch 12, BL_A10", "2 holes", "y 6.6, holes x 101.385 (driven) and 136.385")

    # ---- keep-outs: pads, holes, 185 V copper, lit bodies, the lamps, the bead
    A.padlist = []                                                   # (x, y, sx, sy, shape, drill, net) as built
    for pd in B["pads"]:
        if pd["ref"].startswith("HL") and pd["ref"] != "HL9":
            continue
        y = pd["y"] + (HL9_DOWN if pd["ref"] == "HL9" else 0.0)
        A.padlist.append(dict(x=pd["x"], y=y, sx=pd["sx"], sy=pd["sy"], shape=pd["shape"], drill=pd["drill"], net=pd["net"], kind=pd["kind"]))
    for nm, (a, b) in D_SLOT.items():                                # slot pads 1.8 x 3.3, long axis across the filament
        for (x, y) in (a, b):
            level = nm in ("S", "S2")                                # the legs are plumb there, so the slot lies level
            A.padlist.append(dict(x=x, y=y, sx=3.3 if level else 1.8, sy=1.8 if level else 3.3, shape="slot",
                                  drill=(2.5, 1.0) if level else (1.0, 2.5), net=nm, kind="new"))
    for nm, (a, b) in list(D_HOLE.items()) + list(A.new_holes.items()):
        for (x, y) in (a, b):
            A.padlist.append(dict(x=x, y=y, sx=1.8, sy=1.8, shape="circle", drill=(1.0, 1.0), net=nm, kind="new"))
    for pd in A.padlist:
        hvp = yb.hv(pd["net"])
        r = max(pd["sx"], pd["sy"]) / 2 if pd["shape"] == "circle" else math.hypot(pd["sx"], pd["sy"]) / 2
        c = (pd["x"], pd["y"])
        if pd["kind"] == "np_thru_hole" and 3.1 <= pd["sx"] < 4:     # the standoff holes
            for m in (A.kw, A.kg, A.kt):
                m.disc(c, HOLE_KEEP)
            continue
        A.kw.disc(c, r + 0.32 + W_WHITE / 2)
        A.kt.disc(c, r + 0.30 + DOT_R)
        A.kg.disc(c, r + (HV_GOLD + 0.07 if hvp else C_GOLD) + W_GOLD / 2)
    for t in B["tracks"]:
        if t["layer"] == "F.Cu":
            A.kg.seg(t["a"], t["b"], t["w"] / 2 + (HV_GOLD + 0.07 if yb.hv(t["net"]) else C_GOLD) + W_GOLD / 2)
    for l in A.lights:
        A.kw.line(l["pts"], 1.0 + 0.32 + W_WHITE / 2)
        A.kg.line(l["pts"], 1.0 + 0.40 + W_GOLD / 2)
        A.kt.line(l["pts"], 1.0 + 0.32 + DOT_R)
    for c in A.lamps:
        for m in (A.kw, A.kg, A.kt):
            m.disc(c, LAMP_D / 2 + 0.3)
    for m in (A.kw, A.kg, A.kt):
        m.disc(A.bead, 1.9 + 0.35)
    for t in B["texts"]:
        if t["layer"] == "F.SilkS":
            hw_ = 0.45 * t["h"] * len(t["s"]) + 0.5
            for m in (A.kw, A.kg, A.kt):
                m.rect(t["x"] - hw_, t["y"] - t["h"] * 0.6 - 0.5, t["x"] + hw_, t["y"] + t["h"] * 0.6 + 0.5)

    # ---- the needle's point: gold, clear of the driven cap
    A.needle_tip = [(99.5, 5.75), (99.5, 7.45), (97.4, 6.6)]
    A.kg.a_backup = None
    probe = Mask(A.w, A.h, RES)                                      # the point against copper only (not against its own bar)
    for pd in A.padlist:
        if pd["net"] != "N" and pd["kind"] != "np_thru_hole":
            probe.disc((pd["x"], pd["y"]), math.hypot(pd["sx"], pd["sy"]) / 2 + (HV_GOLD if yb.hv(pd["net"]) else C_GOLD))
    for t in B["tracks"]:
        if t["layer"] == "F.Cu":
            probe.seg(t["a"], t["b"], t["w"] / 2 + (HV_GOLD if yb.hv(t["net"]) else C_GOLD))
    for l in A.lights:
        if not l["name"].startswith("N"):
            probe.line(l["pts"], 1.3)
    tipm = Mask(A.w, A.h, RES)
    tipm.poly(A.needle_tip)
    A.needle_tip_drawn = not (tipm.a & probe.a).any()
    if A.needle_tip_drawn:
        A.gpoly.append(A.needle_tip)
        A.keep(A.needle_tip + [A.needle_tip[0]], 0.0, C_WHITE_GOLD, C_GOLD, C_WHITE_GOLD)

    # ---- the thread, in order
    T = A.thread
    A.entry_x = A.bead[0]
    T.append(("under", [(A.bead[0], A.h), (A.bead[0], A.bead[1])]))
    T.append(("under", rounded([(A.bead[0] + 1.4, A.bead[1] - 1.4), (A.bead[0] + 3.2, row_y), (180.6, row_y), (181.81, 35.0)], 1.0)))
    T.append(("lit", F_))
    T.append(("under", rounded([(2.80, 34.0), (2.80, row_y), bars["Bh"][0]], 1.0)))
    T.append(("lit", bars["Bh"]))
    T.append(("under", rounded([bars["Bh"][1], (Q_X[0], row_y), Q1_[0]], 1.2)))
    T.append(("lit", Q1_))
    T.append(("under", [Q1_[1], D_SLOT["H"][1]]))
    T.append(("lit", H_))
    T.append(("under", [D_SLOT["H"][0], CF_[0]]))
    T.append(("lit", CF_))
    T.append(("under", [CF_[1], D_SLOT["M"][0]]))
    T.append(("lit", M_))
    T.append(("under", [D_SLOT["M"][1], Q2_[0]]))
    T.append(("lit", Q2_))
    T.append(("under", rounded([Q2_[1], (Q_X[1], row_y), bars["Bm"][0]], 1.2)))
    T.append(("lit", bars["Bm"]))
    T.append(("under", rounded([bars["Bm"][1], (98.20, row_y), D_SLOT["S"][1]], 1.6)))
    T.append(("lit", S_))
    T.append(("under", rounded([D_SLOT["S"][0], (139.57, 25.4), (137.17, 25.4), D_SLOT["S2"][1]], 1.15)))
    T.append(("lit", S2_))
    T.append(("under", rounded([D_SLOT["S2"][0], (100.60, row_y), bars["Bs"][0]], 0.6)))
    T.append(("lit", bars["Bs"]))
    T.append(("under", rounded([bars["Bs"][1], (151.86, row_y), D_SLOT["P"][0]], 1.6)))
    T.append(("lit", P_))
    T.append(("under", [D_SLOT["P"][1], N_[0]]))
    T.append(("lit", N_))
    A.n_dots = sum(A.dots(pts, pitch=1.0, r=0.22) for kind, pts in T if kind == "under")

    # ---- the ground: each tube group is a patch with its own diamond twill; plain cloth round them
    half = (A.t12[1][0] - A.t12[0][0]) / 2 + GLASS12[0] / 2 + 0.25           # a patch reaches 0.25 past its glass
    A.seams = [hx - half, hx + half, mx - half, mx + half, px_ - half, px_ + half]
    rows = [ty - 17 + k for k in range(44) if 0.6 < ty - 17 + k < A.h - 0.6]
    for xs in A.seams:
        for y in rows:
            v = [(xs - 0.55, y + 0.3), (xs, y - 0.3), (xs + 0.55, y + 0.3)]
            for a, b in zip(v, v[1:]):
                for p_, q_ in clip_run(a, b, A.kw, least=0.3):
                    A.white.append(([p_, q_], 0.18))
        A.kw.rect(xs - 0.9, 0, xs + 0.9, A.h)
        A.kg.rect(xs - 0.9, 0, xs + 0.9, A.h)

    def patch(i, j):
        return ((abs(i) + abs(j)) % 4 < 2) if abs(j) <= 14 else plain(i, j)

    def herring(i, j):
        return (abs(i) + j) % 4 < 2
    S = A.seams
    A.zones = [(0.0, S[0], 1.0, 1.5, plain, "left edge, plain"), (S[0], S[1], 1.0, hx, patch, "hours patch, diamond twill"),
               (S[1], S[2], 1.0, cx, herring, "colon, herringbone"), (S[2], S[3], 1.0, mx, patch, "minutes patch, diamond twill"),
               (S[3], S[4], 1.0, sx, patch, "seconds patch, diamond twill"), (S[4], S[5], 1.0, px_, patch, "AM/PM patch, diamond twill"),
               (S[5], A.w, 1.0, 186.5, plain, "right edge, plain")]
    A.n_white, A.n_gold = weave(A, [z[:5] for z in A.zones], rows, ty)
    A.draft_bad = draft_mismatch(patch, 0, 21, 14)
    return A


def check_disp(A):
    say("== display, light layout YARN: measures (raster %d px per mm; a gap is the centre distance less one pixel)" % RES)
    B, res, out = A.B, RES, {}
    M = inks(A)
    say("   new holes (round, 1.0 drill, 1.8 pad) against the board's copper as in the file, less HL1-HL8, the BL_A tracks and M_A; HL9 3.0 lower:")
    worst, worsthv = 9e9, 9e9
    for nm, pair in list(A.new_holes.items()):
        for (x, y) in pair:
            b, h = pad_gap(B, x, y, 0.9)
            worst, worsthv = min(worst, b[0]), min(worsthv, h[0])
            say("      %s (%.3f, %.2f): other copper %.2f (%s); 185 V copper %.2f (%s)" % (nm, x, y, b[0], b[1], h[0], h[1]))
    out["new_other"], out["new_hv"] = worst, worsthv
    say("   disp-3-4's slots and holes, the same check against rev B's copper as it is today (slot pads as their 1.8 x 3.3 boxes; holes r 0.9).")
    say("   The earlier rounds re-route ANODE_H1 (final-3 item D6) and the BL_A lines; those moves are not in the board file, so H's driven slot reads as a clash here:")
    for nm, (a, b_) in list(D_SLOT.items()) + list(D_HOLE.items()):
        for tag, (x, y) in (("driven", a), ("return", b_)):
            if nm in D_SLOT:
                hx_, hy_ = (1.65, 0.9) if nm in ("S", "S2") else (0.9, 1.65)
                rim = [(x + hx_ * u, y + hy_ * v) for u in (-1, 1) for v in [k / 8.0 - 1 for k in range(17)]]
                rim += [(x + hx_ * v, y + hy_ * u) for u in (-1, 1) for v in [k / 8.0 - 1 for k in range(17)]]
                res_ = [pad_gap(B, qx, qy, 0.0) for qx, qy in rim]
                g, h = min(r_[0] for r_ in res_), min(r_[1] for r_ in res_)
            else:
                g, h = pad_gap(B, x, y, 0.9)
            say("      %-2s %s (%.3f, %.2f): other copper %.2f (%s); 185 V %.2f" % (nm, tag, x, y, g[0], g[1], h[0]))
    hvm, cum, padm, body = Mask(A.w, A.h, res), Mask(A.w, A.h, res), Mask(A.w, A.h, res), Mask(A.w, A.h, res)
    for pd in A.padlist:
        if pd["kind"] == "np_thru_hole":
            continue
        for m in ([padm] + ([hvm] if yb.hv(pd["net"]) else [cum])):
            if pd["shape"] == "circle":
                m.disc((pd["x"], pd["y"]), pd["sx"] / 2)
            else:
                m.rect(pd["x"] - pd["sx"] / 2, pd["y"] - pd["sy"] / 2, pd["x"] + pd["sx"] / 2, pd["y"] + pd["sy"] / 2)
    for t in B["tracks"]:
        if t["layer"] == "F.Cu":
            (hvm if yb.hv(t["net"]) else cum).seg(t["a"], t["b"], t["w"] / 2)
    for l in A.lights:
        body.line(l["pts"], 1.0)

    def row(label, rule, got):
        out[label] = got
        say("   %-62s rule %-5s measured %s" % (label, rule, "none in reach" if got is None else "%.2f at (%.1f, %.1f)" % (got[0], got[1][0], got[1][1])))
    row("gold to 185 V copper on the front (pads, F.Cu tracks)", "1.00", gap(edt(hvm.a, res, 3.0), M["gold"].a, res))
    row("gold to other copper on the front (pads, slots, KS tracks)", "0.35", gap(edt(cum.a, res, 3.0), M["gold"].a, res))
    row("white to a pad, slot or hole", "0.30", gap(edt(padm.a, res, 3.0), M["white"].a, res))
    row("white to gold", "0.15", gap(edt(M["gold"].a, res, 3.0), M["white"].a, res))
    d_body = edt(body.a, res, 3.0)
    row("gold to a filament's body (2.0 wide; covers the bars' end caps)", "0.30", gap(d_body, M["gold"].a, res))
    row("white to a filament's body", "0.30", gap(d_body, M["white"].a, res))
    say("   body to body, the closest pairs (rule 0.4 line to line; a minus means the drawn ends overlap):")
    names = [l["name"].split(",")[0] for l in A.lights]
    masks = []
    for l in A.lights:
        m = Mask(A.w, A.h, res)
        m.line(l["pts"], 1.0)
        masks.append(m.a)
    pairs = []
    for i in range(len(masks)):
        di = edt(masks[i], res, 1.2)
        for j in range(i + 1, len(masks)):
            g = gap(di, masks[j], res)
            if g and g[0] < 1.0:
                pairs.append((g[0], names[i], names[j], g[1]))
    for g, a, b_, at in sorted(pairs):
        say("      %-3s to %-3s %.2f at (%.1f, %.1f)" % (a, b_, g, at[0], at[1]))
    out["pairs"] = sorted(pairs)
    # what the case shows: its window less the brow, the glass, the lamps, the bodies
    seen = Mask(A.w, A.h, res)
    seen.rect(*CASE_WIN)
    hid = Mask(A.w, A.h, res)
    hid.rect(97.505, 0, 140.265, VALANCE_Y)
    for (x, y) in A.t12:
        hid.poly(rrect(x - GLASS12[0] / 2, y - GLASS12[1] / 2, x + GLASS12[0] / 2, y + GLASS12[1] / 2, GLASS12[2]))
    for (x, y) in A.t17:
        hid.poly(rrect(x - GLASS17[0] / 2, y - GLASS17[1] / 2, x + GLASS17[0] / 2, y + GLASS17[1] / 2, GLASS17[2]))
    for c in A.lamps:
        hid.disc(c, LAMP_D / 2)
    for c in A.screws:
        hid.disc(c, 2.75)
    hid.disc(A.bead, 1.9)
    free = seen.a & ~hid.a & ~body.a
    ink = M["white"].a | M["gold"].a | padm.a | body.a
    d_ink = edt(ink | hid.a, res, 3.0)
    far = np.where(free, d_ink, 0)
    j, i = np.unravel_index(np.argmax(far), far.shape)
    out["cover"] = 100.0 * float(((d_ink <= 1.2) & free).sum()) / float(free.sum())
    out["empty"] = (float(far[j, i]), ((i + 0.5) / res, (j + 0.5) / res))
    say("   the board the case shows (window x %.1f to %.1f, y %.1f to %.1f, less the brow, the glass, the lamps and the bodies): %.0f mm2;"
        " %.1f %% of it within 1.2 mm of ink; the largest empty spot has radius %.2f at (%.1f, %.1f)"
        % (CASE_WIN[0], CASE_WIN[2], CASE_WIN[1], CASE_WIN[3], free.sum() / res ** 2, out["cover"], far[j, i], (i + 0.5) / res, (j + 0.5) / res))
    lowest = max(max(p[1] for p in l["pts"]) + 1.0 for l in A.lights)
    out["lowest"] = lowest
    say("   the lowest lit body ends at y %.2f; the case's sill top is at y %.1f: no sill change (disp-3-4 needed 0.8 to 1.1)" % (lowest, CASE_WIN[3]))
    say("   symmetry (the lights' end points against their mirror image, mm):")
    L = {l["name"].split(",")[0]: l["pts"] for l in A.lights}

    def dev(names_, xa):
        ends = [p for n_ in names_ for p in (L[n_][0], L[n_][-1])]
        return max(min(math.hypot(2 * xa - p[0] - e[0], p[1] - e[1]) for e in ends) for p in ends)
    for label_, names_, xa in (("seconds: S, S2, N, Bs", ("S", "S2", "N", "Bs"), A.axes["seconds"]), ("colon: Q1, Q2, CF", ("Q1", "Q2", "CF"), A.axes["colon"]),
                               ("brackets and their row stitches: H, M, Bh, Bm (about the tubes' own middle)", ("H", "M", "Bh", "Bm"), A.axes["tubes"]),
                               ("the hem F", ("F",), A.axes["frame"])):
        d = dev(names_, xa)
        out["sym " + label_] = d
        say("      %-78s axis x %.3f: off by %.3f" % (label_, xa, d))
    say("      P (the AM/PM box): one piece, plainly directional, as in V3b; the colon's axis (%.3f) and the tubes' middle (%.3f) differ by %.3f, as the board's tubes do"
        % (A.axes["colon"], A.axes["tubes"], A.axes["colon"] - A.axes["tubes"]))
    say("      the patches' draft: cells that differ from their mirror image %d (0 = exact)" % A.draft_bad)
    say("   the weave: %d white dashes, %d gold dashes, %d thread dots; the needle's gold point %s"
        % (A.n_white, A.n_gold, A.n_dots, "drawn" if A.needle_tip_drawn else "NOT drawn (copper in the way)"))
    say("   the thread enters the display's bottom edge at x %.3f (the m lamp HL9's own x, from the board file)" % A.entry_x)
    say("   lights on the display (13 filaments and the m lamp; disp-3-4 had 14):")
    for l in A.lights:
        say("      %-18s %-10s %-15s %-12s drawn %.1f  dyed %-5s %s%s" % (l["name"], l["part"], l["ch"], l["held"], length(l["pts"]), l["dye"], l["place"], "  NEW" if l["new"] else ""))
    return out, M


def svg_disp(A, dye=False, lit=True, digits=("1", "2", "3", "4", "5", "6", "A", "M")):
    s = ['<rect x="0" y="0" width="%.2f" height="%.2f" fill="%s"/>' % (A.w, A.h, MASK_INK)]
    s.append(svg_inks(A))
    for pd in A.padlist:                                             # pads, slots, holes
        x, y = pd["x"], pd["y"]
        if pd["kind"] == "np_thru_hole":
            s.append('<circle cx="%.3f" cy="%.3f" r="%.3f" fill="#000"/>' % (x, y, pd["sx"] / 2))
            continue
        if pd["shape"] == "circle":
            s.append('<circle cx="%.3f" cy="%.3f" r="%.3f" fill="%s"/>' % (x, y, pd["sx"] / 2, GOLD_INK))
        else:
            s.append('<rect x="%.3f" y="%.3f" width="%.3f" height="%.3f" rx="%.2f" fill="%s"/>'
                     % (x - pd["sx"] / 2, y - pd["sy"] / 2, pd["sx"], pd["sy"], 0.4 if pd["shape"] == "slot" else 0.1, GOLD_INK))
        if pd["drill"]:
            dx, dy = pd["drill"]
            s.append('<rect x="%.3f" y="%.3f" width="%.3f" height="%.3f" rx="%.3f" fill="#000"/>' % (x - dx / 2, y - dy / 2, dx, dy, min(dx, dy) / 2))
    for (x, y) in A.screws:
        s.append('<circle cx="%.2f" cy="%.2f" r="2.75" fill="url(#steel)"/><path d="M%.2f %.2f L%.2f %.2f" stroke="#2a2a2e" stroke-width="0.5"/>'
                 % (x, y, x - 1.6, y - 1.0, x + 1.6, y + 1.0))
    for (x, y) in A.lamps:                                           # the colon's neon lamps
        s.append('<circle cx="%.2f" cy="%.2f" r="%.3f" fill="#150d07" stroke="#6b5136" stroke-width="0.2"/>' % (x, y, LAMP_D / 2))
        if lit:
            s.append('<circle cx="%.2f" cy="%.2f" r="2.6" fill="#ff7a1a" opacity="0.55" filter="url(#g2)"/><circle cx="%.2f" cy="%.2f" r="1.15" fill="#ffd9a2"/>' % (x, y, x, y))
    x, y = A.bead                                                    # the m lamp: the bead the thread comes in through
    s.append('<circle cx="%.2f" cy="%.2f" r="1.9" fill="#3a2a14"/>' % (x, y))
    if lit:
        s.append('<circle cx="%.2f" cy="%.2f" r="2.6" fill="#ff8a1c" opacity="0.6" filter="url(#g2)"/>' % (x, y))
    s.append('<circle cx="%.2f" cy="%.2f" r="1.5" fill="%s"/>' % (x, y, "#ffb65c" if lit else "#7a5a2c"))
    for (x, y) in A.t12 + A.t17:                                     # the tubes hide the board behind them
        w_, h_, r_ = GLASS17 if (x, y) in A.t17 else GLASS12
        s.append('<rect x="%.3f" y="%.3f" width="%.2f" height="%.2f" rx="%.1f" fill="#0a0705" fill-opacity="0.80"/>' % (x - w_ / 2, y - h_ / 2, w_, h_, r_))
    if lit:                                                          # the filaments
        for layer in (3, 2, 1, 0):
            for l in A.lights:
                glow, core = TINT[l["dye"] if dye else WARM]
                d = d_of(l["pts"])
                if layer == 3:
                    s.append('<path d="%s" fill="none" stroke="%s" stroke-width="4.6" stroke-linecap="round" stroke-linejoin="round" opacity="0.30" filter="url(#g3)"/>' % (d, glow))
                elif layer == 2:
                    s.append('<path d="%s" fill="none" stroke="%s" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round" opacity="0.6" filter="url(#g2)"/>' % (d, glow))
                elif layer == 1:
                    s.append('<path d="%s" fill="none" stroke="%s" stroke-width="2.0" stroke-linecap="round" stroke-linejoin="round"/>' % (d, glow))
                else:
                    s.append('<path d="%s" fill="none" stroke="%s" stroke-width="1.0" stroke-linecap="round" stroke-linejoin="round" opacity="0.95" filter="url(#g1)"/>' % (d, core))
    k = 0
    for (x, y) in A.t12[:4] + A.t17 + A.t12[4:]:                     # the glass's edge, then the digit
        w_, h_, r_ = GLASS17 if (x, y) in A.t17 else GLASS12
        s.append('<rect x="%.3f" y="%.3f" width="%.2f" height="%.2f" rx="%.1f" fill="#1a0f06" fill-opacity="0.18" stroke="#d9b98f" stroke-opacity="0.45" stroke-width="0.22"/>'
                 % (x - w_ / 2, y - h_ / 2, w_, h_, r_))
        if lit:
            fs = 12.5 if (x, y) in A.t17 else 23.0
            t = ('<text x="%.2f" y="%.2f" font-family="Inter, DejaVu Sans" font-weight="200" font-size="%.1f" text-anchor="middle" fill="%%s"%%s>%s</text>'
                 % (x, y + fs * 0.355, fs, digits[k]))
            s.append(t % ("#ff6a10", ' opacity="0.75" filter="url(#g2)"'))
            s.append(t % ("#ffcf9a", ""))
        k += 1
    x0_, y0_, x1_, y1_ = CASE_WIN                                     # what the case hides, dimmed
    s.append('<path d="M0 0H%.2fV%.2fH0Z M%.2f %.2fV%.2fH%.2fV%.2fZ" fill="#000" fill-opacity="0.5" fill-rule="evenodd"/>' % (A.w, A.h, x0_, y0_, y1_, x1_, y0_))
    s.append('<rect x="97.505" y="%.2f" width="%.3f" height="%.2f" fill="#000" fill-opacity="0.5"/>' % (y0_, 140.265 - 97.505, VALANCE_Y - y0_))
    s.append('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="none" stroke="#8a8a90" stroke-opacity="0.5" stroke-width="0.12" stroke-dasharray="1 0.7"/>'
             % (x0_, y0_, x1_ - x0_, y1_ - y0_))
    return "".join(s)


def sheet_disp(A, D):
    notes = [
        "<b>The idea.</b> The thread comes up from the fascia at x %.1f, through the m lamp (a bead on the hem), and sews the display once round: "
        "the hem (F) from right to left; then back along a row of stitches under the patches, climbing into each patch on the way: up one colon stitch, round "
        "the hours, across the colon's foot, round the minutes, down the other colon stitch; over the seconds and back; round AM/PM. It ends in the needle: "
        "the rigid 38 bar over the seconds, with a gold point." % A.entry_x,
        "<b>Lights: 13 filaments and the m lamp</b> (disp-3-4 had 14). Kept from disp-3-4, same slots and holes: F, H, M, P, S, S2, the colon bars Q1 and Q2 (shim), "
        "the colon foot CF, and the lintel, now the needle N (driven at its point, as the routing plan swapped it). <b>New: three 38 rigid bars</b> Bh, Bm, Bs at y 36.4, "
        "one under each patch on the patch's own axis (they take the place of the four 60 flex F2 and F3). Dropped: F2L, F2R, F3L, F3R. All warm here.",
        "<b>What it mends in disp-3-4:</b> no line below y 37.4, so the case's sill stays where it is; rigid bars under the hem hold themselves (the flex twins hung on their "
        "ends 0.4 from the next line); the needle's eye end and P's return pad are one net. Hidden by the case: dimmed (outside the dashed window; the brow over the seconds).",
        "<b>Ground:</b> each tube group is a patch with its own diamond twill, centred on the group; herringbone seams and a herringbone colon; plain cloth below and at the ends. "
        "Gold warp %.2f, white weft %.2f. The dotted links are the thread under the cloth; most of them run under the glass." % (W_GOLD, W_WHITE),
        "<b>Measured (0.05 mm raster; copper as in the board file, less HL1 to HL8 and the BL_A tracks):</b> the six new holes keep %.2f or more from other copper and %.2f from 185 V copper; "
        "gold to 185 V copper on the front %.2f (rule 1.0), to other pads %.2f; white to a pad %.2f; ink to a body %.2f / %.2f (gold / white); the seen board within 1.2 mm of ink: %.1f %%."
        % (D["new_other"], D["new_hv"], D["gold to 185 V copper on the front (pads, F.Cu tracks)"][0], D["gold to other copper on the front (pads, slots, KS tracks)"][0],
           D["white to a pad, slot or hole"][0], D["gold to a filament's body (2.0 wide; covers the bars' end caps)"][0], D["white to a filament's body"][0], D["cover"]),
        "<b>Buildable?</b> Needs a DISP rev C as disp-3-4 did (slots, holes, the shim, the BL_A routes), with six round holes more and eight slots fewer. "
        "The three new bars' drive tracks are not routed. Glass outlines and corner radii are assumed, as before.",
    ]
    m = 3.0
    svg = board_svg('<g transform="translate(%.2f %.2f)">%s</g>' % (m, m, svg_disp(A)), A.w + 2 * m, A.h + 2 * m)
    sheet("yarn-disp", "YARN, the display: four patches sewn on, a hem, a row of stitches, a needle",
          "TS06-DISP (191.4 x 44), outline, pads, holes and copper from the board file; slots and holes of disp-3-4 from its write-up; 11.5 px per mm; lights on, all warm",
          [("", svg)], notes, int(round((A.w + 2 * m) * PX)) + 68)


TMP = tempfile.mkdtemp(prefix="yarn-")


def main():
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    say("YARN pair, draw_yarn.py %s" % what)
    A = fascia()
    F, FM = check_fascia(A)
    if what in ("all", "fascia"):
        sheet_fascia(A, F)
        sheet_back(A, F)
    Dp = display()
    D, DM = check_disp(Dp)
    say("== the pair: the thread leaves the fascia at x %.3f and enters the display at x %.3f (the two boards share one x frame: both are 191.4 wide and "
        "start at world X 0 in 3d/case-pair/case_pair.py)" % (A.exit_x, Dp.entry_x))
    if what in ("all", "disp"):
        sheet_disp(Dp, D)
    open(os.path.join(OUT, "measures.txt"), "w", encoding="utf-8").write("\n".join(LOG) + "\n")


if __name__ == "__main__":
    main()
