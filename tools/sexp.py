#!/usr/bin/env python3
"""A small S-expression reader and writer for KiCad files.

WHY: every generator before this one edited footprints as text, with regular expressions
written against one exact indentation. That works until a footprint arrives from somewhere
else - KiCad's own library, a rotated variant, a flipped one - and then a pad is silently
missed. A footprint that has to be rotated, flipped to the back and given nets is a tree
operation, so it is done on a tree.

The writer follows KiCad 10's layout closely enough that the repo's regex-based checkers
(tools/checkcopper.py, tools/checkpcb.py, tools/audit.py) read its output unchanged: a list
that holds only atoms goes on one line - (at 1 2), (size 1.7 1.7), (layers "F.Cu" "B.Cu") -
and a list that holds lists opens a block with its children one tab deeper.

    tree = parse(text)          # nested Python lists; strings keep their quotes
    text = dump(tree)
"""
import re

_TOKEN = re.compile(r'\s*(?:(\()|(\))|("(?:[^"\\]|\\.)*")|([^\s()"]+))', re.S)


def parse(text):
    """Text to nested lists. Atoms stay strings; quoted strings keep their quotes, so
    writing a tree back out never has to guess which atoms were quoted."""
    stack, cur = [], []
    pos = 0
    while True:
        m = _TOKEN.match(text, pos)
        if not m or m.end() == pos:
            break
        pos = m.end()
        if m.group(1):
            stack.append(cur)
            cur = []
        elif m.group(2):
            done = cur
            cur = stack.pop()
            cur.append(done)
        else:
            cur.append(m.group(3) or m.group(4))
    if stack:
        raise ValueError("unbalanced parentheses")
    return cur[0] if len(cur) == 1 else cur


def dump(node, depth=0):
    """Nested lists to text, KiCad style."""
    if not isinstance(node, list):
        return str(node)
    ind = "\t" * depth
    if not any(isinstance(c, list) for c in node):
        return ind + "(" + " ".join(str(c) for c in node) + ")"
    head = []
    i = 0
    while i < len(node) and not isinstance(node[i], list):
        head.append(str(node[i]))
        i += 1
    lines = [ind + "(" + " ".join(head)]
    for c in node[i:]:
        lines.append(dump(c, depth + 1) if isinstance(c, list) else "\t" * (depth + 1) + str(c))
    lines.append(ind + ")")
    return "\n".join(lines)


def q(s):
    """Quote a Python string as a KiCad string atom."""
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def unq(a):
    return a[1:-1].replace('\\"', '"').replace("\\\\", "\\") if isinstance(a, str) and a.startswith('"') else a


def num(v):
    """A number as KiCad writes it: no trailing zeros, no exponent."""
    s = ("%.6f" % v).rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def find(node, key):
    """First child list whose head is key."""
    for c in node:
        if isinstance(c, list) and c and c[0] == key:
            return c
    return None


def find_all(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]


def walk(node):
    """Every list in the tree, depth first, the root included."""
    yield node
    for c in node:
        if isinstance(c, list):
            yield from walk(c)
