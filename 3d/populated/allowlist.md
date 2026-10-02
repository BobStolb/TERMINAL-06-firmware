# The 28 footprints drawn without a model, on purpose

For the owner. `python3 tools/model_coverage.py` fails on any footprint that ends with no 3D model unless it is on a short
allowlist (the `none` lists of `tools/models3d.json`, one reason each). Today the allowlist holds **28 footprints** of the 164
on the three boards; the other 136 resolve to a model that exists. This page lists the 28.

Two reasons are in use:

* **Bare hole**: a mounting hole is no part of the board; the screw, standoff or washer in it is case hardware.
* **DNP**: the board marks the footprint `dnp` and `PCB/TS06-DRV/bom.md` lists it under "Not fitted", so the bench builds it empty
  and the render leaves it empty.

The third reason in the brief, a header drawn without its mate, is **not used by any entry**: no header is on the list. Every header
and strip on the three boards has a model (the DRV strips and J1 are drawn with their pin tails through the pads; J1's mating PHR-6
plug is not drawn, which the fit table notes, but J1 itself is drawn).

| # | Board | Ref | What it is | Why it has no model |
|---|---|---|---|---|
| 1 | TS06-DISP | H1 | M3 standoff hole, 3.2 mm, at (3.5, 40.5), shared with TS06-DRV | bare hole |
| 2 | TS06-DISP | H2 | M3 standoff hole, at (187.9, 40.5) | bare hole |
| 3 | TS06-DISP | H3 | M3 standoff hole, at (50.535, 3.3) | bare hole |
| 4 | TS06-DISP | H4 | M3 standoff hole, at (187.9, 7.5) | bare hole |
| 5 | TS06-DRV | H1 | M3 standoff hole, 3.2 mm, at (187.9, 66.5), behind TS06-DISP's H1 | bare hole |
| 6 | TS06-DRV | H2 | M3 standoff hole, at (3.5, 66.5), behind TS06-DISP's H2 | bare hole |
| 7 | TS06-DRV | H3 | M3 standoff hole, at (140.865, 29.3), behind TS06-DISP's H3 | bare hole |
| 8 | TS06-DRV | H4 | M3 standoff hole, at (3.5, 33.5), behind TS06-DISP's H4 | bare hole |
| 9 | TS06-DRV | H5 | M3 case-screw hole, at (3.5, 96.5), screw and nylon washer into the cheek | bare hole |
| 10 | TS06-DRV | H6 | M3 case-screw hole, at (187.9, 96.5) | bare hole |
| 11 | TS06-DRV | H7 | M3 case-screw hole, at (3.5, 3.5) | bare hole |
| 12 | TS06-DRV | H8 | M3 case-screw hole, at (187.9, 22.5) | bare hole |
| 13 | TS06-DRV | R33 | 510k bleeder resistor, 0.25 W, vertical; lower-right group R33-R36 | DNP, not fitted per `bom.md` |
| 14 | TS06-DRV | R34 | 510k bleeder, same group | DNP, not fitted per `bom.md` |
| 15 | TS06-DRV | R35 | 510k bleeder, same group | DNP, not fitted per `bom.md` |
| 16 | TS06-DRV | R36 | 510k bleeder, same group | DNP, not fitted per `bom.md` |
| 17 | TS06-DRV | R37 | 510k bleeder, centre group R37-R40 (beside the RTC module) | DNP, not fitted per `bom.md` |
| 18 | TS06-DRV | R38 | 510k bleeder, same group | DNP, not fitted per `bom.md` |
| 19 | TS06-DRV | R39 | 510k bleeder, same group | DNP, not fitted per `bom.md` |
| 20 | TS06-DRV | R40 | 510k bleeder, same group (behind the RTC module in the iso picture) | DNP, not fitted per `bom.md` |
| 21 | TS06-DRV | R41 | 510k bleeder, left group R41-R44 (by the ANODES legend) | DNP, not fitted per `bom.md` |
| 22 | TS06-DRV | R42 | 510k bleeder, same group | DNP, not fitted per `bom.md` |
| 23 | TS06-DRV | R43 | 510k bleeder, same group | DNP, not fitted per `bom.md` |
| 24 | TS06-DRV | R44 | 510k bleeder, same group | DNP, not fitted per `bom.md` |
| 25 | Fascia R | H1 | M2.5 corner-screw hole, 2.7 mm, at (4.5, 4.5) | bare hole |
| 26 | Fascia R | H2 | M2.5 corner-screw hole, at (186.9, 4.5) | bare hole |
| 27 | Fascia R | H3 | M2.5 corner-screw hole, at (4.5, 35.5) | bare hole |
| 28 | Fascia R | H4 | M2.5 corner-screw hole, at (186.9, 35.5) | bare hole |

4 + 20 + 4 = 28 rows: 16 bare holes (4 on DISP, 8 on DRV, 4 on the fascia) and 12 DNP resistors. The reasons are the ones printed by
`python3 tools/model_coverage.py -v`.

## The empty pads in `TS06-DRV-iso.png`, checked against the list

Every pad that looks empty in the picture, and what it is:

| Empty pads in the picture | Footprints | On the list? |
|---|---|---|
| R33-R36 (lower right, labelled) | TS06-DRV R33, R34, R35, R36 | yes, rows 13-16 |
| R37-R39 (beside the RTC module, labelled) | R37, R38, R39 | yes, rows 17-19 (R40 is the fourth of the group, hidden behind the module, row 20) |
| R41-R44 (left of centre, labelled) | R41, R42, R43, R44 | yes, rows 21-24 |
| the row of pads under the "FASCIA" legend, near the bottom edge | **J1**, the JST PH 6-pin header on the back of the board | **not on the list, and not empty**: 6 pads, not 7, each with the pin of J1's model standing through it (zoom the picture). J1 has a model |
| the row on the right edge | **XS11**, the 1x10 socket strip on the back of the board | **not on the list, and not empty**: 10 pads (the first square), not 16, each with a strip pin through it. XS11 has a model |

So **no empty pad is missing from the list, and no model is missing.** The two rows the brief named by sight (a 7-pad FASCIA row and a
1x16 row) are the 6-pin J1 and the 10-pin XS11; their pins stand up through the pads because the bodies are on the back face.
The pad counts differ from the brief's (7 and 16). The DRV has no footprint with 7 pads at all (the 7-pad row in the repo is the rotary's
landing row on the fascia's back, not on this board), and its 16-pad footprints are the DIP-16 sockets U2, U15-U17 and RN1, drawn with
bodies, not a row on the right edge.

This was also checked without the picture: `python3 tools/model_pad_coverage.py` (new; it is `model_coverage.py`'s second half, which
asks whether the model sits on the pads, not just whether its file exists) puts each footprint's drilled pads against the plan outline of
its own part in the populated GLB. TS06-DRV: 435 drilled pads, and the only footprints with a pad outside their model are the 20
allowlisted ones (8 holes, 12 resistors). TS06-DISP: 189 pads, only its 4 holes. Fascia R: 9 pads, only its 4 holes. Exit 0 on all
three; it exits 1 for any other footprint.
