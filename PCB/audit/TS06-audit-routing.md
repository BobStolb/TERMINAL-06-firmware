# TS06 audit: the routing methods, and their results

Run audit-routing, 2026-11-14. Boards: `PCB/TS06-DISP/TS06-DISP.kicad_pcb` and `PCB/TS06-DRV/TS06-DRV.kicad_pcb`, rev B, at
commit 8e030d4. "Rev B" below means these two files. "Rev C" means the plan in `PCB/TS06-routing-plan.md`.

## Verdict

1. **Rev B's copper is legal and whole.** My scan and KiCad 10.0.8's DRC agree on both boards: 0 clearance errors, 0
   unconnected, 0 vias, 0 dangling ends. No Stop.
2. **Its rules are thin.** The 0.8 mm rule covers 185 V pads only: two low-voltage solder pads sit 0.65 and 0.70 mm from
   185 V tracks. No creepage rule, no width rule, no gate on quality.
3. **The method fits rev B, not rev C.** Typed coordinates plus a home-made router that cannot place a via; rev C adds
   surface-mount parts. Route DRV rev C in KiCad with a rules file; keep the scripts as checks.

## Findings

| # | About | Severity | Finding | Fix |
|---|---|---|---|---|
| R1 | rev B, DRV | **Fix before order** | The 0.8 mm HV rule is one-sided. A low-voltage pad next to a 185 V track gets 0.6. Two places: 0.65 and 0.70 mm | Make the rule cover any pad or any HV copper. Move two tracks by 0.15 mm |
| R2 | rev C | **Fix before order** | The router cannot place a via. Rev C's DRV block is surface-mount. The plan does not say how the block gets routed | Choose the method before any rev C copper: KiCad's interactive router for DRV rev C |
| R3 | rev B, DISP | Should fix | Net BL_K (10 pads) has no track. Only the pour joins it, and the pour is not stored filled. It holds today (KiCad: 0 unconnected). One pad drops off when the HV clearance is raised to 1.25 | Add a track spine through the ten pads |
| R4 | rev B, both | Should fix | DRC-clean means "clean at 0.6 mm under solder mask". Against 1.25 mm (bare copper) 161 + 55 places fail. No creepage rule runs | Write the basis down. Add a creepage rule and a planted-error test for it |
| R5 | rev B, DRV | Should fix | Width is not a rule. The PWR class says 0.5 mm; +5V is drawn at 0.4 (524 mm) and 0.3 (37 mm). XA0-7 and BL_A are 0.2 against a class width of 0.25 | One width table. A `track_width` rule per class |
| R6 | rev B, DRV | Should fix | Ground is a routed tree. From decoder U2 pin 12 to the reservoir C7 the track path is 341 mm for 96 mm straight. The anode loops are 24 to 39 cm2 on tracks alone. The back pour is in 10 pieces | Rev C: pour first, treat the pour as the return, and check it |
| R7 | method | Should fix | Any part move throws away all router copper (49 % of DRV). A person cannot move one track in KiCad: the generator overwrites it | Make the board file the source for routed copper |
| R8 | method | Should fix | Quality is printed, never gated. Nothing checks corners, loops, ground paths or HV next to signal | Thresholds per board with an exit code |
| R9 | method | Should fix | HV class membership is a list of name patterns. Nothing checks that every net that can sit at 185 V is on it | A check that walks the netlist out from HV185 and SW |
| R10 | rev B, DRV | Note | 13 acute corners, worst 17.7 degrees on FB (the boost feedback) at (111.0, 22.0). 4 % of DRV's copper is off the 0/45/90 directions. DISP has none | A clean-up pass, or route by hand |
| R11 | rev B, both | Note | 123 (DRV) and 83 (DISP) places sit within 10 % of the required clearance. None is below it | None. The margin is by design, not spare |
| R12 | rev B, DRV | Note | The boost is routed well: hot loop 80 mm2, switch node 15.9 mm, 2.8 mm of HV beside signal on the whole board | Keep. Make it a rule so rev C keeps it |
| R13 | rev C | Note | 11 nets and 368 mm of track cross the planned block today, one of them HV185 (22 mm). The plan's count of 11 holds | Move HV185 out of the block first |
| R14 | history | Note | The routing study and `routing-baseline/` are about the retired TS06-MAIN, not the pair. Their two actions are closed | Say so at the top of the study |

