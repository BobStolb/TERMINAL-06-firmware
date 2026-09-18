#!/usr/bin/env python3
"""Generate TS06-MAIN, the whole clock on one board - either build.

    python3 tools/mkpcb_main.py                # PCB/TS06-MAIN/TS06-MAIN.kicad_pcb, placement only
    python3 tools/mkpcb_main.py --tht          # PCB/TS06-MAIN-THT/..., placement only
    python3 tools/mkpcb_main.py --route        # ... and route (long: run it in the background, watch the log)

The netlist is tools/ts06main.py, the same file tools/mksch_main.py draws, so board and
schematic cannot disagree about what is connected; tools/checkmatch.py proves it anyway.

THE BOARD IS VERTICAL, in the plane the inherited tube board occupied, tubes on the front,
everything else on the back - exactly as TS06-SEC. World coordinates are the reviewed
FreeCAD assembly's (3d/Clock.FCStd): X across, Y up, the inherited tube board's bottom
edge at world Y 40.10 and its tube centres at Y 60.166 (its own drill file: 20.066 above
its edge). Board local (x, y) = (world X, TOP - world Y) with TOP the world Y of the top
edge, so the ИН-12 pitch 23.36 / 27.42 / 23.36 mm, the colon gap and every other measured
position are carried over untouched. The board runs from world Y 94 down to 9: the extra
height sits BELOW the tubes, behind the fascia, where the through-hole build needs it and
nothing shows.

THREE BANDS on the back, top to bottom:
  * the logic band above the tubes: the Nano across the top right with its USB out through
    the right edge, the decoder, the ten-line cathode spine K0..K9 running the length of
    the digit row and fanning down into each ring, the two ИН-17 anode switches, and the
    185 V converter with its control at the top left - its rail drops between the H1 and
    M10 rings to the trunk below;
  * the tube band: the eight pin fields; inside each ИН-12 ring on the back its anode
    resistor and bleed pair; the eighteen ИН-15 cathode switches inside and between the
    ИН-15 rings, as SEC did;
  * the power band below the tubes: the four ИН-12 anode switches beside their backlight
    LEDs, the 12 V entry at the left edge, the colon, the fascia connector at the bottom
    edge, the RTC, the two expanders under the ИН-15s with the base resistors above them.

ROUTING (tools/pcbroute.py) goes in three stages, with SEC's clearance classes - 0.6 mm
wherever a high-voltage net is involved - and in the order a board is routed by hand:
  1. all the high voltage, the 185 V trunk included, laid first and never moved;
  2. GND, a tree while there is still room, which the pour on each face later fills around;
  3. everything else, negotiated at once in the manner of PathFinder;
  4. one more try, alone and against the finished board, at whatever stage 3 had to drop.
Only copper that cannot be negotiated belongs in stage 1. Putting the cathode spine there too
was tried and is worse - laid net after net it fences the rest in, and six nets were dropped
instead of three. Negotiation beats ordering, which is TS06-SEC's lesson and still holds.
SEC negotiated GND and the trunk along with the signals. Neither carries over to a board this
size, and both were tried here first (18.09.26). GND is 74 of this board's 483 pads: a tree
that large crosses nearly every other net, so almost every net gets reported as overlapping
GND rather than its real neighbour and nothing converges - two runs stuck at ~80 of 98 nets.
Leaving GND to a pour with stubs is worse, because the signal copper cuts the pour into
islands: one region reached 37 of 74 pads and 66 stubs could not close the rest. Leaving it
until after the signals is better but still short, the board being full by then: 21 pads
unreachable and GND in 11 pieces. The trunk has 14 pads and a wide halo everywhere, and
negotiated it defeated the through-hole build outright, coming out in 14 pieces and taking
seven other nets with it.

Regenerate with:  python3 tools/mkpcb_main.py [--tht] [--route]
"""
import math, os, re, sys, time, uuid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ts06main as N

VER, GEN, GENV = 20260206, "pcbnew", "10.0"
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PRETTY = os.path.join(ROOT, "PCB", "lib", "TS06.pretty")
BUILD = "tht" if "--tht" in sys.argv else "smd"
BOARD = "TS06-MAIN-THT" if BUILD == "tht" else "TS06-MAIN"
OUT = os.path.join(ROOT, "PCB", BOARD, BOARD + ".kicad_pcb")
NS = uuid.UUID("5ec06000-7506-4000-8000-0000000000a1" if BUILD == "smd" else "5ec06000-7506-4000-8000-0000000000a2")
ROUTE = "--route" in sys.argv

# Routing parameters in one place, overridable from the environment, so a sweep can try others
# without editing this file and every log records what it ran with. WHY: the first routed board
# was steered by one number - nets left unrouted - and reached zero while its ground pour filled
# as 292 islands and it carried 476 vias (18.09.26). tools/audit.py --quality scores the rest.
def _p(name, default, cast=float):
    v = os.environ.get("TS06_" + name.upper())
    return cast(v) if v not in (None, "") else default

RP = dict(via_cost=_p("via_cost", 900, int),   # a via, against 10 for a 0.1 mm step
          price=_p("price", 60, int),          # first-round cost of sharing a cell
          rise=_p("rise", 1.6),                # how fast that price climbs
          rounds=_p("rounds", 60, int),
          turn=_p("turn", 15, int),            # cost of a change of direction
          bias=_p("bias", 8, int),             # extra cost of a step across the layer grain
          decay=_p("decay", 0.9),              # how fast a history scar fades, 1.0 = never
          tighten=_p("tighten", 2, int),       # passes of rip-up-and-reroute for length
          relax=_p("relax", 4, int),           # rounds of failure before a net is let off the grain
          bundle=_p("bundle", 0, int),         # cost of a step away from a net's own bus
          compact=_p("compact", 0, int))       # cost of a step away from any other net's copper
