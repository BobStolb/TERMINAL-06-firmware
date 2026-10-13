# TS06-DISP light lines, pass 2: V3, the owner's sketch made to fit (drawings and feasibility, nothing built)

No board, schematic, fab, tool, 3D, firmware or spec file was touched. I read `PCB/TS06-DISP/TS06-DISP.kicad_pcb` and `PCB/TS06-DRV/TS06-DRV.kicad_pcb` with a script, and ran the case model `3d/case-pair/case_pair.py` in memory only (it wrote nothing). Marks: *measured* is from a board file or the case model; *listing data* is from the shop pages; *inferred* is arithmetic; *assumed* is my reading, not measured or asked. The scratch scripts stay in the run's folder, not in the repo.

*Work in progress: sections 1 to 3 are in (the scan, V3, the reroutes). The height, the case and the fascia follow.*

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

## 2. V3: the sketch, made to fit

![V3](TS06-DISP-lights-pass2/v3-face.png)

**What it is.** All nine strokes of the sketch, in seven filaments. Each bracket is one 95 mm piece: it runs under the glass edges of its two tubes and comes out on the face for 3.9 mm between them. The box round the ИН-15 pair does the same. The arch stands on the face beside the raised ИН-17s. The colon's two marks and the long line are on the face. The case window is today's: x 3.0 to 182.0, y 2.6 to 39.0.

**What changed against the sketch, and why.**

* **The top runs are under the glass tops, not above them.** Above the glass the brow hides the board (y under 2.6), and a slot needs 4.3 mm where there are 3.4 (pass 1). Under the glass the band is 4.44 mm.
* **Each bracket is one piece, not two.** The sketch drew each bracket as two strokes with a gap on the outer side. One 95 mm piece fits exactly: the arms end 3.5 mm past the inner tube's centre, where the sketch's ends are. It costs two slots, not four, and one channel. *Inferred* from the sold lengths; a 60 + 60 pair overlaps on the outer side.
* **The colon's marks line up with the bracket ends.** Top and bottom, the row reads: bracket arm, gap, colon mark, gap, bracket arm. The gaps are 4.3 and 3.8 mm (slot to slot); the colon mark is centred on the lamps, the tubes are not quite (x 50.54 against 50.28).
* **The box starts 2.3 mm left of AM's glass,** right over the arch's right leg. Further right, XP12's cathode tracks fill the top band (section 1).
* **The long line sits at y 38.7,** under HL9's flange (0.30 mm clear) and over the strip pads. It is one 185 mm piece, lit from x 4.8 to 179.8, centred under the row.
* **Symmetry:** the two brackets mirror each other about the colon; the top lane and the bottom lane are symmetric about the tubes' centre line (y 5.27 and 30.40, 12.57 each side of y 17.83).

**The zones** (every number *measured* on the board file or *inferred* from the sold lengths; slot centres in the board's frame, y down from today's top edge):

| Tag | Stroke (sketch) | Filament (sold) | Slot to slot | Slots: driven, return | Face or inlay | Channel |
|---|---|---|---|---|---|---|
| H | hours bracket (a + b) | 95 mm flex | 89.0 | (39.48, 30.40), (39.48, 5.27) | inlay under H10 and H1; face between them | BL_A1 |
| K | colon, upper mark (e) | 18.5 mm bar | 13.5 | (43.78, 5.27), (57.28, 5.27) | face; its right end under M10's glass corner | BL_A2, with C |
| C | colon, lower mark (f) | 18.5 mm bar | 13.5 | (43.78, 30.40), (57.28, 30.40) | face; its right end under M10's glass corner | BL_A2 |
| M | minutes bracket (c + d) | 95 mm flex | 89.0 | (61.10, 30.40), (61.10, 5.27) | inlay under M10 and M1; face between them | BL_A3 |
| S | arch over the ИН-17 pair (g) | 60 mm flex | 54.0 | (138.40, 19.88), (99.40, 19.88) | face; top at y 9.80, legs down to the ИН-17s' upper third | BL_A6 |
| P | box round the ИН-15 pair (h) | 95 mm flex | 89.0 | (151.86, 30.40), (138.40, 5.27) | face for 2.3 mm, then inlay under AM and PM | BL_A7 |
| F | the long line under all (i) | 185 mm flex | 179.0 | (181.81, 38.70), (2.80, 38.70) | face | BL_A8 |

The return slot of every line stands on the BL_K pour and needs no track. BL_A4 and BL_A5 stay spare. Six zones, six channels: no channel beyond pass 1's sixteen.

