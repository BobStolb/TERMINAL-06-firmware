"""The drawings for power_options.py, in the style of the earlier 12 V plug review sheet.

Sections are views from above, cut through the jack's axis: the inside of the case is on the left,
the outside on the right, depth (Z) runs up the page. Plans of the rear are seen from BEHIND, so the
clock's right-hand end (the jack end) is on the LEFT, as in KiCad's view of TS06-DRV's component face.
"""
import math, os, subprocess
from PIL import Image, ImageDraw, ImageFont

FD = "/usr/share/fonts/truetype/dejavu/"
_F = {}


def font(size, bold=True):
    k = (size, bold)
    if k not in _F:
        _F[k] = ImageFont.truetype(FD + ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"), size)
    return _F[k]


BG = (225, 225, 225)
WHITE = (255, 255, 255)
INK = (25, 25, 25)
TXT = (45, 45, 45)
MUTE = (90, 90, 90)
RED = (198, 40, 40)
GREEN = (46, 125, 50)
ORANGE = (196, 118, 0)
CHEEK = (214, 219, 228)
HATCH = (150, 156, 168)
JACK = (68, 71, 79)
BORE = (200, 204, 208)
PIN = (150, 154, 158)
BOARD = (46, 125, 91)
PLUG = (214, 228, 247)
BARREL = (188, 213, 242)
BLUE = (42, 90, 168)
METAL = (176, 184, 194)
LEAD_R = (200, 50, 50)
LEAD_K = (40, 40, 40)
VIOLET = (130, 80, 223)
BAND = (244, 244, 244)
KIND = {"model": (25, 25, 25), "computed": GREEN, "seen": BLUE, "assumed": RED, "inferred": ORANGE, "board": (0, 110, 110)}


def text(d, xy, s, size=16, fill=TXT, bold=True, anchor="la"):
    d.text(xy, s, font=font(size, bold), fill=fill, anchor=anchor)


def lines(d, x, y, rows, size=16, fill=TXT, gap=6, bold=True):
    for r in rows:
        if isinstance(r, tuple):
            s, c = r
        else:
            s, c = r, fill
        text(d, (x, y), s, size, c, bold)
        y += size + gap
    return y


def hatch_poly(img, pts, fill=CHEEK, line=HATCH, outline=INK, step=11, width=1):
    """A polygon filled and hatched at 45°, outlined."""
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    x0, y0, x1, y1 = int(min(xs)) - 1, int(min(ys)) - 1, int(max(xs)) + 2, int(max(ys)) + 2
    w, h = max(1, x1 - x0), max(1, y1 - y0)
    pat = Image.new("RGB", (w, h), fill)
    pd = ImageDraw.Draw(pat)
    for k in range(-h, w + h, step):
        pd.line([(k, h), (k + h, 0)], fill=line, width=1)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).polygon([(p[0] - x0, p[1] - y0) for p in pts], fill=255)
    img.paste(pat, (x0, y0), mask)
    ImageDraw.Draw(img).polygon(pts, outline=outline, width=width)


