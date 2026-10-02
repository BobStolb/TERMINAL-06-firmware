#!/usr/bin/env python3
"""Does every drilled pad have its part's model over it? The second half of tools/model_coverage.py.

    python3 tools/model_pad_coverage.py [TS06-DRV | TS06-DISP | TS06-FASCIA-rhythm]     # default TS06-DRV

tools/model_coverage.py asks whether each footprint resolves to a model FILE that exists. That does not say the model sits on the
pads: a part drawn at the wrong place, or a strip that covers half its pads, still resolves. This reads the populated GLB of the board
(3d/populated/<board>-populated.glb, the placed models), takes each part's plan outline (the convex hull of its mesh, in the board's
x / y) and checks every drilled pad of that footprint against it, with 0.6 mm to spare. A pad outside its own part's outline is a pad
drawn empty. The list printed must be exactly the allowlisted footprints (3d/populated/allowlist.md); anything else is a missing or
misplaced model. Exit 1 if a footprint that is not on the allowlist has a pad outside its model. Needs numpy.
"""
import math, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import fit_table as FT
import sexp as S
import models3d as M


def hull(pts):
    p = sorted(set((round(float(x), 3), round(float(y), 3)) for x, y in pts))
    if len(p) < 3:
        return p

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for q in p:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], q) <= 0:
            lo.pop()
        lo.append(q)
    for q in reversed(p):
        while len(up) >= 2 and cross(up[-2], up[-1], q) <= 0:
            up.pop()
        up.append(q)
    return lo[:-1] + up[:-1]


def dist_to_hull(pt, h):
    """0 if inside the convex hull (ccw), else the distance to it."""
    n = len(h)
    if n == 0:
        return 1e9
    inside = True
    best = 1e9
    for i in range(n):
        a, b = h[i], h[(i + 1) % n]
        if n >= 3 and (b[0] - a[0]) * (pt[1] - a[1]) - (b[1] - a[1]) * (pt[0] - a[0]) < 0:
            inside = False
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = dx * dx + dy * dy
        t = 0 if L == 0 else max(0, min(1, ((pt[0] - a[0]) * dx + (pt[1] - a[1]) * dy) / L))
        best = min(best, math.hypot(pt[0] - a[0] - t * dx, pt[1] - a[1] - t * dy))
    return 0.0 if inside and n >= 3 else best


def place(at, x, y):
    a = math.radians(float(at[3])) if len(at) > 3 else 0.0
    return (float(at[1]) + x * math.cos(a) + y * math.sin(a), float(at[2]) - x * math.sin(a) + y * math.cos(a))


name = sys.argv[1] if len(sys.argv) > 1 else "TS06-DRV"
glb = {"TS06-DRV": os.path.join(ROOT, "3d/populated/TS06-DRV-populated.glb"), "TS06-DISP": os.path.join(ROOT, "3d/populated/TS06-DISP-populated.glb"),
       "TS06-FASCIA-rhythm": os.path.join(ROOT, "3d/populated/TS06-FASCIA-rhythm-populated.glb")}[name]
parts = FT.glb_parts(glb)
mp = M.load_map()
tree = S.parse(open(os.path.join(ROOT, "PCB", name, name + ".kicad_pcb"), encoding="utf8").read())
plan = {r["ref"]: r for r in M.plan(tree, name, mp, M.dirs(mp))}
hulls = {r: hull(v[:, [0, 2]]) for r, v in parts.items()}
flag = []
total = 0
for fp in S.find_all(tree, "footprint"):
    ref = [S.unq(p[2]) for p in S.find_all(fp, "property") if S.unq(p[1]) == "Reference"][0]
    at = S.find(fp, "at")
    pads = [p for p in S.find_all(fp, "pad") if S.find(p, "drill")]
    if not pads:
        continue
    st = plan[ref]["status"]
    out = []
    for p in pads:
        pa = S.find(p, "at")
        c = place(at, float(pa[1]), float(pa[2]))
        total += 1
        d = dist_to_hull(c, hulls[ref]) if ref in hulls else 1e9
        if d > 0.6:
            out.append((S.unq(p[1]), round(d, 2)))
    if out:
        flag.append((ref, plan[ref]["fp"], st, len(pads), out))
print("%s: %d drilled pads checked against the plan hull of their own part's model (0.6 mm margin)" % (name, total))
for ref, fpn, st, n, out in sorted(flag, key=lambda t: (t[2], t[0])):
    print("  %-5s %-44s %-11s %d of %d pads outside the model: %s" % (ref, fpn[:44], st, len(out), n, ",".join(p for p, _ in out)[:50]))
print("flagged footprints by status:", {s: sum(1 for f in flag if f[2] == s) for s in ("ok", "allowlisted", "missing")})
bad = [f[0] for f in flag if f[2] != "allowlisted"]
print("model pad coverage %s: %s" % (name, "PASS (every footprint outside its model is on the allowlist)" if not bad else "FAIL: " + ", ".join(bad)))
sys.exit(1 if bad else 0)
