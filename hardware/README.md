# IV-DCY hardware

A bus-powered USB-C board built around the STM32F042K6T6. Everything in this
directory is generated from two source files:

| Source | Defines | Generated |
|---|---|---|
| [`skidl/iv_dcy.py`](skidl/iv_dcy.py) | the circuit: parts, values, footprints, MPNs, nets; plus where each symbol sits on the schematic sheet | `kicad/iv_dcy.net`, `kicad/iv_dcy.kicad_sch` |
| [`layout/place_route.py`](layout/place_route.py) | the PCB: outline, placement, every track and via, GND pours, silkscreen, design rules | `kicad/iv_dcy.kicad_pcb`, `kicad/iv_dcy.kicad_pro` |

All symbols and footprints come from the stock KiCad 9 libraries. There is no
project-specific library. The KiCad files are ordinary KiCad 9 files that
can be opened and edited directly. If you edit them by hand rather than
through the Python sources, the next `build.sh` run overwrites the edits.

## Regenerating and checking the design

Requirements: KiCad 9.0 (`kicad-cli` plus the `pcbnew` Python module that
ships with it) and SKiDL 2.2.3. On Ubuntu, the `kicad` package from the
KiCad 9.0 PPA provides both KiCad and the libraries. Create a virtual
environment that can see KiCad's `pcbnew` module:

```bash
python3 -m venv --system-site-packages .venv
```

```bash
.venv/bin/pip install -r hardware/requirements.txt
```

```bash
PYTHON=.venv/bin/python hardware/build.sh
```

`build.sh` runs these steps and stops at the first failure:

1. `skidl/iv_dcy.py`: builds the circuit, runs SKiDL's ERC, and writes the
   netlist and the schematic (drawn by `skidl/kicad_sch.py`).
2. KiCad ERC on the schematic, with every check enabled. It fails on any error
   or warning. Report: `reports/erc.rpt`.
3. The schematic's netlist, exported by `kicad-cli`, is compared with the
   SKiDL netlist pad by pad (`scripts/netlist_compare.py`).
4. `layout/place_route.py` rebuilds the PCB and fills the zones.
5. KiCad DRC with schematic parity and every check enabled. It fails on any
   violation, unconnected item or parity difference. Report: `reports/drc.rpt`.
6. Outputs: `bom/iv_dcy-bom.csv`, `fab/iv_dcy-gerbers.zip` (Gerber X2 plus
   Excellon drill), `fab/iv_dcy-pos.csv` (pick-and-place, top side),
   `docs/iv_dcy-schematic.pdf`, and board images in `docs/`.

Re-running the build gives identical netlist, schematic and board files.
The UUIDs are deterministic.

## Circuit

* **USB-C (J1)**: USB 2.0 receptacle. D+ (A6/B6) and D− (A7/B7) are joined
  next to the connector, so both plug orientations work. CC1/CC2 each have a
  5.1 kΩ pull-down (R1, R2), the USB-C "sink" termination, so a USB-C host or
  charger turns VBUS on. SBU1/SBU2 are unused. The shell is tied to GND.
* **ESD (U3)**: USBLC6-2SC6 in flow-through layout (pins 1/6 = D+,
  3/4 = D−), placed between the connector and the MCU, with its VBUS pin on
  VBUS.
* **Power (U2)**: MCP1700-3.3 low-dropout regulator, VBUS to 3.3 V. C1 is
  1 µF at the input; C2 is 4.7 µF at the output. The total capacitance on
  VBUS (C1) stays far below USB's 10 µF inrush limit. The board's current
  draw has not been measured. It is expected to be a few tens of mA, well
  within both the MCP1700's 250 mA rating and the 100 mA declared in the
  USB descriptor.
* **MCU (U1)**: STM32F042K6T6 in LQFP-32. The USB D+ pull-up and the 48 MHz
  oscillator are on chip, and the clock recovery system trims that oscillator
  to the host's USB frames, so the board needs no crystal. Decoupling: C3
  (100 nF, VDD), C4 (100 nF, VDDIO2), C5 + C6 (1 µF + 10 nF, VDDA), all from
  the single 3.3 V rail. C7 (100 nF) filters NRST.
* **BOOT (SW1, R3)**: PB8 is also the BOOT0 pin on this part. R3 holds it
  low. Pressing SW1 pulls it to 3.3 V, so a board powered up with SW1 held
  starts ST's ROM USB DFU bootloader. This relies on the factory option
  bytes, which take BOOT0 from the pin. After reset, PB8 is an ordinary
  input, so the firmware can read the button.
* **LED (D1, R4)**: on PA4, active high, about 1 mA through 1 kΩ.
* **SWD (J2)**: ARM Cortex 10-pin 1.27 mm header. Pin 1 VTref (3.3 V),
  2 SWDIO, 4 SWCLK, 10 nRESET; 3/5/9 GND; 6 and 8 are not connected (the
  Cortex-M0 has no SWO).

## PCB

* 28 × 36 mm, 2 layers, 1.6 mm FR-4, 1 oz copper; all parts on the top side.
* Design rules: 0.2 mm tracks and clearance (0.4 mm for the VBUS and +3V3
  trunks), 0.6 mm
  vias with 0.3 mm drill, 0.3 mm copper-to-edge. These are within the
  standard capabilities of common low-cost PCB services.
* Both layers carry a GND pour, stitched with vias. The bottom layer is
  almost unbroken GND: only a short VBUS link behind the connector and the
  NRST connection to J2 run there.
* D+/D− run as a short, tightly coupled pair on the top layer over the bottom
  GND plane: connector, then ESD array, then MCU. Full-speed USB (12 Mbit/s)
  does not need impedance-controlled stack-up.
* The USB-C receptacle sits on the bottom board edge, as its footprint expects.
* The bottom silkscreen carries the licence and the source location, as
  CERN-OHL-S-2.0 asks of products.

## Not yet verified

This design has been checked by ERC, DRC and netlist parity only. **No board
has been fabricated, assembled or powered.** See
[../docs/verification.md](../docs/verification.md).

## Licence

CERN-OHL-S-2.0 ([text](../LICENSES/CERN-OHL-S-2.0.txt)). This source
describes Open Hardware and is licensed under the CERN-OHL-S v2. You may
redistribute and modify this source and make products using it under the
terms of the CERN-OHL-S v2. It is distributed WITHOUT ANY EXPRESS OR IMPLIED
WARRANTY, INCLUDING OF MERCHANTABILITY, SATISFACTORY QUALITY AND FITNESS FOR
A PARTICULAR PURPOSE. Source location: https://github.com/hkr-ypt/iv-dcy

The KiCad library symbols and footprints embedded in the KiCad files are
© the KiCad library contributors, CC-BY-SA-4.0 with the KiCad libraries
exception, which waives the share-alike terms for designs that use them.
