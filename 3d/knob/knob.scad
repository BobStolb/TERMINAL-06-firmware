// TS06 MODE knobs for the SR25's 6 mm shaft (OpenSCAD 2021.01).
//
//   A  RSI    a reading of the owner's black lobed РСИ-4 knob: lobed rim, flat engraved ring, raised centre cap
//   B  BEAK   a chicken-head (клювик) pointer knob
//   C  TURNED an instrument knob to be turned in aluminium or brass: skirt, knurled grip, a bright pointer line
//
//   openscad -D 'part="A"' -D 'ang=75' -o knob_A.stl knob.scad     (see make.sh)
//
// Frame: FRONT view. x right, y up, z toward the viewer. z = 0 is the fascia's FRONT face (R and T alike, the
// stack sits on it). The top view of the model is what the owner sees. `ang` is the pointer's direction in that view
// (the dial's six positions are at 75, 45, 15, -15, -45, -75 degrees: 30.00 per step, position 1 at the top).
// Printed knobs are exported upside down (flip=1: top face on the bed, nothing to support inside).
//
// Values marked (inferred) are typical figures, not a measurement of the SR25, the nut or any printer.

part  = "C";       // A | B | C
ang   = 0;         // pointer direction, degrees, front view
fill  = 1;         // 1 = show the engraved marks filled (pictures); 0 = leave them as cuts (STL)
fillc = "gold";    // gold | cream  (colour of the fill in the pictures)
flip  = 0;         // 1 = print orientation (top face down)

// ---- the one parameter the concepts decide: the diameter -----------------------------------------
D = 18.0;          // skirt / lobe-crest diameter. 18.0 = the dial art's 9.0 keep-out (R as ordered).
                   // T layout 1: bodies start at r 9.83 (the plan), so the skirt overhangs a body above D = 19.66;
                   // D = 19.0 leaves 0.33 mm. Layout 2 (in line on a bigger circle, r 15 as a placeholder): bodies and
                   // pads start at about r 14.05, so D up to about 27 keeps them in view; the largest D comes from the
                   // concepts run, and the dial art has to be drawn for it (the marks now sit at r 11.3).

// ---- the SR25 shaft and the stack (3d/SR25.FCStd; no flat, no knurl, no tab in the model: unconfirmed) -----
shaft_d    = 6.00;
bore_set   = 6.2;    // printed knob, set screw: 6.0 + 0.2 for a vertical hole on a 0.4 nozzle (inferred)
bore_turn  = 6.0;    // turned knob: 6.00 +0.05/0 on the drawing
nut_af     = 11.5;   // nut across flats, the most this design clears (inferred; MEASURE)
recess_d   = 14.0;   // underside pocket round the nut: nut_af / cos(30) = 13.3 across corners + 0.7
z_rim      = 2.6;    // underside rim above the fascia front: T's resistors stand 2.0 (0204 raised on its leads)
z_ceil     = 5.5;    // pocket ceiling: R's bushing ends 5.0 above the face (7.00 usable - 2.0 board); T's ends 4.0
// The shaft as modelled stands 13.0 mm beyond the bushing's end: 18.0 above the face on R, 17.0 on T (the plan's "11 mm"
// subtracts the board twice). A knob's bore has to take all of it, or the shaft has to be sawn short.
//   shaft_top = 12.0  the shaft sawn to 12.0 above the fascia's front face (measure with the switch bolted in), the default:
//                     low knobs, 6.5 mm of grip on the shaft above the pocket.  Needs the saw: say if that is not wanted.
//   shaft_top = 18.0  the shaft as it comes: the same knobs, 6 mm taller (the *_uncut.stl files).
shaft_top  = 12.0;
bore_dp    = shaft_top - z_ceil + 0.3;     // bore depth from the pocket ceiling: clears the shaft's end by 0.3

// ---- set screw -----------------------------------------------------------------------------------
m3_insert_d = 4.0;   // hole for an M3 heat-set insert, OD about 4.6 (inferred: check the insert's data sheet)
m3_tap_d    = 2.5;   // tap drill for M3 (turned)

$fn = 96;
eps = 0.01;

function lobe_r(t, Rc, dep, n) = Rc - dep * (1 - cos(n * t)) / 2;

// ================================================================== A: the РСИ reading
A_n     = 8;          // lobes (the photo shows 8 or 9)
A_dep   = 0.9;        // lobe depth, crest to trough
A_top   = z_ceil + bore_dp + 2.0;   // top of the lobed rim above the face
A_bore  = bore_dp;
A_ring_od = 14.4;     // the flat ring's outer edge: leaves a 0.9 rim band at the trough
A_cap_d = 8.4;        // raised centre cap
A_ring_dp = 0.8;      // ring floor below the rim top
A_cap_dn  = 0.3;      // cap top below the rim top
A_screw_z = z_ceil + 3.2;

