# Pajoniiir Mainboard — 3V3 System Rail Design v0.1

**Projekt:** Pajoniiir BL-A1800 / Pajoniiir-M1  
**Ploča:** Pajoniiir Mainboard Rev A  
**Blok:** 02_POWER_3V3  
**Datum:** 2026-09-02  
**Status:** Captured in KiCad; production validation remains EVT work

> **Post-capture update (2026-09-04):** The TPS62132 design is captured. The active display load is the DSI506 module on `3V3_DISPLAY_MODULE` (up to 340 mA documented), and the former separate GT911/MP3202 display path is retired. Final all-on rail and display-transient margin remain EVT work.

---

# 1. Cilj

Ovaj blok pretvara `5V_SYS` u glavni digitalni `3V3_SYS` rail.

Glavni kandidat je:

**TPS62132RGTR**

Važna korekcija u odnosu na raniji preliminarni BOM:

- TPS62132 = fixed **3.3 V**
- TPS62133 = fixed **5.0 V**

Za Pajoniiir se zato koristi TPS62132.

---

# 2. Zašto TPS62132

TPS62132 je aktivni TI synchronous buck:

- VIN = 3–17 V
- fixed VOUT = 3.3 V
- do 3 A
- DCS-Control
- oko 2.5 MHz default switching frequency
- programmable soft-start
- Power Good
- 100% duty-cycle mode
- QFN 3×3 mm

Za Rev A je koristan jer je dovoljno snažan, dobro dokumentiran i fizički nije ekstremno sitan.

TI navodi noviji TPS62903 kao alternativu, ali za prvi Pajoniiir PCB ostajemo na TPS62132 jer je 3×3 mm QFN zahvalniji za prototipiranje i debug.

---

# 3. Consumers of 3V3_SYS

Glavni 3.3 V rail napaja:

- ESP32-P4 relevantne 3.3 V power domene
- external QSPI flash
- ESP32-C6-WROOM-1
- PCM5102A
- GT911 / touch logiku gdje je kompatibilno
- microSD
- LCD logic rail gdje finalni panel zahtijeva 3.3 V
- pull-up mreže
- debug/status logiku

P4 `VDD_HP` core rail nije direktno 3.3 V load nego se iz 3V3_SYS generira lokalnim TLV62569 core DCDC blokom.

---

# 4. Topologija

```text
5V_SYS
  |
  +---- 10uF
  +---- 100nF
  |
  v
TPS62132
  |
  SW
  |
  +---- L = 2.2uH
  |
  v
3V3_SYS
  |
  +---- 22uF
  +---- local bulk/distribution
```

---

# 5. U8 — TPS62132RGTR pin strategy

```text
PVIN  -> 5V_SYS
AVIN  -> 5V_SYS
EN    -> enabled from 5V_SYS / sequencing option
SW    -> inductor
VOS   -> 3V3_SYS sense
PG    -> 3V3_PG
FB    -> AGND on fixed-output version
SS/TR -> soft-start capacitor
DEF   -> LOW for nominal 3.3V
FSW   -> LOW for ~2.5MHz default
AGND  -> GND / exposed pad
PGND  -> GND / exposed pad
EPAD  -> GND plane
```

TI za fixed-output verzije preporučuje FB spojiti na AGND.

---

# 6. Input capacitors

TI reference design za 3.3 V/3 A koristi:

- 10 µF input
- 0.1 µF high-frequency bypass

Rev A:

| RefDes | Value | Type |
|---|---:|---|
| C_3V3_IN1 | 10 µF | X7R/X5R, ≥10 V |
| C_3V3_IN2 | 100 nF | X7R, ≥10 V |

Oba moraju biti neposredno uz PVIN/AVIN power loop.

Dodatni 10 µF footprint može se ostaviti DNP ako transient test pokaže potrebu.

---

# 7. Inductor

TI reference 3.3 V/3 A aplikacija koristi:

**1 µH ili 2.2 µH**

Za Pajoniiir Rev A preferiramo:

**2.2 µH**

Razlozi:

- niži ripple
- bolji EMI margin
- TI ga koristi u karakterizacijskim grafovima
- prikladan za full 3 A rail

Za FSW ≈ 2.5 MHz 2.2 µH je konzervativan izbor.

Kandidat klase:

```text
2.2 µH
shielded
Isat >= 4.5–5 A preferred
low DCR
~4x4 mm class
```

Exact MPN ostaje TBD nakon availability/thermal provjere.

