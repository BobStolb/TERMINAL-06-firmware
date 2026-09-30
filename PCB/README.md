# TERMINAL-06 — custom PCBs

The fascia goes to Rezonit with the clock's electronics. For a small production run, the electronics are the through-hole pair **TS06-DISP + TS06-DRV**: tubes on one board, everything else on the one behind it, no vias on either. The one-board TS06-MAIN is kept, with its history. A tube board of the old kind is deliberately deferred.

| Board | Size | Stack | Status |
|---|---|---|---|
| **TS06-FASCIA** | 176 × 40 mm | 2.0 mm FR4, black mask, white silk, ENIG | Routed. The control panel AND the printed product face. One board, not two. Surface-mount build: no solder visible from the front. Height compressed from the original 52mm 2026-09 - see below. |
| **TS06-FASCIA-THT** | 176 × 52 mm | same stack, ENIG | Second build of the same board, routed. Through-hole, with the A6 divider ON the face. Pick one to fabricate; they are alternatives, not a pair. Not yet height-compressed (the SMD build was chosen for fabrication). |
| **TS06-DISP** + **TS06-DRV** | 191.4 × 44 mm + 191.4 × 100 mm | 1.6 mm, matte black | **The through-hole pair (25.09.26), the build for a small production run.** A display board with the tubes and nothing else, plugged by pin strips into a driver board behind it, the way AlexGyver builds his. **Zero vias on either board.** Both at rev B (30.09.26): TS06-DRV rev B is routed and merged, `tools/verify_pair.sh` gives 27 PASS, 0 FAIL, 0 SKIP, and the fab packages are in `../fab/`. Not ordered. See below. |
| **TS06-MAIN** / **TS06-MAIN-THT** | 176 × 96 mm | 1.6 mm, matte black | **The whole clock on one board**, two builds, one outline, one netlist. Placed and checked; routing in progress — see below. Replaces the inherited AlexGyver board, SEC and COLON. |
| ~~TS06-SEC~~ | 67 × 55 mm | 1.6 mm, matte black | **Superseded 17.09.26 by TS06-MAIN.** Surface-mount build routed and clean (1159 tracks, 79 vias); kept as the worked example of a hard placement and of the router. |
| ~~TS06-COLON~~ | 6.5 mm strip | — | **Superseded 17.09.26 by TS06-MAIN**, which carries the two ИНС-1 at the same measured positions. Placement only. |
| ~~TS06-TUBE~~ | — | — | **Deferred 08.09.26.** See below. |

## The two builds of the fascia

Same outline, same artwork, same netlist, same connector. They differ in one decision:
where the solder is.

* **TS06-FASCIA** — every pad is surface-mount on the back face. The customer sees black
  mask, white silkscreen and the decorative gold, and no joint anywhere. Routed with 64
  signal tracks, all on B.Cu, and **zero vias anywhere on the board** — F.Cu carries only
  the decorative gold, so no signal net can ever collide with it. GND is a pour over the
  back face, same as THT, and reaches all 7 GND pads on its own: R6 (the A7 pull-up) used
  to sit directly in the corridor the other five nets needed to reach J1, walling three
  GND pads (SW4.1, R8.2, R7.2) off from the plane with no B.Cu path a router could find at
  any trace width. Moving R6 out of that corridor — no other placement changed — opened it
  up enough that the pour alone closes the gap, confirmed by checking every GND pad against
  KiCad's own computed `filled_polygon`, not just this repo's simulated one. No stitch
  traces, no vias, nothing extra: placement fixed what routing couldn't.
* **TS06-FASCIA-THT** — the A6 resistor ladder is on the FRONT: five axial resistors above
  the rotary's seven landing holes, and the copper between them is bare, so the divider
  reads as a circuit rather than as decoration. Every other part is behind the panel with
  its front mask closed, so those holes show no gold ring. Routed with 34 tracks and no
  vias: the ladder on F.Cu under opened mask, six signals on B.Cu under mask, and GND as a
  pour over the whole back face.

`preview.svg` (`preview.png` too, where regenerated) in each board's folder is generated
by `tools/render.py` from the board file itself — front face and back face — so the board
can be looked at without opening KiCad.

**TS06-FASCIA height compression (2026-09).** The board felt oversized next to the tube
row, so it was cut from 52mm to 40mm tall. This was a pure translation, not a re-route:
every footprint, all 64 tracks, the GND pour and the silkscreen legend were shifted up by
a fixed 12mm (the dead margin above the control row - SR25's 12.5mm lever-throw keepout
was the real floor, not the visible knob bezel), then the board outline itself was
redrawn 12mm shorter. Nothing about the routing was redesigned, so R6's placement (still
load-bearing for the GND pour closing without vias, see above) is untouched. The two
mounting holes nearest the top edge are the one exception: they're anchored to the board
edge, not the control row, so they were NOT shifted, keeping their original 4.5mm inset
from the (new) top edge. All five checker tools pass clean and match the pre-compression
board's output exactly (same 2 pour islands, same 86% coverage, same 12-net agreement
with the schematic). One thing the pure translation did NOT fix on its own: the MODE
dial's decorative arc (position labels 1-6, their tick marks, and the "MODE" title)
was drawn for the old 26mm-radius-from-center clearance and clipped the new 14mm
budget - the checker tools don't validate silkscreen against the board edge, only
copper, so this needed its own pass. Fixed by rescaling the whole arc/tick/number
system by 0.789 (position 1, the tallest point, now sits at 12.5mm above center
instead of 15.84mm) and moving the "MODE" title from directly above the shaft to
its left, clear of position 1's tick - it was the single tallest element (19mm)
and didn't belong to the numbered fan, so it got its own placement rather than
being scaled with the rest. `checkpcb.py`'s rotary-keepout check had the rotary's position
hardcoded as a literal (30.0, 26.0) from the old layout - fixed to read the rotary
footprint's real position instead, since a checker that only works for one specific
layout isn't a checker. TS06-FASCIA-THT was not touched - the SMD build was the one
chosen for fabrication.

