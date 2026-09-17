# TS06-MAIN — handoff: one board for the whole clock, in two builds

**To:** the next session (Fable Code). **From:** the session that drew TS06-SEC.
**Date:** 17.09.26. **Status of this document:** a brief, not a design. Nothing below is
committed to git.

---

## 1. What is being asked

Replace the current three-board electrical stack with **one board**, so a complete
TERMINAL-06 is **two PCBs total**:

| | Board | Carries |
|---|---|---|
| 1 | **TS06-MAIN** (new) | every tube, every driver, the MCU, the RTC, the 185 V converter |
| 2 | **TS06-FASCIA** (exists, routed) | the control panel and the product face |

Draw TS06-MAIN in **two builds, same outline, same netlist, same connectors**, exactly the
way the fascia already has two:

* **TS06-MAIN** — surface-mount wherever a part exists in surface-mount form.
* **TS06-MAIN-THT** — through-hole: Arduino Nano on headers, DIP logic, TO-92 transistors,
  axial passives.

They are alternatives, not a pair; one gets fabricated.

## 2. Why, in the owner's words (17.09.26)

> "Why are we manufacturing two new sets of boards to bridge the gap between what we have
> and what we don't if the gyver board surplus is only 8 pcs — they will be gone soon
> realistically. I think we should design a single combined board from gyverpcb, colon and
> SEC."

Three things follow, and they are the reason this brief exists:

1. **The surplus is finite.** The design currently depends on the inherited
   AlexGyver/itworkclub ИН-12 board for the MCU, the К155ИД1 cathode decoder, four anode
   drivers and the 185 V converter. About 8 boards are left. A product that cannot be built
   once they run out is not a product.
2. **The stack is where the complexity went.** TS06-SEC and TS06-COLON exist only to bridge
   from that board to the tubes it does not drive. They cost two boards, three harnesses
   (185 V, the ten-line cathode bus, logic) and a set of keyed connector families.
3. **The via count is a symptom, not the disease.** TS06-SEC routes 63 nets and **79 vias**
   into 67 × 55 mm with four tube pin fields and every part on one face. The owner is right
   that this is not the best the design can be; the fix is not a better router, it is more
   board and a layout that is not fighting a bus arriving through a connector.

## 3. What already exists (read these before drawing anything)

**Boards** (`PCB/`):

* `TS06-FASCIA/` and `TS06-FASCIA-THT/` — routed, checked, zero vias. **Read these two as
  the model for how a board in this repo is built**: a generator writes the whole file,
  checkers verify it, `preview.svg` shows it.
* `TS06-SEC/` — routed and clean (1159 tracks, 79 vias), now **superseded by this work**.
  Its generator is still the best worked example of a hard placement problem.
* `TS06-COLON/` — the neon strip, placement only. Also superseded: the colon lamps move onto
  TS06-MAIN.
* `IN-12_norm/` — the inherited board's **real fabrication data** (EasyEDA Gerbers + drill).
  This is the source of the tube geometry, and the only electrical record of the board being
  replaced.

**Tools** (`tools/`), all Python 3.11 + numpy, no other dependencies:

| Tool | What it does |
|---|---|
| `mkpcb_sec.py`, `mkpcb_colon.py`, `mkpcb.py`, `mkpcb_tht.py` | board generators: placement and routing, one file each |
| `mksch.py`, `checksch.py`, `checkmatch.py` | schematic generation, dangling-pin check, schematic-vs-board agreement |
| `pcbroute.py` | the grid router written for SEC (see §8) |
| `checkpcb.py`, `checkcopper.py`, `audit.py` | placement, clearance, connectivity/pour/silk |
| `mkfp.py`, `mkfp_sec.py` | footprint generators |
| `render.py` | `.kicad_pcb` → `preview.svg`, both faces |

