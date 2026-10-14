# TS06 fascia BLUPRNT: the final blueprint face (drawings only, nothing built)

2026-10-14, front round 3, run fascia-BLUPRNT. The owner's words (21:5x UTC): "final BLUPRNT fascia option: converge on 1 mixing all
three, 2-2 looks best, but drop pixelated windows, make diagrams more interesting maybe a nixie blowup components? the gold bars as
stats are a cool idea too, any way for a more interesting font?"

So this is one face. It starts from info-2-2 Data sheet (`TS06-FASCIA-info-2.md`) and takes from the other two what fits:
* from info-2-1, the title block and the clean centre mark;
* from info-2-3, the light path.

New are:
* an exploded view of the ИН-12А, whose lit front cathode is S's window;
* both ladders as gold bars;
* a technical mono for the headings and figures.

The info-2 set stays as history.

The face is fascia R with the rings-and-dots base (front-merge section 6), at one scale (11.5 px per mm). DISP-final V1 Fringes stands
above it for context. No board, schematic, fab, tool, 3D, firmware or spec file was touched. The scripts are scratch, copies of
info-2's. Marks used:
* *measured*: on the drawing's raster (23 px per mm);
* *inferred*: arithmetic;
* *assumed*: my reading.

![BLUPRNT](TS06-FASCIA-BLUPRNT/bluprnt.png)

## 1. The face

