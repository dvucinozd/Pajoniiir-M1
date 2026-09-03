# Pajoniiir Mainboard — MIPI DSI Display & Backlight Design v0.2

**Projekt:** Pajoniiir BL-A1800 / Pajoniiir-M1  
**Ploča:** Pajoniiir Mainboard Rev A  
**Blok:** 10_DISPLAY_MIPI  
**Datum:** 2026-09-02  
**Status:** Engineering design candidate — DSI and backlight electrical baseline locked as candidate; exact LCD/FPC mechanics remain pre-layout gate

---

# 1. Funkcija

Pajoniiir-M1 zadržava dokazani 4.3" display koncept s JC4880P443C_I_W prototipa:

- 4.3" IPS TFT
- native 480 × 800 portrait
- ST7701S controller
- 2-lane MIPI DSI
- RGB565 pixel path
- UI 800 × 480 landscape kroz PPA rotation
- capacitive GT911 touch na istom display assemblyju / FPC-u

Cilj Rev A nije promijeniti grafičku platformu nego integrirati provjereni display path na vlastitu PCB ploču.

---

# 2. Trenutno dokazani firmware timing

Aktualni Pajoniiir firmware i JC4880 vendor-derived BSP koriste:

| Parametar | Vrijednost |
|---|---:|
| DSI data lanes | 2 |
| lane bit rate | **500 Mbps/lane** |
| DPI pixel clock | **34 MHz** |
| pixel format | RGB565 |
| native width | 480 |
| native height | 800 |
| HSYNC pulse | 12 |
| HSYNC back porch | 42 |
| HSYNC front porch | 42 |
| VSYNC pulse | 2 |
| VSYNC back porch | 8 |
| VSYNC front porch | 166 |

Procijenjeni refresh:

~~~text
34,000,000 /
(480 + 12 + 42 + 42) /
(800 + 2 + 8 + 166)

≈ 48.4 Hz
~~~

Ovo je bench-proven baseline i ne treba ga mijenjati u prvoj PCB reviziji bez razloga.

---

# 3. DSI signal set

Dedicated P4 MIPI DSI PHY:

~~~text
DSI_CLK_P
DSI_CLK_N

DSI_D0_P
DSI_D0_N

DSI_D1_P
DSI_D1_N
~~~

Nema GPIO matrix mapiranja za same DSI laneove.

Control signali:

~~~text
GPIO5  -> LCD_RST
GPIO23 -> LCD_BL_PWM
GPIO6  -> LCD_TE optional
~~~

Touch signali se obrađuju u zasebnom GT911 sheetu.

---

# 4. MIPI DPHY power

ESP32-P4 MIPI DPHY zahtijeva:

**2.5 V nominal**

dozvoljeni range:

**2.25–2.75 V**

Preporučeni izvor:

P4 internal adjustable LDO channel.

Pajoniiir baseline:

~~~text
P4 internal LDO channel 3
 -> configure 2500 mV
 -> P4_LDO_MIPI_2V5
 -> VDD_MIPI_DPHY
~~~

Lokalni decoupling uz P4:

- 10 nF
- 100 nF
- 1 µF

Firmware prije DSI bus init-a mora eksplicitno uključiti 2.5 V LDO.

---

# 5. DSI_REXT

Obavezno:

**4.02 kΩ pull-down**

~~~text
DSI_REXT
  |
4.02k 1%
  |
 GND
~~~

RefDes:

**R_DSI_REXT = 4.02 kΩ 1%**

Smjestiti blizu P4 prema Espressif reference layoutu.

---

# 6. MIPI series tuning footprints

Espressif preporučuje rezervirati series resistors na MIPI komunikacijskim linijama.

Rev A:

~~~text
R_DSI_CLK_P = 0 Ω
R_DSI_CLK_N = 0 Ω
R_DSI_D0_P  = 0 Ω
R_DSI_D0_N  = 0 Ω
R_DSI_D1_P  = 0 Ω
R_DSI_D1_N  = 0 Ω
~~~

Poželjno 0201 ili 0402, potpuno simetrično u paru.

Footprintovi moraju biti inline i ne smiju stvarati stub.

Default populacija = 0 Ω.

---

# 7. MIPI impedance

Aktualni Espressif layout target:

**100 Ω differential ±10%**

Ovo je drugačije od USB-a koji koristi 90 Ω.

PCB fab stackup mora biti poznat prije finalnog trace width/spacinga.

---

# 8. MIPI length matching

Espressif current guideline:

## unutar para

maksimalna razlika:

**<10 mil**

za:

- CLK P/N
- D0 P/N
- D1 P/N

## između parova

cilj:

**<30 mil**

među CLK, D0 i D1 pair lengthovima.

Ne raditi agresivno serpentiniranje ako prirodni route već zadovoljava budget.

---

# 9. MIPI spacing / return path

