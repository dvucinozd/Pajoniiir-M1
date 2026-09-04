# Pajoniiir-M1 — Mechanical and Sourcing Gates v0.2

**Updated:** 2026-09-04

**Mechanical milestone:** M1-MECH-B5

**Status:** source and screening decisions advanced; final layout freeze blocked

**Machine authority:** `hardware/Pajoniiir-M1/mechanical_gates.json`

## Current conclusion

The final DSI506 display, direct four-post mainboard mount, B3 board/enclosure screens, three-wall I/O assignment, most external connector MPNs/footprints and the B5 top-wall placement skeleton are defined.

This does not close the corresponding connector gates. Absolute panel datums, cutouts, mated cable envelopes, local clearances and final `Edge.Cuts` still require physical/CAD evidence.

Current state:

```text
layout_freeze_allowed  false
open blockers          12
closed gates           4
blank BOM gates        3
```

## Mechanical baseline

Active display and mount:

```text
Display                 EYOYO DSI506 / DYL0023, 5-inch 800 x 480
Rear PCB                 121.109 x 77.193 mm nominal evidence
Front glass              120 x 75 mm
Visible window           110 x 67 mm at x=5, y=2 mm
Direct mount             four M2.5 posts, 58 x 49 mm
Usable thread depth      3.0 mm
Mainboard seating plane  Z=10.0 mm
Mainboard rear surface   Z=11.6 mm for 1.6 mm PCB
```

The B3 core board screen is 104 x 62 mm. The compact enclosure screen is 128 x 84 x 30 mm with 2 mm walls. Both remain non-production candidates.

The former 121.008 x 73.408 mm JC4880 enclosure is a hard fail for the DSI506 and must not be used for current board geometry.

## Closed gates

| Gate | Closure |
|---|---|
| `D1_INPUT_TVS` | SMBJ6.0CA-TR / `Diode_SMD:D_SMB` |
| `J6_LINE35` | optional 3.5 mm line output removed from Rev A |
| `J9_USB_SERVICE_POGO` | project-local 1x05 factory pogo footprint, DNL |
| `FAB_STACKUP` | JLCPCB JLC04161H-7628, four layers, 1.6 mm |

## Open gates

### C3 and C8 bulk capacitors

Current schematic value is a 330 uF tuning baseline. Closure requires startup/inrush and worst-case transient results, ESR/ripple-current targets and an available mechanical envelope before exact MPN/footprint selection.

### J1 power input

Production intent is Switchcraft 722RAHLP with S760KHZ mating plug. The MPN is locked. The footprint remains blank because the released drawing has not yet yielded an unambiguous three-terminal center-coordinate interpretation without inference.

Closure also requires the left-wall cutout, nut/washer/bushing engagement, reinforcement, plug/cable strain envelope and polarity marking.

### J2/J3 USB host

Both ports use Amphenol 87520-1010ALF with a manufacturer-checked project footprint. Remaining work is final top-wall center spacing, cutouts, insertion clearance, screw-head clearance and full USB plug/cable envelopes.

### J4/J5 RCA

J4 uses Kycon KLPX-0848A-2-W-G and J5 uses KLPX-0848A-2-R-G with the locked project footprint. Closure needs final panel centers/cutouts, shell isolation decision and mated RCA plug/cable envelopes.

### J6 display FFC

The active display connector is Amphenol SFW15R-2STE1LF, 15 contacts, 1.0 mm, top-contact, right-angle SMT ZIF. Its footprint is locked and instantiated.

Remaining evidence:

1. actual host-to-module pin-1 continuity/orientation
2. physical 60 x 15 mm FFC U-bend, insertion and removal keepout
3. absolute J6 XY/Z placement relative to the display and custom mainboard

The former SOFNG 30-pin JC4880 connector is historical evidence only.

### J7 microSD

J7 uses Molex 503398-1892 with a drawing-checked project footprint. Closure requires the right-wall slot center/opening, card insertion/ejection and finger access, lower-right mounting-screw clearance, and physical coexistence with the guarded FFC corridor.

### SW1/SW2 recovery switches

Both use B3U-3000P-B and the exact standard KiCad footprint. Closure requires two separate recessed tool-hole centers, actuator-to-wall/tool geometry, spacing that prevents simultaneous actuation, and clearance to J7, FFC and mounting hardware.

### PCB outline

The 104 x 62 mm core rectangle is a B3/B5 screening envelope only. Closure requires:

- final enclosure walls, bosses, ribs and rear cover
- final board side wings/notches and dimensions
- final mounting-hole diameter and screw head/washer geometry
- display rear-obstruction map
- all connector cutouts and mated cable envelopes
- DSI FFC approach/bend envelope
- final PCB Z and rear-cover clearance

## B5 placement-screen result

The top-wall J2/J3/J4/J5 anchor set passes courtyard and provisional screw-center screens. J7/SW1/SW2 and J1 intentionally remain unanchored until their side-wing/panel evidence exists.

This proves the three-wall architecture is viable enough to continue CAD screening. It does not create production connector centers or `Edge.Cuts`.

## Fabrication and routing boundary

The fabrication stackup gate is closed. Controlled impedance remains open:

- USB0/USB1: 90 ohm differential
- MIPI DSI: 100 ohm differential
- current values in the B5 routing contract are screening geometry only

Exact JLCPCB calculator output, soldermask/model settings and corresponding KiCad rules are required before routing freeze.

## Freeze rule

Final placement/routing freeze is allowed only when every open `blocks_layout_freeze` gate is closed and the production impedance geometry is committed. Until then:

- B5 anchors remain screening locations
- the 104 x 62 mm core remains a screening envelope
- no final `Edge.Cuts` may be added
- no Gerber or EVT PCB order may be described as release-ready