if os.environ.get("TS06_OUT"):
    OUT = os.environ["TS06_OUT"]

W, H = 176.0, 96.0                          # the fascia's width; the height the through-hole build needs
TOP = 100.0                                 # world Y of the top edge; the bottom edge is at world Y 4


def local(wx, wy):
    return round(wx, 4), round(TOP - wy, 4)


IN12_WY = 40.10 + 20.066                    # the inherited board's real tube height, world Y
IN12_X = [13.21, 36.57, 63.99, 87.37]
IN17_X, IN17_WY = [104.605, 117.605], IN12_WY - 5.375
IN15_X = [135.0, 156.0]
COLON_X = 50.535                            # the lamp lead column (FreeCAD, via mkpcb_colon.py)
COLON_WY = [66.5, 52.5]                     # upper and lower lamp centres (FreeCAD INS1 / INS001)
LED_WY = IN12_WY - 17.67                    # backlight row: the inherited board had it 16.01 below the
                                            # tube centres; 17.67 keeps the 3 mm LED body clear of the glass courtyard
LED17_WY = IN17_WY - 13.3                   # SEC had 12.4; a little lower for the same reason

# ---------------------------------------------------------------- footprints
FP_TXT, FP_ENV = {}, {}


def fp_text(name):
    if name not in FP_TXT:
        FP_TXT[name] = open(os.path.join(PRETTY, name + ".kicad_mod"), encoding="utf8").read().rstrip()
    return FP_TXT[name]


def envelope(name):
    """Courtyard bounding box of a footprint, in its own coordinates (pads if it has none)."""
    if name in FP_ENV:
        return FP_ENV[name]
    t = fp_text(name)
    xs, ys = [], []
    for m in re.finditer(r'\(fp_line\n\t\t\(start ([-\d.]+) ([-\d.]+)\)\n\t\t\(end ([-\d.]+) ([-\d.]+)\)[\s\S]*?\(layer "[FB]\.CrtYd"\)', t):
        xs += [float(m.group(1)), float(m.group(3))]
        ys += [float(m.group(2)), float(m.group(4))]
    for m in re.finditer(r'\(fp_circle\n\t\t\(center ([-\d.]+) ([-\d.]+)\)\n\t\t\(end ([-\d.]+) ([-\d.]+)\)[\s\S]*?\(layer "[FB]\.CrtYd"\)', t):
        cx, cy, r = float(m.group(1)), float(m.group(2)), abs(float(m.group(3)) - float(m.group(1)))
        xs += [cx - r, cx + r]
        ys += [cy - r, cy + r]
    if not xs:
        for m in re.finditer(r'\(pad "[^"]*" \w+ \w+\n\t\t\(at ([-\d.]+) ([-\d.]+)\)\n\t\t\(size ([\d.]+) ([\d.]+)\)', t):
            x, y, w, h = map(float, m.groups())
            xs += [x - w / 2 - 0.25, x + w / 2 + 0.25]
            ys += [y - h / 2 - 0.25, y + h / 2 + 0.25]
    FP_ENV[name] = (min(xs), min(ys), max(xs), max(ys))
    return FP_ENV[name]


def variant(base, rot):
    return base if rot == 0 else f"{base}_R{rot}"


# ---------------------------------------------------------------- placement
PARTS = {p.ref: p for p in N.parts(BUILD)}
PLACED = {}                                 # ref -> (footprint, x, y)
GAP = 0.6                                   # courtyard to courtyard; courtyards already clear their pads, so bare pads of different parts stay > 0.8 apart
SMALL = {"R", "R_HV", "R_PWR", "C", "C_BIG", "CP", "F", "D_HV", "D_IN"}


def put(ref, x, y, rot=0):
    p = PARTS[ref]
    fp = variant(p.fp(BUILD), rot)
    assert os.path.exists(os.path.join(PRETTY, fp + ".kicad_mod")), (ref, fp)
    PLACED[ref] = (fp, round(x, 3), round(y, 3))


class Region:
    """Row packer over one or more rectangles: parts go left to right, rows top to bottom,
    then on into the next rectangle. rot is the default footprint variant; small two-pin
    parts are stood upright (90) unless told otherwise."""

    def __init__(self, name, rects, rot=0, upright=True):
        self.name, self.rects, self.rot, self.upright = name, [tuple(r) for r in rects], rot, upright
        self.i, self.over = 0, []
        self.x, self.y, self.rowh = self.rects[0][0], self.rects[0][1], 0.0

    def size(self, ref, rot):
        ex0, ey0, ex1, ey1 = envelope(variant(PARTS[ref].fp(BUILD), rot))
        return ex1 - ex0 + GAP, ey1 - ey0 + GAP, ex0, ey0

    def rot_for(self, ref, rot):
        if rot is not None:
            return rot
        return 90 if (self.upright and PARTS[ref].kind in SMALL) else self.rot

    def add(self, ref, rot=None):
        r = self.rot_for(ref, rot)
        w, h, ex0, ey0 = self.size(ref, r)
        while True:
            x0, y0, x1, y1 = self.rects[self.i]
            if self.x + w <= x1 + 1e-6 and self.y + h <= y1 + 1e-6:
                break
            if self.x > x0 + 1e-6 and self.y + self.rowh + h <= y1 + 1e-6:      # next row
                self.x, self.y, self.rowh = x0, self.y + self.rowh, 0.0
                continue
            if self.i + 1 < len(self.rects):                                    # next rectangle
                self.i += 1
                self.x, self.y, self.rowh = self.rects[self.i][0], self.rects[self.i][1], 0.0
                continue
            self.over.append(ref)
            break
        put(ref, self.x + GAP / 2 - ex0, self.y + GAP / 2 - ey0, r)
        self.x += w
        self.rowh = max(self.rowh, h)

    def fits(self, ref, rot=None):
        r = self.rot_for(ref, rot)
        w, h, _, _ = self.size(ref, r)
        for j in range(self.i, len(self.rects)):
            x0, y0, x1, y1 = self.rects[j]
            x, y, rowh = (self.x, self.y, self.rowh) if j == self.i else (x0, y0, 0.0)
            if x + w <= x1 + 1e-6 and y + h <= y1 + 1e-6:
                return True
            if y + rowh + h <= y1 + 1e-6:
                return True
        return False


