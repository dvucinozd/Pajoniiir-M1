# Pajoniiir Mainboard — Engineering BOM v0.2

**Projekt:** Pajoniiir BL-A1800 / Pajoniiir-M1  
**Ploča:** Pajoniiir Mainboard Rev A  
**Repo:** `dvucinozd/Pajoniiir-M1`  
**Datum:** 2026-09-02  
**Status:** Engineering-intent BOM v0.2 — subsystem/value baseline; nije 1:1 manufacturing BOM. Za stvarni assembly output koristiti KiCad-generated BOM i `Pajoniiir_Manufacturing_Output_Contract_v0.1.md`.

> Ovaj BOM je namjerno konzervativan. Dijelovi koji ovise o konačnom LCD panelu, FPC rasporedu, kućištu ili mjerenju stvarne potrošnje označeni su kao `TBD`, `TBD-MECH` ili `TBD-VALIDATE`. Takve stavke se ne smiju tretirati kao proizvodno zaključane prije schematic/EVT reviewa.

---

## 1. Design baseline

Aktivna arhitektura Pajoniiir firmwarea je P4-only:

- ESP32-P4 je jedini glavni procesor.
- USB0 = Rekordbox mass storage.
- USB1 = DDJ-FLX4 MIDI IN/OUT + 4-kanalni USB Audio.
- MAIN audio = PCM5102A.
- CUE/PFL = USB Audio prema DDJ-FLX4 headphone izlazu.
- Wi-Fi = ESP32-C6 preko ESP-Hosted SDIO.
- Display = 4.3" 480×800 ST7701S MIPI-DSI.
- Touch = GT911.
- microSD = config/cache/controller profiles.
- ESP32-S3, ES8311, speaker amp i kamera nisu dio Rev A proizvoda.

Za novi dizajn mora se koristiti ESP32-P4 v3.x-or-later referentna shema. Espressif eksplicitno ne preporučuje v1.0/v1.3 za nove proizvode.

---

# 2. Kritične zaključane komponente

| RefDes | Qty | Funkcija | Manufacturer | MPN | Package | Ključni parametri | Status |
|---|---:|---|---|---|---|---|---|
| U1 | 1 | Main MCU + PSRAM | Espressif | **ESP32-P4NRW32X** | QFN104, 10×10 mm | upgraded v3.x family, target v3.2+, 32 MB in-package PSRAM | **LOCKED FOR SCHEMATIC; verify actual revision/lot at procurement** |
| U2 | 1 | Firmware QSPI NOR | Winbond | **W25Q128JVPIQ** | WSON-8, 6×5 mm | 128 Mbit / 16 MB, 2.7–3.6 V, 133 MHz, SPI/Dual/Quad | **LOCK-CANDIDATE** |
| U3 | 1 | P4 VDD_HP core DCDC | Texas Instruments | **TLV62569DRLR** | SOT-563 / DRL-6 | 2.5–5.5 V in, 2 A, adjustable | **LOCK-CANDIDATE**, Espressif-verified family |
| U4 | 1 | Wi-Fi coprocessor | Espressif | **ESP32-C6-WROOM-1-N4** | module, 18×25.5 mm | 4 MB flash, PCB antenna, 3.0–3.6 V | **LOCK-CANDIDATE** |
| U5 | 1 | Stereo MAIN DAC | Texas Instruments | **PCM5102APWR** | TSSOP-20 | 2.1 Vrms class, 112 dB SNR, 3-wire BCK PLL, active XSMT mute | **LOCKED by existing hardware path** |
| U6 | 1 | USB0 VBUS power switch | Texas Instruments | **TPS25221DRVR** | WSON-6, 2×2 mm | 2 A continuous, adjustable ILIM, active-high, reverse blocking | **LOCK-CANDIDATE** |
| U12 | 1 | USB1 VBUS power switch | Texas Instruments | **TPS25221DRVR** | WSON-6, 2×2 mm | independent 2 A channel, adjustable ILIM | **LOCK-CANDIDATE** |
| U7 | 1 | 5V input eFuse | Texas Instruments | **TPS259474ARPWR** | VQFN-HR-10, 2×2 mm | 2.7–23 V, 5.5 A class, reverse blocking, OCP/OVP | **LOCK-CANDIDATE** |
| U8 | 1 | 5V→3V3 system buck | Texas Instruments | **TPS62132RGTR** | VQFN-16, 3×3 mm | fixed 3.3 V, 3 A, 3–17 V input | **LOCK-CANDIDATE** |
| U9 | 1 | LCD WLED boost | Monolithic Power Systems | **MP3202DJ-LF-Z** | TSOT23-6 | 2.5–6 V in, 1.3 A switch, PWM dimming | **TBD-VALIDATE against final panel LED string** |
| U10 | 0/1 | Touch controller | GOODIX | **GT911** | panel/module dependent | capacitive touch, I²C | **PANEL-INTEGRATED preferred** |
| U13 | 1 | microSD load switch | Texas Instruments | **TPS22918DBVR** | SOT-23-6 | 2 A, adj. rise time, QOD | **LOCK-CANDIDATE** |
| U14 | 0/1 | 5V_SYS power monitor | Texas Instruments | **INA238AIDGSR** | VSSOP-10 | 16-bit I²C current/voltage/power monitor | **EVT/DVT DNP-CAPABLE** |

