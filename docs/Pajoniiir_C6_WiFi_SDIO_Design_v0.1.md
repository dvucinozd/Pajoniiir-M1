# Pajoniiir Mainboard — ESP32-C6 Wi-Fi / ESP-Hosted SDIO Design v0.1

**Projekt:** Pajoniiir BL-A1800 / Pajoniiir-M1  
**Ploča:** Pajoniiir Mainboard Rev A  
**Blok:** 05_C6_WIFI  
**Datum:** 2026-09-02  
**Status:** Captured in KiCad; RF placement and enclosure validation remain open

---

# 1. Uloga C6 u Pajoniiiru

ESP32-P4 nema integrirani Wi-Fi/Bluetooth radio.

Pajoniiir zato koristi zaseban ESP32-C6 kao mrežni koprocesor preko ESP-Hosted SDIO transporta.

C6 ne izvršava glavni Pajoniiir application firmware. Njegove uloge su:

- Wi-Fi radio
- ESP-Hosted co-processor
- SoftAP / network transport prema P4
- budući BLE/802.15.4 samo ako proizvod kasnije zatraži

Glavni application procesor ostaje ESP32-P4.

---

# 2. Primarni modul

**ESP32-C6-WROOM-1-N4**

Razlozi:

- integrirani ESP32-C6
- 4 MB flash dovoljno za ESP-Hosted slave firmware
- integrirani 40 MHz crystal
- integrirani RF matching
- integrirana PCB antena
- certificirani modul značajno smanjuje RF rizik vlastite ploče
- module footprint je praktičniji od bare-C6 RF implementacije

Alternativa ako kućište/LCD metalni okvir degradira PCB antenu:

**ESP32-C6-WROOM-1U-N4**

s vanjskom U.FL/I-PEX/MHF antenom.

---

# 3. C6 power supply

ESP32-C6-WROOM-1 radi na:

```text
3.0 V ... 3.6 V
3.3 V nominal
```

Espressif preporučuje da vanjski izvor može isporučiti najmanje:

**0.5 A**

Wi-Fi peak current prema aktualnom datasheetu doseže približno:

**382 mA**

za 802.11b TX pri visokoj izlaznoj snazi.

Zato C6 ne treba napajati kroz slabi LDO ili tanku signalnu stazu.

---

# 4. 3V3_C6 rail

Predložena topologija:

```text
3V3_SYS
   |
 FB_C6 / 0R
   |
 3V3_C6
   |
   +---- 22uF local bulk
   +---- 10uF local bulk
   +---- 100nF HF
   |
 ESP32-C6-WROOM-1
```

Default Rev A:

`FB_C6 = 0 Ω`

Footprint mora dopustiti kasniju zamjenu ferrite beadom ako EMI mjerenje pokaže korist.

C6 power trace projektirati za najmanje 0.5 A s marginom.

---

# 5. Local decoupling

Uz module pin 3V3:

| RefDes | Value |
|---|---:|
| C_C6_HF | 100 nF |
| C_C6_LOCAL | 10 µF |
| C_C6_BULK | 22 µF |

22 µF nije striktno minimalni datasheet zahtjev, nego Pajoniiir transient reservoir za Wi-Fi TX burst.

Sve mora biti blizu 3V3/GND module pinova.

---

# 6. C6 EN / reset

C6 module EN:

- HIGH = enabled
- LOW = reset/off
- ne smije floating

Espressif preporučuje tipični EN RC:

```text
R = 10 kΩ
C = 1 µF
```

Pajoniiir:

```text
3V3_C6
   |
 10k
   |
C6_EN ---------------- P4 GPIO54
   |
 1uF
   |
  GND
```

Netovi:

```text
C6_EN
P4_C6_RESET
```

P4 GPIO54 mora moći povući EN LOW radi resetiranja C6.

Predvidjeti 0 Ω series footprint između P4 GPIO54 i C6_EN:

`R_C6_RESET_SER = 0 Ω`

To omogućuje izoliranje C6 tijekom bring-upa.

---

# 7. ESP-Hosted SDIO topology

Koristi se:

- SDIO Slot 1 na P4
- 4-bit bus
- 3.3 V IO
- P4 kao SDIO host
- C6 kao SDIO slave/co-processor

Current firmware već koristi:

```text
CONFIG_ESP_HOSTED_SDIO_HOST_INTERFACE=y
CONFIG_ESP_HOSTED_SDIO_SLOT_1=y
CONFIG_ESP_HOSTED_SDIO_4_BIT_BUS=y
CONFIG_ESP_HOSTED_P4_DEV_BOARD_FUNC_BOARD=y
```

P4 Function-EV-Board mapping koji koristi ESP-Hosted potpuno se poklapa s Pajoniiir firmwareom.

---

# 8. P4 ↔ C6 SDIO pin mapping

| SDIO signal | ESP32-P4 | ESP32-C6-WROOM-1 |
|---|---:|---:|
| CLK | GPIO18 | GPIO19 / module pin 17 |
| CMD | GPIO19 | GPIO18 / module pin 16 |
| DAT0 | GPIO14 | GPIO20 / module pin 18 |
| DAT1 | GPIO15 | GPIO21 / module pin 19 |
| DAT2 | GPIO16 | GPIO22 / module pin 20 |
| DAT3 | GPIO17 | GPIO23 / module pin 21 |
| RESET | GPIO54 | EN / module pin 3 |
| GND | GND | GND |

Net naming:

```text
P4_C6_SDIO_CLK
P4_C6_SDIO_CMD
P4_C6_SDIO_D0
P4_C6_SDIO_D1
P4_C6_SDIO_D2
P4_C6_SDIO_D3
P4_C6_RESET
```

---

# 9. External SDIO pull-ups — mandatory

ESP-Hosted zahtijeva vanjske pull-up otpornike na:

- CMD
- DAT0
- DAT1
- DAT2
- DAT3

Preporučena vrijednost:

**51 kΩ**

Rev A:

```text
R_SDIO_CMD_PU = 51.1 kΩ 1%
R_SDIO_D0_PU  = 51.1 kΩ 1%
R_SDIO_D1_PU  = 51.1 kΩ 1%
R_SDIO_D2_PU  = 51.1 kΩ 1%
R_SDIO_D3_PU  = 51.1 kΩ 1%
```

Pull-upovi idu na:

`3V3_C6 / common 3.3 V SDIO logic domain`

CLK nema pull-up.

Važno: čak i kada se SDIO privremeno debugira u 1-bit modu, DAT2 i DAT3 pull-upovi moraju ostati jer C6 bez njih može pri startupu pogrešno ući u SPI-mode interpretaciju.

---

# 10. SDIO series termination

Za Rev A koristiti tuning footprintove.

Početna konfiguracija:

```text
CLK  = 22 Ω
CMD  = 0 Ω
D0   = 0 Ω
D1   = 0 Ω
D2   = 0 Ω
D3   = 0 Ω
```

RefDes:

- R_SDIO_CLK
- R_SDIO_CMD
- R_SDIO_D0
- R_SDIO_D1
- R_SDIO_D2
- R_SDIO_D3

Ako SI/EMI mjerenje pokaže ringing:

- CMD/DAT se mogu promijeniti na 10–33 Ω
- CLK se može tuningom prilagoditi

Series elemente postaviti blizu host/source P4 strane.

---

# 11. SDIO clock

Current ESP-Hosted P4 configuration koristi:

**40 MHz**

kao uobičajeni optimized target.

Bring-up sequence:

1. 5 MHz ili 10 MHz
2. potvrditi stabilan link
3. 20 MHz
4. 40 MHz
5. iperf/stress validation

Ne počinjati debug na maksimumu ako 4-bit link ne enumerira.

---

# 12. SDIO PCB routing

SDIO nije USB/MIPI differential bus, ali je high-speed synchronous parallel bus.

Pravila:

- sve linije kratke
- CLK posebno čist
- kontinuirani GND plane
- bez ground splitova
- minimalni via count
- držati CMD/DAT grupu približno slične dužine
- izbjegavati duge stubove na pull-upovima/test pointovima
- 4-layer PCB minimum
- ne routeati SDIO ispod C6 antenne

Za prvi layout cilj:

```text
P4 -> series resistors -> short grouped SDIO traces -> C6
```

Pull-upove postaviti uz bus/C6 područje bez velikih stubova.

---

# 13. Dedicated Data Ready GPIO

Za Pajoniiir Rev A **ne dodajemo zaseban SDIO Data-Ready GPIO**.

Current ESP-Hosted P4+C6 SDIO konfiguracija koristi:

- standardne SDIO linije
- zasebni RESET signal
- SDIO protocol interrupt mehanizam

