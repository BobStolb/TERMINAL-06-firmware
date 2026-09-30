"""Tests for context.py --watch --pace (stdlib only, no network).

Run:  python3 ~/.claude/skills/token-budget/tests/test_pace.py -v
Each test uses a temp state dir, a fake home (USERPROFILE and HOME), fixture readings and --now,
so real transcripts, real agents and the real state dir never count.
Rule for new fixtures: --now fakes the clock, but calls_since and active_agents compare it with real
file mtimes. Set every fixture mtime relative to --now with os.utime (see spend() and agent()).
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(SKILL, "context.py")
_spec = importlib.util.spec_from_file_location("tb_context", SCRIPT)
ctx = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ctx)
CFG = ctx.load_config()
PER_WEEKLY = CFG["usd_per_weekly_percent"]
TRIGGER = CFG["quota"]["watch_trigger_pct"]
UTC = timezone.utc
WEEK_START = datetime(2027, 1, 1, tzinfo=UTC)  # far in the future: no real call can count
RESET = WEEK_START + timedelta(days=7)
MID = WEEK_START + timedelta(days=3.5)  # line = 45.0 exactly
KEYS = {"ts", "weekly_est", "line", "delta", "week_start", "weekly_reset", "five_hour_est", "next_ready", "state"}

QUEUE = """# Tasks
## Tasks
1. **X1**: outside the queue section. State: READY.

## Ready queue

Intro text.

