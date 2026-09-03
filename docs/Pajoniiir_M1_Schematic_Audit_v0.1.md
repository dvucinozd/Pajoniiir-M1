# Pajoniiir-M1 — M1-SCH-A Schematic Audit v0.1

**Projekt:** Pajoniiir-M1 Rev A  
**Datum:** 2026-09-02  
**Ažurirano:** 2026-09-03  
**Status:** Electrical capture and KiCad 9.0.9 ERC clean; documented mechanical/sourcing/display hard gates remain before final manufacturing sign-off.

---

## 1. Audit scope

Ovaj audit pokriva stvarni KiCad projekt pod:

~~~text
hardware/Pajoniiir-M1/
~~~

i svih 15 hijerarhijskih leaf sheetova:

~~~text
01_POWER_INPUT
02_POWER_3V3
03_P4_CORE
04_P4_FLASH_CLOCK_RESET
05_C6_WIFI
06_USB_POWER
07_USB0_STORAGE
08_USB1_FLX4
09_AUDIO_PCM5102A
10_DISPLAY_MIPI
11_TOUCH_GT911
12_MICROSD
13_DEBUG_SERVICE
14_TEST_MONITORING
15_DNP_OPTIONS
~~~

Root je `Pajoniiir-M1.kicad_sch`.

---

## 2. Current milestone verdict

### Component-level capture

**PASS / electrically complete with documented hard gates**

Električki su captured: 5 V input protection/eFuse, 5V_PROTECTED → system shunt → 5V_SYS, 3V3_SYS, ESP32-P4 v3.x core, QSPI flash/40 MHz/boot/reset, ESP32-C6-WROOM-1 + 4-bit SDIO, USB0/USB1 independent VBUS switching, oba USB data patha, PCM5102A MAIN audio, MIPI DSI logical signal path, MP3202 backlight, GT911 panel interface, controlled-power microSD, P4/C6 factory recovery, INA238 monitoring i DNP/DNL assembly policy.

### Native KiCad ERC

**PASS in CI — KiCad 9.0.9**

Latest locked baseline:

```text
unexplained_errors = 0
excluded_errors    = 6
warnings           = 0
```

Šest excluded errora nisu generički suppressioni: to su isključivo UUID-scoped `PANEL_DSI_*` dangling-label hard gateovi koji postoje zato što fizički `J_LCD` namjerno nije instanciran. Structural validator provjerava točan set tih šest UUID-a i faila na svakom dodatnom ERC exclusionu ili globalnom severity downgradeu.

Native GUI open/save + Sync Sheet Pins i dalje ostaje zaseban human/tooling sign-off korak; CI ERC ne zamjenjuje fizičku/mehaničku i manufacturing provjeru.

---

## 3. Structural audit results

PASS:

- svi root/child `.kicad_sch` S-expressioni su balansirani
- svaki child hierarchical label ima matching root sheet pin
- svaki matching label/pin ima isti KiCad shape
- nema root sheet pina bez child hierarchical labela
- nema duplih RefDes oznaka
- nema konfliktnih root local labela na istoj koordinati
- nema preklapanja hierarchical sheet blokova
- uklonjen je stari pre-shunt `5V_SYS` label
- `5V_PROTECTED` je jedini label na eFuse output čvoru
- legacy ESP32-S3 / ES8311 / MAX485 / NS4150 blokovi nisu instancirani kao Rev A funkcionalni sklopovi

Tijekom cleanupa sinkronizirano je 76 sheet-pin shapeova. KiCad Sync Sheet Pins zahtijeva da sheet pin i odgovarajući hierarchical label imaju isti shape.

---

## 4. Critical power-path invariant

~~~text
5V INPUT
   |
U7 TPS259474ARPWR
   |
5V_PROTECTED
   |
R_SYS_SHUNT 5mR
   |
5V_SYS
   |
   +-- 3V3 system buck
   +-- USB0 VBUS switch
   +-- USB1 VBUS switch
   +-- LCD backlight
   +-- remaining 5V loads
~~~

Time INA238 mjeri stvarni ukupni downstream current.

---

## 5. RefDes cleanup

`U1 = ESP32-P4NRW32X` ostaje main MCU. Input eFuse je sada `U7 = TPS259474ARPWR`. Nema duplih RefDes oznaka u trenutnoj hijerarhiji.

