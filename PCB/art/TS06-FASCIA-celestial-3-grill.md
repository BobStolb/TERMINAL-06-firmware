# TS06 fascia celestial-3 Sundials: the grill (can it be built, will it work)

2026-10-15, run grill-scicel. The owner (00:0x UTC): "run grills on all, compile insights for the final pcb routing plan".
celestial-3 is a final candidate, not approved. This page reviews it and proposes fixes. It applies none: no board, schematic,
fab, tool, 3D, firmware or spec file was touched, and the face ([TS06-FASCIA-celestial.md](TS06-FASCIA-celestial.md) section 4)
is unchanged. The scripts are scratch, not in the repo. There is no marked picture (the owner dropped it); the doc is the grill.

The model is [the K4W411 grill](TS06-FASCIA-K4W411-grill.md). What it settled for every fascia is cited as "K4W411 #n applies"
in one line. Only what is new or different for this face is written out.

Marks:
* *measured*: read from a repo file (board, case model), or from the face run's own geometry (its window polygons and art
  model, rebuilt with its own script, rastered at 40 px per mm; its art layers at 23 px per mm).
* *inferred*: arithmetic on measured numbers.
* *assumed*: my reading, or a value nobody has measured.

Frame: fascia R's own KiCad frame, front view. Origin at the board's top-left corner, x right, y down, mm. The board is
191.4 x 40 (rev B's Edge.Cuts, *measured*). "Rev B" is the ordered board, `PCB/TS06-FASCIA-rhythm/TS06-FASCIA-rhythm.kicad_pcb`.

## Verdict

**Buildable after changes, and the closest of the candidates to K4W411.** Its lights are K4W411's less the mochi stack: the
same seven arcs, S and P bars at exactly K4W411's places. Only the colours differ (the key arcs and P are white). So almost
every light finding is "K4W411 #n applies", and this face adds no light place to the common base.

What is new:
* the five moons fill the place where K4W411 #6 puts the P bar's clips, so the P bar has no clip place until the buttons are
  measured;
* the rails shown in gold put +5V on the face (on the through-hole base) or need new gold (on rev B, which has no rails);
* the art leaves hairline gold slivers at the panel seams.

K4W411's one blocker (#5, the key arcs against the buttons' boxes) applies here unchanged.

| # | Item | Rating |
|---|---|---|
| — | K4W411 #1, #2, #3, #4, #5, #7, #9, #10, #14, #15, #16 | as K4W411 |
| 1 | The nine lights, end to end; channels | OK (5 channels, 180 mA; 6 if day and night light apart) |
| 2 | The moons' bar: no place for its clips | Needs X |
| 3 | The P bar's lead pads: 1.84 mm between the bar and the key arcs | Needs X |
| 4 | The sun's bar and its pads | OK (pad B moved off J2's spot) |
| 5 | The top band | K4W411 #8 applies, less the stack |
| 6 | The rails shown in gold: +5V on the face, or no rails on rev B | Needs X (owner) |
| 7 | Slivers at the panel seams | Needs X |
| 8 | Sharp tips: the sun's rays, the crescents' horns, the stars | OK |
| 9 | The moons' and the sun's glow; webs | OK (per-window cuts) |
| 10 | Day and night: white and warm through tan FR4 | Needs X (bench) |
| 11 | The path to a board | Needs X |

## 1. Light sources and connection, end to end

### Finding 1. The nine lights (OK)

