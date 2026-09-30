// power_options.scad - pictures of the two favourite power entries for the TERMINAL-06 case.
//
// It includes the case exactly as committed (../case.scad, ../params.scad) and changes nothing
// there: the few overrides below live only in this file. power_options.py --render runs it.
//
//   xvfb-run openscad -o x.png -D 'OPTION="rear2rm"' power_options.scad
//     rear2rm       2РМ14 on the rear panel over XS1's place, plain right cheek (favourite 1)
//     rear2rm_cut   the same with the rear panel and top plate see-through: the lead to XS1's pads
//     cheekjack     a long-bush panel DC jack through the right cheek, axis moved back to Z 57 (favourite 2)
//
// Connector sizes: flange 24, hole spacing 17, seat Ø14 seen (search excerpts of the 2РМ table);
// lengths, the cable part's shape and the panel jack's body are INFERRED (see README.md).

include <../case.scad>

PART = "none";               // the case's own switch: draw nothing by itself
OPTION = "rear2rm";
JACK_HOLE_D = 0;             // the right cheek loses its jack hole: the port moves
JACK_CB_D = 0;

// ---- favourite 1: 2РМ14 at the rear, over XS1's place (power_options.py: place 1)
RM_X = 182.5;  RM_Y = JACK_Y;
RM_FLANGE = 24;  RM_HOLES = 17;  RM_HOLE_D = 3.2;   // seen, seen, inferred
RM_CUT = 16;  RM_FRONT = 12;  RM_REAR = 13;         // inferred (L max 25 seen)
// ---- favourite 2: long-bush DC jack through the right cheek, axis moved back (Z 57) clear of the board
CJ_Y = JACK_Y;  CJ_Z = 57.0;  CJ_HOLE = 12.7;  CJ_REAR = 17;   // hole seen (0.5 in), the rest inferred
PAD1 = [177.4, JACK_Y];  PAD2 = [183.4, JACK_Y];   // XS1 pads 1 (VIN_J) and 2 (GND), board file

module wire(pts, c, d = 1.6) color(c) for (i = [0 : len(pts) - 2])
    hull() { translate(pts[i]) sphere(d = d, $fn = 10); translate(pts[i + 1]) sphere(d = d, $fn = 10); }
// world [X, Y, Z] to OpenSCAD [x, y, z] = [X, Z, Y]
function W(p) = [p[0], p[2], p[1]];

module stack_noxs1() {                              // case.scad's stack(), XS1 left off
    color("#2e6b50") wbox(0, BOARD_W, DISP_BOT_Y, DISP_TOP_Y, Z_DISP_F, Z_DISP_B);
    color("#2e6b50") wbox(0, BOARD_W, DRV_BOT_Y, DRV_TOP_Y, Z_DRV_F, Z_DRV_B);
    for (x = IN12_X) in12(x, IN12_Y);
    for (x = IN15_X) in12(x, IN12_Y);
    for (x = IN17_X) in17(x, IN17_Y);
    for (p = DRV_PARTS) if (p[0] != "XS1") {
        if (p[6] == 1) color(p[0] == "J1" ? "#f2f2f2" : "#222") wbox(p[1], p[2], p[3], p[4], Z_DRV_F - p[5], Z_DRV_F);
        else if (p[0] == "C7" || p[0] == "L1" || p[0] == "C8")
            color(p[0] == "L1" ? "#4d4d4d" : "#2b4c7e") zcyl((p[1] + p[2]) / 2, (p[3] + p[4]) / 2, Z_DRV_B, Z_DRV_B + p[5], min(p[2] - p[1], p[4] - p[3]) - 1);
        else color(p[5] > 12 ? "#555" : "#9aa7b4") wbox(p[1], p[2], p[3], p[4], Z_DRV_B, Z_DRV_B + p[5]);
    }
    for (q = [PAD1, PAD2]) color("#d4af50") wbox(q[0] - 0.5, q[0] + 0.5, q[1] - 1.5, q[1] + 1.5, Z_DRV_B, Z_DRV_B + 0.1);
}

module rm14() {                                     // the block part, flange on the panel's outside face
    color("#b8bec6") {
        wbox(RM_X - RM_FLANGE / 2, RM_X + RM_FLANGE / 2, RM_Y - RM_FLANGE / 2, RM_Y + RM_FLANGE / 2, Z_REAR_OUT, Z_REAR_OUT + 1.5);
        zcyl(RM_X, RM_Y, Z_REAR_OUT + 1.5, Z_REAR_OUT + 1.5 + RM_FRONT, 14, 48);
        zcyl(RM_X, RM_Y, Z_REAR_IN - RM_REAR, Z_REAR_IN, RM_CUT, 48);
    }
    for (dx = [-1, 1], dy = [-1, 1])
        color("#333") zcyl(RM_X + dx * RM_HOLES / 2, RM_Y + dy * RM_HOLES / 2, Z_REAR_OUT + 1.5, Z_REAR_OUT + 3.2, 5.5, 20);
    // the mated cable part (straight nozzle): coupling ring, body, nozzle nut, the lead going down
    color("#9aa2ac") {
        zcyl(RM_X, RM_Y, Z_REAR_OUT + 1.5 + RM_FRONT - 4, Z_REAR_OUT + 1.5 + RM_FRONT + 10, 20, 48);
        zcyl(RM_X, RM_Y, Z_REAR_OUT + 1.5 + RM_FRONT + 10, Z_REAR_OUT + 1.5 + RM_FRONT + 26, 13, 6);
    }
    zt = Z_REAR_OUT + 1.5 + RM_FRONT + 26;
    wire([W([RM_X, RM_Y, zt]), W([RM_X, RM_Y, zt + 14]), W([RM_X, RM_Y - 12, zt + 26]), W([RM_X, Y_BOT - 4, zt + 30])], "#222", 5.5);
    // inside: the two-wire lead from the solder cups to XS1's pads
    zc = Z_REAR_IN - RM_REAR;
    wire([W([RM_X - 2, RM_Y, zc]), W([RM_X - 2, RM_Y, zc - 4]), W([PAD1[0], PAD1[1] + 3, Z_DRV_B + 4]), W([PAD1[0], PAD1[1], Z_DRV_B])], "#c62828");
    wire([W([RM_X + 2, RM_Y, zc]), W([RM_X + 2, RM_Y, zc - 4]), W([PAD2[0], PAD2[1] + 3, Z_DRV_B + 4]), W([PAD2[0], PAD2[1], Z_DRV_B])], "#111");
}

