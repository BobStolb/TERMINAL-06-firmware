# Fascia R rev B: J1 upright (the study and the change)

**The owner, 7 October 2026, about 14:50 UTC, after seeing the six-wire lead on the product page, verbatim:**

> wiring looks good, noe that I look at ot maybe we change the connector from a 90 degree bend to normal upright? so we
> don't have the bending wire at the base for no reason

Rev A had a JST **S6B-PH-SM4-TB** (SMD, side entry) as J1 on the back of the fascia, its mouth towards the bottom edge. The lead lay
along the board, went down the raked face and bent 90 + 12 degrees onto the floor; the case model dropped the floor 7.3 mm for that bend
(`3d/case-pair/checks.md`, row 8). Rev B has a JST **B6B-PH-SM4-TB** (SMD, top entry): the plug stands straight off the back, and the
six wires leave its top straight back into the case, so they reach the floor with a gentle S instead of a tight turn.

Marks: *inferred* = no datasheet or measurement gave the number; *assumed* = a catalogue-typical value nobody has measured. KiCad's
library, the repository's boards and the case model are the sources named; the JST datasheet could not be read (below).

## Part 1: does an upright J1 fit? Yes. Nothing failed.

### The part

| | |
|---|---|
| Part | JST B6B-PH-SM4-TB: PH, 2.0 mm pitch, 6 way, top entry, SMD, two retention tabs |
| Footprint | KiCad 10's `Connector_JST:JST_PH_B6B-PH-SM4-TB_1x06-1MP_P2.00mm_Vertical` (JST's drawing, drawn by KiCad), read from the `kicad:10.0` image. Pads 1.0 x 5.5 on 2.0, the last 2.5 mm of each (towards +y) outside the body are the solder tails; tabs 1.6 x 3.0 at x +-7.4; body outline x +-7.975 (the metal tabs included), y -4.25..0.75 (5.0 deep); pin contacts at y -2.5; courtyard 17.4 x 8.5 |
| 3D model | KiCad's library has **no model** for either SM4-TB part (its GitLab tree lists only `JST_PH_B6B-PH-K` and `JST_PH_S6B-PH-K`). Drawn here, as the repository does (`3d/populated/models/smd_fascia.scad`, variant `jst_b6b_sm4_back`): plastic 13.9 x 5.0 x 6.0 |
| Header height off the board | **6.0 mm, inferred**: the 6.0 of KiCad's STEP of the through-hole B6B-PH-K (read for this: x 13.9, y 4.55, z 6.0; the same PH body) and JST's catalogue listing as remembered. The SM4-TB datasheet was not read: `jst-mfg.com` is blocked by this environment's egress policy (CONNECT refused), and no other host was tried |
| Mated height with a PHR-6 | **9.5 mm off the board, assumed**: the case model's `J1_MATED_H`, which it uses for TS06-DRV's B6B-PH-K (the same header height and housing). The housing shows 3.5 mm above the header |
| Where the wires leave | The housing's top face, straight up from the pin row: on the fascia, straight **back** along its normal (back and 12 degrees down), 6 wires side by side along X. In the case frame the exit is at Y 6.78, Z 3.91 |
| Bend radius | `CABLE_R` 3.0 mm to the ribbon's centre line (assumed, the model's own) |

### Where it goes

J1 keeps its place between the two buttons: the footprint origin at X 155.4 (the minus button at 150.4 + 5.0), as on rev A, so that
**pin 6 (D8) is under the minus button's pad gap and pin 5 (D7) under its D7 pad**, and the pin order is unchanged (1 +5V, 2 GND, 3 A6,
4 A7, 5 D7, 6 D8; D8 at the left seen from the front, +5V at the right). The origin moved up from y 33.4 to **33.0**, so that the courtyard
(y 28.25..36.75) ends 3.25 mm from the bottom edge and the body (28.75..33.75) starts 2.5 mm below the buttons' landing pads (their lowest
edge is y 26.25). Pads run y 30.75..36.25.

**Pin 1 faces the plus button** (the right, +x, seen from the front; the left seen from behind). The footprint is the library part
**mirrored in X for the back**, as the side-entry one was, so the pin order on the board did not change; the silk stub beside pad 1 marks it.
The **tails point to the bottom edge**, the body stands towards the buttons. Six wires leave the plug top as a flat ribbon along X, straight back.
(A rotation of the part instead of a mirror would have put pin 1 at the left and reversed the topology D7/D8 above, A6/A7/+5V below.)

### The plug and the wires against what is near them (case model frame; `checks.md`, row 8)

