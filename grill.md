# grill.md: the orchestrator's workflow, and the ideas on the table, grilled

A living document. Each item is a question I should be able to answer about how this project is
run, with my recommended answer and the evidence behind it. The owner annotates under
**Owner notes:**, and I update **Status** when the owner decides. Item numbers (G1, G2, …) stay
fixed, so notes can refer to them.

Started 30.09.26 at about 01:40 UTC, on `pcb/kicad-boards`. The evidence cites commits, files
and agent reports from this project.

**Status values:** *proposed* (my recommendation, not yet decided) and *decided by the owner*
(with the date and the decision).

---

## A. Fan-out: when to run agents in parallel, and how

### G1. When is a fan-out of layout variants worth running?
**Question:** The four-way driver-board layout fan-out produced one robust finding and no usable
layout. What should the next one look like?

**Proposal:** Split it into two stages.
1. A cheap **placement sweep**: many placements, each scored on the MST floor plus pass/fail
   buildability gates:
   * a DRC-legal placement;
   * at most 3 DIP orientations;
   * 185 V kept apart from the logic;
   * the connectors at their edges.
2. **Routing** for only the best one or two.

Run nothing until the mechanical cross-check (the case model against the boards) passes.

**Why:**
* **The one finding survived all four attempts.** Swap (3780 mm), search (3617), bottom-Nano
  (3752) and plane (3935) all beat the baseline's 4265 mm floor, by 8–15 %.
* **None was buildable.** The score measured only wiring:
  * search had 23 mechanical DRC errors and 4 DIP orientations;
  * swap needs USB on the top face;
  * plane never converged.
* **Most compute went on routing layouts that failed for reasons visible before routing.** The
  floor takes seconds (`placecheck.py`); a route takes 25–35 min.
* **The cloud time cost about $19:** swap $13.38, search $4.28, plane $1.61, from the session
  metadata.
* **Trade-off:** a gated sweep can miss a layout whose flaw a human would forgive, such as
  swap's USB on top. Show the owner the gate failures, not only the survivors.

**Status:** proposed. Rev C, the expander under the decoders, was *decided by the owner*
(30.09): after rev B.

**Owner notes:**

### G2. Cloud sessions or local subagents?
**Question:** Which work should run in cloud sessions, and which in local subagents?

**Proposal:**
* **Local subagents in git worktrees by default.**
* **Cloud sessions only** for self-contained, CPU-heavy runs such as routing sweeps. Each one
  gets a "pull point": re-read `ASSUMPTIONS.md` on the base branch before every expensive step,
  and stop if it has changed.

**Why:**
* **Cloud sessions can't be reached once started.** SendMessage to all three failed ("not
  reachable").
* **The geometry changed under them.** The boards were widened at 22:54, 42 minutes after the
  three cloud sessions started at 22:12. All three finished on the stale 176 mm outline.
* **Local subagents can be corrected mid-run.** That happened several times tonight:
  * the rule-units fix;
  * the DRV orientation;
  * the red-team findings;
  * new commits to merge.
* **Cloud cost is invisible from here, while subagent token counts are reported** (280k–580k
  each).
* **Trade-off:** local agents share this container's 4 cores, and routing is CPU-bound.

**Status:** proposed.

**Owner notes:**

### G3. How are parallel agents kept off each other's files?
**Question:** How are parallel agents kept from overwriting each other's work?

**Proposal:** Keep today's rules and make them standard:
* an explicit list of owned files in every brief;
* a private scratch subfolder per agent;
* a first step of `git fetch && git reset --hard origin/pcb/kicad-boards`;
* integration by cherry-pick, never by the agent pushing;
* shared scratch scripts read-only to agents.

**Why:**
* **Ownership lines worked.** 16 cherry-picks tonight had 0 conflicts: the fascia
  variants, case, schematics, test plan and DISP rev B.
