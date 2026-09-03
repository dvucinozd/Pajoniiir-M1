# Pajoniiir-M1 — M1-MECH-A Physical Evidence Boundary v0.1

**Date:** 2026-09-03  
**Revision:** M1-MECH-A12  
**Status:** Repo-only analytical/sourcing work complete; final layout remains blocked by physical/EVT evidence

---

## 1. Meaning of this checkpoint

M1-MECH-A has reached the point where additional green checkmarks cannot be produced responsibly from repository analysis, public datasheets or arithmetic alone.

Every remaining `blocks_layout_freeze` gate now requires at least one of:

- direct enclosure / PCB / connector measurement,
- authoritative final display-panel mechanical data,
- actual EVT electrical measurements,
- final CAD datum placement.

This is an intentional boundary, not an unfinished desk-research task.

`layout_freeze_allowed` therefore remains **false**.

---

## 2. Closures completed without hardware

### Electrical / sourcing

- **D1 input TVS — CLOSED, M1-MECH-A12**
  - STMicroelectronics `SMBJ6.0CA-TR`
  - bidirectional 6 V TVS
  - `Diode_SMD:D_SMB`
  - committed directly in `01_POWER_INPUT.kicad_sch`
  - chosen bidirectional so the TVS does not introduce a forward-diode path that defeats the TPS259474 reverse-polarity architecture

### Fabrication

- **FAB_STACKUP — CLOSED, M1-MECH-A11**
  - JLCPCB
  - `JLC04161H-7628`
  - 4 layers / 1.6 mm
  - 1 oz outer / 0.5 oz inner
  - primary USB/MIPI routing on L1 referenced to solid L2 GND
  - 90-ohm USB and 100-ohm MIPI targets retained

Exact routed width/spacing is deliberately not invented before layout. `controlled_impedance_locked` remains false until the current JLCPCB calculator result is recorded for the actual chosen pair spacing / route geometry.

### Product / service mechanics

- **J6 optional 3.5 mm line out — CLOSED by removal, M1-MECH-A8**
- **J9 factory USB/JTAG pogo — CLOSED, M1-MECH-A7**

### Display forensics already resolved

- connector identity: SOFNG `0.5TBQP-30P-1`, JLCPCB `C3975120`
- 30 electrical contacts, 0.5 mm pitch
- Altium refs 31/32 are auxiliary GND shell/mount references
- FPC pins 15/16/18/19 are NC on the original JC4880 variant
- original assembly is component-side, right-angle / side-entry

---

## 3. Twelve remaining layout blockers

The machine-readable authority is `hardware/Pajoniiir-M1/mechanical_gates.json`.

### EVT-only bulk-capacitor gates

1. `C3_INPUT_BULK`
2. `C8_PROTECTED_BULK`

These remain intentionally open. The 220 / 330 / 470 uF choice must be based on real startup/inrush and rail-transient measurements plus ESR/ripple/current and final package-height constraints. Selecting an arbitrary 330 uF production MPN now would turn an EVT variable into a false production lock.

### External connector / service-access geometry

3. `J1_POWER_INPUT`
   - preferred: Switchcraft `722RAHLP` + `S760KHZ`
   - needs exact X-wall sign, center/cutout, nut/washer engagement, body keepout and plug/cable envelope

4. `J2_USB0`
5. `J3_USB1`
   - preferred: Amphenol `87520-1010ALF`
   - needs actual long-wall datum, body/shell/cable insertion envelope and connector-driven PCB-Z validation

6. `J4_RCA_L`
7. `J5_RCA_R`
   - preferred main-board family: Kycon `KLPX-0848A-2-W` / `-R`
   - panel-mount fallback retained if local Z/body/plug clearance fails
   - needs actual wall datum and complete mated-plug envelope

8. `J7_MICROSD`
   - preferred: Molex `503398-1892`
   - needs exact slot center, PCB-edge relation, full card travel and finger/service clearance

9. `SW1_RESET`
10. `SW2_BOOT`
   - preferred: `B3U-3000P-B`
   - needs actuator-to-wall distance, separate recessed tool holes, spacing and no interference with the microSD path

These eight gates cannot be closed by choosing footprints in isolation; the selected connector/switch could become mechanically wrong once the real panel datum is applied.

### Display FPC

11. `J_LCD_DISPLAY_FPC`

Still required:

- authoritative final purchased panel/assembly MPN,
- top-vs-bottom electrical contact side,
- exact connector housing / mated FPC Z height and final tail geometry,
- proof whether panel-side 3V3 contacts 4/21/29 are internally common before mapping M1 `3V3_LCD` / `3V3_TOUCH` rails.

J_LCD remains intentionally uninstantiated.

### Global board mechanics

12. `PCB_OUTLINE`

The current `108.00 x 65.06 mm` envelope and candidate mounting centers are placement-feasibility data only. Final Edge.Cuts and mounting datums must wait until connector body/cutout/boss/plug clearances and PCB-Z are proven.

---

## 4. Inputs required to resume final mechanical closure

A single physical/CAD evidence package can unlock most remaining gates:

1. enclosure interior and wall datums in the `M1_FRONT_CENTER` coordinate system,
2. exact PCB mounting boss centers, boss OD/height and screw hardware,
3. chosen POWER_WALL and primary long-I/O-wall signs,
4. wall thickness and local ribs around all connector zones,
5. connector center heights and full plug/cable insertion envelopes,
6. final display assembly MPN plus FPC-side mechanical drawing or direct caliper/inspection evidence,
7. EVT captures for the C3/C8 220/330/470 uF sweep at startup and worst expected USB-load transients.

Once those exist, the remaining gates can be closed in a deterministic order: external connector datums -> PCB Z/standoff -> final outline/mounting -> C3/C8 production packages -> exact impedance geometry -> placement/routing freeze.

---

## 5. Current manufacturing-source state

After M1-MECH-A12:

```text
in_bom=yes RefDes          269
DNP RefDes                  16
intentional blank BOM gates 10
open layout blockers        12
```

D1 is no longer an intentional blank-footprint gate.

---

## 6. Freeze rule

Do not set `layout_freeze_allowed=true` merely because preferred connector MPNs exist.

Final layout freeze requires:

- every remaining `blocks_layout_freeze` gate closed,
- authoritative Edge.Cuts and mounting datums,
- all connector courtyards / mated envelopes checked against enclosure CAD,
- C3/C8 EVT result converted into exact production packages,
- exact 90-ohm USB / 100-ohm MIPI width-spacing values recorded for the locked JLC stackup.

Until then, exploratory placement is allowed; production routing/sign-off is not.
