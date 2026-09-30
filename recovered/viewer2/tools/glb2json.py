#!/usr/bin/env python3
"""GLB -> glTF JSON with its one buffer embedded as base64, for hosts that will not serve .glb/.bin.

    python3 glb2json.py in.glb out.gltf.json

three.js's GLTFLoader reads the result as ordinary glTF (it sniffs the content, not the name).
Reports the extensions the file needs: after gltfpack without -c that is only
KHR_mesh_quantization, which needs no decoder.
"""
import base64, json, struct, sys


def main(src, dst):
    b = open(src, "rb").read()
    assert b[:4] == b"glTF", "not a GLB"
    off, js, binc = 12, None, b""
    while off < len(b):
        ln, typ = struct.unpack("<I4s", b[off:off + 8])
        chunk = b[off + 8:off + 8 + ln]
        if typ == b"JSON":
            js = json.loads(chunk)
        elif typ == b"BIN\x00":
            binc = chunk
        off += 8 + ln
    if js.get("buffers"):
        assert len(js["buffers"]) == 1, "expected one buffer"
        js["buffers"][0]["uri"] = "data:application/octet-stream;base64," + base64.b64encode(binc).decode()
        js["buffers"][0]["byteLength"] = len(binc)
    with open(dst, "w") as fh:
        json.dump(js, fh, separators=(",", ":"))
    print("%s: %d nodes, %d meshes, ext %s" % (dst.split("/")[-1], len(js.get("nodes", [])), len(js.get("meshes", [])),
                                               ",".join(js.get("extensionsRequired", [])) or "none"))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
