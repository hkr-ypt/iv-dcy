/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lucas Wu
 *
 * Text command interface: see cli.h.
 */
#include "cli.h"

#include <stddef.h>
#include <string.h>

#include "usb_identity.h"

static const cli_io_t *io;
static char line[CLI_MAX_LINE + 1];
static size_t len;
static bool overflow;

void cli_init(const cli_io_t *new_io)
{
    io = new_io;
    len = 0;
    overflow = false;
}

static void reply(const char *text)
{
    io->write(text);
    io->write("\r\n");
}

static char upper(char c)
{
    return (c >= 'a' && c <= 'z') ? (char)(c - 'a' + 'A') : c;
}

/* Split off the first space-separated word of *s; returns it, advances *s. */
static char *next_word(char **s)
{
    char *p = *s;
    while (*p == ' ' || *p == '\t') {
        p++;
    }
    char *word = p;
    while (*p != '\0' && *p != ' ' && *p != '\t') {
        p++;
    }
    if (*p != '\0') {
        *p++ = '\0';
    }
    *s = p;
    return word;
}

static void execute(char *cmdline)
{
    for (char *p = cmdline; *p != '\0'; p++) {
        *p = upper(*p);
    }
    char *rest = cmdline;
    const char *cmd = next_word(&rest);
    const char *arg = next_word(&rest);
    const char *extra = next_word(&rest);

    if (cmd[0] == '\0') {
        return;                                   /* blank line: no reply */
    }
    if (strcmp(cmd, "LED") == 0) {
        if (extra[0] != '\0') {
            reply("ERR usage: LED ON|OFF|AUTO");
        } else if (strcmp(arg, "ON") == 0) {
            io->set_led_mode(LED_MODE_ON);
            reply("OK");
        } else if (strcmp(arg, "OFF") == 0) {
            io->set_led_mode(LED_MODE_OFF);
            reply("OK");
        } else if (strcmp(arg, "AUTO") == 0) {
            io->set_led_mode(LED_MODE_AUTO);
            reply("OK");
        } else {
            reply("ERR usage: LED ON|OFF|AUTO");
        }
        return;
    }
    if (arg[0] != '\0') {
        reply("ERR unexpected argument");
        return;
    }
    if (strcmp(cmd, "PING") == 0) {
        reply("PONG");
    } else if (strcmp(cmd, "VERSION") == 0) {
        reply(FW_VERSION_STRING);
    } else if (strcmp(cmd, "INFO") == 0) {
        io->write(USB_PRODUCT_STRING " fw=" FW_VERSION_STRING
                  " vid=" USB_VID_STRING " pid=" USB_PID_STRING " serial=");
        reply(io->serial_number());
    } else if (strcmp(cmd, "BUTTON") == 0) {
        reply(io->button_pressed() ? "PRESSED" : "RELEASED");
    } else if (strcmp(cmd, "HELP") == 0) {
        reply("commands: PING VERSION INFO LED ON|OFF|AUTO BUTTON HELP");
    } else {
        reply("ERR unknown command");
    }
}

void cli_input(char c)
{
    if (c == '\r' || c == '\n') {
        if (overflow) {
            reply("ERR line too long");
        } else {
            line[len] = '\0';
            execute(line);
        }
        len = 0;
        overflow = false;
        return;
    }
    if (overflow) {
        return;                                   /* discard until end of line */
    }
    if (len >= CLI_MAX_LINE) {
        overflow = true;
        return;
    }
    line[len++] = c;
}