**Two leftovers of that compression, fixed 30.09.26.**
* **Five circles moved by half.** The compression moved each circle's end point up 12 mm
  but not its centre. The rotary's 25 mm body ring, on F.SilkS, would have printed as a
  34.7 mm ring 12 mm below the knob and run 3.3 mm off the bottom edge. Its four siblings
  (lever and button keepouts on User.1) had the same fault. These were the board's only 2
  KiCad DRC warnings. All five centres are moved up 12 mm, so each radius is horizontal
  again (12.5 and 12.0 mm). The body ring is back on User.1, where `tools/mkpcb.py` drew it.
* **A stale ground fill.** The stored GND fill reached 11.5 mm above the top edge, and
  Gerbers plot the stored fill. KiCad 10 refilled the pour and saved the board.

After both fixes:
* KiCad DRC: 0 violations and 0 unconnected, at every severity.
* `checkpcb`, `checkcopper` and `audit`: clean.
* `checkmatch`: agrees with the schematic.

**One picture outlived the fix.** `PCB/TS06-FASCIA-rhythm/composite-0-centred.png`, the
reference that the fascia variants are judged against, was drawn from a board older than
the ring fix. So it still showed the ring 12 mm below the knob, and the owner's review
reported it as "the SW1 white circle isn't centred on its hole". It is redrawn from the
fixed board. `tools/mkpcb_fascia_rhythm.py` now refuses to draw a composite from a board
whose F.SilkS ring encloses a control hole off-centre (`silk_rings_off_centre()`).
`tools/render_kicad.py` renders a board in KiCad 10 with the black mask and white silk
that are ordered.

**J1 pin order is fixed for both builds: 1 +5V, 2 GND, 3 A6, 4 A7, 5 D7, 6 D8.** It used
to be whatever the surface-mount routing preferred (D8, D7, GND, A7, +5V, A6). The
through-hole board cannot route to that order, and two builds of one product must not
need two different cables, so the pin order stopped being a layout convenience and became
a specification. The legend is printed on the back silkscreen of both boards.

## TS06-DISP + TS06-DRV — the through-hole pair (25.09.26)

**The clock as two stacked boards, the way AlexGyver builds his: a display board with the tubes
and nothing else, and a driver board behind it with everything else, joined by pin strips.**
Through-hole throughout, **no vias on either board**. The layout is designed as a whole, not
packed and then routed. This supersedes TS06-MAIN-THT as the build for a small production
run. TS06-MAIN (SMD) and its history stay as they are.

A critical review of the pair, and what it means for the case, is in
`../Claude outputs/TS06-pair-review.md`.

### Why two boards, and why these two

The one-board TS06-MAIN failed on the thing the owner cares most about:
* 476, then 339, then 177 vias;
* a ground pour in hundreds of islands;
* cathode switches squeezed into tube rings.

The split study (`../Claude outputs/TS06-split-study.md`) found an 18-wire cut. The owner chose
the Gyver cut instead: **tubes only on the display board**. The halves join the way Gyver joins
his, with a straight pin strip (PLS / рейка штыревая) on one board plugged into a socket strip
(PBS) on the other. No wires, no cable to make up.

That cut is what makes zero vias possible:
* The display board has no drivers, so its copper is only the tube wiring. The ИН-12 cathode
  bus can be threaded through the sockets on one face, as Gyver's tube half does it.
* The driver board has no tube fields, so every block can sit behind the strip pins it drives.

### Circuit changes for the pair (owner, 24.09.26)

| Change | Why |
|---|---|
| **ИН-15 pair on 2 × К155ИД1 + 1 × MCP23017** instead of 18 MPSA42 + 18 base resistors + 2 expanders | A symbol tube lights one glyph at a time, exactly like a digit, so a decoder does the whole job. 37 fewer parts, ~110 fewer joints. Firmware writes a code per tube; 10–15 blanks it. |
| **Every backlight LED addressable**: one MCP23017 port-B pin and one resistor per LED (RN1, an isolated 8 × 220 R network), cathodes common through the MPSA42 on D11 | A lit LED can show which tube's setting is being changed; D11 stays the global brightness PWM. |
| **A second К155ИД1 (U17) for the ИН-17 pair**, on the same A0–A3 lines | The display board delivers the ИН-12 bus and the ИН-17 bundle in the orders their tubes impose. One decoder feeding both would need a ten-line permutation, which two layers cannot make without vias. |
| **`BOARD_TYPE 4`** in the firmware | The pair's own digit map, `digitMask[] = {1, 0, 5, 4, 6, 7, 3, 2, 9, 8}`, and its own anode order `opts[]` (hours on D6/D5, minutes on D4/D3, S10 on D2, S1 on D13: the order types 1 and 2 use). The anode pins are the same six, driving different tubes, so the Nano's digital row fans out without crossing itself. |

Every other Nano pin keeps its function.

### The stack

**TS06-DISP**, 191.4 × 44 mm.
* **On its front:** 4 × ИН-12, 2 × ИН-17, 2 × ИН-15, 2 × ИНС-1 and 9 LEDs.
* **On its back, seven male strips:**
  * XP11 on the left edge (the ИН-12 bus);
  * XP12 on the top edge (31 pins: the ИН-17 bundle and both ИН-15, with 3 spares after pin 10);
  * XP21–XP25 on the bottom edge (anodes, colon, LEDs).

