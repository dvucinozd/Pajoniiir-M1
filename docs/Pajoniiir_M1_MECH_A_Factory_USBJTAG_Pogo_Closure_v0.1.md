# Pajoniiir-M1 — M1-MECH-A Factory USB/JTAG Pogo Closure v0.1

**Datum:** 2026-09-03  
**Revision:** M1-MECH-A7  
**Status:** J9 mechanical gate CLOSED  
**Authority:** `hardware/Pajoniiir-M1/mechanical_gates.json`

---

## Decision

J9 is a custom production-fixture interface, not a user connector and not an assembly part.

Locked footprint:

~~~text
Pajoniiir-M1:Factory_Pogo_USBJTAG_1x05_P1.27_2Tooling
~~~

Geometry:

~~~text
5 electrical pads
pitch             1.27 mm
pad diameter      1.00 mm
pin 1             rectangular
alignment holes   2 x Ø1.20 mm NPTH
tooling geometry  asymmetric / rotation-keyed
courtyard         -5.35..+5.95 mm X, -3.35..+3.35 mm Y
~~~

Pin map:

~~~text
1  3V3_SYS VREF — SENSE ONLY
2  GND
3  USBJTAG_DM_SERVICE
4  USBJTAG_DP_SERVICE
5  CHIP_PU
~~~

The board is powered through the normal qualified 5 V input during factory test. The fixture must never source pin 1.

## Why custom 5-pad instead of forcing a generic USB cable footprint

The existing schematic intentionally carries five factory-service signals, including CHIP_PU and VREF sense. A dedicated pogo fixture preserves that architecture, avoids any accidental USB VBUS/back-power path, and gives production a keyed mechanical datum through two asymmetric tooling holes.

There is no populated connector, no enclosure aperture and no assembly BOM item.

## Closure result

J9 no longer blocks layout freeze as a mechanical sourcing/footprint gate.

Its exact PCB XY position is still chosen during layout together with fixture approach clearance, but that is ordinary placement work rather than missing mechanical definition.
