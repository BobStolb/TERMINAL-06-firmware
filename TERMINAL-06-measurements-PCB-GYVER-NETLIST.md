# TERMINAL-06 — measurement sheet: the inherited board's netlist (Gerber-derived)

**Source:** `PCB/IN-12_norm/` — the EasyEDA Gerbers and drill files the physical boards
were made from (v6.3.53, 2020-06-13). **Method:** `tools/tracegyver.py` rasterises both
copper layers at 0.05 mm, labels the connected copper, joins the layers through the
plated holes and names every hole from geometry. Nothing here was read off a photo or a
datasheet drawing of the board; the board's own copper is the source. Regenerate the
tables with `python3 tools/tracegyver.py`; `--png` also writes
`PCB/IN-12_norm/gyver_copper.png`.

**Captured 17.09.26**, as phase 0 of TS06-MAIN. The board is AlexGyver's *NixieClock
v2.2, IN-12_norm* ("Based on itworkclub PCB", says the bottom copper). AlexGyver's own
page states the project **never had a schematic — the PCB was drawn directly**, so this
sheet is the first circuit record of it.

Companion sheet: `TERMINAL-06-measurements-PCB-IN12BOARD.md` (the geometry, 08.09.26).
Coordinates below are mm from the panel's bottom-left corner, Y up, seen from the
component side. Part names follow AlexGyver's silkscreen render
(`schemes/IN-12_norm.jpg` in his repo): U1 Nano, D1 К155ИД1, U2–U5 TLP627, P1–P4 the
mating headers, S1–S3 the tact switches.

---

## 1. The circuit, in one picture

```
                         5 V in ─┬──────────────┬─────────────────────┬──── U1 5V (Nano)
                        470 µF ═╪═   100 nF ═══╪═  L1 220 µH          │
                                │              │      │               ├──── D1 pin 5 VCC
   D9 ──100 Ω──┤ gate     drain ┼──────────────┼──────┘               ├──── RTC + / VCC
             VT1 IRF840   source│              │  │                   └──── switches' returns
                                └───── GND ────┴──┼─────────────── GND pour (both halves)
                                                  │
                                    VD1 HER106  ──┴──►│──┬── HV+ ──┬──────────────┬── RP1 470 kΩ
                                                         │         │              │   (variable bleed,
                                              C1 4.7 µF ═╪═  Ranode 10 kΩ       one end open)
                                                350 V    │         │              │
                                                        GND        ├── U2..U5 collector (pin 4)  GND
                                                                   │
              D3 ─┤U5 LED  U5 emitter├── P2.5 ─ P1.5 ─ V1 anode (pad 7)   tube 1, hours tens
              D4 ─┤U4      U4       ├── P2.4 ─ P1.4 ─ V2 anode           tube 2, hours units
              D5 ─┤U3      U3       ├── P2.3 ─ P1.3 ─ V3 anode           tube 3, minutes tens
              D6 ─┤U2      U2       ├── P2.2 ─ P1.2 ─ V4 anode           tube 4, minutes units
                    all four LED cathodes ── 470 Ω ── GND

   A3 ── D1 pin 3 (A, 1)    A1 ── pin 6 (B, 2)    A0 ── pin 7 (C, 4)    A2 ── pin 4 (D, 8)
   D1 outputs Q0..Q9 ── P4.k ─ P3.k ── the same socket pad on all four tubes   (§4)

   D10 ── 150 Ω ── P2.6 ─ P1.6 ── HL5 "dot" LED ── GND        (the colon position)
   D11 ── 100 Ω ── P2.1 ─ P1.1 ── HL1..HL4 in parallel ── GND  (backlight, one resistor for four)
   D2  ── 100 Ω ── BUZ+                                        (buzzer, removed in this firmware)
   D7 / D8 / D12 ── S1 / S2 / S3 ── GND                        (SET, ADJ, lever; no pull-ups)
   A4 ── SDA, A5 ── SCL ── both RTC headers                    (§6)
   not connected: D13, A6, A7, VIN, 3V3, REF, RST, TX, RX
```

## 2. The 185 V converter — what it is, and what it is not

