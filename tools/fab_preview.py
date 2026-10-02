#!/usr/bin/env python3
"""The pictures of the three boards as they are ordered, from the committed board files (KiCad 10's own 3D renderer).

    python3 tools/fab_preview.py OUTDIR [--gold divider] [--px-per-mm 12]

writes into OUTDIR (it is made if missing):
    fascia-R-divider-top.png    the fascia R (TS06-FASCIA-rhythm, rev A) with the gold, seen from the front
    three-boards-top.png        TS06-DISP, TS06-DRV and the fascia, top views, one under the other, labelled

The fascia is the art board that tools/fascia_gold.py builds in a scratch directory (nothing under PCB/ is
written). Every picture is KiCad 10's own 3D render, black mask, white silk, ENIG where the mask is open (the stack-up
of render_kicad.py is put in a board that has none). PNGs are kept under 2400 px wide and 3 MB. KiCad runs in Docker,
or from KICAD_CLI, as tools/verify_pair.sh. Needs Pillow, numpy and scipy.

EACH BOARD IS SHOWN WHOLE. tools/render_kicad.py frames a board from a rule measured on the 191.4 x 40 mm fascia (at
zoom 1 the frame is as high as the board's diagonal); on TS06-DRV (191.4 x 100 mm) KiCad draws 9% larger than that
rule says, so the picture lost the board's left and top edges and the right and bottom as well. So here the scale
is measured first: two white squares are planted on a scratch copy at known places, rendered, and found in the
picture; the scale KiCad gives (it is proportional to the zoom and to the frame's height) is then known for that
board, and the real render is framed to hold the Edge.Cuts outline and a 2 mm margin. render_kicad.py is not changed.
"""
import argparse, math, os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)


def kicad_render(tmp, name, fw, fh, zoom):
    """KiCad 10's top view of tmp/name.kicad_pcb as a PIL image (it comes back a few pixels smaller than asked)."""
    from PIL import Image
    import render_kicad as RK
    args = ["pcb", "render", "--side", "top", "--width", str(fw), "--height", str(fh), "--quality", "high",
            "--background", "opaque", "--use-board-stackup-colors", "--zoom", "%.5f" % zoom]
    cli = os.environ.get("KICAD_CLI")
    if cli:
        cmd = [cli] + args + ["-o", os.path.join(tmp, "out.png"), os.path.join(tmp, name + ".kicad_pcb")]
    else:
        cmd = ["docker", "run", "--rm", "--user", "%d:%d" % (os.getuid(), os.getgid()), "-v", tmp + ":/w", "-w", "/w", "-e", "HOME=/tmp",
               RK.IMG, "kicad-cli"] + args + ["-o", "/w/out.png", "/w/%s.kicad_pcb" % name]
    if os.path.exists(os.path.join(tmp, "out.png")):
        os.remove(os.path.join(tmp, "out.png"))
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(os.path.join(tmp, "out.png")):
        sys.exit("kicad-cli failed:\n" + r.stdout + r.stderr)
    return Image.open(os.path.join(tmp, "out.png")).convert("RGB")


def find_marks(im, size_px, n=2):
    """Centres (x, y px) of the white squares in a render: the white that survives eroding by a fifth of the mark's size
    (the silk text and outlines are thinner), the n biggest pieces."""
    import numpy as np
    from scipy import ndimage
    white = ndimage.binary_erosion(np.asarray(im).min(axis=2) > 200, iterations=max(2, int(size_px / 5)))
    lab, k = ndimage.label(white)
    if not k:
        return []
    sizes = np.bincount(lab.ravel())[1:]
    out = []
    for i in np.argsort(-sizes)[:n]:
        ys, xs = np.where(lab == i + 1)
        out.append((float(xs.mean()), float(ys.mean())))
    return sorted(out)


