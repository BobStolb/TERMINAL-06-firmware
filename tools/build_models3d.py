#!/usr/bin/env python3
"""Build the 3D models this project makes itself: OpenSCAD source -> coloured VRML that KiCad loads.

    python3 tools/build_models3d.py                 # every 3d/populated/models/*.scad
    python3 tools/build_models3d.py dip_chip_16     # one, by name

WHY. The kicad Docker image ships no 3D library at all, and the copy of the library on this machine
lacks the Arduino Nano, the Bourns fuse, the LED, the chips that sit in the DIP sockets and the
SMD parts. Parts that no file exists for are drawn here: simple, dimensionally right bodies, each
dimension marked measured (a repo source named) or inferred in the .scad header and in README.md.

HOW. A model is one .scad file. Its first lines say how it is cut into colours and how it is
instantiated:

    // layers: body=#1c1c1c leads=#c0c0c0 mark=#8c8c8c
    // variants: dip_chip_16 N=16 ; dip_chip_28 N=28        (optional: one output per -D set)

For every layer, OpenSCAD runs the file with  -D 'L="<layer>"'  and writes an STL; this script merges
the layers into one VRML 2.0 file (a Shape per layer, with its colour), 3d/populated/models/<name>.wrl.
The model frame is KiCad's: millimetres, x right, y UP on the screen (a footprint's y negated), z up
out of the board face the part stands on. KiCad reads VRML in units of 0.1 inch by default, so the
points are written divided by 2.54 and models3d.json carries "scale": [1, 1, 1] (the unit is a
property of the reader, tested in this repository: see README.md).
"""
import os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
MODELS = os.path.join(ROOT, "3d", "populated", "models")
VRML_UNIT = 2.54      # mm per VRML unit as KiCad reads it (checked: a 10 mm cube written as 3.937 loads as 10 mm)


def read_header(path):
    layers, variants = [], []
    for line in open(path, encoding="utf8"):
        m = re.match(r"^//\s*layers:\s*(.*)$", line)
        if m:
            for tok in m.group(1).split():
                k, v = tok.split("=")
                layers.append((k, v))
        m = re.match(r"^//\s*variants:\s*(.*)$", line)
        if m:
            for part in m.group(1).split(";"):
                part = part.strip()
                if part:
                    toks = part.split()
                    variants.append((toks[0], toks[1:]))
    if not layers:
        sys.exit("%s: no '// layers:' line" % path)
    return layers, variants or [(os.path.splitext(os.path.basename(path))[0], [])]


def stl_triangles(path):
    tri, cur = [], []
    for m in re.finditer(r"vertex\s+(\S+)\s+(\S+)\s+(\S+)", open(path).read()):
        cur.append((float(m.group(1)), float(m.group(2)), float(m.group(3))))
        if len(cur) == 3:
            tri.append(cur)
            cur = []
    return tri


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def shape(tris, rgb, spec=0.25, shin=0.3):
    idx, pts, out = {}, [], []
    for t in tris:
        face = []
        for v in t:
            k = tuple(round(c, 4) for c in v)
            if k not in idx:
                idx[k] = len(pts)
                pts.append(k)
            face.append(idx[k])
        if len(set(face)) == 3:
            out.append(face)
    r, g, b = rgb
    s = ["Shape {\n appearance Appearance { material Material {\n  diffuseColor %.4f %.4f %.4f\n"
         "  specularColor %.3f %.3f %.3f\n  ambientIntensity 0.4\n  shininess %.2f\n } }\n"
         " geometry IndexedFaceSet {\n  creaseAngle 0.5\n  coord Coordinate { point [\n" % (r, g, b, spec, spec, spec, shin)]
    s.append(",\n".join("   %.5f %.5f %.5f" % (p[0] / VRML_UNIT, p[1] / VRML_UNIT, p[2] / VRML_UNIT) for p in pts))
    s.append("\n  ] }\n  coordIndex [\n")
    s.append(",\n".join("   %d, %d, %d, -1" % tuple(f) for f in out))
    s.append("\n  ]\n }\n}\n")
    return "".join(s)


def build(scad, name, defs, layers, outdir):
    """defs: -D settings for OpenSCAD; a COLOR_<layer>=#rrggbb token changes that layer's colour for this variant."""
    layers = [(l, dict(t.split("=", 1) for t in defs if t.startswith("COLOR_")).get("COLOR_" + l, c)) for l, c in layers]
    defs = [d for d in defs if not d.startswith("COLOR_")]
    parts = []
    with tempfile.TemporaryDirectory() as tmp:
        for lname, color in layers:
            stl = os.path.join(tmp, lname + ".stl")
            cmd = ["openscad", "-D", 'L="%s"' % lname] + sum((["-D", d] for d in defs), []) + ["-o", stl, scad]
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0 and "top level object is empty" not in r.stderr:
                sys.exit("openscad failed for %s/%s:\n%s" % (name, lname, r.stderr[-800:]))
            tris = stl_triangles(stl) if os.path.exists(stl) else []        # a layer a variant does not use is empty
            if tris:
                parts.append((lname, color, tris))
    wrl = "#VRML V2.0 utf8\n# %s: written by tools/build_models3d.py from %s; layers %s\n" % (
        name, os.path.relpath(scad, ROOT), ", ".join("%s %s" % l for l in layers))
    for lname, color, tris in parts:
        wrl += shape(tris, hex_rgb(color))
    out = os.path.join(outdir, name + ".wrl")
    open(out, "w").write(wrl)
    print("wrote %s  (%s)" % (os.path.relpath(out, ROOT), ", ".join("%s %d tris" % (p[0], len(p[2])) for p in parts)))


def main(argv):
    want = set(argv[1:])
    for fn in sorted(os.listdir(MODELS)):
        if not fn.endswith(".scad") or fn.startswith("_"):
            continue
        layers, variants = read_header(os.path.join(MODELS, fn))
        for name, defs in variants:
            if want and name not in want and os.path.splitext(fn)[0] not in want:
                continue
            build(os.path.join(MODELS, fn), name, defs, layers, MODELS)


if __name__ == "__main__":
    main(sys.argv)
