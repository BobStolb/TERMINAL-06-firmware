#!/usr/bin/env python3
"""Copper clearance and connectivity check for a KiCad board, offline.

Checks, per layer:
  * track to pad, track to track, track to via, via to pad  - different nets only
  * track/via against NETLESS F.Cu graphics (this board's decorative gold is real
    copper, so a routed trace touching it is a short, not an overlap)
  * every pad has at least one track or via of its own net landing on it

Usage:  python3 tools/checkcopper.py PCB/TS06-FASCIA/TS06-FASCIA.kicad_pcb [clearance_mm]
            [--hv HV185,CAT_*] [--hv-clr 0.6]      # a wider gap around high-voltage nets
"""
import re, sys, math

def extract_footprints(src):
    """Every top-level (footprint ...) block, paren-depth counted so it works
    regardless of indentation convention - this repo's own generators outdent
    footprints to column 0, real KiCad indents them normally as a child of
    kicad_pcb (one tab deeper, and everything inside one tab deeper again).
    Each block is re-indented back to the column-0 convention the field
    regexes below are written against, so nothing past this point needs to
    know or care which convention the file was actually saved in.
    """
    out = []
    key = '(footprint "'
    i = 0
    while True:
        i = src.find(key, i)
        if i < 0:
            break
        line_start = src.rfind('\n', 0, i) + 1
        base_indent = i - line_start
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
        block = src[i:j]
        if base_indent > 0:
            cut = '\t' * base_indent
            lines = block.split('\n')
            block = '\n'.join([lines[0]] + [ln[base_indent:] if ln.startswith(cut) else ln
                                             for ln in lines[1:]])
        out.append(block)
        i = j
    return out

ARGS = sys.argv[1:]
HV, HVCLR = [], 0.6
if "--hv" in ARGS:                 # net names; a trailing * matches a prefix
    k = ARGS.index("--hv"); HV = [p for p in ARGS[k+1].split(",") if p]; del ARGS[k:k+2]
if "--hv-clr" in ARGS:
    k = ARGS.index("--hv-clr"); HVCLR = float(ARGS[k+1]); del ARGS[k:k+2]
SRC = open(ARGS[0], encoding="utf8").read()
CLR = float(ARGS[1]) if len(ARGS) > 1 else 0.2

# Any copper pair that involves a high-voltage net keeps the larger gap. IPC-2221B Table 6-1,
# 151-250 V: 0.4 mm between conductors under solder mask (B4), 0.8 mm between bare
# component terminations (A6) - run with --hv-clr 0.8 and read the PAD/PAD lines to hold
# bare pads to A6. The 0.2 mm default is for the low-voltage logic every other net carries.
def is_hv(n):
    return bool(n) and any(n == p or (p.endswith("*") and n.startswith(p[:-1])) for p in HV)
def need(a, b):
    return HVCLR if (is_hv(a) or is_hv(b)) else CLR

# An unplated hole is not copper: nothing on it carries a voltage, so no net clearance
# applies to it. What does apply is the drill-to-copper distance KiCad checks as
# hole_clearance, 0.25 mm by default.
HOLECLR = 0.25

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

def seg_pad(a, b, p):
    """Distance from a segment to a pad's real outline: a round pad is a circle and an oval
    pad a stadium; rect and roundrect stay rectangles, the conservative reading. Measuring
    every pad as its bounding square put a track that sat 0.6 mm from a round tube pad at
    0.26 mm from the square's corner."""
    if p["shape"] == "circle" or (p["shape"] == "oval" and abs(p["w"] - p["h"]) < 1e-9):
        return seg_seg(a, b, (p["x"], p["y"]), (p["x"], p["y"])) - p["w"]/2
    if p["shape"] == "oval":
        r = min(p["w"], p["h"]) / 2
        if p["w"] > p["h"]:
            c1, c2 = (p["x"] - p["w"]/2 + r, p["y"]), (p["x"] + p["w"]/2 - r, p["y"])
        else:
            c1, c2 = (p["x"], p["y"] - p["h"]/2 + r), (p["x"], p["y"] + p["h"]/2 - r)
        return seg_seg(a, b, c1, c2) - r
    return seg_rect(a, b, p["x"], p["y"], p["w"], p["h"])

