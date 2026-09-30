#!/usr/bin/env python3
"""TS06-FASCIA-rhythm: the fascia with its controls on the display's grid.

    python3 tools/mkpcb_fascia_rhythm.py              # the chosen alignment, from the saved routes
    python3 tools/mkpcb_fascia_rhythm.py --route      # the same, routing afresh (tools/netroute.py)
    python3 tools/mkpcb_fascia_rhythm.py --study DIR [A B C] [--front]
                  # the alignments, routed, into DIR (scratch: not committed), and every composite PNG
                  # into PCB/TS06-FASCIA-rhythm; --front skips the routing (the front does not need it)

THE IDEA. The plain centred fascia (the committed TS06-FASCIA moved 7.7 mm) sits under the tube
row but ignores it: its controls fall between the tubes. Here every control is centred under a
tube, or under the centre of a tube pair, so the panel continues the row's rhythm instead of
starting a new one. Left to right stays pick the screen, pick the field, adjust the value (spec
§6). Three alignments are drawn (ALIGN, below) and one is built (CHOSEN).

THE FRAME. World X is the display board's x (0-191.4). The board is the full row width, 191.4 x
40, so board x IS world X (FASCIA_X0 = 0). y runs down from the top edge, as in every board here.
The controls sit on one row at y = CY.

WHY 191.4 AND NOT 176. With the dial under the hours pair (world 24.89) a 176 board centred at
7.7 puts the shaft 17.2 mm from its edge: the body then crowds the top-left fascia boss (0.2 mm
with the case model's Ø26.94), and the seven landing pads under it run off the edge. At 191.4 the board is the
boards' own outline: it spans cheek to cheek with the same 0.5 mm the display and driver keep,
and the case's fascia bosses sit on the cheeks instead of reaching 8 mm in from them.

WHAT IS THE SAME AS TS06-FASCIA. The netlist, the parts, the footprints of the four levers and
buttons, the connector and its pin order (1 +5V, 2 GND, 3 A6, 4 A7, 5 D7, 6 D8), the 2.0 mm
stack, the four M2.5 corner holes, and the two rules of spec §6: no plated hole anywhere (the
front carries only the decorative gold) and no back-side part inside a control body.

WHAT IS NEW.
  * TS06_Rotary_SR25_PanelMount_Rhythm, written by this script into PCB/lib/TS06.pretty: the
    SR25 panel-mount footprint with its seven landing pads moved 8 mm right and 2.5 mm up. With
    the shaft 24.89 from the edge the stock row (-24 .. +24) would start 0.9 mm from it.
  * The control row is at y 16, not 14. The rotary's rim (Ø25; the case model still carries the
    withdrawn 26.94) then stays under the case's sill: the sill need not be stepped back.
  * The dial is lettered radially: each name sits at the end of its own tick, so the lettering
    ends 26 mm right of the shaft, under the colon, and leaves the minutes free.
  * Everything on the back is placed from the controls' positions (layout()). J1 keeps TS06-FASCIA's
    place between the buttons and TS06-FASCIA's topology (layout() says why): the ladder, the
    lever pull-downs and the two button lines are laid by hand; A6, A7 and +5V are routed by
    tools/netroute.py on B.Cu only, keeping other-net copper 1.1 mm apart so the GND pour - the
    back pour, as on TS06-FASCIA - reaches every GND pad (_router()). No via, stitch or jumper.

The routes are saved in tools/mkpcb_fascia_rhythm_routes.json so the board regenerates exactly.
Coordinates are rounded to 0.001 mm; UUIDs are derived from names, so an unchanged board writes
an unchanged file.
"""
import json, math, os, re, subprocess, sys, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
PRETTY = os.path.join(ROOT, "PCB", "lib", "TS06.pretty")
NAME = "TS06-FASCIA-rhythm"
OUTDIR = os.path.join(ROOT, "PCB", NAME)
ORIG = os.path.join(ROOT, "PCB", "TS06-FASCIA", "TS06-FASCIA")
ROUTES = os.path.join(HERE, "mkpcb_fascia_rhythm_routes.json")
VER, GEN, GENV = 20260206, "pcbnew", "10.0"
NS = uuid.uuid5(uuid.NAMESPACE_URL, "ts06/" + NAME)

W, H, CR = 191.4, 40.0, 1.5            # the row's width; TS06-FASCIA's height and corner radius
CY = 16.0                              # the control row
HOLES = [(4.5, 4.5), (W - 4.5, 4.5), (4.5, H - 4.5), (W - 4.5, H - 4.5)]   # M2.5, as before

# Tube centres, world X (tools/mkpcb_disp.py IN12_X, COLON_X, IN17_X, IN15_X)
T = {"H10": 13.21, "H1": 36.57, "colon": 50.535, "M10": 63.99, "M1": 87.37,
     "S10": 108.635, "S1": 129.135, "IN15B": 150.4, "IN15A": 171.4}
HOURS = round((T["H10"] + T["H1"]) / 2, 3)          # 24.89

# The alignments considered. SW1 rotary, SW2 FIELD, SW3 SUB, SW4 minus, SW5 plus; J1 the cable.
ALIGN = {
    "A": dict(title="clock face: dial under the hours, levers under the minutes, buttons under the seconds",
              SW1=HOURS, SW2=T["M10"], SW3=T["M1"], SW4=T["S10"], SW5=T["S1"],
              under={"SW1": "hours pair", "SW2": "M10", "SW3": "M1", "SW4": "S10", "SW5": "S1"}),
    "B": dict(title="full row: dial under the hours, levers under the minutes, buttons under the ИН-15 pair",
              SW1=HOURS, SW2=T["M10"], SW3=T["M1"], SW4=T["IN15B"], SW5=T["IN15A"],
              under={"SW1": "hours pair", "SW2": "M10", "SW3": "M1", "SW4": "ИН-15Б", "SW5": "ИН-15А"}),
    "C": dict(title="right-hand rank: dial under the hours, levers under the seconds, buttons under the ИН-15 pair",
              SW1=HOURS, SW2=T["S10"], SW3=T["S1"], SW4=T["IN15B"], SW5=T["IN15A"],
              under={"SW1": "hours pair", "SW2": "S10", "SW3": "S1", "SW4": "ИН-15Б", "SW5": "ИН-15А"}),
}
CHOSEN = "B"

