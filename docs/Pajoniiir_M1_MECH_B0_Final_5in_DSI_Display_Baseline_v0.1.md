# Pajoniiir-M1 — M1-MECH-B0 Final 5-inch DSI Display Baseline v0.2

**Date:** 2026-09-04  
**Revision:** M1-MECH-B0 / corrected by M1-ELEC-B0  
**Status:** FINAL PRODUCT DISPLAY MODULE SELECTED; M3 BENCH IDENTITY/PINOUT ADOPTED

---

## 1. Product decision

Pajoniiir-M1 Rev A will use the same physical 5-inch MIPI-DSI capacitive-touch module already used and hardware-accepted in **Pajoniiir-M3**.

The authoritative project identity is therefore:

```text
EYOYO DSI506 / DYL0023
5.0 inch
800 x 480 IPS
MIPI DSI
capacitive touch
3.3 V
15-pin 1.0 mm Raspberry-Pi-style FFC
```

The earlier B0 text used the visually/electrically similar Elecrow `DSI05379I` retail module as a public cross-reference. That retail identification is no longer the final-project authority. The user has confirmed that the final M1 display is the same display used in Pajoniiir-M3, where the DSI506/DYL0023 module has already passed real-hardware display/touch/backlight acceptance.

The old 4.3-inch Guition/JC4880 bare-panel architecture remains superseded.

---

## 2. Cross-project authority

Reference repository:

```text
dvucinozd/Pajoniiir-M3
master @ b3e2bee5ded0a836906ab6f689d79a6e6b49d541
```

Primary evidence:

- `firmware/main-deck-p4/components/bsp_p4_m3/include/bsp_p4_m3.h`
- `firmware/main-deck-p4/components/bsp_p4_m3/bsp_p4_m3.c`
- `docs/HARDWARE_WIRING.md`
- `docs/DISPLAY_DSI506_BRINGUP.md`

M3 records physical acceptance of image, backlight, native landscape orientation and focused capacitive touch on this module. This is stronger evidence for M1 than deriving the interface again from a generic Raspberry Pi display listing.

---

## 3. Locked 15-pin electrical map

The M3 BSP explicitly records the J2 15-pin map:

| Pin | DSI506 signal | M1 net |
|---:|---|---|
| 1 | GND | GND |
| 2 | DSI DATA1− | `DSI_D1_N` |
| 3 | DSI DATA1+ | `DSI_D1_P` |
| 4 | GND | GND |
| 5 | DSI CLK− | `DSI_CLK_N` |
| 6 | DSI CLK+ | `DSI_CLK_P` |
| 7 | GND | GND |
| 8 | DSI DATA0− | `DSI_D0_N` |
| 9 | DSI DATA0+ | `DSI_D0_P` |
| 10 | GND | GND |
| 11 | I2C SCL | `DISPLAY_I2C_SCL` / GPIO8 |
| 12 | I2C SDA | `DISPLAY_I2C_SDA` / GPIO7 |
| 13 | GND | GND |
| 14 | 3V3 | `3V3_DISPLAY_MODULE` |
| 15 | 3V3 | `3V3_DISPLAY_MODULE` |

This signal map is now locked for M1. The remaining connector gate is **mechanical**: exact receptacle MPN, contact side, cable inversion and mating keepout.

---

## 4. Bench-accepted operating profile

Latest accepted M3 baseline:

```text
resolution       800 x 480 native landscape
DSI data lanes   1 active
lane rate        800 Mbps
pixel format     RGB888
DPI clock        27.777 MHz
HFP/HSW/HBP      59 / 2 / 45
VFP/VSW/VBP      109 / 2 / 22
refresh          ~50.0146 Hz
video mode       burst with sync pulses
frame ACK        disabled
```

M1 hardware will still route both physical DSI data lanes because the 15-pin connector exposes lane 1 and preserving it costs little compared with a board respin. Initial M1 firmware should start from the M3-accepted one-lane profile.

---

## 5. Touch and module control

