#!/usr/bin/env python3
"""Independent audit of the board, checking what the other tools do NOT.

checkcopper.py verifies that each pad is TOUCHED by a track of its net. That is a
weaker claim than it sounds: a net split into two islands passes it, because every
pad is touched by something. This checks the real thing - that all pads of a net form
ONE connected component through tracks and vias.

It also checks the things a copper checker never looks at: silkscreen over pads,
silkscreen over silkscreen, and whether every mask opening is actually smaller than
the copper it exposes.

A POURED net gets a different test. "GND is a zone" is a claim, not a fact: a pour is
cut into islands by whatever crosses it, and a pad in a walled-off island is as
disconnected as an unrouted one. So the zone is rasterised at 0.15 mm - polygon minus
every other net's pads, tracks, vias and clearance, minus one cell of erosion so a
channel thinner than the zone's own min_thickness does not count - and flood-filled
from one pad. Any pad of that net the flood does not reach is reported.
"""
import re, sys, math
from collections import defaultdict

def extract_blocks(src, tag):
    """Every top-level (tag ...) block, paren-depth counted rather than a
    fixed-shape regex. A non-greedy \\n\\t) boundary (the old approach) works
    for a bare unfilled zone, but a real KiCad fill embeds filled_polygon
    sub-blocks with their own nested closes, so the first \\n\\t) it finds is
    usually deep inside the fill data, not the end of the zone - silently
    truncating the block and pulling boundary points from the wrong place.
    """
    out = []
    key = '(' + tag
    i = 0
    while True:
        i = src.find(key, i)
        if i < 0:
            break
        nxt = i + len(key)
        if key[-1] != '"' and nxt < len(src) and src[nxt] not in ' \n':
            i = nxt
            continue
        depth, j, in_str, esc = 0, i, False, False
        while j < len(src):
            ch = src[j]
            if in_str:
                if esc: esc = False
                elif ch == '\\': esc = True
                elif ch == '"': in_str = False
            elif ch == '"': in_str = True
            elif ch == '(': depth += 1
            elif ch == ')':
                depth -= 1
                if depth == 0:
                    j += 1
                    break
            j += 1
        out.append(src[i:j])
        i = j
    return out

def extract_footprints(src):
    """Every top-level (footprint ...) block, re-indented to the column-0
    convention the field regexes below are written against - this repo's own
    generators outdent footprints to column 0, real KiCad indents them
    normally as a child of kicad_pcb (one tab deeper throughout).
    """
    out = []
    for block in extract_blocks(src, 'footprint "'):
        i = src.find(block)
        line_start = src.rfind('\n', 0, i) + 1
        base_indent = i - line_start
        if base_indent > 0:
            cut = '\t' * base_indent
            lines = block.split('\n')
            block = '\n'.join([lines[0]] + [ln[base_indent:] if ln.startswith(cut) else ln
                                             for ln in lines[1:]])
        out.append(block)
    return out

SRC = open(sys.argv[1], encoding="utf8").read()
issues = []
def bad(cat, msg): issues.append((cat, msg))

# ------------------------------------------------------------------ parse
def txtbox(t, x, y, sz):
    return (x, y, max(len(t),1)*sz*0.78 + sz*0.3, sz*1.35)