module lobed(h, inset = 0) {
    N = 288;
    linear_extrude(h) offset(delta = -inset)
        polygon([for (i = [0:N - 1]) let (t = 360 * i / N) lobe_r(t, D / 2, A_dep, A_n) * [cos(t), sin(t)]]);
}

module A_body() {
    // 0.45 mm stepped chamfer at the rim, 0.6 mm stepped round on top
    steps_b = 3;
    for (i = [0:steps_b - 1])
        translate([0, 0, z_rim + i * 0.15]) lobed(0.16, 0.45 * (1 - i / steps_b));
    translate([0, 0, z_rim + steps_b * 0.15]) lobed(A_top - z_rim - steps_b * 0.15 - 0.6);
    steps_t = 4;
    for (i = [0:steps_t - 1])
        translate([0, 0, A_top - 0.6 + i * 0.15]) lobed(0.16, 0.6 * pow(i / steps_t, 2));
}

module A_marks() {
    rz = A_top - A_ring_dp;
    // pointer: a groove across the rim band, from the ring to the outside
    rotate([0, 0, ang]) translate([A_ring_od / 2 - 0.3, -0.45, A_top - 0.45]) cube([D / 2 - A_ring_od / 2 + 1.5, 0.9, 1]);
    // pointer dot in the ring
    rotate([0, 0, ang]) translate([(A_cap_d + A_ring_od) / 4, 0, rz - 0.4]) cylinder(h = 1, d = 1.4, $fn = 32);
    // curved arrow on the cap, clockwise, its head near the pointer
    translate([0, 0, A_top - A_cap_dn - 0.3]) linear_extrude(1) rotate(ang) arrow2d(2.8, 0.5, 215, -25);
}

// 2D curved arrow: an arc of radius r and width w from angle a0 to a1 (clockwise when a1 < a0), head at a1
module arrow2d(r, w, a0, a1) {
    n = 40;
    s = (a1 - a0) / n;
    pts_o = [for (i = [0:n]) (r + w / 2) * [cos(a0 + i * s), sin(a0 + i * s)]];
    pts_i = [for (i = [n:-1:0]) (r - w / 2) * [cos(a0 + i * s), sin(a0 + i * s)]];
    polygon(concat(pts_o, pts_i));
    // head: a triangle at a1, pointing along the travel
    dir = sign(a1 - a0);
    ha = a1 + dir * 22;
    polygon([r * [cos(ha), sin(ha)], (r + 0.95) * [cos(a1), sin(a1)], (r - 0.95) * [cos(a1), sin(a1)]]);
}

module knob_A_solid() {
    difference() {
        A_body();
        // ring pocket, then the cap's top trimmed
        translate([0, 0, A_top - A_ring_dp]) difference() {
            cylinder(h = 5, d = A_ring_od);
            translate([0, 0, -1]) cylinder(h = 7, d = A_cap_d);
        }
        translate([0, 0, A_top - A_cap_dn]) cylinder(h = 5, d = A_cap_d + 0.2);
        // nut pocket, bore, M3 insert hole opposite the pointer
        translate([0, 0, z_rim - 1]) cylinder(h = z_ceil - z_rim + 1, d = recess_d);
        translate([0, 0, z_ceil - eps]) cylinder(h = A_bore + eps, d = bore_set);
        rotate([0, 0, ang + 180]) translate([1.5, 0, A_screw_z]) rotate([0, 90, 0]) cylinder(h = 12, d = m3_insert_d, $fn = 40);
        A_marks();
    }
}

// ================================================================== B: the chicken-head
B_hub_d  = 11.0;
B_tail_d = 8.0;  B_tail_x = -3.2;       // tail bulge behind the shaft, carries the insert
B_tip_w  = 1.8;
B_z0     = z_ceil;                      // no pocket: the underside is flat, above the nut and R's bushing end
B_ztop   = z_ceil + bore_dp + 2.0;   // flat top over the shaft
B_x_slope0 = 3.0;                       // the beak starts to fall here
B_z_tip  = 9.5;                         // beak's upper face at the tip
B_bore   = bore_dp;
B_screw_z = B_z0 + 3.5;

