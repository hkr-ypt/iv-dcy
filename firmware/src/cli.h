/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lucas Wu
 *
 * Line-based text command interface carried over the USB CDC-ACM port.
 * Hardware independent, so it is unit tested on the host (tests/test_cli.c).
 *
 * Commands (case-insensitive, one per line, CR and/or LF terminated):
 *   PING              -> PONG
 *   VERSION           -> firmware version, e.g. 0.1.0
 *   INFO              -> product, firmware version, VID/PID, serial number
 *   LED ON|OFF|AUTO   -> OK   (AUTO: blink pattern shows the USB state)
 *   BUTTON            -> PRESSED | RELEASED   (the BOOT button)
 *   HELP              -> list of commands
 * Every reply is one line ending in CR LF; errors start with "ERR ".
 */
#ifndef CLI_H
#define CLI_H

#include <stdbool.h>

enum led_mode { LED_MODE_AUTO = 0, LED_MODE_OFF, LED_MODE_ON };

typedef struct {
    void (*write)(const char *text);   /* send text to the host */
    void (*set_led_mode)(enum led_mode mode);
    bool (*button_pressed)(void);
    const char *(*serial_number)(void);
} cli_io_t;

#define CLI_MAX_LINE 32   /* longest accepted command line, in characters */

void cli_init(const cli_io_t *io);
void cli_input(char c);   /* feed one received character */

#endif /* CLI_H */