**TS06-DRV**, 191.4 × 100 mm, sits 11 mm behind the display on M3 standoffs (a standard 8.5 mm
PBS socket plus a 2.5 mm PLS body). Its seven socket strips are on its **back** face, towards
the display. Every other part is on its front, towards the back of the case, so nothing taller
than the strips lives between the boards. It has three bands:
* **The top band, 26 mm above the display:**
  * the Nano across the top-right corner, its USB proud of the edge;
  * the 12 V jack through the other edge;
  * fuse, polarity diode and 5 V regulator;
  * the 185 V converter in one tight loop, with its driver and control block beside it, and
    (rev B) an over-voltage clamp that stops the switch at 225-270 V without the comparator.
* **The tube band, behind the display:**
  * the three К155ИД1 for the ИН-15 pair and the ИН-17 pair under the top strip;
  * U2 beside the left strip;
  * the six anode channels as three cells over the bottom strips: two resistors and two optos
    per pair of tubes. Rev B draws the resistors for МЛТ-0,5 (15.24 mm), so the seconds' cell lays
    its two back to back in one row and the minutes' and hours' cells keep two rows 5.0 mm apart.
* **The bottom band, 30 mm below the display:**
  * the MCP23017 with its LED network stacked on port B;
  * the RTC module;
  * J1, the fascia connector. It is top-entry, so the cable leaves straight towards the fascia.
    Rev B's 1 k + 10 nF on D7 and D8 and 1 M on A6 sit between the strips and J1, each part on its
    own line's way in, so the lines still fan into J1 in its pin order
    (`recovered/drv-revb/OPTIONS.md`: placed as a block in front of J1, they stalled the route).

The strip order is a specification shared by both boards (`tools/ts06pair.py HEADERS`).
`tools/mkpcb_drv.py` proves three things: every XS pin lands on its XP pin, it carries the
same net, and every display standoff has its hole.

**Why 191.4 mm, not 176** (29.09.26). The two ИН-17 were first drawn 13 mm apart, as every board
before had them, but their Ø20 stems need 20.5 (the tube's outline drawing; concept Rev F). The
owner chose to widen the boards and keep the Gyver pitch:
* the ИН-12s and the colon did not move;
* the seconds pair now stands 20.5 apart, each stem 2.2 mm from the glass beside it;
* the ИН-15 pair moved 15.4 mm right.

XP12 stays one strip of 31 pins, with three spares where the ИН-15 group moved further than the
ИН-17 group. On the driver board, what sits behind the ИН-17s moved 7.62 mm, and what sits behind
the ИН-12s, with the Nano and U2, moved 15.4. It was then re-routed. The review has the finding.

### How the driver board has no vias

A through-hole pad is copper on both faces, so it is the only place a net may change face.
The driver board is placed so that every crossing happens in a part the circuit already has.
There are no wire links and no zero-ohm jumpers.

The long buses are laid by hand, each on one face:
* **Port A of the expander:** out of the bottom of U3, up the left edge, and east under the
  two ИН-15 decoders, as one eight-line bus. In every bend, the inner line turns first.
* **The LED ribbon:** from the network up into lanes under the bottom strips. The two lines
  to the hours' strip run on the front face, so the back face under the strips is free for
  the button lines to cross on their way to J1.
* **The U17 branch of A0–A3:** it leaves under the Nano and runs down a corridor beside it.
  It enters U17 between the chip's rows, the one approach that lands every line on its own
  pin; from below, the bus would arrive mirrored.
* **D9, D10, D12 and D13:** they share that corridor and end in four standing resistors at
  its exit. Their outputs leave on the other face.

The Nano's fan-out below the module is also laid by hand:
* **The digital row, on the back face,** in lanes just below the module:
  * D2–D4 go to the minutes' and S10's opto resistors, standing under the module's end;
  * D5 and D6 go to the hours' opto resistors, lying straight above their optos;
  * D7, D8 and D11 go down the gap between the hours' cell and U2.
* **A7, A6, SCL and SDA, on the front face,** come down the same gap and west between the
  hours' optos' pin rows. They end in one column of their filters and pull-ups, in the order
  they arrive, and change face there.

Everything else is routed by `tools/netroute.py`, which never places a via. It uses negotiated
congestion (PathFinder), with diagonals priced above two straight steps, so long runs come out
square with 45° corners. A polish pass then re-routes each net alone. The result is saved in
`tools/mkpcb_drv_routes.json`, so the board regenerates exactly.

### Assembly-friendly by design

* **Every part is through-hole**, on standard footprints read out of KiCad 10's own libraries
  (`PCB/lib/TS06.pretty`). Nothing needs hot air or paste.
* **Every IC is in a socket and the Nano is on two PBS-15 strips**, so a dead chip or Nano is
  a swap, not a desolder.
* **References are on the silkscreen** of TS06-DRV's component face, and (rev B) the legends a
  builder needs: the block names, the 185 V areas fenced and marked "DANGER 185 V", "12 V DC,
  centre +" at the jack, "HV SET" at the trimmer, "fit U12 before U11", "USB only with 12 V on",
  the RTC module's "- NC C D +" and its outline, J1's pinout and every strip's pin 1 on the face
  towards the display, and the title. All at the fab's floor: 1.0 mm text, 0.15 mm lines, off
  every pad.
* **No wiring harness between the boards.** The fascia cable (JST PH, spec pin order) is the
  only cable.
* **The anode channels are drawn from one pattern**, so a mistake in one is easy to see in all.
* **High voltage is kept in its own net class**, with 0.6 mm clearance enforced by KiCad's DRC
  from the project file. On TS06-DRV (rev B) every bare high-voltage pad keeps 0.8 mm
  (IPC-2221B table 6-1, A6) from all other copper on both faces, the ground pours included: a
  rule in `TS06-DRV.kicad_dru` that KiCad's DRC and zone filler apply, that the router routes to,
  and that `checkcopper.py --hv-pad 0.8` checks. Cathode pads keep 0.5 mm from other nets.
* **No copper within 3.8 mm of a standoff hole** on TS06-DRV (rev B), both faces: keep-out areas
  KiCad holds, clear of a 7 mm washer (3.5) and a 5.5 mm hex spacer's corners (3.18).

**Solder the strips while the two boards are plugged together.** See the review, finding 2.

### TS06-DRV rev B (30.09.26): what changed

Rev B closes the review's open items for the driver board (the review's second grill, E, M and R
rows). Rev A is 78105d6. The record of the work, with the routing choice, is in
`../recovered/drv-revb/` (`STATUS.md`, `OPTIONS.md`).

