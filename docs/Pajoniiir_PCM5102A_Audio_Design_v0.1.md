# Pajoniiir Mainboard — PCM5102A MAIN Audio Design v0.1

**Projekt:** Pajoniiir BL-A1800 / Pajoniiir-M1  
**Ploča:** Pajoniiir Mainboard Rev A  
**Blok:** 09_AUDIO_PCM5102A  
**Datum:** 2026-09-02  
**Status:** Captured in KiCad; RCA MPNs/footprint locked, panel and audio EVT gates open

> **Post-capture update (2026-09-04):** J4/J5 are locked to Kycon KLPX-0848A-2-W-G / KLPX-0848A-2-R-G with project footprint `Pajoniiir-M1:Kycon_KLPX-0848A-2-x-G`. The optional 3.5 mm output was removed from Rev A. Final RCA panel and mated-plug geometry remain open.

---

# 1. Funkcija

PCM5102A je jedini lokalni analogni audio DAC na Pajoniiir-M1 ploči.

Njegova uloga:

- stereo MAIN OUT
- 2.1 Vrms nominalni full-scale single-ended line output
- RCA LEFT / RIGHT
- 3.5 mm stereo line out **removed from Rev A in M1-MECH-A8**

CUE/PFL ne ide preko ovog DAC-a. Cue ostaje USB Audio Class ch3/ch4 prema DDJ-FLX4 headphone izlazu.

---

# 2. U5

Primary:

**PCM5102APWR**

Package:

- TSSOP-20 / PW

Status:

**LOCKED — ista funkcionalna komponenta već je hardverski testirana na prototipu.**

Bench record iz originalnog Pajoniiir projekta potvrđuje da su GPIO50/GPIO52/GPIO51 na PCM5102A breakout-u reproducirali audio na RCA i 3.5 mm izlazu.

---

# 3. P4 I²S mapping

| Funkcija | ESP32-P4 | PCM5102A |
|---|---:|---|
| BCLK | GPIO50 | BCK pin 13 |
| LRCK / WS | GPIO52 | LRCK pin 15 |
| DATA | GPIO51 | DIN pin 14 |
| MCLK / SCK | nije korišten | SCK pin 12 = GND |

Net names:

~~~text
P4_I2S_BCLK
P4_I2S_LRCK
P4_I2S_DOUT
~~~

---

# 4. Zašto SCK ide na GND

PCM5102A podržava 3-wire PCM/I²S preko internog BCK PLL-a.

U tom modu:

- BCK i LRCK dolaze normalno
- SCK ostaje na ground levelu
- nakon 16 uzastopnih LRCK perioda s valjanim BCK/LRCK i SCK=0 uređaj automatski aktivira interni PLL
- vanjski high-frequency MCLK nije potreban

Za Rev A:

**SCK pin 12 direktno na GND**

Ne ostaviti SCK floating.

---

# 5. I²S source termination

Iako breakout prototip radi bez series terminationa, custom PCB treba dati SI marginu.

Rev A initial:

~~~text
GPIO50 BCLK -- 22R --> PCM5102A BCK
GPIO52 LRCK -- 22R --> PCM5102A LRCK
GPIO51 DATA -- 22R --> PCM5102A DIN
~~~

RefDes:

- R_I2S_BCLK = 22 Ω
- R_I2S_LRCK = 22 Ω
- R_I2S_DATA = 22 Ω

Otpornike postaviti blizu P4 source strane.

Ako scope pokaže vrlo čiste bridove i nepotreban rise-time penalty, mogu se zamijeniti 0 Ω.

---

# 6. BCK frequency constraint

Za 3-wire BCK PLL rad, BCK/LRCK omjer mora biti valjan.

Primjeri iz TI tablice:

| Fs | BCK = 32×Fs | BCK = 64×Fs |
|---:|---:|---:|
| 44.1 kHz | 1.4112 MHz | 2.8224 MHz |
| 48 kHz | 1.536 MHz | 3.072 MHz |
| 96 kHz | 3.072 MHz | 6.144 MHz |
| 192 kHz | 6.144 MHz | 12.288 MHz |

Firmware treba zadržati I²S format koji PCM5102A PLL može automatski prihvatiti.

---

# 7. Hardware control straps

Pajoniiir koristi hardware-controlled PCM5102A.

## FMT

I²S format:

**FMT = LOW**

~~~text
FMT -> GND
~~~

## FLT

Normal filter latency:

**FLT = LOW**

~~~text
FLT -> GND
~~~

## DEMP

44.1 kHz de-emphasis nije potreban za standardni moderni digitalni playback path.

**DEMP = LOW**

~~~text
DEMP -> GND
~~~

Sva tri pina imaju determinističko stanje i ne smiju floating.

---

# 8. XSMT — aktivni mute

