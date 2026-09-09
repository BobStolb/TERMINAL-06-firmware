#!/usr/bin/env python3
"""Generate TS06-FASCIA-THT: the through-hole variant, fully routed.

THE IDEA: the A6 divider is the one circuit on this instrument worth reading, so it
comes out from behind the panel and onto the face. Five axial resistors in a row, the
rotary's seven landing holes beneath them, and the traces between them left BARE - mask
opened, ENIG gold. Every joint on the board shows a solder fillet on the front, because
through-hole plating puts one there whichever side the body sits on.

Everything that is not the ladder stays quiet: R6-R8, the connector and the other
landing pads mount on the back and route under mask.

GND is a POUR on B.Cu rather than a routed net. That is what ground planes are for, and
it takes the net with the most stubs out of the routing problem completely. The back is
hidden, so a pour costs nothing visually. NOTE: KiCad shows a zone as an outline until
it is filled - press B in the PCB editor.

TWO RULES SET THE PLACEMENT OF THE BACK PARTS:
  * The panel parts have bodies behind the board - 24 to 25 mm across. Nothing can sit
    inside those circles, so R6-R8 stay in the strip below y 38.5, clear of all of them.
  * A through-hole pad is copper on BOTH faces. The decorative gold is copper too, so
    every back part must also miss the artwork on the front. The pads of the back parts
    have their FRONT mask closed: the face shows the drilled hole, not a gold ring.
    Only the ladder is opened, and only the ladder shows solder.
"""
import os, re, math, uuid

VER, GEN, GENV = 20260206, "pcbnew", "10.0"
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PRETTY = os.path.join(ROOT, "PCB", "lib", "TS06.pretty")
OUT = os.path.join(ROOT, "PCB", "TS06-FASCIA-THT", "TS06-FASCIA-THT.kicad_pcb")

W, H, CR = 176.0, 52.0, 1.5
SWY, RY = 50.0, 45.5   # rotary landing holes / the ladder on the face                    # board outline
CX, CY = 30.0, 26.0                            # rotary centre
LEV = {"SW2": 95.0, "SW3": 118.0}              # FIELD, SUB
BTN = {"SW4": 146.0, "SW5": 164.0}             # minus, plus
CTRL_Y = 26.0
STEP, N_POS, R_START = 30.0, 6, 75.0           # 12 detents -> exactly 30.00 deg
LABEL = ["NORMAL", "SET TIME", "DISPLAY", "AMBIENT", "FORMAT/DATE", "INFO"]
SUBLIVE = [2, 4]                               # positions that read SUB

NETS = ["", "GND", "+5V", "A6", "A7", "D7", "D8",
        "TAP2", "TAP3", "TAP4", "TAP5", "LEVA", "LEVB"]
NI = {n: i for i, n in enumerate(NETS)}

def U(): return str(uuid.uuid4())
def ang(i): return math.radians(R_START - STEP * i)
def px(r, i): return CX + r * math.cos(ang(i))
def py(r, i): return CY - r * math.sin(ang(i))

out = []
def add(s): out.append(s)

def line(x1, y1, x2, y2, layer, w=0.15):
    add(f'\t(gr_line\n\t\t(start {x1:.4f} {y1:.4f})\n\t\t(end {x2:.4f} {y2:.4f})\n'
        f'\t\t(stroke\n\t\t\t(width {w})\n\t\t\t(type solid)\n\t\t)\n'
        f'\t\t(layer "{layer}")\n\t\t(uuid "{U()}")\n\t)')

def arc(x1, y1, xm, ym, x2, y2, layer, w=0.1):
    add(f'\t(gr_arc\n\t\t(start {x1:.4f} {y1:.4f})\n\t\t(mid {xm:.4f} {ym:.4f})\n'
        f'\t\t(end {x2:.4f} {y2:.4f})\n\t\t(stroke\n\t\t\t(width {w})\n\t\t\t(type solid)\n'
        f'\t\t)\n\t\t(layer "{layer}")\n\t\t(uuid "{U()}")\n\t)')

def circ(x, y, r, layer, w=0.12):
    add(f'\t(gr_circle\n\t\t(center {x:.4f} {y:.4f})\n\t\t(end {x+r:.4f} {y:.4f})\n'
        f'\t\t(stroke\n\t\t\t(width {w})\n\t\t\t(type solid)\n\t\t)\n\t\t(fill no)\n'
        f'\t\t(layer "{layer}")\n\t\t(uuid "{U()}")\n\t)')

