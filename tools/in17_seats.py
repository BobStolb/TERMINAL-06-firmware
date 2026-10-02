#!/usr/bin/env python3
"""ИН-17: one side view at two seats, and the numbers behind it.

    python3 tools/in17_seats.py OUT.png [--seats 8.0 5.7] [--tu 8.0 --bend 3.0 --glass-min 6.4]

The fit table FAILs the ИН-17 glass front at 1.29 mm past the window plane, at an inferred 8.0 mm seat (the glass base
8.0 mm above the board's front face, `case_pair.py` IN17_STANDOFF). The model's glass is 24.3 mm from dome to the end of its
stalk; the outline drawing says 22.0. This draws the S10 tube from the right end of the stack (an orthographic projection
along X: the front of the clock is on the LEFT, up is up) at two seats:

  * the one the case model assumes, 8.0 mm;
  * the one that brings the model's glass face level with the ИН-12 face (8.0 minus the model's overshoot: about 5.7 mm),

with the window face plane and the ИН-12 front as lines, the board in section, the ИН-12 next to it, the LED below it and
the leads. It prints, for each seat, in plain numbers: where the glass front stands, how far the solder joint on the back
of the board is from the glass (the ТУ allows no solder closer than 8 mm and no bend closer than 3 mm to the glass,
`knowledge/TERMINAL-06-measurements-IN17.txt`), the lead length needed against the 35 mm the tube comes with (15-20 mm
after the kit manual's trim), and the nearest part to the glass (bounding-box gap, so it can only understate the room).

The numbers come from the placed models (the DISP GLB, as in tools/fit_table.py) and from `tools/stack_frame.py`'s frame
(Z towards the viewer, the ИН-12 front at Z 0); the leads' Y come from the board's own pads. Needs numpy and rsvg-convert.
`python3 tools/fit_table.py ... --in17-seat 5.7` gives the same front and window rows for the fit table.
"""
import argparse, math, os, subprocess, sys, tempfile
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import fit_table as FT          # noqa: E402
import stack_frame as SF        # noqa: E402
import sexp as S                # noqa: E402

GLB = os.path.join(ROOT, "3d", "populated", "TS06-DISP-populated.glb")
PCB = os.path.join(ROOT, "PCB", "TS06-DISP", "TS06-DISP.kicad_pcb")
FREE_LEAD = 35.0            # mm, the tube's free lead length (measurements-IN17 row 7, catalogue: the factory drawing dimensions it)
TRIM = (15.0, 20.0)         # mm, what the kit manual trims the leads to before insertion (same sheet, Rev 4)


def hull(pts):
    """Convex hull of 2D points (monotone chain), as a list of (x, y)."""
    p = sorted(set((round(float(x), 4), round(float(y), 4)) for x, y in pts))
    if len(p) < 3:
        return p

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for q in p:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], q) <= 0:
            lo.pop()
        lo.append(q)
    for q in reversed(p):
        while len(up) >= 2 and cross(up[-2], up[-1], q) <= 0:
            up.pop()
        up.append(q)
    return lo[:-1] + up[:-1]


