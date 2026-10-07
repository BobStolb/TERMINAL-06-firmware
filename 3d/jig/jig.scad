// TS06 fascia T dry-fit jig (OpenSCAD 2021.01).
//
// What it tests: the SR25 rotary's plate rests on the dial's solder joints on fascia T, lifting
// it by about 1 mm, and the bushing then shows less thread above the fascia for washer + nut.
// The jig is a 2.0 mm "fascia" with the dial's bushing hole, the joints as bumps on its BACK, a
// set of shims, and a lead former. See README.md in this folder for the bench steps.
//
// Frame (as printed): z = 0 is the FRONT face of the plate (print it face down on the bed),
// z = 2.0 the back face, bumps and the SR25 go up from there. x and y are the model's own: the
// top view of the model is the BACK of the fascia, so front-view x is mirrored (fpos() does it).
//
//   openscad -D 'part="plate"' -D 'bumps=1' -o jig_plate_L1.stl jig.scad
//   parts: plate | shims | former | set | assembly   (bumps: 0 none, 1 layout 1, 2 layout 2)
//
// Values marked (inferred) are typical figures, not a measurement of the SR25 or of any printer.

part  = "set";
bumps = 1;          // 0 flat plate, 1 first plan's joints (r 10.6 / 12.0), 2 in-line layout on r_l2

// ---- the fascia, as ordered (R) -------------------------------------------------------------
plate_t     = 2.0;      // fascia thickness (fab/ORDER.md)
plate_d     = 38;       // jig plate diameter: holds layout 2's joints out to r 16 and a finger grip
bush_hole   = 9.2;      // R's dial hole (fab/HOLES-VARIANT.md); the bushing is 8.62
hole_comp   = 0.2;      // print compensation for a 0.4 mm nozzle, vertical hole (inferred): model = 9.4
elephant    = 0.3;      // 45 degree chamfer on the front edge of the hole against first-layer squash

// ---- the SR25 (3d/SR25.FCStd; the model has no tab, no flat, no knurl) -----------------------
sr_plate_d  = 25.0;     // body / wafer diameter (the "25 mm plate")
sr_body_h   = 11.3;
sr_bush_d   = 8.62;
sr_bush_len = 7.00;     // usable
sr_shaft_d  = 6.00;
sr_shaft_len= 13.0;     // beyond the bushing, as modelled

// ---- anti-turn tab (none is known: footprints and STEP carry none; measure the real part) ----
tab_mode = 0;           // 0 none, 1 hole, 2 notch in the hole's rim
tab_r    = 6.0;         // radius of a tab hole from the shaft (MEASURE)
tab_ang  = 90;          // direction in the model's plan view, degrees (MEASURE)
tab_d    = 2.0;         // hole diameter, or notch width (MEASURE)

// ---- the joints -------------------------------------------------------------------------------
joint_h = 1.0;          // height of a hand-soldered joint above the back face (inferred)
pad_d   = 1.9;          // the plan's pad
r_in    = 10.6;         // layout 1: the two holes of a tap (plan section 3)
r_out   = 12.0;
tap_step= 30;           // degrees between taps (spec: 12 detents, 30.00)
tap_a0  = 75;           // tap 1's direction in the FRONT view (y up), tap 6 is at -75
r_l2    = 15.0;         // layout 2: the in-line circle's radius. PLACEHOLDER: the concepts run gives the number
l2_pair = 2;            // 2 = two holes per tap, 1 = one shared hole
l2_sep  = 1.4;          // distance between a tap's two holes, along the tangent (as layout 1's stagger)

