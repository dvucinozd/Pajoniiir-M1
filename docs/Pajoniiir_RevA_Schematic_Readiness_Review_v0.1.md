# Pajoniiir-M1 Rev A — Schematic Readiness Review v0.1

**Datum:** 2026-09-02  
**Ažurirano:** 2026-09-03  
**Repo:** dvucinozd/Pajoniiir-M1  
**Branch:** main  
**Status:** Post-capture readiness snapshot — KiCad 9.0.9 ERC PASS; mechanical/sourcing gates remain

---

# 1. Executive summary

Rev A electrical architecture has been captured in the real hierarchical KiCad project and the native KiCad 9.0.9 CI ERC baseline is clean: 0 unexplained errors, 6 approved J_LCD hard-gate exclusions and 0 warnings.

The design is no longer a copy of the JC4880 development board. It is a purpose-built Pajoniiir mainboard centered on:

- ESP32-P4 v3.x
- ESP32-C6-WROOM-1
- dual independent USB host power paths
- PCM5102A MAIN DAC
- ST7701S MIPI DSI display
- GT911 touch
- native microSD
- robust 5 V / 3.3 V power tree
- full recovery and test infrastructure

No known architectural blocker remains for drawing the power, P4, C6, USB, audio, touch, microSD, debug or monitoring sheets.

The only hard blockers before **PCB layout freeze** are final panel/FPC mechanics and a small set of final component/mechanical choices.

---

# 2. Authority order

If documents disagree, use this order:

1. **Pajoniiir_Mainboard_BOM_v0.2.md**
2. **Pajoniiir_Global_GPIO_Allocation_v0.1.md**
3. leaf block design document for the affected subsystem
4. **Pajoniiir_Mainboard_Schematic_Plan_v0.1.md**
5. older BOM/architecture notes
6. JC4880 development-board wiring only as historical reference

Pajoniiir_Mainboard_BOM_v0.1.md is superseded.

---

# 3. Completed design blocks

| Block | Document | Readiness |
|---|---|---|
| Architecture | Pajoniiir_Mainboard_Hardware_Architecture_RevA.md | READY |
| Display forensics | Pajoniiir_Display_FPC_Backlight_Forensics_v0.1.md | READY / source reconstruction |
| P4 silicon selection | Pajoniiir_ESP32P4_v3_2_Silicon_Selection_v0.1.md | READY |
| Consolidated BOM | Pajoniiir_Mainboard_BOM_v0.2.md | READY |
| Global GPIO | Pajoniiir_Global_GPIO_Allocation_v0.1.md | READY |
| Schematic hierarchy | Pajoniiir_Mainboard_Schematic_Plan_v0.1.md | READY |
| 01 Power input | Pajoniiir_Power_Input_Design_v0.1.md | READY |
| 02 3V3 system rail | Pajoniiir_3V3_System_Rail_Design_v0.1.md | READY |
| 03 P4 core | Pajoniiir_ESP32P4_Core_Design_v0.1.md | READY |
| 04 Flash/clock/reset/boot | Pajoniiir_P4_Flash_Clock_Reset_Boot_Design_v0.1.md | READY |
| 05 C6 Wi-Fi | Pajoniiir_C6_WiFi_SDIO_Design_v0.1.md | READY |
| 06 USB power | Pajoniiir_Dual_USB_VBUS_Power_Design_v0.2.md | READY |
| 07 USB0 HS | Pajoniiir_USB0_HS_Storage_Design_v0.1.md | READY |
| 08 USB1 FLX4 FS | Pajoniiir_USB1_FLX4_FS_Design_v0.1.md | READY |
| 09 PCM5102A | Pajoniiir_PCM5102A_Audio_Design_v0.1.md | READY |
| 10 MIPI display/backlight | Pajoniiir_MIPI_DSI_Display_Backlight_Design_v0.2.md | READY WITH FPC MECHANICAL GATE |
| 11 GT911 | Pajoniiir_GT911_Touch_Design_v0.1.md | READY WITH PANEL GATE |
| 12 microSD | Pajoniiir_MicroSD_SDMMC_Design_v0.1.md | READY |
| 13 Debug/service | Pajoniiir_Debug_Recovery_Factory_Service_v0.1.md | READY |
| 14 Test/monitoring | Pajoniiir_Test_Power_Monitoring_Design_v0.1.md | READY |
| 15 DNP options | Pajoniiir_DNP_Option_Matrix_v0.1.md | READY |

