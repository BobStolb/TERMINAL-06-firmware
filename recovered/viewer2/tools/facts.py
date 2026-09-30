#!/usr/bin/env python3
"""Numbers for the facts panels, counted from the boards the build just exported.

    python3 facts.py OUTDIR REPO BOARD...      (reads OUTDIR/<BOARD>-drc.json and OUTDIR/<BOARD>.parts.json)

Writes JSON to stdout: per board its size, thickness, tracks, vias, zones and whether they are
stored filled, fitted / DNP part counts, how many parts carry a 3D body in the export, and KiCad's
DRC result (errors, warnings, unconnected, and the violation types). The page prints these beside
its hand-written notes, so a board that changes shows its new counts after a rebuild.
"""
import collections, json, os, re, subprocess, sys


def count(path):
    s = open(path, encoding="utf8").read()
    return {
        "tracks": len(re.findall(r"^\s*\((?:segment|arc)\b", s, re.M)),
        "vias": len(re.findall(r"^\s*\(via\b", s, re.M)),
        "zones": len(re.findall(r"^\s*\(zone\b", s, re.M)),
        "zones_stored_fill": len(re.findall(r"filled_polygon", s)) > 0,
    }


def main(outdir, repo, boards):
    res = {"commit": "", "date": ""}
    try:
        res["commit"] = subprocess.run(["git", "-C", repo, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
        res["date"] = subprocess.run(["git", "-C", repo, "log", "-1", "--format=%cs"], capture_output=True, text=True).stdout.strip()
        res["branch"] = subprocess.run(["git", "-C", repo, "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True).stdout.strip()
    except Exception:
        pass
    res["boards"] = {}
    for b in boards:
        pcb = os.path.join(repo, "PCB", b, b + ".kicad_pcb")
        f = count(pcb)
        parts = json.load(open(os.path.join(outdir, b + ".parts.json"), encoding="utf8"))
        e = parts["edge"]
        f["size"] = [round(e[1] - e[0], 2), round(e[3] - e[2], 2)]
        f["thickness"] = parts["thickness"]
        real = {k: p for k, p in parts["parts"].items() if not p.get("hole")}
        dnp = [k for k, p in real.items() if "DNP" in p["v"].upper()]
        f["parts"] = len(real) - len(dnp)
        f["dnp"] = len(dnp)
        f["bodies"] = sum(1 for p in real.values() if p["model"])
        f["no_body"] = sorted((k for k, p in real.items() if not p["model"]), key=lambda r: (re.sub(r"\d", "", r), int(re.sub(r"\D", "", r) or 0)))
        drc_path = os.path.join(outdir, b + "-drc.json")
        if os.path.exists(drc_path):
            d = json.load(open(drc_path, encoding="utf8"))
            v = d.get("violations", [])
            f["drc"] = {
                "kicad": d.get("kicad_version", ""),
                "errors": sum(1 for x in v if x.get("severity") == "error"),
                "warnings": sum(1 for x in v if x.get("severity") == "warning"),
                "unconnected": len(d.get("unconnected_items", [])),
                "types": dict(collections.Counter("%s/%s" % (x.get("type"), x.get("severity")) for x in v)),
                "items": [[x.get("severity"), x.get("description"), [i.get("description") for i in x.get("items", [])][:2]] for x in v][:12],
            }
        res["boards"][b] = f
    json.dump(res, sys.stdout, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
