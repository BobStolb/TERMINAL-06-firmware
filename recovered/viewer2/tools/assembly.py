#!/usr/bin/env python3
"""The assembly frame for the viewer, taken from the case model (the source of truth).

    python3 assembly.py REPO OUT.json

Imports REPO/3d/case-pair/case_pair.py read-only, loads its committed boards.json, and runs its own
dims() and derive() - the same numbers params.scad and the STLs were made from. Nothing in the
repository is written (bytecode is off). The page places every board, tube proxy, standoff and
the fascia lead from this file, so a change in the case model moves them all.

World frame (case model): X across the front from the left, Y up, Z depth from the ИН-12 glass
front, + towards the back. The page maps it to three.js as (X, Y, -Z).
"""
import importlib.util, json, math, os, subprocess, sys


VARIANTS = [("A", "TS06-FASCIA", "centred"), ("W", "TS06-FASCIA-wide", "full width"), ("R", "TS06-FASCIA-rhythm", "on the tube grid")]


def fascia_variant(cp, sexp, B, path):
    """Re-run the case model with another fascia board in TS06-FASCIA's place (as FASCIA_PCB= does)."""
    cp.FASCIA_PCB = path
    B2 = dict(B)
    B2["fascia"] = cp._fascia(sexp)
    d = cp.dims(B2)
    G = cp.derive(B2, d)
    try:
        G_lay = cp.derive(B2, cp.dims(B2), lay_down=True)
        R = cp.checks(G, G_lay)
    except Exception:
        R = []
    v = G["v"]
    fas_rows = [{"status": r["status"], "what": r["what"], "result": r["result"]} for r in R
                if any(w in r["what"].lower() for w in ("fascia", "rotary", "sw5", "lead", "slot", "boss"))]
    tally = {}
    for r in R:
        tally[r["status"]] = tally.get(r["status"], 0) + 1
    return {"W": B2["fascia"]["W"], "H": B2["fascia"]["H"], "X0": round(v["FASCIA_X0"], 3),
            "lead": [[round(c, 3) for c in p] for p in G["lead"]], "lead_path": v["LEAD_PATH"],
            "bodies": [[b[0], round(b[1], 3), b[2], b[3], b[4], b[5]] for b in G["bodies"]],
            "checks": tally, "fascia_checks": fas_rows[:14]}


