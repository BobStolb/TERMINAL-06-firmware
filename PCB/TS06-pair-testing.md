# TS06-DISP + TS06-DRV: how to view the boards and test everything

This guide covers the through-hole pair and the fascia cable. It has three parts:

* **A. Viewing.** How to open the boards in KiCad 10 and the case in OpenSCAD.
* **B. Automated checks.** One command, `tools/verify_pair.sh`, runs every check the repository has on the pair.
* **C. Bench bring-up.** Eight stages, from bare boards to a 24-hour soak. Each stage gives the expected value, calculated from the netlist.

The netlist and every part value come from `tools/ts06pair.py`. Board positions come from `tools/mkpcb_disp.py` and `tools/mkpcb_drv.py`. The design decisions are in `PCB/README.md` and `Claude outputs/TS06-pair-review.md`.

---

## A. Viewing the boards

### A1. Install KiCad 10

Download it from the official page, **https://www.kicad.org/download/**, and choose your system:

| System | What to do |
|---|---|
| Windows | Run the 10.x installer with its default options. The defaults include the 3D models. |
| macOS | Open the 10.x `.dmg` and drag the KiCad folder into Applications. |
| Linux | Follow the page for your distribution (Ubuntu PPA, Flatpak, Fedora, Arch, and others). Make sure the version is 10.x. Some distributions ship the 3D models as a separate package, often named `kicad-packages3d`, or as a Flatpak extension. Install it too, or the 3D view shows bare boards. |

The files are KiCad 10 files. KiCad 9 and older cannot open them.

On the first start, KiCad may offer to set up the global libraries. Accept the default. The pair does not use them, but other projects will.

**No online viewer is known to read KiCad 10 files reliably, so none is recommended here.** To look without installing anything, open `copper.png` in each board's folder. It shows both copper faces and is generated from the board file.

### A2. Get the files

```
git clone -b pcb/kicad-boards https://github.com/BobStolb/TERMINAL-06-firmware
cd TERMINAL-06-firmware
```

Later, `git pull` brings the latest version. Without git, choose the `pcb/kicad-boards` branch on GitHub, then **Code → Download ZIP**.

### A3. Open each board

1. Start KiCad. Choose **File → Open Project** and open `PCB/TS06-DISP/TS06-DISP.kicad_pro`.
2. In the project window, double-click `TS06-DISP.kicad_pcb` to open the PCB Editor.
3. Do the same with `PCB/TS06-DRV/TS06-DRV.kicad_pro`.

**There is no schematic for the pair.** Its netlist is the Python file `tools/ts06pair.py`, and the generators write the boards from it. The folders hold no `.kicad_sch` file, so leave the Schematic Editor alone.

**Do not save the boards.** The files in the repository are written by the generators. Refilling zones or running DRC changes the board in memory, so KiCad asks to save when you close it. Answer **Discard**. If you save by accident, restore the file with `git checkout -- PCB/`. Otherwise `tools/verify_pair.sh` reports the board as edited by hand (part B).

### A4. Why the footprint library is inside the project

Each board folder has its own `fp-lib-table`. It names one library, `TS06`, at `${KIPRJMOD}/../lib/TS06.pretty`, which is `PCB/lib/TS06.pretty` in this repository. KiCad reads it when it opens the project, so there is nothing to install or configure. There are three reasons:

* **The Soviet parts have no stock footprints.** The ИН-12 and ИН-15 sockets, the wire-ended ИН-17 and the ИНС-1 lamps are drawn here. The ordinary parts were copied from KiCad 10's own libraries and adjusted.
* **Nobody's library setup can change the boards.** Every footprint the board uses comes from this repository.
* **KiCad can compare each footprint with its library copy.** The generators write rotated copies (`_R90`, `_R180`, `_R270`) into the library for that reason. The DRC's "footprint does not match library" check depends on it (part B).

### A5. Look around the board

