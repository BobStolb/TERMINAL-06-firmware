#!/usr/bin/env python3
"""Read the fab zips back, independently of KiCad: the checks that look at the Gerbers and drills themselves.

    python3 tools/gerbers.py gold ZIP_OR_DIR        # is the fascia's gold copper exposed by openings in the front mask?
    python3 tools/gerbers.py sizes ZIP_OR_DIR       # smallest silk aperture, smallest drills, board size, mask web
    (tools/mkfab.sh calls "gold"; tools/dfm_check.py calls the functions here)

Nothing here calls KiCad. It parses the Gerber (RS-274X, mm) and Excellon files of a fab package, the
way KiCad 10 writes them: circle, rectangle and obround apertures, aperture macros (RoundRect, outlines),
draws, arcs, regions, flashes, and light/clear polarity. Copper and mask are rasterised at 40 pixels per
mm (0.025 mm a pixel) for the two area checks, so those numbers carry about +-0.03 mm of rounding.

Needs python3 with numpy, scipy and Pillow (the area checks only; the aperture, drill and outline
readings need nothing).
"""
import io, math, os, re, sys, zipfile

PPM = 40.0                       # pixels per mm for the raster checks
EXPOSE = 0.05                    # copper past the mask opening, each side (fascia_art.GOLD_GROW)

LAYER_TAGS = {                   # KiCad's file names: <board>-<tag>.<ext>
    "F_Cu": r"-F_Cu\.gtl$", "B_Cu": r"-B_Cu\.gbl$", "F_Mask": r"-F_Mask\.gts$", "B_Mask": r"-B_Mask\.gbs$",
    "F_Silk": r"-F_Silkscreen\.gto$", "B_Silk": r"-B_Silkscreen\.gbo$", "F_Paste": r"-F_Paste\.gtp$",
    "B_Paste": r"-B_Paste\.gbp$", "Edge": r"-Edge_Cuts\.gm1$", "PTH": r"-PTH\.drl$", "NPTH": r"-NPTH\.drl$",
    "Job": r"-job\.gbrjob$",
}


def load(path):
    """{layer tag: text} of a fab zip, or of a folder of the same files."""
    if os.path.isdir(path):
        names = sorted(os.listdir(path))
        read = lambda n: open(os.path.join(path, n), encoding="latin-1").read()
    else:
        z = zipfile.ZipFile(path)
        names = sorted(z.namelist())
        read = lambda n: z.read(n).decode("latin-1")
    out = {}
    for tag, pat in LAYER_TAGS.items():
        for n in names:
            if re.search(pat, n):
                out[tag] = read(n)
                out[tag + ".name"] = n
    return out


# ================================================================================ Gerber
def _ev(expr, params):
    """A macro argument: numbers, $n, + - x / and brackets."""
    e = re.sub(r"\$(\d+)", lambda m: repr(params[int(m.group(1)) - 1]) if int(m.group(1)) - 1 < len(params) else "0.0", expr)
    e = e.replace("x", "*").replace("X", "*")
    if not re.fullmatch(r"[0-9eE+\-*/(). ]*", e):
        raise ValueError("macro expression %r" % expr)
    return float(eval(e, {"__builtins__": {}}))


def _rot(pts, deg):
    if not deg:
        return pts
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return [(x * c - y * s, x * s + y * c) for x, y in pts]


def _rect(cx, cy, w, h, deg=0.0):
    pts = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    return [(x + cx, y + cy) for x, y in _rot(pts, deg)]