def main(repo, out):
    sys.dont_write_bytecode = True
    here = os.path.join(repo, "3d", "case-pair")
    spec = importlib.util.spec_from_file_location("case_pair_ro", os.path.join(here, "case_pair.py"))
    cp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cp)
    B = json.load(open(os.path.join(here, "boards.json"), encoding="utf8"))
    d = cp.dims(B)
    G = cp.derive(B, d)
    d2 = cp.dims(B)
    G_lay = cp.derive(B, d2, lay_down=True)
    try:
        R = cp.checks(G, G_lay)
        tally = {}
        for r in R:
            tally[r["status"]] = tally.get(r["status"], 0) + 1
    except Exception as e:                                   # the checks are a bonus here
        R, tally = [], {"error": str(e)}
    v = G["v"]
    disp, drv, fas = B["disp"], B["drv"], B["fascia"]
    keep = ["BOARD_W", "DISP_H", "DISP_TOP_Y", "DRV_H", "DRV_Y0", "PCB_T", "FASCIA_W", "FASCIA_H", "FASCIA_X0",
            "FASCIA_T", "FASCIA_RAKE", "SILL_TOP_Y", "Z_FACE", "Z_DISP_F", "Z_DISP_B", "Z_DRV_F", "Z_DRV_B",
            "STACK_GAP", "PBS_H", "PLS_BODY", "DRV_TOP_Y", "DRV_BOT_Y", "DISP_BOT_Y",
            "IN12_W", "IN12_H", "IN12_D", "IN12_SEAT", "IN17_FACE", "IN17_H", "IN17_D", "IN17_STEM",
            "IN17_STANDOFF", "INS1_D", "LED_D", "LED_H", "SCREW_HEAD", "SCREW_HEAD_D", "CABLE_HALF",
            "OUT_W", "OUT_H", "OUT_D", "Z_REAR_IN", "Z_REAR_OUT", "Y_FLOOR", "Y_TOP", "X_OUT_L", "X_OUT_R",
            "LEAD_PATH", "LEAD_LEN", "NANO_H", "USB_X", "USB_Y", "USB_Z"]
    frame = {k: round(v[k], 4) for k in keep if k in v}
    names12 = ["H10", "H1", "M10", "M1"]
    tubes = []
    for ref, p in sorted(disp["parts"].items()):
        fp = p["fp"]
        X, Y = p["at"]
        if fp == "TS06_IN12_Socket":
            kind = "IN15" if X in disp["IN15_X"] else "IN12"
            if kind == "IN12":
                name = names12[disp["IN12_X"].index(X)] if X in disp["IN12_X"] else ref
            else:
                name = "ИН-15Б" if X == disp["IN15_X"][0] else "ИН-15А"
            tubes.append({"ref": ref, "kind": kind, "name": name, "X": X, "Y": disp["IN12_Y"]})
        elif fp == "TS06_IN17_Socket":
            tubes.append({"ref": ref, "kind": "IN17", "name": "S10" if X == disp["IN17_X"][0] else "S1",
                          "X": X, "Y": disp["IN17_Y"]})
        elif fp == "TS06_INS1_Lamp":
            tubes.append({"ref": ref, "kind": "INS1", "name": "colon", "X": X, "Y": p["at"][1]})
    leds = [{"ref": k, "X": p["at"][0], "Y": p["at"][1]} for k, p in sorted(disp["parts"].items()) if k.startswith("HL")]
    sys.path.insert(0, os.path.join(repo, "tools"))
    import sexp                                               # noqa: E402  (repo's own reader)
    saved = cp.FASCIA_PCB
    variants = {}
    for key, board, label in VARIANTS:
        path = os.path.join(repo, "PCB", board, board + ".kicad_pcb")
        if os.path.exists(path):
            variants[key] = dict(fascia_variant(cp, sexp, B, path), board=board, label=label)
    cp.FASCIA_PCB = saved
    # F: the printed fascia frame (FASCIA_FRAME=1), with the 176 board standing in for its 179 panel
    try:
        d3 = cp.dims(B)
        if "FASCIA_FRAME" in d3.v:
            d3.v["FASCIA_FRAME"] = 1.0
            Gf = cp.derive(B, d3)
            rows = cp.checks_frame(Gf) if hasattr(cp, "checks_frame") else []
            vf, ff = Gf["v"], Gf.get("ff", {})
            t = {}
            for r in rows:
                t[r["status"]] = t.get(r["status"], 0) + 1
            variants["F"] = {"board": "TS06-FASCIA", "label": "frame", "W": B["fascia"]["W"], "H": B["fascia"]["H"],
                             "X0": round(vf["FASCIA_X0"], 3), "lead": [[round(c, 3) for c in q] for q in Gf["lead"]],
                             "lead_path": vf["LEAD_PATH"], "bodies": [[b[0], round(b[1], 3), b[2], b[3], b[4], b[5]] for b in Gf["bodies"]],
                             "checks": t, "fascia_checks": [{"status": r["status"], "what": r["what"], "result": r["result"]} for r in rows][:14],
                             "frame": {k: ff[k] for k in ("px0", "px1", "ribs") if k in ff}, "stand_in": True}
    except Exception as e:                                       # an older case model without the frame
        print("  (no fascia frame: %s)" % e)
    model = {
        "about": "Generated by viewer2/tools/assembly.py from 3d/case-pair/case_pair.py dims() + derive() "
                 "and its boards.json. World: X right, Y up, Z back from the ИН-12 glass front (mm).",
        "sources": B.get("sources", {}),
        "frame": frame,
        "drv_frame": drv["frame"], "disp_frame": disp["frame"],
        "tubes": tubes, "leds": leds,
        "standoffs": [h[:2] for h in disp["holes"]],
        "case_screws": [[h[0], h[1], h[2]] for h in G["drv_case_holes"]],
        "fascia_holes": fas["holes"],
        "lead": [[round(c, 3) for c in p] for p in G["lead"]],
        "bodies": [[b[0], round(b[1], 3), b[2], b[3], b[4], b[5]] for b in G["bodies"]],
        "checks": tally,
        "fascia_variants": variants,
        "checks_notok": [{"status": r["status"], "what": r["what"], "result": r["result"]} for r in R if r["status"] not in ("OK",)][:40],
    }
    with open(out, "w", encoding="utf8") as fh:
        json.dump(model, fh, ensure_ascii=False, indent=1)
    print("fascia variants: " + ", ".join("%s %s X0 %.3f lead %.1f" % (k, x["board"], x["X0"], x["lead_path"]) for k, x in variants.items()))
    print("assembly: envelope %.1f x %.1f x %.1f mm, stack gap %.1f, FASCIA_X0 %.3f, %d tubes, checks %s"
          % (v["OUT_W"], v["OUT_H"], v["OUT_D"], v["STACK_GAP"], v["FASCIA_X0"], len(tubes), tally))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
