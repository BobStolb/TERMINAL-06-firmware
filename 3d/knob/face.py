#!/usr/bin/env python3
"""Put the knobs' top views on fascia R's face, at scale (a flat picture, not a render of the real thing).

    python3 -I face.py            # run from 3d/knob/ after the build/top_*.png top views exist (see make.sh)

The face is `fab/preview/fascia-R-divider-top.png` (the ordered fascia R with the Divider gold, drawn from the Gerbers'
board file). Its scale was measured on the picture: the board is 2310 x 482 px for 191.4 x 40 mm, so 12.07 px/mm, with the
board's top-left corner at (17, 23) px; the dial's shaft is at (24.89, 16.0) mm from that corner (tools/fascia_art.py).
The knob top views come from OpenSCAD (orthographic, 25.1 px/mm, measured with a 20 mm disc) and are rotated in the plane to
the dial's six positions (75, 45, 15, -15, -45, -75 degrees; 30.00 per step, position 1 at the top). A top view rotated in the
image is the same picture as the knob turned on its shaft, to within the shading. The knob is drawn over the art: it hides
what is under it, and what it leaves in view is what the owner would see from the front, square on.
"""
import math, os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
FACE = os.path.join(ROOT, "fab", "preview", "fascia-R-divider-top.png")
PXMM_FACE = 2310 / 191.4
ORIGIN = (17, 23)
DIAL = (24.89, 16.0)
PXMM_KNOB = 25.1
BG = (255, 255, 229)
POS = [75, 45, 15, -15, -45, -75]
NAMES = ["1 NORMAL", "2 SET TIME", "3 DISPLAY", "4 AMBIENT", "5 FORMAT/DATE", "6 INFO"]


def knob_layer(path, scale):
    """The top view with its background keyed out, scaled to the face's px/mm, cropped square round the shaft."""
    im = Image.open(path).convert("RGB")
    a = Image.new("L", im.size, 0)
    px, ap = im.load(), a.load()
    for y in range(im.size[1]):
        for x in range(im.size[0]):
            r, g, b = px[x, y]
            if abs(r - BG[0]) + abs(g - BG[1]) + abs(b - BG[2]) > 24:
                ap[x, y] = 255
    im = im.convert("RGBA")
    im.putalpha(a)
    half = 330                                   # px at 25.1 px/mm: 13 mm round the shaft
    c = im.size[0] // 2
    im = im.crop((c - half, c - half, c + half, c + half))
    f = scale / PXMM_KNOB
    n = int(round(2 * half * f))
    return im.resize((n, n), Image.LANCZOS)


def face_crop(face, x0_mm, y0_mm, w_mm, h_mm, scale):
    """A window of the face in mm from the board's corner, scaled to `scale` px/mm."""
    x0 = ORIGIN[0] + x0_mm * PXMM_FACE
    y0 = ORIGIN[1] + y0_mm * PXMM_FACE
    box = (int(x0), int(y0), int(x0 + w_mm * PXMM_FACE), int(y0 + h_mm * PXMM_FACE))
    im = face.crop(box)
    return im.resize((int(round(w_mm * scale)), int(round(h_mm * scale))), Image.LANCZOS)


def paste_knob(canvas, layer, ang, cx_mm, cy_mm, x0_mm, y0_mm, scale):
    rot = layer.rotate(ang, resample=Image.BICUBIC)   # counterclockwise on the screen = counterclockwise in the front view
    cx = (cx_mm - x0_mm) * scale
    cy = (cy_mm - y0_mm) * scale
    canvas.alpha_composite(rot, (int(round(cx - rot.size[0] / 2)), int(round(cy - rot.size[1] / 2))))


