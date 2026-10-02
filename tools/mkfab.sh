#!/usr/bin/env bash
# tools/mkfab.sh - the fab package of each TS06 board (grill.md G8, second half):
#
#     tools/mkfab.sh                          # all three: TS06-DISP, TS06-DRV and the fascia R with the divider gold
#     tools/mkfab.sh TS06-DRV                 # one board
#     tools/mkfab.sh TS06-FASCIA-rhythm       # the fascia R (rev A) with the default gold, divider
#     tools/mkfab.sh TS06-FASCIA-rhythm --gold ladder     # another gold; --gold none is the bare board
#     tools/mkfab.sh --keep                   # keep the scratch directory and say where
#     tools/mkfab.sh TS06-FASCIA-rhythm --open-holes      # the fascia with every control bushing hole opened by 0.4 mm
#                                             # (8.8 -> 9.2, 8.0 -> 8.4): an EXTRA zip, fab/TS06-FASCIA-R-revA-divider-holes04-fab.zip
#
# For each board it:
#   1. copies the board, its project (net classes), its .kicad_dru (the 0.8 mm HV pad rule, which the
#      pour fill must respect), its fp-lib-table and PCB/lib to a scratch directory. The committed
#      files are only read: the board in the repository stays unfilled (G8's first half, filling the
#      committed boards, is the owner's decision). THE FASCIA is not plotted as committed: its gold is
#      the F.Cu / F.Mask art that tools/fascia_gold.py draws, so the art board is built in the scratch
#      directory (fascia_gold.py VARIANT OUT --base R, with its own checks) and that board is plotted.
#      Nothing under PCB/ is written;
#   2. exports the Gerbers with `kicad-cli pcb export gerbers --check-zones` (KiCad fills every pour
#      before it plots) and the Excellon drills with `kicad-cli pcb export drill` (plated and
#      non-plated holes in separate files, plus a Gerber X2 drill map);
#   3. exports the copper layers a second time WITHOUT --check-zones, as a control;
#   4. counts the region blocks (G36 ... G37) in every copper Gerber of both exports. A copper layer
#      that carries a pour in the board file must have more regions filled than unfilled, or the
#      board FAILs; a layer with no pour in the board file is reported as such;
#   5. (fascia with a gold) reads the plotted Gerbers back with tools/gerbers.py gold: F.Cu must carry
#      the gold copper and F.Mask must have openings over it (a mask over the gold hides it). The check
#      is run a second time on a mask with the gold's openings removed, and that run must FAIL;
#   6. zips the filled set to fab/<board>-rev<REV>-fab.zip (REV from the board's title block); the
#      fascia's is fab/TS06-FASCIA-R-rev<REV>-<gold>-fab.zip, so the gold is visible in the name
#      (<gold> is the variant, or "bare" for --gold none). If a rebuilt zip differs from the one already
#      there only in the creation dates the Gerbers carry, the old zip is kept and the run says so.
#
# --open-holes (fascia only; with no board named it builds the fascia alone) is a variant held by being an extra file,
# not by a branch: step 1 builds the scratch base board with `tools/mkpcb_fascia_rhythm.py --out FILE --open-holes` (the
# committed board and PCB/lib are not touched; without the flag that script writes the committed board byte for byte),
# the gold is drawn on it with `tools/fascia_gold.py --base-pcb`, and the zip's name carries `-holes04`. After the
# Gerbers are read back, the non-plated drill file must hold exactly the opened sizes (one 9.2, four 8.4, four 2.7).
# Nothing else changes: the three default zips and fab/ORDER.md are not rebuilt or edited by it. See fab/HOLES-VARIANT.md.
#
# It prints a Markdown table of the region counts (the one in fab/README.md) and exits 1 if any
# board FAILed. Nothing but fab/*.zip is written in the working tree.
#
# Needs: bash, python3, zip; the fascia's gold check also numpy, scipy and Pillow. KiCad 10's kicad-cli:
# a local one (on PATH or KICAD_CLI=...), or Docker with the image in KICAD_IMAGE (default
# mirror.gcr.io/kicad/kicad:10.0), as tools/verify_pair.sh.
set -u

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT" || exit 2
KEEP=0
BOARDS=""
GOLD=divider
GOLD_SET=0
OPEN=0
while [ $# -gt 0 ]; do
  a=$1; shift
  case $a in
    --keep) KEEP=1 ;;
    --open-holes) OPEN=1 ;;
    --gold) [ $# -gt 0 ] || { echo "--gold needs a variant (ladder, divider, fans, guilloche or none)"; exit 2; }
            GOLD=$1; GOLD_SET=1; shift ;;
    --gold=*) GOLD=${a#--gold=}; GOLD_SET=1 ;;
    -h|--help) sed -n '2,44p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    TS06-DISP|TS06-DRV|TS06-FASCIA-rhythm) BOARDS="$BOARDS $a" ;;
    TS06-*) echo "unknown board: $a (TS06-DISP, TS06-DRV, TS06-FASCIA-rhythm)"; exit 2 ;;
    *) echo "unknown argument: $a (try --help)"; exit 2 ;;
  esac
