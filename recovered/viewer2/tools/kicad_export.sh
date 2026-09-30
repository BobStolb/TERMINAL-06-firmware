#!/bin/bash
# Runs INSIDE mirror.gcr.io/kicad/kicad:10.0 (one container for all boards, so only one KiCad
# docker ever runs). Mounts: /w = the scratch tree (brd/<BOARD>/<BOARD>.kicad_pcb prepared by
# prep_board.py), /m = the 3D model library (KICAD10_3DMODEL_DIR).
#   kicad_export.sh BOARD...        writes /w/out/<BOARD>.glb, <BOARD>-drc.json, img/<BOARD>-{top,bottom,iso}.png
# RENDER=0 skips the PNG renders; RQ sets their quality (default high).
set -u
RQ=${RQ:-high}
mkdir -p /w/out/img
for B in "$@"; do
  cd /w/brd/$B || exit 1
  t0=$(date +%s)
  # refill every zone first (the stored fill may be stale), and keep KiCad's own DRC result
  kicad-cli pcb drc --refill-zones --save-board --severity-all --format json --units mm \
    -o /w/out/$B-drc.json $B.kicad_pcb >/w/out/$B-drc.log 2>&1
  kicad-cli pcb export glb -D KICAD10_3DMODEL_DIR=/m -f \
    --include-pads --include-tracks --include-zones --include-silkscreen --include-soldermask \
    -o /w/out/$B.glb $B.kicad_pcb >/w/out/$B-glb.log 2>&1 || { echo "GLB FAILED $B"; cat /w/out/$B-glb.log; }
  if [ "${RENDER:-1}" != 0 ]; then
    R="kicad-cli pcb render -D KICAD10_3DMODEL_DIR=/m --use-board-stackup-colors --quality $RQ --background transparent"
    $R --side top    --zoom 1.5 --width 1800 --height 1000 -o /w/out/img/$B-top.png    $B.kicad_pcb >/dev/null 2>&1
    $R --side bottom --zoom 1.5 --width 1800 --height 1000 -o /w/out/img/$B-bottom.png $B.kicad_pcb >/dev/null 2>&1
    $R --side top --perspective --rotate "-40,0,-20" --zoom 1.3 --width 1800 --height 1100 \
       -o /w/out/img/$B-iso.png $B.kicad_pcb >/dev/null 2>&1
  fi
  echo "$B: $(( $(date +%s) - t0 )) s"
done
