# Pajoniiir Mainboard — Global GPIO Allocation v0.2

**Projekt:** Pajoniiir-M1 Rev A

**MCU:** ESP32-P4 v3.2+ / ESP32-P4NRW32X production target

**Datum:** 2026-09-04

**Status:** Current central GPIO authority after M1-ELEC-B2 implementation

---

## 1. Authority change

This file remains the central GPIO source of truth for the custom M1 board.

M1-ELEC-B0 replaces the old 4.3-inch Guition display/touch assignment with the same 5-inch DSI506/DYL0023 module already accepted in Pajoniiir-M3. The final display needs only the shared I2C GPIO7/8 in addition to the dedicated MIPI DSI PHY.

Therefore old `TOUCH_RST`, `TOUCH_INT`, `LCD_RST`, `LCD_TE` and external `LCD_BL_PWM` GPIO ownership is released.

---

## 2. GPIO allocation

| GPIO | Pajoniiir-M1 function | Status | Note |
|---:|---|---|---|
| 0 | Reserved / future LP | FREE-RESERVED | no 32.768 kHz crystal in Rev A |
| 1 | Reserved / future LP | FREE-RESERVED | no 32.768 kHz crystal in Rev A |
| 2 | Spare | FREE | test/aux candidate |
| 3 | Spare | **FREE** | released from old GT911 TOUCH_RST by M1-ELEC-B0 |
| 4 | Spare | **FREE** | released from old GT911 TOUCH_INT by M1-ELEC-B0 |
| 5 | Spare | **FREE** | released from old bare-panel LCD_RST by M1-ELEC-B0 |
| 6 | Spare | **FREE** | released from old bare-panel LCD_TE by M1-ELEC-B0 |
| 7 | **DISPLAY_I2C_SDA** | **LOCKED** | DSI506 J2 pin 12; touch 0x38 + panel controller 0x45 |
| 8 | **DISPLAY_I2C_SCL** | **LOCKED** | DSI506 J2 pin 11; 100 kHz accepted baseline |
| 9 | Spare | FREE | old ES8311 DOUT removed |
| 10 | Spare | FREE | old ES8311 LRCK removed |
| 11 | Spare | FREE | old speaker PA removed |
| 12 | Spare | FREE | old ES8311 BCLK removed |
| 13 | Spare | FREE | old ES8311 MCLK removed |
| 14 | **C6_SDIO_D0** | LOCKED | ESP-Hosted |
| 15 | **C6_SDIO_D1** | LOCKED | ESP-Hosted |
| 16 | **C6_SDIO_D2** | LOCKED | ESP-Hosted |
| 17 | **C6_SDIO_D3** | LOCKED | ESP-Hosted |
| 18 | **C6_SDIO_CLK** | LOCKED | ESP-Hosted |
| 19 | **C6_SDIO_CMD** | LOCKED | ESP-Hosted |
| 20 | **USB0_PWR_EN** | LOCK-CANDIDATE | TPS25221 USB0 |
| 21 | **USB0_FAULT_N** | LOCK-CANDIDATE | TPS25221 USB0 |
| 22 | **USB1_PWR_EN** | LOCK-CANDIDATE | TPS25221 USB1 |
| 23 | Spare | **FREE** | external display PWM not used in DSI506 factory configuration |
| 24 | **P4_USB_SERIAL_JTAG_DM** | RESERVED | factory/service |
| 25 | **P4_USB_SERIAL_JTAG_DP** | RESERVED | factory/service |
| 26 | **USB1_FS_DM** | LOCK-CANDIDATE | DDJ-FLX4 |
| 27 | **USB1_FS_DP** | LOCK-CANDIDATE | DDJ-FLX4 |
| 28 | Spare / future Ethernet group | FREE-RESERVED | do not consume casually |
| 29 | Spare / future Ethernet group | FREE-RESERVED | do not consume casually |
| 30 | Spare / future Ethernet group | FREE-RESERVED | do not consume casually |
| 31 | Spare / future Ethernet group | FREE-RESERVED | do not consume casually |
| 32 | **USB1_FAULT_N** | LOCK-CANDIDATE | TPS25221 USB1 |
| 33 | Spare | FREE | Ethernet not Rev A target |
| 34 | Strapping / spare | RESERVED-STRAP | do not load at reset |
| 35 | **BOOT_MODE** | LOCKED-STRAP | 10 k pull-up + BOOT button |
| 36 | **BOOT_STRAP_HIGH** | LOCKED-STRAP | 10 k pull-up |
| 37 | **UART0_TX** | LOCKED-STRAP | recovery/debug |
| 38 | **UART0_RX** | LOCKED-STRAP | recovery/debug |
| 39 | **SDMMC_D0** | LOCKED | microSD slot 0 |
| 40 | **SDMMC_D1** | LOCKED | microSD slot 0 |
| 41 | **SDMMC_D2** | LOCKED | microSD slot 0 |
| 42 | **SDMMC_D3** | LOCKED | microSD slot 0 |
| 43 | **SDMMC_CLK** | LOCKED | microSD slot 0 |
| 44 | **SDMMC_CMD** | LOCKED | microSD slot 0 |
| 45 | **SD_PWR_EN** | LOCK-CANDIDATE | TPS22918 microSD power-cycle |
| 46 | **SD_CARD_DETECT** | LOCK-CANDIDATE/OPTIONAL | only if selected socket provides CD switch |
| 47 | Spare | FREE | future |
| 48 | Spare | FREE | old ES8311 DIN removed |
| 49 | **DAC_XSMT** | LOCK-CANDIDATE | PCM5102A deterministic mute |
| 50 | **PCM5102A_BCLK** | LOCKED | bench-proven |
| 51 | **PCM5102A_DATA** | LOCKED | bench-proven |
| 52 | **PCM5102A_LRCK** | LOCKED | bench-proven |
| 53 | **SYS_POWER_ALERT_N** | LOCK-CANDIDATE/OPTIONAL | INA238 ALERT if populated |
| 54 | **C6_RESET / EN** | LOCKED | ESP-Hosted reset |