Evidence classes, sources and commands are in the detail below.

## How it was measured

My scripts are in the scratchpad folder `audit/routing/`: `pcbscan.py`, `scan2.py` (clearances, connectivity, corners, HV
runs), `scan3.py`, `loops.py`, `hvwalk.py`, `run_drc.sh` with `rules/`. Real tools: `tools/audit.py`; `bash
tools/verify_pair.sh` (here, with numpy and Docker: **27 PASS, 0 FAIL, 0 SKIP**); KiCad 10.0.8 `kicad-cli pcb drc
--refill-zones --severity-all` on copies of the boards. Every number below is *measured* with these unless it says otherwise.

## 1. The method

**How the tracks came to be.**
* **DISP: typed by hand, all of it.** `tools/mkpcb_disp.py:12`: "Nothing on this board is placed by a packer or routed by a
  router. Every coordinate below is chosen." 388 segments, 2125 mm. The reasons are written beside the numbers.
* **DRV: half typed, half routed.** 373 segments (3393 mm, 51 % of the length) are typed in `tools/mkpcb_drv.py`: the decoder
  fans, the XA and LED buses. 791 segments (3296 mm, 65 nets) come from `tools/netroute.py`, a negotiated router written for
  this project, with its inner search in `tools/astar.c` (C, built on first use; a slow Python copy runs if there is no
  compiler). It works one face at a time on a 0.1 mm grid, with 45 degree steps.
* **No vias, by construction.** `netroute.py:2`: "A router that never places a via". A net changes face only at its own
  through-hole pads. My scan and KiCad both find 0.
* **The saved route is the truth.** The router's result is `tools/mkpcb_drv_routes.json` (11,866 lines). A plain run of the
  generator loads it and writes the board.
* **The study and the baseline** (`Claude outputs/TS06-routing-study.md`, `routing-baseline/`) are about the retired
  one-board TS06-MAIN, routed by the older `tools/pcbroute.py` with 476 vias (R14). The pair's own comparison is the
  two-layout table in `Claude outputs/TS06-pair-review.md:455-482`.

**Can it be repeated?** From the saved file: yes. `verify_pair.sh` regenerates both boards and compares byte for byte (its
`generator` check; passed here). From nothing (`--route`): claimed, not re-checked. `grill.md:246` records one fresh route
that matched byte for byte on 30.09.26, with the hash seed pinned. No check repeats that, and the C search is not compared
with its Python copy. A fresh route on another machine is *assumed* equal.

**Can a person review it?** Only the picture. KiCad is a viewer here: an edit made there is overwritten by the next run, and
the `generator` check fails if the file differs. A change to routed copper is a diff of JSON coordinates. The typed half is
better: each line has a reason beside it.

**What a change costs.** `mkpcb_drv.py:860-865`: the route "is thrown away and re-found whenever the placement changes". So
moving one part voids every earlier look at the routed half (R7). There is no "move this one track".

**Errors it can make that nothing catches.**
1. A rule that is written too narrowly (R1). All three checkers copy the same rule, so all three pass.
2. A net that should be in the HV class but is not on the pattern list (R9). I walked one part out from every HV net
   (`hvwalk.py`): 22 nets on DRV and 48 on DISP come up, all expected (cathodes, opto LED sides, GND, FB, strip neighbours).
   So membership is right in rev B (*inferred*). Rev C adds nets; nothing would flag a miss.
3. Legal but poor copper (R8). The study's own lesson, "every test asked whether the copper was legal and none asked whether it
   was any good", still holds: `audit.py` prints QUALITY and "sets no exit code".
4. A width below the class width (R5). The router takes widths from a dict (`mkpcb_drv.py:869`), not from the class.
5. A net held together only by a pour that is filled later (R3).

**Which rules does the DRC really run with?** (`PCB/TS06-DRV/TS06-DRV.kicad_pro:5-18`, `TS06-DRV.kicad_dru`; DISP is the same
shape.) A clean DRC proves these and no more:
* Board minimums: clearance 0.2, track 0.2, copper to edge 0.5, hole clearance 0.25, thermal spokes 2.
* Class clearances: Default 0.2, CATH 0.25, PWR 0.25, HV 0.6. Class widths are defaults, not limits.
* One custom rule: an **HV pad** keeps 0.8 mm from other nets. Keep-out areas round the standoff holes.
* Not there: creepage, HV to edge, width by class, a rule for the switch node, a rule for bare low-voltage pads near HV.

