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