pads, silk, refs = [], [], []
for f in extract_footprints(SRC):
    ref = (re.search(r'\(property "Reference" "([^"]+)"', f) or [None,"?"])[1]
    at = re.search(r'\n\t\(at ([\d.-]+) ([\d.-]+)\)', f)
    if not at: continue
    ox, oy = float(at.group(1)), float(at.group(2))
    for m in re.finditer(r'\(pad "([^"]*)" (\w+) (\w+)\n\t\t\(at ([\d.-]+) ([\d.-]+)\)\n'
                         r'\t\t\(size ([\d.]+) ([\d.]+)\)([\s\S]{0,320}?)\n\t\)', f):
        b = m.group(8)
        net = (re.search(r'\(net (?:\d+ )?"([^"]*)"', b) or [None,None])[1]
        lay = (re.search(r'\(layers ([^)]*)\)', b) or [None,""])[1]
        L = ["F.Cu","B.Cu"] if ("*.Cu" in lay or "F&B" in lay) else \
            [x for x in ("F.Cu","B.Cu") if x in lay]
        w, h = float(m.group(6)), float(m.group(7))
        pads.append({"id": f"{ref}.{m.group(1)}", "x": ox+float(m.group(4)),
                     "y": oy+float(m.group(5)), "w": w, "h": h, "net": net, "layers": L,
                     "kind": m.group(2),
                     "round": m.group(3) == "circle" or (m.group(3) == "oval" and w == h)})
    for pm in re.finditer(r'\(property "(Reference|Value)" "([^"]*)"\n\t\t\(at ([\d.-]+) ([\d.-]+)[^)]*\)\n'
                          r'\t\t\(layer "([^"]+)"\)([\s\S]{0,200}?)\n\t\)', f):
        if "(hide yes)" in pm.group(6) or not pm.group(2): continue
        sz = float((re.search(r'\(size ([\d.]+)', pm.group(6)) or [None,"1"])[1])
        if "SilkS" in pm.group(5):
            refs.append({"t": pm.group(2), "layer": pm.group(5),
                         "box": txtbox(pm.group(2), ox+float(pm.group(3)), oy+float(pm.group(4)), sz)})
for m in re.finditer(r'\(gr_text "([^"]*)"\n\t\t\(at ([\d.-]+) ([\d.-]+) [\d.-]+\)\n'
                     r'\t\t\(layer "([^"]+)"\)[\s\S]{0,160}?\(size ([\d.]+)', SRC):
    if "SilkS" in m.group(4):
        silk.append({"t": m.group(1), "layer": m.group(4),
                     "box": txtbox(m.group(1), float(m.group(2)), float(m.group(3)), float(m.group(5)))})

# A segment/via's (net ...) field is either just a code, resolved through the
# net table, or - on every save this KiCad setup has actually produced - the
# bare name with no code at all. "net" ends up holding a net NAME string
# either way, so nothing downstream has to care which form the file was in.
netname = {int(a): b for a, b in re.findall(r'^\t\(net (\d+) "([^"]*)"', SRC, re.M)}
def _net_of(code, name):
    return name if name else netname.get(int(code) if code else -1)

tracks = [{"a": (float(g[0]), float(g[1])), "b": (float(g[2]), float(g[3])),
           "w": float(g[4]), "layer": g[5], "net": _net_of(g[6], g[7])}
          for g in re.findall(r'\(segment\n\t\t\(start ([\d.-]+) ([\d.-]+)\)\n\t\t\(end ([\d.-]+) ([\d.-]+)\)\n'
                              r'\t\t\(width ([\d.]+)\)\n\t\t\(layer "([^"]+)"\)\n\t\t\(net (?:(\d+)|"([^"]*)")\)', SRC)]
vias = [{"x": float(g[0]), "y": float(g[1]), "d": float(g[2]), "net": _net_of(g[3], g[4])}
        for g in re.findall(r'\(via\n\t\t\(at ([\d.-]+) ([\d.-]+)\)\n\t\t\(size ([\d.]+)\)'
                            r'[\s\S]{0,90}?\(net (?:(\d+)|"([^"]*)")\)', SRC)]