**Clearances** (*measured* on the drawn centre lines, body 2.0 mm): body to an ИН-12/ИН-15 pin pad 0.50 at the least (the bracket and box legs; rule 0.4); body to HL9's flange 0.30 (F); body to V8's lower pad 0.30 (C); line to line 1.79 at the least (M's leg to the arch's leg); every slot passes the 185 V rules after the one move in section 3. The colon lamps are taken to stand on their leads near the glass fronts, like the ИН-17s, so their 6.97 mm envelope is not on the board face (*assumed*; C passes 0.41 mm from it even if it were).

**What changes on the board for the face** (the list is in section 3): seven pairs of slots; one 185 V track moved about 1 mm; seven drive tracks; the board 2.5 mm taller at the top and 4.0 mm at the bottom, with H1, H2 and H3 moved (section 4).

### 2.1 V3b, the same with no growth (an alternative)

![V3b](TS06-DISP-lights-pass2/v3b-no-growth.png)

If no standoff may move: drop the upper colon mark K (H3's head stays where the sketch drew it) and lift the long line to y 34.0, 3.6 mm under the bracket ends. At y 34.0 the line's slots clear H1 and H2 (x 2.80 and 181.81 are free there), but the line crosses HL9's pads, so HL9 moves 3.0 mm down to (160.9, 38.5) and its M_A track gets 3.0 mm shorter. HL9's pads keep 1.05 mm to XP25's. The cost: the upper colon mark, and the "m" LED then sits half behind the sill when seen straight on (*inferred*: its flange spans y 36.6 to 40.4, the sill top is y 39.0). Board, DRV and case otherwise as V3, without section 4's growth.

## 3. The reroutes

![V3 copper](TS06-DISP-lights-pass2/v3-copper.png)

I tested every drive track with a small grid router (0.1 mm grid, 0.3 mm track, 45-degree moves, the rules of section 1, every slot an obstacle). Lengths are *inferred* from its paths; corners are rounded to 0.1 mm.

| Net | Layer | From, to (through) | Length: old, new | What and why |
|---|---|---|---|---|
| ANODE_H1 (185 V) | B.Cu | H1 pin 7 (40.56, 25.83), a 45-degree jog to (41.40, 26.70), down to (41.40, 33.00), left to (19.56, 33.00), down to XP21.4 | 36.5, 37.6 (+1.1) | The drop moves 0.84 mm right and the run 1.60 mm down, so H's lower slot keeps 0.80 mm. It keeps 0.60 to C's drive track and 1.73 to the next track (K1). The only 185 V track that moves. |
| BL_A1 (H) | F.Cu, one via | via at HL1's old anode pad (14.48, 35.50), right to (34.4, 35.5), up to H's slot (39.48, 30.40) | 5.8, 5.8 + 27.1 | H's slot sits inside ANODE_H1's new route, so its drive crosses it on the front. The track cuts the BL_K pour along its length; the pour stays one piece. |
| BL_A2 (C and K) | B.Cu | XP21.5 (22.1, 41.3), right to (34.4, 41.3), up to (42.3, 33.4), to C's slot (43.78, 30.40) | 21.5, 27.1 (+5.6) | Runs under ANODE_H1's new run with 0.60 mm. |
| BL_A2 (K) | F.Cu | C's slot (43.78, 30.40) straight up to K's slot (43.78, 5.27) | new, 25.1 | B.Cu between the colon and H1 is full; the front is free there (COLON_U is 3.3 mm away). K and C share the colon zone. |
| BL_A3 (M) | B.Cu | XP23 (69.28, 41.3), up to (68.0, 37.3), to M's slot (61.10, 30.40) | 9.8, 14.3 (+4.5) | |
| BL_A6 (S) | B.Cu | XP24 (122.73, 41.3), along y 40.0 to (126.8, 40.0), to (135.0, 31.8), up to (135.1, 23.2), to the arch's right slot (138.40, 19.88) | 12.5, 29.5 (+17.0) | The longest; it passes between S1's pads and ИН-15Б's left pins. BL_A5 to the left leg is 28.2 mm and also fits. |
| BL_A7 (P) | B.Cu | XP25 (154.55, 41.3), up to (154.6, 33.1), to P's slot (151.86, 30.40) | 8.7, 12.0 (+3.3) | |
| BL_A8 (F) | B.Cu | XP25 (167.25, 41.3), right to (179.2, 41.3), to F's slot (181.81, 38.70) | 11.2, 15.7 (+4.5) | |
| BL_A4, BL_A5 | B.Cu | deleted | 17.5 and 10.0, to 0 | spare channels; the strip pins stay |
| M_A (V3b only) | B.Cu | HL9's anode pad moves to y 38.5 | 5.8, 2.8 (-3.0) | V3b only |

Every new track keeps 0.25 mm to other copper and 0.6 mm to 185 V copper (the router's rule), and no two new tracks on one layer come within 2 mm of each other except where they share a net. **Not checked:** a real DRC in KiCad (the board file is not edited), the pour's fill after the F.Cu tracks, thermal reliefs on the slots.
