#!/usr/bin/env python3
"""Generate the TS06-COLON board: placement only, no copper routing yet.

A narrow (<=6.5 mm wide) strip that carries the two ИНС-1 colon neons and their
local 220k ballasts (spec 3, "each lamp gets its own 220k ballast, never shared"),
sitting in the gap between the second and third IN-12 on the Gyver tube board.
XS4 (2-pin JST-XH) brings raw 185V in from SEC and the switched return back to
SEC's MPSA42 - SEC keeps the transistor and the on/off switching, this board only
ballasts and holds the glass. See PCB/README.md and the session's TS06-SEC design
notes for the Option-2-vs-Option-1 decision (Option 2: driver stays on SEC).

Lamp lead positions and the mechanical anchor hole are taken directly from the
FreeCAD "Clock" assembly (INS1 / INS001 objects, real lead-tip picks; the anchor
hole is the old Gyver stock colon-LED footprint, mechanical-only reuse - no
copper connects to it, confirmed dead per the D10/GND trace already used
elsewhere on XS3). Gaps between lamps and between the lower lamp and the anchor
are the REAL measured gaps (9.202 mm, 7.266 mm) - preserved exactly so the
verified "doesn't interfere with other lamps" fit from FreeCAD carries over.
R1/R2 sit above INS1 and below INS001 respectively, since neither of the two
real inter-component gaps is long enough for a 12.4 mm axial body; they reach
their nodes by trace, same as any other resistor that doesn't sit in a straight
line between its two connections.

Pads on both lamps and XS4 are oversized (2.2/1.0 mm on the lamps, matching the
+/-0.2 mm pitch uncertainty against the FreeCAD reference model) - wire-landing
philosophy, same as the fascia's panel hardware and SEC's own IN-17 pads.

Regenerate with:  python3 tools/mkpcb_colon.py
Format tokens from a real KiCad 10.0 save: .kicad_pcb version 20260206, gen "pcbnew".
"""
import os, uuid

VER, GEN, GENV = 20260206, "pcbnew", "10.0"
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PRETTY = os.path.join(ROOT, "PCB", "lib", "TS06.pretty")
OUT = os.path.join(ROOT, "PCB", "TS06-COLON", "TS06-COLON.kicad_pcb")

W = 6.5                        # hard limit - the inter-tube gap
CX = 3.25                      # board centreline, matches the real lamp lead column

# ---- layout, top to bottom, local Y increasing downward ----
# Clearances below are between COURTYARD edges, not pad edges - measuring from pads
# instead produced a real courtyard overlap in an earlier pass. Fixed here, not
# patched around.
#
# R1 and R2 no longer get their own dedicated slot at all - they sit INSIDE the two
# real gaps that already exist (lamp to lamp, lamp to anchor), which were already
# verified clear of interference in FreeCAD and have plenty of room to spare for a
# component whose short axis is only ~3 mm tall. Nothing hangs off the bottom past
# the anchor except XS4 - this is a placement choice, not a new electrical
# connection: R1 is still in series with INS1's far lead and HV185 regardless of
# where its body physically sits, same for R2 and INS001. A resistor doesn't have
# to sit in a straight line between its two nodes; it reaches them by trace.
LAMP_HALF, HR_HALF, XS4_HALF, GAP = 4.0, 1.5, 3.65, 2.0
ANCHOR_PITCH = 2.540                       # exact real round-pad-to-square-pad spacing,
                                            # standard 2.54mm/0.1" pitch - measured via
                                            # CenterOfMass on both pad faces, not a
                                            # picked-point estimate (that earlier read,
                                            # 2.336mm, was one hole's own diameter)
ANCHOR_CENTER_X = 2.497                     # anchor pair's midpoint is ~0.753mm off the
                                            # lamp lead column in world X (49.7815 vs
                                            # ~50.535 average); same offset applied here

y = 2.0                                    # top margin - INS1 starts right here
INS1_ORIGIN_Y = y + LAMP_HALF
INS1_TOP = INS1_ORIGIN_Y - 2.5             # INS1 pad 1 (top / "far" lead -> R1)
INS1_BOT = INS1_ORIGIN_Y + 2.5             # INS1 pad 2 (bottom / shared-node lead)

GAP_A_START = INS1_BOT
GAP_A_END = INS1_BOT + 9.202               # REAL measured gap, lamp to lamp
R1_Y = (GAP_A_START + GAP_A_END) / 2       # R1 centred in the real gap