XSMT:

- LOW = soft mute / analog mute
- HIGH = soft un-mute

Za custom PCB koristimo XSMT aktivno, umjesto da ga samo strapamo HIGH.

Predloženi P4 GPIO:

**GPIO49 = DAC_XSMT**

Status:

**LOCK-CANDIDATE**

GPIO49 je u trenutnom Pajoniiir pin inventoryju slobodan nakon uklanjanja starog S3 monitor-linka.

Prije finalnog schematic locka potvrditi ga još jednom protiv kompletnog v3.x pin-allocation tablea.

---

# 9. XSMT boot state

Cilj:

**DAC mora biti muted dok P4 ne uspostavi stabilne I²S clockove.**

Topologija:

~~~text
P4 GPIO49 ---- 100R ---- XSMT
                         |
                       100k
                         |
                        GND
~~~

RefDes:

- R_XSMT_SER = 100 Ω
- R_XSMT_PD = 100 kΩ

Default:

- P4 reset/floating → XSMT LOW → muted
- firmware pokrene BCLK/LRCK/DATA
- pričeka najmanje dovoljan PLL/clock lock interval
- GPIO49 HIGH
- PCM5102A soft-unmute

---

# 10. Power-down sequence

TI upozorava da se pri nekontroliranom gubitku napajanja može pojaviti pop.

Planned shutdown:

1. postaviti XSMT LOW
2. pričekati najmanje 150 sample periods + 0.2 ms
3. praktično koristiti najmanje 3 ms marginu pri normalnim sampling rateovima
4. zatim zaustaviti I²S clockove / gasiti sustav

Firmware zato treba implementirati:

~~~text
audio_mute_main();
delay >= 3 ms;
stop I2S;
powerdown/reboot;
~~~

Time custom ploča dobiva bolji pop/click behavior od običnog breakout modula.

---

# 11. Audio power rail

Glavni digitalni rail:

**3V3_SYS**

Audio branch:

~~~text
3V3_SYS
   |
 FB_AUDIO / 0R
   |
3V3_AUDIO
~~~

Default:

**FB_AUDIO = 0 Ω**

Footprint 0603/0805 dopušta zamjenu ferrite beadom nakon noise/EMI mjerenja.

Ne uvoditi ferrite samo zato što "audio treba ferrite". Ako bead + local C napravi neželjenu impedance resonance, rezultat može biti gori. Rev A prvo mjeri.

---

# 12. Single 3.3 V supply configuration

PCM5102A reference application podržava single 3.3 V operation.

Rev A:

~~~text
AVDD  = 3V3_AUDIO
CPVDD = 3V3_AUDIO
DVDD  = 3V3_AUDIO
~~~

Nema zasebnog 1.8 V digitalnog supplyja.

LDOO ostaje izlaz internog 1.8 V LDO-a i samo se decoupla.

---

# 13. AVDD decoupling

TI Figure 33:

~~~text
AVDD -> 3.3V
AVDD to AGND:
  100 nF
  10 µF
~~~

Rev A:

- C_AVDD_HF = 100 nF
- C_AVDD_BULK = 10 µF

Placement neposredno uz pin 8.

---

# 14. CPVDD / charge-pump supply

TI Figure 33:

~~~text
CPVDD -> 3.3V
CPVDD to CPGND:
  100 nF
  10 µF
~~~

Rev A:

- C_CPVDD_HF = 100 nF
- C_CPVDD_BULK = 10 µF

Pinovi:

- CPVDD pin 1
- CPGND pin 3

---

# 15. Charge pump capacitors

Flying capacitor:

~~~text
CAPP pin 2
  |
  2.2 µF
  |
CAPM pin 4
~~~

RefDes:

**C_CP_FLY = 2.2 µF**

Negative rail decoupling:

~~~text
VNEG pin 5
  |
  2.2 µF
  |
CPGND
~~~

RefDes:

**C_VNEG = 2.2 µF**

Oba vrlo blizu IC-a.

---

# 16. DVDD / LDOO

DVDD single-supply:

~~~text
DVDD -> 3V3_AUDIO
DVDD to DGND:
  100 nF
  10 µF
~~~

Rev A:

- C_DVDD_HF = 100 nF
- C_DVDD_BULK = 10 µF

LDOO pin 18:

~~~text
LDOO -> 100 nF -> DGND
~~~

RefDes:

- C_LDOO = 100 nF

Ne spajati LDOO na 3V3.

---

# 17. Grounding

PCM5102A ima:

- AGND pin 9
- DGND pin 19
- CPGND pin 3

Rev A koristi:

**jedan solid GND plane**

Ne raditi rezani analogni i digitalni ground otok.

TI layout guidance eksplicitno navodi da se AGND i DGND mogu tretirati kao zajednički ground, uz dobru fizičku partitioning disciplinu.