zones = []
for blk in extract_blocks(SRC, 'zone'):
    nn = re.search(r'\(net_name "([^"]*)"', blk) or re.search(r'\(net \d* ?"([^"]*)"\)', blk)
    ly = re.search(r'\(layers? "([^"]+)"\)', blk)
    cl = re.search(r'\(connect_pads(?: \w+)?\n\t\t\t\(clearance ([\d.]+)\)', blk)   # optional mode: yes, thru_hole_only
    # the zone's own boundary is (polygon (pts ...)) - a filled zone also carries
    # (filled_polygon ...) blocks (KiCad's own computed result, not needed here,
    # and NOT what "\(polygon\n" matches - filled_polygon fails that literal
    # immediately after the "("), so this stays scoped to the true outline even
    # when real fill data is present.
    outline = re.search(r'\(polygon\n[\s\S]*?\n\t\t\)', blk)
    pts = [(float(a), float(b)) for a, b in
           re.findall(r'\(xy ([\d.-]+) ([\d.-]+)\)', outline.group(0) if outline else "")]
    if nn and ly and len(pts) >= 3:
        zones.append({"net": nn.group(1), "layer": ly.group(1),
                      "clr": float(cl.group(1)) if cl else 0.5, "pts": pts})
POURED = {z["net"] for z in zones}

# ------------------------------------------------------------------ A. real net connectivity
def on_pad(p, x, y, tol=0.01):
    return (abs(x-p["x"]) <= p["w"]/2+tol) and (abs(y-p["y"]) <= p["h"]/2+tol)
def pt_seg(p, a, b):
    dx, dy = b[0]-a[0], b[1]-a[1]; L = dx*dx+dy*dy
    t = 0 if L == 0 else max(0, min(1, ((p[0]-a[0])*dx + (p[1]-a[1])*dy)/L))
    return math.hypot(p[0]-(a[0]+t*dx), p[1]-(a[1]+t*dy))
def touches(A, B):
    """Do two copper items of one net join? Items are ("pad"|"trk"|"via", index)."""
    if A[0] == "trk" and B[0] == "trk":
        s, t = tracks[A[1]], tracks[B[1]]
        return s["layer"] == t["layer"] and min(pt_seg(s["a"], t["a"], t["b"]), pt_seg(s["b"], t["a"], t["b"]),
                                                pt_seg(t["a"], s["a"], s["b"]), pt_seg(t["b"], s["a"], s["b"])) < 0.01
    if "trk" in (A[0], B[0]) and "pad" in (A[0], B[0]):
        s, p = (tracks[A[1]], pads[B[1]]) if A[0] == "trk" else (tracks[B[1]], pads[A[1]])
        return s["layer"] in p["layers"] and (on_pad(p, *s["a"]) or on_pad(p, *s["b"]))
    if A[0] == "via" and B[0] == "via":
        # two vias join only where their copper does; "any two vias of a net" hid splits
        u, v = vias[A[1]], vias[B[1]]
        return math.hypot(u["x"]-v["x"], u["y"]-v["y"]) < (u["d"]+v["d"])/2
    if "via" in (A[0], B[0]):
        v = vias[A[1] if A[0]=="via" else B[1]]
        o = B if A[0]=="via" else A
        if o[0] == "trk":
            return pt_seg((v["x"],v["y"]), tracks[o[1]]["a"], tracks[o[1]]["b"]) < 0.01
        return on_pad(pads[o[1]], v["x"], v["y"])
    return False

# An unrouted board splits every net by definition. Reporting that as a dozen faults
# buries the findings that matter, so say it once and move on.
UNROUTED = not tracks and not vias
if UNROUTED:
    print("NOTE: board carries no tracks or vias - net connectivity not applicable.\n"
          "      Placement, artwork and silkscreen are still checked below.\n")
for net in sorted({p["net"] for p in pads if p["net"]} | {v["net"] for v in vias}):
    if not net or UNROUTED or net in POURED: continue   # poured nets: section D
    items = []
    for i, p in enumerate(pads):
        if p["net"] == net: items.append(("pad", i))
    for i, t in enumerate(tracks):
        if t["net"] == net: items.append(("trk", i))
    for i, v in enumerate(vias):
        if v["net"] == net: items.append(("via", i))
    par = {k: k for k in items}
    def find(x):
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    def uni(a, b): par[find(a)] = find(b)
    for A in items:
        for B in items:
            if A < B and touches(A, B): uni(A, B)
    comps = defaultdict(list)
    for it in items: comps[find(it)].append(it)
    if len(comps) > 1:
        groups = []
        for c in comps.values():
            g = sorted(pads[i]["id"] for k, i in c if k == "pad")
            groups.append(g if g else ["(no pads)"])
        bad("NET SPLIT", f'{net} is in {len(comps)} pieces: ' +
            "  ||  ".join(", ".join(g) for g in groups))

