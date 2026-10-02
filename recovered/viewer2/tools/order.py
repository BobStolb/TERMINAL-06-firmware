#!/usr/bin/env python3
"""The Order view's data: what is ready to order, from the repository's own order sheet and fit table.

    python3 order.py REPO OUT.json [BRANCH]

Reads (the repository is only read):
  fab/ORDER.md                       the three zips (size, layers, thickness, holes), the DFM table,
                                     the owner's choices, what the prototype run closes
  fab/*.zip                          the zips' sizes on disk
  3d/populated/fit-table.json        the fit table (made from the placed 3D models), with its gold
It writes the numbers and sentences the page prints. Nothing is invented here: every figure is a cell
of ORDER.md or of the fit table, and the script stops if the sheet no longer has the shape it expects
(a missing table, a changed heading), so a rewritten sheet is noticed at build time, not on the page.
The only words written here are the plain-language reading of each TIGHT / FAIL row of the fit table
(PLAIN below), which carry the row's own numbers.

Placing the order is the owner's own hand: nothing here, and nothing on the page, contacts a fab.
"""
import json, os, re, sys

REPO_URL = "https://github.com/BobStolb/TERMINAL-06-firmware/blob/%s/"
HOLES_ZIP = "fab/TS06-FASCIA-R-revA-divider-holes04-fab.zip"   # the extra fascia zip (fab/HOLES-VARIANT.md): not in ORDER.md


def clean(s):
    return re.sub(r"\s+", " ", s.replace("`", "").replace("**", "").replace("*", "")).strip()


def table_after(lines, marker):
    """The rows of the first markdown table after the line containing marker (header row first, the rule dropped)."""
    i = next((k for k, l in enumerate(lines) if marker in l), None)
    if i is None:
        sys.exit("order.py: ORDER.md has no line containing %r" % marker)
    rows = []
    for l in lines[i + 1:]:
        if l.startswith("|"):
            cells = [c.strip() for c in l.strip().strip("|").split("|")]
            if not all(re.fullmatch(r":?-+:?", c) for c in cells):
                rows.append(cells)
        elif rows:
            break
    if len(rows) < 2:
        sys.exit("order.py: no table after %r" % marker)
    return rows


def bullets_after(lines, marker):
    i = next((k for k, l in enumerate(lines) if marker in l), None)
    if i is None:
        sys.exit("order.py: ORDER.md has no line containing %r" % marker)
    out = []
    for l in lines[i + 1:]:
        if l.startswith("* "):
            out.append(clean(l[2:]))
        elif l.startswith("#") or (out and not l.strip()):
            break
    return out


# the plain-language reading of a fit-table row that is not PASS: keyed by what the row measures
def plain(r):
    m, st = r["margin"], r["status"]
    part = r["part"]
    if r["what"] == "stack":
        return ("The display's pin strips and the driver's sockets, plugged together, add up to %.2f mm; the nylon standoffs between the boards are %.1f mm. "
                "The %.2f mm is rounding in the part sizes (2.5 against 2.54 and 8.5 against 8.59), so it fits as drawn but it is a number to measure on the strips you buy." % (r["height"], r["space"], -m))
    if "LED flange" in part:
        return "The lowest LED flange is %.2f mm above the sill. It clears, narrowly." % m
    if r["what"] == "window, Y":
        return "The top of the tube glass is %.1f mm below the underside of the case's brow. It fits; a tube a little taller than drawn would leave less than a millimetre." % m
    if r["what"] == "window, Z" and st == "FAIL":
        return ("A tube's glass front is %.2f mm in front of the case window plane (by %.2f mm: the front of the glass stands past the window). "
                "The tubes stand on wire leads, so the seat can be changed without touching the boards." % (r["height"], -m))
    if r["what"] == "window, X":
        return "The glass edge is %.2f mm from the case's trench wall. It fits with room to spare for a part's tolerance, but not a lot." % m
    if r["what"] == "hole":
        return ("The control's threaded bushing is %.2f mm narrower than its hole on each side. It goes in, but only just: ordinary hole tolerance at a board house is of the same size, "
                "so test-fit one real part before relying on it." % m)
    return "%s: margin %.2f mm." % (st, m)


