#!/usr/bin/env python3
"""The hand wiring on the back of the fascia: one short wire from each control's lugs to its landing pads.

    python3 handwire.py REPO SITE_DATA_DIR OUT.json

Every control of the fascia (MODE rotary SW1, FIELD and SUB levers SW2 and SW3, the - and + buttons SW4 and SW5)
mounts from behind with only its bushing through the panel; its solder lugs stand 11 to 20 mm behind the board,
so each is wired by hand to landing pads on the fascia's back (tools/mkfp.py, PCB/README.md). This writes the
wires' paths for the product page's 3D view.

WHERE EACH INPUT COMES FROM
  * lug positions: the control models themselves. The populated fascia R (3d/populated/TS06-FASCIA-rhythm-populated.glb)
    carries the STEP bodies of 3d/SR25.step, MT1.step and KMD1.step with their lugs; the lugs are found as the geometry
    standing behind each body's rear face (a 1 mm round tap or common of the rotary; a 3.0 x 0.8 mm plate of a lever or a
    button) and clustered. Nothing is typed in.
  * landing pads and their nets: the fascia's own board file (PCB/TS06-FASCIA-rhythm/*.kicad_pcb), read only.
  * a board that is not populated (A, which stands in for the printed frame F) has no lug models: its control
    bodies are the case model's stand-ins (data/model.json), so each wire starts on the body's back face.

WHAT IS CHOSEN HERE, AND SAID SO ON THE PAGE
  * which lug takes which pad. The rotary: the dial's six positions are at -75..+75 degrees (tools/fascia_art.py ANG), so
    position k (0 V at 1, +5 V at 6) is the tap lug at its angle on the 10 mm ring, and the wiper is the common on the
    same side; the other six taps and the other common stay free. A lever or a button has three lugs and the board two
    pads: the two lugs nearest the pads are used (the middle one to pad 2, the lower one to pad 1), the third stays
    free. Which lug of a real lever is the common is for a meter to say, not the model.
  * the routes and their depths, found here so that no wire touches a body, a lug that is not its own, or another wire.
Standard library, plus numpy (the same as 3d/populated's tools).
"""
import itertools, json, math, os, struct, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kparts                                                  # noqa: E402  (the build's own s-expression reader)

RW = 0.35                       # hook-up wire, 0.7 mm over the insulation
CLR = 0.15                      # the least gap kept beside a wire
ANG = [-75.0 + 30.0 * k for k in range(6)]            # tools/fascia_art.py: dial position k+1, degrees, y down
TAP_NET = ["GND", "TAP2", "TAP3", "TAP4", "TAP5", "+5V"]    # position 1..6: 0 V .. 5 V (TERMINAL-06-control-scheme-revB.md)


# ---------------------------------------------------------------------------------------------- the GLB
def load_glb(path):
    d = open(path, "rb").read()
    ln = struct.unpack("<I", d[8:12])[0]
    off, js, bin_ = 12, None, None
    while off < ln:
        cl, ct = struct.unpack("<II", d[off:off + 8])
        off += 8
        chunk = d[off:off + cl]
        off += cl
        if ct == 0x4E4F534A:
            js = json.loads(chunk)
        elif ct == 0x004E4942:
            bin_ = chunk
    return js, bin_


_DT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
_NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def accessor(js, bin_, i):
    a = js["accessors"][i]
    bv = js["bufferViews"][a["bufferView"]]
    dt, n = _DT[a["componentType"]], _NC[a["type"]]
    off = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    stride = bv.get("byteStride", 0)
    isz = np.dtype(dt).itemsize * n
    if stride and stride != isz:
        arr = np.frombuffer(bin_, dtype=np.uint8, count=a["count"] * stride, offset=off).reshape(a["count"], stride)[:, :isz].copy().view(dt).reshape(a["count"], n)
    else:
        arr = np.frombuffer(bin_, dtype=dt, count=a["count"] * n, offset=off).reshape(a["count"], n)
    if a.get("normalized"):
        arr = arr.astype(np.float64) / np.iinfo(dt).max
    return arr.astype(np.float64)


