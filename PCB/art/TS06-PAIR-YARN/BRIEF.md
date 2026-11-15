# TS06 pair YARN: the brief (context pack for run pair-yarn)

## The owner's words (verbatim, review card answer, 2026-11-15 about 00:12 UTC)
"c, I want to see your go at the creative design process established here, make a fable version fascia and glyph layout"

("c" = display disp-3-4 is not approved yet. "glyph layout" = the light layout of the display board: where its LED filaments
sit and what they draw. "the creative design process established here" = the front rounds in `PCB/art/`: a concept with its
creative decisions, drawn to scale on the real board with the lights on, checked by measurement, written up, then a card.)

## The job
One new pair, designed as one object: **a fascia face and a display light layout**, both yours. No other face is touched.
K4W411 stays the one approved fascia. Drawings and checks only: no board, schematic, fab, tool, 3D, firmware, spec or page file
is edited.

## The concept (given; the details are yours)
**YARN: the board is the cloth, the LED filaments are the thread.** ("Filament" means thread. A yarn is also a tale.)
1. **One thread runs through both boards.** It starts at the spool (the MODE dial), passes the two hoops (FIELD's and SUB's gold
   rings and their link, which are fixed parts of the base), the shuttle (the pill with R7 and R8), the two keys, leaves the
   fascia, enters the display and sews through it as a **running stitch**, and ends in a needle. Where the thread is on top of the
   cloth it is a **lit filament**. Where it goes under, it is a **white dotted line**. So the gaps between filaments, which the
   parts force anyway, become the rhythm of the stitch. The case stacks the display above the fascia: the thread must leave one
   board and enter the other at the same x.
2. **The ground is woven, edge to edge, no empty space:** gold warp and white weft, with true over-and-under. Use real weave
   drafts (plain, twill, diamond twill, herringbone). A diamond twill centred on each control's own axis gives each zone exact
   symmetry; the seams where zones meet are herringbone. The weave parts round the legends so each stands on calm ground.
3. **The display's light layout:** each tube group (hours, minutes, seconds, AM/PM) is a patch sewn onto the cloth, and its lights
   are the stitches that hold it. The colon is two plumb stitches (the owner asked for two vertical bars as its borders). The long
   line under the tubes is the hem. Start from what is known to fit (see Constraints), then change what the idea needs.
4. **S and P on the fascia are two special stitches** in shaped bare-FR4 windows. Choose shapes that say what S and P mean (find
   their meaning in the docs first).
5. **A punched-card band that carries true data** (a Jacquard card): for example the six MODE positions, the ladder's ADC
   thresholds, or the tube pin map, read by script from the firmware or the schematic. Say in the write-up what each row encodes
   and how to read it. No decoration that only looks like data.