Deskriptivni engineering RefDes kao `U_USB0`, `U_USB1`, `U_BL`, `U_MON` i `U_SD_PWR` namjerno ostaju radi preglednosti subsystem reviewa. Manufacturing annotation ih kasnije može normalizirati ako ERP/BOM flow to zahtijeva.

---

## 6. Display / FPC hard gate

Display elektrika je captured, ali **J_LCD namjerno nije instanciran**.

Already captured: 2-lane MIPI DSI, D0/D1/CLK P/N, šest inline 0R tuning footprintova, 3V3_LCD filtering, LCD reset, optional TE, MP3202 backlight, 10uH, SS14, 3.9R || 2.2R LED sense i LEDA/LEDK logical panel-side nets.

Tvornički trag sada identificira FPC1 kao **SOFNG 0.5TBQP-30P-1 / JLCPCB C3975120**, nominalno **30 kontakata, 0.5 mm pitch**. DSI parovi, LEDA/LEDK, TE, LCD reset i touch signali su rekonstruirani iz originalne Guition connectivity ekstrakcije.

Prije J_LCD instanciranja još treba zatvoriti: finalni panel MPN/varijantu, contact-side i mating/mechanical drawing, ulogu Altium symbol referenci 31/32, pinove 15/16/18/19 te potvrdu jesu li originalni FPC 3V3 pinovi 4/21/29 interno zajednički. Ta zadnja stavka je važna jer M1 koristi odvojene filtrirane `3V3_LCD` i `3V3_TOUCH` domene.

Validator namjerno faila ako se `J_LCD` pojavi prije promjene ovog gatea.

---

## 7. Touch status

GT911 se tretira kao panel-integrated. Captured mapping:

~~~text
GPIO3 -> TOUCH_RST
GPIO4 <-> TOUCH_INT
GPIO7 <-> I2C SDA
GPIO8 <-> I2C SCL
~~~

Panel-side: 3V3_LCD → FB_TOUCH → 3V3_TOUCH, 100nF + 4.7uF, 22R SDA/SCL, 4.7k pull-upovi + DNP paralelne opcije, 100R reset/INT i deterministic 0x5D reset sequence.

---

## 8. Backlight status

`U_BL = MP3202DJ-LF-Z`, TSOT23-6.

Local symbol pin model:

~~~text
1 SW
2 GND
3 FB
4 EN
5 OV
6 IN
~~~

JC4880-derived electrical baseline:

~~~text
L_BL = 10uH
D_BL = SS14
C_IN = 10uF + 100nF
C_OUT = 4.7uF + 100nF
R_SENSE = 3.9R || 2.2R
I_LED nominal ~74mA
~~~

Locked sourcing candidate: **L_BL = Coilcraft XGL4030-103MEC**, 10 µH ±20%, 63 mΩ typ DCR, 3.1 A Isat, 3.9 A Irms (40 °C rise), footprint `Inductor_SMD:L_Coilcraft_XxL4030`. EVT još mora potvrditi thermal margin i finalni panel LED string.

---

## 9. Intentional blank-footprint gates

Mechanical / enclosure dependent:

~~~text
01_POWER_INPUT:J1
04_P4_FLASH_CLOCK_RESET:SW1 (RESET)
04_P4_FLASH_CLOCK_RESET:SW2 (BOOT)
07_USB0_STORAGE:J2 (USB0)
08_USB1_FLX4:J3 (USB1)
09_AUDIO_PCM5102A:J4 (RCA L)
09_AUDIO_PCM5102A:J5 (RCA R)
12_MICROSD:J7 (microSD)
~~~

Sourcing / exact land-pattern dependent:

~~~text
01_POWER_INPUT:C3
01_POWER_INPUT:D1
01_POWER_INPUT:C8
~~~

U7 je sada zaključan kao **TPS259474ARPWR** s project-local footprintom `Pajoniiir-M1:Texas_RPW0010A_VQFN-HR-10_2x2mm`, izvedenim iz TI RPW0010A / VQFN-HR-10 2x2 mm drawinga `4225183/A`. Footprint zadržava HotRod L-shaped corner copper, duge IN/OUT landove, 14 copper pad primitiva, 16 stencil paste primitiva, +0.05 mm NSMD mask expansion te 0.100 mm-stencil redukcije približno 93% za corner landove i 82% za IN/OUT. Generički simetrični QFN land pattern nije dopušten.

