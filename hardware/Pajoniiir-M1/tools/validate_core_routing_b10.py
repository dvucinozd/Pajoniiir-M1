#!/usr/bin/env python3
"""Validate the reversible M1-PRELAYOUT-B10 critical-route proof."""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import pcbnew


EXPECTED_QSPI = {"FLASH_CS", "FLASH_Q", "FLASH_WP", "FLASH_HOLD", "FLASH_CK", "FLASH_D"}
CRYSTAL_NETS = {"/XTAL_P", "/XTAL_N", "/04_P4_FLASH_CLOCK_RESET/XTAL_P_NODE"}
QSPI_VIA_NETS = {
    "Net-(U2-~{CS})",
    "Net-(U2-DO/IO_{1})",
    "Net-(U2-~{WP}/IO_{2})",
}
APPROVED_NETS = CRYSTAL_NETS | QSPI_VIA_NETS | {
    "/04_P4_FLASH_CLOCK_RESET/FLASH_CS",
    "/03_P4_CORE/FLASH_Q",
    "/03_P4_CORE/FLASH_WP",
    "/03_P4_CORE/FLASH_HOLD",
    "/03_P4_CORE/FLASH_CK",
    "/03_P4_CORE/FLASH_D",
    "Net-(U2-~{HOLD}/~{RESET}/IO_{3})",
    "Net-(U2-CLK)",
    "Net-(U2-DI/IO_{0})",
    "/3V3_SYS",
    "/03_P4_CORE/P4_CORE_SW",
    "/03_P4_CORE/P4_VDD_HP",
    "/03_P4_CORE/P4_EN_DCDC",
    "/03_P4_CORE/P4_FB_DCDC",
    "/03_P4_CORE/FLASH_VCC",
}
ROUTE_DRC_TYPES = {
    "shorting_items",
    "tracks_crossing",
    "clearance",
    "hole_clearance",
    "track_width",
    "via_dangling",
    "drill_out_of_range",
}


