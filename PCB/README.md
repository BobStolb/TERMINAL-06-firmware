# TERMINAL-06 — custom PCBs

Two boards go to Rezonit for this run. A third is deliberately deferred.

| Board | Size | Stack | Status |
|---|---|---|---|
| **TS06-FASCIA** | 176 × 52 mm | 2.0 mm FR4, black mask, white silk, ENIG | Routed. The control panel AND the printed product face. One board, not two. Surface-mount build: no solder visible from the front. |
| **TS06-FASCIA-THT** | 176 × 52 mm | same stack, ENIG | Second build of the same board, routed. Through-hole, with the A6 divider ON the face. Pick one to fabricate; they are alternatives, not a pair. |
| **TS06-SEC** | 46 × 34 mm | 1.6 mm, matte black | Blocked on P4 bench numbers. |
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

**J1 pin order is fixed for both builds: 1 +5V, 2 GND, 3 A6, 4 A7, 5 D7, 6 D8.** It used
to be whatever the surface-mount routing preferred (D8, D7, GND, A7, +5V, A6). The
through-hole board cannot route to that order, and two builds of one product must not
need two different cables, so the pin order stopped being a layout convenience and became
a specification. The legend is printed on the back silkscreen of both boards.

## Checking

Nothing here is checked by KiCad until it is opened in KiCad, so five tools check it
first. Run all of them after any change to `tools/mk*.py`:

    python3 tools/checkpcb.py   <board>.kicad_pcb    # placement, keepouts, front copper vs pads
    python3 tools/checkcopper.py <board>.kicad_pcb   # clearance and per-pad connectivity
    python3 tools/audit.py      <board>.kicad_pcb    # per-net connectivity, pour fill, silkscreen
    python3 tools/checksch.py   <board>.kicad_sch    # dangling pins and the net list
    python3 tools/checkmatch.py <board>.kicad_sch <board>.kicad_pcb   # the two files agree

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
