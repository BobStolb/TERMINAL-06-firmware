#!/bin/sh
# Rebuild the jig's STL files and pictures from jig.scad (OpenSCAD 2021.01; the PNGs need xvfb-run).
# Run from this folder:  sh make.sh
set -e
S=jig.scad
O="openscad"
P="xvfb-run -a openscad --projection=o --colorscheme=Tomorrow"

# STL files (print orientation: front face down)
$O -D 'part="plate"' -D 'bumps=0' -o jig_plate_flat.stl $S
$O -D 'part="plate"' -D 'bumps=1' -o jig_plate_L1.stl $S
$O -D 'part="plate"' -D 'bumps=2' -o jig_plate_L2.stl $S
$O -D 'part="shims"' -o jig_shims.stl $S
$O -D 'part="former"' -o jig_former.stl $S

# pictures
$P --imgsize=1400,700 --camera=0,0,0,0,0,0,150 -D 'part="compare"' -o jig-plates-back.png $S
$P --imgsize=1200,700 --camera=0,0,3,90,0,0,140 -D 'part="assembly"' -D 'bumps=0' -o jig-assembly-R.png $S
$P --imgsize=1200,700 --camera=0,0,3,90,0,0,140 -D 'part="assembly"' -D 'bumps=1' -o jig-assembly-T.png $S
$P --imgsize=1000,1000 --camera=-8,-12,0,0,0,0,170 -D 'part="set"' -D 'bumps=1' -o jig-print-set.png $S
