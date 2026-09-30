# Power entry for the TERMINAL-06 case: the options

The owner's verdict on the 12 V plug review (five fixes: plain cheek, inside pocket, outside
pocket with a 1.5 mm web, long-barrel plug, jack moved 4.3 mm) was **changes**:

> "I sm completely all for custom connectors, like chunky soviet ones. but you must still explore
> options like cutots, lids, or moving the port to a different place"

This folder explores those options: Soviet panel connectors, cut-outs in the cheek, lids and
panels, and moving the port. It ends with a ranked recommendation. **Nothing in the case model or on
the boards is changed.** `case_pair.py`'s default model, `params.scad`, `checks.md` and `out/`
are as committed. The one SCAD file here includes the case and overrides a few variables
locally, for the pictures only.

## Files

| File | What it is |
|---|---|
| `power_options.py` | Computes every number below from the case model and `PCB/TS06-DRV/TS06-DRV.kicad_pcb`. Writes `numbers.json` and the sheets |
| `sheets.py` | Draws the sheets (PIL), in the style of the earlier plug review sheet |
| `power_options.scad` | Includes `../case.scad` unchanged and draws the two favourites |
| `numbers.json` | All computed numbers |
| `cheek-cutouts-section.png` | Cut-outs, lids and plates in the cheek, drawn in section, plus the rule behind them |
| `move-port-rear.png` | The rear panel seen from behind: parts behind it, the depth budget, every place tried |
| `soviet-connectors.png` | 2РМ14, ШР20, ОНЦ-ВГ DIN, panel DC jack: to scale, each number marked seen or inferred |
| `drv-jack-corner.png` | TS06-DRV's jack corner from the board file: pads, tracks, free space for a header |
| `render-2rm14-rear.png`, `render-2rm14-inside.png` | Favourite 1: 2РМ14 on the rear panel, and the lead inside |
| `render-cheek-jack.png` | Favourite 2: long-bush panel DC jack through the right cheek |

To rebuild: `python3 3d/case-pair/power-options/power_options.py` redraws the sheets.
Add `--render` for the OpenSCAD pictures, which need xvfb-run and take about 30 s.

## Marks

Every number carries one of these marks:

- **model**: from `case_pair.py`'s numbers.
- **assumed**: the model's own guesses: plug barrel 9.5, nose Ø10, 7.0 mm needed.
- **board**: read from the TS06-DRV board file.
- **seen**: in a web-search excerpt of a datasheet table or a distributor's page.
- **computed**: worked out here from the numbers above.
- **inferred**: reasoning, not checked against a part.

**Where the connector numbers come from.** The network policy refused to open any page: asenergi,
arbatex, chipdip, eandc, elektrodetal, radiodetali and Wikipedia were all tried. Web search still
worked, so "seen" means a number quoted in a search excerpt. No datasheet drawing was opened. Check
every connector against the part in hand before cutting a panel.

## The numbers everything rests on

- **Cheek and plug:** the cheek is 6.0 thick and the jack mouth sits 0.8 inside its inner face
  (model). Barrel 9.5, nose Ø10, 7.0 needed (assumed).
- **The rule (computed):** engaged = 9.5 − (0.8 + t), where t is the cheek left in front of the
  nose's stop. So t must be **1.7 mm or less**, or nothing may stop the nose at all; then the whole
  9.5 goes in.
- **Behind the rear panel:** 25.0 mm from TS06-DRV's back face (Z 44.2) to the panel's inner face
  (Z 69.2), less the parts under the connector (model).
- **XS1's pads (board):**

  | Pad | Net | Where (X, Y) | Hole |
  |---|---|---|---|
  | 1 | VIN_J | 177.4, 91.5 | 1.0 x 3.0 slot |
  | 2 | GND | 183.4, 91.5 | 1.0 x 3.0 slot |
  | 3 | GND (switch contact) | 180.4, 86.8 | 3.0 x 1.0 slot |

  Pads 1 and 2 are 6.0 apart.
- **Current:** the clock draws about 0.4 A at 12 V. The adapter is at least 1 A, 5.5 x 2.1,
  centre + (both from `PCB/TS06-pair-testing.md`).