def rect_pts(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def arrow(d, a, b, color, width=3, head=10):
    d.line([a, b], fill=color, width=width)
    for p, q in ((a, b), (b, a)):
        ang = math.atan2(q[1] - p[1], q[0] - p[0])
        tip = p
        l = (tip[0] + head * math.cos(ang + 0.45), tip[1] + head * math.sin(ang + 0.45))
        r = (tip[0] + head * math.cos(ang - 0.45), tip[1] + head * math.sin(ang - 0.45))
        d.polygon([tip, l, r], fill=color)


def dashed(d, a, b, color, width=2, dash=8, gap=6):
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    if L == 0:
        return
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    t = 0.0
    while t < L:
        e = min(L, t + dash)
        d.line([(a[0] + ux * t, a[1] + uy * t), (a[0] + ux * e, a[1] + uy * e)], fill=color, width=width)
        t = e + gap


def dashed_rect(d, x0, y0, x1, y1, color, width=2):
    for a, b in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        dashed(d, a, b, color, width)


def dashed_circle(d, cx, cy, r, color, width=2, n=48):
    for i in range(0, n, 2):
        a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        d.line([(cx + r * math.cos(a0), cy + r * math.sin(a0)), (cx + r * math.cos(a1), cy + r * math.sin(a1))],
               fill=color, width=width)


def panel(img, x, y, w, h, title, sub, status=None, color=GREEN, rows=(), band=150):
    d = ImageDraw.Draw(img)
    d.rectangle([x, y, x + w, y + h], fill=WHITE, outline=(195, 195, 195))
    text(d, (x + 16, y + 12), title, 25, INK)
    if sub:
        text(d, (x + 16, y + 48), sub, 16, MUTE)
    if status is not None:
        d.rectangle([x + 1, y + h - band, x + w - 1, y + h - 1], fill=BAND)
        d.rectangle([x + 1, y + h - band, x + 10, y + h - 1], fill=color)
        text(d, (x + 22, y + h - band + 10), status, 22, color)
        lines(d, x + 22, y + h - band + 44, rows, 15, TXT, 5)
    return d


# ============================================================================ sheet 1: the cheek
def _section(img, x, y, w, v, opt, S=18.0):
    """One cheek section in the X-Z plane at the jack's height. opt: a dict with the cut and the plug."""
    d = ImageDraw.Draw(img)
    X0, Z0 = 177.0, 39.0                     # view's lower-left in world X, Z
    ox, oy = x + 30, y + 490                 # pixel of (X0, Z0)
    P = lambda X, Z: (ox + (X - X0) * S, oy - (Z - Z0) * S)
    Ztop = 61.3
    xin, xout, T = v["X_IN_R"], v["X_OUT_R"], v["CHEEK_T"]
    jz, mouth = v["JACK_Z"], v["JACK_MOUTH_X"]
    text(d, (x + 22, y + 76), "INSIDE  (TS06-DRV board)", 14, MUTE)
    text(d, (P(xout, 0)[0] + 12, y + 76), "OUTSIDE", 14, MUTE)
    # the board and the jack (or where it was)
    bz0, bz1 = v["Z_DRV_F"], v["Z_DRV_B"]
    d.rectangle([*P(X0, bz1), *P(v["BOARD_W"], bz0)], fill=BOARD, outline=INK)
    if opt.get("jack", True):
        jx0 = mouth - v["JACK_BODY_L"]
        d.rectangle([*P(max(jx0, X0), bz1 + v["JACK_BODY_H"]), *P(mouth, bz1)], fill=JACK, outline=INK)
        d.rectangle([*P(max(mouth - 12.5, X0), jz + 3.2), *P(mouth, jz - 3.2)], fill=BORE)
        d.rectangle([*P(max(mouth - 12.5, X0), jz + 1.0), *P(mouth - 5.5, jz - 1.0)], fill=PIN)
    else:
        for n, px in (("1", 177.4), ("2", 183.4)):
            d.rectangle([*P(px - 0.5, bz1 + 0.3), *P(px + 0.5, bz0 - 0.3)], fill=(200, 160, 60))
    d.line([P(X0, jz), P(xout + 8.5, jz)], fill=(130, 130, 130), width=1)
    # the cheek, piece by piece
    for piece in opt["pieces"]:
        kind, X_a, X_b, Z_a, Z_b = piece
        pts = rect_pts(*P(X_a, min(Z_b, Ztop)), *P(X_b, max(Z_a, Z0)))
        if kind == "metal":
            hatch_poly(img, pts, METAL, (120, 128, 140), step=6)
        else:
            hatch_poly(img, pts)
    text(d, (P(xin, 0)[0] + 3, oy - 20), "cheek 6 mm", 13, INK)
    for extra in opt.get("extra", []):
        extra(img, P, S)
    # the plug
    if opt.get("plug") is not None:
        s = opt["stop"]
        tip = mouth + s
        L = v["PLUG_BARREL_L"]
        d.rectangle([*P(tip - L, jz + 2.75), *P(tip, jz - 2.75)], fill=BARREL, outline=BLUE, width=2)
        if opt["plug"] == "straight":
            d.rectangle([*P(tip, jz + 5), *P(tip + 7.5, jz - 5)], fill=PLUG, outline=BLUE, width=2)
            d.rectangle([*P(tip + 7.5, jz + 1.8), *P(min(tip + 12, 206.5), jz - 1.8)], fill=PLUG, outline=BLUE, width=2)
            text(d, P(tip + 1.0, jz + 0.9), "plug", 15, BLUE)
        else:                                  # right-angle: the elbow, the cable up the page (towards the rear)
            d.rectangle([*P(tip, jz + 6.0), *P(tip + 11, jz - 5.5)], fill=PLUG, outline=BLUE, width=2)
            d.rectangle([*P(tip + 3.75, Ztop), *P(tip + 7.25, jz + 6.0)], fill=PLUG, outline=BLUE, width=2)
            text(d, P(tip + 1.0, jz + 0.2), "plug", 15, BLUE)
        # engaged length
        e = L - s
        col = opt["color"]
        za = 58.6
        a, b = P(tip - L, za), P(mouth, za)
        d.line([P(tip - L, jz + 2.75), P(tip - L, za)], fill=col, width=1)
        d.line([P(mouth, bz1 + v["JACK_BODY_H"]), P(mouth, za)], fill=col, width=1)
        arrow(d, a, b, col, 3)
        if b[0] - a[0] > 130:
            text(d, ((a[0] + b[0]) / 2, a[1] - 8), "%.1f mm" % e, 26, col, anchor="ms")
        else:
            text(d, (b[0] + 4, a[1] - 8), "%.1f mm" % e, 26, col, anchor="rs")
    # the view from outside, top right
    ins = opt.get("inset")
    if ins:
        _inset(img, x + w - 190, y + 84, v, ins)


def _inset(img, x, y, v, ins, s=4.0):
    """The cheek seen from outside (from the right): Z runs right to left, Y up. 44 x 34 mm around the jack."""
    d = ImageDraw.Draw(img)
    W, H = 172, 136
    d.rectangle([x, y, x + W, y + H], fill=CHEEK, outline=INK)
    text(d, (x + 4, y + H + 4), "seen from outside", 12, MUTE)
    jy, jz = v["JACK_Y"], v["JACK_Z"]
    cx, cy = x + W * 0.62, y + H * 0.52
    Q = lambda Z, Y: (cx - (Z - jz) * s, cy - (Y - jy) * s)
    # the rear edge of the cheek (Z_REAR_IN) is at the left
    rx = Q(v["Z_REAR_IN"], 0)[0]
    if rx > x:
        d.rectangle([x, y, rx, y + H], fill=BG)
        d.line([(rx, y), (rx, y + H)], fill=INK, width=2)
    for k in ins:
        t = k[0]
        if t == "circle":
            _, dia, fill = k
            r = dia / 2 * s
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill, outline=INK, width=2)
        elif t == "slot":
            _, wdt = k
            r = wdt / 2 * s
            d.rectangle([rx - 2, cy - r, cx, cy + r], fill=WHITE, outline=INK, width=2)
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=WHITE, outline=INK, width=2)
            d.rectangle([rx - 2, cy - r + 2, cx, cy + r - 2], fill=WHITE)
        elif t == "rect":
            _, z0, z1, y0, y1, fill, dash = k
            a, b = Q(z1, y1), Q(z0, y0)
            if dash:
                dashed_rect(d, a[0], a[1], b[0], b[1], INK, 2)
            else:
                d.rectangle([a[0], a[1], b[0], b[1]], fill=fill, outline=INK, width=2)


