#!/usr/bin/env python3
"""Gold-trace variations for TS06-FASCIA: one white-silk base, four different golds.

    python3 tools/fascia_gold.py VARIANT OUT.kicad_pcb [--base A|R] [--base-pcb BOARD.kicad_pcb]
    python3 tools/fascia_gold.py all OUTDIR [--base A|R]        # every variant into OUTDIR
    python3 tools/fascia_gold.py --list
    python3 tools/fascia_gold.py VARIANT OUT.kicad_pcb --preview OUT.png   # a quick flat picture
    python3 tools/fascia_gold.py all OUTDIR --drc                       # KiCad 10 DRC on each, against the base's own
    (the KiCad 3D renders come from tools/render_kicad.py; KiCad runs in Docker unless KICAD_CLI names a binary)

VARIANT is one of ladder, divider, fans, guilloche. --base picks the board: A is PCB/TS06-FASCIA
(176 x 40, controls on y 14), R is PCB/TS06-FASCIA-rhythm (191.4 x 40, controls on y 16). The
output is a scratch board. Nothing under PCB/ is written.
--base-pcb BOARD reads that board in place of the committed one (for R: the board of
`tools/mkpcb_fascia_rhythm.py --out FILE [--open-holes]`, so the fascia with its control holes opened is built the same way;
fab/HOLES-VARIANT.md). Every check below runs against it as against the committed board.

THE WHITE SILK IS CONSTANT. It is the "Plates" silk of tools/fascia_art.py, taken from
fascia_art.v_plates() item for item: the six names, the MODE / FIELD / SUB nameplates, the hairline
dial arc and the leaders. Only the gold changes, so the owner compares gold against gold. build()
asserts that the silk items of every variant are identical to Plates' own, and same_copper()
proves every non-artwork item of the board (footprints, tracks, zone, holes, edge, back silk) is
byte for byte the base's.

SAFETY. On A and R the front copper layer carries no pad, no track, no via and no zone (every part
is on the back; the front holes are NPTH with no annular ring): front_copper_free() checks this on
the base. All gold is therefore netless copper and touches no net; none of it is tied to a net.
The checker (check()) keeps:
  * gold to gold: 0.3 mm between mask openings (0.2 mm between copper, the copper is 0.05 mm larger
    each side) wherever two separate pieces of gold meet; pieces in one group are one piece;
  * gold to silk 0.3 mm; silk to silk 0.25 mm;
  * gold 6.0 mm from each lever's and button's centre (the body), 9.0 mm from the dial's shaft
    (the knob), out of each lever's swing (2 mm either side, 7 mm up, 6.3 mm down);
  * 1.4 mm from the board edge and 3.0 mm from a screw centre;
  * labels 3.0 mm tall or more (there are no gold letters; the - and + are drawn as strokes 3.2 mm long).
KiCad's project rules ask for 0.5 mm copper to the edge and 0.25 mm copper to a hole; these keep
a wide margin over both.

TRUTH. The gold draws things that are so, and the generator reads them from the board rather than
trusting a number typed here: circuit() reads the divider's chain and the lever ladder from the
nets, and asserts they are GND - R1 - TAP2 - R2 - TAP3 - R3 - TAP4 - R4 - TAP5 - R5 - +5V, five
equal resistors; SW1's tap pads carry the same six nets; the levers reach A7 through LEVA / LEVB.
READ (below) is spec section 1's control table: which screens read which control.

ON R. Only divider is laid out for R (the favourite, so the owner can see it on the tube-grid board).
R puts FIELD 39 mm from the dial, so there position 5's trace drops 45 degrees into the frame's side, as
in Plates, and takes no pad (it would touch FORMAT/DATE). The other three are laid out for A; on R
they fail their checks (ladder refuses).

THE VARIANTS (one line each; the owner's review has pictures):
  ladder    the SUB rule as a Soviet relay-logic ladder (GOST-style contacts, an OR join, FIELD's
            gap closed by the lever, SUB as the coil, earth), the dial as a curved ladder, the two
            buttons as contacts to earth.
  divider   the dial IS the divider: the six taps are pads round the arc with a resistor body
            between each pair, tails to GND and +5V, teardrops on every pad; the rule in the same
            PCB language.
  fans      every control wears the dial's own 30-degree fan; a heavy tick is a screen where the spec
            reads that control, a hairline tick a screen where it does nothing (1 and 6 are parking);
            SUB's fan is the box the rule feeds.
  guilloche a rose-engine rosette behind the dial's scale, the rule as three braided cords, SUB in a
            double engraved frame, the - and + on coin medallions.
"""
import argparse, collections, json, math, os, re, shutil, subprocess, sys, tempfile, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fascia_art as fa
from fascia_art import P, ANG, NAMES, THROW, RULES

# spec section 1 (knowledge/TERMINAL-06-spec.txt, Rev D.3): the screens (1..6) on which each control is read.
# SUB's read is conditional on FIELD being thrown down; 1 (NORMAL) and 6 (INFO) ignore everything.
READ = {"FIELD": (2, 3, 4, 5), "SUB": (3, 5), "-": (2, 3, 4, 5), "+": (2, 3, 4, 5)}
PAD_R = 1.1            # radius of FIELD's contact pad: its top edge is the throw point (6.6 mm below centre)
EDGE_MM = 1.4          # gold this far inside the edge (KiCad's rule is 0.5)
HOLE_GAP = 0.1         # a gold line that joins a ring stops with its round end this far short of the ring's hole


# ============================================================================ geometry helpers
def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def add(a, b, k=1.0):
    return (a[0] + k * b[0], a[1] + k * b[1])


def unit(v):
    n = math.hypot(v[0], v[1])
    return (v[0] / n, v[1] / n)


