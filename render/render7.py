#!/usr/bin/env python3
"""Massing study — the side view, 1:1, four ways.

The rejection was proportional, not decorative: the Rev E/F body is 104 mm
deep to carry a display stack 27 mm deep. Seen from the side that is a slab
with three quarters of nothing in it.

Two things change the arithmetic:
  * the real tube is 19.47 wide, not 22, so the row tightens and the face
    drops from 237 to ~195;
  * if the board is meant to be looked at, the case is an EDGE, not a box.

Every option below is drawn at 1:1 against the same ground line with the
same correctly-sized tube, so the only thing being compared is proportion.

Run: python3 render7.py  ->  m-massing.svg
"""
import math, os

import tubes as T

OUT = os.path.dirname(os.path.abspath(__file__))
MONO = "IBM Plex Mono, monospace"
COND = "IBM Plex Sans Condensed, Arial Narrow, sans-serif"
WARM, DEEP, HOT = "#FF9E36", "#FF5A08", "#FFE0BC"
ACC = "#F25610"
DIM = "#8FA4B2"
CASE = "#252A30"
CASE_E = "#454D55"
PCB = "#12181C"          # black mask
PCB_E = "#3A4A52"
COP = "#8A6A3A"          # exposed copper pattern

ENV_H, ENV_D = 28.86, 25.50
BOARD_T = 1.60

GY = 176.0               # shared ground line


def txt(x, y, s, size=3.0, fill=DIM, anchor="middle", family=MONO,
        weight="400", ls=".4"):
    return (f'<text x="{x:.2f}" y="{y:.2f}" font-family="{family}" '
            f'font-size="{size:.2f}" fill="{fill}" text-anchor="{anchor}" '
            f'font-weight="{weight}" letter-spacing="{ls}">{s}</text>')


def tube_side(o, x, ybot, lit=True):
    """The tube in side elevation: glass face at x, barrel running back."""
    y = GY - ybot - ENV_H
    o.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{ENV_D}" height="{ENV_H}" '
             f'rx="1.2" fill="#1B2026" stroke="#5C6771" stroke-width=".55"/>')
    o.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="2.2" height="{ENV_H}" '
             f'fill="{WARM}" opacity="{.34 if lit else .1}"/>')
    # pins into whatever is behind
    for i in range(5):
        yy = y + ENV_H / 2 - 8 + i * 4
        o.append(f'<line x1="{x+ENV_D:.2f}" y1="{yy:.2f}" x2="{x+ENV_D+4.4:.2f}" '
                 f'y2="{yy:.2f}" stroke="#9AA6B0" stroke-width=".45"/>')
    return y


def board(o, x, ytop, h, label=None, copper=True):
    o.append(f'<rect x="{x:.2f}" y="{ytop:.2f}" width="{BOARD_T}" height="{h:.2f}" '
             f'fill="{PCB}" stroke="{PCB_E}" stroke-width=".4"/>')
    if copper:
        for i in range(int(h / 7)):
            yy = ytop + 4 + i * 7
            o.append(f'<line x1="{x+.2:.2f}" y1="{yy:.2f}" x2="{x+BOARD_T-.2:.2f}" '
                     f'y2="{yy:.2f}" stroke="{COP}" stroke-width=".5" opacity=".7"/>')


def dimh(o, x1, x2, y, label, col=DIM, size=2.9):
    o.append(f'<line x1="{x1:.2f}" y1="{y:.2f}" x2="{x2:.2f}" y2="{y:.2f}" '
             f'stroke="{col}" stroke-width=".4"/>')
    for x in (x1, x2):
        o.append(f'<line x1="{x:.2f}" y1="{y-1.8:.2f}" x2="{x:.2f}" y2="{y+1.8:.2f}" '
                 f'stroke="{col}" stroke-width=".4"/>')
    o.append(txt((x1 + x2) / 2, y + 4.4, label, size, col))


def dimv(o, y1, y2, x, label, col=DIM, size=2.9):
    o.append(f'<line x1="{x:.2f}" y1="{y1:.2f}" x2="{x:.2f}" y2="{y2:.2f}" '
             f'stroke="{col}" stroke-width=".4"/>')
    for y in (y1, y2):
        o.append(f'<line x1="{x-1.8:.2f}" y1="{y:.2f}" x2="{x+1.8:.2f}" y2="{y:.2f}" '
                 f'stroke="{col}" stroke-width=".4"/>')
    o.append(txt(x - 2.4, (y1 + y2) / 2 + 1.1, label, size, col, anchor="end"))