---

# 3. ESP32-P4 support BOM

## 3.1 Main power/decoupling

Espressif trenutno preporučuje najmanje oko 380 mA samo za osnovni ESP32-P4 + flash + PSRAM, uz dodatni budžet za MIPI, USB PHY i periferije.

| RefDes | Qty | Value / spec | Package | Napomena |
|---|---:|---|---|---|
| C_P4_BULK1..n | TBD | 10 µF, X7R/X5R, ≥6.3 V | 0805/0603 | na svakom glavnom power entranceu prema P4 reference designu |
| C_P4_DEC1..n | TBD | 100 nF, X7R, ≥10 V | 0402/0603 | po power pinu gdje propisuje Espressif |
| C_MIPI1 | 1 | 10 nF | 0402 | VDD_MIPI_DPHY |
| C_MIPI2 | 1 | 100 nF | 0402 | VDD_MIPI_DPHY |
| C_MIPI3 | 1 | 1 µF | 0603 | VDD_MIPI_DPHY |
| C_USBPHY1 | 1 | 10 nF | 0402 | VDD_USBPHY |
| C_USBPHY2 | 1 | 100 nF | 0402 | VDD_USBPHY |
| C_USBPHY3 | 1 | 4.7 µF | 0603/0805 | VDD_USBPHY |
| R_USBPHY_LINK | 1 | 0 Ω | 0603 | validacijski disconnect/tuning footprint |

## 3.2 Reset/boot

| RefDes | Qty | Value | Package | Funkcija |
|---|---:|---|---|---|
| R_RST | 1 | **10 kΩ 1%** | 0603 | CHIP_PU pull-up |
| C_RST | 1 | **1 µF** | 0603 | CHIP_PU RC delay |
| SW_RST | 1 | momentary NO | TBD-MECH | RESET prema GND |
| SW_BOOT | 1 | momentary NO | TBD-MECH | BOOT/download mode |

## 3.3 40 MHz clock

| RefDes | Qty | Value/spec | Package | Status |
|---|---:|---|---|---|
| Y1 | 1 | **ECS-400-10-37B2-CKY-TR — 40 MHz, ±10 ppm, CL 10 pF** | 2016, 4-SMD | **LOCK-CANDIDATE** |
| C_XTAL1 | 1 | **15 pF C0G/NP0 initial** | 0402 | EVT tuning |
| C_XTAL2 | 1 | **15 pF C0G/NP0 initial** | 0402 | EVT tuning |
| R_XTAL_SER | 1 | 0 Ω default | 0402 | tuning footprint |

Za Y1 je početni proračun rađen s CL=10 pF i približno 2–2.5 pF PCB stray capacitance; 15 pF + 15 pF je EVT startna vrijednost i mora se potvrditi mjerenjem stvarne frekvencije na Rev A ploči.

---

# 4. P4 VDD_HP DCDC blok

U3 = **TLV62569DRLR**.

Za Rev A koristiti Espressifovu **v3.x** TLV62569 referentnu topologiju, uključujući v3.x feedback/compensation mrežu.

| RefDes | Qty | Value | Candidate / note |
|---|---:|---|---|
| L_P4_CORE | 1 | **2.2 µH nominal start point** | Coilcraft XAL4020-222ME class; final prema Espressif/TI ref designu |
| C_CORE_IN | 1+ | 4.7–10 µF X7R | lokalno uz U3 |
| C_CORE_OUT | 1+ | 10–22 µF X7R | final prema stabilnosti/reference designu |
| R_CORE_FB1 | 1 | **499 kΩ** | v3.x reference-specific; provjeriti točnu vezu pri schematic captureu |
| R_CORE_FB2 | 1 | **499 kΩ** | v3.x reference-specific |
| C_CORE_FF | 1 | **22 pF C0G/NP0** | v3.x reference-specific |
| TP_CORE | 1 | test point | mjeriti VDD_HP pri bootu i dual-loadu |

**Napomena:** vrijednosti v3.x DCDC feedback mreže moraju se prenijeti iz aktualne Espressif referentne sheme, ne iz JC4880 v1.3 dizajna.

---

