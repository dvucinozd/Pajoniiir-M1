# Pajoniiir-M1 — Current Design Status B5

**Project:** Pajoniiir-M1 Rev A

**Updated:** 2026-09-04

**Electrical milestone:** M1-ELEC-B2

**Mechanical milestone:** M1-MECH-B5

**Pre-layout milestone:** M1-PRELAYOUT-B5

**Status:** schematic complete and validated; placement/routing freeze blocked by 12 physical/EVT gates

This document is the human-readable current-state index. Machine-readable facts remain authoritative in the KiCad sources and JSON contracts listed below.

## Authority order

When sources disagree, use this order:

1. `hardware/Pajoniiir-M1/*.kicad_sch` for captured connectivity, RefDes, values and footprints
2. `hardware/Pajoniiir-M1/mechanical_gates.json` for gate state and freeze policy
3. `hardware/Pajoniiir-M1/m1_mech_b5_placement_skeleton.json` for B5 placement screening anchors
4. `hardware/Pajoniiir-M1/m1_prelayout_b5_routing_contract.json` for routing topology and impedance status
5. `hardware/Pajoniiir-M1/m1_mech_b4_connector_source_lock.json` for connector MPN and footprint decisions
6. `hardware/Pajoniiir-M1/m1_mech_b3_mainboard_io_envelope.json` and `m1_mech_b3_enclosure_candidate.json` for screening envelopes
7. `hardware/Pajoniiir-M1/final_display_module.json`, `display_connector_b1.json` and DSI506 evidence/lock files
8. `docs/Pajoniiir_Mainboard_BOM_v0.3.md` for engineering BOM interpretation
9. subsystem design documents
10. explicitly superseded JC4880/M1-MECH-A documents as historical evidence only

## Current electrical design

The 15-sheet KiCad hierarchy implements:

- ESP32-P4NRW32X, target silicon v3.2 or newer approved revision
- 32 MB in-package PSRAM and W25Q128JVPIQ 16 MB external QSPI flash
- ESP32-C6-WROOM-1-N4 over four-bit SDIO
- protected 5 V input through TPS259474A eFuse
- 5 mOhm Kelvin system shunt and INA238 monitoring
- TPS62132 3.3 V / 3 A system rail
- independent TPS25221 USB0 and USB1 VBUS switches
- USB0 High-Speed storage host and USB1 Full-Speed DDJ-FLX4 host
- PCM5102A stereo MAIN L/R output
- EYOYO DSI506 / DYL0023 5-inch 800 x 480 DSI display module
- native four-bit SDMMC microSD with switchable card power
- P4 UART, P4 USB Serial/JTAG pogo and C6 recovery paths

The retired `11_TOUCH_GT911` and `15_DNP_OPTIONS` leaf sheets intentionally contain no instantiated components. Touch and backlight are provided by the DSI506 module through the shared display I2C bus.

## Current source and CI baseline

The current hierarchy contains:

| Metric | Current value |
|---|---:|
| Unique `in_bom=yes` RefDes | 242 |
| DNP RefDes | 15 |
| Intentional blank-footprint BOM gates | 3 |
| Blank-footprint RefDes | `C3`, `C8`, `J1` |
| Instantiated RefDes including DNL service items | 245 |

