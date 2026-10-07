#!/usr/bin/env python3
"""The hand wiring on the back of the fascia: one wire from each control's lugs to its landing pads, dressed as a harness.

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
  * the routes, as a careful builder would dress them (route_rotary, route_plate; the drawing is seen from the back, x to the
    right, y down, depth toward the viewer):
      - one group, one path. The dial's seven wires leave their lugs on the lugs' side that faces the group, run down along the
        lug, lie over the body's rear face to the group's line (the first pad column that clears the body's right flank), turn
        down it and run down the flank one over another, the wire that joined first lowest, a flat group standing on edge with
        PITCH between the wires. At the foot of the flank each wire leaves the group in the order of the pads: to the left along
        the pad row, straight on, or (the pads to the right) off the flank to the right, the farther pad first, so no two
        wires cross as seen from the back, and none passes through another (the one that is higher passes over).
      - one bend radius, RHO, for every bend of every wire (fillet() draws true circular arcs and refuses a route whose
        straights cannot hold them), straight between bends, and every wire lands flat on its pad (the last bend levels it out,
        then it lies on the pad to the pad's centre).
      - a lever's or button's two wires leave the plates' two ends, run down the page side by side, and turn down together
        past the body's lower edge, as close to it as a clearance allows. (A stand-in body with its pads too close under it
        for that, the buttons of board A, has its wires go down the body's two sides instead.)
      - the clearances are checked here (check()): wire to wire (exact, segment to segment), to a lug that is not its own, to the
        body, the plan crossings, and the bend radius. They are written into the data for the page's tests.
    The common of the dial is the one wire that joins the group between two taps and leaves it on the other side from them
    (its pad, A6, is the last at the right): as a group stacked on edge it needs no crossing. As a flat ribbon it would cross
    the taps' wires once; the pad row would then need A6 between TAP4 and TAP3, the dial's own order.
Standard library, plus numpy (the same as 3d/populated's tools).
"""
import json, math, os, struct, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kparts                                                  # noqa: E402  (the build's own s-expression reader)

RW = 0.35                       # hook-up wire, 0.7 mm over the insulation
CLR = 0.15                      # the least gap kept beside a wire
RHO = 1.6                       # the one bend radius of every wire's centre line (2.3 wire diameters)
PITCH = 0.95                    # the wires of a group, one over another: 0.7 mm of wire and 0.25 mm of air
LF = 1.2                        # the flat run of a wire on its pad's side of the last bend (covers the pad from its edge to its centre)
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
# A wire is a polyline of corners (x, y, depth). Every corner is rounded by a true circular arc of ONE radius, RHO, the same
# for every wire of every control: the wire turns the same way everywhere, runs straight between turns, and a corner that
# the straights cannot hold is an error (it is never shrunk), so the drawing cannot hide a tight kink.
def fillet(pts, rho=None, step=0.25):
    """The corners `pts` joined by straights and circular arcs of radius rho (mm); returns (dense points, shortest straight, arcs).
    A straight shorter than the two arcs on its ends (their tangent lengths) raises: the route must be designed to fit."""
    rho = RHO if rho is None else rho
    P = [np.array(p, float) for p in pts]
    n = len(P)
    tl = [0.0] * n                                                # tangent length of each corner
    turn = [0.0] * n
    for i in range(1, n - 1):
        a, b = P[i] - P[i - 1], P[i + 1] - P[i]
        ua, ub = a / np.linalg.norm(a), b / np.linalg.norm(b)
        turn[i] = math.acos(max(-1.0, min(1.0, float(ua @ ub))))
        tl[i] = rho * math.tan(turn[i] / 2.0) if turn[i] > 1e-4 else 0.0
    short = 9e9
    for i in range(n - 1):
        free = float(np.linalg.norm(P[i + 1] - P[i])) - tl[i] - tl[i + 1]
        short = min(short, free)
        if free < -1e-6:
            raise ValueError("a straight of %.2f mm between corners %d and %d cannot hold two bends of radius %.2f (%s)" % (free + tl[i] + tl[i + 1], i, i + 1, rho, pts[i]))
    out = [P[0]]
    for i in range(1, n - 1):
        if turn[i] <= 1e-4:
            out.append(P[i])
            continue
        a, b = P[i] - P[i - 1], P[i + 1] - P[i]
        ua, ub = a / np.linalg.norm(a), b / np.linalg.norm(b)
        q0 = P[i] - ua * tl[i]
        nv = ub - ua * float(ua @ ub)
        nv /= np.linalg.norm(nv)
        c = q0 + nv * rho
        m = max(3, int(math.ceil(turn[i] * rho / step)))
        for k in range(m + 1):
            s = turn[i] * k / m
            out.append(c + (q0 - c) * math.cos(s) + ua * rho * math.sin(s))
    out.append(P[-1])
    dense = [out[0]]
    for p in out[1:]:
        seg = p - dense[-1]
        L = np.linalg.norm(seg)
        if L > 1e-9:
            m = max(1, int(math.ceil(L / 0.8)))
            base = dense[-1]
            for k in range(1, m + 1):
                dense.append(base + seg * (k / m))
    return np.array(dense), short


