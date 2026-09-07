# Pajoniiir-M1 — PCB Placement and Routing Constraints v0.3

**Updated:** 2026-09-06
**Milestone:** M1-MECH-B7 board-first pre-layout
**Status:** routing topology retained; production placement and outline open
**Machine authorities:** `board_first_mechanical_contract.json`, `pcb_constraints.json`, `mechanical_gates.json`, `m1_prelayout_b5_routing_contract.json`

## Current PCB state

`Pajoniiir-M1.kicad_pcb` is a four-copper-layer pre-layout shell with no production footprint placement, routes, zones or `Edge.Cuts`.

There is no active board width, height, mount pattern or enclosure envelope. Former 104 x 62 mm, 58 x 49 mm and 128 x 84 x 30 mm values were derived from DSI506 and are historical screening only.

## Layer and stackup contract

```text
Fabricator         JLCPCB
Stackup            JLC04161H-7628
Finished thickness 1.6 mm
Outer copper       1 oz
Inner copper       0.5 oz
F.Cu to In1.Cu     0.2104 mm
```

```text
F.Cu   primary components + USB/MIPI/QSPI/SDIO critical routing
In1.Cu continuous solid GND reference
In2.Cu power distribution + compatible low-speed routing
B.Cu   secondary components and low-speed routing
```

## Board-first placement order

1. Place U1 and its mandatory decoupling, flash and DSI_REXT networks.
2. Establish compact QSPI and ESP32-C6 SDIO islands with the C6 RF keepout.
3. Place power entry, eFuse, Kelvin shunt, 3V3 converter and switched USB power branches.
4. Place J2/J3 with ESD parts and prove the USB routes.
5. Place J6 on a service-accessible edge and prove the 100 ohm U1-to-J6 DSI corridor.
6. Place microSD, PCM5102A/audio outputs and service interfaces while preserving return-current and noise boundaries.
7. Derive the minimum feasible outline, board-owned chassis holes and component-height zones from the resulting packing.

External connector wall assignment follows the product chassis. Former B3/B5 wall coordinates are not production placement.

## Critical routing targets

- USB0: 90 ohm differential; J2 -> D2 -> tuning -> U1, no stubs.
- USB1: preserve 90 ohm differential symmetry; J3 -> D3 -> tuning -> U1.
- MIPI DSI: 100 ohm differential; U1 -> six inline 0 ohm links -> J6; 0.254 mm maximum intra-pair skew and 0.762 mm pair-to-pair target.
- QSPI/SDIO: compact escapes and continuous return reference; preserve the C6 all-layer RF keepout.
- Audio: keep U5 and analog output network away from switch nodes and USB VBUS return bottlenecks.
- Power: preserve Kelvin sensing around R120 and review copper/current density after the outline stabilizes.

Current width/gap numbers in `m1_prelayout_b5_routing_contract.json` are screening values only. Record current JLCPCB calculator output and apply exact KiCad rules before route freeze.

## Freeze requirements

1. all 12 `blocks_layout_freeze` gates closed;
2. board-owned `Edge.Cuts`, chassis mount and height zones validated;
3. complete courtyard and critical-route feasibility pass;
4. absolute connector centers plus cutout/mated cable service envelopes;
5. J6 power budget and per-display cable/adapter profiles;
6. C3/C8 exact production selection from EVT;
7. exact 90 ohm USB and 100 ohm MIPI geometry committed.
