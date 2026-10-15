# Held: the page update (2026-10-15)

The owner held it: "you can also hold the page update since we will still need one when we build the new pcbs".
Kept here so it survives the container. Not applied to `recovered/viewer2/`.

* `0001-*.patch` (308f005): fascia R rev B on the page (upright J1, the rev B zip, the case 2.8 mm lower). Built clean
  (30.9 MB, 101 files); the test suite was not run on it.
* `0002-*.patch` (4eca120): the Fronts view's build step (web copies, K4W411 approved, the rest final candidates).
* Not done: the Fronts tab, its tests, the README line, screenshots. `patch_fronts.py`, `patch_tests2.py`: untested drafts.
* `BRIEF.md`: the run's brief. Apply with `git am` on a fresh branch from `pcb/kicad-boards`, then rebuild and test
  (`recovered/viewer2/README.md`).
