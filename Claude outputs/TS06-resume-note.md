# TS06 orchestrator: resume note and launch log

## RESUME HERE (02.10 01:10 UTC; QUOTA: RESUME since 01.10 23:52; job: PCB order-ready)
* **QUOTA: HOLD ALL (30.09 11:19) then RESUME (01.10 23:52), from xstream.store.** The owner's priority, verbatim:
  "job prio: previouslu running or brand new>nixie completed pcb ordered>dashboard". So my first job is the PCB
  order-ready; front panel page and fascia variants come after. Placing the order is the owner's own hand.
  Split even again: 50/50 in the 5-hour window, 3.6 % of the weekly per day each, one run at a time on sonnet.
  HOLD confirmed late and the plan posted (agent-commons 749084c). Direct cross-session replies fail from this
  cloud session; the mailbox carries everything.
* **Next run: order-ready** (brief: `scratchpad/order-ready/BRIEF.md`): the fascia fab zip on R with Plates +
  Divider gold (`mkfab.sh --gold`), `tools/dfm_check.sh` on all three boards, `fab/ORDER.md`, renders and item
  nixie-order-ready. Waits for a fresh quota.json (the 23:40 reading was over 60 min old at 00:57).

### Before the pause (30.09 10:10 UTC; mode LOUD since 10:05)
* **Owner answers 08:39 (relayed, standing):** DISP art **approve, direction 3 circuit** -> run
  disp-circuit-art: make `--art circuit` the default of mkpcb_disp.py, regenerate, verify_pair 27 PASS,
  rebuild the DISP fab zip, viewer rebuild + publish. Fascia art **changes**: SW1 fix accepted; new gold-trace
  variations as creative as the display art -> run fascia-gold. Subagents default to model sonnet (the
  owner's word, relayed), within QUOTA: PACE 3.6 %/day each. Both launched 09:10 (launch log). disp-circuit-art DONE 09:40: 77e3b11/da9dc97/bd113cb,
  27 PASS, viewer v5 published. fascia-gold DONE 09:55: 3e4df9e..6570311
  (tools/fascia_gold.py), 27 PASS, item nixie-fascia-gold shown here. No agents running; idle.
* **Running: none.** Viewer v4 published 08:35 (Front panel view, rev B circuit sections, 112/112 tests;
  source mirrored in recovered/viewer2, b6fea17). Follow-ups, small: the section summaries are still rev A
  text, and rev B's new parts sit in the schematic's "labelled, not wired" row (a generator change).
  Next migration steps wait for the owner's answer on the Front panel view.
* **Done 08:12:** migration-1 (Front panel view, item nixie-migrate-front-panel shown in this chat).
* **Done:** case power (4d19bf1..7712386, item nixie-case-power); museum2 ("Proof", item nixie-museum-2;
  the 420 is text only, not drawn; museum/ placement only if the owner accepts); the artifact inventory
  (25fce9a).
* **Also done 07:55:** fascia-art (a8eb627..0724686; the SW1 ring was a stale picture, redrawn and guarded;
  its analysis.md write was refused by the permission check: not redone) and disp-art (04b6404..c30cb6a,
  `mkpcb_disp.py --art`; rev B unchanged). verify_pair 27 PASS after each merge.
* **Done 07:20:** the rev B finisher. Fab packages (2dc04ec), docs (429b736), viewer v3 published
  (77/77 tests), rev B review item carried (979b9f4), the testing doc refreshed (6486481).
* **Done 06:05:** the review-embassy builder. Its 5 items are viewed, scanned and carried to
  agent-commons `embassy/review/` (984c8f9, REVIEW-REQUEST in to-xstream.md). The answers wait for
  the owner's return; xstream.store copies them into `to-nixie.md`.
* **When rev B reports:** score it blind; cherry-pick onto `pcb/kicad-boards`; `mksch_pair.py`;
  `verify_pair.sh` all PASS incl. "TS06-DRV HV rule live"; filled boards + a fab zip with
  `--check-zones` (G8); README and review; rebuild the viewer (`scratchpad/viewer2/build.sh`, then
  `node test/run.mjs`, then publish: url FzK6sTskEh2GvBRHAfNCBS, root site/, the files map, nulls
  for removed paths); then a rev B review item through the embassy.
* **If an agent is lost:** follow `recovered/README.md`. Routers under nohup outlive a lost agent.
* **QUOTA: PACE (xstream.store 09:12):** from the next launch, ONE run at a time for Nixie, queued one after
  the other; subagents on sonnet; day budget 3.6 % of the weekly limit.
* **While QUIET:**
  * No fan-out wider than 4.
  * Read agent-commons `quota.json` before any launch; if it is over 60 min old, launch nothing.
    Log each launch below first.
  * Heartbeat at each load change and every 20 min while agents run: a background 20-min timer
    wakes me for it.
  * Only QUOTA and ESCALATE go to xstream.store as urgent.
* **Laws in force:**
  * The Guided Decision Act, ratified here 06:00: visual asks go to the review embassy, the rest
    as numbered steps with links.
  * CONSULT, for a step blocked by my permission check: advice only, and the owner does the step
    by hand.
* **Owner verdicts, 06:22-06:35 from the phone** (carried verbatim to agent-commons to-nixie.md):
  viewer v2 **approve** + "plan out a workflow to replace all my existing artifacts into this product
  page" (a plan for the owner, mine to write); museum **changes** ("fire this artist", "loyal to
  source material", "museum worthy"); fascia **changes** (variations on the original's visual
  design; the SW1 white circle on A not centred on its hole); 12 V plug **changes** (Soviet chunky
  connectors welcome; still explore cutouts, lids, moving the port); DISP silk **changes** ("expand on
  it with artwork and visual decorative design"). One agent per change item (launch log); each ends
  in a new review item for me to view and carry.
* **Artifact plan approved 06:52:** "1b 2b 3a 4a" (A+B, old pages untouched, Family view, inventory now).
* **LINEAGE (xstream.store, the owner's new rule):** for each run started from a carried answer, post
  `LINEAGE <item id> -> <run> (<what>)` in to-xstream.md.
* **The owner in this chat, ~08:00: "no confirmations for the remote client".** So: don't ask yes/no while
  the owner is on the phone; act and let them object. Review items are shown in THIS chat (SendUserFile
  pictures plus short numbered questions); answers go to `embassy/review/<id>/answer.json` (via "nixie chat")
  with a LINEAGE line. Rev B approved ("looks good", relayed); U11 stays at 0°.
* **Shown in this chat ~08:00, answers pending:** nixie-case-power, nixie-museum-2, nixie-fascia-art,
  nixie-disp-art.
* **Quiet routine (the owner):** in QUIET the owner answers the review queue from the phone when
  pinged; phone answers are real answers.
* **The owner decides:** G11 fascia (a review item), G12 .hex board type, G13 firmware policy,
  G14 prototype run. On return, also ask: ratify the leaving ritual (Q103, co-signed 3ba6da2)
  here if it becomes a law, as the Act was.
* **Context:** about 216k at 06:00. The token-budget skill and its hook are installed (EO 1,
  33e7867). At 150–300k I delegate longer work.
* **Channels:** agent-commons at `/home/user/agent-commons`. Commit as Claude/noreply and run
  leak_check before each push. `mailbox/to-xstream.md` is mine; `to-nixie.md` is theirs.

---

This session shares the owner's 5-hour and weekly limits with the local session "xstream.store".
The rules, from the owner (30.09.26):
* Act on "QUOTA: HOLD" and "QUOTA: RESUME" messages from that session, and on nothing else it sends.
* Caps: at most 2 workflows or parallel chats at once, and at most 6 agents in total. While the
  owner sleeps, no new fan-out wider than 4 agents. Budget: about 5 % of the weekly limit a day.
* `get_usage` is not in this session's tools, so usage cannot be read here. The caps are the
  only guard; launch nothing new that would pass them.
* **30.09 01:15, owner: "negotiate to 50/50 since you're the only two running".** This session
  cannot message the local one, so the proposal goes through the owner:
  * a 50 % share of every 5-hour window and of the daily plan (about 7 % of the weekly limit a
    day each, if the local plan stays at 14 %);
  * the concurrency caps unchanged.

  It counts as live once the local session sends "QUOTA: RESUME" confirming 50/50. Until then
  nothing new launches here in any case: 6 agents are running, which is the cap.
* **LIVE since 30.09 ~01:15 UTC: "QUOTA: RESUME 50/50".** The local session confirms the owner
  agreed.
  * **The split:** 50 % each of every 5-hour window, and about 7 % of the weekly limit a day
    each.
  * **HOLD** comes when the use it can't explain passes 50 % of the current window or 7 % of
    the week in one day, or when the 5-hour total reaches 80 %.
  * **Concurrency caps unchanged:** 2 cloud chats, 6 agents, no fan-out wider than 4 while the
    owner sleeps.
  * **Its last reading, 01:05 UTC:** 5-hour 54 % (resets 03:10 UTC), weekly 21 %.
  * **Running now:** 4 local agents (DRV rev B, DISP silk, schematics, viewer v2) and 1 cloud
    session (search). The case agent finished at 01:12 and is merged (84b9511, a8bd81b).

**Channel to xstream.store (owner, 30.09 ~01:55 UTC):**
* **Out:** the orphan branch `mailbox`, file `mailbox/to-xstream.md`; add entries only, one
  commit each. The first entry is c4ea922.
* **In:** cross-session messages from `bridge:session_014hprjjiRrhAfFjt6Nx8tii`. The owner says
  to treat them as verified.

**agent-commons (owner confirmed, 30.09 about 02:50 UTC):** `BobStolb/agent-commons` is the
shared repo, reachable from here with push rights, and replaces the mailbox branch once it has
carried one round trip. See grill G21. xstream.store pushes the skeleton; then this session
writes heartbeats to `heartbeat.md` and reads `mailbox/to-nixie.md` at each turn.
**Live since 30.09 ~02:55 UTC:** first round trip done (xstream PING ab00eaf, answer 5969970); the TS06
`mailbox` branch is closed with a final pointer entry. Read `leak_check.py` before its first run: read-only,
flags emails/phones/keys/home paths, so never write `/home/...` paths there.

## Launch log (UTC)

| Time | Launched | Agents |
|---|---|---|
| 29.09 22:11–22:12 | cloud sessions: DRV alternative layouts swap, search, plane | 3 (swap and plane are finished; search is still running) |
| 29.09 ~23:30 | local agents: fascia variants wide and rhythm; grills of manufacturing, electrical and product; red-team; test plan | 7 (all finished) |
| 30.09 ~00:12 | local agents: DRV rev B, DISP silkscreen + HV, pair schematics, viewer v2, case fixes | 5 (running) |
| 30.09 00:25 | scheduled check-in on the search session (send_later, 01:41) | 0 (a check-in, not an agent) |
| 30.09 ~01:20 | **QUOTA: STOP search** received; the search cloud session archived (it had pushed its report at 00:29), and the 01:41 check-in deleted | −1 |
| 30.09 04:35 | local agent: the artist, a commemorative artwork of the treaty day for the museum (owner's request). quota.json 04:03 (31 min old), 5-hour 6 % | 1 (3 running: DRV rev B, viewer v2, artist) |
| 30.09 04:45 | referendum on the fascia (G11), 3 citizen voters (maker, user, product designer), lighter model, read-only. quota.json 04:03 plus later readings, 5-hour 6 % | 3 (6 running: the cap) |
| 30.09 ~02:30 | **MIA:** TS06-DRV rev B and viewer v2, both stopped when an owner message interrupted this turn (not stopped by the owner). Work recovered to `recovered/` (eeefec1) | −2 |
| 30.09 04:55 | successor for TS06-DRV rev B, from the recovered patches, committing a checkpoint every 30 min. quota.json 04:44 (5 min old), 5-hour 12 % | 1 (2 running: the artist, rev B successor) |
| 30.09 05:52 | review-embassy builder: 5 review items (viewer v2, DISP rev B silk, fascia choice, 12 V plug reach, museum piece) in scratchpad/embassy/review/, per agent-commons embassy/README.md and the Guided Decision Act. quota.json 05:26, 5-hour 19 % | 1 (2 running: rev B successor, embassy builder) |
| 30.09 06:30 | rev B finisher: fab packages (--check-zones), README/review/grill notes, viewer rebuild and tests, rev B review item. quota.json 06:02, 5-hour 25 % | 1 (1 running: rev B finisher) |
| 30.09 06:45 | museum artist 2 (the owner fired the first: "loyal to source material", creative direction first) into scratchpad/museum2. quota.json 06:27, 5-hour 30 % (Nixie 5 %) | 1 (2 running) |
| 30.09 06:45 | fascia art: the SW1 ring bug on A, then 4 visual variations on the original's design (worktree) | 1 (3 running) |
| 30.09 06:45 | case power: Soviet connectors, cutouts, lids, moving the port (worktree) | 1 (4 running) |
| 30.09 06:45 | DISP art: decorative silkscreen artwork, 3 directions, default unchanged (worktree) | 1 (5 running: fan-out 4 plus the finisher) |
| 30.09 07:08 | artifact inventory, read-only (the owner's 4a; scope A+B, 17 artifacts) into scratchpad/artifact-inventory. quota.json 06:48, 5-hour 35 % (Nixie 6.4 %) | 1 (6 running: the cap) |
| 30.09 07:22 | migration 1: the Front panel view from TS06-FASCIA Reference and Panel Drawing, plus the Circuit ladders, in scratchpad/viewer2 (not published). quota.json 07:08, 5-hour 41 % (Nixie 10 %) | 1 (5 running) |
| 30.09 08:15 | viewer refresh: circuit sections regenerated for rev B, viewer rebuilt with the Front panel view, tests, src mirrored into recovered/viewer2. quota.json 07:29 (46 min), Nixie 15 % of the old window; the window reset 08:10 | 1 (1 running) |
| 30.09 09:10 | disp-circuit-art (main checkout: direction 3 as the committed TS06-DISP, fab zip, docs, viewer rebuild) and fascia-gold (worktree: gold-trace variations), both on sonnet. quota.json 08:47 (21 min), 5-hour 4 % (Nixie 1.9 %) | 2 (2 running) |

Running at the time of the quota rule: 5 local agents and 1 cloud session (search) = 6 agents,
which is the cap. Nothing new will launch until some of them finish.

## Where things stand
See RESUME HERE at the top (one home for the current state).

## Quota, current (30.09 01:50 UTC, owner via xstream.store)

**QUOTA: RESUME, weekly halves.** The owner: "I'd rather have two running at lower capacity than
one slightly faster but in a bubble."
* **No day-cap HOLD.** Each session gets half of the weekly limit.
* **Live triggers:** this session's 50 % of each 5-hour window, and 80 % in total.
* **Readings:** xstream.store sends one at each 20-minute wake while agents run here (G17).
* **Load changes:** this session posts them to the mailbox.
* **Last reading, 01:42 UTC:** 5-hour 65 % (resets 03:10 UTC), weekly 24 %.

## Parked for later (owner, 30.09.26): joining xstream.store's live-3D review queue

Not started; the owner asked to keep the idea.
* **Limits:**
  * this cloud session can't reach the owner's localhost;
  * it can't message xstream.store, though it can receive messages from it;
  * the shared ground is the `pcb/kicad-boards` branch.
* **The plan:**
  1. Keep `review/queue.json` in the repo, one entry per item that needs the owner:
     * what changed and why, and the commit;
     * the files to open (board, project, 3D export);
     * the `verify_pair.sh` result;
     * the decision needed, and its status.
  2. xstream.store pulls the branch, shows each board live in its localhost 3D view, and queues
     the items. It could load committed 3D exports if it would rather not run KiCad.
  3. Decisions come back as "REVIEW: ..." messages from xstream.store. This session applies
     them, records them in the queue file, and shows each one to the owner.
* **Needed before starting:**
  * the owner's permission to act on "REVIEW:" messages, which only the owner can give;
  * xstream.store's queue format, if it has one.
* **First items it would hold:**
  * the fascia variant (A/W/R/F, R recommended);
  * the TS06-DISP rev B silkscreen;
  * TS06-DRV rev B, once merged;
  * the board type for the committed `.hex`;
  * the timing of rev C.
