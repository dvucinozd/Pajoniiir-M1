# Pajoniiir Mainboard — Schematic Plan v0.1

**Projekt:** Pajoniiir BL-A1800 / Pajoniiir-M1  
**Ploča:** Pajoniiir Mainboard Rev A  
**Repo:** `dvucinozd/Pajoniiir-M1`  
**Datum:** 2026-09-02  
**Status:** Historical schematic architecture/capture plan. Implementation status is superseded by `Pajoniiir_M1_Schematic_Audit_v0.1.md` and the live KiCad project; pre-capture checkboxes below are not current milestone status.

---

# 1. Svrha dokumenta

Ovaj dokument pretvara hardversku arhitekturu i Engineering BOM v0.2 u konkretan plan za crtanje sheme.

Cilj je da KiCad projekt od početka bude:

- hijerarhijski organiziran
- čitljiv
- lako reviewabilan
- pripremljen za ERC
- pripremljen za Rev A bring-up
- pripremljen za DNP varijante
- kompatibilan s postojećim Pajoniiir firmwareom
- pogodan za buduće PCB revizije bez velikog refaktora sheme

Preporučeni CAD alat: **KiCad 9.x ili noviji aktualni stabilni release**.

Predloženi root projekt:

```text
hardware/
└── Pajoniiir-M1/
    ├── Pajoniiir-M1.kicad_pro
    ├── Pajoniiir-M1.kicad_sch
    ├── Pajoniiir-M1.kicad_pcb
    ├── sym-lib-table
    ├── fp-lib-table
    ├── symbols/
    ├── footprints/
    ├── 3d/
    └── docs/
```

---

# 2. Predložena hijerarhija sheme

Root sheet treba biti gotovo isključivo blok dijagram s hijerarhijskim sheetovima.

Predloženi sheetovi:

```text
00_ROOT
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

Preporuka: koristiti prefiks broja kako bi redoslijed sheetova ostao stabilan u KiCadu, PDF exportu i reviewu.

---

# 3. 00_ROOT — system interconnect

Root sheet mora prikazivati samo glavne funkcionalne blokove i globalne power railove.

## 3.1 Blokovi

```text
                        +-------------------+
                        |  01_POWER_INPUT   |
                        | VIN -> eFuse      |
                        +---------+---------+
                                  |
                                5V_SYS
                                  |
             +--------------------+--------------------+
             |                    |                    |
             v                    v                    v
      +-------------+      +-------------+      +-------------+
      | 02_POWER    |      | 06/07 USB   |      | 09 DISPLAY  |
      | 3V3 rails   |      | VBUS power  |      | backlight   |
      +------+------+      +------+------+      +------+------+
             |                    |                    |
           3V3_SYS               5V                LCD_BL
             |
      +------+-----------------------------------------------+
      |                                                      |
      v                                                      v
+-----------+                                        +---------------+
| 03 P4     |<---- QSPI ---- 04 FLASH/CLOCK         | 05 ESP32-C6   |
| CORE      |<---- SDIO ---------------------------->| ESP-HOSTED    |
+-----+-----+                                        +---------------+
      |
      +---- USB0 PHY ------> 06 USB0 STORAGE
      +---- USB1 PHY ------> 07 USB1 FLX4
      +---- I2S -----------> 08 PCM5102A
      +---- MIPI DSI ------> 09 DISPLAY
      +---- I2C -----------> 10 TOUCH
      +---- SDMMC ---------> 11 MICROSD
      +---- UART/GPIO -----> 12 DEBUG
      +---- MONITOR -------> 13 TEST/MONITORING
```

## 3.2 Root-level power nets

Koristiti konzistentne nazive:

- `VIN_5V`
- `5V_PROTECTED`
- `5V_SYS`
- `3V3_SYS`
- `3V3_C6`
- `3V3_AUDIO`
- `P4_VDD_HP`
- `LCD_BL_VOUT`
- `USB0_VBUS`
- `USB1_VBUS`
- `GND`

Ako se kasnije pokaže potreba, dodati:

- `3V3_SD`
- `3V3_LCD`
- `3V3_TOUCH`

ali u Rev A ne treba nepotrebno fragmentirati railove bez električkog razloga.

---

# 4. Naming convention

## 4.1 Digitalni signalni netovi

Koristiti funkcionalne nazive, ne samo GPIO broj.

Primjeri:

```text
P4_USB0_DP
P4_USB0_DM
P4_USB1_DP
P4_USB1_DM