def min_radius(dense):
    """The smallest radius of curvature (mm) along a dense polyline (circle through each three points 4 apart)."""
    r = 9e9
    for i in range(0, len(dense) - 8, 1):
        a, b, c = dense[i], dense[i + 4], dense[i + 8]
        ab, bc, ca = np.linalg.norm(b - a), np.linalg.norm(c - b), np.linalg.norm(a - c)
        area2 = np.linalg.norm(np.cross(b - a, c - a))
        if area2 > 1e-9:
            r = min(r, ab * bc * ca / (2.0 * area2))
    return r


def seg_seg_dist(A, B):
    """Smallest distance between two polylines (exact: segment to segment), A and B as Nx3 arrays."""
    p0, d1 = A[:-1][:, None, :], (A[1:] - A[:-1])[:, None, :]
    q0, d2 = B[:-1][None, :, :], (B[1:] - B[:-1])[None, :, :]
    r = p0 - q0
    a, e, f = (d1 * d1).sum(-1), (d2 * d2).sum(-1), None
    b, c = (d1 * d2).sum(-1), (d1 * r).sum(-1)
    f = (d2 * r).sum(-1)
    den = a * e - b * b
    s = np.where(den > 1e-12, np.clip((b * f - c * e) / np.where(den > 1e-12, den, 1), 0, 1), 0.0)
    t = (b * s + f) / np.where(e > 1e-12, e, 1)
    t = np.clip(t, 0, 1)
    s = np.clip((b * t - c) / np.where(a > 1e-12, a, 1), 0, 1)
    t = np.clip((b * s + f) / np.where(e > 1e-12, e, 1), 0, 1)
    diff = (p0 + d1 * s[..., None]) - (q0 + d2 * t[..., None])
    return float(np.sqrt((diff * diff).sum(-1)).min())


def plan_crossings(wires):
    """Pairs of wires whose plan views (x, y) cross each other transversally (more than 20 degrees apart), as seen from the back.
    Wires of a dressed group lie over each other (parallel in plan, stacked in depth): that is not a crossing."""
    n = 0
    pairs = []
    for i in range(len(wires)):
        for j in range(i + 1, len(wires)):
            A, B = wires[i][:, :2], wires[j][:, :2]
            p, d1 = A[:-1][:, None, :], (A[1:] - A[:-1])[:, None, :]
            q, d2 = B[:-1][None, :, :], (B[1:] - B[:-1])[None, :, :]
            den = d1[..., 0] * d2[..., 1] - d1[..., 1] * d2[..., 0]
            w = q - p
            with np.errstate(divide="ignore", invalid="ignore"):
                t = (w[..., 0] * d2[..., 1] - w[..., 1] * d2[..., 0]) / den
                u = (w[..., 0] * d1[..., 1] - w[..., 1] * d1[..., 0]) / den
            l1, l2 = np.hypot(d1[..., 0], d1[..., 1]), np.hypot(d2[..., 0], d2[..., 1])
            sin = np.abs(den) / np.maximum(l1 * l2, 1e-12)
            hit = (t > 0.02) & (t < 0.98) & (u > 0.02) & (u < 0.98) & (sin > math.sin(math.radians(20)))
            if hit.any():
                n += 1
                pairs.append((i, j))
    return n, pairs


def box_dist(p, lo, hi):
    q = np.maximum(np.maximum(lo - p, 0), p - hi)
    return np.linalg.norm(q, axis=-1)