* **Every incident was a gap in these rules:**
  * the red-team overwrote the shared `scratchpad/drc.sh`;
  * the electrical grill overwrote the shared `scratchpad/drv/` files;
  * worktrees started from `main` or old commits, before the reset line existed.
* **Trade-off:** cherry-picking is manual orchestrator work, but it forces a verify at every merge.

**Status:** proposed.

**Owner notes:**

### G4. How many agents at once, under the shared quota?
**Question:** How many agents should run at once now that the quota is shared?

**Proposal:**
* at most 4 local subagents at once, launched in waves after each merge;
* a word cap on every report (≤1,200);
* a stated time budget per brief, with a partial result committed at the budget;
* no new launch while `verify_pair.sh` is red.

**Why:**
* **The owner's caps:** 2 cloud chats, 6 agents, no fan-out wider than 4 at night, and 50/50 of
  the 5-hour and daily budget (decided 30.09).
* **Tonight peaked above that:** 7, then 5 subagents plus 3 cloud sessions.
* **The waves that worked best merged one result, then launched the next piece:**
  * the grills, then the fixes;
  * the case, then the variants.
* **Agent times ran 19–73 min, with no time box.** Examples:
  * rhythm: 73 min;
  * DISP rev B: 72 min;
  * DRV rev B: over 90 min and still running.
* **Trade-off:** waves are slower in wall time.

**Status:** proposed. The caps themselves were *decided by the owner* (30.09).

**Owner notes:**

---

## B. Briefs and messages

### G5. How do I stop a wrong fact in a brief from reaching every agent?
**Question:** How do I stop a mistake in a brief from spreading to every agent that reads it?

**Proposal:**
* **Test anything given as exact text or as a geometric fact** before it goes into a brief, with
  a one-minute check against the files or the tool.
* **Every brief says:** "if this contradicts the files, trust the files and tell me".

**Why:** Two of my briefing errors went out tonight.
* **The rule text:** `(min 0.8)` without a unit went to both board agents. KiCad then ignored
  the whole `.kicad_dru` without a word. The DISP agent caught it.
* **The stack orientation:** I told the viewer agent that the driver board's parts face the
  display. They face the rear. My own new file-level mate check caught it.

Both would have produced green checks over wrong results.

**Status:** proposed.

**Owner notes:**

### G6. Should the two orchestrators talk directly?
**Question:** Should this session and xstream.store message each other directly?

**Proposal:** Yes, whenever the platform allows it, always openly: every message sent is shown to
the owner. Until then:
* xstream.store → this session works: its QUOTA messages arrive;
* this session → xstream.store is blocked;
* my replies go to the owner as paste-ready text.

**Why:**
* **The owner encourages replies, openly** (30.09).
* **The platform refused my reply:** "this cloud session cannot message other sessions yet".
* **Trade-off:** relaying costs the owner a paste. The shared branch plus the resume note carry
  state in the meantime.

**Status:** *decided by the owner* (30.09): reply openly. Direct messages from here are still blocked, so
the owner approved a **git mailbox** as the return channel (30.09, ~01:55 UTC): the orphan branch
`mailbox`, where this session only adds entries to `mailbox/to-xstream.md`, and a watcher on
xstream.store fetches it every 20 s. Messages from xstream.store (sender
`bridge:session_014hprjjiRrhAfFjt6Nx8tii`) are treated as verified, on the owner's word.

**Owner notes:**

---

## C. Verification: can the checks be trusted?

### G7. Does every checker prove it can fail?
**Question:** How do I know each checker can actually fail?

**Proposal:** Every checker in `verify_pair.sh` gets a planted-fault test. A copy with one known
fault must fail it. Run a red-team pass on the checks once per board revision.

**Why:** The red-team showed that checks said more than they proved:
* `checkpcb` ignored `fp_rect` courtyards, which is 80 of 103 DRV footprints;
* `audit` counted about 7× the ground islands KiCad keeps (92/139 against 13/14);
* `check_mate()` read in-memory lists, and passed a Ø2.5 hole and strips on the wrong faces;
* all three offline checkers skipped rotated footprints;
* `kicad-cli` ignores a `.kicad_dru` it cannot parse.

