#!/usr/bin/env bash
# SPDX-License-Identifier: CERN-OHL-S-2.0
# Copyright (c) 2026 Lucas Wu
#
# Regenerate the IV-DCY board from source, check it, and write the outputs.
#
#   1. skidl/iv_dcy.py          -> kicad/iv_dcy.net, kicad/iv_dcy.kicad_sch
#   2. KiCad ERC on the schematic            (fails on any error or warning)
#   3. schematic netlist == SKiDL netlist    (fails on any difference)
#   4. layout/place_route.py    -> kicad/iv_dcy.kicad_pcb, kicad/iv_dcy.kicad_pro
#   5. KiCad DRC incl. schematic parity      (fails on any error or warning)
#   6. BOM, Gerbers + drill, pick-and-place, schematic PDF, board images
#
# Needs KiCad 9 (kicad-cli and its pcbnew Python module) and SKiDL; see
# hardware/README.md.  PYTHON must be an interpreter that can import both
# skidl and pcbnew (default: python3).
set -euo pipefail

HW="$(cd "$(dirname "$0")" && pwd)"
PY="${PYTHON:-python3}"
cd "$HW"

(cd "$(mktemp -d)" && "$PY" -c "import pcbnew, skidl") >/dev/null 2>&1 || {
    echo "error: '$PY' cannot import both pcbnew (KiCad 9) and skidl." >&2
    echo "       See hardware/README.md for the environment set-up." >&2
    exit 1
}
command -v kicad-cli >/dev/null || { echo "error: kicad-cli not found" >&2; exit 1; }

# kicad-cli warns about every symbol if KiCad has never been configured on this
# machine (no global symbol/footprint library tables).  Use the stock tables
# in a throw-away configuration directory in that case.
KVER="$(kicad-cli version | cut -d. -f1-2)"
CFG="${KICAD_CONFIG_HOME:-$HOME/.config/kicad}"
if [ ! -f "$CFG/$KVER/sym-lib-table" ]; then
    for t in /usr/share/kicad/template /usr/local/share/kicad/template \
             /Applications/KiCad/KiCad.app/Contents/SharedSupport/template; do
        if [ -f "$t/sym-lib-table" ]; then
            KICAD_CONFIG_HOME="$(mktemp -d)"
            export KICAD_CONFIG_HOME
            mkdir -p "$KICAD_CONFIG_HOME/$KVER"
            cp "$t/sym-lib-table" "$t/fp-lib-table" "$KICAD_CONFIG_HOME/$KVER/"
            break
        fi
    done
fi

K=kicad/iv_dcy
mkdir -p bom fab docs reports
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "== 1. SKiDL: netlist and schematic"
(cd skidl && "$PY" iv_dcy.py 2>&1 | grep -E "ERROR|ERC" || true)

echo "== 2. ERC"
kicad-cli sch erc --severity-all --exit-code-violations -o reports/erc.rpt "$K.kicad_sch"

echo "== 3. schematic netlist vs SKiDL netlist"
kicad-cli sch export netlist -o "$TMP/sch.net" "$K.kicad_sch" >/dev/null
"$PY" scripts/netlist_compare.py "$K.net" "$TMP/sch.net"

echo "== 4. placement and routing"
"$PY" layout/place_route.py
rm -f "$K.kicad_prl"

echo "== 5. DRC (with schematic parity)"
kicad-cli pcb drc --schematic-parity --severity-all --exit-code-violations \
    -o reports/drc.rpt "$K.kicad_pcb"

echo "== 6. outputs"
kicad-cli sch export bom -o bom/iv_dcy-bom.csv \
    --fields 'Reference,Value,Footprint,MPN,${QUANTITY}' \
    --labels 'Reference,Value,Footprint,MPN,Qty' \
    --group-by 'Value,Footprint,MPN' --sort-field Reference \
    --exclude-dnp "$K.kicad_sch" >/dev/null
kicad-cli pcb export gerbers -o "$TMP/gerbers/" --no-protel-ext \
    --layers F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts \
    "$K.kicad_pcb" >/dev/null
kicad-cli pcb export drill -o "$TMP/gerbers/" --format excellon \
    --excellon-separate-th --generate-map --map-format gerberx2 \
    "$K.kicad_pcb" >/dev/null
"$PY" scripts/zip_dir.py "$TMP/gerbers" fab/iv_dcy-gerbers.zip
kicad-cli pcb export pos -o fab/iv_dcy-pos.csv --format csv --units mm \
    --side front --exclude-dnp "$K.kicad_pcb" >/dev/null
kicad-cli sch export pdf -o docs/iv_dcy-schematic.pdf "$K.kicad_sch" >/dev/null
kicad-cli pcb render -o docs/iv_dcy-top.png --side top --width 1000 --height 1200 \
    --quality basic --background opaque "$K.kicad_pcb" >/dev/null 2>&1 \
    || echo "   (3D render skipped: kicad-cli pcb render failed on this machine)"
kicad-cli pcb export svg -o "$TMP/copper.svg" --mode-single --page-size-mode 2 \
    --exclude-drawing-sheet --layers F.Cu,F.SilkS,Edge.Cuts "$K.kicad_pcb" >/dev/null
cp "$TMP/copper.svg" docs/iv_dcy-top-copper.svg

echo "OK: ERC clean, schematic == SKiDL netlist, DRC clean; outputs written."
