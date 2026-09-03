# Pajoniiir-M1 — M1-MECH-B0 Final 5-inch DSI Display Baseline v0.1

**Date:** 2026-09-04  
**Revision:** M1-MECH-B0  
**Status:** FINAL PRODUCT DISPLAY MODULE SELECTED  

---

## 1. Product decision

Pajoniiir-M1 Rev A will use the complete **Elecrow DSI05379I 5-inch MIPI-DSI capacitive-touch display module** as the final production display assembly.

This decision supersedes the earlier M1 assumption that the product would reuse a bare 4.3-inch Guition/JC4880 ST7701S display panel through the 30-contact SOFNG `0.5TBQP-30P-1` FPC interface.

The former Guition panel/FPC work remains useful historical/electrical-forensic evidence, but it is no longer the final product mechanical/display baseline.

---

## 2. New display authority

### Product

- Manufacturer/brand: Elecrow
- Product/SKU: `DSI05379I`
- Display size: 5 inch
- Resolution: 800 × 480
- Refresh rate: 60 Hz
- Display type: IPS
- Touch: capacitive
- Module interface: Raspberry Pi-style MIPI DSI
- Cable family supplied with module: 15-pin, 1.0 mm pitch FFC
- Nominal operating voltage: 3.3 V
- Published active area: 108.00 × 64.80 mm
- Published module size: approximately 121.1 × 77.9 mm

Primary public sources:

- Elecrow product page: https://www.elecrow.com/5-inch-dsi-display-ips-800-480-touch-screen-compatible-with-raspberry-pi-4b-3b-3b.html
- Elecrow user manual v1.4: https://www.elecrow.com/download/product/DSI05379I/5inch-dsi-display_user_manual-v1.4.pdf

---

## 3. User-provided dimensioned rear-view evidence

The dimensioned rear image supplied for the final module is treated as current M1-MECH-B0 mechanical evidence.

Visible/annotated dimensions:

```text
PCB/module rear board width      121.109 mm
PCB/module rear board height      77.193 mm
mounting-hole radius               1.250 mm
mounting-hole diameter             2.500 mm
outer top corner hole inset X       5.000 mm
outer top corner hole inset Y       5.000 mm
outer lower corner hole Y datum    72.930 mm from top reference
```

The same image shows:

- a 15-pin DSI interface connector on the rear PCB,
- a physical Backlight On/Off control,
- a separate FAN header area marked with 3V3/GND/PWM functions,
- eight visible Ø2.5 mm mounting holes,
- integrated display/touch/backlight electronics on the display module PCB.

The image-derived `121.109 × 77.193 mm` board envelope is preferred over the rounded public `121.1 × 77.9 mm` product-page value for preliminary CAD work, but physical caliper or official STEP/CAD verification is still required before final enclosure release.

---

## 4. Immediate incompatibility with the previous enclosure baseline

Previous M1-MECH-A enclosure candidate:

```text
external enclosure envelope  121.008 × 73.408 mm
modeled inner cavity          117.008 × 69.408 mm
```

Final 5-inch display rear board:

```text
121.109 × 77.193 mm
```

Therefore the previous enclosure candidate is invalid for the final product.

Difference versus old *external* enclosure envelope:

```text
X: 121.109 - 121.008 = +0.101 mm
Y:  77.193 -  73.408 = +3.785 mm
```

Difference versus old modeled *inner* cavity:

```text
X: 121.109 - 117.008 = +4.101 mm
Y:  77.193 -  69.408 = +7.785 mm
```

This is a hard geometric contradiction, not a tolerance issue. M1 enclosure width/height must be redesigned around the 5-inch display module.

---

## 5. Electrical architecture consequence

The final product no longer needs the mainboard to replicate the Guition bare-panel support architecture blindly.

The new intended interface becomes:

```text
ESP32-P4 mainboard
    |
    +-- MIPI DSI clock + two data lanes
    +-- display/touch control signals required by the 15-pin module interface
    +-- 3.3 V display-module power domain
    |
    +--> 15-pin 1.0 mm DSI FFC
            |
            +--> Elecrow DSI05379I module
                    + integrated LCD interface electronics
                    + integrated capacitive touch electronics
                    + integrated backlight electronics
```

