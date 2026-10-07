#!/usr/bin/env python3
"""Design-for-manufacture check of the three TS06 boards against generic 2-layer "standard service" limits.

    python3 tools/dfm_check.py                       # TS06-DISP, TS06-DRV, TS06-FASCIA-rhythm (with its gold)
    python3 tools/dfm_check.py TS06-DRV              # one board
    python3 tools/dfm_check.py --gold ladder         # the fascia with another gold (default divider; none = bare)
    python3 tools/dfm_check.py --no-selftest         # skip the deliberately broken copy (G7)
    python3 tools/dfm_check.py --g11                 # the G11 conditions, measured on the fascia with its gold
    python3 tools/dfm_check.py --committed-holes     # the fascia R as committed (8.8 / 8.0 holes), NOT the ordered one: its zip is
                                                     # fab/TS06-FASCIA-R-rev<REV>-<gold>-notordered-fab.zip (tools/mkfab.sh --committed-holes);
                                                     # the ordered fascia has every control hole opened 0.4 mm (fab/HOLES-VARIANT.md): its zip
                                                     # fab/TS06-FASCIA-R-rev<REV>-<gold>-holes04-fab.zip is the default here (--open-holes says so; REV is the board's title block: B since the upright J1);
                                                     # with no board named it checks that one board; works with --g11 too
    python3 tools/dfm_check.py --open-holes --leaders level   # the same for another leader style (slope, level, dogleg, centred;
                                                     # tools/fascia_art.py): its zip is the one tools/mkfab.sh --leaders level wrote

THE LIMITS ARE INFERRED. They are what a typical low-cost 2-layer service quotes as its standard class; no fab
was asked and no price or page was fetched. The owner checks them against the fab chosen:

    track width >= 0.15 mm            copper clearance >= 0.15 mm        annular ring >= 0.15 mm
    plated drill >= 0.3 mm            non-plated drill >= 0.5 mm         hole to hole (wall to wall) >= 0.5 mm
    copper to board edge >= 0.3 mm    silk line >= 0.15 mm               silk text height >= 1.0 mm
    solder-mask sliver >= 0.1 mm      board within 400 x 500 mm

TWO SIDES, each able to fail.
  1. KiCad 10's DRC (Docker, as tools/verify_pair.sh) on a scratch copy of each board (the fascia is the art
     board with its gold, built by tools/fascia_gold.py): the board's own .kicad_dru, with the fab limits as
     rules named "fab: ..." in front of it (the board's own rules, such as the HV pad rule, still win where they
     apply). So that the table can say how close each rule gets, the rules are written at a PROBE value above
     the limit; KiCad then reports every item pair below the probe with its actual value, and a rule FAILs when
     the smallest actual value is below the limit. Where nothing is under the probe the worst value is shown as
     "over <probe>". The pour's clearance and edge distance are checked at the limits themselves, so that
     the probe does not pull the pour back.
  2. tools/gerbers.py reads the fab zips themselves (no KiCad): the smallest silk aperture, the smallest drill
     in each drill file, the board size from the outline, and the narrowest solder-mask web (rasterised at
     0.025 mm a pixel, so about +-0.03 mm).

KiCad has no rule for a silk LINE's width (only for text, which the DRC rows cover) or for mask slivers (it
checks only apertures that bridge different nets, shown as extra information); the Gerber rows cover both.

SELF-TEST (grill G7). A copy of TS06-DISP with one planted fault per rule is put through the same two sides
(and plotted to Gerbers for the second); every row must show FAIL, or this script exits 1 because a check that
cannot fail proves nothing.
"""
import argparse, collections, json, math, os, re, shutil, subprocess, sys, tempfile, uuid, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import gerbers as GB

IMG = os.environ.get("KICAD_IMAGE", "mirror.gcr.io/kicad/kicad:10.0")
LAYERS = "F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts"

# id, label, limit (mm), probe (mm, for the DRC rules), what the number is
RULES = [
    ("track", "track width", 0.15, 0.30),
    ("clear", "copper clearance", 0.15, 0.40),
    ("pth", "plated drill", 0.30, 0.60),
    ("npth", "non-plated drill", 0.50, 1.00),
    ("ring", "annular ring", 0.15, 0.40),
    ("edge", "copper to board edge", 0.30, 0.80),
    ("h2h", "hole to hole (wall to wall)", 0.50, 1.00),
    ("silkw", "silk line (text stroke, DRC)", 0.15, 0.25),
    ("silkh", "silk text height", 1.00, 1.50),
]
LIM = {r[0]: r[2] for r in RULES}
PROBE = {r[0]: r[3] for r in RULES}
LABEL = {r[0]: r[1] for r in RULES}
MASK_WEB, MAX_SIZE = 0.10, (500.0, 400.0)       # mm; the board must fit 500 x 400 either way round

