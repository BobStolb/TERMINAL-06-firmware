#!/usr/bin/env python3
"""Generate the TS06-FASCIA board: outline, placement, nets and the front artwork.

FRONT FACE RULE: nothing punches a hole through it. The fascia's front is the product
face, so every wire-landing pad is SMD on B.Cu and every passive is 1206 on B.Cu. The
only holes are five bushings and four mounting screws. This is also what makes the
decorative gold safe - it is real copper on F.Cu, and it would short to any through-hole
pad it crossed.

Regenerate with:  python3 tools/mkpcb.py
Format tokens from a real KiCad 10.0 save: .kicad_pcb version 20260206, gen "pcbnew".

THIS PASS IS PLACEMENT AND ARTWORK ONLY - no copper routing. The board carries its
footprints, its nets, the front artwork and the decorative gold, and nothing else.

The routing exists and is not lost. It lives on branch pcb/fascia-routed (43 tracks,
7 vias, two layers, audited clean) and verbatim in tools/_fascia_routing.py.disabled.
Re-enabling it is a paste above the assemble section, not a rewrite.

J1's pin order is left as the routing chose it - D8, D7, GND, A7, +5V, A6 - because
that order puts each net on the pin nearest where it arrives from, which is worth
keeping whoever does the routing next.

Two conventions worth knowing before editing:
  * Every footprint is placed at rotation 0. KiCad stores a rotated footprint's pad
    coordinates in a way that is easy to get subtly wrong when writing the file by
    hand, so the layout is arranged to avoid needing rotation at all.
  * Back-side parts are authored directly on B.* layers rather than being "flipped".
    Since these footprints are ours, we write the geometry we want instead of doing
    mirror arithmetic and hoping.
"""
import os, re, math, uuid

VER, GEN, GENV = 20260206, "pcbnew", "10.0"
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PRETTY = os.path.join(ROOT, "PCB", "lib", "TS06.pretty")
OUT = os.path.join(ROOT, "PCB", "TS06-FASCIA", "TS06-FASCIA.kicad_pcb")

W, H, CR = 176.0, 52.0, 1.5                    # board outline
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

def place(fpname, ref, val, x, y, nets=None, back=False):
    t = load(fpname).rstrip()
    assert t.startswith("(footprint") and t.endswith(")")
    t = t[:-1].rstrip()
    if back:
        for a, b in (('(layer "F.Cu")', '(layer "B.Cu")'), ('"F.SilkS"', '"B.SilkS"'),
                     ('"F.Fab"', '"B.Fab"'), ('"F.CrtYd"', '"B.CrtYd"')):
            t = t.replace(a, b)
        t = t.replace("\n\t\t\t)\n\t\t)", "\n\t\t\t)\n\t\t\t(justify mirror)\n\t\t)")
    lay = '(layer "B.Cu")' if back else '(layer "F.Cu")'
    t = t.replace(lay, lay + f'\n\t(uuid "{U()}")\n\t(at {x:.4f} {y:.4f})', 1)
    t = t.replace('(property "Reference" "REF**"', f'(property "Reference" "{ref}"', 1)
    t = re.sub(r'\(property "Value" "[^"]*"', f'(property "Value" "{val}"', t, count=1)
    if nets:
        def netify(m):
            """Insert the net after whatever (layers ...) the pad actually declares.
            This used to match only '(layers "*.Cu" "*.Mask")', which is what through-hole
            pads emit - so the moment the landing pads and the connector became SMD with
            explicit B.Cu layers, every net silently failed to attach and the board looked
            fine while being entirely unconnected."""
            num = m.group(1)
            if num not in nets: return m.group(0)
            n = nets[num]
            return re.sub(r'\(layers [^)]*\)',
                          lambda L: L.group(0) + f'\n\t\t(net {NI[n]} "{n}")',
                          m.group(0), count=1)
        t = re.sub(r'\(pad "(\d+)"[\s\S]*?\n\t\)', netify, t)
    add(t + "\n)")

