#!/usr/bin/env python3
"""TS06-FASCIA-wide: the routed fascia, made as wide as the tube row, by translation.

WHAT. The boards went from 176 to 191.4 mm so the seconds tubes could stand 20.5 apart, and
the owner asked for the fascia to be centred under the tube row. The plain answer is the
same 176 x 40 board moved 7.7 mm right (FASCIA_X0 in 3d/case-pair). This script writes the
other answer: a panel 191.4 x 40, as wide as TS06-DISP and TS06-DRV, which fills the case
from cheek to cheek with the same 0.5 mm clearance each side that those two boards have.

SOURCE. The committed PCB/TS06-FASCIA/TS06-FASCIA.kicad_pcb, read as a tree with
tools/sexp.py. It is the source of truth: it was routed and height-compressed after
tools/mkpcb.py, which still draws the older 52 mm board. Nothing here edits coordinates as
text.

STEPS.
  1. Translate. Every footprint, track, via, graphic, text and zone point moves by
     DX = (191.4 - 176) / 2 = +7.7 mm in x. It is the same pure translation that
     PCB/README.md describes for the height compression. Every control, part and track
     keeps the world X it has on the centred 176 board, and nothing is re-routed: the 64
     tracks and zero vias are the original ones.
  2. Outline. Edge.Cuts is redrawn as a 191.4 x 40 rectangle with 1.5 mm corners, as
     mkpcb.py draws it.
  --pure stops here, so the checkers can show that translation alone changes nothing.
  3. Anchor to the edge, not to the controls. The four M2.5 holes keep their 4.5 mm inset
     from the NEW corners; the README applied the same rule to the two top holes during the
     height compression. The GND pour's boundary is redrawn 0.5 mm inside the new outline.
     The committed boundary, and the fill stored with it, were moved up with everything
     else in the compression and now reach 11.5 mm above the board's top edge. The stale
     filled_polygon is dropped, and KiCad refills the pour (--refill; needs docker and
     the kicad/kicad:10.0 image).
  4. A repair that has nothing to do with width. The height compression moved every
     gr_circle's end point up 12 mm but not its centre. So the rotary's 25.00 mm body ring
     (F.SilkS since commit 6a081e6) is printed as a 34.7 mm ring 12 mm below the knob and
     runs off the bottom edge. The four lever and button keepouts (User.1) have the same
     fault. These are the only two KiCad DRC warnings on the committed board. The fix
     moves each centre up the same 12 mm, which the assert proves exact: each radius comes
     back horizontal, 12.5 and 12.0. The body ring goes back to User.1, where mkpcb.py
     drew it and where its "BODY 25.00" note still sits. At the compressed dial's scale, a
     12.5 mm silk ring would run through MODE and all six numerals.

Usage:
    python3 tools/fascia_variant.py                        # write PCB/TS06-FASCIA-wide/
    python3 tools/fascia_variant.py --refill               # ...then KiCad 10 (docker) refills the pour and saves
    python3 tools/fascia_variant.py --pure OUT.kicad_pcb   # steps 1-2 only, for comparison
    python3 tools/fascia_variant.py --composite OUT.png    # front elevation: tube glass over the fascia, world X

The composite reads the written board back from disk, so it shows what is in the file.
"""
import json, math, os, shutil, subprocess, sys, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
sys.dont_write_bytecode = True                  # leave tools/ as it is
sys.path.insert(0, HERE)
import sexp                                     # noqa: E402
import mkpcb_disp as DISP                       # noqa: E402  placement only on import: W and the tube centres

SRC_DIR = os.path.join(ROOT, "PCB", "TS06-FASCIA")
SRC = os.path.join(SRC_DIR, "TS06-FASCIA.kicad_pcb")
NAME = "TS06-FASCIA-wide"
OUT_DIR = os.path.join(ROOT, "PCB", NAME)
OUT = os.path.join(OUT_DIR, NAME + ".kicad_pcb")