def font(size):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/freefont/FreeSans.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def grid(face, layer, out, title):
    """The six positions, one crop each (dial and its names), 3 x 2, at the face's own scale."""
    scale = PXMM_FACE
    w_mm, h_mm = 58.0, 36.0                      # window: x 0..58, y 0..36 mm (the dial, its names and the SET/INFO leaders)
    cw, ch = int(w_mm * scale), int(h_mm * scale)
    pad = 10
    head = 46
    W = 3 * cw + 4 * pad
    H = 2 * (ch + 28) + 3 * pad + head
    sheet = Image.new("RGBA", (W, H), (24, 26, 30, 255))
    d = ImageDraw.Draw(sheet)
    d.text((pad, 10), title, fill=(230, 230, 230), font=font(22))
    for i, ang in enumerate(POS):
        col, row = i % 3, i // 3
        x = pad + col * (cw + pad)
        y = head + pad + row * (ch + 28 + pad)
        base = face_crop(face, 0, 0, w_mm, h_mm, scale).convert("RGBA")
        paste_knob(base, layer, ang, DIAL[0], DIAL[1], 0, 0, scale)
        sheet.alpha_composite(base, (x, y + 28))
        d.text((x + 4, y + 2), NAMES[i] + "   pointer at %+d deg" % ang, fill=(240, 200, 90), font=font(18))
    sheet.convert("RGB").save(out)
    print(out, sheet.size)


def compare(face, panels, out, title, ang=POS[2]):
    """Several knobs side by side at one position, 2 x n, larger (2 x the face's scale for a closer look)."""
    scale = PXMM_FACE * 1.5
    w_mm, h_mm = 52.0, 36.0
    cw, ch = int(w_mm * scale), int(h_mm * scale)
    pad, head = 10, 46
    cols = 2
    rows = (len(panels) + 1) // 2
    W = cols * cw + (cols + 1) * pad
    H = rows * (ch + 28) + (rows + 1) * pad + head
    sheet = Image.new("RGBA", (W, H), (24, 26, 30, 255))
    d = ImageDraw.Draw(sheet)
    d.text((pad, 10), title, fill=(230, 230, 230), font=font(22))
    for i, (label, layer) in enumerate(panels):
        col, row = i % cols, i // cols
        x = pad + col * (cw + pad)
        y = head + pad + row * (ch + 28 + pad)
        base = face_crop(face, 0, 0, w_mm, h_mm, scale).convert("RGBA")
        layer_s = layer.resize((int(layer.size[0] * 1.5), int(layer.size[1] * 1.5)), Image.LANCZOS)
        paste_knob(base, layer_s, ang, DIAL[0], DIAL[1], 0, 0, scale)
        sheet.alpha_composite(base, (x, y + 28))
        d.text((x + 4, y + 2), label, fill=(240, 200, 90), font=font(18))
    sheet.convert("RGB").save(out)
    print(out, sheet.size)


def main():
    b = os.path.join(HERE, "build")
    face = Image.open(FACE).convert("RGB")
    A = knob_layer(os.path.join(b, "top_A.png"), PXMM_FACE)
    Ac = knob_layer(os.path.join(b, "top_A_cream.png"), PXMM_FACE)
    B = knob_layer(os.path.join(b, "top_B.png"), PXMM_FACE)
    C = knob_layer(os.path.join(b, "top_C.png"), PXMM_FACE)
    grid(face, A, os.path.join(HERE, "face_A-six-positions.png"), "Knob A (РСИ reading, D = 18) on fascia R: the six positions")
    grid(face, B, os.path.join(HERE, "face_B-six-positions.png"), "Knob B (beak, tip radius 9) on fascia R: the six positions")
    grid(face, C, os.path.join(HERE, "face_C-six-positions.png"), "Knob C (turned, D = 18) on fascia R: the six positions")
    compare(face, [("A  gold fill", A), ("A  cream fill (as the original)", Ac), ("B  beak", B), ("C  turned aluminium, bright line", C)],
            os.path.join(HERE, "face_compare.png"), "The knobs on fascia R, position 3 (DISPLAY), 18 mm")


if __name__ == "__main__":
    main()
