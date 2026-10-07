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