- **Protection on the board:** VD2 is a series Schottky and VD4 is a TVS after F1, which trips F1
  (netlist, `tools/ts06pair.py`). Both still guard a reversed lead in every option below.

## A. Cut-outs in the right cheek (board unchanged, the 5.5 x 2.1 plug kept)

The engaged lengths are computed. The nose sizes are assumed. The same numbers are in section
on `cheek-cutouts-section.png`.

| # | Cut | Engaged | Nose-size risk |
|---|---|---|---|
| ref | Plain cheek, Ø9 hole | **2.7 FAIL** | any nose over Ø9 stops outside |
| now | The model: Ø14 pocket from outside, 1.5 web, Ø9 | **7.2** | noses Ø9–14 give 7.2; over Ø14 gives 2.7 |
| A1 | Clear hole Ø11 straight through | **9.5** (whole barrel) | a nose of Ø11.5 or more gives 2.7 |
| A2 | Slot 11 wide, open to the rear edge (24 long), right-angle plug | **9.5** | needs a right-angle plug. Its elbow stands 4.2 proud (Ø11 elbow assumed) |
| A3 | Recessed well Ø18 x 5 deep, 1.0 web, Ø9 | **7.7** | any nose Ø9–18 gives 7.7 |
| A4 | Stepped counterbore: Ø16 x 2, then Ø11 through | **9.5** with a Ø10 nose | a nose of Ø11–16 stops on the step: 4.7 FAIL; over Ø16: 2.7 |

What changes, for all of these: only the right cheek's cut in `case.scad` (JACK_HOLE_D, JACK_CB_D
and JACK_WEB, or a slot). There is no change on the board.

- **Assembly and service (inferred):** as now. The module slides in from behind and the jack
  stays inside the cheek line.
- **Safety:** as now. 12 V only, and VD2 and VD4 guard a reversed plug.
- **Looks (inferred):**
  - A1 shows the jack's mouth 6.8 mm down a plain hole.
  - A4 reads as a deliberate socket.
  - A3 is a round well.
  - A2 cuts a long slot to the rear edge.
- **Cost (inferred):** nothing but print time.
- **Weak point:** A1, A2 and A4 depend on the real plug's nose. A3 needs a printed 1.0 mm web to
  take every plug's push; its strength is inferred, not tested.

## B. Lids, hatches, a removable panel

- **B1: slot and hatch cap.** This is the A2 slot, closed outside by a screwed cap, with a
  right-angle plug and its lead leaving at the rear edge.
  - Engaged: **9.5** (computed). The cap stands **6.2 mm proud** of the cheek (computed from an
    assumed Ø11 elbow, a 1.5 wall and 0.5 of air).
  - To unplug, take out 2 screws.
  - Looks: a chunky boss on the side (inferred).
  - A flip lid over a straight plug cannot close: a straight plug stands out about 25–40 mm
    (inferred).
- **B2: removable metal panel.** A 1.5 mm aluminium plate sits flush with the cheek's inner face,
  with a Ø9 hole. The print has a window around the nose, and the plate is held by countersunk
  screws from inside (inferred).
  - Engaged: **7.2** for any nose over Ø9 (computed). A 1.0 plate gives 7.7; a 2.0 plate gives
    6.7, a FAIL.
  - Metal takes the plug's push, which answers the earlier review's doubt about a 1.5 mm printed
    web.
  - To reach the plate, the right cheek comes off: its 6 cheek screws and the module's 2 screws
    into it, H5 and H7 (inferred).
  - The plate can later carry a panel connector instead of the hole.
  - Board unchanged. Cost: a small cut plate (inferred).

## C. Moving the port (panel socket, flying lead to XS1's pads)

**How the board takes the lead.** Leave XS1 off and solder the two wires into its pads: 1 (VIN_J)
and 2 (GND). These are 1.0 x 3.0 slots (board). This needs **no board change**.

- **Wire:** tinned AWG20 (0.5 mm²) or AWG22 goes into a 1.0 slot (inferred), which is ample for
  0.4 A.
- **Strain relief:** a P-clip under the module screw at H7 (187.9, 100.5), 9 mm above the pads
  (inferred).
