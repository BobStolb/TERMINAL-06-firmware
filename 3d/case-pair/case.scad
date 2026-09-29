// case.scad - TS06-DISP + TS06-DRV case, concept A.
//
// Two cheeks carry everything (Rev F's idea, kept): the electronics module (TS06-DISP riding on
// TS06-DRV) hangs from four bosses, the fascia from four more, and a brow, a trench frame, a base
// and a rear panel close the box between them. Every number is a named variable in params.scad
// with its source; this file only derives from them (the same maths as case_pair.py, which also
// runs the checks and draws the dimensioned sheets).
//
//   openscad -D 'PART="assembly"' case.scad          assembly (also: module, cheek_l, cheek_r,
//                                                     brow, trench, base, rear, fascia_blank, none)
//   openscad -D EXPLODE=1 ...                         pulled apart
//
// World frame: X across the front from the clock's left, Y up (FreeCAD assembly), Z depth from
// the ИН-12 glass front, + toward the back. OpenSCAD: x = X, y = Z, z = Y (the clock faces -y).

include <params.scad>

PART = "assembly";
EXPLODE = 0;
$fn = 40;

// ============================================================ derived (mirrors case_pair.py)
r  = FASCIA_RAKE;
rb = BROW_RAKE;
Z_FACE     = -GLASS_RECESS;                         // the face plane: brow front, fascia top edge
Z_DISP_F   = IN12_D + IN12_SEAT;                    // TS06-DISP front face
Z_DISP_B   = Z_DISP_F + PCB_T;
STACK_GAP  = PBS_H + PLS_BODY;                      // 11: review finding 1 - measure the strips
Z_DRV_F    = Z_DISP_B + STACK_GAP;                  // TS06-DRV, display-facing face
Z_DRV_B    = Z_DRV_F + PCB_T;                       // TS06-DRV, component face (toward the rear)
Z_BACK     = Z_DISP_F - BACK_GAP;                   // no case part behind this, in front of TS06-DISP
IN17_STANDOFF = Z_DISP_F - IN17_D;                  // ИН-17 faces coplanar with the ИН-12s
NANO_H     = PBS_H + PLS_BODY + NANO_PCB_T + USB_H;
DISP_BOT_Y = DISP_TOP_Y - DISP_H;
DRV_TOP_Y  = DISP_TOP_Y + DRV_Y0;
DRV_BOT_Y  = DRV_TOP_Y - DRV_H;
IN12_TOP   = IN12_Y + IN12_H / 2;
IN12_BOT   = IN12_Y - IN12_H / 2;
SOFFIT_Y   = round((IN12_TOP + BROW_CLR) * 100) / 100;
Y_TOP_IN   = DRV_TOP_Y + TOP_CLR;
Y_TOP      = Y_TOP_IN + TOP_T;
X_IN_L = -CHEEK_CLR;            X_IN_R = BOARD_W + CHEEK_CLR;
X_OUT_L = X_IN_L - CHEEK_T;     X_OUT_R = X_IN_R + CHEEK_T;
PART_MAX   = max([for (p = DRV_PARTS) if (p[6] == 0) p[5]]);
Z_REAR_IN  = Z_DRV_B + PART_MAX + REAR_AIR;
Z_REAR_OUT = Z_REAR_IN + REAR_T;

// the fascia: its front face passes through the sill's front edge (SILL_TOP_Y, Z_FACE), raked back.
// fpt(t, s) = [Y, Z] of the point t down the face from the top edge and s behind the front face.
function fpt(t, s = 0) = [SILL_TOP_Y - t * cos(r) - s * sin(r), Z_FACE - t * sin(r) + s * cos(r)];
function zy(p) = [p[1], p[0]];
FAS_BOT    = fpt(FASCIA_H);
Z_SILL_F   = Z_FACE + FASCIA_T / cos(r) + 0.2;