def local(nd):
    if "matrix" in nd:
        return np.array(nd["matrix"]).reshape(4, 4).T
    T, S, R = np.eye(4), np.eye(4), np.eye(4)
    if "translation" in nd:
        T[:3, 3] = nd["translation"]
    if "scale" in nd:
        S[0, 0], S[1, 1], S[2, 2] = nd["scale"]
    if "rotation" in nd:
        x, y, z, w = nd["rotation"]
        R[:3, :3] = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]
    return T @ R @ S


def node_points(js, bin_):
    """{reference: Nx3 vertices in mm}: x = board x, y = height above the back face (negative = behind it), z = board y."""
    out = {}
    nodes = js["nodes"]

    def rec(i, M, top):
        nd = nodes[i]
        M2 = M @ local(nd)
        name = nd.get("name", "")
        if top is None and name[:2] in ("SW", "J1", "R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"):
            top = name
        if "mesh" in nd and top:
            for pr in js["meshes"][nd["mesh"]]["primitives"]:
                P = accessor(js, bin_, pr["attributes"]["POSITION"])
                P = (np.c_[P, np.ones(len(P))] @ M2.T)[:, :3] * 1000.0
                out.setdefault(top, []).append(P)
        for c in nd.get("children", []):
            rec(c, M2, top)
    for r in js["scenes"][js.get("scene", 0)]["nodes"]:
        rec(r, np.eye(4), None)
    return {k: np.vstack(v) for k, v in out.items()}


def cluster(pts, gap):
    """Single-link clusters of (x, z) points closer than gap."""
    n = len(pts)
    lab = list(range(n))

    def find(a):
        while lab[a] != a:
            lab[a] = lab[lab[a]]
            a = lab[a]
        return a
    xz = pts[:, [0, 2]]
    for i in range(n):
        d = np.hypot(*(xz[i + 1:] - xz[i]).T) if i + 1 < n else np.array([])
        for j in np.nonzero(d < gap)[0]:
            lab[find(i)] = find(i + 1 + j)
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    return list(groups.values())


def lugs_of(P, back):
    """The lugs of one control: the geometry standing behind the body's rear face (y < -back), one cluster each."""
    q = P[P[:, 1] < -back - 0.02]
    out = []
    for idx in cluster(q, 3.4):
        c = q[idx]
        lo, hi = c.min(0), c.max(0)
        out.append({"x": round((lo[0] + hi[0]) / 2, 3), "y": round((lo[2] + hi[2]) / 2, 3), "w": round(hi[0] - lo[0], 3), "t": round(hi[2] - lo[2], 3),
                    "d0": round(-hi[1], 3), "d1": round(-lo[1], 3)})
    return sorted(out, key=lambda l: (l["y"], l["x"]))


# ---------------------------------------------------------------------------------------------- paths
def fillet(pts, rho=1.6, step=0.4):
    """A dense polyline through the waypoints with each corner rounded (a quadratic bezier), points about `step` apart."""
    P = [np.array(p, float) for p in pts]
    out = [P[0]]
    for i in range(1, len(P) - 1):
        a, b = P[i] - P[i - 1], P[i + 1] - P[i]
        la, lb = np.linalg.norm(a), np.linalg.norm(b)
        r = min(rho, 0.45 * la, 0.45 * lb)
        if r < 1e-6 or la < 1e-9 or lb < 1e-9:
            out.append(P[i])
            continue
        q0, q1 = P[i] - a / la * r, P[i] + b / lb * r
        n = max(3, int(r * 3))
        for k in range(n + 1):
            t = k / n
            out.append((1 - t) ** 2 * q0 + 2 * (1 - t) * t * P[i] + t ** 2 * q1)
    out.append(P[-1])
    dense = [out[0]]
    for p in out[1:]:
        seg = p - dense[-1]
        L = np.linalg.norm(seg)
        if L > 1e-9:
            m = max(1, int(math.ceil(L / step)))
            base = dense[-1]
            for k in range(1, m + 1):
                dense.append(base + seg * (k / m))
    return np.array(dense)


