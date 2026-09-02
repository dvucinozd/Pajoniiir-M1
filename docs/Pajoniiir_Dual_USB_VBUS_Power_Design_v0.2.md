# Pajoniiir Mainboard — Dual USB VBUS Power Design v0.2

**Projekt:** Pajoniiir BL-A1800 / Pajoniiir-M1  
**Ploča:** Pajoniiir Mainboard Rev A  
**Blok:** 06_USB_POWER  
**Datum:** 2026-09-02  
**Status:** Engineering design candidate — revidirano nakon TPS2561 arhitekturnog audita

---

# 1. Zašto v0.2 mijenja originalni TPS2561 koncept

Prvotni plan koristio je jedan **TPS2561** dual-channel switch.

Detaljni datasheet review pokazao je važnu karakteristiku:

- TPS2561 ima dva odvojena output kanala
- dva odvojena EN pina
- dva odvojena FAULT pina
- ali **jedan zajednički ILIM pin / jedan RILIM**
- oba porta zato koriste isti programirani current-limit threshold

To nije idealno za Pajoniiir jer USB0 napaja Rekordbox storage, a USB1 DDJ-FLX4. Ta dva uređaja nemaju nužno isti current profile i želimo zasebno optimizirati limit i recovery po portu.

Zato je Rev A primary architecture promijenjena na:

**2 × TPS25221**

---

# 2. Novi primary USB power switch

USB0:

**U_USB0 = TPS25221DRVR**

USB1:

**U_USB1 = TPS25221DRVR**

Package:

- WSON-6 / DRV
- 2 × 2 mm

Alternativa za lakši hand-rework prototype:

**TPS25221DBVR**, SOT-23-6 / DBV.

---

# 3. Zašto TPS25221

TPS25221 je aktivni TI USB/power-distribution switch s:

- 2.5–5.5 V operating range
- 2 A continuous output capability
- 0.275–2.7 A programmable current-limit range
- približno 70 mΩ typical RON
- built-in soft-start
- približno 1.5 µs short-circuit response
- active-high EN
- active-low open-drain FAULT
- približno 8 ms FAULT deglitch
- reverse-current blocking kada je disabled
- zaseban RILIM po svakom fizičkom IC-u

Dva zasebna IC-a daju Pajoniiiru stvarno neovisna USB power kanala.

---

# 4. Topologija

~~~text
                         +-------------------------+
                         |       5V_SYS            |
                         +-----------+-------------+
                                     |
                  +------------------+------------------+
                  |                                     |
                  v                                     v
          TPS25221 USB0                         TPS25221 USB1
          EN0 / FLT0 / ILIM0                   EN1 / FLT1 / ILIM1
                  |                                     |
                  v                                     v
             USB0_VBUS                             USB1_VBUS
                  |                                     |
                  v                                     v
          Rekordbox storage                         DDJ-FLX4
~~~

Fault ili short na jednom portu ne smije namjerno isključiti drugi port.

---

# 5. USB0 current-limit target

USB0 je mass-storage port.

Za Rev A početni cilj:

**nominal current limit približno 1.0 A**

TI common resistor table za TPS25221 daje za 54.9 kΩ, uz 1% resistor toleranciju, približno:

~~~text
RILIM = 54.9 kΩ 1%
IOS(min) ≈ 898 mA
IOS(nom) ≈ 1003 mA
IOS(max) ≈ 1092 mA
~~~

Rev A:

**R_USB0_ILIM = 54.9 kΩ 1%**

Finalno potvrditi stvarnim Rekordbox stickovima koje očekujemo podržavati.

---

# 6. USB1 current-limit target

USB1 napaja DDJ-FLX4 i mora tolerirati:

- enumeration
- MIDI
- LED activity
- 4-channel UAC
- startup transient
- reconnect

Ne želimo naslijpo pretpostaviti stvarnu FLX4 potrošnju.

Za Rev A karakterizaciju postavljamo početni nominalni limit:

**približno 1.6 A**

TI common resistor table:

~~~text
RILIM = 34.8 kΩ 1%
IOS(min) ≈ 1438 mA
IOS(nom) ≈ 1585 mA
IOS(max) ≈ 1699 mA
~~~

Rev A initial:

**R_USB1_ILIM = 34.8 kΩ 1%**

Ovo nije finalni production limit. Nakon stvarnog mjerenja FLX4 current profila limit treba spustiti na najnižu vrijednost koja pouzdano prolazi normalni startup i maksimalno realno opterećenje s marginom.

---

# 7. EN strategy

TPS25221 je active-high.

Želimo **default OFF tijekom P4 reset/boot faze**.

Za svaki port:

~~~text
P4_GPIO ----> EN
               |
             100k
               |
              GND
~~~

Rev A:

- R_USB0_EN_PD = 100 kΩ
- R_USB1_EN_PD = 100 kΩ

Prednosti:

- clean P4 boot
- nema random VBUS pulseva dok su GPIO-i floating
- kontrolirana device enumeration sekvenca
- firmware power-cycle recovery

---

# 8. Proposed P4 control GPIO allocation

| Funkcija | P4 GPIO | Status |
|---|---:|---|
| USB0_PWR_EN | GPIO20 | LOCK-CANDIDATE |
| USB0_FAULT_N | GPIO21 | LOCK-CANDIDATE |
| USB1_PWR_EN | GPIO22 | LOCK-CANDIDATE |
| USB1_FAULT_N | GPIO32 | LOCK-CANDIDATE |

Prije finalnog schematic locka napraviti puni v3.x GPIO conflict audit protiv MIPI/USB PHY/finalnog board layera.

---

# 9. FAULT outputs

TPS25221 FAULT je open-drain active LOW. Overcurrent reporting ima oko 8 ms deglitch.

Za svaki port:

~~~text
3V3_SYS
   |
 10k
   |
FAULT_N -------- P4 GPIO
~~~

Rev A:

- R_USB0_FLT_PU = 10 kΩ
- R_USB1_FLT_PU = 10 kΩ

Nets:

- USB0_FAULT_N
- USB1_FAULT_N

---

# 10. Firmware recovery behavior

USB0:

1. detektirati FAULT
2. zaustaviti storage I/O / unmountati ako je moguće
3. USB0_PWR_EN = 0
4. čekati recovery timeout
5. ponovno uključiti VBUS
6. re-enumerirati storage

USB1:

1. detektirati FAULT
2. označiti FLX4 MIDI/UAC offline
3. USB1_PWR_EN = 0
4. čekati
5. ponovno uključiti
6. re-enumerirati MIDI/UAC

Fault na USB0 ne smije resetirati USB1 i obrnuto.

---

# 11. Switch input decoupling

TI preporučuje najmanje 0.1 µF ceramic od IN prema GND neposredno uz switch.

Za svaki TPS25221:

- C_USB0_IN = 100 nF
- C_USB1_IN = 100 nF

Uz zajednički 5V_SYS backbone predvidjeti i lokalni:

- C_USB_PWR_LOCAL = 10 µF

---

# 12. Output capacitance

Rev A po portu:

~~~text
100 nF ceramic
47 µF low-ESR bulk initial
optional 100 µF DNP footprint
~~~

Dakle:

- C_USB0_OUT_HF = 100 nF
- C_USB0_OUT_BULK = 47 µF
- C_USB0_OUT_OPT = 100 µF DNP
- C_USB1_OUT_HF = 100 nF
- C_USB1_OUT_BULK = 47 µF
- C_USB1_OUT_OPT = 100 µF DNP

Finalne vrijednosti zaključati nakon hotplug/inrush mjerenja.

Previše capacitancea povećava inrush i startup stress; premalo capacitancea povećava VBUS dip. Zato Rev A ima tuning footprintove.

---

# 13. Reverse-current/backfeed protection

