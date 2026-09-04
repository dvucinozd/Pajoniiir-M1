# Pajoniiir-M1 Rev A — Readiness Review v0.2

**Updated:** 2026-09-04

**Electrical milestone:** M1-ELEC-B2

**Mechanical milestone:** M1-MECH-B5

**Pre-layout milestone:** M1-PRELAYOUT-B5

**Status:** schematic ready; production PCB layout and fabrication release not ready

## Executive verdict

The Rev A electrical design is captured in the 15-sheet KiCad hierarchy and passes the current structural, native KiCad 9 ERC and manufacturing-output checks.

```text
KiCad files loaded       16/16 PASS
ERC                      0 unexplained / 0 excluded / 0 warnings
Manufacturing BOM        242 source / 242 export PASS
DNP                      15
Blank-footprint gates     3
Mechanical blockers      12
Layout freeze             false
```

The design is ready for controlled exploratory placement and physical closure work. It is not ready for final placement, controlled-impedance routing, Gerbers or an EVT PCB order.

## Authority order

1. live KiCad schematic sources
2. `mechanical_gates.json`
3. B5 placement and routing contracts
4. B4 connector source lock
5. B3 board/enclosure screening contracts
6. final-display and DSI506 evidence/lock contracts
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
| DSI506 display | captured; J6 MPN/pin map/footprint locked |
| Touch/backlight | module-integrated over display I2C |
| microSD | captured; J7 footprint locked |
| Debug/service | captured; J9 gate closed |
| Power monitoring | INA238 and Kelvin shunt captured |
| DNP/DNL policy | captured and CI-checked |

## Current display readiness

The final display is EYOYO DSI506 / DYL0023, 5-inch, 800 x 480. The active connector is Amphenol SFW15R-2STE1LF, 15 contacts, 1.0 mm, top-contact and right-angle.

Electrical pin map, module power, DSI lanes and shared I2C are locked. The initial M3-derived firmware profile is also defined.

Remaining display work is physical:

- host-to-module pin-1 continuity/orientation
- 60 x 15 mm Type-B FFC U-bend and insertion/removal keepout
- local display-side obstruction map
- absolute J6 placement in the final mainboard/enclosure geometry
- all-on/startup/transient display-rail EVT

The retired ST7701S/GT911/MP3202 architecture is not a current blocker and must not be reintroduced.

## Current connector readiness

| Group | MPN | Footprint | Remaining work |
|---|---|---|---|
| J1 | Switchcraft 722RAHLP | open | unambiguous pad centers, wall/cutout and plug geometry |
| J2/J3 | Amphenol 87520-1010ALF | locked | final top-wall centers/cutouts/cables |
| J4/J5 | Kycon KLPX-0848A-2-W-G / -R-G | locked | final centers/cutouts/mated plugs |
| J6 | Amphenol SFW15R-2STE1LF | locked | FFC continuity/bend/absolute placement |
| J7 | Molex 503398-1892 | locked | slot, card access, screw and FFC clearance |
| SW1/SW2 | B3U-3000P-B | locked | recessed tool holes and local clearance |

Connector sourcing is substantially closed. The remaining gates are placement and enclosure integration gates.

## Mechanical readiness

Locked:

- direct mainboard mount to four DSI506 inner posts
- M2.5 thread, 3.0 mm usable depth and 58 x 49 mm pattern
- Z=10.0 mm mainboard seating plane
- M2.5 x 4.0 mm screw-length baseline
- wall assignment for top/left/right/bottom
- 104 x 62 mm core placement screen
- B5 top-wall screening anchors

Open:

- production NPTH diameter and screw head/washer keepout
- local display obstruction map
- side wings/notches
- absolute panel datums and cutouts
- enclosure bosses/ribs/rear cover and thermal/ventilation review
- final `Edge.Cuts`

The 128 x 84 x 30 mm enclosure is a preferred compact screening envelope, not a production lock.

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
