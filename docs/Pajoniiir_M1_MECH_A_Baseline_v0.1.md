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

They do not lock J4/J5 footprints because final connector center height, orientation, MPN and exact panel coordinates still depend on the M1 board. The legacy 3.5 mm aperture remains historical evidence only; J6 was removed from Rev A in M1-MECH-A8.

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

## 8. Candidate Z-stack

Using the validated 30 mm legacy enclosure depth, 2 mm rear wall, final legacy 6 mm standoff decision and 1.6 mm PCB thickness:

~~~text
front/display plane                         Z =  0.0
legacy module back                         Z = 13.9

PCB front/component-side surface            Z = 20.4
PCB rear surface                            Z = 22.0

rear inner wall                             Z = 28.0
rear outer wall                             Z = 30.0
~~~

Therefore:

~~~text
gross front-side clearance under module = 20.4 - 13.9 = 6.5 mm
gross PCB-back to rear-inner clearance   = 28.0 - 22.0 = 6.0 mm
~~~

These are **gross geometric clearances**, not final allowed component heights. Screw heads, bosses, print tolerance, flex motion, adhesive and assembly clearance still need explicit margin.

A second important consequence is the front bezel: if the bare 114.40 × 66.80 mm display is centered in the 121.008 × 73.408 mm enclosure candidate, only **3.304 mm** nominal perimeter remains on each side. M1-MECH-A therefore treats the front face as display/touch-only; connectors belong on side/rear walls unless the enclosure is intentionally redesigned.

The legacy Blender fit also modeled exactly 117.008 × 69.408 mm of inner XY space around a 117.008 × 69.408 mm module reference — effectively zero nominal manufacturing clearance. That confirms the geometry but **does not** establish a printable/production fit tolerance.

---

## 9. M1-MECH-A0 PCB envelope candidate

For placement-feasibility work only, M1 now has a candidate PCB rectangle:

~~~text
108.00 x 65.06 mm
area = 7026.48 mm2

X = -54.000 .. +54.000
Y = -32.530 .. +32.530
~~~

Centered inside the modeled 117.008 x 69.408 mm inner cavity, this leaves nominal cavity clearance:

~~~text
X: 4.504 mm per side
Y: 2.174 mm per side
~~~

Candidate mounting centers remain X=+/-51.3 mm and Y=+/-30.0 mm with the original 2.0 mm hole reference. Relative to the candidate PCB, hole-center margins are 2.70 mm in X and 2.53 mm in Y. For an O2.0 mm hole this leaves 1.70 mm and 1.53 mm of geometric material from hole edge to board edge.

These values are not fabrication approval. Final screw size, plated/non-plated treatment, boss geometry and board-house edge rules still need review.

This candidate exists only in mech_a.json / documentation. CI rejects real Edge.Cuts while final_board_outline_locked=false.

---

## 10. Connector cluster baseline

Front Z=0 is now explicitly reserved for display/touch. User-facing connectors must use a side or rear surface unless the enclosure is redesigned.

### AUDIO_OUT — J4/J5 (J6 removed in M1-MECH-A8)

- legacy RCA hole diameter: 11.88 mm
- RCA center spacing: 19.20 mm
- minimum two-RCA aperture span from outer hole edge to outer hole edge: 31.08 mm
- legacy 3.5 mm aperture: 6.97 mm
- absolute centers remain open

### USB_HOST_PAIR — J2/J3

The old enclosure work carried a 34.0 mm center-spacing reference for the two USB openings. Because M1 changes the connector type to USB-A, this is preserved only as a spacing reference and is not a production cutout.

### POWER_IN — J1

Wall and center remain open. Prefer a wall/region that keeps the high-current path to U7/R120 short and does not interfere with USB cable insertion.

### REMOVABLE_STORAGE — J7

Wall and center remain open. Card insertion and extraction must be straight and externally accessible.

### RECOVERY_BUTTONS — SW1/SW2

Wall and centers remain open. Baseline intent is recessed/tool-accessible service controls, not prominent front-panel UI.

### FACTORY_SERVICE — J9

Rear/internal fixture access only; no normal-user aperture requirement.

No cluster receives an absolute wall assignment in this commit. The remaining datum must come from the legacy Blender geometry or an explicit M1 enclosure wall decision.

---

## 11. Critical fixed-part height screen

The 6.5 mm under-display value is a gross geometric cavity, not a production component-height limit.

Verified height-critical fixed parts:

| RefDes | Part | Datasheet/package max | Gross headroom vs 6.5 mm | Screen |
|---|---|---:|---:|---|
| U1 | ESP32-P4NRW32X / QFN104 | 0.90 mm | 5.60 mm | PASS |
| U4 | ESP32-C6-WROOM-1-N4 | 3.25 mm (3.1 +/- 0.15) | 3.25 mm | PASS |
| L1/L2 | XGL4030-222MEC | 3.10 mm Cmax | 3.40 mm | PASS |
| L3 | XGL4030-103MEC | 3.10 mm Cmax | 3.40 mm | PASS |

The known tallest fixed central part is therefore the C6 module at 3.25 mm maximum physical height, leaving 3.25 mm of gross geometric headroom.

This does **not** include solder/assembly tolerance, adhesive, FPC motion, printed enclosure variation, ribs/bosses or an engineering safety gap. The production allowable component height remains deliberately unlocked.

Remaining height risks are already represented by open gates: C3/C8 bulk capacitors, D1 package selection, all user-facing connectors/switches, and J_LCD mating geometry.

---

## 12. Legacy relative connector evidence

The original Blender work confirms a final qualitative correction sequence:

- RCA openings moved upward
- 3.5 mm opening moved downward
- USB opening(s) stayed at the existing location

This is preserved only as relative legacy evidence. It does not reveal the absolute wall or M1_FRONT_CENTER coordinates, so no connector datum is promoted from it.

A deterministic recovery procedure is now defined as **M1-MECH-A-D1** in `mech_a.json` and `Pajoniiir_M1_MECH_A_Datum_Extraction_v0.1.md`.

---

## 13. What M1-MECH-A has closed

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

## 14. What remains open

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
- J6 resolved: removed from Rev A in M1-MECH-A8; legacy Ø6.97 mm aperture retained only as historical enclosure evidence
- J7 microSD insertion datum/MPN
- SW1/SW2 actuator access geometry/MPNs

---

## 15. Immediate next M1-MECH-A action

Use the 121.008 × 73.408 × 30 mm enclosure candidate and M1-MECH-A0 108 × 65.06 mm PCB envelope candidate to build the first connector-placement envelope and verify that connector bodies/bosses do not invalidate the candidate outline.

No connector footprint is considered production-locked until its panel datum and mating clearance are defined.