// the fascia's own J1 is side-entry and sends its lead toward the fascia's bottom edge: the lead's
// bend sets how far below the fascia the floor has to be (checks.md, 8)
FJ_EXIT  = fpt(FJ_BOX[3] + FJ_PLUG_OUT, FASCIA_T + FJ_HDR_H / 2);
FJ_LOW_Y = FJ_EXIT[0] - CABLE_R * sin(r) - CABLE_R - CABLE_HALF;
Y_FLOOR  = min(0, floor((FJ_LOW_Y - FLOOR_CLR) * 10) / 10);
Y_BOT    = Y_FLOOR - BASE_T;
Z_TOE    = Z_FACE - (SILL_TOP_Y - Y_FLOOR) * tan(r);
Z_BROW_TOP = Z_FACE + (Y_TOP - SOFFIT_Y) * tan(rb);
OUT_W = X_OUT_R - X_OUT_L;  OUT_H = Y_TOP - Y_BOT;  OUT_D = Z_REAR_OUT - Z_TOE;

// openings
JACK_Y = JACK_PIN1[1];
JACK_Z = Z_DRV_B + JACK_AXIS_H;
JACK_MOUTH_X = JACK_PIN1[0] + JACK_BODY_L - 0.8;    // F.Fab: the mouth is 13.7 from pin 1
USB_X = NANO_BOX[0];
USB_Y = (NANO_ROWS_Y[0] + NANO_ROWS_Y[1]) / 2;
USB_Z = Z_DRV_B + PBS_H + PLS_BODY + NANO_PCB_T + USB_H / 2;

// the brow's rib behind the ИН-17 pair, between M1's and ИН-15Б's glass
VAL_X0 = IN12_X[3] + IN12_W / 2 + GLASS_ALLOW;
VAL_X1 = IN15_X[0] - IN12_W / 2 - GLASS_ALLOW;

// the SR25's rim reaches 0.5 mm below the fascia's top edge: the sill steps back over it
ROT = FASCIA_CTRL[0];                               // ["SW1", x, y, hole]
ROT_T_TOP = ROT[2] - ROTARY_D / 2;
ROT_S_CLR = (SILL_TOP_Y - ROT_T_TOP * cos(r) - (SILL_TOP_Y - SILL_T - 0.5)) / sin(r);
SILL_NOTCH_Z  = round(max(Z_SILL_F, fpt(ROT_T_TOP, ROT_S_CLR)[1]) * 100) / 100;
SILL_NOTCH_X0 = ROT[1] - ROTARY_D / 2 - 1;
SILL_NOTCH_X1 = ROT[1] + ROTARY_D / 2 + 1;

module check(name, a, b) echo(str(name, " scad=", a, " py=", b, abs(a - b) < 0.01 ? "  ok" : "  MISMATCH"));
check("Z_DISP_F", Z_DISP_F, PY_Z_DISP_F);
check("Z_DRV_B", Z_DRV_B, PY_Z_DRV_B);
check("PART_MAX", PART_MAX, PY_PART_MAX);
check("Z_REAR_IN", Z_REAR_IN, PY_Z_REAR_IN);
check("SOFFIT_Y", SOFFIT_Y, PY_SOFFIT_Y);
check("Y_FLOOR", Y_FLOOR, PY_Y_FLOOR);
check("Z_TOE", Z_TOE, PY_Z_TOE);
check("OUT_W", OUT_W, PY_OUT_W);
check("OUT_H", OUT_H, PY_OUT_H);
check("OUT_D", OUT_D, PY_OUT_D);

// ============================================================ primitives in world coordinates
module wbox(x0, x1, y0, y1, z0, z1) translate([x0, z0, y0]) cube([x1 - x0, z1 - z0, y1 - y0]);
// extrude a side profile [[Z, Y], ...] along X
module xprism(x0, x1, prof) multmatrix([[0, 0, 1, x0], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]])
    linear_extrude(height = x1 - x0) polygon(prof);
module xcyl(x0, x1, y, z, d) translate([x0, z, y]) rotate([0, 90, 0]) cylinder(h = x1 - x0, d = d);
module zcyl(x, y, z0, z1, d, fn = 0) translate([x, z0, y]) rotate([-90, 0, 0])
    cylinder(h = z1 - z0, d = d, $fn = fn > 0 ? fn : $fn);