---

# 8. Output capacitor

TI tipična 3.3 V shema:

**22 µF**

Rev A:

| RefDes | Value | Type |
|---|---:|---|
| C_3V3_OUT1 | 22 µF | X7R/X5R, ≥6.3 V |
| C_3V3_OUT2 | 100 nF | X7R |

Važno je računati DC-bias gubitak ceramic capacitance.

Ako nominalni 22 µF MLCC pod 3.3 V realno padne znatno ispod toga, koristiti:

- veći package
- viši voltage rating
- ili 2×22 µF

Predvidjeti mjesto za drugi 22 µF DNP footprint.

---

# 9. FSW

Pin FSW ima internal pulldown.

LOW daje približno:

**2.5 MHz**

To je default Rev A konfiguracija.

Prednosti:

- manji inductor
- brži transient response
- jednostavan reference layout

Ako kasnije EMI/audio mjerenje pokaže problem, moguće je razmotriti 1.25 MHz mode.

Za Rev A:

```text
FSW = GND / default LOW
```

uz opcionalni 0 Ω strap footprint.

---

# 10. DEF

TPS62132 DEF:

- LOW = nominal 3.3 V
- HIGH = nominal +5%

Pajoniiir treba:

```text
DEF = LOW
```

Ne trebamo 3.465 V margin mode kao normalni rad.

Ostaviti 0 Ω strap kako bi se u laboratoriju mogao testirati +5% rail ako ikad zatreba, ali DNP alternativni path.

---

# 11. Soft-start

TI reference circuit koristi:

**3.3 nF** na SS/TR.

Rev A default:

```text
C_SS = 3.3 nF
```

Cilj je clean startup nakon 5V_SYS eFuse ramp-a.

Treba osciloskopom provjeriti odnos:

- 5V_SYS rise
- 3V3_SYS rise
- P4 CHIP_PU
- P4 VDD_HP

Ako je 3V3 startup prerano ili prebrz, C_SS se može povećati.

---

# 12. EN

EN ima internal pulldown, pa mora biti deterministički high za normalni rad.

Najjednostavniji Rev A:

```text
5V_SYS -> R_EN -> EN
```

Početni R_EN:

**100 kΩ**

Opcionalno dodati footprint kojim P4 ili supervisor može u budućnosti preuzeti enable.

Međutim, P4 ne može biti jedini kontroler vlastitog 3V3 regulatora tijekom cold boot-a.

Zato default mora biti hardware enabled.

---

# 13. Power Good

PG je open-drain.

Net:

```text
3V3_PG
```

Početni pull-up:

```text
R_PG = 100 kΩ -> 3V3_SYS
```

TI reference figure koristi 100 kΩ.

Preporuka:

- dovesti `3V3_PG` na P4/supervisor samo ako startup architecture to koristi
- obavezno test point

PG je koristan tijekom bring-upa za dokaz da regulator nije samo “oko 3.3 V” nego je u regulation windowu.

---

# 14. VOS routing

VOS je output sense.

Ne uzimati VOS sa switch/inductor hot područja.

Routing pravilo:

```text
VOS sense point
   |
   +--- na 3V3_SYS kod output capacitor/load distribution nodea
```

Sense trace treba biti quiet Kelvin-like route prema stvarnom output nodeu.

---

# 15. Grounding

TPS62132 ima:

- AGND
- PGND
- exposed thermal pad

Sve ih treba povezati na common GND prema TI layout primjeru.

Ne raditi fizički odvojene “analog” i “power” ground otoke sa tankim spojem.

Umjesto toga:

- solid L2 ground plane
- kratki PGND return
- thermal vias ispod exposed pada
- AVIN/AGND layout tih i kompaktan

---

# 16. Switch node

`SW` je najbučniji net ovog bloka.

Pravila:

- minimalna površina
- vrlo kratko do L
- ne routeati ispod C6 antene
- ne routeati uz PCM5102A analog output
- ne routeati uz MIPI/USB HS ako nije nužno
- bez test pointa na finalnom proizvodu

Za EVT se eventualno može ostaviti mali scope pad, ali nije preporučen kao standardni TP.

---

# 17. Power distribution

Nakon output capacitor nodea:

```text
3V3_SYS
  |
  +---- P4 domains
  +---- P4 core DCDC input
  +---- FLASH
  +---- C6 filter -> 3V3_C6
  +---- AUDIO filter -> 3V3_AUDIO
  +---- microSD
  +---- touch
  +---- display logic
```

