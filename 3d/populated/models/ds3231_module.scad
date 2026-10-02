// DS3231 "mini" RTC module (U13), lying over TS06-DRV on its female header, which plugs on the 5-way PLS male header
// of the footprint. Made for 3d/populated. The male header itself is KiCad's PinHeader_1x05 model (models3d.json).
//
// layers: socket=#1d1d1f pcb=#1c4f9c ic=#202022 gold=#d1ad45 cap=#b99a5a
//
// FRAME  KiCad model frame of the base footprint TS06_PinHeader_1x05_DS3231 (pads along -y from (0, 0), a footprint's y
//        negated); the board's U13 is the _R270 copy and gets there through tools/models3d.py's variant rule.
//
// DIMENSIONS                            value                   kind
//   module footprint on the board      x -0.7..16.8, y 1.92..-12.08 (17.5 x 14.0)   MEASURED (repo source): the footprint's F.Fab /
//                                                     F.SilkS rectangle (x 1.27..16.8, y -1.92..12.08 in footprint y) plus 2.0 mm
//                                                     back to the header axis; the descr says "~14 x 16 mm"
//   female socket      2.54 x 12.7 x 8.5            INFERRED: a 5-way 2.54 mm socket (PCB/TS06-DRV/bom.md: PBS 8.5 mm)
//   seat               socket bottom on the PLS body top, 2.54 mm   INFERRED (case_pair.py PLS_BODY 2.5)
//   PCB thickness      1.2 mm                      INFERRED
//   DS3231 SOIC-16W    10.3 x 7.5 x 2.65           INFERRED (datasheet package outline, typical)
//   EEPROM SOIC-8      5.0 x 4.0 x 1.75            INFERRED
//   overall height     14.8 mm above the board face    DERIVED; the footprint descr says "~15 mm tall", case_pair.py FP_H 22.0 for
//                                                     the older standing-module reading (see checks.md finding 6)
L = "pcb";
P = 2.54;
SOC_Z = 2.54;
SOC_H = 8.5;
PCB_Z = SOC_Z + SOC_H;          // 11.04
PCB_T = 1.2;
X0 = -0.7;
X1 = 16.8;
Y0 = 1.92;                      // model y of the +y edge
Y1 = -12.08;

if (L == "socket") translate([-1.27, -4 * P - 1.27, SOC_Z]) cube([2.54, 5 * P, SOC_H]);
if (L == "pcb") translate([X0, Y1, PCB_Z]) cube([X1 - X0, Y0 - Y1, PCB_T]);
if (L == "ic") {
    translate([5.0, -5.08 - 3.75, PCB_Z + PCB_T]) cube([10.3, 7.5, 2.65]);        // DS3231
    translate([14.2, -5.08 + 6.0, PCB_Z + PCB_T]) cube([2.0, 4.0, 1.0]);          // a passive row
    translate([2.2, -5.08 - 2.5, PCB_Z + PCB_T]) cube([2.5, 5.0, 1.75]);          // EEPROM, rotated
}
if (L == "gold") for (i = [0 : 4]) translate([0, -i * P, PCB_Z + PCB_T + 0.01]) cylinder(d = 1.6, h = 0.05, $fn = 18);
if (L == "cap") translate([8.0, -5.08 + 5.5, PCB_Z + PCB_T]) cube([3.2, 1.6, 1.0]);
