#!/usr/bin/env python3
"""The pictures of the three boards as they are ordered, from the committed board files (KiCad 10's own 3D renderer).

    python3 tools/fab_preview.py OUTDIR [--gold divider] [--px-per-mm 12]

writes into OUTDIR (it is made if missing):
    fascia-R-divider-top.png    the fascia R (TS06-FASCIA-rhythm, rev A) with the gold, seen from the front
    three-boards-top.png        TS06-DISP, TS06-DRV and the fascia, top views, one under the other, labelled

The fascia is the art board that tools/fascia_gold.py builds in a scratch directory (nothing under PCB/ is
written). Every picture comes from tools/render_kicad.py: black mask, white silk, ENIG where the mask is open.
PNGs are kept under 2400 px wide and 3 MB. KiCad runs in Docker, or from KICAD_CLI, as tools/verify_pair.sh.
"""
import argparse, os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def render(board, out, ppm):
    r = subprocess.run([sys.executable, os.path.join(HERE, "render_kicad.py"), board, out, "--side", "top", "--px-per-mm", str(ppm)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("render_kicad.py failed on %s:\n%s%s" % (board, r.stdout, r.stderr))


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
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="fab_preview.")
    art = os.path.join(tmp, "TS06-FASCIA-R-%s.kicad_pcb" % a.gold)
    r = subprocess.run([sys.executable, os.path.join(HERE, "fascia_gold.py"), a.gold, art, "--base", "R"], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("fascia_gold.py failed:\n%s%s" % (r.stdout, r.stderr))
    fascia = os.path.join(a.outdir, "fascia-R-%s-top.png" % a.gold)
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
