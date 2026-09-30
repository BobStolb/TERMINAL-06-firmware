"""view.py STATE.json OUT_PREFIX [x0 y0 x1 y1 ppm] [--tools DIR]: a run's routed copper from its state
file, both faces side by side, the nets still sharing drawn bright, over the placement (DRV frame)."""
import json, os, sys
args = [a for a in sys.argv[1:]]
tools = "/home/user/TERMINAL-06-firmware/.claude/worktrees/agent-a92d573b002761b70/tools"
if "--tools" in args:
    i = args.index("--tools"); tools = args[i + 1]; del args[i:i + 2]
sys.path.insert(0, tools)
os.environ.setdefault("TS06_OUT", "/tmp/claude-0/-home-user-TERMINAL-06-firmware/c1b2f23b-2f88-537c-b39a-4eee239c41d3/scratchpad/revb2/place/x.kicad_pcb")
sys.argv = [sys.argv[0], "--place"]
import mkpcb_drv as D
from PIL import Image, ImageDraw
st = json.load(open(args[0]))
out = args[1]
x0, y0, x1, y1, ppm = (float(v) for v in args[2:7]) if len(args) >= 7 else (0, 0, D.W, D.H, 7)
B = D.B
share = set(st["sharing"])
print(st["line"], "| sharing:", " ".join(st["sharing"]), "| unrouted:", " ".join(st["unrouted"]))
tracks = [(n, ly, tuple(a), tuple(b), w) for n, ly, (a, b), w in st["tracks"]] + [t for t in B.tracks]
Wd, Hd = int((x1 - x0) * ppm), int((y1 - y0) * ppm)
im = Image.new("RGB", (Wd * 2 + 10, Hd), (18, 20, 26))
for k, layer in enumerate(("F.Cu", "B.Cu")):
    ox = k * (Wd + 10)
    d = ImageDraw.Draw(im)
    P = lambda x, y: (ox + (x - x0) * ppm, (y - y0) * ppm)
    for p in B.pads:
        if p.kind == "np_thru_hole" or not p.on(layer):
            continue
        r = max(p.w, p.h) / 2
        hv = B.cls(p.net) == "HV"
        d.ellipse([P(p.x - r, p.y - r), P(p.x + r, p.y + r)], fill=(150, 80, 50) if hv else (130, 120, 70))
    for n, ly, a, b, w in tracks:
        if ly != layer:
            continue
        c = (255, 255, 255) if n in share else ((200, 70, 70) if B.cls(n) == "HV" else (70, 150, 90))
        d.line([P(*a), P(*b)], fill=c, width=max(1, int(w * ppm)))
    for p in B.pads:
        if p.net and x0 <= p.x <= x1 and y0 <= p.y <= y1 and p.on(layer):
            d.text(P(p.x + 0.5, p.y + 0.3), p.net[:6], fill=(170, 170, 170))
    d.text((ox + 4, 4), layer, fill=(255, 255, 0))
im.save(out)
print("saved", out)
