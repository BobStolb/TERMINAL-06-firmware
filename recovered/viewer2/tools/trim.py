#!/usr/bin/env python3
"""Trim the transparent margin KiCad leaves around a render, keeping a small border.

    python3 trim.py PNG...

Optional: needs Pillow. Without it the renders are left as they are and this prints a note.
"""
import sys

try:
    from PIL import Image
except ImportError:
    print("  trim: Pillow not installed, renders left untrimmed")
    sys.exit(0)

for p in sys.argv[1:]:
    im = Image.open(p)
    if im.mode != "RGBA":
        continue
    bb = im.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
    if not bb:
        continue
    pad = int(0.04 * max(bb[2] - bb[0], bb[3] - bb[1]))
    box = (max(0, bb[0] - pad), max(0, bb[1] - pad), min(im.width, bb[2] + pad), min(im.height, bb[3] + pad))
    im.crop(box).save(p, optimize=True)
print("  trim: %d renders cropped to the board" % (len(sys.argv) - 1))