def check(wires, lugs, body, own, others=()):
    """The least clearance (mm) of any wire to a body, to a lug that is not its own, and to another wire (surface to surface),
    and the number of plan crossings. Wires are dense (x, y, depth). `others`: wires of the other controls of the board."""
    worst = {"wire-wire": 9e9, "wire-lug": 9e9, "wire-body": 9e9}
    for i, a in enumerate(wires):
        for b in list(wires[i + 1:]) + list(others):
            worst["wire-wire"] = min(worst["wire-wire"], seg_seg_dist(a, b) - 2 * RW)
        arc = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(a, axis=0), axis=1))])
        for j, l in enumerate(lugs):
            # a lug stands from the body's rear face to its tip (the model's tip vertices are all the tool reads: d0 = d1)
            lo = np.array([l["x"] - l["w"] / 2, l["y"] - l["t"] / 2, body["depth"] if body else l["d0"]])
            hi = np.array([l["x"] + l["w"] / 2, l["y"] + l["t"] / 2, l["d1"]])
            pts = a[arc > 8.0] if j == own[i] else a              # a wire starts on its own lug, and runs down along it
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
    out = {k: (None if v > 1e8 else round(v, 2)) for k, v in worst.items()}      # None: nothing of that kind to be clear of
    out["crossings"] = plan_crossings(list(wires))[0]
    return out


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

def route_rotary(items, at, body):
    """The dial's seven wires as ONE dressed group (the page draws it from the back, x to the right, y down, depth toward the viewer).

    Each wire leaves its lug on the lug's side that faces the group, runs down along the lug to just above the body's rear face,
    and lies over that face (a straight, parallel to the board) to the group's line XB, beside the body's right flank. There it
    turns down and joins the group: the seven wires run down the flank one over another (a flat group standing on edge, side by
    side at the pitch PITCH, the wire that joined first lowest), so from every side they run as one path. At the foot of the flank
    each wire leaves the group in the order of its pad and lands on it flat: the wires for the pads to the left turn left along
    the pad row (the group's lowest part is a row of seven, then fewer); the wire for the pad under the line goes straight on; the
    wires for the pads to the right turn right, the farther pad first. The wire that joined first is the lowest of the group, so
    every wire later down the line (and every wire that turns away) passes over the ones below it, never through them."""
    cx, cy = at
    rad, back = body["r"], body["depth"]
    H = back + 2.1                                              # the run over the body's rear face (1.4 mm of air under the wire)
    order = sorted(items, key=lambda it: it[0]["y"])            # the order the lugs are met going down the flank
    edge = cx + rad
    XB = min(it[3][0] for it in items if it[3][0] >= edge + 2.4)    # the line of the group: the first pad column that clears the flank
    D0 = RW + 2 * RHO + 0.25                                    # the lowest level of the group
    py = max(it[3][1] for it in items)
    ya = py - RHO - LF                                          # where a wire coming down onto its pad starts to level out
    right = sorted([it for it in order if it[3][0] > XB + 0.01], key=lambda it: it[3][0])    # pad nearest the line first
    yp = {}
    for r, it in enumerate(right):
        yp[it[2]] = ya - 2 * RHO - 1.0 - (2 * RHO + 0.4) * r         # turn-away heights: the farther pad's wire turns off higher up
    wires, info = [], []
    for idx, (l, net, n, (px, pyy)) in enumerate(order):
        D = D0 + PITCH * idx
        x0, y0 = l["x"] + l["w"] / 2 + RW, l["y"]
        jd = l["d1"] - 1.3
        pts = [(x0, y0, jd), (x0, y0, H), (XB, y0, H), (XB, y0, D)]
        if abs(px - XB) < 0.01:
            pts += [(XB, ya, D), (XB, ya, RW), (XB, pyy, RW)]
            kind = "straight on"
        elif px < XB:
            xa = px + RHO + LF
            pts += [(XB, pyy, D), (xa, pyy, D), (xa, pyy, RW), (px, pyy, RW)]
            kind = "left"
        else:
            pts += [(XB, yp[n], D), (px, yp[n], D), (px, ya, D), (px, ya, RW), (px, pyy, RW)]
            kind = "right"
        wires.append(pts)
        info.append({"level": round(D, 3), "turn": kind})
    return order, wires, info


def plate(lugs, pads, at, body_back):
    """A lever or a button: the two lugs nearest the pads, the middle one to pad 2, the lower one to pad 1."""
    ordered = sorted(lugs, key=lambda l: l["y"])
    low, mid = ordered[-1], ordered[-2]
    items = [(low, pads["1"][2], "1", pads["1"][:2]), (mid, pads["2"][2], "2", pads["2"][:2])]
    return items


