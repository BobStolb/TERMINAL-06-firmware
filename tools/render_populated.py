#!/usr/bin/env python3
"""Render a board WITH its components: top, iso and bottom pictures and a populated GLB, from KiCad 10.

    python3 tools/render_populated.py TS06-DRV  OUTDIR                    # all three views + the GLB
    python3 tools/render_populated.py TS06-DISP OUTDIR --views iso --no-glb
    python3 tools/render_populated.py PCB/TS06-FASCIA-rhythm/TS06-FASCIA-rhythm.kicad_pcb OUTDIR

BOARD is a board name (TS06-DISP, TS06-DRV, TS06-FASCIA-rhythm: PCB/<name>/<name>.kicad_pcb) or a path.
Writes OUTDIR/<name>-top.png, -iso.png, -bottom.png and OUTDIR/<name>-populated.glb.

WHAT IT DOES. The committed board is copied to a scratch directory and never written. In the copy
tools/models3d.py attaches the models of tools/models3d.json (footprints the board gives no model, a
socketed chip on its socket, a part whose own model file does not exist), and the black-mask / white-silk
stackup of render_kicad.py goes in if the board has none. KiCad (kicad-cli in Docker, the image of
tools/render_kicad.py) then renders the copy; the library models are mounted read-only and named by -D, so
the boards' ${KICAD10_3DMODEL_DIR} paths resolve. Pictures are trimmed to their content, kept to 2400 px
wide and checked to be under 3 MB; the GLB is checked to be at most 15 MB.

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
ISO_ZOOM = {"TS06-DISP": 1.25, "TS06-DRV": 1.35, "TS06-FASCIA-rhythm": 1.3}


def board_path(arg):
    if os.path.isfile(arg):
        return arg
    p = os.path.join(ROOT, "PCB", arg, arg + ".kicad_pcb")
    if not os.path.isfile(p):
        sys.exit("no such board: %s" % arg)
    return p


def scratch_board(path, tmp, kicad3d=None):
    """Write the populated copy of the board into tmp; returns (name, plan rows, {VAR: dir})."""
    mp = M.load_map()
    dmap = M.dirs(mp, kicad3d)
    key = M.board_key(path)
    src = open(path, encoding="utf8").read()
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
    box = im.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
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
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()
    path = board_path(a.board)
    os.makedirs(a.outdir, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="render_populated.")
    os.chmod(tmp, 0o777)
    try:
        key, rows, dmap = scratch_board(path, tmp, a.kicad3d)
        miss = [r for r in rows if r["status"] == "missing"]
        if miss:
            print("WARNING: %d footprints without a model: %s" % (len(miss), ", ".join(r["ref"] for r in miss)))
        # extent of the board, as render_kicad does: plan views at one pixel scale
        bx0, by0, bx1, by1 = RK.extent(open(path, encoding="utf8").read())
        bw, bh = bx1 - bx0, by1 - by0
        diag = (bw ** 2 + bh ** 2) ** 0.5
        board = "/w/%s.kicad_pcb" % key
        if not a.no_glb:
            r = kicad(tmp, dmap, ["pcb", "export", "glb"], ["-f", "--include-pads", "--include-tracks", "--include-zones",
                                                           "--include-silkscreen", "--include-soldermask", "-o", "/w/out.glb", board])
            if not os.path.exists(os.path.join(tmp, "out.glb")):
                sys.exit("glb export failed:\n" + r.stdout + r.stderr)
            size = os.path.getsize(os.path.join(tmp, "out.glb"))
            dst = os.path.join(a.outdir, "%s-populated.glb" % key)
            shutil.copy(os.path.join(tmp, "out.glb"), dst)
            print("wrote %s (%.2f MB)%s" % (dst, size / 1048576.0, "" if size <= MAX_GLB else "  OVER 15 MB: do not commit"))
        for v in [x for x in a.views.split(",") if x]:
            if v in ("top", "bottom"):
                ppm = a.width / (bw + 6.0)
                fw, fh = int(a.width), int(round(ppm * (bh + 6.0)))
                zoom = ppm * diag / fh
            else:
                fw, fh = int(a.width), int(round(a.width * 0.56))
                zoom = ISO_ZOOM.get(key, 1.3)
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
