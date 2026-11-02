/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lucas Wu
 *
 * IV-DCY USB reference firmware: enumerates as a USB CDC-ACM serial device
 * and answers the text commands described in cli.h.
 *
 * Status LED in AUTO mode:
 *   fast blink (4 Hz)       not (yet) configured by a host
 *   short flash every 1 s   configured
 *   off                     USB suspended
 */
#include "board.h"
#include "cli.h"
#include "tusb.h"
#include "usb_descriptors.h"
#include "vectors.h"

static enum led_mode led_mode = LED_MODE_AUTO;

static void cdc_write(const char *text)
{
    tud_cdc_write_str(text);
    tud_cdc_write_flush();
}

static void set_led_mode(enum led_mode mode)
{
    led_mode = mode;
}

static const cli_io_t cli_io = {
    .write = cdc_write,
    .set_led_mode = set_led_mode,
    .button_pressed = board_button,
    .serial_number = usb_serial_number,
};

static void led_task(void)
{
    uint32_t t = board_millis();
    bool on;
    switch (led_mode) {
    case LED_MODE_ON:
        on = true;
        break;
    case LED_MODE_OFF:
        on = false;
        break;
    default:
        if (tud_suspended()) {
            on = false;
        } else if (tud_mounted()) {
            on = (t % 1000u) < 100u;
        } else {
            on = (t % 250u) < 125u;
        }
        break;
    }
    board_led(on);
}

static void cdc_task(void)
{
    while (tud_cdc_available() > 0u) {
        char buf[16];
        uint32_t n = tud_cdc_read(buf, sizeof buf);
        for (uint32_t i = 0; i < n; i++) {
            cli_input(buf[i]);
        }
    }
}

int main(void)
{
    board_init();
    cli_init(&cli_io);

    const tusb_rhport_init_t init = {
        .role = TUSB_ROLE_DEVICE,
        .speed = TUSB_SPEED_FULL,
    };
    tusb_init(0, &init);

    for (;;) {
        tud_task();
        cdc_task();
        led_task();
    }
}

/* The USB interrupt only queues events; tud_task() handles them. */
void USB_IRQHandler(void)
{
    tud_int_handler(0);
}

/* Time base for TinyUSB without an RTOS. */
uint32_t tusb_time_millis_api(void)
{
    return board_millis();
}
