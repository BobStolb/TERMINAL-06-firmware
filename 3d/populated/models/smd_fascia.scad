// The SMD parts on the back of the fascia: the eight 1206 resistors (TS06-FASCIA-rhythm) and the JST PH connector: the
// side-entry S6B-PH-SM4-TB that rev A of the fascia R carried, and the upright (top-entry) B6B-PH-SM4-TB of rev B. Made
// for 3d/populated (KiCad's 3D library has a footprint for neither JST part, and no model: checked in its GitLab tree).
//
// layers: body=#1b1b1d term=#c9c9c9 housing=#e6e1d3 tab=#b8bcc0
// variants: r1206_back MODE=0 ; jst_s6b_sm4_back MODE=1 ; jst_b6b_sm4_back MODE=2
//
// FRAME  KiCad model frame of the footprint as authored: z up from the face the part is soldered to (KiCad flips
//        the model for a back-side footprint, so it stands out of the fascia's rear face). Rev B's model (MODE 2) is drawn with model y = footprint y
//        (read off its render); the older MODE 1 below was drawn with y negated and shows its pins and tabs on the wrong side (no board uses it now).
//
// r1206_back (R1-R8, TS06_R_1206_HandSolder, pads at x +-1.85)
//   body 3.2 x 1.6 x 0.55 mm, end caps 0.5 mm      INFERRED: standard 1206 (3216 metric) chip resistor outline
// jst_s6b_sm4_back (J1, TS06_JST_PH_S6B-PH-SM4-TB_Back; cable exits toward +y)
//   housing x -6.95..6.95, y -3.2..4.4 (13.9 x 7.6)   MEASURED (repo source): the footprint's B.Fab rectangle (15.9 x 7.6, which
//                                                     includes the retention tabs at x +-7.35) less the tabs
//   height 4.8 mm                                    INFERRED: case_pair.py FJ_HDR_H 4.8 (assumed there)
//   mouth (the cable side, +y) drawn as a 6.0 x 2.0 recess is NOT modelled; pins and tabs: tabs 1.5 x 3.4 at (+-7.35, 2.9)
//                                                    MEASURED (footprint pads MP)
// jst_b6b_sm4_back (J1 of rev B, TS06_JST_PH_B6B-PH-SM4-TB_Back; the mouth faces away from the board, the solder tails run to +y)
//   housing x -6.95..6.95 (13.9), footprint y -4.25..0.75 (5.0)   MEASURED (repo source): width = the 13.9 of KiCad's STEP of the through-hole
//                                                    B6B-PH-K (3d/populated/kicad3d, read for this: x 13.9, y 4.55, z 6.0), the same PH plastic body; depth =
//                                                    the SM4-TB footprint's F.Fab outline (x +-7.975 there includes the metal tabs outside the plastic)
//   height 6.0 mm                                    INFERRED: JST's catalogue figure for the PH top-entry headers as remembered, and the 6.0 of that STEP; the
//                                                    SM4-TB datasheet itself was not readable here (jst-mfg.com is blocked by the egress policy)
//   mouth (the shroud's opening) is NOT modelled; tabs 1.6 x 3.0 at (+-7.4, fp y -1.75) and pads 1.0 x 5.5 at fp y 0.5   MEASURED (footprint pads)
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
if (MODE == 2) {
    // For a footprint on the BACK KiCad draws the model with its y equal to the footprint's y (the front-side rule, model y = -footprint y, is
    // turned by the flip about the footprint's x axis that a back-side footprint gets: seen in this part's render, whose first version, drawn
    // with y negated, had the body on the tail side). Housing fp y -4.25..0.75, tabs at fp y -1.75, signal pads at fp y 0.5; they run
    // 2.5 mm out of the body at fp y > 0.75: the solder tails
    if (L == "housing") translate([-6.95, -4.25, 0.05]) cube([13.9, 5.0, 5.95]);
    if (L == "tab") for (s = [-1, 1]) translate([s * 7.4 - 0.8, -1.75 - 1.5, 0]) cube([1.6, 3.0, 0.25]);
    if (L == "term") for (k = [0 : 5]) translate([k * 2.0 - 5.0 - 0.5, 0.5 - 2.75, 0]) cube([1.0, 5.5, 0.2]);
}
