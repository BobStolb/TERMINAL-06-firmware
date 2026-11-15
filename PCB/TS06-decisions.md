# TS06: the open decisions, as review cards

Made 2026-11-14 from `PCB/TS06-audit.md` ("The owner's decisions", "The plan's ten October decisions") and
`PCB/TS06-routing-plan.md` section 6. One card per decision. The first option is the recommended one, with its reason.
Answers are written in the **Answer** line when the owner gives them.

Cards B, C and D are also in the owner's review queue since 2026-11-14 (items `nixie-decisions-b`, `-c`, `-d`). Card A was
answered in chat and is not in the queue. An answer in either place counts; this file is the record.

## Card A: the order and the product

### D1. What gets ordered first?
* **a. One rev B bring-up set, plus the window coupon, after audit steps 1 to 11** (recommended: one built set turns every
  "assumed" into a measurement; the coupon answers the bare-FR4 window question every lit fascia waits on).
* b. One rev B bring-up set only; the coupon later.
* c. The coupon only; boards wait for rev C.
* d. Nothing until rev C is drawn.

Sources: audit verdict 3 and 4, steps 12 to 15; routing plan 6.10.
**Answer:** no preference (owner, 2026-11-14). Working default: a. Not final.

### D2. Kit or finished unit?
* **a. A kit the buyer solders** (recommended: the design is through-hole for this; a finished 185 V unit puts more safety
  duty on the seller).
* b. A finished, tested unit.
* c. Both.

Source: BOM audit, product safety section. **Answer:** no preference (owner, 2026-11-14). Working default: a. Not final.

### D3. The 12 V adapter
* **a. Ship a regulated 12 V adapter in the box** (recommended: a 19 to 24 V adapter kills the input diode; cost about 7 per unit).
* b. Name one adapter type in the manual and label the jack.

Source: BOM audit findings 7 and 8. **Answer:** no preference (owner, 2026-11-14). Working default: a. Not final.

## Card B: rev C, the electrical choices

### D4. Where do rev C's light drivers live?
* **a. On a plug-in light board, machine-assembled, with its own 5 V module** (recommended: keeps twelve fine-pitch parts out
  of a hand-soldered kit; the lights become an option; colour changes stay a firmware table).
* b. On DRV as the routing plan has it: two 16-channel chips, hand-soldered, plus a second 5 V module.
* c. One chip with colour groups: fewer parts, but a later colour change means re-wiring.

Sources: audit decision 2; BOM audit 13; layout L3; routing plan 6.3 and 6.6. **Answer:** a (owner, review card, 2026-11-15: "as recommended for all")

### D5. The fascia's base board for rev C
* **a. Rev B's surface-mount layout** (recommended by the routing plan: frees the pill for the connector, no plated holes on
  the face, no power on the face).
* b. The through-hole T layout.

Source: routing plan 6.2 (K4W411 grill #15). **Answer:** a (owner, review card, 2026-11-15: "as recommended for all")

### D6. Spacing at 185 V in rev C
* **a. 1.0 mm clearance, 1.25 mm creepage, as a DRC rule** (recommended for a new layout; rev B stays at 0.8 mm, made two-way).
* b. Stay at 0.8 mm, two-way, in rev C too.

Sources: layout Reconsider; routing R4 (at 1.25 mm today 161 + 55 places fail, so this only fits a new layout). **Answer:** a (owner, review card, 2026-11-15: "as recommended for all")

### D7. The seconds pair in the multiplex
* **a. Decide after bench step 4** (recommended: the brightness at six slots is not known yet).
* b. Take the ИН-17 pair out in rev C in any case: four slots, one more K155ID1, two fewer opto-couplers.
* c. Keep six slots in any case.

Source: BOM audit finding 1 and Reconsider. **Answer:** a: decide after bench step 4 (owner, review card, 2026-11-15: "as recommended for all")

## Card C: approvals (approved today: K4W411 only)

### D8. The display, disp-3-4
* a. Approve, glyph colours still free to change.
* b. Approve as drawn.
* c. Not yet.

Blocker to fix either way: the lintel's driven end (D12). **Answer:** c, not yet (owner, review card, 2026-11-15: "c, I want to see your go at the creative design process established here, make a fable version fascia and glyph layout"). A new pair is being drawn: `PCB/art/TS06-PAIR-YARN/BRIEF.md`.

### D9. Fascias: which to approve (several may be picked)
* organic-2-1 The print
* organic-2-2 Mushroom
* science-2-3 Double slit
* celestial-3 Sundials

Each is "buildable after changes" in its grill. All wait on the button measure (audit step 2). **Answer:** none picked on the card. Read as "not yet": to be asked again beside the new pair.

### D10. Fascia BLUPRNT
* a. Approve.
* b. Not yet.

**Answer:** no answer on the card. Read as "not yet": to be asked again beside the new pair.

## Card D: face details

In the queue, not answered yet. With no face of Card C approved, D11 to D14 can wait: each one belongs to a face that is not approved.

### D11. Organic's S light (only if an organic face is approved)
* **a. Move S onto the plumb bar: a re-run of the two faces** (recommended: one back layout then serves every fascia).
* b. A second back layout for organic boards only.

Source: routing plan 6.5. **Answer:**

### D12. The lintel's short on disp-3-4
* **a. Swap the bar's ends and route its line along the top band** (recommended: fixed in copper).
* b. A polyimide dot on its right cap.

Source: display grill #7; routing plan 6.8. **Answer:**

### D13. Sundials: the sun and the moons
* **a. Apart: each on its own channel** (recommended: free with the 7-way pin map; day and night can differ).
* b. Together on one duty.

Source: routing plan 6.7. **Answer:**

### D14. Sundials: the gold rails
* **a. Gold with no net** (recommended: rev B has no power on the face; a floating strip is safe and plates).
* b. Rails that carry +5 V (needs the through-hole base, D5 b).

Source: celestial grill; routing plan section 0. **Answer:**

## Not cards yet (they wait on a measurement or on a card above)
* **The case sill and variant D** (routing plan 6.9): after audit step 10. "Straight in" makes the case 2.5 mm shallower.
* **Which colours may change** (routing plan 6.6): no decision needed with D4 a or b; with D4 c, name the lines.
* **How P is held, and the key arcs** (K4W411 #5, #6): after the button measure, audit step 2.
* **The held page update:** after the new boards.
