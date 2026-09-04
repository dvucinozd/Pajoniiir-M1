# Pajoniiir Mainboard — ESP32-P4 Core Design v0.1

**Projekt:** Pajoniiir BL-A1800 / Pajoniiir-M1  
**Ploča:** Pajoniiir Mainboard Rev A  
**Blok:** 03_P4_CORE  
**Datum:** 2026-09-02  
**Status:** Captured in KiCad and structurally validated; silicon-lot and EVT checks remain

---

# 1. Kritična odluka: samo P4 v3.x+

Za novi Pajoniiir PCB **ne smije se kopirati ESP32-P4 rev1.3 power/pinout blok s Guition JC4880 ploče**.

Aktualne Espressif hardware guidelines izričito navode:

- za nove dizajne koristiti v3.0 i noviju referentnu shemu
- v1.0/v1.3 nisu preporučeni za nove dizajne
- package pin 54 se promijenio:
  - v1.0/v1.3: NC
  - v3.x+: **VDD_HP_1**
- v3.x DCDC mreža zahtijeva dodatne:
  - 2 × 499 kΩ
  - 1 × 22 pF

Ovo je jedan od najvažnijih razloga zašto Pajoniiir-M1 mora imati vlastitu novu shemu.

---

# 2. Važna napomena: package pin 54 ≠ GPIO54

U trenutnom firmwareu imamo:

```text
GPIO54 -> C6 RESET
```

To **nije** u konfliktu s v3.x promjenom package pina 54.

Razlika:

- **package pin 54** = fizička nožica kućišta, sada VDD_HP_1
- **GPIO54** = GPIO signal koji se nalazi na drugom fizičkom package pinu

U aktualnom P4 datasheetu GPIO54 je u VDD_IO_6 domeni, dok je fizički pin 54 zaseban VDD_HP_1 power pin.

Dakle C6 RESET mapping na GPIO54 može ostati kandidat, ali ga svejedno treba finalno provjeriti protiv v3.x pin matrixa i firmwarea.

---

# 3. U1

Glavni kandidat:

**ESP32-P4NRW32X**

Razlog:

- nova P4 revizija
- 32 MB in-package PSRAM
- odgovara postojećem Pajoniiir memory profilu
- P4 je jedini glavni aplikacijski procesor

---

# 4. Glavne power domene

Pajoniiir koristi 3.3 V kao glavni system supply.

P4 power architecture:

```text
3V3_SYS
 |
 +---- VDD_LP
 +---- VDD_IO_0
 +---- VDD_IO_4
 +---- VDD_IO_5
 +---- VDD_IO_6
 +---- VDD_ANA
 +---- VDD_BAT
 +---- VDD_LDO
 +---- VDD_DCDCC
 +---- VDD_USBPHY
 |
 +---- internal LDO -> VDDO_FLASH -> VDD_FLASHIO
 |
 +---- internal LDO -> VDDO_PSRAM -> VDD_PSRAM_0/1
 |
 +---- internal LDO CH3 2.5V -> VDD_MIPI_DPHY
 |
 +---- TLV62569 external DCDC -> P4_VDD_HP
                           |
                           +-> VDD_HP_0
                           +-> VDD_HP_1
                           +-> VDD_HP_2
                           +-> VDD_HP_3
```

---

# 5. ESP32-P4 minimum current budget

Espressif aktualno preporučuje računati najmanje oko:

**380 mA**

za osnovni P4 + flash + PSRAM, bez vanjskih periferija.

Dodatno:

- MIPI PHY do 50 mA
- USB PHY do 20 mA
- IO domene i vanjske periferije dodatno

Zato je odabrani 3V3_SYS regulator od 3 A namjerno značajno predimenzioniran u odnosu na sam P4.

---

# 6. 3.3 V IO / low-power power pins

Na `3V3_SYS`:

| P4 power pin | Napon | Lokalni C |
|---|---:|---:|
| VDD_LP | 3.0–3.6 V | 100 nF |
| VDD_IO_0 | 1.65–3.6 V | 100 nF |
| VDD_IO_4 | 1.65–3.6 V | 100 nF |
| VDD_IO_5 | 1.65–3.6 V | 100 nF |
| VDD_IO_6 | 1.65–3.6 V | 100 nF |

Za Pajoniiir ih koristimo na 3.3 V radi jednostavne i kompatibilne IO domene.

Na power entrance za ovu grupu dodati:

**10 µF**

uz lokalni 100 nF po power pinu.

---

# 7. VDD_ANA

`VDD_ANA`:

- 3.0–3.6 V
- spojiti na 3V3_SYS
- lokalno 100 nF

Ako EVT pokaže regulator noise coupling u analogne interne blokove, može se dodati 0 Ω/ferrite option.

Default:

```text
3V3_SYS -> 0R -> VDD_ANA
```

---

# 8. VDD_BAT

VDD_BAT ne smije ostati floating.

Pajoniiir Rev A nema bateriju, pa:

```text
VDD_BAT -> 3V3_SYS
```

Decoupling:

- 100 nF
- 10 µF

Ne implementirati battery backup sklop u Rev A.

---

# 9. VDD_LDO

`VDD_LDO` napaja P4 interne LDO regulatore.

Spojiti na:

`3V3_SYS`

Espressif preporuka:

- 10 µF na power traceu
- 100 nF neposredno uz pin

Ovaj net treba biti širok i kratak.

---

# 10. VDD_DCDCC

`VDD_DCDCC` napaja kontrolu eksternog core DCDC-a.

Spojiti na:

`3V3_SYS`

Espressif preporuka:

- 10 µF
- 100 nF neposredno uz pin

DCDC input mora koristiti isti supply kao VDD_DCDCC.

---

# 11. VDD_HP core rail

P4 v3.x ima četiri HP power pina:

- VDD_HP_0
- **VDD_HP_1**
- VDD_HP_2
- VDD_HP_3

Radni raspon:

**0.99–1.3 V**

tipično oko 1.1 V, ali P4 internim control loopom upravlja vanjskim DCDC-om.

Net:

`P4_VDD_HP`

Decoupling:

- 10 µF na glavnom entranceu
- 100 nF neposredno uz svaki VDD_HP_x pin

---

# 12. U3 — TLV62569 external P4 core DCDC

Kandidat:

**TLV62569DRLR**

Espressif ga navodi kao verificirani DCDC model.

Osnovna topologija:

```text
3V3_SYS
 |
 4.7uF
 |
TLV62569
 | VIN
 |
 | EN <----- P4 EN_DCDC
 |
 SW
 |
 2.2uH
 |
 +------ P4_VDD_HP
 |          |
 |         22uF
 |          |
 |         GND
 |
 FB <----- P4 FB_DCDC + v3.x feedback network
```

---

# 13. P4-controlled DCDC

Ključna arhitekturna činjenica:

- `EN_DCDC` kontrolira P4
- `FB_DCDC` kontrolira P4
- ove signale treba spojiti na TLV62569 EN/FB prema aktualnoj v3.x referentnoj shemi
- regulator treba biti fizički vrlo blizu P4

Ne koristiti klasični standalone fixed-feedback buck dizajn kao da P4 nema vlastiti DCDC control.

---

# 14. V3.x feedback mreža

Za v3.x Espressif navodi da mreža mora sadržavati:

- **499 kΩ**
- **499 kΩ**
- **22 pF**

Za stare v1.0/v1.3 revizije ti elementi nisu bili populirani.

Za Pajoniiir-M1:

**obavezno koristiti v3.x topologiju i populirati ih.**

Točan raspored pin-to-pin prenijeti direktno iz aktualne Espressif v3.x TLV62569 figure tijekom KiCad capturea.

Ne reinterpretirati mrežu iz JC4880 sheme.

