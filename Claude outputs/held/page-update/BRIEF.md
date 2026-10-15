# Run page-update: bring the TS06 product page up to date (build and test; never publish)

The owner, 2026-10-14 20:5x UTC (relayed): "nixie will prob be idle for the rest of the week once its done with the fascia
variants and the artifact update". The artifact is the product page "TS06 Board Viewer v2", source `recovered/viewer2/`
(README there: build, inputs, tests). It is NOT published by this run: the owner says yes in chat first; the orchestrator
publishes.

## Start
In your worktree: `git fetch origin pcb/kicad-boards`, then `git reset --hard origin/pcb/kicad-boards` (separate commands).
Read `recovered/viewer2/README.md` (all), `session.md` lines 180-270 (the page's history: page-handwire, fascia-j1-upright,
the 5 questions, "On the answers"), `fab/ORDER.md`, and the page's `src/index.html` / `src/app.js` structure (grep, then
ranges). Build once as it stands (`OUT=<scratch>/page-update/base bash recovered/viewer2/build.sh`, Docker: `nohup dockerd
>/dev/null 2>&1 &` if down) and run the suite (`SITE=... node recovered/viewer2/test/run.mjs`) to get the baseline count.

## What changes
1. **The held J1 update** (session.md: "The page still names the rev A zip and draws side entry: page run needed"): the Order
   view and every fascia drawing follow fascia R rev B with J1 B6B-PH-SM4-TB upright and the ordered zip
   `fab/TS06-FASCIA-R-revB-divider-holes04-fab.zip` (rev A is "-notordered"); the case 2.8 mm lower where the page shows it.
   Use what the repo now holds (3d/, fab/, PCB/); say what you could not bring over.
2. **A Fronts view** ("one back, many fronts"): the art the owner approved in front round 3, as pictures:
   * the display final **disp-3-4** (`PCB/art/TS06-DISP-final-3/disp-3-4-lintel-split-green.png`, its colour settings
     `colours.png` if it shows disp-3-4, else describe), captioned with the owner's words "colour of the particular glyphs might
     change";
   * the six final fascias: organic-2-1 The print and organic-2-2 Mushroom (`PCB/art/TS06-FASCIA-organic-2/`), science-2-3
     Double slit (`TS06-FASCIA-science-2/`), celestial-3 Sundials (`TS06-FASCIA-celestial/`), K4W411 (`TS06-FASCIA-K4W411/`),
     BLUPRNT (`TS06-FASCIA-BLUPRNT/`); each with a one-line caption from its write-up and a link-free note of its light colours;
   * one line naming the themes still in review (steampunk, radio, celestial-2, VAPORWAVE), with no pictures of them and none of
     the earlier, not chosen faces;
   * a plain note that the fronts are drawings: the board-change run (lights, connector, PWM, refit to rev B) comes after the
     owner's approved list is complete (the K4W411 grill, `PCB/art/TS06-FASCIA-K4W411-grill.md`, lists what it needs).
   Pictures: the build makes web copies (JPEG or WebP, the longest side 2400 px or less, a few hundred kB each) from the repo's
   PNGs at build time; nothing new committed under PCB/art. The page stays under 16 MB per file and the whole publish under
   64 MB / 255 files (check `publish-files.json`).
3. Phone width works (16 px gutters, no sideways scroll), light and dark.
4. Tests: add checks for the Fronts view (seven pictures load, captions present, phone width) and the Order view's new zip
   name; the whole suite passes (baseline + yours). README: the Fronts row in the inputs table and one line on how to add a
   final.

## Deliver
* Commits on your worktree branch (stage 1 after the J1 update, stage 2 at the end), trailers below; do not push.
* The built site in scratchpad `page-update/final/site` + `publish-files.json`, and 4 screenshots in `page-update/shots/`
  (Fronts desktop, Fronts phone, Order, the fascia 3D view), each under 2400 px.
* Final report 150 words or fewer: commits, the suite count (before / after), the publish size and file count, what changed,
  what you could not do.

## Rules
* Read the page source and the repo; edit only `recovered/viewer2/` (and its tests, README). No edit to board, schematic, fab,
  3d, firmware, spec or art files. No agent-commons writes. No publishing, no Artifact tool calls.
* No model names in files. Every commit ends with:
  Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_01WoV3gyAFgmtuk6W6Dr4bdA
* View at most 10 images in all; combine crops first.
* Cap 0.8 M tokens / 100 min. Staged commits keep your work if a limit hits.
