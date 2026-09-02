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
