#!/usr/bin/env python3
"""Render a board's face with KiCad 10's own 3D renderer, as the fab would build it:
black solder mask, white silkscreen, ENIG where the mask is open.

    python3 tools/render_kicad.py BOARD.kicad_pcb OUT.png [--side top|bottom] [--px-per-mm 16]
                                  [--crop X0,Y0,X1,Y1] [--also X0,Y0,X1,Y1:OUT2.png ...]
                                  [--quality high|basic]

The board is copied to a scratch directory first and never written. If its (setup) has no
(stackup), the black-mask / white-silk / ENIG one that TS06-DISP and TS06-DRV carry is put in
the copy, so the render shows the colours ordered rather than KiCad's default green.

The view is orthographic, straight down, so board millimetres map linearly onto pixels:
--px-per-mm sets the scale and --crop a window in board coordinates (default: the Edge.Cuts
extent plus 2 mm); --also cuts more windows from the same render. Measured on KiCad 10.0: at
zoom 1 the frame's height spans the diagonal of the board's Edge.Cuts box, and the PNG comes
back a few pixels smaller than asked for; so the zoom is set from the diagonal, and the image
is resampled (Pillow) to the exact scale before the windows are cut.

KiCad comes from KICAD_CLI (a local kicad-cli), or from Docker with the image in KICAD_IMAGE
(default mirror.gcr.io/kicad/kicad:10.0), as tools/verify_pair.sh runs it.
"""
import argparse, os, re, shutil, subprocess, sys, tempfile

IMG = os.environ.get("KICAD_IMAGE", "mirror.gcr.io/kicad/kicad:10.0")

STACKUP = """\t\t(stackup
\t\t\t(layer "F.SilkS"
\t\t\t\t(type "Top Silk Screen")
\t\t\t\t(color "White")
\t\t\t)
\t\t\t(layer "F.Mask"
\t\t\t\t(type "Top Solder Mask")
\t\t\t\t(color "Black")
\t\t\t\t(thickness 0.01)
\t\t\t)
\t\t\t(layer "F.Cu"
\t\t\t\t(type "copper")
\t\t\t\t(thickness 0.035)
\t\t\t)
\t\t\t(layer "dielectric 1"
\t\t\t\t(type "core")
\t\t\t\t(thickness %s)
\t\t\t\t(material "FR4")
\t\t\t\t(epsilon_r 4.5)
\t\t\t\t(loss_tangent 0.02)
\t\t\t)
\t\t\t(layer "B.Cu"
\t\t\t\t(type "copper")
\t\t\t\t(thickness 0.035)
\t\t\t)
\t\t\t(layer "B.Mask"
\t\t\t\t(type "Bottom Solder Mask")
\t\t\t\t(color "Black")
\t\t\t\t(thickness 0.01)
\t\t\t)
\t\t\t(layer "B.SilkS"
\t\t\t\t(type "Bottom Silk Screen")
\t\t\t\t(color "White")
\t\t\t)
\t\t\t(copper_finish "ENIG")
\t\t\t(dielectric_constraints no)
\t\t)
"""


def extent(src):
    xs, ys = [], []
    for m in re.finditer(r'\((gr_line|gr_arc|gr_rect|gr_poly|gr_circle)\b[\s\S]*?\(layer "Edge\.Cuts"\)', src):
        for x, y in re.findall(r'\((?:start|mid|end|xy|center) ([\d.-]+) ([\d.-]+)\)', m.group(0)):
            xs.append(float(x))
            ys.append(float(y))
    if not xs:
        sys.exit("no Edge.Cuts in the board")
    return min(xs), min(ys), max(xs), max(ys)


