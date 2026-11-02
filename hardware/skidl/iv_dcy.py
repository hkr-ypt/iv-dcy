#!/usr/bin/env python3
# SPDX-License-Identifier: CERN-OHL-S-2.0
# Copyright (c) 2026 Lucas Wu
"""
IV-DCY USB reference board -- circuit description (SKiDL).

This file is the single source of truth for the board's connectivity.
Running it writes, into ../kicad/:

    iv_dcy.net         KiCad netlist (read by ../layout/place_route.py)
    iv_dcy.kicad_sch   editable KiCad 9 schematic (drawn by kicad_sch.py)

Circuit summary
---------------
* J1  USB-C receptacle (USB 2.0 only).  Device role: CC1/CC2 each pulled
      down with 5.1 k (R1, R2) so a USB-C host supplies 5 V on VBUS.
* U3  USBLC6-2SC6 ESD protection on D+/D- (flow-through), referenced to VBUS.
* U2  MCP1700 3.3 V LDO, bus powered from VBUS.  C1 input, C2 output.
* U1  STM32F042K6T6 (Cortex-M0, crystal-less USB 2.0 full-speed device,
      internal D+ pull-up, USB DFU bootloader in system ROM).
      Decoupling: C3 (VDD), C4 (VDDIO2), C5 + C6 (VDDA).  C7 on NRST.
* SW1 BOOT button: drives PB8/BOOT0 high; R3 holds it low otherwise.
      Pressed while the board powers up -> ROM USB DFU bootloader.
      After reset PB8 is an ordinary input, so firmware may read the button.
* D1  status LED on PA4 (active high, R4 = 1 k).
* J2  ARM Cortex 10-pin (1.27 mm) SWD connector.

Every symbol and footprint comes from the official KiCad 9 libraries; no
project-specific library is needed.
"""

import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KICAD_DIR = HERE.parent / "kicad"
PROJECT = "iv_dcy"


def _default_kicad_dirs():
    """Point SKiDL at the installed KiCad 9 libraries unless already set."""
    candidates = [
        Path("/usr/share/kicad"),                                   # Linux packages
        Path("/usr/local/share/kicad"),
        Path("/Applications/KiCad/KiCad.app/Contents/SharedSupport"),  # macOS
        Path("C:/Program Files/KiCad/9.0/share/kicad"),             # Windows
    ]
    for base in candidates:
        if (base / "symbols").is_dir():
            # SKiDL looks up one variable per KiCad version; point them all at
            # the KiCad 9 libraries so it does not warn about the others.
            for ver in ("", "6", "7", "8", "9"):
                os.environ.setdefault(f"KICAD{ver}_SYMBOL_DIR", str(base / "symbols"))
                os.environ.setdefault(f"KICAD{ver}_FOOTPRINT_DIR", str(base / "footprints"))
            return
    if "KICAD9_SYMBOL_DIR" not in os.environ:
        sys.exit("KiCad 9 symbol libraries not found: set KICAD9_SYMBOL_DIR "
                 "(and KICAD9_FOOTPRINT_DIR) to your KiCad installation.")


_default_kicad_dirs()

from skidl import (  # noqa: E402  (import after the environment is set)
    ERC, KICAD9, POWER, Net, Part, generate_netlist, set_default_tool,
    subcircuit,
)
import builtins  # noqa: E402

NC = builtins.NC                # SKiDL's no-connect net (installed on import)

set_default_tool(KICAD9)

# ---------------------------------------------------------------------------
# Footprints (all from the stock KiCad 9 footprint libraries)
# ---------------------------------------------------------------------------
FP_0603_R = "Resistor_SMD:R_0603_1608Metric"
FP_0603_C = "Capacitor_SMD:C_0603_1608Metric"
FP_LED = "LED_SMD:LED_0603_1608Metric"
FP_USBC = "Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal"
FP_LQFP32 = "Package_QFP:LQFP-32_7x7mm_P0.8mm"
FP_SOT23 = "Package_TO_SOT_SMD:SOT-23"
FP_SOT23_6 = "Package_TO_SOT_SMD:SOT-23-6"
FP_BUTTON = "Button_Switch_SMD:SW_SPST_B3U-1000P"
FP_SWD = "Connector_PinHeader_1.27mm:PinHeader_2x05_P1.27mm_Vertical"