Najvažnije je:

- clock return currents držati dalje od analog outputa
- charge pump current loops lokalno
- decoupling vrlo blizu pinova

---

# 18. Analog output network

TI reference:

~~~text
OUTR -- 470R ----+---- RCA RIGHT
                 |
                2.2nF
                 |
                AGND

OUTL -- 470R ----+---- RCA LEFT
                 |
                2.2nF
                 |
                AGND
~~~

Rev A:

- R_OUT_R = 470 Ω
- R_OUT_L = 470 Ω
- C_OUT_R = 2.2 nF C0G/NP0
- C_OUT_L = 2.2 nF C0G/NP0

Capacitors postaviti nakon 470 Ω serijskog otpornika, prema connector/output nodeu.

---

# 19. No DC blocking capacitors

PCM5102A koristi ground-centered DirectPath output.

Full-scale output:

približno **2.1 Vrms single-ended**

Zato Rev A ne koristi velike serijske electrolytic DC-blocking kondenzatore na RCA izlazima.

Prednosti:

- nema LF phase shift
- nema velikih audio capacitors
- nema startup charging transienta kroz output coupling C
- manji BOM

---

# 20. RCA connectors

J_RCA_L i J_RCA_R:

**TBD-MECH**

Zahtjevi:

- board-mount
- robust mechanical shell
- dovoljno spacinga za standardne RCA plugove
- shield/GND terminal s niskim impedance pathom
- poželjno izolirani/mehanički stabilni connector ako enclosure design to zahtijeva

Mehaniku zaključati zajedno s kućištem.

---

# 21. 3.5 mm line out — removed from Rev A

M1-MECH-A8 removes J6 / J_LINE_35 from the Rev A schematic and PCB baseline.

Razlozi:

- MAIN product output is RCA LEFT/RIGHT
- CUE/headphones remain DDJ-FLX4 USB Audio
- J6 was production-default DNP and was never a headphone output
- M1-MECH-A4 exposed a real panel/mounting conflict
- retaining a dormant connector would consume enclosure, courtyard and sourcing budget without a required Rev A function

The legacy Ø6.97 mm opening remains historical mechanical evidence only. Reintroduction requires a future board/product revision with fresh combined-load, ESD and panel validation.

---

# 22. Analog ESD option

RCA je vanjski konektor.

Predvidjeti DNP footprint za low-capacitance analog ESD protector na svaki channel, ali ga ne populirati dok se ne provjeri:

- leakage
- capacitance
- THD
- clamp behavior

Rev A baseline:

**DNP**

ESD compliance test će odlučiti treba li zaštita i koji MPN.

---

# 23. Placement

Preferred audio zone:

~~~text
P4
 |
 | short I2S
 v
PCM5102A
 |      |
 |      + local charge pump/decoupling
 |
470R / 2.2nF
 |
RCA L/R at board edge
~~~

PCM5102A držati dalje od:

- MP3202 backlight switch node
- TPS62132 inductor/SW
- TLV62569 core DCDC
- USB HS pair
- C6 antenna
- 5V high-current USB routing

---

# 24. I²S routing

Priority:

1. BCLK
2. LRCK
3. DATA

Pravila:

- kratko
- series R uz P4
- solid GND reference
- ne routeati paralelno uz OUTL/OUTR
- ne prelaziti preko ground splitova
- ne routeati uz switch node

I²S nije differential bus; nema potrebe za length matchingom kao MIPI/USB.

---

# 25. Output routing

OUTL/OUTR nakon DAC-a:

- kratko
- udaljeno od digital clockova
- okruženo GND gdje praktično
- bez via ako nije potrebno
- L/R približno simetrična geometrija
- output RC mreža blizu DAC/RCA zone

---

# 26. Proposed firmware behavior

Boot:

1. GPIO49 konfigurirati output LOW
2. init audio engine
3. start I²S BCLK/LRCK/DATA
4. pričekati najmanje 16 LRCK perioda + sigurnosnu marginu
5. dodatno pričekati nekoliko ms da se output stabilizira
6. GPIO49 HIGH
7. ramp software master volume ako želimo još mekši start

Shutdown/reboot:

1. GPIO49 LOW
2. wait ≥3 ms
3. stop I²S
4. continue shutdown

Fault:

- clock loss sam PCM5102A također detektira i automatski mutea
- firmware svejedno drži XSMT kontrolu kao deterministički master mute

---

# 27. Test points

Digital:

- TP_I2S_BCLK
- TP_I2S_LRCK
- TP_I2S_DATA
- TP_DAC_XSMT

Analog/power:

- TP_3V3_AUDIO
- TP_DAC_VNEG
- TP_DAC_OUTL
- TP_DAC_OUTR
- TP_AUDIO_GND