// ---- shims and former -------------------------------------------------------------------------
shim_t  = 0.5;          // three of these stack to 0.5 / 1.0 / 1.5
shim_id = 10.0;
shim_n  = 3;
spans_fixed = [6.0, 9.0, 7.62, 10.16];  // plan dial span, plan ladder span, 0207 tight, 0207 normal
fixed_labels = ["6.0", "9.0", "7.62", "10.16"];  // the fifth slot is layout 2's span, computed
lead_d  = 0.5;          // 0204 lead wire (plan)
slit_w  = 0.9;          // lead slit width (0.5 wire + 0.4 play)
slit_l  = 3.2;
slit_h  = 5.0;
former_h= 6.5;
body_w  = 2.8;          // cradle for either body (0207 is 2.5 wide)

// ---- ghost parts for the assembly picture (placeholders, measure with the caliper) -----------
nut_t   = 2.0;  nut_af = 10.0;  washer_t = 0.8;  washer_d = 14.0;   // all inferred
lift    = 1.0;                  // plate lift on layout 1 (joint_h); 0 for layout 2

$fn = 72;
eps = 0.01;

function hole_d() = bush_hole + hole_comp;
function l2_chord() = 2 * r_l2 * sin(tap_step / 2);
function l2_span()  = l2_chord() - (l2_pair == 2 ? l2_sep : 0);

// a point given in the FRONT view (r, angle, tangential offset) in the model's frame
module fpos(r, a, dt = 0) {
    xf = r * cos(a) - dt * sin(a);
    yf = r * sin(a) + dt * cos(a);
    translate([-xf, yf, 0]) children();
}

// layout 1 joint list: tap 1 outer only, taps 2-5 both, tap 6 inner only (the plan)
module joints_l1() {
    for (k = [0:5]) {
        a = tap_a0 - tap_step * k;
        if (k < 5) fpos(r_out, a) children();
        if (k > 0) fpos(r_in, a) children();
    }
}
module joints_l2() {
    for (k = [0:5]) {
        a = tap_a0 - tap_step * k;
        if (l2_pair == 1 || k == 0 || k == 5) fpos(r_l2, a) children();
        else for (s = [-1, 1]) fpos(r_l2, a, s * l2_sep / 2) children();
    }
}

module bump() {
    translate([0, 0, plate_t - eps]) cylinder(h = joint_h + eps, d1 = pad_d, d2 = pad_d - 0.8);
}

module hole_cut() {
    translate([0, 0, -1]) cylinder(h = plate_t + 2, d = hole_d());
    // chamfer on the front edge
    translate([0, 0, -eps]) cylinder(h = elephant + eps, d1 = hole_d() + 2 * elephant, d2 = hole_d());
    if (tab_mode == 1)
        translate([tab_r * cos(tab_ang), tab_r * sin(tab_ang), -1]) cylinder(h = plate_t + 2, d = tab_d + hole_comp);
    if (tab_mode == 2)
        rotate([0, 0, tab_ang]) translate([0, -(tab_d + hole_comp) / 2, -1])
            cube([hole_d() / 2 + tab_d, tab_d + hole_comp, plate_t + 2]);
}

// marks cut 0.3 deep into the FRONT face: the SR25's 25 mm edge, the shaft cross, both layouts' joints
module front_marks() {
    d = 0.3;
    translate([0, 0, -eps]) linear_extrude(d + eps) {
        difference() { circle(d = sr_plate_d + 0.5); circle(d = sr_plate_d - 0.1); }          // 25 mm edge, 0.3 wide
        // layout 1 joints: rings
        projection_joints_l1();
        // layout 2 joints: small squares
        projection_joints_l2();
    }
}
module projection_joints_l1() {
    joints_l1() difference() { circle(d = pad_d); circle(d = pad_d - 0.6); }
}
module projection_joints_l2() {
    joints_l2() square(pad_d - 0.5, center = true);
}

module plate(b = bumps) {
    difference() {
        union() {
            cylinder(h = plate_t, d = plate_d);
            if (b == 1) joints_l1() bump();
            if (b == 2) joints_l2() bump();
        }
        hole_cut();
        front_marks();
        // a label cut into the front face (mirrored, so it reads from the front)
        translate([0, -plate_d / 2 + 4.5, -eps]) mirror([1, 0, 0]) linear_extrude(0.4 + eps)
            text(b == 0 ? "FLAT" : (b == 1 ? "L1" : "L2"), size = 3, halign = "center", valign = "center");
    }
}

