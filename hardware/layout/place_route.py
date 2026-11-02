#!/usr/bin/env python3
# SPDX-License-Identifier: CERN-OHL-S-2.0
# Copyright (c) 2026 Lucas Wu
"""
IV-DCY USB reference board -- PCB placement and routing.

Builds ../kicad/iv_dcy.kicad_pcb from scratch with KiCad's pcbnew Python
module:

  1. reads the netlist written by ../skidl/iv_dcy.py,
  2. loads every footprint from the stock KiCad 9 footprint libraries,
  3. places them (PLACEMENT), draws the tracks and vias (TRACKS, VIAS),
  4. adds the board outline, GND pours on both layers and silkscreen text,
  5. fills the zones and saves the board and its project file.

Everything is explicit, so the output is the same on every run.  The board
is a 2-layer, 1.6 mm FR-4 design, 28 x 36 mm; coordinates below are in mm
from the board's top-left corner (x right, y down).

Run with a Python that can import pcbnew (KiCad 9), e.g. on Linux:
    /usr/bin/python3 place_route.py
"""

import json
import os
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent
KICAD_DIR = HERE.parent / "kicad"
sys.path.insert(0, str(HERE.parent / "skidl"))
from sexpr import find, find_all, parse  # noqa: E402

PROJECT = "iv_dcy"
ORIGIN = (100.0, 100.0)          # where the board's top-left corner sits on the page
W, H = 28.0, 36.0                # board size

# Net classes (also written to the project file for DRC).
SIGNAL_W = 0.2
POWER_W = 0.4
VIA_D, VIA_DRILL = 0.6, 0.3
CLEARANCE = 0.2
POWER_NETS = ("VBUS", "+3V3")
# Nets drawn with power symbols keep their name; nets named by a local label
# are "/NAME" in KiCad, so the board uses the same names as the schematic.
GLOBAL_NETS = ("GND", "VBUS", "+3V3")

# Board-wide DRC limits (mm): conservative values most PCB fabs accept.
RULES = {
    "min_clearance": 0.15,
    "min_copper_edge_clearance": 0.3,
    "min_hole_clearance": 0.25,
    "min_hole_to_hole": 0.25,
    "min_through_hole_diameter": 0.3,
    "min_track_width": 0.15,
    "min_via_annular_width": 0.1,
    "min_via_diameter": 0.5,
    "min_silk_clearance": 0.0,
    "min_text_height": 0.6,
    "min_text_thickness": 0.1,
    "solder_mask_to_copper_clearance": 0.0,
}


def fp_dir():
    for env in ("KICAD9_FOOTPRINT_DIR", "KICAD_FOOTPRINT_DIR"):
        if os.environ.get(env):
            return Path(os.environ[env])
    for base in ("/usr/share/kicad/footprints", "/usr/local/share/kicad/footprints",
                 "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints",
                 "C:/Program Files/KiCad/9.0/share/kicad/footprints"):
        if Path(base).is_dir():
            return Path(base)
    sys.exit("KiCad 9 footprint libraries not found: set KICAD9_FOOTPRINT_DIR")


# ---------------------------------------------------------------------------
# Placement: ref -> (x, y, rotation in degrees, reference-text offset or None)
# ---------------------------------------------------------------------------
PLACEMENT = {
    # USB-C receptacle centred on the bottom edge; its "PCB Edge" mark is 3.675
    # mm in front of the footprint origin.
    "J1": (14.0, H - 3.675, 0, (-6.5, 0.6)),
    "R1": (12.7, 25.4, 90, (-1.6, 0.0)),
    "R2": (16.3, 25.4, 90, (1.5, 0.0)),
    "U3": (14.5, 21.5, -90, (2.9, 0.0)),
    # MCU: rotated so that PA11/PA12 (USB) and PA13/PA14 (SWD) face down.
    "U1": (14.0, 12.5, -90, (0.0, 0.0)),
    "C6": (11.75, 5.7, 90, (0.0, -2.2)),
    "C5": (13.35, 5.7, 90, (0.0, -2.2)),
    "C3": (16.8, 5.7, 90, (0.0, -2.2)),
    "C4": (11.2, 19.4, -90, (-1.5, 0.0)),
    # BOOT button and pull-down, NRST capacitor, SWD header on the right.
    "SW1": (22.6, 3.4, 0, (2.0, -2.55)),
    "R3": (22.0, 6.4, 0, (3.0, 0.0)),
    "C7": (21.13, 11.1, 90, (1.5, 0.0)),
    "J2": (22.4, 18.97, 180, (-0.6, 2.2)),
    # Status LED on the left.
    "R4": (7.2, 10.5, 180, (0.0, 1.4)),
    "D1": (4.1, 10.5, 0, (0.0, 1.4)),
    # 3.3 V regulator, bottom left.
    "U2": (5.6, 27.0, 0, (0.0, 2.5)),
    "C1": (8.4, 25.6, 90, (-1.4, -1.2)),
    "C2": (2.6, 29.5, 0, (0.0, 1.4)),
}

