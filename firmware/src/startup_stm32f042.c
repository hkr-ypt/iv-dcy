/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lucas Wu
 *
 * Start-up code for the STM32F042: vector table and reset handler.
 * The Cortex-M0 has no VTOR, so the table must sit at the start of flash
 * (the .isr_vector section, placed first by stm32f042k6.ld).
 */
#include <stdint.h>

#include "vectors.h"

extern uint32_t _sidata[], _sdata[], _edata[], _sbss[], _ebss[], _estack[];

int main(void);

void Default_Handler(void)
{
    for (;;) {
    }
}

void NMI_Handler(void) __attribute__((weak, alias("Default_Handler")));
void HardFault_Handler(void) __attribute__((weak, alias("Default_Handler")));
void SVC_Handler(void) __attribute__((weak, alias("Default_Handler")));
void PendSV_Handler(void) __attribute__((weak, alias("Default_Handler")));
void SysTick_Handler(void) __attribute__((weak, alias("Default_Handler")));
void USB_IRQHandler(void) __attribute__((weak, alias("Default_Handler")));

#define NUM_IRQS 32   /* STM32F042 peripheral interrupts; USB is IRQ 31 */

__attribute__((section(".isr_vector"), used))
void (*const vector_table[16 + NUM_IRQS])(void) = {
    (void (*)(void))(uintptr_t)_estack,   /* initial stack pointer */
    Reset_Handler,
    NMI_Handler,
    HardFault_Handler,
    [11] = SVC_Handler,
    [14] = PendSV_Handler,
    [15] = SysTick_Handler,
    [16 ... 16 + 30] = Default_Handler,   /* IRQ 0..30: unused */
    [16 + 31] = USB_IRQHandler,
};

void Reset_Handler(void)
{
    uint32_t *src = _sidata;
    for (uint32_t *dst = _sdata; dst < _edata;) {
        *dst++ = *src++;
    }
    for (uint32_t *dst = _sbss; dst < _ebss;) {
        *dst++ = 0u;
    }
    (void)main();
    for (;;) {
    }
}
