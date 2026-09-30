#!/usr/bin/env python3
"""Variations on TS06-FASCIA's front artwork: the same board, the same copper, a different face.

    python3 tools/fascia_art.py VARIANT OUT.kicad_pcb [--base A|R]
    python3 tools/fascia_art.py all OUTDIR [--base A|R]       # every variant into OUTDIR
    python3 tools/fascia_art.py --list

VARIANT is one of ledger, plates, drafting, trays (below). --base picks the board: A is
PCB/TS06-FASCIA (176 x 40, controls on y 14), R is PCB/TS06-FASCIA-rhythm (191.4 x 40, controls
on y 16). The output is a scratch board. Nothing under PCB/ is written.

WHAT CHANGES. Only the front artwork: every top-level graphic (gr_line, gr_arc, gr_circle,
gr_poly, gr_text) on F.Cu, F.Mask or F.SilkS is removed and the variant's artwork is written in
its place. Footprints, tracks, zones, holes, the back silk, Edge.Cuts and User.1 are copied
byte for byte, and same_copper() proves it on every build. On this board F.Cu carries no track
and no pad (every part is on the back), so the front copper IS the gold artwork.

WHAT EVERY VARIANT KEEPS (TS06-FASCIA's own language, spec §1 and §6):
  * two inks with two jobs: gold (ENIG: F.Cu with the same shape opened in F.Mask) for the logic
    and the − / +, white silk for the names;
  * the dial's six fixed names on a 150° fan at exactly 30.00° per step, 1 at the top, 6 at the
    bottom, to the right of the knob;
  * §1's SUB rule drawn, not captioned: a gold box round SUB; a gold trace that ends directly
    beneath FIELD at its down-throw (6.6 mm below its centre) and runs into the box; two more
    that leave the box for positions 3 (DISPLAY) and 5 (FORMAT/DATE); nothing drawn where a
    lever swings;
  * no wordmark and no insignia.

WHAT IT FIXES, in every variant: labels at least 3.0 mm (KiCad's text size is the cap height,
measured with pcbnew on KiCad 10.0.6); silk strokes and lines at least 0.15 mm; silk kept 0.3 mm
off the gold and off the holes (there are no front pads); legend rows evenly spaced; art at
least 1.4 mm inside the edge and clear of the M2.5 screw heads.

Gold is drawn as the mask opening (the visible shape) with the copper 0.05 mm larger each side,
so a mask misregistration shows gold, never bare laminate.

THE VARIANTS (one line each; the owner's review has pictures):
  ledger    A set straight: gold C-arc and ticks, fan leaders into an index column of numerals,
            upright regular capitals; the SUB bracket's two diagonals made equal (45°).
  plates    Engraved nameplates: MODE / FIELD / SUB as white plates with the letters cut out,
            heavy gold index bars instead of an arc, condensed capitals, the SUB rule as
            PCB-style traces with 45° corners and round terminals, − / + in gold key frames.
  drafting  Drawing-office: a hairline white dial ring with the 150° fan in gold, leaders ending
            in dots, light italic capitals, the SUB rule in fine gold with arrowheads.
  trays     Instrument trays: each group stands on a white rule with its names set in breaks of
            the rule, gold index triangles on a heavy gold arc, bold capitals, heavy gold rule.

Every build runs check(): text size, stroke and line widths, spacing between items, the edge,
the screw heads, the control rings, the knob and the levers' swing. A failure stops the build.
"""
import argparse, math, os, re, sys, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
BASES = {"A": os.path.join(ROOT, "PCB", "TS06-FASCIA", "TS06-FASCIA.kicad_pcb"),
         "R": os.path.join(ROOT, "PCB", "TS06-FASCIA-rhythm", "TS06-FASCIA-rhythm.kicad_pcb")}
ART_LAYERS = ("F.Cu", "F.Mask", "F.SilkS")
ART_KINDS = ("gr_line", "gr_arc", "gr_circle", "gr_poly", "gr_text", "gr_rect", "gr_curve")
NAMES = ["NORMAL", "SET TIME", "DISPLAY", "AMBIENT", "FORMAT/DATE", "INFO"]
ANG = [-75.0 + 30.0 * k for k in range(6)]          # position k+1, degrees, y down: 1 at the top
LIVE = (2, 4)                                       # positions 3 and 5 read SUB (spec §1)
THROW = 6.6                                         # FIELD's down-throw: the enable trace's end, below its centre
GOLD_GROW = 0.05                                    # copper past the mask opening, each side

