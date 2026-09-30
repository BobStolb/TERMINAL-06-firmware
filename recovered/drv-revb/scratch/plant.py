"""plant.py SRC_DIR DST_DIR: copy a TS06-DRV board and plant one GND track 0.70 mm from VD5.1 (HV185):
legal under the HV class's 0.6 mm, illegal under the 0.8 mm pad rule."""
import os, shutil, sys
src, dst = sys.argv[1], sys.argv[2]
os.makedirs(dst, exist_ok=True)
for f in ("TS06-DRV.kicad_pcb", "TS06-DRV.kicad_pro", "TS06-DRV.kicad_dru", "fp-lib-table"):
    shutil.copy(os.path.join(src, f), os.path.join(dst, f))
p = os.path.join(dst, "TS06-DRV.kicad_pcb")
s = open(p, encoding="utf8").read()
y = 2.8 + 1.1 + 0.70 + 0.125
seg = (f'\t(segment\n\t\t(start 126.0 {y})\n\t\t(end 130.4 {y})\n\t\t(width 0.25)\n\t\t(layer "F.Cu")\n'
       f'\t\t(net 81)\n\t\t(uuid "00000000-0000-4000-8000-00000000abcd")\n\t)\n')
i = s.rindex("\t(embedded_fonts no)")
s = s[:i] + seg + s[i:]
open(p, "w", encoding="utf8").write(s)
print("planted GND track at y", y, "in", p)
