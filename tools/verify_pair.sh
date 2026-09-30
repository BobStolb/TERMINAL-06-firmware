#!/usr/bin/env bash
# tools/verify_pair.sh - every automated check of the through-hole pair TS06-DISP + TS06-DRV,
# in one command, from the repository root (it finds the root itself if run from elsewhere):
#
#     tools/verify_pair.sh              # everything
#     tools/verify_pair.sh --no-drc     # everything but KiCad's own DRC
#     tools/verify_pair.sh --keep       # keep the scratch directory (logs, DRC reports) and say where
#
# It prints one line per check - PASS, FAIL or SKIP, with the numbers that matter - and exits 1 if
# any check FAILed, 0 otherwise. A SKIP (a tool that is not installed) does not fail the run.
# Nothing in the working tree is written: every regeneration and every report goes to a scratch
# directory under $TMPDIR (default /tmp) that is removed at the end.
#
# Needs: bash, Python 3.8+ with numpy (audit.py). KiCad's DRC needs one of: a KiCad 10 kicad-cli
# (on PATH, in the usual install folder, or named by KICAD_CLI=...), or Docker, which runs the
# image in KICAD_IMAGE (default mirror.gcr.io/kicad/kicad:10.0, ~1 GB, pulled once). With neither,
# the DRC lines say SKIP.
#
# THE CHECKS, per board unless noted:
#   netlist        tools/ts06pair.py: every net has two pads; the strips carry the same net on
#                  both boards; nothing crosses between the boards except on a strip pin
#   mate           mkpcb_drv.check_mate(): every XS pin lands on its XP pin with the same net,
#                  and every display standoff has its hole in TS06-DRV
#   firmware       the BOARD_TYPE 4 tables in firmware/nixieClock_TS06 (digit map, anode order,
#                  decoder wiring, MCP23017 address) and the tables of firmware/ts06_bringup agree
#                  with tools/ts06pair.py
#   generator      the committed board, project and fp-lib-table are byte for byte what
#                  tools/mkpcb_disp.py / mkpcb_drv.py write (so the checks below test the source),
#                  and the rotated footprints they write into PCB/lib are the committed ones
#   checkpcb       placement: pads and courtyards inside the outline, courtyard overlaps
#   checkcopper    copper clearance, 0.6 mm wherever a high-voltage net is on either side
#                  (--hv below, the same list as the project's HV net class); no vias
#   audit          per-net connectivity through tracks and pours, pour islands, silkscreen
#   drc            KiCad 10: kicad-cli pcb drc --refill-zones --severity-all
#   bom            PCB/TS06-*/bom.md are what tools/bom_pair.py writes today
#   case           3d/case-pair/case_pair.py --extract: the case model's interference checks
#                  against both boards and the fascia
#   case outputs   boards.json, params.scad, checks.md and out/*.svg are what it writes today
#
# KNOWN, ACCEPTED ITEMS - reported, never FAILed (PCB/README.md "Checked", the pair review):
#   TS06-DISP checkpcb  COURTYARD OFF-BOARD H3: the standoff hole above the colon; its courtyard
#                       runs 0.15 mm past the top edge. Harmless; FAILs if it grows past 0.25 mm.
#   TS06-DISP checkpcb  COURTYARD OVERLAP V3 / V7 and V3 / V8: the two colon lamps' courtyards
#   + drc (2 errors)    overlap the M10 tube's by 0.135 mm at their measured positions (inherited
#                       from TS06-MAIN; review 9: a test fit with a real tube settles it). KiCad
#                       10 reports them as courtyards_overlap, severity error.
#   TS06-DRV checkpcb   COURTYARD OFF-BOARD U1: the Nano's USB receptacle stands proud of the
#                       edge by design (it is reached through the case cheek). FAILs past 2.6 mm.
#   TS06-DRV checkpcb   COURTYARD OFF-BOARD XS11: 0.17 mm past the edge, because the strip must
#                       sit exactly behind the display's XP11. FAILs past 0.25 mm.
#   TS06-DRV drc        4 warnings: silk_edge_clearance x2, the Nano's (U1) outline past the edge
#                       with its USB; lib_footprint_mismatch x2, VT21 (TO-220) and XS1 (DC jack),
#                       whose stock silkscreen is clipped at their pads, so the board's copies
#                       differ from the library files on purpose.
#   case                2 rows are FAIL by design: "12 V plug engagement, plain 6 mm cheek" and
#                       "review's 'Ø14 pocket from inside'". They are the two rejected ways of
#                       passing the DC jack through the cheek, recorded to show why the model
#                       counterbores it from the outside (that row is OK, 7.2 mm).
# Anything else - a new item, or an accepted one that has grown - is a FAIL.
set -u

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT" || exit 2
NO_DRC=0
KEEP=0
for a in "$@"; do
  case $a in
    --no-drc) NO_DRC=1 ;;
    --keep) KEEP=1 ;;
    -h|--help) sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown option: $a (try --help)"; exit 2 ;;
  esac