* **Creative decisions:**
  * **Kept from info-2-2:** the graph paper, the gold centre lines, the MODE switch's hidden outline and protractor, the dimension
    chain and hole pitch. Also the setting steps of the four live screens, one per line under the +5V rail, the 24 hour digit
    brightness bars, the parking screens, the dial's numbers, and the pill as an A7 meter.
  * **New: the exploded ИН-12А at 1:4, between SUB and the pill.** The tube's parts float apart along its axis, front up and right:
    * the base with its 12 pins and the tip-off pip;
    * a spacer;
    * the ten cathodes, as single-stroke numerals in the firmware's stack order;
    * the anode mesh, in gold;
    * the glass, as its front face and barrel.
    The front cathode, a "3", is **S's lit window**. It glows through the gold mesh, and a gold arrow carries its light out through
    the mesh and the glass (info-2-3's light path, now inside the tube). Rear parts break 0.3 mm where a nearer part crosses them,
    as hidden lines do on a drawing. The labels are glass, anode, cathodes ×10 (0 to 9), spacer and 12 pins.
  * **The gold bars as stats, three charts:**
    * the A6 ladder, positions 1 to 6 with ADC 0 to 1023 (it was a staircase in info-2-2);
    * the A7 lever states, open, FIELD, SUB and both;
    * digit brightness over 24 hours.
  * **The panel cable** sits between the key plates.
  * **A title block** sits right of the plus plate: BLUPRNT, TS06 rev C, 1:1 · mm.
  * **Headings and figures in a technical mono** (section 2).
* **Symmetric or organic:** symmetric. The grid, the centre lines and each control's construction are exact (about the board's centre
  and each control's axes). The exploded view, charts and tables are information on calm ground, as in info-2.
* **Lights (A1, A5):**
  * No cell windows.
  * **S** is the lit "3": bare-FR4 strokes 0.6 mm wide, a numeral 4.66 × 2.61 mm (18.63 at 1:4), centred at (105.33, 14.74).
  * **P** is a clean centre mark at (160.9, 6.6): a ring r 0.9 to 1.5 and four ticks to r 3.05, 6.1 mm across, on the ИН-15 pair's
    axis.
  * Window C is gone with its tail. A 0.3 mm gold trace runs in AMBIENT's row, from the name into its mark on FIELD's ring (on the
    GND gold net), and C's place in the tube map gets its colon dots back.
* **Filaments:**
  * The base's places and lengths, **all warm**: rigid bars in warm white, flex in yellow (front-merge section 5).
    * The MODE arc is 38 flex.
    * FIELD and SUB are 18.5 rigid in curved clips, or 38 flex.
    * The keys are 38 flex.
  * S's tail is an **18.5 rigid warm bar, plumb** behind the "3", y 5.5 to 24.0.
  * P's tail is moved 2.1 mm down, as in info-2-1.
* **Pill (A2):** the resistors are not moved, so the circuit is unchanged. The pill is info-2-2's A7 meter: 0 at its foot, 1023 at its
  head, white ticks every 0.5 mm, and gold ticks at 1023, 682, 512 and 409. It sits beside the A7 bars, which give the same four
  numbers.
* **Rails (A3): shown white.** Silk is printed full width over the masked copper, broken at each pad and index bulb. Copper and mask
  are unchanged.
* **White:**
  * the grid: 1 mm dots, 5 mm lines 0.15;
  * the exploded view's outlines, 0.15, with hidden-line breaks of 0.3;
  * leaders, 0.15 with a 0.22 dot;
  * the meter's ticks, the title block's rules and the text.
  * Fragments under 0.06 mm² are dropped, so no silk specks are left.
* **Gold:**
  * the centre lines, hidden outline, protractor and dimension lines, 0.2;
  * the anode mesh, 0.14 lines on a 0.64 mm diagonal pitch;
  * the light path, 0.22 with a head;
  * the A6, A7 and 24 hour bars, and the meter's four ticks.
  All are isolated islands, apart from the AMBIENT trace.
* **Buildable? OK** on the base's needs (front-merge items 9 to 11), with three conditions:
  * S's clip and pour cut move behind the "3" (section 3);
  * the 0.6 mm window strokes need the fab's yes with the bare-FR4 coupon (said once here; not decided);
  * the face uses an outline font (section 2).
  The back behind S's new place is not checked.

![BLUPRNT at 2x](TS06-FASCIA-BLUPRNT/detail-2x.png)

## 2. The font

The fab's floor for silk is 1.0 mm text and 0.15 mm lines (`fab/ORDER.md` line 95, *inferred* there; `PCB/README.md` line 272).
KiCad turns a TrueType text into outlines. So the font's own thinnest stroke must be 0.15 or more at the size and width used. I
measured each candidate on a 200 px per mm raster: the 5th percentile of the stroke width at the glyphs' ridges.

**Proposals** (open licence; no font file goes into the repo; each to be checked with its real file at the fab's floor):
1. **Share Tech Mono** (SIL Open Font License 1.1). A squared technical mono that reads as an instrument. It is my pick for the
   headings, the tables and the figures.
2. **B612 Mono** (SIL Open Font License 1.1). A mono drawn for legibility on cockpit screens, with open, sturdy figures. The safe
   second.
3. **Osifont** (GPL 3 with the font exception; *to verify*). The ISO 3098 lettering of engineering drawings. Its line is a tenth of
   the height, so a 0.15 line needs 1.5 mm capitals: for titles only.

**What the face uses, all installed and free-licensed, so it is buildable as drawn:**

| Use | Font as drawn | Size | Thinnest stroke (*measured*) |
|---|---|---|---|
| Headings (A6 MODE · ADC, J1, BLUPRNT, 6 POS), dimension values | DejaVu Sans Mono Bold, 90 % width; stand-in for proposal 1 | 1.2 mm capitals | 0.170 |
| The tube's title, ИН-12А | DejaVu Sans Mono Bold, 92 % width | 1.4 mm | 0.200 |
| Data rows, labels, cable, title block | DejaVu Sans Bold, 80 to 82 % width; stand-in for proposal 2 | 1.0 mm | 0.160 |
| Long whole lines (the setting steps, the resistor notes, the parking screens) | KiCad's own stroke font, line 0.15; drawn here in Liberation Sans | 1.0 mm | 0.15 by its line |

Two findings:
* **Mono Bold at 1.0 mm fails** (0.140), so the mono is used at 1.2 mm and up.
* **info-2's plain sans (Liberation Sans Regular) would be 0.100 as an outline font.** It only holds as KiCad's stroke font, which
  is what the long lines here keep.

Courier 10 Pitch was tried for "typed notes" and dropped: it has no Cyrillic for ИН-12А.

![Fonts](TS06-FASCIA-BLUPRNT/font-samples.png)

## 3. The light base and what this face changes

The base is front-merge section 6: nine windows and C, ten filaments, three fascia channels, all warm.

| Item | Base | BLUPRNT | On the fascia's back |
|---|---|---|---|
| info S | 2.0 mm dot at (108.6, 4.5) | lit "3" at (105.33, 14.74), 10.7 mm from the base's dot (8.8 from info-2's) | the 18.5 rigid warm tail stands plumb behind it (y 5.5 to 24.0): a new clip place and a pour cut that follows the numeral |
| info P | 2.0 mm dot at (160.9, 4.5) | centre mark, 6.1 across, at (160.9, 6.6) | tail 2.1 mm down; the pour cut follows the mark |
| info C | window at (45.04, 21.2) | removed (A5); gold trace in AMBIENT's row | no cut, no tail |
| the rest | MODE arc, FIELD and SUB up and down, key arcs | unchanged | unchanged |

* The info channel drives S and P only. That makes nine windows and nine filaments on the same three channels, and 20 mA less on the
  5 V side at front-merge's 20 mA a filament (*inferred*).
* No channel is added. The connector stays at 6 channels.
* The plumb bar clears SUB's lever body (x ≤ 93.3) and the pill (x ≥ 113.9) on the back (*inferred* from the art model; the back's
  parts were not checked).

