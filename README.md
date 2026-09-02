# Pajoniiir-M1

Purpose-built Rev A mainboard for the **Pajoniiir standalone dual-deck DJ system**.

This repository contains the hardware architecture, engineering BOM, subsystem electrical designs and the active hierarchical KiCad Rev A schematic capture.

---

## Current status

**M1-SCH-A component capture:** SUBSTANTIALLY COMPLETE  
**Structural schematic audit:** PASS  
**Native KiCad ERC:** PENDING  
**GO for final PCB layout:** NOT YET

The electrical architecture is defined for:

- ESP32-P4 v3.x main MCU
- 32 MB in-package PSRAM
- 16 MB external QSPI flash
- ESP32-C6 Wi-Fi coprocessor via 4-bit SDIO
- USB0 High-Speed Rekordbox storage host
- USB1 Full-Speed DDJ-FLX4 MIDI + 4-channel USB Audio host
- independent protected USB0/USB1 VBUS power
- PCM5102A stereo MAIN output
- ST7701S 4.3" MIPI-DSI display
- GT911 touch
- native microSD
- robust 5 V / 3.3 V power architecture
- P4/C6 recovery and factory programming
- optional system power telemetry

The largest remaining layout gate is the exact physical LCD/touch FPC/panel assembly. Native KiCad Sync Sheet Pins + ERC and final exact-footprint/mechanical closure are still required before M1-SCH-A sign-off.

---

# Architecture

~~~text
                           5V INPUT
                              |
                       TPS259474 eFuse
                              |
                       5V_PROTECTED
                              |
                     5 mΩ Kelvin shunt
                    / INA238 measurement
                              |
                           5V_SYS
          +-------------------+-------------------+
          |                   |                   |
          v                   v                   v
     TPS62132             USB power           MP3202
     3V3_SYS              switches            backlight
          |                   |                   |
          |            +------+-----+             |
          |            |            |             |
          |         USB0 HS       USB1 FS          |
          |         storage       FLX4             |
          |                                      LEDA
          |
   +------+-----------------------------------------------+
   |                   |             |                    |
   v                   v             v                    v
ESP32-P4           ESP32-C6      PCM5102A              microSD
v3.x               SDIO/Wi-Fi    MAIN L/R              SDMMC
   |
   +-- 2-lane MIPI DSI --> ST7701S
   +-- I2C -------------> GT911
~~~

---

# Current authoritative documents

When sources disagree, use this order:

1. **actual `hardware/Pajoniiir-M1/*.kicad_sch` files** for captured connectivity and current RefDes
2. **docs/Pajoniiir_Mainboard_BOM_v0.2.md** for engineering component intent
3. **docs/Pajoniiir_Global_GPIO_Allocation_v0.1.md**
4. **docs/Pajoniiir_M1_Schematic_Audit_v0.1.md**
5. the subsystem leaf-design document
6. **docs/Pajoniiir_Mainboard_Schematic_Plan_v0.1.md**
7. older architecture/research documents

Pajoniiir_Mainboard_BOM_v0.1.md is superseded.

Pajoniiir_MIPI_DSI_Display_Backlight_Design_v0.1.md is superseded by v0.2.

---

# Hardware design documents

## System

- [Hardware architecture Rev A](docs/Pajoniiir_Mainboard_Hardware_Architecture_RevA.md)
- [Engineering BOM v0.2](docs/Pajoniiir_Mainboard_BOM_v0.2.md)
- [Global GPIO allocation v0.1](docs/Pajoniiir_Global_GPIO_Allocation_v0.1.md)
- [Schematic plan v0.1](docs/Pajoniiir_Mainboard_Schematic_Plan_v0.1.md)
- [Schematic readiness review v0.1](docs/Pajoniiir_RevA_Schematic_Readiness_Review_v0.1.md)
- [M1-SCH-A schematic audit v0.1](docs/Pajoniiir_M1_Schematic_Audit_v0.1.md)
- [DNP / option matrix v0.1](docs/Pajoniiir_DNP_Option_Matrix_v0.1.md)

## 01 — Input power

- [Power Input Design v0.1](docs/Pajoniiir_Power_Input_Design_v0.1.md)

Primary:

~~~text
TPS259474ARPWR
UVLO ≈ 4.42 V
OVLO ≈ 5.70 V
ILIM ≈ 4.45 A typ
~~~

## 02 — 3V3 system rail

- [3V3 System Rail Design v0.1](docs/Pajoniiir_3V3_System_Rail_Design_v0.1.md)

Primary:

~~~text
TPS62132RGTR
5 V -> 3.3 V
up to 3 A
~~~

## 03 — ESP32-P4 core

- [ESP32-P4 Core Design v0.1](docs/Pajoniiir_ESP32P4_Core_Design_v0.1.md)
- [ESP32-P4 v3.2 Silicon Selection v0.1](docs/Pajoniiir_ESP32P4_v3_2_Silicon_Selection_v0.1.md)

Primary:

**ESP32-P4NRW32X**

Target actual silicon:

**v3.2 or later approved revision**

Important:

- physical package pin 54 = VDD_HP_1
- v3.x DCDC feedback network required
- legacy v1.3 binary is not compatible with M1 v3.x

## 04 — Flash / clock / reset / boot

- [P4 Flash, Clock, Reset & Boot Design v0.1](docs/Pajoniiir_P4_Flash_Clock_Reset_Boot_Design_v0.1.md)

Primary:

~~~text
W25Q128JVPIQ
16 MB

ECS-400-10-37B2-CKY-TR
40 MHz
±10 ppm
15 pF + 15 pF initial load
~~~

## 05 — C6 Wi-Fi

- [C6 Wi-Fi / SDIO Design v0.1](docs/Pajoniiir_C6_WiFi_SDIO_Design_v0.1.md)

Primary:

**ESP32-C6-WROOM-1-N4**

~~~text
CLK GPIO18
CMD GPIO19
D0  GPIO14
D1  GPIO15
D2  GPIO16
D3  GPIO17
RST GPIO54
~~~

## 06 — USB power

- [Dual USB VBUS Power Design v0.2](docs/Pajoniiir_Dual_USB_VBUS_Power_Design_v0.2.md)

Primary:

~~~text
USB0: TPS25221DRVR
      ~1.0 A nominal initial

USB1: TPS25221DRVR
      ~1.6 A nominal initial
~~~

The earlier single-TPS2561 concept is not the Rev A baseline because its two channels share one RILIM.

## 07 — USB0 High-Speed storage

- [USB0 High-Speed Storage Design v0.1](docs/Pajoniiir_USB0_HS_Storage_Design_v0.1.md)

~~~text
P4 dedicated HS USB PHY
90 Ω differential
TPD2EUSB30ADRTR
USB-A host
~~~

## 08 — USB1 DDJ-FLX4

- [USB1 FLX4 Full-Speed Design v0.1](docs/Pajoniiir_USB1_FLX4_FS_Design_v0.1.md)

~~~text
GPIO26 DM
GPIO27 DP
22 Ω / 22 Ω
TPD2EUSB30ADRTR
USB-A host
~~~

GPIO24/25 remain reserved for P4 USB Serial/JTAG service.

## 09 — MAIN audio

- [PCM5102A Audio Design v0.1](docs/Pajoniiir_PCM5102A_Audio_Design_v0.1.md)

~~~text
GPIO50 BCLK
GPIO51 DATA
GPIO52 LRCK
GPIO49 XSMT

MAIN L/R:
470 Ω + 2.2 nF per channel
~~~

The DAC boots muted through XSMT.

## 10 — Display / backlight

- [MIPI DSI Display & Backlight Design v0.2](docs/Pajoniiir_MIPI_DSI_Display_Backlight_Design_v0.2.md)
- [JC4880 Display FPC & Backlight Forensics v0.1](docs/Pajoniiir_Display_FPC_Backlight_Forensics_v0.1.md)

Display:

~~~text
ST7701S
480 × 800
2-lane DSI
500 Mbps/lane
34 MHz DPI
RGB565
~~~

Backlight baseline reconstructed from original JC4880 schematic:

~~~text
MP3202
10 µH
SS14
3.9 Ω || 2.2 Ω sense
~74 mA nominal LED current
direct EN PWM
M1 target PWM = 1 kHz
~~~

Remaining hard gate:

**exact physical FPC/panel and resolution of the 30-contact MPN vs 32-pin schematic-symbol discrepancy.**

## 11 — Touch

- [GT911 Touch Design v0.1](docs/Pajoniiir_GT911_Touch_Design_v0.1.md)

~~~text
GPIO3 RESET
GPIO4 INT
GPIO7 SDA
GPIO8 SCL
address 0x5D
~~~

## 12 — microSD

- [microSD / SDMMC Design v0.1](docs/Pajoniiir_MicroSD_SDMMC_Design_v0.1.md)

~~~text
GPIO39 D0
GPIO40 D1
GPIO41 D2
GPIO42 D3
GPIO43 CLK
GPIO44 CMD
GPIO45 power enable
GPIO46 optional card detect
~~~