# ---- collect pads
pads = []
for f in extract_footprints(SRC):
    ref = (re.search(r'\(property "Reference" "([^"]+)"', f) or [None, "?"])[1]
    at = re.search(r'\n\t\(at ([\d.-]+) ([\d.-]+)\)', f)
    if not at: continue
    ox, oy = float(at.group(1)), float(at.group(2))
    for m in re.finditer(r'\(pad "([^"]*)" (\w+) \w+\n\t\t\(at ([\d.-]+) ([\d.-]+)\)\n'
                         r'\t\t\(size ([\d.]+) ([\d.]+)\)([\s\S]{0,300}?)\n\t\)', f):
        body = m.group(7)
        net = (re.search(r'\(net (?:\d+ )?"([^"]*)"', body) or [None, None])[1]
        lay = (re.search(r'\(layers ([^)]*)\)', body) or [None, ""])[1]
        for L in (["F.Cu","B.Cu"] if ("*.Cu" in lay or "F&B" in lay)
                  else [x for x in ("F.Cu","B.Cu") if x in lay]):
            pads.append({"ref": f"{ref}.{m.group(1)}", "x": ox+float(m.group(3)),
                         "y": oy+float(m.group(4)), "w": float(m.group(5)),
                         "h": float(m.group(6)), "net": net, "layer": L,
                         "thru": m.group(2) == "thru_hole", "fp": ref, "kind": m.group(2),
                         "shape": re.match(r'\(pad "[^"]*" \w+ (\w+)', m.group(0)).group(1)})

# A segment/via's (net ...) field is either just a code - (net 3) - resolved
# through the net table below, or, on every save this KiCad setup has
# actually produced, the bare name with no code at all - (net "A6"). Track
# whichever form is present per-object rather than assuming one; "net" ends
# up holding a net NAME string either way so the rest of this file never has
# to care which form the file was in.
netname = {int(m.group(1)): m.group(2) for m in re.finditer(r'^\t\(net (\d+) "([^"]*)"', SRC, re.M)}
def _net_of(code, name):
    return name if name is not None else netname.get(int(code) if code is not None else -1)

tracks = [{"a": (float(m.group(1)), float(m.group(2))), "b": (float(m.group(3)), float(m.group(4))),
           "w": float(m.group(5)), "layer": m.group(6), "net": _net_of(m.group(7), m.group(8))}
          for m in re.finditer(r'\(segment\n\t\t\(start ([\d.-]+) ([\d.-]+)\)\n\t\t\(end ([\d.-]+) ([\d.-]+)\)\n'
                               # (net ...) covers all three shapes seen in the wild: a bare
                               # code (net 3), a bare name (net "A6"), or - this repo's own
                               # generator convention, not anticipated here until a
                               # generator actually emitted tracks - both together,
                               # (net 1 "HV185"). Same tolerant shape the pad regex above
                               # already uses; segments/vias just hadn't needed it yet.
                               r'\t\t\(width ([\d.]+)\)\n\t\t\(layer "([^"]+)"\)\n'
                               r'\t\t\(net (\d+)?\s*(?:"([^"]*)")?\)', SRC)]
vias = [{"x": float(m.group(1)), "y": float(m.group(2)), "d": float(m.group(3)), "net": _net_of(m.group(4), m.group(5))}
        for m in re.finditer(r'\(via\n\t\t\(at ([\d.-]+) ([\d.-]+)\)\n\t\t\(size ([\d.]+)\)'
                             r'[\s\S]{0,80}?\(net (\d+)?\s*(?:"([^"]*)")?\)', SRC)]