STEP, R_START = 30.0, 75.0             # 12 detents: exactly 30.00 deg per step, 150 deg span
LABEL = ["NORMAL", "SET TIME", "DISPLAY", "AMBIENT", "FORMAT/DATE", "INFO"]
SUBLIVE = (2, 4)                       # positions 3 and 5 read SUB
R_TICK0, R_TICK1, R_NUM = 9.2, 11.0, 13.4
TXT, CHW = 1.4, 0.95                   # dial lettering size, and the stroke font's advance per size

NETS = ["", "GND", "+5V", "A6", "A7", "D7", "D8", "TAP2", "TAP3", "TAP4", "TAP5", "LEVA", "LEVB"]
NI = {n: i for i, n in enumerate(NETS)}
PINS = {"SW1": {"1": "GND", "2": "TAP2", "3": "TAP3", "4": "TAP4", "5": "TAP5", "6": "+5V", "7": "A6"},
        "SW2": {"1": "LEVA", "2": "A7"}, "SW3": {"1": "LEVB", "2": "A7"},
        "SW4": {"1": "GND", "2": "D7"}, "SW5": {"1": "GND", "2": "D8"},
        "R5": {"1": "+5V", "2": "TAP5"}, "R4": {"1": "TAP5", "2": "TAP4"}, "R3": {"1": "TAP4", "2": "TAP3"},
        "R2": {"1": "TAP3", "2": "TAP2"}, "R1": {"1": "TAP2", "2": "GND"},
        "R7": {"1": "LEVA", "2": "GND"}, "R6": {"1": "+5V", "2": "A7"}, "R8": {"1": "LEVB", "2": "GND"},
        "J1": {"1": "+5V", "2": "GND", "3": "A6", "4": "A7", "5": "D7", "6": "D8"}}
VALUE = {"SW1": "SR25 6-pos", "SW2": "FIELD", "SW3": "SUB", "SW4": "MINUS", "SW5": "PLUS", "J1": "PH 6",
         "R1": "4k7", "R2": "4k7", "R3": "4k7", "R4": "4k7", "R5": "4k7", "R6": "10k", "R7": "20k", "R8": "10k"}
FP = {"SW1": "TS06_Rotary_SR25_PanelMount_Rhythm", "SW2": "TS06_MT1_Lever_PanelMount",
      "SW3": "TS06_MT1_Lever_PanelMount", "SW4": "TS06_KMD1_Button_PanelMount",
      "SW5": "TS06_KMD1_Button_PanelMount", "J1": "TS06_JST_PH_S6B-PH-SM4-TB_Back"}
FP.update({r: "TS06_R_1206_HandSolder" for r in ("R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8")})
BACK = {r for r in FP if r.startswith(("R", "J"))}

# the rotary's landing pads relative to its shaft: +5V .. GND left to right, then the wiper
ROT_PADS = {"6": -16.0, "5": -8.0, "4": 0.0, "3": 8.0, "2": 16.0, "1": 24.0, "7": 32.0}
ROT_PAD_DY = 15.0
LADDER_Y = 35.2                        # the five 4k7 in a row under the landing pads
LEV_PAD_DY, LEV_R_Y = 9.5, 30.0        # lever pads (footprint), their pull-downs 4.5 below them
REF_AT = {}                            # a reference that must move off a neighbour (none now)
J1_DX = 5.0                            # J1 right of the minus button: its pin 5 (D7) under that button's D7 pad
J1_Y = 33.4                            # as on TS06-FASCIA: courtyard bottom 38.5, where the case model's lead leaves


def U(s):
    return str(uuid.uuid5(NS, s))


def f3(v):
    s = ("%.4f" % v).rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


# ============================================================================ the new footprint
def write_rotary_footprint():
    """TS06_Rotary_SR25_PanelMount with the landing pads moved: same hole, same body keepout,
    same lug-ring drawing. Written textually from the stock file so both stay in step."""
    src = open(os.path.join(PRETTY, "TS06_Rotary_SR25_PanelMount.kicad_mod"), encoding="utf8").read()
    src = src.replace('(footprint "TS06_Rotary_SR25_PanelMount"', '(footprint "TS06_Rotary_SR25_PanelMount_Rhythm"', 1)
    src = re.sub(r'\(descr "([^"]*)"\)', lambda m: '(descr "%s Landing pads moved +8 mm in x and -2.5 mm in y '
                 '(row at y+15, x -16..+32: +5V, TAP5..TAP2, GND, wiper) so the row clears the board edge with the '
                 'shaft 24.89 mm from it - TS06-FASCIA-rhythm, written by tools/mkpcb_fascia_rhythm.py.")' % m.group(1), src, 1)

    def pad(m):
        n = m.group(1)
        return m.group(0).replace(m.group(2), "(at %.4f %.4f)" % (ROT_PADS[n], ROT_PAD_DY))
    src = re.sub(r'\(pad "(\d)" smd rect\n\t\t(\(at [\d.-]+ [\d.-]+\))', pad, src)
    for n, dx in ROT_PADS.items():
        assert "(at %.4f %.4f)" % (dx, ROT_PAD_DY) in src, n
    path = os.path.join(PRETTY, FP["SW1"] + ".kicad_mod")
    if not os.path.exists(path) or open(path, encoding="utf8").read() != src:
        open(path, "w", encoding="utf8", newline="\n").write(src)


