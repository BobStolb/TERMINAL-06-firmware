#!/usr/bin/env python3
"""How whole is the ground plane? A raster model of a KiCad zone fill, for comparing layouts.

    python3 tools/planecheck.py tools/mkpcb_drv_plane.py            # this board's B.Cu plane
    python3 tools/planecheck.py tools/mkpcb_drv.py --layer F.Cu     # the baseline's front pour

It imports the generator (placement, hand-laid copper), loads its saved routes (load_routes()),
and fills every GND zone the way KiCad does, on a 0.05 mm grid:
  * copper may go where it keeps max(zone clearance, the other net's class clearance) from every
    other net's pad and track on that face, the hole clearance from unplated holes, and stays
    inside the zone outline;
  * necks thinner than the zone's minimum width are removed (an opening by min_th / 2);
  * a GND pad joins the fill it touches (its thermal ring is counted as copper - optimistic by
    the spokes, which KiCad may drop where only one fits).
It then reports the islands (connected pieces of fill), the largest piece's share of all the
fill, the GND pads each piece reaches, any GND pad no piece reaches, and every stretch of
non-GND copper on the plane's face that is not a pad: the slots the hops cut.
"""
import importlib.util, math, os, sys
import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbkit as K

G = 0.05


def load(path):
    spec = importlib.util.spec_from_file_location("gen", path)
    saved = sys.argv
    sys.argv = [path]
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    sys.argv = saved
    m.load_routes()
    return m


def fill(B, layer, clearance, min_th, hole_clr=0.3, poly_inset=0.5):
    nx, ny = int(B.W / G) + 1, int(B.H / G) + 1
    X = (np.arange(nx) * G)[None, :]
    Y = (np.arange(ny) * G)[:, None]
    ok = (X >= poly_inset) & (X <= B.W - poly_inset) & (Y >= poly_inset) & (Y <= B.H - poly_inset)
    ok = np.broadcast_to(ok, (ny, nx)).copy()
    gnd = np.zeros((ny, nx), bool)
    cls = {k: c for k, c, _ in B.classes}

    def paint(pts, r, grow, mask, val):
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        reach = r + grow + G
        i0, i1 = max(0, int((min(xs) - reach) / G)), min(nx - 1, int((max(xs) + reach) / G) + 1)
        j0, j1 = max(0, int((min(ys) - reach) / G)), min(ny - 1, int((max(ys) + reach) / G) + 1)
        xx = np.broadcast_to(X[:, i0:i1 + 1], (j1 - j0 + 1, i1 - i0 + 1))
        yy = np.broadcast_to(Y[j0:j1 + 1, :], (j1 - j0 + 1, i1 - i0 + 1))
        d = K._dist_field(np, xx, yy, pts) - r
        mask[j0:j1 + 1, i0:i1 + 1][d < grow] = val

    for p in B.pads:
        if p.kind == "np_thru_hole" or not p.on(layer):
            continue
        pts, r = p.geom()
        if p.net == "GND":
            paint(pts, r, 0.5, gnd, True)            # the pad and its thermal ring
        else:
            paint(pts, r, max(clearance, cls[B.cls(p.net or "")]), ok, False)
    slots = []
    for net, ly, a, b, w in B.tracks:
        if ly != layer:
            continue
        if net == "GND":
            paint([a, b], w / 2, 0.0, gnd, True)
        else:
            paint([a, b], w / 2, max(clearance, cls[B.cls(net)]), ok, False)
            slots.append((net, a, b, w))
    for hx, hy, hd in B.holes + [(p.x, p.y, p.drill) for p in B.pads if p.kind == "np_thru_hole"]:
        paint([(hx, hy)], hd / 2, hole_clr, ok, False)
    # the minimum width: an opening by min_th / 2
    rad = max(1, int(round(min_th / 2 / G)))
    yy, xx = np.mgrid[-rad:rad + 1, -rad:rad + 1]
    disk = (xx ** 2 + yy ** 2) <= rad ** 2
    ok = ndimage.binary_opening(ok, structure=disk)
    cu = ok | gnd
    lab, n = ndimage.label(cu, structure=np.ones((3, 3)))
    return lab, n, ok, gnd, slots


