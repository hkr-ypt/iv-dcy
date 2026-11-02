#!/usr/bin/env python3
# SPDX-License-Identifier: CERN-OHL-S-2.0
# Copyright (c) 2026 Lucas Wu
"""
Compare the connectivity of two KiCad netlists (.net, s-expression format).

Used to prove that the drawn schematic (exported with kicad-cli) connects
exactly the same pads as the SKiDL netlist, and to check that every part
carries the same value and footprint in both.

    netlist_compare.py skidl.net schematic.net
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skidl"))
from sexpr import find, find_all, parse  # noqa: E402


def load(path):
    root = parse(Path(path).read_text())
    comps = {}
    for c in find_all(find(root, "components"), "comp"):
        ref = find(c, "ref")[1]
        if ref.startswith("#"):
            continue
        fp = find(c, "footprint")
        comps[ref] = (find(c, "value")[1], fp[1] if fp else "")
    nets = set()
    for n in find_all(find(root, "nets"), "net"):
        nodes = frozenset((find(x, "ref")[1], find(x, "pin")[1]) for x in find_all(n, "node")
                          if not find(x, "ref")[1].startswith("#"))
        if len(nodes) > 1 or (nodes and not find(n, "name")[1].startswith("unconnected")):
            nets.add((find(n, "name")[1].lstrip("/"), nodes))
    return comps, nets


def main(a, b):
    ca, na = load(a)
    cb, nb = load(b)
    ok = True
    for ref in sorted(set(ca) | set(cb)):
        if ca.get(ref) != cb.get(ref):
            print(f"component {ref}: {ca.get(ref)} != {cb.get(ref)}")
            ok = False
    # Compare by pad groups (names are compared too, ignoring a leading '/').
    ga = {nodes: name for name, nodes in na if len(nodes) > 1}
    gb = {nodes: name for name, nodes in nb if len(nodes) > 1}
    for nodes in set(ga) ^ set(gb):
        side = "only in " + (a if nodes in ga else b)
        print(f"net {ga.get(nodes) or gb.get(nodes)} {sorted(nodes)}: {side}")
        ok = False
    for nodes in set(ga) & set(gb):
        if ga[nodes] != gb[nodes]:
            print(f"net name differs: {ga[nodes]} vs {gb[nodes]}")
            ok = False
    print(f"{len(ca)} components, {len(ga)} multi-pad nets: " + ("MATCH" if ok else "MISMATCH"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