// the fascia's frame: local x = X, local y = t (down the face), local z = s (into the case)
module fframe() multmatrix([[1, 0, 0, 0], [0, -sin(r), cos(r), Z_FACE], [0, -cos(r), -sin(r), SILL_TOP_Y], [0, 0, 0, 1]])
    children();
module ex(v) translate(EXPLODE * [v[0], v[2], v[1]]) children();   // v = [dX, dY, dZ]

// ============================================================ profiles
function zin(y) = Z_FACE + (y - SOFFIT_Y) * tan(rb) + BROW_T / cos(rb);   // the brow face's inside
CHEEK_PROFILE = [[Z_TOE, Y_BOT], [Z_REAR_IN, Y_BOT], [Z_REAR_IN, Y_TOP], [Z_BROW_TOP, Y_TOP],
                 [Z_FACE, SOFFIT_Y], [Z_FACE, SILL_TOP_Y], [Z_TOE, Y_FLOOR]];
BROW_PROFILE = [[Z_FACE, SOFFIT_Y], [Z_BROW_TOP, Y_TOP], [Z_REAR_IN, Y_TOP], [Z_REAR_IN, Y_TOP_IN],
                [zin(Y_TOP_IN), Y_TOP_IN], [zin(SOFFIT_Y + SOFFIT_T), SOFFIT_Y + SOFFIT_T],
                [Z_BACK, SOFFIT_Y + SOFFIT_T], [Z_BACK, SOFFIT_Y]];
T_KB = (SILL_TOP_Y - Y_FLOOR - KICK_T * sin(r)) / cos(r);
BASE_PROFILE = [[Z_TOE, Y_BOT], [Z_REAR_IN, Y_BOT], [Z_REAR_IN, Y_FLOOR], zy(fpt(T_KB, KICK_T)),
                zy(fpt(FASCIA_H, KICK_T)), zy(fpt(FASCIA_H, 0)), [Z_TOE, Y_FLOOR]];

// ============================================================ the case
REAR_SCREWS = [for (x = [X_OUT_L + CHEEK_T / 2, X_OUT_R - CHEEK_T / 2]) for (y = [Y_BOT + 8, Y_TOP - 5]) [x, y]];

module drv_boss(h) {                                // [X, Y] of a TS06-DRV case hole (H5-H8)
    left = h[0] < BOARD_W / 2;
    x0 = left ? X_IN_L : h[0] - BOSS_W / 2;
    x1 = left ? h[0] + BOSS_W / 2 : X_IN_R;
    y0r = h[1] - BOSS_W / 2;
    y1 = h[1] + BOSS_W / 2;
    y0 = (y0r < DISP_TOP_Y + 0.5 && y1 > DISP_TOP_Y) ? DISP_TOP_Y + 0.5 : y0r;   // TS06-DISP slides past
    difference() {
        wbox(x0, x1, y0, y1, Z_DRV_F - BOSS_D, Z_DRV_F);
        zcyl(h[0], h[1], Z_DRV_F - 8, Z_DRV_F + 1, 4.0);                     // M3 heat-set insert
    }
}

module fascia_boss(h) {                             // [x, y, drill] in the fascia's frame
    left = h[0] < FASCIA_W / 2;
    x0 = left ? X_IN_L : h[0] - 3.5;
    x1 = left ? h[0] + 3.5 : X_IN_R;
    difference() {
        fframe() translate([x0, h[1] - 3.5, FASCIA_T]) cube([x1 - x0, 7, FBOSS_D]);
        fframe() translate([h[0], h[1], FASCIA_T - 1]) cylinder(h = FBOSS_D - 1, d = 3.5);   // M2.5 insert
        wbox(X_IN_L - 1, X_IN_R + 1, SILL_TOP_Y - SILL_T - 0.2, SILL_TOP_Y + 1, Z_SILL_F - 0.2, Z_BACK + 1);
    }
}