# Each gr_line is read as a whole block: a non-greedy reach for the layer token runs
# past the end of its own block and mislabels the next one.
gold = []
for m in re.finditer(r'\(gr_line\n[\s\S]*?\n\t\)', SRC):
    blk = m.group(0)
    if '(layer "F.Cu")' not in blk: continue
    v = re.search(r'\(start ([\d.-]+) ([\d.-]+)\)\n\t\t\(end ([\d.-]+) ([\d.-]+)\)\n'
                  r'\t\t\(stroke\n\t\t\t\(width ([\d.]+)\)', blk)
    if v:
        gold.append(((float(v.group(1)), float(v.group(2))),
                     (float(v.group(3)), float(v.group(4))), float(v.group(5))))

# A net that is poured is supplied by the zone, not by tracks. The pour is only claimed
# to REACH every pad after tools/audit.py flood-fills it; this file just stops asking.
# Three zone net-field shapes exist in the wild: net and net_name as separate fields
# (this repo's own generators write it that way), net N "NAME" combined with no
# separate net_name field, or - what real KiCad has actually saved every time in this
# project - the bare name with no code at all, net "NAME". Match any of the three.
poured = {m.group(1) for m in re.finditer(r'\(zone\n\t\t\(net (?:\d+ )?"([^"]*)"\)', SRC)}
poured |= {m.group(1) for m in re.finditer(
    r'\(zone\n\t\t\(net \d+\)\n\t\t\(net_name "([^"]*)"\)', SRC)}
poured.discard("")

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
        if p["layer"] != t["layer"] or p["net"] == t["net"]: continue
        g = seg_pad(t["a"], t["b"], p) - t["w"]/2
        if g < (HOLECLR if p["kind"] == "np_thru_hole" else need(t["net"], p["net"])):
            flag(f'TRACK/PAD  {t["net"]}@{t["layer"]} vs {p["ref"]}'
                 f'({p["net"]}) at ({p["x"]:.1f},{p["y"]:.1f})  gap {g:+.2f}')
# ---- track vs track
for i in range(len(tracks)):
    for j in range(i+1, len(tracks)):
        s, t = tracks[i], tracks[j]
        if s["layer"] != t["layer"] or s["net"] == t["net"]: continue
        g = seg_seg(s["a"], s["b"], t["a"], t["b"]) - s["w"]/2 - t["w"]/2
        if g < need(s["net"], t["net"]):
            flag(f'TRACK/TRACK  {s["net"]} vs {t["net"]}'
                 f' @{s["layer"]}  gap {g:+.2f}  near ({s["a"][0]:.1f},{s["a"][1]:.1f})')
# ---- vias
for v in vias:
    for p in pads:
        if p["net"] == v["net"]: continue
        g = seg_pad((v["x"],v["y"]), (v["x"],v["y"]), p) - v["d"]/2
        if g < (HOLECLR if p["kind"] == "np_thru_hole" else need(v["net"], p["net"])):
            flag(f'VIA/PAD  {v["net"]} at ({v["x"]:.1f},{v["y"]:.1f}) vs {p["ref"]}  gap {g:+.2f}')
    for t in tracks:
        if t["net"] == v["net"]: continue
        g = seg_seg(t["a"], t["b"], (v["x"],v["y"]), (v["x"],v["y"])) - t["w"]/2 - v["d"]/2
        if g < need(t["net"], v["net"]):
            flag(f'VIA/TRACK  {v["net"]} at ({v["x"]:.1f},{v["y"]:.1f})'
                 f' vs {t["net"]}@{t["layer"]}  gap {g:+.2f}')
