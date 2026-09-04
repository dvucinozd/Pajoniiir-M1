# Pajoniiir Mainboard — Power Input Design v0.1

**Projekt:** Pajoniiir BL-A1800 / Pajoniiir-M1  
**Ploča:** Pajoniiir Mainboard Rev A  
**Blok:** 01_POWER_INPUT  
**Datum:** 2026-09-02  
**Status:** Captured in KiCad; J1 land pattern and C3/C8 EVT selections remain open

> **Post-capture update (2026-09-04):** U7 and D1 are captured with locked footprints. J1 is selected as Switchcraft 722RAHLP with S760KHZ mating plug, but its land pattern remains intentionally blank pending unambiguous terminal-center evidence. C3/C8 remain EVT-selected production packages.

---

# 1. Cilj

Ovaj dokument zaključava prvi stvarni električni blok buduće Pajoniiir-M1 ploče: ulazno napajanje i generiranje `5V_SYS`.

Glavni ciljevi:

- zaštititi uređaj od pogrešnog polariteta i reverzne struje
- spriječiti nekontrolirani inrush
- imati čist power-up
- zaštititi od sustained overcurrenta i short-circuita
- zadržati kratke transient peakove bez nepotrebnog resetiranja
- izbjegavati brownout ponašanje koje se pojavilo na JC4880 prototipu
- omogućiti mjerenje i dijagnostiku

Glavni kandidat:

**TPS259474ARPWR**

To je TPS25947 circuit-breaker varijanta s auto-retry ponašanjem, integriranim reverse-current blockingom i input reverse-polarity zaštitom.

---

# 2. Zašto TPS259474A

Za Pajoniiir input power path želimo circuit-breaker ponašanje, a ne dugotrajno aktivno current-limit držanje raila u nedefiniranom brownout području.

TPS259474A daje:

- 2.7–23 V input range
- 28.3 mΩ tipični RON
- true reverse-current blocking
- reverse-polarity protection
- adjustable UVLO
- adjustable OVLO
- adjustable output slew rate
- circuit-breaker overcurrent response
- transient blanking preko ITIMER
- fast-trip short-circuit protection
- auto-retry nakon faulta
- Power Good output

Važno:

**TPS259474A nema zaseban FLT pin.**  
TPS259474x koristi `PG` i `PGTH`.

Zato Pajoniiir signalni model treba biti:

```text
EFUSE_PG
```

a ne:

```text
EFUSE_FLT_N
```

---

# 3. Predloženi power chain

```text
EXTERNAL 5V SOURCE
      |
      v
 J_PWR_IN
      |
      +---- TVS
      |
      +---- C_IN_HF
      |
      +---- C_IN_BULK
      |
      v
 TPS259474A
      |
      v
    5V_SYS
      |
      +---- 3V3 system buck
      +---- 2× TPS25221 independent USB VBUS switches
      +---- LCD backlight boost
      +---- optional telemetry
```

---

# 4. Ulazni adapter

## 4.1 Nominalni napon

**5.0 V regulated**

## 4.2 Preporučeni adapter

Za EVT/DVT:

**5 V / 4 A minimum quality adapter**

Poželjno imati i 5 V / 5 A bench/source varijantu za karakterizaciju margine.

Cilj nije da finalni uređaj stalno povlači 4 A, nego da postoji dovoljno margine za:

- FLX4 startup
- USB stick inrush
- Wi-Fi burst
- full LCD backlight
- SD peak
- dual-deck DSP/audio
- regulator conversion losses

---

# 5. J_PWR_IN

Exact MPN ostaje `TBD-MECH`.

Za Rev A preferirati locking connector.

Ne preporučuje se:

- micro-USB
- labavi barrel connector bez retentiona
- slučajna USB-C implementacija bez definirane power-role arhitekture

Konektor mora biti nominalno ocijenjen na najmanje:

**5 A**

uz odgovarajuću temperaturu i PCB contact resistance marginu.

---

# 6. Input TVS

RefDes:

`D_TVS_IN`

M1-MECH-A12 zaključava Rev-A input TVS:

```text
Manufacturer   STMicroelectronics
MPN            SMBJ6.0CA-TR
Polarity       bidirectional
VRWM           6.0 V
VBR min        6.7 V
VC 10/1000     10.3 V
VC 8/20        14.8 V
Package        SMB / DO-214AA
KiCad          Diode_SMD:D_SMB
```

Bidirectional `CA` varijanta je namjerna: ne uvodi forward-diode put koji bi poništio TPS259474 reverse-polarity arhitekturu. 6 V standoff ostaje iznad normalnog 5.25 V maksimuma, a specificirani clamp ostaje ispod absolute input maksimuma eFusea. SMB kućište je maksimalno približno 2.45 mm visoko i prolazi M1 centralni 6.5 mm gross height screen.

---

