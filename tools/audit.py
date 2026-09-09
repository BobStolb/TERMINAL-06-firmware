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

SRC = open(sys.argv[1], encoding="utf8").read()
issues = []
def bad(cat, msg): issues.append((cat, msg))

# ------------------------------------------------------------------ parse
def txtbox(t, x, y, sz):
    return (x, y, max(len(t),1)*sz*0.78 + sz*0.3, sz*1.35)

pads, silk, refs = [], [], []
for f in re.findall(r'\(footprint "[^"]+"[\s\S]*?\n\)', SRC):
    ref = (re.search(r'\(property "Reference" "([^"]+)"', f) or [None,"?"])[1]
    at = re.search(r'\n\t\(at ([\d.-]+) ([\d.-]+)\)', f)
    if not at: continue
    ox, oy = float(at.group(1)), float(at.group(2))
    for m in re.finditer(r'\(pad "([^"]*)" (\w+) \w+\n\t\t\(at ([\d.-]+) ([\d.-]+)\)\n'
                         r'\t\t\(size ([\d.]+) ([\d.]+)\)([\s\S]{0,320}?)\n\t\)', f):
        b = m.group(7)
        net = (re.search(r'\(net \d+ "([^"]*)"', b) or [None,None])[1]
        lay = (re.search(r'\(layers ([^)]*)\)', b) or [None,""])[1]
        L = ["F.Cu","B.Cu"] if ("*.Cu" in lay or "F&B" in lay) else \
            [x for x in ("F.Cu","B.Cu") if x in lay]
        pads.append({"id": f"{ref}.{m.group(1)}", "x": ox+float(m.group(3)),
                     "y": oy+float(m.group(4)), "w": float(m.group(5)),
                     "h": float(m.group(6)), "net": net, "layers": L, "kind": m.group(2)})
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

tracks = [{"a": (float(g[0]), float(g[1])), "b": (float(g[2]), float(g[3])),
           "w": float(g[4]), "layer": g[5], "net": int(g[6])}
          for g in re.findall(r'\(segment\n\t\t\(start ([\d.-]+) ([\d.-]+)\)\n\t\t\(end ([\d.-]+) ([\d.-]+)\)\n'
                              r'\t\t\(width ([\d.]+)\)\n\t\t\(layer "([^"]+)"\)\n\t\t\(net (\d+)\)', SRC)]
vias = [{"x": float(g[0]), "y": float(g[1]), "d": float(g[2]), "net": int(g[3])}
        for g in re.findall(r'\(via\n\t\t\(at ([\d.-]+) ([\d.-]+)\)\n\t\t\(size ([\d.]+)\)'
                            r'[\s\S]{0,90}?\(net (\d+)\)', SRC)]
netname = {int(a): b for a, b in re.findall(r'^\t\(net (\d+) "([^"]*)"', SRC, re.M)}

zones = []
for zm in re.finditer(r'\(zone\n[\s\S]*?\n\t\)', SRC):
    blk = zm.group(0)
    nn = re.search(r'\(net_name "([^"]*)"', blk)
    ly = re.search(r'\(layers? "([^"]+)"\)', blk)
    cl = re.search(r'\(connect_pads\n\t\t\t\(clearance ([\d.]+)\)', blk)
    pts = [(float(a), float(b)) for a, b in re.findall(r'\(xy ([\d.-]+) ([\d.-]+)\)', blk)]
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

# An unrouted board splits every net by definition. Reporting that as a dozen faults
# buries the findings that matter, so say it once and move on.
UNROUTED = not tracks and not vias
if UNROUTED:
    print("NOTE: board carries no tracks or vias - net connectivity not applicable.\n"
          "      Placement, artwork and silkscreen are still checked below.\n")
for net in sorted({p["net"] for p in pads if p["net"]} | {netname[v["net"]] for v in vias}):
    if not net or UNROUTED or net in POURED: continue   # poured nets: section D
    items = []
    for i, p in enumerate(pads):
        if p["net"] == net: items.append(("pad", i))
    for i, t in enumerate(tracks):
        if netname.get(t["net"]) == net: items.append(("trk", i))
    for i, v in enumerate(vias):
        if netname.get(v["net"]) == net: items.append(("via", i))
    par = {k: k for k in items}
    def find(x):
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    def uni(a, b): par[find(a)] = find(b)
    for A in items:
        for B in items:
            if A >= B: continue
            hit = False
            if A[0] == "trk" and B[0] == "trk":
                s, t = tracks[A[1]], tracks[B[1]]
                if s["layer"] == t["layer"]:
                    hit = min(pt_seg(s["a"], t["a"], t["b"]), pt_seg(s["b"], t["a"], t["b"]),
                              pt_seg(t["a"], s["a"], s["b"]), pt_seg(t["b"], s["a"], s["b"])) < 0.01
            elif A[0] == "trk" and B[0] == "pad":
                s, p = tracks[A[1]], pads[B[1]]
                hit = s["layer"] in p["layers"] and (on_pad(p, *s["a"]) or on_pad(p, *s["b"]))
            elif A[0] == "pad" and B[0] == "trk":
                s, p = tracks[B[1]], pads[A[1]]
                hit = s["layer"] in p["layers"] and (on_pad(p, *s["a"]) or on_pad(p, *s["b"]))
            elif "via" in (A[0], B[0]):
                v = vias[A[1] if A[0]=="via" else B[1]]
                o = B if A[0]=="via" else A
                if o[0] == "trk":
                    s = tracks[o[1]]; hit = pt_seg((v["x"],v["y"]), s["a"], s["b"]) < 0.01
                elif o[0] == "pad":
                    hit = on_pad(pads[o[1]], v["x"], v["y"])
                else: hit = True
            if hit: uni(A, B)
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
        clear_rect(p["x"], p["y"], p["w"], p["h"], z["clr"])
    for t in tracks:
        if t["layer"] != z["layer"] or netname.get(t["net"]) == z["net"]: continue
        (ax, ay), (bx, by) = t["a"], t["b"]
        dx, dy = bx-ax, by-ay; L = dx*dx + dy*dy
        u = 0.0 if L == 0 else np.clip(((PX-ax)*dx + (PY-ay)*dy) / L, 0, 1)
        ok[np.hypot(PX - (ax + u*dx), PY - (ay + u*dy)) <= t["w"]/2 + z["clr"]] = False
    for v in vias:
        if netname.get(v["net"]) == z["net"]: continue
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
    reach = {}
    for p in mine:                                   # a pad joins the pour by its spokes
        r = max(p["w"], p["h"])/2 + z["clr"] + 4*G
        sel = (np.abs(PX-p["x"]) <= r) & (np.abs(PY-p["y"]) <= r) & (lab >= 0)
        reach[p["id"]] = set(np.unique(lab[sel]).tolist())
    if any(not v for v in reach.values()):
        for k, v in reach.items():
            if not v:
                bad("POUR UNREACHED", f'{z["net"]} pour on {z["layer"]} does not reach {k}')
    else:
        common = set.intersection(*reach.values()) if reach else set()
        if not common and reach:
            groups = {}
            for k, v in reach.items(): groups.setdefault(tuple(sorted(v)), []).append(k)
            bad("POUR SPLIT", f'{z["net"]} pour on {z["layer"]} is islanded: ' +
                "  ||  ".join(", ".join(sorted(g)) for g in groups.values()))
    print(f'pour "{z["net"]}" on {z["layer"]}: {nlab} island(s), '
          f'{100.0*ok.sum()/ok.size:.0f}% of the outline is copper, '
          f'{len(mine)} pad(s) of the net')

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
