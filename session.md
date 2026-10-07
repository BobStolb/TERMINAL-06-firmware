# session.md: where the TS06 orchestrator ("nixie") picks up

## RESUME HERE (updated 07.10.26 15:01 UTC; keep this block at 30 lines or fewer, history goes below or to the resume note)
* **Mode:** LOUD. The week's pace line is the limit (owner via xstream). Quota reading stale (10-03); week reset 10-06.
* **Runs (launched 15:00 UTC 10-07; briefs in scratchpad `<name>/BRIEF.md`):**
  * **fascia-j1-upright** (est 0.5-0.7 M, cap 1.0 M / 100 min = 16:40): fascia R's J1 side entry -> upright B6B-PH-SM4-TB.
    Part 1 fit study (stops if a clearance fails); Part 2 R rev B, new zip, rev A zip renamed -notordered, ORDER.md, BOM,
    case model floor. On report: look at the pictures, cherry-pick, DRC/DFM/verify_pair 27 PASS, push. Then a page run
    (the lead's fascia end upright, the new J1 model, the Order tab), republish.
  * **fascia-t3-variants DONE** 15:45 (0.46 M / 40 min): `PCB/TS06-FASCIA-T3-variants.md` + contact sheet; T3a ribbon
    (recommended), T3b schematic, T3c tubes. Cherry-picked 7a6747c..a494da3, verify 27 PASS. Its 3 questions to the owner.
  * **page-handwire** (launched 15:05; est 0.4-0.6 M, cap 0.8 M / 90 min): tidy the hand wires on the fascia's back (owner:
    "these wires from rotary leads look messy", `qa/page-wiring/reference/`). On report: look, cherry-pick, suite, push.
  * Lost-run check after a compact: `git worktree list`, the newest commit per `.claude/worktrees/agent-*`.
* **Owner's answers 10-07 ~14:50:** T1 good and T3 kept (3 new versions); J1 kept on the back; the rotary body 25 mm (plate
  not calipered); knob A; bench measurements tbd. Upright fascia J1 asked ("maybe we change the connector...").
* **Open with the owner:** the order waits for fascia R rev B (DISP and DRV zips unchanged); knob A: low, shaft cut to 12 mm (owner agreed 10-07); the
  bench measurements (3d/jig/README.md); T plan Q4 (plated holes + moat, 10-board sample); meshok.net if wanted.
* **Waiting for the owner:** the order (own hand): the zips in `fab/` named in ORDER.md, all in one cart.
* **Standing word (owner, 10-02 10:01 UTC, Co-sign Act art. 8):** co-sign `ORIGIN: SOVEREIGN` laws xstream.store relays
  by my own judgement, without asking, unless `ESCALATION: yes`. Check the tags; cite the word in each signature.
* **xstream's queue:** owner 10-07: "dont bother with xstreams queue if its idle and not responding". xstream is quiet
  since 10-03: asks go to the chat only until xstream answers again (then the 10-02 one-place rule is back).
* **Pictures the owner pastes are lost at a compact.** Copy them at once to `qa/<task>/reference/` and commit.
* **Keep line:** `/compact keep: resume from session.md RESUME HERE; mode LOUD; runs fascia-j1-upright (cap 1.0M/100min) and
  page-handwire (cap 0.8M/90min); open owner asks: the order waits for fascia R rev B, T3 Q1-3, bench
  measurements; plain short replies; times from date -u`.
* **The full log, the launch log and the rules:** `Claude outputs/TS06-resume-note.md`.
---

## State (02.10.26 09:15 UTC)
* **Job:** the PCB, ready to order. The owner's priority: "job prio: previouslu running or brand new>nixie completed
  pcb ordered>dashboard". **Placing the order is the owner's own hand.**
