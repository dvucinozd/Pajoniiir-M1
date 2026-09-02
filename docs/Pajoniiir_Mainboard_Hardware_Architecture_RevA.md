# Pajoniiir Mainboard — Hardverska arhitektura i početni PCB BOM

**Projekt:** Pajoniiir BL-A1800  
**Repozitorij:** `dvucinozd/Pajoniiir`  
**Branch:** `feat/p4-dual-usb-host`  
**Analizirani commit:** `af597d8`  
**Namjena dokumenta:** početni hardverski baseline za izradu vlastite Pajoniiir PCB ploče  
**Datum:** 2026-09-02

---

## 1. Cilj dokumenta

Cilj ovog dokumenta je pretvoriti postojeći Pajoniiir prototip, koji trenutno koristi razvojnu ploču **Guition JC4880P443C_I_W** i vanjski **PCM5102A** modul, u jasnu i proizvodno upotrebljivu hardversku arhitekturu za vlastitu tiskanu ploču.

Dokument nije samo popis modula koji su danas fizički spojeni, nego popis funkcionalnih i električnih blokova koji moraju postojati na budućoj Pajoniiir Mainboard ploči.

Posebno su obrađeni:

- ESP32-P4 glavni procesor
- memorija i flash
- ESP32-C6 Wi-Fi koprocesor
- 4.3" MIPI DSI zaslon
- GT911 touch
- microSD
- PCM5102A MAIN audio izlaz
- dual USB host
- zaštita i napajanje USB VBUS-a
- glavno napajanje
- zaštite
- debug/programiranje
- testne točke
- komponente koje više nisu potrebne
- prijedlog Rev A arhitekture
- prijedlog početnog Engineering BOM-a

---

# 2. Sažetak trenutne Pajoniiir arhitekture

Na branchu `feat/p4-dual-usb-host` Pajoniiir je sada **P4-only** uređaj.

Stari ESP32-S3 više nije dio aktivne proizvodne arhitekture.

Glavni ESP32-P4 direktno obavlja:

- USB0 mass-storage host za Rekordbox USB medij
- USB1 host za DDJ-FLX4
- USB MIDI IN
- USB MIDI OUT / LED feedback
- USB Audio Class prema FLX4
- dva decka
- audio decode
- audio DSP
- mixing
- MAIN izlaz preko PCM5102A
- CUE/PFL prema FLX4 headphone izlazu
- Rekordbox library
- microSD
- LVGL korisničko sučelje
- touch
- Wi-Fi/web UI preko ESP32-C6
- OTA firmware update
- controller profile sustav

Aktivna arhitektura može se svesti na:

```text
                         ┌──────────────────────┐
                         │      ESP32-P4        │
                         │                      │
Rekordbox USB ─ USB0 ──► │ HS USB HOST          │
                         │                      │
DDJ-FLX4 ───── USB1 ───► │ USB HOST             │
 MIDI + UAC 4ch          │                      │
                         │                      │
                         │ I2S                  │
                         └──────┬───────────────┘
                                │
                          BCLK / LRCK / DATA
                                │
                         ┌──────▼───────┐
                         │   PCM5102A   │
                         │   MAIN DAC   │
                         └─────┬────┬───┘
                               │    │
                              RCA  RCA
                               L    R


ESP32-P4 ── MIPI DSI ──► ST7701S 4.3" LCD
ESP32-P4 ── I²C ───────► GT911 Touch
ESP32-P4 ── SDMMC ─────► microSD
ESP32-P4 ── SDIO ──────► ESP32-C6 ── Wi-Fi

CUE/PFL ────────────────► USB UAC CH3/CH4
                           │
                           ▼
                    DDJ-FLX4 headphone jack
```

---

# 3. Osnovna projektna filozofija nove PCB ploče

Nova ploča ne bi trebala biti kopija Guition JC4880P443C_I_W.

Guition ploča je univerzalna HMI/multimedijska development ploča i sadrži više sklopova koji Pajoniiiru više nisu potrebni.

Nova PCB treba biti:

- specifična za Pajoniiir
- P4-only
- dual USB host
- s robusnim VBUS napajanjem
- s integriranim PCM5102A
- s integriranim Wi-Fi modulom
- s MIPI DSI display sučeljem
- s GT911 touchom
- s microSD
- s dovoljnom rezervom napajanja
- s dobrim debug i test mogućnostima

Preporučeni naziv:

**Pajoniiir Mainboard Rev A**

---

# 4. Glavni procesor

## 4.1 ESP32-P4

Za novi dizajn ne preporučuje se kopiranje stare ESP32-P4 revizije koja se nalazi na Guition ploči.

Za novu ploču preporučeni kandidat je novija ESP32-P4 revizija s integriranim 32 MB PSRAM-a.

### Preporučena varijanta

**ESP32-P4NRW32X**

Cilj je zadržati:

- 32 MB PSRAM
- dovoljno memorije za LVGL
- waveform cache
- compressed audio cache
- dva decka
- USB stack
- audio DSP
- Rekordbox parser
- OTA
- web UI

