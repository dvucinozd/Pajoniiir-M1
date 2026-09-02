# Pajoniiir Mainboard — P4 Flash, Clock, Reset & Boot Design v0.1

**Projekt:** Pajoniiir BL-A1800 / Pajoniiir-M1  
**Ploča:** Pajoniiir Mainboard Rev A  
**Blok:** 04_P4_FLASH_CLOCK_RESET  
**Datum:** 2026-09-02  
**Status:** Engineering design candidate — spreman za KiCad capture nakon finalnog symbol/footprint reviewa

---

# 1. Cilj

Ovaj sheet mora omogućiti da potpuno nova Rev A ploča može:

1. stabilno oscilirati na obaveznom 40 MHz crystal clocku,
2. podići ROM bootloader,
3. pristupiti vanjskom 16 MB QSPI flashu,
4. ući u normalni SPI boot,
5. ručno ući u Joint Download Mode,
6. biti flashana i debugirana preko UART0 čak i ako USB/MIPI/periferije još ne rade.

Ovo je minimum-boot platforma cijelog Pajoniiir-M1 hardvera.

---

# 2. External firmware flash

## 2.1 Primarni kandidat

**Winbond W25Q128JVPIQ**

Karakteristike:

- 128 Mbit = 16 MB
- 2.7–3.6 V
- 133 MHz STR
- SPI / Dual SPI / Quad SPI
- WSON-8 6×5 mm
- -40…85 °C
- mass-production family

Alternativa za širi temperaturni raspon:

**W25Q128JVPSQ**

- isti 128 Mbit / Quad SPI koncept
- WSON-8 6×5 mm
- do -40…125 °C family variant

Primary Rev A footprint treba biti kompatibilan s WSON-8 6×5 mm.

---

# 3. P4 ↔ flash mapping

ESP32-P4 dedicated flash interface:

| ESP32-P4 signal | Flash signal |
|---|---|
| FLASH_CS | /CS |
| FLASH_CK | CLK |
| FLASH_D | DI / IO0 |
| FLASH_Q | DO / IO1 |
| FLASH_WP | /WP / IO2 |
| FLASH_HOLD | /HOLD / IO3 |

Net naming:

```text
P4_FLASH_CS
P4_FLASH_CLK
P4_FLASH_D0
P4_FLASH_D1
P4_FLASH_D2
P4_FLASH_D3
```

---

# 4. Flash power

Flash se napaja iz P4 `VDDO_FLASH` raila u 3.3 V režimu.

```text
P4 VDDO_FLASH
      |
      +---- C_VDDO_FLASH = 1uF
      |
      +---- FLASH_VCC
                |
                +---- C_FLASH = 100nF
```

Ne napajati flash neovisnim 3V3 railom mimo P4 VDDO_FLASH arhitekture bez posebnog razloga.

---

# 5. FLASH_CS pull-up

Espressif zahtijeva pull-up na FLASH_CS.

Aktualni Function EV Board koristi:

**10 kΩ**

Rev A:

```text
VDD_FLASH
   |
 10k
   |
P4_FLASH_CS
```

RefDes:

`R_FLASH_CS_PU = 10 kΩ 1%`

Svrha:

- flash ostaje deselectan tijekom power-upa/reset faze,
- deterministički boot state,
- kompatibilnost s Espressif reference designom.

---

# 6. QSPI tuning footprints

Na svih šest flash signalnih vodova predvidjeti series footprint.

Default:

**0 Ω**

```text
P4 ----- 0R ----- FLASH
```

RefDes:

- R_FLASH_CS
- R_FLASH_CLK
- R_FLASH_D0
- R_FLASH_D1
- R_FLASH_D2
- R_FLASH_D3

Package:

0402 preferred.

Razlog:

- edge-rate tuning
- EMI
- ringing
- setup/hold korekcija
- mogućnost kasnije koristiti 10–33 Ω bez PCB respina

Najkritičniji je CLK.

---

# 7. Flash placement

Flash mora biti vrlo blizu P4.

Pravila:

- kratke trase
- minimalni via count
- kontinuirani GND reference
- CLK najkraći i bez nepotrebnih stubova
- 100 nF direktno uz VCC/GND flasha
- 0 Ω tuning footprintovi blizu source/P4 strane ako layout dopušta

Flash ne stavljati između P4 i crystal područja.

