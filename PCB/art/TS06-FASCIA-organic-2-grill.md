# TS06 fascia organic-2: the grill of 2-1 The print and 2-2 Mushroom (can they be built, will they work)

2026-10-15, run grill-organic. The owner (00:0x UTC): "run grills on all, compile insights for the final pcb routing plan". 2-1 The
print and 2-2 Mushroom are on the owner's shortlist of final candidates, not approved yet. This page reviews both faces and proposes
fixes. It applies none: no board, schematic, fab, tool, 3D, firmware or spec file was touched, and the faces and their write-up
([TS06-FASCIA-organic-2.md](TS06-FASCIA-organic-2.md)) are unchanged. The scripts are scratch, not in the repo. No marked picture: the
owner's change during the run made the doc the deliverable.

The model is the K4W411 grill ([TS06-FASCIA-K4W411-grill.md](TS06-FASCIA-K4W411-grill.md)). What it settled for every fascia is cited
as "K4W411 #n" and not repeated. This page adds only what is new or different for these two faces.

Marks:
* *measured*: read from a repo file (board, case model), from the face run's own model and rasters, or from my own raster tests on
  them (40 px per mm against the board; the delivered 11.5 and 23 px per mm rasters for the art).
* *inferred*: arithmetic on measured numbers.
* *assumed*: my reading, or a value nobody has measured.

**Coordinates:** fascia R's own frame, in mm. The origin is the board's top-left corner seen from the front; x runs right, y runs
down. This is KiCad's frame for rev B (`PCB/TS06-FASCIA-rhythm/TS06-FASCIA-rhythm.kicad_pcb`) and the art model's frame. Parts on the
back are given in the same front-view numbers. "t" is y measured down from the top edge.

## Verdict

