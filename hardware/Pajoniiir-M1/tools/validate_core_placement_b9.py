#!/usr/bin/env python3
"""Validate the reversible M1-PRELAYOUT-B9 ESP32-P4 core island."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import pcbnew


P4_SHEETS = {"03_P4_CORE", "04_P4_FLASH_CLOCK_RESET"}
POSITION_TOLERANCE_MM = 0.002


def bbox_edges_mm(fp: pcbnew.FOOTPRINT) -> tuple[float, float, float, float]:
    box = fp.GetBoundingBox()
    return (
        pcbnew.ToMM(box.GetLeft()),
        pcbnew.ToMM(box.GetTop()),
        pcbnew.ToMM(box.GetRight()),
        pcbnew.ToMM(box.GetBottom()),
    )


def bbox_gap_mm(a: pcbnew.FOOTPRINT, b: pcbnew.FOOTPRINT) -> float:
    al, at, ar, ab = bbox_edges_mm(a)
    bl, bt, br, bb = bbox_edges_mm(b)
    return math.hypot(max(bl - ar, al - br, 0.0), max(bt - ab, at - bb, 0.0))


def overlap_pairs(footprints: list[pcbnew.FOOTPRINT]) -> list[tuple[str, str]]:
    overlaps: list[tuple[str, str]] = []
    for index, first in enumerate(footprints):
        al, at, ar, ab = bbox_edges_mm(first)
        for second in footprints[index + 1 :]:
            bl, bt, br, bb = bbox_edges_mm(second)
            if min(ar, br) > max(al, bl) and min(ab, bb) > max(at, bt):
                overlaps.append((first.GetReference(), second.GetReference()))
    return overlaps


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board.resolve()))
    if board is None:
        raise RuntimeError(f"Cannot load board: {args.board}")
    report = json.loads(args.report.read_text(encoding="utf-8"))
    errors: list[str] = []

    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    p4 = {
        ref: fp
        for ref, fp in footprints.items()
        if fp.GetSheetname() in P4_SHEETS
    }
    expected = report.get("placements_mm", {})
    if set(p4) != set(expected):
        errors.append(
            f"P4 RefDes mismatch: missing={sorted(set(expected) - set(p4))} "
            f"extra={sorted(set(p4) - set(expected))}"
        )

    for ref in sorted(set(p4) & set(expected)):
        fp = p4[ref]
        position = fp.GetPosition()
        actual = (
            pcbnew.ToMM(position.x),
            pcbnew.ToMM(position.y),
            fp.GetOrientationDegrees() % 360.0,
        )
        record = expected[ref]
        wanted = (record["x"], record["y"], record["rotation_deg"] % 360.0)
        if any(abs(a - b) > POSITION_TOLERANCE_MM for a, b in zip(actual, wanted)):
            errors.append(f"{ref}: placement drift actual={actual} expected={wanted}")

    edge_cuts = sum(1 for item in board.GetDrawings() if item.GetLayer() == pcbnew.Edge_Cuts)
    track_count = len(list(board.GetTracks()))
    zone_count = len(list(board.Zones()))
    if track_count or zone_count or edge_cuts:
        errors.append(f"B9 must remain unrouted and outline-free: {track_count}/{zone_count}/{edge_cuts}")

    if report.get("milestone") != "M1-PRELAYOUT-B9":
        errors.append("report milestone is not M1-PRELAYOUT-B9")
    if report.get("production_layout") is not False or report.get("layout_freeze_allowed") is not False:
        errors.append("B9 report must remain explicitly non-production and fail-closed")
    if report.get("edge_cuts_present") is not False:
        errors.append("B9 report incorrectly permits Edge.Cuts")

    overlaps = overlap_pairs(list(p4.values()))
    if overlaps:
        errors.append(f"P4 footprint bounding-box overlaps: {overlaps}")

    crystal_gap = bbox_gap_mm(p4["U1"], p4["Y1"])
    if crystal_gap + POSITION_TOLERANCE_MM < 4.5:
        errors.append(f"U1/Y1 body gap {crystal_gap:.3f} mm is below 4.5 mm")

    metrics = report.get("metrics", {})
    recorded_gap = metrics.get("crystal_body_gap_to_U1_mm")
    if not isinstance(recorded_gap, (int, float)) or abs(recorded_gap - crystal_gap) > 0.01:
        errors.append("report crystal clearance does not match the board")
    if metrics.get("p4_footprint_bbox_overlap_count") != len(overlaps):
        errors.append("report overlap count does not match the board")

    xs: list[float] = []
    ys: list[float] = []
    for fp in p4.values():
        left, top, right, bottom = bbox_edges_mm(fp)
        xs.extend((left, right))
        ys.extend((top, bottom))
    actual_bbox = {
        "left": round(min(xs), 3),
        "top": round(min(ys), 3),
        "right": round(max(xs), 3),
        "bottom": round(max(ys), 3),
        "width": round(max(xs) - min(xs), 3),
        "height": round(max(ys) - min(ys), 3),
    }
    group_bbox = metrics.get("p4_group_bbox_mm", {})
    if group_bbox != actual_bbox:
        errors.append(f"report P4 bounding box does not match the board: {group_bbox} != {actual_bbox}")
    if actual_bbox["width"] > 72.0 or actual_bbox["height"] > 60.056:
        errors.append(f"P4 group exceeds its B8 working rectangle: {actual_bbox}")

    actual_centers: dict[str, float] = {}
    for first, second, limit in (("U1", "U2", 17.0), ("U1", "U3", 16.0), ("U3", "L1", 7.5)):
        a = p4[first].GetPosition()
        b = p4[second].GetPosition()
        distance = math.hypot(pcbnew.ToMM(a.x - b.x), pcbnew.ToMM(a.y - b.y))
        actual_centers[f"{first}_{second}"] = round(distance, 3)
        if distance > limit:
            errors.append(f"{first}/{second} center distance {distance:.3f} mm exceeds {limit:.3f} mm")
    if metrics.get("center_distances_mm") != actual_centers:
        errors.append("report anchor-center distances do not match the board")

    label_found = any(
        isinstance(item, pcbnew.PCB_TEXT)
        and item.GetText() == "P4_CORE - B9 ROUTING-FEASIBILITY ISLAND"
        for item in board.GetDrawings()
    )
    if not label_found:
        errors.append("B9 P4 working-group label is absent")

    print("M1-PRELAYOUT-B9 P4 core-island validation")
    print(f"  P4 group footprints: {len(p4)}")
    print(f"  P4 group bbox: {actual_bbox['width']} x {actual_bbox['height']} mm")
    print(f"  U1/Y1 body gap: {crystal_gap:.3f} mm")
    print(f"  footprint bounding-box overlaps: {len(overlaps)}")
    print(f"  tracks/zones/Edge.Cuts: {track_count}/{zone_count}/{edge_cuts}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("PASS: P4 core island is compacted and remains a reversible, fail-closed routing seed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
