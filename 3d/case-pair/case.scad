// case.scad - TS06-DISP + TS06-DRV case, concept A.
//
// Two cheeks carry everything (Rev F's idea, kept): the electronics module (TS06-DISP riding on
// TS06-DRV) hangs from four bosses, the fascia from four more, and a brow, a top plate, a trench
// frame, a base and a rear panel close the box between them. Every number is a named variable in
// params.scad with its source; this file only derives from them (the same maths as case_pair.py,
// which also runs the checks and draws the dimensioned sheets).
//
//   openscad -D 'PART="assembly"' case.scad          assembly (also: module, cheek_l, cheek_r, brow,
//                                                     top, trench, base, rear, fascia_blank,
//                                                     fascia_frame, none)
//   openscad -D EXPLODE=1 ...                         pulled apart
//   openscad -D FASCIA_FRAME=1 ...                    variant D: the fascia in a printed frame
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

// the fascia's own J1 (fascia R rev B) is UPRIGHT: the plug stands off the back along the fascia's normal and the wires leave its top straight
// back into the case, over the pin row. The floor is the model's rule on the lead's lowest point at the plug (never above the frame's Y 0),
// held down by the base's end blocks, which have to clear TS06-DRV's bottom edge by MOD_CLR as the module slides out (checks.md, 7 and 8)
FJ_EXIT  = fpt(FJ_PIN_T, FASCIA_T + FJ_MATED_H);
FJ_LOW_Y = FJ_EXIT[0] - CABLE_HALF;
Y_FLOOR_LEAD  = min(0, floor((FJ_LOW_Y - FLOOR_CLR) * 10) / 10);
Y_FLOOR_SWEEP = floor((DRV_BOT_Y - END_BLOCK - MOD_CLR) * 10) / 10;
Y_FLOOR  = min(Y_FLOOR_LEAD, Y_FLOOR_SWEEP);
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

// the SR25's rim rises above the sill's underside close behind the fascia's top edge: the sill steps back over it
ROT = FASCIA_CTRL[0];                               // ["SW1", x, y, hole]
ROT_T_TOP = ROT[2] - ROTARY_D / 2;
ROT_S_CLR = (SILL_TOP_Y - ROT_T_TOP * cos(r) - (SILL_TOP_Y - SILL_T - 0.5)) / sin(r);
SILL_NOTCH_Z  = round(max(Z_SILL_F, fpt(ROT_T_TOP, ROT_S_CLR)[1]) * 100) / 100;
SILL_NOTCH_X0 = FASCIA_X0 + ROT[1] - ROTARY_D / 2 - 1;     // world X: the fascia is centred
SILL_NOTCH_X1 = FASCIA_X0 + ROT[1] + ROTARY_D / 2 + 1;

// ---- fixings (case review F7): every cheek screw goes into a heat-set insert in an END_BLOCK block
function zin(y) = Z_FACE + (y - SOFFIT_Y) * tan(rb) + BROW_T / cos(rb);   // the brow face's inside
EB = END_BLOCK;
FIX_BASE_Y  = (Y_BOT + Y_FLOOR + EB) / 2;
FIX_BASE_Z  = [BASE_FIX_Z, Z_REAR_IN - REAR_FIX_DZ];
WALL_BLK_Y1 = IN12_BOT - GLASS_BLK_CLR;                     // under H10's and ИН-15А's glass
WALL_BLK_Y0 = min(SILL_TOP_Y - SILL_T, WALL_BLK_Y1 - EB);
FIX_WALL_Y  = (WALL_BLK_Y0 + WALL_BLK_Y1) / 2;
FIX_BROW_Y  = (SOFFIT_Y + SOFFIT_T + Y_TOP_IN) / 2;
FIX_BROW_Z  = zin(FIX_BROW_Y) + EB / 2;
FIX_TOP_Y   = Y_TOP - EB / 2;
FIX_TOP_Z   = [TOP_FIX_Z, Z_REAR_IN - REAR_FIX_DZ];
TOP_LIP_Y0  = Y_TOP - EB;                                   // TS06-DRV's top edge + MOD_CLR
FF_FIX      = fpt(FF_FIX_T, FASCIA_T + EB / 2);             // [Y, Z]: the fascia frame's end blocks
CHEEK_FIX = concat([for (z = FIX_BASE_Z) [FIX_BASE_Y, z]], [[FIX_WALL_Y, WALL_FIX_Z], [FIX_BROW_Y, FIX_BROW_Z]],
                   [for (z = FIX_TOP_Z) [FIX_TOP_Y, z]], FASCIA_FRAME ? [FF_FIX] : []);
