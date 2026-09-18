#!/usr/bin/env python3
"""TS06-DRV: the driver half of the two-board split. Places it, and with --route routes it.

WHAT IT IS: the board that sits BEHIND TS06-DISP on standoffs and carries everything that is not
the display - the Nano, the DS3231, the 185 V converter, the 12 V inlet and the fascia cable.
34 parts and 35 nets, against 146 and 140 on the one-board TS06-MAIN. tools/ts06split.py holds
the cut and the reasoning.

PLACED BY HAND, AND THAT IS THE POINT. TS06-MAIN packs its parts with a row packer and then
grid-searches for somewhere to put the mounting holes that the routed copper has not already
taken. The owner's two complaints about that board were both consequences: two mounting holes in
arbitrary mid-board positions, and cathode switches stuffed inside the tube sockets' pin rings.
Thirty-four parts do not need a packer. Every position below is chosen, the holes come from the
stack rather than from the copper, and nothing sits anywhere it has to be apologised for.

ORIENTATION: the USB port is proud of the BOTTOM edge, which is where the inherited AlexGyver
board puts it and what the owner asked to keep. The stacking socket faces FORWARD, into the
display board's header.
"""
import math, os, re, sys, time, uuid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ts06split as S
import ts06main as N
import pcbroute

# The connector's two halves. Same hole pattern either way - a hole goes through the board and
# does not care which face the body is on - so what differs is only the graphics and the pin
# numbering as read from that face. Which of the two variants each board wants is NOT reasoned
# about here: tools/checkstack.py proves pin n of one lands on pin n of the other, in the
# assembly's world frame, and the answer is whatever passes that.
N.FP["CONN_2x12_HDR"] = {"smd": "TS06_PinHeader_2x12_Back", "tht": "TS06_PinHeader_2x12_Back"}
N.FP["CONN_2x12_SKT"] = {"smd": "TS06_PinHeader_2x12", "tht": "TS06_PinHeader_2x12"}

VER, GEN, GENV = 20260206, "pcbnew", "10.0"
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PRETTY = os.path.join(ROOT, "PCB", "lib", "TS06.pretty")
BUILD, BOARD = "tht", "TS06-DRV"
OUT = os.environ.get("TS06_OUT") or os.path.join(ROOT, "PCB", BOARD, BOARD + ".kicad_pcb")
NS = uuid.UUID("5ec06000-7506-4000-8000-0000000000d1")
ROUTE = "--route" in sys.argv

W, H = 100.0, 70.0                          # 2720 mm2 of courtyard in 7000: 39% filled, room to route
STACK = (0.0, 26.0)                         # where this board's origin sits in TS06-DISP's frame


def _p(name, default, cast=float):
    v = os.environ.get("TS06_" + name.upper())
    return cast(v) if v not in (None, "") else default


RP = dict(via_cost=_p("via_cost", 900, int), price=_p("price", 60, int), rise=_p("rise", 1.6),
          rounds=_p("rounds", 60, int), turn=_p("turn", 15, int), bias=_p("bias", 8, int),
          decay=_p("decay", 1.0), tighten=_p("tighten", 2, int), relax=_p("relax", 4, int),
          bundle=_p("bundle", 0, int), compact=_p("compact", 0, int), cross=_p("cross", 0, int),
          tjoin=_p("tjoin", 1, int), vgrid=_p("vgrid", 0, int))


def U(s):
    return str(uuid.uuid5(NS, s))


def f(v):
    return ("%.4f" % v).rstrip("0").rstrip(".") or "0"


FP_ENV = {}