def with_stackup(src):
    if "(stackup" in src:
        return src
    th = re.search(r'\(general\s+\(thickness ([\d.]+)\)', src)
    core = "%.3f" % (float(th.group(1)) - 0.09) if th else "1.51"
    i = src.index("(setup") + len("(setup")
    return src[:i] + "\n" + (STACKUP % core).rstrip("\n") + src[i:]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("board")
    ap.add_argument("out")
    ap.add_argument("--side", default="top")
    ap.add_argument("--px-per-mm", type=float, default=16.0)
    ap.add_argument("--crop", default="")
    ap.add_argument("--quality", default="high")
    ap.add_argument("--also", action="append", default=[], metavar="X0,Y0,X1,Y1:OUT.png",
                    help="another window from the same render (repeatable)")
    a = ap.parse_args()

    src = open(a.board, encoding="utf8").read()
    bx0, by0, bx1, by1 = extent(src)
    # The whole board is rendered, centred (KiCad centres the Edge.Cuts box in the frame), with
    # a 2 mm margin; the window is cut from that afterwards. (--pan was tried: its offset is not
    # the camera's in board millimetres, so the window is not panned to.)
    fx0, fy0, fx1, fy1 = bx0 - 2, by0 - 2, bx1 + 2, by1 + 2
    fw, fh = int(round((fx1 - fx0) * a.px_per_mm)), int(round((fy1 - fy0) * a.px_per_mm))
    diag = ((bx1 - bx0) ** 2 + (by1 - by0) ** 2) ** 0.5   # mm down the frame's height at zoom 1
    zoom = a.px_per_mm * diag / fh
    jobs = [(a.crop, a.out)] + [tuple(x.split(":", 1)) for x in a.also]

    tmp = tempfile.mkdtemp(prefix="render_kicad.")
    try:
        name = os.path.splitext(os.path.basename(a.board))[0]
        open(os.path.join(tmp, name + ".kicad_pcb"), "w", encoding="utf8").write(with_stackup(src))
        here = os.path.dirname(os.path.abspath(a.board))
        for ext in (".kicad_pro",):
            p = os.path.join(here, name + ext)
            if os.path.exists(p):
                shutil.copy(p, tmp)
        os.chmod(tmp, 0o777)
        args = ["pcb", "render", "--side", a.side, "--width", str(fw), "--height", str(fh),
                "--quality", a.quality, "--background", "opaque", "--use-board-stackup-colors",
                "--zoom", "%.5f" % zoom]
        cli = os.environ.get("KICAD_CLI")
        if cli:
            cmd = [cli] + args + ["-o", os.path.join(tmp, "out.png"), os.path.join(tmp, name + ".kicad_pcb")]
        else:
            cmd = ["docker", "run", "--rm", "--user", "%d:%d" % (os.getuid(), os.getgid()), "-v", tmp + ":/w",
                   "-w", "/w", "-e", "HOME=/tmp", IMG, "kicad-cli"] + args + ["-o", "/w/out.png", "/w/%s.kicad_pcb" % name]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(os.path.join(tmp, "out.png")):
            sys.exit("kicad-cli failed:\n" + r.stdout + r.stderr)
        from PIL import Image
        im = Image.open(os.path.join(tmp, "out.png")).convert("RGB")
        s_got = im.size[1] * zoom / diag                   # px per mm as rendered
        k = a.px_per_mm / s_got
        im = im.resize((max(1, round(im.size[0] * k)), max(1, round(im.size[1] * k))), Image.LANCZOS)
        # board (x, y) -> pixel: the image centre is the Edge.Cuts box centre
        ccx, ccy = (bx0 + bx1) / 2.0, (by0 + by1) / 2.0
        for crop, out in jobs:
            x0, y0, x1, y1 = (float(v) for v in crop.split(",")) if crop else (fx0, fy0, fx1, fy1)
            if a.side == "bottom":                         # seen from behind: x runs the other way
                x0, x1 = 2 * ccx - x1, 2 * ccx - x0
            px0 = round(im.size[0] / 2.0 + (x0 - ccx) * a.px_per_mm)
            py0 = round(im.size[1] / 2.0 + (y0 - ccy) * a.px_per_mm)
            w, h = int(round((x1 - x0) * a.px_per_mm)), int(round((y1 - y0) * a.px_per_mm))
            o = Image.new("RGB", (w, h), (0, 0, 0))
            o.paste(im, (-px0, -py0))
            o.save(out)
            print("wrote %s (%d x %d px, %.2f px/mm, window %.2f,%.2f - %.2f,%.2f)" % (out, w, h, a.px_per_mm, x0, y0, x1, y1))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
