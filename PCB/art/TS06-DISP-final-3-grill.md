# TS06 display disp-3-4: the grill (can it be built, will it work)

2026-10-15, run grill-disp34. The owner (00:0x UTC): "run grills on all, compile insights for the final pcb routing plan".
disp-3-4 is a final candidate, not approved: the lintel over the squared arch, F3 split in two 60 flex in green. The owner's
note on it: "color of the paricular glyphs might change". The face is [TS06-DISP-final-3.md](TS06-DISP-final-3.md) section 5
(last subsection) and section 6 (D1 to D10, E1 to E4, G1 to G6). This page reviews it and proposes fixes. It applies none: no
board, schematic, fab, tool, 3D, firmware or spec file was touched, and the face and its write-up are unchanged. The scripts are
scratch, not in the repo.

Marks:
* *measured*: read from a repo file (board, schematic, BOM, case model), or computed on it by my own scripts;
* *inferred*: arithmetic on measured numbers;
* *assumed*: my reading, or a value nobody has measured.

**Frame:** DISP's own KiCad frame. Origin at the board's top-left corner, x to the right, y down, mm. DRV numbers are in DRV's own
frame (DRV x = 191.4 - DISP x, DRV y = DISP y + 26.0, TS06-DISP-final item 13).

**How I checked the copper:** my own reader of `PCB/TS06-DISP/TS06-DISP.kicad_pcb` (189 pads, 388 tracks). I took the face run's
slots, holes and routed tracks (its router's paths), removed what the change list removes (HL1 to HL8, every BL_A track, the old
ANODE_H1 run, M_A), moved HL9 3.0 down (V3b), and measured every new slot, hole and track against every pad and track that
stays. Slot pad: 1.8 x 3.3, long axis across the filament (pass 2's model). Rules: `TS06-DISP.kicad_pro` and `.kicad_dru`
(HV class `ANODE_*`, `COLON_*`: 0.6, and 0.8 to an HV pad; CATH class `K0` to `K9`, `KS*`, `CAT_*`: 0.25; default 0.2; pass 2
used 0.25 for slots).

## Verdict

**Buildable after changes. Not on the ordered DISP rev B** (it has none of the light slots: a DISP rev C, a DRV rev C and a case
change are needed). The copper is sound: every new slot, hole and track keeps the 185 V rules. Four things would stop it working
as written:

* **The lintel's driven end lies on P's return pad and on gold** (finding 7): the lintel would short and never light. This is
  the one blocker. The fix is cheap.
* **The drive in the plan cannot work on DISP** (finding 2): per-line low-side N-FETs, but every DISP line returns on one
  common-cathode pour.
* **The colon floor's name "K3" is already a cathode net on DISP** (finding 8).
* **The case sill 1.1 lower shows the strip-pin joints** from 19 to 52 degrees above, the usual desk view (finding 10).

| # | Item | Rating |
|---|---|---|
| 1 | Every light, end to end | OK (inventory) |
| 2 | The drive: common-cathode pour against per-line N-FETs | Needs X |
| 3 | Channels: 19 or 15; (a) colour groups or (b) a second chip; HL9 loses its dimming | Needs X |
| 4 | Q1 and Q2: one wire, two resistors; the harness | Needs X |
| 5 | F3's halves and the lintel: XP12.12 and XP12.13 on both boards | Needs X |
| 6 | Every slot, hole and track against tube pads, strips, tracks and 185 V | OK (two at the rule) |
| 7 | The lintel's right end cap on P's return pad and on gold | **Blocker** as drawn |
| 8 | K3's name is a cathode net on DISP | Needs X |
| 9 | Holding the face lines; the back of DISP | Needs X |
| 10 | The case sill 1.1 lower | Needs X |
| 11 | Fab: slots, the split pad, round holes | OK |
| 12 | Light: 20 mA a filament is not one brightness | Needs X |
| 13 | Light: bleed, hot spots, colours by day | OK |
| 14 | A glyph's colour changes later (the owner's note) | Needs X (a decision) |
| 15 | The path to a board | Needs X |

**K4W411's grill, what applies here:**
* K4W411 #1 applies (DRV has no PWM chip and no free output; check the RTC module's I2C addresses).
* K4W411 #2 applies: lines that share a channel each keep their own resistor.
* K4W411 #16 applies to the art: emit DISP's art from the face scripts' vectors, then re-run the checks. Here the gold keeps 0.67
  to 185 V tracks against a 0.6 rule: under two raster pixels (0.043 mm each).
* K4W411 #4, #5, #6, #10 and #13 do not apply. DISP has no bare-FR4 window and no control body; its lines are seen directly, not
  through FR4.

## 1. Light sources and connection, end to end

### Finding 1. Every light on disp-3-4 (OK, as an inventory)

Fourteen filaments, plus the existing "m" LED HL9 and the eight RGB LEDs. Flex lines sit in plated slots, rigid bars in round
holes; the slot or hole called "driven" is the anode (DRV sheet 10: BL_A feeds the anodes, BL_K is the common cathode,
*measured*).

