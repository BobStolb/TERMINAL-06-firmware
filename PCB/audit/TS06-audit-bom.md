# TS06 audit: the BOM and the circuit, as a product (run audit-bom)

Audited: commit 8e030d4 on `pcb/kicad-boards`, 2026-11-14. Rev B is the repo as it is. Rev C is `PCB/TS06-routing-plan.md`.
Classes: *measured* (computed from the files), *inferred*, *assumed* (part data from memory; see Not checked). My scripts are
in the session scratchpad, folder `audit/bom/`: `stress.py` (sections 1 to 3), `pins.py`, `rot.py`, `mate.py` (section 9).

## Verdict

1. Rev B's circuit holds on paper: every 185 V part is inside its rating, the rail has its own clamp and bleeder. No Stop.
2. It is not ready to order: brightness at six slots, three unproven pin identities, the socket contact and four lost sockets.
3. Rev C's lights load the one 5 V module to 87 to 94 % and can draw from USB: give them their own module.

## Findings

| # | About | Severity | Finding | Fix |
|---|---|---|---|---|
| 1 | rev B | Fix before order | ИН-12 brightness at six slots is not proven: 13.5 % duty, 5.7 mA peak, 0.77 mA mean, 31 % of the rated 2.5 mA. The decoder's 7 mA limit leaves no room (E6, open) | Bench it on the old clock (section 6). If dim: seconds pair out of the multiplex in rev C |
| 2 | rev B | Fix before order | ИН-17's anode lead, ИН-15's anode pad and the RTC module's pin order rest on web sheets, not on a part (gates 3, 4, 6). A wrong anode is a new board | Do the three gates with real parts first |
| 3 | rev B | Fix before order | The tube socket contact (72 a unit) is not chosen. DISP's 1.2 mm holes were sized for the tube pin (M5) | Choose it by type, measure its tail, then fix the drill |
| 4 | rev B | Fix before order | The BOM lost the DIP-16 sockets of U2, U15, U16, U17: `tools/bom_pair.py:69` does not know the `_Oval` footprint | One entry in `SOCKETS`; rebuild the BOM |
| 5 | rev B | Should fix | C7 carries 95 mA rms at 31 kHz; the BOM says only "4u7 400V". C8 likewise (E7, open). I expect C7 to fail first | Name the class: 105 °C, low impedance, 200 mA or more at 100 kHz; C8 300 mA |
| 6 | both | Should fix | USB alone feeds the 12 V rail through VD3, at about 4.3 V. The converter runs with its driver under its minimum; all loads draw through the Nano's USB diode | Rev B: a rule in the manual. Rev C: U12's spare half as a 12 V lock on PWM_G |
| 7 | rev B | Should fix | L1 saturates above 15 to 16.7 V in. Nothing acts between 15.3 V and the TVS (17.1 to 18.9 V). No BOM names the adapter | A regulated 12 V adapter on the BOM: 1.5 A (rev C: 2 A) |
| 8 | rev B | Should fix | Against a 19 to 24 V adapter VD4 dies to save the rest. A 24 V 1 A adapter never trips F1 | Say so in the manual; label the jack; ship the adapter |
| 9 | rev B | Should fix | A steady high on D9 holds the switch on. Only F1 limits the current, in seconds. No watchdog | Rev C: D9 through a capacitor, so only edges switch |
| 10 | rev B | Should fix | The anti-poisoning sweep is compiled out. When on, a cathode gets 30 ms in 15 minutes. The ИН-15s are not in it | Turn it on; seconds per cathode; add the ИН-15s |
| 11 | rev B | Should fix | The pair's firmware is not finished: default build `BOARD_TYPE 0`, ИН-15s dark, A7 not read | Finish before a kit is sold. Does not block a board order |
| 12 | rev B | Should fix | The clamp's 225 to 270 V window is computed only; 270 V is 90 % of the 300 V parts. E12 and E13 are open too | Breadboard the zener string now; the rest on the first pair |
| 13 | rev C | Fix before order | One 1.0 A module carries 872 to 940 mA. F1 runs at 77 to 81 % of its hold at 55 °C. USB could be asked for 0.9 A | A second 5 V module for the lights; F1 at 1.6 A hold |
| 14 | rev C | Should fix | Two TSSOP-28 and ten SOT-23-6 parts enter a through-hole kit. No rev C part has a type or a BOM line | A plug-in light board, machine-assembled. Write its BOM |
| 15 | both | Note | Old and single-source parts, with spares for ten units | Section 4. Buy the batch at once, test each part |
| 16 | both | Note | A seller's least duties for safety and EMC | Section 7. Owner's decision |
| 17 | rev B | Note | The eight LEDs draw about 72 mA through the expander (limit 125 mA, *assumed*); VT20 at 95 mA is outside its stated saturation point | None: rev C removes both |
| 18 | rev B | Note | A shorted ИН-15 puts 1.9 W into a 0.5 W resistor | None: a fault case |
| 19 | rev B | Note | Pin maps: every pad net equals the netlist, all 63 strip pins mate, 14 part types agree with the data sheets as I remember them. ИН-17 and ИНС-1 not checked | Section 9 |
| 20 | both | Note | The brief says 3 decoders and 7 opto-couplers. The repo has 4 and 6 | Correct the brief |

