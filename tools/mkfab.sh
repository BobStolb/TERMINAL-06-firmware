#!/usr/bin/env bash
# tools/mkfab.sh - the fab package of each board of the through-hole pair (grill.md G8, second half):
#
#     tools/mkfab.sh                  # TS06-DISP and TS06-DRV
#     tools/mkfab.sh TS06-DRV         # one board
#     tools/mkfab.sh --keep           # keep the scratch directory and say where
#
# For each board it:
#   1. copies the board, its project (net classes), its .kicad_dru (the 0.8 mm HV pad rule, which the
#      pour fill must respect), its fp-lib-table and PCB/lib to a scratch directory. The committed
#      files are only read: the board in the repository stays unfilled (G8's first half, filling the
#      committed boards, is the owner's decision);
#   2. exports the Gerbers with `kicad-cli pcb export gerbers --check-zones` (KiCad fills every pour
#      before it plots) and the Excellon drills with `kicad-cli pcb export drill` (plated and
#      non-plated holes in separate files, plus a Gerber X2 drill map);
#   3. exports the copper layers a second time WITHOUT --check-zones, as a control;
#   4. counts the region blocks (G36 ... G37) in every copper Gerber of both exports. A copper layer
#      that carries a pour in the board file must have more regions filled than unfilled, or the
#      board FAILs; a layer with no pour in the board file is reported as such;
#   5. zips the filled set to fab/<board>-rev<REV>-fab.zip (REV from the board's title block).
#
# It prints a Markdown table of the region counts (the one in fab/README.md) and exits 1 if any
# board FAILed. Nothing but fab/*.zip is written in the working tree.
#
# Needs: bash, python3, zip. KiCad 10's kicad-cli: a local one (on PATH or KICAD_CLI=...), or Docker
# with the image in KICAD_IMAGE (default mirror.gcr.io/kicad/kicad:10.0), as tools/verify_pair.sh.
set -u

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT" || exit 2
KEEP=0
BOARDS=""
for a in "$@"; do
  case $a in
    --keep) KEEP=1 ;;
    -h|--help) sed -n '2,26p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    TS06-*) BOARDS="$BOARDS $a" ;;
    *) echo "unknown argument: $a (try --help)"; exit 2 ;;
  esac
done
BOARDS=${BOARDS:-TS06-DISP TS06-DRV}
LAYERS="F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts"   # through-hole only: no paste
COPPER="F.Cu,B.Cu"

command -v zip >/dev/null 2>&1 || { echo "zip is required"; exit 2; }
command -v python3 >/dev/null 2>&1 || { echo "python3 is required"; exit 2; }

# ---------------------------------------------------------------- kicad-cli: local 10+, else Docker
KCLI=""
for c in "${KICAD_CLI:-}" kicad-cli; do
  [ -n "$c" ] || continue
  if command -v "$c" >/dev/null 2>&1 || [ -x "$c" ]; then
    v=$("$c" version 2>/dev/null | head -n 1 | tr -d '\r')
    case $v in 1[0-9].*|[2-9][0-9].*) KCLI=$c; HOW="local kicad-cli $v"; break ;; esac
  fi
done
IMG=${KICAD_IMAGE:-mirror.gcr.io/kicad/kicad:10.0}
if [ -z "$KCLI" ]; then
  if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    docker image inspect "$IMG" >/dev/null 2>&1 || { echo "(pulling $IMG, about 1 GB, once)"; docker pull "$IMG" >/dev/null 2>&1; } \
      || { echo "docker could not pull $IMG"; exit 2; }
    HOW="docker $IMG"
  else
    echo "no KiCad 10 kicad-cli and no running Docker (start it: nohup dockerd >/dev/null 2>&1 &)"; exit 2
  fi
fi

TMP=$(mktemp -d "${TMPDIR:-/tmp}/mkfab.XXXXXX")
cleanup() { if [ "$KEEP" = 1 ]; then echo "scratch kept: $TMP"; else rm -rf "$TMP"; fi; }
trap cleanup EXIT

# kc ARGS...: run kicad-cli with the scratch directory as the working directory (/w in Docker)
kc() {
  if [ -n "$KCLI" ]; then
    (cd "$TMP" && "$KCLI" "$@")
  else
    USERFLAG=""
    if [ "$(uname -s)" = Linux ]; then USERFLAG="--user $(id -u):$(id -g)"; fi
    # shellcheck disable=SC2086
    MSYS_NO_PATHCONV=1 docker run --rm $USERFLAG -v "$TMP":/w -w /w -e HOME=/tmp "$IMG" kicad-cli "$@"
  fi
}