### Razlog

Tvoj firmware već aktivno koristi 32 MB PSRAM-a.

U `sdkconfig.defaults` postoje:

```text
CONFIG_SPIRAM=y
CONFIG_SPIRAM_USE_MALLOC=y
CONFIG_SPIRAM_MODE_HEX=y
CONFIG_SPIRAM_SPEED_200M=y
CONFIG_SPIRAM_FETCH_INSTRUCTIONS=y
CONFIG_SPIRAM_RODATA=y
CONFIG_SPIRAM_XIP_FROM_PSRAM=y
CONFIG_SPIRAM_FLASH_LOAD_TO_PSRAM=y
```

Dakle 32 MB PSRAM nije luksuz nego dio trenutne arhitekture.

---

# 5. Firmware flash

Pajoniiir trenutno koristi 16 MB firmware flash.

To treba zadržati zbog:

- ESP-IDF
- LVGL
- USB stacka
- audio codeca
- DSP-a
- controller profila
- OTA A/B particija
- rollback mehanizma
- coredump particije

### Preporuka

**16 MB / 128 Mbit QSPI NOR Flash**

Primjeri klase:

- Winbond W25Q128
- GD25Q128
- ISSI IS25LP128
- ekvivalent koji je podržan i provjeren za ESP32-P4

### Obavezni pomoćni elementi

- 100 nF decoupling uz flash
- pull-up na CS prema Espressif preporuci
- 0 Ω tuning footprintovi na SPI signalima
- kvalitetan GND reference plane
- vrlo kratke veze prema P4

---

# 6. P4 clock

ESP32-P4 zahtijeva vanjski glavni clock.

### Y1

**40 MHz crystal**

Preporučene karakteristike:

- 40 MHz
- ±10 ppm ili bolje
- odgovarajući ESR
- odgovarajući CL
- mala kućišna izvedba, npr. 3225 ili 2520

Load kondenzatori moraju biti izračunati prema konkretnom kristalu.

Za Rev A korisno je predvidjeti footprintove tako da se vrijednosti mogu tuningom promijeniti bez izmjene PCB-a.

---

# 7. Reset / Boot / Strapping

Nova ploča treba imati barem:

### SW1 — RESET

Povezan na `CHIP_PU`.

Preporučeni reset network:

- 10 kΩ pull-up
- 1 µF prema GND
- tipka prema GND

### SW2 — BOOT

Za ručni ulazak u download/programming mode.

### Dodatno

Preporučuje se dovesti:

- CHIP_PU
- BOOT
- UART TX
- UART RX
- GND
- 3V3

na debug header ili pogo-pin test pads.

---

# 8. ESP32-P4 core napajanje

ESP32-P4 zahtijeva dobro projektirano napajanje.

Posebnu pažnju treba posvetiti VDD_HP/core DCDC dijelu.

### Kandidat

**TLV62569**

ili drugi Espressif odobren regulator za konkretnu P4 reviziju.

Uz njega trebaju:

- odgovarajući induktor
- input kondenzatori
- output kondenzatori
- feedback otpornici
- vrlo kratka high-current switching petlja
- dobar GND plane

### Važno

Za novu reviziju ESP32-P4 mora se koristiti aktualni Espressif reference design.

Ne treba 1:1 kopirati power dio sa stare Guition P4 revizije.

---

# 9. ESP32-C6 Wi-Fi koprocesor

ESP32-P4 nema integrirani Wi-Fi.

Tvoj firmware koristi ESP-Hosted preko SDIO prema C6.

Trenutni firmware koristi približno:

```text
P4 GPIO18  -> SDIO CLK
P4 GPIO19  -> SDIO CMD
P4 GPIO14  -> SDIO D0
P4 GPIO15  -> SDIO D1
P4 GPIO16  -> SDIO D2
P4 GPIO17  -> SDIO D3
P4 GPIO54  -> C6 RESET
```

## Preporuka

Umjesto bare ESP32-C6 RF implementacije:

**ESP32-C6-WROOM-1**

### Prednosti

Modul već integrira:

- ESP32-C6
- flash
- RF matching
- 40 MHz clock
- PCB antenu ili U.FL varijantu
- RF layout koji je već kvalificiran

Time se znatno smanjuje RF rizik nove PCB ploče.

### Obavezni PCB zahtjevi

- antenna keep-out
- bez bakra ispod PCB antene
- bez visokih metalnih dijelova uz antenu
- odgovarajući 3.3 V decoupling
- SDIO routing
- RESET
- eventualni UART za C6 debug

---

# 10. Display

Aktualna hardverski potvrđena konfiguracija je:

- 4.3"
- IPS TFT
- 480 × 800
- ST7701S
- MIPI DSI
- 2 data lane
- landscape UI kroz rotaciju

Tvoj UI je praktički projektiran za 800 × 480 landscape način rada.

## Preporuka

Zadržati isti ili potpuno kompatibilan LCD panel.

### Potrebna DSI sučelja

