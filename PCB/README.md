# TERMINAL-06 — custom PCBs

Two boards go to Rezonit for this run. A third is deliberately deferred.

| Board | Size | Stack | Status |
|---|---|---|---|
| **TS06-FASCIA** | 176 × 40 mm | 2.0 mm FR4, black mask, white silk, ENIG | Routed. The control panel AND the printed product face. One board, not two. Surface-mount build: no solder visible from the front. Height compressed from the original 52mm 2026-09 - see below. |
| **TS06-FASCIA-THT** | 176 × 52 mm | same stack, ENIG | Second build of the same board, routed. Through-hole, with the A6 divider ON the face. Pick one to fabricate; they are alternatives, not a pair. Not yet height-compressed (the SMD build was chosen for fabrication). |
| **TS06-SEC** | 67 × 55 mm | 1.6 mm, matte black | Surface-mount build routed; every checker and KiCad's own DRC clean. Seconds (2× ИН-17) and AM/PM (2× ИН-15) on one board, the colon board plugs into it. Through-hole build not yet drawn — see below. |
| ~~TS06-TUBE~~ | — | — | **Deferred 08.09.26.** See below. |

## The two builds of the fascia

Same outline, same artwork, same netlist, same connector. They differ in one decision:
where the solder is.

* **TS06-FASCIA** — every pad is surface-mount on the back face. The customer sees black
  mask, white silkscreen and the decorative gold, and no joint anywhere. Routed with 64
  signal tracks, all on B.Cu, and **zero vias anywhere on the board** — F.Cu carries only
  the decorative gold, so no signal net can ever collide with it. GND is a pour over the
  back face, same as THT, and reaches all 7 GND pads on its own: R6 (the A7 pull-up) used
  to sit directly in the corridor the other five nets needed to reach J1, walling three
  GND pads (SW4.1, R8.2, R7.2) off from the plane with no B.Cu path a router could find at
  any trace width. Moving R6 out of that corridor — no other placement changed — opened it
  up enough that the pour alone closes the gap, confirmed by checking every GND pad against
  KiCad's own computed `filled_polygon`, not just this repo's simulated one. No stitch
  traces, no vias, nothing extra: placement fixed what routing couldn't.
* **TS06-FASCIA-THT** — the A6 resistor ladder is on the FRONT: five axial resistors above
  the rotary's seven landing holes, and the copper between them is bare, so the divider
  reads as a circuit rather than as decoration. Every other part is behind the panel with
  its front mask closed, so those holes show no gold ring. Routed with 34 tracks and no
  vias: the ladder on F.Cu under opened mask, six signals on B.Cu under mask, and GND as a
  pour over the whole back face.

`preview.svg` (`preview.png` too, where regenerated) in each board's folder is generated
by `tools/render.py` from the board file itself — front face and back face — so the board
can be looked at without opening KiCad.

**TS06-FASCIA height compression (2026-09).** The board felt oversized next to the tube
row, so it was cut from 52mm to 40mm tall. This was a pure translation, not a re-route:
every footprint, all 64 tracks, the GND pour and the silkscreen legend were shifted up by
a fixed 12mm (the dead margin above the control row - SR25's 12.5mm lever-throw keepout
was the real floor, not the visible knob bezel), then the board outline itself was
redrawn 12mm shorter. Nothing about the routing was redesigned, so R6's placement (still
load-bearing for the GND pour closing without vias, see above) is untouched. The two
mounting holes nearest the top edge are the one exception: they're anchored to the board
edge, not the control row, so they were NOT shifted, keeping their original 4.5mm inset
from the (new) top edge. All five checker tools pass clean and match the pre-compression
board's output exactly (same 2 pour islands, same 86% coverage, same 12-net agreement
with the schematic). One thing the pure translation did NOT fix on its own: the MODE
dial's decorative arc (position labels 1-6, their tick marks, and the "MODE" title)
was drawn for the old 26mm-radius-from-center clearance and clipped the new 14mm
budget - the checker tools don't validate silkscreen against the board edge, only
copper, so this needed its own pass. Fixed by rescaling the whole arc/tick/number
system by 0.789 (position 1, the tallest point, now sits at 12.5mm above center
instead of 15.84mm) and moving the "MODE" title from directly above the shaft to
its left, clear of position 1's tick - it was the single tallest element (19mm)
and didn't belong to the numbered fan, so it got its own placement rather than
being scaled with the rest. `checkpcb.py`'s rotary-keepout check had the rotary's position
hardcoded as a literal (30.0, 26.0) from the old layout - fixed to read the rotary
footprint's real position instead, since a checker that only works for one specific
layout isn't a checker. TS06-FASCIA-THT was not touched - the SMD build was the one
chosen for fabrication.

**J1 pin order is fixed for both builds: 1 +5V, 2 GND, 3 A6, 4 A7, 5 D7, 6 D8.** It used
to be whatever the surface-mount routing preferred (D8, D7, GND, A7, +5V, A6). The
through-hole board cannot route to that order, and two builds of one product must not
need two different cables, so the pin order stopped being a layout convenience and became
a specification. The legend is printed on the back silkscreen of both boards.

