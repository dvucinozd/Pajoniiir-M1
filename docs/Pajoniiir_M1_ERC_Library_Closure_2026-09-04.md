# KiCad 10 ERC and library closure

Local verification date: 2026-09-04. Tool: KiCad 10.0.4. This record covers the working-tree changes after the B5 KiCad 9 CI baseline at `667fd01`; it does not claim a new KiCad 9 CI result.

## Changes

The initial native KiCad 10 report contained two dangling root labels (`EFUSE_PG`, `3V3_PG`) and four warnings: the missing U14 footprint and standard-library mismatches at J2/J3/J7.

- TP25 exposes `EFUSE_PG` in `01_POWER_INPUT`: U7.3, R6.2 and TP25.1.
- TP26 exposes `3V3_PG` in `02_POWER_3V3`: U8.4, R21.2 and TP26.1.
- Unused root sheet outputs now have no-connect markers. The child diagnostic nets remain connected, with existing pull-ups. No P4 GPIO is assigned to either PG signal.
- J2/J3 use project-owned `USB_A_M1`; J7 uses `MicroSD_Det1_M1`. These preserve the existing electrical pin numbers, including USB shield pin 5 and microSD shield pin 10, across standard-library updates.
- U14 uses project footprint `Texas_DGS0010A_VSSOP-10_3x3mm_P0.5mm`. The [TI INA238 datasheet](https://www.ti.com/lit/ds/symlink/ina238.pdf), DGS0010A example board layout, specifies ten 1.45 x 0.30 mm lands, 0.50 mm pitch and 4.40 mm between row centers, with no exposed pad.

## Verification

Retained evidence: [native ERC report](../hardware/Pajoniiir-M1/evidence/erc-kicad10-after-2026-09-04.json), [BOM audit](../hardware/Pajoniiir-M1/evidence/bom-audit-2026-09-04.md) and [schematic source fingerprints](../hardware/Pajoniiir-M1/evidence/erc-source-manifest-2026-09-04.json).

Native ERC reports zero violations across the root and all 15 leaf sheets. The exported netlist preserves every pre-existing net's node membership when TP25/TP26 are removed from the comparison. The source/export BOM parity is 244/244, including 15 DNP entries and the same three intentional blank footprints (C3, C8, J1). Total instantiated RefDes is 247, including the three DNL service interfaces.

`validate_power_good_closure.py` checks all 16 per-sheet ERC violation lists, exact PG net membership, project connector symbols/shield pins and U14's footprint assignment. CI runs this after generating the native ERC and netlist reports.

The local MCP server's ERC summary was not used as acceptance evidence: it reads a top-level violation list, while the native KiCad report stores violations under `sheets[].violations`. The native report and downstream validator are the acceptance path.

KiCad 10 netlist export prints a non-fatal annotation warning both on the pre-change backup and on the updated hierarchy. Export succeeds; structural RefDes/unit checks and complete BOM parity pass. The warning remains a separate KiCad compatibility observation, not a newly introduced connectivity failure.

## Remaining boundary

This closes the observed local ERC/library findings. It does not close J1's land-pattern or panel geometry, display FFC continuity/clearance, final enclosure tolerances after the rear-PCB height correction, or the other mechanical/EVT release gates. Future local and CI validation uses KiCad 10 only.