## 2. The results

| | DRV | DISP |
|---|---|---|
| Nets, pads | 136, 427 | 59, 179 |
| Track segments | 1164 | 388 |
| Track length | 6689 mm (front 2804, back 3885) | 2125 mm (front 373, back 1751) |
| Vias; copper layers used | 0; 2 of 2 | 0; 2 of 2 |
| Length against the shortest tree (`audit.py`) | 1.30x (floor 4536 mm) | 1.15x (floor 1851 mm) |
| Directions 0/90, 45, other | 83 %, 13 %, 4 % | 53 %, 20 %, 27 % |
| Widths in use (mm) | 0.2, 0.25, 0.3, 0.4, 0.5, 0.8 | 0.25, 0.3 |
| Pours, as KiCad fills them (`verify_pair.sh`) | GND front: 15 pieces, the largest 92 %. GND back: 10 pieces, the largest 33 % | BL_K front: 1 piece |
| Copper pairs of different nets within 1 mm | 1461 | 585 |
| ... below the required clearance | 0 | 0 |
| ... within 10 % of it | 123 (8.4 %), in 56 net pairs | 83 (14.2 %), in 52 net pairs |
| Smallest gap | 0.203 (XA0 track to a GND pad, back, at 11.30, 95.00) | 0.250 (the KS bundles) |
| Smallest gap, HV to another net | 0.65 (see R1) | 0.70 (COLON_U to COLON_L, both HV) |
| Track ends that touch nothing | 0 | 0 |
| Nets not joined by tracks alone | 0 | 1 (BL_K) |
| Corners under 89 degrees | 13 | 0 |
| Width changes along a net | 2 (+5V and GND, 0.4 to 0.3, at the Nano) | 0 |
| HV beside non-HV, parallel, gap up to 1.2 mm | 2.8 mm in all (HV185 beside A7: 1.5 mm) | 0 |

**Widths on DRV by class (R5).** HV: 0.4 (462 mm), 0.8 (16 mm, the switch node). PWR: 0.8 (116 mm: +12V and the input), 0.5
(39 mm: the gate), 0.4 (524 mm: +5V), 0.3 (37 mm: +5V). Default: 0.25 (2883 mm), 0.2 (1422 mm: XA0-7, BL_A), 0.4 and 0.3 (GND,
772 mm). With a width-per-class rule added, KiCad fails 199 segments on DRV (91 PWR, 108 Default) and none on DISP.

**The clearance spread (R11).** On DRV 77 of the 123 tight places need 0.2 and have 0.20 to 0.22 (the smallest are in the XA
bus, typed with 0.21 mm gaps); 45 are HV pads at 0.80 to 0.88. On DISP 45 are cathode lines at 0.25 to 0.275 and 38 are HV
pads. The tight places are chosen pitches, not accidents, and all are above the fab's 0.15 mm (`tools/dfm_check.py:57-58`).
The soft "cathode pad 0.5 mm" rule is met everywhere (my scan and KiCad): it can become a hard rule at no cost.

**Loops, along the real copper (`loops.py`).**

| Loop | Area | Note |
|---|---|---|
| Boost hot loop: IRF840 drain, diode, 4.7 uF reservoir, back to source | 80 mm2 (13 x 8 mm) | Good for through-hole parts (R12) |
| Gate: driver, gate resistor, gate, source back to driver | 17 mm2 | Ground leg 24.7 mm for 20.8 straight |
| Anode and cathode: tubes H10, M1, S1 | 2829, 3868, 2443 mm2 | Both boards, ground on tracks only |

The anode loops are large because ground is a tree (R6). U2 pin 12 to C7 minus is 340.6 mm of track for 96.1 mm straight
(3.5x); four other ground paths were 1.1x to 1.2x. `mkpcb_drv.py:985` says the pours "carry no connection of their own". In
the built board they will carry most of the return, and the back pour is in 10 pieces, the largest a third of it. That path
is not designed and not checked. It is a noise risk for the A6 and A7 ladders, not a function risk (*inferred*).

