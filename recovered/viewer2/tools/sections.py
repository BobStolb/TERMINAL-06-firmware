#!/usr/bin/env python3
"""The Sections tab's data: the schematic sections from sch/out, or a stub until they exist.

    python3 sections.py SCH_OUT SITE REPO PARTS_JSON

SCH_OUT/sections.json (written by another agent) is a list - or {"sections": [...]} - of
    {id, title, boards, summary, schematic: [svg], layout: [img], parts: [refs], nets: [names]}
with file paths relative to SCH_OUT. Every file it names is copied to SITE/sch/<same path> if its
type is one the host serves (.svg .png .jpg .webp) and it is under 15 MB; anything else is
dropped with a warning. SITE/data/sections.json gets the entries with their paths made relative
to the page ("sch/...") and a "source" field.

With no SCH_OUT/sections.json, a small stub in the same schema is written instead: four sections
from the netlist's own groups (tools/ts06pair.py), each with a generated parts list as its
"schematic" and a generated layout drawing with the section's parts highlighted.
"""
import html, json, os, re, shutil, sys

ALLOWED = {".svg", ".png", ".jpg", ".jpeg", ".webp"}
MAXB = 15 * 1024 * 1024


def copy_real(src, site):
    raw = json.load(open(os.path.join(src, "sections.json"), encoding="utf8"))
    items = raw["sections"] if isinstance(raw, dict) else raw
    out, n = [], 0
    for s in items:
        e = {k: s.get(k) for k in ("id", "title", "boards", "summary", "parts", "nets")}
        e["id"] = str(e["id"] or "s%d" % len(out))
        for key in ("schematic", "layout"):
            e[key] = []
            for rel in s.get(key) or []:
                p = os.path.normpath(os.path.join(src, rel))
                ext = os.path.splitext(p)[1].lower()
                if not p.startswith(os.path.normpath(src)) or not os.path.isfile(p):
                    print("  sections: missing %s" % rel)
                    continue
                if ext not in ALLOWED or os.path.getsize(p) > MAXB:
                    print("  sections: skipped %s (type or size)" % rel)
                    continue
                dst = os.path.join(site, "sch", os.path.relpath(p, src))
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy(p, dst)
                if ext == ".svg":            # the host refuses XML with DTD machinery (30.09.26)
                    t = open(dst, encoding="utf-8").read()
                    t = re.sub(r"<!DOCTYPE[^>\[]*(\[[^\]]*\])?\s*>", "", t, count=1)
                    open(dst, "w", encoding="utf-8").write(t)
                n += 1
                e[key].append("sch/" + os.path.relpath(p, src).replace(os.sep, "/"))
        out.append(e)
    return {"source": "sch/out", "sections": out}, n


# ------------------------------------------------------------------ the stub
STUB = [("power", "12 V in and the 5 V rail", "The barrel jack, the PTC fuse, the polarity diode and the R-78E 5 V switching regulator, with their capacitors."),
        ("hv", "185 V converter", "The boost converter: TC4420 gate driver, IRF840 switch, L1, the fast diode and C7, with the LM393 comparator, its 2.5 V reference and the RP1 set-point divider."),
        ("anodes", "Anode switches and the digit tubes", "Six TLP627 optocouplers switch the anodes of the four ИН-12 and two ИН-17 tubes through their anode resistors; the DNP bleeds sit beside them."),
        ("colon", "Colon lamps", "The two ИНС-1 lamps, their 220 k ballasts and the MPSA42 that returns them.")]
GROUPS = {"power": ["power"], "hv": ["hv"], "anodes": ["anodes", "digits"], "colon": ["colon"]}
BOARD_OF = {"drv": "TS06-DRV", "disp": "TS06-DISP"}


