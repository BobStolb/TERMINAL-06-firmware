#!/usr/bin/env python3
"""TS06-DRV-search: the driver board with its parts placed by an optimiser (tools/placesearch.py),
not by hand, and routed with no hand-laid copper at all.

    python3 tools/mkpcb_drv_search.py --cand PCB/TS06-DRV-search/cands/cand_3.json --route
    python3 tools/mkpcb_drv_search.py --cand ... --place          # placement only: placement.png
    python3 tools/mkpcb_drv_search.py                             # the chosen candidate, saved routes

THE QUESTION IT ANSWERS. tools/mkpcb_drv.py reached zero vias with a lot of copper laid by hand -
a bus corridor beside the Nano, a fan-out below it, a column of standing resistors where lines
change face, port A up the left edge, the LED ribbon. Is that intricacy the price of the circuit, or
of that particular placement? Here the placement is whatever minimised placesearch.py's cost (MST
length plus a heavy price on MST crossings that cannot be put on opposite faces), and the router
gets every net with nothing locked or pre-laid, on the same settings as the baseline:
NetRouter(turn45=6.0), dirmul [1.0, 1.5] * 4 on both faces, Negotiator(rounds=60), polish().

WHAT IS THE SAME AS THE BASELINE: the netlist (tools/ts06pair.py), the strips and the display's
standoffs (check_mate() below is the baseline's, copied), the frame (Y0 = 26 mm above the display),
the outline (176 x 100), the net classes, the track widths. WHAT A CANDIDATE MAY CHANGE: every other
part's pose; the corner holes H5..H8 go to the free spot nearest each corner; the firmware-only
remaps the candidate carries (which Nano pin drives which anode channel, which RN1 element / port-B
bit lights which LED, which port-A nibble feeds which ИН-15 decoder), applied to the netlist in
memory here; and every opto LED resistor stands (R21/R22 were lying in the baseline).

Output: PCB/TS06-DRV-search/TS06-DRV-search.kicad_pcb (+ .kicad_pro, copper.png, scorecard.json);
the routes are saved beside the candidate (<cand>.routes.json) so the board regenerates exactly.
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbkit as K
import ts06pair as P
import placesearch as PS

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
NAME = "TS06-DRV-search"
A = sys.argv[1:]
CAND = A[A.index("--cand") + 1] if "--cand" in A else os.path.join(ROOT, "PCB", NAME, "cand.json")
TAG = A[A.index("--tag") + 1] if "--tag" in A else ""
OUTDIR = os.path.join(ROOT, "PCB", NAME) if not TAG else os.path.join(ROOT, "PCB", NAME, TAG)
OUT = os.path.join(OUTDIR, NAME + ".kicad_pcb")
ROUTES = CAND.replace(".json", ".routes.json") if not os.environ.get("ORDER") else CAND.replace(".json", f".{os.environ['ORDER']}.routes.json")
PLACE_ONLY = "--place" in A

W, H = 176.0, 100.0
DW, Y0 = 176.0, 26.0
CAN = json.load(open(CAND))
REMAP = CAN["remap"]

# ---- the remaps, applied to the netlist in memory (tools/ts06pair.py carries the chosen one)
PT = P.parts(P.DRV)
for ref in PT:
    part = PT[ref]
    for pin in list(part.pins):
        part.pins[pin] = PS.pin_net(ref, pin, REMAP) if ref in PS.PT else part.pins[pin]
for ref, fp in PS.FP_OVERRIDE.items():
    PT[ref].fp = fp
assert not P.check(), P.check()

CLASSES = [("HV", 0.6, 0.4, P.HV_PATTERNS),
           ("CATH", 0.25, 0.25, P.CATH_PATTERNS),
           ("PWR", 0.25, 0.5, ["+5V", "+12V", "VIN_J", "VIN_F", "GATE_D", "GATE"])]
B = K.Board(NAME, W, H, PT, CLASSES, default=("Default", 0.2, 0.25))

# ---- the fixed things: strips on the back face, the display's standoffs
for ref, fp, x, y, rot, back in PS.fixed_parts():
    B.place(ref, fp, x, y, rot, back)
for i, (hx, hy) in enumerate(PS.fixed_holes()):
    B.place(f"H{i + 1}", "TS06_MountingHole_M3", hx, hy)
    B.holes.append((hx, hy, 3.2))


def snap(v, g=0.127):
    return round(round(v / g) * g, 4)


# ---- the candidate's parts, snapped to a 0.127 mm grid (block by block, so a block stays rigid)
bpos = {}
for b, (x, y, r, m) in CAN["poses"].items():
    bpos[b] = (snap(x) - x, snap(y) - y)
blk_of = {ref: b for b, ps in PS.BLOCKS for ref, *_ in ps}
for ref, fp, x, y, rot, back in CAN["parts"]:
    dx, dy = bpos[blk_of[ref]]
    B.place(ref, fp, x + dx, y + dy, rot, back)

# ---- the corner holes H5..H8: the free spot nearest each corner


def free_spot(cx, cy):
    best = None
    courts = [B.court(r) for r in B.placed]
    for i in range(0, 60):
        for j in range(0, 60):
            x = cx + (i * 0.5 if cx < W / 2 else -i * 0.5)
            y = cy + (j * 0.5 if cy < H / 2 else -j * 0.5)
            box = (x - 3.95, y - 3.95, x + 3.95, y + 3.95)
            if any(box[0] < c[2] and c[0] < box[2] and box[1] < c[3] and c[1] < box[3] for c in courts):
                continue
            if any(abs(p.x - x) < 4.5 and abs(p.y - y) < 4.5 for p in B.pads):
                continue
            d = math.hypot(x - cx, y - cy)
            if best is None or d < best[0]:
                best = (d, x, y)
    return best


for i, (cx, cy) in enumerate(PS.CORNER_HOLES):
    s = free_spot(cx, cy)
    if s:
        B.place(f"H{5 + i}", "TS06_MountingHole_M3", s[1], s[2])
        B.holes.append((s[1], s[2], 3.2))
    else:
        print(f"  no room for a corner hole near ({cx}, {cy})")


# ======================================================================== references on the silk (the baseline's placer, copied)
def place_refs(board, skip=("H",)):
    """Every reference on the silkscreen of its part's face, for the person with the BOM and a
    soldering iron: on the part's body where it fits (between a resistor's pads, inside a
    socket's rows), else just outside its courtyard, never over a pad or another reference."""
    boxes = []                                  # placed text boxes (x0, y0, x1, y1, back)
    pads = [(p.x - max(p.w, p.h) / 2, p.y - max(p.w, p.h) / 2, p.x + max(p.w, p.h) / 2,
             p.y + max(p.w, p.h) / 2) for p in board.pads]
    holes = [(hx - hd / 2, hy - hd / 2, hx + hd / 2, hy + hd / 2) for hx, hy, hd in board.holes]

    def free(bx, back):
        m = 0.2
        if bx[0] < 0.6 or bx[1] < 0.6 or bx[2] > board.W - 0.6 or bx[3] > board.H - 0.6:
            return False
        for q in pads + holes:
            if bx[0] - m < q[2] and q[0] < bx[2] + m and bx[1] - m < q[3] and q[1] < bx[3] + m:
                return False
        for q in boxes:
            if q[4] == back and bx[0] - m < q[2] and q[0] < bx[2] + m and bx[1] - m < q[3] and q[1] < bx[3] + m:
                return False
        return True

    for ref in sorted(board.placed, key=K._refkey):
        if ref.startswith(skip) and ref[len(skip[0]):].isdigit():
            continue
        f, x, y = board.placed[ref]
        c = board.court(ref)
        cx, cy = (c[0] + c[2]) / 2, (c[1] + c[3]) / 2
        wide = (c[2] - c[0]) >= (c[3] - c[1])
        cands = []
        for size in (1.0, 0.8):
            tw, th = len(ref) * 0.8 * size + 0.1, size
            for rot in ((0, 90) if wide else (90, 0)):
                bw, bh = (tw, th) if rot == 0 else (th, tw)
                cands.append((cx, cy, rot, size, bw, bh))
                cands += [(cx, c[1] - bh / 2 - 0.25, rot, size, bw, bh), (cx, c[3] + bh / 2 + 0.25, rot, size, bw, bh),
                          (c[0] - bw / 2 - 0.25, cy, rot, size, bw, bh), (c[2] + bw / 2 + 0.25, cy, rot, size, bw, bh)]
        for tx, ty, rot, size, bw, bh in cands:
            bx = (tx - bw / 2, ty - bh / 2, tx + bw / 2, ty + bh / 2)
            if free(bx, f.back):
                boxes.append(bx + (f.back,))
                board.ref_at[ref] = (round(tx - x, 3), round(ty - y, 3), rot, size)
                break
        else:
            tx, ty, rot, size, bw, bh = cands[0]
            boxes.append((tx - bw / 2, ty - bh / 2, tx + bw / 2, ty + bh / 2, f.back))
            board.ref_at[ref] = (round(tx - x, 3), round(ty - y, 3), rot, 0.8)
            print(f"  reference {ref}: no clear spot, left on the body")


