#!/usr/bin/env python3
"""Shared render primitives for the -06 family.

Everything is authored in millimetres. The two renderers (orthographic face,
axonometric hero) both place content through a transform string, so a tube face
is drawn exactly once and reused in both.

Cathode glyphs are hand-authored WIRE paths — a nixie cathode is a bent wire, so
it is stroked with round caps and joins, never filled. That single decision is
most of what makes a drawn nixie read as a nixie.
"""
import math

# ---------------------------------------------------------------- wire glyphs
# Authored in a 12 wide x 18 tall box, y DOWN (SVG native).
GLYPH = {
"0": "M6 1.3C9.3 1.3 10.7 4.1 10.7 9S9.3 16.7 6 16.7 1.3 13.9 1.3 9 2.7 1.3 6 1.3Z",
"1": "M2.5 4.4 6 1.3 6 16.7",
"2": "M1.7 4.8C1.7 2.3 3.6 1.3 6 1.3 8.6 1.3 10.6 2.7 10.6 5.3 10.6 8.5 7.1 10.6 1.5 16.7L10.8 16.7",
"3": "M1.9 3.1C3.1 1.7 4.7 1.3 6.3 1.3 8.9 1.3 10.6 2.7 10.6 5.1 10.6 7.3 9 8.7 6.6 8.9 9.4 9 11 10.5 11 12.9 11 15.5 8.8 16.7 6.2 16.7 4.2 16.7 2.4 15.9 1.6 14.5",
"4": "M8.7 16.7 8.7 1.3 1.1 12.5 11 12.5",
"5": "M10 1.3 3.3 1.3 2.5 8.1C3.5 7.1 4.9 6.7 6.3 6.7 9.1 6.7 11 8.5 11 11.7 11 15 8.8 16.7 6 16.7 3.8 16.7 2.3 15.9 1.5 14.5",
"6": "M9.6 1.7C8.6 1.4 7.6 1.3 6.6 1.3 3.4 1.3 1.4 4.1 1.4 9.7 1.4 14.7 3.4 16.7 6.2 16.7 8.8 16.7 10.7 15 10.7 12.1 10.7 9.3 8.8 7.5 6.2 7.5 3.8 7.5 1.9 8.9 1.6 11.3",
"7": "M1.5 1.3 10.8 1.3 4.7 16.7",
"8": "M6 8.7C3.5 8.7 1.7 7.1 1.7 4.9 1.7 2.7 3.5 1.3 6 1.3 8.5 1.3 10.3 2.7 10.3 4.9 10.3 7.1 8.5 8.7 6 8.7 3.3 8.7 1.3 10.4 1.3 13 1.3 15.4 3.3 16.7 6 16.7 8.7 16.7 10.7 15.4 10.7 13 10.7 10.4 8.7 8.7 6 8.7Z",
"9": "M2.5 16.3C3.5 16.6 4.5 16.7 5.5 16.7 8.7 16.7 10.6 13.9 10.6 8.3 10.6 3.3 8.7 1.3 5.9 1.3 3.3 1.3 1.4 3 1.4 5.9 1.4 8.7 3.3 10.5 5.9 10.5 8.3 10.5 10.2 9.1 10.5 6.7",
# symbol-tube glyphs
"A": "M1.3 16.7 6 1.3 10.7 16.7M3.1 11.7 8.9 11.7",
"P": "M2.6 16.7 2.6 1.3 7 1.3C9.6 1.3 11 2.9 11 5.5 11 8.1 9.6 9.7 7 9.7L2.6 9.7",
"K": "M2.4 1.3 2.4 16.7M10.4 1.3 3.2 9.2 10.8 16.7",
"M": "M1.4 16.7 1.4 1.3 6 9.5 10.6 1.3 10.6 16.7",
"H": "M1.8 1.3 1.8 16.7M10.2 1.3 10.2 16.7M1.8 9 10.2 9",
"V": "M1.4 1.3 6 16.7 10.6 1.3",
"W": "M0.8 1.3 3.2 16.7 6 6.5 8.8 16.7 11.2 1.3",
"S": "M10.2 3.2C9.2 1.9 7.7 1.3 6 1.3 3.5 1.3 1.8 2.6 1.8 4.7 1.8 9.3 10.4 7.3 10.4 12.6 10.4 15.2 8.4 16.7 5.9 16.7 4 16.7 2.4 16 1.4 14.6",
"F": "M2.4 16.7 2.4 1.3 10.4 1.3M2.4 8.8 8.8 8.8",
"n": "M2.2 16.7 2.2 6.2M2.2 9.2C3 7.1 4.6 6 6.5 6 8.7 6 9.8 7.4 9.8 9.6L9.8 16.7",
"m": "M1 16.7 1 6.2M1 9.2C1.6 7.2 2.8 6 4.3 6 5.9 6 6.6 7.2 6.6 9.2L6.6 16.7M6.6 9.2C7.2 7.2 8.4 6 9.9 6 11.4 6 12 7.2 12 9.2L12 16.7",
"u": "M2.2 6.2 2.2 12.6C2.2 15.3 3.4 16.7 5.5 16.7 7.4 16.7 9 15.6 9.8 13.5M9.8 6.2 9.8 16.7M2.2 6.2 2.2 3.0",
"O": "M6 1.3C9.3 1.3 10.7 4.1 10.7 9S9.3 16.7 6 16.7 1.3 13.9 1.3 9 2.7 1.3 6 1.3Z",
"-": "M2 9 10 9",
"+": "M6 3.5 6 14.5M1.4 9 10.6 9",
"%": "M1.6 1.6 10.4 16.4M3.2 1.3A1.9 1.9 0 1 1 3.19 1.3ZM8.8 16.7A1.9 1.9 0 1 1 8.79 16.7Z",
# Cyrillic cathodes on the IN-15A symbol tube. These are NOT the Latin
# lookalikes - "P" here is U+0420, and without its own entry glyph_path()
# silently falls through to the "8" default, which is very hard to spot in
# a render because an 8 is a plausible thing for a nixie to be showing.
"\u0420": "M2.6 16.7 2.6 1.3 7 1.3C9.6 1.3 11 2.9 11 5.5 11 8.1 9.6 9.7 7 9.7L2.6 9.7",
"\u041f": "M2.2 16.7 2.2 1.3 9.8 1.3 9.8 16.7",
}
GW, GH = 12.0, 18.0


