# Pajoniiir Mainboard — Engineering BOM v0.3

**Project:** Pajoniiir-M1 Rev A

**Updated:** 2026-09-04

**Baseline:** M1-ELEC-B2 / M1-MECH-B5

**Status:** current engineering-intent BOM companion to the live KiCad hierarchy

This document records current component intent and unresolved production choices. It is not a manufacturing BOM. The manufacturing candidate must be exported from `hardware/Pajoniiir-M1/Pajoniiir-M1.kicad_sch` and checked with `validate_manufacturing_outputs.py`.

## Current source baseline

| Metric | Count |
|---|---:|
| Unique `in_bom=yes` RefDes | 242 |
| DNP RefDes | 15 |
| Intentional blank footprints | 3 |
| Instantiated RefDes including DNL service items | 245 |

Intentional blank footprints are `C3`, `C8` and `J1`. Any additional blank footprint is a validation failure.

Current DNP set:

```text
C24 C72 C76 C77 C78 C79 C80 C106 C107 C108 C109 R70 R74 R99 R100
```

## System baseline

- Main compute: ESP32-P4NRW32X, production target silicon v3.2 or newer approved revision
- Firmware storage: W25Q128JVPIQ, 16 MB external QSPI flash
- Wi-Fi: ESP32-C6-WROOM-1-N4 over four-bit SDIO
- MAIN audio: PCM5102APWR stereo DAC
- Display: EYOYO DSI506 / DYL0023, 5-inch 800 x 480 DSI module
- Touch/backlight: module-integrated, controlled over shared display I2C
- Storage: USB0 High-Speed host plus native four-bit microSD
- Controller/audio host: USB1 Full-Speed DDJ-FLX4 MIDI and four-channel USB Audio
- CUE/PFL: DDJ-FLX4 USB Audio/headphone path

The former ST7701S/GT911/MP3202 bare-panel path and optional 3.5 mm line output are not part of the active Rev A BOM.

## Critical ICs and modules

| RefDes | Qty | Function | MPN/value | Footprint | State |
|---|---:|---|---|---|---|
| U1 | 1 | Main MCU + 32 MB PSRAM | ESP32-P4NRW32X | `Pajoniiir-M1:ESP32-P4` | locked for schematic; verify production revision/lot |
| U2 | 1 | 16 MB QSPI flash | W25Q128JVPIQ | `Package_SON:WSON-8-1EP_6x5mm_P1.27mm_EP3.4x4.3mm` | captured |
| U3 | 1 | P4 VDD_HP regulator | TLV62569DRLR | `Package_TO_SOT_SMD:SOT-563` | captured |
| U4 | 1 | Wi-Fi coprocessor | ESP32-C6-WROOM-1-N4 | `Pajoniiir-M1:ESP32-C6-WROOM-1` | captured; RF placement still required |
| U5 | 1 | MAIN stereo DAC | PCM5102APWR | `Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm` | captured |
| U6/U12 | 2 | USB0/USB1 VBUS switches | TPS25221DRVR | `Package_SON:WSON-6-1EP_2x2mm_P0.65mm_EP1x1.6mm` | captured |
| U7 | 1 | Input eFuse | TPS259474ARPWR | `Pajoniiir-M1:Texas_RPW0010A_VQFN-HR-10_2x2mm` | land pattern locked |
| U8 | 1 | 3.3 V / 3 A system buck | TPS62132RGTR | `Package_DFN_QFN:VQFN-16-1EP_3x3mm_P0.5mm_EP1.68x1.68mm_ThermalVias` | captured |
| U13 | 1 | microSD load switch | TPS22918DBVR | `Package_TO_SOT_SMD:SOT-23-6` | captured |
| U14 | 1 | System power monitor | INA238AIDGSR | `Package_SO:VSSOP-10_3x3mm_P0.5mm` | captured for EVT/DVT telemetry |

## Power and monitoring

Input path:

```text
J1 -> D1/input capacitance -> U7 TPS259474A -> 5V_PROTECTED
   -> R120 5 mOhm Kelvin shunt -> 5V_SYS
```

| RefDes | Function | Value/MPN | Footprint/state |
|---|---|---|---|
| J1 | Locking 5 V input | Switchcraft 722RAHLP; S760KHZ mating plug | MPN locked; footprint intentionally blank |
| D1 | Input TVS | SMBJ6.0CA-TR | `Diode_SMD:D_SMB`, locked |
| C3 | Input bulk | 330 uF tuning baseline | exact MPN/package blocked by EVT |
| C8 | Protected-rail bulk | 330 uF tuning baseline | exact MPN/package blocked by EVT |
| U7 | eFuse | TPS259474ARPWR | project HotRod RPW0010A footprint locked |
| R120 | System current shunt | WSK25125L000FEA, 5 mOhm, 1%, 1 W, four-terminal | Vishay WSK2512 Kelvin footprint |
| U14 | Current/voltage monitor | INA238AIDGSR, address 0x40 | captured |
| U8 | 3.3 V buck | TPS62132RGTR | captured |
| L2 | 3.3 V buck inductor | XGL4030-222MEC, 2.2 uH | `Inductor_SMD:L_Coilcraft_XxL4030` |

Initial eFuse targets remain UVLO about 4.42 V, OVLO about 5.70 V and current limit about 4.45 A typical. C3/C8 require startup, inrush, transient, ESR, ripple-current and physical-envelope evidence before production lock.

## P4, flash and clock

