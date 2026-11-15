#!/usr/bin/env python3
"""Tools for draw_yarn.py: paths, a stroke alphabet, rasters for the checks, SVG and the PNG step.

Nothing here knows the design. Units are mm in a board's own frame (x right, y down). Angles are
degrees, 0 = +x, 90 = down (y grows downward), as in the routing plan's tables.
"""
import math, os, shutil, subprocess
import numpy as np

# ------------------------------------------------------------------------------------ paths


def P(c, r, deg):
    a = math.radians(deg)
    return (c[0] + r * math.cos(a), c[1] + r * math.sin(a))


def arc(c, r, a0, a1, step=0.12):
    n = max(2, int(abs(math.radians(a1 - a0)) * r / step) + 1)
    return [P(c, r, a0 + (a1 - a0) * k / n) for k in range(n + 1)]


def length(pts):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


def rounded(pts, r, step=0.12):
    """The polyline through pts with every corner rounded to radius r (less where a leg is short)."""
    out = [pts[0]]
    for a, b, c in zip(pts, pts[1:], pts[2:]):
        v1 = (a[0] - b[0], a[1] - b[1])
        v2 = (c[0] - b[0], c[1] - b[1])
        l1, l2 = math.hypot(*v1), math.hypot(*v2)
        if l1 < 1e-9 or l2 < 1e-9:
            continue
        u1, u2 = (v1[0] / l1, v1[1] / l1), (v2[0] / l2, v2[1] / l2)
        cosang = max(-1.0, min(1.0, u1[0] * u2[0] + u1[1] * u2[1]))
        ang = math.acos(cosang)
        if ang > math.pi - 1e-3 or ang < 1e-3:
            out.append(b)
            continue
        t = min(r / math.tan(ang / 2), l1 * 0.5, l2 * 0.5)
        rr = t * math.tan(ang / 2)
        p1 = (b[0] + u1[0] * t, b[1] + u1[1] * t)
        p2 = (b[0] + u2[0] * t, b[1] + u2[1] * t)
        bis = (u1[0] + u2[0], u1[1] + u2[1])
        bl = math.hypot(*bis)
        cc = (b[0] + bis[0] / bl * rr / math.sin(ang / 2), b[1] + bis[1] / bl * rr / math.sin(ang / 2))
        s0 = math.atan2(p1[1] - cc[1], p1[0] - cc[0])
        s1 = math.atan2(p2[1] - cc[1], p2[0] - cc[0])
        d = s1 - s0
        while d > math.pi:
            d -= 2 * math.pi
        while d < -math.pi:
            d += 2 * math.pi
        n = max(2, int(abs(d) * rr / step) + 1)
        out += [(cc[0] + rr * math.cos(s0 + d * k / n), cc[1] + rr * math.sin(s0 + d * k / n)) for k in range(n + 1)]
    out.append(pts[-1])
    return out


def resample(pts, pitch, first=None):
    """Points every `pitch` along the polyline, starting `first` (default half a pitch) from its start."""
    out, need = [], (pitch / 2 if first is None else first)
    for a, b in zip(pts, pts[1:]):
        seg = math.hypot(b[0] - a[0], b[1] - a[1])
        while need <= seg and seg > 0:
            t = need / seg
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
            need += pitch
        need -= seg
    return out


def mirror_x(pts, x0):
    return [(2 * x0 - x, y) for x, y in pts]


def rrect(x0, y0, x1, y1, r, step=0.12):
    """Closed rounded rectangle, clockwise on screen from the top-left corner's end."""
    pts = []
    for (cx, cy, a0) in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        pts += arc((cx, cy), r, a0, a0 + 90, step)
    return pts + [pts[0]]


