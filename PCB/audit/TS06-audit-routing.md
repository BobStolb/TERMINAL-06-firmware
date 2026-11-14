# TS06 audit: the routing methods, and their results

Run audit-routing, 2026-11-14. Boards: `PCB/TS06-DISP/TS06-DISP.kicad_pcb` and `PCB/TS06-DRV/TS06-DRV.kicad_pcb`, rev B, at
commit 8e030d4. "Rev B" below means these two files. "Rev C" means the plan in `PCB/TS06-routing-plan.md`.

## Verdict

1. **Rev B's copper is legal and whole.** Two independent measures agree: my own scan, and KiCad 10.0.8's DRC on a copy with
   the project's rules. Both boards: 0 clearance errors, 0 unconnected, 0 vias, 0 dangling ends. No Stop.
2. **The rules it is legal against are thin.** The 0.8 mm rule covers 185 V pads only. Two low-voltage solder pads sit 0.65 and
   0.70 mm from 185 V tracks. There is no creepage rule and no width rule. Nothing gates how good the copper is.
3. **The method fits rev B and does not fit rev C.** Typed coordinates plus a home-made router that cannot place a via. Rev C
   adds surface-mount chips and FETs. Route rev C's DRV in KiCad with a rules file, and keep the scripts as checks.

## Findings

| # | About | Severity | Finding | Fix |
|---|---|---|---|---|
| R1 | rev B, DRV | **Fix before order** | The 0.8 mm HV rule is one-sided. A low-voltage pad next to a 185 V track gets 0.6. Two places: 0.65 and 0.70 mm | Make the rule cover any pad or any HV copper. Move two tracks by 0.15 mm |
| R2 | rev C | **Fix before order** | The router cannot place a via. Rev C's DRV block is surface-mount. The plan does not say how the block gets routed | Choose the method before any rev C copper: KiCad's interactive router for DRV rev C |
| R3 | rev B, DISP | Should fix | Net BL_K (10 pads) has no track. Only the pour joins it, and the pour is not stored filled. It holds today (KiCad: 0 unconnected). One pad drops off when the HV clearance is raised to 1.25 | Add a track spine through the ten pads |
| R4 | rev B, both | Should fix | DRC-clean means "clean at 0.6 mm under solder mask". Against 1.25 mm (bare copper) 161 + 55 places fail. No creepage rule runs | Write the basis down. Add a creepage rule and a planted-error test for it |
| R5 | rev B, DRV | Should fix | Width is not a rule. The PWR class says 0.5 mm; +5V is drawn at 0.4 (524 mm) and 0.3 (37 mm). XA0-7 and BL_A are 0.2 against a class width of 0.25 | One width table. A `track_width` rule per class |
| R6 | rev B, DRV | Should fix | Ground is a routed tree. From decoder U2 pin 12 to the reservoir C7 the track path is 341 mm for 96 mm straight. The anode loops are 24 to 39 cm2 on tracks alone | Rev C: pour first, treat the pour as the return, and check it |
| R7 | method | Should fix | Any part move throws away all router copper (49 % of DRV). A person cannot move one track in KiCad: the generator overwrites it | Make the board file the source for routed copper |
| R8 | method | Should fix | Quality is printed, never gated. `audit.py` QUALITY sets no exit code. Nothing checks corners, loops, ground paths or HV next to signal | Thresholds per board with an exit code |
| R9 | method | Should fix | HV class membership is a list of name patterns. Nothing checks that every net that can sit at 185 V is on it | A check that walks the netlist out from HV185 and SW |
| R10 | rev B, DRV | Note | 13 acute corners, worst 17.7 degrees on FB (the boost feedback) at (111.0, 22.0). 4 % of DRV's copper is off the 0/45/90 directions. DISP has none | A clean-up pass, or route by hand |
| R11 | rev B, both | Note | 123 (DRV) and 83 (DISP) places sit within 10 % of the required clearance. All are at or above it, and above the fab's 0.15 mm | None. Know that the margin is by design, not spare |
| R12 | rev B, DRV | Note | The boost is routed well: hot loop 80 mm2, switch node 15.9 mm of track, 2.8 mm of HV running beside signal on the whole board | Keep. Make it a rule so rev C keeps it |
| R13 | rev C | Note | 11 nets and 368 mm of track cross the planned block today, one of them HV185 (22 mm). The plan's count of 11 holds | Move HV185 out of the block before the fine-pitch parts go in |
| R14 | history | Note | The routing study and `routing-baseline/` are about the retired one-board TS06-MAIN, not the pair. Their two actions are closed | Say so at the top of the study |

Evidence classes, sources and commands are in the detail below.