def sheet_cheek(G, N, out):
    v = G["v"]
    T, xin, xout, jz = v["CHEEK_T"], v["X_IN_R"], v["X_OUT_R"], v["JACK_Z"]
    Zlo, Zhi = 30.0, 80.0
    C = {o["id"]: o for o in N["cheek"]}

    def pieces(cut, metal_from=None):
        """Material left beside a round cut (in section): above and below each segment's opening."""
        P = []
        for d0, d1, dia in cut:
            kind = "metal" if metal_from is not None and d0 >= metal_from - 1e-9 else "print"
            P.append((kind, xout - d1, xout - d0, jz + dia / 2, Zhi))
            P.append((kind, xout - d1, xout - d0, Zlo, jz - dia / 2))
        return P

    def col(e):
        return GREEN if e >= v["JACK_ENGAGE_MIN"] + 0.49 else (ORANGE if e >= v["JACK_ENGAGE_MIN"] else RED)

    OPT = []
    o = C["K0"]
    OPT.append(dict(title="1  Plain 6 mm cheek (reference)", sub="Ø9 hole only: the plug nose stops on the outer face",
                    pieces=pieces([(0, T, 9.0)]), plug="straight", stop=o["stop_from_mouth"], color=RED,
                    status="FAIL   %.1f mm engaged  (need %.1f)" % (o["engaged"], v["JACK_ENGAGE_MIN"]),
                    rows=["The earlier sheet's option 1, for comparison.", "Computed from the case model's numbers."],
                    inset=[("circle", 9.0, WHITE)]))
    o = C["A1"]
    OPT.append(dict(title="2  Clear hole Ø11, straight through", sub="The Ø10 nose passes; the barrel seats on the jack",
                    pieces=pieces([(0, T, 11.0)]), plug="straight", stop=o["stop_from_mouth"], color=GREEN,
                    status="OK   %.1f mm engaged (the whole barrel)" % o["engaged"],
                    rows=["Computed. Only if the nose is under Ø11: a Ø11.5 or", "fatter nose stops outside: %.1f mm. Nose size assumed."
                          % o["by_nose"]["11.5"], "The jack mouth shows 6.8 mm down the hole (inferred)."],
                    inset=[("circle", 11.0, WHITE)]))
    o = C["A2"]
    sl = N["slot"]
    OPT.append(dict(title="3  Slot 11 wide, open to the rear edge", sub="A right-angle plug; its lead runs back along the slot",
                    pieces=[("print", xout - T, xout, Zlo, jz - 5.5)], plug="angle", stop=o["stop_from_mouth"], color=GREEN,
                    status="OK   %.1f mm engaged (the whole barrel)" % o["engaged"],
                    rows=["Computed. The slot is %.0f long (to the rear edge)." % sl["length"],
                          "The elbow stands %.1f mm proud of the cheek (Ø11 elbow" % N["hatch"]["elbow_proud"],
                          "assumed). Only with a right-angle plug: inferred."],
                    inset=[("slot", 11.0)]))
    o = C["A3"]
    OPT.append(dict(title="4  Recessed well Ø18, 1.0 mm web", sub="Well 5 deep from outside, Ø9 hole through the web",
                    pieces=pieces([(0, T - 1.0, 18.0), (T - 1.0, T, 9.0)]), plug="straight", stop=o["stop_from_mouth"],
                    color=col(o["engaged"]), status="OK   %.1f mm engaged, any nose Ø9-18" % o["engaged"],
                    rows=["Computed. The model's Ø14 / 1.5 web gives %.1f." % C["K-model"]["engaged"],
                          "A printed 1.0 mm web takes the push of every", "plug: its strength is inferred, not tested."],
                    inset=[("circle", 18.0, (235, 238, 243)), ("circle", 9.0, WHITE)]))
    o = C["A4"]
    OPT.append(dict(title="5  Stepped counterbore", sub="Ø16 x 2 mm from outside, then Ø11 through",
                    pieces=pieces([(0, 2.0, 16.0), (2.0, T, 11.0)]), plug="straight", stop=o["stop_from_mouth"],
                    color=GREEN, status="OK   %.1f mm with a Ø10 nose" % o["engaged"],
                    rows=["Computed. A nose Ø11-16 stops on the step: %.1f (FAIL)." % o["by_nose"]["13"],
                          "Over Ø16: %.1f. The step guides the plug and reads" % o["by_nose"]["17"],
                          "as a deliberate socket (inferred)."],
                    inset=[("circle", 16.0, (235, 238, 243)), ("circle", 11.0, WHITE)]))
    o = C["B1"]
    hz = N["hatch"]

    def cap(img, P, S):
        d = ImageDraw.Draw(img)
        x_out = xout + hz["cap_proud"]
        pts = [P(xout, jz - 7.5), P(x_out, jz - 7.5), P(x_out, 61.3), P(x_out - 1.5, 61.3), P(x_out - 1.5, jz - 6.0),
               P(xout, jz - 6.0)]
        d.polygon(pts, fill=(58, 63, 69), outline=INK)
        text(d, (P(x_out, 0)[0] + 6, P(0, jz - 7.2)[1]), "cap", 14, INK)
    OPT.append(dict(title="6  Slot + hatch cap, right-angle plug", sub="The slot of 3, closed outside by a screwed cap; lead out at the back",
                    pieces=[("print", xout - T, xout, Zlo, jz - 5.5)], plug="angle", stop=o["stop_from_mouth"], color=GREEN,
                    extra=[cap], status="OK   %.1f mm engaged (the whole barrel)" % o["engaged"],
                    rows=["Computed. The cap stands %.1f mm proud (elbow Ø11" % hz["cap_proud"],
                          "assumed, 1.5 wall, 0.5 air). Unplugging = 2 screws.", "A chunky boss on the side: looks inferred."],
                    inset=[("slot", 11.0), ("rect", jz - 9, v["Z_REAR_IN"], v["JACK_Y"] - 9, v["JACK_Y"] + 9, None, True)]))
    o = C["B2"]
    OPT.append(dict(title="7  Removable metal panel, 1.5 mm", sub="Aluminium plate flush with the inner face, Ø9; window in the print",
                    pieces=[("print", xin + 1.5, xout, jz + 5.8, Zhi), ("print", xin + 1.5, xout, Zlo, jz - 5.8),
                            ("metal", xin, xin + 1.5, jz + 4.5, Zhi), ("metal", xin, xin + 1.5, Zlo, jz - 4.5)],
                    plug="straight", stop=o["stop_from_mouth"], color=col(o["engaged"]),
                    status="OK   %.1f mm engaged, any nose over Ø9" % o["engaged"],
                    rows=["Computed. A 1.0 plate: %.1f; a 2.0 plate: 6.7 (FAIL)." % C["B2-1.0"]["engaged"],
                          "Metal takes the plug's push (the printed-web doubt", "goes). Countersunk screws from inside: inferred."],
                    inset=[("rect", jz - 7, jz + 11, v["JACK_Y"] - 10, v["JACK_Y"] + 10, METAL, False), ("circle", 11.6, (235, 238, 243)),
                           ("circle", 9.0, WHITE)]))
    W, H, g = 780, 640, 10
    img = Image.new("RGB", (3 * W + 4 * g, 3 * H + 4 * g), BG)
    for i, o in enumerate(OPT):
        r, c = divmod(i, 3)
        x, y = g + c * (W + g), g + r * (H + g)
        panel(img, x, y, W, H, o["title"], o["sub"], o["status"], o["color"], o["rows"])
        _section(img, x, y, W, v, o)
    # 8: the rule
    x, y = g + 1 * (W + g), g + 2 * (H + g)
    d = panel(img, x, y, W, H, "8  The rule behind all of these", "Engaged length vs. cheek left between the nose's stop and the inner face")
    _rule(img, x, y, v, N)
    # 9: how to read
    x, y = g + 2 * (W + g), g + 2 * (H + g)
    d = panel(img, x, y, W, H, "How to read these", None)
    yy = lines(d, x + 16, y + 56, [
        "View from above, cut through the 12 V jack.", "Inside the case is left, outside is right.", ""], 18, INK, 7)
    yy = lines(d, x + 16, yy, [
        "Hatched grey = the right cheek, cut. Hatched", "steel = an aluminium plate. Dark = the jack on the",
        "board. Green strip = TS06-DRV.", ("Blue = the 12 V plug, pushed in until its nose hits", BLUE),
        ("the cheek, the plate or the jack. The arrow: how", BLUE), ("much of its barrel is inside the jack.", BLUE),
        "Top right: the cut seen from outside.", ""], 16, TXT, 6)
    yy = lines(d, x + 16, yy, ["Numbers used (mm)"], 20, INK)
    yy = lines(d, x + 16, yy + 4, [
        "cheek 6.0, jack mouth 0.8 inside the cheek face:", "from the case model (unchanged).",
        ("plug barrel 9.5, nose Ø10, need 7.0: ASSUMED", RED), ("(the model's; check them on your real plug)", RED), "",
        ("computed = worked out from those numbers.", GREEN), ("inferred = my reasoning, not modelled or tested.", ORANGE)], 16, TXT, 6)
    img.save(out, optimize=True)


