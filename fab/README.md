# Fab packages: TS06-DISP, TS06-DRV and the fascia R

**To order, read `ORDER.md` (the order sheet for the owner).** Pictures of the boards are in `preview/`.

One zip per board of the through-hole pair, built from the committed boards by `tools/mkfab.sh`
(grill.md G8, second half). Rebuilt 30.09.26 from `pcb/kicad-boards` at 77e3b11 (TS06-DISP with
the circuit-as-ornament silkscreen art; TS06-DRV unchanged), with KiCad 10.0.6's `kicad-cli` in Docker.
First built at b8d3f25 (the rev B merge).

The fascia R (rev A, with the Divider gold) was added on 02.10.26. **On 07.10.26 it became rev B** (J1 is the upright JST B6B-PH-SM4-TB instead of the
side-entry S6B-PH-SM4-TB, `PCB/TS06-FASCIA-rhythm/J1-UPRIGHT.md`): `TS06-FASCIA-R-revB-divider-holes04-fab.zip` is the ordered one (control holes
opened 0.4 mm and level leaders, picked by the owner on 02.10.26). Rev A's zip with those holes is kept as `TS06-FASCIA-R-revA-divider-holes04-notordered-fab.zip`
and the first fascia zip, holes as drawn, as `TS06-FASCIA-R-revA-divider-slope-notordered-fab.zip`: both NOT ordered. See below.
It was rebuilt the same day, after the design-for-manufacture check (`tools/dfm_check.py`, the table below) had found
four things on it: thin silk, a small back legend, slivers of mask at four dial rings, and "None" as the finish in its job file.
All four are fixed in the generators; TS06-DISP's and TS06-DRV's zips did not change.

Not ordered: the prototype run is the owner's decision (grill G14). Filling the committed board files (G8, first half) is also the owner's decision.

## What is in each zip

`TS06-DISP-revB-fab.zip` and `TS06-DRV-revB-fab.zip` hold the same 12 files, named after the board:

| File | What it is |
|---|---|
| `<board>-F_Cu.gtl`, `<board>-B_Cu.gbl` | Copper, front and back, with the pours filled by KiCad (`--check-zones`) |
| `<board>-F_Mask.gts`, `<board>-B_Mask.gbs` | Solder mask, front and back |
| `<board>-F_Silkscreen.gto`, `<board>-B_Silkscreen.gbo` | Silkscreen, front and back |
| `<board>-Edge_Cuts.gm1` | Board outline |
| `<board>-PTH.drl`, `<board>-NPTH.drl` | Excellon drills, mm, plated and non-plated in separate files |
| `<board>-PTH-drl_map.gbr`, `<board>-NPTH-drl_map.gbr` | Drill maps (Gerber X2) |
| `<board>-job.gbrjob` | Gerber job file: board size, layer count, thickness, the file list |

All Gerbers are Gerber X2, 4.6 mm format, KiCad's default Protel extensions. There are no paste
layers: every part is through-hole (no SMD pads on either board), and neither board has a via.

| Board | Size (job file) | Plated holes | Non-plated holes |
|---|---|---|---|
| TS06-DISP rev B | 191.5 × 44.1 mm | 179 | 10 |
| TS06-DRV rev B | 191.5 × 100.1 mm | 427 | 8 |
| Fascia R rev B, Divider gold | 191.45 × 40.05 mm, 2.0 mm thick | 0 | 9 |

TS06-DISP's silkscreen files carry the art: front 29 kB to 121 kB, back 104 kB to 173 kB. Its
copper, mask, outline and drill files are the same as before the art, apart from the creation
date, and the thinnest silk line in them is 0.15 mm (the apertures in the two silk files).
TS06-DRV's files are the same as before, apart from the creation date.

The hole counts are the drill files' hits; they equal the boards' through-hole and
non-plated pads. Both job files say 2 layers, 1.6 mm and ENIG, from the boards' own setup; the
finish and the mask colour are chosen when the boards are ordered.

## The fascia R zip