The 15-pin cable carries a shared I2C bus:

```text
GPIO7  SDA
GPIO8  SCL
100 kHz
```

Bench-observed/accepted devices include:

```text
0x38  FT5426 / FT5x06 touch path
0x45  module power/backlight controller
0x18  additional module-side I2C response; role not required for baseline operation
```

Accepted touch transform:

```text
swap_xy  = 0
mirror_x = 1
mirror_y = 1
```

The final module does not require host-side TOUCH_RST or TOUCH_INT wires on the 15-pin interface.

---

## 6. Backlight architecture consequence

M3 proves that the module controls panel power/backlight through its local controller at `0x45`.

Factory configuration does **not** require GPIO23 external PWM. The module's external PWM header requires moving a local 0-ohm selector and is not part of the M1 production baseline.

Therefore the final M1 display path does not need:

- MP3202 WLED boost,
- LEDA/LEDK wiring,
- current-sense network,
- GPIO23 `LCD_BL_PWM`.

These are legacy 4.3-inch bare-panel provisions and should be removed during the B-series schematic migration.

---

## 7. GPIO consequence

The final module also removes the need for the old bare-panel control pins:

```text
GPIO3  old TOUCH_RST  -> released
GPIO4  old TOUCH_INT  -> released
GPIO5  old LCD_RST    -> released
GPIO6  old LCD_TE     -> released
GPIO23 old LCD_BL_PWM -> released

GPIO7  DISPLAY_I2C_SDA -> retained/locked
GPIO8  DISPLAY_I2C_SCL -> retained/locked
```

Dedicated ESP32-P4 MIPI DSI pins remain non-GPIO PHY signals.

---

## 8. Power

The M3 display specification evidence records:

```text
3.3 V
maximum current 340 mA
```

M1 uses a TPS62132-class 3.3 V / 3 A system regulator, so the display passes a first-order regulator-capacity screen. Final all-on rail current, startup transient and local decoupling are still EVT requirements.

Proposed M1 branch:

```text
3V3_SYS
  |
  +-- 0R / ferrite option
  |
3V3_DISPLAY_MODULE
  +-- local bulk
  +-- 100 nF HF
  +-- pins 14 + 15 of DSI connector
```

Do not resurrect separate `3V3_LCD` / `3V3_TOUCH` domains unless measurement demonstrates a need.

---

## 9. Mechanical evidence

The user-provided dimensioned rear image remains the current M1 mechanical authority for preliminary CAD:

```text
rear PCB envelope      121.109 x 77.193 mm
outer hole diameter    ~2.50 mm
outer hole centers     (5.000,5.000)
                       (116.109,5.000)
                       (5.000,72.930)
                       (116.109,72.930)
outer pattern          ~111.109 x 67.930 mm
```

There are eight visible mounting holes; all eight must be confirmed from physical measurement or official CAD before production enclosure release.

---

## 10. Old enclosure incompatibility

Previous enclosure candidate:

```text
external 121.008 x 73.408 mm
inner    117.008 x 69.408 mm
```

Display PCB:

```text
121.109 x 77.193 mm
```

Therefore the old enclosure remains a hard fail and must be redesigned.

---

## 11. Freeze state

```text
final display physical module selected       YES
M3 bench signal map adopted                   YES
15-pin electrical pin map locked              YES
initial DSI operating profile known           YES
shared I2C/touch/backlight behavior known     YES
old 30-pin Guition FPC superseded             YES
old MP3202 backlight architecture superseded  YES
old GT911 RST/INT architecture superseded     YES
production 15-pin receptacle MPN locked       NO
FFC contact-side/cable inversion locked       NO
3V3 all-on/transition EVT complete             NO
new enclosure locked                           NO
mainboard outline locked                       NO
placement/routing freeze allowed               NO
```

The next electrical step is no longer reverse-engineering the display pinout. It is selecting the production 15-pin connector and migrating `10_DISPLAY_MIPI` / touch support to this already bench-proven module contract.