![The fascia's back: base and BLUPRNT](TS06-FASCIA-BLUPRNT/lights-back.png)

## 4. Where each printed fact comes from

| Printed | Source |
|---|---|
| ИН-12А (the hours and minutes tube) | `knowledge/TERMINAL-06-spec.txt` lines 6 and 7 |
| Exploded view: face 19.47 × 28.86, 25.50 deep (drawn at 1:4), 12 pins Ø0.92 with 6.25 free, tip-off pip Ø3.70; the leads leave the rear face | `knowledge/TERMINAL-06-measurements-IN12.txt`, the `3d/IN12.FCStd` parameters (envW, envH, envD, pinCount, pinD, pinFreeL, pipD). The sheet says their provenance is unconfirmed; only the count "12 PINS" is printed |
| The numeral's height, 18.63 (the lit "3" is drawn at 4.66) | the same sheet, reading 4, *measured* |
| CATHODES ×10, 0 TO 9 | `TERMINAL-06-measurements-PCB-GYVER-NETLIST.md` line 127 (ИН-12А pins 2 to 11 are the cathodes 0 to 9) |
| The cathodes' order in the stack, rear to front 1 6 2 7 5 0 4 9 8 3 (drawn, not printed) | `firmware/nixieClock_TS06/nixieClock_TS06.ino` lines 284 to 286 (`cathodeMask`, "the tube's, as type 0"); `effects.ino` line 63 ("scroll along the physical cathode stack") |
| GLASS, ANODE (a mesh), SPACER; the lit cathode's light out through the mesh and glass | general nixie construction, no figures (as science-2-1: "anode: fine mesh", "the one pulled low glows") |
| A6: positions 1 to 6, ADC 0, 205, 409, 614, 818, 1023; 5 × 4.7 kΩ 1 %, 1 V a step | spec section 2, the A6 table (lines 345 to 354) |
| A7: open 1023, FIELD 682, SUB 512, both 409; 10 k pull-up, FIELD 20 k, SUB 10 k to GND | spec section 2 (lines 378 to 380); R6, R7, R8 in the board model |
| J1 · PH 2.0: 1 +5 V, 2 GND, 3 A6, 4 A7, 5 D7 −, 6 D8 + | spec section 2, the J1 table (Rev D.4) |
| Setting steps 2 to 5 | spec section 1, the control table |
| 1 NORMAL and 6 INFO: no input; both are end stops | spec section 1 |
| 6 POS, 30.00° a step, 150° in all, 12 detents | spec section 2, the switch table |
| Digits 21 by day, 6 at 23-07 | firmware `nixieClock_TS06.ino`: `INDI_BRIGHT 21`, `INDI_BRIGHT_N 6`, `NIGHT_START 23`, `NIGHT_END 7` |
| Control pitches 39.10, 23.38, 31.515, 31.515, 21.00; hole pitch 31.00 | the board model's centres and screw holes (as info-1) |
| Title block: BLUPRNT; TS06 rev C; 1:1 · mm | the owner's name for this option; pass 4 section 7 (rev C, the next fascia face); true of the drawing |

* *Assumed:* the firmware's `cathodeMask` gives the order along the stack, not which end faces the glass. It is drawn with the "3" at
  the glass. If the bench shows the other end, the drawing reverses the order and the lit front cathode becomes the "1". The mask
  itself is not yet measured on a tube: `knowledge/QUADRANT-D-spec.txt` line 312 says "the ИН-12 mask looks *almost* right", and
  `knowledge/TERMINAL-06-measurements-IN17.txt` row 16 leaves it to a `secCathodeMap` session. So the order is not printed, only
  drawn.
* *Drawn, not to scale:*
  * the pins' places on the rear face (two side groups and two end groups of three, from the model's radii, compressed);
  * the spacer's holes;
  * the mesh pitch;
  * the barrel's depth, which is cabinet, at half.