The [KiCad 9 CI run for the B5 schematic state](https://github.com/dvucinozd/Pajoniiir-M1/actions/runs/33893027497), at commit `667fd01`, reported:

```text
all 16 schematic files load: PASS
manufacturing BOM parity: source=242 bom=242 dnp=15 blank_gates=3 PASS
native ERC: unexplained_errors=0 excluded_errors=0 warnings=0
```

The project file still carries six legacy UUID-scoped exclusion records from the retired JC4880 connector gate. They are not active violations in the current ERC report and must not be described as current excluded errors.

## Final display contract

The active display is **EYOYO DSI506 / DYL0023, 5-inch, 800 x 480**, using a 15-contact 1.0 mm FFC.

- Host connector: Amphenol `SFW15R-2STE1LF`, top-contact, right-angle SMT ZIF
- Supply: `3V3_DISPLAY_MODULE`, maximum documented module current 340 mA
- DSI routing requirement: clock plus lanes 0 and 1; the PCB is not routed yet
- Initial accepted firmware profile: one active lane at 800 Mbps, RGB888, 27.777 MHz DPI, native landscape
- I2C: GPIO7 SDA, GPIO8 SCL, 100 kHz
- Touch: FT5426/FT5x06-compatible device at `0x38`
- Panel power/backlight controller: `0x45`
- No dedicated touch reset/interrupt, panel reset/TE or external backlight PWM wires

GPIO3, GPIO4, GPIO5, GPIO6 and GPIO23 are released by this migration and remain unassigned spare candidates.

## Mechanical baseline

The custom mainboard mounts directly to the four inner threaded posts on the rear of the DSI506 module.

| Item | Locked/screening value |
|---|---|
| Mount thread | M2.5, physically confirmed |
| Post pattern | 58 x 49 mm |
| Usable thread depth | 3.0 mm |
| Rev A screw-length baseline | M2.5 x 4.0 mm |
| Mainboard seating plane | Z = 10.0 mm from front glass |
| Mainboard rear surface | Z = 11.6 mm for 1.6 mm PCB |
| Core mainboard screening envelope | 104 x 62 mm |
| Enclosure screening envelope | 128 x 84 x 30 mm |
| Candidate wall thickness | 2.0 mm |

The enclosure and 104 x 62 mm core rectangle are screening authorities. They are not production `Edge.Cuts`.

Wall assignment is locked for screening:

- `Y_NEG` top wall: J2 USB0, J3 USB1, J4 MAIN L RCA, J5 MAIN R RCA
- `X_NEG` left wall: J1 power input
- `X_POS` right wall: J7 microSD, SW1 RESET, SW2 BOOT and guarded DSI FFC corridor
- `Y_POS` bottom wall: clear for ventilation, retention and service margin

## Connector status

| RefDes | Production intent | Footprint status | Remaining gate class |
|---|---|---|---|
| J1 | Switchcraft 722RAHLP + S760KHZ plug | open | unambiguous terminal centers, left wing, panel and cable geometry |
| J2/J3 | Amphenol 87520-1010ALF | locked | final panel centers/cutouts and plug envelopes |
| J4 | Kycon KLPX-0848A-2-W-G | locked | final panel center and mated RCA envelope |
| J5 | Kycon KLPX-0848A-2-R-G | locked | final panel center and mated RCA envelope |
| J6 display | Amphenol SFW15R-2STE1LF | locked | FFC pin-1 continuity, bend/removal keepout and absolute placement |
| J7 | Molex 503398-1892 | locked | card slot, finger/ejection access, FFC and screw clearance |
| SW1/SW2 | B3U-3000P-B | locked | recessed tool-hole centers and local clearance |
| J9 | project-local 1x05 factory pogo | closed/DNL | normal placement work only |

The former optional 3.5 mm line output was removed from Rev A. Display connector J6 is unrelated to that retired audio connector; RefDes reuse occurred during the DSI506 migration.

## Placement and routing state

B5 proves a placement skeleton, not production placement.

- J2/J3/J4/J5 have screening anchors and checked courtyard spacing on the top wall.
- J7/SW1/SW2 remain unanchored until the right-side wing, card access and 60 x 15 mm FFC U-bend are solved together.
- J1 remains unanchored until its land pattern and left-side geometry are authoritative.
- The KiCad PCB file is intentionally an empty four-copper-layer shell with no footprints or `Edge.Cuts`.

The locked stackup is JLCPCB `JLC04161H-7628`, 1.6 mm, 1 oz outer copper and 0.5 oz inner copper.

Layer intent:

```text
F.Cu   primary components and critical routing
In1.Cu continuous solid GND reference
In2.Cu power distribution and compatible low-speed routing
B.Cu   secondary components and low-speed routing
```

Routing topology is locked. Production impedance geometry is not:

| Class | Target | Screening width/gap | Production state |
|---|---:|---:|---|
| USB0/USB1 | 90 ohm differential | 0.2332 / 0.15 mm | open |
| MIPI DSI | 100 ohm differential | 0.1722 / 0.15 mm | open |

The screening values may be used for channel budgeting only. The direct JLCPCB calculator record, soldermask/model choice and final KiCad rules are required before release routing.

## Open layout blockers

`layout_freeze_allowed` remains `false`. The 12 open blocking gates are:

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

Closed gates are D1 input TVS, the removed 3.5 mm output, J9 factory pogo and the fabrication stackup.

## Required order before layout freeze

1. Lock the J1 land pattern from unambiguous manufacturer geometry.
2. Prove DSI506 host-to-module pin-1 continuity and the physical FFC bend/removal envelope.
3. Capture the local rear-display obstruction map.
4. Lock enclosure walls, bosses, rear cover and user connector panel datums.
5. Lock screw head/washer choice and NPTH diameter.
6. Lock final side wings/notches and `Edge.Cuts`.
7. Select C3/C8 production parts from startup/inrush/transient EVT evidence.
8. Record exact JLCPCB 90 ohm and 100 ohm impedance geometry and apply it to KiCad rules.
9. Perform final placement, PCB DRC, power-copper review and manufacturing release review.

Gerbers and EVT PCB ordering remain blocked until these gates close.