def text(s, x, y, layer, size=1.6, thick=0.25, just="", rot=0, bold=False):
    j = f'\n\t\t\t(justify {just})' if just else ""
    b = "\n\t\t\t\t(bold yes)" if bold else ""
    add(f'\t(gr_text "{s}"\n\t\t(at {x:.4f} {y:.4f} {rot})\n\t\t(layer "{layer}")\n'
        f'\t\t(uuid "{U()}")\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size {size} {size})\n'
        f'\t\t\t\t(thickness {thick}){b}\n\t\t\t){j}\n\t\t)\n\t)')

def gold_line(x1, y1, x2, y2, w=0.45):
    """Exposed copper. w is the width you SEE - the opening. The copper underneath is
    made wider so the mask laps onto its edge; the other way round leaves a sliver of
    bare laminate showing around every gold feature, which on a black board reads as a
    pale outline rather than a clean edge."""
    line(x1, y1, x2, y2, "F.Cu", w + 0.15)
    line(x1, y1, x2, y2, "F.Mask", w)

def gold_text(s, x, y, size=1.6, thick=0.25, just="", bold=False):
    text(s, x, y, "F.Cu", size, thick + 0.12, just, bold=bold)
    text(s, x, y, "F.Mask", size, thick, just, bold=bold)

# ---------------------------------------------------------------- outline
line(CR, 0, W - CR, 0, "Edge.Cuts", 0.05)
line(W, CR, W, H - CR, "Edge.Cuts", 0.05)
line(W - CR, H, CR, H, "Edge.Cuts", 0.05)
line(0, H - CR, 0, CR, "Edge.Cuts", 0.05)
k = CR - CR * math.sqrt(0.5)
arc(0, CR, k, k, CR, 0, "Edge.Cuts", 0.05)
arc(W - CR, 0, W - k, k, W, CR, "Edge.Cuts", 0.05)
arc(W, H - CR, W - k, H - k, W - CR, H, "Edge.Cuts", 0.05)
arc(CR, H, k, H - k, 0, H - CR, "Edge.Cuts", 0.05)

# ---------------------------------------------------------------- footprints
def load(name):
    return open(os.path.join(PRETTY, name + ".kicad_mod"), encoding="utf8").read()

def place(fpname, ref, val, x, y, nets=None, back=False, front_mask=True):
    t = load(fpname).rstrip()
    t = t[:-1].rstrip()
    if back:
        for a, b in (('(layer "F.Cu")', '(layer "B.Cu")'), ('"F.SilkS"', '"B.SilkS"'),
                     ('"F.Fab"', '"B.Fab"'), ('"F.CrtYd"', '"B.CrtYd"')):
            t = t.replace(a, b)
        t = t.replace("\n\t\t\t)\n\t\t)", "\n\t\t\t)\n\t\t\t(justify mirror)\n\t\t)")
    lay = '(layer "B.Cu")' if back else '(layer "F.Cu")'
    t = t.replace(lay, lay + f'\n\t(uuid "{U()}")\n\t(at {x:.4f} {y:.4f})', 1)
    t = t.replace('(property "Reference" "REF**"', f'(property "Reference" "{ref}"', 1)
    if not front_mask:                       # solder is behind: no gold ring on the face
        t = t.replace('(layers "*.Cu" "*.Mask")', '(layers "*.Cu" "B.Mask")')
    t = re.sub(r'\(property "Value" "[^"]*"', f'(property "Value" "{val}"', t, count=1)
    if nets:
        def netify(m):
            num = m.group(1)
            if num not in nets: return m.group(0)
            n = nets[num]
            return re.sub(r'\(layers [^)]*\)',
                          lambda L: L.group(0) + f'\n\t\t(net {NI[n]} "{n}")',
                          m.group(0), count=1)
        t = re.sub(r'\(pad "(\d+)"[\s\S]*?\n\t\)', netify, t)
    add(t + "\n)")

# The rotary and its ladder are on the FACE. Landing holes on 13 mm pitch so a 10.16 mm
# axial resistor drops into every gap between adjacent taps, in descending voltage order.
place("TS06_Rotary_SR25_THT", "SW1", "SR25 6-pos", CX, CY,
      {"1": "GND", "2": "TAP2", "3": "TAP3", "4": "TAP4", "5": "TAP5", "6": "+5V", "7": "A6"})