def _macro_shapes(lines, params):
    """The shapes of one macro instance: [('circle', cx, cy, r, exposure) | ('poly', pts, exposure)]."""
    params = list(params)
    shapes = []
    for ln in lines:
        ln = ln.strip()
        if not ln or ln[0] == "0" and (len(ln) == 1 or ln[1] == " "):
            continue
        m = re.match(r"\$(\d+)=(.*)", ln)
        if m:
            k = int(m.group(1))
            while len(params) < k:
                params.append(0.0)
            params[k - 1] = _ev(m.group(2), params)
            continue
        a = [x for x in ln.split(",")]
        code = int(a[0])
        v = [_ev(x, params) for x in a[1:]]
        ex = v[0] if v else 1
        if code == 1:                      # circle: exposure, diameter, cx, cy [, rotation]
            c = _rot([(v[2], v[3])], v[4] if len(v) > 4 else 0.0)[0]
            shapes.append(("circle", c[0], c[1], v[1] / 2, ex))
        elif code == 20:                   # vector line: exposure, width, x1, y1, x2, y2, rotation
            w, x1, y1, x2, y2 = v[1:6]
            L = math.hypot(x2 - x1, y2 - y1) or 1e-9
            nx, ny = -(y2 - y1) / L * w / 2, (x2 - x1) / L * w / 2
            pts = [(x1 + nx, y1 + ny), (x2 + nx, y2 + ny), (x2 - nx, y2 - ny), (x1 - nx, y1 - ny)]
            shapes.append(("poly", _rot(pts, v[6] if len(v) > 6 else 0.0), ex))
        elif code == 21:                   # centre line: exposure, w, h, cx, cy, rotation
            shapes.append(("poly", _rot(_rect(v[3], v[4], v[1], v[2]), v[5] if len(v) > 5 else 0.0), ex))
        elif code == 4:                    # outline: exposure, n, x0, y0 ... xn, yn, rotation
            n = int(v[1])
            pts = [(v[2 + 2 * i], v[3 + 2 * i]) for i in range(n + 1)]
            shapes.append(("poly", _rot(pts, v[2 + 2 * (n + 1)] if len(v) > 2 + 2 * (n + 1) else 0.0), ex))
        elif code == 5:                    # polygon: exposure, vertices, cx, cy, diameter, rotation
            n, cx, cy, d = int(v[1]), v[2], v[3], v[4]
            rot = v[5] if len(v) > 5 else 0.0
            pts = [(cx + d / 2 * math.cos(2 * math.pi * i / n), cy + d / 2 * math.sin(2 * math.pi * i / n)) for i in range(n)]
            shapes.append(("poly", _rot(pts, rot), ex))
        else:
            raise ValueError("macro primitive %d is not supported" % code)
    return shapes