// the rear panel (m4): corners and mid-span, along the bottom into the base's lip, along the top into the top plate's
REAR_SCREWS = [for (y = [FIX_BASE_Y, FIX_TOP_Y]) for (x = [X_IN_L + REAR_FIX_X, BOARD_W / 2, X_IN_R - REAR_FIX_X]) [x, y]];
// lead-ins (F8): the sill only where the lowest LEDs' flanges pass, so it still hides XP21-25
SILL_LEADS = [for (l = LEDS) if (l[1] - LED_FLANGE_D / 2 - SILL_TOP_Y < LEADIN_BELOW)
              [l[0] - LED_FLANGE_D / 2 - LEAD_MARGIN, l[0] + LED_FLANGE_D / 2 + LEAD_MARGIN]];
WALL_L_LEAD = IN12_X[0] - IN12_W / 2 - TRENCH_L_X < LEADIN_BELOW;

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
check("SILL_NOTCH_Z", SILL_NOTCH_Z, PY_SILL_NOTCH_Z);
check("SILL_NOTCH_X0", SILL_NOTCH_X0, PY_SILL_NOTCH_X0);
check("FIX_BASE_Y", FIX_BASE_Y, PY_FIX_BASE_Y);
check("WALL_BLK_Y0", WALL_BLK_Y0, PY_WALL_BLK_Y0);
check("WALL_BLK_Y1", WALL_BLK_Y1, PY_WALL_BLK_Y1);
check("FIX_BROW_Y", FIX_BROW_Y, PY_FIX_BROW_Y);
check("FIX_BROW_Z", FIX_BROW_Z, PY_FIX_BROW_Z);
check("FIX_TOP_Y", FIX_TOP_Y, PY_FIX_TOP_Y);
check("TOP_LIP_Y0", TOP_LIP_Y0, PY_TOP_LIP_Y0);
check("FF_FIX_Y", FF_FIX[0], PY_FF_FIX_Y);
check("FF_FIX_Z", FF_FIX[1], PY_FF_FIX_Z);
check("SILL_LEAD_X0", SILL_LEADS[0][0], PY_SILL_LEAD_X0);
check("REAR_SCREWS", len(REAR_SCREWS), PY_REAR_SCREWS);

// ============================================================ primitives in world coordinates
module wbox(x0, x1, y0, y1, z0, z1) translate([x0, z0, y0]) cube([x1 - x0, z1 - z0, y1 - y0]);
// extrude a side profile [[Z, Y], ...] along X
module xprism(x0, x1, prof) multmatrix([[0, 0, 1, x0], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]])
    linear_extrude(height = x1 - x0, convexity = 10) polygon(prof);
module xcyl(x0, x1, y, z, d) translate([x0, z, y]) rotate([0, 90, 0]) cylinder(h = x1 - x0, d = d);
module zcyl(x, y, z0, z1, d, fn = 0) translate([x, z0, y]) rotate([-90, 0, 0])
    cylinder(h = z1 - z0, d = d, $fn = fn > 0 ? fn : $fn);
module ycyl(x, z, y0, y1, d) translate([x, z, y0]) cylinder(h = y1 - y0, d = d);
// extrude a plan profile [[X, Z], ...] along Y
module yprism(y0, y1, prof) translate([0, 0, y0]) linear_extrude(height = y1 - y0, convexity = 10) polygon(prof);
// the raked frame of the fascia plane: local x = X, local y = t (down the face from its top edge), local z = s (behind
// its front face); fframe() is the fascia board's own, FASCIA_X0 to the right (centred under the tube row)
module rake() multmatrix([[1, 0, 0, 0], [0, -sin(r), cos(r), Z_FACE], [0, -cos(r), -sin(r), SILL_TOP_Y], [0, 0, 0, 1]])
    children();
module fframe() rake() translate([FASCIA_X0, 0, 0]) children();
module ex(v) translate(EXPLODE * [v[0], v[2], v[1]]) children();   // v = [dX, dY, dZ]