def glyph_path(ch):
    return GLYPH.get(ch, GLYPH.get(ch.upper(), GLYPH["8"]))


# ---------------------------------------------------------------- defs blocks
def tube_defs(p, warm="#FF9E36", hot="#FFD9A8", deep="#FF5A08"):
    """Filters and gradients every tube render needs. `p` is a unique prefix."""
    return f'''
<linearGradient id="{p}-glass" x1="0" y1="0" x2=".35" y2="1">
  <stop offset="0"   stop-color="#b9d2e0" stop-opacity=".17"/>
  <stop offset=".28" stop-color="#7f9bad" stop-opacity=".07"/>
  <stop offset=".62" stop-color="#39505f" stop-opacity=".05"/>
  <stop offset="1"   stop-color="#8fb0c4" stop-opacity=".13"/>
</linearGradient>
<radialGradient id="{p}-cavity" cx=".5" cy=".62" r=".78">
  <stop offset="0"   stop-color="#241a12"/>
  <stop offset=".55" stop-color="#0e1116"/>
  <stop offset="1"   stop-color="#05070a"/>
</radialGradient>
<radialGradient id="{p}-halo" cx=".5" cy=".5" r=".5">
  <stop offset="0"   stop-color="{deep}" stop-opacity=".55"/>
  <stop offset=".45" stop-color="{deep}" stop-opacity=".20"/>
  <stop offset="1"   stop-color="{deep}" stop-opacity="0"/>
</radialGradient>
<linearGradient id="{p}-spec" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0"   stop-color="#ffffff" stop-opacity=".30"/>
  <stop offset=".45" stop-color="#ffffff" stop-opacity=".05"/>
  <stop offset="1"   stop-color="#ffffff" stop-opacity="0"/>
</linearGradient>
<pattern id="{p}-mesh" width="2.1" height="2.1" patternUnits="userSpaceOnUse">
  <path d="M0 0H2.1M0 0V2.1" stroke="#9fb4c4" stroke-width=".18" fill="none" opacity=".5"/>
</pattern>
<filter id="{p}-bigglow" x="-160%" y="-160%" width="420%" height="420%">
  <feGaussianBlur stdDeviation="2.6"/>
</filter>
<filter id="{p}-midglow" x="-120%" y="-120%" width="340%" height="340%">
  <feGaussianBlur stdDeviation="1.1"/>
</filter>
<filter id="{p}-softglow" x="-120%" y="-120%" width="340%" height="340%">
  <feGaussianBlur stdDeviation=".38"/>
</filter>
<filter id="{p}-blur3" x="-60%" y="-60%" width="220%" height="220%">
  <feGaussianBlur stdDeviation="3"/>
</filter>
<filter id="{p}-blur8" x="-60%" y="-60%" width="220%" height="220%">
  <feGaussianBlur stdDeviation="8"/>
</filter>
'''