# ============================================================================ layout
def layout(key):
    """Every part's position and every hand-laid track for one alignment. Board x = world X."""
    a = ALIGN[key]
    P = {r: (a[r], CY) for r in ("SW1", "SW2", "SW3", "SW4", "SW5")}
    cx = a["SW1"]
    # the A6 ladder: resistor k between landing pads k and k+1, in the order the pads run
    order = ["6", "5", "4", "3", "2", "1"]
    refs = ["R5", "R4", "R3", "R2", "R1"]
    for i, r in enumerate(refs):
        x = cx + (ROT_PADS[order[i]] + ROT_PADS[order[i + 1]]) / 2
        P[r] = (round(x, 4), LADDER_Y)
    # each lever's pull-down straight under its pad 1, so the drop is one vertical track
    P["R7"] = (round(a["SW2"] - 1.6 + 1.85, 4), LEV_R_Y)
    P["R8"] = (round(a["SW3"] - 1.6 + 1.85, 4), LEV_R_Y)
    # the A7 pull-up between the two lever bodies
    mid = round((a["SW2"] + a["SW3"]) / 2, 3)
    P["R6"] = (mid, CY + 6.5)
    # The connector between the two buttons, as on TS06-FASCIA. Its pin order, seen from the
    # front, is D8 D7 A7 A6 GND +5V - the reverse of the controls' order - so it can only sit
    # where most nets arrive from ONE side: here D7 drops straight in from the minus button, D8
    # passes under the pins from the plus button, and everything else comes from the left. The
    # study tried it between the levers (a 60 mm shorter cable) and found no planar routing that
    # left every GND pad on the pour: A7's four ends (both levers, R6, pin 4) straddle it.
    P["J1"] = (round(a["SW4"] + J1_DX, 4), J1_Y)
    tracks = []

    def trk(net, pts, w=0.25):
        for p, q in zip(pts, pts[1:]):
            tracks.append((net, "B.Cu", (round(p[0], 4), round(p[1], 4)), (round(q[0], 4), round(q[1], 4)), w))
    # ladder: every landing pad drops to a fork that lands on the resistor either side of it
    yp = CY + ROT_PAD_DY
    yf = LADDER_Y - 2.05
    for i, n in enumerate(order):
        x = cx + ROT_PADS[n]
        net = PINS["SW1"][n]
        trk(net, [(x, yp), (x, yf)])
        if i > 0:
            trk(net, [(x, yf), (x - 2.05, LADDER_Y)])
        if i < len(order) - 1:
            trk(net, [(x, yf), (x + 2.05, LADDER_Y)])
    for sw, r, net in (("SW2", "R7", "LEVA"), ("SW3", "R8", "LEVB")):
        x = a[sw] - 1.6
        trk(net, [(x, CY + LEV_PAD_DY), (x, LEV_R_Y)])
    # the two button lines, laid as on TS06-FASCIA. Pin 6 (D8) sits under the minus button's pad
    # gap: D8 rises straight through it, runs over both buttons' pads under their bodies and
    # drops into the plus button's D8 pad; D7 drops from the minus button into pin 5. SW4's GND
    # pad stays outside the loop the two make with the pin row, so the pour still reaches it.
    jx, jy = P["J1"]
    s4, s5 = a["SW4"], a["SW5"]
    yd8 = CY + 7.0
    trk("D8", [(jx - 5.0, jy - 2.85), (s4, jy - 2.85 - 1.0), (s4, yd8), (s5 + 1.6, yd8), (s5 + 1.6, CY + LEV_PAD_DY)])
    trk("D7", [(s4 + 1.6, CY + LEV_PAD_DY), (s4 + 1.6, jy - 5.7), (jx - 3.0, jy - 5.3), (jx - 3.0, jy - 2.85)])
    return dict(key=key, a=a, P=P, fixed=tracks)


# ============================================================================ artwork
def artwork(L):
    """The front: dial, lettering and the SUB rule in gold; keepout circles for reference."""
    a, G = L["a"], []
    cx = a["SW1"]

    def line(x1, y1, x2, y2, layer, w):
        G.append(("line", layer, (x1, y1, x2, y2, w)))

    def arc(s, m, e, layer, w):
        G.append(("arc", layer, (s, m, e, w)))

    def text(s, x, y, layer, size, thick, just="", bold=False, mirror=False):
        G.append(("text", layer, (s, x, y, size, thick, just, bold, mirror)))

    def gold_line(x1, y1, x2, y2, w=0.45):
        line(x1, y1, x2, y2, "F.Cu", w + 0.15)
        line(x1, y1, x2, y2, "F.Mask", w)

    def gold_arc(s, m, e, w=0.45):
        arc(s, m, e, "F.Cu", w + 0.15)
        arc(s, m, e, "F.Mask", w)

    def gold_text(s, x, y, size, thick, just="", bold=False):
        text(s, x, y, "F.Cu", size, thick + 0.12, just, bold)
        text(s, x, y, "F.Mask", size, thick, just, bold)

    def P(r, i):
        t = math.radians(R_START - STEP * i)
        return cx + r * math.cos(t), CY - r * math.sin(t)

    def Pa(r, deg):
        t = math.radians(deg)
        return cx + r * math.cos(t), CY - r * math.sin(t)

    # the dial: a gold arc over the 150 deg span, a gold tick per detent, the numeral and the name
    gold_arc(Pa(R_TICK1, R_START), Pa(R_TICK1, 0.0), Pa(R_TICK1, R_START - STEP * 5), 0.5)
    ends = {}
    for i in range(6):
        gold_line(*P(R_TICK0, i), *P(R_TICK1, i), 0.5)
        nx, ny = P(R_NUM, i)
        gold_text(str(i + 1), nx, ny, TXT, 0.22)
        text(LABEL[i], nx + 1.4, ny, "F.SilkS", TXT, 0.22, "left")
        ends[i] = (nx + 1.4 + len(LABEL[i]) * TXT * CHW, ny)
    text("MODE", cx - 8.0, 3.2, "F.SilkS", 1.7, 0.28, bold=True)

    # lever and button lettering
    for r, s in (("SW2", "FIELD"), ("SW3", "SUB")):
        text(s, a[r], CY + 12.4, "F.SilkS", 1.9, 0.32, bold=True)
    gold_text("-", a["SW4"], CY + 12.6, 3.4, 0.6, bold=True)
    gold_text("+", a["SW5"], CY + 12.6, 3.4, 0.6, bold=True)

    # §1's SUB rule as a supply: a box round SUB, fed only from the point FIELD's second throw
    # reaches, and two feeds out of it to positions 3 and 5. Nothing where the lever moves.
    xs, xf = a["SW3"], a["SW2"]
    BX, BR_, BT, BB, rr = xs - 10.0, xs + 10.0, CY - 9.0, CY + 15.0, 2.2
    for p, q in (((BX + rr, BT), (BR_ - rr, BT)), ((BR_, BT + rr), (BR_, BB - rr)),
                 ((BR_ - rr, BB), (BX + rr, BB)), ((BX, BB - rr), (BX, BT + rr))):
        gold_line(*p, *q)
    k = rr - rr * math.sqrt(0.5)
    for s, m, e in (((BX, BT + rr), (BX + k, BT + k), (BX + rr, BT)),
                    ((BR_ - rr, BT), (BR_ - k, BT + k), (BR_, BT + rr)),
                    ((BR_, BB - rr), (BR_ - k, BB - k), (BR_ - rr, BB)),
                    ((BX + rr, BB), (BX + k, BB - k), (BX, BB - rr))):
        gold_arc(s, m, e)
    gold_line(BX, CY + 8.2, xf, CY + 8.2)                 # enable, in from FIELD's second throw
    gold_line(xf, CY + 8.2, xf, CY + 6.6)                 # ends directly beneath the lever
    ytop, ybot = 2.0, CY + 19.0
    e3 = (ends[SUBLIVE[0]][0] + 1.0, ends[SUBLIVE[0]][1])
    e5 = (ends[SUBLIVE[1]][0] + 1.0, ends[SUBLIVE[1]][1])
    k3 = e3[0] + (e3[1] - ytop)                           # 45 deg into the label, as drawn by hand
    k5 = e5[0] + (ybot - e5[1])
    gold_line(xs, BT, xs, ytop)
    gold_line(xs, ytop, k3, ytop)
    gold_line(k3, ytop, *e3)
    gold_line(xs, BB, xs, ybot)
    gold_line(xs, ybot, k5, ybot)
    gold_line(k5, ybot, *e5)

    # the bodies behind the panel, for reference only
    G.append(("circle", "User.1", (cx, CY, 12.5, 0.12)))
    for r in ("SW2", "SW3", "SW4", "SW5"):
        G.append(("circle", "User.1", (a[r], CY, 12.0, 0.12)))
    text("BODY 25.00", cx, CY + 13.8, "User.1", 1.0, 0.15)
    # the connector's pin order, on the back above it
    jx, jy = L["P"]["J1"]
    legend = "1 +5V 2 GND 3 A6 4 A7 5 D7 6 D8"
    text(legend, jx - 9.4 - len(legend) * 0.8 * CHW / 2, H - 1.9, "B.SilkS", 0.8, 0.12, mirror=True)   # left of J1, clear of H4
    text(NAME, W - 30.0, 3.0, "B.SilkS", 1.0, 0.15, mirror=True)
    return G


