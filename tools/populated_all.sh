#!/usr/bin/env bash
# tools/populated_all.sh [OUTDIR] - every populated render, the GLBs, the stack pictures and the fit table, in one go.
#
#     tools/populated_all.sh                 # writes 3d/populated/
#     tools/populated_all.sh /some/dir       # elsewhere (scratch run)
#
# Steps, each of which can be run alone (the commands are the ones in 3d/populated/README.md):
#   1  tools/build_models3d.py       OpenSCAD -> .wrl for the parts nothing else draws          (a few seconds)
#   2  tools/model_coverage.py       every footprint has a model that exists, or is allowlisted; exits 1 otherwise
#   3  tools/render_populated.py     per board: top, iso, bottom PNG and the populated GLB      (KiCad in Docker, ~6 min)
#   4  tools/stack_frame.py          the placement of the boards from 3d/case-pair/case_pair.py
#   5  render_stack.mjs              the assembled stack, front and iso (headless Chromium + three.js; no network)
#   6  tools/fit_table.py            the fit table, from the placed models
# Needs: Docker with the kicad image (nohup dockerd >/dev/null 2>&1 & if it is down), OpenSCAD, Python 3 with Pillow and numpy,
# node with playwright (/opt/node22/lib/node_modules, browsers in $PLAYWRIGHT_BROWSERS_PATH, default /opt/pw-browsers).
# Nothing under PCB/ or fab/ is read for writing; the boards are copied to scratch directories.
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
OUT=${1:-$ROOT/3d/populated}
FASCIA=${FASCIA:-TS06-FASCIA-rhythm}
export PLAYWRIGHT_BROWSERS_PATH=${PLAYWRIGHT_BROWSERS_PATH:-/opt/pw-browsers}
cd "$ROOT"
mkdir -p "$OUT"
say() { printf '\n== %s\n' "$*"; }
say "1 models";   python3 tools/build_models3d.py
say "2 coverage"; python3 tools/model_coverage.py
for B in TS06-DISP TS06-DRV "$FASCIA"; do
  say "3 render $B"; python3 tools/render_populated.py "$B" "$OUT"
done
say "4 stack frame"; python3 tools/stack_frame.py "$OUT/stack.json" --fascia "$FASCIA"
say "5 stack pictures"; node 3d/populated/stack/render_stack.mjs "$OUT/stack.json" "$OUT" "$OUT"
python3 - "$OUT/TS06-stack-front.png" "$OUT/TS06-stack-iso.png" <<'PY'
import sys
sys.path.insert(0, "tools")
import render_populated as r          # trim to the picture, 2400 px wide at most
for f in sys.argv[1:]:
    print(f, r.trim_png(f, r.MAX_W))
PY
say "6 fit table"; python3 tools/fit_table.py "$OUT" "$OUT/fit-table.md" "$OUT/fit-table.json" --fascia "$FASCIA"
say "done: $OUT"