- DSI CLK+
- DSI CLK-
- DSI DATA0+
- DSI DATA0-
- DSI DATA1+
- DSI DATA1-

### Kontrolni signali

- LCD RESET
- backlight enable/PWM
- power rails

### Firmware pinovi

- GPIO5 — LCD reset
- GPIO23 — LCD backlight PWM

### Preporučene dodatne PCB komponente

- DSI_REXT ≈ 4.02 kΩ
- 0 Ω series/tuning footprints
- lokalni DSI PHY decoupling
- FPC connector
- kvalitetan ground reference
- vrlo kratke MIPI parice

---

# 11. LCD backlight driver

Guition ploča sadrži sklop za LCD backlight.

Na vlastitoj PCB ploči moramo ga ponovno implementirati.

### Kandidat

**MP3202** ili drugi LED boost driver koji odgovara točno odabranom panelu.

Sklop treba uključivati:

- boost IC
- inductor
- Schottky diode ako topologija zahtijeva
- current setting resistor
- input/output kondenzatore
- PWM/EN iz P4
- dovoljno visok voltage rating za LED string

Vrijednosti se ne smiju zaključati prije nego odaberemo konačni LCD panel i njegov backlight string.

---

# 12. Touch

Trenutni touch controller:

**GT911**

Trenutna komunikacija:

- I2C SDA — GPIO7
- I2C SCL — GPIO8
- adresa 0x5D

Za novu PCB preporučujem spojiti i dodatne signale:

- GT911 INT
- GT911 RESET

čak i ako ih sada firmware ne koristi.

To omogućuje:

- interrupt-driven touch
- hardware reset toucha
- lakši recovery
- manje I2C pollinga

### Potrebno

- SDA pull-up
- SCL pull-up
- ESD zaštita
- FPC konektor
- pravilna touch naponska domena

---

# 13. microSD

microSD treba ostati.

Ne služi kao glavni Rekordbox media uređaj, ali je važan za:

- controller profile
- config
- cache
- moguće logove
- pomoćne podatke
- future features

Trenutni mapping:

| Signal | GPIO |
|---|---:|
| D0 | 39 |
| D1 | 40 |
| D2 | 41 |
| D3 | 42 |
| CLK | 43 |
| CMD | 44 |

Koristi se 4-bit SDMMC.

## Preporučene dodatne komponente

- microSD socket
- ESD array
- pull-up na CMD
- pull-up na D0-D3
- series resistor footprint na CLK
- series resistor footprints i na drugim linijama ako SI test pokaže potrebu
- lokalni 100 nF
- bulk capacitor npr. 10–47 µF blizu socketa

## Preporučeno napajanje

microSD napajati iz glavnog 3.3 V raila.

Opcionalno dodati:

- high-side load switch ili P-MOSFET

kako bi firmware mogao fizički power-cycleati SD karticu.

---

# 14. PCM5102A MAIN audio DAC

PCM5102A je sada dokazani MAIN audio izlaz.

Aktualni pinovi:

| Funkcija | ESP32-P4 |
|---|---:|
| BCLK | GPIO50 |
| LRCK / WS | GPIO52 |
| DATA | GPIO51 |
| MCLK | nije potreban |

PCM5102A podržava 3-wire I2S jer ima interni PLL.

## Preporučeni IC

**PCM5102APWR**

TSSOP-20 kućište.

## Prednosti

- kvalitetan stereo DAC
- line-level output
- nema potrebe za dodatnim MCLK-om
- nema potrebe za zasebnim izlaznim op-ampom u osnovnoj konfiguraciji
- ground-centered output
- prikladan za RCA MAIN OUT

## Tipični pomoćni elementi

Prema TI referentnom dizajnu treba predvidjeti:

- lokalni 100 nF bypass
- bulk decoupling
- charge pump capacitor
- analog supply filtering
- digital supply filtering
- 470 Ω series R na OUTL
- 470 Ω series R na OUTR
- približno 2.2 nF RF filter C na L/R
- XSMT control
- FMT konfiguraciju
- FLT konfiguraciju

## Izlazi

### J4
RCA LEFT

### J5
RCA RIGHT

Opcionalno:

### J6
3.5 mm stereo line out

Ako se koristi i RCA i 3.5 mm paralelno, treba potvrditi ukupno opterećenje i izlaznu topologiju.

---

# 15. CUE / headphones audio

Važno: nova ploča **ne treba drugi DAC za headphones**.

CUE/PFL signal ide:

```text
P4 audio engine
      |
      +-> MAIN -> PCM5102A -> RCA
      |
      +-> CUE/MONITOR
             |
             -> USB Audio Class ch.3/4
                    |
                    -> DDJ-FLX4
                           |
                           -> FLX4 headphone jack
```

To smanjuje:

- broj DAC-ova
- analogne sklopove
- routing
- trošak
- potencijalne ground-loop probleme

---

# 16. Dual USB host

Ovo je najvažniji električni blok cijelog Pajoniiir Mainboarda.

Trenutna konfiguracija:

### USB0

Rekordbox storage.

### USB1

DDJ-FLX4:

- MIDI IN
- MIDI OUT
- LEDs
- UAC audio
- cue/headphones

USB podaci rade, ali na Guition prototipu VBUS napajanje ostaje glavni hardverski rizik.

---

# 17. Zašto USB VBUS mora biti potpuno nov

Na prototipu je potvrđeno da napajanje JC4880 preko JP1 VCC5V:

- napaja sam P4 board
- ali ne jamči ispravan downstream VBUS prema oba USB host porta

Kasniji bench setup uspio je napajati uređaje, ali je došlo do brownouta pod audio opterećenjem.

Zbog toga buduća PCB mora imati namjenski dual-VBUS power distribution.

---

# 18. Preporučena dual USB power arhitektura

```text
                         +---------------- USB0 VBUS
                         |
5V_SYS ── TPS2561 ───────+
                         |
                         +---------------- USB1 VBUS
```

### U6

**TPS2561**

Dual USB current-limited high-side switch.

Za svaki port:

- zaseban switch kanal
- zaseban current limit
- zaseban enable
- zaseban fault
- thermal protection
- short-circuit protection
- soft-start

## Preporučeni target

Približno:

- USB0: 0.8–1.0 A
- USB1: 0.8–1.0 A

Točan ILIM treba definirati prema:

- DDJ-FLX4 stvarnoj potrošnji
- USB stick peak currentu
- TPS2561 datasheetu
- bench mjerenju

---

# 19. USB firmware-controlled power

Vrlo preporučljivo:

### EN1

P4 kontrolira USB0 VBUS.

### EN2

P4 kontrolira USB1 VBUS.

### FAULT1

P4 čita USB0 overcurrent/fault.

### FAULT2

P4 čita USB1 overcurrent/fault.

To omogućuje softwareu:

- isključiti samo USB stick
- power-cycleati USB0
- power-cycleati FLX4
- razlikovati overcurrent od USB enumeration problema
- prikazati fault u Settings UI
- napraviti automatski recovery bez resetiranja uređaja

Primjer budućeg dijagnostičkog ekrana:

```text
USB POWER

USB0 STORAGE   5.02 V   OK
USB1 FLX4      4.98 V   OK

USB0 FAULT     NO
USB1 FAULT     NO
```

---

# 20. USB konektori

Za Rev A preporučujem:

**USB-A host ×2**

umjesto dva USB-C host konektora.

## Razlog

USB-A host je električki i mehanički jednostavniji.

Nema potrebe za:

- CC1/CC2 konfiguracijom
- Type-C role detectionom
- source current advertisement logikom
- USB-C host role greškama

### USB0

USB-A ženski

za USB stick.

### USB1

USB-A ženski

prema DDJ-FLX4 preko:

**USB-A → USB-C data kabela**

Kasnije se može napraviti Type-C revizija ako bude potrebno.

---

# 21. USB signal integrity

Za svaki USB port treba predvidjeti:

- D+
- D-
- GND
- SHIELD
- VBUS iz TPS2561

## FS USB

Za Full-Speed linije predvidjeti series resistor footprintove, tipično:

- 22 Ω
- 33 Ω

konačna vrijednost nakon SI testiranja.

## HS USB

Za High-Speed port:

- pravilna 90 Ω differential impedance
- kratke parice
- isti layer
- minimalan broj via
- kontinuiran GND plane
- low-capacitance ESD

ESD zaštita HS linija mora imati vrlo malu kapacitivnost, tipično <1 pF.

---

# 22. USB ESD zaštita

Za oba porta treba zaseban USB ESD array.

Kandidati klase:

- TPD2EUSB30
- USBLC6-2
- PESD5V
- ekvivalent za USB 2.0

Za HS port treba izabrati dio s dovoljno niskim Cpar.

---

# 23. Glavno napajanje

Predložena osnovna arhitektura:

```text
External regulated 5 V / 4 A
            |
           TVS
            |
        Input eFuse
            |
           5V_SYS
            |
     ┌──────┼───────────────┐
     │      │               │
     │      │               │
 TPS2561   5→3.3V         LCD BL
 USB VBUS   BUCK            BOOST
            |
       ┌────┼──────┬──────────────┐
       │    │      │              │
      P4   C6    FLASH          PCM5102A
       │
  P4 core DCDC
```

---

# 24. Ulazni eFuse

Preporučeni kandidat:

**TPS25947**

ili ekvivalent.

Poželjne funkcije:

- overcurrent protection
- current limit
- short-circuit protection
- overvoltage protection
- reverse polarity/reverse current zaštita
- thermal shutdown
- controlled soft-start
- power-good

To je vrlo korisno jer uređaj ima:

- veliki P4
- MIPI LCD
- Wi-Fi
- audio DAC
- dva USB host uređaja
- SD karticu

---

# 25. Ulazna TVS zaštita

Na 5 V power input preporučujem TVS diodu.

Odabir ovisi o:

- vanjskom adapteru
- konektoru
- maksimalnom dopuštenom standoff naponu
- željenom IEC ESD/surge nivou

