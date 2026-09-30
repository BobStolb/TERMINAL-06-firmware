# TS06-DISP + TS06-DRV: design review, and what it means for the case

A critical pass over the through-hole pair: what it gets right, what is weak, what was fixed
on the way, and what is still open before an order. The last part turns the stack's geometry
into suggestions for the case, which has not been started.

## Verdict

The pair meets the brief electrically:
* through-hole only;
* no vias on either board;
* a display board that carries nothing but the tubes;
* two boards that plug together with no harness.

Both boards pass KiCad 10's DRC with nothing unconnected. TS06-DRV has no errors; TS06-DISP
has two, the accepted overlap of the colon lamps' courtyards with the M10 tube, which waits on
a test fit (see `PCB/README.md`, "Checked"). An independent audit traced every anode and every
digit through both boards and the firmware.

**The pair now has schematics** (`PCB/TS06-*/TS06-*.kicad_sch`, from `tools/mksch_pair.py`), one sheet per section. They are checked against the boards net for net, and KiCad's ERC, run on this pair for the first time, reports 0 violations. Its first run found two real errors, both undriven power inputs. PWR_FLAGs now mark where 12 V and GND really arrive.

`tools/verify_pair.sh` runs every check in one command, including two that read the written
files with KiCad's own geometry: the mate of all 63 strip pins and 4 standoffs, and the pours
as KiCad fills them. **The committed boards store no zone fill:** refill before plotting Gerbers
(press B, or `kicad-cli pcb export gerbers --check-zones`). The display's LED return, BL_K,
exists only as a pour, so a Gerber plotted unfilled leaves all nine LEDs open.

**One finding blocked an order, and it was mechanical:** the two ИН-17 were placed 13 mm apart,
where their Ø20 stems need 20.5. It came from the tube coordinates every board so far had used.
**It is fixed.** The owner chose to widen the boards to 191.4 mm and keep the Gyver pitch.
Both boards were then re-placed, re-routed and re-verified (next section).

A second round of four independent reviews (30.09.26, next section) found no blocker for the
boards, and several things that DO need new copper on the driver board:
* an independent over-voltage clamp for the 185 V rail (E1);
* 0.8 mm between bare 185 V pads and other copper, per IPC-2221B (E3);
* footprints for the 0.5 W resistors actually on sale (F4);
* a real inductor, and a few protection parts.

These make up **TS06-DRV rev B**, which is now routed and merged (30.09.26, next section). The
display board needed only its silkscreen and a few clearances. The mechanical points from the
first round still stand:
* the stack height;
* the order in which the strips are soldered;
* a few tall parts;
* the case openings for the two connectors.

## TS06-DRV rev B, 30.09.26

Rev B puts the second grill's driver-board items into copper (rev A is 78105d6). The full list,
part by part, is in `PCB/README.md`, "TS06-DRV rev B: what changed":
* the independent over-voltage clamp (E1): VD5-VD7, R75, R76 and VT2 on PWM_G;
* 0.8 mm from every bare 185 V pad to all other copper, as a KiCad rule (E3);
* the USB back-feed diode VD3 (E5) and the input TVS VD4 (E8);
* the fascia inputs' 1 M pull-down on A6 and 1 k + 10 nF on D7 and D8, placed by hand between
  the strips and J1 (E11);
* 0.5 mm at the cathode pads, with oval-pad decoder sockets (E10);
* МЛТ-0,5 footprints (M4), a real L1 (M2), U13 on a male PLS-5 with its legend (M1), larger
  VT21 and J1 holes (M7);
* copper keep-outs round the standoff holes (M12, R1), silkscreen at the fab's floor (M8), the
  DNP attribute (R13);
* a route that reproduces: a fresh `--route` rebuilds the saved one byte for byte (R6).

**Where it stands:**
* `tools/verify_pair.sh`: **27 PASS, 0 FAIL, 0 SKIP**. That includes KiCad's DRC on TS06-DRV
  (0 errors, 0 unconnected), the live HV rule, ERC, the mate from the written files and the case
  model.
* The case model reads the new parts' heights: the case is **81.6 mm deep** (rev A 83.6).
* The fab packages are built from the committed boards, pours filled (`fab/`, `tools/mkfab.sh`).
  Nothing is ordered.

| Scored from the board files | Rev A | Rev B |
|---|---|---|
| Segments / vias | 1097 / **0** | 1164 / **0** |
| Signal copper / its floor | 5936 / 4479 mm = 1.33 | 5918 / 4533 mm = **1.31** |
| Straight (0°/90°) share | **86.1 %** | 83.3 % |
| DIP orientations | 3 | 4 |

**One change is not on the list: U11 now stands at 0°,** a fourth DIP orientation (finding 5).
It came with the placement recovered after the layout agent was lost. Everything passes with it.
Whether to turn it back to 180° is the owner's choice; that would mean routing the board again.

**What no check can show:** the clamp's trip voltage (225-270 V) is computed from the parts'
tolerances. It is measured only on the bench (`PCB/README.md`, "Open before fabrication").

## What holds up

* **A wrong cathode order at the bench is a firmware fix, not a new board.** Every cathode on
  both boards is driven by a К155ИД1 whose input code the firmware chooses: the ИН-12 bus and
  the ИН-17 pair through U2 and U17 on A0–A3, the two ИН-15 through U15 and U16 on the
  expander's port A. If gate 3 (ИН-17 lead order) or gate 4 (ИН-15 pinouts) comes back
  different from the maps the boards were drawn with, the fix is a lookup table. Only three
  things are physical: which pin of each tube is its anode, the RTC module's pin order
  (gate 6), and the ИН-17 pip (gate 5). The ИН-12's hole-to-function map is already closed
  from the inherited board's copper. Gate 2 (sustaining voltages) only sets the anode
  resistor values, which are through-hole parts and can be changed at any time.
