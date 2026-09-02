# Pajoniiir Mainboard — Engineering BOM v0.1

**Projekt:** Pajoniiir BL-A1800 / Pajoniiir-M1  
**Ploča:** Pajoniiir Mainboard Rev A  
**Repo:** `dvucinozd/Pajoniiir-M1`  
**Datum:** 2026-09-02  
**Status:** **SUPERSEDED** — koristiti `Pajoniiir_Mainboard_BOM_v0.2.md` za aktualni Rev A baseline

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
| U1 | 1 | Main MCU + PSRAM | Espressif | **ESP32-P4NRW32X** | QFN104, 10×10 mm | ESP32-P4, 32 MB in-package PSRAM | **LOCK-CANDIDATE**; koristiti v3.x reference design |
| U2 | 1 | Firmware QSPI NOR | Winbond | **W25Q128JVPIQ** | WSON-8, 6×5 mm | 128 Mbit / 16 MB, 2.7–3.6 V, 133 MHz, SPI/Dual/Quad | **LOCK-CANDIDATE** |
| U3 | 1 | P4 VDD_HP core DCDC | Texas Instruments | **TLV62569DRLR** | SOT-563 / DRL-6 | 2.5–5.5 V in, 2 A, adjustable | **LOCK-CANDIDATE**, Espressif-verified family |
| U4 | 1 | Wi-Fi coprocessor | Espressif | **ESP32-C6-WROOM-1-N4** | module, 18×25.5 mm | 4 MB flash, PCB antenna, 3.0–3.6 V | **LOCK-CANDIDATE** |
| U5 | 1 | Stereo MAIN DAC | Texas Instruments | **PCM5102APWR** | TSSOP-20 | 2.1 Vrms class, 112 dB SNR, 3-wire BCK PLL, active XSMT mute | **LOCKED by existing hardware path** |
| U6 | 1 | USB0 VBUS power switch | Texas Instruments | **TPS25221DRVR** | WSON-6, 2×2 mm | 2 A continuous, adjustable ILIM, active-high, reverse blocking | **LOCK-CANDIDATE** |
| U12 | 1 | USB1 VBUS power switch | Texas Instruments | **TPS25221DRVR** | WSON-6, 2×2 mm | independent 2 A channel, adjustable ILIM | **LOCK-CANDIDATE** |
| U7 | 1 | 5V input eFuse | Texas Instruments | **TPS259474ARPWR** | VQFN-HR-10, 2×2 mm | 2.7–23 V, 5.5 A class, reverse blocking, OCP/OVP | **LOCK-CANDIDATE** |
| U8 | 1 | 5V→3V3 system buck | Texas Instruments | **TPS62132RGTR** | VQFN-16, 3×3 mm | fixed 3.3 V, 3 A, 3–17 V input | **LOCK-CANDIDATE** |
| U9 | 1 | LCD WLED boost | Monolithic Power Systems | **MP3202DJ-LF-Z** | TSOT23-6 | 2.5–6 V in, 1.3 A switch, PWM dimming | **TBD-VALIDATE against final panel LED string** |
| U10 | 0/1 | Touch controller | GOODIX | **GT911** | panel/module dependent | capacitive touch, I²C | **TBD: may already be on touch FPC/module** |

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

Funkcije koje želimo:

- reverse current blocking,
- input reverse-polarity protection,
- overcurrent protection,
- short-circuit protection,
- adjustable soft-start,
- thermal shutdown,
- fault/power-good signalling.

| RefDes | Qty | Vrijednost | Napomena |
|---|---:|---|---|
| J_PWR | 1 | 5 V regulated input | **TBD-MECH** locking connector |
| F_IN | 0/1 | optional replaceable fuse footprint | EVT option |
| D_TVS_IN | 1 | 5 V rail TVS, exact MPN TBD | odabrati nakon input connector/surge cilja |
| C_IN_BULK | 1+ | 220–470 µF low-ESR start point | EVT transient reservoir; final mjerenjem |
| C_IN_HF | 1 | 100 nF X7R | uz eFuse |
| R_EFUSE_ILIM | 1 | TBD for ~4 A system ceiling | izračun po TPS25947 datasheetu |
| C_EFUSE_DVDT | 1 | TBD | soft-start/inrush |
| TP_5V_IN | 1 | test point | prije eFuse |
| TP_5V_SYS | 1 | test point | nakon eFuse |

Design rail: **5 V / 4 A preporučeni vanjski adapter**, ali stvarna granica se mora zaključati mjerenjem.

---

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

## J_USB0 — Rekordbox storage

**Preporuka za Rev A:** USB-A receptacle, through-hole shell + SMT signal pins ili robustan THT konektor.

Exact MPN ostaje **TBD-MECH** dok se ne zaključi kućište.

USB0 je High-Speed put i zahtijeva:

- 90 Ω differential impedance,
- minimalan broj via,
- kontinuirani GND reference,
- low-capacitance ESD.

