// The SMD parts on the back of the fascia (TS06-FASCIA-rhythm): the eight 1206 resistors and the JST PH side-entry
// connector. Made for 3d/populated.
//
// layers: body=#1b1b1d term=#c9c9c9 housing=#e6e1d3 tab=#b8bcc0
// variants: r1206_back MODE=0 ; jst_s6b_sm4_back MODE=1
//
// FRAME  KiCad model frame of the footprint as authored: z up from the face the part is soldered to (KiCad flips
//        the model for a back-side footprint, so it stands out of the fascia's rear face).
//
// r1206_back (R1-R8, TS06_R_1206_HandSolder, pads at x +-1.85)
//   body 3.2 x 1.6 x 0.55 mm, end caps 0.5 mm      INFERRED: standard 1206 (3216 metric) chip resistor outline
// jst_s6b_sm4_back (J1, TS06_JST_PH_S6B-PH-SM4-TB_Back; cable exits toward +y)
//   housing x -6.95..6.95, y -3.2..4.4 (13.9 x 7.6)   MEASURED (repo source): the footprint's B.Fab rectangle (15.9 x 7.6, which
//                                                     includes the retention tabs at x +-7.35) less the tabs
//   height 4.8 mm                                    INFERRED: case_pair.py FJ_HDR_H 4.8 (assumed there)
//   mouth (the cable side, +y) drawn as a 6.0 x 2.0 recess is NOT modelled; pins and tabs: tabs 1.5 x 3.4 at (+-7.35, 2.9)
//                                                    MEASURED (footprint pads MP)
MODE = 0;
L = "body";

if (MODE == 0) {
    if (L == "body") translate([-1.1, -0.8, 0]) cube([2.2, 1.6, 0.55]);
    if (L == "term") for (s = [-1, 1]) translate([s * 1.35 - 0.25, -0.8, 0]) cube([0.5, 1.6, 0.6]);
}
if (MODE == 1) {
    // model y is the footprint's y negated: housing B.Fab y -3.2..4.4 -> -4.4..3.2, tabs at fp y +2.9 -> -2.9, signal pads at fp y -2.85 -> +2.85
    if (L == "housing") translate([-6.95, -4.4, 0.05]) cube([13.9, 7.6, 4.8]);
    if (L == "tab") for (s = [-1, 1]) translate([s * 7.35 - 0.75, -2.9 - 1.7, 0]) cube([1.5, 3.4, 0.25]);
    if (L == "term") for (k = [0 : 5]) translate([k * 2.0 - 5.0 - 0.25, 2.85 - 1.75, 0]) cube([0.5, 3.5, 0.2]);
}