def _rule(img, x, y, v, N):
    d = ImageDraw.Draw(img)
    ox, oy, sx, sy = x + 90, y + 585, 100.0, 40.0          # t 0..6.5 across, engaged 0..10 up
    P = lambda t, e: (ox + t * sx, oy - e * sy)
    tmax = N["rule"]["t_stop_max"]
    d.rectangle([*P(0, 10.4), *P(tmax, 0)], fill=(226, 242, 227))
    for t in range(0, 7):
        d.line([P(t, 0), P(t, 10.2)], fill=(225, 225, 225))
        text(d, (P(t, 0)[0], oy + 8), "%d" % t, 14, MUTE, anchor="mt")
    for e in range(0, 11, 2):
        d.line([P(0, e), P(6.4, e)], fill=(225, 225, 225))
        text(d, (ox - 10, P(0, e)[1]), "%d" % e, 14, MUTE, anchor="rm")
    d.line([P(0, 0), P(6.5, 0)], fill=INK, width=2)
    d.line([P(0, 0), P(0, 10.4)], fill=INK, width=2)
    text(d, (ox + 3.25 * sx, oy + 30), "cheek left in front of the nose's stop, mm (0 = nothing stops it)", 14, MUTE, anchor="mt")
    text(d, (ox - 60, oy - 5.2 * sy), "engaged", 14, MUTE, anchor="mm")
    gap, L = N["rule"]["gap"], v["PLUG_BARREL_L"]
    d.line([P(0.05, L - gap - 0.05), P(6.4, L - gap - 6.4)], fill=BLUE, width=3)
    d.ellipse([P(0, L)[0] - 6, P(0, L)[1] - 6, P(0, L)[0] + 6, P(0, L)[1] + 6], fill=BLUE)
    dashed(d, P(0, v["JACK_ENGAGE_MIN"]), P(6.4, v["JACK_ENGAGE_MIN"]), RED, 2)
    text(d, P(4.3, v["JACK_ENGAGE_MIN"] + 0.25), "need 7.0 (assumed)", 14, RED, anchor="lb")
    text(d, P(0.08, 0.4), "OK zone: t <= %.1f" % tmax, 14, GREEN)
    pts = [("1 plain", 6.0, 0, -24), ("model now, 7 plate 1.5", 1.5, 14, 26), ("4 well, 7 plate 1.0", 1.0, 14, -18),
           ("5 step, nose Ø11-16", 4.0, 12, -12)]
    for lab, t, dx, dy in pts:
        e = L - gap - t
        c = GREEN if e >= v["JACK_ENGAGE_MIN"] else RED
        p = P(t, e)
        d.ellipse([p[0] - 6, p[1] - 6, p[0] + 6, p[1] + 6], fill=c, outline=INK)
        text(d, (p[0] + dx, p[1] + dy), "%s: %.1f" % (lab, e), 14, c, anchor="lm" if dx else "rm")
    p = P(0, L)
    text(d, (p[0] + 14, p[1] - 12), "2, 3, 5, 6: nothing stops a Ø10 nose -> %.1f" % L, 14, BLUE, anchor="lm")
    lines(d, x + 16, y + 84, ["Engaged = barrel 9.5 - (0.8 gap + t). So t must be", "1.7 mm or less, or nothing may stop the nose at all.",
                              ("Computed from the model's numbers.", GREEN)], 15, TXT, 5)