Treba dodati i:

- input bulk capacitor
- 100 nF ceramic
- eventualni π filter

---

# 26. 5 V → 3.3 V regulator

Glavni 3.3 V regulator mora biti sinkroni buck.

Ne preporučujem linearni regulator.

Razlog:

- ESP32-P4
- C6
- flash
- microSD
- touch
- digitalni DAC dio
- ostala logika

mogu stvoriti značajnu potrošnju.

### Minimalni target

3.3 V / 2 A

### Preporučeni design target

3.3 V / 3 A

radi rezerve.

Kandidati klase:

- TPS62132
- TPS62132
- MP2145
- SY8089
- drugi kvalitetan synchronous buck

Konačni dio treba odabrati prema:

- cijeni
- dostupnosti
- efikasnosti
- EMI-u
- layout zahtjevima

---

# 27. Power budget

Repo trenutačno predviđa približno:

- do ~1 A USB0
- do ~1 A USB1
- P4 + LCD + Wi-Fi + SD + audio ostatak

Zato:

### Minimum

5 V / 3 A

### Preporučeni design input

**5 V / 4 A**

To daje korisnu rezervu za:

- FLX4 startup
- USB stick peak
- LCD backlight
- Wi-Fi TX burst
- SD current transient
- audio processing

PCB power routing treba projektirati tako da 4 A nije problem.

---

# 28. Napajanje kao topologija zvijezde

Preporučuje se od `5V_SYS` razdvojiti glavne grane:

```text
5V_SYS
 |
 +-- P4/3V3 converter
 |
 +-- USB TPS2561
 |
 +-- LCD backlight
 |
 +-- audio analog filter
```

Treba izbjeći da USB load transient prolazi istom tankom stazom kao P4 napajanje.

To je posebno važno jer je prototip već pokazao brownout ponašanje.

---

# 29. Opcionalni power monitor

Vrlo korisna EVT/DVT komponenta:

**INA226 / INA238 / sličan current monitor**

Mjerio bi:

- 5V_SYS voltage
- total current
- power

Time firmware može logirati:

- USB hotplug peak
- FLX4 startup
- dual-deck load
- Wi-Fi burst
- backlight load

Primjer:

```text
SYSTEM POWER

5V_SYS       4.98 V
CURRENT      1.74 A
POWER        8.67 W

USB0         OK
USB1         OK
```

Ovo nije nužno za finalnu masovnu proizvodnju, ali je vrlo korisno za Rev A.

---

# 30. Debug / programiranje

Ploča mora biti lako servisabilna.

Preporučujem footprint za:

### UART0

- TX
- RX
- GND
- 3V3
- CHIP_PU
- BOOT

Format može biti:

- 1×6 2.54 mm
- 1.27 mm header
- Tag-Connect
- pogo pads

Za proizvodnju je najbolji pogo/Tag-Connect pristup.

---

# 31. Status LED

Preporučujem najmanje jednu P4 status LED.

Moguće namjene:

- boot
- firmware update
- fault
- USB recovery
- diagnostics

Može biti:

- jedna RGB LED
- ili dvije obične LED

Za finalni proizvod LED može biti skrivena unutra ako nije potrebna korisniku.

---

# 32. Reset supervisor

Nije nužno, ali ostaviti footprint nije loša ideja.

Ako se tijekom DVT testiranja pokaže da power-up sequence treba dodatnu kontrolu, može se koristiti supervisor IC.

Primjeri klase:

- TPS3808
- TLV803
- STM809

Za prvu reviziju može biti DNP.

---

# 33. Što NE treba prenijeti s JC4880 ploče

Sljedeće komponente postoje na universal development boardu, ali nisu potrebne u aktivnoj Pajoniiir arhitekturi.

## ESP32-S3

**Izbaciti.**

P4 sada direktno upravlja FLX4.

## ES8311 codec

**Izbaciti.**

MAIN ide preko PCM5102A.

Cue ide preko FLX4 UAC.

## Speaker amplifier

**Izbaciti.**

Nema potrebe za lokalnim speaker outputom.

## Speaker connector

**Izbaciti.**

## Analog microphone circuitry

**Izbaciti.**

## Camera MIPI CSI

**Izbaciti.**

## Camera power/control

**Izbaciti.**

## RS485/MAX485

**Izbaciti.**

## P4-S3 UART control link

**Izbaciti.**

## P4-S3 monitor I2S

**Izbaciti.**

## Battery charger / lithium circuit

Za prvu Pajoniiir PCB reviziju:

**izbaciti**, osim ako se kasnije donese odluka da uređaj mora raditi na bateriju.

## Veliki universal GPIO expansion header

Nije potreban.

Bolje koristiti:

- test pads
- mali debug header
- nekoliko rezervnih GPIO padova

---

# 34. Komponente koje treba zadržati funkcionalno, ali ne nužno identično

S Guition koncepta ostaju potrebni:

- ESP32-P4
- 32 MB PSRAM
- 16 MB flash
- ESP32-C6 Wi-Fi
- LCD
- touch
- microSD
- 5 V napajanje
- 3.3 V napajanje
- USB host
- debug UART