P4_I2S_BCLK
P4_I2S_LRCK
P4_I2S_DOUT

P4_SDMMC_D0
P4_SDMMC_D1
P4_SDMMC_D2
P4_SDMMC_D3
P4_SDMMC_CLK
P4_SDMMC_CMD

P4_C6_SDIO_CLK
P4_C6_SDIO_CMD
P4_C6_SDIO_D0
P4_C6_SDIO_D1
P4_C6_SDIO_D2
P4_C6_SDIO_D3

P4_TOUCH_SDA
P4_TOUCH_SCL
P4_TOUCH_INT
P4_TOUCH_RST

P4_LCD_RST
P4_LCD_BL_PWM
```

GPIO broj staviti u pin label/comment, primjer:

```text
P4_I2S_BCLK   # GPIO50
```

To omogućuje kasniji firmware remap bez preimenovanja cijele sheme.

---

# 5. 01_POWER_INPUT

Ovaj sheet je električki najkritičniji uz USB.

## 5.1 Ulaz

Predloženi ulaz:

```text
J_PWR_IN
5 V regulated
4 A recommended source
```

Konektor: `TBD-MECH`.

Preporučuje se locking tip, ne obični labavi micro-USB/USB-C za osnovno napajanje Rev A.

## 5.2 Power chain

```text
J_PWR_IN
   |
   +-- C_IN_HF
   +-- C_IN_BULK
   |
   +-- TVS
   |
   +-- TPS25947 eFuse
   |
   +--> 5V_PROTECTED / 5V_SYS
```

## 5.3 TPS25947 signali

Izvesti:

- `EFUSE_EN`
- `EFUSE_PG`

Ako nema dovoljno GPIO-a u Rev A, `EFUSE_EN` može biti hardware-on. Za TPS259474A koristiti `EFUSE_PG`/`PGTH`; ova varijanta nema zaseban `FLT` izlaz. `EFUSE_PG` treba dovesti barem na P4 ili test point.

## 5.4 Test points

- TP VIN_5V
- TP 5V_SYS
- TP GND

## 5.5 ERC pravila

- power input označiti `PWR_FLAG`
- output eFusea označiti kao power output
- ne dopustiti drugi izvor na 5V_SYS
- USB VBUS se nikada ne smije direktno vezati natrag na VIN bez switcha

---

# 6. 02_POWER_3V3

U8 = TPS62132RGTR.

## 6.1 Funkcija

```text
5V_SYS
  |
TPS62132
  |