def length_mm(track: pcbnew.PCB_TRACK) -> float:
    start = track.GetStart()
    end = track.GetEnd()
    return math.hypot(pcbnew.ToMM(start.x - end.x), pcbnew.ToMM(start.y - end.y))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, required=True)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--drc", type=Path, required=True)
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board.resolve()))
    if board is None:
        raise RuntimeError(f"Cannot load board: {args.board}")
    report = json.loads(args.report.read_text(encoding="utf-8"))
    project = json.loads(args.project.read_text(encoding="utf-8-sig"))
    drc = json.loads(args.drc.read_text(encoding="utf-8-sig"))
    errors: list[str] = []

    if report.get("milestone") != "M1-PRELAYOUT-B10":
        errors.append("report milestone is not M1-PRELAYOUT-B10")
    for field in ("production_layout", "layout_freeze_allowed", "edge_cuts_present", "zones_present"):
        if report.get(field) is not False:
            errors.append(f"B10 report must keep {field}=false")

    default_classes = [
        entry for entry in project.get("net_settings", {}).get("classes", []) if entry.get("name") == "Default"
    ]
    if len(default_classes) != 1 or default_classes[0].get("clearance") != 0.15:
        errors.append("project Default netclass clearance must be exactly 0.15 mm for the P4 fine-pitch escape")

    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    if len(footprints) != 244:
        errors.append(f"expected 244 footprints, found {len(footprints)}")

    u8 = footprints.get("U8")
    if u8 is None:
        errors.append("U8 footprint is missing")
    else:
        expected_u8_fpid = "Pajoniiir-M1:VQFN-16-1EP_3x3mm_P0.5mm_EP1.68x1.68mm_ThermalVias"
        if u8.GetFPID().GetUniStringLibId() != expected_u8_fpid:
            errors.append("U8 must use the project-local 0.30 mm thermal-via footprint")
        thermal_drills = sorted(
            round(pcbnew.ToMM(pad.GetDrillSize().x), 3)
            for pad in u8.Pads()
            if pad.GetNumber() == "17" and pad.GetDrillSize().x > 0
        )
        if thermal_drills != [0.3, 0.3, 0.3, 0.3]:
            errors.append(f"U8 must retain four 0.30 mm thermal drills, found {thermal_drills}")
    for ref, record in report.get("placement_changes", {}).items():
        fp = footprints.get(ref)
        if fp is None:
            errors.append(f"missing B10 placement footprint: {ref}")
            continue
        position = fp.GetPosition()
        observed = {
            "x": round(pcbnew.ToMM(position.x), 3),
            "y": round(pcbnew.ToMM(position.y), 3),
            "rotation_deg": round(fp.GetOrientationDegrees() % 360.0, 3),
            "side": "F.Cu" if fp.GetLayer() == pcbnew.F_Cu else "B.Cu",
        }
        expected = {
            "x": round(record["x"], 3),
            "y": round(record["y"], 3),
            "rotation_deg": round(record["rotation_deg"] % 360.0, 3),
            "side": record["side"],
        }
        if observed != expected:
            errors.append(f"{ref}: placement drift {observed} != {expected}")

    edge_cuts = sum(1 for item in board.GetDrawings() if item.GetLayer() == pcbnew.Edge_Cuts)
    zones = len(list(board.Zones()))
    if edge_cuts or zones:
        errors.append(f"B10 must remain outline/zone-free: Edge.Cuts={edge_cuts}, zones={zones}")

    lengths: dict[str, float] = defaultdict(float)
    layers: dict[str, int] = defaultdict(int)
    widths: dict[str, set[float]] = defaultdict(set)
    vias_by_net: dict[str, int] = defaultdict(int)
    via_sizes: set[tuple[float, float]] = set()
    segment_count = 0
    via_count = 0
    for item in board.GetTracks():
        name = item.GetNetname()
        if name not in APPROVED_NETS:
            errors.append(f"unapproved routed net in B10: {name}")
        if isinstance(item, pcbnew.PCB_VIA):
            via_count += 1
            vias_by_net[name] += 1
            via_sizes.add(
                (
                    round(pcbnew.ToMM(item.GetWidth(pcbnew.F_Cu)), 3),
                    round(pcbnew.ToMM(item.GetDrillValue()), 3),
                )
            )
            continue
        segment_count += 1
        layer = board.GetLayerName(item.GetLayer())
        layers[layer] += 1
        widths[name].add(round(pcbnew.ToMM(item.GetWidth()), 3))
        lengths[name] += length_mm(item)
        if name in CRYSTAL_NETS and item.GetLayer() != pcbnew.F_Cu:
            errors.append(f"crystal net leaves F.Cu: {name} on {layer}")
        if name.startswith("Net-(U2-") and name not in QSPI_VIA_NETS and item.GetLayer() != pcbnew.F_Cu:
            errors.append(f"direct QSPI flash-side net leaves F.Cu: {name} on {layer}")

    if any(vias_by_net[name] for name in CRYSTAL_NETS):
        errors.append("crystal routes contain vias")
    qspi_signal_vias = sum(vias_by_net[name] for name in QSPI_VIA_NETS)
    if qspi_signal_vias != 6 or any(vias_by_net[name] != 2 for name in QSPI_VIA_NETS):
        errors.append(f"expected one 2-via transition on each package-opposed QSPI net, found {dict(vias_by_net)}")
    if via_sizes != {(0.6, 0.3)}:
        errors.append(f"B10 vias must use the project-safe 0.60/0.30 mm geometry: {sorted(via_sizes)}")

    metrics = report.get("metrics", {})
    if metrics.get("u8_thermal_via_drill_mm") != 0.3:
        errors.append("B10 report must record the 0.30 mm U8 thermal-via drill")
    named_net_count = board.GetNetCount() - 1
    if named_net_count != 193 or metrics.get("named_net_count") != named_net_count:
        errors.append(f"expected 193 named nets and matching report, found {named_net_count}")
    observed_layer_counts = dict(sorted(layers.items()))
    if metrics.get("track_segment_count") != segment_count:
        errors.append("report track-segment count does not match board")
    if metrics.get("via_count") != via_count:
        errors.append("report via count does not match board")
    if metrics.get("track_segments_by_layer") != observed_layer_counts:
        errors.append("report layer counts do not match board")
    observed_lengths = {name: round(value, 3) for name, value in sorted(lengths.items())}
    if metrics.get("track_length_by_net_mm") != observed_lengths:
        errors.append("report net lengths do not match board")
    if metrics.get("qspi_signal_via_count") != qspi_signal_vias:
        errors.append("report QSPI via count does not match board")
    if metrics.get("crystal_body_gap_to_U1_mm", 0.0) < 4.5:
        errors.append("crystal body gap to U1 is below 4.5 mm")
    if metrics.get("p4_footprint_bbox_overlap_count") != 0:
        errors.append("P4 group contains footprint bounding-box overlaps")

    qspi = metrics.get("qspi_end_to_end_track_length_mm", {})
    if set(qspi) != EXPECTED_QSPI:
        errors.append(f"QSPI route set drift: {sorted(qspi)}")
    elif max(qspi.values()) - min(qspi.values()) > 12.5:
        errors.append(f"QSPI feasibility length spread exceeds 12.5 mm: {qspi}")

    for name in ("/3V3_SYS", "/03_P4_CORE/P4_CORE_SW"):
        observed = widths.get(name, set())
        if 0.65 not in observed or min(observed or {1.0}) > 0.20:
            errors.append(f"power net must retain a 0.65 mm trunk and <=0.20 mm package neck: {name} {sorted(observed)}")
    hp_widths = widths.get("/03_P4_CORE/P4_VDD_HP", set())
    if 0.65 not in hp_widths or 0.15 not in hp_widths:
        errors.append(f"VDD_HP must retain the 0.65 mm trunk and 0.15 mm sense/package necks: {sorted(hp_widths)}")

    route_drc = []
    for violation in drc.get("violations", []):
        item_text = " ".join(item.get("description", "") for item in violation.get("items", []))
        if violation.get("type") in ROUTE_DRC_TYPES and ("Track [" in item_text or "Via [" in item_text):
            route_drc.append(violation)
    if route_drc:
        errors.append(f"KiCad DRC found {len(route_drc)} B10 route-geometry violation(s)")

    label = any(
        isinstance(item, pcbnew.PCB_TEXT)
        and item.GetText() == "P4_CORE - B10 CRITICAL-ROUTE PROOF"
        for item in board.GetDrawings()
    )
    if not label:
        errors.append("B10 P4 working-group label is absent")

    print("M1-PRELAYOUT-B10 critical-route validation")
    print(f"  footprints: {len(footprints)}")
    print(f"  tracks/vias/zones/Edge.Cuts: {segment_count}/{via_count}/{zones}/{edge_cuts}")
    print(f"  routed layers: {observed_layer_counts}")
    print(f"  QSPI route lengths: {qspi}")
    print(f"  QSPI spread: {metrics.get('qspi_length_spread_mm')} mm")
    print(f"  crystal body gap: {metrics.get('crystal_body_gap_to_U1_mm')} mm")
    print(f"  KiCad DRC: {len(drc.get('violations', []))} total, {len(route_drc)} route-geometry")
    print(f"  remaining unrouted items: {len(drc.get('unconnected_items', []))}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("PASS: critical P4 routes match the reversible B10 feasibility contract.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
