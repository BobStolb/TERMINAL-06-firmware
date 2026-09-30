# TS06-DRV rev B: status

Resume here: wait for r5 (a fresh `--route` with no seed in the environment; scratch revb2/r5, PID 11427). When it writes its board, compare its routes.json with tools/mkpcb_drv_routes.json and record the result below. Nothing else is open in this mission's files.

Updated: 30.09.26 05:53 UTC. Last routing line: r3 round 13: 0 nets sharing, 0 unrouted, pres 116.8, 1628s (then polished, 30 nets shorter). r5 started 05:50.

## Plan (written before the first edit)
1. Apply the recovered patches (done: b4d187a, 13c6c29, 335f537).
2. Read the congestion round J1 from the placement; write OPTIONS.md with at least 3 options, their costs and the choice; commit (done).
3. Apply the chosen option in `tools/mkpcb_drv.py`; check the placement (`--place`) and the hand-laid copper (`--hand`) (done).
4. Make the negotiated router write its state to disk every round; launch with nohup and PYTHONHASHSEED=0, at most 2 runs (done: r3, r4).
5. From the route that ends "0 nets sharing, 0 unrouted": write the board, then `mksch_pair.py`, `bom_pair.py`, `verify_pair.sh`, and the scorecard against rev A (done).
6. README DRV row, STATUS, commit (done).

## Findings
* (seen) The fascia RC parts (R72-R74, C18, C19) were put by `near()` in a fence 1-5 mm north of J1 (x 138-152, y 77-93, DRV frame). R74 and R73 lay north-south exactly where rev A's back-face bundle turned west into J1 (rev A copper.png, y 92-94).
* (seen) The LED ribbon's BL_A1 and BL_A2 run on the front face at y 69-71, from x 27 to 176. So everything crossing the strip band between the column or the gap and J1 crosses on the back face.
* (seen) The predecessor's stalls: r1 held A6 A7 D7 D8 SCL from round 15 to round 45 while the price rose to 5e7, a hard block rather than congestion. r2 held +5V D8 GND SCL at round 15.
* (computed) `scratch/funnel2.py`: the predecessor's placement has 2 forced crossings (A7 × D7_J) and 3 RC pads on other nets' lines. Option 3 has 0 and 0. SCL × SDA is common to both and resolved at the pull-ups.
* (seen) r3, option 3: at round 10 no J1 net shares. Round 13: **0 nets sharing, 0 unrouted**. r4, the hedge variant, was still at 9 nets at round 8 and was stopped.
* (seen) KiCad DRC on the routed board, first pass: 1 starved thermal (R71.2, F.Cu) and 13 silk warnings, all in rev B's legends (the fences crossed part outlines; the text boxes were smaller than KiCad's). After the fix: 0 errors, 0 unconnected, 2 warnings (the Nano's silk past the edge, accepted).
* (seen) The case model read no height for rev B's new footprints and assumed 25 mm, which made the case 3 mm deeper. With `height=` in their descr it reads them, and the envelope is 81.6 mm deep (the committed rev A outputs say 83.6).
* (seen) `polish()` put a net's hand-laid tracks back a second time when it kept the old route. A `--route` board then carried 8 duplicate SDA segments; a board written from the saved JSON did not. Fixed; `scratch/repolish.py` shows the polished route is identical before and after the fix.
* (computed) DIP orientations went from 3 to 4: U11 at 0° in the recovered placement, 180° in rev A. It is not on the change list; it is reported, not changed.

## Log
* Now: git am of the three patches on 78105d6, because the mission starts from them.
* Now: placement render round J1 (scratch revb2/place/j1.png) and rev A's copper there, because the stall is there.
* Now: OPTIONS.md on the J1 funnel, because the brief asks for it before any re-route (choice: option 3).
* Now: R72-R74, C18, C19 placed by hand in mkpcb_drv.py, because `near()` had fenced the funnel.
* Now: Negotiator.run(state=...) writes the round's line, sharing, unrouted and tracks after every round (TS06_STATE), because a stopped run must lose nothing.
* Now: run r3 (option 3 placement, PYTHONHASHSEED=0), nohup, PID 4708, because the placement changed.
* Now: run r4 (PID 5089), from a scratch copy of tools/ (revb2/v4/tools): R73 and R74 standing in line on D7's and D8's rev A descent. A hedge while r3 ran.
* Now: r3 converged at round 13; r4 stopped by PID; the route saved to tools/mkpcb_drv_routes.json, and board, schematic and BOM regenerated.
* Now: verify_pair run 1: 25 PASS, 2 FAIL (DRV drc; case outputs). Fixed the DRC items in the legend code and R71's no_zone.
* Now: `height=` added to the rev B footprints' descr, because the case model assumed 25 mm.
* Now: verify_pair run 3: 26 PASS, 1 FAIL (case outputs, in 3d/, outside this mission).
* Now: polish's duplicate hand-laid tracks fixed and checked by re-polishing r3's converged state.
* Now: J1's back-face pinout reversed to read in the order the pins stand on that face; DRC re-run, clean.
* Now: r5, a fresh `--route` with no seed in the environment, to show that the script pins it and the route reproduces.

## Checks (command: last count)
* `python3 tools/mkpcb_drv.py`: check 0 problems, 0 cathode pads under 0.5 mm, check_mate clean, 1164 segments, 0 vias.
* `python3 tools/checkcopper.py PCB/TS06-DRV/TS06-DRV.kicad_pcb --hv HV185,SW,BLEED_*,FB_MID,COLON_*,ANODE_*,EMIT_*,OVZ_* --hv-pad 0.8`: clean (160 HV pad-layers held to 0.8 mm).
* `bash tools/verify_pair.sh`: 26 PASS, 1 FAIL, 0 SKIP. The FAIL is "case outputs: 7 of 7 stale". It needs `python3 3d/case-pair/case_pair.py --extract` and a commit by the owner of 3d/.
* KiCad DRC (scratch revb2/drc.sh): 0 errors, 2 warnings (accepted), 0 unconnected.
* Scorecard (scratchpad/scorecard.py): 1164 segments, 0 vias, signal copper 5918 mm on a 4533 mm floor = 1.31, 83.3 % straight. Rev A: 1097, 0, 5936 / 4479 = 1.33, 86.1 %.