- **A short in the lead:** the lead joins before F1, so the adapter alone limits a short in the
  lead itself. Insulate the solder cups (inferred).

**A 2-pin header instead needs a board change** (a rev C). The free space was checked on a 0.5 mm
grid from the board file, against courtyards, pads and tracks with 0.5 clearance:

- **In XS1's place:** a JST VH 2-pin (3.96 pitch, 10 A seen) fits 56 ways and an XH (2.5 pitch)
  fits 187 ways. VIN_J and GND already arrive there.
- **Beside XS1, both fitted:** no VH fits in the right-hand 40 mm. An XH fits above XS1 (X
  174.5–183.9, Y 97.2–103.5) and in a strip at X 173.0–180.4, Y 24.7–56.0.
- **Courtyards used:** VH 8.8 x 9.8 and XH 7.4 x 6.3 (inferred).
- **No standard header fits the existing pads:** they are 6.0 apart.

**Where it can go.** All numbers are computed. The places are drawn on `move-port-rear.png`.

| Place | Connector | Room / need / margin (mm) | Lead at least |
|---|---|---|---|
| 1 rear panel, X 182.5 Y 91.5, over XS1's place | 2РМ14 | 22.2 / 18 / **4.2** | 17 mm |
| 1 | DIN socket | 22.2 / 21 / **1.2** | 14 mm |
| 1 | panel DC jack | 22.2 / 22 / **0.2** (tight) | 13 mm |
| 1 | ШР20 | **no**: its Ø20 body runs into the right cheek | – |
| 2 rear panel, X 178 Y 49.5, the empty patch | ШР20 | 25.0 / 25 / **0.0** | 52 mm |
| 2 | 2РМ14 | 25.0 / 18 / **7.0** | 59 mm |
| 3 right cheek, axis Y 91.5 Z 57 | long-bush DC jack | 12.8 over the board, 12.2 to the rear panel, no part in the way | about 20 mm |
| 4 left cheek | any socket | the lead crosses the whole board, about 271 mm; the USB slot is there too | – |
| 5 bottom | any socket | the clock stands on its base: feet taller than plug + bend | – |

- **Room** = 25.0 less the tallest part under the connector's body. At place 1 that part is the
  H7 screw head, 2.8.
- **Need** = the body behind the panel plus 5 for the solder cups and the bend. Both are inferred:
  no length behind the panel was seen for any part.
- **Cut the lead** about 60 mm longer than the minimum, so the rear panel can lie beside the case
  while it is open (inferred).
- **Rear panel:** it is 1.6 mm FR4 (model), a good panel for any flange. It already carries the
  "12 V DC centre +" label, which changes with the connector.

## D. Chunky Soviet connectors

Numbers marked "seen" are from search excerpts; the rest are inferred. All four are drawn to
scale on `soviet-connectors.png`.

| | 2РМ14 | ШР20 | ОНЦ-ВГ-4-5/16-р (СГ-5 DIN) |
|---|---|---|---|
| Panel part | 2РМ14Б4Ш1В1 (4 pins) | ШР20П4ЭШ8 (4 pins) | ОНЦ-ВГ-4-5/16-р (socket) |
| Cable part | 2РМ14КПН4Г1В1 (4 sockets, straight nozzle) | ШР20П4НГ8 (4 sockets) | ОНЦ-ВГ-4-5/16-в (plug, СШ-5) |
| Contacts, rating | 4 x Ø1.0, 8 A each, 27 A total, 560 V (seen) | 4 x Ø2.5, 25 A each, 100 A total, 850 V (seen) | 5, 2 A, 34 V (seen) |
| Flange | 24 square, holes 17 apart (seen); hole Ø3.2 (inferred) | 30 square, holes 22 ±0.1 apart, Ø3.2 (seen) | 29 x 20.6 x 19 overall, 2 x M3 (seen); holes 22 apart (inferred) |
| Body | seat M14x1, L max 25 (seen); 13 behind the panel (inferred) | Ø20, coupling M24x1.5 (seen); 20 behind (inferred) | 16 behind (inferred) |
| Coupling | bayonet, keyed (inferred) | threaded nut, keyed (inferred) | push-fit, no lock |
| Polarity safety | keyed. Use pins 1, 2 for + and 3, 4 for −. Pins on the clock and sockets on the live lead: touch-safe (inferred) | the same | keyed, but it is the Soviet **audio** socket: a tape-deck lead fits and would get 12 V (inferred) |
| Strain relief | the cable part's nozzle nut grips the lead; cores up to 0.5 mm² (seen) | the cable part's nut; the part is heavy, 37 g (seen) | the plug's own clamp |
| Availability | cable parts listed with 2023 and 2025–26 production (seen); easy (inferred) | listed by several sellers (seen); easy (inferred) | listed with 2019–20 production, maker Копир (seen) |
| Mounts | rear panel place 1 or 2, or a metal plate in the cheek | rear panel place 2 only | rear panel place 1 |
| Looks (inferred) | the grey Soviet instrument socket | the chunkiest: military | 1980s hi-fi |
| Cost (inferred) | low | medium | low |