echo "kicad-cli: $HOW"
mkdir -p "$TMP/PCB" fab
cp -R PCB/lib "$TMP/PCB/lib"
FAILED=0
ROWS="$TMP/rows.txt"
: > "$ROWS"
for B in $BOARDS; do
  if [ ! -f "PCB/$B/$B.kicad_pcb" ]; then echo "FAIL $B: no PCB/$B/$B.kicad_pcb"; FAILED=1; continue; fi
  mkdir -p "$TMP/PCB/$B" "$TMP/out/$B/filled" "$TMP/out/$B/unfilled"
  cp "PCB/$B/$B.kicad_pcb" "PCB/$B/$B.kicad_pro" "PCB/$B/fp-lib-table" "$TMP/PCB/$B/"
  [ -f "PCB/$B/$B.kicad_dru" ] && cp "PCB/$B/$B.kicad_dru" "$TMP/PCB/$B/"
  chmod -R a+rwX "$TMP" 2>/dev/null
  REV=$(sed -n 's/^[[:space:]]*(rev "\([^"]*\)").*/\1/p' "PCB/$B/$B.kicad_pcb" | head -n 1)
  REV=${REV:-X}
  PCB="PCB/$B/$B.kicad_pcb"
  kc pcb export gerbers --check-zones --layers "$LAYERS" -o "out/$B/filled/" "$PCB" \
    > "$TMP/$B.gerbers.log" 2>&1
  kc pcb export drill --format excellon --excellon-units mm --excellon-separate-th \
       --generate-map --map-format gerberx2 -o "out/$B/filled/" "$PCB" > "$TMP/$B.drill.log" 2>&1
  kc pcb export gerbers --layers "$COPPER" -o "out/$B/unfilled/" "$PCB" > "$TMP/$B.control.log" 2>&1
  # count the regions, judge, and write the table rows
  python3 - "$TMP/out/$B" "$PCB" "$B" "$REV" >> "$ROWS" <<'EOF'
import glob, os, re, sys
out, pcb, board, rev = sys.argv[1:5]
text = open(pcb, encoding="utf8").read()
# the copper layers that carry a pour (a zone with a net that is not a keep-out) in the board file
poured = set()
for m in re.finditer(r"\n\t\(zone\b", text):
    depth, k = 0, m.start() + 2
    while True:
        c = text[k]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                break
        k += 1
    z = text[m.start():k + 1]
    net = re.search(r'\(net_name "([^"]*)"\)', z) or re.search(r'\(net "([^"]*)"\)', z)
    if "(keepout" in z or not net or not net.group(1):
        continue
    lay = re.search(r"\(layers? ((?:\"[^\"]+\" ?)+)\)", z)
    for L in re.findall(r'"([^"]+)"', lay.group(1) if lay else ""):
        poured.add((L, net.group(1)))
def gerber(folder, layer):
    tag = {"F.Cu": "F_Cu", "B.Cu": "B_Cu"}[layer]
    fs = [f for f in glob.glob(os.path.join(folder, "*")) if tag in os.path.basename(f)
          and not f.endswith(".gbrjob")]
    return fs[0] if fs else None
def regions(path):
    if not path:
        return None, None
    lines = open(path, encoding="latin-1").read().splitlines()
    return sum(1 for l in lines if l.strip() == "G36*"), sum(1 for l in lines if l.strip() == "G37*")
bad = 0
for layer in ("F.Cu", "B.Cu"):
    f = gerber(os.path.join(out, "filled"), layer)
    u = gerber(os.path.join(out, "unfilled"), layer)
    (f36, f37), (u36, u37) = regions(f), regions(u)
    nets = sorted(n for (L, n) in poured if L == layer)
    if f is None or u is None:
        verdict, bad = "FAIL: no Gerber", 1
    elif f36 != f37 or u36 != u37:
        verdict, bad = "FAIL: G36/G37 unbalanced", 1
    elif nets and f36 > u36:
        verdict = "PASS"
    elif nets:
        verdict, bad = "FAIL: the pour is missing", 1
    else:
        verdict = "n/a: no pour on this layer"
    kb = lambda p: "%.0f kB" % (os.path.getsize(p) / 1024.0) if p else "-"
    print("| %s rev %s | %s | %s | %s (%s) | %s (%s) | %s | %s |" % (
        board, rev, layer, ", ".join(nets) or "none", u36, kb(u), f36, kb(f),
        "+%d" % (f36 - u36) if f36 is not None else "-", verdict))
sys.exit(bad)
EOF
  rc=$?
  n=$(ls "$TMP/out/$B/filled" | wc -l)
  if [ "$n" -lt 9 ]; then
    echo "FAIL $B: only $n files exported (see the logs)"; cat "$TMP/$B.gerbers.log" "$TMP/$B.drill.log"; FAILED=1; continue
  fi
  if [ $rc != 0 ]; then FAILED=1; echo "FAIL $B: a copper layer lacks its pour; not zipped"; continue; fi
  Z="fab/$B-rev$REV-fab.zip"
  rm -f "$Z"
  (cd "$TMP/out/$B/filled" && zip -q -X -j "$ROOT/$Z" ./*)
  echo "$Z: $(unzip -Z1 "$Z" | wc -l) files, $(( $(stat -c %s "$Z") / 1024 )) kB"
  unzip -Z1 "$Z" | sed 's/^/    /'
done

echo
echo "| Board | Copper layer | Pour in the board file (net) | Regions without --check-zones | Regions with --check-zones | Difference | Check |"
echo "|---|---|---|---|---|---|---|"
cat "$ROWS"
exit $FAILED
