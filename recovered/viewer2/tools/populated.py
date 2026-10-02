#!/usr/bin/env python3
"""The populated boards on the page: their pictures, their sizes, what the page may assume about them.

    python3 populated.py REPO SITE [WORKOUT]

REPO/3d/populated/ holds the boards drawn with every component (tools/render_populated.py; README there):
TS06-DISP, TS06-DRV and the fascia R as it is ordered (the Plates print and the Divider gold), each as
a GLB and as top / iso / bottom pictures, and the assembled stack as two pictures. build.sh has already
turned each GLB into SITE/3d/<board>.gltf.json (the host serves no .glb); this copies the pictures to
SITE/img/ under the names the page already uses (<board>-top.png ...: the populated ones replace KiCad's bare renders) and writes
SITE/data/populated.json:

    boards.<board>   populated: true, the GLB it came from and its size, the size of the published
                     glTF JSON, how many footprints have a model (tools/model_coverage.py's own count)
    gold             the fascia's gold (3d/populated/stack.json "fascia_gold"), "none" if the committed board
    pictures         the files copied

The page reads this to know a board's own 3D file already carries its parts, so it draws no stand-in
bodies on it. A board that is not listed (the fascia variants A and W) is drawn as before.
Every file is checked against the host's limit (15 MB each).
"""
import json, os, shutil, sys

MAX = 15 * 1024 * 1024
BOARDS = ["TS06-DRV", "TS06-DISP", "TS06-FASCIA-rhythm"]


def main(repo, site):
    pop = os.path.join(repo, "3d", "populated")
    sys.path.insert(0, os.path.join(repo, "tools"))
    sys.dont_write_bytecode = True
    import model_coverage as MC          # noqa: E402  (the repo's own check; read-only)
    import models3d as M                 # noqa: E402
    mp = M.load_map()
    dmap = M.dirs(mp, os.path.join(pop, "kicad3d"))
    stack = json.load(open(os.path.join(pop, "stack.json"), encoding="utf8"))
    res = {"boards": {}, "gold": stack.get("fascia_gold", "none"), "fascia_board": stack.get("fascia_board"), "pictures": [], "source": "3d/populated/"}
    os.makedirs(os.path.join(site, "img"), exist_ok=True)
    for b in BOARDS:
        glb = os.path.join(pop, b + "-populated.glb")
        if not os.path.isfile(glb):
            continue
        gj = os.path.join(site, "3d", b + ".gltf.json")
        t = MC.tally(MC.check(b, mp, dmap))
        res["boards"][b] = {"populated": True, "glb": "3d/populated/%s-populated.glb" % b, "glb_bytes": os.path.getsize(glb),
                            "published": "3d/%s.gltf.json" % b, "published_bytes": os.path.getsize(gj) if os.path.isfile(gj) else None,
                            "footprints": {"with_model": t["ok"], "allowlisted": t["allowlisted"], "missing": t["missing"]}}
        for v in ("top", "iso", "bottom"):
            src = os.path.join(pop, "%s-%s.png" % (b, v))
            if os.path.isfile(src):
                shutil.copy(src, os.path.join(site, "img", "%s-%s.png" % (b, v)))
                res["pictures"].append("img/%s-%s.png" % (b, v))
    for v in ("front", "iso"):
        src = os.path.join(pop, "TS06-stack-%s.png" % v)
        if os.path.isfile(src):
            shutil.copy(src, os.path.join(site, "img", "stack-%s.png" % v))
            res["pictures"].append("img/stack-%s.png" % v)
    for p in res["pictures"] + [x["published"] for x in res["boards"].values()]:
        f = os.path.join(site, p)
        if os.path.isfile(f) and os.path.getsize(f) > MAX:
            sys.exit("populated.py: %s is %.1f MB, over the host's 15 MB" % (p, os.path.getsize(f) / 1048576))
    json.dump(res, open(os.path.join(site, "data", "populated.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
    for b, x in res["boards"].items():
        print("  %-20s GLB %6.2f MB -> glTF JSON %6.2f MB; footprints: %d with a model, %d allowlisted, %d missing" % (
            b, x["glb_bytes"] / 1048576, (x["published_bytes"] or 0) / 1048576, x["footprints"]["with_model"], x["footprints"]["allowlisted"], x["footprints"]["missing"]))
    print("  fascia gold: %s; %d pictures" % (res["gold"], len(res["pictures"])))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
