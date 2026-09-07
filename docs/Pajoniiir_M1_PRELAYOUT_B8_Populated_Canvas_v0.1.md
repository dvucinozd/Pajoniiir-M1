# Pajoniiir-M1 M1-PRELAYOUT-B8 populated canvas

**Date:** 2026-09-06

**Result:** PASS — live PCB populated for board-first placement work

**Production placement:** no

**Layout freeze:** blocked

## Purpose

B7 proved that the schematic has a complete, loadable footprint inventory. B8 moves that inventory into the live KiCad PCB so placement work can proceed from the mainboard's electrical and physical needs. No display model supplies the PCB origin, outline, mount pattern or connector XY.

## Generated board state

- 247 schematic components
- 244 instantiated footprints
- 3 intentional blank-footprint gates: `C3`, `C8`, `J1`
- 193 named schematic nets
- 715 connected netlist nodes checked
- 8 board-local working domains
- 0 footprint bounding-box overlaps
- 0 tracks or vias
- 0 copper zones
- 0 `Edge.Cuts`

The eight domain rectangles are drawn on `Dwgs.User`: `POWER_SPINE`, `USB_EDGES`, `AUDIO`, `P4_CORE`, `C6_RF`, `DSI_HOST`, `STORAGE` and `SERVICE`. They keep the first placement pass readable. Their coordinates and dimensions are recorded in `hardware/Pajoniiir-M1/m1_board_placement_seed_b8.json`.

## Reproducibility

Export a fresh XML netlist with the same KiCad build used to edit the project, then run the seed only against an empty board:

```powershell
& 'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe' sch export netlist `
  --format kicadxml `
  --output $env:TEMP\Pajoniiir-M1.net.xml `
  hardware\Pajoniiir-M1\Pajoniiir-M1.kicad_sch

& 'C:\Program Files\KiCad\10.0\bin\python.exe' `
  hardware\Pajoniiir-M1\tools\seed_board_placement_b8.py `
  --board hardware\Pajoniiir-M1\Pajoniiir-M1.kicad_pcb `
  --netlist $env:TEMP\Pajoniiir-M1.net.xml `
  --output <empty-board-output.kicad_pcb> `
  --report <placement-report.json>
```

The seed fails closed if the input board already contains footprints or `Edge.Cuts`. It loads only the footprints assigned by the exported schematic, preserves hierarchical schematic UUID paths, applies DNP/BOM state and assigns every available pad to its exported net.

Validate the live canvas with KiCad's bundled Python:

```powershell
& 'C:\Program Files\KiCad\10.0\bin\python.exe' `
  hardware\Pajoniiir-M1\tools\validate_board_placement_b8.py `
  --board hardware\Pajoniiir-M1\Pajoniiir-M1.kicad_pcb `
  --netlist $env:TEMP\Pajoniiir-M1.net.xml `
  --report hardware\Pajoniiir-M1\m1_board_placement_seed_b8.json
```

## What B8 does not establish

B8 does not establish a board outline, mounting holes, connector panel datums, RF edge, power-current geometry, controlled-impedance widths, routing, thermal solution or product enclosure. The large canvas is intentionally loose so each domain can be compacted from its own route and courtyard constraints.

## Next placement order

1. Compact U1, U2, U3, Y1, L1 and their local decoupling into the P4 core/flash island.
2. Move U4 to a candidate outer edge, keep its antenna region clear on all copper layers and prove four-bit SDIO escape.
3. Compact the input/eFuse/shunt/buck and USB switch power spine with J1/C3/C8 still explicit gates.
4. Establish USB, DSI, RCA, microSD and service-edge corridors from actual mated connector envelopes.
5. Derive the smallest feasible board envelope and board-owned chassis mount pattern.

No B8 coordinate may be promoted to production authority until its relevant routing, mechanical and EVT gate closes.

The next pass must use the current [Espressif ESP32-P4 PCB layout guidance](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32p4/pcb-layout-design-esp32p4.html). For v3.x, this means keeping the external DCDC input/output/feedback loops close to U1, placing 100 nF at each power pin and 10 µF at the relevant power entrances, keeping the crystal at least 4.5 mm from the clock pins with no XTAL vias, and preserving a complete GND reference. The current schematic already uses the updated 10 kΩ / 1 µF `CHIP_PU` network from the [Espressif schematic checklist](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32p4/schematic-checklist-esp32p4.html).