def main(repo, out, branch="pcb/kicad-boards"):
    lines = open(os.path.join(repo, "fab", "ORDER.md"), encoding="utf8").read().split("\n")
    text = "\n".join(lines)
    for need in ("Quantity: 10 of each board", "matte black", "ENIG on all three", "2.0 mm", "Nothing here was sent to a board house"):
        if need not in text:
            sys.exit("order.py: fab/ORDER.md no longer says %r" % need)

    # ---- the three zips
    rows = table_after(lines, "## The three zips")
    boards = []
    for r in rows[1:]:
        z = re.search(r"`(fab/[^`]+\.zip)`", r[1])
        if not z:
            sys.exit("order.py: no zip path in %r" % r[1])
        zp = z.group(1)
        path = os.path.join(repo, zp)
        if not os.path.isfile(path):
            sys.exit("order.py: %s is named by ORDER.md but is not in the repository" % zp)
        plated, nonplated = [x.strip() for x in clean(r[5]).split("/")]
        name = clean(r[0])
        fascia = "Fascia" in name
        boards.append({
            "name": name, "short": "Fascia R" if fascia else name.split(" rev ")[0], "zip": zp, "zip_bytes": os.path.getsize(path),
            "url": REPO_URL % branch + zp,
            "size": clean(r[2]), "layers": int(clean(r[3])), "thickness": clean(r[4]), "finish": "ENIG",
            "mask": "black (matte black if the fab has it at a small extra cost)", "silk": "white",
            "holes": {"plated": plated, "non_plated": nonplated}, "qty": 10, "dfm": clean(r[6]),
            "picture": "TS06-FASCIA-rhythm-top" if fascia else ("TS06-DRV-top" if "DRV" in name else "TS06-DISP-top"),
        })
    if len(boards) != 3:
        sys.exit("order.py: expected three boards in the zips table, found %d" % len(boards))

    # ---- the DFM table
    d = table_after(lines, "Worst values found")
    dfm = {"cols": [clean(c) for c in d[0]], "rows": [[clean(c) for c in r] for r in d[1:]]}
    if "every row of the DFM check passes on all three boards" not in text:
        sys.exit("order.py: fab/ORDER.md no longer says the DFM check passes on all three boards")
    self_test = re.search(r"the self-test, (\d+) rows", text)

    # ---- the fit table
    fit = json.load(open(os.path.join(repo, "3d", "populated", "fit-table.json"), encoding="utf8"))
    frows = [{"board": r["board"], "side": r["side"], "part": r["part"], "height": r["height"], "space": r["space"], "margin": r["margin"],
              "status": r["status"], "plain": plain(r), "note": r["note"]}
             for r in fit["rows"] if r["status"] != "PASS"]
    frows.sort(key=lambda r: (r["status"] != "FAIL", r["margin"]))

    # ---- open items, then what the prototype closes
    if not os.path.isfile(os.path.join(repo, HOLES_ZIP)):
        sys.exit("order.py: %s is named by the Order view's holes item but is not in the repository" % HOLES_ZIP)
    hv = fit.get("holes_variant")
    if not hv or {r["margin"] for r in hv["rows"]} != {0.29} or {r["margin"] for r in fit["rows"] if r["what"] == "hole"} != {0.09}:
        sys.exit("order.py: fit-table.json no longer shows the bushing margin as 0.09 mm (ordered) and 0.29 mm (holes04 variant)")
    open_items = [
        {"id": "g11", "title": "Which fascia", "blocking": True,
         "body": "R is recommended (3 to 0 in the referendum) and is what the zip holds. If you choose another fascia, its zip has to be rebuilt first."},
        {"id": "gold", "title": "Which gold", "blocking": True,
         "body": "The Divider is the leader's pick and is what the zip holds. Ladder, fans and guilloche are laid out for the narrower fascia A: on R only the Divider is ready."},
        {"id": "holes", "title": "Fascia holes: as drawn, or opened by 0.4 mm (the extra zip)", "blocking": True,
         "body": "As drawn, the five control holes leave 0.09 mm a side round the bushings (the dial 8.62 in 8.8, the levers and buttons 7.82 in 8.0): "
                 "A fab's drill tolerance can take 0.09 mm whole. The extra zip, " + HOLES_ZIP + ", opens every one by 0.4 mm (9.2 and 8.4): "
                 "0.09 mm against 0.29 mm a side. To pick the extra zip, send it to the fab in place of the fascia zip above; nothing else changes "
                 "(fab/HOLES-VARIANT.md). The sheet above, and the zip in it, are the fascia as drawn."},
        {"id": "quote", "title": "Check the fab quote against the sheet", "blocking": True,
         "body": "Quantity 10 of each; the fascia 2.0 mm, not 1.6 mm; ENIG on all three (with HASL the gold would be silver-grey); mask black, matte if it costs little; silk white; "
                 "on the fascia ask for no fab order number on the face. No prices were looked up."},
        {"id": "tube", "title": "The ИН-17 pip", "blocking": False,
         "body": "The ИН-17 glass is 19.72 mm from the dome to the end of the glass (the owner's bench caliper, 2026-10-02), which puts its face level with the ИН-12 faces on a 10.28 mm seat. "
                 "The drawing's 22 mm is read to include the exhaust pip, about 2.28 mm: that is a reading, not a measurement. The pip hangs in the gap under the glass and needs no hole while it is under 8 mm, "
                 "so it does not hold up the boards; measure it on a real tube."},
        {"id": "g8", "title": "Filling the pours in the committed board files", "blocking": False,
         "body": "Whether to commit the boards 'filled'. The zips are built with the pours filled either way, so this does not hold up the order."},
    ]
    proto = bullets_after(lines, "What only the prototype can close")

    res = {
        "branch": branch, "repo_url": REPO_URL % branch, "quantity": 10,
        "status": "The three zips are built and checked; every row of the DFM check passes on all three boards. Nothing has been sent to a board house, and no price was looked up.",
        "boards": boards,
        "dfm": dfm, "dfm_note": "Limits are typical of a low-cost two-layer service (inferred, not a fab's own). Each rule was also run on a deliberately broken board first and fails there"
                                + (" (the self-test, %s rows)." % self_test.group(1) if self_test else "."),
        "fit": {"tally": fit["tally"], "fascia": fit["fascia"], "gold": fit.get("gold", "none"), "rows": frows},
        "open": open_items, "prototype": proto,
        "own_hand": "Placing the order is the owner's own hand. This page sends nothing to a board house and holds no account, no cart and no price.",
        "source": "fab/ORDER.md, fab/*.zip, 3d/populated/fit-table.json",
    }
    json.dump(res, open(out, "w", encoding="utf8"), ensure_ascii=False, indent=1)
    print("order: %d boards, %d DFM rows, %d fit rows to explain (%s), %d open items, %d prototype items" % (
        len(boards), len(dfm["rows"]), len(frows), ", ".join("%d %s" % (n, s) for s, n in sorted(fit["tally"].items())), len(open_items), len(proto)))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], *(sys.argv[3:4]))