def seg_dist_pts(A, B):
    """Smallest distance between two dense point sets (their segments are short enough to compare by points)."""
    d = np.linalg.norm(A[:, None, :] - B[None, :, :], axis=2)
    return float(d.min())


def box_dist(p, lo, hi):
    q = np.maximum(np.maximum(lo - p, 0), p - hi)
    return np.linalg.norm(q, axis=-1)


def check(wires, lugs, body, own):
    """The least clearance (mm) of any wire to a body, to a lug that is not its own, and to another wire. Wires are dense (x, y, depth)."""
    worst = {"wire-wire": 9e9, "wire-lug": 9e9, "wire-body": 9e9}
    for i, a in enumerate(wires):
        for b in wires[i + 1:]:
            worst["wire-wire"] = min(worst["wire-wire"], seg_dist_pts(a, b) - 2 * RW)
        for j, l in enumerate(lugs):
            lo = np.array([l["x"] - l["w"] / 2, l["y"] - l["t"] / 2, l["d0"]])
            hi = np.array([l["x"] + l["w"] / 2, l["y"] + l["t"] / 2, l["d1"]])
            pts = a[2:] if j == own[i] else a                  # a wire starts on its own lug
            if j == own[i]:
                arc = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(a, axis=0), axis=1))])
                pts = a[arc > 2.0]
            if len(pts):
                worst["wire-lug"] = min(worst["wire-lug"], float(box_dist(pts, lo, hi).min()) - RW)
        if body:
            if body["kind"] == "cyl":
                r = np.hypot(a[:, 0] - body["x"], a[:, 1] - body["y"])         # a cylinder standing from the back face to its depth
                dist = np.hypot(np.maximum(r - body["r"], 0), np.maximum(a[:, 2] - body["depth"], 0))
                dist = np.where((r < body["r"]) & (a[:, 2] < body["depth"]), -1.0, dist)
                worst["wire-body"] = min(worst["wire-body"], float(dist.min()) - RW)
            else:
                lo = np.array([body["x0"], body["y0"], 0.0])
                hi = np.array([body["x1"], body["y1"], body["depth"]])
                worst["wire-body"] = min(worst["wire-body"], float(box_dist(a, lo, hi).min()) - RW)
    return {k: round(v, 2) for k, v in worst.items()}


# ---------------------------------------------------------------------------------------------- the controls
def pad_net(root, ref):
    """{pad: (x, y, net)} of one footprint of a board file (board coordinates, as kparts reads them)."""
    out = {}
    for fp in kparts.kids(root, "footprint"):
        props = {p[1]: p[2] for p in kparts.kids(fp, "property") if len(p) > 2}
        if props.get("Reference") != ref:
            continue
        at = kparts.kid(fp, "at")
        x0, y0, r = float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0.0
        for p in kparts.kids(fp, "pad"):
            if not p[1]:
                continue
            pa = kparts.kid(p, "at")
            dx, dy = kparts.rot(float(pa[1]), float(pa[2]), r)
            nt = kparts.kid(p, "net")
            sz = kparts.kid(p, "size")
            out[p[1]] = (round(x0 + dx, 3), round(y0 + dy, 3), (nt[2] if len(nt) > 2 else nt[1]) if nt else "", (float(sz[1]), float(sz[2])) if sz else (0, 0))
    return out


def rotary(lugs, pads, at):
    """Seven wires: the dial's six tap lugs and the wiper common on the same side; paths with depths found by search."""
    cx, cy = at
    ring = [l for l in lugs if abs(math.hypot(l["x"] - cx, l["y"] - cy) - 10.0) < 0.5]
    com = [l for l in lugs if abs(math.hypot(l["x"] - cx, l["y"] - cy) - 5.45) < 0.5]
    taps = []
    for k, a in enumerate(ANG):
        tx, ty = cx + 10.0 * math.cos(math.radians(a)), cy + 10.0 * math.sin(math.radians(a))
        l = min(ring, key=lambda l: math.hypot(l["x"] - tx, l["y"] - ty))
        assert math.hypot(l["x"] - tx, l["y"] - ty) < 0.2, (k, l)
        taps.append((l, TAP_NET[k]))
    wl = max(com, key=lambda l: l["x"])                          # the common on the dial's side (right)
    want = [(l, net) for l, net in taps] + [(wl, "A6")]
    pad_of = {net: n for n, (x, y, net, sz) in pads.items()}      # pad number by net
    items = []
    for l, net in want:
        n = pad_of[net]
        items.append((l, net, n, pads[n][:2]))
    return items, ring + com


