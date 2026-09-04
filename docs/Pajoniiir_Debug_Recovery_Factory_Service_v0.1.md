# Pajoniiir Mainboard — Debug, Recovery & Factory Service Design v0.1

**Projekt:** Pajoniiir BL-A1800 / Pajoniiir-M1  
**Ploča:** Pajoniiir Mainboard Rev A  
**Blok:** 13_DEBUG_SERVICE  
**Datum:** 2026-09-02  
**Status:** Captured in KiCad; service architecture and J9 factory-pogo footprint locked

---

# 1. Cilj

Rev A mora biti recoverable čak kada ne rade application firmware, Wi-Fi / ESP-Hosted, USB0 storage, USB1 FLX4, display ili microSD.

Zato Pajoniiir-M1 dobiva više neovisnih servisnih puteva.

---

# 2. Recovery hierarchy

1. **P4 UART0** — najrobustniji recovery/download
2. **P4 USB Serial/JTAG** — factory/debug bez USB-UART bridgea
3. **C6 UART0 + boot straps** — direktni C6 recovery
4. RESET/BOOT pogo access
5. test-point railovi

Ni jedan recovery path ne smije ovisiti o glavnom LCD-u ili mreži.

---

# 3. P4 UART0

ESP32-P4 default UART0:

~~~text
GPIO37 = TX
GPIO38 = RX
~~~

Oba su strapping pinovi, pa ih se ne smije agresivno opteretiti tijekom boot sampling intervala.

Rev A:

~~~text
GPIO37 -- 33R --> P4_UART0_TX
GPIO38 -- 33R --> P4_UART0_RX
~~~

Bez velikih capacitors.

---

# 4. P4 BOOT / RESET

Servis mora imati pristup:

~~~text
P4_CHIP_PU
P4_BOOT_GPIO35
P4_BOOT_GPIO36
~~~

Normalno:

- GPIO35 = 10 kΩ pull-up
- GPIO36 = 10 kΩ pull-up

Download:

- GPIO35 LOW
- GPIO36 HIGH
- reset / CHIP_PU cycle

---

# 5. P4 USB Serial/JTAG

Aktualni Espressif P4 hardware guide potvrđuje:

~~~text
GPIO24 = USB Serial/JTAG D-
GPIO25 = USB Serial/JTAG D+
~~~

Pajoniiir namjerno čuva ova dva GPIO-a jer USB1 koristi GPIO26/27.

To omogućuje USB download boot, serial console, JTAG debugging i production programming bez posebnog USB-UART bridge IC-a.

---

# 6. USB Serial/JTAG signal conditioning

Kao i drugi P4 Full-Speed USB path:

~~~text
GPIO24 DM -- 22R -- service pads
GPIO25 DP -- 22R -- service pads
~~~

Optional DNP shunt capacitors:

- C_P4_USBJTAG_DM = DNP
- C_P4_USBJTAG_DP = DNP

Ovaj interface može završiti na factory pogo footprintu; ne mora imati user-facing USB connector.

---

# 7. P4 Tag-Connect / pogo connector

Primary service footprint:

**TC2030-NL-FP class, 6-pin no-parts footprint**

Tag-Connect footprint nije populirani BOM dio.

Predloženi Pajoniiir assignment:

| Pin | Signal |
|---:|---|
| 1 | 3V3_SYS sense/VREF |
| 2 | P4_UART0_TX |
| 3 | P4_UART0_RX |
| 4 | P4_CHIP_PU |
| 5 | GND |
| 6 | P4_BOOT_GPIO35 |

GPIO36 je hard-pulled HIGH pa ga ne moramo trošiti na 6-pin interface.

Uz connector ipak staviti zaseban TP_GPIO36.

---

# 8. P4 USB Serial/JTAG pogo

Za USB Serial/JTAG koristi se zaseban mali 4-pad/5-pad fixture footprint:

~~~text
3V3_SYS VREF
GND
USBJTAG_DM
USBJTAG_DP
optional CHIP_PU
~~~

Ne spajati VBUS s programatora direktno na 5V_SYS bez definirane politike.

Factory fixture u pravilu koristi board vlastito napajanje, a 3V3 je samo reference/sense.

---

# 9. C6 direct recovery

C6 test access:

~~~text
C6_UART_TX
C6_UART_RX
C6_EN
C6_GPIO8
C6_GPIO9
3V3_C6
GND
~~~

Minimalni 6-pin pogo assignment:

| Pin | Signal |
|---:|---|
| 1 | 3V3_C6 VREF |
| 2 | C6_UART_TX |
| 3 | C6_UART_RX |
| 4 | C6_EN |
| 5 | GND |
| 6 | C6_GPIO9_BOOT |

GPIO8 ima hard 10 kΩ pull-up pa Joint Download zahtijeva samo GPIO9 LOW + EN reset.

---

# 10. Separate P4 and C6 fixtures

Ne pokušavati stisnuti P4 i C6 recovery u isti 6-pin connector.

Razlozi:

- smanjuje grešku u proizvodnji
- oba procesora se mogu servisirati neovisno
- jednostavniji fixture
- jasniji silkscreen

Naming:

~~~text
JDBG_P4
JDBG_C6
~~~

---

# 11. Silkscreen

Na bare PCB-u jasno označiti:

~~~text
P4 DBG
C6 DBG
BOOT
RST
3V3
5V
GND
~~~