def envelope(name):
    """The courtyard box if the footprint has one, else the pads with a little margin."""
    if name in FP_ENV:
        return FP_ENV[name]
    t = open(os.path.join(PRETTY, name + ".kicad_mod"), encoding="utf8").read()
    xs, ys = [], []
    # A courtyard is drawn here as fp_line segments, and occasionally an fp_circle - not as a
    # rect. Matching the wrong one falls through to the pad box below, which is SMALLER than the
    # courtyard, and a hand placement built on it overlaps everywhere (28 collisions, 18.09.26).
    for m in re.finditer(r'\(fp_line\n\t\t\(start ([-\d.]+) ([-\d.]+)\)\n\t\t\(end ([-\d.]+) ([-\d.]+)\)'
                         r'[\s\S]*?\(layer "[FB]\.CrtYd"\)', t):
        xs += [float(m.group(1)), float(m.group(3))]
        ys += [float(m.group(2)), float(m.group(4))]
    for m in re.finditer(r'\(fp_circle\n\t\t\(center ([-\d.]+) ([-\d.]+)\)\n\t\t\(end ([-\d.]+) ([-\d.]+)\)'
                         r'[\s\S]*?\(layer "[FB]\.CrtYd"\)', t):
        cx, cy = float(m.group(1)), float(m.group(2))
        rr = abs(float(m.group(3)) - cx)
        xs += [cx - rr, cx + rr]
        ys += [cy - rr, cy + rr]
    if not xs:
        for m in re.finditer(r'\(pad "[^"]*" \w+ \w+\n\t\t\(at ([-\d.]+) ([-\d.]+)\)\n\t\t\(size ([\d.]+) ([\d.]+)\)', t):
            x, y, w, h = map(float, m.groups())
            xs += [x - w / 2 - 0.25, x + w / 2 + 0.25]
            ys += [y - h / 2 - 0.25, y + h / 2 + 0.25]
    FP_ENV[name] = (min(xs), min(ys), max(xs), max(ys))
    return FP_ENV[name]


def variant(base, rot):
    return base if rot == 0 else f"{base}_R{rot}"


PARTS = {p.ref: p for p in S.parts(S.DRV, BUILD)}
PLACED = {}


def put(ref, x, y, rot=0):
    p = PARTS[ref]
    fp = variant(p.fp(BUILD), rot)
    assert os.path.exists(os.path.join(PRETTY, fp + ".kicad_mod")), (ref, fp)
    PLACED[ref] = (fp, round(x, 3), round(y, 3))


def mid(ref, x, y, rot=0):
    """Place a part by the CENTRE OF ITS COURTYARD, not by its footprint origin. A TO-220's
    origin is at its pins and a barrel jack's is at its barrel, so placing by origin means the
    same coordinate means something different for every part and a hand layout collides for
    reasons that are invisible in the source."""
    e = envelope(variant(PARTS[ref].fp(BUILD), rot))
    put(ref, x - (e[0] + e[2]) / 2, y - (e[1] + e[3]) / 2, rot)


def box(ref, rot=0):
    e = envelope(variant(PARTS[ref].fp(BUILD), rot))
    return e[2] - e[0], e[3] - e[1]


def row(refs, x, y, rot=90, pitch=None):
    """A line of small parts along +x, each clear of the last by 0.8 mm of courtyard."""
    for r in refs:
        e = envelope(variant(PARTS[r].fp(BUILD), rot))
        w = e[2] - e[0]
        put(r, x - (e[0] + e[2]) / 2 + w / 2, y, rot)
        x += (pitch if pitch else w + 0.8)
    return x


def col(refs, x, y, rot=0, pitch=None):
    for r in refs:
        e = envelope(variant(PARTS[r].fp(BUILD), rot))
        h = e[3] - e[1]
        put(r, x, y - (e[1] + e[3]) / 2 + h / 2, rot)
        y += (pitch if pitch else h + 0.8)
    return y


# ------------------------------------------------------------------ placement
# Four bands, and every part is where it is for a reason.
#
#   top      the 12 V inlet and the 5 V rail, left to right in the order the current takes;
#            the fascia cable at the far right, as far from the converter as the board allows
#   middle   the 185 V converter, the only thing here that switches, kept in one block
#   right    the divider and trimmer that set the rail, beside the comparator that reads them
#   bottom   the Nano with its USB proud of the bottom edge, which is where the inherited
#            AlexGyver board puts it and what the owner asked to keep, and the RTC beside its
#            own I2C pins

# The 12 V inlet, left to right in the order the current takes it.
mid("XS1", 15.0, 9.0)
mid("F1", 29.0, 9.0)
mid("C8", 38.0, 9.0)
mid("U14", 49.0, 9.0)
mid("C5", 58.0, 9.0)
mid("C14", 63.0, 9.0)

# The fascia cable, top right, as far from the converter as the board allows.
mid("J1", 85.0, 9.0)