* **Faces.** On TS06-DISP, the tubes are on the front face (F) and the pin strips XP11–XP25 are on the back (B). On TS06-DRV, the component face is F, towards the back of the case. The socket strips XS11–XS25 are on B, towards the display. To see a board from behind, use **View → Flip Board View**.
* **Layers.** The **Appearance** panel on the right has a **Layers** tab. The eye icon beside each layer shows or hides it. The **Layer presets** list at the bottom switches between front and back layers. **Ctrl+H** dims every layer except the active one. **PgUp** and **PgDn** switch the active layer between F.Cu and B.Cu.
* **Nets.** Hover over a pad and the status bar names its net. The **`** key (back-quote) highlights every pad and track of the net under the cursor. **Inspect → Net Inspector** lists every net with its length. For example, highlight `HV185` to see where 185 V goes.
* **Find a part.** **Ctrl+F** finds any reference, such as `C7`, `RP1` or `XS21`. Pin 1 of every part is its square pad.
* **Measure.** Use **Inspect → Measure Tool** (**Ctrl+Shift+M**) and click two points. Alternatively, press **Space** to zero the relative coordinates, and the status bar shows dx, dy and the distance. **Inspect → Clearance Resolution** takes two selected items and shows the rule between them. For example, any pad of an `ANODE_*` net shows 0.6 mm, the HV class.
* **Net classes.** Open **File → Board Setup → Design Rules → Net Classes**. `HV` has 0.6 mm clearance and covers `HV185`, `SW`, `BLEED_*`, `FB_MID`, `COLON_*`, `ANODE_*` and `EMIT_*`. `CATH` covers the cathode lines and `PWR` the rails.

### A6. Run KiCad's DRC in the GUI

1. Choose **Inspect → Design Rules Checker**.
2. Tick **Refill all zones before performing DRC**. TS06-DRV's ground pours must be refilled before they can be judged.
3. Click **Run DRC**. The results should be:

| Board | Errors | Warnings | Unconnected | Every item is accepted |
|---|---|---|---|---|
| TS06-DISP | 2 | 0 | 0 | Both errors are courtyard overlaps: V3/V7 and V3/V8, the colon lamps against the M10 tube |
| TS06-DRV | 0 | 4 | 0 | Two are silkscreen past the board edge on U1, the Nano with its USB. Two are library mismatches on VT21 and XS1 |

Part B explains each accepted item. Anything else in the list is new and needs a look. When you close the board, answer **Discard** (see A3).

### A7. The 3D viewer

Choose **View → 3D Viewer** (**Alt+3**). Drag to rotate, scroll to zoom and middle-drag to pan. The toolbar has buttons for the standard views.

* **TS06-DRV** shows KiCad's stock bodies for nearly every part: 95 models. These include the Nano, the jack, L1, C7, VT21, the DIP sockets and the socket strips. The chips themselves are not modelled, so every IC shows as an empty socket, and the RTC module shows as its 5-way socket.
* **TS06-DISP** shows almost nothing but the bare board and its seven pin strips. **No 3D bodies are included for the Soviet parts:** the ИН-12, ИН-17 and ИН-15 tubes and the ИНС-1 lamps. The LEDs have none either. To see the tubes in 3D, use the case model below. Separate STEP models of the tubes are in `3d/` (`IN12.step`, `IN17.step`, `INS1.step`) and open in FreeCAD.
* If a board shows no bodies at all, KiCad's 3D model library is missing. On Linux, install the package mentioned in A1.

### A8. The case model

The case is in `3d/case-pair/`. It is drawn around these boards, and `checks.md` there lists every interference check with its source.

* **OpenSCAD.** Install it from https://openscad.org/downloads.html and open `3d/case-pair/case.scad`. It includes the generated `params.scad`, so keep the two files together. **F5** previews and **F6** renders.
  * To view one part, change `PART = "assembly";` near the top. The choices are `module` (both boards), `cheek_l`, `cheek_r`, `brow`, `trench`, `base`, `rear` and `fascia_blank`.
  * `EXPLODE = 1;` pulls the parts apart.
  * From a terminal: `openscad -D 'PART="module"' -o module.stl 3d/case-pair/case.scad`.
* **STL files.** `3d/case-pair/out/*.stl` (cheeks, brow, trench, base, rear panel and a fascia blank) open in any slicer: PrusaSlicer, Cura, Bambu Studio or OrcaSlicer. Windows 3D Viewer and macOS Quick Look also show them. They are exported where they sit in the assembly, not flat on a bed. Lay each one on a face before printing; in PrusaSlicer, use **Place on face**, key F.
* **Drawings and pictures.** `out/front.svg`, `section.svg`, `plan.svg` and `exploded.svg` are 1:1 drawings. They open in a browser; print at 100 %. There are also PNG views: `iso.png`, `iso_rear.png`, `front.png`, `exploded.png` and `module.png`.
* **Current numbers.** `checks.md` is regenerated every time the checks run, so it has the current envelope: 204.4 × 122.8 × 81.6 mm (TS06-DRV rev B's real part heights). Some tables in the case's own `README.md` still quote the old 176 mm boards.

---

## B. Automated checks: `tools/verify_pair.sh`

### B1. Run it

From the repository root:

```
tools/verify_pair.sh              # everything, about a minute
tools/verify_pair.sh --no-drc     # everything but KiCad's DRC
tools/verify_pair.sh --keep       # keep the logs and DRC reports, and print where they are
```

* **What it needs.** Bash, Python 3.8 or newer, and numpy (`pip install numpy`).
  * On Windows, run it from Git Bash, which comes with Git for Windows, or from WSL.
  * For KiCad's DRC, it uses a KiCad 10 `kicad-cli` if one is on the PATH or in the usual install folder. You can also name one with `KICAD_CLI=/path/to/kicad-cli`.
  * Without KiCad, it uses Docker: the image `mirror.gcr.io/kicad/kicad:10.0`, about 1 GB, pulled once.
  * With neither, the two DRC lines say **SKIP**, the other KiCad-only checks (pours, HV rule live, erc) are not run, and the rest still runs.
  * If Docker cannot see `/tmp` (a snap-installed Docker), run `TMPDIR=$HOME/tmp tools/verify_pair.sh`.
* **What it touches.** Nothing in the working tree. Every regeneration goes into a scratch copy that is deleted at the end.
* **What it prints.** One line per check: **PASS**, **FAIL** or **SKIP**, with the key numbers. On a FAIL, the tool's own output follows, indented. The script exits with 1 if anything failed and 0 otherwise.

This is the output on the committed boards, 30.09.26 06:23 UTC (TS06-DRV rev B):

```
PASS  netlist                    disp 26 parts/59 nets, drv 108 parts/136 nets, 63 strip pins: consistent
PASS  mate                       63 strip pins (59 with a net) land on their pins, same net; 4 standoffs have holes
PASS  firmware tables            BOARD_TYPE 4 digit map, anode order, decoder bits, MCP 0x20; bring-up sketch tables: agree with tools/ts06pair.py
PASS  TS06-DISP generator        TS06-DISP.kicad_pcb, TS06-DISP.kicad_pro, fp-lib-table, TS06.pretty: identical to a fresh run of tools/mkpcb_disp.py
PASS  TS06-DISP checkpcb         30 footprints, 189 pads; accepted: H3 standoff above the colon 0.15 mm, XP11 at the left edge, its pads inside 0.17 mm, colon lamp V7 vs M10, colon lamp V8 vs M10
PASS  TS06-DISP checkcopper --hv 388 tracks, 0 vias, 378 pad-layers; HV 0.6 mm: clean
PASS  TS06-DISP audit            copper 2125 mm, 1.15x its floor, 0 vias, pour islands 1: clean
PASS  TS06-DISP checksch         179 pins connected, 0 dangling
PASS  TS06-DISP checkmatch       59 nets in the schematic, 59 on the board: they agree
PASS  TS06-DRV generator         TS06-DRV.kicad_pcb, TS06-DRV.kicad_pro, fp-lib-table, TS06.pretty: identical to a fresh run of tools/mkpcb_drv.py
PASS  TS06-DRV checkpcb          116 footprints, 435 pads; accepted: Nano USB proud of the edge 2.40 mm, XS11 behind the display's XP11 0.17 mm
PASS  TS06-DRV checkcopper --hv  1164 tracks, 0 vias, 870 pad-layers; HV 0.6 mm: clean
PASS  TS06-DRV audit             copper 6689 mm, 1.30x its floor, 0 vias, pour islands 9,7: clean
PASS  TS06-DRV checksch          516 pins connected, 0 dangling
PASS  TS06-DRV checkmatch        136 nets in the schematic, 136 on the board: they agree
PASS  TS06-DISP drc              KiCad 10.0.6 (docker mirror.gcr.io/kicad/kicad:10.0): 2 errors, 0 warnings, 0 unconnected; all accepted: colon V7 / M10 courtyards, colon V8 / M10 courtyards
PASS  TS06-DRV drc               KiCad 10.0.6 (docker mirror.gcr.io/kicad/kicad:10.0): 0 errors, 2 warnings, 0 unconnected; all accepted: Nano silk past the edge
PASS  pair mate (written files)  63 strip pins (59 with a net), 7 strips a side, 4 standoff holes, from the written files: positions, nets, drills and faces agree
PASS  TS06-DISP pours (KiCad)    BL_K F.Cu: 1 pieces, the largest 100% of 6103 mm2, 0 under 1 mm2
PASS  TS06-DRV pours (KiCad)     GND F.Cu: 15 pieces, the largest 92% of 12963 mm2, 2 under 1 mm2; GND B.Cu: 10 pieces, the largest 33% of 10721 mm2, 2 under 1 mm2
PASS  TS06-DISP HV rule live     V1.7 (ANODE_H10): a K2 track 0.70 mm from its edge: DRC reports 'HV pad clearance, IPC-2221B A6'
PASS  TS06-DRV HV rule live      C7.1 (HV185): a K2 track 0.70 mm from its edge: DRC reports 'HV pad clearance, IPC-2221B A6'
PASS  TS06-DISP erc              KiCad ERC, all severities: 0 violations
PASS  TS06-DRV erc               KiCad ERC, all severities: 0 violations
PASS  bom                        TS06-DISP 26 fitted, TS06-DRV 96 fitted + 12 DNP: identical to tools/bom_pair.py's output
PASS  case                       envelope 204.4 x 122.8 x 81.6 mm; 81 checks: 62 OK, 9 TIGHT, 7 NOTE, 3 FAIL; known: the two rejected jack-opening alternatives; OPEN: the fascia boss on R5's pad (review P6)
PASS  case outputs               7 generated files identical to a fresh run
----
27 PASS, 0 FAIL, 0 SKIP
```

### B2. What each check means

| Check | In one line |
|---|---|
| netlist | `tools/ts06pair.py`: every net has at least two pads, and every net on both boards crosses on a strip pin with the same name on both halves. |
| mate | Every XS socket pin on TS06-DRV sits exactly behind its XP pin on TS06-DISP and carries the same net, and every display standoff has its hole. |
| firmware tables | The clock firmware's `BOARD_TYPE 4` tables agree with the netlist: the digit map, the anode order, the decoder input bits and the expander's address. So do the bring-up sketch's tables. |
| generator | The committed `.kicad_pcb`, `.kicad_pro` and `fp-lib-table`, and the library's rotated footprints, are byte for byte what the generator writes today. So the checks below test the source, not a stale file. |
| checkpcb | Placement: every pad and courtyard inside the outline, and no two courtyards overlapping on the same face. |
| checkcopper --hv | Copper clearance. It holds 0.6 mm wherever a high-voltage net is on either side of a gap, keeps copper away from unplated holes, and confirms zero vias. |
| audit | Per-net connectivity through tracks and pours, which catches a pad that is cut off. It also counts pour islands and checks the silkscreen. |
| checksch | Every pin in the board's schematic sheets is connected; none is left dangling. |
| checkmatch | The schematic and the board carry the same nets. |
| drc | KiCad 10's own DRC with the zones refilled and every severity on, using the HV net class from the project file and the 0.8 mm HV pad rule in the `.kicad_dru`. |
| pair mate (written files) | The mate check again, read from the files KiCad wrote rather than from the netlist: positions, nets, drills and faces of every strip pin and standoff. |
| pours (KiCad) | KiCad fills every pour and the script counts its pieces: the largest share, and slivers under 1 mm². |
| HV rule live | Plants a track 0.70 mm from a 185 V pad in a scratch copy and confirms that KiCad's DRC reports it, so the 0.8 mm rule is really applied. |
| erc | KiCad's electrical rules check on the schematics, every severity on. |
| bom | `PCB/TS06-*/bom.md` is exactly what `tools/bom_pair.py` writes from the netlist today. |
| case | The case model re-reads both boards and the fascia and runs its 81 interference checks. |
| case outputs | The committed `boards.json`, `params.scad`, `checks.md` and drawings match a fresh run of the case model. |

### B3. The accepted exceptions

These items appear in the output but never FAIL. The script's header documents each one. If an accepted item grows past its limit, or a new item appears, the check FAILs.

| Where | Item | Why it is accepted |
|---|---|---|
| TS06-DISP checkpcb | H3's courtyard is 0.15 mm past the top edge | H3 is the standoff hole above the colon. The courtyard is only the keep-out drawn around the hole, not copper. It FAILs past 0.25 mm. |
| TS06-DISP checkpcb and DRC (2 errors) | Colon lamps V7 and V8 overlap the M10 tube's courtyard by 0.135 mm | The lamps stand at their measured positions, inherited from TS06-MAIN. Only a test fit with a real tube settles it (review 9). KiCad 10 files these as `courtyards_overlap` with severity *error*. |
| TS06-DRV checkpcb | U1's courtyard is 2.4 mm past the edge | The Nano's USB socket stands proud of the board on purpose, so the cable can reach it through the case cheek. It FAILs past 2.6 mm. |
| TS06-DRV checkpcb | XS11's courtyard is 0.17 mm past the edge | The strip must sit exactly behind the display's XP11, which is on the edge. It FAILs past 0.25 mm. |
| TS06-DRV DRC (2 warnings) | Silkscreen clipped by the board edge, on U1 | This is the Nano's outline around the same USB overhang. |
| case | Two rows read FAIL: "plain 6 mm cheek" and "Ø14 pocket from inside" | These are the two rejected ways of passing the DC jack through the cheek, recorded to show why the model counterbores it from the outside. The counterbore row reads OK, with 7.2 mm of plug engagement. The power entry is open again: the owner asked for more options (30.09.26). |
| case | A third row reads FAIL: the fascia boss on R5's pad | An OPEN finding (review P6), on the committed fascia A. It goes when the fascia is chosen (grill G11). |

### B4. When something FAILs

| Check | Usual cause | Fix |
|---|---|---|
| generator | The board was saved from KiCad | `git checkout -- PCB/` |
| generator | A generator changed and the board was not regenerated | `python3 tools/mkpcb_disp.py` or `python3 tools/mkpcb_drv.py`, then commit |
| bom | The BOM is stale | `python3 tools/bom_pair.py`, then commit |
| case outputs | The case outputs are stale | `python3 3d/case-pair/case_pair.py --extract`, then commit |
| Any other | A real finding | Read the indented lines under it: they are the tool's own words |

---

## C. Bench bring-up and test

### C0. Safety first: 185 V can hurt

The converter makes **185 V DC** and stores it in **C7, 4.7 µF**: ½·C·V² = ½ × 4.7 µF × 185² = **0.080 J**. That is above the usual touch-safe limits. A shock through the hand hurts, and the jerk that follows is how people get injured on a bench.

**Where the high voltage is:**
* **On TS06-DRV's component face:**
  * C7 and VD1;
  * the IRF840 VT21, whose metal tab is the switch node and reaches about 186 V;
  * the six optos U5–U10, pins 3 and 4;
  * the anode and colon resistors R27–R32 and R56–R59;
  * the bleeder and divider R60–R63.
* **On the strips:**
  * XS21 pins 3 and 4;
  * all three pins of XS22;
  * XS23 pins 2 and 3;
  * XS24 pins 2 and 3;
  * XS25 pins 2 and 5.
* **On TS06-DISP:** every tube anode, the colon lamps and the ИН-15 anodes.
* **The cathode lines** float up to about 60 V, where the К155ИД1 clamps them. That is not 185 V, but still not something to touch.

**The rules, every stage with high voltage on:**
1. **One hand.** Keep the other hand in your pocket or behind your back. Work on a dry, non-conductive surface, with no rings or watch.
2. **Clip, then power.** With the power off and C7 discharged, clip the meter leads on. Power on, read, and power off. Never move a probe on a live board.
3. **The meter** must be rated CAT II 600 V DC or better, with its leads, and have 10 MΩ input. Clip the black lead to GND: C7's negative pad, the barrel jack's sleeve, or U14 pin 2.
4. **Discharge before you touch.** The bleeder, R60 + R61 = 940 kΩ, takes C7 down (stage 3 times it). After power-off, **wait 15 s, then check C7 reads under 10 V** before your hand goes near the board.
   * If it still reads more than 10 V after 30 s, the bleeder is open. Discharge C7 through a 100 kΩ 1 W resistor on insulated clip leads for 5 s (τ = 0.47 s), then fix the bleeder.
   * Never short C7 with a screwdriver.
5. **Oscilloscope ground.** The scope's ground clip is tied to mains earth, and so is a desktop PC's USB ground. Clip it **only to board GND**, never to an anode or HV node. To measure across a resistor that sits at high voltage, use the battery-powered meter, which floats.
6. **Supply.** Use a current-limited bench supply at every stage until stage 8, at the limit the stage gives.

**What to have:**
* the meter;
* a 0–15 V bench supply with a current limit, at least 1 A;
* insulated micro-grabber clips;
* a plastic trimming tool for RP1;
* a stopwatch;
* a 100 kΩ 1 W discharge resistor on clip leads;
* a USB cable for the Nano;
* optionally, an oscilloscope with a 10× probe rated for 300 V or more;
* two home-made probes:
  * **the LED probe:** a 3 mm LED with a 1 kΩ resistor in series. Put a clip on the resistor end, which goes to +5 V, and a male Dupont pin on the LED's cathode, the short leg;
  * **the stand-in lamp:** a 100 kΩ resistor with a male Dupont pin on each end.

**The bring-up sketch** `firmware/ts06_bringup/ts06_bringup.ino` drives the board from the Serial Monitor at 9600 baud.
* **It is safe by default.** Every reset leaves the converter off, every anode off, every decoder blank and every LED off. Opening the Serial Monitor resets the Nano, so it also turns the high voltage off.
* **High voltage starts only on a capital `H`.** A lower-case `h` stops it.
* **Only one anode is ever on.** With the high voltage on, that tube runs at the clock's own duty: 21 of 156 ticks of 128 µs, which is 2.69 ms lit in each 19.97 ms frame, or 13.5 %. `s` gives a 5-second steady burst.
* **The commands:**

| Key | Does |
|---|---|
| `?` | Help and status |
| `H` / `h` | Converter on / off |
| `i` | I²C scan |
| `0`–`9` | That digit on U2 and U17 |
| `g` | Next ИН-15 code |
| `a` / `p` | AM / PM |
| `b` | Blank all decoders |
| `c` | Cycle all decoders, one step a second |
| `t` | Next anode |
| `x` | Anodes off |
| `s` | Steady burst |
| `k` | Colon on / off |
| `l` | Step through the LEDs |
| `r` | Live A6, A7 and buttons |

**What is fitted at each stage:**

| Stage | Sockets | Nano / RTC | Display | Fascia | Supply limit | HV |
|---|---|---|---|---|---|---|
| 1 | none (bare, then assembled) | out | apart | off | no power | none |
| 2 | none | out / out | apart | off | 100 mA | none (rail ≈ 11 V) |
| 3 | U11, U12 | bring-up sketch / out | apart | off | 500 mA | **185 V** |
| 4 | + U3 | sketch / **in** | apart | off | 500 mA | off, then 185 V with the clock |
| 5 | + U2, U15, U16, U17, U5–U10; **U11 out** | sketch / in | apart | off | 200 mA | none (rail ≈ 11 V) |
| 6 | + U11 | sketch, then the clock | **mated**, tubes one at a time | off | 500 mA | **185 V** |
| 7 | all | clock / in | mated | **on** | 500 mA | **185 V** |
| 8 | all | clock / in | mated | on | 1 A | **185 V** |

Fit and pull chips only with the power off and C7 under 10 V. Check every socket's notch against the silkscreen and against KiCad before a chip goes in. The driver board uses three orientations (review 5).

---

### Stage 1: bare boards, continuity and isolation

**Instrument:** the meter on continuity (beeper) and on its highest resistance range, plus a loupe.

**1a. Look first.** Under the loupe, check the strip rows XS21, XS23, XS24 and XS25, and XP21, XP23, XP24 and XP25 on the display. There, a 5 V LED line sits **0.84 mm** from a 185 V anode pad. That is IPC-2221B's 0.8 mm plus 0.04 (review 7). A solder bridge there puts 185 V into the MCP23017. Look also at VT21's three pads (0.94 mm apart: SW against gate and GND) and the empty bleed footprints R33–R44 (0.94 mm).

**1b. Isolation on the bare boards.** Every pair below must read **open** (OL) on the highest range. These are the closest high-to-low-voltage pad pairs on each board, found from the board files. The pad-to-pad gap is the edge-to-edge distance.

| Board | Between | And | Gap |
|---|---|---|---|
| DRV | XS21.3 ANODE_H10 | XS21.2 BL_A1 | 0.84 mm |
| DRV | XS21.4 ANODE_H1 | XS21.5 BL_A2 | 0.84 |
| DRV | XS23.2 ANODE_M10 | XS23.1 BL_A3 | 0.84 |
| DRV | XS23.3 ANODE_M1 | XS23.4 BL_A4 | 0.84 |
| DRV | XS24.2 ANODE_S10 | XS24.1 BL_A5 | 0.84 |
| DRV | XS24.3 ANODE_S1 | XS24.4 BL_A6 | 0.84 |
| DRV | XS25.2 ANODE_AM | XS25.1 BL_A7 | 0.84 |
| DRV | XS25.5 ANODE_PM | XS25.4 M_A and XS25.6 BL_A8 | 0.84 |
| DRV | VT21.2 SW (drain) | VT21.1 GATE and VT21.3 GND | 0.94 |
| DRV | VT1.3 COLON_RET | VT1.2 B1 | 1.04 |
| DRV | C7 pad 1 (+, HV185) | C7 pad 2 (GND), U14 pin 3 (+5 V), C8 pad 1 (+12 V) | — |
| DRV | U14 pin 3 (+5 V) and C8 pad 1 (+12 V) | GND (U14 pin 2) | — |
| DISP | the same nine XP pairs as the XS rows above | | 0.84 |
| DISP | V5 pad A (ANODE_S10) | V5 pad 0 (KS0) | 0.90 |
| DISP | V6 pad A (ANODE_S1) | V6 pad 0 (KS0) | 0.90 |

**1c. Continuity of the strips.** Every strip pin must beep to its pads on its own board, and to nothing next to it. The table is generated from `tools/ts06pair.py`, as *ref.pin*. On TS06-DISP, the ИН-12 socket's pad 7 is the anode.

<details><summary>All 63 strip pins (click to open)</summary>

| Pin | Net | TS06-DRV: XS pin to | TS06-DISP: XP pin to |
|---|---|---|---|
| 11.1 | K6 | U2.9 | V1.2, V2.2, V3.2, V4.2 |
| 11.2 | K5 | U2.10 | V1.1, V2.1, V3.1, V4.1 |
| 11.3 | K7 | U2.8 | V1.3, V2.3, V3.3, V4.3 |
| 11.4 | K4 | U2.11 | V1.12, V2.12, V3.12, V4.12 |
| 11.5 | K8 | U2.2 | V1.4, V2.4, V3.4, V4.4 |
| 11.6 | K3 | U2.13 | V1.11, V2.11, V3.11, V4.11 |
| 11.7 | K9 | U2.1 | V1.5, V2.5, V3.5, V4.5 |
| 11.8 | K2 | U2.14 | V1.10, V2.10, V3.10, V4.10 |
| 11.9 | K0 | U2.15 | V1.6, V2.6, V3.6, V4.6 |
| 11.10 | K1 | U2.16 | V1.9, V2.9, V3.9, V4.9 |
| 12.1 | KS7 | U17.8 | V5.7, V6.7 |
| 12.2 | KS6 | U17.9 | V5.6, V6.6 |
| 12.3 | KS5 | U17.10 | V5.5, V6.5 |
| 12.4 | KS4 | U17.11 | V5.4, V6.4 |
| 12.5 | KS3 | U17.13 | V5.3, V6.3 |
| 12.6 | KS2 | U17.14 | V5.2, V6.2 |
| 12.7 | KS1 | U17.16 | V5.1, V6.1 |
| 12.8 | KS0 | U17.15 | V5.0, V6.0 |
| 12.9 | KS9 | U17.1 | V5.9, V6.9 |
| 12.10 | KS8 | U17.2 | V5.8, V6.8 |
| 12.11–12.13 | (spare) | — | — |
| 12.14 | CAT_B_AMP | U15.8 | V9.9 |
| 12.15 | CAT_B_OHM | U15.9 | V9.10 |
| 12.16 | CAT_B_SIEMENS | U15.10 | V9.12 |
| 12.17 | CAT_B_VOLT | U15.11 | V9.1 |
| 12.18 | CAT_B_HENRY | U15.13 | V9.2 |
| 12.19 | CAT_B_HERTZ | U15.14 | V9.3 |
| 12.20 | CAT_B_FARAD | U15.15 | V9.5 |
| 12.21 | CAT_B_WATT | U15.16 | V9.6 |
| 12.22 | CAT_A_NANO | U16.8 | V10.9 |
| 12.23 | CAT_A_PCT | U16.9 | V10.10 |
| 12.24 | CAT_A_PI | U16.10 | V10.11 |
| 12.25 | CAT_A_KILO | U16.11 | V10.12 |
| 12.26 | CAT_A_MEGA | U16.13 | V10.1 |
| 12.27 | CAT_A_MILLI | U16.14 | V10.2 |
| 12.28 | CAT_A_PLUS | U16.15 | V10.3 |
| 12.29 | CAT_A_MINUS | U16.16 | V10.4 |
| 12.30 | CAT_A_P | U16.1 | V10.5 |
| 12.31 | CAT_A_MICRO | U16.2 | V10.6 |
| 21.1 | BL_K | VT20.3 | HL1.1 … HL9.1 (every LED's cathode) |
| 21.2 | BL_A1 | RN1.9 | HL1.2 |
| 21.3 | ANODE_H10 | R27.2, R33.1 | V1.7 |
| 21.4 | ANODE_H1 | R28.2, R35.1 | V2.7 |
| 21.5 | BL_A2 | RN1.10 | HL2.2 |
| 22.1 | COLON_U | R58.2 | V7.1 |
| 22.2 | COLON_L | R59.2 | V8.1 |
| 22.3 | COLON_RET | VT1.3 | V7.2, V8.2 |
| 23.1 | BL_A3 | RN1.11 | HL3.2 |
| 23.2 | ANODE_M10 | R29.2, R37.1 | V3.7 |
| 23.3 | ANODE_M1 | R30.2, R39.1 | V4.7 |
| 23.4 | BL_A4 | RN1.12 | HL4.2 |
| 24.1 | BL_A5 | RN1.13 | HL5.2 |
| 24.2 | ANODE_S10 | R31.2, R41.1 | V5.A |
| 24.3 | ANODE_S1 | R32.2, R43.1 | V6.A |
| 24.4 | BL_A6 | RN1.14 | HL6.2 |
| 25.1 | BL_A7 | RN1.15 | HL7.2 |
| 25.2 | ANODE_AM | R56.1 | V9.7 |
| 25.3 | (none: mechanical) | — | — |
| 25.4 | M_A | R53.2 | HL9.2 |
| 25.5 | ANODE_PM | R57.1 | V10.7 |
| 25.6 | BL_A8 | RN1.16 | HL8.2 |

The fascia connector J1, a PH 6-way: pin 1 +5 V (U14.3), 2 GND, 3 A6 (Nano pin 25), 4 A7 (26), 5 D7 (10), 6 D8 (11). The Nano's strip pins use KiCad's numbering: 4 and 29 GND, 5–16 D2–D13, 19–26 A0–A7, 27 +5 V. The RTC socket U13: 1 GND, 2 NC, 3 SCL, 4 SDA, 5 +5 V.

</details>

**1d. After soldering: resistance, before any power.** Assemble the boards, soldering the strips with the two boards plugged together (review 2). Leave every socket empty, and the Nano and RTC module out. Unplug the display. Then check:

| Measure | Expected, and why | Pass |
|---|---|---|
| The nine strip neighbours of 1b | Open. ANODE_x reaches only its anode resistor and an empty opto socket. BL_Ax reaches RN1 and an empty U3 socket. | OL |
| Each anode strip pin to GND | Open. The bleed pairs R33–R44 are not fitted (DNP). | OL (about 1.0 MΩ if the bleeds are fitted) |
| Across R27–R30, then R31–R32, in place | 6.8 kΩ, then 12 kΩ. The sockets are empty, so nothing is in parallel. This also proves they are not swapped. | ±5 % |
| Across R56 and R57, in place | 18 kΩ | ±5 % |
| C7 + to C7 − (HV185 to GND) | The bleeder in parallel with the divider: 940 k ∥ (1.5 M + 18 k + RP1). With RP1 at 5 k: 940 k ∥ 1523 k = **581 kΩ**. It creeps up for a few seconds while the meter charges C7. | 550–600 kΩ (5 % bleeders) |
| RP1 pin 1 (FB_LOW) to GND | RP1 itself. The path through R64, the divider and the bleeder, 2.4 MΩ, changes it by less than 1 %. **Turn RP1 until it reads 5.0 kΩ.** That is the lowest rail set-point, 165 V, for stage 3. | 5.0 kΩ |
| C7 + to U12 pin 2 (HV185 to FB) | 1.5 M ∥ (940 k + 18 k + 5 k) = **587 kΩ** with the divider whole. If R62 or R63 is open, it reads 963 kΩ. **Then do not power the converter:** with no feedback it would run away. | 560–615 kΩ |
| U14 pin 3 (+5 V) to GND | R69 + R70 = 20 kΩ, in parallel with the regulator's output. | not under 100 Ω |
| TS06-DISP, diode test: red on XP21.2, black on XP21.1 | HL1 forward: 1.6–2.0 V, and the LED glows faintly. Repeat for each BL_A pin and for M_A (XP25.4) against XP21.1. | LED lights; no LED backwards |

---

### Stage 2: power only, no chips, no modules

**Fitted:** nothing in any socket. The Nano and RTC module are out, the display is unplugged and the fascia is off.
**Instrument:** the bench supply at **12.0 V with a 100 mA limit**, into the barrel jack (centre positive), and the meter on DC volts, black on GND.

| Measure, where | Expected | Pass |
|---|---|---|
| Supply current | 1.5 mA, the R-78E's own no-load draw (RECOM datasheet), + the VREF divider, 5 V / 20 kΩ = 0.25 mA, which is 0.13 mA at 12 V after the regulator, + HV185's idle path, 11.4 V / 581 kΩ = 0.02 mA. **≈ 1.7 mA.** Most supplies show 0.00 A. For the number, put the meter in series on its mA range. | < 5 mA |
| Optional: reverse the supply | VD2, the 1N5822, blocks it. Only its leakage flows. | < 2 mA, nothing warms |
| +12 V: C8 pad 1, or U14 pin 1 | 12.0 V less VD2's drop at about 2 mA, ≈ 0.2 V: **11.8 V** | 11.5–12.0 V |
| +5 V: U14 pin 3 | **5.00 V**. The К155ИД1 is TTL and needs 5 V ± 5 %. | 4.75–5.25 V |
| VREF: U12 socket pin 3 or 5 | R69/R70 halve 5 V. R65 (1 MΩ) pulls it slightly low through R71 (10 kΩ) to ground: 5.00 × (10 k ∥ 1.01 M) / (10 k + 10 k ∥ 1.01 M) = **2.488 V** | 2.46–2.52 V |
| HV185: C7 +, or VD1's banded end | With the converter idle, the 12 V input reaches C7 through L1 and VD1: 11.8 − 0.4 = **≈ 11.4 V**. If it reads 0 V, VD1 is in backwards or L1 is open. | 10.8–11.8 V |
| SW: VT21 middle pin | +12 V through L1: **11.8 V** | = +12 V |
| GATE: VT21 pin 1 | R68 holds it at 0 V | < 0.1 V |

**Every socket's supply pins, before any chip sees them.** The К155ИД1 does not use the usual corner pins:

| Socket | +V pin(s) | GND pin(s) | Expected |
|---|---|---|---|
| U2, U15, U16, U17 (К155ИД1, DIP-16) | **5** | **12** | 5.00 V |
| U3 (MCP23017, DIP-28) | 9, 18 (RESET) | 10; 15, 16, 17 (address 0x20) | 5.00 V |
| U12 (LM393) | 8 | 4 | 5.00 V; pins 3 and 5 = VREF |
| U11 (TC4420) | 1, 8 | 4, 5 | 11.8 V |
| U5–U10 (TLP627) | 4, the collector: HV185 | 2 | ≈ 11.4 V now; 185 V from stage 3 on |
| Nano strips | 27 (5V) | 4, 29 | 5.00 V; pin 30 (VIN) is not connected |
| U13 (RTC socket) | 5 | 1 | 5.00 V |
| J1 | 1 | 2 | 5.00 V |

---

### Stage 3: the converter

**First, flash the Nano with the bring-up sketch** on your computer. Section 4.1 below shows how.

**Fit,** with the power off: U11 (TC4420), U12 (LM393) and the flashed Nano. Nothing else. The display stays unplugged.

**Before the first power-up:** stage 1d set RP1 to 5.0 kΩ and proved the divider whole. Do not skip either.

**Instrument:**
* the meter on 600 V DC, **black clipped to C7 −, red clipped to C7 + (or VD1's band)**, before power;
* the supply at 12.0 V with a **500 mA** limit;
* optionally, a scope.

**3a. Power on, HV off.** The sketch starts with the converter off, so the rail reads ≈ 11.4 V.

The supply current is about **12 mA**:
* the Nano, about 20 mA; clones vary;
* the LM393, 0.4 mA;
* VREF, 0.25 mA;

which is 20.7 mA at 5 V. At about 80 % efficiency through the regulator, that is 20.7 × 5 / 12 / 0.8 = 10.8 mA at 12 V. Add the regulator's own 1.5 mA.

**Pass:** 8–25 mA.

**3b. `H`: the converter starts.** The rail climbs in a fraction of a second to the set-point for RP1 = 5 kΩ:

V = VREF × (R62 + R63 + R64 + RP1) / (R64 + RP1) = 2.5 × 1523 k / 23 k = **165.5 V**

**Pass:** 145–160 V. **If it passes 200 V, or keeps climbing, press `h` or switch off at once.** The feedback is open.

**3c. Set 185 V.** With a plastic tool, turn RP1 slowly and watch the meter. If the rail falls, turn the other way. RP1's own pins sit near 0 V, but it stands among 185 V parts.

The target is R64 + RP1 = 1.5 MΩ / (185 / 2.5 − 1) = 20.55 kΩ, so **RP1 ≈ 2.55 kΩ** (R64 is 18 k). Near 185 V, the rail moves 2.5 × 1.5 M / (20.55 k)² = 8.9 V per kΩ, about **1.8 V per turn** of the 25-turn 5 k 3296W. The whole trimmer spans 165–210 V.

**Pass:** 185 ± 1 V now. The production QC figure is **185 ± 8 V warm** (spec §10).

**3d. No-load current.**
* **What loads the rail:** the bleeder, 185 V / 940 kΩ = 0.197 mA, and the divider, 185 V / 1.52 MΩ = 0.122 mA. That is **0.318 mA**, or 185 × 0.318 mA = **59 mW**.
* **What that costs at 12 V:** at about 80 % efficiency, 59 / 0.8 / 11.8 = **6.2 mA** more than in 3a.

**Pass:** `H` adds 3–15 mA to the supply current. If it adds more than 50 mA, something loads the rail: a bridge, C7 in backwards, or VD1 leaking. Switch off.

**3e. Ripple (scope).** Probe tip on C7 +, ground clip on C7 −. Set AC coupling, 20 MHz bandwidth limit, 0.2 V/div and 1 ms/div.

**How big each step is:**
* D9 runs Timer1 at 16 MHz / 510 = **31.4 kHz**, high for 2 × 190 / 16 MHz = **23.75 µs**.
* L1 charges to I = 11.8 V × 23.75 µs / 220 µH = **1.27 A**.
* That stores ½ × 220 µH × 1.27² = 178 µJ. About 12 µJ more passes straight through from the input while L1 empties into C7 in 1.6 µs.
* So each pulse lifts the rail by 190 µJ / (4.7 µF × 185 V) = **0.22 V**.

**How often it steps:**
* At no load, the rail sags at 0.318 mA / 4.7 µF = 68 V/s.
* The comparator fires one pulse about every 0.22 / 68 = **3.2 ms**, about 300 times a second.

So you see a sawtooth of **≈ 0.2–0.3 V p-p**. For slower wander, the comparator's hysteresis sets the bound. R65 (1 MΩ) moves VREF by 15 mV, which is 15 mV × 74 = 1.1 V of rail.

**Pass:** ≤ 1.5 V p-p, which is the 1.1 V hysteresis plus one pulse.

On VT21's drain (SW), still with the ground clip on GND, you see 0 V for 23.75 µs. Then a flat top at about 186 V for 1.6 µs while L1 empties, then ringing down to 12 V.

**3f. Discharge time after power-off. This is the safety number.** Leave the meter clipped on C7. Switch the **supply off**, not just `h`, and start the stopwatch. With `h` alone, the 12 V input holds the rail at 11.4 V.

C7 discharges through the bleeder and the divider in parallel: 940 k ∥ 1.52 M = 581 kΩ, so τ = 4.7 µF × 581 kΩ = **2.73 s**.

| Down to | t = τ · ln(185 / V) |
|---|---|
| 60 V | 3.1 s |
| **10 V** | **8.0 s** (7.5 s with the meter's 10 MΩ in parallel; 9.6 s if C7 is 20 % high) |
| 1 V | 14.3 s |

**Pass:** under 10 V within 6–11 s. If it is still above 100 V after 10 s, the bleeder (R60/R61) is open: a safety defect. Discharge C7 as in C0 and fix it before going on. From here on, **"wait 15 s and check under 10 V"** is the rule every time the power goes off.

---

### Stage 4: logic, the Nano and the I²C bus

**4.1 How to flash.** This applies to both the bring-up sketch and the clock.

The Nano can be flashed on the board or off it. **On the board, keep the 12 V supply on while USB is connected.** With 12 V off, USB power back-feeds the R-78E's output through the Nano's diode, which RECOM warns can damage it (electrical review E5; rev B adds a 1N5819 across U14).

**Arduino IDE 2.x:**
* **Tools → Board → Arduino AVR Boards → Arduino Nano**; **Tools → Processor → ATmega328P**. On CH340 clones, if the upload times out, choose **ATmega328P (Old Bootloader)**. Pick the Nano's port under **Tools → Port**; Windows and macOS may need the CH340 driver.
* **The bring-up sketch.** Open `firmware/ts06_bringup/ts06_bringup.ino` and choose **Upload** (Ctrl+U). Then open **Tools → Serial Monitor** at **9600 baud**.
* **The clock.**
  1. Copy `libraries/GyverButton` and `libraries/RTClib` into your sketchbook's `libraries` folder. **File → Preferences** shows where the sketchbook is.
  2. Open `firmware/nixieClock_TS06/nixieClock_TS06.ino`.
  3. Change line 37 from `#define BOARD_TYPE 0` to **`#define BOARD_TYPE 4`**, then Upload. The default 0 is the owner's bench board. On the pair, 0 shows scrambled digits (review 8).