# ============================================================================ sheet 2: moving it to the rear
def sheet_rear(G, N, BD, CON, out):
    v = G["v"]
    img = Image.new("RGB", (2380, 1480), BG)
    g = 10
    W1, H1 = 900, 1460
    d = panel(img, g, g, W1, H1, "A  The rear panel, seen from BEHIND", "The clock's right-hand end (the jack end) is on the LEFT. 1:1 at 9 px/mm")
    S = 9.0
    Xr = v["X_OUT_R"]
    ox, oy = g + 60, g + 1345
    P = lambda X, Y: (ox + (Xr - X) * S, oy - (Y - v["Y_BOT"]) * S)
    Xl = 108.0
    # the panel and the lips / cheek behind it
    d.rectangle([*P(Xr, v["Y_TOP"]), *P(Xl, v["Y_BOT"])], fill=(238, 240, 243), outline=INK, width=2)
    lip = G["rear_lips"]
    for name, (y0, y1, z0, z1) in lip.items():
        dashed_rect(d, *P(v["X_IN_R"], y1), *P(Xl, y0), MUTE, 1)
    text(d, P(150, lip["top plate"][1] - 1.0), "top plate's lip behind (Y > %.1f)" % lip["top plate"][0], 13, MUTE)
    hatch_poly(img, rect_pts(*P(Xr, v["Y_TOP"]), *P(v["X_IN_R"], v["Y_BOT"])))
    text(d, (P(Xr, 0)[0] + 2, P(0, 20)[1]), "right", 13, INK)
    text(d, (P(Xr, 0)[0] + 2, P(0, 16)[1]), "cheek", 13, INK)
    # the board's outline and the parts behind, shaded by height
    d.rectangle([*P(v["BOARD_W"], v["DRV_TOP_Y"]), *P(Xl, v["DRV_BOT_Y"])], outline=BOARD, width=2)
    for ref, fp, box, h, side, src in G["drv_parts"]:
        if side != 0 or box[1] < Xl:
            continue
        x0, x1, y0, y1 = box
        k = min(1.0, h / 20.0)
        fill = (int(235 - 120 * k), int(238 - 120 * k), int(242 - 110 * k))
        if ref == "XS1":
            dashed_rect(d, *P(x1, y1), *P(x0, y0), JACK, 2)
            text(d, P(x1 - 0.5, y1 - 0.6), "XS1 not fitted", 12, JACK)
            continue
        d.rectangle([*P(min(x1, Xr), y1), *P(max(x0, Xl), y0)], fill=fill, outline=(120, 120, 120))
        if x1 - x0 > 5 and y1 - y0 > 3:
            c = P((max(x0, Xl) + x1) / 2, (y0 + y1) / 2)
            text(d, c, "%s %g" % (ref, h), 11, INK if k < 0.6 else WHITE, anchor="mm")
    # the rear screws
    for sx, sy in G["rear_screws"]:
        if sx > Xl:
            c = P(sx, sy)
            r = v["SCREW_HEAD_D"] / 2 * S
            d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=(60, 60, 60))
    # the module screw H7 and the P-clip on it
    h7 = N["h7"]
    c = P(h7[1], h7[2])
    r = v["SCREW_HEAD_D"] / 2 * S
    d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], outline=INK, width=2)
    text(d, (c[0] + 30, c[1] - 26), "H7: P-clip under the screw", 12, VIOLET)
    # XS1's pads, where the lead lands
    for n, px, py, net in N["xs1_pads_world"]:
        c = P(px, py)
        d.rectangle([c[0] - 0.5 * S, c[1] - 1.5 * S, c[0] + 0.5 * S, c[1] + 1.5 * S] if n != "3" else
                    [c[0] - 1.5 * S, c[1] - 0.5 * S, c[0] + 1.5 * S, c[1] + 0.5 * S], fill=(200, 160, 60), outline=INK)
        text(d, (c[0], c[1] + 18), "%s %s" % (n, net), 11, INK, anchor="mt")
    # the connectors
    R = {(r["key"], tuple(r["at"])): r for r in N["rear"]}
    hi = R[("2RM14", (182.5, v["JACK_Y"]))]
    mid = R[("SHR20", (178.0, 49.5))]
    for r, key, col in ((hi, "2RM14", GREEN), (mid, "SHR20", ORANGE)):
        c = CON[key]
        cx, cy = r["at"]
        f = c["flange"] / 2
        d.rectangle([*P(cx + f, cy + f), *P(cx - f, cy - f)], outline=col, width=3)
        hh = c["holes"] / 2
        for dx in (-hh, hh):
            for dy in (-hh, hh):
                q = P(cx + dx, cy + dy)
                rr = c["hole_d"] / 2 * S
                d.ellipse([q[0] - rr, q[1] - rr, q[0] + rr, q[1] + rr], outline=col, width=2)
        q = P(cx, cy)
        dashed_circle(d, q[0], q[1], c["body_d"] / 2 * S, col, 2)
        text(d, (q[0], P(0, cy - f)[1] + 6), c["title"].split(" (")[0], 15, col, anchor="mt")
    # the lead
    q = P(*hi["at"])
    for n, px, py, net in N["xs1_pads_world"][:2]:
        dashed(d, (q[0] + (-12 if n == "1" else 12), q[1]), P(px, py), LEAD_R if n == "1" else LEAD_K, 3, 6, 4)
    lines(d, g + 16, g + 80, [
        ("Green: 2РМ14 at X %.1f, Y %.1f, over XS1's place (a DIN socket or a panel DC jack fits here too)." % tuple(hi["at"]), GREEN),
        ("Orange: ШР20 at X %.1f, Y %.1f, the empty patch (its Ø20 body does not fit higher up)." % tuple(mid["at"]), ORANGE),
        "Square = the flange, outside the panel. Dashed circle = the body behind the panel, inside the case.",
        "Shaded boxes: parts on TS06-DRV's back face, darker = taller (height in mm, from the model).",
        ("Dashed red/black: the two-wire lead to XS1's pads. Black discs: the rear panel's screws.", LEAD_R)], 14, TXT, 5)
    # --- B: the depth budget, a section through the 2РМ14
    x2 = g + W1 + g
    W2 = 2380 - x2 - g
    d = panel(img, x2, g, W2, 740, "B  Depth behind the rear panel", "Section at X %.1f, looking from the right. 1:1 at 12 px/mm" % hi["at"][0])
    S2 = 12.0
    Z0, Y0 = 40.0, 70.0
    ox2, oy2 = x2 + 40, g + 690
    Q = lambda Z, Y: (ox2 + (Z - Z0) * S2, oy2 - (Y - Y0) * S2)
    c = CON["2RM14"]
    cy = hi["at"][1]
    d.rectangle([*Q(v["Z_DRV_F"], 109), *Q(v["Z_DRV_B"], v["Y_BOT"] if v["Y_BOT"] > Y0 else Y0)], fill=BOARD)
    text(d, Q(v["Z_DRV_B"] + 0.4, 108), "TS06-DRV", 13, BOARD, anchor="lt")
    hatch_poly(img, rect_pts(*Q(v["Z_REAR_IN"], 112.5), *Q(v["Z_REAR_OUT"], Y0)), (225, 225, 210), (160, 160, 140), 7)
    text(d, (Q(v["Z_REAR_OUT"], 0)[0] + 4, Q(0, 72)[1]), "rear panel 1.6 FR4", 13, INK)
    lp = lip["top plate"]
    hatch_poly(img, rect_pts(*Q(lp[2], lp[1]), *Q(lp[3], lp[0])))
    text(d, Q(lp[2] - 0.4, lp[1]), "top plate lip", 12, INK, anchor="rt")
    # the connector: flange, front, body behind, the mated cable part
    zf = v["Z_REAR_OUT"]
    d.rectangle([*Q(zf, cy + c["flange"] / 2), *Q(zf + 1.5, cy - c["flange"] / 2)], fill=METAL, outline=INK)
    d.rectangle([*Q(zf + 1.5, cy + 7), *Q(zf + 1.5 + c["front"], cy - 7)], fill=METAL, outline=INK)
    d.rectangle([*Q(zf + 1.5 + c["front"] - 3, cy + 10), *Q(zf + 1.5 + c["front"] + 14, cy - 10)], fill=(200, 205, 212), outline=INK)
    d.rectangle([*Q(zf + 1.5 + c["front"] + 14, cy + 5), *Q(zf + 1.5 + c["front"] + 24, cy - 5)], fill=(200, 205, 212), outline=INK)
    text(d, Q(zf + 1.5 + c["front"] - 3, cy - 11.0), "cable part (inferred shape)", 12, MUTE, anchor="lt")
    zb = v["Z_REAR_IN"] - c["rear"]
    d.rectangle([*Q(zb, cy + c["body_d"] / 2), *Q(v["Z_REAR_IN"], cy - c["body_d"] / 2)], fill=METAL, outline=ORANGE, width=2)
    text(d, Q(zb + 0.5, cy + 0.5), "body %g (inferred)" % c["rear"], 12, INK)
    # the lead down to the pads
    for dy, colr in ((-1.5, LEAD_R), (1.5, LEAD_K)):
        d.line([Q(zb, cy + dy), Q(zb - 3.5, cy + dy), Q(v["Z_DRV_B"] + 0.3, v["JACK_Y"] + dy * 0.1)], fill=colr, width=3)
    # dims
    arrow(d, Q(v["Z_DRV_B"], 101.0), Q(v["Z_REAR_IN"], 101.0), INK, 2, 8)
    text(d, Q((v["Z_DRV_B"] + v["Z_REAR_IN"]) / 2 - 2, 101.6), "%.1f room (model)" % N["rear_room_z"], 15, INK, anchor="ms")
    arrow(d, Q(zb - 5, 80.0), Q(v["Z_REAR_IN"], 80.0), ORANGE, 2, 8)
    text(d, Q((zb - 5 + v["Z_REAR_IN"]) / 2, 78.6), "%.0f needed: body + 5 bend (inferred)" % hi["need"], 14, ORANGE, anchor="mt")
    lines(d, x2 + 890, g + 84, [
        ("Place 1 with a 2РМ14: what changes", INK),
        "Case: the rear panel gets a Ø16 hole and four Ø3.2 holes",
        "(sizes inferred); the right cheek loses its jack hole (plain).",
        "The panel's label \"12 V DC centre +\" becomes the pin-out.",
        ("Board: nothing. XS1 is left off; the lead goes into its pads.", GREEN),
        "Assembly: solder the lead to pads 1 and 2, slide the module",
        "in, solder the lead to the connector's cups, screw the panel on.",
        "Service: take the 6 rear screws out and lay the panel beside",
        "the case on its lead. The module comes out with it attached.",
        ("Adapter: fit a 2РМ14КПН4Г1В1 on a 12 V brick's lead, or make", ORANGE),
        ("a short 2РМ14-to-5.5x2.1 jack tail (inferred).", ORANGE),
        ("Everything in this list is inferred unless it carries a number.", ORANGE)], 14, TXT, 6)
    lines(d, x2 + 16, g + 84, [("Margin %.1f mm over the H7 screw head (%.1f, model)." % (hi["margin"], hi["h_under"]), GREEN),
                                "The lead: %.0f mm at least; cut %.0f so the panel" % (hi["lead_min"], hi["lead_cut"]),
                                "can lie beside the case while it is open (inferred)."], 15, TXT, 5)
    # --- C: the table of places
    y3 = g + 740 + g
    d = panel(img, x2, y3, 2380 - x2 - g, 1460 - 740 - g, "C  Every place tried, computed from the model", None)
    rows = []
    lab = {"2RM14": "2РМ14", "SHR20": "ШР20", "DIN5": "DIN socket", "DCJ": "panel DC jack"}
    for r in N["rear"]:
        ok = r["ok"]
        why = "OK" if ok else "NO: " + (r["issues"][0] if r["issues"] else "too deep over %s" % r["tallest"])
        rows.append((lab[r["key"]], "rear, X %.1f Y %.1f:  room %.1f, need %.1f, margin %.1f,  lead >= %.0f mm.  %s" %
                     (r["at"][0], r["at"][1], r["room"], r["need"], r["margin"], r["lead_min"], why),
                     GREEN if ok and r["margin"] >= 1 else (ORANGE if ok else RED)))
    cj = N["cheek_jack"]
    rows.append(("long-bush DC jack", "right cheek, axis Y %.1f Z %.1f: %.1f over the board, %.1f to the rear panel, no part in the way"
                 % (cj["axis_y"], cj["axis_z"], cj["above_board"], cj["below_rear"]), GREEN))
    rows.append(("any socket", "left cheek: the lead crosses the whole board, about %.0f mm; the USB slot is there too"
                 % N["left_cheek_lead"], ORANGE))
    rows.append(("any socket", "bottom: the clock stands on its base; a plug under it needs feet taller than plug + bend", RED))
    yy = y3 + 62
    for a, b, c in rows:
        text(d, (x2 + 16, yy), a, 15, c)
        text(d, (x2 + 200, yy), b, 15, c)
        yy += 30
    # where the places are: the whole case from behind, small
    s3 = 2.2
    mx, my = x2 + 620, y3 + 702
    M = lambda X, Y: (mx + (v["X_OUT_R"] - X) * s3, my - (Y - v["Y_BOT"]) * s3)
    d.rectangle([*M(v["X_OUT_R"], v["Y_TOP"]), *M(v["X_OUT_L"], v["Y_BOT"])], fill=(238, 240, 243), outline=INK, width=2)
    for xa, xb in ((v["X_OUT_R"], v["X_IN_R"]), (v["X_IN_L"], v["X_OUT_L"])):
        d.rectangle([*M(xa, v["Y_TOP"]), *M(xb, v["Y_BOT"])], fill=CHEEK, outline=INK)
    marks = [("1", hi["at"][0], hi["at"][1], GREEN), ("2", mid["at"][0], mid["at"][1], ORANGE),
             ("3", v["X_OUT_R"] - 3, cj["axis_y"], GREEN), ("4", v["X_OUT_L"] + 3, 60.0, ORANGE), ("5", 96.0, v["Y_BOT"], RED)]
    for n, X, Y, c in marks:
        q = M(X, Y)
        d.ellipse([q[0] - 12, q[1] - 12, q[0] + 12, q[1] + 12], fill=c, outline=INK)
        text(d, q, n, 14, WHITE, anchor="mm")
    text(d, (M(v["X_OUT_R"], 0)[0] - 250, M(0, v["Y_TOP"])[1]), "Where each place is:", 15, INK)
    text(d, (M(v["X_OUT_R"], 0)[0] - 250, M(0, v["Y_TOP"])[1] + 22), "the whole case, from behind", 14, MUTE)
    lines(d, M(v["X_OUT_L"], 0)[0] + 24, M(0, v["Y_TOP"])[1], [("1 rear, over XS1", GREEN), ("2 rear, lower", ORANGE),
          ("3 right cheek, raised", GREEN), ("4 left cheek", ORANGE), ("5 bottom", RED)], 14, TXT, 6)
    lines(d, x2 + 16, yy + 14, [
        "Room = rear panel's inner face (Z %.1f) - TS06-DRV's back face (Z %.1f) - the tallest part under the body." % (v["Z_REAR_IN"], v["Z_DRV_B"]),
        "Need = the connector's body behind the panel (inferred: no length seen) + 5 mm for the solder cups and the bend.",
        "Lead >= the shortest run from the solder cups to XS1's pads 1 and 2. XS1 is left off: its pads take the lead.",
        ("Not changed: the board. Pads 1 (VIN_J) and 2 (GND) are 1.0 x 3.0 slots (board file): AWG20-22 goes in.", BOARD)],
        14, TXT, 6)
    img.save(out, optimize=True)


