# What makes a two-layer board route well: ten rules, twenty-two configurations, measured

The record of a day spent finding out why TS06-MAIN routed badly, what fixed it, which of my own
ideas were wrong, and what turned out not to be a routing problem at all.

## How it started

The board passed everything. `audit.py` found two things, `checkcopper.py --hv` one,
`checkmatch.py` agreed, KiCad's own DRC with `--refill-zones --severity-all` was quiet. It was
nevertheless badly routed, and what caught it was the owner opening the 3D view and saying so.

One glance beat six hours of passing tests, because **every test asked whether the copper was
legal and none asked whether it was any good.**

Measured afterwards, the board that passed carried 476 vias, had no grain at all — 33 % of the
front running east-west against 25 % across it, which is what routing at random looks like — and
its ground pour filled as 292 islands.

## The instruments, before any rules

Nothing could be fixed while the only gauge read "0 nets unrouted".

- **`tools/audit.py` grew a QUALITY section.** Copper length; detour against the Euclidean MST of
  each net's own pads; vias per net; the angle mix; how much of each face runs along its grain;
  islands per pour and what fraction of the copper the largest one holds. It sets no exit code —
  no threshold is right for both a nine-net fascia and this board — because what they share is
  being *looked at*.
- **`tools/plotcu.py` draws the copper alone**, a panel per face, coloured by what each net
  carries. `render.py` draws the board as a customer sees it, which is right for a fascia and
  useless for a route: under a black mask every track looks the same.

## The results

All runs surface-mount, 148 parts, 141 nets, `tighten 2` unless noted. "splits" is nets left in
more than one piece; "islands" and "largest" are the ground pour on each face.

| run | what it changes | splits | vias | copper | detour | grain F | islands | largest |
|---|---|---:|---:|---:|---:|---|---|---|
| shipped | a via priced at 2.5 mm, nothing else | 1 | 476 | 8575 | 1.23× | 33/25 | 292/287 | 58/62 |
| baseline | a via at 15 mm, price opening at 3 | 6 | 329 | 8390 | 1.28× | 37/21 | 250/233 | 54/72 |
| A | grain 8, via 9 mm | 3 | **308** | **8281** | 1.25× | 50/8 | 269/242 | 68/55 |
| B | grain 14, via 6 mm | 4 | 363 | 9099 | 1.30× | **64/4** | 307/244 | 80/48 |
| C | **no grain — the control** | 3 | 348 | 8620 | 1.23× | 34/24 | **365/296** | 54/60 |
| D | grain 8 + relax + infrastructure exempt | 2 | 356 | 8647 | 1.23× | 48/12 | 282/240 | 74/61 |
| E | D, grain 14 | 3 | 350 | 8662 | 1.27× | 55/6 | 272/245 | 65/61 |
| F | D + bundle 15 | 3 | 344 | 8756 | 1.25× | 43/11 | 254/249 | 73/63 |
| G | D + bundle 5 | 5 | 330 | 8410 | 1.23× | 47/10 | 275/230 | 75/65 |
| H | D + bundle 15 + grain 14 | 4 | 341 | 8518 | 1.28× | 51/6 | 205/194 | 69/68 |
| I | D + compact 10, *before* the exemption | 2† | 339 | 8477 | 1.28× | 47/9 | 189/177 | 74/74 |
| K | D + cross 20 (return-path) | 3 | 341 | 8603 | 1.23× | 46/10 | 341/320 | **49**/60 |
| L | D + tjoin 0 | 2 | 367 | 8712 | 1.24× | 49/11 | 270/257 | 76/61 |
| N | D + a stage-4 rescue freed of the grain | 2 | 356 | 8645 | 1.23× | 48/12 | 282/238 | 74/61 |
| P | D, relax 2 | 2 | 365 | 8651 | 1.23× | 47/10 | 395/240 | 73/53 |
| Q | D + compact 10 | **1** | 368 | 8815 | 1.25× | 45/11 | 232/218 | 79/65 |
| R | D + compact 10 + bundle 15 | 6 | 407 | 9295 | **1.38×** | 41/11 | 228/293 | 70/57 |
| T | D + compact 20 | 3 | 319 | 8428 | 1.27× | 45/11 | 203/174 | 73/75 |
| V | D + vgrid (via lattice) | 1 | 352 | 8854 | 1.25× | 48/13 | 289/295 | 65/53 |
| **W** | **D, history decay OFF** | **0** | 339 | 8736 | 1.23× | 49/11 | 389/261 | 73/52 |
| X | Q, tighten 4 | 1 | 365 | 8788 | 1.25× | 45/11 | 230/218 | **80**/63 |
| Y | W + compact 10 | 4 | 343 | 8439 | 1.24× | 46/10 | 240/199 | 80/67 |
| Z | W + compact 20 | 3 | 310 | **8255** | 1.25× | 45/10 | 209/164 | **81/75** |

† I's second split is `+5V` shattered into 29 pieces — see the exemption below.

## What the controls showed

**The via price and the grain are not independent, and that is the finding of the day.** Raising
the via price alone — run C, the no-grain control — made the pour *worse than the board that
started all this*: 365 islands against 292. Fewer vias means longer runs on a single face, and a
long run cuts the plane further than a short one that dives to the other side. A dear via only
helps the plane if a grain is telling those longer runs where to go. Ship one without the other
and you have made the board worse while every number you were watching improved.

**Compaction is the strongest lever on the pour.** Run Z: 209 / 164 islands against the shipped
board's 292 / 287, with the largest region holding 81 % and 75 % of the copper on the two faces
against 58 % and 62 %, the lowest copper of any run, and 310 vias against 476.

