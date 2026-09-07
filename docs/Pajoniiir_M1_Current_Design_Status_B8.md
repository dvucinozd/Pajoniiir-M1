# Pajoniiir-M1 current design status B8

**Date:** 2026-09-06

**Electrical milestone:** M1-ELEC-B2

**Mechanical milestone:** M1-MECH-B7

**Pre-layout milestone:** M1-PRELAYOUT-B8

**Layout state:** populated board-first placement canvas; `layout_freeze_allowed=false`

## Product boundary

Pajoniiir-M1 is the primary product assembly: a standalone ESP32-P4 mainboard. Its PCB outline, mounting holes, connector locations, height zones and enclosure datums must be derived from the board's own component packing, routing, thermal, service and manufacturing requirements.

The screen is a replaceable external peripheral. No display PCB, display mounting-post pattern or display enclosure may define the M1 board geometry.

The active machine authority is `hardware/Pajoniiir-M1/board_first_mechanical_contract.json`. `mech_a.json`, `mechanical_gates.json` and `pcb_constraints.json` are synchronized to that boundary.

## Electrical state

The hierarchical KiCad design contains 15 leaf sheets. Current structural validation passes with all 15 sheets and the intentional blank-footprint policy remains limited to J1, C3 and C8. Local KiCad 10 ERC previously passed with zero violations after power-good test points, no-connect markers and library closure were added.

The board retains these main functions:

- ESP32-P4 with ESP32-C6 over four-bit SDIO
- independent USB host ports and switched VBUS branches
- PCM5102A stereo MAIN output
- native four-bit SDMMC microSD
- power protection, current measurement and power-good diagnostics
- generic 15-pin Raspberry-Pi-style MIPI DSI host interface

## Display interface and compatibility

J6 is the board interface, using Amphenol `SFW15R-2STE1LF`, 15 contacts at 1.0 mm pitch, top contact, right-angle SMT ZIF. The locked electrical map routes DSI clock, lane 0, lane 1, shared display I2C and `3V3_DISPLAY_MODULE`.

EYOYO DSI506 / DYL0023 is one validated compatibility profile. Pajoniiir-M3 evidence confirms its electrical map and operating profile, and the supplied photos confirm its Type-B FFC construction. Those facts do not make DSI506 the final product display or the mechanical datum for M1.

Every additional display model must qualify:

- the same 15-pin electrical map, or an explicit adapter;
- startup, steady-state and transient current on `3V3_DISPLAY_MODULE`;
- DSI lanes, rate, pixel format and timing;
- touch/controller I2C behavior where used;
- cable contact orientation, insertion and service envelope.

Type-B is a DSI506 cable fact, not a universal M1 requirement. The board-side connector remains fixed; a cable or adapter profile resolves model-specific orientation.

## Mechanical rebase

The following values are retained only as DSI506-specific or historical screening evidence:

- 58 x 49 mm DSI506 rear-post pattern;
- 104 x 62 mm display-derived board screen;
- 128 x 84 x 30 mm display-derived enclosure screen;
- the 1.4455 mm DSI506 right-edge FFC clearance result;
- all JC4880 enclosure, mount and Z-stack geometry.

They are forbidden as production `Edge.Cuts`, mainboard mounting or connector-placement authority. The B2 through B6 display-specific records remain useful when designing a DSI506 bracket, cable kit or enclosure variant.

The board outline and its chassis mounting pattern remain open. `m1_board_packing_inventory_b7.json` closed the inventory step with 247 schematic components, 244 assigned footprints, 3 intentional blank footprints and 33 footprint classes including the blank-gate class.

M1-PRELAYOUT-B8 now populates the live PCB with all 244 assigned footprints and 193 named schematic nets. Eight `Dwgs.User` rectangles separate the working electrical domains: power spine, USB edges, audio, P4 core, C6 RF, DSI host, storage and service. There are no footprint bounding-box overlaps, tracks, zones or `Edge.Cuts`. These rectangles and their XY coordinates are a reversible working canvas, not connector, mounting or enclosure datums.

## Locked and open items

Locked today:

- electrical connectivity and current 15-sheet hierarchy;
- J6 part, footprint and 15-pin electrical map;
- JLCPCB `JLC04161H-7628` four-layer, 1.6 mm stackup;
- most external connector MPN and footprint intent;
- DSI506 electrical/firmware compatibility profile;
- `layout_freeze_allowed=false` while blockers remain.

The 12 layout blockers remain:

```text
C3_INPUT_BULK
C8_PROTECTED_BULK
J1_POWER_INPUT
SW1_RESET
SW2_BOOT
J2_USB0
J3_USB1
J4_RCA_L
J5_RCA_R
J_LCD_DISPLAY_FPC
J7_MICROSD
PCB_OUTLINE
```

The meaning of the last two gates changed at B7. `J_LCD_DISPLAY_FPC` now asks for board-edge J6 placement, generic service access, branch power qualification and per-display cable profiles. `PCB_OUTLINE` now asks for a board-owned outline and chassis mount derived from completed packing and routing evidence.

## Next board work

1. Tighten the P4 core and flash island around U1 using the Espressif escape and decoupling constraints; keep all B8 coordinates movable.
2. Place U4 at a candidate outer edge, preserve its all-layer antenna keepout and prove the four-bit SDIO escape to U1.
3. Compact the power spine and connector domains around those two critical islands, then derive a minimum feasible board envelope.
4. Add an independent chassis mounting-hole pattern and validate mated cables, height zones and thermal clearance.
5. Close J1/C3/C8 EVT and exact controlled-impedance geometry before final routing freeze.

No Gerber or EVT order is authorized while the outline and blocking gates remain open.

## Validation

```bash
python hardware/Pajoniiir-M1/tools/validate_schematic_structure.py
python hardware/Pajoniiir-M1/tools/validate_mechanical_authority.py
python hardware/Pajoniiir-M1/tools/validate_board_packing_inventory.py
python hardware/Pajoniiir-M1/tools/report_mech_gate_snapshot.py
"C:/Program Files/KiCad/10.0/bin/python.exe" hardware/Pajoniiir-M1/tools/validate_board_placement_b8.py \
  --board hardware/Pajoniiir-M1/Pajoniiir-M1.kicad_pcb \
  --netlist <fresh-kicad-xml-netlist> \
  --report hardware/Pajoniiir-M1/m1_board_placement_seed_b8.json
```

The former B4 panel-window and B5 display-mounted placement validators are no longer CI gates because their coordinate systems were tied to DSI506. Their JSON outputs are explicitly marked historical screening only.