# ============================================================================ routing
class _Part:
    def __init__(self, pins, value):
        self.pins, self.value = pins, value


# GND has no tracks: it is the back pour, and the pour needs its 0.4 mm clearance on both sides of
# its 0.25 mm minimum width to pass between two tracks - 1.05 mm. Routed at the rules' 0.2 mm, the
# study walled GND pads off in every alignment (the router runs nets side by side at the minimum).
# So the router keeps its copper TRK_CLR from every other net's - a track hugging a pad seals the
# pour as surely as two tracks do - except at J1, whose pins it approaches at PAD_CLR: A6 and A7
# run in the 2.3 mm channel between the pins and the retention tabs, side by side, by design.
TRK_CLR, PAD_CLR = 1.1, 0.3
PAIR_CLR = {frozenset(("A6", "A7")): 0.3}


def _router(B):
    """netroute.NetRouter with the clearances above."""
    import netroute as NR

    class PourRouter(NR.NetRouter):
        def _items(self, layer):
            out = []
            for n, pts, r, kind, obj in super()._items(layer):
                tight = kind == "pad" and obj.ref == "J1"
                out.append((n, pts, r - (TRK_CLR - PAD_CLR) if tight else r, kind, obj))
            return out

        def need(self, n1, n2):
            return PAIR_CLR.get(frozenset((n1, n2)), TRK_CLR)
    return PourRouter(B, turn45=6.0)


def model(L, clr=0.2):
    """A pcbkit board of the layout: the geometry the router and the checker work on. Back parts
    are loaded unmirrored because their library copies are already drawn on B.* layers."""
    import pcbkit as K
    B = K.Board(NAME, W, H, {r: _Part(PINS[r], VALUE[r]) for r in PINS}, [("HV", 0.6, 0.4, [])],   # no HV here; netroute wants the class
                default=("Default", clr, 0.25))
    for r, (x, y) in L["P"].items():
        B.place(r, FP[r], x, y)
    for x, y in HOLES:
        B.hole(x, y, 2.7)
        B.keepouts.append((x - 3.6, y - 3.6, x + 3.6, y + 3.6, "*"))   # the case's boss lands here
    # no track between two pins of the connector or two landing pads of a control: those gaps
    # are 1.0 mm, legal for a 0.25 track, and a solder bridge waiting for a hand iron. A track
    # still ends in its own pad through the pad's end (join() opens a net's own copper).
    jx, jy = L["P"]["J1"]
    for gx in (-4.0, -2.0, 0.0, 2.0, 4.0):                              # the five gaps between six pins
        B.keepouts.append((jx + gx - 0.5, jy - 4.6, jx + gx + 0.5, jy - 1.1, "*"))
    # the channel under the pins, between them and the retention tabs, is A6's and A7's: they come
    # in from the left and turn up into pins 3 and 4 from below, as on TS06-FASCIA
    B.keepouts.append((jx - 8.1, jy - 1.1, jx + 8.1, jy + 1.2, "*", {"A6", "A7"}))
    # (the minus button's gap carries D8, laid by hand in layout(): see there)
    for r in ("SW2", "SW3", "SW4", "SW5"):
        x, y = L["P"][r]
        B.keepouts.append((x - 0.5, y + LEV_PAD_DY - 0.75, x + 0.5, y + LEV_PAD_DY + 0.75, "*"))
    B.tracks = list(L["fixed"])
    return B


def route(L, verbose=True):
    import netroute as NR
    B = model(L, TRK_CLR)
    R = _router(B)
    R.fixed = set(L["fixed"])
    R.locked = set()
    R.dirmul = {ly: [1.0, 1.5, 1.0, 1.5, 1.0, 1.5, 1.0, 1.5] for ly in ("F.Cu", "B.Cu")}
    order = ["A6", "+5V", "A7", "D7", "D8"]
    N = NR.Negotiator(R, order, widths={n: 0.25 for n in order}, layers={n: ("B.Cu",) for n in order})
    failed = N.run(rounds=40, verbose=verbose)
    if not failed:
        R.polish(order, layers={n: ("B.Cu",) for n in order}, widths={n: 0.25 for n in order}, verbose=verbose)
    return [t for t in B.tracks if t not in R.fixed], failed, B


