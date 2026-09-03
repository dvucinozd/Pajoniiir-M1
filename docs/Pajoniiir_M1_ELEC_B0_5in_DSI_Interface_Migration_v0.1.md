# Pajoniiir-M1 — M1-ELEC-B0 5-inch DSI Interface Migration v0.1

**Date:** 2026-09-04  
**Status:** SIGNAL MAP LOCKED FROM PAJONIIIR-M3 BENCH EVIDENCE; PRODUCTION CONNECTOR MECHANICS OPEN

---

## 1. Why this migration is now authoritative

The final M1 display is user-confirmed to be the same physical display already used in Pajoniiir-M3.

Pajoniiir-M3 has already performed the expensive uncertainty-reduction work:

- physical 15-pin J2 wiring was confirmed,
- display image was accepted on real hardware,
- backlight control was accepted,
- native landscape/color alignment was accepted,
- FT5426/FT5x06 touch at `0x38` was accepted,
- 100 kHz I2C stability was established,
- a working DSI timing/lane profile was established,
- later waveform/integration testing used that same module.

Reference:

```text
dvucinozd/Pajoniiir-M3
master @ b3e2bee5ded0a836906ab6f689d79a6e6b49d541
```

Therefore M1 does not need to reverse-engineer the display again. It needs to reproduce the known-good electrical contract on a new custom PCB.

---

## 2. Exact 15-pin map

| Pin | Module signal | M1 source/destination |
|---:|---|---|
| 1 | GND | solid GND |
| 2 | DSI DATA1− | P4 `DSI_D1_N` |
| 3 | DSI DATA1+ | P4 `DSI_D1_P` |
| 4 | GND | solid GND |
| 5 | DSI CLK− | P4 `DSI_CLK_N` |
| 6 | DSI CLK+ | P4 `DSI_CLK_P` |
| 7 | GND | solid GND |
| 8 | DSI DATA0− | P4 `DSI_D0_N` |
| 9 | DSI DATA0+ | P4 `DSI_D0_P` |
| 10 | GND | solid GND |
| 11 | I2C SCL | GPIO8 / `DISPLAY_I2C_SCL` |
| 12 | I2C SDA | GPIO7 / `DISPLAY_I2C_SDA` |
| 13 | GND | solid GND |
| 14 | 3V3 | `3V3_DISPLAY_MODULE` |
| 15 | 3V3 | `3V3_DISPLAY_MODULE` |

No panel reset, TE, touch interrupt, touch reset, LEDA or LEDK appears on this interface.

---

## 3. MIPI lane policy

M3's accepted profile uses:

```text
lane0 + clock
1 data lane
800 Mbps
```

The connector nevertheless exposes lane1 on pins 2/3.

M1 rule:

**Route both lane0 and lane1. Do not intentionally delete lane1 from the PCB just because the first firmware profile uses one lane.**

Benefits:

- preserves the native connector contract,
- supports alternate/future module revisions,
- permits later two-lane validation without PCB respin,
- keeps the board electrically closer to the proven development-board wiring.

Initial firmware still starts with one lane because that is the known-good physical result.

---

## 4. Accepted video profile

Latest M3 BSP baseline:

```text
800 x 480 native landscape
RGB888
1 lane @ 800 Mbps
DPI clock 27.777 MHz
HFP 59
HSW 2
HBP 45
VFP 109
VSW 2
VBP 22
~50.0146 Hz
burst with sync pulses
no frame ACK
```

The `VFP=109` profile is later than the earlier M3 wiring-note `VFP=7` snapshot and is the one present in the accepted/current BSP after waveform synchronization work.

M1 must treat the current BSP/source as higher authority than stale descriptive timing text.

---

## 5. Shared I2C

Connector pins 11/12 provide one shared bus:

```text
GPIO8 SCL
GPIO7 SDA
100 kHz
```

Known responses:

```text
0x38 touch
0x45 power/backlight controller
0x18 additional response
```

The M1 schematic should not create a dedicated GT911-only I2C domain. Use a shared `DISPLAY_I2C_*` bus.

I2C pull-up strategy should account for pull-ups already present on the module/development-board wiring. Baseline custom-board recommendation: provide optional/DNP pull-up footprints and confirm rise time on the real M1 cable/module before deciding whether additional populated pull-ups are needed.

---

## 6. Touch migration

Old M1 assumption:

```text
GT911 @ 0x5D
GPIO3 TOUCH_RST
GPIO4 TOUCH_INT
GPIO7 SDA
GPIO8 SCL
```

Final module contract:

```text
FT5426/FT5x06 path @ 0x38
GPIO7 SDA
GPIO8 SCL
100 kHz
no host RST pin on J2
no host INT pin on J2
```

Accepted transform:

```text
swap_xy=0
mirror_x=1
mirror_y=1
```

Consequences:

- release GPIO3,
- release GPIO4,
- remove GT911 address-selection/reset network,
- remove dedicated TOUCH_RST/TOUCH_INT series/pull circuitry from the final design,
- retain only shared I2C signal integrity/tuning features justified by measurement.

