# TS06 audit: evidence (what is proven, and how)

Run audit-evidence, 2026-11-14, on `pcb/kicad-boards` at 8e030d4. Brief: `PCB/audit/BRIEF.md`.

## Verdict

1. **Rev B is well proven as files.** All 27 script checks pass today, with KiCad 10's own DRC and ERC. The boards and
   schematics regenerate byte for byte. The three fab zips rebuild from the repo with only date and version lines changed.
2. **Nothing is proven as hardware.** No board was built and no electrical value was measured. Every check compares files
   with one netlist that was typed once; no check compares that netlist with real parts. Three open bench gates decide copper.
3. **No Stop. Do not order ten sets yet.** Measure the parts in hand, then build one set (the ladder below). Rev C is a plan
   on assumed inputs: measure its 5 V load and the PWM chip's reset state before it is drawn.

## Findings

Class: M = measured here from the files, I = inferred, A = assumed. Sources are in the detail.

| # | Severity | About | Class | Finding | Fix |
|---|---|---|---|---|---|
| 1 | Fix before order | rev B | I | Gates that decide copper are open: the ИН-17 lead order, the ИН-15 anode pin, the RTC module's pin order, the strip heights (the 11 mm standoff), the colon lamps against the M10 glass. No bench record exists. | Ladder steps 1 to 3, on parts in hand, before any order. |
| 2 | Fix before order | rev B, fascia and case | M | The `case` line says PASS with an open FAIL inside it: the fascia boss at (4.5, 35.5) lands on R5's pad, -1.20 mm. "27 PASS, 0 FAIL" hides it. | Decide: trim the boss, move the hole, or move R5. Then print open items as their own count. |
| 3 | Fix before order | rev C | I | The plan stands on assumed inputs: a 5 V load of 872 to 940 mA on a 1.0 A module, 20 mA a filament, the PWM chip's reset state, the clock's own 5 V current. No netlist, no routed board, no DRC. | Ladder step 5 before the schematic. |
| 4 | Should fix | both | I | One source, many mirrors. The schematic, the board, the BOM and the firmware-table check all come from `tools/ts06pair.py`. ERC, `checkmatch` and "firmware tables" prove that the generators agree, not that the circuit is right. Part pin maps are typed once and checked by no file. | A pin-map table checked against data sheets and signed; a circuit simulation of the converter and the clamp; then the bench. |
| 5 | Should fix | both | M | The checks do not repeat on a clean machine: 16 PASS, 5 SKIP, exit code 0. One SKIP line stands for 7 checks, so 11 of 27 did not run. The KiCad image tag floats: 10.0.6 on 30.09, 10.0.8 today. | A requirements file, a pinned image digest, a `--strict` flag that fails on SKIP, the planned count printed. |
| 6 | Should fix (rev C: day one) | both | M | "Which nets are 185 V" is a list of names, typed in three places. The script's list lacks `OVZ_*`, which the project class has. No check works the voltage out from the circuit: a new HV net with a new name gets 0.2 mm, and nothing says so. No check for creepage, HV to board edge, or touch. | Take the list from the netlist. Add a check that walks out from HV185 through the parts and fails on an unclassed net. |
| 7 | Should fix | rev B, fascia | M | The fascia that is to be ordered is not a board in the repo, and `verify_pair.sh` does not cover the fascia. Its zip is built in scratch: gold copper (158 draws) and holes of 8.4 and 9.2 where the committed board has 8.0 and 8.8. Its project sets the least clearance to 0 and ignores 5 DRC check types. | Add the fascia, as built for the fab, and the J1 pin map to the check run. |
| 8 | Should fix | rev B | M | The test plan's stage 3b pass band, 145 to 160 V, shuts out its own computed value, 165.5 V. A good board fails the step. | Correct the band: about 157 to 174 V (+-5 %, *assumed*). |
| 9 | Should fix | rev B | I | "The firmware matches" is proven for tables only. Nothing compiles the sketch. The committed `.hex` is not tied to the source. The A6 and A7 ladder thresholds are calculated. The lever code on A7 is not written. | Compile in the check run; delete the `.hex` or stamp it; measure the ladder (ladder step 9). |
| 10 | Should fix | docs | M | Stale numbers: the page (19 PASS; DRV 95 parts, 130 nets; case 83.6 deep; 4 DRC warnings); the README and the review (case 122.8 x 81.6; today 120.0 x 81.0); the word "ordered" in `fab/ORDER.md`, `tools/mkfab.sh` and the page, against the owner's "not ordered yet". | Write these numbers into the docs from the check run. Say "to order". |
| 11 | Note | rev B | M, A | The safety numbers are calculations: C7 down to 10 V in 8.0 s; the clamp at 225 to 270 V; the 0.8 mm HV pad gap, met with 0.83 to 0.84 mm in about 70 places. None is measured. | Ladder steps 6 to 8. |
| 12 | Note | rev B | M | The committed boards hold no pour fill, so the copper that goes to the fab is made by the KiCad version of the day. Today's rebuild equals the committed zips; `mkfab.sh` would still rewrite all three (the version line). | Pin the image. Treat the version line as a date line. |
| 13 | Note | rev B | M | "It fits its case" stands on a model with 8 TIGHT rows that hang on assumed numbers. No printed part, no test fit. The owner's caliper data is one sample of each part; the rotary's is from a listing photo. | Ladder step 4. |
| 14 | Note | both | M | Keep: the generator check, the red-team of the checks (R1 to R13, closed), the planted-fault test of the HV rule, the fab zips' self-tests. | Keep them in rev C. |