# ============================================================================ writing
def _load(fpname):
    return open(os.path.join(PRETTY, fpname + ".kicad_mod"), encoding="utf8").read()


def _place(ref, x, y):
    """A library footprint as a board footprint, the way tools/mkpcb.py writes them: back parts
    are authored on B.* layers, so they are moved to the back by layer name, never mirrored."""
    back = ref in BACK
    t = _load(FP[ref]).rstrip()
    assert t.startswith("(footprint") and t.endswith(")")
    t = t[:-1].rstrip()
    if back:
        for a_, b_ in (('(layer "F.Cu")', '(layer "B.Cu")'), ('"F.SilkS"', '"B.SilkS"'),
                       ('"F.Fab"', '"B.Fab"'), ('"F.CrtYd"', '"B.CrtYd"')):
            t = t.replace(a_, b_)
        t = t.replace("\n\t\t\t)\n\t\t)", "\n\t\t\t)\n\t\t\t(justify mirror)\n\t\t)")
    lay = '(layer "B.Cu")' if back else '(layer "F.Cu")'
    t = t.replace(lay, lay + '\n\t(uuid "%s")\n\t(at %s %s)' % (U("fp" + ref), f3(x), f3(y)), 1)
    t = t.replace('(property "Reference" "REF**"', '(property "Reference" "%s"' % ref, 1)
    if ref in REF_AT:                      # a reference that would land on a neighbour's pad
        t = re.sub(r'(\(property "Reference" "%s"\n\t\t)\(at [\d.-]+ [\d.-]+ 0\)' % ref,
                   lambda m: m.group(1) + "(at %s %s 0)" % (f3(REF_AT[ref][0]), f3(REF_AT[ref][1])), t, count=1)
    t = re.sub(r'\(property "Value" "[^"]*"', '(property "Value" "%s"' % VALUE[ref], t, count=1)
    nets = PINS[ref]

    def netify(m):
        num = m.group(1)
        if num not in nets:
            return m.group(0)
        n = nets[num]
        return re.sub(r'\(layers [^)]*\)', lambda q: q.group(0) + '\n\t\t(net %d "%s")' % (NI[n], n), m.group(0), count=1)
    t = re.sub(r'\(pad "(\d+)"[\s\S]*?\n\t\)', netify, t)
    k = [0]

    def reuuid(m):
        k[0] += 1
        return '(uuid "%s")' % U("%s.%d" % (ref, k[0]))
    head, body = t.split("\n", 1)
    body = re.sub(r'\(uuid "[^"]*"\)', reuuid, body)
    return head + "\n" + body + "\n)"


