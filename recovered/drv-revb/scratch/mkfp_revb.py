"""Rev B footprints for TS06-DRV: new parts, redrawn drills, silk normalised to >= 0.15 mm.

    python3 mkfp_revb.py <repo root>
"""
import math, os, sys

ROOT = sys.argv[1]
sys.path.insert(0, os.path.join(ROOT, "tools"))
import sexp as S
import pcbkit as K

PRETTY = os.path.join(ROOT, "PCB", "lib", "TS06.pretty")
SILK_W = 0.15


def prop(key, val, x, y, layer, hide=False):
    n = ["property", S.q(key), S.q(val), ["at", S.num(x), S.num(y), "0"], ["layer", S.q(layer)]]
    if hide:
        n.append(["hide", "yes"])
    n.append(["effects", ["font", ["size", "1", "1"], ["thickness", "0.15"]]])
    return n


def line(x0, y0, x1, y1, layer, w):
    return ["fp_line", ["start", S.num(x0), S.num(y0)], ["end", S.num(x1), S.num(y1)],
            ["stroke", ["width", S.num(w)], ["type", "solid"]], ["layer", S.q(layer)]]


def rect(x0, y0, x1, y1, layer, w):
    return ["fp_rect", ["start", S.num(x0), S.num(y0)], ["end", S.num(x1), S.num(y1)],
            ["stroke", ["width", S.num(w)], ["type", "solid"]], ["fill", "no"], ["layer", S.q(layer)]]


def text(t, x, y, layer, size=1.0, th=0.15, rot=0):
    return ["fp_text", "user", S.q(t), ["at", S.num(x), S.num(y), S.num(rot)], ["layer", S.q(layer)],
            ["effects", ["font", ["size", S.num(size), S.num(size)], ["thickness", S.num(th)]]]]


def pad(name, shape, x, y, w, h, drill, rr=None):
    n = ["pad", S.q(name), "thru_hole", shape, ["at", S.num(x), S.num(y)], ["size", S.num(w), S.num(h)],
         ["drill", S.num(drill)], ["layers", '"*.Cu"', '"*.Mask"'], ["remove_unused_layers", "no"]]
    if rr is not None:
        n.insert(7, ["roundrect_rratio", S.num(rr)])
    return n


def footprint(name, descr, tags, body):
    return (["footprint", S.q(name), ["version", "20260206"], ["generator", '"kicad-footprint-generator"'],
             ["layer", '"F.Cu"'], ["descr", S.q(descr)], ["tags", S.q(tags)]] + body + [["embedded_fonts", "no"]])


def write(tree):
    path = os.path.join(PRETTY, S.unq(tree[1]) + ".kicad_mod")
    with open(path, "w", encoding="utf8", newline="\n") as fh:
        fh.write(S.dump(tree) + "\n")
    print("wrote", os.path.relpath(path, ROOT))


# ---------------------------------------------------------------- МЛТ-0,5 / С2-23-0,5, lying
P, D, L, PAD, DR = 15.24, 4.2, 10.8, 1.7, 1.1
bx0, bx1 = P / 2 - L / 2, P / 2 + L / 2
s = 0.1                                      # silk line centre just outside the body
body = [prop("Reference", "REF**", P / 2, -D / 2 - 1.3, "F.SilkS"),
        prop("Value", "R_MLT-0.5", P / 2, D / 2 + 1.3, "F.Fab"),
        ["attr", "through_hole"], ["duplicate_pad_numbers_are_jumpers", "no"],
        line(PAD / 2 + 0.25, 0, bx0 - s, 0, "F.SilkS", SILK_W),
        line(P - PAD / 2 - 0.25, 0, bx1 + s, 0, "F.SilkS", SILK_W),
        rect(bx0 - s, -D / 2 - s, bx1 + s, D / 2 + s, "F.SilkS", SILK_W),
        rect(-PAD / 2 - 0.25, -D / 2 - 0.25, P + PAD / 2 + 0.25, D / 2 + 0.25, "F.CrtYd", 0.05),
        line(0, 0, bx0, 0, "F.Fab", 0.1), line(P, 0, bx1, 0, "F.Fab", 0.1),
        rect(bx0, -D / 2, bx1, D / 2, "F.Fab", 0.1),
        text("${REFERENCE}", P / 2, 0, "F.Fab"),
        pad("1", "circle", 0, 0, PAD, PAD, DR), pad("2", "circle", P, 0, PAD, PAD, DR)]
write(footprint("TS06_R_Axial_MLT-0.5_P15.24mm",
                "Resistor, 0.5 W 350 V, lying: МЛТ-0,5 / С2-23-0,5, body Ø4.2 x 10.8 mm on Ø0.8 mm leads, "
                "1.1 mm finished holes, pitch 15.24 mm. Drawn for the TERMINAL-06 THT driver board, rev B.",
                "resistor axial MLT-0.5 C2-23-0.5 0.5W", body))

