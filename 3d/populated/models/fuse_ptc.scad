// Radial PTC fuse (F1), the outline of the Bourns MF-RG1100 footprint. Made for 3d/populated: the KiCad model
// Fuse.3dshapes/Fuse_Bourns_MF-RG1100.step is not on this machine.
//
// layers: body=#d8a31f leads=#c9c9c9
//
// FRAME  KiCad model frame. Pad 1 at (0, 0), pad 2 at (5.1, -1.2) (footprint y +1.2 negated).
//
// DIMENSIONS                       value            kind
//   body width x thickness    17.5 x 3.0 mm      MEASURED (repo source): TS06_Fuse_PTC_MF-RG1100.kicad_mod F.Fab rectangle
//                                                (x -6.2..11.3, y -0.9..2.1), centred between the pads
//   body height               13.0 mm            INFERRED: case_pair.py FP_H "radial PTC" 13.0 (assumed there); the stock
//                                                footprint states none. PCB/TS06-DRV/bom.md notes the real fitted part is a
//                                                smaller MF-R110; the 11 A outline is drawn because it is the footprint
//   lift off the board        1.0 mm             INFERRED
//   leads D1.0 (pad drill 1.01)                  MEASURED (footprint pads: D2.01, drill 1.01); 2.5 mm through the board INFERRED
L = "body";
W = 17.5;
T = 3.0;
H = 13.0;
LIFT = 1.0;
cx = 2.55;
cy = -0.6;

if (L == "body") translate([cx, cy, LIFT])
    hull() {
        translate([-W / 2, -T / 2, 0]) cube([W, T, H * 0.6]);
        translate([-W / 2 + 1.8, -T / 2, 0]) cube([W - 3.6, T, H]);
    }
if (L == "leads") {
    translate([0, 0, -2.5]) cylinder(d = 1.0, h = 2.5 + LIFT + 0.5, $fn = 12);
    translate([5.1, -1.2, -2.5]) cylinder(d = 1.0, h = 2.5 + LIFT + 0.5, $fn = 12);
}