# ------------------------------------------------------------------------------------ the stroke alphabet
# Capitals, digits and signs as centre lines on a unit square (x across, y down from the cap line to
# the base line). They stand in for KiCad's stroke font in the pictures: every fixed name is scaled so
# that its ink has the left bearing and the width that tools/fascia_art.py measured with pcbnew (FONT),
# so the names' boxes, which the checks use, are KiCad's and not this alphabet's.
GLYPH = {
    "A": (0.80, [[(0, 1), (0.4, 0), (0.8, 1)], [(0.14, 0.66), (0.66, 0.66)]]),
    "B": (0.60, [[(0, 0), (0, 1), (0.44, 1), (0.6, 0.88), (0.6, 0.62), (0.44, 0.5), (0, 0.5)], [(0.44, 0.5), (0.56, 0.4), (0.56, 0.12), (0.42, 0), (0, 0)]]),
    "D": (0.62, [[(0, 0), (0, 1), (0.36, 1), (0.62, 0.74), (0.62, 0.26), (0.36, 0), (0, 0)]]),
    "E": (0.55, [[(0.55, 0), (0, 0), (0, 1), (0.55, 1)], [(0, 0.48), (0.4, 0.48)]]),
    "F": (0.55, [[(0.55, 0), (0, 0), (0, 1)], [(0, 0.48), (0.4, 0.48)]]),
    "I": (0.0, [[(0, 0), (0, 1)]]),
    "L": (0.50, [[(0, 0), (0, 1), (0.5, 1)]]),
    "M": (0.80, [[(0, 1), (0, 0), (0.4, 0.72), (0.8, 0), (0.8, 1)]]),
    "N": (0.62, [[(0, 1), (0, 0), (0.62, 1), (0.62, 0)]]),
    "O": (0.66, [[(0.2, 0), (0.46, 0), (0.66, 0.22), (0.66, 0.78), (0.46, 1), (0.2, 1), (0, 0.78), (0, 0.22), (0.2, 0)]]),
    "P": (0.58, [[(0, 1), (0, 0), (0.42, 0), (0.58, 0.12), (0.58, 0.4), (0.42, 0.52), (0, 0.52)]]),
    "R": (0.60, [[(0, 1), (0, 0), (0.42, 0), (0.58, 0.12), (0.58, 0.4), (0.42, 0.52), (0, 0.52)], [(0.3, 0.52), (0.6, 1)]]),
    "S": (0.58, [[(0.58, 0.14), (0.42, 0), (0.16, 0), (0, 0.13), (0, 0.36), (0.14, 0.47), (0.44, 0.53), (0.58, 0.64), (0.58, 0.87), (0.42, 1), (0.16, 1), (0, 0.86)]]),
    "T": (0.62, [[(0, 0), (0.62, 0)], [(0.31, 0), (0.31, 1)]]),
    "U": (0.62, [[(0, 0), (0, 0.8), (0.18, 1), (0.44, 1), (0.62, 0.8), (0.62, 0)]]),
    "Y": (0.64, [[(0, 0), (0.32, 0.5), (0.64, 0)], [(0.32, 0.5), (0.32, 1)]]),
    "/": (0.50, [[(0.5, -0.05), (0, 1.2)]]),
    "1": (0.30, [[(0.02, 0.2), (0.3, 0), (0.3, 1)]]),
    "2": (0.58, [[(0, 0.16), (0.15, 0), (0.42, 0), (0.57, 0.15), (0.57, 0.38), (0, 1), (0.58, 1)]]),
    "3": (0.58, [[(0, 0), (0.56, 0), (0.26, 0.4), (0.42, 0.4), (0.58, 0.55), (0.58, 0.85), (0.42, 1), (0.14, 1), (0, 0.88)]]),
    "4": (0.60, [[(0.44, 1), (0.44, 0), (0, 0.68), (0.6, 0.68)]]),
    "5": (0.57, [[(0.54, 0), (0.06, 0), (0, 0.45), (0.14, 0.38), (0.4, 0.38), (0.57, 0.52), (0.57, 0.84), (0.4, 1), (0.14, 1), (0, 0.88)]]),
    "6": (0.57, [[(0.5, 0), (0.3, 0), (0.08, 0.25), (0, 0.55), (0, 0.82), (0.15, 1), (0.42, 1), (0.57, 0.84), (0.57, 0.58), (0.42, 0.42), (0.15, 0.42), (0, 0.6)]]),
    "-": (0.62, [[(0, 0.5), (0.62, 0.5)]]),
    "+": (0.72, [[(0, 0.5), (0.72, 0.5)], [(0.36, 0.14), (0.36, 0.86)]]),
    " ": (0.30, []),
}
CAP_UP = 0.543            # KiCad: capitals run from 0.543 of the size above the anchor to 0.457 below (fascia_art.py)
GLYPH_GAP = 0.30


def text_strokes(s, x, y, h, just="centre", ink=None, bearing=0.0, advance=None):
    """Centre lines of the string. ink = (left bearing, ink width) per mm of size from KiCad, if known."""
    xs, cur, strokes = [], 0.0, []
    for ch in s:
        w, st = GLYPH[ch]
        xs.append((cur, w, st))
        cur += w + GLYPH_GAP
    natural = cur - GLYPH_GAP
    if ink:
        width = ink[1] * h
        adv = (advance if advance is not None else ink[1] + 2 * ink[0]) * h
        lead = ink[0] * h
    else:
        width = natural * h
        adv = width
        lead = 0.0
    k = width / natural if natural > 0 else h
    left = x + lead if just == "left" else (x - adv + lead if just == "right" else x - adv / 2 + lead)
    top = y - CAP_UP * h
    for (gx, w, st) in xs:
        for line in st:
            strokes.append([(left + (gx + px) * k, top + py * h) for px, py in line])
    return strokes, (left, top, left + width, top + h)


