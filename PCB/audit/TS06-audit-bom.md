# TS06 audit: the BOM and the circuit, as a product (run audit-bom)

Audited: commit 8e030d4 on `pcb/kicad-boards`, 2026-11-14. Rev B means the repo as it is. Rev C means `PCB/TS06-routing-plan.md`.
Evidence classes: *measured* (computed from the files), *inferred*, *assumed* (part data from memory, not re-checked: both web
fetches failed, see Not checked). My two scripts are outside the repo, in the session scratchpad, folder `audit/bom/`:
`stress.py <repo>` (every number in sections 1 to 3) and `pins.py <repo>` (section 9).

## Verdict

1. Rev B's circuit holds on paper. Every part on the 185 V side is inside its rating, the rail has its own clamp and bleeder, and
   the pad nets of all 146 footprints equal the netlist. I found no Stop.
2. It is not ready to order. Four things can still change a board or a purchase: tube brightness at six slots, three pin
   identities that no real part has confirmed, the tube socket contact, and four sockets missing from the BOM.
3. Rev C's lights load the one 5 V module to 87 to 94 % and can be fed from a USB port by mistake. Give the lights their own
   5 V module, and put the surface-mount parts on a small plug-in board.

## Findings

| # | About | Severity | Finding | Fix |
|---|---|---|---|---|
| 1 | rev B | Fix before order | ИН-12 brightness at six slots is not proven: 13.5 % duty, 5.7 mA peak, 0.77 mA mean, 31 % of the rated 2.5 mA. The decoder's 7 mA limit leaves no room. Open since 30.09 (E6) | Bench it this week on the old clock (section 6). If dim: take the seconds pair out of the multiplex in rev C |
| 2 | rev B | Fix before order | The anode lead of ИН-17, the anode pad of ИН-15 and the RTC module's pin order rest on web sheets, not on a part (gates 3, 4, 6 open). A wrong anode is a new board | Do gates 3, 4 and 6 with real parts first |
| 3 | rev B | Fix before order | The tube socket contact (72 a unit) is not chosen. DISP's 1.2 mm holes were sized for the tube pin (M5 open) | Choose the contact by type, measure its tail, then fix the drill |
| 4 | rev B | Fix before order | The BOM lost the four DIP-16 sockets of U2, U15, U16, U17. `tools/bom_pair.py:69` does not know the `_Oval` footprint | One entry in `SOCKETS`; rebuild the BOM |
| 5 | rev B | Should fix | C7 carries 95 mA rms at 31 kHz. The BOM says only "4u7 400V". C8 is in the same state. Open since 30.09 (E7). C7 is the part I expect to fail first | Name the class: 105 °C, low impedance, 200 mA or more at 100 kHz. C8: low impedance, 300 mA or more |
| 6 | rev B, rev C | Should fix | USB alone feeds the 12 V rail through VD3, at about 4.3 V. The converter then runs with its driver under its 4.5 V minimum, and all loads draw through the Nano's USB diode | Rev B: a rule in the manual. Rev C: U12's spare half as a 12 V under-voltage lock on PWM_G, two resistors |
| 7 | rev B | Should fix | L1 saturates above about 15 to 16.7 V in. Nothing acts between 15.3 V and the TVS (17.1 to 18.9 V). No BOM names the adapter | Put a regulated 12 V adapter on the BOM by its figures: 1.5 A (rev C: 2 A) |
| 8 | rev B | Should fix | Against a 19 to 24 V adapter, VD4 is a part that dies to save the rest. A 24 V 1 A adapter never trips F1 | Say so in the manual; label the jack; ship the adapter |
| 9 | rev B | Should fix | A steady high on D9 holds the switch on. Only F1 limits the current, and it takes seconds. The firmware has no watchdog | Rev C: couple D9 through a capacitor, so only edges switch |
| 10 | rev B | Should fix | The anti-poisoning sweep is compiled out (`BURN_ENABLED 0`). When on, each cathode gets 30 ms in 15 minutes. The ИН-15s are not in it | Turn it on, make it seconds per cathode, add the ИН-15s |
| 11 | rev B | Should fix | The firmware for the pair is not finished: the default build is `BOARD_TYPE 0`, the ИН-15s stay dark, A7 is not read | Finish it before a kit is sold. It does not block a board order |
| 12 | rev B | Should fix | The clamp's 225 to 270 V window is computed only. 270 V is 90 % of the 300 V parts. The snubber (E12) and bleeders (E13) are open too | Breadboard the zener string before first power; the rest on the first pair |
| 13 | rev C | Fix before order | One 1.0 A module carries 872 to 940 mA. F1 runs at 77 to 81 % of its hold current at 55 °C. USB could be asked for 0.9 A | A second 5 V module for the lights only; F1 at 1.6 A hold |
| 14 | rev C | Should fix | Two TSSOP-28 chips and ten SOT-23-6 parts enter a through-hole kit. No rev C part has a type number or a BOM line yet | A small plug-in light board, machine-assembled. Write its BOM |
| 15 | both | Note | Old and single-source parts: section 4, with spares for ten units | Buy the batch's old-stock parts at once, test each |
| 16 | both | Note | A seller's least duties for safety and EMC: section 7 | Owner's decision |
| 17 | rev B | Note | The eight backlight LEDs draw about 72 mA through the expander (limit 125 mA, *assumed*). VT20 runs at 95 mA, outside its stated saturation point | None: rev C removes both |
| 18 | rev B | Note | A shorted ИН-15 puts 1.9 W into a 0.5 W resistor | None: a fault case, the part chars and opens |
| 19 | both | Note | Pin maps: 12 part types agree with the data sheets as I remember them. ИН-17 is not checked | Section 9 |
| 20 | both | Note | The brief's counts are old: it says 3 decoders and 7 opto-couplers. The repo has 4 and 6 | Correct the brief for the next runs |