# ---- pad vs pad between different parts: that is placement, not routing. Pads inside one
# footprint keep whatever spacing the manufacturer's land pattern gives them.
for i in range(len(pads)):
    for j in range(i+1, len(pads)):
        p, q = pads[i], pads[j]
        if p["layer"] != q["layer"] or p["fp"] == q["fp"]: continue
        if "np_thru_hole" in (p["kind"], q["kind"]): continue
        if p["net"] and p["net"] == q["net"]: continue
        if p["shape"] == "circle" and q["shape"] == "circle":
            g = math.hypot(p["x"] - q["x"], p["y"] - q["y"]) - p["w"]/2 - q["w"]/2
        else:
            g = math.hypot(max(abs(p["x"] - q["x"]) - (p["w"] + q["w"])/2, 0.0),
                           max(abs(p["y"] - q["y"]) - (p["h"] + q["h"])/2, 0.0))
        if g < need(p["net"], q["net"]):
            flag(f'PAD/PAD  {p["ref"]}({p["net"]}) vs {q["ref"]}({q["net"]}) @{p["layer"]}  gap {g:+.2f}')
# ---- anything routed on F.Cu vs the netless decorative copper
for (ga, gb, gw) in gold:
    for t in tracks:
        if t["layer"] != "F.Cu": continue
        g = seg_seg(t["a"], t["b"], ga, gb) - t["w"]/2 - gw/2
        if g < CLR:
            flag(f'TRACK/GOLD  {t["net"]} vs decorative copper  gap {g:+.2f}'
                 f'  near ({ga[0]:.1f},{ga[1]:.1f})')
    for v in vias:
        g = seg_seg(ga, gb, (v["x"],v["y"]), (v["x"],v["y"])) - gw/2 - v["d"]/2
        if g < CLR:
            flag(f'VIA/GOLD  {v["net"]} at ({v["x"]:.1f},{v["y"]:.1f})  gap {g:+.2f}')

for (tx, ty, tw, th) in goldtext:
    for t in tracks:
        if t["layer"] != "F.Cu": continue
        g = seg_rect(t["a"], t["b"], tx, ty, tw, th) - t["w"]/2
        if g < CLR:
            flag(f'TRACK/GOLDTEXT  {t["net"]} vs text at ({tx:.1f},{ty:.1f})  gap {g:+.2f}')
    for v in vias:
        g = seg_rect((v["x"],v["y"]), (v["x"],v["y"]), tx, ty, tw, th) - v["d"]/2
        if g < CLR:
            flag(f'VIA/GOLDTEXT  {v["net"]} at ({v["x"]:.1f},{v["y"]:.1f})  gap {g:+.2f}')

# ---- connectivity: every netted pad touched by its own net
# A board with no tracks at all is not "37 faults", it is one fact. Say it once.
if not tracks and not vias:
    print(f'{len(pads)} pad-layers - board carries no tracks or vias, '
          f'so connectivity is not applicable. Clearance results above stand.')
    for b in dict.fromkeys(bad): print("  " + b)
    sys.exit(1 if bad else 0)
# A plated through-hole is one node on both faces: a track landing on either side of it
# connects it. Only a surface pad has to be met on its own layer.
seen_pad = set()
for p in pads:
    if not p["net"] or p["net"] in poured: continue
    key = (p["ref"], "" if p["thru"] else p["layer"])
    if key in seen_pad: continue
    seen_pad.add(key)
    hit = any((p["thru"] or t["layer"] == p["layer"]) and t["net"] == p["net"]
              and seg_rect(t["a"], t["b"], p["x"], p["y"], p["w"], p["h"]) <= 0.01
              for t in tracks)
    if not hit:
        where = "any layer" if p["thru"] else p["layer"]
        flag(f'UNROUTED  {p["ref"]} net {p["net"]} at ({p["x"]:.1f},{p["y"]:.1f}) on {where}')

print(f'{len(tracks)} tracks, {len(vias)} vias, {len(pads)} pad-layers, clearance target {CLR} mm')
seen = set()
for b in bad:
    if b not in seen: seen.add(b); print("  " + b)
print(("\n%d issue(s)" % len(seen)) if seen else "\nclean")
sys.exit(1 if seen else 0)
