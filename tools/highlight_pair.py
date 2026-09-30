#!/usr/bin/env python3
"""Each section of the through-hole pair, lit up on its board: one PNG per section per board.

    python3 tools/highlight_pair.py OUTDIR      # layout-<board>-<section>.png for every section, and
                                                # OUTDIR/sections.json, the viewer's manifest

The sections and their parts are tools/mksch_pair.py's (which takes them from the part groups of
tools/ts06pair.py), so a picture and its schematic sheet always show the same parts. The boards are
read from PCB/TS06-{DRV,DISP}/*.kicad_pcb as they are saved.

WHAT A PICTURE SHOWS. The board dimmed: black mask, its copper faint (both faces; the ground pours
as a faint tint of their outline). Over it, in warm orange: the section's footprints (courtyard and
pads; a courtyard on the far face dashed) and the tracks of the section's nets, front copper
brighter than back. Short labels: the section's references, and a title.

WHICH NETS ARE LIT. Every net a section's parts touch, except the rails GND, +5V and +12V, which run
everywhere; each rail is lit in the section that makes it (+12V and its jack nets in "power in",
+5V in "5 V rail"). The board-link section lights its strips but not their nets' tracks: those
tracks belong to the sections at either end, and lit together they would be the whole board.
"""
import json, math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sexp                                 # noqa: E402
import ts06pair as TP                       # noqa: E402
import mksch_pair as MS                     # noqa: E402

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, ".."))
RAILS = {"GND", "+5V", "+12V"}
RAIL_HOME = {"power-in": {"+12V"}, "5v": {"+5V"}}
NO_TRACKS = {"stack"}
WIDTH = 2400                                # the picture, pixels
SS = 3                                      # drawn at SS x and scaled down: smooth edges
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

C = dict(page=(14, 15, 17), mask=(4, 4, 5), edge=(70, 70, 74), zone=(15, 13, 10),
         cu_f=(64, 52, 36), cu_b=(46, 38, 28), pad=(78, 64, 44), drill=(4, 4, 5),
         hi_f=(255, 150, 50), hi_b=(214, 106, 28), hi_pad=(255, 170, 80), court=(255, 196, 120),
         label=(255, 226, 190), halo=(0, 0, 0), title=(236, 236, 236), sub=(150, 150, 150))


def rot(x, y, r):
    """(x, y) turned r degrees counter-clockwise as seen on screen (y down) - tools/pcbkit.py's _rot."""
    a = math.radians(r)
    return x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a)


def xy(n):
    return float(n[1]), float(n[2])


def arc_pts(s, m, e, n=16):
    """Points along the circle through start, mid and end."""
    (x1, y1), (x2, y2), (x3, y3) = s, m, e
    d = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    if abs(d) < 1e-9:
        return [s, e]
    ux = ((x1 ** 2 + y1 ** 2) * (y2 - y3) + (x2 ** 2 + y2 ** 2) * (y3 - y1) + (x3 ** 2 + y3 ** 2) * (y1 - y2)) / d
    uy = ((x1 ** 2 + y1 ** 2) * (x3 - x2) + (x2 ** 2 + y2 ** 2) * (x1 - x3) + (x3 ** 2 + y3 ** 2) * (x2 - x1)) / d
    a1, a2, a3 = (math.atan2(p[1] - uy, p[0] - ux) for p in (s, m, e))
    r = math.hypot(x1 - ux, y1 - uy)

    def norm(a):
        return (a - a1) % (2 * math.pi)
    sweep = norm(a3) if norm(a2) < norm(a3) else norm(a3) - 2 * math.pi
    return [(ux + r * math.cos(a1 + sweep * i / n), uy + r * math.sin(a1 + sweep * i / n)) for i in range(n + 1)]


