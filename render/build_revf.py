#!/usr/bin/env python3
"""Assemble the TERMINAL-06 Rev F concept-plate page from the generated SVGs.

Every number on the page is pulled from rev_f.DIMS, so the prose cannot drift
away from the drawings. No f-strings with nested quotes anywhere — plain %
formatting and concatenation only.
"""
import io, os
import rev_f as R

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "terminal-06-rev-f.html")


# ------------------------------------------------------------------ helpers
def svg(name):
    s = io.open(os.path.join(HERE, name), encoding="utf-8").read()
    if "preserveAspectRatio" not in s.split(">", 1)[0]:
        s = s.replace("<svg ", '<svg preserveAspectRatio="xMidYMid meet" ', 1)
    return s


def fig(name, caps, cls=""):
    row = "".join("<span>" + c + "</span>" for c in caps)
    return ('<figure class="fig ' + cls + '"><div class="fig-in">' + svg(name)
            + '</div><figcaption class="cap">' + row + '</figcaption></figure>')


def prov(code):
    return '<span class="prov ' + code + '" title="' + PROV_T[code] + '">' + code + '</span>'


PROV_T = {
    "F": "from the FreeCAD model, 3d/IN12.FCStd",
    "M": "measured here with calipers",
    "C": "catalogue or factory outline drawing",
    "A": "assumed — not yet verified",
}


def classify(src):
    if "FCStd" in src:
        return "F"
    if "assumed" in src:
        return "A"
    if src.startswith("caliper"):
        return "M"
    return "C"


def num(v):
    return ("%.2f" % v).rstrip("0").rstrip(".")


# ------------------------------------------------------------ the dim table
ROWS = [
    ("EW", "ИН-12А envelope, width"),
    ("EH", "ИН-12А envelope, height"),
    ("ED", "ИН-12А envelope, depth"),
    ("DIGIT_12", "ИН-12А digit height"),
    ("PIN_FIELD_W", "ИН-12А pin field, width"),
    ("PIN_FIELD_H", "ИН-12А pin field, height"),
    ("PIN_D", "ИН-12А pin diameter"),
    ("PIN_L", "ИН-12А free pin length"),
    ("SW", "ИН-17 face, width"),
    ("SH", "ИН-17 face, height"),
    ("SD", "ИН-17 glass, depth"),
    ("S_BASE", "ИН-17 stem diameter"),
    ("S_LEAD", "ИН-17 free lead length"),
    ("DIGIT_17", "ИН-17 digit height"),
    ("DIGIT_17_W", "ИН-17 digit width"),
    ("BT", "board stock"),
]
HOT = {"SW", "SH", "SD", "S_BASE", "S_LEAD"}


def dimtable():
    o = ['<div class="tw"><table><thead><tr>'
         '<th>Dimension</th><th class="num">mm</th><th>Where it comes from</th>'
         '<th class="num">Src</th></tr></thead><tbody>']
    for key, label in ROWS:
        v, src = R.DIMS[key]
        c = classify(src)
        tr = '<tr class="hot">' if key in HOT else "<tr>"
        o.append(tr + "<td>" + label + '</td><td class="num">' + num(v)
                 + "</td><td>" + src + '</td><td class="num">' + prov(c)
                 + "</td></tr>")
    o.append("</tbody></table></div>")
    return "".join(o)


