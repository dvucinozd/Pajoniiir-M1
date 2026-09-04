# Pajoniiir-M1 — M1-MECH-A Physical Evidence Boundary v0.2

**Date:** 2026-09-04
**Revision:** M1-MECH-A13 / post M1-ELEC-B2 convergence
**Status:** Repository-only mechanical convergence complete; layout freeze intentionally blocked by physical/EVT/new-enclosure evidence

## 1. Current final-display authority

The active final-product display is **EYOYO DSI506 / DYL0023, 5-inch 800×480**. The production host receptacle is **Amphenol SFW15R-2STE1LF**, 15 contacts, 1.0 mm pitch, TOP contact, right-angle/side-entry SMT ZIF. Its project footprint is drawing-verified and instantiated in `10_DISPLAY_MIPI`. The older 30-pin Guition/JC4880 FPC path is historical evidence only.

Preliminary dimensioned-image evidence for the final display rear PCB is **121.109 × 77.193 mm**, with eight visible mounting holes. The outer four image-derived centers imply approximately **111.109 × 67.930 mm** spacing and ~2.5 mm holes. These dimensions are sufficient to reject the old enclosure, but not sufficient for production CAD release without physical caliper data or official CAD.

## 2. Old enclosure decision is closed: REJECTED

The previous external enclosure was 121.008 × 73.408 mm with a 117.008 × 69.408 mm inner cavity. The final display rear PCB is larger than even the old external Y dimension. `final_display_module.json` therefore records `HARD_FAIL__ENCLOSURE_REDIMENSION_REQUIRED`.

Consequences:

- the old 108.00 × 65.06 mm mainboard feasibility rectangle is **not** final Edge.Cuts authority;
- the old ±51.3 × ±30.0 mounting candidate is **not** final M1 mounting authority;
- the old 6.5 mm / 6.0 mm front/rear gross Z-clearance screen is **not** a DSI506 production component-height limit;
- a new enclosure/mainboard datum set is mandatory.

## 3. Remaining layout blockers (12)

1. `C3_INPUT_BULK`
2. `C8_PROTECTED_BULK`
3. `J1_POWER_INPUT`
4. `SW1_RESET`
5. `SW2_BOOT`
6. `J2_USB0`
7. `J3_USB1`
8. `J4_RCA_L`
9. `J5_RCA_R`
10. `J_LCD_DISPLAY_FPC`
11. `J7_MICROSD`
12. `PCB_OUTLINE`

The blocker count is intentionally unchanged. B2 convergence removed stale assumptions; it did not invent enclosure measurements or EVT data.

## 4. What is already closed

- DSI506 identity and M3-derived signal/bring-up contract
- production J6 MPN/contact count/pitch/TOP-contact geometry
- drawing-verified J6 footprint and B2 schematic instantiation
- legacy 30-pin display electrical/backlight architecture removal
- D1 TVS production selection
- J9 factory USB/JTAG pogo fixture footprint
- optional legacy 3.5 mm line-out removal
- JLCPCB JLC04161H-7628 4-layer / 1.6 mm stackup

## 5. Physical/EVT package required to continue

1. DSI506 caliper/official CAD package: full XY/Z, all eight mounting-hole centers and hole diameters.
2. Actual FFC continuity/orientation check proving host pin 1 ↔ module pin 1 and conductor side with the selected TOP-contact receptacle.
3. FFC approach, insertion and minimum-bend keepout in the proposed enclosure.
4. New enclosure interior, wall, rib and boss datums in `M1_FRONT_CENTER`.
5. Exact connector cutouts and full mated plug/cable envelopes for power, USB, RCA, microSD and service buttons.
6. C3/C8 startup/inrush and worst-case USB-load transient sweep with ESR/ripple/current data.

## 6. Freeze rule

`layout_freeze_allowed` remains **false**. Production Edge.Cuts/routing freeze is allowed only after every `blocks_layout_freeze` gate is closed, the new DSI506-compatible enclosure/mainboard datums are authoritative, C3/C8 are converted from EVT variables to exact packages, and exact 90 Ω USB / 100 Ω MIPI width-spacing values are recorded for the locked JLC stackup.
