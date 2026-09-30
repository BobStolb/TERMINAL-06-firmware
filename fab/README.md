# Fab packages: TS06-DISP and TS06-DRV, rev B

One zip per board of the through-hole pair, built from the committed boards by `tools/mkfab.sh`
(grill.md G8, second half). Rebuilt 30.09.26 from `pcb/kicad-boards` at 77e3b11 (TS06-DISP with
the circuit-as-ornament silkscreen art; TS06-DRV unchanged), with KiCad 10.0.6's `kicad-cli` in Docker.
First built at b8d3f25 (the rev B merge).

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

TS06-DISP's silkscreen files carry the art: front 29 kB to 121 kB, back 104 kB to 173 kB. Its
copper, mask, outline and drill files are the same as before the art, apart from the creation
date, and the thinnest silk line in them is 0.15 mm (the apertures in the two silk files).
TS06-DRV's files are the same as before, apart from the creation date.

The hole counts are the drill files' hits; they equal the boards' through-hole and
non-plated pads. Both job files say 2 layers, 1.6 mm and ENIG, from the boards' own setup; the
finish and the mask colour are chosen when the boards are ordered.

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
bash tools/mkfab.sh            # both boards; prints the table above
bash tools/mkfab.sh --keep     # the same, and keeps the scratch directory (both exports, logs)
```

It needs `zip`, `python3` and KiCad 10's `kicad-cli`: a local one, or Docker with
`mirror.gcr.io/kicad/kicad:10.0`, found the same way as in `tools/verify_pair.sh`. The committed
board files are only read. The Gerbers and drills carry their creation date, so a rebuild is not
byte-identical to these zips; the region counts and the file list are.