## 5. Setting steps the firmware does not do yet

The face prints the spec's scheme (spec Rev D.4 section 1, control scheme rev B). The firmware is the display-layer port. Its TODO is
in the header of `ts06pair.ino`, and the spec's own list is section 5, "Firmware status: control scheme NOT implemented". This is
as info-2 section 7 found it. Its key points were rechecked here: `ts06pair.ino` lines 30 to 41 ("A7 is not read"; NORMAL and INFO
"are meant to ignore every input") and spec line 672 ("Still to write: A6 mode state machine ...; A7 lever decode").
* **Not done: A7 is not read at all.** So none of the FIELD or SUB steps work yet:
  * SET TIME: hour or minute by FIELD;
  * DISPLAY: brightness or effects, then transition or glitch;
  * AMBIENT: colon or backlight;
  * FORMAT/DATE: format or date, then day-month or year;
  * the SUB rule.
* **Not done:** only SET TIME is its own screen (PROGRAM). There "−" switches hours and minutes and "+" counts up, so "− and + adjust
  it" is not yet how it works.
* **Not done:** DISPLAY, AMBIENT, FORMAT/DATE, NORMAL and INFO all run the old two-button controls:
  * "−" cycles the backlight mode, and a hold turns glitch on or off;
  * "+" cycles the transition effect.
  So these are not true yet:
  * "NORMAL and INFO: no input";
  * AMBIENT's style cycling;
  * FORMAT/DATE's 12/24 h flip and date edit;
  * the glitch *rate*.
* **Done:**
  * the five-reading agreement filter (`rotaryStable()`);
  * the A6 position decode (`rotaryPos()`, positions 1 to 6 as printed);
  * the day and night digit brightness (the 24 hour bars).
  The A6 and A7 numbers on the face are the spec's ladders. The A6 ones are what the firmware decodes.

## 6. The checks (*measured* on the raster, 23 px per mm)

| Check | Rule | BLUPRNT |
|---|---|---|
| White, gold to a name, plate, key legend, tube map, leader or index dot | 0.75 | 0.78, 0.80 |
| White, gold to E1's exposed gold (rings, link, marks, pads) | 0.30 (gold frame 0.75) | 0.43, 0.75 |
| Pattern gold to any copper | 0.30 | 0.39 |
| White, gold to a lit window (the "3" and the centre mark included) | 0.35 | 0.39, 0.40 |
| Lit window to copper | 0.30 | 0.39 |
| Lit window to a legend | (base's least was 0.26, C to AMBIENT) | 1.17 |
| White to the pattern's gold | 0.30 | 0.33 |
| AMBIENT trace to its name; to white; to pattern gold | 0.75; 0.30; 0.30 | 0.78; 1.17; 2.39 |
| Silk to silk in the exploded view (hidden-line break) | 0.15 | 0.30 by construction |
| Thinnest font stroke | 0.15 | 0.160 (section 2) |
| Free board within 1.2 mm of some ink | (no empty space) | 98.6 % |

White may run over copper under the mask (the rails, the key rings, the capsule), so white to copper is 0 by design.

## 7. What did not fit, and left open

* **Did not fit at a readable size:**
  * info-2-1's revision table and its section A-A of the MODE switch;
  * info-2-3's whole clock in section.
  The only calm blocks tall enough (between SUB and the pill, and between the pill and the minus key) now hold the exploded tube and
  the ladders' bars. What came across: info-2-1's title block (shortened) and centre mark (as P), and info-2-3's light path (inside
  the tube).
* *Assumed:* S's plumb 18.5 bar lights a 4.7 mm numeral evenly enough through 2.0 mm FR4. The bench decides. A short flex piece bent
  to the "3" is the fallback.
* *Assumed:* the 0.6 mm window strokes are wide enough to cut and to light. info-1's marks used the same 0.6.
* Not checked:
  * KiCad DRC (no board file edited);
  * the text in the real proposal fonts (stand-ins drawn);
  * the back's copper and parts behind S's new place;
  * the connector's place on the back (front-merge item 11).
