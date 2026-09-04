# Pajoniiir-M1 — PCB Placement and Routing Constraints v0.2

**Updated:** 2026-09-04

**Milestone:** M1-PRELAYOUT-B5

**Status:** placement skeleton and routing topology validated; final placement/routing freeze blocked

**Machine authorities:** `pcb_constraints.json`, `m1_mech_b5_placement_skeleton.json`, `m1_prelayout_b5_routing_contract.json`

## Current PCB state

`Pajoniiir-M1.kicad_pcb` is intentionally an empty KiCad 9 four-copper-layer shell. It has no footprints, routes, zones or `Edge.Cuts`.

Current screening geometry:

| Item | Value | State |
|---|---:|---|
| Core mainboard | 104 x 62 mm | B3/B5 placement screen |
| Direct mount pattern | 58 x 49 mm | locked |
| Mainboard seating plane | Z = 10.0 mm | locked |
| Mainboard rear surface | Z = 11.6 mm | locked for 1.6 mm PCB |
| Enclosure candidate | 128 x 84 x 30 mm | screening only |
| Wall thickness | 2.0 mm | screening only |

The legacy 108 x 65.06 mm board rectangle and 121.008 x 73.408 mm enclosure belong to the rejected JC4880 geometry and have no current `Edge.Cuts` authority.

## Layer and stackup contract

Selected fabrication stackup:

```text
Fabricator         JLCPCB
Stackup            JLC04161H-7628
Finished thickness 1.6 mm
Outer copper       1 oz
Inner copper       0.5 oz
F.Cu to In1.Cu     0.2104 mm
Prepreg            7628, Er 4.4 screening value
Core Er            4.6 screening value
```

Layer roles:

```text
F.Cu   primary components + USB/MIPI/QSPI/SDIO critical routing
In1.Cu continuous solid GND reference; no split beneath critical routes
In2.Cu power distribution + compatible low-speed routing
B.Cu   secondary components and low-speed routing
```

Primary USB/MIPI routing belongs on F.Cu referenced to In1.Cu. Any required layer transition needs adjacent GND return vias and a recalculated geometry.

## Mechanical placement domains

Wall assignment is fixed for screening:

- top `Y_NEG`: J2 USB0, J3 USB1, J4 MAIN L RCA, J5 MAIN R RCA
- left `X_NEG`: J1 power input
- right `X_POS`: J7 microSD, SW1 RESET, SW2 BOOT and the guarded display FFC corridor
- bottom `Y_POS`: clear

The display-facing mainboard side is substantially component-free. J6 is the only planned exception and requires local FFC/collision validation. The rear/outward face is the primary component side.

## B5 top-wall screening anchors

These anchors prove feasibility only; they are not production XY:

| RefDes | Anchor X/Y mm | Rotation | Checked result |
|---|---:|---:|---|
| J2 | 19.51 / 3.90 | 180 deg | Amphenol courtyard fits USB window |
| J3 | 51.21 / 3.90 | 180 deg | 16.10 mm courtyard gap to J2 |
| J4 | 70.31 / 1.75 | 90 deg | Kycon courtyard fits RCA window |
| J5 | 82.51 / 1.75 | 90 deg | 1.00 mm courtyard gap to J4 |

Final screw-head/washer and panel-cutout checks remain required.

Right-side placement remains deliberately unanchored:

```text
SW1/SW2 recovery zone   Y 7.5 .. 21.0 mm
guarded FFC corridor    Y 22.07 .. 42.07 mm
J7 microSD zone         Y 43.0 .. 61.0 mm
```

J7, SW1 and SW2 must be solved together with the right-side wing, card insertion/ejection, lower-right mounting screw and 60 x 15 mm FFC U-bend.

J1 remains unanchored until the Switchcraft 722RAHLP terminal-center geometry, left-side wing and panel/cable envelope are authoritative.

## Critical routing targets

### USB0 High-Speed

- 90 ohm differential
- J2 -> D2 ESD -> series tuning -> U1, no stubs
- D2 immediately behind J2
- avoid layer changes and In1 plane voids
- keep away from switch nodes and high-current return bottlenecks

### USB1 Full-Speed

- preserve 90 ohm differential geometry
- J3 -> D3 ESD -> optional tuning -> U1
- 22 ohm source series remains populated
- DNP shunt capacitors must be symmetric if enabled
- avoid switch nodes

### MIPI DSI

- 100 ohm differential
- U1 -> six strictly inline 0 ohm positions -> J6
- intra-pair skew maximum 0.254 mm
- pair-to-pair target maximum 0.762 mm
- avoid layer changes and all tee stubs
- preserve a continuous In1 GND reference

### Other critical domains

- Keep U2/QSPI tuning elements in a compact U1-local island.
- Keep U4 close enough for compact SDIO escape while preserving the official all-layer RF keepout.
- Keep J7/U13 in the lower-right media domain and do not route through the FFC corridor.
- Keep U5 and the output RC/RCA network away from switching nodes and USB VBUS return bottlenecks.
- Preserve Kelvin sense routing around R120 independently of generic high-current copper.

## Impedance gate

Current screening values:

| Class | Target | Width | Edge gap | Other-copper clearance |
|---|---:|---:|---:|---:|
| USB0/USB1 | 90 ohm diff | 0.2332 mm | 0.15 mm | 0.30 mm |
| MIPI DSI | 100 ohm diff | 0.1722 mm | 0.15 mm | 0.30 mm |

These values are suitable for placement/channel budgeting only. Before routing freeze:

1. record a current JLCPCB calculator result for JLC04161H-7628
2. record selected width/gap for 90 ohm and 100 ohm classes
3. record the soldermask/model option used for fabrication
4. apply exact values to KiCad net classes/custom rules
5. run PCB DRC and preserve the stackup in fabrication notes

## Power routing

```text
J1 -> U7 eFuse -> R120 Kelvin shunt -> 5V_SYS
                                      +-> U8 3V3
                                      +-> U6/U12 USB VBUS
```

J1 routing cannot freeze before its footprint. C3/C8 routing cannot freeze before EVT selects exact production packages. USB VBUS branches require a final copper-width/current-density and thermal review.

## Freeze rule

Final placement/routing requires:

1. all 12 `blocks_layout_freeze` gates closed
2. final enclosure, side wings/notches, mounting hardware and `Edge.Cuts`
3. absolute connector centers, cutouts and mated plug/cable envelopes
4. DSI FFC pin-1 and bend/removal proof plus absolute J6 placement
5. C3/C8 production selection from EVT evidence
6. exact production impedance rules
7. completed placement review, PCB DRC and power-copper review

`edge_cuts_allowed`, `routing_freeze_allowed` and `fabrication_release_allowed` remain false.