# ---------------------------------------------------------------------------
# Routing.  A point is (x, y) or (ref, pad) for a pad centre.
# ---------------------------------------------------------------------------
F, B = "F.Cu", "B.Cu"

TRACKS = [
    # ---- USB D+/D- -------------------------------------------------------
    # D+ pads A6 and B6 joined in front of the pad row (under the receptacle
    # body), D- pads B7 and A7 joined behind it; both leave on top copper.
    ("USB_DP", F, SIGNAL_W, [(13.75, 28.645), (13.75, 29.575), (14.75, 29.575), (14.75, 28.645)]),
    ("USB_DM", F, SIGNAL_W, [(13.25, 28.645), (13.25, 27.625), (14.25, 27.625)]),
    ("USB_DM", F, SIGNAL_W, [(14.25, 28.645), (14.25, 25.1), (13.55, 24.4), ("U3", "4")]),
    ("USB_DP", F, SIGNAL_W, [(14.75, 28.645), (14.75, 25.1), (15.45, 24.4), ("U3", "6")]),
    ("USB_DM", F, SIGNAL_W, [("U3", "4"), ("U3", "3")]),
    ("USB_DP", F, SIGNAL_W, [("U3", "6"), ("U3", "1")]),
    ("USB_DM", F, SIGNAL_W, [("U3", "3"), (13.55, 18.5), (14.4, 17.65), ("U1", "21")]),
    ("USB_DP", F, SIGNAL_W, [("U3", "1"), (15.45, 18.5), (15.2, 18.25), ("U1", "22")]),
    # ---- CC pull-downs ----------------------------------------------------
    ("CC1", F, SIGNAL_W, [(12.7, 28.645), ("R1", "1")]),
    ("CC2", F, SIGNAL_W, [(15.75, 28.645), (15.75, 27.0), (16.3, 26.45), ("R2", "1")]),
    # ---- VBUS ----------------------------------------------------------------
    ("VBUS", F, POWER_W, [(11.6, 28.645), (11.6, 27.6)]),
    ("VBUS", F, POWER_W, [(16.4, 28.645), (16.4, 27.6)]),
    ("VBUS", B, POWER_W, [(11.6, 27.6), (16.4, 27.6)]),
    ("VBUS", B, POWER_W, [(14.5, 23.8), (14.5, 27.6)]),
    ("VBUS", F, SIGNAL_W, [("U3", "5"), (14.5, 23.8)]),
    ("VBUS", F, POWER_W, [(11.6, 27.6), (9.0, 27.6), (8.4, 27.0), ("U2", "3")]),
    ("VBUS", F, POWER_W, [("C1", "1"), (8.4, 27.0)]),
    # ---- 3.3 V -----------------------------------------------------------------
    ("+3V3", F, POWER_W, [("U2", "2"), (1.6, 27.95)]),
    ("+3V3", F, POWER_W, [("C2", "1"), (1.6, 29.5), (1.6, 6.3), (11.75, 6.3)]),
    ("+3V3", F, POWER_W, [(1.6, 18.575), ("C4", "1")]),
    ("+3V3", F, SIGNAL_W, [("C4", "1"), ("U1", "17")]),
    ("+3V3", F, POWER_W, [(11.75, 6.3), (16.8, 6.3), (19.0, 6.3), (19.0, 1.2), (26.4, 1.2),
                          (26.4, 18.97), ("J2", "1")]),
    ("+3V3", F, SIGNAL_W, [("C6", "1"), (11.75, 6.3)]),
    ("+3V3", F, SIGNAL_W, [("C5", "1"), (13.35, 6.3)]),
    ("+3V3", F, SIGNAL_W, [(13.6, 6.525), ("U1", "5")]),
    ("+3V3", F, SIGNAL_W, [("C3", "1"), ("U1", "1")]),
    ("+3V3", F, POWER_W, [(26.4, 3.4), ("SW1", "2")]),
    # ---- NRST: pin 4 -> via -> bottom -> J2 pin 10 -> C7 ----------------------
    ("NRST", F, SIGNAL_W, [("U1", "4"), (14.4, 7.1)]),
    ("NRST", B, SIGNAL_W, [(14.4, 7.1), (14.4, 7.9), (20.0, 13.5), (20.39, 13.89), ("J2", "10")]),
    ("NRST", F, SIGNAL_W, [("J2", "10"), ("C7", "1")]),
    # ---- SWD -------------------------------------------------------------------
    ("SWDIO", F, SIGNAL_W, [("U1", "23"), (16.0, 18.97), ("J2", "2")]),
    ("SWCLK", F, SIGNAL_W, [("U1", "24"), (16.8, 17.7), ("J2", "4")]),
    # ---- BOOT0 -----------------------------------------------------------------
    ("BOOT0", F, SIGNAL_W, [("U1", "31"), (20.0, 10.5), (20.0, 6.4), ("R3", "1")]),
    ("BOOT0", F, SIGNAL_W, [("R3", "1"), (21.175, 4.0)]),
    # ---- LED ---------------------------------------------------------------------
    ("LED", F, SIGNAL_W, [("U1", "10"), ("R4", "1")]),
    ("LED_A", F, SIGNAL_W, [("R4", "2"), ("D1", "2")]),
    # ---- GND: short stubs to stitching vias (both layers are GND pours) ---------
    ("GND", F, POWER_W, [(10.8, 28.645), (9.68, 28.645)]),
    ("GND", F, POWER_W, [(17.2, 28.645), (18.32, 28.645)]),
    ("GND", F, SIGNAL_W, [("R1", "2"), (12.7, 23.5)]),
    ("GND", F, SIGNAL_W, [("R2", "2"), (16.3, 23.5)]),
    ("GND", F, SIGNAL_W, [("U3", "2"), (14.5, 19.2)]),
    ("GND", F, SIGNAL_W, [("C6", "2"), ("C5", "2")]),
    ("GND", F, SIGNAL_W, [("C5", "2"), (12.55, 3.9)]),
    ("GND", F, SIGNAL_W, [("C3", "2"), (16.8, 3.9)]),
    ("GND", F, SIGNAL_W, [("C4", "2"), (11.2, 21.2)]),
    ("GND", F, SIGNAL_W, [("C7", "2"), (22.2, 10.275)]),
    ("GND", F, SIGNAL_W, [("R3", "2"), (23.8, 6.4)]),
    ("GND", F, SIGNAL_W, [("D1", "1"), (3.3, 9.3)]),
    ("GND", F, SIGNAL_W, [("U1", "16"), (8.6, 15.3)]),
    ("GND", F, SIGNAL_W, [("U1", "32"), (19.35, 9.7)]),
    ("GND", F, SIGNAL_W, [("U2", "1"), (5.06, 24.9)]),
    ("GND", F, SIGNAL_W, [("C1", "2"), (8.4, 23.8)]),
    ("GND", F, SIGNAL_W, [("C2", "2"), (3.425, 30.7)]),
]