# ======================================================================== the two boards mate
def check_mate():
    """Every XS pin here must sit exactly behind its XP pin on TS06-DISP (x mirrored, y offset by Y0),
    carry the same signal, and every display standoff must have its hole here."""
    import mkpcb_disp as DISP
    bad = []
    for k in P.HEADERS:
        n = len(P.HEADERS[k])
        for i in range(1, n + 1):
            xp, xs = DISP.B.pad(f"XP{k}", i), B.pad(f"XS{k}", i)
            if abs((DW - xp.x) - xs.x) > 1e-3 or abs(xp.y + Y0 - xs.y) > 1e-3:
                bad.append(f"XS{k}.{i} at ({xs.x}, {xs.y}) but XP{k}.{i} lands at ({DW - xp.x}, {xp.y + Y0})")
            if xp.net != xs.net:
                bad.append(f"XS{k}.{i} carries {xs.net} but XP{k}.{i} carries {xp.net}")
    mine = {(round(x, 3), round(y, 3)) for x, y, d in B.holes}
    for x, y, d in DISP.B.holes:
        if (round(DW - x, 3), round(y + Y0, 3)) not in mine:
            bad.append(f"display standoff at ({x}, {y}) has no hole here at ({DW - x}, {y + Y0})")
    return bad


def overlaps():
    out = []
    refs = list(B.placed)
    for i, a in enumerate(refs):
        ca = B.court(a)
        for b in refs[i + 1:]:
            cb = B.court(b)
            if ca[0] < cb[2] - 0.05 and cb[0] < ca[2] - 0.05 and ca[1] < cb[3] - 0.05 and cb[1] < ca[3] - 0.05:
                if B.placed[a][0].back == B.placed[b][0].back:
                    out.append(f"courtyards {a} / {b}")
    for i, p in enumerate(B.pads):
        for q in B.pads[i + 1:]:
            if p.ref != q.ref and abs(p.x - q.x) < 1.6 and abs(p.y - q.y) < 1.6:
                out.append(f"pads {p.ref}.{p.name} / {q.ref}.{q.name}")
    return out