Pravila:

- continuous GND reference
- najmanje 3W od drugih high-speed/high-frequency signalnih trasa
- ne voditi paralelno s USB/SDIO/clock trasama
- ground copper oko parova gdje je praktično
- CLK pair posebno dobro ground-shieldati
- bez switching power nodeova u blizini
- minimalni parasitic capacitance

Ako se mijenja layer:

- P/N via transition zajedno
- pair ground-return via uz transition

---

# 10. FPC signal inventory

Javni JC4880 schematic reconstruction potvrđuje da LCD FPC nosi sljedeće grupe:

## Power

- ESP_3V3
- GND

## Backlight

- LEDA
- LEDK

## MIPI DSI

- DSI DATA0 P/N
- DSI DATA1 P/N
- DSI CLK P/N

## Touch

- TOUCH_RST
- TOUCH_INT
- SDA
- SCL

## Other

- TE
- LCD reset

To nam daje funkcionalni connector pin inventory.

---

# 11. Exact FPC pin order remains a hard gate

**Ne zaključavati KiCad connector pin numbers dok nemamo authoritative FPC pin order.**

Još nedostaje:

- exact panel manufacturer MPN
- exact FPC pitch
- exact contact count
- top/bottom-contact orientation
- exact pin number order
- LEDA/LEDK electrical specification
- touch power details

Do tada shema smije imati samo placeholder connector block bez finalnog footprint mappinga.

Ovo je namjerna zaštita od skupe PCB greške.

---

# 12. LCD logic power

Community reconstruction pokazuje:

**3.3 V logic/panel power**

Pajoniiir:

~~~text
3V3_SYS
 |
0R / optional filter
 |
3V3_LCD
 |
LCD FPC
~~~

RefDes:

**FB_LCD = 0 Ω default**

Lokalno uz FPC:

- 100 nF
- 4.7 µF ili 10 µF

Finalni zahtjev potvrditi s exact panel datasheetom.

---

# 13. LCD reset

Postojeći dokazani mapping:

**GPIO5**

Topologija:

~~~text
GPIO5 -- 100R -- LCD_RST
                  |
                100k
                  |
                 GND
~~~

Predloženo:

- R_LCD_RST_SER = 100 Ω
- R_LCD_RST_PD = 100 kΩ

Time panel ostaje u resetu/fiksnom stanju dok P4 GPIO još nije konfiguriran.

Ako exact panel traži drugačiji default level, prilagoditi nakon datasheeta.

---

# 14. TE — tearing effect

Panel FPC ima TE signal.

Postojeći Pajoniiir firmware ga ne treba za trenutni DSI/DPI + PPA path, ali Rev A ga ne ostavlja nepovezanog bez opcije.

Predloženo:

~~~text
LCD_TE -- 0R DNP --> GPIO6
~~~

R_LCD_TE_SER:

**0 Ω, DNP default**

TE net također na mali test pad.

Prednost:

- budući scan synchronization
- dodatna tear diagnostics
- nema PCB respina ako firmware kasnije želi TE

---

# 15. Backlight architecture

Candidate driver:

**MP3202DJ-LF-Z**

MPS status:

ACTIVE.

Relevantno:

- 2.5–6 V input
- internal 1.3 A switch/current limit class
- >1 MHz switching
- WLED boost
- 104 mV feedback reference
- open-load protection
- PWM dimming capability

Input:

**5V_SYS**

Output:

**LEDA**

Current return:

**LEDK through current-sense network**

---

# 16. Backlight electrical baseline from original JC4880 schematic

Public forensic reconstruction of the original Guition schematic gives the actual proven backlight network:

| RefDes role | Value / part |
|---|---|
| U_BL | **MP3202DJ-LF-Z** candidate / MP3202 original |
| L_BL | **10 µH** |
| D_BL | **SS14** |
| C_BL_IN | **10 µF / 10 V** |
| C_BL_HF | **100 nF / 25 V** |
| C_BL_OUT | **4.7 µF / 35 V** |
| C_BL_OUT_HF | **100 nF / 50 V** |
| R_BL_PWM | **0 Ω** |
| R_BL_EN_PD | **10 kΩ** |
| R_BL_SENSE_A | **3.9 Ω** |
| R_BL_SENSE_B | **2.2 Ω** |

The two sense resistors are parallel:

~~~text
3.9 Ω || 2.2 Ω ≈ 1.4066 Ω
~~~

With MP3202 typical FB regulation at 104 mV:

~~~text
I_LED ≈ 0.104 V / 1.4066 Ω
      ≈ 73.9 mA
~~~

Rev A full-brightness target:

**approximately 74 mA total LED current**

This is a lock-candidate for the same LCD assembly family used by JC4880.

---

# 17. Rev A PWM strategy

Original JC4880 hardware routes:

~~~text
LCD_PWM
   |
  0 Ω
   |
MP3202 EN
   |
 10 kΩ
   |
  GND
~~~

The current JC4880-derived Pajoniiir BSP happens to use 5 kHz PWM.

MP3202 manufacturer guidance for direct EN PWM is **1 kHz or below** because of soft-start behavior.

Therefore the new M1 board baseline is:

~~~text
GPIO23 LCD_BL_PWM
       |
      0 Ω
       |
MP3202 EN
       |
     10 kΩ
       |
      GND

M1 PWM frequency = 1 kHz
~~~

This intentionally changes only the M1 board-support frequency, not the electrical brightness model.

---

# 18. High-frequency PWM alternative

If DVT proves 1 kHz unacceptable because of visible/acoustic/camera artifacts, MPS supports >1 kHz dimming through a filtered PWM injection into FB.

That approach remains:

**ALT / NOT PRIMARY**

Do not populate the filtered-FB network in the baseline Rev A unless measurements justify it.

---

# 19. Backlight hard shutdown

Direct PWM through EN naturally gives complete backlight shutdown at 0% duty.

The 10 kΩ EN pulldown guarantees:

- backlight OFF while GPIO23 is high-impedance/reset
- no floating EN
- deterministic cold boot

Backlight should remain 0% until the DSI panel has completed reset/init and a valid framebuffer is active.

---

# 20. Backlight EMI placement

MP3202 is a >1 MHz switching boost and must be physically separated from:

- PCM5102A
- MAIN L/R routes
- RCA connectors
- 40 MHz crystal
- C6 antenna
- MIPI DSI pairs

The SW node must have minimum copper area and shortest practical loop.

---

# 21. Backlight power path

~~~text
5V_SYS
 |
10 µF + 100 nF
 |
MP3202
 |
10 µH / SW / SS14
 |
LEDA
 |
LCD LED string
 |
LEDK / FB
 |
3.9 Ω || 2.2 Ω
 |
GND
~~~

Output reservoir:

~~~text
4.7 µF / 35 V
100 nF / 50 V
~~~

During EVT verify actual LEDA voltage, open-load behavior, capacitor DC-bias derating and SS14 reverse-voltage margin.

---

# 22. Display initialization sequence

Hardware/firmware bring-up:

1. 3V3_LCD stable
2. configure P4 internal MIPI LDO = 2.5 V
3. confirm VDD_MIPI_DPHY
4. backlight duty = 0
5. assert/deassert LCD_RST
6. create DSI bus, 2 lanes, 500 Mbps
7. DBI command interface
8. ST7701S init table
9. Sleep Out 0x11
10. wait ~120 ms
11. Display On 0x29
12. wait ~20 ms
13. create DPI path 34 MHz
14. framebuffer/PPA ready
15. ramp backlight

Backlight ne paliti prije stabilne slike.

---

# 23. ST7701S init table source

Ne prepisivati generički ST7701 init s interneta.

Koristiti:

- dokazani Pajoniiir/JC4880 vendor-derived init table
- isti gamma/power values koji su već prošli real-hardware smoke test

Exact init table ostaje u firmware BSP-u, ne u PCB shemi.

---

# 24. Proposed FPC-side ESD

FPC je interni connector, pa nije izložen korisniku kao USB.

Ne dodavati heavy ESD protection na MIPI pair jer capacitance može degradirati link.

Ako enclosure design učini FPC user-serviceable/exposed:

- reevaluate
- koristiti ultra-low-C MIPI-rated ESD samo ako potreban

Baseline:

**no extra MIPI ESD array**

---

# 25. Test points

Power/control:

- TP_3V3_LCD
- TP_MIPI_2V5
- TP_LCD_RST
- TP_LCD_BL_PWM
- TP_LEDA
- TP_LED_CURRENT / LEDK sense
- TP_LCD_TE

MIPI data:

ne koristiti velike TP-ove.

Ako je potreban signal-integrity probing:

- tiny high-speed probe pads
- bez stuba
- DNP/engineering only

---

# 26. Preliminary BOM additions

