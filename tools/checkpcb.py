#!/usr/bin/env python3
"""Offline placement check: courtyard overlaps, board-edge escapes, keepout intrusions,
and F.Cu copper crossing any pad that reaches F.Cu.

The last one is the check that caught the real bug in this board: the decorative gold
on the face is genuine copper, so a through-hole pad under it is a short, not a graphic.

Usage:  python3 tools/checkpcb.py PCB/TS06-FASCIA/TS06-FASCIA.kicad_pcb
"""
import re, sys, math

src = open(sys.argv[1], encoding="utf8").read()
W, H = 176.0, 52.0
bad = []

fps = re.findall(r'\(footprint "[^"]+"[\s\S]*?\n\)', src)
parts = []
for f in fps:
    ref = (re.search(r'\(property "Reference" "([^"]+)"', f) or [None, "?"])[1]
    at = re.search(r'\n\t\(at ([\d.-]+) ([\d.-]+)\)', f)
    if not at: continue
    ox, oy = float(at.group(1)), float(at.group(2))
    pads = []
    for pm in re.finditer(r'\(pad "([^"]*)" (\w+) \w+\n\t\t\(at ([\d.-]+) ([\d.-]+)\)\n'
                          r'\t\t\(size ([\d.]+) ([\d.]+)\)[\s\S]*?\(layers ([^)]*)\)', f):
        pads.append({"n": pm.group(1), "kind": pm.group(2),
                     "x": ox + float(pm.group(3)), "y": oy + float(pm.group(4)),
                     "w": float(pm.group(5)), "h": float(pm.group(6)),
                     "layers": pm.group(7)})
    cy = [tuple(map(float, m.groups())) for m in
          re.finditer(r'\(fp_line\n\t\t\(start ([\d.-]+) ([\d.-]+)\)\n\t\t\(end ([\d.-]+) ([\d.-]+)\)'
                      r'[\s\S]*?\(layer "[FB]\.CrtYd"\)', f)]
    for cm in re.finditer(r'\(fp_circle\n\t\t\(center ([\d.-]+) ([\d.-]+)\)\n'
                          r'\t\t\(end ([\d.-]+) ([\d.-]+)\)[\s\S]*?\(layer "[FB]\.CrtYd"\)', f):
        ccx, ccy, cex, cey = map(float, cm.groups())
        r = math.hypot(cex - ccx, cey - ccy)
        cy.append((ccx - r, ccy - r, ccx + r, ccy + r))
    box = None
    if cy:
        xs = [p for s in cy for p in (s[0], s[2])]; ys = [p for s in cy for p in (s[1], s[3])]
        box = (ox + min(xs), oy + min(ys), ox + max(xs), oy + max(ys))
    parts.append({"ref": ref, "x": ox, "y": oy, "pads": pads, "box": box})

# 1. pads and courtyards inside the board
for p in parts:
    for d in p["pads"]:
        if not (0 < d["x"] - d["w"]/2 and d["x"] + d["w"]/2 < W
                and 0 < d["y"] - d["h"]/2 and d["y"] + d["h"]/2 < H):
            bad.append(f'OFF-BOARD  {p["ref"]} pad {d["n"]} at ({d["x"]:.2f},{d["y"]:.2f})')
    if p["box"]:
        x1, y1, x2, y2 = p["box"]
        if x1 < 0 or y1 < 0 or x2 > W or y2 > H:
            bad.append(f'COURTYARD OFF-BOARD  {p["ref"]}  {p["box"]}')

# 2. courtyard overlaps between parts on the same side
for i in range(len(parts)):
    for j in range(i + 1, len(parts)):
        a, b = parts[i]["box"], parts[j]["box"]
        if not a or not b: continue
        if a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]:
            bad.append(f'COURTYARD OVERLAP  {parts[i]["ref"]} / {parts[j]["ref"]}')

# 3. F.Cu graphics crossing any pad that reaches F.Cu
# Read each gr_line as a whole block first. A non-greedy [\s\S]*? reaching for the
# layer token will happily run past the end of its own block into the next one, which
# made every F.Mask opening over the ladder read as a piece of front copper.
segs = []
for m in re.finditer(r'\(gr_line\n[\s\S]*?\n\t\)', src):
    blk = m.group(0)
    if '(layer "F.Cu")' not in blk: continue
    v = re.search(r'\(start ([\d.-]+) ([\d.-]+)\)\n\t\t\(end ([\d.-]+) ([\d.-]+)\)'
                  r'\n\t\t\(stroke\n\t\t\t\(width ([\d.]+)\)', blk)
    if v: segs.append(list(map(float, v.groups())))