---

# 15. TLV62569 pasive — početni BOM

| RefDes | Value | Funkcija |
|---|---:|---|
| C_CORE_IN | 4.7 µF | TLV62569 input |
| L_CORE | 2.2 µH | core buck inductor |
| C_CORE_OUT | 22 µF | P4_VDD_HP output |
| R_CORE_1 | 499 kΩ | v3.x P4 feedback network |
| R_CORE_2 | 499 kΩ | v3.x P4 feedback network |
| C_CORE_FF | 22 pF C0G | v3.x P4 feedback network |
| TP_CORE | test point | P4_VDD_HP measurement |

Exact capacitor voltage/package i inductor current rating provjeriti s TLV62569 datasheetom i P4 load transientom.

---

# 16. VDD_USBPHY

Pajoniiir aktivno koristi USB, pa VDD_USBPHY mora biti napajan.

Napon:

**3.3 V**

Espressif preporučuje lokalno:

- 10 nF
- 100 nF
- 4.7 µF

Predvidjeti:

```text
3V3_SYS -- R_USBPHY_0R --> VDD_USBPHY
```

R = 0 Ω default.

Iako je v3.x leakage problem riješen, 0 Ω footprint ostaje koristan za debug i mjerenje.

---

# 17. VDD_MIPI_DPHY

Pajoniiir koristi MIPI DSI.

VDD_MIPI_DPHY treba:

**2.5 V**

Radni raspon:

2.25–2.75 V.

Preporučeni izvor:

P4 interni adjustable LDO, npr. LDO channel 3 kao na P4 Function-EV konceptu.

Power path:

```text
P4 VDDO_3 / LDO CH3 configured to 2.5V
       |
       +---- VDD_MIPI_DPHY
```

Lokalno uz VDD_MIPI_DPHY:

- 10 nF
- 100 nF
- 1 µF

Firmware prije DSI inicijalizacije mora konfigurirati odgovarajući interni LDO na 2.5 V.

Ovo treba dokumentirati i u firmware board layeru.

---

# 18. VDDO_3 / internal LDO for MIPI

P4 internal peripheral LDO output je software-controlled.

Važno:

- default output može biti 0
- software ga mora konfigurirati
- MIPI DSI ne smije se inicijalizirati prije nego je 2.5 V rail aktivan

Net naming:

```text
P4_LDO_MIPI_2V5
```

Test point:

`TP_MIPI_2V5`

Preporučeno za Rev A.

---

# 19. Flash power

External flash koristi P4:

`VDDO_FLASH`

Default:

**3.3 V**

Pošto koristimo 3.3 V W25Q128JV kandidat, ne planiramo 1.8 V flash.

Power path:

```text
P4 VDDO_FLASH
 |
 +-- 1uF
 |
 +--> FLASH_VCC
 +--> P4 VDD_FLASHIO
```

VDD_FLASHIO lokalno:

- 100 nF
- 1 µF

Flash sam:

- 100 nF uz VCC

---

# 20. PSRAM power

ESP32-P4NRW32X ima in-package PSRAM.

P4 generira:

`VDDO_PSRAM`

tipično oko 1.9 V nakon software konfiguracije.

Spojiti prema:

- VDD_PSRAM_0
- VDD_PSRAM_1

Lokalno na svaki PSRAM IO power pin:

- 100 nF
- 1 µF

Na VDDO_PSRAM:

- 1 µF

Ne dodavati vanjski PSRAM u Rev A.

---

# 21. CHIP_PU

Aktualna Espressif preporuka:

```text
R = 10 kΩ
C = 1 µF
```

CHIP_PU ne smije biti floating.

Minimum timing:

- power rail stabilization prije enablea: ≥50 µs
- reset low time: ≥1000 µs

Rev A koristi:

- 10 kΩ pull-up
- 1 µF prema GND
- RESET switch prema GND
- test point

