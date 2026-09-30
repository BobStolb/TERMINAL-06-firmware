# TS06-DRV-plane: an unbroken ground plane on the back, parts as bridges

## Concept

The back face (B.Cu) is one GND pour. Ground is never routed, and every other net lies on the front face. Where two front-face nets must cross, one passes between the pads of a part in series with the other (a lying resistor, a DIP's channel, an opto's channel). Back-face copper is allowed only inside "hop windows": within 3 mm of a pad of a circuit part, and never along the strips.

## Verdict: worse than the baseline, and not converged

* **The layout did not converge.**
  * The final snapshot (10 negotiation rounds) still has **69 nets sharing** copper.
  * Earlier runs went further but still stalled:
    * a 20-round run with a soft back-face price stopped at 23 nets sharing;
    * three 30-round window runs were killed by a container restart at round 12, all at 50–54 nets.
* **The collisions are structural** (listed below), so more rounds will not fix them. Only a different placement will.
* **The plane itself is the one clear win.** With hop windows, the back face is:
  * 21 islands, the largest holding **98.7 %** of the fill;
  * reaching **55 of 56** ground pads.
  * The baseline's back pour is 139 islands with the largest at 64 %; its front pour is 82 islands at 85 %.
* **But the hops are not short.** Windows chained along DIP and Nano pin rows allow runs of up to 71 mm, and 0.9 m of signal and power copper still sits on the back.
* **What remains useful:**
  * the bridge-row idea;
  * the plane checker (`tools/planecheck.py`);
  * the obstruction list below.

## Scorecard

| | plane (this, snapshot) | baseline (measured here) |
|---|---|---|
| converged | **no**: 69 nets sharing after 10 rounds | yes, round 16 |
| B.check | 202 problems (the sharing) | 7 (1 clearance, 6 router stubs) |
| vias | 0 | 0 |
| track length | 5673 mm (F 4776, B 897) | 6335 mm (F 2443, B 3892) |
| MST floor (placecheck.py) | **3935 mm** (ratio 1.44, meaningless unconverged) | 4265 mm (ratio 1.49) |
| segments | 2565 | 1060 |
| axis-aligned length | 88.7 % | 84.8 % |
| hand-laid segments | 0 | 369 |
| DIP pin-1 orientations | 3 (90/180/270) | 3 |
| board height used | 100 mm (full 176 × 100) | 100 mm |
| tallest part | U13 DS3231 standing, ≈ 21 mm, top band (128, 11) | same part, bottom band |
| USB / jack | right edge top / left edge top (as baseline) | same |
| GND islands, back face | **21**; largest 98.7 %; 1 GND pad off it | 139; largest 64 %; 19 GND pads off it |
| GND islands, front face | no front pour | 82; largest 85 % |
| B.Cu signal copper | 64 runs, 897 mm; longest 70.6 mm (+5V) | 3892 mm (two-layer design) |
| KiCad 10 DRC (`--refill-zones`) | 24 clearance, 95 tracks crossing, 9 shorting, 1 unconnected (U1.29 GND), 1 courtyard overlap (R26/H8) | 1 clearance, 0 unconnected |