**KiCad's DRC, on copies, with stricter rules.**

| Rules | DISP | DRV |
|---|---|---|
| The project's own | 0 clearance, 0 unconnected. 2 courtyard overlaps (V3 with V7 and V8), accepted by the repo | 0 clearance, 0 unconnected. 2 silk-at-edge warnings (U1), accepted |
| 0.8 mm for any HV copper, not only HV pads | 3: COLON_U to COLON_L tracks, 0.70 (both HV; harmless) | 2: the R1 places. 1 starved thermal appears (C6 pin 2) |
| 1.25 mm for any HV copper | 55, and BL_K pad HL3.1 comes off its pour | 161, and 3 starved thermals |
| Creepage 1.25 mm, HV to non-HV | 35: mostly strip pins, where an anode pin sits beside an LED pin at 0.84 | did not finish in 7.5 minutes |
| Width per class, cathode pad 0.5 hard, HV to edge 1.0 | 0 | 199 width, 0 others (HV to the outline: 1.70 mm at least, my scan) |

**R1 in detail.** The rule text is `A.Type == 'Pad' && A.hasNetclass('HV')`. It fires when the pad is HV. It does not fire when
the pad is low-voltage and the track is HV. A solder joint is bare metal either way, and the voltage across the gap is the
same. The two places: strip XS23 pin 4 (BL_A4) to the ANODE_M10 track, 0.65 mm, front, at (114.5, 67.3); resistor R44 pin 2
(GND) to an HV185 track, 0.70 mm, back, at (70.63, 50.8). The project's own basis is 0.8 mm for a bare joint at 171 to 250 V
(`mkpcb_drv.py:84`; the standard's table value is *assumed, not re-checked*). The repo's "HV rule live" test plants a track
beside an HV pad, so it cannot see this case.

**R4 in detail.** HV tracks keep 0.6 mm to other nets and rely on solder mask as insulation. That is a fair basis (the coated
value in the same table is 0.4 mm, *assumed*), but it is not written down, and no rule measures the path along the surface.

## 3. Against a normal flow

*Inferred* from the measurements above: no autorouter and no interactive session was run.

**Where the scripted result is better.**
* Zero vias on 195 nets. An autorouter would not try.
* It regenerates byte for byte, and one constant moves a whole group (`SB` and `SC`, `mkpcb_drv.py:72-76`). The mate between
  the two boards is computed, not eyeballed.
* The typed bundles are regular: ten parallel cathode strands at exactly 0.25 mm, 1.15x the floor, no acute corner.

**Where it is worse.**
* The rules live in four places (`CLASSES`, `pad_rules`, the `WIDTHS` dict, the project files). A normal project has one
  rules file, and the router obeys it while you draw.
* No single-track edit: every change is a full re-route or a hand edit of numbers.
* 13 acute corners and 4 % off-angle copper. An interactive router makes none.
* Ground is a 0.4 mm tree. A person pours ground first and routes on top of it.
* About 3,900 lines of home-made code (`netroute.py`, `pcbkit.py`, `astar.c`, the two generators) must be right. KiCad's
  router is used by many people; this one by one project.

## 4. Fit for rev C

**What rev C asks** (`PCB/TS06-routing-plan.md` 4.2, 4.3): on DRV, two 16-channel PWM chips, 20 P-FETs in dual packages and
14 line resistors in a block at x 86.5 to 128.5, y 24.5 to 45.0 (861 mm2); a 7-way connector; up to 872 mA on 5 V. On DISP,
about ten track changes.

**Can this method deliver it?**
* **DISP rev C: yes.** A handful of typed tracks. Keep the generator.
* **DRV rev C: not as it stands (R2).** The chips and FETs are surface-mount: their pads are on one face. The router changes
  face only at through-hole pads of the same net. A net that joins only surface-mount pads (a PWM output to a gate, the common
  source rail) can then never cross another one. The repo's other router, `pcbroute.py`, has vias, and its own study records why
  its results were poor. So rev C needs new router code, or one-pin holes used as vias, or another method.
* The block is not empty today: 11 nets and 368 mm of track cross it (front 157, back 211), no pads. HV185 is one of them
  (22 mm). The plan's "re-route the 11 nets" holds (R13).
* 872 mA on a 0.4 mm track: about 1.2 mOhm per mm, so about 0.1 V lost over the 95 mm from the regulator to the block, and the
  same again in ground (*inferred*: a straight-line estimate, 35 um copper). The PWM switches that drop onto the ladders'
  ground.

**The method I would use.**
1. DISP rev C: the typed generator, as today.
2. DRV rev C: generate once (placement, the typed copper, the netlist), lock those items, then route the block and the re-routes
   in KiCad's interactive router with a rules file. From then on the board file is the source of truth for routed copper. The
   scripts stay as checks. The `generator` check compares the locked items only.
3. Vias inside the block only (a rule area); none elsewhere.

**Rules on day one** (in the `.kicad_dru`, so the router obeys them while drawing).
* HV class: 0.6 mm track to track under mask; **0.8 mm between any HV copper and any pad of another net, and between any HV pad
  and any copper**; a creepage rule for bare HV joints; HV to board edge 1.0 mm (today's smallest: 1.70 mm).
* The switch node in its own class: 2 mm from FB, VREF, A6, A7, SDA, SCL; length limit 20 mm (15.9 today).
* CATH: 0.25 mm, pads 0.5 mm, hard.
* PWR: `track_width` minimums. +12V and the input 0.8. Logic +5V 0.5. A new light rail and its ground return 1.0 mm or a pour,
  taken from the regulator on their own, not through the logic rail.
* Ground: pours first; every ground pad on a pour with two spokes; a track tree only as back-up.

**Checks to add.**
1. KiCad DRC with these rules in `verify_pair.sh`, and one planted error per rule to prove the rule is live (the repo already
   does this for the HV pad rule).
2. A netlist walk from every HV net, compared with the HV class (R9).
3. Thresholds with an exit code (R8): acute corners 0; pour-only nets 0; boost hot loop under 100 mm2; HV beside A6, A7, FB
   under 5 mm; ground path ratio under 2; detour under 1.35x; the largest pour piece over 80 %.
4. If any router copper stays: a fresh route compared with the saved one.
5. The voltage drop of the light rail, from the real copper.

## Reconsider

| Choice | Today | Starting today | Cost of changing | Call |
|---|---|---|---|---|
| Where routed copper lives | Python and a JSON file; the board file is an output | The KiCad board file, drawn with a rules file; scripts check it | 2 to 4 days for DRV (*assumed*); byte-exact regeneration is lost for routed copper | **change in rev C** (DRV) |
| The home-made via-less router | 49 % of DRV | Would not write one | Already paid for rev B | **keep** rev B as routed; do not extend it |
| Typed copper on DISP | All 388 segments | The same | None | **keep** |
| Zero vias | A hard rule on both boards | A goal on through-hole nets; vias allowed in a surface-mount block | Small | **keep** on DISP; **change in rev C** inside the DRV block |
| Ground | A routed tree, pours as filler | Pours as the return, checked | A ground re-route | **change in rev C** |
| The HV rule | 0.6 class, 0.8 for HV pads only | 0.8 for any bare joint against HV, plus creepage | Minutes, and two tracks | **change before the rev B order** |
| Widths and quality numbers | A dict in the generator; printed, not gated | Class widths as DRC rules; thresholds with an exit code | Half a day (*assumed*) | **change in rev C** |
| The 0.1 mm grid and its corners | 13 acute corners | The same, with a clean-up pass | Small | **change later** |

## Not checked

* A fresh `--route` of DRV against the saved route (too long for this run). The claim rests on `grill.md:246`.
* KiCad's creepage DRC on DRV: it did not finish in 7.5 minutes. A 2.0 mm creepage run was not started.
* The pours' real return paths: the board files hold unfilled pours, so I measured track paths only.
* Fascia R rev B: outside this run's two boards. The spacing standard's table values: from the project's comment and memory.
* Width against current, hole and edge distances, creepage place by place, the strip pin map (anode pins beside LED pins,
  0.84 mm between pads): left to audit-layout.

**Earlier reviews.** `grill.md` G9 (a repeatable route) is closed by its note of 30.09.26 but still marked "in progress". The
routing study's two actions (move the Nano and the decoder; split the board) are closed by the pair.
