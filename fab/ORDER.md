# Order sheet: the three TS06 boards

For the owner, who places the order by hand. Nothing here was sent to a board house: no site was
contacted, nothing was uploaded, no price was looked up, so there are no prices on this page. Anything
marked *inferred* is a typical figure for a low-cost two-layer service, not something a fab told us;
check it against the fab you choose.

Status: the three zips are built and checked, and every row of the DFM check passes on all three boards. The
four findings the fascia had in the first version of this sheet (silk lines, back legend text, mask slivers, the
finish in its job file) are fixed in the generators and the zip is rebuilt; they are closed below.

## The three zips

All three are in this folder. Upload one zip per board; each holds the Gerbers, the drills and a job file.

| Board | Zip | Size | Layers | Thickness | Holes (plated / non-plated) | DFM check |
|---|---|---|---|---|---|---|
| TS06-DISP rev B (the tubes) | `fab/TS06-DISP-revB-fab.zip` (120 kB) | 191.4 x 44.0 mm | 2 | 1.6 mm | 179 / 10 | all PASS |
| TS06-DRV rev B (the driver) | `fab/TS06-DRV-revB-fab.zip` (333 kB) | 191.4 x 100.0 mm | 2 | 1.6 mm | 427 / 8 | all PASS |
| Fascia R rev A with the Divider gold | `fab/TS06-FASCIA-R-revA-divider-fab.zip` (48 kB) | 191.4 x 40.0 mm | 2 | **2.0 mm** | 0 / 9 | all PASS |

Notes on the table:
* The job files inside the zips say 191.5 x 44.1, 191.5 x 100.1 and 191.45 x 40.05: they add the width of the outline line. The boards are the sizes in the table.
* All three job files now say finish ENIG, and the fascia's says 2.0 mm (its board file carries the same stack-up as TS06-DISP and TS06-DRV). KiCad does not write the mask and silk colours into a job file; they are in the boards' stack-ups (black, white) and in the renders.
* The fascia is **2.0 mm** thick, not 1.6 mm. That is deliberate: the case is drawn for a 2.0 mm fascia (`PCB/README.md`, `3d/case-pair`). Make sure the fab quote says 2.0 mm for this one.
* The fascia has no plated holes (every part is surface-mounted on its back; the front holes are for the switch bodies and screws). Its zip therefore has no plated drill file. It does carry a back solder-paste layer, for the eight 1206 resistors, in case you want a stencil; ignore it if you solder by hand.
* The gold of the fascia is in the zip as copper on the front with openings in the front mask over it. That was read back out of the Gerbers, not just trusted: the mask is open over all of the gold (see "What was checked").

Pictures: `fab/preview/` (the fascia with the gold, and the three boards side by side).

## What you choose at the fab