class Gerber:
    """prims: ('draw', pts, width, dark) | ('region', [contours], dark) | ('flash', (x, y), aperture code, dark)."""

    def __init__(self, text):
        self.ap = {}          # code -> ('C', d) | ('R', w, h) | ('O', w, h) | ('P', d, n, rot) | ('M', name, params)
        self.macros = {}
        self.prims = []
        self.used = set()     # aperture codes that draw or flash (not region contours)
        self._parse(text)

    def _parse(self, text):
        dec, unit = 6, 1.0
        dark, interp, multi = True, 1, True
        cur = (0.0, 0.0)
        code = None
        region = None         # list of contours while between G36 and G37
        contour = None
        for m in re.finditer(r"%([^%]*)%|([^%*]*)\*", text):
            ext, blk = m.group(1), m.group(2)
            if ext is not None:
                parts = [p.strip() for p in ext.replace("\r", "").replace("\n", "").split("*") if p.strip()]
                if not parts:
                    continue
                head = parts[0]
                f = re.match(r"FS([LT])[AI]X(\d)(\d)Y(\d)(\d)", head)
                if f:
                    if f.group(1) != "L":
                        raise ValueError("only leading-zero-omitted Gerber is read")
                    dec = int(f.group(3))
                elif head.startswith("MOIN"):
                    unit = 25.4
                elif head.startswith("MOMM"):
                    unit = 1.0
                elif head.startswith("ADD"):
                    a = re.match(r"ADD(\d+)([A-Za-z_][\w.$]*)(?:,(.*))?$", head)
                    c, name, par = int(a.group(1)), a.group(2), a.group(3)
                    v = [float(x) * unit for x in par.split("X")] if par else []
                    if name == "C":
                        self.ap[c] = ("C", v[0])
                    elif name == "R":
                        self.ap[c] = ("R", v[0], v[1])
                    elif name == "O":
                        self.ap[c] = ("O", v[0], v[1])
                    elif name == "P":
                        self.ap[c] = ("P", v[0], int(v[1]), v[2] if len(v) > 2 else 0.0)
                    else:
                        self.ap[c] = ("M", name, v)
                elif head.startswith("AM"):
                    self.macros[head[2:]] = parts[1:]
                elif head == "LPD":
                    dark = True
                elif head == "LPC":
                    dark = False
                continue
            blk = blk.strip().replace("\n", "").replace("\r", "")
            if not blk or blk.startswith("G04"):
                continue
            if blk.startswith("M02"):
                break
            t = re.findall(r"([GDXYIJ])(-?\d+)", blk)
            vals = {}
            ops = []
            for k, s in t:
                if k == "G":
                    g = int(s)
                    if g in (1, 2, 3):
                        interp = g
                    elif g == 75:
                        multi = True
                    elif g == 74:
                        multi = False
                    elif g == 36:
                        region, contour = [], None
                    elif g == 37:
                        if contour and len(contour) > 1:
                            region.append(contour)
                        if region:
                            self.prims.append(("region", region, dark))
                        region, contour = None, None
                elif k == "D":
                    d = int(s)
                    if d >= 10:
                        code = d
                    else:
                        ops.append(d)
                else:
                    vals[k] = int(s) / (10 ** dec) * unit
            if not ops:
                continue
            op = ops[-1]
            nxt = (vals.get("X", cur[0]), vals.get("Y", cur[1]))
            if op == 2:
                if region is not None:
                    if contour and len(contour) > 1:
                        region.append(contour)
                    contour = [nxt]
                cur = nxt
            elif op == 1:
                pts = [cur, nxt]
                if interp in (2, 3):
                    if not multi:
                        raise ValueError("single-quadrant arcs are not read")
                    pts = self._arc(cur, nxt, vals.get("I", 0.0), vals.get("J", 0.0), interp == 2)
                if region is not None:
                    if contour is None:
                        contour = [cur]
                    contour.extend(pts[1:])
                else:
                    self.used.add(code)
                    w = self.ap[code][1] if self.ap.get(code, ("",))[0] == "C" else 0.0
                    self.prims.append(("draw", pts, w, dark))
                cur = nxt
            elif op == 3:
                self.used.add(code)
                self.prims.append(("flash", nxt, code, dark))
                cur = nxt

    @staticmethod
    def _arc(a, b, i, j, cw):
        c = (a[0] + i, a[1] + j)
        r = math.hypot(i, j)
        a0, a1 = math.atan2(a[1] - c[1], a[0] - c[0]), math.atan2(b[1] - c[1], b[0] - c[0])
        if cw:
            if a1 >= a0 - 1e-12:
                a1 -= 2 * math.pi
        else:
            if a1 <= a0 + 1e-12:
                a1 += 2 * math.pi
        step = 2 * math.acos(max(0.0, 1 - 0.004 / r)) if r > 0.004 else 0.5
        n = max(4, int(abs(a1 - a0) / step) + 1)
        pts = [(c[0] + r * math.cos(a0 + (a1 - a0) * k / n), c[1] + r * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n + 1)]
        pts[0], pts[-1] = a, b
        return pts

    # ------------------------------------------------------------------ shapes of an aperture
    def shapes(self, code):
        a = self.ap[code]
        if a[0] == "C":
            return [("circle", 0.0, 0.0, a[1] / 2, 1)]
        if a[0] == "R":
            return [("poly", _rect(0, 0, a[1], a[2]), 1)]
        if a[0] == "O":
            w, h = a[1], a[2]
            if abs(w - h) < 1e-9:
                return [("circle", 0.0, 0.0, w / 2, 1)]
            if w > h:
                d = (w - h) / 2
                return [("poly", _rect(0, 0, w - h, h), 1), ("circle", -d, 0.0, h / 2, 1), ("circle", d, 0.0, h / 2, 1)]
            d = (h - w) / 2
            return [("poly", _rect(0, 0, w, h - w), 1), ("circle", 0.0, -d, w / 2, 1), ("circle", 0.0, d, w / 2, 1)]
        if a[0] == "P":
            d, n, rot = a[1], a[2], a[3]
            return [("poly", _rot([(d / 2 * math.cos(2 * math.pi * i / n), d / 2 * math.sin(2 * math.pi * i / n)) for i in range(n)], rot), 1)]
        return _macro_shapes(self.macros[a[1]], a[2])

    # ------------------------------------------------------------------ readings
    def bbox(self):
        xs, ys = [], []
        for p in self.prims:
            if p[0] == "draw":
                xs += [q[0] for q in p[1]]
                ys += [q[1] for q in p[1]]
            elif p[0] == "region":
                for c in p[1]:
                    xs += [q[0] for q in c]
                    ys += [q[1] for q in c]
            else:
                xs.append(p[1][0])
                ys.append(p[1][1])
        return (min(xs), min(ys), max(xs), max(ys)) if xs else None

    def smallest_aperture(self):
        """The smallest circle (or smaller side of another aperture) that a draw or flash uses; None if none."""
        sizes = []
        for c in self.used:
            a = self.ap[c]
            if a[0] == "C" and a[1] > 0:
                sizes.append(a[1])
            elif a[0] in ("R", "O"):
                sizes.append(min(a[1], a[2]))
        return min(sizes) if sizes else None

    def count(self):
        k = {"draw": 0, "region": 0, "flash": 0}
        for p in self.prims:
            k[p[0]] += 1
        return k


