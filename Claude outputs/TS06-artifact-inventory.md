# TS06 artifact inventory (read-only)

> Repo copy: artifact links are left out on purpose (two of the pages are shared with anyone who has the link). The owner's artifact list has them.


Prepared 2026-09-30 for the migration of 17 artifacts into the TS06 Board Viewer ((link in the owner's artifact list)). Nothing was published, changed, pinned or deleted. The old artifacts stay untouched.

- **Method:** each artifact was read with the Artifact tool (`read`, and `list` with scope `files`). Every one is a single page with no published files, and none declares runtime capabilities, so none has an asset store. Dates come from the artifact list.
- **Today's design** (from README.md and PCB/README.md on branch pcb/kicad-boards): TS06-DISP rev B + TS06-DRV rev B (191.4 mm, through-hole, zero vias), TS06-FASCIA 176 x 40, case 204.4 x 122.8 x 81.6 mm.
- **Sizes:** exact byte counts where the read service reported them (1 KB = 1000 bytes); estimates for the five small pages it returned inline.
- **Marks:** each claim is marked **seen** (read in the artifact, the list or the repo) or **inferred** (judgement or estimate). In the table, (s) = seen and (i) = inferred.
- **Personal data:** none is copied here. Pages that hold it say "contains seller or personal details (not copied)".

## Summary

**Headline, by primary target view:** History 6 · Family 8 · Front panel 2 · Parts and buying 1 · Product 0 · Build 0 · Circuit 0 · Case 0.
Secondary feeds: Circuit ← A1, A2 (the A6/A7 ladders) · Case ← A4 (IN-17 20.5 mm spacing, two-cheek origin) · Product ← A5 (effects player) · Parts and buying ← A5 (dated Rev E cost), B7, B8 (anonymised).

| ID | Artifact | Updated | Size | Target view | Effort | Flags |
|---|---|---|---|---|---|---|
| A1 | TS06-FASCIA Panel Drawing | 2026-09-08 | ~30 KB (i) | Front panel | M | pinned |
| A2 | TS06-FASCIA Reference | 2026-09-09 | ~15 KB (i) | Front panel | S | — |
| A3 | TS06-FASCIA Buy List | 2026-09-09 | ~15 KB (i) | Parts and buying | S | personal data |
| A4 | TERMINAL·06 Rev F | 2026-09-09 | 345 KB (s) | History | M | — |
| A5 | TERMINAL-06 Plate Set | 2026-09-05 | 372 KB (s) | History | L | — |
| A6 | TERMINAL-06 Open Deck | 2026-09-02 | 185 KB (s) | History | S | — |
| A7 | Terminal·06 Concept Plates (24.08) — Rev C | 2026-08-24 | 421 KB (s) | History | M | inline data, personal data |
| A8 | Terminal·06 Concept Plates (25.08) — Rev A | 2026-08-25 | 371 KB (s) | History | M | link-shared, inline data, personal data |
| A9 | Terminal 06 3D model | 2026-08-25 | 650 KB (s) | History | M | link-shared, inline data, 3D |
| B1 | MIMI-06 Kuro | 2026-09-02 | 332 KB (s) | Family | M | pinned |
| B2 | Mimi·06 Concept Plates | 2026-08-25 | 2,323 KB (s) | Family | M | pinned, inline data |
| B3 | QUADRANT Desk Miniature | 2026-09-05 | 100 KB (s) | Family | S | personal data |
| B4 | SCALER-06 Decatron | 2026-09-02 | 136 KB (s) | Family | S-M | personal data |
| B5 | Staircase Nixie Clock | 2026-08-25 | ~24 KB (i) | Family | S | — |
| B6 | Not a Nixie | 2026-08-28 | ~40 KB (i) | Family | M | personal data |
| B7 | Meshok Tube Board | 2026-08-25 | 66 KB (s) | Family | M | personal data |
| B8 | Meshok Watchlist | 2026-08-25 | 50 KB (s) | Family | M | personal data |

Group A = TERMINAL-06 (A1–A9); group B = sibling clock and tube projects (B1–B8).

**Cross-cutting findings**
- **The two Concept Plates copies differ** (seen): the 24.08 copy is **Rev C** (6 plates) and the 25.08 copy is **Rev A** (5 plates). The list dates run opposite to the content age; see "A7 vs A8" below.
- **TERMINAL-06 Open Deck is a strict subset of TERMINAL-06 Plate Set** (seen, by diff): nothing to migrate beyond a dated link.
- **Repo copies** (seen): knowledge/ in the repo holds browser-saved copies of A1, A4, B1, B2, B3 and B4, each matching the live version's dates and plates, so those six are not the only copy.
- **Link-shared pages** (seen): A8 (Concept Plates, Rev A) and A9 (3D model) are shared with anyone who has the link.
- **Big inline data** (seen): B2 2.3 MB (1.7 MB SVG + 2 base64 JPEGs), A9 0.65 MB bundle (three.js + fonts), A7/A8 about 0.4 MB each incl. one base64 JPEG, A4/A5/B1 about 0.3 MB of SVG.
- **Browser-only state** (seen): A3 keeps the owner's buying ticks in localStorage (key ts06-buylist-v1). They exist only in the owner's browser and will not move with the page.
- **Scripts that read the clock or use randomness** (seen): A5, A6, B1, B3 (setInterval + the viewer's clock), B4 (random simulation). No page fetches live data. External resources are Google Fonts stylesheets and plain links.

## Per-artifact sections

### A1. TS06-FASCIA Panel Drawing
- **URL:** (link in the owner's artifact list) · **updated** 2026-09-08 · pinned (seen, list)
- **Form:** single page, no published files; no assets capability, so no asset store (seen). Size about 30 KB of HTML (inferred, estimated from the read). No runtime capabilities (seen).
- **Holds (seen):**
  - Title block: TS06-FASCIA rev A, 2026-09-08, "Rezonit order, 15 off"; 176.00 × 52.00 mm, 2.0 mm FR4 2-layer, matte black mask, white silk, ENIG gold; 1 × JST-XH 6-way; 8 R, 5 SW, 1 J.
  - Panel drawing: front face and back-side placement ("x-ray"), two tabs, inline SVG drawn 1:1 by script (dial, FIELD/SUB levers, −/+ buttons, gold SUB traces, R1–R8, landing pads, J1).
  - "What the controls do": interactive 6-position dial (Normal, Set Time, Display, Ambient, Format/Date, Info) showing what FIELD, SUB and the buttons do on each screen; the "SUB is live only when FIELD is on its second throw" rule.
  - Hardware table (rotary Ø8.62 bushing → 8.80 hole, 7.00 mm usable, Ø6 shaft, Ø25 body, 30° × 6; МТ1 and КМД1 bushings Ø7.82 → 8.00 holes) and the control scheme rev B table.
  - Ladder design: A6 tapped divider (5 × 4k7, ADC codes 0/205/409/614/818/1023, 5.64 k source impedance) and A7 lever ladder (R6 10k, R7 20k, R8 10k; codes 1023/682/512/409); why no pull-ups and why the filter caps sit at the main-board end.
  - "Open before Gerbers" log: 12 detents (closed), bushing stack depth (open), SUB rule and INFO-to-6 (resolved), the 26.94 mm body figure withdrawn.
- **Images / 3D:** no raster images; all drawings are inline SVG built by inline script (seen). No 3D.
- **Superseded by today's design:**
  - 176 × 52 mm outline: today's TS06-FASCIA is 176 × 40 (height compressed 2026-09), with 191.4 × 40 variants beside it (seen, PCB/README.md, PCB/TS06-FASCIA-variants.md).
  - J1 "GND +5V A6 A7 D7 D8" on JST-XH: today J1 is fixed as 1 +5V, 2 GND, 3 A6, 4 A7, 5 D7, 6 D8, and the cable is JST PH (seen, PCB/README.md).
  - "Hand-wired controls with lugs behind" and the dial arc geometry: today's board is a routed SMD build with a rescaled MODE arc (seen, PCB/README.md); the drawing's positions no longer match the board file (inferred).
  - "Two 100 nF caps at the main-board end": DRV rev B adds its own filters (1 M on A6, 1 k + 10 nF on D7/D8) (seen); whether A6/A7 still get 100 nF is not checked (inferred partly superseded).
- **Still current:** the A6 divider and A7 lever ladder (R6 is still the A7 pull-up, seen in PCB/README.md); the control scheme rev B and its dial semantics (a repo file TERMINAL-06-control-scheme-revB.md exists, seen by name only); the hardware bushing figures (inferred).
- **Unique:** the interactive dial explainer (per-position FIELD/SUB/button roles) and the ladder rationale with ADC code tables, as written here (inferred unique among artifacts; the Reference page may overlap, see A2). A browser-saved copy of this same version (rev A, 2026-09-08) is in the repo at knowledge/TS06-FASCIA Panel Drawing.html (seen).
- **Target view:** Front panel (drawing + controls + ladder); the 176 × 52 drawing itself to History, marked "superseded by TS06-FASCIA 176 × 40".
- **Effort:** M. The dial explainer and ladder SVGs are script-built and need re-hosting as code, not copy; the drawing must be split into current (controls, ladders) and history (outline, J1 order).
- **Risks:** Google Fonts stylesheet (external, allowed); inline script builds all SVG, so a text-only copy loses the drawings (seen). No local storage, no live data (seen). Dark-only palette, no light theme (seen).

### A2. TS06-FASCIA Reference
- **URL:** (link in the owner's artifact list) · **updated** 2026-09-09 (seen, list)
- **Form:** single page, no published files, no runtime capabilities, so no asset store (seen). About 15 KB (inferred, estimated from the read).
- **Holds (seen):**
  - Header stats: 176 × 52 mm, 2.0 mm FR4 2-layer ENIG, black mask/white silk, B.Cu-only signals, 0 vias, 6-pin JST-PH to the main board. Written for the SMD build.
  - 01 Front face: one static inline SVG (MODE dial with six labels, FIELD/SUB levers with gold boxes, −/+ buttons, SW1–SW5 callouts); points to PCB/TS06-FASCIA/preview.svg.
  - 02 "Five controls on two analog pins": A6 tapped divider table (positions → taps) and A7 two-lever table (paths to GND).
  - 03 Net reference: +5V, GND, A6, TAP2–TAP5, A7, LEVA/LEVB, D7, D8, each with pads and the reason.
  - 04 J1 pinout 1 +5V, 2 GND, 3 A6, 4 A7, 5 D7, 6 D8. 05 Routing notes: 64 B.Cu tracks, 0 vias, the R6 corridor story and the GND pour fix.
- **Images / 3D:** one static inline SVG, CSS-variable coloured (seen). No raster, no 3D.
- **Superseded by today's design:** the 176 × 52 outline and the dial label geometry (today 176 × 40 after the 2026-09 compression, with a rescaled MODE arc) (seen, PCB/README.md).
- **Still current:** J1 pin order and JST-PH; the net list; B.Cu-only routing with 0 vias; the R6 move and GND pour story (all match PCB/README.md, seen).
- **Unique:** the per-net "why" table is the only net-by-net explanation among the artifacts (inferred); the R6 story is also in PCB/README.md (seen), so not unique.
- **Target view:** Front panel (net reference, J1 pinout, routing notes) and Circuit (the ladders).
- **Effort:** S. Static HTML and one SVG; only the outline figure needs updating or a "176 × 52, before compression" caption.
- **Risks:** Google Fonts stylesheet only (seen). Already has light and dark tokens (seen). No script, no storage, no live data (seen).

### A3. TS06-FASCIA Buy List
- **URL:** (link in the owner's artifact list) · **updated** 2026-09-09 (seen, list)
- **Form:** single page, no published files, no runtime capabilities, so no asset store (seen). About 15 KB (inferred, estimated from the read).
- **Holds (seen):**
  - A tickable checklist for 15 fascia boards (10 units + 5 spares), with a live "n / N ticked" tally.
  - Step 1: one JST S6B-PH-SM4-TB side-entry SMD connector to check the footprint before the board order; Step 2: the bulk connector buy with a pack-size question, and how to spot a through-hole clone.
  - 1206 resistors (4.7 k 1 % ×100, 10 k ×100, 20 k ×100) with the reason for 1 %; cable side (PHR-6 housings, SPH-002T-P0.5 contacts, 26 AWG six-colour wire); tools (PH crimper IWS-3220 class, flux, tweezers, wick, loupe, IPA).
  - The board: TS06-FASCIA 176 × 52, 2.0 mm, ENIG "not optional" (the gold artwork); "already yours" counts for rotary, МТ1 and КМД1-1 (have 1/10/11 of 20).
  - Four open questions (listing pack size, 6-way housings in the owner's box, crimper fit, bushing stack depth).
- **Personal data:** contains seller or personal details (not copied): one seller handle next to the МТ1 levers, and marketplace listing prices.
- **Images / 3D:** none (seen).
- **Superseded by today's design:** the board line "176 × 52" (today 176 × 40, or 191.4 × 40 variants) (seen, PCB/README.md, TS06-FASCIA-variants.md); the note that the main-board end is JST-XH with an XH crimper (today's TS06-DRV J1 is a top-entry connector on a JST PH cable) (inferred from PCB/README.md "fascia cable (JST PH)").
- **Still current:** the SMD connector, resistor values and counts, cable parts, tools, ENIG requirement, and the control-part counts (inferred; not checked against PCB/TS06-*/bom.md).
- **Unique:** the purchasing checklist itself, the "have n of 20" counts, the fake-listing advice and the open buying questions (inferred unique; the repo BOMs cover the pair, not these notes). The owner's tick state lives only in the owner's browser (seen: localStorage key "ts06-buylist-v1").
- **Target view:** Parts and buying.
- **Effort:** S. Static rows plus a 20-line tick script; the only care is personal data and the tick state.
- **Risks:** localStorage for ticks (per-viewer; ticks do not move with the page, and a shared page would need a shared-state capability instead) (seen). Seller handle and prices must not be carried over verbatim (seen). Google Fonts only (seen). Dark-only palette (seen).

### A4. TERMINAL·06 Rev F
- **URL:** (link in the owner's artifact list) · **updated** 2026-09-09 (seen, list); page footer "concept plates · 09.09.2026" (seen)
- **Form:** single page, no published files, no runtime capabilities, so no asset store (seen). 344,664 bytes (seen, read). No script at all (seen).
- **Holds (seen):** concept plates 00–09 that supersede Rev E, with a sticky plate navigator and a provenance key (F FreeCAD, M calipered, C catalogue, A assumed).
  - Masthead: "Two cheeks and six boards", 204.3 × 62 × 44 (was 237 × 96 × 104); 4 × ИН-12, 2 × ИН-17, 2 × ИН-15, 185 V; lit front elevation.
  - 00 Corrections (why Rev E is withdrawn: ИН-12А has 12 pins out of the rear; 19.47 width, not 25.27; ИН-17 face 14 × 20 after three passes). 01 The part: ИН-12А/ИН-15 dimension table with sources (envelope, pin field 12.40 × 17.00, ИН-17 stem Ø20, digit heights).
  - 02 The object (cheeks, "the boards are the case", lit and unlit 3/4 views); 03 Front elevation 1:1 (gaps, the "seconds read small" note, options A/B); 04 Plan: seconds pair at 20.5 centres set by the Ø20 stems; board planes z 2 / 27.5 / 42.4.
  - 05 Cheek profile 1:1 (44 × 62, direct-solder this run); 06 Exploded section (6 boards + 2 cheeks); 07 HV containment (the 185 V compartment, 6 of 8 faces closed, 2 rules); 08 Scale 1:1 against a phone and a mug; 09 Five open items, ranked; note that MIMI-06 and SCALER-06 still carry the Rev E ИН-12 error.
- **Images / 3D:** 10 inline SVGs, about 313 KB of the 345 KB (the two 3/4 heroes are ~86 KB and ~84 KB; the front elevation 32 KB appears twice) (seen). No raster, no data URIs, no 3D (seen). The footer says the drawings come from rev_f.py; render/rev_f.py and render/build_revf.py are in the repo (seen by name).
- **Superseded by today's design:** the whole architecture (six boards incl. a tube board and a main board, no enclosure, 204.3 × 62 × 44, z planes, direct-solder tube board, cheek at 6.0 mm) is superseded by the TS06-DISP + TS06-DRV rev B pair (191.4 mm) in a 204.4 × 122.8 × 81.6 case (seen, PCB/README.md). The control legend in the hero (RUN/TIME/DISP/AMB/INFO/DATE, SET/ADJ, ▲▼) is superseded by the rev B control scheme (seen, compare A1).
- **Still current:** the ИН-17 stem Ø20 → 20.5 mm seconds spacing (PCB/README.md cites "concept Rev F" for it, seen); ИН-12А geometry from 3d/IN12.FCStd (seen); the two-cheeks idea (3d/case-pair/README.md "keeps Rev F's idea", seen); ИН-15 treated as the ИН-12 body (inferred still used).
- **Unique:** the corrections record (why Rev E was withdrawn, the ИН-17 three-pass story), the provenance-marked dimension table, the HV containment reasoning and the 1:1 scale plate, as a page (inferred). A browser-saved copy of this same version is in the repo at knowledge/TERMINAL·06 Rev F.html (seen, same footer date), and knowledge/TERMINAL-06-concept-plates.txt holds the Rev F plate text source (seen by header).
- **Target view:** History, dated 09.09.26, marked "superseded by TS06-DISP + TS06-DRV rev B and the pair case"; the ИН-17 spacing finding and the part table cross-linked from Product/Case.
- **Effort:** M. No script and no images to move, but 313 KB of SVG with shared gradient ids (ff-, r1- prefixes) must be carried whole or re-rendered from render/rev_f.py; heavy for one view.
- **Risks:** big inline SVG (about 0.3 MB) with blur filters, slow on phones (inferred); duplicate SVG ids if merged with other plate sets (seen prefixes, collision risk inferred). Google Fonts only. Dark-only palette (seen).

### A5. TERMINAL-06 Plate Set
- **URL:** (link in the owner's artifact list) · **updated** 2026-09-05 (seen, list). Page is concept plates **Rev E**, rail date 02.09.2026, footer "Rev E · 01.09.2026" (seen).
- **Form:** single page, no published files, no runtime capabilities, so no asset store (seen). 372,296 bytes (seen, read). One inline script, about 15 KB (seen).
- **Holds (seen):** "Open Deck" Rev E, 8 plates against spec Rev D.2; its footer says it **supersedes the earlier TERMINAL-06 Open Deck page** (same Rev E content plus plates 01A–01C).
  - Masthead: 10 glass + 1 LED, face 176 → 237 mm, rotary 6 pos / 160°, refresh "401 Hz · blocked", cost ≈10 600 ₽/unit, retail 27 000 ₽.
  - 00 Six corrections to Rev C (10 glass, ~32°/step, rotary Ø26.94, МТ1 bushing 7.85, XS3 8-pin, no trench/brow). 01 Hero 3/4 and a **live lit front elevation** with an effects player (flip effects 0–5, glitch, anti-poison sweep, ИН-15 idle cycle, night dim, backlight breathe) on the firmware's own timings.
  - 01A night 3/4 and rear 3/4; 01B left 3/4, right profile, plan (the Rev D plinth overhang error); 01C exploded, fascia ×2.6, scale 1:1. 02 Case section (plinth, "open deck", 185 V safety note, PETG print settings). 03 General arrangement (tube centres table, annex gap, "grow the fascia to 237").
  - 04 Dial study (32°/step, click-a-screen legend RUN/TIME/DISP/AMB/INFO/DATE). 05 Effects table from the AlexGyver source (6 flip effects with step times, glitch, cathode sweep, colon/backlight, the DOT_BRIGHT 35/15 correction). 06 Cost per unit by group, Rev D.2 vs Rev E, and the P2 ghosting blocker. 07 Listing kit: marketplace title, tags, ten photo slots, video plan, rear panel.
- **Images / 3D:** 16 inline SVGs (largest ~78 KB, ~40 KB, ~39 KB, ~37 KB) (seen); lit elevation is HTML/CSS tubes animated by script (seen). No raster, no data URIs, no 3D (seen).
- **Superseded by today's design:** all the Rev E geometry: 237 × 104 × 96 case with a plinth, tubes standing on a deck (withdrawn by Rev F because the ИН-12А was drawn wrong), 237 mm fascia, rotary Ø26.94 and 32°/step (withdrawn: Ø25.00, 30°/step, see A1), XS3 8-pin panel cable, one main board with daughterboards, the RUN/TIME/… legend, 401 Hz "blocked" status (seen in Rev F and PCB/README.md; today's build is the DISP + DRV pair in a 204.4 × 122.8 × 81.6 case).
- **Still current:** the effects descriptions and timings (from the firmware, inferred still valid; the repo firmware README confirms effects extended to six tubes and the DOT_BRIGHT 35/15 discrepancy, seen); the 185 V "bleed before touching" safety wording (inferred).
- **Unique:** the interactive effects player, the per-group unit cost table and pricing, and the marketplace listing kit (title, tags, 10 photo slots, video plan) (inferred unique; Open Deck A6 is the earlier copy of most of it). The effects table overlaps repo knowledge/ANIMATIONS-effects-reference.txt (seen by name only).
- **Target view:** History (Rev E, 01–05.09.26, "superseded by Rev F, then by the DISP + DRV pair"); the effects player could feed Product; listing kit and cost could feed Parts and buying (flagged as Rev E era).
- **Effort:** L. 16 large SVGs plus a script-driven tube stage with shared ids (gt, bt, tf-…); the effects player must be re-hosted and retested; cost and listing content must be dated.
- **Risks:** big inline SVG (~0.3 MB) and a timer script (setInterval, reads the viewer's clock) (seen); business figures (cost, retail, founder price, marketplace name) are sensitive to publish (inferred). No storage, no fetch (seen). Dark-only (seen).

### A6. TERMINAL-06 Open Deck
- **URL:** (link in the owner's artifact list) · **updated** 2026-09-02 (seen, list). Concept plates Rev E, rail date 02.09.2026 (seen).
- **Form:** single page, no published files, no runtime capabilities, so no asset store (seen). 184,896 bytes (seen, read). One inline script, about 15 KB (seen).
- **Holds (seen):** the Rev E "Open Deck" set: masthead, plates 00 (corrections), 01 (hero + live lit front elevation with the effects player), 02 (case section), 03 (general arrangement), 04 (dial study), 05 (effects table), 06 (cost), 07 (listing kit).
- **Relation to A5 (seen, by diff):** a strict subset of TERMINAL-06 Plate Set. All 8 of its SVGs appear verbatim in the Plate Set, the script is byte-identical, and the text differs only by the title, the Plate Set's added plates 01A–01C and its "supersedes the earlier Open Deck page" note.
- **Images / 3D:** 8 inline SVGs (largest ~78 KB) plus the CSS/script tube stage (seen). No raster, no data URIs, no 3D (seen).
- **Superseded by today's design:** everything that is superseded in A5 (Rev E geometry, 237 mm face, rotary Ø26.94 / 32°, XS3 8-pin, old legend) (seen, as A5). It is also superseded as a page by A5 itself (seen).
- **Still current:** as A5 (effects descriptions) (inferred).
- **Unique:** nothing. Every element is also in A5 (seen, by diff).
- **Target view:** History, as an alias of A5 ("earlier copy of Rev E, 02.09.26"); nothing to migrate beyond a dated link.
- **Effort:** S. Record it as a pointer to A5; migrate A5 only.
- **Risks:** none beyond A5's (timer script, big SVG); migrating both would duplicate ids and content (inferred).

### A7. Terminal·06 Concept Plates (24.08) — content is **Rev C**
- **URL:** (link in the owner's artifact list) · **updated** 2026-08-24 (seen, list). Live version id 1787603586 = published 2026-08-24 20:33 UTC (seen id; reading it as a UTC timestamp is inferred).
- **Form:** single page, no published files, no runtime capabilities, so no asset store (seen). 420,538 bytes (seen, read). No script (seen).
- **Holds (seen):** "Concept plates · Rev C", six plates plus notes.
  - Fact strip: 4 + 2 tubes, 6 screens, 185 V, 401 Hz, 27 000 ₽ list price, 10 units.
  - Plates 01 three-quarter hero (27° yaw, trench and brow), 02 front elevation lit, 03 rear panel (12 V ⌀8 barrel, USB slot, vent, 185 V warning, no power switch), 04 general arrangement 1:1 (520 × 297 sheet; front, profile, fascia, TS06-SEC; panel dims unverified), 05 dial study (30° vs 60° per step), 06 listing banner (image).
  - "What Rev C changed" table (Rev A → Rev C: controls, power, backlight, colon, A6/A7 ladders, panel cable XS1 6-pin JST-XH, 2.0 mm fascia, tube envelopes, price). "Three things still open" (nothing on the fascia measured; control firmware not written; whether marketplace payouts work).
  - Ten photo slots; a reference board of 9 external links (market and case-form references); "How to read these" (spec vs chosen vs interpretation; tube pitch 24.5/49.5/81.5/106.5, colon 65.5, ИН-17 137/155).
- **Personal data:** the reference board contains seller or personal details (not copied): shop names, listing URLs and one personal build-log site.
- **Images / 3D:** 11 inline SVGs (largest ~76 KB, ~67 KB, ~47 KB, ~33 KB) and **one inline JPEG data URI** (listing banner, 1800 × 1013, ~123 KB decoded, ~164 KB as base64) (seen). No 3D (seen).
- **Superseded by today's design:** all of it: the 176 × 96 × 78 wedge with trench and brow, 6-tube row (no ИН-15), one ИНС-1, XS1 on JST-XH, TS06-SEC board, tube envelopes 22 × 24 (Rev F: 19.47 × 28.86 with rear pins) (seen, against Rev F and PCB/README.md). Superseded in turn by Rev E (A5) and Rev F (A4).
- **Still current:** the A6/A7 ladder idea and 185 V rail (seen in PCB/README.md); the "firmware forked from AlexGyver NixieClock v2.5" credit (seen, repo README).
- **Unique:** the Rev A → Rev C change table, the "three things still open" note (incl. the payout question), and this listing-banner JPEG (differs from A8's JPEG) (inferred unique among artifacts). The drawings can likely be regenerated from render/render*.py (inferred from render/README.md).
- **Target view:** History (Rev C, 24.08.26, "superseded by Rev E, then Rev F, then the DISP + DRV pair").
- **Effort:** M. No script, but ~0.4 MB of SVG + base64 JPEG; the JPEG should become an asset; external links must be reviewed for personal data.
- **Risks:** big inline data (164 KB base64 JPEG) (seen); duplicate filter ids inside its own SVGs (h-g1..h-g3 defined twice, seen) and id collisions with A8 if both are merged (inferred); external links to third-party shops (seen).

### A8. Terminal·06 Concept Plates (25.08) — content is **Rev A**
- **URL:** (link in the owner's artifact list) · **updated** 2026-08-25 (seen, list). Live version id 1787530092 = published 2026-08-24 00:08 UTC (seen id; timestamp reading inferred). **Shared with anyone with the link** (seen, read header: viewers see this version).
- **Form:** single page, no published files, no runtime capabilities, so no asset store (seen). 370,860 bytes (seen, read). No script (seen).
- **Holds (seen):** "Concept renders · Rev A", five plates: 01 hero (brow overhang at 74.5 mm), 02 front elevation lit (IN-12 at 30/52/86/108, IN-17 at 136/152; controls SET · PWR · LUM · PROG · ADJ), 03 rear panel, 04 general arrangement 1:1 (fascia pitch 22/42/24/24/42, ⌀12.2 and ⌀13.2 holes), 05 listing banner (image). Fact strip: 6 tubes, 185 V, 401 Hz, ±2 ppm, $329, 10 units. Same reference board (9 links), ten photo slots (lever/backlight version), "How to read these" and the insignia statement (hexagon mark "06", no franchise marks).
- **Personal data:** same reference board, contains seller or personal details (not copied).
- **Images / 3D:** 9 inline SVGs (largest ~74 KB, ~58 KB, ~47 KB) and one inline JPEG data URI (banner 1800 × 1013, ~124 KB decoded, ~165 KB base64; a different file from A7's) (seen). No 3D.
- **Superseded by today's design:** everything (Rev A controls with hardware power and backlight levers, $329 pricing, 6-tube row, wedge case) (seen, A7's own change table says so).
- **Still current:** the insignia idea (hexagon "06" mark, no franchise marks) (inferred; not checked against today's silkscreen).
- **Unique:** the Rev A control set and dimensions, the insignia statement, and this banner JPEG (inferred unique).
- **Target view:** History (Rev A, 24.08.26, "superseded by Rev C").
- **Effort:** M, for the same reasons as A7; S if History keeps only a dated summary plus the banner asset.
- **Risks:** the page is link-shared, so its URL may be in use outside (seen share state); big inline JPEG; duplicate filter ids (seen); third-party links (seen).

### A7 vs A8: do the two Concept Plates copies differ? — **Yes, they are two different revisions** (seen)
- A7 (HgeS7…, listed 24.08) is **Rev C**, 6 plates, 420,538 bytes, 11 SVGs, priced 27 000 ₽; A8 (5GQY…, listed 25.08) is **Rev A**, 5 plates, 370,860 bytes, 9 SVGs, priced $329.
- A7 adds the dial study plate, the "What Rev C changed" table and "Three things still open"; A8 has the insignia paragraph and the lever-based controls.
- The listing banner JPEGs are different files (different hashes, same 1800 × 1013 size). The 9 reference links are the same in both.
- The list dates run opposite to the content: A8's content is older (version stamp 24.08 00:08 UTC) than A7's (24.08 20:33 UTC). A8's later "updated" date likely comes from its link share, not a content change (inferred).

### A9. Terminal 06 3D model
- **URL:** (link in the owner's artifact list) · **updated** 2026-08-25 (seen, list). Page title "TERMINAL·06 — 3D model". **Shared with anyone with the link** (seen, read header).
- **Form:** single page, no published files, no runtime capabilities, so no asset store (seen). 649,879 bytes (seen). It is a **self-unpacking bundle**: a loader script, a 28 KB page template and a 602 KB base64 manifest of 11 gzipped entries, unpacked in the browser into blob URLs (seen).
  - Manifest (seen): three.js r184 sources incl. OrbitControls, OBJExporter and GLTFExporter (~914 KB unpacked, ~292 KB base64); the viewer element (~16 KB); a three.js loader (~1 KB); the **TERMINAL-06 model factory** `buildTerminal06(THREE)` (~20 KB); 7 embedded Inter woff2 font files (~219 KB unpacked). No external script, font or data URL (seen: ext_resources empty).
- **Holds (seen):** a header "TERMINAL · 06 · Six-digit nixie instrument · Rev C · 176 × 96 × 78 mm · 12° fascia rake · 4 + 2 cold-cathode tubes" over a full-window orbitable 3D stage (studio lighting, shadows) with download/export (OBJ, glTF) of the model. The model is built procedurally in millimetres from the Rev C plates: raked lower body, recessed fascia, trench with liner, orange PETG brow, embossed insignia, feet, ИН-12А (22 × 24, digit 18) and ИН-17 (15 × 20, digit 8) envelopes with single-wire numerals and anode screens, ИНС-1 colon lamps, engraved control-field dividers. A small maker badge sits bottom right.
- **Images / 3D:** real-time 3D (WebGL), procedural geometry, no mesh files; a small inline SVG placeholder thumbnail (seen). No raster images.
- **Superseded by today's design:** all of it: the Rev C body (176 × 96 × 78, trench and brow), 6 tubes with no ИН-15, 22 × 24 ИН-12 envelope standing in a trench (seen against Rev F and PCB/README.md). The product page already shows today's assembly in 3D (seen in the approved plan, the repo's approved migration plan (outputs folder, TS06-artifact-migration-plan.md)).
- **Still current:** nothing of the geometry; the idea of an exportable model is reused by the product page (inferred).
- **Unique:** the only 3D model of the Rev C concept, and its model-factory code (~20 KB) (inferred unique; no Rev C 3D in the repo's 3d/ folder, which holds FreeCAD parts and the pair case; checked by file name only).
- **Target view:** History (Rev C in 3D, 25.08.26, "superseded by the DISP + DRV pair model on the Product view").
- **Effort:** M. Keep it working as its own file (the bundle can be published unchanged as a supporting HTML page) or export a GLB once and show it in the page's existing viewer; either way no content rewrite, but testing the WebGL path is needed.
- **Risks:** heavy page (650 KB, ~1.2 MB unpacked JS/fonts) (seen); needs WebGL and DecompressionStream (seen in loader); a second copy of three.js next to the product page's own viewer (inferred); link-shared URL may be in use outside (seen); maker badge links out (seen).

### B1. MIMI-06 Kuro
- **URL:** (link in the owner's artifact list) · **updated** 2026-09-02 · pinned (seen, list). Variant study Rev 2 "KURO", rail 02.09.2026, footer 01.09.2026 (seen).
- **Form:** single page, no published files, no runtime capabilities, so no asset store (seen). 332,371 bytes (seen). One inline script, ~9 KB (seen).
- **Holds (seen):** the "cute" sibling of TERMINAL-06 in a dark colourway, with a 16-digit 5 × 7 character VFD under the tube row.
  - Masthead: display module 150 × 25 mm in a 148 × 26 window, bit-banged SPI, text faces not bitmaps, retail 31 000 ₽.
  - 01 The face: 3/4 hero and lit front elevation with a **live VFD** (canvas) and a state player (idle, greeting, night, alarm, wink, setting; auto-cycle, scroll) showing kaomoji frames.
  - 02 The display decided (three sourcing paths; 6/8/16-digit table; command set; three open items). 03 Timing: why SoftwareSerial breaks the 416 µs multiplex slot, bit-banged SPI on D0/D1 instead.
  - 04 KURO palette, shell 176 × 104 × 72, light discipline, "KURO is cheaper than MILK", the fascia split from TERMINAL-06 Rev E. 05 Deltas vs TERMINAL-06 Rev E and open items (price/MOQ, CGRAM, SPI vs ISR).
- **Personal data:** none seen; sourcing is described by marketplace type only (seen).
- **Images / 3D:** 3 inline SVGs (~205 KB hero, ~74 KB, ~13 KB) and one canvas drawn by script (seen). No raster, no data URIs, no 3D.
- **Relation to TERMINAL-06:** built on Rev E (237 mm face, TS06-SEC, shared tube board pitch 24.5/49.5/81.5/106.5), all since superseded for TERMINAL-06 by Rev F and the DISP + DRV pair (seen, PCB/README.md); Rev F notes MIMI still carries the Rev E ИН-12 error (seen, A4).
- **Unique:** the VFD sourcing decision, the SPI-vs-multiplex timing argument and the live kaomoji player (inferred unique among artifacts). A browser-saved copy of this same version is in the repo (knowledge/MIMI-06 Kuro.html, same rail date and footer, seen); the earlier study is in the repo's outputs folder (MIMI-06-variant-study.md) (seen by name).
- **Target view:** Family (card: MIMI-06 Kuro, Rev 2, 01–02.09.26, "built on TERMINAL-06 Rev E; not updated for Rev F or the pair").
- **Effort:** M as a full page (big SVG + script), S as a Family card with a link and one image.
- **Risks:** ~0.3 MB inline SVG and a timer script (setInterval, Date) (seen); Google Fonts only (seen); dark-only (seen).

### B2. Mimi·06 Concept Plates
- **URL:** (link in the owner's artifact list) · **updated** 2026-08-25 · pinned (seen, list). Variant study "against TERMINAL·06 Rev C" (seen).
- **Form:** single page, no published files, no runtime capabilities, so no asset store (seen). **2,323,067 bytes** (seen), the largest page in scope. No script (seen).
- **Holds (seen):** the first MIMI-06 study (milk PETG, blush brow, ears, 128 × 32 graphic VFD), 176 × 74 × 118 mm, 31 000 ₽.
  - Four views: 3/4 lit, 3/4 daylight, front elevation lit, front elevation daylight (two lighting setups for a cream shell).
  - "Six states, one panel": the VFD expression frames (image). Delta table against TERMINAL·06 Rev C (shared tube board, TS06-SEC, fascia 176 × 52, controls; hardware UART on D0/D1; materials ≈11 600 ₽).
  - "Six things to settle first" (UART vs ISR timing, send text not frames, VFD brightness vs tubes, milk PETG finishing, shared open items, different buyer tags). Listing kit: shop banner (image).
- **Images / 3D:** 4 inline SVGs of ~370–480 KB each (~1.7 MB, dot-by-dot VFD matrices) and **2 inline JPEG data URIs**: VFD expression sheet 1900 × 1185 (~349 KB base64) and shop banner 1800 × 1013 (~243 KB base64) (seen). No 3D.
- **Relation to MIMI-06 Kuro:** superseded by B1, whose footer says it supersedes the milk colourway and the 128 × 32 graphic-VFD assumption (seen in B1).
- **Unique:** the milk colourway renders (lit and daylight), the 128 × 32 face frames and the MIMI banner (inferred unique among artifacts). A browser-saved copy is in the repo (knowledge/Mimi·06 Concept Plates.html, same header and footer text, seen).
- **Target view:** Family (as MIMI-06's history, dated 25.08.26, "superseded by MIMI-06 Kuro").
- **Effort:** M. No script, but 2.3 MB of inline data: the two JPEGs should become assets and the four SVGs likely too (or be replaced by rasters).
- **Risks:** **big inline data** (2.3 MB page; 1.7 MB SVG, 0.6 MB base64) (seen); pinned by the owner (seen); has light and dark tokens already (seen).

### B3. QUADRANT Desk Miniature
- **URL:** (link in the owner's artifact list) · **updated** 2026-09-05 (seen, list). Concept plates Rev 2, 02.09.2026; plate 01A is marked Rev 3 (seen).
- **Form:** single page, no published files, no runtime capabilities, so no asset store (seen). 99,620 bytes (seen). One inline script, ~3 KB (seen).
- **Holds (seen):** QUADRANT, a 2 × 2 ИН-17 desk miniature (74 × 82 × 78 mm, ~340 g), respecified after the ИН-17 turned out to be end-view only; the wristwatch on ИН-17 is withdrawn.
  - 00 Corrections (end-view only; no rear pair; lead labour drops). 01 Hero and a **live 2 × 2 tube face** (script, reads the viewer's clock). 01A night 3/4. 02 General arrangement (window, not a plinth; what a desk object does not need).
  - 03 Drive: static 2 × HV5622, no multiplex, so no P2 ghosting; matched-quad binning. 04 The wrist sibling QUADRANT-W on ИН-16 against two market competitors. 05 Cost and price (≈3 500 ₽ per unit, proposed 15 000 ₽). 06 Open items in order.
- **Personal data:** contains seller or personal details (not copied): marketplace seller handles and shop names with stock counts and prices in the cost table, plate 04 and plate 06.
- **Images / 3D:** 4 inline SVGs (~35 KB, ~19 KB, ~6 KB, ~4 KB) plus the CSS/script tube face (seen). No raster, no data URIs, no 3D.
- **Relation to TERMINAL-06:** a separate product that borrows the shop's 170–185 V practice and ИН-17 data; its ИН-17 face note (20 × 15) differs from Rev F's 14 × 20 reading (seen both; which is right is not checked).
- **Unique:** the QUADRANT concept itself (desk and wrist), the ИН-17 viewing-axis finding and the QUADRANT-W costing (inferred unique among artifacts). The repo holds a browser-saved copy with the same plates 00–06 incl. 01A (knowledge/QUADRANT Desk Miniature.html, seen) and knowledge/QUADRANT-D-spec.txt and the outputs folder's QUADRANT-wrist-feasibility.md (seen by name).
- **Target view:** Family (card: QUADRANT desk miniature, Rev 2/3, 02–05.09.26).
- **Effort:** S. Small page (100 KB), one short script; only the personal details need scrubbing.
- **Risks:** seller handles and prices (seen); timer script reading the viewer's clock (seen); Google Fonts only; dark-only (seen).

### B4. SCALER-06 Decatron
- **URL:** (link in the owner's artifact list) · **updated** 2026-09-02 (seen, list). Concept plates Rev 2, 02.09.2026 (seen).
- **Form:** single page, no published files, no runtime capabilities, so no asset store (seen). 136,431 bytes (seen). One inline script, ~11 KB (seen).
- **Holds (seen):** SCALER-06, "fourth product · decatron · not a clock": an ОГ-3 decatron ring that steps once per event, with a five-source mode switch (background Geiger, avalanche entropy, mains, audio, external jacks, off), ≈400 V shared rail, 150 × 190 × 120 half-rack module, proposed 24 000 ₽.
  - 01 One step per event: hero and a **live panel simulation** (mode buttons, "bring near" sources, CPM trace, inject a pulse). 02 Five things to count (the correction that made it demonstrable; reuses TERMINAL-06's six-position rotary and A6 ladder). 03 Which decatron (8-pin scaler vs 13-pin readable vs 15-pin imports; ОГ-3 glows violet).
  - 04 One rail, two tubes (СБМ-20 and ОГ class share ~400 V; ИН-2 rate digits with an ИН-15А prefix). 05 Parts and sources. 06 Form and finish (half-rack lab module). 07 What it must never claim (not a dosimeter) and open items.
- **Personal data:** contains seller or personal details (not copied): seller handles and shop names with stock counts and prices (plates 02, 03, 05).
- **Images / 3D:** 6 inline SVGs (largest ~65 KB) plus a script-driven simulation (seen). No raster, no data URIs, no 3D.
- **Relation to TERMINAL-06:** shares the six-position rotary and A6 ladder approach and the ИН-15А (seen); Rev F notes SCALER still carries the Rev E ИН-12 error in its plates (seen, A4).
- **Unique:** the SCALER-06 concept and its five-mode simulation (inferred unique among artifacts). The repo holds a browser-saved copy with the same seven plates (knowledge/SCALER-06 Decatron.html, seen) and knowledge/SCALER-06-spec.txt (seen by name). The footer cites a sellers register and a concept watchlist in the owner's notes folder (not in this repo; inferred to be the Meshok pages' sources).
- **Target view:** Family (card: SCALER-06 decatron, Rev 2, 02.09.26).
- **Effort:** S–M. Small page (136 KB), but the simulation script must keep working, and seller details must be removed.
- **Risks:** seller handles and prices (seen); timer + random-number simulation (seen); safety wording ("not a dosimeter") must travel with it (seen); dark-only (seen).

### B5. Staircase Nixie Clock
- **URL:** (link in the owner's artifact list) · **updated** 2026-08-25 (seen, list). "Build specification · Rev A · 25 Aug 2026" (seen).
- **Form:** single page, no published files, no runtime capabilities, so no asset store (seen). About 24 KB (inferred, estimated from the read; small enough to be returned inline). No script (seen).
- **Holds (seen):** a separate concept: a tiered HH:MM:SS clock from eight upright tube types (IN-18, IN-8-2, IN-14, IN-16, IN-2, IN-19A/B, IN-1) on one 190 V rail, statically driven.
  - 01 Elevation (four tiers, 20 mm risers, rising character centreline). 02 Tube roster (view, character height, envelope, voltages, currents, termination, role; flat types excluded).
  - 03 Why each tube sits where it sits. 04 Anode resistors per position (formula, fitted values, 30.7 mA total, 5.83 W; "do not use an NCH8200HV"). 05 Supply and drive (190 V rail, HV5622 × 3, static not multiplexed, bleeder and sequencing).
  - 06 Mechanical (riser formula, character-position table, mostly estimates). 07 Cautions (IN-19 poisoning, glyph mismatch, blue spot, 190 V safety, life). 08 Open items (built from datasheets only, without the project files).
- **Personal data:** none seen. Footer links to public datasheet pages (seen).
- **Images / 3D:** one small inline SVG elevation using CSS variables (seen). No raster, no 3D.
- **Relation to TERMINAL-06:** none structural: it excludes the ИН-12 and ИН-15 flat tubes and says it was written without the project documents (seen).
- **Unique:** the whole staircase concept, its tube roster and resistor table (inferred unique; not found by name in the repo's knowledge/ list, checked by file name only).
- **Target view:** Family (card: Staircase clock, Rev A, 25.08.26, marked "standalone study, not part of TERMINAL-06").
- **Effort:** S. Small static page with light and dark tokens already.
- **Risks:** external datasheet links (seen); none else (no script, no storage).

### B6. Not a Nixie
- **URL:** (link in the owner's artifact list) · **updated** 2026-08-28 (seen, list). Dated 27 August 2026 in the page (seen).
- **Form:** single page, no published files, no runtime capabilities, so no asset store (seen). About 40 KB (inferred, estimated from the read; returned inline). No script (seen).
- **Holds (seen):** a buyer's analysis of seven auction tabs of Soviet gas-discharge panels, none of which is a nixie.
  - Masthead: two seller claims ruled on (the ИГПВ is not a nixie; ГИПС-16-1 is elegant, not the most capable). 01 What a nixie is (shaped cathodes; the word and its Russian flattening).
  - 02 Four mechanisms with diagrams (shaped cathode, DC matrix, AC memory plasma, self-scan). 03 The seven listings ruled on (type, spec side panel, drive difficulty). 04 Pixel density ranked (pitch, dots/cm², fill).
  - 05 Reading Soviet part-number prefixes (ИН, ИВ/ИЛ, ГИП, ГИПС, ГИПП/ИГПП, ИГГ/ИГПВ, suffix Л). 06 If you want one in a device: buy/skip verdicts, incl. a character plasma module or a ГИПС-16-1 as a status line for TERMINAL-06.
- **Personal data:** contains seller or personal details (not copied): seller names and cities, a quoted private correspondence with a seller, listing numbers and prices, and links to the listings.
- **Images / 3D:** 4 small inline SVG mechanism diagrams using CSS variables (seen). No raster, no 3D.
- **Relation to TERMINAL-06:** suggests a second (plasma or self-scan) status display alongside the nixies; not adopted in today's design (DISP + DRV carry no such display, seen in PCB/README.md).
- **Unique:** the mechanism explainer, the prefix decoder and the density ranking are reusable reference; the listing verdicts are dated market notes (inferred unique among artifacts).
- **Target view:** Family (as "Tube and display reference"; the generic parts 01, 02, 04, 05 only). The listing section belongs with the buying notes and must be scrubbed.
- **Effort:** M. Small and static, but the personal and listing details are woven through section 03 and 06 and need careful editing.
- **Risks:** personal data and a private correspondence (seen); 20+ external links incl. auction listings (seen). Has light and dark tokens (seen).

### B7. Meshok Tube Board
- **URL:** (link in the owner's artifact list) · **updated** 2026-08-25 (seen, list). Page stamp "Updated 25 Aug 2026" (seen).
- **Form:** single page, no published files, no runtime capabilities, so no asset store (seen). 65,988 bytes (seen). No script (seen).
- **Holds (seen):** a procurement board for indicator tubes across twelve auction-site sellers, ranked by what disappears if you wait.
  - Masthead tallies (watched lots, lots at the sellers, unwatched lots found, live auctions). 01 What is actually on a clock (one live auction; a secured purchase for TERMINAL-06's ИН-17 seconds tubes; a date rail of expiring lots).
  - 02 The scarcity ladder: 21 part rows (price, stock, scarcity class, other sources, which concept each unblocks, incl. TERMINAL-06's ИН-17 and ИН-12 restock).
  - 03 Seller profiles (12 cards). 04 Three ways to spend it (probe / line / shelf baskets). 05 What this does to the tier list. 06 Parts worth a new concept.
- **Personal data:** **contains seller or personal details (not copied)**: seller handles, profile ids, cities, ratings, terms, stock and prices per seller, the owner's purchases, cart and budget.
- **Images / 3D:** none (seen: no SVG, no images).
- **Relation to TERMINAL-06:** supply notes for ИН-17, ИН-12А/Б, ИН-15А, ИНС-1 and sockets (seen); prices dated 25.08 and not re-checked (inferred stale).
- **Unique:** the sourcing research as of 25.08 (inferred unique; SCALER-06 cites a sellers register that is not in this repo).
- **Target view:** Family (a dated, **anonymised** "where the glass comes from" card, per the owner's group-B decision); its TERMINAL-06 rows (ИН-17, ИН-12, ИН-15А, ИНС-1, sockets) also feed Parts and buying, anonymised. The rest stays in the old page.
- **Effort:** M. No images or script, but nearly every line carries seller data, so migration means rewriting, not copying.
- **Risks:** **personal data throughout** (seen); time-bound prices, auctions and a live cart state (seen); has light and dark tokens (seen).

### B8. Meshok Watchlist
- **URL:** (link in the owner's artifact list) · **updated** 2026-08-25 (seen, list). "Rev D · concept board · not a spec" (seen).
- **Form:** single page, no published files, no runtime capabilities, so no asset store (seen). 50,411 bytes (seen). One small inline script (~0.7 KB, a "show only what changed in Rev D" filter) (seen).
- **Holds (seen):** two tier lists.
  - Part one "The shelf": 18 indicator parts tiered S/A/B/C/F by supply depth × price × driveability (e.g. ИВ-4, ИН-15А, ИН-2 in S; ИЛД3 and ИФК-120 in F with safety reasons).
  - Part two "The roster": 21 device concepts tiered S/A/B/C/LED (Marquee, Console, Groove, Cyclops; Abacus, Metric, Callsign, Pulse, Grid-32, Deka, Nighteye; Nameplate, Chorus, Monolith, Dash, Relic, Study; two Archive showcases; Halo, Ghostlight), several reusing TERMINAL-06's MPSA42 low-side switch and BCD path.
  - Corrections (ИН-28 is a grid-fired glow indicator, not a magic eye; one panel no longer purchasable). "Buy by seller, not by part" table. Blockers checklist (12 items).
- **Personal data:** contains seller or personal details (not copied): seller cities and terms tied to specific listings, listing prices and stock.
- **Images / 3D:** none (seen). CSS "glow chips" only.
- **Relation to TERMINAL-06:** lists TERMINAL-06, EMBER-06 and MIMI-06 as the bench for comparison (seen); no TERMINAL-06 design content.
- **Unique:** the concept roster (21 ideas) and parts tier list as of Rev D (inferred unique among artifacts; its source file is cited as WATCHLIST-concept-tierlist.md in the owner's notes folder, not in this repo).
- **Target view:** Family (as "Ideas and parts shelf", dated 25.08.26); seller rows go to Parts and buying only in anonymised form.
- **Effort:** M. Static and mid-sized, but seller details sit inside part entries and the ordering table; the filter script is trivial.
- **Risks:** seller details (seen); time-bound prices (seen); has light and dark tokens (seen).

## Proposed view map

| View | Fed by (primary) | Also fed by (secondary) | What moves |
|---|---|---|---|
| Product | — | A5 | the Rev E effects player, only if restyled for today's tube row (inferred) |
| Build | — | — | nothing in these 17 artifacts is build instructions for the pair (seen) |
| Circuit | — | A1, A2 | A6 tapped divider and A7 lever ladder with ADC codes |
| Front panel | A1, A2 | — | dial explainer, control semantics, net reference, J1 pinout, routing notes; label A1's 176 × 52 drawing as history |
| Case | — | A4 | IN-17 Ø20 stem → 20.5 mm seconds spacing; the two-cheek idea the pair case keeps |
| Parts and buying | A3 | A5, B7, B8 | fascia buy list (ticks need a shared-state decision); dated Rev E cost; anonymised TERMINAL-06 sourcing rows |
| History | A4, A5, A6, A7, A8, A9 | A1 | dated plate sets, newest first: Rev F 09.09 → Rev E 01–05.09 (A6 as alias) → Rev C 24.08 (+ 3D model 25.08) → Rev A 24.08; each marked "superseded by …" |
| Family | B1–B8 | — | one dated card per sibling (MIMI-06 with its earlier study, QUADRANT, SCALER-06, Staircase) plus a reference shelf (Not a Nixie, Watchlist, Tube Board), all anonymised |

## Suggested migration order

1. **Front panel: A2 (S), then A1 (M).** Current content, highest value, small. A1's script-built drawings are the first real porting test.
2. **Circuit (secondary): the ladders from A1/A2.** Same material, done together with step 1.
3. **Parts and buying: A3 (S)**, then the anonymised TERMINAL-06 rows from B7/B8. Decide first whether ticks become shared state or are dropped.
4. **History: A4 Rev F (M)**, cross-linking its still-current findings to Case.
5. **History: A5 Plate Set (L)**, with A6 as a dated alias only.
6. **History: A7 and A8 (M each)**: move both banner JPEGs into the asset store first.
7. **History: A9 3D model (M)**: publish the bundle as its own file, or export one GLB for the page's viewer.
8. **Family, easy cards first: B5, B3 (S), B4 (S–M), B1 (M).**
9. **Family, heavy or sensitive last: B2 (M, 2.3 MB → assets), then B6, B8, B7 (M, personal-data rewrite with the owner's review).**

Why this order: current before history, small before large, and pages with personal data last, when the pattern is settled and a reviewer can check each one.
