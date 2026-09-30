#!/usr/bin/env python3
"""The case model's STL parts -> one glTF JSON (embedded base64), one named node per part.

    python3 stl2gltf.py OUT.gltf.json cheek_l=path/cheek_l.stl brow=path/brow.stl ...

The STLs come from 3d/case-pair (OpenSCAD: x = X, y = Z, z = Y, mm, in world position). They are
written here in the viewer's frame, three.js's right-handed Y-up: (X, Y, -Z), still in mm, so the
page adds them as they are. Vertices are welded (the page shades them flat). ASCII and binary STL.
"""
import base64, json, struct, sys


def read_stl(path):
    b = open(path, "rb").read()
    tris = []
    if b[:5] == b"solid" and b"facet" in b[:400]:
        v = []
        for line in b.decode("ascii", "replace").splitlines():
            t = line.split()
            if t and t[0] == "vertex":
                v.append((float(t[1]), float(t[2]), float(t[3])))
                if len(v) == 3:
                    tris.append(v)
                    v = []
    else:
        n = struct.unpack("<I", b[80:84])[0]
        for i in range(n):
            f = struct.unpack("<12f", b[84 + i * 50:84 + i * 50 + 48])
            tris.append([f[3:6], f[6:9], f[9:12]])
    return tris


def main(out, parts):
    blob = bytearray()
    views, accs, meshes, nodes = [], [], [], []
    for name, path in parts:
        tris = read_stl(path)
        index, pos, idx = {}, [], []
        for t in tris:
            for x, y, z in t:
                p = (round(x, 3), round(z, 3), round(-y, 3))       # OpenSCAD (X, Z, Y) -> three (X, Y, -Z)
                k = index.get(p)
                if k is None:
                    k = index[p] = len(pos)
                    pos.append(p)
                idx.append(k)
        lo = [min(p[i] for p in pos) for i in range(3)]
        hi = [max(p[i] for p in pos) for i in range(3)]
        while len(blob) % 4:
            blob.append(0)
        o = len(blob)
        for p in pos:
            blob += struct.pack("<3f", *p)
        views.append({"buffer": 0, "byteOffset": o, "byteLength": len(pos) * 12, "target": 34962})
        accs.append({"bufferView": len(views) - 1, "componentType": 5126, "count": len(pos), "type": "VEC3", "min": lo, "max": hi})
        o = len(blob)
        fmt = "<%dI" % len(idx)
        blob += struct.pack(fmt, *idx)
        views.append({"buffer": 0, "byteOffset": o, "byteLength": len(idx) * 4, "target": 34963})
        accs.append({"bufferView": len(views) - 1, "componentType": 5125, "count": len(idx), "type": "SCALAR"})
        meshes.append({"name": name, "primitives": [{"attributes": {"POSITION": len(accs) - 2}, "indices": len(accs) - 1, "material": 0}]})
        nodes.append({"name": name, "mesh": len(meshes) - 1})
        print("  %-12s %6d triangles" % (name, len(tris)))
    g = {"asset": {"version": "2.0", "generator": "viewer2/tools/stl2gltf.py"},
         "scene": 0, "scenes": [{"nodes": list(range(len(nodes)))}], "nodes": nodes, "meshes": meshes,
         "materials": [{"name": "case", "pbrMetallicRoughness": {"baseColorFactor": [0.25, 0.27, 0.3, 1], "metallicFactor": 0, "roughnessFactor": 0.8}}],
         "accessors": accs, "bufferViews": views,
         "buffers": [{"byteLength": len(blob), "uri": "data:application/octet-stream;base64," + base64.b64encode(bytes(blob)).decode()}]}
    with open(out, "w") as fh:
        json.dump(g, fh, separators=(",", ":"))


if __name__ == "__main__":
    main(sys.argv[1], [a.split("=", 1) for a in sys.argv[2:]])