**The return-path rule is actively harmful here.** Worst pour of any configuration — 341 / 320
islands, largest holding 49 % — because pushing tracks off one another is precisely the opposite
of compaction. It is a real electromagnetic rule and this board does not want it: nothing on it
has fast edges except the boost converter, and the cathode lines switch at kilohertz. If it is
ever wanted it belongs on the converter's nets alone.

**The via lattice does not pay,** as the arithmetic predicted before it was written: 350 vias with
their clearance cover about 3 % of this board against 41 % for the tracks. The pour is cut by
copper, not by drills.

**T-junction discipline costs vias and buys little** — 367, the most of any run, for a pour no
better than the control.

**Bundling and compaction fight.** Separately each helps; together (run R) they gave six splits,
407 vias and a 1.38× detour, the worst of everything tried.

**Two passes of tightening is enough.** Run X added a third and fourth: they recovered 70 mm and
then 1 mm.

**Infrastructure nets must be exempt from all of it.** `+5V` has 29 pads, more than anything but
GND. It came out in 29 pieces under the grain; that was diagnosed as a via-price problem and
given cheap vias; then it came out in 29 pieces again under compaction with the cheap vias in
place. A net with pads everywhere has to travel in every direction and change face constantly.
Every rule that is good for a point-to-point signal is a trap for a small power tree.

## Two of my own ideas were wrong

**History decay.** I added it because "a cell contested in round three is still dear in round
twenty, so late nets detour round congestion that has moved elsewhere". That sounds right and is
wrong. PathFinder makes its history term cumulative *on purpose*: it is the tie-breaker of last
resort, the thing that finally makes one of two nets give up a corridor for good. Let it fade and
they swap the corridor for ever. Turned off, the negotiation reached **zero overlaps at round 20
and every net routed** — the first time that has happened on this board.

It is not a universal, and the control says so: with compaction on, the sign flips — decay on
gave one split, decay off gave four. Compaction already concentrates the nets, and permanent
scars on top of that over-constrain the search.

**The via lattice**, argued against on the arithmetic, written anyway, and duly useless. That one
at least cost only ten lines.

## A silent bug that no checker could see

`route_net()` grows a tree by Prim's, and it was adding each pad to the grown set **whether or
not its connection had succeeded**. So the next pad could be wired to a pad that reaches nothing,
and what came out was an island rather than a branch — silently, because every pad still has
copper on it and a per-pad checker is satisfied by that.

GND had `VT10.2` and `VT11.2` wired to each other and to nothing else for exactly this reason. It
survived all twenty-two configurations above, because none of them touched the cause. It is the
one finding that was in every single run, including the board that shipped.

## And then: the router was never the thing that was wrong

The same few nets kept topping the detour table, so `tools/placecheck.py` was written to ask why.
It sums the Euclidean MST over each net's own pads — the shortest wiring that could possibly
exist — which is what the **placement** costs before routing is attempted.

- The Nano sits in a corner with **28 connections reaching across a 176 mm board.** `D12` runs
  151.9 mm.
- The К155ИД1 sits at y = 77.5, **40 mm above the row of tubes it drives**, so each of its ten
  cathode lines pays that detour twice.

| proposal | floor | |
|---|---|---|
| as placed | 6419 mm | |
| Nano slid along the edge it is already pinned to, USB unchanged | 5947 mm | 7.4 % less |
| …and the К155ИД1 moved onto the tube row beside it | 5393 mm | **16.0 % less** |
| each base resistor paired with its transistor (18 of 20 are over 8 mm away; one is 52.7 mm) | 6191 mm | 3.6 % less |
| both | 5165 mm | **19.5 % less** |

**Sixteen per cent of the floor from two parts, against about three per cent of the copper from
every routing rule put together.**

The base-resistor line corrects an obvious guess: only 3.6 %, not because the distances are small
— there are 583 mm of them — but because the resistor sits *between* the expander and the
transistor, so shortening one side lengthens the other. Worth doing for routability (the nets no
configuration could close are long base nets) but not for length.

## What was kept

`grain 8`, `via 900` (9 mm), `relax 4`, `tighten 2`, history decay **off**, the infrastructure
exemption, a stage-4 rescue freed of the grain, and the `route_net` fix. Compaction, bundling,
the return-path rule, the T-junction restriction and the via lattice are all implemented and all
default to off, with the numbers above as the reason.

Compaction is the one to reconsider: it gives much the best pour and costs one net. If the
placement is ever fixed, it should be tried again — a board with 19 % less to route has room for
a convention that a full one cannot afford.

## What to do next

1. **Move the Nano and the К155ИД1.** Nothing in the routing rules comes close. Both positions
   found here collide with tube sockets as they stand, so this needs a real placement pass.
   `TS06_AT_U1=21.98,66` prices a proposal against a real route.
2. **Consider the two-board split** — `TS06-split-study.md`, 18 wires. It agrees with the
   placement finding: both say the decoder belongs beside the tubes.

## Reproducing anything here

Every routing parameter reads from the environment through `RP` in `tools/mkpcb_main.py` and is
printed at the start of every run, so a board can say what made it.

```bash
TS06_BIAS=8 TS06_COMPACT=10 TS06_OUT=/tmp/try.kicad_pcb python tools/mkpcb_main.py --route
python tools/audit.py /tmp/try.kicad_pcb
python tools/plotcu.py /tmp/try.kicad_pcb /tmp/try.png
```