VIAS = [
    ("VBUS", 11.6, 27.6), ("VBUS", 16.4, 27.6), ("VBUS", 14.5, 23.8),
    ("NRST", 14.4, 7.1),
    ("GND", 12.7, 23.5), ("GND", 16.3, 23.5), ("GND", 14.5, 19.2),
    ("GND", 12.55, 3.9), ("GND", 16.8, 3.9), ("GND", 11.2, 21.2),
    ("GND", 22.2, 10.275), ("GND", 23.8, 6.4), ("GND", 3.3, 9.3),
    ("GND", 8.6, 15.3), ("GND", 19.35, 9.7), ("GND", 5.06, 24.9),
    ("GND", 8.4, 23.8), ("GND", 3.425, 30.7),
    # extra stitching between the two GND pours
    ("GND", 1.2, 1.2), ("GND", 26.8, 34.8), ("GND", 1.2, 34.8),
    ("GND", 24.5, 23.5), ("GND", 20.5, 30.5), ("GND", 7.0, 31.0),
    ("GND", 7.5, 21.0), ("GND", 7.0, 3.0),
]

SILK_TEXT = [
    # text, x, y, size, layer
    ("IV-DCY", 22.6, 25.5, 1.2, "F.SilkS"),
    ("USB ref. r1.0", 22.6, 27.4, 0.8, "F.SilkS"),
    ("BOOT", 20.9, 0.85, 0.7, "F.SilkS"),
    ("SWD", 25.0, 21.2, 0.7, "F.SilkS"),
    ("IV-DCY USB reference r1.0", 11.0, 11.5, 1.0, "B.SilkS"),
    ("CERN-OHL-S-2.0", 11.0, 13.3, 0.8, "B.SilkS"),
    # CERN-OHL-S-2.0 section 4.1: products carry the Source Location.
    ("github.com/hkr-ypt/iv-dcy", 10.5, 15.1, 0.8, "B.SilkS"),
]


