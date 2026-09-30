#!/usr/bin/env python3
"""Copy one board into the scratch tree for export, and give it a black-mask / white-silk stackup
if it has none.

    python3 prep_board.py REPO/PCB/TS06-X/TS06-X.kicad_pcb OUTDIR

The repository file is never touched. TS06-DRV and TS06-DISP already carry a stackup with black
mask and white silk. TS06-FASCIA has none (it is written by a different generator), so KiCad would
render it green; PCB/README.md orders it "2.0 mm FR4, black mask, white silk, ENIG", and that is
the stackup injected here, into the copy only. Prints "stackup: kept" or "stackup: injected".
"""
import os, re, shutil, sys

STACKUP = """		(stackup
			(layer "F.SilkS" (type "Top Silk Screen") (color "White"))
			(layer "F.Mask" (type "Top Solder Mask") (color "Black") (thickness 0.01))
			(layer "F.Cu" (type "copper") (thickness 0.035))
			(layer "dielectric 1" (type "core") (thickness {core}) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
			(layer "B.Cu" (type "copper") (thickness 0.035))
			(layer "B.Mask" (type "Bottom Solder Mask") (color "Black") (thickness 0.01))
			(layer "B.SilkS" (type "Bottom Silk Screen") (color "White"))
			(copper_finish "ENIG")
			(dielectric_constraints no)
		)
"""


def main(src, outdir):
    os.makedirs(outdir, exist_ok=True)
    d = os.path.dirname(src)
    name = os.path.splitext(os.path.basename(src))[0]
    for f in (name + ".kicad_pcb", name + ".kicad_pro", "fp-lib-table"):
        p = os.path.join(d, f)
        if os.path.exists(p):
            shutil.copy(p, os.path.join(outdir, f))
    pcb = os.path.join(outdir, name + ".kicad_pcb")
    s = open(pcb, encoding="utf8").read()
    if "(stackup" in s:
        print("stackup: kept")
        return
    m = re.search(r"\(general\s+\(thickness ([\d.]+)\)", s)
    t = float(m.group(1)) if m else 1.6
    core = round(t - 2 * 0.035 - 2 * 0.01, 3)
    i = s.index("(setup")
    j = s.index("\n", i) + 1
    s = s[:j] + STACKUP.format(core=core) + s[j:]
    open(pcb, "w", encoding="utf8").write(s)
    print("stackup: injected (black mask, white silk, %.2f mm)" % t)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
