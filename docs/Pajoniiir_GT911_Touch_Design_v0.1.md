# Pajoniiir Mainboard — GT911 Touch Design v0.1

> **SUPERSEDED FOR THE ACTIVE REV A DISPLAY.** The DSI506 module uses an FT5426/FT5x06-compatible touch device at `0x38` on `DISPLAY_I2C_SDA/SCL`, with no dedicated reset or interrupt wires. `11_TOUCH_GT911.kicad_sch` is intentionally retired and empty.

**Projekt:** Pajoniiir BL-A1800 / Pajoniiir-M1  
**Ploča:** Pajoniiir Mainboard Rev A  
**Blok:** 11_TOUCH_GT911  
**Datum:** 2026-09-02  
**Status:** Engineering design candidate — custom-board GPIO mapping zaključan kao kandidat

---

# 1. Funkcija

Pajoniiir-M1 koristi GT911 capacitive touch controller koji je dio 4.3" display/touch assemblyja.

Glavna PCB ne mora nužno sadržavati bare GT911 IC.

Primarni očekivani model:

~~~text
LCD/touch assembly
  |
  +-- GT911 controller on panel/FPC assembly
  |
  +-- FPC to Pajoniiir-M1
~~~

Pajoniiir mainboard mora osigurati:

- 3.3 V touch power prema exact panel zahtjevu
- I2C SDA
- I2C SCL
- RESET
- INT
- GND

---

# 2. Novi Rev A GPIO mapping

Custom-board mapping:

| Funkcija | ESP32-P4 |
|---|---:|
| TOUCH_RST | **GPIO3** |
| TOUCH_INT | **GPIO4** |
| TOUCH_SDA | **GPIO7** |
| TOUCH_SCL | **GPIO8** |

Ovo je namjerno drugačije od jednog JC4880 firmware/schematic patha koji koristi GPIO22/21 za reset/interrupt.

Razlog:

GPIO21/22 na Pajoniiir-M1 koriste USB power fault/enable.

Aktualni Pajoniiir firmware ionako danas koristi GT911 u polling modu s RST/INT = NC, pa novi board target može migrirati na GPIO3/4 bez narušavanja dokazano funkcionalnog touch protokola.

---

# 3. I2C address

GT911 podržava dvije 7-bit adrese:

- **0x5D**
- 0x14

Pajoniiir koristi:

**0x5D**

To treba ostati deterministički isto kao na aktualnom firmwareu.

Adresa se latcha tijekom reset/power-up sequencea preko INT pina.

---

# 4. Deterministic 0x5D reset sequence

Za odabir 0x5D:

1. konfigurirati GPIO3 TOUCH_RST kao output
2. konfigurirati GPIO4 TOUCH_INT kao output LOW
3. povući TOUCH_RST LOW
4. držati reset LOW >100 µs
5. zadržati INT LOW
6. pustiti TOUCH_RST HIGH
7. pričekati najmanje >5 ms
8. završiti address-selection timing
9. GPIO4 prebaciti iz output LOW u **high-impedance input**
10. ne uključivati internal pull-up/pull-down na INT
11. probeati I2C 0x5D

Praktični firmware timing može koristiti veću marginu, npr.:

~~~text
RST low       1 ms
RST high wait 10 ms
INT release   after address latch
settle        50 ms if driver/application needs conservative startup
~~~

---

# 5. RESET network

GT911 reset je active LOW.

Rev A mainboard:

~~~text
3V3_TOUCH
   |
 10k
   |
TOUCH_RST ---- 100R ---- GPIO3
~~~

RefDes:

- R_TOUCH_RST_PU = 10 kΩ
- R_TOUCH_RST_SER = 100 Ω

Reset pull-up daje sigurno released stanje ako P4 još nije inicijalizirao pin.

P4 ga i dalje može aktivno povući LOW.

---

# 6. INT network

GT911 INT tijekom normalnog rada ne treba external pull-up ako panel/controller output radi po standardnom Goodix modelu.

Goodix programming guide za normalni input state preporučuje:

- host INT kao floating input
- bez internal pull-up
- bez internal pull-down

Rev A:

~~~text
GT911_INT ---- 100R ---- GPIO4
~~~

RefDes:

- R_TOUCH_INT_SER = 100 Ω

Bez statičkog pull-up/downa na host strani.

Tijekom reset/address selectiona P4 GPIO4 privremeno postaje output LOW.

Nakon toga vraća se u input mode.

---