W1 = DISP.W                  # 191.4: the tube row (TS06-DISP = TS06-DRV)
CR = 1.5                     # corner radius, as mkpcb.py
ZONE_INSET = 0.5             # pour boundary inside the outline, as mkpcb.py's routing drew it
COMPRESS_DY = 12.0           # PCB/README.md: the height compression shifted everything up 12 mm
NS = uuid.UUID("5f0c6d8e-2b1a-4c3e-9d7f-0a6b1c2d3e4f")   # fixed: new items get the same UUID every run
COORD = ("start", "mid", "end", "center", "at", "xy")
KNOWN = {"version", "generator", "generator_version", "general", "paper", "title_block",
         "layers", "setup", "property", "net", "footprint", "gr_line", "gr_arc", "gr_circle",
         "gr_rect", "gr_poly", "gr_text", "segment", "arc", "via", "zone", "embedded_fonts"}


def U(tag):
    return '"%s"' % uuid.uuid5(NS, NAME + "/" + tag)


def f(a):
    return float(a)


def unq(a):
    return sexp.unq(a)


# ---------------------------------------------------------------------------- reading
def layer(node):
    ly = sexp.find(node, "layer")
    return unq(ly[1]) if ly else None


def ref_of(fp):
    return next((unq(p[2]) for p in sexp.find_all(fp, "property") if unq(p[1]) == "Reference"), "")


def outline_extent(root):
    xs, ys = [], []
    for c in root:
        if isinstance(c, list) and c[0].startswith("gr_") and layer(c) == "Edge.Cuts":
            for k in ("start", "mid", "end"):
                p = sexp.find(c, k)
                if p:
                    xs.append(f(p[1]))
                    ys.append(f(p[2]))
    assert abs(min(xs)) < 1e-9 and abs(min(ys)) < 1e-9, "outline must start at (0, 0)"
    return max(xs), max(ys)


# ---------------------------------------------------------------------------- the steps
def move(pt, dx, dy=0.0):
    pt[1] = sexp.num(f(pt[1]) + dx)
    pt[2] = sexp.num(f(pt[2]) + dy)


def translate(root, dx):
    """Step 1. Board-frame coordinates only: a footprint's own (at), and every point of every
    top-level graphic, track, via and zone. Pads and fp_* graphics are local to their footprint
    and stay as they are."""
    n = 0
    for c in root:
        if not isinstance(c, list):
            continue
        assert c[0] in KNOWN, "unhandled top-level item %s - teach translate() about it" % c[0]
        if c[0] == "footprint":
            move(sexp.find(c, "at"), dx)
            n += 1
        elif c[0].startswith("gr_") or c[0] in ("segment", "arc", "via", "zone"):
            for node in sexp.walk(c):
                if node and node[0] in COORD and len(node) >= 3:
                    move(node, dx)
            n += 1
    return n


def redraw_outline(root, w, h):
    """Step 2. Remove every Edge.Cuts graphic and draw w x h with CR corners, where the old
    outline sat in the file."""
    idx = [i for i, c in enumerate(root) if isinstance(c, list) and c[0].startswith("gr_")
           and layer(c) == "Edge.Cuts"]
    at = idx[0]
    for i in reversed(idx):
        del root[i]
    stroke = ["stroke", ["width", "0.05"], ["type", "solid"]]
    k = CR - CR * math.sqrt(0.5)
    N = sexp.num
    items = []
    for i, (a, b) in enumerate((((CR, 0), (w - CR, 0)), ((w, CR), (w, h - CR)),
                                ((w - CR, h), (CR, h)), ((0, h - CR), (0, CR)))):
        items.append(["gr_line", ["start", N(a[0]), N(a[1])], ["end", N(b[0]), N(b[1])],
                      [x if not isinstance(x, list) else list(x) for x in stroke],
                      ["layer", '"Edge.Cuts"'], ["uuid", U("edge/line%d" % i)]])
    for i, (a, m, b) in enumerate((((0, CR), (k, k), (CR, 0)),
                                   ((w - CR, 0), (w - k, k), (w, CR)),
                                   ((w, h - CR), (w - k, h - k), (w - CR, h)),
                                   ((CR, h), (k, h - k), (0, h - CR)))):
        items.append(["gr_arc", ["start", N(a[0]), N(a[1])], ["mid", N(m[0]), N(m[1])],
                      ["end", N(b[0]), N(b[1])],
                      [x if not isinstance(x, list) else list(x) for x in stroke],
                      ["layer", '"Edge.Cuts"'], ["uuid", U("edge/arc%d" % i)]])
    root[at:at] = items


