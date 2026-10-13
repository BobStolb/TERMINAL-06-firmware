# TS06-DISP light lines, pass 2: V3, the owner's sketch made to fit (drawings and feasibility, nothing built)

No board, schematic, fab, tool, 3D, firmware or spec file was touched. I read `PCB/TS06-DISP/TS06-DISP.kicad_pcb` and `PCB/TS06-DRV/TS06-DRV.kicad_pcb` with a script, and ran the case model `3d/case-pair/case_pair.py` in memory only (it wrote nothing). Marks: *measured* is from a board file or the case model; *listing data* is from the shop pages; *inferred* is arithmetic; *assumed* is my reading, not measured or asked. The scratch scripts stay in the run's folder, not in the repo.

*Work in progress: section 1 is the board scan. The face, the reroutes, the height, the case and the fascia follow.*

## 1. The board scan, with the owner's new rule

**The new rule.** The owner allows the inlay under the bulb. So a filament may pass under the glass, between the glass edge and the pin pads, if the shim gap is 2.4 mm or more (section 5). The glass is then no obstacle for a body. Only the slots need clean copper. Pass 1 kept every body 0.5 mm off the glass; that is why most of V0 failed.

**Rules I kept from pass 1, section 1** (all *measured* from the repo's DRU and README): slot pad to other-net copper 0.25 mm; to 185 V tracks 0.6 mm; to 185 V pads 0.8 mm; to the board edge 0.5 mm; out of the standoff keep-outs; 0.3 mm to a screw head. Slot 1.0 x 2.5 mm plated, ring 0.4 (*inferred*). The BL_K pour is ignored (it is the return). The BL_A tracks of HL1-HL8 are free: they may be deleted or reused.

**New body rules** (*assumed*): body to an ИН-12/ИН-15 pin pad 0.4 mm at least (a printed wall in the shim between the channel and the pin hole); to other pads, HL9's flange and screw heads 0.3 mm; line to line 0.4 mm.

**The tubes' bands** (*measured* from the footprints and `case_pair.py`):

| Band | Glass edge | Pin pad edge | Room | Centre line |
|---|---|---|---|---|
| top, under each ИН-12/ИН-15 | y 3.40 | y 7.84 | 4.44 | y 5.62 |
| bottom, under each ИН-12/ИН-15 | y 32.26 | y 27.83 | 4.44 | y 30.04 |
| left side of H10 | x 3.48 | x 6.47 | 2.99 | x 4.97 |
| right side of M1 | x 97.11 | x 94.11 | 2.99 | x 95.61 |
| right side of PM | x 181.14 | x 178.14 | 2.99 | x 179.64 |

A 2.0 mm body fits each band with 0.5 mm or more on each side. The ИН-17s stand 7.8 mm off the board (*measured*: the case model puts their faces level with the ИН-12s), so under them only their lead pads count.

**Free slot sites on the lanes V3 uses** (*measured*: a scan every 0.1 mm with the rules above; "free" means a slot at the end of a level line fits there today):

| Lane | Free x (mm) | What blocks the rest |
|---|---|---|
| top, y 5.27 (under the glass tops) | 8.0-45.8, 55.3-103.1, 134.5-139.4; over the ИН-15 pair only scraps under 0.4 mm long | H3's keep-out at the colon; XP12's cathode tracks fan down over AM and PM (CAT_B_* and CAT_A_*, B.Cu) |
| bottom, y 30.40 (under the glass bottoms) | 2.0-15.3, 42.3-45.7, 54.3-66.3, 93.1-101.9, 115.0-118.5, 135.8-152.7, 158.8-163.0, 177.1-189.0 | each tube's anode track (B.Cu, 185 V) runs along y 31.4; ANODE_H1 takes x 15.3 to 42.3 |
| spine, y 38.70 (between HL9 and the strip pads) | 8.3-13.7, 22.9-45.7, 54.9-67.8, 77.7-113.6, 123.5-153.1, 160.4-160.8, 168.1-183.1 | H1 and H2 (heads and keep-outs) at both ends; the strip pads' clearance in between |
| arch legs, x 99.4 and x 138.4 | y 8 to 32, all of it | nothing: the ИН-17 glass is raised |

**What the scan says before any drawing:**

* **The hours bracket's lower end cannot sit under H1 today.** ANODE_H1 (185 V, B.Cu) drops from H1's pin 7 at x 40.56 and runs along y 31.4 to x 19.56. A slot at (39.48, 30.40) is -0.80 mm from it. The track must move about 1 mm (section 3).
* **The AM/PM box cannot start at AM's glass edge.** CAT_B_AMP, CAT_B_OHM, CAT_B_SIEMENS and CAT_B_VOLT leave XP12 between x 140.4 and 148.0. A slot at (141.0, 5.27) is -0.82 mm from CAT_B_AMP. At x 138.4 it is free, so the box starts there.
* **The upper colon mark does not fit while H3 stays.** Between H3's head (bottom at y 6.05) and V7's upper pad (top at y 7.90) there are 1.85 mm, and a body is 2.0. Its slots are free (x 43.78 and 57.28 at y 5.27); only the head is in the way.
* **The long line does not fit while H1 and H2 stay.** At y 38.7 (the only height under HL9's flange and over the strip pads) a 185 mm line needs slot centres 179.0 mm apart. Free sites span x 8.3 to 183.1, which is 174.8 mm. H1's head and keep-out take the left end.
* **Everything else fits on today's copper.** The arch's legs, the minutes bracket, the colon's lower mark and the box's other end stand on free sites.
