# Pajoniiir-M1 — M1-MECH-A Panel Packing Feasibility v0.1

**Datum:** 2026-09-03  
**Revision:** M1-MECH-A4  
**Status:** Wall-class topology screened; absolute wall signs and centers remain open  
**Authority:** `hardware/Pajoniiir-M1/mech_a.json`

---

## 1. Purpose

The legacy Blender source is not currently available through the active MCP connection, so M1 cannot truthfully recover absolute connector centers yet.

That does not prevent a first-order question from being answered:

**Can the major production connector clusters physically coexist on the candidate enclosure / PCB edges without forcing a larger enclosure?**

M1-MECH-A4 answers that question while deliberately avoiding invented absolute coordinates.

---

## 2. Candidate long-wall geometry

Known enclosure and PCB candidate:

~~~text
enclosure long wall     121.008 mm
candidate PCB long edge 108.000 mm
candidate mount centers X = ±51.300 mm
candidate mount holes   Ø2.000 mm
~~~

The selected wall is symbolically:

~~~text
Y_LONG_WALL = Y_NEG or Y_POS
~~~

The sign remains open until the final ergonomic/CAD orientation is recovered or explicitly chosen.

---

## 3. USB host-pair span

Preferred USB candidate:

~~~text
Amphenol 87520-1010ALF
front-face width used for packing = 14.50 mm
~~~

Retaining the old **34.00 mm dual-USB center spacing only as a first-order packing reference**:

~~~text
USB pair occupied span
= center spacing + one connector width
= 34.00 + 14.50
= 48.50 mm
~~~

The 34 mm value is not a final J2/J3 datum.

---

## 4. RCA pair span

Legacy evidence:

~~~text
RCA aperture diameter = 11.88 mm
RCA center spacing    = 19.20 mm
~~~

Panel aperture span:

~~~text
19.20 + 11.88 = 31.08 mm
~~~

This is a panel-aperture screen. Exact Kycon internal body/courtyard clearance remains a separate gate.

---

## 5. USB + RCA primary long-wall packing

Reserve a deliberately non-zero **8.00 mm inter-cluster panel gap** between the USB and RCA groups.

~~~text
USB pair              48.50 mm
inter-cluster reserve  8.00 mm
RCA pair              31.08 mm
--------------------------------
total                  87.58 mm
~~~

Centered on the enclosure wall:

~~~text
(121.008 - 87.58) / 2 = 16.714 mm gross end margin per side
~~~

Centered on the candidate PCB long edge:

~~~text
(108.00 - 87.58) / 2 = 10.21 mm gross end margin per side
~~~

Packed half-span:

~~~text
87.58 / 2 = 43.79 mm
~~~

Candidate mounting-hole centers are at `|X| = 51.30 mm`.

So:

~~~text
mount-hole center to packed end = 51.30 - 43.79 = 7.51 mm
mount-hole edge to packed end   = 50.30 - 43.79 = 6.51 mm
~~~

### Verdict

**PASS — first-order packing only.**

USB_HOST_PAIR + J4/J5 RCA can share one long wall without immediately invalidating the 121.008 mm enclosure or 108 mm PCB candidate.

The remaining 6.51 mm to the Ø2 hole edge is **not** enough to declare final clearance, because boss OD, screw head/driver access and real connector body courtyards are still unknown.

---

## 6. J6 3.5 mm same-row test — closure evidence

Legacy J6 aperture:

~~~text
Ø6.97 mm
~~~

Assume only 5.00 mm reserve after the RCA group:

~~~text
existing USB+RCA pack = 87.58 mm
reserve                =  5.00 mm
J6 aperture            =  6.97 mm
--------------------------------
total                  = 99.55 mm
~~~

Centered on the 108 mm PCB edge:

~~~text
PCB end margin each side = (108 - 99.55) / 2 = 4.225 mm
packed half-span         = 49.775 mm
to mount-hole center     = 51.300 - 49.775 = 1.525 mm
to Ø2 mount-hole edge    = 50.300 - 49.775 = 0.525 mm
~~~

### Verdict

**FAIL — this screen was one of the inputs to M1-MECH-A8, which removes J6 from the Rev A board.**

Only 0.525 mm remains to the candidate mounting-hole edge before any boss, connector body or courtyard allowance.

Before the A8 product decision, the theoretically valid alternatives were:

1. different wall,
2. separate Z row / panel-mounted or harness solution if enclosure geometry permits,
3. Rev A DNP/removal,
4. mounting/outline revision only if 3.5 mm output is a firm product requirement.

This is a real mechanical constraint, not a sourcing preference.

---

## 7. Preferred wall-class topology

No wall **sign** or absolute center is frozen, but the topology can now be narrowed.

### One long Y wall — primary user cable wall

~~~text
J2 USB0
J3 USB1
J4 RCA L
J5 RCA R
~~~

USB and RCA should occupy opposite halves with internal electrical/EMI separation preserved.

### One X side wall — power

~~~text
J1 5 V locking input
~~~

This keeps the locking power plug out of the dense USB/RCA panel pack and supports a short J1/U7 high-current spine near a board edge.

### Opposite X / separate accessible side — media/service

~~~text
J7 microSD
SW1 RESET
SW2 BOOT
~~~

microSD needs direct finger/card access. RESET/BOOT should remain recessed or tool-accessible.

### Rear/internal fixture

~~~text
J9 factory pogo
~~~

No normal user panel allocation is required.

### J6

**Removed from Rev A in M1-MECH-A8. No wall or PCB-edge budget is reserved.**

---

## 8. What A4 does *not* claim

A4 does not define:

- Y_NEG vs Y_POS,
- X_NEG vs X_POS,
- exact connector X/Y/Z centers,
- exact cutout rectangles,
- connector-body courtyards,
- plug/cable bend volumes,
- boss diameters,
- final mounting pattern,
- final PCB Edge.Cuts.

Those are still hard gates.

---

## 9. Immediate next mechanical closure

The highest-value next datum is now explicit:

**recover or define the actual primary long-wall sign and absolute J2/J3/J4/J5 centers, then test the 87.58 mm first-order pack against real bosses, connector bodies and plug/cable volumes.**

Until then:

~~~text
layout_freeze_allowed = false
all affected connector gates remain open
~~~
