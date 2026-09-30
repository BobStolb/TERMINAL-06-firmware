"""funnel2.py: the funnel's crossings plus the RC pads that sit on another net's straight band."""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import funnel as F


def segd(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    L = (bx - ax) ** 2 + (by - ay) ** 2
    t = max(0, min(1, ((px - ax) * (bx - ax) + (py - ay) * (by - ay)) / L)) if L else 0
    return math.hypot(px - ax - t * (bx - ax), py - ay - t * (by - ay))


NET = {"R72": ("A6", "GND"), "R73": ("D7", "D7_J"), "R74": ("D8", "D8_J"), "C18": ("D7_J", "GND"), "C19": ("D8_J", "GND")}


def blocked(name, rc):
    F.score(name, rc)
    pads = [(rc[r][i], NET[r][i], f"{r}.{i + 1}") for r in rc for i in (0, 1)]
    hits = []
    for n, a, b in F.bands(rc):
        for p, pn, lbl in pads:
            if pn != n and segd(p, a, b) < 1.15 and p not in (a, b):
                hits.append(f"{n} over {lbl} ({pn})")
    print(f"   {len(hits)} RC pads on another net's band: " + ", ".join(hits))


C = {"R72": ((139.4, 80.0), (139.4, 90.16)), "R73": ((167.0, 80.0), (156.84, 80.0)),
     "R74": ((169.5, 83.0), (159.34, 83.0)), "C18": ((156.84, 83.0), (156.84, 85.5)),
     "C19": ((159.34, 86.0), (159.34, 88.5))}
blocked("predecessor (near() at J1)", F.PRED)
blocked("option C (block east of the funnel, R72 west)", C)