module rear_with_hole(alpha = 1) {
    difference() {
        color([0.08, 0.09, 0.11, alpha]) wbox(X_OUT_L, X_OUT_R, Y_BOT, Y_TOP, Z_REAR_IN, Z_REAR_OUT);
        zcyl(RM_X, RM_Y, Z_REAR_IN - 1, Z_REAR_OUT + 1, RM_CUT, 48);
        for (dx = [-1, 1], dy = [-1, 1]) zcyl(RM_X + dx * RM_HOLES / 2, RM_Y + dy * RM_HOLES / 2, Z_REAR_IN - 1, Z_REAR_OUT + 1, RM_HOLE_D, 16);
        for (x = [VENT_X0 : VENT_PITCH : VENT_X1 - VENT_W])
            hull() for (y = [VENT_Y0 + VENT_W / 2, VENT_Y1 - VENT_W / 2]) zcyl(x + VENT_W / 2, y, Z_REAR_IN - 1, Z_REAR_OUT + 1, VENT_W, 16);
    }
    if (alpha == 1) color("white") for (l = [["12 V DC  pins 1,2 +  3,4 -", 60], ["! 185 V INSIDE", 45], ["unplug, wait 15 s", 36]])
        translate([150, Z_REAR_OUT, l[1]]) rotate([90, 0, 180]) linear_extrude(0.15)
            text(l[0], size = 4.5, font = "DejaVu Sans:style=Bold");
}

module cheek_r_jack() difference() {                // favourite 2: the right cheek with the moved jack's hole
    cheek(false);
    xcyl(X_IN_R - 1, X_OUT_R + 1, CJ_Y, CJ_Z, CJ_HOLE);
}

module panel_jack() {
    color("#c8ccd2") {
        translate([X_OUT_R, CJ_Z, CJ_Y]) rotate([0, 90, 0]) cylinder(h = 2.5, d = 15, $fn = 6);   // hex nut (inferred)
        xcyl(X_OUT_R + 2.5, X_OUT_R + 3.5, CJ_Y, CJ_Z, 11.4);   // bush end
    }
    color("#222") xcyl(X_IN_R - CJ_REAR, X_IN_R, CJ_Y, CJ_Z, 12);
    // the adapter's plug, seated: overmould and lead
    color("#1b1d20") xcyl(X_OUT_R + 3.5, X_OUT_R + 22, CJ_Y, CJ_Z, 10);
    wire([W([X_OUT_R + 22, CJ_Y, CJ_Z]), W([X_OUT_R + 34, CJ_Y - 4, CJ_Z + 4]), W([X_OUT_R + 40, Y_BOT - 4, CJ_Z + 14])], "#1b1d20", 3.5);
    // inside: lugs to XS1's pads
    wire([W([X_IN_R - CJ_REAR, CJ_Y + 2, CJ_Z]), W([PAD1[0] - 1, PAD1[1] + 3, Z_DRV_B + 4]), W([PAD1[0], PAD1[1], Z_DRV_B])], "#c62828");
    wire([W([X_IN_R - CJ_REAR, CJ_Y - 2, CJ_Z]), W([X_IN_R - CJ_REAR + 3, CJ_Y - 4, CJ_Z - 6]), W([PAD2[0], PAD2[1], Z_DRV_B])], "#111");
}

module case_parts(see_through = false) {
    color("#3a3f45") cheek(true);
    color("#f28c28") brow();
    if (!see_through) color("#2b2f34") top_plate();
    color("#30363d") trench();
    color("#30363d") base();
    fascia_dressed();
    stack_noxs1();
}

if (OPTION == "rear2rm") {
    case_parts();
    color("#3a3f45") cheek(false);
    rear_with_hole();
    rm14();
} else if (OPTION == "rear2rm_cut") {
    case_parts(true);
    color([0.23, 0.25, 0.27, 0.35]) cheek(false);
    rear_with_hole(0.22);
    rm14();
} else if (OPTION == "cheekjack") {
    case_parts();
    color("#3a3f45") cheek_r_jack();
    rear_panel(true);
    panel_jack();
}