done

PY=${PYTHON:-}
if [ -z "$PY" ]; then
  for c in python3 python; do
    if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(sys.version_info < (3, 8))' 2>/dev/null; then
      PY=$c; break
    fi
  done
fi
if [ -z "$PY" ]; then echo "FAIL  python 3.8 or newer not found (set PYTHON=...)"; exit 2; fi
export PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8

TMP=$(mktemp -d "${TMPDIR:-/tmp}/verify_pair.XXXXXX") || { echo "FAIL  cannot make a scratch directory"; exit 2; }
cleanup() { if [ "$KEEP" = 1 ]; then echo "scratch kept: $TMP"; else rm -rf "$TMP"; fi; }
trap cleanup EXIT
H="$TMP/helper.py"

NPASS=0; NFAIL=0; NSKIP=0
# report STATUS NAME DETAIL [LOGFILE]: one line, and on FAIL the tail of the tool's own output
report() {
  printf '%-4s  %-26s %s\n' "$1" "$2" "$3"
  case $1 in
    PASS) NPASS=$((NPASS + 1)) ;;
    SKIP) NSKIP=$((NSKIP + 1)) ;;
    *) NFAIL=$((NFAIL + 1))
       if [ -n "${4:-}" ] && [ -s "$4" ]; then tail -n 25 "$4" | sed 's/^/        | /'; fi ;;
  esac
}
# judge NAME KIND ARGS...: the helper prints "STATUS<TAB>detail", then any explanation lines
judge() {
  local name=$1; shift
  local out status detail
  out=$("$PY" "$H" "$@" 2>&1)
  status=$(printf '%s\n' "$out" | head -n 1 | cut -f1)
  detail=$(printf '%s\n' "$out" | head -n 1 | cut -f2-)
  case $status in PASS|FAIL|SKIP) ;; *) status=FAIL; detail="checker error: $(printf '%s' "$out" | tail -n 1)" ;; esac
  report "$status" "$name" "$detail"
  printf '%s\n' "$out" | tail -n +2 | sed 's/^/        | /'
}

# ------------------------------------------------------------------------------ the parsers
cat > "$H" <<'PYEOF'
import json, os, re, sys

HV = "HV185,SW,BLEED_*,FB_MID,COLON_*,ANODE_*,EMIT_*"

# (regex on a checkpcb line, the most it may stick out past the outline in mm or None, why)
ACCEPT_CHECKPCB = {
    "TS06-DISP": [
        (r"COURTYARD OFF-BOARD +H3 ", 0.25, "H3 standoff above the colon"),
        (r"COURTYARD OVERLAP +V3 / V7$", None, "colon lamp V7 vs M10"),
        (r"COURTYARD OVERLAP +V3 / V8$", None, "colon lamp V8 vs M10"),
    ],
    "TS06-DRV": [
        (r"COURTYARD OFF-BOARD +U1 ", 2.6, "Nano USB proud of the edge"),
        (r"COURTYARD OFF-BOARD +XS11 ", 0.25, "XS11 behind the display's XP11"),
    ],
}
# (KiCad violation type, the set of references it names, why)
ACCEPT_DRC = {
    "TS06-DISP": [
        ("courtyards_overlap", {"V3", "V7"}, "colon V7 / M10 courtyards"),
        ("courtyards_overlap", {"V3", "V8"}, "colon V8 / M10 courtyards"),
    ],
    "TS06-DRV": [
        ("silk_edge_clearance", {"U1"}, "Nano silk past the edge"),
        ("lib_footprint_mismatch", {"VT21"}, "VT21 silk clipped at its pads"),
        ("lib_footprint_mismatch", {"XS1"}, "XS1 silk clipped at its pads"),
    ],
}
ACCEPT_CASE = ["12 V plug engagement, plain 6 mm cheek", "review's 'Ø14 pocket from inside'"]