# KiCad 10.0.6 stroke font, measured with pcbnew at size 10 / stroke 1 (see --help): per 1 mm of
# text size, the advance (the justification box), and the stroke-centre ink's left bearing and
# width. Caps run from -0.543 to +0.457 of the size about the anchor; the slash descends to 0.696.
FONT = {"NORMAL": (6.005, 0.304, 5.571), "SET TIME": (6.767, 0.256, 6.286), "DISPLAY": (6.052, 0.304, 5.619),
        "AMBIENT": (6.290, 0.161, 6.000), "FORMAT/DATE": (10.338, 0.304, 9.810), "INFO": (3.529, 0.304, 3.000),
        "MODE": (4.195, 0.304, 3.667), "FIELD": (4.148, 0.304, 3.619), "SUB": (3.100, 0.256, 2.619),
        "1": (1.052, 0.256, 0.571), "2": (1.052, 0.209, 0.619), "3": (1.052, 0.209, 0.619),
        "4": (1.052, 0.256, 0.619), "5": (1.052, 0.256, 0.571), "6": (1.052, 0.256, 0.571)}
CAP_UP, CAP_DN, SLASH_DN = 0.543, 0.457, 0.696
ITALIC_SLANT = 0.125                                # KiCad's italic shear, measured on "E"


# ============================================================================ the base board
def child_spans(src):
    """(start, end) of every child of the root (kicad_pcb ...) list, by paren depth."""
    spans, depth, start, i, n, in_str = [], 0, None, 0, len(src), False
    while i < n:
        c = src[i]
        if in_str:
            if c == "\\":
                i += 1
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == "(":
            depth += 1
            if depth == 2:
                start = i
        elif c == ")":
            if depth == 2:
                spans.append((start, i + 1))
            depth -= 1
        i += 1
    return spans


def is_art(block):
    head = re.match(r"\((\w+)", block).group(1)
    ly = re.search(r'\(layer "([^"]+)"', block)
    return head in ART_KINDS and ly is not None and ly.group(1) in ART_LAYERS


def strip_art(src):
    """The board text without its front artwork, and where the new artwork goes (the removed
    items' first position, so the file keeps KiCad's order: graphics before zones)."""
    out, last, at = [], 0, None
    for s, e in child_spans(src):
        if is_art(src[s:e]):
            j = src.rfind("\n", 0, s)                 # drop the item's own line start too
            out.append(src[last:j])
            if at is None:
                at = sum(len(x) for x in out)
            last = e
    out.append(src[last:])
    return "".join(out), at


def not_art(src):
    return [src[s:e] for s, e in child_spans(src) if not is_art(src[s:e])]


def same_copper(base_src, new_src):
    """Everything but the front artwork is identical, item for item."""
    a, b = not_art(base_src), not_art(new_src)
    if a != b:
        diff = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
        sys.exit("non-art items differ from the base: %d vs %d items, first difference at item %s"
                 % (len(a), len(b), diff[:1] or "length"))
    return len(a)


def geometry(src):
    """Controls, board size and screw holes, read from the board."""
    G = {"ctrl": {}, "screws": []}
    for s, e in child_spans(src):
        b = src[s:e]
        if not b.startswith("(footprint"):
            continue
        at = re.search(r'\n\s*\(at ([\d.-]+) ([\d.-]+)', b)
        x, y = float(at.group(1)), float(at.group(2))
        ref = re.search(r'\(property "Reference" "([^"]+)"', b)
        ref = ref.group(1) if ref else ""
        if re.match(r"SW[1-5]$", ref):
            G["ctrl"][ref] = (x, y)
        elif "MountingHole" in b[:80]:
            G["screws"].append((x, y))
    xs, ys = [], []
    for s, e in child_spans(src):
        b = src[s:e]
        if '(layer "Edge.Cuts")' in b:
            for x, y in re.findall(r'\((?:start|mid|end|xy) ([\d.-]+) ([\d.-]+)\)', b):
                xs.append(float(x))
                ys.append(float(y))
    G["W"], G["H"] = max(xs) - min(xs), max(ys) - min(ys)
    return G