# 7. I2C bus

Existing proven pins:

~~~text
GPIO7 SDA
GPIO8 SCL
~~~

GT911 podržava do 400 kbit/s.

Aktualni vendor examples često koriste 100 kHz; za Rev A bring-up zadržati 100 kHz, a tek kasnije po potrebi podići na 400 kHz.

---

# 8. I2C pull-ups

Budući da je ES8311 uklonjen, ovaj I2C bus je puno jednostavniji.

Initial:

~~~text
SDA -> 4.7 kΩ -> 3V3_TOUCH
SCL -> 4.7 kΩ -> 3V3_TOUCH
~~~

RefDes:

- R_TOUCH_SDA_PU = 4.7 kΩ
- R_TOUCH_SCL_PU = 4.7 kΩ

Dodati DNP parallel footprints:

- R_TOUCH_SDA_PU2 = 4.7 kΩ DNP
- R_TOUCH_SCL_PU2 = 4.7 kΩ DNP

Ako 400 kHz edge measurement pokaže da je 4.7 kΩ preslabo zbog FPC capacitancea, paralelni 4.7 kΩ daje efektivno ~2.35 kΩ bez PCB respina.

---

# 9. I2C series tuning

Rev A:

- R_TOUCH_SDA_SER = 22 Ω
- R_TOUCH_SCL_SER = 22 Ω

near P4 source/bus root.

Ovo nije strogi I2C requirement nego EMI/ringing tuning element.

Može se zamijeniti 0 Ω nakon mjerenja.

---

# 10. Touch power

Javni JC4880 connector reconstruction pokazuje 3.3 V na display/touch FPC-u.

Pajoniiir:

~~~text
3V3_LCD
   |
 0R
   |
3V3_TOUCH
~~~

RefDes:

**FB_TOUCH = 0 Ω default**

Lokalno uz FPC:

- 100 nF
- 4.7 µF

Finalno potvrditi exact panel/touch power arrangement prije connector freezea.

---

# 11. No bare GT911 on mainboard by default

Engineering BOM treba GT911 tretirati kao:

~~~text
U_TOUCH = DNP / PANEL-INTEGRATED
~~~

dok se ne odabere točan LCD/touch assembly.

Ako finalno odabrani panel daje samo raw touch sensor electrodes bez GT911-a, arhitektura bi se radikalno promijenila i to nije preferirana Rev A opcija.

Preferred procurement:

**panel assembly koji već sadrži GT911/controller electronics.**

---

# 12. ESD strategy

Touch FPC je interni connector.

Baseline:

- nema velikog external ESD arraya na INT/RST
- I2C ESD može biti DNP option ako panel FPC postane service-exposed

Predvidjeti optional 4-channel low-cap ESD footprint samo ako routing/mehanika dopušta bez nepotrebnog bus capacitancea.

Rev A default:

**DNP**

---

# 13. Interrupt-driven mode

Današnji firmware polling je dokazano funkcionalan.

Nova ploča dobiva TOUCH_INT kako bi kasnije mogla preći na interrupt-driven touch.

Prednosti:

- manje I2C pollinga
- manje CPU wakeups
- brži response na touch event
- čistiji event model

ISR ne smije raditi I2C transakciju direktno.

Preporučeni flow:

~~~text
GT911 INT
 -> GPIO ISR
 -> notify task / set flag
 -> task reads GT911 over I2C
 -> clear GT911 status
~~~

Polling fallback ostaviti u BSP-u za debug.

---

# 14. Firmware migration

Novi `bsp_pajoniiir_m1`:

~~~text
TOUCH_SDA = GPIO7
TOUCH_SCL = GPIO8
TOUCH_RST = GPIO3
TOUCH_INT = GPIO4
TOUCH_ADDR = 0x5D
~~~

Bring-up može prvo koristiti:

~~~text
rst_gpio_num = GPIO_NUM_NC
int_gpio_num = GPIO_NUM_NC
~~~

ako panel iz nekog razloga ne izvede te linije.

Ali proizvodni M1 path treba preferirati explicit reset/address selection.

---

# 15. Coordinate model

Panel native:

**480 × 800**

Landscape UI:

**800 × 480**

PPA/display rotation je 90°.

Touch driver treba najprije potvrditi raw native coordinate orientation prije primjene UI transformacije.

Test points:

- native top-left
- native top-right
- native bottom-left
- native bottom-right
- center

Tek nakon toga zaključati:

- swap_xy
- mirror_x
- mirror_y

Ne naslijepo kopirati old JC4880 flags ako finalni panel FPC orientation bude drugačiji.

---

# 16. Connector interaction

Touch signali dijele LCD FPC:

~~~text
3V3_TOUCH
GND
SDA
SCL
TOUCH_RST
TOUCH_INT
~~~

Exact pin numbers ostaju blokirani istim hard gateom kao LCD DSI pinout.

Ne smije se freezeati connector footprint iz generičkog 4.3" ST7701S oglasa.

---

# 17. Test points

- TP_TOUCH_SDA
- TP_TOUCH_SCL
- TP_TOUCH_RST
- TP_TOUCH_INT
- TP_3V3_TOUCH
- TP_TOUCH_GND

I2C TP-ovi mali i bez dugih stubova.

---

# 18. Preliminary BOM

| RefDes | Qty | Value / part | Status |
|---|---:|---|---|
| GT911 | 0/1 | panel-integrated expected | TBD-PANEL |
| FB_TOUCH | 1 | 0 Ω | rail isolation/tuning |
| C_TOUCH_HF | 1 | 100 nF | local |
| C_TOUCH_BULK | 1 | 4.7 µF | local |
| R_TOUCH_RST_PU | 1 | 10 kΩ | required |
| R_TOUCH_RST_SER | 1 | 100 Ω | candidate |
| R_TOUCH_INT_SER | 1 | 100 Ω | candidate |
| R_TOUCH_SDA_PU | 1 | 4.7 kΩ | initial |
| R_TOUCH_SCL_PU | 1 | 4.7 kΩ | initial |
| R_TOUCH_SDA_PU2 | 1 | 4.7 kΩ DNP | 400 kHz tuning |
| R_TOUCH_SCL_PU2 | 1 | 4.7 kΩ DNP | 400 kHz tuning |
| R_TOUCH_SDA_SER | 1 | 22 Ω | tuning |
| R_TOUCH_SCL_SER | 1 | 22 Ω | tuning |
| D_TOUCH_ESD | 0/1 | low-C multichannel | DNP |

---

# 19. KiCad nets

~~~text
3V3_TOUCH
TOUCH_SDA
TOUCH_SCL
TOUCH_RST
TOUCH_INT
GND
~~~

P4 aliases:

~~~text
GPIO3 TOUCH_RST
GPIO4 TOUCH_INT
GPIO7 TOUCH_SDA
GPIO8 TOUCH_SCL
~~~

---

# 20. Bring-up

1. verify 3V3_TOUCH
2. hold RST low
3. drive INT low
4. release RST
5. release INT to input
6. scan bus
7. expect 0x5D
8. read product ID
9. read raw coordinate
10. enable normal polling
11. enable interrupt path
12. verify 100 repeated reset cycles

---

# 21. Acceptance criteria

- 0x5D detected on every cold boot
- no random 0x14 address selection
- no I2C timeout during 1 h interaction test
- reset recovery works
- interrupt path works
- polling fallback works
- corners map correctly after rotation
- no false touch from backlight PWM/USB/RF
- Wi-Fi TX does not corrupt I2C or create phantom events

---

# 22. EMI/noise test

Touch is particularly sensitive to display/backlight noise.

Test:

- backlight 0%, 10%, 50%, 100%
- Wi-Fi TX
- USB0 sustained read
- USB1 UAC
- RCA audio active
- finger near enclosure/USB cables
- external grounded/ungrounded power adapter

Monitor:

- false touch count
- coordinate jitter
- I2C errors

If backlight switching induces noise:

1. verify ground/layout first
2. adjust I2C series R
3. evaluate touch rail ferrite
4. only then add more filtering

---

# 23. Zaključak

Rev A GT911 interface:

~~~text
GPIO3 -> TOUCH_RST
GPIO4 <- TOUCH_INT
GPIO7 <-> SDA
GPIO8 -> SCL

Address:
0x5D deterministic via INT LOW during reset

I2C:
4.7k pullups initial
optional parallel 4.7k DNP
22R series tuning

RST:
10k pullup + 100R series

INT:
100R series
NO static pull after address selection
~~~

Time touch prestaje biti "polling-only slučajno radi" periferni uređaj i postaje potpuno kontroliran, recoverable subsystem.

**Sljedeći blok:** 12_MICROSD — native SDMMC 4-bit, slot power, pull-up network, ESD, CLK tuning i optional GPIO45 power-cycle.
