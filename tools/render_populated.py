#!/usr/bin/env python3
"""Render a board WITH its components: top, iso and bottom pictures and a populated GLB, from KiCad 10.

    python3 tools/render_populated.py TS06-DRV  OUTDIR                    # all three views + the GLB
    python3 tools/render_populated.py TS06-DISP OUTDIR --views iso --no-glb
    python3 tools/render_populated.py PCB/TS06-FASCIA-rhythm/TS06-FASCIA-rhythm.kicad_pcb OUTDIR
    python3 tools/render_populated.py TS06-FASCIA-rhythm OUTDIR --gold divider        # the fascia as it is ordered

BOARD is a board name (TS06-DISP, TS06-DRV, TS06-FASCIA-rhythm: PCB/<name>/<name>.kicad_pcb) or a path.
Writes OUTDIR/<name>-top.png, -iso.png, -bottom.png and OUTDIR/<name>-populated.glb.

WHAT IT DOES. The committed board is copied to a scratch directory and never written. In the copy
tools/models3d.py attaches the models of tools/models3d.json (footprints the board gives no model, a
socketed chip on its socket, a part whose own model file does not exist), and the black-mask / white-silk
stackup of render_kicad.py goes in if the board has none. KiCad (kicad-cli in Docker, the image of
tools/render_kicad.py) then renders the copy; the library models are mounted read-only and named by -D, so
the boards' ${KICAD10_3DMODEL_DIR} paths resolve. The GLB is exported with --fuse-shapes and without the copper
tracks (they lie under the mask; --glb-tracks puts them in): TS06-DRV is then 13.4 MiB, against 19.6 MiB without either
(the limit for a committed model file is 15 MB). Pictures are trimmed to their content, kept to 2400 px
wide and checked to be under 3 MB; the GLB is checked to be at most 15 MB.

--gold VARIANT (none, divider, ...; the fascia boards only, default none = the committed board with its plain silk): render the
board that is ordered instead, the fascia with the Plates white print and that gold. Its art board is built in the scratch
directory by tools/fascia_gold.py (its own checks must be clean), exactly as tools/mkfab.sh builds the board it plots; the
model map still applies (it is keyed by the committed board's name), so the controls keep their bodies. Nothing under
PCB/ is written. The pictures and the GLB keep the names <board>-top.png ... <board>-populated.glb.

Options: --views top,iso,bottom   --no-glb   --width 2400   --kicad3d DIR (KiCad's 3D library; default the
files this project uses, vendored in 3d/populated/kicad3d)   --keep (leave the scratch copy and say where).
"""
import argparse, os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import sexp as S          # noqa: E402
import models3d as M      # noqa: E402
import render_kicad as RK  # noqa: E402
import stack_frame as SF   # noqa: E402  (art_board: the fascia with its Plates print and gold)

MAX_W = 2400
MAX_PNG = 3 * 1024 * 1024
MAX_GLB = 15 * 1024 * 1024

# per board, per view: kicad-cli pcb render arguments (besides size and quality). Top/bottom are the
# orthographic plan views; iso is a perspective three-quarter view from the front, below the horizon
# a little, so the standing parts show their sides.
VIEWS = {
    "top": ["--side", "top"],
    "bottom": ["--side", "bottom"],
    "iso": ["--perspective", "--rotate", "-45,0,-25"],
}
ISO_ZOOM = {"TS06-DISP": 1.05, "TS06-DRV": 0.85, "TS06-FASCIA-rhythm": 1.05}


def board_path(arg):
    if os.path.isfile(arg):
        return arg
    p = os.path.join(ROOT, "PCB", arg, arg + ".kicad_pcb")
    if not os.path.isfile(p):
        sys.exit("no such board: %s" % arg)
    return p


def scratch_board(path, tmp, kicad3d=None, bare=False, art=None):
    """Write the populated copy of the board into tmp; returns (name, plan rows, {VAR: dir}).
    bare: attach nothing (only the models the board carries itself): the render as it was before the map.
    art: a scratch board to read instead of path (the fascia with its gold); the model map and the project file are
    those of the committed board `path`, whose name the copy keeps."""
    mp = M.load_map()
    dmap = M.dirs(mp, kicad3d)
    key = M.board_key(path)
    if bare:
        mp = {"vars": mp.get("vars", {}), "parts": {}, "boards": {key: {"footprints": {}, "refs": {}, "none": {}}}}
    src = open(art or path, encoding="utf8").read()
    tree = S.parse(src)
    rows = M.apply(tree, key, mp, dmap)
    open(os.path.join(tmp, key + ".kicad_pcb"), "w", encoding="utf8").write(RK.with_stackup(S.dump(tree) + "\n"))
    pro = os.path.join(os.path.dirname(path), key + ".kicad_pro")
    if os.path.exists(pro):
        shutil.copy(pro, tmp)
    return key, rows, dmap


def kicad(tmp, dmap, sub, args):
    """kicad-cli <sub> <args> on the scratch board, with the model directories mounted and named (-D)."""
    mounts, defs = [], []
    for k, v in dmap.items():
        mounts += ["-v", "%s:/v/%s:ro" % (v, k)]
        defs += ["-D", "%s=/v/%s" % (k, k)]
    cli = os.environ.get("KICAD_CLI")
    if cli:                                           # a local kicad-cli: the same variables, real paths
        defs = sum((["-D", "%s=%s" % (k, v)] for k, v in dmap.items()), [])
        cmd = [cli] + sub + defs + args
    else:
        cmd = ["docker", "run", "--rm", "--user", "%d:%d" % (os.getuid(), os.getgid()), "-v", tmp + ":/w", "-w", "/w",
               "-e", "HOME=/tmp"] + mounts + [RK.IMG, "kicad-cli"] + sub + defs + args
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r


