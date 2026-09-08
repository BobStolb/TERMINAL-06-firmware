#!/usr/bin/env python3
"""ИН-12А component reference — drawn from IN12.FCStd, not from assumption.

Every number here comes from the spreadsheet inside the user's own FreeCAD
model (3d/IN12.FCStd, aliases envW/envH/envD/pinD/pinFreeL/pipD/...), which
supersedes the 22 x 24 x 14 envelope the Rev E.2 plates were drawn with.

The correction that matters is not a dimension, it is an architecture: the
leads leave the BACK of this tube, so it cannot stand on a deck over a
socket. It hangs off a board behind it, facing forward.

Run: python3 render5.py   ->  r-in12-reference.svg, r-in12-mounting.svg
"""
import math, os

import tubes as T

OUT = os.path.dirname(os.path.abspath(__file__))
MONO = "IBM Plex Mono, monospace"
COND = "IBM Plex Sans Condensed, Arial Narrow, sans-serif"
WARM, DEEP, HOT = "#FF9E36", "#FF5A08", "#FFE0BC"
ACC = "#F25610"
DIMC = "#8FA4B2"

# ------------------------------------------------------- from IN12.FCStd
ENV_W, ENV_H, ENV_D = 19.47, 28.86, 25.50     # envelope, mm
PIN_D, PIN_FREE_L   = 0.92, 6.25              # pin diameter, free length
PIN_N               = 12
PIN_R_NEAR          = 6.20                    # ClosestPinRad
PIN_R_FAR           = 8.50                    # fARTHpINRad
PIP_D               = 3.70                    # tip-off pip
DIGIT_H             = 18.63                   # calipered 27.08
BOARD_T             = 1.60                    # TS06-TUBE, assumed 1.6 mm

S = 3.4                                        # px per mm on these sheets


def txt(x, y, s, size=3.0, fill=DIMC, anchor="middle", family=MONO,
        weight="400", ls=".4", extra=""):
    return (f'<text x="{x:.2f}" y="{y:.2f}" font-family="{family}" '
            f'font-size="{size:.2f}" fill="{fill}" text-anchor="{anchor}" '
            f'font-weight="{weight}" letter-spacing="{ls}"{extra}>{s}</text>')


def dimh(o, x1, x2, y, label, col=DIMC, size=3.0, above=True):
    o.append(f'<line x1="{x1:.2f}" y1="{y:.2f}" x2="{x2:.2f}" y2="{y:.2f}" '
             f'stroke="{col}" stroke-width=".4"/>')
    for x in (x1, x2):
        o.append(f'<line x1="{x:.2f}" y1="{y-2:.2f}" x2="{x:.2f}" y2="{y+2:.2f}" '
                 f'stroke="{col}" stroke-width=".4"/>')
    o.append(txt((x1 + x2) / 2, y - 1.8 if above else y + 4.2, label, size, col))


def dimv(o, y1, y2, x, label, col=DIMC, size=3.0, anchor="start", dx=2.4):
    o.append(f'<line x1="{x:.2f}" y1="{y1:.2f}" x2="{x:.2f}" y2="{y2:.2f}" '
             f'stroke="{col}" stroke-width=".4"/>')
    for y in (y1, y2):
        o.append(f'<line x1="{x-2:.2f}" y1="{y:.2f}" x2="{x+2:.2f}" y2="{y:.2f}" '
                 f'stroke="{col}" stroke-width=".4"/>')
    o.append(txt(x + dx, (y1 + y2) / 2 + 1.1, label, size, col, anchor=anchor))


def pin_field(cx, cy, n=PIN_N, rx=PIN_R_NEAR, ry=PIN_R_FAR, start=-90.0):
    """The 12 pin centres, on the model's own near/far radii.

    IN12.FCStd carries ClosestPinRad 6.2 and fARTHpINRad 8.5, i.e. a field
    12.4 wide x 17.0 tall — which is exactly the X/Y span of the pin sketch
    in IN12.step. The *ordering* of the twelve around that field is the
    model's business; an even distribution is drawn here and labelled as
    such rather than guessed at pin by pin.
    """
    out = []
    for i in range(n):
        a = math.radians(start + i * (360.0 / n))
        out.append((cx + math.cos(a) * rx, cy + math.sin(a) * ry))
    return out