def holes_to_corners(root, w0, w1):
    """Step 3a. Each M2.5 hole keeps its inset from the nearest side of the ORIGINAL board, but
    measured from the new one. y does not change."""
    moved = []
    for fp in sexp.find_all(root, "footprint"):
        if "MountingHole" not in fp[1]:
            continue
        at = sexp.find(fp, "at")
        x0 = f(at[1]) - (w1 - w0) / 2            # back to the original frame
        inset = x0 if x0 < w0 / 2 else w0 - x0
        x1 = inset if x0 < w0 / 2 else w1 - inset
        moved.append((x0, f(at[2]), x1))
        at[1] = sexp.num(x1)
    return moved


def redraw_zone(root, w, h):
    """Step 3b. The pour boundary 0.5 mm inside the new outline; the stale fill is dropped."""
    for z in sexp.find_all(root, "zone"):
        poly = sexp.find(z, "polygon")
        pts = sexp.find(poly, "pts")
        e = ZONE_INSET
        pts[1:] = [["xy", sexp.num(x), sexp.num(y)] for x, y in ((e, e), (w - e, e), (w - e, h - e), (e, h - e))]
        z[:] = [c for c in z if not (isinstance(c, list) and c[0] == "filled_polygon")]


def repair_circles(root):
    """Step 4. A gr_circle whose centre sits exactly COMPRESS_DY below a control, and whose end
    point is level with that control, is one the height compression half-moved. Move its centre
    up by the same COMPRESS_DY; the radius then comes back horizontal, as mkpcb.py wrote it."""
    ctrl = {ref_of(fp): (f(sexp.find(fp, "at")[1]), f(sexp.find(fp, "at")[2]))
            for fp in sexp.find_all(root, "footprint") if ref_of(fp).startswith("SW")}
    done = []
    for c in sexp.find_all(root, "gr_circle"):
        cen, end = sexp.find(c, "center"), sexp.find(c, "end")
        cx, cy, ex, ey = f(cen[1]), f(cen[2]), f(end[1]), f(end[2])
        hit = [r for r, (x, y) in ctrl.items()
               if abs(x - cx) < 1e-6 and abs(cy - COMPRESS_DY - y) < 1e-6 and abs(ey - y) < 1e-6]
        if not hit:
            continue
        cen[2] = sexp.num(cy - COMPRESS_DY)
        r = ex - cx
        assert abs(f(cen[2]) - ey) < 1e-9 and r > 0, "the repair must leave a horizontal radius"
        was = layer(c)
        if hit[0] == "SW1" and was == "F.SilkS":
            sexp.find(c, "layer")[1] = '"User.1"'
        done.append((hit[0], was, layer(c), r, math.hypot(ex - cx, ey - cy)))
    return done


# ---------------------------------------------------------------------------- writing
def dump(node, depth=0):
    """sexp.dump, except that a (pts ...) list packs its (xy ...) points onto shared lines,
    the way KiCad itself writes them."""
    if not isinstance(node, list):
        return str(node)
    ind = "\t" * depth
    if not any(isinstance(c, list) for c in node):
        return ind + "(" + " ".join(str(c) for c in node) + ")"
    if node[0] == "pts" and all(isinstance(c, list) and c[0] == "xy" for c in node[1:]):
        lines, cur = [], []
        for c in node[1:]:
            s = "(" + " ".join(str(a) for a in c) + ")"
            if cur and len(" ".join(cur + [s])) > 96:
                lines.append(cur)
                cur = []
            cur.append(s)
        lines.append(cur)
        return "\n".join([ind + "(pts"] + [ind + "\t" + " ".join(l) for l in lines] + [ind + ")"])
    head, i = [], 0
    while i < len(node) and not isinstance(node[i], list):
        head.append(str(node[i]))
        i += 1
    out = [ind + "(" + " ".join(head)]
    for c in node[i:]:
        out.append(dump(c, depth + 1) if isinstance(c, list) else "\t" * (depth + 1) + str(c))
    out.append(ind + ")")
    return "\n".join(out)