# ============================================================================ the artwork model
class Art:
    """Items in board mm. ink: gold | silk. grp: items of one group may touch each other."""

    def __init__(self):
        self.items = []

    def add(self, **k):
        self.items.append(k)

    def line(self, ink, a, b, w, grp):
        self.add(kind="line", ink=ink, pts=[a, b], w=w, grp=grp)

    def path(self, ink, pts, w, grp):
        for a, b in zip(pts, pts[1:]):
            self.line(ink, a, b, w, grp)

    def arc(self, ink, c, r, a0, a1, w, grp):
        self.add(kind="arc", ink=ink, c=c, r=r, a0=a0, a1=a1, w=w, grp=grp)

    def circle(self, ink, c, r, w, grp, fill=False):
        self.add(kind="circle", ink=ink, c=c, r=r, w=w, grp=grp, fill=fill)

    def poly(self, ink, pts, grp):
        self.add(kind="poly", ink=ink, pts=pts, w=0.0, grp=grp)

    def text(self, ink, s, x, y, size, t, grp, just="left", width=None, italic=False, knockout=False):
        """y is the middle of the capitals, not KiCad's anchor."""
        self.add(kind="text", ink=ink, s=s, x=x, y=y, h=size, wd=width or size, t=t, grp=grp,
                 just=just, italic=italic, knockout=knockout)

    def rrect(self, ink, x0, y0, x1, y1, r, w, grp, chamfer=False):
        """A rounded (or chamfered) rectangle outline."""
        if chamfer:
            self.path(ink, [(x0 + r, y0), (x1 - r, y0), (x1, y0 + r), (x1, y1 - r), (x1 - r, y1),
                            (x0 + r, y1), (x0, y1 - r), (x0, y0 + r), (x0 + r, y0)], w, grp)
            return
        self.line(ink, (x0 + r, y0), (x1 - r, y0), w, grp)
        self.line(ink, (x1, y0 + r), (x1, y1 - r), w, grp)
        self.line(ink, (x1 - r, y1), (x0 + r, y1), w, grp)
        self.line(ink, (x0, y1 - r), (x0, y0 + r), w, grp)
        for c, a0 in (((x1 - r, y0 + r), -90), ((x1 - r, y1 - r), 0), ((x0 + r, y1 - r), 90), ((x0 + r, y0 + r), 180)):
            self.arc(ink, c, r, a0, a0 + 90, w, grp)


def P(c, r, deg):
    a = math.radians(deg)
    return (c[0] + r * math.cos(a), c[1] + r * math.sin(a))


def text_box(it):
    """The ink's bounding box of a text item (stroke included), from FONT. A knockout text's box
    is its plate: KiCad pads the plate by the text's stroke width on every side... plus the
    measured margin (see KO_MARGIN)."""
    adv, x0c, wc = FONT[it["s"]]
    s, h, t = it["wd"], it["h"], it["t"]
    if it["just"] == "left":
        left = it["x"] + x0c * s
    elif it["just"] == "right":
        left = it["x"] - (adv - x0c) * s
    else:
        left = it["x"] - adv * s / 2 + x0c * s
    right = left + wc * s
    top, bot = it["y"] - h / 2.0, it["y"] + h / 2.0
    if "/" in it["s"]:
        bot = it["y"] + (SLASH_DN + (CAP_UP - CAP_DN) / 2) * h
    if it["italic"]:
        right += ITALIC_SLANT * h
    box = [left - t / 2, top - t / 2, right + t / 2, bot + t / 2]
    if it.get("knockout"):
        m = KO_MARGIN * h
        box = [box[0] - m, box[1] - m, box[2] + m, box[3] + m]
    return box


KO_MARGIN = 0.25          # knockout plate margin per mm of text height (checked against the render)


def anchor_y(it):
    """KiCad's anchor for a text whose capitals should be centred on it["y"]."""
    return it["y"] + (CAP_UP - CAP_DN) / 2.0 * it["h"]


# ============================================================================ the variants
def rows(cy):
    """Six legend rows, 4.6 mm apart, the first 10.7 mm above the control row."""
    return [cy - 10.7 + 4.6 * k for k in range(6)]


def sub_rule(A, G, style):
    """§1's SUB rule for geometry G: the box round SUB, FIELD's enable trace, and the two traces
    from positions 3 and 5 (their start points in style['from3'], style['from5']).
    style: w, r (corner), chamfer (bool), top_y, bot_y, box (x0,y0,x1,y1), enable_y, arrows,
    pads (terminal dots), grp."""
    w, g = style["w"], "rule"
    fx, fy = G["ctrl"]["SW2"]
    sx, sy = G["ctrl"]["SW3"]
    x0, y0, x1, y1 = style["box"]
    A.rrect("gold", x0, y0, x1, y1, style["r"], w, g, chamfer=style.get("chamfer", False))
    ey = style["enable_y"]
    e0 = (fx, fy + THROW + max(style.get("pads") or 0.0, w / 2))   # the trace's (or pad's) top edge is the throw point
    A.path("gold", [e0, (fx, ey), (x0, ey)], w, g)
    for (px, py), rail, into in ((style["from3"], style["top_y"], y0), (style["from5"], style["bot_y"], y1)):
        d = abs(rail - py)
        up = -1 if rail < py else 1
        if style.get("chamfer_in"):
            c = style["chamfer_in"]
            pts = [(px, py), (px + d, rail), (sx - c, rail), (sx, rail - up * c), (sx, into)]
        else:
            pts = [(px, py), (px + d, rail), (sx, rail), (sx, into)]
        A.path("gold", pts, w, g)
        if style.get("pads"):
            A.circle("gold", (px, py), style["pads"], 0.0, g, fill=True)
        if style.get("arrows"):
            # an arrowhead where the trace enters the box: the supply flows into SUB
            L, Wd = style["arrows"]
            tip = (sx, into)
            A.poly("gold", [tip, (sx - Wd / 2, into + up * L), (sx + Wd / 2, into + up * L)], g)
    if style.get("pads"):
        A.circle("gold", e0, style["pads"], 0.0, g, fill=True)
    if style.get("arrows"):
        L, Wd = style["arrows"]
        A.poly("gold", [(x0, ey), (x0 - L, ey - Wd / 2), (x0 - L, ey + Wd / 2)], g)