def dist2(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def fillet(pts, r):
    """A polyline with round corners: [('line', a, b) | ('arc', c, r, a0, a1)]. A corner whose
    tangent length would pass the middle of a neighbouring segment gets a smaller radius."""
    out, cur, n = [], pts[0], len(pts)
    for i in range(1, n - 1):
        p0, p, p1 = pts[i - 1], pts[i], pts[i + 1]
        d1, d2 = unit(sub(p, p0)), unit(sub(p1, p))
        cr = d1[0] * d2[1] - d1[1] * d2[0]
        phi = math.acos(max(-1.0, min(1.0, d1[0] * d2[0] + d1[1] * d2[1])))
        if phi < 1e-6 or r <= 0:
            continue
        t = r * math.tan(phi / 2)
        tmax = min(dist2(p0, p) if i == 1 else dist2(p0, p) / 2, dist2(p, p1) if i == n - 2 else dist2(p, p1) / 2)
        rr = r
        if t > tmax:
            t, rr = tmax, tmax / math.tan(phi / 2)
        t1, t2 = add(p, d1, -t), add(p, d2, t)
        if dist2(cur, t1) > 1e-6:
            out.append(("line", cur, t1))
        s = 1.0 if cr > 0 else -1.0
        c = add(t1, (-d1[1] * s, d1[0] * s), rr)
        a1 = math.degrees(math.atan2(t1[1] - c[1], t1[0] - c[0]))
        ph = math.degrees(phi)
        out.append(("arc", c, rr, a1, a1 + ph) if s > 0 else ("arc", c, rr, a1 - ph, a1))
        cur = t2
    if dist2(cur, pts[-1]) > 1e-6:
        out.append(("line", cur, pts[-1]))
    return out


def sample(prims, step=0.3):
    """The centre-line of fillet() output as a dense list of points (for braiding)."""
    pts = []
    for pr in prims:
        if pr[0] == "line":
            a, b = pr[1], pr[2]
            n = max(1, int(dist2(a, b) / step))
            seg = [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n + 1)]
        else:
            _, c, r, a0, a1 = pr
            # the arc runs from the corner's entry to its exit; entry is the end nearer the previous point
            n = max(2, int(abs(a1 - a0) * math.pi / 180 * r / step))
            seg = [P(c, r, a0 + (a1 - a0) * i / n) for i in range(n + 1)]
            if pts and dist2(pts[-1], seg[0]) > dist2(pts[-1], seg[-1]):
                seg.reverse()
        if pts and dist2(pts[-1], seg[0]) < 1e-6:
            seg = seg[1:]
        pts.extend(seg)
    return pts