## Detail

Scripts for the numbers below are in the scratchpad folder `audit/evidence/` (`zip_vs_board.py`, `j1_map.py`), not in the repo.
A rule for the whole doc: **a reading by a person or a model is not a check.** A check is the output of ERC or DRC with real
rules, a simulation, or a bench measurement. And a DRC pass proves only the rules that were loaded.

**Sources of the findings.** 1: review:576-590, `PCB/README.md:347-355`, the gates file in `knowledge/`. 2:
`3d/case-pair/checks.md:67`. 3: `PCB/TS06-routing-plan.md:360-372, 539-550` (its own labels: 10 assumed, 19 inferred).
4: `tools/verify_pair.sh:458-520`, `PCB/README.md:319`. 5, 12: the runs in sections 2 and 4. 6:
`tools/verify_pair.sh:495`, `tools/ts06pair.py:398-401`. 7: `zip_vs_board.py`, the fascia's `.kicad_pro`; J1's pin map
equals DRV's (`j1_map.py`), but no standing check holds it. 8: `PCB/TS06-pair-testing.md:461-463`. 9:
`tools/verify_pair.sh:196-277`, `PCB/README.md:362-365`. 10: section 4. 11: claims 6, 8, 10. 13: `checks.md`, section 5.
14: review:432-453. ("review" is the pair review, `TS06-pair-review.md`; "testing" is `PCB/TS06-pair-testing.md`.)

### 1. The claims the product stands on

| Claim | Evidence that exists | Kind | Strength |
|---|---|---|---|
| It works | ERC 0, DRC 0 unconnected, the netlist self-check, the worked numbers in `PCB/TS06-pair-testing.md`. The review's "an independent audit traced every anode" (review:17) is a reading. | Script, calculation | Strong that the files agree. Weak that the circuit works: no simulation, no bench. |
| It is safe | HV clearance by rule (0.6 mm, pads 0.8 mm); a fuse, a TVS and an over-voltage clamp on the BOM; the bleed and clamp numbers. | Script, calculation | Medium for spacing. None for touch, the clamp or the discharge time. |
| It fits its case | `3d/case-pair/checks.md`: 85 rows, 68 OK, 8 TIGHT, 6 NOTE, 3 FAIL (2 by design, 1 open). Caliper sheets. | Model, some measurement | Medium for clearances. None for a real fit. |
| It can be assembled | The strip mate, read from the written files: 63 pins, places, nets, drills, faces. | Script, reading | Strong for the mate. None for hand assembly: no trial build. |
| The order files are right | The zips rebuild the same. Tracks and drills in the zips equal the boards. Pours are filled. | Script | Strong that zip = repo. Medium that a fab can make it: `tools/dfm_check.py` says its limits are inferred. |
| The firmware matches | The table check, `tools/verify_pair.sh:196-277`. | Script | Medium for the tables. Weak for the rest (finding 9). |

### 2. `tools/verify_pair.sh`, check by check

Clean container: **16 PASS, 0 FAIL, 5 SKIP**. With numpy, and the KiCad 10 image in Docker (KiCad 10.0.8):
**27 PASS, 0 FAIL, 0 SKIP**, 83 s. So the review's "27 PASS" (review:65, `PCB/README.md:313`) holds today.

