# Pajoniiir Mainboard — Global GPIO Allocation v0.1

**Projekt:** Pajoniiir-M1 Rev A  
**MCU:** ESP32-P4 v3.x / ESP32-P4NRW32X candidate  
**Datum:** 2026-09-02  
**Status:** Pre-schematic global pin lock candidate

---

# 1. Svrha

Ovaj dokument je centralni izvor istine za GPIO raspodjelu nove Pajoniiir-M1 ploče.

Razlog za uvođenje globalnog audita sada:

- originalna Guition ploča ima legacy funkcije koje više ne koristimo
- neki community/vendor firmware koristi GPIO21/22 za GT911 RST/INT
- novi USB power blok treba četiri GPIO-a
- audio dobiva zaseban XSMT mute GPIO
- želimo sačuvati P4 USB Serial/JTAG service path
- strapping pinovi ne smiju biti slučajno opterećeni

Ovaj dokument ima prednost nad starim JC4880 pinoutom za novu Pajoniiir-M1 ploču.

---

# 2. Zaključani / kandidat GPIO-i

| GPIO | Pajoniiir-M1 funkcija | Status | Napomena |
|---:|---|---|---|
| 0 | Reserved / future LP | FREE-RESERVED | ne koristimo 32.768 kHz crystal u Rev A |
| 1 | Reserved / future LP | FREE-RESERVED | ne koristimo 32.768 kHz crystal u Rev A |
| 2 | Spare | FREE | test/aux candidate |
| 3 | **TOUCH_RST** | LOCK-CANDIDATE | novi custom-board mapping |
| 4 | **TOUCH_INT** | LOCK-CANDIDATE | novi custom-board mapping |
| 5 | **LCD_RST** | LOCKED | postojeći firmware |
| 6 | **LCD_TE** | LOCK-CANDIDATE/DNP | panel tearing-event; optional 0 Ω connection |
| 7 | **I2C_SDA / GT911** | LOCKED | postojeći firmware |
| 8 | **I2C_SCL / GT911** | LOCKED | postojeći firmware |
| 9 | Spare | FREE | stari ES8311 DOUT uklonjen |
| 10 | Spare | FREE | stari ES8311 LRCK uklonjen |
| 11 | Spare | FREE | stari speaker PA uklonjen |
| 12 | Spare | FREE | stari ES8311 BCLK uklonjen |
| 13 | Spare | FREE | stari ES8311 MCLK uklonjen |
| 14 | **C6_SDIO_D0** | LOCKED | ESP-Hosted |
| 15 | **C6_SDIO_D1** | LOCKED | ESP-Hosted |
| 16 | **C6_SDIO_D2** | LOCKED | ESP-Hosted |
| 17 | **C6_SDIO_D3** | LOCKED | ESP-Hosted |
| 18 | **C6_SDIO_CLK** | LOCKED | ESP-Hosted |
| 19 | **C6_SDIO_CMD** | LOCKED | ESP-Hosted |
| 20 | **USB0_PWR_EN** | LOCK-CANDIDATE | TPS25221 USB0 |
| 21 | **USB0_FAULT_N** | LOCK-CANDIDATE | TPS25221 USB0 |
| 22 | **USB1_PWR_EN** | LOCK-CANDIDATE | TPS25221 USB1 |
| 23 | **LCD_BL_PWM** | LOCKED | postojeći firmware |
| 24 | **P4_USB_SERIAL_JTAG_DM** | RESERVED | factory/service |
| 25 | **P4_USB_SERIAL_JTAG_DP** | RESERVED | factory/service |
| 26 | **USB1_FS_DM** | LOCK-CANDIDATE | DDJ-FLX4 |
| 27 | **USB1_FS_DP** | LOCK-CANDIDATE | DDJ-FLX4 |
| 28 | Spare / future Ethernet group | FREE-RESERVED | ne koristiti bez reviewa |
| 29 | Spare / future Ethernet group | FREE-RESERVED | ne koristiti bez reviewa |
| 30 | Spare / future Ethernet group | FREE-RESERVED | ne koristiti bez reviewa |
| 31 | Spare / future Ethernet group | FREE-RESERVED | ne koristiti bez reviewa |
| 32 | **USB1_FAULT_N** | LOCK-CANDIDATE | TPS25221 USB1 |
| 33 | Spare | FREE | RMII TXEN alternative; Ethernet nije Rev A cilj |
| 34 | Strapping / spare | RESERVED-STRAP | ne opterećivati pri bootu |
| 35 | **BOOT_MODE** | LOCKED-STRAP | 10k pull-up + BOOT button |
| 36 | **BOOT_STRAP_HIGH** | LOCKED-STRAP | 10k pull-up |
| 37 | **UART0_TX** | LOCKED-STRAP | recovery/debug |
| 38 | **UART0_RX** | LOCKED-STRAP | recovery/debug |
| 39 | **SDMMC_D0** | LOCKED | microSD slot 0 |
| 40 | **SDMMC_D1** | LOCKED | microSD slot 0 |
| 41 | **SDMMC_D2** | LOCKED | microSD slot 0 |
| 42 | **SDMMC_D3** | LOCKED | microSD slot 0 |
| 43 | **SDMMC_CLK** | LOCKED | microSD slot 0 |
| 44 | **SDMMC_CMD** | LOCKED | microSD slot 0 |
| 45 | SD_PWR_EN candidate | RESERVED | optional microSD power-cycle |
| 46 | Spare | FREE | future |
| 47 | Spare | FREE | future |
| 48 | Spare | FREE | old ES8311 DIN removed |
| 49 | **DAC_XSMT** | LOCK-CANDIDATE | PCM5102A deterministic mute |
| 50 | **PCM5102A_BCLK** | LOCKED | bench-proven |
| 51 | **PCM5102A_DATA** | LOCKED | bench-proven |
| 52 | **PCM5102A_LRCK** | LOCKED | bench-proven |
| 53 | Spare | FREE | ADC/debug candidate |
| 54 | **C6_RESET / EN** | LOCKED | ESP-Hosted reset |