# 7. Input capacitors

Početni EVT prijedlog:

| RefDes | Value | Tip |
|---|---:|---|
| C_IN_HF | 100 nF | X7R ceramic |
| C_IN_MID | 10 µF | X7R/X5R ceramic |
| C_IN_BULK | 330 µF | low-ESR electrolytic/polymer candidate |

Predvidjeti footprint tako da se `C_IN_BULK` može mijenjati:

- 220 µF
- 330 µF
- 470 µF

bez PCB respina.

Cilj Rev A nije “pogoditi” minimalni kondenzator nego omogućiti mjerenje startup/hotplug transienta.

---

# 8. U7 — TPS259474ARPWR pin strategy

Funkcionalni pinovi:

```text
IN        -> VIN_5V
OUT       -> 5V_SYS
EN/UVLO   -> UVLO divider
OVLO      -> OVLO divider
PG        -> EFUSE_PG
PGTH      -> PG threshold network
ILM       -> R_ILM to GND
ITIMER    -> C_ITIMER to GND
DVDT      -> C_DVDT to GND
GND       -> GND
```

---

# 9. UVLO

Cilj je da sustav ne pokušava raditi na ozbiljno srušenom 5 V inputu.

Početni target:

**VIN_UVLO ≈ 4.4 V rising**

Koristimo TPS25947 tipični EN/UVLO rising threshold od oko 1.20 V.

Početni divider:

```text
VIN_5V
 |
 R_UV_TOP = 402 kΩ
 |
 +---- EN/UVLO
 |
 R_UV_BOT = 150 kΩ
 |
GND
```

Proračun:

```text
VIN_UV ≈ 1.20 V × (402k + 150k) / 150k
       ≈ 4.416 V
```

Zašto oko 4.4 V:

- dovoljno nisko da ne nuisance-tripa kvalitetan 5 V adapter
- dovoljno visoko da prekine rad ako supply ozbiljno kolabira
- daje jasan event umjesto dugog P4 brownout područja

Finalni prag treba validirati osciloskopom na Rev A.

---

# 10. OVLO

Početni target:

**VIN_OVLO ≈ 5.7 V rising**

Početni divider:

```text
VIN_5V
 |
 R_OV_TOP = 562 kΩ
 |
 +---- OVLO
 |
 R_OV_BOT = 150 kΩ
 |
GND
```

Proračun:

```text
VIN_OV ≈ 1.20 V × (562k + 150k) / 150k
       ≈ 5.696 V
```

Ovo ostavlja razumnu marginu iznad normalnog 5 V adaptera, ali prekida rail prije ozbiljnog overvoltagea na 5 V sustavu.

---

# 11. Main current threshold

TPS259474x koristi:

```text
R_ILM(Ω) = 3334 / I_LIM(A)
```

Za Rev A predlažemo:

```text
R_ILM = 750 Ω, 1%
```

što daje tipični nominalni threshold:

```text
I_LIM ≈ 3334 / 750
      ≈ 4.45 A
```

TI navodi približan raspon za 750 Ω:

- oko 3.96 A minimum
- oko 4.45 A typical
- oko 4.84 A maximum

Prednost 750 Ω:

- omogućuje ~4 A sustav s određenom marginom
- zadržava UL2367 uvjet koji TI navodi za `RILM ≥ 750 Ω`
- transient load iznad ILIM može proći kroz ITIMER prozor prije breaker akcije

Ovo je vrlo dobar EVT start point.

---

# 12. ITIMER

Cilj ITIMER-a nije pustiti trajni overload, nego tolerirati kratke startup peakove.

Početni kandidat:

```text
C_ITIMER = 4.7 nF
```

TPS259474x koristi oko 1.8 µA discharge current, a tipični ΔVITIMER je oko 1.51 V.

Approx:

```text
t_ITIMER ≈ 1.51 × 4.7 / 1.8
          ≈ 3.94 ms
```

Dakle load iznad ILIM, ali ispod fast-trip granice, može trajati oko 4 ms prije circuit-breaker tripa.

Za Rev A predvidjeti alternativne vrijednosti:

- 2.2 nF ≈ 1.85 ms
- 4.7 nF ≈ 3.94 ms
- 10 nF ≈ 8.39 ms

Default:

**4.7 nF**

---

# 13. Fast-trip ponašanje

TPS259474x ima fast-trip zaštitu oko višeg praga, približno vezanu uz višekratnik ILIM.

To znači:

- normalan kratki transient može proći ITIMER prozor
- ozbiljan short ne čeka puni ITIMER interval

Ovo je posebno korisno jer `5V_SYS` napaja i USB power-switch blok.

---

# 14. dVdt / soft-start

Početni kandidat:

```text
C_DVDT = 4.7 nF
```

TI jednadžba:

```text
C_DVDT(pF) = 2000 / SR(V/ms)
```