**Footprints** (`PCB/lib/TS06.pretty/`) — already correct and checked:
`TS06_IN12_Socket` (also used for ИН-15: same envelope), `TS06_IN17_Socket`, back-mounted
pre-rotated SMD lands (SOT-23, SOIC-28W, 0805, 1206, 2512, SMDIP-4), JST VH/XH and IDC
connectors, `TS06_LED_D3.0mm`, the ИНС-1 and panel-hardware footprints.

**Knowledge** (`knowledge/`, plus `TERMINAL-06-measurements-PCB-IN12BOARD.md` at the root) —
the measurement sheets are ground truth and outrank any datasheet:
`TERMINAL-06-spec.txt` (the product spec; §4, §5, §5a-pre are the drive scheme),
`TERMINAL-06-measurements-IN12/IN17/INS1.txt`, `TERMINAL-06-anode-driver-study.txt`,
`TERMINAL-06-concept-plates.txt` (case and face geometry).

**Firmware** is in `firmware/`. The pin map below is a contract with it.

**3D:** `3d/Clock.FCStd` is the reviewed 8-tube assembly and the authority on where tubes
sit. `3d/IN12.FCStd`, `3d/IN17.FCStd`, `3d/TS06-COLON.step`, `3d/TS06-FASCIA.step`.

## 4. The circuit to reproduce (this is the whole netlist, in prose)

**MCU:** ATmega328P — Arduino Nano today. **The pin map is fixed by firmware. Do not
renumber anything without editing `firmware/`:**

```
D2  ИН-17 seconds-TENS anode      D9   HV converter oscillator (31 kHz)
D3..D6  ИН-12 HHMM anodes (4)     D10  colon MPSA42 base
D7  button −  (fascia)            D11  backlight PWM
D8  button +  (fascia)            D12  free
D0/D1 serial                      D13  ИН-17 seconds-UNITS anode
A0..A3  К155ИД1 BCD               A4/A5  I²C: DS3231 (0x68) + MCP23017 0x20, 0x21
A6  rotary (fascia)               A7   levers (fascia)
```

**Digit multiplex, 1/6:** one К155ИД1 (DIP-16 Soviet part, no SMD form — it is
through-hole in *both* builds) decodes A0..A3 to a **ten-line cathode bus K0..K9 shared by
all six digit tubes**: 4× ИН-12А + 2× ИН-17. Anodes are switched high-side, one channel per
tube, six channels total: the inherited board has four (the ИН-12s), SEC added two TLP627s
for the ИН-17s. On TS06-MAIN all six live together — consider 2× TLP627-4 (quad) instead of
six singles. Codes 10–15 select no cathode: the firmware writes a blanking code between
slots. **Empty multiplex slots, not the anode drivers, were the ghosting root cause**
(spec §5a-pre) — do not re-litigate that.

**Anode chain per digit tube:** 185 V → anode resistor → tube anode, switched by the opto.
ИН-17 at 1/6 duty: **12 kΩ** (6.6 mA peak, 1.10 mA average) per the spec; ИН-12 values come
from the inherited board — capture them (§6).

**AM/PM, off the multiplex entirely:** 2× ИН-15 (ИН-15Б "AM" = 8 real cathodes, ИН-15А "PM"
= 10), **18 channels**, each a 10 kΩ base resistor into an MPSA42 low-side switch, driven by
two MCP23017 expanders on the same two I²C wires as the RTC. Anode of each ИН-15 sits on
185 V through **8k2** (static drive, not multiplexed). Every MPSA42 must be a **300 V** part:
an off cathode sees close to the full rail.

**Colon:** 2× ИНС-1 neon, **each with its own 220 kΩ ballast, never shared**, both returning
to one MPSA42 low-side switch on D10 (10 kΩ base). Low-side, not an opto: grounds are common,
and a Darlington's turn-off would smear D10's PWM fade.

**Backlight:** amber LEDs under the tubes, PWM on D11; the inherited board has a four-LED row
under the ИН-12s (2.54 mm pairs), SEC added two for the ИН-17s plus HL3, the "m" indicator.
Series resistors sized per LED colour (SEC used 150 R, 220 R).