def write_pcb(L, G, tracks, path):
    out = []
    o = out.append
    o('(kicad_pcb\n\t(version %d)\n\t(generator "%s")\n\t(generator_version "%s")' % (VER, GEN, GENV))
    o('\t(general\n\t\t(thickness 2.0)\n\t\t(legacy_teardrops no)\n\t)\n\t(paper "A3")')
    o('\t(title_block\n\t\t(title "%s")\n\t\t(rev "A")\n\t\t(company "TERMINAL-06")\n'
      '\t\t(comment 1 "the fascia on the tube grid, alignment %s: %s")\n\t)' % (NAME, L["key"], L["a"]["title"].replace('"', "'")))
    o('\n'.join(['\t(layers', '\t\t(0 "F.Cu" signal)', '\t\t(2 "B.Cu" signal)',
                 '\t\t(9 "F.Adhes" user "F.Adhesive")', '\t\t(11 "B.Adhes" user "B.Adhesive")',
                 '\t\t(13 "F.Paste" user)', '\t\t(15 "B.Paste" user)',
                 '\t\t(5 "F.SilkS" user "F.Silkscreen")', '\t\t(7 "B.SilkS" user "B.Silkscreen")',
                 '\t\t(1 "F.Mask" user)', '\t\t(3 "B.Mask" user)',
                 '\t\t(17 "Dwgs.User" user "User.Drawings")', '\t\t(19 "Cmts.User" user "User.Comments")',
                 '\t\t(21 "Eco1.User" user "User.Eco1")', '\t\t(23 "Eco2.User" user "User.Eco2")',
                 '\t\t(25 "Edge.Cuts" user)', '\t\t(27 "Margin" user)',
                 '\t\t(31 "F.CrtYd" user "F.Courtyard")', '\t\t(29 "B.CrtYd" user "B.Courtyard")',
                 '\t\t(35 "F.Fab" user)', '\t\t(33 "B.Fab" user)',
                 '\t\t(39 "User.1" user "Keepouts")', '\t\t(41 "User.2" user)',
                 '\t\t(43 "User.3" user)', '\t\t(45 "User.4" user)', '\t)']))
    o('\t(setup\n\t\t(pad_to_mask_clearance 0)\n\t\t(allow_soldermask_bridges_in_footprints no)\n'
      '\t\t(tenting\n\t\t\t(front yes)\n\t\t\t(back yes)\n\t\t)\n\t)')
    for i, n in enumerate(NETS):
        o('\t(net %d "%s")' % (i, n))
    for ref in sorted(L["P"], key=lambda r: (re.sub(r"\d", "", r), int(re.sub(r"\D", "", r)))):
        o(_place(ref, *L["P"][ref]))
    for i, (hx, hy) in enumerate(HOLES):
        # column-0 like every other footprint here, which is the layout the checkers read
        o('(footprint "MountingHole_2.7mm"\n\t(version %d)\n\t(generator "%s")\n\t(generator_version "%s")\n'
          '\t(layer "F.Cu")\n\t(uuid "%s")\n\t(at %s %s)\n\t(descr "M2.5 clearance, non-plated")\n'
          '\t(property "Reference" "H%d"\n\t\t(at 0 -2.6 0)\n\t\t(layer "F.Fab")\n\t\t(hide yes)\n\t\t(uuid "%s")\n'
          '\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 0.8 0.8)\n\t\t\t\t(thickness 0.12)\n\t\t\t)\n\t\t)\n\t)\n'
          '\t(attr exclude_from_pos_files exclude_from_bom)\n'
          '\t(pad "" np_thru_hole circle\n\t\t(at 0 0)\n\t\t(size 2.7 2.7)\n\t\t(drill 2.7)\n'
          '\t\t(layers "F&B.Cu" "*.Mask")\n\t\t(uuid "%s")\n\t)\n\t(embedded_fonts no)\n)'
          % (VER, GEN, GENV, U("hole%d" % i), f3(hx), f3(hy), i + 1, U("holeref%d" % i), U("holepad%d" % i)))

    def gl(x1, y1, x2, y2, layer, w, tag):
        o('\t(gr_line\n\t\t(start %s %s)\n\t\t(end %s %s)\n\t\t(stroke\n\t\t\t(width %s)\n\t\t\t(type solid)\n\t\t)\n'
          '\t\t(layer "%s")\n\t\t(uuid "%s")\n\t)' % (f3(x1), f3(y1), f3(x2), f3(y2), f3(w), layer, U(tag)))

    def ga(s, m, e, layer, w, tag):
        o('\t(gr_arc\n\t\t(start %s %s)\n\t\t(mid %s %s)\n\t\t(end %s %s)\n\t\t(stroke\n\t\t\t(width %s)\n'
          '\t\t\t(type solid)\n\t\t)\n\t\t(layer "%s")\n\t\t(uuid "%s")\n\t)'
          % (f3(s[0]), f3(s[1]), f3(m[0]), f3(m[1]), f3(e[0]), f3(e[1]), f3(w), layer, U(tag)))
    # outline: TS06-FASCIA's, 1.5 mm corners
    k = CR - CR * math.sqrt(0.5)
    gl(CR, 0, W - CR, 0, "Edge.Cuts", 0.05, "e1")
    gl(W, CR, W, H - CR, "Edge.Cuts", 0.05, "e2")
    gl(W - CR, H, CR, H, "Edge.Cuts", 0.05, "e3")
    gl(0, H - CR, 0, CR, "Edge.Cuts", 0.05, "e4")
    ga((0, CR), (k, k), (CR, 0), "Edge.Cuts", 0.05, "a1")
    ga((W - CR, 0), (W - k, k), (W, CR), "Edge.Cuts", 0.05, "a2")
    ga((W, H - CR), (W - k, H - k), (W - CR, H), "Edge.Cuts", 0.05, "a3")
    ga((CR, H), (k, H - k), (0, H - CR), "Edge.Cuts", 0.05, "a4")
    for i, (kind, layer, d) in enumerate(G):
        tag = "g%d%s%s" % (i, kind, layer)
        if kind == "line":
            gl(*d[:4], layer, d[4], tag)
        elif kind == "arc":
            ga(d[0], d[1], d[2], layer, d[3], tag)
        elif kind == "circle":
            x, y, r, w = d
            o('\t(gr_circle\n\t\t(center %s %s)\n\t\t(end %s %s)\n\t\t(stroke\n\t\t\t(width %s)\n\t\t\t(type solid)\n'
              '\t\t)\n\t\t(fill no)\n\t\t(layer "%s")\n\t\t(uuid "%s")\n\t)' % (f3(x), f3(y), f3(x + r), f3(y), f3(w), layer, U(tag)))
        else:
            s, x, y, size, th, just, bold, mirror = d
            js = [j for j in (just, "mirror" if mirror else "") if j]
            o('\t(gr_text "%s"\n\t\t(at %s %s 0)\n\t\t(layer "%s")\n\t\t(uuid "%s")\n\t\t(effects\n\t\t\t(font\n'
              '\t\t\t\t(size %s %s)\n\t\t\t\t(thickness %s)%s\n\t\t\t)%s\n\t\t)\n\t)'
              % (s, f3(x), f3(y), layer, U(tag), f3(size), f3(size), f3(th),
                 "\n\t\t\t\t(bold yes)" if bold else "", ("\n\t\t\t(justify %s)" % " ".join(js)) if js else ""))
    for i, (net, ly, a_, b_, w) in enumerate(tracks):
        o('\t(segment\n\t\t(start %s %s)\n\t\t(end %s %s)\n\t\t(width %s)\n\t\t(layer "%s")\n\t\t(net %d)\n'
          '\t\t(uuid "%s")\n\t)' % (f3(a_[0]), f3(a_[1]), f3(b_[0]), f3(b_[1]), f3(w), ly, NI[net], U("seg%d" % i)))
    # GND: the back pour, as on TS06-FASCIA - thermal spokes to every GND pad
    o('\t(zone\n\t\t(net %d)\n\t\t(net_name "GND")\n\t\t(layer "B.Cu")\n\t\t(uuid "%s")\n\t\t(name "GND")\n'
      '\t\t(hatch edge 0.5)\n\t\t(connect_pads\n\t\t\t(clearance 0.4)\n\t\t)\n\t\t(min_thickness 0.25)\n'
      '\t\t(filled_areas_thickness no)\n\t\t(fill yes\n\t\t\t(thermal_gap 0.4)\n\t\t\t(thermal_bridge_width 0.5)\n'
      '\t\t\t(island_removal_mode 0)\n\t\t)\n\t\t(polygon\n\t\t\t(pts\n\t\t\t\t(xy 0.5 0.5)\n\t\t\t\t(xy %s 0.5)\n'
      '\t\t\t\t(xy %s %s)\n\t\t\t\t(xy 0.5 %s)\n\t\t\t)\n\t\t)\n\t)' % (NI["GND"], U("zone"), f3(W - 0.5), f3(W - 0.5), f3(H - 0.5), f3(H - 0.5)))
    text = "\n".join(out) + "\n\t(embedded_fonts no)\n)\n"
    assert "(via" not in text
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf8", newline="\n").write(text)