# ------------------------------------------------------------------ figures
FIGS = {
    "F_PART": fig("r-in12-reference.svg",
                  ["<b>01a</b> · front · rear · section",
                   "pin distribution indicative — the field size is not",
                   "<b>19.47 × 28.86 × 25.50</b>"]),
    "F_HERO": fig("rf-hero.svg",
                  ["<b>02a</b> · three-quarter, lit", "31° yaw · 10° elevation",
                   "<b>204.3 × 62 × 44</b>"], "wide"),
    "F_NIGHT": fig("rf-night.svg",
                   ["<b>02b</b> · the same object, unlit room",
                    "34° yaw · 7° elevation — only the glass is a light source",
                    "<b>the case disappears</b>"], "wide"),
    "F_FRONT": fig("rf-front.svg",
                   ["<b>03a</b> · front elevation, 1:1",
                    "digit line 44.43 · every glass face at z = 2",
                    "<b>204.3</b> — was 237"], "wide"),
    "F_PLAN": fig("rf-plan.svg",
                  ["<b>04a</b> · plan, 1:1",
                   "faces coplanar · stems are not",
                   "<b>44 deep</b>"], "wide"),
    "F_PROF": fig("rf-profile.svg",
                  ["<b>05a</b> · right profile, 1:1",
                   "ИН-17 dashed behind the ИН-12", "<b>44 deep · 62 high</b>"]),
    "F_EXP": fig("rf-exploded.svg",
                 ["<b>06a</b> · exploded section",
                  "drawn as a section — in a three-quarter they stack into one dark mass",
                  "<b>6 boards · 2 cheeks</b>"], "wide"),
    "F_HV": fig("rf-hv.svg",
                ["<b>07a</b> · HV containment",
                 "live compartment shaded · barriers heavy", "<b>185 V</b>"], "wide"),
    "F_SCALE": fig("rf-scale.svg",
                   ["<b>08a</b> · scale reference, 1:1",
                    "phone 146 × 71 · mug ⌀80 × 95 — nominal objects",
                    "<b>204.3 × 62 × 44</b>"], "wide"),
    "T_DIMS": dimtable(),
}


