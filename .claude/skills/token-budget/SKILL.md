---
name: token-budget
description: Cost, usage-limit and context-size rules for Claude Code sessions in every project. Load it when a "[token-budget]" line appears, when choosing between working inline, delegating to subagents or asking the user to /compact, when writing a subagent brief, when estimating what a task costs or what share of the usage window it takes, and before searching the user's own files or other projects (ask for a screenshot first).
---

# Token budget

Every API step re-reads the whole context. So one step costs about context size × cache-read price, and a task costs about steps × context. Context size is the biggest lever, bigger than the choice of model.

## Gauge and hook
- `python3 ~/.claude/skills/token-budget/context.py` prints this session's context, the cost per step, the cost of a cold re-read, and the rule that applies. `--transcript <path>` gauges another session.
- The same script runs as a `UserPromptSubmit` hook (`--hook`, registered in `~/.claude/settings.json`), before each user message, in every project:
  - silent below 150k
  - prints a `[token-budget]` line to you when the context crosses 150k, 300k, and every +100k after that, and when the cache was cold
  - **block mode:** at ≥ 300k after ≥ 60 min idle, it pauses the user's first message once, shows them the cost, and saves the message (a file in the temp folder, plus the clipboard). Any second message goes through. Slash commands are never paused. The app's automatic message after a limit reset (config `auto_continue`) is never paused: nobody may be there to run /compact. Claude gets a note instead: keep the context lean and suggest /compact at the next task boundary.
- The number is the context of the last API call plus the visible text since. It lags one reply behind, which does not matter for these thresholds.
- Thresholds, and the dollars per 1% of the usage window, are in `config.json` next to the script. Hook activity is logged in `<temp>/claude-token-budget/runs.log`.

## Decide by context size
| Main context | Do |
|---|---|
| < 150k | Short tasks (≤ ~15–20 steps) inline. |
| 150–300k | Inline only for ≤ ~8 steps or for your own visual sign-off. Delegate the rest with a context pack. Aim for an agent context below a third of yours. |
| > 300k | Delegate most work. Suggest `/compact` at the next task boundary, after the resume notes are written. |

## Compaction and clearing
Both reset the context. They differ in what carries over.

| | `/compact` | `/checkpoint` → `/clear` → resume |
|---|---|---|
| Carries over | a summary of the chat, plus files | files only: CLAUDE.md, memory, the resume note |
| Start | about 90k, after 1–3 min | about 70k, in seconds |
| Cost of the reset (about 200k, warm cache) | about $0.35–0.40 | about $0.45–0.60 (write the note, read it back) |
| Each later step | about 20k more than after `/clear` (about +$0.004 per Opus step, +$0.40 per 100 steps) | baseline |
| Cold cache (idle longer than the cache TTL) | re-reads the whole context once at the write price first (about $1.5 at 200k) | avoids that re-read |

**Suggest `/compact`** (the default) when:
- the same line of work continues, and chat nuance matters that is not in files yet (an open discussion, preferences the user gave in chat)
- a background run is in progress (the session and its tasks continue)
- the cache is warm, for example right after a reply, before a short break.

**Suggest `/clear`** when:
- a milestone was just committed, and the resume note is current
- the user switches to an unrelated area
- the cache is cold after a long break, and the context is large
- AND no background run is in progress.

**Suggest neither** below 150k.

**How to suggest.** First write the resume note: decisions, state, next step, and what you wait on from the user. Then give one line of reason and copy blocks:
- `/compact`: one block with focus text:
  ```
  /compact keep: <the 2–4 things that must survive>
  ```
- `/clear`: three separate blocks, in order, with the resume note's absolute path. Leave out `/checkpoint` if you wrote the note in this turn.
  ```
  /checkpoint
  ```
  ```
  /clear
  ```
  ```
  continue from <absolute path of the resume note>
  ```

**Other rules**
- Only the user can run `/compact` or `/clear`.
- Keep the resume note lean: the "RESUME HERE" part at the top, 30 lines or fewer. Move history to a separate file, so the next session reads only the note.
- **Pasted screenshots are lost at both.** Save them at once (visual-qa skill, section 2).
- Hidden cost: everything you write (files written, long replies) stays in your context and is re-read on every later step. Long documents are cheaper when an agent writes them from a brief.

