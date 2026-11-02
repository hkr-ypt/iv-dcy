# IV-DCY firmware

Firmware for the IV-DCY USB reference board (STM32F042K6T6). It enumerates
as a USB CDC-ACM device and answers the text commands listed in
[../docs/usb-interface.md](../docs/usb-interface.md).

| File | Contents |
|---|---|
| `src/usb_identity.h` | **the** USB identity: VID, PID, strings, firmware version |
| `src/usb_descriptors.c` | device, configuration (CDC-ACM with IAD) and string descriptors; serial number from the chip's unique ID |
| `src/main.c` | start-up order, TinyUSB device task, CDC input, status LED |
| `src/cli.c` | the command parser (hardware independent) |
| `src/board.c` | clocks (HSI48 + clock recovery from USB SOF), SysTick, LED/button GPIO, unique ID |
| `src/startup_stm32f042.c`, `src/stm32f042k6.ld` | vector table, reset handler, memory map |
| `src/tusb_config.h` | TinyUSB configuration |
| `tests/` | host unit tests: command parser, descriptors, single-source USB identity |
| `tools/iv_dcy_check.py` | host-side check over the serial port (needs a board) |

The code accesses registers directly through the CMSIS device header and
does not use the ST HAL.

## Building

Requirements: CMake ≥ 3.24, git, and the GNU Arm Embedded toolchain
(`arm-none-eabi-gcc`; tested with 13.2.1 from Ubuntu 24.04's
`gcc-arm-none-eabi` package).

```bash
cmake -S firmware -B build/firmware
```

```bash
cmake --build build/firmware
```

Outputs: `build/firmware/iv_dcy.elf`, `iv_dcy.bin`, `iv_dcy.hex`,
`iv_dcy.map`. The build currently uses about 11 KiB of the 32 KiB flash and
2.2 KiB of the 6 KiB RAM, including a 1 KiB stack reserve that the linker
checks.

At configure time, CMake fetches the pinned dependencies with shallow git
clones of release tags and checks each against its expected commit
(`cmake/deps.cmake`):

| Dependency | Version | Licence |
|---|---|---|
| [TinyUSB](https://github.com/hathach/tinyusb) | 0.21.0 | MIT |
| [STM32F0 CMSIS device headers](https://github.com/STMicroelectronics/cmsis-device-f0) | v2.3.8 | Apache-2.0 |
| [CMSIS 6 core headers](https://github.com/ARM-software/CMSIS_6) | v6.4.0 | Apache-2.0 |

To build offline, pass existing checkouts to CMake, for example
`-DFETCHCONTENT_SOURCE_DIR_TINYUSB=/path/to/tinyusb`. The other two use the
variables `..._CMSIS_DEVICE_F0` and `..._CMSIS_CORE`.

## Tests (host)

```bash
cmake -S firmware/tests -B build/tests
```

```bash
cmake --build build/tests && ctest --test-dir build/tests --output-on-failure
```

* `cli` exercises every command, case and whitespace handling, argument
  errors, line-length overflow and recovery, and input split across USB
  packets.
* `descriptors` builds the real `usb_descriptors.c` against TinyUSB's headers
  on the host. It checks the device descriptor against `usb_identity.h`, and
  walks the configuration descriptor (lengths, interface numbering, IAD,
  endpoint count, sizes and uniqueness). It also checks every string
  descriptor, including the serial number format.
* `identity_single_source` fails if the VID or PID literal appears in any
  file under `src/` other than `usb_identity.h`.

The tests build with AddressSanitizer and UndefinedBehaviorSanitizer by
default (`-DIV_DCY_SANITIZE=OFF` to disable).

## Flashing

**USB DFU (no programmer).** Hold the BOOT button while plugging the board
in, then release it. The STM32's ROM bootloader enumerates as "STM32
BOOTLOADER", USB ID 0483:df11, which is ST's own ID, not this project's.
Then run:

```bash
dfu-util -a 0 -s 0x08000000:leave -D build/firmware/iv_dcy.bin
```

STM32CubeProgrammer works as well. A blank STM32F042 may start the
bootloader without the button.

**SWD.** Connect an ST-LINK, CMSIS-DAP or J-Link probe to J2 (ARM 10-pin
1.27 mm), for example with OpenOCD:

```bash
openocd -f interface/stlink.cfg -f target/stm32f0x.cfg -c "program build/firmware/iv_dcy.elf verify reset exit"
```

## Changing the USB identity

Edit `src/usb_identity.h` and rebuild. Nothing else needs to change. The
descriptors, the `INFO` reply and `tools/iv_dcy_check.py` all read this
file, and the `identity_single_source` test fails if a copy of the VID or PID
appears anywhere else under `src/`. PID `0x6767` is the value this project
will request from pid.codes and **is not assigned yet**. For boards you hand
to anyone else before it is assigned, use the pid.codes test PID `0x0001`.

## Status LED (AUTO mode)

| Pattern | Meaning |
|---|---|
| fast blink, 4 Hz | powered, not (yet) configured by a USB host |
| short flash every second | configured by the host |
| off | USB suspended |

## Not yet verified on hardware

The firmware compiles, links and passes its host tests. It has **not** run on
an STM32F042 yet; see [../docs/verification.md](../docs/verification.md).