# ================================================================================ Excellon
def excellon(text):
    """({tool: diameter mm}, {tool: hits}) of a KiCad drill file (metric)."""
    tools, hits, cur = {}, {}, None
    inch = "INCH" in text.split("%")[0]
    for ln in text.splitlines():
        ln = ln.strip()
        m = re.match(r"T(\d+)C([\d.]+)", ln)
        if m:
            tools[int(m.group(1))] = float(m.group(2)) * (25.4 if inch else 1.0)
            continue
        m = re.fullmatch(r"T(\d+)", ln)
        if m:
            cur = int(m.group(1))
            hits.setdefault(cur, 0)
            continue
        if cur is not None and re.match(r"X[-\d.]+Y[-\d.]+", ln):
            hits[cur] += 1
    return tools, hits


def job_size(text):
    m = re.search(r'"Size"\s*:\s*\{\s*"X"\s*:\s*([\d.]+)\s*,\s*"Y"\s*:\s*([\d.]+)', text or "")
    return (float(m.group(1)), float(m.group(2))) if m else None


# ================================================================================ raster
def _np():
    try:
        import numpy as np
        from scipy import ndimage
        from PIL import Image, ImageDraw
    except ImportError as e:
        sys.exit("tools/gerbers.py: the area checks need numpy, scipy and Pillow (%s)" % e)
    return np, ndimage, Image, ImageDraw


def raster(g, bbox, ppm=PPM, only=None):
    """The dark area of a Gerber as a boolean array over bbox (x0, y0, x1, y1). only: a set of prim kinds."""
    np, ndimage, Image, ImageDraw = _np()
    x0, y0, x1, y1 = bbox
    W, H = int(math.ceil((x1 - x0) * ppm)) + 1, int(math.ceil((y1 - y0) * ppm)) + 1
    im = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(im)
    T = lambda p: ((p[0] - x0) * ppm, (y1 - p[1]) * ppm)

    def circle(c, r, v):
        cx, cy = T(c)
        d.ellipse([cx - r * ppm, cy - r * ppm, cx + r * ppm, cy + r * ppm], fill=v)

    for p in g.prims:
        if only and p[0] not in only:
            continue
        v = 255 if p[-1] else 0
        if p[0] == "draw":
            w = p[2]
            if w <= 0:
                continue
            for a, b in zip(p[1], p[1][1:]):           # a round-ended stroke: one quad a segment and a disc at each end
                L = math.hypot(b[0] - a[0], b[1] - a[1])
                if L > 1e-9:
                    nx, ny = -(b[1] - a[1]) / L * w / 2, (b[0] - a[0]) / L * w / 2
                    d.polygon([T((a[0] + nx, a[1] + ny)), T((b[0] + nx, b[1] + ny)), T((b[0] - nx, b[1] - ny)), T((a[0] - nx, a[1] - ny))], fill=v)
                circle(a, w / 2, v)
            circle(p[1][-1], w / 2, v)
        elif p[0] == "region":
            for c in p[1]:
                d.polygon([T(q) for q in c], fill=v)
        else:
            ox, oy = p[1]
            for s in g.shapes(p[2]):
                sv = v if s[-1] else (0 if v else 255)
                if s[0] == "circle":
                    circle((ox + s[1], oy + s[2]), s[3], sv)
                else:
                    d.polygon([T((ox + q[0], oy + q[1])) for q in s[1]], fill=sv)
    return np.asarray(im) > 0