**arduino-cli:**

```
arduino-cli core update-index
arduino-cli core install arduino:avr
# the bring-up sketch, then its monitor
arduino-cli compile --upload -p /dev/ttyUSB0 --fqbn arduino:avr:nano firmware/ts06_bringup
arduino-cli monitor -p /dev/ttyUSB0 -c baudrate=9600
# the clock, after setting BOARD_TYPE 4
arduino-cli compile --upload -p /dev/ttyUSB0 --fqbn arduino:avr:nano --libraries libraries firmware/nixieClock_TS06
```

* On old-bootloader clones, use `--fqbn arduino:avr:nano:cpu=atmega328old`.
* The port is `COM3` or similar on Windows, and `/dev/cu.usbserial-…` on macOS.

**Three things to know:**
* **Do not flash the committed `nixieClock_TS06.hex`.** It is a stale BOARD_TYPE 1 build (review 8).
* **The clock firmware starts the converter the moment it boots.** Flash it only when you are ready for 185 V. The bring-up sketch never does this.
* **The clock sets the RTC to the build time at every boot** (`rtc.adjust()` in `setup()`, review 8). This is a known issue. The time is lost at every power cycle until that is fixed.

**4.2 Fit U3 and the RTC module.** With the power off, fit U3 (MCP23017) and the DS3231 module in U13.
* **U3:** check the notch. It is one of the three orientations on this board.
* **The module:** before plugging it in, read the labels on its pins. The socket expects **GND, NC, SCL, SDA, +5 V** from pin 1, which is "− NC C D +". This is gate 6. The wrong order puts 5 V on the module's ground.

