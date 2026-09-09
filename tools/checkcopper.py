#!/usr/bin/env python3
"""Copper clearance and connectivity check for a KiCad board, offline.

Checks, per layer:
  * track to pad, track to track, track to via, via to pad  - different nets only
  * track/via against NETLESS F.Cu graphics (this board's decorative gold is real
    copper, so a routed trace touching it is a short, not an overlap)
  * every pad has at least one track or via of its own net landing on it

Usage:  python3 tools/checkcopper.py PCB/TS06-FASCIA/TS06-FASCIA.kicad_pcb [clearance_mm]
"""
import re, sys, math

SRC = open(sys.argv[1], encoding="utf8").read()
CLR = float(sys.argv[2]) if len(sys.argv) > 2 else 0.2

def seg_seg(a, b, c, d):
    def sp(p, q, r):
        dx, dy = q[0]-p[0], q[1]-p[1]
        L = dx*dx + dy*dy
        t = 0 if L == 0 else max(0, min(1, ((r[0]-p[0])*dx + (r[1]-p[1])*dy)/L))
        return math.hypot(r[0]-(p[0]+t*dx), r[1]-(p[1]+t*dy))
    d1 = (b[0]-a[0], b[1]-a[1]); d2 = (d[0]-c[0], d[1]-c[1])
    den = d1[0]*d2[1] - d1[1]*d2[0]
    if abs(den) > 1e-12:
        t = ((c[0]-a[0])*d2[1] - (c[1]-a[1])*d2[0]) / den
        u = ((c[0]-a[0])*d1[1] - (c[1]-a[1])*d1[0]) / den
        if 0 <= t <= 1 and 0 <= u <= 1: return 0.0
    return min(sp(a,b,c), sp(a,b,d), sp(c,d,a), sp(c,d,b))

def seg_rect(a, b, cx, cy, w, h):
    """Distance from a segment to an axis-aligned rectangle."""
    hw, hh = w/2, h/2
    corners = [(cx-hw,cy-hh),(cx+hw,cy-hh),(cx+hw,cy+hh),(cx-hw,cy+hh)]
    edges = list(zip(corners, corners[1:]+corners[:1]))
    for p in (a, b):
        if cx-hw <= p[0] <= cx+hw and cy-hh <= p[1] <= cy+hh: return 0.0
    return min(seg_seg(a, b, e[0], e[1]) for e in edges)

# ---- collect pads
pads = []
for f in re.findall(r'\(footprint "[^"]+"[\s\S]*?\n\)', SRC):
    ref = (re.search(r'\(property "Reference" "([^"]+)"', f) or [None, "?"])[1]
    at = re.search(r'\n\t\(at ([\d.-]+) ([\d.-]+)\)', f)
    if not at: continue
    ox, oy = float(at.group(1)), float(at.group(2))
    for m in re.finditer(r'\(pad "([^"]*)" (\w+) \w+\n\t\t\(at ([\d.-]+) ([\d.-]+)\)\n'
                         r'\t\t\(size ([\d.]+) ([\d.]+)\)([\s\S]{0,300}?)\n\t\)', f):
        body = m.group(7)
        net = (re.search(r'\(net \d+ "([^"]*)"', body) or [None, None])[1]
        lay = (re.search(r'\(layers ([^)]*)\)', body) or [None, ""])[1]
        for L in (["F.Cu","B.Cu"] if ("*.Cu" in lay or "F&B" in lay)
                  else [x for x in ("F.Cu","B.Cu") if x in lay]):
            pads.append({"ref": f"{ref}.{m.group(1)}", "x": ox+float(m.group(3)),
                         "y": oy+float(m.group(4)), "w": float(m.group(5)),
                         "h": float(m.group(6)), "net": net, "layer": L})

tracks = [{"a": (float(m.group(1)), float(m.group(2))), "b": (float(m.group(3)), float(m.group(4))),
           "w": float(m.group(5)), "layer": m.group(6), "net": int(m.group(7))}
          for m in re.finditer(r'\(segment\n\t\t\(start ([\d.-]+) ([\d.-]+)\)\n\t\t\(end ([\d.-]+) ([\d.-]+)\)\n'
                               r'\t\t\(width ([\d.]+)\)\n\t\t\(layer "([^"]+)"\)\n\t\t\(net (\d+)\)', SRC)]
vias = [{"x": float(m.group(1)), "y": float(m.group(2)), "d": float(m.group(3)), "net": int(m.group(4))}
        for m in re.finditer(r'\(via\n\t\t\(at ([\d.-]+) ([\d.-]+)\)\n\t\t\(size ([\d.]+)\)'
                             r'[\s\S]{0,80}?\(net (\d+)\)', SRC)]
netname = {int(m.group(1)): m.group(2) for m in re.finditer(r'^\t\(net (\d+) "([^"]*)"', SRC, re.M)}
gold = [((float(m.group(1)), float(m.group(2))), (float(m.group(3)), float(m.group(4))), float(m.group(5)))
        for m in re.finditer(r'\(gr_line\n\t\t\(start ([\d.-]+) ([\d.-]+)\)\n\t\t\(end ([\d.-]+) ([\d.-]+)\)\n'
                             r'\t\t\(stroke\n\t\t\t\(width ([\d.]+)\)[\s\S]*?\(layer "F\.Cu"\)', SRC)]

