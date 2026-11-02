/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lucas Wu
 */
#ifndef USB_DESCRIPTORS_H
#define USB_DESCRIPTORS_H

/* String descriptor indices. */
enum {
    STRID_LANGID = 0,
    STRID_MANUFACTURER,
    STRID_PRODUCT,
    STRID_SERIAL,
    STRID_CDC,
};

#define USB_SERIAL_LEN 24   /* 96-bit unique ID as upper-case hex */

/* The serial number string (also reported by the INFO command). */
const char *usb_serial_number(void);

#endif /* USB_DESCRIPTORS_H */
