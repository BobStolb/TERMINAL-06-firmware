// 3 mm through-hole LED standing on the board face (TS06_LED_D3.0mm: HL1..HL9). Made for 3d/populated.
//
// layers: lens=#f2a31c flange=#d98a10 leads=#c9c9c9
//
// FRAME  KiCad model frame. Pad 1 (cathode, square) at (-1.27, 0), pad 2 (anode) at (1.27, 0).
//
// DIMENSIONS                         value        kind
//   body D          3.0 mm                         MEASURED (repo source): footprint name and descr (KiCad LED_D3.0mm)
//   overall height  5.3 mm above the board face    MEASURED (repo source): footprint descr "a 5.3 mm-tall body"; also
//                                                  case_pair.py LED_H (marked assumed there)
//   flange          D3.8 x 0.6 mm, flat on the cathode side   INFERRED (case_pair.py LED_FLANGE_D 3.8, assumed)
//   leads           D0.5, 1.5 mm proud of the back face       INFERRED (case_pair.py PIN_TAIL 1.5, assumed)
// Amber, opaque: a clear 3 mm lens is drawn as a solid.
L = "lens";
H = 5.3;
FL_D = 3.8;
FL_T = 0.6;
BODY_D = 3.0;
R = BODY_D / 2;

if (L == "lens") {
    translate([0, 0, FL_T]) cylinder(d = BODY_D, h = H - R - FL_T, $fn = 40);
    translate([0, 0, H - R]) sphere(r = R, $fn = 40);
}
if (L == "flange") {
    intersection() {
        cylinder(d = FL_D, h = FL_T, $fn = 40);
        translate([-1.45, -3, -1]) cube([6, 6, 3]);          // the flat, on the cathode side (-x)
    }
}
if (L == "leads") {
    for (x = [-1.27, 1.27]) translate([x, 0, -1.6 - 1.5]) cylinder(d = 0.5, h = 1.6 + 1.5 + 0.3, $fn = 10);
}
