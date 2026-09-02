# Pajoniiir-M1 — Hardware / Firmware Contract v0.1

**Projekt:** Pajoniiir-M1 Rev A  
**Datum:** 2026-09-02  
**Status:** Pre-bring-up firmware contract for the custom PCB

---

# 1. Purpose

This document defines every hardware behavior that the M1 firmware must explicitly support.

The custom M1 PCB is not just a JC4880 pin-compatible clone.

Firmware must understand:

- ESP32-P4 v3.x silicon
- independent USB VBUS switches
- PCM5102A XSMT
- controlled microSD power
- explicit GT911 reset/interrupt
- 1 kHz direct-EN backlight PWM
- optional system power monitor
- M1-specific recovery/test interfaces

---

# 2. New board target

Create a dedicated board target:

~~~text
bsp_pajoniiir_m1
~~~

Do not replace the existing JC4880 BSP.

Recommended structure:

~~~text
firmware/main-deck-p4/
  components/
    bsp_jc4880/
    bsp_pajoniiir_m1/

  sdkconfig.defaults.jc4880
  sdkconfig.defaults.m1
~~~

Application/UI/audio/library code should remain shared where practical.

---

# 3. Silicon revision contract

M1 hardware:

~~~text
ESP32-P4NRW32X
target silicon v3.2+
~~~

M1 build must not use:

~~~text
CONFIG_ESP32P4_SELECTS_REV_LESS_V3=y
~~~

Required concept:

~~~text
CONFIG_ESP32P4_SELECTS_REV_LESS_V3=n
~~~

or equivalent current ESP-IDF configuration.

The JC4880 v1.3 and M1 v3.x binaries are separate build artifacts.

---

# 4. Board GPIO contract

~~~text
GPIO3   TOUCH_RST
GPIO4   TOUCH_INT
GPIO5   LCD_RST
GPIO6   LCD_TE optional
GPIO7   I2C_SDA
GPIO8   I2C_SCL

GPIO14  C6_SDIO_D0
GPIO15  C6_SDIO_D1
GPIO16  C6_SDIO_D2
GPIO17  C6_SDIO_D3
GPIO18  C6_SDIO_CLK
GPIO19  C6_SDIO_CMD

GPIO20  USB0_PWR_EN
GPIO21  USB0_FAULT_N
GPIO22  USB1_PWR_EN
GPIO23  LCD_BL_PWM

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
~~~

No M1 driver should silently use one of these pins for a legacy JC4880 function.

---

# 5. Backlight contract

M1 electrical path:

~~~text
GPIO23 -> 0R -> MP3202 EN
EN -> 10k -> GND
~~~

M1 PWM target:

**1 kHz**

not the current JC4880-derived 5 kHz value.

Proposed define:

~~~text
BSP_LCD_BL_PWM_FREQ_HZ 1000
~~~

Brightness:

- 0% = EN held low / backlight off
- 1–100% = PWM duty
- backlight stays 0 until panel init completes

The old JC4880 BSP may keep its current behavior independently.

---

# 6. Touch startup contract

M1 touch:

~~~text
SDA = GPIO7
SCL = GPIO8
RST = GPIO3
INT = GPIO4
address target = 0x5D
~~~

Startup:

1. configure INT as output LOW
2. assert RST LOW
3. wait >=1 ms conservative
4. release RST HIGH
5. wait >=10 ms
6. release INT into high-impedance input
7. no internal pull-up/down on INT
8. probe 0x5D
9. if desired, probe 0x14 only as diagnostic fallback

Normal mode:

- interrupt-driven preferred
- polling fallback retained for diagnostics

ISR should only notify a task; I2C transaction occurs outside ISR.

---

# 7. USB VBUS contract

Both ports default hardware OFF through EN pulldowns.

Firmware must not assume VBUS exists at app start.

## USB0

~~~text
EN     GPIO20
FAULT  GPIO21 active-low
~~~

## USB1

~~~text
EN     GPIO22
FAULT  GPIO32 active-low
~~~

Startup sequence:

1. USB host stack initialized
2. set USB0 EN high
3. wait VBUS settle
4. enumerate storage
5. set USB1 EN high
6. wait VBUS settle
7. enumerate FLX4

Staggering avoids simultaneous inrush.

---

# 8. USB fault recovery

Each port is independently recoverable.

Pseudo-flow:

~~~text
on USBx_FAULT_N low:
    log fault
    stop owner traffic
    disable USBx power
    wait recovery delay
    enable USBx power
    re-enumerate
~~~

Do not reboot P4 as first recovery action.

Fault counters belong in diagnostics.

---

# 9. USB0 contract

USB0 is the P4 dedicated High-Speed root.

Role:

~~~text
Rekordbox media storage
~~~

Firmware must verify/log negotiated speed.

A High-Speed-capable stick unexpectedly enumerating only at Full-Speed should be diagnostic evidence, not silently ignored during EVT.

---

# 10. USB1 contract

USB1 uses:

~~~text
GPIO26 D-
GPIO27 D+
~~~

Role:

- FLX4 MIDI IN/OUT
- controller LED feedback
- 4-channel UAC
- cue channels 3/4

GPIO24/25 are not available for USB1 because they are reserved for USB Serial/JTAG service.

---

# 11. PCM5102A contract

~~~text
GPIO50 BCLK
GPIO52 LRCK
GPIO51 DATA
GPIO49 XSMT
MCLK unused
~~~

Boot:

1. GPIO49 output LOW immediately
2. init audio engine
3. start BCLK/LRCK/DATA
4. wait for stable clock/PLL
5. optional software volume ramp
6. GPIO49 HIGH