# ------------------------------------------------------------------------------------ rasters for the checks
class Mask:
    """A boolean raster of a board, `res` pixels per mm. A pixel is set when its centre is inside a shape."""

    def __init__(self, w, h, res, ox=0.0):
        self.res, self.w, self.h, self.ox = res, w, h, ox          # ox: the board x that sits at the raster's left edge
        self.nx, self.ny = int(round(w * res)), int(round(h * res))
        self.a = np.zeros((self.ny, self.nx), bool)

    def _win(self, x0, y0, x1, y1):
        i0, i1 = max(0, int(math.floor(x0 * self.res))), min(self.nx, int(math.ceil(x1 * self.res)) + 1)
        j0, j1 = max(0, int(math.floor(y0 * self.res))), min(self.ny, int(math.ceil(y1 * self.res)) + 1)
        return i0, i1, j0, j1

    def seg(self, a, b, r):
        a, b = (a[0] - self.ox, a[1]), (b[0] - self.ox, b[1])
        i0, i1, j0, j1 = self._win(min(a[0], b[0]) - r, min(a[1], b[1]) - r, max(a[0], b[0]) + r, max(a[1], b[1]) + r)
        if i0 >= i1 or j0 >= j1:
            return
        X = ((np.arange(i0, i1) + 0.5) / self.res)[None, :]
        Y = ((np.arange(j0, j1) + 0.5) / self.res)[:, None]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = dx * dx + dy * dy
        if L > 0:
            t = np.clip(((X - a[0]) * dx + (Y - a[1]) * dy) / L, 0, 1)
        else:
            t = 0.0
        d2 = (X - a[0] - t * dx) ** 2 + (Y - a[1] - t * dy) ** 2
        self.a[j0:j1, i0:i1] |= d2 <= r * r

    def line(self, pts, r):
        if len(pts) == 1:
            self.seg(pts[0], pts[0], r)
        for a, b in zip(pts, pts[1:]):
            self.seg(a, b, r)

    def butt(self, a, b, r):
        """A straight stroke with square (butt) ends: the weave's dashes."""
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        if L == 0:
            return
        nx, ny = -dy / L * r, dx / L * r
        self.poly([(a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny), (b[0] - nx, b[1] - ny), (a[0] - nx, a[1] - ny)])

    def disc(self, c, r):
        self.seg(c, c, r)

    def rect(self, x0, y0, x1, y1):
        x0, x1 = x0 - self.ox, x1 - self.ox
        i0, i1, j0, j1 = self._win(x0, y0, x1, y1)
        X = ((np.arange(i0, i1) + 0.5) / self.res)[None, :]
        Y = ((np.arange(j0, j1) + 0.5) / self.res)[:, None]
        self.a[j0:j1, i0:i1] |= (X >= x0) & (X <= x1) & (Y >= y0) & (Y <= y1)

    def poly(self, pts, grow=0.0):
        src = pts
        pts = [(p[0] - self.ox, p[1]) for p in pts]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        i0, i1, j0, j1 = self._win(min(xs), min(ys), max(xs), max(ys))
        if i0 >= i1 or j0 >= j1:
            return
        X = ((np.arange(i0, i1) + 0.5) / self.res)[None, :]
        Y = ((np.arange(j0, j1) + 0.5) / self.res)[:, None]
        inside = np.zeros((j1 - j0, i1 - i0), bool)
        n = len(pts)
        for k in range(n):
            (xa, ya), (xb, yb) = pts[k], pts[(k + 1) % n]
            if ya == yb:
                continue
            cond = (ya > Y) != (yb > Y)
            xint = xa + (Y - ya) * (xb - xa) / (yb - ya)
            inside ^= cond & (X < xint)
        self.a[j0:j1, i0:i1] |= inside
        if grow > 0:
            self.line(list(src) + [src[0]], grow)

    def at(self, xs, ys):
        i = np.floor((np.asarray(xs) - self.ox) * self.res).astype(int)
        j = np.floor(np.asarray(ys) * self.res).astype(int)
        ok = (i >= 0) & (i < self.nx) & (j >= 0) & (j < self.ny)
        out = np.ones(i.shape, bool)
        out[ok] = self.a[j[ok], i[ok]]
        return out


