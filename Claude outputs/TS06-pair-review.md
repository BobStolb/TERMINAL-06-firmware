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

Both boards pass KiCad 10's DRC with no errors and nothing unconnected (see `PCB/README.md`,
"Checked"). An independent audit traced every anode and every digit through both boards
and the firmware.

**One finding blocked an order, and it was mechanical:** the two ИН-17 were placed 13 mm apart,
where their Ø20 stems need 20.5. It came from the tube coordinates every board so far had used.
**It is fixed.** The owner chose to widen the boards to 191.4 mm and keep the Gyver pitch.
Both boards were then re-placed, re-routed and re-verified (next section).

Everything that could still go wrong is mechanical, and none of it needs new copper:
* the stack height;
* the order in which the strips are soldered;
* a few tall parts;
* the case openings for the two connectors.

Those need an assembly note, a test fit, and the case drawn around the right numbers.

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

### 5. Three chip orientations on one board

On TS06-DRV, U15, U16, U17 and RN1 have pin 1 to the left. U3 and the six optos (U5–U10)
have it to the right. U2, U11 and U12 have it at the bottom. Each orientation is what made the zero-via
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

**Two older problems the audit found, which affect every board type:**
* **The RTC is reset to the build time on every boot.** `setup()` calls `rtc.adjust()`
  unconditionally, so a power cut loses the time. It should only run when the RTC reports
  it lost power.
* **The committed `nixieClock_TS06.hex` is stale.** It is a BOARD_TYPE 1 build of the
  first commit, not what the source builds today. Rebuild it before anyone flashes it.

Neither was changed here, because both alter what the owner's bench clock does today.

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
* **The I²C lines run ≈ 140 mm** from the Nano to the expander, with the RTC on the way.
  At 100 kHz with 4.7 kΩ pull-ups, that is well inside the bus's capacitance budget.
* **TS06-DRV's ground pours are in pieces.**
  * The ground is a routed tree: every GND pad is joined by track. The pours on both faces
    only add area around it.
  * Between the hand-laid buses, the pours break into many islands: `audit.py` counts 95 on
    the front and 137 on the back. Each touches a ground pad, since KiCad removes those that
    do not.
  * Three pads whose back-face pour was only a sliver keep out of the pours, which is what
    cleared KiCad's "starved thermal" errors.
  * It works, but it is not a ground plane. The "plane" alternative layout (below) tests
    whether a placement built around an unbroken back-face ground can do better.
* **The case model's tight spots:**
  * the trench's left wall is 0.475 mm from H10's glass;
  * the sill is 0.59 mm from the ИН-17 LEDs.

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
| Ground pour islands, front / back | 95 / 137 | 72 / 98 |
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

## What is still open before an order

| Item | Blocks | How |
|---|---|---|
| Gate 3, ИН-17 lead order | anode identity only (cathodes are a table) | bench rig, one lead at a time |
| Gate 4, ИН-15 pinouts | anode identity only | same rig |
| Gate 5, ИН-17 pip projection | the tube's standing height | calipers on a real tube |
| Gate 6, RTC module pin order | U13's socket order | meter the module |
| PBS + PLS heights | the standoff length | calipers, finding 1 |
| Colon vs M10 courtyard | nothing electrical | test fit |
| ~~ИН-17 pair spacing: 13.0, needs 20.5~~ | fixed: boards widened to 191.4, the pair at 20.5 | gate 5 confirms the Ø20 stem |
| The fascia (176 mm) under a 191.4 mm tube row | the fascia's position only | centre it, or widen the fascia to match: the owner's call |
| Firmware: 6-slot timing | ghosting, flicker, brightness | bench, first pair |
| Firmware: `rtc.adjust()` on every boot, stale `.hex` | every board type | a one-line fix and a rebuild (finding 8) |

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
  model makes it 71.2 mm, from glass front to rear panel, and **204.4 W × 120.3 H × 83.6 D
  mm** outside. That is 20–28 mm deeper than Rev F's 44 mm cheek. The two-board stack costs
  that depth, and it should be drawn in from the start rather than found later.

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
     the floor. The path is 135 mm. **Make the PHR-6 lead 180–200 mm** so the module can be
     lifted out. At 150 mm the slack is 15 mm.
   * The model also shows where the fascia is tight:
     * its top-right screw hole is 1.2–2.6 mm from SW5's КМД1 body;
     * a mounting boss comes within 0.4 mm of R5;
     * the rotary's rim is 0.5 mm below the fascia's top edge, so the sill has to step back
       over it.
6. **Heat is not a problem.** The clock draws about 3.5 W, most of it in the tubes. Slots at
   the top of the rear panel are enough; no fan and no heatsink on VT21 (it switches, it
   does not dissipate).
7. **Service.**
   1. Unplug, wait 15 s, remove the rear panel.
   2. Remove the four module screws; the stack lifts out.
   3. The display pulls straight off the driver board. Pull at both ends evenly, not one
      end first, or the long XP12 strip twists the tube pins.
   4. Every chip is socketed and the Nano is on strips, so a repair is a swap.
