# Pajoniiir-M1 — M1-MECH-A Datum Extraction v0.1

**Procedure ID:** M1-MECH-A-D1  
**Status:** Ready; source CAD currently unavailable in this session  
**Primary source:** `D:\AI\BLENDER\flx4_0407.blend`

---

## Goal

Recover exact legacy enclosure feature coordinates and transform them into the authoritative `M1_FRONT_CENTER` frame without relying on screenshots or remembered positions.

## Transform anchor

The legacy Blender module reference must first reproduce:

~~~text
117.008 x 69.408 x 13.900 mm
~~~

and align to the M1 landscape display/module frame. Promotion is rejected if the transformed module envelope differs by more than 0.1 mm from the locked reference.

## Features to extract

For every relevant feature record:

1. wall/surface ID
2. center X/Y/Z in M1_FRONT_CENTER
3. aperture diameter or width/height
4. insertion-axis direction
5. distance to nearest case edge
6. distance to nearest standoff/boss
7. internal body keepout
8. external mating clearance

Required features:

- RCA L
- RCA R
- 3.5 mm line output
- legacy USB openings
- all main-board standoffs
- display/module reference
- inner/outer case wall surfaces

## Known legacy checks

~~~text
RCA hole diameter      11.88 mm
RCA center spacing     19.20 mm
3.5 mm hole diameter    6.97 mm
main standoff height     6.00 mm
~~~

Qualitative final correction history:

~~~text
RCA: move upward
3.5 mm: move downward
USB: leave in existing position
~~~

These values are cross-checks, not substitutes for extracting the actual centers.

## Promotion rule

A recovered legacy cutout becomes an M1 datum only after the selected production connector MPN fits both the aperture and its full internal/external mating envelope. Otherwise it remains legacy evidence and the gate stays open.