Analog testpointovi mali i bez dugih stubova.

---

# 28. Preliminary BOM

| RefDes | Qty | Part/value |
|---|---:|---|
| U5 | 1 | PCM5102APWR |
| FB_AUDIO | 1 | 0 Ω default / ferrite option |
| C_AUDIO_BRANCH | 1 | 10 µF |
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
| R_OUT_L | 1 | 470 Ω |
| R_OUT_R | 1 | 470 Ω |
| C_OUT_L | 1 | 2.2 nF C0G/NP0 |
| C_OUT_R | 1 | 2.2 nF C0G/NP0 |
| J_RCA_L | 1 | RCA TBD-MECH |
| J_RCA_R | 1 | RCA TBD-MECH |
| J_LINE_35 | 0 | removed from Rev A in M1-MECH-A8 |
| D_AUDIO_L | 0/1 | low-C ESD DNP |
| D_AUDIO_R | 0/1 | low-C ESD DNP |

---

# 29. KiCad nets

~~~text
3V3_SYS
3V3_AUDIO

P4_I2S_BCLK
P4_I2S_LRCK
P4_I2S_DOUT

DAC_XSMT

DAC_OUTL_RAW
DAC_OUTR_RAW

MAIN_L
MAIN_R

DAC_VNEG
GND
~~~

---

# 30. Bring-up sequence

## Phase 1 — power

- 3V3_AUDIO
- DVDD
- AVDD
- CPVDD
- LDOO ~1.8 V
- VNEG ~negative rail

## Phase 2 — clocks

- SCK = 0 V
- BCLK valid
- LRCK valid
- DATA active
- XSMT LOW

## Phase 3 — unmute

- XSMT HIGH
- output returns from mute cleanly
- no pop

## Phase 4 — analog

Inject:

- 1 kHz
- -1 dBFS
- both channels

Measure:

- Vrms
- THD+N
- channel balance
- DC offset
- noise floor

---

# 31. System interference tests

Ponoviti analogno mjerenje u stanjima:

- Wi-Fi OFF / ON / iperf TX
- USB0 idle / sustained storage read
- USB1 FLX4 UAC active
- full LCD backlight
- low PWM backlight
- dual-deck playback
- microSD access

Tražimo:

- RF buzz
- switching whine
- USB frame-correlated noise
- backlight PWM tones
- ground-loop artifacts

---

# 32. Pop/click acceptance

Testirati najmanje:

- 100 cold boots
- 100 software reboots
- 100 planned powerdowns
- USB plug/unplug tijekom idle
- Wi-Fi startup
- rapid track starts/stops

Acceptance:

**nema neprihvatljivog audible pop/click na MAIN OUT**

Ako postoji:

1. scope XSMT
2. scope I²S start/stop
3. provjeriti power rail collapse order
4. povećati mute timing
5. po potrebi dodati external power-sense behavior na XSMT u Rev B

---

# 33. Schematic review checklist

- [ ] PCM5102APWR TSSOP-20 pin mapping verified
- [ ] SCK hard-tied GND
- [ ] FMT GND
- [ ] FLT GND
- [ ] DEMP GND
- [ ] XSMT GPIO49 + 100k pulldown
- [ ] BCK/LRCK/DATA 22R source series
- [ ] AVDD 100nF + 10uF
- [ ] CPVDD 100nF + 10uF
- [ ] CAPP-CAPM 2.2uF
- [ ] VNEG 2.2uF to CPGND
- [ ] DVDD 100nF + 10uF
- [ ] LDOO 100nF
- [ ] OUT L/R 470R + 2.2nF
- [ ] no output DC-block caps
- [ ] solid shared ground
- [ ] RCA mechanical MPN pending
- [x] J6 optional 3.5 mm removed from Rev A — M1-MECH-A8

---

# 34. Zaključak

Pajoniiir Rev A MAIN audio:

~~~text
ESP32-P4
 GPIO50 BCLK --22R--
 GPIO52 LRCK --22R-- > PCM5102APWR
 GPIO51 DATA --22R--
 GPIO49 XSMT -------->

SCK = GND
FMT = GND
FLT = GND
DEMP = GND

3V3_SYS -> 0R/FB -> 3V3_AUDIO

OUTL -> 470R -> MAIN_L
                |
               2.2nF
                |
               GND

OUTR -> 470R -> MAIN_R
                |
               2.2nF
                |
               GND
~~~

Custom board time dobiva deterministički boot mute i planirani soft powerdown, što je kvalitativno poboljšanje u odnosu na jednostavni breakout prototip.

**Sljedeći blok:** 10_DISPLAY_MIPI — ST7701S panel, DSI lanes, 2.5 V DPHY rail, exact FPC dependency i backlight power.