# 5. QSPI firmware flash

U2 = **W25Q128JVPIQ**.

Razlozi odabira:

- 16 MB odgovara sadašnjem firmware partition/OTA modelu.
- 2.7–3.6 V odgovara defaultnom P4 VDDO_FLASH 3.3 V režimu.
- WSON 6×5 mm je dovoljno kompaktan i još uvijek proizvodno razuman.
- Winbond ga navodi u aktualnoj W25Q-JV selection guide obitelji kao mass-production variant.
- **W25Q128JVPSQ** je preporučena pin/package-compatible temperaturno robusnija alternativa (-40…125 °C family variant).

| RefDes | Qty | Value | Package |
|---|---:|---|---|
| C_FLASH | 1 | 100 nF | 0402/0603 |
| R_FLASH_CS | 1 | **10 kΩ 1% pull-up** | 0603 |
| R_FLASH_CLK | 1 | 0 Ω | 0402 |
| R_FLASH_CS_SER | 1 | 0 Ω | 0402 |
| R_FLASH_D0 | 1 | 0 Ω | 0402 |
| R_FLASH_D1 | 1 | 0 Ω | 0402 |
| R_FLASH_D2 | 1 | 0 Ω | 0402 |
| R_FLASH_D3 | 1 | 0 Ω | 0402 |

0 Ω footprintovi služe za SI/EMI tuning i po potrebi se zamjenjuju malim serijskim otpornicima.

---

# 6. ESP32-C6 / Wi-Fi

U4 = **ESP32-C6-WROOM-1-N4**.

Za Pajoniiir je C6 mrežni coprocessor, ne aplikacijski procesor. 4 MB varijanta je dovoljna kao početni proizvodni kandidat za ESP-Hosted slave firmware; ako build kasnije zatraži veću particiju, footprint ostaje isti unutar WROOM-1 serije.

### P4 ↔ C6 SDIO

Firmware baseline:

| Signal | ESP32-P4 |
|---|---:|
| SDIO CLK | GPIO18 |
| SDIO CMD | GPIO19 |
| SDIO D0 | GPIO14 |
| SDIO D1 | GPIO15 |
| SDIO D2 | GPIO16 |
| SDIO D3 | GPIO17 |
| C6 RESET | GPIO54 |

### C6 support

| RefDes | Qty | Value | Napomena |
|---|---:|---|---|
| C_C6_HF | 1 | **100 nF** | lokalno |
| C_C6_LOCAL | 1 | **10 µF** | lokalno |
| C_C6_BULK | 1 | **22 µF** | Wi-Fi TX transient reserve |
| R_C6_EN | 1 | **10 kΩ** | EN pull-up |
| C_C6_EN | 1 | **1 µF** | EN RC delay |
| R_C6_RESET_SER | 1 | 0 Ω | P4 GPIO54 → C6 EN isolation/debug |
| R_SDIO_CMD_PU | 1 | **51.1 kΩ 1%** | mandatory SDIO pull-up |
| R_SDIO_D0_PU | 1 | **51.1 kΩ 1%** | mandatory SDIO pull-up |
| R_SDIO_D1_PU | 1 | **51.1 kΩ 1%** | mandatory SDIO pull-up |
| R_SDIO_D2_PU | 1 | **51.1 kΩ 1%** | mandatory SDIO pull-up |
| R_SDIO_D3_PU | 1 | **51.1 kΩ 1%** | mandatory SDIO pull-up |
| R_SDIO_CLK | 1 | **22 Ω initial** | SI tuning |
| R_SDIO_CMD/D0-D3 | 5 | 0 Ω | SI tuning |
| R_C6_GPIO8_PU | 1 | 10 kΩ | direct recovery/download mode |
| R_C6_GPIO9_PU | 1 | 10 kΩ | normal boot + recovery |
| R_C6_UART_TX/RX | 2 | 33 Ω | direct C6 debug |
| TP_C6_* | multiple | test pads | 3V3, EN, UART, boot, SDIO |

**RF:** ispod PCB antene nema coppera, trase ni visokih komponenti. Antena mora imati keep-out prema Espressif module placement pravilima.

---

# 7. Glavni 3.3 V rail

U8 = **TPS62132RGTR**.

Zašto:

- fixed 3.3 V,
- do 3 A,
- širok ulazni raspon,
- ACTIVE proizvod,
- dovoljno rezerve za P4 IO railove, C6, flash, SD i touch.

| RefDes | Qty | Vrijednost | Napomena |
|---|---:|---|---|
| L_3V3 | 1 | TBD prema TPS62132 datasheetu/EVM | odabrati low-DCR, Isat s marginom |
| C_3V3_IN | set | TBD, X7R | prema TI reference designu |
| C_3V3_OUT | set | TBD, X7R | prema TI reference designu |
| TP_3V3 | 1 | test point | obavezno |