## TS06-SEC — seconds and AM/PM

Generated by `tools/mkpcb_sec.py`: placement, then routing by `tools/pcbroute.py`. A full
run takes about five minutes. The generator's docstring carries the reasoning in full; in
short:

* **67 × 55 mm, not the spec's 46 × 34.** The tube centres are not a layout choice — they
  come from the reviewed 8-tube assembly (`3d/Clock.FCStd`). The four tubes span 66 mm and
  their glass covers most of the front, so everything but the tubes, the three LEDs and the
  connectors mounts on the back. The ИН-17 at V5 overhangs the left edge by 1.37 mm (its
  glass, standing on its leads, not the board); `checkpcb.py` reports that courtyard, and it
  is accepted.
* **What it carries:** 2× ИН-17 and their TLP627 anode drivers; 2× ИН-15 (V9 ИН-15Б for AM,
  V10 ИН-15А for PM) with 18 cathode channels — two MCP23017s and eighteen MMBTA42s, one per
  real cathode; the colon switch (the colon board arrives on XS4); two amber backlight LEDs
  for the ИН-17s and the "m" LED HL3. XS1 is 185 V in, XS2 the ИН-17 cathode bus (IDC 2×5),
  XS3 the logic connector.
* **High voltage is its own clearance class:** 0.6 mm around the 185 V feed, the tube
  anodes, the TLP627 emitters, the bleed mid-points, every ИН-15 cathode and the colon
  return. The ИН-17 cathode bus is not in it: the К155ИД1 outputs clamp near 60 V, and the
  tube's own pins sit 0.9 mm apart.
* **79 vias — the first board in the family with any.** Four tube pin fields, ~90 nets and
  every part on one face of 67 × 55 mm do not route on two layers without them. The router
  charges each via as much as 15 mm of track, so each one is a detour it could not find.
* **Routing.** The high-voltage locals are laid first. Everything else — the ИН-17 bus, the
  185 V feed, the 5 V signals, +5V and GND — is negotiated at once in the manner of
  PathFinder, because laid one net at a time they walled each other in: the 185 V feed cut
  the back face in two, and the bus, laid early, boxed in the backlight LEDs.
* **GND is a routed tree and a pour on each face.** The pours alone left GND pads in
  pockets that signal tracks had closed on both faces — `audit.py` and KiCad's refilled DRC
  both said so — so GND is routed from XS3 like any other net, and the pours fill whatever
  the tracks leave. Surface-mount pads join the pours solid, through-hole pads by spokes;
  HL3's GND pin joins solid too, because tracks leave no room there for two spokes.
* **Checked:** `checkcopper.py --hv "HV185,CAT_*,ANODE_*,EMIT_*,BLEED_*,COLON_RET"` clean,
  `audit.py` clean (both pours), KiCad 10 DRC with zones refilled clean at every severity;
  `checkpcb.py` reports only the V5 overhang above. There is no SEC schematic yet, so
  `checksch.py` and `checkmatch.py` do not apply.
* **Footprints corrected on the way:** `TS06_IN12_Socket` and `TS06_IN17_Socket` were
  mirrored in Y; the ИН-12 socket's description carried raw quotes that stopped the whole
  `TS06.pretty` library loading; the ИН-17 pip hole is gone — the ТУ's 8 mm soldering rule
  holds the glass at least 6.4 mm off the board — and its silkscreen outlines were redrawn
  clear of the pads.
* **Still open:** the through-hole build (tube board plus a stacked driver board); a bench
  check of the ИН-15 pinouts (taken from tec.org.ru and rudatasheet.ru, which agree) and of
  the ИН-17 pip's projection, which must be under 6.4 mm; HL3's position is provisional; and
  the fascia was drawn around the old SEC outline, to be revisited.

## Checking

Nothing here is checked by KiCad until it is opened in KiCad, so five tools check it
first. Run all of them after any change to `tools/mk*.py`:

    python3 tools/checkpcb.py   <board>.kicad_pcb    # placement, keepouts, front copper vs pads
    python3 tools/checkcopper.py <board>.kicad_pcb   # clearance and per-pad connectivity
    python3 tools/audit.py      <board>.kicad_pcb    # per-net connectivity, pour fill, silkscreen
    python3 tools/checksch.py   <board>.kicad_sch    # dangling pins and the net list
    python3 tools/checkmatch.py <board>.kicad_sch <board>.kicad_pcb   # the two files agree

`checkcopper.py --hv NETS` (a trailing `*` matches every net with that prefix) holds 0.6 mm wherever a listed net is on
either side of a gap, and keeps copper 0.25 mm from unplated holes. `audit.py` checks a
poured net as one net across both faces — pour islands, pads, tracks and vias together — so
a back-face pad that reaches a front pour through a via is checked rather than skipped; a
round pad is cut out of the pour as a circle, not its bounding square; and two vias of a net
count as joined only where their copper touches. `checkpcb.py` reads each courtyard graphic
as a whole block and compares courtyards only between parts on the same face.

