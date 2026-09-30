"""conf.py STATE.json [--tools DIR]: where the nets of a run's state still share (exact pairs)."""
import json, os, sys
args = sys.argv[1:]
tools = "/home/user/TERMINAL-06-firmware/.claude/worktrees/agent-a92d573b002761b70/tools"
if "--tools" in args:
    i = args.index("--tools"); tools = args[i + 1]; del args[i:i + 2]
sys.path.insert(0, tools)
os.environ.setdefault("TS06_OUT", "/tmp/claude-0/-home-user-TERMINAL-06-firmware/c1b2f23b-2f88-537c-b39a-4eee239c41d3/scratchpad/revb2/place/x.kicad_pcb")
sys.argv = [sys.argv[0], "--place"]
import mkpcb_drv as D
import netroute as NR
import pcbkit as K
B = D.B
st = json.load(open(args[0]))
print(st["line"])
B.tracks += [(n, ly, tuple(a), tuple(b), w) for n, ly, (a, b), w in st["tracks"]]
R = NR.NetRouter(B, turn45=6.0)
R.fixed = set(D.FIXED)
segs = {}
for ly in ("F.Cu", "B.Cu"):
    S = [t for t in B.tracks if t[1] == ly]
    for i, ti in enumerate(S):
        for tj in S[i + 1:]:
            if ti[0] == tj[0] or (ti in R.fixed and tj in R.fixed):
                continue
            if max(ti[2][0], ti[3][0]) + 2 < min(tj[2][0], tj[3][0]) or max(tj[2][0], tj[3][0]) + 2 < min(ti[2][0], ti[3][0]):
                continue
            if max(ti[2][1], ti[3][1]) + 2 < min(tj[2][1], tj[3][1]) or max(tj[2][1], tj[3][1]) + 2 < min(ti[2][1], ti[3][1]):
                continue
            need = R.need(ti[0], tj[0]) + ti[4] / 2 + tj[4] / 2 - 1e-6
            d = K.dist(([ti[2], ti[3]], 0), ([tj[2], tj[3]], 0))
            if d < need:
                fx = "(hand)" if tj in R.fixed else ""
                fy = "(hand)" if ti in R.fixed else ""
                print(f"  {ly[0]} {ti[0]}{fy} {[round(v, 1) for v in ti[2]]}-{[round(v, 1) for v in ti[3]]}  x  {tj[0]}{fx} {[round(v, 1) for v in tj[2]]}-{[round(v, 1) for v in tj[3]]}  gap {d - ti[4] / 2 - tj[4] / 2:.2f} < {R.need(ti[0], tj[0]):.2f}")
