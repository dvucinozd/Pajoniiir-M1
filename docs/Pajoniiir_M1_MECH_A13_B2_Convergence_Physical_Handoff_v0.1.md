# Pajoniiir-M1 — M1-MECH-A13 B2 Convergence & Physical Handoff v0.1

**Date:** 2026-09-04
**Milestone:** M1-MECH-A13
**Result:** REPO/SOFTWARE CLOSURE PASS — production layout freeze remains intentionally blocked

## Purpose

M1-ELEC-B2 changed the final product from the legacy JC4880/Guition 4.3-inch display architecture to the bench-proven EYOYO DSI506 / DYL0023 5-inch module. This checkpoint converges every active mechanical machine contract onto that decision without fabricating dimensions that require physical evidence.

## Current mechanical authority

- Display: EYOYO DSI506 / DYL0023, 5-inch, 800×480.
- Preliminary rear PCB evidence: 121.109 × 77.193 mm.
- Visible holes: 8; outer four image-derived centers ~111.109 × 67.930 mm, ~Ø2.5 mm.
- Host connector: J6 Amphenol SFW15R-2STE1LF, 15P, 1.0 mm, TOP contact, right-angle side-entry SMT ZIF, 2.7 mm housing height.
- Old JC4880 geometry: preserved under `legacy_guition_display_reference`; not active authority.
- Old 121.008 × 73.408 × 30 mm enclosure: rejected for DSI506.
- Old 108 × 65.06 mm mainboard feasibility rectangle and old Z-stack: superseded; no Edge.Cuts authority.

## Active blockers

| Gate | State | Closure class |
|---|---|---|
| `C3_INPUT_BULK` | OPEN | physical/EVT/new-enclosure evidence |
| `C8_PROTECTED_BULK` | OPEN | physical/EVT/new-enclosure evidence |
| `J1_POWER_INPUT` | OPEN | physical/EVT/new-enclosure evidence |
| `SW1_RESET` | OPEN | physical/EVT/new-enclosure evidence |
| `SW2_BOOT` | OPEN | physical/EVT/new-enclosure evidence |
| `J2_USB0` | OPEN | physical/EVT/new-enclosure evidence |
| `J3_USB1` | OPEN | physical/EVT/new-enclosure evidence |
| `J4_RCA_L` | OPEN | physical/EVT/new-enclosure evidence |
| `J5_RCA_R` | OPEN | physical/EVT/new-enclosure evidence |
| `J_LCD_DISPLAY_FPC` | OPEN | physical/EVT/new-enclosure evidence |
| `J7_MICROSD` | OPEN | physical/EVT/new-enclosure evidence |
| `PCB_OUTLINE` | OPEN | physical/EVT/new-enclosure evidence |

**Total: 12.** This is the correct hard boundary without a physical/CAD/EVT evidence package.

## Fail-closed policy

The repository must reject any attempt to set layout freeze true, add final Edge.Cuts, reactivate the old display/backlight mechanical model, or treat the old enclosure/Z-stack as production authority while these blockers remain.

## Next evidence order

DSI506 physical CAD/caliper + FFC orientation → new enclosure/boss/wall datums → user connector absolute datums and mated envelopes → PCB Z/standoffs and final outline → C3/C8 EVT packages → exact impedance width/spacing → placement/routing freeze.