# ======================================================================== routing
WIDTHS = {"+12V": 0.8, "VIN_J": 0.8, "VIN_F": 0.8, "SW": 0.8, "+5V": 0.4, "GND": 0.4}


def route_order():
    """The baseline's order: the constrained signal buses first, then 185 V, rails, the rest, GND last."""
    nets = sorted({p.net for p in B.pads if p.net})
    hv = [n for n in nets if B.cls(n) == "HV"]
    order = ([f"A{i}" for i in range(4)] + [f"XA{i}" for i in range(8)] + [f"XB{i}" for i in range(8)] +
             [f"BL_A{i}" for i in range(1, 9)] + ["SDA", "SCL", "A6", "A7"] + [f"D{i}" for i in range(2, 14)] +
             ["SW", "HV185"] + [n for n in hv if n not in ("SW", "HV185")] +
             ["+12V", "VIN_J", "VIN_F", "GATE_D", "GATE", "+5V"])
    order += [n for n in nets if n not in order and n != "GND"]
    return [n for n in order if n in nets] + ["GND"]


def route():
    import netroute as NR
    R = NR.NetRouter(B, turn45=6.0)
    R.dirmul = {ly: [1.0, 1.5] * 4 for ly in ("F.Cu", "B.Cu")}
    order = route_order()
    if os.environ.get("ORDER") == "dec":     # variant: the decoder fans (the structural hot spot) first
        dec = [n for n in order if B.cls(n) == "CATH"]
        order = dec + [n for n in order if n not in dec]
    N = NR.Negotiator(R, order, widths=WIDTHS)
    conflicts = N.conflicts

    def checkpoint():                        # conflicts() runs once a round: save the copper each time,
        c = conflicts()                      # so a recycled container loses at most one round
        with open(ROUTES + ".partial", "w") as fh:
            json.dump([[n, ly, [list(a), list(b)], w] for n, ly, a, b, w in B.tracks], fh, indent=0)
        return c
    N.conflicts = checkpoint
    failed = N.run(rounds=int(os.environ.get("ROUNDS", 60)))
    if not failed:
        R.polish(route_order(), widths=WIDTHS, verbose=True)
    with open(ROUTES, "w") as fh:
        json.dump([[n, ly, [list(a), list(b)], w] for n, ly, a, b, w in B.tracks], fh, indent=0)
    return failed