# The Nano down the left, USB 2.4 mm proud of the bottom edge - the inherited board's
# arrangement, which the owner asked to keep. Its courtyard runs off the board on purpose, and
# it occupies x 2.9 to 21.1 all the way down, so everything else lives to the right of it.
mid("U1", 18.0, H - 46.2 / 2 + 2.4)
mid("U13", 31.0, 61.0)             # DS3231 mini module, beside the Nano's A4 / A5

# The converter block. The loop that carries the switched current - inductor, MOSFET, catch
# diode, reservoir - is kept in one place and as short as the parts allow; it is the only thing
# on this board with edges fast enough to care.
mid("L1", 34.0, 26.0)
mid("VT21", 46.0, 28.0)            # TO-220, tab and all
mid("VD2", 32.0, 43.0, 90)         # the 12 V input diode, stood up beside the Nano:
                                   # 19 mm lying down reaches into the MOSFET and the driver
mid("VD1", 58.0, 20.0)             # the 185 V catch diode
mid("C7", 58.0, 29.0)              # 4u7 400 V reservoir, right beside it
mid("C10", 58.0, 36.0)
mid("C9", 71.0, 20.0)
mid("C12", 71.0, 25.0)
mid("C6", 71.0, 30.0)

# Gate driver beside the MOSFET it drives, comparator beside the divider it reads.
mid("U11", 46.0, 45.0)
mid("U12", 46.0, 58.0)

