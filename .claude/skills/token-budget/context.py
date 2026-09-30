"""Token-budget gauge and UserPromptSubmit hook for Claude Code (stdlib only).

Gauge:  python3 ~/.claude/skills/token-budget/context.py [--transcript PATH]
        Without --transcript it reads the newest session transcript of the current
        directory's project (~/.claude/projects/<cwd, non-alphanumerics as '-'>/).
Hook:   python3 ~/.claude/skills/token-budget/context.py --hook   (hook JSON on stdin)
Usage:  ... --record-usage 42 17 --resets <5h resetsAt> --weekly-resets <weekly resetsAt>
        saves an exact reading from the desktop app's get_usage tool (and prints a calibration
        when an earlier reading in the same window exists).
        ... --watch   (run in the background) exits when the estimate (reading + logged spend
        since, in all projects) reaches the trigger %, or after watch_max_min. Its exit wakes Claude.
        ... --watch --pace --queue tasks.md   also compares the weekly estimate with a pace line
        (0 at the weekly window start, 90% at its reset). It exits with PACE BEHIND (and the first
        READY queue item) when no agent works, or PACE AHEAD. It writes pace.json in the state dir.
Tests: --now 2026-09-26T12:00:00Z simulates idle time, --state-dir DIR isolates state,
        --no-clipboard leaves the clipboard alone, --watch --once / --trigger N.

Context = input + cache read + cache write of the latest API call (latest by timestamp, over
the whole file: transcripts are not in time order), plus the visible text written since, at about
3.5 characters per token. Thinking is not counted: it may be dropped from the context.
After /compact, the newest compact_boundary gives the size: postTokens plus the system
prompt and tools (config post_compact_overhead_k).
Hook mode never fails a prompt: any error exits 0. Exit 2 (block) is deliberate only.
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
CHARS_PER_TOKEN = 3.5
IMAGE_TOKENS = 1600
# USD per million tokens (Anthropic API list prices). Cache write = 1.25x input (5 min TTL), 2x (1 h TTL).
PRICES = {
    "claude-fable-5-1": {"in": 10.00, "out": 50.00, "read": 0.25},  # platform.claude.com pricing, 2026-09-28
    "claude-fable-5": {"in": 10.00, "out": 50.00, "read": 1.00},
    "claude-opus-5-5": {"in": 4.00, "out": 20.00, "read": 0.20},
    "claude-opus-5": {"in": 5.00, "out": 25.00, "read": 0.50},
    "claude-sonnet-5-5": {"in": 2.00, "out": 10.00, "read": 0.20},  # platform.claude.com pricing, 2026-09-29
    "claude-sonnet-5": {"in": 2.00, "out": 10.00, "read": 0.20},
    "claude-haiku-4-5": {"in": 1.00, "out": 5.00, "read": 0.10},
}
DEFAULTS = {
    "note_at_k": 150,               # tell Claude: delegate longer tasks
    "compact_at_k": 300,            # tell Claude: suggest /compact at the next task boundary
    "repeat_every_k": 100,          # above compact_at_k, remind again every +100k
    "post_compact_overhead_k": 60,  # system prompt + tools + CLAUDE.md, re-sent after /compact
    "block": {"enabled": True, "min_context_k": 300, "idle_min": 60},
    # The app's automatic message after a limit reset (its text cannot be edited). Nobody may be
    # at the keyboard to run /compact, so such a message is never paused.
    "auto_continue": {"patterns": [r"usage limit.*reset.*continue"]},
    "usd_per_window_percent": None,  # API-equivalent USD per 1% of the 5-hour window
    "usd_per_weekly_percent": None,  # ... per 1% of the weekly limit
    "quota": {"note_at_pct": 80, "watch_trigger_pct": 85, "watch_max_min": 60, "watch_interval_s": 120,
              # --pace: the line runs from 0 at the weekly window start to pace_stop_pct at its reset.
              "pace_stop_pct": 90, "pace_ahead_pts": 10, "pace_agent_idle_min": 5},
}


def load_config():
    cfg = json.loads(json.dumps(DEFAULTS))
    try:
        with open(os.path.join(HERE, "config.json"), encoding="utf-8") as f:
            user = json.load(f)
    except (OSError, ValueError):
        return cfg
    for key, value in user.items():
        if isinstance(value, dict) and isinstance(cfg.get(key), dict):
            cfg[key].update(value)
        elif not key.startswith("_"):
            cfg[key] = value
    return cfg


def parse_ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def reset_minute(s):
    """get_usage jitters a reset time by up to a second (03:59:59.586Z and 04:00:00.236Z for one
    window). Store and compare reset times rounded to the nearest minute."""
    if not s:
        return s
    t = parse_ts(s).astimezone(timezone.utc)
    t = datetime.fromtimestamp(round(t.timestamp() / 60) * 60, timezone.utc)
    return f"{t:%Y-%m-%dT%H:%M:%SZ}"


def anchor_kind(r):
    if r.get("isSidechain") or not r.get("timestamp"):
        return None
    m = r.get("message") or {}
    if r.get("type") == "assistant" and m.get("usage") and not str(m.get("model", "<")).startswith("<"):
        return "call"
    if r.get("type") == "system" and r.get("subtype") == "compact_boundary":
        return "compact"
    return None


def read_records(path):
    """Parse the whole transcript. A tail window is not safe: at /compact the app re-appends
    copies of old records (seen: 964 lines back to the first day), so the newest API call can
    sit far above the file end. A 35 MB transcript parses in about 0.25 s."""
    recs = []
    with open(path, "rb") as f:
        for line in f:
            try:
                recs.append(json.loads(line))
            except ValueError:
                pass
    return recs


def visible_tokens(content):
    if isinstance(content, str):
        return len(content) / CHARS_PER_TOKEN
    total = 0.0
    for c in content or []:
        if not isinstance(c, dict):
            continue
        t = c.get("type")
        if t == "text":
            total += len(c.get("text", "")) / CHARS_PER_TOKEN
        elif t == "tool_use":
            total += len(json.dumps(c.get("input"), ensure_ascii=False)) / CHARS_PER_TOKEN
        elif t == "tool_result":
            total += visible_tokens(c.get("content"))
        elif t == "image":
            total += IMAGE_TOKENS
    return total


def gauge(path, cfg, prompt=None):
    """Return the context estimate for one transcript, or None if it has no API call yet."""
    recs = read_records(path)
    anchor = None
    for r in recs:
        kind = anchor_kind(r)
        if kind and (anchor is None or parse_ts(r["timestamp"]) >= anchor[1]):
            anchor = (kind, parse_ts(r["timestamp"]), r)
    if anchor is None:
        return None
    kind, ts, r = anchor
    g = {"kind": kind, "ts": ts, "anchor_id": r.get("uuid") or r["timestamp"],
         "model": None, "ttl_min": None, "last_call": None, "since": 0}
    if kind == "compact":
        g["post"] = (r.get("compactMetadata") or {}).get("postTokens") or 0
        g["context"] = g["post"] + cfg["post_compact_overhead_k"] * 1000
        return g
    m = r["message"]
    u = m["usage"]
    cc = u.get("cache_creation") or {}
    g["model"] = m.get("model")
    g["ttl_min"] = 60 if cc.get("ephemeral_1h_input_tokens") else 5 if cc.get("ephemeral_5m_input_tokens") else None
    g["last_call"] = sum(u.get(k) or 0 for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
    since = 0.0
    for x in recs:
        if x.get("isSidechain") or not x.get("timestamp"):
            continue
        xm = x.get("message") or {}
        same_call = xm.get("id") and xm.get("id") == m.get("id")
        if not same_call and parse_ts(x["timestamp"]) <= ts:
            continue
        if x.get("type") == "assistant":
            since += visible_tokens(xm.get("content"))
        elif x.get("type") == "user":
            content = xm.get("content")
            is_prompt = isinstance(content, str) or not any(
                isinstance(c, dict) and c.get("type") == "tool_result" for c in content or [])
            if is_prompt and prompt is not None:
                continue  # hook mode adds the new prompt from stdin instead
            since += visible_tokens(content)
    if prompt:
        since += len(prompt) / CHARS_PER_TOKEN
    g["since"] = int(since)
    g["context"] = g["last_call"] + g["since"]
    return g


def price(model):
    return next((PRICES[k] for k in sorted(PRICES, key=len, reverse=True) if (model or "").startswith(k)),
                PRICES["claude-opus-5-5"])


def costs(g):
    """(USD per step, USD for a cold re-read of the whole context)."""
    p = price(g["model"])
    write_mult = 1.25 if g["ttl_min"] == 5 else 2.0
    return g["context"] * p["read"] / 1e6, g["context"] * p["in"] * write_mult / 1e6


# ---------- quota: exact reading (the app's get_usage tool) + logged spend since ----------

def call_cost(model, u):
    p = price(model)
    cc = u.get("cache_creation") or {}
    w5, w1 = cc.get("ephemeral_5m_input_tokens") or 0, cc.get("ephemeral_1h_input_tokens") or 0
    if not (w5 or w1):
        w5 = u.get("cache_creation_input_tokens") or 0
    return ((u.get("input_tokens") or 0) * p["in"] + (u.get("output_tokens") or 0) * p["out"]
            + (u.get("cache_read_input_tokens") or 0) * p["read"]
            + w5 * p["in"] * 1.25 + w1 * p["in"] * 2.0) / 1e6


def calls_since(t0):
    """{message id: (time, USD)} for every API call after t0, in all projects (main sessions and agents)."""
    calls = {}
    for path in glob.glob(os.path.join(os.path.expanduser("~/.claude/projects"), "**", "*.jsonl"), recursive=True):
        try:
            if os.path.getmtime(path) < t0.timestamp():
                continue
            with open(path, "rb") as f:
                for line in f:
                    if b'"usage"' not in line:
                        continue
                    try:
                        r = json.loads(line)
                    except ValueError:
                        continue
                    m = r.get("message") or {}
                    if (not m.get("usage") or not m.get("id") or not r.get("timestamp")
                            or str(m.get("model", "<")).startswith("<")):
                        continue
                    t = parse_ts(r["timestamp"])
                    if t > t0:  # a call is logged once per content block: keep the largest usage
                        calls[m["id"]] = (t, max(call_cost(m.get("model"), m["usage"]), calls.get(m["id"], (t, 0))[1]))
        except OSError:
            continue
    return calls


def load_reading(sdir):
    try:
        with open(os.path.join(sdir, "usage.json"), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def estimate(cfg, sdir, now):
    """Estimated % of the 5-hour and weekly limits, or None without a recorded reading.
    It cannot see claude.ai chat or other machines, so it can only read LOW: confirm with get_usage."""
    a = load_reading(sdir)
    if not a or not cfg.get("usd_per_window_percent") or not cfg.get("usd_per_weekly_percent"):
        return None
    t0 = parse_ts(a["time"])
    calls = calls_since(t0)
    e = {"reading": a, "spent": sum(usd for _, usd in calls.values())}
    for key, pct, reset, per in (("five", "five_hour_pct", "five_hour_resets", "usd_per_window_percent"),
                                 ("weekly", "weekly_pct", "weekly_resets", "usd_per_weekly_percent")):
        base, since = a[pct], t0
        if a.get(reset) and now >= parse_ts(a[reset]):
            base, since = 0, parse_ts(a[reset])  # that window rolled over since the reading
            if key == "five":
                # A new 5-hour window opens at the first call after the last one ended, so
                # several may have passed since the reading. Count only the current one.
                start = None
                for t in sorted(t for t, _ in calls.values() if t > since):
                    if start is None or t >= start + timedelta(hours=5):
                        start = t
                since = start if start and now < start + timedelta(hours=5) else now
            else:
                while now >= since + timedelta(days=7):
                    since += timedelta(days=7)  # the weekly window resets on a fixed schedule
        e[key] = base + sum(usd for t, usd in calls.values() if t >= since and t > t0) / cfg[per]
    return e


def describe(e):
    a = e["reading"]
    return (f"estimated 5-hour ~{e['five']:.0f}%, weekly ~{e['weekly']:.0f}% (exact reading "
            f"{a['five_hour_pct']:g}%/{a['weekly_pct']:g}% at {a['time'][11:16]} UTC + ${e['spent']:.2f} logged since)")


def share(cfg, usd):
    per = cfg.get("usd_per_window_percent")
    return f" (~{usd / per:.0f}% of a 5-hour window)" if per else ""


def level(ctx, cfg):
    k = ctx / 1000
    if k < cfg["note_at_k"]:
        return 0
    if k < cfg["compact_at_k"]:
        return 1
    return 2 + int((k - cfg["compact_at_k"]) // cfg["repeat_every_k"])


def verdict(lvl, cfg):
    if lvl == 0:
        return f"under {cfg['note_at_k']}k: work inline"
    if lvl == 1:
        return (f"{cfg['note_at_k']}-{cfg['compact_at_k']}k: inline only for <= ~8 steps or your own visual "
                "sign-off; delegate longer work to a subagent with a context pack")
    return f"over {cfg['compact_at_k']}k: delegate most work; suggest /compact at the next task boundary"


# ---------- state (per session, in the temp folder) ----------

def load_state(sdir, sid):
    try:
        with open(os.path.join(sdir, sid + ".json"), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_state(sdir, sid, st):
    try:
        os.makedirs(sdir, exist_ok=True)
        with open(os.path.join(sdir, sid + ".json"), "w", encoding="utf-8") as f:
            json.dump(st, f)
        return True
    except OSError:
        return False


def log_run(sdir, line):
    try:
        path = os.path.join(sdir, "runs.log")
        if os.path.exists(path) and os.path.getsize(path) > 64_000:
            with open(path, encoding="utf-8") as f:
                keep = f.readlines()[-200:]
            with open(path, "w", encoding="utf-8") as f:
                f.writelines(keep)
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def copy_clipboard(path):
    try:
        if os.name == "nt":
            subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command",
                            "Set-Clipboard -Value ([IO.File]::ReadAllText($env:TB_PROMPT_FILE))"],
                           env=dict(os.environ, TB_PROMPT_FILE=path), timeout=8, capture_output=True, check=True)
        elif sys.platform == "darwin":
            with open(path, "rb") as f:
                subprocess.run(["pbcopy"], stdin=f, timeout=5, check=True)
        else:
            return False
        return True
    except (OSError, subprocess.SubprocessError):
        return False


# ---------- modes ----------

def run_hook(args, cfg):
    data = json.loads(sys.stdin.buffer.read().decode("utf-8", "replace") or "{}")
    path = data.get("transcript_path")
    if not path or not os.path.isfile(path):
        return 0
    sid = re.sub(r"[^A-Za-z0-9_-]", "", str(data.get("session_id") or ""))[:64] or "unknown"
    prompt = data.get("prompt") or ""
    if re.match(r"\s*/(compact|clear)\b", prompt):
        return 0  # a note here would only land in the compaction summary
    g = gauge(path, cfg, prompt)
    if g is None:
        return 0
    sdir = args.state_dir
    st = load_state(sdir, sid)
    k = g["context"] // 1000
    idle = (args.now - g["ts"]).total_seconds() / 60
    step, cold = costs(g)
    cold_cache = g["kind"] == "call" and idle >= (g["ttl_min"] or 60)
    stamp = f"{args.now:%Y-%m-%dT%H:%M:%SZ} {sid[:8]} ctx={k}k idle={idle:.0f}min"

    auto = any(re.search(p, prompt, re.I | re.S) for p in cfg["auto_continue"].get("patterns", []))
    b = cfg["block"]
    if (b.get("enabled") and not auto and cold_cache and idle >= b["idle_min"] and k >= b["min_context_k"]
            and not prompt.lstrip().startswith("/") and st.get("blocked_for") != g["anchor_id"]):
        st["blocked_for"] = g["anchor_id"]
        if save_state(sdir, sid, st):  # never block unless the next message is sure to pass
            saved = os.path.join(sdir, f"blocked-{sid[:8]}.txt")
            try:
                with open(saved, "w", encoding="utf-8") as f:
                    f.write(prompt)
            except OSError:
                saved = None
            copied = bool(saved and prompt and not args.no_clipboard and copy_clipboard(saved))
            ratio = max(1, round(g["context"] / ((cfg["post_compact_overhead_k"] + 30) * 1000)))
            where = (f"Your message is saved in {saved}" + (" and copied to the clipboard." if copied else ".")
                     if saved else "Your message could not be saved: copy it before you continue.")
            sys.stderr.write(
                f"token-budget: this message was paused once (not sent).\n"
                f"Context is {k}k tokens and the prompt cache expired (idle {idle:.0f} min). Sending now re-reads "
                f"all of it: about ${cold:.2f}{share(cfg, cold)}, then about ${step:.3f} per step.\n"
                f"- Longer session ahead: run /compact first. It re-reads the context once too, but every later "
                f"step then costs about {ratio}x less.\n"
                f"- Quick question: send the message again. It goes through: the pause happens once per break.\n"
                f"{where}\n"
                f"Cheapest next time: /compact before a long break, while the cache is still warm.\n")
            log_run(sdir, stamp + " action=block")
            return 2

    lines = []
    if auto and k >= cfg["note_at_k"]:
        lines.append(f"[token-budget] This is the app's automatic message after a limit reset: nobody may be at "
                     f"the keyboard to run /compact, so it was not paused. Context ~{k}k"
                     + (f", cold cache: this turn re-reads it (~${cold:.2f})" if cold_cache else "")
                     + ". Continue the task. Delegate long work to subagents, update the resume note after "
                     "each step, and at the next task boundary stop with a /compact suggestion for the user.")
        st["cold_noted_for"] = g["anchor_id"]  # this line already says the cache was cold
    lvl = level(g["context"], cfg)
    if lvl >= 1 and lvl > st.get("level", 0):
        lines.append(f"[token-budget] Main context ~{k}k tokens; every step re-reads it (~${step:.3f}/step). "
                     f"Rule, {verdict(lvl, cfg)}. Details: the token-budget skill.")
    if cold_cache and lvl >= 1 and st.get("cold_noted_for") != g["anchor_id"]:
        st["cold_noted_for"] = g["anchor_id"]
        lines.append(f"[token-budget] The prompt cache was cold (idle {idle:.0f} min): this turn re-reads ~{k}k "
                     f"tokens (~${cold:.2f}). If a long task follows, suggest /compact before it.")
    e = estimate(cfg, sdir, args.now)
    if e:
        bucket = int(max(e["five"], e["weekly"]) // 5) * 5
        if bucket >= cfg["quota"]["note_at_pct"] and bucket > st.get("quota_bucket", 0):
            lines.append(f"[token-budget] Usage: {describe(e)}. Read the exact % with get_usage; "
                         f"at >= 90% run the checkpoint skill.")
        st["quota_bucket"] = bucket
    st["level"] = lvl
    save_state(sdir, sid, st)
    log_run(sdir, stamp + (" auto" if auto else "") + (" action=note" if lines else " action=quiet"))
    if lines:
        print("\n".join(lines))
    return 0


def find_transcript():
    root = os.path.expanduser("~/.claude/projects")
    enc = re.sub(r"[^A-Za-z0-9]", "-", os.getcwd())
    files = glob.glob(os.path.join(root, enc, "*.jsonl")) or glob.glob(os.path.join(root, "*", "*.jsonl"))
    return max(files, key=os.path.getmtime) if files else None


def run_gauge(args, cfg):
    path = args.transcript or find_transcript()
    if not path:
        print("no transcript found")
        return 1
    g = gauge(path, cfg)
    if g is None:
        print(f"{os.path.basename(path)}: no API call yet")
        return 0
    k = g["context"] // 1000
    idle = (args.now - g["ts"]).total_seconds() / 60
    step, cold = costs(g)
    if g["kind"] == "compact":
        print(f"{os.path.basename(path)[:8]}: context ~{k}k tokens (estimate after /compact at {g['ts']:%m-%d %H:%M} "
              f"UTC: summary {g['post'] // 1000}k + ~{cfg['post_compact_overhead_k']}k system prompt and tools)")
    else:
        print(f"{os.path.basename(path)[:8]}: context ~{k}k tokens (last call {g['last_call'] // 1000}k at "
              f"{g['ts']:%m-%d %H:%M} UTC + ~{g['since'] // 1000}k written since)")
        print(f"model {g['model']}, cache TTL {g['ttl_min'] or '?'} min, idle {idle:.0f} min: "
              f"~${step:.3f} per step, a cold re-read ~${cold:.2f}{share(cfg, cold)}")
    print(verdict(level(g["context"], cfg), cfg))
    e = estimate(cfg, args.state_dir, args.now)
    if e:
        print("usage: " + describe(e))
    return 0


def run_record(args, cfg):
    five, weekly = args.record_usage
    prev = load_reading(args.state_dir)
    data = {"time": f"{args.now:%Y-%m-%dT%H:%M:%SZ}", "five_hour_pct": five, "weekly_pct": weekly,
            "five_hour_resets": reset_minute(args.resets), "weekly_resets": reset_minute(args.weekly_resets)}
    os.makedirs(args.state_dir, exist_ok=True)
    with open(os.path.join(args.state_dir, "usage.json"), "w", encoding="utf-8") as f:
        json.dump(data, f)
    # Durable history of every reading, for the account ledger (expense-log skill). Explicit
    # --state-dir (tests) writes only into that state dir, never into the real history.
    hist_dir = args.state_dir if "--state-dir" in sys.argv else os.path.expanduser("~/.claude/ledger")
    try:
        os.makedirs(hist_dir, exist_ok=True)
        with open(os.path.join(hist_dir, "readings.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps(data) + "\n")
    except OSError:
        pass
    print(f"recorded: 5-hour {five:g}%, weekly {weekly:g}% at {data['time']}")
    if not prev:
        return 0
    usd = sum(u for t, u in calls_since(parse_ts(prev["time"])).values() if t <= args.now)
    for label, pct, reset, per, min_delta in (("5-hour", "five_hour_pct", "five_hour_resets", "usd_per_window_percent", 5),
                                              ("weekly", "weekly_pct", "weekly_resets", "usd_per_weekly_percent", 2)):
        delta = data[pct] - prev[pct]
        if reset_minute(prev.get(reset)) == data[reset] and delta >= min_delta:
            print(f"calibration, {label}: ${usd:.2f} logged since the previous reading / +{delta:g}% = "
                  f"${usd / delta:.2f} per 1% (config {cfg[per]}). Too low if claude.ai chat was used meanwhile.")
    return 0


def run_watch(args, cfg):
    q = cfg["quota"]
    trigger = args.trigger or q["watch_trigger_pct"]
    start = datetime.now(timezone.utc)
    while True:
        now = datetime.now(timezone.utc)
        e = estimate(cfg, args.state_dir, now)
        if e is None:
            print("watch: no usage reading recorded. Read get_usage, then run --record-usage.")
            return 1
        if max(e["five"], e["weekly"]) >= trigger:
            print(f"watch TRIGGER (>= {trigger:g}%): {describe(e)}. Read get_usage; at >= 90% run the checkpoint skill.")
            return 0
        if args.once or (now - start).total_seconds() >= q["watch_max_min"] * 60:
            print(f"watch {'ONCE' if args.once else 'TIMER'}: {describe(e)}. "
                  f"Read get_usage, record it, and restart the watcher if the run continues.")
            return 0
        time.sleep(q["watch_interval_s"])


# ---------- pace (--watch --pace): weekly use against a line from reset to reset ----------

def iso(t):
    return f"{t.astimezone(timezone.utc):%Y-%m-%dT%H:%M:%SZ}"


def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def save_json(path, data):
    """Write through a temp file: a dashboard may read pace.json at any time."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path + ".tmp", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=1)
        os.replace(path + ".tmp", path)
    except OSError:
        pass


