# Pajoniiir-M1 KiCad Rev A

Live KiCad 9 project for the Pajoniiir-M1 custom mainboard.

## Current design state

- Electrical milestone: M1-ELEC-B2
- Mechanical milestone: M1-MECH-B7
- Pre-layout milestone: M1-PRELAYOUT-B8 populated domain canvas
- Root schematic plus 15 leaf sheets: structurally clean
- Current manufacturing source: 244 `in_bom=yes`, 15 DNP, 3 intentional blank footprints
- PCB: 244 footprints and 193 named nets in eight reversible working domains; no routes/zones/`Edge.Cuts`
- Board packing inventory: 247 schematic components, 244 assigned footprints, 3 intentional blanks
- Final placement/routing freeze: blocked by 12 physical/EVT gates

J6 is a generic 15-pin Raspberry-Pi-style MIPI DSI host using Amphenol SFW15R-2STE1LF. DSI506 / DYL0023 is one validated display profile. `11_TOUCH_GT911.kicad_sch` stays empty because touch behavior belongs to the selected display profile.

## Authorities

1. `*.kicad_sch` — connectivity, RefDes, values and footprints
2. `board_first_mechanical_contract.json` — mainboard geometry boundary
3. `mechanical_gates.json` and `pcb_constraints.json` — freeze and layout gates
4. `m1_prelayout_b5_routing_contract.json` — routing topology and impedance state
5. `m1_board_packing_inventory_b7.json` — footprint population and packing sequence
6. `m1_board_placement_seed_b8.json` — populated-domain coordinates and non-production boundary
7. `m1_mech_b4_connector_source_lock.json` — exact external connector intent
8. `display_compatibility_dsi506.json` — first qualified display profile

The B2-B6 display-mounted placement and enclosure JSON files are retained as historical DSI506 screening only.

Human-readable current state: `../../docs/Pajoniiir_M1_Current_Design_Status_B8.md`.

## Mechanical and routing boundary

The board mounts to its own chassis. Final `Edge.Cuts`, chassis holes, connector coordinates and height zones must come from board component packing, routing and service requirements. Display rear posts and display-derived board/enclosure screens are not production authority.

The selected stackup is JLCPCB JLC04161H-7628, four layers and 1.6 mm. Exact 90 ohm USB and 100 ohm MIPI width/gap values still require a recorded JLCPCB calculator result before routing freeze.

Do not add production `Edge.Cuts`, call screening anchors final placement, or release Gerbers while `layout_freeze_allowed` is false.

## Validation

Run from the repository root:

```bash
python hardware/Pajoniiir-M1/tools/validate_schematic_structure.py
python hardware/Pajoniiir-M1/tools/validate_mechanical_authority.py
python hardware/Pajoniiir-M1/tools/validate_board_packing_inventory.py
python hardware/Pajoniiir-M1/tools/report_mech_gate_snapshot.py
"C:/Program Files/KiCad/10.0/bin/python.exe" hardware/Pajoniiir-M1/tools/validate_board_placement_b8.py \
  --board hardware/Pajoniiir-M1/Pajoniiir-M1.kicad_pcb \
  --netlist <fresh-kicad-xml-netlist> \
  --report hardware/Pajoniiir-M1/m1_board_placement_seed_b8.json
```

Native KiCad ERC, hierarchy load, manufacturing BOM parity, netlist and PDF export are enforced in CI. B8 placement validation additionally uses KiCad's bundled `pcbnew` Python module locally.