def part(lib, name, ref, value, footprint, mpn):
    """A part with a fixed tag (reproducible netlists) and an MPN field."""
    p = Part(lib, name, ref=ref, value=value, footprint=footprint, tag=ref)
    p.fields["MPN"] = mpn
    return p


def R(ref, value, mpn):
    return part("Device", "R", ref, value, FP_0603_R, mpn)


def C(ref, value, mpn):
    return part("Device", "C", ref, value, FP_0603_C, mpn)


@subcircuit
def usb_input(vbus, gnd, usb_dp, usb_dm):
    """USB-C receptacle, CC pull-downs and ESD protection."""
    cc1 = Net("CC1")
    cc2 = Net("CC2")
    j1 = part("Connector", "USB_C_Receptacle_USB2.0_16P", "J1", "USB_C_Receptacle",
             FP_USBC, "GCT USB4105-GF-A")
    vbus += j1["VBUS"]          # A4/A9/B4/B9
    gnd += j1["GND"]            # A1/A12/B1/B12
    gnd += j1["SHIELD"]         # shell tied straight to GND
    usb_dp += j1["D+"]          # A6 + B6 (both plug orientations)
    usb_dm += j1["D-"]          # A7 + B7
    cc1 += j1["CC1"]
    cc2 += j1["CC2"]
    j1["SBU1"] += NC
    j1["SBU2"] += NC

    # 5.1 k Rd on each CC line: identifies the board as a USB-C sink.
    r1 = R("R1", "5.1k", "0603 5.1k 1%")
    r2 = R("R2", "5.1k", "0603 5.1k 1%")
    cc1 += r1[1]
    cc2 += r2[1]
    gnd += r1[2], r2[2]

    # ESD array, flow-through: pins 1/6 and 3/4 are the same line inside.
    u3 = part("Power_Protection", "USBLC6-2SC6", "U3", "USBLC6-2SC6",
             FP_SOT23_6, "STMicroelectronics USBLC6-2SC6")
    usb_dp += u3[1], u3[6]
    usb_dm += u3[3], u3[4]
    vbus += u3["VBUS"]
    gnd += u3["GND"]


@subcircuit
def power(vbus, v33, gnd):
    """VBUS -> 3.3 V linear regulator."""
    u2 = part("Regulator_Linear", "MCP1700x-330xxTT", "U2", "MCP1700-3.3",
             FP_SOT23, "Microchip MCP1700T-3302E/TT")
    vbus += u2["VI"]
    v33 += u2["VO"]
    gnd += u2["GND"]
    c1 = C("C1", "1uF", "0603 1uF 16V X5R")
    c2 = C("C2", "4.7uF", "0603 4.7uF 10V X5R")
    vbus += c1[1]
    v33 += c2[1]
    gnd += c1[2], c2[2]


@subcircuit
def mcu(v33, gnd, usb_dp, usb_dm, swdio, swclk, nrst, boot0, led):
    """STM32F042K6T6 with its decoupling."""
    u1 = part("MCU_ST_STM32F0", "STM32F042K6Tx", "U1", "STM32F042K6T6",
             FP_LQFP32, "STMicroelectronics STM32F042K6T6")
    v33 += u1["VDD"], u1["VDDA"], u1["VDDIO2"]
    gnd += u1["VSS"], u1["VSSA"]
    usb_dm += u1["PA11"]
    usb_dp += u1["PA12"]
    swdio += u1["PA13"]
    swclk += u1["PA14"]
    nrst += u1["NRST"]
    boot0 += u1["PB8"]          # pin 31: BOOT0 at reset, PB8 afterwards
    led += u1["PA4"]

    c3 = C("C3", "100nF", "0603 100nF 16V X7R")     # VDD
    c4 = C("C4", "100nF", "0603 100nF 16V X7R")     # VDDIO2
    c5 = C("C5", "1uF", "0603 1uF 16V X5R")         # VDDA bulk
    c6 = C("C6", "10nF", "0603 10nF 50V X7R")       # VDDA HF
    c7 = C("C7", "100nF", "0603 100nF 16V X7R")     # NRST filter
    v33 += c3[1], c4[1], c5[1], c6[1]
    nrst += c7[1]
    gnd += c3[2], c4[2], c5[2], c6[2], c7[2]

    # Unused GPIOs: explicit no-connects.
    for pin in ("PF0", "PF1", "PA0", "PA1", "PA2", "PA3", "PA5", "PA6", "PA7",
                "PB0", "PB1", "PA8", "PA9", "PA10", "PA15", "PB3", "PB4",
                "PB5", "PB6", "PB7"):
        u1[pin] += NC