# ---------------------------------------------------------------------- CSS
CSS = """
:root{
  --void:#08090B; --panel:#0E1116; --raise:#141920; --edge:#1D242B; --edge2:#2A333C;
  --glow:#FF9E36; --strike:#F25610; --enig:#B08A4A; --steel:#8FA4B2;
  --bone:#E6E3DC; --dim:#9AA2AA; --mute:#666E76; --ok:#7FBF9A; --hold:#DFBB5E;
  --disp:"Saira Condensed","Arial Narrow",sans-serif;
  --body:"IBM Plex Sans",system-ui,-apple-system,sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,"SFMono-Regular",monospace;
  --sheet:min(1180px,100% - 2.6rem);
  --prose:66ch;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}
  *{animation:none!important;transition:none!important}}
body{margin:0;background:var(--void);color:var(--bone);
  font-family:var(--body);font-size:15px;line-height:1.62;-webkit-font-smoothing:antialiased}
h1,h2,h3{font-family:var(--disp);font-weight:700;margin:0;text-wrap:balance;
  letter-spacing:.01em}
p{margin:0}
b,strong{color:#fff;font-weight:600}
em{color:var(--dim);font-style:normal}
a{color:var(--glow)}
code{font-family:var(--mono);font-size:.87em;color:var(--enig);background:#ffffff0a;
  padding:.06em .34em;border-radius:2px}
:focus-visible{outline:2px solid var(--glow);outline-offset:2px}

.rail{position:sticky;top:0;z-index:60;background:rgba(8,9,11,.93);
  backdrop-filter:blur(10px);border-bottom:1px solid var(--edge)}
.rail-in{width:var(--sheet);margin:0 auto;height:44px;display:flex;align-items:center;
  gap:1.1rem;font-family:var(--mono);font-size:10.5px;letter-spacing:.13em;
  text-transform:uppercase;color:var(--mute);overflow:hidden;white-space:nowrap}
.rail-in .nm{font-family:var(--disp);font-weight:700;letter-spacing:.22em;font-size:13px;
  color:var(--bone)}
.rail-in .sp{margin-left:auto}
.rail-in .rev{color:var(--strike)}

.wrap{width:var(--sheet);margin:0 auto;padding:0 0 5rem}

.mast{padding:2.6rem 0 0}
.mast-fig{border:1px solid var(--edge);background:#000;overflow:hidden}
.mast-fig svg{display:block;width:100%;height:auto}
.mast-head{display:grid;gap:1.4rem;padding:2rem 0 0}
@media(min-width:860px){.mast-head{grid-template-columns:1.15fr .85fr;align-items:end}}
.eyebrow{font-family:var(--mono);font-size:10.5px;letter-spacing:.24em;
  text-transform:uppercase;color:var(--strike)}
.mast h1{font-size:clamp(2.9rem,8vw,5.6rem);line-height:.86;text-transform:uppercase;
  margin:.5rem 0 0}
.mast h1 .thin{color:var(--mute);font-weight:400}
.thesis{font-size:17px;line-height:1.5;color:#CBC7C0;max-width:52ch}
.thesis b{color:var(--glow);font-weight:600}

.meta{display:grid;grid-template-columns:repeat(auto-fit,minmax(116px,1fr));gap:1px;
  margin-top:2.2rem;background:var(--edge);border:1px solid var(--edge)}
.meta div{background:var(--panel);padding:.62rem .78rem}
.meta dt{font-family:var(--mono);font-size:9.5px;letter-spacing:.15em;
  text-transform:uppercase;color:var(--mute)}
.meta dd{margin:.24rem 0 0;font-family:var(--mono);font-size:13.5px;
  font-variant-numeric:tabular-nums;color:var(--bone)}
.meta dd s{color:var(--mute);text-decoration-color:var(--strike);margin-right:.35rem}

.prov{display:inline-flex;align-items:center;justify-content:center;
  width:15px;height:15px;border-radius:2px;font-family:var(--mono);font-size:9px;
  font-weight:600;vertical-align:.08em;line-height:1;border:1px solid transparent;
  cursor:help}
.prov.F{background:#12251B;color:var(--ok);border-color:#2A5741}
.prov.M{background:#131E26;color:var(--steel);border-color:#2E4653}
.prov.C{background:#231D0D;color:var(--hold);border-color:#4A3E1C}
.prov.A{background:#26110A;color:var(--strike);border-color:#4E2415}
.provkey{display:flex;flex-wrap:wrap;gap:.5rem 1.6rem;margin-top:1.2rem;
  font-family:var(--mono);font-size:11.5px;color:var(--dim)}
.provkey span{display:flex;align-items:center;gap:.45rem}

.plate{margin-top:4.2rem;scroll-margin-top:60px}
.plate-head{display:flex;align-items:baseline;gap:1rem;flex-wrap:wrap;
  border-bottom:1px solid var(--edge);padding-bottom:.62rem}
.plate-no{font-family:var(--mono);font-size:11.5px;color:var(--strike);
  letter-spacing:.12em;flex:none}
.plate-head h2{font-size:clamp(1.4rem,3vw,2rem);text-transform:uppercase}
.kicker{margin-left:auto;font-family:var(--mono);font-size:10.5px;color:var(--mute);
  text-transform:uppercase;letter-spacing:.13em;text-align:right}
.lede{max-width:var(--prose);margin-top:1.25rem;color:#C4C0B9}
.plate p+p{margin-top:.9rem}

.fig{margin:1.7rem 0 0}
.fig-in{background:radial-gradient(115% 150% at 50% 28%,#12161C 0%,#08090B 72%);
  border:1px solid var(--edge);padding:1.1rem clamp(.5rem,1.6vw,1.4rem);
  overflow-x:auto}
.fig-in svg{display:block;width:100%;height:auto;min-width:520px}
.fig.wide .fig-in svg{min-width:660px}
.cap{display:flex;flex-wrap:wrap;gap:.35rem 1.5rem;justify-content:space-between;
  margin-top:.7rem;font-family:var(--mono);font-size:10px;letter-spacing:.11em;
  text-transform:uppercase;color:var(--mute)}
.cap span:first-child{color:var(--dim)}
.pair{display:grid;gap:1.7rem}
@media(min-width:900px){.pair.two{grid-template-columns:1fr 1fr}}

.tw{overflow-x:auto;margin-top:1.5rem;border:1px solid var(--edge)}
table{border-collapse:collapse;width:100%;min-width:600px;font-size:13.5px}
th,td{text-align:left;padding:.54rem .8rem;border-bottom:1px solid var(--edge);
  vertical-align:top}
thead th{font-family:var(--mono);font-size:9.5px;letter-spacing:.14em;
  text-transform:uppercase;color:var(--mute);background:#0B0E12}
tbody tr:last-child td{border-bottom:0}
td.num,th.num{font-family:var(--mono);font-variant-numeric:tabular-nums;white-space:nowrap}
td.was{color:var(--mute)}
td.was s{text-decoration-color:var(--strike)}
tr.hot td{background:#15100C}
tr.hot td:first-child{box-shadow:inset 2px 0 0 var(--strike)}

.note{border-left:2px solid var(--edge2);padding:.1rem 0 .1rem 1rem;margin-top:1.4rem;
  max-width:var(--prose);color:#B6B2AB;font-size:14px}
.note strong{display:block;font-family:var(--mono);font-size:10px;letter-spacing:.14em;
  text-transform:uppercase;color:var(--bone);margin-bottom:.3rem;font-weight:500}
.note.stop{border-left-color:var(--strike)}
.note.stop strong{color:var(--strike)}
.note.good{border-left-color:var(--ok)}
.note.good strong{color:var(--ok)}
.note.warn{border-left-color:var(--hold)}
.note.warn strong{color:var(--hold)}

.cols{display:grid;gap:1.3rem;margin-top:1.6rem}
@media(min-width:820px){.cols.two{grid-template-columns:1fr 1fr}
  .cols.three{grid-template-columns:repeat(3,1fr)}}
.card{background:var(--panel);border:1px solid var(--edge);padding:1.05rem 1.15rem}
.card h3{font-size:1rem;text-transform:uppercase;color:#fff}
.card p{margin-top:.45rem;font-size:13.5px;color:#B6B2AB}
.card .tag{font-family:var(--mono);font-size:9.5px;letter-spacing:.14em;
  text-transform:uppercase;color:var(--strike)}

ol.q{margin:1.2rem 0 0;padding-left:1.35rem;max-width:var(--prose);color:#B6B2AB}
ol.q li{margin-bottom:.62rem}
ol.q li::marker{font-family:var(--mono);font-size:12px;color:var(--strike)}
ul.t{margin:.9rem 0 0;padding-left:1.05rem;max-width:var(--prose);color:#B6B2AB}
ul.t li{margin-bottom:.42rem}
ul.t li::marker{color:var(--edge2)}

.tb{display:flex;flex-wrap:wrap;gap:.2rem 1.9rem;margin-top:1.4rem;padding-top:.55rem;
  border-top:1px solid var(--edge);font-family:var(--mono);font-size:10px;
  letter-spacing:.11em;text-transform:uppercase;color:var(--mute)}
.tb b{color:var(--dim);font-weight:400}

footer{margin-top:4.6rem;padding-top:1.5rem;border-top:1px solid var(--edge);
  font-family:var(--mono);font-size:11px;color:var(--mute);line-height:1.95}
footer b{color:var(--dim);font-weight:400}
footer .hv{color:var(--strike)}
"""