`R_SYS_SHUNT` je zaključan kao **Vishay WSK25125L000FEA**, 5 mΩ, 1%, 1 W, 4-terminal, s footprintom `Resistor_SMD:R_Shunt_Vishay_WSK2512_6332Metric_T1.19mm`.

Svaki novi blank footprint izvan ovog allowlista validator tretira kao error.


### J6 Rev A removal closure

M1-MECH-A8 removes optional J6 3.5 mm line-out from the Rev A schematic/PCB baseline. MAIN remains RCA J4/J5 and CUE/headphones remain via DDJ-FLX4 USB Audio. J6 was already production-default DNP and not a headphone output; M1-MECH-A4 additionally showed only 0.525 mm to the candidate mounting-hole edge in the same primary I/O row before boss/courtyard allowance.

### J9 factory pogo closure

M1-MECH-A7 closes the former blank-footprint J9 gate with project-local footprint `Pajoniiir-M1:Factory_Pogo_USBJTAG_1x05_P1.27_2Tooling`. J9 remains DNL / `in_bom=no`, so manufacturing BOM parity/counts are unchanged. The footprint is a 5-pad 1.27 mm production pogo row with two asymmetric Ø1.2 mm tooling holes and explicit pin-1 datum. Existing signal mapping is preserved: 3V3_SYS VREF sense-only, GND, USBJTAG D-/D+, CHIP_PU. Fixture power injection through VREF is forbidden.

---

## 10. USB status

USB0: dedicated P4 HS, 0R data tuning, TPD2EUSB30A, independent VBUS, shield tuning i 90R diff target. Hard gate je exact USB-A MPN/footprint.

USB1: P4 FS GPIO26/27, 22R/22R, DNP data caps, TPD2EUSB30A, independent VBUS, shield tuning i očuvani GPIO24/25 USB Serial/JTAG. Hard gate je exact USB-A MPN/footprint.

---

## 11. microSD status

Captured: native 4-bit SDMMC0, GPIO39-44, GPIO45 controlled power, GPIO46 card detect, TPS22918, CT/QOD, pull-upovi na switched 3V3_SD, series tuning i DNP CLK capacitor.

Hard gate: exact microSD socket MPN/footprint i final low-C ESD odluka.

---

## 12. Debug / recovery status

Captured independent paths: P4 UART0, P4 USB Serial/JTAG i C6 UART/boot/EN. P4 i C6 recovery su zasebni. Tag-Connect footprintovi su DNL/no-parts, a VREF je sense-only.

---

## 13. Structural validator

Added:

~~~text
hardware/Pajoniiir-M1/tools/validate_schematic_structure.py
~~~

Run from repo root:

~~~bash
python3 hardware/Pajoniiir-M1/tools/validate_schematic_structure.py
~~~

Provjerava S-expression balance, hierarchy name/shape sync, duplicate RefDes, root label collisions, sheet overlap, blank-footprint allowlist, banned legacy blocks, 5V_PROTECTED→shunt→5V_SYS invariants, INA238/MP3202 presence i J_LCD hard gate.

Ne radi native ERC, footprint pin-to-pad validation, PCB DRC, impedance verification ni field-solver analizu.

### Manufacturing-output CI

Dodani su native KiCad exporti i source-parity provjera. CI sada generira manufacturing BOM CSV, hierarchy netlist, kompletni schematic PDF i Markdown BOM-audit. `validate_manufacturing_outputs.py` zahtijeva da KiCad BOM sadrži točno isti `in_bom=yes` RefDes skup kao 15 leaf sheetova te iste Value/Footprint podatke. Trenutni M1-MECH-A8 source baseline ima 269 `in_bom=yes` RefDes-a, 16 DNP stavki i 11 dopuštenih blank-footprint manufacturing gateova.

Detalji: `Pajoniiir_Manufacturing_Output_Contract_v0.1.md`.

### Run #76 review evidence

KiCad 9 CI run #76 (`d8bffb3a`) je potpuno zelen nakon presentation cleanup-a. Generated manufacturing BOM ima **270/270 RefDes parity PASS**, **17 DNP** i točno **12 intentional blank-footprint gateova**. Schematic PDF ima 16 stranica; render-first human review potvrđuje da nema rezanih engineering-note blokova niti title-block preklapanja. `03_P4_CORE` je namjerno A2 kako U1B ostaje unutar review framea. Manual BOM review nije pronašao dodatne skrivene TBD/blank-footprint stavke izvan odobrenog gate skupa.

