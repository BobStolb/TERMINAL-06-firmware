#!/usr/bin/env python3
"""TS06-DISP + TS06-DRV case concept: the numbers, the checks and the drawings.

    python3 3d/case-pair/case_pair.py              # params.scad, checks.md, out/*.svg
    python3 3d/case-pair/case_pair.py --extract    # re-read the three boards into boards.json first
    python3 3d/case-pair/case_pair.py --render     # also STL + PNG through OpenSCAD (xvfb-run)
    python3 3d/case-pair/case_pair.py IN12_SEAT=0  # a what-if: print the envelope, write nothing

WHAT THIS IS. A case drawn around the through-hole pair as it stands in this repository, not
around remembered numbers. Every dimension below is one of six kinds, and the kind is written
beside it (and carried into params.scad as a comment):

    board     read out of the board generators / board files by --extract (boards.json)
    doc       a number stated in a document in this repository (named)
    measured  read on a part on the owner's bench (the instrument and the date are named)
    reading   taken from a measurement by a stated step (a difference, say), not measured itself
    design    a choice made here, with the reason
    assumed   a catalogue-typical value nobody has measured yet - check it on the part

THE FRAME. World X and Y are the FreeCAD assembly's, as the pair review uses them: X across the
front from the clock's left (TS06-DISP's x = 0), Y up (TS06-DISP's top edge at Y 78, TS06-DRV's
bottom edge at Y 4). Z is depth: 0 at the ИН-12 glass front, positive towards the back.
OpenSCAD gets x = X, y = Z, z = Y, so the clock faces -y (OpenSCAD's front view).

WHERE THE BOARD NUMBERS COME FROM. tools/mkpcb_disp.py and tools/mkpcb_drv.py are imported as
modules: that runs their placement and hand-laid copper and nothing else (no router, no file
written - both only write under `if __name__ == "__main__"`). The same generators write the
committed PCB/TS06-DISP and PCB/TS06-DRV boards (191.4 x 44 and 191.4 x 100); reading the
generators rather than the .kicad_pcb files keeps this in step with a board that is being
changed. TS06-FASCIA is read from its .kicad_pcb (FASCIA_PCB=<board> puts another in its place).
Parts are keyed by reference and footprint; a footprint FP_H does not list falls back to the
height its own descr states, so a new footprint (a larger L1, say) is picked up, not refused.
"""
import hashlib, json, math, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
TOOLS = os.path.join(ROOT, "tools")
OUTDIR = os.path.join(HERE, "out")
BOARDS = os.path.join(HERE, "boards.json")
FASCIA_PCB = os.environ.get("FASCIA_PCB") or os.path.join(ROOT, "PCB", "TS06-FASCIA", "TS06-FASCIA.kicad_pcb")   # a variant can be tried in its place


# ============================================================================ extraction
def _sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha1(fh.read()).hexdigest()[:12]


def extract():
    """Read the three boards. Imports the generators read-only; writes only boards.json."""
    sys.dont_write_bytecode = True               # leave tools/ exactly as it is
    sys.path.insert(0, TOOLS)
    import mkpcb_disp as S                        # noqa: E402  (placement only on import)
    import mkpcb_drv as D                         # noqa: E402
    import sexp                                   # noqa: E402

    top = S.TOP                                   # world Y of TS06-DISP's top edge
    yd = D.Y0 + top                               # world Y = yd - (DRV board y)

    def disp_w(x, y):
        return (round(x, 3), round(top - y, 3))

    def drv_w(x, y):
        return (round(D.DW - x, 3), round(yd - y, 3))

    def box(c, f):
        (ax, ay), (bx, by) = f(c[0], c[1]), f(c[2], c[3])
        return [round(min(ax, bx), 3), round(max(ax, bx), 3), round(min(ay, by), 3), round(max(ay, by), 3)]

    out = {"_about": "World-frame geometry of TS06-DISP, TS06-DRV and TS06-FASCIA for the case concept. "
                     "Written by 3d/case-pair/case_pair.py --extract; do not edit by hand.",
           "sources": {p: _sha(os.path.join(ROOT, p)) for p in
                       ("tools/mkpcb_disp.py", "tools/mkpcb_drv.py", "tools/ts06pair.py",
                        "PCB/TS06-FASCIA/TS06-FASCIA.kicad_pcb")}}
    disp = {"W": S.W, "H": S.H, "TOP": top, "frame": "X = x, Y = TOP - y",
            "holes": [disp_w(x, y) + (d,) for x, y, d in S.B.holes],
            "IN12_X": S.IN12_X, "IN15_X": S.IN15_X, "IN17_X": S.IN17_X,
            "IN12_Y": round(top - S.Y12, 3), "IN17_Y": round(top - S.Y17, 3),
            "COLON": [disp_w(S.COLON_X, y) for y in S.COLON_Y], "parts": {}}
    for ref, (f, x, y) in S.B.placed.items():
        disp["parts"][ref] = {"fp": f.name, "back": f.back, "at": disp_w(x, y), "box": box(S.B.court(ref), disp_w)}
    # the pads that decide what the brow, the trench wall and the sill must hide
    for ref in ("XP11", "XP12", "XP21", "XP22", "XP23", "XP24", "XP25"):
        pads = [p for p in S.B.pads if p.ref == ref]
        xs = [disp_w(p.x, p.y)[0] for p in pads]
        ys = [disp_w(p.x, p.y)[1] for p in pads]
        w = max(p.w for p in pads)
        disp["parts"][ref]["pads"] = [round(min(xs) - w / 2, 3), round(max(xs) + w / 2, 3),
                                      round(min(ys) - w / 2, 3), round(max(ys) + w / 2, 3)]
    drv = {"W": D.W, "H": D.H, "Y0": D.Y0, "frame": "X = %g - x, Y = %g - y" % (D.DW, yd),
           "holes": [], "parts": {}}
    for i, (x, y, d) in enumerate(D.B.holes):
        drv["holes"].append(["H%d" % (i + 1)] + list(drv_w(x, y)) + [d])
    for ref, (f, x, y) in D.B.placed.items():
        if ref.startswith("H"):
            continue
        drv["parts"][ref] = {"fp": f.name, "back": f.back, "at": drv_w(x, y), "box": box(D.B.court(ref), drv_w),
                             # a part with any pad on a 185 V net, by the generator's own net classes
                             "hv": any(p.net and D.B.cls(p.net) == "HV" for p in D.B.pads if p.ref == ref),
                             # the height its footprint states ("height=16mm"), for a part FP_H does not know
                             "h_descr": _descr_height(f.tree)}
    for ref in ("XS1", "U1", "J1"):
        drv["parts"][ref]["pads"] = [[p.name] + list(drv_w(p.x, p.y)) for p in D.B.pads if p.ref == ref]
    # the jack's body and the Nano's outline, from their footprints' fabrication layer
    fas = _fascia(sexp)
    out.update({"disp": disp, "drv": drv, "fascia": fas})
    with open(BOARDS, "w") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
    print("wrote", os.path.relpath(BOARDS, ROOT))


def _descr_height(tree):
    """'height=16mm' in a footprint's descr, or None."""
    import re
    for n in tree:
        if isinstance(n, list) and n and n[0] == "descr":
            m = re.search(r"height\s*=\s*([0-9.]+)\s*mm", str(n[1]))
            return float(m.group(1)) if m else None
    return None


def _fascia(sexp):
    """TS06-FASCIA in its own frame (x across, y down from the top edge), read from the board."""
    t = sexp.parse(open(FASCIA_PCB, encoding="utf8").read())
    root = t[0] if isinstance(t[0], list) else t
    find = lambda n, k: [c for c in n if isinstance(c, list) and c and c[0] == k]
    unq = lambda s: s.strip('"') if isinstance(s, str) else s
    xs, ys = [], []
    for c in root:
        if isinstance(c, list) and c and c[0] in ("gr_line", "gr_arc") and \
                unq(find(c, "layer")[0][1]) == "Edge.Cuts":
            for k in ("start", "end"):
                p = find(c, k)[0]
                xs.append(float(p[1]))
                ys.append(float(p[2]))
    fas = {"W": max(xs) - min(xs), "H": max(ys) - min(ys), "holes": [], "parts": {}}
    for fp in find(root, "footprint"):
        name = unq(fp[1])
        at = find(fp, "at")[0]
        x, y = float(at[1]), float(at[2])
        ref = next((unq(p[2]) for p in find(fp, "property") if unq(p[1]) == "Reference"), "")
        if "MountingHole" in name:
            drill = next(float(find(p, "drill")[0][1]) for p in find(fp, "pad"))
            fas["holes"].append([x, y, drill])
            continue
        cx, cy = [], []
        for g in fp:
            if isinstance(g, list) and g and g[0] in ("fp_line", "fp_rect") and \
                    "CrtYd" in unq(find(g, "layer")[0][1]):
                for k in ("start", "end"):
                    p = find(g, k)[0]
                    cx.append(x + float(p[1]))
                    cy.append(y + float(p[2]))
        hole = [float(find(p, "drill")[0][1]) for p in find(fp, "pad") if find(p, "drill")]
        fas["parts"][ref] = {"fp": name, "at": [x, y], "side": unq(find(fp, "layer")[0][1]),
                             "box": [min(cx), max(cx), min(cy), max(cy)] if cx else None,
                             "panel_hole": max(hole) if hole else None}
    fas["holes"].sort()
    return fas


# ============================================================================ the numbers
class Dims:
    """name -> value, with the kind and the source kept beside it (written into params.scad)."""

    def __init__(self):
        self.rows, self.v = [], {}

    def __call__(self, name, value, kind, src, group=""):
        assert name not in self.v, name
        self.rows.append((name, value, kind, src, group))
        self.v[name] = value
        return value


def dims(B):
    d = Dims()
    disp, drv, fas = B["disp"], B["drv"], B["fascia"]
    g = "boards"
    d("BOARD_W", disp["W"], "board", "tools/mkpcb_disp.py W = tools/mkpcb_drv.py W", g)
    d("DISP_H", disp["H"], "board", "tools/mkpcb_disp.py H", g)
    d("DISP_TOP_Y", disp["TOP"], "board", "tools/mkpcb_disp.py TOP: world Y of TS06-DISP's top edge", g)
    d("DRV_H", drv["H"], "board", "tools/mkpcb_drv.py H", g)
    d("DRV_Y0", drv["Y0"], "board", "tools/mkpcb_drv.py Y0: TS06-DRV's top edge is 26 above TS06-DISP's", g)
    d("PCB_T", 1.6, "board", "tools/pcbkit.py Board.thickness (both boards)", g)
    d("FASCIA_W", fas["W"], "board", "PCB/TS06-FASCIA/TS06-FASCIA.kicad_pcb Edge.Cuts", g)
    d("FASCIA_H", fas["H"], "board", "PCB/TS06-FASCIA/TS06-FASCIA.kicad_pcb Edge.Cuts (was 52, PCB/README.md)", g)
    # the tube row's centre is the middle of H10 and ИН-15А, not of the board: TS06-DISP's margins are
    # 3.475 left and 10.265 right of the glass. A fascia too wide to centre there stops at the board edge.
    row_c = (disp["IN12_X"][0] + disp["IN15_X"][1]) / 2
    d("FASCIA_X0", float(os.environ.get("FASCIA_X0", round(min(max(row_c - fas["W"] / 2, 0.0), disp["W"] - fas["W"]), 3))),
      "design", "the owner, 29.09.26: the fascia centred under the tube row, on the middle of H10 and "
      "ИН-15А (X %.3f), kept within the board width" % row_c, g)
    d("FASCIA_T", 2.0, "doc", "PCB/README.md: TS06-FASCIA 2.0 mm FR4", g)
    d("FASCIA_HOLE_D", fas["holes"][0][2], "board", "TS06-FASCIA.kicad_pcb mounting holes (M2.5)", g)

    g = "stack"
    d("PBS_H", 8.5, "doc", "PCB/TS06-DRV/bom.md: socket strip PBS, 8.5 mm (review finding 1: PBS runs 7.0-8.5)", g)
    d("PLS_BODY", 2.5, "doc", "PCB/TS06-DISP/bom.md: 11 mm = 8.5 PBS + 2.5 PLS body", g)
    d("IN12_W", 19.47, "doc", "3d/IN12.FCStd envW (render/rev_f.py DIMS)", g)
    d("IN12_H", 28.86, "doc", "3d/IN12.FCStd envH (render/rev_f.py DIMS)", g)
    d("IN12_D", 25.50, "doc", "3d/IN12.FCStd envD: glass front to rear seating plane (measurements-IN12)", g)
    d("IN12_DIGIT", 18.63, "doc", "render/rev_f.py DIGIT_12, caliper 27.08", g)
    d("IN12_SEAT", 4.5, "assumed", "socket seat: review puts the socketed glass front ~30 in front of TS06-DISP; "
                                   "TS06-LIB-SOCKET is not captured", g)
    d("IN17_FACE", 14.0, "doc", "ИН-17 outline drawing: face 14 (measurements-IN17 Rev 5)", g)
    d("IN17_H", 20.0, "doc", "ИН-17 outline drawing: 20 across the long face axis", g)
    d("IN17_D", 19.72, "measured", "the owner's bench caliper, 2026-10-02: ИН-17 glass 19.72 from the dome to the end of the glass "
                                   "(the outline drawing's 22 is read to include the exhaust pip, IN17_PIP)", g)
    d("IN17_PIP", 2.28, "reading", "the exhaust pip below the glass end, between the leads: the drawing's 22 minus the measured "
                                   "19.72 = about 2.28 (a reading: the drawing was not shown to be taken to the pip's tip, and the "
                                   "pip itself has not been measured)", g)
    d("IN17_STEM", 20.0, "doc", "ИН-17 outline drawing: round stem Ø20 at the base", g)
    d("IN17_DIGIT", 9.0, "doc", "render/rev_f.py DIGIT_17", g)
    d("IN17_STANDOFF_MIN", 6.4, "doc", "TS06_IN17_Socket descr: >= 6.4 mm glass to board (TU: no solder within 8 mm)", g)
    d("GLASS_ALLOW", 0.4, "doc", "TERMINAL-06-cad-component-library.md §7: glass gets max-of-sample + 0.4", g)
    d("LED_D", 3.0, "board", "TS06_LED_D3.0mm", g)
    d("LED_H", 5.3, "assumed", "3 mm LED body height above the board", g)
    d("LED_FLANGE_D", 3.8, "assumed", "3 mm LED flange diameter", g)
    d("INS1_D", 6.97, "doc", "TS06_INS1_Lamp descr: measured 6.97 mm envelope", g)
    d("PIN_TAIL", 1.5, "assumed", "trimmed through-hole lead + fillet proud of a board face", g)
    d("SCREW_HEAD", 2.0, "assumed", "M3 low head (DIN 7984 2.0; ISO 7380 1.65) - review finding 3", g)
    d("SCREW_HEAD_D", 5.5, "assumed", "M3 low-head diameter", g)

    g = "design"
    d("CHEEK_T", 6.0, "doc", "pair review, envelope: 6 mm cheeks", g)
    d("CHEEK_CLR", 0.5, "doc", "pair review, envelope: 0.5 mm each side", g)
    d("GLASS_RECESS", 1.0, "design", "tube glass sits 1 mm behind the face plane, so a knock lands on the case", g)
    d("SILL_TOP_Y", 39.0, "design", "trench floor: above the XP21-25 pads (37.55; review: >= 38), below the "
                                     "ИН-17 LEDs' flange (41.49 - 1.9 = 39.59)", g)
    d("SILL_T", 2.0, "design", "printed", g)
    d("BACK_GAP", 2.5, "design", "no case part closer than this to TS06-DISP's front face (pin tails, screw heads)", g)
    d("TRENCH_L_X", 3.0, "doc", "pair review 4: the trench's left wall hides XP11, the left 3 mm", g)
    d("TRENCH_R_X", round(disp["IN15_X"][1] + d.v["IN12_W"] / 2 + d.v["GLASS_ALLOW"] + 0.5, 3), "design",
      "right wall: ИН-15А (V10) glass + GLASS_ALLOW + 0.5, still hiding the H4 standoff screw and XP12's end", g)
    d("BROW_CLR", 0.8, "design", "soffit above the tall glass: 2 x GLASS_ALLOW", g)
    d("VALANCE_Y0", 74.0, "doc", "pair review 3: the brow covers the display board's top 4 mm (78 - 4)", g)
    d("VALANCE_T", 1.5, "design", "printed rib behind the ИН-17 pair", g)
    d("BROW_T", 3.0, "design", "printed brow face", g)
    d("SOFFIT_T", 2.0, "design", "printed", g)
    d("BROW_RAKE", 12.0, "doc", "spec §6: front raked 12° - the brow leans back like the fascia", g)
    d("TOP_T", 3.0, "design", "printed top plate, black like the chassis (case review m5; spec §6: chassis matte black)", g)
    d("MOD_CLR", 0.5, "doc", "the module's clearance to a case part it slides past: the pair review's 0.5 to each cheek", g)
    d("END_BLOCK", 8.0, "doc", "case review F7: every insert a cheek screw goes into sits in a block of at least 8 mm", g)
    # the top plate's rear block has to sit above TS06-DRV's top edge, which slides under it
    d("TOP_CLR", d.v["MOD_CLR"] + d.v["END_BLOCK"] - d.v["TOP_T"], "design",
      "TS06-DRV's top edge to the top plate's underside: MOD_CLR + END_BLOCK - TOP_T, so the plate's rear block "
      "(the rear panel's inserts, the cheek screws) clears the board; was the pair review's 3", g)
    d("REAR_AIR", 5.0, "doc", "pair review, envelope: 5 mm of air in front of the rear panel", g)
    d("REAR_T", 1.6, "doc", "pair review suggestion 2: the rear panel is a 1.6 mm FR4 blank", g)
    d("BASE_T", 3.0, "design", "printed or 3 mm aluminium", g)
    d("KICK_T", 2.0, "design", "the raked strip under the fascia; thin enough to clear the fascia plug", g)
    d("FASCIA_RAKE", 12.0, "doc", "spec §6 and cad-component-library: front raked 12°", g)
    d("FLOOR_CLR", 0.5, "design", "between the fascia lead's lowest point and the floor", g)
    d("VENT_W", 2.0, "doc", "pair review 4: slots no wider than 2.5 mm (2.0 used)", g)
    # case review m4: not over the 185 V switch node (X 100-130 put them over VT21, C7 and VD1); over the
    # logic side instead, centred on the Nano's courtyard as the generator places it
    u1 = drv["parts"]["U1"]["box"]
    span = 30.0
    vc = (max(u1[0], 0.0) + u1[1]) / 2
    d("VENT_X0", round(vc - span / 2, 1), "board", "case review m4: over the logic side - a 30 mm span (the pair "
      "review's) centred on U1, the Nano (courtyard X %.1f-%.1f in mkpcb_drv)" % (u1[0], u1[1]), g)
    d("VENT_X1", round(vc + span / 2, 1), "board", "VENT_X0 + 30", g)
    d("VENT_Y0", 85.0, "doc", "pair review suggestion 2: world Y 85-100 (inside the Nano's Y %.1f-%.1f)" % (u1[2], u1[3]), g)
    d("VENT_Y1", 100.0, "doc", "pair review suggestion 2", g)
    d("VENT_PITCH", 4.5, "design", "", g)
    d("VENT_HV_CLR", 5.0, "design", "no 185 V part (a pad on an HV-class net) within this of the vent field, projected", g)
    d("BOSS_W", 8.0, "design", "square boss on a cheek's inner face, M3 heat-set insert", g)
    d("BOSS_D", 10.0, "design", "boss length in Z, in front of TS06-DRV", g)
    d("FBOSS_D", 8.0, "design", "fascia boss depth behind the fascia", g)
    d("JACK_HOLE_D", 9.0, "doc", "pair review suggestion 3: Ø9 through", g)
    d("JACK_CB_D", 14.0, "doc", "pair review suggestion 3: Ø14 pocket (put on the OUTSIDE here - see checks)", g)
    d("JACK_WEB", 1.5, "doc", "pair review suggestion 3: thin the cheek to 1.5-2 mm", g)
    d("USB_SLOT_W", 12.0, "doc", "pair review suggestion 3: slot about 12 x 9 (12 along Y)", g)
    d("USB_SLOT_H", 9.0, "doc", "pair review suggestion 3 (9 along Z)", g)
    d("VIEW_DEG", 10.0, "doc", "cad-component-library §5 / spec §6: brow clearance at a 10° viewing angle", g)

    g = "parts"
    d("JACK_BODY_L", 14.5, "board", "TS06_BarrelJack_Horizontal F.Fab: x -13.70..0.80", g)
    d("JACK_BODY_W", 9.0, "board", "TS06_BarrelJack_Horizontal F.Fab: y -4.51..4.50", g)
    d("JACK_BODY_H", 11.0, "assumed", "5.5 x 2.1 PCB jack body height (PJ-002A class)", g)
    d("JACK_AXIS_H", 6.5, "assumed", "barrel axis above the board (PJ-002A class)", g)
    d("PLUG_BARREL_L", 9.5, "assumed", "5.5 x 2.1 plug sleeve length (common 9.5; long-barrel 12/14 exist)", g)
    d("PLUG_NOSE_D", 10.0, "assumed", "plug overmould nose - larger than the Ø9 hole, so it stops on the web", g)
    d("JACK_ENGAGE_MIN", 7.0, "assumed", "sleeve engagement for both contacts to make", g)
    d("NANO_PCB_T", 1.6, "assumed", "Arduino Nano board", g)
    d("USB_H", 4.0, "assumed", "mini-B receptacle height above the Nano board", g)
    d("USB_W", 7.7, "assumed", "mini-B receptacle width", g)
    d("USB_L", 9.2, "assumed", "mini-B receptacle length", g)
    d("USB_PLUG_W", 11.0, "assumed", "mini-B plug overmould across Y", g)
    d("USB_PLUG_H", 8.0, "assumed", "mini-B plug overmould across Z", g)
    d("FJ_HDR_H", 4.8, "assumed", "JST S6B-PH-SM4-TB housing height off the fascia's back", g)
    d("FJ_PLUG_OUT", 3.0, "assumed", "mated PHR-6 beyond the header mouth, to where the wires leave it", g)
    d("CABLE_R", 3.0, "assumed", "bend radius of the 6-wire PH lead (to the ribbon's centre line)", g)
    d("CABLE_HALF", 0.65, "assumed", "half the lead's thickness (6 x AWG28 side by side)", g)
    d("J1_MATED_H", 9.5, "assumed", "B6B-PH-K 6.0 header + PHR-6 housing, off TS06-DRV's display-facing face", g)
    d("LEAD_LEN", 190.0, "doc", "PCB/TS06-DRV/bom.md: fascia lead, 6-way JST PH, 180-200 mm (the middle; was the "
                                "pair review's 150)", g)
    # what hangs behind the fascia: keepouts only, the depths are the least known numbers here
    d("ROTARY_D", 25.00, "doc", "knowledge/TERMINAL-06-spec.txt §6, MEASURE BEFORE ORDERING PANELS: body / wafer "
                                "25.00, which supersedes the withdrawn 26.94 (Rev D.3)", g)
    d("ROTARY_DEPTH", 22.0, "doc", "knowledge/TERMINAL-06-spec.txt §6: the lugs sit >= 11.3 behind the fascia's rear "
                                   "face, and the §1 table gives them 10 mm of free length: 21.3, rounded up", g)
    d("MT1_W", 11.92, "doc", "measurements-MT1 #2 (candidate W)", g)
    d("MT1_L", 10.43, "doc", "measurements-MT1 #1 (candidate L)", g)
    d("MT1_DEPTH", 30.0, "assumed", "cad-component-library: 'your spec says 30 mm depth; verify per sample'", g)
    d("KMD1_A", 13.75, "doc", "measurements-KMD1 #1 (orientation not known)", g)
    d("KMD1_B", 16.91, "doc", "measurements-KMD1 #2 (orientation not known)", g)
    d("KMD1_DEPTH", 20.0, "assumed", "КМД1-1 body depth: not captured (measurements-KMD1 #8)", g)

    g = "fixings"
    d("INS_M3_D", 4.0, "assumed", "M3 heat-set insert: hole diameter (M3 x 5.7 class)", g)
    d("INS_M3_L", 5.7, "assumed", "M3 heat-set insert: length", g)
    d("INS_M25_D", 3.5, "assumed", "M2.5 heat-set insert: hole diameter", g)
    d("INS_M25_L", 4.0, "assumed", "M2.5 heat-set insert: length", g)
    d("INS_WALL_MIN", 1.5, "doc", "case review m4: at least 1.5 mm of wall round an insert", g)
    d("CLR_M3", 3.4, "design", "M3 clearance hole through a cheek", g)
    d("CB_D", 6.2, "design", "counterbore for an M3 socket head, from the cheek's outside", g)
    d("CB_DEPTH", 2.0, "design", "counterbore depth", g)
    d("SCREW_M3_L", 8.0, "design", "M3 x 8 through a cheek: 4 mm of cheek under the counterbore, 4 mm into the insert", g)
    d("SCREW_M25_L", 6.0, "design", "M2.5 x 6: fascia, rear panel, sill ties", g)
    d("MOD_WASHER_T", 0.8, "assumed", "nylon washer under the module screws' heads (PCB/TS06-DRV/bom.md: M3 + nylon washer)", g)
    d("TIP_CLR_MIN", 1.0, "doc", "case review F7: no screw within 1 mm of glass or a board", g)
    d("GLASS_BLK_CLR", 1.0, "design", "a new block under the tall glass stays this far below it (so it needs no lead-in)", g)
    d("BASE_FIX_Z", 10.0, "design", "front base screw: behind the fascia's lower bosses (Z <= 2.1)", g)
    d("WALL_FIX_Z", 16.0, "design", "trench screw: in the blocks under H10 / ИН-15А, behind the fascia's upper bosses (Z <= 8.6)", g)
    d("TOP_FIX_Z", 20.0, "design", "front top-plate screw: in front of TS06-DRV's strips (Z >= 34.1)", g)
    d("REAR_FIX_DZ", 12.0, "design", "rear base / top-plate screws this far in front of the rear panel", g)
    d("LEADIN", 3.0, "doc", "case review F8: 45° x 3 mm lead-ins on the rear edges the module passes within 1 mm", g)
    d("LEADIN_BELOW", 1.0, "doc", "case review F8: the square-edged clearances under 1 mm get one", g)
    d("LEAD_MARGIN", 1.0, "design", "a sill lead-in runs this far past the LED flange on each side", g)
    d("SLOT_X", 0.6, "doc", "case review F9: the crossmember holes slotted along X by ±0.6", g)
    d("PRINT_SHRINK", 0.4, "assumed", "PETG shrinkage along a long print, % (compensate the slicer's X scale)", g)
    d("REAR_HOLE_D", 2.7, "design", "M2.5 clearance in the FR4 rear panel (slotted ±SLOT_X along X)", g)
    d("REAR_FIX_X", 4.0, "design", "rear-panel corner screws this far in from the cheeks' inner faces", g)

    g = "variant D"
    d("FASCIA_FRAME", float(os.environ.get("FASCIA_FRAME", 0)), "design",
      "variant D, the printed fascia frame: 1 = on. Off by default: the owner has not chosen a fascia variant", g)
    d("FF_PANEL_W", 179.0, "doc", "case review, variant D: a 179 x 40 fascia, X 3.0-182.0 (no such board yet; the "
                                  "176 board stands in)", g)
    d("FF_PANEL_H", 40.0, "doc", "case review, variant D", g)
    d("FF_WEB", 4.0, "design", "the frame's depth behind the panel", g)
    d("FF_LEDGE", 2.0, "design", "the rabbet's ledge behind the panel's left, right and bottom edges", g)
    d("FF_TOP", 4.5, "design", "the top rail behind the panel (under the sill): above the КМД1 bodies (t >= 5.5)", g)
    d("FF_RIB_W", 2.0, "design", "ribs under the panel's middle, between the controls", g)
    d("FF_HOLE_E", 3.0, "design", "the 179 panel's lower holes, in from its side edges (FR4 web 1.65)", g)
    d("FF_HOLE_T", 5.0, "design", "the 179 panel's holes, down from its top edge / up from its bottom edge", g)
    d("FF_FIX_T", 20.0, "design", "the cheek screw into the frame's end blocks, down the face", g)
    d("FF_TIE_Z", 8.0, "design", "the sill ties (M2.5, down through the sill into the frame's rib heads)", g)
    return d


