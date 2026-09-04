# Pajoniiir-M1 — Manufacturing Output Contract v0.2

**Milestone:** M1-ELEC-B2 / M1-MECH-B5

**Updated:** 2026-09-04

**Status:** CI-enforced manufacturing-output baseline

## Authority

Engineering BOM documents describe intent. The manufacturing candidate is exported directly from the root KiCad hierarchy:

```text
hardware/Pajoniiir-M1/Pajoniiir-M1.kicad_sch
```

The current source-derived baseline is:

| Metric | Current value |
|---|---:|
| Unique `in_bom=yes` RefDes | 242 |
| DNP RefDes | 15 |
| Intentional blank-footprint gates | 3 |
| Blank-footprint RefDes | `C3`, `C8`, `J1` |

These counts are snapshots. CI derives the expected set from the 15 leaf schematics and compares it with the KiCad-generated BOM.

## CI outputs

Relevant schematic/library/tool changes produce:

```text
Pajoniiir-M1-manufacturing-bom.csv
Pajoniiir-M1-manufacturing-bom-audit.md
Pajoniiir-M1.net.xml
Pajoniiir-M1-schematic.pdf
Pajoniiir-M1-erc.json
```

The bundle is uploaded as the GitHub Actions artifact `Pajoniiir-M1-M1-SCH-A`.

## Enforced checks

`validate_manufacturing_outputs.py` fails when:

- a source `in_bom=yes` RefDes is missing from the exported BOM
- KiCad exports an unexpected RefDes
- Value or Footprint differs between source and export
- a new blank footprint appears outside the gate allowlist
- an allowlisted blank footprint becomes populated without removing the stale allowlist entry
- a manufacturing RefDes does not end with a numeric suffix

This is separate from ERC. ERC checks electrical consistency; BOM parity checks hierarchy loading and assembly database integrity.

## Current blank-footprint gates

```text
C3  input bulk capacitor; exact MPN/package waits for startup/inrush/transient EVT
C8  protected-rail bulk capacitor; exact MPN/package waits for transient EVT
J1  Switchcraft 722RAHLP; land pattern waits for unambiguous terminal-center evidence
```

J2/J3, J4/J5, J6, J7 and SW1/SW2 now have exact footprints. Their mechanical gates remain open for panel datums, cutouts, mating envelopes or local clearance, but they are no longer blank-footprint manufacturing gates.

J8/J9/J10 service interfaces are DNL/`in_bom=no` and do not appear in the manufacturing BOM.

## Current DNP set

The current 15 DNP RefDes are:

```text
C24 C72 C76 C77 C78 C79 C80 C106 C107 C108 C109 R70 R74 R99 R100
```

DNP entries remain visible in the exported assembly data so EVT tuning choices are explicit.

## Latest verified result

The latest KiCad 9 CI run covering the B5 schematic state reported:

```text
all 16 schematic files load: PASS
manufacturing BOM parity: source=242 bom=242 dnp=15 blank_gates=3 PASS
native ERC: unexplained_errors=0 excluded_errors=0 warnings=0
```

Historical run #76 reported 270/270, 17 DNP and 12 blank gates before the J6 audio removal, D1 lock, DSI506 migration and B4 footprint locks. Those numbers are retained only as historical evidence and are not the current baseline.

## Sign-off interpretation

Passing the workflow proves:

1. structural schematic contracts pass
2. every schematic loads under native KiCad 9
3. native ERC has no unexplained errors or warnings
4. KiCad exports the manufacturing BOM
5. exported RefDes/Value/Footprint data match the source hierarchy
6. KiCad exports the hierarchy netlist
7. KiCad generates the complete schematic PDF

It does not authorize PCB fabrication. Final manufacturing sign-off still requires closure of all layout-blocking mechanical/EVT gates, final `Edge.Cuts`, production impedance rules, PCB DRC and fabrication-output review.