# ---- the tubes, lamps and LEDs on the front, at the reviewed coordinates
for i, x in enumerate(IN12_X):
    put(f"V{i + 1}", *local(x, IN12_WY))
for i, x in enumerate(IN17_X):
    put(f"V{i + 5}", *local(x, IN17_WY))
put("V9", *local(IN15_X[0], IN12_WY))
put("V10", *local(IN15_X[1], IN12_WY))
put("V7", *local(COLON_X, COLON_WY[0]))
put("V8", *local(COLON_X, COLON_WY[1]))
LED_X = IN12_X + IN17_X + IN15_X
for i, x in enumerate(LED_X):
    put(f"HL{i + 1}", *local(x, LED17_WY if 4 <= i < 6 else LED_WY))
put("HL9", *local((IN15_X[0] + IN15_X[1]) / 2, LED_WY))

THT = BUILD == "tht"
CY12 = local(0, IN12_WY)[1]                 # ИН-12 / ИН-15 centre line
CY17 = local(0, IN17_WY)[1]
RING_TOP, RING_BOT = CY12 - 10.2, CY12 + 10.2    # the stadium's end pads reach 8.99 + a 1.0 mm pad radius
LED_Y = local(0, LED_WY)[1]
BAND_TOP = (2.8, RING_TOP - 0.6)            # the logic band, y range
BAND_BOT = (LED_Y + 2.8, H - 3.0)           # the power band: below the LED pads
TX = {nm: local(x, 0)[0] for nm, x in zip(N.TUBES, IN12_X + IN17_X)}
R = {}
if THT:
    SMALL.discard("C_BIG")                  # 5 mm-pitch discs lie flat in the through-hole build


def region(name, rects, refs=(), rot=0, upright=True):
    reg = Region(name, rects, rot, upright)
    for ref in refs:
        if ref in PARTS:
            reg.add(ref)
    R[name] = reg
    return reg


# ---- the logic band: Nano at the top left with its USB 2.4 mm proud of the left edge, the
# converter next to it, the two ИН-17 anode switches above their tubes, the AM/PM small parts
# above the ИН-15 rings
put("U1", 21.98, 14.0, 270)
reg = region("conv", [(49.5, BAND_TOP[0], 99.3 if THT else 96.0, BAND_TOP[1])], ["L1", "VT21" if not THT else None, "C7"])
if THT:
    reg.add("VT21", 90)                     # TO-220 lying flat, its body along the band
reg.add("U11", 90 if THT else 0)
reg.add("VD1", 0)
for ref in ("C12", "R67", "R68", "R60", "R61"):
    reg.add(ref)
for i, nm in enumerate(["S10", "S1"]):     # DIP-4s are narrower and sit further right, so the THT converter row fits
    x0 = (99.6 + 11.0 * i) if THT else (96.6 + 13.6 * i)
    region(f"opto_{nm}", [(x0, BAND_TOP[0], x0 + (10.9 if THT else 13.4), BAND_TOP[1])],
           [f"U{9 + i}", f"R{25 + i}", f"R{41 + 2 * i}", f"R{42 + 2 * i}"])
# ---- AM/PM: EACH EXPANDER SITS WITH ITS OWN TUBE'S CHANNELS, U3 and ИН-15Б above the rings,
# U4 and ИН-15А below them. The first layout put every switch and base resistor in one strip
# above the rings while both expanders sat below, so all eighteen channels crossed the tube
# band twice - measured as the board's worst congestion on 18.09.26 and, with the coin cell
# below, the reason the negotiation could not place about a dozen nets. Split this way each
# channel's three parts and its expander share a band, and only the cathode run enters the
# ring. Some switches sit inside the ring itself, clear of the Ø5 pip hole and 0.6 mm from the
# ring's own pads: four SOT-23s at the corners, or two TO-92s above and below the hole. That is
# what TS06-SEC does, and it earns its place - each collector reaches the pad beside it instead
# of crossing the ring's edge, which is the one boundary every other net has to cross too.
# MOVING THEM ALL OUT WAS TRIED AND IS FAR WORSE. The interior is a pocket, so a switch in there
# does strand the odd base or emitter - three pins on the first board that routed. But put the
# switches outside and their eighteen collectors have to come back IN through the ring's edge,
# each with a 0.6 mm high-voltage halo, and they choke the ground the signals need: the
# negotiation went from 3 nets unplaced to 24 (18.09.26). Three stranded pins is the cheaper
# defect by a wide margin, and stage 4 clears most of them.
# Taking even three of them out - the ones whose base or emitter was stranded - costs more than
# it saves, for the same reason as taking them all out: 3 nets unplaced became 13 (18.09.26).
# The ring keeps its full set and the few stranded pins are the price.
chan = [(vt, r) for vt, r, *_ in N.CH]
corners = ((0, -5.5), (0, 5.5)) if THT else ((-2.15, -4.7), (2.15, -4.7), (-2.15, 4.7), (2.15, 4.7))
for tube_x, first in zip(IN15_X, (0, 8)):
    cx, cy = local(tube_x, IN12_WY)
    for j, (dx, dy) in enumerate(corners):
        put(chan[first + j][0], cx + dx, cy + dy, 0)
