#!/usr/bin/env python3
"""The fit table: how tall the parts are on each board, as drawn, against the room the case model gives them.

    python3 tools/fit_table.py GLBDIR OUT.md [OUT.json] [--fascia TS06-FASCIA-rhythm] [--gold divider]

GLBDIR holds the three populated GLBs of tools/render_populated.py. Every number in a row comes from the models as
placed on the boards (the bounding box of each part's meshes in the GLB, in the board's own frame: u = 0 on the
board's back face, the component face at u = thickness) or, for the space, from 3d/case-pair/case_pair.py's own
derived geometry (tools/stack_frame.py: the same dims() and derive() the case drawings and checks use).

Columns: part, height, space, margin, PASS | TIGHT | FAIL.
    margin = space - height (a clearance row: the gap itself).
    PASS   margin >= 1 mm
    TIGHT  margin < 1 mm
    FAIL   margin < -0.25 mm: an interference bigger than the rounding in the sources (PLS body 2.5 against the model's 2.54, ...)
Where the model and case_pair.py disagree about a part's size the row says so ("case_pair assumes ...").
The control holes are read from the fascia board (the footprints' drills), not typed here. After the tally comes the
holes04 variant (fab/HOLES-VARIANT.md): the same three bushing rows with every control hole opened 0.4 mm, read from the
board `tools/mkpcb_fascia_rhythm.py --open-holes` writes. Those rows are shown beside the table, not in it: the tally, the
rows of fit-table.json and everything else stay what the committed board gives (tools/stack_frame.py has the helpers).
Needs numpy.
"""
import json, math, os, struct, sys, tempfile
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import stack_frame as SF  # noqa: E402

FAIL_BELOW = -0.25