def disk(r_px):
    np = _np()[0]
    k = int(math.ceil(r_px))
    y, x = np.ogrid[-k:k + 1, -k:k + 1]
    return x * x + y * y <= r_px * r_px


# ================================================================================ the gold check
def gold_check(files, selftest=False):
    """Is the fascia's gold really exposed? Returns (ok, [lines]).

    F.Cu carries the gold (the front has no other copper); F.Mask must open over it. The art board puts the
    copper EXPOSE (0.05 mm) wider each side than the mask opening, so:
      * the copper core (copper eroded by 0.09 mm) must lie inside the openings. Mask webs narrower than
        0.15 mm are allowed and counted (the art leaves a few 0.1 mm webs where a trace ends inside a ring);
        a wider piece of covered copper is a FAIL;
      * the openings made by draws and regions (not the flashes, which are the holes' own) must lie inside the
        copper: an opening past the copper would show bare board.
    selftest=True drops the gold's openings from the mask, which must FAIL."""
    np, ndimage, Image, ImageDraw = _np()
    lines, ok = [], True
    cu, mk = Gerber(files["F_Cu"]), Gerber(files["F_Mask"])
    if selftest:
        mk.prims = [p for p in mk.prims if p[0] == "flash"]
    n = cu.count()
    if not cu.prims:
        return False, ["FAIL  F.Cu carries no copper at all: no gold"], {"under_mm2": None, "webs": 0, "stray_mm2": 0.0, "pct": 0.0}
    box = Gerber(files["Edge"]).bbox()
    bbox = (box[0] - 1, box[1] - 1, box[2] + 1, box[3] + 1)
    C = raster(cu, bbox)
    O = raster(mk, bbox)
    Og = raster(mk, bbox, only={"draw", "region"})
    px = 1.0 / (PPM * PPM)                                           # mm2 a pixel
    core = ndimage.binary_erosion(C, structure=disk(0.09 * PPM))
    under = core & ~O                                                # copper core with mask on it
    solid = ndimage.binary_opening(under, structure=disk(0.075 * PPM))   # ... in a piece wider than 0.15 mm
    webs, nweb = ndimage.label(under & ~ndimage.binary_dilation(solid, structure=disk(0.075 * PPM + 1)))
    nweb = int((np.bincount(webs.ravel())[1:] >= 4).sum()) if nweb else 0
    stray_px = ndimage.label(Og & ~C)[0]
    stray_area = sum(int(k) for k in np.bincount(stray_px.ravel())[1:] if k >= 4) * px
    lab, nc = ndimage.label(core)
    hit = len(set(np.unique(lab[core & O])) - {0}) if nc else 0
    lines.append("F.Cu: %d draws, %d regions, %d flashes; gold copper %.1f mm2, mask opened over it %.1f mm2 (%.0f%% of the copper)" % (
        n["draw"], n["region"], n["flash"], C.sum() * px, (C & O).sum() * px, 100.0 * (C & O).sum() / max(1, C.sum())))
    if solid.sum():
        ok = False
        lines.append("FAIL  %.2f mm2 of the gold's copper lies under solder mask, in pieces wider than 0.15 mm (no opening)" % (solid.sum() * px))
    else:
        lines.append("PASS  the gold's copper core is inside the F.Mask openings: nothing wider than 0.15 mm is under mask; "
                     "%d thin mask web(s) over gold, %.3f mm2 in all" % (nweb, under.sum() * px))
    if nc and hit < nc:
        ok = False
        lines.append("FAIL  %d of %d gold pieces have no opening" % (nc - hit, nc))
    if stray_area > 0.005:
        ok = False
        lines.append("FAIL  %.2f mm2 of mask opening lies outside the gold's copper" % stray_area)
    else:
        lines.append("PASS  every gold opening in F.Mask lies inside the F.Cu copper (%.3f mm2 outside, pixel noise)" % stray_area)
    stats = {"under_mm2": solid.sum() * px, "webs": nweb, "stray_mm2": stray_area, "pct": 100.0 * (C & O).sum() / max(1, C.sum())}
    return ok, lines, stats