---

# 8. 40 MHz crystal — obavezan

ESP32-P4 firmware podržava samo:

**40 MHz crystal**

Točnost prema Espressif smjernici:

**±10 ppm**

Ne koristiti slobodni 40 MHz oscillator module ako želimo slijediti standardni P4 reference design.

---

# 9. Primarni crystal kandidat

**ECS-400-10-37B2-CKY-TR**

Manufacturer: ECS Inc.

Karakteristike:

- 40.000 MHz
- tolerance ±10 ppm
- stability ±10 ppm
- load capacitance 10 pF
- ESR 40 Ω
- operating temperature -30…85 °C
- package 2.0 × 1.6 mm
- fundamental mode

Status za Rev A:

**LOCK-CANDIDATE**

Ako kasnije želimo -40 °C product target, tražiti pin/footprint-compatible ili layout-compatible industrijski alternativni dio s istim 40 MHz / ±10 ppm zahtjevom.

---

# 10. Crystal load capacitor calculation

Crystal ima:

`CL = 10 pF`

Espressif formula:

```text
CL = (C1 × C2)/(C1 + C2) + Cstray
```

Ako koristimo simetrične kondenzatore:

`C1 = C2 = C`

onda:

```text
CL = C/2 + Cstray
```

Za početnu procjenu:

`Cstray ≈ 2.0–2.5 pF`

Dobivamo:

```text
C ≈ 2 × (10pF - 2.0…2.5pF)
C ≈ 15…16pF
```

Rev A početna vrijednost:

**15 pF C0G/NP0, 0402 ×2**

```text
XTAL_P ---- Y1 ---- XTAL_N
   |                   |
 15pF                15pF
   |                   |
  GND                 GND
```

Ovo je početna EVT vrijednost, ne apsolutno finalna.

Finalno treba izmjeriti frequency error na sastavljenoj PCB ploči i po potrebi tuning:

- 12 pF
- 15 pF
- 16 pF
- 18 pF

---

# 11. Crystal series tuning resistor

Predvidjeti:

`R_XTAL_SER = 0 Ω`

na XTAL_P strani, blizu P4.

Svrha:

- damping
- harmonic/EMI tuning
- mogućnost zamjene malim R bez respina

Default:

**0 Ω**

Ne populirati dodatne kapacitivne tuning elemente osim C1/C2 dok mjerenje ne pokaže potrebu.

---

# 12. Crystal PCB constraints

Prema aktualnim ESP32-P4 layout smjernicama:

- complete GND plane ispod crystal/P4 područja,
- clock trase bez via,
- ne routeati digitalne high-speed signale ispod crystala,
- ground copper/via stitching za izolaciju,
- ne postavljati velike induktore blizu,
- series element uz P4 stranu,
- matching capacitors uz crystal ends,
- držati crystal body približno najmanje 4.5 mm od P4 clock pin područja prema aktualnoj P4 layout preporuci, ali trase ostaviti direktne i bez nepotrebnog loopa.

Posebno udaljiti:

- TLV62569 inductor,
- TPS62132 inductor,
- MP3202 backlight inductor,
- USB HS,
- MIPI DSI.

---

# 13. CHIP_PU / RESET

CHIP_PU je već definiran u P4 core bloku, ali fizički RESET tipka pripada minimum-boot pathu.

Rev A:

```text
3V3_SYS
  |
 10k
  |
CHIP_PU -------- SW_RESET -------- GND
  |
 1uF
  |
 GND
```

Vrijednosti:

- R_RESET_PU = 10 kΩ
- C_RESET = 1 µF
- SW_RESET = momentary NO

Espressif minimum:

- power stabilization prije CHIP_PU high: 50 µs
- reset low: ≥1000 µs

---

# 14. Boot strapping pins

ESP32-P4 strapping pins:

- GPIO34
- GPIO35
- GPIO36
- GPIO37
- GPIO38

Boot mode je primarno određen s GPIO35/36:

| Mode | GPIO35 | GPIO36 |
|---|---:|---:|
| SPI boot | 1 | X |
| Joint Download | 0 | 1 |

GPIO37/38 su dodatni strap inputs i istovremeno UART0.

---

# 15. GPIO35 — BOOT

Default mora biti HIGH.

Rev A:

```text
3V3_SYS
  |
 10k
  |
GPIO35 -------- SW_BOOT -------- GND
```

