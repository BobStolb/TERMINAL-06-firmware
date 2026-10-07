#!/bin/sh
# The commands that wrote the jig's STL files and pictures (OpenSCAD 2021.01; the PNGs need xvfb-run).
# They were run one by one, not as this script. Run from this folder:  sh make.sh
set -e
O="openscad"
P="xvfb-run -a openscad --colorscheme=Cornfield"

# STL files (print orientation: front face down)
$O -D 'part="plate"' -D 'bumps=0' -o jig_plate_flat.stl jig.scad
$O -D 'part="plate"' -D 'bumps=1' -o jig_plate_L1.stl jig.scad
$O -D 'part="plate"' -D 'bumps=2' -o jig_plate_L2.stl jig.scad
$O -D 'part="shims"' -o jig_shims.stl jig.scad
$O -D 'part="former"' -o jig_former.stl jig.scad
# OpenSCAD 2021.01 writes ASCII STL; the repository's files were converted to binary STL (50 bytes a triangle) to keep them small.

# pictures
$P --projection=p --imgsize=1400,700 --camera=0,-2,0,45,0,0,130 -D 'part="compare"' -o jig-plates-back.png jig.scad
$P --projection=o --imgsize=1600,800 --camera=0,0,8,90,0,0,125 -D 'part="section"' -o jig-section.png jig.scad
$P --projection=o --imgsize=900,900 --camera=0,0,0,0,180,0,100 --viewall --autocenter -D 'part="plate"' -D 'bumps=1' -o jig-plate-front.png jig.scad
$P --projection=o --imgsize=1000,1100 --camera=0,0,0,0,0,0,200 --viewall --autocenter -D 'part="set"' -D 'bumps=1' -o jig-print-set.png jig.scad