@subcircuit
def user_io(v33, gnd, boot0, led):
    """BOOT button and status LED."""
    sw1 = part("Switch", "SW_Push", "SW1", "BOOT",
             FP_BUTTON, "Omron B3U-1000P")
    boot0 += sw1[1]
    v33 += sw1[2]
    r3 = R("R3", "10k", "0603 10k 1%")
    boot0 += r3[1]
    gnd += r3[2]

    led_a = Net("LED_A")
    r4 = R("R4", "1k", "0603 1k 1%")
    d1 = part("Device", "LED", "D1", "green",
             FP_LED, "0603 green LED")
    led += r4[1]
    led_a += r4[2], d1["A"]
    gnd += d1["K"]


@subcircuit
def debug_port(v33, gnd, swdio, swclk, nrst):
    """ARM Cortex 10-pin SWD connector."""
    j2 = part("Connector", "Conn_ARM_JTAG_SWD_10", "J2", "SWD",
             FP_SWD, "Samtec FTSH-105-01-L-DV (or equivalent)")
    v33 += j2["VTref"]
    swdio += j2["SWDIO/TMS"]
    swclk += j2["SWCLK/TCK"]
    nrst += j2["~{RESET}"]
    gnd += j2[3], j2[5], j2["GNDDetect"]
    j2["SWO/TDO"] += NC         # Cortex-M0 has no SWO
    j2["NC/TDI"] += NC


def build():
    vbus = Net("VBUS")
    gnd = Net("GND")
    v33 = Net("+3V3")
    # VBUS comes from the USB host through J1 (passive pins) and GND is the
    # host's ground: neither has a driver on this board, so mark them as
    # power sources for ERC.
    vbus.drive = POWER
    gnd.drive = POWER
    usb_dp = Net("USB_DP")
    usb_dm = Net("USB_DM")
    swdio = Net("SWDIO")
    swclk = Net("SWCLK")
    nrst = Net("NRST")
    boot0 = Net("BOOT0")
    led = Net("LED")

    usb_input(vbus, gnd, usb_dp, usb_dm, tag="usb_input")
    power(vbus, v33, gnd, tag="power")
    mcu(v33, gnd, usb_dp, usb_dm, swdio, swclk, nrst, boot0, led, tag="mcu")
    user_io(v33, gnd, boot0, led, tag="user_io")
    debug_port(v33, gnd, swdio, swclk, nrst, tag="debug_port")