SWX = [8.0, 21.0, 34.0, 47.0, 60.0, 73.0, 86.0]   # +5V TAP5 TAP4 TAP3 TAP2 GND A6
LAD = [("R5", "4k7", "+5V", "TAP5"), ("R4", "4k7", "TAP5", "TAP4"),
       ("R3", "4k7", "TAP4", "TAP3"), ("R2", "4k7", "TAP3", "TAP2"),
       ("R1", "4k7", "TAP2", "GND")]
for i, (ref, val, p1, p2) in enumerate(LAD):
    place("TS06_R_Axial_P10.16mm_Front", ref, val, (SWX[i] + SWX[i+1]) / 2, RY,
          {"1": p1, "2": p2})

# Everything else stays behind the panel. Their landing holes are drilled through the
# face, but the front mask stays closed over them, so the face shows a bare hole and no
# gold. R6-R8 sit in the strip below y 38.5 - the only band this board has that is
# outside all five body keepouts AND clear of the artwork.
for ref, val, xx, nets in (("SW2", "FIELD", LEV["SW2"], {"1": "LEVA", "2": "A7"}),
                           ("SW3", "SUB",   LEV["SW3"], {"1": "LEVB", "2": "A7"})):
    place("TS06_MT1_Lever_THT", ref, val, xx, CTRL_Y, nets, front_mask=False)
for ref, val, xx, nets in (("SW4", "MINUS", BTN["SW4"], {"1": "GND", "2": "D7"}),
                           ("SW5", "PLUS",  BTN["SW5"], {"1": "GND", "2": "D8"})):
    place("TS06_KMD1_Button_THT", ref, val, xx, CTRL_Y, nets, front_mask=False)
RX = "TS06_R_Axial_P10.16mm_Back"
place(RX, "R6", "10k", 95.0, 41.5, {"1": "+5V",  "2": "A7"},  back=True, front_mask=False)
place(RX, "R8", "10k", 136.0, 39.0, {"1": "LEVB", "2": "GND"}, back=True, front_mask=False)
place(RX, "R7", "20k", 136.0, 44.0, {"1": "LEVA", "2": "GND"}, back=True, front_mask=False)
place("TS06_JST_PH_S6B-PH-K-S_Back", "J1", "PH 6 THT", 152.0, 45.5,
      {"1": "+5V", "2": "GND", "3": "A6", "4": "A7", "5": "D7", "6": "D8"},
      back=True, front_mask=False)
add(f'\t(gr_text "1 +5V  2 GND  3 A6  4 A7  5 D7  6 D8"\n\t\t(at 152.0 50.4 0)\n'
    f'\t\t(layer "B.SilkS")\n\t\t(uuid "{U()}")\n\t\t(effects\n\t\t\t(font\n'
    f'\t\t\t\t(size 1.0 1.0)\n\t\t\t\t(thickness 0.15)\n\t\t\t)\n'
    f'\t\t\t(justify mirror)\n\t\t)\n\t)')

for hx, hy in ((4.5, 4.5), (W - 4.5, 4.5), (4.5, H - 4.5), (W - 4.5, H - 4.5)):
    add(f'\t(footprint "MountingHole_2.7mm"\n\t\t(version {VER})\n\t\t(generator "{GEN}")\n'
        f'\t\t(generator_version "{GENV}")\n\t\t(layer "F.Cu")\n\t\t(uuid "{U()}")\n'
        f'\t(at {hx} {hy})\n\t\t(descr "M2.5 clearance, non-plated")\n'
        f'\t\t(attr exclude_from_pos_files exclude_from_bom)\n'
        f'\t\t(pad "" np_thru_hole circle\n\t\t\t(at 0 0)\n\t\t\t(size 2.7 2.7)\n'
        f'\t\t\t(drill 2.7)\n\t\t\t(layers "F&B.Cu" "*.Mask")\n\t\t\t(uuid "{U()}")\n\t\t)\n'
        f'\t\t(embedded_fonts no)\n\t)')

# ---------------------------------------------------------------- front artwork
# dial: ticks, gold numerals, word column, leader lines
arc(px(13.9, 0), py(13.9, 0), px(13.9, 2.5), py(13.9, 2.5), px(13.9, 5), py(13.9, 5),
    "F.SilkS", 0.12)