## 1. The 185 V side, part by part (rev B)

D9 clocks the converter: 31.4 kHz, on-time 23.75 µs, fixed by `DUTY 190` (`nixieClock_TS06.ino:47`). The comparator only lets
pulses through or stops them, so the peak is input voltage x on-time / L at any load. The load is 10.5 mA, 1.94 W: 31 % of the
pulses are used; the stage can give 6.2 W (*measured*; tube voltages *assumed*).

| Part | Stress | Rating (*assumed*) | Verdict |
|---|---|---|---|
| VT21 IRF840 | 185 V (270 in a fault), 1.30 A peak, about 0.3 W | 500 V, 8 A | Wide margin, no heatsink |
| VD1 HER106 or UF4007 | 185 V, 1.30 A peak, 10.5 mA mean | 600 or 1000 V, 1 A, fast | Good |
| L1 5900-221-RC | 1.30 A at 12 V; 1.51 A at 12.6 V with L 10 % low | 1.8 A | 72 to 84 %; over at 16.7 V in |
| C7 4u7 400 V | 185 V, 95 mA rms | 400 V; ripple not stated | Finding 5 |
| R60-R63 (bleeder, divider) | 91 to 93 V, under 20 mW each | 350 V, 0.5 W | Good |
| R27-R32 (multiplexed anodes) | 224 mW at the peak, 30 mW mean | 0.5 W | Good; 6k8 still "TBC" |
| R56, R57 18k (ИН-15) | 113 mW steady | 0.5 W | Good |
| R58, R59 220k (colon) | 185 V before the lamp strikes, 77 mW lit | 350 V, 0.5 W | Good |
| U5-U10 TLP627 | up to 185 V off, 5.7 mA peak, LED 8.2 mA | 300 V, 150 mA | 62 %; 90 % at the clamp's top |
| VT1 MPSA42 (colon) | 185 V off, 1.2 mA | 300 V | 62 % |
| K155ID1 outputs | off: at their own clamp, 60 to 70 V; on: 5.7 mA peak | 60 V at least, 7 mA | By design; 81 % of the current |

* **The clamp (finding 12).** With U12 out, the rail sits at 244 V typical, 270 V at worst (`tools/ts06pair.py:377-386`,
  computed there). At 244 V an ИН-12 peak is 14 mA, twice the decoder's limit (*measured*): fine for a fault, not for long. The
  three zeners, two resistors and VT2 can be tried on a breadboard, with a current-limited supply, before any board exists.

## 2. The 12 V input and the 5 V rail

