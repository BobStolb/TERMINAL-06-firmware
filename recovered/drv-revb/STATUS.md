# TS06-DRV rev B: status

Resume here: watch runs r3 (option 3, tree placement) and r4 (variant: R73/R74 standing in line on the gap's descent, scratch revb2/v4/tools); take the first that ends "0 nets sharing, 0 unrouted", copy its routes.json to tools/mkpcb_drv_routes.json (for r4 also its 4 pl() lines into tools/mkpcb_drv.py) and regenerate.

Updated: 30.09.26 05:28 UTC. Last routing line: r3 round 10: 8 nets sharing, 0 unrouted, pres 34.6, 1471s (+5V GND HV185 M_A OPT_M1 OPT_M10 OPT_S10 PWM_G); r4 round 7: 12 nets sharing (A7 SCL SDA among them).

## Plan (written before the first edit)
1. Apply the recovered patches (done: b4d187a, 13c6c29, 335f537).
2. Read the congestion round J1 from the placement; write OPTIONS.md with at least 3 options, costs and the choice; commit.
3. Apply the chosen option in `tools/mkpcb_drv.py` (and `tools/ts06pair.py` if a footprint or a note changes); check the placement (`--place`) and the hand-laid copper (`--hand`).
4. Make the negotiated router write its state to disk every round (route JSON + last line), launch it with nohup and PYTHONHASHSEED=0, at most 2 runs.
5. From the route that ends "0 nets sharing, 0 unrouted": write the board, then `mksch_pair.py`, `bom_pair.py`, `verify_pair.sh`, the scorecard against rev A.
6. README DRV row, STATUS, commit.

## Findings
* (seen) Rev A's route (78105d6's mkpcb_drv_routes.json): SCL ran west along y 54.4 to x 126.7 then down to U13; rev B's R61 (МЛТ, GND pad at 136.1, 54.3) now sits on that line. SDA ran down the corridor (x 152.2) and west along y 75.8. A6, A7, D7, D8 all on the back face, nested, turning west at y 91.9-94.6.
* (inferred) SCL's stall in r1/r2 may be that blocked rev A path; watch it in r3 (option 4 is the fallback).
* (seen) The fascia RC parts (R72-R74, C18, C19) were put by `near()` in a fence 1-5 mm north of J1 (x 138-152, y 77-93, DRV frame): R74 and R73 stand lying N-S exactly where rev A's back-face bundle turned west into J1 (rev A copper.png, y 92-94).
* (seen) The LED ribbon's BL_A1/BL_A2 run on the front face at y 69-71 from x 27 to 176, so everything crossing the strip band between the column/gap and J1 crosses on the back face.
* (seen) Predecessor's stalls: r1 A6 A7 D7 D8 SCL (rounds 15-45, pres to 5e7: a hard, not a congestion, block); r2 +5V D8 GND SCL at round 15.
* (computed) J1 pins at y 95.0, x 137.4 (+5V) ... 147.4 (D8_J), 2.0 pitch. The open ground east of J1: x 152-183, y 80-98 (H6's keep-out from x 184).
* (seen) r3 round 10: no J1 net shares any more (A6, A7, D7, D8, D7_J, D8_J, SCL, SDA all clear); the predecessor's r2 at round 10 still had A6 A7 D7 D8 SCL. The 5 pairs left are crossings in the middle of the board (PWM_G x OPT_M1/OPT_M10, HV185 x OPT_S10, M_A x OPT_S10, +5V x GND), the kind rev A's run resolved by round 15.

## Log
* Now: git am of the three patches on 78105d6, because the mission starts from them.
* Now: placement render round J1 (scratch revb2/place/j1.png) and rev A's copper there, because the stall is there.

* Now: OPTIONS.md on the J1 funnel, because the brief asks for it before any re-route (choice: option 3).
* Now: R72-R74, C18, C19 placed by hand in mkpcb_drv.py, because near() had fenced the funnel.
* Now: Negotiator.run(state=...) writes the round's line, sharing, unrouted and tracks after every round (TS06_STATE), because a stopped run must lose nothing.
* Now: run r3 (option 3 placement, PYTHONHASHSEED=0), nohup, PID 4708, because the placement changed.
* Now: run r4 (PID 5089) from a scratch copy of tools/ (revb2/v4/tools, PCB symlinked): R73/R74 standing N-S in line on D7/D8's rev A descent (x 165.1/168.2, pad 1 on top at y 74/76), C18 west of R73's pad 2, C19 east of R74's; same R72. Because a hedge on the RC block's shape costs nothing while r3 runs (2 routing processes max).
* Now: conflict pairs of r3's round 10 read from its state file (scratch revb2/conf.py), because the sharing list alone does not say where.

## Checks (command: last count)
* `python3 tools/mkpcb_drv.py --place`: runs, no overlap printed (option 3 placement).
* `python3 tools/mkpcb_drv.py --hand`: exit 0, no hand-laid problem.
* `scratch/funnel2.py`: predecessor 3 crossings / 3 blocking pads; option 3: 1 (SCL x SDA, common) / 0.
