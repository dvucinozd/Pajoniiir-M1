# Pajoniiir-M1 — ESP32-P4 v3.2 Silicon Selection & Migration v0.1

**Projekt:** Pajoniiir-M1 Rev A  
**Datum:** 2026-09-02  
**Status:** Production silicon selection candidate

---

# 1. Final silicon family decision

Pajoniiir-M1 Rev A shall use:

**ESP32-P4NRW32X**

not:

**ESP32-P4NRW32**

The suffix **X** identifies the upgraded P4 product family.

The selected device provides:

- ESP32-P4 v3.x silicon
- 32 MB in-package PSRAM
- QFN104, 10 × 10 mm
- -40…85 °C rated ambient family
- 1.8 V in-package PSRAM interface
- no in-package firmware flash, so W25Q128JV external flash remains required

---

# 2. Official Espressif lifecycle status

Espressif PCN202600801 explicitly maps:

~~~text
OLD / planned EOL:
ESP32-P4NRW32

NEW / recommended:
ESP32-P4NRW32X
~~~

The PCN identifies the new revision as **v3.2** and tells customers to place orders using the new part numbers.

Therefore:

**ESP32-P4NRW32X is the correct procurement family for a new M1 design.**

---

# 3. Procurement target

Primary BOM MPN:

~~~text
ESP32-P4NRW32X
~~~

Required incoming condition:

~~~text
chip revision >= v3.2 preferred
upgraded X product family
32 MB PSRAM
QFN104
~~~

Because Espressif notes that a part-number family can contain multiple chip revisions over its lifetime, incoming inspection should record actual silicon revision.

---

# 4. Marking / revision identification

Espressif packaging information maps manufacturing codes:

| Revision | Manufacturing code pattern |
|---|---|
| v0.0 | X A XX |
| v1.0 | X C XX |
| v1.3 | X E XX |
| v3.0 | X F XX |
| v3.1 | X G XX |
| **v3.2** | **X H XX** |

The product-name suffix X identifies the upgraded product family.

Factory incoming inspection should log:

- printed product name
- manufacturing/revision code
- lot code
- eFuse/ROM chip revision reported by test firmware

---

# 5. Main hardware incompatibility

Old rev1.3:

~~~text
physical package pin 54 = NC
~~~

New v3.x/v3.2:

~~~text
physical package pin 54 = VDD_HP_1
~~~

For Pajoniiir-M1:

**physical pin 54 must be connected to P4_VDD_HP.**

Do not confuse physical package pin 54 with **GPIO54**, which is a separate logical GPIO signal used by Pajoniiir to reset the C6.

---

# 6. P4 VDD_HP DCDC changes

Espressif PCN requires for v3.2 migration:

- both 499 kΩ feedback resistors populated
- 22 pF feedforward capacitor populated
- correct v3.x current reference topology
- physical pin 54 tied to VDD_HP

Pajoniiir-M1 core design already includes:

~~~text
R_CORE_FB1 = 499 kΩ
R_CORE_FB2 = 499 kΩ
C_CORE_FF  = 22 pF
~~~

with TLV62569.

This is aligned with the official v3.2 migration requirement.

---

# 7. USB migration note

The PCN also states that when updating old v1.3 PCB designs to v3.2:

**remove the old 1 MΩ resistor on USB_DP.**

Pajoniiir-M1 is a new design and should follow the current v3.x reference design directly.

Do not copy any old JC4880 USB_DP pull network.

---

# 8. ESP-IDF software requirement

Official minimums for v3.2:

~~~text
release/v5.5 -> ESP-IDF >= 5.5.3
release/v6.0 -> ESP-IDF >= 6.0
~~~

Pajoniiir currently targets the ESP-IDF 6.0.x line, so the framework version itself is acceptable.

---

# 9. Mandatory Kconfig change for M1

Current JC4880 firmware contains old-silicon configuration similar to:

~~~text
CONFIG_ESP32P4_SELECTS_REV_LESS_V3=y
CONFIG_ESP32P4_REV_MIN_100=y
CONFIG_ESP32P4_REV_MIN_FULL=100
~~~

