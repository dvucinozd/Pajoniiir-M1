# Pajoniiir-M1 — M1-MECH-A USB Host Connector Strategy v0.1

> **HISTORICAL SELECTION RECORD.** B4 subsequently locked and instantiated Amphenol 87520-1010ALF for J2/J3; final panel datums and mated-cable geometry remain open. See `Pajoniiir_M1_Current_Design_Status_B5.md`.

**Datum:** 2026-09-03  
**Revision:** M1-MECH-A3  
**Status:** Active preferred candidate selected; J2/J3 remain open hard gates  
**Authority:** `hardware/Pajoniiir-M1/mech_a.json`

---

## 1. Lifecycle correction

M1-MECH-A1 used GCT `USB1125-GF-B` as the first useful USB-A geometry envelope:

~~~text
USB 2.0 Type-A
right-angle THT
3 A
6.48 mm profile
10.00 mm body
5000 mating cycles
~~~

That geometry screen was useful, but GCT currently marks the **USB1125 series Not Recommended for New Designs**.

Therefore:

**USB1125-GF-B is demoted to historical envelope evidence and must not become the Rev A production BOM part.**

---

## 2. Preferred conditional production candidate

### Amphenol 87520-1010ALF

Current screen:

~~~text
interface            USB 2.0 Type-A receptacle
orientation          right-angle / horizontal
termination          through-hole
mechanical retention board lock
current rating       3 A
mating cycles        5000
part status          Active (current distributor listing)
family drawing       Released
~~~

The released Amphenol 87520 family drawing gives the shell/profile screen:

~~~text
profile nominal      7.0 mm
profile tolerance   +0.10 / -0.30 mm
screen worst case    7.1 mm
front-face width    14.5 mm class
recommended PCB      1.57 mm family/product baseline
~~~

The exact MPN remains conditional until panel datum, footprint and enclosure keepout are frozen.

---

## 3. Z-stack screen

Temporary MECH-A screening gap remains:

~~~text
0.50 mm
~~~

Using the **7.10 mm worst-case profile**:

~~~text
required front clearance = 7.10 + 0.50 = 7.60 mm
module back Z            = 13.90 mm
PCB front Z              = 21.50 mm
PCB rear Z               = 23.10 mm
rear inner wall Z        = 28.00 mm
gross rear clearance     =  4.90 mm
~~~

Compared with the original candidate:

~~~text
old PCB front Z          = 20.40 mm
old gross rear clearance =  6.00 mm
new screened PCB shift   = +1.10 mm rearward
new gross rear clearance =  4.90 mm
~~~

This means the active USB-A candidate **does fit the total gross 30 mm stack on first-order screening**, but the old 6 mm legacy standoff cannot be frozen.

Important: `4.90 mm` is a gross geometric remainder, **not a final standoff dimension**. Screw heads, boss geometry, rear-side components, assembly tolerance and print tolerance still consume space.

---

## 4. Lifecycle-stable alternate

### Würth Elektronik 614004190021

Manufacturer data:

~~~text
status                  Active
expected lifetime       >10 years
USB                     2.0 Type-A horizontal
mount                    THT
variant                  High Current
power-contact rating     3 A
other-contact rating     1 A
recommended PCB          1.6 mm
mating cycles            1500
envelope                 approx. 15.7 x 14.15 x 6.9 mm
~~~

Using 6.9 mm envelope height + the same temporary 0.5 mm screen:

~~~text
required front clearance = 7.40 mm
PCB front Z              = 21.30 mm
PCB rear Z               = 22.90 mm
gross rear clearance     =  5.10 mm
~~~

This alternate is mechanically slightly easier and has unusually clear manufacturer lifecycle support, but its **1500 mating-cycle rating is lower** than the preferred Amphenol candidate.

For a user-accessible DJ device, that durability difference is enough to keep Amphenol first unless later sourcing or enclosure evidence changes the decision.

---

## 5. Common-part policy

Baseline intent:

**J2 and J3 should use the same USB-A receptacle MPN.**

Benefits:

- one land pattern,
- one enclosure aperture family,
- one sourcing line,
- one shell/ESD/mechanical validation,
- fewer assembly variants.

Only split J2/J3 mechanics if a later wall/placement study proves a real need.

---

## 6. What still blocks J2/J3 footprint lock

Both USB gates remain open until all of these are known:

1. physical wall used by the USB_HOST_PAIR cluster,
2. absolute connector-face centers in `M1_FRONT_CENTER`,
3. PCB edge relative to inside wall,
4. shell/body keepout,
5. panel aperture and wall thickness,
6. external USB plug insertion clearance,
7. cable bend / strain envelope,
8. rear-side component clearance after Z rebalance,
9. final shell-stake drill / land-pattern review,
10. exact production lifecycle/availability confirmation.

Therefore:

~~~text
J2 status = open
J3 status = open
layout_freeze_allowed = false
~~~

---

## 7. Current decision hierarchy

~~~text
preferred conditional:
  Amphenol 87520-1010ALF
  3 A
  5000 mating cycles
  ~7.1 mm worst-case profile screen

active alternate:
  Würth 614004190021
  3 A power contacts
  1500 mating cycles
  ~6.9 mm envelope
  manufacturer expected lifetime >10 years

reference only:
  GCT USB1125-GF-B
  NRND
  do not promote to production BOM
~~~

---

## 8. Immediate next action

The next USB mechanical datum is no longer “find a connector.”

It is:

**assign the USB_HOST_PAIR cluster to a real enclosure wall and prove the connector-face / PCB-edge / cable / boss envelope.**

That same wall study can then determine whether the candidate PCB Z moves toward approximately the screened `Z=21.5 mm` front plane or whether local perimeter relief allows the board to remain closer to the current Z-stack.

---

## 9. Sources

- Amphenol 87520 released family drawing: https://cdn.amphenol-cs.com/media/wysiwyg/files/drawing/87520.pdf
- Amphenol 87520-1010ALF current part listing: https://www.digikey.com/en/products/detail/amphenol-cs-fci/87520-1010ALF/1528948
- Würth 614004190021 product/datasheet: https://www.we-online.com/components/products/datasheet/614004190021.pdf
- Würth WR-USB current catalog/lifecycle: https://www.we-online.com/en/components/products/em/connectors/input_output_connectors/input_output_wr_usb_sub
- GCT USB Type-A lifecycle/product page: https://gct.co/usb-connector/usb-a-type