Ali nova PCB treba koristiti komponente i layout prilagođene Pajoniiiru.

---

# 35. Preliminarni glavni Engineering BOM

Ovo nije još finalni manufacturing BOM, nego početni popis glavnih komponenti.

| RefDes | Qty | Funkcija | Preporučeni dio / klasa | Status |
|---|---:|---|---|---|
| U1 | 1 | Main SoC | ESP32-P4NRW32X | obavezno |
| U2 | 1 | Flash | 16 MB QSPI NOR | obavezno |
| Y1 | 1 | P4 clock | 40 MHz crystal, ±10 ppm | obavezno |
| U3 | 1 | P4 core DCDC | TLV62569 class | obavezno |
| L1 | 1 | P4 DCDC inductor | prema P4 ref designu | obavezno |
| U4 | 1 | Wireless | ESP32-C6-WROOM-1 | obavezno za Wi-Fi |
| U5 | 1 | MAIN DAC | PCM5102APWR | obavezno |
| U6 | 1 | Dual USB VBUS | TPS2561 | obavezno |
| U7 | 1 | Input eFuse | TPS25947 class | preporučeno |
| U8 | 1 | 3.3 V buck | 2–3 A synchronous buck | obavezno |
| U9 | 1 | LCD backlight | MP3202 class | obavezno |
| U10 | 0/1 | Touch | GT911 | ovisi o modulu |
| DS1 | 1 | Display | 4.3" 480x800 ST7701S | obavezno |
| J1 | 1 | microSD | socket | obavezno |
| J2 | 1 | USB0 | USB-A host | obavezno |
| J3 | 1 | USB1 | USB-A host | obavezno |
| J4 | 1 | MAIN L | RCA | obavezno |
| J5 | 1 | MAIN R | RCA | obavezno |
| J6 | 0/1 | Stereo line out | 3.5 mm | opcionalno |
| J7 | 1 | 5 V input | locking DC connector | obavezno |
| SW1 | 1 | Reset | tactile | obavezno |
| SW2 | 1 | Boot | tactile | obavezno |
| D1 | 1 | Input TVS | 5 V rail class | preporučeno |
| D2 | 1 | USB0 ESD | USB 2.0 low-C | obavezno |
| D3 | 1 | USB1 ESD | USB 2.0 low-C | obavezno |
| U11 | 0/1 | Power monitor | INA226/INA238 | EVT opcija |
| LED1 | 1 | Status | LED ili RGB | preporučeno |
| TPx | više | Test points | power/data/debug | obavezno za Rev A |

---

# 36. Pasivni sklopovi koje će finalni BOM morati sadržavati

Finalni BOM mora eksplicitno uključiti:

## ESP32-P4

- sve decoupling kondenzatore
- core regulator passives
- crystal load C
- reset R/C
- boot pull-up/down
- flash pull-up
- flash tuning resistors
- DSI reference resistor

## USB

- 2× current-limit R
- 2× EN pull-down
- 2× FAULT pull-up
- 2× VBUS bulk C
- 2× ESD array
- FS series R
- HS optional tuning R

## PCM5102A

- 470 Ω ×2
- 2.2 nF ×2
- 100 nF bypass više komada
- bulk C
- charge-pump C
- mode strap resistors

## microSD

- CMD pull-up
- D0–D3 pull-up
- CLK series R
- local bulk C
- ESD

## touch

- SDA pull-up
- SCL pull-up
- RESET pull
- INT pull

## C6

- power decoupling
- EN/reset
- SDIO tuning/pull-up komponente

---

# 37. Audio PCB layout pravila

PCM5102A treba staviti blizu RCA konektora.

Preporučeni tok:

```text
P4
 |
 | I2S digital
 |
PCM5102A
 |
 | analog L/R
 |
RF filter
 |
RCA L / RCA R
```

Digitalne I2S linije ne treba provlačiti paralelno uz analogne izlaze.

Treba:

- odvojiti noisy buck switching node
- držati backlight boost dalje od PCM5102A
- držati USB HS dalje od analognog audio dijela
- koristiti solid GND plane
- pravilno rasporediti analogni i digitalni povrat

Ne preporučuje se rezati GND plane ispod DAC-a bez dobrog razloga.

---

# 38. PCB broj slojeva

Preporučeno:

**4-layer minimum**

Predloženi stack:

```text
L1  Components + critical signals
L2  Solid GND
L3  Power + slower signals
L4  Signals
```

Za bolji SI i lakši routing kasnije se može razmotriti i 6-layer, ali 4-layer je realan minimum.

---

# 39. Zašto 2-layer nije preporučljiv

Ploča ima istovremeno:

- MIPI DSI
- USB High-Speed
- USB Full-Speed
- QSPI flash
- SDIO
- SDMMC
- I2S
- Wi-Fi
- switching regulatore
- analogni audio

Na 2-layer ploči bi bilo vrlo teško osigurati:

- kontinuiranu reference ground ravninu
- kontroliranu impedanciju
- nizak EMI
- dobar return path
- dovoljno čisto analogno područje

---

# 40. Predloženi placement zoning

Preporuka:

```text
┌───────────────────────────────────────┐
│             LCD / FPC                 │
│             MIPI DSI                  │
├───────────────────────────────────────┤
│                                       │
│ ESP32-C6       ESP32-P4      FLASH    │
│ antenna        + core DCDC             │
│                                       │
├──────────────────┬────────────────────┤
│ USB0 + ESD       │ USB1 + ESD         │
│                  │                    │
│      TPS2561 dual VBUS switch         │
├──────────────────┴────────────────────┤
│                                       │
│  PCM5102A                 microSD     │
│     │                                 │
│ RCA L/R                               │
├───────────────────────────────────────┤
│ 5V INPUT -> eFuse -> regulators       │
└───────────────────────────────────────┘
```

Backlight boost treba držati što dalje od PCM5102A analognog područja.

---

# 41. Grounding

Treba koristiti jedan kvalitetan solid GND plane.

Posebnu pažnju dati:

- USB connector shield
- RCA shield
- DC input
- C6 RF return path
- DCDC switching return
- PCM5102A analog return

RCA ground ne treba provlačiti dugim tankim stazama.

---

# 42. Mehanički aspekt

Buduća PCB treba biti projektirana zajedno s kućištem.

Treba rano zaključati:

- LCD FPC poziciju
- USB0
- USB1
- RCA L
- RCA R
- DC input
- microSD dostupnost
- reset/boot dostupnost
- montažne rupe
- PCB visinu
- C6 antenna keep-out

Ako će PCB biti neposredno iza LCD-a, treba paziti na metalni LCD frame i C6 antenu.

---

# 43. Hlađenje

ESP32-P4 pri:

- 200 MHz PSRAM
- LVGL
- MIPI DSI
- dual USB
- Wi-Fi
- dual-deck audio DSP

može razviti značajnu toplinu.

Za PCB treba predvidjeti:

- dovoljan copper spread ispod P4
- thermal vias gdje je dopušteno package preporukom
- airflow
- ne stavljati P4 neposredno uz najtopliji regulator

Kod zatvorenog kućišta treba napraviti multi-hour thermal soak.

---

# 44. Rev A test points

Rev A mora imati test pointove za najmanje:

## Power

- VIN 5V
- 5V_SYS
- 3V3
- P4 core rail
- GND
- USB0 VBUS
- USB1 VBUS

## USB

- USB0 D+
- USB0 D-
- USB1 D+
- USB1 D-

## Audio

- BCLK
- LRCK
- DATA
- DAC OUTL
- DAC OUTR

## Debug

- P4 TX
- P4 RX
- CHIP_PU
- BOOT

## Wi-Fi

- C6 reset
- C6 UART TX/RX ako je moguće

---

# 45. Rev A mjerenja koja moraju proći

Prije zatvaranja hardvera treba definirati acceptance matrix.

## Power

- 5V_SYS idle
- 5V_SYS dual-deck
- startup transient
- Wi-Fi TX transient
- FLX4 connect transient
- USB stick connect transient
- najniži zabilježeni napon

## USB0

- cold boot s umetnutim stickom
- hotplug
- remove/reinsert
- long playback
- filesystem read
- controller active istovremeno

## USB1

- FLX4 enumerate
- MIDI IN
- MIDI OUT
- LED feedback
- UAC audio
- disconnect/reconnect
- više ponovljenih reconnect ciklusa

## Combined

- dual deck
- USB0 mount
- FLX4 MIDI
- FLX4 UAC
- Wi-Fi
- full backlight
- minimalno 30 min
- zatim višesatni soak

---

# 46. Brownout acceptance

S obzirom na postojeću povijest, brownout treba tretirati kao zaseban hardware gate.

Moraju se mjeriti:

- VIN
- 5V_SYS
- 3V3
- P4 core
- USB0 VBUS
- USB1 VBUS

po mogućnosti osciloskopom.

Normalni multimetar može propustiti vrlo kratak voltage dip.

---

# 47. USB VBUS acceptance

Za svaki port treba potvrditi:

- 4.75–5.25 V
- nema backfeeda
- current limit radi
- short-circuit ne resetira P4
- FAULT signal radi
- software power-cycle radi
- drugi USB port ostaje živ tijekom faulta

---

# 48. Budući firmware dodatak koji hardver treba omogućiti

Preporučujem da hardware sada predvidi GPIO za:

- USB0_EN
- USB0_FAULT
- USB1_EN
- USB1_FAULT

i opcionalno:

- SD_PWR_EN
- LCD_PWR_EN
- DAC_XSMT
- power monitor interrupt

Ne mora sve biti implementirano u prvom firmwareu, ali PCB treba dati mogućnost.

---

# 49. Preporučeni Pajoniiir Mainboard Rev A blok dijagram

