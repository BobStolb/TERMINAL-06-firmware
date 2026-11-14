# TS06 audit: layout (TS06-DISP, TS06-DRV, fascia R rev B)

Run audit-layout, 2026-11-14, on `pcb/kicad-boards` at 8e030d4. Brief: `PCB/audit/BRIEF.md`.

## Verdict

1. **Rev B has no Stop in its layout.** The fab zips match the board files, KiCad's own DRC is clean, and the 185 V copper keeps the
   project's rule everywhere but two places.
2. **Two things to fix before an order:** two bare low-voltage pads 0.65 and 0.70 mm from 185 V tracks (the rule looks one way only),
   and no place on the board for the snubber and the high-frequency capacitor that the earlier review left "to the bench".
3. **The rev C plan needs two layout decisions first:** a separate, wide 5 V and ground feed for the lights (today's 5 V tree is
   0.1 to 0.4 ohm), and anode pins that no longer sit beside 5 V pins on the strips.

## Findings

Evidence: **M** measured (script or tool named in the detail), **I** inferred, **A** assumed. "B" = rev B as in the repo, "C" = the rev C plan.

| # | Severity | About | Finding | Fix |
|---|---|---|---|---|
| L1 | **Fix before order** | B, DRV | Two bare low-voltage pads are nearer than 0.8 mm to 185 V tracks: XS23.4 (BL_A4) 0.65 mm, R44.2 (GND) 0.70 mm. The 0.8 mm rule only fires when the *pad* is high-voltage, so every check passes. M | Add the mirror rule to `.kicad_dru` and to `checkcopper.py`; move two tracks |
| L2 | **Fix before order** | B, DRV | The boost has no footprint for an RC snubber on the switch node or for a film or ceramic capacitor across C7. Review item E12 is open "for the bench", but the board gives the bench nowhere to fit them. M + I | Three unfitted footprints beside VT21 and C7 |
| L3 | **Fix before order** (rev C) | C, DRV | The 5 V rail is a 561 mm tree of 0.3 to 0.4 mm track: 0.10 ohm to the 185 V reference divider, 0.23 ohm to the Nano, 0.41 ohm to the fascia plug. The 185 V set point is half of that rail. Rev C adds up to 0.87 A of chopped light current. M + I | A separate 5 V and ground feed for the lights, 1.0 mm or wider, from the regulator; a fixed reference for the 185 V loop |
| L4 | **Fix before order** (rev C) | C, both | On four strips an anode pin (185 V) stands beside a backlight pin (5 V): 9 pairs a board, bare pads 0.84 mm apart. The plan also takes XS25.3, the one empty pin beside an anode. Known since the pair review (finding 7), not changed. M | Rev C: a blank position, or another anode, on each side of every anode pin. Rev B: Should fix; inspect the nine pairs before power |
| L5 | Should fix | B, fascia | The fascia as ordered has no board file in the repo. `PCB/TS06-FASCIA-rhythm` is rev B (upright J1) with 8.8 / 8.0 mm holes and no gold; the zip is plotted from scratch copies. `verify_pair.sh` does not cover the fascia. M | Commit the as-ordered board (or its hash and build line); add the fascia to the one-command check |
| L6 | Should fix | B, all | No test point on any board. First power-up of a 185 V supply means probing component legs. M | Loops or pads for GND (2), +12V, +5V, 185 V through a divider, FB, VREF, GATE, PWM_G |
| L7 | Should fix | B, DRV, DISP | The silkscreen shows references only: no values. A kit builder needs the BOM open for all 96 parts. M | Print values, or ship a placement sheet per value |
| L8 | Should fix | B, fascia, case | The case check's open FAIL "fascia boss on R5's pad" does not match the board: R5.1's pad edge is 5.54 mm from H3's centre, 2.04 mm outside a 3.5 mm boss. The case model has R5 at (10.0, 36.0); the board has it at (12.9, 35.2). M | Refresh the case model's fascia parts; re-run; close or restate review P6 |
| L9 | Should fix | B, DRV | Ground is two pours with no via between them. Front: one piece holds 92 % (11 949 mm2). Back: four islands of 1 641 to 3 552 mm2. They join only at the 62 ground pads. Eight pour pieces are 1 mm2 or less. M | Rev C: allow stitching vias; drop pour pieces under 5 mm2 |
| L10 | Should fix | C, DRV | The plan puts 20 FETs and two PWM chips at x 86.5 to 128.5, y 24.5 to 45.0: between the 185 V comparator U12 (107, 22.5) with its 20 kohm FB node, and the anode opto-couplers (y 47 to 57). I | Keep 5 mm from FB, VREF and R64; route light current away from U12's ground |
| L11 | Should fix | B, DRV | PWM_G, the node that gates the boost, is 175 mm of 0.25 mm track, crosses under the switch node at (74.7, 7.3), and runs 0.27 mm from FB at U12. M | Rev C: move R66 next to U11; 1 mm between PWM_G and FB |
| L12 | Note | B, all | **The fab zips match the boards today.** Drills, tracks, pads and outlines are identical; the pours in the zips equal today's KiCad fill in piece count and area. M | None |
| L13 | Note | B, all | `verify_pair.sh` with KiCad 10.0.8: 27 PASS, 0 FAIL, 0 SKIP. `dfm_check.py`: all rows PASS on the three boards; its self-test fails all 17 planted faults. No DRC severity is changed, no exclusion is stored. M | None |
| L14 | Note | B, both | Worst 185 V gaps apart from L1: 0.83 to 0.84 mm between bare pads fixed by part pitch (TO-220, strips, TO-92 next to a diode). Pours keep 0.60 mm from HV tracks and 0.80 mm from HV pads. Edges: 1.70 mm (DRV), 1.85 mm (DISP). No HV copper within 4 mm of a mounting hole. M | Rev C: 1.0 / 1.25 mm where the part pitch allows |
| L15 | Note | B, DRV | The hot loop is compact for through-hole parts: 80 mm2 through the pad centres. The switch-node track is 15.9 mm. FB is 9.1 mm long and 28.8 mm from the switch node. M | Keep |
| L16 | Note | B, DRV | Decoupling: U3, U11 within 5 mm; the four decoders 9 to 12 mm (ground side 11 to 21 mm); the Nano none within 48 mm (it has its own). M | Fine for TTL at this speed |
| L17 | Note | B, all | Track widths carry today's currents with room: 0.8 mm for 12 V and the switch node, 0.4 mm for 5 V and 185 V. M + A | See L3 for rev C |
| L18 | Note | B, pair | The 63 strip pins mate at mirrored x, same pin, same net; 4 standoff holes agree. Only strips (and DRV's J1, outside DISP's shadow) are on the inner faces. No body covers a joint of the other side. 59 of DRV's 69 HV joints face DISP across the 11 mm gap. M | Assembly rule: trim leads to 2 mm on both inner faces |
| L19 | Note | B, DRV | Mounting-hole keep-outs are in: nearest copper is 3.83 mm from a hole centre (review M12 closed). `bom.md` still says "tracks pass 2.2 mm from H5's centre". M | Correct the BOM line |
| L20 | Note | B, DRV | Pad order of the key parts agrees with their pinouts (FET, diodes, opto-couplers, decoders' supply pins, comparator, gate driver, regulator, Nano, expander). The decoders' inputs and outputs are wired in routing order, not in truth-table order; the firmware tables carry the map. M + A | Keep the "firmware tables" check; note it in the build guide |
| L21 | Note | B, DRV | `checkcopper --hv` in `verify_pair.sh` omits OVZ_* (the zener string, up to 164 V); the KiCad HV class has it. Measured: OVZ nets keep 0.83 mm. M | Add OVZ_* to the list |
| L22 | Note | B, DISP | KiCad's two accepted DRC errors: the colon lamps' courtyards overlap tube V3's by 0.13 mm in x. M | Dry fit with real parts before the order |
| L23 | Note | B, DRV | The decoder sockets' pads are 1.2 mm wide on a 0.8 mm drill: a 0.20 mm ring, the thinnest on the pair. No part runs above about 0.5 W; VT21 has 3 mm to L1 and no room for a heat sink. M + A | Rev C: 1.4 mm pads; measure VT21 on the bench |

Detail, Reconsider and "Not checked" follow.
