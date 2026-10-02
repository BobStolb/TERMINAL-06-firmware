#!/usr/bin/env python3
"""Where the three boards stand in the case: the placement of TS06-DISP, TS06-DRV and the fascia, from case_pair.py.

    python3 tools/stack_frame.py OUT.json [--fascia TS06-FASCIA-rhythm]

Imports 3d/case-pair/case_pair.py read-only (its committed boards.json, its own dims() and derive(), with the
fascia board named swapped in as FASCIA_PCB= does), and writes, for each board, the 4x4 matrix that takes a
KiCad GLB export of it (units of metres, x right, y up out of the board, z = the board's y downward; the back
face of the board at y = 0) to the stack's frame in millimetres:

    X across the front from the clock's left, Y up, Z towards the viewer; the ИН-12 glass front is Z = 0.

That is the case model's world (X, Y, Z-from-the-glass, + towards the back) with Z flipped to three.js's
right-handed "towards the viewer". The matrices are row-major lists of 16, ready for Matrix4.set().
Also written: the case numbers the fit table compares against (frame values).
"""
import importlib.util, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))


def load_case_pair():
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("case_pair_ro", os.path.join(ROOT, "3d", "case-pair", "case_pair.py"))
    cp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cp)
    return cp


def geometry(fascia="TS06-FASCIA-rhythm"):
    cp = load_case_pair()
    sys.path.insert(0, HERE)
    import sexp                                                  # noqa: E402
    B = json.load(open(os.path.join(ROOT, "3d", "case-pair", "boards.json"), encoding="utf8"))
    if fascia:
        path = os.path.join(ROOT, "PCB", fascia, fascia + ".kicad_pcb")
        cp.FASCIA_PCB = path
        B["fascia"] = cp._fascia(sexp)
    d = cp.dims(B)
    G = cp.derive(B, d)
    return cp, B, d, G


def matrices(G):
    v = G["v"]
    r = math.radians(v["FASCIA_RAKE"])
    s, c = math.sin(r), math.cos(r)
    T = v["FASCIA_T"]
    top = v["DISP_TOP_Y"]
    # GLB (x, u, zg): u = 0 on the board's back face, zg = the board's y (down)
    disp = [1, 0, 0, 0,
            0, 0, -1, top,
            0, 1, 0, -v["Z_DISP_B"]]
    drv = [-1, 0, 0, v["BOARD_W"],
           0, 0, -1, v["DRV_TOP_Y"],
           0, -1, 0, -v["Z_DRV_F"]]
    fas = [1, 0, 0, v["FASCIA_X0"],
           0, s, -c, v["SILL_TOP_Y"] - T * s,
           0, c, s, -v["Z_FACE"] - T * c]
    row4 = [0, 0, 0, 1]
    return {"TS06-DISP": disp + row4, "TS06-DRV": drv + row4, "fascia": fas + row4}


def main(argv):
    out = argv[1]
    fascia = "TS06-FASCIA-rhythm"
    if "--fascia" in argv:
        fascia = argv[argv.index("--fascia") + 1]
    cp, B, d, G = geometry(fascia)
    v = G["v"]
    keep = ["BOARD_W", "DISP_H", "DISP_TOP_Y", "DRV_H", "DRV_TOP_Y", "DRV_BOT_Y", "DISP_BOT_Y", "PCB_T", "FASCIA_W", "FASCIA_H",
            "FASCIA_X0", "FASCIA_T", "FASCIA_RAKE", "SILL_TOP_Y", "Z_FACE", "Z_DISP_F", "Z_DISP_B", "Z_DRV_F", "Z_DRV_B",
            "STACK_GAP", "PBS_H", "PLS_BODY", "IN12_D", "IN12_SEAT", "IN17_D", "IN17_STANDOFF", "IN12_H", "IN12_W",
            "GLASS_ALLOW", "GLASS_RECESS", "SOFFIT_Y", "BROW_CLR", "Z_REAR_IN", "Y_TOP_IN", "Y_FLOOR", "Z_BACK", "BACK_GAP",
            "IN12_Y", "IN17_Y", "IN12_TOP", "IN17_TOP", "IN12_BOT", "REAR_AIR", "LED_H", "PIN_TAIL", "FJ_HDR_H", "SILL_T"]
    json.dump({"about": "tools/stack_frame.py from 3d/case-pair/case_pair.py; fascia board %s. Frame: X right, Y up, Z towards "
                        "the viewer, mm, the ИН-12 glass front at Z 0." % fascia,
               "fascia_board": fascia,
               "matrix": matrices(G),
               "frame": {k: round(v[k], 4) for k in keep if k in v},
               "drv_parts": [[p[0], p[1], p[3]] for p in G["drv_parts"]]},
              open(out, "w", encoding="utf8"), indent=1, ensure_ascii=False)
    print("wrote", out)


if __name__ == "__main__":
    main(sys.argv)