def plus_minus(A, G, y, size, w, frame=None):
    for ref, sign in (("SW4", "-"), ("SW5", "+")):
        x = G["ctrl"][ref][0]
        h = size / 2.0
        A.line("gold", (x - h, y), (x + h, y), w, "pm" + sign)
        if sign == "+":
            A.line("gold", (x, y - h), (x, y + h), w, "pm" + sign)
        if frame:
            s, r, fw = frame
            A.rrect("gold", x - s / 2, y - s / 2, x + s / 2, y + s / 2, r, fw, "pm" + sign)


def lead_start(D, r_mark, a, r_out):
    """Where a level line through the index mark at angle a (radius r_mark) crosses radius r_out,
    on the right: every leader leaves the scale level with its own mark."""
    y = D[1] + r_mark * math.sin(math.radians(a))
    return (D[0] + math.sqrt(max(0.0, r_out * r_out - (y - D[1]) ** 2)), y)


def text_right(s, x, size, width=None, italic=False):
    """x of the ink's right end for a left-justified text anchored at x."""
    adv, x0c, wc = FONT[s]
    return x + (x0c + wc) * (width or size) + (ITALIC_SLANT * size if italic else 0)


def v_ledger(G):
    """A set straight."""
    A = Art()
    D = G["ctrl"]["SW1"]
    R = rows(D[1])
    TX, TT = 3.0, 0.3                      # position names and numerals
    CT, CTT = 3.2, 0.4                     # control names
    # the scale: gold C-arc, ticks outward
    A.arc("gold", D, 10.0, ANG[0], ANG[-1], 0.5, "scale")
    for a in ANG:
        A.line("gold", P(D, 10.0, a), P(D, 11.6, a), 0.5, "scale")
    x_num = D[0] + 15.4
    x_name = x_num + 2.2
    for k, a in enumerate(ANG):
        live = k in LIVE
        A.line("gold" if live else "silk", P(D, 12.5 if live else 12.4, a), (x_num - 1.9, R[k]), 0.4 if live else 0.2, "lead%d" % k)
        A.text("silk", str(k + 1), x_num, R[k], TX, TT, "num%d" % k, just="center")
        A.text("silk", NAMES[k], x_name, R[k], TX, TT, "name%d" % k)
    A.text("silk", "MODE", D[0] - 12.0, D[1], CT, CTT, "mode", just="right")
    ny = D[1] + 13.0
    fx, sx = G["ctrl"]["SW2"][0], G["ctrl"]["SW3"][0]
    A.text("silk", "FIELD", fx, ny, CT, CTT, "field", just="center")
    A.text("silk", "SUB", sx, ny, CT, CTT, "sub", just="center")
    e3 = text_right(NAMES[2], x_name, TX) + TT / 2 + 1.2
    e5 = text_right(NAMES[4], x_name, TX) + TT / 2 + 1.2
    sub_rule(A, G, dict(w=0.45, r=2.5, top_y=D[1] - 12.0, bot_y=D[1] + 20.0,
                        box=(sx - 11, D[1] - 9.5, sx + 11, D[1] + 16.2), enable_y=D[1] + 8.4,
                        from3=(e3, R[2]), from5=(e5, R[4])))
    plus_minus(A, G, ny, 3.4, 0.6)
    return A


