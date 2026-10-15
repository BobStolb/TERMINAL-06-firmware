# TS06 fascia BLUPRNT: the grill (can it be built, will it work)

2026-10-15, run grill-bluprnt. The owner (00:0x UTC): "run grills on all, compile insights for the final pcb routing plan".
BLUPRNT is a final candidate, not approved. This page grills its round 2 ([TS06-FASCIA-BLUPRNT.md](TS06-FASCIA-BLUPRNT.md)):
* the exploded ИН-12А at 1:4, with its lit "3" as window S at (105.61, 15.07);
* the mirrored ИН-17 at 1:3, with its lit "3" as window P at (131.36, 15.61).

It proposes fixes and applies none. No board, schematic, fab, tool, 3D, firmware, spec or face file was touched. The scripts are
scratch (`scratchpad/grills/grill-bluprnt/`). They rebuild the face's layers by importing the face run's own script, unchanged.

Marks, as in the K4W411 grill:
* *measured*: read from a repo file, or from the face's own geometry (its script, or its layers rebuilt at 23 px per mm);
* *inferred*: arithmetic on measured numbers;
* *assumed*: my reading, or a value nobody has measured.

Frame: fascia R's own (KiCad) frame, seen from the front. The origin is the board's top-left corner, x to the right, y down;
the board is 191.4 x 40.0 (*measured*: `PCB/TS06-FASCIA-rhythm`, Edge.Cuts). The face shares this frame.

The base board is fascia R rev B, the ordered one: `PCB/TS06-FASCIA-rhythm/TS06-FASCIA-rhythm.kicad_pcb`, the source of
`fab/TS06-FASCIA-R-revB-divider-holes04-fab.zip`.

**What the K4W411 grill settled applies here too, and is not repeated:**
* #1, DRV has no PWM chip yet;
* #2, one resistor per filament on a shared channel;
* #3, J2's pin map;
* #4, the base windows over rev B's back copper;
* #5, the key arcs against the button boxes;
* #7, the base filaments' forms and lengths;
* #10, the coupon;
* #12, the halo;
* #13, colours through FR4;
* #15, the T art model;
* #16, layers from vectors.

Where a number changes for BLUPRNT, it is given in one line.

## Verdict

**Buildable after changes, like K4W411. BLUPRNT adds no blocker of its own.** Both lit "3"s can be made and lit with what is sold.
The back is clear on rev B. The fine work is at or near the fab's floor. Three new things count most:

* **P's tail sits on K4W411's connector spot.** That spot is spot (a), right of the pill. The routing plan needs one J2 spot that
  every face can use (finding 2).
* **The gold mesh is drawn 0.14 mm wide,** under the 0.15 floor. No check in the repo would catch it (finding 8).
* **Two fonts dip under 0.15 mm.** These are the "BLUPRNT" title, and the ink traps in B612 Mono's 3, 6 and 9. The face run read
  its fonts at the 5th percentile, not at the thinnest point (finding 10).