| Part (silkscreen) | Connection |
|---|---|
| VT1 **IRF840** TO-220, pins S-D-G left to right at Y 60.20 | gate ← 100 Ω ← D9; source → GND; drain → L1 and VD1 anode |
| L1 **220 µH** | drain node ↔ +5 V |
| VD1 **HER106** | anode at the drain node, cathode → HV+ |
| C1 **4.7 µF 350 V** | HV+ ↔ GND, the reservoir |
| **10 kΩ** (vertical, left of the optos) | HV+ → the common collector bus of U2..U5. **The one and only anode resistor on the board, shared by all four tubes** — legal because only one opto conducts at a time |
| RP1 **470 kΩ** trimmer | one end unconnected, wiper on HV+, other end on GND: **a variable bleed resistor from HV+ to GND, nothing else** |
| **470 Ω** (top, beside the trimmer) | the four opto LED cathodes → GND, one resistor for four LEDs |

**There is no feedback.** Nothing measures the rail. D9 runs at a fixed 31 kHz and a fixed
on-time (`DUTY 190` of 255 in the firmware, 23.8 µs), the MOSFET is driven straight from
the 5 V pin through 100 Ω with no pull-down, and the stage delivers a **fixed energy per
cycle** in discontinuous conduction:

| Quantity | Value |
|---|---|
| Peak inductor current, 5 V in, 23.8 µs on, 220 µH | 0.54 A |
| Energy per cycle ½·L·I² | 32 µJ |
| Deliverable power at 31.25 kHz | **≈ 1.0 W** (before losses) |
| Discharge time at 185 V | 0.7 µs of the 8 µs left — deep DCM, the model holds |
| Four multiplexed ИН-12 at 2.5–5 mA average | 0.5–0.9 W |
| Same stage fed from 12 V | 1.3 A peak, 186 µJ, **≈ 5.8 W** |

The rail therefore sits wherever the load balances that 1 W: with four tubes it is
≈185 V, with nothing but the trimmer it would climb towards √(P·R) — several hundred
volts against a 350 V capacitor — which is why the trimmer exists at all. It is the
adjustable dummy load that keeps the rail down, not a regulator. AlexGyver's page says
exactly this in fewer words: the voltage is set by "the resistor and the PWM duty".

**Consequences for TS06-MAIN** (the numbers behind the 17.09.26 power-input decision):
six multiplexed digits plus two statically driven ИН-15 at 8k2 plus the colon need
≈3.5 W at 185 V. The stock stage cannot supply it from 5 V at any trimmer setting. Fed
from 12 V, the same topology has margin; a real feedback loop replaces the bleed
trimmer; and every tube gets its own anode resistor, because a stiff rail and a shared
10 kΩ would no longer limit anything.

## 3. Corrections to earlier documents

| Where | It said | The copper says |
|---|---|---|
| `TERMINAL-06-measurements-PCB-IN12BOARD.md` §1 | "Ground pour: none, either layer" | Both halves carry a **bottom-side pour**: GND on the driver half, the LED/GND return (P1.7) on the tube half. Top layer: pads only, 53 sub-millimetre stubs, no traces — that part was right. |
| prototype plan, 04.09.26 | "the 100 Ω resistors beside the optos are LED-side current limiters, ~38 mA" | The three 100 Ω are the D9 gate resistor, the D11 backlight resistor and the D2 buzzer resistor. The opto LEDs share **one 470 Ω** on the cathode side: ≈8 mA, not 38. |
| prototype plan, 06.09.26 | "a 470 kΩ fixed resistor plus the 500 kΩ P504 trimmer between HV+ and ground (the feedback divider)" | Only the trimmer sits between HV+ and GND, as a bleed. The "470" is the LED resistor. There is no divider and nothing to feed back to. |
| spec §4 | "the stock board has no per-tube anode resistor" | True per tube. There is one **shared 10 kΩ** from HV+ to all four collectors. |
| handoff §6.1 | "topology and component values are not recorded anywhere in this repo" | Now they are — above. Only the trimmer's setting and the rail under load still need a meter (gates sheet, gate 1). |
| handoff §6.2, IN12BOARD §3 | "which hole is the anode and which are the ten cathodes is not known — meter it" | Known, §4 below, and cross-checked four ways. No meter session needed. |
| firmware header | "IN-12 turned" board, `BOARD_TYPE 0` | Confirmed: the mask that matches this copper is `{7, 3, 6, 4, 1, 9, 8, 0, 5, 2}`. |

