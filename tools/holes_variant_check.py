#!/usr/bin/env python3
"""What the fascia R's opened control holes touch (the holes04 variant, fab/HOLES-VARIANT.md).

    python3 tools/holes_variant_check.py              # print the tables; exit 1 if a criterion fails
    python3 tools/holes_variant_check.py --extra 0.6  # what-if: another opening (the generator's --open-holes MM)

The variant opens every control bushing hole by 0.4 mm in diameter (SW1 rotary 8.8 -> 9.2; SW2..SW5 levers and buttons
8.0 -> 8.4). This script builds, in a scratch directory, the board both ways with tools/mkpcb_fascia_rhythm.py
(`--out FILE [--open-holes]`; nothing under PCB/ is written) and shows:

  1. the default board is the committed board byte for byte, and the variant differs from it by the five pads' size and
     drill, nothing else;
  2. each control footprint carries ONE hole and no anti-rotation tab, key slot or locating hole (so none can collide);
  3. the art checks on the variant: tools/fascia_art.py's (the Plates silk) and tools/fascia_gold.py's (the gold: 6 mm
     from lever and button centres, 9 mm from the dial shaft, and every other rule) run on the variant board, clean;
  4. the gap from each hole's edge, before and after, to: the gold, the white silk art, the footprint's own silk ring,
     the nearest copper (pads and tracks on the back), the neighbouring hole, the board edge and the screw holes.

Criteria (a gap below one FAILs): art edge to hole edge 0.3 (the art's own gold-to-silk spacing); silk ring's inner edge to
hole edge 0.4 (the 0.4 the art keeps from a ring); copper to hole edge 0.25 (KiCad's project rule, fascia_gold.py);
hole wall to hole wall 0.5 and hole edge to board edge 0.5 (tools/dfm_check.py's hole-to-hole limit, rounded up at the edge).
A ring is "grown with the hole" only if it would fail; none does, so none is changed.
"""
import argparse, math, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import sexp as S                    # noqa: E402
import fascia_art as fa             # noqa: E402
import fascia_gold as fg            # noqa: E402

COMMITTED = os.path.join(ROOT, "PCB", "TS06-FASCIA-rhythm", "TS06-FASCIA-rhythm.kicad_pcb")
CONTROLS = ("SW1", "SW2", "SW3", "SW4", "SW5")
BUSHING = {"SW1": 8.62, "SW2": 7.82, "SW3": 7.82, "SW4": 7.82, "SW5": 7.82}   # 3d/*.step, calipered (tools/fit_table.py)
CRIT = dict(art=0.3, ring=0.4, copper=0.25, h2h=0.5, edge=0.5)