# The trimmer and the divider that set the rail, in the space right of the comparator.
mid("RP1", 68.0, 38.0)
for k, r in enumerate(["R60", "R61", "R62", "R63", "R64", "R65",
                       "R66", "R67", "R68", "R69", "R70", "R71"]):
    mid(r, 64.0 + 7.0 * (k % 3), 46.0 + 6.0 * (k // 3), 90)

# The stacking socket up the right edge, facing forward into the display board's header.
mid("XJ2", 92.0, 40.0)

# Four mounting holes, one near each corner, clear of every part: these are the standoffs the
# stack sits on and they are chosen for the mechanics, not found in the gaps left by copper.
HOLES = [(4.0, 4.0), (W - 4.0, 4.0), (4.0, H - 4.0), (W - 4.0, H - 4.0)]

# AND THE PARTS MOVE FOR THEM, not the other way round. A hole put down where the parts happened
# to leave room is how TS06-MAIN ended up with two of them stranded mid-board, and on the first
# cut of this board the bottom-left standoff landed on the Nano's own pad - which does not show
# up as a courtyard collision, because a mounting hole has no courtyard, and only surfaced as one
# net that would not route (D13, 18.09.26). So it is checked here, where it can be seen.
for hx, hy in HOLES:
    for ref, (fp, px, py) in PLACED.items():
        e = envelope(fp)
        if (px + e[0] - 1.6 < hx < px + e[2] + 1.6) and (py + e[1] - 1.6 < hy < py + e[3] + 1.6):
            raise SystemExit(f"mounting hole at ({hx}, {hy}) is inside {ref}'s courtyard "
                             f"({px+e[0]:.1f},{py+e[1]:.1f})-({px+e[2]:.1f},{py+e[3]:.1f}): "
                             f"move the part, or move the hole and say why")

missing = sorted(set(PARTS) - set(PLACED))
assert not missing, "not placed: " + " ".join(missing)

# ------------------------------------------------------------------ the file
NETS = [""] + sorted(S.nets(S.DRV, BUILD))
NI = {n: i for i, n in enumerate(NETS)}
out = []


def add(s):
    out.append(s)


def text(t, x, y, layer, size=1.0, mirror=False):
    j = "\n\t\t\t(justify mirror)" if mirror else ""
    add(f'\t(gr_text "{t}"\n\t\t(at {f(x)} {f(y)} 0)\n\t\t(layer "{layer}")\n\t\t(uuid "{U("t" + t + layer)}")\n'
        f'\t\t(effects\n\t\t\t(font\n\t\t\t\t(size {f(size)} {f(size)})\n\t\t\t\t(thickness {f(size * 0.15)})\n\t\t\t){j}\n\t\t)\n\t)')


for i, (x0, y0, x1, y1) in enumerate([(0, 0, W, 0), (W, 0, W, H), (W, H, 0, H), (0, H, 0, 0)]):
    add(f'\t(gr_line\n\t\t(start {f(x0)} {f(y0)})\n\t\t(end {f(x1)} {f(y1)})\n\t\t(stroke\n\t\t\t(width 0.1)\n'
        f'\t\t\t(type solid)\n\t\t)\n\t\t(layer "Edge.Cuts")\n\t\t(uuid "{U("edge%d" % i)}")\n\t)')
for i, (hx, hy) in enumerate(HOLES):
    add(f'\t(footprint "MountingHole_2.7mm"\n\t\t(version {VER})\n\t\t(generator "{GEN}")\n\t\t(layer "F.Cu")\n'
        f'\t\t(uuid "{U("hole%d" % i)}")\n\t\t(at {f(hx)} {f(hy)})\n\t\t(descr "M2.5 clearance, non-plated")\n'
        f'\t\t(attr exclude_from_pos_files exclude_from_bom)\n\t\t(pad "" np_thru_hole circle\n\t\t\t(at 0 0)\n'
        f'\t\t\t(size 2.7 2.7)\n\t\t\t(drill 2.7)\n\t\t\t(layers "F&B.Cu" "*.Mask")\n\t\t\t(uuid "{U("holep%d" % i)}")\n'
        f'\t\t)\n\t\t(embedded_fonts no)\n\t)')

PADS = {}                                   # (ref, pad) -> (x, y, layers, shape), nets only
DEAD = []                                   # pads with NO net: obstacles all the same
for ref, (fp, px, py) in sorted(PLACED.items()):
    p = PARTS[ref]
    src = open(os.path.join(PRETTY, fp + ".kicad_mod"), encoding="utf8").read()
    body = src[src.index("\n", src.index("(footprint")) + 1:src.rindex(")")]
    body = re.sub(r'^\t', "\t\t", body, flags=re.M)
    nets_txt = body
    for m in re.finditer(r'\(pad "([^"]*)" (\w+) (\w+)\n\t\t\t\(at ([-\d.]+) ([-\d.]+)\)\n\t\t\t\(size ([\d.]+) ([\d.]+)\)', body):
        nm = m.group(1)
        net = p.pins.get(nm)
        x, y = px + float(m.group(4)), py + float(m.group(5))
        lay = ("F.Cu", "B.Cu") if m.group(2) == "thru_hole" else (("B.Cu",) if "_Back" in fp else ("F.Cu",))
        li = tuple(0 if l == "F.Cu" else 1 for l in lay)
        w, h = float(m.group(6)), float(m.group(7))
        sh = ("circle", x, y, w / 2) if m.group(3) == "circle" else ("rect", x, y, w, h)
        if not net:
            # A PAD WITH NO NET IS STILL A PAD. Skipping them here leaves the router blind to
            # every unconnected pin, and it runs tracks straight across them: seven clearance
            # violations on the first routed TS06-DRV, all of them over an NC pin of a DIP
            # (18.09.26). They get a name of their own so nothing can ever join them.
            DEAD.append((f"NC.{ref}.{nm}", li, sh, x, y, len(li) == 2))
            continue
        PADS[ref, nm] = (x, y, li, sh)
        nets_txt = nets_txt.replace(m.group(0), m.group(0) + f'\n\t\t\t(net {NI[net]} "{net}")', 1)
    add(f'\t(footprint "TS06:{fp}"\n\t\t(layer "{"B.Cu" if "_Back" in fp else "F.Cu"}")\n\t\t(uuid "{U("fp" + ref)}")\n'
        f'\t\t(at {f(px)} {f(py)})\n\t\t(property "Reference" "{ref}"\n\t\t\t(at 0 0 0)\n\t\t\t(layer "{"B" if "_Back" in fp else "F"}.SilkS")\n'
        f'\t\t\t(hide yes)\n\t\t\t(uuid "{U("ref" + ref)}")\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 0.8 0.8)\n'
        f'\t\t\t\t\t(thickness 0.12)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n{nets_txt}\n\t)')

text(f"{BOARD}  TERMINAL-06", 45.0, H - 1.6, "B.SilkS", 1.2, True)
text("USB", 14.0, H - 0.8, "B.SilkS", 1.0, True)

# ------------------------------------------------------------------ routing
tracks = vias = 0
if ROUTE:
    rt = pcbroute.Router(W, H, hv_nets=N.HV_NETS)
    for ref, (fp, px, py) in PLACED.items():
        for (r, nm), (x, y, li, sh) in PADS.items():
            if r == ref:
                rt.paint(PARTS[ref].pins[nm], li, sh)
                if len(li) == 2:
                    rt.drill(x, y, 1.0)
    for nm, li, sh, x, y, thru in DEAD:
        rt.paint(nm, li, sh)
        if thru:
            rt.drill(x, y, 1.0)
    for hx, hy in HOLES:
        rt.hole(hx, hy, 2.7)
    pads_of = {}
    for (r, nm), v in PADS.items():
        pads_of.setdefault(PARTS[r].pins[nm], []).append(v)

    def width(n):
        # the router carries 0.35 mm at most (pcbroute.CLASSES), and these are TS06-MAIN's
        return 0.35 if n in ("GND", "+5V", "+12V") else (0.25 if n in N.HV_NETS else 0.2)

    def span(n):
        ps = pads_of[n]
        return -max(math.hypot(a[0] - b[0], a[1] - b[1]) for a in ps for b in ps)

    t0 = time.time()
    hv = sorted((n for n in pads_of if n in N.HV_NETS), key=lambda n: (span(n), n))
    for n in hv:
        rt.route_net(n, width(n), pads_of[n])
    print(f"stage 1 (high voltage): {len(hv)} nets, {len(rt.failed)} not found, {time.time()-t0:.0f} s", flush=True)

    gnd = pads_of["GND"]
    nf = len(rt.failed)
    rt.route_net("GND", 0.35, gnd, via_cost=RP["via_cost"], bias=RP["bias"])
    print(f"stage 2 (GND): {len(gnd)} pads, {len(rt.failed)-nf} not found, {time.time()-t0:.0f} s", flush=True)

    order = sorted((n for n in pads_of if n != "GND" and n not in N.HV_NETS), key=lambda n: (span(n), n))

    def opts_for(n):
        if len(pads_of[n]) >= 8:
            return {"via_cost": min(250, RP["via_cost"]), "bias": 0, "compact": 0, "bundle": 0}
        return {"via_cost": RP["via_cost"]}
    print("routing parameters: " + "  ".join(f"{k}={v}" for k, v in RP.items()), flush=True)
    nf = len(rt.failed)
    rt.negotiate([(n, width(n), pads_of[n], opts_for(n)) for n in order],
                 rounds=RP["rounds"], price=RP["price"], rise=RP["rise"], turn=RP["turn"],
                 bias=RP["bias"], decay=RP["decay"], tighten=RP["tighten"], relax=RP["relax"],
                 compact=RP["compact"], cross=RP["cross"], tjoin=RP["tjoin"], vgrid=RP["vgrid"],
                 log=lambda m: print(m, flush=True))
    print(f"stage 3 (the rest): {len(order)} nets, {len(rt.failed)-nf} not routed, {time.time()-t0:.0f} s", flush=True)
    for n in list(dict.fromkeys(fl[0] for fl in rt.failed[nf:])):
        snap, mark = rt.snapshot(), len(rt.failed)
        if rt.route_net(n, width(n), pads_of[n], via_cost=150, bias=0) == 0:
            del rt.failed[mark:]
        else:
            rt.restore(snap)
    for fl in rt.failed:
        print("  NOT ROUTED", fl)
    for k, (x1, y1, x2, y2, w, lay, n) in enumerate(rt.segments):
        add(f'\t(segment\n\t\t(start {x1:.4f} {y1:.4f})\n\t\t(end {x2:.4f} {y2:.4f})\n\t\t(width {w})\n'
            f'\t\t(layer "{lay}")\n\t\t(net {NI[n]})\n\t\t(uuid "{U("seg" + str(k))}")\n\t)')
    for k, (x, y, n) in enumerate(rt.vias):
        add(f'\t(via\n\t\t(at {x:.4f} {y:.4f})\n\t\t(size 0.8)\n\t\t(drill 0.4)\n'
            f'\t\t(layers "F.Cu" "B.Cu")\n\t\t(net {NI[n]})\n\t\t(uuid "{U("via" + str(k))}")\n\t)')
    tracks, vias = len(rt.segments), len(rt.vias)

for zl in ("F.Cu", "B.Cu"):
    add('\t(zone\n\t\t(net %d)\n\t\t(net_name "GND")\n\t\t(layers "%s")\n\t\t(uuid "%s")\n'
        '\t\t(name "GND")\n\t\t(hatch edge 0.5)\n\t\t(connect_pads thru_hole_only\n\t\t\t(clearance 0.6)\n\t\t)\n'
        '\t\t(min_thickness 0.25)\n\t\t(filled_areas_thickness no)\n'
        '\t\t(fill\n\t\t\t(thermal_gap 0.5)\n\t\t\t(thermal_bridge_width 0.5)\n\t\t\t(island_removal_mode 0)\n\t\t)\n'
        '\t\t(polygon\n\t\t\t(pts\n%s\n\t\t\t)\n\t\t)\n\t)'
        % (NI["GND"], zl, U("zone GND " + zl), "\n".join("\t\t\t\t(xy %.2f %.2f)" % pt for pt in
           ((0.5, 0.5), (W - 0.5, 0.5), (W - 0.5, H - 0.5), (0.5, H - 0.5)))))

head = [f'(kicad_pcb\n\t(version {VER})\n\t(generator "{GEN}")\n\t(generator_version "{GENV}")',
        '\t(general\n\t\t(thickness 1.6)\n\t\t(legacy_teardrops no)\n\t)', '\t(paper "A4")']
layers = ['\t(layers', '\t\t(0 "F.Cu" signal)', '\t\t(2 "B.Cu" signal)',
          '\t\t(9 "F.Adhes" user "F.Adhesive")', '\t\t(11 "B.Adhes" user "B.Adhesive")',
          '\t\t(13 "F.Paste" user)', '\t\t(15 "B.Paste" user)',
          '\t\t(5 "F.SilkS" user "F.Silkscreen")', '\t\t(7 "B.SilkS" user "B.Silkscreen")',
          '\t\t(1 "F.Mask" user)', '\t\t(3 "B.Mask" user)',
          '\t\t(17 "Dwgs.User" user "User.Drawings")', '\t\t(19 "Cmts.User" user "User.Comments")',
          '\t\t(21 "Eco1.User" user "User.Eco1")', '\t\t(23 "Eco2.User" user "User.Eco2")',
          '\t\t(25 "Edge.Cuts" user)', '\t\t(27 "Margin" user)',
          '\t\t(31 "F.CrtYd" user "F.Courtyard")', '\t\t(29 "B.CrtYd" user "B.Courtyard")',
          '\t\t(35 "F.Fab" user)', '\t\t(33 "B.Fab" user)',
          '\t\t(39 "User.1" user "Keepouts")', '\t\t(41 "User.2" user)',
          '\t\t(43 "User.3" user)', '\t\t(45 "User.4" user)', '\t)']
setup = ['\t(setup', '\t\t(pad_to_mask_clearance 0)', '\t\t(allow_soldermask_bridges_in_footprints no)',
         '\t\t(tenting\n\t\t\t(front yes)\n\t\t\t(back yes)\n\t\t)', '\t)']
netlines = ['\t(net %d "%s")' % (i, n) for i, n in enumerate(NETS)]
if not ROUTE and os.path.exists(OUT) and "--force" not in sys.argv:
    if "(segment" in open(OUT, encoding="utf8").read():
        sys.exit(f"refusing to overwrite the ROUTED {os.path.relpath(OUT, ROOT)} with an unrouted board."
                 f"{chr(10)}  add --route, --force, or set TS06_OUT.")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf8", newline="\n") as fh:
    fh.write("\n".join(head + layers + setup + netlines + out) + "\n\t(embedded_fonts no)\n)\n")
print("wrote", os.path.relpath(OUT, ROOT))
print(f"board {W} x {H} mm, {len(PLACED)} parts, {len(NETS)-1} nets, {len(HOLES)} holes, "
      f"{tracks} tracks, {vias} vias")