def v_plates(G):
    """Engraved nameplates."""
    A = Art()
    D = G["ctrl"]["SW1"]
    R = rows(D[1])
    TX, TW, TT = 3.2, 2.4, 0.3             # condensed position names
    # the scale: a white hairline arc and six heavy gold index bars
    A.arc("silk", D, 9.2, ANG[0] - 4, ANG[-1] + 4, 0.2, "scale_w")
    for k, a in enumerate(ANG):
        A.line("gold", P(D, 10.2, a), P(D, 12.3, a), 1.0, "bar%d" % k)
    x_name = D[0] + 15.0
    for k, a in enumerate(ANG):
        A.line("silk", lead_start(D, 12.3, a, 13.4), (x_name - 0.2, R[k]), 0.2, "lead%d" % k)
        A.text("silk", NAMES[k], x_name, R[k], TX, TT, "name%d" % k, width=TW)
    ny = D[1] + 15.3                       # the plate row
    PH, PW, PT = 3.2, 2.6, 0.4
    fx, sx = G["ctrl"]["SW2"][0], G["ctrl"]["SW3"][0]
    A.text("silk", "MODE", D[0], ny, PH, PT, "mode", just="center", width=PW, knockout=True)
    A.text("silk", "FIELD", fx, ny, PH, PT, "field", just="center", width=PW, knockout=True)
    A.text("silk", "SUB", sx, ny, PH, PT, "sub", just="center", width=PW, knockout=True)
    e3 = text_right(NAMES[2], x_name, TX, TW) + TT / 2 + 2.2
    e5 = text_right(NAMES[4], x_name, TX, TW) + TT / 2 + 2.2
    sub_rule(A, G, dict(w=0.6, r=2.0, chamfer=True, chamfer_in=2.4, top_y=D[1] - 11.8, bot_y=D[1] + 21.4,
                        box=(sx - 11.5, D[1] - 9.0, sx + 11.5, D[1] + 19.0), enable_y=D[1] + 8.4,
                        from3=(e3, R[2]), from5=(e5, R[4]), pads=0.8))
    plus_minus(A, G, ny, 3.2, 0.7, frame=(6.4, 1.0, 0.5))
    return A


def v_drafting(G):
    """Drawing-office."""
    A = Art()
    D = G["ctrl"]["SW1"]
    R = rows(D[1])
    TX, TT = 3.0, 0.22                     # light italic
    CT, CTT = 3.2, 0.25
    # the dial: a hairline white ring over the dead 210°, the live 150° in gold, gold ticks
    A.arc("silk", D, 10.0, ANG[-1] + 5, 360 + ANG[0] - 5, 0.15, "ring")
    A.arc("gold", D, 10.0, ANG[0], ANG[-1], 0.3, "scale")
    for a in ANG:
        A.line("gold", P(D, 10.0, a), P(D, 11.4, a), 0.3, "scale")
    x_name = D[0] + 17.0
    x_dot = D[0] + 14.2
    for k, a in enumerate(ANG):
        # the leader starts at a dot just past the tick, runs out along the tick's own line to the
        # row's height, then level to the name: a drawing's leader, with a 90° or oblique elbow
        s = P(D, 12.4, a)
        A.circle("silk", s, 0.45, 0.0, "lead%d" % k, fill=True)
        if abs(s[1] - R[k]) < 0.6 or s[0] >= x_dot - 0.5:
            A.line("silk", s, (x_name - 0.8, R[k]), 0.15, "lead%d" % k)
        else:
            A.path("silk", [s, (x_dot, R[k]), (x_name - 0.8, R[k])], 0.15, "lead%d" % k)
        A.text("silk", NAMES[k], x_name, R[k], TX, TT, "name%d" % k, italic=True)
    A.text("silk", "MODE", D[0] - 12.0, D[1], CT, CTT, "mode", just="right", italic=True)
    ny = D[1] + 13.0
    fx, sx = G["ctrl"]["SW2"][0], G["ctrl"]["SW3"][0]
    A.text("silk", "FIELD", fx, ny, CT, CTT, "field", just="center", italic=True)
    A.text("silk", "SUB", sx, ny, CT, CTT, "sub", just="center", italic=True)
    e3 = text_right(NAMES[2], x_name, TX, italic=True) + TT / 2 + 1.2
    e5 = text_right(NAMES[4], x_name, TX, italic=True) + TT / 2 + 1.2
    sub_rule(A, G, dict(w=0.3, r=1.5, top_y=D[1] - 12.0, bot_y=D[1] + 20.0,
                        box=(sx - 11, D[1] - 9.5, sx + 11, D[1] + 16.2), enable_y=D[1] + 8.4,
                        from3=(e3, R[2]), from5=(e5, R[4]), arrows=(1.6, 1.2)))
    plus_minus(A, G, ny, 3.4, 0.35)
    return A


