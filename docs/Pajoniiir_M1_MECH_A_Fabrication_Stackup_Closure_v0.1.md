# Pajoniiir-M1 — M1-MECH-A Fabrication Stackup Closure v0.1

**Datum:** 2026-09-03  
**Revision:** M1-MECH-A11  
**Status:** FAB_STACKUP gate CLOSED; exact routed width/spacing remains pre-routing controlled-impedance work

## Decision

Rev A fabrication baseline is now:

```text
Fabricator       JLCPCB
Stackup          JLC04161H-7628
Layer count      4
Finished PCB     1.6 mm
Outer copper     1 oz
Inner copper     0.5 oz
L1 -> L2         7628 prepreg, 0.2104 mm, Er 4.4
L2 -> L3         FR-4 core, 1.065 mm, Er 4.6
L3 -> L4         7628 prepreg, 0.2104 mm, Er 4.4
```

Layer use:

```text
L1 / F.Cu   components + primary USB/MIPI/high-speed signals
L2 / In1    uninterrupted GND reference plane
L3 / In2    power distribution + low-speed where appropriate
L4 / B.Cu   secondary signals/components
```

Primary USB/MIPI routing is intentionally kept on L1 referenced directly to the solid L2 ground plane. High-speed traces must not use L3 as a split-power reference.

## Controlled impedance

Targets are locked:

```text
USB0 HS       90 ohm differential ±10%
USB1 FS       90 ohm differential ±10%
MIPI DSI     100 ohm differential ±10%
```

JLCPCB currently publishes controlled-impedance support on 4-layer boards and standard ±10% impedance tolerance. Its current stackup table explicitly lists `JLC04161H-7628`, and a 2026 JLCPCB case study uses that exact 4-layer / 1.6 mm stackup for 90-ohm USB and 100-ohm PCIe/MIPI DSI targets.

## Why exact width/gap is not frozen in A11

A stackup selection and a routed impedance geometry are different freeze points.

JLCPCB's current impedance calculator accepts the selected stackup, layer, target impedance and pair spacing, then derives the trace width. Manufacturing compensation can also affect the final artwork width. Therefore A11 does **not** invent a width/gap pair from a generic FR-4 formula.

Before `controlled_impedance_locked` becomes true, the layout must record the current JLCPCB calculator result for this exact stackup for:

- USB 90 ohm differential,
- MIPI DSI 100 ohm differential,
- any high-speed path that changes layer/reference geometry.

Changing the stackup from `JLC04161H-7628` requires a fresh impedance calculation.

## Gate result

`FAB_STACKUP` no longer blocks M1-MECH-A. `controlled_impedance_locked` deliberately remains `false`; this prevents stackup selection from being mistaken for completed PCB routing sign-off.

## Sources

- JLCPCB controlled-impedance stackups: https://jlcpcb.com/impedance
- JLCPCB impedance calculator guide: https://jlcpcb.com/help/article/user-guide-to-the-jlcpcb-impedance-calculator
- JLCPCB PCB capabilities: https://jlcpcb.com/capabilities/pcb-ca-
- JLCPCB 2026 controlled-impedance case study: https://jlcpcb.com/blog/pibrick-cm5-jlcpcb-case-study