# ---------------------------------------------------------------- a tube face
def tube_face(p, w, h, lit, ghosts=True, glyphset="0123456789",
              warm="#FF9E36", hot="#FFE0BC", deep="#FF6A12",
              digit_frac=.70, dim=1.0, socket=True, ghost_op=.085, spec_op=1.0,
              mesh_op=.42):
    """SVG for one tube, in LOCAL mm coords, origin at the glass top-left.

    Returns a fragment to be wrapped in <g transform="...">.
    """
    o = []
    r = min(w, h) * .07
    # --- glow pool behind the glass -------------------------------------
    if lit and dim > .02:
        o.append(f'<ellipse cx="{w/2:.2f}" cy="{h*.52:.2f}" rx="{w*.95:.2f}" ry="{h*.72:.2f}" '
                 f'fill="url(#{p}-halo)" opacity="{.85*dim:.2f}"/>')
    # --- envelope --------------------------------------------------------
    o.append(f'<rect x="0" y="0" width="{w:.2f}" height="{h:.2f}" rx="{r:.2f}" fill="url(#{p}-cavity)"/>')
    # anode mesh, inset
    o.append(f'<rect x="{w*.09:.2f}" y="{h*.07:.2f}" width="{w*.82:.2f}" height="{h*.80:.2f}" '
             f'fill="url(#{p}-mesh)" opacity="{mesh_op}"/>')

    # --- cathode stack ---------------------------------------------------
    dh = h * digit_frac
    sc = dh / GH
    dw = GW * sc
    x0 = (w - dw) / 2.0
    y0 = (h - dh) / 2.0 - h * .02
    sw = max(.42, sc * 1.15)

    if ghosts:
        o.append('<g stroke-linecap="round" stroke-linejoin="round" fill="none">')
        for i, ch in enumerate(glyphset):
            if ch == lit:
                continue
            dx = (i - len(glyphset) / 2.0) * sc * .30
            dy = (i - len(glyphset) / 2.0) * sc * .22
            o.append(f'<g transform="translate({x0+dx:.2f} {y0+dy:.2f}) scale({sc:.4f})">'
                     f'<path d="{glyph_path(ch)}" stroke="#8fa8bd" stroke-width="{1.05:.2f}" '
                     f'opacity="{ghost_op}"/></g>')
        o.append('</g>')

    # --- the lit cathode: three layers, hot core last --------------------
    if lit and dim > .02:
        d = glyph_path(lit)
        g = (f'<g transform="translate({x0:.2f} {y0:.2f}) scale({sc:.4f})" fill="none" '
             f'stroke-linecap="round" stroke-linejoin="round">')
        o.append(g)
        o.append(f'<path d="{d}" stroke="{deep}" stroke-width="3.4" opacity="{.85*dim:.2f}" filter="url(#{p}-bigglow)"/>')
        o.append(f'<path d="{d}" stroke="{warm}" stroke-width="2.0" opacity="{.95*dim:.2f}" filter="url(#{p}-midglow)"/>')
        o.append(f'<path d="{d}" stroke="{warm}" stroke-width="1.35" opacity="{dim:.2f}" filter="url(#{p}-softglow)"/>')
        o.append(f'<path d="{d}" stroke="{hot}" stroke-width=".62" opacity="{.92*dim:.2f}"/>')
        o.append('</g>')

    # --- glass over the top ---------------------------------------------
    o.append(f'<rect x="0" y="0" width="{w:.2f}" height="{h:.2f}" rx="{r:.2f}" fill="url(#{p}-glass)"/>')
    o.append(f'<rect x="{w*.06:.2f}" y="{h*.04:.2f}" width="{w*.22:.2f}" height="{h*.62:.2f}" '
             f'rx="{w*.09:.2f}" fill="url(#{p}-spec)" opacity="{spec_op}"/>')
    o.append(f'<rect x="0" y="0" width="{w:.2f}" height="{h:.2f}" rx="{r:.2f}" fill="none" '
             f'stroke="#9ab6c8" stroke-width=".34" opacity=".62"/>')
    if socket:
        o.append(f'<rect x="{w*.10:.2f}" y="{h-.5:.2f}" width="{w*.80:.2f}" height="1.5" rx=".4" '
                 f'fill="#181c21" stroke="#333c44" stroke-width=".2"/>')
    return "\n".join(o)