// the end blocks at both cheeks, and the M3 inserts in them from the cheek faces (F7)
module blocks(y0, y1, z0, z1) for (x = [X_IN_L, X_IN_R - EB]) wbox(x, x + EB, y0, y1, z0, z1);
module inserts_x(y, z) {
    xcyl(X_IN_L - 1, X_IN_L + INS_M3_L + 0.5, y, z, INS_M3_D);
    xcyl(X_IN_R - INS_M3_L - 0.5, X_IN_R + 1, y, z, INS_M3_D);
}
module insert_rear(x, y) zcyl(x, y, Z_REAR_IN - INS_M25_L - 1, Z_REAR_IN + 1, INS_M25_D, 20);   // the rear panel's M2.5
// a 45° x LEADIN cut on the rear top edge (at Z = z, top face at Y = y) of whatever lies over X x0-x1 (F8)
module lead_top(x0, x1, z, y) xprism(x0, x1, [[z - LEADIN - 0.01, y + 0.01], [z + 0.01, y + 0.01], [z + 0.01, y - LEADIN - 0.01]]);

// ============================================================ profiles
CHEEK_PROFILE = [[Z_TOE, Y_BOT], [Z_REAR_IN, Y_BOT], [Z_REAR_IN, Y_TOP], [Z_BROW_TOP, Y_TOP],
                 [Z_FACE, SOFFIT_Y], [Z_FACE, SILL_TOP_Y], [Z_TOE, Y_FLOOR]];
// the brow: the orange face and the soffit; the soffit's rear lip carries a 45° lead-in for the tall glass (F8)
BROW_PROFILE = [[Z_FACE, SOFFIT_Y], [Z_BROW_TOP, Y_TOP], [zin(Y_TOP), Y_TOP], [zin(SOFFIT_Y + SOFFIT_T), SOFFIT_Y + SOFFIT_T],
                [Z_BACK - LEADIN - SOFFIT_T, SOFFIT_Y + SOFFIT_T], [Z_BACK - LEADIN - SOFFIT_T, SOFFIT_Y + LEADIN + SOFFIT_T],
                [Z_BACK, SOFFIT_Y + LEADIN + SOFFIT_T], [Z_BACK, SOFFIT_Y + LEADIN], [Z_BACK - LEADIN, SOFFIT_Y]];
// the top plate: black, a separate part behind the brow face (case review m5)
TOP_PROFILE = [[zin(Y_TOP_IN), Y_TOP_IN], [zin(Y_TOP), Y_TOP], [Z_REAR_IN, Y_TOP], [Z_REAR_IN, Y_TOP_IN]];
T_KB = (SILL_TOP_Y - Y_FLOOR - KICK_T * sin(r)) / cos(r);
BASE_PROFILE = [[Z_TOE, Y_BOT], [Z_REAR_IN, Y_BOT], [Z_REAR_IN, Y_FLOOR], zy(fpt(T_KB, KICK_T)),
                zy(fpt(FASCIA_H, KICK_T)), zy(fpt(FASCIA_H, 0)), [Z_TOE, Y_FLOOR]];

// ============================================================ the case

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
    x0 = left ? X_IN_L - FASCIA_X0 : h[0] - 3.5;     // the fascia frame is FASCIA_X0 right of world X
    x1 = left ? h[0] + 3.5 : X_IN_R - FASCIA_X0;
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
            if (!FASCIA_FRAME)                      // variant D's frame replaces these four
                for (h = FASCIA_HOLES) if ((h[0] < FASCIA_W / 2) == left) fascia_boss(h);
        }
        if (left)                                   // USB: 12 x 9 slot, open to the rear edge
            wbox(X_OUT_L - 1, X_IN_L + 1, USB_Y - USB_SLOT_W / 2, USB_Y + USB_SLOT_W / 2,
                 USB_Z - USB_SLOT_H / 2, Z_REAR_IN + 1);
        else {                                      // 12 V: Ø9 through, Ø14 counterbore from OUTSIDE
            xcyl(X_IN_R - 1, X_OUT_R + 1, JACK_Y, JACK_Z, JACK_HOLE_D);
            xcyl(X_IN_R + JACK_WEB, X_OUT_R + 1, JACK_Y, JACK_Z, JACK_CB_D);
        }
        // M3 x 8 from outside through the cheek into the inserts in the crossmembers' end blocks (F7)
        for (p = CHEEK_FIX) {
            xcyl(x0 - 1, x1 + 1, p[0], p[1], CLR_M3);
            xcyl(left ? x0 - 1 : x1 - CB_DEPTH, left ? x0 + CB_DEPTH : x1 + 1, p[0], p[1], CB_D);
        }
    }
}