def write_project(path):
    """The .kicad_pro, fp-lib-table, sym-lib-table and the schematic: TS06-FASCIA's, renamed. The
    netlist is unchanged; the schematic names SW1's new footprint."""
    d = os.path.dirname(path)
    base = os.path.splitext(path)[0]
    pro = json.load(open(ORIG + ".kicad_pro", encoding="utf8"))
    pro["meta"]["filename"] = os.path.basename(base) + ".kicad_pro"
    open(base + ".kicad_pro", "w", encoding="utf8", newline="\n").write(json.dumps(pro, indent=2) + "\n")
    for f in ("fp-lib-table", "sym-lib-table"):
        open(os.path.join(d, f), "w", encoding="utf8", newline="\n").write(
            open(os.path.join(os.path.dirname(ORIG), f), encoding="utf8").read())
    sch = open(ORIG + ".kicad_sch", encoding="utf8").read()
    sch = sch.replace('(project "TS06-FASCIA"', '(project "%s"' % NAME)
    sch = sch.replace('(title "TS06-FASCIA - control panel and product face")',
                      '(title "%s - control panel and product face, on the tube grid")' % NAME)
    sch = sch.replace('"TS06:TS06_Rotary_SR25_PanelMount"', '"TS06:%s"' % FP["SW1"])
    open(base + ".kicad_sch", "w", encoding="utf8", newline="\n").write(sch)


def save_routes(tracks, key):
    with open(ROUTES, "w") as fh:
        json.dump({"alignment": key, "tracks": [[n, ly, [list(a_), list(b_)], w] for n, ly, a_, b_, w in tracks]}, fh, indent=0)


def load_routes(key):
    d = json.load(open(ROUTES))
    assert d["alignment"] == key, "saved routes are for alignment %s; run with --route" % d["alignment"]
    return [(n, ly, tuple(a_), tuple(b_), w) for n, ly, (a_, b_), w in d["tracks"]]


# ============================================================================ the composite
def nearest(X):
    """The tube centre nearest a world X, and the offset from it."""
    cands = dict(T)
    cands["hours pair"] = HOURS
    nm = min(cands, key=lambda k: abs(cands[k] - X))
    return nm.replace("IN15B", "ИН-15Б").replace("IN15A", "ИН-15А"), X - cands[nm]


def composite(pcb, png, title, ctrl, x0=0.0, cy=CY, bw=W, note=""):
    """Front elevation in world X and Y: the tube glass above the fascia as the case holds it
    (top edge at Y 39, raked 12 deg, so 40 mm of board shows as 39.1), the fascia's own front
    face as tools/render.py draws it, the control bodies behind it dashed, and a centre line
    from every tube down through the panel. ctrl: {SW1..SW5: world X}; x0: the board's world X;
    cy: its control row; bw: its width."""
    import mkpcb_disp as DSP
    subprocess.run([sys.executable, os.path.join(HERE, "render.py"), pcb, png + ".tmp.svg"],
                   capture_output=True, text=True, check=True)
    src = open(png + ".tmp.svg", encoding="utf8").read()
    os.remove(png + ".tmp.svg")
    i = src.find('<g transform="translate(')
    depth, j = 0, i
    while True:
        a_, b_ = src.find("<g", j), src.find("</g>", j)
        if a_ != -1 and a_ < b_:
            depth += 1
            j = a_ + 2
        else:
            depth -= 1
            j = b_ + 4
            if depth == 0:
                break
    front = src[i:j]
    front = re.sub(r'^<g transform="translate\([^)]*\) ?">', "", front)[:-4]
    Ytop, mx = 92.0, 10.0
    c12 = math.cos(math.radians(12))
    SY = lambda Y: Ytop - Y
    top = DSP.TOP
    y12, y17 = top - DSP.Y12, top - DSP.Y17
    s = []
    add = s.append
    Hs = Ytop + 16
    add('<rect x="-%g" y="0" width="%g" height="%g" fill="#15181a"/>' % (mx, W + 2 * mx, Hs))
    # case inside walls
    for X in (-0.5, W + 0.5):
        add('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#5a6068" stroke-width="0.25" stroke-dasharray="1.2,0.8"/>'
            % (X, SY(80), X, SY(-2)))
    # TS06-DISP
    add('<rect x="0" y="%g" width="%g" height="44" fill="#1f2326" stroke="#3b4045" stroke-width="0.2"/>' % (SY(top), W))
    # tube centre lines through everything
    for nm, X in T.items():
        add('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#f25610" stroke-width="0.18" stroke-dasharray="0.8,0.6" opacity="0.8"/>'
            % (X, SY(top + 2), X, SY(-1.5)))
    # the fascia as the customer sees it, projected
    add('<g transform="translate(%g,%g) scale(1,%g)">%s</g>' % (x0, SY(39.0), c12, front))
    # the other width, for comparison
    ox, ow = (7.7, 176.0) if bw > 180 else (0.0, W)
    add('<rect x="%g" y="%g" width="%g" height="%g" fill="none" stroke="#9aa0a6" stroke-width="0.2" '
        'stroke-dasharray="0.6,0.6"/>' % (ox, SY(39.0), ow, 40 * c12))
    # bodies behind the panel (dashed), the case model's sizes
    for r in ("SW1", "SW2", "SW3", "SW4", "SW5"):
        X, Y = ctrl[r], 39.0 - cy * c12
        if r == "SW1":
            add('<ellipse cx="%g" cy="%g" rx="12.5" ry="%g" fill="none" stroke="#7fb0ff" stroke-width="0.2" '
                'stroke-dasharray="0.8,0.5"/>' % (X, SY(Y), 12.5 * c12))
        else:
            w_, h_ = (10.43, 11.92) if r in ("SW2", "SW3") else (13.75, 16.91)
            add('<rect x="%g" y="%g" width="%g" height="%g" fill="none" stroke="#7fb0ff" stroke-width="0.2" '
                'stroke-dasharray="0.8,0.5"/>' % (X - w_ / 2, SY(Y) - h_ / 2 * c12, w_, h_ * c12))
    # tubes: ИН-12 and ИН-15 glass Ø19.47, ИН-17 faces 14, the colon lamps
    glass = "fill='#ffb45a' fill-opacity='0.10' stroke='#ffb45a' stroke-width='0.3'"
    for X in DSP.IN12_X + DSP.IN15_X:
        add("<circle cx='%g' cy='%g' r='%g' %s/>" % (X, SY(y12), 19.47 / 2, glass))
    for X in DSP.IN17_X:
        add("<circle cx='%g' cy='%g' r='7' %s/>" % (X, SY(y17), glass))
    for y in DSP.COLON_Y:
        add("<circle cx='%g' cy='%g' r='%g' %s/>" % (DSP.COLON_X, SY(top - y), 6.97 / 2, glass))
    for X in DSP.IN12_X + DSP.IN15_X:
        add("<circle cx='%g' cy='%g' r='0.5' fill='#ffb45a'/>" % (X, SY(y12)))
    for X in DSP.IN17_X:
        add("<circle cx='%g' cy='%g' r='0.5' fill='#ffb45a'/>" % (X, SY(y17)))
    lab = "font-family='DejaVu Sans' font-size='2.4' fill='#c9c6bf'"
    small = "font-family='DejaVu Sans' font-size='2.2' fill='#8a8f96'"
    for i, (nm, X) in enumerate(T.items()):
        add("<text x='%g' y='%g' text-anchor='middle' %s>%s %.3f</text>" % (X, SY(top + 2.6 + 3.2 * (i % 2)), lab,
                                                                          nm.replace("IN15B", "ИН-15Б").replace("IN15A", "ИН-15А"), X))
    for r in ("SW1", "SW2", "SW3", "SW4", "SW5"):
        X = ctrl[r]
        nm, off = nearest(X)
        add("<text x='%g' y='%g' text-anchor='middle' %s>%s %.3f</text>" % (X, SY(-4.0), lab, r, X))
        rel = ("under %s" % nm) if abs(off) < 0.005 else ("%s %+.2f" % (nm, off))
        add("<text x='%g' y='%g' text-anchor='middle' %s>%s</text>" % (X, SY(-6.6), small, rel))
    add("<text x='0' y='%g' font-family='DejaVu Sans' font-size='3.2' fill='#e8e6e0'>%s</text>" % (SY(top + 9.4), title))
    add("<text x='0' y='%g' %s>World X = TS06-DISP x. Glass: ИН-12 / ИН-15 Ø19.47, ИН-17 face 14, ИНС-1 Ø6.97. "
        "Fascia %g x 40 from X %g, raked 12° (39.1 seen), top edge at the sill, Y 39.</text>" % (SY(-10.0), small, bw, x0))
    add("<text x='0' y='%g' %s>Dashed grey: the board at the other width. Dashed blue: the bodies behind the panel. "
        "Dashed walls: the case inside, 192.4. %s</text>" % (SY(-13.0), small, note))
    out = ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="-%g 0 %g %g">%s</svg>'
           % ((W + 2 * mx) * 8, Hs * 8, mx, W + 2 * mx, Hs, "\n".join(s)))
    open(png + ".svg", "w", encoding="utf8").write(out)
    subprocess.run(["rsvg-convert", png + ".svg", "-o", png], check=True)
    os.remove(png + ".svg")