To smanjuje GPIO usage i ostaje kompatibilno sa službenim P4 Function-EV-Board setupom.

Ako buduća ESP-Hosted revizija uvede dodatni optional wake/data-ready signal, može se dodati kroz rezervni test/aux GPIO u Rev B.

---

# 14. C6 direct programming/debug

Iako ESP-Hosted može kasnije nadograđivati C6 slave firmware preko hosta, Rev A mora omogućiti direktan C6 recovery.

Potrebni test pads:

```text
C6_UART_TX
C6_UART_RX
C6_EN
C6_GPIO8
C6_GPIO9
3V3_C6
GND
```

Module pinovi:

- TXD0 module pin 25 = C6 GPIO16
- RXD0 module pin 24 = C6 GPIO17

---

# 15. C6 boot strapping

C6 boot mode kontroliraju:

- GPIO8
- GPIO9

Normal SPI boot:

```text
GPIO9 = HIGH
GPIO8 = don't care
```

Joint Download Boot:

```text
GPIO8 = HIGH
GPIO9 = LOW
```

GPIO9 ima interni weak pull-up, ali za proizvodni recovery path predlažemo eksplicitne otpornike.

---

# 16. C6 manufacturing boot network

Rev A:

```text
3V3_C6 -- 10k --> C6_GPIO8

3V3_C6 -- 10k --> C6_GPIO9
                    |
                  TP/BOOT
                    |
                   GND
```

Dakle:

```text
R_C6_GPIO8_PU = 10 kΩ
R_C6_GPIO9_PU = 10 kΩ
```

Za Joint Download:

1. povući GPIO9 LOW
2. resetirati C6 preko EN
3. GPIO8 ostaje HIGH
4. C6 ROM ulazi u Joint Download mode
5. flash preko UART0

Ovo može biti pogo-fixture funkcija bez fizičke C6 BOOT tipke na finalnom kućištu.

---

# 17. C6 UART0

Net mapping:

```text
C6 GPIO16 / TXD0 -> C6_UART_TX
C6 GPIO17 / RXD0 -> C6_UART_RX
```

Predvidjeti:

- 33 Ω series resistor na TX
- 33 Ω series resistor na RX
- pogo/test pads

Time C6 ostaje potpuno recoverable čak ako:

- SDIO firmware ne radi
- P4 firmware je neispravan
- ESP-Hosted OTA nije dostupan

---

# 18. RF antenna placement

Za ESP32-C6-WROOM-1 s PCB antenom:

- modul postaviti na rub PCB-a
- antenna end okrenuti prema vanjskom rubu uređaja
- nema coppera ispod antenna keep-out zone
- nema high-speed trase ispod antene
- nema ground pour u keep-outu prema module recommendation
- metalni LCD frame držati dalje od antene
- ne stavljati RCA/USB metalno kućište neposredno uz antenu
- ne zatvarati antenu između PCB grounda i metalnog kućišta

Ako enclosure geometrija to ne dopušta:

**prebaciti U4 na ESP32-C6-WROOM-1U-N4** i koristiti vanjsku antenu.

---

# 19. LCD interaction with antenna

Pajoniiir ima veliki 4.3" LCD s metalnim/mehaničkim frameom.

Zato C6 antena ne smije završiti:

- direktno iza metalnog LCD framea
- pod ravnom metalnom pločom
- između dvije velike ground površine

Poželjni placement:

```text
PCB edge
+----------------------------------+
| C6 module ---> [ANTENNA OUTSIDE] |
|                                  |
|       P4 / rest of board         |
|                                  |
|             LCD FPC              |
+----------------------------------+
```

Prije finalnog layouta napraviti mehanički 3D overlay s LCD-om i kućištem.

---

# 20. 1U fallback provision

Ako postoji realna mogućnost metalnog enclosurea, footprint/design treba provjeriti može li se bez respina koristiti WROOM-1U.

WROOM-1U koristi vanjski antenna connector kompatibilan s U.FL/MHF-I/AMC klasom.

Najsigurnije je još prije PCB freezea odlučiti:

- WROOM-1 PCB antenna
ili
- WROOM-1U external antenna

Ne ostavljati odluku nakon proizvodnje prve mehanički zatvorene serije.

---

# 21. Optional power isolation

Predvidjeti:

`FB_C6`

kao 0603/0805 footprint.

Default:

**0 Ω**

DVT alternative:

- ferrite bead 600 Ω @100 MHz class
- low-DCR, current rating ≥0.5 A

