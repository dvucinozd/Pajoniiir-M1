# Pajoniiir Mainboard — microSD / SDMMC Design v0.1

**Projekt:** Pajoniiir BL-A1800 / Pajoniiir-M1  
**Ploča:** Pajoniiir Mainboard Rev A  
**Blok:** 12_MICROSD  
**Datum:** 2026-09-02  
**Status:** Engineering design candidate — spreman za KiCad capture uz finalni socket MPN

---

# 1. Funkcija

microSD nije primarni music-media put. USB0 ostaje Rekordbox storage.

microSD na Pajoniiir-M1 služi za:

- config
- cache
- controller profileove
- servisne podatke
- crash/diagnostic pomoćne artefakte
- buduće lokalne assete

Koristimo native ESP32-P4 SDMMC host, 4-bit mode.

---

# 2. P4 native SDMMC0 mapping

Aktualne Espressif smjernice potvrđuju fixed IO-MUX mapping:

~~~text
GPIO39 -> SDMMC D0
GPIO40 -> SDMMC D1
GPIO41 -> SDMMC D2
GPIO42 -> SDMMC D3
GPIO43 -> SDMMC CLK
GPIO44 -> SDMMC CMD
~~~

Ovo ostaje zaključano jer postojeći Pajoniiir firmware već koristi isti mapping.

---

# 3. Power rail

SD kartica se napaja iz sistemskih 3.3 V.

Za Rev A uvodimo kontrolirani card rail:

~~~text
3V3_SYS
   |
TPS22918
   |
3V3_SD
   |
microSD socket
~~~

Glavni kandidat:

**TPS22918DBVR**

Karakteristike:

- 1–5.5 V
- 2 A continuous
- ~53 mΩ typ @3.3 V
- active-high ON
- adjustable rise time
- quick output discharge
- SOT-23-6
- ACTIVE

Ovo je bolja Rev A implementacija od običnog P-MOSFET-a jer daje kontrolirani inrush i determinističko pražnjenje raila pri power-cycleu.

---

# 4. SD power control GPIO

Predloženo:

**GPIO45 = SD_PWR_EN**

Status:

**LOCK-CANDIDATE**

GPIO45 je uz SDMMC pin grupu, ali nije potreban u našem 4-bit SDMMC0 načinu rada.

Topologija:

~~~text
GPIO45 ----> TPS22918 ON
               |
             100k
               |
              GND
~~~

R_SD_EN_PD = 100 kΩ

Default nakon P4 reseta:

**SD OFF**

Firmware eksplicitno uključuje karticu tijekom storage init-a.

---

# 5. TPS22918 slew-rate / CT

Rev A start point:

**C_SD_CT = 470 pF, 25 V X7R/C0G-class where practical**

TI tipično navodi oko:

**~850 µs 10–90% rise @3.3 V**

za 470 pF.

To daje dovoljno kontroliran startup da smanjimo inrush, bez višemilisekundnog nepotrebnog čekanja.

Alternative za EVT:

- 220 pF -> brži rise
- 470 pF -> default
- 1 nF -> sporiji rise

Finalno zaključati scope mjerenjem stvarne kartice i lokalnog capacitancea.

---

# 6. QOD / full card reset

Želimo da isključena kartica stvarno izgubi napajanje, a ne da 3V3_SD dugo pluta.

TPS22918 QOD koristimo preko external resistor konfiguracije:

~~~text
VOUT / 3V3_SD
   |
R_QOD
   |
QOD pin
~~~

Rev A initial:

**R_SD_QOD = 100 Ω**

Cilj:

- kontrolirano dischargeanje 3V3_SD pri OFF
- ne ostavljati card rail polunapunjen
- omogućiti pravi power-cycle recovery

Finalni discharge time izmjeriti na realnom socketu i kartici.

---

# 7. Input/output decoupling

Uz TPS22918:

~~~text
3V3_SYS
 |
1uF + 100nF
 |
TPS22918
 |
3V3_SD
 |
10uF + 100nF
 |
microSD
~~~

Rev A:

- C_SD_SW_IN = 1 µF
- C_SD_SW_IN_HF = 100 nF
- C_SD_OUT = 10 µF
- C_SD_OUT_HF = 100 nF

Dodatni 22 µF DNP footprint uz socket:

- C_SD_OUT_OPT = 22 µF DNP

---

# 8. Pull-ups

Espressif preporučuje pull-up na svim SDIO/SDMMC signalnim GPIO-ima.

Rev A:

~~~text
CMD -> 10k -> 3V3_SD
D0  -> 10k -> 3V3_SD
D1  -> 10k -> 3V3_SD
D2  -> 10k -> 3V3_SD
D3  -> 10k -> 3V3_SD
~~~