def repair():
    """For a negotiation that stalls with a few nets still sharing: take up only those nets and
    route them again one at a time, everything else fixed as a hard obstacle, trying the orders
    until one leaves nothing shared; then polish. Returns the nets still sharing."""
    import itertools
    import netroute as NR
    R = NR.NetRouter(B, turn45=6.0)
    R.dirmul = {ly: [1.0, 1.5] * 4 for ly in ("F.Cu", "B.Cu")}
    N = NR.Negotiator(R, route_order(), widths=WIDTHS)
    stuck = sorted(N.conflicts())
    print("repair: sharing", stuck, flush=True)
    keep = [t for t in B.tracks if t[0] not in stuck]
    for k, order in enumerate(itertools.permutations(stuck)):
        if k >= 48:
            break
        B.tracks[:] = keep
        left = []
        for n in order:
            rest, _ = R.route(n, NR.LAYERS, WIDTHS.get(n))
            left += [n] if rest else []
        con = N.conflicts()
        print(f"  order {order}: unrouted {left}, sharing {sorted(con)}", flush=True)
        if not left and not con:
            R.polish(route_order(), widths=WIDTHS, verbose=False)
            break
    return sorted(set(N.conflicts()) | {n for n in route_order() if len(R.pieces(n)) > 1})


def load_routes():
    with open(ROUTES) as fh:
        for n, ly, (a, b), w in json.load(fh):
            B.tracks.append((n, ly, tuple(a), tuple(b), w))