Dakle:

- R_BOOT35_PU = 10 kΩ
- SW_BOOT = momentary NO prema GND

Kad korisnik drži BOOT i resetira/uključi board:

`GPIO35 = 0`

→ Joint Download candidate mode.

Ne stavljati veliki kondenzator na GPIO35.

Espressif izričito upozorava da veliki C može uzrokovati pogrešan boot mode.

---

# 16. GPIO36

Za pouzdan Joint Download Mode:

`GPIO36 = HIGH`

Rev A:

`R_BOOT36_PU = 10 kΩ -> 3V3_SYS`

Time BOOT button treba manipulirati samo GPIO35.

---

# 17. GPIO37 / GPIO38 — UART0 i strap pins

Default UART0:

- GPIO37 = UART0_TXD
- GPIO38 = UART0_RXD

Pošto su istovremeno strap pins:

- bez velikih kapaciteta,
- bez jakih pull-down/up mreža koje bi mijenjale boot state,
- eksterni USB-UART adapter ne smije agresivno voziti pinove tijekom reset sampling intervala.

Preporučeni series resistors:

**33 Ω ×2**

```text
GPIO37 -- 33R --> DEBUG_UART_TX
GPIO38 -- 33R --> DEBUG_UART_RX
```

---

# 18. UART0 service interface

Minimalni servisni header/pogo interface:

```text
GND
3V3_SYS
UART0_TX
UART0_RX
CHIP_PU
GPIO35_BOOT
```

Optional:

`GPIO36_BOOT`

Preporuka:

**Tag-Connect ili pogo pads**, bez trajnog velikog headera.

---

# 19. UART flashing sequence

Za ručni UART download:

1. držati BOOT,
2. resetirati ili power-cycleati,
3. GPIO35 = LOW,
4. GPIO36 = HIGH,
5. ROM ulazi u Joint Download Mode,
6. UART0 ispisuje "waiting for download",
7. esptool/Flash Download Tool programira W25Q128JV,
8. otpustiti BOOT,
9. reset,
10. GPIO35 = HIGH → normal SPI boot.

---

# 20. USB download fallback

ESP32-P4 također može imati USB download path, ali Pajoniiir firmware aktivno koristi USB host funkcije.

Zato **UART0 ostaje obavezni recovery path**.

Možemo dodatno izvesti test pads za USB Serial/JTAG relevantne GPIO-e ako ostanu slobodni, ali finalna ploča ne smije ovisiti samo o USB downloadu.

---

# 21. RTC 32.768 kHz crystal

Za Pajoniiir Rev A:

**ne populirati external RTC crystal**

Razlozi:

- nije potreban za audio playback timing,
- ne donosi bitnu funkciju trenutnom proizvodu,
- štedi BOM i layout,
- GPIO0/GPIO1 ostaju dostupni.

Opcionalni footprint se može potpuno izostaviti.

---

# 22. Minimum boot LED

Preporučuje se jedna servisna LED, ali ne na strap pinu.

Net:

`P4_STATUS_LED`

Odabrati slobodan non-strap GPIO u kasnijem pin-allocation passu.

Ne koristiti GPIO35-38.

LED nije uvjet za ROM boot, ali olakšava factory/bring-up status.

---

# 23. Test points

Obavezno:

```text
TP_CHIP_PU
TP_BOOT_GPIO35
TP_BOOT_GPIO36
TP_UART0_TX
TP_UART0_RX
TP_FLASH_CS
TP_FLASH_CLK
TP_VDD_FLASH
TP_XTAL_P   small RF-safe probe pad only if justified
```

Crystal testpoint treba biti vrlo mali ili DNP probe pad; veliki pad povećava stray C i može poremetiti oscilator.

Za normalnu frequency validaciju preferirati non-invasive active probe.

---

# 24. Preliminary RefDes