BOARDS = {
    "TS06-DISP": dict(name="TS06-DISP", zip="fab/TS06-DISP-revB-fab.zip"),
    "TS06-DRV": dict(name="TS06-DRV", zip="fab/TS06-DRV-revB-fab.zip"),
    "TS06-FASCIA-rhythm": dict(name="TS06-FASCIA-rhythm", zip=None),      # named after the gold
}


def fab_rules(probe):
    v = (lambda k: PROBE[k]) if probe else (lambda k: LIM[k])
    return """(version 1)
(rule "fab: track width" (constraint track_width (min %.3fmm)))
(rule "fab: copper clearance" (condition "A.Type != 'Zone' && B.Type != 'Zone'") (constraint clearance (min %.3fmm)))
(rule "fab: copper clearance, pour" (condition "A.Type == 'Zone' || B.Type == 'Zone'") (constraint clearance (min %.3fmm)))
(rule "fab: plated drill" (condition "A.Pad_Type == 'Through-hole'") (constraint hole_size (min %.3fmm)))
(rule "fab: non-plated drill" (condition "A.Pad_Type == 'NPTH, mechanical'") (constraint hole_size (min %.3fmm)))
(rule "fab: annular ring" (constraint annular_width (min %.3fmm)))
(rule "fab: copper to edge" (condition "A.Type != 'Zone'") (constraint edge_clearance (min %.3fmm)))
(rule "fab: copper to edge, pour" (condition "A.Type == 'Zone'") (constraint edge_clearance (min %.3fmm)))
(rule "fab: hole to hole" (constraint hole_to_hole (min %.3fmm)))
(rule "fab: silk text stroke front" (layer "F.SilkS") (constraint text_thickness (min %.3fmm)))
(rule "fab: silk text stroke back" (layer "B.SilkS") (constraint text_thickness (min %.3fmm)))
(rule "fab: silk text height front" (layer "F.SilkS") (constraint text_height (min %.3fmm)))
(rule "fab: silk text height back" (layer "B.SilkS") (constraint text_height (min %.3fmm)))
""" % (v("track"), v("clear"), LIM["clear"], v("pth"), v("npth"), v("ring"), v("edge"), LIM["edge"], v("h2h"),
       v("silkw"), v("silkw"), v("silkh"), v("silkh"))


# ================================================================================ KiCad
def kicad(tmp, args):
    cli = os.environ.get("KICAD_CLI")
    if cli:
        cmd = [cli] + args
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=tmp)
    else:
        cmd = ["docker", "run", "--rm", "--user", "%d:%d" % (os.getuid(), os.getgid()), "-v", tmp + ":/w", "-w", "/w",
               "-e", "HOME=/tmp", IMG, "kicad-cli"] + args
        r = subprocess.run(cmd, capture_output=True, text=True)
    return r


def open_up(tmp):
    for r, ds, fs in os.walk(tmp):
        os.chmod(r, 0o777)
        for f in fs:
            os.chmod(os.path.join(r, f), 0o666)


LEADERS = os.environ.get("TS06_LEADERS", "level")      # the fascia R's leader style (--leaders); level is the owner's pick (2026-10-02)


def fascia_zip(gold, open_holes=False):
    """The fascia R's zip in fab/: named after the gold, after the leader style when it is not level, and after the opened
    holes of the variant (tools/mkfab.sh names it the same way)."""
    return os.path.join(ROOT, "fab", "TS06-FASCIA-R-rev%s-%s%s%s-fab.zip" % (
        fascia_rev(), "bare" if gold == "none" else gold, "" if LEADERS == "level" else "-" + LEADERS,
        "-holes04" if open_holes else "-notordered"))


def fascia_rev():
    """The fascia R's revision, from its title block, as tools/mkfab.sh reads it (so the zip's name agrees with it)."""
    m = re.search(r'^\s*\(rev "([^"]*)"\)', open(os.path.join(ROOT, "PCB", "TS06-FASCIA-rhythm", "TS06-FASCIA-rhythm.kicad_pcb"),
                                                  encoding="utf8").read(), re.M)
    return m.group(1) if m else "X"