def out(status, detail, *more):
    print(status + "\t" + detail)
    for m in more:
        print(m)
    sys.exit(0)


def text(path):
    with open(path, "rb") as fh:
        return fh.read().replace(b"\r\n", b"\n")


def outline(pcb):
    src = open(pcb, encoding="utf8").read()
    xs, ys = [], []
    for m in re.finditer(r"\(gr_(?:line|rect)\s*\(start ([-\d.]+) ([-\d.]+)\)\s*\(end ([-\d.]+) ([-\d.]+)\)(.*?)\(layer \"Edge\.Cuts\"\)", src, re.S):
        if "(gr_" in m.group(5):
            continue
        xs += [float(m.group(1)), float(m.group(3))]
        ys += [float(m.group(2)), float(m.group(4))]
    return min(xs), min(ys), max(xs), max(ys)


def k_netlist(log, rc):
    s = open(log, encoding="utf8").read()
    parts = re.findall(r"^(disp|drv): (\d+) parts, (\d+) nets", s, re.M)
    pins = re.search(r"header pins: (\d+)", s)
    d = ", ".join(f"{b} {p} parts/{n} nets" for b, p, n in parts) + (f", {pins.group(1)} strip pins" if pins else "")
    if rc == "0" and "netlist consistent" in s:
        out("PASS", d + ": consistent")
    out("FAIL", d or "tools/ts06pair.py did not finish", *[l for l in s.splitlines() if "[PAIR]" in l][:20])


def k_mate(log, rc):
    s = open(log, encoding="utf8").read().splitlines()
    if rc != "0" or not s or not s[0].startswith("MATE"):
        out("FAIL", "check_mate() did not run", *s[-10:])
    _, nbad, npins, nnet, nholes = s[0].split()
    if nbad == "0":
        out("PASS", f"{npins} strip pins ({nnet} with a net) land on their pins, same net; {nholes} standoffs have holes")
    out("FAIL", f"{nbad} problem(s)", *s[1:21])