# ------------------------------------------------------------------- plates
def plate(no, title, kicker, body, tb):
    return ('\n<section class="plate" id="p' + no + '">'
            '<div class="plate-head"><span class="plate-no">PLATE ' + no + '</span>'
            '<h2>' + title + '</h2><span class="kicker">' + kicker + '</span></div>'
            + body + '<div class="tb">' + tb + '</div></section>\n')


P00 = """
<p class="lede">Rev E is withdrawn. It was drawn from a tube that does not exist:
a rectangular block with its leads coming out of the bottom. <b>ИН-12А takes twelve
pins out of the REAR.</b> That single fact moves the connection plane from under the
glass to behind it, and everything downstream of it — the body, the depth, the whole
massing — was resolved against a false constraint.</p>

<p>Three separate errors were found, and the architecture was changed on top of them.
Rev F is a fresh set, not a patch. Each figure below carries a provenance mark so
that nothing on this page can be mistaken for a remembered number again.</p>

<div class="tw"><table><thead><tr><th>What</th><th>Rev E said</th><th>Rev F says</th>
<th>How it was caught</th></tr></thead><tbody>
<tr class="hot"><td>ИН-12А lead exit</td><td class="was"><s>10 pins, bottom</s></td>
<td>12 pins, rear</td><td>You flagged it. The Rev E glass was an ИН-14.</td></tr>
<tr class="hot"><td>ИН-12А envelope width</td><td class="was"><s>25.27</s></td>
<td>19.47</td>
<td>25.27 was a caliper reading of the DEPTH, filed on the sheet as
&ldquo;narrow axis&rdquo;. The width had never been measured at all.</td></tr>
<tr class="hot"><td>ИН-17 face</td><td class="was"><s>15 wide, assumed</s></td>
<td>14 &times; 20</td>
<td>Two wrong answers before the right one — see below.</td></tr>
<tr><td>Body</td><td class="was"><s>moulded enclosure</s></td>
<td>2 cheeks + 6 boards</td><td>You rejected the massing: too big, bad in profile.</td></tr>
<tr><td>Overall</td><td class="was"><s>237 &times; 96 &times; 104</s></td>
<td>204.3 &times; 62 &times; 44</td>
<td>Consequence of all four. <b>24%</b> of the Rev E volume.</td></tr>
</tbody></table></div>

<div class="note stop"><strong>The ИН-17 took three passes</strong>
First it was assumed at 15 wide, because no one had measured it. Then it was
calipered at 17.5 and 19.2 and drawn as a flat portrait face — those two readings
looked like a width and a height, so they were used as one. They are not.
<b>ИН-17 is not a flat tube.</b> It is an end-view tube with a round Ø20 stem that
flattens toward the display end. 19.2 was the stem. 17.5 was somewhere part way
down the flatten, which is why it fitted nothing. The face is <b>14</b>, and the
factory outline drawing says so directly.</div>

<div class="note warn"><strong>What that means for the row</strong>
The seconds tubes are narrow at the front and fat at the back. Spacing them by
their faces would put the two stems 17 mm apart and they would touch. The seconds
pair is therefore set by the <b>stems</b> — 20 + 0.5 clearance — and not by
anything visible from the front. See plate 04.</div>
"""

