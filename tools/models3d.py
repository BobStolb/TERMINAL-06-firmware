#!/usr/bin/env python3
"""models3d: attach 3D models to a board's footprints at render time, from tools/models3d.json.

    python3 tools/models3d.py plan  BOARD.kicad_pcb              # what every footprint resolves to
    python3 tools/models3d.py apply BOARD.kicad_pcb OUT.kicad_pcb # a scratch copy with the models attached

WHY. The committed boards (PCB/) and the fab packages built from them are not touched: the boards'
own (model ...) lines are whatever the generators wrote (92 of TS06-DRV's 116 footprints, 7 of
TS06-DISP's 30, none of the fascia's), and several of those name files that exist nowhere on this
machine. The map in tools/models3d.json says, per board and per footprint (or per reference), which
model files belong on which part, with offset, rotation and scale. This module reads the map and
writes the models into a COPY of the board. render_populated.py renders that copy; model_coverage.py
asks the same question without rendering and fails on any footprint that ends with no model.

THE MAP (tools/models3d.json)
    {"vars":   {"NAME": "directory, relative to the repository"},       # ${NAME} in a model path
     "parts":  {"name": {model}},                                       # reusable model entries
     "boards": {"TS06-DISP": {
         "footprints": {"TS06_IN12_Socket": {"models": [ "IN12_tube" | {model} , ... ], "replace": false}},
         "refs":       {"V5": {...}},                                   # a reference beats its footprint
         "none":       {"footprints": {"TS06_MountingHole_M3": "reason"}, "refs": {}}}}}
    a model: {"file": "${VAR}/dir/file.step", "offset": [x, y, z] mm, "rotate": [rx, ry, rz] deg,
              "scale": [sx, sy, sz], "kind": "taken"|"made", "note": "..."}   (KiCad's own convention)
    "replace": true drops the models the board itself carries on that footprint (a dead path, say);
    without it the map's models are added to them (a socketed chip is a second model on the socket).
    A footprint named BASE_R90 / _R180 / _R270 (a pre-rotated copy, written by tools/pcbkit.py) takes the
    entry of BASE when it has none of its own, with the offset turned and the z rotation reduced by the
    same angle, exactly as pcbkit turns a model it carries.

${KICAD10_3DMODEL_DIR} is KiCad's own library (not shipped in the kicad Docker image); every other
${NAME} is a "vars" entry. dirs() returns where each is looked up.
"""
import json, math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import sexp as S  # noqa: E402

MAP = os.path.join(HERE, "models3d.json")
KICAD_VAR = "KICAD10_3DMODEL_DIR"
VARIANT = re.compile(r"^(.*)_R(90|180|270)$")


def load_map(path=MAP):
    with open(path, encoding="utf8") as fh:
        return json.load(fh)


def dirs(mp, kicad3d=None):
    """{VAR: absolute directory}. KiCad's library: --kicad3d / $KICAD10_3DMODEL_DIR / the copy kept in
    3d/populated/kicad3d (the files this project uses, vendored there)."""
    d = {k: os.path.normpath(os.path.join(ROOT, v)) for k, v in mp.get("vars", {}).items()}
    d[KICAD_VAR] = os.path.abspath(kicad3d or os.environ.get(KICAD_VAR)
                                   or os.path.join(ROOT, "3d", "populated", "kicad3d"))
    return d


def expand(path, dmap):
    """${VAR}/rest -> a real path, or None when the variable is unknown."""
    m = re.match(r"^\$\{(\w+)\}(.*)$", path)
    if not m:
        return path
    base = dmap.get(m.group(1))
    return os.path.normpath(base + m.group(2)) if base else None


def _rot(x, y, r):
    """as pcbkit._rot: r degrees counter-clockwise as seen on screen (y down)."""
    r %= 360
    return {0: (x, y), 90: (y, -x), 180: (-x, -y), 270: (-y, x)}[r]


def _norm(m, mp):
    if isinstance(m, str):
        m = mp["parts"][m]
    out = dict(m)
    out.setdefault("offset", [0, 0, 0])
    out.setdefault("rotate", [0, 0, 0])
    out.setdefault("scale", [1, 1, 1])
    return out


def _turn(m, rot):
    """a model of the unrotated footprint, for the footprint pre-rotated by rot (see the docstring)."""
    if not rot:
        return m
    m = dict(m)
    x, y = _rot(m["offset"][0], m["offset"][1], rot)
    m["offset"] = [round(x, 6), round(y, 6), m["offset"][2]]
    m["rotate"] = [m["rotate"][0], m["rotate"][1], (m["rotate"][2] - rot) % 360]
    return m


def is_dnp(fp):
    """True when the footprint carries KiCad's do-not-populate attribute: (attr through_hole dnp)."""
    return any("dnp" in a[1:] for a in S.find_all(fp, "attr"))


def entry_for(bmap, ref, fpname, mp, dnp=False):
    """-> (kind, payload): ("models", {models, replace}) | ("none", reason) | (None, None)."""
    none = bmap.get("none", {})
    if ref in none.get("refs", {}):
        return "none", none["refs"][ref]
    if dnp and none.get("dnp"):
        return "none", none["dnp"]
    if ref in bmap.get("refs", {}):
        e = bmap["refs"][ref]
        return "models", {"replace": e.get("replace", False), "models": [_norm(m, mp) for m in e["models"]]}
    base, rot = fpname, 0
    for name in (fpname, None):
        if name is None:
            m = VARIANT.match(fpname)
            if not m:
                break
            name, rot = m.group(1), int(m.group(2))
        if name in none.get("footprints", {}):
            return "none", none["footprints"][name]
        if name in bmap.get("footprints", {}):
            e = bmap["footprints"][name]
            return "models", {"replace": e.get("replace", False),
                              "models": [_turn(_norm(m, mp), rot) for m in e["models"]]}
    return None, None


