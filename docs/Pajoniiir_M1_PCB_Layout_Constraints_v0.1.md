# Pajoniiir-M1 — PCB Placement & Routing Constraints v0.1

**Datum:** 2026-09-03  
**State:** Pre-mechanical layout / electrical constraints locked  
**Machine-readable authority:** `hardware/Pajoniiir-M1/pcb_constraints.json`

---

## 1. What is locked now

The existing `Pajoniiir-M1.kicad_pcb` is intentionally only a KiCad 9 four-copper-layer shell. It is not a routed board and its 1.6 mm thickness is not an impedance authority.

What is locked before mechanics:

- functional placement domains
- high-current power-spine order
- RF keepout intent
- connector-side ESD placement order
- source-series placement intent
- USB and MIPI differential-impedance targets
- sensitive/switching-domain separation rules
- Kelvin shunt measurement topology

What is **not** locked:

- Edge.Cuts
- board X/Y
- mounting holes
- connector X/Y/Z
- layer dielectric thicknesses
- trace width/gap values
- final via geometry
- copper weights
- finished PCB thickness

---

## 2. Logical four-layer intent

Preferred role assignment:

~~~text
L1 / F.Cu   components + critical signals
L2 / In1.Cu continuous GND reference
L3 / In2.Cu power distribution + low-speed signals
L4 / B.Cu   secondary signals/components + compatible GND fill
~~~

The layer **roles** are electrical intent. Actual dielectric spacing must come from the chosen fabricator before any controlled-impedance width/gap is frozen.

---

## 3. Critical routing targets

### USB0 High-Speed

- 90 ohm differential, ±10%
- series elements near ESP32-P4
- D2 TPD2EUSB30A immediately adjacent to J2
- minimal vias
- no stubs
- continuous adjacent GND reference
- do not cross backlight/buck switching-node return discontinuities

### USB1 Full-Speed

- preserve 90 ohm differential geometry
- source series near P4
- D3 at J3
- optional shunt capacitors remain DNP unless EMI validation requires them
- any populated shunt pair must be symmetric

### MIPI DSI

- 100 ohm differential, ±10%
- intra-pair skew target <10 mil
- pair-to-pair target <30 mil
- six 0R tuning positions remain strictly inline
- minimal layer changes
- continuous GND reference
- keep DSI corridor away from U9/L3/D4 switching zone

Exact width/gap is **TBD-STACKUP**, not a schematic constant.

---

## 4. Placement topology

### Compute island

U1 ESP32-P4 central. U2 flash, U3 core buck/L1 and Y1 remain close to U1 according to their critical loops.

### RF island

U4 ESP32-C6-WROOM antenna must sit at a board edge with official copper keepout on every layer. No connector shell, cable or enclosure metal may intrude without RF revalidation.

### 5 V spine

~~~text
J1 -> U7 eFuse -> R120 Kelvin shunt -> 5V_SYS
                                      |
                    +-----------------+------------------+
                    |                 |                  |
                   U8                U6/U12             U9
                  3V3               USB VBUS         backlight
~~~

R120 Kelvin sense taps must not share generic high-current branch copper.

### USB edge zones

J2/J3 are mechanical-edge anchors once their MPNs are known. D2/D3 live directly behind the connector shell; power switches U6/U12 remain on the high-current side of those ports.

### Audio zone

U5 plus output RC network and J4/J5/J6 form a quiet edge domain. Keep it away from U8/U9 switch nodes and from USB VBUS high-current bottlenecks.

### Display zone

DSI is a quiet high-speed corridor. Backlight U9/L3/D4 is a separate noisy power island even though both serve the display assembly.

### microSD

U13 and J7 form a user-accessible edge domain after card insertion mechanics are known.

---

## 5. Mechanical dependency

No user-facing connector may be assigned a final production location or footprint until the corresponding gate in `mechanical_gates.json` is closed.

This specifically prevents provisional J1/J2/J3/J4/J5/J6/J7/SW1/SW2 choices from silently becoming manufacturing defaults.

---

## 6. PCB freeze gate

Final layout freeze requires all of the following:

1. every `blocks_layout_freeze` mechanical gate closed
2. authoritative Edge.Cuts/mounting datums
3. connector and display Z/X/Y clearance review
4. chosen fabricator stackup
5. calculated 90 ohm USB / 100 ohm MIPI width-gap geometry
6. final power-copper/current-density review
7. KiCad PCB DRC and manufacturing output review

Until then, exploratory electrical clustering is allowed, but Gerbers/EVT ordering is not.