def trim_png(path, width_cap):
    from PIL import Image
    im = Image.open(path).convert("RGBA")
    # KiCad casts the board's shadow onto the transparent background (alpha up to ~210 in the iso views); the board itself is >= 240
    # except at its anti-aliased edge, and 255 inside. Keep the board, drop the shadow.
    im.putalpha(im.getchannel("A").point(lambda v: 0 if v < 230 else v))
    box = im.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
    if box and (box[0] <= 1 or box[1] <= 1 or box[2] >= im.size[0] - 1 or box[3] >= im.size[1] - 1):
        print("WARNING: %s runs into the frame: part of the board is cut off" % os.path.basename(path))
    if box:
        pad = 12
        im = im.crop((max(0, box[0] - pad), max(0, box[1] - pad), min(im.size[0], box[2] + pad), min(im.size[1], box[3] + pad)))
    if im.size[0] > width_cap:
        im = im.resize((width_cap, round(im.size[1] * width_cap / im.size[0])), Image.LANCZOS)
    im.save(path, optimize=True)
    return im.size


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("board")
    ap.add_argument("outdir")
    ap.add_argument("--views", default="top,iso,bottom")
    ap.add_argument("--no-glb", action="store_true")
    ap.add_argument("--width", type=int, default=MAX_W)
    ap.add_argument("--quality", default="high")
    ap.add_argument("--kicad3d")
    ap.add_argument("--glb-no-zones", action="store_true", help="leave the copper pours out of the GLB (smaller)")
    ap.add_argument("--glb-tracks", action="store_true", help="put the copper tracks in the GLB (they sit under the mask; 1.6 MiB for TS06-DRV)")
    ap.add_argument("--glb-flags", default="", help="extra kicad-cli export glb flags, e.g. '--fuse-shapes --min-distance 0.01mm'")
    ap.add_argument("--gold", default="none", metavar="VARIANT",
                    help="the fascia boards only: render the board as ordered, with the Plates print and this gold (none, divider, ...)")
    ap.add_argument("--bare", action="store_true", help="no map: the board with only the models it carries itself (the 'before' picture)")
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()
    path = board_path(a.board)
    os.makedirs(a.outdir, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="render_populated.")
    os.chmod(tmp, 0o777)
    try:
        art = None
        if a.gold != "none":
            if a.bare:
                sys.exit("--gold and --bare do not go together")
            art = SF.art_board(os.path.splitext(os.path.basename(path))[0], a.gold, tmp)
        key, rows, dmap = scratch_board(path, tmp, a.kicad3d, a.bare, art)
        miss = [r for r in rows if r["status"] == "missing"]
        if miss:
            print("WARNING: %d footprints without a model: %s" % (len(miss), ", ".join(r["ref"] for r in miss)))
        # extent of the board, as render_kicad does: plan views at one pixel scale
        bx0, by0, bx1, by1 = RK.extent(open(art or path, encoding="utf8").read())
        bw, bh = bx1 - bx0, by1 - by0
        diag = (bw ** 2 + bh ** 2) ** 0.5
        board = "/w/%s.kicad_pcb" % key
        if not a.no_glb:
            r = kicad(tmp, dmap, ["pcb", "export", "glb"], ["-f", "--include-pads"] + (["--include-tracks"] if a.glb_tracks else []) + ([] if a.glb_no_zones else ["--include-zones"]) +
                                                          ["--include-silkscreen", "--include-soldermask", "--fuse-shapes"] + a.glb_flags.split() +
                                                          ["-o", "/w/out.glb", board])
            if not os.path.exists(os.path.join(tmp, "out.glb")):
                sys.exit("glb export failed:\n" + r.stdout + r.stderr)
            size = os.path.getsize(os.path.join(tmp, "out.glb"))
            dst = os.path.join(a.outdir, "%s-populated.glb" % key)
            shutil.copy(os.path.join(tmp, "out.glb"), dst)
            print("wrote %s (%.2f MB)%s" % (dst, size / 1048576.0, "" if size <= MAX_GLB else "  OVER 15 MB: do not commit"))
        for v in [x for x in a.views.split(",") if x]:
            # the frame is made roomy and the picture trimmed afterwards: KiCad's zoom 1 is the whole scene (tall parts, parts
            # that overhang the board), not the board outline, so a tight frame cuts the board off
            if v in ("top", "bottom"):
                fw = int(a.width * 1.3)
                ppm = fw / (bw + 30.0)
                fh = int(round(ppm * (bh + 30.0)))
                zoom = ppm * diag / fh
            else:
                fw, fh = int(a.width * 1.2), int(round(a.width * 1.2 * 0.62))
                zoom = ISO_ZOOM.get(key, 1.0)
            args = ["--use-board-stackup-colors", "--quality", a.quality, "--background", "transparent",
                                             "--width", str(fw), "--height", str(fh), "--zoom", "%.4f" % zoom] + VIEWS[v] + \
                   ["-o", "/w/%s.png" % v, board]
            r = kicad(tmp, dmap, ["pcb", "render"], args)
            out = os.path.join(tmp, v + ".png")
            if not os.path.exists(out):
                sys.exit("render %s failed:\n%s%s" % (v, r.stdout, r.stderr))
            dst = os.path.join(a.outdir, "%s-%s.png" % (key, v))
            shutil.copy(out, dst)
            w, h = trim_png(dst, a.width)
            n = os.path.getsize(dst)
            print("wrote %s (%d x %d px, %.2f MB)%s" % (dst, w, h, n / 1048576.0, "" if n < MAX_PNG else "  OVER 3 MB"))
    finally:
        if a.keep:
            print("scratch kept:", tmp)
        else:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
