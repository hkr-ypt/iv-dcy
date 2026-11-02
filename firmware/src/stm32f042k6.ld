/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lucas Wu
 *
 * Linker script for the STM32F042K6: 32 KiB flash, 6 KiB SRAM.
 */
ENTRY(Reset_Handler)

MEMORY
{
    FLASH (rx)  : ORIGIN = 0x08000000, LENGTH = 32K
    RAM   (rwx) : ORIGIN = 0x20000000, LENGTH = 6K
}

_estack = ORIGIN(RAM) + LENGTH(RAM);
_min_stack_size = 0x400;   /* the link fails if less than this is left */

SECTIONS
{
    .isr_vector :
    {
        KEEP(*(.isr_vector))
    } > FLASH

    .text :
    {
        *(.text*)
        *(.rodata*)
        . = ALIGN(4);
    } > FLASH

    .ARM.exidx :
    {
        *(.ARM.exidx*)
    } > FLASH

    _sidata = LOADADDR(.data);

    .data :
    {
        . = ALIGN(4);
        _sdata = .;
        *(.data*)
        . = ALIGN(4);
        _edata = .;
    } > RAM AT > FLASH

    .bss (NOLOAD) :
    {
        . = ALIGN(4);
        _sbss = .;
        *(.bss*)
        *(COMMON)
        . = ALIGN(4);
        _ebss = .;
    } > RAM

    PROVIDE(end = _ebss);

    .stack_reserve (NOLOAD) :
    {
        . = ALIGN(8);
        . = . + _min_stack_size;
    } > RAM
}
