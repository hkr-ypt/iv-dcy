# SPDX-License-Identifier: CERN-OHL-S-2.0
# Copyright (c) 2026 Lucas Wu
"""
Minimal KiCad 9 schematic writer.

Draws a flat, label-based schematic from a list of parts (as produced by
iv_dcy.py from the SKiDL circuit) and a hand-chosen placement table:

* every connected pin gets a short wire stub ending in a net label, or in a
  power symbol for the power nets (GND, +3V3, VBUS);
* every unconnected pin gets a no-connect flag;
* PWR_FLAG symbols mark the nets that are supplied from off the board.

Because each pin is joined to its net only through a label, the drawing
cannot introduce a connection the SKiDL circuit does not have; the build
script additionally exports the netlist back out of this schematic with
kicad-cli and checks it against the SKiDL netlist.

Library symbols are copied from the installed KiCad libraries (derived
"extends" symbols are flattened, as KiCad itself does when it saves).
"""

import copy
import uuid
from pathlib import Path

from sexpr import Sym, dump, find, find_all, parse

GRID = 1.27
STUB = 2.54
POWER_NETS = {"GND": "GND", "+3V3": "+3V3", "VBUS": "VBUS"}
NS = uuid.UUID("6f0d3b0e-6a2f-4c55-9a43-5d1f2d7c9b10")


def uid(*parts):
    """Deterministic UUID so that regenerating gives an identical file."""
    return str(uuid.uuid5(NS, "/".join(str(p) for p in parts)))


def snap(v):
    return round(round(v / GRID) * GRID, 4)


class SymbolLibrary:
    def __init__(self, symbol_dir):
        self.dir = Path(symbol_dir)
        self._libs = {}

    def _lib(self, nick):
        if nick not in self._libs:
            self._libs[nick] = parse((self.dir / f"{nick}.kicad_sym").read_text())
        return self._libs[nick]

    def _raw(self, nick, name):
        for s in find_all(self._lib(nick), "symbol"):
            if s[1] == name:
                return s
        raise KeyError(f"{nick}:{name} not found in {self.dir}")

    def get(self, nick, name):
        """Flattened symbol named 'nick:name', ready for a schematic."""
        sym = copy.deepcopy(self._raw(nick, name))
        ext = find(sym, "extends")
        if ext is not None:
            parent = self.get(nick, ext[1])
            props = find_all(sym, "property")
            body = [x for x in parent[2:] if not (isinstance(x, list) and x[0] == "property")]
            pname = parent[1].split(":", 1)[1]
            for x in body:
                if isinstance(x, list) and x[0] == "symbol":
                    x[1] = x[1].replace(pname, name, 1)
            # Keep the parent's flags (pin_names, in_bom, ...) then the child's
            # properties, then the graphics/pins.
            head = [x for x in body if not (isinstance(x, list) and x[0] == "symbol")]
            units = [x for x in body if isinstance(x, list) and x[0] == "symbol"]
            sym = [Sym("symbol"), name] + head + props + units
        sym[1] = f"{nick}:{name}"
        return sym

    @staticmethod
    def pins(sym):
        """[(number, name, x, y, angle)] in symbol coordinates (y up)."""
        out = []

        def walk(n):
            for x in n:
                if isinstance(x, list):
                    if x and x[0] == "pin":
                        at = find(x, "at")
                        out.append((find(x, "number")[1], find(x, "name")[1],
                                    float(at[1]), float(at[2]), int(float(at[3]))))
                    else:
                        walk(x)
        walk(sym)
        return out


def _rot(px, py, angle):
    """Symbol coords (y up) -> schematic offset (y down) for a symbol rotation."""
    x, y = px, -py
    if angle == 0:
        return x, y
    if angle == 90:
        return y, -x
    if angle == 180:
        return -x, -y
    if angle == 270:
        return -y, x
    raise ValueError(angle)


def _dir(pin_angle, sym_angle):
    """Unit vector (schematic coords) pointing from the pin end away from the body."""
    a = (pin_angle + 180 + sym_angle) % 360
    return {0: (1, 0), 90: (0, -1), 180: (-1, 0), 270: (0, 1)}[a]