# ---------------------------------------------------------------------------
def mm(x, y):
    return pcbnew.VECTOR2I_MM(ORIGIN[0] + x, ORIGIN[1] + y)


def load_netlist(path):
    root = parse(Path(path).read_text())
    comps = {}
    for c in find_all(find(root, "components"), "comp"):
        fields = {find(f, "name")[1]: f[2] for f in find_all(find(c, "fields") or [], "field")
                  if len(f) > 2}
        comps[find(c, "ref")[1]] = dict(value=find(c, "value")[1],
                                        footprint=find(c, "footprint")[1], fields=fields)
    nets = {}
    for n in find_all(find(root, "nets"), "net"):
        name = find(n, "name")[1]
        for node in find_all(n, "node"):
            nets[(find(node, "ref")[1], find(node, "pin")[1])] = name
    return comps, nets


def schematic_symbols(sch_path):
    """ref -> (symbol UUID, {pin number: pin name}) from the schematic.

    The UUID links each footprint to its symbol; the pin names give KiCad's
    names for the single-pin nets of unconnected pins.
    """
    from kicad_sch import SymbolLibrary
    root = parse(Path(sch_path).read_text())
    lib_pins = {s[1]: {num: name for num, name, *_ in SymbolLibrary.pins(s)}
                for s in find_all(find(root, "lib_symbols"), "symbol")}
    out = {}
    for s in find_all(root, "symbol"):
        ref = [p[2] for p in find_all(s, "property") if p[1] == "Reference"]
        if ref and not ref[0].startswith("#"):
            out[ref[0]] = (find(s, "uuid")[1], lib_pins[find(s, "lib_id")[1]])
    return out


def unconnected_net_name(ref, pin_name, pad):
    """The net name KiCad gives an unconnected symbol pin."""
    name = pin_name.replace("/", "{slash}")
    if name in ("", "~"):
        return f"unconnected-({ref}-Pad{pad})"
    return f"unconnected-({ref}-{name}-Pad{pad})"


