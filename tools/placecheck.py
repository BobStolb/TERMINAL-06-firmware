#!/usr/bin/env python3
"""How much of this board's wiring is decided by WHERE THE PARTS ARE, before any routing?

WHY IT EXISTS: a day was spent tuning the router on TS06-MAIN - a grain, a via price, history
decay, a tighten pass, bundle affinity - and it moved the copper by about 300 mm and took a
third of the vias out. Then somebody asked why the same few nets kept appearing at the top of
the detour table, and the answer was that they are long because their parts are far apart. The
Nano sat at one corner with twenty-eight connections reaching across the board; the К155ИД1 sat
40 mm above the row of tubes it drives, so every one of its ten cathode lines paid that detour
twice. Moving those two parts takes 16% off the floor - five times what every routing rule put
together achieved (18.09.26).

So this measures the floor, not the copper. For each net it takes the Euclidean minimum spanning
tree over that net's own pads: the shortest wiring that could POSSIBLY connect them, with no
obstacles, no clearances and no layers. No router beats it, so it is what the placement costs
before routing is even attempted. GND is left out, being poured rather than wired.

It does not place anything. It says where to look, which is the honest scope: the constraints
that decide a real placement - the USB port out through the case, the tube positions set by the
fascia, a courtyard that must not overlap - live in tools/mkpcb_main.py and not in a metric.

Usage:
  python3 tools/placecheck.py BOARD.kicad_pcb                 the floor, and what each part costs
  python3 tools/placecheck.py BOARD.kicad_pcb --move U1=22,66 --move U2=20,41
  python3 tools/placecheck.py BOARD.kicad_pcb --sweep U2       best position for one part
  python3 tools/placecheck.py BOARD.kicad_pcb --sweep U1 --x 21.98      ... on a fixed column
"""
import re, sys, math
from collections import defaultdict

A = sys.argv[1:]
SRC = open(A[0], encoding="utf8").read()
MOVES = dict(m.split("=", 1) for m in (A[i + 1] for i, a in enumerate(A) if a == "--move"))
SWEEP = A[A.index("--sweep") + 1] if "--sweep" in A else None
FIXX = float(A[A.index("--x") + 1]) if "--x" in A else None
FIXED = re.compile(r"^(V|HL)\d")            # the fascia decides these; never suggest moving them


def footprints(s):
    """Top-level (footprint ...), paren-counted but skipping quoted strings - a value like
    "10k (1%)" throws the count off otherwise. Parts sit at column 0 here, holes at one tab."""
    out, i, key = [], 0, re.compile("\n\t*" + re.escape("(footprint "))
    while True:
        m = key.search(s, i)
        if not m:
            return out
        i = m.start() + 1
        d, j, q = 0, i, False
        while True:
            ch = s[j]
            if q:
                if ch == chr(92):
                    j += 1
                elif ch == '"':
                    q = False
            elif ch == '"':
                q = True
            elif ch == "(":
                d += 1
            elif ch == ")":
                d -= 1
                if d == 0:
                    break
            j += 1
        out.append(s[i:j + 1])
        i = j


padof, pos = defaultdict(list), {}           # net -> [(ref, dx, dy)] offsets inside the part
for b in footprints(SRC):
    ref = (re.search(r'\(property "Reference" "([^"]+)"', b) or [None, "?"])[1]
    at = re.search(r'\n\t+\(at ([-\d.]+) ([-\d.]+)', b)
    if not at or ref == "?":
        continue
    pos[ref] = (float(at.group(1)), float(at.group(2)))
    for pm in re.finditer(r'\(pad "[^"]*" \w+ \w+\n\t+\(at ([-\d.]+) ([-\d.]+)\)'
                          r'[\s\S]{0,400}?\(net (\d+) "([^"]*)"\)', b):
        if pm.group(4):
            padof[pm.group(4)].append((ref, float(pm.group(1)), float(pm.group(2))))