| | 5 V load | Of the 1.0 A module | Input | At 12 V | Of F1's hold, 23 / 55 °C |
|---|---|---|---|---|---|
| Rev B, all on | 239 mA | 24 % | 3.8 W | 0.32 A | 29 / 40 % |
| Rev C, plan's 872 mA | 872 mA | 87 % | 7.4 W | 0.62 A | 56 / 77 % |
| Rev C, plan's 940 mA | 940 mA | 94 % | 7.8 W | 0.65 A | 59 / 81 % |

*Measured* from the netlist; efficiencies (89 %, 78 %) and F1's hold at 55 °C (73 %) are *assumed*.

* **Rev C is tight (finding 13).** The plan says the firmware's LED cap "is a must" (`TS06-routing-plan.md:373`). A regulator
  should not depend on firmware to stay inside its rating. A second 5 V module for the lights fixes the margin, spreads the
  heat, and closes the USB path below.
* **The USB path (finding 6).** VD3 stops USB from lifting U14's output above its input (E5). Its side effect: with USB in and
  12 V out, the 12 V rail sits near 4.3 V (*inferred*). The firmware starts D9 at every boot (`1_setup.ino:53-61`) and cannot
  know 12 V is absent. The driver runs below its 4.5 V minimum (*assumed*), the switch is half on, the peak is at most
  0.47 A (*inferred*). All of it flows through the Nano's USB diode, a 0.5 A part on most modules (*assumed*).
* **The fix is two resistors.** U12's second half is parked (`tools/ts06pair.py:355`). Make it compare the 12 V rail, divided,
  with VREF, output on PWM_G: below about 10 V the converter stays off, in hardware.

## 3. Protection

| Threat | What acts | Result | Class |
|---|---|---|---|
| A short on the board | F1, 1.1 A hold | Trips, resets | *inferred* |
| Plug reversed | VD2 blocks; VD4 conducts forward, F1 trips | Safe | *inferred* |
| 19 to 24 V adapter | VD4, then F1 | Finding 8 | *inferred* |
| Unregulated "12 V" at 15 to 17 V | nothing | L1 at 90 to 110 % of saturation | *measured* |
| Feedback open, U12 absent | zener clamp on PWM_G | 225 to 270 V | computed in the repo |
| D9 stuck high | F1 only | Finding 9 | *inferred* |
| Power off | R60 + R61, and the divider | 185 to 60 V in 3.1 s; 8.0 s on the divider alone | *measured* |
| A finger on the rail | the case only | 185 V, 80 mJ in C7 | section 7 |

* **Finding 8.** VD4 stands 5 W steady (*assumed*). A 19 V 3 A adapter gives it about 50 W until F1 opens, which takes seconds
  (*assumed*). VD4 fails short: the clock is safe and dead. With VD4 at the top of its tolerance a 19 V adapter trips nothing:
  the rail sits at 18.6 V and L1 peaks at 2.0 A (*measured*).
* **Finding 9.** With the switch held on, the current is 12 V over about 1.2 ohm. A reset is safe: the pins float and R71
  holds PWM_G low. A hang is safe: the timer keeps running. The risk is a sketch that writes D9 high, and kit buyers write
  sketches.

## 4. Old, single-source and module-only parts