def composite_of(L, pcb, png, note=""):
    composite(pcb, png, "Alignment %s — %s" % (L["key"], L["a"]["title"]),
              {r: L["a"][r] for r in ("SW1", "SW2", "SW3", "SW4", "SW5")}, note=note)


def composite_baseline(png):
    """TS06-FASCIA as committed, centred at X0 7.7 as the case model has it: the reference."""
    import sexp as S
    t = S.parse(open(ORIG + ".kicad_pcb", encoding="utf8").read())
    ctrl = {}
    for fp in S.find_all(t, "footprint"):
        ref = [S.unq(p[2]) for p in S.find_all(fp, "property") if S.unq(p[1]) == "Reference"]
        if ref and ref[0] in ("SW1", "SW2", "SW3", "SW4", "SW5"):
            at = S.find(fp, "at")
            ctrl[ref[0]] = round(float(at[1]) + 7.7, 3)
            cy = float(at[2])
    composite(ORIG + ".kicad_pcb", png, "Reference — TS06-FASCIA as committed, centred (X0 7.7)", ctrl, x0=7.7, cy=cy,
              bw=176.0, note="Not this variant: the plain centring it is judged against.")


# ============================================================================ main
def build(key, path, reroute, verbose=True):
    write_rotary_footprint()
    L = layout(key)
    G = artwork(L)
    if reroute:
        tracks, failed, _ = route(L, verbose)
        if failed:
            print("unrouted:", " ".join(failed))
    else:
        tracks, failed = load_routes(key), []
    write_pcb(L, G, list(L["fixed"]) + tracks, path)
    return L, tracks, failed


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    if "--study" in sys.argv:
        out = sys.argv[sys.argv.index("--study") + 1] if len(sys.argv) > sys.argv.index("--study") + 1 else os.path.join(OUTDIR, "study")
        os.makedirs(out, exist_ok=True)
        os.makedirs(OUTDIR, exist_ok=True)
        keys = [k for k in sys.argv if k in ALIGN] or list(ALIGN)
        for key in keys:
            p = os.path.join(out, "%s-%s.kicad_pcb" % (NAME, key))
            if "--front" in sys.argv:                  # the composites only: the front does not depend on routing
                write_rotary_footprint()
                L = layout(key)
                write_pcb(L, artwork(L), list(L["fixed"]), p)
            else:
                L, tracks, failed = build(key, p, True, verbose=False)
                print("alignment %s: %d routed tracks + %d laid, unrouted: %s" % (key, len(tracks), len(L["fixed"]), failed or "none"))
            composite_of(L, p, os.path.join(OUTDIR, "composite-%s.png" % key))
        composite_baseline(os.path.join(OUTDIR, "composite-0-centred.png"))
        sys.exit(0)
    path = os.path.join(OUTDIR, NAME + ".kicad_pcb")
    reroute = "--route" in sys.argv or not os.path.exists(ROUTES)
    L, tracks, failed = build(CHOSEN, path, reroute)
    if reroute and not failed:
        save_routes(tracks, CHOSEN)
    write_project(path)
    composite_of(L, path, os.path.join(OUTDIR, "composite-%s.png" % CHOSEN), "Built.")
    print("wrote %s: alignment %s, %d tracks (%d laid by hand), 0 vias" % (os.path.relpath(path, ROOT), CHOSEN,
                                                                         len(tracks) + len(L["fixed"]), len(L["fixed"])))