| Line | Sold part, colour | Held by | Driven end | Return | To DRV | Default |
|---|---|---|---|---|---|---|
| H, hours bracket | 95 flex, warm | slots; the shim's channel (inlay) | (39.48, 30.40) BL_A1, F.Cu 27.1 | (39.48, 5.27) BL_K | XP21.2 | on |
| M, minutes bracket | 95 flex, warm | the same | (61.10, 30.40) BL_A3, 14.3 | (61.10, 5.27) BL_K | XP23.1 | on |
| P, AM/PM box | 95 flex, warm | the same | (151.86, 30.40) BL_A7, 12.0 | (138.40, 5.27) BL_K | XP25.1 | on |
| F, the long line | 185 flex, warm | slots only (finding 9) | (181.81, 34.0) BL_A8, 17.6 | (2.80, 34.0) BL_K | XP25.6 | on |
| S, squared arch | 60 flex, warm | slots only | (139.57, 18.92) BL_A6, 31.0 | (98.20, 18.92) BL_K | XP24.4 | on |
| Q1, Q2, colon bars | 26 rigid each, warm | the shim | wires through H1's and M10's 5.0 centre holes | a return wire | harness | on |
| F2L | 60 flex, pink | slots only | (37.305, 36.40) BL_A2, 17.2 | shared pad (92.305, 36.40) BL_K | XP21.5 | off |
| F2R | 60 flex, blue | slots only | (147.305, 36.40) BL_A9, 17.2 | the shared pad | XP25.3 (spare today) | off |
| F3L | 60 flex, green | slots only | (89.255, 38.80) BL_A4, 13.4 | (35.255, 38.80) BL_K | XP23.4 | off |
| F3R | 60 flex, green | slots only | (149.355, 38.80) BL_A11, B.Cu 42.9 | (95.355, 38.80) BL_K | XP12.13 (spare today) | off |
| K3, colon floor | 18.5 rigid, pink | two holes; the shim's channel | (58.285, 31.60), a harness wire | (42.785, 31.60) BL_K | harness | off |
| S2, inner arch | 60 flex, blue | slots only | (100.60, 22.69) BL_A5, 24.9 | (137.17, 22.69) BL_K | XP24.1 | off |
| S3, lintel | 38 rigid, green | two holes | (136.385, 6.60) BL_A10, 4.9 | (101.385, 6.60) BL_K | XP12.12 (spare today) | off |
| HL9, the "m" | existing 3 mm LED | its pads, moved 3.0 down (V3b) | M_A (162.17, 38.50) | BL_K (159.63, 38.50) | XP25.4; D12 via R53 220R | on |
| 8 RGB LEDs | addressable 5 mm, diffused | a printed carrier behind DISP | DATA from D11 | 5 V, GND | harness, 3 wires | off |

All coordinates and lengths are the face run's (*measured* there); I re-measured the copper (finding 6). Return pins: all
lines on the pour leave by XP21.1 (BL_K): 12 filaments and HL9, about 255 mA at 20 mA a filament (*inferred*), well inside a
2.54 strip pin.

### Finding 2. The drive: a common-cathode pour against per-line N-FETs (Needs X)

**What the repo says** (*measured*):
* DRV sheet 10's note: all nine cathodes share BL_K behind one NPN switch (VT20), and BL_A1 to BL_A8 feed the
  anodes from the port expander through RN1.
* On DISP every line's return slot or hole sits on the one BL_K pour (F.Cu zone, net BL_K).
* The plan for DRV puts **one N-FET per channel** (front-merge item 8, TS06-DISP-final item 12, final-3 D9 and G5). K4W411's
  grill wires the fascia that way too: a common anode +5V_L, and each channel's cathodes to a low-side N-FET.

**The problem** (*inferred*): a low-side N-FET switches a cathode. On DISP all the cathodes are one net, so per-line N-FETs
there would switch nothing apart. As written, the DRV rev C design cannot drive DISP's lines one at a time.

**Fix, pick one before DRV rev C is drawn:**
* **(1) High-side P-FETs, my pick.** One logic-level P-FET per channel, source at +5 V, drain to that channel's 120 R resistors
  and BL_A lines. Tie BL_K to GND on DRV; VT20 and RN1 go.
  * The PWM chip's outputs run inverted (a configuration bit of the part type, *assumed*). Add a pull-up on each gate, or hold
    the chip's output-enable high until it is set up, so the lights stay off at reset.
  * Nothing changes on DISP: HL9 and every filament keep their polarity, and the exposed gold on the face stays at 0 V.
* **(2) N-FETs, with the pour turned into the common anode.** BL_K becomes +5 V on DRV. Every DISP filament goes in reversed,
  and HL9 must be turned round (its cathode is on BL_K today). The pour, its gold art and the shared split pad then sit at +5 V
  on the face: a slip onto GND shorts the 5 V module.
