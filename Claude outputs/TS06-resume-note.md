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

## Launch log (UTC)

| Time | Launched | Agents |
|---|---|---|
| 29.09 22:11–22:12 | cloud sessions: DRV alternative layouts swap, search, plane | 3 (swap and plane are finished; search is still running) |
| 29.09 ~23:30 | local agents: fascia variants wide and rhythm; grills of manufacturing, electrical and product; red-team; test plan | 7 (all finished) |
| 30.09 ~00:12 | local agents: DRV rev B, DISP silkscreen + HV, pair schematics, viewer v2, case fixes | 5 (running) |
| 30.09 00:25 | scheduled check-in on the search session (send_later, 01:41) | 0 (a check-in, not an agent) |

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