CLK nema pull-up.

Za razliku od C6 SDIO busa, ovdje pull-upovi idu na **3V3_SD**, ne na stalni 3V3_SYS.

Tako pri ugašenoj SD kartici nema signalnog back-poweranja kroz pull-up mrežu.

---

# 9. Series tuning resistors

Na svaku signalnu liniju rezervirati series resistor footprint.

Rev A:

~~~text
D0  = 0 Ω
D1  = 0 Ω
D2  = 0 Ω
D3  = 0 Ω
CMD = 0 Ω
CLK = 22 Ω initial
~~~

CLK series resistor mora biti uz P4/source stranu.

Ostali 0 Ω footprintovi služe za SI tuning.

---

# 10. CLK tuning capacitor

Espressif eksplicitno preporučuje rezervirati capacitor-to-GND footprint na SD clocku.

Rev A:

~~~text
SD_CLK ---- C_SD_CLK_TUNE ---- GND
~~~

Default:

**DNP**

Package:

0402

Tuning range nakon mjerenja:

- 2.2 pF
- 4.7 pF
- 10 pF

Samo ako scope/SI pokaže overshoot/ringing.

---

# 11. Signal isolation while power OFF

Kada je SD_PWR_EN LOW i 3V3_SD = 0 V, P4 ne smije aktivno voziti SD linije HIGH i back-powerati karticu kroz ESD diode.

Firmware power-cycle sequence mora:

1. stopirati SDMMC host activity
2. GPIO39-44 staviti u high-Z / sigurno stanje
3. SD_PWR_EN LOW
4. čekati da 3V3_SD padne ispod reset nivoa
5. delay
6. SD_PWR_EN HIGH
7. pričekati rail settle
8. ponovno konfigurirati SDMMC
9. reinitialize card

Ovo je ključno za stvarni hardware reset.

---

# 12. Power-cycle timing

Početni recovery flow:

~~~text
unmount
disable SDMMC pins
SD_PWR_EN = 0
wait 20 ms minimum
verify 3V3_SD discharged if telemetry/debug available
SD_PWR_EN = 1
wait 5–10 ms
configure SDMMC
initialize card
mount filesystem
~~~

Za problematične kartice firmware može povećati OFF interval na 100 ms.

---

# 13. microSD socket

J_SD = **TBD-MECH**

Zahtjevi:

- push-push ili push-pull ovisno o kućištu
- board-edge accessible
- shielded
- card detect preferred
- dovoljno robustan za servisnu upotrebu
- no proprietary board-only footprint

Card-detect prekidač je poželjan.

---

# 14. Card Detect

Ako finalni socket ima CD switch:

predloženi GPIO:

**GPIO46 = SD_CARD_DETECT**

Status:

**LOCK-CANDIDATE**

Topologija:

~~~text
3V3_SYS
 |
10k
 |
SD_CARD_DETECT ---- socket switch ---- GND
~~~

Firmware active-low.

Ako odabrani socket nema detect switch:

GPIO46 ostaje FREE.

---

# 15. ESD

microSD je user-accessible port pa ESD zaštita ima više smisla nego na internom LCD FPC-u.

Predvidjeti low-capacitance multi-line ESD array za:

- CMD
- CLK
- D0-D3

ali ne zaključavati generički high-C TVS.

Primarni kriteriji:

- vrlo mala capacitance
- 3.3 V kompatibilno
- više kanala
- dovoljno nisko clamping
- placement uz socket

Status:

**TBD-ESD**

Za Rev A možemo ostaviti DNP footprint ako signal-integrity margin bude prioritet, ali shield/mehanika mora biti dobra.

---

# 16. Socket shield

microSD metalni shield:

**direct GND**

s više kratkih GND via uz shield tabs.

Nema potrebe za zasebnim chassis-net eksperimentom kao kod vanjskih USB kablova.

---

# 17. Routing

SDMMC0:

- 4-layer board minimum
- continuous L2 GND
- CLK najkritičniji
- CMD/D0-D3 grupirati
- kratko od P4 do socket-a
- bez switching nodeova ispod busa
- ne routeati pod C6 antenna keep-out
- izbjegavati duge testpoint stubove

---

# 18. Length matching

U našem 4-bit non-UHS production modu ne treba agresivno serpentiniranje.

Cilj:

- D0-D3/CMD približno slične duljine
- CLK direktan i čist
- prioritet signal integrityja ispred umjetne geometrijske jednakosti

Ako kasnije idemo prema višim SD speed modovima, tada napraviti stroži timing budget.

---

# 19. Card operating mode

Rev A product baseline:

**standard 3.3 V SDMMC operation**