def scratch(key, gold, mutate=None, open_holes=False):
    """A scratch project of one board: returns (tmp dir, project name). The fascia is the art board of its gold.
    open_holes (fascia only): the base board is the generator's with every control hole opened (tools/mkpcb_fascia_rhythm.py --open-holes)."""
    tmp = tempfile.mkdtemp(prefix="dfm.")
    shutil.copytree(os.path.join(ROOT, "PCB", "lib"), os.path.join(tmp, "PCB", "lib"))
    name = "board"
    proj = os.path.join(tmp, "PCB", name)
    os.makedirs(proj)
    src = os.path.join(ROOT, "PCB", key)
    pcb = os.path.join(proj, name + ".kicad_pcb")
    base, base_args = os.path.join(src, key + ".kicad_pcb"), []
    if open_holes:
        if key != "TS06-FASCIA-rhythm":
            shutil.rmtree(tmp, ignore_errors=True)
            sys.exit("--open-holes applies to TS06-FASCIA-rhythm only")
        base = os.path.join(tmp, "base-open.kicad_pcb")
        r = subprocess.run([sys.executable, os.path.join(HERE, "mkpcb_fascia_rhythm.py"), "--out", base, "--open-holes"], capture_output=True, text=True)
        if r.returncode != 0:
            shutil.rmtree(tmp, ignore_errors=True)
            sys.exit("tools/mkpcb_fascia_rhythm.py --open-holes failed:\n%s%s" % (r.stdout, r.stderr))
        base_args = ["--base-pcb", base]
    if key == "TS06-FASCIA-rhythm" and gold != "none":
        r = subprocess.run([sys.executable, os.path.join(HERE, "fascia_gold.py"), gold, pcb, "--base", "R"] + base_args, capture_output=True, text=True)
        if r.returncode != 0:
            shutil.rmtree(tmp, ignore_errors=True)
            sys.exit("tools/fascia_gold.py %s --base R failed its own checks:\n%s%s" % (gold, r.stdout, r.stderr))
    else:
        shutil.copy(base, pcb)
    if mutate:
        t = open(pcb, encoding="utf8").read()
        open(pcb, "w", encoding="utf8").write(mutate(t))
    shutil.copy(os.path.join(src, key + ".kicad_pro"), os.path.join(proj, name + ".kicad_pro"))
    shutil.copy(os.path.join(src, "fp-lib-table"), os.path.join(proj, "fp-lib-table"))
    own = ""
    p = os.path.join(src, key + ".kicad_dru")
    if os.path.exists(p):
        own = re.sub(r"^\s*\(version 1\)\s*", "", open(p, encoding="utf8").read())
    open(os.path.join(proj, name + ".kicad_dru"), "w").write(fab_rules(True) + own)
    open_up(tmp)
    return tmp, name


def drc(tmp, name):
    """KiCad's DRC with the fab rules: [violation dicts]. Zones are refilled."""
    out = "drc.json"
    r = kicad(tmp, ["pcb", "drc", "--refill-zones", "--severity-all", "--units", "mm", "--format", "json", "-o", "/w/" + out if not os.environ.get("KICAD_CLI") else out,
                    ("/w/" if not os.environ.get("KICAD_CLI") else "") + "PCB/%s/%s.kicad_pcb" % (name, name)])
    p = os.path.join(tmp, out)
    if not os.path.exists(p):
        sys.exit("kicad-cli DRC failed:\n" + r.stdout + r.stderr)
    return json.load(open(p, encoding="utf8")).get("violations", [])


def plot(tmp, name):
    """Gerbers and drills of the scratch board (the planted copy has no zip), into tmp/out."""
    pre = "/w/" if not os.environ.get("KICAD_CLI") else ""
    pcb = pre + "PCB/%s/%s.kicad_pcb" % (name, name)
    o = pre + "out/" if pre else "out/"
    os.makedirs(os.path.join(tmp, "out"), exist_ok=True)
    open_up(tmp)
    kicad(tmp, ["pcb", "export", "gerbers", "--check-zones", "--layers", LAYERS, "-o", o, pcb])
    kicad(tmp, ["pcb", "export", "drill", "--format", "excellon", "--excellon-units", "mm", "--excellon-separate-th",
                "--generate-map", "--map-format", "gerberx2", "-o", o, pcb])
    return os.path.join(tmp, "out")


# ================================================================================ readings
def parse_violations(vs):
    """{rule id: (smallest actual, [(actual, text, pos)])} for the fab rules; other violations are counted by type."""
    ids = {"fab: track width": "track", "fab: copper clearance": "clear", "fab: copper clearance, pour": "clear",
           "fab: plated drill": "pth", "fab: non-plated drill": "npth", "fab: annular ring": "ring",
           "fab: copper to edge": "edge", "fab: copper to edge, pour": "edge", "fab: hole to hole": "h2h",
           "fab: silk text stroke front": "silkw", "fab: silk text stroke back": "silkw",
           "fab: silk text height front": "silkh", "fab: silk text height back": "silkh"}
    got = collections.defaultdict(list)
    other = collections.Counter()
    unparsed = []
    for v in vs:
        d = v["description"]
        m = re.search(r"rule '([^']+)'", d)
        a = re.search(r"actual ([\d.]+) mm", d)
        if m and m.group(1) in ids:
            rid = ids[m.group(1)]
            if not a:
                unparsed.append(d)
                continue
            its = v.get("items") or [{}]
            got[rid].append((float(a.group(1)), its[0].get("description", ""), its[0].get("pos", {})))
        else:
            other[(v["severity"], v["type"])] += 1
    return got, other, unparsed