* **High voltage stays in its own lanes.** Every 185 V net is its own net class (0.6 mm
  clearance, which KiCad's DRC enforces from the project file). Bare high-voltage pads are
  0.8 mm from every other pad (IPC-2221B A6). `checkcopper.py --hv` is clean on TS06-DISP.
* **The display board is drawn by hand, every line.** The ИН-12 bus is ten parallel zig-zags
  threaded through the sockets on the back face, the way Gyver's tube half does it. The
  ИН-17 and ИН-15 bundles wrap their tubes from above. Anodes and LEDs drop straight to the
  bottom strips. There is nothing there for a router to have made ugly.
* **Every change of face happens in a part that is in the circuit anyway.** A through-hole pad
  is the only place a net may change face, so the driver board is placed around its series
  resistors:
  * the four lines that share the corridor beside the Nano (the converter's PWM, the colon,
    the "m" LED, the S1 opto) end in four standing resistors at its exit;
  * the opto resistors of the minutes and S10 (the 470 R in series with each opto's LED)
    stand under the Nano;
  * the I²C pull-ups and the fascia's ladder filters stand in one column beside the hours'
    optos. A7, A6, SCL and SDA reach the column on the front face, threaded between the
    optos' pin rows, and leave it on the back face.

  No wire links and no zero-ohm jumpers.
* **On the driver board, the long buses are drawn too.** Port A of the expander runs up the
  left edge as one eight-line bus. The LED ribbon runs in lanes under the bottom strips. The
  U17 branch of A0–A3 drops down a corridor beside the Nano and enters U17 between its rows,
  the one approach that lands every line on its own pin without a crossing. The Nano's
  fan-out is drawn as well: every pin below the module except D7, D8 and D11, which are
  drawn only as far as the gap beside U2. The router fills in the rest: those three lines
  onwards, the I²C pair past its pull-ups, the rails and the wiring inside each cell.

## Findings, most serious first

### Fixed: the two ИН-17 did not fit 13 mm apart

TS06-DISP puts S10 and S1 at x 104.605 and 117.605: 13.0 mm between centres. It carried that
from TS06-MAIN, which took it from the FreeCAD assembly. The ИН-17's own record says it cannot
work: `knowledge/TERMINAL-06-measurements-IN17.md` Rev 5, closed from a factory outline drawing
on 09.09.26.
* The ИН-17 is a round **Ø20 stem** flattening to a 14 mm face.
* Concept Rev F spaced the pair **20.5** apart for exactly this reason: "a 3 mm face gap puts
  the stems 17 apart and they touch".

At 13.0:
* the two stems overlap by 7 mm;
* S10's stem overlaps M1's glass;
* S1's stem overlaps ИН-15Б's glass.

The case model's check (`3d/case-pair/checks.md`, row 9) found it; the repo's tube record
confirms it. No courtyard check could see it, because the ИН-17 footprint has no lead circle
yet (gate 5) and its courtyard is only the leads.

**What fixing it costs.** Spacing the seconds pair at 20.5 needs about 13 mm more of the row
between M1 and ИН-15Б. There are two ways to find it:

| | Keep the 176 mm boards | Widen the boards (Rev F's face is 204 mm) |
|---|---|---|
| How | Close the ИН-12 pairs from 23.4 to ~21 mm; close the ИН-15 pair to 20.5; use most of the right margin | Keep every other pitch; move the ИН-15 pair ~13 mm right; boards and case ~13 mm wider |
| Look | the tubes nearly touch; not Gyver's pitch | as drawn, with a wider clock |
| Work | both boards re-placed along x | both boards re-placed; the fascia is not tied to the tubes |

Either way, the display board's copper and XP12 move, and so do the driver board's XS12 and
the decoder rows under it, which means a re-route. The layout method here makes that
routine, but the look is a design decision, so it is left to the owner.

**Fixed on 29.09.26: the owner chose to widen the boards and keep the Gyver pitch.**
* **The display:** S10 and S1 now stand 20.5 apart, each stem 2.2 mm from the glass beside
  it. The ИН-15 pair moved 15.4 mm right, and both boards are 191.4 mm wide.
* **XP12:** still one strip, now 31 pins. Three spares take up the 7.62 mm the ИН-15 group
  moved beyond the ИН-17 group.
* **The driver board:** re-placed by blocks and re-routed. Round 15 had 0 nets sharing, and it
  has 0 vias and 0 DRC errors.
* **The case:** its check now reads 0.5 mm stem to stem, the margin Rev F chose, and the case
  is 204.4 mm wide, Rev F's face.

Gate 5, a real ИН-17 on calipers, should still confirm the Ø20 stem: one caliper reading gave
19.30 mm.

### 1. The 11 mm stack is a sum of two catalogue numbers: check it against the parts in hand

The boards are 11 mm apart because a standard PBS socket is 8.5 mm tall and a PLS header's
plastic body is 2.5 mm. Both vary between makers (PBS runs 7.0–8.5 mm). An 11 mm M3 standoff
exists but is uncommon: a 10 mm standoff plus a 1 mm washer does the same job.
**Before ordering, measure one PBS and one PLS from the batch you will buy, and set the
standoffs from that.** If they disagree with 11 mm, the strips either do not seat or they
bend the display board over its four standoffs.

The standoffs share that gap with the strips' plastic, and no courtyard check sees it: the
hole's footprint is on the front, the strip's on the back. The independent check found the
top-right standoff (display H4) with a hex spacer's corner 0.5 mm from XP12's end and a
7 mm washer 0.2 mm from it. **Fixed:** H4 moved 2 mm down on both boards, to display
(172.5, 7.5), now (187.9, 7.5) on the widened board. A 5.5 mm hex spacer clears the strip by 1.9 mm and a 7 mm washer by 1.6 mm.

### 2. Solder the strips while they are plugged together

Seven strip pairs carry 60 contacts across two boards. If each board's strips are
soldered on their own, a tenth of a millimetre of tilt on each makes the stack hard to mate
and puts the tube pins under load. The fix costs nothing and belongs in the assembly
instructions:

1. Fit all seven PLS strips into their PBS sockets.
2. Drop the sockets into TS06-DRV and the headers into TS06-DISP.
3. Screw the four standoffs in.
4. Solder both boards with the stack assembled.

The same order also sets the stack height from the real parts (finding 1).

### 3. Some solder joints show on the display's front face

The headers sit on TS06-DISP's back face, so their joints are on the front, among the
tubes. The bottom strips (XP21–XP25) are hidden if the fascia, or the case lip above it,
rises to world Y ≈ 38. **XP12 across the top and XP11 down the left edge are not hidden by anything but
the case.** The brow has to cover the top 4 mm of the display board, and the trench wall
the left 3 mm. The four standoff screws land on that face too. Three are in corners; only
H3, at the top of the colon column, is between tubes. Use black countersunk or low-head
screws.

### 4. 185 V is on the driver board's rear-facing side, and C7 stays charged

TS06-DRV's component face looks at the back of the case. It carries C7 (4.7 µF at 185 V,
about 0.08 J and 0.9 mC, above the usual touch-safe limits), the switch's TO-220 tab (the SW
node, up to about 190 V), the six optos, and every anode and ballast resistor. The bleeder
(R60 + R61, 940 kΩ) and the feedback divider (1.52 MΩ) take C7 down with a time constant of
about 2.7 s, so it is safe after about 15 s, not immediately.

**The rear of the case must be a closed panel held by screws.** Its vent slots should be
no wider than 2.5 mm, and it needs a high-voltage mark. The service note should read:
"unplug, wait 15 s".

### 5. Three chip orientations on one board (four in rev B)

On TS06-DRV, U15, U16, U17 and RN1 have pin 1 to the left. U3 and the six optos (U5–U10)
have it to the right. U2, U11 and U12 have it at the bottom. **Rev B stands U11 at 0°**, a
fourth orientation. It came from the recovered placement and is not on rev B's change list;
the owner decides whether to turn it back. Each orientation is what made the zero-via
routing possible, but at an assembly bench it is the most likely mistake: a DIP socket
soldered backwards is caught only when a chip is fitted, and a chip fitted backwards may
be destroyed.

**Mitigation:**

* Every socket's notch is on the silkscreen.
* The assembly sheet should list each socket's notch direction.
* Fit the sockets first and check them against the sheet before fitting any chip.

### 6. The tallest parts set the case's depth

| Part | Height above TS06-DRV | Can it lie down? |
|---|---|---|
| U13, DS3231 mini standing in a 5-way PBS | ≈ 21–22 mm | yes, with a right-angle header (≈ 12 mm) |
| VT21, IRF840 in TO-220, vertical | ≈ 19 mm | only if the board beside it is kept clear: the tab is the 185 V switch node and would need an insulating pad |
| C7, 4.7 µF 400 V, Ø10 radial | ≈ 16–20 mm | yes: lay it on its side (≈ 11 mm) |
| U1, Nano on PBS-15 sockets | ≈ 16.6 mm | no, it stays removable |
| L1, radial 220 µH | ≈ 16 mm (its footprint's height) | no |

The case model measures each part against the rear panel: U13 has 5.0 mm, C7 7.0, VT21
8.0, the Nano 10.4 and L1 11.0. U13 sets the depth. Laying down U13, C7 and VT21 makes the
case 78.2 mm deep instead of 83.6. After that, the Nano and L1 set it.

**Rev B:** U13 sits on a male PLS-5 (15 mm) and L1 is the axial Bourns part, lying (12 mm). The
case model reads their heights from the footprints: C7 now sets the depth with 5.0 mm, then
VT21 6.0, the Nano 8.4, U13 10.0 and L1 13.0. The case is **81.6 mm deep**. Laying down U13, C7
and VT21 still gives 78.2.

### 7. Header neighbours: 5 V next to 185 V at the minimum spacing

On XS21 and XS23–XS25, backlight lines (5 V) sit beside anode pins (185 V). At 2.54 mm pitch
with 1.7 mm pads, the gap is 0.84 mm against IPC-2221B's 0.8 mm for uncoated component leads.
It passes, but only just. A solder bridge there puts 185 V into the MCP23017's port B.
**Inspect those four strips under a loupe before power-up.**

### 8. The firmware must be told which board it is on, and it now knows

The pair needs `BOARD_TYPE 4`. It is in the firmware but is not the default (0). A clock
built with these boards and flashed with the default shows scrambled digits. For a batch,
either change the default on a pair branch or put it at the top of the build sheet.

The independent audit found that type 4 carried only the digit map and the anode order. The
rest of the firmware still assumed the bench board:
* It read the PROGRAM/RUN lever on D12, which drives the "m" LED on the pair.
* It scanned four slots, so S10 and S1 would never light.
* It had no MCP23017 code, so the backlight and both ИН-15 would stay dark.

**Fixed** (`firmware/nixieClock_TS06/ts06pair.ino`), compiled for the Nano as types 0 and
4, with types 0–3 byte-identical before and after:
* type 4 scans all six slots;
* it drives the "m" LED on D12;
* it starts the MCP23017 with both ИН-15 blank and all eight backlight LEDs on, still dimmed
  by D11;
* it reads PROGRAM/RUN from the fascia's MODE rotary on A6, where SET TIME is PROGRAM.

The fascia has no lever: its A7 carries the FIELD and SUB levers on a ladder.

**Still to write, or to check on the bench:**
* **Six slots at the current timing:** a 50 Hz frame and 13.5 % duty, against 75 Hz and
  20 % at four slots. Check for flicker and ghosting, and whether the ИН-12 is still bright
  enough.
* **The rotary's other screens.**
* **The spec's agreement filter on A6.** With the fascia unplugged, A6 floats, so bring a
  pair up with the panel connected.
* **The levers on A7.**
* **The ИН-15 content,** AM/PM and the idle cycle. `GLYPH_Q` in `tools/ts06pair.py` has the
  tables.
* **Per-LED backlight.**

**Older problems the audits found, which affect every board type:**
* **Fixed 30.09.26: the RTC was reset to the build time on every boot.** `setup()` called
  `rtc.adjust()` unconditionally, so a power cut lost the time. It now runs only when the
  DS3231 reports it lost power (`rtc.lostPower()`). After flashing, set the time with SET
  TIME, as on any shipped unit.
* **Fixed 30.09.26: leaving PROGRAM rewrote the clock.** `leaveProgram()` wrote
  `DateTime(2026, 1, 1, hh, mm, 0)` every time, edited or not. On BOARD_TYPE 4 the MODE
  dial passes SET TIME on its way from NORMAL, so every turn of the dial cost up to 59 s
  and the date. The RTC is now written only after an edit, and the date is kept.
  Types 0 and 4 compile (11,850 and 12,072 bytes) with no new warnings.
* **The committed `nixieClock_TS06.hex` is stale.** It is a BOARD_TYPE 1 build of the
  first commit, not what the source builds today. Rebuild it for the board you flash; it
  is left as it is because the bench clock's type is the owner's to say.

A per-slot digit table for the two ИН-17 slots and the ИН-15 codes is still cheap insurance
for gates 3 and 4.

### 9. Smaller points

* **The colon lamps' courtyards overlap the M10 tube's by 0.135 mm** at their measured
  positions. This is inherited from TS06-MAIN and needs a check with a real tube.
* **A hole courtyard (H3, above the colon) runs 0.15 mm past the display board's top
  edge.** Harmless.
* **Decoupling:** each decoder has its 100 nF on the 5 V rail, but not tight against its
  pins, where the port-A bus runs. For static TTL decoders this is fine. The MCP23017, the
  comparator and the driver have theirs close.
* **The I²C lines carry about 235 mm of copper each** (238 and 233 mm; about 140 mm point to
  point) from the Nano to the expander, with the RTC on the way.
  At 100 kHz with 4.7 kΩ pull-ups, that is well inside the bus's capacitance budget.
* **TS06-DRV's ground pours are in pieces.**
  * The ground is a routed tree: every GND pad is joined by track. The pours on both faces
    only add area around it.
  * Between the hand-laid buses, the pours break into islands. KiCad's own fill keeps **13
    pieces on the front and 14 on the back**, the largest holding 91 % and 75 % of the copper.
    Rev B: 15 on the front and 10 on the back, the largest 92 % and 33 %.
    This review first quoted 95 and 137 from `audit.py`, whose grid model also counted pieces
    that touch no ground copper, which KiCad removes. `audit.py` now counts only the kept
    pieces, and `verify_pair.sh` reports KiCad's own count (the red-team's finding F5).
  * Six pads whose pour was only a sliver keep out of the pours (`no_zone` in the
    generator), which is what cleared KiCad's "starved thermal" errors.
  * It works, but it is not a ground plane. The "plane" alternative layout (below) tests
    whether a placement built around an unbroken back-face ground can do better.
* **The case model's tight spots:**
  * the trench's left wall is 0.475 mm from H10's glass;
  * the sill is 0.59 mm from the ИН-17 LEDs.

## The second grill, 30.09.26

Four review agents worked independently at commit 40cc33b:
* manufacturing, pinouts and assembly;
* electrical, safety and EMC;
* fascia, case and product;
* a red-team of the checks themselves.

Every finding below was checked against the files before it was acted on. The pinouts all
check out against their datasheets:
* К155ИД1, MCP23017, LM393, TC4420, TLP627, R-78E, MPSA42 and IRF840;
* the Nano, the jack, the diodes, the electrolytics and the LEDs;
* all 63 board-to-board pins.

**Status key:**
* **fixed:** with the commit;
* **rev B:** in TS06-DRV rev B, routed and merged on 30.09.26 (b8d3f25; see "TS06-DRV rev B"
  above);
* **DISP:** the display board's silkscreen and clearance pass, now in progress;
* **case:** the case-model pass, now in progress;
* **open:** needs a decision or the bench.

### Electrical, safety, EMC

| ID | Finding | Checked | Status |
|---|---|---|---|
| E1 | Nothing independent limits the 185 V rail: without U12, or with it reversed, the converter runs open-loop (a model reaches 300 V in 40 ms with the display off) | Circuit: U12's open collector is the only thing holding PWM_G low | **rev B**: zener string + NPN on PWM_G. Until then, the bring-up rule is: fit and check U12 before U11 |
| E2 | The static ИН-15s ran at 4.2–5.4 mA through 8k2, about twice their 2.5 mA rating | Arithmetic; the ИН-15 is not multiplexed | **fixed** 28ce526: 18k, 2.5 mA |
| E3 | Bare HV pads were 0.60 mm from the GND pour and some LV tracks; IPC-2221B A6 at 171–250 V asks 0.8 mm | Table 6-1; the net-class clearance is 0.6 | **rev B** + **DISP**: a custom KiCad rule at 0.8 mm, a refill, and the tracks moved |
| E4 | At power-on, L1's current ratcheted past saturation: D9 jumped straight to DUTY with C7 at 12 V | Firmware: `setPWM(GEN, DUTY)` in `setup()` | **fixed** 28ce526: an 85 ms soft-start. L1 itself: **rev B** |
| E5 | USB power back-feeds the R-78E's output | The Nano's USB diode feeds +5V | **rev B**: a 1N5819 across U14. Until then, connect USB only with 12 V applied |
| E6 | The ИН-12s are structurally dim at 6 slots: 13.5 % duty caps the average at about 0.95 mA | К155ИД1 7 mA sink limit | **open**: bench, dead-time or slot trade-off |
| E7 | C7's ripple current, about 0.11 A rms at 31 kHz, meets or exceeds a general-purpose part's rating | Model | **open**: a 105 °C high-ripple C7, a low-ESR C8 |
| E8 | A 19–24 V adapter would kill U11 (20 V max) and VT21's gate | Datasheet limits | **rev B**: a 1.5KE18A after F1 |
| E9 | RP1 could set up to 252 V | 2.5 V × (1 + 1500k / 15k) | **fixed** 28ce526: 18k + 5k trimmer gives 165–210 V |
| E10 | Cathode pads 0.32–0.35 mm from LV and other cathode tracks | Board geometry | **rev B** + **DISP**: 0.5 mm where it can be routed |
| E11 | The fascia inputs float when the lead is unplugged; D7/D8 have no filtering | Circuit | **rev B**: 1 M from A6 to GND; 1 k + 10 nF on D7 and D8. The firmware no longer rewrites the RTC on a spurious PROGRAM (d7aafdc) |
| E12 | The switch node rings with no snubber; R67 is 10 Ω | Model only | **open**: R67 22–47 Ω and an RC snubber, sized on the bench |
| E13 | Off anodes can float up and ghost; the bleeders are DNP | TLP627 dark current | **open**: fit the DNP bleeders if the bench shows ghosting |
| E14 | The input is about 5.1 W, not 3.5 W; A0–A2 each sink 6.4 mA, not 3.2 | SN74141 input loads | **fixed** in this review |

### Manufacturing, pinouts, assembly

| ID | Finding | Status |
|---|---|---|
| M1 | U13: the DS3231 mini's header is female, so the board needs a male PLS-5. Pad 1 (square) is GND, and the module's "+" is its pin 1: matching square to square reverses it | BOM **fixed** d7aafdc; footprint and "− NC C D +" legend **rev B** |
| M2 | No Ø12 mm radial 220 µH part saturates above about 1.3 A; the note asks for 1.8 A | **rev B**: a real part, a new footprint |
| M3 | F1's footprint is named after an 11 A part | BOM **fixed**: 1.1 A, e.g. MF-R110 |
| M4 | МЛТ-0,5 / С2-23-0,5 (Ø4.2 × 10.8, 0.8 mm leads) fit neither the 0.8 mm drill nor the 3.8 mm row spacing | **rev B**: 1.1 mm drill, 15.24 mm pitch, ≥5 mm rows |
| M5 | The tube socket contact is unspecified, and the 1.2 mm hole was sized for the tube's own pin | BOM line **fixed** (72 contacts); which contact is **open** |
| M6 | TLP627 is obsolete | BOM **fixed**: TLP627MF, from authorised stock |
| M7 | VT21 and J1 holes are tight once the fab's tolerance is applied | **rev B** |
| M8 | All silkscreen is 0.12 mm, below the fab minimum of 0.15 mm | **rev B** + **DISP** |
| M9 | The LEDs and ИНС-1 have no polarity marks, and the square pad means opposite things on them | **DISP** |
| M10 | Soldering the strips while mated needs an order and a jig | In the viewer's assembly steps |
| M11 | The display's bottom edge has no support for 184 mm | **open**, optional: a 5th standoff at DISP (97, 40.5) |
| M12 | Tracks run 2.2–2.4 mm from mounting-hole centres, under metal standoffs and screw heads | BOM **fixed**: nylon. Copper keep-outs: **rev B** + **DISP** |
| M13 | BOM gaps: cable crimps, ИН-17 spacers, socket contacts | **fixed** d7aafdc |
| M14 | Standoff length should err long: 11 mm + a 0.5 mm shim | **open**: bench |
| M15 | The saved boards carry unfilled pours, and Gerbers plot the stored fill | Fascia **fixed** a7c3660. DRV/DISP: the fab packages are plotted filled (`fab/`); saving the boards filled is **open**, the owner's decision |

### Fascia, case, product

| ID | Finding | Status |
|---|---|---|
| P1 | The case's right trench wall covered ИН-15А, and its check printed OK | **fixed** a7c3660 |
| P2 | A Ø34.7 mm silkscreen ring off-centre on the fascia's face, running off its edge | **fixed** a7c3660, with the stale ground fill |
| P3 | SW5's body hits the fascia's top-right mounting boss | **open**: the fascia variant decides (below) |
| P4 | The fascia was centred on the board, not on the tubes; its controls sit 0.1–9 mm off the tube centres | Centring **fixed** a7c3660 (X 4.305). Alignment: **open**, the variants |
| P5 | Open slots beside the fascia show TS06-DRV | **open**: the full-width fascia or the frame closes them |
| P6 | A fascia boss lands on R5's pad (−1.2 mm to its courtyard) | The check now FAILs. **open**: variant |
| P7 | The brow top, the base and the left wall can't take their screws; the left screw points at H10's glass | **fixed** 84b9511: M3 inserts in ≥8 mm end blocks, screw lengths on the drawings, no shank within 2.5 mm of glass or a board. The top plate's lip costs 2.5 mm of height: 122.8 mm |
| P8 | The module goes in blind past square-edged sub-millimetre clearances | **fixed** 84b9511: 45° × 3 lead-ins on the soffit, the left wall, and the sill where HL5/HL6 pass. A swept-module collision test is empty |
| P9 | Printed parts set the spacing that precise FR4 hole patterns span | **fixed** 84b9511: the rear panel's holes are slotted ±0.6. The assembly order screws the module first, and the slicer scale is set to +0.4 % |
| P10 | Every pass through SET TIME rewrote the clock and lost the date. "−" never decrements | Rewrite **fixed** d7aafdc. "−" is **open** (a UX decision) |
| P11 | The spec's assembly time and PCB cost no longer describe this build | **open**: re-cost |
| m1–m5 | The rotary modelled at the withdrawn Ø26.94; legends too small (1.5–1.7 mm); the rear panel held only at its corners, with vents over the switch node; the whole top orange | m1, m4, m5 **fixed** 84b9511: Ø25.00 × 22 deep; six rear fixings, with vents over the Nano and none within 5 mm of 185 V; a separate black top plate. m2: **open**, after the fascia variant |

### Red-team of the checks

This agent attacked the verification itself: it planted faults and watched which checks
caught them. It found no blocker. The copper is sound, but several checks said more than they
proved:

| ID | Finding | Status |
|---|---|---|
| R1 | Metal standoffs and case screws sit over signal copper with only solder mask between. K6 and A3 are 0.81 mm from H3's edge, and XA7 0.63 mm from H2's. No check looked | BOM **fixed**: nylon. Keep-outs of r ≥ 3.8 mm as KiCad rule areas: **rev B** + **DISP** |
| R2 | The committed boards store no zone fill. DISP's BL_K exists only as a pour, so Gerbers plotted without a refill leave all nine LEDs open | **Stated** above and in the README. `verify_pair.sh` now fills with KiCad and reports the pieces. The fab export is **built** (`fab/`, `tools/mkfab.sh`: every poured copper Gerber checked for its regions). Committing filled boards: **open**, the owner's decision |
| R3 | "Both boards pass DRC with no errors": DISP's two accepted items are errors, not warnings | **fixed** in this review and the README |
| R4 | `checkpcb.py` read courtyards only from lines and circles. 80 of 103 DRV footprints (drawn as rectangles) had no edge or overlap check, and XP11's 0.17 mm overhang went unseen | **fixed**: rectangles and polygons are read. XP11 is accepted as the mirror of XS11 |
| R5 | `audit.py`'s island count was a grid model, about 7× KiCad's fill on DRV | **fixed**: it counts kept pieces. `verify_pair.sh` reports KiCad's own count |
| R6 | The route does not reproduce: a fresh `--route` stuck at 2 nets sharing (A7, D7). The committed board comes from the saved JSON | **rev B**: deterministic routing, the JSON named as the source. A fresh `--route` reproduced the saved route byte for byte (2aec60c) |
| R7 | DISP's "1.04×" counted a poured net in its floor; like for like it is 1.14× | **DISP**: restated |
| R8 | Cathode clearance: 19 gaps under 0.45 mm on DRV, the least 0.32 mm | **rev B** (E10) |
| R9 | `check_mate()` reads the generators' lists, not the files. It passed a Ø2.5 hole, a moved hole and strips on the wrong faces | **fixed**: `tools/kicad_checks.py mate` reads the written files with pcbnew, and `verify_pair.sh` runs it. Tested: it catches a Ø2.5 hole and a strip moved 2 mm |
| R10 | "checkcopper --hv clean" holds only for the list in `ts06pair.HV_PATTERNS` | The list is now stated in the README |
| R11 | `checkcopper`, `checkpcb` and `audit` silently skipped any footprint whose position carries an angle, which KiCad writes once a part is rotated in the GUI | `checkpcb` and `audit` **fixed** and tested with planted angles. `checkcopper`: **rev B** |
| R12 | Stale text: the 28-pin XP12, 60 strip pins, 95/137 islands, three `no_zone` pads, a 135 mm lead, the case README's 176 mm boards | **fixed** here and in the README; the rest is in the owners' passes |
| R13 | V9/V10 socket contacts missing from the BOM; the DNP bleeders have no `dnp` attribute on the board | BOM **fixed**. The attribute: **rev B** |

## Placement alternatives, scored

The driver board's placement was challenged by layouts built from different concepts, each
routed with the same router settings. Each was scored from its board file, with the same script,
before its author's verdict was read.

**The Nano in the bottom band, USB through the bottom edge** (a local agent; 29.09.26, on the
176 mm board):

| | Baseline (Nano top right) | Nano in the bottom band |
|---|---|---|
| Routing | converged, round 16 | converged, round 13 |
| Vias | 0 | 0 |
| Segments (hand-laid + routed) | 1067 (369 + 698) | 1071 (303 + 768) |
| Signal copper / its floor (MST) | 5608 / 4265 mm = **1.31** | 5129 / 3752 mm = **1.37** |
| Straight (0°/90°) share | **85.6 %** | 81.5 % |
| Ground pour islands, front / back (`audit.py`'s old grid count; KiCad keeps 13 / 14 on the baseline) | 95 / 137 | 72 / 98 |
| KiCad 10 DRC | 0 errors, 0 unconnected | 1 error (a starved thermal, fixable), 0 unconnected |
| Firmware | as is | a new anode table |
| USB | through the right-hand cheek | through the case's base |

**Rejected for this revision.**
* **What it gains:** 12 % off the placement's floor, 8.5 % off the copper, 66 fewer hand-laid
  segments, and fewer ground islands.
* **Why that isn't enough:** it loses on what the brief puts first, a board that does not look
  like a router made it. The Nano's escape is the router's, so the copper runs 1.37× its floor
  instead of 1.31×, a smaller share of it is square, and the tangle round the module is visible
  on both faces.
* **Other costs:** it moves the USB into the base of the case and needs a firmware table change.
* **It stays the fallback.** The widening makes its one hard constraint easier: XS24 and XS23
  move 7.8 mm further apart, so the slot the Nano stands in grows from 27 to about 35 mm.

**Three more concepts** are being tried in separate cloud sessions, on branches
`pcb/drv-alt-swap`, `pcb/drv-alt-search` and `pcb/drv-alt-plane`:
* the bands swapped: logic on top, power at the bottom;
* a placement optimiser;
* an unbroken ground plane on the back face, with parts placed as bridges.

They started before the widening, so they are scored against the 176 mm baseline above. For
comparison, the widened baseline has:
* 1097 segments (369 hand-laid);
* 5936 mm of signal copper on a 4479 mm floor (1.33×);
* 86.1 % square;
* 0 DRC errors.

**Swap, logic on top and power at the bottom** (cloud session, branch `pcb/drv-alt-swap`), scored
from its board file first:

| | Baseline (176 mm) | Swap |
|---|---|---|
| Routing | converged, round 16 | converged, 12-15 rounds |
| Vias | 0 | 0 |
| Segments (hand-laid) | 1067 (369) | 1053 (322) |
| Signal copper / its floor | 5608 / 4265 = 1.31 | 4660 / 3780 = **1.23** |
| Straight share | **85.6 %** | 79.1 % |
| Port A bus | 889 mm, round the board | **98 mm**, eight short diagonals |
| KiCad 10 DRC | 0 errors | 1 error (a starved thermal, fixable), 0 unconnected |
| USB / DC jack | right-hand cheek / left-hand cheek, top | **top face** / right-hand cheek, bottom |

**Not adopted for this revision, but the strongest alternative so far.**
* **What it gains:** it is the shortest layout (17 % less copper), and the expander sits under
  the decoders it drives.
* **What it costs:**
  * its router-drawn lines are less square than the baseline's buses;
  * the "m" LED's line laps the board (198 mm);
  * the fascia's four lines run 110 mm down the middle to J1;
  * the USB moves to the top of the case.
* **Porting it** to the 191.4 mm row would be a new placement.
* **The choice:** it is a matter of taste. The owner can have it instead, at the cost of one
  more re-placement and route.

### "Plane": an unbroken ground plane on the back, parts as bridges (rejected)

A cloud session on the 176 mm geometry, on branch `pcb/drv-alt-plane` (15b576f). Its board
file was scored here with `scorecard.py`: 2565 segments, 0 vias, 5673 mm of copper (4776 mm
front, 897 mm back), 88.7 % axis-aligned, a 3935 mm floor (ratio 1.44), and 3 DIP
orientations. That matches its own `REPORT.md`, whose DRC and island figures are below.

| | plane | baseline |
|---|---|---|
| Converged | **no**: 69 nets still sharing after 10 rounds; stalled at 23–54 in other runs | yes |
| KiCad DRC | 24 clearance, 95 tracks crossing, 9 shorts, 1 unconnected | 0 errors |
| Back-face GND | **21 islands, the largest holding 98.7 %**, reaching 55 of 56 ground pads | 139 islands, the largest 64 % |
| Signal copper on the back | 897 mm, in "hop windows" chained up to 71 mm | a two-layer design |

**Rejected.** The collisions are structural, so more rounds would not fix them, and the
geometry is stale. Two things are worth keeping:
* **The bridge row:** series resistors laid under the Nano's digital row, so the analogue
  lines cross between their pads.
* **The plane checker,** `tools/planecheck.py` on that branch.

If a future revision wants a real ground plane, that is where to start.

### "Search": an annealing placement optimiser (rejected as a layout, kept as a method)

A cloud session on the 176 mm geometry, branch `pcb/drv-alt-search` (0eeeba7). It was archived
on 30.09 at about 01:20 UTC to save quota, after it had pushed its result and report. Its board
file was scored here before the report was read:

| | search (cand_11fr) | baseline (176 mm, same method) |
|---|---|---|
| Converged | yes, round 37; 0 unconnected | yes |
| Hand-laid segments | **0** | 369 |
| Segments / vias | 1236 / 0 | 1067 / 0 |
| MST floor | **3617 mm** (15 % lower) | 4265 mm |
| Signal copper / floor | 1.32 | 1.31 |
| Straight share | 77.7 % | 85.6 % |
| DIP pin-1 orientations | 4 | 3 |
| KiCad DRC errors | **23**: 14 holes inside another part's courtyard, 7 starved thermals, 2 courtyard overlaps | 0 |

**Rejected as a layout:**
* its placement is not legal (the 23 DRC errors);
* it uses all four chip orientations;
* 185 V and logic are not separated: HV185 runs about 100 mm along the top edge;
* the jack moves to the bottom edge;
* it is drawn on the stale 176 mm outline.

**Kept as a method.** It shows that the baseline's hand-laid buses come from its placement,
not from the circuit. An optimiser placement cuts the floor by 15 % and routes with no hand
copper at all. With a cost that also prices orientations, HV separation and edge connectors,
`tools/placesearch.py` on that branch is a good seed for a future revision.

## What is still open before an order

| Item | Blocks | How |
|---|---|---|
| Gate 3, ИН-17 lead order | anode identity only (cathodes are a table) | bench rig, one lead at a time |
| Gate 4, ИН-15 pinouts | anode identity only | same rig |
| Gate 5, ИН-17 pip projection | the tube's standing height | calipers on a real tube |
| Gate 6, RTC module pin order | U13's socket order | meter the module |
| PBS + PLS heights | the standoff length | calipers, finding 1 |
| Colon vs M10 courtyard | nothing electrical | test fit |
| Rev B's OV clamp trip voltage | the 185 V rail's protection without U12 | bench: U12 out, RP1 at either end, a current-limited 12 V supply; the 225-270 V window is computed, not measured |
| U11's orientation (rev B stands it at 0°) | nothing electrical; one more socket direction at assembly | the owner's choice; turning it back means routing again |
| ~~ИН-17 pair spacing: 13.0, needs 20.5~~ | fixed: boards widened to 191.4, the pair at 20.5 | gate 5 confirms the Ø20 stem |
| The fascia under the 191.4 mm tube row | the fascia's board and the case bosses | four variants built and scored in `PCB/TS06-FASCIA-variants.md` (recommended: R, the controls on the tube grid): the owner's call |
| **Rev C (owner, 30.09):** the expander under the decoders | nothing: copper length only | Swap moved U3 under the decoders and cut the port-A bus from 889 to 98 mm; four alternatives agree the placement leaves 10–15 % of the floor. Do it after rev B is verified, with a placement sweep scored on the floor **and** buildability gates (DRC-legal placement, ≤3 orientations, HV separated, connectors at their edges), routing only the best one or two |
| Firmware: 6-slot timing | ghosting, flicker, brightness | bench, first pair |
| ~~Firmware: `rtc.adjust()` on every boot~~, stale `.hex` | every board type | the RTC writes are fixed; rebuild the `.hex` for the board you flash (finding 8) |

## The case

What follows is written for a case not yet drawn, from the boards as they now stand.
World coordinates are the FreeCAD assembly's: X across the front from the clock's left,
Y up.

### The envelope

* **Width:** the boards are 191.4 mm. With 0.5 mm clearance each side and 6 mm cheeks, the
  outside is 204.4 mm: concept Rev F's face width (204.3).
* **Height:** TS06-DRV spans world Y 4 to 104, 26 mm above the display board and 30 mm below
  it. The case model puts the inside at **114.3 mm**. The extra 8 mm is the floor: the fascia's
  own connector is side-entry, so its cable leaves towards the floor and the floor sits
  7.3 mm below the assembly's Y 0. An 8 mm trough in the base would win that back.
* **Depth**, from the tube glass to the rearmost part:

  | Layer | Depth |
  |---|---|
  | Glass front to the display board's front face (socketed ИН-12) | ≈ 30 mm |
  | TS06-DISP | 1.6 mm |
  | The stack gap | 11 mm |
  | TS06-DRV | 1.6 mm |
  | The tallest part (finding 6) | 15–22 mm |
  | **Total** | **≈ 59–66 mm** |

  With 5 mm of air in front of the rear panel, the inside is about 64–71 mm deep. The case
  model made it 71.2 mm, from glass front to rear panel, and 204.4 W × 120.3 H × 83.6 D mm
  outside for rev A. With rev B and the case fixes it is 69.2 mm and **204.4 W × 122.8 H ×
  81.6 D mm** (`3d/case-pair/checks.md`). That is 20–28 mm deeper than Rev F's 44 mm cheek.
  The two-board stack costs that depth, and it should be drawn in from the start rather than
  found later.

The model is in `3d/case-pair/`: an OpenSCAD model, 1:1 drawings, STL parts and an
interference check against every board. `checks.md` there lists each check and where every
dimension comes from.

### Suggestions

1. **Keep Rev F's "cheeks and boards" idea: nothing moulded but the cheeks.**
   * Two cheeks, printed or cut from plywood or aluminium, carry the whole electronics
     stack. Four screws hold it: TS06-DRV's corner holes H6 and H8 on the left cheek
     (world X 3.5; Y 7.5 and 81.5), and H5 and H7 on the right (world X 187.9; Y 7.5 and
     100.5). Put bosses or a small aluminium angle on each cheek's inner face.
   * The display rides on the driver board through its four standoffs, so the pair lifts
     out as one module.
2. **Make the rear panel a board.** It closes the high-voltage side (finding 4), and a bare
   1.6 mm FR4 blank in black mask with white silkscreen costs almost nothing added to the
   same order. It matches the fascia and can carry:
   * the label: 12 V, polarity, the high-voltage mark, "unplug and wait 15 s";
   * vent slots no wider than 2.5 mm above the converter (world X 100–130, Y 85–100).

   Hold it with four screws into the cheeks.
3. **Watch the connector openings: the cheek's thickness eats the plug.**
   * **DC jack:** its mouth is 0.3 mm inside the right-hand end of the board (world X 191.4,
     Y ≈ 91.5).
     * A plain 6 mm cheek leaves a 5.5 × 2.1 plug only 2.7 mm of engagement.
     * A pocket from the inside does not help: the plug still stops at the outer face.
     * **Counterbore the cheek from the OUTSIDE**, leaving a 1.5 mm web. The case model then
       gives 7.2 mm of engagement.
   * **USB (the Nano's mini-B):** the receptacle ends 1.9 mm inside the cheek (world X ≈ −2.4,
     Y ≈ 94). The cheek needs a slot about 12 × 9 mm so the plug's overmould can pass. **Open
     the slot to the cheek's rear edge.** A closed window would stop the module from lifting
     out.
   * Alternatively, move both to the rear panel, but that means a panel jack and a USB
     extension. The board-mounted parts are simpler.
4. **Brow and trench.**
   * The brow must hide the display board's top 4 mm (the XP12 joints) and the whole top
     band of TS06-DRV behind it.
   * The trench's left wall must hide XP11 (the left 3 mm).
   * Keep the spec's trench coupon test: one socketed ИН-12 at full rake, before printing
     the chassis.
5. **Fascia.**
   * Tie the fascia to the cheeks, not to the stack.
   * Check its registration: the FreeCAD assembly has it about 7 mm off the stack in X.
     Decide which is right before either is cut.
   * J1 on TS06-DRV is a top-entry PH on the display-facing side, at world X 44–54, Y 9.
     The cable leaves it straight forward, towards the fascia.
   * The fascia's own connector is side-entry, near world X 152, so its cable turns down to
     the floor. The path is 139 mm with the fascia centred on the tube row. **Make the PHR-6
     lead 180–200 mm** so the module can be lifted out. At 150 mm the slack is 11 mm.
   * The model also shows where the fascia is tight:
     * its top-right screw hole is 1.2–2.6 mm from SW5's КМД1 body;
     * a mounting boss comes within 0.4 mm of R5;
     * the rotary's rim is 0.5 mm below the fascia's top edge, so the sill has to step back
       over it.
6. **Heat is not a problem.** The clock draws about 5 W (0.43 A at 12 V; electrical review E14), most of it in the tubes and the converter. Slots at
   the top of the rear panel are enough; no fan and no heatsink on VT21 (it switches, it
   does not dissipate).
7. **Service.**
   1. Unplug, wait 15 s, remove the rear panel.
   2. Remove the four module screws; the stack lifts out.
   3. The display pulls straight off the driver board. Pull at both ends evenly, not one
      end first, or the long XP12 strip twists the tube pins.
   4. Every chip is socketed and the Nano is on strips, so a repair is a swap.
