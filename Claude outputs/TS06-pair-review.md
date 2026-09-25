# TS06-DISP + TS06-DRV: design review, and what it means for the case

A critical pass over the through-hole pair: what it gets right, what is weak, what was fixed
on the way, and what is still open before an order. The last part turns the stack's geometry
into suggestions for the case, which has not been started.

## Verdict

The pair meets the brief: through-hole only, no vias on either board, a display board that
carries nothing but the tubes, and two boards that plug together with no harness. Most of
what could still go wrong is **mechanical, not electrical**: the stack height, the order in
which the strips are soldered, a few tall parts, and the case openings for the two
connectors. None of these needs new copper. They need an assembly note, a test fit and the
case drawn around the right numbers.

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
    the "m" LED, one anode) end in four standing resistors at its exit;
  * the minutes' and S10's anode resistors stand under the Nano;
  * the I²C pull-ups and the fascia's ladder filters sit just above the LED ribbon, where
    those lines must cross it.

  No wire links and no zero-ohm jumpers.
* **On the driver board, the long buses are drawn too.** Port A of the expander runs up the
  left edge as one eight-line bus. The LED ribbon runs in lanes under the bottom strips. The
  U17 branch of A0–A3 drops down a corridor beside the Nano and enters U17 between its rows,
  the one approach that lands every line on its own pin without a crossing. The router fills
  in the rest: the Nano's digital row, the I²C pair, the rails and the wiring inside each
  cell.

## Findings, most serious first

### 1. The 11 mm stack is a sum of two catalogue numbers: check it against the parts in hand

The boards are 11 mm apart because a standard PBS socket is 8.5 mm tall and a PLS header's
plastic body is 2.5 mm. Both vary between makers (PBS runs 7.0–8.5 mm). An 11 mm M3 standoff
exists but is uncommon: a 10 mm standoff plus a 1 mm washer does the same job.
**Before ordering, measure one PBS and one PLS from the batch you will buy, and set the
standoffs from that.** If they disagree with 11 mm, the strips either do not seat or they
bend the display board over its four standoffs.

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
the left 3 mm. The four standoff screws also land on that face, between the tubes: use
black countersunk or low-head screws.

### 4. 185 V is on the driver board's rear-facing side, and C7 stays charged

TS06-DRV's component face looks at the back of the case. It carries C7 (4.7 µF at 185 V,
about 0.08 J and 0.9 mC, above the usual touch-safe limits), the switch's TO-220 tab (the SW
node, up to about 190 V), the six optos, and every anode and ballast resistor. The bleeder
(R60 + R61, 940 kΩ) and the feedback divider (1.52 MΩ) take C7 down with a time constant of
about 2.7 s, so it is safe after about 15 s, not immediately.

**The rear of the case must be a closed panel held by screws.** Its vent slots should be
no wider than 2.5 mm, and it needs a high-voltage mark. The service note should read:
"unplug, wait 15 s".

### 5. Four chip orientations on one board

On TS06-DRV, U15, U16, U17 and RN1 have pin 1 to the left. U3 and the six optos have it to
the right. U2, U11 and U12 have it at the bottom. Each orientation is what made the zero-via
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
| U1, Nano on PBS-15 sockets | ≈ 15 mm | no, it stays removable |
| L1, radial 220 µH | ≈ 12–14 mm | no |

Laying down the module and the capacitor, and the switch if its footprint is redrawn,
saves up to 7 mm of case depth. The Nano then sets the height.

### 7. Header neighbours: 5 V next to 185 V at the minimum spacing

On XS21 and XS23–XS25, backlight lines (5 V) sit beside anode pins (185 V). At 2.54 mm pitch
with 1.7 mm pads, the gap is 0.84 mm against IPC-2221B's 0.8 mm for uncoated component leads.
It passes, but only just. A solder bridge there puts 185 V into the MCP23017's port B.
**Inspect those four strips under a loupe before power-up.**

### 8. The firmware must be told which board it is on

The pair needs `BOARD_TYPE 4`, which is in the firmware but not the default (0). That type
carries three things of the pair's own:
* its digit map;
* its anode order: hours on D6/D5, minutes on D4/D3, S10 on D2, S1 on D13. This is the order
  types 1 and 2 already use, and it is what lets the Nano's digital row fan out without
  crossing itself;
* a note that the fascia's rotary ladder reaches the Nano's A7 and the levers A6. The spec
  has them the other way round, but no firmware reads either yet. Whoever writes the fascia
  code must read the rotary on A7 when `BOARD_TYPE` is 4.

