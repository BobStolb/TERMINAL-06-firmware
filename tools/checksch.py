#!/usr/bin/env python3
"""Offline connectivity check for a KiCad schematic - the ERC you can run without KiCad.

Parses lib_symbols pin positions, transforms every placed instance's pins into sheet
coordinates, and reports any pin that has no wire, junction or label on it. Catches
the failure that looks fine on screen until you generate a netlist: a symbol whose
pins are longer or shorter than the wiring assumed, leaving hairline gaps.

Usage:  python3 tools/checksch.py PCB/TS06-FASCIA/TS06-FASCIA.kicad_sch

HIERARCHY (added 30.09.26 for the TS06-DISP/TS06-DRV schematics, tools/mksch_pair.py).
Give it the root sheet and it follows every (sheet ...) into its file, as KiCad does:
  * a local label is local to its sheet: on the root it keeps its bare name (as before),
    on a sub-sheet it becomes "/Sheet name/NAME", KiCad's own name for such a net;
  * a global label is one net across all sheets, under its bare name;
  * a power symbol (a lib symbol marked "power" whose pin is a power input) names its net
    by its Value, and is not a member of the net itself (its reference starts with #);
  * a hierarchical label joins the sheet pin of the same name on the parent's sheet box.
A flat, single-sheet schematic reads exactly as it did before.
"""
import os, re, sys, math

def tok(s):
    out, i, n = [], 0, len(s)
    while i < n:
        c = s[i]
        if c.isspace(): i += 1
        elif c in "()": out.append(c); i += 1
        elif c == '"':
            j = i + 1; b = []
            while s[j] != '"':
                if s[j] == "\\": b.append(s[j + 1]); j += 2
                else: b.append(s[j]); j += 1
            out.append(('S', "".join(b))); i = j + 1
        else:
            j = i
            while j < n and not s[j].isspace() and s[j] not in "()\"": j += 1
            out.append(('A', s[i:j])); i = j
    return out

def parse(t, i=0):
    assert t[i] == "("
    node, i = [], i + 1
    while t[i] != ")":
        if t[i] == "(":
            sub, i = parse(t, i); node.append(sub)
        else:
            node.append(t[i][1]); i += 1
    return node, i + 1

def kids(n, name): return [c for c in n if isinstance(c, list) and c and c[0] == name]
def kid(n, name):
    k = kids(n, name); return k[0] if k else None
def nums(n, k=1): return [float(x) for x in n[k:] if re.match(r'^-?[\d.]+$', str(x))]
def prop(n, name): return next((p[2] for p in kids(n, "property") if p[1] == name), None)

def load(path):
    return parse(tok(open(path, encoding="utf8").read()))[0]

# --- every sheet of the design: (tree, sheet path, index of parent, sheet box in the parent)
sheets = [(load(sys.argv[1]), "/", None, None)]
i = 0
while i < len(sheets):
    tree = sheets[i][0]
    base = os.path.dirname(os.path.abspath(sys.argv[1]))
    for sh in kids(tree, "sheet"):
        name, fn = prop(sh, "Sheetname"), prop(sh, "Sheetfile")
        sheets.append((load(os.path.join(base, fn)), sheets[i][1] + name + "/", i, sh))
    i += 1

def to_sheet(px, py, X, Y, rot):
    a = math.radians(rot)
    sx = px * math.cos(a) - py * math.sin(a)
    sy = px * math.sin(a) + py * math.cos(a)
    return round(X + sx, 3), round(Y - sy, 3)

def label_name(kind, text, spath):
    if kind == "label" and spath != "/":
        return spath + text                     # KiCad names a sub-sheet's local net "/Sheet/NAME"
    return text

bad = ok = 0
par = {}
def find(x):
    par.setdefault(x, x)
    while par[x] != x: par[x] = par[par[x]]; x = par[x]
    return x
def union(a, b): par[find(a)] = find(b)

def on_seg(p, s):
    (x1,y1),(x2,y2) = s
    if p in s: return False
    cross = (x2-x1)*(p[1]-y1) - (y2-y1)*(p[0]-x1)
    if abs(cross) > 1e-6: return False
    return (min(x1,x2)-1e-6 <= p[0] <= max(x1,x2)+1e-6
            and min(y1,y2)-1e-6 <= p[1] <= max(y1,y2)+1e-6)