Ne uvodimo SD 3.0 1.8 V voltage switching / UHS-I kao requirement za config/cache medij.

Razlog:

- nepotrebna kompleksnost
- nema koristi za ovu storage ulogu
- USB0 je glavni high-throughput music path

---

# 20. Firmware error recovery

Na fatalni SD error:

1. stop I/O
2. unmount
3. hardware power-cycle TPS22918
4. reinitialize
5. remount
6. ako drugi pokušaj ne uspije -> mark SD unavailable, ne resetirati cijeli Pajoniiir

microSD kvar ne smije srušiti:

- USB playback
- FLX4
- MAIN audio
- web UI

---

# 21. Test points

- TP_3V3_SD
- TP_SD_PWR_EN
- TP_SD_CLK micro
- TP_SD_CMD micro
- TP_SD_D0 micro
- TP_SD_GND

D1-D3 testpointovi samo ako layout dopušta bez značajnih stubova.

---

# 22. Preliminary BOM

| RefDes | Qty | Part/value | Status |
|---|---:|---|---|
| U_SD_PWR | 1 | TPS22918DBVR | LOCK-CANDIDATE |
| R_SD_EN_PD | 1 | 100 kΩ | required |
| C_SD_CT | 1 | 470 pF, >=25 V | EVT initial |
| R_SD_QOD | 1 | 100 Ω | EVT initial |
| C_SD_SW_IN | 1 | 1 µF | required |
| C_SD_SW_IN_HF | 1 | 100 nF | required |
| C_SD_OUT | 1 | 10 µF | required |
| C_SD_OUT_HF | 1 | 100 nF | required |
| C_SD_OUT_OPT | 1 | 22 µF | DNP |
| R_SD_CMD_PU | 1 | 10 kΩ | required |
| R_SD_D0_PU | 1 | 10 kΩ | required |
| R_SD_D1_PU | 1 | 10 kΩ | required |
| R_SD_D2_PU | 1 | 10 kΩ | required |
| R_SD_D3_PU | 1 | 10 kΩ | required |
| R_SD_CLK_SER | 1 | 22 Ω | initial |
| R_SD_CMD_SER | 1 | 0 Ω | tuning |
| R_SD_D0_SER | 1 | 0 Ω | tuning |
| R_SD_D1_SER | 1 | 0 Ω | tuning |
| R_SD_D2_SER | 1 | 0 Ω | tuning |
| R_SD_D3_SER | 1 | 0 Ω | tuning |
| C_SD_CLK_TUNE | 1 | DNP | SI tuning |
| J_SD | 1 | microSD socket | TBD-MECH |
| D_SD_ESD | 0/1 | low-C array | TBD/DNP |
| R_SD_CD_PU | 0/1 | 10 kΩ | if socket has CD |

---

# 23. KiCad nets

~~~text
3V3_SYS
3V3_SD
SD_PWR_EN
SD_CARD_DETECT

SDMMC_D0
SDMMC_D1
SDMMC_D2
SDMMC_D3
SDMMC_CLK
SDMMC_CMD
GND
~~~

---

# 24. Bring-up

1. SD_PWR_EN low
2. verify 3V3_SD near 0 V
3. set P4 bus safe/high-Z
4. SD_PWR_EN high
5. measure ~0.85 ms class rail rise
6. initialize at low clock
7. identify card
8. mount filesystem
9. read/write
10. power-cycle 100 times
11. remove/reinsert 100 times
12. combined USB/audio/Wi-Fi stress

---

# 25. Acceptance criteria

- no P4 brownout on SD power-up
- 3V3_SD fully turns off
- 100/100 hardware power-cycle recoveries
- no bus back-power when OFF
- no CRC/timeouts in sustained access
- SD fault never resets USB/audio
- card-detect behaves correctly if populated
- SD access does not inject audible noise into MAIN OUT

---

# 26. Zaključak

Rev A microSD blok:

~~~text
GPIO39 D0
GPIO40 D1
GPIO41 D2
GPIO42 D3
GPIO43 CLK
GPIO44 CMD

GPIO45 -> TPS22918 SD power enable
GPIO46 <- optional card detect

3V3_SYS -> TPS22918 -> 3V3_SD

CT 470pF initial
QOD 100R initial
CLK 22R
CMD/D0-D3 0R tuning
10k pullups to 3V3_SD
CLK capacitor footprint DNP
~~~

Ovaj dizajn omogućuje pravi firmware-controlled hardware reset kartice bez rebootanja cijelog uređaja.

**Sljedeći blok:** 13_DEBUG_SERVICE — UART0, USB Serial/JTAG, C6 recovery, Tag-Connect/pogo i factory programming.