def week_bounds(a, now):
    """(start, reset) of the weekly window that holds now, from the reading's weekly reset, or None.
    The window resets on a fixed 7-day schedule, as in estimate()."""
    if not a or not a.get("weekly_resets"):
        return None
    reset = parse_ts(a["weekly_resets"])
    while now >= reset:
        reset += timedelta(days=7)
    while now < reset - timedelta(days=7):
        reset -= timedelta(days=7)
    return reset - timedelta(days=7), reset


def pace_line(start, now, stop_pct):
    """The weekly % the line allows at now: stop_pct x the share of the week gone since start."""
    frac = (now - start).total_seconds() / timedelta(days=7).total_seconds()
    return stop_pct * min(1.0, max(0.0, frac))


QUEUE_ITEM = re.compile(r"\s*\d+\.\s+\*\*(?P<id>[^*]+)\*\*:?\s*(?P<text>.*?)\s*State:\s*(?P<state>[A-Z]+)")


def read_queue(path):
    """(item, why): item = {id, text} of the first READY item in the '## Ready queue' section of path,
    or None, and then why = the reason in words. Items look like
    'N. **<Id>**: <text>. State: READY|WAITING (...)|RUNNING|DONE.'
    A file in another encoding or with a BOM must not stop the watcher: bad bytes become U+FFFD."""
    if not path:
        return None, "no --queue given"
    try:
        with open(path, encoding="utf-8-sig", errors="replace") as f:
            lines = f.read().splitlines()
    except (OSError, UnicodeError) as err:
        return None, f"cannot read the queue file ({getattr(err, 'strerror', None) or err})"
    inside = found = False
    for line in lines:
        line = line.lstrip("\ufeff")  # a BOM left in the middle of a file (joined files)
        if line.startswith("## "):
            inside = line[3:].strip().lower().startswith("ready queue")
            found = found or inside
            continue
        m = QUEUE_ITEM.match(line) if inside else None
        if m and m["state"] == "READY":
            return {"id": m["id"].strip(), "text": m["text"].rstrip(". ")}, None
    if not found:
        return None, f"no '## Ready queue' section in {os.path.basename(path)}"
    return None, "no READY item in the queue"


