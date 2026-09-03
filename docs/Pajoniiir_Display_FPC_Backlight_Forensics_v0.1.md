# Pajoniiir-M1 — JC4880 Display FPC & Backlight Forensics v0.1

**Projekt:** Pajoniiir-M1 Rev A  
**Datum:** 2026-09-02  
**Ažurirano:** 2026-09-03  
**Status:** M1-MECH-A9 resolves 30-vs-32 and pins 15/16/18/19; exact panel variant, physical mating/contact-side and 3V3 internal-common status remain hard gates

---

# 1. Svrha

Ovaj dokument bilježi što možemo pouzdano izvući iz originalne Guition JC4880P443 V1.0 sheme za LCD/touch FPC i backlight blok.

Izvor:

```text
Repository:
abludomotica-hue/Ablutech-Academy-Pro

File:
Cursos_Generados/Modulo-JC4880P443C/Extracts/
JC4880P443_V1.0_extracted.txt
```

To je tekstualna ekstrakcija javno mirrorane originalne Guition sheme.

Dodatno je potvrđen javni vendor-package mirror:

```text
wegi1/ESP32P4-JC4880P443C-I-W
5-Schematic/JC4880P443_V1.0.pdf
```

---

# 2. FPC1 identification

Originalna shema označava LCD connector:

```text
FPC1
0.5TBQP-30P-1
```

JLCPCB catalog za taj MPN potvrđuje:

- manufacturer: **SOFNG**
- MPN: **0.5TBQP-30P-1**
- JLCPCB: **C3975120**
- package: **FPC0.5mm-30pin**
- pitch: **0.5 mm**
- nominal electrical contact count: **30**

Dakle **MPN, nominalni broj kontakata i pitch više nisu nepoznati**. M1-MECH-A9 dodatno potvrđuje da Altium reference 31/32 nisu dodatni FPC kontakti nego auxiliary shell/mount reference vezane na GND. Stvarna mating/contact-side geometrija i dalje nije zaključana.

## Critical discrepancy

Tekstualna schematic ekstrakcija istovremeno sadrži symbol references:

```text
PIFPC101 ... PIFPC1032
```

dakle 32 numerirana symbol pina.

To više nije konflikt oko nominalnog konektora — SOFNG dio je 30-contact / 0.5 mm — nego konflikt između **30 električnih kontakata** i **32 Altium symbol referencea**:

```text
physical/electrical connector identity = 30 contacts, 0.5 mm
Altium extracted symbol references      = 1 ... 32
```

M1-MECH-A9 zatvara ovu dilemu: originalni Guition raster prikazuje **kontakte 1..30** unutar FPC1 te zasebne reference **31 i 32** izvan kontaktnog niza, obje vezane na GND. To odgovara 30 električnih kontakata + 2 shell/mount referencea.

J_LCD footprint se i dalje ne zaključava jer contact-side, mating height/insertion geometry i konačna panel varijanta još nisu potvrđeni.

---

# 3. High-confidence FPC pin mapping

Iz extracted connectivity referenci možemo vrlo visoko pouzdano rekonstruirati sljedeće.

| FPC1 pin | Net | Funkcija |
|---:|---|---|
| 1 | LEDK | backlight cathode/current-return node |
| 2 | LEDA | boosted LED anode rail |
| 3 | GND | ground |
| 4 | ESP_3V3 | panel/touch 3.3 V |
| 5 | GND | ground |
| 6 | DSI_A_DATA0_P | MIPI lane 0 + |
| 7 | DSI_A_DATA0_N | MIPI lane 0 - |
| 8 | GND | ground |
| 9 | DSI_A_DATA1_P | MIPI lane 1 + |
| 10 | DSI_A_DATA1_N | MIPI lane 1 - |
| 11 | GND | ground |
| 12 | DSI_A_CLK_P | MIPI clock + |
| 13 | DSI_A_CLK_N | MIPI clock - |
| 14 | GND | ground |
| 17 | GND | ground |
| 20 | GND | ground |
| 21 | ESP_3V3 | panel/touch 3.3 V |
| 22 | TE | tearing-effect output |
| 23 | GPIO5 | LCD reset |
| 24 | GND | ground |
| 25 | TOUCH_RST | GT911 reset |
| 26 | RTC_DAT/SDA1 | touch I2C SDA |
| 27 | RTC_CLK/SCL1 | touch I2C SCL |
| 28 | TOUCH_INT | GT911 interrupt |
| 29 | ESP_3V3 | panel/touch 3.3 V |
| 30 | GND | ground |
| 31 | GND | auxiliary shell/mount reference; resolved M1-MECH-A9 |
| 32 | GND | auxiliary shell/mount reference; resolved M1-MECH-A9 |

## Pins 15/16/18/19 — resolved NC

