#!/bin/sh
# Rebuild the knobs' STL files and pictures (OpenSCAD 2021.01, Python 3 with Pillow, xvfb-run for the PNGs).
# Run from this folder:  sh make.sh        The intermediate files go to build/ (not committed).
set -e
O="openscad"
P="xvfb-run -a openscad --colorscheme=Cornfield"
mkdir -p build

# 1. print files, top face down (flip=1), shaft sawn to 12.0 (default) and left as it comes (shaft_top=18)
for k in A B C; do
  $O -D "part=\"$k\"" -D ang=0 -D flip=1 -o knob_$k.stl knob.scad
  $O -D "part=\"$k\"" -D ang=0 -D flip=1 -D shaft_top=18 -o knob_${k}_uncut.stl knob.scad
done
# (the files above are ASCII STL; they were converted to binary STL for the repository: 50 bytes a triangle)

# 2. the cut body and its fill, upright (flip=0), for the pictures
for k in A B C; do
  $O -D "part=\"$k\"" -D ang=0 -o build/knob_$k.stl knob.scad
  $O -D "part=\"${k}_fill\"" -D ang=0 -o build/knob_${k}_fill.stl knob.scad
  cp build/knob_$k.stl build/section_$k.stl
done

# 3. pictures: oblique, top views for face.py, the section on the stack
for k in A B C; do
  $P --projection=p --imgsize=900,700 --camera=0,0,9,58,0,-30,100 -D "part=\"pic$k\"" -o knob_$k-oblique.png knob.scad
  $P --projection=o --imgsize=1000,1000 --camera=0,0,0,0,0,0,100 -D "part=\"pic$k\"" -o build/top_$k.png knob.scad
done
$P --projection=o --imgsize=1000,1000 --camera=0,0,0,0,0,0,100 -D 'part="picA"' -D 'fillc="cream"' -o build/top_A_cream.png knob.scad
$P --projection=o --imgsize=2000,1000 --camera=14,0,6,90,0,0,150 -D 'part="section"' -o knobs-section.png knob.scad

# 4. the knobs on fascia R's face, and the turner's drawing
python3 -I face.py
python3 -I drawing.py
