#!/usr/bin/env python3
"""Checks of the WRITTEN board files with KiCad's own geometry (pcbnew). Run with KiCad's Python,
e.g. inside the KiCad 10 image (tools/verify_pair.sh does this):

    python3 tools/kicad_checks.py mate PCB/TS06-DISP/TS06-DISP.kicad_pcb PCB/TS06-DRV/TS06-DRV.kicad_pcb
    python3 tools/kicad_checks.py fill PCB/TS06-DISP/TS06-DISP.kicad_pcb PCB/TS06-DRV/TS06-DRV.kicad_pcb

WHY. check_mate() in tools/mkpcb_drv.py compares the generators' in-memory lists. It never reads the
files, a drill size or a face, and a red-team pass (30.09.26) planted three faults it passes: a
Ø2.5 standoff hole, a hole footprint moved 2 mm while the list stayed put, and both halves of a strip
on the wrong faces. `mate` reads what will be fabricated. `fill` counts the ground pours the way
KiCad fills them: tools/audit.py's grid model overstated TS06-DRV's islands about 7x.

mate: every XP pad of the display lands on an XS pad of the driver (x -> DW - x, y -> y + Y0) with
the same net and the same drill; every XP strip sits on the display's back and every XS strip on
the driver's back. The driver's component side faces the rear of the clock, which is why its x is
mirrored, so the two backs face each other across the strip gap. Every display hole has a driver
hole of the same drill.
fill: fills every zone and prints, per zone and layer, the pieces KiCad keeps, the share of the
largest, and how many are under 1 mm2. A pour that fills to nothing is a FAIL.
Output lines start with PASS or FAIL; the exit code is the number of FAILs (capped at 1).
"""
import sys
import pcbnew

DW, Y0 = 191.4, 26.0          # tools/mkpcb_drv.py: DRV x = DW - DISP x, DRV y = DISP y + Y0
mm = pcbnew.ToMM


def strip_pads(board, prefix):
    out, faces = {}, {}
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if not ref.startswith(prefix) or ref == "XS1":     # XS1 is the DC jack
            continue
        faces[ref] = "back" if fp.GetLayer() == pcbnew.B_Cu else "front"
        for p in fp.Pads():
            pos = p.GetPosition()
            out[(ref[2:], p.GetNumber())] = (mm(pos.x), mm(pos.y), p.GetNetname(), mm(p.GetDrillSize().x))
    return out, faces


def holes(board):
    out = []
    for fp in board.GetFootprints():
        if fp.GetReference().startswith("H") and not fp.GetReference().startswith("HL"):
            for p in fp.Pads():
                pos = p.GetPosition()
                out.append((fp.GetReference(), mm(pos.x), mm(pos.y), mm(p.GetDrillSize().x)))
    return out


def mate(disp_path, drv_path):
    disp, drv = pcbnew.LoadBoard(disp_path), pcbnew.LoadBoard(drv_path)
    xp, xp_face = strip_pads(disp, "XP")
    xs, xs_face = strip_pads(drv, "XS")
    bad = []
    for k, (x, y, net, dr) in sorted(xp.items()):
        if k not in xs:
            bad.append("XP%s pin %s has no XS%s pin" % (k[0], k[1], k[0]))
            continue
        X, Y, NET, DR = xs[k]
        if abs(DW - x - X) > 1e-3 or abs(y + Y0 - Y) > 1e-3:
            bad.append("XP%s.%s at (%.3f, %.3f) meets (%.3f, %.3f), not XS%s.%s at (%.3f, %.3f)"
                       % (k[0], k[1], x, y, DW - x, y + Y0, k[0], k[1], X, Y))
        if net != NET:
            bad.append("XP%s.%s is %s but XS%s.%s is %s" % (k[0], k[1], net or "(no net)", k[0], k[1], NET or "(no net)"))
        if abs(dr - DR) > 1e-3:
            bad.append("XP%s.%s drill %.2f against XS%s.%s drill %.2f" % (k[0], k[1], dr, k[0], k[1], DR))
    for k in sorted(set(xs) - set(xp)):
        bad.append("XS%s pin %s has no XP%s pin" % (k[0], k[1], k[0]))
    for ref, face in sorted(xp_face.items()):
        if face != "back":
            bad.append("%s is on the display's %s; the strips must face the driver (back)" % (ref, face))
    for ref, face in sorted(xs_face.items()):
        if face != "back":
            bad.append("%s is on the driver's %s; the sockets must face the display (the driver's back)"
                       % (ref, face))
    hd, hv = holes(disp), holes(drv)
    for ref, x, y, d in hd:
        m = [h for h in hv if abs(h[1] - (DW - x)) < 1e-3 and abs(h[2] - (y + Y0)) < 1e-3]
        if not m:
            bad.append("display hole %s at (%.3f, %.3f) has no driver hole at (%.3f, %.3f)" % (ref, x, y, DW - x, y + Y0))
        elif abs(m[0][3] - d) > 1e-3:
            bad.append("display hole %s drill %.2f against driver %s drill %.2f" % (ref, d, m[0][0], m[0][3]))
    nets = sum(1 for v in xp.values() if v[2])
    head = "%d strip pins (%d with a net), %d strips a side, %d standoff holes, from the written files" % (
        len(xp), nets, len(xp_face), len(hd))
    if bad:
        print("FAIL mate " + head)
        for b in bad:
            print("  " + b)
        return 1
    print("PASS mate " + head + ": positions, nets, drills and faces agree")
    return 0


def fill(paths):
    fails = 0
    for path in paths:
        b = pcbnew.LoadBoard(path)
        zones = list(b.Zones())
        pcbnew.ZONE_FILLER(b).Fill(zones)
        name = path.split("/")[-1]
        rows = []
        for z in zones:
            if z.GetIsRuleArea():
                continue
            for ly in z.GetLayerSet().Seq():
                poly = z.GetFilledPolysList(ly)
                areas = sorted((poly.Outline(i).Area() / 1e12 for i in range(poly.OutlineCount())), reverse=True)
                tot = sum(areas)
                rows.append("%s %s: %d pieces, the largest %.0f%% of %.0f mm2, %d under 1 mm2"
                            % (z.GetNetname(), b.GetLayerName(ly), len(areas),
                               100 * areas[0] / tot if tot else 0, tot, sum(1 for a in areas if a < 1)))
                if not areas:
                    fails += 1
                    rows[-1] += "  <- fills to nothing"
        print(("FAIL" if fails else "PASS") + " fill %s: %s" % (name, "; ".join(rows) or "no zones"))
    return 1 if fails else 0


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "mate":
        sys.exit(mate(sys.argv[2], sys.argv[3]))
    if len(sys.argv) >= 3 and sys.argv[1] == "fill":
        sys.exit(fill(sys.argv[2:]))
    sys.exit(__doc__)
