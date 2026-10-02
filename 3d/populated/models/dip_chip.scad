// DIP chip, standing in a 7.62 mm (300 mil) socket of the TS06 boards. Made for 3d/populated.
//
// layers: body=#1c1c1e leads=#bcc0c4 mark=#8e8e93
// variants: dip_chip_4 N=4 ; dip_chip_8 N=8 ; dip_chip_16 N=16 ; dip_chip_28 N=28
//
// FRAME  KiCad model frame (mm, x right, y up = a footprint's y negated, z up from the board face).
//        Pin 1 at (0, 0), the left column goes down the page (y -2.54 each), the right column is at x 7.62:
//        the pad layout of every TS06_DIP-N_W7.62mm_Socket footprint. The pre-rotated _R90/_R180/_R270
//        footprints reach this through tools/models3d.py's variant rule.
//
// DIMENSIONS              value                       kind
//   SEAT  4.0             socket top above the board  MEASURED: the KiCad DIP-N_W7.62mm_Socket models, read back from a
//                         face                        GLB export of TS06-DRV (socket top 5.6 mm, board face 1.6 mm)
//   H     4.5             chip body, seating plane    INFERRED: JEDEC MS-001 plastic DIP is 4.57 mm max; chosen so that
//                         to top                      socket + chip is 8.5 mm, the figure 3d/case-pair/case_pair.py FP_H uses
//   W     6.35 (7.11 N=28) body width               INFERRED: JEDEC MS-001 (PDIP, 300 mil) 6.35 mm; the skinny
//                                                     28-pin SPDIP (MCP23017-E/SP) is 7.11 mm
//   LEN   4.6 / 9.3 / 19.2 / 34.7                     INFERRED: typical body length for 4 / 8 / 16 / 28 pins (DIP-4
//                                                     optocoupler, PDIP-8, PDIP-16, SPDIP-28)
//   leads 0.5 x 0.3 mm, 3.5 mm into the socket        INFERRED: typical DIP lead
// Not drawn: the pin-1 notch (a dot marks pin 1), the leads' kink, the package's mould draft.
N = 16;
L = "body";
SEAT = 4.0;
H = 4.5;
W = (N == 28) ? 7.11 : 6.35;
LEN = (N == 4) ? 4.6 : (N == 8) ? 9.3 : (N == 16) ? 19.2 : 34.7;
P = 2.54;
cy = -(N / 2 - 1) * P / 2;            // body centre, y
cx = 3.81;

module body() {
    translate([cx, cy, SEAT])
    hull() {
        translate([-W / 2, -LEN / 2, 0]) cube([W, LEN, H * 0.55]);
        translate([-W / 2 + 0.35, -LEN / 2 + 0.35, 0]) cube([W - 0.7, LEN - 0.7, H]);
    }
}

module lead(px, py, side) {            // side -1 left column, +1 right column
    bx = cx + side * (W / 2 - 0.05);
    hull() {
        translate([bx - 0.15, py - 0.25, SEAT + 1.0]) cube([0.3, 0.5, 0.3]);
        translate([px - 0.15, py - 0.25, SEAT - 3.5]) cube([0.3, 0.5, 0.1]);
    }
}

if (L == "body") body();
if (L == "leads") for (i = [0 : N / 2 - 1]) {
    lead(0, -i * P, -1);
    lead(7.62, -i * P, 1);
}
// pin-1 dot: top face, left column side, at the pin-1 end (the +y end of the body)
if (L == "mark") translate([cx - W / 2 + 1.1, cy + LEN / 2 - 1.1, SEAT + H - 0.02])
    cylinder(d = 0.9, h = 0.06, $fn = 16);