`checkmatch.py` is the one that matters most and was written last: every other tool can
pass while the schematic and the board disagree about what they are connecting.

All five tools, plus `render.py`, read `.kicad_pcb` files two different ways depending on
who last saved them: this repo's own `tools/mk*.py` generators outdent each `(footprint
...)` block to column 0 and always number net references, while the real KiCad 10 install
this board gets edited in indents footprints normally *and* writes every net reference —
pads, tracks, vias, the zone itself — as a bare name with no code at all, no matter how
many times the file gets saved. Every tool here parses both forms; nothing needs
reformatting by hand before a check runs, and nothing should ever again. If a check comes
back suspiciously empty (`0 footprints`, `no tracks or vias`) after a real KiCad save, that
means a *new* variant slipped through, not that the board is broken — fix the parser, not
the file.

`IN-12_norm/` is the inherited AlexGyver/itworkclub board's fab data, kept as reference.
`lib/` holds project-local symbols and footprints — nothing here relies on a stock KiCad
library, because none of the Soviet panel hardware has one.

## Why TS06-TUBE is deferred

Three reasons were ever offered for fabricating a custom ИН-12 tube board. Only one is
still alive, and it is not an electrical one:

1. **Four anode bleed resistors need a home.** **Withdrawn 06.09.26** — the ghosting root
   cause turned out to be empty multiplex slots (spec §5a-pre), not the anode drivers.
   Dead reason.
2. **The socket pin pattern.** **Not a reason.** The footprint is fully known from the
   inherited board's Gerbers — see `../TERMINAL-06-measurements-PCB-IN12BOARD.md`. The
   tube defines the pattern, so any socket that fits the tube fits those holes.
3. **Deck geometry — the only live reason.** Tube pitch (23.36 / 27.42 / 23.36 mm), deck
   height, forward offset and rake are all fixed by someone else's layout. Spec §6's
   "Brow reveal" note is the argument: the brow was sized to clear the 18.63 mm digit, but
   the envelope is 28.70 mm, so ~10 mm of glass sits behind the top deck.

**Against it:** ten main boards are already owned, therefore ten tube halves are already
owned. TS06-TUBE is ~1 425 ₽/unit of Group D that does not have to be spent.

**Decision rule: print a brow, test-fit it against a real tube, and see whether the case
alone gives the reveal.** Do not order copper to fix a plastic problem. Revisit only if
the test-fit fails.

## TS06-MAIN — one board for the whole clock (in progress, 17.09.26)

The three-board electrical stack (inherited AlexGyver board + TS06-SEC + TS06-COLON) is
being replaced by **one board carrying every tube, every driver, the Nano, the RTC and the
185 V converter**, in two builds like the fascia: **TS06-MAIN** (surface-mount wherever a
part exists in that form) and **TS06-MAIN-THT**. The brief is
`../Claude outputs/TS06-MAIN-handoff.md`; SEC and COLON are superseded by it and stay in
the repo as the worked examples they are.

**Decisions taken by the owner on 17.09.26**, answering the brief's open questions:

| Question | Decision |
|---|---|
| Power input | **12 V on the same 5.5 × 2.1 mm barrel jack the stock board uses, not 5 V**: the stock converter is an energy-limited stage good for ≈1 W and the full clock needs ≈3.5 W (see `../TERMINAL-06-measurements-PCB-GYVER-NETLIST.md`). A switching 5 V regulator (R-78E05 class) feeds the logic. The Nano's USB stays reachable through a case opening, at the bottom edge as on the stock board, for reflashing and for a PC time-set link; USB alone runs the logic with the tubes dark. |
| MCU | Arduino Nano on headers in **both** builds. |
| RTC | Bare DS3231SN with a CR2032 holder in the SMD build; the owner's **DS3231 mini module** (pins − NC C D +, the same header the stock board carries) on a 5-way header in the THT build. |
| Tube positions | The reviewed coordinates, Gyver pitch included, unchanged. The board is sized for itself; the fascia is not a width constraint. |
| Anode chain | One fixed series resistor per digit tube (the stock board has a single shared 10 kΩ) plus DNP bleed footprints on all six. |
| Optos | Six TLP627 singles, one beside each tube. |
| "m" LED | HL3 on the free D12 through its resistor, so always-on versus 12-hour-only is a firmware choice. |
| Backlight | Eight amber LEDs, the ИН-15 pair included. |
| Layers | Two. Vias budgeted, not hunted. |

**Phase 0, the capture, is done from the fabrication data** rather than the bench:
`tools/tracegyver.py` traces every net of the inherited board from its Gerbers and writes
the result up in `../TERMINAL-06-measurements-PCB-GYVER-NETLIST.md`. What the bench still
has to supply is listed in `../knowledge/TERMINAL-06-measurements-TS06-MAIN-gates.txt`.