* **One type for both boards.** The fascia can use (1) as well: its lines' anodes per channel, its cathodes to a common return
  wire, the mirror of K4W411 #3. The routing plan should pick one FET type for DISP and fascia.

**Cost:** none in parts (a P-FET for an N-FET). One decision.

### Finding 3. Channels: 19 or 15, (a) or (b), and HL9 (Needs X)

**The count** (*inferred* from section 4 of the face's write-up, checked line by line against finding 1):

| | DISP | Fascia (6; K4W411 needs 5) | Total | One 16-channel chip? |
|---|---|---|---|---|
| One channel per line | 13: H, Q (Q1 + Q2), M, S, P, F; F2L, F2R, F3L, F3R, K3, S2, S3 | 6 | **19** (18 with K4W411) | no |
| (a) One per colour group | 9: the six warm; Rose = F2L + K3, Ice = F2R + S2, Green = F3L + F3R + S3 | 6 | **15** (14) | yes, 1 spare |
| (b) A second chip, the same part, the next I2C address | 13 | 6 | 19 of 32 | two chips |

**HL9, new:** the "m" LED runs from D12 through R53 with its cathode on BL_K, and VT20 on D11's PWM dims all nine
(*measured*: sheet 10). The plan frees D11 for the RGB chain and drops VT20. Then HL9 has no dimming: at night it stays at full
brightness beside dimmed lines (*inferred*). Fix: put M_A on a PWM channel (the chip's output through R53 can drive one small
LED, *assumed* for the part type, or a FET like the others). With (a) that is the last of 16; with (b) 20 of 32. Or software PWM
on D12 from the multiplex interrupt (no part, firmware only).

**Per FET** (*inferred*, 20 mA a filament): one line 20 mA; Q 40 mA; Rose and Ice 40 mA; Green 60 mA.

**My pick: (b), with the owner's note in mind** (finding 14). With (a), a colour change is a DRV wiring change; with (b) it is a
purchase and a firmware table. (b) costs one chip, one 100 nF capacitor, one address strap and 4 or 5 FETs more, no MCU pin. Take
(a) only if the owner fixes the colours now.

### Finding 4. Q1 and Q2: one wire, two resistors; the harness (Needs X)

* TS06-DISP-final item 12 gives "Q1 and Q2 one each" (two 120 R on DRV), but item 11 and final-3 D8 give the colon **one** drive
  wire, "Q drive, Q return" (*measured*, in the two write-ups).
* Two resistors need two drive wires. One wire means Q1 and Q2 in parallel on one resistor, which K4W411 #2 rejects (the bar
  with the lower forward voltage takes more of the current).
* **Fix:** 3 colon wires (Q1 drive, Q2 drive, return). The harness becomes **7 wires**: LED 5 V, GND, DATA; Q1, Q2, the colon
  return; K3's drive. With finding 2's fix (1), the colon return is GND and could share the LED GND wire: then 6.
* **Where the harness lands on DRV** is not placed by any write-up: a 6 or 7 way header on DRV, with room not checked.
  The DISP to DRV gap is 11.0 (*inferred* in pass 2), and the joints, the LED carrier and the harness share it.

### Finding 5. F3's halves and the lintel: XP12.12 and XP12.13 on both boards (Needs X)

**On DISP: OK.**
* F3L on BL_A4 (XP23.4) is 13.4 mm on B.Cu. Its nearest 185 V copper is XP23.3 (ANODE_M1) at 1.54, against a rule of 0.8
  (*measured*).
* F3R on XP12.13 is 42.9 mm on B.Cu, down the right of the seconds. Its nearest 185 V copper is 7.09 away. But it passes four
  copper items at the limit (*measured*):
  * P's return slot: 0.25 (pass 2's slot rule 0.25; KiCad's default 0.2);
  * F2R's driven slot: 0.26;
  * S's driven slot: 0.27;
  * the CAT_B_AMP track: 0.33 (rule 0.25).
  It passes, but the router held it on a 0.1 grid: KiCad's DRC decides.
* XP12.11, 12 and 13 have no net on DISP, and XS12.11, 12 and 13 have none on DRV (*measured*, both board files).

**On DRV: not checked by anyone.**
* XS12.12 and XS12.13 sit in DRV's **top** strip, at (56.11, 28.2) and (53.57, 28.2). Every other light line meets DRV at the
  bottom strips (y 67.3), and RN1, the backlight's part today, is at x 26.7 to 44.5, y 74.4 to 82.0 (*measured*).
* So BL_A10 and BL_A11 need about 45 to 50 mm of DRV track to wherever the PWM block goes, through a full through-hole board
  (*inferred*). The PWM chip's place should be chosen with these two in view.

**Only if option (a) is taken and F3's two halves stay one colour forever:** F3R could take its drive from BL_A4 on DISP, from
its inner slot, with one resistor per half on DISP's back. That frees XP12.13 and the 42.9 mm route. It is not routed, and it
ties F3R to F3L for good, so I do not propose it now.