for rects, exp, cap, anode_r, pullup, group in (
        ([(124.5, BAND_TOP[0], W - 3.0, BAND_TOP[1]),          # clear of the seconds opto at 123.6
          (163.5, RING_TOP, W - 3.0, RING_BOT),                # the strip right of the PM ring
          (142.3, RING_TOP, 148.7, RING_BOT)],                 # and the gap between the two rings
         "U3", "C1", "R56", "R54", chan[:8]),
        ([(126.0, BAND_BOT[0], W - 3.0, H - 3.0)]
         + ([(97.0, 74.0, 124.0, H - 3.0)] if THT else []),    # the through-hole parts need more room;
         "U4", "C2", "R57", "R55", chan[8:])):                 # in the SMD build the coin cell is there
    reg = region("ampm_" + exp, rects)
    reg.add(exp, 90)                        # the expander first: it is much the biggest part here
    if THT:
        reg.add(cap)                        # its decoupling beside it, not at the end of the row
    # WHERE THE BASE RESISTOR GOES depends on how big the parts are, and the two builds differ.
    # Through-hole: each resistor goes next to its own transistor. Laid in separate rows the two
    # ends of a base net end up rows apart, and with a TO-92 and an axial resistor at each end
    # seven of those nets could not be routed at all (18.09.26).
    # Surface-mount: the transistors keep one row and the resistors another. The parts are small
    # enough that a base net crosses one row either way, and a contiguous block of resistors
    # sits close to the expander that drives all eighteen of them - pairing them instead spread
    # those eighteen outputs over the whole block and cost seven more unrouted nets than it saved.
    inring = [g for g in group if g[0] in PLACED]      # already placed inside the tube ring
    for vt, r in group:
        if vt not in PLACED:
            reg.add(vt, 90 if THT else 0)
        if THT:
            reg.add(r)
    if not THT:
        # The resistors of the in-ring transistors go FIRST, at the end of the row nearest the
        # ring. Left in channel order, R2 landed 30 mm from VT2 and its base net was the last
        # thing on the board that would not route (18.09.26).
        for vt, r in inring + [g for g in group if g not in inring]:
            reg.add(r)
    for ref in ((anode_r, pullup) if THT else (cap, anode_r, pullup)):
        reg.add(ref)
    # NOTE how finely balanced this block is. Moving the decoupling cap from the end of the row
    # to just after the expander shifts every part after it by one slot, and on the surface-mount
    # build that alone took +5V from whole to 29 pieces (18.09.26). Change the order here only
    # with a routing run to show for it.
# ---- each ИН-12 ring: the bleed pair inside it on the back (upright at x +3.15, y +-3.8: 0.6 mm
# from the ring's own pads and clear of the Ø5 pip hole), the anode resistor just below it
for i, nm in enumerate(["H10", "H1", "M10", "M1"]):
    cx, cy = local(IN12_X[i], IN12_WY)
    put(f"R{33 + 2 * i}", cx + 3.15, cy - 3.8, 90)
    put(f"R{34 + 2 * i}", cx + 3.15, cy + 3.8, 90)
    put(f"R{27 + i}", cx + 2.5, RING_BOT + 2.6, 0)
# ИН-17 anode resistors beside S1, in the gap before the AM ring
put("R31", 123.6, CY17 - 5.0, 90)
put("R32", 123.6, CY17 + 5.0, 90)
# ---- backlight resistors beside their LEDs
for i in range(8):
    lx, ly = PLACED[f"HL{i + 1}"][1:]
    put(f"R{45 + i}", lx + 4.6, ly, 90)
put("R53", PLACED["HL9"][1] + 4.6, PLACED["HL9"][2], 90)
# ---- the power band
put("XS1", 11.0, 74.0, 180)                 # jack at the left edge, mouth out through x = 0; its break-contact pad sits above the body
for i, nm in enumerate(["H10", "H1", "M10", "M1"]):   # ИН-12 anode switches right under their LEDs
    put(f"U{5 + i}", TX[nm], BAND_BOT[0] + 3.2, 0)
    put(f"R{21 + i}", TX[nm] + (9.0 if i % 2 == 0 else -9.0), BAND_BOT[0] + 3.0, 90)
reg = region("entry", [(17.5, BAND_BOT[0] + 7.0, 46.0, H - 3.0)], ["F1", "C8", "U14"])
reg.add("VD2", 0)
for ref in ("C9", "C10", "C11", "C3"):
    reg.add(ref)
region("colon", [(46.5, BAND_BOT[0], 57.0, H - 3.0)], ["R58", "R59", "VT1", "R1", "VT20", "R20", "C5", "C6", "C13", "C14"])
# the rail's control loop - comparator, reference, divider, trimmer - under the M10/M1 switches
region("mid", [(57.5, BAND_BOT[0] + 6.7, 85.0, 84.3), (80.5, BAND_BOT[0], 85.0, BAND_BOT[0] + 6.4)],
       ["U12", "RP1", "R69", "R70", "R65", "R66", "R71", "R62", "R63", "R64"])
put("J1", 68.0, H - 6.5, 0)                 # fascia cable at the bottom edge, housing toward the edge
put("U2", 91.0, 77.5, 0)                    # decoder, upright, below the M1 switch
put("C4", 84.0, 87.5, 90)                   # its decoupling, beside its bottom end
if THT:
    put("U13", 89.0, 92.5, 90)              # the DS3231 mini module's header, lying along the bottom edge