def k_firmware(root):
    sys.path.insert(0, os.path.join(root, "tools"))
    import ts06pair as P, ts06main as M
    bad = []
    fwdir = os.path.join(root, "firmware", "nixieClock_TS06")
    fw = "\n".join(open(os.path.join(fwdir, f), encoding="utf8").read() for f in sorted(os.listdir(fwdir)) if f.endswith(".ino"))
    keys = {k: int(v) for k, v in re.findall(r"#define (KEY\d) (\d+)", fw)}
    blk = re.search(r"#elif \(BOARD_TYPE == 4\)(.*?)#endif", fw, re.S)
    if not blk:
        out("FAIL", "no BOARD_TYPE 4 block in nixieClock_TS06.ino")
    blk = blk.group(1)
    mask = [int(x) for x in re.search(r"digitMask\[\] = \{([^}]*)\}", blk).group(1).split(",")]
    opts = [keys[x.strip()] for x in re.search(r"opts\[NUM_INDI\] = \{([^}]*)\}", blk).group(1).split(",")]
    want_pins = [int(P.TUBE_PIN4[t][1:]) for t in P.TUBES]
    if mask != P.DIGIT_MASK4:
        bad.append(f"firmware digitMask {mask} but DIGIT_MASK4 {P.DIGIT_MASK4}")
    if opts != want_pins:
        bad.append(f"firmware anode order {opts} but TUBE_PIN4 gives {want_pins}")
    # decoderNibble: PORTC bit s (Nano A<s>) takes bit b of the code; the board wires weight -> Nano pin
    shifts = {int(s): int(b) for b, s in re.findall(r"bitRead\(m, (\d)\) << (\d)\)", fw)}
    wired = {int(M.K155_INPUT[w][1]): {"A1": 0, "B2": 1, "C4": 2, "D8": 3}[w] for w in M.K155_INPUT}
    if shifts != wired:
        bad.append(f"firmware decoder bits {shifts} but the board wires {wired}")
    u3 = P.parts(P.DRV)["U3"].pins
    addr = 0x20 | sum((u3[str(15 + i)] == "+5V") << i for i in range(3))
    fa = re.search(r"#define MCP_ADDR +0x([0-9A-Fa-f]+)", open(os.path.join(root, "firmware", "nixieClock_TS06", "ts06pair.ino"), encoding="utf8").read())
    if not fa or int(fa.group(1), 16) != addr:
        bad.append(f"ts06pair.ino MCP_ADDR is not the board's 0x{addr:02X}")
    note = "BOARD_TYPE 4 digit map, anode order, decoder bits, MCP 0x%02X" % addr
    bu = os.path.join(root, "firmware", "ts06_bringup", "ts06_bringup.ino")
    if os.path.exists(bu):
        s = open(bu, encoding="utf8").read()

        def arr(name):
            return [int(x) for x in re.search(name + r"\[\d*\] = \{([^}]*)\}", s).group(1).split(",")]

        def strip_pin(net):
            for k, pins in P.HEADERS.items():
                if net in pins:
                    return int(k), pins.index(net) + 1
            return 0, 0
        qpin = {int(fn[1]): int(pin) for pin, fn in M.K155.items() if fn.startswith("Q")}
        weight = {"A1": 0, "B2": 1, "C4": 2, "D8": 3}
        want = {
            "ANODE_PIN": want_pins,
            "DIGIT_CODE": P.DIGIT_MASK4,
            "NANO_BIT": [int(M.K155_INPUT[w][1]) for w in ("A1", "B2", "C4", "D8")],
            "U15_BIT": [P.XA_IN["U15"][w] for w in ("A1", "B2", "C4", "D8")],
            "U16_BIT": [P.XA_IN["U16"][w] for w in ("A1", "B2", "C4", "D8")],
            "Q_PIN": [qpin[c] for c in range(10)],
            "XS11_PIN": [strip_pin(f"K{d}")[1] for d in range(10)],
            "XS12_PIN": [strip_pin(f"KS{d}")[1] for d in range(10)],
            "U15_XS12": [strip_pin(f"CAT_B_{g}")[1] if g else 0 for g in P.GLYPH_Q["U15"]],
            "U16_XS12": [strip_pin(f"CAT_A_{g}")[1] if g else 0 for g in P.GLYPH_Q["U16"]],
            "BL_STRIP": [strip_pin(f"BL_A{P.BL_OF_GPB[k]}")[0] for k in range(8)],
            "BL_PIN": [strip_pin(f"BL_A{P.BL_OF_GPB[k]}")[1] for k in range(8)],
        }
        for name, w in want.items():
            try:
                got = arr(name)
            except AttributeError:
                bad.append(f"ts06_bringup.ino has no {name}")
                continue
            if got != w:
                bad.append(f"ts06_bringup.ino {name} {got} but the board gives {w}")
        for name, u in (("G_U15", "U15"), ("G_U16", "U16")):
            g = re.search(name + r"\[\] PROGMEM = \"([^\"]*)\"", s).group(1).split()
            if g != [x or "-" for x in P.GLYPH_Q[u]]:
                bad.append(f"ts06_bringup.ino {name} {g} but GLYPH_Q gives {P.GLYPH_Q[u]}")
        for t, nm in enumerate(P.TUBES):
            r = P.parts(P.DRV)[f"R{27 + t}"]
            k, n = strip_pin("ANODE_" + nm)
            item = re.search(r'TUBE_TXT\[\] PROGMEM =\s*((?:"[^"]*"\s*)+);', s).group(1)
            item = "".join(re.findall(r'"([^"]*)"', item)).split("|")[t]
            if not (item.startswith(nm + " ") and f" R{27 + t} {r.value.split()[0]} " in item and item.endswith(f"XS{k}.{n}")):
                bad.append(f"ts06_bringup.ino TUBE_TXT '{item}' but the board has {nm}: R{27 + t} {r.value}, XS{k}.{n}")
        note += "; bring-up sketch tables"
    if bad:
        out("FAIL", f"{len(bad)} table(s) disagree with tools/ts06pair.py", *bad)
    out("PASS", note + ": agree with tools/ts06pair.py")