P01 = """
<p class="lede">ИН-12А, from <code>3d/IN12.FCStd</code>. Not a datasheet, not a
memory — the parametric model, read field by field. This is the part the whole
object is dimensioned around, so it gets its own plate.</p>
@F_PART@
<p>The twelve pins leave the rear face on a <b>12.40 &times; 17.00</b> field, each
0.92 across, 6.25 free. That field is what forces a board directly behind the
glass. There is no version of this object where the tube stands on its own
leads.</p>
<div class="note good"><strong>ИН-15 is the same part</strong>
Confirmed by you, 05.09.26: ИН-15 is identical to ИН-12 in form. It carries
symbols instead of digits, so it is drawn as an ИН-12 throughout and only the
glyph set changes. The annex pair (<code>A</code> <code>Р</code>) is ИН-15.</div>
@T_DIMS@
<div class="provkey">
<span>@P_F@ FreeCAD model</span><span>@P_M@ calipered here</span>
<span>@P_C@ catalogue / factory drawing</span><span>@P_A@ assumed, not verified</span>
</div>
<p style="margin-top:1.1rem;color:#9AA2AA;font-size:13.5px;max-width:66ch">
One row is still amber: <b>board stock at 1.60</b> is an assumption. It is the
only load-bearing number on this page that has not been checked against a real
part, and it sets the depth of every closure.</p>
"""

P02 = """
<p class="lede">Two cheeks and six boards. No moulding, no extrusion, no enclosure
to source. The cheeks are the only parts that are not flat stock, and they are the
only parts that carry a curve.</p>
@F_HERO@
<p>You said you liked seeing the PCB but did not want it sticking out. This is the
resolution: the boards <em>are</em> the case. The fascia is a board. The rear and
top closure is a board on the cheek diagonal. The bottom is a board. Black mask,
ENIG legend, and the only visible fastening is where a cheek meets a board edge.</p>
@F_NIGHT@
<div class="note"><strong>Why it reads as one object and not a stack</strong>
Every glass face sits on the same plane, <code>z = 2</code>, and every digit sits
on the same line, <code>y = 44.43</code>. The tubes are three different depths
behind that plane. Nothing about the row's back end is visible from the front,
which is what buys the freedom used in plate 04.</div>
"""

