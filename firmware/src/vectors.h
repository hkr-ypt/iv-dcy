/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lucas Wu
 *
 * Exception and interrupt handlers referenced by the vector table
 * (startup_stm32f042.c).  Handlers not defined elsewhere fall back to
 * Default_Handler.
 */
#ifndef VECTORS_H
#define VECTORS_H

void Reset_Handler(void);
void Default_Handler(void);
void NMI_Handler(void);
void HardFault_Handler(void);
void SVC_Handler(void);
void PendSV_Handler(void);
void SysTick_Handler(void);   /* board.c */
void USB_IRQHandler(void);    /* main.c */

#endif /* VECTORS_H */