def pieces_of(slots):
    """Join back-face track segments of one net that touch into runs; a run's length is the slot."""
    runs = []
    by = {}
    for s in slots:
        by.setdefault(s[0], []).append(s)
    for net, segs in by.items():
        par = list(range(len(segs)))

        def f(i):
            while par[i] != i:
                par[i] = par[par[i]]
                i = par[i]
            return i
        for i in range(len(segs)):
            for j in range(i + 1, len(segs)):
                if K.dist(([segs[i][1], segs[i][2]], 0), ([segs[j][1], segs[j][2]], 0)) < 1e-3:
                    par[f(i)] = f(j)
        grp = {}
        for i, s in enumerate(segs):
            grp.setdefault(f(i), []).append(s)
        for g in grp.values():
            L = sum(math.dist(a, b) for _, a, b, _ in g)
            xs = [c for _, a, b, _ in g for c in (a[0], b[0])]
            ys = [c for _, a, b, _ in g for c in (a[1], b[1])]
            runs.append((L, net, (round(min(xs), 1), round(min(ys), 1), round(max(xs), 1), round(max(ys), 1)), len(g)))
    return sorted(runs, reverse=True)


def report(B, layer="B.Cu"):
    zs = [z for z in B.zones if z["net"] == "GND" and z["layer"] == layer]
    z = zs[0] if zs else dict(clearance=0.5, min_th=0.3)
    lab, n, ok, gnd, slots = fill(B, layer, z["clearance"], z["min_th"])
    sizes = ndimage.sum(np.ones_like(lab), lab, index=range(1, n + 1)) * G * G
    gpads = [p for p in B.pads if p.net == "GND" and p.on(layer) and p.kind != "np_thru_hole"]
    reach = {}
    lost = []
    for p in gpads:
        k = lab[int(round(p.y / G)), int(round(p.x / G))]
        if k == 0:
            lost.append(f"{p.ref}.{p.name}")
        reach.setdefault(k, []).append(f"{p.ref}.{p.name}")
    big = int(np.argmax(sizes)) + 1
    total = float(sizes.sum())
    with_pad = sorted((k for k in reach if k), key=lambda k: -sizes[k - 1])
    out = {
        "layer": layer, "zone clearance": z["clearance"], "zone min width": z["min_th"],
        "fill area mm2": round(total), "board area mm2": round(B.W * B.H),
        "islands": int(n), "islands with a GND pad": len(with_pad),
        "largest island share": round(float(sizes[big - 1]) / total, 4),
        "GND pads": len(gpads), "GND pads on the largest island": len(reach.get(big, [])),
        "GND pads on no fill": lost,
        "GND pads off the largest island": sorted(set(sum((reach[k] for k in with_pad if k != big), []))),
        "hop runs": pieces_of(slots),
    }
    return out


if __name__ == "__main__":
    path = sys.argv[1]
    layer = sys.argv[sys.argv.index("--layer") + 1] if "--layer" in sys.argv else "B.Cu"
    m = load(path)
    B = m.B
    if not any(z["net"] == "GND" and z["layer"] == layer for z in B.zones):
        if "mkpcb_drv_plane" in path:
            B.zone("GND", "B.Cu", clearance=0.25, min_th=0.25, gap=0.5, bridge=0.5)
        else:                                   # the baseline pours both faces at 0.5 / 0.3
            B.zone("GND", "F.Cu", clearance=0.5, min_th=0.3, gap=0.5, bridge=0.5)
            B.zone("GND", "B.Cu", clearance=0.5, min_th=0.3, gap=0.5, bridge=0.5)
    if "--score" in sys.argv:
        L = sum(math.dist(a, b) for _, _, a, b, _ in B.tracks)
        ax = sum(math.dist(a, b) for _, _, a, b, _ in B.tracks if abs(a[0] - b[0]) < 1e-3 or abs(a[1] - b[1]) < 1e-3)
        byl = {}
        for _, ly, a, b, _ in B.tracks:
            byl[ly] = byl.get(ly, 0) + math.dist(a, b)
        dips = {(f.rot % 360) for r, (f, x, y) in B.placed.items() if "DIP" in f.name}
        print(f"track length {L:.0f} mm ({', '.join(f'{k} {v:.0f}' for k, v in sorted(byl.items()))}), "
              f"{len(B.tracks)} segments, axis-aligned {100 * ax / L:.1f}%, hand-laid {len(getattr(m, 'FIXED', ()))}, "
              f"DIP rotations {sorted(dips)}")
    r = report(B, layer)
    for k, v in r.items():
        if k == "hop runs":
            print(f"{k}: {len(v)} runs, {sum(x[0] for x in v):.1f} mm in all, longest {v[0][0] if v else 0:.1f} mm")
            for L, net, box, ns in v[:40]:
                print(f"    {L:6.1f} mm  {net:12s} {ns:3d} seg  box {box}")
        elif isinstance(v, list):
            print(f"{k}: {len(v)}  {' '.join(v[:30])}")
        else:
            print(f"{k}: {v}")