# =============================================== SHEET 1 — the part
def in12_reference():
    W, H = 250.0, 118.0
    o = [f'<rect x="0" y="0" width="{W}" height="{H}" fill="#0B0D10"/>']

    o.append(txt(W / 2, 11, "ИН-12А — THE PART, FROM IN12.FCStd", 6.0,
                 "#E4E1DA", family=COND, weight="700", ls=".6"))
    o.append(txt(W / 2, 17.5, "envelope · pin field · what the plates had wrong",
                 3.2, "#6B737B"))

    # ---------------- FRONT ELEVATION ----------------
    fx, fy = 30.0, 34.0
    o.append(txt(fx + ENV_W / 2, fy - 5, "FRONT", 3.4, "#C8C4BC", family=COND,
                 weight="700"))
    frag = T.tube_face("r1", ENV_W, ENV_H, "4", ghosts=True,
                       warm=WARM, hot=HOT, deep=DEEP,
                       digit_frac=DIGIT_H / ENV_H, ghost_op=.07,
                       spec_op=.7, mesh_op=.34, socket=False)
    o.append(f'<g transform="translate({fx:.2f} {fy:.2f})">{frag}</g>')
    dimh(o, fx, fx + ENV_W, fy + ENV_H + 8, f"{ENV_W}", above=False)
    dimv(o, fy, fy + ENV_H, fx - 7, f"{ENV_H}", anchor="end", dx=-2.4)
    dimv(o, fy + (ENV_H - DIGIT_H) / 2, fy + (ENV_H + DIGIT_H) / 2,
         fx + ENV_W + 6, f"{DIGIT_H} digit", col=ACC)

    # ---------------- REAR VIEW ----------------
    rx0, ry0 = 92.0, 34.0
    o.append(txt(rx0 + ENV_W / 2, ry0 - 5, "REAR", 3.4, "#C8C4BC", family=COND,
                 weight="700"))
    o.append(f'<rect x="{rx0:.2f}" y="{ry0:.2f}" width="{ENV_W}" height="{ENV_H}" '
             f'rx="1.4" fill="#171B20" stroke="#5C6771" stroke-width=".6"/>')
    cx, cy = rx0 + ENV_W / 2, ry0 + ENV_H / 2
    # field outline
    o.append(f'<ellipse cx="{cx:.2f}" cy="{cy:.2f}" rx="{PIN_R_NEAR}" '
             f'ry="{PIN_R_FAR}" fill="none" stroke="#3C444C" stroke-width=".35" '
             f'stroke-dasharray="1.6 1.4"/>')
    for (px, py) in pin_field(cx, cy):
        o.append(f'<circle cx="{px:.2f}" cy="{py:.2f}" r="{PIN_D/2*1.9:.2f}" '
                 f'fill="#9AA6B0" stroke="#20262C" stroke-width=".25"/>')
    # tip-off pip, off to one side
    o.append(f'<circle cx="{cx:.2f}" cy="{ry0 + ENV_H - 3.4:.2f}" r="{PIP_D/2:.2f}" '
             f'fill="#2A3138" stroke="#6E7883" stroke-width=".4"/>')
    o.append(txt(cx + PIP_D, ry0 + ENV_H - 2.6, f"pip ⌀{PIP_D}", 2.6, "#6B737B",
                 anchor="start"))
    dimh(o, cx - PIN_R_NEAR, cx + PIN_R_NEAR, ry0 + ENV_H + 4.5,
         f"{PIN_R_NEAR*2:.1f}", size=2.8, above=False)
    dimv(o, cy - PIN_R_FAR, cy + PIN_R_FAR, rx0 + ENV_W + 6,
         f"{PIN_R_FAR*2:.1f}", size=2.8)
    o.append(txt(rx0 + ENV_W / 2, ry0 + ENV_H + 14,
                 f"{PIN_N} pins ⌀{PIN_D} · free length {PIN_FREE_L}", 2.8, "#8FA4B2"))
    o.append(txt(rx0 + ENV_W / 2, ry0 + ENV_H + 18,
                 "field 12.4 × 17.0 — distribution indicative", 2.6, "#5A6169"))

    # ---------------- SECTION ----------------
    sx, sy = 152.0, 34.0
    o.append(txt(sx + ENV_D / 2, sy - 5, "SECTION", 3.4, "#C8C4BC", family=COND,
                 weight="700"))
    # glass barrel, front face at sx
    o.append(f'<rect x="{sx:.2f}" y="{sy:.2f}" width="{ENV_D}" height="{ENV_H}" '
             f'rx="1.2" fill="#1B2026" stroke="#5C6771" stroke-width=".6"/>')
    o.append(f'<rect x="{sx:.2f}" y="{sy:.2f}" width="2.2" height="{ENV_H}" '
             f'fill="{WARM}" opacity=".22"/>')
    o.append(txt(sx + 1.1, sy - 1.4, "▼", 2.4, WARM))
    # pins out the back
    pb = sx + ENV_D
    for i in range(7):
        yy = sy + 6 + i * ((ENV_H - 12) / 6.0)
        o.append(f'<line x1="{pb:.2f}" y1="{yy:.2f}" x2="{pb + PIN_FREE_L:.2f}" '
                 f'y2="{yy:.2f}" stroke="#9AA6B0" stroke-width=".55"/>')
    # the board the pins land in
    o.append(f'<rect x="{pb:.2f}" y="{sy - 4:.2f}" width="{BOARD_T}" '
             f'height="{ENV_H + 8}" fill="#1E5B3A" stroke="#2C7A4E" stroke-width=".4"/>')
    o.append(txt(pb + BOARD_T + 2, sy - 6, "TS06-TUBE — vertical", 2.8, "#8FBFA4",
                 anchor="start"))
    o.append(txt(pb + BOARD_T + 2, sy - 2.2, "board BEHIND the tube", 2.8, "#8FBFA4",
                 anchor="start"))
    dimh(o, sx, sx + ENV_D, sy + ENV_H + 8, f"{ENV_D} barrel", above=False)
    dimh(o, pb, pb + PIN_FREE_L, sy + ENV_H + 15, f"{PIN_FREE_L}", size=2.8,
         above=False)
    o.append(txt(sx + ENV_D / 2, sy + ENV_H + 22,
                 "the whole barrel is forward of the board", 2.8, ACC))

    # ---------------- the correction ----------------
    by = 88.0
    o.append(f'<rect x="14" y="{by:.1f}" width="{W-28:.1f}" height="22" '
             f'fill="#14100C" stroke="{ACC}" stroke-width=".5"/>')
    o.append(txt(19, by + 6, "WHAT THE Rev E.2 PLATES DREW, AND WHAT THE PART IS",
                 3.0, ACC, anchor="start", weight="600"))
    rows = [("envelope", "22 × 24 × 14", f"{ENV_W} × {ENV_H} × {ENV_D}"),
            ("leads", "socket strip under the tube", "12 pins out the REAR face"),
            ("mounts on", "a horizontal deck", "a VERTICAL board behind the row")]
    for i, (k, was, now) in enumerate(rows):
        yy = by + 11.5 + i * 3.4
        o.append(txt(19, yy, k, 2.7, "#6B737B", anchor="start"))
        o.append(txt(52, yy, was, 2.7, "#8A6A5A", anchor="start"))
        o.append(txt(132, yy, "→", 2.7, "#4A5058", anchor="start"))
        o.append(txt(140, yy, now, 2.7, "#C8C4BC", anchor="start"))

    defs = '<defs>' + T.tube_defs("r1", warm=WARM, deep=DEEP) + '</defs>'
    return ('<svg preserveAspectRatio="xMidYMid meet" viewBox="0 0 %.1f %.1f" '
            'xmlns="http://www.w3.org/2000/svg" role="img">%s\n%s</svg>'
            % (W, H, defs, "\n".join(o)))


