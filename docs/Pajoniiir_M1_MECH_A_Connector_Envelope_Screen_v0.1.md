# Pajoniiir-M1 — M1-MECH-A Connector Envelope Screen v0.1

**Datum:** 2026-09-03  
**Revision:** M1-MECH-A1  
**Status:** Candidate connector envelopes screened; no mechanical gate closed  
**Machine-readable authority:** `hardware/Pajoniiir-M1/mech_a.json`

---

## 1. Why this screen exists

M1-MECH-A0 established a 108.00 × 65.06 mm candidate PCB and a candidate Z-stack inside the validated 121.008 × 73.408 × 30.0 mm legacy enclosure.

The current gross stack is:

~~~text
module back                    Z = 13.90
PCB front/component side       Z = 20.40
PCB rear                       Z = 22.00
rear inner wall                Z = 28.00

front gross clearance              6.50 mm
rear gross clearance               6.00 mm
PCB thickness                      1.60 mm
total free Z around PCB           12.50 mm
~~~

That 6.50/6.00 mm split passed the known central IC/module/inductor height screen, but it had not yet been challenged by real external connector bodies.

This document performs that challenge.

---

## 2. Screening rule

For a conservative front-side screen:

~~~text
required_front_clearance = connector_profile + screening_gap

PCB_front_Z = module_back_Z + required_front_clearance
PCB_rear_Z  = PCB_front_Z + PCB_thickness
rear_gap    = rear_inner_Z - PCB_rear_Z
~~~

A temporary **0.50 mm screening gap** is used only to detect obvious mechanical conflicts. It is **not** a production tolerance or safety-clearance freeze.

The calculation deliberately treats the module-back plane as continuous across the board. Edge-mounted connectors may have more local room if the real display/module rear geometry is relieved near the perimeter. That can only be promoted after CAD or physical measurement proves it.

---

## 3. Candidate screen

| Ref | Candidate | Relevant physical evidence | M1-MECH-A1 result |
|---|---|---|---|
| J1 | Molex 43650-0200 | Micro-Fit 3.0, 2 circuits, right-angle THT, 1.60 mm PCB, 8.5 A/contact, 9.65 mm length, 6.98 mm mated height | electrically strong; conservative central Z screen needs more than present 6.5 mm |
| J2/J3 | GCT USB1125-GF-B | USB 2.0 Type-A, right-angle THT, 3 A, 6.48 mm profile, 10.00 mm body, 5000 cycles | present 6.50 mm gross front gap leaves only 0.02 mm before tolerance/safety: **not production-acceptable** |
| J4 | Kycon KLPX-0848A-2-W-G | right-angle RCA, Ø8.3 mm barrel, ~10 mm body profile | legacy Ø11.88 aperture is promising, but global Z screen fails |
| J5 | Kycon KLPX-0848A-2-R-G | same geometry as J4 | same result |
| J7 | Molex 503398-1892 | microSD, normal-mount SMT, push-push, card detect, 1.28 mm height, 10k cycles | global height screen passes; panel slot/card access still open |
| SW1/SW2 | Omron B3U-3000P / B3U-3000PM family | side-actuated compact SMT tactile family | promising service-button family; exact suffix and actuator datum remain open |

J6 remains intentionally unresolved until the project decides whether the 3.5 mm line output is populated or removed/DNP.

J_LCD remains the separate display/FPC hard gate.

---

## 4. Z-stack implications

### USB-A

Using 6.48 mm profile + 0.50 mm screening gap:

~~~text
required front clearance = 6.98 mm
PCB front Z              = 20.88 mm
PCB rear Z               = 22.48 mm
rear clearance           =  5.52 mm
~~~

So USB-A is not fundamentally impossible in the 30 mm enclosure, but the current 6.0 mm legacy-standoff-derived stack is not a production freeze.

### 5 V Micro-Fit candidate

Using the published 6.98 mm mated-height value conservatively + 0.50 mm screening gap:

~~~text
required front clearance = 7.48 mm
PCB front Z              = 21.38 mm
PCB rear Z               = 22.98 mm
rear clearance           =  5.02 mm
~~~

The exact housing-above-PCB profile still needs drawing-level verification; the number is being used only as a conservative envelope screen.

### RCA pair

Using the ~10.0 mm body profile + 0.50 mm screening gap:

~~~text
required front clearance = 10.50 mm
PCB front Z              = 24.40 mm
PCB rear Z               = 26.00 mm
rear clearance           =  2.00 mm
~~~

This is the first **dominant mechanical conflict** exposed by M1-MECH-A1. A simple global Z shift that accommodates these right-angle RCA bodies would collapse rear clearance to about 2 mm.

That does **not** prove the RCA candidate is unusable, because an edge-mounted connector may sit beside a locally relieved module/shell region. It does prove that the project must resolve the real perimeter geometry before freezing the standoff height or connector footprint.

---

## 5. Legacy RCA aperture correlation

Kycon KLPX-0848A-2-x-G uses an approximately Ø8.3 mm barrel.

Legacy Blender evidence recorded:

~~~text
RCA panel hole diameter = 11.88 mm
~~~

First-order concentric aperture margin:

~~~text
diameter clearance = 11.88 - 8.30 = 3.58 mm
radial clearance   = 1.79 mm
~~~

Therefore the **aperture diameter itself is not the blocker** on this candidate. Body depth/profile, exact wall center, wall thickness, PCB-edge relation and plug clearance are the unresolved dimensions.

---

## 6. Mechanical verdict

M1-MECH-A1 changes one important assumption:

**The legacy 6.0 mm main standoff height must remain evidence/candidate only. It is not a final M1 value.**

The current M1-MECH-A0 XY board envelope is **not yet disproven**. The new blocker is connector-driven Z/perimeter geometry.

Priority order is now:

1. Resolve the RCA implementation strategy.
2. Recover exact legacy wall/cutout/module perimeter geometry through M1-MECH-A-D1 or direct physical measurement.
3. Rebalance PCB Z / standoff height from real connector envelopes.
4. Assign connector clusters to walls and record absolute centers/insertion axes.
5. Only then promote exact connector MPNs/footprints and final Edge.Cuts.

---

## 7. Candidate sources

- Molex 43650-0200: https://www.molex.com/en-us/products/part-detail/436500200
- GCT USB1125 family / USB1125-GF-B: https://gct.co/usb-connector/usb-a-type
- Kycon KLPX-0848A-2-x-G drawing: https://www.kycon.com/Pub_Eng_Draw/KLPX-0848A-2-x-G.pdf
- Molex 503398-1892: https://www.molex.com/en-us/products/part-detail/5033981892
- Omron B3U family: https://components.omron.com/eu-en/products/switches/B3U

These are screening candidates, not final BOM locks.
