# Local CAD libraries

## ESP32-P4X symbol

The KiCad 9 geometry was normalized against the current official Espressif `ESP32-P4X` pin map from:

- https://github.com/espressif/kicad-libraries
- official symbol: `ESP32-P4X`
- required M1 MPN: `ESP32-P4NRW32X`

All 105 physical pin numbers, names and electrical types are programmatically matched to the official symbol. The local copy exists because the current upstream symbol library is stored in KiCad 10 format while Pajoniiir-M1 targets KiCad 9.

## ESP32-P4 footprint

`footprints.pretty/ESP32-P4.kicad_mod` is the official Espressif KiCad 9 footprint from the same upstream library.

Verify upstream package drawing again before fabrication.

## TPS259474 / RPW0010A footprint

`footprints.pretty/Texas_RPW0010A_VQFN-HR-10_2x2mm.kicad_mod` is the project-local KiCad 9 land pattern for `TPS259474ARPWR`.

Source of truth: TI TPS25947 package drawing `4225183/A`, package `RPW0010A` (VQFN-HR-10, 2 x 2 mm), including the example board layout and 0.100 mm stencil design. The copper geometry uses the asymmetric HotRod corner lands and long IN/OUT pads; the stencil keeps TI's approximately 93% corner-pad and 82% IN/OUT-pad paste coverage. Solder mask is +0.05 mm NSMD rather than zero expansion, consistent with the package drawing tolerance and the TI E2E footprint discussion.

Do not substitute a generic symmetric QFN footprint. Re-run `tools/validate_schematic_structure.py` after any change to this footprint.

## INA238 / DGS0010A footprint

`footprints.pretty/Texas_DGS0010A_VSSOP-10_3x3mm_P0.5mm.kicad_mod` uses the TI INA238 DGS0010A example land pattern: ten 1.45 x 0.30 mm pads, 0.50 mm pitch, 4.40 mm row centers, no exposed pad. Source: [TI INA238 datasheet](https://www.ti.com/lit/ds/symlink/ina238.pdf), DGS0010A example board layout. Native pcbnew loading and pad geometry were checked locally.

## Stable connector symbols

`USB_A_M1` (J2/J3) and `MicroSD_Det1_M1` (J7) retain the existing symbol geometry and electrical numbering. Their shield pins are 5 and 10 respectively, matching the project footprints. They isolate the design from standard-library shield renumbering. After changes, export the native netlist/ERC and run `tools/validate_power_good_closure.py`.