## Subagents: small contexts
An agent does not see your context. Before it reads anything, it starts at about 60k (measured 2026-09-26: the system prompt, the tool and connector lists, skills, CLAUDE.md and your brief). It grows with everything it reads. The pack controls only the growth, so keep that small:
1. **Write a context pack for every brief** (40–80 lines, 1–2k tokens), in the project's checkpoint folder if it has one:
   - the goal, with the user's words quoted verbatim
   - the exact files and line ranges to read (for example `normals.py:120-210`), and the instruction not to read whole large files
   - known facts and numbers, and the commands that work
   - the acceptance test, and the files the agent must not touch.
2. **Summaries, not dumps.** Give the agent scripts that print summaries. Long logs go to a file, and the agent reads the `tail`.
3. **Image budget** (this is its home, the value lives in the runbook). The agent combines comparisons into one image before it views them. Default 6 image reads, judges 10.
4. **Split diagnosis from fix.** The diagnosis agent writes its findings to its checkpoint. A new agent starts the fix from those findings.
5. **Pass paths, not reports.**
6. **Measure.** Judge a pack by the growth: the average context per step minus the first step. With packs, the growth was about 45–60k (two refactor agents, 2026-09-26). Without packs, it was 70–250k. Above about 60k of growth, the pack is too loose.
7. If the project has its own checkpoint or brief protocol, follow it. It takes priority over this section.

## Main-session habits (measured 2026-09-26: the main session was 85% of the spend in a design phase)
With Opus and the 1-hour cache, a token that enters your context costs $8 per million once, which is 40 times the price of one re-read. So:
- **Short replies in STE.** Answer first. Do not repeat what the user can see already.
- **Keep large inputs out of your context.** Read line ranges, and use `tail` and `cut`. Agents return 150 words or fewer. For visual sign-off, view one composite image, not many separate images.
- **Merge steps.** Put related checks in one command, and make independent calls in parallel. Each step re-reads the whole context.
- **Do not change the session model or effort in the middle of a session.** That can void the message cache, and then the whole context is written again. If a change is necessary, make it right after a compaction.
- **Reminders and progress (the user asked for them):**
  - Remind the user in one line when a habit applies: combine quick messages into one, approve a predictable chain of steps up front, `/compact` before a break, lean restart at a boundary.
  - At each milestone, report the token-saving progress in 2–3 lines: estimate against actual, agent start and growth, and your context size.
- **Talk before work.** Planning talk before a task is cheap (1–3 steps). Do not rush from a question into execution.
- **Estimate first, then compare.** Write the cost estimate of a task in the log before you start it. The expense-log skill adds the actual cost.

## Lean agent types (`~/.claude/agents/`)
`worker` (Read, Edit, Write, Bash, Grep, Glob, with Sonnet 5.5 `claude-sonnet-5-5`), `checker` (read-only, with Bash, Haiku), `researcher` (web only, Haiku). Create these files once yourself (frontmatter below). Use them with `agentType` in workflows, or `subagent_type` with the Agent tool. **Measured 2026-09-26: `worker` starts at 10k, the default agent at 54k**, for the same task. Prefer them for every pack-driven task. New agent files may need a moment to load: the first attempt reported "agent type not found". Give an agent only the tools its task needs.

**New lean agent types.** Most specialization belongs in the context pack, so try `worker` + a pack first. Create a new type only when:
- it needs a different tool set (an MCP server such as a CAD or EDA tool, or web tools)
- the same domain setup repeats in 3 or more briefs
- it needs another default model.
Write it to `<project>/.claude/agents/<name>.md` (that project only) or `~/.claude/agents/<name>.md` (all projects). Frontmatter: `name`, `description`, `tools` (the fewest that work), `model`. Body: the fixed domain rules, 30 lines or fewer. **It loads only in the next session.** Until then, use `worker` + the pack.

## Model and effort
Effort pays only when there are real decisions AND wrong steps are expensive to detect.
A project's own model rule (in its CLAUDE.md, runbook or memory) wins over this table.