**4.3 I²C scan, HV off.** Power on and type `i`. The sketch first reads the idle bus with the ATmega's own pull-ups off, then scans:

| Line | Expected | If not |
|---|---|---|
| idle bus | SDA high, SCL high. R54 and R55, 4.7 kΩ, hold both lines at 5 V | a line held low: look for a short at U3 pins 12/13 or U13 pins 3/4; a missing pull-up |
| 0x20 | MCP23017, U3: A0–A2 grounded gives 0x20 + 0 | U3 in backwards, no 5 V on its pin 9, or RESET (pin 18) low |
| 0x68 | DS3231 | the module's pin order (gate 6), or no module |
| 0x57, or another 0x50–0x57 | only if your module carries an AT24C32 EEPROM. The larger ZS-042 does; the 5-pin "mini" usually doesn't | not a fault |
| "MCP23017 takes register writes…" | the expander read back its direction registers | U3 is answering but not working |
| DS3231 time, temperature | any time; room temperature ± 3 °C, the DS3231 sensor's accuracy; OSF set means the oscillator stopped at some point since the time was last set (no battery, or a new one), so set the time | — |

The bus arithmetic:
* **Rise time:** 0.85 × 4.7 kΩ × about 100 pF of track and three chips = **0.4 µs**, inside the 1 µs standard-mode limit.
* **Sink current:** 5 V / 4.7 kΩ = **1.1 mA**, under the 3 mA limit.