def footprints(tree):
    """[(ref, name without library, layer, node)] of a parsed board."""
    out = []
    for fp in tree:
        if isinstance(fp, list) and fp and fp[0] == "footprint":
            ref = next((S.unq(p[2]) for p in S.find_all(fp, "property") if S.unq(p[1]) == "Reference"), "?")
            layer = S.unq(S.find(fp, "layer")[1])
            out.append((ref, S.unq(fp[1]).split(":")[-1], layer, fp))
    return out


def board_key(path):
    return os.path.splitext(os.path.basename(path))[0]


def plan(tree, key, mp, dmap):
    """One row per footprint:
        {ref, fp, layer, status, models: [{file, resolved, exists, ...}], reason}
    status: "ok" (every model file in the effective list exists, and there is at least one),
            "allowlisted" (on the map's none list; reason says why),
            "missing" (no model at all, or a model file that does not exist)."""
    bmap = mp["boards"].get(key)
    if bmap is None:
        raise SystemExit("models3d: no board %r in the map (has %s)" % (key, ", ".join(mp["boards"])))
    rows = []
    for ref, name, layer, fp in footprints(tree):
        own = []
        for m in S.find_all(fp, "model"):
            own.append(_own_model(m))
        kind, pay = entry_for(bmap, ref, name, mp, is_dnp(fp))
        row = {"ref": ref, "fp": name, "layer": layer, "reason": "", "models": [], "replace": False,
               "own": own, "map": []}
        if kind == "none":
            row["status"], row["reason"] = "allowlisted", pay
            rows.append(row)
            continue
        eff = []
        if kind == "models":
            row["replace"] = pay["replace"]
            row["map"] = pay["models"]
            if not pay["replace"]:
                eff += own
            eff += pay["models"]
        else:
            eff += own
        for m in eff:
            r = expand(m["file"], dmap)
            m = dict(m)
            m["resolved"] = r
            m["exists"] = bool(r and os.path.isfile(r))
            row["models"].append(m)
        if not row["models"]:
            row["status"], row["reason"] = "missing", "no model on the board and none in the map"
        elif not all(m["exists"] for m in row["models"]):
            bad = [m["file"] for m in row["models"] if not m["exists"]]
            row["status"], row["reason"] = "missing", "model file not found: " + ", ".join(bad)
        else:
            row["status"] = "ok"
        rows.append(row)
    return rows


def _own_model(m):
    off = S.find(m, "offset")
    sc = S.find(m, "scale")
    ro = S.find(m, "rotate")
    g = lambda n, d: [float(v) for v in S.find(n, "xyz")[1:4]] if n else d
    return {"file": S.unq(m[1]), "offset": g(off, [0, 0, 0]), "scale": g(sc, [1, 1, 1]),
            "rotate": g(ro, [0, 0, 0]), "kind": "board", "note": "carried by the board's own footprint"}


def model_node(m):
    n = S.num
    return ["model", S.q(m["file"]),
            ["offset", ["xyz"] + [n(v) for v in m["offset"]]],
            ["scale", ["xyz"] + [n(v) for v in m["scale"]]],
            ["rotate", ["xyz"] + [n(v) for v in m["rotate"]]]]


def apply(tree, key, mp, dmap):
    """Write the map's models into the parsed board, in place. Returns plan()'s rows."""
    rows = plan(tree, key, mp, dmap)
    by_ref = {r["ref"]: r for r in rows}
    for ref, name, layer, fp in footprints(tree):
        r = by_ref[ref]
        if r["status"] == "allowlisted":                  # a hole, or a footprint left empty (DNP): no body at all
            fp[:] = [c for c in fp if not (isinstance(c, list) and c and c[0] == "model")]
            continue
        if not r["map"]:
            continue
        if r["replace"]:
            fp[:] = [c for c in fp if not (isinstance(c, list) and c and c[0] == "model")]
        for m in r["map"]:
            fp.append(model_node(m))
    return rows


def cmd_plan(board, mp, dmap):
    tree = S.parse(open(board, encoding="utf8").read())
    rows = plan(tree, board_key(board), mp, dmap)
    for r in rows:
        print("%-5s %-44s %-11s %s" % (r["ref"], r["fp"], r["status"],
                                       r["reason"] or ", ".join(os.path.basename(m["file"]) for m in r["models"])))
    return rows


def main(argv):
    if len(argv) < 3 or argv[1] not in ("plan", "apply"):
        sys.exit(__doc__)
    mp = load_map()
    dmap = dirs(mp)
    if argv[1] == "plan":
        cmd_plan(argv[2], mp, dmap)
        return
    tree = S.parse(open(argv[2], encoding="utf8").read())
    apply(tree, board_key(argv[2]), mp, dmap)
    open(argv[3], "w", encoding="utf8").write(S.dump(tree) + "\n")
    print("wrote", argv[3])


if __name__ == "__main__":
    main(sys.argv)
