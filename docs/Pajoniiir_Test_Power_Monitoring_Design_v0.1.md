# Pajoniiir Mainboard — Test & Power Monitoring Design v0.1

**Projekt:** Pajoniiir BL-A1800 / Pajoniiir-M1  
**Ploča:** Pajoniiir Mainboard Rev A  
**Blok:** 14_TEST_MONITORING  
**Datum:** 2026-09-02  
**Status:** Engineering design candidate — telemetry optional/DNP for Rev A

---

# 1. Cilj

Pajoniiir je već pokazao da USB hotplug i load transients mogu izazvati brownout na development-board power topologiji.

Zato Rev A treba imati dovoljno mjernih točaka da možemo objektivno razlikovati:

- input adapter problem
- main eFuse trip
- 5V_SYS droop
- 3V3_SYS droop
- USB0/USB1 inrush
- Wi-Fi burst
- SD inrush
- backlight load
- P4 core instability

Rev A zato dobiva opcionalnu digitalnu 5V_SYS telemetriju.

---

# 2. Optional power monitor

Primary candidate:

**INA238AIDGSR**

Status:

**ACTIVE**

Relevantno:

- 16-bit ADC
- I2C
- shunt current measurement
- bus voltage measurement
- calculated power
- ALERT output
- 2.7–5.5 V device supply
- 16 selectable addresses
- high-side sensing

Rev A:

**DNP-CAPABLE**

Footprint i shunt se projektiraju, ali monitor se može izostaviti u cost-down BOM-u nakon DVT-a.

---

# 3. Measurement location

INA238 mjeri glavni protected 5 V rail nakon eFusea, prije grananja na potrošače.

~~~text
TPS259474A
    |
5V_PROTECTED
    |
 R_SHUNT
    |
5V_SYS
    |
    +-- 3V3 buck
    +-- USB0
    +-- USB1
    +-- backlight
~~~

Time mjerimo ukupnu stvarnu potrošnju uređaja.

---

# 4. Shunt resistor

Rev A:

**R_SYS_SHUNT = 5 mΩ, 1%, 1 W, 2512, 4-terminal/Kelvin preferred**

Pri 4.5 A:

~~~text
Vshunt = 4.5 A × 0.005 Ω
       = 22.5 mV

P = I²R
  = 4.5² × 0.005
  ≈ 101 mW
~~~

To daje veliku thermal marginu i mali voltage drop.

Uz INA238 ±40.96 mV range:

~~~text
IFS ≈ 40.96 mV / 5 mΩ
    ≈ 8.19 A
~~~

što je dobar mjerni raspon za Pajoniiir.

---

# 5. Kelvin sensing

Shunt mora imati:

- high-current pads/traces
- zasebne thin Kelvin sense traceove s unutarnje strane shunt padova
- IN+ i IN− se ne smiju spojiti na udaljene high-current net nodeove

Layout:

~~~text
power trace ==== [ RSHUNT ] ==== power trace
                  |      |
               Kelvin+ Kelvin-
                  |      |
                 INA238
~~~

Bez shared copper dropa u sense pathu.

---

# 6. INA input filter

Rev A initial:

~~~text
IN+ -- 10 Ω --+
              |
            100 nF
              |
IN- -- 10 Ω --+
~~~

R_FILTER_P = 10 Ω  
R_FILTER_N = 10 Ω  
C_FILTER = 100 nF

TI dopušta do 100 Ω, ali koristimo 10 Ω radi minimalne dodatne gain error osjetljivosti.

---

# 7. INA238 power

~~~text
3V3_SYS -> INA238 VS
          |
         100 nF
          |
         GND
~~~

Dodatno 1 µF lokalno.

RefDes:

- C_INA_HF = 100 nF
- C_INA_LOCAL = 1 µF

---

# 8. I2C bus

INA238 se može spojiti na shared P4 I2C:

~~~text
GPIO7 SDA
GPIO8 SCL
~~~

Touch i INA238 koriste isti fizički bus.

Odabrana adresa:

**0x40**

A0 = GND  
A1 = GND

To ne kolidira s GT911 0x5D.

Postojeći touch pull-upovi mogu služiti busu; ne duplicirati nepotrebne jake pull-upove na INA sheetu.

---

# 9. ALERT

INA238 ALERT je koristan za brownout/power-envelope debugging.

Predloženi GPIO:

**GPIO53 = SYS_POWER_ALERT_N**

Status:

**LOCK-CANDIDATE / optional**

Topologija:

~~~text
3V3_SYS
 |
10k
 |
SYS_POWER_ALERT_N ---- GPIO53
       |
     INA238 ALERT
~~~

Ako INA238 nije populiran:

GPIO53 ostaje slobodan.

---

# 10. Alert use cases

Firmware može konfigurirati ALERT za:

- overcurrent
- overpower
- bus undervoltage
- conversion-ready tijekom test firmwarea

Najkorisnije u EVT/DVT:

**5V_SYS undervoltage** i **system overcurrent**.

P4 tada može timestampati power incident uz:

- USB fault state
- Wi-Fi state
- SD state
- audio load
- backlight duty

---

# 11. Optional rail dividers

Ne treba digitalni monitor na svakom railu.

Predvidjeti P4 ADC DNP dividers samo za engineering:

## 5V_SYS_ADC

Primjer:

~~~text
5V_SYS -- 100k --+-- 100k -- GND
                 |
               ADC pin
                 |
               100nF
                 |
                GND