```text
                           ┌───────────────────┐
                           │  5V DC INPUT      │
                           └─────────┬─────────┘
                                     │
                                   TVS
                                     │
                                   eFuse
                                     │
                                   5V_SYS
                                     │
           ┌─────────────────────────┼──────────────────────────┐
           │                         │                          │
        3.3V BUCK                TPS2561                  BACKLIGHT
           │                  DUAL USB SWITCH                BOOST
           │                    │       │                       │
           │                   VBUS0   VBUS1                    │
           │                    │       │                       │
           │                  USB0    USB1                      │
           │                    │       │                       │
           │                    │       └────────► DDJ-FLX4     │
           │                    │            MIDI + UAC         │
           │                    ▼                              LCD
           │               REKORDBOX USB                       │
           │                                                   │
 ┌─────────┼───────────────┐                                  │
 │         │               │                                  │
 │      ESP32-C6       PCM5102A                               │
 │         ▲               ▲                                  │
 │         │ SDIO          │ I2S                              │
 │         │               │                                  │
 │      ┌──┴───────────────┴────────┐                         │
 │      │         ESP32-P4           │────────────────────────►│
 │      │                            │      MIPI DSI            │
 │      └───────┬──────────┬─────────┘                         │
 │              │          │                                   │
 │             I2C       SDMMC                                 │
 │              │          │                                   │
 │            GT911      microSD                               │
 │              │                                              │
 └──────────────┴───────────────────────────────────────────────┘
```

---

# 50. Konačna preporuka

Za novu PCB ploču ne treba razmišljati kao:

> "Kako da preselim Guition ploču na svoju PCB?"

nego kao:

> "Koji je minimalan, robustan i proizvodno ispravan hardver koji Pajoniiir firmware stvarno treba?"

Prema trenutnom branchu odgovor je:

## Pajoniiir Mainboard treba imati

1. ESP32-P4 nove revizije
2. 32 MB PSRAM
3. 16 MB QSPI flash
4. P4 core DCDC
5. 40 MHz crystal
6. ESP32-C6-WROOM-1
7. 4.3" 480×800 ST7701S MIPI DSI LCD
8. GT911 touch
9. microSD
10. PCM5102A MAIN DAC
11. RCA LEFT
12. RCA RIGHT
13. dual USB host
14. dual current-limited USB VBUS switch
15. USB ESD zaštitu
16. 5 V input eFuse
17. 5 V → 3.3 V buck
18. LCD backlight boost
19. RESET
20. BOOT
21. debug/programming pads
22. status LED
23. test points
24. opcionalni power monitor

## Ne treba imati

- ESP32-S3
- ES8311
- speaker amp
- speaker connector
- analog microphone
- camera
- RS485
- P4/S3 UART
- P4/S3 monitor I2S
- battery circuit u prvoj reviziji
- univerzalni veliki GPIO header

---

# 51. Preporučeni sljedeći razvojni koraci

Nakon ovog dokumenta preporučeni redoslijed je:

1. zaključati blok dijagram
2. odabrati točan ESP32-P4 MPN
3. odabrati točan 16 MB flash
4. odabrati 3.3 V buck
5. odabrati input eFuse
6. zaključati TPS2561
7. definirati USB current limit
8. odabrati točan 4.3" LCD panel/FPC
9. zaključati GT911 izvedbu
10. integrirati PCM5102A reference circuit
11. definirati debug header
12. definirati test pointove
13. napraviti kompletan BOM v0.1
14. nacrtati power tree
15. nacrtati USB blok
16. nacrtati P4 core
17. nacrtati MIPI display
18. nacrtati audio
19. napraviti schematic review
20. tek nakon toga krenuti na PCB layout

---

# 52. Zaključak

Pajoniiir je sada dovoljno hardverski sazrio da se odvoji od development-board faze.

Aktualni branch već jasno dokazuje glavne arhitekturne odluke:

- ESP32-P4 je jedini glavni procesor
- dva USB root porta rade istovremeno
- USB0 je storage
- USB1 je FLX4 MIDI + USB audio
- PCM5102A je MAIN izlaz
- FLX4 je CUE/headphone izlaz
- LCD/touch arhitektura je stabilna
- Wi-Fi ide preko ESP32-C6
- microSD ostaje pomoćni storage
- glavni otvoreni hardverski problem je robustan VBUS/power path

Zbog toga je najvažniji dizajnerski cilj Rev A ploče:

**ne samo integrirati sve komponente, nego eliminirati brownout i USB power rizik koji postoji na prototipu.**

Ako se napajanje, USB VBUS i PCB signal-integrity naprave pravilno, ostatak projekta može vrlo velikim dijelom ostati kompatibilan s već postojećim i testiranim firmwareom.

---

**Predloženi naziv ploče:**  
`Pajoniiir Mainboard Rev A`

**Predloženi sljedeći dokument:**  
`Pajoniiir_Mainboard_BOM_v0.1.md`

u kojem će svaki dio imati:

- RefDes
- Manufacturer
- MPN
- package
- value
- voltage/current rating
- tolerance
- quantity
- lifecycle status
- DNP status
- alternativni dio
- razlog odabira