| Check (lines) | What it proves | What it cannot prove |
|---|---|---|
| netlist (1) | Every net has two pads or more. The strips carry the same net on both boards. No net crosses off a strip. | That the circuit is right. Any pin map. |
| mate (1), pair mate from the written files (1) | All 63 strip pins and 4 standoff holes meet: place, net, drill, face. | Real strip heights and tolerances. |
| firmware tables (1) | Digit map, anode order, decoder bits, the expander's address and the bring-up tables equal the netlist. | A compile. The `.hex`. Timing. Ladder thresholds. |
| generator (2) | The committed board, project, library table and footprints are what the generator writes. | That the generator is right. The schematics and the fascia are not in this check; run here, they also come out byte for byte. |
| checkpcb (2) | Pads and courtyards inside the outline; overlaps; accepted items with limits. | Heights. 3D clashes. |
| checkcopper --hv (2) | 0.2 mm everywhere, 0.6 mm round the named HV nets, no vias, every pad touched. | A net not on the list. The pours (the files hold no fill). The 0.8 mm pad rule is off here; run here with `--hv-pad 0.8` and `OVZ_*`, it is clean. |
| audit (2) | Each net is one piece through tracks and pours (a grid model); silkscreen and mask. | The real fill. |
| checksch (2), checkmatch (2), erc (2) | No loose pin. Schematic nets equal board nets. KiCad's ERC: 0. | Independence: both sides come from one netlist, with symbols the same script wrote. |
| drc (2) | KiCad 10, pours refilled, all severities: 0 unconnected; DISP 2 accepted errors, DRV 2 accepted warnings. Rules loaded: 0.2 default, HV 0.6, CATH 0.25, edge 0.5, HV pad 0.8. | Any rule not loaded: creepage, HV to edge or hole, voltage itself. |
| pours (2) | A pour that fills to nothing fails. | Pieces pass: DRV's back GND is 10 pieces, the largest 33 %. |
| HV rule live (2) | A planted 0.70 mm gap is reported, so the custom rule is loaded. | - |
| bom (1), case (1), case outputs (1) | `bom.md` and the case outputs are what their scripts write; the case rows are known. | A full kit BOM. Finding 2. |

**Does any check know which nets are 185 V?** Only by name: `verify_pair.sh:495` (typed), `ts06pair.py:398-401` (the source
of the project class), and the rules file through that class. The cathode nets (up to about 60 V, `mkpcb_drv.py:88`) get
0.25 mm; their 0.5 mm at pads is a soft rule in the generator with no standing check.

**Does any check run KiCad's own DRC with real rules?** Yes, the `drc` lines, with the project's classes and one custom
rule. Not on a clean machine.

**The 5 skips.** Two `audit` lines (numpy). Two `drc` lines. One "pair mate (written files)" line, which also stands for
the two pours, the two "HV rule live" and the two ERC lines (`verify_pair.sh:591-659`). So 11 checks of 27 did not run, and
the exit code was 0.

### 3. Sampled claims, re-derived