| Face | Verdict | New blockers | New Needs X |
|---|---|---|---|
| **2-1 The print** | **Buildable after changes.** Not on the ordered board as it stands. The art has no blocker. | none (K4W411 #5 applies: the same key arcs) | 1, 2, 3, 7, 8, 11 |
| **2-2 Mushroom** | **Buildable after changes.** Not on the ordered board as it stands. The art has no blocker. | none (K4W411 #5 applies) | 1, 2, 3, 12, 13, 14, 17 |

The biggest new item is **finding 1**: the S light, as the face run drew it, has no place in a light base shared with K4W411. The
fix is a small face change: put S on K4W411's stack bar.

| # | Item | Face | Rating |
|---|---|---|---|
| 1 | S has no place in a light base shared with K4W411 | both | Needs X |
| 2 | P on K4W411's P bar place; its clips land behind the window | both | Needs X |
| 3 | The T layout's ladder joints sit in the top band behind the sill | both | Needs X (T layout only) |
| 4 | Channels, the connector, the current | both | OK |
| 5 | AMBIENT's gold trace and its stem | both | OK |
| 6 | The lit fork and the lit lake: glow, bleed, hot spots | 2-1 | OK |
| 7 | The lake's island needs back copper behind it | 2-1 | Needs X |
| 8 | The opened GND rail: the screw heads, and its net | 2-1 | Needs X |
| 9 | Fine features | 2-1 | OK |
| 10 | Colours by day and lit | 2-1 | OK |
| 11 | The print has no vector source | 2-1 | Needs X |
| 12 | The S mushroom on a level bar: a dim cap | 2-2 | Needs X (fixed by 1) |
| 13 | P: the drawn bar runs into the push buttons' boxes | 2-2 | Needs X (fixed by 2) |
| 14 | Green S and P | 2-2 | Needs X (bench) |
| 15 | The pill: R7 and R8 lean in | 2-2 | OK (with K4W411 #15) |
| 16 | Fine features and the white rail lines | 2-2 | OK |
| 17 | The strokes are clipped on the raster | 2-2 | Needs X |

## 0. What K4W411's grill settles for both faces

Both faces stand on the same model as K4W411 (pass 4's E1, the through-hole "T" art model, rings-and-dots) and keep its seven base
windows unchanged: MODE arc, FIELD up and down, SUB up and down, the two key arcs (*measured*: the face script's window list).

| K4W411 # | Applies? | What is different for organic-2 |
|---|---|---|
| 1 DRV has no PWM chip | applies | the same 5 fascia channels (finding 4) |
| 2 one resistor per bar on a shared FET | applies | channel 5 carries S and P only: 40 mA, not 60. On 2-2 both are green |
| 3 the new connector J2, pin map, routes | applies unchanged | pin 6 carries 40 mA. Spot (a), x 130.5 to 139.0, is clear of every organic source |
| 4 base windows over rev B's back copper | applies unchanged | the same five windows; the S and P windows sit over the GND pour only, 14.7 mm or more from any track (*measured*) |
| 5 key arcs against the push buttons' boxes | applies unchanged | **Blocker until measured**, for both faces |
| 6 the P bar's clips | changed | finding 2 |
| 7 filament forms and lengths | applies unchanged | |
| 8 the stack bar; nothing on the back above t 4.5 | partly | organic has no stack. Finding 1 puts S on the stack's place; finding 3 adds the ladder's joints to the top band |
| 9 depth behind the fascia | applies | |
| 10 the coupon and the order notes | applies | add: green through bare FR4 (2-2), a 0.75 mm slot ring round a mask island (2-1), a 0.65 mm stem (2-2) |
| 11 fine features | applies | numbers in findings 9 and 16 |
| 12 the stack's glow | no stack | its fix applies to every organic window: cut the back pour per window outline plus 0.1 |
| 13 colours through bare FR4 | applies | findings 10 and 14 |
| 14 bleed between lights | applies | findings 6 and 14 |
| 15 the face is drawn on the T art model | applies | both faces; 2-2 also moves R7 and R8 (finding 15) |
| 16 KiCad layers from vectors, re-checks | applies | findings 11 and 17: both patterns come out of a raster |

## 1. Shared by both faces

### Finding 1. S has no place in a light base shared with K4W411 (Needs X)

**What the face run drew** (*measured*: the face script's back view, scratch `pages2.py`; the write-up calls it *assumed*):
* S keeps "its old tail", an 18.5 rigid bar lying level and centred on the window: y 6.0 on 2-1, y 6.6 on 2-2, x about 99.8 to 118.3.
* The S windows: 2-1's fork x 106.05 to 111.15, y 4.70 to 7.30; 2-2's mushroom x 106.75 to 110.43, y 4.35 to 7.97 (*measured*).

**The clash with K4W411, the approved face** (*measured* on K4W411's write-up, section 4, and its grill #8):
* K4W411's stack bar stands plumb at x 107.3 (body x 106.3 to 108.3), y 5.6 to 24.1 (or 6.26 to 24.76, centred as K4W411 #8
  proposes).
* The organic S bar crosses it at x 106.3 to 108.3, y 5.0 to 7.0. Only one of the two can be fitted.
* The stack bar's top pad, at about (107.3, 5.3), lies right behind the organic S window. Copper behind a window darkens it.
* So one pad set cannot serve both faces. The owner's rule for the base ("the sources and pads stay, windows differ") breaks at S.
* K4W411's other S place (level at y 8.35, x 109.64 to 128.13, inside the pill) does not suit either: it lights only x 110.6 and
  right, and the pill's copper starts at x 113.7.

**Fix (a), my pick: put organic's S on K4W411's stack bar.** A face change, no board cost.
* 2-1: turn the fork upright, about x 106.0 to 108.6, y 7.6 to 12.7. The ridges left of the pill run up and down there (seen on a
  crop of the face, *assumed*), so an upright fork follows the print. The fork is 2.6 mm wide: 0.3 mm past the bar body on each side.
* 2-2: stand the mushroom on the bar, cap up, about y 7.6 to 11.2. The stem runs along the bar; the 3.7 mm cap reaches 0.85 mm past
  the body on each side, like K4W411's bottom pal (1.0 mm). It lights better than any level bar (finding 12).
* Keep the window 1 mm or more below the bar's top end (6.26 centred), for its dark end (K4W411 #8's bench check).
* If the base also carries K4W411's S-bar pad at (109.7, 11.3), the upright fork's right edge keeps 0.35 mm to it (*inferred*;
  rule 0.30). The mushroom's cap keeps 1.1 mm.
* Cost: a face re-run (the S window moves 1.3 mm left and about 3 to 5 mm down; the pattern re-grows round it). The base gains no
  pads.

**Fix (b): keep the faces as drawn and give organic its own level S bar.** Cost: two pads that only organic boards carry; those
boards cannot carry the stack bar's pads; the base is then not common at S.

### Finding 2. P on K4W411's P bar place; its clips land behind the window (Needs X)

**P fits K4W411's P bar place** (level, y 6.3, x 151.65 to 170.15; body y 5.3 to 7.3). *Measured* on my 40 px per mm raster of the
windows:
* 2-1's lake: 2 % of its area lies more than 0.5 mm beyond the bar body; the farthest point is 0.62 mm (its top edge).
* 2-2's mushrooms: 4 % more than 0.5 mm; the farthest is 0.85 mm (the stems' feet).
* Both light well enough (*assumed*; K4W411 #12's bench decides). So P needs no face change and no pads of its own.

**The clips do not fit.**
* K4W411 #6 moves the P bar's clips into the 7.2 mm gap between the two push buttons' boxes, x 157.5 to 164.3, because the bar's
  ends sit over the boxes if they stand 13.75 mm across.
* K4W411's P windows (the eyes) sit outside that gap. Organic's sit inside it: 2-1's lake spans x 157.13 to 164.67, the whole gap;
  2-2's mushrooms span x 158.37 to 163.57, leaving 0.87 and 0.73 mm.
* A clip's feet land on the board beside the bar, behind the parts of the window past the bar body (the lake's top, the stems'
  feet). They would shade them (*assumed*). Feet above the bar would also reach the top band (t 4.5, K4W411 #8).

**Fix:** hold the P bar by its two soldered leads plus a dab of clear adhesive at each end, outside the windows. Or use end clips
once K4W411 #5's bench measure shows a gap behind the boxes deeper than the clip. Cost: none.

**Pads at the P bar's ends are tight.** The key arcs' top ends and the P bar's ends leave about 3.6 mm in x for two pads on each
side (*inferred*: the - arc's flex ends at x 147.6 to 148.1, the bar at 151.65; mirrored on the right). Use 1.2 mm pads with 0.4 mm
between them (Routing needs below). The same holds for K4W411.

### Finding 3. The T layout's ladder joints sit in the top band behind the sill (Needs X, T layout only)

* On the T art model, R1, R7 and R8 have their top leads on the GND rail at **y 2.77** (*measured* on the model: R1 at (28.44, 2.77),
  R7 at (116.09, 2.77), R8 at (121.69, 2.77); 2-2 moves R7 and R8 to (114.50, 2.77) and (123.27, 2.77)).
* On the T layout these are plated holes. Each leaves a cut lead and a solder joint standing about 1 to 1.5 mm off the back
  (*assumed*), about 1.9 mm across (*inferred*: 2-2's bottom pads are 2.90 apart centre to centre and 1.00 apart edge to edge).
* The sill stands behind the top 3.6 mm of the fascia; variant D's top rail behind the top 4.5 mm (K4W411 #8, *measured* there).
  The joints span y 1.8 to 3.7: inside both.
* R1 may sit where the sill steps back over the rotary (to 3.5 mm deep, case checks group 8). The case model uses a stand-in board,
  so this is *assumed*. R7 and R8 have no such step.
* This holds for K4W411 too (its R7 and R8 tops are on the same rail). Its grill did not list it.

**Fix**, one of:
* path (b) of K4W411 #15 (keep rev B's surface-mount ladder on the back): nothing stands there;
* on the T layout, move the ladder's top holes down to y 5.5 or more, with a short stub from the rail. The pill's art shortens by
  about 2.7 mm at the top;
* step the sill back over x 112 to 126, as over the rotary. A case change.

Cost: small either way. It does not touch the lights.

### Finding 4. Channels, the connector, the current (OK)

* Both faces light 9 filaments: the base's 7, S and P. With K4W411's grouping that is **5 channels**: CH1 MODE, CH2 FIELD up and
  down, CH3 SUB up and down, CH4 the keys, CH5 S and P (*inferred*; the grouping is the face run's *assumed* one and K4W411's).
* J2's pin map (K4W411 #3) serves both faces unchanged: pin 1 +5V_L, pins 2 to 6 CH1 to CH5, pin 7 spare.
* Current at 20 mA a filament (120R at Vf 2.6, K4W411 #2): **180 mA**, 20 mA less than K4W411. Against the same clock with K4W411, every 5 V
  figure drops by 20 mA (*inferred*).
* CH5 carries 40 mA. S and P share it: same colour on each face, same behaviour.
* If every same-colour source shared one channel: 2-1 would need 1 (all warm), 2-2 would need 2 (warm, green). Then the controls'
  lights could not light one at a time.

### Finding 5. AMBIENT's gold trace and its stem (OK)

* The trace (45.04, 20.62 to 21.58, 0.35 wide) is tied to FIELD's ring by a masked stem 0.25 wide and 12.9 mm long, under the tube
  map's white dots (*measured*: the face script).
* On rev B there is no front copper and no plated hole (*measured*: no F.Cu tracks, no vias; only a GND zone on the back). The gold
  net reaches GND only through front-merge's via on the link at (75.68, 16.0), a plated hole (K4W411 #15).
* Without that via, the stem just joins two isolated gold islands. With it, the trace is on GND. Either is fine.
* Silk dots over masked copper are normal. The stem keeps 1.5 mm or more from AMBIENT's circle mark (*inferred*).
* Cost: none. Drop the stem if the owner wants no masked copper there.

## 2. organic-2-1 The print

![organic-2-1](TS06-FASCIA-organic-2/organic-2-1-the-print.png)

**Verdict: buildable after changes.** All its lights are warm and sit on K4W411's places once S moves (finding 1). New work: S's
upright fork, the lake's back copper, the rail's screw keep-out, and a vector trace of the print.

### Light sources, end to end

| Light | Sold part, colour | Held by | Its leads | J2 pin | DRV | Findings |
|---|---|---|---|---|---|---|
| MODE arc | 38 flex, yellow | arc clips; the over-length folded back off the board | pads past each end: anode via 120R to +5V_L, cathode to CH1 | 2 | CH1, 20 mA | K4W411 #4, #7 |
| FIELD up, down | 18.5 rigid, warm white, on the chord | two clips each | the same; both cathodes to CH2 | 3 | CH2, 40 mA | K4W411 #4, #7 |
| SUB up, down | the same | two clips each | both cathodes to CH3 | 4 | CH3, 40 mA | K4W411 #4, #7 |
| Key - arc, key + arc | 38 flex, yellow | arc clips; the over-length folded back | both cathodes to CH4 | 5 | CH4, 40 mA | K4W411 #4, #5, #7 |
| S, the lit fork | 18.5 rigid, warm white, on the stack's place (finding 1) | two end clips | cathode to CH5 | 6 | CH5 | 1, 6 |
| P, the lit lake | 18.5 rigid, warm white, on K4W411's P place | leads plus adhesive (finding 2) | cathode to CH5 | 6 | CH5, 40 mA with S | 2, 6, 7 |

*Inferred* from K4W411 #1 to #3. No clip, pad or route is drawn on any board.

### Finding 6. The lit fork and the lit lake: glow, bleed, hot spots (OK)

* **Glow** (*measured* on my raster of the windows, against a 2.0 mm bar body):
  * the fork, 6.74 mm2, slot 0.9: on the drawn level bar every point is within 0.30 mm of the body. Upright on the stack bar
    (finding 1), its 2.6 mm width puts 0.3 mm past each side. Even (*assumed*).
  * the lake, 9.06 mm2, slot 0.75: within 0.33 mm of the drawn bar, 0.62 mm of K4W411's P place. Even, a little dimmer at the
    top on the P place (*assumed*).
* **Halo:** narrow slots in black mask over 2.0 mm FR4. The pour cut per window outline plus 0.1 (K4W411 #12's way) keeps the light
  to the slot.
* **Bleed:** every light on this face is warm, so bleed changes no colour. The nearest other lit window to the lake is the - key
  arc, 9.1 mm away; to the fork, SUB up, 14 mm (*inferred*).
* **Hot spots:** no bar end lies under a window. The windows are 2.6 to 7.5 mm long on an 18.5 bar.

### Finding 7. The lake's island needs back copper behind it (Needs X)

* The lake is a 0.75 mm slot ring that closes round an island of mask, about **2.95 x 1.15 mm** (*inferred* from the face script:
  ring semi-axes 1.85 and 0.95, slot 0.75).
* **If the back pour is cut once under the whole lake,** the bar lights the FR4 under the island. Black mask passes a little light,
  so the island may glow dimly instead of reading dark (*assumed*; the coupon decides).
* **If the pour is cut per ring** (outline plus 0.1), a copper island 2.75 x 0.95 mm stays behind the island. But it is not joined
  to the pour. KiCad's zone fill removes unjoined islands by default, so it would vanish without notice.
* **Fix:** keep it as a no-net copper shape on B.Cu (drawn, not poured), or set that zone to keep islands. Cost: one shape.

### Finding 8. The opened GND rail: the screw heads, and its net (Needs X)

* **Screw heads:** the rail is opened in the mask along its whole length, including the two top corners where it turns down at
  x 9.0 and x 182.4.
  * There it comes **1.86 mm from H1's screw head and 1.95 mm from H2's** (*measured* on the delivered 11.5 px per mm raster, plus
    or minus 0.09). The face's own rule is 3.0.
  * The face's check table says 3.05 because it measured the pattern gold only. The rail's gold has no screw keep-out (*measured*:
    the face script's rail function).
  * **Fix:** keep the corners and the short drops masked. Open only the straight run from x 10.8 to 180.6. Every point of that run
    is 3.0 or more from both heads (*inferred*: the run must start at x 9.9 or more). Cost: none.
* **Its net:**
  * On the T layout, the rail is real GND: R7's and R8's tops sit on it. Opened, it is exposed GND.
  * Rev B has no front copper and no plated hole. There it is an isolated gold strip, unless vias tie it to the back pour. Vias are
    plated holes, which spec section 6 rules out for R.
  * Either way it is fine (ENIG islands plate, K4W411 #11). A GND strip along the top edge is a harmless place to touch (*assumed*).
* Nothing stands in front of the fascia's top edge (the sill is behind it, K4W411 #8), so the rail shows as drawn.

### Finding 9. Fine features (OK)

*Measured* by the face run on its 23 px per mm raster (`checks2-1.json`, scratch). The limits are the fab's standard class
(`fab/ORDER.md`: silk line 0.15, silk text 1.0 high, mask web 0.10, copper clearance 0.15).

| Feature | 2-1 | Limit | |
|---|---|---|---|
| Thinnest white ridge | 0.17 | 0.15 | OK, 0.02 over: less than one raster pixel (finding 11) |
| Thinnest gold ridge | 0.26 | 0.15 | OK |
| White to gold (silk to a mask opening) | 0.22 (K4W411: 0.31) | the fab clips silk off openings | OK. The fab may trim up to about 0.1 off ridge ends near gold (*assumed*); not visible at 0.92 pitch |
| Pattern gold to other copper; mask web between gold ridges | 0.34 | 0.15; 0.10 | OK |
| The rail's opening to a pad's opening | 0.3 | 0.10 | OK |
| Gold to the board edge | 1.48 | 1.4 (pass 4's checker) | OK |
| Window slots; the lake's island | 0.75 and 0.9 wide; 1.15 wide | mask web 0.10 | OK |
| Pieces | 579 white, 333 gold islands | | OK: islands plate (K4W411 #11) |

### Finding 10. Colours by day and lit (OK)

* All warm: the colour that changes least through bare FR4 (K4W411 #13).
* By day the fork and the lake are tan ridges among gold ridges of a close hue, so they nearly vanish (*assumed*). That suits
  minutiae. Lit, they are the only glowing ridges.
* The glow drawn round them is light, not ink.

### Finding 11. The print has no vector source (Needs X)

* K4W411 #16 says: emit the face script's own polylines; do not trace the raster. **This face has no polylines for its ridges.**
  The ridge field is computed on a raster (filtered noise, thresholded), then split into white and gold and cleaned on the raster
  (*measured*: the face script's print function).
* Its fine margins are within a pixel: the thinnest white ridge is 0.17 against 0.15, and one pixel is 0.043 mm.
* **Fix:** regenerate the field at 46 px per mm or more. Trace each white and gold piece's outline, smooth it, and emit polygons
  (silk on F.Silkscreen; gold on F.Cu with no net, plus the same shape opened in F.Mask). Drop or thicken pieces under 0.15. Then
  re-run K4W411 #16's checks on the polygons.
* Cost: one tracing script and about 900 polygons. KiCad handles that count (*assumed*).

### Routing needs, 2-1

Coordinates in fascia R's frame (origin top-left, front view, mm). Pads 1.5 x 1.5 mm unless the row says so; every pad on B.Cu.
Pad places are *inferred* (1.0 to 1.5 mm past each window or bar end, kept below t 4.5 and off the controls' bodies), to within
about 1 mm.

| id | face | board | source (form, sold length, colour) | pad A (x, y, layer) | pad B (x, y, layer) | mA | shares with | proposed channel | connector pin | conflicts (copper, parts, 185 V, case) | evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 21-MODE | 2-1 | fascia R | flex, 38, yellow (warm); r 14.2 about (24.89, 16), 130 to 230 deg | (11.6, 5.6, B.Cu), outside the arc's top end | (17.0, 27.8, B.Cu) | 20 | none | CH1 | J2.2 | rev B's +5V track under the window (K4W411 #4); the flex's top corner reaches t 4.36: clear of the sill (3.6), 0.14 into variant D's rail (4.5); over-length folded off the board (K4W411 #7); no 185 V | window *measured*; pads *inferred* |
| 21-FU | 2-1 | fascia R | rigid, 18.5, warm white; on the chord, y 5.9, x 54.7 to 73.2 | (53.7, 5.9, B.Cu) | (74.2, 5.9, B.Cu) | 20 | 21-FD | CH2 | J2.3 | clip tops must stay below t 4.5 (K4W411 #8); rev B: GND pour only | *inferred* (K4W411 #7) |
| 21-FD | 2-1 | fascia R | rigid, 18.5, warm white; y 26.1, x 54.7 to 73.2 | (53.7, 26.1, B.Cu) | (74.2, 26.1, B.Cu) | 20 | 21-FU | CH2 | J2.3 | rev B's SW2 landing pads, LEVA and A7 under the window and the bar (K4W411 #4) | *measured* (rev B), *inferred* |
| 21-SU | 2-1 | fascia R | rigid, 18.5, warm white; y 5.9, x 78.1 to 96.6 | (77.1, 5.9, B.Cu) | (97.6, 5.9, B.Cu) | 20 | 21-SD | CH3 | J2.4 | as 21-FU | *inferred* |
| 21-SD | 2-1 | fascia R | rigid, 18.5, warm white; y 26.1, x 78.1 to 96.6 | (77.1, 26.1, B.Cu) | (97.6, 26.1, B.Cu) | 20 | 21-SU | CH3 | J2.4 | rev B's SW3 pads, LEVB, A7 (K4W411 #4); pad B sits on A7 (y 26.2) until A7 moves | *measured* (rev B), *inferred* |
| 21-K- | 2-1 | fascia R | flex, 38, yellow; r 10.0 about (150.4, 16), 105 to 255 deg | (149.3, 6.1, B.Cu), 1.2 mm pad | (149.3, 25.9, B.Cu) | 20 | 21-K+ | CH4 | J2.5 | the push button's box corners (K4W411 #5, **Blocker** until measured); rev B's SW4 pad 1 (K4W411 #4); pad A 0.4 mm from 21-P's pad A | *measured* (window), *inferred* |
| 21-K+ | 2-1 | fascia R | flex, 38, yellow; r 10.0 about (171.4, 16), -75 to 75 deg | (172.5, 6.1, B.Cu), 1.2 mm pad | (172.5, 25.9, B.Cu) | 20 | 21-K- | CH4 | J2.5 | K4W411 #5; rev B's SW5 pad 2 and D8's end at (173.0, 25.5) (K4W411 #4: re-route D8) | *measured* (rev B), *inferred* |
| 21-S | 2-1 | fascia R | rigid, 18.5, warm white; **K4W411's stack place**, plumb x 107.3, y 6.26 to 24.76 | (107.3, 5.3, B.Cu), 1.2 mm pad | (109.3, 24.3, B.Cu), sideways | 20 | 21-P | CH5 | J2.6 | needs the fork turned upright (finding 1); A7 1.3 mm below the bar's end, so pad B goes sideways (K4W411 #8) | *inferred* |
| 21-S-alt | 2-1 | fascia R | rigid, 18.5, warm white; level as drawn, y 6.0, x 99.8 to 118.3 | (98.8, 6.0, B.Cu) | (119.3, 6.0, B.Cu) | 20 | 21-P | CH5 | J2.6 | only if finding 1 (b): crosses the stack's place; T layout: passes 1.3 mm under R7's top joint | *measured* (face script), *inferred* |
| 21-P | 2-1 | fascia R | rigid, 18.5, warm white; K4W411's P place, y 6.3, x 151.65 to 170.15 | (150.9, 6.3, B.Cu), 1.2 mm pad | (170.9, 6.3, B.Cu), 1.2 mm pad | 20 | 21-S | CH5 | J2.6 | 0.25 mm above the boxes' tops if they stand 13.75 across (K4W411 #6); clips would shade the lake: leads plus adhesive (finding 2) | *measured* (windows), *inferred* |

* **Total:** 180 mA at 20 mA a filament (9 filaments; one S row is fitted, not both).
* **Channels needed alone:** 9, one per filament. With K4W411's grouping: 5.
* **Channels if same-colour sources share:** 1 (all warm).
* **Connector pins:** 6 of J2's 7 (+5V_L and CH1 to CH5); pin 7 spare.
* **Changes the other faces may not need:**
  * fascia R: S on the stack's place with an upright fork (finding 1); the lake island's B.Cu shape (finding 7); the rail's mask
    opening, stopped short of the corners (finding 8); a traced print (finding 11);
  * DRV, DISP: nothing beyond K4W411 #1 and #3.

## 3. organic-2-2 Mushroom

![organic-2-2](TS06-FASCIA-organic-2/organic-2-2-mushroom.png)

**Verdict: buildable after changes.** The lights are 2-1's, except S and P, which ship green. New work:
* stand S on the stack's bar, which also fixes its dim cap;
* move P up 0.3 mm, onto K4W411's place;
* try green on the bench;
* clip the strokes as vectors.

The moved R7 and R8 matter only on the T layout.

### Light sources, end to end

As 2-1's table (section 2), except: **S and P are 18.5 rigid bars, green** (sold: front-merge section 5), on CH5, J2 pin 6. S stands
on the stack's place (finding 1); P lies on K4W411's P place (finding 2). The seven base lights are warm, as on 2-1.

### Finding 12. The S mushroom on a level bar: a dim cap (Needs X, fixed by finding 1)

*Measured* on my 40 px per mm raster of the window (7.72 mm2, y 4.35 to 7.97), against a 2.0 mm bar body:

| Bar | Window more than 0.5 mm past the body | more than 1.0 mm | farthest point |
|---|---|---|---|
| the drawn tail, level at y 6.6 | 20 % | 4 % | 1.25 (the cap's crown) |
| level, centred on the window's area (y 5.87) | 8 % | 0 % | 1.10 |
| plumb on the stack's place, the mushroom stood on it (finding 1) | the cap's sides only | 0 % | 0.85 (*inferred*) |

* On the drawn tail the cap's top reads dimmer than its stem, the reverse of a glowing cap (*assumed*; the bench decides).
* **Fix:** finding 1 (a). If the owner keeps the face as drawn (finding 1 (b)), centre the level bar at y 5.87, not 6.6.
* Cost: none beyond finding 1.

### Finding 13. P: the drawn bar runs into the push buttons' boxes (Needs X, fixed by finding 2)

* The face run's back view lays P's bar level at y 6.6 (body 5.6 to 7.6), centred on the two mushrooms (*measured*: scratch
  `pages2.py`).
* If the boxes stand 13.75 mm across, their top edge is at y 7.545 (K4W411 #6). The bar's body then **overlaps both boxes by
  0.055 mm**, over x 152.0 to 157.3 and 164.5 to 170.5 (*inferred*). A bar cannot lie flat there.
* **Fix:** K4W411's P place, y 6.3 (body 5.3 to 7.3). It clears the boxes by 0.245 mm, and the mushrooms still light (finding 2:
  4 % of the window past 0.5 mm; the stems' feet at 0.85 mm).
* The stems' feet (y 7.55 to 8.18) lie at x 159.6 to 163.0, inside the gap between the boxes, so no box sits behind them
  (*inferred*).
* Cost: none.

### Finding 14. Green S and P (Needs X, bench)

* Green is sold as an 18.5 rigid bar (front-merge section 5). Both green lights share CH5: same colour, same behaviour. OK.
* **Forward voltage:** the repo has none for any colour (K4W411 #2). A green emitter often runs higher than a warm-white one. At
  3.0 to 3.2 V a 120R gives 15 to 17 mA, so green would read dimmer than the warm arcs (*assumed*).
* **Through bare FR4:** the tan board shifts green toward yellow-green (*assumed*, from K4W411 #13's tan reading). The bright mint
  of the drawing will not show. By day the mushrooms are tan shapes on black; they still read as mushrooms.
* **Bleed:** the nearest warm windows to a green one are the key arcs, 10.2 mm (+ arc) and 10.3 mm (- arc) from P (*inferred*). No
  mixing.
* **Fix:** add green to K4W411 #2's forward-voltage check and to the coupon (K4W411 #10, item 3). Trim S's and P's resistors to
  match the warm lights. Cost: none.

### Finding 15. The pill: R7 and R8 lean in (OK, with K4W411 #15)

* **On the T layout** (K4W411 #15 (a)):
  * R7's holes move to (114.50, 2.77) and (117.44, 11.28); R8's move to (123.27, 2.77) and (120.34, 11.28).
  * The 9.0 mm pitch is kept. The bottom pads are 1.00 mm apart edge to edge (*measured* by the face run), well over the 0.15 rule.
  * Four holes move; the nets do not.
  * Their top joints are still in the top band: finding 3.
  * The S bar on the stack's place keeps 6.2 mm to R7's top joint (*inferred*). The level bar of finding 1 (b) would pass 1.15 mm
    under it.
* **On rev B** (K4W411 #15 (b)): R6 to R8 stay surface-mount on the back. The leaning resistors are the cap's outer gills, so they
  must then be drawn as silk and gold, as K4W411 #15 (b) says for the bunny's ears.
* Nobody has drawn the back routes from the moved pads to J1 yet (K4W411 #15). Cost: part of #15.

### Finding 16. Fine features and the white rail lines (OK)

| Feature | 2-2 | Limit | |
|---|---|---|---|
| Thinnest white (the mycelium's joins, the half gills) | 0.17 measured; drawn at 0.15 to 0.18 | 0.15 | OK, at the limit. The script draws the joins exactly 0.15 wide, and its thin-piece filter keeps pieces down to 0.14 (*measured*: the face script). Emit them at 0.16 or more |
| Thinnest gold (full gills, little caps) | 0.25 | 0.15 | OK |
| White to gold; gold to other copper | 0.22; 0.35 | the fab clips silk; 0.15 | OK |
| Gold to the board edge; to a screw head | 1.61; 3.86 or more | 1.4; 3.0 | OK (*measured*: the face run; my raster for the heads) |
| Window necks: the narrowest stem | 0.65 | mask web 0.10 | OK. Add a 0.65 stem to the coupon (K4W411 #10) |
| Pieces | 298 white, 190 gold islands | | OK (K4W411 #11) |

* **The rails' white lines** (0.3 wide, on both masked rails):
  * on the T layout: silk over masked copper;
  * on rev B: plain silk, because rev B has no front rails.
  * Buildable either way.
* **For the owner:** K4W411's white stitch on the rails was removed at the owner's word ("rails look a bit wonky, remove them").
  This face draws rail lines again.

### Finding 17. The strokes are clipped on the raster (Needs X)

* Unlike 2-1, this face draws its strokes as polylines: gills, mycelium, the little mushrooms, the pill (*measured*: the face
  script). So the vectors exist.
* But every keep-out (names, windows, gold, the pill) and the thin-piece filter run on the raster, after drawing. Emitting the raw
  polylines would skip them.
* **Fix:**
  1. emit the polylines;
  2. clip them in vector form against the same keep-out outlines;
  3. drop pieces under the limits;
  4. re-run K4W411 #16's checks.

  Cost: a clipping step in the emit script; smaller than finding 11.

### Routing needs, 2-2

Same frame, pad rule and evidence marks as 2-1's table. The seven base rows are 2-1's (same windows, parts and pads). Only S, P and
the S-alt bar differ.

| id | face | board | source (form, sold length, colour) | pad A (x, y, layer) | pad B (x, y, layer) | mA | shares with | proposed channel | connector pin | conflicts (copper, parts, 185 V, case) | evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 22-MODE | 2-2 | fascia R | flex, 38, yellow (warm); r 14.2 about (24.89, 16), 130 to 230 deg | (11.6, 5.6, B.Cu) | (17.0, 27.8, B.Cu) | 20 | none | CH1 | J2.2 | as 21-MODE | *inferred* |
| 22-FU | 2-2 | fascia R | rigid, 18.5, warm white; on the chord, y 5.9, x 54.7 to 73.2 | (53.7, 5.9, B.Cu) | (74.2, 5.9, B.Cu) | 20 | 22-FD | CH2 | J2.3 | as 21-FU | *inferred* |
| 22-FD | 2-2 | fascia R | rigid, 18.5, warm white; y 26.1, x 54.7 to 73.2 | (53.7, 26.1, B.Cu) | (74.2, 26.1, B.Cu) | 20 | 22-FU | CH2 | J2.3 | as 21-FD (K4W411 #4) | *measured* (rev B), *inferred* |
| 22-SU | 2-2 | fascia R | rigid, 18.5, warm white; y 5.9, x 78.1 to 96.6 | (77.1, 5.9, B.Cu) | (97.6, 5.9, B.Cu) | 20 | 22-SD | CH3 | J2.4 | as 21-SU | *inferred* |
| 22-SD | 2-2 | fascia R | rigid, 18.5, warm white; y 26.1, x 78.1 to 96.6 | (77.1, 26.1, B.Cu) | (97.6, 26.1, B.Cu) | 20 | 22-SU | CH3 | J2.4 | as 21-SD (pad B on A7 until A7 moves) | *measured* (rev B), *inferred* |
| 22-K- | 2-2 | fascia R | flex, 38, yellow; r 10.0 about (150.4, 16), 105 to 255 deg | (149.3, 6.1, B.Cu), 1.2 mm pad | (149.3, 25.9, B.Cu) | 20 | 22-K+ | CH4 | J2.5 | as 21-K- (K4W411 #5 **Blocker** until measured) | *inferred* |
| 22-K+ | 2-2 | fascia R | flex, 38, yellow; r 10.0 about (171.4, 16), -75 to 75 deg | (172.5, 6.1, B.Cu), 1.2 mm pad | (172.5, 25.9, B.Cu) | 20 | 22-K- | CH4 | J2.5 | as 21-K+ | *inferred* |
| 22-S | 2-2 | fascia R | rigid, 18.5, **green**; K4W411's stack place, plumb x 107.3, y 6.26 to 24.76 | (107.3, 5.3, B.Cu), 1.2 mm pad | (109.3, 24.3, B.Cu), sideways | 20 (15 to 17 if green's Vf is 3.0 to 3.2) | 22-P | CH5 | J2.6 | needs the mushroom stood on the bar (findings 1, 12); A7 1.3 mm below the bar's end (K4W411 #8) | *inferred* |
| 22-S-alt | 2-2 | fascia R | rigid, 18.5, green; level, centred on the window's area, y 5.87, x 99.3 to 117.8 | (98.3, 5.9, B.Cu) | (118.8, 5.9, B.Cu) | 20 | 22-P | CH5 | J2.6 | only if finding 1 (b): crosses the stack's place; T layout: 1.15 mm under R7's moved top joint | *measured* (face script), *inferred* |
| 22-P | 2-2 | fascia R | rigid, 18.5, **green**; K4W411's P place, y 6.3, x 151.65 to 170.15 (not the drawn y 6.6) | (150.9, 6.3, B.Cu), 1.2 mm pad | (170.9, 6.3, B.Cu), 1.2 mm pad | 20 (15 to 17) | 22-S | CH5 | J2.6 | the drawn y 6.6 overlaps the boxes by 0.055 (finding 13); clips would shade the mushrooms: leads plus adhesive (finding 2) | *measured* (windows), *inferred* |

* **Total:** 180 mA at 20 mA a filament. It is 170 to 174 mA if the two green bars draw 15 to 17 mA (*assumed* Vf).
* **Channels needed alone:** 9. With K4W411's grouping: 5.
* **Channels if same-colour sources share:** 2 (warm, green).
* **Connector pins:** 6 of J2's 7; pin 7 spare.
* **Changes the other faces may not need:**
  * fascia R: S on the stack's place with the mushroom stood on it (findings 1, 12); green bars on S and P (finding 14); on the T
    layout only, R7's and R8's four holes moved (finding 15); the strokes clipped as vectors (finding 17);
  * DRV, DISP: nothing beyond K4W411 #1 and #3.

## 4. Left open

* Not measured:
  * the green bar's forward voltage (finding 14);
  * the push button's stand-off and orientation (K4W411 #5). It also decides whether P can have end clips (finding 2);
  * a bar's dark end length (K4W411 #8). It sets how low S must sit (finding 1).
* *Assumed*:
  * the S and P sources are 18.5 rigid bars (the face run's own assumption);
  * the height of a through-hole joint (finding 3);
  * R1's place against the sill's step over the rotary, read on the case model's stand-in board (finding 3).
* Not done: routing on any board; KiCad DRC; a check of the faces at 46 px per mm (findings 11 and 17); the bench and the coupon.
* The pad places in both Routing needs tables are proposals, good to about 1 mm. The routing-plan run fixes them.
