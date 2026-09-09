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
for f in extract_footprints(SRC):
    ref = (re.search(r'\(property "Reference" "([^"]+)"', f) or [None, "?"])[1]
    for m in re.finditer(r'\(pad "([^"]*)" \w+ \w+[\s\S]{0,400}?\n\t\)', f):
        net = re.search(r'\(net (?:\d+ )?"([^"]*)"', m.group(0))
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
