#!/usr/bin/env python3
"""TS06-DISP and TS06-DRV: the one-board netlist cut in two, joined by one stacking connector.

WHY: TS06-MAIN puts the whole clock on one 176 x 96 mm board and every complaint about it comes
back to that. Mounting holes end up wherever the copper left room. Cathode switches get stuffed
INSIDE the tube sockets' pin rings, where two of their emitters then cannot reach ground at all.
The Nano sits in a corner with twenty-eight connections reaching across the board, which is 16%
of the routing floor by itself (tools/placecheck.py). The inherited AlexGyver board is two boards
for exactly these reasons, and tools/boardsplit.py priced the seam at eighteen wires.

THE PARTITION, and why it is this one and not a tidier-looking one. Three depths were measured
with tools/boardsplit.py on the through-hole board:

    A  the tubes and their own drivers        18 wires, SEVEN of them at 185 V
    B  A + the six ИН-12 anode drivers        18 wires, ONE of them at 185 V
    C  B + the whole 185 V converter          23 wires, none at 185 V

B is taken. It crosses no more wires than A while leaving the switched anodes on the board the
tubes are on - which is where they belong electrically anyway, since an anode line is 185 V and
wants to be short - so the ONLY high-voltage conductor between the boards is the rail itself.
The six anode drives become ordinary 5 V Nano pins. C removes even that, and costs five more
wires and a display board packed to 97% of its area; its eight-part driver board is barely worth
fabricating.

THE KEY. The owner chose stacking headers, which are not polarised: mate them one row over and
185 V lands on a logic pin. So position 4 carries NO PIN - it is plugged on the socket and
snipped on the header - and the rail sits at position 1 behind two grounds, as far from the logic
as the connector allows.

Names: the display board is TS06-DISP (176 x 96 mm, the tube positions unchanged, what the fascia
sees), the driver board TS06-DRV (small, behind it on standoffs, carrying the Nano, the RTC, the
converter, the switches and the power inlet).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ts06main as M


def _n(prefix, a, b):
    return {f"{prefix}{k}" for k in range(a, b + 1)}


# Everything the fascia shows, everything that drives it, and - per B above - the six ИН-12
# anode drivers with their resistors and bleeds.
DISPLAY = (
    _n("V", 1, 10)                      # six ИН-12, two ИН-15, two ИНС-1 colon lamps
    | _n("HL", 1, 9)                    # eight backlight LEDs and the "m" dot
    | {"U2"}                            # К155ИД1: its ten cathode lines stop crossing, four BCD start
    | {"U3", "U4"}                      # both MCP23017: eighteen ИН-15 cathodes become SDA and SCL
    | _n("VT", 1, 19)                   # the colon switch and the eighteen ИН-15 cathode switches
    | _n("R", 1, 19)                    # their base resistors
    | _n("R", 45, 59)                   # backlight, colon and dot resistors, expander pull-ups
    | {"U5", "U6", "U7", "U8", "U9", "U10", "VT20"}    # the six anode drivers and the dot switch
    | _n("R", 20, 44)                   # anode resistors, the DNP bleeds, the driver base resistors
    | {"C1", "C2", "C3", "C4", "C11", "C13"}           # decoupling that belongs to the above
)

DISP, DRV = "disp", "drv"
BOARDS = (DISP, DRV)
TITLE = {DISP: "TS06-DISP", DRV: "TS06-DRV"}

# The connector, position by position. None is the key: no pin, plugged on the socket side.
# 2 x 12 at 2.54 mm. The rail is at 1 with grounds at 2 and 3 and the key at 4 behind it, so the
# nearest logic pin is two positions and two grounds away from 185 V.
PINOUT = [
    "HV185", "GND",        # 1  2
    "GND", None,           # 3  4   <- the key
    "+5V", "GND",          # 5  6
    "D2", "D3",            # 7  8   ИН-12 anode drives, now plain 5 V logic
    "D4", "D5",            # 9  10
    "D6", "D11",           # 11 12
    "D13", "GND",          # 13 14
    "A0", "A1",            # 15 16  BCD into the К155ИД1
    "A2", "A3",            # 17 18
    "GND", "GND",          # 19 20
    "SDA", "SCL",          # 21 22  both expanders
    "D10", "D12",          # 23 24  colon switch, "m" dot
]
KEY_PIN = PINOUT.index(None) + 1
CONN = {DISP: "XJ1", DRV: "XJ2"}


def side(ref):
    return DISP if ref in DISPLAY else DRV


def crossing(build="tht"):
    """Nets with a pad on both boards. These, and only these, are what the connector carries."""
    out = []
    for n, pads in M.nets(build).items():
        if len({side(p.split(".")[0]) for p in pads}) > 1:
            out.append(n)
    return sorted(out)


def _connector(board, build):
    """One half of the stacking pair, as a Part with the pinout above."""
    pins = {i + 1: n for i, n in enumerate(PINOUT) if n}
    kind = "CONN_2x12_HDR" if board == DISP else "CONN_2x12_SKT"
    return M.Part(CONN[board], f"2x12 2.54 {'header' if board == DISP else 'socket'}",
                  "CONN_2x12", kind, pins, "connector",
                  f"position {KEY_PIN} has no pin: the key. 185 V on 1.", builds=(build,))


def parts(board, build="tht"):
    return [p for p in M.parts(build) if side(p.ref) == board] + [_connector(board, build)]


def nets(board, build="tht"):
    out = {}
    for p in parts(board, build):
        for pin, n in p.pins.items():
            if n:
                out.setdefault(n, []).append(f"{p.ref}.{pin}")
    return out


def check(build="tht"):
    """Every crossing net must appear on the connector, and nothing else should need to."""
    bad, cross = [], set(crossing(build))
    carried = {n for n in PINOUT if n}
    for n in sorted(cross - carried):
        bad.append(f"{n} crosses the seam and the connector does not carry it")
    for n in sorted(carried - cross):
        bad.append(f"the connector carries {n}, which does not cross the seam")
    for board in BOARDS:
        for n, pads in nets(board, build).items():
            if len(pads) < 2:
                bad.append(f"{TITLE[board]}: {n} has one pad ({pads[0]}) and goes nowhere")
    known = {p.ref for p in M.parts(build)}
    for r in sorted(DISPLAY - known):
        bad.append(f"DISPLAY names {r}, which is not in the {build} build")
    return bad


if __name__ == "__main__":
    build = "smd" if "--smd" in sys.argv else "tht"
    cross = crossing(build)
    print(f"{build} build: {len(M.parts(build))} parts, {len(M.nets(build))} nets on one board")
    print(f"the seam: {len(cross)} wires -> {' '.join(cross)}")
    hv = [n for n in cross if n in M.HV_NETS]
    print(f"  at high voltage: {' '.join(hv) if hv else 'none'}")
    print(f"  connector: 2 x 12, key at position {KEY_PIN}, "
          f"{sum(1 for n in PINOUT if n == 'GND')} ground positions")
    print()
    for b in BOARDS:
        ps, ns = parts(b, build), nets(b, build)
        print(f"{TITLE[b]:10s} {len(ps):3d} parts, {len(ns):3d} nets, "
              f"{sum(len(v) for v in ns.values())} connected pins")
    print()
    bad = check(build)
    print("\n".join("  [SPLIT] " + b for b in bad) if bad else "the split is consistent")
    sys.exit(1 if bad else 0)