---

## 7. Backlight/panel-control migration

Old M1 architecture contains a replica WLED boost:

```text
GPIO23 -> MP3202 EN
MP3202 -> LEDA/LEDK
```

The final module does not need this.

M3 physically proved module-local panel power and brightness control through `0x45`.

Known control registers used by the accepted BSP:

```text
0x85 POWERON
0x86 PWM
0x81 PORTA
```

Baseline production rule:

- keep the module in its factory control configuration,
- do not move its 0-ohm external-PWM selector,
- do not connect GPIO23 external PWM,
- remove MP3202, 10 uH boost inductor, SS14, LEDA/LEDK output capacitors and LED current-sense resistors from the M1 final display path.

GPIO23 becomes available for future use but remains unassigned until another board-wide GPIO review.

---

## 8. Bare-panel control migration

The 15-pin module interface also removes:

```text
GPIO5 LCD_RST
GPIO6 LCD_TE
```

No such pins exist on the accepted J2 interface.

The panel module manages its own local bridge/panel sequencing through its controller architecture. M1 does not add speculative extra reset/TE wires.

---

## 9. 3.3 V display power

M3 module evidence specifies 3.3 V and up to about 340 mA.

M1 already uses a TPS62132 3 A-class 3.3 V regulator.

First-order result:

**PASS for regulator class, not yet final all-on power sign-off.**

Recommended branch:

```text
3V3_SYS
  |
  +-- 0R / ferrite option
  |
3V3_DISPLAY_MODULE
  +-- local bulk capacitor
  +-- 100 nF HF
  +-- J_DISPLAY pins 14 + 15
```

The old split `3V3_LCD -> 3V3_TOUCH` hierarchy is not needed for this integrated module unless EMI/transient measurement later justifies filtering.

Acceptance still requires all-on current and cold-start transient measurement.

---

## 10. MIPI hardware retained from M1-A

The following original M1 engineering remains valid:

- P4 internal MIPI DPHY LDO at 2.5 V,
- DSI_REXT implementation,
- 100-ohm differential target,
- continuous GND reference plane,
- pair length/skew discipline,
- avoid switching-power adjacency,
- route P/N via transitions symmetrically,
- route both physical data lanes.

Existing inline 0-ohm DSI tuning footprints may be retained if their final land pattern and placement do not harm the 100-ohm channel.

---

## 11. Production connector gate

The signal map is locked, but the custom PCB still needs an exact connector.

Remaining evidence:

1. exact 15-position 1.0 mm horizontal FFC receptacle MPN,
2. top-contact or bottom-contact orientation,
3. cable contact orientation/inversion from M1 PCB to the display module,
4. actuator direction and serviceability,
5. connector height,
6. insertion/bend keepout,
7. exact manufacturer footprint/courtyard.

The production footprint must be validated against the physical cable/module; do not choose a connector solely because it says `15 pin 1.0 mm`.

---

## 12. Schematic migration plan

### `10_DISPLAY_MIPI`

Convert from bare-panel/backlight capture into the complete-module interface:

Retain:

```text
MIPI LDO / DPHY support
DSI_REXT
DSI CLK/D0/D1 routing/tuning
3V3 module branch/decoupling
shared display I2C
```

Remove:

```text
30-pin SOFNG J_LCD concept
MP3202 WLED boost and LEDA/LEDK network
LCD_RST
LCD_TE
LCD_BL_PWM
```

Add:

```text
15-pin J_DISPLAY module connector
DISPLAY_I2C_SCL/SDA
3V3_DISPLAY_MODULE pins 14/15
GND pins 1/4/7/10/13
```

### `11_TOUCH_GT911`

The old GT911-specific reset/address-selection architecture is obsolete. During schematic migration either:

- repurpose the sheet as shared display-I2C/touch documentation/tuning, or
- retire the leaf in a controlled root-sheet/validator update.

Do not leave the old GT911 `0x5D` circuitry in the production BOM merely for historical compatibility.

---

## 13. Firmware migration plan

Create/modify `bsp_pajoniiir_m1` from the M3 DSI506 behavior while retaining M1's different USB/audio/power GPIO assignments.

Do not clone the M3 board BSP blindly because M3 and M1 differ elsewhere.

Carry across specifically:

- DSI506 15-pin signal contract,
- 1-lane 800 Mbps starting profile,
- RGB888/timing profile,
- `0x45` power/backlight sequencing,
- `0x38` FT5x06 touch path at 100 kHz,
- accepted touch transform.

---

## 14. Gate result

Closed by M1-ELEC-B0:

- display electrical contact count,
- 15-pin signal order,
- lane polarity/order,
- touch transport/address/bus speed,
- need for host reset/INT,
- backlight-control architecture,
- need for old MP3202,
- need for old GPIO23 PWM,
- need for old LCD reset/TE pins.

Still open:

- exact production FFC connector mechanics,
- all-on 3V3 power/transient EVT,
- new enclosure/connector keepout,
- final PCB placement/routing.

This is sufficient to proceed with the B-series schematic rewrite without further display pinout reverse engineering.
