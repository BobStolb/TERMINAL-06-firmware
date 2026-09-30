#!/usr/bin/env python3
"""Power entry for the TERMINAL-06 case: every option the owner asked about, worked out from the case model.

    python3 3d/case-pair/power-options/power_options.py            numbers.json + the drawings (PNG) here
    python3 3d/case-pair/power-options/power_options.py --render   also the OpenSCAD pictures (xvfb-run)

It reads the case model (3d/case-pair/case_pair.py, default numbers, nothing changed) and the driver
board (PCB/TS06-DRV/TS06-DRV.kicad_pcb), and writes only into this folder. The committed case outputs
(params.scad, checks.md, out/) are not touched.

Every number carries its kind, the case model's four plus two:
    model     read from case_pair.py's derived numbers (board / doc / design there)
    assumed   the case model's own assumed plug numbers (barrel 9.5, nose Ø10, 7 mm needed)
    board     read from the TS06-DRV board file
    seen      in a web-search excerpt of a datasheet or a distributor's page. The pages themselves
              could not be opened from here (the network policy refused them), so no drawing was looked at
    computed  worked out here from the numbers above
    inferred  reasoning, not checked against a part
"""
import json, math, os, sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
CASE = os.path.dirname(HERE)
ROOT = os.path.normpath(os.path.join(CASE, "..", ".."))
sys.path.insert(0, CASE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import case_pair as CP          # noqa: E402  (main() is guarded: importing writes nothing)
import sexp                     # noqa: E402

DRV_PCB = os.path.join(ROOT, "PCB", "TS06-DRV", "TS06-DRV.kicad_pcb")


# ============================================================================ the model
def model():
    with open(os.path.join(CASE, "boards.json"), encoding="utf8") as fh:
        B = json.load(fh)
    d = CP.dims(B)
    G = CP.derive(B, d)
    CP.profiles(G)
    CP.fixings(G)
    return G


# ============================================================================ the plug in the cheek
# A cut through the cheek is a list of (depth from the outside face, to depth, opening Ø). The plug's
# nose (overmould) stops at the first depth, going in, where the opening is smaller than the nose; if
# nothing stops it, it goes on until it meets the jack's own face, and the whole barrel is in.
def engagement(v, cut, nose=None):
    nose = v["PLUG_NOSE_D"] if nose is None else nose
    gap = v["X_IN_R"] - v["JACK_MOUTH_X"]                  # jack mouth to the cheek's inner face
    for d0, d1, dia in cut:
        if dia < nose:
            t_stop = v["CHEEK_T"] - d0                     # cheek left between the stop and the inner face
            return round(max(0.0, v["PLUG_BARREL_L"] - (gap + t_stop)), 2), round(gap + t_stop, 2)
    return v["PLUG_BARREL_L"], 0.0                         # seated on the jack face


def cheek_options(v):
    T = v["CHEEK_T"]
    W = v["JACK_WEB"]
    A = []
    A.append(dict(id="K0", name="Plain 6 mm cheek, Ø9 hole", cut=[(0, T, v["JACK_HOLE_D"])],
                  change="none", note="the reference: the plug stops on the outer face"))
    A.append(dict(id="K-model", name="The model now: Ø14 pocket from outside, 1.5 web, Ø9",
                  cut=[(0, T - W, v["JACK_CB_D"]), (T - W, T, v["JACK_HOLE_D"])],
                  change="cheek only", note="the earlier review's option 3"))
    A.append(dict(id="A1", name="Clear hole Ø11 straight through", cut=[(0, T, 11.0)],
                  change="cheek only", note="the nose passes; the barrel seats on the jack face"))
    A.append(dict(id="A2", name="Slot 11 wide, open to the rear edge (right-angle plug)", cut=[(0, T, 11.0)],
                  change="cheek only", note="same section as A1; the cable runs back along the slot"))
    A.append(dict(id="A3", name="Recessed well Ø18 x 5 deep, 1.0 web, Ø9", cut=[(0, T - 1.0, 18.0), (T - 1.0, T, 9.0)],
                  change="cheek only", note="any nose Ø9-18 stops on the web"))
    A.append(dict(id="A4", name="Stepped counterbore Ø16 x 2 + Ø11 through", cut=[(0, 2.0, 16.0), (2.0, T, 11.0)],
                  change="cheek only", note="a Ø10 nose passes both steps"))
    A.append(dict(id="B1", name="Hatch cap over a right-angle plug (Ø11 hole)", cut=[(0, T, 11.0)],
                  change="cheek + a screwed cap", note="the cap does not touch the plug"))
    A.append(dict(id="B2", name="Removable metal panel 1.5 flush inside, Ø9", cut=[(0, T - 1.5, 22.0), (T - 1.5, T, 9.0)],
                  change="cheek window + 1.5 aluminium plate", note="metal web: no printed-web doubt"))
    A.append(dict(id="B2-1.0", name="Removable metal panel 1.0 flush inside, Ø9", cut=[(0, T - 1.0, 22.0), (T - 1.0, T, 9.0)],
                  change="cheek window + 1.0 aluminium plate", note=""))
    noses = [8.0, 9.5, 10.0, 11.5, 13.0, 15.0, 17.0]
    for o in A:
        o["engaged"], o["stop_from_mouth"] = engagement(v, o["cut"])
        o["ok"] = o["engaged"] >= v["JACK_ENGAGE_MIN"]
        o["by_nose"] = {"%g" % n: engagement(v, o["cut"], n)[0] for n in noses}
    return A


# ============================================================================ the connectors
# (name, the numbers and where each came from). Lengths behind the panel are not in any excerpt seen.
CONNECTORS = {
    "2RM14": dict(
        title="2РМ14 (4 contacts, bayonet)",
        panel_part="2РМ14Б4Ш1В1 (block, 4 pins)", cable_part="2РМ14КПН4Г1В1 (cable, 4 sockets, straight nozzle)",
        flange=24.0, holes=17.0, hole_d=3.2, cut_d=16.0, front=12.0, rear=13.0, body_d=16.0, overall=25.0,
        amps=8.0, amps_total=27.0, volts=560, contacts="4 x Ø1.0",
        seen=["flange 24 (B), hole spacing 17 (A), L max 25, seat M14x1: the 2РМ table (search excerpts, twice)",
              "4 contacts Ø1.0, 8 A each, 27 A total, 560 V: distributor pages (search excerpts)",
              "cable part takes cores up to 0.5 mm²; nozzle П straight, У angled; Ш pin, Г socket",
              "cable parts listed with 2023 and 2025-26 production years (listing titles)"],
        inferred=["flange hole Ø3.2 (M3) - the excerpt gives no hole size", "25 split as about 12 ahead of the flange and 13 behind",
                  "body behind the flange Ø16 (the M16x1 figure in the excerpt)", "bayonet coupling, keyed shell"]),
    "SHR20": dict(
        title="ШР20 (4 contacts Ø2.5, threaded)",
        panel_part="ШР20П4ЭШ8 (block, 4 pins)", cable_part="ШР20П4НГ8 (cable, 4 sockets)",
        flange=30.0, holes=22.0, hole_d=3.2, cut_d=20.0, front=14.0, rear=20.0, body_d=20.0, overall=None,
        amps=25.0, amps_total=100.0, volts=850, contacts="4 x Ø2.5",
        seen=["flange 30 (B), hole spacing 22 ±0.1 (A), holes Ø3.2 (d), body Ø20 (D), coupling M24x1.5: search excerpts",
              "4 contacts Ø2.5, 25 A each, 100 A total, 850 V; cable part no more than 37 g: search excerpts"],
        inferred=["about 14 ahead of the flange and 20 behind it: no length seen", "Э/Н (screened or not) do not change the mating face"]),
    "DIN5": dict(
        title="ОНЦ-ВГ-4-5/16-р (СГ-5, DIN 5-pin)",
        panel_part="ОНЦ-ВГ-4-5/16-р (block socket)", cable_part="ОНЦ-ВГ-4-5/16-в (cable plug, СШ-5)",
        flange=29.0, flange_h=20.6, holes=22.0, hole_d=3.2, cut_d=15.5, front=3.0, rear=16.0, body_d=16.0, overall=19.0,
        amps=2.0, amps_total=None, volts=34, contacts="5",
        seen=["overall 29 x 20.6 x 19, 5 contacts, 2 A, 34 V, two M3 screws: search excerpts",
              "block sockets listed with 2019-20 production (listing title), maker Копир"],
        inferred=["hole spacing 22 and a Ø15.5 cut-out: the usual DIN flange, not seen for this part",
                  "the same socket family carries audio: a tape-deck lead fits it"]),
    "DCJ": dict(
        title="Panel DC jack 5.5 x 2.1 (threaded bush)",
        panel_part="panel jack, threaded bush, nut", cable_part="the adapter's own 5.5 x 2.1 plug",
        flange=None, holes=None, hole_d=None, cut_d=12.7, front=2.0, rear=17.0, body_d=12.0, overall=None,
        amps=1.0, amps_total=None, volts=30, contacts="2 + switch",
        seen=["bush 0.45 in (11.4), panel hole 0.5 in (12.7): a seller's page (search excerpt)",
              "a DC-005 panel jack: 1 A, 30 V; long-bush kinds take panels up to 16 mm: search excerpts"],
        inferred=["about 17 behind the panel", "3-5 A kinds exist; 1 A is still 2.5x the clock's 0.4 A"]),
}


# ============================================================================ behind the rear panel
def rear_space(G, fitted_xs1=False):
    """Parts on TS06-DRV's rear face (world boxes, heights), plus the screw heads there."""
    v = G["v"]
    parts = [(ref, box, h) for ref, fp, box, h, side, src in G["drv_parts"] if side == 0 and (fitted_xs1 or ref != "XS1")]
    head = v["SCREW_HEAD"] + v["MOD_WASHER_T"]
    for name, x, y, dia in G["B"]["drv"]["holes"]:
        r = v["SCREW_HEAD_D"] / 2
        parts.append(("screw " + name, [x - r, x + r, y - r, y + r], head))
    return parts


def disk_max_h(parts, cx, cy, r, margin=1.0):
    hmax, who = 0.0, None
    for ref, (x0, x1, y0, y1), h in parts:
        dx = max(x0 - cx, 0, cx - x1)
        dy = max(y0 - cy, 0, cy - y1)
        if math.hypot(dx, dy) < r + margin and h > hmax:
            hmax, who = h, ref
    return hmax, who


def place(G, key, cx, cy, parts):
    v = G["v"]
    c = CONNECTORS[key]
    room_z = v["Z_REAR_IN"] - v["Z_DRV_B"]                             # model: 25.0
    r = c["body_d"] / 2
    hmax, who = disk_max_h(parts, cx, cy, r)
    bend = 5.0                                                          # inferred: solder cup + wire bend
    need = c["rear"] + bend
    room = room_z - hmax
    fl = (c.get("flange") or c["cut_d"]) / 2
    flh = (c.get("flange_h") or c.get("flange") or c["cut_d"]) / 2
    lips = G["rear_lips"]
    issues = []
    if cy + r > lips["top plate"][0]:
        issues.append("body into the top plate's lip (Y > %.1f)" % lips["top plate"][0])
    if cy - r < lips["base"][1]:
        issues.append("body into the base's lip (Y < %.1f)" % lips["base"][1])
    if cx + r > v["X_IN_R"]:
        issues.append("body into the right cheek (X > %.1f)" % v["X_IN_R"])
    for sx, sy in G["rear_screws"]:
        dx = max(abs(sx - cx) - fl, 0)
        dy = max(abs(sy - cy) - flh, 0)
        if math.hypot(dx, dy) < v["SCREW_HEAD_D"] / 2 + 0.5:
            issues.append("flange over the rear screw at %.1f, %.1f" % (sx, sy))
    if cx + fl > v["X_OUT_R"] or cy + flh > v["Y_TOP"]:
        issues.append("flange past the panel's edge")
    # the lead: from the solder cups to XS1's pads 1 and 2, on the board's rear face
    pads = [p for p in G["B"]["drv"]["parts"]["XS1"]["pads"] if p[0] in ("1", "2")]
    z_cup = v["Z_REAR_IN"] - c["rear"]
    runs = [abs(z_cup - v["Z_DRV_B"]) + abs(cx - px) + abs(cy - py) for n, px, py in pads]
    return dict(key=key, at=[cx, cy], body_r=r, h_under=hmax, tallest=who, room=round(room, 2), need=need,
                margin=round(room - need, 2), issues=issues, lead_min=round(max(runs), 1),
                lead_cut=round(max(runs) + 60.0, 0), ok=room >= need and not issues)


# ============================================================================ the board file
def board():
    t = sexp.parse(open(DRV_PCB, encoding="utf8").read())
    root = t[0] if isinstance(t[0], list) else t
    find = lambda n, k: [c for c in n if isinstance(c, list) and c and c[0] == k]
    unq = lambda s: s.strip('"') if isinstance(s, str) else s

    def xf(at, x, y):
        ax, ay = float(at[1]), float(at[2])
        r = math.radians(float(at[3])) if len(at) > 3 else 0.0
        return ax + x * math.cos(r) + y * math.sin(r), ay - x * math.sin(r) + y * math.cos(r)

    fps, pads = {}, []
    for fp in find(root, "footprint"):
        at = find(fp, "at")[0]
        ref = [unq(p[2]) for p in find(fp, "property") if unq(p[1]) == "Reference"][0]
        pts = []
        for ln in find(fp, "fp_line") + find(fp, "fp_rect") + find(fp, "fp_circle") + find(fp, "fp_poly"):
            ly = find(ln, "layer")
            if ly and unq(ly[0][1]).endswith("CrtYd"):
                if ln[0] == "fp_circle":                   # a circle: its centre plus and minus its radius
                    c, e = find(ln, "center")[0], find(ln, "end")[0]
                    cx, cy = float(c[1]), float(c[2])
                    r = math.hypot(float(e[1]) - cx, float(e[2]) - cy)
                    pts += [xf(at, cx + dx, cy + dy) for dx, dy in ((r, 0), (-r, 0), (0, r), (0, -r))]
                    continue
                for k in ("start", "end"):
                    for s in find(ln, k):
                        pts.append(xf(at, float(s[1]), float(s[2])))
                for pp in find(ln, "pts"):
                    for xy in find(pp, "xy"):
                        pts.append(xf(at, float(xy[1]), float(xy[2])))
        for p in find(fp, "pad"):
            pat = find(p, "at")[0]
            x, y = xf(at, float(pat[1]), float(pat[2]))
            net = find(p, "net")
            dr = find(p, "drill")
            sz = find(p, "size")[0]
            pads.append(dict(ref=ref, n=unq(p[1]), x=round(x, 3), y=round(y, 3), net=unq(net[0][-1]) if net else None,
                             drill=[c for c in dr[0][1:] if not isinstance(c, list)] if dr else None,
                             w=float(sz[1]), h=float(sz[2])))
        if pts:
            xs, ys = [q[0] for q in pts], [q[1] for q in pts]
            fps[ref] = dict(fp=unq(fp[1]), at=[float(a) for a in at[1:]], crt=[min(xs), max(xs), min(ys), max(ys)])
    names = {c[1]: unq(c[2]) for c in find(root, "net") if len(c) > 2}
    tracks = []
    for c in find(root, "segment"):
        s, e = find(c, "start")[0], find(c, "end")[0]
        n = find(c, "net")
        tracks.append(dict(a=(float(s[1]), float(s[2])), b=(float(e[1]), float(e[2])), w=float(find(c, "width")[0][1]),
                           layer=unq(find(c, "layer")[0][1]), net=names.get(n[0][1]) if n else None))
    return dict(fps=fps, pads=pads, tracks=tracks)


def seg_dist(p, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
    return math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy)


def seg_rect(a, b, x0, x1, y0, y1):
    """Distance from segment a-b to the rectangle (0 if they meet)."""
    inside = lambda p: x0 <= p[0] <= x1 and y0 <= p[1] <= y1
    if inside(a) or inside(b):
        return 0.0
    def cross(p, q, r, s):
        d = lambda u, v, w: (v[0] - u[0]) * (w[1] - u[1]) - (v[1] - u[1]) * (w[0] - u[0])
        return d(p, q, r) * d(p, q, s) < 0 and d(r, s, p) * d(r, s, q) < 0
    C = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    if any(cross(a, b, C[i], C[(i + 1) % 4]) for i in range(4)):
        return 0.0
    pr = lambda p: math.hypot(max(x0 - p[0], 0, p[0] - x1), max(y0 - p[1], 0, p[1] - y1))
    return min(pr(a), pr(b), *[seg_dist(c, a, b) for c in C])


def free_rects(BD, w, h, x_rng, y_rng, skip=("XS1",), skip_nets=(), clr=0.5, step=0.5):
    """Board-frame positions where a w x h courtyard (a new THT header) touches no courtyard, pad or track.
    THT pads go through both layers, so tracks on either layer block, except skip_nets (the header's own)."""
    boxes = [f["crt"] for r, f in BD["fps"].items() if r not in skip]
    pads = [p for p in BD["pads"] if p["ref"] not in skip]
    out = []
    y = y_rng[0]
    while y + h <= y_rng[1] + 1e-9:
        x = x_rng[0]
        while x + w <= x_rng[1] + 1e-9:
            ok = x >= 0.5 and y >= 0.5 and x + w <= 190.9 and y + h <= 99.5
            if ok:
                for b in boxes:
                    if b[0] < x + w + clr and b[1] > x - clr and b[2] < y + h + clr and b[3] > y - clr:
                        ok = False
                        break
            if ok:
                for p in pads:
                    if abs(p["x"] - (x + w / 2)) < w / 2 + p["w"] / 2 + clr and abs(p["y"] - (y + h / 2)) < h / 2 + p["h"] / 2 + clr:
                        ok = False
                        break
            if ok:
                for t in BD["tracks"]:
                    if t["net"] not in skip_nets and seg_rect(t["a"], t["b"], x, x + w, y, y + h) < t["w"] / 2 + clr:
                        ok = False
                        break
            if ok:
                out.append((round(x, 2), round(y, 2)))
            x += step
        y += step
    return out


# ============================================================================ main
def main():
    G = model()
    v = G["v"]
    N = {"_about": "Written by power_options.py from the case model (default numbers) and TS06-DRV.kicad_pcb.",
         "model": {k: v[k] for k in ("CHEEK_T", "X_IN_R", "X_OUT_R", "JACK_MOUTH_X", "JACK_Y", "JACK_Z", "Z_DRV_B",
                                     "Z_REAR_IN", "Z_REAR_OUT", "REAR_T", "PLUG_BARREL_L", "PLUG_NOSE_D",
                                     "JACK_ENGAGE_MIN", "JACK_HOLE_D", "JACK_CB_D", "JACK_WEB", "Y_TOP", "Y_BOT",
                                     "TOP_LIP_Y0", "OUT_W", "OUT_H", "OUT_D")}}
    gap = v["X_IN_R"] - v["JACK_MOUTH_X"]
    N["rule"] = dict(gap=round(gap, 2), t_stop_max=round(v["PLUG_BARREL_L"] - v["JACK_ENGAGE_MIN"] - gap, 2),
                     text="the nose must be able to reach within this much of the cheek's inner face")
    A = cheek_options(v)
    N["cheek"] = [{k: o[k] for k in ("id", "name", "engaged", "stop_from_mouth", "ok", "by_nose", "change", "note")} for o in A]
    # hatch cap: how proud of the cheek a right-angle plug's elbow sits (elbow Ø11 across X: assumed like the nose)
    elbow = 11.0
    out_x = v["JACK_MOUTH_X"] + elbow                   # seated: its tip on the jack face
    N["hatch"] = dict(elbow_assumed=elbow, elbow_proud=round(out_x - v["X_OUT_R"], 2),
                      cap_proud=round(out_x - v["X_OUT_R"] + 0.5 + 1.5, 2))
    # the slot, open to the rear edge
    N["slot"] = dict(width=11.0, z0=round(v["JACK_Z"] - 5.5, 2), z1=v["Z_REAR_IN"], length=round(v["Z_REAR_IN"] - v["JACK_Z"] + 5.5, 2))
    # behind the rear panel
    parts = rear_space(G)
    N["rear_room_z"] = round(v["Z_REAR_IN"] - v["Z_DRV_B"], 2)
    P_HI = (182.5, v["JACK_Y"])        # over XS1's freed place: the shortest lead
    P_MID = (178.0, 49.5)              # the empty patch X 167-191, Y 24-60, clear of the H2 screw head and U16
    N["rear"] = [place(G, "2RM14", *P_HI, parts), place(G, "DCJ", *P_HI, parts), place(G, "DIN5", *P_HI, parts),
                 place(G, "SHR20", *P_HI, parts), place(G, "SHR20", *P_MID, parts), place(G, "2RM14", *P_MID, parts)]
    # the long-bush jack through the right cheek, its axis raised clear of the board
    ax_z = 57.0
    N["cheek_jack"] = dict(axis_y=v["JACK_Y"], axis_z=ax_z, above_board=round(ax_z - v["Z_DRV_B"], 2),
                           below_rear=round(v["Z_REAR_IN"] - ax_z, 2), body_d=12.0, rear=17.0,
                           body_x0=round(v["X_IN_R"] - 17.0, 2))
    bz0 = ax_z - 6.0
    hits = [(ref, round(v["Z_DRV_B"] + h, 2)) for ref, (x0, x1, y0, y1), h in parts
            if x1 > v["X_IN_R"] - 17.0 and y0 < v["JACK_Y"] + 6 and y1 > v["JACK_Y"] - 6 and v["Z_DRV_B"] + h > bz0]
    N["cheek_jack"]["collisions"] = hits
    # the left cheek: how far the lead runs
    N["left_cheek_lead"] = round(abs(v["X_IN_L"] - 180.4) + 30 + 60, 0)
    # the board
    BD = board()
    xs1 = [p for p in BD["pads"] if p["ref"] == "XS1"]
    N["xs1_pads"] = xs1
    DW, YD = G["B"]["drv"]["W"], v["DRV_TOP_Y"]
    N["xs1_pads_world"] = [(p["n"], round(DW - p["x"], 2), round(YD - p["y"], 2), p["net"]) for p in xs1]
    N["h7"] = [h for h in G["B"]["drv"]["holes"] if h[0] == "H7"][0]
    # rev C: where a 2-pin header could go near the right end, XS1 kept (both fitted) or dropped
    HDR = {"JST VH 2-pin (B2P-VH, 3.96)": (8.8, 9.8), "JST XH 2-pin (B2B-XH-A, 2.5)": (7.4, 6.3)}
    N["free"] = {}
    for name, (w, h) in HDR.items():
        keep = free_rects(BD, w, h, (0, 40), (0, 100), skip=())
        x0, x1, y0, y1 = BD["fps"]["XS1"]["crt"]
        drop = free_rects(BD, w, h, (x0, x1), (y0, y1), skip=("XS1",), skip_nets=("VIN_J", "GND"))
        N["free"][name] = dict(size=[w, h], with_xs1=len(keep), with_xs1_first=keep[:6],
                               in_xs1_place=len(drop), in_xs1_place_first=drop[:4])
    with open(os.path.join(HERE, "numbers.json"), "w", encoding="utf8") as fh:
        json.dump(N, fh, indent=1, ensure_ascii=False)
    # the report
    print("gap jack mouth to cheek %.2f; nose must reach within %.2f of the inner face" % (gap, N["rule"]["t_stop_max"]))
    for o in N["cheek"]:
        print("  %-8s %-58s %4.1f mm %s   by nose %s" % (o["id"], o["name"], o["engaged"], "OK  " if o["ok"] else "FAIL",
                                                         " ".join("%s:%g" % kv for kv in o["by_nose"].items())))
    print("hatch:", N["hatch"])
    print("slot:", N["slot"])
    print("rear room %.1f" % N["rear_room_z"])
    for r in N["rear"]:
        print("  %-6s at %-14s h_under %4.1f (%s) room %4.1f need %4.1f margin %5.1f lead %5.1f (cut %g) %s %s"
              % (r["key"], r["at"], r["h_under"], r["tallest"], r["room"], r["need"], r["margin"], r["lead_min"],
                 r["lead_cut"], "OK" if r["ok"] else "NO", "; ".join(r["issues"])))
    print("cheek jack:", N["cheek_jack"])
    print("XS1 pads (world):", N["xs1_pads_world"], " H7:", N["h7"])
    for k, f in N["free"].items():
        print("  %s: %d spots with XS1 kept (first %s); %d in XS1's place (first %s)"
              % (k, f["with_xs1"], f["with_xs1_first"][:3], f["in_xs1_place"], f["in_xs1_place_first"][:2]))
    if "--draw" in sys.argv or "--render" in sys.argv or len(sys.argv) == 1:
        import sheets
        sheets.draw_all(G, N, BD, CONNECTORS, HERE)
    if "--render" in sys.argv:
        import sheets
        sheets.render(HERE)
    return G, N, BD


if __name__ == "__main__":
    sys.path.insert(0, HERE)
    main()
