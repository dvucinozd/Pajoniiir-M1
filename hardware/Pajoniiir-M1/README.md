# Pajoniiir-M1 KiCad Rev A

Live KiCad 9 project for the Pajoniiir-M1 custom mainboard.

## Current design state

- Electrical milestone: M1-ELEC-B2
- Mechanical milestone: M1-MECH-B5
- Pre-layout milestone: M1-PRELAYOUT-B5
- Root schematic plus 15 leaf sheets: structurally clean
- Current manufacturing source: 242 `in_bom=yes`, 15 DNP, 3 intentional blank footprints
- PCB: empty four-layer pre-layout shell, no footprints/routes/`Edge.Cuts`
- Final placement/routing freeze: blocked by 12 physical/EVT gates

The active display is EYOYO DSI506 / DYL0023 with the instantiated Amphenol SFW15R-2STE1LF 15-pin connector. `11_TOUCH_GT911.kicad_sch` is intentionally retired and empty because touch/backlight are module-integrated.

## Authorities

1. `*.kicad_sch` — connectivity, RefDes, values and footprints
2. `mechanical_gates.json` — gate and freeze state
3. `m1_mech_b5_placement_skeleton.json` — B5 placement screening
4. `m1_prelayout_b5_routing_contract.json` — routing topology and impedance state
5. `m1_mech_b4_connector_source_lock.json` — production connector intent
6. `m1_mech_b3_mainboard_io_envelope.json` and `m1_mech_b3_enclosure_candidate.json` — screening envelopes
7. `final_display_module.json`, `display_connector_b1.json` and DSI506 evidence/lock files

Human-readable current state: `../../docs/Pajoniiir_M1_Current_Design_Status_B5.md`.

## Mechanical and routing boundary

The 104 x 62 mm core board and 128 x 84 x 30 mm enclosure are screening candidates, not final production geometry. The direct four-post M2.5 mount is locked; the final NPTH diameter, screw-head/washer geometry, side wings, panel datums and `Edge.Cuts` remain open.

The selected stackup is JLCPCB JLC04161H-7628, four layers and 1.6 mm. Exact 90 ohm USB and 100 ohm MIPI width/gap values still require a recorded JLCPCB calculator result before routing freeze.

Do not add production `Edge.Cuts`, call screening anchors final placement, or release Gerbers while `layout_freeze_allowed` is false.

## Validation

Run from the repository root:

```bash
python hardware/Pajoniiir-M1/tools/validate_schematic_structure.py
python hardware/Pajoniiir-M1/tools/validate_mechanical_authority.py
python hardware/Pajoniiir-M1/tools/validate_b4_panel_windows.py
python hardware/Pajoniiir-M1/tools/validate_b5_placement_skeleton.py
python hardware/Pajoniiir-M1/tools/report_mech_gate_snapshot.py
```

Native KiCad 9 ERC, hierarchy load, manufacturing BOM parity, netlist and PDF export are enforced in CI.