Ferrite koristiti samo ako mjerenje pokaže da C6 RF/current burst unosi mjerljiv noise u 3V3_SYS/audio.

---

# 22. Test points

Obavezno:

```text
TP_3V3_C6
TP_C6_EN
TP_C6_UART_TX
TP_C6_UART_RX
TP_C6_GPIO8
TP_C6_GPIO9
TP_C6_SDIO_CLK
TP_C6_SDIO_CMD
TP_C6_SDIO_D0
TP_C6_SDIO_D1
TP_C6_SDIO_D2
TP_C6_SDIO_D3
TP_GND_C6
```

SDIO TP-ovi moraju biti mali da ne stvore velike stubs/capacitance.

---

# 23. Preliminary BOM additions

| RefDes | Qty | Value / part | Status |
|---|---:|---|---|
| U4 | 1 | ESP32-C6-WROOM-1-N4 | LOCK-CANDIDATE |
| FB_C6 | 1 | 0 Ω default / ferrite option | tuning |
| C_C6_HF | 1 | 100 nF | required |
| C_C6_LOCAL | 1 | 10 µF | required |
| C_C6_BULK | 1 | 22 µF | Pajoniiir transient reserve |
| R_C6_EN | 1 | 10 kΩ | required |
| C_C6_EN | 1 | 1 µF | recommended RC reset |
| R_C6_RESET_SER | 1 | 0 Ω | isolation/debug |
| R_SDIO_CMD_PU | 1 | 51.1 kΩ 1% | mandatory |
| R_SDIO_D0_PU | 1 | 51.1 kΩ 1% | mandatory |
| R_SDIO_D1_PU | 1 | 51.1 kΩ 1% | mandatory |
| R_SDIO_D2_PU | 1 | 51.1 kΩ 1% | mandatory |
| R_SDIO_D3_PU | 1 | 51.1 kΩ 1% | mandatory |
| R_SDIO_CLK | 1 | 22 Ω initial | SI tuning |
| R_SDIO_CMD | 1 | 0 Ω | SI tuning |
| R_SDIO_D0 | 1 | 0 Ω | SI tuning |
| R_SDIO_D1 | 1 | 0 Ω | SI tuning |
| R_SDIO_D2 | 1 | 0 Ω | SI tuning |
| R_SDIO_D3 | 1 | 0 Ω | SI tuning |
| R_C6_GPIO8_PU | 1 | 10 kΩ | direct recovery boot |
| R_C6_GPIO9_PU | 1 | 10 kΩ | normal boot + recovery |
| R_C6_UART_TX | 1 | 33 Ω | debug |
| R_C6_UART_RX | 1 | 33 Ω | debug |

---

# 24. KiCad nets

Power:

```text
3V3_SYS
3V3_C6
GND
```

SDIO:

```text
P4_C6_SDIO_CLK
P4_C6_SDIO_CMD
P4_C6_SDIO_D0
P4_C6_SDIO_D1
P4_C6_SDIO_D2
P4_C6_SDIO_D3
```

Control/debug:

```text
P4_C6_RESET
C6_EN
C6_UART_TX
C6_UART_RX
C6_BOOT_GPIO8
C6_BOOT_GPIO9
```

---

# 25. Firmware configuration baseline

Current Pajoniiir host side:

```text
CONFIG_SLAVE_IDF_TARGET_ESP32C6=y
CONFIG_ESP_HOSTED_CP_TARGET_ESP32C6=y
CONFIG_ESP_HOSTED_SDIO_HOST_INTERFACE=y
CONFIG_ESP_HOSTED_SDIO_SLOT_1=y
CONFIG_ESP_HOSTED_SDIO_4_BIT_BUS=y
CONFIG_ESP_HOSTED_P4_DEV_BOARD_FUNC_BOARD=y
```

Current ESP-Hosted P4 default mapping:

```text
CLK   GPIO18
CMD   GPIO19
D0    GPIO14
D1    GPIO15
D2    GPIO16
D3    GPIO17
RESET GPIO54
```

Current optimized clock target:

```text
CONFIG_ESP_HOSTED_SDIO_CLOCK_FREQ_KHZ=40000
```

Za custom Pajoniiir board kasnije možemo prestati koristiti semantički naziv `P4_DEV_BOARD_FUNC_BOARD` i prebaciti mapping u vlastiti board config, ali fizički pinout ostaje isti.