A clock built with these boards and flashed with the default shows scrambled digits. For a batch,
either change the default on a pair branch or put it at the top of the build sheet. As
cheap insurance for gates 3 and 4, give the firmware a per-slot digit table for the two
ИН-17 slots and the ИН-15 codes. Then a surprise at the bench is fixed by editing a table,
with no code to rewrite.

### 9. Smaller points

* **The colon lamps' courtyards overlap the M10 tube's by 0.3 mm** at their measured
  positions. This is inherited from TS06-MAIN and needs a check with a real tube.
* **A hole courtyard (H3, above the colon) runs 0.15 mm past the display board's top
  edge.** Harmless.
* **Decoupling:** each decoder has its 100 nF on the 5 V rail, but not tight against its
  pins, where the port-A bus runs. For static TTL decoders this is fine. The MCP23017, the
  comparator and the driver have theirs close.
* **The I²C lines run ≈ 140 mm** from the Nano to the expander, with the RTC on the way.
  At 100 kHz with 4.7 kΩ pull-ups, that is well inside the bus's capacitance budget.

## What is still open before an order

| Item | Blocks | How |
|---|---|---|
| Gate 3, ИН-17 lead order | anode identity only (cathodes are a table) | bench rig, one lead at a time |
| Gate 4, ИН-15 pinouts | anode identity only | same rig |
| Gate 5, ИН-17 pip projection | the tube's standing height | calipers on a real tube |
| Gate 6, RTC module pin order | U13's socket order | meter the module |
| PBS + PLS heights | the standoff length | calipers, finding 1 |
| Colon vs M10 courtyard | nothing electrical | test fit |

## The case

What follows is written for a case not yet drawn, from the boards as they now stand.
World coordinates are the FreeCAD assembly's: X across the front from the clock's left,
Y up.

### The envelope

* **Width:** the boards are 176 mm. With 0.5 mm clearance each side and 6 mm cheeks, the
  outside is about 189 mm.
* **Height:** TS06-DRV spans world Y 4 to 104, 26 mm above the display board and 30 mm below
  it. With a base and 3 mm of top clearance, the inside needs about 106 mm.
* **Depth**, from the tube glass to the rearmost part:

  | Layer | Depth |
  |---|---|
  | Glass front to the display board's front face (socketed ИН-12) | ≈ 30 mm |
  | TS06-DISP | 1.6 mm |
  | The stack gap | 11 mm |
  | TS06-DRV | 1.6 mm |
  | The tallest part (finding 6) | 15–22 mm |
  | **Total** | **≈ 60–66 mm** |

  With 5 mm of air in front of the rear panel, the inside is about 65–72 mm deep. That is
  20–28 mm deeper than Rev F's 44 mm cheek. The two-board stack costs that depth, and it
  should be drawn in from the start rather than found later.

### Suggestions

1. **Keep Rev F's "cheeks and boards" idea: nothing moulded but the cheeks.**
   * Two cheeks, printed or cut from plywood or aluminium, carry the whole electronics
     stack. Four screws hold it: TS06-DRV's corner holes H6 and H8 on the left cheek
     (world X 3.5; Y 7.5 and 81.5), and H5 and H7 on the right (world X 172.5; Y 7.5 and
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
   * **DC jack:** its mouth is flush with the right-hand end of the board (world X 176,
     Y ≈ 91.5). A 6 mm cheek leaves a 5.5 × 2.1 plug with only 3–4 mm of engagement. Thin
     the cheek to 1.5–2 mm around the jack: a Ø 14 pocket from inside, a Ø 9 hole through.
   * **USB (the Nano's mini-B):** it stands 2.4 mm proud of the left end (world X ≈ −2.4,
     Y ≈ 94). The cheek needs a slot about 12 × 9 mm so the plug's overmould can pass.
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
     The cable leaves it straight forward, towards the fascia. The fascia's own connector sits
     near world X 152, so the lead runs about 100 mm along the case floor. A 150 mm PHR-6
     lead, made up once, leaves slack for lifting the module out.
6. **Heat is not a problem.** The clock draws about 3.5 W, most of it in the tubes. Slots at
   the top of the rear panel are enough; no fan and no heatsink on VT21 (it switches, it
   does not dissipate).
7. **Service.**
   1. Unplug, wait 15 s, remove the rear panel.
   2. Remove the four module screws; the stack lifts out.
   3. The display pulls straight off the driver board. Pull at both ends evenly, not one
      end first, or the long XP12 strip twists the tube pins.
   4. Every chip is socketed and the Nano is on strips, so a repair is a swap.
