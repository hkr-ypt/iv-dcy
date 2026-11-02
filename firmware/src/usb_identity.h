/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lucas Wu
 *
 * USB identity of the IV-DCY device.
 *
 * This header is the ONLY place in the firmware where the vendor ID, product
 * ID, descriptor strings and firmware version are defined.  The USB
 * descriptors (usb_descriptors.c), the INFO/VERSION replies (cli.c) and the
 * host test tool (tools/iv_dcy_check.py, which parses this file) all take
 * their values from here.  tests/check_identity.cmake fails the test suite if
 * the VID or PID literal appears anywhere else under src/.
 */
#ifndef USB_IDENTITY_H
#define USB_IDENTITY_H

/* 0x1209 is the pid.codes vendor ID for open-source hardware projects. */
#define USB_VID 0x1209

/* Product ID requested from pid.codes for this project.  It is NOT assigned
 * until pid.codes accepts the request; until then, builds that leave your
 * desk should use the pid.codes test PID 0x0001 instead. */
#define USB_PID 0x6767

#define USB_MANUFACTURER_STRING  "IV-DCY project"
#define USB_PRODUCT_STRING       "IV-DCY USB reference"
#define USB_CDC_INTERFACE_STRING "IV-DCY CDC"

/* Firmware version: reported by VERSION/INFO and as bcdDevice (0xJJMN). */
#define FW_VERSION_MAJOR 0
#define FW_VERSION_MINOR 1
#define FW_VERSION_PATCH 0

/* ---- derived values (do not edit) ------------------------------------- */
#define USB_ID_STR_(x) #x
#define USB_ID_STR(x)  USB_ID_STR_(x)

#define FW_VERSION_STRING                                                     \
    USB_ID_STR(FW_VERSION_MAJOR) "." USB_ID_STR(FW_VERSION_MINOR) "."          \
    USB_ID_STR(FW_VERSION_PATCH)

#define USB_BCD_DEVICE                                                        \
    ((FW_VERSION_MAJOR << 8) | (FW_VERSION_MINOR << 4) | FW_VERSION_PATCH)

#define USB_VID_STRING USB_ID_STR(USB_VID)
#define USB_PID_STRING USB_ID_STR(USB_PID)

#endif /* USB_IDENTITY_H */