def route_plate(items, body):
    """The pair of wires of a lever or a button: out of the lug plates toward the pads, side by side, level over the body's rear
    face, down past the body's lower edge together (one line of drops, the same height), and out flat onto their pads. The wire of
    the middle lug passes the lower lug on the side of its own pad, a clearance away, and settles into its lane before the lug."""
    low = items[0][0]
    # both wires turn down on one line, yc: as far down the page as the lower lug allows a wire of bend radius RHO to leave it, and
    # not lower than a bend's room above the pads (the lower lug of a button is only 3 mm from them: its wire dives from the plate at once)
    yc = min(low["y"] + RHO, items[0][3][1] - RHO - 0.1)
    wires, info = [], []
    for k, (l, net, n, (px, py)) in enumerate(items):
        jd = l["d1"] - 1.3
        if n == "1":                                               # from the lower lug, straight down the page to the drop
            xs = px
            pts = [(xs, yc - RHO, jd), (xs, yc, jd), (xs, yc, RW), (px, py, RW)]
        else:                                                      # from the middle lug, down the lower lug's right side
            xc = low["x"] + low["w"] / 2 + RW + CLR                # the plate's right end, a clearance off the lower plate's end
            pts = [(xc, l["y"], jd), (xc, yc, jd), (xc, yc, RW), (px, py, RW)]
        wires.append(pts)
        info.append({"level": round(jd, 3), "turn": "pad " + n})
    return wires, info


def route_plate_side(items, body):
    """A lever or button whose pads sit too close under its body for a wire to come down in front of the pads' edge and level out
    (the stand-in buttons of board A: the pads are 1 mm below the body): the wires leave the plates in opposite directions, down
    past the body's two sides, and land flat on their pads from the outside, along the pads' long side."""
    wires, info = [], []
    for k, (l, net, n, (px, py)) in enumerate(items):
        jd = l["d1"] - 1.3
        yl = l["y"]
        if n == "1":
            xs, xl = l["x"] - 1.0, body["x0"] - RW - 0.3
        else:
            xs, xl = l["x"] + 1.0, body["x1"] + RW + 0.3
        pts = [(xs, yl, jd), (xl, yl, jd), (xl, py, jd), (xl, py, RW), (px, py, RW)]
        wires.append(pts)
        info.append({"level": round(jd, 3), "turn": "pad " + n + " side"})
    return wires, info


def standin(ref, X0, body, pads, at):
    """No lug model: the control is the case model's stand-in body, and its wires start on the body's back face (depth `dep`),
    where a lug would be. Virtual lugs are put there, and the wires are routed exactly as the real ones are: the dial's seven as one
    group down its flank, a lever's or button's two side by side past the body's lower edge. Returns the corner lists and the nets."""
    _, X, t, a, b, dep = body
    cx, cy = X - X0, t
    py = max(v[1] for v in pads.values())
    if ref == "SW1":
        rad = a / 2
        XB = min(v[0] for v in pads.values() if v[0] >= cx + rad + 2.4)
        # the order the wires join the group: the pads to the right (they turn away first, so they go lowest), then the pad on the
        # line, then the pads to the left from the nearest (the farther the pad, the higher the wire, so it passes over the others)
        names = sorted(pads, key=lambda nm: (0 if pads[nm][0] > XB + 0.01 else 1 if abs(pads[nm][0] - XB) < 0.01 else 2, abs(pads[nm][0] - XB)))
        items = []
        for i, nm in enumerate(names):
            lug = {"x": cx + 4.0, "y": cy - 9.0 + 3.0 * i, "w": 0.1, "t": 0.1, "d0": dep + 1.75, "d1": dep + 1.75}
            items.append((lug, pads[nm][2], nm, pads[nm][:2]))
        bd = {"kind": "cyl", "x": cx, "y": cy, "r": rad, "depth": dep}
        order, wires, _ = route_rotary(items, (cx, cy), bd)
        return wires, [(it[1], it[2]) for it in order], bd
    y1 = cy + b / 2
    bd = {"kind": "box", "x0": cx - a / 2, "x1": cx + a / 2, "y0": cy - b / 2, "y1": y1, "depth": dep}
    room = py - RHO - 0.1 >= y1 + RW + CLR
    ylow = (y1 - 0.9) if room else py - 2 * RHO - 0.1
    lugs = [{"x": cx, "y": ylow, "w": 3.0, "t": 0.8, "d0": dep + 3.0, "d1": dep + 3.0},
            {"x": cx, "y": ylow - 6.0 if room else ylow, "w": 3.0, "t": 0.8, "d0": dep + 3.0, "d1": dep + 3.0}]
    items = [(lugs[0], pads["1"][2], "1", pads["1"][:2]), (lugs[1], pads["2"][2], "2", pads["2"][:2])]
    wires, _ = route_plate(items, bd) if room else route_plate_side(items, bd)
    return wires, [(it[1], it[2]) for it in items], bd


