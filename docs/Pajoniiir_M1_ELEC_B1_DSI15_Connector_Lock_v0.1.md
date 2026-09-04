# Pajoniiir-M1 — M1-ELEC-B1 15-pin DSI Connector Lock v0.1

**Date:** 2026-09-04  
**Revision:** M1-ELEC-B1  
**Status:** connector MPN, contact side and drawing-derived project footprint locked; physical cable integration remains gated

## Decision

Final host-side DSI connector:

```text
Manufacturer  Amphenol Communications Solutions / FCI
MPN           SFW15R-2STE1LF
Contacts      15
Pitch         1.00 mm
Contact side  TOP
Entry         right-angle / side-entry
Mount         SMT
Insertion     ZIF
Height        2.70 mm
```

The exact Amphenol part is Active and has a released customer drawing. Raspberry Pi's Compute Module Camera/Display Adapter reference package uses this 15-way 1.0 mm top-contact part for the standard Raspberry-Pi-style DSI/CSI interface.

## Locked M1 pin map

```text
 1  GND
 2  DSI_D1_N
 3  DSI_D1_P
 4  GND
 5  DSI_CLK_N
 6  DSI_CLK_P
 7  GND
 8  DSI_D0_N
 9  DSI_D0_P
10  GND
11  DISPLAY_I2C_SCL / GPIO8
12  DISPLAY_I2C_SDA / GPIO7
13  GND
14  3V3_DISPLAY_MODULE
15  3V3_DISPLAY_MODULE
```

This map comes from the same DSI506/DYL0023 interface already accepted on real hardware in Pajoniiir-M3.

## Cable rule

`TOP contact` describes the receptacle. It does not prove the exposed-conductor orientation of the particular supplied FFC at both ends. Before production placement, verify actual cable pin 1 and conductor side so host pin 1 reaches module pin 1.

## Footprint closure

M1-ELEC-B2 imported/reconstructed the project footprint from the released Amphenol recommended PCB layout and checked it against drawing `10172241`. The locked footprint is:

`hardware/Pajoniiir-M1/libraries/footprints.pretty/Amphenol_SFW15R-2STE1LF.kicad_mod`

It is instantiated on J6 in `10_DISPLAY_MIPI.kicad_sch`. Future footprint changes require a fresh drawing comparison and mechanical review.

## Remaining connector gate

Only these connector-specific items remain:

1. physical cable inversion / pin-1 continuity check;
2. FFC bend, insertion and removal keepout;
3. final connector XY/Z placement relative to the display and custom mainboard.

## Sources

- https://www.amphenol-cs.com/product/sfw15r2ste1lf.html
- https://cdn.amphenol-cs.com/media/wysiwyg/files/drawing/10172241.pdf
- https://datasheets.raspberrypi.com/cmcd/CMCD-A-1P1.zip
- `dvucinozd/Pajoniiir-M3@b3e2bee5ded0a836906ab6f689d79a6e6b49d541`