def generate(out, extra=None):
    cmd = [sys.executable, os.path.join(HERE, "mkpcb_fascia_rhythm.py"), "--out", out]
    if extra is not None:
        cmd += ["--open-holes", str(extra)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("tools/mkpcb_fascia_rhythm.py failed:\n" + r.stdout + r.stderr)


def place(at, x, y):
    a = math.radians(float(at[3])) if len(at) > 3 else 0.0
    return (float(at[1]) + x * math.cos(a) + y * math.sin(a), float(at[2]) - x * math.sin(a) + y * math.cos(a))


def read(path):
    """Everything the gaps need, from a board file: controls (centre, hole d, ring r and width, own pads), the other pads as
    bounding circles, the B.Cu / F.Cu tracks, the screw holes, the board size."""
    t = S.parse(open(path, encoding="utf8").read())
    ctrl, pads, screws = {}, [], []
    for fp in S.find_all(t, "footprint"):
        ref = [S.unq(p[2]) for p in S.find_all(fp, "property") if S.unq(p[1]) == "Reference"][0]
        at = S.find(fp, "at")
        c = (float(at[1]), float(at[2]))
        own = []
        for p in S.find_all(fp, "pad"):
            pa, sz = S.find(p, "at"), S.find(p, "size")
            ctr = place(at, float(pa[1]), float(pa[2]))
            rad = math.hypot(float(sz[1]), float(sz[2])) / 2          # a circle round the pad: safe side
            dr = S.find(p, "drill")
            own.append((S.unq(p[1]), p[2], ctr, rad, float(dr[-1]) if dr else 0.0))
            if ref not in CONTROLS:
                pads.append((ref, S.unq(p[1]), ctr, rad))
        if ref in CONTROLS:
            ring = None
            for ci in S.find_all(fp, "fp_circle"):
                if S.unq(S.find(ci, "layer")[1]) == "F.SilkS":
                    ce, en, st = S.find(ci, "center"), S.find(ci, "end"), S.find(ci, "stroke")
                    ring = (math.hypot(float(en[1]) - float(ce[1]), float(en[2]) - float(ce[2])), float(S.find(st, "width")[1]))
            hole = [o for o in own if o[1] == "np_thru_hole"]
            ctrl[ref] = dict(c=c, own=own, holes=hole, ring=ring, d=hole[0][4] if len(hole) == 1 else None,
                             fp=S.unq(S.find(fp, "descr")[1]) if S.find(fp, "descr") else "")
        elif "MountingHole" in S.unq(fp[1]):
            screws.append((c, float([o for o in own][0][4]) / 2))
    segs = []
    for sg in S.find_all(t, "segment"):
        a, b = S.find(sg, "start"), S.find(sg, "end")
        segs.append(((float(a[1]), float(a[2])), (float(b[1]), float(b[2])), float(S.find(sg, "width")[1])))
    return dict(ctrl=ctrl, pads=pads, segs=segs, screws=screws)


def gaps(B, G, A, W, H):
    """{ref: {what: gap from the hole's edge}} for one board."""
    out = {}
    refs = list(B["ctrl"])
    for ref in refs:
        k = B["ctrl"][ref]
        c, r = k["c"], k["d"] / 2
        g = {}
        gold = [x for x in A.items if x["ink"] == "gold"]
        silk = [x for x in A.items if x["ink"] == "silk"]
        g["gold"] = min(fa.dist_pt(x, c) for x in gold) - r
        g["silk art"] = min(fa.dist_pt(x, c) for x in silk) - r
        g["silk ring"] = (k["ring"][0] - k["ring"][1] / 2 - r) if k["ring"] else None
        cu = [math.hypot(p[2][0] - c[0], p[2][1] - c[1]) - p[3] - r for p in B["pads"]]
        cu += [fa.pseg(c, a, b) - w / 2 - r for a, b, w in B["segs"]]
        cu += [math.hypot(o[2][0] - c[0], o[2][1] - c[1]) - o[3] - r for o in k["own"] if o[1] != "np_thru_hole"]
        g["copper"] = min(cu)
        g["next hole"] = min(math.hypot(B["ctrl"][q]["c"][0] - c[0], B["ctrl"][q]["c"][1] - c[1]) - B["ctrl"][q]["d"] / 2 - r
                             for q in refs if q != ref)
        g["screw hole"] = min(math.hypot(sc[0] - c[0], sc[1] - c[1]) - sr - r for sc, sr in B["screws"])
        g["board edge"] = min(c[0], W - c[0], c[1], H - c[1]) - r
        out[ref] = g
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--extra", type=float, default=0.4, help="the opening in mm (default 0.4)")
    a = ap.parse_args()
    bad = []
    tmp = tempfile.mkdtemp(prefix="holes_variant.")
    try:
        d0, d1 = os.path.join(tmp, "default.kicad_pcb"), os.path.join(tmp, "open.kicad_pcb")
        generate(d0)
        generate(d1, a.extra)
        t0, t1 = open(d0, "rb").read(), open(d1, "rb").read()
        same = t0 == open(COMMITTED, "rb").read()
        print("1. The boards")
        print("   default board from the generator == the committed board, byte for byte: %s" % ("YES" if same else "NO"))
        if not same:
            bad.append("the generator's default board is not the committed board")
        l0, l1 = t0.decode().split("\n"), t1.decode().split("\n")
        ch = [(i, x, y) for i, (x, y) in enumerate(zip(l0, l1)) if x != y]
        ok = len(l0) == len(l1) and len(ch) == 10 and all(("(size" in x and "(size" in y) or ("(drill" in x and "(drill" in y) for _, x, y in ch)
        print("   variant vs default: %d lines differ, %s" % (len(ch), "all of them a control pad's (size D D) or (drill D): %s" % ", ".join(
            sorted({"%s -> %s" % (x.split()[-1].strip(")"), y.split()[-1].strip(")")) for _, x, y in ch})) if ok else "NOT only the pads' size and drill"))
        if not ok:
            bad.append("the variant differs from the default by more than the five pads")
        B0, B1 = read(d0), read(d1)
        print()
        print("2. Anything else a control footprint carries near its hole (anti-rotation tab, key slot, locating hole)")
        for ref in CONTROLS:
            k = B1["ctrl"][ref]
            nonpad = [o for o in k["own"] if o[4] > 0 and o[1] != "np_thru_hole"]
            words = [w for w in ("anti-rotation", "anti rotation", "key slot", "keyway", "locating", "tab ") if w in k["fp"].lower()]
            print("   %s at (%.3f, %.3f): %d hole(s) (the bushing's, D%.1f), %d smd landing pad(s), other drilled pads %d, footprint text names %s" % (
                ref, k["c"][0], k["c"][1], len(k["holes"]), k["d"], len(k["own"]) - len(k["holes"]), len(nonpad), ", ".join(words) or "no tab or locating hole"))
            if len(k["holes"]) != 1 or nonpad or words:
                bad.append("%s carries more than its one bushing hole" % ref)
        print("   (a real part's anti-rotation tab or flat is not in these footprints or in the STEP files' hole data: the dry fit, G14, closes it)")
        print()
        print("3. The art checks, run on the variant board (tools/fascia_art.py plates, tools/fascia_gold.py divider)")
        fa.BASES["R"] = d1
        _, _, probs_art, n_art = fa.build("plates", "R")
        A, G, probs_gold, st, n_gold, _ = fg.build("divider", "R")
        print("   fascia_art plates on R: %s (%d other items identical to the base)" % ("checks clean" if not probs_art else "%d problems" % len(probs_art), n_art))
        print("   fascia_gold divider on R: %s (%d other items identical to the base)" % ("checks clean" if not probs_gold else "%d problems" % len(probs_gold), n_gold))
        print("      margins (mm): controls +%.2f beyond 6.0 from a lever / button centre, dial +%.2f beyond 9.0 from the shaft; gold-silk %.2f (need 0.30), edge %.2f (1.4)" % (
            st["ctrl"], st["dial"], st["gold_silk"], st["edge"]))
        for p in probs_art + probs_gold:
            print("      " + p)
            bad.append(p)
        # the art items are the same on the default board: the keep-outs are measured from the centres, which the holes do not move
        fa.BASES["R"] = d0
        A0 = fg.build("divider", "R")[0]
        same_art = [x for x in A0.items] == [x for x in A.items]
        print("   the art (every gold and silk item) is identical on the default and the variant board: %s" % ("YES" if same_art else "NO"))
        if not same_art:
            bad.append("the art differs between the two boards")
        print()
        print("4. Gaps from the hole's edge (mm), default -> variant; the bushing's margin is (hole - bushing) / 2 a side")
        gA = gaps(B0, G, A0, G["W"], G["H"])
        gB = gaps(B1, G, A, G["W"], G["H"])
        names = [("gold", "art"), ("silk art", "art"), ("silk ring", "ring"), ("copper", "copper"), ("next hole", "h2h"), ("screw hole", "h2h"), ("board edge", "edge")]
        print()
        print("| control | hole D | bushing D | bushing margin a side | " + " | ".join(n for n, _ in names) + " |")
        print("|---|---|---|---|" + "---|" * len(names))
        for ref in CONTROLS:
            k0, k1 = B0["ctrl"][ref], B1["ctrl"][ref]
            cells = []
            for n, cr in names:
                v0, v1 = gA[ref][n], gB[ref][n]
                if v1 is None:
                    cells.append("-")
                    continue
                ok_ = v1 >= CRIT[cr] - 1e-9
                if not ok_:
                    bad.append("%s %s: %.3f mm from the hole's edge, need %.2f" % (ref, n, v1, CRIT[cr]))
                cells.append("%.2f -> %.2f%s" % (v0, v1, "" if ok_ else " **FAIL**"))
            print("| %s | %.1f -> %.1f | %.2f | +%.2f -> +%.2f | %s |" % (ref, k0["d"], k1["d"], BUSHING[ref],
                                                                       (k0["d"] - BUSHING[ref]) / 2, (k1["d"] - BUSHING[ref]) / 2, " | ".join(cells)))
        print()
        print("   criteria (gap from the hole's edge): art %.2f, silk ring %.2f, copper %.2f, hole to hole %.2f, board edge %.2f" % (
            CRIT["art"], CRIT["ring"], CRIT["copper"], CRIT["h2h"], CRIT["edge"]))
        print("   silk ring radii (centre-line, unchanged): %s; none had to grow" % ", ".join(
            "%s %.1f" % (r, B1["ctrl"][r]["ring"][0]) for r in CONTROLS))
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    print()
    if bad:
        print("HOLES VARIANT CHECK: FAIL")
        for b in bad:
            print("   " + b)
        return 1
    print("HOLES VARIANT CHECK: PASS (nothing collides; no silk ring changed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
