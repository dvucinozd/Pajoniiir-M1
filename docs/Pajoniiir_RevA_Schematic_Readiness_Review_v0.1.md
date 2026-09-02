# Pajoniiir-M1 Rev A — Schematic Readiness Review v0.1

**Datum:** 2026-09-02  
**Repo:** dvucinozd/Pajoniiir-M1  
**Branch:** main  
**Status:** Pre-KiCad schematic readiness gate

---

# 1. Executive summary

Rev A electrical architecture is now sufficiently specified to begin schematic capture.

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
| 10 MIPI display/backlight | Pajoniiir_MIPI_DSI_Display_Backlight_Design_v0.1.md | READY WITH PANEL GATE |
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

## BLOCKER A — exact LCD/touch assembly

Need:

- exact manufacturer MPN
- exact FPC contact count
- exact FPC pitch
- exact pin order
- contact orientation
- panel mechanical drawing
- touch controller placement
- LEDA/LEDK electrical specification

Without this, J_LCD footprint must remain unfrozen.

## BLOCKER B — backlight LED string

Need:

- number of LEDs
- series/parallel configuration
- LED Vf range
- target current
- maximum current

Then lock:

- MP3202 inductor
- Schottky diode
- current-sense resistor
- output capacitor
- 5 kHz filtered-FB dimming network

## BLOCKER C — exact mechanical connectors

Need final MPNs for:

- 5 V input
- USB-A ×2
- RCA ×2
- microSD socket
- RESET/BOOT switches

These do not block drawing the logical schematic, but block footprint and PCB mechanical freeze.

## BLOCKER D — exact orderable P4 silicon

Before EVT procurement:

- confirm orderable ESP32-P4NRW32X v3.x revision
- verify package drawing and symbol/footprint against current datasheet/PCN

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
- backlight dimming filter

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

# 10. KiCad library tasks

Before ERC sign-off:

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

Schematic cannot advance to PCB until:

- zero unexplained ERC errors
- every NC explicit
- no floating EN/reset/strap pins
- all power outputs/inputs typed correctly
- all DNP elements marked
- no legacy JC4880 nets remain accidentally connected
- GPIO map matches Pajoniiir_Global_GPIO_Allocation_v0.1.md

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

**YES**

Power, compute, USB, audio, Wi-Fi, touch logic, microSD, debug and monitoring are sufficiently specified.

## GO for final PCB layout

**NOT YET**

Wait for:

1. exact LCD/touch FPC
2. exact backlight LED string
3. final connector mechanics
4. final P4 orderable silicon confirmation

---

# 16. Next engineering milestone

**Milestone M1-SCH-A**

Create the real KiCad Rev A schematic and pass:

- symbol review
- power review
- GPIO review
- ERC
- schematic design review

Only after M1-SCH-A passes should the project enter PCB placement/routing.