~~~

Ali zbog GPIO budgeta i zato što INA238 već mjeri 5V_SYS, ovo nije primary.

Status:

**DNP / not required**

---

# 12. USB port current characterization

Ne dodajemo dva dodatna INA238 u production baseline.

USB0 i USB1 već imaju optional shunt/jumper measurement footprints iz USB power designa.

Tijekom EVT-a:

- USB0 measure with current probe or temporary low-ohm shunt
- USB1 measure with current probe or temporary low-ohm shunt

Total system current kontinuirano bilježi INA238.

---

# 13. Critical rail test points

Mandatory large/accessible:

~~~text
TP_VIN_5V
TP_5V_SYS
TP_3V3_SYS
TP_P4_VDD_HP
TP_3V3_C6
TP_3V3_AUDIO
TP_3V3_SD
TP_USB0_VBUS
TP_USB1_VBUS
TP_MIPI_2V5
TP_LEDA
~~~

GND:

najmanje 3 scope-friendly ground loops oko ploče:

- power area
- P4/digital area
- audio/display area

---

# 14. Scope probe philosophy

Za railove:

- normalni test pointovi
- ground spring-friendly pad blizu raila

Za high-speed buses:

- nema velikih loops
- samo micro probe pads gdje stvarno potrebno

Testability ne smije uništiti signal integrity.

---

# 15. Thermal monitoring

INA238 ima internal die temperature sensing, ali ne mjeri hotspot drugih regulatora.

EVT thermal survey treba obuhvatiti:

- TPS259474A
- TPS62132
- TLV62569
- USB0 TPS25221
- USB1 TPS25221
- MP3202
- ESP32-P4
- ESP32-C6
- PCM5102A
- SD load switch

IR kamera / thermocouple measurement pri worst-case combined loadu.

---

# 16. Brownout event capture

Recommended test firmware ring buffer:

~~~text
timestamp
5V_SYS_mV
system_mA
system_mW
3V3 status
eFuse PG
USB0 fault
USB1 fault
USB0 enabled
USB1 enabled
SD powered
Wi-Fi state
backlight %
deck/audio load state
reset reason
~~~

Kod reboot-a zadnjih N sampleova spremiti u retained/crash log ako je moguće.

---

# 17. Sampling rate

INA238 nije audio-rate instrument.

Za power diagnostics dovoljno:

- normal telemetry: 10–50 samples/s
- stress diagnostics: 100–500 samples/s ovisno o conversion time/averaging
- pravi microsecond transient i dalje se mjeri osciloskopom

Digital monitor i scope se nadopunjuju.

---

# 18. DNP strategy

Rev A PCB footprint sadrži INA238 i shunt.

Opcije:

## EVT

populate:
- shunt
- INA238
- ALERT
- full telemetry

## Cost-down production

Ako se INA238 uklanja:

- R_SHUNT se zamijeni 0 Ω high-current jumperom ili footprint-compatible shuntom po dizajnu
- INA footprint DNP
- ALERT GPIO oslobođen

Bolje je zadržati 5 mΩ shunt samo ako njegov cost/drop nije problem.

---

# 19. Preliminary BOM

| RefDes | Qty | Part/value | Status |
|---|---:|---|---|
| U_MON | 0/1 | INA238AIDGSR | DNP-capable |
| R_SYS_SHUNT | 1 | 5 mΩ 1%, ≥1 W, Kelvin/4-terminal preferred | EVT |
| R_INA_P | 1 | 10 Ω | filter |
| R_INA_N | 1 | 10 Ω | filter |
| C_INA_DIFF | 1 | 100 nF | filter |
| C_INA_HF | 1 | 100 nF | supply |
| C_INA_LOCAL | 1 | 1 µF | supply |
| R_INA_ALERT_PU | 1 | 10 kΩ | optional |
| TP_RAIL_* | set | test pads | mandatory |
| TP_GND_LOOP_* | 3+ | scope ground loops | mandatory |

---

# 20. GPIO allocation update

~~~text
GPIO53 -> SYS_POWER_ALERT_N
~~~

samo kada je INA238 populiran.

Ovo je optional function i ne smije blokirati buduću važniju funkciju.

---

# 21. Factory use

Factory test može koristiti INA238 za:

- no-load current sanity
- boot current envelope
- detect assembly short/high-current board
- full-load power sanity
- USB attach power delta

Primjer:

~~~text
boot_idle_current within expected window
USB0_delta within expected window
USB1_delta within expected window
backlight_delta within expected window
~~~

To je vrlo korisno za proizvodni screening.

---

# 22. Acceptance

Monitoring subsystem prolazi ako:

- current reading usporediv s bench DMM-om
- no measurable impact on 5V_SYS stability
- ALERT radi
- I2C ne interferira s GT911
- shunt nema thermal issue
- Kelvin layout daje stabilno mjerenje
- monitor može biti DNP bez promjene funkcije ostatka boarda

---

# 23. Zaključak

Rev A monitoring:

~~~text
5V_PROTECTED
   |
5mΩ Kelvin shunt
   |
5V_SYS
   |
INA238 high-side measurement

INA238:
3V3_SYS supply
I2C address 0x40
GPIO7/8 shared bus
GPIO53 optional ALERT
~~~

Ovo daje Pajoniiiru ugrađeni engineering alat za dokazivanje power margine i hvatanje brownout uzroka bez oslanjanja samo na subjektivno opažanje.
