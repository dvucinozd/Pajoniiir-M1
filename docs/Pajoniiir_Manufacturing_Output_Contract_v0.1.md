# Pajoniiir-M1 — Manufacturing Output Contract v0.1

**Datum:** 2026-09-03  
**Milestone:** M1-SCH-A  
**Status:** CI-enforced manufacturing-output baseline

---

## Purpose

`docs/Pajoniiir_Mainboard_BOM_v0.2.md` is an engineering-intent BOM. It was assembled before and during schematic capture and intentionally uses subsystem-oriented names, grouped quantities and TBD gates. It is not a manufacturing netlist and must not be used as a 1:1 substitute for the KiCad design database.

The authoritative manufacturing candidate is exported directly from the root hierarchical schematic with KiCad 9.

Current source baseline contains:

- **270** unique RefDes with `in_bom=yes`
- **17** DNP RefDes included for assembly-option visibility
- **12** intentional `in_bom=yes` blank-footprint gates
- additional DNL/service elements such as `JDBG_USB` may remain `in_bom=no`

These counts are a snapshot, not a hard-coded invariant. CI derives the current expected set from the 15 leaf schematics and compares it against the KiCad-generated BOM.

---

## CI outputs

Every relevant schematic/library/tool change now produces the M1-SCH-A review bundle:

~~~text
Pajoniiir-M1-manufacturing-bom.csv
Pajoniiir-M1-manufacturing-bom-audit.md
Pajoniiir-M1.net.xml
Pajoniiir-M1-schematic.pdf
Pajoniiir-M1-erc.json
~~~

The bundle is uploaded as the GitHub Actions artifact:

~~~text
Pajoniiir-M1-M1-SCH-A
~~~

The generated BOM is exported with one row per RefDes and includes Reference, Value, Footprint, Quantity and DNP state.

---

## Machine checks

`validate_manufacturing_outputs.py` compares the KiCad BOM with the source hierarchy and fails CI when:

- a source `in_bom=yes` RefDes is missing from the KiCad BOM
- KiCad emits an unexpected RefDes
- Value differs between source and generated BOM
- Footprint differs between source and generated BOM
- a new blank footprint appears outside the approved manufacturing gate set
- an approved blank-footprint gate becomes populated without removing the stale allowlist entry

This is deliberately separate from ERC. ERC proves electrical-rule consistency; manufacturing-output parity proves that hierarchy loading and BOM extraction preserve the assembly database.

---

## Intentional blank-footprint manufacturing gates

Current `in_bom=yes` gates:

~~~text
J1
C3
D1
C8
SW1
SW2
J2
J3
J4
J5
J6
J7
~~~

`J_LCD` is a documentation alias, not an instantiated RefDes. It is not in this list because the physical display connector remains intentionally uninstantiated until its mating geometry and remaining pin-domain questions are closed.

---

## Sign-off interpretation

Passing CI now means:

1. structural schematic contracts pass
2. all schematics load under native KiCad 9
3. native ERC has no unexplained errors or warnings
4. KiCad can export the full manufacturing BOM
5. KiCad BOM RefDes/Value/Footprint data match the source hierarchy
6. KiCad can export a hierarchy netlist
7. KiCad can generate the complete multi-page schematic PDF

It does **not** mean final production sign-off.

Run #76 additionally completed the review-layer checks: 16/16 schematic PDF pages were rendered and visually reviewed, and the generated manufacturing BOM was reviewed against engineering intent with 270/270 parity, 17 DNP entries and exactly 12 intentional blank-footprint gates.

Still manual/physical:

Hierarchy pin synchronization is no longer a manual gate: CI compares every child hierarchical label with the corresponding root sheet pin in both directions by name and electrical shape, then native KiCad 9 loads and exports the full root hierarchy. A GUI open/save remains optional editor hygiene only.

- exact LCD/FPC mechanical closure
- exact external connector MPN/footprints
- final board outline and enclosure datums
- PCB-fabricator stackup and controlled-impedance rules
