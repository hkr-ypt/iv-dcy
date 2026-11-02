# Third-party components

This repository contains only the project's own files. Third-party code and
data are fetched or installed separately and keep their own licences.

| Component | Version | Licence | How it is used |
|---|---|---|---|
| [TinyUSB](https://github.com/hathach/tinyusb), © Ha Thach and contributors | 0.21.0 | MIT | USB device stack, compiled into the firmware. Fetched by CMake at build time. |
| [cmsis-device-f0](https://github.com/STMicroelectronics/cmsis-device-f0), © STMicroelectronics | v2.3.8 | Apache-2.0 | STM32F0 register definitions (headers only). Fetched at build time. |
| [CMSIS 6](https://github.com/ARM-software/CMSIS_6), © Arm Limited | v6.4.0 | Apache-2.0 | Cortex-M0 core header (headers only). Fetched at build time. |
| [KiCad libraries](https://www.kicad.org/libraries/license/) | 9.0 | CC-BY-SA-4.0 with the KiCad library exception | Symbols and footprints, embedded in the KiCad files as KiCad always does. The exception waives the share-alike terms for designs that use them. |
| [SKiDL](https://github.com/devbisme/skidl) | 2.2.3 | MIT | Build-time tool (circuit description to netlist). Not redistributed. |
| [KiCad](https://www.kicad.org/) | 9.0 | GPL-3.0-or-later | Build-time tool (ERC, DRC, plotting) and editor. Not redistributed. |

## Distributing firmware binaries

A compiled `iv_dcy.bin`/`.hex` contains TinyUSB code and is built with the
CMSIS headers. Anyone distributing a binary should include, alongside it:

* the MIT licence notices of this project (`LICENSES/MIT.txt`) and of
  TinyUSB (its `LICENSE` file), and
* the Apache-2.0 licence text that covers the CMSIS headers.

This repository does not distribute firmware binaries.