done
if [ "$OPEN" = 1 ]; then
  BOARDS=${BOARDS:-TS06-FASCIA-rhythm}
  case " $BOARDS " in
    *" TS06-DISP "*|*" TS06-DRV "*) echo "--open-holes applies to the fascia only: tools/mkfab.sh TS06-FASCIA-rhythm --open-holes"; exit 2 ;;
  esac
fi
BOARDS=${BOARDS:-TS06-DISP TS06-DRV TS06-FASCIA-rhythm}
case $GOLD in
  ladder|divider|fans|guilloche|none) ;;
  *) echo "unknown gold: $GOLD (ladder, divider, fans, guilloche or none)"; exit 2 ;;
esac
case " $BOARDS " in
  *" TS06-FASCIA-rhythm "*) ;;
  *) [ "$GOLD_SET" = 1 ] && { echo "--gold only applies to TS06-FASCIA-rhythm"; exit 2; } ;;
esac
LAYERS="F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts"   # through-hole boards: no paste
LAYERS_FASCIA="$LAYERS,B.Paste"            # the fascia's resistors are SMD on the back: a back paste layer
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
  REV=$(sed -n 's/^[[:space:]]*(rev "\([^"]*\)").*/\1/p' "PCB/$B/$B.kicad_pcb" | head -n 1)
  REV=${REV:-X}
  # N: the name of the scratch board (the Gerbers are named after it); Z: the zip; PL: the plotted layers
  N=$B; Z="fab/$B-rev$REV-fab.zip"; PL=$LAYERS; ARTNOTE=""
  if [ "$B" = TS06-FASCIA-rhythm ]; then
    TAG=$GOLD; [ "$GOLD" = none ] && TAG=bare
    [ "$OPEN" = 1 ] && TAG="$TAG-holes04"
    N="TS06-FASCIA-R-$TAG"; Z="fab/TS06-FASCIA-R-rev$REV-$TAG-fab.zip"; PL=$LAYERS_FASCIA
  fi
  mkdir -p "$TMP/PCB/$N" "$TMP/out/$N/filled" "$TMP/out/$N/unfilled"
  cp "PCB/$B/$B.kicad_pro" "$TMP/PCB/$N/$N.kicad_pro"
  cp "PCB/$B/fp-lib-table" "$TMP/PCB/$N/"
  [ -f "PCB/$B/$B.kicad_dru" ] && cp "PCB/$B/$B.kicad_dru" "$TMP/PCB/$N/$N.kicad_dru"
  BASE_PCB="PCB/$B/$B.kicad_pcb"; BASE_ARGS=""
  if [ "$OPEN" = 1 ]; then
    # the variant's base board: the generator's own board with every control hole opened by 0.4 mm, in the scratch directory
    BASE_PCB="$TMP/$N.base.kicad_pcb"
    if ! python3 tools/mkpcb_fascia_rhythm.py --out "$BASE_PCB" --open-holes > "$TMP/$N.open.log" 2>&1; then
      echo "FAIL $B: tools/mkpcb_fascia_rhythm.py --open-holes failed; not zipped"; sed 's/^/    /' "$TMP/$N.open.log"; FAILED=1; continue
    fi
    BASE_ARGS="--base-pcb $BASE_PCB"
  fi
  if [ "$B" = TS06-FASCIA-rhythm ] && [ "$GOLD" != none ]; then
    # the art board, built in the scratch directory with the generator's own checks (base R)
    # shellcheck disable=SC2086
    if ! python3 tools/fascia_gold.py "$GOLD" "$TMP/PCB/$N/$N.kicad_pcb" --base R $BASE_ARGS > "$TMP/$N.gold.log" 2>&1; then
      echo "FAIL $B: tools/fascia_gold.py $GOLD --base R failed its own checks; not zipped"; sed 's/^/    /' "$TMP/$N.gold.log"; FAILED=1; continue
    fi
    ARTNOTE=$(head -n 1 "$TMP/$N.gold.log")
  else
    cp "$BASE_PCB" "$TMP/PCB/$N/$N.kicad_pcb"
  fi
  chmod -R a+rwX "$TMP" 2>/dev/null
  PCB="PCB/$N/$N.kicad_pcb"
  kc pcb export gerbers --check-zones --layers "$PL" -o "out/$N/filled/" "$PCB" \
    > "$TMP/$N.gerbers.log" 2>&1
  kc pcb export drill --format excellon --excellon-units mm --excellon-separate-th \
       --generate-map --map-format gerberx2 -o "out/$N/filled/" "$PCB" > "$TMP/$N.drill.log" 2>&1
  kc pcb export gerbers --layers "$COPPER" -o "out/$N/unfilled/" "$PCB" > "$TMP/$N.control.log" 2>&1
  # count the regions, judge, and write the table rows
  python3 - "$TMP/out/$N" "$TMP/$PCB" "$B" "$REV" >> "$ROWS" <<'EOF'
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
  # a board with no plated hole (the fascia) gets no plated drill file: an empty one only confuses a fab's upload
  for f in "$TMP/out/$N/filled/"*-PTH.drl; do
    if [ -f "$f" ] && [ "$(grep -c '^X' "$f")" = 0 ]; then rm -f "$f" "${f%.drl}-drl_map.gbr"; fi
  done
  n=$(ls "$TMP/out/$N/filled" | wc -l)
  if [ "$n" -lt 9 ]; then
    echo "FAIL $B: only $n files exported (see the logs)"; cat "$TMP/$N.gerbers.log" "$TMP/$N.drill.log"; FAILED=1; continue
  fi
  if [ $rc != 0 ]; then FAILED=1; echo "FAIL $B: a copper layer lacks its pour; not zipped"; continue; fi
  if [ "$B" = TS06-FASCIA-rhythm ] && [ "$GOLD" != none ]; then
    # the gold must be in the Gerbers, with openings in the mask over it (and the check must be able to fail)
    echo "$B: $ARTNOTE"
    echo "$B: the gold in the Gerbers (F.Cu and F.Mask), read back by tools/gerbers.py:"
    if ! python3 tools/gerbers.py gold "$TMP/out/$N/filled"; then
      echo "FAIL $B: the gold is not exposed in the Gerbers; not zipped"; FAILED=1; continue
    fi
  fi
  if [ "$OPEN" = 1 ]; then
    # the opened holes must be in the drill file the fab drills from: one 9.2 (the dial), four 8.4, the four 2.7 screw holes
    if ! python3 - "$TMP/out/$N/filled" <<'PYEOF'
