# Pajoniiir Mainboard — USB1 Full-Speed DDJ-FLX4 Design v0.1

**Projekt:** Pajoniiir-M1 Rev A  
**Blok:** 08_USB1_FLX4  
**Namjena:** DDJ-FLX4 MIDI + USB Audio Class host  
**Datum:** 2026-09-02

---

# 1. Funkcija

USB1 je namjenski **USB 2.0 Full-Speed OTG host** za Pioneer DDJ-FLX4.

Na tom portu Pajoniiir koristi:

- MIDI IN
- MIDI OUT
- controller LED feedback
- 4-channel USB Audio Class
- CUE/PFL audio na kanalima 3/4

USB1 je fiksni host i koristi USB-A female konektor.

---

# 2. P4 Full-Speed PHY izbor

ESP32-P4 Full-Speed OTG ima dva integrirana FS transceiver patha.

Default FS OTG mapping:

- GPIO26 = USB D-
- GPIO27 = USB D+

Rev A namjerno koristi upravo:

**GPIO26 / GPIO27**

Time GPIO24/GPIO25 ostaju dostupni za P4 USB Serial/JTAG service/debug funkciju.

---

# 3. Signal chain

~~~text
ESP32-P4
GPIO26 DM -- 22R --+
                   |--> TPD2EUSB30A --> USB-A --> FLX4
GPIO27 DP -- 22R --+
~~~

VBUS dolazi samo iz USB1 TPS25221 switcha.

---

# 4. Net names

- USB1_FS_DM
- USB1_FS_DP
- USB1_VBUS
- USB1_SHIELD
- GND

---

# 5. Series resistors

Espressif preporučuje:

**22/33 Ω**

series resistor na FS D-/D+ blizu P4.

Rev A initial:

- R_USB1_DM = 22 Ω
- R_USB1_DP = 22 Ω

Package 0402.

Ako signal/EMI mjerenje pokaže potrebu:

- probati 27 Ω
- probati 33 Ω

Oba elementa moraju biti iste vrijednosti.

---

# 6. Optional ground capacitors

Espressif dopušta optional ground capacitor footprintove na FS data linijama.

Rev A:

- C_USB1_DM = DNP
- C_USB1_DP = DNP

Ne zaključavati vrijednost bez mjerenja.

Ako EMI tuning zatraži C:

- populirati simetrično
- koristiti malu C0G/NP0 vrijednost
- ponovno provjeriti USB signal integrity

---

# 7. ESD

Primary:

**TPD2EUSB30ADRTR**

Isti dio kao USB0.

Iako Full-Speed ne zahtijeva <1 pF kao HS u istoj mjeri, korištenje istog low-C dijela:

- pojednostavljuje BOM
- minimizira distortion
- daje isti ESD protection standard

Placement neposredno uz USB1 connector.

---

# 8. Differential routing

I FS pair routeati kao:

**90 Ω differential target**

Pravila:

- parallel/equal
- continuous GND
- minimal vias
- no split plane
- no switching node crossing
- no antenna keep-out crossing

FS je tolerantniji od HS, ali nema razloga namjerno napraviti loš channel.

---

# 9. USB1 connector

J_USB1 = USB-A receptacle, **TBD-MECH**.

DDJ-FLX4 se spaja:

**USB-A → USB-C data cable**

Prednosti nad USB-C source portom na Rev A:

- nema CC1/CC2
- nema Rp advertisement
- nema role ambiguity
- fiksna host topologija
- lakši bring-up

---

# 10. USB1 VBUS

Iz U_USB1 TPS25221.

Initial:

**RILIM = 34.8 kΩ → ~1.6 A nominal**

Ovo je namjerno engineering margin, ne finalna tvrdnja o FLX4 potrošnji.

Finalni RILIM nakon scope/current measurementa.

---

# 11. Power sequencing

USB1 VBUS mora defaultno biti OFF.

Boot:

1. P4 start
2. USB host stack start
3. MIDI/UAC driver ready
4. USB1_PWR_EN high
5. VBUS rise
6. FLX4 enumeration
7. MIDI descriptors
8. UAC descriptors
9. audio stream enable

---

# 12. Preserve P4 USB Serial/JTAG

Pošto USB1 koristi GPIO26/27, možemo sačuvati:

- GPIO24 = Serial/JTAG D-
- GPIO25 = Serial/JTAG D+

Preporuka:

izvesti GPIO24/25 na **factory/service test pads** ili optional internal USB test connector.

Time imamo tri neovisna recovery/debug puta:

1. UART0 GPIO37/38
2. P4 USB Serial/JTAG GPIO24/25
3. external debugger/JTAG ako kasnije zatreba

To je korisno na prvoj custom P4 ploči.

---

# 13. USB Serial/JTAG test path

Ne mora imati vanjski user-facing connector.

Predvidjeti:

- TP_P4_USBJTAG_DM
- TP_P4_USBJTAG_DP
- GND
- optional 5V sense only if needed

Ako se koristi pogo fixture, fixture može imati svoj USB connector.

---

# 14. Shield strategy

USB1_SHIELD isti koncept kao USB0:

- 0 Ω to GND default candidate
- 1 nF DNP option
- 1 MΩ DNP option

Ako finalno metalno kućište ima pravi chassis node, reevaluirati prije EMC freezea.

---

# 15. Data ESD path

Fizički red:

~~~text
USB-A
 |
TPD2EUSB30A
 |
signal route
 |
22R / 22R near P4
 |
GPIO26 / GPIO27
~~~

Series R je blizu P4, ESD blizu connectora.

---

# 16. No USB hub

Rev A ne koristi hub između P4 i FLX4.

Razlog:

- P4 već ima zaseban FS root
- manji latency
- manji BOM
- manje software complexity
- manje power interactions
- bolji fault isolation

---

# 17. FLX4 data validation

Bring-up mora potvrditi:

- stable FS enumeration
- MIDI IN
- MIDI OUT
- LED feedback
- UAC interface discovery
- 4 channels
- continuous audio
- simultaneous MIDI + UAC
- disconnect/reconnect
- 100 repeated reconnect cycles

---

# 18. Audio-specific USB1 test

CUE/PFL path:

~~~text
P4 mixer
 -> UAC ch3/ch4
 -> USB1 FS
 -> DDJ-FLX4
 -> headphone output
~~~

Test:

- no dropouts
- no MIDI jitter correlated with UAC
- no audible click during normal control traffic
- recovery after cable reconnect

---

# 19. Test points

- TP_USB1_VBUS
- TP_USB1_DM micro pad
- TP_USB1_DP micro pad
- TP_USB1_FAULT_N
- TP_USB1_EN
- TP_GND_USB1

Data test pads small / DNP probe style.

---

# 20. BOM additions

| RefDes | Qty | Part/value |
|---|---:|---|
| D_USB1_ESD | 1 | TPD2EUSB30ADRTR |
| R_USB1_DM | 1 | 22 Ω |
| R_USB1_DP | 1 | 22 Ω |
| C_USB1_DM | 1 | DNP tuning |
| C_USB1_DP | 1 | DNP tuning |
| J_USB1 | 1 | USB-A receptacle TBD-MECH |
| R_USB1_SHIELD | 1 | 0 Ω default |
| C_USB1_SHIELD | 1 | 1 nF DNP |
| R_USB1_SHIELD_HI | 1 | 1 MΩ DNP |

---

# 21. Layout checklist

- [ ] GPIO26 DM
- [ ] GPIO27 DP
- [ ] 22R/22R at P4 side
- [ ] optional C footprints DNP
- [ ] TPD2EUSB30A at connector
- [ ] 90 Ω differential target
- [ ] continuous GND reference
- [ ] no large stubs
- [ ] USB1 VBUS exclusively from U_USB1
- [ ] GPIO24/25 preserved for Serial/JTAG service
- [ ] shield strategy same family as USB0

---

# 22. Acceptance criteria

- FLX4 always enumerates as expected
- UAC 4-channel stable
- MIDI bidirectional stable
- LEDs do not disturb audio
- no USB1 disconnect under full system load
- no VBUS brownout
- fault/recovery independently works
- USB0 storage remains alive during USB1 reconnect/fault
- P4 USB Serial/JTAG service path remains available

---

# 23. Zaključak

USB1 Rev A:

~~~text
P4 GPIO26/27 FS OTG
 -> 22R / 22R
 -> TPD2EUSB30ADRTR
 -> USB-A
 -> DDJ-FLX4

VBUS:
TPS25221 independent
~1.6A nominal initial
firmware EN/FAULT recovery

P4 GPIO24/25:
reserved for USB Serial/JTAG factory/service
~~~

S time su oba USB data patha električki definirana.