def build(pure=False):
    root = sexp.parse(open(SRC, encoding="utf8").read())
    w0, h0 = outline_extent(root)
    dx = (W1 - w0) / 2
    log = ["source %s: %g x %g; target %g x %g; DX = %+g" % (os.path.relpath(SRC, ROOT), w0, h0, W1, h0, dx)]
    log.append("1. translated %d items by %+g mm" % (translate(root, dx), dx))
    redraw_outline(root, W1, h0)
    log.append("2. outline redrawn %g x %g, r %g" % (W1, h0, CR))
    if not pure:
        for x0, y, x1 in holes_to_corners(root, w0, W1):
            log.append("3. hole (%g, %g) on the 176 board -> x %g (world X %g -> %g)" % (x0, y, x1, x0 + dx, x1))
        redraw_zone(root, W1, h0)
        log.append("3. GND pour boundary redrawn %g inside the outline; fill left to KiCad" % ZONE_INSET)
        for ref, was, now, r, bad_r in repair_circles(root):
            log.append("4. %s circle recentred on the control (r %.2f drawn as %.2f)%s"
                       % (ref, r, bad_r, "; layer %s -> %s" % (was, now) if was != now else ""))
    return root, log


def write_project(pcb_text):
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT, "w", encoding="utf8") as fh:
        fh.write(pcb_text)
    for fn in ("fp-lib-table", "sym-lib-table"):     # both point at ${KIPRJMOD}/../lib, which still resolves
        shutil.copyfile(os.path.join(SRC_DIR, fn), os.path.join(OUT_DIR, fn))
    # the project file carries the board's design rules; KiCad pairs it with the board by name
    pro = json.load(open(os.path.join(SRC_DIR, "TS06-FASCIA.kicad_pro"), encoding="utf8"))
    pro["meta"]["filename"] = NAME + ".kicad_pro"
    pro["pcbnew"]["last_paths"]["step"] = NAME + ".step"
    for s in pro["schematic"]["top_level_sheets"]:
        s["filename"] = NAME + ".kicad_sch"
    with open(os.path.join(OUT_DIR, NAME + ".kicad_pro"), "w", encoding="utf8") as fh:
        json.dump(pro, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    # the schematic is the same circuit; its symbol instances are keyed by project name
    sch = sexp.parse(open(os.path.join(SRC_DIR, "TS06-FASCIA.kicad_sch"), encoding="utf8").read())
    n = 0
    for node in sexp.walk(sch):
        if node and node[0] == "project" and len(node) > 1 and node[1] == '"TS06-FASCIA"':
            node[1] = sexp.q(NAME)
            n += 1
        if node and node[0] == "title" and len(node) == 2:
            node[1] = sexp.q(NAME + " - control panel and product face, as wide as the tube row")
    with open(os.path.join(OUT_DIR, NAME + ".kicad_sch"), "w", encoding="utf8") as fh:
        fh.write(sexp.dump(sch) + "\n")
    return n


def refill(path):
    """KiCad's own pour: kicad-cli refills the zones and saves the board in place."""
    rel = os.path.relpath(path, ROOT)
    cmd = ["docker", "run", "--rm", "--user", "%d:%d" % (os.getuid(), os.getgid()),
           "-v", ROOT + ":/w", "-w", "/w", "-e", "HOME=/tmp", "mirror.gcr.io/kicad/kicad:10.0",
           "kicad-cli", "pcb", "drc", "--refill-zones", "--save-board", "--units", "mm",
           "-o", "/tmp/refill.rpt", "/w/" + rel]
    r = subprocess.run(cmd, capture_output=True, text=True)
    print((r.stdout + r.stderr).strip())
    if r.returncode != 0:
        sys.exit("refill failed")


# ---------------------------------------------------------------------------- the composite
def composite(png):
    """Front elevation in world X: TS06-DISP's glass above, the fascia (raked 12°, so 40 mm of
    face shows 39.1 mm tall) below, the centred 176 board dashed for comparison. Reads the board
    back from disk and the case's numbers from 3d/case-pair."""
    sys.path.insert(0, os.path.join(ROOT, "3d", "case-pair"))
    import case_pair                            # noqa: E402  (main() is guarded)
    B = json.load(open(os.path.join(ROOT, "3d", "case-pair", "boards.json"), encoding="utf8"))
    v = case_pair.dims(B).v
    rake = math.radians(v["FASCIA_RAKE"])
    top = v["SILL_TOP_Y"]
    Yf = lambda t: top - t * math.cos(rake)    # a point t mm down the face, projected

    root = sexp.parse(open(OUT, encoding="utf8").read())
    fw, fh_ = outline_extent(root)
    holes, ctl = [], {}
    for fp in sexp.find_all(root, "footprint"):
        at = sexp.find(fp, "at")
        x, y = f(at[1]), f(at[2])
        drill = [f(sexp.find(p, "drill")[1]) for p in sexp.find_all(fp, "pad") if sexp.find(p, "drill")]
        if "MountingHole" in fp[1]:
            holes.append((x, y, drill[0]))
        elif ref_of(fp).startswith("SW"):
            ctl[ref_of(fp)] = (x, y, max(drill))
    x0_old = (W1 - 176.0) / 2
    old_holes = [(4.5, 4.5), (171.5, 4.5), (4.5, 35.5), (171.5, 35.5)]

    tubes = [("H10", DISP.IN12_X[0], "12"), ("H1", DISP.IN12_X[1], "12"), ("M10", DISP.IN12_X[2], "12"),
             ("M1", DISP.IN12_X[3], "12"), ("S10", DISP.IN17_X[0], "17"), ("S1", DISP.IN17_X[1], "17"),
             ("ИН-15Б", DISP.IN15_X[0], "15"), ("ИН-15А", DISP.IN15_X[1], "15")]
    y12, y17 = DISP.TOP - DISP.Y12, DISP.TOP - DISP.Y17
    colon = [(DISP.COLON_X, DISP.TOP - y) for y in DISP.COLON_Y]
    names = {"SW1": "SW1 rotary", "SW2": "SW2 FIELD", "SW3": "SW3 SUB", "SW4": "SW4 −", "SW5": "SW5 +"}

    S = 8.0                                     # px per mm
    X0, X1, YT, YB = -14.0, W1 + 14.0, DISP.TOP + 14.0, Yf(fh_) - 30.0
    sx = lambda X: (X - X0) * S
    sy = lambda Y: (YT - Y) * S
    E = []
    add = E.append
    INK, MUTE, GOLD, GLASS, BOARD, CASE = "#1d2125", "#6b7178", "#b8860b", "#c98a2b", "#20262b", "#9aa1a8"

    def rect(x0, y0, x1, y1, **k):
        a = " ".join('%s="%s"' % (kk.replace("_", "-"), vv) for kk, vv in k.items())
        add('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" %s/>' % (sx(x0), sy(y1), (x1 - x0) * S, (y1 - y0) * S, a))

    def text(X, Y, s, size=11, anchor="middle", fill=INK, weight="normal"):
        add('<text x="%.2f" y="%.2f" font-family="DejaVu Sans" font-size="%g" text-anchor="%s" fill="%s" '
            'font-weight="%s">%s</text>' % (sx(X), sy(Y), size, anchor, fill, weight, s))

    def line(xa, ya, xb, yb, col=INK, w=1.0, dash=None):
        d = ' stroke-dasharray="%s"' % dash if dash else ""
        add('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="%s" stroke-width="%g"%s/>'
            % (sx(xa), sy(ya), sx(xb), sy(yb), col, w, d))

    def ell(X, Y, rx, ry, **k):
        a = " ".join('%s="%s"' % (kk.replace("_", "-"), vv) for kk, vv in k.items())
        add('<ellipse cx="%.2f" cy="%.2f" rx="%.2f" ry="%.2f" %s/>' % (sx(X), sy(Y), rx * S, ry * S, a))

    # the case cheeks and TS06-DISP
    rect(-v["CHEEK_CLR"] - v["CHEEK_T"], YB + 16, -v["CHEEK_CLR"], DISP.TOP + 6, fill="#e4e6e8", stroke=CASE)
    rect(W1 + v["CHEEK_CLR"], YB + 16, W1 + v["CHEEK_CLR"] + v["CHEEK_T"], DISP.TOP + 6, fill="#e4e6e8", stroke=CASE)
    text(-v["CHEEK_CLR"] - v["CHEEK_T"] / 2, DISP.TOP + 8, "cheek", 10, fill=MUTE)
    text(W1 + v["CHEEK_CLR"] + v["CHEEK_T"] / 2, DISP.TOP + 8, "cheek", 10, fill=MUTE)
    rect(0, DISP.TOP - DISP.H, W1, DISP.TOP, fill="#f3efe6", stroke=CASE, stroke_width=1)
    text(0, DISP.TOP + 1.8, "TS06-DISP %g x %g, tube centres from tools/mkpcb_disp.py" % (DISP.W, DISP.H), 10, "start", MUTE)
    # the glass
    for name, x, kind in tubes:
        if kind == "17":
            w_, h_, yc = v["IN17_FACE"], v["IN17_H"], y17
        else:
            w_, h_, yc = v["IN12_W"], v["IN12_H"], y12
        add('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" rx="%.2f" fill="%s" fill-opacity="0.18" stroke="%s" '
            'stroke-width="1.6"/>' % (sx(x - w_ / 2), sy(yc + h_ / 2), w_ * S, h_ * S, (3.5 if kind != "17" else 2) * S, GLASS, GLASS))
        line(x, DISP.TOP + 1, x, Yf(fh_) - 3, GLASS, 1.0, "5,4")
        text(x, yc + h_ / 2 + 1.5, name, 11, weight="bold")
        text(x, yc - h_ / 2 - 3.2, "%.2f" % x, 10, fill=MUTE)
    for x, y in colon:
        ell(x, y, v["INS1_D"] / 2, v["INS1_D"] / 2, fill=GLASS, fill_opacity="0.18", stroke=GLASS, stroke_width="1.4")
    line(DISP.COLON_X, DISP.TOP + 1, DISP.COLON_X, Yf(fh_) - 3, GLASS, 0.8, "2,4")
    text(DISP.COLON_X, colon[0][1] + 5, "colon", 10)
    text(DISP.COLON_X, colon[1][1] - 6.5, "%.3f" % DISP.COLON_X, 10, fill=MUTE)

    # the wide board
    add('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" rx="%.2f" fill="%s" fill-opacity="0.92" stroke="%s" '
        'stroke-width="1.4"/>' % (sx(0), sy(Yf(0)), fw * S, (Yf(0) - Yf(fh_)) * S, CR * S, BOARD, INK))
    for hx, hy, d in holes:
        ell(hx, Yf(hy), d / 2, d / 2 * math.cos(rake), fill="#f7f7f5", stroke="#f7f7f5")
    for ref, (x, y, d) in sorted(ctl.items()):
        ell(x, Yf(y), d / 2, d / 2 * math.cos(rake), fill="#f7f7f5", stroke=GOLD, stroke_width="1.6")
        line(x - 2.5, Yf(y), x + 2.5, Yf(y), GOLD, 1)
        line(x, Yf(y) - 2.5, x, Yf(y) + 2.5, GOLD, 1)
    # the tube centre lines again, over the board, so the alignment reads through it
    for name, x, kind in tubes:
        line(x, Yf(0), x, Yf(fh_), "#e0b262", 0.9, "5,4")
    line(DISP.COLON_X, Yf(0), DISP.COLON_X, Yf(fh_), "#e0b262", 0.7, "2,4")
    # the centred 176 board over it, dashed
    RED = "#ff7a6e"
    rect(x0_old, Yf(fh_), x0_old + 176.0, Yf(0), fill="none", stroke=RED, stroke_width=1.3, stroke_dasharray="7,5")
    for hx, hy in old_holes:
        ell(hx + x0_old, Yf(hy), 1.35, 1.35 * math.cos(rake), fill="none", stroke=RED, stroke_width="1.4")
    # labels under the board: each control's world X and its nearest tube centre
    centres = [(n, x) for n, x, _ in tubes] + [("colon", DISP.COLON_X)]
    yl = Yf(fh_) - 6
    for ref, (x, y, d) in sorted(ctl.items()):
        near = min(centres, key=lambda c: abs(c[1] - x))
        text(x, yl, names[ref], 11, weight="bold")
        text(x, yl - 3.6, "X %.2f" % x, 10)
        text(x, yl - 7.0, "%+.2f to %s" % (x - near[1], near[0]), 10, fill=MUTE)
    inset = min(min(hx, fw - hx) for hx, hy, d in holes)
    text(fw / 2, Yf(fh_) + 2.2, "TS06-FASCIA-wide %g x %g (raked 12°: shown %.1f tall), M2.5 holes %g from the new corners"
         % (fw, fh_, Yf(0) - Yf(fh_), inset), 10, fill="#e8e6e0")
    text(0, YB + 8, "solid: TS06-FASCIA-wide, %g wide, %g mm to each cheek.   red dashed: the centred 176 board "
         "(FASCIA_X0 %g) and its holes.   The controls are at the same world X on both." % (fw, v["CHEEK_CLR"], x0_old),
         11, "start", INK)
    text(0, YB + 3.5, "Glass: ИН-12 / ИН-15 envelope %.2f x %.2f, ИН-17 face %g x %g, ИНС-1 Ø%.2f (3d/case-pair DIMS). "
         "World X = TS06-DISP x." % (v["IN12_W"], v["IN12_H"], v["IN17_FACE"], v["IN17_H"], v["INS1_D"]),
         11, "start", MUTE)
    Wpx, Hpx = (X1 - X0) * S, (YT - YB) * S
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %.1f %.1f">'
           '<rect width="100%%" height="100%%" fill="#fbfaf7"/>%s</svg>' % (Wpx, Hpx, Wpx, Hpx, "".join(E)))
    svg_path = os.path.splitext(png)[0] + ".svg"
    with open(svg_path, "w", encoding="utf8") as fh:
        fh.write(svg)
    r = subprocess.run(["rsvg-convert", "-o", png, svg_path], capture_output=True, text=True)
    print("wrote", os.path.relpath(svg_path, ROOT), "and" if r.returncode == 0 else "(no rsvg-convert:",
          os.path.relpath(png, ROOT) if r.returncode == 0 else r.stderr.strip() + ")")
    print("\n  control      world X   nearest tube centre   offset")
    for ref, (x, y, d) in sorted(ctl.items()):
        near = min(centres, key=lambda c: abs(c[1] - x))
        print("  %-11s %8.2f   %-8s %8.3f   %+6.2f" % (names[ref], x, near[0], near[1], x - near[1]))


def main():
    a = sys.argv[1:]
    if "--composite" in a:
        composite(os.path.abspath(a[a.index("--composite") + 1]))
        return
    pure = "--pure" in a
    root, log = build(pure)
    text = dump(root) + "\n"
    if pure:
        path = os.path.abspath(a[a.index("--pure") + 1])
        with open(path, "w", encoding="utf8") as fh:
            fh.write(text)
        print("\n".join(log))
        print("wrote", path, "(steps 1-2 only)")
        return
    n = write_project(text)
    print("\n".join(log))
    print("wrote", os.path.relpath(OUT_DIR, ROOT) + "/: board, project, schematic (%d instances renamed), lib tables" % n)
    if "--refill" in a:
        refill(OUT)


if __name__ == "__main__":
    main()
