#!/usr/bin/env python3
"""Hold the board to the schematic. Nothing else in this toolchain does.

checksch.py proves the schematic wires up. checkcopper.py and audit.py prove the board
routes and connects. Both can pass while the two files disagree about WHAT they are
connecting - which is exactly what happened here: the surface-mount board had gone to
J1 in the order its own routing preferred, and the through-hole board, routed later to
a different order, would have shipped a cable that fits neither drawing.

Compares net by net: every net name, and the exact set of ref.pin on it.

Usage:  python3 tools/checkmatch.py PCB/TS06-FASCIA-THT/TS06-FASCIA-THT.kicad_sch \\
                                    PCB/TS06-FASCIA-THT/TS06-FASCIA-THT.kicad_pcb
"""
import os, re, subprocess, sys

sch, pcb = sys.argv[1], sys.argv[2]
here = os.path.dirname(os.path.abspath(__file__))

r = subprocess.run([sys.executable, os.path.join(here, "checksch.py"), sch, "--netlist"],
                   capture_output=True, text=True)
S = {}
for ln in r.stdout.splitlines():
    if ln.startswith("#NET\t"):
        _, nm, pins = ln.split("\t")
        S[nm] = set(pins.split(",")) if pins else set()

P = {}
SRC = open(pcb, encoding="utf8").read()
for f in re.findall(r'\(footprint "[^"]+"[\s\S]*?\n\)', SRC):
    ref = (re.search(r'\(property "Reference" "([^"]+)"', f) or [None, "?"])[1]
    for m in re.finditer(r'\(pad "([^"]*)" \w+ \w+[\s\S]{0,400}?\n\t\)', f):
        net = re.search(r'\(net \d+ "([^"]*)"', m.group(0))
        if net and m.group(1):
            P.setdefault(net.group(1), set()).add(f"{ref}.{m.group(1)}")

bad = []
for nm in sorted(set(S) | set(P)):
    if nm.startswith("(unnamed"):
        bad.append(f'UNNAMED NET in the schematic carrying {sorted(S[nm])}'); continue
    a, b = S.get(nm, set()), P.get(nm, set())
    if a == b: continue
    if not a: bad.append(f'{nm}: on the board only - {sorted(b)}')
    elif not b: bad.append(f'{nm}: in the schematic only - {sorted(a)}')
    else:
        if a - b: bad.append(f'{nm}: in the schematic, not on the board - {sorted(a-b)}')
        if b - a: bad.append(f'{nm}: on the board, not in the schematic - {sorted(b-a)}')

print(f'{len(S)} nets in the schematic, {len(P)} on the board')
for x in bad: print("  " + x)
print(("\n%d disagreement(s)" % len(bad)) if bad else "\nthey agree")
sys.exit(1 if bad else 0)