# ======================================================================== the scorecard
def scorecard(check_bad, failed):
    segs = B.tracks
    L = [math.hypot(b[0] - a[0], b[1] - a[1]) for _, _, a, b, _ in segs]
    axis = sum(l for l, (_, _, a, b, _) in zip(L, segs) if abs(a[0] - b[0]) < 1e-3 or abs(a[1] - b[1]) < 1e-3)
    dips = [r for r in B.placed if "DIP" in B.placed[r][0].name]
    parts = [r for r in B.placed if not r.startswith("H")]
    ys = [B.court(r) for r in parts]
    usb = B.court("U1")
    jack = B.court("XS1")
    return dict(
        converged=not failed and not [b for b in check_bad if "stub" not in b],
        nets_failed=failed, check_problems=len(check_bad), vias=0,
        track_mm=round(sum(L), 1), segments=len(segs), axis_fraction=round(axis / max(sum(L), 1e-9), 3),
        hand_laid_segments=0,
        dip_pin1_orientations=len({B.placed[r][0].rot for r in dips}), dips=len(dips),
        y_used=[round(min(c[1] for c in ys), 1), round(max(c[3] for c in ys), 1)],
        x_used=[round(min(c[0] for c in ys), 1), round(max(c[2] for c in ys), 1)],
        usb_court=[round(v, 1) for v in usb], jack_court=[round(v, 1) for v in jack],
        c7_at=list(B.P("C7", 1)), nano_at=list(B.P("U1", 1)),
        remap=REMAP, cand=os.path.relpath(CAND, ROOT))


if __name__ == "__main__":
    missing = sorted(set(PT) - set(B.placed), key=K._refkey)
    assert not missing, "not placed: " + " ".join(missing)
    os.makedirs(OUTDIR, exist_ok=True)
    ov = overlaps()
    for o in ov:
        print("  [PLACE]", o)
    if PLACE_ONLY:
        K.plot_placement(B, os.path.join(OUTDIR, "placement.png"), ppm=7)
        sys.exit(0)
    failed = []
    if "--repair" in A:                      # the copper saved per round, then the stuck nets again
        with open(ROUTES + ".partial" if not os.path.exists(ROUTES) or "--partial" in A else ROUTES) as fh:
            for n, ly, (a, b), w in json.load(fh):
                B.tracks.append((n, ly, tuple(a), tuple(b), w))
        failed = repair()
        print("after repair:", " ".join(failed) if failed else "none", flush=True)
        with open(ROUTES, "w") as fh:
            json.dump([[n, ly, [list(a), list(b)], w] for n, ly, a, b, w in B.tracks], fh, indent=0)
    elif "--route" in A or not os.path.exists(ROUTES):
        failed = route()
        print("unrouted/sharing:", " ".join(failed) if failed else "none", flush=True)
    else:
        load_routes()
    B.zone("GND", "F.Cu", clearance=0.5, min_th=0.3, gap=0.5, bridge=0.5)
    B.zone("GND", "B.Cu", clearance=0.5, min_th=0.3, gap=0.5, bridge=0.5)
    B.hide_refs = True
    place_refs(B)
    B.text("TS06-DRV-search", 88.0, 97.5, "F.SilkS", 1.0)
    bad = B.check()
    print(f"check: {len(bad)} problem(s)")
    mate = check_mate()
    print("mate:", "every strip pin and standoff lines up" if not mate else "")
    for m in mate:
        print("  [MATE]", m)
    n = B.write(OUT, title=NAME, comment="TERMINAL-06 driver board, optimiser-placed")
    B.write_project(OUT.replace(".kicad_pcb", ".kicad_pro"))
    B.write_library()
    sc = scorecard(bad, failed)
    sc["mate_problems"] = len(mate)
    sc["placement_problems"] = ov
    with open(os.path.join(OUTDIR, "scorecard.json"), "w") as fh:
        json.dump(sc, fh, indent=1)
    print(json.dumps(sc))
    print(f"wrote {os.path.relpath(OUT, ROOT)}: {len(B.placed)} parts, {n} nets, {len(B.tracks)} segments, 0 vias")
    B.plot(os.path.join(OUTDIR, "copper.png"), ppm=8, color=lambda n: ((255, 90, 90) if B.cls(n) == "HV" else (87, 217, 121)))