INS001_TOP = GAP_A_END                     # INS001 pad 1 (top / shared-node lead)
INS001_ORIGIN_Y = INS001_TOP + 2.5
INS001_BOT = INS001_ORIGIN_Y + 2.5         # INS001 pad 2 (bottom / "far" lead -> R2)

GAP_B_START = INS001_BOT
GAP_B_END = INS001_BOT + 7.266             # REAL measured gap, lower lamp to anchor
R2_Y = (GAP_B_START + GAP_B_END) / 2       # R2 centred in the real gap

ANCHOR_Y = GAP_B_END - 0.5                 # centre point between the two small holes;
                                            # -0.5 is a real-overlay fine-tune (confirmed
                                            # against the actual Gyver pad positions in
                                            # FreeCAD, not derived from any measured gap)
y = ANCHOR_Y + 1.0                         # tightened - visually confirmed excess here

# XS4 is the right-angle variant: pads run across X. Only thing below the anchor now.
XS4_ORIGIN_Y = y + XS4_HALF
H = XS4_ORIGIN_Y + XS4_HALF + 1.0          # bottom margin, tightened same as above

NETS = ["", "HV185", "COLON_RET", "R1_LINK", "R2_LINK"]
NI = {n: i for i, n in enumerate(NETS)}

def U(): return str(uuid.uuid4())

out = []
def add(s): out.append(s)

# ---------------------------------------------------------------- board outline
add(f'\t(gr_rect\n\t\t(start 0 0)\n\t\t(end {W} {H:.4f})\n'
    f'\t\t(stroke\n\t\t\t(width 0.05)\n\t\t\t(type default)\n\t\t)\n'
    f'\t\t(fill none)\n\t\t(layer "Edge.Cuts")\n\t\t(uuid "{U()}")\n\t)')

# ---------------------------------------------------------------- footprints
def load(name):
    return open(os.path.join(PRETTY, name + ".kicad_mod"), encoding="utf8").read()

def place(fpname, ref, val, x, y, nets=None):
    t = load(fpname).rstrip()
    assert t.startswith("(footprint") and t.endswith(")")
    t = t[:-1].rstrip()
    lay = '(layer "F.Cu")'
    # No rotation token, ever - matches this repo's own convention (mkpcb.py's header
    # note) and this repo's placement checker, whose (at x y) regex only matches the
    # bare two-argument form. Anything that needs a different orientation gets its
    # own pre-rotated footprint variant instead (see TS06_R_Axial_P10.16mm_Vertical).
    t = t.replace(lay, lay + f'\n\t(uuid "{U()}")\n\t(at {x:.4f} {y:.4f})', 1)
    t = t.replace('(property "Reference" "REF**"', f'(property "Reference" "{ref}"', 1)
    if val is not None:
        import re
        t = re.sub(r'\(property "Value" "[^"]*"', f'(property "Value" "{val}"', t, count=1)
    if nets:
        import re
        def netify(m):
            num = m.group(1)
            if num not in nets: return m.group(0)
            n = nets[num]
            return re.sub(r'\(layers [^)]*\)',
                          lambda L: L.group(0) + f'\n\t\t(net {NI[n]} "{n}")',
                          m.group(0), count=1)
        t = re.sub(r'\(pad "(\d+)"[\s\S]*?\n\t\)', netify, t)
    add(t + "\n)")

place("TS06_INS1_Lamp", "V1", "INS1", CX, INS1_ORIGIN_Y, {"1": "R1_LINK", "2": "COLON_RET"})
place("TS06_INS1_Lamp", "V2", "INS1", CX, INS001_ORIGIN_Y, {"1": "COLON_RET", "2": "R2_LINK"})

# R1 + R2: edge-to-edge variant, stacked one above the other, both hidden along
# with the backlight LED leads by whatever already covers this end of the board.
place("TS06_R_Axial_EdgeToEdge", "R1", "220k", CX, R1_Y, {"1": "R1_LINK", "2": "HV185"})
place("TS06_R_Axial_EdgeToEdge", "R2", "220k", CX, R2_Y, {"1": "R2_LINK", "2": "HV185"})

# Right-angle variant: pads run across X, cable exits downward off the board edge.
place("TS06_XS4_JST_XH_2p_RA", "XS4", None, CX, XS4_ORIGIN_Y, {"1": "HV185", "2": "COLON_RET"})

