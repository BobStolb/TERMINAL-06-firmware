# Pictures of the boards as ordered

Rendered by KiCad 10's own 3D renderer from the committed board files, as the fab would build them:
black solder mask, white silkscreen, ENIG (gold) where the mask is open. Front (top) views. Saved here
so that a product page can use them later; nothing in this folder is published.

| Picture | What it shows |
|---|---|
| `fascia-R-divider-top.png` | The fascia R (`PCB/TS06-FASCIA-rhythm`, rev B) with the Plates white print and the Divider gold, seen from the front: the six position names, MODE / FIELD / SUB nameplates, the dial drawn as its own resistor divider, the SUB rule, the lever ladder and the two key frames. 191.4 x 40 mm. |
| `three-boards-top.png` | The three boards one under the other, each labelled: TS06-DISP rev B (the tubes), TS06-DRV rev B (the driver) and the fascia R with the Divider gold. Same scale for all three. |

## Regenerate

From the repository root (KiCad 10 in Docker, or `KICAD_CLI`; needs Pillow):

```
python3 tools/fab_preview.py fab/preview                    # both pictures, the Divider gold
python3 tools/fab_preview.py fab/preview --gold ladder      # another gold (see fab/ORDER.md: only the divider is laid out for R)
```

`tools/fab_preview.py` builds the fascia's art board in a scratch directory with `tools/fascia_gold.py`
(nothing under `PCB/` is written) and renders each board with `tools/render_kicad.py`. A single board
can be rendered by hand, for example:

```
python3 tools/fascia_gold.py divider /tmp/fascia-R-divider.kicad_pcb --base R
python3 tools/render_kicad.py /tmp/fascia-R-divider.kicad_pcb fascia.png --side top --px-per-mm 12
```

Size limits kept by the script: at most 2400 px wide and 3 MB a file.

Each board is shown whole, with a 2 mm margin. `tools/render_kicad.py` frames a board from a rule that holds for the
fascia (191.4 x 40 mm) but not for TS06-DRV (191.4 x 100 mm), where KiCad draws about 9% larger than the rule says; the
three-board picture used to lose TS06-DRV's left and top edges because of it. `tools/fab_preview.py` now measures the
scale first (two white squares planted on a scratch copy are found in a test render) and frames the real render from
that. It needs numpy and scipy as well as Pillow.
