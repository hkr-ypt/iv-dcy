/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lucas Wu
 *
 * Unit tests for the text command interface (src/cli.c).
 */
#include "cli.h"
#include "test.h"
#include "usb_identity.h"

static char out[512];
static enum led_mode led = LED_MODE_AUTO;
static bool button;

static void write_cb(const char *s) { strncat(out, s, sizeof out - strlen(out) - 1); }
static void led_cb(enum led_mode m) { led = m; }
static bool button_cb(void) { return button; }
static const char *serial_cb(void) { return "0123456789ABCDEF01234567"; }

static const cli_io_t io = { write_cb, led_cb, button_cb, serial_cb };

/* Send `input` and return everything the device wrote back. */
static const char *send(const char *input)
{
    out[0] = '\0';
    while (*input) {
        cli_input(*input++);
    }
    return out;
}

int main(void)
{
    cli_init(&io);

    CHECK_STR(send("PING\r\n"), "PONG\r\n");
    CHECK_STR(send("ping\n"), "PONG\r\n");
    CHECK_STR(send("  Ping  \r"), "PONG\r\n");
    CHECK_STR(send("\r\n\r\n"), "");                       /* blank lines ignored */
    CHECK_STR(send("VERSION\r\n"), FW_VERSION_STRING "\r\n");
    CHECK_STR(send("INFO\r\n"),
              USB_PRODUCT_STRING " fw=" FW_VERSION_STRING " vid=" USB_VID_STRING
              " pid=" USB_PID_STRING " serial=0123456789ABCDEF01234567\r\n");
    CHECK_STR(send("HELP\r\n"),
              "commands: PING VERSION INFO LED ON|OFF|AUTO BUTTON HELP\r\n");

    CHECK_STR(send("LED ON\r\n"), "OK\r\n");
    CHECK(led == LED_MODE_ON);
    CHECK_STR(send("led off\r\n"), "OK\r\n");
    CHECK(led == LED_MODE_OFF);
    CHECK_STR(send("LED AUTO\r\n"), "OK\r\n");
    CHECK(led == LED_MODE_AUTO);
    CHECK_STR(send("LED\r\n"), "ERR usage: LED ON|OFF|AUTO\r\n");
    CHECK_STR(send("LED BLUE\r\n"), "ERR usage: LED ON|OFF|AUTO\r\n");
    CHECK_STR(send("LED ON NOW\r\n"), "ERR usage: LED ON|OFF|AUTO\r\n");
    CHECK(led == LED_MODE_AUTO);

    button = false;
    CHECK_STR(send("BUTTON\r\n"), "RELEASED\r\n");
    button = true;
    CHECK_STR(send("BUTTON\r\n"), "PRESSED\r\n");

    CHECK_STR(send("FOO\r\n"), "ERR unknown command\r\n");
    CHECK_STR(send("PING 1\r\n"), "ERR unexpected argument\r\n");

    /* Exactly CLI_MAX_LINE characters is accepted; one more is rejected and
     * the rest of that line discarded. */
    char line[CLI_MAX_LINE + 8];
    memset(line, 'X', CLI_MAX_LINE);
    strcpy(line + CLI_MAX_LINE, "\r\n");
    CHECK_STR(send(line), "ERR unknown command\r\n");
    memset(line, 'X', CLI_MAX_LINE + 1);
    strcpy(line + CLI_MAX_LINE + 1, "\r\n");
    CHECK_STR(send(line), "ERR line too long\r\n");
    CHECK_STR(send("PING\r\n"), "PONG\r\n");               /* recovers */

    /* Commands split across several USB packets. */
    CHECK_STR(send("PI"), "");
    CHECK_STR(send("NG\r\n"), "PONG\r\n");

    return TEST_RESULT();
}