**4.4 The decoder inputs, before the decoders go in.** Measure at the empty U2 and U15/U16 sockets. The К155ИД1 inputs are pin 3 = A (weight 1), 6 = B (2), 7 = C (4) and 4 = D (8).

| Type | Code sent | Expected at the socket |
|---|---|---|
| `0` | digit 0 → code **1** on U2 and U17 (Nano A3) | U2 pin 3 = 5 V; pins 6, 7, 4 = 0 V |
| `7` | digit 7 → code **2** (Nano A1) | U2 pin 6 = 5 V; pins 3, 7, 4 = 0 V |
| `4` | digit 4 → code **6** (A1 + A0) | U2 pins 6 and 7 = 5 V; 3, 4 = 0 V |
| `8` | digit 8 → code **9** (A3 + A2) | U2 pins 3 and 4 = 5 V; 6, 7 = 0 V |
| `a` | U15 code **2** (GPA1), U16 blank (code 15) | U15 pin 6 = 5 V, pins 3, 4, 7 = 0 V; U16 pins 3, 4, 6, 7 all 5 V |
| `p` | U15 blank, U16 code **8** (GPA6) | U16 pin 4 = 5 V, pins 3, 6, 7 = 0 V; U15 all four 5 V |
| `b` | all blank, code 15 | every input pin at 5 V |

