#!/usr/bin/env python3
"""Validate the reversible M1-PRELAYOUT-B8 populated PCB canvas."""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pcbnew


def component_records(root: ET.Element) -> tuple[dict[str, dict[str, object]], set[str]]:
    elements = root.find("components")
    if elements is None:
        raise RuntimeError("Netlist has no components section")
    records: dict[str, dict[str, object]] = {}
    blanks: set[str] = set()
    for element in elements:
        props = {
            prop.get("name", ""): prop.get("value", "")
            for prop in element.findall("property")
        }
        ref = element.get("ref", "")
        fpid = (element.findtext("footprint") or "").strip()
        sheetpath = element.find("sheetpath")
        sheet_tstamp = (sheetpath.get("tstamps", "/") if sheetpath is not None else "/").rstrip("/")
        component_tstamps = (element.findtext("tstamps") or "").strip("/").split()
        if not component_tstamps:
            raise RuntimeError(f"{ref}: component has no schematic timestamp")
        component_tstamp = component_tstamps[0]
        path = f"{sheet_tstamp}/{component_tstamp}" if sheet_tstamp else f"/{component_tstamp}"
        records[ref] = {
            "value": element.findtext("value") or "",
            "fpid": fpid,
            "sheetname": props.get("Sheetname", ""),
            "sheetfile": props.get("Sheetfile", ""),
            "path": path,
            "dnp": "dnp" in props,
            "exclude_from_bom": "exclude_from_bom" in props,
        }
        if not fpid:
            blanks.add(ref)
    return records, blanks


def net_assignments(root: ET.Element) -> list[tuple[str, str, str]]:
    elements = root.find("nets")
    if elements is None:
        raise RuntimeError("Netlist has no nets section")
    result: list[tuple[str, str, str]] = []
    for net in elements:
        name = net.get("name", "")
        for node in net.findall("node"):
            result.append((node.get("ref", ""), node.get("pin", ""), name))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, required=True)
    parser.add_argument("--netlist", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board.resolve()))
    if board is None:
        raise RuntimeError(f"Cannot load board: {args.board}")
    root = ET.parse(args.netlist).getroot()
    expected, blank_refs = component_records(root)
    expected_refs = {ref for ref, record in expected.items() if record["fpid"]}
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    errors: list[str] = []

    if set(footprints) != expected_refs:
        errors.append(
            f"footprint RefDes mismatch: missing={sorted(expected_refs - set(footprints))} "
            f"extra={sorted(set(footprints) - expected_refs)}"
        )
    if blank_refs != {"C3", "C8", "J1"}:
        errors.append(f"unexpected blank-footprint set: {sorted(blank_refs)}")

    for ref in sorted(expected_refs & set(footprints)):
        fp = footprints[ref]
        record = expected[ref]
        checks = {
            "value": fp.GetValue(),
            "fpid": fp.GetFPIDAsString(),
            "sheetname": fp.GetSheetname(),
            "sheetfile": fp.GetSheetfile(),
            "path": fp.GetPath().AsString(),
            "dnp": fp.IsDNP(),
            "exclude_from_bom": fp.IsExcludedFromBOM(),
        }
        for field, actual in checks.items():
            if actual != record[field]:
                errors.append(f"{ref}: {field} expected={record[field]!r} actual={actual!r}")

    checked_nodes = 0
    for ref, pin, expected_net in net_assignments(root):
        if ref in blank_refs:
            continue
        fp = footprints.get(ref)
        if fp is None:
            continue
        pads = [pad for pad in fp.Pads() if pad.GetNumber() == pin]
        if not pads:
            errors.append(f"{ref}.{pin}: pad absent")
            continue
        actual_nets = {pad.GetNetname() for pad in pads}
        if actual_nets != {expected_net}:
            errors.append(f"{ref}.{pin}: expected net {expected_net!r}, got {sorted(actual_nets)!r}")
        checked_nodes += 1

    edge_cuts = sum(1 for item in board.GetDrawings() if item.GetLayer() == pcbnew.Edge_Cuts)
    if edge_cuts:
        errors.append(f"Edge.Cuts must remain absent, found {edge_cuts} item(s)")
    track_count = len(list(board.GetTracks()))
    zone_count = len(list(board.Zones()))
    if track_count:
        errors.append(f"B8 canvas must remain unrouted, found {track_count} track/via item(s)")
    if zone_count:
        errors.append(f"B8 canvas must have no zones, found {zone_count}")

    report = json.loads(args.report.read_text(encoding="utf-8"))
    if report.get("milestone") != "M1-PRELAYOUT-B8":
        errors.append("placement report milestone is not M1-PRELAYOUT-B8")
    if report.get("production_layout") is not False or report.get("edge_cuts_present") is not False:
        errors.append("placement report must remain explicitly non-production and without Edge.Cuts")
    domain_refs = {
        ref
        for domain in report.get("placement_domains", {}).values()
        for ref in domain.get("refs", [])
    }
    if domain_refs != expected_refs:
        errors.append("placement report domain RefDes set does not match populated PCB")

    print("M1-PRELAYOUT-B8 board validation")
    print(f"  footprints: {len(footprints)}")
    net_elements = root.find("nets")
    print(f"  schematic nets: {len(net_elements) if net_elements is not None else 0}")
    print(f"  checked connected nodes: {checked_nodes}")
    print(f"  tracks/zones/Edge.Cuts: {track_count}/{zone_count}/{edge_cuts}")
    print(f"  domains: {len(report.get('placement_domains', {}))}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("PASS: populated board matches schematic and remains a reversible board-first canvas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