**Power validation:** 3V3 rail mora se mjeriti osciloskopom pri Wi-Fi TX, USB hotplugu, SD pristupu i dual-deck DSP opterećenju.

---

# 8. 5V ulaz i eFuse

U7 = **TPS259474ARPWR**.

Rev A baseline:

| RefDes | Qty | Vrijednost | Napomena |
|---|---:|---|---|
| J_PWR | 1 | 5 V regulated input, ≥4 A source target | **TBD-MECH** locking connector |
| D_TVS_IN | 1 | 5 V rail TVS | TBD nakon surge/connector cilja |
| C_IN_HF | 1 | 100 nF X7R | uz eFuse |
| C_IN_MID | 1 | 10 µF | input |
| C_IN_BULK | 1 | 330 µF initial | 220–470 µF tuning |
| R_UV_TOP | 1 | **402 kΩ 1%** | UVLO |
| R_UV_BOT | 1 | **150 kΩ 1%** | UVLO |
| R_OV_TOP | 1 | **562 kΩ 1%** | OVLO |
| R_OV_BOT | 1 | **150 kΩ 1%** | OVLO |
| R_EFUSE_ILIM | 1 | **750 Ω 1%** | ~4.45 A typ |
| C_EFUSE_ITIMER | 1 | **4.7 nF** | ~3.9 ms initial |
| C_EFUSE_DVDT | 1 | **4.7 nF** | controlled 5V rise |
| C_5V_SYS_HF | 1 | 100 nF | output |
| C_5V_SYS_MID | 1 | 22 µF | output |
| C_5V_SYS_BULK | 1 | 330 µF | output reservoir |
| TP_5V_IN | 1 | test point | prije eFuse |
| TP_5V_SYS | 1 | test point | nakon shunt/monitor path |

Početni pragovi:

~~~text
UVLO ≈ 4.42 V
OVLO ≈ 5.70 V
ILIM ≈ 4.45 A typ
~~~

TPS259474A koristi PG/PGTH; nema zaseban FLT pin.

# 9. Dual USB VBUS

Rev A primary architecture koristi **2 × TPS25221DRVR**, po jedan switch za svaki port. Raniji TPS2561 koncept je demotiran u ALT jer ima zajednički RILIM za oba kanala.

Početni EVT targeti:

| RefDes | Qty | Value | Funkcija |
|---|---:|---|---|
| U_USB0 | 1 | TPS25221DRVR | USB0 independent switch |
| U_USB1 | 1 | TPS25221DRVR | USB1 independent switch |
| R_USB0_ILIM | 1 | **54.9 kΩ 1%** | ~1.0 A nominal storage limit |
| R_USB1_ILIM | 1 | **34.8 kΩ 1%** | ~1.6 A nominal FLX4 initial limit |
| R_USB0_EN_PD | 1 | 100 kΩ | default OFF |
| R_USB1_EN_PD | 1 | 100 kΩ | default OFF |
| R_USB0_FLT_PU | 1 | 10 kΩ | active-low fault pull-up |
| R_USB1_FLT_PU | 1 | 10 kΩ | active-low fault pull-up |
| C_USB0_IN | 1 | 100 nF | local switch input |
| C_USB1_IN | 1 | 100 nF | local switch input |
| C_USB_PWR_LOCAL | 1 | 10 µF | local 5V_SYS reserve |
| C_USB0_OUT_HF | 1 | 100 nF | USB0 output |
| C_USB1_OUT_HF | 1 | 100 nF | USB1 output |
| C_USB0_OUT_BULK | 1 | 47 µF | EVT initial |
| C_USB1_OUT_BULK | 1 | 47 µF | EVT initial |
| C_USB0_OUT_OPT | 1 | 100 µF | DNP tuning |
| C_USB1_OUT_OPT | 1 | 100 µF | DNP tuning |

Predloženi P4 control GPIO-i: GPIO20/21 za USB0 EN/FAULT_N i GPIO22/32 za USB1 EN/FAULT_N; finalno potvrditi punim v3.x pin-conflict auditom.

Detalji su u `Pajoniiir_Dual_USB_VBUS_Power_Design_v0.2.md`.
---

# 10. USB signal path

## USB0 — Rekordbox storage / High-Speed

Dedicated ESP32-P4 HS PHY.

| RefDes | Qty | Vrijednost / MPN |
|---|---:|---|
| J_USB0 | 1 | USB-A receptacle **TBD-MECH** |
| D_USB0_ESD | 1 | **TPD2EUSB30ADRTR** |
| R_USB0_DM | 1 | 0 Ω tuning |
| R_USB0_DP | 1 | 0 Ω tuning |
| R_USB0_SHIELD | 1 | 0 Ω default |
| C_USB0_SHIELD | 1 | 1 nF DNP |
| R_USB0_SHIELD_HI | 1 | 1 MΩ DNP |

