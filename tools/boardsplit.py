#!/usr/bin/env python3
"""If this board were two boards joined by a connector, how many wires would have to cross?

WHY IT EXISTS: the inherited AlexGyver board is two - a DRIVER half (Nano, К155ИД1, RTC, the
switches, the converter, power in) and a TUBE half (four sockets, the pip holes, the backlight
LEDs), joined by the P1/P3 headers. TS06-MAIN collapses all of it onto one board, and the
routing study has been measuring what that costs. Whether the inherited split is a lesson
rather than a limitation is a question with a NUMBER behind it, and the number is cheap: how
many nets have pads on both sides of a proposed seam.

HOW THE SEAM IS FOUND: not by guessing. Whatever the fascia holds - the tubes and the backlight
LEDs - is fixed to the display side. Every other part is then moved across one at a time, always
whichever leaves the fewest nets crossing, INCLUDING WHEN THAT IS WORSE than leaving it where it
is. That last part is the whole trick. A driver and the loads it drives have to move together or
not at all: each ИН-15 cathode runs from the tube to exactly one transistor, so moving the
transistor only swaps a CAT_ net for a base net, and moving the base resistor only swaps that
for an expander output. The eighteen of them collapse to SDA and SCL only when the expanders
themselves cross, forty-one parts later. A search that refuses to go uphill stops at 37 wires
and never finds the 18.

The curve it prints is wires-crossing against display-board size; its knees are the seams.

Usage:  python3 tools/boardsplit.py PCB/TS06-MAIN/TS06-MAIN.kicad_pcb [--at N] [--fascia RE]
"""
import re, sys
from collections import defaultdict

ARGS = sys.argv[1:]
SRC = open(ARGS[0], encoding="utf8").read()
AT = int(ARGS[ARGS.index("--at") + 1]) if "--at" in ARGS else None
FASCIA = re.compile(ARGS[ARGS.index("--fascia") + 1] if "--fascia" in ARGS else r"^(V|HL)\d")
POWER = {"GND", "+5V", "+12V", "HV185"}


def footprints(src):
    """Every top-level (footprint ...), paren-counted but SKIPPING quoted strings. A value like
    "10k (1%)" otherwise throws the count off and swallows the rest of the file. Part footprints
    sit at column 0 in these boards and mounting holes at one tab, so match either."""
    out, i, key = [], 0, re.compile("\n\t*" + re.escape("(footprint "))
    while True:
        m = key.search(src, i)
        if not m:
            return out
        i = m.start() + 1
        d, j, q = 0, i, False
        while True:
            ch = src[j]
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
        out.append(src[i:j + 1])
        i = j


parts, pads_of = {}, defaultdict(list)
for b in footprints(SRC):
    ref = (re.search(r'\(property "Reference" "([^"]+)"', b) or [None, "?"])[1]
    at = re.search(r'\n\t+\(at ([-\d.]+) ([-\d.]+)', b)
    if not at or ref == "?":
        continue
    ox, oy = float(at.group(1)), float(at.group(2))
    parts[ref] = (ox, oy)
    for pm in re.finditer(r'\(pad "[^"]*" \w+ \w+\n\t+\(at ([-\d.]+) ([-\d.]+)\)'
                          r'[\s\S]{0,400}?\(net (\d+) "([^"]*)"\)', b):
        if pm.group(4):
            pads_of[pm.group(4)].append(ref)

if not parts:
    sys.exit("no footprints with references in " + ARGS[0])


def crossing(side):
    return sorted(n for n, rs in pads_of.items()
                  if len({side[r] for r in rs if r in side}) > 1)


side = {r: (0 if FASCIA.match(r) else 1) for r in parts}
if not any(v == 0 for v in side.values()):
    sys.exit("nothing matched --fascia, so there is no display side to start from")

curve, snap = [(sum(1 for v in side.values() if v == 0), len(crossing(side)), "the fascia parts")], {}
while any(v == 1 for v in side.values()):
    pick, bk = None, None
    for r, v in side.items():
        if v == 1:
            side[r] = 0
            k = len(crossing(side))
            side[r] = 1
            if bk is None or k < bk:
                pick, bk = r, k
    side[pick] = 0
    n0 = sum(1 for v in side.values() if v == 0)
    curve.append((n0, bk, pick))
    snap[n0] = dict(side)

print(f"{len(parts)} parts, {len(pads_of)} nets")
print(f"{'display':>8} {'driver':>7} {'wires':>6}   moved across")
prev = None
for n0, k, who in curve:
    if len(parts) - n0 < 4:
        break
    gain = f"   <-- {prev - k} fewer" if prev is not None and k < prev else ""
    print(f"{n0:8d} {len(parts) - n0:7d} {k:6d}   {who}{gain}")
    prev = k

if AT is not None and AT in snap:
    s, cr = snap[AT], crossing(snap[AT])
    print()
    print(f"=== the seam at {AT} display parts: {len(cr)} wires")
    print("  power:  " + " ".join(sorted(set(cr) & POWER)))
    print("  signal: " + " ".join(sorted(set(cr) - POWER)))
    print()
    print("  display: " + " ".join(sorted(r for r, v in s.items() if v == 0)))
    print("  driver:  " + " ".join(sorted(r for r, v in s.items() if v == 1)))