# ---------------------------------------------------------------- mechanical anchor
# Two small NPTH holes, not one - the real Gyver stock colon-LED footprint is a
# round pad and a square pad. Both pitch and centre offset from the lamp column
# are real measured geometry (CenterOfMass on both real pad faces), not a guess.
# No copper - mechanical registration only.
for i, ax in enumerate((ANCHOR_CENTER_X - ANCHOR_PITCH / 2, ANCHOR_CENTER_X + ANCHOR_PITCH / 2)):
    add(f'\t(footprint "MountingHole_NPTH_Anchor{i+1}"\n\t\t(version {VER})\n\t\t(generator "{GEN}")\n'
        f'\t\t(generator_version "{GENV}")\n\t\t(layer "F.Cu")\n\t\t(uuid "{U()}")\n'
        f'\t\t(at {ax:.4f} {ANCHOR_Y:.4f})\n'
        f'\t\t(descr "Mechanical-only registration hole #{i+1} of 2, matching the old Gyver '
        f'stock colon-LED footprint (round + square pad). No copper - dead net, mounting only.")\n'
        f'\t\t(attr exclude_from_pos_files exclude_from_bom)\n'
        f'\t\t(pad "" np_thru_hole circle\n\t\t\t(at 0 0)\n\t\t\t(size 1.4 1.4)\n'
        f'\t\t\t(drill 0.9)\n\t\t\t(layers "F&B.Cu" "*.Mask")\n\t\t\t(uuid "{U()}")\n\t\t)\n'
        f'\t\t(embedded_fonts no)\n\t)')

# ---------------------------------------------------------------- routing
# Board is 6.5 mm wide with two obstacles right in the middle of it (the anchor's
# two NPTH holes at ANCHOR_CENTER_X +/- ANCHOR_PITCH/2), so every net gets its own
# lane rather than running straight down the centreline:
#   R1_LINK, R2_LINK  - left edge, X = CX-2.6 (R1/R2's own pad-1 X)
#   HV185             - right edge, X = CX+2.6 (R1/R2's own pad-2 X) until it has
#                       to cross under COLON_RET to reach XS4 pad 1 on the left
#   COLON_RET         - centreline down to V2, then ANCHOR_CENTER_X (the exact gap
#                       between the two anchor holes) to clear them, then over to
#                       XS4 pad 2 on the right
# HV185 and COLON_RET end up needing to swap sides (HV185 finishes left of centre
# at XS4 pad 1, COLON_RET finishes right of centre at pad 2, having started on the
# opposite sides) - but that doesn't actually require a via. HV185 just runs past
# XS4's whole pad row first and loops back up into pad 1 from below, staying clear
# of COLON_RET's approach into pad 2 (which stays well above that loop) the whole
# way. No layer change needed anywhere on this board.
TW = 0.3                                   # trace width - low current (<1 mA per
                                            # lamp through 220k), width is for
                                            # clearance margin, not ampacity

def track(x1, y1, x2, y2, layer, net):
    # (net N) only - a bare code, no name. That combined form is valid for pad (which
    # self-documents with both), but real KiCad's grammar for segment/via is code-only;
    # writing (net N "NAME") here parses as a syntax error, not just an ignored extra
    # field. Confirmed against a real "expects ')'" error opening this exact file.
    add(f'\t(segment\n\t\t(start {x1:.4f} {y1:.4f})\n\t\t(end {x2:.4f} {y2:.4f})\n'
        f'\t\t(width {TW})\n\t\t(layer "{layer}")\n\t\t(net {NI[net]})\n'
        f'\t\t(uuid "{U()}")\n\t)')

def via(x, y, net, size=0.8, drill=0.4):
    add(f'\t(via\n\t\t(at {x:.4f} {y:.4f})\n\t\t(size {size})\n\t\t(drill {drill})\n'
        f'\t\t(layers "F.Cu" "B.Cu")\n\t\t(net {NI[net]})\n\t\t(uuid "{U()}")\n\t)')

R1_PAD1_X, R1_PAD2_X = CX - 2.6, CX + 2.6
XS4_PAD1_X, XS4_PAD2_X = CX - 1.25, CX + 1.25

# R1_LINK: V1 pad 1 (top / far lead) -> R1 pad 1
track(CX, INS1_TOP, R1_PAD1_X, INS1_TOP, "F.Cu", "R1_LINK")
track(R1_PAD1_X, INS1_TOP, R1_PAD1_X, R1_Y, "F.Cu", "R1_LINK")