def edt(a, res, cap):
    """Distance in mm from each pixel centre to the nearest set pixel's centre, exact up to `cap`."""
    R = int(math.ceil(cap * res))
    ny, nx = a.shape
    idx = np.arange(nx)[None, :]
    left = np.maximum.accumulate(np.where(a, idx, -10 ** 7), axis=1)
    right = np.minimum.accumulate(np.where(a, idx, 10 ** 7)[:, ::-1], axis=1)[:, ::-1]
    g = np.minimum(np.minimum(idx - left, right - idx), R + 1).astype(np.float32)
    g2 = g * g
    out = np.full(a.shape, float((R + 1) ** 2), np.float32)
    for dy in range(-R, R + 1):
        if dy == 0:
            np.minimum(out, g2, out=out)
        elif dy > 0:
            np.minimum(out[dy:], g2[:-dy] + dy * dy, out=out[dy:])
        else:
            np.minimum(out[:dy], g2[-dy:] + dy * dy, out=out[:dy])
    return np.sqrt(out) / res


def gap(dist_a, b, res):
    """Least gap from the shape behind dist_a to the set pixels of b: centre distance less one pixel
    (a centre lies up to 0.7 pixel inside its shape, so this never overstates the gap by more than that)."""
    if not b.any():
        return None
    j, i = np.unravel_index(np.argmin(np.where(b, dist_a, 1e9)), b.shape)
    return float(dist_a[j, i]) - 1.0 / res, ((i + 0.5) / res, (j + 0.5) / res)


def edge_inset(w, h, r, res, margin):
    """Mask of the pixels nearer than `margin` to a rounded-rectangle outline (or outside it)."""
    nx, ny = int(round(w * res)), int(round(h * res))
    X = ((np.arange(nx) + 0.5) / res)[None, :]
    Y = ((np.arange(ny) + 0.5) / res)[:, None]
    qx = np.abs(X - w / 2) - (w / 2 - r)
    qy = np.abs(Y - h / 2) - (h / 2 - r)
    d = np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2) + np.minimum(np.maximum(qx, qy), 0) - r   # < 0 inside
    return d > -margin


def clip_run(a, b, ko, step=0.05, least=0.4):
    """The parts of the straight stroke a-b whose centre line is outside the keep-out mask `ko`."""
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    n = max(2, int(L / step) + 1)
    t = np.linspace(0, 1, n)
    xs, ys = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
    bad = ko.at(xs, ys)
    out, s = [], None
    for k in range(n + 1):
        free = k < n and not bad[k]
        if free and s is None:
            s = k
        if not free and s is not None:
            e = k - 1
            if (t[e] - t[s]) * L >= least:
                out.append(((xs[s], ys[s]), (xs[e], ys[e])))
            s = None
    return out


# ------------------------------------------------------------------------------------ SVG
def d_of(pts, close=False):
    return "M" + " L".join("%.3f %.3f" % (x, y) for x, y in pts) + ("Z" if close else "")


def d_segs(segs):
    return "".join("M%.3f %.3f L%.3f %.3f" % (a[0], a[1], b[0], b[1]) for a, b in segs)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


CHROME = ("google-chrome", "chromium", "chromium-browser", "chrome")


def find_browser():
    for n in CHROME:
        p = shutil.which(n)
        if p:
            return p
    return None


def render(html_path, png_path, width, height=6000, bg="#16161a", pad=26):
    """HTML (with inline SVG) to PNG: a headless browser screenshot, then ImageMagick trims the page to its ink.
    No network is used: the page holds no link, and the browser's own background calls are switched off."""
    br = find_browser()
    if not br or not shutil.which("convert"):
        print("   no headless browser or no ImageMagick here: left %s unrendered" % html_path)
        return False
    raw = png_path + ".raw.png"
    cmd = [br, "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
           "--disable-background-networking", "--disable-component-update", "--disable-sync", "--no-first-run",
           "--disable-default-apps", "--host-resolver-rules=MAP * ~NOTFOUND", "--window-size=%d,%d" % (width, height),
           "--screenshot=" + raw, "file://" + os.path.abspath(html_path)]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=300)
    if not os.path.exists(raw):
        print("   the browser wrote no picture for", html_path)
        return False
    subprocess.run(["convert", raw, "-trim", "+repage", "-bordercolor", bg, "-border", str(pad), "-strip", png_path], check=True)
    os.remove(raw)
    return True