## J_USB1 — DDJ-FLX4

**Preporuka:** USB-A receptacle; FLX4 se spaja A→C data kabelom.

Za FS path predvidjeti:

| RefDes | Qty | Value |
|---|---:|---|
| R_USB1_DP | 1 | 22 Ω initial |
| R_USB1_DM | 1 | 22 Ω initial |

Može se koristiti 33 Ω nakon eye/edge/EMI validacije ako bude potrebno.

## ESD

| RefDes | Qty | Funkcija | MPN status |
|---|---:|---|---|
| D_USB0_ESD | 1 | HS D+/D- low-C ESD array | **TBD exact; Cpar cilj <1 pF** |
| D_USB1_ESD | 1 | FS D+/D- ESD array | **TBD exact** |

Kandidatske obitelji: TI TPD2EUSBxx, ST USBLC6-2, Nexperia PESD USB obitelj. Finalni MPN se bira po stvarnoj capacitance/specifikaciji i layoutu.

---

# 11. PCM5102A MAIN audio

U5 = **PCM5102APWR**.

Aktualni firmware pinovi ostaju:

| I²S | ESP32-P4 |
|---|---:|
| BCLK | GPIO50 |
| LRCK/WS | GPIO52 |
| DATA/DOUT → DAC DIN | GPIO51 |
| MCLK | unused |

Početni analogni BOM:

| RefDes | Qty | Value | Napomena |
|---|---:|---|---|
| R_OUT_L | 1 | **470 Ω** | line output RF network |
| R_OUT_R | 1 | **470 Ω** | line output RF network |
| C_OUT_L | 1 | **2.2 nF** | C0G/NP0 preferred |
| C_OUT_R | 1 | **2.2 nF** | C0G/NP0 preferred |
| C_DAC_CP | 1+ | **2.2 µF class** | charge pump; potvrditi exact pin network pri schematic captureu |
| C_DAC_DEC | set | 100 nF + bulk prema TI reference | AVDD/DVDD/CPVDD |
| R_XSMT | 1 | TBD | mute control/strap |
| R_FMT | 1 | strap for I²S | hardware format |
| R_FLT | 1 | strap default filter | hardware filter |

Konektori:

| RefDes | Qty | Funkcija | Status |
|---|---:|---|---|
| J_RCA_L | 1 | MAIN LEFT RCA | **TBD-MECH exact MPN** |
| J_RCA_R | 1 | MAIN RIGHT RCA | **TBD-MECH exact MPN** |
| J_LINE_35 | 0/1 | optional 3.5 mm stereo line out | DNP by default |

PCM5102A i RCA mreža trebaju biti fizički daleko od backlight boosta, USB HS para i switching nodeova.

---

# 12. Display / MIPI-DSI

Ciljana funkcionalna specifikacija:

- 4.3"
- 480×800
- ST7701S
- 2-lane MIPI DSI
- landscape kroz rotation
- firmware baseline 500 Mbps/lane class

**Finalni LCD/FPC MPN nije još zaključan.** To je namjerno: FPC pinout, backlight string i mehanička geometrija moraju biti potvrđeni prije PCB-a.

| RefDes | Qty | Value / funkcija |
|---|---:|---|
| J_LCD | 1 | FPC connector — **TBD after exact panel** |
| R_DSI_REXT | 1 | **4.02 kΩ 1%** pull-down |
| R_DSI_CLK_P/N | 2 | 0 Ω tuning footprints |
| R_DSI_D0_P/N | 2 | 0 Ω tuning footprints |
| R_DSI_D1_P/N | 2 | 0 Ω tuning footprints |
| U_BL | 1 | MP3202DJ-LF-Z candidate |
| L_BL | 1 | TBD by LED current/voltage |
| R_BL_SENSE | 1 | TBD by target backlight current |
| C_BL_IN/OUT | set | TBD per MP3202 + panel |
| D_BL | 0/1 | Schottky if required by exact application topology |

GPIO baseline:

- LCD RESET = GPIO5
- Backlight PWM/EN = GPIO23

---

# 13. Touch / GT911

Baseline:

- SDA = GPIO7
- SCL = GPIO8
- I²C address currently 0x5D

Nova ploča treba, za razliku od minimalnog prototipa, dovesti i:

- `TOUCH_INT`
- `TOUCH_RST`

| RefDes | Qty | Value |
|---|---:|---|
| R_I2C_SDA | 1 | 2.2–4.7 kΩ TBD after bus capacitance |
| R_I2C_SCL | 1 | 2.2–4.7 kΩ TBD after bus capacitance |
| R_TOUCH_INT | 1 | TBD |
| R_TOUCH_RST | 1 | TBD |
| D_TOUCH_ESD | 0/1 | optional ESD array at exposed FPC |

---

# 14. microSD

P4 SDMMC baseline:

| Signal | GPIO |
|---|---:|
| D0 | GPIO39 |
| D1 | GPIO40 |
| D2 | GPIO41 |
| D3 | GPIO42 |
| CLK | GPIO43 |
| CMD | GPIO44 |