# ============================================================================ sheet 3: the connectors
def sheet_connectors(G, N, CON, out):
    img = Image.new("RGB", (2380, 1130), BG)
    g, W, H = 10, 582, 1110
    keys = ["2RM14", "SHR20", "DIN5", "DCJ"]
    S = 7.0
    for i, k in enumerate(keys):
        c = CON[k]
        x, y = g + i * (W + g), g
        d = panel(img, x, y, W, H, c["title"], c["panel_part"])
        text(d, (x + 16, y + 70), "mates: " + c["cable_part"], 13, MUTE)
        # front view (the flange), centred
        cx, cy = x + 140, y + 300
        if c.get("flange"):
            fw = c["flange"] * S / 2
            fh = (c.get("flange_h") or c["flange"]) * S / 2
            d.rectangle([cx - fw, cy - fh, cx + fw, cy + fh], fill=METAL, outline=INK, width=2)
            hh = c["holes"] * S / 2
            pos = [(-hh, -hh), (hh, -hh), (-hh, hh), (hh, hh)] if k != "DIN5" else [(-hh, 0), (hh, 0)]
            for dx, dy in pos:
                r = c["hole_d"] * S / 2
                d.ellipse([cx + dx - r, cy + dy - r, cx + dx + r, cy + dy + r], fill=WHITE, outline=INK)
        r = (c["cut_d"] if k == "DCJ" else c["body_d"] - 2) * S / 2
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(95, 100, 108), outline=INK, width=2)
        r2 = r * 0.72
        d.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], fill=(40, 40, 44))
        npin = {"2RM14": 4, "SHR20": 4, "DIN5": 5, "DCJ": 1}[k]
        for j in range(npin):
            if k == "DIN5":
                a = math.radians(180 + j * 45)
            elif k == "DCJ":
                a = None
            else:
                a = math.radians(45 + j * 90)
            pr = {"2RM14": 1.0, "SHR20": 2.5, "DIN5": 1.4, "DCJ": 2.0}[k] * S / 2
            px, py = (cx, cy) if a is None else (cx + r2 * 0.55 * math.cos(a), cy + r2 * 0.55 * math.sin(a))
            d.ellipse([px - pr, py - pr, px + pr, py + pr], fill=(215, 190, 120), outline=INK)
        text(d, (cx, y + 96), "front", 13, MUTE, anchor="mt")
        # dimensions on the front view
        if c.get("flange"):
            fw = c["flange"] * S / 2
            fh = (c.get("flange_h") or c["flange"]) * S / 2
            arrow(d, (cx - fw, cy + fh + 22), (cx + fw, cy + fh + 22), KIND["seen"], 2, 8)
            text(d, (cx, cy + fh + 18), "%g" % c["flange"], 15, KIND["seen"], anchor="ms")
            hh = c["holes"] * S / 2
            arrow(d, (cx - hh, cy - fh - 18), (cx + hh, cy - fh - 18), KIND["seen"] if k != "DIN5" else KIND["inferred"], 2, 8)
            text(d, (cx, cy - fh - 22), "%g" % c["holes"], 15, KIND["seen"] if k != "DIN5" else KIND["inferred"], anchor="ms")
        else:
            rr = c["cut_d"] * S / 2
            arrow(d, (cx - rr, cy + rr + 22), (cx + rr, cy + rr + 22), KIND["seen"], 2, 8)
            text(d, (cx, cy + rr + 18), "hole %g" % c["cut_d"], 15, KIND["seen"], anchor="ms")
        # side view, to the right: panel line, front ahead, body behind
        panel_x = x + 400
        d.line([(panel_x, cy - 150), (panel_x, cy + 150)], fill=INK, width=3)
        text(d, (panel_x, cy + 156), "panel", 12, MUTE, anchor="mt")
        fh = (c.get("flange_h") or c.get("flange") or c["cut_d"] + 3) * S / 2
        d.rectangle([panel_x - 12, cy - fh, panel_x - 1, cy + fh], fill=METAL, outline=INK)
        ff = c["front"] * S
        d.rectangle([panel_x - 12 - ff, cy - (c["body_d"] - 2) * S / 2, panel_x - 12, cy + (c["body_d"] - 2) * S / 2],
                    fill=METAL, outline=INK)
        rb = c["rear"] * S
        d.rectangle([panel_x + 2, cy - c["body_d"] * S / 2, panel_x + 2 + rb, cy + c["body_d"] * S / 2], fill=(225, 228, 233),
                    outline=KIND["inferred"], width=2)
        text(d, (panel_x + 2 + rb / 2, cy + c["body_d"] * S / 2 + 6), "%g behind" % c["rear"], 12, KIND["inferred"], anchor="mt")
        text(d, (panel_x - 12 - ff / 2, cy - c["body_d"] * S / 2 - 6), "%g ahead" % c["front"], 12, KIND["inferred"], anchor="mb")
        text(d, (panel_x, y + 96), "side (outside left)", 13, MUTE, anchor="mt")
        # the facts
        amps = "%g A a contact" % c["amps"] + (", %g A in all" % c["amps_total"] if c.get("amps_total") else "")
        rows = [("Rating: %s, %s, %s V" % (c["contacts"], amps, c["volts"]), KIND["seen"]),
                ("Clock needs about 0.4 A (PCB/TS06-pair-testing.md)", INK), ""]
        rows += [("Seen (search excerpts):", KIND["seen"])]
        for s in c["seen"]:
            rows += _wrap("- " + s, 56, KIND["seen"])
        rows += ["", ("Inferred:", KIND["inferred"])]
        for s in c["inferred"]:
            rows += _wrap("- " + s, 56, KIND["inferred"])
        rows += [""] + [(s, INK) for s in _facts(k)]
        yy = lines(d, x + 16, y + 490, [r if isinstance(r, tuple) else (r, TXT) for r in rows], 14, TXT, 5)
    img.save(out, optimize=True)