def route_rotary(items, at, depths):
    cx, cy = at
    wires = []
    for (l, net, n, (px, py)), dk in zip(items, depths):
        rx, ry = l["x"] - cx, l["y"] - cy
        r = math.hypot(rx, ry)
        ux, uy = rx / r, ry / r
        jd = l["d1"] - 1.3                                       # the joint, 1.3 mm from the lug's tip
        rout = 13.4 if r > 8 else 13.0
        wires.append([(l["x"], l["y"], jd), (cx + ux * rout, cy + uy * rout, dk), (px, py, dk), (px, py, RW)])
    return wires


def plate(lugs, pads, at, body_back):
    """A lever or a button: the two lugs nearest the pads, the middle one to pad 2, the lower one to pad 1."""
    ordered = sorted(lugs, key=lambda l: l["y"])
    low, mid = ordered[-1], ordered[-2]
    items = [(low, pads["1"][2], "1", pads["1"][:2]), (mid, pads["2"][2], "2", pads["2"][:2])]
    return items


def route_plate(items, at, ylow):
    wires = []
    for k, (l, net, n, (px, py)) in enumerate(items):
        jd = l["d1"] - 1.3
        side = 1.0 if n == "2" else -1.0
        xo = l["x"] + side * 2.5                                  # round the lug plate's side (it is 3.0 wide)
        yo = ylow + 1.9                                            # below the body's lower edge
        wires.append([(l["x"] + side * 0.6, l["y"], jd), (xo, l["y"], jd - 0.2 * k), (xo, yo, jd - 0.2 * k), (px, py - 0.4, 3.5), (px, py, RW)])
    return wires


def standin(ref, X0, body, pads, at):
    """No lug model: each wire starts on the stand-in body's back face (depth `dep`) and runs to its pad."""
    _, X, t, a, b, dep = body
    cx, cy = X - X0, t
    names = sorted(pads, key=lambda n: pads[n][0])          # left to right, so the wires do not cross on their way down
    wires, nets = [], []
    n = len(names)
    for i, nm in enumerate(names):
        px, py, net = pads[nm][:3]
        # the start: along the body's lower rear edge, spread over its width; depth = the body's back face
        sx = cx + (i - (n - 1) / 2) * min(2.0, (a - 4) / max(1, n - 1)) if ref != "SW1" else cx + (i - 3) * 1.6
        sy = cy + (b / 2 - 1.2 if ref != "SW1" else 7.0)
        wires.append([(sx, sy, dep), (sx, sy + 2.0, dep + 1.0), (px, py - 1.0, dep + 1.0 - 0.3 * i), (px, py - 0.4, 3.5), (px, py, RW)])
        nets.append((net, nm))
    return wires, nets