module B_plan() {
    hull() { circle(d = B_hub_d); translate([D / 2 - B_tip_w / 2, 0]) circle(d = B_tip_w, $fn = 40); }
    hull() { circle(d = B_hub_d); translate([B_tail_x, 0]) circle(d = B_tail_d); }
}
function B_prof(dz) = [[-30, B_ztop + dz], [B_x_slope0, B_ztop + dz],
                       [D / 2 + 1, B_ztop - (B_ztop - B_z_tip) * (D / 2 + 1 - B_x_slope0) / (D / 2 - B_x_slope0) + dz],
                       [D / 2 + 1, B_z0 - 1], [-30, B_z0 - 1]];
module B_under(dz, w) rotate([90, 0, 0]) linear_extrude(w, center = true) polygon(B_prof(dz));

module B_marks() {
    // a line along the beak's upper face, from over the shaft to the tip
    intersection() {
        difference() { B_under(1, 0.7); B_under(-0.35, 1); }
        translate([-4, -2, 0]) cube([30, 4, 40]);
    }
}

module knob_B_solid() {
    difference() {
        intersection() {
            translate([0, 0, B_z0]) linear_extrude(20) B_plan();
            B_under(0, 40);
        }
        translate([0, 0, B_z0 - eps]) cylinder(h = B_bore + eps, d = bore_set);
        // M3 insert hole into the tail, along -x
        translate([-3.0, 0, B_screw_z]) rotate([0, -90, 0]) cylinder(h = 7, d = m3_insert_d, $fn = 40);
        B_marks();
    }
}

// ================================================================== C: the turned instrument knob
C_skirt_top = 6.8;      // the skirt's top face: the pointer plane
C_grip_d    = 14.0;
C_top       = z_ceil + bore_dp + 2.0;
C_knurl_n   = 44;
C_bore      = bore_dp;
C_screw_z   = z_ceil + 3.5;
C_line_w    = 0.8;      // pointer line width, cut through the anodise
C_line_dp   = 0.4;

module C_profile() {
    r = D / 2; g = C_grip_d / 2;
    polygon([[0, z_rim], [r - 0.3, z_rim], [r, z_rim + 0.3], [r, C_skirt_top - 0.4], [r - 0.4, C_skirt_top],
             [g + 0.3, C_skirt_top], [g, C_skirt_top + 0.3], [g, C_top - 0.8], [g - 0.8, C_top], [0, C_top]]);
}

module C_knurl_cut() {
    g = C_grip_d / 2;
    for (i = [0:C_knurl_n - 1])
        rotate([0, 0, i * 360 / C_knurl_n]) translate([0, 0, C_skirt_top + 0.9])
            linear_extrude(C_top - C_skirt_top - 0.9 - 1.1)
                polygon([[g + 0.05, -0.24], [g - 0.35, 0], [g + 0.05, 0.24]]);
}

module C_marks() {
    g = C_grip_d / 2;
    rotate([0, 0, ang]) {
        // top of the grip, centre to the edge
        translate([0, -C_line_w / 2, C_top - C_line_dp]) cube([g, C_line_w, 2]);
        // down the flank
        translate([g - C_line_dp, -C_line_w / 2, C_skirt_top - C_line_dp]) cube([C_line_dp + 1.2, C_line_w, C_top - C_skirt_top + 1]);
        // across the skirt and over its rim
        translate([g - 0.4, -C_line_w / 2, C_skirt_top - C_line_dp]) cube([D / 2 - g + 1, C_line_w, 2]);
    }
}

module knob_C_solid() {
    difference() {
        rotate_extrude() C_profile();
        translate([0, 0, z_rim - 1]) cylinder(h = z_ceil - z_rim + 1, d = recess_d);
        translate([0, 0, z_ceil - eps]) cylinder(h = C_bore + eps, d = bore_turn);
        rotate([0, 0, ang + 180]) translate([2, 0, C_screw_z]) rotate([0, 90, 0]) cylinder(h = 8, d = m3_tap_d, $fn = 32);
        C_knurl_cut();
        C_marks();
    }
}

// ================================================================== the marks' fill, pictures, orientation
// The fill is what a filled engraving would be: the marks cut out of the body's own envelope. It is built here in
// CGAL (part "X_fill"), exported to build/, and the pictures draw it in colour on top of the cut body.
module A_fill() { intersection() { A_marks(); A_body(); } }
module B_envelope() { intersection() { translate([0, 0, B_z0]) linear_extrude(20) B_plan(); B_under(0, 40); } }
module B_fill()  { intersection() { B_marks(); B_envelope(); } }
module C_fill()  { intersection() { C_marks(); rotate_extrude() C_profile(); } }