3V3_SYS
```

## 6.2 Consumers

`3V3_SYS` napaja:

- ESP32-P4 I/O/system railove prema referentnoj shemi
- external QSPI flash
- ESP32-C6-WROOM-1
- PCM5102A 3.3 V operation
- GT911 / touch subsystem ako kompatibilno
- microSD
- LCD logic gdje panel to zahtijeva

## 6.3 Layout-sensitive elementi

Na shemi ih grupirati fizičkim redoslijedom:

```text
VIN caps -> U8 -> SW -> L -> output caps -> feedback
```

Ne crtati feedback mrežu daleko od regulatora na shemi jer to otežava review layouta.

## 6.4 Test points

- `TP_3V3_SYS`
- opcionalno `TP_BUCK_SW` samo za laboratorij, jasno označen kao noisy node

---

# 7. 03_P4_CORE

Ovo je glavni sheet za ESP32-P4.

## 7.1 U1

`ESP32-P4NRW32X`

Prije capturea finalne sheme potvrditi:

- v3.x pinout
- VDD_HP_1 razliku u odnosu na staru v1.3 ploču
- sve power pinove
- exposed pad / GND requirements
- PSRAM in-package konfiguraciju

## 7.2 Funkcionalne grupe pinova

Na custom KiCad simbolu pinove grupirati po funkciji:

1. power
2. reset/strapping
3. USB HS
4. USB FS
5. MIPI DSI
6. flash interface
7. SDMMC
8. C6 SDIO
9. I2S audio
10. I2C touch
11. UART/debug
12. misc GPIO

## 7.3 GPIO assignment baseline

### Audio

- GPIO50 = I2S BCLK
- GPIO52 = I2S LRCK/WS
- GPIO51 = I2S DATA

### Touch

- GPIO3 = RST
- GPIO4 = INT
- GPIO7 = SDA
- GPIO8 = SCL

### microSD

- GPIO39 = D0
- GPIO40 = D1
- GPIO41 = D2
- GPIO42 = D3
- GPIO43 = CLK
- GPIO44 = CMD

### LCD

- GPIO5 = LCD RESET
- GPIO6 = optional TE
- GPIO23 = BACKLIGHT PWM

### C6 SDIO

- GPIO18 = CLK
- GPIO19 = CMD
- GPIO14 = D0
- GPIO15 = D1
- GPIO16 = D2
- GPIO17 = D3
- GPIO54 = C6 RESET

### USB power control

- GPIO20 = USB0 EN
- GPIO21 = USB0 FAULT_N
- GPIO22 = USB1 EN
- GPIO32 = USB1 FAULT_N

### microSD control

- GPIO45 = SD_PWR_EN
- GPIO46 = optional CARD_DETECT

### Audio mute

- GPIO49 = PCM5102A XSMT

### Monitoring

- GPIO53 = optional INA238 ALERT

## 7.4 Reserved GPIO table

U schematic notes dodati tablicu:

| GPIO | Rev A funkcija | Status |
|---|---|---|
| 5 | LCD_RST | locked |
| 7 | TOUCH_SDA | locked |
| 8 | TOUCH_SCL | locked |
| 14 | C6_SDIO_D0 | locked |
| 15 | C6_SDIO_D1 | locked |
| 16 | C6_SDIO_D2 | locked |
| 17 | C6_SDIO_D3 | locked |
| 18 | C6_SDIO_CLK | locked |
| 19 | C6_SDIO_CMD | locked |
| 23 | LCD_BL_PWM | locked |
| 39 | SD_D0 | locked |
| 40 | SD_D1 | locked |
| 41 | SD_D2 | locked |
| 42 | SD_D3 | locked |
| 43 | SD_CLK | locked |
| 44 | SD_CMD | locked |
| 50 | I2S_BCLK | locked |
| 51 | I2S_DATA | locked |
| 52 | I2S_LRCK | locked |
| 54 | C6_RESET | tentative-v3.x check |

Posebno provjeriti GPIO54/v3.x mapiranje prije schematic locka.

---

# 8. P4 VDD_HP core regulator

Može biti na `03_P4_CORE` ili kao pod-sheet.

Preporuka: ostaviti ga unutar P4 sheeta jer je električki dio SoC-a.

## 8.1 U3

TLV62569DRLR

## 8.2 Netovi

- input = `3V3_SYS`
- output = `P4_VDD_HP`
- feedback = lokalni netovi
- GND = solid GND

## 8.3 V3.x rule

Schematic comment:

> DO NOT COPY JC4880 P4 REV1.3 CORE DCDC VALUES. USE CURRENT ESPRESSIF V3.X REFERENCE NETWORK.

## 8.4 Test point

`TP_P4_VDD_HP`

---

# 9. 04_P4_FLASH_CLOCK_RESET

Namjerno odvojeno od glavnog P4 simbola zbog preglednosti.

## 9.1 QSPI flash

U2 = W25Q128JVPIQ candidate.

Netovi:

- `FLASH_CS`
- `FLASH_CLK`
- `FLASH_D0`
- `FLASH_D1`
- `FLASH_D2`
- `FLASH_D3`

Serijski 0 Ω footprints uz P4 ili flash, prema layout izboru.

## 9.2 40 MHz crystal

- Y1 = 40 MHz ±10 ppm
- Cload TBD nakon odabira MPN-a
- kratki netovi `XTAL_P`, `XTAL_N`

## 9.3 Reset

- 10 kΩ pull-up
- 1 µF prema GND
- RESET switch
- test point

## 9.4 BOOT

- strap prema aktualnom P4 reference designu
- BOOT switch
- test point

---

# 10. 05_C6_WIFI

U4 = ESP32-C6-WROOM-1-N4 candidate.

## 10.1 Interfaces

### P4 ↔ C6 SDIO

- CLK
- CMD
- D0-D3

### Control

- C6_RESET
- optional HOST_WAKE
- optional SLAVE_WAKE ako ESP-Hosted topologija bude zahtijevala

### Debug

- C6 UART TX
- C6 UART RX
- C6 EN

## 10.2 Antenna

Na shemi staviti velik note:

> MODULE ANTENNA KEEP-OUT REQUIRED ON PCB. NO COPPER, TRACES OR METAL UNDER ANTENNA REGION.

## 10.3 Power

Poželjno odvojiti net label:

`3V3_C6`

U početku može biti spojen preko 0 Ω / ferrite bead na `3V3_SYS`.

To daje mogućnost kasnije dodati EMI filtriranje bez PCB respina.

Predloženo:

```text
3V3_SYS -- FB_C6 / 0R --> 3V3_C6
```

---

# 11. 06_USB0_STORAGE

USB0 = High-Speed root za Rekordbox storage.

## 11.1 Data path

```text
ESP32-P4 HS USB PHY
      |
   D+ / D-
      |
 optional 0R tuning
      |
 low-C ESD
      |
 USB-A receptacle
