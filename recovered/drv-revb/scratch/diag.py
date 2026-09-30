"""diag.py ROUNDS OUTDIR: run the negotiated router for a few rounds and show where nets still share."""
import os, sys, json
sys.path.insert(0, "/home/user/TERMINAL-06-firmware/.claude/worktrees/agent-af654573c23937790/tools")
os.environ.setdefault("TS06_OUT", "/tmp/claude-0/-home-user-TERMINAL-06-firmware/c1b2f23b-2f88-537c-b39a-4eee239c41d3/scratchpad/revb/place/x.kicad_pcb")
rounds, out = int(sys.argv[1]), sys.argv[2]
os.makedirs(out, exist_ok=True)
import mkpcb_drv as D
import netroute as NR
from PIL import Image, ImageDraw
B = D.B
R = NR.NetRouter(B, turn45=6.0)
R.locked = set(D.LOCKED)
R.fixed = set(D.FIXED)
R.dirmul = {ly: [1.0, 1.5, 1.0, 1.5, 1.0, 1.5, 1.0, 1.5] for ly in ("F.Cu", "B.Cu")}
N = NR.Negotiator(R, D.route_order(), widths=D.WIDTHS)
N.run(rounds=rounds)
con = N.conflicts()
rows = []
for n, ts in sorted(con.items()):
    for t in ts:
        rows.append([n, t[1], t[2], t[3]])
json.dump(rows, open(os.path.join(out, "conflicts.json"), "w"), indent=0)
json.dump([[n, ly, [list(a), list(b)], w] for n, ly, a, b, w in B.tracks if (n, ly, a, b, w) not in D.FIXED],
          open(os.path.join(out, "routes.json"), "w"), indent=0)
ppm = 7
for layer in ("F.Cu", "B.Cu"):
    im = Image.new("RGB", (int(B.W * ppm), int(B.H * ppm)), (20, 22, 28))
    d = ImageDraw.Draw(im)
    P = lambda x, y: (x * ppm, y * ppm)
    for n, ly, a, b, w in B.tracks:
        if ly == layer:
            c = (200, 70, 70) if B.cls(n) == "HV" else (70, 150, 90)
            d.line([P(*a), P(*b)], fill=c, width=max(1, int(w * ppm)))
    for p in B.pads:
        if p.kind == "np_thru_hole" or not p.on(layer):
            continue
        r = max(p.w, p.h) / 2
        d.ellipse([P(p.x - r, p.y - r), P(p.x + r, p.y + r)], fill=(200, 180, 80))
    for n, ly, a, b in rows:
        if ly == layer:
            d.line([P(*a), P(*b)], fill=(255, 255, 255), width=3)
            d.text(P(*a), n, fill=(255, 255, 0))
    for hx, hy, hd in B.holes:
        d.ellipse([P(hx - 3.8, hy - 3.8), P(hx + 3.8, hy + 3.8)], outline=(255, 80, 200))
    im.save(os.path.join(out, f"diag_{layer[0]}.png"))
print("conflicts:", sorted(con))