def k_same(label, *pairs):
    """pairs of (committed, regenerated); CRLF-insensitive. A directory pair compares every file."""
    diff, n = [], 0
    for a, b in zip(pairs[::2], pairs[1::2]):
        if os.path.isdir(b):                # a library: one entry, every footprint in it compared
            n += 1
            names = sorted(set(os.listdir(b)) | set(os.listdir(a) if os.path.isdir(a) else []))
            for f in names:
                fa, fb = os.path.join(a, f), os.path.join(b, f)
                if not os.path.exists(fa) or not os.path.exists(fb) or text(fa) != text(fb):
                    diff.append(os.path.relpath(fa))
            continue
        n += 1
        if not os.path.exists(b):
            diff.append(f"{os.path.relpath(a)} was not written")
        elif not os.path.exists(a) or text(a) != text(b):
            diff.append(os.path.relpath(a))
    names = ", ".join(os.path.basename(a) for a in pairs[::2])
    if diff:
        out("FAIL", f"{len(diff)} file(s) differ from a fresh run of {label}: regenerate and commit, "
                    "or the board was edited by hand", *["  " + d for d in diff[:15]])
    out("PASS", f"{names}: identical to a fresh run of {label}")


def k_checkpcb(board, log, pcb):
    s = open(log, encoding="utf8").read()
    head = re.search(r"^(\d+) footprints, (\d+) pads", s, re.M)
    if not head:
        out("FAIL", "checkpcb.py did not finish")
    issues = [l.strip() for l in s.splitlines() if l.startswith("  ")]
    x0, y0, x1, y1 = outline(pcb)
    acc, bad = [], []
    for l in issues:
        for rx, lim, why in ACCEPT_CHECKPCB.get(board, []):
            if re.search(rx, l):
                box = re.search(r"\(([-\d.e]+), ([-\d.e]+), ([-\d.e]+), ([-\d.e]+)\)", l)
                if lim is not None and box:
                    a, b, c, d = map(float, box.groups())
                    over = max(x0 - a, y0 - b, c - x1, d - y1)
                    if over > lim + 1e-9:
                        bad.append(f"{l}  -> {over:.2f} mm past the edge, accepted only up to {lim}")
                    else:
                        acc.append(f"{why} {over:.2f} mm")
                else:
                    acc.append(why)
                break
        else:
            bad.append(l)
    d = f"{head.group(1)} footprints, {head.group(2)} pads"
    if bad:
        out("FAIL", d + f"; {len(bad)} new issue(s)", *["  " + b for b in bad])
    out("PASS", d + ("; accepted: " + ", ".join(acc) if acc else "; clean"))


def k_checkcopper(log, rc):
    s = open(log, encoding="utf8").read()
    m = re.search(r"^(\d+) tracks, (\d+) vias, (\d+) pad-layers", s, re.M)
    if not m:
        out("FAIL", "checkcopper.py did not finish")
    d = f"{m.group(1)} tracks, {m.group(2)} vias, {m.group(3)} pad-layers; HV 0.6 mm"
    if rc != "0" or s.strip().splitlines()[-1].strip() != "clean":
        out("FAIL", d + ": clearance findings", *[l for l in s.splitlines() if l.startswith("  ")][:20])
    if m.group(2) != "0":
        out("FAIL", d + ": the pair is designed with no vias")
    out("PASS", d + ": clean")


def k_audit(log, rc):
    s = open(log, encoding="utf8").read()
    q = re.search(r"QSUMMARY cu=(\S+) detour=(\S+) vias=(\S+) islands=(\S+)", s)
    d = f"copper {q.group(1)} mm, {float(q.group(2)):.2f}x its floor, {q.group(3)} vias, pour islands {q.group(4)}" if q else "no summary"
    if rc == "0" and s.strip().splitlines()[-1].strip() == "clean":
        out("PASS", d + ": clean")
    rep = s.split("QSUMMARY", 1)[-1]
    found = [l for l in rep.splitlines() if l.startswith("  [")]
    out("FAIL", d + f": {len(found)} finding(s)", *(found[:20] or s.strip().splitlines()[-10:]))