```

## 11.2 Power path

```text
5V_SYS
  |
TPS25221 x2 CH1
  |
USB0_VBUS
  |
USB-A VBUS
```

## 11.3 Signals to P4

- `USB0_PWR_EN`
- `USB0_FAULT_N`

## 11.4 Connector shield

Ne vezati mehanički shield naslijepo direktno u signal GND bez razmišljanja.

Za Rev A predvidjeti opciju:

- direct GND via 0 Ω
- RC/chassis coupling footprint

ovisno o EMC strategiji.

## 11.5 Test

- VBUS TP
- D+ TP
- D- TP
- fault TP

---

# 12. 07_USB1_FLX4

USB1 = DDJ-FLX4.

Funkcije:

- MIDI IN
- MIDI OUT
- LED feedback
- USB Audio Class
- CUE/PFL channels 3/4

## 12.1 Data path

```text
ESP32-P4 FS USB
 |
22R / 22R initial
 |
ESD
 |
USB-A receptacle
 |
USB-A -> USB-C cable
 |
DDJ-FLX4
```

## 12.2 Power

TPS25221 x2 channel 2.

Netovi:

- `USB1_PWR_EN`
- `USB1_FAULT_N`
- `USB1_VBUS`

## 12.3 Critical validation

USB1 power path mora podnijeti:

- FLX4 enumeration
- LED activity
- MIDI
- 4ch UAC
- reconnect
- startup transient

bez brownouta P4.

---

# 13. TPS25221 x2 shared implementation

Iako se USB sheetovi prikazuju odvojeno, U6 može fizički biti na jednom sheetu.

Preporuka:

- U6 staviti na `06_USB0_STORAGE`
- CH1 = USB0
- CH2 = USB1
- na `07_USB1_FLX4` dovesti hijerarhijske netove

Alternativa: napraviti zaseban `06_USB_POWER` sheet.

Ako KiCad projekt krene rasti, bolja finalna hijerarhija je:

```text
06_USB_POWER
07_USB0_STORAGE
08_USB1_FLX4
```

i ostale sheetove pomaknuti za +1.

Za Rev A preporučujem upravo ovu varijantu jer jasno odvaja power od signal integrity dijela.

---

# 14. 08_AUDIO_PCM5102A

U5 = PCM5102APWR.

## 14.1 I²S input

- `P4_I2S_BCLK`
- `P4_I2S_LRCK`
- `P4_I2S_DOUT`

MCLK = NC / not used.

## 14.2 DAC control

Izvesti:

- `DAC_XSMT`

FMT i FLT mogu biti strapirani, ali ostaviti 0 Ω / resistor selection mogućnost.

## 14.3 Power

Preporučeni pristup:

```text
3V3_SYS
 |
ferrite bead / 0R
 |
3V3_AUDIO
 |
PCM5102A
```

Time se analogni DAC ne napaja direktno s najbučnijeg digitalnog raila bez mogućnosti filtriranja.

## 14.4 Analog outputs

```text
PCM5102A OUTL
  |
470R
  +---- RCA_L
  |
2.2nF
  |
GND

PCM5102A OUTR
  |