else:
    # The CR2032 holder's negative contact is a single Ø17.8 mm land - a wall on the back face
    # wherever it stands. It went in the middle of the power band at first, where it covered a
    # whole 16 mm tile and blocked every corridor crossing it; here it is against the bottom
    # edge, below the decoder and left of the AM/PM block, where nothing has to get past.
    region("rtc", [(97.0, BAND_BOT[0], 123.0, 74.0)], ["U13", "C15"])
    put("BT1", 110.0, 84.0, 0)

missing = [r for r in PARTS if r not in PLACED]
assert not missing, f"not placed: {missing}"
for nm, reg in R.items():
    if reg.over:
        print(f"  REGION {nm} overflows with {reg.over}", file=sys.stderr)

# Mounting holes go where BOTH builds have room: searched over a half-millimetre grid against
# every pad, track and via of each routed board, then spread out. The first guesses sat inside
# the AM/PM block, and they were the whole of KiCad's hole-clearance and solder-mask-bridge
# complaints (18.09.26). No case exists yet, so the case follows these rather than the reverse.
HOLES = [(4.0, 10.5), (170.0, 12.0), (6.0, 90.0), (170.0, 90.0), (83.0, 22.0), (90.0, 89.5)]

# ---------------------------------------------------------------- emit
NETS = [""] + sorted({n for p in PARTS.values() for n in p.pins.values() if n},
                     key=lambda s: (s not in ("GND", "+5V", "+12V", "HV185"), s))
NI = {n: i for i, n in enumerate(NETS)}
out = []


def U(key):
    return str(uuid.uuid5(NS, key))


def value_for(p):
    v = p.value
    return v.split(" / ")[0 if BUILD == "smd" else 1] if " / " in v else v


def emit_part(ref):
    p = PARTS[ref]
    fp, x, y = PLACED[ref]
    t = fp_text(fp)
    assert t.startswith("(footprint") and t.endswith(")")
    t = t[:-1].rstrip()
    back = not p.front
    if back and "B.CrtYd" not in t:         # a front-authored symmetric part mounted on the back
        for a, b in (('"F.SilkS"', '"B.SilkS"'), ('"F.Fab"', '"B.Fab"'), ('"F.CrtYd"', '"B.CrtYd"')):
            t = t.replace(a, b)
        t = t.replace("\n\t\t\t)\n\t\t)", "\n\t\t\t)\n\t\t\t(justify mirror)\n\t\t)")
    lay = '(layer "F.Cu")'
    t = t.replace(lay, ('(layer "B.Cu")' if back else lay) + f'\n\t(uuid "{U(ref)}")\n\t(at {x:.4f} {y:.4f})', 1)
    t = t.replace('(property "Reference" "REF**"', f'(property "Reference" "{ref}"', 1)
    t = re.sub(r'\(property "Value" "[^"]*"', f'(property "Value" "{value_for(p)}"', t, count=1)
    k = [0]

    def fresh(m):
        k[0] += 1
        return f'(uuid "{U(ref + "/" + str(k[0]))}")'
    t = re.sub(r'\(uuid "[^"]*"\)', fresh, t)

    def netify(m):
        n = p.pins.get(m.group(1))
        if not n:
            return m.group(0)
        return re.sub(r'\(layers [^)]*\)', lambda L: L.group(0) + f'\n\t\t(net {NI[n]} "{n}")', m.group(0), count=1)
    t = re.sub(r'\(pad "([^"]*)"[\s\S]*?\n\t\)', netify, t)
    have = set(re.findall(r'\(pad "([^"]*)"', t))
    lost = {pn for pn, n in p.pins.items() if n} - have
    assert not lost, (ref, fp, lost)
    out.append(t + "\n)")


add = out.append
add(f'\t(gr_rect\n\t\t(start 0 0)\n\t\t(end {W} {H})\n\t\t(stroke\n\t\t\t(width 0.05)\n\t\t\t(type default)\n'
    f'\t\t)\n\t\t(fill none)\n\t\t(layer "Edge.Cuts")\n\t\t(uuid "{U("outline")}")\n\t)')
for ref in sorted(PLACED, key=lambda r: (re.match(r"[A-Z]+", r).group(0), int(re.search(r"\d+", r).group(0)))):
    emit_part(ref)
for i, (hx, hy) in enumerate(HOLES):
    add(f'\t(footprint "MountingHole_2.7mm"\n\t\t(version {VER})\n\t\t(generator "{GEN}")\n'
        f'\t\t(generator_version "{GENV}")\n\t\t(layer "F.Cu")\n\t\t(uuid "{U("H" + str(i))}")\n'
        f'\t\t(at {hx} {hy})\n\t\t(descr "M2.5 clearance, non-plated")\n'
        f'\t\t(attr exclude_from_pos_files exclude_from_bom)\n'
        f'\t\t(pad "" np_thru_hole circle\n\t\t\t(at 0 0)\n\t\t\t(size 2.7 2.7)\n'
        f'\t\t\t(drill 2.7)\n\t\t\t(layers "F&B.Cu" "*.Mask")\n\t\t\t(uuid "{U("H" + str(i) + "p")}")\n\t\t)\n'
        f'\t\t(embedded_fonts no)\n\t)')


def text(s, x, y, layer, size=1.0, mirror=False):
    j = "\n\t\t\t(justify mirror)" if mirror else ""
    add(f'\t(gr_text "{s}"\n\t\t(at {x} {y} 0)\n\t\t(layer "{layer}")\n\t\t(uuid "{U("txt " + s + str(x) + str(y))}")\n'
        f'\t\t(effects\n\t\t\t(font\n\t\t\t\t(size {size} {size})\n\t\t\t\t(thickness 0.15)\n\t\t\t){j}\n\t\t)\n\t)')