Za 4.7 nF = 4700 pF:

```text
SR ≈ 2000 / 4700
   ≈ 0.426 V/ms
```

Za 5 V rail:

```text
t_rise ≈ 5 / 0.426
       ≈ 11.75 ms
```

To je dovoljno sporo za kontrolirani startup, ali ne ekstremno sporo.

Ako Rev A mjerenje pokaže prevelik input inrush:

- povećati C_DVDT

Ako pokaže nepotrebno spor boot:

- smanjiti C_DVDT

TI preporučuje dodatni 100 Ω series resistor ako se koristi `C_DVDT > 10 nF`.

---

# 15. Power Good

TPS259474A koristi:

`PG`

Net:

```text
EFUSE_PG
```

Preporuka:

- pull-up na `3V3_SYS`
- dovesti na P4 GPIO ako GPIO budget dopušta
- svakako test point

Time firmware može znati:

- je li 5V_SYS stvarno uspostavljen
- je li input power block u validnom stanju

---

# 16. PGTH

`PGTH` omogućuje definiranje Power Good thresholda.

Početni cilj:

PG se smije smatrati validnim kada je `5V_SYS` dovoljno blizu nominalnom railu.

Rev A mreža je zaključana na:

```text
5V_PROTECTED
 |
 R_PGTH_TOP = 100 kΩ, 1%
 |
 +---- PGTH
 |
 R_PGTH_BOT = 36.5 kΩ, 1%
 |
GND
```

Prema TPS25947 Rev C jednadžbi `VPG = VPGTH(R) × (Rtop + Rbot) / Rbot`, uz tipičnih 1.20 V na PGTH:

```text
VPG(rising, typ) ≈ 4.488 V
VPG(rising, threshold tolerance) ≈ 4.424 ... 4.574 V
VPG(falling, typ) ≈ 4.076 V
```

Divider na 5 V vuče približno 36.6 µA, što daje veliku marginu prema maksimalnom PGTH leakageu. Power Good ovdje služi dijagnostici validnosti zaštićenog 5 V raila, a ne kao hard boot-sequencing uvjet.

---

# 17. Current telemetry

TPS25947 `ILM` pin služi i kao current monitor funkcija u određenoj konfiguraciji obitelji.

Međutim, isti pin definira current threshold preko `R_ILM`.

Za Rev A preporuka je:

1. koristiti `R_ILM = 750 Ω`
2. ostaviti pristupačan test point na ILM netu
3. ne opterećivati ga ADC-om dok ne provjerimo utjecaj na current-limit accuracy

Za kontinuiranu firmware telemetriju bolji je zaseban:

- INA226
- INA238
- ili sličan current monitor

na 5V_SYS.

---

# 18. Auto-retry

TPS259474A je auto-retry varijanta.

To znači da nakon faulta može automatski pokušati ponovno pokretanje.

To je namjerno odabrano za Rev A jer:

- uređaj se može sam oporaviti od prolaznog input faulta
- ne zahtijeva fizičko isključivanje nakon svakog transient incidenta

Ali tijekom EVT testiranja treba posebno provjeriti da hard fault ne uzrokuje neželjeni termalni restart-loop.

Ako se pokaže da želimo hard latch-off ponašanje, footprint-kompatibilna TPS259474L varijanta postaje kandidat za Rev B.

---

# 19. 5V_SYS bulk

Nakon eFusea predvidjeti lokalni reservoir.

Initial:

```text
C_5V_SYS_BULK = 330 µF
C_5V_SYS_MID  = 22 µF
C_5V_SYS_HF   = 100 nF
```

Cilj:

- stabilizirati USB hotplug load
- smanjiti transient koji vidi 3.3 V buck
- smanjiti backlight/USB međusobni coupling

Ali ne koristiti golemi output capacitor bez dVdt proračuna, jer i njega eFuse mora napuniti pri startupu.

---

# 20. Star topology nakon 5V_SYS

Fizički power split:

```text
TPS259474A OUT
      |
      +========== 5V_SYS backbone =========+
      |                 |                  |
      |                 |                  |
      v                 v                  v
  TPS62133          TPS25221 x2            MP3202
   3V3              USB VBUS           LCD BL
```

Ne koristiti jednu dugu tanku 5V stazu koja prvo ide kroz USB blok pa tek onda prema P4 regulatoru.

---

# 21. Ground return

Power-input ground treba imati nizak impedance path u ground plane.

Posebno:

- eFuse GND
- bulk capacitor return
- TPS25221 x2 return
- system buck return

trebaju biti projektirani tako da USB current transient ne inducira ground bounce u audio području.

---

# 22. Test points

Obavezno:

```text
TP_VIN_5V
TP_5V_SYS
TP_EFUSE_PG
TP_EFUSE_ILM
TP_EFUSE_EN_UVLO
TP_EFUSE_OVLO
TP_GND_POWER
```