Ako se pri EVT pokaže spor/kompliciran startup zbog eFuse + 3V3 buck sekvence, ostaviti mogućnost supervisor IC-a u DNP sheetu.

---

# 22. Power-entry capacitors

Espressif preporučuje 10 µF na power entranceima.

Na P4 području grupirati bulk capacitors tako da budu jasni u shemi:

```text
C_P4_3V3_BULK      10uF
C_P4_VDD_LDO_BULK  10uF
C_P4_DCDCC_BULK    10uF
C_P4_HP_BULK       10uF
C_P4_BAT_BULK      10uF
```

Ne mora svaki fizički biti daleko od drugih; placement će se optimizirati prema P4 reference layoutu.

---

# 23. Decoupling table

| Domena | Lokalni decoupling |
|---|---|
| VDD_LP | 100 nF |
| VDD_IO_0 | 100 nF |
| VDD_IO_4 | 100 nF |
| VDD_IO_5 | 100 nF |
| VDD_IO_6 | 100 nF |
| VDD_ANA | 100 nF |
| VDD_BAT | 100 nF + 10 µF |
| VDD_LDO | 100 nF + 10 µF |
| VDD_DCDCC | 100 nF + 10 µF |
| VDD_HP_0 | 100 nF |
| VDD_HP_1 | 100 nF |
| VDD_HP_2 | 100 nF |
| VDD_HP_3 | 100 nF |
| P4_VDD_HP entrance | 10 µF |
| VDD_USBPHY | 10 nF + 100 nF + 4.7 µF |
| VDD_MIPI_DPHY | 10 nF + 100 nF + 1 µF |
| VDD_FLASHIO | 100 nF + 1 µF |
| VDD_PSRAM_0 | 100 nF + 1 µF |
| VDD_PSRAM_1 | 100 nF + 1 µF |
| VDDO_FLASH | 1 µF |
| VDDO_PSRAM | 1 µF |
| P4_LDO_MIPI_2V5 / VDDO_3 | 1 µF |

Finalni broj i package vrijednosti prenijeti iz aktualne v3.x reference sheme pri captureu.

---

# 24. Power routing constraints

Minimum prema aktualnim Espressif layout smjernicama:

- 3.3 V main power: **≥25 mil**
- VDD_LP / VDD_IO_x / VDD_BAT / VDD_ANA: **≥10 mil**
- VDD_HP_0/1/2/3: **≥20 mil**
- VDD_LDO: **≥20 mil**
- VDD_DCDCC: **≥20 mil**

Power koristiti star routing gdje je praktično.

P4 DCDC:

- što bliže P4
- minimalni input/output/feedback loopovi
- regulator i inductor na istoj strani kao P4 ako layout dopušta

---

# 25. Ground

Za P4 koristiti:

**solid ground plane**

Ne rezati GND ispod:

- P4
- flash
- DCDC
- USB HS
- MIPI

Exposed/ground pins spojiti s dovoljnim brojem via u L2 GND.

---

# 26. P4 current/thermal test points

Obavezno:

```text
TP_3V3_P4
TP_P4_VDD_HP
TP_P4_LDO_MIPI_2V5
TP_VDD_USBPHY
TP_VDDO_FLASH
```

Opcionalno:

```text
TP_VDDO_PSRAM
```

P4 core test point mora biti mali i ne smije degradirati high-current/core loop.

---

# 27. Rev A bring-up sequence za P4 core

## Step 1 — bez firmware funkcija

Provjeriti:

- 3V3_SYS
- CHIP_PU
- UART boot
- flash access
- P4_VDD_HP

## Step 2 — PSRAM

Provjeriti:

- VDDO_PSRAM
- 32 MB PSRAM detect
- PSRAM stress

## Step 3 — USB PHY

Provjeriti:

- VDD_USBPHY
- USB0/USB1 initialization

## Step 4 — MIPI LDO

Provjeriti:

- 2.5 V LDO output
- DSI init

---