if not pos:
    sys.exit("no footprints with references in " + A[0])
for ref, xy in MOVES.items():
    pos[ref] = tuple(float(v) for v in xy.split(","))


def mst(p):
    if len(p) < 2:
        return 0.0
    rest, tot = list(p[1:]), 0.0
    d = [math.dist(p[0], q) for q in rest]
    while rest:
        k = min(range(len(rest)), key=d.__getitem__)
        tot += d[k]
        q = rest.pop(k)
        d.pop(k)
        for i, r in enumerate(rest):
            d[i] = min(d[i], math.dist(q, r))
    return tot


def floor(P, only=None):
    return sum(mst(sorted({(round(P[r][0] + dx, 3), round(P[r][1] + dy, 3)) for r, dx, dy in ps}))
               for n, ps in padof.items() if n and n != "GND" and (only is None or only(n)))


base = floor(pos)
xs = [p[0] for p in pos.values()]
ys = [p[1] for p in pos.values()]
print(f"{len(pos)} parts, {len(padof)} nets")
print(f"routing floor (MST over each net's own pads, GND excluded): {base:.0f} mm")
if MOVES:
    print("  with " + ", ".join(f"{k} at {v}" for k, v in MOVES.items()))

if SWEEP:
    if SWEEP not in pos:
        sys.exit(SWEEP + " is not on this board")
    print()
    print(f"sweeping {SWEEP} (now at {pos[SWEEP][0]:.1f}, {pos[SWEEP][1]:.1f})"
          + (f", column fixed at x={FIXX}" if FIXX is not None else "") + ":")
    P, best = dict(pos), None
    cols = [FIXX] if FIXX is not None else [min(xs) + k * (max(xs) - min(xs)) / 32.0 for k in range(33)]
    rows = [min(ys) + k * (max(ys) - min(ys)) / 32.0 for k in range(33)]
    for x in cols:
        for y in rows:
            P[SWEEP] = (x, y)
            f = floor(P)
            if best is None or f < best[2]:
                best = (x, y, f)
    print(f"  best at ({best[0]:.1f}, {best[1]:.1f}): {best[2]:.0f} mm, "
          f"{100 * (base - best[2]) / base:.1f}% less than as placed")
    sys.exit(0)

# what each part would save by sitting where its own connections want it - a Weber point over
# the other ends of its nets. Unconstrained, so it is an upper bound and a direction, not a plan.
link = defaultdict(list)
for n, ps in padof.items():
    if not n or n == "GND" or len(ps) > 8:
        continue
    for ra, ax, ay in ps:
        for rb, bx, by in ps:
            if ra != rb:
                link[ra].append((pos[rb][0] + bx, pos[rb][1] + by))
rows = []
for ref, pts in link.items():
    if FIXED.match(ref):
        continue
    now = sum(math.dist(pos[ref], p) for p in pts)
    x, y = pos[ref]
    for _ in range(60):                      # Weiszfeld
        nx = ny = den = 0.0
        for px, py in pts:
            d = max(math.hypot(x - px, y - py), 1e-6)
            nx += px / d
            ny += py / d
            den += 1 / d
        x, y = nx / den, ny / den
    rows.append((now - sum(math.dist((x, y), p) for p in pts), ref, pos[ref], (x, y), len(pts)))
rows.sort(reverse=True)
print()
print("what a part would save by sitting where its own connections want it:")
print(f"  {'saves':>7}  ref    is at            wants           links")
for s, ref, p, b, n in rows[:12]:
    print(f"  {s:7.0f}  {ref:5s} ({p[0]:6.1f},{p[1]:5.1f})  ({b[0]:6.1f},{b[1]:5.1f})  {n:5d}")
print()
print("These are unconstrained and each is computed against every OTHER part staying put, so")
print("they do not add up and the best pair is not the best two singly. Use --sweep and --move")
print("to price a real proposal.")