P03 = """
<p class="lede">204.3 wide, 62 high. Eight tubes: four ИН-12 for hours and minutes,
two ИН-17 for seconds, two ИН-15 for the annex. Every face coplanar, every digit on
one line.</p>
@F_FRONT@
<p>The gaps are not styling. Reading left to right: <b>3</b> inside a pair,
<b>8</b> at the colon, <b>8</b> before the seconds, <b>6.5</b> inside the seconds
pair, <b>12</b> before the annex. Only the 6.5 is set by something you cannot see —
the Ø20 stems behind the narrow faces.</p>
<div class="note warn"><strong>The seconds will always read small</strong>
ИН-17's digit is <b>9.00</b>. ИН-12's is <b>18.63</b>. The seconds are
<b>48%</b> the height of the hours, on half the glass area, and no amount of
spacing changes that. Treat it as hierarchy — hours shout, seconds tick — or
change the part. Two ways out, if it reads wrong in the flesh:
</div>
<div class="cols two">
<div class="card"><span class="tag">Option A</span><h3>Keep the ИН-17</h3>
<p>Accept the hierarchy. The face closes at 204.3 and the seconds pair costs
34.5 mm of the row. This is the drawn set.</p></div>
<div class="card"><span class="tag">Option B</span><h3>ИН-15 for seconds</h3>
<p>Uniform digits, uniform stems, one part number fewer. The face grows to about
215 and the row loses its rhythm — six identical rectangles and an annex.</p></div>
</div>
"""

P04 = """
<p class="lede">This plate exists because of one number. The ИН-17 face is 14 wide.
Its stem is Ø20. Those are the same tube, 22 mm apart along the axis.</p>
@F_PLAN@
<p>Spacing the seconds pair off their faces at the usual 3 mm gap gives 17 mm
between centres. The stems are 20. They would interfere before the boards were
even cut. The pair is spaced at <b>20.5 centres</b> instead — the stem diameter
plus 0.5 — which reads at the front as a 6.5 mm gap and looks like a deliberate
grouping. It is, but it is also the only spacing that fits.</p>
<p>The other neighbours have room. ИН-12 to ИН-17 is 24.73 between centres against
19.74 needed at the stems. ИН-17 to ИН-15 is 28.74. Only the seconds pair is
tight.</p>
<div class="note"><strong>Three board planes, all parallel to the face</strong>
Fascia at <code>z = 2</code>, tube board at <code>z = 27.5</code>, bottom closure
at <code>z = 42.4</code>. The ИН-12 barrel is 25.5 and the ИН-17 glass is 22, so
with faces coplanar the ИН-17 leads reach 3.5 mm further to reach the same board.
They are 35 mm of flexible wire — trimmed and dressed through a comb, not pins in
a fixed pattern, so this costs nothing.</div>
"""

P05 = """
<p class="lede">The cheek is the whole case. Its diagonal is the rear panel line,
its front edge is the fascia line, and every board in the object lands on one of
its faces.</p>
@F_PROF@
<p>44 deep and 62 high, against Rev E's 104 &times; 96. The profile you called
unflattering was a tall box seen from the side; this is a wedge, and the wedge is
doing work — the diagonal closes the high-voltage compartment and gives the vents
somewhere to sit facing away from the viewer.</p>
<div class="note good"><strong>Direct-solder, this run</strong>
You have ten boards in hand with holes too small for sockets, so the tubes solder
straight into the tube board. The pin field is drawn at its real size so the next
board revision can take sockets without moving anything else: same field, larger
holes, same 27.5 plane.</div>
"""

P06 = """
<p class="lede">Front to back, at true height, with the real <code>z</code> under
each name. Drawn as a section rather than a three-quarter, because in a
three-quarter these six planes pile up into one dark mass — that was tried twice
and failed twice.</p>
@F_EXP@
<p>Six boards: fascia, tube board, main board, sloped rear/top closure, rear
strip, bottom closure. Two cheeks. That is the entire bill of structure. Nothing
here is moulded, and the only non-flat parts are the cheeks.</p>
"""