Opcionalno:

```text
TP_EFUSE_DVDT
TP_EFUSE_ITIMER
```

---

# 23. Measurement plan

## 23.1 Cold power-up

Oscilloscope:

CH1 = VIN_5V  
CH2 = 5V_SYS  
CH3 = 3V3_SYS  
CH4 = P4_VDD_HP

Provjeriti:

- monotonic rise
- nema oscillationa
- nema repeated eFuse retrya
- nema P4 brownout pulsea

## 23.2 USB0 insert

Mjeriti:

- 5V_SYS
- USB0_VBUS
- 3V3_SYS

## 23.3 FLX4 connect

Mjeriti:

- 5V_SYS
- USB1_VBUS
- 3V3_SYS
- EFUSE_PG

## 23.4 Worst-case combined

Istovremeno:

- full backlight
- Wi-Fi TX
- USB storage access
- FLX4 UAC
- dual deck playback

---

# 24. Acceptance criteria

Rev A power-input blok prolazi ako:

- 5V_SYS nema reset-inducing dip
- eFuse se ne retriggera pri normalnom bootu
- normalni USB hotplug ne tripa main eFuse
- sustained overload uredno prekida rail
- short ne oštećuje board
- reverse polarity ne napaja board
- nema backfeed iz 5V_SYS prema inputu
- PG signal korektno prati rail validity
- eFuse temperature ostaje unutar razumne margine

---

# 25. KiCad net list za 01_POWER_INPUT

Hijerarhijski outputi:

```text
5V_SYS
EFUSE_PG
```

Hijerarhijski input/control:

```text
EFUSE_FORCE_OFF      optional future control
```

Lokalni netovi:

```text
VIN_5V
EFUSE_EN_UVLO
EFUSE_OVLO
EFUSE_ILM
EFUSE_ITIMER
EFUSE_DVDT
EFUSE_PGTH
```

---

# 26. Preliminary RefDes table

| RefDes | Part/value | Status |
|---|---|---|
| J1 | 5V locking power connector | TBD-MECH |
| D1 | SMBJ6.0CA-TR | ST, bidirectional 6 V TVS, SMB / `Diode_SMD:D_SMB` |
| U1 | TPS259474ARPWR | LOCK-CANDIDATE |
| R1 | 402 kΩ 1% | UVLO top |
| R2 | 150 kΩ 1% | UVLO bottom |
| R3 | 562 kΩ 1% | OVLO top |
| R4 | 150 kΩ 1% | OVLO bottom |
| R5 | 750 Ω 1% | ILIM |
| C1 | 100 nF | input HF |
| C2 | 10 µF | input ceramic |
| C3 | 330 µF | input bulk |
| C4 | 4.7 nF | ITIMER |
| C5 | 4.7 nF | dVdt |
| C6 | 100 nF | 5V_SYS HF |
| C7 | 22 µF | 5V_SYS mid |
| C8 | 330 µF | 5V_SYS bulk |
| R_PG | 10 kΩ | PG pull-up initial |
| R_PGTH_TOP / R_PGTH_BOT | 100 kΩ / 36.5 kΩ, 1% | LOCKED Rev A; VPG rising ≈ 4.49 V typ |

---

# 27. Open items

Prije finalnog schematic locka:

- [ ] exact input connector
- [x] exact TVS — ST SMBJ6.0CA-TR / SMB, M1-MECH-A12
- [x] PGTH values — 100 kΩ / 36.5 kΩ, VPG rising ≈ 4.49 V typ
- [ ] confirm PG pull-up voltage/rating
- [ ] confirm 5V_SYS output bulk vs dVdt/inrush
- [ ] confirm 750 Ω ILIM under measured maximum load
- [ ] confirm 4.7 nF ITIMER with FLX4 + USB0 startup
- [ ] confirm 4.7 nF dVdt startup behavior
- [ ] thermal measurement TPS259474A at worst-case continuous current
- [ ] reverse polarity bench test
- [ ] hard-short bench test with current-limited source

---

# 28. Zaključak

Za Pajoniiir-M1 Rev A glavni power-input kandidat je:

```text
TPS259474ARPWR
RILIM = 750 Ω
ITIMER = 4.7 nF initial
DVDT = 4.7 nF initial
UVLO ≈ 4.42 V
OVLO ≈ 5.70 V
```

Ovo nije slučajan generic eFuse blok. Vrijednosti su ciljano odabrane za Pajoniiir:

- 5 V sustav
- približno 4 A power envelope
- dual USB host
- osjetljiv P4 na brownout
- potrebu toleriranja kratkih load transienta
- potrebu clean-cut zaštite kod stvarnog sustained faulta

**Sljedeći električni blok:** `02_POWER_3V3` — TPS62133 3.3 V rail i kompletan 3V3 power budget.
