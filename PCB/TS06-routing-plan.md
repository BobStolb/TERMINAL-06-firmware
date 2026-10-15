# TS06 routing plan: one light base for every face, the channels, and the board changes

2026-10-15, run routing-plan. The owner (00:0x UTC): "run grills on all, compile insights for the final pcb routing plan". Earlier
(10-14, 23:0x UTC): "after we have a list of approved fascias we will look what needs to be done to accomodate all and then make
appropriate changes".

This page reads the seven grills together and turns them into one plan for the board-change run:
* approved: [K4W411](art/TS06-FASCIA-K4W411-grill.md);
* final candidates: [disp-3-4](art/TS06-DISP-final-3-grill.md), [organic-2-1 The print and 2-2 Mushroom](art/TS06-FASCIA-organic-2-grill.md),
  [science-2-3 Double slit](art/TS06-FASCIA-science-2-3-grill.md), [celestial-3 Sundials](art/TS06-FASCIA-celestial-3-grill.md),
  [BLUPRNT](art/TS06-FASCIA-BLUPRNT-grill.md).

It changes nothing. No board, schematic, fab, tool, 3D, firmware, spec or face file was touched. Nothing is routed. The scripts
are scratch, not in the repo. There is no picture: the owner asked for the doc only.

Marks:
* *measured*: read from a repo file, or computed on it by my own scripts (the faces' window outlines from the grill runs, rastered
  at 20 px per mm, all seven faces at once; the boards' footprints and tracks);
* *inferred*: arithmetic or reasoning on measured numbers;
* *assumed*: my reading, or a value nobody has measured.

Grill findings are cited as "K4W411 #5", "DISP #7", "organic #1", "science #3", "celestial #6", "BLUPRNT #2".

**Frames.** Fascia R: its own KiCad frame, front view, origin at the top-left corner, x right, y down, mm; the board is 191.4 x 40.
Back parts are given in front-view numbers. "t" is y down from the top edge. DISP: its own frame (origin top-left). DRV: its own
frame (DRV x = 191.4 - DISP x).

## 0. The answers in short

| Question | Choice | Why, in one line |
|---|---|---|
| How the lights are driven | **One P-FET per channel on the high side, for DISP and the fascia.** Every return goes to ground | DISP's lines share one cathode pour (DISP #2). On the fascia it halves the routing: the cathode pads sit in the ground pour |
| Where J2 goes | **In the pill, behind it: a 7-way header laid level, courtyard x 110.3 to 129.7, y 12.6 to 21.1** | Spot (a) is under BLUPRNT's P bar, spot (b) is under science's screen. This spot is clear of every window and every source of all six fascias (*measured*) |
| J2's pins | **7: GND_L, CH1 MODE, CH2 FIELD, CH3 SUB, CH4 keys, CH5 S family, CH6 P family** | With high-side drive no +5V_L pin is needed. S and P get a channel each, so celestial's day and night come free |
| S | **Three S places on the base: S1 (level in the pill, y 8.35), T (plumb, x 106.0 to 107.3), SCR (science's screen, y 35.8).** Organic's S moves onto T. BLUPRNT's S uses T's pads | Organic's level S crosses K4W411's stack bar. BLUPRNT's S at x 106.0 and the stack at 107.3 can share one pad pair |
| Science's screen | **Its own place (SCR) on the common base, raised to y 35.8** | Two pads and a resistor place cost nothing on other boards. Its anode goes straight up to J2: no hop |
| P's holding | **Leads plus a dab of clear silicone at each bar end, on every face.** No clips between the button boxes | Organic's lake and mushrooms, science's slits and celestial's moons fill the gap where K4W411 #6 put the clips |
| P's pads | **1.0 x 1.5 mm at (149.73, 6.3) and (172.07, 6.3), on every face** | 1.84 mm between the bar's end and the key arc's end; a 1.5 pad does not fit (science #5) |
| The flex in the top band | **Rule kept: no part or lead above t 4.5.** MODE's flex corner (t 4.36) is the one exception: 0.5 mm relief in the frame's top rail, if variant D is built | Today's sill stops at t 3.6, so it only matters for variant D |
| A6/A7 jogs and 0R hops | **None on rev C.** The control wiring moves to the bottom band; A7, A6 and +5V run as three lanes at y 38.15, 38.6 and 39.05 | Rev C re-routes the back anyway (K4W411 #4). Lights above, controls below: one layer is enough |
| Features under 0.15 mm | **Fixed in the art export, not on the board:** draw at 0.16, then an opening test with a 0.15 disc on the Gerbers | KiCad's DRC does not measure graphic polygons (BLUPRNT #8, #13) |
| Celestial's gold rails | **Gold with no net** | Rev B has no front power. A floating gold strip is safe and plates (K4W411 #11) |
| Raster faces | **One export path for all seven faces:** render each layer at 100 px per mm or finer, cut, drop pieces under 0.15, trace to polygons | Organic 2-1 has no vectors at all; the others cut on a raster |
| Channels | **(b): a second 16-channel chip.** 21 of 32 channels used | The owner expects colour changes; with (b) a change is a firmware table, with (a) a re-wire |
| The base board | **Rev B's surface-mount layout (K4W411 #15 (b)), as rev C** | It frees the pill for J2, keeps the fascia free of plated holes, and keeps power off the face |

## 1. Accommodation study: every need, and the faces that need it

Faces: **K** K4W411 (approved), **O1** organic-2-1, **O2** organic-2-2, **Sc** science-2-3, **C** celestial-3, **B** BLUPRNT, **D** disp-3-4.
Drop a face and its rows drop with it, unless another face is in the column. "All F" is every fascia; "all" adds D.

### 1a. Common to all

| # | Need | Faces | Board | Cost | Source |
|---|---|---|---|---|---|
| 1 | PWM chip(s), FETs, the master light switch, the J2 mate | all | DRV | section 3 | K4W411 #1, DISP #2, #3 |
| 2 | J2 on the fascia, its lead to DRV | all F | fascia R, DRV | one 7-way part each end, a lead | K4W411 #3 |
| 3 | The seven base windows and their sources (MODE 38 flex, four 18.5 lever bars, two 38 flex key arcs) | all F | fascia R | 7 pad pairs, 7 resistors | K4W411 #7 |
| 4 | No copper behind any window: landing pads and tracks off the windows | all F | fascia R | the back re-done (section 4.1) | K4W411 #4 |
| 5 | The key arcs against the button boxes: one bench measure | all F | bench | minutes | K4W411 #5 (blocker until measured) |
| 6 | The back pour cut per window (outline + 0.1), not one cut per group | all F | fascia R | none | K4W411 #12 |
| 7 | Bare-FR4 windows: the coupon and the order notes | all F | fab | one coupon | K4W411 #10 |
| 8 | The art as polygons from a fine raster or vectors, then the checks | all | fascia R, DISP | one export tool | K4W411 #16 |
| 9 | Nothing on the back above t 4.5 | all F | fascia R | none | K4W411 #8 |
| 10 | A resistor value per line set by look, not by one current | all | DRV, fascia R | a bench session | DISP #12, science #12 |
| 11 | The RTC module's I2C addresses (a bus scan) | all | bench | minutes | K4W411 #1 |
| 12 | Lights off from power-on until the firmware has set the chips up | all | DRV | one P-FET, one small FET, two resistors | new (section 3.3) |
| 13 | The case model carries the 191.4 fascia and J2's plug and lead | all F | case | a model update | new (section 4.4) |

### 1b. Needed by some faces only

| # | Need | Faces | Board | Cost | Source |
|---|---|---|---|---|---|
| 14 | S1: level 18.5 bar in the pill, y 8.35 | K, C | fascia R | a pad pair, a resistor | K4W411 #8, celestial #4 |
| 15 | T: plumb 18.5 bar, x 106.0 to 107.3 | K (stack), O1, O2 (their S, moved), B (S) | fascia R | a pad pair, a resistor | K4W411 #8, organic #1, BLUPRNT #3 |
| 16 | SCR: science's screen bar, y 35.8 | Sc | fascia R | a pad pair, a resistor | science #2, #10 |
| 17 | P: level 18.5 bar, y 6.3 | K, O1, O2, Sc, C | fascia R | a pad pair (1.0 wide), a resistor | K4W411 #6, science #5 |
| 18 | BP: plumb 18.5 bar at x 131.36 | B | fascia R | a pad pair, a resistor | BLUPRNT #2 |
| 19 | P held without clips between the boxes | K, O1, O2, Sc, C | assembly | silicone, a hand step | organic #2, celestial #2 |
| 20 | S and P on separate channels (day and night) | C (option) | DRV | free with J2's 7 pins | celestial #1 |
| 21 | S moved onto T (fork upright; mushroom stood on the bar) | O1, O2 | face | a face re-run | organic #1, #12 |
| 22 | The screen raised to y 35.8; slits 0.8 x 4.0 at y 4.6 to 8.6 | Sc | face | an art re-run | science #5, #10 |
| 23 | Control lanes under the screen, y 38.15 to 39.05 | Sc (forced); all F (one layout) | fascia R | none: the back is re-done anyway | science #3 |
| 24 | A no-net copper shape behind the lake's island | O1 | fascia R | one shape | organic #7 |
| 25 | The opened GND rail stopped short of the corners (screw heads) | O1 | face | none | organic #8 |
| 26 | Rails as no-net gold | C (also O2's white rail lines, silk) | face | none | celestial #6, organic #16 |
| 27 | Features under 0.15 mm | B (mesh 0.141, title 0.148, digit ink traps 0.11), Sc (white 0.13, seam slivers), C (seam slivers), O2 (joins at 0.15) | face export | art re-runs, one filter | BLUPRNT #8, #10; science #8, #9; celestial #7; organic #16 |
| 28 | Raster to vectors | O1 (trace the print), O2 and B (clip in vector form), Sc and C (sliver filter); K and D (emit their vectors) | export | one tool | organic #11, #17; BLUPRNT #13 |
| 29 | Green, white, pink, blue through bare FR4; yellow flex beside warm bar | O2 (green), C (white), K (pink, blue, white), Sc (two warms) | coupon | coupon rows | organic #14, celestial #10, K4W411 #13, science #12 |
| 30 | A 0.55 mm "3" on the coupon; which cathode is at the front | B | coupon, bench | minutes | BLUPRNT #6, #12 |
| 31 | Rev B base: the bunny's ears, the dial's beads, the leaning gills, the pill meter's ticks drawn as art | K, O2, B (and every face drawn on the T model) | face | art changes | K4W411 #15, organic #15, BLUPRNT #13 |
| 32 | 0.5 mm relief in variant D's top rail over MODE's top end | all F, only if variant D is built | case | none | BLUPRNT #4, organic 21-MODE |
| 33 | P-FET drive (a shared cathode pour) | D | DRV | none in parts | DISP #2 |
| 34 | 14 DISP channels with HL9; a second chip, or colour groups | D | DRV | section 3 | DISP #3 |
| 35 | The lintel's ends swapped; BL_A10 along the top band | D | DISP | ~40 mm of track | DISP #7 (blocker as drawn) |
| 36 | The colon floor's net named BL_A12 (not K3) | D | DISP, DRV, firmware | none | DISP #8 |
| 37 | Q1 and Q2 on two wires; a 6-wire harness | D | DISP, DRV | one wire | DISP #4 |
| 38 | XP12.12 and XP12.13 as BL_A10 and BL_A11; their DRV routes | D | DISP, DRV | ~32 mm each on DRV | DISP #5 |
| 39 | BL_A9 moved to y 43.2; BL_A6 nudged 0.1 | D | DISP | none | DISP #6 |
| 40 | HL9 on a PWM channel (VT20 goes) | D | DRV | one channel | DISP #3 |
| 41 | A placing jig and silicone dots for the face lines | D | assembly | one jig | DISP #9 |
| 42 | The sill 0.8 lower, not 1.1; the strip joints blackened | D | case | one number | DISP #10 |

**What is common:** rows 1 to 13 hold for every fascia whatever the owner picks; rows 3, 4, 6 and 17 cover the seven base lights
and the P place, which five of the six fascias use. **What only some need:** the S places (each used by one to four faces), BP
(BLUPRNT only), SCR and the lanes (science only), and every DISP row (one display). No row forces a change on another face.

## 2. One light base for every fascia

The owner's rule: the sources and pads stay; the windows differ per fascia. So every fascia board carries the same back copper:
the same pads, resistor places, J2 and tracks. What differs per face is the front (art, windows) and the back pour's cuts under
that face's windows. A face fits only the sources it uses; empty pads cost nothing.

I checked this on all six fascias at once (*measured*): the faces' window outlines (from the grill runs), rastered together, with
each face's sources and the fixed parts (both box orientations of the two push buttons, the lever and dial bodies, J1's
courtyard, the four screw bosses at r 3.5, the top band).

### 2.1 The drive: high-side P-FETs, returns to ground

* **DISP needs it** (DISP #2): all its lines return on one BL_K pour, so only the anode side can be switched per line.
* **The fascia gains from it** (*inferred*). With a switched anode (channel) and the cathode on ground:
  * each source needs **one** routed net, its anode. Its cathode pad sits in the back's GND pour;
  * K4W411 #3's way (common +5V_L, switched cathodes) needs two routed nets per source on a single back layer.
* So J2 carries the six channels plus one ground return (GND_L). The light current returns through J2's GND_L and, in part,
  through J1's GND wire: about 3 mV of shift at 0.2 A on two leads (*inferred*, 26 AWG, 0.2 m). That is nothing next to the
  ladder's steps. **Bench check:** read A6 and A7 with all lights off, then all full on. They must not change.
* One FET type on DRV for both boards: a logic-level P-FET, SOT-23, -20 V, 0.5 A or more, about 0.5 ohm or less at -4.5 V
  (*assumed* part class; no part chosen).

### 2.2 Two zones on the back of fascia R

* **The light zone:** from the top band (y 0.6 to 3.7, tracks only) down to about y 27.5. It holds every light pad and resistor,
  J2, and the light tracks.
* **The control zone:** below about y 28, and J1. It holds the control landing pads, R1 to R8 and their tracks.
* The two zones never cross. That is why one copper layer is enough and no 0R hop is needed (*inferred*; section 4.1 gives the
  lanes and the order of the pins that keep it so).

### 2.3 The twelve source places and their pads

Every pad is on B.Cu. The anode pad is routed (through its own 120R place, the value set by the bench); the cathode pad sits in
the GND pour. **Measured:** every pad keeps 0.35 mm or more from every window of all six fascias (organic's S moved, row T), off
the top band and off J1's courtyard. The base pads come from the science and celestial grills' searches (their Routing needs
tables), nudged by 0.05 to 0.10 where my all-face check found 0.25 to 0.29; the key - arc's anode moved 2.2 mm left to clear J1.

| Place | Source (sold part) | Anode pad (routed) | Cathode pad (pour) | Pad size | Channel | Faces that fit it |
|---|---|---|---|---|---|---|
| M | MODE arc, 38 flex (r 14.2 about the dial, 130 to 230 deg) | (12.29, 5.26) | (15.76, 29.01) | 1.5 x 1.5 | CH1 | all F |
| FU | FIELD up, 18.5 bar on the chord, y 5.9, x 54.74 to 73.24 | (52.74, 5.91) | (74.0, 8.0) | 1.5 x 1.5 | CH2 | all F |
| FD | FIELD down, the same at y 26.1 | (52.74, 26.11) | (74.0, 28.2) | 1.5 x 1.5 | CH2 | all F |
| SU | SUB up, y 5.9, x 78.12 to 96.62 | (98.66, 5.91) | (77.4, 8.0) | 1.5 x 1.5 | CH3 | all F |
| SD | SUB down, y 26.1 | (98.64, 25.06) | (77.4, 28.2) | 1.5 x 1.5 | CH3 | all F |
| KM | key - arc, 38 flex (r 10 about (150.4, 16), 105 to 255 deg) | (145.61, 27.69), bottom end | (144.39, 5.26), top end | 1.5 x 1.5 | CH4 | all F |
| KP | key + arc, 38 flex (-75 to 75 deg about (171.4, 16)) | (173.99, 27.79), bottom end | (177.39, 5.26), top end | 1.5 x 1.5 | CH4 | all F |
| S1 | level 18.5 bar, y 8.35, x 109.64 to 128.13 | (110.15, 11.6), left lead bent down | (129.0, 10.5), right lead bent down | 1.2; 1.5 | CH5 | K (heart), C (sun) |
| T | plumb 18.5 bar, x 106.0 (BLUPRNT) to 107.3 (K4W411, organic), y about 5.8 to 24.8 | (109.3, 24.5), bottom lead bent right | (109.3, 6.0), top lead bent right | 1.2 x 1.2 | CH5 | K (stack), O1, O2, B (their S) |
| SCR | level 18.5 bar, y 35.8, x 109.6 to 128.1 | (107.59, 34.96) | (130.14, 34.96) | 1.5 x 1.5 | CH5 | Sc (screen) |
| P | level 18.5 bar, y 6.3, x 151.65 to 170.15 | (149.73, 6.3) | (172.07, 6.3) | 1.0 x 1.5 | CH6 | K, O1, O2, Sc, C |
| BP | plumb 18.5 bar, x 131.36, y 5.9 to 24.4 | (129.4, 23.8) | (129.4, 6.5) | 1.5 x 1.2 | CH6 | B (P) |

* **One resistor place per source** (1206, on the back), in the light zone, on the source's anode route. They must keep 0.3 from
  every window, stay out of the top band, and stay out of every control body's outline (both orientations of the push buttons'
  boxes, the levers' 11.92 square, the dial's r 12.5): those bodies sit flush on the back. Tracks may pass under the bodies, as on
  rev B. Twelve places; a face fits 9 (10 on K4W411).
* **Places never fitted together** (S1 and SCR; P and BP) could share one resistor place. I keep them apart: one place per
  source is simpler to check, and an empty 1206 costs nothing.
* **A plumb bar at either x on one pad pair:** T's pads sit 2.0 to 3.3 mm right of the bar's axis. On K4W411 and organic the
  leads bend 2.0 mm; on BLUPRNT (bar at x 106.0) they bend 3.3 mm. Only the clips and the pour cut set the bar's x, and both are
  per face.
* **Lead pads off the bars' end caps:** no pad of another net may lie under a fitted bar's metal cap (DISP #7's lesson). Checked
  for every face's fitted set (*inferred* from the bar ends). The nearest is on K4W411: S1's left cap (its anode, from x 109.64,
  y 7.35) against T's top pad (a cathode, to y 6.6), 0.75 apart.

### 2.4 J2: place, part, pin map

**Place (*measured*: a search of every 19.4 x 8.5 mm spot, both ways round, against all six fascias' windows and sources + 0.3,
the fixed parts, the top band and the edges):**

| Spot | Result |
|---|---|
| (a) K4W411 #3: upright, x 130.5 to 139.0, y 5.5 to 24.9 | **No.** BLUPRNT's P bar (x 130.36 to 132.36) lies on it (BLUPRNT #2) |
| (b) K4W411 #3: level, x 100 to 120, y 27 to 35.5 | **No.** Science's screen lobes (x 111.59 to 126.19, from y 31.21) lie on it (science #4) |
| (c) right of J1, level | **No.** 19.4 mm do not fit between J1 (x 164.1) and H4's boss (x 183.4) |
| **(d) in the pill, level: x 110.3 to 129.7, y 12.6 to 21.1** | **Yes, for all six.** 0.52 to BLUPRNT's P "3", 1.35 to S1's cathode pad, 0.4 to S1's anode pad, 2.0 to the T bar's body, 10 to the screen's top. No source body and no fixed part inside |
| (e) between the dial and FIELD, level: x 38.0 to 57.4, y 7.5 to 16.0 | Yes. The fallback if the owner takes the T layout (K4W411 #15 (a)), whose resistors stand in the pill |
| (f) left edge, upright: x 0.5 to 9.25, about y 8.3 to 27.7 | Yes, but every light route runs the board's length, and the case's cheek is beside it |

* **Part:** J1's family, 2.0 mm pitch, top-entry SMD, **7 ways** (K4W411 #3's reason stands: J1's 6-way lead cannot go into it).
  Courtyard 19.4 x 8.5 (*inferred* from J1's 17.4 x 8.5).
* **Case (*inferred*):** the plug stands 9.5 off the back at y 12.6 to 21.1. That is 5 mm lower on the face than the push buttons'
  boxes (tops at y 7.5), which the case model puts 0.84 below DISP's bottom edge; so the plug stays about 6 mm below it. The lead
  drops behind the fascia in the clear column between the SUB lever's body (x 93.3) and the - key's box (x 141.9). **To check on
  the case model** (row 13).
* **Pin map.** Pins numbered as J1: pin 1 is the rightmost in front view (J1 on rev B: pin 1 at x 160.4, pin 6 at x 150.4). The order
  is chosen so that no two light routes cross on the one back layer (section 4.1).

| J2 pin | x (front view) | Net | Sources | Worst current |
|---|---|---|---|---|
| 1 | 126 | CH6, the P family | P or BP | 20 mA |
| 2 | 124 | CH4, the keys | KM + KP | 40 mA |
| 3 | 122 | GND_L, the light return | every cathode, through the pour | 200 mA |
| 4 | 120 | CH1, MODE | M | 20 mA |
| 5 | 118 | CH2, FIELD | FU + FD | 40 mA |
| 6 | 116 | CH3, SUB | SU + SD | 40 mA |
| 7 | 114 | CH5, the S family | S1, T, SCR (K4W411: S1 + T) | 40 mA |

Worst currents at 20 mA a source, before the bench's resistor table. Per face, the firmware maps each function to its channel:

| Face | CH5 | CH6 | Pins used |
|---|---|---|---|
| K4W411 | heart (S1) + stack (T), one duty | eyes (P) | 7 |
| organic-2-1, 2-2 | S on T | P | 7 |
| science-2-3 | screen (SCR) | slits (P) | 7 |
| celestial-3 | sun (S1) | moons (P): day and night apart, or one duty | 7 |
| BLUPRNT | S "3" on T | P "3" on BP | 7 |

K4W411 #3's map had S, P and the stack on one channel and pin 7 spare. Here K4W411's eyes get their own channel; the firmware
can still run all three together.

### 2.5 What each face must change to fit the base

| Face | Change to fit | Cost |
|---|---|---|
| K4W411 | Nothing on the face. The stack bar centred, y 6.26 to 24.76 (K4W411 #8). P held by leads and silicone, not clips | none |
| organic-2-1 | S: the fork turned upright on T, about x 106.0 to 108.6, y 7.6 to 12.7 (organic #1 (a)). As drawn, its fork sits on T's top pad: 0.00 mm (*measured*) | a face re-run |
| organic-2-2 | S: the mushroom stood on T, cap up, about y 7.6 to 11.2. P at y 6.3, not 6.6 (organic #13) | a face re-run |
| science-2-3 | The screen bar at y 35.8 (science #10). The slits 0.8 x 4.0 at y 4.6 to 8.6 (science #5). Nothing else: J2 and the lanes avoid the screen | an art re-run |
| celestial-3 | Nothing for the lights. The moons' bar by leads and silicone | none |
| BLUPRNT | S's bar at x 106.0 (BLUPRNT #3) on T's pads; P on BP | none |

**If a face cannot change:** organic kept as drawn needs its own level S bar at y 6.0 (organic's 21-S-alt and 22-S-alt rows). Its
window sits on T's top pad, so T's pads would have to move on organic's boards only: a second back layout, a second set of checks
and a second stencil. That is the only case where one base does not serve all.

### 2.6 The disputes, one by one

1. **J2 (spot (a) under BLUPRNT's P tail, spot (b) under science's screen).** Spot (d), in the pill (section 2.4). It needs no
   jumper and no lane change, and it is central: S, P and the keys are within 60 mm of it; MODE, the farthest, about 125 mm. Cost:
   on the T layout the pill holds R6 to R8, so (d) needs the rev B base (section 2.7); otherwise spot (e).
2. **S (organic's S crosses K4W411's stack bar; BLUPRNT wants S at x 106.0).** Organic moves its S onto T (organic #1 (a), a face
   re-run). BLUPRNT keeps x 106.0 and uses T's pads, which serve any plumb bar from x 106.0 to 107.3. One plumb place, not two.
3. **Science's screen, a new light place.** It is SCR on the base, at the raised y 35.8. Its anode pad (107.59, 34.96) routes up
   at x 110.6 to J2's pin 7 from below: 1.59 mm or more from every window (*measured* on the corridor). The control lanes pass
   under it at y 38.15 to 39.05: 0.45 mm (centre line) from the lobes' feet, against 0.425 needed (*measured*). No hop over A7 is
   needed, because A7 no longer runs above the screen.
4. **How P is held.** Leads plus a dab of clear neutral-cure silicone at each bar end, x 151.65 to 153.4 and 168.4 to 170.15, on
   every face. Those ends are clear of every face's P windows (the nearest, celestial's moons, start at x 153.7). The dabs lie at
   y 5.3 to 7.3, above the boxes' top (7.545 in the 13.75-across case). End clips may come back on faces whose windows leave room,
   once K4W411 #5's measure shows a gap behind the boxes. This also holds DISP's way (DISP #9: silicone in a jig).
5. **P pads 1.0 mm wide.** Adopted for every face with the P place (science #5, celestial #3): 0.43 and 0.38 mm to the nearest
   window of all six faces (*measured*).
6. **The flex in the top band.** Rule kept: no part, lead, joint or clip above t 4.5 (K4W411 #8). Two things reach in:
   * MODE's flex corner at t 4.36 (BLUPRNT #4, organic): clear of today's sill (t 3.6). If variant D is built, cut 0.5 mm of relief
     in its top rail over x 9 to 18;
   * the lever-up arcs as flex (t 4.40): use the 18.5 bars on the chord (body top t 4.9), the base default.
   The light bus runs in the band as flat tracks under the mask, which K4W411 #8 allows.
7. **A6/A7 jogs and 0R hops on rev B.** None on rev C. Rev C re-does the back anyway (K4W411 #4: +5V, LEVA, LEVB, A7 and D8
   all cross windows on rev B). The control nets stay in the bottom band, so no light net has to cross them. Science's A6 jog
   becomes the general rule: the three lanes at y 38.15 / 38.6 / 39.05. BLUPRNT's 2 to 6 jumpers and science's two are not needed.
8. **Features under 0.15 mm.** All fixed in the art export (section 4.1, step 6), not on the board:
   * BLUPRNT: the mesh drawn at 0.16 (BLUPRNT #8); the title in the 1.5 mm mono font or a 10.2 mm block; the digits 3, 6, 9 in
     KiCad's stroke font at 1.2, unless the fab says yes to the ink traps (BLUPRNT #10);
   * science: the plane wave at 0.50 pitch (science #8); the seam slivers dropped (science #9);
   * celestial: the seam slivers dropped (celestial #7);
   * organic-2-2: the joins emitted at 0.16 (organic #16).
   One check covers all: an opening with a 0.15 disc on the rasterised F.Silk and F.Cu Gerbers (BLUPRNT #13, step 4).
9. **Celestial's gold rails.** Gold with no net (celestial #6's pick). On the rev B base there is no front power, so they are new
   front copper either way. They keep 4.8 mm from the screw holes (*inferred* from the rails' ends at x 9.0 and 182.4).
10. **Raster faces.** One export path for all, so every face meets the same checks:
    * render each layer from the face's own script at 100 px per mm or finer (organic-2-1's ridge field at 46 px per mm or more,
      organic #11);
    * make the cuts (keep-outs, clips) on that raster, or in vector form where the face has vectors (organic-2-2, BLUPRNT);
    * drop every piece under 0.15 (an opening);
    * trace the outlines, smooth, emit polygons (F.Silkscreen; F.Cu with no net plus the same F.Mask opening; the windows as mask
      openings on both faces and copper keep-outs on both layers);
    * re-run the checks on the Gerbers (section 4.5).

### 2.7 The base board: rev B's layout

K4W411 #15 leaves the owner a choice: build the T layout (16 plated holes, the parts stand on the face) or keep rev B's
surface-mount parts and draw them as art. For the routing, **(b), rev B's layout, is the better base** (*inferred*):
* the pill is free for J2 (on the T layout R6 to R8 stand there);
* no plated hole, as spec section 6 says for R; one back layer is enough (section 2.2);
* no top-band joints (organic #3) and no 5 V rail on the face (celestial #6).
The cost is art: K4W411's bunny ears and the dial's beads, organic-2-2's leaning gills and BLUPRNT's pill-meter gaps are drawn as
silk and gold, not real parts. If the owner wants (a), J2 goes to spot (e) and section 4.1's topology must be re-checked.

## 3. Channels

### 3.1 The PWM chips on DRV

* **Part type:** a 16-channel, 12-bit I2C LED PWM controller, TSSOP-28, run from +5V. Its address is set by six straps (0x40 to
  0x7F). It is surface-mount, so it breaks DRV's through-hole rule, as front-merge item 8 already said.
* **Addresses:** chip 1 at **0x40** (all straps low), chip 2 at **0x41** (A0 high). The bus today holds U3, the port expander at 0x20,
  and U13, the RTC module (*measured*: sheet 04). The module's own addresses are not in the repo; such modules usually answer at 0x68
  and 0x57 (*assumed*). **Bench check:** an I2C scan of the fitted module (K4W411 #1). The chips also answer a shared "all call"
  address at reset (*assumed*: 0x70); the firmware turns it off.
* **Bus:** A4 and A5, with the 4k7 pull-ups R54 and R55 that are there (*measured*: sheet 04, BOM). Each chip gets a 100 nF.
  Output enable to ground. No new MCU pin.
* **Place: DRV x 86.5 to 128.5, y 24.5 to 45.0** (*measured*: no part's courtyard inside it; tracks of 11 nets cross it and are
  re-routed). That is 42 x 20.5 mm, about 860 mm². It holds the two chips, 20 channel P-FETs, the master switch and the 14 DISP
  line resistors: about 570 mm² with dual P-FETs (SOT-23-6), 690 mm² with singles (*inferred*). Tight with singles; take the duals.
* **Why there:** it sits between DRV's top strip and its bottom strips. XS12.12 and XS12.13 (DRV (56.11, 28.2) and (53.57, 28.2))
  are about 33 mm away along y 31, under XS12 and above U15 and U17 (a 2.5 mm corridor, its tracks not checked). DISP #5 counted
  45 to 50 mm to a block near the bottom strips. The bottom strips are 22 to 90 mm away (XS25, at the far left, is the farthest).
  RN1's fan-out to every strip goes; this block's fan-out replaces it.

### 3.2 The channel map, DISP and fascia, with option (b)

Chip 1, 0x40: DISP. Each line keeps its own resistor on DRV (DISP #3; K4W411 #2). Values by look (DISP #12) once the bench is done.

| Ch | Line | Net on DISP | Strip pin (DISP XP) | Resistor | mA at 20 a filament (by look) |
|---|---|---|---|---|---|
| 0 | H, hours bracket | BL_A1 | XP21.2 | 120R | 20 (34) |
| 1 | M, minutes bracket | BL_A3 | XP23.1 | 120R | 20 (34) |
| 2 | P, AM/PM box | BL_A7 | XP25.1 | 120R | 20 (34) |
| 3 | F, the long line | BL_A8 | XP25.6 | 120R | 20 (70) |
| 4 | S, squared arch | BL_A6 | XP24.4 | 120R | 20 |
| 5 | Q1 + Q2, colon bars | harness | two wires | 2 x 120R | 40 (2 x 9) |
| 6 | F2L, pink | BL_A2 | XP21.5 | 120R | 20 |
| 7 | F2R, blue | BL_A9 | XP25.3 | 120R | 20 |
| 8 | F3L, green | BL_A4 | XP23.4 | 120R | 20 |
| 9 | F3R, green | BL_A11 | XP12.13 | 120R | 20 |
| 10 | CF, colon floor, pink | BL_A12 | harness | 120R | 20 (6) |
| 11 | S2, inner arch, blue | BL_A5 | XP24.1 | 120R | 20 |
| 12 | S3, lintel, green | BL_A10 | XP12.12 | 120R | 20 (14) |
| 13 | HL9, the "m" | M_A | XP25.4 | R53 220R, kept | about 14 |
| 14 | spare | | | | |
| 15 | the master light switch (section 3.3) | | | | |

Chip 2, 0x41: the fascia, through J2. The resistors are on the fascia.

| Ch | Fascia channel | J2 pin | Sources |
|---|---|---|---|
| 0 | CH1 MODE | 4 | M |
| 1 | CH2 FIELD | 5 | FU, FD |
| 2 | CH3 SUB | 6 | SU, SD |
| 3 | CH4 keys | 2 | KM, KP |
| 4 | CH5 S family | 7 | S1, T, SCR |
| 5 | CH6 P family | 1 | P, BP |
| 6 to 15 | spare (10) | | |

* **In use:** 21 of 32 (20 lines and the master). BL_K (XP21.1) is plain ground on DRV.
* **What changes on DRV:** RN1 (the 8 x 220R network), VT20 (the HV NPN in BL_K) and its base resistor R20 go (*measured*: sheet 10).
  U3's port B is freed. D11 drives the RGB chain. D12 is freed (HL9 moves to channel 13).
* **Spares:** they take a later split with no DRV re-wire: Q1 and Q2 apart, or a line that leaves its colour group (DISP #14). A
  split on the fascia needs a J2 pin: J2 has none spare, by choice.

### 3.3 Lights off at power-on: the master switch

* The part type's outputs come up low until the firmware writes it: every channel "off", outputs not inverted (*assumed* from the
  part type's register defaults; **check the datasheet** before the schematic). Low on a P-FET's gate means on.
* So without care, every light flashes on at full from power-on until the set-up: all 20 lines, about 0.5 A (*inferred*).
* Holding output enable high does not help: with its default setting it also drives the outputs low (*assumed*, the same check).
* **Fix:** one master P-FET (logic level, 1 A or more, about 0.1 ohm) between +5V and V_LIGHT, the supply of all 20 channel
  P-FETs. Its gate has a 10k pull-up (off). A small N-FET pulls the gate low when chip 1's channel 15 drives high. At power-on
  channel 15 is low, so no light can turn on. The firmware sets both chips up, writes every light off, then turns channel 15 on.
* Cost: two transistors, two resistors. The fascia's GND_L stays plain ground (not switched), so the cathodes stay in the pour.
* With option (a) there is no channel left for it: it takes D12 instead.

### 3.4 Current and the 5 V margin

The 5 V module U14 gives 1.0 A. The DISP grill's figures, with K4W411's ten fascia filaments (*inferred* there):

| Everything at full, the RGB LEDs full white | 20 mA a filament | DISP lines by look (DISP #12) |
|---|---|---|
| The clock | 872 mA, 87 % | 922 mA, 92 % |
| + the two PWM chips (*assumed* 10 to 20 mA) | 890 mA, 89 % | 940 mA, 94 % |
| + the LED cap (R + G + B <= 255) | 700 mA, 70 % | 750 mA, 75 % |

* The other fascias have nine filaments: 20 mA less.
* **Matching the fascia by look lowers it** (*inferred*, DISP #12's mA per lit mm): an 18.5 bar lights about 15.5 mm, a 38 flex
  about 28. At one look the bars take about 11 mA, not 20. On K4W411 that saves about 60 mA.
* **The LED cap is a must:** 25 % margin with it, 6 % without. It is firmware only.
* Per FET: the largest is F at 70 mA by look. The master carries up to about 0.6 A (*inferred*: 0.04 W at 0.1 ohm).
* Per pin: XP21.1 (BL_K) carries the DISP returns, about 330 mA by look. J2's GND_L carries up to 200 mA. Both are well inside
  the pins' ratings (*assumed* 1 A or more).

### 3.5 (a) colour groups or (b) a second chip

| | (a) one chip, one FET per colour group | **(b) two chips, one channel per line (my pick)** |
|---|---|---|
| Channels | DISP 9 + HL9 + fascia 6 = 16 of 16 | 21 of 32 |
| Master switch | on D12 | on chip 1's channel 15 |
| A glyph changes colour later | re-wire the line to another group's FET on DRV, or a solder jumper per colour line (7) | a firmware table; a resistor if the forward voltage differs |
| Parts against (a) | | + one chip, one 100 nF, one strap; about 5 more FETs |
| Board | | about 1.5 cm² more |

**Recommendation: (b).** The owner expects some glyphs to change colour (DISP #14). Under (b) that costs no DRV change. It also
keeps every line under its own control and leaves spares. Take (a) only if the colours are fixed now and DRV must change least.
Option (c), the fascia on 3 channels, I do not propose: the control arcs would no longer light one at a time.

## 4. The routing plan, per board

### 4.1 Fascia R rev C (one back for every face)

Start from rev B's file (`PCB/TS06-FASCIA-rhythm`). Keep: the 191.4 x 40 outline, 2.0 mm FR4, the four M2.5 holes, the five control
holes, J1 at (155.4, 33.0) with its pin map, R1 to R8 and their values, the GND pour on B.Cu. No plated hole.

**The control zone (below about y 28):**
1. **Landing pads off the windows** (K4W411 #4):
   * SW2's and SW3's (LEVA, A7; LEVB, A7) below their down arcs, at y 28.7 to 35;
   * SW4's and SW5's (D7, D8, GND) left of J1, at x 138 to 146, y 30 to 36. Their hand wires cross behind the board: harmless;
   * SW1's taps stay at y 31 (2.4 mm below MODE's window, *inferred*). Only A6's pad (SW1.7) moves (item 3).
2. **R6** (the A7 ladder's top resistor) moves from (75.68, 22.5), which is in the light zone, to the bottom band at about x 50 to 55.
3. **Three lanes** from J1 leftward. They run tight (0.45 mm pitch) only under science's screen, and spread elsewhere:
   * A7 at y 38.15 under the screen, ending at R6;
   * A6 at y 38.6 under the screen, ending at its landing pad, which sits between the A7 and +5V lanes (about x 57);
   * +5V at y 39.05, on to R5 and SW1.6.
   They rise into J1's pins 4, 3 and 1 from below, left pin first, so none crosses another. R6 sits where the A6 lane has ended,
   so it joins A7 to +5V without a crossing. Under the screen they keep 0.45 mm (centre line) from the lobes' feet (*measured*;
   0.425 needed) and 0.83 from the board edge.
4. **D7 and D8** enter J1's pins 5 and 6 from below, from their pads on the left, above the lanes.
5. LEVA, LEVB, TAP2 to TAP5: short and local, as rev B.

**The light zone (*measured*: each corridor's centre line against all six faces' windows; 0.425 needed):**
6. The 24 pads of section 2.3, the 12 resistor places, J2 at x 110.3 to 129.7, y 12.6 to 21.1.
7. **The top band bus**, flat tracks under the mask, at most three lanes at y 1.2, 2.1 and 3.0 (0.55 mm or more from any window):
   CH1, CH2 and CH3 from the left; CH6 from the right.
8. **Trunks:** CH2 down x 52.2 to FU's and FD's anodes; CH3 down x 99.4 to SU's and SD's. No window within 3 mm of either.
9. **Drops into J2 from above:** CH1, CH2 and CH3 down x 115.9, 115.45 and 115.0 to pins 4, 5 and 6, nested so they do not cross
   (0.50 mm to the sun and the heart); CH6 down x 127.0 to pin 1 (1.08 mm); S1's anode along y 11.3 to pin 7 (1.15 mm).
10. **From below:** T's anode (1.66 mm) and SCR's anode, up x 110.6 (1.59 mm), to pin 7; BP's anode to pin 1.
11. **CH4:** from pin 2 down to y 27.6, then along it to KM's anode (145.61, 27.69) and KP's (173.99, 27.79). It runs 0.5 mm above
    J1's courtyard and 0.95 mm below the key arcs' ends.
12. MODE's anode goes straight up into the band (1.79 mm).
13. Each resistor sits on its own source's branch, after the split.

**Keep-outs:** no part, pad or resistor inside a control body's outline (the boxes both ways round: x 141.95 to 158.85 and 162.95
to 179.85 at y 9.1 to 22.9, or x 143.5 to 157.3 and 164.5 to 178.3 at y 7.55 to 24.45; the levers' 11.92 squares; the dial's r 12.5).
Tracks may pass under them, under the mask, as rev B's D8 does. Nothing above t 4.5 but flat tracks.

**Per face, on a copy of the common back:**
14. The pour cut under each window, outline + 0.1 (K4W411 #12). Organic-2-1 keeps a no-net B.Cu shape behind the lake's island
    (organic #7).
15. Every cathode pad must stay in a pour region joined to J1's GND and J2's GND_L. The lanes and the bus leave necks; KiCad's
    zone fill and its unconnected-items report show any island.
16. The front: the art from the export (section 2.6, item 10), the windows as mask openings on both faces and copper keep-outs on
    both layers.
17. Back silk: each source's outline and polarity (+ at the anode pad), its clip or silicone places, the resistor names, "LIGHTS"
    at J2.

### 4.2 DISP rev C

From rev B's file. The DISP grill's list (DISP #15), with this plan's choices:
1. The 20 plated slots, F2's shared pad and the four round holes (D1, D5, E1, E2, G1). The tracks D2 to D4, D6, E1, E2, G2 to G4.
2. BL_A9 moved to y 43.2 (0.90 to XP25.2, 0.65 to the edge). BL_A6 nudged 0.1 where DRC shows it (DISP #6).
3. **The lintel's ends swapped** (DISP #7, the blocker): drive the left hole (101.385, 6.60). BL_A10 runs from XP12.12 up to the band
   above XP12's pads (y 0.9), left, then down: about 40 mm on B.Cu. Route it first and DRC it: it is *inferred*, not routed. Trim
   the gold within 0.3 of the left cap. The right hole goes on BL_K, the net of P's return pad and the gold under its cap.
4. The colon floor's net is **BL_A12**, not K3 (DISP #8).
5. HL9 3.0 down (V3b). HL1 to HL8 removed.
6. XP12.12 = BL_A10, XP12.13 = BL_A11, XP25.3 = BL_A9. The BL_K pour stays: it becomes plain ground on DRV.
7. The art from the export, yielding round the slots, the holes and the rigid bars' end caps (DISP #11).

**The 185 V rules** (`TS06-DISP.kicad_pro` and `.kicad_dru`): HV class (ANODE_*, COLON_*) 0.6 mm to tracks and 0.8 to HV pads; CATH
class 0.25. Filament bodies 2.0 wide, 0.4 to pin pads, 0.4 line to line. Three margins sit at 0.00 to 0.02 on the face run's 0.1 grid
(DISP #6): only KiCad's DRC on the real tracks settles them.

### 4.3 DRV rev C

From rev B's file and schematic:
1. **Out:** RN1, VT20, R20 (sheet 10).
2. **In, at x 86.5 to 128.5, y 24.5 to 45.0:** the two chips (0x40, 0x41) and their 100 nF; 20 channel P-FETs (dual packages);
   the master P-FET, its N-FET and two resistors; 14 DISP line resistors (standing 0207 parts in a row, or a socket strip where a
   colour may change, DISP #14). R53 stays as HL9's resistor.
3. **Nets:** BL_K to GND. The FET drains through the resistors to the strip pins of section 3.2, including XS25.3, XS12.12 and
   XS12.13 (spare on rev B). M_A to channel 13. D11 to the RGB chain's DATA.
4. **J2's mate:** 7-way, J1's family, through-hole vertical, at x 116.5 to 134.5, y 91.7 to 97.2, beside DRV J1 (*measured*: free).
   Pin 1 to pin 1 with the fascia's J2. About 50 mm of route from the block for six channels and GND_L.
5. **The DISP harness:** 6 wires (LED 5 V; GND, which is also the colon's return; DATA; Q1; Q2; CF). Use plated pads, 2.54 pitch,
   at the block's top edge (x 110 to 128, y 25 to 30, *measured* free), with the wires soldered in. A header and plug would stand
   about 11 mm in the 11.0 mm gap to DISP (*assumed*).
6. **Routes:** XS12.12 and XS12.13 along y 31, about 33 mm. The bottom strips: 22 to 90 mm. Re-route the 11 nets that cross the
   block today.
7. **The schematic:** sheet 10 (backlight) becomes the light drive; sheet 11 (fascia) gains J2's mate; sheet 04 lists the two chips
   on the bus.

### 4.4 The leads and the case

* **Fascia to DRV:** a second lead of 7 wires, the J1 lead's class (180 to 200 mm, from the case checks for J1), pin 1 to pin 1.
  It runs beside J1's lead.
* **DRV to DISP:** the 6-wire harness of 4.3, item 5.
* **The case model** (`3d/case-pair`):
  * it still carries the 176 mm stand-in fascia (`FASCIA_W` 176, *measured*); it must take the 191.4 fascia R;
  * add J2's plug (9.5 off the back) and its lead's path to DRV;
  * the sill 0.8 lower (DISP #10), with the strip joints blackened;
  * only if variant D is built: re-place its panel holes and ribs for the 191.4 fascia's light places and J2 (they were placed for
    the stand-in's parts), and cut 0.5 mm relief in its top rail over MODE's top end.

### 4.5 The checks after the changes

| Board | Checks |
|---|---|
| Fascia R rev C, each face | KiCad DRC with the fab rules, zone fill, unconnected items 0; a window check (no copper on either layer within 0.3 of that face's windows); `tools/fascia_gold.py`; the 0.15 opening test on the rasterised F.Silk and F.Cu Gerbers (new, BLUPRNT #13); gold to the edge 1.4 or more, to a screw head 3.0 or more; `tools/dfm_check.py` on the zip |
| DISP rev C | KiCad DRC with the HV classes; `bash tools/verify_pair.sh` against DRV rev C (the new strip nets, BL_K as ground); the art's checks on the vectors; `tools/dfm_check.py` |
| DRV rev C | the schematic checks (`tools/checksch.py`, ERC); KiCad DRC; `bash tools/verify_pair.sh`; `tools/dfm_check.py`, with the SMD parts' paste and mask |
| The case | `3d/case-pair/case_pair.py`'s checks with J2's plug and the sill |

## 5. Order of work for the board-change run

| Step | Work | Its check |
|---|---|---|
| 0 | The owner's decisions (section 6, items 1 to 4) | — |
| 1 | **Bench, before any copper:** the button's stand-off and orientation (K4W411 #5); a rigid bar's lead form, pitch and dark ends (DISP #7, K4W411 #8); each colour's forward voltage at 10 and 20 mA (K4W411 #2); a 60 and a 185 flex side by side, a 38 flex beside an 18.5 bar (DISP #12, science #12); the RTC module's I2C scan; which cathode is at the front of each tube (BLUPRNT #12); an unlit coloured flex by day (DISP #13) | the resistor table and the pad pitches written down |
| 2 | **The coupon** (K4W411 #10 plus rows 29 and 30): a small board on its own | lit and by day, against the faces' colours |
| 3 | **DRV rev C schematic:** section 4.3, items 1 to 5 and 7 | ERC, `tools/checksch.py`; the datasheet's reset state |
| 4 | **DISP rev C copper:** section 4.2; the lintel's BL_A10 first | KiCad DRC with the HV rules |
| 5 | **DRV rev C layout:** the block, the routes, J2's mate, the harness pads | KiCad DRC; `verify_pair.sh` with DISP rev C |
| 6 | **Fascia R rev C, the common back:** section 4.1, items 1 to 13 | KiCad DRC; a window check against the union of all six faces' windows |
| 7 | **The art export tool** (section 2.6, item 10), then DISP's art | the 0.15 opening test; DISP DRC again |
| 8 | **Each approved fascia:** a copy of the common back, its front and pour cuts | section 4.5, per face |
| 9 | **The case model** | the case checks |
| 10 | **Firmware:** the channel table per face, the master switch order, the LED cap | the bring-up: every channel lights alone; A6 and A7 steady with all lights on |

**What can be ordered as is:** nothing for the lights. The three rev B zips make a working clock (tubes, controls, the old amber
backlight), but none carries the new lights: DISP rev B has no slots, DRV rev B no PWM chip, fascia R rev B no light pad. The coupon
can go out at once, alone: it settles the colours and the 0.55 mm strokes before any face is frozen.

**What waits:** DISP rev C and DRV rev C wait for step 1 (resistor values, the bar's pitch) and the owner's (a) or (b). Each fascia
waits for its approval, its face fixes (section 2.5) and the coupon. The case waits for J2's place to be accepted.

## 6. Open for the owner

1. **The push button:** one measure of its stand-off behind a 2.0 mm panel and which way its box lies (K4W411 #5). It is the blocker
   for every fascia's key arcs, and it decides whether P can have clips.
2. **The fascia's base:** rev B's surface-mount layout (my pick) or the through-hole T layout (K4W411 #15).
3. **Channels:** (b) a second chip (my pick) or (a) colour groups.
4. **Approvals:** disp-3-4, organic-2-1, organic-2-2, science-2-3, celestial-3 and BLUPRNT are still candidates.
5. **Organic:** move S onto the plumb bar (a face re-run, my pick), or a second back layout for organic boards only.
6. **Colours that may change** (your note on disp-3-4): with (b) it is a firmware table; with (a), say which lines now.
7. **Celestial:** the sun and the moons on one duty or apart (free with this pin map).
8. **The lintel:** swap its ends (my pick) or a polyimide dot on its right cap (DISP #7).
9. **The case:** the sill 0.8 lower, not 1.1 (DISP #10); variant D or not.
10. **The order:** the coupon alone now (my pick), or rev B's three boards as a bring-up set while rev C is drawn.

## 7. Left open

* **Not done:** no board was routed and no DRC was run. The topology of section 4.1 is *inferred*: I checked its corridors and pads
  against every face's windows, not a routed board.
* **DRV's room** is counted from courtyards only. The 11 nets that cross the block, the y 31 corridor under XS12 and the FET
  packages are not checked.
* **The part type's reset state** and output-enable behaviour are *assumed* from its usual register defaults.
* **The case:** J2's plug and lead are not modelled; the 6 mm below DISP is *inferred*.
* **The window outlines:** organic's S and P windows are boxes from its write-up (its grill exported none), which errs on the safe
  side. Science's slits are as drawn; the lowered ones (science #5) reach 0.44 mm lower, where no pad or route of the base lies.
* **Not measured** (from the grills): the button's stand-off; a bar's lead form and dark ends; every colour's forward voltage; the
  RTC module's addresses; the flex's least bend radius; the DISP to DRV gap (11.0, *inferred*).