| Change | Parts | Review item |
|---|---|---|
| **An over-voltage clamp independent of U12:** a zener string (82 + 82 + 75 V) into an NPN that pulls PWM_G low. It starts at 225 V or more and clamps by 270 V at every tolerance (computed in `tools/ts06pair.py`, not measured) | VD5, VD6 (1N4762A), VD7 (1N4761A), R75 100k, R76 10k, VT2 2N3904 | E1 |
| **0.8 mm from every bare 185 V pad to all other copper**, both faces, the ground pours included: a rule in `TS06-DRV.kicad_dru` that KiCad's DRC and zone filler apply | - | E3 |
| **A USB back-feed diode** across the 5 V regulator | VD3 1N5819 | E5 |
| **An input TVS** after the fuse, so a 19-24 V adapter trips F1 | VD4 1.5KE18A | E8 |
| **The fascia inputs filtered and pulled down:** 1 M from A6 to ground, 1 k + 10 nF on D7 and D8 (J1 pins 5 and 6 are now D7_J and D8_J). Placed by hand between the strips and J1, each on its own line's way in | R72, R73, R74, C18, C19 | E11 |
| **0.5 mm from cathode pads to other nets**, with oval-pad sockets for the decoders | U2, U15-U17 | E10, R8 |
| **МЛТ-0,5 footprints** for the 0.5 W resistors: 1.1 mm holes at 15.24 mm | R27-R32, R56-R63 | M4 |
| **A real L1:** Bourns 5900-221-RC, 220 µH, 1.8 A, axial, lying | L1 | E4, M2 |
| **The RTC module on a male PLS-5**, its outline and the "- NC C D +" legend drawn | U13 | M1 |
| **Larger holes** for VT21 (1.2 mm) and J1 (0.85 mm) | VT21, J1 | M7 |
| **No copper within 3.8 mm of a standoff hole**, as KiCad keep-out areas | H1-H8 | M12, R1 |
| **Silkscreen legends at the fab's floor** (1.0 mm text, 0.15 mm lines): block names, the 185 V fences, the jack, the trimmer, the bring-up order, J1's pinout | - | M8 |
| **The DNP attribute** on the bleeders | R33-R44 | R13 |
| **A reproducible route:** the router pins its hash seed, and a fresh `--route` rebuilds the saved route byte for byte (2aec60c) | - | R6 |

**What rev B scores against rev A** (`scorecard.py`, from the board files alone):

| | Rev A (78105d6) | Rev B |
|---|---|---|
| Segments / vias | 1097 / **0** | 1164 / **0** |
| Signal copper / its floor | 5936 / 4479 mm = 1.33 | 5918 / 4533 mm = **1.31** |
| Straight (0°/90°) share | **86.1 %** | 83.3 % |
| DIP orientations | 3 | 4 (U11, below) |
| Case depth (the case model) | 83.6 mm | **81.6 mm** |

**U11 now stands at 0°, a fourth DIP orientation.** In rev A the TC4420 stood at 180°, like U12
and U2. Rev B's placement came from the work recovered after the layout agent was lost, and it
puts U11 at 0°, moved from (81, 20.7) to (57, 14.8) in the board's frame. It is not on the change
list above. The board passes every check with it, but a fourth orientation is one more way to
fit a socket backwards (review, finding 5). Whether to turn it back is the owner's choice;
turning it moves its pins, so the board would be routed again.

**The case is 81.6 mm deep, not 83.6.** The case model now reads the new footprints' real
heights. With U13 on a male header, C7 (20 mm, worst case) is the tallest part, 5.0 mm clear of
the rear panel.

### Checked