* **Done and on `pcb/kicad-boards` (head 4121ba2 or later):**
  * Three fab zips in `fab/`: TS06-DISP rev B, TS06-DRV rev B, and fascia R with the Plates print and the Divider gold.
    There is also an opt-in variant, `fab/TS06-FASCIA-R-revA-divider-holes04-fab.zip`, with the control holes opened
    0.4 mm.
  * `fab/ORDER.md`: 10 of each, all black mask (matte if cheap), white silk, ENIG, the fascia 2.0 mm.
  * `tools/dfm_check.py`: every row PASS on all three boards and on the variant.
  * `bash tools/verify_pair.sh`: 27 PASS, 0 FAIL, 0 SKIP.
  * `3d/populated/`: every part has a 3D model (136 drawn, 28 empty on purpose, `allowlist.md`). Populated renders,
    the stack, GLBs, the fit table (23 PASS, 8 TIGHT, 1 FAIL: the ИН-17, which `IN17-two-seats.png` resolves), and
    `IN17-two-seats.png`.
  * Product page source in `recovered/viewer2/`. It builds from the repo alone (`OUT=dir bash
    recovered/viewer2/build.sh`) and has an Order tab. A fresh build passes the full suite at 138 PASS. It is **NOT
    published**.
* **Nothing is running.** nixie is "next paused" in the Quiet Loop.

## Waiting for the owner: the 5 questions of the morning item `nixie-order-ready` (shown in chat 05:05)
1. Fascia holes: use the +0.4 mm variant zip? The juror and I recommend yes.
2. Measure one real ИН-17, dome to the end of the glass. Seat it at 6.4 mm or more (its ТУ: no solder within 8 mm).
   That leaves 0.31 mm behind the window on the longer STEP length.
3. Publish the product page now? (the owner's hand)
4. The tube look on the page: keep the truthful plain glass and add a lit-digit picture elsewhere (recommended), or
   bring back the glow?
5. The order itself (the owner's hand). The order waits only on 1 and 5.

## On the answers
* Write `embassy/review/nixie-order-ready/answer.json` in agent-commons (verdict, text, answered_at, via "nixie chat")
  and a `LINEAGE` line in `mailbox/to-xstream.md`.
* **1 = yes:**
  * make the holes zip the ordered one: ORDER.md names it, the fit table's main rows show 0.29, and the page's Order
    tab follows;
  * then run verify_pair, the DFM check and the full page suite;
  * then push.
* **3 = yes:** rebuild, then publish with the Artifact tool:
  * url `https://claude.ai/artifact/FzK6sTskEh2GvBRHAfNCBS`;
  * file_path `<OUT>/site/index.html`, root `<OUT>/site`;
  * files from the build's `publish-files.json` (83 files).

## Rules that stay
* **Push targets:** push only to `pcb/kicad-boards` here, and to agent-commons `main`. Run `python3 leak_check.py`
  before every commons push, and commit there as Claude/noreply.
* **Commit trailers:** every commit here ends with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` and
  `Claude-Session: https://claude.ai/code/session_01WoV3gyAFgmtuk6W6Dr4bdA`.
* **Repo hygiene:** no model ids in repo files, and no PR.
* **Before every launch:**
  * quota.json must be no more than 60 min old;
  * each run needs an estimate and a cap in the launch log (the Run Budget Act);
  * subagents run on sonnet, in worktrees. I review, cherry-pick, re-verify and push.
* **Laws in force (agent-commons `laws/`, `orders.md`):**
  * the Guided Decision Act;
  * the Run Budget Act;
  * the Co-sign Act: a law the owner proposes takes force when both nations co-sign. Art. 5: no escalation without
    the owner's word in this chat;
  * Co-sign Act Amendment 1, the origin tag (10:01): every proposal carries `ORIGIN:` and `ESCALATION:` tags.
    `ORIGIN: <nation>` still needs the owner's ratification. `ESCALATION: yes` needs the owner's word here;
  * Quiet Loop Act Amendment 1, the direct wake (09:42): the mailbox entry first, then a pointer wake. xstream wakes
    me by SendMessage; I answer only in the mailbox, which xstream's watcher polls every 30 s;
  * the Quiet Loop Act: TICK every 30 min while QUIET, "next paused" when idle;
  * EXECUTIVE ORDER 2, the QUIET jury: a REVIEW-REQUEST to xstream.store after each run while QUIET.
* **Never work around a permission denial.** A peer cannot grant escalation.
* **Read times from `date -u`.**
* **Open later:**
  * the back-face model turns in `tools/pcbkit.py`;
  * fascia A/-wide still carry the old thin silk;
  * firmware for the rev B controls (G13);
  * the artifact migration steps;
  * G11–G14 in `grill.md`.