def _wrap(s, n, c):
    out, cur = [], ""
    for w in s.split(" "):
        if len(cur) + len(w) + 1 > n:
            out.append((cur, c))
            cur = "  " + w
        else:
            cur = (cur + " " + w).strip() if not cur.startswith("  ") else cur + " " + w
    out.append((cur, c))
    return out


def _facts(k):
    F = {
        "2RM14": ["Mount: rear panel (1.6 FR4 suits a flange), or a", "metal plate in the cheek. Polarity: keyed shell,",
                  "use 2 pins for + and 2 for -. Strain relief: the", "cable part's nozzle nut grips the lead. Pins on",
                  "the clock, sockets on the live lead: touch-safe.", "Looks: the grey Soviet instrument socket.",
                  "Cost: low, still made (inferred)."],
        "SHR20": ["Mount: rear panel, low at the jack end (its 30", "mm flange misses XS1's place). Keyed, threaded",
                  "coupling nut. Heavy cable part (37 g) hangs off", "the back. 25 A contacts: far more than needed.",
                  "Looks: the chunkiest, military. Cost: medium", "(inferred)."],
        "DIN5": ["Mount: rear panel. Keyed, push-fit, no lock.", "Risk: the same socket as Soviet audio (a tape",
                 "lead fits it and would get 12 V): inferred.", "2 A is 5x the clock's draw. Strain relief: the",
                 "plug's own clamp. Looks: 1980s hi-fi. Cost: low."],
        "DCJ": ["Mount: rear panel, or through the 6 mm cheek", "with a long bush. Keeps the adapter you have.",
                "Polarity: centre + as now; the board's VD2 and", "VD4 still guard a reversed plug. Strain relief:",
                "none but the plug's own. Looks: plain. Cost:", "the lowest (inferred)."],
    }
    return F[k]