`tools/verify_pair.sh` runs every check below on both boards in one command, with the accepted items
listed in its header. `TS06-pair-testing.md` explains it for the owner, with how to view the boards
and the staged bench bring-up. Two of its checks read the written files with KiCad's own geometry
(`tools/kicad_checks.py`, under the KiCad image's Python):
* **`mate`:** all 63 strip pins and the 4 standoff holes, with their positions, nets, drills
  and faces;
* **`fill`:** the pours as KiCad fills them.

**The committed boards store no zone fill.** Refill before plotting Gerbers: press B in the PCB
editor, or use `kicad-cli pcb export gerbers --check-zones`. TS06-DISP's LED return, BL_K, is a
pour with no tracks, so a Gerber plotted unfilled leaves all nine LEDs open. `tools/mkfab.sh`
builds the fab packages that way (`../fab/`, grill.md G8) and checks that every poured copper
layer's Gerber carries its pour regions. Filling the committed files is the owner's decision.

**`tools/verify_pair.sh` on rev B (30.09.26, after 2dc04ec): 27 PASS, 0 FAIL, 0 SKIP.**

`checkcopper.py --hv` is run with the pair's HV list, `ts06pair.HV_PATTERNS`:
`HV185,SW,BLEED_*,FB_MID,COLON_*,ANODE_*,EMIT_*`. The cathode nets have their own class,
CATH, at 0.25 mm.

Both boards are generated from `tools/mkpcb_disp.py` and `tools/mkpcb_drv.py` and pass every
board checker in this repo, plus KiCad 10's own DRC (`kicad-cli pcb drc --refill-zones`, HV class from
the project file). Since 30.09.26 the pair has schematics as well, generated from the same netlist by `tools/mksch_pair.py`, one sheet per section. `checksch.py` finds no dangling pin, `checkmatch.py` agrees net for net with each board (136 nets on rev B's TS06-DRV, 59 on TS06-DISP), and KiCad's ERC reports 0 violations at every severity. `verify_pair.sh` runs all three.
The results as of 30.09.26 (TS06-DRV rev B), on the widened boards:

| | TS06-DISP | TS06-DRV |
|---|---|---|
| Tracks / vias | rev B (30.09.26): 388 / **0** | rev B (30.09.26): 1164 / **0** (373 laid by hand, 791 routed); rev A 1097 / 0 |
| Copper, and its ratio to the placement's floor | 2125 mm, 1.15× its 1851 mm floor. Like for like with TS06-DRV: signals only, since BL_K is poured and has no tracks (the 1.04× given before counted BL_K's 164 mm in the floor; rev A was 1.14× on this basis) | 6689 mm: 5918 mm of signals, 1.31× their 4533 mm floor, and 772 mm of ground tracks under the ground pours (rev A: 5936 mm, 1.33× 4479 mm) |
| Straight (0°/90°) share of the copper | 53 % | 83.3 % (rev A 86.1 %) |
| DIP orientations | - | 4 (rev A 3): U11 now stands at 0°, from the recovered placement and not on rev B's change list; the owner decides whether to turn it back |
| Ground pours as KiCad fills them | BL_K: 1 piece | GND: 15 pieces on the front (the largest 92 %), 10 on the back (the largest 33 %); rev A 13 and 14 |
| Case model (`3d/case-pair`) | the pair's case: 204.4 × 122.8 × 81.6 mm outside | 81.6 mm deep (rev A 83.6): C7 is the tallest part, 5.0 mm clear of the rear panel |
| Routing | drawn by hand; every bare 185 V pad 0.8 mm from other copper (IPC-2221B A6), every cathode pad 0.5 mm, no copper within 3.8 mm of a standoff hole | converged in negotiated routing: round 13, 0 nets sharing, 0 unrouted; then polished (30 nets shorter). PYTHONHASHSEED pinned to 0 by the script: a fresh `--route` reproduces the saved route byte for byte (checked 30.09.26); the saved route is the source. Every bare HV pad 0.8 mm from other copper (the `.kicad_dru` rule, proved live), 0 cathode pads under 0.5 mm, no copper within 3.8 mm of a standoff hole |
| `check_mate()` | — | `[]`: all 63 strip pins (59 carry a net) land on their pins with the same net, all four display standoffs have holes |
| `checkcopper.py --hv` | clean | clean |
| `audit.py` | clean; BL_K in one piece | clean |
| KiCad 10 DRC | **0 unconnected**, 0 warnings, 2 errors, accepted, awaiting the test fit: the colon lamps' courtyards overlap the M10 tube's by 0.135 mm. Run with `TS06-DISP.kicad_dru`, the A6 rule (0.8 mm, HV pad to any other net), which the pour fill honours too | **0 errors, 0 unconnected**, 2 warnings: the Nano's USB outline stands past the edge by design. Run with `TS06-DRV.kicad_dru`, the A6 rule (0.8 mm, HV pad to any other net) |
| `checkpcb.py` | H3's courtyard 0.15 mm past the top edge; XP11's 0.17 mm past the left edge (the mirror of XS11); the two colon overlaps | the Nano's courtyard past the edge (its USB, by design); XS11's 0.17 mm past it (the strip sits where the display's XP11 is) |

A second, independent model checks the boards as objects too: the case model in `3d/case-pair`
reads both generators and tests the tubes, strips, standoffs, tall parts and connectors against
the case. It is what found the ИН-17 spacing. Its check of the pair now reads stem to stem
0.5 mm, and 2.2 mm to the glass either side.

The same checks against the display's standoffs caught one thing no courtyard check sees: a
standoff and a strip body share the 11 mm gap. H4 was moved 2 mm to clear XP12 (review, finding 1).

### Open before fabrication

* **Bench gates:** the ИН-17 lead order, the ИН-15 pinouts, the ИН-17 pip and the RTC module
  (rev B draws the module lying beside its PLS-5; check its body falls on the outlined side).
* **Rev B on the bench:** with U12 out of its socket and RP1 at either end, the OV clamp must
  hold the rail between 225 and 270 V (typically ~242 V; computed from the parts' tolerances, not
  yet measured) - bring it up on a current-limited 12 V supply with C7 bled. L1 is the Bourns 5900-221-RC (axial, 1.8 A): check the supplier's
  datasheet revision before ordering.
* **Parts to measure:** the PBS and PLS heights of the batch being bought.
* **Test fit:** the colon lamps against the M10 glass.
* **The owner's decisions:** whether rev B is the board for the prototype, and whether U11 turns
  back to 180° (rev B stands it at 0°, a fourth DIP orientation); the prototype order (grill.md
  G14); filling the committed boards (G8, first half). The fab packages are built (`../fab/`).

Cathode-order surprises are firmware tables. Only anode identity and the RTC pin order are
copper. On the firmware side, `BOARD_TYPE 4` now runs the pair: six slots, the "m" LED, the
expander, and the MODE rotary as PROGRAM/RUN. The rotary's other screens, the levers on A7 and
the ИН-15 content are still to write. The review has the list.

## TS06-SEC — seconds and AM/PM

Generated by `tools/mkpcb_sec.py`: placement, then routing by `tools/pcbroute.py`. A full
run takes about five minutes. The generator's docstring carries the reasoning in full; in
short:

* **67 × 55 mm, not the spec's 46 × 34.** The tube centres are not a layout choice — they
  come from the reviewed 8-tube assembly (`3d/Clock.FCStd`). The four tubes span 66 mm and
  their glass covers most of the front, so everything but the tubes, the three LEDs and the
  connectors mounts on the back. The ИН-17 at V5 overhangs the left edge by 1.37 mm (its
  glass, standing on its leads, not the board); `checkpcb.py` reports that courtyard, and it
  is accepted.
* **What it carries:** 2× ИН-17 and their TLP627 anode drivers; 2× ИН-15 (V9 ИН-15Б for AM,
  V10 ИН-15А for PM) with 18 cathode channels — two MCP23017s and eighteen MMBTA42s, one per
  real cathode; the colon switch (the colon board arrives on XS4); two amber backlight LEDs
  for the ИН-17s and the "m" LED HL3. XS1 is 185 V in, XS2 the ИН-17 cathode bus (IDC 2×5),
  XS3 the logic connector.
* **High voltage is its own clearance class:** 0.6 mm around the 185 V feed, the tube
  anodes, the TLP627 emitters, the bleed mid-points, every ИН-15 cathode and the colon
  return. The ИН-17 cathode bus is not in it: the К155ИД1 outputs clamp near 60 V, and the
  tube's own pins sit 0.9 mm apart.
* **79 vias — the first board in the family with any.** Four tube pin fields, ~90 nets and
  every part on one face of 67 × 55 mm do not route on two layers without them. The router
  charges each via as much as 15 mm of track, so each one is a detour it could not find.
* **Routing.** The high-voltage locals are laid first. Everything else — the ИН-17 bus, the
  185 V feed, the 5 V signals, +5V and GND — is negotiated at once in the manner of
  PathFinder, because laid one net at a time they walled each other in: the 185 V feed cut
  the back face in two, and the bus, laid early, boxed in the backlight LEDs.
* **GND is a routed tree and a pour on each face.** The pours alone left GND pads in
  pockets that signal tracks had closed on both faces — `audit.py` and KiCad's refilled DRC
  both said so — so GND is routed from XS3 like any other net, and the pours fill whatever
  the tracks leave. Surface-mount pads join the pours solid, through-hole pads by spokes;
  HL3's GND pin joins solid too, because tracks leave no room there for two spokes.
* **Checked:** `checkcopper.py --hv "HV185,CAT_*,ANODE_*,EMIT_*,BLEED_*,COLON_RET"` clean,
  `audit.py` clean (both pours), KiCad 10 DRC with zones refilled clean at every severity;
  `checkpcb.py` reports only the V5 overhang above. There is no SEC schematic yet, so
  `checksch.py` and `checkmatch.py` do not apply.
* **Footprints corrected on the way:** `TS06_IN12_Socket` and `TS06_IN17_Socket` were
  mirrored in Y; the ИН-12 socket's description carried raw quotes that stopped the whole
  `TS06.pretty` library loading; the ИН-17 pip hole is gone — the ТУ's 8 mm soldering rule
  holds the glass at least 6.4 mm off the board — and its silkscreen outlines were redrawn
  clear of the pads.
* **Still open:** the through-hole build (tube board plus a stacked driver board); a bench
  check of the ИН-15 pinouts (taken from tec.org.ru and rudatasheet.ru, which agree) and of
  the ИН-17 pip's projection, which must be under 6.4 mm; HL3's position is provisional; and
  the fascia was drawn around the old SEC outline, to be revisited.

## Checking

Nothing here is checked by KiCad until it is opened in KiCad, so five tools check it
first. Run all of them after any change to `tools/mk*.py`:

    python3 tools/checkpcb.py   <board>.kicad_pcb    # placement, keepouts, front copper vs pads
    python3 tools/checkcopper.py <board>.kicad_pcb   # clearance and per-pad connectivity
    python3 tools/audit.py      <board>.kicad_pcb    # per-net connectivity, pour fill, silkscreen
    python3 tools/checksch.py   <board>.kicad_sch    # dangling pins and the net list
    python3 tools/checkmatch.py <board>.kicad_sch <board>.kicad_pcb   # the two files agree

`checkcopper.py --hv NETS` (a trailing `*` matches every net with that prefix) holds 0.6 mm wherever a listed net is on
either side of a gap, and keeps copper 0.25 mm from unplated holes. `audit.py` checks a
poured net as one net across both faces — pour islands, pads, tracks and vias together — so
a back-face pad that reaches a front pour through a via is checked rather than skipped; a
round pad is cut out of the pour as a circle, not its bounding square; and two vias of a net
count as joined only where their copper touches. `checkpcb.py` reads each courtyard graphic
as a whole block and compares courtyards only between parts on the same face.

`checkmatch.py` is the one that matters most and was written last: every other tool can
pass while the schematic and the board disagree about what they are connecting.

All five tools, plus `render.py`, read `.kicad_pcb` files two different ways depending on
who last saved them: this repo's own `tools/mk*.py` generators outdent each `(footprint
...)` block to column 0 and always number net references, while the real KiCad 10 install
this board gets edited in indents footprints normally *and* writes every net reference —
pads, tracks, vias, the zone itself — as a bare name with no code at all, no matter how
many times the file gets saved. Every tool here parses both forms; nothing needs
reformatting by hand before a check runs, and nothing should ever again. If a check comes
back suspiciously empty (`0 footprints`, `no tracks or vias`) after a real KiCad save, that
means a *new* variant slipped through, not that the board is broken — fix the parser, not
the file.

`IN-12_norm/` is the inherited AlexGyver/itworkclub board's fab data, kept as reference.
`lib/` holds project-local symbols and footprints — nothing here relies on a stock KiCad
library, because none of the Soviet panel hardware has one.

## Why TS06-TUBE is deferred

Three reasons were ever offered for fabricating a custom ИН-12 tube board. Only one is
still alive, and it is not an electrical one:

1. **Four anode bleed resistors need a home.** **Withdrawn 06.09.26** — the ghosting root
   cause turned out to be empty multiplex slots (spec §5a-pre), not the anode drivers.
   Dead reason.
2. **The socket pin pattern.** **Not a reason.** The footprint is fully known from the
   inherited board's Gerbers — see `../TERMINAL-06-measurements-PCB-IN12BOARD.md`. The
   tube defines the pattern, so any socket that fits the tube fits those holes.
3. **Deck geometry — the only live reason.** Tube pitch (23.36 / 27.42 / 23.36 mm), deck
   height, forward offset and rake are all fixed by someone else's layout. Spec §6's
   "Brow reveal" note is the argument: the brow was sized to clear the 18.63 mm digit, but
   the envelope is 28.70 mm, so ~10 mm of glass sits behind the top deck.

**Against it:** ten main boards are already owned, therefore ten tube halves are already
owned. TS06-TUBE is ~1 425 ₽/unit of Group D that does not have to be spent.

**Decision rule: print a brow, test-fit it against a real tube, and see whether the case
alone gives the reveal.** Do not order copper to fix a plastic problem. Revisit only if
the test-fit fails.

## TS06-MAIN — one board for the whole clock (17.09.26)

The three-board electrical stack (inherited AlexGyver board + TS06-SEC + TS06-COLON) is
replaced by **one board carrying every tube, every driver, the Nano, the RTC and the 185 V
converter**, in two builds like the fascia: **TS06-MAIN** (surface-mount wherever a part
exists in that form) and **TS06-MAIN-THT**. Same outline, same netlist, same connectors;
one gets fabricated. The brief is `../Claude outputs/TS06-MAIN-handoff.md`.

**Decisions taken by the owner on 17.09.26**, answering the brief's open questions:

| Question | Decision |
|---|---|
| Power input | **12 V on the same 5.5 × 2.1 mm barrel jack the stock board uses, not 5 V**: the stock converter is an energy-limited stage good for ≈1 W and the full clock needs ≈3.5 W (see `../TERMINAL-06-measurements-PCB-GYVER-NETLIST.md`). An R-78E5.0-1.0 switching regulator feeds the 5 V rail. The Nano's USB is reachable through the left edge, for reflashing and for a PC time-set link; USB alone runs the logic with the tubes dark. |
| MCU | Arduino Nano on headers in **both** builds. |
| RTC | Bare DS3231SN with a CR2032 holder in the SMD build; the owner's **DS3231 mini module** (pins − NC C D +, the same header the stock board carries) on a 5-way header in the THT build. The one place the two netlists differ. |
| Tube positions | The reviewed coordinates, Gyver pitch included, unchanged. The board is sized for itself; the fascia is not a width constraint (it happens to be 176 mm too). |
| Anode chain | One series resistor per digit tube (the stock board has a single shared 10 kΩ) plus DNP bleed footprints on all six. 6k8 for the ИН-12s is a design value until bench gate 2. |
| Optos | Six TLP627 singles. |
| "m" LED | HL9 on the free D12 through its resistor, so always-on versus 12-hour-only is a firmware choice. |
| Backlight | Eight amber LEDs, the ИН-15 pair included. |
| Layers | Two. Vias budgeted, not hunted. |

**How it is built.** `tools/ts06main.py` is the netlist both builds share — every part,
pin and net, with the display chain, the AM/PM section and the colon carried over from the
inherited copper and SEC, and the converter redesigned: 12 V in, the same 220 µH / 31 kHz
boost clocked from D9, but through a TC4420 driver, with an LM393 watching the rail through
a 1.5 M / 20.5 k divider and holding the driver off whenever the rail is above the set-point
(152–252 V on the trimmer). `tools/mksch_main.py` draws it as a labelled netlist grouped by
function into `lib/TS06M.kicad_sym`; `tools/mkfp_main.py` adds the footprints (every land
pattern read out of KiCad 10's own libraries, back-mounted and pre-rotated as this repo does
it); `tools/mkpcb_main.py` places and, with `--route`, routes either build; `tools/bom_main.py`
writes each build's `bom.md`.

**Where things are.** The board is vertical in the plane the inherited tube board
occupied, tubes on the front, everything else on the back. World coordinates are the FreeCAD
assembly's; board local (x, y) = (world X, 100 − world Y), so the board runs from world Y 100
down to 4 — the extra height is below the tubes, behind the fascia, where the through-hole
build needs it. Three bands on the back: the logic band above the tube rings (Nano across the
top left with its USB 2.4 mm proud of the left edge, the converter, the two ИН-17 anode
switches, the AM/PM small parts above the ИН-15 rings), the tube band (bleed pairs inside the
ИН-12 rings, ИН-15 cathode switches inside their rings), and the power band below the LEDs
(the four ИН-12 anode switches under their tubes, the 12 V jack at the left edge, the
converter's control loop, the fascia cable at the bottom edge, the decoder, the RTC, the two
expanders under the ИН-15s).

**Checked.** Both placements pass `checkpcb.py` except three intended items — the Nano's USB
connector proud of the edge, and the two colon lamps' courtyards touching the M10 glass
courtyard by 0.3 mm at their measured positions — and `checkcopper.py --hv` finds no bare
pad pair inside the high-voltage clearance. Both schematics pass `checksch.py` with no
dangling pin, KiCad 10 loads them, and **KiCad's own netlist export agrees with the netlist
module net for net** (141 nets in the SMD build). `3d/Clock.FCStd` now carries the board
(`3d/TS06-MAIN.step`, KiCad's export) in the tube plane with the two inherited halves and
the colon board switched off.

**Routing, 18.09.26.** Three stages and a retry, and the ORDER is most of it. High voltage
first including the 185 V trunk, then GND as a tree while there is still room, then everything
else negotiated at once, then one more try alone at whatever was dropped. Five other orders were
tried and every one is worse; each is recorded beside its decision in `tools/mkpcb_main.py`.

The rest is the cost function, and it was rebuilt after the first routed board turned out to be
legal and badly routed at the same time — 476 vias, no grain at all, a ground pour in 292
islands, and every checker in this repo quiet. Ten rules were implemented, each switchable, each
run against a control; twenty-two configurations were measured. `../Claude outputs/TS06-routing-study.md`
has the table and the reasoning, including the two ideas of mine that turned out to be wrong.
What is kept: a face grain (F.Cu east-west, B.Cu north-south), a via priced honestly at 9 mm of
track instead of 2.5, a relaxation that lets a net off the grain when it keeps failing, two
passes of rip-up-and-reroute for length, and an exemption that frees any net with eight or more
pads from all of it. What is implemented and off, with numbers: compaction, bundling, the
return-path rule, T-junction discipline, the via lattice, history decay.

| | TS06-MAIN | TS06-MAIN-THT |
|---|---|---|
| Tracks / vias | 2852 / **339** (was 3047 / 476) | 2340 / **177** (was 2823 / 271) |
| Nets not connected | **0** (was 1) | **13**, unchanged |
| Copper | 8726 mm at 1.23× its floor | 7403 mm at 1.30× |
| Grain, front / back | **49 / 11**, **46 / 13** (was 33 / 25) | **44 / 14**, **43 / 13** (was 26 / 33) |
| GND through copper alone | 3 pieces; the pour closes one | **whole** |
| `checkmatch.py` | agrees, 141 nets | agrees, 140 nets |
| `checkcopper.py --hv` | **clean** | 87 items, all pads of the 13 split nets |

**The surface-mount build routes completely.** Every signal net is connected — the VT2 base that
used to be split is routed — and `checkcopper.py --hv` finds nothing at all. `checkpcb.py` still
reports the same three intended items as before: the Nano's USB proud of the edge and the two
colon lamps touching the M10 glass courtyard by 0.3 mm.

**Its one remaining defect is two ground pads,** and it is now understood. VT10.2 and VT11.2, the
emitters of two ИН-15 cathode switches, sit inside a socket ring and cannot be reached. The
ring's PADS are not the fence — they leave 1.9 to 2.5 mm between them and a 0.2 mm track between
two 185 V pads needs 1.4 — it is stage 1's twelve cathode TRACKS, which leave the ring through
those same gaps with a 0.6 mm halo each and never move.

Letting them out first works and costs too much, measured twice: all twelve in-ring GND pads
given a stub before the high voltage gives a whole ground and **24** signal nets overlapping;
only the two the high voltage actually walls in gives a ground in two pieces and **7** signal
nets lost. Seven signals for two grounds is a bad trade, so it is not made. Those two emitters
need a wire link, or the switches moved out of the ring — itself measured, and worse (3 nets
unplaced became 13). Widening the in-ring switch spread does not help either: the escape
corridor measures the same at 4.7, 5.2 and 5.6 mm, because the barrier is the tracks.

This defect was in every board this project has made. It was hidden by a stage-2 retry that
offered a stranded pad the three nearest GND pads **regardless of whether they were themselves
connected**: the two are 4.4 mm apart, each was offered the other, the connection succeeded and
both were counted saved. The retry now only anchors on pads that reach the hub, and the routing
log prints how many pieces the copper alone joins GND into before the pour is given any credit.

**The through-hole build is still not routable as placed.** The new rules improve its copper
markedly — 177 vias against 271, and a grain of 44 / 14 where it used to run more across than
along — but they do not touch its connectivity: 13 nets are split either way, including the I²C
pair, the backlight return and one cathode line. Through-hole pads block both faces, so there is
far less room. It is the alternative build and only one gets made, so this does not block the
surface-mount board. What it needs is a placement pass, not a router.

**And the router was not the main thing wrong.** `tools/placecheck.py` measures what a placement
costs before any routing: the Euclidean MST over each net's own pads, which no router can beat.
The Nano sits in a corner with 28 connections reaching across a 176 mm board, and the decoder
sits 40 mm above the row of tubes it drives, so each of its ten cathode lines pays that detour
twice. Sliding the Nano along the edge it is already pinned to — USB unchanged — is worth 7.4 %
of the floor, and moving the decoder onto the tube row beside it takes it to **16 %**. That is
five times what every routing rule put together achieved. Both positions collide with tube
sockets as they stand, so it needs a real placement pass.

`tools/boardsplit.py` prices the other way out, the one the inherited board took: a display board
and a driver board joined by **18 wires** — three power, four BCD, six ИН-12 anodes, SDA, SCL,
the backlight cathode and two spare Nano pins. `../Claude outputs/TS06-split-study.md` has the
curve and the case either way. It agrees with the placement finding: both say the decoder belongs
beside the tubes.


**The bench still owes** the items in `../knowledge/TERMINAL-06-measurements-TS06-MAIN-gates.txt`:
the stock stage's operating point, the sustaining voltages, the ИН-17 lead order, the ИН-15
pinouts, the pip projection, the mini module's battery, the adapter.
