# Recovered work of two agents lost on 30.09.26

Two of the orchestrator's agents went silent on 30.09.26 between 02:27 and 02:33 UTC. The platform
later reported them as "stopped by the user", but the owner stopped nothing. **The likely cause:** a
message from the owner reached the orchestrator as "[Request interrupted by user]" at about 02:28.
That interrupt ends the orchestrator's turn, and the platform stops the background agents with it.

The evidence:
* The viewer agent's last screenshot is timestamped 02:27:06.
* The layout agent's router wrote its last round at 02:33:26.
* The only agents lost were the two still running at that moment. Every other agent that night had
  finished earlier.

Both agents' work is kept here, in full, so a successor can pick it up.

## TS06-DRV rev B (the layout agent)
**Mission:** the driver board's revision B, all the review's open items:
* an independent over-voltage clamp;
* 0.8 mm at bare 185 V pads, as a KiCad rule;
* the USB back-feed diode and the input TVS;
* the fascia-input RC and pull-down;
* МЛТ-0,5 footprints;
* a real L1;
* the RTC's male header;
* keep-outs at the mounting holes;
* the silkscreen legends.

**Done:**
* `patches/0001`: the tools. The HV pad rule, the hole keep-outs and the DNP attribute.
* `patches/0002`: the rev B netlist and footprints. The OV clamp, the protection parts, МЛТ-0,5
  and L1.
* `patches/0003`: the recovered work in progress: `tools/mkpcb_drv.py` (+446/−93 lines) and the
  README, uncommitted when the agent was lost.

**Left unfinished:** the routing.
* Run r1 stalled at 5 nets sharing after 45 rounds.
* Run r2 was at 4 nets sharing after round 15: +5V, D8, GND and SCL. See `scratch/route-r*.log`.
* The congestion sits round J1, where the fascia link now carries the new 1 k + 10 nF on D7/D8 and
  1 M on A6.
* The agent was re-placing parts when it was lost. See `scratch/diag*.log`, `scratch/region.py`
  and `scratch/clamp.py`.

**To resume:**
1. Start a worktree from `pcb/kicad-boards`.
2. `git am recovered/drv-revb/patches/*.patch`.
3. Place, then route. The saved route no longer matches the netlist.

## Viewer v2 (the page agent)
**Mission:** rebuild the board viewer in three.js:
* camera buttons, with dragging that works;
* the assembled stack in its case, with an explode slider;
* an 18-step build and bring-up walkthrough;
* the schematic sections;
* the fascia variants A/W/R/F;
* a black mask with white silkscreen.

**Done:** the page and its build.
* `index.html` and `app.js` are the built page.
* `src/` is the source.
* `tools/` holds the exporters: `kicad_export.sh`, `glb2json.py`, `assembly.py`, `stl2gltf.py`,
  `kparts.py` and `sections.py`.
* `test/` holds its Playwright tests.
* `build.sh` rebuilds everything from the repo's boards. The built assets (about 26 MB) are not
  kept here.

**Left unfinished:** its last run of the final tests, and the rebuild from the latest boards. It was
built from f376a3b, before TS06-DISP rev B's silkscreen was merged.

## Lessons (also in agent-commons lessons.md)
* Interrupting the orchestrator's turn stops its background agents. So:
  * finish or checkpoint long runs before an interrupt;
  * a long agent commits work in progress at least every 30 minutes, so a loss costs at most 30
    minutes.
* An agent's report of "stopped by the user" isn't proof that the owner stopped it. Check the
  timeline.
