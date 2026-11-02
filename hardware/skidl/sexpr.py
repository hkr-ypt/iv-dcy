# SPDX-License-Identifier: CERN-OHL-S-2.0
# Copyright (c) 2026 Lucas Wu
"""Tiny S-expression reader/writer for KiCad files (lists of str/Sym)."""

import re


class Sym(str):
    """An unquoted atom (keyword or number) as opposed to a quoted string."""


_TOKEN = re.compile(r'\s*(?:(\()|(\))|"((?:[^"\\]|\\.)*)"|([^\s()"]+))', re.S)


def parse(text):
    """Parse one S-expression; quoted strings become str, atoms become Sym."""
    stack, cur = [], []
    pos = 0
    n = len(text)
    while pos < n:
        m = _TOKEN.match(text, pos)
        if not m:
            if text[pos:].strip() == "":
                break
            raise ValueError("bad s-expression near %r" % text[pos:pos + 40])
        pos = m.end()
        if m.group(1):
            stack.append(cur)
            cur = []
        elif m.group(2):
            done = cur
            cur = stack.pop()
            cur.append(done)
        elif m.group(3) is not None:
            cur.append(m.group(3).replace('\\"', '"').replace("\\\\", "\\"))
        else:
            cur.append(Sym(m.group(4)))
    if len(cur) != 1:
        raise ValueError("expected exactly one top-level expression")
    return cur[0]


def _atom(x):
    if isinstance(x, Sym):
        return str(x)
    if isinstance(x, bool):
        return "yes" if x else "no"
    if isinstance(x, int):
        return str(x)
    if isinstance(x, float):
        s = ("%.4f" % x).rstrip("0").rstrip(".")
        return "0" if s in ("-0", "") else s
    return '"%s"' % str(x).replace("\\", "\\\\").replace('"', '\\"')


def dump(node, indent=0):
    """Serialise in KiCad's style: one nested list per line, tab indented."""
    if not isinstance(node, list):
        return _atom(node)
    head = [_atom(x) for x in node if not isinstance(x, list)]
    kids = [x for x in node if isinstance(x, list)]
    # Atoms that follow a child list (rare) are kept in order.
    if not kids:
        return "(" + " ".join(head) + ")"
    out = "(" + " ".join(_atom(x) for x in node[:1])
    for x in node[1:]:
        if isinstance(x, list):
            out += "\n" + "\t" * (indent + 1) + dump(x, indent + 1)
        else:
            out += " " + _atom(x)
    return out + "\n" + "\t" * indent + ")"


def find(node, key):
    """First child list whose head is `key`."""
    for x in node:
        if isinstance(x, list) and x and x[0] == key:
            return x
    return None


def find_all(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]
