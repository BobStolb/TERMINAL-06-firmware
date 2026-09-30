# TS06-FASCIA: four ways to sit under the tube row

The boards were widened to 191.4 mm so the seconds tubes could stand 20.5 mm apart. The fascia
was drawn for the 176 mm row. The owner asked for it centred under the tubes, and for the
alternatives, grilled. This page scores each one. The owner chooses.

Every number below was measured here, not taken from an author's report. The tools:
* `checkpcb`, `checkcopper`, `audit` and `checkmatch`;
* KiCad 10 DRC with zones refilled;
* `3d/case-pair/case_pair.py`, with `FASCIA_PCB=<board>` for the variants.

| | **A · centred** | **W · full width** | **R · on the tube grid** | **F · frame** |
|---|---|---|---|---|
| Board | `PCB/TS06-FASCIA` | `PCB/TS06-FASCIA-wide` | `PCB/TS06-FASCIA-rhythm` | case model only (`FASCIA_FRAME=1`), in progress |
| Size | 176 × 40 | 191.4 × 40 | 191.4 × 40 | a 179 × 40 panel in a printed frame |
| Where, world X | 4.3–180.3, on the middle of H10 and ИН-15А (92.3) | 0–191.4, cheek to cheek | 0–191.4, cheek to cheek | 3.0–182.0, the trench window |
| How it was made | the committed board, moved | the same 64 tracks, translated; holes to the new corners | re-placed and re-routed: 53 tracks | — |
| Controls vs the tube above (mm) | SW1 −2.3 (H1) · SW2 −9.3 (S10) · SW3 −6.8 (S1) · SW4 −0.1 (ИН-15Б) · SW5 −3.1 (ИН-15А) | +1.1 · −5.9 · −3.4 · +3.3 · +0.3 | **0 for all five**: dial under the hours pair, FIELD/SUB under M10/M1, −/+ under the ИН-15s | as A |
| Checkers | clean | clean | clean | — |
| KiCad DRC | 0 violations, 0 unconnected | 0 violations, 0 unconnected | 0 violations, 0 unconnected | — |
| Fascia boss vs R5's pad | **FAIL**, −1.2 mm (the boss lands on it) | OK, 6.5 mm | OK, 1.7 mm | the frame replaces the bosses |
| SW5 vs the top-right boss | TIGHT, 1.2 / 2.6 mm | OK, 8.4 / 7.2 mm | OK, 9.2 / 8.4 mm | frame: no boss there |
| Rotary vs the sill | TIGHT (the sill needs a notch) | TIGHT (notch) | **OK** (no notch) | as A |
| Open slots beside it, where TS06-DRV shows | 4.8 mm left, 11.6 mm right | none (0.5 mm to each cheek) | none | none |
| Lead path | 139 mm | 142 mm | 138 mm | as A |
| Area, cost | 7040 mm² | 7656 mm², +8.75 %, about +70–90 ₽ | 7656 mm², +8.75 %, about +60–90 ₽ | a printed part |
| Reach | one hand | one hand | two hands: 86 mm from FIELD to − | one hand |

All four keep the case's outside at 204.4 × 120.3 × 83.6 mm, and the fascia lead is specified
at 180–200 mm in every case.

## The approaches

**A · centred.** The smallest change. It fixes the position the owner asked for, but it leaves
three problems:
* the slots either side show the driver board;
* one boss sits on R5's pad;
* SW5 crowds its boss.

The controls miss the tubes by 0.1–9.3 mm, and misses of a few mm read as mistakes. The
product review's rule is that a control should sit exactly on a tube centre, or at least
10 mm off one.

**W · full width.** A pure translation of the routed board. Nothing is re-routed, and the holes
move to the corners, which clears both tight spots. The board, the fascia and the cheeks are
one width. The controls keep their old positions, so they are still 0.3–5.9 mm off the tubes.
`tools/fascia_variant.py --refill` rebuilds it byte for byte.

**R · on the tube grid.** A new layout on the full-width board, so every control is under a tube
centre and the panel continues the row's rhythm. Three alignments were routed; B was built.
* **Built, B:** the dial under the hours pair, the levers under the minutes, the buttons under
  the ИН-15s.
* **A:** buttons under the seconds, leaving the right 50 mm empty.
* **C:** levers under the seconds, with 80 mm of gold feed crossing the minutes.

B gives the cleanest case checks: the rotary clears the sill without a notch. It costs a
two-handed reach. `python3 tools/mkpcb_fascia_rhythm.py` rebuilds it byte for byte from its
saved route, and `composite-{0-centred,A,B,C}.png` show each alignment against the tubes.

**F · frame.** A case change rather than a board. It is a printed frame between the cheeks that
continues the trench walls, with the fascia dropped into a rabbet. It closes the slots, carries
the panel along its length instead of at four corner bosses, and removes the boss problems.
It can hold A's board as it is. It is being modelled now.

## Recommendation

**R, alignment B.** It is the only variant that answers "under the tube row" with the controls
as well as the outline:
* it passes every check, with no fascia row TIGHT or FAIL;
* its DRC is clean;
* the sill loses its notch;
* it costs the same as W.

If one-handed reach matters more than the rhythm, take **W**. Take **F** only if the fascia
should stay a small panel.

Whichever is chosen still needs two things:
* **Larger legends:** the dial's labels are about 1.5 mm, and the product review asks for at
  least 3 mm caps to be read at arm's length.
* **A dry fit** of a real КМД1 and МТ1 against the panel.