text(f"{BOARD}  TERMINAL-06  {'SMD' if BUILD == 'smd' else 'THT'} build", 110.0, H - 1.6, "B.SilkS", 1.2, True)
text("12V", 4.0, 77.0, "B.SilkS", 1.0, True)
text("USB", 4.0, 2.0, "B.SilkS", 1.0, True)

# ---------------------------------------------------------------- routing
tracks = vias = 0
if ROUTE:
    from pcbroute import Router, VIA_D, VIA_DRILL, G
    PADS = []
    for blk in out:
        if not blk.startswith("(footprint"):
            continue
        at = re.search(r'\n\t\(at ([\d.-]+) ([\d.-]+)\)', blk)
        ox, oy = float(at.group(1)), float(at.group(2))
        ref = re.search(r'\(property "Reference" "([^"]*)"', blk).group(1)
        for m in re.finditer(r'\(pad "([^"]*)" (\w+) (\w+)\n\t\t\(at ([\d.-]+) ([\d.-]+)\)\n\t\t\(size ([\d.]+) ([\d.]+)\)([\s\S]*?)\n\t\)', blk):
            px_, py_, pw, ph = ox + float(m.group(4)), oy + float(m.group(5)), float(m.group(6)), float(m.group(7))
            body = m.group(8)
            lay = re.search(r'\(layers ([^)]*)\)', body).group(1)
            drill = re.search(r'\(drill (?:oval )?([\d.]+)', body)
            net = re.search(r'\(net \d+ "([^"]*)"\)', body)
            PADS.append({"ref": ref, "pad": m.group(1), "type": m.group(2), "net": net.group(1) if net else None, "x": px_, "y": py_,
                         "layers": (0, 1) if "*.Cu" in lay or "F&B.Cu" in lay else ((0,) if "F.Cu" in lay else (1,)),
                         "shape": ("circle", px_, py_, pw / 2) if m.group(3) == "circle" else ("rect", px_, py_, pw, ph),
                         "drill": float(drill.group(1)) if drill else None})
    rt = Router(W, H, N.HV_NETS)
    for p in PADS:
        if p["type"] == "np_thru_hole":
            rt.hole(p["x"], p["y"], p["drill"] or 3.5)
        else:
            rt.paint(p["net"], p["layers"], p["shape"])
            if p["type"] == "thru_hole":
                rt.drill(p["x"], p["y"], p["drill"])
            else:
                rt.novia(p["shape"], VIA_D / 2 + 0.1)
    for hx, hy in HOLES:
        rt.hole(hx, hy, 2.7)
    pads_of, hub_pad = {}, {}
    for p in PADS:
        if p["net"]:
            t = (p["x"], p["y"], p["layers"], p["shape"])
            pads_of.setdefault(p["net"], []).append(t)
            if (p["ref"] == "U2" and p["net"].startswith("K")) or (p["ref"], p["pad"]) in (("XS1", "2"), ("C7", "1"), ("U14", "3"), ("VD2", "1")):
                hub_pad[p["net"]] = t
    HV = set(N.HV_NETS)
    POWER = {"HV185", "+5V", "+12V", "GND", "SW"}

    def width(n):
        return 0.35 if n in POWER else 0.25 if n in HV else 0.2

    def span(n):
        xs, ys = [q[0] for q in pads_of[n]], [q[1] for q in pads_of[n]]
        return (max(xs) - min(xs)) + (max(ys) - min(ys))

    # ---- stage 1: all the high voltage, the 185 V trunk included, laid first and never moved.
    # The trunk has 14 pads spread over the whole board and a 0.6 mm halo everywhere; negotiated,
    # it defeated the through-hole build outright, coming out in 14 pieces and taking seven other
    # nets with it (18.09.26).
    # The ten-line cathode spine K0..K9 was tried here too, on the same reasoning, and it is a
    # mistake: laid net after net it fences the rest in, and the negotiation ended with six nets
    # dropped instead of three. That is TS06-SEC's own lesson - negotiation beats ordering - and
    # it applies to everything that can be negotiated. Only copper that CANNOT be, because its
    # halo is too wide or its reach too long, belongs in this stage.
    t0 = time.time()
    order = sorted((n for n in pads_of if n in HV), key=lambda n: (span(n), n))
    nf0 = len(rt.failed)
    base, best = rt.snapshot(), None
    for attempt in range(8):
        rt.restore(base)
        for n in order:
            rt.route_net(n, width(n), pads_of[n])
        lost = list(dict.fromkeys(fl[0] for fl in rt.failed[nf0:]))
        if best is None or len(rt.failed) < best[1]:
            best = (attempt, len(rt.failed), rt.snapshot())
        again = lost + [n for n in order if n not in lost]
        if not lost or again == order:
            break
        order = again
    rt.restore(best[2])
    print(f"stage 1 (high voltage, the 185 V trunk included): {len(order)} nets, "
          f"{len(rt.failed) - nf0} connection(s) not found (kept attempt {best[0] + 1}), "
          f"{time.time() - t0:.0f} s", flush=True)

    # ---- stage 2: GND, a tree laid BEFORE the signals, then a pour on both faces.
    # GND is 74 of this board's 483 pads. It is NOT negotiated with the signals: a tree that
    # large crosses nearly every other net, so almost every net is then reported as overlapping
    # GND rather than its real neighbour and nothing converges (two runs stuck at ~80 of 98 nets
    # overlapping, 18.09.26). Nor is it left to a pour with stubs: the signal copper cuts the
    # pour into islands, so one region reached 37 of 74 pads and 66 stubs could not close the
    # rest. Nor last, after the signals: with the board full its tree could not reach 21 pads
    # and GND came out in 11 pieces.
    # So it is laid HERE, after the high voltage and before the signals, the way a board is
    # routed by hand: power and ground while there is room, signals afterwards, and they have
    # the negotiation to find their way round. The pours then add area over the top.
    gnd = pads_of["GND"]
    hub = hub_pad.get("GND", gnd[0])        # the jack's GND pin: the tree grows from the supply
    nf0, stranded = len(rt.failed), []
    fails = rt.route_net("GND", 0.3, [hub] + [p for p in gnd if p is not hub],
                         via_cost=RP["via_cost"], bias=RP["bias"])
    print(f"stage 2 (GND): {len(gnd)} pads wired as a tree, {fails} connection(s) not found, "
          f"{time.time() - t0:.0f} s", flush=True)
    # Whatever will not fit at 0.3 mm is retried at 0.2 mm, and against the three nearest GND
    # pads rather than only the one the tree picked. The pads that fail are inside the tube
    # rings, under the expanders and among the ИН-15 switches, where the gap the negotiation
    # leaves is one narrow track wide; 0.2 mm is this board's signal width and carries the few
    # milliamps such a leaf returns many times over. Without this the net came out in fourteen
    # pieces (18.09.26).
    if fails:
        lost = [f[1] for f in rt.failed[nf0:] if f[0] == "GND"]
        del rt.failed[nf0:]
        at = {(round(p[0], 2), round(p[1], 2)): p for p in gnd}
        saved, tried = 0, list(dict.fromkeys(lost))
        for xy in tried:
            p = at.get(xy)
            if p is None:
                continue
            near = sorted((q for q in gnd if q is not p), key=lambda q: math.hypot(q[0] - p[0], q[1] - p[1]))
            mark = len(rt.failed)
            if any(rt.connect("GND", 0.2, p, q, via_cost=RP["via_cost"], bias=RP["bias"]) for q in near[:3]):
                del rt.failed[mark:]
                saved += 1
            else:
                stranded.append(p)
        print(f"stage 2 (GND): {saved} of {len(tried)} retried at 0.2 mm, {time.time() - t0:.0f} s", flush=True)
    # Last resort for a pad the tree cannot reach at any width: a via straight up into the front
    # face's pour, which the negotiation's layer_cost keeps in one piece. pour_reach() says where
    # that pour actually joins up, so the via lands somewhere the copper really is.
    portals = [(p["x"], p["y"]) for p in PADS if p["net"] == "GND" and p["type"] == "thru_hole"]
    reach = rt.pour_reach("GND", (0, 1), [(hub[0], hub[1])], portals + [(v[0], v[1]) for v in rt.vias if v[2] == "GND"])
    joined = sum(1 for p in gnd if any(reach[L][int(round(p[1] / G)), int(round(p[0] / G))] for L in reach))
    print(f"stage 2 (GND): the pours alone join {joined}/{len(gnd)} pads; the tree carries the rest", flush=True)
    if stranded:
        mark, stitched = len(rt.failed), 0
        for p in stranded:
            for layer in (0, 1):
                if rt.fanout("GND", 0.2, p, layer, reach=reach[layer], via_cost=RP["via_cost"]):
                    stitched += 1
                    break
        del rt.failed[mark:]
        print(f"stage 2 (GND): {stitched} of {len(stranded)} stranded pad(s) stitched into a pour, "
              f"{time.time() - t0:.0f} s", flush=True)

    # ---- stage 3: everything else, negotiated at once in the manner of PathFinder.
    # THE PRICE HAS TO BEAT A VIA, and at first it did not. A plain step costs 10, an overlapped
    # cell costs `price`, and crossing a net on the other face costs two vias, so a net only
    # stops sharing a corridor once price x (overlap length) exceeds 2 x via_cost. At SEC's
    # via_cost 1500 and a price starting at 3, a 15-cell overlap costs 45 against 3000 for the
    # crossing: three runs stalled at 80-89 of ~98 nets overlapping, the count falling by one or
    # two a round while each round took 2-5 minutes (18.09.26). With a via at 2.5 mm of track
    # and a price of 60 that same overlap costs 900 against 500, so the router changes face
    # instead - which is what the nearly empty front is for, the tubes and LEDs being its only
    # copper. The owner budgets vias deliberately rather than hunting them to zero.
    # Both faces are priced alike: making the front dearer to keep it clear for the GND pour was
    # tried and cost three signal nets while leaving GND no better (18.09.26).
    order = sorted((n for n in pads_of if n != "GND" and n not in HV), key=lambda n: (span(n), n))
    nf0 = len(rt.failed)
    print("routing parameters: " + "  ".join(f"{k}={v}" for k, v in RP.items()), flush=True)
    # A NET WITH PADS ALL OVER THE BOARD MUST BE ABLE TO CHANGE FACE. A via cost chosen to
    # keep signals tidy strands one: +5V has 29 pads, more than anything but GND, and at a via
    # priced at 9 mm of track it came out of the negotiation in 29 pieces while every ordinary
    # signal routed (18.09.26). Eight pads is the line - it takes +5V, +12V and the backlight
    # cathode, and leaves the seven-pad К155ИД1 cathode lines on the tidy price.
    # BUSES for the bundle rule. Nets whose names differ only in a trailing number come off one
    # driver and are meant to travel together: the ten К155ИД1 cathode lines K0..K9 to the tubes,
    # the two expander ports, the Nano pins D2..D13, the eight backlight anodes. Three members is
    # the smallest thing worth calling a bus. Whether the base nets B1..B20 belong here is a real
    # question - they are short and local rather than a bus - and the answer is measured, not
    # assumed: TS06_BUNDLE=0 turns the whole rule off for a control run.
    grp = {}
    for nm in order:
        grp.setdefault(nm.rstrip("0123456789"), []).append(nm)
    GROUPS = {nm: k for k, v in grp.items() if k and len(v) >= 3 for nm in v}
    if RP["bundle"]:
        print(f"  {len(set(GROUPS.values()))} bus(es) over {len(GROUPS)} nets: "
              + " ".join(sorted(set(GROUPS.values()))), flush=True)

    def via_price(n):
        return min(250, RP["via_cost"]) if len(pads_of[n]) >= 8 else RP["via_cost"]
    rt.negotiate([(n, width(n), sorted(pads_of[n], key=lambda q: q is not hub_pad.get(n)),
                   {"via_cost": via_price(n)}) for n in order],
                 rounds=RP["rounds"], price=RP["price"], rise=RP["rise"], turn=RP["turn"],
                 bias=RP["bias"], decay=RP["decay"], tighten=RP["tighten"], relax=RP["relax"],
                 groups=GROUPS, bundle=RP["bundle"], compact=RP["compact"],
                 log=lambda m: print(m, flush=True))
    print(f"stage 3 (everything else, negotiated): {len(order)} nets, {len(rt.failed) - nf0} not routed, "
          f"{time.time() - t0:.0f} s", flush=True)

    # ---- stage 4: one more try at whatever the negotiation dropped.
    # negotiate() takes out the nets that still overlap when the rounds run out, which frees
    # their copper; a single net routed on its own afterwards, against the finished board and
    # with cheap vias, sometimes finds the way it could not while everything moved at once.
    # Nets it could not connect at all are retried here too, for the same reason.
    # A net is kept only if it routes COMPLETELY - a half-laid net is a split net with extra
    # copper in the way.
    dropped = list(dict.fromkeys(f[0] for f in rt.failed[nf0:]))
    if dropped:
        saved = []
        for n in dropped:
            snap, mark = rt.snapshot(), len(rt.failed)
            if rt.route_net(n, width(n), pads_of[n], via_cost=max(150, RP["via_cost"] // 4),
                            bias=RP["bias"]) == 0:
                del rt.failed[mark:]
                saved.append(n)
            else:
                rt.restore(snap)
        print(f"stage 4 (dropped nets, retried alone): {len(saved)} of {len(dropped)} placed"
              + (" - " + " ".join(saved) if saved else "") + f", {time.time() - t0:.0f} s", flush=True)

    for fl in rt.failed:
        print("  NOT ROUTED", fl)
    for k, (x1, y1, x2, y2, w, lay, n) in enumerate(rt.segments):
        add(f'\t(segment\n\t\t(start {x1:.4f} {y1:.4f})\n\t\t(end {x2:.4f} {y2:.4f})\n\t\t(width {w})\n'
            f'\t\t(layer "{lay}")\n\t\t(net {NI[n]})\n\t\t(uuid "{U("seg" + str(k))}")\n\t)')
    for k, (x, y, n) in enumerate(rt.vias):
        add(f'\t(via\n\t\t(at {x:.4f} {y:.4f})\n\t\t(size {VIA_D})\n\t\t(drill {VIA_DRILL})\n'
            f'\t\t(layers "F.Cu" "B.Cu")\n\t\t(net {NI[n]})\n\t\t(uuid "{U("via" + str(k))}")\n\t)')
    tracks, vias = len(rt.segments), len(rt.vias)
    for zl in ("F.Cu", "B.Cu"):
        add('\t(zone\n\t\t(net %d)\n\t\t(net_name "GND")\n\t\t(layers "%s")\n\t\t(uuid "%s")\n'
            '\t\t(name "GND")\n\t\t(hatch edge 0.5)\n\t\t(connect_pads thru_hole_only\n\t\t\t(clearance 0.6)\n\t\t)\n'
            '\t\t(min_thickness 0.25)\n\t\t(filled_areas_thickness no)\n'
            '\t\t(fill\n\t\t\t(thermal_gap 0.5)\n\t\t\t(thermal_bridge_width 0.5)\n\t\t\t(island_removal_mode 0)\n\t\t)\n'
            '\t\t(polygon\n\t\t\t(pts\n%s\n\t\t\t)\n\t\t)\n\t)'
            % (NI["GND"], zl, U("zone GND " + zl), "\n".join("\t\t\t\t(xy %.2f %.2f)" % pt for pt in
               ((0.5, 0.5), (W - 0.5, 0.5), (W - 0.5, H - 0.5), (0.5, H - 0.5)))))

head = [f'(kicad_pcb\n\t(version {VER})\n\t(generator "{GEN}")\n\t(generator_version "{GENV}")',
        '\t(general\n\t\t(thickness 1.6)\n\t\t(legacy_teardrops no)\n\t)', '\t(paper "A4")']
layers = ['\t(layers', '\t\t(0 "F.Cu" signal)', '\t\t(2 "B.Cu" signal)',
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
          '\t\t(43 "User.3" user)', '\t\t(45 "User.4" user)', '\t)']
setup = ['\t(setup', '\t\t(pad_to_mask_clearance 0)', '\t\t(allow_soldermask_bridges_in_footprints no)',
         '\t\t(tenting\n\t\t\t(front yes)\n\t\t\t(back yes)\n\t\t)', '\t)']
nets = ['\t(net %d "%s")' % (i, n) for i, n in enumerate(NETS)]
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf8", newline="\n") as fh:
    fh.write("\n".join(head + layers + setup + nets + out) + "\n\t(embedded_fonts no)\n)\n")
print("wrote", os.path.relpath(OUT, ROOT))
print(f"board {W} x {H} mm, {len(PLACED)} parts, {len(NETS) - 1} nets, {len(HOLES)} holes, {tracks} tracks, {vias} vias")
