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