## 4. The display chain — closed four ways

The К155ИД1 (DIP-16, pin 1 top-left at (78.23, 70.36), pins 1–8 down the left column,
9–16 up the right) is wired from the Nano exactly as the datasheet pinout requires, and
exactly as the firmware's `decoderNibble` assumes:

| Nano | К155ИД1 pin | Function | firmware bit (`1_setup.ino`) |
|---|---|---|---|
| A3 | 3 | A, weight 1 | bit 0 of the mask |
| A1 | 6 | B, weight 2 | bit 1 |
| A0 | 7 | C, weight 4 | bit 2 |
| A2 | 4 | D, weight 8 | bit 3 |
| 5 V / GND | 5 / 12 | VCC / GND | — |

The ten outputs go to P4, which mates pin-for-pin with P3 on the tube board (a pure
translation of 40.13 mm in Y, the FreeCAD assembly and the header rows agree), and each
P3 pin reaches **the same socket pad on all four tubes**. Socket pads are numbered as in
`TS06_IN12_Socket`: clockwise from the upper-left as seen from the tube side; pad 7 is
the anode (unique copper per tube), pad 8 has no copper at all (ИН-12А pin 12, n/c). The
ИН-12А datasheet (pin 1 anode, pins 2–11 cathodes 0 9 8 7 6 5 4 3 2 1) lands pin *d* on
pad ((7 − d) mod 12) + 1.

```
К155ИД1 output -> header pin -> socket pad (all four tubes) -> ИН-12А cathode, against firmware digitMask (BOARD_TYPE 0):
  Q0 pin 16 -> P4.8  = P3.8  -> pad  3 = cathode 7   firmware shows digit 7 with code 0: ok
  Q1 pin 15 -> P4.7  = P3.7  -> pad 12 = cathode 4   firmware shows digit 4 with code 1: ok
  Q2 pin  8 -> P4.4  = P3.4  -> pad  5 = cathode 9   firmware shows digit 9 with code 2: ok
  Q3 pin  9 -> P4.1  = P3.1  -> pad  9 = cathode 1   firmware shows digit 1 with code 3: ok
  Q4 pin 13 -> P4.5  = P3.5  -> pad 11 = cathode 3   firmware shows digit 3 with code 4: ok
  Q5 pin 14 -> P4.6  = P3.6  -> pad  4 = cathode 8   firmware shows digit 8 with code 5: ok
  Q6 pin 11 -> P4.3  = P3.3  -> pad 10 = cathode 2   firmware shows digit 2 with code 6: ok
  Q7 pin 10 -> P4.2  = P3.2  -> pad  6 = cathode 0   firmware shows digit 0 with code 7: ok
  Q8 pin  1 -> P4.10 = P3.10 -> pad  2 = cathode 6   firmware shows digit 6 with code 8: ok
  Q9 pin  2 -> P4.9  = P3.9  -> pad  1 = cathode 5   firmware shows digit 5 with code 9: ok
  10/10 agree
```

Four independent sources — the К155ИД1 datasheet pinout, the ИН-12А datasheet cathode
order, this copper, and a firmware table proven on the bench with real tubes — agree on
all ten digits. A wrong assumption in any one of them would show up as a scrambled
permutation, not as ten matches.

**Socket pad → function, ИН-12А, in `TS06_IN12_Socket` numbering:**

| pad | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cathode | 5 | 6 | 7 | 8 | 9 | 0 | **anode** | n/c | 1 | 2 | 3 | 4 |

**What TS06-MAIN copies.** Name the cathode bus by digit, K0..K9, and wire К155ИД1
output Q*c* to the cathode of digit *d* where `digitMask[d] = c` — i.e. Q0→K7, Q1→K4,
Q2→K9, Q3→K1, Q4→K3, Q5→K8, Q6→K2, Q7→K0, Q8→K6, Q9→K5 — and the firmware keeps
`BOARD_TYPE 0` unchanged. (Wiring Q*d*→K*d* and switching to `BOARD_TYPE 3` would be
the equally valid alternative; it costs one `#define` and buys nothing.) The ИН-17 cathode
for digit *d* joins K*d*; its lead order is gate 3 of the bench sheet.