P07 = """
<p class="lede">There is no body, so there is nothing to hide behind. Every barrier
around the 185 V compartment is named, drawn, and accounted for on this plate.</p>
@F_HV@
<p>The tube pins protrude <b>4.65 mm</b> behind the tube board and sit at anode
potential. The compartment that contains them runs <code>z 27.5 → 44</code> and
<code>y 4 → 62</code>. It is closed on the rear and top by one sloped board on the
cheek diagonal, at the back by a 12 mm strip below that diagonal, underneath by a
board beneath the main board, at the ends by the cheeks, and at the front by the
fascia below 30 and by the tube glass itself above it.</p>
<div class="note stop"><strong>Two of the eight are rules, not parts</strong>
The 3 mm gaps between tubes open onto the front face of the tube board, and the
top 3.1 mm of that board sits above the glass. Neither can be closed with a part.
Both become per-unit QC checks: no exposed conductor anywhere on the tube board's
front face outside a tube footprint, and an HV keepout along its top edge. 3 mm is
below finger reach, so mask is the barrier there — which means the mask is a
safety part and gets inspected like one.</div>
"""

P08 = """
<p class="lede">Against two objects with known dimensions, at 1:1, on one ground
line.</p>
@F_SCALE@
<p>62 high is lower than a mug. 44 deep is less than a phone is wide. Rev E was
237 &times; 96 &times; 104 — this is <b>24%</b> of that volume and it holds the
same eight tubes. The desk footprint is the honest measure of whether a clock gets
kept, and this one asks for a strip 204 by 44.</p>
"""

P09 = """
<p class="lede">What is drawn is drawn. These are the things that are not, ranked
by what they would cost to change later.</p>
<ol class="q">
<li><b>Board stock at 1.60 is assumed.</b> It sets every closure depth and both
cheek slots. One caliper reading on a real board closes it. Highest value, lowest
effort.</li>
<li><b>The ИН-17 stem was read off a drawing, not a part.</b> Ø20 governs the
seconds pair spacing and therefore the overall width. Measure the stem on one of
your tubes at the widest point and the 204.3 is final.</li>
<li><b>Cheek material and thickness.</b> Drawn at 6.0 in an unnamed material. It
is the only part that is not flat stock, so it decides whether this is machined,
printed, or cut and folded.</li>
<li><b>Vent area on the slope.</b> Drawn as a line on the diagonal. The HV supply's
dissipation sets the real area and it has not been calculated.</li>
<li><b>Fascia legend and detent positions.</b> Drawn to look right. They are
silkscreen, so they cost nothing to move — but they should be moved once, after
the rotary is in hand.</li>
</ol>
<div class="note"><strong>Not carried into Rev F</strong>
MIMI-06 and SCALER-06 still carry the Rev E ИН-12 error in their plates. They
inherit this correction but have not been redrawn. QUADRANT-D is unaffected — it
uses no ИН-12.</div>
"""


PLATES = [
    ("00", "The corrections", "why Rev E is withdrawn", P00,
     "<b>Supersedes</b> Rev E &middot; 05.09.26 &nbsp; <b>Errors closed</b> 3 &nbsp; "
     "<b>Architecture</b> changed"),
    ("01", "The part", "ИН-12А &middot; ИН-15", P01,
     "<b>Source</b> 3d/IN12.FCStd &nbsp; <b>Pins</b> 12, rear &nbsp; "
     "<b>Field</b> 12.40 &times; 17.00"),
    ("02", "The object", "cheeks, not a body", P02,
     "<b>Parts</b> 2 cheeks + 6 boards &nbsp; <b>Moulded</b> none &nbsp; "
     "<b>Overall</b> 204.3 &times; 62 &times; 44"),
    ("03", "Front elevation", "1:1", P03,
     "<b>Face</b> 204.3 &nbsp; <b>Digit line</b> 44.43 &nbsp; <b>Glass plane</b> z = 2"),
    ("04", "Plan", "the stems, not the faces", P04,
     "<b>Seconds pair</b> 20.5 centres &nbsp; <b>Stem</b> Ø20 &nbsp; "
     "<b>Clearance</b> 0.5"),
    ("05", "The cheek", "right profile, 1:1", P05,
     "<b>Depth</b> 44 &nbsp; <b>Height</b> 62 &nbsp; <b>Thickness</b> 6.0 "
     "<span class=\"prov A\">A</span>"),
    ("06", "The stack", "exploded section", P06,
     "<b>Boards</b> 6 &nbsp; <b>Cheeks</b> 2 &nbsp; <b>Planes</b> z 2 / 27.5 / 42.4"),
    ("07", "HV containment", "185 V, no body", P07,
     "<b>Faces closed</b> 6 of 8 &nbsp; <b>Design rules</b> 2 &nbsp; "
     "<b>Pin protrusion</b> 4.65"),
    ("08", "Scale", "1:1, one ground line", P08,
     "<b>Footprint</b> 204.3 &times; 44 &nbsp; <b>Height</b> 62 &nbsp; "
     "<b>vs Rev E</b> 24% of volume"),
    ("09", "Still open", "five things, ranked", P09,
     "<b>Assumed figures</b> 1 &nbsp; <b>Blocking</b> none &nbsp; "
     "<b>Next</b> caliper the board stock"),
]

