/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lucas Wu
 *
 * USB descriptors: one configuration with a single CDC-ACM function
 * (communication interface + data interface, grouped by an interface
 * association descriptor).  Full speed, bus powered.
 *
 * All identity values (VID, PID, strings, version) come from usb_identity.h.
 * The serial number string is the MCU's 96-bit unique ID in hexadecimal.
 */
#include "tusb.h"

#include "board.h"
#include "usb_descriptors.h"
#include "usb_identity.h"

enum { ITF_NUM_CDC = 0, ITF_NUM_CDC_DATA, ITF_NUM_TOTAL };

#define EP_CDC_NOTIF 0x81
#define EP_CDC_OUT   0x02
#define EP_CDC_IN    0x82

static const tusb_desc_device_t device_descriptor = {
    .bLength            = sizeof(tusb_desc_device_t),
    .bDescriptorType    = TUSB_DESC_DEVICE,
    .bcdUSB             = 0x0200,
    /* Miscellaneous / common class / IAD: required for a composite-style
     * CDC function so that hosts bind the right driver. */
    .bDeviceClass       = TUSB_CLASS_MISC,
    .bDeviceSubClass    = MISC_SUBCLASS_COMMON,
    .bDeviceProtocol    = MISC_PROTOCOL_IAD,
    .bMaxPacketSize0    = CFG_TUD_ENDPOINT0_SIZE,
    .idVendor           = USB_VID,
    .idProduct          = USB_PID,
    .bcdDevice          = USB_BCD_DEVICE,
    .iManufacturer      = STRID_MANUFACTURER,
    .iProduct           = STRID_PRODUCT,
    .iSerialNumber      = STRID_SERIAL,
    .bNumConfigurations = 1,
};

const uint8_t *tud_descriptor_device_cb(void)
{
    return (const uint8_t *)&device_descriptor;
}

#define CONFIG_TOTAL_LEN (TUD_CONFIG_DESC_LEN + TUD_CDC_DESC_LEN)

static const uint8_t configuration_descriptor[] = {
    /* config number, interface count, string index, total length,
     * attributes (bus powered), max power in mA */
    TUD_CONFIG_DESCRIPTOR(1, ITF_NUM_TOTAL, 0, CONFIG_TOTAL_LEN, 0x00, 100),
    /* interface number, string index, notification EP and size,
     * data OUT EP, data IN EP, data EP size */
    TUD_CDC_DESCRIPTOR(ITF_NUM_CDC, STRID_CDC, EP_CDC_NOTIF, 8,
                       EP_CDC_OUT, EP_CDC_IN, 64),
};

TU_VERIFY_STATIC(sizeof(configuration_descriptor) == CONFIG_TOTAL_LEN,
                 "configuration descriptor length");

const uint8_t *tud_descriptor_configuration_cb(uint8_t index)
{
    (void)index;   /* only one configuration */
    return configuration_descriptor;
}

const char *usb_serial_number(void)
{
    static char serial[USB_SERIAL_LEN + 1];
    if (serial[0] == '\0') {
        static const char hex[] = "0123456789ABCDEF";
        uint32_t uid[3];
        board_uid(uid);
        for (unsigned w = 0; w < 3u; w++) {
            for (unsigned n = 0; n < 8u; n++) {
                serial[w * 8u + n] = hex[(uid[w] >> (28u - 4u * n)) & 0xFu];
            }
        }
        serial[USB_SERIAL_LEN] = '\0';
    }
    return serial;
}

static const char *string_for(uint8_t index)
{
    switch (index) {
    case STRID_MANUFACTURER: return USB_MANUFACTURER_STRING;
    case STRID_PRODUCT:      return USB_PRODUCT_STRING;
    case STRID_SERIAL:       return usb_serial_number();
    case STRID_CDC:          return USB_CDC_INTERFACE_STRING;
    default:                 return NULL;
    }
}

#define MAX_STRING_CHARS 31u
static uint16_t string_descriptor[MAX_STRING_CHARS + 1u];

const uint16_t *tud_descriptor_string_cb(uint8_t index, uint16_t langid)
{
    (void)langid;
    size_t count;
    if (index == STRID_LANGID) {
        string_descriptor[1] = 0x0409;   /* English (United States) */
        count = 1;
    } else {
        const char *s = string_for(index);
        if (s == NULL) {
            return NULL;
        }
        count = strlen(s);
        if (count > MAX_STRING_CHARS) {
            count = MAX_STRING_CHARS;
        }
        for (size_t i = 0; i < count; i++) {
            string_descriptor[1u + i] = (uint8_t)s[i];   /* ASCII -> UTF-16LE */
        }
    }
    string_descriptor[0] = (uint16_t)((TUSB_DESC_STRING << 8) | (2u * count + 2u));
    return string_descriptor;
}