def build(repo, data_dir):
    out = {"about": "Written by recovered/viewer2/tools/handwire.py. Native fascia coordinates: x and y as in the board file (y down the page), "
                    "depth = mm behind the back face. Wires are dense polylines, radius %.2f mm." % RW,
           "wire_r": RW, "boards": {}}
    model = json.load(open(os.path.join(data_dir, "model.json"), encoding="utf8"))
    for board, key, populated in (("TS06-FASCIA-rhythm", "R", True), ("TS06-FASCIA", "A", False)):
        path = os.path.join(repo, "PCB", board, board + ".kicad_pcb")
        if not os.path.isfile(path):
            continue
        root = kparts.parse(open(path, encoding="utf8").read())
        info = {"source": "PCB/%s/%s.kicad_pcb" % (board, board), "controls": {}, "lugs_from": None}
        P = None
        if populated:
            glb = os.path.join(repo, "3d", "populated", board + "-populated.glb")
            if os.path.isfile(glb):
                js, b = load_glb(glb)
                P = node_points(js, b)
                info["lugs_from"] = os.path.relpath(glb, repo).replace(os.sep, "/")
        brd = kparts.board(path)["parts"]
        for ref in ("SW1", "SW2", "SW3", "SW4", "SW5"):
            at = brd[ref]["at"][:2]
            pads = pad_net(root, ref)
            c = {"at": at, "pads": {n: [v[0], v[1], v[2]] for n, v in pads.items()}}
            if P is not None and ref in P:
                pts = P[ref]
                back = 11.31 if ref == "SW1" else 16.66
                assert abs(-pts[:, 1].min() - back) > 1 and pts[:, 1].min() < -back, ref
                lugs = lugs_of(pts, back)
                body_pts = pts[(pts[:, 1] >= -back - 0.02) & (pts[:, 1] <= 0.0)]
                if ref == "SW1":
                    body = {"kind": "cyl", "x": at[0], "y": at[1], "r": round((body_pts[:, 0].max() - body_pts[:, 0].min()) / 2, 2), "depth": back}
                else:
                    body = {"kind": "box", "x0": round(body_pts[:, 0].min(), 2), "x1": round(body_pts[:, 0].max(), 2),
                            "y0": round(body_pts[:, 2].min(), 2), "y1": round(body_pts[:, 2].max(), 2), "depth": back}
                c["model"] = "lugs"
                c["lugs"] = lugs
                c["body"] = body
                if ref == "SW1":
                    items, rel = rotary(lugs, pads, at)
                    best = None
                    for perm in itertools.permutations(range(7)):
                        depths = [12.6 + 1.25 * i for i in perm]
                        raw = route_rotary(items, at, depths)
                        dense = [fillet(w) for w in raw]
                        res = check(dense, lugs, body, [lugs.index(it[0]) for it in items])
                        score = min(res.values())
                        if best is None or score > best[0]:
                            best = (score, raw, dense, res, depths)
                        if score >= 0.35:
                            break
                    score, raw, dense, res, depths = best
                else:
                    items = plate(lugs, pads, at, back)
                    raw = route_plate(items, at, body["y1"])
                    dense = [fillet(w) for w in raw]
                    res = check(dense, lugs, body, [lugs.index(it[0]) for it in items])
                c["clearance"] = res
                c["wires"] = [{"net": it[1], "pad": it[2], "lug": {"x": it[0]["x"], "y": it[0]["y"]},
                               "pts": [[round(float(v), 3) for v in p] for p in d]} for it, d in zip(items, dense)]
            else:
                bodies = {b[0]: b for b in model["fascia_variants"][("F" if key == "A" else key)]["bodies"]}
                X0 = model["fascia_variants"]["F" if key == "A" else key]["X0"]
                raw, nets = standin(ref, X0, bodies[ref], pads, at)
                dense = [fillet(w) for w in raw]
                c["model"] = "standin"
                c["wires"] = [{"net": n[0], "pad": n[1], "pts": [[round(float(v), 3) for v in p] for p in d]} for n, d in zip(nets, dense)]
            info["controls"][ref] = c
        out["boards"][board] = info
    return out


def main(repo, data_dir, out):
    res = build(repo, data_dir)
    with open(out, "w", encoding="utf8") as fh:
        json.dump(res, fh, ensure_ascii=False, separators=(",", ":"))
    for b, info in res["boards"].items():
        for ref, c in info["controls"].items():
            print("  %-20s %s %-7s %2d wires %s" % (b, ref, c["model"], len(c["wires"]),
                  ("lugs %d, clearance %s" % (len(c["lugs"]), c["clearance"])) if c["model"] == "lugs" else "(no lug model: from the stand-in body's back face)"))


if __name__ == "__main__":
    main(*sys.argv[1:4])