| # | Claim (source) | Result | How |
|---|---|---|---|
| 1 | 27 PASS, 0 FAIL, 0 SKIP (review:65) | Holds | Run here with all tools. |
| 2 | Tracks and vias: DRV 1164 / 0, DISP 388 / 0 (`PCB/README.md:323`) | Holds | checkcopper; the zips hold the same 621 + 543 and 53 + 335 draws. |
| 3 | Boards 191.4 x 44 and 191.4 x 40 (brief) | Holds | Outline Gerbers: 191.40 x 44.00, 191.40 x 100.00 (DRV), 191.40 x 40.00. |
| 4 | 63 strip pins (review:23) | Holds | `ts06pair.HEADERS`: 10 + 31 + 5 + 3 + 4 + 4 + 6. |
| 5 | 165.5 V at RP1 = 5 k; 185 V at 2.55 k; span 165 to 210 V (testing:461-469) | Holds; its pass band does not | 2.5 V x 1523 k / 23 k, from the netlist's R62 to R64, RP1, R69, R70. Finding 8. |
| 6 | C7 to 10 V in 8.0 s, tau 2.73 s (testing:497-503) | Holds as a calculation | 4.7 uF x (940 k in parallel with 1.52 M). |
| 7 | C7+ to U12 pin 2 reads 560 to 615 k; 963 k if R62 or R63 is open (page, Test tab) | Holds | 1500 k in parallel with 963 k = 586 k. |
| 8 | 0.84 mm from a 5 V LED line to a 185 V anode pad at the strips (page) | Holds; not the least | `--hv-pad 0.95`: 0.840 at 30 pad faces on DISP and 36 on DRV; the least is 0.830, VD7.1 to VT2.1. |
| 9 | Every cathode pad keeps 0.5 mm (`PCB/README.md:329`) | Holds | checkcopper on the cathode nets, `--hv-pad 0.5`: clean on both boards. |
| 10 | The clamp, 82 + 82 + 75 V, trips at 225 to 270 V (`PCB/TS06-DRV/bom.md`) | Holds as a calculation | 239 V +-5 % is 227 to 251 V; R75 and VT2's base add about 7 V. Zener data assumed. |
| 11 | L1 peaks at 1.27 A (testing, 3e) | Holds as a calculation | Duty 190 (`ts06_bringup.ino:58`), 23.75 us, 11.8 V, 220 uH. Against 1.8 A (BOM text, assumed). |
| 12 | Case 204.4 x 122.8 x 81.6 mm (`PCB/README.md:327`, review:68) | Does not hold | `3d/case-pair/checks.md`: 204.4 x 120.0 x 81.0. |
| 13 | 19 PASS; DRV 95 parts, 130 nets (page) | Does not hold | 27 lines; 108 parts, 136 nets. |
| 14 | 5 V worst case 872 mA, 87 % (`PCB/TS06-routing-plan.md:366`) | Cannot be checked | The sum is right; 20 mA a filament and the clock's own current are not measured. |
| 15 | The stack is 11 mm = 8.5 + 2.5 (testing, bench gates) | Cannot be checked | Two catalogue numbers. Calipers decide. |

Eight hold outright. Three hold as calculations, two of them on part data from memory. Two do not hold. Two cannot be checked from files.

### 4. Stale and missing

* **The page** is older than rev B in its Test tab (claim 13; "4 warnings"; case 83.6 deep). Its Order table loads at run
  time and is not in the snapshot. Its source is `recovered/viewer2/`, a recovered copy.
* **"Ordered":** `fab/ORDER.md:92`, `tools/mkfab.sh` and the page call the fascia zip "the ordered zip". Nothing is ordered.
* **The brief** says 3 decoders and 7 opto-couplers. The netlist has 4 К155ИД1 and 6 TLP627.
* **`verify_pair.sh:31-32`** says its HV list is "the same list as the project's HV net class". On DRV it is not (finding 6).
* **Fab zips from the repo.** `tools/mkfab.sh`, run on a scratch copy with only `tools/`, `fab/` and five `PCB/` folders:
  all three zips rebuild. Each member differs from the committed one only in the date and tool-version lines (10.0.6, then
  10.0.8). Tracks and drill hits in the zips equal the boards, except the fascia by design (finding 7).
* **Files that are gone.** None that the build needs: the 27 checks and the fab build ran from that small copy. What lives
  outside the repo: the KiCad image (a floating tag) and numpy, scipy and Pillow (no versions pinned).

### 5. Measured by the owner, against assumed

**Measured, with calipers, one sample each** (`knowledge/TERMINAL-06-measurements-*.txt`): ИН-12, ИН-17, ИНС-1, the КМД1
button, the МТ1 toggle. **Not measured:** the rotary (a listing photo, by its own sheet). The two sheets at the repo root
are read from the inherited board's Gerbers: exact, but file data, and about the old board. **Electrical measurements:
none.** The gates file lists them as open.

The cheapest assumptions to turn into measurements, cheapest first:

1. The RTC module's pin order and labels (a meter, 5 minutes). It is copper.
2. Mated strip height, the ИН-17 pip and stem, the button's stand-off (calipers).
3. Which lead of the ИН-17 and the ИН-15 is the anode; the sustaining voltage of each tube type (one resistor and an HV
   source). They set copper and R27 to R32, R56, R57 ("6k8 TBC").
