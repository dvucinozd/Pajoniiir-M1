#!/usr/bin/env python3
"""Check native ERC and netlist evidence for the PG diagnostic additions.

Run after exporting the complete hierarchy with kicad-cli. This deliberately
reads per-sheet ERC violations; an absent top-level list is not a clean report.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def validate(netlist_path: Path, erc_path: Path) -> None:
    report = json.loads(erc_path.read_text(encoding="utf-8"))
    sheets = report.get("sheets")
    if not isinstance(sheets, list) or len(sheets) != 16:
        raise ValueError("Expected a native ERC report covering all 16 schematic sheets")
    violations = list(report.get("violations", []))
    for sheet in sheets:
        if not isinstance(sheet.get("violations"), list):
            raise ValueError("ERC sheet has no explicit violations list")
        violations.extend(sheet["violations"])
    if violations:
        raise ValueError(f"ERC is not clean: {len(violations)} violations (including exclusions)")

    root = ET.parse(netlist_path).getroot()
    nets = [
        {(n.get("ref"), n.get("pin")) for n in net.findall("node")}
        for net in root.findall("./nets/net")
    ]
    expected = {
        "TP25": {("TP25", "1"), ("U7", "3"), ("R6", "2")},
        "TP26": {("TP26", "1"), ("U8", "4"), ("R21", "2")},
    }
    for ref, nodes in expected.items():
        matches = [net for net in nets if (ref, "1") in net]
        if matches != [nodes]:
            raise ValueError(f"{ref}: diagnostic PG net has missing or unexpected connections: {matches}")

    components = {c.get("ref"): c for c in root.findall("./components/comp")}
    for ref, symbol, shield_pin in [
        ("J2", "USB_A_M1", "5"),
        ("J3", "USB_A_M1", "5"),
        ("J7", "MicroSD_Det1_M1", "10"),
    ]:
        component = components[ref]
        source = component.find("libsource")
        if source is None or source.get("lib") != "Pajoniiir-M1" or source.get("part") != symbol:
            raise ValueError(f"{ref}: expected project-owned connector symbol {symbol}")
        if not any((ref, shield_pin) in net for net in nets):
            raise ValueError(f"{ref}: footprint-compatible shield pin {shield_pin} is missing")
    footprint = components["U14"].findtext("footprint")
    if footprint != "Pajoniiir-M1:Texas_DGS0010A_VSSOP-10_3x3mm_P0.5mm":
        raise ValueError(f"U14: unexpected footprint: {footprint}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("netlist", type=Path)
    parser.add_argument("erc", type=Path)
    args = parser.parse_args()
    validate(args.netlist, args.erc)
    print("PASS: native ERC clean; PG diagnostics, connector shields and U14 footprint verified")


if __name__ == "__main__":
    main()