### Finding 6. Every slot, hole and track against the copper and the 185 V rules (OK, two at the rule)

Worst margin of each new slot or hole (*measured*: my check, frame above; "rule" is the one for that pair):

| Slot or hole | Net | Nearest other-net copper | Nearest 185 V copper (rule 0.6 track / 0.8 pad) |
|---|---|---|---|
| H driven (39.48, 30.40) | BL_A1 | ANODE_H1 (D6) track 1.09 | the same, 1.09 |
| H return (39.48, 5.27) | BL_K | K6 track 0.44 (0.25) | 7.45 |
| M driven (61.10, 30.40) | BL_A3 | K3's driven hole 1.05 | 5.83 |
| P driven (151.86, 30.40) | BL_A7 | ANODE_AM track 1.48 | 1.48 |
| P return (138.40, 5.27) | BL_K | BL_A11 track 0.25 (0.25); S3's hole 0.30 | 15.2 |
| F driven (181.81, 34.0) / return (2.80, 34.0) | | ANODE_PM track 5.63 / standoff hole H1 3.31 | 5.63 / 13.2 |
| S driven (139.57, 18.92) | BL_A6 | BL_A11 track 0.27 | 4.42 |
| S2 driven (100.60, 22.69) | BL_A5 | KS7 track 0.55 (0.25) | 7.16 |
| S2 return (137.17, 22.69) | BL_K | BL_A6 track 0.27 | ANODE_S1 track 1.26 |
| S3 holes (136.385 / 101.385, 6.60) | BL_A10 / BL_K | P's return slot 0.30 / KS7 track 1.07 | 14.1 / 16.4 |
| K3 holes (58.285 / 42.785, 31.60) | K3's wire / BL_K | M's slot 1.05 / H's slot 1.54 | COLON_RET 4.60 / COLON_U 3.60 |
| F2L driven (37.305, 36.40) | BL_A2 | F3L's return slot 0.44 | 5.80 |
| F2's shared pad (92.305, 36.40) | BL_K | F3L's driven slot 0.44 | ANODE_M1 track 3.20 |
| F2R driven (147.305, 36.40) | BL_A9 | BL_A11 track 0.26 | 7.21 |
| F3L driven / return | BL_A4 / BL_K | F2's pad 0.44 / BL_A2 track 0.27 | 5.60 / 7.79 |
| F3R driven / return | BL_A11 / BL_K | BL_A9 track 0.27 / 4.30 | 6.18 / 6.71 |

New tracks, nearest 185 V copper (*measured*):
* ANODE_H1 (D6, itself 185 V): 0.74 to V2.8 (a pad with no net; the HV track rule 0.6), 0.84 to XP21.5, 1.54 to XP21.3.
* **BL_A9 (F2R): 0.80 to XP25.2 (ANODE_AM, pad rule 0.8): no margin.** It runs at y 43.1, between that pad and the board edge
  (0.75 to the edge, rule 0.5). Fix: move the run to y 43.2. Then it is 0.90 to the pad and 0.65 to the edge (*inferred*).
* **BL_A6 (S): 0.61 to the ANODE_S1 track (rule 0.6): 0.01 margin.** Fix: one 0.1 nudge where DRC shows it.
* BL_A7 (P): 0.75 to ANODE_AM. BL_A3, BL_A4 and BL_A8: 1.49 to 1.54 to strip pads. BL_A11: 7.09. BL_A10: 14.8.

**Bodies** (the face run's checks, *measured* there): 2.0 body; 0.4 line to line everywhere (2.4 pitch). To pin pads: F3 9.98
and 10.02, S3 8.54, K3 4.02. To other pads: F3 0.65 to XP23.1 and XP24.1 (rule 0.3), K3 1.50 to V8, S3 2.55 to XP12.

**Not a problem:** S2's crown runs 0.30 inside the raised ИН-17 glass outline (front view). The glass stands 7.8 mm off the board
and S2 stays 8.0 or more from the tube axis, outside the lead circle (r 3.2). The face run's "ИН-17 stem" flag is a 20 mm circle
round each axis, not a part.

## 2. Mechanics

### Finding 7. The lintel's right end cap on P's return pad and on gold (Blocker as drawn)

The drawing's own model (*assumed* in the face run, from front-merge's Q): the 38 rigid bar's holes are 35.0 apart, so 1.5 mm
of bar, its metal end cap, lies past each hole.

