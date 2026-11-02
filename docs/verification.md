# Verification status

This page separates what has been checked from what has not. **No IV-DCY
board has been fabricated, assembled or powered yet.** Every result below
comes from design tools and host-side tests.

Tools used: KiCad 9.0.9, SKiDL 2.2.3, arm-none-eabi-gcc 13.2.1, host GCC
13.3, CMake 3.28, Ubuntu 24.04.

## Hardware: checked

| Check | Result |
|---|---|
| SKiDL ERC on the circuit description | no errors, no warnings |
| KiCad ERC on the schematic, all checks, errors and warnings | 0 violations (`hardware/reports/erc.rpt`) |
| Schematic netlist (exported by `kicad-cli`) against the SKiDL netlist | identical: 18 components, 13 multi-pad nets, same pads, names, values, footprints |
| KiCad DRC, all checks, errors and warnings, zones refilled | 0 violations, 0 unconnected items (`hardware/reports/drc.rpt`) |
| KiCad DRC schematic parity (PCB against schematic) | 0 issues |
| Rebuild from source twice | identical KiCad files, BOM and placement file |
| Build on a machine with no KiCad user configuration | works (`build.sh` supplies the stock library tables) |
| Outputs | BOM, Gerber X2 for both copper, mask, paste and silk layers plus the outline, Excellon PTH/NPTH drill files with maps, top-side pick-and-place, schematic PDF |

## Firmware: checked

| Check | Result |
|---|---|
| Configure and build from an empty build directory, dependencies fetched at pinned commits | succeeds; the project's own sources compile with `-Wall -Wextra -Wshadow -Wstrict-prototypes -Wmissing-prototypes -Werror` |
| Memory use | flash 11,180 B of 32 KiB (34%); RAM 2,224 B of 6 KiB (36%) including a 1 KiB stack reserve that the linker enforces |
| Linked image | vector table: initial SP `0x20001800` (top of RAM); Reset, SysTick and USB handlers at the right indices with the Thumb bit set; device descriptor bytes in flash read VID 0x1209, PID 0x6767, bcdDevice 0x0010 |
| Host unit tests (`ctest`, ASan + UBSan) | 3 of 3 pass: command parser, USB descriptors, single-source USB identity |
| Negative test of the identity check | adding a stray PID literal to `main.c` makes `identity_single_source` fail |
| Changing `USB_PID` in `usb_identity.h` alone | the descriptor in the binary changes accordingly, and all tests still pass |
| GCC `-fanalyzer` on `cli.c`, `usb_descriptors.c`, `board.c` | no findings |
| `tools/iv_dcy_check.py` | all checks pass against the real `cli.c` running behind a pseudo-terminal. This tests the tool and the protocol, **not** USB. |

## Not verified (needs hardware)

* PCB fabrication and assembly; footprint fit of the real parts, especially
  the USB-C receptacle at the board edge.
* Power: VBUS to 3.3 V regulation and current consumption. Expected to be a
  few tens of mA; not measured.
* USB enumeration on any host, and the descriptors as a host reads them
  (`lsusb -v`, USBView).
* CDC-ACM communication through a real USB stack.
* HSI48 clock recovery (CRS) locking to USB start-of-frame on real silicon.
* USB-C operation with USB-C hosts, USB-A-to-C cables and chargers (CC
  terminations).
* USB signal quality, ESD robustness and EMC.
* Entry into the ROM DFU bootloader with the BOOT button, and flashing with
  `dfu-util`; SWD programming through J2.
* LED patterns and BUTTON readback.
* Part availability: the MPNs were not checked with distributors.

**USB-IF compliance testing has not been done, and no compliance is claimed.**

## Bring-up checklist for the first boards

1. Inspect the board for solder bridges, especially at U1 (0.8 mm pitch) and
   J1.
2. Power it from a current-limited USB source or a USB power meter. Expect
   tens of mA. Measure 3.3 V at C2.
3. Hold BOOT and plug in. `lsusb` should list `0483:df11 STM32 BOOTLOADER`.
   Flash the firmware with `dfu-util` (see `firmware/README.md`).
4. Re-plug without BOOT. The LED should flash about once a second, and
   `lsusb` should list `1209:6767 IV-DCY project IV-DCY USB reference`.
   Check `lsusb -v -d 1209:6767` against
   [usb-interface.md](usb-interface.md).
5. Run `python3 firmware/tools/iv_dcy_check.py`. It should print
   `all checks passed`.
6. Repeat with the plug reversed, and with a USB-A-to-C cable.

Record the results here when they are available.