**185 V converter:** MCU-driven at 31 kHz from D9, on the inherited board. **Its topology and
component values are not recorded anywhere in this repo** — see §6. This is the critical
path of the whole project.

**Fascia connector — a specification, not a layout convenience.**
`J1: 1 +5V, 2 GND, 3 A6, 4 A7, 5 D7, 6 D8`. Board side `S6B-PH-K-S` (THT) or
`S6B-PH-SM4-TB` (SMD); cable `PHR-6`. Both fascia builds already use this order, and the
legend is silkscreened. The panel buttons need no pull-ups (the ATmega's are enabled).

**Three keyed connector families** so 5 V cannot meet 185 V at 11 pm. On TS06-MAIN the
inter-board harnesses mostly vanish: what remains is the fascia cable, 5 V power in, and
whatever the case needs.

## 5. Geometry that is already fixed

**Tube positions** (world coordinates of the reviewed assembly; `3d/Clock.FCStd` is the
authority, and `tools/mkpcb_sec.py`'s header records the transform):

| Tubes | World X | World Y of centres |
|---|---|---|
| ИН-12 ×4 (HH:MM) | 13.21, 36.57, 63.99, 87.37 | 60.17 |
| ИНС-1 colon pair | in the gap between X 36.57 and 63.99 | measured gaps 9.202 / 7.266 mm, preserve exactly |
| ИН-17 ×2 (seconds) | 104.605, 117.605 (13.0 pitch) | 54.79 (5.375 below the ИН-12 line) |
| ИН-15 ×2 (AM/PM) | 135.0, 156.0 (21.0 pitch) | 60.166 |

**ИН-12 pitch is 23.36 / 27.42 / 23.36 mm** — someone else's layout, now permanent because
the case and the fascia were drawn around it. The ИН-12 socket pattern is a **stadium, not a
circle**: 12 plated holes (repo footprint drills 1.2 mm) at the offsets tabulated in
`TERMINAL-06-measurements-PCB-IN12BOARD.md` §3, plus a **Ø5 mm unplated centre hole** for the
exhaust pip. The same footprint serves ИН-15.

**ИН-17** is wire-ended, no socket: 11 leads used of 12, on a 5.6 × 11.7 mm stadium, key gap
on the right just below centre (confirmed on a real tube). **No pip hole** — the ТУ forbids
soldering closer than 8 mm to the glass, so the tube stands ≥ 6.4 mm off the board and the
pip clears it. Verify the pip's projection on a bench tube before fabrication.

**Fascia:** 176 × 40 mm, compressed from 52 mm. A combined main board spanning the tube deck
will be roughly **170 × 80 mm** — about three times SEC's area for a little over twice the
parts, which is the point.

**The old three-board split leaves scars to remove:** SEC's XS1 (185 V in), XS2 (the ten-line
cathode bus), XS4 (to the colon) and the colon's own connector all disappear. That bus becomes
a straight spine on copper.

## 6. Not yet known — gates before any board is ordered

These are measurement tasks, not design tasks. Several block the netlist itself.

1. **The 185 V converter, from the physical Gyver driver half.** Topology, inductor, switch,
   diode, feedback divider, reservoir cap, and how D9's 31 kHz drives it. `PCB/IN-12_norm/`
   has the copper; the board is in hand. **Highest risk item in the project.** Either capture
   it, or deliberately choose a fresh, documented boost design and say so.
2. **ИН-12 hole-to-function mapping.** The socket geometry is known; which hole is the anode
   and which are the ten cathodes is **not**. Meter it: continuity between the same-position
   hole on two different tube positions — no continuity → anode (unique per tube), continuity
   → a cathode bussed to the К155ИД1.
3. **ИН-17 cathode order** (`secCathodeMap` in the spec): one bench session, never a
   datasheet — surplus markings lie.
4. **ИН-15 pinouts.** SEC used a map derived from tec.org.ru and rudatasheet.ru, which agree
   with each other, and calibrated against the inherited board's copper. Confirm on a tube.
5. **ИН-12 anode resistor values and the sustaining voltage** — the inherited board's values,
   read off the board.
6. **5 V input:** connector, current budget with all eight tubes and the backlight, and where
   it enters the case.
7. **Mounting:** hole positions and standoffs for a ~170 × 80 mm board in the existing case,
   from `3d/Clock.FCStd`.

## 7. Decisions to take early (with a recommendation)

| Decision | Recommendation |
|---|---|
| **Layer count** | The owner dislikes vias. On two layers, eight tube pin fields (96+ plated holes) and 18 AM/PM channels will still need some. **Price a 4-layer 170 × 80 board at Rezonit before choosing**: inner GND and 185 V planes would remove nearly every via, shorten the HV loops and make the multiplex quieter. If it stays 2-layer, budget vias deliberately rather than treating each as a defect. |
| **MCU form** | Keep the **Nano module on headers in the THT build** (socketed, replaceable, and the firmware/bootloader story stays unchanged); use a **bare ATmega328P-AU in the SMD build** only if you also add an ISP header and accept flashing differences. When in doubt, Nano in both. |
| **RTC** | The ZS-042 DS3231 module needs its charging circuit disabled (spec). On a fresh board, **fit the DS3231 and its crystal directly** and skip the module and its defect — but that is new-circuit risk; the module on headers is the conservative choice. |
| **Optos** | 2× TLP627-4 for six anode channels, if the quad's isolation and pinout suit the layout. |
| **К155ИД1** | DIP-16 in both builds. No SMD equivalent exists. |
| **The 8 surplus boards** | Keep them as the prototype platform while TS06-MAIN is drawn and fabricated. They are also the only reference for §6.1 and §6.5. |
| **SEC and COLON** | Leave both in the repo, marked superseded in `PCB/README.md`. Their generators and the measured geometry inside them are the starting material for TS06-MAIN's placement. |

## 8. How this repo builds a board (follow it, it works)

**The generator is the source of truth.** `tools/mkpcb_*.py` writes the entire `.kicad_pcb`
from source, deterministically (uuid5, no randomness). Hand edits in KiCad are lost on the
next run — if a hand tweak is worth keeping, put it in the generator. Same for the schematic
via `tools/mksch.py`, and `checkmatch.py` proves the two agree.

**Check everything, every time:**

```
python3 tools/checkpcb.py    <board>.kicad_pcb
python3 tools/checkcopper.py <board>.kicad_pcb --hv "HV185,CAT_*,ANODE_*,EMIT_*,BLEED_*,COLON_RET"
python3 tools/audit.py       <board>.kicad_pcb
python3 tools/checksch.py    <board>.kicad_sch
python3 tools/checkmatch.py  <board>.kicad_sch <board>.kicad_pcb
"D:/Program Files/bin/kicad-cli.exe" pcb drc --refill-zones --severity-all -o drc.rpt <board>.kicad_pcb
```

KiCad's DRC is the final arbiter, and `--refill-zones` matters on any board with a pour.
When you open a generated board in KiCad, press **B** to fill zones.

**Conventions that will bite you otherwise:**

* **KiCad grammar:** pads may carry `(net N "NAME")`; **segments and vias must be code-only
  `(net N)`** — the combined form is a parse error.
* **No rotation tokens.** `checkpcb.py` reads a bare `(at x y)`, so oriented parts use
  **pre-rotated footprint variants** (see `tools/mkfp_sec.py`, which generates them).
* **Wire-landing pads:** oversize pads and drills by about +0.2 mm wherever a bare tube lead
  or panel wire lands. The measurement sheets' pitch uncertainty is real.
* **High voltage is a clearance class:** 0.6 mm wherever an HV net is on either side of a
  gap (IPC-2221B B4 for 151–250 V is 0.4 mm under mask; 0.6 mm keeps 50 % margin). **And
  design to A6 = 0.8 mm between bare pads of different parts from the start** — on SEC six
  pad pairs ended at 0.61–0.78 mm and can only be fixed now by moving parts or conformal
  coating. The cathode bus K0..K9 is *not* HV: the К155ИД1 clamps near 60 V.
* **Fix the parser, not the file.** If a checker misreads a valid board, fix the checker and
  prove no regression against the finished boards.
* **Do not commit** unless the owner asks.
* **Long runs:** a full SEC route takes ~5 minutes. Run generators in the background writing
  to a log, and watch the log — a lost background run went unnoticed once.

## 9. Routing: what SEC learned the hard way

`tools/pcbroute.py` is an A* grid router (0.1 mm, two layers) with the clearance classes
above baked in. Two things in it matter more than the rest:

* **Negotiation beats ordering.** Routing nets one after another fences them in: whichever
  net arrives first takes the corridor. On SEC the 185 V feed cut the back face in two, and
  the cathode bus — routed early and then frozen — boxed the backlight LEDs into a pocket
  with no way out on either face. `negotiate()` routes a whole group at once in the manner of
  PathFinder: nets may overlap at a price, the price rises each round, and cells that stay
  contested get dearer permanently, until nothing overlaps. **Route the whole board in one
  negotiated group**, not in fixed stages, except genuinely local copper.
* **Pours do not reach into pockets.** GND as a pour alone left pads walled off on both
  faces — KiCad's own refilled DRC agreed. GND on SEC is *both* a routed tree grown from the
  logic connector *and* a pour on each face. Do the same, or give GND a plane (§7).

Two knobs worth knowing: `layer_cost` makes one face the second choice per step (useful if
you want a face kept clear for a plane), and `via_cost` defaults to 15 mm of track, so every
via the router places is a detour it could not find. Reading the via count as a map of where
the layout is too tight is more useful than trying to drive it to zero.

**For TS06-MAIN specifically:** the ten-line cathode bus now runs the length of the board
under the tube row instead of arriving through a connector. Lay it out as a deliberate spine
— straight, one face, fanning up into each tube's ring — and place the anode chains and the
18 AM/PM channels around it. Most of SEC's vias came from a bus that had to climb out of a
connector at one corner and reach two pin fields at the other.

## 10. Suggested phases

Each phase ends with something checked, not just drawn.

0. **Capture** (blocking): §6.1 the converter, §6.2 the ИН-12 pin functions, §6.5 the anode
   values. Write them into a new measurement sheet in the repo's style.
1. **Schematic** for TS06-MAIN, generated by a new `tools/mksch_main.py`, both builds sharing
   one netlist. `checksch.py` clean.
2. **Outline, tube placement and mechanics**: board outline, the eight tubes and the colon
   pair at the fixed coordinates, mounting holes, fascia connector, power entry. Check
   against `3d/Clock.FCStd`, and update the assembly.
3. **Placement of everything else**, in one pass, per build. `checkpcb.py` clean, and the
   A6 0.8 mm bare-pad rule satisfied by construction.
4. **Routing**, negotiated in one group. All checkers plus KiCad DRC clean.
5. **`preview.svg`, `PCB/README.md`, BOM deltas** (18 MPSA42, 2 MCP23017, 6 opto channels,
   the converter parts), and mark SEC/COLON superseded.
6. Repeat 3–5 for the second build.

## 11. Acceptance criteria

* Both builds: every net routed, `checkcopper.py --hv …` clean, `audit.py` clean,
  `checkmatch.py` clean, KiCad DRC clean at every severity with zones refilled.
* No HV pad pair between parts under 0.8 mm, and no HV conductor gap under 0.6 mm.
* The Nano pin map in §4 unchanged, or `firmware/` updated in the same change.
* One cable fits either build, as with the fascia.
* A clock is buildable from **two fabricated PCBs** and no inherited board.
