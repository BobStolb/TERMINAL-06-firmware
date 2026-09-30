"""repolish.py STATE.json OUT.json: the polish pass alone, from a run's converged state, as route() runs it;
writes the routed tracks as route() saves them, and says whether they equal tools/mkpcb_drv_routes.json."""
import json, os, sys
WT = "/home/user/TERMINAL-06-firmware/.claude/worktrees/agent-a92d573b002761b70"
sys.path.insert(0, WT + "/tools")
os.environ.setdefault("TS06_OUT", "/tmp/claude-0/-home-user-TERMINAL-06-firmware/c1b2f23b-2f88-537c-b39a-4eee239c41d3/scratchpad/revb2/place/z.kicad_pcb")
state, out = sys.argv[1], sys.argv[2]
sys.argv = [sys.argv[0], "--place"]
import mkpcb_drv as D
import netroute as NR
B = D.B
B.tracks += [(n, ly, tuple(a), tuple(b), w) for n, ly, (a, b), w in json.load(open(state))["tracks"]]
R = NR.NetRouter(B, turn45=6.0)
R.locked = set(D.LOCKED)
R.fixed = set(D.FIXED)
R.dirmul = {ly: [1.0, 1.5, 1.0, 1.5, 1.0, 1.5, 1.0, 1.5] for ly in ("F.Cu", "B.Cu")}
R.polish([n for n in D.route_order() if n not in D.LOCKED], widths=D.WIDTHS, verbose=False)
rows = [[n, ly, [list(a), list(b)], w] for n, ly, a, b, w in B.tracks if (n, ly, a, b, w) not in D.FIXED]
json.dump(rows, open(out, "w"), indent=0)
saved = json.load(open(WT + "/tools/mkpcb_drv_routes.json"))
print("tracks", len(rows), "saved", len(saved), "identical to the saved route:", rows == saved)
dups = len(B.tracks) - len(set(B.tracks))
print("duplicate tracks on the board after polish:", dups)