| Against | Result |
|---|---|
| The two КМД1 bodies, fascia R's own SW4 and SW5 (13.75 x 16.91, 20 deep, *assumed*) | **4.30 mm** between the plug's body and the nearer body, in the plane of the fascia (both are prisms along its normal); the wires leave 5.40 mm from that body's edge |
| The buttons' landing pads (their hand wires come down beside the plug) | 2.50 mm from the plug's body |
| The kick strip | The strip starts at the fascia's bottom edge; the plug's courtyard ends **3.25 mm** above it. Rev A's plug stood below the edge, 0.5 mm from the strip (TIGHT) |
| The sill | 26.5 mm under its underside |
| TS06-DISP | 23.5 mm under its bottom edge (the plug's highest point Y 10.5) |
| The module's withdrawal sweep | The module comes out backwards (+Z), away from the plug; 38.3 mm from the plug's top to TS06-DRV's front face. The sweep row (7) is now what sets the floor: 0.50 mm |
| TS06-DRV and its J1 plug | The lead lies on the floor from Z 16.5; DRV J1's drop column is at Z 27.1, 10.6 mm further back |
| The cheeks, R's four screw bosses | 28.5 mm to the cheek, 20.1 mm to the nearest boss (r 3.5) |
| Variant D's bottom ledge (t 38.0 on) | the courtyard ends 1.25 mm above it: **no cut** (it was cut over X 146.7-165.9 for rev A's plug and lead) |
| The floor | see below; the tightest clearance of the change is the base blocks to TS06-DRV's bottom edge, **0.50 mm** (the model's own limit) |

### The lead's new route

Out of the housing along the fascia's normal (12 degrees below horizontal), an R3 bend to a 45 degree slope, 12.6 mm straight, an R3 bend
back to horizontal, then along the floor, diagonal across the case, to DRV J1's drop column, up (two R3 bends) into DRV J1 (`G["lead"]` in
the case model; the page draws the same points). **Path 143 mm against the 190 mm lead: 47 mm of slack** (rev A: 139 mm, 51 mm). The
module can still come back the ~30 mm the model says DRV J1 needs before it can be reached from below. The model's path is not a taut
shortest path; the slack is what the lead's loop on the floor takes up.

### The floor

* **The model's own rule** (`Y_FLOOR = min(0, lowest lead point - FLOOR_CLR)`): the lead's lowest point at the plug is Y 6.13, so the rule
  gives **Y 0.0**, the frame's 0: the lead no longer needs any room below the fascia.
* **A limit the rule did not carry** (it had never bound, the bend had put the floor far below it): the base's end blocks stand 8 mm
  (`END_BLOCK`) tall on the floor, and as the module slides out TS06-DRV's bottom edge (Y 4.0) must clear them by 0.5 (`MOD_CLR`, as at the
  top). That holds the floor at **Y -4.5**. At Y 0 the blocks would be 4.0 mm *into* the module's edge (row 7 used to be stamped OK whatever
  the numbers; it is computed now).
* So the floor went from **-7.3 to -4.5: the case is 2.8 mm lower, 204.4 x 120.0 x 81.0** (was 122.8 high, 81.6 deep: the toe is 0.55 mm
  shorter). Not the full 7.3 mm.