Text extraction alone was ambiguous, but the original Guition LCD schematic raster is explicit: FPC1 pins **15, 16, 18 and 19** carry no-connect markers.

M1-MECH-A9 therefore records:

```text
15 = NC
16 = NC
18 = NC
19 = NC
```

This resolution applies to the original JC4880 electrical variant and must still be cross-checked if a different final purchased panel variant is selected.

## 3.1. 3V3 supply-domain hard gate

Originalna Guition shema vodi FPC1 pinove **4, 21 i 29** na isti net `ESP_3V3`.

Pajoniiir-M1 namjerno ima dvije filtrirane domene:

```text
3V3_LCD
3V3_TOUCH
```

Dok se ne potvrdi jesu li panel/FPC 3V3 pinovi 4/21/29 interno međusobno spojeni, **ne smijemo ih proizvoljno raspodijeliti između 3V3_LCD i 3V3_TOUCH**. U suprotnom bi sam panel mogao premostiti dva filtera i poništiti namjernu rail separaciju.

To je stvarni električni hard-gate za instanciranje J_LCD, odvojen od čiste mehaničke nepoznanice footprinta.

---

# 4. What this confirms for Pajoniiir-M1

The new M1 connector must carry:

```text
LEDA
LEDK
3V3_LCD / 3V3_TOUCH
GND

DSI_D0_P/N
DSI_D1_P/N
DSI_CLK_P/N

LCD_RST
LCD_TE

TOUCH_RST
TOUCH_INT
TOUCH_SDA
TOUCH_SCL
```

Our custom-board remap remains valid:

```text
FPC TOUCH_RST -> M1 GPIO3
FPC TOUCH_INT -> M1 GPIO4
FPC SDA       -> M1 GPIO7
FPC SCL       -> M1 GPIO8
FPC LCD_RST   -> M1 GPIO5
FPC TE        -> M1 GPIO6 optional
```

We do NOT need to preserve the old motherboard's GPIO assignment for touch reset/interrupt.

---

# 5. Original JC4880 MP3202 backlight block

Original schematic values:

| RefDes | Original value / MPN | Function |
|---|---|---|
| IC1 | MP3202 | WLED boost driver |
| L3 | **10 µH** | boost inductor |
| D8 | **SS14** | Schottky rectifier |
| C57 | **10 µF / 10 V** | input/local capacitor |
| C54 | **100 nF / 25 V** | local/input bypass |
| C55 | **4.7 µF / 35 V** | boosted output capacitor |
| C56 | **100 nF / 50 V** | high-frequency output/OV network capacitor |
| R69 | **0 Ω** | LCD_PWM → EN series link |
| R72 | **10 kΩ** | EN pulldown |
| R66 | **3.9 Ω** | LED sense resistor |
| R67 | **2.2 Ω** | LED sense resistor |

Backlight nets:

```text
LEDA
LEDK
LCD_PWM
VOUT-BAT on old board
GND
```

For Pajoniiir-M1:

```text
old VOUT-BAT -> new 5V_SYS
```

---

# 6. LED current reconstruction

R66 and R67 are parallel from the LEDK / FB current-sense node to GND.

Equivalent resistance:

```text
R_EQ = 3.9 Ω || 2.2 Ω

R_EQ ≈ 1.4066 Ω
```

MP3202 typical feedback reference:

```text
V_FB ≈ 104 mV
```

Therefore approximate full-brightness LED current:

```text
I_LED ≈ 0.104 V / 1.4066 Ω

I_LED ≈ 73.9 mA
```

Engineering baseline:

**~74 mA total LED current at 100% brightness**

Tolerance must include:

- MP3202 FB range
- R66/R67 tolerance
- temperature
- LED string characteristics

This is sufficient to lock the first Rev A electrical replica for the same panel assembly.

---

# 7. PWM discovery

Original JC4880 hardware:

```text
LCD_PWM
   |
  0 Ω R69
   |
MP3202 EN

EN
 |
10 kΩ R72
 |
GND
```

So the original board uses **direct EN PWM dimming**, not FB injection dimming.

---

# 8. Conflict with current Pajoniiir firmware

Current JC4880-derived Pajoniiir BSP uses:

```text
GPIO23 LEDC
frequency = 5 kHz
```

MP3202 manufacturer guidance says direct EN PWM should be approximately:

**1 kHz or below**

because of the device soft-start behavior.

For PWM above 1 kHz, MPS recommends a filtered-PWM feedback topology.

Therefore current prototype state is:

```text
hardware topology: direct EN PWM
firmware: 5 kHz
manufacturer preferred direct-EN frequency: <=1 kHz
```

It works on the development board, but it is not the cleanest baseline for a new production design.

---

# 9. Pajoniiir-M1 Rev A recommendation

Primary recommendation:

**retain the proven direct-EN hardware topology and change the new M1 BSP backlight PWM to 1 kHz.**

Rev A:

```text
GPIO23
  |
0 Ω
  |
MP3202 EN
  |
10 kΩ
  |
GND

PWM = 1 kHz
```

Reasons:

1. follows MP3202 direct-PWM guidance
2. reproduces original Guition hardware topology
3. fewer components
4. simpler validation
5. no analog FB injection network
6. brightness remains duty-cycle controlled
7. firmware change is trivial in M1-specific BSP
8. old JC4880 target can keep its existing 5 kHz value if desired

---

# 10. Alternative if 1 kHz is unacceptable

If testing finds:

- visible flicker
- audible interaction
- camera-band artifacts
- unacceptable acoustic behavior

then use MPS filtered-PWM topology for >1 kHz.

That is **ALT**, not primary Rev A.

Do not implement both baseline methods at once unless needed for DVT tuning.

---

# 11. Rev A backlight baseline

For the same display assembly:

~~~text
U_BL       = MP3202DJ-LF-Z
L_BL       = 10 µH
D_BL       = SS14
C_BL_IN    = 10 µF / 10 V
C_BL_HF    = 100 nF / 25 V
C_BL_OUT   = 4.7 µF / 35 V
C_BL_OUTHF = 100 nF / 50 V

R_BL_PWM   = 0 Ω
R_BL_EN_PD = 10 kΩ

R_BL_SENSE_A = 3.9 Ω
R_BL_SENSE_B = 2.2 Ω

I_LED_nominal ≈ 74 mA
PWM direct to EN = 1 kHz on M1
~~~

---

# 12. Voltage-rating caution

Even though the old schematic uses the listed voltage ratings, the new PCB should verify:

- measured LEDA boost voltage at 100%
- open-load OV voltage
- actual capacitor DC-bias derating
- Schottky reverse-voltage margin

Especially:

**C55 4.7 µF / 35 V** must be selected with sufficient effective capacitance at actual boost voltage.

A higher voltage-rated MLCC or suitable technology may be preferred if package/availability allow.

---

# 13. What remains unresolved

The backlight electrical blocker is now substantially resolved.

Still unresolved before final J_LCD footprint lock:

1. exact physical panel MPN / purchased panel variant
2. contact-side orientation
3. physical mating height and authoritative mechanical drawing
4. interpretation of Altium symbol references 31/32
5. pins 15/16/18/19
6. whether FPC 3V3 pins 4/21/29 are internally common, and therefore how they may safely map to M1 3V3_LCD / 3V3_TOUCH
7. confirmation that the final purchased panel assembly is the same electrical variant as JC4880

Already resolved: **SOFNG 0.5TBQP-30P-1, C3975120, 30 contacts, 0.5 mm pitch**.

---

# 14. Confidence classification

## HIGH confidence

- MP3202
- 10 µH
- SS14
- 3.9 Ω || 2.2 Ω
- 0 Ω PWM-to-EN
- 10 kΩ EN pulldown
- 10 µF / 100 nF input side
- 4.7 µF / 100 nF output side
- FPC DSI lane mapping listed above
- TE, reset, touch SDA/SCL/RST/INT presence
- 3.3 V and GND pins listed above

## MEDIUM confidence

- SOFNG 0.5TBQP-30P-1 as the exact production connector variant until contact-side/mating geometry is checked against the physical panel

## NOT YET LOCKED

- FPC 3V3 pins 4/21/29 internal-common status / safe M1 rail mapping
- exact final panel supplier MPN
- connector contact-side/orientation/mating height
- physical interpretation of symbol references 31/32

---

# 15. Design decision

For Pajoniiir-M1 Rev A:

**BACKLIGHT ELECTRICAL BASELINE = LOCK-CANDIDATE**

using the original JC4880 values above.

**FPC FOOTPRINT = STILL BLOCKED**

Nominal connector identity, 30-contact count, 0.5 mm pitch, 31/32 shell role and NC status of pins 15/16/18/19 are now known. Final footprint lock still waits for mating/contact-side mechanics, exact final panel variant, and safe 3V3 domain mapping for contacts 4/21/29.


---

## M1-MECH-A9 evidence update

Primary visual evidence used for the two resolved sub-gates:

- Original Guition LCD/CSI schematic raster mirrored from the board documentation package:  
  https://github.com/wegi1/ESP32P4-JC4880P443C-I-W/blob/main/5-Schematic/2_LCD%26CSI.png
- JLCPCB component record confirming SOFNG `0.5TBQP-30P-1`, `C3975120`, package `FPC0.5mm-30pin`:  
  https://jlcpcb.com/partdetail/SOFNG-0_5TBQP_30P1/C3975120

The visual source is stronger than text-extraction ordering for NC markers and shell-pin interpretation.