# R2_LINK: V2 pad 2 (bottom / far lead) -> R2 pad 1
track(CX, INS001_BOT, R1_PAD1_X, INS001_BOT, "F.Cu", "R2_LINK")
track(R1_PAD1_X, INS001_BOT, R1_PAD1_X, R2_Y, "F.Cu", "R2_LINK")

# HV185: R1 pad 2 -> R2 pad 2 (straight run, same X) -> straight past XS4's whole
# pad row -> loop back up into pad 1 from below. Clears COLON_RET's approach into
# pad 2 (which stays well above this loop) without a layer change - one F.Cu path,
# no via.
HV_LOOP_Y = XS4_ORIGIN_Y + 1.5              # past XS4 pad radius (0.8) with margin
track(R1_PAD2_X, R1_Y, R1_PAD2_X, R2_Y, "F.Cu", "HV185")
track(R1_PAD2_X, R2_Y, R1_PAD2_X, HV_LOOP_Y, "F.Cu", "HV185")
track(R1_PAD2_X, HV_LOOP_Y, XS4_PAD1_X, HV_LOOP_Y, "F.Cu", "HV185")
track(XS4_PAD1_X, HV_LOOP_Y, XS4_PAD1_X, XS4_ORIGIN_Y, "F.Cu", "HV185")

# COLON_RET: V1 pad 2 -> V2 pad 1 (straight run down the centreline), then a
# detour to the RIGHT (clear of V2's own oversized 2.2 mm pad 2 and R2_LINK's
# trace, both of which sit directly in the way of a direct line to the anchor
# lane) before cutting back to ANCHOR_CENTER_X to thread the two anchor holes,
# then over to XS4 pad 2. Checked against V2 pad 2's real footprint, not just
# eyeballed - a first pass that went straight to ANCHOR_CENTER_X clipped both
# V2 pad 2 and R2_LINK's own trace.
CR_DETOUR_X = XS4_PAD2_X + 0.3             # clears V2 pad 2 (radius 1.1) with margin,
                                            # clears HV185's lane at CX+2.6 too
CR_DETOUR_Y = INS001_BOT + 1.6             # past V2 pad 2's real bottom edge (radius 1.1)
CR_JOG_Y = XS4_ORIGIN_Y - 1.6
track(CX, INS1_BOT, CX, INS001_TOP, "F.Cu", "COLON_RET")
track(CX, INS001_TOP, CR_DETOUR_X, INS001_TOP, "F.Cu", "COLON_RET")
track(CR_DETOUR_X, INS001_TOP, CR_DETOUR_X, CR_DETOUR_Y, "F.Cu", "COLON_RET")
track(CR_DETOUR_X, CR_DETOUR_Y, ANCHOR_CENTER_X, CR_DETOUR_Y, "F.Cu", "COLON_RET")
track(ANCHOR_CENTER_X, CR_DETOUR_Y, ANCHOR_CENTER_X, CR_JOG_Y, "F.Cu", "COLON_RET")
track(ANCHOR_CENTER_X, CR_JOG_Y, XS4_PAD2_X, CR_JOG_Y, "F.Cu", "COLON_RET")
track(XS4_PAD2_X, CR_JOG_Y, XS4_PAD2_X, XS4_ORIGIN_Y, "F.Cu", "COLON_RET")

# ---------------------------------------------------------------- assemble
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
setup = ['\t(setup', '\t\t(pad_to_mask_clearance 0)',
         '\t\t(allow_soldermask_bridges_in_footprints no)',
         '\t\t(tenting\n\t\t\t(front yes)\n\t\t\t(back yes)\n\t\t)', '\t)']
nets = ["\t(net %d \"%s\")" % (i, n) for i, n in enumerate(NETS)]

os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w", encoding="utf8").write(
    "\n".join(head + layers + setup + nets + out) + "\n\t(embedded_fonts no)\n)\n")
print("wrote", os.path.relpath(OUT, ROOT))
print(f"board: {W} x {H:.3f} mm")
print(f"INS1 leads:   Y={INS1_TOP:.3f} / {INS1_BOT:.3f}")
print(f"INS001 leads: Y={INS001_TOP:.3f} / {INS001_BOT:.3f}")
print(f"anchor:       Y={ANCHOR_Y:.3f}, two holes at X={ANCHOR_CENTER_X - ANCHOR_PITCH/2:.3f}/{ANCHOR_CENTER_X + ANCHOR_PITCH/2:.3f}")
print(f"R1/R2:        Y={R1_Y:.3f}/{R2_Y:.3f}")
print(f"XS4 origin:   Y={XS4_ORIGIN_Y:.3f}")