def edge_box(text):
    """The Edge.Cuts extent of a board file: (x0, y0, x1, y1)."""
    xs, ys = [], []
    for m in re.finditer(r"\((?:gr_line|gr_arc|gr_rect|gr_circle|gr_poly)\b[\s\S]*?\(layer \"Edge\.Cuts\"\)", text):
        blk = m.group(0)
        if blk.startswith("(gr_circle"):
            c = re.search(r"\(center ([-\d.]+) ([-\d.]+)\)", blk)
            e = re.search(r"\(end ([-\d.]+) ([-\d.]+)\)", blk)
            r = math.hypot(float(e.group(1)) - float(c.group(1)), float(e.group(2)) - float(c.group(2)))
            xs += [float(c.group(1)) - r, float(c.group(1)) + r]
            ys += [float(c.group(2)) - r, float(c.group(2)) + r]
            continue
        for x, y in re.findall(r"\((?:start|mid|end|xy) ([-\d.]+) ([-\d.]+)\)", blk):
            xs.append(float(x))
            ys.append(float(y))
    return (min(xs), min(ys), max(xs), max(ys))


def fits(w, h):
    return max(w, h) <= MAX_SIZE[0] + 1e-9 and min(w, h) <= MAX_SIZE[1] + 1e-9


def measure(key, tmp, name, files, show_drc_other=True):
    """Every row for one board: [(group, rule, limit text, worst text, ok, how, detail lines)] and the extras."""
    rows = []
    vs = drc(tmp, name)
    got, other, unparsed = parse_violations(vs)
    if unparsed:
        sys.exit("DRC lines without a value:\n  " + "\n  ".join(unparsed[:5]))
    for rid, label, limit, probe in RULES:
        h = got.get(rid, [])
        if h:
            worst = min(h, key=lambda t: t[0])
            ok = worst[0] >= limit - 1e-9
            text = "%.3f mm" % worst[0]
            detail = []
            if not ok:
                bad = sorted(x for x in h if x[0] < limit - 1e-9)
                detail = ["%.3f mm at (%.2f, %.2f): %s" % (x[0], x[2].get("x", 0), x[2].get("y", 0), x[1]) for x in bad[:3]]
                if len(bad) > 3:
                    detail.append("... %d more below the limit" % (len(bad) - 3))
        else:
            ok, text, detail = True, "over %.2f mm" % probe, []
        rows.append(("KiCad DRC", label, ">= %.2f mm" % limit, text, ok, "DRC, probe %.2f" % probe, detail))
    # the Gerber side
    r = GB.readings(files)
    for a, mn, cnt in r["silk"]:
        ok = mn is None or mn >= LIM["silkw"] - 1e-9
        rows.append(("Gerber, from the zip", "smallest silk aperture", ">= 0.15 mm",
                     "no silk" if mn is None else "%.3f mm" % mn, ok, a.split("-", 1)[-1], [] if ok else ["%s: %.3f mm" % (a, mn)]))
    for tag, label, lim in (("PTH", "smallest plated drill", LIM["pth"]), ("NPTH", "smallest non-plated drill", LIM["npth"])):
        mn, hits, tools = r["drills"][tag]
        ok = mn is None or mn >= lim - 1e-9
        rows.append(("Gerber, from the zip", label, ">= %.2f mm" % lim, ("none: no such holes" if mn is None else "%.3f mm (%d holes)" % (mn, hits)),
                     ok, "%s.drl" % tag, [] if ok else ["tools %s" % ", ".join("%.3f" % t for t in tools)]))
    w, h = r["size"]
    ok = fits(w, h)
    rows.append(("Gerber, from the zip", "board size, from the outline", "within 500 x 400 mm", "%.2f x %.2f mm" % (w, h), ok, "Edge_Cuts.gm1", []))
    for tag, lbl in (("F_Mask", "front"), ("B_Mask", "back")):
        worst, ok, where = GB.mask_web(files, tag, MASK_WEB)
        rows.append(("Gerber, from the zip", "narrowest solder-mask web, " + lbl, ">= %.2f mm" % MASK_WEB,
                     "over %.2f mm" % (14 / GB.PPM) if worst is None else "%.3f mm" % worst, ok, "%s raster, +-0.03 mm" % tag.replace("_", "."),
                     ["thin web at (%.2f, %.2f), %.3f mm2 (Gerber y is up: the board's y is %.2f)" % (x, y, a, -y) for x, y, a in where]))
    # the board file's own outline (the DRC side of the size rule)
    pcb = open(os.path.join(tmp, "PCB", name, name + ".kicad_pcb"), encoding="utf8").read()
    x0, y0, x1, y1 = edge_box(pcb)
    rows.append(("KiCad DRC", "board size, from the board file's outline", "within 500 x 400 mm", "%.2f x %.2f mm" % (x1 - x0, y1 - y0),
                 fits(x1 - x0, y1 - y0), "Edge.Cuts", []))
    return rows, other