Pin 1 na Tag-Connect footprintu jasno obilježiti.

---

# 12. Service power policy

Factory programmer ne smije slučajno napajati board kroz signalni VREF.

VREF pinovi služe kao **sense/reference only**.

Ako je potreban fixture power input, koristiti zaseban FACTORY_5V_IN kroz definirani power path ili glavni 5 V input connector.

---

# 13. Manual RESET / BOOT access

Rev A engineering board treba fizičke tipke:

- SW_RESET
- SW_BOOT

Finalni production enclosure može ih sakriti iza service holea ili ih kasnije ukloniti iz user accessa.

Footprintove na Rev A zadržati.

---

# 14. Console strategy

P4 primary console tijekom bring-upa: **UART0**.

Kasnije production firmware može koristiti USB Serial/JTAG console, ali UART ostaje hard recovery.

C6 primary recovery console: **UART0 direct pads**.

ESP-Hosted logs preko P4 nisu dovoljan recovery path.

---

# 15. JTAG

P4 USB Serial/JTAG je primarni low-BOM debug path.

Ako budući hard debugging zatraži dedicated external JTAG pins/debugger, Rev A ima dovoljno spare GPIO-a, ali ne treba sada trošiti PCB prostor i pinove bez potrebe.

---

# 16. Logic-level policy

Svi P4 i C6 servisni UART signali:

**3.3 V logic**

Ne priključivati RS-232 voltage-level adapter.

Fixture mora koristiti 3.3 V TTL UART.

---

# 17. UART ESD

Debug pads su interni/factory access.

Default: **nema zasebne ESD diode**.

Ako finalni enclosure izvede debug header van korisniku, protection se mora ponovno definirati.

---

# 18. Test point set

P4:

- TP_P4_UART_TX
- TP_P4_UART_RX
- TP_P4_BOOT35
- TP_P4_BOOT36
- TP_CHIP_PU
- TP_USBJTAG_DM
- TP_USBJTAG_DP

C6:

- TP_C6_UART_TX
- TP_C6_UART_RX
- TP_C6_EN
- TP_C6_GPIO8
- TP_C6_GPIO9

Power:

- TP_5V_SYS
- TP_3V3_SYS
- TP_P4_VDD_HP
- TP_3V3_C6
- GND test loops

---

# 19. Factory programming flow

## P4

1. power board from qualified 5 V source
2. fixture detects 3V3 VREF
3. force GPIO35 LOW
4. pulse CHIP_PU
5. flash bootloader/partition/app
6. verify flash
7. reset normal boot
8. read serial number / test firmware

## C6

1. ensure 3V3_C6 valid
2. force GPIO9 LOW
3. pulse C6_EN
4. flash ESP-Hosted slave image
5. release GPIO9
6. reset
7. verify C6 UART boot
8. run P4↔C6 SDIO self-test

---

# 20. Production test firmware

Rev A treba imati dedicated factory-test app/mode koji može provjeriti rail health, PSRAM, flash, C6, Wi-Fi, microSD, USB0, USB1, PCM5102A tone, LCD, touch, buttons i FAULT pinove.

Rezultat treba biti machine-readable preko UART/USB console.

---

# 21. Fixture detection

Fixture treba čitati board identification iz firmwarea.

Ne uvoditi dodatni EEPROM ili trošiti GPIO samo za Rev A board ID.

Board revision se može kodirati kroz:

- firmware board ID
- PCB silkscreen
- manufacturing database

---

# 22. Preliminary BOM / footprints

| RefDes | Qty | Item | Status |
|---|---:|---|---|
| JDBG_P4 | 1 | TC2030-NL-FP class | PCB footprint only, DNL |
| JDBG_C6 | 1 | TC2030-NL-FP class | PCB footprint only, DNL |
| JDBG_USB | 1 | 4/5-pad pogo footprint | PCB-only |
| R_UART_P4_TX | 1 | 33 Ω | required |
| R_UART_P4_RX | 1 | 33 Ω | required |
| R_USBJTAG_DM | 1 | 22 Ω | candidate |
| R_USBJTAG_DP | 1 | 22 Ω | candidate |
| C_USBJTAG_DM | 1 | DNP | tuning |
| C_USBJTAG_DP | 1 | DNP | tuning |
| SW_RESET | 1 | momentary NO | Rev A |
| SW_BOOT | 1 | momentary NO | Rev A |

---

# 23. Acceptance criteria

- P4 recoverable with application flash erased
- C6 recoverable with corrupt ESP-Hosted image
- UART boot logs stable
- USB Serial/JTAG enumerates independently of USB1
- fixture cannot back-power board through VREF
- BOOT/RESET sequence repeatable 100/100
- no strapping failures with debug cable attached
- no permanent debug connector required for production unit

---

# 24. Zaključak

Rev A dobiva tri nezavisna servisna puta:

~~~text
P4 UART0:
GPIO37 / GPIO38
Tag-Connect/pogo
BOOT + RESET

P4 USB Serial/JTAG:
GPIO24 / GPIO25
factory pogo

C6 direct UART:
UART0 + GPIO9 + EN
separate pogo
~~~

Time board ostaje servisabilan čak i kod potpunog firmware failurea.

**Sljedeći blok:** 14_TEST_MONITORING — 5V_SYS current/voltage telemetry, optional INA238, shunt, ALERT i DNP strategy.