* **Quantity: 10 of each board (the owner's choice).** A prototype run, not the production batch.
  * The cheap promotional prices at the usual fabs are for small boards (often up to 100 x 100 mm, 1.6 mm, HASL, green). These boards are 191.4 mm long, the fascia is 2.0 mm and needs ENIG, so they likely cost more than the promo (*inferred*; no prices were checked).
* **Mask and silk colours (the owner's choice, all three boards).**
  * Solder mask: black, **matte black if the fab offers it at a small extra cost**.
  * Silk: white.
  * The stack-ups of all three boards say "Black" and "White" (KiCad has no matte setting), so the renders agree with this; matte is chosen at the fab. These are the colours the fascia art and its renders assume (`tools/fascia_art.py`, `tools/render_kicad.py`): the gold shows against black, the names in white.
* **Surface finish.** ENIG on all three. All three job files say ENIG (the fascia's does since this rebuild: its board file now carries the stack-up). The fascia's gold look needs ENIG: with HASL the "gold" would be silver-grey (inferred).
* **The fab's own order number on the silk.** Many fabs print one. On the fascia, which is the visible face, ask for **no number**, or a hidden spot on the back (inferred: most have a "no marking" or "marking position" option; some charge for it). On DISP and DRV the number can go anywhere on the back.

## Your open choices

1. **G11, which fascia.** R is recommended (3 to 0 in the referendum). This sheet and the zip assume R. If you choose another fascia, the zip is to be rebuilt; say so.
2. **The gold.** Divider is the leader's pick and is what the zip holds. The other three (ladder, fans, guilloche) are still in `tools/fascia_gold.py`, and the zip can be rebuilt with another by one command:
   ```
   bash tools/mkfab.sh TS06-FASCIA-rhythm --gold ladder      # or fans, guilloche; --gold none is the bare board
   ```
   The zip's name carries the gold. **Be aware:** ladder, fans and guilloche are laid out for the narrower fascia A (176 mm), not for R. On R the generator stops and prints what is wrong with them (ladder: its rows do not line up; fans and guilloche: gold touches the white names and a control). So today only the Divider is ready for R; another gold on R needs a layout first. The flag is there; the artwork is not.
3. **G8, first half.** Whether to commit the board files themselves "filled" (with the copper pours stored in them). The zips are built with the pours filled either way, and you order from the zips, so this does not hold up the order.

## What only the prototype can close (G14)

Parts and a bench are needed for these; the prototype run is the way to close them:
* the ИН-15 / ИН-17 pinouts and the pip height;
* the PBS / PLS heights;
* the RTC module's pin order;
* the L1 part;
* the anode resistors marked TBC;
* the ИН-12 brightness at 6 slots (E6);
* the КМД1 and МТ1 dry fit (also a G11 condition);
* the colon courtyard overlap.

## What was checked

* `bash tools/verify_pair.sh`: 27 PASS, 0 FAIL, 0 SKIP.
* `bash tools/mkfab.sh`: PASS for all three (the pours are in the Gerbers; the fascia's gold is in F.Cu and open in F.Mask, with no thin mask web over it). The DISP and DRV zips are unchanged by the rebuild.
* `python3 tools/dfm_check.py`: every row PASS on all three boards, exit 0. It is KiCad's DRC with generic fab limits (below, *inferred*), plus a second reading of the zips themselves. Every check was also run on a deliberately broken board first and shows FAIL there (the self-test, 17 rows).
* `python3 tools/dfm_check.py --g11`: passes (below).

The limits used (all *inferred*, typical of a low-cost two-layer service): track width 0.15 mm; copper clearance 0.15 mm; plated drill 0.3 mm; non-plated drill 0.5 mm; annular ring 0.15 mm; copper to board edge 0.3 mm; hole to hole 0.5 mm wall to wall; silk line 0.15 mm; silk text height 1.0 mm; mask sliver 0.1 mm; board within 400 x 500 mm.

Worst values found (smaller is nearer the limit):

| | TS06-DISP | TS06-DRV | Fascia R |
|---|---|---|---|
| Track width (limit 0.15) | 0.25 | 0.25 | 0.25 |
| Copper clearance (0.15) | 0.25 | 0.21 | 0.375 |
| Annular ring (0.15) | 0.30 | 0.20 | over 0.40 |
| Copper to edge (0.3) | 0.75 | 0.75 | over 0.80 |
| Smallest plated / non-plated drill (0.3 / 0.5) | 0.9 / 3.2 | 0.8 / 3.2 | none / 2.7 |
| Silk line, from the Gerbers (0.15) | 0.15 | 0.15 | 0.15 (was 0.10 back, 0.12 front) |
| Silk text height (1.0) | 1.0 | 1.0 | 1.0 (was 0.8) |
| Narrowest mask web, front (0.1) | 0.3 | 0.3 | 0.100 (was below 0.1: 0.05) |
| Board size | 191.4 x 44.0 | 191.4 x 100.0 | 191.4 x 40.0 |

Reading the fascia's mask web: 0.100 mm is the raster's reading, which steps in 0.025 mm and carries about +-0.03 mm, so
it means "no piece of mask thinner than 0.1 mm of any size worth the name". What is left near that value are the
tips of the crescents of mask where a box edge crosses an entry ring's hole (three rings of the SUB box, 0.004 mm2 each).

### The four findings on the fascia: closed

All four are fixed in the generators and the fascia zip is rebuilt. (They were found by the first DFM check, in the
version of this sheet before.)
1. **Front silk rings of 0.12 mm round the controls:** `tools/mkfp.py` draws every silk line at least 0.15 mm (`SILK_W`); the five rings are 0.15 now.
2. **Back silk:** the eight 1206 outlines (0.10) and J1's outline (0.12) are 0.15 mm, in the same footprint generator; J1's pin legend text is 1.0 mm tall with a 0.15 mm stroke (it was 0.8 / 0.12), in `tools/mkpcb_fascia_rhythm.py`. TS06-DISP and TS06-DRV use none of those footprints: their board files and their zips are unchanged.
3. **Mask slivers at the dial rings:** `tools/fascia_gold.py` (the Divider) ends every gold line 0.1 mm clear of a ring's hole, so no line cuts a hole's disc of mask in two. The check also found the +5V terminal ring 0.096 mm from the GND symbol (a mask web just under the limit, which the raster read as 0.1): it is moved 0.4 mm out and the gap is asserted. Done for R and for A. The other three golds on A (ladder, fans, guilloche) have no line ending in a ring's hole.
4. **The finish "None" in the fascia's job file:** the fascia board now carries the stack-up (black mask, white silk, ENIG, 2.0 mm), written by `tools/mkpcb_fascia_rhythm.py`.

Not closed, and not on the order: guilloche on A (not laid out for R) still leaves thin mask pieces (the narrowest 0.05 mm, 0.004 mm2 each) at the wavy rings of its two medallions: a different cause (a tight wave), in a gold that is not chosen. TS06-FASCIA (A), TS06-FASCIA-wide, TS06-FASCIA-THT, TS06-MAIN and TS06-MAIN-THT still carry the footprint copies with the thinner silk in their board files: A and wide have no generator that writes them (`tools/mkpcb.py` still draws the older 52 mm board; wide is made from A), and none of them is in the order.

## The G11 conditions, measured on the fascia with the gold

* **Legends of at least 3 mm: met.** All nine legends are set 3.2 mm tall; the drawn capitals measure 3.5 mm (FORMAT/DATE is 4.4 mm because of its slash).
* **Boss to R5 margin: 1.4 mm is left.** The boss round the bottom-left screw clears R5's courtyard by 1.69 mm as drawn (the 1.7 mm of G11); to R5's pad copper itself 2.04 mm. Against typical fab tolerance (outline about +-0.2 mm, hole position about +-0.1 mm, *inferred*, both against us) that leaves 1.39 mm to the courtyard and 1.74 mm to the copper. Still clear.
* **The dry fit of a real КМД1 and МТ1 needs the parts**, so it stays open for the prototype (G14).

## Rebuild and re-check

```
bash tools/mkfab.sh                      # all three zips; a zip is kept if only its creation date would change
python3 tools/dfm_check.py               # the DFM tables, with the deliberately broken board first
python3 tools/dfm_check.py --g11         # the G11 measurements above
python3 tools/fab_preview.py fab/preview # the pictures (each board whole)
```