def head(o, x, w, tag, name, thesis, col="#C8C4BC"):
    o.append(txt(x, 26, tag, 3.0, "#5A6169", anchor="start"))
    o.append(txt(x, 33, name, 5.2, col, anchor="start", family=COND, weight="700",
                 ls=".5"))
    for i, line in enumerate(thesis):
        o.append(txt(x, 40 + i * 4.2, line, 2.8, "#7E858D", anchor="start"))


def foot(o, x, w, dims, note, col=DIM):
    o.append(txt(x, GY + 16, dims, 3.2, col, anchor="start", weight="600"))
    for i, line in enumerate(note):
        o.append(txt(x, GY + 22 + i * 4.0, line, 2.7, "#6B737B", anchor="start"))


# ============================================================== A — rejected
def opt_a(o, x):
    head(o, x, 120, "A · AS DRAWN", "THE SLAB",
         ["104 deep to carry a 27 mm stack.", "The side view is mostly nothing."],
         col="#8A6A5A")
    BH, BD, LEAN = 56.0, 104.0, 12.0
    o.append(f'<polygon points="{x:.1f},{GY:.1f} {x+BD:.1f},{GY:.1f} '
             f'{x+BD:.1f},{GY-BH:.1f} {x+LEAN:.1f},{GY-BH:.1f}" '
             f'fill="{CASE}" stroke="{CASE_E}" stroke-width=".6"/>')
    # the dead volume
    o.append(f'<rect x="{x+30:.1f}" y="{GY-BH:.1f}" width="{BD-30:.1f}" '
             f'height="{BH:.1f}" fill="#3A2418" opacity=".55"/>')
    o.append(txt(x + 66, GY - 26, "77 mm of", 3.0, "#C0714A"))
    o.append(txt(x + 66, GY - 21, "empty case", 3.0, "#C0714A"))
    ty = tube_side(o, x, 62.0)
    board(o, x + ENV_D, ty - 2, ENV_H + 4)
    dimh(o, x, x + BD, GY + 6, "104 deep", col="#C0714A")
    dimv(o, GY - 90.86, GY, x - 6, "91")
    foot(o, x, 120, "237 × 91 × 104",
         ["The proportion you rejected — kept only",
          "so the other three can be judged against",
          "something."],
         col="#8A6A5A")


# ============================================================== B — sill
def opt_b(o, x):
    head(o, x, 120, "B · SILL", "THE LEDGE",
         ["Case shrinks to a control sill.", "Boards sit behind it, on show."])
    SH, SD = 26.0, 46.0
    o.append(f'<polygon points="{x:.1f},{GY:.1f} {x+SD:.1f},{GY:.1f} '
             f'{x+SD:.1f},{GY-SH:.1f} {x+5:.1f},{GY-SH:.1f}" '
             f'fill="{CASE}" stroke="{CASE_E}" stroke-width=".6"/>')
    o.append(f'<circle cx="{x+16:.1f}" cy="{GY-SH-0.1:.1f}" r="4.6" fill="#343A42" '
             f'stroke="#79818B" stroke-width=".5"/>')
    o.append(txt(x + 16, GY - SH - 7, "controls on top", 2.6, "#6B737B"))
    ty = tube_side(o, x + 4.0, SH + 4.0)
    board(o, x + 4.0 + ENV_D, ty - 4, ENV_H + 10)
    # main board, vertical, behind
    board(o, x + 40.0, GY - 54, 40, copper=True)
    o.append(txt(x + 44, GY - 34, "main board,", 2.6, "#8FA4B2", anchor="start"))
    o.append(txt(x + 44, GY - 30, "vertical,", 2.6, "#8FA4B2", anchor="start"))
    o.append(txt(x + 44, GY - 26, "on show", 2.6, "#8FA4B2", anchor="start"))
    dimh(o, x, x + 52, GY + 6, "52 deep")
    dimv(o, GY - 64.9, GY, x - 6, "65")
    foot(o, x, 120, "195 × 65 × 52",
         ["Half the depth. The sill is the only", "moulded part; everything else is board."])