# Text on F.Cu is copper too - the dial numerals and the plus/minus glyphs are drawn
# that way on purpose. A checker that only looks at gr_line would happily route a
# trace straight through a numeral. Bounding boxes are deliberately generous.
goldtext = []
for m in re.finditer(r'\(gr_text "([^"]*)"\n\t\t\(at ([\d.-]+) ([\d.-]+) [\d.-]+\)\n'
                     r'\t\t\(layer "F\.Cu"\)[\s\S]*?\(size ([\d.]+)', SRC):
    txt, tx, ty, sz = m.group(1), float(m.group(2)), float(m.group(3)), float(m.group(4))
    goldtext.append((tx, ty, max(len(txt), 1) * sz * 0.95 + sz * 0.4, sz * 1.5))

bad = []
def flag(s): bad.append(s)

# ---- track vs pad
for t in tracks:
    for p in pads:
        if p["layer"] != t["layer"] or p["net"] == netname.get(t["net"]): continue
        g = seg_rect(t["a"], t["b"], p["x"], p["y"], p["w"], p["h"]) - t["w"]/2
        if g < CLR:
            flag(f'TRACK/PAD  {netname.get(t["net"])}@{t["layer"]} vs {p["ref"]}'
                 f'({p["net"]}) at ({p["x"]:.1f},{p["y"]:.1f})  gap {g:+.2f}')
# ---- track vs track
for i in range(len(tracks)):
    for j in range(i+1, len(tracks)):
        s, t = tracks[i], tracks[j]
        if s["layer"] != t["layer"] or s["net"] == t["net"]: continue
        g = seg_seg(s["a"], s["b"], t["a"], t["b"]) - s["w"]/2 - t["w"]/2
        if g < CLR:
            flag(f'TRACK/TRACK  {netname.get(s["net"])} vs {netname.get(t["net"])}'
                 f' @{s["layer"]}  gap {g:+.2f}  near ({s["a"][0]:.1f},{s["a"][1]:.1f})')
# ---- vias
for v in vias:
    for p in pads:
        if p["net"] == netname.get(v["net"]): continue
        g = seg_rect((v["x"],v["y"]), (v["x"],v["y"]), p["x"], p["y"], p["w"], p["h"]) - v["d"]/2
        if g < CLR:
            flag(f'VIA/PAD  {netname.get(v["net"])} at ({v["x"]:.1f},{v["y"]:.1f}) vs {p["ref"]}  gap {g:+.2f}')
    for t in tracks:
        if t["net"] == v["net"]: continue
        g = seg_seg(t["a"], t["b"], (v["x"],v["y"]), (v["x"],v["y"])) - t["w"]/2 - v["d"]/2
        if g < CLR:
            flag(f'VIA/TRACK  {netname.get(v["net"])} at ({v["x"]:.1f},{v["y"]:.1f})'
                 f' vs {netname.get(t["net"])}@{t["layer"]}  gap {g:+.2f}')
# ---- anything routed on F.Cu vs the netless decorative copper
for (ga, gb, gw) in gold:
    for t in tracks:
        if t["layer"] != "F.Cu": continue
        g = seg_seg(t["a"], t["b"], ga, gb) - t["w"]/2 - gw/2
        if g < CLR:
            flag(f'TRACK/GOLD  {netname.get(t["net"])} vs decorative copper  gap {g:+.2f}'
                 f'  near ({ga[0]:.1f},{ga[1]:.1f})')
    for v in vias:
        g = seg_seg(ga, gb, (v["x"],v["y"]), (v["x"],v["y"])) - gw/2 - v["d"]/2
        if g < CLR:
            flag(f'VIA/GOLD  {netname.get(v["net"])} at ({v["x"]:.1f},{v["y"]:.1f})  gap {g:+.2f}')

for (tx, ty, tw, th) in goldtext:
    for t in tracks:
        if t["layer"] != "F.Cu": continue
        g = seg_rect(t["a"], t["b"], tx, ty, tw, th) - t["w"]/2
        if g < CLR:
            flag(f'TRACK/GOLDTEXT  {netname.get(t["net"])} vs text at ({tx:.1f},{ty:.1f})  gap {g:+.2f}')
    for v in vias:
        g = seg_rect((v["x"],v["y"]), (v["x"],v["y"]), tx, ty, tw, th) - v["d"]/2
        if g < CLR:
            flag(f'VIA/GOLDTEXT  {netname.get(v["net"])} at ({v["x"]:.1f},{v["y"]:.1f})  gap {g:+.2f}')

# ---- connectivity: every netted pad touched by its own net
for p in pads:
    if not p["net"] or p["net"] == "": continue
    hit = any(t["layer"] == p["layer"] and netname.get(t["net"]) == p["net"]
              and seg_rect(t["a"], t["b"], p["x"], p["y"], p["w"], p["h"]) <= 0.01
              for t in tracks)
    if not hit:
        flag(f'UNROUTED  {p["ref"]} net {p["net"]} at ({p["x"]:.1f},{p["y"]:.1f}) on {p["layer"]}')

print(f'{len(tracks)} tracks, {len(vias)} vias, {len(pads)} pad-layers, clearance target {CLR} mm')
seen = set()
for b in bad:
    if b not in seen: seen.add(b); print("  " + b)
print(("\n%d issue(s)" % len(seen)) if seen else "\nclean")
sys.exit(1 if seen else 0)
