# -06 render toolkit

Generates every drawing in the concept-plate pages from millimetre dimensions. Pure Python
standard library — **no pip install, no dependencies**. Tested on Python 3.11; needs 3.6+
for f-strings.

## The three files

| File | What it is | Run it? |
|---|---|---|
| `tubes.py` | Shared primitives — the hand-authored wire-cathode glyph paths, the glow filter stack, the tube face, the knob / lever / button / hexmark. | No. Imported by the other two. |
| `render.py` | **Axonometric heroes** (3/4 views) and **general-arrangement sheets** (front + profile + plan, dimensioned). Self-contained. | Yes |
| `render2.py` | **Lit front elevations**, the **rear panel** and the **tube macro**. Imports `tubes` and `render`. | Yes |
| `render3.py` | **Night heroes** and the **rear three-quarter**. Imports `tubes` and `render`. | Yes |
| `render4.py` | **TERMINAL-06 extended set** — left 3/4, right profile, plan, exploded, fascia macro, scale sheet. Imports `tubes`, `render`, `render3`. | Yes |

Keep all five in the same folder.

## Running it

```bash
python3 render.py     # 8 files: svg-*-hero.svg, svg-*-ga.svg
python3 render2.py    # 6 files: v-*-front.svg, v-terminal-rear.svg, v-terminal-macro.svg
python3 render3.py    # 5 files: n-*-night.svg, n-terminal-rear34.svg
python3 render4.py    # 6 files: n-terminal-{left,profile,plan,exploded,fascia,scale}.svg
```

Both write `.svg` into **their own folder** (`OUT = os.path.dirname(__file__)`), print each
filename and its byte size, and overwrite silently. 14 files, ~740 KB total.

| Output | View |
|---|---|
| `svg-terminal-hero.svg` · `svg-mimi-hero.svg` · `svg-quadrant-hero.svg` · `svg-scaler-hero.svg` | 3/4 axonometric |
| `svg-terminal-ga.svg` · `svg-mimi-ga.svg` · `svg-quadrant-ga.svg` · `svg-scaler-ga.svg` | front + right profile + plan, with dimensions |
| `v-terminal-front.svg` · `v-mimi-front.svg` · `v-quadrant-front.svg` · `v-scaler-front.svg` | lit front elevation, 1:1, full silkscreen |
| `v-terminal-rear.svg` | rear panel — DC in, service USB, vent, HV warning |
| `v-terminal-macro.svg` | one ИН-12А at ×5 with callouts (listing slot 4) |
| `n-terminal-night.svg` · `n-mimi-night.svg` · `n-quadrant-night.svg` · `n-scaler-night.svg` | night 3/4 — tubes are the only light source |
| `n-terminal-rear34.svg` | rear three-quarter, night — DC in, service port, vent, HV triangle |
| `n-terminal-left.svg` | left three-quarter, lit — the side the hero hides |
| `n-terminal-profile.svg` | right profile, 1:1 orthographic, dimensioned |
| `n-terminal-plan.svg` | plan, 1:1 orthographic — plinth inset, tube pitch, the two gaps |
| `n-terminal-exploded.svg` | four layers on the vertical, captioned |
| `n-terminal-fascia.svg` | fascia detail ×2.6 — rotary at 32°/detent, levers, buttons |
| `n-terminal-scale.svg` | 1:1 beside a 146 × 71 phone and a ⌀80 × 95 mug |

## Fonts — read this before judging the output

The SVGs reference **IBM Plex Sans Condensed** and **IBM Plex Mono** by name. They are not
embedded. If those aren't installed on the machine viewing the file, every label silently
falls back to Arial Narrow / a default mono and the drawings look subtly wrong — wider
labels, collisions in the dial legend.

Install both (free, OFL): <https://github.com/IBM/plex/releases> or Google Fonts. In the
published plate pages this doesn't arise, because the page loads them from Google Fonts.

Digits inside the tubes are **not** type — they're vector paths, so they render identically
everywhere regardless of fonts.

## Viewing and rasterising

Open any `.svg` straight in a browser. For PNG:

```bash
# best quality, honours installed fonts
inkscape --export-type=png --export-width=2400 v-terminal-front.svg

# lighter alternative
rsvg-convert -w 2400 v-terminal-front.svg -o v-terminal-front.png

# no tools installed? headless Chrome works
chromium --headless --screenshot=out.png --window-size=2400,1400 v-terminal-front.svg
```

For Etsy, export the front elevations at **2000 px on the long edge or more** — the glow is
built from Gaussian blur filters and low resolution muddies it.

## Changing the design

All geometry is millimetres, declared as constants at the top of each product block.

**`render.py`** — world coordinates, **y up**, z into the screen.

```python
T_W, T_H, T_D, T_LEAN            = 237.0, 56.0, 104.0, 12.0   # base slab + front rake
T_PW, T_PH, T_PD, T_PX, T_PZ     = 213.0, 16.0, 46.0, 12.0, 30.0   # plinth: w, h, d, inset, setback
T_TUBES = [(24.5, 22, 24, "2"), ...]   # (centre_x, width, height, lit glyph)
```