`TS06-FASCIA-R-revB-divider-holes04-fab.zip` is the fascia `PCB/TS06-FASCIA-rhythm` (rev B) with the Plates white
print and a gold: the **Divider** by default. The committed board has no gold of its own, so `tools/mkfab.sh`
builds the art board in its scratch directory with `tools/fascia_gold.py divider OUT --base R` (that
script's own checks must be clean) and plots that. Nothing under `PCB/` is written.

* The zip has 11 files: the same names as above with the prefix `TS06-FASCIA-R-divider`, and one more,
  `B_Paste.gbp` (the eight 1206 resistors are surface-mount on the back). There is no plated drill file or
  plated drill map: the board has no plated hole. The board is 2.0 mm thick (the job file says so), and its job
  file says finish ENIG, as the other two: the board file carries the same stack-up (black mask, white silk, ENIG), written by `tools/mkpcb_fascia_rhythm.py`.
* The gold is in F.Cu as copper, 0.05 mm wider each side than the opening in F.Mask over it, so a mask
  misregistration shows gold and never bare board. `tools/mkfab.sh` reads the plotted Gerbers back with
  `tools/gerbers.py gold` (no KiCad): F.Cu must carry the gold; F.Mask must be open over all of it (about
  85% of the copper's area, the rest is the 0.05 mm rim); no opening may lie past the copper. The same check is
  run on a mask with the gold's openings removed, and must FAIL. Found: the openings are present, and no thin web
  of mask is left over the gold (the Divider's lines end clear of the dial rings' holes; before, four rings had 0.05 mm slivers).
* The name carries the gold. `--gold VARIANT` picks another (`ladder`, `fans`, `guilloche`; `none` is the bare
  board, `TS06-FASCIA-R-revB-bare-fab.zip`). Only the divider is laid out for R; the other three stop on their own
  checks (`tools/fascia_gold.py` says why).

## Design-for-manufacture check

`python3 tools/dfm_check.py` (limits *inferred*, typical of a low-cost two-layer service; `ORDER.md` lists them) reads each
board twice: KiCad's DRC under the fab limits, and the zip's own Gerbers and drills. Worst value found, and the
rule's limit; the fascia R's column is after the fixes, with the value it had before.

| Rule | Limit | TS06-DISP | TS06-DRV | Fascia R (before the fixes) |
|---|---|---|---|---|
| Track width | 0.15 | 0.25 | 0.25 | 0.25 |
| Copper clearance | 0.15 | 0.25 | 0.21 | 0.325 (rev A 0.375) |
| Annular ring | 0.15 | 0.30 | 0.20 | over 0.40 |
| Copper to edge | 0.30 | 0.75 | 0.75 | over 0.80 |
| Silk line, DRC text stroke | 0.15 | 0.15 | 0.15 | 0.15 (0.12) |
| Silk text height | 1.0 | 1.0 | 1.0 | 1.0 (0.8) |
| Smallest silk aperture, front / back, from the zip | 0.15 | 0.15 / 0.15 | 0.15 / 0.15 | 0.15 / 0.15 (0.12 / 0.10) |
| Smallest plated / non-plated drill | 0.3 / 0.5 | 0.9 / 3.2 | 0.8 / 3.2 | none / 2.7 |
| Narrowest mask web, front | 0.10 | 0.3 | 0.3 | 0.100 (0.05) |
| Narrowest mask web, back | 0.10 | 0.3 | 0.3 | over 0.35 |
| Board size | within 500 x 400 | 191.4 x 44.0 | 191.4 x 100.0 | 191.4 x 40.0 |
| **Result** | | all PASS | all PASS | all PASS (4 rows FAILed) |

Rows that do not appear above (plated drill, non-plated drill and hole-to-hole in the DRC; the fascia's gold exposed) also
PASS. The check's own self-test, a copy of TS06-DISP with one planted fault per rule, shows FAIL on all 17 rows, so the
rows can fail. The mask web reading is the raster's (steps of 0.025 mm, about +-0.03 mm).

## Region check

Every copper Gerber is exported twice: with `--check-zones` (KiCad fills every pour before it
plots; this is the set in the zip) and without it (a control, not shipped). The script counts the
region blocks (`G36` … `G37`) in each. A copper layer that carries a pour in the board file must
have more regions filled than unfilled, or the script fails and does not write the zip.

| Board | Copper layer | Pour in the board file (net) | Regions without --check-zones | Regions with --check-zones | Difference | Check |
|---|---|---|---|---|---|---|
| TS06-DISP rev B | F.Cu | BL_K | 0 (13 kB) | 1 (221 kB) | +1 | PASS |
| TS06-DISP rev B | B.Cu | none | 0 (27 kB) | 0 (27 kB) | +0 | n/a: no pour on this layer |
| TS06-DRV rev B | F.Cu | GND | 0 (57 kB) | 15 (550 kB) | +15 | PASS |
| TS06-DRV rev B | B.Cu | GND | 0 (54 kB) | 10 (443 kB) | +10 | PASS |

**What the difference means.** The committed boards store no fill. Plotted without
`--check-zones`, TS06-DISP's F.Cu has no BL_K pour, so all nine LEDs would be open, and TS06-DRV
has no ground pour on either face. TS06-DISP's back face has no pour by design, so it has nothing
to check. The filled counts equal the pieces KiCad's own fill keeps in
`tools/verify_pair.sh`'s "pours (KiCad)" rows (BL_K 1; GND 15 on the front, 10 on the back): one
region per piece.

## Rebuild

From the repository root:

```
bash tools/mkfab.sh                                   # all three boards; prints the table above
bash tools/mkfab.sh TS06-FASCIA-rhythm --gold fans    # the fascia with another gold (see above)
bash tools/mkfab.sh --keep                            # the same, and keeps the scratch directory (both exports, logs)
python3 tools/dfm_check.py                            # design-for-manufacture tables (inferred generic limits), see ORDER.md
bash tools/mkfab.sh TS06-FASCIA-rhythm --committed-holes   # the fascia as committed (holes 8.8 / 8.0), NOT ordered: ...-notordered-fab.zip
python3 tools/dfm_check.py --committed-holes          # the same DFM check on that zip (the default checks the ordered one)
```

`TS06-FASCIA-R-revB-divider-holes04-fab.zip` is the ordered fascia zip (the dial hole 8.8 opened to 9.2, the lever and button holes 8.0 to 8.4:
the owner's pick, 2026-10-02) with the level leaders (his second pick, the same day). The zip with the holes as drawn is kept as
`TS06-FASCIA-R-revA-divider-slope-notordered-fab.zip`, not ordered. `HOLES-VARIANT.md` says what differs and the margins; `ORDER.md` names the zip.

It needs `zip`, `python3` and KiCad 10's `kicad-cli`: a local one, or Docker with
`mirror.gcr.io/kicad/kicad:10.0`, found the same way as in `tools/verify_pair.sh`. The committed
board files are only read. The Gerbers and drills carry their creation date, so a rebuild is not
byte-identical to these zips; the region counts and the file list are. So that a rebuild does not leave a
changed file behind for nothing, `tools/mkfab.sh` keeps the zip already in this folder when the rebuilt one
differs from it only in those dates (it says so).

The fascia's gold check needs numpy, scipy and Pillow as well; `tools/dfm_check.py` needs the same.