# ==================================================================== reading a board
def load(board):
    proj = MS.BOARDS[board][0]
    tree = sexp.parse(open(os.path.join(ROOT, "PCB", proj, proj + ".kicad_pcb"), encoding="utf8").read())
    B = dict(edges=[], fps={}, tracks=[], zones=[], vias=[])
    NETS.clear()
    NETS.update({g[1]: sexp.unq(g[2]) for g in tree if isinstance(g, list) and g[0] == "net" and len(g) > 2})
    for g in tree:
        if not isinstance(g, list):
            continue
        ly = sexp.find(g, "layer")
        ly = sexp.unq(ly[1]) if ly else None
        if g[0] == "gr_line" and ly == "Edge.Cuts":
            B["edges"].append((xy(sexp.find(g, "start")), xy(sexp.find(g, "end"))))
        elif g[0] == "gr_rect" and ly == "Edge.Cuts":
            (x1, y1), (x2, y2) = xy(sexp.find(g, "start")), xy(sexp.find(g, "end"))
            pts = [(x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1)]
            B["edges"] += list(zip(pts, pts[1:]))
        elif g[0] == "gr_arc" and ly == "Edge.Cuts":
            pts = arc_pts(xy(sexp.find(g, "start")), xy(sexp.find(g, "mid")), xy(sexp.find(g, "end")))
            B["edges"] += list(zip(pts, pts[1:]))
        elif g[0] == "segment":
            B["tracks"].append(dict(net=_net(g), layer=ly, pts=[xy(sexp.find(g, "start")), xy(sexp.find(g, "end"))],
                                    w=float(sexp.find(g, "width")[1])))
        elif g[0] == "arc":
            B["tracks"].append(dict(net=_net(g), layer=ly, w=float(sexp.find(g, "width")[1]),
                                    pts=arc_pts(xy(sexp.find(g, "start")), xy(sexp.find(g, "mid")), xy(sexp.find(g, "end")))))
        elif g[0] == "via":
            B["vias"].append(dict(net=_net(g), at=xy(sexp.find(g, "at")), size=float(sexp.find(g, "size")[1])))
        elif g[0] == "zone":
            nn = sexp.find(g, "net_name")
            lys = sexp.find(g, "layers") or sexp.find(g, "layer")
            layers = [sexp.unq(a) for a in lys[1:]] if lys else []
            fills = [p for p in sexp.find_all(g, "filled_polygon")]
            poly = sexp.find(g, "polygon")
            polys = ([[xy(p) for p in sexp.find_all(sexp.find(f, "pts"), "xy")] for f in fills] if fills else
                     [[xy(p) for p in sexp.find_all(sexp.find(poly, "pts"), "xy")]] if poly else [])
            for pl in polys:
                B["zones"].append(dict(net=sexp.unq(nn[1]) if nn else None, layers=layers, poly=pl, filled=bool(fills)))
        elif g[0] == "footprint":
            B["fps"].update(_footprint(g))
    return B


NETS = {}                                   # the board's net table: number -> name


def _net(g):
    """A net by name or by number (tracks carry only the number: (net 39))."""
    n = sexp.find(g, "net")
    if not n:
        return None
    if len(n) > 2:
        return sexp.unq(n[2]) or None
    v = n[1]
    return NETS.get(v) if re.match(r"^\d+$", str(v)) else (sexp.unq(v) or None)