def main():
    comps, pad_nets = load_netlist(KICAD_DIR / f"{PROJECT}.net")
    symbols = schematic_symbols(KICAD_DIR / f"{PROJECT}.kicad_sch")
    missing = set(comps) ^ set(PLACEMENT)
    if missing:
        sys.exit(f"placement and netlist disagree on: {sorted(missing)}")

    pcb_path = KICAD_DIR / f"{PROJECT}.kicad_pcb"
    pro_path = KICAD_DIR / f"{PROJECT}.kicad_pro"
    # Always start from nothing, so the output never depends on a previous run.
    for old in (pcb_path, pro_path, KICAD_DIR / f"{PROJECT}.kicad_prl"):
        old.unlink(missing_ok=True)
    # pcbnew orders items by UUID when saving: a fixed seed makes the UUIDs,
    # and so the file, identical on every run.
    pcbnew.KIID.SeedGenerator(0x1D0C)
    board = pcbnew.NewBoard(str(pcb_path))
    board.SetCopperLayerCount(2)

    nets = {}

    def net(name):
        if name not in GLOBAL_NETS and not name.startswith(("/", "unconnected-")):
            name = "/" + name
        if name not in nets:
            n = pcbnew.NETINFO_ITEM(board, name)
            board.Add(n)
            nets[name] = n
        return nets[name]

    for name in sorted(set(pad_nets.values())):
        net(name)

    # ---- footprints ----------------------------------------------------------
    fps = {}
    lib_root = fp_dir()
    for ref in sorted(comps):
        c = comps[ref]
        lib, name = c["footprint"].split(":")
        fp = pcbnew.FootprintLoad(str(lib_root / f"{lib}.pretty"), name)
        if fp is None:
            sys.exit(f"footprint {c['footprint']} not found")
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
        fp.SetReference(ref)
        fp.SetValue(c["value"])
        if c["fields"].get("MPN"):
            fp.SetField("MPN", c["fields"]["MPN"])
            mpn = fp.GetFieldByName("MPN")
            mpn.SetVisible(False)
            mpn.SetLayer(pcbnew.F_Fab)
        x, y, rot, ref_off = PLACEMENT[ref]
        fp.SetPosition(mm(x, y))
        fp.SetOrientationDegrees(rot)
        sym_uuid, pin_names = symbols[ref]
        fp.SetPath(pcbnew.KIID_PATH("/" + sym_uuid))
        ref_text = fp.Reference()
        ref_text.SetTextSize(pcbnew.VECTOR2I_MM(0.7, 0.7))
        ref_text.SetTextThickness(pcbnew.FromMM(0.12))
        ref_text.SetTextAngleDegrees(0)
        ref_text.SetKeepUpright(True)
        ref_text.SetPosition(mm(x + ref_off[0], y + ref_off[1]))
        fp.Value().SetVisible(False)
        if ref == "J1":
            # Connector ground and shell: solid connection to the GND pours
            # (lowest impedance for cable-shield and ESD currents).
            fp.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
        for pad in fp.Pads():
            num = pad.GetNumber()
            n = pad_nets.get((ref, num))
            if n:
                pad.SetNet(net(n))
            elif num in pin_names:
                pad.SetNet(net(unconnected_net_name(ref, pin_names[num], num)))
        board.Add(fp)
        fps[ref] = fp

    def point(p):
        if isinstance(p[0], str):
            ref, num = p
            for pad in fps[ref].Pads():
                if pad.GetNumber() == num:
                    return pad.GetPosition()
            sys.exit(f"no pad {ref}.{num}")
        return mm(*p)

    layer_id = {F: pcbnew.F_Cu, B: pcbnew.B_Cu}
    for name, layer, width, pts in TRACKS:
        pts = [point(p) for p in pts]
        for a, b in zip(pts, pts[1:]):
            if a == b:
                continue
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(a)
            t.SetEnd(b)
            t.SetWidth(pcbnew.FromMM(width))
            t.SetLayer(layer_id[layer])
            t.SetNet(net(name))
            board.Add(t)

    for name, x, y in VIAS:
        v = pcbnew.PCB_VIA(board)
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetPosition(mm(x, y))
        v.SetWidth(pcbnew.FromMM(VIA_D))
        v.SetDrill(pcbnew.FromMM(VIA_DRILL))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNet(net(name))
        board.Add(v)

    # ---- outline -------------------------------------------------------------
    edge = pcbnew.PCB_SHAPE(board)
    edge.SetShape(pcbnew.SHAPE_T_RECT)
    edge.SetStart(mm(0, 0))
    edge.SetEnd(mm(W, H))
    edge.SetLayer(pcbnew.Edge_Cuts)
    edge.SetWidth(pcbnew.FromMM(0.1))
    board.Add(edge)

    # ---- GND pours on both layers --------------------------------------------
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNet(net("GND"))
        z.SetZoneName(f"GND_{'F' if layer == pcbnew.F_Cu else 'B'}")
        z.SetLocalClearance(pcbnew.FromMM(0.25))
        z.SetMinThickness(pcbnew.FromMM(0.2))
        z.SetThermalReliefGap(pcbnew.FromMM(0.25))
        z.SetThermalReliefSpokeWidth(pcbnew.FromMM(0.3))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        outline = z.Outline()
        outline.NewOutline()
        for x, y in ((0.3, 0.3), (W - 0.3, 0.3), (W - 0.3, H - 0.3), (0.3, H - 0.3)):
            outline.Append(mm(x, y))
        board.Add(z)

    # ---- silkscreen text -------------------------------------------------------
    for text, x, y, size, layer in SILK_TEXT:
        t = pcbnew.PCB_TEXT(board)
        t.SetText(text)
        t.SetPosition(mm(x, y))
        t.SetTextSize(pcbnew.VECTOR2I_MM(size, size))
        t.SetTextThickness(pcbnew.FromMM(0.15 if size >= 1.0 else 0.12))
        t.SetLayer(pcbnew.F_SilkS if layer == "F.SilkS" else pcbnew.B_SilkS)
        if layer.startswith("B."):
            t.SetMirrored(True)
        board.Add(t)

    # ---- design rules (also stored in the project file) -------------------------
    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(2)
    ds.SetBoardThickness(pcbnew.FromMM(1.6))
    ds.m_MinClearance = pcbnew.FromMM(RULES["min_clearance"])
    ds.m_CopperEdgeClearance = pcbnew.FromMM(RULES["min_copper_edge_clearance"])
    ds.m_HoleClearance = pcbnew.FromMM(RULES["min_hole_clearance"])
    ds.m_HoleToHoleMin = pcbnew.FromMM(RULES["min_hole_to_hole"])
    ds.m_MinThroughDrill = pcbnew.FromMM(RULES["min_through_hole_diameter"])
    ds.m_TrackMinWidth = pcbnew.FromMM(RULES["min_track_width"])
    ds.m_ViasMinAnnularWidth = pcbnew.FromMM(RULES["min_via_annular_width"])
    ds.m_ViasMinSize = pcbnew.FromMM(RULES["min_via_diameter"])
    ds.m_MinSilkTextHeight = pcbnew.FromMM(RULES["min_text_height"])
    ds.m_MinSilkTextThickness = pcbnew.FromMM(RULES["min_text_thickness"])
    ds.m_SilkClearance = pcbnew.FromMM(RULES["min_silk_clearance"])
    ds.m_SolderMaskToCopperClearance = pcbnew.FromMM(RULES["solder_mask_to_copper_clearance"])
    default_nc = ds.m_NetSettings.GetDefaultNetclass()
    default_nc.SetClearance(pcbnew.FromMM(CLEARANCE))
    default_nc.SetTrackWidth(pcbnew.FromMM(SIGNAL_W))
    default_nc.SetViaDiameter(pcbnew.FromMM(VIA_D))
    default_nc.SetViaDrill(pcbnew.FromMM(VIA_DRILL))

    pcbnew.SaveBoard(str(pcb_path), board)
    make_uuids_deterministic(pcb_path)
    # Reload, so that the zone filler sees the project's design rules (hole
    # clearance and so on) and items are ordered by their now-fixed UUIDs,
    # then fill the zones and save the final board.
    board = pcbnew.LoadBoard(str(pcb_path))
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(pcb_path), board)
    make_uuids_deterministic(pcb_path)
    # pcbnew writes the project file from its in-memory settings on every
    # save; add the net classes and DRC limits last.
    write_project(pro_path)
    (KICAD_DIR / f"{PROJECT}.kicad_prl").unlink(missing_ok=True)
    print(f"wrote {pcb_path}")