# height of every part on TS06-DRV's component face (the one that faces the rear panel)
FP_H = {
    "TS06_DIP-16_W7.62mm_Socket": (8.5, "assumed", "DIP socket + chip"),
    "TS06_DIP-28_W7.62mm_Socket": (8.5, "assumed", "DIP socket + chip"),
    "TS06_DIP-8_W7.62mm_Socket": (8.5, "assumed", "DIP socket + chip"),
    "TS06_DIP-4_W7.62mm_Socket": (8.5, "assumed", "DIP socket + opto"),
    "TS06_R_Axial_DIN0207_P2.54mm_Vertical": (11.0, "assumed", "0207 resistor standing"),
    "TS06_R_Axial_DIN0207_P10.16mm": (3.5, "assumed", "0207 resistor lying"),
    "TS06_R_Axial_DIN0309_P12.70mm": (4.5, "assumed", "0309 resistor lying"),
    "TS06_C_Disc_P5.00mm": (10.0, "assumed", "radial ceramic"),
    "TS06_C_Disc_P2.50mm": (8.0, "assumed", "radial ceramic"),
    "TS06_CP_Radial_D6.3mm_P2.50mm": (12.5, "assumed", "Ø6.3 x 11 electrolytic on its seat"),
    "TS06_CP_Radial_D10.0mm_P5.00mm": (20.0, "doc", "pair review finding 6: C7 16-20 mm, worst case"),
    "TS06_L_Radial_D12.0mm_P5.00mm": (None, "board", "the footprint's descr (Fastron 11P: height=16mm; review said 12-14)"),
    "TS06_TO-220-3_Vertical_HV": (19.0, "doc", "pair review finding 6: IRF840 standing"),
    "TS06_TO-92_Inline_Wide": (8.0, "assumed", "TO-92 on its leads"),
    "TS06_Arduino_Nano": (None, "derived", "PBS 8.5 + PLS body 2.5 + Nano 1.6 + mini-B 4.0 (review said ~15)"),
    "TS06_BarrelJack_Horizontal": (11.0, "assumed", "JACK_BODY_H"),
    "TS06_Fuse_PTC_MF-RG1100": (13.0, "assumed", "radial PTC"),
    "TS06_D_DO-201AD_P15.24mm": (6.0, "assumed", "DO-201AD lying"),
    "TS06_D_DO-41_P10.16mm": (3.5, "assumed", "DO-41 lying"),
    "TS06_R-78E_SIP3": (10.5, "assumed", "RECOM R-78E SIP3"),
    "TS06_Trimmer_3296W": (10.5, "assumed", "Bourns 3296W"),
    "TS06_PinSocket_1x05": (22.0, "doc", "U13 - pair review finding 6: DS3231 mini standing in a 5-way PBS, 21-22"),
}
UNKNOWN_H = 25.0     # a part whose height nothing states: taller than anything known, so it shows up in check 1
LAID = {"U13": (12.0, "review finding 6: module on a right-angle header"),
        "C7": (11.0, "review finding 6: capacitor on its side"),
        "VT21": (11.0, "review finding 6: TO-220 lying, if its footprint is redrawn")}


# ============================================================================ derived geometry
def derive(B, d, lay_down=False):
    """Everything the model, the drawings and the checks share. Mirrors case.scad's derivations."""
    v = dict(d.v)
    disp, drv, fas = B["disp"], B["drv"], B["fascia"]
    G = {"v": v, "B": B}
    r = math.radians(v["FASCIA_RAKE"])
    rb = math.radians(v["BROW_RAKE"])
    # --- the stack in Z
    v["Z_FACE"] = -v["GLASS_RECESS"]
    v["Z_DISP_F"] = v["IN12_D"] + v["IN12_SEAT"]
    v["Z_DISP_B"] = v["Z_DISP_F"] + v["PCB_T"]
    v["STACK_GAP"] = v["PBS_H"] + v["PLS_BODY"]
    v["Z_DRV_F"] = v["Z_DISP_B"] + v["STACK_GAP"]
    v["Z_DRV_B"] = v["Z_DRV_F"] + v["PCB_T"]
    v["Z_BACK"] = v["Z_DISP_F"] - v["BACK_GAP"]
    v["IN17_STANDOFF"] = v["Z_DISP_F"] - v["IN17_D"]          # faces coplanar with the ИН-12s
    v["NANO_H"] = v["PBS_H"] + v["PLS_BODY"] + v["NANO_PCB_T"] + v["USB_H"]
    # --- the stack in Y
    v["DISP_BOT_Y"] = v["DISP_TOP_Y"] - v["DISP_H"]
    v["DRV_TOP_Y"] = v["DISP_TOP_Y"] + v["DRV_Y0"]
    v["DRV_BOT_Y"] = v["DRV_TOP_Y"] - v["DRV_H"]
    v["IN12_Y"], v["IN17_Y"] = disp["IN12_Y"], disp["IN17_Y"]
    v["IN12_TOP"] = v["IN12_Y"] + v["IN12_H"] / 2
    v["IN12_BOT"] = v["IN12_Y"] - v["IN12_H"] / 2
    v["IN17_TOP"] = v["IN17_Y"] + v["IN17_H"] / 2
    v["SOFFIT_Y"] = round(v["IN12_TOP"] + v["BROW_CLR"], 2)
    v["Y_TOP_IN"] = v["DRV_TOP_Y"] + v["TOP_CLR"]
    v["Y_TOP"] = v["Y_TOP_IN"] + v["TOP_T"]
    # --- X
    v["X_IN_L"] = -v["CHEEK_CLR"]
    v["X_IN_R"] = v["BOARD_W"] + v["CHEEK_CLR"]
    v["X_OUT_L"] = v["X_IN_L"] - v["CHEEK_T"]
    v["X_OUT_R"] = v["X_IN_R"] + v["CHEEK_T"]
    # --- parts on TS06-DRV and the rear panel
    parts = []
    G["unknown_h"] = []
    for ref, p in sorted(drv["parts"].items()):
        fp = p["fp"]
        if p["back"]:                                           # display-facing: the strips and J1
            h = v["J1_MATED_H"] if ref == "J1" else v["PBS_H"]
            parts.append((ref, fp, p["box"], h, 1, "J1_MATED_H" if ref == "J1" else "PBS_H"))
            continue
        # a footprint not in FP_H (a new L1, say) takes the height its descr states, else a tall guess
        h, kind, src = FP_H.get(fp, (None, "board", "not in FP_H: the footprint's descr"))
        if fp == "TS06_Arduino_Nano":
            h = v["NANO_H"]
        elif h is None:
            h = p.get("h_descr")
            if h is None:
                h, src = UNKNOWN_H, "not in FP_H and no height in its descr: %.0f assumed" % UNKNOWN_H
            if fp not in FP_H or p.get("h_descr") is None:
                G["unknown_h"].append((ref, fp, h))
        if lay_down and ref in LAID:
            h = LAID[ref][0]
        parts.append((ref, fp, p["box"], h, 0, src))
    G["drv_parts"] = parts
    rear = [p for p in parts if p[4] == 0]
    v["PART_MAX"] = max(p[3] for p in rear)
    v["Z_REAR_IN"] = round(v["Z_DRV_B"] + v["PART_MAX"] + v["REAR_AIR"], 3)
    v["Z_REAR_OUT"] = v["Z_REAR_IN"] + v["REAR_T"]
    # --- the fascia: its front face passes through the sill's front edge, raked back 12°
    def fpt(t, s=0.0):
        """(Y, Z) of a point t mm down the fascia face from its top edge and s mm behind its front."""
        return (v["SILL_TOP_Y"] - t * math.cos(r) - s * math.sin(r),
                v["Z_FACE"] - t * math.sin(r) + s * math.cos(r))
    G["fpt"] = fpt
    v["FAS_BOT_Y"], v["FAS_BOT_Z"] = fpt(v["FASCIA_H"])
    v["Z_SILL_F"] = round(v["Z_FACE"] + v["FASCIA_T"] / math.cos(r) + 0.2, 3)
    # --- the fascia's own connector: side entry, the lead leaves towards the fascia's bottom edge
    fj = fas["parts"]["J1"]
    v["FJ_X"] = fj["at"][0] + v["FASCIA_X0"]                   # world X: the fascia is centred
    v["FJ_MOUTH_T"] = fj["box"][3]                              # courtyard edge nearest the bottom
    ex_y, ex_z = fpt(v["FJ_MOUTH_T"] + v["FJ_PLUG_OUT"], v["FASCIA_T"] + v["FJ_HDR_H"] / 2)
    cy, cz = ex_y - v["CABLE_R"] * math.sin(r), ex_z + v["CABLE_R"] * math.cos(r)   # bend centre, + normal
    v["FJ_EXIT_Y"], v["FJ_EXIT_Z"] = ex_y, ex_z
    v["FJ_BEND_Y"], v["FJ_BEND_Z"] = cy, cz
    v["FJ_LOW_Y"] = cy - v["CABLE_R"] - v["CABLE_HALF"]
    v["Y_FLOOR"] = min(0.0, math.floor((v["FJ_LOW_Y"] - v["FLOOR_CLR"]) * 10) / 10)
    v["Y_BOT"] = v["Y_FLOOR"] - v["BASE_T"]
    v["Z_TOE"] = v["Z_FACE"] - (v["SILL_TOP_Y"] - v["Y_FLOOR"]) * math.tan(r)
    v["Z_BROW_TOP"] = v["Z_FACE"] + (v["Y_TOP"] - v["SOFFIT_Y"]) * math.tan(rb)
    # --- the envelope
    v["OUT_W"] = v["X_OUT_R"] - v["X_OUT_L"]
    v["OUT_H"] = v["Y_TOP"] - v["Y_BOT"]
    v["OUT_D"] = v["Z_REAR_OUT"] - v["Z_TOE"]
    v["IN_H"] = v["Y_TOP_IN"] - v["Y_FLOOR"]
    v["IN_D"] = v["Z_REAR_IN"] - v["Z_FACE"]
    # --- openings
    xs1 = drv["parts"]["XS1"]
    pin1 = next(p for p in xs1["pads"] if p[0] == "1")
    v["JACK_Y"] = pin1[2]                                      # barrel axis: pin 1's line (F.Fab is symmetric)
    v["JACK_Z"] = v["Z_DRV_B"] + v["JACK_AXIS_H"]
    v["JACK_MOUTH_X"] = round(pin1[1] + v["JACK_BODY_L"] - 0.8, 3)   # F.Fab mouth at -13.70 from pin 1
    u1 = drv["parts"]["U1"]
    rows = sorted({p[2] for p in u1["pads"]})
    v["USB_Y"] = round((rows[0] + rows[-1]) / 2, 3)
    v["USB_X"] = u1["box"][0]                                  # courtyard: 2.4 mm proud of the left edge
    v["USB_Z"] = v["Z_DRV_B"] + v["PBS_H"] + v["PLS_BODY"] + v["NANO_PCB_T"] + v["USB_H"] / 2
    # --- module screws, display standoffs, the fascia's holes
    G["drv_case_holes"] = [h for h in drv["holes"] if h[0] in ("H5", "H6", "H7", "H8")]
    G["disp_holes"] = disp["holes"]
    G["fascia_holes"] = fas["holes"]
    profiles(G)
    return G