Routing: **90 Ω differential ±10%**, minimal vias, continuous GND. ESD capacitance target <1 pF; TPD2EUSB30A is suitable low-C candidate.

## USB1 — DDJ-FLX4 / Full-Speed

P4 GPIO26 = DM, GPIO27 = DP.

| RefDes | Qty | Vrijednost / MPN |
|---|---:|---|
| J_USB1 | 1 | USB-A receptacle **TBD-MECH** |
| D_USB1_ESD | 1 | **TPD2EUSB30ADRTR** |
| R_USB1_DM | 1 | **22 Ω** |
| R_USB1_DP | 1 | **22 Ω** |
| C_USB1_DM | 1 | DNP tuning |
| C_USB1_DP | 1 | DNP tuning |
| R_USB1_SHIELD | 1 | 0 Ω default |
| C_USB1_SHIELD | 1 | 1 nF DNP |
| R_USB1_SHIELD_HI | 1 | 1 MΩ DNP |

GPIO24/25 ostaju rezervirani za P4 USB Serial/JTAG factory/service.

# 11. PCM5102A MAIN audio

U5 = **PCM5102APWR**.

Pin baseline:

~~~text
GPIO50 = BCLK
GPIO52 = LRCK/WS
GPIO51 = DATA
GPIO49 = XSMT
SCK = GND
FMT = LOW
FLT = LOW
DEMP = LOW
~~~

Support BOM:

| RefDes | Qty | Value |
|---|---:|---|
| FB_AUDIO | 1 | 0 Ω default / ferrite option |
| R_I2S_BCLK | 1 | 22 Ω |
| R_I2S_LRCK | 1 | 22 Ω |
| R_I2S_DATA | 1 | 22 Ω |
| R_XSMT_SER | 1 | 100 Ω |
| R_XSMT_PD | 1 | 100 kΩ |
| C_AVDD_HF | 1 | 100 nF |
| C_AVDD_BULK | 1 | 10 µF |
| C_CPVDD_HF | 1 | 100 nF |
| C_CPVDD_BULK | 1 | 10 µF |
| C_CP_FLY | 1 | 2.2 µF |
| C_VNEG | 1 | 2.2 µF |
| C_DVDD_HF | 1 | 100 nF |
| C_DVDD_BULK | 1 | 10 µF |
| C_LDOO | 1 | 100 nF |
| R_OUT_L | 1 | **470 Ω** |
| R_OUT_R | 1 | **470 Ω** |
| C_OUT_L | 1 | **2.2 nF C0G** |
| C_OUT_R | 1 | **2.2 nF C0G** |
| J_RCA_L | 1 | RCA **TBD-MECH** |
| J_RCA_R | 1 | RCA **TBD-MECH** |
| J_LINE_35 | 0/1 | 3.5 mm line out DNP |

Nema DC-blocking capacitors na RCA outputima.

# 12. Display / MIPI-DSI

Baseline:

- 4.3", 480×800
- ST7701S
- 2-lane MIPI DSI
- 500 Mbps/lane
- 34 MHz DPI
- RGB565
- PPA landscape rotation

### DSI / panel interface

| RefDes | Qty | Vrijednost / funkcija |
|---|---:|---|
| J_LCD | 1 | **SOFNG 0.5TBQP-30P-1 / JLCPCB C3975120 — 30 contacts, 0.5 mm pitch; footprint still TBD-MECH pending contact-side/mating geometry, Altium 31/32 interpretation, pins 15/16/18/19 and panel 3V3 commonality** |
| R_DSI_REXT | 1 | **4.02 kΩ 1%** |
| R_DSI_CLK_P/N | 2 | 0 Ω tuning |
| R_DSI_D0_P/N | 2 | 0 Ω tuning |
| R_DSI_D1_P/N | 2 | 0 Ω tuning |
| FB_LCD | 1 | 0 Ω default |
| C_LCD_HF | 1 | 100 nF |
| C_LCD_BULK | 1 | 10 µF |
| R_LCD_RST_SER | 1 | 100 Ω |
| R_LCD_RST_PD | 1 | 100 kΩ |
| R_LCD_TE_SER | 1 | 0 Ω DNP |

MIPI target: **100 Ω differential ±10%**, P/N skew <10 mil, pair-to-pair mismatch <30 mil.

GPIO5 = LCD_RST, GPIO23 = LCD_BL_PWM, GPIO6 = optional LCD_TE.

### Backlight — JC4880 forensic baseline