The shared blocker stays: the key arcs against the button boxes (K4W411 #5). BLUPRNT keeps the base's key arcs, so that blocker
applies here as much as to K4W411.

| # | Item | Rating |
|---|---|---|
| 1 | S and P end to end: bars, leads, channel 5, current | OK (K4W411 #1 to #3 apply) |
| 2 | P's tail on K4W411's J2 spot (a) | **Needs X** (new) |
| 3 | S's bar off the "3"'s light centre; the face's flex fallback | **Needs X** (new) |
| 4 | The two tails against rev B's back, the parts, the top band | OK (K4W411 #8 applies; one base note) |
| 5 | The "3" windows: strokes, the mask cusp, the back cut | OK, with one emission rule |
| 6 | The coupon must carry a 0.55 mm "3" at both sizes | **Needs X** (adds to K4W411 #10) |
| 7 | The face's back check was read on rev A | OK (corrected numbers) |
| 8 | Gold anode mesh 0.14 mm, under the 0.15 floor | **Needs X** (new) |
| 9 | White linework in the exploded views | OK, at the floor |
| 10 | Lettering against the 0.15 line and the 1.0 mm text | **Needs X** (new) |
| 11 | Glow over each "3": evenness, lit length, bowls, colour | OK (bench) |
| 12 | Which cathode is at the front (the lit numeral rests on it) | **Needs X** (a look at one tube) |
| 13 | From the picture to layers: raster steps, fonts, the checks | **Needs X** (adds to K4W411 #16) |

## 1. Light sources and connection, end to end

### Finding 1. S and P end to end (OK; K4W411 #1, #2, #3 apply)

BLUPRNT keeps the base's seven control lights. It changes only S and P (*measured*: BLUPRNT md section 3, `f_bluprnt2.py`):

| Light | Window | Sold part | Held by | Leads | J2 pin | DRV |
|---|---|---|---|---|---|---|
| S | the ИН-12А's "3": strokes 0.55, 4.66 x 2.61, centre (105.61, 15.07) | 18.5 rigid, warm white, plumb at x 105.61, y 5.8 to 24.3 | two clips at the bar's ends | pads beside each end (finding 4); anode via 120R to +5V_L, cathode to CH5 | 6 | CH5 |
| P | the ИН-17's "3": strokes 0.55, 3.00 x 1.83, centre (131.36, 15.61) | 18.5 rigid, warm white, plumb at x 131.36, y 5.9 to 24.4 | the same | the same | 6 | CH5 |

* Channel 5 carries S and P only: 40 mA. K4W411 carries 60 mA there, with its stack.
* The fascia has nine filaments, all warm: 180 mA at 20 mA each (*inferred*).
* With disp-3-4 the clock's worst case is **852 mA, 85 %, or 660 mA with the LED cap**. K4W411 gives 872 mA (*inferred*: disp-3
  table, line 143, less one fascia filament).
* **Channels.**
  * One per function (the earlier runs' map): 5, CH1 to CH5. CH6 is not fitted.
  * Every BLUPRNT light is warm, so colour never stops lights sharing a channel. Only behaviour does.
  * Front-merge's three groups need 3 channels: MODE + FIELD + SUB, the keys, and S + P.
  * On 3 channels, disp-3-4 one per line comes to 13 + 3 = **16**: one chip, no spare (*inferred*: disp-3 table, lines 136 to
    139). The cost is K4W411 #1's: the control arcs no longer light one at a time.
* The face's write-up says "the connector stays at 6 channels" and "three channels". Read it as K4W411's 7-way J2: pins 1 to 6
  are used, and pin 7 is spare.

### Finding 2. P's tail sits on K4W411's J2 spot (a) (Needs X, new)

* K4W411 #3 picked **spot (a)** for J2: upright, at x 130.5 to 139.0, y 5.5 to 24.9.
* BLUPRNT's P bar body runs x 130.36 to 132.36, y 5.9 to 24.4.
* They overlap by **1.86 x 18.5 mm** (*measured*, `backcheck.py`).
* J2 cannot move right to clear it. The key - arc's flex starts at x 139.4 (K4W411 #3), so the spot is already 0.4 mm from it.
* So J2 needs a spot that every face can use.
* **What BLUPRNT allows** (*measured* on rev B: between x 100 and 140, the back holds only A7 and the GND pour):
  * **Spot (b), laid level at x 100 to 120, y 27 to 35.5.** It sits between A7 (y 26.2) and A6 (y 36.1), 9.65 mm apart edge to
    edge. That leaves 0.6 mm a side for the 8.5 mm courtyard. A7 does not have to move. The lights are all above A7, though, so
    their nets cross it. Hop A7 with 0R jumpers on the back, one each for CH5, +5V_L and the other cathodes that come this way,
    or lower A7. Cost: 2 to 6 jumpers, or one re-route.
  * **Behind the pill**, upright at x 114.6 to 123.1, y 5.5 to 24.9, on the rev B base only. It keeps 7.6 mm to S's bar (moved, finding 3) and
    7.3 mm to P's. But it collides with K4W411's S bar (level in the pill at y 8.35) and with the T model's ladder (K4W411 #15).
* **Fix:** the routing plan picks spot (b) as the common J2 place, unless another face rules it out. Cost: the jumpers above.

### Finding 3. S's bar is off the "3"'s light centre; the flex fallback is not sold (Needs X, new)

* The "3" carries its ink on the right, in the spine. On the rebuilt layers, the ink's centre is at x 105.92 for S and 131.54
  for P (*measured*). The bars sit on the numerals' box centres, 105.61 and 131.36.
* Share of each window over a 2.0 mm bar body (*measured*, `barshift.py`):

| Bar at x | Window over the body | Window past the body, left / right |
|---|---|---|
| S, 105.61 (drawn) | 66 % | 0.48 / 0.56 (the spine) |
| **S, 106.00 (proposed)** | **79 %** | 0.87 (the two arc tips) / 0.17 |
| S, 106.30 (nearer K4W411's stack bar at 107.3) | 75 % | 1.17 / 0 |
| P, 131.36 (drawn) | 93 % | 0.14 / 0.16 |

* **Fix:**
  * Move S's bar 0.39 mm right, to x 106.00. Then the spine lies over the body, and only the two short arc tips reach past it.
  * Leave P where it is.
  * If the routing plan wants one plumb source shared by BLUPRNT's S and K4W411's stack, x 106.3 still covers 75 %.
  * Cost: none.
* **The face's fallback** is "a short flex piece bent to the 3" (BLUPRNT md section 7). No such part is sold. The flex starts at
  38 mm (front-merge section 5). The "3"'s bowls bend at radii of 0.75 to 1.3 mm, and nobody has measured the flex's least bend
  radius. So the plumb bar is the only form; if the bench shows the spine dim, the fix is the shift above.

## 2. Mechanics

### Finding 4. The two tails against rev B's back, the parts and the top band (OK; K4W411 #8 applies)

*Measured* on rev B (`backcheck.py`):

| | S bar | P bar |
|---|---|---|
| Nearest back track, edge to edge | A7, 1.77 | A7, 1.68 |
| Nearest pad or part | SW3's panel-hole pad, 13.2 | SW4's panel-hole pad, 14.0 |
| Top end to the t 4.5 line (K4W411 #8) | 1.30 | 1.40 |
| The pour cut under the numeral (the clips must stay off it) | y 12.4 to 17.7 | y 13.8 to 17.4 |

* The button boxes (K4W411 #5) reach at most x 141.9. That is 9.5 mm from P's body.
* **The leads** must bend sideways, as in K4W411 #8. The top end has only 1.3 mm to the frame's top rail, so a lead out of the
  end would reach it.
* **Proposed pads** (1.5 x 1.2, B.Cu, with S moved as in finding 3):
  * S at (108.0, 6.4) and (108.0, 23.7);
  * P at (129.4, 6.5) and (129.4, 23.8), on the pill side, away from the key arc.
  * Each pad keeps 0.2 mm to its bar's body and 1.7 mm or more to A7 (*inferred*).
* **The clips** go at the bar ends: S at y 5.8 to 7.8 and 22.3 to 24.3, P likewise. There they stay off the numeral's pour cut.
  A clip over the cut would shade the "3".
* **One base item the K4W411 grill did not list** (*inferred* from the window boxes it measured):
  * The MODE flex's outer edge comes to y 4.36 at its upper end (r 15.2 at 230 deg).
  * The lever-up arcs come to y 4.40, if they are flex on the arc.
  * Both are 0.10 to 0.14 mm inside the t 4.5 band.
  * The 18.5 bar on the chord stays below it (body top at 4.9).
  * **Fix:** 0.2 mm of relief in variant D's top rail behind the MODE and lever-up ends, or bars on the lever arcs. This is the
    same for every face.
* Depth and the gap to DISP: K4W411 #9 applies (two more 2.0 mm bars, flat on the back).

## 3. Fab

### Finding 5. The "3" windows: strokes, the mask cusp, the back cut (OK, with one emission rule)

*Measured* on a 200 px per mm raster of the face's own numeral (`measure.py`):
* **Strokes:** 0.55 mm, as a mask opening on both faces. That is far above the 0.10 mask web.
* **The window to white and to gold:** 0.40 for both, against the 0.35 rule.
* **The cusp.** The middle of a "3" is two bowls that meet tangentially, so the mask notch on the right of the junction tapers
  to nothing:
  * S has a sliver under 0.10 mm at (106.52, 15.05), 0.001 mm²;
  * P has one at (132.16, 15.58), 0.0008 mm².
  * It is the same kind of crescent tip that the ordered fascia already passes with (`fab/ORDER.md`, the mask web note).
* **Emission rule:** end each notch where the mask reaches 0.10 mm. That is a fill of about 0.05 mm at the tip. Cost: none.
* **The bowls** (*inferred* from the numeral's geometry):
  * S's bowls are 1.78 x 1.85 mm inside;
  * P's are 0.95 x 1.14 (top) and 0.95 x 1.28 (bottom).
* **The back cut.** Cut the GND pour per stroke, at the numeral grown by 0.1, as K4W411 #12 does per pal.
  * The pour then stays inside the bowls: 1.58 mm across for S, 0.75 mm for P.
  * That copper stays tied to the pour through the "3"'s open left side. The necks are 1.23 for S and 0.56 for P (*inferred*),
    so no zone island is left.
  * A cut of the whole numeral's outline would light the bowls too, and the P "3" would read as a blob.

### Finding 6. The coupon must carry a 0.55 mm "3" at both sizes (Needs X; adds to K4W411 #10)

* K4W411's coupon list goes down to a 0.95 mm slit.
* BLUPRNT's strokes are 0.55 mm, the narrowest lit feature of any face so far.
* The P "3" is 3.0 mm tall, with 0.95 mm bowls.
* **Add to the coupon:**
  * S's and P's "3"s at full size, with the back cut as in finding 5, each over a warm 18.5 bar;
  * the S "3" with its bar at x 105.61 and at 106.00 (finding 3).
* **The coupon must show:** whether the 0.55 strokes read lit, and whether P's bowls stay dark.
* Cost: two features on the coupon.

### Finding 7. The face's back check was read on rev A (OK)

* The face run checked the back on `R-open.kicad_pcb`, rev A. It gives A6 at y 33.7, +5V at 38.8, A7 level to x 142.8, and J1
  at (155.4, 33.4).
* Rev B gives A6 at y **36.1**, +5V at **39.0**, A7 level to **139.1** then diagonal to (149.6, 36.7), and J1 at (155.4, **33.0**)
  (*measured*).
* The tails' gaps to A7 are the same on both, so the face's conclusion stands.

### Finding 8. The gold anode mesh is 0.14 mm, under the 0.15 floor (Needs X, new)

* **What is drawn:** the mesh is drawn as a band |x + y - 0.9 n| < 0.1, which makes lines 0.2 / √2 = **0.141 mm** across, on a
  0.636 mm pitch (*measured*: `f_bluprnt2.py`, `explode()`; the face md says "0.14 lines").
* **The floor:** copper is 0.15 in `tools/dfm_check.py`'s limits (`fab/ORDER.md`, the limits line).
* **No check would catch it:**
  * The mesh would be F.Cu graphic shapes, and KiCad's track-width rule applies to tracks only (*inferred*).
  * `tools/gerbers.py` reads the smallest **aperture** that a draw or flash uses (its `smallest_aperture`, lines 284 to 285).
    Regions are not read. Rasterised copper is checked for the mask web, not for width.
* **Fix:**
  * Draw the mesh at 0.16 on the same pitch. The gap is then 0.48, still above 0.15.
  * Drop mesh pieces under 0.10 mm² where it is clipped at the glass and the lit "3". The face keeps pieces down to 0.05 mm².
  * Cost: none.

### Finding 9. White linework in the exploded views (OK, at the floor)

*Measured* on the face's script and on its rebuilt layers:
* The outlines, leaders and graph lines are 0.15. The leader dots are 0.22 and the grid dots 0.20.
* The hidden-line breaks are 0.30, so no two separate parts of a stack come closer (by construction in the face script).
* After the face's speck filter, each view keeps 12 or 13 fragments shorter than 0.6 mm. The shortest is 0.30 mm long (0.066 mm²),
  at (103.12, 7.46) and (139.10, 7.46).
* One raster speck of 0.002 mm² is left at (109.57, 7.99). It must not come through into the vectors.
* Every line is at the floor, with no margin. K4W411 #11 rated 0.15 the same way. If the fab's yes is in doubt, the views can go to
  0.18 (the base's white). The cost is that more of the rear cathodes break away in the 1:3 stack.

### Finding 10. Lettering against the 0.15 line and the 1.0 mm text (Needs X, new)

**How the face run measured:** its "thinnest" column (BLUPRNT md section 2) is the **5th percentile** of the ridge widths
(`fontmeasure.py`, `np.percentile(w, 5)`), not the thinnest point.

**My re-measure:** each string as printed (font, capital height, width), rastered at 200 px per mm. Two readings: the least ridge
width, and the share of ink that an opening with a 0.15 mm disc removes (`fontopen.py`, `fontglyph.py`, `fontfix.py`):

| Use | Size | 5th percentile (the face's) | Least | Under 0.15 | Rating |
|---|---|---|---|---|---|
| ИН-12А, ИН-17, Osifont | 1.8 | 0.170 | 0.168 | none | OK |
| **BLUPRNT, Osifont** | 1.6 | 0.150 | **0.148** | **the whole word: 20 % of its ink** | **Needs X** |
| 6 POS, J1 PH 2.0, Share Tech Mono | 1.5 | 0.160 | 0.156 | none | OK |
| B612 Mono Bold, 0.85 to 0.90 width, letters | 1.2 | 0.160 | 0.149 to 0.155 | none in the cores | OK |
| **B612 Mono Bold digits 3, 6 and 9** | 1.2 | 0.160 | **0.110, 0.113, 0.120** | **their ink traps** (1.5, 0.6, 0.5 % of each glyph) | **Needs X** |

* **BLUPRNT:** Osifont's line is a tenth of its height, so 1.6 is exactly the floor.
  * 1.8 gives 0.163, but the word is then 9.5 mm long. The title block is 8.4 wide.
  * **Fix:** widen the block to 10.2 mm, or set the word in Share Tech Mono at 1.5 (least 0.156). Cost: the block's width.
* **B612's ink traps:** the notches at the joins of 3, 6 and 9 scale with the size.
  * They are 0.130 at 1.5 mm, so no size the face can afford clears 0.15.
  * They print in the dimension values (39.10, 23.38, 31.515), SCALE 1:3, 0-9, J1's "3 A6" and "6 D8 +", and the 24-hour heading.
  * Silk ink usually spreads into a notch (*assumed*). The risk is a fab's checker or a broken digit.
  * **Fix:** ask the fab, or set the digits in KiCad's stroke font at 1.2 (0.15 line). Cost: a mixed look in the figures.
* **Text heights:** every string is 1.0 mm or more in capitals. OK.
* **The minus sign, Cyrillic, ×:** the face's per-glyph fallbacks hold (BLUPRNT md section 2).

## 4. Light quality

### Finding 11. Glow over each "3" (OK; the bench decides)

* **Lit length:** the windows span y 12.43 to 17.65 (S) and 13.83 to 17.35 (P) (*measured*).
  * The bars give 6.6 mm of margin at each end for S, and 7.9 and 7.0 for P.
  * Any dark end under 6 mm still lights the whole numeral, so K4W411 #8's dark-end bench check does not limit BLUPRNT.
* **Across:** P is 93 % over its bar, and S 79 % once moved (finding 3). Through 2.0 mm FR4, 0.2 to 0.9 mm past the body reads a
  little dimmer at the arc tips (*assumed*, as K4W411 #12).
* **Shape:** the front mask sets the edge, so the "3" is as sharp as the opening. Per-stroke back cuts keep the bowls dark (finding
  5); a halo under the black mask is K4W411 #12.
* **Colour:** all warm, which changes least through tan FR4 (K4W411 #13 applies, with less at stake). By day the lit "3" is a
  tan numeral among nine white silk ones. It reads as the odd one, which is the drawing's point.
* **Bleed:** the nearest other lit windows are SUB's arcs, 5 mm or more from S, and the key - arc, 6.9 mm from P. K4W411 #14
  applies.

### Finding 12. Which cathode is at the front (Needs X: a look at one tube)

* The lit window is a "3" only because the face takes the firmware's `cathodeMask` (1 6 2 7 5 0 4 9 8 3) as rear to front. The
  face md marks this *assumed*.
* The ИН-17's own order is "not captured" (BLUPRNT md section 4).
* If the bench shows another digit at the glass, the window's outline changes. After the order, that is a reprint.
* **Check before the face is frozen:** light each digit of one ИН-12А and one ИН-17 and look from the side. The front cathode is
  the one nothing hides. Cost: minutes.

## 5. The path to a board

### Finding 13. From the picture to layers (Needs X; adds to K4W411 #16)

K4W411 #15 applies: BLUPRNT is drawn on the T art model.
* The pill meter's ticks stop short round the T model's R6 to R8.
* Under K4W411 #15 (b), the rev B base, those gaps have nothing in them. Run the ticks full width. Cost: one art change.

K4W411 #16 applies. The steps BLUPRNT adds:
1. **Clipping, made in raster in the face run:** the hidden-line breaks (0.3), the mesh clipped at the glass and the lit "3"
   (0.4), and the speck drop. They are raster masks in `f_bluprnt2.py`. To emit vectors, the board-change run needs:
   * a polygon clipper, or
   * a fine raster (100 px per mm or more), traced to polygons and checked again.
   The 23 px per mm raster is too coarse: its 0.15 lines come out 3 px, which is 0.13 mm.
2. **The windows:** each "3" as a polyline of width 0.55, turned into a polygon with round ends. Then:
   * F.Mask and B.Mask openings;
   * copper keep-outs on both layers;
   * the back cut at +0.1 per stroke;
   * the cusp filled to 0.10 (finding 5).
3. **The fonts:**
   * Plot on a machine with the three fonts installed, or embed them in the board file.
   * A missing font silently falls back to KiCad's default (*assumed*).
   * Read the Gerber's silk, not the board, to see that the right outlines came out.
   * The licences allow it: OFL 1.1 and LGPL 3 with the font exception (BLUPRNT md section 2).
4. **A width check that sees regions:**
   * KiCad's text-thickness rule does not measure a TrueType outline (*inferred*).
   * `gerbers.py` reads only apertures (finding 8).
   * Add an opening test with a 0.15 mm disc on the rasterised F.Silk and F.Cu: findings 8 and 10 in one test.
5. **The back:** S and P pads, their two 1206 resistors and the per-stroke cuts, routed to J2 at the common spot (finding 2).

**What KiCad or the fab cannot make:** nothing on the face. Not as drawn:
* the "3"s by day are tan, not white;
* the mesh must be 0.02 mm wider;
* two font details need the fab's yes or a change.

## Routing needs

Frame: fascia R, KiCad front view, origin at the board's top-left corner (0, 0), x right, y down, mm. The base lights' pads are
given at their window ends (*inferred*: the window boxes measured in the K4W411 grill). Their final places follow K4W411 #4 and
#7. S and P use finding 4's pads, with S moved as in finding 3. Anodes run through their own 120R to +5V_L (J2.1).

| id | face | board | source (form, sold length, colour) | pad A (x, y, layer) | pad B (x, y, layer) | mA | shares with | proposed channel | connector pin | conflicts (copper, parts, 185 V, case) | evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BP-MODE | BLUPRNT (base) | fascia R | flex, 38, yellow (warm) | (15.76, 5.12, B.Cu) | (15.76, 26.88, B.Cu) | 20 | none | CH1 | J2.2 | +5V track under the window (K4W411 #4); outer edge at y 4.36, in the t 4.5 band (finding 4); 13.2 mm over, folded (K4W411 #7) | *inferred* |
| BP-FU | BLUPRNT (base) | fascia R | rigid 18.5 on the chord, or flex 38, warm | (59.51, 6.39, B.Cu) | (68.47, 6.39, B.Cu) | 20 | FIELD down | CH2 | J2.3 | flex on the arc reaches y 4.40 (finding 4) | *inferred* |
| BP-FD | BLUPRNT (base) | fascia R | the same | (59.51, 25.61, B.Cu) | (68.47, 25.61, B.Cu) | 20 | FIELD up | CH2 | J2.3 | SW2's pads, LEVA, A7 under the window (K4W411 #4) | *measured* (K4W411) |
| BP-SU | BLUPRNT (base) | fascia R | the same | (82.89, 6.39, B.Cu) | (91.85, 6.39, B.Cu) | 20 | SUB down | CH3 | J2.4 | as FIELD up | *inferred* |
| BP-SD | BLUPRNT (base) | fascia R | the same | (82.89, 25.61, B.Cu) | (91.85, 25.61, B.Cu) | 20 | SUB up | CH3 | J2.4 | SW3's pads, LEVB, A7 (K4W411 #4) | *measured* (K4W411) |
| BP-KM | BLUPRNT (base) | fascia R | flex, 38, yellow (warm) | (147.81, 6.34, B.Cu) | (147.81, 25.66, B.Cu) | 20 | key + | CH4 | J2.5 | SW4.1 under the window (K4W411 #4); the button box, **blocker** until measured (K4W411 #5) | *measured* (K4W411) |
| BP-KP | BLUPRNT (base) | fascia R | flex, 38, yellow (warm) | (173.99, 6.34, B.Cu) | (173.99, 25.66, B.Cu) | 20 | key - | CH4 | J2.5 | SW5.2, D8 (K4W411 #4); the button box (K4W411 #5) | *measured* (K4W411) |
| BP-S | BLUPRNT | fascia R | rigid, 18.5, warm white, plumb at x 106.00, y 5.8 to 24.3 | (108.0, 6.4, B.Cu) | (108.0, 23.7, B.Cu) | 20 | P | CH5 | J2.6 | A7 1.77 below; top 1.30 from the band (leads sideways); clips off y 12.4 to 17.7; no 185 V | *measured* (rev B) |
| BP-P | BLUPRNT | fascia R | rigid, 18.5, warm white, plumb at x 131.36, y 5.9 to 24.4 | (129.4, 6.5, B.Cu) | (129.4, 23.8, B.Cu) | 20 | S | CH5 | J2.6 | **on K4W411's J2 spot (a)** (finding 2); A7 1.68 below; top 1.40 from the band | *measured* (rev B) |

* **Total:** 180 mA on the fascia, nine filaments at 20 mA. With disp-3-4: 852 mA, 85 %, or 660 mA with the LED cap (*inferred*).
* **Channels alone:** 5 (CH1 to CH5).
* **Channels if same-colour sources share:**
  * All nine are warm. With front-merge's groups that makes 3: MODE + FIELD + SUB, the keys, and S + P.
  * Any fewer merges behaviours, not colours.
  * On 3, disp-3-4 one per line fits one chip at exactly 16.
* **Connector pins:** 6 of K4W411's 7-way J2 (+5V_L and CH1 to CH5). Pin 7 is spare.
* **What BLUPRNT forces that other faces may not:**
  * **J2 cannot go at K4W411's spot (a):** P's tail is there. Spot (b), between A7 and A6 at x 100 to 120, fits rev B with A7
    hopped by 0R jumpers.
  * Two plumb bars, with pads, at x 106.0 and 131.36. They are near K4W411's stack bar (x 107.3), but not on its S and P bars.
  * No change on DRV beyond K4W411 #1 and #3.
  * No change on DISP.

## Left open

* **Not measured:**
  * which cathode is at the front of each tube (finding 12);
  * the flex's least bend radius (finding 3);
  * whether 0.55 mm strokes read lit through 2.0 mm FR4 (finding 6);
  * the fab's view on B612's ink traps (finding 10);
  * everything K4W411's grill left open (the button stand-off, the forward voltages, the RTC's I2C addresses).
* **Not done:** routing; KiCad DRC; a check of the fonts inside KiCad itself.
* **No marked picture.** The owner said to skip it, so this page is the deliverable. One check picture of the two views over rev
  B's back was drawn in scratch to confirm finding 2 and finding 4. It is not in the repo.
