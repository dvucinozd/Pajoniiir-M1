# Pajoniiir-M1 — M1-MECH-A Mechanical Baseline v0.1

**Datum:** 2026-09-03  
**Milestone:** M1-MECH-A  
**Status:** Display datum locked; legacy enclosure candidate validated; final PCB outline still open  
**Machine-readable authority:** `hardware/Pajoniiir-M1/mech_a.json`

---

## 1. Coordinate system

M1-MECH-A uses a front-facing, landscape device coordinate system:

~~~text
origin = center of nominal bare display front envelope
X+     = right
Y+     = down
Z+     = rear / inward
units  = mm
~~~

This is the mechanical reference frame for later connector, PCB and enclosure datums.

---

## 2. Manufacturer-locked display geometry

GUITION's official JC4880P443C_I_W/Y dimensional drawing gives:

| Item | Landscape X | Landscape Y | Status |
|---|---:|---:|---|
| Bare display/front envelope | 114.40 mm | 66.80 mm | locked reference |
| Active display area | 93.60 mm | 56.16 mm | locked reference |
| Module/shell envelope | 117.01 mm | 69.41 mm | legacy module reference |
| Rear shell reference | 108.00 mm | 65.06 mm | legacy module reference |

The original shell drawing also shows **4 × Ø2 mm** mounting holes on a **102.6 × 60.0 mm** center-spacing pattern. Relative to M1_FRONT_CENTER this corresponds to candidate centers:

~~~text
(-51.3, -30.0)
(+51.3, -30.0)
(-51.3, +30.0)
(+51.3, +30.0)
~~~

This pattern is authoritative for the original GUITION shell geometry. It is only a **candidate** for the new M1 custom-board mounting pattern until enclosure reuse is explicitly frozen.

Manufacturer source:

~~~text
JC4880P443C_I_W Specifications-EN-V1.0
Product Size, pages 6–7
https://www.guition.com/icms/upload/fb081940d6fc11f09850077a33e1404f/FTPData/UEditor/file/2026121/1768961095795/JC4880P443C_I_W%20Specifications-EN-V1.0.pdf
~~~

---

## 3. Legacy Blender correlation

Prior enclosure work used:

~~~text
D:\AI\BLENDER\flx4_0407.blend
~~~

Relevant recorded objects included:

~~~text
FINAL_PRINT_EXPORT_ONLY_ESP32_PCM_CASE_MODIFIED
middle_obj_FIT_TEST_ASSEMBLED
middle_obj_REFERENCE_LOCKED
~~~

The recorded fit-test module envelope was:

~~~text
117.008 × 69.408 × 13.900 mm
~~~

Manufacturer module reference:

~~~text
117.010 × 69.410 × 13.800 mm
~~~

Difference:

~~~text
X: -0.002 mm
Y: -0.002 mm
Z: +0.100 mm
~~~

That is a strong geometric correlation: the legacy Blender enclosure was built around this same JC4880 physical platform.

---

## 4. Legacy enclosure candidate

Recorded legacy outer case:

~~~text
121.008 × 73.408 × 30.000 mm
wall thickness = 2.0 mm
~~~

The X/Y envelope is exactly the recorded 117.008 × 69.408 mm module fit plus 2 mm wall on both sides.

M1-MECH-A therefore promotes this from "unknown old model" to:

**validated legacy enclosure candidate**

It is **not** yet final M1 authority. No Edge.Cuts is generated from it until PCB and connector clearance are demonstrated.

---

## 5. Useful legacy cutout evidence

Recorded legacy openings:

~~~text
RCA hole diameter      11.88 mm
RCA center spacing     19.20 mm
3.5 mm hole diameter    6.97 mm
main standoff height    6.00 mm
~~~

These values are preserved as enclosure evidence.

They do not lock J4/J5/J6 footprints because final connector center height, orientation, MPN and exact panel coordinates still depend on the M1 board.

---

## 6. Candidate M1 board bay

A conservative pre-layout **rear mechanical working envelope** is now defined:

~~~text
X max = 108.00 mm
Y max =  65.06 mm
~~~

The original 102.6 × 60.0 mm mounting-center pattern then sits 2.70 mm from the X edges and 2.53 mm from the Y edges of that reference envelope. This is internally consistent with the manufacturer drawing and avoids the earlier incorrect interpretation of 60 mm as the full available Y envelope.

This is a **candidate mechanical envelope**, not `Edge.Cuts`.

The current KiCad PCB shell must remain without final outline while:

~~~text
final_board_outline_locked = false
~~~

---

## 7. Coordinate extents now available

Relative to `M1_FRONT_CENTER`:

~~~text
validated legacy enclosure candidate:
X = -60.504 .. +60.504
Y = -36.704 .. +36.704
Z =   0.000 ..  30.000

bare display/front envelope:
X = -57.200 .. +57.200
Y = -33.400 .. +33.400
Z = 0

legacy module fit reference:
X = -58.504 .. +58.504
Y = -34.704 .. +34.704
Z =   0.000 ..  13.900

rear mechanical working-envelope candidate:
X = -54.000 .. +54.000
Y = -32.530 .. +32.530

legacy/mounting candidate centers:
(-51.3, -30.0)
(+51.3, -30.0)
(-51.3, +30.0)
(+51.3, +30.0)
~~~

This gives us a real datum tree for later connector coordinates without pretending that the PCB outline has already been chosen.

---

## 8. What M1-MECH-A has closed

- display/front-envelope family identified
- bare front envelope quantified
- active display size quantified
- legacy module/shell envelope quantified
- original shell mounting pattern quantified
- legacy Blender model correlated to the same physical platform
- external enclosure candidate quantified
- legacy RCA/3.5 mm cutout diameters preserved
- 6 mm legacy main standoff height preserved
- M1 mechanical coordinate system defined

---

## 9. What remains open

### PCB

- exact X/Y Edge.Cuts
- M1 mounting-hole pattern
- standoff/screw diameter for the new board
- final PCB Z plane in the 30 mm enclosure

### Display/FPC

- bare panel tail geometry
- contact-side orientation
- mating height
- 31/32 vs 30-contact interpretation
- pins 15/16/18/19
- 3V3 commonality

### User-facing I/O

- J1 5 V input location/MPN
- J2/J3 USB-A locations/MPNs
- J4/J5 RCA center locations/MPNs
- J6 retain/remove + MPN if retained
- J7 microSD insertion datum/MPN
- SW1/SW2 actuator access geometry/MPNs

---

## 10. Immediate next M1-MECH-A action

Use the 121.008 × 73.408 × 30 mm enclosure candidate and 108 × 65.06 mm rear mechanical working-envelope candidate to build the first connector-placement envelope.

No connector footprint is considered production-locked until its panel datum and mating clearance are defined.