# ---------------------------------------------------------------- neon lamp
def neon_dot(p, cx, cy, r, on=True, deep="#FF5A08", warm="#FF8A28", dim=1.0):
    if not on or dim < .02:
        return (f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="#2a1d13" '
                f'stroke="#3d2c1d" stroke-width=".2"/>')
    return (f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r*2.9:.2f}" fill="{deep}" opacity="{.32*dim:.2f}" '
            f'filter="url(#{p}-bigglow)"/>'
            f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r*1.25:.2f}" fill="{warm}" opacity="{.9*dim:.2f}" '
            f'filter="url(#{p}-midglow)"/>'
            f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="#FFD9A8" opacity="{dim:.2f}"/>')


# ---------------------------------------------------------------- panel parts
def panel_defs(p, accent, metal_hi="#5b636d", metal_lo="#1a1e23"):
    return f'''
<linearGradient id="{p}-fascia" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#1c2025"/><stop offset=".5" stop-color="#14171b"/>
  <stop offset="1" stop-color="#0f1216"/>
</linearGradient>
<linearGradient id="{p}-case" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#2b3037"/><stop offset=".45" stop-color="#1e2228"/>
  <stop offset="1" stop-color="#14171b"/>
</linearGradient>
<radialGradient id="{p}-knob" cx=".36" cy=".30" r=".85">
  <stop offset="0" stop-color="{metal_hi}"/>
  <stop offset=".55" stop-color="#2b3138"/>
  <stop offset="1" stop-color="{metal_lo}"/>
</radialGradient>
<linearGradient id="{p}-bat" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#2a3037"/><stop offset=".35" stop-color="#98a3ad"/>
  <stop offset=".62" stop-color="#5d666f"/><stop offset="1" stop-color="#20252a"/>
</linearGradient>
<radialGradient id="{p}-btn" cx=".38" cy=".32" r=".8">
  <stop offset="0" stop-color="#4a525b"/><stop offset=".6" stop-color="#242a30"/>
  <stop offset="1" stop-color="#171b1f"/>
</radialGradient>
<linearGradient id="{p}-vig" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#000" stop-opacity=".55"/>
  <stop offset=".35" stop-color="#000" stop-opacity="0"/>
  <stop offset=".75" stop-color="#000" stop-opacity="0"/>
  <stop offset="1" stop-color="#000" stop-opacity=".62"/>
</linearGradient>
<linearGradient id="{p}-refl" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#000" stop-opacity="0"/>
  <stop offset="1" stop-color="#000" stop-opacity="1"/>
</linearGradient>
'''