def table(title, rows, other, extra=()):
    print(title)
    print()
    print("| Side | Rule | Limit (inferred) | Worst value | Result | Read from |")
    print("|---|---|---|---|---|---|")
    for side, rule, lim, worst, ok, how, detail in rows:
        print("| %s | %s | %s | %s | %s | %s |" % (side, rule, lim, worst, "PASS" if ok else "**FAIL**", how))
    bad = [(r[1], r[6]) for r in rows if not r[4]]
    for rule, detail in bad:
        for d in detail:
            print("    %s: %s" % (rule, d))
    for e in extra:
        print("    " + e)
    if other:
        print("    Also in KiCad's report, under the board's own rules (not counted here; tools/verify_pair.sh accepts them): " +
              ", ".join("%s %s x%d" % (k[0], k[1], n) for k, n in sorted(other.items())))
    print()


# ================================================================================ the broken copy
def plant(text):
    """A scratch board with one planted fault for every rule: TS06-DISP's header (layers, setup, nets) with a 520 x 30 mm
    outline and the faults on it, so that nothing of the real board gets in the way. Nothing under PCB/ is written."""
    def U():
        return str(uuid.uuid4())

    def seg(x0, y0, x1, y1, w, layer, net):
        return '\t(segment\n\t\t(start %s %s)\n\t\t(end %s %s)\n\t\t(width %s)\n\t\t(layer "%s")\n\t\t(net %d)\n\t\t(uuid "%s")\n\t)\n' % (
            x0, y0, x1, y1, w, layer, net, U())

    def fp(ref, x, y, pads):
        ps = ""
        for num, typ, shape, dx, size, drill, net in pads:
            n = '\n\t\t\t(net %d "%s")' % net if net else ""
            ps += '\t\t(pad "%s" %s %s\n\t\t\t(at %s 0)\n\t\t\t(size %s %s)\n\t\t\t(drill %s)\n\t\t\t(layers "*.Cu" "*.Mask")%s\n\t\t\t(uuid "%s")\n\t\t)\n' % (
                num, typ, shape, dx, size, size, drill, n, U())
        return ('\t(footprint "plant:%s"\n\t\t(layer "F.Cu")\n\t\t(uuid "%s")\n\t\t(at %s %s)\n\t\t(property "Reference" "%s"\n\t\t\t(at 0 0 0)\n\t\t\t(hide yes)\n'
                '\t\t\t(layer "F.Fab")\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1 1)\n\t\t\t\t\t(thickness 0.15)\n\t\t\t\t)\n\t\t\t)\n\t\t\t(uuid "%s")\n\t\t)\n%s\t)\n') % (
            ref, U(), x, y, ref, U(), ps)

    def rect(x0, y0, x1, y1, layer, fill="yes", w=0):
        return '\t(gr_rect\n\t\t(start %s %s)\n\t\t(end %s %s)\n\t\t(stroke\n\t\t\t(width %s)\n\t\t\t(type solid)\n\t\t)\n\t\t(fill %s)\n\t\t(layer "%s")\n\t\t(uuid "%s")\n\t)\n' % (
            x0, y0, x1, y1, w, fill, layer, U())

    def line(x0, y0, x1, y1, w, layer):
        return '\t(gr_line\n\t\t(start %s %s)\n\t\t(end %s %s)\n\t\t(stroke\n\t\t\t(width %s)\n\t\t\t(type solid)\n\t\t)\n\t\t(layer "%s")\n\t\t(uuid "%s")\n\t)\n' % (
            x0, y0, x1, y1, w, layer, U())

    cut = min(i for i in (text.find("\n\t(footprint"), text.find("\n\t(segment"), text.find("\n\t(gr_"), text.find("\n\t(zone")) if i > 0)
    nets = dict((int(a), b) for a, b in re.findall(r'\n\t\(net (\d+) "([^"]*)"\)', text))
    n1, n2 = 1, 2
    items = rect(0, 0, 520, 30, "Edge.Cuts", "no", 0.1)                  # the outline: 520 mm long
    items += seg(10, 10, 14, 10, 0.10, "B.Cu", n1)                       # track width 0.10
    items += seg(20, 10, 24, 10, 0.2, "B.Cu", n1)                        # clearance: 0.10 between two nets
    items += seg(20, 10.3, 24, 10.3, 0.2, "B.Cu", n2)
    items += seg(30, 0.35, 34, 0.35, 0.2, "B.Cu", n1)                    # copper about 0.2 from the top edge
    items += fp("ZZ1", 40, 15, [("1", "thru_hole", "circle", 0, 0.45, 0.2, (n1, nets[n1]))])   # plated 0.2; ring 0.125
    items += fp("ZZ2", 45, 15, [("", "np_thru_hole", "circle", 0, 0.3, 0.3, None)])            # non-plated 0.3
    items += fp("ZZ3", 50, 15, [("1", "thru_hole", "circle", 0, 1.6, 0.8, (n2, nets[n2])),
                                ("2", "thru_hole", "circle", 1.0, 1.6, 0.8, (n2, nets[n2]))])  # holes 0.2 apart wall to wall
    items += ('\t(gr_text "x"\n\t\t(at 55 15 0)\n\t\t(layer "F.SilkS")\n\t\t(uuid "%s")\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 0.6 0.6)\n\t\t\t\t(thickness 0.1)\n\t\t\t)\n\t\t)\n\t)\n' % U())
    items += line(10, 20, 15, 20, 0.1, "F.SilkS") + line(10, 22, 15, 22, 0.1, "B.SilkS")     # silk lines 0.10
    items += rect(20, 20, 22, 22, "F.Mask") + rect(22.06, 20, 24.06, 22, "F.Mask")           # mask webs of 0.06
    items += rect(30, 20, 32, 22, "B.Mask") + rect(32.06, 20, 34.06, 22, "B.Mask")
    return text[:cut] + "\n" + items + ")\n"


