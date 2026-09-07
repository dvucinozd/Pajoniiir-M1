#!/usr/bin/env python3
"""Apply the reversible M1-PRELAYOUT-B9 ESP32-P4 core-island placement.

The pass moves only the 03_P4_CORE / 04_P4_FLASH_CLOCK_RESET footprints.
It creates no copper, zones, Edge.Cuts, mounting holes, or production datums.
Run with KiCad's bundled Python so the pcbnew module is available.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import pcbnew


MM = pcbnew.FromMM
P4_SHEETS = {"03_P4_CORE", "04_P4_FLASH_CLOCK_RESET"}


# Coordinates remain inside the B8 P4_CORE working rectangle.  They are a
# deterministic routing-feasibility seed, not production mechanical datums.
PLACEMENTS: dict[str, tuple[float, float, float]] = {
    # ESP32-P4, external core DCDC, flash and 40 MHz clock anchors.
    "U1": (55.0, 150.0, 0.0),
    "U2": (55.0, 166.5, 0.0),
    "U3": (66.0, 139.0, 0.0),
    "L1": (71.0, 144.0, 0.0),
    "Y1": (42.0, 136.0, 0.0),

    # v3.x external DCDC loop and HP rail reservoir.
    "C40": (66.0, 133.5, 0.0),
    "R27": (61.0, 138.0, 0.0),
    "R28": (61.0, 134.5, 0.0),
    "C42": (71.0, 137.5, 0.0),
    "C41": (76.0, 144.0, 0.0),
    "C43": (76.0, 148.0, 0.0),

    # Crystal: R36 stays at the chip side; load capacitors flank Y1.
    "R36": (48.0, 140.5, 90.0),
    "C61": (38.4, 136.0, 0.0),
    "C62": (45.6, 136.0, 0.0),

    # Quad-SPI tuning row between U1 and U2.
    "R32": (47.5, 159.5, 90.0),
    "R29": (50.3, 159.5, 90.0),
    "R33": (53.1, 159.5, 90.0),
    "R34": (55.9, 159.5, 90.0),
    "R30": (58.7, 159.5, 90.0),
    "R31": (61.5, 159.5, 90.0),
    "R35": (47.0, 173.0, 0.0),
    "C60": (61.0, 165.0, 0.0),
    "C30": (61.0, 168.5, 0.0),
    "C31": (61.0, 172.0, 0.0),

    # P4-local supply links and decoupling banks.  Final escape routing may
    # move these within the island; no coordinate is mechanically frozen.
    "C26": (43.0, 140.5, 0.0),
    "R25": (47.4, 144.5, 90.0),
    "C48": (43.0, 145.0, 0.0),
    "C49": (43.0, 148.5, 0.0),
    "C50": (43.0, 152.0, 0.0),
    "C51": (43.0, 155.5, 0.0),
    "C52": (43.0, 159.0, 0.0),
    "C53": (43.0, 162.5, 0.0),
    "C54": (43.0, 166.0, 0.0),
    "C55": (43.0, 169.5, 0.0),
    "C56": (43.0, 173.0, 0.0),
    "C57": (43.0, 176.5, 0.0),
    "C58": (43.0, 180.0, 0.0),
    "C59": (47.0, 180.0, 0.0),

    "C44": (64.5, 148.0, 0.0),
    "C45": (64.5, 151.5, 0.0),
    "C46": (64.5, 155.0, 0.0),
    "C47": (64.5, 158.5, 0.0),
    "R26": (68.0, 162.0, 90.0),
    "C27": (68.0, 166.0, 0.0),
    "C28": (68.0, 169.5, 0.0),
    "C29": (68.0, 173.0, 0.0),
    "C32": (72.0, 152.0, 0.0),
    "C33": (72.0, 155.5, 0.0),
    "C34": (72.0, 159.0, 0.0),
    "C35": (72.0, 162.5, 0.0),
    "C36": (72.0, 166.0, 0.0),
    "C37": (51.0, 180.0, 0.0),
    "C38": (55.0, 180.0, 0.0),
    "C39": (59.0, 180.0, 0.0),

    # Reset, strap, UART and tool-access parts remain in the same reversible
    # P4 working group but outside the high-density escape area.
    "R24": (63.0, 180.0, 0.0),
    "C63": (67.0, 180.0, 0.0),
    "R37": (71.0, 180.0, 0.0),
    "R38": (75.0, 180.0, 0.0),
    "R39": (79.0, 180.0, 0.0),
    "R40": (83.0, 180.0, 0.0),
    "R41": (87.0, 180.0, 0.0),
    "SW1": (80.0, 168.0, 0.0),
    "SW2": (87.0, 168.0, 0.0),
}


def mm_position(fp: pcbnew.FOOTPRINT) -> tuple[float, float]:
    position = fp.GetPosition()
    return pcbnew.ToMM(position.x), pcbnew.ToMM(position.y)


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
    dx = max(bl - ar, al - br, 0.0)
    dy = max(bt - ab, at - bb, 0.0)
    return math.hypot(dx, dy)


def center_distance_mm(a: pcbnew.FOOTPRINT, b: pcbnew.FOOTPRINT) -> float:
    ax, ay = mm_position(a)
    bx, by = mm_position(b)
    return math.hypot(ax - bx, ay - by)


def overlap_pairs(footprints: list[pcbnew.FOOTPRINT]) -> list[tuple[str, str]]:
    overlaps: list[tuple[str, str]] = []
    for index, first in enumerate(footprints):
        al, at, ar, ab = bbox_edges_mm(first)
        for second in footprints[index + 1 :]:
            bl, bt, br, bb = bbox_edges_mm(second)
            if min(ar, br) > max(al, bl) and min(ab, bb) > max(at, bt):
                overlaps.append((first.GetReference(), second.GetReference()))
    return overlaps


def p4_refs(board: pcbnew.BOARD) -> set[str]:
    return {
        fp.GetReference()
        for fp in board.GetFootprints()
        if fp.GetSheetname() in P4_SHEETS
    }


def edge_cut_count(board: pcbnew.BOARD) -> int:
    return sum(1 for drawing in board.GetDrawings() if drawing.GetLayer() == pcbnew.Edge_Cuts)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board.resolve()))
    if board is None:
        raise RuntimeError(f"Cannot load board: {args.board}")
    if len(list(board.GetFootprints())) != 244:
        raise RuntimeError("B9 requires the complete 244-footprint B8 canvas")
    if list(board.GetTracks()) or list(board.Zones()) or edge_cut_count(board):
        raise RuntimeError("B9 accepts only the unrouted, zoneless canvas without Edge.Cuts")

    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    actual_p4_refs = p4_refs(board)
    if actual_p4_refs != set(PLACEMENTS):
        missing = sorted(actual_p4_refs - set(PLACEMENTS))
        extra = sorted(set(PLACEMENTS) - actual_p4_refs)
        raise RuntimeError(f"P4 placement map drift: missing={missing} extra={extra}")

    for ref, (x, y, rotation) in PLACEMENTS.items():
        fp = footprints[ref]
        fp.SetOrientationDegrees(rotation)
        fp.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
        fp.SetIsPlaced(True)

    for drawing in board.GetDrawings():
        if isinstance(drawing, pcbnew.PCB_TEXT) and drawing.GetText() == "P4_CORE - B8 WORKING GROUP":
            drawing.SetText("P4_CORE - B9 ROUTING-FEASIBILITY ISLAND")

    xs: list[float] = []
    ys: list[float] = []
    for ref in sorted(actual_p4_refs):
        left, top, right, bottom = bbox_edges_mm(footprints[ref])
        xs.extend((left, right))
        ys.extend((top, bottom))

    overlaps = overlap_pairs([footprints[ref] for ref in sorted(actual_p4_refs)])
    if overlaps:
        raise RuntimeError(f"Refusing overlapping B9 placement: {overlaps}")
    crystal_gap = bbox_gap_mm(footprints["U1"], footprints["Y1"])
    if crystal_gap < 4.5:
        raise RuntimeError(f"Refusing U1/Y1 body gap below 4.5 mm: {crystal_gap:.3f} mm")

    metrics = {
        "p4_group_bbox_mm": {
            "left": round(min(xs), 3),
            "top": round(min(ys), 3),
            "right": round(max(xs), 3),
            "bottom": round(max(ys), 3),
            "width": round(max(xs) - min(xs), 3),
            "height": round(max(ys) - min(ys), 3),
        },
        "center_distances_mm": {
            "U1_U2": round(center_distance_mm(footprints["U1"], footprints["U2"]), 3),
            "U1_U3": round(center_distance_mm(footprints["U1"], footprints["U3"]), 3),
            "U3_L1": round(center_distance_mm(footprints["U3"], footprints["L1"]), 3),
        },
        "crystal_body_gap_to_U1_mm": round(crystal_gap, 3),
        "p4_footprint_bbox_overlap_count": len(overlaps),
    }

    payload = {
        "schema_version": 1,
        "milestone": "M1-PRELAYOUT-B9",
        "status": "P4_CORE_ISLAND_ROUTING_FEASIBILITY_SEED",
        "production_layout": False,
        "layout_freeze_allowed": False,
        "edge_cuts_present": False,
        "source_canvas": "m1_board_placement_seed_b8.json",
        "moved_sheet_groups": sorted(P4_SHEETS),
        "placement_count": len(PLACEMENTS),
        "placements_mm": {
            ref: {"x": x, "y": y, "rotation_deg": rotation}
            for ref, (x, y, rotation) in sorted(PLACEMENTS.items())
        },
        "metrics": metrics,
        "rules": [
            "Coordinates are a reversible board-local routing-feasibility seed.",
            "No coordinate is an enclosure, connector-panel, mounting-hole, or production outline datum.",
            "No copper, zones, Edge.Cuts, Gerbers, or layout freeze are authorized at B9.",
            "The next pass must prove P4 escape/routing and may move components within the island.",
        ],
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    if not pcbnew.SaveBoard(str(args.output.resolve()), board):
        raise RuntimeError(f"Failed to save board: {args.output}")
    args.report.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