# ------------------------------------------------------------------ B. mask openings
gold = re.findall(r'\(gr_line\n\t\t\(start ([\d.-]+) ([\d.-]+)\)\n\t\t\(end ([\d.-]+) ([\d.-]+)\)\n'
                  r'\t\t\(stroke\n\t\t\t\(width ([\d.]+)\)[\s\S]*?\(layer "(F\.Cu|F\.Mask)"\)', SRC)
cu = {(a,b,c,d): float(w) for a,b,c,d,w,L in gold if L == "F.Cu"}
mk = {(a,b,c,d): float(w) for a,b,c,d,w,L in gold if L == "F.Mask"}
for k, w in cu.items():
    if k in mk and mk[k] > w:
        bad("MASK HALO", f'gold line at ({k[0]},{k[1]}) copper {w} mm but opening {mk[k]} mm '
                         f'- {(mk[k]-w)/2:.3f} mm of bare laminate shows each side')
        break
ct = re.findall(r'\(gr_text "([^"]*)"\n\t\t\(at ([\d.-]+) ([\d.-]+) [\d.-]+\)\n\t\t\(layer "(F\.Cu|F\.Mask)"\)'
                r'[\s\S]{0,200}?\(thickness ([\d.]+)\)', SRC)
tc = {(t,x,y): float(th) for t,x,y,L,th in ct if L == "F.Cu"}
tm = {(t,x,y): float(th) for t,x,y,L,th in ct if L == "F.Mask"}
for k, th in tc.items():
    if k in tm and tm[k] > th:
        bad("MASK HALO", f'gold text "{k[0]}" copper stroke {th} mm but mask stroke {tm[k]} mm '
                         f'- every glyph gets a bare-laminate outline')
        break

# ------------------------------------------------------------------ C. silkscreen collisions
def boxes_hit(A, B, gap=0.0):
    return (abs(A[0]-B[0]) < (A[2]+B[2])/2 + gap) and (abs(A[1]-B[1]) < (A[3]+B[3])/2 + gap)
alltxt = silk + refs
for i in range(len(alltxt)):
    for j in range(i+1, len(alltxt)):
        a, b = alltxt[i], alltxt[j]
        if a["layer"] != b["layer"]: continue
        if boxes_hit(a["box"], b["box"]):
            bad("SILK/SILK", f'"{a["t"]}" and "{b["t"]}" overlap on {a["layer"]} '
                             f'near ({a["box"][0]:.1f},{a["box"][1]:.1f})')
for t in alltxt:
    side = "F.Cu" if "F." in t["layer"] else "B.Cu"
    for p in pads:
        if side not in p["layers"]: continue
        if boxes_hit(t["box"], (p["x"], p["y"], p["w"], p["h"])):
            bad("SILK/PAD", f'"{t["t"]}" ({t["layer"]}) printed over pad {p["id"]} '
                            f'at ({p["x"]:.1f},{p["y"]:.1f})')