# ================================================================================ the Gerber-side DFM readings
def readings(files):
    """{'silk': [(file, smallest aperture)], 'drills': {'PTH': (min, hits, tools)...}, 'size': (w, h), 'job': (w, h)}."""
    r = {"silk": [], "drills": {}}
    for tag in ("F_Silk", "B_Silk"):
        if tag in files:
            g = Gerber(files[tag])
            r["silk"].append((files[tag + ".name"], g.smallest_aperture(), g.count()))
    for tag in ("PTH", "NPTH"):
        if tag in files:
            tools, hits = excellon(files[tag])
            used = {t: tools[t] for t in tools if hits.get(t)}
            r["drills"][tag] = (min(used.values()) if used else None, sum(hits.values()), sorted(set(used.values())))
        else:
            r["drills"][tag] = (None, 0, [])
    b = Gerber(files["Edge"]).bbox()
    r["size"] = (b[2] - b[0], b[3] - b[1])
    r["job"] = job_size(files.get("Job"))
    return r


def mask_web(files, tag, limit=0.1):
    """The narrowest web of solder mask on one face (a strip of mask between two openings, or an opening and the
    board edge). Returns (worst web in mm to the nearest pixel (None: wider than the largest tried), ok, [(x, y, mm2)]
    where the pieces thinner than the limit are, largest first; empty when ok).
    Mask material M = board area minus the openings; M is opened with a disk of growing diameter, and a piece
    that disappears (4 pixels or more, 0.0025 mm2) is a web narrower than the disk."""
    np, ndimage, Image, ImageDraw = _np()
    mk = Gerber(files[tag])
    edge = Gerber(files["Edge"])
    box = edge.bbox()
    bbox = (box[0] - 0.5, box[1] - 0.5, box[2] + 0.5, box[3] + 0.5)
    O = raster(mk, bbox)
    E = raster(edge, bbox, only={"draw"})
    board = ndimage.binary_fill_holes(E)
    if board.sum() < 0.5 * (box[2] - box[0]) * (box[3] - box[1]) * PPM * PPM:   # outline not closed: use its box
        board = np.zeros_like(O)
        board[int(0.5 * PPM):-int(0.5 * PPM), int(0.5 * PPM):-int(0.5 * PPM)] = True
    M = board & ~O
    dist = ndimage.distance_transform_edt(M)

    def thin(diam_px, where=False):
        r = diam_px / 2.0
        eroded = dist > r - 1e-9
        back = ndimage.distance_transform_edt(~eroded) <= r + 1e-9
        t = M & ~back
        lab, n = ndimage.label(t)
        if not n:
            return [] if where else 0
        sizes = np.bincount(lab.ravel())[1:]
        if not where:
            return int((sizes >= 4).sum())
        out = []
        for i in np.argsort(-sizes)[:8]:
            if sizes[i] < 4:
                break
            ys, xs = np.where(lab == i + 1)
            out.append((float(bbox[0] + xs.mean() / PPM), float(bbox[3] - ys.mean() / PPM), float(sizes[i] / (PPM * PPM))))
        return out

    need_px = int(round(limit * PPM))
    ok = thin(need_px) == 0
    lo, hi = 1, 14                     # diameters in pixels: the largest that removes nothing = the narrowest web
    if thin(hi):
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if thin(mid):
                hi = mid
            else:
                lo = mid
        worst = lo / PPM
    else:
        worst = None                   # no web narrower than hi pixels
    return worst, ok, ([] if ok else thin(need_px, where=True))


# ================================================================================ command line
def main(argv):
    if len(argv) < 3 or argv[1] not in ("gold", "sizes"):
        print(__doc__)
        return 2
    files = load(argv[2])
    if argv[1] == "gold":
        ok, lines, _ = gold_check(files)
        for ln in lines:
            print("    " + ln)
        bad_ok, bad_lines, bad = gold_check(files, selftest=True)
        if bad_ok:
            print("    self-test, the gold's openings removed from F.Mask: PASS, THE CHECK CANNOT FAIL")
        else:
            print("    self-test, the gold's openings removed from F.Mask: FAIL, as it must (%.0f mm2 of gold copper under mask)" % bad["under_mm2"])
        return 0 if ok and not bad_ok else 1
    r = readings(files)
    print(r)
    for tag in ("F_Mask", "B_Mask"):
        print(tag, mask_web(files, tag))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