module shims() {
    for (i = [0:shim_n - 1])
        translate([(i - (shim_n - 1) / 2) * (sr_plate_d + 3), 0, 0])
            difference() { cylinder(h = shim_t, d = sr_plate_d); translate([0, 0, -1]) cylinder(h = shim_t + 2, d = shim_id); }
}

module former() {
    spans = concat(spans_fixed, [l2_span()]);
    n = len(spans);
    pitch = 5.2;
    w = n * pitch + 3;
    len_x = max(spans) + 2 * 4;
    difference() {
        translate([-len_x / 2, 0, 0]) cube([len_x, w, former_h]);
        for (i = [0:n - 1]) {
            y = 2.6 + 1.5 + i * pitch;
            s = spans[i];
            for (sx = [-1, 1]) translate([sx * s / 2 - slit_w / 2, y - slit_l / 2, former_h - slit_h]) cube([slit_w, slit_l, slit_h + 1]);
            // body cradle between the slits
            translate([-s / 2, y - body_w / 2, former_h - 1.0]) cube([s, body_w, 2]);
            // span label on the top face beside the cradle, cut 0.4 deep
            translate([-len_x / 2 + 0.9, y + 1.6, former_h - 0.4]) linear_extrude(1)
                text(i < len(spans_fixed) ? fixed_labels[i] : str(round(s * 100) / 100), size = 1.5, halign = "left", valign = "bottom");
        }
    }
}

// the print set: plate with the chosen bumps, the shims, the former, laid out on one 180 x 80 bed area
module print_set() {
    plate();
    // three shim rings in a column to the right of the plate
    for (i = [0:shim_n - 1])
        translate([plate_d / 2 + 4 + sr_plate_d / 2, (i - (shim_n - 1) / 2) * (sr_plate_d + 3), 0])
            difference() { cylinder(h = shim_t, d = sr_plate_d); translate([0, 0, -1]) cylinder(h = shim_t + 2, d = shim_id); }
    // the former below the plate
    translate([0, -plate_d / 2 - 4 - (len(spans_fixed) + 1) * 5.2 - 3, 0]) former();
}

// ---- the assembly picture: plate on its back-up bumps, SR25 ghost resting on them, nut on the front
module ghost_sr25(zb) {
    // zb = z of the SR25's plate face (the face against the bumps / shims)
    color([0.55, 0.58, 0.62, 0.55]) translate([0, 0, zb]) cylinder(h = sr_body_h, d = sr_plate_d);
    color([0.75, 0.78, 0.80, 1.0]) translate([0, 0, zb - sr_bush_len]) cylinder(h = sr_bush_len + eps, d = sr_bush_d);
    color([0.85, 0.85, 0.88, 1.0]) translate([0, 0, zb - sr_bush_len - sr_shaft_len]) cylinder(h = sr_shaft_len + eps, d = sr_shaft_d);
}
module ghost_stack() {
    color([0.9, 0.7, 0.2, 1.0]) translate([0, 0, -washer_t]) difference() { cylinder(h = washer_t, d = washer_d); translate([0, 0, -1]) cylinder(h = 3, d = sr_bush_d); }
    color([0.9, 0.5, 0.2, 1.0]) translate([0, 0, -washer_t - nut_t]) difference() { cylinder(h = nut_t, d = nut_af / cos(30), $fn = 6); translate([0, 0, -1]) cylinder(h = 4, d = sr_bush_d); }
}
// ---- a schematic cross-section, FRONT UP: the plate, the joints under it, the SR25 on them, the stack on the front
// z = 0 is the front face. lift = how far the SR25's plate stands off the back (0 on R, the joint height on T).
module sx(x0, x1, z0, z1) translate([x0, z0]) square([x1 - x0, z1 - z0]);
module slab(c) { color(c) rotate([90, 0, 0]) linear_extrude(0.6, center = true) children(); }