Shutdown/reboot:

1. GPIO49 LOW
2. wait >=3 ms
3. stop I2S
4. continue reboot/power-down

Any audio subsystem reset should mute hardware first.

---

# 12. microSD power contract

~~~text
GPIO45 SD_PWR_EN
GPIO46 SD_CARD_DETECT optional
~~~

Card power is OFF after hardware reset.

Init:

1. put SD bus pins in safe state
2. GPIO45 HIGH
3. wait 3V3_SD settle
4. configure SDMMC0
5. init card
6. mount

Power-cycle recovery:

1. stop file I/O
2. unmount
3. deinit SDMMC
4. GPIO39–44 high-Z
5. GPIO45 LOW
6. wait >=20 ms; 100 ms fallback
7. GPIO45 HIGH
8. wait settle
9. reinit/mount

Never drive a powered-off card HIGH through signal pins.

---

# 13. C6 contract

P4 host SDIO:

~~~text
CLK GPIO18
CMD GPIO19
D0  GPIO14
D1  GPIO15
D2  GPIO16
D3  GPIO17
RESET GPIO54
~~~

Baseline:

- 4-bit
- bring-up at reduced frequency if needed
- production target 40 MHz after validation

C6 reset is independently available and should be used before rebooting the P4 when Wi-Fi coprocessor recovery is possible.

---

# 14. Display / MIPI contract

Baseline remains:

~~~text
480x800 native
2 DSI lanes
500 Mbps/lane
RGB565
DPI 34 MHz
PPA rotation to 800x480
~~~

Startup:

1. enable/configure P4 internal DPHY LDO to 2.5 V
2. set backlight 0
3. create DSI
4. reset/init ST7701S
5. create DPI/framebuffer
6. UI ready
7. ramp backlight

Optional GPIO6 TE should remain disabled unless the final panel pin mapping is confirmed and the feature is intentionally enabled.

---

# 15. Power-monitor contract

If INA238 is populated:

~~~text
I2C address 0x40
ALERT GPIO53
~~~

If not populated:

- firmware must tolerate NACK at 0x40
- GPIO53 remains free/unused
- absence is not a boot error

Board capability detection can be compile-time or runtime.

---

# 16. Power-event diagnostics

Recommended structured event:

~~~text
timestamp
5V_SYS_mV
system_mA
system_mW
USB0_EN
USB0_FAULT
USB1_EN
USB1_FAULT
SD_PWR
C6_state
backlight_percent
audio_state
reset_reason
~~~

Keep bounded recent-event history for crash/soak debugging.

---

# 17. Factory-test mode

M1 firmware should implement a factory/self-test mode reachable without the GUI.

Minimum sequence:

1. identify chip revision
2. verify 32 MB PSRAM
3. verify 16 MB flash
4. verify 5V/3V3/core rails where telemetry exists
5. test C6 reset + SDIO
6. test Wi-Fi
7. power and enumerate USB0
8. power and enumerate USB1 / FLX4 if fixture available
9. microSD power-cycle + read/write
10. PCM5102A test tone
11. LCD pattern
12. touch grid
13. test USB FAULT inputs
14. print machine-readable PASS/FAIL

---

# 18. Build identity

Every M1 image should expose:

~~~text
PRODUCT=Pajoniiir
BOARD=Pajoniiir-M1
PCB_REV=RevA
P4_FAMILY=ESP32-P4NRW32X
HW_PROFILE=M1
~~~

This must appear in:

- boot log
- web diagnostics
- factory report
- crash report

---

# 19. M1-specific compile-time sanity checks

Recommended compile-time checks:

- USB0 EN != USB1 EN
- USB FAULT pins do not collide
- PCM5102A pins do not collide
- touch pins do not collide with USB power
- C6 SDIO matches expected M1 mapping
- SDMMC0 mapping is fixed 39–44
- legacy ES8311 path disabled
- legacy speaker PA disabled
- old pre-v3 silicon selector disabled

Fail the build rather than silently accepting an invalid board pin map.

---

# 20. Legacy features explicitly off on M1

M1 firmware must not initialize:

- ES8311
- NS4150 speaker amp
- analog microphone
- RS485
- camera
- S3 link
- battery/IP5306
- old monitor-link I2S

This reduces boot time, power use and accidental GPIO ownership conflicts.

---

# 21. Bring-up stages

## M1-BRINGUP-0

UART + chip revision + flash + PSRAM.

## M1-BRINGUP-1

3V3/core rails + reset/boot stability.

## M1-BRINGUP-2

display + backlight + touch.

## M1-BRINGUP-3

microSD power/recovery.

## M1-BRINGUP-4

PCM5102A.

## M1-BRINGUP-5

C6 SDIO/Wi-Fi.

## M1-BRINGUP-6

USB0 storage.

## M1-BRINGUP-7

USB1 FLX4 MIDI/UAC.

## M1-BRINGUP-8

combined multi-hour soak.

---

# 22. Definition of Done

Hardware/firmware contract is satisfied when:

- M1 has its own BSP
- v3.x build boots
- GPIO map exactly matches the hardware authority document
- 1 kHz backlight control verified
- GT911 deterministic 0x5D startup verified
- each USB VBUS can be independently power-cycled
- USB fault handling works
- microSD hardware power-cycle works
- PCM5102A boot/shutdown mute works
- C6 reset/recovery works
- optional INA238 absence/presence both supported
- all legacy JC4880-only hardware is disabled on M1