## 5. The mating headers

P1 (tube board, left edge) mates with P2 (driver board), P3 with P4, pin *k* to pin *k*.

| pin | P1 = P2 | P3 = P4 |
|---|---|---|
| 1 | backlight LED anodes (D11 via 100 Ω) | Q3 → cathode 1 |
| 2 | V4 anode (minutes units) ← U2 emitter | Q7 → cathode 0 |
| 3 | V3 anode (minutes tens) ← U3 emitter | Q6 → cathode 2 |
| 4 | V2 anode (hours units) ← U4 emitter | Q2 → cathode 9 |
| 5 | V1 anode (hours tens) ← U5 emitter | Q4 → cathode 3 |
| 6 | dot LED anode (D10 via 150 Ω) | Q5 → cathode 8 |
| 7 | GND (LED cathodes, the tube half's pour) | Q1 → cathode 4 |
| 8 | — | Q0 → cathode 7 |
| 9 | — | Q9 → cathode 5 |
| 10 | — | Q8 → cathode 6 |

Opto to tube: U5 (top) = D3 = hours tens = V1, U4 = D4 = V2, U3 = D5 = V3, U2 (bottom)
= D6 = V4 — the firmware's `KEY0..KEY3 = D3..D6` in tube order. TLP627 pins: 1 LED anode
(from the Nano pin), 2 LED cathode (to the shared 470 Ω), 3 emitter (to the anode), 4
collector (the 10 kΩ bus).

## 6. Everything else on the driver half

| Item | Holes | Net |
|---|---|---|
| Power in "5V / GND" | (74.67, 74.93) / (74.67, 77.47), 2.54 mm pair | +5 V / GND. The 470 µF 6.3 V sits across it; the "ANY CERAMIC" 100 nF sits by the К155ИД1 |
| RTC mini header | (78.48 … 88.64, 37.85), five at 2.54 | **− NC C D +** = GND, n/c, SCL (A5), SDA (A4), +5 V. This is the small DS3231 module's pin order |
| RTC ZS-042 header | (75.94 … 88.64, 41.66), six at 2.54 | **32K SQW SCL SDA VCC GND**: 32K and SQW unconnected, the rest as above. The board takes either module |
| S1, S2, S3 | 6 × 6 mm tact pattern, 6.5 × 4.5 mm, at X 15.34 / 28.04 / 40.74, Y 36.07 / 40.57 | to D7, D8, D12; the other side on GND. No pull-ups on the board |
| BUZ | (45.72, 75.95) − / (48.26, 75.95) + | − GND, + ← 100 Ω ← D2 |
| Nano U1 | X 54.35 (D side) and 69.59 (A side), 15 each at 2.54, pin 1 (TX1 / VIN) at Y 76.45; the D12 hole sits at Y 40.64, off-pitch | as in §1. Powered through its **5V pin**, VIN open |
| Mounting | NPTH Ø3.0 at (3.56, 78.23), (3.56, 36.58), (95.56, 78.23), (95.56, 36.58) | 3.5 mm inset, 92.0 × 41.65 mm apart |

Tube half: four sockets (`IN12BOARD.md` §3), the Ø5 pip holes, HL1–HL4 backlight LEDs
at Y 4.06 (anode at X 12.19 / 35.56 / 62.99 / 86.10, cathode 2.54 to the right), the
dot LED HL5 at (48.51 / 51.05, 2.79), P1 and P3.

## 7. Still open on this board

* The **trimmer's setting and the rail under load** — gate 1 of
  `knowledge/TERMINAL-06-measurements-TS06-MAIN-gates.txt`. The copper fixes the
  circuit; only the operating point is a bench number.
* Whether the physical boards carry the silkscreen's values (IRF840, HER106, 220 µH,
  4.7 µF 350 V, 470 kΩ) — a glance, not a measurement; the prototype plan read the
  trimmer as "P504".