---

## 14. M1-SCH-A exit gates remaining

- [x] 15-sheet component-level capture
- [x] structural hierarchy audit
- [x] unique RefDes audit
- [x] root power-path correction
- [x] DNP/DNL policy captured
- [x] local structural validator committed
- [x] hierarchy pin-sync equivalence — bidirectional root/child name+shape validator + native KiCad root load/netlist/PDF export
- [x] native KiCad 9.0.9 ERC — 0 unexplained errors, 6 approved J_LCD exclusions, 0 warnings
- [x] final U7 RPW0010A land pattern freeze — `Pajoniiir-M1:Texas_RPW0010A_VQFN-HR-10_2x2mm`
- [x] final L_BL part / footprint — XGL4030-103MEC / L_Coilcraft_XxL4030
- [x] final system shunt part / footprint — WSK25125L000FEA / WSK2512 T1.19mm
- [ ] J_LCD physical gate closed
- [ ] USB-A exact MPNs
- [ ] microSD exact MPN
- [ ] RCA exact MPNs
- [ ] 5V input exact MPN
- [ ] RESET/BOOT exact switch MPNs
- [x] schematic PDF generation in CI
- [x] schematic PDF human review — run #76, 16/16 pages reviewed
- [x] manufacturing BOM/netlist extraction + schematic-source parity check in CI
- [x] historical run #76 engineering/manual BOM review — 270/270, 17 DNP, 12 intentional blank gates; M1-MECH-A8 source baseline is 269/16/11 after intentional J6 removal

---

### Mechanical gate authority

Open physical gates are now machine-readable in `hardware/Pajoniiir-M1/mechanical_gates.json` and described in `Pajoniiir_M1_Mechanical_Sourcing_Gates_v0.1.md`. Both structural and manufacturing validators derive blank-footprint policy from that manifest.

---

### M1-MECH-A progress

Display/front geometry and the legacy enclosure candidate are now quantified in `mech_a.json`. The old Blender fit-test envelope (117.008 × 69.408 × 13.900 mm) matches GUITION's 117.01 × 69.41 × 13.8 mm module reference closely, so the 121.008 × 73.408 × 30 mm / 2 mm-wall enclosure is retained as a validated M1 candidate rather than discarded. Final PCB outline and connector datums remain open.

---

## 15. PCB-layout status

**GO for exploratory functional placement:** YES, uz placeholder mechanics i obavezni `pcb_constraints.json` / `Pajoniiir_M1_PCB_Layout_Constraints_v0.1.md` constraint set.

**GO for final placement freeze:** NO.

**GO for final USB/MIPI routing:** NO.

**GO for Gerbers / EVT order:** NO.

Final layout čeka authoritative display/FPC mechanics, exact connector footprints, final PCB outline, fab stackup, 90R USB geometry, 100R MIPI geometry i preostale manufacturing/sourcing odluke. Native ERC više nije blocker.

---

## 16. Recommended next sequence

1. Resolve remaining LCD/panel/FPC mating geometry, pins 15/16/18/19 and 3V3-domain commonality.
2. Select exact USB-A, RCA, microSD, 5V input and RESET/BOOT/service-switch MPNs from the final enclosure/mechanical constraints.
3. Lock PCB outline / connector datums / display FPC location.
4. Obtain PCB fab stackup and derive controlled-impedance geometries.
5. Begin final placement/routing only after those physical gates close.

Optional editor hygiene before manual schematic editing: open/save once in native KiCad GUI. This is no longer a sign-off gate because hierarchy pin synchronization is already enforced bidirectionally in CI and the full root hierarchy is loaded/exported by native KiCad 9.

---

## 17. Conclusion

Pajoniiir-M1 više nije u architecture-only fazi. Projekt sada ima stvarni hijerarhijski component-level Rev A schematic capture sa strukturno čistim inter-sheet contractom.

Native KiCad ERC, schematic PDF human review i manufacturing BOM cross-check više nisu blockeri. Preostali rad prije finalnog PCB layouta koncentriran je isključivo na mehaničko i exact-footprint zatvaranje, finalni outline/datume i fab stackup. Najveći pojedinačni blocker ostaje fizička LCD/touch panel/FPC definicija, sada sužena na jasno identificirane mating/pin/3V3-domain nepoznanice.