# ---------------------------------------------------------------- L1: Bourns 5900 axial choke, lying
P, D, L, PAD, DR = 27.94, 11.5, 22.9, 2.0, 1.1
bx0, bx1 = P / 2 - L / 2, P / 2 + L / 2
body = [prop("Reference", "REF**", P / 2, -D / 2 - 1.3, "F.SilkS"),
        prop("Value", "L_Axial_5900", P / 2, D / 2 + 1.3, "F.Fab"),
        ["attr", "through_hole"], ["duplicate_pad_numbers_are_jumpers", "no"],
        line(PAD / 2 + 0.25, 0, bx0 - s, 0, "F.SilkS", SILK_W),
        line(P - PAD / 2 - 0.25, 0, bx1 + s, 0, "F.SilkS", SILK_W),
        rect(bx0 - s, -D / 2 - s, bx1 + s, D / 2 + s, "F.SilkS", SILK_W),
        rect(-PAD / 2 - 0.25, -D / 2 - 0.25, P + PAD / 2 + 0.25, D / 2 + 0.25, "F.CrtYd", 0.05),
        line(0, 0, bx0, 0, "F.Fab", 0.1), line(P, 0, bx1, 0, "F.Fab", 0.1),
        rect(bx0, -D / 2, bx1, D / 2, "F.Fab", 0.1),
        text("${REFERENCE}", P / 2, 0, "F.Fab"),
        pad("1", "circle", 0, 0, PAD, PAD, DR), pad("2", "circle", P, 0, PAD, PAD, DR)]
write(footprint("TS06_L_Axial_D11.5mm_L22.9mm_P27.94mm",
                "Inductor, axial, lying: Bourns 5900 series high-current choke (5900-221-RC: 220 uH, Isat 1.8 A), "
                "body Ø11.5 x 22.9 mm on Ø0.8 mm leads, 1.1 mm finished holes, pitch 27.94 mm; 11.5 mm tall. "
                "Drawn for the TERMINAL-06 THT driver board, rev B.",
                "inductor axial choke Bourns 5900", body))

# ---------------------------------------------------------------- U13: male PLS-5 for the DS3231 mini module
# Pads exactly as TS06_PinHeader_1x05 (pin 1 at the origin, pins down +y). The module's own female
# header plugs on and the module lies over the board beside the row: its body, ~14 x 16 mm, is drawn
# on the silk so that it is fitted the right way round; the legend names the module's pins.
PIT = 2.54
mod_w, mod_d = 16.0, 14.0                       # across the row, along it
my0, my1 = 2 * PIT - mod_d / 2, 2 * PIT + mod_d / 2
body = [prop("Reference", "REF**", -2.6, -2.4, "F.SilkS"),
        prop("Value", "DS3231_mini_on_PLS-5", 8.0, my1 + 1.3, "F.Fab"),
        ["attr", "through_hole"], ["duplicate_pad_numbers_are_jumpers", "no"],
        # the strip's own outline and pin-1 corner
        line(-1.4, -1.4, 1.4, -1.4, "F.SilkS", SILK_W), line(-1.4, -1.4, -1.4, 11.56, "F.SilkS", SILK_W),
        line(-1.4, 11.56, 1.4, 11.56, "F.SilkS", SILK_W), line(1.4, -1.4, 1.4, 11.56, "F.SilkS", SILK_W),
        line(-2.0, -2.0, -2.0, -0.6, "F.SilkS", SILK_W), line(-2.0, -2.0, -0.6, -2.0, "F.SilkS", SILK_W),
        # the module lying beside the strip (the + side of the row, x > 0)
        rect(2.2, my0, 2.2 + mod_w - 1.4, my1, "F.SilkS", SILK_W),
        rect(-1.77, min(-1.77, my0 - 0.25), 2.2 + mod_w - 1.4 + 0.25, max(11.93, my1 + 0.25), "F.CrtYd", 0.05),
        rect(-1.27, -1.27, 1.27, 11.43, "F.Fab", 0.1),
        rect(1.27, my0, 2.2 + mod_w - 1.4, my1, "F.Fab", 0.1),
        text("${REFERENCE}", 9.0, 2 * PIT, "F.Fab")]
for i in range(5):
    body.append(pad(str(i + 1), "rect" if i == 0 else "circle", 0, i * PIT, 1.7, 1.7, 1.0))
write(footprint("TS06_PinHeader_1x05_DS3231",
                "Male PLS-5 (2.54 mm) for the DS3231 mini module, whose own female header plugs on; pads as "
                "TS06_PinHeader_1x05, pad 1 (square) is GND. The module (~14 x 16 mm) lies over the board on the "
                "outlined side, ~15 mm tall. Drawn for the TERMINAL-06 THT driver board, rev B.",
                "pin header 1x05 DS3231 RTC module", body))