def _footprint(g):
    at = sexp.find(g, "at")
    X, Y = float(at[1]), float(at[2])
    R = float(at[3]) if len(at) > 3 else 0.0
    layer = sexp.unq(sexp.find(g, "layer")[1])
    props = {sexp.unq(p[1]): sexp.unq(p[2]) for p in sexp.find_all(g, "property")}

    def T(p):
        dx, dy = rot(p[0], p[1], R)
        return X + dx, Y + dy
    pads, court = [], []
    for p in sexp.find_all(g, "pad"):
        pa = sexp.find(p, "at")
        px, py = T(xy(pa))
        pr = float(pa[3]) if len(pa) > 3 else R
        sz = sexp.find(p, "size")
        dr = sexp.find(p, "drill")
        drill = None
        if dr:
            v = [a for a in dr[1:] if not isinstance(a, list) and a != "oval"]
            drill = float(v[0]) if v else None
        lys = [sexp.unq(a) for a in (sexp.find(p, "layers") or [None])[1:]]
        rr = sexp.find(p, "roundrect_rratio")
        pads.append(dict(name=sexp.unq(p[1]), kind=p[2], shape=p[3], at=(px, py), rot=pr, w=float(sz[1]), h=float(sz[2]),
                         drill=drill, layers=lys, net=_net(p), rr=float(rr[1]) if rr else 0.0))
    for n in g:
        if not isinstance(n, list) or n[0] not in ("fp_line", "fp_rect", "fp_circle", "fp_poly", "fp_arc"):
            continue
        ly = sexp.find(n, "layer")
        if not ly or not sexp.unq(ly[1]).endswith("CrtYd"):
            continue
        if n[0] == "fp_line":
            court.append([T(xy(sexp.find(n, "start"))), T(xy(sexp.find(n, "end")))])
        elif n[0] == "fp_rect":
            (x1, y1), (x2, y2) = xy(sexp.find(n, "start")), xy(sexp.find(n, "end"))
            court.append([T(q) for q in ((x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1))])
        elif n[0] == "fp_circle":
            c, e = xy(sexp.find(n, "center")), xy(sexp.find(n, "end"))
            r = math.hypot(e[0] - c[0], e[1] - c[1])
            court.append([T((c[0] + r * math.cos(2 * math.pi * i / 48), c[1] + r * math.sin(2 * math.pi * i / 48)))
                          for i in range(49)])
        elif n[0] == "fp_arc":
            court.append([T(q) for q in arc_pts(xy(sexp.find(n, "start")), xy(sexp.find(n, "mid")), xy(sexp.find(n, "end")))])
        elif n[0] == "fp_poly":
            pts = [T(xy(q)) for q in sexp.find_all(sexp.find(n, "pts"), "xy")]
            court.append(pts + pts[:1])
    return {props.get("Reference", "?"): dict(at=(X, Y), layer=layer, pads=pads, court=court)}


# ==================================================================== drawing
def pad_poly(p):
    w, h, (cx, cy), r = p["w"], p["h"], p["at"], p["rot"]
    if p["shape"] == "circle":
        return None
    if p["shape"] == "oval":
        rad = min(w, h) / 2
        pts = []
        if w >= h:
            d = w / 2 - rad
            pts = [(d + rad * math.cos(a), rad * math.sin(a)) for a in [math.pi * (i / 12 - 0.5) for i in range(13)]]
            pts += [(-d - rad * math.cos(a), -rad * math.sin(a)) for a in [math.pi * (i / 12 - 0.5) for i in range(13)]]
        else:
            d = h / 2 - rad
            pts = [(rad * math.cos(a), d + rad * math.sin(a)) for a in [math.pi * i / 12 for i in range(13)]]
            pts += [(-rad * math.cos(a), -d - rad * math.sin(a)) for a in [math.pi * i / 12 for i in range(13)]]
    else:
        rr = min(w, h) * p["rr"] if p["shape"] == "roundrect" else 0
        if rr > 0:
            pts = []
            for sx, sy, a0 in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
                ccx, ccy = sx * (w / 2 - rr), sy * (h / 2 - rr)
                pts += [(ccx + rr * math.cos(math.radians(a0 + 15 * i)), ccy + rr * math.sin(math.radians(a0 + 15 * i)))
                        for i in range(7)]
        else:
            pts = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    return [(cx + a, cy + b) for a, b in (rot(x, y, r) for x, y in pts)]