Consequences to be audited before changing the production schematic:

1. derive the exact 15-pin Elecrow/Raspberry-Pi-compatible DSI pinout from authoritative documentation,
2. map ESP32-P4 DSI lane polarity/order to that connector,
3. determine exactly how touch I²C/reset/interrupt are carried on the module interface,
4. determine actual display-module current requirement; public Elecrow pages contain inconsistent current text, so power budgeting must use the manual and/or measurement rather than an unverified storefront number,
5. determine whether the existing M1 MP3202 backlight circuit is now unnecessary,
6. determine whether the existing M1 discrete GT911 touch section is now unnecessary,
7. select and lock the exact 15-pin 1.0 mm FFC connector and cable orientation on the M1 PCB,
8. retain ESD/EMI protection and controlled-impedance requirements appropriate to MIPI DSI.

Until those items are completed, the current `10_DISPLAY_MIPI.kicad_sch` is historical/pre-B0 implementation evidence and must not be treated as final display-production capture.

---

## 6. Mechanical architecture consequence

M1-MECH-B must be rebuilt around the 5-inch module first, then the custom mainboard and enclosure must be fitted behind/around it.

The 5-inch module becomes the primary XY datum object.

Recommended new coordinate convention:

```text
M1_FRONT_CENTER origin = center of final 5-inch active/display front envelope
X = right in landscape orientation
Y = down in landscape orientation
Z = rear/inward
```

The old `108.00 × 65.06 mm` custom-mainboard candidate and old 4.3-inch mounting pattern are no longer production authority. They may be reused only if a new fit study against the 5-inch module proves them valid.

---

## 7. Mounting-hole evidence

The dimensioned image clearly supports the four outer hole centers as approximately:

```text
from rear-PCB top-left datum:

upper-left       (  5.000,  5.000 ) mm
upper-right      (116.109,  5.000 ) mm
lower-left       (  5.000, 72.930 ) mm
lower-right      (116.109, 72.930 ) mm

hole diameter ≈ 2.50 mm
```

This gives an outer-hole center pattern of approximately:

```text
111.109 × 67.930 mm
```

The image also contains four inner mounting holes, but their complete authoritative Y-coordinate pattern is not promoted from the raster alone. The official 3D file or physical measurement should be used before assigning those four holes to enclosure or mainboard mounting.

---

## 8. M1-MECH-B closure order

The next deterministic work sequence is:

1. obtain/import the Elecrow `DSI05379I` 3D model or measure the real module,
2. lock full front/rear/display-PCB Z envelope,
3. lock all eight mounting-hole centers and decide which holes M1 uses structurally,
4. lock exact 15-pin DSI connector/cable orientation and mating keepout,
5. redesign enclosure XY around the 5-inch board,
6. place the custom M1 mainboard relative to display board, DSI connector and mounting hardware,
7. re-run J1/J2/J3/J4/J5/J7/SW1/SW2 wall packing against the larger enclosure,
8. freeze PCB Z/standoffs,
9. freeze final custom-mainboard Edge.Cuts,
10. only then begin production placement/routing freeze.

---

## 9. Superseded assumptions

The following M1-MECH-A assumptions are superseded for final-product mechanical design:

- 4.3-inch Guition front envelope as product display datum,
- Guition `117.008 × 69.408 mm` module shell as final enclosure-fit object,
- `121.008 × 73.408 mm` enclosure as a viable final external envelope,
- 30-pin SOFNG bare-panel FPC as final product display connector,
- old display-driven 108 × 65.06 mm rear working envelope as production PCB authority.

They remain historical design evidence only.

---

## 10. Freeze status after B0

```text
final display module selected             YES
final display XY family                    YES
old 4.3-inch product baseline superseded  YES
final enclosure locked                     NO
final DSI connector/pinout locked          NO
final display power budget locked          NO
final mainboard outline locked             NO
placement/routing freeze allowed           NO
```

M1-MECH-B0 is therefore a **baseline switch**, not a final mechanical freeze.
