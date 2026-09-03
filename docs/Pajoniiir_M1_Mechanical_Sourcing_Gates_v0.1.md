# Pajoniiir-M1 — Mechanical & Sourcing Gate Closure v0.1

**Datum:** 2026-09-03  
**Status:** Physical gates formalized; final layout freeze remains blocked  
**Machine-readable authority:** `hardware/Pajoniiir-M1/mechanical_gates.json`

---

## M1-MECH-A baseline evidence

Manufacturer and legacy Blender geometry are now correlated in `hardware/Pajoniiir-M1/mech_a.json` and `Pajoniiir_M1_MECH_A_Baseline_v0.1.md`. The validated legacy enclosure candidate is 121.008 × 73.408 × 30.000 mm with 2.0 mm walls; the bare display/front reference is 114.40 × 66.80 mm. These values narrow the mechanical search space but do not yet authorize final Edge.Cuts.

---

## Current conclusion

Electrical capture, hierarchy synchronization, native KiCad ERC, manufacturing BOM review and schematic PDF review are complete.

The repository currently contains **no authoritative PCB outline, enclosure CAD, board-edge connector datums or mounting-hole coordinate set**. Therefore exact user-facing connector MPNs cannot be responsibly frozen from the electrical schematic alone.

The policy is deliberate: no arbitrary footprint is allowed to turn a mechanical unknown into a false green check.

---

## Open physical gates

The machine-readable manifest records every open gate, its current RefDes, required evidence and closure condition. It is now the source of truth for both structural and manufacturing blank-footprint validation.

Key classes:

- input bulk EVT tuning still open: `C3`, `C8`
- input TVS `D1` **CLOSED in M1-MECH-A12** — ST SMBJ6.0CA-TR / `Diode_SMD:D_SMB`
- user-facing mechanics still open: `J1`, `J2`, `J3`, `J4`, `J5`, `J7`, `SW1`, `SW2`
- `J6` **CLOSED in M1-MECH-A8 by removal from Rev A**
- factory fixture: `J9` **CLOSED in M1-MECH-A7** — project-local PCB-only 5-pad pogo footprint with asymmetric tooling holes
- display/FPC: documentation alias `J_LCD`, intentionally not instantiated
- global mechanics: PCB outline / mounting datums
- fabrication stackup **CLOSED in M1-MECH-A11** — JLCPCB `JLC04161H-7628`; exact routed impedance width/spacing remains a layout-stage calculation

---

## Display/FPC evidence already locked

Public JLCPCB data identifies:

~~~text
Manufacturer: SOFNG
MPN: 0.5TBQP-30P-1
JLCPCB: C3975120
Package: FPC0.5mm-30pin
Description: FPC-30P-0.5mm
~~~

JLCPCB also exposes an EasyEDA symbol/footprint entry for the part. This is enough to confirm identity/contact count/pitch, but **not** enough to override the unresolved panel-side mating/contact orientation and pin-domain questions.

Source:

~~~text
https://jlcpcb.com/partdetail/SOFNG-0_5TBQP_30P1/C3975120
~~~

Remaining J_LCD evidence required before instantiation:

1. authoritative purchased panel/assembly MPN
2. top-vs-bottom electrical contact-side orientation
3. exact connector housing / mated FPC Z height and final panel-tail geometry
4. confirmation that original FPC 3V3 pins 4/21/29 are internally common before mapping M1's separately filtered LCD/touch rails

Already resolved by M1-MECH-A9/A10: physical sequence is 30 electrical contacts, 31/32 are GND shell/mount references, pins 15/16/18/19 are NC, and the original assembly uses component-side right-angle/side-entry insertion.

---

## Connector closure inputs

### USB-A J2/J3

Need final board-edge X/Y datum, insertion direction, vertical/right-angle decision, enclosure cutout and shell-retention/keepout envelope.

### RCA J4/J5

Need panel datum, center height, horizontal spacing, connector orientation and whether isolated shell mechanics are required. J6 is no longer part of the Rev A PCB: M1-MECH-A8 closes it by removal.

### microSD J7

Need card insertion direction, enclosure access geometry, push-push vs push-pull choice, socket height and final card-detect switch requirement.

### 5 V input J1

Need enclosure cutout, board-edge orientation, locking/mating cable requirement and connector Z/depth envelope.

### RESET/BOOT SW1/SW2

Need top/side actuation decision, access method and actuator height relative to enclosure.

### Factory USB pogo J9 — CLOSED

Locked in M1-MECH-A7:

~~~text
Footprint: Pajoniiir-M1:Factory_Pogo_USBJTAG_1x05_P1.27_2Tooling
5 pads @ 1.27 mm
pad diameter: 1.0 mm
pin 1: rectangular + silkscreen marker
tooling: 2 × Ø1.2 mm NPTH, asymmetric coordinates
assembly: DNL / PCB-only
~~~

Pin map:

~~~text
1  3V3_SYS VREF sense-only
2  GND
3  USBJTAG_DM_SERVICE
4  USBJTAG_DP_SERVICE
5  CHIP_PU
~~~

The fixture must power the board through the normal qualified 5 V path and must never source pin 1. No user-facing enclosure aperture is required.

---

## Board/fabrication closure inputs

Fabrication stackup is already locked by M1-MECH-A11:

```text
JLCPCB JLC04161H-7628
4 layers / 1.6 mm
1 oz outer / 0.5 oz inner
L1 high-speed -> solid L2 GND reference
```

Before controlled-impedance routing/final layout freeze:

- lock board X/Y and mounting holes
- lock connector/display edge datums
- calculate and record exact width/spacing from the current JLCPCB impedance calculator for USB 90 ohm differential and MIPI DSI 100 ohm differential
- size/review power/high-current copper from 5V input through eFuse/shunt/USB branches

---

## Freeze rule

Final placement/routing freeze is allowed only when `layout_freeze_allowed` can truthfully become `true` in the gate manifest with every `blocks_layout_freeze` gate closed.

Exploratory electrical clustering remains allowed; production footprints, Edge.Cuts, connector datums and controlled-impedance routing must not be represented as final while this manifest remains open.