---

# 4. Locked core components

## Main compute

- ESP32-P4NRW32X — v3.x candidate
- W25Q128JVPIQ — 16 MB QSPI flash
- ECS-400-10-37B2-CKY-TR — 40 MHz crystal
- ESP32-C6-WROOM-1-N4 — Wi-Fi coprocessor

## Power

- TPS259474ARPWR — input eFuse
- TPS62132RGTR — 3.3 V / 3 A buck
- TLV62569DRLR — P4 VDD_HP DCDC
- TPS25221DRVR ×2 — USB0/USB1 independent VBUS switches
- TPS22918DBVR — microSD load switch
- MP3202DJ-LF-Z — backlight boost candidate

## Audio

- PCM5102APWR

## Protection / monitoring

- TPD2EUSB30ADRTR ×2 — USB data ESD
- INA238AIDGSR — optional EVT/DVT monitor

---

# 5. Key locked electrical values

## Input power

~~~text
UVLO ≈ 4.42 V
OVLO ≈ 5.70 V
TPS259474 RILIM = 750 Ω
ITIMER = 4.7 nF
dVdt = 4.7 nF
~~~

## 3V3

~~~text
TPS62132
L = 2.2 µH initial
CIN = 10 µF + 100 nF
COUT = 22 µF + optional 22 µF
SS/TR = 3.3 nF
~~~

## USB

~~~text
USB0 TPS25221 RILIM = 54.9 kΩ ~1.0 A nominal
USB1 TPS25221 RILIM = 34.8 kΩ ~1.6 A nominal initial

USB0 HS = 90 Ω diff
USB1 FS = 22 Ω / 22 Ω source series
~~~

## PCM5102A

~~~text
I2S source series = 22 Ω ×3
XSMT pulldown = 100 kΩ
OUT L/R = 470 Ω + 2.2 nF
~~~

## MIPI

~~~text
100 Ω differential
DSI_REXT = 4.02 kΩ
P/N skew <10 mil
pair-to-pair mismatch <30 mil
~~~

## microSD

~~~text
TPS22918 CT = 470 pF
QOD R = 100 Ω initial
CLK series = 22 Ω
CMD/D0-D3 pullups = 10 kΩ to 3V3_SD
~~~

## Monitoring

~~~text
5V_SYS shunt = 5 mΩ
INA238 address = 0x40
~~~

---

# 6. Locked GPIO map

~~~text
GPIO3   TOUCH_RST
GPIO4   TOUCH_INT
GPIO5   LCD_RST
GPIO6   LCD_TE optional
GPIO7   I2C_SDA
GPIO8   I2C_SCL

GPIO14  C6_SDIO_D0
GPIO15  C6_SDIO_D1
GPIO16  C6_SDIO_D2
GPIO17  C6_SDIO_D3
GPIO18  C6_SDIO_CLK
GPIO19  C6_SDIO_CMD

GPIO20  USB0_PWR_EN
GPIO21  USB0_FAULT_N
GPIO22  USB1_PWR_EN
GPIO23  LCD_BL_PWM

GPIO24  USB Serial/JTAG DM
GPIO25  USB Serial/JTAG DP
GPIO26  USB1 FS DM
GPIO27  USB1 FS DP

GPIO32  USB1_FAULT_N

GPIO35  BOOT
GPIO36  boot strap high
GPIO37  UART0 TX
GPIO38  UART0 RX