def render(board, out, ppm, margin=2.0):
    """The whole board, Edge.Cuts plus margin mm, at ppm px per mm (see the docstring: the scale is measured first)."""
    import render_kicad as RK
    src = open(board, encoding="utf8").read()
    bx0, by0, bx1, by1 = RK.extent(src)
    bw, bh = bx1 - bx0, by1 - by0
    name = os.path.splitext(os.path.basename(board))[0]
    tmp = tempfile.mkdtemp(prefix="fab_render.")
    try:
        pro = os.path.join(os.path.dirname(os.path.abspath(board)), name + ".kicad_pro")
        if os.path.exists(pro):
            shutil.copy(pro, tmp)
        os.chmod(tmp, 0o777)
        K0 = 0.005                                       # px per mm = K x zoom x the asked height, as measured; a first guess
        # 1. the scale: two 8 mm white squares at known places, 15% / 30% and 85% / 70% of the way across the board
        S, pc = 8.0, 4.0
        pts = [(bx0 + 0.15 * bw, by0 + 0.30 * bh), (bx0 + 0.85 * bw, by0 + 0.70 * bh)]
        mark = "".join('\t(gr_rect\n\t\t(start %g %g)\n\t\t(end %g %g)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type solid)\n\t\t)\n'
                       '\t\t(fill yes)\n\t\t(layer "F.SilkS")\n\t\t(uuid "00000000-0000-4000-8000-00000000000%d")\n\t)\n'
                       % (x - S / 2, y - S / 2, x + S / 2, y + S / 2, i) for i, (x, y) in enumerate(pts))
        i = src.rindex(")")
        open(os.path.join(tmp, name + ".kicad_pcb"), "w", encoding="utf8").write(RK.with_stackup(src[:i] + mark + ")\n"))
        fh0, fw0 = int(round((bh + 4) * pc)), int(round((bw + 4) * pc))
        zoom0 = pc / (K0 * fh0)
        im = kicad_render(tmp, name, fw0, fh0, zoom0)
        marks = find_marks(im, S * pc)
        if len(marks) < 2:
            sys.exit("the scale of %s could not be measured: the two white squares were not found in the render" % board)
        d_px = math.hypot(marks[1][0] - marks[0][0], marks[1][1] - marks[0][1])
        d_mm = math.hypot(pts[1][0] - pts[0][0], pts[1][1] - pts[0][1])
        k = (d_px / d_mm) / (zoom0 * fh0)
        # 2. the real render, framed to hold the board: the frame is asked 64 px bigger than the window
        pad = 64
        fh, fw = int(round((bh + 2 * margin) * ppm)) + pad, int(round((bw + 2 * margin) * ppm)) + pad
        open(os.path.join(tmp, name + ".kicad_pcb"), "w", encoding="utf8").write(RK.with_stackup(src))
        im = kicad_render(tmp, name, fw, fh, ppm / (k * fh))
        cx, cy = (bx0 + bx1) / 2.0, (by0 + by1) / 2.0     # the image centre is the Edge.Cuts centre (measured on the marks to 0.1 mm)
        w, h = int(round((bw + 2 * margin) * ppm)), int(round((bh + 2 * margin) * ppm))
        x0, y0 = round(im.size[0] / 2.0 - (bw / 2.0 + margin) * ppm), round(im.size[1] / 2.0 - (bh / 2.0 + margin) * ppm)
        if x0 < 0 or y0 < 0 or x0 + w > im.size[0] or y0 + h > im.size[1]:
            sys.exit("the frame of %s is smaller than the board and its margin (%s px, window %d x %d)" % (board, im.size, w, h))
        im.crop((x0, y0, x0 + w, y0 + h)).save(out)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def save(im, path, limit=3 * 1024 * 1024):
    """A PNG under the size limit: full colour first, then a palette."""
    im.save(path, optimize=True)
    if os.path.getsize(path) > limit:
        im.convert("P", palette=1, colors=160).save(path, optimize=True)
    assert im.size[0] <= 2400 and os.path.getsize(path) <= limit, "%s is too large" % path


def main():
    from PIL import Image, ImageDraw, ImageFont
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("outdir")
    ap.add_argument("--gold", default="divider", choices=("ladder", "divider", "fans", "guilloche"))
    ap.add_argument("--px-per-mm", type=float, default=12.0)
    ap.add_argument("--leaders", default=None, choices=("slope", "level", "dogleg", "centred"),
                    help="the fascia's leader style (tools/fascia_art.py; default slope, the committed face); the picture's name carries it")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="fab_preview.")
    art = os.path.join(tmp, "TS06-FASCIA-R-%s.kicad_pcb" % a.gold)
    r = subprocess.run([sys.executable, os.path.join(HERE, "fascia_gold.py"), a.gold, art, "--base", "R"]
                       + (["--leaders", a.leaders] if a.leaders else []), capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("fascia_gold.py failed:\n%s%s" % (r.stdout, r.stderr))
    fascia = os.path.join(a.outdir, "fascia-R-%s%s-top.png" % (a.gold, "-" + a.leaders if a.leaders and a.leaders != "slope" else ""))
    render(art, fascia, a.px_per_mm)
    print("wrote", fascia)
    # the three boards, labelled, at a scale that keeps the width under 2400 px
    ppm = min(a.px_per_mm, 11.0)
    parts = [("TS06-DISP rev B: the tubes (front face)", os.path.join(ROOT, "PCB", "TS06-DISP", "TS06-DISP.kicad_pcb")),
             ("TS06-DRV rev B: the driver (front face)", os.path.join(ROOT, "PCB", "TS06-DRV", "TS06-DRV.kicad_pcb")),
             ("Fascia R (TS06-FASCIA-rhythm rev A) with the %s gold" % a.gold, art)]
    ims = []
    for label, b in parts:
        out = os.path.join(tmp, os.path.basename(b) + ".png")
        render(b, out, ppm)
        ims.append((label, Image.open(out).convert("RGB")))
    W = max(i.size[0] for _, i in ims)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 30)
    except OSError:
        font = ImageFont.load_default()
    bar = 54
    H = sum(i.size[1] + bar for _, i in ims)
    sheet = Image.new("RGB", (W, H), (245, 245, 242))
    d = ImageDraw.Draw(sheet)
    y = 0
    for label, im in ims:
        d.text((16, y + 10), label, fill=(20, 20, 20), font=font)
        sheet.paste(im, (0, y + bar))
        y += bar + im.size[1]
    out = os.path.join(a.outdir, "three-boards-top.png")
    save(sheet, out)
    save(Image.open(fascia).convert("RGB"), fascia)
    print("wrote", out, "%d x %d px, %d kB" % (sheet.size[0], sheet.size[1], os.path.getsize(out) // 1024))
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