TPS25221 blokira reverse current kada je disabled.

Tijekom EVT-a obavezno testirati:

- port disabled
- vanjski device priključen
- nema značajnog napajanja natrag prema 5V_SYS
- drugi port ostaje potpuno funkcionalan

---

# 14. VBUS voltage-drop budget

TPS25221 tipični RON je približno 70 mΩ.

Pri 1 A:

~~~text
Vdrop ≈ 1 A × 0.07 Ω = 70 mV
~~~

Pri 1.6 A:

~~~text
Vdrop ≈ 112 mV
~~~

Na to se dodaju:

- input eFuse drop
- PCB trace drop
- connector drop
- cable drop

Zato USB1 treba posebno izmjeriti na samom USB connector VBUS pinu pod FLX4 peak loadom.

---

# 15. VBUS routing

Svaki VBUS path:

- projektirati za najmanje 2 A continuous capability
- kratko
- široko
- minimalan broj via
- koristiti više paralelnih via ako je promjena layera nužna
- bez uskog neck-downa uz switch

Predloženi PCB net class:

**USB_VBUS_HIGH_CURRENT**

---

# 16. Optional characterization shunt

Rev A može imati po portu 0 Ω jumper footprint u 1206/2010 formatu s Kelvin test padovima.

Normalno:

**0 Ω**

Tijekom laboratorijske karakterizacije može se privremeno zamijeniti 10–20 mΩ shuntom samo ako je dodatni voltage drop prihvatljiv.

Time možemo precizno izmjeriti storage inrush i FLX4 startup bez trajnog current-monitor IC-a.

---

# 17. USB0 power block

~~~text
5V_SYS
 |
100nF
 |
TPS25221 U_USB0
 |
 +-- ILIM -> 54.9k -> GND
 +-- EN   <- GPIO20 + 100k pulldown
 +-- FLT  -> GPIO21 + 10k pullup 3V3
 |
USB0_VBUS
 |
100nF + 47uF + optional 100uF
 |
USB-A STORAGE
~~~

---

# 18. USB1 power block

~~~text
5V_SYS
 |
100nF
 |
TPS25221 U_USB1
 |
 +-- ILIM -> 34.8k -> GND
 +-- EN   <- GPIO22 + 100k pulldown
 +-- FLT  -> GPIO32 + 10k pullup 3V3
 |
USB1_VBUS
 |
100nF + 47uF + optional 100uF
 |
USB-A -> DDJ-FLX4
~~~

---

# 19. Port power-up sequencing

Preporučeni boot:

1. 5V_SYS valid
2. 3V3_SYS valid
3. P4 boot
4. USB host driver init
5. USB0_PWR_EN = 1
6. wait VBUS settle
7. USB0 enumerate storage
8. USB1_PWR_EN = 1
9. wait VBUS settle
10. USB1 enumerate FLX4

Staggering smanjuje simultani inrush.

---

# 20. Main eFuse coordination

Main TPS259474A nominalni threshold je trenutno oko 4.45 A typ.

Port limits initial:

~~~text
USB0 ≈1.0 A nominal
USB1 ≈1.6 A nominal
~~~

Čak i uz tolerance peaks ukupni port current ostavlja marginu za P4/system/LCD/C6/SD/audio, ali koordinacija se mora potvrditi stvarnim mjerenjem.

Main eFuse ne bi trebao prvi tripati kod normalnog single-port USB faulta.

---

# 21. Preliminary BOM

