# Fascia R with opened bushing holes: the ordered zip

**PICKED.** The owner chose it (2026-10-02, 10:37 UTC: "1-  yes"), so `fab/TS06-FASCIA-R-revB-divider-holes04-fab.zip` is the
fascia zip that `fab/ORDER.md` names. The zip with the holes as drawn (8.8 and 8.0 mm) is kept, renamed, as the one that was
NOT ordered: `fab/TS06-FASCIA-R-revA-divider-slope-notordered-fab.zip` (it also has the sloped leaders the owner replaced with
the level ones at 11:31 UTC: "a"). The committed board `PCB/TS06-FASCIA-rhythm` keeps its 8.8 / 8.0 holes: the opened board is
written by `tools/mkpcb_fascia_rhythm.py --open-holes` (scratch), never into `PCB/`. Nothing was sent to a board house.
**Rev B (7 October 2026):** the same holes are in the rev B zip (`fab/TS06-FASCIA-R-revB-divider-holes04-fab.zip`, upright J1:
`PCB/TS06-FASCIA-rhythm/J1-UPRIGHT.md`); rev A's zip with them is `fab/TS06-FASCIA-R-revA-divider-holes04-notordered-fab.zip`, not ordered.
The numbers below were taken on rev A and do not depend on J1.
(The text below was written before the pick; its numbers are unchanged. "The variant" is the ordered board; "as ordered" in its
tables is the committed board, the one not ordered.)

## What differs

The fascia's five control holes are 0.4 mm wider in diameter. Nothing else on the board moves.

| Control | Hole as ordered | Hole in the variant | Bushing (calipered, `3d/*.step`) | Room a side, as ordered | Room a side, variant |
|---|---|---|---|---|---|
| SW1 rotary (the dial) | 8.8 | **9.2** | 8.62 | 0.09 | **0.29** |
| SW2, SW3 levers | 8.0 | **8.4** | 7.82 | 0.09 | **0.29** |
| SW4, SW5 buttons | 8.0 | **8.4** | 7.82 | 0.09 | **0.29** |

The four M2.5 corner holes (2.7) stay.

## Why

0.09 mm a side is less than the drilling tolerance of a low-cost fab (typically a tenth of a millimetre or more on
a non-plated hole; *inferred*, no fab was asked). One hole drilled a tenth small and the part does not go in; the board is
then a 2.0 mm fascia with gold on it that has to be reamed by hand. 0.29 mm a side takes a tolerance like that and
leaves room. The price is play: until its nut is tightened a part can sit up to 0.29 mm off centre in the hole.
The repo has no model of the nuts, so this is not checked; a dry fit with real parts (G14) closes it.

## What was checked (nothing collides, no silk ring changed)

`python3 tools/holes_variant_check.py` builds the board both ways in a scratch directory and prints its tables.

* The default board the generator writes is the committed board byte for byte. The variant differs from it by ten lines:
  the five pads' size and drill.
* Each control footprint carries one hole and no anti-rotation tab, key slot or locating hole. A real part's own flat
  or tab is not in the footprints or the STEP files; the dry fit closes that.
* The art checks run clean on the variant board: `tools/fascia_art.py` (Plates silk) and `tools/fascia_gold.py` (the gold:
  6 mm from a lever or button centre, 9 mm from the dial shaft, and its other rules). The keep-outs are measured from
  the centres, which the holes do not move, so the art is identical on the two boards. Margins as before: controls
  +0.49 mm beyond 6.0, dial +1.30 mm beyond 9.0.
* The silk rings round the holes (footprint F.SilkS, radius 6.4 on the dial, 5.6 on the levers and buttons) stay as
  they are. Their inner edge was 1.92 mm (dial) and 1.52 mm (others) from the hole's edge and is now 1.73 and 1.32 mm.
  The criterion is 0.4 mm. None had to grow.
* Gaps from the new hole's edge: gold at least 2.29 mm, white silk art at least 4.50 mm, copper at least 2.67 mm, the
  next hole 12.60 mm, a screw hole 13.75 mm, the board edge 11.40 mm. All pass.

## The zip

`fab/TS06-FASCIA-R-revB-divider-holes04-fab.zip` (49 kB, 11 files, the same names as the zip not ordered with `-holes04`).
Built by `bash tools/mkfab.sh TS06-FASCIA-rhythm` (the default since the pick; `--open-holes` says the same); nothing under `PCB/` is
written. As first built (same leaders as the zip not ordered; the level leaders of 11:31 UTC then changed its silk and gold files too)
against that zip five files differ: the non-plated drill file and its map (the five hole sizes), the back copper (the ground pour keeps
its clearance from the larger holes), and both solder masks (the openings round the holes). The front copper (the gold),
both silk files, the outline, the paste layer and the job file are identical.

* `python3 tools/dfm_check.py --open-holes`: every row PASS; the self-test, 17 rows, FAILs on all 17 as it must; the worst
  values are the same as on the current fascia zip (copper clearance 0.375, mask web 0.100, smallest drill 2.7 mm, nine
  holes: one 9.2, four 8.4, four 2.7).
* `python3 tools/dfm_check.py --open-holes --g11`: passes, the same numbers as the current zip (boss to R5 still 1.39 mm).
* `python3 tools/dfm_check.py` (the three current zips) and `--g11`: unchanged, pass.
* `bash tools/verify_pair.sh`: 27 PASS, 0 FAIL, 0 SKIP.
* The fit table (`3d/populated/fit-table.md`) now has the ordered board's bushing rows, +0.29 a side, in its table, and shows
  the committed holes (+0.09, the zip not ordered) below it. The renders and GLBs of the fascia in `3d/populated/` and the
  pictures in `fab/preview/` are drawn on the opened board.

## What was done when it was picked

`fab/ORDER.md`'s table names `fab/TS06-FASCIA-R-revB-divider-holes04-fab.zip` and says the other one was not ordered; the page's
Order view reads it from there. Nothing else changes: the other two zips, the quantity, 2.0 mm, ENIG, black mask, white silk and
the "no fab number on the face" request all stay. `bash tools/mkfab.sh` builds the opened zip by default (`--committed-holes`
builds the not-ordered one, named `...-notordered-fab.zip`); `python3 tools/dfm_check.py` checks it by default
(`--committed-holes` checks the other).