# 28. Critical schematic review rules

Prije ERC sign-offa:

- [ ] U1 je v3.x-compatible symbol/footprint
- [ ] physical pin 54 = VDD_HP_1, nije NC
- [ ] svih 4 VDD_HP pinova spojeno
- [ ] v3.x 499k/499k/22pF DCDC mreža populirana
- [ ] EN_DCDC pravilno spojen
- [ ] FB_DCDC pravilno spojen
- [ ] VDD_BAT nije floating
- [ ] VDD_USBPHY decoupling kompletan
- [ ] MIPI 2.5 V source definiran
- [ ] VDDO_FLASH koristi 3.3 V flash
- [ ] VDDO_PSRAM konfiguracija dokumentirana
- [ ] CHIP_PU 10k/1uF
- [ ] svaki power pin ima lokalni decoupling
- [ ] test pointovi postoje

---

# 29. Firmware implications

Postojeći firmware branch je još konfiguriran za stariju P4 reviziju.

Za novi Rev A PCB trebat će:

- ukloniti/izmijeniti rev1.3-specific sdkconfig opcije
- targetirati v3.x silicon
- provjeriti eFuse/chip revision guards
- konfigurirati P4 internal LDO za MIPI 2.5 V
- potvrditi PSRAM init za novi P4 part
- potvrditi GPIO mapping

Ovo treba riješiti prije prvog Rev A flashanja.

---

# 30. Preliminary P4 core BOM additions

| RefDes | Qty | Value/part |
|---|---:|---|
| U1 | 1 | ESP32-P4NRW32X |
| U3 | 1 | TLV62569DRLR |
| L_CORE | 1 | 2.2 µH |
| C_CORE_IN | 1 | 4.7 µF |
| C_CORE_OUT | 1 | 22 µF |
| R_CORE_1 | 1 | 499 kΩ 1% |
| R_CORE_2 | 1 | 499 kΩ 1% |
| C_CORE_FF | 1 | 22 pF C0G |
| R_CHIP_PU | 1 | 10 kΩ |
| C_CHIP_PU | 1 | 1 µF |
| C_USBPHY_1 | 1 | 10 nF |
| C_USBPHY_2 | 1 | 100 nF |
| C_USBPHY_3 | 1 | 4.7 µF |
| R_USBPHY | 1 | 0 Ω |
| C_MIPI_1 | 1 | 10 nF |
| C_MIPI_2 | 1 | 100 nF |
| C_MIPI_3 | 1 | 1 µF |
| C_FLASHIO_1 | 1 | 100 nF |
| C_FLASHIO_2 | 1 | 1 µF |
| C_PSRAM0_1 | 1 | 100 nF |
| C_PSRAM0_2 | 1 | 1 µF |
| C_PSRAM1_1 | 1 | 100 nF |
| C_PSRAM1_2 | 1 | 1 µF |
| C_VDDO_FLASH | 1 | 1 µF |
| C_VDDO_PSRAM | 1 | 1 µF |
| C_MIPI_LDO_OUT | 1 | 1 µF |
| C_P4_BULK | multiple | 10 µF by domain/entrance |
| C_P4_DECOUPLING | multiple | 100 nF per power pin |

---

# 31. Zaključak

P4 core za Pajoniiir-M1 Rev A treba biti projektiran oko četiri ključne činjenice:

1. **Koristimo v3.x P4, ne JC4880 v1.3 reference.**
2. **Fizički package pin 54 sada je VDD_HP_1 i mora biti napajan.**
3. **TLV62569 v3.x feedback mreža 499k/499k/22pF mora biti populirana.**
4. **MIPI PHY dobiva software-configured 2.5 V iz P4 internog LDO-a.**

Time dobijamo čistu osnovu za sljedeći sheet:

**04_P4_FLASH_CLOCK_RESET — W25Q128JV, 40 MHz crystal, strapping, boot i UART minimum-boot platforma.**