---

## 3. Dedicated non-GPIO interfaces

### USB0 High-Speed

Dedicated P4 HS PHY provides USB DM/DP and does not consume GPIO26/27.

### MIPI DSI

Dedicated DSI PHY:

```text
DSI CLK P/N
DSI DATA0 P/N
DSI DATA1 P/N
DSI_REXT
VDD_MIPI_DPHY
```

The final DSI506 connector exposes both data lanes. M1 routes both lanes, while the initial accepted firmware profile uses lane0 + clock at 800 Mbps.

---

## 4. Final display GPIO contract

M3 bench evidence for the same physical display locks:

```text
GPIO7 -> DSI506 J2 pin 12 SDA
GPIO8 -> DSI506 J2 pin 11 SCL
I2C = 100 kHz
0x38 = FT5426/FT5x06 touch
0x45 = panel power/backlight controller
```

There are no host wires for reset, touch interrupt, TE or factory external PWM on the 15-pin interface.

Released by M1-ELEC-B0:

```text
GPIO3
GPIO4
GPIO5
GPIO6
GPIO23
```

Do not reassign these released GPIOs until the rest of the board allocation is reviewed; `FREE` means electrically available, not automatically safe for arbitrary new features.

---

## 5. USB power mapping

```text
GPIO20 -> USB0_PWR_EN
GPIO21 <- USB0_FAULT_N
GPIO22 -> USB1_PWR_EN
GPIO32 <- USB1_FAULT_N
```

All EN lines retain hardware pulldowns so ports are off during P4 reset.

---

## 6. Service interfaces

```text
UART0 TX GPIO37
UART0 RX GPIO38
USB Serial/JTAG DM GPIO24
USB Serial/JTAG DP GPIO25
```

GPIO24/25 stay reserved for the factory pogo path; USB1 FS therefore remains GPIO26/27.

---

## 7. Strapping policy

Reserved strap group remains GPIO34..38. Do not add large capacitance or low-impedance external loads that alter reset sampling.

---

## 8. Spare pool after display migration

Clean spare candidates now include:

```text
GPIO2
GPIO3
GPIO4
GPIO5
GPIO6
GPIO9
GPIO10
GPIO11
GPIO12
GPIO13
GPIO23
GPIO33
GPIO47
GPIO48
```

Optional-function pins GPIO46/53 are not counted as unconditional spares.

---

## 9. Firmware rule

The future `bsp_pajoniiir_m1` must not inherit JC4880 assumptions for:

- GT911 address/reset/interrupt,
- ST7701S panel reset/TE,
- GPIO23 MP3202 PWM,
- 480x800 portrait timing.

It should start from the DSI506 contract captured in `Pajoniiir_M1_ELEC_B0_5in_DSI_Interface_Migration_v0.1.md` while retaining M1-specific USB/audio/power mappings from this file.
