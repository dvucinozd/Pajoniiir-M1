# Pajoniiir-M1 — M1-MECH-A Power Input Connector Strategy v0.1

> **HISTORICAL SELECTION RECORD.** J1 is now locked to Switchcraft 722RAHLP, while its PCB land pattern remains open pending terminal-center evidence. See `Pajoniiir_M1_Current_Design_Status_B5.md`.

**Datum:** 2026-09-03  
**Revision:** M1-MECH-A5  
**Status:** Preferred conditional J1 connector architecture selected; J1 gate remains open  
**Authority:** `hardware/Pajoniiir-M1/mech_a.json`

---

## 1. Decision

J1 should use a **user-grade threaded locking DC power connector**, not an internal-style wire-to-board latch.

Preferred conditional pair:

~~~text
J1 chassis/PCB jack = Switchcraft 722RAHLP
mating cable plug   = Switchcraft S760KHZ
~~~

This is now the preferred Rev A mechanical/electrical direction.

The exact J1 footprint and panel cutout remain open until wall and local enclosure geometry are authoritative.

---

## 2. Why the earlier Micro-Fit candidate is demoted

The earlier Molex 43650-0200 screen was attractive electrically, but it is fundamentally a wire-to-board connector family.

For a user-accessible main power inlet its mating-cycle rating is too low for the product role.

Result:

**Micro-Fit remains historical envelope/electrical evidence only; it is not the preferred J1 production architecture.**

---

## 3. Preferred jack — Switchcraft 722RAHLP

Manufacturer data:

~~~text
type                     locking DC power jack
center pin               2.0 mm
mounting                 panel + right-angle PCB
PCB termination          through-hole
locking                  threaded
rated voltage            24 VDC
rated current            7.5 A
jack life                10,000 cycles
temperature              -40 to +105 °C
contact resistance       0.01 ohm
bushing thread           5/16-32 UNEF 2A
bushing length           5.5 mm
hardware                 hex nut + flat washer
~~~

This directly satisfies several M1 needs at once:

- positive cable retention,
- panel load transfer,
- high cycle life,
- right-angle edge placement,
- substantial current margin.

---

## 4. Mating plug — Switchcraft S760KHZ

Manufacturer data:

~~~text
type                     locking DC power plug
center interface         2.0 mm
locking                  threaded
rated voltage            24 VDC
rated current            7.5 A
plug life                5,000 cycles
temperature              high-temp family
~~~

The system-level mating durability is therefore limited by the replaceable cable plug:

~~~text
jack = 10,000 cycles
plug =  5,000 cycles
system conservative rating = 5,000 cycles
~~~

That is appropriate for the primary external power connector.

---

## 5. Current-margin screen

Current M1 eFuse baseline with `RILM = 750 ohm`:

~~~text
ILIM minimum  ≈ 3.96 A
ILIM typical  ≈ 4.45 A
ILIM maximum  ≈ 4.84 A
~~~

Selected connector pair:

~~~text
7.50 A
~~~

Margin against worst documented eFuse threshold:

~~~text
7.50 - 4.84 = 2.66 A

7.50 / 4.84 = 1.55x
~55% rating margin
~~~

### Verdict

**PASS — first-order connector current screen.**

This is much healthier than selecting a connector that is only nominally 5 A while the eFuse can reach approximately 4.84 A.

---

## 6. Wall/topology consequence

M1-MECH-A4 already assigned the power cluster to an X-side wall class:

~~~text
POWER_IN = X_NEG or X_POS
~~~

The selected barrel jack's insertion axis is normal to that side wall.

Therefore the old Micro-Fit-style global “under-display height” arithmetic is no longer the authoritative J1 fit model.

J1 now needs a **local side-wall study**:

- exact X wall sign,
- cutout center,
- bushing/wall/nut relation,
- PCB edge,
- connector body,
- plug,
- cable bend,
- nearby boss/standoff,
- local display/module relief.

---

## 7. 2.0 mm enclosure wall screen

Candidate enclosure wall:

~~~text
2.0 mm
~~~

722RAHLP bushing:

~~~text
5.5 mm
~~~

A 2 mm wall is therefore **plausible on first-order thread-length screening**, and the connector includes a washer and nut.

However, this does **not** yet freeze the panel cutout.

Final validation still needs:

- actual washer thickness,
- nut thread engagement,
- anti-rotation requirement,
- print tolerance,
- panel bearing area,
- local wall reinforcement if needed.

---

## 8. Alternate — Kycon KLDLX-0202-A

The Kycon architecture remains mechanically attractive:

~~~text
right-angle panel mount
threaded locking
M8x0.75
5000 cycles
minimum recommended panel thickness 1.5 mm
~~~

Its current manufacturer drawing states **5 A**, while current distributor metadata still shows **3 A** in some listings.

Because J1 is a safety/reliability-critical power inlet, that discrepancy is not acceptable for an exact production lock.

Result:

**Kycon remains an alternate only until current-production rating is confirmed.**

---

## 9. Other Switchcraft candidate

Switchcraft RAPC722BKZ is also valid:

~~~text
5 A
5000 cycles
bayonet twist lock
right-angle THT
~~~

It is not preferred because 722RAHLP provides:

- 7.5 A current rating,
- 10,000-cycle chassis-jack durability,
- threaded lock,
- high-temperature construction.

RAPC722BKZ remains a possible fallback if the 722RAHLP geometry later proves incompatible with the enclosure.

---

## 10. J1 gate closure requirements

J1 remains open until all of the following pass:

1. choose `X_NEG` or `X_POS`,
2. define exact cutout center in `M1_FRONT_CENTER`,
3. define panel hole and any anti-rotation feature,
4. verify 2 mm wall + washer + nut + thread engagement,
5. place PCB edge and exact footprint,
6. verify body clearance to module/enclosure,
7. verify plug insertion and threaded access,
8. verify cable bend/strain clearance,
9. verify nearby boss/standoff clearance,
10. lock polarity convention and panel marking,
11. validate production sample mechanically.

Until then:

~~~text
J1 status = open
layout_freeze_allowed = false
~~~

---

## 11. Sources

- Switchcraft 722RAHLP: https://www.switchcraft.com/2-0mm-pin-meter-5-5mm-bushing-length-temp-max-105-c-7-5a/722rahlp/
- Switchcraft S760KHZ: https://www.switchcraft.com/standard-dc-power-jacks-and-plugs/2-0mm-center-pin-short-barrel-locking-high-temp/s760khz/
- Switchcraft RAPC722BKZ: https://www.switchcraft.com/bkz-series-dc-power-jacks-and-plugs/right-angle-pc-mount-dc-power-jack-pin-size-0-080-2-0mm-bayonet-twist-lock/rapc722bkz/
- Kycon KLDLX-0202-A drawing: https://www.kycon.com/Pub_Eng_Draw/KLDLX-0202-x.pdf
- Kycon DC power family: https://www.kycon.com/website/Products/DCPower/dcpower.html
