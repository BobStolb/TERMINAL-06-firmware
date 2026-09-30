"""region.py OUT.png x0 y0 x1 y1 [ppm] [display]: courtyards, pads, holes, tracks of TS06-DRV in a window
(DRV frame; with 'display' the window's y is the display frame, y + 26)."""
import os, sys
sys.path.insert(0, "/home/user/TERMINAL-06-firmware/.claude/worktrees/agent-af654573c23937790/tools")
os.environ.setdefault("TS06_OUT", "/tmp/claude-0/-home-user-TERMINAL-06-firmware/c1b2f23b-2f88-537c-b39a-4eee239c41d3/scratchpad/revb/place/x.kicad_pcb")
import mkpcb_drv as D
from PIL import Image, ImageDraw

out = sys.argv[1]
x0, y0, x1, y1 = map(float, sys.argv[2:6])
ppm = float(sys.argv[6]) if len(sys.argv) > 6 else 12
if "display" in sys.argv:
    y0 += D.Y0; y1 += D.Y0
B = D.B
W, H = int((x1 - x0) * ppm), int((y1 - y0) * ppm)
im = Image.new("RGB", (W, H), (22, 26, 32))
d = ImageDraw.Draw(im)
P = lambda x, y: ((x - x0) * ppm, (y - y0) * ppm)
for gx in range(int(x0) - 1, int(x1) + 2):
    if gx % 5 == 0:
        d.line([P(gx, y0), P(gx, y1)], fill=(40, 44, 52))
        d.text(P(gx + 0.1, y0 + 0.1), str(gx), fill=(90, 90, 90))
for gy in range(int(y0) - 1, int(y1) + 2):
    if gy % 5 == 0:
        d.line([P(x0, gy), P(x1, gy)], fill=(40, 44, 52))
        d.text(P(x0 + 0.1, gy + 0.1), f"{gy}/{gy - D.Y0:g}", fill=(90, 90, 90))
for net, layer, a, b, w in B.tracks:
    c = (230, 90, 90) if layer == "F.Cu" else (90, 150, 255)
    d.line([P(*a), P(*b)], fill=c, width=max(1, int(w * ppm)))
for ref, (f, x, y) in B.placed.items():
    c = f.court
    col = (70, 140, 230) if f.back else (80, 200, 120)
    d.rectangle([P(x + c[0], y + c[1]), P(x + c[2], y + c[3])], outline=col)
    d.text(P(x + c[0] + 0.2, y + c[1] + 0.1), ref, fill=col)
for p in B.pads:
    if p.kind == "np_thru_hole":
        continue
    r = max(p.w, p.h) / 2
    hv = B.cls(p.net) == "HV"
    d.ellipse([P(p.x - r, p.y - r), P(p.x + r, p.y + r)], fill=(240, 120, 60) if hv else ((220, 190, 80) if p.net else (120, 110, 90)))
for hx, hy, hd in B.holes:
    d.ellipse([P(hx - hd / 2, hy - hd / 2), P(hx + hd / 2, hy + hd / 2)], outline=(255, 255, 255))
    r = B.hole_ko
    d.ellipse([P(hx - r, hy - r), P(hx + r, hy + r)], outline=(255, 80, 200))
for ko in B.keepouts:
    a, b_, c, e = ko[:4]
    d.rectangle([P(a, b_), P(c, e)], outline=(255, 255, 0))
im.save(out)
print("saved", out, W, H)