def profiles(G):
    """Side profiles (Z, Y) of every part extruded along X, plus the boxes. Same maths as case.scad."""
    v, fpt = G["v"], G["fpt"]
    rb = math.radians(v["BROW_RAKE"])
    zy = lambda p: (p[1], p[0])                                 # fpt gives (Y, Z)
    zin = lambda y: v["Z_FACE"] + (y - v["SOFFIT_Y"]) * math.tan(rb) + v["BROW_T"] / math.cos(rb)
    G["zin"] = zin
    LI, EB = v["LEADIN"], v["END_BLOCK"]
    G["cheek"] = [(v["Z_TOE"], v["Y_BOT"]), (v["Z_REAR_IN"], v["Y_BOT"]), (v["Z_REAR_IN"], v["Y_TOP"]),
                  (v["Z_BROW_TOP"], v["Y_TOP"]), (v["Z_FACE"], v["SOFFIT_Y"]), (v["Z_FACE"], v["SILL_TOP_Y"]),
                  (v["Z_TOE"], v["Y_FLOOR"])]
    # the brow: the orange raked face and the soffit. The top plate behind it is a separate black part
    # (case review m5). The soffit ends at the rear in a lip whose lower edge is a 45° lead-in for the tall
    # glass, which comes in from behind 0.8 mm under it (F8).
    sy, st, zb = v["SOFFIT_Y"], v["SOFFIT_T"], v["Z_BACK"]
    G["brow"] = [(v["Z_FACE"], sy), (v["Z_BROW_TOP"], v["Y_TOP"]), (zin(v["Y_TOP"]), v["Y_TOP"]),
                 (zin(sy + st), sy + st), (zb - LI - st, sy + st), (zb - LI - st, sy + LI + st),
                 (zb, sy + LI + st), (zb, sy + LI), (zb - LI, sy)]
    G["top"] = [(zin(v["Y_TOP_IN"]), v["Y_TOP_IN"]), (zin(v["Y_TOP"]), v["Y_TOP"]), (v["Z_REAR_IN"], v["Y_TOP"]),
                (v["Z_REAR_IN"], v["Y_TOP_IN"])]
    G["fascia"] = [zy(fpt(0, 0)), zy(fpt(v["FASCIA_H"], 0)), zy(fpt(v["FASCIA_H"], v["FASCIA_T"])),
                   zy(fpt(0, v["FASCIA_T"]))]
    r = math.radians(v["FASCIA_RAKE"])
    t_kb = (v["SILL_TOP_Y"] - v["Y_FLOOR"] - v["KICK_T"] * math.sin(r)) / math.cos(r)
    G["base"] = [(v["Z_TOE"], v["Y_BOT"]), (v["Z_REAR_IN"], v["Y_BOT"]), (v["Z_REAR_IN"], v["Y_FLOOR"]),
                 zy(fpt(t_kb, v["KICK_T"])), zy(fpt(v["FASCIA_H"], v["KICK_T"])), zy(fpt(v["FASCIA_H"], 0)),
                 (v["Z_TOE"], v["Y_FLOOR"])]
    # boxes: (X0, X1, Y0, Y1, Z0, Z1)
    G["sill"] = (v["X_IN_L"], v["X_IN_R"], v["SILL_TOP_Y"] - v["SILL_T"], v["SILL_TOP_Y"], v["Z_SILL_F"], v["Z_BACK"])
    G["wall_l"] = (v["X_IN_L"], v["TRENCH_L_X"], v["SILL_TOP_Y"], v["SOFFIT_Y"], v["Z_FACE"], v["Z_BACK"])
    G["wall_r"] = (v["TRENCH_R_X"], v["X_IN_R"], v["SILL_TOP_Y"], v["SOFFIT_Y"], v["Z_FACE"], v["Z_BACK"])
    disp = G["B"]["disp"]
    hw = v["IN12_W"] / 2 + v["GLASS_ALLOW"]
    v["VAL_X0"] = round(disp["IN12_X"][3] + hw, 3)              # right of M1's glass
    v["VAL_X1"] = round(disp["IN15_X"][0] - hw, 3)              # left of ИН-15Б's glass
    # the valance hangs from the soffit's rear lip, so over its span the lead-in is filled
    G["valance"] = (v["VAL_X0"], v["VAL_X1"], v["VALANCE_Y0"], sy + LI, v["Z_BACK"] - v["VALANCE_T"], v["Z_BACK"])
    G["rear"] = (v["X_OUT_L"], v["X_OUT_R"], v["Y_BOT"], v["Y_TOP"], v["Z_REAR_IN"], v["Z_REAR_OUT"])
    n = int((v["VENT_X1"] - v["VENT_X0"] - v["VENT_W"]) // v["VENT_PITCH"]) + 1
    G["vents"] = [(v["VENT_X0"] + i * v["VENT_PITCH"], v["VENT_X0"] + i * v["VENT_PITCH"] + v["VENT_W"])
                  for i in range(n)]
    # what hangs behind the fascia: [ref, x, t, across X, along the face, depth], fascia frame
    fas = G["B"]["fascia"]["parts"]
    G["bodies"] = []
    for ref in ("SW1", "SW2", "SW3", "SW4", "SW5"):
        x, t = fas[ref]["at"]
        if ref == "SW1":
            a = b = v["ROTARY_D"]; dep = v["ROTARY_DEPTH"]
        elif ref in ("SW2", "SW3"):
            a, b, dep = v["MT1_L"], v["MT1_W"], v["MT1_DEPTH"]
        else:
            a, b, dep = v["KMD1_A"], v["KMD1_B"], v["KMD1_DEPTH"]
        G["bodies"].append((ref, x + v["FASCIA_X0"], t, a, b, dep))   # x in world X
    # the rotary's rim rises above the sill's underside just behind the fascia's top edge: the sill steps back over it
    ref, x, t, a, b, dep = G["bodies"][0]
    t_top = t - b / 2
    y_under = v["SILL_TOP_Y"] - v["SILL_T"] - 0.5
    s_clear = (v["SILL_TOP_Y"] - t_top * math.cos(r) - y_under) / math.sin(r)
    v["ROT_TOP_Y"] = G["fpt"](t_top, v["FASCIA_T"])[0]
    v["SILL_NOTCH_X0"], v["SILL_NOTCH_X1"] = x - a / 2 - 1.0, x + a / 2 + 1.0
    v["SILL_NOTCH_Z"] = round(max(v["Z_SILL_F"], G["fpt"](t_top, s_clear)[1]), 2)
    # module bosses on the cheeks, in front of TS06-DRV; never across TS06-DISP's edge (it slides past)
    G["bosses"] = []
    for name, hx, hy, dia in G["drv_case_holes"]:
        left = hx < v["BOARD_W"] / 2
        x0, x1 = (v["X_IN_L"], hx + v["BOSS_W"] / 2) if left else (hx - v["BOSS_W"] / 2, v["X_IN_R"])
        y0, y1 = hy - v["BOSS_W"] / 2, hy + v["BOSS_W"] / 2
        if y0 < v["DISP_TOP_Y"] + 0.5 and y1 > v["DISP_TOP_Y"]:
            y0 = v["DISP_TOP_Y"] + 0.5
        G["bosses"].append((name, x0, x1, y0, y1, v["Z_DRV_F"] - v["BOSS_D"], v["Z_DRV_F"], hx, hy))
    # the fascia lead, as the ribbon's centre line: DRV J1 -> floor -> fascia J1
    j1 = G["B"]["drv"]["parts"]["J1"]
    jx = sum(p[1] for p in j1["pads"]) / len(j1["pads"])
    jy = j1["pads"][0][2]
    rc = v["CABLE_R"]
    yf = v["Y_FLOOR"] + v["CABLE_HALF"]
    z_top = v["Z_DRV_F"] - v["J1_MATED_H"]
    G["lead"] = [(jx, jy, z_top), (jx, jy, z_top - rc), (jx, yf + rc, z_top - rc), (jx, yf, z_top - 2 * rc),
                 (v["FJ_X"], yf, v["FJ_BEND_Z"]), (v["FJ_X"], v["FJ_EXIT_Y"], v["FJ_EXIT_Z"])]
    L = rc * math.pi / 2 * 2                                    # the two quarter bends at DRV J1
    L += (jy - (yf + rc))                                       # down to the floor
    L += math.hypot(v["FJ_X"] - jx, (z_top - 2 * rc) - v["FJ_BEND_Z"])   # along the floor, diagonal
    L += rc * math.radians(90 + v["FASCIA_RAKE"])               # up into the fascia plug
    v["LEAD_PATH"] = round(L, 1)
    fixings(G)
    fascia_frame(G)
    screws(G)


def fixings(G):
    """Where every cheek screw goes, and the blocks that take their inserts (case review F7), the rear
    panel's fixings (m4), the lead-ins (F8). Same maths as case.scad."""
    v, zin = G["v"], G["zin"]
    EB, LI = v["END_BLOCK"], v["LEADIN"]
    rb = math.radians(v["BROW_RAKE"])
    # the base: blocks on the floor at each cheek, front and rear; a full-width lip at the rear
    v["FIX_BASE_Y"] = round((v["Y_BOT"] + v["Y_FLOOR"] + EB) / 2, 3)
    v["FIX_BASE_Z0"], v["FIX_BASE_Z1"] = v["BASE_FIX_Z"], v["Z_REAR_IN"] - v["REAR_FIX_DZ"]
    # the trench: blocks under H10 and ИН-15А's glass, GLASS_BLK_CLR below it, END_BLOCK tall, through the sill
    v["WALL_BLK_Y1"] = round(v["IN12_BOT"] - v["GLASS_BLK_CLR"], 3)
    v["WALL_BLK_Y0"] = round(min(v["SILL_TOP_Y"] - v["SILL_T"], v["WALL_BLK_Y1"] - EB), 3)
    v["FIX_WALL_Y"] = round((v["WALL_BLK_Y0"] + v["WALL_BLK_Y1"]) / 2, 3)
    v["FIX_WALL_Z"] = v["WALL_FIX_Z"]
    # the brow: blocks behind the face, midway between the soffit and the top plate
    v["FIX_BROW_Y"] = round((v["SOFFIT_Y"] + v["SOFFIT_T"] + v["Y_TOP_IN"]) / 2, 3)
    v["FIX_BROW_Z"] = round(zin(v["FIX_BROW_Y"]) + EB / 2, 3)
    # the top plate: blocks under it at the front and a full-width lip at the rear, above TS06-DRV's edge
    v["FIX_TOP_Y"] = v["Y_TOP"] - EB / 2
    v["FIX_TOP_Z0"], v["FIX_TOP_Z1"] = v["TOP_FIX_Z"], v["Z_REAR_IN"] - v["REAR_FIX_DZ"]
    v["TOP_LIP_Y0"] = v["Y_TOP"] - EB                           # = TS06-DRV's top edge + MOD_CLR
    # the fascia frame (variant D): its end blocks, END_BLOCK behind the panel
    v["FF_FIX_Y"], v["FF_FIX_Z"] = [round(c, 3) for c in G["fpt"](v["FF_FIX_T"], v["FASCIA_T"] + EB / 2)]
    G["cheek_fix"] = [("base, front", v["FIX_BASE_Y"], v["FIX_BASE_Z0"]), ("base, rear", v["FIX_BASE_Y"], v["FIX_BASE_Z1"]),
                      ("trench", v["FIX_WALL_Y"], v["FIX_WALL_Z"]), ("brow", v["FIX_BROW_Y"], v["FIX_BROW_Z"]),
                      ("top plate, front", v["FIX_TOP_Y"], v["FIX_TOP_Z0"]), ("top plate, rear", v["FIX_TOP_Y"], v["FIX_TOP_Z1"])]
    if v["FASCIA_FRAME"]:
        G["cheek_fix"].append(("fascia frame", v["FF_FIX_Y"], v["FF_FIX_Z"]))
    # blocks at the left cheek (the right ones mirror them): (part, Y0, Y1, Z0, Z1, the insert's Y, Z, what is in
    # front of the insert along the face)
    xl = (v["X_IN_L"], v["X_IN_L"] + EB)
    face_at = lambda y: zin(y) - v["BROW_T"] / math.cos(rb)
    G["blocks"] = [
        ("base, front", v["Y_BOT"], v["Y_FLOOR"] + EB, v["FIX_BASE_Z0"] - EB / 2, v["FIX_BASE_Z0"] + EB / 2, v["FIX_BASE_Y"], v["FIX_BASE_Z0"]),
        ("base, rear", v["Y_BOT"], v["Y_FLOOR"] + EB, v["FIX_BASE_Z1"] - EB / 2, v["Z_REAR_IN"], v["FIX_BASE_Y"], v["FIX_BASE_Z1"]),
        ("trench", v["WALL_BLK_Y0"], v["WALL_BLK_Y1"], v["FIX_WALL_Z"] - EB / 2, v["FIX_WALL_Z"] + EB / 2 + LI, v["FIX_WALL_Y"], v["FIX_WALL_Z"]),
        ("brow", v["FIX_BROW_Y"] - EB / 2, v["FIX_BROW_Y"] + EB / 2, face_at(v["FIX_BROW_Y"]), v["FIX_BROW_Z"] + EB / 2, v["FIX_BROW_Y"], v["FIX_BROW_Z"]),
        ("top plate, front", v["TOP_LIP_Y0"], v["Y_TOP"], v["FIX_TOP_Z0"] - EB / 2, v["FIX_TOP_Z0"] + EB / 2, v["FIX_TOP_Y"], v["FIX_TOP_Z0"]),
        ("top plate, rear", v["TOP_LIP_Y0"], v["Y_TOP"], v["FIX_TOP_Z1"] - EB / 2, v["Z_REAR_IN"], v["FIX_TOP_Y"], v["FIX_TOP_Z1"])]
    G["block_x"] = xl
    # the rear panel (m4): three screws along the bottom into the base's lip, three along the top into the top
    # plate's - the corners and mid-span. None into the cheeks' 6 mm rear edges: an insert there has 1.25 mm walls.
    xs = (v["X_IN_L"] + v["REAR_FIX_X"], v["BOARD_W"] / 2, v["X_IN_R"] - v["REAR_FIX_X"])
    G["rear_screws"] = [(x, y) for y in (v["FIX_BASE_Y"], v["FIX_TOP_Y"]) for x in xs]
    G["rear_lips"] = {"base": (v["Y_BOT"], v["Y_FLOOR"] + EB, v["Z_REAR_IN"] - EB, v["Z_REAR_IN"]),
                      "top plate": (v["TOP_LIP_Y0"], v["Y_TOP"], v["Z_REAR_IN"] - EB, v["Z_REAR_IN"])}
    # lead-ins (F8), 45° x LEADIN on the rear edges the module passes within LEADIN_BELOW: the soffit (in the brow
    # profile), the left trench wall's inner edge, and the sill where the lowest LEDs' flanges pass - only there,
    # so the sill still hides XP21-25
    disp = G["B"]["disp"]
    fl = v["LED_FLANGE_D"] / 2
    G["sill_leads"] = [(round(p["at"][0] - fl - v["LEAD_MARGIN"], 3), round(p["at"][0] + fl + v["LEAD_MARGIN"], 3))
                       for k, p in sorted(disp["parts"].items(), key=lambda kp: kp[1]["at"][0])
                       if k.startswith("HL") and p["at"][1] - fl - v["SILL_TOP_Y"] < v["LEADIN_BELOW"]]
    h10_l = disp["IN12_X"][0] - v["IN12_W"] / 2
    G["wall_l_lead"] = h10_l - v["TRENCH_L_X"] < v["LEADIN_BELOW"]


def fascia_frame(G):
    """Variant D: a printed frame between the cheeks, raked with the fascia, whose pocket continues the trench
    walls (X TRENCH_L_X-TRENCH_R_X). The 179 x 40 panel drops into it; the 176 board stands in for it here, at its
    own FASCIA_X0. Local frame: X (world), t down the face from the top edge, s behind the front face."""
    v = G["v"]
    fas = G["B"]["fascia"]
    ff = {"x0": v["TRENCH_L_X"], "x1": v["TRENCH_R_X"], "px0": v["TRENCH_L_X"], "px1": v["TRENCH_L_X"] + v["FF_PANEL_W"]}
    # what stands behind the stand-in, in world X: control bodies (the КМД1 either way round) and back-side parts
    keep = []
    for ref, x, t, a, b, dep in G["bodies"]:
        half = max(a, b) / 2 if ref in ("SW4", "SW5") else a / 2
        keep.append((x - half, x + half, ref))
    for ref, p in fas["parts"].items():
        if p["box"] and not ref.startswith("SW"):
            keep.append((p["box"][0] + v["FASCIA_X0"], p["box"][1] + v["FASCIA_X0"], ref))
    keep.sort()
    lo, hi = ff["x0"] + v["FF_LEDGE"], ff["x1"] - v["FF_LEDGE"]
    gaps, edge = [], lo
    for a, b, ref in keep:
        if a > edge:
            gaps.append((edge, a))
        edge = max(edge, b)
    inner = [g for g in gaps if g[0] > lo and g[1] < hi]      # between two parts, not against a ledge
    widest = sorted(sorted(inner, key=lambda g: g[1] - g[0])[-2:])
    ff["ribs"] = [round((a + b) / 2, 1) for a, b in widest]
    ff["rib_gaps"] = widest
    ff["keep"] = keep
    ff["boss_r"] = v["INS_M25_D"] / 2 + v["INS_WALL_MIN"]
    # the 179 panel's holes: its top two over the ribs (clear of SW5, which a corner hole sits on), its bottom two
    # at its corners
    tb = v["FF_PANEL_H"] - v["FF_HOLE_T"]
    ff["holes"] = [(ff["ribs"][0], v["FF_HOLE_T"]), (ff["ribs"][1], v["FF_HOLE_T"]),
                   (ff["px0"] + v["FF_HOLE_E"], tb), (ff["px1"] - v["FF_HOLE_E"], tb)]
    fj = fas["parts"]["J1"]["box"]
    ff["j1_notch"] = (fj[0] + v["FASCIA_X0"] - 1.0, fj[1] + v["FASCIA_X0"] + 1.0)
    ff["rot_notch"] = (v["SILL_NOTCH_X0"], v["SILL_NOTCH_X1"])
    G["ff"] = ff


def screws(G):
    """Every case screw: (group, spec, seat [X, Y, Z], axis, length, diameter, boards it passes through)."""
    v, fpt = G["v"], G["fpt"]
    r = math.radians(v["FASCIA_RAKE"])
    nrm = (0.0, -math.sin(r), math.cos(r))                      # into the case, normal to the fascia
    S = []
    for name, y, z in G["cheek_fix"]:
        for x, ax in ((v["X_OUT_L"] + v["CB_DEPTH"], 1.0), (v["X_OUT_R"] - v["CB_DEPTH"], -1.0)):
            S.append(("cheek into the " + name, "M3 x %g low head" % v["SCREW_M3_L"], (x, y, z), (ax, 0.0, 0.0),
                      v["SCREW_M3_L"], 3.0, ()))
    for name, hx, hy, dia in G["drv_case_holes"]:
        S.append(("module into the cheek bosses (H5-H8, from behind, nylon washer)", "M3 x 8",
                  (hx, hy, v["Z_DRV_B"] + v["MOD_WASHER_T"]),
                  (0.0, 0.0, -1.0), 8.0, 3.0, ("TS06-DRV",)))
    if v["FASCIA_FRAME"]:
        for x, t in G["ff"]["holes"]:
            y, z = fpt(t, 0)
            S.append(("fascia into the frame", "M2.5 x %g" % v["SCREW_M25_L"], (x, y, z), nrm, v["SCREW_M25_L"], 2.5,
                      ("TS06-FASCIA",)))
        for x in G["ff"]["ribs"]:
            S.append(("sill tie into the frame", "M2.5 x %g countersunk" % v["SCREW_M25_L"], (x, v["SILL_TOP_Y"], v["FF_TIE_Z"]),
                      (0.0, -1.0, 0.0), v["SCREW_M25_L"], 2.5, ()))
    else:
        for x, t, dia in G["fascia_holes"]:
            y, z = fpt(t, 0)
            S.append(("fascia into the cheek bosses", "M2.5 x %g" % v["SCREW_M25_L"], (x + v["FASCIA_X0"], y, z), nrm,
                      v["SCREW_M25_L"], 2.5, ("TS06-FASCIA",)))
    for x, y in G["rear_screws"]:
        S.append(("rear panel into the %s" % ("base" if y < 0 else "top plate"), "M2.5 x %g" % v["SCREW_M25_L"],
                  (x, y, v["Z_REAR_OUT"]), (0.0, 0.0, -1.0), v["SCREW_M25_L"], 2.5, ()))
    G["screws"] = S


# ============================================================================ checks
def _orient(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _hits(p, q, poly):
    for k in range(len(poly)):
        a, b = poly[k], poly[(k + 1) % len(poly)]
        d1, d2, d3, d4 = _orient(a, b, p), _orient(a, b, q), _orient(p, q, a), _orient(p, q, b)
        if (d1 > 0) != (d2 > 0) and (d3 > 0) != (d4 > 0):
            return True
    return False


def _rect(b):
    """(X0, X1, Y0, Y1, Z0, Z1) box -> its (Z, Y) side outline."""
    return [(b[4], b[2]), (b[5], b[2]), (b[5], b[3]), (b[4], b[3])]


def sill_profile(G, x):
    """The sill's (Z, Y) section at X = x: stepped back over the rotary, and with its lead-in where the
    lowest LEDs pass."""
    v = G["v"]
    y0, y1, z1 = v["SILL_TOP_Y"] - v["SILL_T"], v["SILL_TOP_Y"], v["Z_BACK"]
    z0 = v["SILL_NOTCH_Z"] if v["SILL_NOTCH_X0"] <= x <= v["SILL_NOTCH_X1"] else v["Z_SILL_F"]
    if any(a <= x <= b for a, b in G["sill_leads"]):
        li = v["LEADIN"]
        return [(z0, y0), (z1 - li - 1, y0), (z1 - li - 1, y1 - li - 0.5), (z1, y1 - li - 0.5), (z1, y1 - li),
                (z1 - li, y1), (z0, y1)]
    return [(z0, y0), (z1, y0), (z1, y1), (z0, y1)]


def occluders(G, x):
    """What stands between a point inside the case and a viewer in front, in the section at X = x.
    Tube glass is transparent and is not an occluder."""
    v = G["v"]
    occ = [("brow", G["brow"]), ("top plate", G["top"]), ("fascia", G["fascia"]), ("base", G["base"]),
           ("sill", sill_profile(G, x)),
           ("TS06-DISP", [(v["Z_DISP_F"], v["DISP_BOT_Y"]), (v["Z_DISP_B"], v["DISP_BOT_Y"]),
                          (v["Z_DISP_B"], v["DISP_TOP_Y"]), (v["Z_DISP_F"], v["DISP_TOP_Y"])])]
    if G["valance"][0] <= x <= G["valance"][1]:
        occ.append(("valance", _rect(G["valance"])))
    if x < v["TRENCH_L_X"] or x > v["TRENCH_R_X"]:
        occ.append(("trench wall", _rect(G["wall_l"])))
    return occ


def view_range(G, x, target, lim=60.0, step=0.1):
    """Viewing angles (deg; + = eye above the clock) from which the point target = (Z, Y) is seen."""
    occ = [p for _, p in occluders(G, x)]
    z0 = G["v"]["Z_TOE"] - 5.0
    seen = []
    for i in range(int(round(-lim / step)), int(round(lim / step)) + 1):
        th = i * step
        t = math.tan(math.radians(th))
        p = (target[0] - 1e-4, target[1] + 1e-4 * t)
        q = (z0, target[1] + (target[0] - z0) * t)
        seen.append((round(th, 1), not any(_hits(p, q, poly) for poly in occ)))
    runs, cur = [], None
    for th, ok in seen:
        if ok and cur is None:
            cur = [th, th]
        elif ok:
            cur[1] = th
        elif cur is not None:
            runs.append(tuple(cur))
            cur = None
    if cur is not None:
        runs.append(tuple(cur))
    return runs


def _fmt_runs(runs, lim=60.0):
    if not runs:
        return "hidden from every angle within ±%g°" % lim
    return "seen from " + ", ".join("%+.1f° to %+.1f°" % r for r in runs)


def checks(G, G_lay, G_ff=None):
    v, B = G["v"], G["B"]
    disp, drv, fas = B["disp"], B["drv"], B["fascia"]
    R = []

    def row(cid, what, result, status, note=""):
        R.append({"id": cid, "what": what, "result": result, "status": status, "note": note})

    # 1. the rear panel against every part on TS06-DRV's component face
    rear = sorted([p for p in G["drv_parts"] if p[4] == 0], key=lambda p: -p[3])
    for ref, fp, box, h, side, src in rear[:7]:
        clr = v["Z_REAR_IN"] - (v["Z_DRV_B"] + h)
        row("1", "rear panel vs %s (%s, %.1f tall)" % (ref, fp.replace("TS06_", ""), h),
            "%.1f mm clear" % clr, "OK" if clr >= v["REAR_AIR"] - 1e-6 else "FAIL", src)
    if G["unknown_h"]:
        row("1", "parts whose footprint FP_H does not list",
            "; ".join("%s (%s): %.1f" % (ref, fp.replace("TS06_", ""), h) for ref, fp, h in G["unknown_h"]), "NOTE",
            "height from the footprint's descr, or %.0f if it states none; add the footprint to FP_H" % UNKNOWN_H)
    vl = G_lay["v"]
    h_l1 = next((p[3] for p in G["drv_parts"] if p[0] == "L1"), 0.0)
    row("1", "if U13, C7 and VT21 lie down (review finding 6)",
        "tallest becomes %.1f mm; rear panel %.1f mm further forward; outside depth %.1f"
        % (vl["PART_MAX"], v["Z_REAR_IN"] - vl["Z_REAR_IN"], vl["OUT_D"]), "NOTE",
        "the Nano (%.1f) and L1 (%.1f) then set the depth" % (v["NANO_H"], h_l1))

    # 2. the DC jack through the right cheek
    gap = v["X_IN_R"] - v["JACK_MOUTH_X"]
    eng_full = v["PLUG_BARREL_L"] - (gap + v["CHEEK_T"])
    eng_web = v["PLUG_BARREL_L"] - (gap + v["JACK_WEB"])
    row("2", "12 V plug engagement, plain 6 mm cheek",
        "%.1f mm (plug stops on the outer face %.1f mm from the jack mouth)" % (eng_full, gap + v["CHEEK_T"]),
        "FAIL" if eng_full < v["JACK_ENGAGE_MIN"] else "OK", "needs >= %.1f (assumed)" % v["JACK_ENGAGE_MIN"])
    row("2", "12 V plug engagement, Ø%g counterbore from OUTSIDE, %.1f mm web, Ø%g hole"
        % (v["JACK_CB_D"], v["JACK_WEB"], v["JACK_HOLE_D"]),
        "%.1f mm (nose Ø%g stops on the web)" % (eng_web, v["PLUG_NOSE_D"]),
        "OK" if eng_web >= v["JACK_ENGAGE_MIN"] else "FAIL",
        "implemented; a plug whose nose is under Ø%g reaches the jack face: %.1f mm"
        % (v["JACK_HOLE_D"], v["PLUG_BARREL_L"]))
    row("2", "review's 'Ø14 pocket from inside'",
        "%.1f mm - same as the plain cheek: the outer face does not move" % eng_full, "FAIL",
        "the pocket has to be on the outside; this model puts it there")
    cb_lo = v["JACK_Z"] - v["JACK_CB_D"] / 2
    row("2", "jack counterbore vs TS06-DRV / rear panel",
        "Ø%g at Y %.1f, Z %.2f: spans Z %.1f..%.1f; board %.1f..%.1f, rear panel %.1f"
        % (v["JACK_CB_D"], v["JACK_Y"], v["JACK_Z"], cb_lo, v["JACK_Z"] + v["JACK_CB_D"] / 2,
           v["Z_DRV_F"], v["Z_DRV_B"], v["Z_REAR_IN"]), "OK", "all in the cheek; the board edge is 0.5 mm inboard")

    # 3. USB
    intrude = v["X_IN_L"] - v["USB_X"]
    row("3", "Nano mini-B receptacle vs the left cheek",
        "protrudes %.1f mm into the cheek (to X %.1f); slot %g x %g, Y %.1f..%.1f, Z %.1f..%.1f"
        % (intrude, v["USB_X"], v["USB_SLOT_W"], v["USB_SLOT_H"], v["USB_Y"] - v["USB_SLOT_W"] / 2,
           v["USB_Y"] + v["USB_SLOT_W"] / 2, v["USB_Z"] - v["USB_SLOT_H"] / 2, v["USB_Z"] + v["USB_SLOT_H"] / 2),
        "OK", "overmould %g x %g passes with %.1f / %.1f mm a side"
        % (v["USB_PLUG_W"], v["USB_PLUG_H"], (v["USB_SLOT_W"] - v["USB_PLUG_W"]) / 2,
           (v["USB_SLOT_H"] - v["USB_PLUG_H"]) / 2))
    row("3", "module withdrawal past the USB receptacle",
        "a closed 12 x 9 window would trap the module (receptacle %.1f mm inside it); the slot runs open to "
        "the cheek's rear edge (Z %.1f), closed by the rear panel" % (intrude, v["Z_REAR_IN"]), "OK",
        "added here - not in the review")
    slot_top = v["USB_Y"] + v["USB_SLOT_W"] / 2
    near = [(y, z) for n, y, z in G["cheek_fix"]]
    dmin = min(math.hypot(max(0.0, abs(y - v["USB_Y"]) - v["USB_SLOT_W"] / 2),
                          max(0.0, (v["USB_Z"] - v["USB_SLOT_H"] / 2) - z, z - v["Z_REAR_IN"])) - v["CB_D"] / 2
               for y, z in near)
    row("3", "left cheek's screw holes vs the USB slot",
        "the rear panel no longer screws into the cheek; the nearest cheek counterbore (Ø%g) is %.1f mm from the slot "
        "(slot Y %.2f..%.2f)" % (v["CB_D"], dmin, v["USB_Y"] - v["USB_SLOT_W"] / 2, slot_top),
        "OK" if dmin >= 1.5 else "TIGHT", "")

    # 4. brow vs tube tops at the viewing angle
    th = math.radians(v["VIEW_DEG"])
    vis_depth = (v["SOFFIT_Y"] - v["IN12_TOP"]) / math.tan(th) - v["GLASS_RECESS"]
    dig_top = v["IN12_Y"] + v["IN12_DIGIT"] / 2
    lim_rear = math.degrees(math.atan((v["SOFFIT_Y"] - dig_top) / (v["IN12_D"] + v["GLASS_RECESS"])))
    row("4", "brow vs ИН-12 / ИН-15 glass top at %g° from above" % v["VIEW_DEG"],
        "soffit %.2f mm above the glass (Y %.2f vs %.2f); the glass top shows for its first %.1f of %.1f mm"
        % (v["SOFFIT_Y"] - v["IN12_TOP"], v["SOFFIT_Y"], v["IN12_TOP"], vis_depth, v["IN12_D"]), "NOTE",
        "the brow hides the dome/getter band behind that, as spec §6 'brow reveal' describes")
    runs = view_range(G, disp["IN12_X"][2], (v["IN12_D"], dig_top))
    row("4", "ИН-12 digit top (%.2f) at the rearmost cathode, from above" % dig_top,
        "seen up to %+.1f° (analytic %.1f°); frontmost cathode: %s"
        % (max(r[1] for r in runs), lim_rear, _fmt_runs(view_range(G, disp["IN12_X"][2], (0.0, dig_top)))),
        "OK" if lim_rear >= v["VIEW_DEG"] else "FAIL", "the digit clears the brow at %g° wherever the cathode "
                                                          "sits (depth to the digit plane is not captured)" % v["VIEW_DEG"])
    d17 = v["IN17_Y"] + v["IN17_DIGIT"] / 2
    row("4", "ИН-17 digit top (%.2f) at the glass rear (Z %g)" % (d17, v["IN17_D"]),
        _fmt_runs(view_range(G, disp["IN17_X"][0], (v["IN17_D"], d17))), "OK")

    # 5. what the brow, valance, sill and trench walls must hide
    zt = v["Z_DISP_F"] - v["PIN_TAIL"]
    xp12 = disp["parts"]["XP12"]["pads"]
    for label, x in (("over the ИН-17 pair (valance)", (v["VAL_X0"] + v["VAL_X1"]) / 2),
                     ("over the ИН-15 pair (no valance)", disp["IN15_X"][0])):
        r_ = view_range(G, x, (zt, xp12[2]))
        row("5", "XP12 joints (pad bottom Y %.2f) %s" % (xp12[2], label), _fmt_runs(r_),
            "OK" if not any(a <= v["VIEW_DEG"] and b >= -v["VIEW_DEG"] and b - a > 2 for a, b in r_) else "TIGHT",
            "over the ИН-15s the only line of sight is the %.1f mm slot between glass top and soffit"
            % (v["SOFFIT_Y"] - v["IN12_TOP"]) if "no valance" in label else "")
    for yy in (v["DISP_TOP_Y"] + 0.5, 95.0):
        r_ = view_range(G, 90.0, (v["Z_DRV_F"], yy))
        row("5", "TS06-DRV top band, front face at Y %.1f" % yy, _fmt_runs(r_),
            "OK" if not r_ or min(abs(a) for a, b in r_) > 40 else "TIGHT")
    xp2 = disp["parts"]["XP21"]["pads"]
    r_ = view_range(G, disp["parts"]["XP21"]["at"][0] + 2.54, (zt, xp2[3]))
    row("5", "XP21-25 joints (pad top Y %.2f) behind the sill (top Y %.1f)" % (xp2[3], v["SILL_TOP_Y"]),
        _fmt_runs(r_), "OK" if not r_ or min(abs(a) for a, b in r_) > 30 else "TIGHT")
    xps = [disp["parts"][k]["pads"][:2] for k in sorted(disp["parts"]) if k.startswith("XP2")]
    gx = min(max(a - pb, pa - b) for a, b in G["sill_leads"] for pa, pb in xps) if G["sill_leads"] else 99.0
    row("5", "sill lead-ins (F8) vs the XP21-25 pads behind the sill",
        "lead-ins only at X %s, where the lowest LEDs pass; %.2f mm from the nearest XP2x pad in X"
        % (", ".join("%.1f-%.1f" % s for s in G["sill_leads"]), gx), "OK" if gx >= 2.0 else "TIGHT",
        "a full-width 45° x %g lead-in would let the joints be seen from ~20° to ~52° above" % v["LEADIN"])
    xp11 = disp["parts"]["XP11"]["pads"]
    zc = v["Z_BACK"] - (v["LEADIN"] if G["wall_l_lead"] else 0.0)    # the wall's inner face ends here
    a_pad = math.degrees(math.atan((v["TRENCH_L_X"] - xp11[1]) / (v["Z_DISP_F"] - zc)))
    a_tip = math.degrees(math.atan((v["TRENCH_L_X"] - xp11[1]) / (v["Z_DISP_F"] - v["PIN_TAIL"] - zc)))
    a_tip0 = math.degrees(math.atan((v["TRENCH_L_X"] - xp11[1]) / (v["Z_DISP_F"] - v["PIN_TAIL"] - v["Z_BACK"])))
    row("5", "XP11 joints (pads X %.2f..%.2f) behind the left trench wall (X %.1f)" % (xp11[0], xp11[1], v["TRENCH_L_X"]),
        "hidden head-on and from the left; from the right past %.1f° (joint tip) / %.1f° (pad edge), "
        "and then only through H10's glass" % (a_tip, a_pad), "OK",
        "the wall's %g mm lead-in (F8) brings this down from %.1f° (joint tip)" % (v["LEADIN"], a_tip0)
        if G["wall_l_lead"] else "")

    # 6. clearances that are tight
    h10_l = disp["IN12_X"][0] - v["IN12_W"] / 2
    v10_r = disp["IN15_X"][1] + v["IN12_W"] / 2
    row("6", "left trench wall vs H10 glass", "%.3f mm nominal, %.3f mm with the +%.1f glass allowance"
        % (h10_l - v["TRENCH_L_X"], h10_l - v["TRENCH_L_X"] - v["GLASS_ALLOW"], v["GLASS_ALLOW"]),
        "TIGHT", "set by the review's 3 mm; the trench coupon test (cad library §5) decides it. Its rear edge "
        "has a 45° x %g lead-in (F8)" % v["LEADIN"])
    gap_r = v["TRENCH_R_X"] - v10_r
    row("6", "right trench wall vs ИН-15А (V10) glass", "%.3f mm nominal, %.3f mm with the +%.1f glass allowance"
        % (gap_r, gap_r - v["GLASS_ALLOW"], v["GLASS_ALLOW"]),
        "FAIL" if gap_r - v["GLASS_ALLOW"] < 0 else "TIGHT" if gap_r - v["GLASS_ALLOW"] < 0.5 - 1e-6 else "OK")
    led_lo = min(p["at"][1] for k, p in disp["parts"].items() if k.startswith("HL")) - v["LED_FLANGE_D"] / 2
    row("6", "sill top vs the lowest LED flange (HL5/HL6, under the ИН-17s)",
        "%.2f mm (flange bottom Y %.2f)" % (led_lo - v["SILL_TOP_Y"], led_lo), "TIGHT" if led_lo - v["SILL_TOP_Y"] < 1 else "OK",
        "the ИН-17 LEDs sit 1.0 lower than the ИН-12 ones. The sill's rear edge has a 45° x %g lead-in under them (F8)"
        % v["LEADIN"])
    row("6", "sill top vs the XP21-25 pads", "%.2f mm above the pad tops" % (v["SILL_TOP_Y"] - xp2[3]), "OK")
    in17_bot = v["IN17_Y"] - v["IN17_H"] / 2
    row("6", "sill / fascia top vs the lowest glass (ИН-17 bottom Y %.2f)" % in17_bot,
        "%.2f mm" % (in17_bot - v["SILL_TOP_Y"]), "OK")
    row("6", "case parts in front of TS06-DISP vs pin tails and screw heads",
        "%.1f mm gap; tails %.1f, low heads %.1f -> %.1f mm clear" % (v["BACK_GAP"], v["PIN_TAIL"], v["SCREW_HEAD"],
                                                                 v["BACK_GAP"] - max(v["PIN_TAIL"], v["SCREW_HEAD"])),
        "OK", "H3's head (X 50.5, Y 74.7) sits between H1 and M10 in plain view: black low-head screw")
    h8 = next(b for b in G["bosses"] if b[0] == "H8")
    row("6", "H8 boss vs TS06-DISP's top edge (the module slides past it)",
        "boss clipped to Y >= %.1f (hole at %.1f); %.1f mm behind TS06-DISP in Z"
        % (h8[3], h8[8], h8[5] - v["Z_DISP_B"]), "OK", "a symmetric 8 mm boss would overlap the board edge by 0.5")
    hole = {h[0]: h for h in G["drv_case_holes"]}
    rh = v["SCREW_HEAD_D"] / 2
    g8 = drv["parts"]["U1"]["box"][2] - (hole["H8"][2] + rh)
    g7 = (hole["H7"][2] - rh) - drv["parts"]["XS1"]["box"][3]
    row("6", "module screw heads (Ø%.1f) on the component face" % v["SCREW_HEAD_D"],
        "H8 vs the Nano's courtyard %.2f mm; H7 vs the jack's courtyard %.2f mm" % (g8, g7),
        "OK" if min(g8, g7) > 0.5 else "TIGHT")

    # 7. the module slides in and out along Z: nothing of the case may sit in the tubes' swept outline
    sweep = []
    sweep.append("soffit %.2f above the tall glass" % (v["SOFFIT_Y"] - v["IN12_TOP"]))
    sweep.append("valance X %.2f..%.2f between M1 (%.2f) and ИН-15Б (%.2f) glass, %.2f above the ИН-17 tops"
                 % (v["VAL_X0"], v["VAL_X1"], disp["IN12_X"][3] + v["IN12_W"] / 2, disp["IN15_X"][0] - v["IN12_W"] / 2,
                    v["VALANCE_Y0"] - v["IN17_TOP"]))
    sweep.append("sill %.2f under the lowest LED flange" % (led_lo - v["SILL_TOP_Y"]))
    row("7", "module withdrawal sweep (tubes, LEDs, TS06-DISP)", "; ".join(sweep), "OK",
        "a full-width valance down to Y %.1f would stop the ИН-12s coming out" % v["VALANCE_Y0"])
    li = v["LEADIN"]
    row("7", "lead-ins on the rear edges the module passes within %g mm (F8)" % v["LEADIN_BELOW"],
        "45° x %g: the soffit's rear edge (0.80 over the tall glass; a %.1f lip carries it), the left trench wall's "
        "inner rear edge (%.3f from H10), the sill's rear edge at X %s (%.2f under HL5/HL6's flanges); and the new "
        "trench blocks' rear top edges" % (li, v["SOFFIT_T"], h10_l - v["TRENCH_L_X"],
                                           ", ".join("%.1f-%.1f" % s for s in G["sill_leads"]), led_lo - v["SILL_TOP_Y"]),
        "OK", "the module rides up a lead-in if it comes in up to %g mm off" % li)
    blk = [b for b in G["blocks"] if b[0] == "trench"][0]
    row("7", "sweep past the new blocks (F7)",
        "trench blocks %.2f under H10's and ИН-15А's glass (X %.1f-%.1f and %.1f-%.1f); top plate's rear lip %.2f over "
        "TS06-DRV's top edge; base blocks and lip %.2f under its bottom edge"
        % (v["IN12_BOT"] - blk[2], G["block_x"][0], G["block_x"][1], v["X_IN_R"] - v["END_BLOCK"], v["X_IN_R"],
           v["TOP_LIP_Y0"] - v["DRV_TOP_Y"], v["DRV_BOT_Y"] - (v["Y_FLOOR"] + v["END_BLOCK"])),
        "OK", "the top lip keeps the review's %.1f, the same as each cheek; FR4 edge on plastic, not glass" % v["MOD_CLR"])

    # 8. the fascia lead
    row("8", "fascia J1 (side entry, lead towards the bottom edge) vs the floor",
        "lead's lowest point Y %.2f; floor put at Y %.1f - %.1f mm below the FreeCAD frame's 0, "
        "fascia's bottom edge %.1f above the floor" % (v["FJ_LOW_Y"], v["Y_FLOOR"], -v["Y_FLOOR"],
                                                        v["FAS_BOT_Y"] - v["Y_FLOOR"]), "NOTE",
        "this costs %.1f mm of height; a trough %.0f mm deep in the base under X %.0f-%.0f would save it"
        % (-v["Y_FLOOR"], -v["Y_FLOOR"] + 1, v["FASCIA_X0"] + fas["parts"]["J1"]["box"][0] - 2, v["FASCIA_X0"] + fas["parts"]["J1"]["box"][1] + 2))
    kick_clr = (v["FASCIA_T"] + 0.5) - v["KICK_T"]            # plug's near face 0.5 off the fascia's back
    row("8", "kick strip (%.1f thick) vs the mated fascia plug below the fascia's edge" % v["KICK_T"],
        "%.1f mm (plug's near face assumed 0.5 off the fascia's back)" % kick_clr,
        "TIGHT" if kick_clr < 1 else "OK")
    slack = v["LEAD_LEN"] - v["LEAD_PATH"]
    row("8", "fascia lead length", "path %.0f mm (plug to plug, diagonal on the floor) vs a %.0f mm lead: %.0f mm slack"
        % (v["LEAD_PATH"], v["LEAD_LEN"], slack), "TIGHT" if slack < 40 else "OK",
        "the module has to come back ~30 mm before DRV J1 can be reached from below; the BOM's 180-200 mm allows it")
    z_top = v["Z_DRV_F"] - v["J1_MATED_H"]
    for ref, x, t, a, b_, dep in G["bodies"]:
        cs = [G["fpt"](tt, ss) for tt in (t - b_ / 2, t + b_ / 2) for ss in (v["FASCIA_T"], v["FASCIA_T"] + dep)]
        zmax, ymax = max(c[1] for c in cs), max(c[0] for c in cs)
        name = {"SW1": "SR25 rotary", "SW2": "МТ1 lever", "SW3": "МТ1 lever", "SW4": "КМД1 button", "SW5": "КМД1 button"}[ref]
        if ref in ("SW3", "SW4"):
            continue
        res = "reaches Z %.1f (TS06-DRV at %.1f: %.1f clear%s), top Y %.2f" % (
            zmax, v["Z_DRV_F"], v["Z_DRV_F"] - zmax,
            "; DRV J1's mated plug at %.1f: %.1f clear" % (z_top, z_top - zmax) if ref == "SW1" else "", ymax)
        st = "OK"
        if ymax > v["SILL_TOP_Y"] - v["SILL_T"]:
            res += "; above the sill's underside (%.1f): sill stepped back to Z %.1f over X %.1f-%.1f" % (
                v["SILL_TOP_Y"] - v["SILL_T"], v["SILL_NOTCH_Z"], v["SILL_NOTCH_X0"], v["SILL_NOTCH_X1"])
            st = "TIGHT"
        size = "Ø%.2f" % a if ref == "SW1" else "%.2f x %.2f" % (a, b_)
        row("8", "%s %s body (%s, %.0f deep) behind the fascia" % (ref, name, size, dep), res, st,
            "the compressed fascia put the rotary's rim %.1f below its top edge; that leaves a %.1f mm slot behind the "
            "fascia's top edge, seen from above. The 19 mm rotary variant would clear the sill"
            % (t - b_ / 2, v["SILL_NOTCH_Z"] - v["Z_SILL_F"] + 0.2) if st != "OK" else
            "depth assumed")
    fh = [h for h in fas["holes"] if h[0] < 20 and h[1] > 20][0]
    r5 = fas["parts"]["R5"]["at"]
    # measured to R5's courtyard, which holds its pads and fillets: the boss presses on the fascia's back face
    r5_box = fas["parts"]["R5"]["box"]
    gap5 = r5_box[0] - (fh[0] + 3.5)
    row("8", "fascia boss at (%.1f, %.1f) vs R5 (1206, back face) at (%.1f, %.1f)" % (fh[0], fh[1], r5[0], r5[1]),
        "%.2f mm between a ±3.5 mm boss and R5's courtyard (pads and fillets)" % gap5,
        "FAIL" if gap5 < 0 else "TIGHT" if gap5 < 1.0 else "OK",
        "the boss lands on R5's pad: trim it on that side, move the hole, or move R5" if gap5 < 0 else "")
    # the top-right fascia hole and the КМД1 beside it
    sw5 = fas["parts"]["SW5"]["at"]
    hole = [h for h in fas["holes"] if h[0] > 100 and h[1] < 20][0]
    for a, b in ((v["KMD1_A"], v["KMD1_B"]), (v["KMD1_B"], v["KMD1_A"])):
        dx = max(0.0, hole[0] - (sw5[0] + a / 2))
        dy = max(0.0, (sw5[1] - b / 2) - hole[1])
        dist = math.hypot(dx, dy)
        row("8", "SW5 КМД1 body (%g across x %g down) vs the fascia hole at (%.1f, %.1f)" % (a, b, hole[0], hole[1]),
            "%.2f mm from the hole centre to the body; an M2.5 nut or insert boss needs ~3" % dist,
            "TIGHT" if dist < 3.0 else "OK", "the КМД1's orientation and third dimension are not captured")
    sl, sr = v["FASCIA_X0"] - v["X_IN_L"], v["X_IN_R"] - (v["FASCIA_X0"] + v["FASCIA_W"])
    row("8", "open slots beside the fascia, between its edges and the cheeks",
        "%.2f mm left, %.2f mm right, the fascia's full height: TS06-DRV shows through" % (sl, sr), "NOTE",
        "variant D closes them (section 12)")

    # 9. the ИН-17 stems against each other and against the glass either side, in the board plane
    p17 = disp["IN17_X"][1] - disp["IN17_X"][0]
    dy = abs(disp["IN12_Y"] - disp["IN17_Y"])
    rs, rg = v["IN17_STEM"] / 2, v["IN12_W"] / 2
    g_pair = p17 - 2 * rs
    g_m1 = math.hypot(disp["IN17_X"][0] - disp["IN12_X"][3], dy) - rs - rg
    g_15 = math.hypot(disp["IN15_X"][0] - disp["IN17_X"][1], dy) - rs - rg
    worst = min(g_pair, g_m1, g_15)
    row("9", "ИН-17 pair: centres %.3f apart, Ø%g stems" % (p17, v["IN17_STEM"]),
        "stem to stem %.2f mm; S10's stem to M1's glass %.2f; S1's stem to ИН-15Б's glass %.2f" % (g_pair, g_m1, g_15),
        "FAIL" if worst < 0 else "TIGHT" if worst < 0.5 else "OK",
        "Rev F's 20.5 (stem + 0.5); TS06-DISP was re-spaced to it on 29.09.26, having carried the "
        "FreeCAD 13.0 until then. The stem is the drawing's Ø20 (one caliper reading: 19.30): gate 5")

    # 10. the fixings (case review F7, F9)
    EB, ri = v["END_BLOCK"], v["INS_M3_D"] / 2
    bx = G["block_x"][1] - G["block_x"][0]
    for name, y0, y1, z0, z1, y, z in G["blocks"]:
        wall = min(y - y0, y1 - y, z - z0, z1 - z, bx - (v["INS_M3_L"] + 0.5) + ri) - ri
        ok = min(bx, y1 - y0, z1 - z0) >= EB - 1e-6 and wall >= v["INS_WALL_MIN"] - 1e-6
        row("10", "end blocks for the cheek screws into the %s" % name,
            "%.1f x %.1f x %.1f mm (X x Y x Z) at each cheek; M3 insert at Y %.2f, Z %.2f, %.2f mm of wall round it"
            % (bx, y1 - y0, z1 - z0, y, z, wall), "OK" if ok else "FAIL",
            {"base, front": "was a Ø3.4 hole at Y -8.8 on the edge of the 3 mm base",
             "top plate, front": "was a Ø3.4 hole at Y 108.5 on the edge of the 3 mm top bar",
             "trench": "was an M3 x 8 into the 3.5 mm left wall, its tip at X 3.5, 0.025 from H10's glass (3.475)"}
            .get(name, ""))
    groups = {}
    for s in G["screws"]:
        c, what = _screw_clear(G, s)
        g0 = groups.setdefault(s[0], [s[1], 0, 99.0, ""])
        g0[1] += 1
        if c < g0[2]:
            g0[2], g0[3] = c, what
    for name, (spec, n, c, what) in groups.items():
        row("10", "screw vs glass and boards: %s (%d x %s)" % (name, n, spec),
            "%.2f mm from %s at the closest" % (c, what), "OK" if c >= v["TIP_CLR_MIN"] - 1e-6 else "FAIL",
            "the whole shank, not only its tip; the boards it clamps are left out")
    span = v["X_IN_R"] - v["X_IN_L"]
    err = span * v["PRINT_SHRINK"] / 100
    row("10", "printed crossmembers set the cheek spacing, FR4 hole patterns span it (F9)",
        "%.1f mm between the cheeks: %.2f mm short at %.1f%% shrink; TS06-DRV's H5-H8 (Ø3.2 for M3) float 0.1 a side"
        % (span, err, v["PRINT_SHRINK"]), "NOTE",
        "screw the module in first, so the DRV locates the cheeks, then the crossmembers; scale the crossmembers "
        "+%.1f%% in X in the slicer. The rear panel's holes are slotted ±%.1f along X" % (v["PRINT_SHRINK"], v["SLOT_X"]))

    # 11. the rear panel (case review m4)
    xs = sorted({x for x, y in G["rear_screws"]})
    row("11", "rear panel fixings",
        "%d x M2.5: X %s, along the bottom (base lip, Y %.1f) and the top (top plate's lip, Y %.1f); longest free edge "
        "%.1f mm (was %.1f between the corner screws)"
        % (len(G["rear_screws"]), ", ".join("%.1f" % x for x in xs), v["FIX_BASE_Y"], v["FIX_TOP_Y"],
           max(b - a for a, b in zip(xs, xs[1:])), v["X_OUT_R"] - v["X_OUT_L"] - v["CHEEK_T"]), "OK",
        "none into the cheeks' side edges: see the next row")
    r25 = v["INS_M25_D"] / 2
    walls = []
    for part, (y0, y1, z0, z1) in G["rear_lips"].items():
        for x, y in G["rear_screws"]:
            if y0 <= y <= y1:
                walls.append((min(y - y0, y1 - y, x - v["X_IN_L"], v["X_IN_R"] - x) - r25, part))
    w, part = min(walls)
    row("11", "walls round the rear panel's M2.5 inserts (Ø%g)" % v["INS_M25_D"],
        "%.2f mm at the least (%s lip, %g deep)" % (w, part, EB), "OK" if w >= v["INS_WALL_MIN"] - 1e-6 else "FAIL",
        "in a cheek's 6 mm rear edge, where the corner screws were, the same insert has %.2f mm"
        % ((v["CHEEK_T"] - v["INS_M25_D"]) / 2))
    hv = _hv_under(G, v["VENT_X0"], v["VENT_X1"])
    hv_old = _hv_under(G, 100.0, 130.0)
    row("11", "rear-panel vents vs 185 V parts (a pad on an HV-class net in mkpcb_drv)",
        "%d slots at X %.1f-%.1f, Y %.0f-%.0f, over U1 (the Nano); %s within %g mm"
        % (len(G["vents"]), v["VENT_X0"], G["vents"][-1][1], v["VENT_Y0"], v["VENT_Y1"],
           ", ".join(hv) if hv else "no 185 V part", v["VENT_HV_CLR"]), "FAIL" if hv else "OK",
        "at X 100-130 the field sat over %s" % ", ".join(hv_old))
    row("11", "rear panel holes vs the print error (F9)",
        "Ø%g slotted ±%.1f along X; the lips' inserts drift up to %.2f at %.1f%% shrink"
        % (v["REAR_HOLE_D"], v["SLOT_X"], (xs[-1] - xs[0]) / 2 * v["PRINT_SHRINK"] / 100, v["PRINT_SHRINK"]),
        "OK", "")

    # 12. variant D: the fascia frame (FASCIA_FRAME=1)
    if G_ff is not None:
        R += checks_frame(G_ff)
    return R


def _glass_and_boards(G):
    """Glass (nominal envelopes) and boards, as world boxes (X0, X1, Y0, Y1, Z0, Z1); the fascia in its own raked
    frame (X, t, s)."""
    v = G["v"]
    out = []
    for nm, kind, x, y, w, h, z0, z1 in _tubes(G):
        if kind == "ИН-17":
            w = h = v["IN17_STEM"]
        out.append(("%s's glass" % nm, (x - w / 2, x + w / 2, y - h / 2, y + h / 2, z0, z1), False))
    for x, y in G["B"]["disp"]["COLON"]:
        rr = v["INS1_D"] / 2
        out.append(("an ИНС-1", (x - rr, x + rr, y - rr, y + rr, 2.0, v["Z_DISP_F"]), False))
    out.append(("TS06-DISP", (0, v["BOARD_W"], v["DISP_BOT_Y"], v["DISP_TOP_Y"], v["Z_DISP_F"], v["Z_DISP_B"]), False))
    out.append(("TS06-DRV", (0, v["BOARD_W"], v["DRV_BOT_Y"], v["DRV_TOP_Y"], v["Z_DRV_F"], v["Z_DRV_B"]), False))
    out.append(("TS06-FASCIA", (v["FASCIA_X0"], v["FASCIA_X0"] + v["FASCIA_W"], 0, v["FASCIA_H"], 0, v["FASCIA_T"]), True))
    if v["FASCIA_FRAME"]:
        ff = G["ff"]
        out.append(("TS06-FASCIA", (ff["px0"], ff["px1"], 0, v["FF_PANEL_H"], 0, v["FASCIA_T"]), True))
    return out


def _screw_clear(G, s):
    """Least distance from a screw's shank to glass or a board it does not pass through, and what that is."""
    v = G["v"]
    name, spec, p0, ax, L, dia, through = s
    r = math.radians(v["FASCIA_RAKE"])
    best = (99.0, "")
    for what, b, raked in _glass_and_boards(G):
        if what in through:
            continue
        m = 99.0
        for i in range(61):
            X, Y, Z = (p0[k] + ax[k] * L * i / 60 for k in range(3))
            if raked:
                dy, dz = v["SILL_TOP_Y"] - Y, Z - v["Z_FACE"]
                Y, Z = dy * math.cos(r) - dz * math.sin(r), dy * math.sin(r) + dz * math.cos(r)
            d = math.sqrt(max(b[0] - X, 0, X - b[1]) ** 2 + max(b[2] - Y, 0, Y - b[3]) ** 2 + max(b[4] - Z, 0, Z - b[5]) ** 2)
            m = min(m, d)
        if m - dia / 2 < best[0]:
            best = (m - dia / 2, what)
    return best


def _hv_under(G, x0, x1):
    """185 V parts whose courtyard comes within VENT_HV_CLR of a vent field X x0-x1, Y VENT_Y0-VENT_Y1."""
    v = G["v"]
    c = v["VENT_HV_CLR"]
    return sorted(ref for ref, p in G["B"]["drv"]["parts"].items()
                  if p.get("hv") and not p["back"] and p["box"][0] < x1 + c and p["box"][1] > x0 - c
                  and p["box"][2] < v["VENT_Y1"] + c and p["box"][3] > v["VENT_Y0"] - c)


def checks_frame(G):
    """Section 12: variant D, the fascia frame - what it changes against the cheek-boss mounting."""
    v, B = G["v"], G["B"]
    fas, ff = B["fascia"], G["ff"]
    R = []

    def row(what, result, status, note=""):
        R.append({"id": "12", "what": "D: " + what, "result": result, "status": status, "note": note})

    x0 = v["FASCIA_X0"]
    row("the frame",
        "a printed frame between the cheeks, raked %g°: pocket X %.3f-%.3f (continuing the trench walls) for a %g x %g "
        "panel; a rabbet ledge %g wide behind its sides and bottom, a top rail %g under the sill; ribs at X %s; the "
        "panel on 4 x M2.5 into bosses at (X, down the face) %s; one M3 from each cheek into the frame's end blocks; "
        "the sill tied down to the rib heads"
        % (v["FASCIA_RAKE"], ff["x0"], ff["x1"], v["FF_PANEL_W"], v["FF_PANEL_H"], v["FF_LEDGE"], v["FF_TOP"],
           ", ".join("%.1f" % x for x in ff["ribs"]), ", ".join("(%.1f, %.1f)" % h for h in ff["holes"])), "NOTE",
        "replaces the four bosses cantilevered from the cheeks. There is no 179 board yet: the 176 board stands in, at "
        "its own X %.3f-%.3f, and its holes do not meet the frame's" % (x0, x0 + v["FASCIA_W"]))
    # R5, against the boss for the panel's bottom-left screw and the left ledge
    r5 = fas["parts"]["R5"]["box"]
    r5x0, r5t0, r5t1 = r5[0] + x0, r5[2], r5[3]
    near = [(math.hypot(max(0.0, r5x0 - hx - 0.0, hx - (r5[1] + x0)), max(0.0, r5t0 - ht, ht - r5t1)) - ff["boss_r"], hx, ht)
            for hx, ht in ff["holes"]]
    g5, hx, ht = min(near)
    g5l = r5x0 - (ff["x0"] + v["FF_LEDGE"])
    row("fascia boss vs R5 (stand-in, back face)",
        "%.2f mm from the boss at (%.1f, %.1f) (Ø%.1f) to R5's courtyard; the left ledge %.2f from it"
        % (g5, hx, ht, 2 * ff["boss_r"], g5l), "FAIL" if g5 < 0 else "TIGHT" if g5 < 1.0 else "OK",
        "today, the cheek boss: -1.20 mm, on R5's pad (FAIL)")
    # SW5, against everything of the frame behind the panel
    sw5 = next(b for b in G["bodies"] if b[0] == "SW5")
    res, worst = [], 99.0
    for a, b in ((v["KMD1_A"], v["KMD1_B"]), (v["KMD1_B"], v["KMD1_A"])):
        bx0, bx1, bt0, bt1 = sw5[1] - a / 2, sw5[1] + a / 2, sw5[2] - b / 2, sw5[2] + b / 2
        d_rail = bt0 - v["FF_TOP"]
        d_ledge = (ff["x1"] - v["FF_LEDGE"]) - bx1
        d_boss = min(math.hypot(max(0.0, bx0 - hx, hx - bx1), max(0.0, bt0 - ht, ht - bt1)) - ff["boss_r"] for hx, ht in ff["holes"])
        d_rib = min(max(bx0 - (x + v["FF_RIB_W"] / 2), (x - v["FF_RIB_W"] / 2) - bx1) for x in ff["ribs"])
        m = min(d_rail, d_ledge, d_boss, d_rib)
        worst = min(worst, m)
        res.append("%g across: %.2f (top rail %.2f, right ledge %.2f, nearest boss %.2f)" % (a, m, d_rail, d_ledge, d_boss))
    row("SW5 КМД1 body vs the frame", "; ".join(res), "FAIL" if worst < 0 else "TIGHT" if worst < 1.0 else "OK",
        "today, the top-right cheek boss: 1.22 / 2.62 mm from its hole centre (TIGHT). The frame puts no screw in that "
        "corner: the panel's top screws sit over the ribs")
    # the slots beside the fascia
    sl0, sr0 = x0 - v["X_IN_L"], v["X_IN_R"] - (x0 + v["FASCIA_W"])
    fit = ((ff["x1"] - ff["x0"]) - v["FF_PANEL_W"]) / 2
    sl, sr = x0 - ff["x0"], ff["x1"] - (x0 + v["FASCIA_W"])
    row("slots beside the fascia",
        "the %g panel: %.3f a side; the 176 stand-in: %.2f left, %.2f right, with the frame's %g ledge behind both "
        "(it overlaps the stand-in by %.2f / %.2f), so TS06-DRV no longer shows"
        % (v["FF_PANEL_W"], fit, sl, sr, v["FF_LEDGE"], v["FF_LEDGE"] - sl, v["FF_LEDGE"] - sr),
        "OK" if min(v["FF_LEDGE"] - sl, v["FF_LEDGE"] - sr) > 0 else "FAIL",
        "today: %.2f left and %.2f right, open" % (sl0, sr0))
    row("the %g panel in the pocket" % v["FF_PANEL_W"],
        "pocket %.3f wide (the trench walls' X): %.4f mm a side" % (ff["x1"] - ff["x0"], fit),
        "TIGHT" if fit < 0.15 else "OK", "a printed pocket wants ~0.2 a side: make the board 178.6, or ease the pocket's "
                                         "sides by 0.2 and let the seam sit 0.2 off the walls")
    # ribs and bosses against what stands behind the stand-in
    gaps = []
    for x in ff["ribs"]:
        for a, b, ref in ff["keep"]:
            gaps.append((max(a - (x + max(v["FF_RIB_W"] / 2, ff["boss_r"])), (x - max(v["FF_RIB_W"] / 2, ff["boss_r"])) - b), ref, x))
    g, ref, x = min(gaps)
    row("ribs (with their boss and tie heads) vs the stand-in's controls and back-side parts",
        "%.2f mm, the rib at X %.1f to %s" % (g, x, ref), "OK" if g >= 1.0 else "TIGHT" if g >= 0 else "FAIL",
        "set in the two widest gaps between the stand-in's parts; the 179 board has to leave them free")
    row("frame vs the rotary and the fascia's J1",
        "top rail cut over X %.1f-%.1f, as the sill is (the rotary's rim); bottom ledge cut over X %.1f-%.1f for J1's "
        "plug and lead" % (ff["rot_notch"] + ff["j1_notch"]), "OK", "")
    row("the sill",
        "bears on the frame's top rail across the width (not over the rotary) and is screwed down into the %d rib "
        "heads (M2.5, countersunk into the sill's top)" % len(ff["ribs"]), "OK",
        "assemble the frame and the trench on the bench first, then fit them between the cheeks")
    # the frame's own fixings: its end blocks, and every screw that is new or moved
    EB, ri = v["END_BLOCK"], v["INS_M3_D"] / 2
    wall = min(EB / 2, EB) - ri
    row("end blocks for the cheek screws into the frame",
        "%.1f x %.1f x %.1f mm (X x down the face x behind the panel); M3 insert at Y %.2f, Z %.2f, %.2f mm of wall"
        % (EB, 2 * EB, EB, v["FF_FIX_Y"], v["FF_FIX_Z"], wall), "OK" if wall >= v["INS_WALL_MIN"] else "FAIL", "")
    groups = {}
    for s in G["screws"]:
        if "frame" not in s[0]:
            continue
        c, what = _screw_clear(G, s)
        g0 = groups.setdefault(s[0], [s[1], 0, 99.0, ""])
        g0[1] += 1
        if c < g0[2]:
            g0[2], g0[3] = c, what
    for name, (spec, n, c, what) in groups.items():
        row("screw vs glass and boards: %s (%d x %s)" % (name, n, spec), "%.2f mm from %s at the closest" % (c, what),
            "OK" if c >= v["TIP_CLR_MIN"] - 1e-6 else "FAIL", "the stand-in and the 179 outline both counted")
    return R


# ============================================================================ params.scad
def write_scad(G, d, path):
    v, B = G["v"], G["B"]
    L = ["// params.scad - GENERATED by case_pair.py from boards.json and the DIMS table. Do not edit:",
         "// change case_pair.py (or pass -D NAME=value to openscad for a quick what-if) and regenerate.",
         "// World frame: X across the front from the clock's left, Y up (FreeCAD assembly), Z depth",
         "// from the ИН-12 glass front, + toward the back. case.scad maps x = X, y = Z, z = Y.",
         "// Kinds: board = read from the board files; doc = stated in a repo document; design = chosen",
         "// here; assumed = typical value, not yet measured.", ""]
    grp = None
    for name, value, kind, src, g in d.rows:
        if g != grp:
            L += ["", "// ---- %s" % g]
            grp = g
        L.append("%-18s = %s;  // [%s] %s" % (name, _scad(value), kind, src))
    L += ["", "// ---- read from the boards (world coordinates)"]
    disp, drv, fas = B["disp"], B["drv"], B["fascia"]
    L.append("IN12_X   = %s;  // board: mkpcb_disp IN12_X (H10 H1 M10 M1)" % _scad(disp["IN12_X"]))
    L.append("IN15_X   = %s;  // board: mkpcb_disp IN15_X (ИН-15Б, ИН-15А)" % _scad(disp["IN15_X"]))
    L.append("IN17_X   = %s;  // board: mkpcb_disp IN17_X (S10, S1)" % _scad(disp["IN17_X"]))
    L.append("IN12_Y   = %s;  // board: TOP - Y12" % _scad(disp["IN12_Y"]))
    L.append("IN17_Y   = %s;  // board: TOP - Y17" % _scad(disp["IN17_Y"]))
    L.append("COLON    = %s;  // board: V7, V8 (ИНС-1)" % _scad(disp["COLON"]))
    L.append("LEDS     = %s;  // board: HL1-HL9" % _scad(sorted(p["at"] for k, p in disp["parts"].items() if k.startswith("HL"))))
    L.append("DISP_HOLES = %s;  // board: mkpcb_disp H1-H4 (M3, the standoffs)" % _scad([h[:2] for h in disp["holes"]]))
    L.append("DRV_CASE_HOLES = %s;  // board: mkpcb_drv HOLES H5-H8 -> cheeks" % _scad([h[1:3] for h in G["drv_case_holes"]]))
    strips = [[k] + p["box"] for k, p in sorted(disp["parts"].items()) if k.startswith("XP")]
    L.append("DISP_STRIPS = %s;  // board: XP courtyards [ref, X0, X1, Y0, Y1]" % _scad(strips))
    parts = [[ref, box[0], box[1], box[2], box[3], round(h, 2), side] for ref, fp, box, h, side, src in G["drv_parts"]]
    L.append("// TS06-DRV parts [ref, X0, X1, Y0, Y1, height, side]: side 0 = component face (to the rear),")
    L.append("// 1 = display face. Boxes are courtyards; heights per case_pair.py FP_H (kind in checks.md).")
    L.append("DRV_PARTS = [")
    for p in parts:
        L.append("  %s," % _scad(p))
    L.append("];")
    L.append("NANO_BOX  = %s;  // board: U1 courtyard [X0, X1, Y0, Y1] (USB end at X0)" % _scad(drv["parts"]["U1"]["box"]))
    rows = sorted({p[2] for p in drv["parts"]["U1"]["pads"]})
    L.append("NANO_ROWS_Y = %s;  // board: U1 pad rows (world Y); the mini-B sits midway" % _scad([rows[0], rows[-1]]))
    L.append("JACK_PIN1 = %s;  // board: XS1 pin 1 [X, Y]" % _scad(next(p[1:] for p in drv["parts"]["XS1"]["pads"] if p[0] == "1")))
    L.append("J1_BOX    = %s;  // board: DRV J1 courtyard (display face)" % _scad(drv["parts"]["J1"]["box"]))
    L.append("FASCIA_HOLES = %s;  // board: TS06-FASCIA [x, y, drill], fascia frame (y down from top)" % _scad(fas["holes"]))
    ctl = [[k, p["at"][0], p["at"][1], p["panel_hole"]] for k, p in sorted(fas["parts"].items()) if k.startswith("SW")]
    L.append("FASCIA_CTRL  = %s;  // board: SW1-SW5 [ref, x, y, panel hole]" % _scad(ctl))
    L.append("FJ_BOX       = %s;  // board: fascia J1 courtyard [x0, x1, y0, y1], back face" % _scad(fas["parts"]["J1"]["box"]))
    L.append("LEAD = %s;  // derived: fascia lead centre line [X, Y, Z]" % _scad([[round(c, 2) for c in p] for p in G["lead"]]))
    ff = G["ff"]
    L.append("FF_RIB_X = %s;  // derived (variant D): the frame's ribs, in the two widest gaps between the stand-in's "
             "controls and back-side parts" % _scad(ff["ribs"]))
    L.append("FF_HOLES = %s;  // derived (variant D): the 179 panel's M2.5 holes [X, down the face]: over the ribs, and "
             "its bottom corners" % _scad([[round(c, 3) for c in h] for h in ff["holes"]]))
    L += ["", "// ---- derived in case_pair.py; case.scad derives the same and echoes it for comparison"]
    for k in ("Z_DISP_F", "Z_DRV_B", "PART_MAX", "Z_REAR_IN", "SOFFIT_Y", "Y_FLOOR", "Z_TOE", "OUT_W", "OUT_H", "OUT_D",
              "SILL_NOTCH_Z", "SILL_NOTCH_X0", "FIX_BASE_Y", "WALL_BLK_Y0", "WALL_BLK_Y1", "FIX_BROW_Y", "FIX_BROW_Z",
              "FIX_TOP_Y", "TOP_LIP_Y0", "FF_FIX_Y", "FF_FIX_Z"):
        L.append("PY_%-12s = %s;" % (k, _scad(round(v[k], 3))))
    L.append("PY_%-12s = %s;" % ("SILL_LEAD_X0", _scad(round(G["sill_leads"][0][0], 3))))
    L.append("PY_%-12s = %s;" % ("REAR_SCREWS", _scad(len(G["rear_screws"]))))
    with open(path, "w", encoding="utf8") as fh:
        fh.write("\n".join(L) + "\n")


def _scad(x):
    if isinstance(x, bool):
        return "true" if x else "false"
    if isinstance(x, (int, float)):
        return ("%.4f" % x).rstrip("0").rstrip(".") if isinstance(x, float) else str(x)
    if isinstance(x, str):
        return '"%s"' % x
    if isinstance(x, (list, tuple)):
        return "[" + ", ".join(_scad(e) for e in x) + "]"
    raise TypeError(x)


# ============================================================================ drawings
INK, MUTE, DIM, RED, AMB = "#1F2328", "#6E7781", "#2F6DB5", "#CF222E", "#B35900"
CASE, CASE_CUT, BRIGHT = "#D0D7DE", "#8C959F", "#F59E42"
BOARD, BOARD_E, GLASS, GLASS_E = "#2D333B", "#57606A", "#FFE3C2", "#D9822B"
PART, PHANTOM = "#AFC2D5", "#8250DF"
FONT = "DejaVu Sans, Arial, Helvetica, sans-serif"


class Sheet:
    """A drawing at 1:1 in mm. f(u, w) maps model coordinates to the sheet."""

    def __init__(self, w, h, title, sub, f):
        self.w, self.h, self.title, self.sub, self.f, self.o = w, h, title, sub, f, []

    def P(self, pts):
        return " ".join("%.2f,%.2f" % self.f(*p) for p in pts)

    def poly(self, pts, fill="none", stroke=INK, sw=0.3, dash=None, op=None, close=True):
        tag = "polygon" if close else "polyline"
        extra = (' stroke-dasharray="%s"' % dash if dash else "") + (' fill-opacity="%s"' % op if op is not None else "")
        self.o.append('<%s points="%s" fill="%s" stroke="%s" stroke-width="%.2f" stroke-linejoin="round"%s/>'
                      % (tag, self.P(pts), fill, stroke, sw, extra))

    def box(self, u0, u1, w0, w1, **k):
        self.poly([(u0, w0), (u1, w0), (u1, w1), (u0, w1)], **k)

    def circle(self, u, w, r, fill="none", stroke=INK, sw=0.3, dash=None):
        x, y = self.f(u, w)
        self.o.append('<circle cx="%.2f" cy="%.2f" r="%.2f" fill="%s" stroke="%s" stroke-width="%.2f"%s/>'
                      % (x, y, r, fill, stroke, sw, ' stroke-dasharray="%s"' % dash if dash else ""))

    def line(self, a, b, stroke=INK, sw=0.25, dash=None):
        self.poly([a, b], stroke=stroke, sw=sw, dash=dash, close=False)

    def text(self, u, w, s, size=2.6, fill=INK, anchor="start", weight="400", raw=False, rot=0):
        x, y = (u, w) if raw else self.f(u, w)
        t = ' transform="rotate(%g %.2f %.2f)"' % (rot, x, y) if rot else ""
        s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        self.o.append('<text x="%.2f" y="%.2f" font-family="%s" font-size="%.2f" fill="%s" text-anchor="%s" '
                      'font-weight="%s"%s>%s</text>' % (x, y, FONT, size, fill, anchor, weight, t, s))

    def label(self, at, to, s, col=INK, size=2.5, anchor="start"):
        """A leader from model point `at` to model point `to`, text at `to`."""
        (x0, y0), (x1, y1) = self.f(*at), self.f(*to)
        self.o.append('<polyline points="%.2f,%.2f %.2f,%.2f" fill="none" stroke="%s" stroke-width="0.2"/>'
                      % (x0, y0, x1, y1, col))
        self.o.append('<circle cx="%.2f" cy="%.2f" r="0.5" fill="%s"/>' % (x0, y0, col))
        dx = 1.0 if anchor == "start" else -1.0
        self.text(x1 + dx, y1 + size * 0.35, s, size, col, anchor, raw=True)

    def dim(self, a, b, off, s, horiz=True, col=DIM, size=2.4):
        """Dimension between model points a and b, offset `off` mm on the sheet (perpendicular)."""
        (xa, ya), (xb, yb) = self.f(*a), self.f(*b)
        if horiz:
            y = ya + off
            segs = [(xa, ya, xa, y), (xb, yb, xb, y), (xa, y, xb, y)]
            tx, ty, rot = (xa + xb) / 2, y - 0.8, 0
        else:
            x = xa + off
            segs = [(xa, ya, x, ya), (xb, yb, x, yb), (x, ya, x, yb)]
            tx, ty, rot = x - 0.8, (ya + yb) / 2, -90
        for i, (p, q, r_, t_) in enumerate(segs):
            self.o.append('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="%s" stroke-width="%.2f"%s/>'
                          % (p, q, r_, t_, col, 0.2 if i < 2 else 0.25, ' stroke-dasharray="0.6 0.6"' if i < 2 else ""))
        for (px, py) in ((segs[2][0], segs[2][1]), (segs[2][2], segs[2][3])):
            self.o.append('<circle cx="%.2f" cy="%.2f" r="0.45" fill="%s"/>' % (px, py, col))
        self.text(tx, ty, s, size, col, "middle", raw=True, rot=rot)

    def svg(self, notes=()):
        head = ['<rect x="0" y="0" width="%.1f" height="%.1f" fill="#FFFFFF"/>' % (self.w, self.h)]
        head.append('<text x="8" y="10" font-family="%s" font-size="5" font-weight="700" fill="%s">%s</text>'
                    % (FONT, INK, self.title))
        head.append('<text x="8" y="16" font-family="%s" font-size="2.8" fill="%s">%s</text>' % (FONT, MUTE, self.sub))
        foot = []
        for i, n in enumerate(notes):
            foot.append('<text x="8" y="%.1f" font-family="%s" font-size="2.4" fill="%s">%s</text>'
                        % (self.h - 4 - 3.4 * (len(notes) - 1 - i), FONT, MUTE, n.replace("&", "&amp;").replace("<", "&lt;")))
        return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %.1f %.1f" width="%.0f" height="%.0f">\n%s\n</svg>\n'
                % (self.w, self.h, self.w * 4, self.h * 4, "\n".join(head + self.o + foot)))


def _tubes(G):
    v, disp = G["v"], G["B"]["disp"]
    out = []
    for nm, x in zip(("H10", "H1", "M10", "M1"), disp["IN12_X"]):
        out.append((nm, "ИН-12", x, v["IN12_Y"], v["IN12_W"], v["IN12_H"], 0.0, v["IN12_D"]))
    for nm, x in zip(("S10", "S1"), disp["IN17_X"]):
        out.append((nm, "ИН-17", x, v["IN17_Y"], v["IN17_FACE"], v["IN17_H"], 0.0, v["IN17_D"]))
    for nm, x in zip(("AM", "PM"), disp["IN15_X"]):
        out.append((nm, "ИН-15", x, v["IN12_Y"], v["IN12_W"], v["IN12_H"], 0.0, v["IN12_D"]))
    return out


def draw_front(G):
    v, disp, fas = G["v"], G["B"]["disp"], G["B"]["fascia"]
    M, MT = 34.0, 26.0
    W, H = v["OUT_W"] + 2 * M + 30, v["OUT_H"] + MT + 44
    f = lambda X, Y: (X - v["X_OUT_L"] + M, v["Y_TOP"] - Y + MT)
    S = Sheet(W, H, "TS06 PAIR CASE - FRONT ELEVATION  1:1",
              "concept A · outside %.1f W x %.1f H x %.1f D mm · world X/Y of the FreeCAD assembly"
              % (v["OUT_W"], v["OUT_H"], v["OUT_D"]), f)
    r = math.radians(v["FASCIA_RAKE"])
    for x0, x1 in ((v["X_OUT_L"], v["X_IN_L"]), (v["X_IN_R"], v["X_OUT_R"])):
        S.box(x0, x1, v["Y_BOT"], v["Y_TOP"], fill=CASE, sw=0.35)
    S.box(v["X_IN_L"], v["X_IN_R"], v["Y_BOT"], v["Y_FLOOR"], fill=CASE)
    S.box(v["X_IN_L"], v["X_IN_R"], v["Y_FLOOR"], v["FAS_BOT_Y"], fill="#BFC7CF")
    # fascia, projected (raked 12°: 40 along the face is 39.1 tall)
    X0 = v["FASCIA_X0"]
    S.box(X0, X0 + v["FASCIA_W"], v["FAS_BOT_Y"], v["SILL_TOP_Y"], fill=BOARD, stroke=BOARD_E)
    names = {"SW1": "MODE", "SW2": "FIELD", "SW3": "SUB", "SW4": "−", "SW5": "+"}
    for ref, p in sorted(fas["parts"].items()):
        if not ref.startswith("SW"):
            continue
        fx, fy = p["at"]
        fx += X0
        yy = v["SILL_TOP_Y"] - fy * math.cos(r)
        S.circle(fx, yy, (p["panel_hole"] or 8) / 2 + (4.5 if ref == "SW1" else 1.2), fill="#57606A", stroke="#8C959F")
        S.text(fx, yy - 11.5 if ref != "SW1" else yy - 16, "%s %s" % (ref, names[ref]), 2.2, "#E6EDF3", "middle")
    for hx, hy, dd in fas["holes"]:
        S.circle(X0 + hx, v["SILL_TOP_Y"] - hy * math.cos(r), dd / 2, fill="#1F2328", stroke="#8C959F", sw=0.2)
    fj = fas["parts"]["J1"]["box"]
    S.box(X0 + fj[0], X0 + fj[1], v["SILL_TOP_Y"] - fj[3] * math.cos(r), v["SILL_TOP_Y"] - fj[2] * math.cos(r),
          stroke=PHANTOM, dash="1 0.8", sw=0.25)
    # the window: TS06-DISP behind the tubes
    S.box(v["TRENCH_L_X"], v["TRENCH_R_X"], v["SILL_TOP_Y"], v["SOFFIT_Y"], fill=BOARD, stroke=BOARD_E)
    for x, y in [p["at"] for k, p in disp["parts"].items() if k.startswith("HL")]:
        S.circle(x, y, v["LED_D"] / 2, fill="#F7C873", stroke="#9A6700", sw=0.2)
    for x, y in disp["COLON"]:
        S.circle(x, y, v["INS1_D"] / 2, fill=GLASS, stroke=GLASS_E, sw=0.3)
    hx, hy, _ = disp["holes"][2]
    S.circle(hx, hy, v["SCREW_HEAD_D"] / 2, fill="#0D1117", stroke="#8C959F", sw=0.2)
    glyph = {"H10": "1", "H1": "2", "M10": "3", "M1": "4", "S10": "5", "S1": "6", "AM": "A", "PM": "P"}
    for nm, kind, x, y, w, h, z0, z1 in _tubes(G):
        S.box(x - w / 2, x + w / 2, y - h / 2, y + h / 2, fill=GLASS, stroke=GLASS_E, sw=0.35, op=0.9)
        dg = v["IN17_DIGIT"] if kind == "ИН-17" else v["IN12_DIGIT"]
        S.text(x, y - dg / 2 + 0.2, glyph[nm], dg * 1.28, "#E8590C", "middle", "300")
    # trench walls, the blocks under H10 and ИН-15А (F7), and the brow
    S.box(v["X_IN_L"], v["TRENCH_L_X"], v["SILL_TOP_Y"], v["SOFFIT_Y"], fill=CASE)
    S.box(v["TRENCH_R_X"], v["X_IN_R"], v["SILL_TOP_Y"], v["SOFFIT_Y"], fill=CASE)
    S.box(v["X_IN_L"], v["X_IN_L"] + v["END_BLOCK"], v["SILL_TOP_Y"], v["WALL_BLK_Y1"], fill=CASE)
    S.box(v["X_IN_L"], v["X_IN_R"], v["SOFFIT_Y"], v["Y_TOP"], fill=BRIGHT, stroke=INK, sw=0.35)
    # hidden: the boards, the bosses, the openings at the ends
    S.box(0, v["BOARD_W"], v["DRV_BOT_Y"], v["DRV_TOP_Y"], stroke=MUTE, dash="1.2 0.8", sw=0.2)
    S.box(0, v["BOARD_W"], v["DISP_BOT_Y"], v["DISP_TOP_Y"], stroke=MUTE, dash="1.2 0.8", sw=0.2)
    for b in G["bosses"]:
        S.box(b[1], b[2], b[3], b[4], stroke=MUTE, dash="0.8 0.6", sw=0.2)
        S.circle(b[7], b[8], 1.6, stroke=MUTE, dash="0.6 0.4", sw=0.2)
    S.circle(v["X_OUT_R"] - v["CHEEK_T"] / 2, v["JACK_Y"], v["JACK_HOLE_D"] / 2, stroke=RED, dash="0.8 0.6", sw=0.25)
    S.box(v["X_OUT_L"], v["X_IN_L"], v["USB_Y"] - v["USB_SLOT_W"] / 2, v["USB_Y"] + v["USB_SLOT_W"] / 2,
          stroke=RED, dash="0.8 0.6", sw=0.25)
    S.label((v["X_OUT_R"] - 3, v["JACK_Y"]), (v["X_OUT_R"] + 6, v["JACK_Y"] + 6), "12 V jack, right cheek", RED, 2.2)
    S.label((v["X_OUT_L"] + 3, v["USB_Y"]), (v["X_OUT_L"] - 6, v["USB_Y"] + 10), "USB, left cheek", RED, 2.2, "end")
    # labels
    S.label((140, 100), (140, v["Y_TOP"] + 6), "brow (safety orange, spec §6) hides TS06-DRV's top band; black top "
            "plate behind it", INK, 2.4)
    S.label((1.5, 60), (-20, 66), "trench wall", INK, 2.2, "end")
    S.label((20, 16), (20, v["Y_BOT"] - 6), "TS06-FASCIA %g x %g, raked %g°, 4 x M2.5 x 6"
            % (v["FASCIA_W"], v["FASCIA_H"], v["FASCIA_RAKE"]), INK, 2.2)
    S.label((100, (v["Y_FLOOR"] + v["FAS_BOT_Y"]) / 2), (100, v["Y_BOT"] - 6), "kick strip (base)", INK, 2.2)
    # dimensions
    yb = v["Y_BOT"]
    S.dim((v["X_OUT_L"], yb), (v["X_OUT_R"], yb), 22, "%.1f outside" % v["OUT_W"])
    S.dim((v["X_IN_L"], yb), (v["X_IN_R"], yb), 15, "%.1f between cheeks" % (v["X_IN_R"] - v["X_IN_L"]))
    S.dim((v["TRENCH_L_X"], v["SOFFIT_Y"]), (v["TRENCH_R_X"], v["SOFFIT_Y"]), -3,
          "trench window %.1f x %.1f" % (v["TRENCH_R_X"] - v["TRENCH_L_X"], v["SOFFIT_Y"] - v["SILL_TOP_Y"]))
    xr = v["X_OUT_R"]
    chain = [v["Y_BOT"], v["Y_FLOOR"], v["FAS_BOT_Y"], v["SILL_TOP_Y"], v["SOFFIT_Y"], v["Y_TOP"]]
    for a, b in zip(chain, chain[1:]):
        S.dim((xr, a), (xr, b), 9, "%.1f" % (b - a), horiz=False)
    S.dim((v["X_OUT_L"], v["Y_BOT"]), (v["X_OUT_L"], v["Y_TOP"]), -12, "%.1f outside" % v["OUT_H"], horiz=False)
    S.dim((v["X_OUT_L"], v["DRV_BOT_Y"]), (v["X_OUT_L"], v["DRV_TOP_Y"]), -24, "TS06-DRV %g" % v["DRV_H"], horiz=False)
    return S.svg(["Hidden (dashed): TS06-DRV Y %g-%g and TS06-DISP Y %g-%g outlines, the four module bosses (H5-H8), "
                  "the jack and USB openings in the cheeks, the fascia connector J1 (violet)."
                  % (v["DRV_BOT_Y"], v["DRV_TOP_Y"], v["DISP_BOT_Y"], v["DISP_TOP_Y"]),
                  "Chain on the right, bottom up: base, kick strip, fascia (projected), trench window, brow. "
                  "Fascia centred under the tube row, X %.1f-%.1f (the FreeCAD assembly has it elsewhere: review 5)."
                  % (v["FASCIA_X0"], v["FASCIA_X0"] + v["FASCIA_W"]),
                  "The grey step under H10 is the trench's end block (%g mm, an M3 x %g from the cheek into its insert); "
                  "its twin under ИН-15А sits inside the right wall." % (v["END_BLOCK"], v["SCREW_M3_L"])])


def draw_section(G):
    v, B = G["v"], G["B"]
    disp, drv = B["disp"], B["drv"]
    xs = disp["IN12_X"][2]                                       # M10's centre line
    M, MT = 58.0, 26.0
    W, H = v["OUT_D"] + 2 * M + 70, v["OUT_H"] + MT + 44
    f = lambda Z, Y: (Z - v["Z_TOE"] + M, v["Y_TOP"] - Y + MT)
    S = Sheet(W, H, "SECTION A-A AT X = %.2f (M10), LOOKING AT THE LEFT CHEEK  1:1" % xs,
              "the stack front to back · cut parts filled · beyond / phantom dashed · sight lines at ±%g°" % v["VIEW_DEG"], f)
    S.poly(G["cheek"], fill="#F3F5F7", stroke=MUTE, sw=0.25)
    S.box(v["USB_Z"] - v["USB_SLOT_H"] / 2, v["Z_REAR_IN"], v["USB_Y"] - v["USB_SLOT_W"] / 2,
          v["USB_Y"] + v["USB_SLOT_W"] / 2, fill="#FFFFFF", stroke=RED, sw=0.25, dash="0.8 0.5")
    S.text(v["USB_Z"] - v["USB_SLOT_H"] / 2 + 0.4, v["USB_Y"] + v["USB_SLOT_W"] / 2 - 2.4, "USB slot", 2.0, RED)
    for b in G["bosses"]:
        if b[7] < 88:
            S.box(b[5], b[6], b[3], b[4], fill="#E3E8ED", stroke=MUTE, sw=0.25)
            S.text(b[5] + 0.5, b[4] + 1.0, "boss " + b[0], 1.8, MUTE)
    # beyond the cut, at the left cheek: the end blocks (F7), and the cheek screws M3 x 8 into their inserts
    for name, y0, y1, z0, z1, y, z in G["blocks"]:
        S.box(z0, z1, y0, y1, fill="#E3E8ED", stroke=MUTE, sw=0.2, dash="0.8 0.5")
    for name, y, z in G["cheek_fix"]:
        S.circle(z, y, v["CB_D"] / 2, stroke=RED, sw=0.25)
        S.circle(z, y, v["CLR_M3"] / 2, fill="#FFFFFF", stroke=RED, sw=0.25)
    rc = v["CB_D"] / 2
    where = {"base, front": (0, rc + 1.2, "middle"), "base, rear": (0, rc + 1.2, "middle"),
             "trench": (0, -rc - 2.4, "middle"), "brow": (0, -rc - 2.4, "middle"),
             "top plate, front": (0, -rc - 2.4, "middle"), "top plate, rear": (-rc - 1.0, -0.7, "end")}
    for name, y, z in G["cheek_fix"]:
        dz, dy, anc = where.get(name, (0, -rc - 2.4, "middle"))
        S.text(z + dz, y + dy, "M3 x %g" % v["SCREW_M3_L"], 1.8, RED, anc)
    # cut: the case
    S.poly(G["base"], fill=CASE_CUT, sw=0.3)
    for part, (y0, y1, z0, z1) in G["rear_lips"].items():          # the rear lips run the full width: cut here
        S.box(z0, z1, y0, y1, fill=CASE_CUT if part == "base" else "#57606A", sw=0.3)
    S.poly(G["fascia"], fill=BOARD, stroke=BOARD_E, sw=0.3)
    S.poly(sill_profile(G, disp["IN12_X"][2]), fill=CASE_CUT, sw=0.3)
    S.poly(G["brow"], fill=BRIGHT, sw=0.3)
    S.poly(G["top"], fill="#57606A", sw=0.3)
    S.box(v["Z_REAR_IN"], v["Z_REAR_OUT"], v["Y_BOT"], v["Y_TOP"], fill=BOARD, stroke=BOARD_E, sw=0.3)
    for x, y in G["rear_screws"][:1] + G["rear_screws"][3:4]:     # the rear panel's screws (beyond, at X 3.5)
        S.box(v["Z_REAR_OUT"] - v["SCREW_M25_L"], v["Z_REAR_OUT"], y - 1.25, y + 1.25, stroke=RED, sw=0.25, dash="0.6 0.4")
        S.text(v["Z_REAR_OUT"] - 1, v["Y_TOP"] + 1.5 if y > 0 else v["Y_BOT"] - 3.2,
               "rear panel: 3 x M2.5 x %g along this edge" % v["SCREW_M25_L"], 1.8, RED, "end")
    # cut: the stack
    S.box(v["Z_DISP_F"], v["Z_DISP_B"], v["DISP_BOT_Y"], v["DISP_TOP_Y"], fill="#2E7D5B", stroke=INK, sw=0.25)
    S.box(v["Z_DRV_F"], v["Z_DRV_B"], v["DRV_BOT_Y"], v["DRV_TOP_Y"], fill="#2E7D5B", stroke=INK, sw=0.25)
    S.box(0, v["IN12_D"], v["IN12_BOT"], v["IN12_TOP"], fill=GLASS, stroke=GLASS_E, sw=0.35)
    S.box(v["IN12_D"], v["Z_DISP_F"], v["IN12_Y"] - 8.5, v["IN12_Y"] + 8.5, stroke=GLASS_E, sw=0.2, dash="0.6 0.4")
    dg0, dg1 = v["IN12_Y"] - v["IN12_DIGIT"] / 2, v["IN12_Y"] + v["IN12_DIGIT"] / 2
    S.box(1.0, 24.5, dg0, dg1, stroke="#E8590C", sw=0.2, dash="0.5 0.5")
    S.text(12.75, dg0 + 1.5, "digits 18.63", 1.8, "#E8590C", "middle")
    # everything on TS06-DRV's component face: the silhouette over all X, and the parts cut here
    ys = sorted({round(y, 2) for p in G["drv_parts"] if p[4] == 0 for y in (p[2][2], p[2][3])})
    sil = []
    for a, b in zip(ys, ys[1:]):
        m = (a + b) / 2
        h = max([p[3] for p in G["drv_parts"] if p[4] == 0 and p[2][2] <= m <= p[2][3]] or [0])
        sil += [(v["Z_DRV_B"] + h, a), (v["Z_DRV_B"] + h, b)]
    S.poly([(v["Z_DRV_B"], ys[0])] + sil + [(v["Z_DRV_B"], ys[-1])], stroke=PART, sw=0.35, dash="1 0.6", close=False)
    for ref, fp, bx, h, side, src in G["drv_parts"]:
        if bx[0] <= xs <= bx[1]:
            z0, z1 = (v["Z_DRV_B"], v["Z_DRV_B"] + h) if side == 0 else (v["Z_DRV_F"] - h, v["Z_DRV_F"])
            S.box(z0, z1, bx[2], bx[3], fill=PART, stroke=INK, sw=0.2)
    for ref in ("U13", "C7", "VT21", "U1", "L1"):
        bx, h = next((p[2], p[3]) for p in G["drv_parts"] if p[0] == ref)
        S.text(v["Z_DRV_B"] + h + 0.8, (bx[2] + bx[3]) / 2 - 0.6, "%s %.1f" % (ref, h), 2.0, INK)
    # beyond the cut: DRV J1 and its plug, the H3 standoff; phantom: ИН-17 and the fascia's connector
    j = drv["parts"]["J1"]["box"]
    S.box(v["Z_DRV_F"] - v["J1_MATED_H"], v["Z_DRV_F"], j[2], j[3], stroke=INK, dash="0.8 0.5", sw=0.25)
    S.text(v["Z_DRV_F"] - v["J1_MATED_H"] - 0.8, j[3] + 1.6, "DRV J1 + plug (X 44-54)", 1.9, INK, "end")
    hx, hy, _ = disp["holes"][2]
    S.box(v["Z_DISP_B"], v["Z_DRV_F"], hy - 2.75, hy + 2.75, stroke=INK, dash="0.8 0.5", sw=0.2)
    S.box(0, v["IN17_D"], v["IN17_Y"] - v["IN17_H"] / 2, v["IN17_Y"] + v["IN17_H"] / 2, stroke=PHANTOM, dash="1.2 0.6", sw=0.25)
    S.text(11, v["IN17_Y"] - v["IN17_H"] / 2 + 1.5, "ИН-17 (phantom)", 1.8, PHANTOM, "middle")
    lead = [(p[2], p[1]) for p in G["lead"]]
    S.poly(lead, stroke=PHANTOM, sw=0.45, dash="2 0.8 0.4 0.8", close=False)
    S.text(17, 1.2, "fascia lead %.0f mm (phantom)" % v["LEAD_PATH"], 1.9, PHANTOM)
    # sight lines past the brow's lower edge and the fascia's top edge
    t = math.tan(math.radians(v["VIEW_DEG"]))
    z_far = v["Z_DISP_F"]
    S.line((v["Z_TOE"] - 12, v["SOFFIT_Y"] + (v["Z_FACE"] - v["Z_TOE"] + 12) * t), (z_far, v["SOFFIT_Y"] - (z_far - v["Z_FACE"]) * t),
           AMB, 0.3, "2 1")
    S.line((v["Z_TOE"] - 12, v["SILL_TOP_Y"] - (v["Z_FACE"] - v["Z_TOE"] + 12) * t), (z_far, v["SILL_TOP_Y"] + (z_far - v["Z_FACE"]) * t),
           AMB, 0.3, "2 1")
    S.text(v["Z_TOE"] - 12, v["SOFFIT_Y"] + (v["Z_FACE"] - v["Z_TOE"] + 12) * t + 1.5, "eye %g° above" % v["VIEW_DEG"], 2.0, AMB)
    S.text(v["Z_TOE"] - 12, v["SILL_TOP_Y"] - (v["Z_FACE"] - v["Z_TOE"] + 12) * t - 1.2, "eye %g° below" % v["VIEW_DEG"], 2.0, AMB)
    # labels
    S.label((2, v["IN12_TOP"] - 6), (-22, 64), "ИН-12 M10, glass %.2f x %.2f" % (v["IN12_D"], v["IN12_H"]), INK, 2.1, "end")
    S.label((v["Z_DISP_F"] + 0.8, 36), (6, 31), "TS06-DISP", INK, 2.1)
    S.label((v["Z_DRV_F"] + 0.8, 22), (6, 24), "TS06-DRV", INK, 2.1)
    S.label((v["Z_REAR_OUT"] - 0.8, 104), (50, v["Y_TOP"] + 4), "rear panel, FR4 blank", INK, 2.1)
    zb = v["Z_FACE"] + (95 - v["SOFFIT_Y"]) * math.tan(math.radians(v["BROW_RAKE"])) + 1.5
    S.label((zb, 95), (-22, 100), "brow (orange) + top plate (black)", INK, 2.2, "end")
    S.label((10, v["SILL_TOP_Y"] - 1), (-18, v["SILL_TOP_Y"] - 20), "sill / trench floor", INK, 2.2, "end")
    S.label((-5, 20), (-24, 26), "TS06-FASCIA, 12°", INK, 2.2, "end")
    S.label((-4, v["Y_FLOOR"] + 2), (-24, v["Y_FLOOR"] + 4), "kick + base", INK, 2.2, "end")
    # dimensions: depth chain along the bottom, heights on the right
    yb = v["Y_BOT"]
    zc = [v["Z_TOE"], v["Z_FACE"], 0.0, v["Z_DISP_F"], v["Z_DISP_B"], v["Z_DRV_F"], v["Z_DRV_B"],
          v["Z_DRV_B"] + v["PART_MAX"], v["Z_REAR_IN"], v["Z_REAR_OUT"]]
    for i, (a, b) in enumerate(zip(zc, zc[1:])):
        S.dim((a, yb), (b, yb), 8 + 4.5 * (i % 2), "%.1f" % (b - a), size=2.0)
    S.dim((v["Z_TOE"], yb), (v["Z_REAR_OUT"], yb), 22, "%.1f outside depth" % v["OUT_D"])
    S.dim((0, yb), (v["Z_REAR_IN"], yb), 29, "%.1f glass front to rear panel (review: 65-72)" % v["Z_REAR_IN"])
    zr = v["Z_REAR_OUT"]
    yc = [v["Y_BOT"], v["Y_FLOOR"], v["DRV_BOT_Y"], v["SILL_TOP_Y"], v["SOFFIT_Y"], v["DRV_TOP_Y"], v["Y_TOP_IN"], v["Y_TOP"]]
    for i, (a, b) in enumerate(zip(yc, yc[1:])):
        S.dim((zr, a), (zr, b), 8 + 5 * (i % 2), "%.1f" % (b - a), horiz=False, size=2.0)
    S.dim((zr, v["Y_BOT"]), (zr, v["Y_TOP"]), 22, "%.1f outside height" % v["OUT_H"], horiz=False)
    return S.svg(["Chain along the bottom: toe to face %.1f · recess %.1f · glass to TS06-DISP %.1f (25.5 + %.1f socket seat, "
                  "assumed) · board · stack %.1f · board · tallest part %.1f (U13) · air %.1f · panel %.1f."
                  % (v["Z_FACE"] - v["Z_TOE"], v["GLASS_RECESS"], v["Z_DISP_F"], v["IN12_SEAT"], v["STACK_GAP"],
                     v["PART_MAX"], v["REAR_AIR"], v["REAR_T"]),
                  "Blue-grey dashed skyline: every part on TS06-DRV's rear face, all X. The floor is %.1f below the "
                  "FreeCAD Y 0 so the fascia lead can leave its side-entry J1 (checks.md, 8)." % -v["Y_FLOOR"]])


def draw_plan(G):
    v, B = G["v"], G["B"]
    drv = B["drv"]
    yc = v["JACK_Y"]
    M, MT = 34.0, 36.0
    W, H = v["OUT_W"] + 2 * M + 34, v["OUT_D"] + MT + 40
    f = lambda X, Z: (X - v["X_OUT_L"] + M, v["Z_REAR_OUT"] - Z + MT)
    S = Sheet(W, H, "PLAN SECTION B-B AT Y = %.1f (DC JACK AXIS), FRONT DOWN  1:1" % yc,
              "the two openings, TS06-DRV's top band from above, and the fascia lead on the floor (phantom)", f)
    rb = math.radians(v["BROW_RAKE"])
    zf = v["Z_FACE"] + (yc - v["SOFFIT_Y"]) * math.tan(rb)
    # left cheek with the USB slot, right cheek with the jack counterbore
    z_slot = v["USB_Z"] - v["USB_SLOT_H"] / 2
    S.box(v["X_OUT_L"], v["X_IN_L"], zf, z_slot, fill=CASE_CUT)
    S.box(v["X_OUT_L"], v["X_IN_L"], z_slot, v["Z_REAR_IN"], stroke=RED, dash="0.8 0.5", sw=0.25)
    jz0, jz1 = v["JACK_Z"] - v["JACK_HOLE_D"] / 2, v["JACK_Z"] + v["JACK_HOLE_D"] / 2
    cz0, cz1 = v["JACK_Z"] - v["JACK_CB_D"] / 2, v["JACK_Z"] + v["JACK_CB_D"] / 2
    xw = v["X_IN_R"] + v["JACK_WEB"]
    S.poly([(v["X_IN_R"], zf), (v["X_OUT_R"], zf), (v["X_OUT_R"], cz0), (xw, cz0), (xw, jz0), (v["X_IN_R"], jz0)], fill=CASE_CUT)
    S.poly([(v["X_IN_R"], jz1), (xw, jz1), (xw, cz1), (v["X_OUT_R"], cz1), (v["X_OUT_R"], v["Z_REAR_IN"]),
            (v["X_IN_R"], v["Z_REAR_IN"])], fill=CASE_CUT)
    # brow face plate cut, the rear panel with its vents
    S.box(v["X_IN_L"], v["X_IN_R"], zf, zf + v["BROW_T"] / math.cos(rb), fill=BRIGHT)
    xs = [v["X_OUT_L"]] + [x for a, b in G["vents"] for x in (a, b)] + [v["X_OUT_R"]]
    for a, b in zip(xs[0::2], xs[1::2]):
        S.box(a, b, v["Z_REAR_IN"], v["Z_REAR_OUT"], fill=BOARD, stroke=BOARD_E, sw=0.25)
    # below the cut, seen from above: TS06-DISP's top edge, the soffit, XS12, the H8 boss
    S.box(0, v["BOARD_W"], v["Z_DISP_F"], v["Z_DISP_B"], stroke=MUTE, sw=0.25)
    S.box(v["X_IN_L"], v["X_IN_R"], v["Z_FACE"] + 3, v["Z_BACK"], stroke=MUTE, sw=0.2)
    xs12 = drv["parts"]["XS12"]["box"]
    S.box(xs12[0], xs12[1], v["Z_DRV_F"] - v["PBS_H"], v["Z_DRV_F"], stroke=MUTE, sw=0.2)
    for b in G["bosses"]:
        if b[0] == "H8":
            S.box(b[1], b[2], b[5], b[6], stroke=MUTE, sw=0.25)
    # TS06-DRV and what the cut passes through on its rear face
    S.box(0, v["BOARD_W"], v["Z_DRV_F"], v["Z_DRV_B"], fill="#2E7D5B", stroke=INK, sw=0.25)
    for ref, fp, bx, h, side, src in G["drv_parts"]:
        if side == 0 and bx[2] <= yc <= bx[3]:
            S.box(max(bx[0], 0.3) if ref == "U1" else bx[0], bx[1], v["Z_DRV_B"], v["Z_DRV_B"] + h, fill=PART, stroke=INK, sw=0.2)
            S.text((bx[0] + bx[1]) / 2, v["Z_DRV_B"] + h + 1.2, ref, 1.9, INK, "middle")
    # the USB receptacle and plug; the jack body and plug
    uz0, uz1 = v["USB_Z"] - v["USB_H"] / 2, v["USB_Z"] + v["USB_H"] / 2
    S.box(v["USB_X"], v["USB_X"] + v["USB_L"], uz0, uz1, fill="#C9CED3", stroke=INK, sw=0.25)
    S.box(v["USB_X"] - 22, v["USB_X"], v["USB_Z"] - v["USB_PLUG_H"] / 2, v["USB_Z"] + v["USB_PLUG_H"] / 2,
          stroke=PHANTOM, dash="1 0.6", sw=0.25)
    S.text(v["USB_X"] - 23, v["USB_Z"] + 1, "mini-B plug", 2.0, PHANTOM, "end")
    S.box(v["JACK_MOUTH_X"] - v["JACK_BODY_L"], v["JACK_MOUTH_X"], v["Z_DRV_B"], v["Z_DRV_B"] + v["JACK_BODY_H"],
          fill="#C9CED3", stroke=INK, sw=0.25)
    eng = v["PLUG_BARREL_L"] - (v["X_IN_R"] - v["JACK_MOUTH_X"] + v["JACK_WEB"])
    S.box(v["JACK_MOUTH_X"] - eng, xw, v["JACK_Z"] - 2.75, v["JACK_Z"] + 2.75, stroke=PHANTOM, dash="1 0.6", sw=0.25)
    S.box(xw, xw + 22, v["JACK_Z"] - v["PLUG_NOSE_D"] / 2, v["JACK_Z"] + v["PLUG_NOSE_D"] / 2, stroke=PHANTOM, dash="1 0.6", sw=0.25)
    S.text(xw + 23, v["JACK_Z"] + 1, "5.5/2.1 plug", 2.0, PHANTOM)
    # the fascia lead on the floor
    S.poly([(p[0], p[2]) for p in G["lead"]], stroke=PHANTOM, sw=0.45, dash="2 0.8 0.4 0.8", close=False)
    S.text(100, (G["lead"][3][2] + G["lead"][4][2]) / 2 + 3.5, "fascia lead on the floor, %.0f mm" % v["LEAD_PATH"],
           2.0, PHANTOM, "middle")
    S.box(v["FASCIA_X0"], v["FASCIA_X0"] + v["FASCIA_W"], v["Z_FACE"], v["Z_FACE"] - 8, stroke=MUTE, dash="1 0.8", sw=0.2)
    S.text(v["FASCIA_X0"] + v["FASCIA_W"] / 2, v["Z_FACE"] - 4.5, "TS06-FASCIA below (raked)", 2.0, MUTE, "middle")
    # dimensions
    S.dim((v["X_OUT_R"], cz1), (v["X_OUT_R"], cz0), 8, "Ø%g cb" % v["JACK_CB_D"], horiz=False, size=2.0)
    S.dim((v["X_IN_R"], jz1), (xw, jz1), -9, "web %.1f" % v["JACK_WEB"], size=2.0)
    S.dim((v["JACK_MOUTH_X"] - eng, jz0), (xw, jz0), 10, "engaged %.1f" % eng, size=2.0)
    S.dim((v["USB_X"], uz1), (v["X_IN_L"], uz1), -6, "%.1f into cheek" % (v["X_IN_L"] - v["USB_X"]), size=1.9)
    S.dim((v["X_OUT_L"], z_slot), (v["X_OUT_L"], z_slot + v["USB_SLOT_H"]), -8, "slot %g" % v["USB_SLOT_H"], horiz=False, size=2.0)
    S.dim((v["X_OUT_L"], v["Z_REAR_OUT"]), (v["X_OUT_R"], v["Z_REAR_OUT"]), -8, "%.1f outside" % v["OUT_W"])
    S.dim((v["VENT_X0"], v["Z_REAR_OUT"]), (G["vents"][-1][1], v["Z_REAR_OUT"]), -3,
          "%d vents x %.1f wide" % (len(G["vents"]), v["VENT_W"]), size=2.0)
    return S.svg(["Right cheek: Ø%g counterbore from the OUTSIDE, %.1f mm web, Ø%g hole - the review's pocket 'from "
                  "inside' would leave the outer face where it is and the plug at %.1f mm engagement."
                  % (v["JACK_CB_D"], v["JACK_WEB"], v["JACK_HOLE_D"], v["PLUG_BARREL_L"] - (v["X_IN_R"] - v["JACK_MOUTH_X"] + v["CHEEK_T"])),
                  "Left cheek: the %g x %g USB slot runs open to the rear edge so the module can be drawn out "
                  "backwards past the receptacle; the rear panel closes it." % (v["USB_SLOT_W"], v["USB_SLOT_H"])])


def draw_exploded(G):
    v = G["v"]
    M, MT = 64.0, 30.0
    off = {"base": (0, -26), "fascia": (-30, -4), "trench": (-16, 0), "brow": (-14, 22), "top": (0, 44), "module": (22, 0),
           "rear": (52, 0)}
    W, H = v["OUT_D"] + M + 150, v["OUT_H"] + MT + 104
    f = lambda Z, Y: (Z - v["Z_TOE"] + M, v["Y_TOP"] + 56 - Y + MT)
    S = Sheet(W, H, "EXPLODED SIDE VIEW - WHAT COMES APART, AND WITH WHAT",
              "cheeks carry everything; the module (TS06-DISP + TS06-DRV) lifts out backwards as one piece", f)
    mv = lambda pts, k: [(z + off[k][0], y + off[k][1]) for z, y in pts]
    S.poly(G["cheek"], fill="#F3F5F7", stroke=MUTE, sw=0.3)
    S.text(20, 16, "cheek x2, 6 mm - the only structure", 2.3, MUTE, "middle")
    for name, y, z in G["cheek_fix"]:                       # the cheek's screw holes, counterbored outside
        S.circle(z, y, v["CB_D"] / 2, stroke=RED, sw=0.25)
    S.poly(mv(G["base"], "base"), fill=CASE_CUT)
    for part, key in (("base", "base"), ("top plate", "top")):
        y0, y1, z0, z1 = G["rear_lips"][part]
        S.poly(mv(_rect((0, 0, y0, y1, z0, z1)), key), fill=CASE_CUT if key == "base" else "#57606A")
    for name, y0, y1, z0, z1, y, z in G["blocks"]:
        k = {"base": "base", "trench": "trench", "brow": "brow", "top plate": "top"}[name.split(",")[0]]
        S.poly(mv(_rect((0, 0, y0, y1, z0, z1)), k), fill="#E3E8ED", stroke=MUTE, sw=0.2)
    S.poly(mv(G["fascia"], "fascia"), fill=BOARD, stroke=BOARD_E)
    for k, bx in (("trench", G["sill"]), ("trench", G["wall_l"])):
        S.poly(mv(_rect(bx), k), fill=CASE, sw=0.3)
    S.poly(mv(G["brow"], "brow"), fill=BRIGHT)
    S.poly(mv(G["top"], "top"), fill="#57606A")
    S.poly(mv(_rect(G["rear"]), "rear"), fill=BOARD, stroke=BOARD_E)
    dz, dy = off["module"]
    S.box(v["Z_DISP_F"] + dz, v["Z_DISP_B"] + dz, v["DISP_BOT_Y"], v["DISP_TOP_Y"], fill="#2E7D5B")
    S.box(v["Z_DRV_F"] + dz, v["Z_DRV_B"] + dz, v["DRV_BOT_Y"], v["DRV_TOP_Y"], fill="#2E7D5B")
    S.box(0 + dz, v["IN12_D"] + dz, v["IN12_BOT"], v["IN12_TOP"], fill=GLASS, stroke=GLASS_E)
    for ref, fp, bx, h, side, src in G["drv_parts"]:
        if side == 0 and h >= 15:
            S.box(v["Z_DRV_B"] + dz, v["Z_DRV_B"] + h + dz, bx[2], bx[3], fill=PART, stroke=INK, sw=0.2)
    m3, m25 = "M3 x %g" % v["SCREW_M3_L"], "M2.5 x %g" % v["SCREW_M25_L"]
    txt = [((30, v["Y_BOT"] - 26 - 5), "base + kick strip: 2 x %s per cheek, into 8 mm end blocks" % m3, "middle"),
           ((-34, -10), "TS06-FASCIA: 4 x %s into cheek bosses" % m25, "middle"),
           ((-3, 84), "trench (sill + walls): 1 x %s per cheek, into the blocks under H10 / ИН-15А" % m3, "middle"),
           ((-20, v["Y_TOP"] + 6), "brow (safety orange): 1 x %s per cheek" % m3, "end"),
           ((34, v["Y_TOP"] + 50), "top plate (black): 2 x %s per cheek" % m3, "middle"),
           ((66, -2), "module: 4 x M3 x 8 + nylon washers (H5-H8) into cheek bosses, from behind", "middle"),
           ((v["Z_REAR_OUT"] + 52 + 3, 54), "rear panel (FR4 blank):", "start"),
           ((v["Z_REAR_OUT"] + 52 + 3, 50), "6 x %s, 3 into the base's lip" % m25, "start"),
           ((v["Z_REAR_OUT"] + 52 + 3, 46), "and 3 into the top plate's;", "start"),
           ((v["Z_REAR_OUT"] + 52 + 3, 42), "holes slotted ±%.1f along X" % v["SLOT_X"], "start")]
    for (z, y), s, anc in txt:
        S.text(z, y, s, 2.3, INK, anc)
    return S.svg(["Service (review 7): unplug, wait 15 s; 6 screws off the rear panel; 4 module screws; draw the module "
                  "back ~30 mm and unplug J1 from below; lift out.",
                  "Assembly (F9): screw the module in before tightening the crossmember screws, so TS06-DRV sets the "
                  "cheeks' spacing. The display pulls straight off TS06-DRV (seven strip pairs).",
                  "Red circles: the cheek's counterbored M3 holes; grey: the end blocks (8 mm) with their inserts."])


def write_svgs(G):
    os.makedirs(OUTDIR, exist_ok=True)
    for name, fn in (("front", draw_front), ("section", draw_section), ("plan", draw_plan), ("exploded", draw_exploded)):
        with open(os.path.join(OUTDIR, name + ".svg"), "w", encoding="utf8") as fh:
            fh.write(fn(G))


# ============================================================================ checks.md
def screw_table(G):
    """[(spec, qty, into, closest mm, to what)] - the screws grouped by what they go into."""
    rows = {}
    for s in G["screws"]:
        key = (s[1], s[0])
        c, what = _screw_clear(G, s)
        r = rows.setdefault(key, [0, 99.0, ""])
        r[0] += 1
        if c < r[1]:
            r[1], r[2] = c, what
    return [(k[0], n, k[1], c, w) for k, (n, c, w) in rows.items()]


def write_checks(G, G_lay, d, R, path, G_ff=None):
    v = G["v"]
    L = ["# TS06 pair case, concept A: checks", "",
         "Generated by `case_pair.py` from `boards.json` and the DIMS table - do not edit. "
         "Status: OK, TIGHT (passes with under ~1 mm or depends on an assumed number), FAIL (does not work as "
         "stated), NOTE (a consequence worth knowing).", "",
         "## Envelope", "",
         "| | mm | from |", "|---|---|---|",
         "| Outside width | %.1f | %.1f boards + 2 x 0.5 + 2 x %.0f cheeks |" % (v["OUT_W"], v["OUT_W"] - 1.0 - 2 * v["CHEEK_T"], v["CHEEK_T"]),
         "| Outside height | %.1f | base %.0f + floor to TS06-DRV %.1f + board %.0f + top clearance %.1f + top plate %.0f |"
         % (v["OUT_H"], v["BASE_T"], v["DRV_BOT_Y"] - v["Y_FLOOR"], v["DRV_H"], v["TOP_CLR"], v["TOP_T"]),
         "| Outside depth | %.1f | toe %.1f in front of the face + glass-to-rear-panel %.1f + panel %.1f + recess %.1f |"
         % (v["OUT_D"], v["Z_FACE"] - v["Z_TOE"], v["Z_REAR_IN"], v["REAR_T"], v["GLASS_RECESS"]),
         "| Inside height (floor to top plate) | %.1f | review estimate ~106 |" % v["IN_H"],
         "| Glass front to rear panel | %.1f | review estimate 65-72 |" % v["Z_REAR_IN"],
         "| Same, with U13 / C7 / VT21 laid down | %.1f | outside depth %.1f |" % (G_lay["v"]["Z_REAR_IN"], G_lay["v"]["OUT_D"]),
         "", "## Results", "", "| # | Check | Result | Status | Note |", "|---|---|---|---|---|"]
    for r in R:
        L.append("| %s | %s | %s | **%s** | %s |" % (r["id"], r["what"], r["result"], r["status"], r["note"]))
    L += ["", "## Screws", "", "Every case screw, its length, what it goes into, and how close its shank comes to glass "
          "or a board it does not clamp (check 10). The cheek screws go in from a %g mm counterbore on the cheek's "
          "outside." % v["CB_DEPTH"], "", "| Screw | Qty | Into | Closest to glass or a board |", "|---|---|---|---|"]
    for spec, n, into, c, what in screw_table(G):
        L.append("| %s | %d | %s | %.1f mm (%s) |" % (spec, n, into, c, what))
    if G_ff is not None:
        for spec, n, into, c, what in screw_table(G_ff):
            if "frame" in into:
                L.append("| %s | %d | variant D: %s | %.1f mm (%s) |" % (spec, n, into, c, what))
        L.append("")
        L.append("Variant D drops the four fascia screws into the cheek bosses and adds the frame's rows. The cheek "
                 "screws are low-head (DIN 7984, 2 mm) so the head sits in the %g mm counterbore." % v["CB_DEPTH"])
    L += ["", "## Every dimension and where it comes from", "", "| Name | Value | Kind | Source |", "|---|---|---|---|"]
    for name, value, kind, src, g in d.rows:
        L.append("| `%s` | %s | %s | %s |" % (name, _scad(value), kind, src))
    L += ["", "## Part heights on TS06-DRV's rear face", "", "| Footprint | mm | Kind | Note |", "|---|---|---|---|"]
    for fp, (h, kind, src) in sorted(FP_H.items()):
        if h is None:
            hs = [p[3] for p in G["drv_parts"] if p[1] == fp]
            h = hs[0] if hs else None
        L.append("| %s | %s | %s | %s |" % (fp.replace("TS06_", ""), "%.1f" % h if h is not None else "-", kind, src))
    with open(path, "w", encoding="utf8") as fh:
        fh.write("\n".join(L) + "\n")


# ============================================================================ OpenSCAD
VIEWS = {   # name: (part, explode, --camera=tx,ty,tz,rx,ry,rz,dist)
    "iso": ("assembly", 0, "88,30,50,62,0,325,520"),
    "iso_rear": ("assembly", 0, "88,30,50,62,0,145,520"),
    "front": ("assembly", 0, "88,30,50,90,0,0,470"),
    "exploded": ("assembly", 1, "88,30,50,62,0,325,760"),
    "module": ("module", 0, "88,30,50,55,0,210,470"),
}
STL_PARTS = ["cheek_l", "cheek_r", "brow", "top", "trench", "base", "rear", "fascia_blank",
             "fascia_frame"]    # the last is variant D's, rendered with FASCIA_FRAME=1 (its cheeks: -D FASCIA_FRAME=1)


def render():
    scad = os.path.join(HERE, "case.scad")
    os.makedirs(OUTDIR, exist_ok=True)
    run = lambda args: subprocess.run(["nice", "-n", "15"] + args, cwd=HERE, capture_output=True, text=True)
    # 1. does case.scad derive what case_pair.py derived?
    r = run(["openscad", "-o", os.path.join(OUTDIR, "echo.echo"), "-D", 'PART="none"', scad])
    echo = open(os.path.join(OUTDIR, "echo.echo")).read() if os.path.exists(os.path.join(OUTDIR, "echo.echo")) else r.stderr
    print(echo.strip().replace("ECHO: ", "  scad: "))
    os.remove(os.path.join(OUTDIR, "echo.echo")) if os.path.exists(os.path.join(OUTDIR, "echo.echo")) else None
    # 2. printable parts
    for p in STL_PARTS:
        out = os.path.join(OUTDIR, p + ".stl")
        r = run(["openscad", "-o", out, "-D", 'PART="%s"' % p] + (["-D", "FASCIA_FRAME=1"] if p == "fascia_frame" else [])
                + [scad])
        print("  %-14s %s" % (p, "ok" if r.returncode == 0 and os.path.exists(out) else "FAILED\n" + r.stderr[-800:]))
    # 3. pictures (OpenCSG preview needs an X server: xvfb-run)
    for name, (part, ex, cam) in VIEWS.items():
        out = os.path.join(OUTDIR, name + ".png")
        r = run(["xvfb-run", "-a", "-s", "-screen 0 1600x1200x24", "openscad", "-o", out, "--imgsize=1600,1100",
                 "--camera=" + cam, "--projection=o" if name == "front" else "--projection=p", "--colorscheme=Tomorrow",
                 "-D", 'PART="%s"' % part, "-D", "EXPLODE=%d" % ex, scad])
        print("  %-14s %s" % (name + ".png", "ok" if r.returncode == 0 else "FAILED\n" + r.stderr[-800:]))


# ============================================================================ main
def main():
    if "--extract" in sys.argv or not os.path.exists(BOARDS):
        extract()
    with open(BOARDS, encoding="utf8") as fh:
        B = json.load(fh)
    d = dims(B)
    sets = [a.split("=", 1) for a in sys.argv[1:] if "=" in a and not a.startswith("-")]
    for k, val in sets:                             # what-ifs: NAME=value (not written to params.scad)
        assert k in d.v, "unknown dimension " + k
        d.v[k] = float(val)
    G = derive(B, d)
    d2 = dims(B)
    d2.v.update({k: float(val) for k, val in sets})
    G_lay = derive(B, d2, lay_down=True)
    d3 = dims(B)                                    # variant D, scored beside the default (section 12)
    d3.v.update({k: float(val) for k, val in sets})
    d3.v["FASCIA_FRAME"] = 1.0
    G_ff = derive(B, d3)
    if sets:
        v = G["v"]
        print("what-if %s: envelope %.1f W x %.1f H x %.1f D, glass front to rear panel %.1f, floor Y %.1f"
              % (" ".join("=".join(x) for x in sets), v["OUT_W"], v["OUT_H"], v["OUT_D"], v["Z_REAR_IN"], v["Y_FLOOR"]))
        return
    R = checks(G, G_lay, G_ff)
    write_scad(G, d, os.path.join(HERE, "params.scad"))
    write_checks(G, G_lay, d, R, os.path.join(HERE, "checks.md"), G_ff)
    write_svgs(G)
    v = G["v"]
    print("envelope %.1f W x %.1f H x %.1f D   (glass front to rear panel %.1f, floor at Y %.1f)"
          % (v["OUT_W"], v["OUT_H"], v["OUT_D"], v["Z_REAR_IN"], v["Y_FLOOR"]))
    n = {}
    for r in R:
        n[r["status"]] = n.get(r["status"], 0) + 1
        print("  %-3s [%s] %s: %s" % (r["id"], r["status"], r["what"], r["result"]))
    print("checks: " + ", ".join("%d %s" % (c, s) for s, c in sorted(n.items())))
    if "--render" in sys.argv:
        render()


if __name__ == "__main__":
    main()