6. **Colour:** every filament warm by default (the neon's orange). Show one more view where stitches take dyed colours by function.
If a part of this concept cannot be built, change it and say why. Wild is welcome; a mirror that is nearly exact but has one odd
bit is not: each zone is either exactly symmetric or plainly directional.

## What the owner likes and dislikes (from the earlier rounds, session.md)
* Likes: art that covers the whole board with no empty space; white dotted artwork; white and thin gold in turns; an eye-catching
  curve; thick gold traces that carry information; art that conveys real information; warm orange as the default light; wild mode.
* Dislikes: near-symmetry with one odd bit; filaments in awkward places; no separate AM glyph; no colon glyph; one glyph alone on
  one side; small needless lines by SUB (a dot or a circle on FIELD's ring instead).
* Rules: no logos, brands or existing characters. No font file in the repo (KiCad's stroke font, or a font installed on the
  machine, named in the write-up). One wiring layout for all fascias; a change is allowed if it helps the theme, and is listed.

## Constraints: read these first, in this order (never read a whole `.kicad_pcb`; scan it with a short script)
1. `PCB/TS06-routing-plan.md` section 0 and the fascia sections: the one common light base (MODE arc, FIELD and SUB arcs, key
   arcs, S places S1 / T / SCR, P's pads, J2 in the pill, the rule "no part or lead above t 4.5").
2. `PCB/art/TS06-FRONT-merge.md` sections 1 to 6: what fits under the glass (2 filaments per bulb, not 3), the filament types and
   lengths (18.5 rigid, 38 flex, 60 flex), the colon borders, the fascia base "rings-and-dots", what is fixed on it.
3. `PCB/art/TS06-DISP-final-3.md` and `PCB/art/TS06-DISP-final-3-grill.md`: the last display layout (disp-3-4), its measures and
   its faults (the lintel's driven end on a return pad; the sill; the viewing height). Do not repeat its faults.
4. `PCB/art/TS06-FASCIA-organic-2.md` (the form of a write-up and its checks) and one grill of a fascia
   (`PCB/art/TS06-FASCIA-K4W411-grill.md`) for the checks a face must pass.
5. The boards: fascia R rev B in `PCB/TS06-FASCIA-rhythm/`, the display in `PCB/TS06-DISP/`. Take outlines, holes, parts, texts
   and copper from the files by script. `tools/fascia_art.py` and `tools/disp_art.py` are older art tools: reuse what helps.
6. The fab's floor: white line 0.15 mm (draw at 0.16), gold islands 0.35 mm or more from other copper, bare-FR4 windows wait on
   the window coupon. 185 V nets on the display: stay 1.0 mm or more away with any new copper.

## What to deliver
* `PCB/art/TS06-PAIR-YARN/draw_yarn.py` (and helpers): **the drawing script goes in the repo this time** (the earlier rounds' scripts
  were scratch copies and are lost). It must run from the repo root with no file from outside the repo, and print its measures.
* Pictures in `PCB/art/TS06-PAIR-YARN/`: `yarn-pair.png` (display above fascia as in the case, lights on, all warm, about 11.5 px
  per mm), `yarn-colours.png` (the dyed view), `yarn-fascia.png` and `yarn-disp.png` (each board alone, with a short notes block
  as the earlier sheets had), `detail-2x.png` (the finest part at twice the scale), `lights-back.png` (the fascia's back: pads,
  bars, windows). Look at every picture yourself before you commit it, and fix what reads badly. No names of people in any picture.
* `PCB/art/TS06-PAIR-YARN.md`, 2500 words at most, plain words, short sentences: 1) the idea in five lines; 2) the creative
  decisions, each with its reason; 3) the lights: a table for each board (name, part, place, length, colour, channel); 4) what
  each ink does (white, gold, mask, windows), with line widths; 5) the card band: what it encodes; 6) the checks, measured by the
  script (smallest gaps to legends, pads, holes, windows, 185 V nets; symmetry per zone; the thread's crossing x on both boards);
  7) "Buildable?": the change list against the common light base and against disp-3-4; 8) a short grill of your own work: the five
  worst risks, each with its fix; 9) questions for the owner (three at most).
  Mark every number *measured* (give the script), *inferred* or *assumed*.

## Rules of the run
1. Start: in your worktree, `git fetch origin pcb/kicad-boards`, then `git reset --hard origin/pcb/kicad-boards` (separate commands).
2. Write only inside `PCB/art/TS06-PAIR-YARN/` and the one file `PCB/art/TS06-PAIR-YARN.md`. Scratch files go to your scratch folder.
3. Commit in three stages on your worktree branch: the fascia; the display; the pair sheets and the write-up. Never amend. Do not
   push. No agent-commons. Every commit message ends with:
   Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>
   Claude-Session: https://claude.ai/code/session_01WoV3gyAFgmtuk6W6Dr4bdA
4. No model names in files. Parts by type number, not by shop or brand. Web: none needed; no downloads.
5. Python: `python3 -m pip install --break-system-packages numpy` if needed. The system's PIL is broken: use `convert`
   (ImageMagick), cairosvg or matplotlib if present, or write SVG and convert it. Check what is installed before you choose.
6. **Cap: 0.9 M tokens / 120 min.** At 0.75 M, stop drawing, commit what stands, and write the write-up. A smaller true result
   beats a larger unfinished one.
7. Final report, 200 words or fewer: the commits, the idea as built, what you changed from this concept and why, the worst risk,
   your questions.
