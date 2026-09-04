# Pajoniiir-M1 — Schematic Audit v0.2

**Updated:** 2026-09-04

**Electrical milestone:** M1-ELEC-B2

**Mechanical context:** M1-MECH-B5

**Status:** electrical capture and KiCad 9 validation pass; final PCB placement/routing remains blocked

## Scope

This audit covers the root KiCad schematic and all 15 leaf sheets under `hardware/Pajoniiir-M1/`.

```text
01_POWER_INPUT
02_POWER_3V3
03_P4_CORE
04_P4_FLASH_CLOCK_RESET
05_C6_WIFI
06_USB_POWER
07_USB0_STORAGE
08_USB1_FLX4
09_AUDIO_PCM5102A
10_DISPLAY_MIPI
11_TOUCH_GT911
12_MICROSD
13_DEBUG_SERVICE
14_TEST_MONITORING
15_DNP_OPTIONS
```

`11_TOUCH_GT911` and `15_DNP_OPTIONS` intentionally contain no instantiated symbols after the DSI506 migration. Their presence preserves the hierarchy and historical sheet roles.

## Current verdict

| Check | Result |
|---|---|
| 15-sheet structural contract | PASS |
| Unique RefDes/unit contract | PASS |
| Root/child hierarchical pin name and shape equivalence | PASS |
| Critical 5 V/shunt topology | PASS |
| Final DSI506 connector contract | PASS |
| KiCad 9 load of root and 15 leaves | PASS |
| Native KiCad 9 ERC | 0 unexplained errors, 0 excluded errors, 0 warnings |
| Manufacturing BOM parity | 242 source / 242 export, 15 DNP, 3 blank gates, PASS |
| Final PCB placement/routing freeze | BLOCKED |

The `.kicad_pro` file still contains six UUID-scoped exclusion records from the retired JC4880 connector gate. Current KiCad 9 ERC reports zero excluded errors, so those records are inactive configuration history rather than current violations.

## Captured electrical architecture

### Power

```text
J1 -> D1 -> U7 TPS259474A -> 5V_PROTECTED
   -> R120 5 mOhm Kelvin shunt -> 5V_SYS
```

`5V_SYS` supplies the TPS62132 3.3 V system regulator and independent TPS25221 USB VBUS paths. INA238 measures across the system shunt. J1, C3 and C8 remain intentional blank-footprint production gates.

### ESP32-P4

U1 is ESP32-P4NRW32X with a project-local KiCad 9 symbol/footprint derived from current Espressif data. Both symbol units are instantiated. The P4 v3.x power model, physical pin 54 `VDD_HP_1`, TLV62569 core regulator, 499 k/499 k/22 pF feedback network, DSI_REXT, MIPI LDO and USB PHY supplies are captured.

### Flash, clock and recovery

W25Q128JVPIQ external flash, 40 MHz ECS crystal, boot/reset straps, P4 UART0, P4 USB Serial/JTAG pogo and C6 recovery paths are captured. SW1/SW2 use B3U-3000P-B footprints but remain open for enclosure tool-hole placement.

### ESP32-C6

ESP32-C6-WROOM-1-N4 is connected over four-bit SDIO with external pull-ups and series tuning. GPIO54 controls C6 reset/EN. RF antenna placement and final enclosure performance remain PCB/EVT work.

### USB

USB0 uses the dedicated P4 High-Speed PHY, TPD2EUSB30A and Amphenol 87520-1010ALF. USB1 uses GPIO26/27 Full-Speed, 22 ohm source series, TPD2EUSB30A and the same connector. Each port has an independent TPS25221 VBUS switch and EN/FAULT path.

J2/J3 MPNs and footprints are locked. Their gates remain open only for final panel/cutout/mated-cable geometry.

### MAIN audio

PCM5102APWR uses GPIO50 BCLK, GPIO51 DATA, GPIO52 LRCK and GPIO49 XSMT. The outputs use 470 ohm plus 2.2 nF filters into Kycon white/red RCA connectors. The former 3.5 mm line output was removed from Rev A.

### Final display

The active design is EYOYO DSI506 / DYL0023, 5-inch, 800 x 480. J6 is Amphenol SFW15R-2STE1LF with a locked project footprint.

Captured interface:

```text
clock + DSI lane0 + DSI lane1
GPIO7 DISPLAY_I2C_SDA
GPIO8 DISPLAY_I2C_SCL
3V3_DISPLAY_MODULE on pins 14/15
```

The initial accepted firmware profile uses one lane at 800 Mbps, RGB888 and 27.777 MHz DPI. Touch is FT5426/FT5x06-compatible at 0x38 and panel power/backlight is controlled by the module device at 0x45.

There is no active MP3202 backlight boost, GT911 reset/interrupt network, LCD reset/TE or GPIO23 external PWM path. GPIO3/4/5/6/23 are released and unassigned.

The remaining J6 gate is physical: FFC pin-1 continuity, U-bend/insertion/removal keepout and absolute placement.

### microSD

The four-bit SDMMC bus, GPIO45-controlled TPS22918 supply and optional GPIO46 card detect are captured. J7 is Molex 503398-1892 with a locked footprint. Panel slot/access and local FFC/screw clearance remain open.

## Source and manufacturing inventory

Current source-derived counts:

```text
in_bom=yes      242
DNP              15
blank footprints  3: C3, C8, J1
DNL service       J8, J9, J10
```

Exact B4 footprints are present for J2/J3 USB, J4/J5 RCA, J7 microSD and SW1/SW2. J6 uses the B2 display connector footprint.

Historical 269/16/10 and run #76 270/17/12 figures predate the final display migration and B4 footprint locks. They are not current acceptance numbers.

## Structural validator coverage

`validate_schematic_structure.py` checks:

- balanced KiCad S-expressions and expected hierarchy
- bidirectional child-label/root-pin name and shape equivalence
- duplicate RefDes and duplicate RefDes/unit instances
- U1 two-unit geometry and pin partitioning
- prohibited ESP32-S3/ES8311/MAX485/NS4150 legacy blocks
- exact project eFuse and DSI506 connector contracts
- `5V_PROTECTED -> R120 -> 5V_SYS` topology
- blank-footprint allowlist derived from `mechanical_gates.json`
- B2 display authority and fail-closed mechanical/PCB state
- PCB copper-layer count and absence of `Edge.Cuts` while the outline gate is open

Native KiCad ERC and downstream manufacturing export remain separate CI checks.

## Remaining release boundary

Electrical capture is complete. The 12 remaining blockers are physical/EVT/layout gates:

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

Production placement/routing additionally requires exact 90 ohm USB and 100 ohm MIPI width/gap values for JLCPCB JLC04161H-7628.

## Go / no-go

- Schematic capture: **PASS / complete**
- Structural and manufacturing-source validation: **PASS**
- Exploratory placement using B5 screening anchors: **allowed**
- Final component placement: **blocked**
- Final USB/MIPI routing: **blocked**
- Gerbers and EVT PCB order: **blocked**

The next work should close J1 geometry, DSI FFC continuity/bend, display obstruction mapping, final enclosure/panel datums, mounting hardware, `Edge.Cuts`, C3/C8 EVT selection and production impedance rules.