470R
  +---- RCA_R
  |
2.2nF
  |
GND
```

Točan položaj RC mreže u odnosu na konektor treba uskladiti s TI Figure 33 referentnom topologijom.

## 14.5 DNP 3.5 mm out

Ako ostavimo opcionalni stereo jack:

- vezati ga nakon RC mreže
- footprint DNP u Rev A
- ne smije opteretiti RCA signal pri DNP stanju

---

# 15. 09_DISPLAY_MIPI

## 15.1 MIPI differential pairs

Netovi:

- `DSI_CLK_P`
- `DSI_CLK_N`
- `DSI_D0_P`
- `DSI_D0_N`
- `DSI_D1_P`
- `DSI_D1_N`

## 15.2 Control

- LCD_RST
- LCD_BL_PWM

## 15.3 Required analog/PHY support

- MIPI PHY decoupling
- DSI_REXT = 4.02 kΩ
- 0 Ω tuning footprints na svim DSI pair signalima samo ako ih layout i reference design opravdavaju

## 15.4 FPC

J_LCD ostaje TBD dok se ne zaključa točan panel.

Na shemi obavezno dokumentirati:

- FPC pitch
- contact side
- pin 1 orientation
- LED+ / LED-
- logic voltage
- touch signals ako dijele FPC

Bez ovoga PCB ne smije u layout freeze.

---

# 16. LCD backlight

U_BL = MP3202DJ-LF-Z candidate.

## 16.1 Input

5V_SYS.

## 16.2 Control

`LCD_BL_PWM` s GPIO23.

Ako MP3202 EN/PWM zahtijeva specifičnu logiku ili level, uključiti buffer samo ako datasheet/measurement pokaže potrebu.

## 16.3 Output

`LCD_BL_VOUT` prema LED stringu.

## 16.4 Lock condition

Ne zaključavati:

- inductor
- diode
- sense resistor
- OVP network

dok nije poznat finalni LCD LED string.

---

# 17. 10_TOUCH_GT911

## 17.1 Interface

- SDA = GPIO7
- SCL = GPIO8
- INT = odabrati slobodan P4 GPIO
- RESET = odabrati slobodan P4 GPIO

INT/RST pinovi trebaju biti firmware-configurable.

## 17.2 Pull-ups

Početno 4.7 kΩ, ali finalna vrijednost ovisi o:

- FPC dužini
- I2C frekvenciji
- bus capacitance

## 17.3 Address selection

GT911 reset/INT sequencing može utjecati na adresu.

Na shemi i firmwareu treba eksplicitno dokumentirati željenu 0x5D konfiguraciju.

---

# 18. 11_MICROSD

## 18.1 SDMMC 4-bit

- D0 GPIO39
- D1 GPIO40
- D2 GPIO41
- D3 GPIO42
- CLK GPIO43
- CMD GPIO44

## 18.2 Pull-ups

Predvidjeti pull-up na:

- CMD
- D0
- D1
- D2
- D3

Početna vrijednost 10 kΩ, finalno prema Espressif SDMMC preporuci.

## 18.3 CLK tuning

R_SD_CLK = 22 Ω initial.

Ostaviti 0402/0603 footprint blizu P4.

## 18.4 Optional power cycle

`SD_PWR_EN` kroz load switch ili P-MOSFET može biti DNP u Rev A, ali footprint je koristan.

---

# 19. 12_DEBUG_SERVICE

Rev A treba biti servisabilan bez lemljenja žica na fine pitch pinove.

## 19.1 P4 UART

- TX
- RX
- GND
- 3V3
- CHIP_PU
- BOOT

## 19.2 C6 debug

- TX
- RX
- EN
- RESET
- GND

## 19.3 USB Serial/JTAG

Ako P4 dedicated USB Serial/JTAG pinovi nisu zauzeti active topologyjem, predvidjeti test pads ili optional connector.

Ne uvoditi novi vanjski USB connector samo radi JTAG-a ako otežava finalnu mehaniku.

## 19.4 Connector

Preferred:

- Tag-Connect footprint
- pogo pads

Ne preferirati stalni 2.54 mm header na finalnom proizvodu.

---

# 20. 13_TEST_MONITORING

Ovaj sheet sadrži samo EVT/DVT opcije.

## 20.1 Current monitor

INA226/INA238 class.

Mjeri:

- 5V_SYS
- total system current

DNP default.

## 20.2 Optional divider rails

Može se omogućiti P4 ADC mjerenje:

- 5V_SYS divider
- USB0_VBUS divider
- USB1_VBUS divider

Ako ima dovoljno ADC resursa.

To daje firmware telemetry bez skupljeg current monitor IC-a.

## 20.3 Testpoint matrix

Na sheetu definirati sve TP oznake i funkcije.

---

# 21. 14_DNP_OPTIONS

Ovaj sheet sadrži stvari koje ne želimo u Rev A populaciji, ali mogu biti korisne za eksperiment.

Primjeri:

- optional 3.5 mm line out
- optional SD load switch
- optional current monitor
- optional reset supervisor
- optional EMI ferrite beads
- optional shield RC network
- optional status RGB LED

Ne stavljati ovdje obsolete funkcije poput S3, ES8311, camera ili RS485.

Njih uopće ne treba nositi u novu shemu.

---

# 22. Net classes za budući PCB

Iako je ovo schematic plan, net classes treba planirati prije layouta.

Predložene klase:

## USB_HS

- 90 Ω differential
- D+/D-
- tight pair
- low via count

## USB_FS

- differential pair
- manje strogo od HS, ali i dalje kontrolirano

## MIPI_DSI

- differential pair
- impedance prema Espressif/board stackup recommendation
- strict length matching unutar para
- međupair matching prema DPHY budgetu

## QSPI_FLASH

- kratko
- low stub
- matching po potrebi

## SDIO_C6

- kratko
- CLK kontroliran
- data/cmd matching prema SDIO timing budgetu

## SDMMC

- CLK kritičan
- D0-D3/CMD grupirani

## I2S

- BCLK/LRCK/DATA
- držati dalje od analog outputa

## ANALOG_AUDIO

- OUTL/OUTR
- no switching cross
- minimal loop area

## POWER_5V_HIGH

- 5V_SYS
- USB0_VBUS
- USB1_VBUS
- dimenzionirati za current + transient margin

---

# 23. ERC rules

## 23.1 Power flags

Dodati samo gdje je stvarno potrebno.

Ne “gasiti” ERC upozorenja naslijepo.

## 23.2 No-connect pins

Svaki NC pin eksplicitno označiti NC.

## 23.3 DNP

DNP elementi trebaju imati:

- `DNP` property
- BOM exclude flag gdje je potrebno
- jasno objašnjenje čemu služe

## 23.4 Active-low naming

Koristiti suffix:

`_N`

Primjeri:

- USB0_FAULT_N
- USB1_FAULT_N
- C6_RESET_N samo ako signal stvarno jest active-low

---

# 24. KiCad symbol strategy

## 24.1 Koristiti official symbols gdje postoje

Za generičke R/C/L i standardne IC-e.

## 24.2 Custom verified symbols

Obavezno ručno verificirati:

- ESP32-P4NRW32X
- ESP32-C6-WROOM-1-N4
- exact LCD connector
- exact USB connectors
- exact RCA
- exact microSD socket

Pin 1 i exposed pad greške su kritične.

## 24.3 Symbol review checklist

Za svaki custom IC:

- pin count
- pin number
- pin name
- electrical type
- power pins
- NC
- exposed pad
- footprint mapping

Ne koristiti community symbol bez usporedbe s originalnim datasheetom.

---

# 25. Footprint strategy

Prije povezivanja footprinta treba imati “footprint lock” listu.

## Must verify

- U1 ESP32-P4 package revision
- U2 WSON flash
- U3 TLV62569 DRL
- U4 ESP32-C6-WROOM
- U5 PCM5102A TSSOP
- U6 TPS25221 x2 DRC
- U7 TPS25947 RPW
- U8 TPS62132 RGT
- U9 MP3202 DJ
- LCD FPC
- USB-A ×2
- RCA ×2
- SD socket
- DC input

Za svaki footprint spremiti link na manufacturer mechanical drawing u property `Datasheet`.

---

# 26. Schematic design review gates

## Gate A — architecture

Prije crtanja:

- [x] P4-only arhitektura
- [x] PCM5102A MAIN
- [x] FLX4 CUE/UAC
- [x] dual USB
- [x] C6 SDIO
- [x] MIPI display
- [x] microSD

## Gate B — component lock

Prije finalnog capturea:

- [ ] P4 exact orderable v3.x MPN
- [ ] exact crystal
- [ ] exact LCD
- [ ] exact connectors
- [ ] final USB ILIM
- [ ] final backlight values

## Gate C — ERC

- [ ] zero unexplained ERC errors
- [ ] zero floating power pins
- [ ] every NC intentional
- [ ] every DNP intentional

## Gate D — pre-layout

- [ ] net classes assigned
- [ ] differential pairs named correctly
- [ ] connector pin 1 verified
- [ ] all test points included
- [ ] all debug nets included

---

# 27. Schematic bring-up sequence

Rev A board ne treba paliti “sve odjednom”.

## Phase 1 — naked power

Bez P4 firmware aktivnosti potvrditi:

- VIN
- eFuse output
- 3V3
- P4 core rail
- no abnormal current
- no hot component

## Phase 2 — P4 boot

Provjeriti:

- 40 MHz clock
- reset
- boot strap
- QSPI flash
- UART log

## Phase 3 — display/touch

- DSI output
- backlight
- touch I2C

## Phase 4 — microSD

- init
- read/write
- hot/reinsert behavior

## Phase 5 — PCM5102A

- BCLK
- LRCK
- DATA
- analog L/R
- noise floor

## Phase 6 — C6 Wi-Fi

- SDIO enumeration
- ESP-Hosted
- Wi-Fi
- web UI

## Phase 7 — USB0

- VBUS enable
- storage enumerate
- MP3 playback

## Phase 8 — USB1

- FLX4 enumerate
- MIDI
- LED
- UAC

## Phase 9 — combined load

- full backlight
- Wi-Fi
- USB0
- USB1
- dual-deck audio
- multi-hour soak

---

# 28. Brownout-specific design review

S obzirom na prototip, svaki schematic review mora posebno provjeriti:

1. Je li 5V_SYS topologija dovoljno niskoimpedantna?
2. Ima li USB0 vlastiti lokalni bulk C?
3. Ima li USB1 vlastiti lokalni bulk C?
4. Je li TPS25221 x2 input dovoljno dobro bypassan?
5. Je li 3V3 buck odvojen od USB VBUS load transienta?
6. Je li P4 core regulator lokalno pravilno decouplan?
7. Ima li input eFuse soft-start koji ne uzrokuje spor/pogrešan startup?
8. Postoji li dovoljno velik ulazni bulk reservoir?
9. Je li ground return USB powera odvojen fizički od osjetljivog audio dijela?
10. Mogu li se svi railovi mjeriti test pointovima?

---

# 29. Audio-specific design review

1. PCM5102A mora biti blizu RCA konektora.
2. I2S ne voditi uz analog output.
3. Backlight SW node daleko od audio područja.
4. P4 core DCDC daleko od RCA input/output trase.
5. RCA ground return direktno i široko prema GND planeu.
6. 3V3_AUDIO filter/0R option obavezno.
7. XSMT mora imati determinističko stanje na bootu.
8. Ne smije biti pop/glitch zbog floating control pina.

---

# 30. USB-specific design review

1. USB0 HS pair bez stuba.
2. USB0 ESD tik uz connector.
3. USB1 series R bliže source strani.
4. VBUS trace dimenzioniran na najmanje 1 A + margin.
5. TPS25221 x2 thermal pad layout po datasheetu.
6. FAULT pinovi imaju pull-up.
7. EN pinovi imaju definiran boot state.
8. shield strategy dokumentirana.
9. nema backfeed patha.
10. svaki port može se fizički power-cycleati.

---

# 31. MIPI-specific design review

1. DSI pair pinout potvrđen s LCD FPC datasheetom.
2. Pair polarity potvrđen.
3. lane0/lane1 mapping potvrđen.
4. DSI_REXT vrijednost i pin potvrđeni.
5. MIPI DPHY decoupling neposredno uz P4.
6. pair impedance definiran prema stackupu.
7. bez layer transitiona gdje nije nužno.
8. bez split planea ispod MIPI parova.
9. backlight power udaljen od DSI parova.

---

# 32. Recommended first KiCad files

Prvi konkretni commit nakon ovog plana trebao bi sadržavati:

```text
hardware/Pajoniiir-M1/
├── Pajoniiir-M1.kicad_pro
├── Pajoniiir-M1.kicad_sch
├── sheets/
│   ├── 01_POWER_INPUT.kicad_sch
│   ├── 02_POWER_3V3.kicad_sch
│   ├── 03_P4_CORE.kicad_sch
│   ├── 04_P4_FLASH_CLOCK_RESET.kicad_sch
│   ├── 05_C6_WIFI.kicad_sch
│   ├── 06_USB_POWER.kicad_sch
│   ├── 07_USB0_STORAGE.kicad_sch
│   ├── 08_USB1_FLX4.kicad_sch
│   ├── 09_AUDIO_PCM5102A.kicad_sch
│   ├── 10_DISPLAY_MIPI.kicad_sch
│   ├── 11_TOUCH_GT911.kicad_sch
│   ├── 12_MICROSD.kicad_sch
│   ├── 13_DEBUG_SERVICE.kicad_sch
│   ├── 14_TEST_MONITORING.kicad_sch
│   └── 15_DNP_OPTIONS.kicad_sch
├── symbols/
├── footprints/
└── docs/
```

Napomena: stvarni KiCad hijerarhijski sheet file layout treba potvrditi s načinom na koji KiCad sprema child sheet reference; struktura iznad je organizacijski cilj, ne razlog za ručno uređivanje KiCad S-expression datoteka.

---

# 33. Definition of Done za Schematic Rev A

Shema je spremna za PCB tek kad:

- svaki blok ima izvor i potrošač napajanja
- svaka naponska domena je dokumentirana
- svaki P4 pin ima poznatu funkciju ili NC
- P4 revizija je finalno potvrđena
- svi power regulator values su zaključani
- dual USB VBUS je dimenzioniran
- flash MPN je potvrđen
- LCD/FPC je finalan
- touch pinout je finalan
- RCA/USB/SD/DC footprints su mehanički potvrđeni
- ERC nema neobjašnjene greške
- BOM je reproducibilan
- test points pokrivaju sve kritične railove i busove
- schematic review je odrađen protiv datasheetova, ne samo protiv prethodne development ploče

---

# 34. Sljedeći konkretni korak

Nakon ovog plana treba prijeći s dokumentacije na stvarni ECAD projekt.

Preporučeni redoslijed capturea:

1. `01_POWER_INPUT`
2. `02_POWER_3V3`
3. `03_P4_CORE`
4. `04_P4_FLASH_CLOCK_RESET`
5. `06_USB_POWER`
6. `07_USB0_STORAGE`
7. `08_USB1_FLX4`
8. `09_AUDIO_PCM5102A`
9. `05_C6_WIFI`
10. `12_MICROSD`
11. `10_DISPLAY_MIPI`
12. `11_TOUCH_GT911`
13. `13_DEBUG_SERVICE`
14. `14_TEST_MONITORING`
15. `15_DNP_OPTIONS`

Razlog za ovaj redoslijed je da se najprije zaključa power integrity i P4 minimum-boot platforma, zatim USB/audio koji su ključni za samu funkciju Pajoniiira, a tek onda display i pomoćni blokovi.

---

# 35. Zaključak

Pajoniiir-M1 shemu treba projektirati kao **namjenski embedded audio/USB proizvod**, a ne kao smanjenu kopiju JC4880 development boarda.

Najvažnije arhitekturne odluke ovog plana su:

- jedan ESP32-P4 kao glavni procesor
- zaseban ESP32-C6 modul samo za radio/network funkcije
- vlastiti robustan 5V power tree
- dva fizički neovisno switchana USB VBUS kanala
- integrirani PCM5102A
- direktni MIPI DSI display
- direktni GT911 touch
- microSD preko native SDMMC
- puna bring-up i test infrastruktura
- bez S3/ES8311/camera/RS485 legacy sklopova

Time Rev A ostaje dovoljno jednostavan za proizvodnju, ali dovoljno instrumentiran da možemo precizno pronaći svaki problem tijekom prvog hardware bring-upa.

**Sljedeća faza:** izrada stvarnog KiCad projekta i prvog sheeta `01_POWER_INPUT`.