def v_trays(G):
    """Instrument trays."""
    A = Art()
    D = G["ctrl"]["SW1"]
    R = [y + 0.4 for y in rows(D[1])]
    TX, TT = 3.0, 0.45                     # bold position names
    CT, CTT = 3.2, 0.5
    # the scale: a heavy gold arc outside, gold index triangles pointing at the knob
    A.arc("gold", D, 12.3, ANG[0], ANG[-1], 0.6, "scale")
    for a in ANG:
        tip, b = P(D, 9.3, a), P(D, 11.5, a)
        n = (-math.sin(math.radians(a)), math.cos(math.radians(a)))
        A.poly("gold", [tip, (b[0] + 0.9 * n[0], b[1] + 0.9 * n[1]), (b[0] - 0.9 * n[0], b[1] - 0.9 * n[1])], "scale")
    x_name = D[0] + 17.4
    for k, a in enumerate(ANG):
        A.line("silk", lead_start(D, 12.3, a, 13.3), (x_name - 0.3, R[k]), 0.25, "lead%d" % k)
        A.text("silk", NAMES[k], x_name, R[k], TX, TT, "name%d" % k)
    # the trays: a rule under each group, returns at its ends, the names in breaks of the rule
    ty = D[1] + 18.5
    fx, sx = G["ctrl"]["SW2"][0], G["ctrl"]["SW3"][0]
    mx, px = G["ctrl"]["SW4"][0], G["ctrl"]["SW5"][0]
    RW, RET = 0.3, 3.0

    def tray(x0, x1, labels, grp):
        """labels: [(text, x, ink)]; the rule breaks round each."""
        cuts = []
        for s, x, ink in labels:
            if ink == "silk":
                A.text("silk", s, x, ty, CT, CTT, grp + s, just="center")
                b = text_box(A.items[-1])
                cuts.append((b[0] - 1.2, b[2] + 1.2))
            else:
                cuts.append((x - 3.2, x + 3.2))
        xs = [x0] + [v for c in sorted(cuts) for v in c] + [x1]
        for a, b in zip(xs[0::2], xs[1::2]):
            A.line("silk", (a, ty), (b, ty), RW, grp + "r%.0f" % a)
        A.line("silk", (x0, ty), (x0, ty - RET), RW, grp + "r%.0f" % x0)
        A.line("silk", (x1, ty), (x1, ty - RET), RW, grp + "r%.0f" % xs[-2])

    tray(D[0] - 21.0, text_right(NAMES[4], x_name, TX) + 3.0, [("MODE", D[0], "silk")], "tm")
    tray(fx - 8.6, sx + 13.2, [("FIELD", fx, "silk"), ("SUB", sx, "silk")], "tl")
    tray(mx - 8.0, px + 6.2, [("-", mx, "gold"), ("+", px, "gold")], "tb")
    plus_minus(A, G, ty, 3.6, 0.8)
    e3 = text_right(NAMES[2], x_name, TX) + TT / 2 + 1.4
    e5 = text_right(NAMES[4], x_name, TX) + TT / 2 + 1.4
    sub_rule(A, G, dict(w=0.8, r=2.5, top_y=D[1] - 11.8, bot_y=D[1] + 13.8,
                        box=(sx - 11.2, D[1] - 9.4, sx + 11.2, D[1] + 12.6), enable_y=D[1] + 8.4,
                        from3=(e3, R[2]), from5=(e5, R[4])))
    return A


VARIANTS = {"ledger": v_ledger, "plates": v_plates, "drafting": v_drafting, "trays": v_trays}


# ============================================================================ writing KiCad
def f(v):
    s = ("%.4f" % v).rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def emit(A, ns):
    n = [0]

    def u():
        n[0] += 1
        return str(uuid.uuid5(ns, "art%d" % n[0]))

    out = []

    def stroke(w):
        return "\t\t(stroke\n\t\t\t(width %s)\n\t\t\t(type solid)\n\t\t)\n" % f(w)

    for it in A.items:
        layers = [("F.Cu", GOLD_GROW * 2), ("F.Mask", 0.0)] if it["ink"] == "gold" else [("F.SilkS", 0.0)]
        for ly, grow in layers:
            k = it["kind"]
            if k == "line":
                (x1, y1), (x2, y2) = it["pts"]
                out.append("\t(gr_line\n\t\t(start %s %s)\n\t\t(end %s %s)\n%s\t\t(layer \"%s\")\n\t\t(uuid \"%s\")\n\t)"
                           % (f(x1), f(y1), f(x2), f(y2), stroke(it["w"] + grow), ly, u()))
            elif k == "arc":
                a0, a1 = it["a0"], it["a1"]
                s, m, e = P(it["c"], it["r"], a0), P(it["c"], it["r"], (a0 + a1) / 2), P(it["c"], it["r"], a1)
                out.append("\t(gr_arc\n\t\t(start %s %s)\n\t\t(mid %s %s)\n\t\t(end %s %s)\n%s\t\t(layer \"%s\")\n\t\t(uuid \"%s\")\n\t)"
                           % (f(s[0]), f(s[1]), f(m[0]), f(m[1]), f(e[0]), f(e[1]), stroke(it["w"] + grow), ly, u()))
            elif k == "circle":
                c, r = it["c"], it["r"]
                w = it["w"] + grow if it["w"] or not it["fill"] else grow
                out.append("\t(gr_circle\n\t\t(center %s %s)\n\t\t(end %s %s)\n%s\t\t(fill %s)\n\t\t(layer \"%s\")\n\t\t(uuid \"%s\")\n\t)"
                           % (f(c[0]), f(c[1]), f(c[0] + r), f(c[1]), stroke(w), "yes" if it["fill"] else "no", ly, u()))
            elif k == "poly":
                pts = " ".join("(xy %s %s)" % (f(x), f(y)) for x, y in it["pts"])
                out.append("\t(gr_poly\n\t\t(pts\n\t\t\t%s\n\t\t)\n%s\t\t(fill yes)\n\t\t(layer \"%s\")\n\t\t(uuid \"%s\")\n\t)"
                           % (pts, stroke(grow), ly, u()))
            elif k == "text":
                font = "\t\t\t\t(size %s %s)\n\t\t\t\t(thickness %s)\n" % (f(it["h"]), f(it["wd"]), f(it["t"] + grow))
                if it["italic"]:
                    font += "\t\t\t\t(italic yes)\n"
                just = "" if it["just"] == "center" else "\t\t\t(justify %s)\n" % it["just"]
                out.append("\t(gr_text \"%s\"\n\t\t(at %s %s 0)\n\t\t(layer \"%s\"%s)\n\t\t(uuid \"%s\")\n\t\t(effects\n"
                           "\t\t\t(font\n%s\t\t\t)\n%s\t\t)\n\t)"
                           % (it["s"], f(it["x"]), f(anchor_y(it)), ly, " knockout" if it["knockout"] else "", u(), font, just))
    return "\n".join(out)