class Canvas:
    def __init__(self, B, title, sub):
        xs = [p[0] for e in B["edges"] for p in e] or [0, 100]
        ys = [p[1] for e in B["edges"] for p in e] or [0, 100]
        self.x0, self.x1, self.y0, self.y1 = min(xs), max(xs), min(ys), max(ys)
        m = 6.0
        self.s = WIDTH / (self.x1 - self.x0 + 2 * m)
        self.head = 64
        H = int((self.y1 - self.y0 + 2 * m) * self.s) + self.head
        self.ox, self.oy = self.x0 - m, self.y0 - m
        self.im = Image.new("RGB", (WIDTH * SS, H * SS), C["page"])
        self.d = ImageDraw.Draw(self.im)
        self.title, self.sub = title, sub

    def P(self, p):
        return ((p[0] - self.ox) * self.s * SS, (p[1] - self.oy) * self.s * SS + self.head * SS)

    def mm(self, v):
        return max(1, v * self.s * SS)

    def poly(self, pts, fill=None, outline=None, width=0.1):
        self.d.polygon([self.P(p) for p in pts], fill=fill, outline=outline,
                       width=int(self.mm(width)) if outline else 0)

    def line(self, pts, col, w, dash=None):
        pp = [self.P(p) for p in pts]
        if dash:
            for a, b in zip(pp, pp[1:]):
                L = math.hypot(b[0] - a[0], b[1] - a[1])
                n = max(1, int(L / (self.mm(dash) * 2)))
                for i in range(n):
                    t0, t1 = i / n, (i + 0.5) / n
                    self.d.line([(a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0),
                                 (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)], fill=col, width=int(self.mm(w)))
            return
        self.d.line(pp, fill=col, width=int(self.mm(w)), joint="curve")
        r = self.mm(w) / 2
        for x, y in (pp[0], pp[-1]):
            self.d.ellipse([x - r, y - r, x + r, y + r], fill=col)

    def circle(self, c, r, fill):
        x, y = self.P(c)
        rr = self.mm(r)
        self.d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=fill)

    def pad(self, p, col):
        pl = pad_poly(p)
        if pl is None:
            self.circle(p["at"], p["w"] / 2, col)
        else:
            self.poly(pl, fill=col)

    def text(self, xy_px, t, size, col, bold=False, halo=True, anchor="mm"):
        f = ImageFont.truetype(FONT_B if bold else FONT, int(size * SS))
        if halo:
            self.d.text(xy_px, t, font=f, fill=C["halo"], anchor=anchor, stroke_width=int(3 * SS), stroke_fill=C["halo"])
        self.d.text(xy_px, t, font=f, fill=col, anchor=anchor)
        return self.d.textbbox(xy_px, t, font=f, anchor=anchor, stroke_width=int(3 * SS) if halo else 0)

    def save(self, path):
        im = self.im.resize((self.im.size[0] // SS, self.im.size[1] // SS), Image.LANCZOS)
        im.save(path, optimize=True)


def render(board, B, sec, refs, nets, path):
    proj = MS.BOARDS[board][0]
    title = f"{proj}  ·  {sec.get('manifest_title', sec['title'])}"
    cv = Canvas(B, title, "")
    # the board, dimmed
    xs = (cv.x0, cv.x1)
    ys = (cv.y0, cv.y1)
    cv.poly([(xs[0], ys[0]), (xs[1], ys[0]), (xs[1], ys[1]), (xs[0], ys[1])], fill=C["mask"])
    for z in B["zones"]:
        cv.poly(z["poly"], fill=C["zone"])
    for layer, col in (("B.Cu", C["cu_b"]), ("F.Cu", C["cu_f"])):
        for t in B["tracks"]:
            if t["layer"] == layer:
                cv.line(t["pts"], col, t["w"])
    for fp in B["fps"].values():
        for p in fp["pads"]:
            if p["kind"] != "np_thru_hole":
                cv.pad(p, C["pad"])
    # the section, lit
    lit = [t for t in B["tracks"] if t["net"] in nets]
    for layer, col in (("B.Cu", C["hi_b"]), ("F.Cu", C["hi_f"])):
        for t in lit:
            if t["layer"] == layer:
                cv.line(t["pts"], col, max(t["w"], 0.3))
    for fp in B["fps"].values():
        for p in fp["pads"]:
            if p["net"] in nets and p["kind"] != "np_thru_hole":
                cv.pad(p, C["hi_b"])
    for ref in refs:
        fp = B["fps"].get(ref)
        if not fp:
            continue
        for p in fp["pads"]:
            if p["kind"] != "np_thru_hole":
                cv.pad(p, C["hi_pad"])
        far = fp["layer"] == "B.Cu"
        for c in fp["court"]:
            cv.line(c, C["court"], 0.18, dash=0.5 if far else None)
    for fp in B["fps"].values():                # the holes, drilled through everything
        for p in fp["pads"]:
            if p["drill"]:
                cv.circle(p["at"], p["drill"] / 2, C["drill"])
    for x0, x1 in ((xs[0], xs[1]),):
        cv.line([(x0, ys[0]), (x1, ys[0]), (x1, ys[1]), (x0, ys[1]), (x0, ys[0])], C["edge"], 0.2)
    # labels: each reference at its footprint, moved clear of labels already placed
    placed = []
    for ref in sorted(refs, key=MS.refkey):
        fp = B["fps"].get(ref)
        if not fp:
            continue
        pts = [q for c in fp["court"] for q in c] or [p["at"] for p in fp["pads"]]
        bx0, by0 = min(q[0] for q in pts), min(q[1] for q in pts)
        bx1, by1 = max(q[0] for q in pts), max(q[1] for q in pts)
        cands = [((bx0 + bx1) / 2, (by0 + by1) / 2), ((bx0 + bx1) / 2, by0 - 1.2), ((bx0 + bx1) / 2, by1 + 1.2),
                 (bx0 - 2.5, (by0 + by1) / 2), (bx1 + 2.5, (by0 + by1) / 2)]
        f = ImageFont.truetype(FONT_B, int(15 * SS))
        for c in cands:
            px = cv.P(c)
            bb = cv.d.textbbox(px, ref, font=f, anchor="mm")
            if not any(bb[0] < q[2] and q[0] < bb[2] and bb[1] < q[3] and q[1] < bb[3] for q in placed):
                cv.text(px, ref, 15, C["label"], bold=True)
                placed.append((bb[0] - 4 * SS, bb[1] - 2 * SS, bb[2] + 4 * SS, bb[3] + 2 * SS))
                break
    # title and legend
    cv.text((22 * SS, 22 * SS), title, 24, C["title"], bold=True, halo=False, anchor="lm")
    n_lit = len({t["net"] for t in lit})
    legend = (f"{len([r for r in refs if r in B['fps']])} parts, {n_lit} nets' tracks lit  ·  "
              "orange: this section (front copper bright, back copper darker; dashed courtyard: part on the back)")
    cv.text((22 * SS, 48 * SS), legend, 14, C["sub"], halo=False, anchor="lm")
    cv.save(path)
    return n_lit


# ==================================================================== the manifest
def section_nets(sec_id, board_refs):
    nets = set()
    for board, refs in board_refs.items():
        parts = TP.parts(MS.BOARDS[board][1])
        for r in refs:
            nets |= {n for n in parts[r].pins.values() if n}
    return sorted(n for n in nets if n not in RAILS or n in RAIL_HOME.get(sec_id, set()))


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(out, exist_ok=True)
    for p in TP.PARTS:
        MS.symbol_for(p)
    boards = {b: load(b) for b in ("drv", "disp")}
    per = {}                                    # section id -> {board: [refs]}
    for b in ("drv", "disp"):
        for sec, refs in MS.sections_for(b):
            per.setdefault(sec["id"], {})[b] = refs
    svgs = {b: {sid: v for k, v, sid in MS.sheet_svgs(b)} for b in ("drv", "disp")}
    manifest = []
    for sec in MS.SECTIONS:
        if sec["id"] not in per:
            continue
        br = per[sec["id"]]
        nets = section_nets(sec["id"], br)
        entry = dict(id=sec["id"], title=sec.get("manifest_title", sec["title"]),
                     boards=[MS.BOARDS[b][0] for b in ("drv", "disp") if b in br],
                     summary=sec.get("summary", ""), schematic=[], layout=[],
                     parts=sorted({r for refs in br.values() for r in refs}, key=MS.refkey), nets=nets)
        for b in ("drv", "disp"):
            if b not in br:
                continue
            sv = svgs[b].get(sec["id"])
            if sv and os.path.exists(os.path.join(out, sv)):
                entry["schematic"].append(sv)
            elif sv:
                print(f"  note: {sv} is not in {out} yet (export the schematic SVGs first)")
            png = f"layout-{b}-{sec['id']}.png"
            lit = set() if sec["id"] in NO_TRACKS else set(nets)
            n = render(b, boards[b], sec, br[b], lit, os.path.join(out, png))
            entry["layout"].append(png)
            print(f"  {png:34s} {len(br[b]):3d} parts, {n:3d} nets lit, "
                  f"{os.path.getsize(os.path.join(out, png)) // 1024:4d} kB")
        manifest.append(entry)
    with open(os.path.join(out, "sections.json"), "w", encoding="utf8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1)
    print(f"wrote {os.path.join(out, 'sections.json')} ({len(manifest)} sections)")


if __name__ == "__main__":
    main()