module cheek(left) {
    x0 = left ? X_OUT_L : X_IN_R;
    x1 = left ? X_IN_L : X_OUT_R;
    difference() {
        union() {
            xprism(x0, x1, CHEEK_PROFILE);
            for (h = DRV_CASE_HOLES) if ((h[0] < BOARD_W / 2) == left) drv_boss(h);
            for (h = FASCIA_HOLES) if ((h[0] < FASCIA_W / 2) == left) fascia_boss(h);
        }
        if (left)                                   // USB: 12 x 9 slot, open to the rear edge
            wbox(X_OUT_L - 1, X_IN_L + 1, USB_Y - USB_SLOT_W / 2, USB_Y + USB_SLOT_W / 2,
                 USB_Z - USB_SLOT_H / 2, Z_REAR_IN + 1);
        else {                                      // 12 V: Ø9 through, Ø14 counterbore from OUTSIDE
            xcyl(X_IN_R - 1, X_OUT_R + 1, JACK_Y, JACK_Z, JACK_HOLE_D);
            xcyl(X_IN_R + JACK_WEB, X_OUT_R + 1, JACK_Y, JACK_Z, JACK_CB_D);
        }
        for (s = REAR_SCREWS) if ((s[0] < 0) == left) zcyl(s[0], s[1], Z_REAR_IN - 8, Z_REAR_IN + 1, 3.5);
        // fixing holes through the cheek: base, trench walls, brow (M3, counterbored outside)
        for (p = [[Y_FLOOR - BASE_T / 2, 10], [Y_FLOOR - BASE_T / 2, Z_REAR_IN - 12],
                  [(SILL_TOP_Y + SOFFIT_Y) / 2, 12], [Y_TOP - TOP_T / 2, 20], [Y_TOP - TOP_T / 2, Z_REAR_IN - 12]]) {
            xcyl(x0 - 1, x1 + 1, p[0], p[1], 3.4);
            xcyl(left ? x0 - 1 : x1 - 2, left ? x0 + 2 : x1 + 1, p[0], p[1], 6.2);
        }
    }
}

module brow() {
    xprism(X_IN_L, X_IN_R, BROW_PROFILE);
    wbox(VAL_X0, VAL_X1, VALANCE_Y0, SOFFIT_Y + 0.01, Z_BACK - VALANCE_T, Z_BACK);   // hides XP12 over the ИН-17s
}

module trench() {
    difference() {                                  // the sill (trench floor), stepped back over the rotary
        wbox(X_IN_L, X_IN_R, SILL_TOP_Y - SILL_T, SILL_TOP_Y, Z_SILL_F, Z_BACK);
        wbox(SILL_NOTCH_X0, SILL_NOTCH_X1, SILL_TOP_Y - SILL_T - 1, SILL_TOP_Y + 1, Z_SILL_F - 1, SILL_NOTCH_Z);
    }
    wbox(X_IN_L, TRENCH_L_X, SILL_TOP_Y, SOFFIT_Y, Z_FACE, Z_BACK);      // hides XP11 (review 4)
    wbox(TRENCH_R_X, X_IN_R, SILL_TOP_Y, SOFFIT_Y, Z_FACE, Z_BACK);
}

module base() xprism(X_IN_L, X_IN_R, BASE_PROFILE);

module rear_panel(label = false) {
    color("#15181b") difference() {
        wbox(X_OUT_L, X_OUT_R, Y_BOT, Y_TOP, Z_REAR_IN, Z_REAR_OUT);
        for (x = [VENT_X0 : VENT_PITCH : VENT_X1 - VENT_W])        // vents <= 2.5 wide (review 4)
            hull() for (y = [VENT_Y0 + VENT_W / 2, VENT_Y1 - VENT_W / 2]) zcyl(x + VENT_W / 2, y, Z_REAR_IN - 1, Z_REAR_OUT + 1, VENT_W, 16);
        for (s = REAR_SCREWS) zcyl(s[0], s[1], Z_REAR_IN - 1, Z_REAR_OUT + 1, 2.7);
    }
    if (label) color("white") for (l = [["12 V DC  centre +", 60], ["! 185 V INSIDE", 45], ["unplug, wait 15 s", 36]])
        translate([150, Z_REAR_OUT, l[1]]) rotate([90, 0, 180]) linear_extrude(0.15) text(l[0], size = 4.5, font = "DejaVu Sans:style=Bold");
}