**Considered and not picked:**

- **РШ2Н / РГ1Н** (seen: 3 A a contact, 400 V, 2.8 pitch): a rectangular block connector, not a
  chunky panel socket.
- **РС4ТВ** (seen: 4 contacts, 4 A, 200 V; the cable socket is Ø14 x 36): a smaller threaded
  alternative to the 2РМ14.
- **2РМТ14:** the heat-resistant 2РМ14; its sizes are the same (inferred).

**The adapter (inferred).** Fit the cable part to a 12 V brick's lead in place of its barrel plug,
or make a short tail from the Soviet connector to a 5.5 x 2.1 jack, so any brick works.

## Ranked recommendation

1. **2РМ14 on the rear panel, place 1, with a lead to XS1's pads.**
   - No board change. Margin 4.2 mm on an inferred body length; lead at least 17 mm, cut to about
     77.
   - Bayonet, keyed, 8 A contacts, and a nozzle nut for strain relief.
   - The right cheek goes plain. It is the chunky Soviet look the owner asked for, and it is still
     made.
   - Check before cutting: the body's length behind the flange and the flange hole size.
   - Pictures: `render-2rm14-rear.png` and `render-2rm14-inside.png`.
2. **Long-bush panel DC jack through the right cheek, its axis moved 6.3 mm towards the back
   (Z 50.7 to 57), 12.8 off the board** (place 3).
   - Keeps any standard 12 V brick. The barrel seats fully by the jack's own design, whatever the
     nose.
   - No part is in the way (computed). No board change: XS1 is left off and a 20 mm lead goes to
     its pads.
   - The cheaper, plainer fallback. Picture: `render-cheek-jack.png`.
3. **ШР20 on the rear panel, place 2.** The chunkiest, but margin 0.0 on an inferred 20 mm body,
   a lead of at least 52 mm and a 37 g cable part.
4. **B2, the removable metal panel.** 7.2 with any nose over Ø9 (7.7 with a 1.0 plate). It keeps
   XS1 fitted, and the plate can later carry a 2РМ14.
5. **A3, the recessed well Ø18 with a 1.0 web.** 7.7 with any nose Ø9–18. It is only three
   numbers in the model, but the printed web is untested.
6. **Panel DC jack on the rear panel.** Tight at place 1 (0.2 margin) and fine at place 2 (the
   lead is at least 59 mm).
7. **A1 and A4, the clear hole and the stepped counterbore.** 9.5, but only if the real nose is
   under Ø11.
8. **B1 and A2, the slot with or without the hatch cap.** 9.5, but they need a right-angle plug
   and add a 6.2 mm boss or a long slot.
9. **The DIN socket.** 2 A and the risk of an audio lead.
10. **Left cheek or bottom.** A 271 mm lead, or feet under the clock.

## Not done, or still open

- No connector dimension was checked against a datasheet drawing or a part, because the pages
  could not be opened. That covers the lengths behind the panel, the flange hole sizes, the
  DIN's hole spacing and the panel jack's body.
- The plug's nose, the elbow of a right-angle plug and the 7 mm needed are still the model's
  assumptions.
- No web or plate was strength-tested.
- The case model was not changed. When an option is chosen, it goes into `case_pair.py` and
  `case.scad` (and their checks) as a separate change.
- The board was not changed. A rev C header is only described above.