place("TS06_Rotary_SR25_PanelMount", "SW1", "SR25 6-pos", CX, CY,
      {"1": "GND", "2": "TAP2", "3": "TAP3", "4": "TAP4", "5": "TAP5", "6": "+5V", "7": "A6"})
place("TS06_MT1_Lever_PanelMount", "SW2", "FIELD", LEV["SW2"], CTRL_Y, {"1": "LEVA", "2": "A7"})
place("TS06_MT1_Lever_PanelMount", "SW3", "SUB",   LEV["SW3"], CTRL_Y, {"1": "LEVB", "2": "A7"})
place("TS06_KMD1_Button_PanelMount", "SW4", "MINUS", BTN["SW4"], CTRL_Y, {"1": "GND", "2": "D7"})
place("TS06_KMD1_Button_PanelMount", "SW5", "PLUS",  BTN["SW5"], CTRL_Y, {"1": "GND", "2": "D8"})

# The A6 divider, on the back, below the rotary's 25 mm body keepout.
# Each resistor sits in the gap between the two switch pads it bridges, in the same
# descending order. R5 (+5V..TAP5) leftmost, R1 (TAP2..GND) rightmost.
LAD = [("R5", "4k7", "+5V", "TAP5"), ("R4", "4k7", "TAP5", "TAP4"),
       ("R3", "4k7", "TAP4", "TAP3"), ("R2", "4k7", "TAP3", "TAP2"),
       ("R1", "4k7", "TAP2", "GND")]
for i, (ref, val, p1, p2) in enumerate(LAD):
    place("TS06_R_1206_HandSolder", ref, val, 10.0 + i * 8.0, 48.0,
          {"1": p1, "2": p2}, back=True)

# The lever ladder drops into the clear band under the lever bodies, level with each
# other, so the A7 and GND runs stay straight.
place("TS06_R_1206_HandSolder", "R7", "20k", 95.0, 40.5, {"1": "LEVA", "2": "GND"}, back=True)
place("TS06_R_1206_HandSolder", "R6", "10k", 106.5, 40.5, {"1": "+5V", "2": "A7"}, back=True)
place("TS06_R_1206_HandSolder", "R8", "10k", 118.0, 40.5, {"1": "LEVB", "2": "GND"}, back=True)
place("TS06_JST_PH_S6B-PH-SM4-TB_Back", "J1", "PH 6", 152.0, 45.4,
      {"1": "D8", "2": "D7", "3": "GND", "4": "A7", "5": "+5V", "6": "A6"}, back=True)
add(f'\t(gr_text "1 D8  2 D7  3 GND  4 A7  5 +5V  6 A6"\n\t\t(at 152.0 50.9 0)\n'
    f'\t\t(layer "B.SilkS")\n\t\t(uuid "{U()}")\n\t\t(effects\n\t\t\t(font\n'
    f'\t\t\t\t(size 1.0 1.0)\n\t\t\t\t(thickness 0.15)\n\t\t\t)\n'
    f'\t\t\t(justify mirror)\n\t\t)\n\t)')

# ---------------------------------------------------------------- mounting holes
for hx, hy in ((4.5, 4.5), (W - 4.5, 4.5), (4.5, H - 4.5), (W - 4.5, H - 4.5)):
    add(f'\t(footprint "MountingHole_2.7mm"\n\t\t(version {VER})\n\t\t(generator "{GEN}")\n'
        f'\t\t(generator_version "{GENV}")\n\t\t(layer "F.Cu")\n\t\t(uuid "{U()}")\n'
        f'\t\t(at {hx} {hy})\n\t\t(descr "M2.5 clearance, non-plated")\n'
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
gold_text("-", BTN["SW4"], 38.6, 3.4, 0.6, bold=True)
gold_text("+", BTN["SW5"], 38.6, 3.4, 0.6, bold=True)

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
gold_line(BX, 34.2, LEV["SW2"], 34.2)          # enable, in from FIELD's second throw
gold_line(LEV["SW2"], 34.2, LEV["SW2"], 32.6)  # ends directly beneath it, no angle
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