module section_one(lift, ox, label) {
    s_top = sr_bush_len - plate_t - lift;          // bushing's end above the front face: 5.0 on R, 4.0 on T
    stack = washer_t + nut_t;
    translate([ox, 0, 0]) {
        // the plate, with the 9.2 hole
        slab([0.25, 0.55, 0.85]) { sx(-plate_d / 2, -bush_hole / 2, -plate_t, 0); sx(bush_hole / 2, plate_d / 2, -plate_t, 0); }
        // joints under the plate (layout 1: r 10.6 and r 12.0 on one side), only when lifted
        if (lift > 0) slab([0.85, 0.35, 0.15]) for (r = [r_in, r_out]) translate([r, -plate_t - lift / 2]) square([pad_d, lift + 0.02], center = true);
        // SR25 body, bushing, shaft
        slab([0.55, 0.58, 0.62]) sx(-sr_plate_d / 2, sr_plate_d / 2, -plate_t - lift - sr_body_h, -plate_t - lift);
        slab([0.78, 0.80, 0.84]) sx(-sr_bush_d / 2, sr_bush_d / 2, -plate_t - lift, s_top);
        slab([0.90, 0.90, 0.93]) sx(-sr_shaft_d / 2, sr_shaft_d / 2, s_top, s_top + sr_shaft_len);
        // washer and nut on the front
        slab([0.95, 0.75, 0.25]) { sx(-washer_d / 2, -sr_bush_d / 2, 0, washer_t); sx(sr_bush_d / 2, washer_d / 2, 0, washer_t); }
        slab([0.95, 0.50, 0.20]) { sx(-nut_af / 2, -sr_bush_d / 2, washer_t, stack); sx(sr_bush_d / 2, nut_af / 2, washer_t, stack); }
        // the thread left above the nut: a red bar beside the bushing, and the label
        slab([0.85, 0.10, 0.10]) sx(sr_bush_d / 2 + 0.3, sr_bush_d / 2 + 0.9, stack, s_top);
        translate([0, 0, 0]) color("black") rotate([90, 0, 0]) linear_extrude(0.7, center = true) {
            translate([-sr_plate_d / 2, s_top + sr_shaft_len + 2.5]) text(label, size = 2.2);
            translate([sr_bush_d / 2 + 1.5, (stack + s_top) / 2 - 0.9]) text(str(s_top - stack), size = 1.8);
        }
    }
}
module section_pair() {
    section_one(0, -24, "R: no joints");
    section_one(joint_h, 24, "T: joints 1.0 under the plate");
}

module assembly() {
    zb = plate_t + (bumps == 0 ? 0 : (bumps == 1 ? joint_h : 0));
    difference() {                                         // section: cut away y < 0
        union() {
            color([0.20, 0.45, 0.75]) plate();
            ghost_sr25(zb);
            ghost_stack();
        }
        translate([-60, -120, -60]) cube([120, 120, 140]);
    }
}

// both plates side by side, the SR25's 25 mm edge drawn as a thin red ring on the back, for the picture
module compare() {
    for (i = [0, 1]) translate([(i == 0 ? -1 : 1) * (plate_d / 2 + 2), 0, 0]) {
        plate(i + 1);
        color("red") translate([0, 0, plate_t + joint_h + 0.05]) difference() { cylinder(h = 0.15, d = sr_plate_d + 0.3); translate([0, 0, -1]) cylinder(h = 2, d = sr_plate_d - 0.3); }
    }
}

if (part == "plate") plate();
else if (part == "compare") compare();
else if (part == "section") section_pair();
else if (part == "shims") shims();
else if (part == "former") former();
else if (part == "assembly") assembly();
else print_set();