def glb_parts(path):
    """{ref: vertices (n x 3, mm) in the board frame (x, u, zg)} for every placed part; board layers are left out."""
    b = open(path, "rb").read()
    off, js, binc = 12, None, b""
    while off < len(b):
        ln, typ = struct.unpack("<I4s", b[off:off + 8])
        ch = b[off + 8:off + 8 + ln]
        if typ == b"JSON":
            js = json.loads(ch)
        elif typ == b"BIN\x00":
            binc = ch
        off += 8 + ln
    nodes = js["nodes"]

    def accessor(i):
        a = js["accessors"][i]
        bv = js["bufferViews"][a["bufferView"]]
        start = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        stride = bv.get("byteStride") or 12
        raw = np.frombuffer(binc, dtype=np.uint8, count=stride * (a["count"] - 1) + 12, offset=start)
        idx = (np.arange(a["count"])[:, None] * stride + np.arange(12)[None, :])
        return raw[idx].copy().view(np.float32).reshape(a["count"], 3).astype(float)

    def mat(nd):
        if "matrix" in nd:
            return np.array(nd["matrix"], dtype=float).reshape(4, 4).T
        m = np.eye(4)
        if "scale" in nd:
            m = np.diag(list(nd["scale"]) + [1.0]) @ m
        if "rotation" in nd:
            x, y, z, w = nd["rotation"]
            R = np.eye(4)
            R[:3, :3] = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                         [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                         [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]
            m = R @ m
        if "translation" in nd:
            T = np.eye(4)
            T[:3, 3] = nd["translation"]
            m = T @ m
        return m

    out = {}

    def rec(i, M, path):
        nd = nodes[i]
        Mn = M @ mat(nd)
        p = path + [nd.get("name", "")]
        if "mesh" in nd and len(p) > 2:
            ref = p[1]
            for prim in js["meshes"][nd["mesh"]]["primitives"]:
                pos = accessor(prim["attributes"]["POSITION"])
                h = np.hstack([pos, np.ones((len(pos), 1))]) @ Mn.T
                out.setdefault(ref, []).append(h[:, :3] * 1000.0)
        for c in nd.get("children", []):
            rec(c, Mn, p)
    for r in js["scenes"][0]["nodes"]:
        rec(r, np.eye(4), [])
    return {k: np.vstack(v) for k, v in out.items()}


def status(margin):
    margin = round(margin, 2)
    return "FAIL" if margin < FAIL_BELOW else ("TIGHT" if margin < 1.0 else "PASS")


def main(argv):
    glbdir, outmd = argv[1], argv[2]
    outjson = argv[3] if len(argv) > 3 and not argv[3].startswith("--") else None
    fascia = argv[argv.index("--fascia") + 1] if "--fascia" in argv else "TS06-FASCIA-rhythm"
    gold = argv[argv.index("--gold") + 1] if "--gold" in argv else "none"       # the fascia as ordered (see stack_frame.py)
    cp, B, d, G = SF.geometry(fascia, gold)
    v = G["v"]
    M = SF.matrices(G)
    disp = glb_parts(os.path.join(glbdir, "TS06-DISP-populated.glb"))
    drv = glb_parts(os.path.join(glbdir, "TS06-DRV-populated.glb"))
    fas = glb_parts(os.path.join(glbdir, fascia + "-populated.glb"))
    T = v["PCB_T"]
    TF = v["FASCIA_T"]
    fp_of = {r: p["fp"] for r, p in B["drv"]["parts"].items()}
    fp_of.update({r: p["fp"] for r, p in B["disp"]["parts"].items()})
    case_h = {p[0]: p[3] for p in G["drv_parts"]}
    rows = []

    def add(board, side, part, height, space, note="", what="height"):
        m = space - height
        rows.append({"board": board, "side": side, "part": part, "height": round(height, 2), "space": round(space, 2),
                     "margin": round(m, 2), "status": status(m), "note": note, "what": what})

    def top(parts, ref, face):
        return parts[ref][:, 1].max() - face

    def bottom(parts, ref):
        return -parts[ref][:, 1].min()

    # ---------------------------------------------------------------- DRV component side: against the rear panel
    space = v["Z_REAR_IN"] - v["Z_DRV_B"]
    tall = sorted(((top(drv, r, T), r) for r in drv if top(drv, r, T) > 1.0), reverse=True)
    seen = set()
    for h, r in tall:
        key = fp_of.get(r, r)
        if key in seen:
            continue
        seen.add(key)
        if len(seen) > 8:
            break
        cph = case_h.get(r)
        note = "case_pair assumes %.1f" % cph if cph is not None and abs(cph - h) > 0.6 else ""
        add("TS06-DRV", "component face", r + " " + key.replace("TS06_", ""), h, space, note)
    if "C7" in drv:
        add("TS06-DRV", "component face", "C7 CP_Radial_D10.0mm_P5.00mm (4u7 / 400 V)", top(drv, "C7", T), space,
            "case_pair assumes %.1f (pair review finding 6: 16-20 mm for the real part); the KiCad radial model is only %.1f tall, so "
            "the other rows understate the real part" % (case_h.get("C7", 0), top(drv, "C7", T)))
        add("TS06-DRV", "component face", "C7 at case_pair's %.1f mm" % case_h.get("C7", 0), case_h.get("C7", 0), space, "")
    # ---------------------------------------------------------------- DRV display-facing side: the strips and J1
    for r in ("XS12", "J1"):
        if r in drv:
            add("TS06-DRV", "display-facing face", r + " " + fp_of.get(r, r).replace("TS06_", ""), bottom(drv, r), v["STACK_GAP"],
                "" if r != "J1" else "the mated PHR-6 plug is not drawn; case_pair assumes %.1f above the face" % cp.dims(B).v["J1_MATED_H"])
    xs_depth = max(bottom(drv, r) for r in drv if r.startswith("XS"))
    xp_body = 2.54
    add("TS06-DISP + TS06-DRV", "between the boards", "PLS body %.2f (KiCad PinHeader model) + PBS %.2f (strip model, deepest)" % (xp_body, xs_depth),
        xp_body + xs_depth, v["STACK_GAP"], "mated header and strip against the 11.0 mm standoff; the 0.04-0.13 mm is the PLS 2.5 / 2.54 and PBS 8.5 rounding",
        what="stack")
    # ---------------------------------------------------------------- DISP front side: the tubes against the case window
    def world_box(verts, mat):
        m = np.array(mat, dtype=float).reshape(4, 4)
        w = np.hstack([verts, np.ones((len(verts), 1))]) @ m.T
        return w[:, :3].min(0), w[:, :3].max(0)

    Md = M["TS06-DISP"]
    soffit = v["SOFFIT_Y"]
    glass12 = [r for r in disp if fp_of.get(r) == "TS06_IN12_Socket"]
    glass17 = [r for r in disp if fp_of.get(r) == "TS06_IN17_Socket"]
    lamps = [r for r in disp if fp_of.get(r) == "TS06_INS1_Lamp"]
    leds = [r for r in disp if fp_of.get(r) == "TS06_LED_D3.0mm"]
    face_plane = -v["Z_FACE"]               # the window's face plane, in the viewer-ward Z of the stack frame (+1.0)
    # tubes only: the vertices above the board face (the sleeves and pins below do not count)
    def tube_verts(r):
        a = disp[r]
        return a[a[:, 1] > T + 1.0]
    topY = max(world_box(tube_verts(r), Md)[1][1] for r in glass12)
    add("TS06-DISP", "front face", "ИН-12/15 glass top (Y %.2f) vs brow soffit (Y %.2f)" % (topY, soffit), topY, soffit,
        "case_pair: soffit 0.8 above the glass", what="window, Y")
    f12 = max(world_box(tube_verts(r), Md)[1][2] for r in glass12)
    add("TS06-DISP", "front face", "ИН-12/15 glass front (Z %+.2f) vs the window face plane (Z %+.2f)" % (f12, face_plane), f12, face_plane,
        "", what="window, Z")
    f17 = max(world_box(tube_verts(r), Md)[1][2] for r in glass17)
    add("TS06-DISP", "front face", "ИН-17 glass front (Z %+.2f) vs the window face plane (Z %+.2f)" % (f17, face_plane), f17, face_plane,
        "3d/IN17.step is 24.3 mm from dome to the end of the glass stalk; case_pair.py IN17_D says 22.0 (outline drawing). With the glass 8.0 off the board, "
        "the model's front stands %.1f mm proud of the ИН-12 plane. Measure a bench tube before ordering." % (f17 - world_box(tube_verts(glass12[0]), Md)[1][2]),
        what="window, Z")
    top17 = max(world_box(tube_verts(r), Md)[1][1] for r in glass17)
    add("TS06-DISP", "front face", "ИН-17 glass top (Y %.2f) vs brow soffit (Y %.2f)" % (top17, soffit), top17, soffit, "", what="window, Y")
    fl = max(world_box(disp[r], Md)[1][2] for r in lamps)
    add("TS06-DISP", "front face", "colon lamp tip (Z %+.2f) vs the window face plane (Z %+.2f)" % (fl, face_plane), fl, face_plane,
        "the lamps' height is inferred (tip flush with the ИН-12 faces)", what="window, Z")
    # side clearance to the trench walls
    xmin = min(world_box(tube_verts(r), Md)[0][0] for r in glass12)
    add("TS06-DISP", "front face", "H10 glass left edge (X %.2f) vs trench wall (X %.2f)" % (xmin, v["TRENCH_L_X"]), v["TRENCH_L_X"] * 0 + 0.0, xmin - v["TRENCH_L_X"],
        "clearance row: margin = gap; case_pair allows +0.4 for glass tolerance", what="window, X")
    xmax = max(world_box(tube_verts(r), Md)[1][0] for r in glass12)
    add("TS06-DISP", "front face", "ИН-15А glass right edge (X %.2f) vs trench wall (X %.2f)" % (xmax, v["TRENCH_R_X"]), 0.0, v["TRENCH_R_X"] - xmax,
        "clearance row: margin = gap", what="window, X")
    # the lowest LED flange against the sill
    ledy = min(world_box(disp[r], Md)[0][1] for r in leds)
    add("TS06-DISP", "front face", "lowest LED flange (Y %.2f) vs sill top (Y %.2f)" % (ledy, v["SILL_TOP_Y"]), 0.0, ledy - v["SILL_TOP_Y"],
        "clearance row: margin = gap", what="window, Y")
    # ---------------------------------------------------------------- DISP back side
    deep = sorted(((bottom(disp, r), r) for r in disp), reverse=True)
    seen = set()
    for h, r in deep:
        key = fp_of.get(r, r)
        if key in seen:
            continue
        seen.add(key)
        if len(seen) > 4:
            break
        add("TS06-DISP", "back face", r + " " + key.replace("TS06_", ""), h, v["STACK_GAP"],
            "header pins mate into the 8.5 mm PBS" if key.startswith("TS06_PinHeader") else "pin tail past the back face")
    add("TS06-DISP", "back face", lamps[0] + " INS1_Lamp leads (trimmed length is the model's 10 mm leads)", bottom(disp, lamps[0]), v["STACK_GAP"],
        "the longest tail on the board that is not a header pin")
    # ---------------------------------------------------------------- the fascia
    hole = SF.control_holes(os.path.join(SF.ROOT, "PCB", fascia, fascia + ".kicad_pcb"))     # the footprints' drills, from the board
    bush = {"SW1": 8.62, "SW2": 7.82, "SW3": 7.82, "SW4": 7.82, "SW5": 7.82}
    for r, what in (("SW1", "rotary"), ("SW2", "lever"), ("SW4", "button")):
        add("fascia R", "front face", "%s %s: bushing D%.2f in a D%.1f hole (per side)" % (r, what, bush[r], hole[r]), bush[r] / 2, hole[r] / 2,
            "bushing diameters are the calipered values of the repo's STEP files; the hole is the footprint's drill", what="hole")
    # the holes04 variant: the same rows on the board with every control hole opened (fab/HOLES-VARIANT.md); not part of rows / the tally
    vrows = []
    if fascia == "TS06-FASCIA-rhythm":
        with tempfile.TemporaryDirectory(prefix="fit_table.") as vtmp:
            vhole = SF.control_holes(SF.open_holes_board(vtmp))
        for r, what in (("SW1", "rotary"), ("SW2", "lever"), ("SW4", "button")):
            m = vhole[r] / 2 - bush[r] / 2
            vrows.append({"part": "%s %s: bushing D%.2f in a D%.1f hole (per side)" % (r, what, bush[r], vhole[r]), "height": round(bush[r] / 2, 2),
                          "space": round(vhole[r] / 2, 2), "margin": round(m, 2), "status": status(m),
                          "note": "the hole is %.1f mm wider than the committed one (+%.2f a side before)" % (vhole[r] - hole[r], hole[r] / 2 - bush[r] / 2)})
    for r, what in (("SW1", "rotary shaft"), ("SW2", "lever"), ("SW4", "button")):
        add("fascia R", "front face", "%s %s, reach beyond the front face" % (r, what), top(fas, r, TF), top(fas, r, TF) + 100.0,
            "", what="reach")
    rows = [x for x in rows if x["what"] != "reach"]
    # the bodies behind the fascia, against everything on TS06-DRV's display-facing face
    dr_boxes = {r: world_box(drv[r], M["TS06-DRV"]) for r in drv if bottom(drv, r) > 1.0}
    for r in ("SW1", "SW2", "SW4"):
        lo, hi = world_box(fas[r][fas[r][:, 1] < 0.0], M["fascia"])        # behind the fascia's back face (u < 0)
        gaps = []
        for q, (a, b2) in dr_boxes.items():
            gx = max(a[0] - hi[0], lo[0] - b2[0], 0.0)
            gy = max(a[1] - hi[1], lo[1] - b2[1], 0.0)
            gz = max(a[2] - hi[2], lo[2] - b2[2], 0.0)
            gaps.append((math.sqrt(gx * gx + gy * gy + gz * gz), q))
        gaps.append((lo[2] + v["Z_DRV_F"], "TS06-DRV's front face"))
        g, q = min(gaps)
        depth = -fas[r][:, 1].min()
        add("fascia R", "back face", "%s body behind the fascia (%.1f deep); nearest TS06-DRV display-side part %s" % (r, depth, q), 0.0, g,
            "clearance row: margin = the gap between the part's world bounding boxes (the fascia is raked 12 deg: conservative)", what="behind")
    md = ["# Fit table", "",
          "Generated by `python3 tools/fit_table.py` from the populated models and `3d/case-pair/case_pair.py`. "
          "Heights are read from the placed models (GLB bounding boxes); the space is the case model's own. Fascia: **%s**%s." % (
              fascia, "" if gold == "none" else ", with the Plates print and the %s gold (the board that is ordered)" % gold.capitalize()), "",
          "PASS: margin >= 1 mm. TIGHT: margin < 1 mm. FAIL: margin < %.2f mm (an interference larger than the rounding in the sources). "
          "A *clearance row* has height 0 and the margin is the gap itself." % FAIL_BELOW, ""]
    cur = None
    for x in rows:
        k = (x["board"], x["side"])
        if k != cur:
            md += ["", "## %s, %s" % k, "", "| Part | Height / position | Space / limit | Margin | |", "|---|---:|---:|---:|---|"]
            cur = k
        md.append("| %s | %.2f | %.2f | %+.2f | **%s**%s |" % (x["part"], x["height"], x["space"], x["margin"], x["status"],
                                                               ("<br>" + x["note"]) if x["note"] else ""))
    t = {}
    for x in rows:
        t[x["status"]] = t.get(x["status"], 0) + 1
    md += ["", "Rows: " + ", ".join("%d %s" % (n, s) for s, n in sorted(t.items())), ""]
    if vrows:
        md += ["## fascia R, front face: the holes04 variant", "",
               "The same three bushing rows with every control hole opened 0.4 mm in diameter (`tools/mkpcb_fascia_rhythm.py --open-holes`; the extra zip "
               "`fab/TS06-FASCIA-R-revA-divider-holes04-fab.zip`, `fab/HOLES-VARIANT.md`). The committed board, the zip in `fab/ORDER.md` and the rows above keep the "
               "0.09 mm; these rows are not in the tally. The 1 mm line of PASS is for heights: for a clearance fit, +0.29 a side is three times the committed +0.09.", "",
               "| Part | Height / position | Space / limit | Margin | |", "|---|---:|---:|---:|---|"]
        for x in vrows:
            md.append("| %s | %.2f | %.2f | %+.2f | **%s**<br>%s |" % (x["part"], x["height"], x["space"], x["margin"], x["status"], x["note"]))
        md.append("")
    open(outmd, "w", encoding="utf8").write("\n".join(md))
    if outjson:
        out = {"fascia": fascia, "gold": gold, "rows": rows, "tally": t}
        if vrows:
            out["holes_variant"] = {"extra_mm": 0.4, "about": "the three bushing rows on the board with every control hole opened 0.4 mm (fab/HOLES-VARIANT.md); not in rows or tally", "rows": vrows}
        json.dump(out, open(outjson, "w", encoding="utf8"), indent=1, ensure_ascii=False)
    print("wrote %s: %s" % (outmd, t))
    for x in rows:
        print("%-22s %-20s %-5s h %6.2f space %6.2f margin %+6.2f  %s" % (x["board"], x["side"], x["status"], x["height"], x["space"], x["margin"], x["part"][:70]))


if __name__ == "__main__":
    main(sys.argv)
