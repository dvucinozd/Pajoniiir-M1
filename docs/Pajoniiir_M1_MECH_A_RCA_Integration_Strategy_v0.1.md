# Pajoniiir-M1 — M1-MECH-A RCA Integration Strategy v0.1

**Datum:** 2026-09-03  
**Revision:** M1-MECH-A2  
**Status:** Preferred conditional architecture selected; J4/J5 remain open hard gates  
**Authority:** `hardware/Pajoniiir-M1/mech_a.json`

---

## 1. Decision

M1 should **prefer two individual right-angle RCA jacks directly on the main PCB** if the real enclosure/display perimeter geometry proves adequate local clearance.

Current preferred geometry family:

~~~text
J4 LEFT  = Kycon KLPX-0848A-2-W
J5 RIGHT = Kycon KLPX-0848A-2-R
~~~

Gold-flash `-G` variants remain same-family alternates, not the baseline requirement.

If local clearance fails, use a **panel-mounted RCA fallback**:

~~~text
J4 LEFT  = Same Sky RCJ-033 (white)
J5 RIGHT = Same Sky RCJ-032 (red)
~~~

No J4/J5 footprint is production-locked by this decision.

---

## 2. Why individual main-board RCA remains preferred

The legacy enclosure evidence is already organized around two independent RCA openings:

~~~text
legacy RCA hole diameter  = 11.88 mm
legacy center spacing     = 19.20 mm
~~~

Kycon KLPX-0848A-2-x provides an approximately Ø8.3 mm mating barrel.

First-order concentric aperture screen:

~~~text
diameter slack = 11.88 - 8.30 = 3.58 mm
radial slack   = 3.58 / 2      = 1.79 mm
~~~

This is favorable for the aperture itself.

Two independent board-mounted jacks also let M1 preserve the known **19.20 mm** pair spacing while keeping the PCM5102A output path on the main PCB with no internal audio harness.

---

## 3. Important correction to the A1 Z screen

M1-MECH-A1 used **10.0 mm** as a conservative Kycon RCA profile screen because the manufacturer drawing carries 10.0 mm body-face dimensions.

That value must **not** be interpreted as an authoritative PCB-plane-to-top height.

The final board-mounted RCA pass/fail test requires:

1. authoritative board-relative body envelope from the manufacturer drawing/CAD model,
2. exact PCB edge position,
3. local display/module rear relief at that edge,
4. enclosure wall thickness and inside surface,
5. plug/cable insertion envelope,
6. manufacturing and assembly clearance.

Therefore the earlier “10.5 mm including 0.5 mm screening gap” remains useful only as a **global conservative conflict detector**. It is not a standoff-height design dimension.

---

## 4. Why a global PCB shift is not the preferred fix

The current candidate stack has:

~~~text
module back        Z = 13.90
PCB front          Z = 20.40
PCB rear           Z = 22.00
rear inner wall    Z = 28.00
front gross gap        6.50 mm
rear gross gap         6.00 mm
~~~

A hypothetical global shift based on the conservative 10.0 mm RCA screen would reduce rear-side clearance to roughly 2 mm. That is mechanically unattractive and could create new conflicts elsewhere.

So the closure rule is:

**first prove local edge/perimeter relief; do not move the entire PCB merely to satisfy the conservative RCA screen.**

---

## 5. Panel-mounted fallback

Same Sky RCJ-032 / RCJ-033 are panel-mounted RCA jacks with threaded mounting and solder-eyelet termination.

Advantages:

- RCA mechanical load is transferred to the enclosure instead of the PCB,
- RCA body height no longer drives main-PCB Z clearance,
- red/white variants are current catalog parts.

Costs:

- two internal audio connections are added,
- assembly becomes more complex,
- harness routing and strain relief become real design requirements,
- the audio ground/shield implementation must be reviewed,
- the old Ø11.88 mm openings are **not automatically a final mounting datum** for a 1/4-32 threaded bushing.

The fallback therefore removes the PCB Z blocker but does not close the panel-mechanical gate by itself.

---

## 6. Rejected/deprioritized dual-RCA module

Switchcraft PJRAN2X1U__X has:

~~~text
jack center spacing = 15.0 mm
legacy M1 evidence  = 19.2 mm
mismatch            =  4.2 mm
~~~

It therefore does not preserve the existing pair geometry. The module also introduces its own 25.0 mm paired housing and does not provide a compelling Z-stack advantage.

Result: **deprioritized for Rev A** unless the enclosure is intentionally redesigned.

---

## 7. Closure test for preferred Kycon route

J4/J5 may move from “screened candidate” to exact production footprints only when all of these are known and pass:

- AUDIO_OUT physical wall assignment,
- absolute J4/J5 cutout centers in `M1_FRONT_CENTER`,
- board edge relative to the wall,
- board-relative connector body envelope,
- local display/module perimeter clearance,
- enclosure inside-wall clearance,
- RCA plug and cable insertion envelope,
- shell/ground isolation policy,
- courtyard/keepout,
- retained or intentionally revised center spacing.

Until then:

~~~text
J4 status = open
J5 status = open
layout_freeze_allowed = false
~~~

---

## 8. Immediate next action

Recover the **local RCA wall/perimeter geometry** from `flx4_0407.blend`, a dimensioned export, or direct physical measurement.

If the Kycon family fits locally, M1 keeps a clean one-board architecture.

If it does not, promote the Same Sky panel-mount pair and redesign only the RCA panel mounting / short internal audio interconnect instead of forcing the entire PCB Z-stack rearward.

---

## 9. Sources

- Kycon KLPX-0848A-2-x manufacturer drawing: https://www.kycon.com/Pub_Eng_Draw/KLPX-0848A-2-x.pdf
- Kycon KLPX-0848A-2-x-G manufacturer drawing: https://www.kycon.com/Pub_Eng_Draw/KLPX-0848A-2-x-G.pdf
- Same Sky RCA catalog: https://www.sameskydevices.com/catalog/interconnect/connectors/rca-connectors
- Same Sky RCJ-032: https://www.sameskydevices.com/product/interconnect/connectors/rca-connectors/rcj-032
- Same Sky RCJ-033: https://www.sameskydevices.com/product/interconnect/connectors/rca-connectors/rcj-033
- Switchcraft PJRAN2X1U__X drawing: https://www.switchcraft.com/assets/1/24/pjran2x1u__x_series_cd.pdf
