# TS06 audit: the report

Run audit-report, 2026-11-14 UTC. It joins the four audits in `PCB/audit/`: evidence (E), layout (L), BOM (B), routing (R).
They read `pcb/kicad-boards` at 8e030d4. Rev B is the repo. Rev C is the plan, `PCB/TS06-routing-plan.md`.
M = measured from the files, I = inferred, A = assumed. Costs are A.

## Verdict

1. **No Stop.** Rev B is sound as files: 27 checks pass, KiCad's DRC and ERC are clean, the fab zips match the repo.
2. **Nothing is proven as hardware.** No board was built. No voltage was measured. Every part rating is from memory.
3. **Do not order rev B as it is.** First: two track moves, three footprints, a BOM repair, five bench tests.
4. **Then order one small lot and build one set.** Not ten.
5. **Rev C is a plan on unmeasured inputs.** It needs its own 5 V supply for the lights, a new strip pin map and a new
   routing method.

## Can rev B be ordered as it is?

**No.** Findings 1 to 5 below. None is a Stop.

* Two bare pads are too near 185 V tracks.
* Three pin orders were never tried on a part. The tubes are soldered in: a wrong pin costs tubes and a board.
* The converter has no snubber pads. Brightness at six multiplex slots is unknown. The BOM has holes.

After steps 1 to 11: yes, as one bring-up set.

## Next steps, in order

**Bench first.**

1. [ ] RTC module on a meter. Pass: pad 1 is GND, pad 5 is its +.
2. [ ] Calipers. Mated strips: 11.0 ±0.3 mm. ИН-17: pip under 6.4 mm, stem 20.0 mm or less. The button's stand-off
   behind a 2.0 mm panel.
3. [ ] Each tube type on a rig, one lead at a time, through a resistor. Pass: every lit lead, and the anode, is the
   pad of that name. Note the sustaining voltage.
4. [ ] The old clock with `INDI_BRIGHT 14` and 6k8 anode resistors, in daylight. Bright enough?
5. [ ] The clamp on a breadboard, on a current-limited supply. Pass: it holds 225 to 270 V.
6. [ ] For rev C: the 5 V current of the clock; one filament; the PWM chip's outputs at power-on.

**Then the files.**

7. [ ] Make the 0.8 mm rule two-way (`.kicad_dru`, `tools/checkcopper.py`). Move the two tracks. Plant a fault to
   prove the rule.
8. [ ] DRV: three unfitted footprints beside VT21 and C7. Test points where they fit.
9. [ ] BOM: four DIP-16 sockets back; 72 socket contacts out; C7 and C8 by class; a 12 V adapter.
10. [ ] "Straight in" in every doc (list below). Case model: `IN12_SEAT` 2.0, fascia R rev B as its fascia. Re-run it.
11. [ ] Check run: SKIP fails; KiCad image pinned; open items counted; the fascia in the run, committed as ordered.
    Test plan stage 3b: 157 to 174 V. Rebuild the zips.

**Then hardware.**

12. [ ] Coupons: the fascia on paper, 1:1, with its parts; a printed trench with an ИН-12 at 2.0 mm; the jack cheek
    with a real plug.
13. [ ] Order one small lot of rev B. Bare boards: 500 V DC from HV185 to GND, 100 MΩ or more (A).
14. [ ] Build one set by `PCB/TS06-pair-testing.md`, stages 1 to 8. Fit the snubber if the converter rings.
15. [ ] 48 h in the closed case. Then decide rev C.

## The top ten

| # | Finding | Fix and cost |
|---|---|---|
| 1 | **Fix before order**, rev B. Unproven on parts: ИН-17 leads, ИН-15 anode, RTC module pins, the 11 mm stack. (E1, B2; I) | Steps 1 to 3. An evening |
| 2 | **Fix before order**, rev B. DRV pads XS23.4 and R44.2 are 0.65 and 0.70 mm from 185 V tracks. The 0.8 mm rule looks one way, so every check passes. (L1 = R1; M) | Step 7. Hours; a new DRV zip |
| 3 | **Fix before order**, rev B. ИН-12 brightness at six slots: 13.5 % duty, 31 % of the rated mean current. (B1; M) | Step 4. 30 minutes |
| 4 | **Fix before order**, rev B. No pads for a snubber or a film capacitor across C7. C7's ripple class is not named. The clamp is computed only. (L2, B5, B12; M, I) | Steps 5, 8, 9. Hours |
| 5 | **Fix before order**, rev B. The BOM cannot build a unit: four DIP-16 sockets lost, 72 unwanted contacts, no adapter. (B3, B4; M) | Step 9. An hour |
| 6 | **Should fix**, both. On a clean machine 11 of 27 checks skip and the run exits 0. HV nets are a typed name list. (E5, E6, R9; M) | Step 11. Rev C: a check that walks out from HV185 |
| 7 | **Should fix**, rev B. The fascia to be ordered is no board in the repo and is not in the check run. (E7, L5; M) | Step 11 |
| 8 | **Fix before order**, rev C. Lights: 872 to 940 mA on one 1.0 A module, through a 0.1 to 0.4 ohm tree. The 185 V reference is half of that rail, so the tubes' voltage moves with the lights. (L3 = B13; M, I) | A second 5 V module, its own 1.0 mm feed and return. 4 USD a unit |
| 9 | **Fix before order**, rev C. The router cannot place a via; the new block is surface-mount, beside the feedback node. On four strips an anode pin is 0.84 mm from a 5 V pin. (R2, B14, L10, L4; M, I) | A plug-in light board, or DRV routed in KiCad with a rules file. Re-pin the strips. 2 to 4 days |
| 10 | **Should fix**, rev B. On USB alone the converter runs at 4.3 V. D9 stuck high leaves only F1. A 15 to 17 V adapter saturates L1. The anti-poisoning sweep is off. (B6 to B11; I) | Manual rules, a named adapter. Two guards in rev C. Firmware: days |