| RefDes | Qty | Value / part | Status |
|---|---:|---|---|
| J_LCD | 1 | SOFNG 0.5TBQP-30P-1 / C3975120, 30 contacts, 0.5 mm pitch | ID/pitch confirmed; footprint still TBD-MECH pending contact-side/mating geometry, 31/32, pins 15/16/18/19 and 3V3-domain mapping |
| R_DSI_REXT | 1 | 4.02 kΩ 1% | LOCKED |
| R_DSI_CLK_P | 1 | 0 Ω | tuning |
| R_DSI_CLK_N | 1 | 0 Ω | tuning |
| R_DSI_D0_P | 1 | 0 Ω | tuning |
| R_DSI_D0_N | 1 | 0 Ω | tuning |
| R_DSI_D1_P | 1 | 0 Ω | tuning |
| R_DSI_D1_N | 1 | 0 Ω | tuning |
| FB_LCD | 1 | 0 Ω / ferrite option | candidate |
| C_LCD_HF | 1 | 100 nF | candidate |
| C_LCD_BULK | 1 | 10 µF | candidate |
| R_LCD_RST_SER | 1 | 100 Ω | candidate |
| R_LCD_RST_PD | 1 | 100 kΩ | candidate |
| R_LCD_TE_SER | 1 | 0 Ω DNP | optional |
| U_BL | 1 | MP3202DJ-LF-Z | LOCK-CANDIDATE |
| L_BL | 1 | **Coilcraft XGL4030-103MEC — 10 µH ±20%** | LOCK-CANDIDATE; 63 mΩ typ / 69.5 mΩ max DCR, Isat 3.1 A, Irms 3.9 A (40 °C rise) |
| D_BL | 1 | **SS14** | JC4880 proven baseline |
| C_BL_IN | 1 | **10 µF / 10 V** | input |
| C_BL_HF | 1 | **100 nF / 25 V** | input HF |
| C_BL_OUT | 1 | **4.7 µF / 35 V** | output |
| C_BL_OUT_HF | 1 | **100 nF / 50 V** | output HF |
| R_BL_PWM | 1 | **0 Ω** | GPIO23 to EN |
| R_BL_EN_PD | 1 | **10 kΩ** | EN pulldown |
| R_BL_SENSE_A | 1 | **3.9 Ω** | current sense |
| R_BL_SENSE_B | 1 | **2.2 Ω** | current sense |
| R/C_BL_PWM_ALT | set | DNP | filtered >1 kHz PWM alternative |

---

# 27. KiCad nets

~~~text
3V3_SYS
3V3_LCD
5V_SYS
P4_LDO_MIPI_2V5

DSI_CLK_P
DSI_CLK_N
DSI_D0_P
DSI_D0_N
DSI_D1_P
DSI_D1_N
DSI_REXT

LCD_RST
LCD_TE
LCD_BL_PWM
LCD_BL_ENABLE

LEDA
LEDK

GND
~~~

Touch nets from same FPC:

~~~text
TOUCH_SDA
TOUCH_SCL
TOUCH_RST
TOUCH_INT
~~~

ali pripadaju zasebnom sheetu.

---

# 28. Bring-up acceptance

## DSI

- stable 2.5 V PHY rail
- 100% cold boot display init
- no lane errors
- no random blank frames
- no visual corruption
- sustained UI animation

## Timing

- exact native 480×800
- correct RGB color order
- correct PPA 90° landscape rotation
- no tearing regression

## Backlight

- 0–100% smooth range
- no visible flicker
- no audible coil whine
- no interference in PCM5102A output
- no MIPI errors correlated with PWM

---

# 29. Pre-layout hard gates

- [ ] authoritative exact panel MPN
- [ ] exact LCD FPC contact count/pitch
- [ ] exact FPC pin-number order
- [ ] connector top/bottom-contact choice
- [ ] panel 3.3 V current
- [x] Backlight electrical replica values recovered from original JC4880 schematic
- [ ] confirm final purchased panel assembly uses same LED/backlight electrical variant
- [ ] validate ~74 mA target and actual LEDA voltage on EVT
- [x] lock L_BL candidate: XGL4030-103MEC
- [ ] validate M1 direct-EN PWM at 1 kHz
- [ ] 100 Ω differential MIPI geometry from PCB fab stackup
- [ ] FPC/mechanical position in enclosure
- [ ] metal LCD frame checked against C6 antenna

Dok ove stavke nisu zatvorene, **display connector footprint se ne smije freezeati.**

---

# 30. Zaključak

Električki DSI dio Rev A je sada čvrsto definiran:

~~~text
ST7701S
480x800
2-lane MIPI DSI
500 Mbps/lane
34 MHz DPI
RGB565

MIPI:
100 Ω differential
pair skew <10 mil
pair-to-pair <30 mil
4.02k DSI_REXT
0R tuning footprints

CONTROL:
GPIO5 LCD_RST
GPIO23 LCD_BL_PWM
GPIO6 optional TE

POWER:
P4 internal 2.5V LDO -> MIPI DPHY
3V3_SYS -> 3V3_LCD
5V_SYS -> MP3202 -> LEDA/LEDK
~~~

Backlight power values are now lock-candidates from the original JC4880 schematic. The remaining display hard gate is the exact physical panel/FPC connector and resolution of the 30-pin MPN versus 32-pin schematic-symbol discrepancy.

**Sljedeći blok:** 11_TOUCH_GT911 — I2C pull-ups, GPIO3 reset, GPIO4 interrupt, ESD, address-selection timing i firmware migration iz polling u interrupt-capable mode.