# Arcs and lettering on F.Cu are copper as well. The box corners of the SUB rule are
# arcs and the plus and minus glyphs are text, so a check that reads only gr_line sees
# about half of the front copper. Arcs are sampled; text gets a generous box.
for m in re.finditer(r'\(gr_arc\n[\s\S]*?\n\t\)', src):
    blk = m.group(0)
    if '(layer "F.Cu")' not in blk: continue
    v = re.search(r'\(start ([\d.-]+) ([\d.-]+)\)\n\t\t\(mid ([\d.-]+) ([\d.-]+)\)\n'
                  r'\t\t\(end ([\d.-]+) ([\d.-]+)\)\n\t\t\(stroke\n\t\t\t\(width ([\d.]+)\)', blk)
    if not v: continue
    ax, ay, mx, my, bx, by, aw = map(float, v.groups())
    pts = [(ax, ay), (mx, my), (bx, by)]
    for k in range(len(pts) - 1):
        segs.append([pts[k][0], pts[k][1], pts[k+1][0], pts[k+1][1], aw])

txts = []
for m in re.finditer(r'\(gr_text "([^"]*)"\n\t\t\(at ([\d.-]+) ([\d.-]+) [\d.-]+\)\n'
                     r'\t\t\(layer "F\.Cu"\)[\s\S]*?\(size ([\d.]+)', src):
    t, tx, ty, sz = m.group(1), float(m.group(2)), float(m.group(3)), float(m.group(4))
    txts.append((tx, ty, max(len(t), 1) * sz * 0.95 + sz * 0.4, sz * 1.5))

fcu_pads = [d for p in parts for d in p["pads"]
            if "*.Cu" in d["layers"] or "F.Cu" in d["layers"] or "F&B" in d["layers"]]
def seg_pt_dist(x1, y1, x2, y2, px_, py_):
    dx, dy = x2 - x1, y2 - y1
    L = dx*dx + dy*dy
    t = 0 if L == 0 else max(0, min(1, ((px_-x1)*dx + (py_-y1)*dy) / L))
    return math.hypot(px_ - (x1+t*dx), py_ - (y1+t*dy))
for x1, y1, x2, y2, w in segs:
    for d in fcu_pads:
        clear = seg_pt_dist(x1, y1, x2, y2, d["x"], d["y"]) - w/2 - max(d["w"], d["h"])/2
        if clear < 0.2:
            bad.append(f'F.Cu ART TOUCHES PAD  {d["n"]} at ({d["x"]:.2f},{d["y"]:.2f}) '
                       f'clearance {clear:+.2f} mm')

for tx, ty, tw, th in txts:
    for d in fcu_pads:
        dx = max(abs(d["x"] - tx) - tw/2, 0.0) - d["w"]/2
        dy = max(abs(d["y"] - ty) - th/2, 0.0) - d["h"]/2
        clear = math.hypot(max(dx, 0.0), max(dy, 0.0)) if (dx > 0 or dy > 0) else -1.0
        if clear < 0.2:
            bad.append(f'F.Cu LETTERING TOUCHES PAD  {d["n"]} at ({d["x"]:.2f},{d["y"]:.2f}) '
                       f'clearance {clear:+.2f} mm')

# 4. keepout intrusions - nothing on the back inside the rotary body circle
for p in parts:
    for d in p["pads"]:
        if p["ref"] == "SW1" or d["n"] == "":
            continue          # the rotary owns that keepout; its own bushing hole is fine
        if "B.Cu" in d["layers"] or "*.Cu" in d["layers"]:
            if math.hypot(d["x"] - 30.0, d["y"] - 26.0) < 12.5 + 0.5:
                bad.append(f'IN ROTARY BODY KEEPOUT  {p["ref"]} pad {d["n"]}')

print(f'{len(parts)} footprints, {sum(len(p["pads"]) for p in parts)} pads, {len(segs)} F.Cu graphics')
for b in sorted(set(bad)): print("  " + b)
print(("\n%d issue(s)" % len(set(bad))) if bad else "\nclean")
sys.exit(1 if bad else 0)
