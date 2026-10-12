# TS06 parked ideas: planned and grilled, not running

The owner, 2026-10-07 about 23:25 UTC: "I want you to remind me to keep my adhd in check and dont blindly follow me when
I say run things", then: "also my adhd tasks still get planned out and grilled if not running".

So every idea that is not run gets an entry here: the owner's words, a short plan, a grill (the hard questions), and when
to pick it up. Nothing here runs until the owner says so *and* the check passes: does it move the main goal, does the
pace allow it, is a decision open first.

**The main goal now:** the board order (`fab/ORDER.md`), the owner's own hand. After it: the bench measurements
(`3d/jig/README.md`).

---

## P1. Fascia face: pick one after pass 3, then stop
* **Words:** 10-07 20:58 "striking and coherent, no weird doglegs, symmetrical and pleasing"; 23:05 "combine B* and C*
  with new info"; 23:22 "1" (let pass 3 finish, pick one face tomorrow, park it, no pass 4 tonight).
* **Plan:** the owner looks at pass 3's sheet once and picks a face. The pick goes into `PCB/TS06-FASCIA-pass3.md`. A T
  board (front-mounted beads, plated holes) is built only later: the THT plan said 4 runs, about 1.3-1.5 M tokens.
* **Grill:**
  * Does it move the order? No. Fascia R rev B is the one to order and stays as it is.
  * The trap is endless passes: pass 1, 2 and 3 in one night, about 1.3 M tokens, and the week went 2 points over. Rule:
    one pick, then no new pass until R rev B is on the bench.
  * Facts not yet known: the rotary's 25 mm plate is not measured (it decides whether the dial beads fit), and knob A is
    not in hand.
  * A rails face puts two bare 5 V lines on the front (see P3).
* **When:** pick tomorrow (5 min). Build: after the boards arrive and the dry fit is done.

## P1a. Fascia pass 4: the levers' meaning made plain, C*'s richness, pointers to the tubes (planned, not run)
* **Words:** 10-07 23:5x UTC, after pass 3: "the purpose of showing visuallly which lever acted on which menu option got
  lost a bit in the clutter, can you make that more promiant while keping any gold traces connecting the two levers
  themselves to the center while the traces to rotary posyions go on the sides / best candidate is d2 but I still hope to
  see integrated complexity from C* / title line should be something else completely / ... maybe we have the traces from
  rotary positions/levers/buttons actually physsically point to the bulbs they will be changing, since fascia sits right
  underneath the bulbs."
* **Principle (10-08 ~00:00 UTC):** "info first as a design choice, deal with clutter creatively": the information
  stays; clutter is solved by form (merge lines into pointers, shape the rail, a tube-map glyph per screen, ink
  hierarchy, quiet parking screens). In the brief.
* **What the spec says** (`knowledge/TERMINAL-06-spec.txt` §1 table): FIELD is read on positions 2 SET TIME, 3 DISPLAY,
  4 AMBIENT, 5 FORMAT/DATE; SUB only on 3 and 5, and only when FIELD is thrown to its second position; the keys work on
  2 to 5; positions 1 and 6 read nothing. What each screen changes: SET TIME the hours or minutes tubes; AMBIENT the colon
  lamps or the backlight; FORMAT/DATE the digits (12/24 h, the date); DISPLAY all tubes; INFO is shown on the ИН-15 pair.