**4.5 The clock boots, and it talks to the expander.** Flash the clock with BOARD_TYPE 4 (4.1). Clip the meter on C7 first: **the converter starts at boot** and the rail comes to the 185 V set in stage 3.

On boot, the clock's `pairInit()` writes the expander:
* port B high: every LED line;
* port A at code 15: both ИН-15 blank;
* D12 high: the "m" LED.

With the power off and C7 discharged, move the meter's red lead, then power on again:

| Where | Expected | Why |
|---|---|---|
| C7 + | 185 V | the converter, clocked by the firmware |
| XS21.2 (BL_A1), and each BL_A strip pin | 5 V | GPB high through RN1, 220 Ω, into the meter's 10 MΩ |
| U15/U16 socket pins 3, 4, 6, 7 | 5 V | code 15 |
| XS25.4 (M_A) | 5 V | D12 high through R53 |

Then flash the bring-up sketch back for stage 5.

---

### Stage 5: decoders and optos, no tubes, no high voltage

**Power off and discharge. Pull U11 (TC4420).** Now nothing can start the converter, whatever the Nano runs. R68 holds the gate low, and the rail sits at the 12 V input through L1 and VD1: ≈ 11.4 V. This makes the whole stage safe to probe.

**Fit** U2, U17, U15, U16 (К155ИД1) and U5–U10 (TLP627). Check every notch.

**Supply:** 12 V with a 200 mA limit. The four TTL decoders add 16 mA each, typically (25 mA maximum), so about 64 mA at 5 V. At 12 V that is 64 × 5 / 12 / 0.85 = 31 mA more than stage 4. **Pass:** about 30–70 mA in all.

**5a. Every decoder output, with the LED probe.** Clip the probe's resistor end to **+5 V: U14 pin 3**.
* **On the output the code selects:** the К155ИД1 pulls it low and the LED lights. The current is (5.0 − 2.0 LED − 0.4 output) / 1 kΩ = **2.6 mA**.
* **On every other output:** the output is off and the LED stays dark.

Find pin 1 of XS11 and XS12 in KiCad (the square pad) and mark it on the strip with a pen. Then type a digit. The sketch prints the decoder pin and the strip pins that must light the probe, for example:

```
digit 3 = code 4: U2/U17 pin 13 low -> XS11.6 (IN-12), XS12.5 (IN-17)
```

Touch every pin of XS11 and XS12. **Only the named pins light it.** `c` steps all four decoders once a second, 0–9 and then blank. `g` steps the ИН-15 pair alone.

| Digit | Code | U2 / U17 pin | XS11 pin (ИН-12) | XS12 pin (ИН-17) |
|---|---|---|---|---|
| 0 | 1 | 15 | 9 | 8 |
| 1 | 0 | 16 | 10 | 7 |
| 2 | 5 | 14 | 8 | 6 |
| 3 | 4 | 13 | 6 | 5 |
| 4 | 6 | 11 | 4 | 4 |
| 5 | 7 | 10 | 2 | 3 |
| 6 | 3 | 9 | 1 | 2 |
| 7 | 2 | 8 | 3 | 1 |
| 8 | 9 | 2 | 5 | 10 |
| 9 | 8 | 1 | 7 | 9 |

| ИН-15 code | U15 (ИН-15Б) glyph → XS12 pin | U16 (ИН-15А) glyph → XS12 pin | decoder pin |
|---|---|---|---|
| 0 | W → 21 | − → 29 | 16 |
| 1 | F → 20 | + → 28 | 15 |
| 2 | **A (AM)** → 14 | n → 22 | 8 |
| 3 | Ω → 15 | % → 23 | 9 |
| 4 | H → 18 | M → 26 | 13 |
| 5 | Hz → 19 | m → 27 | 14 |
| 6 | V → 17 | K → 25 | 11 |
| 7 | S → 16 | π → 24 | 10 |
| 8 | (none) | **P (PM)** → 30 | 1 |
| 9 | (none) | µ → 31 | 2 |

**5b. Every anode switch, with the meter.** Clip black to GND and red to the anode strip pin (table below). Type `t` until that tube is selected, then `s`. With the converter off, `s` holds the anode steady until you press `t`, `x` or `s` again.

| Tube | Nano pin | Opto LED resistor | Opto | Anode resistor | Strip pin |
|---|---|---|---|---|---|
| H10 | D6 | R21 | U5 | R27 6k8 | XS21.3 |
| H1 | D5 | R22 | U6 | R28 6k8 | XS21.4 |
| M10 | D4 | R23 | U7 | R29 6k8 | XS23.2 |
| M1 | D3 | R24 | U8 | R30 6k8 | XS23.3 |
| S10 | D2 | R25 | U9 | R31 12k | XS24.2 |
| S1 | D13 | R26 | U10 | R32 12k | XS24.3 |

| Measure | Expected | Pass |
|---|---|---|
| The selected tube's strip pin | the 11.4 V rail less the Darlington's saturation at a microamp, ≈ 0.7 V: **≈ 10.7 V**. The anode resistor drops nothing into 10 MΩ. | 9.5–11.5 V |
| The other five anode pins | off | < 1 V (typically under 0.1 V) |
| Across the selected opto's 470 Ω (R21–R26) | the opto LED's current: (4.8 V Nano output − 1.15 V LED) / 470 Ω = **7.8 mA**, so **3.65 V** | 3.2–4.0 V |
| XS25.2 and XS25.5 (the ИН-15 anodes) | always the rail, through R56/R57: ≈ 11.4 V. They have no switch. | = rail |

