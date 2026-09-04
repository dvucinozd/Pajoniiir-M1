# Pajoniiir-M1 — Hardware / Firmware Contract v0.2

**Projekt:** Pajoniiir-M1 Rev A  
**Datum:** 2026-09-04  
**Status:** Current pre-bring-up custom-PCB contract after M1-ELEC-B2 implementation

---

## 1. Purpose

The custom M1 PCB gets a dedicated firmware target:

```text
bsp_pajoniiir_m1
```

The board is not a JC4880 clone. It combines M1-specific power/USB/audio/service hardware with the same 5-inch DSI506/DYL0023 display module already accepted in Pajoniiir-M3.

The M3 display BSP is the reference for display/touch behavior; M1 must not carry forward the old 4.3-inch ST7701S/GT911/MP3202 assumptions.

---

## 2. Silicon contract

```text
ESP32-P4NRW32X
production target silicon v3.2+
```

M1 and old JC4880 binaries remain separate build artifacts.

---

## 3. GPIO contract

```text
GPIO7   DISPLAY_I2C_SDA
GPIO8   DISPLAY_I2C_SCL

GPIO14  C6_SDIO_D0
GPIO15  C6_SDIO_D1
GPIO16  C6_SDIO_D2
GPIO17  C6_SDIO_D3
GPIO18  C6_SDIO_CLK
GPIO19  C6_SDIO_CMD

GPIO20  USB0_PWR_EN
GPIO21  USB0_FAULT_N
GPIO22  USB1_PWR_EN
GPIO24  P4_USB_SERIAL_JTAG_DM
GPIO25  P4_USB_SERIAL_JTAG_DP
GPIO26  USB1_FS_DM
GPIO27  USB1_FS_DP
GPIO32  USB1_FAULT_N

GPIO35  BOOT
GPIO36  BOOT_STRAP_HIGH
GPIO37  UART0_TX
GPIO38  UART0_RX

GPIO39  SDMMC_D0
GPIO40  SDMMC_D1
GPIO41  SDMMC_D2
GPIO42  SDMMC_D3
GPIO43  SDMMC_CLK
GPIO44  SDMMC_CMD
GPIO45  SD_PWR_EN
GPIO46  SD_CARD_DETECT optional

GPIO49  DAC_XSMT
GPIO50  DAC_BCLK
GPIO51  DAC_DATA
GPIO52  DAC_LRCK
GPIO53  SYS_POWER_ALERT_N optional
GPIO54  C6_RESET
```

Released by the final display migration:

```text
GPIO3  old TOUCH_RST
GPIO4  old TOUCH_INT
GPIO5  old LCD_RST
GPIO6  old LCD_TE
GPIO23 old LCD_BL_PWM
```

These are free candidates, not automatically assigned to new features.

---

## 4. Final display connector contract

The final module uses a 15-pin 1.0 mm DSI connector:

```text
1   GND
2   DSI DATA1-
3   DSI DATA1+
4   GND
5   DSI CLK-
6   DSI CLK+
7   GND
8   DSI DATA0-
9   DSI DATA0+
10  GND
11  I2C SCL  -> GPIO8
12  I2C SDA  -> GPIO7
13  GND
14  3V3
15  3V3
```

M1 routes clock, lane0 and lane1. Initial firmware activates lane0 only because that profile is already accepted on the same module in M3.

---

## 5. DSI PHY/video contract

P4 internal MIPI LDO remains required:

```text
LDO channel 3
2500 mV
VDD_MIPI_DPHY
```

Initial display profile:

```text
resolution       800 x 480
orientation      native landscape
DSI lanes active 1
lane rate        800 Mbps
format           RGB888
DPI clock        27.777 MHz
HFP/HSW/HBP      59 / 2 / 45
VFP/VSW/VBP      109 / 2 / 22
mode             burst with sync pulses
frame ACK        off
```

Do not copy the old ST7701S 480x800 / 500 Mbps / RGB565 init table into the M1 target.