* **What would give more** (not done, it changes the base's blocks): blocks cut to 8 mm tall counting the 3 mm base (not 8 above it) let the
  floor rise to **Y -1.5**, 3.0 mm more (about 117.0 high). Say if you want it.

### By hand: can a finger push the plug in and pull it, module out?

Yes. With the rear panel off and the module drawn back, the back of the fascia is open: the plug is reached from behind. Its two long faces
are the grip: the side towards the buttons has 4.3 mm to the nearest body (a fingertip pinch needs about 3, *assumed*); the side towards the
bottom edge is open (3.25 mm to the edge, nothing under it but the kick strip further down); along X there is nothing else on the back for
28.5 mm to the cheek on the right and for most of the board to the left. The housing's top 3.5 mm above the header is the part to hold; a
PH plug has a latch-less friction fit, so pull on the housing, never on the wires. The buttons' hand wires come down 2.5 mm above the plug's
body: keep them clear when pulling.

## Part 2: what changed

| File | Change |
|---|---|
| `tools/mkfp.py`, `PCB/lib/TS06.pretty/TS06_JST_PH_B6B-PH-SM4-TB_Back.kicad_mod` | the new footprint, written like the side-entry one: SMD only on the back, **no plated hole** (spec 6), pads on B.Cu / B.Mask / B.Paste |
| `3d/populated/models/smd_fascia.scad`, `jst_b6b_sm4_back.wrl`, `tools/models3d.json` | the drawn 3D model and its mapping to the footprint |
| `tools/mkpcb_fascia_rhythm.py` | J1 is the upright part at origin y 33.0; D8 and D7 laid into the pads' top ends; the keepouts under the tails; the title block and the schematic say **rev B**; the docstring |
| `tools/mkpcb_fascia_rhythm_routes.json` | A6, A7 and +5V re-routed by `tools/netroute.py` (30 tracks; no via, stitch or jumper) |
| `PCB/TS06-FASCIA-rhythm/*.kicad_pcb`, `.kicad_sch`, `drc.rpt` | regenerated |
| `tools/dfm_check.py` | reads the revision from the board (it had `revA` in the zip's name) |
| `fab/TS06-FASCIA-R-revB-divider-holes04-fab.zip` | the new ordered zip (divider gold, holes opened 0.4 mm, level leaders); 11 files, 49 kB |
| `fab/TS06-FASCIA-R-revA-divider-holes04-notordered-fab.zip` | the rev A zip that was to be ordered, renamed, kept as a record: **not to be sent** |
| `fab/ORDER.md`, `fab/README.md`, `fab/HOLES-VARIANT.md`, `PCB/README.md`, `PCB/TS06-FASCIA-rhythm/bom.md`, `tools/mkfab.sh` (comments) | the names, the revision, the part |
| `3d/case-pair/` | `case_pair.py`, `case.scad`, `boards.json`, `params.scad`, `checks.md`, `README.md`, `out/` (STLs and pictures: they were stale since the rear panel moved from 71.2 to 69.2) |
| `3d/populated/` | R's top / iso / bottom pictures and GLB, the stack pictures and `stack.json` (the fit table did not change) |
| `tools/verify_pair.sh` | copies R's board into the case model's scratch tree |

TS06-FASCIA (F, the 176 board) and the other fascias are **untouched**: F keeps its side-entry J1 in its file, and the case model takes only J1
from R (`boards.json` `fascia_j1`, put into the 176 stand-in's parts in the stand-in's frame by `use_fascia_j1`).

### Checks

| Check | Result |
|---|---|
| KiCad DRC (`kicad-cli pcb drc --refill-zones --severity-all`) | 0 violations, 0 unconnected (every GND pad on the pour), 0 footprint errors |
| `python3 tools/dfm_check.py` | every row PASS, exit 0 (self-test 17 rows FAIL as it must); copper clearance worst 0.325 mm (rev A 0.375) |
| the gold check in `tools/mkfab.sh` | PASS: 0.00 mm2 of gold under mask, 85% open, the check on a mask without the openings FAILs as it must; the NPTH drill file holds one 9.2, four 8.4, four 2.7 |
| `bash tools/verify_pair.sh` | **27 PASS, 0 FAIL, 0 SKIP** |
| the case model | 85 rows: 68 OK, 8 TIGHT, 6 NOTE, 3 FAIL: the same three FAILs as before (two rejected jack openings by design; the boss on R5's pad, open); OpenSCAD's derivation of the floor agrees (`Y_FLOOR scad=-4.5 py=-4.5 ok`) |
| the 3D coverage (`tools/model_coverage.py`) | 136 resolved, 28 allowlisted, 0 missing |

The picture of the back with the new J1: `3d/populated/TS06-FASCIA-rhythm-bottom.png` (and `-iso.png`, `-top.png`).

### What the page will need (the next run; `recovered/viewer2/` was not touched)

* **The zip's name:** `recovered/viewer2/src/index.html` (the "R was picked" line), `recovered/viewer2/test/run.mjs` (`hzip`) and
  `recovered/viewer2/tools/order.py` (`HOLES_ZIP`) all name `fab/TS06-FASCIA-R-revA-divider-holes04-fab.zip`, which is now
  `...-revA-divider-holes04-notordered-fab.zip`; the ordered one is `...-revB-divider-holes04-fab.zip`. The Order tab's text ("rev A") too.
* **The lead and the plug:** `app.js` draws the fascia's J1 as a side-entry part (a 4.8 high box, "mouth towards the bottom edge") and the
  lead climbing the rake into it; `README.md` says the same. The lead's points now come from the case model (`LEAD` in `params.scad`: the
  fascia end is a sampled S, not one bend); the plug is 6.0 high with the mated housing to 9.5 and sits at X 155.4 on R. The text about
  "climbs the raked fascia" and the lead's numbers (143 mm path, 47 mm slack, floor 4.5 below the frame's 0) change.
* **Selector F:** F still carries the side-entry J1 at X 156.3; the case model's lead now ends on R's plug (X 155.4). Either draw the same
  lead for both and say so, or give F its own.
* **The case's size:** 204.4 x 120.0 x 81.0 (was 122.8 high, 81.6 deep), the floor, the kick strip (4.4 tall), the variant D ledge (no cut).
* **The 3D models:** J1's body and tabs from `parts.json`/`tools/kparts.py` follow the board; the model was drawn here (6.0 high).
* **The tests** that count rows or compare these strings.

### Open, skipped or refused

* The JST datasheet for the B6B-PH-SM4-TB could not be read (the host is blocked); the 6.0 mm header height is *inferred*, the 9.5 mm mated
  height *assumed*. A caliper reading of the part, or the datasheet, closes both. If the header is 6.5 or 7.0 the wires leave 0.5-1.0 mm
  further back: nothing here changes (the plug is 4.3 mm from the nearest body).
* The КМД1 depth (20) and orientation are still assumed (`measurements-KMD1 #8`).
* The floor at -4.5 is held by the base's end blocks, not by the lead; cutting them lowers the case another 3.0 mm (above).
* A dry fit with a real part and plug (the jig of `3d/jig/` can take it) would show the finger room by hand.
* There was no fascia BOM in the repository; `bom.md` here is the first (hand-written; the lead's two PHR-6 and its crimps are on TS06-DRV's).
