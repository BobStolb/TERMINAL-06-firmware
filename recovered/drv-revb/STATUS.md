# TS06-DRV rev B: status

Resume here: write OPTIONS.md (the J1 congestion options), then re-place the fascia RC block and route.

Updated: 30.09.26 05:05 UTC. Last routing line: none yet in this session (predecessor r2: round 15, 4 nets sharing: +5V D8 GND SCL).

## Plan (written before the first edit)
1. Apply the recovered patches (done: b4d187a, 13c6c29, 335f537).
2. Read the congestion round J1 from the placement; write OPTIONS.md with at least 3 options, costs and the choice; commit.
3. Apply the chosen option in `tools/mkpcb_drv.py` (and `tools/ts06pair.py` if a footprint or a note changes); check the placement (`--place`) and the hand-laid copper (`--hand`).
4. Make the negotiated router write its state to disk every round (route JSON + last line), launch it with nohup and PYTHONHASHSEED=0, at most 2 runs.
5. From the route that ends "0 nets sharing, 0 unrouted": write the board, then `mksch_pair.py`, `bom_pair.py`, `verify_pair.sh`, the scorecard against rev A.
6. README DRV row, STATUS, commit.

## Findings
* (seen) The fascia RC parts (R72-R74, C18, C19) were put by `near()` in a fence 1-5 mm north of J1 (x 138-152, y 77-93, DRV frame): R74 and R73 stand lying N-S exactly where rev A's back-face bundle turned west into J1 (rev A copper.png, y 92-94).
* (seen) The LED ribbon's BL_A1/BL_A2 run on the front face at y 69-71 from x 27 to 176, so everything crossing the strip band between the column/gap and J1 crosses on the back face.
* (seen) Predecessor's stalls: r1 A6 A7 D7 D8 SCL (rounds 15-45, pres to 5e7: a hard, not a congestion, block); r2 +5V D8 GND SCL at round 15.
* (computed) J1 pins at y 95.0, x 137.4 (+5V) ... 147.4 (D8_J), 2.0 pitch. The open ground east of J1: x 152-183, y 80-98 (H6's keep-out from x 184).

## Log
* Now: git am of the three patches on 78105d6, because the mission starts from them.
* Now: placement render round J1 (scratch revb2/place/j1.png) and rev A's copper there, because the stall is there.

## Checks (command: last count)
* `python3 tools/mkpcb_drv.py --place`: runs, no overlap printed.
