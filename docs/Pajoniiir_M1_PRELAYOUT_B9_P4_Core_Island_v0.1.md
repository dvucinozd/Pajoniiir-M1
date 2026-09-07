# Pajoniiir-M1 M1-PRELAYOUT-B9 P4 core island

**Date:** 2026-09-07

**Result:** PASS - compact, reproducible routing-feasibility seed

**Production placement:** no

**Layout freeze:** blocked

## Purpose

B9 performs the first electrical compaction inside the B8 board-first canvas. It groups the ESP32-P4, external QSPI flash, v3.x external core DCDC, 40 MHz crystal and their local support parts without choosing the product outline, connector panel, mounting pattern or enclosure.

The pass follows the current Espressif ESP32-P4 guidance: use a complete GND reference, keep the external DCDC input/output/feedback loops close to the SoC, place local bypass and reservoir capacitors around the relevant supply pins, keep the crystal body at least 4.5 mm from the chip, keep the crystal traces free of vias, and retain QSPI series-tuning footprints.

## Generated board state

- 63 footprints from `03_P4_CORE` and `04_P4_FLASH_CLOCK_RESET` moved deterministically;
- P4 working-group bounding box: 52.602 x 50.033 mm;
- U1 to U2 center distance: 16.500 mm;
- U1 to U3 center distance: 15.556 mm;
- U3 to L1 center distance: 7.071 mm;
- U1-to-Y1 body gap: 7.285 mm;
- zero P4 footprint bounding-box overlaps;
- zero tracks/vias, zones and `Edge.Cuts` on the board.

The six QSPI tuning resistors form a row between U1 and U2. R36 is on the chip side of the crystal path, while C61 and C62 flank Y1. U3, L1, R27, R28, C40, C41, C42 and C43 form the candidate external-DCDC cluster. These are placement intentions that still require actual escape and copper-loop proof.

## Reproducibility

Apply the placement to the complete unrouted B8 canvas with KiCad's bundled Python:

```powershell
& 'C:\Program Files\KiCad\10.0\bin\python.exe' `
  hardware\Pajoniiir-M1\tools\apply_core_placement_b9.py `
  --board hardware\Pajoniiir-M1\Pajoniiir-M1.kicad_pcb `
  --output <b9-output.kicad_pcb> `
  --report <b9-report.json>
```

The apply tool refuses an incomplete board or any board that already contains tracks, zones or `Edge.Cuts`. It moves only the two P4/flash sheet groups and records all 63 coordinates in the JSON report.

Validate the live board:

```powershell
& 'C:\Program Files\KiCad\10.0\bin\python.exe' `
  hardware\Pajoniiir-M1\tools\validate_core_placement_b9.py `
  --board hardware\Pajoniiir-M1\Pajoniiir-M1.kicad_pcb `
  --report hardware\Pajoniiir-M1\m1_prelayout_b9_core_island.json
```

The validator fails if a coordinate drifts, a P4 footprint overlaps, Y1 violates the 4.5 mm body gap, the critical anchors spread beyond the screening limits, the working group exceeds its B8 rectangle, or copper/zones/`Edge.Cuts` appear.

## Boundary and next pass

B9 establishes a reproducible starting point for routing study. It does not prove the final U1 escape, DCDC current loops, QSPI timing, crystal routing, thermal behavior or EMI performance. All coordinates remain movable.

The next pass should route or otherwise prove the critical U1 escape corridors, then place U4 at a candidate board edge with its antenna keepout and four-bit SDIO path. A board outline remains prohibited until those islands, connector envelopes, power spine and mounting requirements establish a board-owned envelope.

## Source guidance

- [Espressif ESP32-P4 PCB Layout Design](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32p4/pcb-layout-design-esp32p4.html)
- [Espressif ESP32-P4 Schematic Checklist](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32p4/schematic-checklist-esp32p4.html)