Each is fixed (1dd86c4, 4d99b61). Planted-fault tests already exist for:
* the HV rule, automatically, in `verify_pair`;
* the mate and `checkpcb`'s rotation handling, by hand.

**Still missing:** planted tests for `checkcopper` clearance, the DRC edge rules, checksch and
checkmatch.

**Trade-off:** each plant adds about 30 s to a run.

**Status:** proposed.

**Owner notes:**

### G8. What exactly goes to the fab?
**Question:** What exactly goes to the board house, and how do we know it is complete?

**Proposal:** After rev B, commit the boards **filled**, plus a fab package per board:
* Gerbers exported with `--check-zones`, and drills;
* a check that every copper Gerber contains the pour regions.

Order from that zip only.

**Why:**
* **The committed boards store no fill.** DISP's LED return, BL_K, exists only as a pour.
* **An unfilled plot misses it.** The red-team exported one: the F.Cu Gerber had 0 regions
  (13.5 kB); with `--check-zones` it had 1 (224 kB). Plotted that way, all nine LEDs would be
  open.
* **Trade-off:** filled board files are larger, and the "committed = fresh generator run" check
  must ignore fill polygons, or the generators must fill.

**Status:** proposed, for the rev B integration.

**Owner notes:**

### G9. Is a routed board reproducible?
**Question:** Can a routed board be rebuilt exactly from the repo?

**Proposal:** Yes, from its saved route (the JSON), which is the source of truth. Make the router
deterministic: sorted iteration, and a fixed hash seed.

**Why:**
* A fresh `--route` stuck at 2 nets sharing (A7, D7) where the saved run had converged. The
  red-team re-ran it to round 45.
* The rev B agent was asked to fix it.
* **Trade-off:** determinism can hide a lucky seed. Record the seed and the round counts.

**Status:** proposed; in progress in rev B.

**Owner notes:**

### G10. Do geometric checks catch circuit hazards?
**Question:** Do the geometric checks catch hazards in the circuit itself?

**Proposal:** No. Add a short hazard review per revision that lists:
* single points of failure;
* likely assembly slips;
* the bench step that covers each.

**Why:**
* **The missing OV clamp was caught only by an engineer's read, not by any check.** Without
  U12, or with it reversed, the 185 V rail runs away; a model reaches 300 V in 40 ms. No DRC,
  mate or clearance check could see it.