module brow() difference() {
    union() {
        xprism(X_IN_L, X_IN_R, BROW_PROFILE);
        wbox(VAL_X0, VAL_X1, VALANCE_Y0, SOFFIT_Y + LEADIN, Z_BACK - VALANCE_T, Z_BACK);   // hides XP12 over the ИН-17s
        blocks(FIX_BROW_Y - EB / 2, FIX_BROW_Y + EB / 2, zin(FIX_BROW_Y + EB / 2) - 1, FIX_BROW_Z + EB / 2);
    }
    inserts_x(FIX_BROW_Y, FIX_BROW_Z);
}

module top_plate() difference() {
    union() {
        xprism(X_IN_L, X_IN_R, TOP_PROFILE);
        blocks(TOP_LIP_Y0, Y_TOP_IN + 0.01, FIX_TOP_Z[0] - EB / 2, FIX_TOP_Z[0] + EB / 2);
        blocks(TOP_LIP_Y0, Y_TOP_IN + 0.01, FIX_TOP_Z[1] - EB / 2, Z_REAR_IN);
        wbox(X_IN_L, X_IN_R, TOP_LIP_Y0, Y_TOP_IN + 0.01, Z_REAR_IN - EB, Z_REAR_IN);   // the rear panel's top screws (m4)
    }
    for (z = FIX_TOP_Z) inserts_x(FIX_TOP_Y, z);
    for (s = REAR_SCREWS) if (s[1] > 0) insert_rear(s[0], s[1]);
}

module trench() difference() {
    union() {
        difference() {                              // the sill (trench floor), stepped back over the rotary
            wbox(X_IN_L, X_IN_R, SILL_TOP_Y - SILL_T, SILL_TOP_Y, Z_SILL_F, Z_BACK);
            wbox(SILL_NOTCH_X0, SILL_NOTCH_X1, SILL_TOP_Y - SILL_T - 1, SILL_TOP_Y + 1, Z_SILL_F - 1, SILL_NOTCH_Z);
        }
        wbox(X_IN_L, TRENCH_L_X, SILL_TOP_Y, SOFFIT_Y, Z_FACE, Z_BACK);      // hides XP11 (review 4)
        wbox(TRENCH_R_X, X_IN_R, SILL_TOP_Y, SOFFIT_Y, Z_FACE, Z_BACK);
        blocks(WALL_BLK_Y0, WALL_BLK_Y1, WALL_FIX_Z - EB / 2, WALL_FIX_Z + EB / 2 + LEADIN);   // F7: under H10 / ИН-15А
        for (s = SILL_LEADS)                        // under the sill's lead-ins, so they are a full LEADIN deep
            wbox(s[0], s[1], SILL_TOP_Y - LEADIN - 0.5, SILL_TOP_Y - SILL_T + 0.01, Z_BACK - LEADIN - 1, Z_BACK);
    }
    inserts_x(FIX_WALL_Y, WALL_FIX_Z);
    // F8: 45° lead-ins on the rear edges the module passes within LEADIN_BELOW
    for (s = SILL_LEADS) lead_top(s[0], s[1], Z_BACK, SILL_TOP_Y);
    lead_top(TRENCH_L_X, X_IN_L + EB, WALL_FIX_Z + EB / 2 + LEADIN, WALL_BLK_Y1);          // the left block, under H10
    if (WALL_L_LEAD)                                // the left wall's inner rear edge, beside H10
        yprism(SILL_TOP_Y - 0.01, SOFFIT_Y + 0.01, [[TRENCH_L_X + 0.01, Z_BACK - LEADIN - 0.01],
               [TRENCH_L_X + 0.01, Z_BACK + 0.01], [TRENCH_L_X - LEADIN - 0.01, Z_BACK + 0.01]]);
    if (FASCIA_FRAME) for (x = FF_RIB_X) {          // variant D: the sill ties, M2.5 countersunk
        ycyl(x, FF_TIE_Z, SILL_TOP_Y - SILL_T - 1, SILL_TOP_Y + 1, REAR_HOLE_D);
        translate([x, FF_TIE_Z, SILL_TOP_Y - 1.4]) cylinder(h = 1.41, d1 = REAR_HOLE_D, d2 = 5.2);
    }
}

