# The routing baseline: TS06-MAIN before the via cost was lowered

This folder is a **snapshot of a failure**, kept on purpose. It is what the router did with
the parameters it was first given, and it is the reason those parameters were changed in a way
that quietly cost the board its structure for the rest of the session.

## What is here

| file | what it is |
|---|---|
| `TS06-MAIN-vc1500.kicad_pcb` | the board, routed with the original parameters |
| `TS06-MAIN-vc1500.png` | its copper, front face above, back face below |
| `route-vc1500.log` | the routing run, round by round |
| `audit-vc1500.txt` | `tools/audit.py` on it, including the quality metrics |

## The parameters

```
via_cost=1500   price=3   rise=1.4   rounds=10   turn=15   bias=0   decay=1.0   tighten=0
```

These are TS06-SEC's parameters, inherited unexamined. A via was priced at **15 mm of track** —
the sane value, and the repo's stated standing preference — and a contested cell opened at 3.

## What went wrong, in one line

**The price of sharing a cell could not beat the price of a via, so no net ever moved.**

A plain 0.1 mm step costs 10, so 1 mm of track costs 100. Crossing another net means two vias,
3000. A net sharing fifteen cells with a neighbour pays 3 × 15 = 45. Forty-five against three
thousand: the negotiation's entire mechanism — raise the price until somebody yields — was
switched off, because yielding was five hundred times dearer than not yielding.

The log shows it plainly. Overlapping nets, round by round:

```
84  77  76  68  66  70  65  62  53  52
```

Ten rounds, four minutes each, and the price had climbed only from 3 to 96 — nowhere near the
3000 it needed. Round 6 went **up**. Three runs like this stalled in the low eighties before
the parameters were changed.

## What was changed, and the part of it that was wrong

The fix was `via_cost 250, price 60, rise 1.6`, and it worked: the board converged. But 250 is
**2.5 mm of track**, and at that price a via is cheaper than almost any detour. The board that
shipped carried **476 vias**, its copper had no grain at all, and its ground pour filled as 292
islands. None of that was noticed, because the only number being steered by was how many nets
were left unrouted, and that number reached zero.

The right fix was not "make vias cheap enough that nets never have to yield". It was to make the
price of a contested cell climb fast enough to beat a via that is still priced honestly — and,
as the later runs showed, to give the board a grain so that the longer same-face runs a dear via
implies have somewhere sensible to go.

## The numbers, against what shipped and what replaced it

|  | this baseline | shipped | with a grain |
|---|---|---|---|
| nets left split | 6 | 1 | 3 |
| vias | 329 | 476 | 308 |
| copper | 8390 mm | 8575 mm | 8281 mm |
| detour against the floor | 1.28× | 1.23× | 1.25× |
| grain, front | 37 % / 21 % | 33 % / 25 % | **50 % / 8 %** |
| pour islands | 250 / 233 | 292 / 287 | 269 / 242 |

Note the baseline is not uniformly worse — it has fewer vias and fewer islands than the board
that shipped. It is worse where it counts: **six nets never routed at all**, and it had not
converged after ten rounds, with no sign that it would.

One net in it is worth looking at on its own. `K9` was rescued in the last stage, alone and with
cheap vias, and came out at **344.9 mm against a 143.6 mm floor, carrying 23 vias**. That is the
signature of the whole approach: a net that cannot be negotiated gets thrown in afterwards and
sprawls wherever there is room.

## Reproducing it

```bash
TS06_VIA_COST=1500 TS06_PRICE=3 TS06_RISE=1.4 TS06_BIAS=0 TS06_DECAY=1.0 TS06_TIGHTEN=0 TS06_ROUNDS=10 TS06_OUT=out.kicad_pcb python tools/mkpcb_main.py --route
```

Roughly 45 minutes. Every routing parameter now reads from the environment through `RP` in
`tools/mkpcb_main.py`, and the run prints the set it used, so any board in this repo can say
what made it.