# ------------------------------------------------------------------ D. does the pour reach?
G = 0.15
islands = []
for z in zones:
    import numpy as np
    poly = z["pts"]
    x0 = min(p[0] for p in poly); x1 = max(p[0] for p in poly)
    y0 = min(p[1] for p in poly); y1 = max(p[1] for p in poly)
    xs = np.arange(x0 + G/2, x1, G); ys = np.arange(y0 + G/2, y1, G)
    PX, PY = np.meshgrid(xs, ys)
    ok = np.zeros(PX.shape, bool)
    for i in range(len(poly)):                       # even-odd, any polygon
        ax, ay = poly[i]; bx, by = poly[(i+1) % len(poly)]
        if ay == by: continue
        ok ^= ((ay > PY) != (by > PY)) & (PX < (bx-ax) * (PY-ay) / (by-ay) + ax)

    def clear_rect(cx, cy, w, h, m):                 # knock a keep-out out of the pour
        ok[(np.abs(PX-cx) <= w/2 + m) & (np.abs(PY-cy) <= h/2 + m)] = False
    for p in pads:
        if z["layer"] not in p["layers"] or p["net"] == z["net"]: continue
        if p["round"]:
            # a round pad keeps its clearance as a circle. Knocked out as its bounding square,
            # a ring of tube pins closed the channels between neighbours that KiCad's fill
            # leaves open, and islanded pads inside the ring that are in fact joined.
            ok[np.hypot(PX-p["x"], PY-p["y"]) <= p["w"]/2 + z["clr"]] = False
        else:
            clear_rect(p["x"], p["y"], p["w"], p["h"], z["clr"])
    for t in tracks:
        if t["layer"] != z["layer"] or t["net"] == z["net"]: continue
        (ax, ay), (bx, by) = t["a"], t["b"]
        dx, dy = bx-ax, by-ay; L = dx*dx + dy*dy
        u = 0.0 if L == 0 else np.clip(((PX-ax)*dx + (PY-ay)*dy) / L, 0, 1)
        ok[np.hypot(PX - (ax + u*dx), PY - (ay + u*dy)) <= t["w"]/2 + z["clr"]] = False
    for v in vias:
        if v["net"] == z["net"]: continue
        ok[np.hypot(PX - v["x"], PY - v["y"]) <= v["d"]/2 + z["clr"]] = False

    # one cell of erosion: copper thinner than about 2G will not fill at min_thickness
    e = ok.copy()
    e[1:, :] &= ok[:-1, :]; e[:-1, :] &= ok[1:, :]
    e[:, 1:] &= ok[:, :-1]; e[:, :-1] &= ok[:, 1:]
    ok = e

    lab = -np.ones(ok.shape, int)
    nlab = 0
    from collections import deque
    H_, W_ = ok.shape
    for sy in range(H_):
        for sx in range(W_):
            if not ok[sy, sx] or lab[sy, sx] >= 0: continue
            q = deque([(sy, sx)]); lab[sy, sx] = nlab
            while q:
                cy_, cx_ = q.popleft()
                for ny, nx in ((cy_-1,cx_), (cy_+1,cx_), (cy_,cx_-1), (cy_,cx_+1)):
                    if 0 <= ny < H_ and 0 <= nx < W_ and ok[ny, nx] and lab[ny, nx] < 0:
                        lab[ny, nx] = nlab; q.append((ny, nx))
            nlab += 1

    mine = [p for p in pads if z["layer"] in p["layers"] and p["net"] == z["net"]]
    islands.append((z, PX, PY, lab))
    print(f'pour "{z["net"]}" on {z["layer"]}: {nlab} island(s), '
          f'{100.0*ok.sum()/ok.size:.0f}% of the outline is copper, '
          f'{len(mine)} pad(s) of the net')