---

# 3. Dedicated non-GPIO interfaces

Sljedeće funkcije ne troše standardne GPIO-matrix pinove na način prikazan gore.

## USB0 High-Speed

Dedicated P4 HS PHY:

- physical USB_DM
- physical USB_DP
- VDD_USBPHY

USB0 nije mapiran na GPIO26/27.

## MIPI DSI

Dedicated DSI PHY:

- DSI CLK P/N
- DSI DATA0 P/N
- DSI DATA1 P/N
- DSI_REXT
- VDD_MIPI_DPHY

MIPI data lanes nisu obični GPIO-i.

---

# 4. Touch mapping odluka

Originalni JC4880 hardware/community dokumenti navode GPIO22/GPIO21 za GT911 RST/INT u jednom firmware pathu.

Međutim, aktivni Pajoniiir firmware danas koristi:

~~~text
rst_gpio_num = GPIO_NUM_NC
int_gpio_num = GPIO_NUM_NC
~~~

i radi pollingom.

Zato custom-board Rev A smije odabrati nove pinove.

Nova odluka:

~~~text
GPIO3 -> TOUCH_RST
GPIO4 -> TOUCH_INT
GPIO7 -> TOUCH_SDA
GPIO8 -> TOUCH_SCL
~~~

Prednosti:

- USB power GPIO21/22 ostaju dostupni
- touch dobiva stvarni hardware reset
- touch dobiva interrupt-driven opciju
- nema strapping konflikta
- GPIO3/4 su inače slobodni u aktivnoj Pajoniiir arhitekturi

Firmware migration mora ažurirati board support layer za novi M1 target.

---

# 5. USB power mapping

~~~text
GPIO20 -> USB0_PWR_EN
GPIO21 <- USB0_FAULT_N
GPIO22 -> USB1_PWR_EN
GPIO32 <- USB1_FAULT_N
~~~

Svi EN imaju hardware pulldown, pa su portovi OFF tijekom resetiranja P4.

FAULT signali imaju external pull-up na 3V3.

---

# 6. Service interfaces preserved

## UART0

~~~text
GPIO37 TX
GPIO38 RX
~~~

Primary recovery.

## USB Serial/JTAG

~~~text
GPIO24 DM
GPIO25 DP
~~~

Reserved for factory/service pogo interface.

Ovo je razlog zašto USB1 FS koristi GPIO26/27.

---

# 7. Strapping policy

Strapping pinovi:

- GPIO34
- GPIO35
- GPIO36
- GPIO37
- GPIO38

Pravila:

- GPIO35 = explicit 10k pull-up; BOOT button to GND
- GPIO36 = explicit 10k pull-up
- GPIO37/38 samo UART series 33R i high-impedance service tool tijekom reset samplinga
- GPIO34 ne koristiti u Rev A bez posebnog razloga
- nema velikih capacitors na strap pinovima