module base() difference() {
    union() {
        xprism(X_IN_L, X_IN_R, BASE_PROFILE);
        blocks(Y_FLOOR - 0.01, Y_FLOOR + EB, FIX_BASE_Z[0] - EB / 2, FIX_BASE_Z[0] + EB / 2);
        blocks(Y_FLOOR - 0.01, Y_FLOOR + EB, FIX_BASE_Z[1] - EB / 2, Z_REAR_IN);
        wbox(X_IN_L, X_IN_R, Y_FLOOR - 0.01, Y_FLOOR + EB, Z_REAR_IN - EB, Z_REAR_IN);   // the rear panel's bottom screws (m4)
    }
    for (z = FIX_BASE_Z) inserts_x(FIX_BASE_Y, z);
    for (s = REAR_SCREWS) if (s[1] < 0) insert_rear(s[0], s[1]);
}

module rear_panel(label = false) {
    color("#15181b") difference() {
        wbox(X_OUT_L, X_OUT_R, Y_BOT, Y_TOP, Z_REAR_IN, Z_REAR_OUT);
        for (x = [VENT_X0 : VENT_PITCH : VENT_X1 - VENT_W])        // vents <= 2.5 wide (review 4), over the logic (m4)
            hull() for (y = [VENT_Y0 + VENT_W / 2, VENT_Y1 - VENT_W / 2]) zcyl(x + VENT_W / 2, y, Z_REAR_IN - 1, Z_REAR_OUT + 1, VENT_W, 16);
        for (s = REAR_SCREWS)                       // slotted ±SLOT_X along X: the printed parts set the spacing (F9)
            hull() for (dx = [-SLOT_X, SLOT_X]) zcyl(s[0] + dx, s[1], Z_REAR_IN - 1, Z_REAR_OUT + 1, REAR_HOLE_D, 16);
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
        // J1, upright: the header (its plastic is 13.9 wide inside the 15.95 outline, which counts the metal tabs) and the mated PHR-6 standing
        // out of its mouth up to where the wires leave (illustrative bodies)
        color("#f2f2f2") translate([FJ_BODY[0] + 1.025, FJ_BODY[2], FASCIA_T]) cube([FJ_BODY[1] - FJ_BODY[0] - 2.05, FJ_BODY[3] - FJ_BODY[2], FJ_HDR_H]);
        color("#e6e1d3") translate([FJ_BODY[0] + 1.5, FJ_PIN_T - 2.0, FASCIA_T + FJ_HDR_H - 1.0])
            cube([FJ_BODY[1] - FJ_BODY[0] - 3.0, 4.0, FJ_MATED_H - FJ_HDR_H + 1.0]);
        if (FASCIA_FRAME)                           // variant D is drawn for a 179 board that does not exist yet
            color("#d63384") translate([62, FASCIA_H - 5, -0.05]) mirror([0, 1, 0]) mirror([0, 0, 1])
                linear_extrude(0.2) text("176 STAND-IN", size = 3.2, font = "DejaVu Sans:style=Bold");
    }
}

