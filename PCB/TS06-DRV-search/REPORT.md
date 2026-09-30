# TS06-DRV-search: an optimiser-proposed layout

## Concept
I did not choose the layout by hand. `tools/placesearch.py` treats the board as 24 rigid blocks and anneals their poses and three firmware-only remaps. The cost is MST length plus a heavy price for MST crossings that cannot be put on opposite faces. The best candidate was then routed with **no hand-laid copper at all** on the baseline's router settings.

## Verdict: inconclusive, with a lean towards "worse to build, easier to route"
- **What worked.** `cand_11fr` converged with nothing hand-laid: 0 nets sharing at round 37 of 60, `B.check()` and `check_mate()` clean, 0 vias, 0 unconnected in KiCad DRC.

  The baseline needed a corridor, a fan-out, a hop column, the port-A bus and the LED ribbon laid by hand. So its intricacy comes from its placement, not the circuit.
- **What it costs.** It is not simpler to assemble: the 14 DIPs use all 4 pin-1 orientations; the anode cells are scattered; HV and logic are not separated (HV185 runs ~100 mm along the top edge on the back, the control block sits ~60 mm from the switch); the jack is on the bottom edge; four mechanical DRC findings remain.

  The cost did not price these. I would not ship this placement; I would use the method, with a better cost, to seed a hand-tidied layout.