Camera lives in each `*_hero()`: `Scene(yaw=29, pitch=10, scale=2.75)`. Lower `pitch` for a
flatter, more product-shot angle; `scale` is px per mm and only affects framing.

**`render2.py`** — screen coordinates, **y down** from the top of the object.

```python
TW, TBASE_H, TPL_H, TTUBE_H = 237.0, 56.0, 16.0, 24.0
TUBES = [(24.5, 22, 24, "2"), ...]
SCREENS = ["RUN", "TIME", "DISP", "AMB", "INFO", "DATE"]   # dial legend
```

**`tubes.py`** — the `GLYPH` dict holds one SVG path per cathode, authored in a 12 × 18 box,
y down. They are **stroked, never filled** (`stroke-linecap="round"`), because a nixie cathode
is a bent wire. To add a glyph, draw it in that box and add an entry. `tube_face()` takes
`digit_frac` (glyph height as a fraction of tube height), `ghost_op` (unlit cathode opacity),
`dim` (0–1 brightness) and `glyphset` (which cathodes exist in this tube).

**`render3.py`** — same world as `render.py` (y up), plus two things worth knowing.

`night(col, k, warm, warmth)` is the whole lighting model: take the daylight colour, multiply
it down by `NIGHT * k`, then bleed `warmth` of the glow colour into it. Every surface in every
night render is one call to that. Raise `NIGHT` to lift the whole set; change a face's `k` to
relight one panel.

`frag_on_face(sc, origin, frag)` drops a `tubes.tube_face()` fragment — glass, mesh, ghost
cathodes, the four-layer glow — onto an axonometric face, so the 3/4 views get the same tube
rendering the 1:1 elevations do. `origin` is the world point the fragment's **top-left** corner
lands on, which for a tube is `(x0, deck + height, z)`.

> **The y-flip trap.** The world is y-**up**; every `tube_face()` fragment is y-**down**. The
> helper passes `(0, -1, 0)` as the face's v vector to reconcile them. Get that sign wrong and
> every glyph renders vertically mirrored — and it is genuinely hard to spot, because a flipped
> 3 still looks like a 3 and a flipped A looks like a slightly odd A. Check a **4** or a **9**.

Note also that `glyph_path()` falls back to the `"8"` path for any character not in `GLYPH`,
silently. Cyrillic **Р** and **П** are their own entries now (U+0420 / U+041F) — they are *not*
the Latin lookalikes, and before they were added the AM/PM tube rendered a perfectly plausible
8. If a new symbol tube renders an 8 you did not ask for, that is why.

**`render4.py`** — two lessons are baked into this one, both worth knowing before you add
a view of your own.

*Do not use the axonometric camera for a plan or a profile.* `Scene` sorts faces by a depth
term that **grows with height**, so at a steep pitch the upper geometry sorts as *further
away* and the drawing silently inverts — the plan view came out as a bare case lid with
mirrored type on it. Elevations are built as true orthographic SVG instead, which is what
they should have been anyway: they are drawings, and a drawing is measurable.

*Captions are not silkscreen.* `text_on_face()` maps type onto a surface, which is right for
a wordmark on a panel and wrong for a label — on a horizontal plane it foreshortens into an
unreadable smear. `screen_label()` projects an anchor point and then writes plain
screen-space text, and it also pushes the text's far end into `sc.pts` so the viewBox
actually includes it. Without that last step a caption hangs off the edge of the sheet with
no warning, because `Scene` sizes its viewBox from geometry only.

One more, for any hand-built sheet: **those are screen-space, y down.** The detent-fan and
knob-pointer maths were copied from the world-space (y up) code and came out mirrored, with
the dial legend fanning below the knob instead of around it. Negate `cos` when you move
angle maths between the two.

### The one trap

**The two scripts each hold their own copy of the dimensions.** Change the plinth width in
`render.py` and the hero updates but the elevation doesn't — they will silently disagree.
This is the same class of error that put a 190 mm plinth under a 210 mm tube row in Rev E.

Until a shared `dims.py` exists: **change a number in both files, then regenerate both and
put the hero and the elevation side by side before trusting either.**

## Where the output goes

The plate pages inline these SVGs directly rather than linking them, so regenerating a file
does not update a published page — the SVG has to be re-injected and the page republished.
The pages that consume them:

- TERMINAL-06 concept plates → hero, GA, front, rear, macro
- MIMI-06 «KURO» → hero, GA, front
- QUADRANT → hero, GA, front
- SCALER-06 → hero, GA, front

## Provenance

Written for the TERMINAL-06 Rev E case revision, 02.09.2026. Supersedes nothing — the older
`terminal06-render-source.zip` toolchain (`front.py`, `dial.py`, `hero.py`) still describes
the **Rev C trench geometry** and has not been updated. Feed `dial.py` **32°**, the measured
detent angle, if you go back to it.