GPIO39  SD D0
GPIO40  SD D1
GPIO41  SD D2
GPIO42  SD D3
GPIO43  SD CLK
GPIO44  SD CMD
GPIO45  SD_PWR_EN
GPIO46  SD_CARD_DETECT optional

GPIO49  DAC_XSMT
GPIO50  DAC_BCLK
GPIO51  DAC_DATA
GPIO52  DAC_LRCK
GPIO53  INA238 ALERT optional
GPIO54  C6_RESET
~~~

---

# 7. Hard blockers before PCB layout freeze

## BLOCKER A — exact LCD/touch assembly mechanics

Electrical reconstruction is now substantially complete from the original JC4880 schematic.

Recovered with high confidence:

- DSI lane pin mapping
- TE
- LCD reset
- touch SDA/SCL/RST/INT
- 3.3 V/GND group
- LEDA/LEDK
- connector identity **SOFNG 0.5TBQP-30P-1 / C3975120**
- nominal connector geometry **30 contacts / 0.5 mm pitch**

Still required:

- exact final panel manufacturer MPN / purchased variant
- interpret Altium symbol references 31/32 relative to the 30-contact physical connector
- pins 15/16/18/19
- contact-side orientation and mating height
- authoritative panel/connector mechanical drawing
- confirm whether original FPC 3V3 pins 4/21/29 are internally common before mapping M1's separate 3V3_LCD and 3V3_TOUCH rails
- confirm purchased assembly is electrically the same JC4880 variant

Until then J_LCD footprint remains unfrozen.

## BLOCKER B — backlight is no longer a schematic blocker

Original JC4880 schematic reconstruction recovered:

~~~text
MP3202
10 µH
SS14
10 µF / 10 V input
100 nF / 25 V input HF
4.7 µF / 35 V output
100 nF / 50 V output HF
3.9 Ω || 2.2 Ω sense
~74 mA nominal LED current
0 Ω PWM-to-EN
10 kΩ EN pulldown
~~~

Rev A recommendation:

**direct EN PWM at 1 kHz in the M1-specific BSP.**

Remaining work is EVT validation of actual LEDA voltage/current and confirmation that the final purchased panel is the same electrical variant.

## BLOCKER C — exact mechanical connectors

Need final MPNs for:

- 5 V input
- USB-A ×2
- RCA ×2
- microSD socket
- RESET/BOOT switches

These do not block drawing the logical schematic, but block footprint and PCB mechanical freeze.

## P4 silicon — resolved for schematic

Selected MPN:

**ESP32-P4NRW32X**

Official Espressif product/PCN material lists it as the upgraded v3.x product family replacing ESP32-P4NRW32.

Target actual silicon for EVT:

**v3.2 or later approved revision**

Remaining work:

- verify incoming marking/lot/revision at procurement
- verify KiCad QFN104 symbol and footprint against the current datasheet
- use a separate M1 v3.x firmware binary with the pre-v3 selector disabled

This is no longer a PCB architecture blocker.

---

# 8. Items to validate in EVT, not before schematic

These values are intentionally engineering starting points:

- USB0 current limit
- USB1 FLX4 current limit
- input bulk capacitance
- 5V_SYS output bulk
- TPS259474 ITIMER
- TPS259474 dVdt
- TPS22918 SD CT/QOD timing
- crystal 15 pF load capacitors
- C6/Audio ferrite vs 0 Ω
- USB/MIPI/QSPI tuning resistors
- M1 1 kHz backlight PWM behavior / backlight current

They do not block schematic capture.

---

# 9. Schematic capture order

Recommended KiCad capture sequence:

1. 00_ROOT
2. 01_POWER_INPUT
3. 02_POWER_3V3
4. 03_P4_CORE
5. 04_P4_FLASH_CLOCK_RESET
6. 05_C6_WIFI
7. 06_USB_POWER
8. 07_USB0_STORAGE
9. 08_USB1_FLX4
10. 09_AUDIO_PCM5102A
11. 12_MICROSD
12. 13_DEBUG_SERVICE
13. 14_TEST_MONITORING
14. 10_DISPLAY_MIPI
15. 11_TOUCH_GT911
16. 15_DNP_OPTIONS

Display/touch are drawn late because their final connector pin numbering depends on the panel gate.

---

# 10. KiCad library / manufacturing tasks

Native ERC sign-off is complete. Remaining library work is tied to exact mechanical/manufacturing choices:

## Custom symbols to verify/create

- ESP32-P4NRW32X
- ESP32-C6-WROOM-1-N4
- exact LCD FPC
- exact USB-A
- exact RCA
- exact microSD socket

## Footprints requiring manufacturer drawing verification

- P4 QFN104
- W25Q128JV WSON
- C6-WROOM module
- PCM5102A TSSOP-20
- TPS259474
- TPS62132
- TLV62569
- TPS25221
- TPS22918
- MP3202
- INA238
- all connectors

---

# 11. ERC policy

Current KiCad 9.0.9 CI baseline satisfies:

- **0 unexplained ERC errors**
- **0 warnings**
- exactly **6 UUID-scoped J_LCD hard-gate exclusions**
- every additional exclusion or global severity downgrade is rejected by the structural validator
- CI now fails on any future non-excluded ERC warning

PCB may still not enter final layout freeze until the physical/mechanical gates below are closed.

---

# 12. PCB stackup requirement

Minimum:

**4 layers**

Recommended functional stack:

~~~text
L1 components + high-speed signals
L2 solid GND
L3 power distribution + secondary signals
L4 secondary signals
~~~

Final impedance dimensions come from the selected PCB fabricator stackup.

---

# 13. PCB critical placement order

1. ESP32-P4
2. P4 decoupling
3. P4 core DCDC
4. 40 MHz crystal
5. QSPI flash
6. MIPI FPC / display connector
7. USB0 HS connector/ESD
8. USB1 connector/ESD
9. C6 module at board edge / antenna keep-out
10. 3V3 buck
11. USB power switches
12. PCM5102A + RCA zone
13. backlight boost far from audio
14. microSD
15. service/test pads

---

# 14. Rev A design philosophy

The board should be:

- electrically conservative
- measurable
- recoverable
- firmware-controllable
- no hidden legacy blocks
- no shared USB fault domain
- no unnecessary analog/audio path
- no reliance on development-board accidents

Rev A intentionally has more test points and tuning footprints than later production revisions.

---

# 15. Go / No-Go

## GO for schematic capture

**COMPLETED / PASS**

Power, compute, USB, audio, Wi-Fi, touch logic, microSD, debug and monitoring are captured and native ERC-clean subject only to the documented J_LCD hard gate.

## GO for final PCB layout

**NOT YET**

Wait for:

1. resolve final LCD/touch panel variant, contact-side/mating mechanics, 31/32 interpretation, pins 15/16/18/19 and 3V3 rail commonality
2. final USB-A/RCA/microSD/5V-input/reset-boot connector mechanics
3. final board outline and PCB-fabricator stackup


---

# 16. Next engineering milestone

**Milestone M1-SCH-A — electrical/CI portion complete**

Completed:

- real hierarchical KiCad Rev A capture
- symbol/power/GPIO structural review
- KiCad 9.0.9 native ERC clean baseline
- generated manufacturing BOM/netlist parity review complete (historical run #76: 270/270; current M1-MECH-A8 source baseline: 269 after intentional J6 removal)
- 16-page schematic PDF human review complete
- hierarchy pin-sync equivalence complete: bidirectional root/child name+shape validation plus native KiCad root load/export

Remaining before final manufacturing sign-off:

- display and connector mechanical closure


Only after those physical/review gates close should the project enter final PCB placement/routing.
