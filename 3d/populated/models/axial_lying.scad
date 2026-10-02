// An axial part lying on the board, bent leads into two holes: the МЛТ-0,5 resistors (R27..R32, R56..R63)
// and the Bourns 5900 choke L1. Made for 3d/populated.
//
// layers: body=#7d8140 band=#8a2b1d leads=#c9c9c9
// variants: mlt05_lying BODY_D=4.2 BODY_L=10.8 PITCH=15.24 AXIS=2.6 STYLE=0 ; l1_axial BODY_D=11.5 BODY_L=22.9 PITCH=27.94 AXIS=6.0 STYLE=1 COLOR_body=#2b2d33 COLOR_band=#2b2d33
//
// FRAME  KiCad model frame. Pad 1 at (0, 0), pad 2 at (PITCH, 0): TS06_R_Axial_MLT-0.5_P15.24mm and
//        TS06_L_Axial_D11.5mm_L22.9mm_P27.94mm. The _R180/_R270 copies take the variant rule.
//
// DIMENSIONS                      value             kind
//   МЛТ-0,5   BODY_D 4.2, BODY_L 10.8, leads D0.8, pitch 15.24     MEASURED (repo source): the footprint's own descr and
//                                                  PCB/TS06-DRV/bom.md ("body <= D4.2 x 10.8 mm, leads D0.8")
//   L1        BODY_D 11.5, BODY_L 22.9, leads D0.8, pitch 27.94    MEASURED (repo source): footprint descr and bom.md
//                                                  (Bourns 5900-221-RC data)
//   AXIS      2.6 / 6.0 above the board face      INFERRED: the footprint states "height=4.7mm" / "height=12mm" for a
//                                                  lying part; the axis is put at height - D/2 so the body top is there
//   leads     bent 90 deg at the body, 2.5 mm through the board                INFERRED
//   STYLE 0 draws the resistor (olive body, three bands); STYLE 1 the choke (dark body, plain).
BODY_D = 4.2;
BODY_L = 10.8;
PITCH = 15.24;
AXIS = 2.6;
STYLE = 0;
L = "body";
LEAD_D = 0.8;
cx = PITCH / 2;
x0 = cx - BODY_L / 2;
x1 = cx + BODY_L / 2;
// a part of the 4.2 mm resistor rides 0.5 mm up (axis 2.6 - radius 2.1); the choke 0.25 mm (6.0 - 5.75)

module along_x(x, len, d) { translate([x, 0, AXIS]) rotate([0, 90, 0]) cylinder(d = d, h = len, $fn = 32); }
module vert(x, z0, z1) { translate([x, 0, z0]) cylinder(d = LEAD_D, h = z1 - z0, $fn = 12); }

if (L == "body") {
    along_x(x0, BODY_L, BODY_D);
}
if (L == "band" && STYLE == 0) {
    for (k = [0 : 2]) along_x(x0 + 1.6 + k * 1.3, 0.7, BODY_D + 0.04);
    along_x(x1 - 1.4, 0.7, BODY_D + 0.04);
}
if (L == "leads") {
    vert(0, -2.5, AXIS);
    vert(PITCH, -2.5, AXIS);
    translate([0, 0, AXIS]) sphere(d = LEAD_D, $fn = 12);
    translate([PITCH, 0, AXIS]) sphere(d = LEAD_D, $fn = 12);
    along_x(0, x0 + 0.1, LEAD_D);
    along_x(x1 - 0.1, PITCH - x1 + 0.1, LEAD_D);
}