| RefDes | Qty | Value / part |
|---|---:|---|
| U_BL | 1 | **MP3202DJ-LF-Z** |
| L_BL | 1 | **10 µH** |
| D_BL | 1 | **SS14** |
| C_BL_IN | 1 | **10 µF / 10 V** |
| C_BL_HF | 1 | **100 nF / 25 V** |
| C_BL_OUT | 1 | **4.7 µF / 35 V** |
| C_BL_OUT_HF | 1 | **100 nF / 50 V** |
| R_BL_PWM | 1 | **0 Ω** |
| R_BL_EN_PD | 1 | **10 kΩ** |
| R_BL_SENSE_A | 1 | **3.9 Ω** |
| R_BL_SENSE_B | 1 | **2.2 Ω** |

Sense equivalent:

~~~text
3.9 Ω || 2.2 Ω ≈ 1.4066 Ω
I_LED @104mV typ ≈ 73.9 mA
~~~

M1 baseline uses **direct EN PWM at 1 kHz**. The current JC4880 firmware's 5 kHz value should not be copied into the new M1 BSP without using the alternate filtered-FB topology.

Backlight electrical values are now lock-candidates if the final panel is the same electrical JC4880 assembly family. Connector identity/contact count/pitch are known; exact mating footprint, final panel MPN, pins 15/16/18/19 and safe mapping of original common FPC 3V3 pins 4/21/29 remain the hard display gate.

# 13. Touch / GT911

Preferred: GT911 integriran u finalni panel/touch assembly.

Rev A mapping:

~~~text
GPIO3 = TOUCH_RST
GPIO4 = TOUCH_INT
GPIO7 = TOUCH_SDA
GPIO8 = TOUCH_SCL
address = 0x5D
~~~

| RefDes | Qty | Value |
|---|---:|---|
| FB_TOUCH | 1 | 0 Ω default |
| C_TOUCH_HF | 1 | 100 nF |
| C_TOUCH_BULK | 1 | 4.7 µF |
| R_TOUCH_RST_PU | 1 | 10 kΩ |
| R_TOUCH_RST_SER | 1 | 100 Ω |
| R_TOUCH_INT_SER | 1 | 100 Ω |
| R_TOUCH_SDA_PU | 1 | 4.7 kΩ |
| R_TOUCH_SCL_PU | 1 | 4.7 kΩ |
| R_TOUCH_SDA_PU2 | 1 | 4.7 kΩ DNP |
| R_TOUCH_SCL_PU2 | 1 | 4.7 kΩ DNP |
| R_TOUCH_SDA_SER | 1 | 22 Ω |
| R_TOUCH_SCL_SER | 1 | 22 Ω |
| D_TOUCH_ESD | 0/1 | low-C array DNP |

GPIO4 se tijekom address-selection reseta vozi LOW, a nakon latcha vraća u high-Z input bez statičkog pull-up/downa.

# 14. microSD

P4 SDMMC0:

~~~text
GPIO39 D0
GPIO40 D1
GPIO41 D2
GPIO42 D3
GPIO43 CLK
GPIO44 CMD
GPIO45 SD_PWR_EN
GPIO46 optional CARD_DETECT
~~~

Power switch:

**TPS22918DBVR**

| RefDes | Qty | Value |
|---|---:|---|
| U_SD_PWR | 1 | TPS22918DBVR |
| R_SD_EN_PD | 1 | 100 kΩ |
| C_SD_CT | 1 | **470 pF ≥25 V** |
| R_SD_QOD | 1 | **100 Ω initial** |
| C_SD_SW_IN | 1 | 1 µF |
| C_SD_SW_IN_HF | 1 | 100 nF |
| C_SD_OUT | 1 | 10 µF |
| C_SD_OUT_HF | 1 | 100 nF |
| C_SD_OUT_OPT | 1 | 22 µF DNP |
| R_SD_CMD_PU | 1 | 10 kΩ to 3V3_SD |
| R_SD_D0_PU | 1 | 10 kΩ to 3V3_SD |
| R_SD_D1_PU | 1 | 10 kΩ to 3V3_SD |
| R_SD_D2_PU | 1 | 10 kΩ to 3V3_SD |
| R_SD_D3_PU | 1 | 10 kΩ to 3V3_SD |
| R_SD_CLK_SER | 1 | 22 Ω |
| R_SD_CMD_SER | 1 | 0 Ω |
| R_SD_D0_SER | 1 | 0 Ω |
| R_SD_D1_SER | 1 | 0 Ω |
| R_SD_D2_SER | 1 | 0 Ω |
| R_SD_D3_SER | 1 | 0 Ω |
| C_SD_CLK_TUNE | 1 | DNP |
| J_SD | 1 | microSD socket **TBD-MECH** |
| D_SD_ESD | 0/1 | low-C array TBD/DNP |

