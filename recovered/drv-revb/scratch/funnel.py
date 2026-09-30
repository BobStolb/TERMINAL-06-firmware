"""funnel.py [JSON]: rubber-band crossings round J1 for a placement of the fascia RC block (DRV frame).
Each net is drawn as straight lines from where it enters the region (the gap, the column) through its
pads there; two nets' bands that cross must be paid for by a face change in the J1 funnel."""
import itertools, json, sys
J1 = {"+5V": (137.4, 95.0), "GND": (139.4, 95.0), "A6": (141.4, 95.0), "A7": (143.4, 95.0), "D7_J": (145.4, 95.0), "D8_J": (147.4, 95.0)}
ENTRY = {"A7": (153.4, 57.0), "A6": (152.95, 57.0), "D7": (167.8, 44.0), "D8": (168.4, 44.0),
         "SCL": (151.8, 53.1), "SDA": (151.8, 56.1)}
U13 = {"GND": (131.23, 74.27), "SCL": (126.15, 74.27), "SDA": (123.61, 74.27), "+5V": (121.07, 74.27)}


def cross(p, q, r, s):
    def o(a, b, c):
        v = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        return (v > 1e-9) - (v < -1e-9)
    if len({p, q, r, s}) < 4:
        return False
    return o(p, q, r) * o(p, q, s) < 0 and o(r, s, p) * o(r, s, q) < 0


def bands(rc):
    """rc: {ref: (pad 1, pad 2)}: R72 (A6, GND), R73 (D7, D7_J), R74 (D8, D8_J), C18 (D7_J, GND), C19 (D8_J, GND)."""
    b = [("A7", ENTRY["A7"], J1["A7"]),
         ("A6", ENTRY["A6"], rc["R72"][0]), ("A6", rc["R72"][0], J1["A6"]),
         ("D7", ENTRY["D7"], rc["R73"][0]), ("D8", ENTRY["D8"], rc["R74"][0]),
         ("D7_J", rc["R73"][1], rc["C18"][0]), ("D7_J", rc["C18"][0], J1["D7_J"]),
         ("D8_J", rc["R74"][1], rc["C19"][0]), ("D8_J", rc["C19"][0], J1["D8_J"]),
         ("GND", J1["GND"], U13["GND"]), ("+5V", J1["+5V"], U13["+5V"]),
         ("SCL", ENTRY["SCL"], U13["SCL"]), ("SDA", ENTRY["SDA"], U13["SDA"])]
    return b


def score(name, rc):
    b = bands(rc)
    xs = sorted((a[0], c[0]) for a, c in itertools.combinations(b, 2) if a[0] != c[0] and cross(a[1], a[2], c[1], c[2]))
    print(f"{name}: {len(xs)} forced crossings: " + ", ".join(f"{a} x {c}" for a, c in xs))
    return xs


PRED = {"R72": ((138.74, 90.39), (138.74, 80.22)), "R73": ((147.63, 79.59), (147.63, 89.75)),
        "R74": ((151.44, 77.05), (151.44, 87.21)), "C18": ((144.6, 90.39), (142.1, 90.39)),
        "C19": ((151.62, 89.75), (151.62, 92.25))}
if __name__ == "__main__":
    score("predecessor (near() at J1)", PRED)
    for a in sys.argv[1:]:
        score("candidate", {k: tuple(map(tuple, v)) for k, v in json.loads(a).items()})