| Light | Window (*measured*) | Sold part, colour | Held by | Channel (K4W411's J2 map) |
|---|---|---|---|---|
| MODE arc | r 14.2 about (24.89, 16), 130 to 230 deg | 38 flex, warm (the flex is sold as "yellow") | arc clips; over-length folded back (K4W411 #7) | CH1 |
| FIELD up, down | r 10.6 about (63.99, 16), 50 deg each | 18.5 rigid, warm white, level on the chord (or 38 flex) | two clips each | CH2 |
| SUB up, down | the same about (87.37, 16) | the same | two clips each | CH3 |
| Key - arc, key + arc | r 10.0, 150 deg each | **38 flex, white** | arc clips | CH4 |
| **S, the sun** | disc dia 2.3 and eight rays to r 2.35 at (118.885, 8.35); x 116.71 to 121.06, y 6.19 to 10.51 | 18.5 rigid, warm white, level at y 8.35, x 109.64 to 128.13 (K4W411's S place) | two end clips | CH5 |
| **P, five moons** | dia 2.9 at y 6.3, x 153.7 to 168.1; lit parts x 153.7 to 155.15, 157.3 to 158.75, 159.45 to 162.35, 163.05 to 164.5, 166.65 to 168.1 | **18.5 rigid, white**, level at y 6.3, x 151.65 to 170.15 (K4W411's P place) | finding 2 | CH5 |

* **Wiring and drive:** K4W411 #1 and #3 apply (no PWM chip on DRV yet; J2 with a 120R per light on the fascia's back).
* **Current** (*inferred*, 20 mA a light): CH1 20, CH2 40, CH3 40, CH4 40 (white), CH5 40 (warm S, white P). **180 mA**, nine
  lights; 20 mA less than K4W411.
* **Sharing:** S (warm) and P (white) share CH5 with one resistor each: K4W411 #2 applies (different colours in parallel need
  their own resistors, and get them). The two white key arcs share CH4 (same colour, same behaviour).
* **Day and night, an option:** the face's idea is the sun by day and the moon by night. If the owner wants them to light at
  different times, S and P need their own channels: S on CH5, P on CH6 (J2's spare pin 7). Cost: one more DRV channel and FET.
  Nothing else on the fascia changes.
* **No new light place:** S and P are exactly K4W411's bars (*measured*: the face's script, kawaii-2's places). The common base's
  pads serve this face as they are.

### Finding 2. The moons' bar has no place for its clips (Needs X)

* K4W411 #6: if the buttons' boxes stand 13.75 across, the P bar's end clips (x 151.65 to 153.65 and 168.15 to 170.15) land on
  the boxes, so it moves the clips into the 7.2 mm gap between the boxes, x 157.5 to 164.3.
* Here the moons fill that gap. Between the lit parts there are **0.70 mm** (x 158.75 to 159.45 and 162.35 to 163.05). With 0.3
  kept off each window, **0.10 mm** is left: no clip fits (*inferred* from the measured outlines). A clip leg on a moon's pour
  cut would shadow it.
* At the ends there is room in x (151.65 to 153.4 and 168.4 to 170.15, 1.75 mm, clear of the moons), but that is on the boxes
  in the 13.75-across orientation.
* **Fix**, after K4W411 #5's bench check of the button:
  * **Boxes 16.91 across** (their tops at y 9.125): end clips as drawn. The bar's foot is 1.83 mm above the boxes. Cost: none.
  * **Boxes 13.75 across** (tops at y 7.545, 0.245 under the bar): hold the bar by its two soldered leads plus a dab of clear
    silicone at each end, over the boxes' top edge. Or end clips with a top leg only, landing at y 4.5 to 5.3 (0.8 mm, under the
    top band; the moons are not under the ends). Cost: none in parts; the silicone is a hand step.
* The outer crescents' lower horns reach y 7.76, 0.21 into the boxes' outline in the 13.75-across case (*measured*). A box
  behind a horn's tip shades a sliver that gets little light anyway: no change.

### Finding 3. The P bar's lead pads (Needs X)

The same as the science-2-3 grill's finding 5, because the bar and the key arcs are at the same places:
* between the bar's end cap (x 150.65) and the key - arc's end cap (x 148.81) there are 1.84 mm; a 1.5 mm pad with 0.3 each side
  needs 2.1; above is the top band and below are the boxes;
* **fix:** pads 1.0 wide x 1.5 tall at **(149.73, 6.3)** and **(172.07, 6.3)**, keeping 0.45 to the arcs' ends and the bar
  and 0.50 to the boxes (*measured*);
* it holds for K4W411's P bar too (same place).

### Finding 4. The sun's bar and its pads (OK)

* The bar lies on K4W411's S place, so K4W411's numbers apply: 1.03 mm to R7's lower pad on the art model's pill (the splayed
  R7 and R8, as K4W411's bunny), and only the GND pour behind it on rev B (*measured*: no rev B back copper within 0.5 of the
  sun).
* K4W411 #8's left-lead problem was the stack bar. This face has no stack: the left lead is free. A pad at (107.64, 8.34) fits
  (*measured*, by the search in the routing table's note).
* The right lead: the nearest free pad is (130.16, 8.34), but that takes 0.41 of K4W411's J2 spot (a) (x 130.5 to 139.0).
  **Fix:** bend the lead down to a pad at **(129.0, 10.5)**, under the bar's right end.
* The disc and rays span y 6.19 to 10.51; the bar's body covers 7.35 to 9.35. The rays' tips run 1.16 mm past the body and read
  dimmer. On a sun that reads as rays fading out: no change.

## 2. Mechanics

### Finding 5. The top band (K4W411 #8 applies, less the stack)

The moons' top is at y 4.86, 0.36 below t 4.5; the bar's body tops out at 5.3 (*measured*). Clips,
leads and pads stay under t 4.5 (findings 2 and 3). MODE's over-length and the FIELD-up and SUB-up clips as K4W411 #8.

Depth (K4W411 #9), the base windows on rev B (#4), the key arcs and the boxes (#5) and the forms (#7) apply as written there:
the seven base windows are the same polygons (*measured*).

## 3. Fab

### Finding 6. The rails shown in gold (Needs X, the owner's call)

The face opens the mask over the two rails, GND on top and +5V below, as ENIG. Two facts the face run did not have:

* **Rev B has no rails.** Its front copper is the old rhythm art (18 lines, 5 arcs and 8 texts on F.Cu, each with a mask
  opening) and no power on the front; GND is the back pour and +5V a back track at y 39.0 (*measured*). The rails exist only
  on the art model, the through-hole layout K4W411 #15 talks about.
* **On that through-hole layout the rails are the power wiring** (*measured*: the art model's rails carry the nets "gnd" and
  "p5v", 0.8 wide, at y 2.767 and 29.233, x 9.0 to 182.4, with the dial's and ladder's ends on them). Opening the bottom one puts
  bare +5V on the face, where fingers go. From the +5V rail (*measured* on the art model, full rail):
  * 1.65 mm to the dial's tap-5 pad (exposed gold, on the dial's divider);
  * 4.68 mm to the nearest exposed GND gold (FIELD's ring);
  * 1.13 mm to masked GND copper (the ladder's capsule).
  5 V is safe to touch. The risks are small: a dropped tool across rail and ring, a static spark into +5V rather than GND, and
  skin films across 1.65 mm into the dial's divider (*assumed* negligible against its 10k to 20k values).
* **Fix, my pick: draw the rails as gold with no net** (power on the back). On rev B's base (K4W411 #15 (b)) that is the
  natural way: they are new front copper anyway. On the through-hole base (#15 (a)) it moves the +5V run to the back.
  Then nothing at 5 V shows. Cost: none on rev B's base; a back re-route on the through-hole base.
* **Other ways:** keep +5V under the mask and show only GND (breaks the dial panel's mirror on y 16, where the two rails are
  each other's images); or accept bare +5V as drawn.
* The rails keep 2.37 mm or more from the board edge (*inferred*: 2.767 − 0.4), over pass 4's 1.4 rule for gold.

### Finding 7. Slivers at the panel seams (Needs X)

* The panels are cut by masks and mirrored. Where a line straddles a seam or the board's margin, the cut keeps a sliver
  (*measured*, opening by a 0.13 mm disc at 23 px per mm):
  * gold: 0.04 mm slivers 10.5 mm and 9.0 mm long at x 184.96 to 185.00 (the right narrow panel's seam), 4.8 mm long at x 55.83,
    and 4 mm long along y 39.35 to 39.39 (x 22.9 to 26.9, the bottom margin);
  * white: short pieces only (the largest 0.15 mm², by FIELD's and SUB's upper windows at y 4.1 to 4.6).
* In all, 1.8 % of the white area and 1.6 % of the gold is narrower than about 0.13 mm (about 1,000 and 450 pieces); most are
  the round-cut ends where white stops short of gold.
* A 0.04 mm gold sliver cannot be etched; it vanishes or lifts (*assumed*, standard fab behaviour).
* **Fix:** after the cuts, drop every piece narrower than 0.15, in the vector export (K4W411 #16). Cost: one filter.

### Finding 8. Sharp tips (OK)

The sun's rays (0.8 mm at r 1.55, to a point at r 2.35), the crescents' horns and the four-point stars narrow to points. Mask
openings and silk round off at the fab's limit; the last 0.2 mm or so of each tip will be blunt or ragged (*assumed*). They
read the same from a step away. No change, or blunt each tip at 0.15 (silk) and 0.2 (windows) in the export.

Everything else is as K4W411 #10 and #11 (coupon and order notes; the drawn widths and webs pass).

## 4. Light quality

### Finding 9. The moons' and the sun's glow; webs (OK)

* **The moons:** the bar's lit length (1 mm dark at each end, *assumed*) runs x 152.65 to 169.15. The lit parts span 153.7 to
  168.1: 1.05 mm of margin each side. In y they span 4.86 to 7.76 over a body of 5.3 to 7.3, 0.46 past it each way. Even
  (*assumed*, as K4W411 #12 takes 2 mm bars for windows up to 4 mm).
* **The webs** between the half moons and the full moon are 0.70 mm of mask, wider than K4W411's 0.45. K4W411 #12's fix applies:
  cut the back pour per moon (outline plus 0.1), not as one slot, so the moons stay apart when lit.
* **The sun:** finding 4. One cut for the disc and rays together is fine (they are one shape).
* **Bleed** (K4W411 #14): the moons' nearest other window is a key arc's end, 4.9 mm from the outer horn (*inferred*). Both are
  white: no colour bleed. The sun is 18 mm from any other window (the key - arc).

### Finding 10. Day and night: white and warm through tan FR4 (Needs X, bench)

* The face's meaning is two colours: warm for the day lights (MODE, the levers, the sun), white for the night (the moons and the
  key arcs).
* K4W411 #13 says bare FR4 glows tan and white reads cream. If white comes out cream, the night lights move toward the day
  lights, and the split the face is built on gets weak (*assumed*).
* "White" is also two sold parts here: the 38 flex in white (the key arcs) and the 18.5 bar in white (the moons). Their match is
  *assumed*.
* **Fix:** on K4W411 #10's coupon, put a warm-white bar, a white bar and a white flex side by side behind the same FR4. If the
  white reads too warm, a blue-ish cast helps: drive the white a little harder (its resistor), or accept cream as "moonlight".
  Cost: none.

## 5. The path to a board

### Finding 11. What the board-change run must do (Needs X)

K4W411 #15 (the face is drawn on the through-hole art model; rev B is surface-mount; the splayed R7 and R8 are K4W411's bunny
ears) and #16 (layers from vectors, re-checks) apply. What this face adds:
1. **The rails' net** (finding 6): no-net gold on either base, my pick.
2. **The P bar's holding** (finding 2) after K4W411 #5's measure; its pads 1.0 wide (finding 3); the sun's right pad off J2's
   spot (finding 4).
3. **Per-moon pour cuts** (finding 9).
4. **Art export:** the sliver filter (finding 7).
5. **Bench:** warm against white through FR4 (finding 10); K4W411's checks.
6. **Owner:** day and night on one channel or two (finding 1).

**What KiCad or the fab cannot make as drawn:** the seam slivers. Everything else can be made.

## Routing needs

Board: fascia R (the common base; rev B's frame). Pads are on B.Cu, 1.5 x 1.5 unless said. They come from a search that keeps 0.3
off the face's windows, every light body of the face, rev B's back copper, the control bodies (both orientations where not
known), J1's plug, the screw bosses (r 3.5), the top band (t < 4.5) and 0.5 off the edge (*measured* on the raster); the lever
pads between FIELD and SUB, the P pads and the sun's right pad were set by hand and checked the same way. Channels and pins are
K4W411's J2 map (pin 1 +5V_L). The seven base lights and both bars sit where K4W411's do, so these rows are K4W411's too, with
K4W411's colours (pink key arcs and S, blue P) in place of this face's.

| id | face | board | source (form, sold length, colour) | pad A (x, y, layer) | pad B (x, y, layer) | mA | shares with | proposed channel | connector pin | conflicts (copper, parts, 185 V, case) | evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| cel-MODE | celestial-3 | fascia R | 38 flex, warm (yellow) | (15.76, 28.91, B.Cu) | (12.34, 5.26, B.Cu) | 20 | none | CH1 | J2.2 | body on rev B +5V at (12.6, 23.1) (K4W411 #4); window top at y 4.14 in the top band | measured |
| cel-FLDu | celestial-3 | fascia R | 18.5 rigid, warm white, level y 5.9, x 54.74 to 73.24 | (52.74, 5.91, B.Cu) | (74.0, 8.0, B.Cu) | 20 | FLDd | CH2 | J2.3 | none on rev B | measured |
| cel-FLDd | celestial-3 | fascia R | 18.5 rigid, warm white, level y 26.1, x 54.74 to 73.24 | (52.74, 26.11, B.Cu) | (74.0, 28.2, B.Cu) | 20 | FLDu | CH2 | J2.3 | body on SW2.1, SW2.2, LEVA, A7, +5V (K4W411 #4) | measured |
| cel-SUBu | celestial-3 | fascia R | 18.5 rigid, warm white, level y 5.9, x 78.12 to 96.62 | (77.4, 8.0, B.Cu) | (98.66, 5.91, B.Cu) | 20 | SUBd | CH3 | J2.4 | none on rev B | measured |
| cel-SUBd | celestial-3 | fascia R | 18.5 rigid, warm white, level y 26.1, x 78.12 to 96.62 | (77.4, 28.2, B.Cu) | (98.64, 25.06, B.Cu) | 20 | SUBu | CH3 | J2.4 | body on SW3.1, SW3.2, LEVB, A7 (K4W411 #4) | measured |
| cel-KEYm | celestial-3 | fascia R | 38 flex, white | (147.81, 27.69, B.Cu) | (144.44, 5.26, B.Cu) | 20 | KEYp | CH4 | J2.5 | body on SW4.1; over the box corners (K4W411 #5) | measured |
| cel-KEYp | celestial-3 | fascia R | 38 flex, white | (177.39, 5.26, B.Cu) | (173.99, 27.69, B.Cu) | 20 | KEYm | CH4 | J2.5 | body on D8, SW5.2; over the box corners (K4W411 #5) | measured |
| cel-S | celestial-3 | fascia R | 18.5 rigid, warm white, level y 8.35, x 109.64 to 128.13 (K4W411's S place) | (107.64, 8.34, B.Cu) | (129.0, 10.5, B.Cu) | 20 | P | CH5 | J2.6 | 1.03 to R7's lower pad on the through-hole pill; pad B kept off J2 spot (a) | measured |
| cel-P | celestial-3 | fascia R | 18.5 rigid, white, level y 6.3, x 151.65 to 170.15 (K4W411's P place) | (149.73, 6.3, B.Cu), 1.0 x 1.5 | (172.07, 6.3, B.Cu), 1.0 x 1.5 | 20 | S (or alone on CH6) | CH5 (CH6 for day and night) | J2.6 (J2.7) | 0.245 above the boxes (13.75 across); no clip place between the moons (finding 2) | measured, inferred |

* **Total:** 180 mA (nine lights at 20 mA).
* **Channels alone:** 5 (CH1 MODE, CH2 FIELD, CH3 SUB, CH4 keys, CH5 S + P); 6 if the sun and moons light apart.
* **If same-colour lights share:** warm MODE, FIELD, SUB, S on one and white keys and P on another: 2, if the arcs may light
  together; colour alone never needs more than 2.
* **Connector pins:** 6 of K4W411's 7-way J2 (+5V_L, CH1 to CH5); 7 with day and night apart.
* **Forces on fascia R that other faces may not need:** the rails as no-net gold on the front (if the rails show); the P bar held
  without clips between the boxes (any face whose P windows fill x 157.5 to 164.3). Nothing on DRV or DISP beyond K4W411 #1,
  plus one channel if day and night light apart.

## 6. Left open

* Not measured: the buttons' stand-off and orientation (K4W411 #5), which decides finding 2; white against warm through FR4
  (finding 10).
* Not done: routing on any board; KiCad DRC; the through-hole layout's back copper (no board exists, K4W411 #15).
* The pads in the table are places that fit, not a layout. The routing-plan run sets them.
