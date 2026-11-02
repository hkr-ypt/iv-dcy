/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lucas Wu
 *
 * STM32F042K6T6 bring-up, register level (CMSIS device header only).
 *
 * Clock: the STM32F042 has a 48 MHz RC oscillator (HSI48) that the clock
 * recovery system (CRS) keeps trimmed to the 1 kHz USB start-of-frame
 * packets, so no crystal is needed for full-speed USB.  HSI48 also drives
 * the core (SYSCLK = HCLK = PCLK = 48 MHz, one flash wait state).
 * References: ST RM0091 sections 3 (flash), 6 (RCC), 7 (CRS), 8 (GPIO).
 */
#include "board.h"

#include "stm32f0xx.h"
#include "vectors.h"

uint32_t SystemCoreClock = 8000000u;   /* HSI after reset; updated below */

static volatile uint32_t ms_ticks;

void SysTick_Handler(void)
{
    ms_ticks++;
}

uint32_t board_millis(void)
{
    return ms_ticks;
}

void board_init(void)
{
    /* One wait state and the prefetch buffer are required above 24 MHz. */
    FLASH->ACR = FLASH_ACR_PRFTBE | FLASH_ACR_LATENCY;

    /* Start HSI48 and run the system from it, AHB and APB undivided. */
    RCC->CR2 |= RCC_CR2_HSI48ON;
    while ((RCC->CR2 & RCC_CR2_HSI48RDY) == 0u) {
    }
    RCC->CFGR = (RCC->CFGR & ~(RCC_CFGR_SW | RCC_CFGR_HPRE | RCC_CFGR_PPRE))
              | RCC_CFGR_SW_HSI48;
    while ((RCC->CFGR & RCC_CFGR_SWS) != RCC_CFGR_SWS_HSI48) {
    }
    SystemCoreClock = 48000000u;

    /* USB kernel clock = HSI48 (USBSW = 0), trimmed by the CRS to USB SOF.
     * The CRS reset configuration already selects USB SOF as the sync
     * source with the 48 MHz / 1 kHz reload value; enable auto-trimming. */
    RCC->CFGR3 &= ~RCC_CFGR3_USBSW;
    RCC->APB1ENR |= RCC_APB1ENR_CRSEN;
    CRS->CR |= CRS_CR_AUTOTRIMEN | CRS_CR_CEN;

    /* GPIO: PA4 push-pull output (LED); PB8 stays an input (BOOT button).
     * PA13/PA14 keep their reset function (SWD). */
    RCC->AHBENR |= RCC_AHBENR_GPIOAEN | RCC_AHBENR_GPIOBEN;
    GPIOA->BRR = 1u << 4;
    GPIOA->MODER = (GPIOA->MODER & ~GPIO_MODER_MODER4) | GPIO_MODER_MODER4_0;

    /* USB peripheral clock; PA11/PA12 connect to the USB block directly
     * (no alternate-function setting needed on this package). */
    RCC->APB1ENR |= RCC_APB1ENR_USBEN;

    SysTick_Config(SystemCoreClock / 1000u);
}

void board_led(bool on)
{
    if (on) {
        GPIOA->BSRR = 1u << 4;
    } else {
        GPIOA->BRR = 1u << 4;
    }
}

bool board_button(void)
{
    return (GPIOB->IDR & (1u << 8)) != 0u;
}

void board_uid(uint32_t uid[3])
{
    const volatile uint32_t *id = (const volatile uint32_t *)UID_BASE;
    uid[0] = id[0];
    uid[1] = id[1];
    uid[2] = id[2];
}
