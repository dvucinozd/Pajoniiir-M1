# Pajoniiir-M1 — Mechanical and Sourcing Gates v0.3

**Updated:** 2026-09-06
**Mechanical milestone:** M1-MECH-B7
**Status:** board-first authority locked; layout freeze blocked
**Machine authority:** `hardware/Pajoniiir-M1/mechanical_gates.json`

## Current conclusion

The mainboard is the mechanical authority. No display model defines its outline, mounting pattern, connector walls or Z stack. DSI506 geometry and the former B2-B6 direct-mount studies are historical profile evidence only.

```text
layout_freeze_allowed  false
open blockers          12
closed gates           4
blank BOM gates        3
```

Most external connector MPNs and footprints are selected, but panel centers and board placement remain open. The final board envelope must come from complete component packing, critical-route feasibility, thermal/height zoning, connector service access and an independent chassis mount.

## Closed gates

| Gate | Closure |
|---|---|
| `D1_INPUT_TVS` | SMBJ6.0CA-TR / `Diode_SMD:D_SMB` |
| `J6_LINE35` | optional 3.5 mm line output removed from Rev A |
| `J9_USB_SERVICE_POGO` | project-local 1x05 factory pogo footprint, DNL |
| `FAB_STACKUP` | JLCPCB JLC04161H-7628, four layers, 1.6 mm |

## Open component and connector gates

### C3 and C8

The current 330 uF values are tuning baselines. Startup/inrush and worst-case rail transient tests must establish capacitance, ESR and ripple-current targets. The board-first placement study must establish the available package and height envelope.

### J1 power input

Switchcraft 722RAHLP with S760KHZ mating plug is the selected production intent. The footprint stays blank until the terminal centers are resolved without inference. Closure also needs board-edge placement, panel engagement, reinforcement, polarity marking and the full mated cable/strain envelope.

### J2/J3 USB, J4/J5 RCA, J7 microSD and SW1/SW2

Exact part and footprint intent is retained. Each gate remains open for board-local placement, chassis cutout, full mated/user-access envelope and local routing/courtyard clearance. No former B3 wall assignment or B5 anchor is production authority.

### J6 DSI host

J6 is a generic 15-pin Raspberry-Pi-style MIPI DSI host. Amphenol SFW15R-2STE1LF and its project footprint are locked. Clock, lane 0, lane 1, display I2C and `3V3_DISPLAY_MODULE` are captured.

Closure requires:

1. service-accessible board-edge placement with a viable U1-to-J6 MIPI route;
2. generic insertion/removal clearance in the board chassis;
3. startup/transient power budget for the supported display matrix;
4. a cable or adapter orientation record for every supported display profile.

DSI506 Type-B cable and rear-board geometry belong only to its compatibility profile.

### PCB outline

Closure requires:

- complete footprint/courtyard packing;
- a board-owned chassis mounting pattern and edge clearances;
- power, USB, MIPI, SDIO, QSPI and audio routing feasibility;
- thermal and component-height zones;
- external connector cutouts and full mated cable/service envelopes;
- manufacturing panelization and assembly review.

## Freeze rule

Final placement/routing freeze is allowed only after all 12 blocking gates close and exact 90 ohm USB / 100 ohm MIPI geometry is recorded for the locked stackup. Until then, no final `Edge.Cuts`, Gerber or EVT order may be described as release-ready.