Also: no test points, no values on the silk (L6, L7): with step 8.

## Where the audits disagree, and my call

* **The `case` line** prints PASS with 3 FAIL rows inside. Two are jack openings the owner already rejected. One is
  open: the fascia boss on R5's pad (E2). Layout says the board is clear (L8). **Call: layout.** Fascia R has R5 at
  (12.89, 35.2) and H3 at (4.5, 35.5): 2.04 mm clear (M, re-read). The case model reads the old fascia,
  `PCB/TS06-FASCIA/`. Step 10 closes the row.
* **The tube socket contact.** B3: "not chosen". **Call: settled.** The owner, 2026-10-12: "straight in". No contact;
  the 1.2 mm holes fit the pins. Pin 6.0 mm, gap 2.0 mm by a jig (parked P7).
* **The converter before the order.** Evidence: hand-wire all of it first. BOM: only the clamp. **Call: BOM.**
  Hand-wired ringing does not carry over to a board.
* **5 V for the lights.** A wide feed from the one module (L3), or a second module (B13). **Call: both.**
* **Where copper lives.** Evidence: keep the scripts. Routing: KiCad for DRV rev C. **Call:** scripts for rev B and DISP;
  DRV rev C's block in KiCad, or on a plug-in board.

**Still carrying the socket choice:**

* `PCB/TS06-DISP/bom.md:26`, from `tools/bom_pair.py:113`: 72 contacts.
* `PCB/TS06-pair-testing.md:684` and `:858`: "socketed ИН-12".
* `3d/case-pair/case_pair.py:290`, `checks.md:149`: `IN12_SEAT` 4.5. At 2.0 the case is 78.5 mm deep, not 81.0 (M).
* The page's build steps: `recovered/viewer2/src/app.js:1196-1263`.
* `tools/models3d.json:21`, `3d/populated/README.md:26`; the pair review's M5.

New with "straight in": a soldered tube does not come out. Light every tube on the rig first.

## The plan's ten October decisions (section 6)

* **As they are:** 1 (the button: now step 2), 2 (the fascia's base), 4 to 8.
* **3, the second PWM chip: changed.** It needs the second 5 V module, and it adds twelve fine-pitch parts to a
  through-hole kit. New question: a plug-in light board.
* **9, the case sill and variant D: changed.** The case gets 2.5 mm shallower. Decide after step 10.
* **10, the order: settled in part.** Rev B: after steps 1 to 11, as one bring-up set. The coupon was not audited.
* Outside section 6: the plan gives strip pin XS25.3 to a light. Do not: it is the only gap beside an anode (L4).

## Reconsider

| Choice today | Call, and its cost |
|---|---|
| K155ID1 and TLP627, multiplexed | **Keep.** A high-voltage serial driver only for a later product line |
| Six multiplex slots | **Change in rev C** if step 4 says dim: ИН-17s steady, four slots. One K155ID1 |
| Converter clocked by the Nano | **Keep.** Rev C: a 12 V lock, D9 through a capacitor |
| Nano module, 12 V jack, through-hole | **Keep.** The adapter goes on the BOM |
| One 5 V module | **Change in rev C:** a second one for the lights |
| Rev C lights as surface-mount on DRV | **Change in rev C:** a plug-in board, machine-assembled |
| Split boards, pin strips | **Keep.** Re-pin in rev C |
| Two layers, zero vias, ground as a routed tree | **Keep** on DISP. **Change in rev C** on DRV: pours first, stitched with vias, checked |
| 185 V spacing: 0.6 mm, 0.8 mm at HV pads only | **Change now:** 0.8 mm at any pad. Rev C: 1.0 / 1.25 mm, a creepage rule |
| Boards written by scripts | **Keep** for rev B and DISP. Do not extend the router |
| Pin maps typed in scripts | **Change in rev C:** stock library symbols as a second source |
| The check gate; boards saved unfilled | **Change now.** Hours (grill G8 is the owner's) |

## The owner's decisions

1. One rev B bring-up set first, or wait for rev C.
2. Rev C lights: on DRV, or a plug-in board. A second 5 V module.
3. The seconds pair out of the multiplex, if step 4 says dim.
4. A kit or a finished unit. Ship the 12 V adapter, or name one.
5. Rev C spacing at 185 V: 0.8 mm, or 1.0 / 1.25 mm.

## How far to trust this audit

* **Measured by real tools:** KiCad 10.0.8 DRC and ERC; the repo's check run, 27 PASS, 0 FAIL, 0 SKIP today; the fab
  zips rebuilt and compared; distances and widths computed from the board files.
* **A model's reading:** the severities, the stress tables, the costs, every rev C call. The audits are model runs,
  like the reviews before them. Expect shared blind spots.
* **From memory:** every part rating and spacing-standard value. Two data sheet sites were blocked. Check first:
  TLP627, the 5 V module, F1.
* **Not done:** a bench measurement, a simulation, a firmware compile.
* Outside write-ups on model-run board reviews (vendor claims only, no independent test) say:
  1. Run the real ERC and DRC and read the output. Done.
  2. A clean DRC proves only the rules that were loaded. Finding 2 is a live case.
  3. ERC and DRC do not see a wrong pin map. Check each pin against the data sheet and the part: steps 1 to 3.
  4. The vendor's own boards still had to be built and tested by people. So must this one.

## Not checked

* A fresh route of DRV. KiCad's creepage DRC on DRV (it did not finish). The art faces, the grills, the coupon.
* The page's Order tab. Parked P2 says it names the rev A fascia zip: order from `fab/ORDER.md`.
* Re-run here: only the case what-if and R5's place.