def build(variant, base="A", out=None):
    src = open(BASES[base], encoding="utf8").read()
    G = geometry(src)
    A = VARIANTS[variant](G)
    problems = check(A, G)
    stripped, at = strip_art(src)
    ns = uuid.uuid5(uuid.NAMESPACE_URL, "ts06/fascia-art/%s/%s" % (base, variant))
    new = stripped[:at] + "\n" + emit(A, ns) + stripped[at:]
    n = same_copper(src, new)
    if out:
        open(out, "w", encoding="utf8").write(new)
    return A, G, problems, n


# ============================================================================ checks
def segments(it, step=2.0):
    """The item as stroke segments [(a, b, half-width)], or a box for text, or a polygon."""
    k = it["kind"]
    if k == "line":
        return [(it["pts"][0], it["pts"][1], it["w"] / 2)]
    if k in ("arc", "circle"):
        a0, a1 = (it["a0"], it["a1"]) if k == "arc" else (0.0, 360.0)
        n = max(2, int(abs(a1 - a0) / step))
        pts = [P(it["c"], it["r"], a0 + (a1 - a0) * i / n) for i in range(n + 1)]
        if k == "circle" and it["fill"]:
            return [(it["c"], it["c"], it["r"] + it["w"] / 2)]
        return [(a, b, it["w"] / 2) for a, b in zip(pts, pts[1:])]
    if k == "poly":
        p = it["pts"]
        return [(a, b, 0.0) for a, b in zip(p, p[1:] + p[:1])]
    x0, y0, x1, y1 = text_box(it)
    c = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return [(a, b, 0.0) for a, b in zip(c, c[1:] + c[:1])]


def area(it):
    """A filled region to test containment against: a text's box or a polygon, else None."""
    if it["kind"] == "text":
        x0, y0, x1, y1 = text_box(it)
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    if it["kind"] == "poly":
        return it["pts"]
    return None


def pseg(p, a, b):
    ax, ay = a
    dx, dy = b[0] - ax, b[1] - ay
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L))
    return math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy)