def k_drc(board, report, how):
    if not os.path.exists(report):
        out("FAIL", f"kicad-cli wrote no report ({how})")
    r = json.load(open(report, encoding="utf8"))
    acc, bad = [], []
    for v in r.get("violations", []):
        refs = set(re.findall(r"\b(?:Footprint|of) ([A-Z]+\d+)\b", " ".join(i.get("description", "") for i in v.get("items", []))))
        for typ, want, why in ACCEPT_DRC.get(board, []):
            if v.get("type") == typ and refs == want:
                acc.append((v.get("severity"), why))
                break
        else:
            bad.append(f"  {v.get('severity')}: {v.get('type')}: {v.get('description')} {sorted(refs)}")
    unc = r.get("unconnected_items", [])
    par = r.get("schematic_parity", [])
    for u in unc[:10]:
        bad.append("  unconnected: " + " / ".join(i.get("description", "") for i in u.get("items", [])))
    bad += ["  parity: " + p.get("description", "") for p in par[:10]]
    ne = sum(1 for v in r.get("violations", []) if v.get("severity") == "error")
    nw = sum(1 for v in r.get("violations", []) if v.get("severity") == "warning")
    d = f"KiCad {r.get('kicad_version', '?')} ({how}): {ne} errors, {nw} warnings, {len(unc)} unconnected"
    if bad:
        out("FAIL", d + f"; {len(bad)} not accepted", *bad[:25])
    whys = sorted({w for _, w in acc})
    out("PASS", d + ("; all accepted: " + ", ".join(whys) if acc else "; clean"))


def k_bom(tmp_root):
    pairs = []
    for b in ("TS06-DISP", "TS06-DRV"):
        pairs += [os.path.join("PCB", b, "bom.md"), os.path.join(tmp_root, "PCB", b, "bom.md")]
    diff = [a for a, b in zip(pairs[::2], pairs[1::2]) if not os.path.exists(b) or text(a) != text(b)]
    counts = []
    for b in ("TS06-DISP", "TS06-DRV"):
        m = re.search(r"(\d+) parts fitted, (\d+) footprints left empty", open(os.path.join("PCB", b, "bom.md"), encoding="utf8").read())
        counts.append(f"{b} {m.group(1)} fitted" + (f" + {m.group(2)} DNP" if m and m.group(2) != "0" else "") if m else b)
    if diff:
        out("FAIL", "stale: " + ", ".join(diff) + " - run python3 tools/bom_pair.py and commit")
    out("PASS", ", ".join(counts) + ": identical to tools/bom_pair.py's output")


def k_case(log, rc, checks):
    s = open(log, encoding="utf8").read()
    env = re.search(r"envelope ([\d.]+) W x ([\d.]+) H x ([\d.]+) D", s)
    if rc != "0" or not env or not os.path.exists(checks):
        out("FAIL", "case_pair.py did not finish", *s.strip().splitlines()[-10:])
    rows = re.findall(r"^\| [\d]+ \| (.*?) \| .*? \| \*\*(OK|TIGHT|NOTE|FAIL)\*\* \|", open(checks, encoding="utf8").read(), re.M)
    count = {k: sum(1 for _, st in rows if st == k) for k in ("OK", "TIGHT", "NOTE", "FAIL")}
    fails = [w for w, st in rows if st == "FAIL"]
    new = [w for w in fails if w not in ACCEPT_CASE]
    d = (f"envelope {env.group(1)} x {env.group(2)} x {env.group(3)} mm; {len(rows)} checks: "
         f"{count['OK']} OK, {count['TIGHT']} TIGHT, {count['NOTE']} NOTE, {count['FAIL']} FAIL")
    if new:
        out("FAIL", d + f"; {len(new)} not accepted", *["  " + w for w in new])
    out("PASS", d + (" (both rejected jack-opening alternatives)" if fails else ""))


def k_case_fresh(tmp_case):
    here = os.path.join("3d", "case-pair")
    diff, n = [], 0
    for f in ["boards.json", "params.scad", "checks.md"] + sorted(
            os.path.join("out", x) for x in os.listdir(os.path.join(tmp_case, "out")) if x.endswith(".svg")):
        n += 1
        a, b = os.path.join(here, f), os.path.join(tmp_case, f)
        if f == "boards.json":              # the source hashes change with line endings; compare the geometry
            ja, jb = json.load(open(a, encoding="utf8")), json.load(open(b, encoding="utf8"))
            ja.pop("sources", None), jb.pop("sources", None)
            same = ja == jb
        else:
            same = text(a) == text(b)
        if not same:
            diff.append(f)
    if diff:
        out("FAIL", f"{len(diff)} of {n} stale: " + ", ".join(diff) + " - run python3 3d/case-pair/case_pair.py --extract and commit")
    out("PASS", f"{n} generated files identical to a fresh run")


