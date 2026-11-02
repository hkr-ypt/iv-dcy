/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lucas Wu
 *
 * Board support for the IV-DCY USB reference board (STM32F042K6T6).
 *
 *   PA4         status LED, active high (D1 via R4)
 *   PB8/BOOT0   BOOT button, high while pressed (R3 pull-down)
 *   PA11/PA12   USB D-/D+ (USB full-speed device, internal D+ pull-up)
 *   PA13/PA14   SWDIO/SWCLK
 */
#ifndef BOARD_H
#define BOARD_H

#include <stdbool.h>
#include <stdint.h>

void board_init(void);          /* clocks (HSI48 + CRS), SysTick, GPIO, USB clock */
uint32_t board_millis(void);    /* milliseconds since board_init() */
void board_led(bool on);
bool board_button(void);
void board_uid(uint32_t uid[3]);   /* 96-bit factory unique ID */

#endif /* BOARD_H */
