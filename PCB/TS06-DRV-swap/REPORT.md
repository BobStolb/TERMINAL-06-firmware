# TS06-DRV, swap layout: logic on top, power at the bottom

## Concept

The bands are turned round: the 12 V inlet, the 5 V regulator, the whole 185 V converter, J1 and the AM/PM anode resistors fill the bottom band, while the Nano stands on end at the top edge (USB out the top) with the MCP23017 straight under the two ИН-15 decoders. Nearly every logic line becomes short; what stays long is the opto/converter/backlight/fascia traffic down the middle and one lap for D12.

## Verdict: better on floor, port A and convergence; not simpler everywhere

- **Better:** routing floor −11 %; port A 889 mm of hand-laid bus → 98 mm; converged with zero vias in 12-15 negotiation rounds (~12 min per run; every variant I ran converged); hand-laid copper 322 segments / 2.5 m against the baseline's 369 / 3.3 m.
- **Not simpler:** D12 (the "m" LED) now laps the top and left edges (198 mm); the four fascia lines run 110 mm down the middle to J1; the LED ribbon is as long as the baseline's; the bottom band is full, so all 100 mm of height is still used; USB moves to the case's top face.

**Moderately better**, pending the coordinator's baseline numbers for track length and DRC.

## Scorecard

| Item | Swap | Baseline (my measurement, same method) |
|---|---|---|
| Converged | **yes**: 0 nets sharing, `B.check` 0 problems, mate clean | (coordinator) |
| Vias | **0** | 0 |
| Total track length | 5251 mm (GND tree 616, non-GND 4635) | (coordinator) |
| MST floor (`placecheck.py`) | **3780 mm** | 4268 mm (generator's pads, same MST) |
| Ratio track / floor | 1.23 (non-GND vs floor, which excludes GND); 1.39 including GND | – |
| Track segments | 1054 | – |
| Axis-aligned share of length | 79 % | – |
| Hand-laid segments | 322 (2520 mm) | 369 (3309 mm) |
| Distinct DIP pin-1 orientations | 3: left (U3, U11, U12, U15-U17), down (U2, RN1), right (the six optos) | 3 |
| Board height used | 100 mm (courtyards from -1.6, USB proud, to 100.0) | 100 mm |
| Tallest part | DS3231 module on U13, ≈21-22 mm, top band (70, 8-18) | same part, bottom band |
| USB | top edge, x ≈ 86-101, 1.6 mm proud | right edge |
| DC jack | right edge, bottom-right corner (y 88) | left edge, top |
| GND pour islands | 16 F.Cu, 13 B.Cu (each reaches a GND pad; the routed GND tree carries continuity) | – |
| KiCad 10 DRC (refill zones, HV class from the .kicad_pro) | **0 clearance, 0 unconnected**; 1 error `starved_thermal` (U1.29 GND, 1 spoke of 2, also tracked); warnings: 22 silk overlap, 2 silk/edge (USB overhang), 103 library-not-configured (container) | (coordinator) |

Other tall parts, all in the bottom band: VT21 TO-220 ≈19 mm (115-121, 95.5), C7 Ø10 16-20 mm (106, 78-84), L1 12-14 mm (121-126, 80.5). The Nano (≈15 mm) is in the top band. The DS3231 could lie flat on a right-angle header, as the review suggests.

Switching loop (drain → VD1 → C7 → source): 14.6 × 17 mm pad box, ≈248 mm², against the baseline's 19.9 × 13 mm, ≈259 mm². Comparable, not tighter. SW is 17 mm of copper.

## Key placement decisions

- **Nano: vertical, USB up**, at x 86-101 just right of U17 and XS12's end. The analogue column faces U17 and the digital column faces the cells.
  - Its pin-1 end puts the gaps between the idle TX/RX/RST pins level with U2's input gaps: A0/A1 leave east through them, A2/A3 under the module's end.
- **A0-A3 split at the Nano's pads:**
  - West branch on B.Cu: down the 5 mm gap between U17 and the module, into U17's inputs from below.
  - East branch on F.Cu: inside the module, up under H3 at y 33-35, down into U2's baseline input stubs.
  - Both hand-laid; neither crosses anything on its face.
- **U3 under U15/U16 (rot 90, pin 1 at 25.4, 59.0):** GPA7..GPA0 lie left-to-right in the order U16's then U15's inputs want: eight 45° lines on B.Cu, no remap.
- **RN1 at the left edge (x 9-17, y 65-83),** not under U3. There is no vertical room for decoder + fan + U3 + RN1 + ribbon above the bottom strips; I measured ~5 mm short.
  - Port B runs in lanes under U3 and drops between RN1's columns into its left column.
  - The right column feeds the LED ribbon under the bottom strips, as in the baseline but on **F.Cu**, so everything coming up from the bottom band crosses it on B.Cu.
- **Anode cells:** the baseline's cells over the bottom strips, with S turned to `cell_right` (away from U3).
  - The 185 V comes up from the converter through the strip-row gaps. It crosses the ribbon on B.Cu and changes face at the opto/ballast pads.
  - AM/PM anode resistors R56/R57 lie in the bottom band and rise into XS25 from below, so no 185 V goes near U3/RN1.
- **Where lines change face (all at pads of parts already in the circuit):**
  - D13 and D3 come down inside the module to their 470R hops (R25, R26) below it. The OPT lines then cross the J1 lines westwards on F.Cu.
  - D2/D4/D5/D6 end in standing 470R near the Nano's east side.
  - D9 ends in R66 east of the J1 lines, and PWM_G crosses them on F.Cu to the comparator.
  - A6/A7 change face at their ladder filters C5/C6 just above J1, to cross D7/D8 into J1's pin order.
- **J1:** bottom edge, back face, as in the baseline. A top-band J1 would save ~4 × 100 mm of track and the C5/C6 hop, but costs ~100 mm more cable that must leave the top of the stack and come round the display board to a fascia below the tubes. I judged that worse.
- **Mounting holes:** H5 (3.5, 96.5), H6 (172.5, 96.5), H7 (3.5, 14.0) moved below D12's corner, H8 (172.5, 3.5).

## Remaps (all firmware-only; `TS06_DRV_VARIANT=swap` in `tools/ts06pair.py`, off by default so the baseline netlist is unchanged)

| Remap | Swap | Baseline |
|---|---|---|
| Opto pins (`TUBE_PIN4`; the firmware `opts[]` for BOARD_TYPE 4 must follow) | H10 D6, H1 D5, **M10 D2, M1 D4, S10 D13, S1 D3** | M10 D4, M1 D3, S10 D2, S1 D13 |
| Port B → LED (`BL_OF_GPB`) | [8,7,6,5,4,3,2,1]: GPBk lights HL(8-k) | – |
| RN1 elements | GPBk on RN1 pin 9+k, its LED on pin 8-k | – |

- **All 470R opto resistors are the standing 2.54 mm footprint** (the baseline had H10/H1 lying). This is a footprint choice the brief allows.
- **Port A is unchanged:** `XA_IN` and `GLYPH_Q` are exactly as before.
- **Not touched:** J1's order, the RTC's order, the strip order, the A0-A3 → decoder mapping and the digit map.

## Remaining problems

1. `starved_thermal` on the Nano's GND pin 29 (connected by track; a pad-connection override would clear it).
2. **Fixed in the final routing:** the first converged run laid the 185 V spine along y 46-50, under U17's A0-A3 lanes and beside the 470R hops. `route()` now keeps HV nets out of the strip y 42-49.3 between the logic and the cells (a router keep-out that only HV nets see). The re-route converged in 15 rounds and came out shorter: HV185 is 227 mm instead of 253, total 5251 mm instead of 5276. No 185 V copper now rises above y 49.5, the colon ballasts' own pads. (`TS06_HVKO=0` routes without the keep-out.)
3. D12's 198 mm lap round the top and left edges. It is forced: D12 is fixed to the "m" LED, at XS25 on the far left, and its pin is at the Nano's east top.
4. 29 GND pour islands. Each touches a GND pad, but the pour is fragmented in the dense bottom band.
5. 22 silk overlaps in the crowded bottom band.
6. USB opening in the case's top face; all 100 mm of board height still used.
7. **Shared files:** `ts06pair.py` gained the variant switch (backward-compatible); `write_library` added rotated footprint copies under `PCB/lib/TS06.pretty/` (committed). `pcbkit.py` and `netroute.py` are unchanged.
8. **Baseline bug noticed:** `B.plot(color=lambda n: ... else None)` crashes in the current pcbkit; my generator returns a colour instead.

![copper](copper.png) — front face above, back face below (seen through). [placement.png](placement.png) shows parts and hand-laid copper.

## Reproduce

```sh
git checkout pcb/drv-alt-swap
pip install numpy scipy pillow
python3 tools/mkpcb_drv_swap.py --place     # placement.png only
python3 tools/mkpcb_drv_swap.py             # board from the saved routes (tools/mkpcb_drv_swap_routes.json)
python3 tools/mkpcb_drv_swap.py --route     # route afresh (~13 min, converges in round 15): NetRouter(turn45=6),
                                            # dirmul [1,1.5]*4, Negotiator(rounds=60), polish; reproduces the saved routes
TS06_ORDER=power TS06_HVKO=0 python3 tools/mkpcb_drv_swap.py --route   # power nets first: converged in 12 rounds
python3 tools/placecheck.py PCB/TS06-DRV-swap/TS06-DRV-swap.kicad_pcb
docker run --rm -v $PWD/PCB/TS06-DRV-swap:/w -w /w mirror.gcr.io/kicad/kicad:10.0 \
  kicad-cli pcb drc --refill-zones --severity-all --format json -o /w/drc.json /w/TS06-DRV-swap.kicad_pcb
```
