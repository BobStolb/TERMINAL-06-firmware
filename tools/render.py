#!/usr/bin/env python3
"""Draw a .kicad_pcb as an SVG, front face and back face, straight from the file.

Not a substitute for KiCad's own view - the stroke font is approximated with an SVG
font and arcs are drawn as circular arcs from three points. It is here so the board can
be LOOKED at without opening KiCad, which is what caught the last round of faults.

The front view shows what the customer sees: black mask, white silkscreen, and bare
gold only where the mask is actually opened. The back view is mirrored, so it is what
you see with the board turned over in your hands, and the pour is drawn as it fills.

Usage:  python3 tools/render.py PCB/TS06-FASCIA-THT/TS06-FASCIA-THT.kicad_pcb out.svg
"""
import re, sys, math

SRC = open(sys.argv[1], encoding="utf8").read()
OUT = sys.argv[2] if len(sys.argv) > 2 else "board.svg"
S = 5.0                                   # px per mm
PAD = 6.0

MASK, SILK, GOLD, CU, ZONE, HOLE = "#0d0f10", "#e8e6e0", "#d8b25e", "#8a6a3a", "#5c4526", "#000"

def extract_blocks(src, tag):
    """Every top-level (tag ...) block, paren-depth counted rather than a
    fixed-shape regex. A non-greedy \\n\\t) boundary works for a bare
    unfilled zone, but a real KiCad fill embeds filled_polygon sub-blocks
    with their own nested closes, so the first \\n\\t) found is usually deep
    inside the fill data - silently truncating the block.
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

def blocks(kind):
    return extract_blocks(SRC, kind)

def fpblocks():
    """(footprint ...) blocks, re-indented to the column-0 convention the
    field regexes elsewhere in this file are written against - this repo's
    own generators outdent footprints to column 0, real KiCad indents them
    normally as a child of kicad_pcb (one tab deeper throughout)."""
    out = []
    for block in extract_blocks(SRC, 'footprint "'):
        i = SRC.find(block)
        line_start = SRC.rfind('\n', 0, i) + 1
        base_indent = i - line_start
        if base_indent > 0:
            cut = '\t' * base_indent
            lines = block.split('\n')
            block = '\n'.join([lines[0]] + [ln[base_indent:] if ln.startswith(cut) else ln
                                             for ln in lines[1:]])
        out.append(block)
    return out

def num(pat, blk, n=1):
    m = re.search(pat, blk)
    return [float(x) for x in m.groups()] if m else None

class Layer:
    def __init__(self): self.d = []
    def add(self, s): self.d.append(s)

def arc_path(ax, ay, mx, my, bx, by):
    d = 2 * (ax*(my-by) + mx*(by-ay) + bx*(ay-my))
    if abs(d) < 1e-9: return f'M{ax},{ay} L{bx},{by}'
    ux = ((ax*ax+ay*ay)*(my-by) + (mx*mx+my*my)*(by-ay) + (bx*bx+by*by)*(ay-my)) / d
    uy = ((ax*ax+ay*ay)*(bx-mx) + (mx*mx+my*my)*(ax-bx) + (bx*bx+by*by)*(mx-ax)) / d
    r = math.hypot(ax-ux, ay-uy)
    cross = (mx-ax)*(by-ay) - (my-ay)*(bx-ax)
    return f'M{ax},{ay} A{r},{r} 0 0,{1 if cross > 0 else 0} {bx},{by}'

def collect(side):
    """side is 'F' or 'B'. Returns dicts of svg fragments per visual role."""
    cu, mask, silk, pads, holes = Layer(), Layer(), Layer(), Layer(), Layer()
    def stroke(L, d, w, col, cap="round"):
        L.add(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{w}" '
              f'stroke-linecap="{cap}"/>')
    # graphics
    for k in ("gr_line", "gr_arc", "gr_circle"):
        for b in blocks(k):
            ly = re.search(r'\(layer "([^"]+)"\)', b)
            wd = re.search(r'\(width ([\d.]+)\)', b)
            if not ly or not wd: continue
            ly, wd = ly.group(1), float(wd.group(1))
            if k == "gr_line":
                v = num(r'\(start ([\d.-]+) ([\d.-]+)\)\n\t\t\(end ([\d.-]+) ([\d.-]+)\)', b)
                d = f'M{v[0]},{v[1]} L{v[2]},{v[3]}'
            elif k == "gr_arc":
                v = num(r'\(start ([\d.-]+) ([\d.-]+)\)\n\t\t\(mid ([\d.-]+) ([\d.-]+)\)\n'
                        r'\t\t\(end ([\d.-]+) ([\d.-]+)\)', b)
                d = arc_path(*v)
            else:
                v = num(r'\(center ([\d.-]+) ([\d.-]+)\)\n\t\t\(end ([\d.-]+) ([\d.-]+)\)', b)
                r = math.hypot(v[2]-v[0], v[3]-v[1])
                d = (f'M{v[0]-r},{v[1]} a{r},{r} 0 1,0 {2*r},0 a{r},{r} 0 1,0 {-2*r},0')
            if ly == "Edge.Cuts": stroke(silk, d, 0.25, "#3b4045")
            elif ly == side + ".Mask": stroke(mask, d, wd, GOLD)
            elif ly == side + ".SilkS": stroke(silk, d, wd, SILK)
            elif ly == side + ".Cu": stroke(cu, d, wd, CU)
    # text
    for m in re.finditer(r'\(gr_text "([^"]*)"\n\t\t\(at ([\d.-]+) ([\d.-]+) ([\d.-]+)\)\n'
                         r'\t\t\(layer "([^"]+)"\)[\s\S]{0,260}?\(size ([\d.]+)', SRC):
        t, x, y, rot, ly, sz = (m.group(1), float(m.group(2)), float(m.group(3)),
                                float(m.group(4)), m.group(5), float(m.group(6)))
        col = GOLD if ly == side + ".Mask" else SILK if ly == side + ".SilkS" else None
        if ly == side + ".Cu": continue                # under mask, invisible
        if not col: continue
        anch = "middle"
        if "(justify left" in m.group(0): anch = "start"
        mirror = ' transform="scale(-1,1)"' if side == "B" else ""
        silk.add(f'<g transform="translate({x},{y})"><text x="0" y="{sz*0.36}" '
                 f'font-family="DejaVu Sans Mono,monospace" font-size="{sz*1.05}" '
                 f'fill="{col}" text-anchor="{anch}"{mirror}>{t.replace("&","&amp;")}</text></g>')
    # tracks and zone
    for b in blocks("segment"):
        ly = re.search(r'\(layer "([^"]+)"\)', b).group(1)
        if ly != side + ".Cu": continue
        v = num(r'\(start ([\d.-]+) ([\d.-]+)\)\n\t\t\(end ([\d.-]+) ([\d.-]+)\)', b)
        w = float(re.search(r'\(width ([\d.]+)\)', b).group(1))
        stroke(cu, f'M{v[0]},{v[1]} L{v[2]},{v[3]}', w, CU)
    for b in blocks("zone"):
        if ('"%s.Cu"' % side) not in b: continue
        # the zone's own boundary is (polygon (pts ...)) - a filled zone also
        # carries (filled_polygon ...) blocks (KiCad's own computed result);
        # "\(polygon\n" does not match "filled_polygon" (the literal char
        # right after "(" differs), so this stays scoped to the simple
        # boundary even when real fill data is present.
        outline = re.search(r'\(polygon\n[\s\S]*?\n\t\t\)', b)
        pts = re.findall(r'\(xy ([\d.-]+) ([\d.-]+)\)', outline.group(0) if outline else "")
        d = "M" + " L".join(f"{a},{c}" for a, c in pts) + " Z"
        cu.d.insert(0, f'<path d="{d}" fill="{ZONE}" opacity="0.55"/>')
    # footprints
    for f in fpblocks():
        at = re.search(r'\n\t\(at ([\d.-]+) ([\d.-]+)\)', f)
        if not at: continue
        ox, oy = float(at.group(1)), float(at.group(2))
        for k, tag in (("fp_line", "l"), ("fp_circle", "c")):
            for m in re.finditer(r'\(%s\n[\s\S]*?\n\t\)' % k, f):
                b = m.group(0)
                ly = re.search(r'\(layer "([^"]+)"\)', b)
                wd = re.search(r'\(width ([\d.]+)\)', b)
                if not ly or not wd or ly.group(1) != side + ".SilkS": continue
                if tag == "l":
                    v = num(r'\(start ([\d.-]+) ([\d.-]+)\)\n\t\t\(end ([\d.-]+) ([\d.-]+)\)', b)
                    d = f'M{ox+v[0]},{oy+v[1]} L{ox+v[2]},{oy+v[3]}'
                else:
                    v = num(r'\(center ([\d.-]+) ([\d.-]+)\)\n\t\t\(end ([\d.-]+) ([\d.-]+)\)', b)
                    r = math.hypot(v[2]-v[0], v[3]-v[1]); cx, cy = ox+v[0], oy+v[1]
                    d = f'M{cx-r},{cy} a{r},{r} 0 1,0 {2*r},0 a{r},{r} 0 1,0 {-2*r},0'
                stroke(silk, d, float(wd.group(1)), SILK)
        for m in re.finditer(r'\(pad "([^"]*)" (\w+) (\w+)\n\t\t\(at ([\d.-]+) ([\d.-]+)\)\n'
                             r'\t\t\(size ([\d.]+) ([\d.]+)\)([\s\S]{0,340}?)\n\t\)', f):
            nm, kind, shp = m.group(1), m.group(2), m.group(3)
            x, y = ox+float(m.group(4)), oy+float(m.group(5))
            w, h = float(m.group(6)), float(m.group(7))
            body = m.group(8)
            lay = (re.search(r'\(layers ([^)]*)\)', body) or [None, ""])[1]
            drill = re.search(r'\(drill ([\d.]+)\)', body)
            onside = ("*.Cu" in lay or "F&B" in lay or (side + ".Cu") in lay)
            open_mask = ("*.Mask" in lay or (side + ".Mask") in lay)
            if onside and kind != "np_thru_hole":
                col = GOLD if open_mask else CU
                if shp == "rect":
                    pads.add(f'<rect x="{x-w/2}" y="{y-h/2}" width="{w}" height="{h}" fill="{col}"/>')
                else:
                    pads.add(f'<circle cx="{x}" cy="{y}" r="{w/2}" fill="{col}"/>')
            if drill:
                holes.add(f'<circle cx="{x}" cy="{y}" r="{float(drill.group(1))/2}" fill="{HOLE}"/>')
    return cu, mask, silk, pads, holes

def view(side, oy):
    cu, mask, silk, pads, holes = collect(side)
    flip = f'translate({W},0) scale(-1,1)' if side == "B" else ""
    inner = "\n".join(["".join(cu.d), "".join(pads.d), "".join(mask.d),
                       "".join(silk.d), "".join(holes.d)])
    return (f'<g transform="translate({PAD},{oy}) {flip}">'
            f'<rect x="0" y="0" width="{W}" height="{H}" rx="1.5" fill="{MASK}"/>'
            f'{inner}</g>')

def board_extent():
    """Width and height from the Edge.Cuts geometry actually in the file. This used to be
    the fascia's fixed 176 x 52, which drew every other board on a fascia-sized plate.
    Every generator here puts the board origin at (0, 0)."""
    xs, ys = [], []
    for k in ("gr_rect", "gr_line", "gr_arc", "gr_poly"):
        for b in blocks(k):
            if '(layer "Edge.Cuts")' not in b: continue
            for x, y in re.findall(r'\((?:start|mid|end|xy) ([\d.-]+) ([\d.-]+)\)', b):
                xs.append(float(x)); ys.append(float(y))
    return (max(xs), max(ys)) if xs else (176.0, 52.0)

W, H = board_extent()
body = view("F", PAD) + view("B", PAD*2 + H)
total_h = PAD*3 + H*2
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{(W+PAD*2)*S}" '
       f'height="{total_h*S}" viewBox="0 0 {W+PAD*2} {total_h}">'
       f'<rect width="100%" height="100%" fill="#191c1e"/>'
       f'<text x="{PAD}" y="{PAD-1.6}" font-family="monospace" font-size="2.2" '
       f'fill="#7C7972">FRONT - as the customer sees it</text>'
       f'<text x="{PAD}" y="{PAD*2+H-1.6}" font-family="monospace" font-size="2.2" '
       f'fill="#7C7972">BACK - mirrored, as the board sits in your hand</text>'
       f'{body}</svg>')
open(OUT, "w", encoding="utf8").write(svg)
print("wrote", OUT)