if __name__ == "__main__":
    kind, args = sys.argv[1], sys.argv[2:]
    globals()["k_" + kind](*args)
PYEOF

echo "TS06-DISP + TS06-DRV verification   $(date '+%Y-%m-%d %H:%M')   $("$PY" -c 'import platform; print("python", platform.python_version())')"
echo "repository: $ROOT"

HAVE_NUMPY=1
"$PY" -c 'import numpy' >/dev/null 2>&1 || HAVE_NUMPY=0

# A scratch copy of what the generators read and write, so that nothing here touches the tree:
# they write rotated footprints into PCB/lib, the board files into PCB/<board>, the case model's
# outputs into 3d/case-pair, and the BOMs into PCB/<board>/bom.md.
G="$TMP/tree"
mkdir -p "$G/PCB" "$G/3d"
cp -R tools "$G/tools"
rm -rf "$G/tools/__pycache__"
cp -R PCB/lib "$G/PCB/lib"
cp -R PCB/TS06-FASCIA "$G/PCB/TS06-FASCIA"
cp -R 3d/case-pair "$G/3d/case-pair"

# ------------------------------------------------------------------------------ the pair as a whole
"$PY" tools/ts06pair.py > "$TMP/netlist.log" 2>&1
judge "netlist" netlist "$TMP/netlist.log" "$?"

"$PY" - > "$TMP/mate.log" 2>&1 <<'PYEOF'
import sys
sys.path.insert(0, "tools")
import mkpcb_drv as D, mkpcb_disp as S, ts06pair as P
bad = D.check_mate()
pins = sum(len(v) for v in P.HEADERS.values())
nets = sum(1 for v in P.HEADERS.values() for n in v if n)
print("MATE", len(bad), pins, nets, len(S.B.holes))
for b in bad:
    print("  " + b)
PYEOF
judge "mate" mate "$TMP/mate.log" "$?"

judge "firmware tables" firmware "$ROOT"

# ------------------------------------------------------------------------------ each board
for B in TS06-DISP TS06-DRV; do
  PCB="PCB/$B/$B.kicad_pcb"
  case $B in TS06-DISP) GEN=mkpcb_disp.py ;; *) GEN=mkpcb_drv.py ;; esac

  # the committed files against a fresh run of their generator (in the scratch tree)
  if (cd "$G" && TS06_OUT= "$PY" "tools/$GEN") > "$TMP/$B.gen.log" 2>&1; then
    judge "$B generator" same "tools/$GEN" \
      "PCB/$B/$B.kicad_pcb" "$G/PCB/$B/$B.kicad_pcb" \
      "PCB/$B/$B.kicad_pro" "$G/PCB/$B/$B.kicad_pro" \
      "PCB/$B/fp-lib-table" "$G/PCB/$B/fp-lib-table" \
      "PCB/lib/TS06.pretty" "$G/PCB/lib/TS06.pretty"
  else
    report FAIL "$B generator" "tools/$GEN did not run" "$TMP/$B.gen.log"
  fi

  "$PY" tools/checkpcb.py "$PCB" > "$TMP/$B.checkpcb.log" 2>&1
  judge "$B checkpcb" checkpcb "$B" "$TMP/$B.checkpcb.log" "$PCB"

  "$PY" tools/checkcopper.py "$PCB" --hv "HV185,SW,BLEED_*,FB_MID,COLON_*,ANODE_*,EMIT_*" > "$TMP/$B.copper.log" 2>&1
  judge "$B checkcopper --hv" checkcopper "$TMP/$B.copper.log" "$?"

  if [ "$HAVE_NUMPY" = 1 ]; then
    "$PY" tools/audit.py "$PCB" > "$TMP/$B.audit.log" 2>&1
    judge "$B audit" audit "$TMP/$B.audit.log" "$?"
  else
    report SKIP "$B audit" "numpy is not installed for $PY (pip install numpy)"
  fi
done

# ------------------------------------------------------------------------------ KiCad DRC
# A local KiCad 10 kicad-cli if there is one, else Docker, else SKIP. The DRC runs on a copy of the
# committed board with its project file (the HV net class) and the project library beside it.
DRC_HOW=""
KCLI=""
if [ "$NO_DRC" = 1 ]; then
  DRC_SKIP="skipped by --no-drc"