The Nano's own "L" LED is on D13, so it lights with S1. It also blinks at every reset, because the bootloader flashes D13.

**5c. The colon switch, with the stand-in lamp.** Plug the 100 kΩ stand-in between **XS22.1** (COLON_U) and **XS22.3** (COLON_RET), and measure XS22.3 to GND.
* **Off:** the rail through R58 and the stand-in into the meter: 11.4 × 10 M / (10 M + 220 k + 100 k) = **11.0 V**.
* **`k` on:** VT1 saturates. Its base current is (4.8 − 0.75) / 10 kΩ = 0.4 mA, for 35 µA of collector current. It reads **< 0.2 V**.

**Pass:** off > 10 V, on < 0.3 V. Repeat with the stand-in on XS22.2, which tests R59.

**5d. The LED switch and the expander's port B, with a spare LED.** Push a 3 mm LED into XS21: **cathode, the short leg, into pin 1 (BL_K); anode into pin 2 (BL_A1)**. Then type `l` repeatedly:

| Step | What lights |
|---|---|
| all nine | lit |
| HL1 alone | lit |
| HL2 … HL8, HL9 | dark |
| off | dark |

The current is (4.6 V port output − 2.0 V LED − 0.1 V VT20) / 220 Ω = **11 mA**.

For each other LED line, move the anode leg to its strip pin: XS21.5, XS23.1, XS23.4, XS24.1, XS24.4, XS25.1, XS25.6, and XS25.4 for the "m". Take the cathode to XS21.1 with a jumper. Each must light only in its own step and in "all".

---

### Stage 6: the display mated, tubes one at a time

**Power off, discharge, refit U11.**
* **Fit the tubes one at a time.** Fit the socketed ИН-12s one by one.
* **The ИН-17s are wire-ended.** Solder them only after **gate 3** has confirmed their lead order. A wrong one cannot be undone.
* **Plug TS06-DISP onto the strips** and screw its four standoffs.

**Why one tube at a time.** The bring-up sketch lights one anode at a time, so a missing tube does no harm. The clock firmware is different. It scans six slots, and a slot without its tube lights the others' decaying anodes (spec §5a-pre). **Do not judge ghosting with the clock until all six tubes are in.**

**For each tube:**
1. Power off and discharge.
2. Clip the meter **across that tube's anode resistor**: red on the opto end (pin 1, EMIT), black on the anode end (pin 2, ANODE). Both ends sit at 140–185 V. Only a floating battery meter goes here, never a scope ground.
3. Power on and type `H`. Select the tube with `t` and type a digit.
4. The tube lights at the clock's 13.5 % duty. The meter reads the **average**.
5. Type `s` for a 5-second steady burst. The meter now reads **V_R**, and the tube's peak current is I = V_R / R.
6. Type `h`, power off and wait.
7. Type each digit 0–9. **The right numeral must light.** For the ИН-17, this confirms gate 3's cathode order in the circuit.

**The expected values.** The resistor gets what is left of the rail after the tube's sustaining voltage, the opto's saturation (≈ 1 V) and the decoder's output (≈ 1 V; the К155ИД1 allows up to 2.5 V at 7 mA).

The sustaining voltages are the repository's working figures, and gate 2 is what measures them:
* **ИН-12:** about 140 V.
* **ИН-17:** about 105 V. One source says 160 V instead.
* **ИН-15:** 140 V is assumed.

| Tube | Resistor | V_R, steady (`s`) | Peak current | Meter at 13.5 % | Pass, steady |
|---|---|---|---|---|---|
| ИН-12, V1–V4 | R27–R30, 6k8 | 185 − 140 − 1 − 1 = **43 V** | 43 / 6.8 k = **6.3 mA** | 43 × 21/156 = **5.8 V** (0.85 mA average) | 33–53 V (4.9–7.8 mA; sustain 130–150 V), average 4.4–7.1 V |
| ИН-17, V5–V6 | R31–R32, 12k | 185 − 105 − 2 = **78 V** | 78 / 12 k = **6.5 mA** | 78 × 21/156 = **10.5 V** (0.88 mA) | 66–90 V (5.5–7.5 mA; sustain 93–117 V), average 8.9–12.1 V |

**What a reading says:**
* **Record it.** V_sustain ≈ 185 − V_R − 2 V. This is **gate 2**, measured in the circuit.
* **An ИН-17 reading near 23 V** means the tube sustains at about 160 V, as tec.org.ru says. That is 1.9 mA, and the tube is dim. It is not a board fault: gate 2 decides R31/R32, which are through-hole and easy to change.
* **A reading near 0 V** means the tube is not lit. Check the anode identity (gates 3 and 4), the opto, or a pin not seated.
* **The wrong numeral** means the cathode order is different. That is a firmware table, not copper (review, "What holds up").

**The ИН-15 pair (V9 ИН-15Б, V10 ИН-15А).** They have no anode switch. R56 and R57 feed them from the rail, so a tube is lit whenever the converter is on and its decoder has a glyph code.
* **Measure** across R56 for V9 and R57 for V10.
* **Glyphs:** `a` lights A on V9, `p` lights P on V10, and `g` steps through every glyph. Check each glyph against the table in 5a. This is **gate 4**; a different glyph means a firmware table.
* **Current:** V_R = 185 − 140 − 1 = **44 V**, so 44 / 18 k = **2.4 mA** DC, the tube's rated indication current, and R56 dissipates 44 × 2.4 mA = 0.11 W. **Pass:** 34–54 V (sustain 130–150 V).
* R56/R57 were 8k2 (5.4 mA, twice the rating) until the electrical review (E2). If the glow is patchy at 18 k, gate 2 may lower them to 15 k (2.9 mA).

**The colon.** `k` must strike **both** ИНС-1 together.
* Each lamp gets (185 − ≈ 65 V burning voltage, assumed) / 220 kΩ = **0.55 mA**.
* Across R58 and across R59, expect **≈ 120 V**. **Pass:** 115–130 V each, and **the two within 3 V of each other**. The spec asks for a matched pair (§3).

**The backlight.** `l` steps through the LEDs. Each LED under its tube lights alone: HL1 under H10 … HL8 under ИН-15А, and HL9 is the "m" between the ИН-15s.
* Across RN1's resistor for that LED (pins 8−k and 9+k for HL(k+1)): 11 mA × 220 Ω = **2.4 V**. **Pass:** 1.8–3.0 V.
* All eight together draw 91 mA from the MCP23017, inside its 125 mA supply-pin limit.
* The "m" (HL9) is fed from D12 through R53: (4.8 − 2.0 − 0.1) / 220 Ω = **12 mA**, or 2.7 V across R53.

**Then the clock with all six tubes.** Flash BOARD_TYPE 4. Check:
* the order, H10 H1 : M10 M1 S10 S1;
* the right digits;
* **no ghosting:** in a dim room, no faint neighbouring numerals on the ИН-12s or the ИН-17s;
* **no visible flicker.**

The pair scans six slots at a **50 Hz frame and 13.5 % duty** per tube (the four-slot bench board ran 75 Hz and 20 %). This is the review's bench item on the six-slot timing: judge flicker and brightness here.

---

### Stage 7: the fascia

**Power off.** Check the PH cable is one-to-one: pin 1 to pin 1 … pin 6 to pin 6, with no pin to its neighbour. Plug it into J1. The pins are 1 +5 V, 2 GND, 3 A6, 4 A7, 5 D7, 6 D8.

**Flash the bring-up sketch** if the clock is on the Nano. Type `r`: the sketch prints A6, A7 and both buttons four times a second.

**The ADC codes are ratiometric.** The ladders hang from the same +5 V rail the ADC uses as its reference, so the codes do not depend on the rail's exact value. The spec writes ADC = 1023 × V / 5 V; the ATmega's own 1024 × V / Vref differs by less than one code.

**A6, the MODE rotary.** Five 4.7 kΩ 1 % resistors (R1–R5 on the fascia) run in series across 5 V, 23.5 kΩ in all, and the wiper takes a tap. Position *n* is (n − 1)/5 of the rail.
* **The tolerance:** with 1 % parts, the worst tap 2 is 1.01 / (1.01 + 4 × 0.99) × 1023 = 208 against the ideal 205, so ±3.3 codes. Taps 3 and 4 are ±4.9 codes. Add the ADC's ±2 LSB.
* **The firmware's window:** `rotaryPos()` in `ts06pair.ino` rounds (A6 + 102) / 205 + 1. That leaves about 100 codes either side.