def cross(a, b, c, d):
    def o(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    return o(a, b, c) * o(a, b, d) < 0 and o(c, d, a) * o(c, d, b) < 0


def segseg(a, b, c, d):
    if cross(a, b, c, d):
        return 0.0
    return min(pseg(a, c, d), pseg(b, c, d), pseg(c, a, b), pseg(d, a, b))


def inside(p, poly):
    x, y, n, r = p[0], p[1], len(poly), False
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            r = not r
    return r


def dist(i, j):
    """Clearance between two items (negative: they overlap)."""
    best = 1e9
    for a, b, wa in segments(i):
        for c, d, wb in segments(j):
            best = min(best, segseg(a, b, c, d) - wa - wb)
    for x, y in ((i, j), (j, i)):
        ar = area(x)
        if ar:
            for a, b, w in segments(y):
                if inside(a, ar) or inside(b, ar):
                    return -1.0
    return best


def dist_pt(it, p):
    best = 1e9
    ar = area(it)
    if ar and inside(p, ar):
        return -1.0
    for a, b, w in segments(it):
        best = min(best, pseg(p, a, b) - w)
    return best


RULES = dict(silk_silk=0.25, silk_gold=0.3, gold_gold=0.3, edge=1.4, screw=3.0, ring_gap=0.4,
             knob=9.0, min_text=3.0, min_silk=0.15, lever_half=2.0, lever_up=7.0, lever_down=THROW - 0.3)


def check(A, G):
    """Every rule the owner and the fab set, plus the panel's own keep-outs. Returns the problems."""
    bad = []
    it = A.items
    for x in it:
        if x["kind"] == "text":
            if x["h"] < RULES["min_text"] - 1e-9:
                bad.append("text %r is %.2f mm tall" % (x["s"], x["h"]))
            if x["t"] < RULES["min_silk"] - 1e-9:
                bad.append("text %r stroke %.2f" % (x["s"], x["t"]))
        elif x["ink"] == "silk" and x["kind"] != "poly" and not (x["kind"] == "circle" and x["fill"]) and x["w"] < RULES["min_silk"] - 1e-9:
            bad.append("silk %s in %s is %.2f wide" % (x["kind"], x["grp"], x["w"]))
    # spacing between items of different groups
    for a in range(len(it)):
        for b in range(a + 1, len(it)):
            i, j = it[a], it[b]
            if i["grp"] == j["grp"]:
                continue
            need = RULES["silk_silk"] if i["ink"] == j["ink"] == "silk" else RULES["gold_gold"] if i["ink"] == j["ink"] else RULES["silk_gold"]
            d = dist(i, j)
            if d < need:
                bad.append("%s %s (%s) and %s %s (%s): %.2f mm apart, need %.2f" % (
                    i["ink"], i["kind"], i["grp"], j["ink"], j["kind"], j["grp"], d, need))
    # the edge, the screws, the rings, the knob, the levers' swing
    W, H = G["W"], G["H"]
    edge = [((0, 0), (W, 0)), ((W, 0), (W, H)), ((W, H), (0, H)), ((0, H), (0, 0))]
    for x in it:
        d = min(segseg(a, b, c, e) - w for a, b, w in segments(x) for c, e in edge)
        box = [p for s in segments(x) for p in s[:2]]
        if d < RULES["edge"] or any(not (0 <= p[0] <= W and 0 <= p[1] <= H) for p in box):
            bad.append("%s %s (%s) is %.2f mm from the edge" % (x["ink"], x["kind"], x["grp"], d))
        for s in G["screws"]:
            d = dist_pt(x, s)
            if d < RULES["screw"]:
                bad.append("%s (%s) is %.2f mm from the screw at %s" % (x["kind"], x["grp"], d, s))
        for ref, c in G["ctrl"].items():
            ring = 6.4 if ref == "SW1" else 5.6
            d = dist_pt(x, c)
            lim = RULES["knob"] if ref == "SW1" else ring + RULES["ring_gap"]
            enable_end = ref == "SW2" and x["grp"] == "rule" and x["kind"] in ("line", "circle") and any(
                abs(p[0] - c[0]) < 1e-6 and abs(p[1] - (c[1] + THROW)) < 1e-6 for p in (x.get("pts") or [x.get("c")]))
            if d < lim and not enable_end:
                bad.append("%s %s (%s) is %.2f mm from %s's centre, need %.2f" % (x["ink"], x["kind"], x["grp"], d, ref, lim))
        for ref in ("SW2", "SW3"):
            cx, cy = G["ctrl"][ref]
            zone = [(cx - RULES["lever_half"], cy - RULES["lever_up"]), (cx + RULES["lever_half"], cy - RULES["lever_up"]),
                    (cx + RULES["lever_half"], cy + RULES["lever_down"]), (cx - RULES["lever_half"], cy + RULES["lever_down"])]
            zi = {"kind": "poly", "pts": zone, "ink": "zone", "grp": "zone", "w": 0.0}
            if dist(x, zi) < 0:
                bad.append("%s %s (%s) is in %s's swing" % (x["ink"], x["kind"], x["grp"], ref))
    return bad


# ============================================================================ main
def main():
    ap = argparse.ArgumentParser(description="Variations on TS06-FASCIA's front artwork.")
    ap.add_argument("variant", nargs="?")
    ap.add_argument("out", nargs="?")
    ap.add_argument("--base", default="A", choices=sorted(BASES))
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list or not a.variant:
        for k, fn in VARIANTS.items():
            print("%-9s %s" % (k, fn.__doc__.strip()))
        return
    todo = list(VARIANTS) if a.variant == "all" else [a.variant]
    failed = False
    for v in todo:
        out = os.path.join(a.out, "%s-%s.kicad_pcb" % (v, a.base)) if a.variant == "all" else a.out
        if a.variant == "all":
            os.makedirs(a.out, exist_ok=True)
        A, G, problems, n = build(v, a.base, out)
        print("%s on %s: %d art items, %d other items identical to the base; %s" % (
            v, a.base, len(A.items), n, "checks clean" if not problems else "%d problems:" % len(problems)))
        for p in problems:
            print("    " + p)
        failed |= bool(problems)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
