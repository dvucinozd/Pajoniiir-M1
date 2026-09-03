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

- input bulk/TVS tuning and sourcing: `C3`, `D1`, `C8`
- user-facing mechanics still open: `J1`, `J2`, `J3`, `J4`, `J5`, `J7`, `SW1`, `SW2`
- `J6` **CLOSED in M1-MECH-A8 by removal from Rev A**
- factory fixture: `J9` **CLOSED in M1-MECH-A7** — project-local PCB-only 5-pad pogo footprint with asymmetric tooling holes
- display/FPC: documentation alias `J_LCD`, intentionally not instantiated
- global mechanics: PCB outline / mounting datums
- fabrication: stackup and controlled-impedance geometry

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
2. contact-side orientation and FPC insertion direction
3. mating height / Z envelope
4. meaning of the original Altium references 31/32 vs the physical 30-contact connector
5. pins 15/16/18/19
6. confirmation that original FPC 3V3 pins 4/21/29 are internally common before combining M1's separately filtered LCD/touch rails

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

Before controlled-impedance routing can start, lock:

- board X/Y and mounting holes
- connector/display edge datums
- chosen PCB fabricator
- layer count and copper weights
- finished thickness
- actual dielectric stackup

Then derive:

- USB0 HS: 90 ohm differential target
- USB1 FS: preserve differential geometry even though timing margin is larger
- MIPI DSI: 100 ohm differential target
- power/high-current copper from 5V input through eFuse/shunt/USB branches

---

## Freeze rule

Final placement/routing freeze is allowed only when `layout_freeze_allowed` can truthfully become `true` in the gate manifest with every `blocks_layout_freeze` gate closed.

Exploratory electrical clustering remains allowed; production footprints, Edge.Cuts, connector datums and controlled-impedance routing must not be represented as final while this manifest remains open.