| Position | Screen (spec §1, rev B) | Tap voltage | Ideal ADC | Pass | Firmware window |
|---|---|---|---|---|---|
| 1 | NORMAL | 0.00 V | 0 | 0–7 | 0–102 |
| 2 | SET TIME | 1.00 V | 205 | 198–212 | 103–307 |
| 3 | DISPLAY | 2.00 V | 409 | 402–416 | 308–512 |
| 4 | AMBIENT | 3.00 V | 614 | 607–621 | 513–717 |
| 5 | FORMAT/DATE | 4.00 V | 818 | 811–825 | 718–922 |
| 6 | INFO | 5.00 V | 1023 | 1016–1023 | 923–1023 |

The sketch prints each reading's offset from the ideal. **Record the six readings** in the unit's build log (spec §10). No code may appear between detents: the 100 nF C5 at the board end holds the last value while a non-shorting wiper is lifted. With the ladder's worst source impedance of 5.64 kΩ, that is a 0.56 ms low-pass (spec §2).

**A7, the FIELD and SUB levers.** R6 (10 kΩ) pulls A7 up. FIELD closes R7 (20 kΩ) to ground, and SUB closes R8 (10 kΩ).

| Levers | Arithmetic | Ideal ADC | Pass (1 % parts ±5, ADC ±2) | Suggested threshold |
|---|---|---|---|---|
| both open | pull-up only; pin leakage ≤ 1 µA × 10 kΩ = 2 codes | 1023 | 1016–1023 | > 852 |
| FIELD | 1023 × 20 / (10 + 20) | 682 | 675–689 | 598–852 |
| SUB | 1023 × 10 / (10 + 10) | 512 | 505–519 | 461–597 |
| both | 20 ∥ 10 = 6.67 kΩ; 1023 × 6.67 / 16.67 | 409 | 402–416 | < 461 |

The worst gap between two states is 103 codes (spec §2). **The clock does not read A7 yet** (`ts06pair.ino`, TODO). The thresholds above are the midpoints to use when it does. The sketch shows the nearest state and the offset.

**The buttons.** Press "−" (D7) and "+" (D8): the sketch shows DOWN for each. The ATmega's internal pull-ups hold them high, so the fascia needs no resistor for them.

**Then the clock.** Flash BOARD_TYPE 4.
* **SET TIME (position 2)** enters PROGRAM. The HH:MM pair blinks, "−" switches the field and "+" counts up. Turning the knob away writes the RTC with the seconds zeroed.
* **Every other position is RUN.** "−" steps the backlight mode, and holding it toggles glitch. "+" steps the transition effect.
* **The other screens are not written yet** (review 8). Always bring a pair up with the panel connected: with the fascia unplugged, A6 floats and the clock can drop into PROGRAM on its own.

---

### Stage 8: full-system soak

**Setup:**
* the clock (BOARD_TYPE 4), all tubes, the display mated and the fascia connected;
* 12 V with a 1 A limit, or the adapter you intend to ship (gate 7);
* the meter clipped on C7 before power;
* ideally, a second meter in series with the supply.

**The expected input current,** with today's firmware (ИН-15 blank, backlight on steady):

| Load | Arithmetic | mA |
|---|---|---|
| **5 V side** | | |
| Nano | typical, clones vary | 20 |
| 4 × К155ИД1 | 16 mA each, typical | 64 |
| MCP23017 + 8 LEDs | 1 + 8 × 11.4 | 92 |
| "m" LED | 12.3 | 12 |
| opto LEDs | 7.8 mA × 6 × 21/156 (always one lit, 81 % of the time) | 6 |
| LM393, VREF, RTC | 0.4 + 0.25 + 0.2 | 1 |
| **5 V total** | | **≈ 195** |
| … at 12 V, R-78E at about 87 % | 195 × 5 / 11.8 / 0.87 | **95** |
| **185 V side** | | |
| digit tubes | (4 × 6.3 + 2 × 6.5 mA) × 21/156 | 5.1 |
| colon | 2 × 0.55 mA × the fade's duty | ≈ 0.3 |
| bleeder + divider | | 0.3 |
| **185 V total** | ≈ 5.8 mA × 185 V = 1.07 W | |
| … at 12 V, converter at about 85 % | 1.07 / 0.85 / 11.8 | **107** |
| TC4420 and gate charge | | 1 |
| **Total at 12 V** | | **≈ 200 mA (2.4 W)** |

**Pass:** 150–280 mA.
* **When the ИН-15 firmware is written,** both tubes lit add 2 × 5.4 mA × 185 V = 2.0 W, which is **≈ 200 mA** more.
* **The adapter:** that puts the finished clock at about 0.4 A at 12 V, well inside the ≥ 1 A adapter assumed in gate 7.
* **The converter's ceiling:** 190 µJ × 31.4 kHz = **6.0 W**, so it has margin at both loads.

**After an hour warm:**

| Check | Expected | Pass |
|---|---|---|
| HV on C7 | 185 V | 185 ± 8 V (spec §10) |
| VT21 (IRF840) | barely warm. It switches on at zero current, since L1 empties completely each cycle. Its conduction loss is (1.27² / 3) × 0.85 Ω × 23.75 µs = 11 µJ per pulse × about 5,600 pulses a second = **60 mW** | < 45 °C; no heatsink needed |
| R-78E, К155ИД1s | warm | touchable |
| Anode resistors | ИН-12: 43 V × 6.3 mA × 13.5 % = **37 mW** each | cool |
| Colon ballasts | 120 V × 0.55 mA = **66 mW** when lit | cool |
| R56/R57 | 0.11 W each once the ИН-15 is lit; 0 today | warm, not hot |

**Over 24 hours** (spec §9 burn-in, §10 QC):
* no flicker, no ghosting, no dark or stuck numeral;
* both colon dots strike together and match;
* the backlight is even;
* **RTC drift < 2 s** against a reference clock. Do not power-cycle during the test: the clock resets the RTC to its build time at boot (review 8).

**Afterwards:** switch off and time C7 down to 10 V once more. It should take ≈ 8 s, the same as stage 3.

---

### The bench gates

These come from `knowledge/TERMINAL-06-measurements-TS06-MAIN-gates.txt`, whose gates the pair inherits, and from the review's "open before an order" list. Do them before ordering boards for ten units: the spec's "three things that will bite" include ordering before measuring.

| Gate | What is measured | Where in this plan | What it decides |
|---|---|---|---|
| 1. The stock stage's operating point | Rail and input current of the old converter | Stages 3 and 8 measure the pair's own converter instead | The converter's input budget and, with gate 7, the adapter rating |
| 2. Sustaining voltage of each tube type | Volts across a lit tube | Stage 6, from V_R: V_sustain ≈ 185 − V_R − 2 | The anode resistors: R27–R30 (6k8, "TBC"), R31–R32 (12k) and R56–R57 (18k) |
| 3. ИН-17 lead order | One lead at a time on the rig, **before soldering** | Before stage 6; stage 6 confirms the cathodes | Which lead is the anode, which is physical (the footprint's pad names). The cathode order is a firmware table |
| 4. ИН-15 pinouts | Each pad lit on the rig | Stage 6, `g` | The anode identity, which is physical. The glyph map is `GLYPH_Q`, in firmware |
| 5. ИН-17 pip projection, and the Ø20 stem | Calipers | Before stage 6 | Pip under 6.4 mm, or the footprint needs a hole. The stem confirms the 20.5 mm pitch the boards were widened for |
| 6. The RTC module | Pin labels, battery type, a charging resistor and diode (the ZS-042 defect) | Stage 4.2 | U13's socket order (copper), and whether to remove the charger with a CR2032 |
| 7. The 12 V adapter | Volts, amps, plug, polarity | Stage 8 | The adapter to ship: at least 1 A at 12 V, 5.5 × 2.1 mm, centre positive |
| PBS and PLS heights | Calipers on the batch you will buy | Assembly | The standoff length: 11 mm = 8.5 + 2.5 (review 1) |
| Colon against the M10 glass | A test fit with a real tube | Stage 6 | Whether the accepted 0.135 mm courtyard overlap is real |
| Six-slot timing | Flicker, ghosting, brightness | Stages 6 and 8 | The firmware's frame rate and duty (spec §5a) |
| Ladder thresholds on a real panel and cable | The six A6 and four A7 codes | Stage 7 | The firmware's A6/A7 tables (spec §5: measured, not calculated) |
| Trench coupon | One socketed ИН-12 at full rake in a printed trench | Case | The trench wall: 0.475 mm nominal to H10's glass |
| Firmware: `rtc.adjust()` at every boot; the stale `.hex` | — | — | A one-line fix and a rebuild before anything ships (review 8) |

---

### A record for each unit

Serial · date · 12 V idle current (stage 2) · HV at RP1 = 5 k and trimmed · RP1's final value (optional, power off: RP1 pin 1 to GND) · no-load current delta · C7 discharge time to 10 V · I²C devices · V_R steady for each tube (H10 H1 M10 M1 S10 S1, ИН-15Б, ИН-15А) · both colon ballasts · the six A6 codes and four A7 codes · full-system current · HV warm · drift over 24 h · tube batch, anode resistor values, colon pair.