At the right end (*measured* on the drawing's geometry and its art raster):
* The bar ends at x 137.885. P's return slot pad (BL_K) starts at x 137.5, so the cap lies 0.17 to 0.39 mm onto it, on the
  solder of P's tab. P's slot hole edge is 0.015 from the bar's end.
* An exposed gold patch of the art (BL_K) lies under the same cap (x 137.35 to 138.35, y 7.09 to 8.13), 0.5 mm deep.
* The right hole is S3's **driven** end (BL_A10). So the cap shorts the lintel's anode to its own return, and the lintel never
  lights (*inferred*; through 120 R, so nothing burns).

The left end is the return (BL_K), on the A4 gold dummy pad: same net, harmless as drawn.

**Fix:**
1. **Bench check first:** one 38 and one 18.5 rigid bar. Measure the lead form (round or flat), the length, where it leaves the
   cap, and whether it bends without cracking the substrate. The 35.0 and 15.5 pitches are guesses.
2. **Swap the lintel's ends** (my pick). Put the right hole on BL_K, the same net as P's return pad and the gold, so the overlap
   is harmless. Drive the left hole.
   * Route BL_A10 from XP12.12 up to the band above XP12's pads (y 0.9), left under the valance, then down to (101.385, 6.60),
     about 40 mm on B.Cu. The face run's router found this corridor for another net (75.6 mm, *measured* there). Mine is
     *inferred*, not routed.
   * Then trim the gold dummy pad A4 and any gold within 0.3 of the left cap: the left cap would lie 1.0 deep in gold
     (*measured*). That is an art change only.
3. Or keep the polarity and insulate the right cap with a polyimide dot, and cut the gold back. It is cheap, but an assembly step
   decides it.

Shifting the bar left would break the exact symmetry. Dropping the lintel below P's pad would push S2's corners under R 6.

### Finding 8. K3's name is a cathode net on DISP (Needs X)

* `TS06-DISP.kicad_pcb` already has a net **K3**: cathode 3 of the ИН-12s, in the CATH class (pattern `K3` in
  `TS06-DISP.kicad_pro`; 6 uses, *measured*).
* If the board-change run names the colon floor's driven hole "K3", KiCad joins it to that cathode line. The 5 V floor would be
  wired to a cathode that sits near 185 V class when off (*inferred*).
* **Fix:** call the bar CF (colon floor) and its net BL_A12, in the board, the harness and the firmware. Cost: none.
* The face run's own scripts used BL_K3 internally. That is safe, but easy to misread as BL_K.

### Finding 9. Holding the face lines; the back of DISP (Needs X)

**The face lines are held only by their ends** (*inferred*: no write-up says how). F, F2L, F2R, F3L, F3R, S, S2 and the face
parts of H, M and P lie on the face outside the shim.
* A 50 mm flex span held only at two tabs will bow or droop. On an upright board it droops downward, toward the next line,
  which is only 0.4 away (F, F2, F3 at a 2.4 pitch).
* S's and S2's corners (R 8.4 and R 6.0) will spring open without help.
* **Fix:** a printed placing jig on the slots. Clear neutral-cure silicone dots under each body every 15 mm or so, cured in
  the jig (*assumed*). Or a thin printed retainer with combs, if the case allows it. Cost: one jig, a tube of silicone.
* The rigid bars hold themselves by their leads (K3 also in its shim channel, D7).

**The back of DISP** (the 11.0 gap to DRV, *inferred* in pass 2):
* There are 24 slot and hole joints (20 slots, 4 round holes). The new ones are at y 31.6 to 38.8 (F2, F3, K3) and y 6.6 to 22.7 (S, S2, S3). Each has a
  lead tail.
* The LED carrier (TS06-DISP-final 3a) is not drawn yet. It must keep clear of every one of them, of the F3R track's area (only
  under the mask: no clash), and of the harness.
* The nearest new joints to an LED pocket are S2's slots, 8.0 from the ИН-17 axes (*measured*). The pockets are about r 3.5 (*assumed*: the LED's r 2.9 flange and a wall).
  Room, if the carrier is drawn round them.
* Cut every lead tail to 1.5 or less, as the case model assumes (`PIN_TAIL`).
* Nothing on DISP is near K4W411 #5's button boxes: those are behind the fascia.

### Finding 10. The case sill 1.1 lower (Needs X)

I ran `3d/case-pair/case_pair.py` in memory with `SILL_TOP_Y` 39.0 and then 37.9 (world Y, the same as board y 39.0 and 40.1),
everything else as in the repo (*measured*; it wrote nothing).

* **The strip-pin joints show.** The case's row 5 "XP21-25 joints behind the sill" goes from "hidden from every angle within
  ±60°" to **"seen from +19.3° to +52.0°"** (from above). That is where a desk clock is seen from. The rays pass between the
  sill's back edge and the pin tails (the case keeps 2.5 off DISP's face).
* **It breaks the case's own note.** `params.scad` says the sill top must be at least 38 ("review: >= 38") to hide the pads.
  37.9 is under it.
* **The fascia moves too.** In the model the fascia hangs from the sill's front edge, so it drops 1.1 with it. SW5's top goes
  from Y 33.16 to 32.06, and the fascia plug from 23.5 to 24.6 under DISP. Every other row keeps its status, except the sill's gap to the old HL5 and HL6 flanges, which gets better
  (those LEDs go anyway). "Case only" holds:
  no board changes. But it is not only the sill.