# ============================================================== C — frame
def opt_c(o, x):
    head(o, x, 120, "C · FRAME", "THE CHEEKS",
         ["Two end plates, nothing between.", "The boards ARE the structure."])
    CW, CH = 44.0, 66.0
    # a plate that tapers to the front, so the side reads as a fin not a box
    o.append(f'<path d="M{x+3:.1f} {GY:.1f} L{x+CW:.1f} {GY:.1f} '
             f'L{x+CW:.1f} {GY-CH+4:.1f} Q{x+CW:.1f} {GY-CH:.1f} {x+CW-4:.1f} {GY-CH:.1f} '
             f'L{x+20:.1f} {GY-CH:.1f} L{x+3:.1f} {GY-CH+26:.1f} Z" '
             f'fill="{CASE}" stroke="{CASE_E}" stroke-width=".6"/>')
    o.append(f'<rect x="{x+12:.1f}" y="{GY-CH+22:.1f}" width="24" height="{CH-34:.1f}" '
             f'rx="3" fill="#0E1216" stroke="#3A4149" stroke-width=".4"/>')
    ty = tube_side(o, x + 2.0, 30.0)
    board(o, x + 2.0 + ENV_D, ty - 5, ENV_H + 12)
    board(o, x + 8.0, GY - 13, 11, copper=True)
    dimh(o, x, x + CW, GY + 6, "44 deep")
    dimv(o, GY - CH, GY, x - 6, "66")
    foot(o, x, 120, "195 × 66 × 44",
         ["Lightest of the four. Window through the",
          "cheek. Controls move to a cheek or the",
          "front edge of the main board."])


# ============================================================== D — panel
def opt_d(o, x):
    head(o, x, 120, "D · PANEL", "THE BACKPLATE",
         ["One black board is the whole rear.", "Tubes stand off the front of it."])
    o.append(f'<path d="M{x+16:.1f} {GY:.1f} L{x+40:.1f} {GY:.1f} '
             f'L{x+34:.1f} {GY-16:.1f} L{x+22:.1f} {GY-16:.1f} Z" '
             f'fill="{CASE}" stroke="{CASE_E}" stroke-width=".6"/>')
    o.append(txt(x + 28, GY + 1.5, "foot", 2.6, "#6B737B"))
    board(o, x + 27.0, GY - 82, 68, copper=True)
    o.append(f'<rect x="{x+27.0:.1f}" y="{GY-82:.1f}" width="{BOARD_T}" height="68" '
             f'fill="none" stroke="{ACC}" stroke-width=".5" opacity=".8"/>')
    ty = tube_side(o, x + 1.5, 40.0)
    o.append(txt(x + 34, GY - 74, "the panel is", 2.6, ACC, anchor="start"))
    o.append(txt(x + 34, GY - 70, "the product", 2.6, ACC, anchor="start"))
    o.append(txt(x + 34, GY - 44, "controls on", 2.6, "#8FA4B2", anchor="start"))
    o.append(txt(x + 34, GY - 40, "its lower half", 2.6, "#8FA4B2", anchor="start"))
    dimh(o, x, x + 36, GY + 6, "36 deep")
    dimv(o, GY - 82, GY, x - 6, "82")
    foot(o, x, 120, "195 × 82 × 36",
         ["Thinnest, and the most exposed board.", "Reads as an instrument, not a clock."])


def main():
    W, H = 566.0, 232.0
    o = [f'<rect x="0" y="0" width="{W}" height="{H}" fill="#0B0D10"/>']
    o.append(txt(W / 2, 13, "MASSING STUDY — THE SIDE VIEW, 1:1", 7.2, "#E4E1DA",
                 family=COND, weight="700", ls=".6"))
    o.append(txt(W / 2, 19.5,
                 "same ground line · same tube · the only variable is proportion",
                 3.2, "#6B737B"))
    o.append(f'<line x1="10" y1="{GY:.1f}" x2="{W-10:.1f}" y2="{GY:.1f}" '
             f'stroke="#3A4149" stroke-width=".6"/>')

    opt_a(o, 26.0)
    opt_b(o, 166.0)
    opt_c(o, 300.0)
    opt_d(o, 428.0)

    for xx in (152.0, 286.0, 414.0):
        o.append(f'<line x1="{xx:.1f}" y1="24" x2="{xx:.1f}" y2="{GY+34:.1f}" '
                 f'stroke="#1C2126" stroke-width=".6"/>')

    o.append(txt(W / 2, H - 8,
                 "Face drops 237 → 195 in B/C/D because the real tube is 19.47 wide, "
                 "not 22 — the row tightens by 42 mm. ИН-17 and ИН-15 still unmodelled.",
                 2.9, "#5A6169"))

    defs = '<defs>' + T.tube_defs("ms", warm=WARM, deep=DEEP) + '</defs>'
    svg = ('<svg preserveAspectRatio="xMidYMid meet" viewBox="0 0 %.1f %.1f" '
           'xmlns="http://www.w3.org/2000/svg" role="img">%s\n%s</svg>'
           % (W, H, defs, "\n".join(o)))
    with open(os.path.join(OUT, "m-massing.svg"), "w") as f:
        f.write(svg)
    print("m-massing.svg", len(svg))


if __name__ == "__main__":
    main()