# =============================================== SHEET 2 — the consequence
def in12_mounting():
    """The depth stack, and why the plinth cannot survive as drawn."""
    W, H = 276.0, 132.0
    o = [f'<rect x="0" y="0" width="{W}" height="{H}" fill="#0B0D10"/>']
    o.append(txt(W / 2, 11, "WHAT THIS DOES TO THE CASE", 6.0, "#E4E1DA",
                 family=COND, weight="700", ls=".6"))
    o.append(txt(W / 2, 17.5, "right section, 1:1 — Rev E.2 as drawn vs. the part as modelled",
                 3.2, "#6B737B"))

    GY = 96.0

    # ---------- LEFT: what the plates drew (wrong) ----------
    ox = 22.0
    o.append(txt(ox + 30, 24, "Rev E.2 AS DRAWN — WRONG", 3.4, "#8A6A5A",
                 family=COND, weight="700"))
    o.append(f'<polygon points="{ox:.1f},{GY:.1f} {ox+52:.1f},{GY:.1f} '
             f'{ox+52:.1f},{GY-28:.1f} {ox+6:.1f},{GY-28:.1f}" '
             f'fill="#20242A" stroke="#3C444C" stroke-width=".6"/>')
    o.append(f'<rect x="{ox+15:.1f}" y="{GY-36:.1f}" width="23" height="8" '
             f'fill="#262B31" stroke="#3C444C" stroke-width=".5"/>')
    o.append(f'<rect x="{ox+23:.1f}" y="{GY-50:.1f}" width="7" height="14" '
             f'fill="#39434B" stroke="#5C6771" stroke-width=".5"/>')
    o.append(f'<line x1="{ox+23:.1f}" y1="{GY-36:.1f}" x2="{ox+30:.1f}" '
             f'y2="{GY-36:.1f}" stroke="#C05A3A" stroke-width="1.2"/>')
    o.append(txt(ox + 34, GY - 44, "socket under the tube —", 2.7, "#C05A3A",
                 anchor="start"))
    o.append(txt(ox + 34, GY - 40.6, "this pin exit does not exist", 2.7, "#C05A3A",
                 anchor="start"))
    o.append(txt(ox + 26, GY + 6, "tube stands on a deck", 2.8, "#8A6A5A"))

    # ---------- RIGHT: the part as modelled ----------
    nx = 132.0
    o.append(txt(nx + 40, 24, "THE PART AS MODELLED", 3.4, "#8FBFA4",
                 family=COND, weight="700"))
    # base
    o.append(f'<polygon points="{nx:.1f},{GY:.1f} {nx+72:.1f},{GY:.1f} '
             f'{nx+72:.1f},{GY-22:.1f} {nx+6:.1f},{GY-22:.1f}" '
             f'fill="#20242A" stroke="#3C444C" stroke-width=".6"/>')
    # vertical tube board rising out of the base, set back
    bx = nx + 44
    o.append(f'<rect x="{bx:.1f}" y="{GY-70:.1f}" width="{BOARD_T}" height="48" '
             f'fill="#1E5B3A" stroke="#2C7A4E" stroke-width=".4"/>')
    # tube cantilevered forward off it
    tz = bx - ENV_D
    o.append(f'<rect x="{tz:.1f}" y="{GY-62:.1f}" width="{ENV_D}" height="{ENV_H}" '
             f'rx="1.2" fill="#1B2026" stroke="#5C6771" stroke-width=".6"/>')
    o.append(f'<rect x="{tz:.1f}" y="{GY-62:.1f}" width="2.2" height="{ENV_H}" '
             f'fill="{WARM}" opacity=".3"/>')
    for i in range(5):
        yy = GY - 58 + i * 5
        o.append(f'<line x1="{bx - 0.2:.1f}" y1="{yy:.1f}" x2="{bx + BOARD_T:.1f}" '
                 f'y2="{yy:.1f}" stroke="#9AA6B0" stroke-width=".5"/>')
    o.append(txt(tz - 2, GY - 62 + ENV_H / 2, "glass", 2.8, WARM, anchor="end"))
    o.append(txt(bx + 4, GY - 46, "TS06-TUBE", 2.8, "#8FBFA4", anchor="start"))
    o.append(txt(bx + 4, GY - 42.4, "vertical", 2.8, "#8FBFA4", anchor="start"))
    dimh(o, tz, bx, GY - 62.5, f"{ENV_D} barrel — all forward", size=2.8)
    o.append(txt(nx + 36, GY + 6, "tube hangs off a board behind it", 2.8, "#8FBFA4"))
    o.append(f'<line x1="{nx:.1f}" y1="{GY:.1f}" x2="{nx+80:.1f}" y2="{GY:.1f}" '
             f'stroke="#3A4149" stroke-width=".5"/>')
    o.append(f'<line x1="{ox:.1f}" y1="{GY:.1f}" x2="{ox+60:.1f}" y2="{GY:.1f}" '
             f'stroke="#3A4149" stroke-width=".5"/>')

    # ---------- the open question ----------
    qy = 106.0
    o.append(f'<rect x="14" y="{qy:.1f}" width="{W-28:.1f}" height="16" '
             f'fill="#0F1318" stroke="#3C444C" stroke-width=".5"/>')
    o.append(txt(19, qy + 5.5, "STILL OPEN — THIS IS A CASE DECISION, NOT A DRAWING FIX",
                 3.0, "#DFBB5E", anchor="start", weight="600"))
    o.append(txt(19, qy + 10.2,
                 "How the bulkhead resolves — full-width plate behind the row, a spine per pair, "
                 "or dropped below the sightline — is undecided.",
                 2.7, "#8B939C", anchor="start"))
    o.append(txt(19, qy + 13.6,
                 "Socket seat height is uncharacterised. Direct-solder is assumed here, "
                 "which puts the board hard against the glass.",
                 2.7, "#8B939C", anchor="start"))

    defs = '<defs>' + T.tube_defs("r2", warm=WARM, deep=DEEP) + '</defs>'
    return ('<svg preserveAspectRatio="xMidYMid meet" viewBox="0 0 %.1f %.1f" '
            'xmlns="http://www.w3.org/2000/svg" role="img">%s\n%s</svg>'
            % (W, H, defs, "\n".join(o)))


def main():
    for name, s in (("r-in12-reference.svg", in12_reference()),
                    ("r-in12-mounting.svg", in12_mounting())):
        with open(os.path.join(OUT, name), "w") as f:
            f.write(s)
        print(name, len(s))


if __name__ == "__main__":
    main()