Kartica se može stvarno power-cycleati bez rebootanja P4.

# 15. Debug / service

Rev A service architecture:

## P4 UART0

- GPIO37 TX
- GPIO38 RX
- 33 Ω series
- BOOT GPIO35
- CHIP_PU

## P4 USB Serial/JTAG

- GPIO24 DM
- GPIO25 DP
- 22 Ω series initial
- factory pogo pads

## C6 direct recovery

- UART TX/RX
- C6 EN
- GPIO9 boot control
- separate pogo/Tag-Connect footprint

PCB footprints:

| RefDes | Qty | Funkcija |
|---|---:|---|
| JDBG_P4 | 1 | TC2030-NL-FP class, DNL |
| JDBG_C6 | 1 | TC2030-NL-FP class, DNL |
| JDBG_USB | 1 | P4 USB Serial/JTAG pogo footprint |

Programmer VREF je sense-only i ne smije back-powerati board.

# 16. Test points — obavezni za Rev A

Power:

- VIN_5V
- 5V_SYS
- 3V3_SYS
- P4_VDD_HP
- 3V3_C6
- 3V3_AUDIO
- 3V3_SD
- USB0_VBUS
- USB1_VBUS
- MIPI_2V5
- LEDA

Debug/control:

- CHIP_PU
- BOOT GPIO35
- GPIO36
- P4 UART0 TX/RX
- C6 UART TX/RX
- C6 EN
- USB FAULT/EN
- DAC_XSMT

High-speed data TP-ovi smiju biti samo micro-probe/DNP tipa bez velikih stubova.

Dodati najmanje tri scope-friendly GND loopa: power, digital i audio/display zona.

# 17. EVT / DVT opcionalni power monitor

Primary candidate:

**INA238AIDGSR**

Mjerenje:

~~~text
TPS259474A -> 5V_PROTECTED -> 5mΩ Kelvin shunt -> 5V_SYS
~~~

| RefDes | Qty | Value |
|---|---:|---|
| U_PWRMON | 0/1 | INA238AIDGSR |
| R_SYS_SHUNT | 1 | **Vishay WSK25125L000FEA — 5 mΩ, 1%, 1 W, 4-terminal** | `Resistor_SMD:R_Shunt_Vishay_WSK2512_6332Metric_T1.19mm` |
| R_INA_P | 1 | 10 Ω |
| R_INA_N | 1 | 10 Ω |
| C_INA_DIFF | 1 | 100 nF |
| C_INA_HF | 1 | 100 nF |
| C_INA_LOCAL | 1 | 1 µF |
| R_INA_ALERT_PU | 1 | 10 kΩ |

I2C address: **0x40** (A0=A1=GND).  
Shared P4 I2C: GPIO7/8.  
GPIO53 = optional SYS_POWER_ALERT_N.

INA238 je DNP-capable nakon DVT-a; PCB mora ostati funkcionalan bez njega.

# 18. Komponente koje se namjerno NE ugrađuju

| Blok | Rev A |
|---|---|
| ESP32-S3 | **NO POPULATE / nema footprinta** |
| ES8311 codec | **NO** |
| speaker amplifier | **NO** |
| speaker connector | **NO** |
| analog microphone | **NO** |
| MIPI CSI camera | **NO** |
| RS485/MAX485 | **NO** |
| P4↔S3 UART | **NO** |
| P4→S3 monitor I²S | **NO** |
| battery charger | **NO u Rev A** |
| large generic GPIO header | **NO** |

---

# 19. Mehaničke stavke koje još nisu zaključane

Sljedeće stavke moraju čekati kućište i finalni panel:

1. exact LCD panel MPN
2. LCD FPC connector MPN
3. GT911 FPC/topologija ako touch controller nije integriran na panel
4. USB-A receptacle MPN ×2
5. RCA connector MPN ×2
6. DC input connector MPN
7. microSD socket MPN
8. RESET/BOOT tactile switch MPN
9. mounting holes / standoffs
10. PCB outline

---

# 20. Lifecycle / validation status

## Manufacturer-verified ACTIVE / current candidate