| RefDes | Qty | Value / funkcija |
|---|---:|---|
| J_SD | 1 | microSD socket — **TBD-MECH exact MPN** |
| R_SD_CMD_PU | 1 | 10 kΩ initial |
| R_SD_D0_PU | 1 | 10 kΩ initial |
| R_SD_D1_PU | 1 | 10 kΩ initial |
| R_SD_D2_PU | 1 | 10 kΩ initial |
| R_SD_D3_PU | 1 | 10 kΩ initial |
| R_SD_CLK | 1 | 22 Ω initial / tuning |
| C_SD_DEC | 1 | 100 nF |
| C_SD_BULK | 1 | 22 µF start point |
| U_SD_LOAD | 0/1 | optional high-side load switch | DNP until firmware recovery need confirmed |

---

# 15. Debug / service

Rev A treba imati proizvodno pristupačne pogo/Tag-Connect točke za:

- P4 UART0 TX
- P4 UART0 RX
- GND
- 3V3
- CHIP_PU
- BOOT
- C6 UART TX/RX
- C6 RESET

Preporuka je **Tag-Connect/no-header footprint** ili pogo-pad raspored, kako konektor ne bi ostao u finalnom uređaju.

---

# 16. Test points — obavezni za Rev A

| TP | Net |
|---|---|
| TP1 | VIN_5V |
| TP2 | 5V_SYS |
| TP3 | 3V3_SYS |
| TP4 | P4_VDD_HP |
| TP5 | USB0_VBUS |
| TP6 | USB1_VBUS |
| TP7 | USB0_D+ |
| TP8 | USB0_D- |
| TP9 | USB1_D+ |
| TP10 | USB1_D- |
| TP11 | I2S_BCLK |
| TP12 | I2S_LRCK |
| TP13 | I2S_DATA |
| TP14 | DAC_OUT_L |
| TP15 | DAC_OUT_R |
| TP16 | P4_CHIP_PU |
| TP17 | P4_BOOT |
| TP18 | C6_RESET |
| TP19 | GND power probe |
| TP20 | GND signal probe |

---

# 17. EVT opcionalni power monitor

Za Rev A ostaviti footprint:

| RefDes | Qty | Kandidat | Status |
|---|---:|---|---|
| U_PWRMON | 0/1 | INA226 / INA238 class | **DNP default; EVT option** |
| R_SHUNT | 0/1 | TBD mΩ / ≥1 W depending architecture | EVT option |

Cilj je u firmwareu/logovima moći korelirati brownout, USB hotplug i dual-deck load sa stvarnom 5V_SYS strujom.

---

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
- ESP32-C6-WROOM-1 — aktualni Espressif modul; datasheet v1.4.
- W25Q128JV family — nalazi se u Winbond 2025 product selection guide, mass-production označen.
- ESP32-P4NRW32X — nalazi se u aktualnom ESP32-P4 datasheetu; **prije EVT narudžbe obavezno potvrditi stvarni orderable revision/availability**, jer je dostupna javna P4 dokumentacija i dalje označena kao pre-release.

---

# 21. Rev A schematic lock gates

Prije PCB layouta moraju se zatvoriti:

- [ ] potvrda točnog orderable ESP32-P4 v3.x MPN-a
- [ ] potvrda P4 v3.x TLV62569 reference values/net topology
- [ ] finalni 40 MHz crystal MPN + CL proračun
- [ ] flash compatibility / boot test s W25Q128JV
- [ ] finalni LCD panel i FPC pinout
- [ ] MP3202 LED-string calculation
- [ ] GT911 voltage/INT/RST pinout
- [ ] USB0 actual peak current
- [ ] FLX4 actual USB1 peak/startup current
- [ ] TPS25221 USB0/USB1 RILIM final values from measured device currents
- [ ] TPS25947 system ILIM / dVdt
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
- Winbond W25Q-JV selection / W25Q128JV:  
  https://www.winbond.com/
- MPS MP3202:  
  https://www.monolithicpower.com/en/products/power-management/display-power-and-control/backlight-drivers-wled/mp3202dj-lf-z.html

---

# 23. Zaključak

Ovaj BOM v0.1 već dovoljno precizno zaključava **elektroničku arhitekturu** da se može krenuti u pravi schematic capture, ali namjerno ne glumi finalni manufacturing BOM.

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
```

Najveći preostali hardverski rizici prije layouta ostaju:

1. potvrda stvarne P4 v3.x orderable revizije,
2. finalni LCD/FPC,
3. USB VBUS current-limit dimenzioniranje stvarnim mjerenjem,
4. 5V_SYS transient/brownout margin,
5. konačna mehanika konektora.

**Sljedeći dokument:** `Pajoniiir_Mainboard_Schematic_Plan_v0.1.md`, kojim se ovaj BOM pretvara u hijerarhijske sheetove za KiCad/Altium.