# ---------------------------------------------------------------- the decoders' sockets: oval pads
# A К155ИД1 output idles at up to ~60 V. Lines thread the socket between its pins (U2's inputs and
# 5 V, the ИН-15 decoders' wraps): with 1.6 mm round pads a 0.25 mm line in a gap is 0.345 mm from
# each pin; with pads 1.2 mm along the row (2.0 across) it is 0.545 (rev B, grill E10).
_t = S.parse(open(os.path.join(PRETTY, "TS06_DIP-16_W7.62mm_Socket.kicad_mod"), encoding="utf8").read())
_t[1] = S.q("TS06_DIP-16_W7.62mm_Socket_Oval")
for _n in _t:
    if isinstance(_n, list) and _n[0] == "pad":
        S.find(_n, "size")[1:3] = ["1.6", "1.2"]
        if _n[3] == "circle":
            _n[3] = "oval"
    if isinstance(_n, list) and _n[0] == "descr":
        _n[1] = S.q(S.unq(_n[1]) + " OVAL PADS 1.6 x 1.2 mm (1.2 along the row), so that a line threading between "
                    "two pins keeps 0.5 mm from each: the TS06-DRV decoder sockets (rev B).")
write(_t)


# ---------------------------------------------------------------- redrawn drills
def edit_pads(name, fn, descr_add):
    path = os.path.join(PRETTY, name + ".kicad_mod")
    t = S.parse(open(path, encoding="utf8").read())
    for n in t:
        if isinstance(n, list) and n[0] == "pad":
            fn(n)
        if isinstance(n, list) and n[0] == "descr" and descr_add not in S.unq(n[1]):
            n[1] = S.q(S.unq(n[1]) + " " + descr_add)
    with open(path, "w", encoding="utf8", newline="\n") as fh:
        fh.write(S.dump(t) + "\n")
    print("edited", name)


def to220(n):
    S.find(n, "size")[1:3] = ["1.7", "2.4"]
    S.find(n, "drill")[1:] = ["1.2"]


def ph(n):
    S.find(n, "size")[1:3] = ["1.3", "1.8"]
    S.find(n, "drill")[1:] = ["0.85"]


edit_pads("TS06_TO-220-3_Vertical_HV", to220,
          "REV B: 1.2 mm holes (the IRF840's 0.9 x 0.5 mm leads, Rezonit +0/-0.13) in 1.7 x 2.4 mm pads, "
          "0.84 mm between the drain and its neighbours.")
edit_pads("TS06_JST_PH_B6B-PH-K_Vertical", ph,
          "REV B: 0.85 mm holes (JST asks Ø0.70 +0.10/-0 for the 0.5 mm square posts; Rezonit's +0/-0.13 on "
          "0.85 gives 0.72-0.85) in 1.3 x 1.8 mm pads.")
t = open(os.path.join(PRETTY, "TS06_TO-220-3_Vertical_HV.kicad_mod"), encoding="utf8").read()
t = t.replace("PADS NARROWED to 1.6 x 2.4 mm oval: 0.94 mm between pads, for 185 V on the drain (IPC-2221B A6 asks 0.8).",
              "Pads 1.7 x 2.4 mm oval: 0.84 mm between pads, for 185 V on the drain (IPC-2221B A6 asks 0.8).")
open(os.path.join(PRETTY, "TS06_TO-220-3_Vertical_HV.kicad_mod"), "w", encoding="utf8", newline="\n").write(t)


# ---------------------------------------------------------------- silk >= 0.15 mm on the driver board's own footprints
def normalise(name):
    """Silk lines to 0.15 mm at least, and every silk line that would run within 0.15 mm of one of the
    footprint's own pads dropped from the library too (the board writer drops them from the board, so
    board and library then agree and KiCad does not report a library mismatch)."""
    path = os.path.join(PRETTY, name + ".kicad_mod")
    t = S.parse(open(path, encoding="utf8").read())
    changed = 0
    for n in S.walk(t):
        if isinstance(n, list) and n and n[0] in ("fp_line", "fp_rect", "fp_circle", "fp_arc", "fp_poly"):
            ly = S.find(n, "layer")
            if ly and S.unq(ly[1]).endswith("SilkS"):
                w = S.find(S.find(n, "stroke"), "width")
                if float(w[1]) < SILK_W - 1e-9:
                    w[1] = S.num(SILK_W)
                    changed += 1
        if isinstance(n, list) and n and n[0] in ("fp_text", "property"):
            ly = S.find(n, "layer")
            eff = S.find(n, "effects")
            if ly and S.unq(ly[1]).endswith("SilkS") and eff:
                f = S.find(eff, "font")
                th, sz = S.find(f, "thickness"), S.find(f, "size")
                if th is not None and float(th[1]) < SILK_W:
                    th[1] = S.num(SILK_W); changed += 1
                if sz is not None and float(sz[1]) < 1.0:
                    sz[1] = sz[2] = "1"; changed += 1
    with open(path, "w", encoding="utf8", newline="\n") as fh:
        fh.write(S.dump(t) + "\n")
    f = K.Footprint(name)
    keep = [c for c in t if not K.Board._silk_on_pad(c, f)]
    dropped = len(t) - len(keep)
    with open(path, "w", encoding="utf8", newline="\n") as fh:
        fh.write(S.dump(keep) + "\n")
    print(f"silk {name}: {changed} widened, {dropped} dropped at pads")


for name in sys.argv[2:]:
    normalise(name)
