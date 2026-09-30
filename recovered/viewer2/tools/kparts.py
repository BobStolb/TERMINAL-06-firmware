#!/usr/bin/env python3
"""Read a .kicad_pcb and write the per-part data the viewer needs to find parts.

    python3 kparts.py BOARD.kicad_pcb [--models DIR] > parts.json

For every footprint: reference, value, footprint name, side, position and rotation, the
courtyard's bounding box in board coordinates (KiCad frame: x right, y down, mm), the pad
centres, and whether its 3D model file exists (so the GLB export will carry a node named
after the reference). The viewer uses the box to draw a highlight for any part, with or
without a 3D body, and the node name to tint the body when there is one.
Standard library only.
"""
import json, math, os, re, sys


def parse(text):
    """Minimal s-expression reader: lists of atoms (str) and lists; quoted strings unquoted."""
    tok = re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+')
    stack, cur = [], []
    for m in tok.finditer(text):
        t = m.group(0)
        if t == "(":
            stack.append(cur)
            cur = []
        elif t == ")":
            done = cur
            cur = stack.pop()
            cur.append(done)
        elif t[0] == '"':
            cur.append(t[1:-1].replace('\\"', '"').replace("\\\\", "\\"))
        else:
            cur.append(t)
    return cur[0]


def kids(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]


def kid(node, key):
    k = kids(node, key)
    return k[0] if k else None


def rot(lx, ly, deg):
    """KiCad footprint local -> board offset (y down, positive angle counter-clockwise on screen)."""
    a = math.radians(deg)
    return (lx * math.cos(a) + ly * math.sin(a), -lx * math.sin(a) + ly * math.cos(a))


def board(path, models=None):
    root = parse(open(path, encoding="utf8").read())
    thick = float(kid(kid(root, "general"), "thickness")[1])
    xs, ys = [], []
    for g in root:
        if isinstance(g, list) and g and g[0] in ("gr_line", "gr_arc", "gr_rect") and kid(g, "layer") and kid(g, "layer")[1] == "Edge.Cuts":
            for k in ("start", "end", "mid"):
                p = kid(g, k)
                if p:
                    xs.append(float(p[1]))
                    ys.append(float(p[2]))
    out = {"file": os.path.basename(path), "thickness": thick,
           "edge": [min(xs), max(xs), min(ys), max(ys)], "parts": {}}
    for fp in kids(root, "footprint"):
        name = fp[1].split(":")[-1]
        layer = kid(fp, "layer")[1]
        at = kid(fp, "at")
        x, y = float(at[1]), float(at[2])
        r = float(at[3]) if len(at) > 3 else 0.0
        props = {p[1]: p[2] for p in kids(fp, "property") if len(p) > 2}
        ref = props.get("Reference", "")
        if not ref or ref.startswith("REF"):
            continue
        cx, cy = [], []
        for g in fp:
            if not (isinstance(g, list) and g and g[0] in ("fp_line", "fp_rect", "fp_circle", "fp_poly", "fp_arc")):
                continue
            ly = kid(g, "layer")
            if not ly or "CrtYd" not in ly[1]:
                continue
            pts = []
            if g[0] == "fp_poly":
                pts = [(float(p[1]), float(p[2])) for p in kid(g, "pts") if isinstance(p, list) and p[0] == "xy"]
            elif g[0] == "fp_circle":
                c, e = kid(g, "center"), kid(g, "end")
                rr = math.hypot(float(e[1]) - float(c[1]), float(e[2]) - float(c[2]))
                pts = [(float(c[1]) + dx * rr, float(c[2]) + dy * rr) for dx, dy in ((-1, -1), (1, 1), (-1, 1), (1, -1))]
            else:
                for k in ("start", "end", "mid"):
                    p = kid(g, k)
                    if p:
                        pts.append((float(p[1]), float(p[2])))
                if g[0] == "fp_rect" and len(pts) >= 2:
                    pts += [(pts[0][0], pts[1][1]), (pts[1][0], pts[0][1])]
            for px, py in pts:
                dx, dy = rot(px, py, r)
                cx.append(x + dx)
                cy.append(y + dy)
        pads = []
        for p in kids(fp, "pad"):
            pa = kid(p, "at")
            dx, dy = rot(float(pa[1]), float(pa[2]), r)
            sz = kid(p, "size")
            pads.append([p[1], round(x + dx, 3), round(y + dy, 3), round(max(float(sz[1]), float(sz[2])), 3) if sz else 0])
        if not cx and pads:                      # no courtyard: the pads' extent plus 0.5
            cx = [q[1] - q[3] / 2 - 0.5 for q in pads] + [q[1] + q[3] / 2 + 0.5 for q in pads]
            cy = [q[2] - q[3] / 2 - 0.5 for q in pads] + [q[2] + q[3] / 2 + 0.5 for q in pads]
        model = None
        for m in kids(fp, "model"):
            model = m[1]
            break
        has_model = False
        if model and models:
            rel = model.replace("${KICAD10_3DMODEL_DIR}/", "").replace("${KICAD9_3DMODEL_DIR}/", "")
            has_model = os.path.exists(os.path.join(models, rel))
        attrs = kid(fp, "attr")
        out["parts"][ref] = {
            "v": props.get("Value", ""), "fp": name, "side": "B" if layer.startswith("B") else "F",
            "at": [round(x, 3), round(y, 3), round(r, 2)],
            "box": [round(min(cx), 3), round(max(cx), 3), round(min(cy), 3), round(max(cy), 3)] if cx else None,
            "model": has_model,
            "hole": "MountingHole" in name or (attrs is not None and "board_only" in attrs and not pads[1:]),
            "npads": len(pads),
        }
        if len(pads) <= 64:
            out["parts"][ref]["pads"] = [[q[0], q[1], q[2]] for q in pads]
    return out


if __name__ == "__main__":
    args = sys.argv[1:]
    models = None
    if "--models" in args:
        i = args.index("--models")
        models = args[i + 1]
        del args[i:i + 2]
    json.dump(board(args[0], models), sys.stdout, ensure_ascii=False, separators=(",", ":"))