def _font(size=1.27, justify=None, hide=False):
    eff = [Sym("effects"), [Sym("font"), [Sym("size"), size, size]]]
    if justify:
        eff.append([Sym("justify")] + [Sym(j) for j in justify])
    if hide:
        eff.append([Sym("hide"), Sym("yes")])
    return eff


def _prop(name, value, x, y, angle=0, hide=False, justify=None):
    return [Sym("property"), name, value, [Sym("at"), x, y, angle],
            _font(justify=justify, hide=hide)]


class Schematic:
    def __init__(self, project, title, symbol_dir, paper="A4", rev="", date="",
                 comments=()):
        self.project = project
        self.lib = SymbolLibrary(symbol_dir)
        self.root = uid(project, "root")
        self.items = []
        self.lib_symbols = {}
        self.pwr_count = 0
        self.flg_count = 0
        self.title = title
        self.paper = paper
        self.rev = rev
        self.date = date
        self.comments = comments

    # ---- primitives --------------------------------------------------------
    def _use(self, nick, name):
        key = f"{nick}:{name}"
        if key not in self.lib_symbols:
            self.lib_symbols[key] = self.lib.get(nick, name)
        return self.lib_symbols[key]

    def wire(self, x1, y1, x2, y2):
        self.items.append([Sym("wire"), [Sym("pts"), [Sym("xy"), x1, y1], [Sym("xy"), x2, y2]],
                           [Sym("stroke"), [Sym("width"), 0], [Sym("type"), Sym("default")]],
                           [Sym("uuid"), uid("wire", x1, y1, x2, y2)]])

    def label(self, name, x, y, direction):
        angle = {(1, 0): 0, (-1, 0): 180, (0, -1): 90, (0, 1): 270}[direction]
        just = ["left", "bottom"] if angle in (0, 90) else ["right", "bottom"]
        self.items.append([Sym("label"), name, [Sym("at"), x, y, angle],
                           _font(justify=just), [Sym("uuid"), uid("label", name, x, y)]])

    def no_connect(self, x, y):
        self.items.append([Sym("no_connect"), [Sym("at"), x, y], [Sym("uuid"), uid("nc", x, y)]])

    def text(self, s, x, y, size=1.27):
        self.items.append([Sym("text"), s, [Sym("exclude_from_sim"), Sym("no")],
                           [Sym("at"), x, y, 0], _font(size=size, justify=["left", "bottom"]),
                           [Sym("uuid"), uid("text", s, x, y)]])

    def _symbol(self, nick, name, ref, value, x, y, angle=0, fields=None,
                ref_at=None, val_at=None, in_bom=True, on_board=True, hide_ref=False):
        sym = self._use(nick, name)
        lib_props = {p[1]: p for p in find_all(sym, "property")}
        node = [Sym("symbol"), [Sym("lib_id"), f"{nick}:{name}"], [Sym("at"), x, y, angle],
                [Sym("unit"), 1], [Sym("exclude_from_sim"), Sym("no")],
                [Sym("in_bom"), Sym("yes" if in_bom else "no")],
                [Sym("on_board"), Sym("yes" if on_board else "no")],
                [Sym("dnp"), Sym("no")], [Sym("uuid"), uid("sym", ref)]]
        rx, ry = ref_at if ref_at else (x, y - 5.08)
        vx, vy = val_at if val_at else (x, y + 5.08)
        node.append(_prop("Reference", ref, rx, ry, hide=hide_ref))
        node.append(_prop("Value", value, vx, vy))
        fields = dict(fields or {})
        for key in ("Footprint", "Datasheet", "Description"):
            if key not in fields:
                p = lib_props.get(key)
                fields[key] = p[2] if p else ""
        for key, val in fields.items():
            node.append(_prop(key, val, x, y, hide=True))
        for num, *_ in self.lib.pins(sym):
            node.append([Sym("pin"), num, [Sym("uuid"), uid("pin", ref, num)]])
        node.append([Sym("instances"), [Sym("project"), self.project,
                     [Sym("path"), f"/{self.root}", [Sym("reference"), ref], [Sym("unit"), 1]]]])
        self.items.append(node)
        return sym

    def power(self, net, x, y):
        self.pwr_count += 1
        ref = "#PWR%03d" % self.pwr_count
        below = net == "GND"
        self._symbol("power", POWER_NETS[net], ref, net, x, y,
                     ref_at=(x, y + 6.35 if below else y - 6.35),
                     val_at=(x, y + 3.81 if below else y - 3.81),
                     in_bom=False, on_board=False, hide_ref=True)

    def pwr_flag(self, x, y):
        self.flg_count += 1
        ref = "#FLG%02d" % self.flg_count
        self._symbol("power", "PWR_FLAG", ref, "PWR_FLAG", x, y,
                     ref_at=(x, y - 6.35), val_at=(x, y - 3.81),
                     in_bom=False, on_board=False, hide_ref=True)

    def junction(self, x, y):
        self.items.append([Sym("junction"), [Sym("at"), x, y], [Sym("diameter"), 0],
                           [Sym("color"), 0, 0, 0, 0], [Sym("uuid"), uid("junction", x, y)]])

    # ---- a whole part, wired to its nets by stubs ---------------------------------
    def part(self, p, x, y, angle=0, ref_at=None, val_at=None, stub=STUB):
        """p: dict(ref, lib, name, value, footprint, fields, pins={num: net|None}).

        ref_at / val_at are offsets from the symbol origin for the reference
        and value text.  Power pins on the same side and net (for example the
        three +3V3 pins on top of the MCU) are bussed to one power symbol.
        """
        x, y = snap(x), snap(y)
        if ref_at:
            ref_at = (x + ref_at[0], y + ref_at[1])
        if val_at:
            val_at = (x + val_at[0], y + val_at[1])
        sym = self._symbol(p["lib"], p["name"], p["ref"], p["value"], x, y, angle,
                           fields=dict(Footprint=p["footprint"], **p.get("fields", {})),
                           ref_at=ref_at, val_at=val_at)
        done = set()
        groups = {}
        for num, _name, px, py, pang in self.lib.pins(sym):
            dx, dy = _rot(px, py, angle)
            ex, ey = round(x + dx, 4), round(y + dy, 4)
            if (ex, ey) in done:        # stacked pins share one stub
                continue
            done.add((ex, ey))
            net = p["pins"].get(num)
            if net is None:
                self.no_connect(ex, ey)
                continue
            ux, uy = _dir(pang, angle)
            sx, sy = round(ex + ux * stub, 4), round(ey + uy * stub, 4)
            self.wire(ex, ey, sx, sy)
            if net in POWER_NETS:
                row = sy if ux == 0 else sx
                groups.setdefault((net, ux, uy, row), []).append((sx, sy))
            else:
                self.label(net, sx, sy, (ux, uy))
        for (net, ux, uy, _row), ends in groups.items():
            ends.sort()
            for (ax, ay), (bx, by) in zip(ends, ends[1:]):
                self.wire(ax, ay, bx, by)
            for jx, jy in ends[1:-1]:
                self.junction(jx, jy)
            self.power(net, *ends[0])

    def flagged_power(self, net, x, y):
        """A PWR_FLAG on `net`: flag and power symbol joined by a short wire."""
        if net == "GND":
            self.pwr_flag(x, y)
            self.wire(x, y, x, y + STUB)
            self.power("GND", x, y + STUB)
        else:
            self.power(net, x, y)
            self.wire(x, y, x + 4 * STUB, y)
            self.pwr_flag(x + 4 * STUB, y)

    # ---- output ---------------------------------------------------------------------
    def write(self, path):
        tb = [Sym("title_block"), [Sym("title"), self.title]]
        if self.date:
            tb.append([Sym("date"), self.date])
        if self.rev:
            tb.append([Sym("rev"), self.rev])
        for i, c in enumerate(self.comments, 1):
            tb.append([Sym("comment"), i, c])
        doc = [Sym("kicad_sch"), [Sym("version"), 20250114], [Sym("generator"), "eeschema"],
               [Sym("generator_version"), "9.0"], [Sym("uuid"), self.root],
               [Sym("paper"), self.paper], tb,
               [Sym("lib_symbols")] + [self.lib_symbols[k] for k in sorted(self.lib_symbols)]]
        doc += self.items
        doc.append([Sym("sheet_instances"), [Sym("path"), "/", [Sym("page"), "1"]]])
        doc.append([Sym("embedded_fonts"), Sym("no")])
        Path(path).write_text(dump(doc) + "\n")
