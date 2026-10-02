#!/bin/bash
# viewer2/tools/mksections.sh - the page's schematic sections, regenerated from the repository alone.
#
#   tools/mksections.sh REPO OUTDIR
#
# Writes OUTDIR/sch-<board>-<nn>-<section>.svg (one per schematic sheet, cropped and slimmed),
# OUTDIR/layout-<board>-<section>.png (each section lit up on its board) and OUTDIR/sections.json,
# the manifest tools/sections.py reads. This is what build.sh runs when SCH is not given, so a fresh
# clone needs nothing kept elsewhere.
#
# How, all of it the repository's own tools:
#   1. kicad-cli sch export svg (KiCad 10, in Docker: mirror.gcr.io/kicad/kicad:10.0, or KICAD_CLI=a local
#      binary) turns every sheet of PCB/TS06-DRV and PCB/TS06-DISP into a black-on-white SVG;
#   2. tools/mksch_pair.py --svg-out crops and slims them under their section names;
#   3. tools/highlight_pair.py draws the layout pictures and writes sections.json (the section names,
#      summaries, parts and nets come from tools/mksch_pair.py and tools/ts06pair.py).
# The repository is only read. The schematic sheets (.kicad_sch) must be in PCB/ (they are committed).
set -euo pipefail
[ $# -eq 2 ] || { echo "usage: $0 REPO OUTDIR"; exit 1; }
REPO=$(cd "$1" && pwd)
mkdir -p "$2"
OUT=$(cd "$2" && pwd)
IMAGE=${KICAD_IMAGE:-mirror.gcr.io/kicad/kicad:10.0}
RAW=$(mktemp -d "${TMPDIR:-/tmp}/ts06-sch-raw.XXXXXX")
trap 'rm -rf "$RAW"' EXIT
chmod 777 "$RAW"
for B in TS06-DRV TS06-DISP; do
  [ -f "$REPO/PCB/$B/$B.kicad_sch" ] || { echo "no PCB/$B/$B.kicad_sch"; exit 1; }
  if [ -n "${KICAD_CLI:-}" ]; then
    (cd "$REPO" && "$KICAD_CLI" sch export svg --exclude-drawing-sheet --black-and-white -o "$RAW" "PCB/$B/$B.kicad_sch") | tail -1
  else
    docker run --rm --user "$(id -u):$(id -g)" -v "$REPO":/w:ro -v "$RAW":/o -w /w -e HOME=/tmp "$IMAGE" \
      kicad-cli sch export svg --exclude-drawing-sheet --black-and-white -o /o "PCB/$B/$B.kicad_sch" | tail -1
  fi
done
rm -f "$OUT"/sch-*.svg "$OUT"/layout-*.png "$OUT"/sections.json
python3 "$REPO/tools/mksch_pair.py" --svg-out "$RAW" "$OUT"
python3 "$REPO/tools/highlight_pair.py" "$OUT"
du -sk "$OUT" | awk '{printf "sections: %d kB in %s\n", $1, "'"$OUT"'"}'
