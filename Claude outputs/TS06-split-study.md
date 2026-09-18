# Splitting TS06-MAIN in two, the way the AlexGyver board is split

**The short answer: 18 wires.** A display board carrying the tubes and everything that drives
them, a driver board carrying the Nano, the RTC, the converter, the switches and the power
inlet, and a single 2×10 ribbon between them. That is a better interface than most two-board
clocks manage, and it is arrived at by measurement rather than by taste.

## Why this was worth asking

The inherited board is two: a **driver half** (Nano, К155ИД1, RTC, the three switches, the
converter, power in) and a **tube half** (four sockets, the pip holes, HL1–HL4), joined by the
P1/P3 headers. TS06-MAIN collapses all of that onto one 176 × 96 mm board, and the routing
study has been showing what that costs — 140 nets fighting for two layers, a ground pour that
fills as hundreds of islands, and a through-hole build that will not route as placed at all.

So: is the inherited split a lesson rather than a limitation?

## How the seam was found

Not by guessing. The tubes and the backlight LEDs are fixed to the display board, because they
are what the fascia holds. Every other part is then moved across one at a time, always choosing
whichever part leaves the fewest nets crossing — **including when that is worse than leaving it
where it is**, because the interesting moves are the ones that only pay off as a group. A
driver and the loads it drives have to travel together or not at all, and a method that only
takes improving steps cannot see that.

The result is a curve of wires-crossing against display-board size, and its knees are the
natural seams.

## The curve

| display parts | driver parts | wires cross | what just moved across |
|---:|---:|---:|---|
| 19 | 129 | 50 | the tubes and the backlight alone |
| 20 | 128 | **45** | the К155ИД1 — ten cathode lines out, four BCD lines in |
| 28 | 120 | **37** | the eight backlight resistors |
| 40 | 108 | **34** | the colon resistors |
| 41–82 | | 34 → 18 | *the plateau* — see below |
| **83** | **65** | **18** | both expanders, all 18 ИН-15 cathode transistors and their base resistors |
| 91 | 57 | 16 | the Nano and the power jack, i.e. no longer really a split |

Two things are worth reading off it.

**The К155ИД1 should go on the display board, and that is nearly free.** One part moved, five
wires saved: its ten cathode lines K0…K9 stop crossing and are replaced by four BCD inputs.
This is the "move the driver to its loads" rule, and it pays immediately.

**The long flat stretch from 41 to 82 parts is the interesting part.** Each ИН-15 cathode runs
from the tube to exactly one transistor, so moving a transistor across just swaps a `CAT_*` net
for a `B*` base net — no gain. Moving its base resistor swaps that for an expander output — no
gain. The eighteen only collapse when **U3 and U4 themselves** cross, at which point eighteen
nets become SDA and SCL. Forty-one parts have to move together before a single wire is saved.
A greedy search that refuses to go uphill stops dead at 37 and never finds this.

## The interface at the seam

18 conductors:

| | |
|---|---|
| power | `+5V`, `GND`, `HV185` |
| ИН-12 digit select | `A0` `A1` `A2` `A3` — BCD into the К155ИД1 |
| ИН-12 anode drive | `ANODE_H1` `ANODE_H10` `ANODE_M1` `ANODE_M10` `ANODE_S1` `ANODE_S10` |
| ИН-15 and colon | `SDA`, `SCL` |
| backlight | `BL_K` |
| spare Nano pins | `D10`, `D12` |

**Driver board keeps:** the Nano, the DS3231, the boost converter (L1, VD1, VD2, the TC4420,
the comparator, the divider), the anode driver transistors U5–U10, the switches, the power
jack and the fuse. 65 parts.

**Display board keeps:** all ten tubes, the nine backlight LEDs, the К155ИД1, both MCP23017
expanders, the 18 ИН-15 cathode transistors with their base resistors, and the backlight and
colon resistors. 83 parts.

Seven of the eighteen conductors sit at 185 V — `HV185` and the six anodes. On a 2.54 mm
connector that is not a clearance problem (IPC-2221B asks 0.8 mm between bare terminations at
this voltage, and 2.54 mm is three times that), but it does argue for a **keyed** connector
rather than a plain ribbon header, because inserting it reversed would put 185 V on `+5V`.

## What this would actually buy

The honest case for it:

- **Two easy routing problems instead of one hard one.** The driver board has no tube sockets
  on it at all — no 12-pin rings with 0.6 mm halos carving up the middle of the board. The
  display board is 83 parts of which most are a transistor and a resistor sitting directly
  beside the tube they drive, which is close to the easiest routing problem there is.
- **A real ground plane on each.** The pour fragmentation measured all session is a consequence
  of 140 nets on two layers. Split, each board carries far fewer and the pour has room to stay
  in one piece.
- **The through-hole build might become routable.** It currently fails on placement, with 13
  split nets and 50 pads inside another part's courtyard. Halving the congestion is the most
  plausible route to fixing that without a hand placement pass.
- **The fascia stays free to change.** The owner has said the tube positions are settled and
  the fascia is not; a display board that carries only the tubes and their drivers is the piece
  that has to track the fascia, and it would no longer drag the Nano and the converter with it.
- **Panelising the two costs nothing extra** at Rezonit if they fit the same panel, so the fab
  price is roughly unchanged.

The honest case against:

- **A connector is a new failure mode**, and this one carries 185 V.
- **Two boards need two sets of mounting**, and the mechanical design is currently one plate.
- **It is a redesign, not an edit.** The netlist is unchanged but the placement, both outlines,
  both schematics and the 3D assembly all move.

## What I would not conclude from this

That the single board cannot be made to work. The surface-mount build is one net short of
complete and the routing rules being tested today are still improving it. The split is worth
considering on its own merits — a cleaner ground, an easier through-hole build, a fascia that
can change independently — and not as a rescue.

## Reproducing

```bash
python tools/boardsplit.py PCB/TS06-MAIN/TS06-MAIN.kicad_pcb --at 83
```

It reads the placed board rather than the netlist, so it stays true as long as the board does,
and `--fascia` takes a different reference pattern if what has to sit on the display side ever
changes.
