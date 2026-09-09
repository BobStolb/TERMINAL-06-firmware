#!/usr/bin/env python3
"""Independent audit of the board, checking what the other tools do NOT.

checkcopper.py verifies that each pad is TOUCHED by a track of its net. That is a
weaker claim than it sounds: a net split into two islands passes it, because every
pad is touched by something. This checks the real thing - that all pads of a net form
ONE connected component through tracks and vias.

It also checks the things a copper checker never looks at: silkscreen over pads,
silkscreen over silkscreen, and whether every mask opening is actually smaller than
the copper it exposes.
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
           "layer": g[5], "net": int(g[6])}
          for g in re.findall(r'\(segment\n\t\t\(start ([\d.-]+) ([\d.-]+)\)\n\t\t\(end ([\d.-]+) ([\d.-]+)\)\n'
                              r'\t\t\(width ([\d.]+)\)\n\t\t\(layer "([^"]+)"\)\n\t\t\(net (\d+)\)', SRC)]
vias = [{"x": float(g[0]), "y": float(g[1]), "net": int(g[3])}
        for g in re.findall(r'\(via\n\t\t\(at ([\d.-]+) ([\d.-]+)\)\n\t\t\(size ([\d.]+)\)'
                            r'[\s\S]{0,90}?\(net (\d+)\)', SRC)]
netname = {int(a): b for a, b in re.findall(r'^\t\(net (\d+) "([^"]*)"', SRC, re.M)}

# ------------------------------------------------------------------ A. real net connectivity
def on_pad(p, x, y, tol=0.01):
    return (abs(x-p["x"]) <= p["w"]/2+tol) and (abs(y-p["y"]) <= p["h"]/2+tol)
def pt_seg(p, a, b):
    dx, dy = b[0]-a[0], b[1]-a[1]; L = dx*dx+dy*dy
    t = 0 if L == 0 else max(0, min(1, ((p[0]-a[0])*dx + (p[1]-a[1])*dy)/L))
    return math.hypot(p[0]-(a[0]+t*dx), p[1]-(a[1]+t*dy))

for net in sorted({p["net"] for p in pads if p["net"]} | {netname[v["net"]] for v in vias}):
    if not net: continue
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