module fascia_blank() {                             // the fit proxy the cad library asks for (§5)
    fframe() difference() {
        linear_extrude(FASCIA_T) polygon([[1.5, 0], [FASCIA_W - 1.5, 0], [FASCIA_W, 1.5], [FASCIA_W, FASCIA_H - 1.5],
                                          [FASCIA_W - 1.5, FASCIA_H], [1.5, FASCIA_H], [0, FASCIA_H - 1.5], [0, 1.5]]);
        for (h = FASCIA_HOLES) translate([h[0], h[1], -1]) cylinder(h = FASCIA_T + 2, d = h[2]);
        for (c = FASCIA_CTRL) translate([c[1], c[2], -1]) cylinder(h = FASCIA_T + 2, d = c[3]);
    }
}

module fascia_dressed() {                           // the board, its controls and J1 (illustrative bodies)
    color("#1c1f22") fascia_blank();
    fframe() {
        for (c = FASCIA_CTRL) translate([c[1], c[2], 0]) {
            if (c[0] == "SW1") {
                color("#6e7781") translate([0, 0, FASCIA_T]) cylinder(h = ROTARY_DEPTH, d = ROTARY_D);
                color("#2d333b") translate([0, 0, -14]) cylinder(h = 14, d = 20);
                color("#f28c28") translate([-0.6, -9, -14.2]) cube([1.2, 6, 0.4]);
            } else if (c[0] == "SW2" || c[0] == "SW3") {
                color("#8c959f") translate([-MT1_L / 2, -MT1_W / 2, FASCIA_T]) cube([MT1_L, MT1_W, MT1_DEPTH]);
                color("#c9d1d9") rotate([-20, 0, 0]) translate([0, 0, -16]) cylinder(h = 16, d1 = 2.5, d2 = 4);
            } else {
                color("#8c959f") translate([-KMD1_A / 2, -KMD1_B / 2, FASCIA_T]) cube([KMD1_A, KMD1_B, KMD1_DEPTH]);
                color("#2d333b") translate([0, 0, -6]) cylinder(h = 6, d = 11);
            }
        }
        color("#f2f2f2") translate([FJ_BOX[0] + 1, FJ_BOX[2], FASCIA_T]) cube([FJ_BOX[1] - FJ_BOX[0] - 2, FJ_BOX[3] - FJ_BOX[2], FJ_HDR_H]);
        color("#f2f2f2") translate([FJ_BOX[0] + 3, FJ_BOX[3], FASCIA_T + 0.5]) cube([FJ_BOX[1] - FJ_BOX[0] - 6, FJ_PLUG_OUT, FJ_HDR_H - 1]);
    }
}

module lead() color("#8250df") for (i = [0 : len(LEAD) - 2])
    hull() for (p = [LEAD[i], LEAD[i + 1]]) translate([p[0], p[2], p[1]]) sphere(d = 2 * CABLE_HALF + 0.6, $fn = 10);

// ============================================================ the module: TS06-DISP on TS06-DRV
module in12(x, y) color([1, 0.74, 0.42, 0.45]) hull() for (dx = [-1, 1], dy = [-1, 1])
    zcyl(x + dx * (IN12_W / 2 - 2), y + dy * (IN12_H / 2 - 2), 0, IN12_D, 4);
module in17(x, y) color([1, 0.74, 0.42, 0.45]) hull() {
    wbox(x - IN17_FACE / 2, x + IN17_FACE / 2, y - IN17_H / 2, y + IN17_H / 2, 0, 0.5);
    zcyl(x, y, IN17_D - 0.5, IN17_D, IN17_STEM);
}

