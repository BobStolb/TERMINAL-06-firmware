// What the nixie tubes of TS06-DISP stand on. Made for 3d/populated.
//
// layers: sleeve=#d1ad45 wire=#c9cdd1 pip=#e3e7ea
// variants: in12_contacts MODE=0 ; in17_wires MODE=1 ; in17_pip MODE=2
//
// FRAME  KiCad model frame (a footprint's y negated), origin = the footprint origin, z up from the board face.
//
// in12_contacts (V1-V4, V9, V10)   twelve tube-socket contacts on the TS06_IN12_Socket pad ring, one per pad.
//   pad positions    MEASURED (repo source): PCB/lib/TS06.pretty/TS06_IN12_Socket.kicad_mod, pads 1-12
//   sleeve height    4.5 mm      INFERRED: case_pair.py IN12_SEAT 4.5 (assumed there: "TS06-LIB-SOCKET is not captured"). The
//                                tube model (3d/IN12.step) is placed with its glass 4.5 mm above the board face to match.
//   sleeve D1.7, bore not drawn, tail D1.0 to 1.0 mm past the back face   INFERRED; PCB/TS06-DISP/bom.md only says
//                                "tube socket contact, 12 per tube, tail to suit the 1.2 mm hole"
//
// in17_wires (V5, V6)    the wire leads of the IN-17 between the end of the model's own stubs and the board.
//   pad positions    MEASURED (repo source): TS06_IN17_Socket.kicad_mod, the 11 pads (the 12th lead is absent)
//   why             3d/IN17.step carries only 5.5 mm of lead, and tools/models3d.json scales the whole model along the tube's
//                   axis by 19.72 / 24.3 (the owner's bench caliper, 2026-10-02: the glass is 19.72 from the dome to the end of
//                   the glass), so its stubs are 4.46 mm long. With the glass end STANDOFF = 10.28 mm off the board (case_pair.py
//                   IN17_STANDOFF = Z_DISP_F - IN17_D, so the faces are coplanar with the IN-12s) the stubs end 5.82 mm above
//                   the board, so wires D0.4 are drawn from there down to 0.8 mm past the back face.  INFERRED
//                   (wire D0.4; the stubs in IN17.step measure 0.3 across).  See README.md, open item "IN-17 leads".
//
// in17_pip (V5, V6)      the exhaust pip of the IN-17, standing out of the glass end between the leads.
//   length          2.28 mm     A READING (case_pair.py IN17_PIP): the outline drawing's 22 mm minus the measured 19.72 of glass.
//                               The pip itself has not been measured; the drawing is read to include it.
//   diameter 3.5, round tip     INFERRED (the lead pattern is 5.6 mm across, so a pip under 5 mm stands between the rows).
//   place           centred on the lead pattern; the tip 2.28 mm below the glass end, 8.0 mm above the board face.
STANDOFF = 10.28;     // the glass end above the board face: case_pair.py IN17_STANDOFF
PIP = 2.28;           // case_pair.py IN17_PIP
STUB_END = STANDOFF - 5.5 * 19.72 / 24.3;      // where the model's scaled stubs end above the board: 5.82
MODE = 0;
L = "sleeve";

IN12 = [[-3.981, -8.002], [0.000, -8.990], [3.987, -8.002], [5.741, -4.494], [5.741, 0.000], [5.741, 4.495],
        [3.987, 8.000], [0.000, 8.991], [-3.981, 8.000], [-5.742, 4.495], [-5.742, 0.000], [-5.742, -4.494]];
IN17 = [[2.7774, -1.5], [2.7774, -4.0], [1.3649, -6.0], [-1.3651, -6.0], [-2.7776, -4.0], [-2.8576, -1.5],
        [-2.8176, 1.1425], [-2.7776, 3.6825], [-1.3651, 5.6825], [1.3649, 5.6825], [2.7774, 3.6825]];

if (MODE == 0 && L == "sleeve") for (p = IN12) {
    translate([p[0], -p[1], -2.6]) cylinder(d = 1.0, h = 2.6 + 0.2, $fn = 14);
    translate([p[0], -p[1], 0]) cylinder(d = 1.7, h = 4.5, $fn = 18);
}
if (MODE == 1 && L == "wire") for (p = IN17) translate([p[0], -p[1], -2.4])
    cylinder(d = 0.4, h = 2.4 + STUB_END + 0.1, $fn = 10);
if (MODE == 2 && L == "pip") translate([-0.04, 0.16, 0]) hull() {
    translate([0, 0, STANDOFF - PIP + 1.75]) sphere(d = 3.5, $fn = 24);
    translate([0, 0, STANDOFF + 0.09]) cylinder(d = 3.5, h = 0.01, $fn = 24);
}
