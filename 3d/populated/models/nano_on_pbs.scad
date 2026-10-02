// Arduino Nano (U1) plugged into two 15-way PBS socket strips. Made for 3d/populated: the KiCad model
// Module.3dshapes/Arduino_Nano_WithMountingHoles.step is not on this machine, which is why the board's own
// footprint draws only the Nano's outline.
//
// layers: strip=#1b1b1d pcb=#12508a chip=#1e1e20 steel=#c4c8cc gold=#d1ad45 tact=#2c2c2e pins=#c9c9c9
//
// FRAME  KiCad model frame of the base footprint TS06_Arduino_Nano: pin 1 at (0, 0), column 1 down the page
//        (model y 0 .. -35.56), column 2 at x 15.24; the USB end is the pin-15 end, model -y. The board's U1 is the _R90 copy and gets there
//        through tools/models3d.py's variant rule.
//
// DIMENSIONS                          value                        kind
//   pin rows / pitch               15.24 x 2.54 mm, 15 pins each     MEASURED (repo source): TS06_Arduino_Nano.kicad_mod pads
//   Nano PCB                        17.78 x 43.18 x 1.6 mm           MEASURED (repo source): the footprint's F.Fab outline (x -1.27..16.51,
//                                                                    y -3.81..39.37 in footprint y, so pin 1 is 3.81 from the far end and
//                                                                    the last pin 3.81 from the USB end); thickness case_pair.py NANO_PCB_T 1.6 (assumed there)
//   USB end                         the +y_fp end (pads 15/16): the footprint's F.Fab shell rectangle is x 3.81..11.43, y 31.75..41.91,
//                                                                    which overhangs the PCB end (39.37) by 2.54       MEASURED (same file)
//   PBS strips                      2.54 x 38.1 x 8.5 mm            MEASURED (repo source): PCB/TS06-DRV/bom.md, "Socket strip PBS-15, 8.5 mm"
//   male header body under the Nano 2.5 mm                           MEASURED (repo source): case_pair.py PLS_BODY 2.5 (PCB/TS06-DISP/bom.md "8.5 PBS + 2.5 PLS body")
//   mini-B receptacle height        4.0 mm                           INFERRED: case_pair.py USB_H (assumed there); width and length are the footprint's 7.62 x 10.16
//   ATmega328P TQFP-32 7 x 7 x 1.0; USB-UART SOIC-16 10 x 4 x 1.6; reset switch 3.5 x 6 x 2.5   INFERRED (typical, positions approximate)
//   overall height                  16.6 mm above the board face     DERIVED: 8.5 + 2.5 + 1.6 + 4.0; matches case_pair.py NANO_H
//   not drawn: the ICSP header (the pads are shown unpopulated, as most Nanos ship), crystal, regulator, LEDs, mounting holes
L = "strip";
P = 2.54;
STRIP_H = 8.5;
PLS_H = 2.5;
PCB_Z = STRIP_H + PLS_H;            // 11.0
PCB_T = 1.6;
TOP = PCB_Z + PCB_T;                // 12.6

module strip(x) translate([x - 1.27, -35.56 - 1.27, 0]) cube([2.54, 15 * P, STRIP_H]);
module plsbody(x) translate([x - 1.27, -35.56 - 1.27, STRIP_H]) cube([2.54, 15 * P, PLS_H]);

if (L == "strip") { strip(0); strip(15.24); plsbody(0); plsbody(15.24); }
// PCB: footprint y -3.81..39.37 -> model y +3.81..-39.37
if (L == "pcb") translate([-1.27, -39.37, PCB_Z]) cube([17.78, 39.37 + 3.81, PCB_T]);
// mini-B shell: footprint x 3.81..11.43, y 31.75..41.91 -> model y -41.91..-31.75
if (L == "steel") translate([3.81, -41.91, TOP]) cube([7.62, 10.16, 4.0]);
if (L == "chip") {
    translate([7.62 - 3.5, -12.0 - 3.5, TOP]) cube([7, 7, 1.0]);                    // ATmega328P, TQFP-32
    translate([7.62 - 2.0, -27.0 - 5.0, TOP]) cube([4, 10, 1.6]);                   // USB-UART, SOIC-16
}
if (L == "tact") translate([7.62 - 1.75, -20.5 - 3.0, TOP]) cube([3.5, 6, 2.5]);   // reset switch
// ICSP pads, unpopulated: 2 x 3 at 2.54 pitch near the far end
if (L == "gold") for (i = [0 : 2], j = [0 : 1]) translate([6.35 + j * 2.54, 0.2 - i * 2.54, TOP + 0.01]) cylinder(d = 1.7, h = 0.04, $fn = 16);
if (L == "pins") for (x = [0, 15.24], i = [0 : 14]) translate([x, -i * P, -2.9]) cylinder(d = 0.65, h = 2.9 + 1.0, $fn = 10);