Card power:

**TPS22918DBVR**

## 13 — Debug / recovery

- [Debug, Recovery & Factory Service v0.1](docs/Pajoniiir_Debug_Recovery_Factory_Service_v0.1.md)

Recovery paths:

1. P4 UART0
2. P4 USB Serial/JTAG
3. C6 direct UART/BOOT
4. RESET/BOOT pogo access

## 14 — Test / monitoring

- [Test & Power Monitoring Design v0.1](docs/Pajoniiir_Test_Power_Monitoring_Design_v0.1.md)

EVT/DVT option:

~~~text
INA238AIDGSR
5 mΩ Kelvin shunt
I2C 0x40
GPIO53 ALERT optional
~~~

## 15 — DNP options

- [DNP / Option Matrix v0.1](docs/Pajoniiir_DNP_Option_Matrix_v0.1.md)

No legacy S3, ES8311, speaker amp, RS485, camera or battery-charger blocks are carried into M1 as speculative DNP circuitry.

---

# Global GPIO baseline

| GPIO | Function |
|---:|---|
| 3 | TOUCH_RST |
| 4 | TOUCH_INT |
| 5 | LCD_RST |
| 6 | LCD_TE optional |
| 7 | I2C SDA |
| 8 | I2C SCL |
| 14–17 | C6 SDIO D0–D3 |
| 18 | C6 SDIO CLK |
| 19 | C6 SDIO CMD |
| 20 | USB0_PWR_EN |
| 21 | USB0_FAULT_N |
| 22 | USB1_PWR_EN |
| 23 | LCD_BL_PWM |
| 24/25 | P4 USB Serial/JTAG |
| 26/27 | USB1 FS DM/DP |
| 32 | USB1_FAULT_N |
| 35 | BOOT |
| 36 | boot strap high |
| 37/38 | UART0 TX/RX |
| 39–42 | SDMMC D0–D3 |
| 43 | SDMMC CLK |
| 44 | SDMMC CMD |
| 45 | SD_PWR_EN |
| 46 | optional SD card detect |
| 49 | DAC_XSMT |
| 50 | DAC_BCLK |
| 51 | DAC_DATA |
| 52 | DAC_LRCK |
| 53 | optional power monitor ALERT |
| 54 | C6_RESET |

---

# Key component baseline

~~~text
ESP32-P4NRW32X
W25Q128JVPIQ
ECS-400-10-37B2-CKY-TR
TLV62569DRLR
ESP32-C6-WROOM-1-N4
PCM5102APWR
TPS259474ARPWR
TPS62132RGTR
TPS25221DRVR x2
TPS22918DBVR
MP3202DJ-LF-Z
TPD2EUSB30ADRTR x2
INA238AIDGSR optional
~~~

---

# Remaining pre-layout gates

## 1. LCD / FPC mechanics

Resolve:

- exact final panel MPN
- exact connector physical MPN
- 30-contact vs 32-symbol discrepancy
- pins 15/16/18/19
- FPC contact orientation
- mating height
- mechanical drawing

## 2. Final connector mechanics

Lock exact production MPNs for:

- 5 V input
- USB-A ×2
- RCA ×2
- microSD
- RESET / BOOT switches

These do not block electrical schematic capture.

---

# Next milestone

## M1-SCH-A sign-off

The real KiCad hierarchy now exists under:

~~~text
hardware/Pajoniiir-M1/
~~~

and all 15 planned leaf sheets have component-level capture.

Current sign-off gates:

- [x] hierarchy captured
- [x] structural child/root audit clean
- [x] duplicate RefDes audit clean
- [x] 5V_PROTECTED -> shunt -> 5V_SYS power path corrected
- [x] display/touch electrical capture
- [x] DNP/DNL policy captured
- [x] local structural validator committed
- [ ] native KiCad Sync Sheet Pins
- [ ] native KiCad ERC with zero unexplained errors
- [ ] final LCD/FPC physical definition
- [ ] exact external connector MPNs / footprints
- [ ] U7 HotRod RPW land pattern freeze
- [ ] L_BL and Kelvin shunt exact sourcing/footprints
- [ ] schematic PDF human review
- [ ] manufacturing BOM/netlist cross-check

Use:

~~~bash
python3 hardware/Pajoniiir-M1/tools/validate_schematic_structure.py
~~~

for the lightweight source-level structural check.

Only after **M1-SCH-A sign-off** should the project move into final PCB placement/routing.