* **How much drop F3 needs** (the same model, the view at x 92.3, F3's lowest edge at y 39.8):

| Sill lower by | F3's lowest edge seen from | Strip joints seen from | The case note (>= 38) |
|---|---|---|---|
| 0 (today) | never (its lower 0.8 is always hidden) | never | kept |
| 0.6 | +21.9° | +40.4° | kept |
| **0.8** | **+0.1° (level and above)** | **+33.1°** | **kept** |
| 1.1 (the face run's B4) | -0.5° | +19.3° | broken |

**Fix:** lower the sill **0.8, not 1.1**. F3 then shows whole from level and above, and the case note holds. Also blacken the 22
strip-pin joints of XP21 to XP25 with a paint marker, for views above 33°. Trimming the tails does not help: a shorter tail
moves the joint further from the sill's back edge, and it shows from a lower angle (*inferred*). Cost: a number in `params.scad`, and the bench look.

## 3. Fab

### Finding 11. Slots, the split pad, round holes (OK)

* The slots are plated, 1.0 x 2.5: 20 of them. F2's two inner slots share one 3.8 x 3.3 pad, with a 1.0 web between their
  holes. There are 4 round holes, 1.0 drill and 1.8 pad (*assumed*).
* Hole to hole is 1.05 or more. F3L's driven slot to F2's pad is 0.44. These meet the board's own minimums (hole to hole 0.25,
  hole clearance 0.25; *measured*, `TS06-DISP.kicad_pro`).
* The order notes must ask for plated slots. The ordered DISP rev B has none of these (*measured*: `fab/ORDER.md` lists rev B as
  ordered).
* Gold, silk and mask: the face run's checks, gold 0.67 / 0.84 to 185 V (0.6 / 0.8), white to gold 0.22. These are raster
  numbers; K4W411 #16 applies (re-check on the vectors).
* The art must yield round each rigid bar's **end caps**, not only round its holes (finding 7). D10 names slots and holes
  only.

## 4. Light quality

### Finding 12. 20 mA a filament is not one brightness (Needs X)

* Every sold filament is "3 V DC", from 38 mm flex to 460 mm (front-merge section 5, listing data). One voltage for every length
  means the LED chips are in parallel along each line. So a line's current spreads over its length, and **brightness per mm goes
  as mA per lit mm** (*inferred*).
* Lit length (*inferred*: flex L - 10 for the two 5.0 tabs, rigid L - 3), and mA per lit mm at 20 mA:
  * F: 175 mm, **0.11**;
  * H, M, P: 85 mm, 0.24;
  * S, S2, F2L, F2R, F3L, F3R: 50 mm, 0.40;
  * S3: 35 mm, 0.57;
  * Q1, Q2: 23 mm, 0.87;
  * K3: 15.5 mm, **1.29**.
* That is an **11 to 1 spread** at one current. The warm long line F would be the dimmest line on the board, under green and
  pink lines three or four times brighter per mm. K3 would glare beside F2L in the same Rose group.
* **Fix:** size each line's resistor for one look, not one current, and let the bench set it.
  * To match the 60 flex at 20 mA: F 70 mA, H, M and P 34 mA each, S3 14, Q1 and Q2 9 each, K3 6. The DISP filaments then draw
    330 mA, not 280.
  * The 5 V worst case becomes **922 mA, 92 %** (730 mA, 73 % with the LED cap; *inferred* on the face run's 872 / 680). The
    LED cap is then a must.
  * F at 70 mA passes 70 mA through one FET and strip pin: fine.
  * **Bench check:** a 60 flex and the 185 at 20 mA side by side. Then set the resistor table.
* This applies to the fascia as well (38 flex arcs beside 18.5 bars). It is left to the routing plan.

### Finding 13. Bleed, hot spots, colours by day (OK)

* **Bleed:** the lines are seen directly, 2.0 wide with 0.4 dark between them. At 2.4 pitch they stay apart to the eye at a
  metre (8 arc minutes, *inferred*). Green under blue under warm reads as three lines.
* **Hot spots:** none at the lines. The tabs and caps are dark metal, and every window of light is a body.
* **The gaps:** F2's centre gap is 6.0 and F3's 10.1. The green ends run 2.05 past F2's at both outer ends. Each lit end loses
  its dark length too (K4W411 #8's bench check).
* **By day** (*assumed*): an unlit filament is pale silicone (yellow for warm, milky for colours), not the dark brown the
  drawing shows for "off". In the warm default the seven colour lines show as pale strips on the black face. **Bench check:**
  one coloured flex, unlit, by daylight. Decide whether that is wanted before the order.
* **Rigid against flex:** S3 (rigid) above S and S2 (flex), and K3 (rigid) beside F2L (flex). They may differ in tint and in how
  they spread light. The bench decides; finding 12's resistor table is the trim.

### Finding 14. A glyph's colour changes later (the owner's note) (Needs X: a decision)

What a later colour change costs (*inferred*):

| Change | DISP copper | DRV | Firmware |
|---|---|---|---|
| A flex line to another sold flex colour (yellow, red, green, blue, pink, white) | none | its resistor, if the new colour's forward voltage differs (red and yellow about 0.8 to 1.0 V lower, *assumed*: about 24 mA instead of 17 at 120 R) | the colour table |
| A rigid bar (K3, S3) to another sold bar colour (warm white, white, red, green, blue, pink) | none | the same | the same |
| A colour not sold (orange, purple) | no | | |
| S3 as flex instead of rigid | no: a 38 flex on the face puts its slots in the KS fan (the face run's search) | | |
| **Under (a)**, a line leaves its colour group | none | **re-wire the line to another group's FET**, or a 4th group: 16 channels, 17 with HL9, so a second chip anyway | the groups |
| **Under (b)** | none | none | the table |

**Fix:** choose (b), or (a) with a solder jumper per line to pick its group FET. Use through-hole resistors in a socket strip
where a colour may change. Cost: (b) as in finding 3; or 13 jumpers.

## 5. The path to a board

### Finding 15. What the board-change run must do (Needs X)

1. **DISP rev C** from rev B's file. Rev B is ordered and has none of this.
   * The 20 slots, the shared pad and the 4 holes (D1, D5, E1, E2, G1).
   * The tracks D2 to D4, D6, E1, E2, G2 to G4.
   * BL_A9 at y 43.2 (finding 6); BL_A10 from the left if finding 7's swap is taken.
   * HL9 3.0 down (V3b); HL1 to HL8 removed.
   * Name the floor's net BL_A12 (finding 8).
   * The art from vectors, yielding round the bars' end caps.
   * Then KiCad DRC with the HV rules, `verify_pair` against DRV rev C, and `tools/dfm_check.py` on the zip.
2. **DRV rev C:**
   * the PWM chip or chips by finding 3;
   * P-FETs by finding 2 (or the pour to +5 V);
   * 14 resistors for DISP, sized by finding 12;
   * BL_K to GND; VT20 and RN1 out;
   * M_A onto a channel;
   * the mates of XS12.12, XS12.13 and XS25.3;
   * a 6 or 7 way harness header.
   The room is not checked.
3. **Shim:** Q1 and Q2 1.0 higher, a channel for K3 (D7).
4. **LED carrier:** drawn round the 24 joints (finding 9).
5. **Harness:** 7 wires (finding 4).
6. **Case:** the sill 0.8 lower (finding 10).
7. **Jig:** for placing and gluing the face lines (finding 9).

## Routing needs

Frame: DISP's own (origin top-left, y down, mm). Slots and holes are plated through, so "PTH" (both layers). Pad A is the
driven end (the anode); pad B the return on the BL_K pour. Proposed channels: **(b)**, chip 1 for DISP; (a)'s group in brackets.

| id | face | board | source (form, sold length, colour) | pad A (x, y, layer) | pad B (x, y, layer) | mA | shares with | proposed channel | connector pin | conflicts (copper, parts, 185 V, case) | evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| D-H | disp-3-4 | DISP | flex 95, warm | (39.48, 30.40) PTH; BL_A1 F.Cu | (39.48, 5.27) PTH | 20 (34 for the look) | none | 1.1 (a: own) | XP21.2 | 1.09 to ANODE_H1 D6 (0.6) | measured |
| D-M | disp-3-4 | DISP | flex 95, warm | (61.10, 30.40) PTH; BL_A3 B.Cu | (61.10, 5.27) PTH | 20 (34) | none | 1.2 (own) | XP23.1 | 1.05 to K3's hole | measured |
| D-P | disp-3-4 | DISP | flex 95, warm | (151.86, 30.40) PTH; BL_A7 | (138.40, 5.27) PTH | 20 (34) | none | 1.3 (own) | XP25.1 | return pad 0.25 to BL_A11, 0.30 to S3; under S3's cap (#7) | measured |
| D-F | disp-3-4 | DISP | flex 185, warm | (181.81, 34.0) PTH; BL_A8 | (2.80, 34.0) PTH | 20 (70) | none | 1.4 (own) | XP25.6 | 1.49 to XP25.5 ANODE_PM (0.8) | measured |
| D-S | disp-3-4 | DISP | flex 60, warm | (139.57, 18.92) PTH; BL_A6 | (98.20, 18.92) PTH | 20 | none | 1.5 (own) | XP24.4 | BL_A6 0.61 to ANODE_S1 (0.6); slot 0.27 to BL_A11 | measured |
| D-Q | disp-3-4 | shim | 2 x rigid 26, warm | Q1, Q2: wires via H1's and M10's 5.0 holes | a return wire | 2 x 20 (2 x 9) | Q1 + Q2 | 1.6 (own) | harness, 3 wires | one wire, two resistors (#4) | inferred |
| D-F2L | disp-3-4 | DISP | flex 60, pink | (37.305, 36.40) PTH; BL_A2 | (92.305, 36.40) shared pad PTH | 20 | (a) K3 | 1.7 (Rose) | XP21.5 | 0.44 to F3L's return | measured |
| D-F2R | disp-3-4 | DISP | flex 60, blue | (147.305, 36.40) PTH; BL_A9 | (92.305, 36.40) shared pad | 20 | (a) S2 | 1.8 (Ice) | XP25.3 | BL_A9 0.80 to XP25.2 ANODE_AM (0.8): move to y 43.2 | measured |
| D-F3L | disp-3-4 | DISP | flex 60, green | (89.255, 38.80) PTH; BL_A4 | (35.255, 38.80) PTH | 20 | (a) F3R, S3 | 1.9 (Green) | XP23.4 | 0.44 to F2's pad; body 0.65 to XP23.1; sill (#10) | measured |
| D-F3R | disp-3-4 | DISP | flex 60, green | (149.355, 38.80) PTH; BL_A11 B.Cu 42.9 | (95.355, 38.80) PTH | 20 | (a) F3L, S3 | 1.10 (Green) | XP12.13 (DRV top strip) | route 0.25 / 0.26 / 0.27 to P, F2R, S slots; DRV side 45 mm (#5) | measured |
| D-CF (K3) | disp-3-4 | DISP | rigid 18.5, pink | (58.285, 31.60) PTH round; harness wire | (42.785, 31.60) PTH round | 20 (6) | (a) F2L | 1.11 (Rose) | harness | net name (#8); shim channel D7 | measured |
| D-S2 | disp-3-4 | DISP | flex 60, blue | (100.60, 22.69) PTH; BL_A5 | (137.17, 22.69) PTH | 20 | (a) F2R | 1.12 (Ice) | XP24.1 | 0.55 to KS7 (0.25); return 1.26 to ANODE_S1 | measured |
| D-S3 | disp-3-4 | DISP | rigid 38, green | (136.385, 6.60) PTH round; BL_A10 (swap to the left, #7) | (101.385, 6.60) PTH round | 20 (14) | (a) F3L, F3R | 1.13 (Green) | XP12.12 (DRV top strip) | **driven cap on P's return pad and gold (#7)**; 0.30 to P | measured, cap assumed |
| D-HL9 | disp-3-4 | DISP | existing 3 mm LED, the "m" | M_A (162.17, 38.50) PTH | BL_K (159.63, 38.50) PTH | about 14 (220 R) | none | 1.14 (a: the 16th) | XP25.4 | loses dimming when VT20 goes (#3) | measured |
| D-RGB | disp-3-4 | carrier | 8 addressable RGB 5 mm | DATA from D11 | 5 V, GND | 96 capped (288) | none | none (one data pin) | harness, 3 wires | carrier vs 24 joints (#9) | inferred |

* **Total mA** (DISP, *inferred*): 14 filaments at 20 mA = 280, plus HL9 about 14 and the LEDs 96 capped. At finding 12's matched
  look the filaments draw about 330. The clock's 5 V worst case: 872 mA (87 %) as the face run counts it; 922 mA (92 %) matched;
  680 / 730 with the LED cap. The PWM chip or chips add about 10 to 20 mA (*assumed*).
* **Channels needed alone:** DISP 13, or 14 with HL9.
* **Channels if same-colour sources share:** DISP 9, or 10 with HL9 (Rose = F2L + CF, Ice = F2R + S2, Green = F3L + F3R + S3).
* **Connector pins:** 12 BL strip pins (BL_A1 to BL_A11 and BL_K, three of them spare today: XP25.3, XP12.12, XP12.13), plus
  M_A, plus a 6 or 7 wire harness (finding 4). XP12.11 stays the last spare.
* **What DISP forces that the fascias may not:**
  * the drive polarity (finding 2): every DISP return is one common-cathode pour;
  * two light lines in DRV's top strip (finding 5);
  * HL9's dimming once VT20 goes;
  * 19 lines in all with a fascia of 6, so a second chip unless colours are grouped;
  * a harness header on DRV;
  * the case sill.

## 6. Left open

* **Not measured:**
  * a rigid bar's lead form and pitch (finding 7);
  * the brightness of a 60 and a 185 flex at one current (finding 12);
  * an unlit coloured flex by day (finding 13);
  * each colour's forward voltage (K4W411 #2);
  * the DISP to DRV gap (11.0, *inferred*).
* **Not done:**
  * a KiCad DRC (no board was edited);
  * the routes on DRV;
  * the room for the PWM chip or chips, the FETs and the harness header on DRV;
  * BL_A10's top-band route (finding 7, *inferred* only);
  * the LED carrier's outline.
* **The copper check** uses the face run's routed points (0.1 mm grid). Three margins are 0.00 to 0.02 (P's return slot to BL_A11,
  BL_A9 to XP25.2, BL_A6 to ANODE_S1). Only KiCad's DRC on the real tracks settles them.
* No marked picture: the owner asked for the doc only (a change sent by the coordinator during this run).