| Work | Model, effort |
|---|---|
| Captures, mechanical checks with a clear pass/fail, when the commands are known to work | Haiku, low |
| Measurements or scans that must install or debug tools | Sonnet, medium. Two Haiku scans (2026-09-26) failed on tool errors and returned partial results |
| Research (ask for verbatim quotes with URLs) | Haiku, medium |
| Build to a written spec | Sonnet, medium |
| Diagnosis | Sonnet, high. Escalate to Opus if it goes in circles |
| Visual sign-off | You, on 2x crops. Never accept an agent's visual verdict |

Prices, in USD per million tokens. This table is a summary. The single source is `context.py` `PRICES`, which also lists Fable 5.1 and Opus 5:

| Model | Cache read | Output |
|---|---|---|
| Opus 5.5 | 0.20 | 20 |
| Sonnet 5 | 0.20 | 10 |
| Haiku 4.5 | 0.10 | 5 |

A cache write costs 1.25× the input price (5 min cache) or 2× (1 h cache). Opus and Sonnet re-reads cost the same, so a shorter Opus run can cost the same as a longer Sonnet one.

## Verify in proportion to the stakes
- Re-check an agent's claim when a decision, a commit or a figure that other people will see depends on it.
- For general-interest answers, pass the claim on with a caveat. Do not re-fetch what an agent already quoted with its source.

## The user as an agent
- **Ask for a screenshot before any file hunt** in the user's own projects or folders (this is its home). A screenshot with 1–2 lines costs about 2–3k tokens. A search costs 10–50k.
- The user is often the cheapest worker for visual judgement, parameter search in a GUI tool, real devices, and people. Give them a human task card (visual-qa skill, section 8). Turn what they find into a script.

## Quota
- Usage limits cover the whole account: a 5-hour window and a weekly limit, shared with claude.ai chat.
- **Exact numbers (desktop app):** the `get_usage` tool (`mcp__ccd_session_mgmt__get_usage`) returns the % used of the 5-hour and weekly limits with their reset times, plus this session's context by category. Check it before you launch a workflow or a long task, and when a background run finishes. The hook cannot call it. If the tool is deferred, load it with ToolSearch.
- **After each reading, record it:** `context.py --record-usage <5-hour %> <weekly %> --resets <5-hour resetsAt> --weekly-resets <weekly resetsAt>`. The hook and the watcher estimate from the last reading plus the spend logged since, in all projects. The estimate cannot see claude.ai chat or other machines, so it can only read low: confirm it with `get_usage`. When an earlier reading in the same window exists, the command prints a calibration ($ per 1%). Copy it into `config.json` once the change is 10% or more.
- **You cannot act between turns.** A turn starts only on a user message, on a finished background task, or when a background command exits. An instruction such as "check every 30 minutes" cannot wake you.
- **Usage watcher:** when you launch a long background run, also start `python3 ~/.claude/skills/token-budget/context.py --watch` as a background command. It exits at an estimated 85%, or after 60 minutes, and its exit wakes you. Then read `get_usage` and record it. At 90% or more, run the `checkpoint` skill. Below that, restart the watcher. Each wake costs one short turn.
  - **Pace mode:** add `--pace --queue <tasks.md>`. A pace line runs from 0 at the weekly window start to 90% at the weekly reset. It is a gauge, not a spend target. The daily cap in the runbook decides launches.
  - `PACE BEHIND`: 5+ points below the line, a READY row in `## Ready queue`, no agent write for 5 min. Start that row only if the WIP gate (commit-gate) and the daily cap allow it. Never burst to catch up.
  - `PACE AHEAD` (10+ points above the line): use fewer parallel runs and skip optional checks.
  - The same wake does not repeat within 60 min (`--pace-snooze`). Each check writes `pace.json` to the state dir. `--watch --once --pace` prints the status once.
- The user can type `/checkpoint` at any time. It runs the same procedure.
- `config.json` holds the measured dollars per 1% of the 5-hour window. Recalibrate it after a plan change: take one turn's API-equivalent cost from the gauge and divide it by the % that turn used.