## Scorecard (cand_11fr; the coordinator scores the baseline)
| | TS06-DRV-search |
|---|---|
| Converged | **yes**: 0 sharing at round 37, polish done, `B.check()` 0 problems |
| Vias | 0 |
| Track length | 5589 mm in all; 4784 mm without GND |
| MST floor (placecheck.py) | 3617 mm (the baseline's under my cost: 4268 mm) |
| Track / floor | 1.32 without GND (1.55 with the GND tree) |
| Track segments | 1236 |
| Axis-aligned fraction of length | 0.777 |
| Hand-laid segments | **0** |
| Distinct DIP pin-1 orientations | 4 (of 14 DIPs) |
| Board height used | y 5.8 – 100.0 of 100 (the jack courtyard reaches the bottom edge) |
| Tallest part | C7 (Ø10 400 V radial, ≈16–20 mm) at (40, 78), lower left, front face. L1 (Ø12) is beside it, and the Nano on sockets is lower right. |
| USB | Nano lower right, rotated 270; USB out of the **right edge** (courtyard to x 178.4, 2.4 mm proud like the baseline) at y 71–89 |
| 12 V jack | **bottom edge**, lower left (x 8–20, mouth at y 100) |
| GND pour | 26 filled regions on F.Cu, 30 on B.Cu after KiCad's refill. Pad-less islands are removed; the routed GND tree carries the connection. |
| KiCad 10 DRC (`kicad-cli pcb drc --refill-zones`, HV class from the generated .kicad_pro) | 0 unconnected, 0 clearance or short errors. 68 findings in all: 103 lib_footprint_issues (local library), 41 silk, 7 starved_thermal, **14 pth_inside_courtyard, 2 courtyards_overlap** (see Remaining problems) |

## The optimiser, and how well it predicted the router
`tools/placesearch.py` works as follows (its docstring has the details):
- **Blocks.** Converter loop, control, power inlet and U3+RN1 keep the baseline's arrangement. I drew the opto cells (flat opto, standing 470R, anode resistor under it, standing bleeds), each decoder with its 100n, RTC with pull-ups, J1 (back) with the A6/A7 filters, the two MPSA42 switches and a few loose parts.
- **Moves.** Translate, turn in 90° steps, "mirror" (pad centroids reflected; never a mirrored footprint). Restarts run in parallel, ~8 ms per iteration.

Calibration: the same cost applied to the baseline placement.

| | cost | MST mm | crossings | near a pad | frustrated (away from pads) | frustrated (all) |
|---|---|---|---|---|---|---|
| baseline (mkpcb_drv.py) | 8213 | 4268 | 340 | 108 | 61 | 111 |
| cand 11 | 5486 | 3716 | 182 | 110 | 0 | 27 |
| cand 12r | 5862 | 4058 | 263 | 138 | 5 | 51 |
| cand 21 | 6300 | 4022 | 301 | 139 | 15 | 50 |
| **cand 11fr** (11 refined under "all") | 5594* | **3610** | **172** | 101 | – | **9** |

\*Under the old weighting.

The baseline scores badly: it routes only because hand-laid copper resolves its crossings. Only 1 of 6 random restarts (seed 11) found the good basin; the others ended at 5894–11510. Run more restarts than I did.

Router struggle, in nets sharing by round, with the standard settings:

| round | 0 | 5 | 10 | 15 | 19–20 | end |
|---|---|---|---|---|---|---|
| cand 11 | 73 | 66 | 32 | 10 | 8 | stuck at 4 (K2 K9 BL_A1 D6) from round 39; the run was lost at round 46 in a container restart, and the rerun shows the same trajectory |
| cand 11, decoder fans routed first | 59 | 62 | – | – | – | stuck at 4 (XB0/XB1 beside RN1, BL_A8/M_A at XS25) from round 43 |
| cand 12r | 67 | 74 | 38 | 30 | – | lost at round 16 (27 sharing) |
| cand 21 | 64 | 62 | 43 | 25 | 17 | lost at round 19 |
| **cand 11fr** | – | – | – | – | – | **0 at round 37** |

The ranking held. Fewer predicted crossings meant faster convergence (11 < 21 ≈ 12r), and the round-0 counts track the crossing counts only loosely.

**Lesson.** The near-pad discount is right for counting crossings but wrong for frustration: an MST edge is one track on one face whatever pads its net has, so a decoder's 2-pad lines crossing the strip order form an odd cycle beside the pads. Cand 11's last stuck pair was exactly that (K2/K9, U2→XS11), scored 0 by my first cost and 27 frustrated when counted over all crossings. A cold re-anneal under the corrected cost gave 11fr (9), which converged. `FRUSTR_ALL=1` is now the default. The decoder-first run's leftovers were local squeezes from a mirrored U3+RN1 block, priced too cheaply.

## Key placement decisions (all the optimiser's)
- **Nano:** lower right, USB out of the right edge, like the baseline's side of the case. J1 sits on the back face under the Nano's rows, below the display.
- **Decoders:** U2 beside XS11 as in the baseline; U17 and U15/U16 along XS12; U3 directly under the ИН-15 decoders with RN1 beside it, so port A is ~10 mm instead of the left-edge run.
- **Converter:** lower left beside the inlet; its control block top left, so the FB divider runs up the left side.
- **Opto cells:** spread over the lower middle and right, each near its Nano pin (the remap allowed that).

## Remaps (applied in `tools/ts06pair.py` on this branch)
1. **Anode channels (firmware opts[] only).** H10←D13, H1←D6, M10←D4, M1←D3, S10←D2, S1←D5. For BOARD_TYPE 4, opts[] becomes `{KEY5, KEY3, KEY1, KEY0, KEY4, KEY2}`; it was `{KEY3, KEY2, KEY1, KEY0, KEY4, KEY5}`. I have **not** edited the firmware.
2. **LEDs.** RN1 element k / GPBk now lights HL(8−k): `BL_OF_GPB = [8, 7, 6, 5, 4, 3, 2, 1]`.
3. **Port-A nibbles:** unchanged (the search could have swapped them and did not).
4. **Footprints.** R21/R22 (H10/H1 opto 470R) now stand, like the other four.

Nothing else changed: J1 order, RTC order, strip order and the A0–A3 map are all as before.

`tools/mkpcb_drv.py` is drawn for the old maps: regenerate the baseline from `pcb/kicad-boards`. (On this branch `--baseline` reads 4284 mm / 347 crossings because R21/R22 now stand; the table is from the unedited netlist.)

## Remaining problems
- **Mechanical DRC findings:**
  - J1 (back face) is inside the Nano's courtyard: its pins are between the Nano's socket rows. The sockets clear the joints, but it is a real clash for DRC and for assembly order (J1 must go in before the Nano sockets);
  - F1's body overhangs XS25's solder joints;
  - U14 touches display standoff H2's courtyard;
  - R1 and C6 courtyards touch.

  The overlap term compared only same-face courtyards, so a back part under a front one was never priced; the rest is ≈12 mm² residual overlap the refine did not remove.
- **HV/logic separation.** The HV term only prices 185 V pads within 4 mm of logic pads. It says nothing about long HV tracks, so HV185 crosses the whole top band and threads between logic. The long FB divider run is also a noise risk. Add wirelength weight on HV nets and on FB/FB_LOW.
- **Assemblability is not in the cost:** pin-1 orientations, cell alignment, and the jack on the bottom edge.
- **Robustness.** Of 6 routing runs (two lost to a container restart), the one that converged had the fewest predicted frustrated crossings: 1 board, not a proven method. Firmware not changed.

## Pictures
`placement.png`, `copper.png` (F.Cu above, B.Cu below, HV red), `cands/*.png` (blocks and MST per candidate), routing logs in `logs/`.

## Reproduce
```
python3 tools/placesearch.py --runs 4 --iters 80000 --seed 11
cp PCB/TS06-DRV-search/cands/cand_11.json PCB/TS06-DRV-search/cands/cand_11f.json
python3 tools/placesearch.py --refine PCB/TS06-DRV-search/cands/cand_11f.json --iters 20000   # -> cand_11fr.json
python3 tools/mkpcb_drv_search.py --cand PCB/TS06-DRV-search/cands/cand_11fr.json --route
python3 tools/mkpcb_drv_search.py --cand PCB/TS06-DRV-search/cands/cand_11fr.json
python3 tools/placecheck.py PCB/TS06-DRV-search/TS06-DRV-search.kicad_pcb
kicad-cli pcb drc --refill-zones --format json PCB/TS06-DRV-search/TS06-DRV-search.kicad_pcb   # in mirror.gcr.io/kicad/kicad:10.0
```
Without `--route` the board regenerates from `cand_11fr.routes.json`. Shared tools (pcbkit.py, netroute.py) are unchanged.