// ============================================================ variant D: the fascia frame (FASCIA_FRAME = 1)
// A printed frame between the cheeks, raked with the fascia. Its pocket continues the trench walls (X TRENCH_L_X to
// TRENCH_R_X) and takes a FF_PANEL_W x FF_PANEL_H panel in a rabbet: a ledge behind its sides and bottom, a top rail
// under the sill, ribs between the controls. The panel screws into four bosses; each cheek screws into an end block;
// the sill bears on the top rail and is screwed down into the rib heads. It replaces the four cheek bosses.
FF_X0 = TRENCH_L_X;  FF_X1 = TRENCH_R_X;
FF_D = FASCIA_T + FF_WEB;
FF_BOSS_R = INS_M25_D / 2 + INS_WALL_MIN;
FF_J1 = [FASCIA_X0 + FJ_BOX[0] - 1, FASCIA_X0 + FJ_BOX[1] + 1];
module fascia_frame() difference() {
    union() {
        rake() difference() {
            translate([X_IN_L, 0, 0]) cube([X_IN_R - X_IN_L, FF_PANEL_H, FF_D]);
            translate([FF_X0, -1, -1]) cube([FF_X1 - FF_X0, FF_PANEL_H + 2, FASCIA_T + 1]);       // the rabbet
            translate([FF_X0 + FF_LEDGE, FF_TOP, FASCIA_T - 1])                                      // the window behind
                cube([FF_X1 - FF_X0 - 2 * FF_LEDGE, FF_PANEL_H - FF_LEDGE - FF_TOP, FF_WEB + 2]);
            translate([SILL_NOTCH_X0, -1, FASCIA_T - 1]) cube([SILL_NOTCH_X1 - SILL_NOTCH_X0, FF_TOP + 2, FF_WEB + 2]);  // rotary
            if (FF_J1_CUT)                         // the side-entry plug reached the ledge; the upright one (rev B) does not
                translate([FF_J1[0], FF_PANEL_H - FF_LEDGE - 1, FASCIA_T - 1]) cube([FF_J1[1] - FF_J1[0], FF_LEDGE + 2, FF_WEB + 2]);  // J1
        }
        rake() {
            for (x = FF_RIB_X) translate([x - FF_RIB_W / 2, 0, FASCIA_T]) cube([FF_RIB_W, FF_PANEL_H, FF_WEB]);
            for (h = FF_HOLES) translate([h[0], h[1], FASCIA_T]) cylinder(h = INS_M25_L + 0.5 + INS_WALL_MIN, r = FF_BOSS_R);
            for (x = [X_IN_L, X_IN_R - EB]) translate([x, FF_FIX_T - EB, FASCIA_T]) cube([EB, 2 * EB, EB]);
        }
        for (x = FF_RIB_X) hull() {                 // the rib heads under the sill, for its ties
            wbox(x - FF_BOSS_R, x + FF_BOSS_R, SILL_TOP_Y - SILL_T - EB, SILL_TOP_Y - SILL_T,
                 FF_TIE_Z - FF_BOSS_R, FF_TIE_Z + FF_BOSS_R);
            rake() translate([x - FF_RIB_W / 2, 0, FASCIA_T]) cube([FF_RIB_W, 2 * EB, FF_WEB]);
        }
    }
    wbox(X_IN_L - 1, X_IN_R + 1, SILL_TOP_Y - SILL_T, SILL_TOP_Y + 5, Z_SILL_F - 0.2, Z_BACK + 1);   // the sill sits here
    rake() for (h = FF_HOLES) translate([h[0], h[1], FASCIA_T - 0.01]) cylinder(h = INS_M25_L + 0.5, d = INS_M25_D);
    inserts_x(FF_FIX[0], FF_FIX[1]);
    for (x = FF_RIB_X) ycyl(x, FF_TIE_Z, SILL_TOP_Y - SILL_T - INS_M25_L - 0.5, SILL_TOP_Y - SILL_T + 0.01, INS_M25_D);
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
    color("#f28c28") ex([0, 36, -12]) brow();                // safety orange (spec §6)
    color("#2b2f34") ex([0, 62, 0]) top_plate();             // black, like the chassis (case review m5)
    color("#30363d") ex([0, 0, -30]) trench();
    color("#30363d") ex([0, -30, 0]) base();
    if (FASCIA_FRAME) color("#30363d") ex([0, -8, -42]) fascia_frame();
    ex([0, 0, 50]) rear_panel(true);
    ex([0, -6, -60]) fascia_dressed();
    ex([0, 0, 22]) stack();
    if (EXPLODE == 0) lead();
}

if (PART == "assembly") assembly();
else if (PART == "module") stack();
else if (PART == "cheek_l") cheek(true);
else if (PART == "cheek_r") cheek(false);
else if (PART == "brow") brow();
else if (PART == "top") top_plate();
else if (PART == "trench") trench();
else if (PART == "base") base();
else if (PART == "rear") rear_panel();
else if (PART == "fascia_blank") fascia_blank();
else if (PART == "fascia_frame") fascia_frame();