def build(repo, data_dir):
    out = {"about": "Written by recovered/viewer2/tools/handwire.py. Native fascia coordinates: x and y as in the board file (y down the page), "
                    "depth = mm behind the back face. Wires are dense polylines, radius %.2f mm; every bend has radius %.2f mm." % (RW, RHO),
           "wire_r": RW, "bend_r": RHO, "boards": {}}
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
        built = {}
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
                    items, raw, route = route_rotary(items, at, body)
                else:
                    items = plate(lugs, pads, at, back)
                    raw, route = route_plate(items, body)
                fl = [fillet(w) for w in raw]
                dense = [f[0] for f in fl]
                c["route"] = route
                c["bend_radius"] = round(min(min_radius(d) for d in dense), 2)
                c["_items"], c["_dense"] = items, dense
            else:
                bodies = {b[0]: b for b in model["fascia_variants"][("F" if key == "A" else key)]["bodies"]}
                X0 = model["fascia_variants"]["F" if key == "A" else key]["X0"]
                raw, nets, bd = standin(ref, X0, bodies[ref], pads, at)
                dense = [fillet(w)[0] for w in raw]
                c["model"] = "standin"
                c["bend_radius"] = round(min(min_radius(d) for d in dense), 2)
                c["_nets"], c["_dense"], c["_body"] = nets, dense, bd
            built[ref] = c
        # the clearances, with every wire of the board in view: a wire of one control may not touch a wire of another
        all_dense = {r2: c2["_dense"] for r2, c2 in built.items()}
        for ref, c in built.items():
            dense = c["_dense"]
            others = [d for r2, ds in all_dense.items() if r2 != ref for d in ds]
            if c["model"] == "lugs":
                items = c["_items"]
                c["clearance"] = check(dense, c["lugs"], c["body"], [c["lugs"].index(it[0]) for it in items], others)
                c["wires"] = [{"net": it[1], "pad": it[2], "lug": {"x": it[0]["x"], "y": it[0]["y"]}, "level": c["route"][i]["level"], "turn": c["route"][i]["turn"],
                               "length": round(float(np.linalg.norm(np.diff(d, axis=0), axis=1).sum()), 1),
                               "pts": [[round(float(v), 3) for v in p] for p in d]} for i, (it, d) in enumerate(zip(items, dense))]
            else:
                c["clearance"] = check(dense, [], c.pop("_body"), [], others)
                c["wires"] = [{"net": n[0], "pad": n[1], "length": round(float(np.linalg.norm(np.diff(d, axis=0), axis=1).sum()), 1),
                               "pts": [[round(float(v), 3) for v in p] for p in d]} for n, d in zip(c["_nets"], dense)]
            for k in ("_items", "_dense", "_nets"):
                c.pop(k, None)
            info["controls"][ref] = c
        out["boards"][board] = info
    return out


def main(repo, data_dir, out):
    res = build(repo, data_dir)
    with open(out, "w", encoding="utf8") as fh:
        json.dump(res, fh, ensure_ascii=False, separators=(",", ":"))
    for b, info in res["boards"].items():
        for ref, c in info["controls"].items():
            ln = [w["length"] for w in c["wires"]]
            print("  %-20s %s %-7s %2d wires, %.0f-%.0f mm, bends r %.2f, %s" % (b, ref, c["model"], len(c["wires"]), min(ln), max(ln), c["bend_radius"],
                  ("lugs %d, clearance %s" % (len(c["lugs"]), c["clearance"])) if c["model"] == "lugs" else "(no lug model: from the stand-in body's back face) clearance %s" % c["clearance"]))


if __name__ == "__main__":
    main(*sys.argv[1:4])