def knob(p, cx, cy, r, accent, pointer_deg=0.0):
    o = [f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r*1.16:.2f}" fill="#0c0f12" opacity=".8"/>',
         f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="url(#{p}-knob)" '
         f'stroke="#6d757e" stroke-width=".22"/>']
    # knurl
    for i in range(28):
        a = math.radians(i * 360 / 28)
        o.append(f'<line x1="{cx+math.cos(a)*r*.86:.2f}" y1="{cy+math.sin(a)*r*.86:.2f}" '
                 f'x2="{cx+math.cos(a)*r*.99:.2f}" y2="{cy+math.sin(a)*r*.99:.2f}" '
                 f'stroke="#0d1013" stroke-width=".22" opacity=".55"/>')
    a = math.radians(pointer_deg - 90)
    o.append(f'<line x1="{cx+math.cos(a)*r*.16:.2f}" y1="{cy+math.sin(a)*r*.16:.2f}" '
             f'x2="{cx+math.cos(a)*r*.86:.2f}" y2="{cy+math.sin(a)*r*.86:.2f}" '
             f'stroke="{accent}" stroke-width="{r*.13:.2f}" stroke-linecap="round"/>')
    o.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r*.20:.2f}" fill="#0e1114"/>')
    return "\n".join(o)


def lever(p, cx, cy, half, tilt=1):
    """МТ1 toggle: bezel nut, bat, ball tip. tilt +1 = up, -1 = down."""
    ty = cy - half * tilt
    return (f'<ellipse cx="{cx:.2f}" cy="{cy:.2f}" rx="{half*.62:.2f}" ry="{half*.30:.2f}" '
            f'fill="#2b3138" stroke="#666f78" stroke-width=".2"/>'
            f'<rect x="{cx-half*.17:.2f}" y="{min(cy,ty):.2f}" width="{half*.34:.2f}" '
            f'height="{half:.2f}" rx="{half*.17:.2f}" fill="url(#{p}-bat)"/>'
            f'<circle cx="{cx:.2f}" cy="{ty:.2f}" r="{half*.33:.2f}" fill="url(#{p}-knob)" '
            f'stroke="#7d868f" stroke-width=".18"/>'
            f'<circle cx="{cx-half*.10:.2f}" cy="{ty-half*.11:.2f}" r="{half*.10:.2f}" '
            f'fill="#c9d2da" opacity=".55"/>')


def button(p, cx, cy, r):
    return (f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r*1.22:.2f}" fill="#0f1216" '
            f'stroke="#3b434b" stroke-width=".22"/>'
            f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="url(#{p}-btn)" '
            f'stroke="#5c656e" stroke-width=".2"/>'
            f'<circle cx="{cx-r*.26:.2f}" cy="{cy-r*.30:.2f}" r="{r*.34:.2f}" '
            f'fill="#8e98a2" opacity=".18"/>')


def hexmark(cx, cy, r, col):
    pts = " ".join("%.2f,%.2f" % (cx + math.cos(math.radians(60*i-90))*r,
                                  cy + math.sin(math.radians(60*i-90))*r) for i in range(6))
    return (f'<polygon points="{pts}" fill="none" stroke="{col}" stroke-width="{r*.16:.2f}"/>'
            f'<line x1="{cx-r*.92:.2f}" y1="{cy:.2f}" x2="{cx+r*.92:.2f}" y2="{cy:.2f}" '
            f'stroke="{col}" stroke-width="{r*.16:.2f}"/>')


MONO = "IBM Plex Mono, ui-monospace, monospace"
COND = "IBM Plex Sans Condensed, Arial Narrow, sans-serif"


def text(x, y, s, fill="#8A8F97", size=2.6, anchor="middle", family=MONO,
         weight="400", ls=.5, op=1.0):
    return (f'<text x="{x:.2f}" y="{y:.2f}" font-family="{family}" font-size="{size:.2f}" '
            f'fill="{fill}" text-anchor="{anchor}" font-weight="{weight}" '
            f'letter-spacing="{ls}" opacity="{op}">{s}</text>')
