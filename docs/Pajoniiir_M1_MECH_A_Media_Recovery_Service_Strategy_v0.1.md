# Pajoniiir-M1 — M1-MECH-A Media & Recovery Service Strategy v0.1

**Datum:** 2026-09-03  
**Revision:** M1-MECH-A6  
**Status:** Preferred J7/SW1/SW2 candidates and opposite-wall relationship selected; absolute datums remain open  
**Authority:** `hardware/Pajoniiir-M1/mech_a.json`

---

## 1. Wall relationship

M1-MECH-A6 locks one additional piece of topology without inventing absolute left/right orientation:

~~~text
POWER_WALL         = one X side
MEDIA_SERVICE_WALL = the opposite X side
~~~

Which wall is `X_NEG` and which is `X_POS` remains open.

This relative decision is now fixed because it prevents the external locking power cable from obstructing:

- microSD insertion/ejection,
- RESET access,
- BOOT access.

The long Y wall remains reserved for the larger USB + RCA cluster.

---

## 2. J7 preferred conditional socket

### Molex 503398-1892

Current manufacturer information:

~~~text
type             microSD
mount            normal SMT
entry            front
ejection         push-push
card detect      yes, open switch
height           1.28 mm
width            13.10 mm
depth            14.05 mm
durability       10,000 mating cycles
PCB retention    yes
temperature      -25 to +85 °C
~~~

### Why it fits M1 well

- Very low height.
- Board-edge front entry.
- Push-push operation reduces dependence on a large fingernail recess.
- Card detect matches the existing optional GPIO46 design intent.
- 10,000-cycle durability is appropriate for removable user media.

J7 is therefore upgraded from a generic microSD gate to a **preferred conditional exact MPN candidate**.

The footprint is still not locked.

---

## 3. SW1 / SW2 preferred conditional switch

### B3U-3000P-B

Current sourcing is under **Aratas (formerly Omron Components)**; the mechanical family is the established Omron B3U design.

Relevant data:

~~~text
operation             side-actuated
circuit               SPST-NO momentary
mount                  SMT
locating boss          yes
body class             4.0 x 2.5 mm
side-actuated height   ~3.2 mm family drawing
operating force        1.59 N / 162 gf
travel                 0.20 mm
mechanical life        100,000 cycles
ingress                dust proof
~~~

The locating-boss version is preferred because RESET/BOOT are accessed through enclosure holes with a tool; positive switch registration is more valuable here than saving one small locator drill.

---

## 4. Recovery-access policy

RESET and BOOT are service controls, not normal user UI.

Baseline:

- separate access holes,
- recessed / tool-accessible,
- no large common opening,
- no accidental card/finger actuation path,
- actuator direction normal to the chosen service wall,
- exact hole size and wall-to-actuator distance derived from CAD/physical validation.

The two switches may share the same wall as J7, but they must not intrude into the card insertion/ejection envelope.

---

## 5. First-order short-wall packing

Candidate X-wall length:

~~~text
73.408 mm
~~~

For feasibility only, reserve:

~~~text
microSD body width              13.10 mm
clearance around microSD         5.00 mm each side
gap to recovery region           8.00 mm
SW1 reserved service zone        6.00 mm
gap SW1-to-SW2                   6.00 mm
SW2 reserved service zone        6.00 mm
----------------------------------------
occupied span                   49.10 mm
~~~

Centered wall remainder:

~~~text
(73.408 - 49.10) / 2 = 12.154 mm per end
~~~

### Verdict

**PASS — short-wall capacity is not a blocker.**

The 49.10 mm number is a packaging screen only. It is not a cutout drawing.

---

## 6. What remains open for J7

Before the microSD footprint/cutout is frozen:

1. assign the actual `X_NEG` or `X_POS` service wall,
2. exact socket/card center,
3. exact slot width/height,
4. PCB edge-to-wall position,
5. full card insertion/ejection travel,
6. finger clearance,
7. shell/retention courtyard,
8. boss/standoff interference,
9. exact land pattern and sourcing lifecycle check.

---

## 7. What remains open for SW1 / SW2

Before switch footprint/access-hole freeze:

1. absolute centers,
2. actuator-to-wall gap,
3. tool-hole diameter/shape,
4. RESET-to-BOOT spacing,
5. no overlap with J7 card path,
6. locating-boss drill,
7. exact footprint and courtyard,
8. service labeling / differentiation strategy.

Until those pass:

~~~text
J7  status = open
SW1 status = open
SW2 status = open
layout_freeze_allowed = false
~~~

---

## 8. Immediate next mechanical step

After A6 the remaining largest external-I/O uncertainty is no longer “which type of microSD or service switch.”

It is **absolute wall datum recovery**:

- choose which X wall is power,
- the opposite X wall automatically becomes media/service,
- then place J1/J7/SW1/SW2 against actual boss and wall geometry.

The primary long-wall J2/J3/J4/J5 datum remains the other major external-I/O closure.

---

## 9. Sources

- Molex 503398-1892 product page: https://www.molex.com/en-us/products/part-detail/5033981892
- Molex 503398 series chart: https://www.molex.com/en-us/products/series-chart/503398
- B3U manufacturer family drawing: https://omronfs.omron.com/en_US/ecb/products/pdf/en-b3u.pdf
- Current B3U-3000P-B listing: https://www.digikey.com/en/products/detail/aratas-formerly-omron-components/B3U-3000P-B/2748498
