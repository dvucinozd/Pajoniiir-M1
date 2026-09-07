#!/usr/bin/env python3
"""Validate the B7 board-packing inventory, optionally against a KiCad XML netlist."""
from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
INVENTORY = BASE / "m1_board_packing_inventory_b7.json"


def main() -> int:
    data = json.loads(INVENTORY.read_text(encoding="utf-8"))
    errors: list[str] = []
    if data.get("milestone") != "M1-PRELAYOUT-B7":
        errors.append("packing inventory milestone drift")
    if data.get("board_geometry_assumptions", {}).get("display_model_defines_outline") is not False:
        errors.append("display profile is allowed to define the board outline")
    if data.get("placement_started") is not False:
        errors.append("inventory incorrectly claims placement has started")
    if data.get("inventory", {}).get("intentional_blank_footprint_refdes") != ["C3", "C8", "J1"]:
        errors.append("intentional blank-footprint set drift")

    phases = data.get("packing_phases", [])
    if [p.get("order") for p in phases] != list(range(1, len(phases) + 1)):
        errors.append("packing phase order is not contiguous")
    if len({p.get("id") for p in phases}) != len(phases):
        errors.append("packing phase IDs are not unique")

    if len(sys.argv) == 2:
        root = ET.parse(sys.argv[1]).getroot()
        components = list(root.find("components") or [])
        observed = Counter((c.findtext("footprint") or "<blank>") for c in components)
        expected = Counter(data["inventory"]["footprint_population"])
        if len(components) != data["inventory"]["schematic_component_count"]:
            errors.append(f"component count drift: {len(components)}")
        if observed != expected:
            errors.append("footprint population drift; regenerate the B7 packing inventory")
        blank_refs = sorted(c.get("ref") for c in components if not c.findtext("footprint"))
        if blank_refs != data["inventory"]["intentional_blank_footprint_refdes"]:
            errors.append(f"blank footprint drift: {blank_refs}")
    elif len(sys.argv) > 2:
        raise SystemExit("usage: validate_board_packing_inventory.py [netlist.xml]")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(
        "PASS: B7 board packing inventory is internally consistent"
        + (" and matches the live netlist." if len(sys.argv) == 2 else ".")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
