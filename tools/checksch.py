#!/usr/bin/env python3
"""Offline connectivity check for a KiCad schematic - the ERC you can run without KiCad.

Parses lib_symbols pin positions, transforms every placed instance's pins into sheet
coordinates, and reports any pin that has no wire, junction or label on it. Catches
the failure that looks fine on screen until you generate a netlist: a symbol whose
pins are longer or shorter than the wiring assumed, leaving hairline gaps.

Usage:  python3 tools/checksch.py PCB/TS06-FASCIA/TS06-FASCIA.kicad_sch
"""
import re, sys, math

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

root, _ = parse(tok(open(sys.argv[1], encoding="utf8").read()))

# --- library pin geometry, in symbol space
libpins = {}
for sym in kids(kid(root, "lib_symbols"), "symbol"):
    name = sym[1]
    if re.search(r"_\d+_\d+$", name): continue
    pts = []
    for sub in kids(sym, "symbol"):
        for p in kids(sub, "pin"):
            at = nums(kid(p, "at")); ln = nums(kid(p, "length"))[0]
            pts.append((at[0], at[1], at[2], ln, kid(p, "number")[1]))
    libpins[name] = pts

def to_sheet(px, py, X, Y, rot):
    a = math.radians(rot)
    sx = px * math.cos(a) - py * math.sin(a)
    sy = px * math.sin(a) + py * math.cos(a)
    return round(X + sx, 3), round(Y - sy, 3)

# --- everything a pin may legally land on
ends = set()
for w in kids(root, "wire"):
    for p in kids(kid(w, "pts"), "xy"):
        ends.add((round(float(p[1]), 3), round(float(p[2]), 3)))
for j in kids(root, "junction"):
    a = nums(kid(j, "at")); ends.add((round(a[0], 3), round(a[1], 3)))
for l in kids(root, "label"):
    a = nums(kid(l, "at")); ends.add((round(a[0], 3), round(a[1], 3)))
for nc in kids(root, "no_connect"):          # a no-connect flag is a deliberate, legal landing
    a = nums(kid(nc, "at")); ends.add((round(a[0], 3), round(a[1], 3)))

bad = ok = 0
for s in kids(root, "symbol"):
    lid = kid(s, "lib_id")
    if not lid: continue
    ref = next((p[2] for p in kids(s, "property") if p[1] == "Reference"), "?")
    at = nums(kid(s, "at")); X, Y, rot = at[0], at[1], (at[2] if len(at) > 2 else 0)
    for px, py, _, _, num in libpins.get(lid[1], []):
        x, y = to_sheet(px, py, X, Y, rot)
        if (x, y) in ends: ok += 1
        else:
            bad += 1
            near = sorted(ends, key=lambda e: math.hypot(e[0] - x, e[1] - y))[:1]
            d = math.hypot(near[0][0] - x, near[0][1] - y) if near else 999
            print(f"  DANGLING  {ref:4s} pin {num:2s} at ({x:8.3f},{y:8.3f})"
                  f"   nearest connection {d:6.2f} mm away at {near[0] if near else '-'}")
print(f"\n{ok} pins connected, {bad} dangling")

# ---------------------------------------------------------------- net trace
# Union-find over wire endpoints. A point sitting on another wire's interior is a
# T-junction and connects, same as KiCad treats it.
segs = []
for w in kids(root, "wire"):
    a, b = kids(kid(w, "pts"), "xy")
    segs.append(((round(float(a[1]),3), round(float(a[2]),3)),
                 (round(float(b[1]),3), round(float(b[2]),3))))
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

for a, b in segs: union(a, b)
allpts = {p for s in segs for p in s}
for p in allpts:
    for s in segs:
        if on_seg(p, s): union(p, s[0])

names, members = {}, {}
for l in kids(root, "label"):
    a = nums(kid(l, "at")); pt = (round(a[0],3), round(a[1],3))
    if pt not in par:
        # A label is normally dropped on the MIDDLE of a wire, not its endpoint.
        # KiCad attaches it to that wire; this checker used to ignore it and then
        # report a perfectly well-named net as unnamed.
        for sg in segs:
            if on_seg(pt, sg) or pt in sg:
                par[pt] = pt; union(pt, sg[0]); break
    if pt in par: names.setdefault(find(pt), set()).add(l[1])
for sym in kids(root, "symbol"):
    lid = kid(sym, "lib_id")
    if not lid: continue
    ref = next((q[2] for q in kids(sym, "property") if q[1] == "Reference"), "?")
    at = nums(kid(sym, "at")); X, Y, rot = at[0], at[1], (at[2] if len(at) > 2 else 0)
    for px, py, _, _, num in libpins.get(lid[1], []):
        pt = to_sheet(px, py, X, Y, rot)
        if pt in par: members.setdefault(find(pt), []).append(f"{ref}.{num}")

# Same-named local labels are one net in KiCad, so the pieces are merged by name here
# before anything is printed. --netlist prints the result in a form another tool can
# read; tools/checkmatch.py uses it to hold the board to the schematic.
byname = {}
for r in members:
    nm = "/".join(sorted(names.get(r, []))) or f"(unnamed-{r})"
    byname.setdefault(nm, set()).update(members[r])
if "--netlist" in sys.argv:
    for nm in sorted(byname):
        print("#NET\t%s\t%s" % (nm, ",".join(sorted(byname[nm]))))

print("\n--- nets ---")
for r in sorted(members, key=lambda k: -len(members[k])):
    nm = "/".join(sorted(names.get(r, []))) or "(unnamed)"
    print(f"  {nm:10s} {sorted(members[r])}")
conflict = [n for n in names.values() if len(n) > 1]
if conflict: print("\n  WARNING - one net carries several label names:", conflict)
sys.exit(1 if bad else 0)