---

# 26. Bring-up sequence

## Phase 1 — C6 power only

Provjeriti:

- 3V3_C6 = stabilan
- EN RC startup
- current nije abnormalan
- UART ROM boot log

## Phase 2 — direct C6 firmware

- Joint Download preko GPIO8/GPIO9
- flash ESP-Hosted slave firmware
- normal SPI boot
- UART log

## Phase 3 — SDIO 1-bit low speed

- 5–10 MHz
- CMD/D0/D1
- potvrditi enumeration

## Phase 4 — SDIO 4-bit

- DAT2/DAT3 aktivirati
- 20 MHz
- 40 MHz

## Phase 5 — network

- SoftAP `Pajoniiir`
- DHCP
- web UI
- iperf
- sustained transfer

---

# 27. Power acceptance

Mjeriti:

CH1 = 3V3_SYS  
CH2 = 3V3_C6  
CH3 = C6_EN  
CH4 = SDIO_CLK ili P4 rail

Pri:

- C6 boot
- Wi-Fi TX
- SoftAP client connect
- iperf
- dual-deck + Wi-Fi

Acceptance:

- nema P4 resetiranja
- 3V3_C6 nema neprihvatljivog dipa
- C6 se ne spontano resetira
- SDIO CRC/timeout errors = 0 tijekom soak testa

---

# 28. SDIO acceptance

Testovi:

- 100 cold boots
- 100 C6 reset cycles
- 100 P4 reset cycles
- 1-bit fallback test
- 4-bit 40 MHz
- 1 h iperf
- 4 h combined dual-USB/audio/Wi-Fi soak

Pass criteria:

- bez enumeration failurea
- bez sustained CRC errors
- bez SDIO timeouta
- bez random C6 resetova

---

# 29. RF acceptance

U finalnom kućištu mjeriti:

- RSSI prema poznatom AP-u
- throughput
- reconnect
- orientation sensitivity
- LCD on/off razliku
- USB cables connected/disconnected
- RCA cables connected/disconnected

Ako metalni LCD/enclosure degradira performanse:

- prebaciti na WROOM-1U
- ili promijeniti mechanical placement

---

# 30. Critical schematic review checklist

- [ ] WROOM module pin 1/29 footprint verified
- [ ] 3V3_C6 može dati ≥0.5 A
- [ ] 100nF + 10uF + 22uF lokalno
- [ ] EN 10k + 1uF
- [ ] P4 GPIO54 reset path
- [ ] CMD pull-up 51.1k
- [ ] DAT0-3 svaki pull-up 51.1k
- [ ] nema pull-upa na CLK
- [ ] P4↔C6 pin mapping točan
- [ ] CLK series 22R
- [ ] ostale SDIO linije imaju 0R tuning footprints
- [ ] C6 UART TX/RX test pads
- [ ] GPIO8/GPIO9 recovery pads/network
- [ ] antenna keep-out definiran u footprintu
- [ ] mechanical LCD frame ne ulazi u keep-out
- [ ] WROOM-1U fallback odlučen prije layout freezea

---

# 31. Zaključak

Pajoniiir C6 blok za Rev A:

```text
ESP32-C6-WROOM-1-N4

POWER:
3V3_SYS -> 0R/FB -> 3V3_C6
100nF + 10uF + 22uF
supply capability >= 0.5A

RESET:
P4 GPIO54 -> 0R -> C6 EN
EN 10k pull-up + 1uF

SDIO:
P4 GPIO18 -> C6 GPIO19 CLK
P4 GPIO19 -> C6 GPIO18 CMD
P4 GPIO14 -> C6 GPIO20 D0
P4 GPIO15 -> C6 GPIO21 D1
P4 GPIO16 -> C6 GPIO22 D2
P4 GPIO17 -> C6 GPIO23 D3

PULLUPS:
CMD, D0-D3 = 51.1k each

SERIES:
CLK = 22R initial
CMD/D0-D3 = 0R tuning

DEBUG:
C6 UART0 TX/RX
GPIO8/GPIO9 boot recovery
EN test access

RF:
module antenna at PCB edge
strict keep-out
WROOM-1U fallback if enclosure requires external antenna
```

**Sljedeći blok:** `06_USB_POWER` — TPS2561 dual-VBUS zaštita, točan ILIM, inrush capacitance, EN/FAULT GPIO strategy i izolacija USB0/USB1 brownouta.