for i in range(N_POS):
    line(px(11.6, i), py(11.6, i), px(13.9, i), py(13.9, i), "F.SilkS", 0.3)
    gold_text(str(i + 1), px(16.4, i), py(16.4, i), 1.5, 0.25)
    line(px(16.4, i) + 1.6, py(16.4, i), 50.6, py(16.4, i), "F.SilkS", 0.1)
    text(LABEL[i], 52.0, py(16.4, i), "F.SilkS", 1.7, 0.26, "left")
text("MODE", CX, 7.0, "F.SilkS", 1.7, 0.28)

# lever and button lettering
text("FIELD", LEV["SW2"], 38.4, "F.SilkS", 1.9, 0.32, bold=True)
text("SUB",   LEV["SW3"], 38.4, "F.SilkS", 1.9, 0.32, bold=True)
# 1.6 lower than on the surface-mount board: the buttons now have landing holes at
# y 35.5 whose copper reaches the front face, and a 3.4 mm glyph at 38.6 came within
# 0.4 mm of one. Still reads as the mark under its button.
gold_text("-", BTN["SW4"], 40.2, 3.4, 0.6, bold=True)
gold_text("+", BTN["SW5"], 40.2, 3.4, 0.6, bold=True)

# the SUB rule, drawn as a supply. Nothing is drawn where the lever itself sits.
BX, BR_, BT, BB = 108.0, 128.0, 17.0, 41.0
for a, b, c, d in ((BX + 2.2, BT, BR_ - 2.2, BT), (BR_, BT + 2.2, BR_, BB - 2.2),
                   (BR_ - 2.2, BB, BX + 2.2, BB), (BX, BB - 2.2, BX, BT + 2.2)):
    gold_line(a, b, c, d)
q = 2.2 - 2.2 * math.sqrt(0.5)
for sx, sy, mx, my, ex, ey in (
        (BX, BT + 2.2, BX + q, BT + q, BX + 2.2, BT),
        (BR_ - 2.2, BT, BR_ - q, BT + q, BR_, BT + 2.2),
        (BR_, BB - 2.2, BR_ - q, BB - q, BR_ - 2.2, BB),
        (BX + 2.2, BB, BX + q, BB - q, BX, BB - 2.2)):
    arc(sx, sy, mx, my, ex, ey, "F.Cu", 0.45)
    arc(sx, sy, mx, my, ex, ey, "F.Mask", 0.6)
gold_line(BX, 33.5, LEV["SW2"], 33.5)          # enable, in from FIELD's second throw
gold_line(LEV["SW2"], 33.5, LEV["SW2"], 32.0)  # ends directly beneath it, no angle
y3, y5 = py(16.4, SUBLIVE[0]), py(16.4, SUBLIVE[1])
gold_line(118.0, BT, 118.0, 11.0)              # out of the top face -> position 3
gold_line(118.0, 11.0, 65.0 + (y3 - 11.0), 11.0)
gold_line(65.0 + (y3 - 11.0), 11.0, 65.0, y3)
gold_line(118.0, BB, 118.0, 45.0)              # out of the bottom face -> position 5
gold_line(118.0, 45.0, 71.0 + (45.0 - y5), 45.0)
gold_line(71.0 + (45.0 - y5), 45.0, 71.0, y5)

# keepouts, documentation only
circ(CX, CY, 12.5, "User.1")                   # rotary body, behind the panel
text("BODY 25.00", CX, 40.4, "User.1", 1.0, 0.15)
for x in list(LEV.values()) + list(BTN.values()):
    circ(x, CTRL_Y, 12.0, "User.1")

# ---------------------------------------------------------------- routing
# Front, BARE: the ladder only. Copper 0.60 wide, mask opening 0.45, so the mask laps
# 0.075 onto the edge of every trace and no bare laminate shows around the gold.
# Back, under mask: six signals on 0.30. GND is not routed at all - it is the pour.
#
# Lanes, top to bottom, chosen so nothing crosses:
#   y 31.5  LEVB going east over SW3's bushing (the only way past SW3's own A7 pad)
#   y 38.5  A7 stepping from SW2 across to R6
#   y 42.2  A7 trunk, R6 -> J1
#   y 44.0  LEVA trunk, SW2 -> R7
#   y 47.6  +5V trunk, ladder -> R6 -> J1
#   y 49.3  A6, the rotary common -> J1

def track(pts, net, layer="B.Cu", w=0.3):
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        add(f'\t(segment\n\t\t(start {x1:.3f} {y1:.3f})\n\t\t(end {x2:.3f} {y2:.3f})\n'
            f'\t\t(width {w})\n\t\t(layer "{layer}")\n\t\t(net {NI[net]})\n'
            f'\t\t(uuid "{U()}")\n\t)')

