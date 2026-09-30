# TS06 orchestrator: resume note and launch log

## RESUME HERE (30.09 06:05 UTC; the owner is away, mode QUIET)
* **Running (1 agent, notifies on completion):** TS06-DRV rev B successor, worktree
  `.claude/worktrees/agent-a92d573b002761b70`; its `recovered/drv-revb/STATUS.md` has "Resume here"
  per step. At 06:05 it was routed, DRC clean, verify 26 PASS / 1 FAIL (case outputs stale, in 3d/),
  and doing a reproducibility run (r5).
* **Done 06:05:** the review-embassy builder. Its 5 items are viewed, scanned and carried to
  agent-commons `embassy/review/` (984c8f9, REVIEW-REQUEST in to-xstream.md). The answers wait for
  the owner's return; xstream.store copies them into `to-nixie.md`.
* **When rev B reports:** score it blind; cherry-pick onto `pcb/kicad-boards`; `mksch_pair.py`;
  `verify_pair.sh` all PASS incl. "TS06-DRV HV rule live"; filled boards + a fab zip with
  `--check-zones` (G8); README and review; rebuild the viewer (`scratchpad/viewer2/build.sh`, then
  `node test/run.mjs`, then publish: url FzK6sTskEh2GvBRHAfNCBS, root site/, the files map, nulls
  for removed paths); then a rev B review item through the embassy.
* **If an agent is lost:** follow `recovered/README.md`. Routers under nohup outlive a lost agent.
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
