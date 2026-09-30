# TS06 orchestrator: resume note and launch log

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

Running at the time of the quota rule: 5 local agents and 1 cloud session (search) = 6 agents,
which is the cap. Nothing new will launch until some of them finish.

## Where things stand

* **Pushed to pcb/kicad-boards:**
  * the grill fixes:
    * fascia centred on the tube row;
    * trench wall, fascia silk ring and fill;
    * BOM corrections;
    * ИН-15 and HV-set values;
    * firmware: RTC writes, soft-start, A6 filter;
  * the test guide and the one-command check (19 PASS);
  * red-team fixes to the checkers;
  * the fascia variants W and R, with their comparison.
* **Waiting on the agents:**
  * DRV rev B: OV clamp, 0.8 mm HV pads, protection parts, МЛТ-0,5 footprints, L1, keep-outs, silk;
  * DISP silk and HV clearances;
  * schematics and highlighted layouts;
  * viewer v2 (three.js, assembly, steps, sections, variants);
  * case fixes and the frame variant F.
* **When each lands:**
  1. score it blind;
  2. cherry-pick it;
  3. run `tools/verify_pair.sh`;
  4. commit filled boards and a fab export after rev B;
  5. rebuild and republish the viewer (https://claude.ai/artifact/FzK6sTskEh2GvBRHAfNCBS).
* **The owner decides:** the fascia variant (recommended R, see `PCB/TS06-FASCIA-variants.md`).

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