def selftest():
    print("SELF-TEST (grill G7): TS06-DISP with one planted fault per rule, through the same two sides")
    print()
    tmp, name = scratch("TS06-DISP", "none", mutate=plant)
    try:
        files = GB.load(plot(tmp, name))
        rows, other = measure("TS06-DISP", tmp, name, files)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    table("Planted copy (every row must say FAIL):", rows, other)
    stuck = [r[1] for r in rows if r[4]]
    if stuck:
        print("SELF-TEST FAILED: these checks stayed PASS on a copy that breaks them: " + "; ".join(stuck))
        return False
    print("SELF-TEST PASSED: all %d rows FAIL on the broken copy." % len(rows))
    print()
    return True


# ================================================================================ G11
def g11(gold, open_holes=False):
    """The two G11 conditions that a board file can answer, measured on the fascia R with its gold: the legend height and
    the boss-to-R5 margin against typical fab tolerances. The dry fit of a real КМД1 and МТ1 needs parts (G14)."""
    import fascia_art as fa
    import fascia_gold as fg
    fa.LEADERS = LEADERS
    TOL_OUTLINE, TOL_HOLE, BOSS_R = 0.2, 0.1, 3.5       # mm: outline +-0.2 and hole position +-0.1 are INFERRED fab tolerances;
    print("G11 conditions on the fascia R with the %s gold%s (measured from the art board that tools/fascia_gold.py builds, and its Gerbers)" % (
        gold, ", control holes opened 0.4 mm (as ordered)" if open_holes else ", control holes as committed (NOT ordered)"))
    print()
    tmp, name = scratch("TS06-FASCIA-rhythm", gold, open_holes=open_holes)
    try:
        text = open(os.path.join(tmp, "PCB", name, name + ".kicad_pcb"), encoding="utf8").read()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    # 1. the legends: font height, and the capital height the silk Gerber really draws
    legends = [(m.group(1), float(m.group(2))) for m in re.finditer(
        r'\(gr_text "([^"]*)"\s+\(at [^)]*\)\s+\(layer "F\.SilkS"[^)]*\)\s+\(uuid "[^"]*"\)\s+\(effects\s+\(font\s+\(size ([\d.]+) [\d.]+\)', text)]
    if not legends:
        sys.exit("no front legends found in the art board")
    src = open(fa.BASES["R"], encoding="utf8").read()
    A = fg.silk_base(fa.geometry(src))
    z = GB.load(fascia_zip(gold, open_holes))
    sg = GB.Gerber(z["F_Silk"])
    drawn = []
    for it in A.items:
        if it["kind"] != "text":
            continue
        x0, y0, x1, y1 = fa.text_box(it)
        ys = []
        for p in sg.prims:
            if p[0] == "draw" and all(x0 - 0.2 <= q[0] <= x1 + 0.2 and -(y1 + 0.2) <= q[1] <= -(y0 - 0.2) for q in p[1]):
                ys += [q[1] for q in p[1]]
                w = p[2]
        if ys:
            drawn.append((it["s"], max(ys) - min(ys) + w))
    mn = min(h for _, h in legends)
    print("1. Legend height (condition: at least 3 mm)")
    print("   %d legends on the front silk, font height %.1f to %.1f mm: %s" % (
        len(legends), mn, max(h for _, h in legends), ", ".join("%s %.1f" % t for t in legends)))
    print("   the capital height the silk Gerber draws (stroke centre-lines plus one stroke width): %s" %
          ", ".join("%s %.2f" % t for t in drawn))
    print("   -> %s: the shortest legend is %.1f mm tall as set (font height, the measure fascia_art.py's own 3 mm rule uses)%s" % (
        "PASS" if mn >= 3.0 - 1e-9 else "FAIL", mn,
        "; the drawn capitals are %.2f to %.2f mm" % (min(h for _, h in drawn), max(h for _, h in drawn)) if drawn else ""))
    # 2. the boss-to-R5 margin
    fps = [m.start() for m in re.finditer(r"\n\(footprint ", text)] + [len(text)]
    holes, r5 = [], None
    for i in range(len(fps) - 1):
        blk = text[fps[i]:fps[i + 1]]
        ref = re.search(r'\(property "Reference" "([^"]*)"', blk).group(1)
        at = re.search(r"\n\t\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)", blk)
        x, y = float(at.group(1)), float(at.group(2))
        if ref.startswith("H"):
            holes.append((ref, x, y))
        if ref == "R5":
            cx = [float(a) for a in re.findall(r"\(fp_line\s*\(start ([-\d.]+) [-\d.]+\)\s*\(end [-\d.]+ [-\d.]+\)[\s\S]*?\(layer \"[BF]\.CrtYd\"\)", blk)]
            cx += [float(a) for a in re.findall(r"\(fp_line\s*\(start [-\d.]+ [-\d.]+\)\s*\(end ([-\d.]+) [-\d.]+\)[\s\S]*?\(layer \"[BF]\.CrtYd\"\)", blk)]
            pads = [(float(a), float(w)) for a, w in re.findall(r'\(pad "[12]" smd \w+\s+\(at ([-\d.]+) [-\d.]+\)\s+\(size ([\d.]+) ', blk)]
            r5 = (x, y, min(cx), min(a - w / 2 for a, w in pads))
    h = [(ref, x, y) for ref, x, y in holes if x < 20 and y > 20][0]
    court_left, pad_left = r5[0] + r5[2], r5[0] + r5[3]
    gap_c, gap_p = court_left - (h[1] + BOSS_R), pad_left - (h[1] + BOSS_R)
    left_c, left_p = gap_c - TOL_OUTLINE - TOL_HOLE, gap_p - TOL_OUTLINE - TOL_HOLE
    print()
    print("2. Boss to R5 (condition: the 1.7 mm margin holds against fab tolerance)")
    print("   the bottom-left hole %s at (%.2f, %.2f); a +-%.1f mm boss presses on the fascia's back round it (the case check's boss, 3d/case-pair);" % (h[0], h[1], h[2], BOSS_R))
    print("   R5 at (%.2f, %.2f): its courtyard's left edge x %.2f, its pad's left edge x %.2f" % (r5[0], r5[1], court_left, pad_left))
    print("   nominal margin: %.2f mm to R5's courtyard (the 1.7 mm of G11), %.2f mm to R5's pad copper" % (gap_c, gap_p))
    print("   fab tolerance, INFERRED: outline +-%.1f mm, hole position +-%.1f mm; worst case both against us, added: %.1f mm" % (TOL_OUTLINE, TOL_HOLE, TOL_OUTLINE + TOL_HOLE))
    print("   -> margin left: %.2f mm to the courtyard, %.2f mm to the pad copper (%.2f / %.2f if the two add as squares)" % (
        left_c, left_p, gap_c - math.hypot(TOL_OUTLINE, TOL_HOLE), gap_p - math.hypot(TOL_OUTLINE, TOL_HOLE)))
    print("   -> %s: the boss still clears R5's courtyard by %.2f mm in the worst case" % ("PASS" if left_c > 0 else "FAIL", left_c))
    print("   The dry fit of a real КМД1 and МТ1 needs the parts: open for the prototype (G14).")
    print()
    return mn >= 3.0 - 1e-9 and left_c > 0