names, members, nets_seen = {}, {}, []
for si, (root, spath, parent, box) in enumerate(sheets):
    where = "" if spath == "/" else f" [{spath}]"
    # --- library pin geometry, in symbol space; which lib symbols are power symbols
    libpins, power = {}, set()
    for sym in kids(kid(root, "lib_symbols") or [], "symbol"):
        name = sym[1]
        if re.search(r"_\d+_\d+$", name): continue
        pts = []
        for sub in kids(sym, "symbol"):
            for p in kids(sub, "pin"):
                at = nums(kid(p, "at")); ln = nums(kid(p, "length"))[0]
                pts.append((at[0], at[1], at[2], ln, kid(p, "number")[1], p[1]))
        libpins[name] = pts
        if kid(sym, "power") is not None or "power" in sym:
            power.add(name)

    # --- everything a pin may legally land on
    ends = set()
    for w in kids(root, "wire"):
        for p in kids(kid(w, "pts"), "xy"):
            ends.add((round(float(p[1]), 3), round(float(p[2]), 3)))
    for kind in ("junction", "label", "global_label", "hierarchical_label", "no_connect"):
        for j in kids(root, kind):   # a no-connect flag is a deliberate, legal landing
            a = nums(kid(j, "at")); ends.add((round(a[0], 3), round(a[1], 3)))
    placed = []
    pinpts = {}
    for s in kids(root, "symbol"):
        lid = kid(s, "lib_id")
        if not lid: continue
        ref = next((p[2] for p in kids(s, "property") if p[1] == "Reference"), "?")
        # the reference of this instance in this project, if the file carries several
        for inst in kids(kid(s, "instances") or [], "project"):
            for pth in kids(inst, "path"):
                r = kid(pth, "reference")
                if r: ref = r[1]
        at = nums(kid(s, "at")); X, Y, rot = at[0], at[1], (at[2] if len(at) > 2 else 0)
        for px, py, _, _, num, etype in libpins.get(lid[1], []):
            pt = to_sheet(px, py, X, Y, rot)
            placed.append((ref, lid[1], num, etype, pt, s))
            pinpts[pt] = pinpts.get(pt, 0) + 1
    for ref, lib, num, etype, (x, y), s in placed:
        if (x, y) in ends or pinpts[(x, y)] > 1: ok += 1
        else:
            bad += 1
            near = sorted(ends, key=lambda e: math.hypot(e[0] - x, e[1] - y))[:1]
            d = math.hypot(near[0][0] - x, near[0][1] - y) if near else 999
            print(f"  DANGLING  {ref:4s} pin {num:2s} at ({x:8.3f},{y:8.3f}){where}"
                  f"   nearest connection {d:6.2f} mm away at {near[0] if near else '-'}")

    # ---------------------------------------------------------------- net trace
    # Union-find over wire endpoints. A point sitting on another wire's interior is a
    # T-junction and connects, same as KiCad treats it. Points are keyed by sheet.
    K = lambda p: (si, p[0], p[1])
    segs = []
    for w in kids(root, "wire"):
        a, b = kids(kid(w, "pts"), "xy")
        segs.append(((round(float(a[1]),3), round(float(a[2]),3)),
                     (round(float(b[1]),3), round(float(b[2]),3))))
    for a, b in segs: union(K(a), K(b))
    allpts = {p for s in segs for p in s}
    for p in allpts:
        for s in segs:
            if on_seg(p, s): union(K(p), K(s[0]))
    for pt, n in pinpts.items():                 # pins meeting pins connect
        if n > 1 or pt in allpts: find(K(pt))
    labels = [(kind, l) for kind in ("label", "global_label", "hierarchical_label") for l in kids(root, kind)]
    for kind, l in labels:
        a = nums(kid(l, "at")); pt = (round(a[0],3), round(a[1],3))
        if K(pt) not in par:
            # A label is normally dropped on the MIDDLE of a wire, not its endpoint.
            # KiCad attaches it to that wire; this checker used to ignore it and then
            # report a perfectly well-named net as unnamed.
            for sg in segs:
                if on_seg(pt, sg) or pt in sg:
                    find(K(pt)); union(K(pt), K(sg[0])); break
        if kind == "hierarchical_label":
            union(K(pt), ("H", si, l[1]))      # ... to the sheet pin of that name, one level up
            continue
        if K(pt) in par or pinpts.get(pt): names.setdefault(find(K(pt)), set()).add(label_name(kind, l[1], spath))
    if box is not None:
        for p in kids(box, "pin"):
            a = nums(kid(p, "at")); pt = (round(a[0],3), round(a[1],3))
            union((parent, pt[0], pt[1]), ("H", si, p[1]))
    for ref, lib, num, etype, pt, s in placed:
        if lib in power and etype == "power_in":
            val = prop(s, "Value")
            nets_seen.append((K(pt), val))
            continue
        if ref.startswith("#") or K(pt) not in par:
            continue                            # a power symbol, or a pin on nothing but a no-connect
        members.setdefault(K(pt), []).append(f"{ref}.{num}")

# power symbols name their nets; everything is resolved once all sheets are joined
roots_names = {}
for k, v in names.items():
    roots_names.setdefault(find(k), set()).update(v)
for k, val in nets_seen:
    roots_names.setdefault(find(k), set()).add(val)
groups = {}
for k, ms in members.items():
    groups.setdefault(find(k), []).extend(ms)

print(f"\n{ok} pins connected, {bad} dangling")

# Same-named labels are one net in KiCad, so the pieces are merged by name here
# before anything is printed. --netlist prints the result in a form another tool can
# read; tools/checkmatch.py uses it to hold the board to the schematic.
byname = {}
for r in groups:
    nm = "/".join(sorted(roots_names.get(r, []))) or f"(unnamed-{r})"
    byname.setdefault(nm, set()).update(groups[r])
if "--netlist" in sys.argv:
    for nm in sorted(byname):
        print("#NET\t%s\t%s" % (nm, ",".join(sorted(byname[nm]))))

print("\n--- nets ---")
for r in sorted(groups, key=lambda k: -len(groups[k])):
    nm = "/".join(sorted(roots_names.get(r, []))) or "(unnamed)"
    print(f"  {nm:10s} {sorted(groups[r])}")
conflict = [n for n in roots_names.values() if len(n) > 1]
if conflict: print("\n  WARNING - one net carries several label names:", conflict)
sys.exit(1 if bad else 0)
