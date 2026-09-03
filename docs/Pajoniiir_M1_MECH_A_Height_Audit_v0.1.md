# Pajoniiir-M1 — M1-MECH-A Height Audit v0.1

**Datum:** 2026-09-03  
**Status:** Critical fixed central parts PASS geometry screen; production height limit not locked  
**Authority:** `hardware/Pajoniiir-M1/mech_a.json`

---

## Basis

Candidate M1 Z-stack provides **6.5 mm gross** space from PCB front/component-side surface to the back of the legacy display/module reference.

That 6.5 mm is not a manufacturing clearance specification.

## Verified critical fixed parts

| RefDes | Part | Maximum physical height used | Gross remaining space | Result |
|---|---|---:|---:|---|
| U1 | ESP32-P4NRW32X, QFN104 | 0.90 mm | 5.60 mm | PASS_GEOMETRY_SCREEN |
| U4 | ESP32-C6-WROOM-1-N4 | 3.25 mm | 3.25 mm | PASS_GEOMETRY_SCREEN |
| L1/L2 | Coilcraft XGL4030-222MEC | 3.10 mm | 3.40 mm | PASS_GEOMETRY_SCREEN |
| L3 | Coilcraft XGL4030-103MEC | 3.10 mm | 3.40 mm | PASS_GEOMETRY_SCREEN |

Sources:

- Espressif ESP32-P4 Series Datasheet, QFN104 A total thickness max 0.9 mm
- Espressif ESP32-C6-WROOM-1 Datasheet, 3.1 +/- 0.15 mm module height
- Coilcraft XGL4030 dimensions, Cmax 3.1 mm

## Interpretation

The fixed compute/RF/power core does not presently force a deeper enclosure. The remaining Z risks are the components whose MPN/mechanics are already intentionally open.

## Open height gates

- C3/C8: exact bulk capacitor package/height
- D1: final TVS package
- J1/J2/J3/J4/J5/J6/J7: exact connector body and mating envelope
- SW1/SW2: actuator/body height and access method
- J_LCD: connector mating height + FPC/panel stack

## Freeze rule

A production maximum component height may only be added after physical safety clearance and tolerance stack are defined. Until then, `production_allowable_component_height_mm` must remain null.