---

# 8. Ethernet reservation policy

ESP32-P4 RMII može koristiti dio GPIO28-36/39-54 ovisno o muxu.

Pajoniiir Rev A **nema Ethernet PHY**.

Ipak GPIO28-31 ostavljamo kao FREE-RESERVED kako bi budući M2/Rev B mogao lakše dodati Ethernet ako postane proizvodni zahtjev.

GPIO32 je potrošen za USB1_FAULT_N; to bi se u Ethernet reviziji moglo remapirati na drugi slobodan GPIO.

---

# 9. Legacy Guition functions removed

Sljedeći stari GPIO ownership više ne postoji:

- GPIO9 ES8311 DOUT
- GPIO10 ES8311 LRCK
- GPIO11 speaker PA
- GPIO12 ES8311 BCLK
- GPIO13 ES8311 MCLK
- GPIO48 ES8311 DIN
- GPIO26/27 RS485
- GPIO49-52 RMII development-board routing

Na Pajoniiir-M1 custom PCB-u ti signali pripadaju novoj arhitekturi prema ovoj tablici.

---

# 10. Spare GPIO pool

Najčišći spare pool nakon trenutnog locka:

~~~text
GPIO2
GPIO9
GPIO10
GPIO11
GPIO12
GPIO13
GPIO33
GPIO46
GPIO47
GPIO48
GPIO53
~~~

Restricted/reserved spares:

~~~text
GPIO0/1  LP/RTC related
GPIO28-31 future Ethernet
GPIO34   strap
GPIO45   SD power candidate
~~~

---

# 11. Firmware board target requirement

Nova ploča ne smije nastaviti koristiti naziv/semantiku `bsp_jc4880` kao konačni proizvodni target.

Predloženo:

~~~text
components/bsp_pajoniiir_m1/
~~~

Novi BSP treba imati centralni header:

~~~text
BSP_LCD_RST_GPIO       5
BSP_LCD_BL_GPIO        23
BSP_LCD_TE_GPIO        6
BSP_I2C_SDA_GPIO       7
BSP_I2C_SCL_GPIO       8
BSP_TOUCH_RST_GPIO     3
BSP_TOUCH_INT_GPIO     4

BSP_C6_CLK_GPIO        18
BSP_C6_CMD_GPIO        19
BSP_C6_D0_GPIO         14
BSP_C6_D1_GPIO         15
BSP_C6_D2_GPIO         16
BSP_C6_D3_GPIO         17
BSP_C6_RESET_GPIO      54

BSP_USB0_PWR_EN_GPIO   20
BSP_USB0_FAULT_GPIO    21
BSP_USB1_PWR_EN_GPIO   22
BSP_USB1_FAULT_GPIO    32

BSP_PCM5102_BCLK_GPIO  50
BSP_PCM5102_WS_GPIO    52
BSP_PCM5102_DOUT_GPIO  51
BSP_PCM5102_XSMT_GPIO  49
~~~

---

# 12. Pre-layout lock checklist

- [ ] full v3.x P4 symbol pin review
- [ ] MIPI dedicated pins confirmed
- [ ] USB HS dedicated pins confirmed
- [ ] USB FS GPIO26/27 confirmed
- [ ] USB Serial/JTAG GPIO24/25 preserved
- [ ] GPIO3/4 available in selected power domain at 3.3V
- [ ] GPIO20/21/22/32 do not conflict with final peripheral mux
- [ ] GPIO49 XSMT does not conflict with any retained function
- [ ] all strapping pin external states reviewed
- [ ] firmware `bsp_pajoniiir_m1` matches this table exactly

---

# 13. Zaključak

Globalna Rev A raspodjela sada uklanja otkriveni touch/USB konflikt.

Ključne nove odluke:

~~~text
TOUCH:
GPIO3 RESET
GPIO4 INT
GPIO7 SDA
GPIO8 SCL

USB POWER:
GPIO20 USB0 EN
GPIO21 USB0 FAULT
GPIO22 USB1 EN
GPIO32 USB1 FAULT

AUDIO:
GPIO49 XSMT
GPIO50 BCLK
GPIO51 DATA
GPIO52 LRCK

SERVICE:
GPIO24/25 USB Serial/JTAG
GPIO37/38 UART0
~~~

Ovaj dokument treba provjeriti prije svakog budućeg dodavanja GPIO funkcije.