- TPS25221 family — TI ACTIVE; Rev A primary USB VBUS switch.
- TPS2561 family — TI ACTIVE; ALT only because both channels share one RILIM.
- TPS25947 family — TI ACTIVE.
- TPS62132RGTR — TI ACTIVE.
- TLV62569 family — TI ACTIVE; TI navodi i novije alternative, ali Espressif ga i dalje eksplicitno navodi kao verified P4 DCDC model.
- PCM5102A — TI ACTIVE; MAIN audio design locked around PCM5102APWR with hardware XSMT mute.
- MP3202 — MPS ACTIVE.
- XGL4030-103MEC — Coilcraft current production 10 µH shielded power inductor; 3.1 A Isat / 3.9 A Irms class.
- WSK25125L000FEA — Vishay current-sense shunt, 5 mΩ, 1%, 1 W, 4-terminal.
- ESP32-C6-WROOM-1 — aktualni Espressif modul; datasheet v1.4.
- W25Q128JV family — nalazi se u Winbond 2025 product selection guide, mass-production označen.
- ESP32-P4NRW32X — nalazi se u aktualnom ESP32-P4 datasheetu; **prije EVT narudžbe obavezno potvrditi stvarni orderable revision/availability**, jer je dostupna javna P4 dokumentacija i dalje označena kao pre-release.

---

# 21. Rev A schematic lock gates

Prije PCB layouta moraju se zatvoriti:

- [x] ESP32-P4 v3.x MPN locked: **ESP32-P4NRW32X**; target actual rev v3.2+
- [ ] potvrda P4 v3.x TLV62569 reference values/net topology
- [x] Y1 candidate ECS-400-10-37B2-CKY-TR + 15 pF initial CL network; EVT frequency tuning remains
- [ ] flash compatibility / boot test s W25Q128JV
- [ ] finalni LCD panel MPN / FPC physical connector; electrical pin mapping mostly reconstructed, 30-vs-32 discrepancy remains
- [x] MP3202 JC4880 backlight baseline reconstructed (~74 mA); EVT validation remains
- [x] GT911 interface strategy: GPIO3 RST / GPIO4 INT / 0x5D; exact FPC pins still pending
- [ ] USB0 actual peak current
- [ ] FLX4 actual USB1 peak/startup current
- [ ] TPS25221 USB0/USB1 RILIM final values from measured device currents
- [x] TPS259474A initial ILIM/ITIMER/dVdt/UVLO/OVLO values defined; EVT validation remains
- [ ] 5V/4A adapter connector
- [ ] RCA mechanical choice
- [ ] USB-A mechanical choice
- [ ] microSD socket choice
- [ ] enclosure PCB outline

---

# 22. Izvori za BOM v0.1

Primarni izvori provjereni 2026-09-02:

- Espressif ESP32-P4 Series Datasheet:  
  https://documentation.espressif.com/esp32-p4_datasheet_en.html
- Espressif ESP32-P4 Hardware Design Guidelines / Schematic Checklist:  
  https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32p4/schematic-checklist-esp32p4.html
- Espressif ESP32-C6-WROOM-1 Datasheet:  
  https://documentation.espressif.com/esp32-c6-wroom-1_wroom-1u_datasheet_en.html
- TI PCM5102A:  
  https://www.ti.com/product/PCM5102A
- TI TPS25221:  
  https://www.ti.com/product/TPS25221
- TI TPD2EUSB30A:  
  https://www.ti.com/product/TPD2EUSB30A
- TI TPS2561 (alternate):  
  https://www.ti.com/product/TPS2561
- TI TPS25947:  
  https://www.ti.com/product/TPS25947
- TI TPS62132:  
  https://www.ti.com/product/TPS62132
- TI TLV62569:  
  https://www.ti.com/product/TLV62569
- TI TPS22918:  
  https://www.ti.com/product/TPS22918
- TI INA238:  
  https://www.ti.com/product/INA238
- Winbond W25Q-JV selection / W25Q128JV:  
  https://www.winbond.com/
- MPS MP3202:  
  https://www.monolithicpower.com/en/products/power-management/display-power-and-control/backlight-drivers-wled/mp3202dj-lf-z.html

---

# 23. Zaključak

Ovaj BOM v0.2 već dovoljno precizno zaključava **elektroničku arhitekturu** da se može krenuti u pravi schematic capture, ali namjerno ne glumi finalni manufacturing BOM.

Najvažniji zaključani kandidati su:

```text
ESP32-P4NRW32X
W25Q128JVPIQ
TLV62569DRLR
ESP32-C6-WROOM-1-N4
PCM5102APWR
TPS25221DRVR x2
TPS259474ARPWR
TPS62132RGTR
MP3202DJ-LF-Z
TPS22918DBVR
INA238AIDGSR (EVT/DVT option)
```

Najveći preostali hardverski rizici prije layouta ostaju:

1. finalni LCD/FPC mechanics and exact panel procurement,
3. USB VBUS current-limit dimenzioniranje stvarnim mjerenjem,
4. 5V_SYS transient/brownout margin,
5. konačna mehanika konektora.

**Sljedeći dokument:** `Pajoniiir_Mainboard_Schematic_Plan_v0.1.md`, kojim se ovaj BOM pretvara u hijerarhijske sheetove za KiCad/Altium.