Lane1 stays physically routed even though the initial profile does not use it.

---

## 6. Shared display I2C contract

```text
SDA GPIO7
SCL GPIO8
100 kHz
```

Known module devices:

```text
0x38 touch
0x45 panel power/backlight controller
0x18 additional module response observed in M3 diagnostics
```

Do not issue generic register writes to unknown `0x18`.

---

## 7. Touch contract

The accepted touch path is FT5426/FT5x06-compatible at `0x38`.

No dedicated M1 GPIO reset or interrupt is carried by the 15-pin interface.

Initial transform:

```text
swap_xy  = 0
mirror_x = 1
mirror_y = 1
```

The accepted bus rate is **100 kHz**. Do not raise it to 400 kHz by default; M3 found 400 kHz caused runtime touch read failures on this module.

---

## 8. Panel power/backlight contract

The module-local controller at `0x45` owns panel power and brightness.

Known M3 register contract:

```text
0x85 POWERON
0x86 PWM
0x81 PORTA
```

Baseline startup concept:

1. initialize shared I2C,
2. attach `0x45`,
3. PWM = 0,
4. POWERON = 0 and settle,
5. acquire 2.5 V MIPI LDO,
6. create DSI host,
7. POWERON = 1,
8. allow panel/controller settle,
9. create/start DPI video,
10. set required module enable/orientation state,
11. ramp PWM through `0x45`.

The final M1 PCB does **not** use GPIO23 external PWM and does not populate an MP3202 WLED boost for this display.

Do not move the display module's 0-ohm external-PWM selector in baseline production.

---

## 9. Display power contract

Module supply:

```text
3V3_DISPLAY_MODULE
pins 14 + 15
GND pins 1/4/7/10/13
```

M3 specification evidence records up to **340 mA** at 3.3 V.

M1 TPS62132 is a 3 A-class 3.3 V regulator, so regulator nameplate capacity passes first-order screening. The following remain mandatory before release:

- all-on M1 3V3 current measurement,
- cold-start rail droop/overshoot,
- display enable/backlight transients,
- local connector bulk/decoupling validation.

Use a dedicated `3V3_DISPLAY_MODULE` branch with a 0-ohm/ferrite option and local capacitance.

---

## 10. USB VBUS contract

Both ports power up hardware-off.

```text
USB0 EN GPIO20 / FAULT GPIO21
USB1 EN GPIO22 / FAULT GPIO32
```

Stagger enable to avoid simultaneous inrush. Fault recovery should power-cycle only the affected port before escalating to a system reset.

USB0 remains the P4 dedicated HS storage root. USB1 FS remains GPIO26/27 for DDJ-FLX4.

---

## 11. PCM5102A contract

```text
GPIO50 BCLK
GPIO52 LRCK
GPIO51 DATA
GPIO49 XSMT
MCLK unused
```

Hold XSMT low through boot/reconfiguration and unmute only after clocks/stream are stable.

---

## 12. microSD / C6 / service contracts

microSD:

```text
D0..D3 GPIO39..42
CLK GPIO43
CMD GPIO44
power enable GPIO45
card detect GPIO46 optional
```

ESP32-C6 SDIO:

```text
D0..D3 GPIO14..17
CLK GPIO18
CMD GPIO19
RESET GPIO54
```

Recovery/service remains UART0 GPIO37/38 plus USB Serial/JTAG pogo on GPIO24/25.

---

## 13. Bring-up acceptance for M1 display

M1 hardware bring-up starts from the M3-known-good profile and then verifies the custom PCB:

- 3.3 V module rail startup and current,
- DPHY 2.5 V,
- `0x38` and `0x45` presence,
- stable 800x480 image,
- correct color order,
- touch at 100 kHz,
- brightness 0..100 through `0x45`,
- cold boot/reconnect,
- sustained UI/waveform scanout,
- no display-induced audio/USB regression.

A failure on the M1 custom PCB should first be treated as a board/power/SI/integration regression against a known-good module profile, not as a reason to invent a new panel driver.