* **Plan (one run, D2 as the base):**
  1. The logic layer, bold gold, symmetric about the control row: from the names, positions 2 and 3 run **over the top**
     and 4 and 5 run **under the bottom** to FIELD (C*'s parallel lines at 2 mm pitch with concentric bends: the
     integrated complexity); 3 and 5 go on to SUB. The FIELD-to-SUB link (the SUB rule: SUB fed from FIELD's second
     throw) runs **in the centre**, on the control row, between the two levers. Positions 1 and 6 get no line (they read
     nothing), which itself shows the end stops.
  2. The rails start at SUB (the critics' point 3), so the lanes over and under FIELD are free; from SUB rightwards D2's
     rails frame the ladder and the keys, and close at the right end as in D2.
  3. Pointers to the tubes: a white tube index along the top edge (a small mark at each tube's x: H10 13.2, H1 36.6,
     colon 50.5, M10 64.0, M1 87.4, S10 108.6, S1 129.1, ИН-15 150.4 and 171.4), and short white pointers from the lines
     that change a tube to its mark (SET TIME to the hours and minutes, AMBIENT's colon to the colon, INFO to the ИН-15
     pair; DISPLAY changes all tubes, so it points to the whole index).
  4. Three hierarchy levels, checked in the picture: the logic bold gold; the circuit (rails, ring of beads, ladder)
     standard gold; ornament and pointers white hairline. Less ornament than D2 if needed to make the logic read first.
  5. The title: something else completely; draw the owner's pick, or 3 or 4 candidates in a crop.
* **Grill:**
  * Does it move the order? No. Fascia R rev B is ordered as it stands; this is the future T face.
  * Clutter is the owner's own complaint, and pointers add lines. The test is a 3-second read: can a stranger tell which
    lever works on which screen? If the pointers blur that, drop them to a crop and say so.
  * Lanes are tight: over FIELD's ring there are about 4.7 mm, so two lines at 2.0 mm fit and three do not (pass 3).
    That is why the rails must start at SUB, or the logic lines lose their lanes.
  * Gold for logic, not just circuit: spec §6 draws the SUB rule in gold ("drawn, not captioned"), which is against
    xstream's critics' "gold = circuit only". Say which rule wins and why (the owner's purpose: the logic made plain).
  * The fascia is raked 12 degrees under the tubes; whether the top-edge index shows from the front is *assumed*.
  * Pace: the week was +1.8 over its line at 23:15 UTC, plus pass 3 since. Launch only with xstream's GO after the
    morning reading.
* **Cost:** one run, estimate 0.4-0.5 M, cap 0.6 M / 90 min. The brief is ready in the session's scratchpad
  (`fascia-pass4/BRIEF.md`).
* **When:** after the morning reading (about 10:00-11:30 MSK) with xstream's GO, ideally after the order is placed.

## P2. Page update and republish (upright J1, rev B zip, lower case, tidy hand wiring)
* **Words:** held since 10-07 afternoon for the owner's go ("wait for pace, coordinate with xstream").
* **Plan:** one run, estimate 0.4-0.6 M, cap 0.8 M / 90 min. It changes the zip name in the Order tab (`src/index.html`,
  `test/run.mjs`, `tools/order.py`), draws the upright plug and the new lead, the 2.8 mm lower case and the tidy wiring,
  passes the 187 tests, and is republished to the same link.
* **Grill:**
  * Does it move the order? Only one way: **the live page's Order tab still names the rev A fascia zip.** If the order is
    placed from the page, it would take the wrong fascia. Order from `fab/ORDER.md`, not from the page, until this is done.
  * Pace: under the Pace Act this is an announced launch. Only when the week is on its line, or with xstream's GO.
* **When:** after the morning reading (about 10:00-11:30 MSK), if the owner wants the page right before ordering.
  Otherwise after the order.

* **Added 10-12 18:59 UTC, owner: "straight in"** (asked: sockets or solder the ИН-12 / ИН-15 pins straight in). So
  no socket contacts. The same run also changes: the BOM line of 72 contacts (`tools/bom_pair.py`, regenerate the BOM),
  build step 2's text and the tube proxies on the page, "socketed" in `PCB/TS06-pair-testing.md`, and the case's
  `IN12_SEAT` (4.5 mm, *assumed* for a socket) in `3d/case-pair/case_pair.py`, then its checks. The board and the order
  do not change (the 1.2 mm holes fit the tubes' own pins). Needs one bench number first: how high the ИН-12 glass
  sits above the board when soldered (pins fully home, or a chosen height with a spacer).

## P3. A resettable fuse on DRV's J1 pin 1 (only if a rails face is built)
* **Words:** a pass-1 question (exposed 5 V rails 26.5 mm apart on the face).
* **Plan:** a PTC on DRV in series with J1 pin 1 (+5V to the fascia). The hold current is *inferred* at about 0.5 A, and
  DRV's 5 V source is not checked.
* **Grill:**
  * Does it move the order? No, and it would change DRV, which is in the order. Do not touch DRV now.
  * It is needed only if a rails face is built. A medallions face (A or A*) needs none.
* **When:** with the T board build (P1), as a DRV rev C item.

## P4. The base end blocks cut (case about 3 mm lower)
* **Words:** the J1-upright run's finding; the owner has not asked for it.
* **Plan:** `3d/case-pair/case_pair.py` base end blocks 8 mm (including the base), floor -4.5 to about -1.5,
  regenerate outputs and `checks.md`, verify_pair 27 PASS. A small run (*inferred* 0.2-0.3 M).
* **Grill:** cosmetic, the case is printed later, and it touches the case checks. It does not move the order.
* **When:** before the case is printed.

## P5. SW1 pad order on fascia R (removes the A6 wire's pass over three tap wires)
* **Words:** the page-handwire run's note (+5V, TAP5, TAP4, A6, TAP3, TAP2, GND).
* **Grill:** it changes the zip about to be ordered, for a cosmetic gain on the back's hand wiring. Not worth the risk.
* **When:** not for rev B. Revisit only if R ever gets a rev C for another reason.

## P6. Small open words (no run needed)
* The title strip's text on the chosen face (xstream: "TERMINAL-06  TS06-FASCIA rev C"): the owner's word, when P1 is
  built.
* T plan Q4 (plated holes with a black moat, a 10-board T sample first): decided with P1's build.
* meshok.net in the session's allowed domains: the owner's own setting, only if wanted for buying parts.
* The Pace Act art. 7: settled by the owner (10-07 23:27 UTC): no priority list in law; Amendment 2 proposed.
* JST PH B6B-PH-SM4-TB heights (*inferred* in the J1-upright write-up; jst-mfg.com refused by this session's network):
  one FETCH ask to xstream when the page run or a T build needs them (owner 23:4x: "get the info cheaply"). Not tonight.

## P7. A soldering jig for the ИН-12 and ИН-15 (straight in)
* **Words:** 10-12 19:0x UTC, owner: "what is best for alignment?" (after "straight in").
* **Plan:** a printed comb that sits on TS06-DISP (located by its standoff holes) with a cradle per tube at the real pitch
  (23.36 / 27.42 / 23.36 mm), holding each glass plumb at one gap above the board, about 2 mm (*inferred*). Tack one
  corner pin per tube, check the row by eye and with a straight edge on the glass fronts, then solder the rest. The
  case's `IN12_SEAT` becomes that gap (P2).
* **Grill:**
  * Not fully home: the glass's rear face and its pip are not a true flat, so each tube would lean its own way, and the
    iron's heat and the board's flex would sit right at the glass-to-pin seal. No ИН-12 soldering distance is in the repo
    (the ИН-17's ТУ says 8 mm); *inferred* risk.
  * Not the case's 4.5 mm: the pins are 6.25 mm (model, not calipered); through a 1.6 mm board (*assumed*) a 4.5 mm gap
    leaves about 0.15 mm of pin out the back, no joint. Gap at most about 3.5 mm for 1 mm of pin out the back.
  * **Measured by the owner (10-12 19:07 UTC): free pin length 6.0 mm** ("three fifths of a centimeter / thats the free
    lead length"; the ИН-12, *assumed*, as asked). DISP is 1.6 mm (fab/ORDER.md). So the gap is 0 to 3.4 mm for 1 mm of
    pin out the back; at 2.0 mm, 2.4 mm out the back. Pick: **2.0 mm**; case `IN12_SEAT` 4.5 -> 2.0 (glass 2.5 mm nearer
    the board) in P2.
  * Does it move the order? No. Needed when the boards are here, before the tubes go in.
* **Cost:** a small model run like `3d/jig/` (*inferred* 0.2-0.3 M), or in the P2 run.
* **When:** after the boards arrive; with or after P2.

## P8. The tube backlight: one LED on one side looks lopsided
* **Words:** 10-12 19:24 UTC, owner (four shop pictures in `qa/backlight-options/reference/`): "Im not so sure now I like
  the stock backlight of a single led one one side of the bulb, are any of these better picks or maybe you have other
  suggestions". The four: a 3 W white star module (5 V), a WS2812 seven-LED round board, red soft LED filaments, a 5 mm
  amber Piranha.
* **What the board has:** HL1-HL8, one 3 mm amber LED beside each tube, each on its own MCP23017 pin and 220 R (about
  12 mA, *inferred*), common return through the MPSA42 on D11 (PWM). Spec: amber only, diffused, behind 2 mm printed
  shield rings. Per-tube LEDs show which tube a setting changes.
* **The four, judged:** 3 W white: wrong colour, about 0.6 A each against 12 mA, too big. WS2812 board: about 23 mm, no
  room round a tube, RGB amber is muddy, its timing upsets the tube multiplexing, rewiring. Filament: a line for a whole
  row, not per tube, needs its own driver, red is near the neon's orange; maybe a case accent later. Piranha amber: the
  right colour and a wide beam, the best of the four, but 4 legs on a 5.08 mm square do not fit the 3 mm LED holes, and
  it is still one point on one side.
* **Plan (no board change):** a printed light-guide ring round each tube's base, in clear or natural PETG, fed by the
  existing LED, so the glow goes all round; plus diffused (milky) wide-angle 3 mm amber LEDs instead of clear. Bench test
  first: one tube, one LED, one printed ring, at the 2.0 mm gap (P7).
* **Grill:** a second LED per tube or a centre LED changes TS06-DISP (rev C) and holds the order: not worth it before a
  bench test. Two LEDs on one MCP pin is about 24 mA, at its 25 mA limit. Does it move the order? No, if no board change.
* **When:** the ring with the case work (P2 or the case run), the bench test when the tubes and LEDs are in hand.
* **Owner 19:34 UTC:** "good idea on the diffusion but I feel the filaments might work great if used creatively, why
  wouldn't it work as backlight if it can wrap around the bulbs envelope nicely?" Grill of a filament ring per tube:
  * Room: the ИН-12 glass is 19.47 x 28.86 mm (model), the pitch 23.36 mm, so 3.9 mm between glasses; two filaments of
    about 3 mm (*inferred*) need 6. A closed ring does not fit; arcs above and below each tube do.
  * The case trench sits close to the glass; any wrap widens it (a case change, not printed yet).
  * Drive: on the board's own HL pads (MCP pin, 220 R, about 12 mA) a filament glows dim and even, per tube kept; more
    light needs a transistor per tube (DISP change) or one driver for all (per-tube highlight lost).
  * Colour: red sits next to the neon's orange and may wash the digits; amber or 2200 K warm white filaments exist.
  * Unknown: the listing's length, voltage, thickness, bend radius (the owner can read its specs tab).
  * Next: bench test one ИН-12, one filament, 5 V through 220 R, arcs vs a wrap, red vs amber. No board change.
  * **Listing specs (owner 20:09 UTC, pictures in qa/backlight-options/reference/):** lengths 38/60/80/95/125/130/145/
    185/200/255/300/360/450/460 mm (±1-2 mm), 3 V DC, under 300 mA, 100-110 lm, CRI 80; colours warm white, white, red,
    green, blue, pink, yellow. Not cuttable (*inferred*: COB with end tabs). Thickness not given.
  * Fit per arc (*inferred*, glass 19.47 wide at 23.36 pitch, filament about 2.5 mm): an arc of about 120 degrees round
    each end of the glass, about 25-30 mm glowing; so **38 mm** is the length to try (tabs included). A continuous
    scalloped line over the four ИН-12s is **125-130 mm** (per-tube light lost).
  * Drive on the HL pads: 2 arcs in parallel on one pin, about 5 mA each, about 1/8 of the rated current per mm: a soft
    glow, maybe weak by day. Two in series need about 5.4 V: no.
  * Colour: warm white or yellow (nearest the spec's amber), not red.
  * **Owner 20:11 UTC: "short and single end variants available too"** (pictures saved): rigid ceramic/glass bars
    18.5/26/38/54/68 mm (warm white among the colours), and single-end flexible ones 59/70 mm with a small board and an
    8-pin chip at the end.
    * Rigid **18.5 mm** bar: shorter than the 19.47 mm glass, so one above and one below each tube fit with no bending and
      nothing in the gaps; 26 mm and longer reach into the neighbour's room. Could hide in the case's brow and sill and
      light the glass indirectly. **Check the voltage:** bulb-type filaments are often tens of volts; only 3 V ones work.
    * Single-end with a chip: the chip is likely an effect driver (flicker or fade, *inferred*); steady PWM dimming and
      12 mA from a pin may not suit it. Check what the chip does before buying.

## P9. Layered light lines on the case (a "glyph" look), user-controllable
* **Words:** 10-12 20:3x UTC, owner: "Im thinking of a layered approach, have the longest available strips as accents on
  the case edges or outlines, one horizontal that spans all tubes, one more for the 4 in12s, one for two in17s, and one for
  in15s basically mirroring what you did for the fascia variant, these lines can be on different sides as to not clutter
  and create visual interest. Im basically thinking of the back of a nothing phone, feel me? maybe we can even mix colors?
  user controllable".
* **Plan:**
  * Four lines, lengths from the filament listing (tube x from fascia R): the whole row about 185-200 mm; the four ИН-12
    (x 13-87, about 95 mm with the glass); the two ИН-17 (x 109-129, about 38-60 mm); the ИН-15 pair (x 150-171, about
    38-60 mm). Put on different edges (top brow, bottom sill, a side) so no two run side by side.
  * Meaning, not only accent (the owner's "info first"): a line glows when its tube group is being set or shown (SET
    TIME the ИН-12 line, INFO the ИН-15 line, the seconds line ticks), same logic as the fascia.
  * Colour: each filament is one colour; mix by giving each layer its own colour and dimming each on its own; two
    filaments on the main line give a two-colour blend. Any colour needs RGB strips (loses the filament look; addressable
    ones upset the tube timing).
  * Drive: one channel per line (or per colour): a small add-on board with a 16-channel I2C PWM chip and small MOSFETs,
    tapped from the RTC module's 5-way header (I2C + 5 V). No change to the ordered boards. Firmware: a few I2C writes,
    new items under AMBIENT.
* **Grill:**
  * Does it move the order? No; it must not change it (the add-on is separate).
  * 5 V budget: about 0.1 A per line at accent brightness (*inferred*), 0.4 A for four, plus dropping resistors' heat;
    the supply's spare current is not known here.
  * Case: grooves and diffusers in the case edges; the case is not printed yet, so it is the right time to plan, after
    the bench test (P8) shows how the filaments look.
  * Clutter: four lines plus the tube glow plus a gold fascia; the owner's own rule says each line must carry meaning.
* **Cost:** a design run (case renders with the lines, the add-on circuit) *inferred* 0.4-0.6 M; firmware later.
* **When:** after the order and the P8 bench test.

