# Pajoniiir-M1

Purpose-built Rev A mainboard for the **Pajoniiir standalone dual-deck DJ system**.

This repository contains the live hierarchical KiCad design, electrical and firmware contracts, mechanical evidence, placement/routing screening contracts, local CAD libraries and fail-closed validation tools.

## Current status

**Electrical milestone:** M1-ELEC-B2

**Mechanical milestone:** M1-MECH-B5

**Pre-layout milestone:** M1-PRELAYOUT-B5

**Schematic structure:** PASS — 15/15 leaf sheets

**Native KiCad 9 ERC:** PASS — 0 unexplained errors, 0 excluded errors, 0 warnings in the latest B5 schematic run

**Manufacturing BOM parity:** PASS — 242 source / 242 exported, 15 DNP, 3 intentional blank footprints

**Mechanical B2/B3/B4 contracts:** PASS

**B4 panel-window contract:** PASS

**B5 placement skeleton:** PASS

**Final placement/routing freeze:** BLOCKED — 12 physical/EVT gates remain

**Gerber/EVT order:** NOT AUTHORIZED

The current human-readable snapshot is [Pajoniiir M1 Current Design Status B5](docs/Pajoniiir_M1_Current_Design_Status_B5.md).

## Architecture

```text
                         5 V LOCKING INPUT
                                |
                         TPS259474 eFuse
                                |
                         5V_PROTECTED
                                |
                    5 mOhm Kelvin system shunt
                       / INA238 measurement
                                |
                             5V_SYS
              +-----------------+------------------+
              |                                    |
          TPS62132                         USB VBUS switches
          3V3_SYS                          TPS25221 x2
              |                               |       |
      +-------+---------+                  USB0 HS  USB1 FS
      |       |         |                  storage   FLX4
      v       v         v
  ESP32-P4 ESP32-C6  PCM5102A
      |      SDIO      MAIN L/R
      |
      +-- MIPI DSI + shared I2C --> DSI506 5-inch module
      +-- SDMMC -----------------> microSD
```

The final product display is **EYOYO DSI506 / DYL0023, 5-inch, 800 x 480**. Touch and backlight are module-integrated and controlled through the shared display I2C bus. The former JC4880 4.3-inch ST7701S/GT911/MP3202 path is historical evidence only.

## Electrical baseline

- ESP32-P4NRW32X, target silicon v3.2 or newer approved revision
- 32 MB in-package PSRAM
- W25Q128JVPIQ 16 MB external QSPI flash
- ESP32-C6-WROOM-1-N4 over four-bit SDIO
- USB0 dedicated High-Speed storage host
- USB1 GPIO26/27 Full-Speed DDJ-FLX4 MIDI/UAC host
- independent TPS25221 VBUS switching, about 1.0 A USB0 and 1.6 A USB1 initial limits
- PCM5102APWR stereo MAIN output with deterministic XSMT boot mute
- native four-bit SDMMC microSD with TPS22918 power cycling
- P4 UART, P4 USB Serial/JTAG pogo and C6 recovery paths
- optional INA238 system power telemetry

## Final display contract

```text
Display           EYOYO DSI506 / DYL0023
Resolution        800 x 480 native landscape
Host connector    Amphenol SFW15R-2STE1LF
FFC               15 contacts, 1.0 mm, Type-B/reverse contact
Supply            3V3_DISPLAY_MODULE, up to 340 mA documented
DSI routing       clock + lane0 + lane1
Initial profile   lane0 active, 800 Mbps, RGB888, 27.777 MHz DPI
I2C               GPIO7 SDA / GPIO8 SCL, 100 kHz
Touch             0x38, FT5426/FT5x06-compatible
Panel controller  0x45, module power/backlight
```

GPIO3, GPIO4, GPIO5, GPIO6 and GPIO23 were released by the display migration and remain unassigned spare candidates.

## Mechanical baseline

The mainboard mounts directly to four physically confirmed M2.5 posts on the display.

```text
post pattern                   58 x 49 mm
usable thread depth            3.0 mm
Rev A screw baseline           M2.5 x 4.0 mm
mainboard seating plane        Z = 10.0 mm
mainboard rear surface         Z = 11.6 mm at 1.6 mm thickness
core board screening envelope  104 x 62 mm
enclosure screening envelope   128 x 84 x 30 mm
candidate wall thickness       2.0 mm
```

Wall assignment:

- top / `Y_NEG`: J2 USB0, J3 USB1, J4/J5 RCA
- left / `X_NEG`: J1 power
- right / `X_POS`: J7 microSD, SW1/SW2 and guarded DSI FFC corridor
- bottom / `Y_POS`: intentionally clear

The enclosure and core board dimensions are screening values. They are not production `Edge.Cuts`.

## Connector and footprint state

| RefDes | Production part | Footprint | Mechanical state |
|---|---|---|---|
| J1 | Switchcraft 722RAHLP | open | terminal-center and panel geometry required |
| J2/J3 | Amphenol 87520-1010ALF | locked | panel/cable envelope open |
| J4/J5 | Kycon KLPX-0848A-2-W-G / -R-G | locked | panel/cable envelope open |
| J6 | Amphenol SFW15R-2STE1LF | locked | FFC pin-1/bend/placement open |
| J7 | Molex 503398-1892 | locked | slot/access/clearance open |
| SW1/SW2 | B3U-3000P-B | locked | recessed tool-hole placement open |
| J9 | project-local factory pogo | closed, DNL | normal placement work only |