1. **T19**: the layout step. Pack: `checkpoints/t19/pack.md`. State: WAITING (the user's pick).
2. **T20**: the second item (with parens). Pack: `p.md`. State: READY.
3. **T21**: third. State: READY (pack to write).

## Order of work
1. **Z9**: after the section. State: READY.
"""
QUEUE_NONE = QUEUE.replace("State: READY", "State: DONE")


def iso(t):
    return f"{t:%Y-%m-%dT%H:%M:%SZ}"


def line_at(now):
    return 90 * (now - WEEK_START).total_seconds() / (7 * 86400)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="tb-pace-")
        self.home = os.path.join(self.tmp, "home")
        self.sdir = os.path.join(self.tmp, "state")
        self.subagents = os.path.join(self.home, ".claude", "projects", "proj", "sess", "subagents")
        os.makedirs(self.subagents)
        self.queue = os.path.join(self.tmp, "tasks.md")
        self.queue_none = os.path.join(self.tmp, "tasks_none.md")
        for path, text in ((self.queue, QUEUE), (self.queue_none, QUEUE_NONE)):
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def reading(self, weekly, at, five=10, weekly_resets=RESET):
        os.makedirs(self.sdir, exist_ok=True)
        with open(os.path.join(self.sdir, "usage.json"), "w", encoding="utf-8") as f:
            json.dump({"time": iso(at), "five_hour_pct": five, "weekly_pct": weekly,
                       "five_hour_resets": iso(at + timedelta(hours=3)),
                       "weekly_resets": iso(weekly_resets) if weekly_resets else None}, f)

    def spend(self, at, usd_out_tokens=1_000_000):
        """One logged Opus 5.5 call at `at` (1M output tokens = $20 at list price)."""
        path = os.path.join(self.home, ".claude", "projects", "proj", "main.jsonl")
        usage = {"input_tokens": 0, "output_tokens": usd_out_tokens, "cache_read_input_tokens": 0,
                 "cache_creation_input_tokens": 0}
        with open(path, "w", encoding="utf-8") as f:
            f.write(json.dumps({"type": "assistant", "timestamp": iso(at), "message": {
                "id": "msg1", "model": "claude-opus-5-5", "usage": usage, "content": []}}) + "\n")
        os.utime(path, (at.timestamp(), at.timestamp()))  # calls_since skips files older than the reading
        return ctx.call_cost("claude-opus-5-5", usage)

    def agent(self, now, age_s, name="agent-a1.jsonl"):
        path = os.path.join(self.subagents, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write("{}\n")
        t = now.timestamp() - age_s
        os.utime(path, (t, t))

    def run_pace(self, now, *extra, once=True, queue="ok", timeout=60):
        args = [sys.executable, SCRIPT, "--watch", "--pace", "--no-clipboard", "--state-dir", self.sdir,
                "--now", iso(now)] + (["--once"] if once else [])
        if queue:  # "ok", "none" or a path
            args += ["--queue", {"ok": self.queue, "none": self.queue_none}.get(queue, queue)]
        env = dict(os.environ, USERPROFILE=self.home, HOME=self.home)
        p = subprocess.run(args + list(extra), capture_output=True, text=True, encoding="utf-8", env=env,
                           timeout=timeout)
        self.assertEqual(p.stderr, "", p.stderr)
        pace = ctx.load_json(os.path.join(self.sdir, "pace.json"))
        return p.returncode, p.stdout.splitlines(), pace


class TestPaceMath(Base):
    """Acceptance 1: the pace math at 4 fixture times (+ a reading from the previous week)."""

    def check(self, pace, now, weekly):
        self.assertTrue(KEYS <= set(pace), set(pace))
        self.assertEqual(pace["ts"], iso(now))
        self.assertEqual(pace["week_start"], iso(WEEK_START))
        self.assertEqual(pace["weekly_reset"], iso(RESET))
        self.assertAlmostEqual(pace["weekly_est"], weekly, delta=0.006)
        self.assertAlmostEqual(pace["line"], line_at(now), delta=0.006)
        self.assertAlmostEqual(pace["delta"], weekly - line_at(now), delta=0.006)
        self.assertAlmostEqual(pace["hours_to_reset"], (RESET - now).total_seconds() / 3600, delta=0.006)

    def test_1_start_of_week(self):
        now = WEEK_START
        self.reading(0, now)
        code, out, pace = self.run_pace(now)
        self.check(pace, now, 0)
        self.assertEqual((pace["line"], pace["hours_to_reset"], pace["state"], pace["wake"]), (0, 168, "ON_PACE", "ONCE"))
        self.assertEqual(code, 0)
        self.assertTrue(out[0].startswith("watch ONCE: "), out)
        self.assertTrue(out[1].startswith("pace: weekly ~0.0% vs pace line 0.0% (+0.0 points), 168.0 h"), out)

    def test_2_mid_week_behind(self):
        now = MID
        self.reading(30, now - timedelta(hours=2))
        usd = self.spend(now - timedelta(hours=1))
        self.assertAlmostEqual(usd, 20.0, places=6)
        code, out, pace = self.run_pace(now)
        weekly = 30 + usd / PER_WEEKLY
        self.check(pace, now, weekly)
        self.assertEqual(pace["line"], 45.0)
        self.assertEqual((pace["state"], pace["wake"]), ("BEHIND", "BEHIND"))
        self.assertEqual(pace["next_ready"], {"id": "T20", "text": "the second item (with parens). Pack: `p.md`"})
        self.assertEqual(code, 0)
        self.assertTrue(out[0].startswith(f"PACE BEHIND: weekly ~{weekly:.1f}% vs pace line 45.0% "
                                          f"({weekly - 45:+.1f} points), 84.0 h to the weekly reset"), out)
        self.assertTrue(out[0].endswith("Start the first READY item: T20: the second item (with parens). Pack: `p.md`."), out)

    def test_3_mid_week_ahead(self):
        now = MID
        self.reading(60, now - timedelta(hours=2))
        code, out, pace = self.run_pace(now)
        self.check(pace, now, 60)
        self.assertEqual((pace["delta"], pace["state"], pace["wake"]), (15.0, "AHEAD", "AHEAD"))
        self.assertTrue(out[0].startswith("PACE AHEAD: weekly ~60.0% vs pace line 45.0% (+15.0 points)"), out)
        self.assertIn("fewer parallel runs", out[0])

    def test_4_one_hour_before_reset(self):
        now = RESET - timedelta(hours=1)
        self.reading(88, now - timedelta(minutes=30))
        code, out, pace = self.run_pace(now)
        self.check(pace, now, 88)
        self.assertAlmostEqual(pace["line"], 90 * 167 / 168, delta=0.006)  # 89.46
        self.assertEqual((pace["hours_to_reset"], pace["state"]), (1.0, "ON_PACE"))
        self.assertEqual(pace["wake"], "TRIGGER")  # the old 85 % rule still wakes first
        self.assertTrue(out[0].startswith(f"watch TRIGGER (>= {TRIGGER:g}%): "), out)
        self.assertTrue(out[1].startswith("pace: weekly ~88.0% vs pace line 89.5% (-1.5 points), 1.0 h"), out)

    def test_5_reading_from_previous_week(self):
        now = WEEK_START + timedelta(days=1.5)
        self.reading(70, WEEK_START - timedelta(days=1), weekly_resets=WEEK_START)
        code, out, pace = self.run_pace(now)
        self.check(pace, now, 0)  # the window rolled over: the estimate restarts at 0
        self.assertEqual(pace["state"], "BEHIND")

    def test_6_units(self):
        a = {"weekly_resets": iso(RESET)}
        self.assertEqual(ctx.week_bounds(a, WEEK_START), (WEEK_START, RESET))
        self.assertEqual(ctx.week_bounds(a, RESET), (RESET, RESET + timedelta(days=7)))  # at the reset: next week
        self.assertEqual(ctx.week_bounds(a, WEEK_START - timedelta(seconds=1)), (WEEK_START - timedelta(days=7), WEEK_START))
        self.assertIsNone(ctx.week_bounds({"weekly_resets": None}, MID))
        self.assertEqual(ctx.pace_line(WEEK_START, MID, 90), 45.0)
        self.assertEqual(ctx.pace_line(WEEK_START, RESET + timedelta(hours=5), 90), 90.0)
        self.assertEqual(ctx.pace_line(WEEK_START, WEEK_START - timedelta(hours=5), 90), 0.0)
        self.assertEqual(ctx.first_ready(self.queue)["id"], "T20")
        self.assertIsNone(ctx.first_ready(self.queue_none))
        self.assertIsNone(ctx.first_ready(os.path.join(self.tmp, "missing.md")))
        self.assertIsNone(ctx.first_ready(None))


class TestWakeRules(Base):
    """Acceptance 2: each wake fires only when its condition holds; flip one input and it goes away."""

    def behind(self, weekly=30):
        self.reading(weekly, MID - timedelta(hours=2))

    def test_behind_fires(self):
        self.behind()
        code, out, pace = self.run_pace(MID)
        self.assertEqual((code, pace["wake"]), (0, "BEHIND"))
        self.assertTrue(out[0].startswith("PACE BEHIND: "))

    def test_behind_margin(self):
        self.behind(41)  # 4 points below the line < 5
        code, out, pace = self.run_pace(MID)
        self.assertEqual((pace["state"], pace["wake"]), ("ON_PACE", "ONCE"))
        self.assertTrue(out[0].startswith("watch ONCE: "))
        self.behind(40)  # exactly 5 points below: fires
        self.assertEqual(self.run_pace(MID)[2]["wake"], "BEHIND")

    def test_behind_margin_arg(self):
        self.behind(30)  # 15 below
        code, out, pace = self.run_pace(MID, "--pace-margin", "20")
        self.assertEqual((pace["state"], pace["wake"]), ("ON_PACE", "ONCE"))

    def test_behind_needs_ready_item(self):
        self.behind()
        code, out, pace = self.run_pace(MID, queue="none")
        self.assertEqual((pace["state"], pace["wake"], pace["next_ready"]), ("BEHIND", "ONCE", None))
        self.assertIn("no READY item in the queue", pace["held"])
        self.assertIn("no wake: no READY item in the queue", out[1])

    def test_behind_needs_queue(self):
        self.behind()
        code, out, pace = self.run_pace(MID, queue=None)
        self.assertEqual((pace["state"], pace["wake"]), ("BEHIND", "ONCE"))
        self.assertIn("no --queue given", pace["held"])

    def test_running_agent_blocks_behind(self):
        self.behind()
        self.agent(MID, 60)  # written a minute ago: an agent works
        code, out, pace = self.run_pace(MID)
        self.assertEqual((pace["wake"], pace["agents_active"]), ("ONCE", 1))
        self.assertIn("1 agent(s) worked in the last 5 min", pace["held"])
        self.agent(MID, 6 * 60)  # 6 min old: idle, BEHIND fires
        self.agent(MID, 0, name="agent-a1.meta.json")  # not a transcript: never counts
        code, out, pace = self.run_pace(MID)
        self.assertEqual((pace["wake"], pace["agents_active"]), ("BEHIND", 0))

    def test_running_workflow_agent_blocks_behind(self):
        self.behind()
        self.agent(MID, 60, name=os.path.join("workflows", "wf_1", "agent-b1.jsonl"))
        code, out, pace = self.run_pace(MID)
        self.assertEqual((pace["wake"], pace["agents_active"]), ("ONCE", 1))
        self.agent(MID, 6 * 60, name=os.path.join("workflows", "wf_1", "agent-b1.jsonl"))
        self.agent(MID, 0, name=os.path.join("workflows", "wf_1", "journal.jsonl"))  # not an agent transcript
        self.assertEqual(self.run_pace(MID)[2]["wake"], "BEHIND")

    def test_agent_does_not_block_ahead(self):
        self.reading(60, MID - timedelta(hours=2))
        self.agent(MID, 60)
        self.assertEqual(self.run_pace(MID)[2]["wake"], "AHEAD")

    def test_ahead_threshold(self):
        self.reading(54.9, MID - timedelta(hours=2))  # 9.9 above
        code, out, pace = self.run_pace(MID)
        self.assertEqual((pace["state"], pace["wake"]), ("ON_PACE", "ONCE"))
        self.reading(55, MID - timedelta(hours=2))  # exactly 10 above: fires
        self.assertEqual(self.run_pace(MID)[2]["wake"], "AHEAD")

    def test_trigger_before_ahead(self):
        self.reading(TRIGGER + 1, MID - timedelta(hours=2))
        self.assertEqual(self.run_pace(MID)[2]["wake"], "TRIGGER")
        self.assertEqual(self.run_pace(MID, "--trigger", "99")[2]["wake"], "AHEAD")

    def test_snooze_behind(self):
        self.behind()
        self.assertEqual(self.run_pace(MID)[2]["wake"], "BEHIND")
        code, out, pace = self.run_pace(MID + timedelta(minutes=30))
        self.assertEqual((pace["state"], pace["wake"]), ("BEHIND", "ONCE"))
        self.assertIn("BEHIND snoozed until 13:00 UTC", pace["held"])  # MID = Jan 4 12:00
        self.assertEqual(self.run_pace(MID + timedelta(minutes=61))[2]["wake"], "BEHIND")

    def test_snooze_ahead(self):
        self.reading(60, MID - timedelta(hours=2))
        self.assertEqual(self.run_pace(MID)[2]["wake"], "AHEAD")
        self.assertEqual(self.run_pace(MID + timedelta(minutes=59))[2]["wake"], "ONCE")
        self.assertEqual(self.run_pace(MID + timedelta(minutes=60))[2]["wake"], "AHEAD")

    def test_snooze_is_per_reason(self):
        self.behind()
        self.assertEqual(self.run_pace(MID)[2]["wake"], "BEHIND")
        self.reading(60, MID)
        self.assertEqual(self.run_pace(MID + timedelta(minutes=10))[2]["wake"], "AHEAD")

    def test_snooze_arg(self):
        self.behind()
        self.assertEqual(self.run_pace(MID)[2]["wake"], "BEHIND")
        self.assertEqual(self.run_pace(MID + timedelta(minutes=30), "--pace-snooze", "10")[2]["wake"], "BEHIND")

    def test_watch_loop_exits_on_behind(self):
        self.behind()
        code, out, pace = self.run_pace(MID, once=False, timeout=60)
        self.assertEqual((code, pace["wake"]), (0, "BEHIND"))
        self.assertTrue(out[0].startswith("PACE BEHIND: "))

    def test_no_reading(self):
        code, out, pace = self.run_pace(MID)
        self.assertEqual((code, out, pace), (1, ["watch: no usage reading recorded. Read get_usage, then run --record-usage."], None))

    def test_no_weekly_reset(self):
        self.reading(30, MID - timedelta(hours=2), weekly_resets=None)
        code, out, pace = self.run_pace(MID)
        self.assertEqual((code, pace["state"], pace["wake"], pace["line"]), (0, "NO_RESET", "ONCE", None))
        self.assertIn("no pace line", out[1])


class TestRobustness(Base):
    """Round 2: a bad queue file or snooze file must not stop the watcher (the 85% trigger lives in it)."""

    def behind(self, weekly=30):
        self.reading(weekly, MID - timedelta(hours=2))  # 15 points below the line at MID

    def write(self, name, data):
        path = os.path.join(self.tmp, name)
        with open(path, "wb") as f:
            f.write(data)
        return path

    def test_queue_cp1251(self):
        """A tasks.md in cp1251 (not UTF-8): no traceback, pace.json written, BEHIND still finds T20."""
        text = QUEUE.replace("the second item", "\u0432\u0442\u043e\u0440\u0430\u044f \u0437\u0430\u0434\u0430\u0447\u0430")
        path = self.write("tasks_cp1251.md", text.encode("cp1251"))
        with self.assertRaises(UnicodeDecodeError):
            open(path, encoding="utf-8").read()  # the fixture is really not UTF-8
        self.assertEqual(ctx.first_ready(path)["id"], "T20")
        self.behind()
        code, out, pace = self.run_pace(MID, queue=path)
        self.assertEqual((code, pace["wake"], pace["next_ready"]["id"]), (0, "BEHIND", "T20"))
        self.assertTrue(out[0].startswith("PACE BEHIND: "))

    def test_queue_cp1251_watch_loop(self):
        """The --watch loop (no --once) with a cp1251 queue still wakes on the trigger."""
        path = self.write("tasks_cp1251.md", QUEUE_NONE.encode("cp1251") + b"\xcf\xf0\xe8\xe2\xe5\xf2\n")
        self.reading(TRIGGER + 1, MID - timedelta(hours=2))
        code, out, pace = self.run_pace(MID, once=False, queue=path)
        self.assertEqual((code, pace["wake"]), (0, "TRIGGER"))

    def test_queue_bom(self):
        """A UTF-8 BOM at the file start (before '## Ready queue') or in the middle does not hide the section."""
        body = "## Ready queue\n1. **T30**: bom item. State: READY.\n"
        start = self.write("tasks_bom.md", ("\ufeff" + body).encode("utf-8"))
        middle = self.write("tasks_bom_mid.md", ("# Tasks\n\n" + "\ufeff" + body).encode("utf-8"))
        self.assertEqual(ctx.first_ready(start), {"id": "T30", "text": "bom item"})
        self.assertEqual(ctx.first_ready(middle), {"id": "T30", "text": "bom item"})
        self.behind()
        self.assertEqual(self.run_pace(MID, queue=start)[2]["wake"], "BEHIND")

    def test_queue_reasons(self):
        """When BEHIND is held for the queue, the held text says why."""
        nosec = self.write("tasks_nosec.md", b"# Tasks\n## Ready  list\n1. **T1**: x. State: READY.\n")
        self.assertEqual(ctx.read_queue(nosec), (None, "no '## Ready queue' section in tasks_nosec.md"))
        self.assertEqual(ctx.read_queue(self.queue_none), (None, "no READY item in the queue"))
        self.assertEqual(ctx.read_queue(None), (None, "no --queue given"))
        self.assertTrue(ctx.read_queue(os.path.join(self.tmp, "missing.md"))[1].startswith("cannot read the queue file"))
        self.behind()
        code, out, pace = self.run_pace(MID, queue=nosec)
        self.assertEqual((code, pace["wake"]), (0, "ONCE"))
        self.assertIn("no wake: no '## Ready queue' section in tasks_nosec.md", out[1])
        code, out, pace = self.run_pace(MID, queue=os.path.join(self.tmp, "missing.md"))
        self.assertEqual((code, pace["wake"]), (0, "ONCE"))
        self.assertIn("cannot read the queue file", pace["held"])

    def test_corrupt_snooze(self):
        """A pace_snooze.json edited by hand (list, text, bad time, number, broken JSON) is ignored, then rewritten."""
        self.behind()
        for data in (b"[1, 2]", b'"garbage"', b'{"BEHIND": "garbage"}', b'{"BEHIND": 123}', b"{not json",
                     b'{"BEHIND": null}', b"\xff\xfe"):
            with self.subTest(data=data):
                os.makedirs(self.sdir, exist_ok=True)
                with open(os.path.join(self.sdir, "pace_snooze.json"), "wb") as f:
                    f.write(data)
                code, out, pace = self.run_pace(MID)
                self.assertEqual((code, pace["wake"]), (0, "BEHIND"))
                snooze = ctx.load_json(os.path.join(self.sdir, "pace_snooze.json"))
                self.assertEqual(snooze["BEHIND"], iso(MID))

    def test_snooze_naive_time(self):
        """A snooze time without a zone counts as UTC (no TypeError from aware - naive)."""
        self.behind()
        os.makedirs(self.sdir, exist_ok=True)
        with open(os.path.join(self.sdir, "pace_snooze.json"), "w", encoding="utf-8") as f:
            json.dump({"BEHIND": "2027-01-04T11:30:00"}, f)  # 30 min before MID
        code, out, pace = self.run_pace(MID)
        self.assertEqual((code, pace["wake"]), (0, "ONCE"))
        self.assertIn("BEHIND snoozed until 12:30 UTC", pace["held"])


if __name__ == "__main__":
    unittest.main()