def lead_ys(top, ref="V5"):
    """Y (stack frame) of the footprint's pads, from the DISP board file."""
    t = S.parse(open(PCB, encoding="utf8").read())
    for fp in S.find_all(t, "footprint"):
        r = [S.unq(p[2]) for p in S.find_all(fp, "property") if S.unq(p[1]) == "Reference"][0]
        if r != ref:
            continue
        at = S.find(fp, "at")
        a = math.radians(float(at[3])) if len(at) > 3 else 0.0
        ys = []
        for p in S.find_all(fp, "pad"):
            pa = S.find(p, "at")
            x, y = float(pa[1]), float(pa[2])
            ys.append(top - (float(at[2]) - x * math.sin(a) + y * math.cos(a)))
        return ys
    sys.exit("no %s on %s" % (ref, PCB))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("out", help="PNG to write (at most 2400 px wide)")
    ap.add_argument("--seats", type=float, nargs=2, default=None, metavar=("UPPER", "LOWER"),
                    help="the two seats in mm (default: the case model's 8.0 and the one that makes the face level with the ИН-12)")
    ap.add_argument("--tu", type=float, default=8.0, help="no solder closer than this to the glass (ТУ), mm")
    ap.add_argument("--bend", type=float, default=3.0, help="no bend closer than this to the glass (ТУ), mm")
    ap.add_argument("--glass-min", type=float, default=6.4, help="the footprint's minimum glass-to-board distance, mm (case_pair.py IN17_STANDOFF_MIN)")
    a = ap.parse_args()

    cp, B, d, G = SF.geometry("TS06-FASCIA-rhythm", "none")
    v = G["v"]
    T, top, zb = v["PCB_T"], v["DISP_TOP_Y"], v["Z_DISP_B"]
    seat0 = v["IN17_STANDOFF"]
    disp = FT.glb_parts(GLB)

    def world(arr):      # board-frame vertices (x, u, zg) -> stack frame (X, Y, Z)
        return np.column_stack([arr[:, 0], top - arr[:, 2], arr[:, 1] - zb])

    def tube(ref):
        w = disp[ref]
        return world(w[w[:, 1] > T + 1.0])
    f17 = tube("V5")[:, 2].max()
    f12 = max(tube(r)[:, 2].max() for r in ("V1", "V2", "V3", "V4", "V9", "V10"))
    level = seat0 - (f17 - f12)
    seats = a.seats or [seat0, round(level, 2)]
    base_u = disp["V5"][disp["V5"][:, 1] > 8.5][:, 1].min()
    assert abs(base_u - (T + seat0)) < 0.05, "the model's glass base is not at the 8.0 seat: %.3f" % base_u
    window = -v["Z_FACE"]
    sill, soffit = v["SILL_TOP_Y"], v["SOFFIT_Y"]
    glass = world(disp["V5"][disp["V5"][:, 1] > base_u - 0.5])
    glass_y = (glass[:, 1].min(), glass[:, 1].max())

    # ------------------------------------------------------------------ the numbers, per seat
    others = {r: world(disp[r][disp[r][:, 1] > T]) for r in disp if r != "V5" and not r.startswith("XP") and r != "V6"}
    others["V6"] = tube("V6")

    def bbox_gap(p, q):
        lo = np.maximum(p.min(0) - q.max(0), q.min(0) - p.max(0))
        return float(np.linalg.norm(np.maximum(lo, 0.0)))

    def seat_numbers(s):
        g = glass + np.array([0.0, 0.0, s - seat0])
        gaps = sorted((bbox_gap(g, q), r) for r, q in others.items())
        by = {}
        for gp, r in gaps:
            cls = "LED" if r.startswith("HL") else "colon lamp" if r in ("V7", "V8") else "IN-12/15 glass" if r != "V6" else "IN-17 (S1)"
            by.setdefault(cls, (gp, r))
        return dict(seat=s, front=f17 + (s - seat0), proud=f17 + (s - seat0) - f12, win=window - (f17 + (s - seat0)),
                    joint=s + T, joint_m=s + T - a.tu, glass_board_m=s - a.glass_min, bend_room=s - a.bend,
                    need=s + T, tails=[L - (s + T) for L in TRIM], nearest=by, near=min(gaps))

    N = [seat_numbers(s) for s in seats]
    lowest_tu = a.tu - T
    N_tu = seat_numbers(lowest_tu)

    print("ИН-17 glass front at the model's 8.0 seat: Z %+.2f; ИН-12 front Z %+.2f; window face plane Z %+.2f; "
          "the face is level with the ИН-12 at a seat of %.2f mm" % (f17, f12, window, level))
    hdr = "%-34s" + " %10s" * 3
    print(hdr % ("seat (glass base above board face)", "%.2f mm" % seats[0], "%.2f mm" % seats[1], "%.2f mm" % lowest_tu))
    rows = [("glass front, Z", "front", "%+.2f"), ("in front of the ИН-12 front by", "proud", "%+.2f"),
            ("window plane minus glass front", "win", "%+.2f"),
            ("glass to the joint on the back, mm", "joint", "%.2f"), ("  minus the ТУ %.1f mm" % a.tu, "joint_m", "%+.2f"),
            ("glass to board minus %.1f (footprint)" % a.glass_min, "glass_board_m", "%+.2f"),
            ("room between a %.1f mm bend and the board" % a.bend, "bend_room", "%.2f")]
    for lab, k, f in rows:
        print(hdr % ((lab,) + tuple(f % n[k] for n in N + [N_tu])))
    for i, L in enumerate(TRIM):
        print(hdr % (("lead tail past the back face, trimmed to %.0f mm" % L,) + tuple("%.1f" % n["tails"][i] for n in N + [N_tu])))
    print("lead needed from glass to the back face: %s mm; the tube's free lead is %.0f mm" % (
        " / ".join("%.1f" % n["need"] for n in N + [N_tu]), FREE_LEAD))
    for n in N + [N_tu]:
        print("seat %.2f nearest parts (bbox gap, mm): %s" % (n["seat"], ", ".join("%s %s %.2f" % (cls, r, gp) for cls, (gp, r) in sorted(n["nearest"].items()))))

    # ------------------------------------------------------------------ the picture (SVG -> PNG)
    K = 36.0
    Zhi, Zlo, Yhi, Ylo = 6.0, -35.0, 70.5, 36.5
    ML, MT, PW = 110, 150, 700
    W = int(ML + (Zhi - Zlo) * K + 30 + PW)
    Hh = int(MT + (Yhi - Ylo) * K + 90)

    def X(z):
        return ML + (Zhi - z) * K

    def Y(y):
        return MT + (Yhi - y) * K
    o = []
    A = o.append
    A('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" font-family="DejaVu Sans, Arial, sans-serif">' % (W, Hh, W, Hh))
    A('<rect width="100%" height="100%" fill="#ffffff"/>')
    A('<clipPath id="pl"><rect x="%d" y="%d" width="%d" height="%d"/></clipPath>' % (ML, MT, (Zhi - Zlo) * K, (Yhi - Ylo) * K))
    A('<defs><pattern id="hatch" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="8" height="8" fill="#e4e0d4"/>'
      '<line x1="0" y1="0" x2="0" y2="8" stroke="#8a8470" stroke-width="2"/></pattern></defs>')
    A('<text x="%d" y="52" font-size="34" font-weight="bold" fill="#1d2330">ИН-17 at two seats: side view from the right end of the stack</text>' % ML)
    A('<text x="%d" y="88" font-size="22" fill="#4a5163">S10 tube, orthographic along X. The front of the clock is on the left. Millimetres; Z 0 is the ИН-12 glass front.</text>' % ML)
    A('<rect x="%d" y="%d" width="%d" height="%d" fill="#f6f8fb" stroke="#c9ceda"/>' % (ML, MT, (Zhi - Zlo) * K, (Yhi - Ylo) * K))
    A('<g clip-path="url(#pl)">')
    # board in section
    A('<rect x="%.1f" y="%d" width="%.1f" height="%d" fill="url(#hatch)" stroke="#6b665a" stroke-width="2"/>' % (X(T - zb), MT, T * K, (Yhi - Ylo) * K))
    A('<text transform="translate(%.1f %.1f) rotate(-90)" font-size="19" fill="#4d493e">TS06-DISP, 1.6</text>' % (X(-zb + 0.4) - 6, Y(37.2)))

    def poly(pts, fill, stroke, sw=2.5, dash="", op=1.0):
        pp = " ".join("%.1f,%.1f" % (X(z), Y(y)) for y, z in pts)
        A('<polygon points="%s" fill="%s" fill-opacity="%.2f" stroke="%s" stroke-width="%.1f"%s/>' % (pp, fill, op, stroke, sw, (' stroke-dasharray="%s"' % dash) if dash else ""))
    # ИН-12 neighbour (M1), for reference
    poly(hull(tube("V4")[:, [1, 2]]), "#9aa3b5", "#7b8498", 2, "9 6", 0.22)
    A('<text x="%.1f" y="%.1f" font-size="19" fill="#5d667a" text-anchor="start">ИН-12 (M1), for reference: its front is the green line</text>' % (X(-1.0), Y(44.7)))
    # LED under the tube
    led = world(disp["HL5"][disp["HL5"][:, 1] > T])
    poly(hull(led[:, [1, 2]]), "#55595f", "#2f3236", 2, "", 0.75)
    A('<text x="%.1f" y="%.1f" font-size="19" fill="#3a3d42">LED HL5 (5.3 tall)</text>' % (X(-23.4) + 0, Y(41.1)))
    # leads (the same wires at either seat)
    ys = [y for y in lead_ys(top) if glass_y[0] - 0.5 <= y <= glass_y[1] + 0.5]
    for y in ys:
        A('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#7a7f8a" stroke-width="2.5"/>' % (X(base_u - zb), Y(y), X(-0.8 - zb), Y(y)))
    A('<text x="%.1f" y="%.1f" font-size="18" fill="#59606e">leads D0.4, 35 mm free,</text>' % (X(-22.6), Y(47.9)))
    A('<text x="%.1f" y="%.1f" font-size="18" fill="#59606e">cut flush after soldering</text>' % (X(-22.6), Y(46.9)))
    # the glass at each seat
    cols = [("#1f6fd1", "#3b8bef"), ("#d9730d", "#f59a3c")]
    for (s, n), (st, fl) in zip(zip(seats, N), cols):
        g = glass + np.array([0.0, 0.0, s - seat0])
        poly(hull(g[:, [1, 2]]), fl, st, 3, "", 0.30)
        A('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="%s" stroke-width="2.5" stroke-dasharray="3 5"/>' % (X(n["front"]), MT, X(n["front"]), MT + (Yhi - Ylo) * K, st))
    # the planes
    A('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#c4262e" stroke-width="3" stroke-dasharray="14 7"/>' % (X(window), Y(soffit), X(window), Y(sill)))
    A('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="#2a8a4b" stroke-width="3" stroke-dasharray="14 7"/>' % (X(f12), MT, X(f12), MT + (Yhi - Ylo) * K))
    # the 8 mm of the ТУ, measured back from each glass base, and the joint on the back face
    yd = [Yhi - 2.1, Yhi - 4.6]
    for (s, n), (st, fl), y in zip(zip(seats, N), cols, yd):
        zb_ = s + T - zb
        zbase, zjoint = zb_ - 0.0, -zb          # Z of the glass base and of the back face, as the Z axis has them: base Z = u - zb
        zbase, zjoint = (T + s) - zb, 0.0 - zb
        A('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="3"/>' % (X(zbase), Y(y), X(zjoint), Y(y), st))
        for z in (zbase, zjoint):
            A('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="3"/>' % (X(z), Y(y) - 9, X(z), Y(y) + 9, st))
        ztu = zbase - a.tu
        A('<polygon points="%.1f,%.1f %.1f,%.1f %.1f,%.1f" fill="#c4262e"/>' % (X(ztu), Y(y) + 3, X(ztu) - 9, Y(y) + 21, X(ztu) + 9, Y(y) + 21))
        A('<text x="%.1f" y="%.1f" font-size="19" fill="%s" font-weight="bold" text-anchor="end">seat %.1f: glass to joint %.1f mm%s</text>' % (
            X(zjoint) + 4, Y(y) - 14, st, s, n["joint"], "" if n["joint_m"] >= -1e-9 else ", %.1f short of the %.0f" % (-n["joint_m"], a.tu)))
    A('</g>')
    # axes
    for z in range(-35, 7, 5):
        A('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="#8f96a6" stroke-width="1.5"/>' % (X(z), MT + (Yhi - Ylo) * K, X(z), MT + (Yhi - Ylo) * K + 8))
        A('<text x="%.1f" y="%d" font-size="19" fill="#4a5163" text-anchor="middle">%d</text>' % (X(z), MT + (Yhi - Ylo) * K + 30, z))
    A('<text x="%.1f" y="%d" font-size="20" fill="#4a5163" text-anchor="middle">Z, towards the viewer (front at left)</text>' % (X((Zhi + Zlo) / 2), MT + (Yhi - Ylo) * K + 62))
    for y in range(40, 71, 5):
        A('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#8f96a6" stroke-width="1.5"/>' % (ML - 8, Y(y), ML, Y(y)))
        A('<text x="%d" y="%.1f" font-size="19" fill="#4a5163" text-anchor="end">%d</text>' % (ML - 14, Y(y) + 6, y))
    A('<text transform="translate(34 %.1f) rotate(-90)" font-size="20" fill="#4a5163" text-anchor="middle">Y, up (mm)</text>' % (MT + (Yhi - Ylo) * K / 2))
    # labels on the lines (outside the clip)
    A('<text x="%.1f" y="%d" font-size="20" fill="#c4262e" font-weight="bold" text-anchor="end">window plane, Z %+.2f</text>' % (X(window) + 4, MT - 14, window))
    A('<text transform="translate(%.1f %.1f) rotate(-90)" font-size="18" fill="#1f6fd1">%.1f seat: glass front Z %+.2f</text>' % (X(N[0]["front"]) - 6, Y(37.2), seats[0], N[0]["front"]))
    A('<text transform="translate(%.1f %.1f) rotate(-90)" font-size="18" fill="#d9730d">%.1f seat: front Z %+.2f (level)</text>' % (X(N[1]["front"]) + 24, Y(37.0), seats[1], N[1]["front"]))
    A('<text x="%.1f" y="%d" font-size="20" fill="#2a8a4b" font-weight="bold" text-anchor="start">ИН-12 front, Z %+.2f</text>' % (X(f12) + 8, MT - 14, f12))
    # legend / numbers panel
    px = ML + (Zhi - Zlo) * K + 30
    yy = MT + 6

    def line(txt, col="#1d2330", size=22, bold=False, dy=32):
        nonlocal yy
        A('<text x="%.1f" y="%.1f" font-size="%d" fill="%s"%s>%s</text>' % (px, yy, size, col, ' font-weight="bold"' if bold else "", txt))
        yy += dy
    for (s, n), (st, fl) in zip(zip(seats, N), cols):
        A('<rect x="%.1f" y="%.1f" width="26" height="22" fill="%s" fill-opacity="0.3" stroke="%s" stroke-width="3"/>' % (px, yy - 18, fl, st))
        A('<text x="%.1f" y="%.1f" font-size="25" font-weight="bold" fill="%s">seat %.1f mm</text>' % (px + 38, yy, st, s))
        yy += 36
        line("glass front Z %+.2f: %.2f mm in front of the ИН-12" % (n["front"], n["proud"]), size=20, dy=26)
        line("%.2f mm %s the window plane" % (abs(n["win"]), "behind" if n["win"] >= 0 else "past"), "#c4262e" if n["win"] < 0 else "#1d2330", 20, dy=26)
        line("glass to the joint on the back: %.1f mm" % n["joint"], "#c4262e" if n["joint_m"] < 0 else "#1d2330", 20, dy=26)
        line("(ТУ: no solder within %.0f mm: %+.1f)" % (a.tu, n["joint_m"]), "#c4262e" if n["joint_m"] < 0 else "#1d2330", 20, dy=26)
        line("bend room (3 mm rule): %.1f mm" % n["bend_room"], size=20, dy=26)
        led_gp, led_r = n["nearest"]["LED"]
        line("nearest LED: %.1f mm away" % led_gp, size=20, dy=26)
        line("lead needed %.1f mm of %.0f free" % (n["need"], FREE_LEAD), size=20, dy=44)
    line("the ТУ limit puts the lowest seat at", size=20, dy=26)
    line("%.1f mm: glass front Z %+.2f, %.2f mm behind" % (lowest_tu, N_tu["front"], N_tu["win"]), size=20, dy=26)
    line("the window plane, %.2f in front of the ИН-12" % N_tu["proud"], size=20, dy=44)
    for col, dash, txt in (("#c4262e", "14 7", "window face plane"), ("#2a8a4b", "14 7", "ИН-12 glass front (Z 0)"), ("#c4262e", "", "red wedge: 8 mm from the glass (ТУ)")):
        if dash:
            A('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="3" stroke-dasharray="%s"/>' % (px, yy - 7, px + 40, yy - 7, col, dash))
        else:
            A('<polygon points="%.1f,%.1f %.1f,%.1f %.1f,%.1f" fill="%s"/>' % (px + 20, yy - 16, px + 10, yy + 2, px + 30, yy + 2, col))
        A('<text x="%.1f" y="%.1f" font-size="20" fill="#1d2330">%s</text>' % (px + 54, yy, txt))
        yy += 30
    A('</svg>')
    svg = os.path.join(tempfile.mkdtemp(prefix="in17_seats."), "seats.svg")
    open(svg, "w", encoding="utf8").write("\n".join(o))
    r = subprocess.run(["rsvg-convert", svg, "-o", a.out], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("rsvg-convert failed: " + r.stderr)
    os.remove(svg)
    os.rmdir(os.path.dirname(svg))
    print("wrote %s (%d x %d px design, %d kB)" % (a.out, W, Hh, os.path.getsize(a.out) // 1024))


if __name__ == "__main__":
    main()