| Part | A unit | Risk for ten units | Second source | Buy for ten |
|---|---|---|---|---|
| K155ID1 | 4 | Old stock only; dead or re-marked chips | The 74141 family under its other old names. None new | 50, each tested |
| ИН-12А | 4 | Old stock, price rising | ИН-12Б (its comma pin meets the unused pad 8, *inferred*) | 46 |
| ИН-17 | 2 | Old stock, fragile leads | None with this shape | 24 |
| ИН-15А, ИН-15Б | 1 + 1 | The scarcest tubes here | None | 12 + 12 |
| ИНС-1 | 2 | Low | Any small neon, with a new ballast value | 24 |
| TLP627 | 6 | The BOM calls it obsolete and names a later suffix: not re-checked | 300 V Darlington opto-couplers in DIP-4 (LTV-852, EL852 class, *assumed*; check the turn-off tail) | 66 |
| Nano module | 1 | Clones differ: USB chip, diode, even the processor | Many makers; ask for ATmega328P by name | 12 |
| DS3231 mini module | 1 | Module-only; soldered cell, may arrive flat | None with this pin order | 12, cells measured |
| R-78E5.0-1.0 | 1 | One maker | Other 78xx-pinout switching modules; check pinout and input range | 11 |
| 5900-221-RC | 1 | One maker; own footprint | None that drops in at 1.8 A | 12 |
| Rotary, levers, buttons | 1, 2, 2 | Old stock; worn contacts shift the ladder | New panel parts, other bushing sizes | 12, 24, 24 |

## 5. Completeness, count and cost

* **Count (*measured*).** DRV 96 fitted parts and 12 empty places; DISP 26; fascia R 14; 606 plated holes on the pair.
* **Missing or loose:**
  * four DIP-16 sockets (finding 4); `PCB/README.md:232` says every chip is socketed;
  * the adapter; C7's and C8's class; a voltage for C3 and C11;
  * the socket contact and the ИН-17 spacer, as type numbers;
  * the fascia resistors' tolerance: the firmware's thresholds assume 1 % (`ts06pair.ino:21`);
  * the control wiring, the knob, the case parts, inserts and screws: they are in `3d/`, on no BOM;
  * one product BOM for three boards, case and hardware. Today: three files, two formats;
  * every rev C part. The plan says "no part chosen" (`TS06-routing-plan.md:128`).
* **Rough cost for one unit in USD, all *assumed*, no quote:** tubes and lamps 70; chips, modules, semiconductors 35;
  passives, L1, fuse 12; sockets, strips, contacts, jack, lead 18; three boards at ten sets 15; controls and knob 15; case
  and hardware 12; adapter 7. **About 185.** Ten units: about 1850, plus 150 of spares. Rev C's lights: about 30 more a unit.
  Tubes are near 40 % of the cost: their spares policy matters most.

## 6. Life and use

* **Brightness (finding 1).** Six slots: 21 lit ticks of 26, 13.5 % a tube, 50 Hz (*measured*). The old clock was judged at
  four slots, 20.2 %. A test with no new part: on the old clock set `INDI_BRIGHT 14`, which is 14 / (26 x 4), the same
  13.5 %. Fit 6k8 anode resistors. Look at it in daylight.
* **If it is dim.** Rev C frees the expander's port B (`TS06-routing-plan.md:344`). Give each ИН-17 its own decoder from that
  port, lit steadily through about 30k, as the ИН-15s are. The multiplex returns to the four slots proven on the bench. Cost:
  one more K155ID1, two fewer TLP627.
* **Poisoning (finding 10).** H10 shows only 0, 1, 2. Each ИН-15 will show one sign twelve hours a day. The sweep is off
  (`nixieClock_TS06.ino:113`) and lasts 0.3 s when on (`func.ino:13-25`). Practice is seconds per cathode, several times a
  day (*assumed*).
* **C7.** At 95 mA rms a general 85 °C part will not last (*inferred*). A 105 °C low-impedance part in the same can will.
* **Heat.** 3.8 W in the case today, up to 7.8 W in rev C: about 5 K and 10 K at the case surface (*inferred*: 0.09 m²,
  9 W/m²K). Print in PETG, as `3d/case-pair` says; PLA softens near 55 °C (*assumed*).
* **What fails first:** an old-stock chip or tube at first power; C7, if a general part; poisoned cathodes within months, if
  the sweep stays off; the Nano's USB socket; the RTC cell, after years.

## 7. Product safety and EMC, in plain terms

All *assumed*; not legal advice. The input is 12 V, so the mains rules bite on the adapter. The clock still makes 185 V at
10 mA with 80 mJ stored: more than a person should touch. The least a seller should do:

1. Sell it with, or name, a certified 12 V adapter. It is the barrier to the mains.
2. Close the case: no finger reaches a board with the power on. Check the rear vents and the gaps beside the fascia.
3. Print "185 V" on DRV and the rear panel. State the wait after unplugging: 10 seconds.
4. Put the bring-up rules of `PCB/TS06-pair-testing.md` section C0 at the front of the manual.
5. Fit the fuse, the clamp and the bleeder in every unit, never as options.
6. Listen for the converter on a radio near the adapter lead. If heard: the snubber (E12) and a ferrite on the lead.
7. Say what is in the box: old-stock tubes and chips with lead in their coatings, a lithium cell on the RTC module.
8. Keep a record for each unit. Finished units carry more duties than kits: decide which you sell.

## 8. Firmware match (BOARD_TYPE 4)

The sketch is `firmware/nixieClock_TS06/`, with `ts06pair.ino`. All *measured* by reading both sides.

| Item | Firmware | Netlist | Match |
|---|---|---|---|
| Anodes H10 H1 M10 M1 S10 S1 | `opts[]` = D6 D5 D4 D3 D2 D13 | `TUBE_PIN4` | yes |
| Digit to code | `digitMask` 1 0 5 4 6 7 3 2 9 8 | `DIGIT_MASK4` | yes |
| Decoder inputs | A0 = C, A1 = B, A2 = D, A3 = A | `K155_INPUT` | yes |
| Converter, colon, backlight, m | D9, D10, D11, D12 | R66, R1, R20, R53 | yes |
| Buttons | D7, D8, pulled up | R73, R74 to J1.5, J1.6 | yes |
| Expander | 0x20; port A to U15, U16 as A D B C | `XA_IN` | yes |
| Backlight bits | GPB k lights HL k+1 | `BL_OF_GPB` | yes |
| Rotary | A6, six steps | J1.3, R72, C5 | yes |
| Levers | A7 not read | J1.4, C6 | not written |
| ИН-15 signs | port A held at 15, dark | `GLYPH_Q` | not written |
| Default build | `BOARD_TYPE 0` (`nixieClock_TS06.ino:37`) | type 4 | **no** |

No watchdog. The colon's PWM shares the converter's timer, so it runs at 31 kHz too: untested with VT1 on the pair.

## 9. Pin maps

Where a wrong pin costs a board. Three checks, *measured*:

* **Board against netlist** (`pins.py`): 146 footprints; the net on every pad equals `tools/ts06pair.py`.
* **Rotated copies** (`rot.py`): 37 in use; each is a pure rotation of its base, none mirrored.
* **The strips** (`mate.py`): all 63 pins mate. x(DRV) + x(DISP) = 191.4 and y(DRV) - y(DISP) = 26.0 on every pin, same net.

Symbol pin numbers against the data sheet. I had no data sheet: "agrees" means with my memory, *assumed*.

| Part | Symbol pins | Status |
|---|---|---|
| K155ID1 | 3 A, 6 B, 7 C, 4 D, 5 VCC, 12 GND; outputs 0 to 9 on 16 15 8 9 13 14 11 10 1 2 | agrees |
| TLP627 | 1 anode, 2 cathode, 3 emitter, 4 collector | agrees |
| IRF840 | 1 G, 2 D, 3 S; stock TO-220 footprint, tab side drawn | agrees |
| VD1 and every diode | pad 1 cathode; VD1's cathode on HV185 | agrees |
| LM393, TC4420, MCP23017, R-78E | LM393 1 out, 2 in-, 3 in+, 4 GND, 8 V+; TC4420 1, 8 VDD, 2 in, 6, 7 out; R-78E 1 in, 2 GND, 3 out | agree |
| MPSA42, 2N3904 | 1 E, 2 B, 3 C; stock TO-92, flat drawn | agree |
| Nano module, jack | 1 D1 to 15 D12, 16 D13 to 30 VIN; jack 1 centre pin | agree |
| DS3231 mini | GND, NC, SCL, SDA, +5V | order agrees; which way it lies: gate 6 |
| ИН-12А | anode pad 7; data-sheet pin d on pad ((7 - d) mod 12) + 1; pads from the old board's Gerbers | agrees; proven on the old clock |
| ИН-15А, ИН-15Б | same socket, anode pad 7 | signs agree; no tube lit (gate 4) |
| ИН-17 | pads named by digit | **not checked** (gate 3) |
| ИНС-1 | pad 1 anode | **not checked** against a lamp |