Only `J1`, `C3` and `C8` intentionally have blank footprints in the manufacturing source.

## PCB and routing state

`hardware/Pajoniiir-M1/Pajoniiir-M1.kicad_pcb` is intentionally an empty four-copper-layer shell. It contains no placed footprints, routes or `Edge.Cuts`.

The stackup is locked to JLCPCB `JLC04161H-7628`, 1.6 mm, 1 oz outer copper and 0.5 oz inner copper.

```text
F.Cu   components + critical USB/MIPI/QSPI/SDIO routing
In1.Cu continuous solid GND reference
In2.Cu power distribution + compatible low-speed routing
B.Cu   secondary components and low-speed routing
```

B5 locks routing topology and provides screening geometry:

- USB: 90 ohm differential; screening 0.2332 mm width / 0.15 mm gap
- MIPI: 100 ohm differential; screening 0.1722 mm width / 0.15 mm gap

These numbers are not production impedance locks. Exact JLCPCB calculator records, soldermask/model selection and matching KiCad rules are required before route freeze.

## Open layout blockers

The current 12 blocking gates are:

```text
C3_INPUT_BULK
C8_PROTECTED_BULK
J1_POWER_INPUT
SW1_RESET
SW2_BOOT
J2_USB0
J3_USB1
J4_RCA_L
J5_RCA_R
J_LCD_DISPLAY_FPC
J7_MICROSD
PCB_OUTLINE
```

Although most connector MPNs and footprints are locked, their gates stay open until absolute panel datums, cutouts, mating envelopes and local clearances are physically validated.

## Repository structure

```text
docs/                         engineering and status documents
hardware/Pajoniiir-M1/        KiCad project and machine contracts
  *.kicad_sch                 root plus 15 hierarchical sheets
  Pajoniiir-M1.kicad_pcb      empty four-layer pre-layout shell
  *.json                      electrical/mechanical/freeze authorities
  libraries/                  project symbols and footprints
  tools/                      migration and fail-closed validators
.github/workflows/            KiCad and mechanical CI
```

## Authority order

When sources disagree:

1. live `hardware/Pajoniiir-M1/*.kicad_sch`
2. `mechanical_gates.json`
3. B5 placement and routing JSON contracts
4. B4 connector source lock
5. B3 mainboard/enclosure screening contracts
6. final-display and DSI506 evidence/lock JSON files
7. [Engineering BOM v0.3](docs/Pajoniiir_Mainboard_BOM_v0.3.md)
8. [Global GPIO allocation](docs/Pajoniiir_Global_GPIO_Allocation_v0.1.md)
9. subsystem documents
10. explicitly superseded A/JC4880 documents as historical evidence

## Current documents

### Status and release gates

- [Current Design Status B5](docs/Pajoniiir_M1_Current_Design_Status_B5.md)
- [Schematic Audit](docs/Pajoniiir_M1_Schematic_Audit_v0.1.md)
- [Schematic Readiness Review](docs/Pajoniiir_RevA_Schematic_Readiness_Review_v0.1.md)
- [Manufacturing Output Contract](docs/Pajoniiir_Manufacturing_Output_Contract_v0.1.md)
- [Mechanical and Sourcing Gates](docs/Pajoniiir_M1_Mechanical_Sourcing_Gates_v0.1.md)
- [PCB Placement and Routing Constraints](docs/Pajoniiir_M1_PCB_Layout_Constraints_v0.1.md)

### Electrical contracts

- [Engineering BOM v0.3](docs/Pajoniiir_Mainboard_BOM_v0.3.md)
- [Global GPIO Allocation](docs/Pajoniiir_Global_GPIO_Allocation_v0.1.md)
- [Hardware/Firmware Contract](docs/Pajoniiir_M1_Hardware_Firmware_Contract_v0.1.md)
- [5-inch DSI Interface Migration](docs/Pajoniiir_M1_ELEC_B0_5in_DSI_Interface_Migration_v0.1.md)
- [15-pin DSI Connector Lock](docs/Pajoniiir_M1_ELEC_B1_DSI15_Connector_Lock_v0.1.md)
- [Final 5-inch Display Baseline](docs/Pajoniiir_M1_MECH_B0_Final_5in_DSI_Display_Baseline_v0.1.md)

### Historical and subsystem design records

The original architecture, schematic plan, JC4880 display/backlight, GT911 and M1-MECH-A documents remain in `docs/` as design provenance. Their old display, enclosure and pre-capture status statements do not override the current B5 authorities.

## Validation

From the repository root:

```bash
python hardware/Pajoniiir-M1/tools/validate_schematic_structure.py
python hardware/Pajoniiir-M1/tools/validate_mechanical_authority.py
python hardware/Pajoniiir-M1/tools/validate_b4_panel_windows.py
python hardware/Pajoniiir-M1/tools/validate_b5_placement_skeleton.py
python hardware/Pajoniiir-M1/tools/report_mech_gate_snapshot.py
```

Native KiCad 9 CI separately loads every schematic, exports and cross-checks the manufacturing BOM, exports the hierarchy netlist/PDF and enforces ERC cleanliness.

Final placement, routing, Gerbers and EVT ordering remain blocked until every `blocks_layout_freeze` gate is closed and the production impedance geometry is recorded.
