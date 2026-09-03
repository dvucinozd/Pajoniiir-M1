# Pajoniiir Mainboard — DNP / Option Matrix v0.1

**Projekt:** Pajoniiir-M1 Rev A  
**Blok:** 15_DNP_OPTIONS  
**Datum:** 2026-09-02  
**Status:** Engineering option policy

---

# 1. Svrha

DNP element postoji samo ako:

- pomaže EVT/DVT mjerenju,
- omogućuje tuning bez PCB respina,
- predstavlja jasno definiranu buduću opciju,
- ili omogućuje cost-down nakon validacije.

DNP nije mjesto za vraćanje legacy funkcija.

---

# 2. Zabranjeni legacy footprintovi

Na Rev A PCB-u **nema footprinta** za:

- ESP32-S3
- ES8311
- speaker amp
- speaker connector
- analog microphone
- MAX485 / RS485
- camera / MIPI CSI
- old P4↔S3 UART
- old monitor I²S bridge
- battery charger
- generic large expansion header

Ako se neka od tih funkcija vrati, to je nova board revision, ne DNP populate varijanta.

---

# 3. Power DNP / tuning

| Element | Default | Svrha |
|---|---|---|
| input bulk alternate 220/470 µF | DNP alternatives | transient tuning |
| 3V3 second 22 µF | DNP | load transient tuning |
| FB_C6 ferrite | 0 Ω default | EMI tuning |
| FB_AUDIO ferrite | 0 Ω default | audio noise tuning |
| FB_LCD ferrite | 0 Ω default | display noise tuning |
| FB_TOUCH ferrite | 0 Ω default | touch noise tuning |
| INA238 monitor | populate EVT, optional DNP later | power telemetry |

---

# 4. USB DNP / tuning

## USB0 HS

- 0 Ω inline DM/DP tuning
- shield 1 nF option
- shield 1 MΩ option
- optional VBUS 100 µF
- optional measurement shunt footprint

## USB1 FS

- optional DM/DP shunt capacitors
- shield 1 nF option
- shield 1 MΩ option
- optional VBUS 100 µF
- optional measurement shunt footprint

No CMC populated by default.

---

# 5. Flash / clock tuning

- QSPI 0 Ω footprints on CS/CLK/D0-D3
- crystal series 0 Ω
- alternate 12/16/18 pF crystal load values are assembly variants, not simultaneous footprints

---

# 6. Audio DNP

- J6 3.5 mm stereo line-out: **removed from Rev A in M1-MECH-A8; no DNP footprint reserved**
- optional analog ESD protectors
- FB_AUDIO ferrite alternative

No headphone amplifier DNP.

No speaker path DNP.

---

# 7. Display DNP

- LCD_TE 0 Ω link, DNP default
- DSI six 0 Ω tuning elements populated by default
- optional backlight control straps depending final MP3202 network
- no extra MIPI ESD by default

---

# 8. Touch DNP

- parallel second 4.7 kΩ SDA pull-up
- parallel second 4.7 kΩ SCL pull-up
- optional low-C touch ESD array
- polling firmware remains software fallback, not a hardware DNP option

---

# 9. microSD DNP

- 22 µF extra output capacitor
- CLK-to-GND tuning capacitor
- optional SD ESD array
- card detect resistor/net only if selected socket supports CD

TPS22918 itself is **not** DNP in Rev A baseline; controlled card power is part of the architecture.

---

# 10. Debug DNP

Tag-Connect footprints are **DNL — Do Not Load**, because they are bare PCB pads.

- JDBG_P4 = footprint only
- JDBG_C6 = footprint only
- JDBG_USB = footprint only

Optional USB Serial/JTAG capacitors are DNP.

---

# 11. Monitoring DNP

INA238 path has two assembly modes.

## EVT/DVT

- INA238 populated
- 5 mΩ shunt populated
- ALERT pull-up populated

## Cost-down

- INA238 DNP
- ALERT pull-up DNP
- shunt path handled by approved production jumper/shunt strategy

Do not leave an open 5V_SYS power path when U_MON is DNP.

---

# 12. DNP BOM properties

Svaki optional element u KiCadu mora imati:

~~~text
Populate = DNP
Variant = EVT / DVT / PROD / ALT
Reason = <short engineering reason>
~~~

i biti pravilno excluded/flagged u manufacturing BOM-u.

---

# 13. Variant matrix

| Blok | EVT | DVT | Production baseline |
|---|---|---|---|
| INA238 | POP | POP | TBD after DVT |
| extra USB VBUS C | test variants | selected | selected |
| SD CLK C | tune | selected/DNP | selected/DNP |
| touch extra pullups | tune | selected/DNP | selected/DNP |
| analog ESD | evaluate | compliance dependent | compliance dependent |
| LCD TE link | DNP/experiment | TBD | DNP unless used |
| 3.5 mm line out | removed | removed | removed from Rev A (M1-MECH-A8) |
| ferrites | 0 Ω first | tune | selected |
| debug footprints | DNL pads | DNL pads | DNL pads |

---

# 14. Pravilo za Rev A

Ako ne možemo objasniti zašto neki DNP footprint postoji i koji se test njime provodi, taj footprint se uklanja prije layouta.

Cilj nije "ostaviti sve za svaki slučaj", nego zadržati samo jeftine, strateške tuning/recovery mogućnosti.