def make_uuids_deterministic(path):
    """pcbnew assigns random UUIDs; renumber them so rebuilds are identical."""
    import re
    import uuid
    ns = uuid.UUID("2b0c6a51-0f7e-4f3d-8d6c-1e8f0a6b9c42")
    count = iter(range(1 << 30))
    text = re.sub(r'\(uuid "[0-9a-f-]+"\)',
                  lambda m: '(uuid "%s")' % uuid.uuid5(ns, str(next(count))),
                  path.read_text())
    path.write_text(text)


def write_project(path):
    """Project file: net classes and DRC limits used by KiCad's DRC."""
    pro = json.loads(path.read_text()) if path.exists() else {}
    pro.setdefault("meta", {"filename": path.name, "version": 3})
    bds = pro.setdefault("board", {}).setdefault("design_settings", {})
    bds["rules"] = dict(RULES)
    ns = pro.setdefault("net_settings", {})
    common = {"bus_width": 12, "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25,
              "diff_pair_width": 0.2, "line_style": 0, "microvia_diameter": 0.3,
              "microvia_drill": 0.1, "pcb_color": "rgba(0, 0, 0, 0.000)",
              "priority": 2147483647, "schematic_color": "rgba(0, 0, 0, 0.000)",
              "wire_width": 6, "clearance": CLEARANCE, "via_diameter": VIA_D,
              "via_drill": VIA_DRILL}
    ns["classes"] = [
        dict(common, name="Default", track_width=SIGNAL_W),
        dict(common, name="Power", track_width=POWER_W, priority=0),
    ]
    ns["meta"] = {"version": 4}
    ns["netclass_patterns"] = [{"netclass": "Power", "pattern": n} for n in POWER_NETS]
    path.write_text(json.dumps(pro, indent=2) + "\n")


if __name__ == "__main__":
    main()
