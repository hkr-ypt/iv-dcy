#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lucas Wu
"""
Talk to an IV-DCY board over its USB CDC-ACM port and check the replies.

    pip install pyserial
    python3 firmware/tools/iv_dcy_check.py            # find the board by VID/PID
    python3 firmware/tools/iv_dcy_check.py --port /dev/ttyACM0
    python3 firmware/tools/iv_dcy_check.py --port COM5

The expected VID, PID and version are read from firmware/src/usb_identity.h,
so this tool never disagrees with the firmware it was shipped with.
Exit status 0 means every check passed.
"""
import argparse
import re
import sys
import time
from pathlib import Path

IDENTITY_H = Path(__file__).resolve().parent.parent / "src" / "usb_identity.h"


def read_identity(path=IDENTITY_H):
    text = path.read_text()

    def define(name):
        m = re.search(rf"^#define {name}\s+(\S+)", text, re.M)
        if not m:
            sys.exit(f"{name} not found in {path}")
        return m.group(1)

    return dict(
        vid=int(define("USB_VID"), 16),
        pid=int(define("USB_PID"), 16),
        version="{}.{}.{}".format(define("FW_VERSION_MAJOR"), define("FW_VERSION_MINOR"),
                                  define("FW_VERSION_PATCH")),
        product=define("USB_PRODUCT_STRING").strip('"'),
    )


def find_port(vid, pid):
    from serial.tools import list_ports
    ports = [p for p in list_ports.comports() if p.vid == vid and p.pid == pid]
    if not ports:
        sys.exit(f"no serial port with USB ID {vid:04x}:{pid:04x} found "
                 "(is the board plugged in and enumerated?)")
    if len(ports) > 1:
        print(f"note: {len(ports)} boards found, using {ports[0].device}")
    p = ports[0]
    print(f"found {p.device}: {vid:04x}:{pid:04x} serial={p.serial_number} "
          f"product={p.product!r} manufacturer={p.manufacturer!r}")
    return p.device


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--port", help="serial port (default: search by VID/PID)")
    ap.add_argument("--timeout", type=float, default=1.0, help="reply timeout in s")
    args = ap.parse_args()

    import serial  # pyserial

    ident = read_identity()
    port = args.port or find_port(ident["vid"], ident["pid"])
    ser = serial.Serial(port, 115200, timeout=args.timeout)
    time.sleep(0.1)
    ser.reset_input_buffer()

    def ask(cmd):
        ser.write((cmd + "\r\n").encode())
        reply = ser.readline().decode(errors="replace").rstrip("\r\n")
        print(f"> {cmd}\n< {reply}")
        return reply

    failures = 0

    def check(ok, what):
        nonlocal failures
        print(("  ok   " if ok else "  FAIL ") + what)
        failures += not ok

    check(ask("PING") == "PONG", "PING answered PONG")
    check(ask("VERSION") == ident["version"], f"VERSION is {ident['version']}")
    info = ask("INFO")
    check(info.startswith(ident["product"]), "INFO names the product")
    check(f"vid=0x{ident['vid']:04x}" in info.lower() and f"pid=0x{ident['pid']:04x}" in info.lower(),
          "INFO reports the VID/PID from usb_identity.h")
    check(re.search(r"serial=[0-9A-F]{24}$", info) is not None, "INFO reports a 24-digit serial")
    check(ask("BUTTON") in ("PRESSED", "RELEASED"), "BUTTON answered")
    check(ask("BOGUS").startswith("ERR "), "unknown command rejected")
    ser.close()
    print("all checks passed" if failures == 0 else f"{failures} check(s) failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