def bare(pts, net, w=0.60, opening=0.45):
    """A real trace on the front with the mask opened over it - copper you can see and
    solder to. The opening is narrower than the copper on purpose (see gold_line)."""
    track(pts, net, "F.Cu", w)
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        line(x1, y1, x2, y2, "F.Mask", opening)

# --- the ladder, on the face
SWX = {"+5V": 8.0, "TAP5": 21.0, "TAP4": 34.0, "TAP3": 47.0, "TAP2": 60.0,
       "GND": 73.0, "A6": 86.0}
bare([(SWX["+5V"], SWY), (9.42, RY)], "+5V")             # first rung, off the end pad
bare([(SWX["GND"], SWY), (71.58, RY)], "GND")            # last rung, off the sixth pad
for tap, xl, xr in (("TAP5", 19.58, 22.42), ("TAP4", 32.58, 35.42),
                    ("TAP3", 45.58, 48.42), ("TAP2", 58.58, 61.42)):
    bare([(xl, RY), (xr, RY)], tap)                      # rung to rung, straight across
    bare([(SWX[tap], SWY), (SWX[tap], RY)], tap)         # and up to the landing hole

# --- the back
track([(9.42, RY), (9.42, 47.6), (147.0, 47.6), (147.0, RY)], "+5V")   # ladder top -> J1
track([(89.92, 47.6), (89.92, 41.5)], "+5V")                           # tee up to R6
track([(86.0, SWY), (86.0, 49.3), (151.0, 49.3), (151.0, RY)], "A6")   # wiper -> J1
track([(96.6, 35.5), (96.6, 38.5), (100.08, 38.5), (100.08, 42.2),
       (153.0, 42.2), (153.0, RY)], "A7")                              # SW2 -> R6 -> J1
track([(119.6, 35.5), (119.6, 42.2)], "A7")                            # SW3 joins it
track([(93.4, 35.5), (93.4, 44.0), (130.92, 44.0)], "LEVA")            # SW2 -> R7
track([(116.4, 35.5), (116.4, 31.5), (130.92, 31.5), (130.92, 39.0)], "LEVB")
track([(147.6, 35.5), (147.6, 38.5), (155.0, 38.5), (155.0, RY)], "D7")
track([(165.6, 35.5), (165.6, 38.5), (157.0, 38.5), (157.0, RY)], "D8")

# --- GND: a pour over the whole back face, 0.5 in from the edge
add('\t(zone\n\t\t(net %d)\n\t\t(net_name "GND")\n\t\t(layers "B.Cu")\n\t\t(uuid "%s")\n'
    '\t\t(name "GND")\n\t\t(hatch edge 0.5)\n\t\t(connect_pads\n\t\t\t(clearance 0.4)\n\t\t)\n'
    '\t\t(min_thickness 0.25)\n\t\t(filled_areas_thickness no)\n'
    '\t\t(fill\n\t\t\t(thermal_gap 0.4)\n\t\t\t(thermal_bridge_width 0.5)\n\t\t)\n'
    '\t\t(polygon\n\t\t\t(pts\n%s\n\t\t\t)\n\t\t)\n\t)'
    % (NI["GND"], U(), "\n".join("\t\t\t\t(xy %.2f %.2f)" % pt for pt in
       ((0.5, 0.5), (W - 0.5, 0.5), (W - 0.5, H - 0.5), (0.5, H - 0.5)))))

# ---------------------------------------------------------------- assemble
head = [f'(kicad_pcb\n\t(version {VER})\n\t(generator "{GEN}")\n\t(generator_version "{GENV}")',
        '\t(general\n\t\t(thickness 2.0)\n\t\t(legacy_teardrops no)\n\t)', '\t(paper "A3")']
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
setup = ['\t(setup', '\t\t(pad_to_mask_clearance 0)',
         '\t\t(allow_soldermask_bridges_in_footprints no)',
         '\t\t(tenting\n\t\t\t(front yes)\n\t\t\t(back yes)\n\t\t)', '\t)']
nets = ["\t(net %d \"%s\")" % (i, n) for i, n in enumerate(NETS)]

open(OUT, "w", encoding="utf8").write(
    "\n".join(head + layers + setup + nets + out) + "\n\t(embedded_fonts no)\n)\n")
print("wrote", os.path.relpath(OUT, ROOT))
