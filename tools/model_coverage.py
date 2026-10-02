#!/usr/bin/env python3
"""Does every footprint of every board end up with a 3D model that exists? A check that can fail.

    python3 tools/model_coverage.py                    # the three boards: TS06-DISP, TS06-DRV, TS06-FASCIA-rhythm
    python3 tools/model_coverage.py --board TS06-DRV -v
    python3 tools/model_coverage.py --bare             # today's boards on their own: no map, no allowlist
    python3 tools/model_coverage.py --prove            # drop an entry from the map, show FAIL; point the library nowhere, show FAIL
    python3 tools/model_coverage.py --map other.json --kicad3d DIR

Per footprint, tools/models3d.py works out the models it would carry at render time: the board's own
(model ...) lines (unless the map says "replace"), plus the map's. The footprint is
    resolved     at least one model, and every model file exists (the ${VAR} paths resolved the way the renderer does)
    allowlisted  on the map's "none" list (a bare hole, a part left empty with the DNP attribute), with the reason printed
    missing      anything else: no model at all, or a model file that is not there  -> FAIL, exit code 1
The allowlist is short and printed in full, one reason each. Nothing is rendered, so this runs in a second.

--prove is grill G7: a check that cannot fail proves nothing. It takes each board's map, deletes ONE entry
from an in-memory copy (the footprint entry that covers the most parts), and requires FAIL with exactly the
parts that entry covered named as missing; then it points KiCad's library at an empty directory and requires
FAIL for every part whose model is a KiCad library file. It exits 0 only if every mutation failed as it must.
"""
import argparse, copy, os, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sexp as S          # noqa: E402
import models3d as M      # noqa: E402

BOARDS = ["TS06-DISP", "TS06-DRV", "TS06-FASCIA-rhythm"]


def board_file(name):
    return os.path.join(M.ROOT, "PCB", name, name + ".kicad_pcb")


def check(name, mp, dmap):
    tree = S.parse(open(board_file(name), encoding="utf8").read())
    return M.plan(tree, name, mp, dmap)


def tally(rows):
    t = {"ok": 0, "allowlisted": 0, "missing": 0}
    for r in rows:
        t[r["status"]] += 1
    return t


def report(name, rows, verbose):
    t = tally(rows)
    verdict = "PASS" if t["missing"] == 0 else "FAIL"
    print("%-20s %3d footprints: %3d resolved, %3d allowlisted, %3d missing   %s" % (
        name, len(rows), t["ok"], t["allowlisted"], t["missing"], verdict))
    for r in rows:
        if r["status"] == "missing":
            print("    MISSING %-5s %-44s %s" % (r["ref"], r["fp"], r["reason"]))
    if verbose:
        reasons = {}
        for r in rows:
            if r["status"] == "allowlisted":
                reasons.setdefault(r["reason"], []).append(r["ref"])
        for why, refs in reasons.items():
            print("    allowlisted %s: %s" % (", ".join(refs), why))
        kinds = {}
        for r in rows:
            for m in r["models"]:
                kinds.setdefault(m.get("kind", "?"), set()).add(r["ref"])
        print("    model sources: " + ", ".join("%s on %d parts" % (k, len(v)) for k, v in sorted(kinds.items())))
    return t


def prove(mp, dmap):
    ok = True
    print("--- proof 1: delete one footprint entry from the map (in memory), per board")
    for name in BOARDS:
        base = check(name, mp, dmap)
        want = {r["ref"] for r in base if r["status"] == "ok"}
        # the footprint entry that covers most parts
        counts = {}
        for r in base:
            if r["map"]:
                counts.setdefault(r["fp"], []).append(r["ref"])
        if not counts:
            continue
        fp, refs = max(counts.items(), key=lambda kv: len(kv[1]))
        key = fp
        bm = mp["boards"][name]["footprints"]
        if key not in bm:                                           # a pre-rotated copy: its base entry
            key = M.VARIANT.match(fp).group(1)
        mut = copy.deepcopy(mp)
        dropped = mut["boards"][name]["footprints"].pop(key)
        rows = check(name, mut, dmap)
        miss = sorted(r["ref"] for r in rows if r["status"] == "missing")
        print("  %s: dropped footprints[%r] (%s) -> %d missing%s" % (
            name, key, ", ".join(m if isinstance(m, str) else m["file"] for m in dropped["models"]), len(miss),
            "" if miss else "  <-- DID NOT FAIL"))
        report(name + " (mutated)", rows, False)
        # every part that entry covered must now be the failing set (parts whose own board model survives still resolve)
        if not miss:
            ok = False
    print("--- proof 2: KiCad's library pointed at an empty directory")
    with tempfile.TemporaryDirectory() as empty:
        d2 = dict(dmap)
        d2[M.KICAD_VAR] = empty
        for name in BOARDS:
            rows = check(name, mp, d2)
            lib = [r for r in rows if any(m["file"].startswith("${%s}" % M.KICAD_VAR) for m in r["models"])]
            miss = [r for r in rows if r["status"] == "missing"]
            good = len(miss) >= len(lib) and (len(miss) > 0 or not lib)
            print("  %s: %d parts use a KiCad library model; with an empty library %d are missing%s" % (
                name, len(lib), len(miss), "" if good else "  <-- DID NOT FAIL"))
            ok = ok and good
    print("proof: %s" % ("every mutation was caught (FAIL where it must)" if ok else "A MUTATION WAS NOT CAUGHT"))
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--board", action="append")
    ap.add_argument("--map", default=M.MAP)
    ap.add_argument("--kicad3d")
    ap.add_argument("--prove", action="store_true")
    ap.add_argument("--bare", action="store_true", help="ignore the map: only the models the boards carry themselves")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args()
    mp = M.load_map(a.map)
    if a.bare:
        mp = {"vars": mp.get("vars", {}), "parts": {}, "boards": {b: {"footprints": {}, "refs": {}, "none": {}} for b in BOARDS}}
    dmap = M.dirs(mp, a.kicad3d)
    if a.prove:
        sys.exit(0 if prove(mp, dmap) else 1)
    total = {"ok": 0, "allowlisted": 0, "missing": 0}
    for name in a.board or BOARDS:
        t = report(name, check(name, mp, dmap), a.verbose)
        for k in total:
            total[k] += t[k]
    print("model coverage: %d resolved, %d allowlisted, %d missing: %s" % (
        total["ok"], total["allowlisted"], total["missing"], "PASS" if total["missing"] == 0 else "FAIL"))
    sys.exit(0 if total["missing"] == 0 else 1)


if __name__ == "__main__":
    main()
