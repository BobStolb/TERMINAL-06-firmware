#!/usr/bin/env python3
"""Reader for the two boards of the YARN pair. It only reads; it never writes a board file.

    python3 PCB/art/TS06-PAIR-YARN/yarn_boards.py            # prints a summary of both boards

Everything the drawing needs from the boards comes through here: outline, holes, parts, pads,
tracks, zone outlines and texts, all in each board's own KiCad frame (origin top-left, x right,
y down, mm). Rotation follows KiCad: a footprint at angle a puts its local point (x, y) at
(X + x cos a + y sin a, Y - x sin a + y cos a).
"""
import math, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
FASCIA = os.path.join(ROOT, "PCB", "TS06-FASCIA-rhythm", "TS06-FASCIA-rhythm.kicad_pcb")
DISP = os.path.join(ROOT, "PCB", "TS06-DISP", "TS06-DISP.kicad_pcb")

_TOK = re.compile(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+')


def parse(text):
    stack = [[]]
    for m in _TOK.finditer(text):
        t = m.group(0)
        if t == "(":
            new = []
            stack[-1].append(new)
            stack.append(new)
        elif t == ")":
            stack.pop()
        elif t[0] == '"':
            stack[-1].append(t[1:-1].replace('\\"', '"'))
        else:
            stack[-1].append(t)
    return stack[0][0]


def kids(n, name):
    return [c for c in n if isinstance(c, list) and c and c[0] == name]


def kid(n, name):
    k = kids(n, name)
    return k[0] if k else None


def nums(n):
    return [float(v) for v in n[1:] if re.match(r"^-?[\d.]+(e-?\d+)?$", str(v))]


def _width(x):
    st = kid(x, "stroke")
    if st and kid(st, "width"):
        return float(kid(st, "width")[1])
    w = kid(x, "width")
    return float(w[1]) if w else 0.0


def _rot(px, py, deg):
    a = math.radians(deg)
    return (px * math.cos(a) + py * math.sin(a), -px * math.sin(a) + py * math.cos(a))


def arc3(s, m, e, step=0.15):
    """Points along the arc through start, mid, end."""
    (x1, y1), (x2, y2), (x3, y3) = s, m, e
    d = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    if abs(d) < 1e-12:
        return [s, e], None, None
    ux = ((x1 * x1 + y1 * y1) * (y2 - y3) + (x2 * x2 + y2 * y2) * (y3 - y1) + (x3 * x3 + y3 * y3) * (y1 - y2)) / d
    uy = ((x1 * x1 + y1 * y1) * (x3 - x2) + (x2 * x2 + y2 * y2) * (x1 - x3) + (x3 * x3 + y3 * y3) * (x2 - x1)) / d
    r = math.hypot(x1 - ux, y1 - uy)
    a1, a2, a3 = (math.atan2(p[1] - uy, p[0] - ux) for p in (s, m, e))
    def unwrap(a, ref, sign):
        while sign * (a - ref) < 0:
            a += sign * 2 * math.pi
        return a
    sign = 1
    if not (unwrap(a2, a1, 1) <= unwrap(a3, a1, 1)):
        sign = -1
    a3u = unwrap(a3, a1, sign)
    n = max(2, int(abs(a3u - a1) * r / step) + 1)
    pts = [(ux + r * math.cos(a1 + (a3u - a1) * k / n), uy + r * math.sin(a1 + (a3u - a1) * k / n)) for k in range(n + 1)]
    return pts, (ux, uy), r


def load(path):
    t = parse(open(path, encoding="utf-8").read())
    nets = {int(n[1]): n[2] for n in kids(t, "net")}
    B = dict(path=path, nets=nets, edge=[], graphics=[], texts=[], parts=[], pads=[], tracks=[], zones=[])
    for x in t:
        if not isinstance(x, list):
            continue
        k = x[0]
        if k in ("gr_line", "gr_arc", "gr_circle", "gr_rect"):
            layer = kid(x, "layer")[1]
            it = dict(kind=k[3:], layer=layer, w=_width(x))
            if k == "gr_line":
                it["pts"] = [tuple(nums(kid(x, "start"))), tuple(nums(kid(x, "end")))]
            elif k == "gr_arc":
                pts, c, r = arc3(tuple(nums(kid(x, "start"))), tuple(nums(kid(x, "mid"))), tuple(nums(kid(x, "end"))))
                it.update(pts=pts, c=c, r=r)
            elif k == "gr_circle":
                c = tuple(nums(kid(x, "center")))
                e = tuple(nums(kid(x, "end")))
                it.update(c=c, r=math.hypot(e[0] - c[0], e[1] - c[1]))
            else:
                s, e = tuple(nums(kid(x, "start"))), tuple(nums(kid(x, "end")))
                it["pts"] = [s, (e[0], s[1]), e, (s[0], e[1]), s]
            (B["edge"] if layer == "Edge.Cuts" else B["graphics"]).append(it)
        elif k == "gr_text":
            eff = kid(x, "effects")
            font = kid(eff, "font")
            just = kid(eff, "justify")
            at = nums(kid(x, "at"))
            th = kid(font, "thickness")
            B["texts"].append(dict(s=x[1], x=at[0], y=at[1], rot=at[2] if len(at) > 2 else 0.0,
                                   layer=kid(x, "layer")[1], h=nums(kid(font, "size"))[0], wd=nums(kid(font, "size"))[1],
                                   t=float(th[1]) if th else 0.15, bold=bool(kid(font, "bold")) or "bold" in font,
                                   just=(just[1] if just and just[1] in ("left", "right") else "centre"),
                                   mirror=bool(just and "mirror" in just)))
        elif k == "segment":
            s, e = tuple(nums(kid(x, "start"))), tuple(nums(kid(x, "end")))
            B["tracks"].append(dict(a=s, b=e, w=float(kid(x, "width")[1]), layer=kid(x, "layer")[1],
                                    net=nets.get(int(kid(x, "net")[1]), "")))
        elif k == "zone":
            poly = kid(kid(x, "polygon"), "pts") if kid(x, "polygon") else None
            pts = [tuple(nums(p)) for p in kids(poly, "xy")] if poly else []
            ly = kid(x, "layer") or kid(x, "layers")
            B["zones"].append(dict(net=kid(x, "net_name")[1] if kid(x, "net_name") else "", layers=ly[1:], pts=pts))
        elif k == "footprint":
            at = nums(kid(x, "at"))
            X, Y, A = at[0], at[1], (at[2] if len(at) > 2 else 0.0)
            ref = val = ""
            for pr in kids(x, "property"):
                if pr[1] == "Reference":
                    ref = pr[2]
                elif pr[1] == "Value":
                    val = pr[2]
            part = dict(ref=ref, val=val, lib=x[1], x=X, y=Y, rot=A, layer=kid(x, "layer")[1], pads=[], gfx=[])
            for p in kids(x, "pad"):
                pat = nums(kid(p, "at"))
                dx, dy = _rot(pat[0], pat[1], A)
                size = nums(kid(p, "size"))
                prot = pat[2] if len(pat) > 2 else 0.0          # KiCad stores the pad's absolute angle
                if abs((prot % 180) - 90) < 1:
                    size = [size[1], size[0]]
                dr = kid(p, "drill")
                drill = None
                if dr:
                    dn = nums(dr)
                    if "oval" in dr:
                        dd = [dn[0], dn[1]]
                        if abs((prot % 180) - 90) < 1:
                            dd = [dd[1], dd[0]]
                        drill = tuple(dd)
                    elif dn:
                        drill = (dn[0], dn[0])
                net = kid(p, "net")
                pad = dict(ref=ref, num=p[1], kind=p[2], shape=p[3], x=X + dx, y=Y + dy, sx=size[0], sy=size[1],
                           drill=drill, net=(net[2] if net and len(net) > 2 else ""), layers=kid(p, "layers")[1:])
                part["pads"].append(pad)
                B["pads"].append(pad)
            for g in x:
                if isinstance(g, list) and g[0] in ("fp_line", "fp_circle", "fp_arc", "fp_rect", "fp_poly"):
                    ly = kid(g, "layer")[1]
                    it = dict(kind=g[0][3:], layer=ly, w=_width(g))
                    def tr(p):
                        d = _rot(p[0], p[1], A)
                        return (X + d[0], Y + d[1])
                    if g[0] == "fp_line":
                        it["pts"] = [tr(nums(kid(g, "start"))), tr(nums(kid(g, "end")))]
                    elif g[0] == "fp_circle":
                        c, e = nums(kid(g, "center")), nums(kid(g, "end"))
                        it.update(c=tr(c), r=math.hypot(e[0] - c[0], e[1] - c[1]))
                    elif g[0] == "fp_arc":
                        pts, c, r = arc3(tr(nums(kid(g, "start"))), tr(nums(kid(g, "mid"))), tr(nums(kid(g, "end"))))
                        it.update(pts=pts, c=c, r=r)
                    elif g[0] == "fp_rect":
                        s, e = nums(kid(g, "start")), nums(kid(g, "end"))
                        it["pts"] = [tr(q) for q in (s, (e[0], s[1]), e, (s[0], e[1]), s)]
                    else:
                        it["pts"] = [tr(nums(q)) for q in kids(kid(g, "pts"), "xy")]
                        it["pts"].append(it["pts"][0])
                    part["gfx"].append(it)
            B["parts"].append(part)
    xs = [p[0] for it in B["edge"] for p in it.get("pts", [])]
    ys = [p[1] for it in B["edge"] for p in it.get("pts", [])]
    B["box"] = (min(xs), min(ys), max(xs), max(ys))
    return B


def hv(net):
    """The 185 V nets of the display (TS06-DISP.kicad_pro, class HV)."""
    return net.startswith("ANODE_") or net.startswith("COLON_")


def summary(B, name):
    print("== %s  %s" % (name, os.path.relpath(B["path"], ROOT)))
    print("   outline box %.2f %.2f %.2f %.2f; %d parts, %d pads, %d tracks, %d zones, %d texts, %d graphics"
          % (B["box"] + (len(B["parts"]), len(B["pads"]), len(B["tracks"]), len(B["zones"]), len(B["texts"]), len(B["graphics"]))))
    for p in B["parts"]:
        holes = sorted({pd["drill"] for pd in p["pads"] if pd["drill"]})
        print("   %-5s %-14s at %8.3f %7.3f rot %5.1f %s pads %2d drills %s" % (p["ref"], p["val"][:14], p["x"], p["y"], p["rot"], p["layer"], len(p["pads"]), holes))


if __name__ == "__main__":
    for nm, path in (("fascia R rev B", FASCIA), ("display", DISP)):
        summary(load(path), nm)