class GArt(fa.Art):
    def route(self, pts, w, r, grp, ink="gold"):
        for pr in fillet(pts, r):
            if pr[0] == "line":
                self.line(ink, pr[1], pr[2], w, grp)
            else:
                self.arc(ink, pr[1], pr[2], pr[3], pr[4], w, grp)

    def dot(self, c, r, grp):
        self.circle("gold", c, r, 0.0, grp, fill=True)

    def ring(self, c, r, w, grp):
        self.circle("gold", c, r, w, grp)

    def polyline(self, pts, w, grp, ink="gold"):
        for a, b in zip(pts, pts[1:]):
            if dist2(a, b) > 1e-6:
                self.line(ink, a, b, w, grp)

    def teardrop(self, c, rp, d, w, length, grp):
        """A tapered fillet that blends a trace of width w, leaving the pad of radius rp at c in the
        direction d, into the pad: two tangent lines from the trace's edges, length mm along d."""
        d = unit(d)
        n = (-d[1], d[0])
        pts = []
        for s in (1.0, -1.0):
            a = add(add(c, d, length), n, s * w / 2)
            v = sub(a, c)
            al, dd = math.atan2(v[1], v[0]), math.hypot(v[0], v[1])
            be = math.acos(min(1.0, rp / dd))
            t = P(c, rp, math.degrees(al + s * be))
            pts.append((a, t))
        (a1, t1), (a2, t2) = pts
        self.poly("gold", [a1, a2, t2, t1], grp)

    def pad(self, c, rp, grp, d=None, w=None, tear=None):
        self.dot(c, rp, grp)
        if d is not None and tear:
            self.teardrop(c, rp, d, w, tear, grp)

    def ground(self, c, direction, w, grp, stem=1.4, gap=1.0, halves=(2.2, 1.4, 0.6), start=0.0):
        """A GOST earth: a stem, then three bars, each shorter, across the stem. The stem runs from start mm
        along direction (from a ring's rim, say) to stem mm; the bars stand at its end."""
        d = unit(direction)
        n = (-d[1], d[0])
        e = add(c, d, stem)
        self.line("gold", add(c, d, start) if start else c, e, w, grp)
        for k, h in enumerate(halves):
            m = add(e, d, gap * k)
            self.line("gold", add(m, n, h), add(m, n, -h), w, grp)

    def rect(self, c, u, length, width, w, grp):
        """An outlined rectangle centred on c, its long side along u."""
        u = unit(u)
        n = (-u[1], u[0])
        h, k = length / 2, width / 2
        q = [add(add(c, u, sx * h), n, sy * k) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        self.polyline(q + [q[0]], w, grp)


# ============================================================================ the constant silk and the layout
def silk_base(G):
    """Plates' silk, item for item (tools/fascia_art.py v_plates), and nothing else."""
    A = GArt()
    for it in fa.v_plates(G).items:
        if it["ink"] == "silk":
            A.items.append(it)
    return A


def layout(G, A):
    ctrl = G["ctrl"]
    txt = {it["s"]: it for it in A.items if it["kind"] == "text"}
    L = dict(D=ctrl["SW1"], F=ctrl["SW2"], S=ctrl["SW3"], M=ctrl["SW4"], Pl=ctrl["SW5"], W=G["W"], H=G["H"])
    L["rows"] = [txt[n]["y"] for n in NAMES]
    L["nbox"] = [fa.text_box(txt[n]) for n in NAMES]
    L["plate"] = {n: fa.text_box(txt[n]) for n in ("MODE", "FIELD", "SUB")}
    L["ny"] = txt["MODE"]["y"]
    L["e3"], L["e5"] = L["nbox"][2][2] + 2.2, L["nbox"][4][2] + 2.2       # where DISPLAY's and FORMAT/DATE's traces start
    L["compact"] = (L["F"][0] - L["D"][0]) < 50                            # R: FIELD is close to the dial (Plates' own test)
    if L["compact"]:                                                       # and Plates starts the traces a little sooner there
        L["e3"] -= 1.0
        L["e5"] -= 1.4
    L["throw_y"] = L["F"][1] + THROW + PAD_R                                # centre of FIELD's contact pad
    return L


# ============================================================================ the four golds
def key_glyph(A, c, sign, size, w, grp):
    h = size / 2.0
    A.line("gold", (c[0] - h, c[1]), (c[0] + h, c[1]), w, grp)
    if sign == "+":
        A.line("gold", (c[0], c[1] - h), (c[0], c[1] + h), w, grp)


def g_ladder(A, G, L):
    """The SUB rule as a relay-logic ladder: SUB is read when (position 3 OR position 5) AND FIELD is down."""
    D, F, S, M, Pl = L["D"], L["F"], L["S"], L["M"], L["Pl"]
    R, e3, e5, ty = L["rows"], L["e3"], L["e5"], L["throw_y"]
    w = 0.6
    # the dial as a curved ladder: two rails and six rungs; 3 and 5 (the live ones) carry a terminal dot
    A.arc("gold", D, 10.2, ANG[0], ANG[-1], 0.5, "dial")
    A.arc("gold", D, 12.3, ANG[0], ANG[-1], 0.5, "dial")
    for k, a in enumerate(ANG):
        stop = k in (0, 5)                      # 1 and 6 are the end stops: their rungs are heavier
        A.line("gold", P(D, 10.2, a), P(D, 12.3, a), 1.1 if stop else 0.7, "dial")
    # the two dial contacts in parallel (an OR), then FIELD's gap, then the SUB coil, then earth
    x0 = max(e3, e5) + 3.2
    Lc = 6.0
    join = x0 + Lc + 3.0
    g = "rule"

    def contact(y):
        xa, xb = x0 + 1.2, x0 + Lc - 1.2
        A.line("gold", (x0, y), (xa, y), w, g)
        A.dot((xa, y), 0.75, g)
        A.dot((xb, y), 0.75, g)
        a = math.radians(30)
        A.line("gold", (xa, y), (xa + 3.6 * math.cos(a), y - 3.6 * math.sin(a)), w, g)
        A.line("gold", (xb, y), (x0 + Lc, y), w, g)

    A.dot((e3, R[2]), 0.8, g)
    A.line("gold", (e3, R[2]), (x0, R[2]), w, g)
    contact(R[2])
    A.line("gold", (x0 + Lc, R[2]), (join, R[2]), w, g)
    A.dot((e5, R[4]), 0.8, g)
    assert abs(R[4] - ty) < 0.05, "FORMAT/DATE's row is not level with FIELD's contact: this variant is laid out for A"
    A.line("gold", (e5, R[4]), (x0, R[4]), w, g)
    contact(R[4])
    A.line("gold", (x0 + Lc, R[4]), (join, R[4]), w, g)
    A.line("gold", (join, R[2]), (join, ty), w, g)
    A.dot((join, ty), 0.85, g)
    fx = F[0]
    gap = 2.0                                   # FIELD's two contacts, one each side of where the lever's tip lands
    A.line("gold", (join, ty), (fx - gap, ty), w, g)
    A.dot((fx - gap, ty), PAD_R, g)
    A.dot((fx + gap, ty), PAD_R, g)
    sx = S[0]
    bx0, bx1 = sx - 11.5, sx + 11.5
    by0, by1 = S[1] - 9.0, L["plate"]["SUB"][3] + 1.4
    A.line("gold", (fx + gap, ty), (bx0, ty), w, g)
    A.polyline([(bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1), (bx0, by0)], w, g)         # the coil: a plain rectangle
    A.dot((bx0, ty), 0.85, g)
    A.dot((bx1, ty), 0.85, g)
    ex = bx1 + 5.0
    A.polyline([(bx1, ty), (ex, ty), (ex, ty + 8.0)], w, g)
    A.ground((ex, ty + 8.0), (0, 1), 0.5, g, stem=0.0, gap=1.2, halves=(2.4, 1.5, 0.6))
    # the buttons: two square contacts, each to earth
    y = L["ny"]
    xm, xp = M[0], Pl[0]
    for x, sg in ((xm, "-"), (xp, "+")):
        A.polyline([(x - 3.2, y - 3.2), (x + 3.2, y - 3.2), (x + 3.2, y + 3.2), (x - 3.2, y + 3.2), (x - 3.2, y - 3.2)], 0.5, "btn")
        key_glyph(A, (x, y), sg, 3.2, 0.7, "btn")
    mid = (xm + xp) / 2
    A.line("gold", (xm + 3.2, y), (mid, y), 0.5, "btn")
    A.line("gold", (xp - 3.2, y), (mid, y), 0.5, "btn")
    A.dot((mid, y), 0.75, "btn")
    A.ground((mid, y), (0, 1), 0.5, "btn", stem=2.0, gap=1.2, halves=(2.4, 1.5, 0.6))


def seq_chain(A, p, u, parts, w, grp, body_w=1.6):
    """Parts laid one after another from p in direction u: ('wire', mm) or ('res', mm) (a GOST body:
    an outlined rectangle, its leads the wires either side). Returns the end point."""
    u = unit(u)
    for kind, ln in parts:
        q = add(p, u, ln)
        if kind == "wire":
            A.line("gold", p, q, w, grp)
        else:
            A.rect(add(p, u, ln / 2), u, ln, body_w, 0.3, grp)
        p = q
    return p


def a7_ladder(A, cx, y0, sp, grp="a7"):
    """The lever ladder as the board wires it: +5V - R6 (10k) - A7 - two legs, each a lever contact
    and a resistor to earth: FIELD's R7 (20k, drawn as two 10k bodies) and SUB's R8 (10k)."""
    w = 0.45
    yn = y0 + 9.0
    A.ring((cx, y0), 0.7, 0.4, grp)                                   # the +5V terminal
    p = seq_chain(A, (cx, y0 + 0.9), (0, 1), [("wire", 2.0), ("res", 3.4), ("wire", yn - (y0 + 0.9 + 5.4))], w, grp)
    A.dot((cx, yn), 0.7, grp)
    xl, xr = cx - sp / 2, cx + sp / 2
    A.polyline([(xl, yn), (xr, yn)], w, grp)
    yg = yn + 15.6
    for x, bodies in ((xl, 2), (xr, 1)):
        A.line("gold", (x, yn), (x, yn + 2.0), w, grp)
        A.dot((x, yn + 2.0), 0.6, grp)                                 # the lever's contact, open
        A.dot((x, yn + 4.6), 0.6, grp)
        a = math.radians(70)
        A.line("gold", (x, yn + 4.6), (x + 1.2 * math.cos(a) * 1.0, yn + 4.6 - 2.3 * math.sin(a) * 1.0), w, grp)
        parts = [("wire", 2.0)]
        for i in range(bodies):
            parts += ([("wire", 0.6)] if i else []) + [("res", 3.4)]
        end = seq_chain(A, (x, yn + 4.6 + 0.6), (0, 1), parts, w, grp)
        A.line("gold", end, (x, yg), w, grp)
    A.polyline([(xl, yg), (xr, yg)], w, grp)
    A.dot((cx, yg), 0.7, grp)
    A.ground((cx, yg), (0, 1), w, grp, stem=1.2, gap=1.0, halves=(2.0, 1.3, 0.6))


def g_divider(A, G, L):
    """The dial is the real A6 divider: taps round the arc, a resistor between each pair, tails to
    GND (position 1) and +5V (position 6); beside the levers the real A7 ladder; the rule in the same
    PCB language, pads with teardrops."""
    D, F, S, M = L["D"], L["F"], L["S"], L["M"]
    R, e3, e5, ty = L["rows"], L["e3"], L["e5"], L["throw_y"]
    r0 = 11.3
    tw = 0.5
    pr = 0.95
    lug_r, lug_w = pr - 0.3, 0.6                         # a drilled lug: gold ring, black hole (the rotary's tap lugs)
    body_len, body_w = 2.9, 1.7
    span = math.degrees(body_len / 2 / r0)
    g = "div"

    def stop(w, ring_r=lug_r, ring_w=lug_w):
        """How far from a ring's centre a gold line of width w must end: its round end then stays HOLE_GAP clear
        of the ring's hole. A line that ran on to the centre would cut the hole's disc of mask in two, and the
        slivers (0.05 mm and thinner) are what a fab drops (tools/dfm_check.py, the mask web row)."""
        return ring_r - ring_w / 2 + w / 2 + HOLE_GAP
    ga = math.degrees(stop(tw) / r0)                     # the same, as an angle on the dial's arc
    for k, a in enumerate(ANG):
        A.ring(P(D, r0, a), lug_r, lug_w, g)
    for k in range(5):
        a0, a1 = ANG[k], ANG[k + 1]
        m = (a0 + a1) / 2
        c = P(D, r0, m)
        tang = (-math.sin(math.radians(m)), math.cos(math.radians(m)))
        A.rect(c, tang, body_len, body_w, 0.3, g)
        A.arc("gold", D, r0, a0 + ga, m - span, tw, g)   # leads: the arc between the lug's rim and the body
        A.arc("gold", D, r0, m + span, a1 - ga, tw, g)
    # tails round the dead side to the two ends of the chain, then their symbols (GND at 1, +5V at 6)
    endA = 172.0
    A.arc("gold", D, r0, -endA + ga, ANG[0] - ga, tw, g)          # each end stops at the rim of the lug it joins
    A.arc("gold", D, r0, ANG[-1] + ga, endA - ga, tw, g)
    eg, ep = P(D, r0, -endA), P(D, r0, endA)
    A.ring(eg, lug_r, lug_w, g)
    A.ring(ep, lug_r, lug_w, g)
    n0 = len(A.items)
    A.ground(eg, (-1, 0), 0.45, g, stem=1.8, gap=1.1, halves=(2.0, 1.3, 0.6), start=stop(0.45))
    n1 = len(A.items)
    tr, tw_, tout = 1.0, 0.4, 3.2                                 # the +5V terminal ring, tout mm out from its lug
    A.line("gold", add(ep, (-1, 0), stop(0.45)), add(ep, (-1, 0), tout - stop(0.45, tr, tw_)), 0.45, g)
    A.ring(add(ep, (-1, 0), tout), tr, tw_, g)
    # the GND symbol and the +5V terminal are one group, so check() does not keep them apart; at 2.8 mm out they
    # stood 0.096 mm apart (a mask web under the fab's 0.1 mm), so the gap is asserted here
    gap = min(fa.dist(a, b) for a in A.items[n0:n1] for b in A.items[n1:])
    assert gap >= 0.3, "the GND symbol and the +5V terminal ring are %.3f mm apart, need 0.3" % gap
    # the rule: FIELD's contact pad, the SUB box, and the traces from 3 and 5, in 45-degree routing
    w, r = 0.6, 2.6
    fx, sx = F[0], S[0]
    bx0, bx1 = sx - 11.5, sx + 11.5
    by0 = S[1] - 9.0
    by1 = L["plate"]["SUB"][3] + (1.4 if L["compact"] else 2.0)
    rr = "rule"
    A.rrect("gold", bx0, by0, bx1, by1, 3.0, w, rr)
    top_y, bot_y, h = (2.2 if L["compact"] else 1.9), L["H"] - 3.6, 1.8
    d3 = R[2] - top_y
    ent_r, ent_w = 1.0, 0.4                              # an entry ring, where a trace meets the box
    rim = stop(w, ent_r, ent_w)                          # the traces end at its rim, not in its hole
    p3 = [(e3, R[2]), (e3 + d3, top_y), (sx - h, top_y), (sx, top_y + h), (sx, by0 - rim)]
    A.route(p3, w, r, rr)
    entries = [(sx, by0), (bx0, ty)]
    if L["compact"]:                                     # R: 5's trace drops 45 degrees and enters the box's side
        dd = 3.2
        p5 = [(e5, R[4]), (e5 + dd, R[4] + dd), (bx0 - rim, R[4] + dd)]
        entries.append((bx0, R[4] + dd))
    else:
        d5 = bot_y - R[4]
        p5 = [(e5, R[4]), (e5 + d5, bot_y), (sx - h, bot_y), (sx, bot_y - h), (sx, by1 + rim)]
        entries.append((sx, by1))
    A.route(p5, w, r, rr)
    A.pad((e3, R[2]), 0.85, rr, d=(1, -1), w=w, tear=2.0)
    if not L["compact"]:                                 # (on R a pad would touch FORMAT/DATE: Plates starts the trace bare there too)
        A.pad((e5, R[4]), 0.85, rr, d=(1, 1), w=w, tear=2.0)
    A.pad((fx, ty), PAD_R, rr, d=(1, 0), w=w, tear=2.2)
    A.line("gold", (fx, ty), (bx0 - rim, ty), w, rr)
    for c in entries:
        A.ring(c, ent_r, ent_w, rr)
    # the lever ladder in the clear between SUB's box and the buttons
    free0, free1 = bx1 + 0.3, M[0] - 6.0
    sp = 3.8 if free1 - free0 < 14 else 5.6
    a7_ladder(A, (free0 + free1) / 2.0, 6.5, sp)
    # the buttons: the same key frames as Plates use, so - and + read the same
    y = L["ny"]
    for x, sg in ((L["M"][0], "-"), (L["Pl"][0], "+")):
        A.rrect("gold", x - 3.2, y - 3.2, x + 3.2, y + 3.2, 1.0, 0.5, "btn" + sg)
        key_glyph(A, (x, y), sg, 3.2, 0.7, "btn" + sg)


def fan(A, C, live, rf, heavy, grp, lit_w=0.9, dead_w=0.25, hub=None):
    """The dial's own fan round C: an arc of radius rf over 150 degrees and six ticks 30 degrees
    apart; a heavy tick where the control is read, a hairline stub where it does nothing."""
    A.arc("gold", C, rf, ANG[0], ANG[-1], heavy, grp)
    for k, a in enumerate(ANG):
        on = (k + 1) in live
        A.line("gold", P(C, rf, a), P(C, rf + (1.7 if on else 0.9), a), lit_w if on else dead_w, grp)


def g_fans(A, G, L):
    """Every control wears the dial's fan. Heavy ticks mark the screens where spec section 1 reads it."""
    D, F, S, M, Pl = L["D"], L["F"], L["S"], L["M"], L["Pl"]
    R, e3, e5, ty = L["rows"], L["e3"], L["e5"], L["throw_y"]
    for k, a in enumerate(ANG):
        A.line("gold", P(D, 10.2, a), P(D, 12.3, a), 1.0, "bar%d" % k)
    rl, rb = 8.4, 7.0          # a lever's fan stands clear of its 2 mm swing, a button's of the screws
    fan(A, F, READ["FIELD"], rl, 0.35, "fanF")
    fan(A, M, READ["-"], rb, 0.35, "fanM")
    fan(A, Pl, READ["+"], rb, 0.35, "fanP")
    # SUB's fan is the receiving bus of the rule: a heavy arc, ticks 3 and 5 wired
    w = 0.6
    sx, sy = S
    rs = rl
    rr = "rule"
    fan(A, S, READ["SUB"], rs, 0.7, rr)
    tip3, tip5 = P(S, rs + 1.7, ANG[2]), P(S, rs + 1.7, ANG[4])
    base6 = P(S, rs, ANG[5])
    A.dot((F[0], ty), PAD_R, rr)
    # FIELD's trace drops under its own fan, runs level, and climbs into the low end of SUB's arc
    lo = ty + 3.0
    A.route([(F[0], ty), (F[0] + 3.0, lo), (base6[0] - 3.0, lo), base6], w, 2.0, rr)
    top_y, bot_y = 1.9, L["H"] - 3.6
    hx = sx + rs + 5.6
    d3 = R[2] - top_y
    p3 = [(e3, R[2]), (e3 + d3, top_y), (hx - 2.4, top_y), (hx, top_y + 2.4), (hx, tip3[1]), tip3]
    d5 = bot_y - R[4]
    p5 = [(e5, R[4]), (e5 + d5, bot_y), (hx - 2.4, bot_y), (hx, bot_y - 2.4), (hx, tip5[1]), tip5]
    A.route(p3, w, 2.4, rr)
    A.route(p5, w, 2.4, rr)
    A.dot((e3, R[2]), 0.85, rr)
    A.dot((e5, R[4]), 0.85, rr)
    y = L["ny"]
    for x, sg in ((M[0], "-"), (Pl[0], "+")):
        key_glyph(A, (x, y), sg, 3.4, 0.8, "key" + sg)


def g_guilloche(A, G, L):
    """A rose-engine rosette behind the scale, braided cords for the rule, SUB in a double frame,
    coin medallions on - and +."""
    D, F, S, M, Pl = L["D"], L["F"], L["S"], L["M"], L["Pl"]
    R, e3, e5, ty = L["rows"], L["e3"], L["e5"], L["throw_y"]
    g = "rose"
    base, amp, m = 11.1, 0.85, 20
    r_in, r_out = base - amp - 0.5, base + amp + 0.5        # the bounding rules stand 0.3 mm (mask) clear of the lobes
    A.circle("gold", D, r_in, 0.2, g)
    A.circle("gold", D, r_out, 0.2, g)
    win = 4.6                                               # each index bar stands in a window of the weave
    for i in range(4):
        ph = i * 360.0 / m / 4
        run, n = [], 720
        for j in range(n + 1):
            th = 360.0 * j / n
            cut = any(abs(((th - a + 180) % 360) - 180) < win for a in ANG)
            if cut:
                A.polyline(run, 0.2, g)
                run = []
                continue
            run.append(P(D, base + amp * math.sin(math.radians(m * th + ph * m)), th))
        A.polyline(run, 0.2, g)
    for a in ANG:
        A.line("gold", P(D, r_in + 0.4, a), P(D, r_out - 0.4, a), 0.9, g)
    # the rule as braided cords
    w = 0.28
    sx = S[0]
    bx0, bx1 = sx - 11.5, sx + 11.5
    by0, by1 = S[1] - 9.6, L["plate"]["SUB"][3] + 1.8
    rr_ = "rule"
    A.rrect("gold", bx0, by0, bx1, by1, 3.0, 0.4, rr_)
    A.rrect("gold", bx0 + 0.9, by0 + 0.9, bx1 - 0.9, by1 - 0.9, 2.1, 0.2, rr_)
    top_y, bot_y, h = 2.6, L["H"] - 3.6, 1.2
    d3 = R[2] - top_y
    d5 = bot_y - R[4]
    paths = [
        [(e3, R[2]), (e3 + d3, top_y), (sx - h, top_y), (sx, top_y + h), (sx, by0)],
        [(e5, R[4]), (e5 + d5, bot_y), (sx - h, bot_y), (sx, bot_y - h), (sx, by1)],
        [(F[0], ty), (bx0, ty)],
    ]
    for pts in paths:
        cl = sample(fillet(pts, 2.6), 0.25)
        braid(A, cl, w, rr_)
    A.dot((F[0], ty), PAD_R, rr_)
    A.dot((e3, R[2]), 0.85, rr_)
    A.dot((e5, R[4]), 0.85, rr_)
    # coin medallions
    y = L["ny"]
    for x, sg in ((M[0], "-"), (Pl[0], "+")):
        gg = "coin" + sg
        A.circle("gold", (x, y), 3.85, 0.35, gg)
        pts = [P((x, y), 3.1 + 0.3 * math.sin(math.radians(28 * t)), t) for t in [i * 1.0 for i in range(361)]]
        A.polyline(pts, 0.2, gg)
        key_glyph(A, (x, y), sg, 3.2, 0.7, gg)


def braid(A, cl, w, grp, lam=3.4, amp=0.75, taper=1.8):
    """Two strands twisting round the centre-line cl (a dense point list), as a guilloche cord."""
    n = len(cl)
    s = [0.0]
    for i in range(1, n):
        s.append(s[-1] + dist2(cl[i - 1], cl[i]))
    total = s[-1]
    for sign in (1.0, -1.0):
        pts = []
        for i in range(n):
            j0, j1 = max(0, i - 1), min(n - 1, i + 1)
            t = unit(sub(cl[j1], cl[j0]))
            nn = (-t[1], t[0])
            k = min(1.0, s[i] / taper, (total - s[i]) / taper)
            off = sign * amp * k * math.sin(2 * math.pi * s[i] / lam)
            pts.append(add(cl[i], nn, off))
        A.polyline(pts, w, grp)


VARIANTS = {"ladder": g_ladder, "divider": g_divider, "fans": g_fans, "guilloche": g_guilloche}
DOCS = {k: " ".join(v.__doc__.strip().split("\n\n")[0].split()) for k, v in VARIANTS.items()}


# ============================================================================ the circuit, read from the board
def circuit(src):
    """The divider chain and the lever ladder as the board's own nets say they are. Returns a dict and
    asserts the drawings' assumptions."""
    tree = fa_sexp().parse(src)

    def find(n, k):
        return [c for c in n if isinstance(c, list) and c and c[0] == k]

    parts = {}
    for fp in find(tree, "footprint"):
        ref = ([p[2].strip('"') for p in find(fp, "property") if p[1] == '"Reference"'] or [""])[0]
        val = ([p[2].strip('"') for p in find(fp, "property") if p[1] == '"Value"'] or [""])[0]
        pads = []
        for p in find(fp, "pad"):
            net = find(p, "net")
            pads.append((p[1].strip('"'), net[0][-1].strip('"') if net else ""))
        parts[ref] = (val, pads)
    res = {}
    for r in ("R1", "R2", "R3", "R4", "R5"):
        res[r] = (parts[r][0], tuple(sorted(n for _, n in parts[r][1])))
    chain = ["GND"]
    left = {r: set(res[r][1]) for r in res}
    node = "GND"
    order = []
    while left:
        nxt = [r for r, ns in left.items() if node in ns]
        assert len(nxt) == 1, "divider chain is not a chain at %s: %s" % (node, nxt)
        r = nxt[0]
        (other,) = list(left.pop(r) - {node})
        order.append(r)
        chain.append(other)
        node = other
    assert chain == ["GND", "TAP2", "TAP3", "TAP4", "TAP5", "+5V"], chain
    assert len({v for v, _ in res.values()}) == 1, "the five divider resistors are not equal"
    taps = {n for _, n in parts["SW1"][1] if n}
    assert set(chain) <= taps and "A6" in taps, "SW1 does not carry the divider's nets"
    lev = {ref: {n for _, n in parts[ref][1] if n} for ref in ("SW2", "SW3")}
    assert lev["SW2"] == {"LEVA", "A7"} and lev["SW3"] == {"LEVB", "A7"}, lev
    j1 = [n for (pn, n) in parts["J1"][1] if pn.isdigit()]
    assert j1 == ["+5V", "GND", "A6", "A7", "D7", "D8"], j1
    vals = {r: parts[r][0] for r in ("R6", "R7", "R8")}
    assert vals == {"R6": "10k", "R7": "20k", "R8": "10k"}, vals
    assert {parts[r][1][0][1] for r in ("R6",)} <= {"+5V", "A7"} and {n for _, n in parts["R6"][1]} == {"+5V", "A7"}
    assert {n for _, n in parts["R7"][1]} == {"LEVA", "GND"} and {n for _, n in parts["R8"][1]} == {"LEVB", "GND"}
    return dict(chain=chain, order=order, value=res["R1"][0], j1=j1, ladder=vals)


def fa_sexp():
    import sexp
    return sexp


def front_copper_free(src):
    """The base's front copper: pads (with copper) on F.Cu, tracks, vias, zones. Should be empty."""
    tree = fa_sexp().parse(src)
    bad = []

    def find(n, k):
        return [c for c in n if isinstance(c, list) and c and c[0] == k]

    for fp in find(tree, "footprint"):
        ref = ([p[2] for p in find(fp, "property") if p[1] == '"Reference"'] or ['""'])[0]
        for p in find(fp, "pad"):
            ly = " ".join(find(p, "layers")[0][1:]) if find(p, "layers") else ""
            if not re.search(r'"(F\.Cu|\*\.Cu|F&B\.Cu)"', ly):
                continue
            size = [float(v) for v in find(p, "size")[0][1:3]]
            dr = find(p, "drill")
            drill = float(dr[0][-1]) if dr else 0.0
            if p[2] == "np_thru_hole" and abs(size[0] - drill) < 1e-6 and abs(size[1] - drill) < 1e-6:
                continue                                  # a bare hole: no copper ring
            bad.append("%s pad %s on %s" % (ref, p[1], ly))
    for k in ("segment", "via", "arc"):
        for it in find(tree, k):
            ly = find(it, "layer")
            if ly and ly[0][1] == '"F.Cu"':
                bad.append("%s on F.Cu" % k)
    for z in find(tree, "zone"):
        if any('"F.Cu"' in str(l) for l in find(z, "layer") + find(z, "layers")):
            bad.append("zone on F.Cu")
    return bad


# ============================================================================ checks (fascia_art.check, with bounding boxes)
def item_bbox(it):
    xs, ys = [], []
    for a, b, w in fa.segments(it):
        xs += [a[0] - w, a[0] + w, b[0] - w, b[0] + w]
        ys += [a[1] - w, a[1] + w, b[1] - w, b[1] + w]
    return (min(xs), min(ys), max(xs), max(ys))


def bbox_gap(a, b):
    dx = max(a[0] - b[2], b[0] - a[2], 0.0)
    dy = max(a[1] - b[3], b[1] - a[3], 0.0)
    return math.hypot(dx, dy)


def check(A, G):
    """fascia_art.check's rules, faster, with the smallest margins found. Returns (problems, stats).
    One problem line per rule and pair of groups, with the worst value."""
    worst = {}

    def note(key, val, text):
        if key not in worst or val < worst[key][0]:
            worst[key] = (val, text)

    it = A.items
    st = dict(gold_gold=1e9, gold_silk=1e9, edge=1e9, screw=1e9, ctrl=1e9, dial=1e9)
    for x in it:
        if x["kind"] == "text":
            if x["h"] < RULES["min_text"] - 1e-9:
                note(("text", x["s"]), x["h"], "text %r is %.2f mm tall" % (x["s"], x["h"]))
            if x["ink"] == "gold":
                note(("gtext", x["s"]), 0, "gold text %r: none expected" % x["s"])
        elif x["ink"] == "silk" and x["kind"] != "poly" and not (x["kind"] == "circle" and x["fill"]) and x["w"] < RULES["min_silk"] - 1e-9:
            note(("silkw", x["grp"]), x["w"], "silk %s in %s is %.2f wide" % (x["kind"], x["grp"], x["w"]))
    bb = [item_bbox(x) for x in it]
    groups = {}
    for i, x in enumerate(it):
        groups.setdefault(x["grp"], []).append(i)
    gbb = {}
    for g, idx in groups.items():
        gbb[g] = (min(bb[i][0] for i in idx), min(bb[i][1] for i in idx), max(bb[i][2] for i in idx), max(bb[i][3] for i in idx))
    names = list(groups)
    for ai in range(len(names)):
        for bi in range(ai + 1, len(names)):
            ga, gb = names[ai], names[bi]
            if bbox_gap(gbb[ga], gbb[gb]) > 1.0:
                continue
            for i in groups[ga]:
                for j in groups[gb]:
                    if bbox_gap(bb[i], bb[j]) > 1.0:
                        continue
                    a, b = it[i], it[j]
                    if a["ink"] == b["ink"] == "silk":
                        need = RULES["silk_silk"]
                    elif a["ink"] == b["ink"]:
                        need = RULES["gold_gold"]
                    else:
                        need = RULES["silk_gold"]
                    d = fa.dist(a, b)
                    if a["ink"] == b["ink"] == "gold":
                        st["gold_gold"] = min(st["gold_gold"], d)
                    elif a["ink"] != b["ink"]:
                        st["gold_silk"] = min(st["gold_silk"], d)
                    if d < need:
                        note(("pair", ga, gb), d, "%s (%s) and %s (%s): %.2f mm apart, need %.2f" % (
                            a["ink"], ga, b["ink"], gb, d, need))
    W, H = G["W"], G["H"]
    edge = [((0, 0), (W, 0)), ((W, 0), (W, H)), ((W, H), (0, H)), ((0, H), (0, 0))]
    for x in it:
        if x["ink"] != "gold":
            continue
        d = min(fa.segseg(a, b, c, e) - w for a, b, w in fa.segments(x) for c, e in edge)
        box = [p for s in fa.segments(x) for p in s[:2]]
        st["edge"] = min(st["edge"], d)
        if d < EDGE_MM or any(not (0 <= p[0] <= W and 0 <= p[1] <= H) for p in box):
            note(("edge", x["grp"]), d, "gold (%s) is %.2f mm from the edge, need %.1f" % (x["grp"], d, EDGE_MM))
        for s in G["screws"]:
            d = fa.dist_pt(x, s)
            st["screw"] = min(st["screw"], d)
            if d < RULES["screw"]:
                note(("screw", x["grp"]), d, "gold (%s) is %.2f mm from the screw at %s, need 3.0" % (x["grp"], d, s))
        for ref, c in G["ctrl"].items():
            d = fa.dist_pt(x, c)
            lim = RULES["knob"] if ref == "SW1" else 5.6 + RULES["ring_gap"]
            k = "dial" if ref == "SW1" else "ctrl"
            st[k] = min(st[k], d - lim)
            if d < lim:
                note((k, x["grp"], ref), d, "gold (%s) is %.2f mm from %s's centre, need %.2f" % (x["grp"], d, ref, lim))
        for ref in ("SW2", "SW3"):
            cx, cy = G["ctrl"][ref]
            zone = [(cx - RULES["lever_half"], cy - RULES["lever_up"]), (cx + RULES["lever_half"], cy - RULES["lever_up"]),
                    (cx + RULES["lever_half"], cy + RULES["lever_down"]), (cx - RULES["lever_half"], cy + RULES["lever_down"])]
            zi = {"kind": "poly", "pts": zone, "ink": "zone", "grp": "zone", "w": 0.0}
            if fa.dist(x, zi) < 0:
                note(("swing", x["grp"], ref), -1, "gold (%s) is in %s's swing" % (x["grp"], ref))
    return [t for _, t in worst.values()], st


# ============================================================================ build
def gold_items(A):
    return [x for x in A.items if x["ink"] == "gold"]


def build(variant, base="A", out=None):
    src = open(fa.BASES[base], encoding="utf8").read()
    G = fa.geometry(src)
    fc = front_copper_free(src)
    if fc:
        sys.exit("the base has front copper, so gold would not be netless: %s" % fc)
    cir = circuit(src)
    A = silk_base(G)
    silk0 = [dict(x) for x in A.items]
    L = layout(G, A)
    try:
        VARIANTS[variant](A, G, L)
    except AssertionError as e:
        sys.exit("%s on %s: %s" % (variant, base, e))
    assert [x for x in A.items if x["ink"] == "silk"] == silk0, "the silk changed"
    problems, stats = check(A, G)
    stripped, at = fa.strip_art(src)
    ns = uuid.uuid5(uuid.NAMESPACE_URL, "ts06/fascia-gold/%s/%s" % (base, variant))
    new = stripped[:at] + "\n" + fa.emit(A, ns) + stripped[at:]
    n = fa.same_copper(src, new)
    if out:
        open(out, "w", encoding="utf8").write(new)
    return A, G, problems, stats, n, cir


# ============================================================================ KiCad DRC
IMG = os.environ.get("KICAD_IMAGE", "mirror.gcr.io/kicad/kicad:10.0")
DRU = """(version 1)
(rule "front labels at least 3 mm (the owner's rule)"
\t(layer "F.SilkS")
\t(constraint text_height (min 3mm)))
(rule "front gold labels at least 3 mm"
\t(layer "F.Cu")
\t(constraint text_height (min 3mm)))
(rule "front silk stroke at least 0.15 mm"
\t(layer "F.SilkS")
\t(constraint text_thickness (min 0.15mm)))
(rule "silk to silk 0.2 mm"
\t(layer "F.SilkS")
\t(constraint silk_clearance (min 0.2mm)))
"""


def drc(board, base):
    """KiCad 10's DRC (refilled zones, every severity, with the owner's label rules) on a board, run in
    a scratch copy of the base's project. Returns ({(severity, type): count}, unconnected count)."""
    bdir = {"A": "TS06-FASCIA", "R": "TS06-FASCIA-rhythm"}[base]
    tmp = tempfile.mkdtemp(prefix="fascia_drc.")
    try:
        proj = os.path.join(tmp, "PCB", "board")
        os.makedirs(proj)
        shutil.copytree(os.path.join(fa.ROOT, "PCB", "lib"), os.path.join(tmp, "PCB", "lib"))
        shutil.copy(board, os.path.join(proj, "board.kicad_pcb"))
        shutil.copy(os.path.join(fa.ROOT, "PCB", bdir, bdir + ".kicad_pro"), os.path.join(proj, "board.kicad_pro"))
        open(os.path.join(proj, "board.kicad_dru"), "w").write(DRU)
        shutil.copy(os.path.join(fa.ROOT, "PCB", bdir, "fp-lib-table"), os.path.join(proj, "fp-lib-table"))
        for r, ds, fs in os.walk(tmp):
            os.chmod(r, 0o777)
            for f in fs:
                os.chmod(os.path.join(r, f), 0o666)
        args = ["pcb", "drc", "--refill-zones", "--severity-all", "--units", "mm", "--format", "json"]
        cli = os.environ.get("KICAD_CLI")
        if cli:
            cmd = [cli] + args + ["-o", os.path.join(tmp, "out.json"), os.path.join(proj, "board.kicad_pcb")]
        else:
            cmd = ["docker", "run", "--rm", "--user", "%d:%d" % (os.getuid(), os.getgid()), "-v", tmp + ":/w", "-w", "/w",
                   "-e", "HOME=/tmp", IMG, "kicad-cli"] + args + ["-o", "/w/out.json", "/w/PCB/board/board.kicad_pcb"]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if not os.path.exists(os.path.join(tmp, "out.json")):
            sys.exit("kicad-cli DRC failed:\n" + r.stdout + r.stderr)
        d = json.load(open(os.path.join(tmp, "out.json")))
        c = collections.Counter((v["severity"], v["type"]) for v in d.get("violations", []))
        return c, len(d.get("unconnected_items", []))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def fmt_counts(c):
    return ", ".join("%s %s x%d" % (k[0], k[1], n) for k, n in sorted(c.items())) or "none"


def drc_report(name, board, base, base_run):
    """DRC of one board against the committed base's: what is new. True when no new error and nothing unconnected."""
    c, unc = drc(board, base)
    new = {k: n - base_run[0].get(k, 0) for k, n in c.items() if n > base_run[0].get(k, 0)}
    print("    DRC %s: %d violations (%s), %d unconnected; new against the committed %s board: %s" % (
        name, sum(c.values()), fmt_counts(c), unc, base, fmt_counts(new)))
    return not any(k[0] == "error" for k in new) and unc == 0


# ============================================================================ a quick flat picture (not KiCad's render)
def preview(A, G, path, px=14):
    from PIL import Image, ImageDraw
    W, H = G["W"], G["H"]
    k = 2
    s = px * k
    im = Image.new("RGB", (int((W + 4) * s), int((H + 4) * s)), (18, 18, 20))
    d = ImageDraw.Draw(im)

    def T(p):
        return ((p[0] + 2) * s, (p[1] + 2) * s)

    d.rectangle([T((0, 0)), T((W, H))], fill=(28, 28, 30), outline=(90, 90, 90))
    for ref, c in G["ctrl"].items():
        r = 4.4 if ref == "SW1" else 4.0
        d.ellipse([T((c[0] - r, c[1] - r)), T((c[0] + r, c[1] + r))], fill=(70, 70, 80))
    for c in G["screws"]:
        d.ellipse([T((c[0] - 1.35, c[1] - 1.35)), T((c[0] + 1.35, c[1] + 1.35))], fill=(70, 70, 80))
    for ink, col in (("silk", (235, 235, 235)), ("gold", (240, 200, 60))):
        for x in A.items:
            if x["ink"] != ink:
                continue
            kd = x["kind"]
            if kd == "text":
                b = fa.text_box(x)
                d.rectangle([T((b[0], b[1])), T((b[2], b[3]))], outline=col, fill=col if x.get("knockout") else None)
                d.text(T((b[0] + 0.3, b[1] + 0.3)), x["s"], fill=(0, 0, 0) if x.get("knockout") else col)
            elif kd == "poly":
                d.polygon([T(p) for p in x["pts"]], fill=col)
            elif kd == "circle" and x["fill"]:
                c, r = x["c"], x["r"] + x["w"] / 2
                d.ellipse([T((c[0] - r, c[1] - r)), T((c[0] + r, c[1] + r))], fill=col)
            else:
                for a, b, w in fa.segments(x):
                    d.line([T(a), T(b)], fill=col, width=max(1, int(2 * w * s)))
                    for p in (a, b):
                        d.ellipse([T((p[0] - w, p[1] - w)), T((p[0] + w, p[1] + w))], fill=col)
    im = im.resize((im.size[0] // k, im.size[1] // k), Image.LANCZOS)
    im.save(path)


# ============================================================================ main
def main():
    ap = argparse.ArgumentParser(description="Gold-trace variations on TS06-FASCIA.")
    ap.add_argument("variant", nargs="?")
    ap.add_argument("out", nargs="?")
    ap.add_argument("--base", default="A", choices=sorted(fa.BASES))
    ap.add_argument("--base-pcb", default="", metavar="BOARD", help="read this board as the base (scratch copy of the same fascia) instead of the committed one")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--preview", default="", metavar="PNG", help="also write a quick flat picture")
    ap.add_argument("--drc", action="store_true", help="also run KiCad 10's DRC on each board and compare it with the base board's")
    a = ap.parse_args()
    if a.list or not a.variant:
        for k, v in DOCS.items():
            print("%-10s %s" % (k, v))
        return
    if a.base_pcb:
        if not os.path.isfile(a.base_pcb):
            sys.exit("--base-pcb %s: no such file" % a.base_pcb)
        fa.BASES[a.base] = os.path.abspath(a.base_pcb)
    todo = list(VARIANTS) if a.variant == "all" else [a.variant]
    failed = False
    base_run = drc(fa.BASES[a.base], a.base) if a.drc else None
    if a.drc:
        print("the committed %s board's own DRC: %d violations (%s), %d unconnected" % (
            a.base, sum(base_run[0].values()), fmt_counts(base_run[0]), base_run[1]))
    for v in todo:
        out = os.path.join(a.out, "%s-%s.kicad_pcb" % (v, a.base)) if a.variant == "all" else a.out
        if a.variant == "all":
            os.makedirs(a.out, exist_ok=True)
        A, G, problems, st, n, cir = build(v, a.base, out)
        ng = len(gold_items(A))
        print("%s on %s: %d gold items, %d silk items (Plates', unchanged), %d other board items identical to the base; %s" % (
            v, a.base, ng, len(A.items) - ng, n, "checks clean" if not problems else "%d problems:" % len(problems)))
        gg = ">1.0" if st["gold_gold"] > 1e8 else "%.2f" % st["gold_gold"]
        print("    margins (mm): gold-gold %s (need 0.30), gold-silk %.2f (0.30), edge %.2f (%.1f), screw %.2f (3.0), "
              "controls +%.2f beyond 6.0, dial +%.2f beyond 9.0" % (
                  gg, st["gold_silk"], st["edge"], EDGE_MM, st["screw"], st["ctrl"], st["dial"]))
        for p in problems:
            print("    " + p)
        failed |= bool(problems)
        if a.drc and out:
            failed |= not drc_report(v, out, a.base, base_run)
        if a.preview:
            preview(A, G, a.preview if a.variant != "all" else os.path.join(a.out, "%s-%s.png" % (v, a.base)))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
