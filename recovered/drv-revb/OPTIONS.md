# TS06-DRV rev B: the routing stall round J1, and the way out

30.09.26, before the next route. Coordinates are the driver board's frame (mm).

## What stalls, and why
* Run r1 held **A6 A7 D7 D8 SCL** from round 15 to round 45 while the sharing price rose from 263
  to 5 × 10⁷. A price that high moves any net that has another path. These nets had none: the
  block is **hard, not congestion**.
* Rev A converged with J1 in the same place (round 15). Its back-face bundle came down the corridor
  between the colon's ballast R58 and the hours' cell, and turned west into J1 at y 92-94.
* Rev B added five parts to the net group (R72 1 M on A6; R73, R74 1 k and C18, C19 10 nF on D7
  and D8). `near()` put them in a fence 2-15 mm north of J1, at x 138-152 and y 77-93, which is
  exactly where that bundle turns. R73 and R74 lie north-south across the funnel. C18 sits in
  front of J1's A6 and A7 pins.
* The LED ribbon's BL_A1 and BL_A2 run on the front face at y 69-71, from x 27 to 176. So every
  line from the column or the gap to J1 crosses the strip band on the back face. Only the last
  20 mm before J1 has both faces free.

**Rubber-band count** (`scratch/funnel.py`, `funnel2.py`): each net's straight lines from where it
enters (the column, the gap) through its pads to J1 and U13.

| Placement | Crossings between nets | RC pads lying on another net's line |
|---|---|---|
| Predecessor (`near()` at J1) | A7 × D7_J twice, SCL × SDA | 3: R73.1 (D7) and C18.1 (D7_J) on A7's; R72.1 (A6) on J1's ground |
| Option 3 below | SCL × SDA only | 0 |

SCL × SDA is common to both, and U13 already resolves it: the two lines change face at their
pull-ups in the column.

## Options

| # | Option | What it costs | What it buys |
|---|---|---|---|
| 1 | **The D7/D8 RC and the A6 pull-down next to the Nano** (filtering at the MCU input, which is equally valid) | The gap below the Nano is 3.7 mm between U5's 185 V pin (0.8 mm rule) and C4. It holds exactly D7, D8 and D11, so the parts must go under the module, among the hand-laid digital fan. That means re-laying hand copper (lanes at 0.65 mm pitch), the riskiest kind of change. D7_J and D8_J still run the full 50 mm to J1, so the funnel keeps its 6 lines. There is no room for R72 in the column: R58's 185 V pad and the 0.8 mm rule. | 3 ground pads leave the funnel |
| 2 | **Move J1 along the bottom edge** (east, under the corridor) | J1's position is the fascia's and the case's: the fascia variants (`PCB/TS06-FASCIA-variants.md`) and `3d/case-pair` place the cable from it, and this mission owns neither. +5V and GND grow by the same distance towards U13 | Shorter A6, A7, D7 and D8, but the RC fence would still need placing |
| 3 | **Re-place the congested block by hand** (the RC parts on their own nets' paths) | 5 part positions in `mkpcb_drv.py`. No hand copper, no netlist change. The notes say "at J1", and the parts stay within 30 mm of it, on the cable side of the MCU | R73 and R74 lie east-west on D7's and D8's own descent, east of the A6/A7 funnel: D7 and D8 in from the east, D7_J and D8_J out to the west, C18 and C19 beside those west pads. R72 lies north-south west of the A6 line beside J1's GND pin. The funnel is as open as rev A's |
| 4 | **Give SCL another path** | SCL runs west from the column to U13 over the colon's bodies. It shared in both runs, but always with the J1 nets, and its band crosses nothing but SDA. Hand-laying it fixes a symptom | Held as the fallback if option 3 leaves SCL alone |

## Choice: option 3
**The evidence:**
* The stall is hard (r1's price), so it needs a changed placement, not more rounds or a new order.
* The only placement change between rev A (converged) and rev B inside the funnel is the RC fence.
* Option 3 takes the funnel from 2 forced crossings and 3 pads on other nets' lines to 0 and 0,
  with no change outside `mkpcb_drv.py`'s placement.
* Options 1 and 2 cost hand copper or another owner's geometry, for less.

**Fallbacks:** if option 3 stalls on SCL alone, try option 4. If it stalls in the funnel, the RC
block goes further east (x 160-175 has room to H6's keep-out at x 184).

**The router is not deterministic by itself.** `mkpcb_drv.py --route` re-executes itself with
**PYTHONHASHSEED=0**: the hash seed is pinned. The sets are not sorted. Every run here is launched
with the seed set explicitly.

## Result (added after the route)

| Run | Placement | Round 10 | Outcome |
|---|---|---|---|
| r1, r2 (predecessor) | `near()` at J1 | 9-11 nets, A6 A7 D7 D8 SCL among them | stalled: 5 nets (r1, round 45), 4 nets (r2, round 15) |
| **r3** | option 3, as above | 8 nets, **none of them at J1** | **round 13: 0 nets sharing, 0 unrouted**; polished, 30 nets shorter |
| r4 (hedge) | option 3, R73/R74 standing in line on the gap's descent | - | stopped at round 8 (9 nets, SDA among them) once r3 converged |

Both runs used PYTHONHASHSEED=0. The committed route is r3's (`tools/mkpcb_drv_routes.json`).
The board is written from it: check() 0, check_mate() `[]`, 0 cathode pads under 0.5 mm, KiCad
DRC 0 errors. Option 4 was not needed.