module placed(h_top) {
    if (flip == 1) translate([0, 0, h_top]) rotate([180, 0, 0]) children();
    else children();
}

// picture: the cut body (dark) and its fill (gold, cream or bare aluminium) from build/*.stl
module pic(k) {
    color([0.20, 0.20, 0.23]) import(str("build/knob_", k, ".stl"));
    c = k == "C" ? [0.88, 0.89, 0.91] : (fillc == "cream" ? [0.95, 0.90, 0.72] : [0.92, 0.72, 0.22]);
    color(c) import(str("build/knob_", k, "_fill.stl"));
}

// a schematic cross-section on the stack, FRONT UP, for the three knobs: plate, washer, nut, bushing, shaft, knob.
// Export the three knob STLs with ang = 0 to build/section_X.stl first, then render part "section".
module sx(x0, x1, z0, z1) translate([x0, z0]) square([x1 - x0, z1 - z0]);
module slab(c) { color(c) rotate([90, 0, 0]) linear_extrude(0.6, center = true) children(); }
module section_stack(ox, lift, k) {
    washer_t = 0.8; nut_t = 2.0; washer_d = 14.0;     // placeholders (inferred): MEASURE
    s_top = 7.0 - 2.0 - lift;                          // bushing end above the face: 5.0 R, 4.0 T
    shaft_end = shaft_top;                             // sawn to this above the face (18.0 if it is left uncut)
    translate([ox, 0, 0]) {
        slab([0.25, 0.55, 0.85]) { sx(-14, -4.31, -2, 0); sx(4.31, 14, -2, 0); }                      // the fascia, 2.0
        slab([0.55, 0.58, 0.62]) sx(-12.5, 12.5, -2 - lift - 11.3, -2 - lift);                        // SR25 body behind it
        slab([0.78, 0.80, 0.84]) sx(-4.31, 4.31, -2 - lift, s_top);                                   // bushing
        slab([0.90, 0.90, 0.93]) sx(-3, 3, s_top, shaft_end);                                         // shaft
        slab([0.95, 0.75, 0.25]) { sx(-washer_d / 2, -4.31, 0, washer_t); sx(4.31, washer_d / 2, 0, washer_t); }
        slab([0.95, 0.50, 0.20]) { sx(-nut_af / 2, -4.31, washer_t, washer_t + nut_t); sx(4.31, nut_af / 2, washer_t, washer_t + nut_t); }
        // the knob: its cut in the y = 0 plane
        color([0.12, 0.12, 0.14]) rotate([90, 0, 0]) linear_extrude(0.9, center = true)
            projection(cut = true) rotate([-90, 0, 0]) import(str("build/section_", k, ".stl"));
    }
}
module section_pic() {
    section_stack(-30, 0, "A");      // lift 0: R
    section_stack(0, 0, "B");
    section_stack(30, 0, "C");
    // reference heights above the fascia face, as thin lines across all three
    for (h = [[z_rim, [0.85, 0.1, 0.1]], [washer_nut_top, [0.95, 0.5, 0.2]], [5.0, [0.2, 0.2, 0.2]], [z_ceil, [0.1, 0.5, 0.1]]])
        color(h[1]) translate([-46, 0.6, h[0] - 0.03]) cube([92, 0.2, 0.06]);
    color("black") rotate([90, 0, 0]) linear_extrude(0.5, center = true) {
        translate([-30 - 9, -9]) text("A", size = 3);
        translate([0 - 9, -9]) text("B", size = 3);
        translate([30 - 9, -9]) text("C", size = 3);
        translate([46.5, 0.4]) text("red 2.6 knob rim", size = 1.5);
        translate([46.5, 2.2]) text("orange 2.8 nut top (placeholder)", size = 1.5);
        translate([46.5, 4.0]) text("black 5.0 bushing end (R)", size = 1.5);
        translate([46.5, 5.8]) text("green 5.5 pocket ceiling", size = 1.5);
        translate([46.5, shaft_top - 0.5]) text(str(shaft_top, " shaft end"), size = 1.4);
    }
}
washer_nut_top = 2.8;

if (part == "A") placed(A_top) knob_A_solid();
else if (part == "B") placed(B_ztop) knob_B_solid();
else if (part == "C") placed(C_top) knob_C_solid();
else if (part == "A_fill") A_fill();
else if (part == "B_fill") B_fill();
else if (part == "C_fill") C_fill();
else if (part == "picA") pic("A");
else if (part == "picB") pic("B");
else if (part == "picC") pic("C");
else if (part == "section") section_pic();
else if (part == "calib") color("red") cylinder(h = 1, d = 20);