C6 i audio trebaju imati lokalni 0 Ω / ferrite option:

```text
3V3_SYS -- 0R/FB --> 3V3_C6
3V3_SYS -- 0R/FB --> 3V3_AUDIO
```

Default Rev A može koristiti 0 Ω, a ferrite se populira tek ako EMI/noise mjerenje pokaže korist.

---

# 18. Estimated load strategy

Ne zaključavamo finalni 3V3 current budget samo iz datasheet maksimuma.

Rev A treba mjeriti stvarni rail current u stanjima:

1. P4 boot
2. LCD/touch
3. Wi-Fi idle
4. Wi-Fi TX
5. SD read
6. USB0 active
7. USB1 active
8. dual-deck decode/DSP
9. all-on worst case

TPS62132 3 A daje dobru rezervu, ali thermal/layout validacija ostaje obavezna.

---

# 19. Test points

Obavezno:

```text
TP_5V_SYS_BUCK_IN
TP_3V3_SYS
TP_3V3_PG
TP_GND_3V3
```

Opcionalno:

```text
TP_SS_TR
```

Ne preporučuje se veliki SW testpoint.

---

# 20. Preliminary RefDes table

| RefDes | Part/value | Status |
|---|---|---|
| U8 | TPS62132RGTR | LOCK-CANDIDATE |
| C20 | 10 µF, ≥10 V | input |
| C21 | 100 nF, ≥10 V | input HF |
| C22 | 3.3 nF | SS/TR |
| L2 | 2.2 µH, Isat ≥4.5–5 A preferred | TBD MPN |
| C23 | 22 µF, ≥6.3 V | output |
| C24 | 22 µF | optional DNP output reserve |
| C25 | 100 nF | output HF |
| R20 | 100 kΩ | EN pull-up |
| R21 | 100 kΩ | PG pull-up |
| R22 | 0 Ω | FSW LOW strap / config |
| R23 | 0 Ω | DEF LOW strap / config |
| FB_C6 | 0 Ω default / ferrite option | branch |
| FB_AUDIO | 0 Ω default / ferrite option | branch |

---

# 21. KiCad nets

Inputs:

```text
5V_SYS
```

Outputs:

```text
3V3_SYS
3V3_PG
```

Derived child rails:

```text
3V3_C6
3V3_AUDIO
```

Local:

```text
BUCK_SW
BUCK_SS_TR
BUCK_EN
BUCK_FSW
BUCK_DEF
```

---

# 22. Bring-up measurement

Oscilloscope:

CH1 = 5V_SYS  
CH2 = 3V3_SYS  
CH3 = 3V3_PG  
CH4 = P4_VDD_HP

Provjeriti:

- monotonic 3V3 rise
- PG transition
- no overshoot
- no repeated startup
- load transient recovery
- rail noise

---

# 23. Acceptance criteria

Blok prolazi ako:

- 3V3_SYS = unutar TPS62132 regulation tolerance
- boot transient ne spušta rail ispod P4 dopuštenja
- Wi-Fi TX burst ne uzrokuje reset
- microSD access ne uzrokuje vidljiv rail collapse
- converter ne ulazi u thermal limit
- output ripple prihvatljiv
- nema audio-correlated switching artefakta
- PG je stabilan pri normalnom radu

---

# 24. Layout constraints

Najvažniji layout loopovi:

```text
5V_SYS -> input C -> PVIN -> internal FET -> SW -> L -> COUT -> PGND
```

moraju biti vrlo kompaktni.

Preporučeni placement:

```text
CIN
 |
U8 -- L2 -- COUT
 |          |
GND plane --+
```

VOS sense voditi od output nodea, ne iz SW hot zone.

---

# 25. Zaključak

Rev A 3V3 system rail:

```text
U8      = TPS62132RGTR
VIN     = 5V_SYS
VOUT    = 3.3 V
IOUT    = up to 3 A
L       = 2.2 µH initial
CIN     = 10 µF + 100 nF
COUT    = 22 µF + optional second 22 µF
C_SS    = 3.3 nF
FSW     = LOW (~2.5 MHz)
DEF     = LOW (nominal 3.3 V)
FB      = AGND
PG pull = 100 kΩ
```

Ovim su prva dva power bloka dovoljno definirana da možemo prijeći na:

**03_P4_CORE — ESP32-P4 v3.x power domains, decoupling i TLV62569 VDD_HP regulator.**