## 10. Earlier findings: closed or open

From `Claude outputs/TS06-pair-review.md` (second grill, 30.09.26), against the netlist today:

* **Closed in the files:** E1, E2, E4 (`1_setup.ino:53-61`), E5 (but finding 6), E8 (but finding 8), E9 (165.5 to 210.8 V,
  *measured*), E11, M1, M2, M3, M6, M13.
* **Open:** E6 (finding 1), E7 (5), E12, E13 and the clamp's bench test (12), M5 (3), gates 3 to 6 (2), P11 (the cost).
* **New here:** findings 4, 6, 7, 9, 10, 13, 14.

## Reconsider

| Choice | Today | Starting today, I would pick | Cost of changing | Call |
|---|---|---|---|---|
| Decoders and opto-couplers, multiplexed | 4 K155ID1, 6 TLP627 | For a through-hole kit in this market: the same. For a product line: a high-voltage serial driver, no multiplex | A new DRV, a new display core, a grey-market chip in a fine package | **Keep.** Change later |
| The seconds pair in the multiplex | six slots, 13.5 % | Four slots; ИН-17s steady from the freed port B | One K155ID1 more, two TLP627 fewer, a block re-laid | **Change in rev C** if the bench says dim |
| The converter | MCU clock, comparator gate, driver, FET | A current-mode controller in DIP-8 with a sense resistor: no firmware in the loop, a limit on every pulse | The HV corner redrawn and proven again | **Keep**, with two guards in rev C (findings 6, 9). Change later |
| A boost module instead | none | No: single source, surface-mount, dearer | none | **Keep** |
| Nano module | on socket strips | The same: buyers re-flash over USB | A bare MCU saves little, needs a programmer | **Keep.** Name the processor |
| 12 V barrel input | jack, fuse, TVS, Schottky | The same. 5 V cannot feed 8 W and 185 V in one stage; a USB-C lead that asks for 12 V is an accessory | none | **Keep.** Ship the adapter |
| One 5 V module for all | 1.0 A, 24 % used | Logic and lights apart | One module, about 4 USD | **Change in rev C** |
| Through-hole | every part on the pair | The same: the old parts are through-hole, and it is the kit's character | none | **Keep** |
| Rev C's surface-mount lights | planned on DRV | A plug-in light board, machine-assembled, sold as an option | One small board and a header | **Change in rev C** |
| RTC as a module | DS3231 mini | The same, bought once for the batch | none | **Keep** |

## Not checked

* **No data sheet was read.** Both fetches failed: the two makers' sites are outside this session's allowed network. Every
  rating is from memory. Re-check first: TLP627's status and later suffix, the 5 V module's derating and back-feed rule, F1's
  hold against temperature, the driver's supply limits.
* Nothing was measured on a bench.
* ИН-17's lead order, ИНС-1's anode mark, which way the RTC module lies.
* Fascia R's board against its hand-written BOM; the ladder against the firmware's thresholds.
* `bash tools/verify_pair.sh` was not run here. The other audits own it.
* The page: its Order tab is empty in the snapshot, so it gave no BOM facts.
* Which board type the committed `.hex` was built for.
* Prices (no quote), heat (no model), EMC (no measurement), the law, rev C's PWM chip.