def first_ready(path):
    """{id, text} of the first READY item in the '## Ready queue' section of path, or None."""
    return read_queue(path)[0]


def active_agents(now, idle_min):
    """Subagent transcripts (all projects) written in the last idle_min minutes: an agent works now.
    Plain agents write <project>/<session>/subagents/agent-*.jsonl, workflow agents one level deeper
    (subagents/workflows/wf_*/agent-*.jsonl), so search the whole subagents tree.
    With --now, this compares the fake time with real file mtimes (as calls_since does):
    tests must set fixture mtimes relative to --now."""
    pattern = os.path.join(os.path.expanduser("~/.claude/projects"), "*", "*", "subagents", "**", "agent-*.jsonl")
    found = []
    for path in glob.glob(pattern, recursive=True):
        try:
            if now.timestamp() - os.path.getmtime(path) < idle_min * 60:
                found.append(path)
        except OSError:
            continue
    return found


def pace_state(args, cfg, e, now):
    q = cfg["quota"]
    item, why = read_queue(args.queue)
    p = {"ts": iso(now), "weekly_est": e["weekly"], "five_hour_est": e["five"],
         "line": None, "delta": None, "week_start": None, "weekly_reset": None, "hours_to_reset": None,
         "next_ready": item, "queue_note": why,
         "agents_active": len(active_agents(now, q["pace_agent_idle_min"])),
         "state": "NO_RESET", "wake": None, "held": None}
    wb = week_bounds(e["reading"], now)
    if wb:
        start, reset = wb
        line = pace_line(start, now, q["pace_stop_pct"])
        delta = e["weekly"] - line  # > 0: above the line (ahead), < 0: below it (behind)
        p.update(line=line, delta=delta, week_start=iso(start), weekly_reset=iso(reset),
                 hours_to_reset=(reset - now).total_seconds() / 3600,
                 state="BEHIND" if -delta >= args.pace_margin else "AHEAD" if delta >= q["pace_ahead_pts"] else "ON_PACE")
    return p


