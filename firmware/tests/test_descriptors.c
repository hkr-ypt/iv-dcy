/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lucas Wu
 *
 * Builds src/usb_descriptors.c on the host and checks the descriptors it
 * returns: identity values, lengths, the interface/endpoint structure and
 * the string table.
 */
#include "board.h"
#include "tusb.h"
#include "test.h"
#include "usb_descriptors.h"
#include "usb_identity.h"

/* Board stub: a fixed unique ID. */
void board_uid(uint32_t uid[3])
{
    uid[0] = 0x00380027u;
    uid[1] = 0x3536510Bu;
    uid[2] = 0x20313748u;
}

static void string_eq(uint8_t index, const char *expected)
{
    const uint16_t *d = tud_descriptor_string_cb(index, 0x0409);
    CHECK(d != NULL);
    if (d == NULL) {
        return;
    }
    size_t n = strlen(expected);
    CHECK((d[0] >> 8) == TUSB_DESC_STRING);
    CHECK((d[0] & 0xFF) == 2 * n + 2);
    char got[64] = { 0 };
    for (size_t i = 0; i < n && i < sizeof got - 1; i++) {
        got[i] = (char)d[1 + i];
    }
    CHECK_STR(got, expected);
}

int main(void)
{
    /* ---- device descriptor ---------------------------------------------- */
    const tusb_desc_device_t *dev = (const tusb_desc_device_t *)tud_descriptor_device_cb();
    CHECK(dev->bLength == 18);
    CHECK(dev->bDescriptorType == TUSB_DESC_DEVICE);
    CHECK(dev->bcdUSB == 0x0200);
    CHECK(dev->idVendor == 0x1209);
    CHECK(dev->idVendor == USB_VID);
    CHECK(dev->idProduct == USB_PID);
    /* bcdDevice 0xJJMN, cross-checked against the version string. */
    unsigned major, minor, patch;
    CHECK(sscanf(FW_VERSION_STRING, "%u.%u.%u", &major, &minor, &patch) == 3);
    CHECK(minor <= 9 && patch <= 9);
    CHECK(dev->bcdDevice == ((major << 8) | (minor << 4) | patch));
    CHECK(dev->bMaxPacketSize0 == 64);
    CHECK(dev->bDeviceClass == 0xEF && dev->bDeviceSubClass == 0x02 &&
          dev->bDeviceProtocol == 0x01);          /* IAD */
    CHECK(dev->bNumConfigurations == 1);

    /* ---- configuration descriptor: walk every descriptor ----------------- */
    const uint8_t *cfg = tud_descriptor_configuration_cb(0);
    uint16_t total = (uint16_t)(cfg[2] | (cfg[3] << 8));
    CHECK(cfg[0] == 9 && cfg[1] == TUSB_DESC_CONFIGURATION);
    CHECK(total == 75);                           /* 9 + 66 for one CDC-ACM */
    CHECK(cfg[4] == 2);                           /* bNumInterfaces */
    CHECK((cfg[7] & 0x80) != 0);                  /* bmAttributes bit 7 set */
    CHECK((cfg[7] & 0x40) == 0);                  /* bus powered */
    CHECK(cfg[8] == 50);                          /* 100 mA, in 2 mA units */

    int interfaces = 0, iads = 0, endpoints = 0;
    uint8_t ep_addr[8];
    for (uint16_t off = 0; off < total;) {
        uint8_t len = cfg[off], type = cfg[off + 1];
        CHECK(len >= 2 && off + len <= total);
        if (len < 2) {
            break;
        }
        if (type == TUSB_DESC_INTERFACE) {
            CHECK(cfg[off + 2] == interfaces);     /* numbered 0, 1, ... */
            interfaces++;
        } else if (type == TUSB_DESC_INTERFACE_ASSOCIATION) {
            CHECK(cfg[off + 2] == 0 && cfg[off + 3] == 2);
            iads++;
        } else if (type == TUSB_DESC_ENDPOINT) {
            uint16_t size = (uint16_t)(cfg[off + 4] | (cfg[off + 5] << 8));
            CHECK(size <= 64);                     /* full-speed limit */
            if (endpoints < 8) {
                ep_addr[endpoints] = cfg[off + 2];
            }
            endpoints++;
        }
        off = (uint16_t)(off + len);
    }
    CHECK(interfaces == cfg[4]);
    CHECK(iads == 1);
    CHECK(endpoints == 3);
    for (int i = 0; i < endpoints && i < 8; i++) {
        for (int j = i + 1; j < endpoints && j < 8; j++) {
            CHECK(ep_addr[i] != ep_addr[j]);
        }
    }

    /* ---- strings ---------------------------------------------------------- */
    const uint16_t *lang = tud_descriptor_string_cb(0, 0);
    CHECK(lang != NULL && lang[0] == ((TUSB_DESC_STRING << 8) | 4) && lang[1] == 0x0409);
    string_eq(dev->iManufacturer, USB_MANUFACTURER_STRING);
    string_eq(dev->iProduct, USB_PRODUCT_STRING);
    string_eq(dev->iSerialNumber, "003800273536510B20313748");
    string_eq(STRID_CDC, USB_CDC_INTERFACE_STRING);
    CHECK(tud_descriptor_string_cb(STRID_CDC + 1, 0x0409) == NULL);
    CHECK(strlen(usb_serial_number()) == USB_SERIAL_LEN);

    return TEST_RESULT();
}
