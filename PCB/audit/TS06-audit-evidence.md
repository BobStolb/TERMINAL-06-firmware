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
| 8 | Should fix | rev B | M | The test plan's stage 3b pass band, 145 to 160 V, shuts out its own computed value, 165.5 V. A good board fails the step. | Correct the band: about 158 to 173 V. |
| 9 | Should fix | rev B | I | "The firmware matches" is proven for tables only. Nothing compiles the sketch. The committed `.hex` is not tied to the source. The A6 and A7 ladder thresholds are calculated. The lever code on A7 is not written. | Compile in the check run; delete the `.hex` or stamp it; measure the ladder (ladder step 9). |
| 10 | Should fix | docs | M | Stale numbers: the page (19 PASS; DRV 95 parts, 130 nets; case 83.6 deep; 4 DRC warnings); the README and the review (case 122.8 x 81.6; today 120.0 x 81.0); the word "ordered" in `fab/ORDER.md`, `tools/mkfab.sh` and the page, against the owner's "not ordered yet". | Write these numbers into the docs from the check run. Say "to order". |
| 11 | Note | rev B | M, A | The safety numbers are calculations: C7 down to 10 V in 8.0 s; the clamp at 225 to 270 V; the 0.8 mm HV pad gap, met with 0.83 to 0.84 mm in about 70 places. None is measured. | Ladder steps 6 to 8. |
| 12 | Note | rev B | M | The committed boards hold no pour fill, so the copper that goes to the fab is made by the KiCad version of the day. Today's rebuild equals the committed zips; `mkfab.sh` would still rewrite all three (the version line). | Pin the image. Treat the version line as a date line. |
| 13 | Note | rev B | M | "It fits its case" stands on a model with 8 TIGHT rows that hang on assumed numbers. No printed part, no test fit. The owner's caliper data is one sample of each part; the rotary's is from a listing photo. | Ladder step 4. |
| 14 | Note | both | M | Keep: the generator check, the red-team of the checks (R1 to R13, closed), the planted-fault test of the HV rule, the fab zips' self-tests. | Keep them in rev C. |
