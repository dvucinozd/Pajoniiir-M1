# Pajoniiir Mainboard — USB0 High-Speed Storage Design v0.1

> **Post-capture update (2026-09-04):** J2 is locked to Amphenol 87520-1010ALF with project footprint `Pajoniiir-M1:Amphenol_87520-1010ALF`. The remaining gate is final top-wall cutout, insertion and mated-cable geometry.

**Projekt:** Pajoniiir-M1 Rev A  
**Blok:** 07_USB0_STORAGE  
**Namjena:** Rekordbox USB mass-storage host  
**Datum:** 2026-09-02

---

# 1. Funkcija

USB0 je namjenski **USB 2.0 High-Speed host** za Rekordbox media storage.

P4 koristi svoj dedicated High-Speed OTG PHY:

- physical P4 pin 49 = USB_DM
- physical P4 pin 50 = USB_DP
- VDD_USBPHY = 3.3 V domain

USB0 je fiksni host. Zato koristimo USB-A female konektor i nemamo USB-C CC/role logiku.

---

# 2. Signal chain

~~~text
ESP32-P4 USB2 HS PHY
    DM / DP
       |
  0R tuning footprints
       |
 TPD2EUSB30A
       |
 USB-A receptacle
       |
 Rekordbox USB stick
~~~

VBUS dolazi isključivo iz USB0 TPS25221 power switcha.

---

# 3. Net names

- USB0_HS_DM
- USB0_HS_DP
- USB0_VBUS
- USB0_SHIELD
- GND

Ne koristiti generičke D+/D- netove između više portova.

---

# 4. P4 pins

Dedicated HS PHY:

| Signal | P4 package pin |
|---|---:|
| USB0_HS_DM | 49 |
| USB0_HS_DP | 50 |
| VDD_USBPHY | 51 |

Ovi pinovi nisu GPIO-matrix USB linije. Oni pripadaju dedicated High-Speed PHY-u.

---

# 5. ESD protection

Primary:

**TPD2EUSB30ADRTR**

Karakteristike relevantne za Pajoniiir:

- 2-channel ESD array
- 0.7 pF typical IO capacitance
- USB 2.0/3.x capable
- ±8 kV IEC contact class
- 5 A surge rating
- active production

Placement:

**odmah uz USB-A connector**

ESD current return mora ići najkraćim putem u GND plane, a ne kroz P4 područje.

---

# 6. HS series tuning

Espressif za HS ne propisuje 22/33 Ω kao za FS.

Rev A:

- R_USB0_DM = 0 Ω
- R_USB0_DP = 0 Ω

0402 inline footprints, samo ako ih možemo postaviti bez stuba i bez degradacije pair geometryja.

Ako layout postane čišći bez njih, dopušteno ih je izostaviti uz prethodni SI review.

Ne populirati shunt capacitors na HS data lines u Rev A.

---

# 7. Differential impedance

USB0 routing:

**90 Ω differential ±10%**

Pravila:

- DM/DP paralelno
- jednake duljine
- continuous GND reference
- minimum via transitions
- ako je via nužna, par ground-return via uz transition
- bez split planea
- bez stubova
- ne routeati uz buck/backlight switch node
- ne routeati pod C6 antenom

---

# 8. Length matching

Za USB2 HS nije cilj umjetno serpentinati kratku razliku i time dodavati discontinuity.

Prioritet:

1. continuous impedance
2. kratko
3. paralelno
4. približno length matched

Ne uvoditi meandre ako su prirodno gotovo jednake duljine.

---

# 9. USB-A connector

J_USB0 = **TBD-MECH**

Zahtjevi:

- USB 2.0 Type-A receptacle
- host orientation
- rated ≥2 A VBUS kontaktno
- robustan mechanical retention
- through-hole shield tabs preferred
- data contacts SMT ili THT prema mehanici kućišta

Exact MPN zaključati tek nakon PCB/enclosure 3D positioning reviewa.

---

# 10. VBUS

USB0_VBUS dolazi iz:

**U_USB0 TPS25221DRVR**

Initial current limit:

**54.9 kΩ RILIM → ~1.0 A nominal**

Power sheet već sadrži:

- 100 nF
- 47 µF initial bulk
- optional 100 µF DNP

Ne spajati connector VBUS direktno na 5V_SYS.

---

# 11. Shield strategy

Rev A koristi zasebni net:

**USB0_SHIELD**

Predvidjeti tri mogućnosti:

1. R_SHIELD0 = 0 Ω prema GND — default candidate
2. C_SHIELD0 = 1 nF DNP
3. R_SHIELD0_HI = 1 MΩ DNP

Prije EMC testa default je 0 Ω / short low-impedance connection uz connector.

Ako finalno kućište dobije pravi chassis/metal frame, strategiju ponovno razmotriti.

---

# 12. Optional common-mode choke

Ne populirati CMC u baselineu.

Razlog:

- svaki dodatni inline element degradira HS channel
- prvo napraviti čist 90 Ω pair
- dodati CMC samo ako emissions/compliance test pokaže stvarnu potrebu

Ako layout prostor dopušta, može se ostaviti DNP footprint s explicitnim 0R bypassom, ali ne smije pogoršati baseline route.

---

# 13. Connector ESD geometry

Preferred order fizički:

~~~text
USB connector
   |
ESD
   |
(optional CMC)
   |
P4
~~~

ESD mora biti bliže connectoru nego P4-u.

ESD ground via staviti tik uz ESD GND pad.

---

# 14. VBUS ESD / surge

USB VBUS power path već ima current limiting.

Ako konektor očekuje ozbiljan field ESD, predvidjeti dodatni local VBUS TVS footprint kao DNP candidate.

Ne koristiti data-line TPD2EUSB30A kao zamjenu za zasebnu VBUS power protection odluku.

---

# 15. Test points

Data-line testpoints na 480 Mbit/s mogu degradirati SI.

Zato:

- TP_USB0_DM = micro probe pad / DNP
- TP_USB0_DP = micro probe pad / DNP
- TP_USB0_VBUS = normal power TP
- TP_USB0_GND = normal GND TP

Velike 2.54 mm test loops na DM/DP nisu dopuštene.

---

# 16. Bring-up

1. USB0_PWR_EN OFF
2. P4 HS host stack init
3. enable USB0 VBUS
4. measure VBUS rise
5. insert known USB2 HS stick
6. verify HS enumeration, not FS fallback
7. mount filesystem
8. sustained sequential read
9. MP3 playback
10. disconnect/reconnect
11. combined USB1 + Wi-Fi + audio soak

---

# 17. Acceptance

- device enumerates at High-Speed
- no random FS fallback
- no CRC/retry storm
- no disconnect under sustained read
- no P4 brownout during attach
- ESD protection does not degrade link
- USB0 short/fault does not affect USB1

---

# 18. BOM additions

| RefDes | Qty | Part/value |
|---|---:|---|
| D_USB0_ESD | 1 | TPD2EUSB30ADRTR |
| R_USB0_DM | 1 | 0 Ω tuning |
| R_USB0_DP | 1 | 0 Ω tuning |
| J_USB0 | 1 | USB-A receptacle TBD-MECH |
| R_USB0_SHIELD | 1 | 0 Ω default |
| C_USB0_SHIELD | 1 | 1 nF DNP |
| R_USB0_SHIELD_HI | 1 | 1 MΩ DNP |

---

# 19. Layout lock checklist

- [ ] dedicated P4 HS pins 49/50 used
- [ ] VDD_USBPHY correctly powered/decoupled
- [ ] 90 Ω differential stackup calculation done by PCB fab geometry
- [ ] TPD2EUSB30A adjacent to connector
- [ ] ESD ground via adjacent to device
- [ ] no large testpoint stubs
- [ ] no split plane under pair
- [ ] shield connection strategy documented
- [ ] USB0 VBUS only from TPS25221

---

# 20. Zaključak

USB0 Rev A is a deliberately simple HS path:

~~~text
P4 dedicated USB HS DM/DP
 -> 0R tuning
 -> TPD2EUSB30ADRTR
 -> USB-A
 -> Rekordbox storage
~~~

Power is independently controlled by TPS25221.

**Next:** USB1 Full-Speed DDJ-FLX4.