# A poured net is one net, not one pour. An island joins it through a pad's spokes, a via
# standing in it or a track of the net lying in it, and a pad on the other face joins
# through tracks and vias exactly as in section A - a surface-mount GND pad on the back of
# a board poured on the front is reached by nothing else. So every pad of the net is
# grouped by what really connects: islands, pads, tracks and vias together.
for net in sorted(POURED):
    items = [("pad", i) for i, p in enumerate(pads) if p["net"] == net] + \
            [("trk", i) for i, t in enumerate(tracks) if t["net"] == net] + \
            [("via", i) for i, v in enumerate(vias) if v["net"] == net]
    par = {k: k for k in items}
    def find(x):
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    for A in items:
        for B in items:
            if A < B and touches(A, B): par[find(A)] = find(B)
    for zi, (z, PX, PY, lab) in enumerate(islands):
        if z["net"] != net: continue
        def near(x, y, r):
            sel = (np.abs(PX-x) <= r) & (np.abs(PY-y) <= r) & (lab >= 0)
            return set(np.unique(lab[sel]).tolist())
        for k in items:
            if k[0] == "pad":
                p = pads[k[1]]
                if z["layer"] not in p["layers"]: continue
                hit = near(p["x"], p["y"], max(p["w"], p["h"])/2 + z["clr"] + 4*G)   # by its spokes
            elif k[0] == "via":
                v = vias[k[1]]
                hit = near(v["x"], v["y"], v["d"]/2 + z["clr"] + 4*G)
            else:
                t = tracks[k[1]]
                if t["layer"] != z["layer"]: continue
                hit = near(*t["a"], t["w"]/2 + 2*G) | near(*t["b"], t["w"]/2 + 2*G)
            for h in hit:
                node = ("isl", zi, h)
                par.setdefault(node, node)
                par[find(k)] = find(node)
    groups = defaultdict(list)
    for k in items:
        if k[0] == "pad": groups[find(k)].append(pads[k[1]]["id"])
    if len(groups) > 1:
        bad("POUR SPLIT", f'{net} (poured) is in {len(groups)} pieces: ' +
            "  ||  ".join(", ".join(sorted(g)) for g in groups.values()))

# ------------------------------------------------------------------ E. is the copper any GOOD?
# Everything above this line asks whether the board is LEGAL. None of it asks whether it is WELL
# ROUTED, and the difference is not small: TS06-MAIN reached "2 findings" while carrying 476 vias
# and a ground pour that filled as 292 islands, because the only number anyone steered by was how
# many nets were left unrouted (18.09.26). These are the numbers to steer by instead.
#
# They are advice, not findings. Nothing in this section touches the exit code, because there is
# no threshold that is right for every board here - a fascia with nine nets and this one with a
# hundred and forty cannot share a number. What they can share is being LOOKED at.
import numpy as _np

def _mst(pts):
    """Euclidean minimum spanning tree over a net's own pads: the floor for any tree that touches
    all of them, obstacles, clearances and layers ignored. No real route can beat it, so
    laid/floor is a detour ratio that means the same thing on any board."""
    if len(pts) < 2:
        return 0.0
    rest, tot = list(pts[1:]), 0.0
    d = [math.dist(pts[0], q) for q in rest]
    while rest:
        k = min(range(len(rest)), key=d.__getitem__)
        tot += d[k]
        q = rest.pop(k)
        d.pop(k)
        for i, r in enumerate(rest):
            d[i] = min(d[i], math.dist(q, r))
    return tot

_len_of, _face, _grain, _ang = defaultdict(float), defaultdict(float), defaultdict(float), defaultdict(float)
for _t in tracks:
    (_ax, _ay), (_bx, _by) = _t["a"], _t["b"]
    _dx, _dy, _L = _bx - _ax, _by - _ay, math.dist(_t["a"], _t["b"])
    if _L < 1e-9:
        continue
    _len_of[_t["net"]] += _L
    _face[_t["layer"]] += _L
    # GRAIN: the convention this repo routes to is F.Cu east-west, B.Cu north-south, so that nets
    # cross between faces instead of fighting on one. A board with no grain reads about a third in
    # each column and its pour comes out as confetti.
    _along = abs(_dx) > abs(_dy) if _t["layer"] == "F.Cu" else abs(_dy) > abs(_dx)
    _grain[_t["layer"], "diagonal" if abs(abs(_dx) - abs(_dy)) < _L * 0.15
           else "along" if _along else "across"] += _L
    _a = math.degrees(math.atan2(_dy, _dx)) % 90
    _ang["orthogonal" if min(_a, 90 - _a) < 0.6 else "45" if abs(_a - 45) < 0.6 else "other"] += _L

