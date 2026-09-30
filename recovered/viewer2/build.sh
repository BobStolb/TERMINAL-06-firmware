#!/bin/bash
# viewer2/build.sh - rebuild the TS06 board viewer (site/) from the repository's current boards.
#
#   ./build.sh [REPO]            full build: KiCad exports + renders, conversions, assembly, sections, page
#   RENDER=0 ./build.sh [REPO]   skip the PNG renders (keeps the ones already in site/img)
#   PAGE_ONLY=1 ./build.sh       only re-stamp the page (src/ -> site/) and re-copy the sections
#   VIEWER_BRANCH=...            the branch named on the page (default pcb/kicad-boards); the commit is REPO's HEAD
#
# REPO defaults to the current directory if it holds PCB/TS06-DRV, else /home/user/TERMINAL-06-firmware.
# The repository is only read. Nothing is committed and nothing in it is written (scratch copies only).
#
# NEEDS
#   docker, with the image mirror.gcr.io/kicad/kicad:10.0 (KICAD_IMAGE=... to change). One container
#       runs every KiCad step, so only one KiCad docker is ever up. If `docker info` fails, start the
#       daemon first:  nohup dockerd >/dev/null 2>&1 &
#   python3 (standard library; Pillow, if present, trims the renders' empty margins)
#   node + npm: gltfpack 1.3.0 is installed into tools/node_modules on first use (npm registry access)
#   MODELS   KiCad's 3D models, mounted as KICAD10_3DMODEL_DIR (default: ../3dmodels beside viewer2/).
#            Parts whose model is missing export without a body; the page draws proxies for them.
#   SCH      the schematic sections (default: ../sch/out). sections.json there is copied with the files
#            it names (SVG/PNG/JPG/WEBP only; a PDF is skipped); without it a 4-section stub in the same
#            schema is generated from tools/ts06pair.py.
#   The case parts come from REPO/3d/case-pair/out/*.stl as committed (cheeks, brow, top, trench, base,
#   rear, and fascia_frame for variant F; regenerate them with `python3 3d/case-pair/case_pair.py
#   --render`, which needs OpenSCAD). The assembly frame, the fascia positions, the control bodies,
#   the lead and the case checks come from REPO/3d/case-pair/case_pair.py itself, imported read-only.
#
# BOARDS  TS06-DRV, TS06-DISP and the fascia variants that exist: TS06-FASCIA (A, centred),
#   TS06-FASCIA-wide (W) and TS06-FASCIA-rhythm (R). F (FASCIA_FRAME=1, a printed frame) is a case-model
#   variant: the page shows A's board in it, at the case model's position. The fascia comparison copies
#   the composites from the variant folders and F's renders from 3d/case-pair/variant-D/ (F reads
#   "in progress" when there are none).
#
# TIME  about 5-6 minutes (KiCad: DRC with zone refill, GLB export and 3 renders per board, 5 boards).
#
# OUTPUT  site/index.html + app.js, site/3d/*.gltf.json (glTF JSON, buffer embedded as base64:
#   the host serves no .glb/.bin), site/img/*.png, site/data/*.json, site/sch/**. Files are checked
#   against the host's rules (types .png .jpg .webp .svg .json .js .css .txt, <= 15 MB each).
set -euo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
if [ $# -ge 1 ]; then REPO=$(cd "$1" && pwd)
elif [ -d "$PWD/PCB/TS06-DRV" ]; then REPO=$PWD
else REPO=/home/user/TERMINAL-06-firmware; fi
MODELS=${MODELS:-$(cd "$HERE/.." && pwd)/3dmodels}
SCH=${SCH:-$(cd "$HERE/.." && pwd)/sch/out}
IMAGE=${KICAD_IMAGE:-mirror.gcr.io/kicad/kicad:10.0}
BOARDS=""
for B in TS06-DRV TS06-DISP TS06-FASCIA TS06-FASCIA-wide TS06-FASCIA-rhythm; do   # the fascia variants A, W, R
  if [ -f "$REPO/PCB/$B/$B.kicad_pcb" ]; then BOARDS="$BOARDS $B"; fi
done
BOARDS=${BOARDS# }
SITE=$HERE/site
WORK=$HERE/work/build
T=$HERE/tools
t0=$(date +%s)
say() { printf '[%3ds] %s\n' $(( $(date +%s) - t0 )) "$*"; }
mkdir -p "$SITE/3d" "$SITE/img" "$SITE/data" "$WORK"
say "repo $REPO ($(git -C "$REPO" rev-parse --abbrev-ref HEAD 2>/dev/null) $(git -C "$REPO" rev-parse --short HEAD 2>/dev/null)); labelled ${VIEWER_BRANCH:-pcb/kicad-boards}"

if [ "${PAGE_ONLY:-0}" != 1 ]; then
  # ---------------------------------------------------------------- 0. tools
  command -v docker >/dev/null || { echo "docker is required"; exit 1; }
  docker info >/dev/null 2>&1 || { echo "docker daemon not running: nohup dockerd >/dev/null 2>&1 &"; exit 1; }
  if [ ! -x "$T/node_modules/.bin/gltfpack" ]; then
    say "installing gltfpack 1.3.0 into tools/"
    [ -f "$T/package.json" ] || echo '{"name":"ts06-viewer2-tools","private":true}' > "$T/package.json"
    npm install --prefix "$T" --no-audit --no-fund gltfpack@1.3.0 >/dev/null
  fi
  GLTFPACK=$T/node_modules/.bin/gltfpack
  [ -d "$MODELS" ] || { echo "no 3D model library at $MODELS (set MODELS=...)"; exit 1; }

  # ---------------------------------------------------------------- 1. scratch copies of the boards
  rm -rf "$WORK/brd" "$WORK/out"
  mkdir -p "$WORK/brd" "$WORK/out"
  cp -r "$REPO/PCB/lib" "$WORK/brd/lib"
  for B in $BOARDS; do
    printf '  %-12s ' "$B"; python3 "$T/prep_board.py" "$REPO/PCB/$B/$B.kicad_pcb" "$WORK/brd/$B"
  done
  cp "$T/kicad_export.sh" "$WORK/"
  chmod -R a+rwX "$WORK"

  # ---------------------------------------------------------------- 2. KiCad: refill + DRC, GLB, renders
  say "KiCad 10 in docker: refill zones + DRC, GLB export$([ "${RENDER:-1}" = 0 ] || echo ', renders')"
  docker run --rm -v "$WORK":/w -v "$MODELS":/m:ro -e HOME=/tmp -e RENDER="${RENDER:-1}" "$IMAGE" \
    bash /w/kicad_export.sh $BOARDS | sed 's/^/  /'
  for B in $BOARDS; do [ -s "$WORK/out/$B.glb" ] || { echo "no GLB for $B"; cat "$WORK/out/$B-glb.log"; exit 1; }; done
  grep -h "Could not add 3D model" "$WORK"/out/*-glb.log | sed 's/^/  note: /' || true

  # ---------------------------------------------------------------- 3. quantise + embed
  say "gltfpack (KHR_mesh_quantization only, 16-bit positions, named nodes kept) and base64 embedding"
  for B in $BOARDS; do
    "$GLTFPACK" -i "$WORK/out/$B.glb" -o "$WORK/out/$B.q.glb" -kn -vp 16 -si 0.5 -se 0.0005 >/dev/null
    printf '  '; python3 "$T/glb2json.py" "$WORK/out/$B.q.glb" "$SITE/3d/$B.gltf.json"
  done

  # ---------------------------------------------------------------- 4. the case parts
  say "case parts from 3d/case-pair/out/*.stl"
  CP=$REPO/3d/case-pair/out
  PARTS_STL=""
  for p in cheek_l cheek_r brow top trench base rear fascia_frame; do    # top and fascia_frame: newer case models
    if [ -f "$CP/$p.stl" ]; then PARTS_STL="$PARTS_STL $p=$CP/$p.stl"; fi
  done
  python3 "$T/stl2gltf.py" "$SITE/3d/case.gltf.json" $PARTS_STL

  # ---------------------------------------------------------------- 5. parts, assembly frame, facts
  say "parts, assembly frame (case_pair.py), facts"
  for B in $BOARDS; do python3 "$T/kparts.py" "$REPO/PCB/$B/$B.kicad_pcb" --models "$MODELS" > "$WORK/out/$B.parts.json"; done
  python3 - "$WORK/out" "$SITE/data/parts.json" $BOARDS <<'EOF'
import json, sys
out = {b: json.load(open("%s/%s.parts.json" % (sys.argv[1], b), encoding="utf8")) for b in sys.argv[3:]}
json.dump(out, open(sys.argv[2], "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
EOF
  python3 "$T/assembly.py" "$REPO" "$SITE/data/model.json" | sed 's/^/  /'
  python3 "$T/facts.py" "$WORK/out" "$REPO" $BOARDS > "$SITE/data/facts.json"

  # ---------------------------------------------------------------- 6. images
  if [ "${RENDER:-1}" != 0 ]; then
    python3 "$T/trim.py" "$WORK"/out/img/*.png
    cp "$WORK"/out/img/*.png "$SITE/img/"
  fi
  for v in iso iso_rear front exploded module; do cp "$CP/$v.png" "$SITE/img/case-$v.png"; done
  # the fascia comparison: composites from the variant folders; F (a printed frame) only if the case
  # model has it and has rendered it
  python3 - "$REPO" "$SITE" <<'EOF2'
import glob, json, os, shutil, sys
repo, site = sys.argv[1], sys.argv[2]
os.makedirs(os.path.join(site, "img", "fv"), exist_ok=True)
pics = []
for rel, label in (("PCB/TS06-FASCIA-rhythm/composite-0-centred.png", "A · centred (176), controls where they were"),
                   ("PCB/TS06-FASCIA-wide/front_composite.png", "W · full width, controls translated"),
                   ("PCB/TS06-FASCIA-rhythm/composite-B.png", "R · on the tube grid, alignment B (built)"),
                   ("PCB/TS06-FASCIA-rhythm/composite-A.png", "R · alignment A (not built)"),
                   ("PCB/TS06-FASCIA-rhythm/composite-C.png", "R · alignment C (not built)"),
                   ("PCB/TS06-FASCIA-wide/case_front_compare.png", "Case front: A against W")):
    src = os.path.join(repo, rel)
    if os.path.isfile(src) and os.path.getsize(src) < 15 * 1048576:
        dst = "img/fv/" + rel.split("/")[1].replace("TS06-FASCIA-", "") + "-" + os.path.basename(rel)
        shutil.copy(src, os.path.join(site, dst))
        pics.append({"src": dst, "label": label, "from": rel})
case = os.path.join(repo, "3d", "case-pair")
frame = "FASCIA_FRAME" in open(os.path.join(case, "case_pair.py"), encoding="utf8").read()
fpics = []
order = ["front_frame", "iso_frame", "exploded_frame", "front_noframe", "slot_right_frame", "slot_right_noframe"]
found = glob.glob(os.path.join(case, "variant-D", "*.png")) + glob.glob(os.path.join(case, "out", "*frame*.png"))
found.sort(key=lambda f: (order.index(os.path.basename(f)[:-4]) if os.path.basename(f)[:-4] in order else 99, f))
for f in found:
    dst = "img/fv/F-" + os.path.basename(f)
    shutil.copy(f, os.path.join(site, dst))
    fpics.append({"src": dst, "label": "F · " + os.path.basename(f), "from": os.path.relpath(f, repo)})
json.dump({"pictures": pics + fpics, "frame": "rendered" if fpics else ("modelled, no renders yet" if frame else "in progress")},
          open(os.path.join(site, "data", "variants.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("  fascia variants: %d pictures, F %s" % (len(pics) + len(fpics), "rendered" if fpics else "in progress"))
EOF2
fi

# ------------------------------------------------------------------ 7. sections
say "sections from $SCH"
python3 "$T/sections.py" "$SCH" "$SITE" "$REPO" "$SITE/data/parts.json" | sed 's/^/  /'

# ------------------------------------------------------------------ 8. the page
say "page"
COMMIT=$(git -C "$REPO" rev-parse --short HEAD 2>/dev/null || echo unknown)
BRANCH=${VIEWER_BRANCH:-pcb/kicad-boards}     # the label the owner sees; a worktree's own branch name is not it
DATE=$(git -C "$REPO" log -1 --format=%cd --date=format:%d.%m.%y 2>/dev/null || date +%d.%m.%y)
sed -e "s/@@COMMIT@@/$COMMIT/g" -e "s#@@BRANCH@@#$BRANCH#g" -e "s/@@DATE@@/$DATE/g" \
    -e "s/@@BUILT@@/$(date -u +%Y-%m-%dT%H:%MZ)/g" "$HERE/src/index.html" > "$SITE/index.html"
cp "$HERE/src/app.js" "$SITE/app.js"
rm -f "$SITE/ts06-viewer.html"

# ------------------------------------------------------------------ 9. host rules
python3 - "$SITE" <<'EOF'
import os, sys
site = sys.argv[1]
ok = {".png", ".jpg", ".webp", ".svg", ".json", ".js", ".css", ".txt", ".html"}
tot, bad = 0, []
rows = []
for d, _, fs in os.walk(site):
    for f in fs:
        p = os.path.join(d, f)
        n = os.path.getsize(p)
        tot += n
        ext = os.path.splitext(f)[1].lower()
        if ext not in ok or (ext == ".html" and f != "index.html") or n > 15 * 1024 * 1024:
            bad.append(os.path.relpath(p, site))
        rows.append((n, os.path.relpath(p, site)))
for n, r in sorted(rows, reverse=True)[:8]:
    print("  %8.2f MB  %s" % (n / 1048576, r))
print("  total %.1f MB in %d files%s" % (tot / 1048576, len(rows), "" if tot < 60 * 1048576 else "  (OVER 60 MB)"))
if bad:
    print("  NOT ALLOWED:", bad); sys.exit(1)
EOF
say "done: $SITE/index.html"