That must **not** be reused for M1.

The v3.x M1 board target must ensure:

~~~text
CONFIG_ESP32P4_SELECTS_REV_LESS_V3=n
~~~

or the equivalent current ESP-IDF configuration state where pre-v3 selection is disabled.

Revision minimum settings must be regenerated for v3.x using the actual ESP-IDF menuconfig options rather than copying the old JC4880 file.

---

# 10. Binary compatibility rule

Espressif explicitly warns:

**v1.3 and v3.2 cannot run the same binary.**

Therefore Pajoniiir should treat these as separate board targets:

~~~text
JC4880 legacy target -> rev1.3 binary

Pajoniiir-M1 target -> v3.x/v3.2 binary
~~~

Do not try to distribute one universal P4 image across both boards unless Espressif later explicitly supports such a mode.

---

# 11. Recommended firmware structure

Preferred product architecture:

~~~text
firmware/main-deck-p4/
  components/
    bsp_jc4880/          # legacy Guition rev1.3 target
    bsp_pajoniiir_m1/    # new custom v3.x target

  sdkconfig.defaults.jc4880
  sdkconfig.defaults.m1
~~~

M1 file contains no pre-v3 selector.

Shared application/audio/UI code remains common.

---

# 12. Performance implication

Official v3.2 PCN lists improvements over v1.3 including:

- CPU stable frequency increasing from 360 MHz to 400 MHz
- PSRAM interface stable up to 250 MHz instead of 200 MHz
- DMA/PPA improvements
- memory-layout improvements
- power-management improvements
- security fixes/features

For Pajoniiir these are positive because the workload combines:

- LVGL
- PPA rotation
- MIPI DSI
- dual USB
- audio decode/DSP
- Wi-Fi
- PSRAM-heavy buffers

However, Rev A firmware should initially retain conservative known-good operating frequencies until basic bring-up passes.

Do not immediately increase PSRAM frequency simply because v3.2 supports more.

---

# 13. First-boot silicon verification

Factory test firmware should print:

~~~text
board = Pajoniiir-M1
chip = ESP32-P4
chip_revision = <actual>
psram_bytes = 33554432
flash_bytes = 16777216
idf_version = <actual>
~~~

Acceptance:

- revision reports v3.x / expected v3.2+
- 32 MB PSRAM detected
- 16 MB external flash detected
- no revision compatibility warning
- USB/SDIO basic smoke tests pass

---

# 14. Procurement QA

Before ordering EVT quantity:

1. purchase only **ESP32-P4NRW32X**
2. do not accept old ESP32-P4NRW32 substitution
3. verify distributor/manufacturer listing says upgraded X family
4. request revision/lot info where possible
5. retain at least several chips from one lot for failure analysis
6. log top marking of assembled EVT units

For production:

- incoming lot tracking
- approved-vendor list
- no silent old-part substitution

---

# 15. KiCad symbol/footprint rule

The KiCad symbol must be created/verified from the **current v3.x datasheet**, not the old JC4880 module schematic.

Critical review:

- QFN104 pin numbering
- physical pin 54 VDD_HP_1
- VDD_HP_0/1/2/3
- dedicated HS USB pins
- dedicated MIPI pins
- flash pins
- PSRAM power pins
- exposed ground pad

Footprint shall follow current Espressif package drawing / published footprint.

---

# 16. Schematic readiness effect

Previous readiness item:

~~~text
confirm exact orderable P4 v3.x silicon
~~~

is now reduced to:

**RESOLVED FOR SCHEMATIC / PROCUREMENT-CHECK AT ORDER TIME**

Selected MPN:

**ESP32-P4NRW32X**

Remaining action is normal procurement verification, not an architectural design blocker.

---

# 17. Final decision

Pajoniiir-M1 Rev A silicon baseline:

~~~text
ESP32-P4NRW32X
target revision: v3.2 or newer approved revision
32 MB PSRAM
external 16 MB W25Q128JV flash

ESP-IDF >= 6.0
pre-v3 selector disabled
separate M1 binary / board BSP
~~~

The old ESP32-P4NRW32 rev1.3 family is not approved for the M1 PCB.
