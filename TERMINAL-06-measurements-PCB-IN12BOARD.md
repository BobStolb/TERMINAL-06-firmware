# TERMINAL-06 — measurement sheet: the inherited ИН-12 board (Gerber-derived)

**Source:** `PCB/IN-12_norm/` — EasyEDA v6.3.53, generated 2020-06-13T07:22:25+03:00.
**Method:** parsed directly from `Gerber_BoardOutline.GKO`, `Gerber_Drill_PTH.DRL` and
`Gerber_Drill_NPTH.DRL`. These are **not** estimates off a photo — they are the
fabrication data the physical board was made from, converted from imperial
(2.4 format, inches) to millimetres. Origin is the board's bottom-left corner.

**Captured 08.09.26**, during the "do we actually need TS06-TUBE" question. Every
number here is exact to the resolution the Gerbers carry (0.0001 in = 2.54 µm).

---

## 1. Panel

| Item | Value |
|---|---|
| Panel outline | **99.06 × 80.77 mm** (3.8999 × 3.1800 in) |
| Layers | 2. **Top layer carries no traces at all** — 142 pad flashes only. All routing is bottom-side. |
| Ground pour | **None, either layer.** All copper is discrete traces. A pad is never grounded by sitting in a pour on this board. |
| Construction | Ships as ONE panel, cut along the silkscreened white line into the tube board and the driver board, which then mate via P1↔P2 / P3↔P4. |
| Tube half | Y ≈ 0 … 44 mm of the panel (the four tube positions plus the mating headers at Y 36–42). |

## 2. ИН-12А tube positions — the four numbers that fix the deck geometry

All four tube centres sit on **Y = 20.07 mm**.

| Tube | X centre (mm) | Gap to next (mm) |
|---|---|---|
| 1 (H tens) | 13.21 | — |
| 2 (H units) | 36.57 | **23.36** |
| 3 (M tens) | 63.99 | **27.42** ← the HH:MM group break |
| 4 (M units) | 87.37 | **23.38** |

**Pitch is 23.36 / 27.42 / 23.36 mm.** This is the single most consequential number
on the board: it is fixed by someone else's layout and it is what TS06-TUBE would
exist to change.

## 3. ИН-12А socket footprint — complete, ready to draw in KiCad

**12 plated holes, Ø 1.194 mm (0.047 in), plus one unplated Ø 5.00 mm (0.197 in)
centre hole.** The pattern is **not a circle and not an ellipse** — it is a
stadium/oval: two straight vertical flanks joined by top and bottom arcs. Do not try
to generate it from a "pin circle diameter"; use the coordinates.

Offsets from the tube centre (the 5 mm NPTH hole), in mm:

| # | ΔX | ΔY |
|---|---|---|
| 1 | +5.74 | 0.00 |
| 2 | +5.74 | +4.49 |
| 3 | +3.99 | +8.00 |
| 4 | 0.00 | +8.99 |
| 5 | −3.99 | +8.00 |
| 6 | −5.74 | +4.49 |
| 7 | −5.74 | 0.00 |
| 8 | −5.74 | −4.50 |
| 9 | −3.99 | −8.01 |
| 10 | 0.00 | −8.99 |
| 11 | +3.99 | −8.01 |
| 12 | +5.74 | −4.50 |

Overall pin envelope: **11.48 mm across (X) × 17.98 mm tall (Y).** The tube's wide
axis therefore runs along **Y** in this layout, i.e. the tubes stand upright with the
board flat.

**Pin numbering is NOT established.** These are geometric positions only. Which
physical hole is the anode and which are the ten cathodes has to be metered, exactly
as `secCathodeMap` does for the ИН-17s. The 04.09.26 procedure still applies:
continuity between the **same-position** hole on two **different** tube positions —
**no continuity → anode** (unique per tube), **continuity → shared cathode** (bussed
to the К155ИД1).

## 4. Other features on the tube half

| Y (mm) | X positions (mm) | Ø | Reading |
|---|---|---|---|
| 4.06 | 12.19 / 14.73 · 35.56 / 38.10 · 62.99 / 65.53 · 86.10 / 88.64 | 0.81 mm | **Four LED positions**, 2.54 mm pitch pairs, one under each tube — the D11 backlight row. Matches the bench observation that the LED-negative pads daisy-chain along the bottom edge. |
| 2.79 | 48.51 / 51.05 | — | Single 2.54 mm pair on the centreline. |
| 37.85 | 78.48 … 88.64, 2.54 mm pitch | 0.89 mm | **5-pin 0.1 in header** — one half of a mating pair. |
| 41.66 | 75.94 … 88.64, 2.54 mm pitch | — | **6-pin 0.1 in header.** |
| 36.07 / 40.64 | 15.34 / 21.84 / 28.04 / 34.54 / 40.74 / 47.24 (+54.35) | — | Left-hand inter-board connection, irregular ~6.2/6.5 mm pitch. Not a standard header pitch — inspect physically before copying. |

## 5. What this settles, and what it does not

**Settles:** the ИН-12 socket footprint is fully known and can be drawn in KiCad
without touching a caliper. "We need a new board because the socket pins are a
different width" is **not** a reason — the tube defines the pattern, so any socket
that fits the tube fits these holes.

**Settles:** the tube pitch (23.36 / 27.42 / 23.36) and the fact that all four tubes
sit on one Y line with the tube's wide axis vertical.

**Does not settle:** hole-to-function mapping (anode vs. cathodes) — meter it.

**Does not settle:** whether TS06-TUBE is worth fabricating. That is a **case**
decision (deck height, forward offset, rake — spec §6 "Brow reveal"), not an
electrical one, and it should be judged against a printed brow test-fit. Note the
counter-argument on the other side: ten main boards are already owned, which means
ten tube halves are already owned, and TS06-TUBE is ~1 425 ₽/unit of Group D that
does not have to be spent. The anode-bleed rationale for this board was **withdrawn
06.09.26** (root cause was empty multiplex slots, spec §5a-pre), so geometry is the
only live reason left.
