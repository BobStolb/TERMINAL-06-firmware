# TS06 fascia science-2-3 Double slit: the grill (can it be built, will it work)

2026-10-15, run grill-scicel. The owner (00:0x UTC): "run grills on all, compile insights for the final pcb routing plan".
science-2-3 is a final candidate, not approved. This page reviews it and proposes fixes. It applies none: no board, schematic,
fab, tool, 3D, firmware or spec file was touched, and the face ([TS06-FASCIA-science-2.md](TS06-FASCIA-science-2.md) section 4)
is unchanged. The scripts are scratch, not in the repo. There is no marked picture (the owner dropped it); the doc is the grill.

The model is [the K4W411 grill](TS06-FASCIA-K4W411-grill.md). What it settled for every fascia is cited as "K4W411 #n applies"
in one line. Only what is new or different for this face is written out.

Marks:
* *measured*: read from a repo file (board, case model), or from the face run's own geometry (its window polygons, rebuilt
  with its own script, rastered at 40 px per mm; its art layers at 23 px per mm).
* *inferred*: arithmetic on measured numbers.
* *assumed*: my reading, or a value nobody has measured.

Frame: fascia R's own KiCad frame, front view. Origin at the board's top-left corner, x right, y down, mm. The board is
191.4 x 40 (rev B's Edge.Cuts, *measured*). "Rev B" is the ordered board, `PCB/TS06-FASCIA-rhythm/TS06-FASCIA-rhythm.kicad_pcb`.

## Verdict

**Buildable after changes, as K4W411 is. Two things are new and both sit in the bottom band, where the screen is:**

* the screen (S) is a light place no other face uses, and on rev B its windows and its bar sit on the A6 track;
* the screen's lobes are 6.5 mm tall over a 2 mm bar, so as drawn they will not glow evenly.

The art itself has two fab faults the face run's checks did not catch: the plane wave's white lines come out 0.13 mm (under
0.15), and the zone seams leave hairline slivers. Both are fixed in the export, not on the board. K4W411's one blocker (#5, the
key arcs against the buttons' boxes) applies here unchanged.

| # | Item | Rating |
|---|---|---|
| — | K4W411 #1 (no PWM chip on DRV), #3 (J2), #5 (key arcs vs the boxes), #9, #10, #13, #15, #16 | as K4W411 |
| 1 | The nine lights, end to end; channels | OK (5 channels, 180 mA) |
| 2 | The screen is a new light place, off the common base | Needs X |
| 3 | Rev B's A6 track under the screen | Needs X |
| 4 | The screen's leads cannot reach J2 without crossing A7 | Needs X |
| 5 | The slits' light (P): no form drawn; the top band; clips; lead pads | Needs X |
| 6 | The base windows on rev B copper; the lever and key forms | K4W411 #4 and #7 apply |
| 7 | The bottom band and the case | OK |
| 8 | The plane wave's white lines: 0.13 mm | Needs X |
| 9 | Slivers at the zone seams | Needs X |
| 10 | The screen's glow: 6.5 mm lobes over a 2 mm bar | Needs X |
| 11 | The lobes' webs; bleed; hot spots | OK (per-lobe cuts) |
| 12 | One warm, two products (yellow flex, warm-white bars) | Needs X (bench) |
| 13 | The path to a board | Needs X |

## 1. Light sources and connection, end to end

### Finding 1. The nine lights (OK)

The face keeps the base's seven arcs and moves the two info lights (section 4 of the face's doc). Every light is warm.