| RefDes | Qty | Value / MPN | Status |
|---|---:|---|---|
| U_FLASH | 1 | W25Q128JVPIQ | LOCK-CANDIDATE |
| C_FLASH | 1 | 100 nF X7R | required |
| R_FLASH_CS_PU | 1 | 10 kΩ 1% | required |
| R_FLASH_CS | 1 | 0 Ω | tuning |
| R_FLASH_CLK | 1 | 0 Ω | tuning |
| R_FLASH_D0 | 1 | 0 Ω | tuning |
| R_FLASH_D1 | 1 | 0 Ω | tuning |
| R_FLASH_D2 | 1 | 0 Ω | tuning |
| R_FLASH_D3 | 1 | 0 Ω | tuning |
| Y1 | 1 | ECS-400-10-37B2-CKY-TR | LOCK-CANDIDATE |
| C_XTAL_P | 1 | 15 pF C0G | EVT initial |
| C_XTAL_N | 1 | 15 pF C0G | EVT initial |
| R_XTAL_SER | 1 | 0 Ω | tuning |
| R_CHIP_PU | 1 | 10 kΩ | required |
| C_CHIP_PU | 1 | 1 µF | required |
| SW_RESET | 1 | momentary NO | TBD-MECH |
| R_BOOT35_PU | 1 | 10 kΩ | required |
| R_BOOT36_PU | 1 | 10 kΩ | required |
| SW_BOOT | 1 | momentary NO | TBD-MECH |
| R_UART_TX | 1 | 33 Ω | initial |
| R_UART_RX | 1 | 33 Ω | initial |

---

# 25. KiCad nets

```text
P4_FLASH_CS
P4_FLASH_CLK
P4_FLASH_D0
P4_FLASH_D1
P4_FLASH_D2
P4_FLASH_D3

P4_XTAL_P
P4_XTAL_N

P4_CHIP_PU
P4_BOOT_GPIO35
P4_BOOT_GPIO36

P4_UART0_TX
P4_UART0_RX

VDD_FLASH
3V3_SYS
GND
```

---

# 26. Bring-up measurements

## Crystal

- active probe / frequency counter
- cilj ≈40 MHz
- izmjeriti frequency offset
- tuning C1/C2 po potrebi

## Flash

- ROM boot detekcija
- JEDEC ID read
- erase/write/read
- XIP boot
- Quad mode
- full OTA image test

## Strap

- normal power-up → SPI boot
- BOOT + reset → Joint Download
- 20+ ponavljanja bez slučajnog pogrešnog moda

## UART

- boot log bez corruptiona
- flashing na punoj planiranoj brzini
- reset tijekom UART spojenog adaptera bez strap problema

---

# 27. Acceptance criteria

Sheet prolazi ako:

- crystal starta na svakom cold bootu,
- frequency error je unutar projektiranog ppm budgeta,
- flash je 100% stabilan kroz repeated boot/OTA,
- normal boot nikada slučajno ne ulazi u download mode,
- BOOT tipka pouzdano ulazi u download mode,
- UART0 uvijek daje recovery pristup,
- QSPI nema vidljiv ringing/timing problem na planiranoj frekvenciji.

---

# 28. Layout lock rules

Prije PCB freezea:

- [ ] Y1 exact footprint verified
- [ ] W25Q128JVPIQ WSON pin 1 verified
- [ ] FLASH_CS 10k pull-up
- [ ] 0R on all QSPI lines
- [ ] crystal C1/C2 15pF initial
- [ ] no via in XTAL traces
- [ ] no digital trace under crystal
- [ ] GPIO35 and GPIO36 10k pull-ups
- [ ] no large C on GPIO35
- [ ] UART0 GPIO37/38 not hard-loaded
- [ ] Tag-Connect/pogo pinout documented
- [ ] BOOT and RESET accessible in prototype enclosure

---

# 29. Zaključak

Rev A minimum-boot platforma je sada dovoljno određena:

```text
FLASH:
W25Q128JVPIQ
16 MB
3.3 V
Quad SPI
10k FLASH_CS pull-up
0R tuning on all QSPI lines

CLOCK:
ECS-400-10-37B2-CKY-TR
40 MHz
±10 ppm
CL = 10 pF
15 pF + 15 pF initial load caps
0R series tuning footprint

BOOT:
GPIO35 10k pull-up + BOOT-to-GND
GPIO36 10k pull-up

RESET:
CHIP_PU 10k + 1uF + reset button

RECOVERY:
UART0 TX GPIO37
UART0 RX GPIO38
33R series
Tag-Connect / pogo access
```

**Sljedeći blok:** `05_C6_WIFI` — ESP32-C6-WROOM-1, SDIO/ESP-Hosted, reset/wakeup, 3V3_C6 filtering i RF antenna keep-out.