def pace_text(p):
    if p["line"] is None:
        return (f"weekly ~{p['weekly_est']:.1f}%, no pace line: the reading has no weekly reset time "
                f"(record one with --weekly-resets)")
    return (f"weekly ~{p['weekly_est']:.1f}% vs pace line {p['line']:.1f}% ({p['delta']:+.1f} points), "
            f"{p['hours_to_reset']:.1f} h to the weekly reset ({p['weekly_reset'][5:16].replace('T', ' ')} UTC)")


def clock(args, t0):
    """The current time. With --now, a fake clock that starts there and runs in whole seconds."""
    real = datetime.now(timezone.utc)
    if not args.fake_now:
        return real
    return args.fake_now + timedelta(seconds=int((real - t0).total_seconds()))


def snooze_time(snooze, state):
    """The time of the last wake for state in pace_snooze.json, or None if absent or not a valid time."""
    try:
        t = parse_ts(snooze[state])
    except (KeyError, TypeError, AttributeError, ValueError):
        return None
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def run_watch_pace(args, cfg):
    """--watch --pace: the trigger and timer of run_watch, plus the PACE BEHIND and PACE AHEAD wakes."""
    q = cfg["quota"]
    trigger = args.trigger or q["watch_trigger_pct"]
    t0 = datetime.now(timezone.utc)
    start = clock(args, t0)
    snooze_path = os.path.join(args.state_dir, "pace_snooze.json")
    while True:
        now = clock(args, t0)
        e = estimate(cfg, args.state_dir, now)
        if e is None:
            print("watch: no usage reading recorded. Read get_usage, then run --record-usage.")
            return 1
        p = pace_state(args, cfg, e, now)
        snooze = load_json(snooze_path)
        if not isinstance(snooze, dict):  # missing or edited by hand: start a new snooze record
            snooze = {}
        held = []  # why the pace state does not wake the session
        last = snooze_time(snooze, p["state"])
        if p["state"] in ("BEHIND", "AHEAD") and last and \
                timedelta(0) <= now - last < timedelta(minutes=args.pace_snooze):
            held.append(f"{p['state']} snoozed until {iso(last + timedelta(minutes=args.pace_snooze))[11:16]} UTC")
        if p["state"] == "BEHIND":
            if not p["next_ready"]:
                held.append(p["queue_note"])
            if p["agents_active"]:
                held.append(f"{p['agents_active']} agent(s) worked in the last {q['pace_agent_idle_min']:g} min")
        if max(e["five"], e["weekly"]) >= trigger:
            wake = "TRIGGER"
        elif p["state"] in ("BEHIND", "AHEAD") and not held:
            wake = p["state"]
        elif args.once:
            wake = "ONCE"
        elif (now - start).total_seconds() >= q["watch_max_min"] * 60:
            wake = "TIMER"
        else:
            wake = None
        p["wake"], p["held"] = wake, "; ".join(held) or None
        save_json(os.path.join(args.state_dir, "pace.json"),
                  {k: round(v, 2) if isinstance(v, float) else v for k, v in p.items()})
        if wake in ("BEHIND", "AHEAD"):
            snooze[wake] = iso(now)
            save_json(snooze_path, snooze)
        status = (f"pace: {pace_text(p)}, state {p['state']}"
                  + (f", next READY {p['next_ready']['id']}" if p["next_ready"] else "")
                  + (f", no wake: {p['held']}" if p["held"] else "") + ".")
        if wake == "TRIGGER":
            print(f"watch TRIGGER (>= {trigger:g}%): {describe(e)}. Read get_usage; at >= 90% run the checkpoint skill.")
            print(status)
        elif wake == "BEHIND":
            r = p["next_ready"]
            print(f"PACE BEHIND: {pace_text(p)}. Start the first READY item: {r['id']}: {r['text']}.")
            print(f"usage: {describe(e)}. Read get_usage and record it first. If it is still behind, "
                  f"start the item, then restart the watcher.")
        elif wake == "AHEAD":
            print(f"PACE AHEAD: {pace_text(p)}. Use fewer parallel runs and skip optional checks "
                  f"until the line catches up.")
            print(f"usage: {describe(e)}. Read get_usage, record it, and restart the watcher.")
        elif wake:
            print(f"watch {wake}: {describe(e)}. Read get_usage, record it, and restart the watcher if the run continues.")
            print(status)
        if wake:
            return 0
        time.sleep(q["watch_interval_s"])


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--hook", action="store_true", help="run as a UserPromptSubmit hook (JSON on stdin)")
    ap.add_argument("--transcript", help="gauge this transcript instead of the newest one")
    ap.add_argument("--now", type=parse_ts, help="pretend the current UTC time is this (tests)")
    ap.add_argument("--state-dir", default=os.path.join(tempfile.gettempdir(), "claude-token-budget"))
    ap.add_argument("--no-clipboard", action="store_true")
    ap.add_argument("--record-usage", nargs=2, type=float, metavar=("FIVE_HOUR_PCT", "WEEKLY_PCT"),
                    help="save an exact reading from the app's get_usage tool")
    ap.add_argument("--resets", help="with --record-usage: the 5-hour reset time (ISO)")
    ap.add_argument("--weekly-resets", help="with --record-usage: the weekly reset time (ISO)")
    ap.add_argument("--watch", action="store_true",
                    help="exit when the estimated usage reaches the trigger, or on the timer (run in background)")
    ap.add_argument("--trigger", type=float, help="with --watch: override the trigger %% (tests)")
    ap.add_argument("--once", action="store_true", help="with --watch: print the estimate once and exit")
    ap.add_argument("--pace", action="store_true",
                    help="with --watch: also wake on PACE BEHIND / PACE AHEAD of the weekly pace line; write pace.json")
    ap.add_argument("--queue", help="with --pace: the tasks file whose '## Ready queue' gives the first READY item")
    ap.add_argument("--pace-margin", type=float, default=5,
                    help="with --pace: points below the line for PACE BEHIND (default 5)")
    ap.add_argument("--pace-snooze", type=float, default=60,
                    help="with --pace: minutes without a second wake for the same reason (default 60)")
    args = ap.parse_args()
    args.fake_now = args.now
    args.now = args.now or datetime.now(timezone.utc)
    cfg = load_config()
    if args.hook:
        return run_hook(args, cfg)
    if args.record_usage:
        return run_record(args, cfg)
    if args.watch:
        return run_watch_pace(args, cfg) if args.pace else run_watch(args, cfg)
    return run_gauge(args, cfg)


if __name__ == "__main__":
    try:
        for stream in (sys.stdout, sys.stderr):
            stream.reconfigure(encoding="utf-8")
        code = main()
    except BaseException:
        if "--hook" not in sys.argv:
            raise
        code = 0  # a broken hook must never block the user's prompt
    sys.exit(code)