Notes on the table:
* **DRC:** both boards also show 103 `lib_footprint_issues` (the project's library path inside docker) plus silkscreen notes. Neither is copper.
* **GND pad count:** my raster checker names U1.4 as the stray Nano ground pad; KiCad names U1.29. Either way, one Nano GND pin needs a front-face stub to the other.
* **Baseline numbers** come from a fresh `mkpcb_drv.py --route` run in a scratch copy. The committed `PCB/TS06-DRV/TS06-DRV.kicad_pcb` is stale: 34 parts, 44 vias.

## Key placement decisions

1. **The bridge row.** Every Nano output with a series resistor lies in one row of vertical 10.16 mm resistors directly under the digital row:
   * R21–R26 (opto), R66 (D9), R1 (D10), R20 (D11), R53 (D12);
   * R23–R26, R66, R1, R20 and R53 change from standing to lying 10.16 mm for this.

   The analogue side (A0–A3, I²C, A6/A7, 5 V) runs horizontally between their pads, under all the digital lines. This removed the whole hand-laid fan-out and corridor of the baseline, and it works.
2. **The 185 V feed runs through the optos' channels.** The optos stand LED row up and output row down, so the feed meets no 5 V line; the opto itself is the bridge.
3. **J1 moved to the top band, front face,** at the street's west end, at (108, 26.5).
   * In run v1 (J1 at the bottom) the bundle D7/D8/A6/A7 collided with B1, PWM_G, OPT_M10 and M_A. Those four lines have no series part, so they cannot bridge anything.
   * **Mechanical cost:** the fascia lead leaves the rear-facing side and must run round the board's bottom edge to the fascia, about 200 mm instead of 150 mm.
4. **Everything else keeps the baseline's positions:** the decoders under XS12, U2 beside XS11, the anode cells, the converter, the power entry, and U3/RN1 at the bottom left.

## Remaps

None. The circuit, pin maps and firmware are untouched. The only changes are footprint choices: the standing-to-lying resistors in decision 1, done in the generator and not in `ts06pair.py`.

## Obstructions: why F.Cu-only is not planar here

These are from the collision pairs of the snapshot, grouped by region, and from working the pinouts by hand.

1. **U2 against XS11 is a chirality problem.**
   * XS11 wants K6 K5 K7 K4 K8 K3 K9 K2 K0 K1 top to bottom: increasing pin numbers down the 9–16 column. No rotation of the К155ИД1 puts that column facing the strip in that order.
   * The workaround, threading the far column through the chip, leaves the four inputs and 5 V (pins 3–7, on the facing column) only 2 exits for 5 lines.
   * So U2 needs at least 3 crossings with no bridge part. The collision pairs show A0/A1 against K4–K7.
2. **Decoder 5 V (pin 5) sits between the input pins.**
   * Every decoder needs a 5 V hop, or an input threaded through its channel. For U17 the channel trick works on paper (A2 and A3 enter through the gaps at pins 6/5 and 7/6).
   * Collisions: +5V against XA0/4/6/7.
3. **Port A up the left edge against I²C and the LED ribbon.**
   * With U3 at the bottom left, SDA/SCL can reach its pins 12/13 only through the pocket fenced by the XA bus and BL_A8. This is the worst cluster: 22 pairs in the bottom-left, including BL_A1–A6 against XA1.
   * **Fix (not tried):** put U3 in the tube band directly under U15/U16. GPA7…0 are then already in the decoders' input order. Send port B down past XS25's left end to RN1.
4. **The AM/PM feed against port A.** HV185 must reach R57's far pad (x 14), inside the XA bus's turn into U16/U15 (HV185 against XA0–5).
5. **The A-bus branch to U17 against the S cell** (A0–A3 against OPT_S1/S10 and HV185): the bridge resistors sit too far east to span it.
6. **At U17, KS0/KS1 and KS8/KS9 need the channel swap** (one output dives into the chip's channel). The router did not find it; it would have to be hand-laid.

**A soft price on back-face copper does not work.** With HOP_COST = 3 or 8 and no windows (runs v1 and v2), negotiation pressure grows ×1.5 per round, so by round 20 the back face is cheap:

| run | B.Cu copper | islands | largest island | GND pads off it |
|---|---|---|---|---|
| v1 (HOP_COST 3) | 2.3 m | 85 | 56 % | 33 |
| v2 (HOP_COST 8) | 2.3 m | 153 | 45 % | 40 |

In this concept ground is not routed on the front, so every pad off the main island is an open circuit. Windows are the only mechanism of the two that kept the plane whole.

## Remaining problems

* Not converged: 69 nets sharing (above).
* R26's courtyard overlaps hole H8.
* One Nano GND pin is off the plane.
* The hop windows let hops chain along pin rows: the 71 mm +5V run, and 59 mm for D7/D8 under the Nano. The windows should be capped per hop, or limited to 2-terminal parts.
* J1's move has a mechanical cost (above).

## Files

* `tools/mkpcb_drv_plane.py`: the generator.
  * Hop windows are a subclass of `Negotiator` in the generator. The router settings are otherwise as specified; the polish is front-face only.
  * GND is excluded from routing.
* `tools/mkpcb_drv_plane_routes.json`: the 10-round snapshot.
* `tools/planecheck.py`: a raster zone-fill model. It reports islands, the largest share, stray GND pads, and back-face runs, plus `--score`.
* This folder: `TS06-DRV-plane.kicad_pcb`/`.kicad_pro`, `copper.png` (front above, back below) and `placement.png`.
* Shared tools are unchanged. `PCB/lib` gains rotated footprint variants, written by `write_library` as usual.

## Reproduce

```
pip install numpy scipy
python3 tools/mkpcb_drv_plane.py --place                    # placement.png, overlap and mate checks
ROUNDS=10 HOP_R=3.0 HOP_COST=3 python3 tools/mkpcb_drv_plane.py --route   # ~22 min; the snapshot
python3 tools/mkpcb_drv_plane.py                            # board from the saved routes
python3 tools/planecheck.py tools/mkpcb_drv_plane.py --score
python3 tools/planecheck.py tools/mkpcb_drv.py --score      # baseline B.Cu (after its own --route)
python3 tools/planecheck.py tools/mkpcb_drv.py --layer F.Cu
python3 tools/placecheck.py PCB/TS06-DRV-plane/TS06-DRV-plane.kicad_pcb
docker run --rm -v $PWD/PCB/TS06-DRV-plane:/w mirror.gcr.io/kicad/kicad:10.0 \
  sh -c 'cp -r /w /tmp/b && cd /tmp/b && kicad-cli pcb drc --refill-zones -o drc.rpt TS06-DRV-plane.kicad_pcb; cat drc.rpt'
```
