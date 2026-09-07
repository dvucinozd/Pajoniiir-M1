# Pajoniiir-M1 Rev A — Readiness Review v0.2

**Updated:** 2026-09-04

**Electrical milestone:** M1-ELEC-B2

**Mechanical milestone:** M1-MECH-B7

**Pre-layout milestone:** M1-PRELAYOUT-B5

**Status:** schematic ready; production PCB layout and fabrication release not ready

## Executive verdict

The Rev A electrical design is captured in the 15-sheet KiCad hierarchy and passes local structural, native KiCad 10.0.4 ERC and manufacturing-output checks. Fresh KiCad 9 CI is pending after the [PG/library changes](Pajoniiir_M1_ERC_Library_Closure_2026-09-04.md). The B7 rebase makes the mainboard independent of display geometry. The user-confirmed DSI506 height remains profile evidence only.

```text
KiCad files loaded       16/16 PASS
ERC                      0 unexplained / 0 excluded / 0 warnings
Manufacturing BOM        244 source / 244 export PASS
DNP                      15
Blank-footprint gates     3
Mechanical blockers      12
Layout freeze             false
```

The design is ready for controlled exploratory placement and physical closure work. It is not ready for final placement, controlled-impedance routing, Gerbers or an EVT PCB order.

## Authority order

1. live KiCad schematic sources
2. `mechanical_gates.json`
3. `pcb_constraints.json` and the routing contract
4. B4 connector source lock
5. display compatibility profiles
6. historical display-mounted screening records
7. `Pajoniiir_Mainboard_BOM_v0.3.md`
8. global GPIO and hardware/firmware contracts
9. subsystem documents
10. explicitly superseded JC4880/M1-MECH-A documents as history only

## Completed electrical scope

| Block | Current state |
|---|---|
| 5 V input/eFuse | captured; D1 locked; J1/C3/C8 production packages open |
| 3.3 V system rail | captured around TPS62132 |
| ESP32-P4 v3.x core | captured with v3.x power/feedback contract |
| Flash/clock/boot | captured |
| ESP32-C6 SDIO/Wi-Fi | captured; RF placement/EVT open |
| USB0/USB1 VBUS | independent TPS25221 paths captured |
| USB0 HS data | captured; J2 footprint locked |
| USB1 FLX4 FS data | captured; J3 footprint locked |
| PCM5102A MAIN output | captured; J4/J5 footprints locked |
| Generic 15-pin DSI host | captured; J6 MPN/pin map/footprint locked |
| Touch/backlight | module-integrated over display I2C |
| microSD | captured; J7 footprint locked |
| Debug/service | captured; J9 gate closed |
| Power monitoring | INA238 and Kelvin shunt captured |
| DNP/DNL policy | captured and CI-checked |

## Current DSI interface readiness

The board provides a generic 15-pin Raspberry-Pi-style DSI host using Amphenol SFW15R-2STE1LF, 15 contacts, 1.0 mm, top-contact and right-angle. DSI506/DYL0023 is one validated display profile.

Electrical pin map, module power, DSI lanes and shared I2C are locked. The initial M3-derived firmware profile is also defined.

Remaining display work is physical:

- board-edge J6 placement and viable MIPI route
- generic insertion/removal service clearance
- per-display cable or adapter orientation
- supported-display startup/transient power budget

The retired ST7701S/GT911/MP3202 architecture is not a current blocker and must not be reintroduced.

## Current connector readiness

| Group | MPN | Footprint | Remaining work |
|---|---|---|---|
| J1 | Switchcraft 722RAHLP | open | unambiguous pad centers, wall/cutout and plug geometry |
| J2/J3 | Amphenol 87520-1010ALF | locked | final top-wall centers/cutouts/cables |
| J4/J5 | Kycon KLPX-0848A-2-W-G / -R-G | locked | final centers/cutouts/mated plugs |
| J6 | Amphenol SFW15R-2STE1LF | locked | board-edge placement, power budget and display-profile cables |
| J7 | Molex 503398-1892 | locked | slot, card access, screw and FFC clearance |
| SW1/SW2 | B3U-3000P-B | locked | recessed tool holes and local clearance |

Connector sourcing is substantially closed. The remaining gates are placement and enclosure integration gates.

## Mechanical readiness

Locked:

- mainboard is a standalone assembly
- display models cannot define board `Edge.Cuts`, mounts or connector coordinates
- JLCPCB four-layer 1.6 mm stackup
- J6 connector, footprint and 15-pin electrical map
- exact external connector part intent where recorded

Open:

- board-owned chassis mounting pattern and screw keepouts
- complete footprint/courtyard packing and critical-route feasibility
- component-height and thermal zones
- absolute panel datums and cutouts
- enclosure bosses/ribs/rear cover and thermal/ventilation review
- final `Edge.Cuts`

The former DSI506-derived board, mount and enclosure dimensions are historical profile screening and cannot constrain the production mainboard.

## Stackup and routing readiness

JLCPCB JLC04161H-7628 is locked as the four-layer, 1.6 mm fabrication stackup. Layer roles and critical route topology are locked.

Production impedance geometry remains open. Current 0.2332/0.15 mm USB and 0.1722/0.15 mm MIPI width/gap values are screening inputs only. A direct current JLCPCB calculator record and matching KiCad rules are required before route freeze.

## EVT choices still open

- C3/C8 production capacitance technology, ESR, ripple rating, MPN and package
- final USB current limits against measured devices
- 3.3 V all-on load and display transient margin
- RF performance in the final enclosure
- audio noise/pop behavior under display, USB and Wi-Fi activity
- microSD power-cycle and signal-integrity tuning
- crystal and optional tuning-element selections

Only C3/C8 currently block footprint completion. The remaining electrical items are validation gates for release quality.

## Go / no-go

| Activity | State |
|---|---|
| Schematic changes and ERC | GO |
| Manufacturing BOM/netlist/PDF generation | GO |
| Mechanical CAD and physical evidence capture | GO |
| Exploratory B5 placement | GO with screening labels |
| Final connector XY and `Edge.Cuts` | NO-GO |
| Final USB/MIPI routing | NO-GO |
| Gerbers / EVT board order | NO-GO |

## Next milestone

Close the remaining physical/EVT gates in this order:

1. J1 land pattern evidence
2. DSI FFC pin-1 continuity and bend/removal proof
3. local display obstruction map
4. enclosure walls/bosses/rear cover and absolute panel datums
5. screw/NPTH and final side-wing/outline geometry
6. C3/C8 EVT production selection
7. exact controlled-impedance geometry and KiCad rules
8. final placement, routing, PCB DRC and manufacturing review