4. The 5 V current of a Nano, an RTC module and an expander; one filament at the wanted look (rev C's budget).
5. The PWM chip's outputs from power-on to set-up (a scope, a breakout).
6. The converter on a hand-wired board: set-point span, ripple, L1's peak current, heat, discharge time, the clamp.

### 6. The evidence ladder

**A. Before any board order.**

| Step | Test | Pass mark |
|---|---|---|
| 0 | `bash tools/verify_pair.sh` with all tools, then `bash tools/mkfab.sh` on a copy | 27 PASS, 0 SKIP; zips the same but for date lines. Done here, 2026-11-14. |
| 0b | Simulate the converter and the clamp with the BOM values | Rail 185 V +-5 %; L1's peak under 1.44 A; the clamp holds under 270 V with the feedback open. |
| 1 | The RTC module on a meter | Pad 1 is GND and pad 5 is the module's +, as U13's legend. |
| 2 | Calipers on the parts of the batch | Mated strips 11.0 +-0.3 mm; pip under 6.4 mm; stem 20.0 mm or less. |
| 3 | Each tube type on a rig, one lead at a time, through a resistor | Every lit lead is the footprint's pad of that name; the anode lead is the anode pad. Record the sustaining voltage. |
| 4 | Coupons: the printed trench with a socketed ИН-12; the printed cheek with the jack and a real plug; a 1:1 paper print of the fascia with its parts and the boss; the colon lamps beside an M10 tube | The tube goes in without touching; the plug seats 7 mm or more; the boss clears R5 and SW5 by 0.5 mm or more; the lamps clear the glass. |
| 5 | Rev C on a breadboard: one PWM chip, one P-FET, one filament of each colour, one RGB LED | No light before set-up, with the master switch; the worst-case sum at or under 80 % of the 5 V module. |
| 6 | The converter hand-wired (U12, U11, VT21, L1, VD1, C7, the divider, the bleeder, the clamp), on a 500 mA limit | 165 V +-5 % at RP1 = 5 k; trims to 185 +-1 V; ripple 1.5 V p-p or less; no part over 60 C after 30 min at 10 mA load. |
| 7 | The same board, supply off | Under 10 V in 6 to 11 s. |
| 8 | The same board, U12 out | The rail holds between 225 and 270 V. |

**B. One prototype set, before the batch.**

| Step | Test | Pass mark |
|---|---|---|
| 9 | Bare boards: insulation at 500 V DC, HV185 to GND and across the strips' HV neighbours, before any part | 100 M or more; no flash-over in 60 s. |
| 10 | The test plan's stages 1 to 8, with finding 8 corrected, and its record sheet filled | Every stage passes; the codes on A6 and A7 are read on the real panel and lead. |
| 11 | 48 h soak in the closed case | No reset, no ghosting; the hottest part under 70 C. |

The pass marks of steps 0b, 4, 5, 6, 9 and 11 that are not in the repo's docs are *assumed*: the owner sets them.

## Reconsider

| Choice | Today | Starting today | Cost of changing | Call |
|---|---|---|---|---|
| Where the design lives | Scripts write the boards, schematics and BOM. KiCad files are output. | The same, for a design that scripts change: it gives byte-for-byte rebuilds and checks on the source, which a hand-drawn project cannot. | For rev B: all of the re-check work, for no gain. | **Keep.** |
| Symbols and pin maps | Typed in the scripts. | KiCad's stock library symbols and footprints wherever they exist: a second source for every pin map. | Small, part by part. | **Change in rev C.** |
| The rules | Classes by name pattern; one custom rule; a second, custom copper checker. | A fuller rules file as the one gate: HV pad, HV to edge and hole, creepage; classes derived from the netlist. The custom checker stays as a second opinion. | One day. | **Change in rev C.** |
| The gate | SKIP passes; tools not pinned. | SKIP fails; image and packages pinned; the run on every push. | Hours. No board file changes. | **Change now.** |
| Pour fill | Not in the committed boards; made at export. | Commit the filled boards, so every file check sees the copper that is made. | One run, larger diffs. | **Change in rev C** (grill G8, the owner's). |
| Order of proof | Files first, bench later. | Bench first for what decides copper. | An evening or two. | **Change now:** ladder A. |
| A release copy for buyers | None. | A plain KiCad project, frozen at release, that a buyer can open and check. | Small, once. | **Change later.** |

## Not checked

* Route quality and my own measure of HV distances: left to the layout and routing runs.
* Part data sheets: no web fetch was made. Ratings of the zeners, the opto-coupler, the FET and L1 are from the repo's text or
  from memory: *assumed, not re-checked*.
* The commits the docs cite (78105d6, 2dc04ec, 77e3b11, 3222f27): this clone is shallow, 51 commits; none resolves here.
* The page's Order table and Facts (loaded at run time); the `recovered/viewer2` build.
* A firmware compile (no compiler here). `tools/dfm_check.py` was not run.
* The art faces and five of the six grills; the `qa/` pictures; the case geometry beyond `checks.md`.