module stack() {
    color("#2e6b50") wbox(0, BOARD_W, DISP_BOT_Y, DISP_TOP_Y, Z_DISP_F, Z_DISP_B);
    color("#2e6b50") wbox(0, BOARD_W, DRV_BOT_Y, DRV_TOP_Y, Z_DRV_F, Z_DRV_B);
    for (x = IN12_X) in12(x, IN12_Y);
    for (x = IN15_X) in12(x, IN12_Y);
    for (x = IN17_X) in17(x, IN17_Y);
    for (c = COLON) color([1, 0.74, 0.42, 0.6]) zcyl(c[0], c[1], 2, Z_DISP_F, INS1_D);
    for (l = LEDS) color("#f7c873") zcyl(l[0], l[1], Z_DISP_F - LED_H, Z_DISP_F, LED_D);
    for (h = DISP_HOLES) {
        color("#b0b8c0") zcyl(h[0], h[1], Z_DISP_B, Z_DRV_F, 6.35, 6);          // 11 mm M3 standoffs
        color("#0d1117") zcyl(h[0], h[1], Z_DISP_F - SCREW_HEAD, Z_DISP_F, SCREW_HEAD_D);
    }
    for (s = DISP_STRIPS) color("#222") wbox(s[1], s[2], s[3], s[4], Z_DISP_B, Z_DISP_B + PLS_BODY);
    for (p = DRV_PARTS) {
        if (p[6] == 1) color(p[0] == "J1" ? "#f2f2f2" : "#222") wbox(p[1], p[2], p[3], p[4], Z_DRV_F - p[5], Z_DRV_F);
        else if (p[0] == "U1") {                     // the Nano: strips, board, mini-B proud of the edge
            color("#222") wbox(max(p[1], 0.3) + 2, p[2] - 1, p[3], p[4], Z_DRV_B, Z_DRV_B + PBS_H + PLS_BODY);
            color("#1f5fa8") wbox(0.4, p[2], p[3] + 0.3, p[4] - 0.3, Z_DRV_B + PBS_H + PLS_BODY, Z_DRV_B + PBS_H + PLS_BODY + NANO_PCB_T);
            color("#c0c0c0") wbox(USB_X, USB_X + USB_L, USB_Y - USB_W / 2, USB_Y + USB_W / 2, USB_Z - USB_H / 2, USB_Z + USB_H / 2);
        } else if (p[0] == "XS1") {
            color("#222") wbox(JACK_MOUTH_X - JACK_BODY_L, JACK_MOUTH_X, JACK_Y - JACK_BODY_W / 2, JACK_Y + JACK_BODY_W / 2, Z_DRV_B, Z_DRV_B + JACK_BODY_H);
        } else if (p[0] == "C7" || p[0] == "L1" || p[0] == "C8")
            color(p[0] == "L1" ? "#4d4d4d" : "#2b4c7e") zcyl((p[1] + p[2]) / 2, (p[3] + p[4]) / 2, Z_DRV_B, Z_DRV_B + p[5], min(p[2] - p[1], p[4] - p[3]) - 1);
        else if (p[0] == "U13")
            color("#1f5fa8") wbox(p[1], p[2], (p[3] + p[4]) / 2 - 1, (p[3] + p[4]) / 2 + 1, Z_DRV_B, Z_DRV_B + p[5]);
        else
            color(p[5] > 12 ? "#555" : "#9aa7b4") wbox(p[1], p[2], p[3], p[4], Z_DRV_B, Z_DRV_B + p[5]);
    }
}

// ============================================================ assembly
module assembly() {
    color("#3a3f45") ex([-40, 0, 0]) cheek(true);
    color("#3a3f45") ex([40, 0, 0]) cheek(false);
    color("#f28c28") ex([0, 40, 0]) brow();
    color("#30363d") ex([0, 0, -30]) trench();
    color("#30363d") ex([0, -30, 0]) base();
    ex([0, 0, 50]) rear_panel(true);
    ex([0, -6, -55]) fascia_dressed();
    ex([0, 0, 22]) stack();
    if (EXPLODE == 0) lead();
}

if (PART == "assembly") assembly();
else if (PART == "module") stack();
else if (PART == "cheek_l") cheek(true);
else if (PART == "cheek_r") cheek(false);
else if (PART == "brow") brow();
else if (PART == "trench") trench();
else if (PART == "base") base();
else if (PART == "rear") rear_panel();
else if (PART == "fascia_blank") fascia_blank();