| RefDes | Function | Value/MPN |
|---|---|---|
| U1 | ESP32-P4 | ESP32-P4NRW32X |
| U2 | QSPI flash | W25Q128JVPIQ |
| Y1 | Main crystal | ECS-400-10-37B2-CKY-TR, 40 MHz, +/-10 ppm |
| U3 | P4 core regulator | TLV62569DRLR |
| R27/R28/C42 | P4 v3.x feedback network | 499 k / 499 k / 22 pF |
| R24 | DSI_REXT | 4.02 k, 1% |

P4 physical package pin 54 is `VDD_HP_1`; it must not be confused with GPIO54. M1 requires a separate v3.x firmware target and must not use a pre-v3 binary.

## C6 Wi-Fi

| Item | Baseline |
|---|---|
| Module | ESP32-C6-WROOM-1-N4 |
| Power | `3V3_C6`, 100 nF + 10 uF + 22 uF |
| Reset | P4 GPIO54 through 0 ohm to C6 EN, 10 k pull-up + 1 uF |
| SDIO | P4 GPIO14..19, four-bit bus |
| Pull-ups | 51.1 k on CMD and D0..D3 |
| Series | 22 ohm clock; 0 ohm CMD/data tuning |

The module antenna requires an edge placement and all-layer keepout. WROOM-1U remains a fallback only if enclosure/RF validation requires an external antenna.

## USB

| RefDes | Function | MPN/value | Footprint/state |
|---|---|---|---|
| U6 | USB0 VBUS switch | TPS25221DRVR, 54.9 k RILIM, about 1.0 A | captured |
| U12 | USB1 VBUS switch | TPS25221DRVR, 34.8 k RILIM, about 1.6 A initial | captured |
| D2/D3 | USB data ESD | TPD2EUSB30ADRTR | `Package_TO_SOT_SMD:Texas_DRT-3` |
| J2/J3 | USB 2.0 Type-A host | Amphenol 87520-1010ALF | project footprint locked |

USB0 uses the dedicated P4 High-Speed PHY with 0 ohm inline tuning. USB1 uses GPIO26/27 Full-Speed with 22 ohm source series. GPIO24/25 remain reserved for P4 USB Serial/JTAG service.

Connector panel centers, cutouts, insertion clearance and mated cable envelopes remain open mechanical gates.

## MAIN audio

| RefDes | Function | MPN/value | Footprint/state |
|---|---|---|---|
| U5 | Stereo DAC | PCM5102APWR | TSSOP-20 |
| J4 | MAIN L | Kycon KLPX-0848A-2-W-G | project RCA footprint locked |
| J5 | MAIN R | Kycon KLPX-0848A-2-R-G | project RCA footprint locked |
| R80/C91 | Left output filter | 470 ohm / 2.2 nF C0G | captured |
| R81/C92 | Right output filter | 470 ohm / 2.2 nF C0G | captured |

GPIO50 is BCLK, GPIO51 DATA, GPIO52 LRCK and GPIO49 XSMT. The DAC boots muted. The retired 3.5 mm line-output connector has no Rev A footprint.

## Display module

| RefDes | Function | MPN/value | Footprint/state |
|---|---|---|---|
| J6 | 15-pin DSI host connector | Amphenol SFW15R-2STE1LF | project footprint locked and instantiated |
| FB3 | Display module power isolation | 0 ohm / ferrite option | 0603 |
| C93/C94 | Local display supply | 100 nF / 10 uF | captured |
| R82..R87 | Six inline DSI tuning links | 0 ohm | 0201 |
| R95/R96 | Display I2C series | 22 ohm | 0402 |
| R97/R98 | Display I2C pull-ups | 4.7 k | 0603 |
| R99/R100 | Parallel I2C pull-up options | 4.7 k DNP | 0603 |

J6 pin map:

```text
1 GND       2 DSI_D1_N   3 DSI_D1_P   4 GND
5 DSI_CLK_N 6 DSI_CLK_P  7 GND        8 DSI_D0_N
9 DSI_D0_P 10 GND       11 I2C_SCL   12 I2C_SDA
13 GND     14 3V3       15 3V3
```

The remaining display gate is physical: actual cable pin-1 continuity, FFC bend/removal keepout and absolute J6 placement. There is no discrete MP3202 backlight block or GT911 reset/interrupt network in the active BOM.

## microSD

| RefDes | Function | MPN/value | Footprint/state |
|---|---|---|---|
| U13 | Card power switch | TPS22918DBVR | SOT-23-6 |
| J7 | Push-push microSD socket | Molex 503398-1892 | project footprint locked |
| C103/R105 | CT/QOD | 470 pF / 100 ohm | captured |
| R109 | SD clock series | 22 ohm | captured |
| R112..R116 | Bus pull-ups | 10 k to switched `3V3_SD` | captured |

The panel slot, card insertion/ejection/finger envelope, lower-right screw clearance and FFC coexistence remain open.

## Recovery and service

- SW1/SW2: B3U-3000P-B with exact standard KiCad footprint; panel tool-hole placement remains open.
- J8/J10: P4/C6 Tag-Connect pads, DNL.
- J9: project-local 1x05 USB Serial/JTAG factory pogo, DNL, closed sourcing/footprint gate.
- Factory fixtures must sense VREF only and must power the board through the qualified 5 V input path.

## Production choices still open

The following are not production BOM locks:

1. J1 exact land pattern
2. C3 and C8 exact capacitance technology, MPN and footprint
3. final mounting-hole diameter and screw head/washer hardware
4. panel cutouts and absolute connector centers
5. DSI FFC bend/orientation and absolute J6 location
6. final PCB side wings/notches and `Edge.Cuts`
7. exact 90 ohm USB and 100 ohm MIPI width/spacing

Use `mechanical_gates.json` for the complete closure evidence and current layout-freeze state.