else
  for c in "${KICAD_CLI:-}" kicad-cli \
           "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli" \
           "/c/Program Files/KiCad/10.0/bin/kicad-cli.exe" \
           "/mnt/c/Program Files/KiCad/10.0/bin/kicad-cli.exe"; do
    [ -n "$c" ] || continue
    if command -v "$c" >/dev/null 2>&1 || [ -x "$c" ]; then
      v=$("$c" version 2>/dev/null | head -n 1 | tr -d '\r')
      case $v in
        1[0-9].*|[2-9][0-9].*) KCLI=$c; DRC_HOW="local kicad-cli $v"; break ;;
        *) DRC_SKIP="kicad-cli $c is version '${v:-?}', not 10+" ;;
      esac
    fi
  done
  IMG=${KICAD_IMAGE:-mirror.gcr.io/kicad/kicad:10.0}
  if [ -z "$KCLI" ]; then
    if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
      if docker image inspect "$IMG" >/dev/null 2>&1 || { echo "      (pulling $IMG, about 1 GB, once)"; docker pull "$IMG" >/dev/null 2>&1; }; then
        DRC_HOW="docker $IMG"
      else
        DRC_SKIP="docker could not pull $IMG"
      fi
    else
      DRC_SKIP="${DRC_SKIP:+$DRC_SKIP; }no KiCad 10 kicad-cli and no running Docker"
    fi
  fi
fi

for B in TS06-DISP TS06-DRV; do
  if [ -z "$DRC_HOW" ]; then
    if [ "$NO_DRC" = 1 ]; then report SKIP "$B drc" "$DRC_SKIP"
    else report SKIP "$B drc" "KiCad DRC not run: $DRC_SKIP (install KiCad 10, or set KICAD_CLI=...)"; fi
    continue
  fi
  D="$TMP/drc"
  mkdir -p "$D/PCB/$B" "$D/out"
  [ -d "$D/PCB/lib" ] || cp -R PCB/lib "$D/PCB/lib"
  cp "PCB/$B/$B.kicad_pcb" "PCB/$B/$B.kicad_pro" "PCB/$B/fp-lib-table" "$D/PCB/$B/"
  chmod -R a+rwX "$D" 2>/dev/null
  if [ -n "$KCLI" ]; then
    (cd "$D" && "$KCLI" pcb drc --refill-zones --severity-all --units mm --format json \
       -o "out/$B.json" "PCB/$B/$B.kicad_pcb") > "$TMP/$B.drc.log" 2>&1
  else
    HOSTD=$D
    if command -v cygpath >/dev/null 2>&1; then HOSTD=$(cygpath -w "$D"); fi
    USERFLAG=""
    if [ "$(uname -s)" = Linux ]; then USERFLAG="--user $(id -u):$(id -g)"; fi
    # shellcheck disable=SC2086
    MSYS_NO_PATHCONV=1 docker run --rm $USERFLAG -v "$HOSTD":/w -w /w -e HOME=/tmp "$IMG" \
      kicad-cli pcb drc --refill-zones --severity-all --units mm --format json \
      -o "/w/out/$B.json" "/w/PCB/$B/$B.kicad_pcb" > "$TMP/$B.drc.log" 2>&1
  fi
  judge "$B drc" drc "$B" "$D/out/$B.json" "$DRC_HOW"
done

# ------------------------------------------------------------------------------ BOM and case
if (cd "$G" && "$PY" tools/bom_pair.py) > "$TMP/bom.log" 2>&1; then
  judge "bom" bom "$G"
else
  report FAIL "bom" "tools/bom_pair.py did not run" "$TMP/bom.log"
fi

(cd "$G" && FASCIA_PCB= "$PY" 3d/case-pair/case_pair.py --extract) > "$TMP/case.log" 2>&1
judge "case" case "$TMP/case.log" "$?" "$G/3d/case-pair/checks.md"
if [ -s "$G/3d/case-pair/checks.md" ]; then
  judge "case outputs" case_fresh "$G/3d/case-pair"
fi

echo "----"
echo "$NPASS PASS, $NFAIL FAIL, $NSKIP SKIP"
[ "$NFAIL" -eq 0 ]
