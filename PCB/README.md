# TERMINAL-06 — custom PCBs

Two boards go to Rezonit for this run. A third is deliberately deferred.

| Board | Size | Stack | Status |
|---|---|---|---|
| **TS06-FASCIA** | 176 × 52 mm | 2.0 mm FR4, black mask, white silk | In progress — the control panel AND the printed product face. One board, not two. |
| **TS06-SEC** | 46 × 34 mm | 1.6 mm, matte black | Blocked on P4 bench numbers. |
| ~~TS06-TUBE~~ | — | — | **Deferred 08.09.26.** See below. |

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