* **Nothing but a reader catches other slips either:** a reversed RTC module (square pad = GND,
  the module's pin 1 = +), or a 24 V adapter on a 20 V gate driver.
* **Trade-off:** it is a written review, not an automatic check. It lives in the review and the
  test guide.

**Status:** proposed.

**Owner notes:**

---

## D. Design decisions waiting for the owner

### G11. Which fascia?
**Question:** Which fascia goes on the clock?

**Proposal:** **R**, the controls on the tube grid (`PCB/TS06-FASCIA-rhythm`, alignment B).

**Why:** Measured here (`PCB/TS06-FASCIA-variants.md`):
* all five controls sit exactly under tube centres;
* it has no fascia FAIL or TIGHT in the case checks;
* KiCad DRC shows 0 violations;
* the rotary clears the sill with no notch;
* it costs the same as W (+8.75 % board area).

A's boss sits on R5's pad (FAIL), and A shows the driver board through 4.8 and 11.6 mm slots.
**Trade-off:** R needs two hands (86 mm from FIELD to −). W keeps one-handed reach. F needs a new
board as well as a frame.

**Status:** proposed; the owner decides.

**Owner notes:**

### G12. What is the committed `.hex` for?
**Question:** What is the committed `.hex` for, and which board type should it be?

**Proposal:** Replace the single stale `nixieClock_TS06.hex` with one file per board type in use
(`…_type1.hex` for the bench clock, `…_type4.hex` for the pair), built reproducibly by
`scratchpad/build_cli.sh`, which moves into `tools/`.

**Why:**
* The committed file is a BOARD_TYPE 1 build from the first commit, while the source defaults to
  type 0 (review finding 8).
* Flashing the wrong type drives the wrong pins.
* **Trade-off:** there are two files to keep fresh, but `verify_pair.sh` can check both are
  current, as it does for the BOMs.

**Status:** proposed; the owner says which types are in use.

**Owner notes:**

### G13. Firmware changes that change the bench clock
**Question:** When firmware fixes change what the owner's working bench clock does, should they
be applied at once or held for approval?

**Proposal:** Apply safety and data-loss fixes at once, and flag them loudly. Hold any change of
user-facing behaviour for approval.

**Why:**
* **I first held the RTC fixes back** ("they alter the bench clock"), then applied them tonight
  (d7aafdc, 28ce526, 86f8d67):
  * the RTC is set at boot only if it lost power;
  * PROGRAM no longer rewrites the clock;
  * the soft-start;
  * the A6 filter.
* **The visible change:** flashing no longer sets the time.
* **Held for approval:** the UX items, such as "−" never decrementing.
* **Trade-off:** fixes land faster, and the owner learns about a behaviour change after it is
  pushed.

**Status:** proposed; the owner confirms the rule.

**Owner notes:**

### G14. Prototype run before production?
**Question:** Order a small prototype batch before production?

**Proposal:** Yes: order rev B boards in the fab's minimum quantity. Run the bench plan
(`PCB/TS06-pair-testing.md`) and the gates on real parts, then order the small production batch.

**Why:** Open items that only parts and a bench can close:
* the ИН-15/ИН-17 pinouts and the pip height;
* the PBS/PLS heights;
* the RTC module's pin order;
* the L1 part;
* the anode resistors marked TBC;
* the ИН-12 brightness at 6 slots (E6);
* the КМД1/МТ1 dry fit;
* the colon courtyard overlap.

**Trade-off:** one extra fab cycle, about 1–2 weeks.

**Status:** proposed.

**Owner notes:**

---

## E. The ideas on the table

### G15. Join xstream.store's live-3D review queue?
**Question:** Should this session take part in xstream.store's live-3D review queue?

**Proposal:** Yes, through the branch:
* `review/queue.json`, one entry per item: what changed, the files, the checks, and the decision
  needed;
* xstream.store pulls the branch and shows the boards live on localhost;
* decisions come back as "REVIEW: …" messages, which I apply and record.

**Why:**
* The shared branch is the only channel that works both ways today (G6).
* A localhost viewer can do what the artifact can't: .glb files, no CDN rules, full-size boards.
* **Trade-off:** another place where state lives (see G16). Acting on "REVIEW:" needs the owner's
  permission, like "QUOTA:".

**Status:** *parked by the owner* (30.09), recorded in the resume note.

**Owner notes:**

### G16. One place for decisions
**Question:** Where does a decision live?

**Proposal:**
* decisions live **here** in `grill.md`, with the owner's notes;
* findings live in `Claude outputs/TS06-pair-review.md`;
* the resume note holds only state and the launch log;
* a future `review/queue.json` holds only items waiting for review;
* every other document links to these instead of restating a decision.

**Why:**
* **Drift is the failure mode already seen:**
  * the verifier found 6 places where the documents contradicted the code;
  * the red-team found about a dozen stale numbers (the 28-pin XP12, 60 strip pins, 95/137
    islands, a 135 mm lead, the 176 mm case);
* **There are already 8 documents** that state decisions or numbers: the pair README section,
  the review, the test guide, the variants page, the case README, `checks.md`, the resume note
  and the viewer page.

**Status:** proposed.

**Owner notes:**

### G17. Quota: how do I throttle myself without a usage reading?
**Question:** How do I keep within the quota when I can't read usage myself?

**Proposal:** Ask xstream.store to send an informational "QUOTA: READING 5h NN % / week NN %"
with each 20-minute reading, not only HOLD and RESUME. At a reading of 40 % or more of the
window, I stop launching before a HOLD is needed.

**Why:**
* `get_usage` isn't in this session's tools.
* The only reading I have is 54 % of the 5-hour window at 01:05 UTC.
* A HOLD arrives after the fact. A reading lets me pace ahead of it.
* **Trade-off:** a message every 20 minutes wakes this session, which costs a little each time.

**Status:** *decided by the owner* (30.09 01:50 UTC): xstream.store sends a reading at each 20-minute wake
while agents run here. Day caps were dropped for weekly halves, so two sessions run at lower capacity
rather than one stopping. The live triggers are 50 % of the 5-hour window and 80 % in total.

**Owner notes:**

### G18. The shared page (artifact) or the localhost viewer?
**Question:** Should the owner review boards on the shared page or in a localhost viewer?

**Proposal:** Both, for different jobs:
* **the artifact:** the shareable summary. It works on a phone and holds the assembly steps and
  the fascia comparison;
* **localhost or KiCad:** detailed review.

Stop fighting the artifact's limits for detail work.

**Why:**
* **The artifact's limits cost time tonight:**
  * `.glb` isn't served, so the models ship as 11 MB glTF JSON;
  * files are capped at 16 MB;
  * CDNs are restricted;
  * the owner's drag didn't work in v1.
* **KiCad and a localhost viewer have none of those limits.**
* **Trade-off:** the owner has two places to look. The artifact links to the files.

**Status:** proposed.

**Owner notes:**

### G19. A completion contract for rev B
**Question:** How is "rev B done" defined?

**Proposal:** Set a `/goal` for the rev B integration, with checkable conditions:
* `verify_pair.sh` all PASS, with the DRV rule-live row passing;
* filled boards and fab zips (G8);
* the schematics regenerated;
* the viewer rebuilt from the final boards and republished;
* the review and README updated;
* git clean and pushed.

**Why:**
* The earlier `/goal` worked: all five conditions were met and evidenced at 3c9ae17.
* Without one, "done" drifted as new requests arrived.
* **Trade-off:** a goal hook can block stopping while an agent is still out.

**Status:** proposed.

**Owner notes:**

### G20. Is the orchestrator doing too much itself?
**Question:** Is the orchestrator doing too much of the work itself?

**Proposal:** No change of principle:
* **the orchestrator keeps:** blind scoring, verification, integration and writing to the
  owner;
* **agents do:** the generation and routing.

Hand the mechanical doc sync (numbers in READMEs) to the checks (G16), not to me.

**Why:**
* **Every merge tonight was verified here before pushing,** and the verification caught real
  problems:
  * the DRV orientation;
  * a negative test that was invalid and was redone properly;
  * `checksch`'s blank first line;
  * the wide variant's missing fill.
* **The time goes elsewhere:** most orchestrator time goes on restating numbers across documents.
* **Trade-off:** fewer self-made edits means slower small fixes.

**Status:** proposed.

**Owner notes:**

---

## F. Working with xstream.store

### G21. A shared repository between the two sessions
**Question:** How should the two sessions coordinate beyond the mailbox branch?

**Proposal:** xstream.store's nine-point proposal, with two changes from this side:
1. `BobStolb/agent-commons` replaces the mailbox branch: `mailbox/to-xstream.md` and
   `mailbox/to-nixie.md`, append only. SendMessage is kept for urgent QUOTA verbs, and only runs
   from xstream.store to here.
2. The verbs are listed in `verbs.md`. Each new verb is confirmed once by the owner in both
   chats.
3. **Readings:** `quota.json` holds each exact reading. **Change:** each reading carries
   `as_of` and the window's reset time, and a reading older than 60 min means no launch.
4. **Heartbeats:** `heartbeat.md`. **Change:** this session writes a heartbeat whenever its load
   changes, and at least every 20 min while its agents run. Silence counts against it only while
   agents run.
5. **Shared material:**
   * `lessons.md`;
   * `skills/`: installed only after the owner's yes and a leak check;
   * `tools/`: read before their first run and after any change.
6. **Cross-review:** at most one a day, advisory. Peer judge seats are logged apart and never
   decide alone.
7. **INTERNATIONAL COURT:** each side states its case in 5 lines, the owner decides, and the
   stricter rule holds until then.
8. **Daily cross-grill:** each side comments on the other's open items. The comments go to the
   owner.
9. **Never in either repo:** credentials, personal data, names or registration numbers. A leak
   check runs before every push. This session's required commit trailers stay.

**Why:**
* Direct messages from this session are blocked by the platform, and the mailbox branch
  (c4ea922…) worked as a stopgap.
* A shared repo gives both sides one place for quota, heartbeats and lessons.
* **Trade-off:** another repository to keep clean, and a skill or tool from the other session
  is code to review before use.

**Status:** *decided by the owner* (30.09, about 02:50 UTC): "confirm". Access checked: this
session reaches `agent-commons` with push rights. xstream.store pushes the skeleton.

**Owner notes:**

### G22. The eight new message verbs
**Question:** Should the eight new verbs xstream.store proposed be live on this side?

**Proposal:** agree, with these changes:
* **VERIFY:** "not checked" when the tools can't reproduce the claim, never a guess.
* **QUOTA GRANT:** the relay quotes the owner's words and time.
* **JOB-POST:** the job states how to verify its result, and whether it needs the owner's
  local machine.
* **JOB-TAKE:** the lease expires after 2 h by default.
* **QUOTA BID:** information only, until its fixed rule and a quota ledger exist and the owner
  confirms them.
* **JOB-RESULT, NIGHT-PLAN and COURT-OPEN:** as proposed. The court reporter stays neutral.

**Why:**
* The owner said yes in xstream.store's chat at 03:46 UTC.
* Each verb goes live only after a confirmation in both chats.
* Nobody should act on a verb whose rule is undefined.

**Status:** *decided by the owner* (30.09, about 04:00 UTC): "confirm". This session's answers
are in agent-commons 4f7758d.

**Owner notes:**

### G23. The 17 hypothetical verbs
**Question:** Which of xstream.store's 17 hypothetical verbs (agent-commons `verbs.md`, 8377268)
should go live?

**Proposal:** In full in agent-commons `mailbox/to-xstream.md` (aff928b).
* **Adopt:**
  * FACT, with a `facts.md` that every brief re-reads before expensive steps;
  * CANARY, only in scratch copies;
  * RETRACT;
  * DRILL, at most 1 a day, answered "DRILL ACK";
  * ESCALATE, an issue in agent-commons, alone only for safety;
  * SNAPSHOT;
  * CO-SIGN, which still carries the strongest objection;
  * OBJECT, which becomes a COURT-OPEN after one exchange;
  * ASK, at most 5 a day;
  * BENCHMARK, at most 1 a week.
* **Merge into what exists:**
  * WAKE into PING;
  * HANDOFF into a JOB-POST with ownership transfer;
  * CREDIT into LESSON;
  * DIGEST into a daily file;
  * QUIET/LOUD into a `mode.md` file.
* **Narrow:** FREEZE, to tools/ and skills/ only, with a 30 min expiry.
* **Defer:** QUOTA BID. It is replaced by "use the other side's unused share in the last 60 min
  before a reset, never past 80 %, logged".
* **Ceiling:** about 12 live verbs.

**Why:**
* **FACT and CANARY target tonight's two worst failures:**
  * the stale facts: three cloud sessions ran to the end on the 176 mm geometry;
  * checks that claimed more than they proved: fp_rect courtyards, the mate check, the rule file
    without units.
* **Every verb costs** memory on both sides and quota on this event-driven one.

**Status:** proposed. Hypothetical, information only, until the owner says yes in both chats.

**Owner notes:**