| RefDes | Qty | Value / MPN | Status |
|---|---:|---|---|
| U_USB0 | 1 | TPS25221DRVR | LOCK-CANDIDATE |
| U_USB1 | 1 | TPS25221DRVR | LOCK-CANDIDATE |
| R_USB0_ILIM | 1 | 54.9 kΩ 1% | EVT initial |
| R_USB1_ILIM | 1 | 34.8 kΩ 1% | EVT initial |
| R_USB0_EN_PD | 1 | 100 kΩ | required |
| R_USB1_EN_PD | 1 | 100 kΩ | required |
| R_USB0_FLT_PU | 1 | 10 kΩ | required |
| R_USB1_FLT_PU | 1 | 10 kΩ | required |
| C_USB0_IN | 1 | 100 nF | required |
| C_USB1_IN | 1 | 100 nF | required |
| C_USB_PWR_LOCAL | 1 | 10 µF | recommended |
| C_USB0_OUT_HF | 1 | 100 nF | output |
| C_USB1_OUT_HF | 1 | 100 nF | output |
| C_USB0_OUT_BULK | 1 | 47 µF | EVT initial |
| C_USB1_OUT_BULK | 1 | 47 µF | EVT initial |
| C_USB0_OUT_OPT | 1 | 100 µF | DNP tuning |
| C_USB1_OUT_OPT | 1 | 100 µF | DNP tuning |
| R_USB0_SHUNT | 1 | 0 Ω | optional measurement location |
| R_USB1_SHUNT | 1 | 0 Ω | optional measurement location |

---

# 22. KiCad nets

~~~text
5V_SYS
USB0_VBUS
USB1_VBUS
USB0_PWR_EN
USB1_PWR_EN
USB0_FAULT_N
USB1_FAULT_N
USB0_ILIM
USB1_ILIM
~~~

---

# 23. Required test points

- TP_USB0_VBUS
- TP_USB1_VBUS
- TP_USB0_EN
- TP_USB1_EN
- TP_USB0_FAULT_N
- TP_USB1_FAULT_N
- TP_USB0_ILIM
- TP_USB1_ILIM
- TP_5V_SYS_USB
- TP_GND_USB

---

# 24. EVT measurement matrix

USB0:

- empty port VBUS
- stick insert peak
- mount
- sequential/random read
- remove/reinsert
- controlled short test

USB1:

- FLX4 cold attach peak
- enumeration
- MIDI only
- LEDs active
- 4ch UAC active
- playback
- reconnect
- fault/recovery

Combined:

- USB0 read
- USB1 UAC/MIDI
- Wi-Fi TX
- full backlight
- dual-deck DSP

---

# 25. Acceptance criteria

- USB0 and USB1 mogu se neovisno disableati
- disabled port nema značajan backfeed
- svaki FAULT input radi
- short na USB0 ne ubija USB1
- short na USB1 ne ubija USB0
- nema P4 brownouta pri normalnom attachu
- nema main eFuse tripa pri valjanom USB startupu
- VBUS ostaje u dopuštenom području pod normalnim loadom
- switch temperature prihvatljiva
- firmware može neovisno recoverati svaki port

---

# 26. TPS2561 status nakon redesign-a

TPS2561 nije loš dio i ostaje fallback ako mjerenja pokažu da oba porta mogu sigurno koristiti isti current limit.

Za Rev A engineering board važniji su:

- individualni RILIM
- individualni fault isolation
- mogućnost zasebnog tuninga USB0 i FLX4

Status:

**TPS2561 = ALT / NOT PRIMARY**

---

# 27. Zaključak

Rev A USB power architecture:

~~~text
USB0:
TPS25221DRVR
RILIM = 54.9k
~1.0 A nominal
GPIO20 EN
GPIO21 FAULT_N

USB1:
TPS25221DRVR
RILIM = 34.8k
~1.6 A nominal initial
GPIO22 EN
GPIO32 FAULT_N

both:
default OFF
firmware controlled
independent fault
independent current limit
reverse blocking when disabled
47uF + 100nF output initial
~~~

Ovaj dizajn bolje odgovara stvarnom Pajoniiir zahtjevu od prvotnog TPS2561 rješenja.

**Sljedeći blokovi:** 07_USB0_STORAGE i 08_USB1_FLX4 — D+/D− PHY routing, USB-A konektori, ESD zaštita, shield/grounding i SI pravila.