# ---------------------------------------------------------------------------
# Schematic drawing: where each symbol sits on the A4 sheet (mm).  Purely
# presentational -- connectivity comes from the circuit above.
# ---------------------------------------------------------------------------
SHEET_LAYOUT = {
    #  ref : (x, y, rotation, reference-text offset, value-text offset)
    "J1": (45.72, 68.58, 0, (-5.08, -20.32), (12.7, 27.94)),
    "R1": (83.82, 53.34, 0, (2.54, -1.27), (2.54, 1.27)),
    "R2": (96.52, 53.34, 0, (2.54, -1.27), (2.54, 1.27)),
    "U3": (91.44, 86.36, 0, (-5.08, -7.62), (5.08, 7.62)),
    "U2": (50.8, 142.24, 0, (0, -5.08), (8.89, 5.08)),
    "C1": (30.48, 147.32, 0, (3.81, -1.27), (3.81, 1.27)),
    "C2": (71.12, 147.32, 0, (3.81, -1.27), (3.81, 1.27)),
    "U1": (162.56, 83.82, 0, (-12.7, -30.48), (-12.7, 33.02)),
    "C3": (127.0, 142.24, 0, (3.81, -1.27), (3.81, 1.27)),
    "C4": (142.24, 142.24, 0, (3.81, -1.27), (3.81, 1.27)),
    "C5": (157.48, 142.24, 0, (3.81, -1.27), (3.81, 1.27)),
    "C6": (172.72, 142.24, 0, (3.81, -1.27), (3.81, 1.27)),
    "C7": (190.5, 142.24, 0, (3.81, -1.27), (3.81, 1.27)),
    "SW1": (236.22, 43.18, 0, (0, -3.81), (0, 3.81)),
    "R3": (254.0, 53.34, 0, (2.54, -1.27), (2.54, 1.27)),
    "R4": (231.14, 76.2, 90, (0, -2.54), (0, 2.54)),
    "D1": (256.54, 76.2, 180, (0, -3.81), (0, 3.81)),
    "J2": (243.84, 127.0, 0, (-7.62, -20.32), (-10.16, 17.78)),
}

SHEET_NOTES = [
    ("USB-C receptacle, CC pull-downs (USB-C sink), ESD protection", 20.32, 30.48),
    ("3.3 V supply (bus powered)", 20.32, 124.46),
    ("STM32F042K6T6: crystal-less USB full-speed device", 134.62, 30.48),
    ("Decoupling: C3 VDD, C4 VDDIO2, C5+C6 VDDA, C7 NRST", 119.38, 124.46),
    ("BOOT button (hold while plugging in: USB DFU bootloader)", 213.36, 30.48),
    ("Status LED (PA4, active high)", 213.36, 66.04),
    ("SWD: ARM Cortex 10-pin, 1.27 mm", 213.36, 99.06),
]


def circuit_parts():
    """The SKiDL circuit's parts as plain dicts for the schematic writer."""
    circuit = builtins.default_circuit
    parts = []
    for p in sorted(circuit.parts, key=lambda q: q.ref):
        pins = {}
        for pin in p.pins:
            net = pin.nets[0].name if pin.nets else None
            pins[pin.num] = None if net in (None, circuit.NC.name) else net
        parts.append(dict(ref=p.ref, lib=p.lib.filename, name=p.name, value=p.value,
                          footprint=p.footprint, fields={"MPN": p.fields.get("MPN", "")},
                          pins=pins))
    return parts


def write_schematic(path):
    from kicad_sch import Schematic
    sch = Schematic(PROJECT, "IV-DCY USB reference board",
                    os.environ["KICAD9_SYMBOL_DIR"], paper="A4", rev="1.0",
                    comments=("USB 2.0 full-speed CDC-ACM device, VID 0x1209",
                              "Hardware: CERN-OHL-S-2.0",
                              "Generated by hardware/skidl/iv_dcy.py"))
    for p in circuit_parts():
        x, y, rot, ref_at, val_at = SHEET_LAYOUT[p["ref"]]
        sch.part(p, x, y, rot, ref_at=ref_at, val_at=val_at)
    # VBUS and GND are supplied by the USB host: tell ERC so.
    sch.flagged_power("VBUS", 20.32, 40.64)
    sch.flagged_power("GND", 45.72, 40.64)
    for text, x, y in SHEET_NOTES:
        sch.text(text, x, y)
    sch.write(path)


def main():
    build()
    KICAD_DIR.mkdir(parents=True, exist_ok=True)
    ERC()
    net_path = KICAD_DIR / f"{PROJECT}.net"
    generate_netlist(file_=str(net_path), track_src=False)
    # Drop the generation time stamp so that rebuilding gives identical files.
    text = net_path.read_text()
    net_path.write_text(re.sub(r'\(date "[^"]*"\)', '(date "")', text, count=1))
    write_schematic(KICAD_DIR / f"{PROJECT}.kicad_sch")


if __name__ == "__main__":
    main()