| Light | Window (*measured*) | Sold part, colour | Held by | Channel (K4W411's J2 map) |
|---|---|---|---|---|
| MODE arc | r 14.2 about (24.89, 16), 130 to 230 deg | 38 flex, warm (the flex is sold as "yellow") | arc clips; over-length folded back (K4W411 #7) | CH1 |
| FIELD up, down | r 10.6 about (63.99, 16), 50 deg each | 18.5 rigid, warm white, level on the chord (or 38 flex) | two clips each | CH2 |
| SUB up, down | the same about (87.37, 16) | the same | two clips each | CH3 |
| Key - arc, key + arc | r 10.0, 150 deg each | 38 flex, warm (yellow) | arc clips | CH4 |
| **S, the screen** | five lobes, x 111.59 to 126.19, y 31.21 to 37.71, 28.8 mm² | 18.5 rigid, warm white, level at y 37.0, x 109.6 to 128.1 | two end clips | CH5 |
| **P, the two slits** | 0.8 x 4.6 each, x 159.51 to 162.31, y 3.56 to 8.16 | not drawn ("P's tail, as the base"); I propose the common P bar: 18.5 rigid, warm white, level at y 6.3, x 151.65 to 170.15 | two clips (finding 5) | CH5 |

* **Wiring:** K4W411 #3's way applies. Each light has its own 120R on the fascia's back to +5V_L, and each channel's
  cathodes join at one J2 pin.
* **Current** (*inferred*, 20 mA a light, front-merge's rating): CH1 20, CH2 40, CH3 40, CH4 40, CH5 40 (S and P). **180 mA**
  in all, nine lights, the base's count less C.
* **Sharing:** S and P are the same colour and were always one info channel, so they share CH5 with a resistor each (K4W411 #2
  applies). Every light is warm, so colour never forces a channel. Behaviour does: MODE, FIELD and SUB light by state. On 3
  channels (the base's: MODE + FIELD + SUB, the keys, S + P) nothing changes in colour; only the arcs lose lighting one at a time.
* **DRV:** K4W411 #1 applies (no PWM chip, no fascia connector on rev B). This face needs no channel K4W411 does not.
* **5 V:** 20 mA less than K4W411 (nine lights, not ten). Nothing new.

### Finding 2. The screen is a new light place (Needs X)

K4W411 and celestial-3 put S in the pill, level at y 8.35 (kawaii-2's place). This face puts S 28.65 mm lower, under the
seconds' zone, at y 37.0 (*measured*: the face's script). The owner's rule for the routing plan is "windows differ per fascia,
the sources and pads stay". The screen's bar cannot be the pill's bar: the lobes are 23 mm from it.

* **Fix:** the common base carries a second S place: two pads, one resistor place and one route, fitted only on the faces that
  use it. A pad pair costs nothing on boards that leave it empty.
* **Pads** (*measured* by a search that keeps 0.3 off every window, light body, rev B back copper and control body; 1.5 x 1.5,
  B.Cu): at the bar as drawn, (107.59, 37.26) and (130.14, 37.26). At the raised bar of finding 10, (107.59, 34.96) and
  (130.14, 34.96).
* **Cost:** 2 pads, a 1206 place, the route (finding 4).

### Finding 3. Rev B's A6 track under the screen (Needs X)

* On rev B, A6 runs level on the back at **y 36.10 from x 62.30 to 147.70** (0.25 wide, *measured*). It crosses all five
  lobes 1.6 mm above their base: 1.58 mm² of copper inside the windows (*measured*).
* The screen's bar (y 36.0 to 38.0) lies on it for its whole length. The +5V track runs at y 39.00 below, 0.875 from the bar's
  body (*measured*). That one is clear.
* On `R-open` (rev A) A6 ran at y 33.70: also through the screen (*measured*).
* The face run did not check the back (its doc, section 8: "Not checked against the back's copper").
* **Fix, my pick:** jog A6 down under the screen: level at **y 38.35** from about x 108 to 130, with a 45-degree step at each
  end. It then keeps 0.52 mm to the lobes' foot (37.71) and 0.40 mm to +5V (y 39.0, edge to edge) (*inferred*). This needs
  the raised bar of finding 10: the pads of the bar as drawn reach y 38.01, 0.2 from the jogged track. The screen's pads are then open upward,
  with only A7 between them and J2 (finding 4).
* **Other way:** jog A6 up over the screen, level at y 30.0 (1.1 mm to the lobes' top, 3.55 to A7). Then the screen sits in a
  pocket under A6, and its leads must cross A6 and A7.
* The back pour is cut per lobe (finding 11).
* **Cost:** one re-route of about 25 mm. No front change.

### Finding 4. The screen's leads cannot reach J2 without crossing A7 (Needs X)

* On rev B's one back layer, A7 runs level at y 26.2 from x 90.0 to 139.1 and then down to J1; A6 and +5V run below it to J1
  (*measured*). Every track in the bottom band ends at J1 (155.4, 33.0).
* K4W411's J2 spot (a) (x 130.5 to 139.0, y 5.5 to 24.9) is above A7. The screen's pads are below it. So the screen's two
  nets (+5V_L in, CH5 out) must cross A7, and A6 too if A6 stays between them.
* K4W411's spot (b) (x 100 to 120, y 27 to 35.5) sits on the screen's lobes (x 111.59 to 126.19, y 31.21 to 37.71): not usable
  with this face.
* **Fix, my pick:** with A6 jogged down (finding 3), only A7 lies between the screen and J2. Two 0R jumpers (1206) hop it, one on
  each of the screen's routes. With A6 jogged up instead, each route crosses two tracks 3.8 mm apart: a 1206 cannot span both,
  so that costs four jumpers or two long ones.
* **Other ways:** a via pair and a front hop under the screen's calm ground (the art is plain mask there, so a masked track
  shows only as a faint ridge, *assumed*); or J2 below A7, which then makes the seven upper lights cross A7 instead. Both cost
  more.
* **Cost:** two 0R parts.

### Finding 5. The slits' light (P): form, top band, clips, lead pads (Needs X)

* **Form.** The face names only "P's tail, as the base", a short bar *assumed* by the science runs. I propose the same P bar
  as K4W411 and celestial-3: 18.5 rigid, warm white, level at y 6.3, x 151.65 to 170.15. Then this face needs no new P place.
* **Fit to the bar** (*measured* windows, *inferred* gaps): the slits span y 3.56 to 8.16 (middle 5.86). The bar's body spans
  5.3 to 7.3. So each slit's top is 1.74 mm above the body and its foot 0.86 mm below. In x the bar covers both slits whole.
* **The top band.** The slits' top 0.94 mm lie above t 4.5, where variant D's frame rail lies behind the panel (K4W411 #8).
  Today's sill reaches 3.6, which the slits' top touches. No part goes there, but the rail covers the cut's top, and that
  part is also farthest from the bar: those tips stay dark.
* **Fix:** shorten and lower the slits: 0.8 x 4.0 at y 4.6 to 8.6 (middle 6.6, 0.3 under the bar's axis). Each slit then has
  0.7 mm above the body and 1.3 below; none is in the band. Cost: an art change at P (the fronts re-cut round the slits,
  mirrored as now).
* **Clips.** K4W411 #6 puts the P bar's two clips in the 7.2 mm gap between the button boxes (x 157.5 to 164.3). Here the slits
  take its middle. With 0.3 kept off each slit, the clips have **x 157.5 to 159.2 and 162.6 to 164.3** (1.7 mm each). A 1.5 mm
  clip fits. Cost: none.
* **Lead pads.** Between the bar's end cap (x 150.65) and the key - arc's end cap (x 148.81) there are **1.84 mm** (*measured*:
  the windows' round ends). A 1.5 mm pad with 0.3 each side needs 2.1. Above is the top band; below are the boxes (top at
  y 7.545 if they stand 13.75 across, 0.245 under the bar).
  * **Fix:** pads 1.0 wide x 1.5 tall at **(149.73, 6.3)** and, mirrored, **(172.07, 6.3)**. They keep 0.45 to the arcs' ends and
    to the bar, and 0.50 to the boxes (*measured*). Hand soldering a 1.0 mm pad is fine.
  * This is the same for K4W411's P bar (same place): K4W411 #6 said only "pads at y 6.3 or above".

## 2. Mechanics

### Finding 6. The base windows and their forms (K4W411 #4, #5 and #7 apply)

The seven base windows are K4W411's, at the same places (*measured*: the same polygons). On rev B: MODE on +5V; FIELD down on
SW2's pads, LEVA and A7; SUB down on SW3's pads, LEVB and A7; the key arcs on SW4.1, SW5.2 and D8. Fixes and costs as K4W411 #4.
The key arcs against the boxes: K4W411 #5 (the blocker until measured). The forms and over-lengths: K4W411 #7.

### Finding 7. The bottom band and the case (OK)

* The screen's bar, its clips and its pads stand clear of every control body, J1's plug (x 147.4 to 163.4, y 28.8 to 33.8), the
  screw bosses (r 3.5) and the top band (*measured*: no body within 0.3).
* Today's case has nothing behind the bottom band: the fascia plug stands 9.5 off the back at 28.8 to 33.8 down the face, and the
  kick strip starts below the bottom edge (*measured*: `3d/case-pair/checks.md`, group 8).
* **If the case takes variant D's frame:** its 2 mm ledge lies behind the bottom edge (y 38 to 40, `FF_LEDGE`). The bar as drawn
  (body to 38.0, clips to about 38.5, *assumed* clip size) and its pads (to 38.01) touch it. The raised bar of finding 10 clears
  it by 0.7. Cost: none, with finding 10.
* Depth: K4W411 #9 applies.

## 3. Fab

### Finding 8. The plane wave's white lines come out 0.13 mm (Needs X)

* The band along the bottom edge is drawn as level lines 0.45 mm apart: white 0.16 and gold 0.20 in turn (face doc, section 4).
* The face then cuts white back to 0.32 from gold. The gap between a white line's edge and the next gold line's edge is
  0.45 − 0.08 − 0.10 = 0.27, so the cut eats both edges of every white line (*inferred*).
* **Measured** on the face's own art layer (23 px per mm, plumb runs, y 37.6 to 39.6): white lines **median 0.130 mm, 10 % at
  0.087 or less**. Gold lines 0.174. The silk limit is 0.15 (K4W411 #11).
* The face run reported its smallest silk as 0.15 to 0.16 (the drawn widths, not what is left after the cut).
* **Fix:** pitch 0.50 instead of 0.45 (white 0.16, gold 0.20, gap 0.32 kept). Or both lines 0.15 at 0.45, which sits on every
  limit with no margin. Cost: an art re-run.

### Finding 9. Slivers at the zone seams (Needs X)

* The zones and strips are cut by masks. Where a plumb hairline straddles a seam, the cut keeps a sliver of it (*measured*,
  opening by a 0.13 mm disc at 23 px per mm):
  * white: a 0.09 mm sliver down the right edge, x 190.35 to 190.78, 36.5 mm long (a hairline at x 190.8 = 212 x 0.9, cut by
    the board's 0.6 margin); 1-pixel slivers on the seam at x 181.83;
  * gold: 0.04 mm slivers up to 8 mm long on the seam at x 96.35 (a hairline at 96.3, cut at 96.34).
* In all, 6.2 % of the white area and 1.3 % of the gold is narrower than about 0.13 mm, in about 3,750 and 1,000 pieces. Most
  are the tapered ends where white is cut round gold; the long seam slivers are the ones that matter.
* A 0.04 mm gold sliver cannot be etched. It either vanishes or lifts and floats (*assumed*, standard fab behaviour).
* **Fix:** after the cuts, drop every piece narrower than 0.15, in the vector export (K4W411 #16). Or start each strip's hairlines
  so none falls within 0.1 of a seam. Cost: one filter in the export script.

Everything else is as K4W411 #10 and #11: the bare-FR4 windows need the coupon and the order notes; the drawn line widths,
mask webs (the lobes' webs are 0.56 to 0.75, finding 11) and islands pass.

## 4. Light quality

### Finding 10. The screen's glow: 6.5 mm lobes over a 2 mm bar (Needs X)

* The main lobe stands 6.5 mm tall (y 31.21 to 37.71). The ±1 lobes peak at 32.9, the ±2 lobes at 36.1 (*inferred* from the
  face's curve: 7.0 x cos²(πu/3.2) · sinc²(u/11.2)).
* The bar as drawn (y 37.0) lights a band from 36.0 to 38.0. The main lobe's peak is **4.8 mm** above the bar's top edge; the
  area's centre is at y 35.83, 1.17 above the bar's axis (*measured*).
* Through 2.0 mm FR4 the light spreads about a millimetre or two (*assumed*; K4W411 #12 takes a 2 mm bar as lighting windows up
  to about 4 mm wide). So the lobes' feet will glow and their peaks fade. Lit, the screen will read as a glowing strip with
  faint bumps, not the five peaks of the curve.
* **Fix, cheap first:**
  1. Raise the bar to the area's centre: **y 35.8** (body 34.8 to 36.8). The main peak is then 3.6 mm above the body, the lobes'
     feet 0.9 below. Cost: none.
  2. A small white printed hood over the screen's pour cut (about 17 x 8 x 3 mm), with the bar inside along its foot. A light
     box evens the glow over the whole cut. Cost: one printed part; depth is no issue (K4W411 #9).
  3. If the bench still shows dim peaks: a second 18.5 bar at y 33.0 on the same channel, its own resistor. Cost: one part,
     20 mA, two pads.
* **Bench check:** one bar behind a 2 mm FR4 coupon with the main lobe cut, lit at 20 mA: how far up the lobe it reads even.

### Finding 11. The lobes' webs; bleed; hot spots (OK)

* The lobes part at the fringes' zeros with **0.56 mm** of mask (inner zeros) and **0.75 mm** (outer zeros) (*inferred* from the
  face's 0.5 mm cut level). That is wider than K4W411's 0.45 webs.
* K4W411 #12's fix applies: cut the back pour per lobe (outline plus 0.1), not as one cut. The bar then lights the FR4 only under
  each lobe, and the webs stay dark.
* The slits' web is 1.2 mm of mask between two 0.8 mm windows. One bar lights both; per-slit cuts as above.
* Bleed: the screen is 13 mm or more from any other window (the key - arc); the slits are 10.7 mm from the key - arc's end
  (*inferred* from the measured outlines). No bar end
  lies under a window: the screen's lit length (1 mm dark at each end, *assumed*) is 110.6 to 127.1, the lobes 111.59 to 126.19.
* The lobes' foot corners narrow to points at the cut level. The fab rounds them and little light reaches them. Cosmetic.

### Finding 12. One warm, two products (Needs X, bench)

* The face is all warm by design (section 5 of its doc). But "warm" is two sold parts: the 38 flex in "yellow" (MODE and the
  key arcs) and the rigid bars in "warm white" (the four lever arcs, S, P). Front-merge (section 5) only *assumes* they match.
* On a face that reads as one colour, a mismatch shows: the two outer arcs one tint, the four lever arcs and the screen another.
* Brightness per mm may differ too: a 38 flex and an 18.5 bar at the same 20 mA spread the light over different lengths
  (*assumed*; no datasheet in the repo).
* **Fix:** add to K4W411 #10's coupon one 38 yellow flex beside one 18.5 warm-white bar, through the same FR4. Trim the
  resistors to match brightness. If the tints differ, use 38 flex in yellow for the lever arcs too (K4W411 #7 allows it).
  Cost: none.
* K4W411 #13 (colours through tan FR4) applies.

**The display.** The face echoes display V1 Fringes. The final display, disp-3-4, keeps the tube pairs' x (so the face's sources
still sit under its tubes) and the refined V1 fronts, but drops the collapse lobe over the seconds (TS06-DISP-final-3.md, the
disp-3-4 section). The fascia's screen then carries that motif alone. No build impact.

## 5. The path to a board

### Finding 13. What the board-change run must do (Needs X)

K4W411 #15 (the face is drawn on the T art model; rev B is surface-mount) and #16 (layers from vectors, re-checks) apply. The
pill is E1's (R7 and R8 mirror-placed), which is the T layout. What this face adds, in order:
1. **Back:** jog A6 under the screen, to y 38.35 (finding 3); K4W411 #4's six pads and five re-routes.
2. **Lights:** the second S place (two pads, a resistor) at the raised bar (finding 2, 10); two 0R hops over A7 (finding 4); the
   P pads 1.0 wide (finding 5).
3. **Windows:** per-lobe and per-slit pour cuts (finding 11); the slits shortened and lowered (finding 5).
4. **Art export:** the band at 0.50 pitch (finding 8); the sliver filter (finding 9).
5. **Bench:** the screen's glow (finding 10); yellow flex beside warm-white bar (finding 12); K4W411's checks.

**What KiCad or the fab cannot make as drawn:** the band's white lines (0.13) and the seam slivers. Everything else can be made.

## Routing needs

Board: fascia R (the common base; rev B's frame). Pads are on B.Cu, 1.5 x 1.5 unless said. They come from a search that keeps 0.3
off the face's windows, every light body of the face, rev B's back copper, the control bodies (both orientations where not
known), J1's plug, the screw bosses (r 3.5), the top band (t < 4.5) and 0.5 off the edge (*measured* on the raster); the four
lever pads between FIELD and SUB were set by hand (*measured* with the same check), because the searched ones overlapped: below
the up bars and below the down bars (above the down bars they would land on rev B's R6 pads and A7).
Channels and pins are K4W411's J2 map (pin 1 +5V_L).

| id | face | board | source (form, sold length, colour) | pad A (x, y, layer) | pad B (x, y, layer) | mA | shares with | proposed channel | connector pin | conflicts (copper, parts, 185 V, case) | evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| sci-MODE | science-2-3 | fascia R | 38 flex, warm (yellow) | (15.76, 28.91, B.Cu) | (12.34, 5.26, B.Cu) | 20 | none | CH1 | J2.2 | body on rev B +5V at (12.6, 23.1) (K4W411 #4); window top at y 4.14 in the top band | measured |
| sci-FLDu | science-2-3 | fascia R | 18.5 rigid, warm white, level y 5.9, x 54.74 to 73.24 | (52.74, 5.91, B.Cu) | (74.0, 8.0, B.Cu) | 20 | FLDd | CH2 | J2.3 | none on rev B | measured |
| sci-FLDd | science-2-3 | fascia R | 18.5 rigid, warm white, level y 26.1, x 54.74 to 73.24 | (52.74, 26.11, B.Cu) | (74.0, 28.2, B.Cu) | 20 | FLDu | CH2 | J2.3 | body on SW2.1, SW2.2, LEVA, A7, +5V (K4W411 #4) | measured |
| sci-SUBu | science-2-3 | fascia R | 18.5 rigid, warm white, level y 5.9, x 78.12 to 96.62 | (77.4, 8.0, B.Cu) | (98.66, 5.91, B.Cu) | 20 | SUBd | CH3 | J2.4 | none on rev B | measured |
| sci-SUBd | science-2-3 | fascia R | 18.5 rigid, warm white, level y 26.1, x 78.12 to 96.62 | (77.4, 28.2, B.Cu) | (98.64, 25.06, B.Cu) | 20 | SUBu | CH3 | J2.4 | body on SW3.1, SW3.2, LEVB, A7 (K4W411 #4) | measured |
| sci-KEYm | science-2-3 | fascia R | 38 flex, warm (yellow) | (147.81, 27.69, B.Cu) | (144.44, 5.26, B.Cu) | 20 | KEYp | CH4 | J2.5 | body on SW4.1; over the box corners (K4W411 #5) | measured |
| sci-KEYp | science-2-3 | fascia R | 38 flex, warm (yellow) | (177.39, 5.26, B.Cu) | (173.99, 27.69, B.Cu) | 20 | KEYm | CH4 | J2.5 | body on D8, SW5.2; over the box corners (K4W411 #5) | measured |
| sci-S | science-2-3 | fascia R | 18.5 rigid, warm white, level y 35.8 (drawn 37.0), x 109.6 to 128.1 | (107.59, 34.96, B.Cu) | (130.14, 34.96, B.Cu) | 20 | P | CH5 | J2.6 | **new place**; rev B A6 under it (jog to y 38.35); leads cross A7 to J2 spot (a) (two 0R); spot (b) is on it; variant D's ledge if left at 37.0 | measured |
| sci-P | science-2-3 | fascia R | 18.5 rigid, warm white, level y 6.3, x 151.65 to 170.15 | (149.73, 6.3, B.Cu), 1.0 x 1.5 | (172.07, 6.3, B.Cu), 1.0 x 1.5 | 20 | S | CH5 | J2.6 | 0.245 above the boxes (13.75 across); clips only at x 157.5-159.2 and 162.6-164.3; slit tops in the top band | measured, inferred |

* **Total:** 180 mA (nine lights at 20 mA).
* **Channels alone:** 5 (CH1 MODE, CH2 FIELD, CH3 SUB, CH4 keys, CH5 S + P).
* **If same-colour lights share:** all are warm, so colour forces nothing; 3 if MODE, FIELD and SUB may light together.
* **Connector pins:** 6 of K4W411's 7-way J2 (+5V_L, CH1 to CH5); pin 7 spare.
* **Forces on fascia R that other faces may not need:** a second S place in the bottom band (two pads, a resistor, the route
  with two 0R hops over A7); A6 jogged under the screen; J2 not at K4W411's spot (b). The P pads 1.0 wide apply to every face
  with the P bar at y 6.3. Nothing on DRV or DISP beyond K4W411 #1.

## 6. Left open

* Not measured: the buttons' stand-off and orientation (K4W411 #5); how far up a 6.5 mm lobe one bar lights through 2 mm FR4
  (finding 10); yellow flex against warm-white bar (finding 12).
* Not done: routing on any board; KiCad DRC; the T layout's back copper (no board exists, K4W411 #15), so the screen's back
  was checked on rev B only.
* The pads in the table are places that fit, not a layout. The routing-plan run sets them.