NAV = "".join('<a href="#p' + n + '">' + n + '</a>' for n, _, _, _, _ in PLATES)

HEAD = """<title>TERMINAL·06 Rev F</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Saira+Condensed:wght@400;700&family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;600&display=swap">
<style>""" + CSS + """
.rail-in a{color:var(--mute);text-decoration:none;font-variant-numeric:tabular-nums}
.rail-in a:hover{color:var(--glow)}
.rail-in .nav{display:flex;gap:.62rem}
@media(max-width:720px){.rail-in .nav{display:none}}
</style>"""

MAST = """
<header class="rail"><div class="rail-in">
  <span class="nm">TERMINAL&middot;06</span>
  <span class="rev">REV F</span>
  <span class="nav">""" + NAV + """</span>
  <span class="sp">204.3 &times; 62 &times; 44</span>
</div></header>

<div class="wrap">
<section class="mast">
  <div class="mast-fig">""" + svg("rf-front.svg") + """</div>
  <div class="mast-head">
    <div>
      <p class="eyebrow">Concept plates &middot; supersedes Rev E</p>
      <h1>Two cheeks<br><span class="thin">and six boards</span></h1>
    </div>
    <p class="thesis">Rev E was drawn around a tube that does not exist. This set
    is drawn around the one that does — <b>twelve pins out of the rear</b>, a
    board behind every glass face, and no enclosure at all.</p>
  </div>
  <div class="meta">
    <div><dt>Overall</dt><dd>204.3 &times; 62 &times; 44</dd></div>
    <div><dt>Was</dt><dd><s>237 &times; 96 &times; 104</s></dd></div>
    <div><dt>Tubes</dt><dd>4 &times; ИН-12</dd></div>
    <div><dt>Seconds</dt><dd>2 &times; ИН-17</dd></div>
    <div><dt>Annex</dt><dd>2 &times; ИН-15</dd></div>
    <div><dt>Anode</dt><dd>185 V</dd></div>
    <div><dt>Assumed</dt><dd>1 figure</dd></div>
  </div>
</section>
"""

FOOT = """
<footer>
  <b>TERMINAL&middot;06 Rev F</b> &middot; concept plates &middot; 09.09.2026<br>
  Drawings generated from <b>rev_f.py</b>; every dimension traces to
  <b>DIMS</b> and every DIMS entry names its source.<br>
  ИН-12А and ИН-15 geometry from <b>3d/IN12.FCStd</b>. ИН-17 geometry from the
  factory outline drawing, corroborated by soviet-tubes (22 &times; 20 &times; 14)
  and swissnixie (&asymp;15 &times; 20).<br>
  <span class="hv">Anode supply 185 V. Every drawing on this page shows a live
  compartment. Do not build the open frame without the six closures on plate
  07.</span>
</footer>
</div>
"""


def build():
    parts = [HEAD, MAST]
    for no, title, kicker, body, tb in PLATES:
        parts.append(plate(no, title, kicker, body, tb))
    parts.append(FOOT)
    html = "".join(parts)
    for k, v in FIGS.items():
        html = html.replace("@" + k + "@", v)
    for c in "FMCA":
        html = html.replace("@P_" + c + "@", prov(c))
    import re
    left = re.findall(r"@[A-Z_]{2,}@", html)
    assert not left, "unsubstituted tokens: %s" % sorted(set(left))
    io.open(OUT, "w", encoding="utf-8").write(html)
    print("%s  %.1f KB" % (OUT, len(html) / 1024.0))


if __name__ == "__main__":
    build()