# ============================================================================ sheet 4: the board's corner
def sheet_board(G, N, BD, out):
    v = G["v"]
    img = Image.new("RGB", (2380, 1060), BG)
    g = 10
    W1, H1 = 1180, 1040
    d = panel(img, g, g, W1, H1, "D  TS06-DRV's jack corner, from the board file",
              "Component face, seen from behind (KiCad's view): the board's right edge is on the LEFT. 20 px/mm")
    S = 20.0
    xm, ym = 54.0, 42.4
    lines(d, g + 16, g + 78, [("Red tracks: VIN_J. Copper-red = F.Cu, blue = B.Cu. Grey boxes: courtyards. Dashed: XS1, left off.", TXT),
                              ("Red/black: the new lead into pads 1 and 2. Violet: a P-clip under H7's screw (strain relief, inferred).", VIOLET),
                              ("Green dashed: free for a 2-pin XH header in a rev C, with XS1 kept (computed from the file).", GREEN)], 14, TXT, 5)
    main, d0 = img, d
    img = Image.new("RGB", (int((xm + 1.5) * S) + 2, int((ym + 1.5) * S) + 2), WHITE)
    d = ImageDraw.Draw(img)
    ox, oy = 0, 0
    P = lambda x, y: (ox + (x + 1.5) * S, oy + (y + 1.5) * S)
    d.rectangle([*P(0, 0), *P(xm + 2, ym + 2)], fill=(232, 240, 234), outline=BOARD, width=3)
    for t in BD["tracks"]:
        a, b = t["a"], t["b"]
        if max(a[0], b[0]) < 0 or min(a[0], b[0]) > xm or max(a[1], b[1]) < 0 or min(a[1], b[1]) > ym:
            continue
        col = (205, 120, 110) if t["layer"] == "F.Cu" else (110, 140, 205)
        if t["net"] in ("VIN_J",):
            col = LEAD_R
        d.line([P(max(-0.5, min(a[0], xm)), max(-0.5, min(a[1], ym))) if False else P(*a), P(*b)], fill=col,
               width=max(1, int(t["w"] * S)))
    for ref, f in BD["fps"].items():
        x0, x1, y0, y1 = f["crt"]
        if x0 > xm or y0 > ym:
            continue
        if ref == "XS1":
            dashed_rect(d, *P(x0, y0), *P(x1, y1), JACK, 3)
            text(d, P(x0 + 0.3, y0 + 0.2), "XS1 (leave off)", 15, JACK)
        else:
            d.rectangle([*P(x0, y0), *P(min(x1, xm), min(y1, ym))], outline=(100, 100, 100), width=1)
            text(d, P(x0 + 0.2, y0 + 0.1), ref, 13, MUTE)
    for p in BD["pads"]:
        if p["x"] > xm or p["y"] > ym:
            continue
        c = P(p["x"], p["y"])
        w, h = p["w"] * S / 2, p["h"] * S / 2
        d.rectangle([c[0] - w, c[1] - h, c[0] + w, c[1] + h], fill=(212, 175, 80), outline=(120, 90, 20))
        if p["drill"] and p["drill"][0] == "oval":
            dw, dh = float(p["drill"][1]) * S / 2, float(p["drill"][2]) * S / 2
            d.rounded_rectangle([c[0] - dw, c[1] - dh, c[0] + dw, c[1] + dh], radius=min(dw, dh), fill=WHITE)
        elif p["drill"]:
            r = float(p["drill"][0]) * S / 2
            d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=WHITE)
    # labels on XS1's pads
    for p in BD["pads"]:
        if p["ref"] == "XS1":
            c = P(p["x"], p["y"])
            text(d, (c[0], c[1] + 42), "%s  %s" % (p["n"], p["net"]), 16, LEAD_R if p["net"] == "VIN_J" else INK, anchor="mt")
            if p["n"] != "3":
                text(d, (c[0], c[1] + 62), "slot %sx%s" % (p["drill"][1], p["drill"][2]), 13, MUTE, anchor="mt")
    # the free spot for a 2-pin header (rev C), with XS1 kept
    xh = N["free"]["JST XH 2-pin (B2B-XH-A, 2.5)"]
    xs = [q[0] for q in xh["with_xs1_first"][:5]]
    if xs:
        x0, y0 = min(xs), xh["with_xs1_first"][0][1]
        dashed_rect(d, *P(x0, y0), *P(x0 + 7.4, y0 + 6.3), GREEN, 3)
    # the lead and its clip
    for n, col in (("1", LEAD_R), ("2", LEAD_K)):
        p = [q for q in BD["pads"] if q["ref"] == "XS1" and q["n"] == n][0]
        c = P(p["x"], p["y"])
        d.line([c, (c[0] + (40 if n == "1" else -10), c[1] - 90), (P(3.5, 3.5)[0] + 40, P(3.5, 3.5)[1] + 10)], fill=col, width=5)
    h7 = P(3.5, 3.5)
    d.arc([h7[0] - 30, h7[1] - 30, h7[0] + 70, h7[1] + 40], 200, 520, fill=VIOLET, width=4)
    main.paste(img, (g + 40, g + 150))
    img, d = main, d0
    # right: the facts
    x2 = g + W1 + g
    d = panel(img, x2, g, 2380 - x2 - g, H1, "How the board takes the lead", "Read from PCB/TS06-DRV/TS06-DRV.kicad_pcb (board) unless marked")
    pads = {p["n"]: p for p in BD["pads"] if p["ref"] == "XS1"}
    rows = [
        ("No board change: leave XS1 off and solder the lead into its pads.", GREEN), "",
        ("Pad 1 = VIN_J (to F1, the PTC), pad 2 = GND, pad 3 = GND (the jack's", (0, 110, 110)),
        ("switch contact). Pads 1 and 2 are %s mm slots, 6.0 mm apart." % "x".join(pads["1"]["drill"][1:]), (0, 110, 110)),
        ("Pad sizes %sx%s and %sx%s mm." % (pads["1"]["w"], pads["1"]["h"], pads["2"]["w"], pads["2"]["h"]), (0, 110, 110)), "",
        ("A 1.0 mm slot takes a tinned AWG20 (0.5 mm²) or AWG22 wire; the", ORANGE),
        ("clock draws about 0.4 A (PCB/TS06-pair-testing.md), so either is", ORANGE),
        ("ample. The 2РМ14's cable part takes up to 0.5 mm² (seen).", ORANGE), "",
        ("The lead joins before F1: a short in the lead itself is limited only", ORANGE),
        ("by the adapter. VD2 (series Schottky) and VD4 (TVS -> trips F1) still", ORANGE),
        ("guard the board against a reversed lead (netlist, tools/ts06pair.py).", ORANGE), "",
        ("A 2-pin header instead needs a board change (rev C):", RED),
        ("- in XS1's place: VH (3.96, 10 A) fits %d ways, XH (2.5) %d ways." % (
            N["free"]["JST VH 2-pin (B2P-VH, 3.96)"]["in_xs1_place"], N["free"]["JST XH 2-pin (B2B-XH-A, 2.5)"]["in_xs1_place"]), RED),
        ("- beside XS1 (both fitted): a VH fits nowhere in the right 40 mm;", RED),
        ("  an XH fits above XS1 and in a strip at world X 173-180, Y 25-56.", RED),
        ("Header courtyards (VH 8.8 x 9.8, XH 7.4 x 6.3) are inferred.", ORANGE),
        ("Checked on a 0.5 mm grid: courtyards, pads, tracks (0.5 clear).", GREEN), "",
        ("No 2.54/5.08 header fits pads 1-2 as they are: they are 6.0 apart.", GREEN),
    ]
    lines(d, x2 + 16, g + 90, [r if isinstance(r, tuple) else (r, TXT) for r in rows], 16, TXT, 7)
    img.save(out, optimize=True)


# ============================================================================ all
def draw_all(G, N, BD, CON, here):
    sheet_cheek(G, N, os.path.join(here, "cheek-cutouts-section.png"))
    sheet_rear(G, N, BD, CON, os.path.join(here, "move-port-rear.png"))
    sheet_connectors(G, N, CON, os.path.join(here, "soviet-connectors.png"))
    sheet_board(G, N, BD, os.path.join(here, "drv-jack-corner.png"))
    for f in ("cheek-cutouts-section.png", "move-port-rear.png", "soviet-connectors.png", "drv-jack-corner.png"):
        p = os.path.join(here, f)
        im = Image.open(p)
        print("  %-28s %dx%d  %.0f kB" % (f, im.size[0], im.size[1], os.path.getsize(p) / 1024))


VIEWS = {   # name: (OPTION, --camera=tx,ty,tz,rx,ry,rz,dist)
    "render-2rm14-rear": ("rear2rm", "130,60,60,66,0,150,430"),
    "render-2rm14-inside": ("rear2rm_cut", "183,57,92,25,0,160,175"),
    "render-cheek-jack": ("cheekjack", "175,40,70,68,0,62,380"),
}


def render(here):
    scad = os.path.join(here, "power_options.scad")
    for name, (opt, cam) in VIEWS.items():
        out = os.path.join(here, name + ".png")
        r = subprocess.run(["nice", "-n", "15", "xvfb-run", "-a", "-s", "-screen 0 1600x1200x24", "openscad", "-o", out,
                            "--imgsize=1600,1100", "--camera=" + cam, "--projection=p", "--colorscheme=Tomorrow",
                            "-D", 'OPTION="%s"' % opt, scad], cwd=here, capture_output=True, text=True)
        print("  %-26s %s" % (name + ".png", "ok" if r.returncode == 0 else "FAILED\n" + r.stderr[-1500:]))