import collections, glob, re, sys
f = glob.glob(sys.argv[1] + "/*-NPTH.drl")
if not f:
    sys.exit("no NPTH drill file")
tool, cur, hits = {}, None, collections.Counter()
for l in open(f[0], encoding="latin-1"):
    l = l.strip()
    m = re.match(r"T(\d+)C([\d.]+)", l)
    if m:
        tool[m.group(1)] = float(m.group(2))
        continue
    m = re.match(r"T(\d+)$", l)
    if m:
        cur = m.group(1)
        continue
    if cur and l.startswith("X"):
        hits[tool[cur]] += 1
got = dict(sorted(hits.items()))
want = {2.7: 4, 8.4: 4, 9.2: 1}
print("the NPTH drill file holds (diameter: holes) %s; the variant needs %s: %s" % (got, want, "PASS" if got == want else "FAIL"))
sys.exit(0 if got == want else 1)
PYEOF
    then echo "FAIL $B: the opened holes are not what the drill file holds; not zipped"; FAILED=1; continue; fi
  fi
  rm -f "$TMP/old.zip"
  if [ -f "$Z" ]; then cp "$Z" "$TMP/old.zip"; fi
  rm -f "$Z"
  (cd "$TMP/out/$N/filled" && zip -q -X -j "$ROOT/$Z" ./*)
  # a rebuild that differs from the zip already there only in creation dates: keep the old one
  if [ -f "$TMP/old.zip" ] && python3 - "$TMP/old.zip" "$Z" <<'EOF'
import re, sys, zipfile
def norm(path):
    z = zipfile.ZipFile(path)
    d = {}
    for n in z.namelist():
        t = z.read(n).decode("latin-1")
        # the dates KiCad writes: ISO times, "date 2026-09-30 09:14:41", and the drill header's date
        t = re.sub(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(\+\d{2}:\d{2})?", "DATE", t)
        d[n] = t
    return d
sys.exit(0 if norm(sys.argv[1]) == norm(sys.argv[2]) else 1)
EOF
  then
    cp "$TMP/old.zip" "$Z"
    echo "$Z: unchanged, a rebuild differs only in the creation dates; the zip already there is kept ($(unzip -Z1 "$Z" | wc -l) files, $(( $(stat -c %s "$Z") / 1024 )) kB)"
  else
    echo "$Z: $(unzip -Z1 "$Z" | wc -l) files, $(( $(stat -c %s "$Z") / 1024 )) kB"
  fi
  unzip -Z1 "$Z" | sed 's/^/    /'
done

echo
echo "| Board | Copper layer | Pour in the board file (net) | Regions without --check-zones | Regions with --check-zones | Difference | Check |"
echo "|---|---|---|---|---|---|---|"
cat "$ROWS"
exit $FAILED