_vias_of = defaultdict(int)
for _v in vias:
    _vias_of[_v["net"]] += 1

_padpts = defaultdict(set)
for _p in pads:
    if _p["net"]:
        _padpts[_p["net"]].add((round(_p["x"], 3), round(_p["y"], 3)))

_rows = []
for _nm, _L in _len_of.items():
    if not _nm or _nm in POURED:
        continue
    _floor = _mst(sorted(_padpts.get(_nm, ())))
    if _floor > 0.2:
        _rows.append((_L / _floor, _L, _floor, _vias_of.get(_nm, 0), len(_padpts[_nm]), _nm))
_rows.sort(reverse=True)

_cu = sum(_face.values())
_sig = sum(r[1] for r in _rows)
_flr = sum(r[2] for r in _rows)
print("QUALITY - how well routed, as opposed to how legal. None of this is a finding.")
print()
print("  copper      %8.0f mm   %.0f front / %.0f back" % (_cu, _face["F.Cu"], _face["B.Cu"]))
if _flr:
    print("  detour      %8.2fx    %.0f mm of signal against a %.0f mm floor, over %d nets"
          % (_sig / _flr, _sig, _flr, len(_rows)))
print("  vias        %8d     %.1f per net, %d of %d nets carry none"
      % (len(vias), len(vias) / max(len(_rows), 1), sum(1 for r in _rows if r[3] == 0), len(_rows)))
_at = sum(_ang.values()) or 1.0
print("  angles      " + "   ".join("%s %.0f%%" % (k, 100 * v / _at)
                                    for k, v in sorted(_ang.items(), key=lambda t: -t[1])))
for _ly in ("F.Cu", "B.Cu"):
    _tl = sum(v for (l, _), v in _grain.items() if l == _ly) or 1.0
    print("  grain %-5s %7.0f%% %-11s %.0f%% across it, %.0f%% diagonal"
          % (_ly, 100 * _grain[_ly, "along"] / _tl,
             "east-west," if _ly == "F.Cu" else "north-south,",
             100 * _grain[_ly, "across"] / _tl, 100 * _grain[_ly, "diagonal"] / _tl))
_isl = []
for _z, _PX, _PY, _lab in islands:
    _sz = _np.bincount(_lab[_lab >= 0].ravel()) if (_lab >= 0).any() else _np.zeros(0, int)
    _tot = _sz.sum() * G * G or 1.0
    _isl.append(len(_sz))
    print('  pour %-3s %-5s %4d island(s), the largest holds %.0f%% of its %.0f mm2 of copper, '
          "%d under 1 mm2" % (_z["net"], _z["layer"], len(_sz),
                              100 * (_sz.max() if _sz.size else 0) * G * G / _tot, _tot,
                              int((_sz * G * G < 1.0).sum())))
if _rows:
    print()
    print("  the copper that wanders furthest from its own floor:")
    print("     ratio     laid    floor  vias  net")
    for _r in _rows[:8]:
        print("    %6.1f %8.1f %8.1f %5d  %s" % (_r[0], _r[1], _r[2], _r[3], _r[5]))
print()
print("QSUMMARY cu=%.0f detour=%.3f vias=%d islands=%s"
      % (_cu, _sig / _flr if _flr else 0.0, len(vias), ",".join(str(i) for i in _isl) or "-"))
print()

# ------------------------------------------------------------------ report
print(f'{len(pads)} pad-layers, {len(tracks)} tracks, {len(vias)} vias, '
      f'{len(alltxt)} visible silk texts\n')
seen, cats = set(), defaultdict(int)
for c, m in issues:
    if (c, m) in seen: continue
    seen.add((c, m)); cats[c] += 1
    print(f'  [{c}] {m}')
print("\n" + (f'{len(seen)} finding(s) across {len(cats)} categories' if seen else "clean"))
sys.exit(1 if seen else 0)