def layout_svg(board, parts, hl, title):
    e = parts["edge"]
    W, H = e[1] - e[0], e[3] - e[2]
    pad = 6
    s = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="%g %g %g %g" font-family="IBM Plex Mono, monospace">'
         % (e[0] - pad, e[2] - pad - 6, W + 2 * pad, H + 2 * pad + 6),
         '<rect x="%g" y="%g" width="%g" height="%g" fill="#15171a"/>' % (e[0] - pad, e[2] - pad - 6, W + 2 * pad, H + 2 * pad + 6),
         '<text x="%g" y="%g" font-size="3.2" fill="#c9c4bb">%s · parts of this section in orange · generated stub</text>' % (e[0], e[2] - 3, html.escape(title)),
         '<rect x="%g" y="%g" width="%g" height="%g" fill="#050505" stroke="#8a8a8a" stroke-width="0.3"/>' % (e[0], e[2], W, H)]
    for ref, p in sorted(parts["parts"].items()):
        b = p.get("box")
        if not b:
            continue
        on = ref in hl
        s.append('<rect x="%g" y="%g" width="%g" height="%g" fill="%s" stroke="%s" stroke-width="%g"/>'
                 % (b[0], b[2], b[1] - b[0], b[3] - b[2], "rgba(255,138,61,.35)" if on else "none",
                    "#ff8a3d" if on else "#e8e8e8", 0.35 if on else 0.12))
        for q in p.get("pads", []):
            s.append('<circle cx="%g" cy="%g" r="0.55" fill="%s"/>' % (q[1], q[2], "#ffb27a" if on else "#b9a36a"))
        if on:
            s.append('<text x="%g" y="%g" font-size="2.6" fill="#ffffff" text-anchor="middle">%s</text>'
                     % ((b[0] + b[1]) / 2, (b[2] + b[3]) / 2 + 0.9, html.escape(ref)))
    s.append("</svg>")
    return "\n".join(s)


def list_svg(title, rows, nets):
    h = 28 + 14 * (len(rows) + 3) + 14 * ((len(nets) + 5) // 6)
    s = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 %d" font-family="IBM Plex Mono, monospace" font-size="11">' % h,
         '<rect width="640" height="%d" fill="#ffffff"/>' % h,
         '<text x="16" y="22" font-size="14" font-weight="600" fill="#1d1b18">%s</text>' % html.escape(title),
         '<text x="16" y="38" fill="#a16207">STUB: the real schematic sheet appears here once sch/out/sections.json exists.</text>']
    y = 58
    for ref, val, pins in rows:
        s.append('<text x="16" y="%d" fill="#1d1b18"><tspan font-weight="600">%s</tspan>  %s</text>' % (y, html.escape(ref), html.escape(val)))
        s.append('<text x="190" y="%d" fill="#6b665d">%s</text>' % (y, html.escape(pins[:70])))
        y += 14
    y += 8
    s.append('<text x="16" y="%d" fill="#1d1b18" font-weight="600">Nets</text>' % y)
    for i in range(0, len(nets), 6):
        y += 14
        s.append('<text x="16" y="%d" fill="#c2410c">%s</text>' % (y, html.escape("  ".join(nets[i:i + 6]))))
    s.append("</svg>")
    return "\n".join(s)


def stub(site, repo, parts_all):
    sys.dont_write_bytecode = True
    sys.path.insert(0, os.path.join(repo, "tools"))
    import ts06pair as P                                                  # noqa: E402
    os.makedirs(os.path.join(site, "sch", "stub"), exist_ok=True)
    out = []
    for sid, title, summary in STUB:
        ps = [p for p in P.PARTS if p.group in GROUPS[sid]]
        boards = sorted({BOARD_OF[p.board] for p in ps})
        nets = sorted({n for p in ps for n in p.pins.values() if n and n not in ("GND",)})
        rows = [(p.ref, p.value, " ".join("%s:%s" % (k, v or "-") for k, v in p.pins.items())) for p in ps]
        sch = "sch/stub/%s-sch.svg" % sid
        open(os.path.join(site, sch), "w", encoding="utf8").write(list_svg(title, rows, nets))
        lay = []
        for b in boards:
            refs = {p.ref for p in ps if BOARD_OF[p.board] == b}
            f = "sch/stub/%s-%s.svg" % (sid, b)
            open(os.path.join(site, f), "w", encoding="utf8").write(layout_svg(b, parts_all[b], refs, "%s — %s" % (b, title)))
            lay.append(f)
        out.append({"id": sid, "title": title, "boards": boards, "summary": summary, "schematic": [sch],
                    "layout": lay, "parts": [p.ref for p in ps], "nets": nets})
    return {"source": "stub", "sections": out}


def main(src, site, repo, parts_json):
    os.makedirs(os.path.join(site, "data"), exist_ok=True)
    shutil.rmtree(os.path.join(site, "sch"), ignore_errors=True)
    if os.path.isfile(os.path.join(src, "sections.json")):
        res, n = copy_real(src, site)
        print("sections: %d from %s, %d files copied" % (len(res["sections"]), src, n))
    else:
        res = stub(site, repo, json.load(open(parts_json, encoding="utf8")))
        print("sections: %s has no sections.json yet - wrote a %d-section stub" % (src, len(res["sections"])))
    json.dump(res, open(os.path.join(site, "data", "sections.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(*sys.argv[1:5])
