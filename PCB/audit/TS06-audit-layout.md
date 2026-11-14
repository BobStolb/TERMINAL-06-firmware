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
| L9 | Should fix | B, DRV | Ground is two pours with no via between them. Front: one piece holds 92 % (11 949 mm2). Back: four islands of 1 641 to 3 552 mm2. They join only at the 62 ground pads. Four pour pieces are under 1 mm2. M | Rev C: allow stitching vias; drop pour pieces under 5 mm2 |
| L10 | Should fix | C, DRV | The plan puts 20 FETs and two PWM chips at x 86.5 to 128.5, y 24.5 to 45.0: between the 185 V comparator U12 (107, 22.5) with its 20 kohm FB node, and the anode opto-couplers (y 47 to 57). I | Keep 5 mm from FB, VREF and R64; route light current away from U12's ground |
| L11 | Should fix | B, DRV | PWM_G, the node that gates the boost, is 175 mm of 0.25 mm track, crosses under the switch node at (74.7, 7.3), and runs 0.27 mm from FB at U12. M | Rev C: move R66 next to U11; 1 mm between PWM_G and FB |
| L12 | Note | B, all | **The fab zips match the boards today.** Drills, tracks, pads and outlines are identical; the pours in the zips equal today's KiCad fill in piece count and area. M | None |
| L13 | Note | B, all | `verify_pair.sh` with KiCad 10.0.8: 27 PASS, 0 FAIL, 0 SKIP. `dfm_check.py`: every row PASS on the three boards, and its self-test fails all 17 planted faults. No DRC severity is changed and no exclusion is stored. M | None |
| L14 | Note | B, both | Worst 185 V gaps apart from L1: 0.83 mm between VD7 and VT2 (a placement choice) and 0.84 mm between bare pads fixed by part pitch (TO-220, strips). Pours keep 0.60 mm from HV tracks and 0.80 mm from HV pads. Edges: 1.70 mm (DRV), 1.85 mm (DISP). No HV copper within 4 mm of a mounting hole. M | Rev C: 1.0 / 1.25 mm where the part pitch allows |
| L15 | Note | B, DRV | The hot loop is compact for through-hole parts: 80 mm2 through the pad centres. The switch-node track is 15.9 mm. FB is 9.1 mm long and 28.8 mm from the switch node. M | Keep |
| L16 | Note | B, DRV | Decoupling: U3 and U11 within 5 mm; the decoders 9 to 12 mm; the Nano has its own. Fine for TTL at this speed. M | None |
| L17 | Note | B, all | Track widths carry today's currents with room (table in the detail). M + A | See L3 for rev C |
| L18 | Note | B, pair | The 63 strip pins mate at mirrored x, same pin, same net; the 4 standoff holes agree. Only strips are in the 11 mm gap. No body covers a joint of the other face. 59 of DRV's 69 HV joints face DISP across the gap. M | Assembly rule: trim leads to 2 mm on both inner faces |
| L19 | Note | B, DRV | Mounting-hole keep-outs are in: nearest copper is 3.83 mm from a hole centre (review M12 closed). `bom.md` still says "tracks pass 2.2 mm from H5's centre". M | Correct the BOM line |
| L20 | Note | B, DRV | Pad order of the key parts agrees with their pinouts (FET, diodes, opto-couplers, comparator, gate driver, regulator, Nano, expander, decoders' supply pins). The decoders' inputs and outputs are wired in routing order; the firmware tables carry the map. M + A | Keep the "firmware tables" check |
| L21 | Note | B, DRV | `checkcopper --hv` in `verify_pair.sh` omits OVZ_* (the zener string, up to 164 V); the KiCad HV class has it. Measured: OVZ nets keep 0.83 mm. M | Add OVZ_* to the list |
| L22 | Note | B, DISP | KiCad's two accepted DRC errors: the colon lamps' courtyards overlap tube V3's by 0.13 mm in x. M | Dry fit with real parts before the order |
| L23 | Note | B, DRV | The decoder sockets' pads are 1.2 mm wide on a 0.8 mm drill: a 0.20 mm ring, the thinnest on the pair. No part runs above about 0.5 W (*assumed*); VT21 has no room for a heat sink. M + A | Rev C: 1.4 mm pads; measure VT21 on the bench |

## Detail

### How it was measured

* Repo checks, with KiCad 10.0.8 in Docker: `bash tools/verify_pair.sh --keep`, `python3 tools/dfm_check.py`.
* My scans (Python, read-only) are in the scratchpad folder `audit/layout/`: `hvclear.py`, `zipcmp.py`, `parts.py`, `more.py`, `boost.py`, `last.py`, `chk.py`. Coordinates are board millimetres, y down.
* IPC spacings, IPC current capacity and part pinouts are from memory: *assumed, not re-checked*. No web fetch was made.

### The rules the checks run with (L1, L13, L21)

* There is a real high-voltage class. `TS06-DRV.kicad_pro`: class HV, 0.6 mm, for HV185, SW, BLEED_*, FB_MID, COLON_*, ANODE_*,
  EMIT_*, OVZ_*. `TS06-DISP.kicad_pro`: HV for ANODE_*, COLON_*. Cathode nets are class CATH, 0.25 mm (they float to about 70 V at
  most; *assumed*, the decoder's clamp).
* `.kicad_dru` (both boards) adds one rule: `A.Type == 'Pad' && A.hasNetclass('HV') && A.Net != B.Net`, 0.8 mm. `verify_pair.sh`
  proves this rule is live by planting a track (rows "HV rule live").
* The numbers follow IPC-2221B table 6-1 for 171 to 250 V: 0.4 mm under mask, 0.8 mm for bare terminations (*assumed*). They suit a board where 185 V and logic share one ground behind a closed case.
* **The gap in the rule (L1).** A bare pad is the weak surface, whichever net it is on. The rule covers a 185 V pad beside a
  low-voltage track, not a low-voltage pad beside a 185 V track. `checkcopper.py --hv-pad` has the same one-way view.
  Two places fall through (`hvclear.py`):
  * DRV F.Cu: an ANODE_M10 track (0.4 mm) passes pad XS23.4 (BL_A4, round 1.7 mm, at (114.50, 67.30)) at **0.65 mm**.
  * DRV B.Cu: an HV185 track passes pad R44.2 (GND, at (70.63, 50.80)) at **0.70 mm**. R44 is unfitted, the pad is still bare.
  Fix: a second rule, `A.Type == 'Pad' && B.hasNetclass('HV') && A.Net != B.Net`, 0.8 mm; the same in `checkcopper.py`.

### 185 V clearance and creepage (L1, L4, L14)

There is no slot and no cut-out near 185 V copper, so on these boards creepage along the surface equals the clearance measured.

**DRV, the worst five to another net** (`hvclear.py`; 1 164 tracks, 870 pad-layers):

| Gap | Layer | 185 V item | Other item | At |
|---|---|---|---|---|
| 0.650 | F | ANODE_M10 track | XS23.4 pad, BL_A4 (5 V) | (114.50, 67.30) |
| 0.700 | B | HV185 track | R44.2 pad, GND | (70.63, 50.80) |
| 0.830 | F, B | VD7.1 pad, OVZ_2 | VT2.1 pad, GND | (127.35, 11.65) |
| 0.840 | F, B | VT21.2 pad, SW (drain) | VT21.3 GND and VT21.1 GATE pads | (74.44, 16.15) |
| 0.840 | F, B | anode pads on XS21, XS23, XS24, XS25 | backlight pads beside them (9 pairs) | e.g. (171.84, 67.30) |

**DISP, the worst five** (388 tracks, 378 pad-layers):

| Gap | Layer | 185 V item | Other item | At |
|---|---|---|---|---|
| 0.700 | F | COLON_U track | COLON_L track (both HV, small difference) | (48.44, 23.00), (48.44, 37.40) |
| 0.840 | F, B | XP25.5 ANODE_PM | XP25.4 M_A and XP25.6 BL_A8 | (164.71, 41.30) |
| 0.840 | F, B | XP25.2 ANODE_AM | XP25.1 BL_A7 | (157.09, 41.30) |
| 0.840 | F, B | XP21.3, XP21.4 anodes | XP21.2 BL_A1, XP21.5 BL_A2 | (17.02, 41.30), (19.56, 41.30) |
| 0.840 | F, B | XP23.3, XP24.3 anodes | XP23.4 BL_A4, XP24.4 BL_A6 | (74.36, 41.30), (120.19, 41.30) |

* **Pours** (read from the zips' filled copper, `zipcmp.py`): DRV's ground pours and DISP's BL_K pour keep 0.600 mm from every HV
  track and 0.800 mm from every HV pad, on each face. None is below.
* **Edges:** nearest HV copper is VD5's pads, 1.70 mm from DRV's top edge, and the strip pads, 1.85 mm from DISP's bottom edge.
* **Holes:** no HV copper lies within 4 mm of a mounting hole's wall. The nearest drilled hole of another net is the empty strip
  pin XS25.3 / XP25.3, 1.19 mm from ANODE_AM's pad.
* **The strips (L4).** XS21: BL_K, BL_A1, ANODE_H10, ANODE_H1, BL_A2. XS23, XS24: backlight, anode, anode, backlight. XS25: BL_A7, ANODE_AM, empty, M_A, ANODE_PM, BL_A8. A solder bridge puts 185 V through an anode resistor into the port expander or the Nano. The rev C plan (`PCB/TS06-routing-plan.md`, section 4) uses XS25.3 for a light: the only spacer goes.

### The boost converter (L2, L11, L15)

* L1 lies along y 6.4, x 46.5 to 74.4; VT21 at (71.9 to 77.0, 16.5); VD1 along y 21.5; C7 at (82.5 to 87.5, 13.5) (`parts.py`). The switch node is 15.9 mm of 0.8 mm track.
* **Hot loop** (drain, VD1, C7+, C7-, source): 80 mm2 through the pad centres, 37.4 mm round. Source to C7- is 6.3 mm, and both
  pads sit in the same pour piece on each face. Input loop (C8, L1, VT21, back to C8): 103 mm2, set by L1's length.
* The loop closes only through C7, a 4.7 uF electrolytic. HV185 has 15 pads and C7 is the only capacitor on it. SW has three
  pads: L1, VD1, VT21. So there is no place for a snubber or a low-inductance capacitor (L2). The pair review lists this as
  E12, "open: sized on the bench". Add the pads now; fit them or not after the first scope picture.
* **Feedback:** the divider starts at R62.1 (92.0, 2.6) beside C7, runs along the top edge to R63 (111.0, 2.6), then down to R64
  and U12. FB is 9.1 mm, FB_MID 3.8 mm; FB copper is 28.8 mm from SW and 12.0 mm from HV185. This is good practice.
* **PWM_G (L11):** R66 (2k2) is at (141.4, 41.9), 85 mm from the gate driver U11 (57.0, 14.8). The node after it is the
  high-impedance side. It crosses under the switch node once, at (74.7, 7.3) (about 5 fF by plate area; *inferred*, harmless). On
  the front it passes 0.27 mm from R64.1, a bare FB pad, with 9.3 mm of it within 1 mm of FB. On the back 52.6 mm of it runs
  within 1 mm of VREF.
* **Ground return:** U12's and RP1's ground share the back pour piece that carries the boost's input return (3 552 mm2). There is no star point. With a 6 mm hot-loop return at 31 kHz this is acceptable; the bench decides.

### Ground and decoupling (L9, L16)

* DRV has pours on both faces, so "no plane" is too strong. Front: 15 pieces, the largest 11 949 mm2 (62 % of the board). Back:
  10 pieces, the largest 33 % of the copper. The faces meet at 62 ground pads and nowhere else. DISP has no ground net at all;
  its one pour is BL_K (6 103 mm2). The fascia has one GND pour on the back.
* Decoupling: the distances are in L16. U12's capacitor C13 is 2.9 mm from pin 8 but 17.2 mm from the ground pin; the regulator's input capacitor C12 is 14.9 mm away.

### Track width against current (L3, L17)

Capacity is IPC-2221, outer layer, 35 um, 10 K rise (*assumed* formula). Currents are from the BOM and the review (*assumed*).

| Net | Width | Capacity | Current today | Resistance, source to farthest load |
|---|---|---|---|---|
| VIN_J, VIN_F, +12V, SW | 0.8 mm | 2.0 A | 1.2 to 1.4 A peak | 0.02 ohm (+12V) |
| +5V | 0.4 mm (some 0.3) | 1.2 A (1.0 A) | about 0.25 A | 0.41 ohm to J1.1 over 330 mm |
| GATE, GATE_D | 0.5 mm | 1.4 A | pulses | short |
| HV185, anodes | 0.4 mm (DISP 0.3) | 1.2 A | under 15 mA | 0.14 ohm |
| cathodes, logic | 0.25 mm; backlight and XA 0.2 mm | 0.9 A; 0.7 A | under 20 mA | not limiting |

* **Rev C (L3).** +5V from U14.3: 0.096 ohm to R69.1, 0.10 ohm to U12, 0.12 to 0.20 ohm to the decoders, 0.23 ohm to the Nano,
  0.32 ohm to U2, 0.41 ohm to J1.1 (`more.py`, `last.py`). VREF is R69 / R70 from +5V, so the 185 V rail follows the 5 V rail
  where R69 taps it. A light block fed from this tree at 0.87 A drops 0.1 to 0.3 V and moves the 185 V rail by 2 to 6 %
  (*inferred*), in step with the lights. The fascia's two ladders are read against the Nano's 5 V, down another branch.
  The plan's section 3.4 budgets the regulator (87 %) but not the copper.

### Mechanics (L8, L18, L19, L22)

* **Mate** (`parts.py`, and the "mate" and "pair mate (written files)" rows): 63 DISP pads against 63 DRV pads at x' = 191.4 - x,
  same strip, pin and net; DISP y + 26.0 = DRV y. Standoffs: DISP H1 to H4 against DRV H1 to H4, same mirror.
* **The 11 mm gap.** Both boards carry their parts on the outer faces. On the inner faces: DISP's seven XP strips, DRV's seven XS
  strips and DRV's J1 at y 95, below DISP's shadow (DRV y 26 to 70). So nothing but strip bodies and lead ends is in the gap.
* **Solder access:** no courtyard on one face covers a pad of a part on the other face, on either board (`more.py`). The strips
  must still be soldered while mated (review M10).
* **Holes:** DRV's eight keep-outs have radius 3.82 mm; the nearest copper is 3.83 mm from a centre. DISP's pour stops 3.80 mm from each standoff centre.

### Fab (L5, L7, L12, L13)

* **Zips against boards** (`zipcmp.py`):

| Board | Plated / unplated holes | Tracks F / B | Pad places | Outline | Pours in the zip |
|---|---|---|---|---|---|
| DISP | 179 / 10, all the same | 53 / 335, all the same | 179, the same | 191.4 x 44.0 | 1 region, BL_K |
| DRV | 427 / 8, all the same | 621 / 543, all the same | 427, the same | 191.4 x 100.0 | 15 front, 10 back |
| Fascia R | 0 / 9: five differ by +0.4 mm, as `fab/HOLES-VARIANT.md` says | back 55, the same; front 137 gold strokes, only in the zip | 39, the same | 191.4 x 40.0 | 1 back |

  Today's KiCad fill gives the same pieces and areas as the zips: DRV 12 963 and 10 721 mm2 against 12 964 and 10 723; DISP 6 103.
* **Fascia source (L5):** `PCB/TS06-FASCIA-rhythm` is the source. Its title block says rev B and J1 is the upright
  B6B-PH-SM4-TB. The holes and the gold are added by `tools/mkpcb_fascia_rhythm.py --open-holes` and `tools/fascia_gold.py divider`
  into a scratch folder. So the ordered copper cannot be opened and looked at; only rebuilt. The folder's `drc.rpt` is from
  2026-10-07 (0 violations). The fascia's silk has no revision text.
* **DFM** (limits *inferred*, `fab/ORDER.md`; no fab named): worst track 0.25 mm, clearance 0.203 mm, ring 0.20 mm, copper to edge 0.75 mm, smallest drill 0.8 mm, mask web 0.30 mm (fascia front 0.100 mm, at the limit).
* **Silk:** present: "DANGER 185 V" (DRV, twice), "! 185 V" (DISP, both faces), "12 V DC, centre +", "K" on seven diodes, pin-1 marks, LED and lamp polarity. Missing: values (L7), test points (L6). The committed boards store no pour fill (review M15, still open): never plot them without `--check-zones`.

## Reconsider

| Choice | Today | Starting today | Cost of change | Call |
|---|---|---|---|---|
| Zero vias | None on any board; power and ground run as long trees | Allow vias for ground stitching and power. They cost nothing at a fab | Routing rules and the generator | **Change in rev C** |
| Two layers, no plane | Two pours on DRV, the back one in four islands | Two layers is right for 31 kHz through-hole. Make the back ground continuous under the boost and the logic | Follows from vias | **Keep** two layers; stitch in rev C |
| Split boards and the pin-strip stack | Tubes on DISP, all else on DRV, 63 pins on 7 strips, soldered mated | Keep the split. Re-pin: anodes on their own strip or between blanks | Both boards' strip areas re-routed | **Keep** the split; **change the pin map in rev C** |
| 185 V spacing rule | 0.6 mm track, 0.8 mm HV pad, one-way | Same numbers, both ways now; 1.0 / 1.25 mm in a new layout | Two tracks now | **Change now** (L1), widen in rev C |
| Test points | None | Ten, on the outer faces | Small | **Change in rev C**, or with any respin |
| 5 V distribution | One 0.4 mm tree, 0.1 to 0.4 ohm | A bus of 1 mm or more; lights on their own feed; VREF from a reference | DRV routing | **Change in rev C** (L3) |
| Boards saved without fill | Fill made at plot time | Save them filled | None | **Change now** (the owner's G8) |
| Fascia built from flags | As-ordered board only in scratch | Commit what is ordered | None | **Change now** (L5) |

## Not checked

* No part was in hand: body heights, the 11 mm stack, the colon lamps beside V3 and the fascia controls need a dry fit.
* Pad numbering of the tube sockets (the project's own), the RTC module and the DC jack against real parts (review gates 3 to 6).
* Creepage under part bodies and through flux; temperature by measurement; the switch node's ringing.
* `tools/mkfab.sh` was not run (it can rewrite `fab/`). Whether a rebuild gives the same zips is audit-evidence's question.
* The "+" marks of C7 and C8 on the silk (the footprints carry silk shapes; I did not render them).
* The page snapshot was not used. Route statistics and the routing method are audit-routing's.
