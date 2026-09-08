# Pajoniiir-M1 M1-PRELAYOUT-B10 P4 critical routes

**Date:** 2026-09-08

**Result:** PASS - critical-route geometry is feasible and has zero route-specific KiCad DRC violations

**Production layout:** no

**Layout freeze:** blocked

**ECAD toolchain:** KiCad 10.x only

## Purpose

B10 converts the B9 P4 placement seed into real copper evidence for the external flash, 40 MHz crystal and ESP32-P4 external core regulator. It remains a reversible pre-layout study: connector edges, chassis holes, final board outline, planes, complete power escape and production impedance geometry are still open.

The live board keeps the four-layer `JLC04161H-7628` stack. U1 is rotated 180 degrees so its flash pins face U2, FB/EN/VDD_HP face the regulator area, and XTAL_P/N face the crystal area. The project Default clearance is 0.15 mm, matching the existing board minimum and allowing the 0.35 mm-pitch U1 pad escape to be checked without false 0.20 mm clearance failures.

## Routed scope

### External QSPI flash

- all six U1-to-series-resistor and resistor-to-U2 signal paths are routed;
- the U1 fanout uses 0.15 mm F.Cu tracks;
- D, CLK and HOLD remain on F.Cu;
- WP, Q and CS each use one 0.60/0.30 mm via pair to cross beneath the package on B.Cu;
- U2 VCC is routed to C60 through In2.Cu;
- QSPI signal-via count is six;
- measured route-length range is 16.408 to 28.616 mm, a 12.208 mm screening spread.

This spread is feasibility evidence, not a production timing or SI lock. The routes may be shortened or rebalanced after the complete P4 escape and return-plane review.

### Crystal

- XTAL_P, R36, Y1, XTAL_N, C61 and C62 are connected on F.Cu;
- the three crystal nets contain no vias;
- U1-to-Y1 body gap is 5.203 mm;
- the P/N paths do not cross and have no route-specific DRC finding.

The placement follows Espressif's guidance to keep the crystal away from the chip, place the series resistor near the chip side, keep load capacitors by the crystal and avoid XTAL vias.

### External core DCDC

- C40-to-U3 VIN, U3 SW-to-L1, L1-to-C41/C43 VDD_HP, EN and FB are routed;
- VIN, SW and VDD_HP trunks use 0.65 mm copper;
- fine-pitch package necks use 0.15 or 0.20 mm copper;
- the feedback divider and output sense stay away from the compact F.Cu switch node;
- VDD_HP uses B.Cu for the longer connection back to U1.

The topology follows TI's TLV62569 placement guidance: keep the input capacitor, inductor and output capacitors close, use short direct power paths and keep FB away from SW.

## Measured board state

```text
footprints                         244
named schematic nets              193
track segments                     78
vias                               11
zones                               0
Edge.Cuts primitives                0
P4 footprint bbox overlaps          0
crystal body gap to U1          5.203 mm
QSPI route-length spread       12.208 mm
remaining unconnected items       499
```

Track layers:

```text
F.Cu      70 segments
B.Cu       7 segments
In2.Cu     1 segment
```

## DRC result and limits

KiCad 10.0.4 reports zero violations involving a B10 track or via for clearance, shorts, crossing tracks, hole clearance, track width, dangling vias or drill size.

The full unfinished board still reports 13 non-routing findings:

- four 0.20 mm thermal-via drills inside the existing U8 exposed pad against the 0.30 mm project minimum;
- six silkscreen-over-copper findings;
- two silkscreen-overlap findings;
- one intentionally missing-outline finding because `Edge.Cuts` remains prohibited.

There are 499 unrouted items because B10 routes only the three critical P4 blocks. A zero-violation full-board DRC is therefore not claimed.

## Reproduction

Start from the committed unrouted B9 board:

```powershell
& 'C:\Program Files\KiCad\10.0\bin\python.exe' `
  hardware\Pajoniiir-M1\tools\route_core_feasibility_b10.py `
  --board <b9-board.kicad_pcb> `
  --output <b10-board.kicad_pcb> `
  --report <b10-report.json>
```

Generate a DRC JSON and validate the live B10 state:

```powershell
kicad-cli pcb drc --format json --output <b10-drc.json> `
  hardware\Pajoniiir-M1\Pajoniiir-M1.kicad_pcb

& 'C:\Program Files\KiCad\10.0\bin\python.exe' `
  hardware\Pajoniiir-M1\tools\validate_core_routing_b10.py `
  --board hardware\Pajoniiir-M1\Pajoniiir-M1.kicad_pcb `
  --project hardware\Pajoniiir-M1\Pajoniiir-M1.kicad_pro `
  --report hardware\Pajoniiir-M1\m1_prelayout_b10_core_routes.json `
  --drc <b10-drc.json>
```

The validator fails on placement or metric drift, unapproved routed nets, crystal vias, incorrect QSPI transitions, undersized B10 vias, missing power trunks, any B10 route-geometry DRC violation, zones or `Edge.Cuts`.

## Boundary and next pass

B10 proves only the routed core subset. It does not authorize a production outline, placement freeze, planes, Gerbers or an EVT order. C60 and the other local grounds await the plane/stitching pass.

The next pass should place U4 at a candidate outer edge, preserve its all-layer antenna keepout and prove the four-bit SDIO route to U1. That pass should also correct U8's 0.20 mm thermal-via drill conflict and begin the complete P4 power/GND escape.

## Source guidance

- [Espressif ESP32-P4 PCB Layout Design](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32p4/pcb-layout-design-esp32p4.html)
- [Espressif ESP32-P4 Schematic Checklist](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32p4/schematic-checklist-esp32p4.html)
- [Texas Instruments TLV62569 datasheet](https://www.ti.com/lit/ds/symlink/tlv62569.pdf)