# ================================================================================ main
def run_board(key, gold, open_holes=False):
    spec = BOARDS[key]
    if key == "TS06-FASCIA-rhythm":
        z = fascia_zip(gold, open_holes)
    else:
        z = os.path.join(ROOT, spec["zip"])
    if not os.path.exists(z):
        sys.exit("%s is missing: run tools/mkfab.sh first" % os.path.relpath(z, ROOT))
    files = GB.load(z)
    tmp, name = scratch(key, gold, open_holes=open_holes)
    try:
        rows, other = measure(key, tmp, name, files)
        extra = []
        if key == "TS06-FASCIA-rhythm" and gold != "none":
            ok, lines, st = GB.gold_check(files)
            bad_ok, bad_lines, bad = GB.gold_check(files, selftest=True)
            rows.append(("Gerber, from the zip", "gold exposed: F.Mask openings over the F.Cu gold", "no gold under mask",
                         "%.2f mm2 under mask; %d thin webs; %.0f%% of the gold open" % (st["under_mm2"], st["webs"], st["pct"]), ok, "F_Cu, F_Mask raster",
                         [] if ok else lines))
            rows.append(("self-test", "the same check on a mask without the gold's openings", "must FAIL",
                         "%.0f mm2 under mask: FAIL, as it must" % bad["under_mm2"] if not bad_ok else "PASS: the check cannot fail",
                         not bad_ok, "F_Mask, openings dropped", []))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    rev = re.search(r"-rev([A-Z0-9]+)-", os.path.basename(z))
    title = "%s rev %s%s%s, zip %s" % (key, rev.group(1) if rev else "?", "" if key != "TS06-FASCIA-rhythm" else ", gold %s" % gold,
                                       ("" if key != "TS06-FASCIA-rhythm" else ", control holes opened 0.4 mm (as ordered)" if open_holes else ", control holes as committed (NOT ordered)"),
                                       os.path.relpath(z, ROOT))
    table(title, rows, other, extra)
    return all(r[4] for r in rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("boards", nargs="*", help="any of %s (default: all three)" % ", ".join(BOARDS))
    ap.add_argument("--gold", default="divider", choices=("ladder", "divider", "fans", "guilloche", "none"))
    ap.add_argument("--no-selftest", action="store_true")
    ap.add_argument("--g11", action="store_true")
    ap.add_argument("--open-holes", action="store_true", help="the fascia R with its control holes opened 0.4 mm, the ordered one (zip ...-holes04-fab.zip): "
                    "the default now; given alone it checks the fascia alone")
    ap.add_argument("--committed-holes", action="store_true", help="the fascia R as committed (8.8 / 8.0 holes), NOT the ordered one (zip ...-notordered-fab.zip, "
                    "which mkfab.sh --committed-holes writes); given alone it checks the fascia alone")
    ap.add_argument("--leaders", default=LEADERS, choices=("slope", "level", "dogleg", "centred"),
                    help="the fascia R's leader style (tools/fascia_art.py; default level, the owner's pick): its zip is the one "
                         "tools/mkfab.sh --leaders STYLE wrote, ...-<gold>-<style>[-holes04]-fab.zip")
    a = ap.parse_args()
    globals()["LEADERS"] = a.leaders
    os.environ["TS06_LEADERS"] = a.leaders             # the art boards built here (tools/fascia_gold.py, a subprocess) take it from the environment
    if a.open_holes and a.committed_holes:
        ap.error("--open-holes and --committed-holes do not go together")
    holes = not a.committed_holes                       # the ordered fascia has its control holes opened (fab/HOLES-VARIANT.md)
    todo = a.boards or (["TS06-FASCIA-rhythm"] if (a.open_holes or a.committed_holes) else list(BOARDS))
    if (a.open_holes or a.committed_holes) and todo != ["TS06-FASCIA-rhythm"]:
        ap.error("--open-holes / --committed-holes apply to TS06-FASCIA-rhythm only")
    for k in todo:
        if k not in BOARDS:
            ap.error("unknown board %s (%s)" % (k, ", ".join(BOARDS)))
    print("DFM check against generic 2-layer limits (INFERRED, to be checked against the fab chosen); KiCad %s" % ("local" if os.environ.get("KICAD_CLI") else "10 in Docker (" + IMG + ")"))
    print()
    good = True
    if a.g11:
        return 0 if g11(a.gold, holes) else 1
    if not a.no_selftest:
        good &= selftest()
    for k in todo:
        good &= run_board(k, a.gold, holes and k == "TS06-FASCIA-rhythm")
    print("DFM CHECK: %s" % ("PASS for %s" % ", ".join(todo) if good else "FAIL (see the rows above)"))
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
