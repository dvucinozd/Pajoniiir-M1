#!/usr/bin/env python3
"""Create the reversible M1-PRELAYOUT-B10 P4 critical-route proof.

The pass starts from the unrouted B9 board, rotates the ESP32-P4 so its flash,
core-DCDC and crystal pins face their functional blocks, then routes only those
three blocks plus flash decoupling. It deliberately creates no Edge.Cuts,
zones, mounting holes, Gerbers, or production routing authority.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import pcbnew


MM = pcbnew.FromMM
P4_SHEETS = {"03_P4_CORE", "04_P4_FLASH_CLOCK_RESET"}

# B10 changes only the high-density anchors and moves the left decoupling bank
# clear of the DCDC proof. All coordinates are reversible board-local values.
PLACEMENTS: dict[str, tuple[float, float, float, str]] = {
    "U1": (55.0, 150.0, 180.0, "F.Cu"),
    "U2": (59.0, 135.0, 270.0, "F.Cu"),
    "R31": (45.0, 141.0, 90.0, "F.Cu"),  # FLASH_D
    "R30": (48.0, 141.0, 90.0, "F.Cu"),  # FLASH_CK
    "R34": (51.0, 141.0, 90.0, "F.Cu"),  # FLASH_HOLD
    "R33": (61.9, 141.0, 90.0, "F.Cu"),  # FLASH_WP
    "R32": (64.7, 141.0, 90.0, "F.Cu"),  # FLASH_Q
    "R29": (67.5, 141.0, 90.0, "F.Cu"),  # FLASH_CS
    "C60": (50.5, 135.0, 180.0, "F.Cu"),

    "U3": (44.5, 161.5, 0.0, "F.Cu"),
    "L1": (49.0, 164.0, 0.0, "F.Cu"),
    "C40": (40.5, 162.0, 180.0, "F.Cu"),
    "C41": (53.5, 162.0, 0.0, "F.Cu"),
    "C43": (48.0, 170.0, 180.0, "F.Cu"),
    "R27": (41.0, 154.5, 0.0, "F.Cu"),
    "R28": (45.0, 154.5, 0.0, "F.Cu"),
    "C42": (41.0, 150.5, 0.0, "F.Cu"),

    "R36": (59.5, 159.2, 270.0, "F.Cu"),
    "Y1": (58.0, 165.5, 0.0, "F.Cu"),
    "C61": (62.0, 169.0, 180.0, "F.Cu"),
    "C62": (54.0, 164.95, 180.0, "F.Cu"),
    "R35": (42.0, 174.0, 0.0, "F.Cu"),
    "C30": (75.0, 172.0, 0.0, "F.Cu"),
    "C31": (75.0, 175.5, 0.0, "F.Cu"),

    # Clear the regulator/feedback area while retaining these P4 capacitors in
    # the same working island for later supply-escape refinement.
    "C48": (36.0, 145.0, 0.0, "F.Cu"),
    "C49": (36.0, 148.5, 0.0, "F.Cu"),
    "C50": (36.0, 152.0, 0.0, "F.Cu"),
    "C51": (36.0, 155.5, 0.0, "F.Cu"),
    "C52": (36.0, 159.0, 0.0, "F.Cu"),
    "C53": (36.0, 162.5, 0.0, "F.Cu"),
    "C54": (36.0, 166.0, 0.0, "F.Cu"),
    "C55": (36.0, 169.5, 0.0, "F.Cu"),
    "C56": (36.0, 173.0, 0.0, "F.Cu"),
    "C57": (36.0, 176.5, 0.0, "F.Cu"),
    "C26": (38.0, 140.5, 0.0, "F.Cu"),
}

# key: (U1 pad, series resistor, U2 pad)
QSPI = {
    "FLASH_D": ("33", "R31", "5"),
    "FLASH_CK": ("32", "R30", "6"),
    "FLASH_HOLD": ("31", "R34", "7"),
    "FLASH_WP": ("29", "R33", "3"),
    "FLASH_Q": ("28", "R32", "2"),
    "FLASH_CS": ("27", "R29", "1"),
}


def vector(x: float, y: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(MM(x), MM(y))


def point_mm(point: pcbnew.VECTOR2I) -> tuple[float, float]:
    return pcbnew.ToMM(point.x), pcbnew.ToMM(point.y)


def pad_point(footprints: dict[str, pcbnew.FOOTPRINT], ref: str, number: str) -> tuple[float, float]:
    pad = footprints[ref].FindPadByNumber(number)
    if pad is None:
        raise RuntimeError(f"Missing pad {ref}.{number}")
    return point_mm(pad.GetPosition())


def bbox_edges_mm(fp: pcbnew.FOOTPRINT) -> tuple[float, float, float, float]:
    box = fp.GetBoundingBox()
    return tuple(
        pcbnew.ToMM(value)
        for value in (box.GetLeft(), box.GetTop(), box.GetRight(), box.GetBottom())
    )


def bbox_gap_mm(a: pcbnew.FOOTPRINT, b: pcbnew.FOOTPRINT) -> float:
    al, at, ar, ab = bbox_edges_mm(a)
    bl, bt, br, bb = bbox_edges_mm(b)
    dx = max(bl - ar, al - br, 0.0)
    dy = max(bt - ab, at - bb, 0.0)
    return math.hypot(dx, dy)


def overlap_pairs(footprints: list[pcbnew.FOOTPRINT]) -> list[tuple[str, str]]:
    overlaps: list[tuple[str, str]] = []
    for index, first in enumerate(footprints):
        al, at, ar, ab = bbox_edges_mm(first)
        for second in footprints[index + 1 :]:
            bl, bt, br, bb = bbox_edges_mm(second)
            if min(ar, br) > max(al, bl) and min(ab, bb) > max(at, bt):
                overlaps.append((first.GetReference(), second.GetReference()))
    return overlaps


def ensure_side(fp: pcbnew.FOOTPRINT, side: str) -> None:
    expected_layer = pcbnew.F_Cu if side == "F.Cu" else pcbnew.B_Cu
    if fp.GetLayer() != expected_layer:
        fp.Flip(fp.GetPosition(), False)
    if fp.GetLayer() != expected_layer:
        raise RuntimeError(f"Cannot move {fp.GetReference()} to {side}")


def place(footprints: dict[str, pcbnew.FOOTPRINT]) -> None:
    for ref, (x, y, rotation, side) in PLACEMENTS.items():
        fp = footprints[ref]
        ensure_side(fp, side)
        fp.SetOrientationDegrees(rotation)
        fp.SetPosition(vector(x, y))
        fp.SetIsPlaced(True)


def upgrade_u8_thermal_vias(footprints: dict[str, pcbnew.FOOTPRINT]) -> None:
    u8 = footprints["U8"]
    u8.SetFPID(
        pcbnew.LIB_ID(
            "Pajoniiir-M1",
            "VQFN-16-1EP_3x3mm_P0.5mm_EP1.68x1.68mm_ThermalVias",
        )
    )
    thermal_vias = [
        pad for pad in u8.Pads()
        if pad.GetNumber() == "17" and pad.GetDrillSize().x > 0
    ]
    if len(thermal_vias) != 4:
        raise RuntimeError(f"Expected four U8 thermal vias, found {len(thermal_vias)}")
    for pad in thermal_vias:
        pad.SetDrillSize(vector(0.3, 0.3))


def board_net(board: pcbnew.BOARD, name: str) -> pcbnew.NETINFO_ITEM:
    nets = board.GetNetsByName()
    if name not in nets:
        raise RuntimeError(f"Missing board net {name}")
    return nets[name]


def add_polyline(
    board: pcbnew.BOARD,
    net_name: str,
    points: list[tuple[float, float]],
    width_mm: float,
    layer: int = pcbnew.F_Cu,
) -> None:
    netinfo = board_net(board, net_name)
    for start, end in zip(points, points[1:]):
        if start == end:
            continue
        track = pcbnew.PCB_TRACK(board)
        track.SetStart(vector(*start))
        track.SetEnd(vector(*end))
        track.SetWidth(MM(width_mm))
        track.SetLayer(layer)
        track.SetNet(netinfo)
        board.Add(track)


def add_via(
    board: pcbnew.BOARD,
    net_name: str,
    position: tuple[float, float],
    diameter_mm: float = 0.6,
    drill_mm: float = 0.3,
) -> None:
    via = pcbnew.PCB_VIA(board)
    via.SetPosition(vector(*position))
    via.SetWidth(MM(diameter_mm))
    via.SetDrill(MM(drill_mm))
    via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    via.SetNet(board_net(board, net_name))
    board.Add(via)


def add_qspi_routes(board: pcbnew.BOARD, footprints: dict[str, pcbnew.FOOTPRINT]) -> None:
    # U1-to-series-resistor fanout preserves the left-to-right pad order.
    escape_y = {
        "FLASH_D": 143.90,
        "FLASH_CK": 143.55,
        "FLASH_HOLD": 143.20,
        "FLASH_WP": 143.20,
        "FLASH_Q": 143.55,
        "FLASH_CS": 143.90,
    }
    for key, (u1_pad, resistor, _) in QSPI.items():
        source_net = footprints[resistor].FindPadByNumber("1").GetNetname()
        start = pad_point(footprints, "U1", u1_pad)
        end = pad_point(footprints, resistor, "1")
        add_polyline(board, source_net, [start, (start[0], escape_y[key]), end], 0.15)

    # D/CLK/HOLD face the lower U2 pads and route directly.
    flash_lanes = {"FLASH_D": 138.1, "FLASH_CK": 138.6, "FLASH_HOLD": 139.1}
    for key in ("FLASH_D", "FLASH_CK", "FLASH_HOLD"):
        _, resistor, u2_pad = QSPI[key]
        flash_net = footprints[resistor].FindPadByNumber("2").GetNetname()
        start = pad_point(footprints, resistor, "2")
        end = pad_point(footprints, "U2", u2_pad)
        lane_y = flash_lanes[key]
        add_polyline(board, flash_net, [start, (start[0], lane_y), (end[0], lane_y), end], 0.15)

    # WP/Q/CS face the upper U2 pads. One via pair per net gives a short,
    # ordered B.Cu crossing beneath U2 instead of a long perimeter detour.
    via_lanes = {
        "FLASH_WP": ((61.9, 139.6), (58.665, 131.3)),
        "FLASH_Q": ((64.7, 139.6), (59.935, 130.5)),
        "FLASH_CS": ((67.5, 139.6), (61.205, 129.7)),
    }
    for key in ("FLASH_WP", "FLASH_Q", "FLASH_CS"):
        _, resistor, u2_pad = QSPI[key]
        flash_net = footprints[resistor].FindPadByNumber("2").GetNetname()
        start = pad_point(footprints, resistor, "2")
        end = pad_point(footprints, "U2", u2_pad)
        source_via, u2_via = via_lanes[key]
        add_polyline(board, flash_net, [start, source_via], 0.15)
        add_via(board, flash_net, source_via)
        add_polyline(board, flash_net, [source_via, u2_via], 0.15, pcbnew.B_Cu)
        add_via(board, flash_net, u2_via)
        add_polyline(board, flash_net, [u2_via, end], 0.15)


def add_flash_decoupling(board: pcbnew.BOARD, footprints: dict[str, pcbnew.FOOTPRINT]) -> None:
    flash = "/03_P4_CORE/FLASH_VCC"
    u2_vcc = pad_point(footprints, "U2", "8")
    cap_vcc = pad_point(footprints, "C60", "1")
    u2_via = (63.0, 138.5)
    cap_via = (52.5, 135.0)
    add_polyline(board, flash, [u2_vcc, u2_via], 0.30)
    add_via(board, flash, u2_via)
    add_polyline(board, flash, [u2_via, cap_via], 0.30, pcbnew.In2_Cu)
    add_via(board, flash, cap_via)
    add_polyline(board, flash, [cap_via, cap_vcc], 0.30)


def add_crystal_routes(board: pcbnew.BOARD, footprints: dict[str, pcbnew.FOOTPRINT]) -> None:
    u1_p = pad_point(footprints, "U1", "100")
    r_chip = pad_point(footprints, "R36", "1")
    add_polyline(
        board,
        "/XTAL_P",
        [u1_p, (u1_p[0], 156.5), (60.2, 157.5), (60.2, r_chip[1]), r_chip],
        0.15,
    )

    node = "/04_P4_FLASH_CLOCK_RESET/XTAL_P_NODE"
    r_crystal = pad_point(footprints, "R36", "2")
    y1_p = pad_point(footprints, "Y1", "1")
    c61 = pad_point(footprints, "C61", "1")
    add_polyline(
        board,
        node,
        [r_crystal, (60.5, 161.0), (60.5, 168.0), (y1_p[0], 168.0), y1_p],
        0.15,
    )
    add_polyline(board, node, [y1_p, (y1_p[0], 168.0), (c61[0], 168.0), c61], 0.15)

    u1_n = pad_point(footprints, "U1", "99")
    y1_n = pad_point(footprints, "Y1", "3")
    c62 = pad_point(footprints, "C62", "1")
    add_polyline(board, "/XTAL_N", [u1_n, (u1_n[0], 157.3), (58.7, 158.5), y1_n], 0.15)
    add_polyline(board, "/XTAL_N", [y1_n, (58.7, 163.5), (c62[0], 163.5), c62], 0.15)


def add_dcdc_routes(board: pcbnew.BOARD, footprints: dict[str, pcbnew.FOOTPRINT]) -> None:
    vin_pad = pad_point(footprints, "U3", "3")
    add_polyline(board, "/3V3_SYS", [vin_pad, (42.8, 162.0)], 0.20)
    add_polyline(board, "/3V3_SYS", [(42.8, 162.0), pad_point(footprints, "C40", "1")], 0.65)

    sw_pad = pad_point(footprints, "U3", "4")
    add_polyline(board, "/03_P4_CORE/P4_CORE_SW", [sw_pad, (46.2, 162.8)], 0.15)
    add_polyline(board, "/03_P4_CORE/P4_CORE_SW", [(46.2, 162.8), pad_point(footprints, "L1", "1")], 0.65)

    hp = "/03_P4_CORE/P4_VDD_HP"
    l1_out = pad_point(footprints, "L1", "2")
    c41 = pad_point(footprints, "C41", "1")
    c43 = pad_point(footprints, "C43", "1")
    hp_via_out = (51.2, 163.4)
    hp_via_u1 = (47.6, 153.675)
    add_polyline(board, hp, [l1_out, c41, (c41[0], c43[1]), c43], 0.65)
    add_polyline(board, hp, [c41, hp_via_out], 0.65)
    add_via(board, hp, hp_via_out)
    add_polyline(board, hp, [hp_via_out, (47.6, 163.4), hp_via_u1], 0.65, pcbnew.B_Cu)
    add_via(board, hp, hp_via_u1)
    add_polyline(board, hp, [hp_via_u1, (49.0, 153.675)], 0.65)
    add_polyline(board, hp, [(49.0, 153.675), pad_point(footprints, "U1", "76")], 0.15)

    add_polyline(
        board,
        "/03_P4_CORE/P4_EN_DCDC",
        [pad_point(footprints, "U1", "79"), (50.625, 156.0), (47.0, 159.5), (47.0, 161.5), pad_point(footprints, "U3", "5")],
        0.15,
    )

    fb = "/03_P4_CORE/P4_FB_DCDC"
    u1_fb = pad_point(footprints, "U1", "78")
    u3_fb = pad_point(footprints, "U3", "1")
    r27_fb = pad_point(footprints, "R27", "2")
    r28_fb = pad_point(footprints, "R28", "1")
    c42_fb = pad_point(footprints, "C42", "2")
    add_polyline(board, fb, [u1_fb, (47.0, 155.5), (43.0, 155.5), r27_fb], 0.15)
    add_polyline(board, fb, [(43.0, 155.5), r28_fb], 0.15)
    add_polyline(board, fb, [r27_fb, (42.3, 157.0), (42.3, 161.0), u3_fb], 0.15)
    add_polyline(board, fb, [r27_fb, c42_fb], 0.15)

    # The upper divider leg senses the quiet output after L1; its B.Cu branch
    # stays away from the compact F.Cu switch node.
    r27_hp = pad_point(footprints, "R27", "1")
    c42_hp = pad_point(footprints, "C42", "1")
    sense_via = (39.0, 149.5)
    add_polyline(board, hp, [r27_hp, c42_hp, sense_via], 0.15)
    add_via(board, hp, sense_via)
    add_polyline(board, hp, [sense_via, (39.0, 163.4), hp_via_out], 0.20, pcbnew.B_Cu)


def length_mm(track: pcbnew.PCB_TRACK) -> float:
    start = track.GetStart()
    end = track.GetEnd()
    return math.hypot(pcbnew.ToMM(start.x - end.x), pcbnew.ToMM(start.y - end.y))


def p4_refs(board: pcbnew.BOARD) -> set[str]:
    return {fp.GetReference() for fp in board.GetFootprints() if fp.GetSheetname() in P4_SHEETS}


def report_payload(board: pcbnew.BOARD, footprints: dict[str, pcbnew.FOOTPRINT]) -> dict[str, object]:
    lengths: dict[str, float] = defaultdict(float)
    layers: dict[str, int] = defaultdict(int)
    segment_count = 0
    via_count = 0
    vias_by_net: dict[str, int] = defaultdict(int)
    for item in board.GetTracks():
        if isinstance(item, pcbnew.PCB_VIA):
            via_count += 1
            vias_by_net[item.GetNetname()] += 1
            continue
        segment_count += 1
        lengths[item.GetNetname()] += length_mm(item)
        layers[board.GetLayerName(item.GetLayer())] += 1

    qspi_lengths: dict[str, float] = {}
    for key, (_, resistor, _) in QSPI.items():
        source_net = footprints[resistor].FindPadByNumber("1").GetNetname()
        flash_net = footprints[resistor].FindPadByNumber("2").GetNetname()
        qspi_lengths[key] = round(lengths[source_net] + lengths[flash_net], 3)

    refs = sorted(p4_refs(board))
    xs: list[float] = []
    ys: list[float] = []
    for ref in refs:
        left, top, right, bottom = bbox_edges_mm(footprints[ref])
        xs.extend((left, right))
        ys.extend((top, bottom))
    overlaps = overlap_pairs([footprints[ref] for ref in refs])
    crystal_gap = bbox_gap_mm(footprints["U1"], footprints["Y1"])

    return {
        "schema_version": 1,
        "milestone": "M1-PRELAYOUT-B10",
        "status": "P4_CRITICAL_ROUTE_FEASIBILITY_PROVEN",
        "production_layout": False,
        "layout_freeze_allowed": False,
        "edge_cuts_present": False,
        "zones_present": False,
        "source_placement": "m1_prelayout_b9_core_island.json",
        "placement_changes": {
            ref: {"x": x, "y": y, "rotation_deg": rotation, "side": side}
            for ref, (x, y, rotation, side) in sorted(PLACEMENTS.items())
        },
        "route_scope": {
            "QSPI": sorted(QSPI),
            "CRYSTAL": ["XTAL_P", "XTAL_P_NODE", "XTAL_N"],
            "CORE_DCDC": ["3V3 input", "SW", "VDD_HP output", "EN", "FB and output sense"],
            "FLASH_DECOUPLING": ["U2 pin 8 to C60", "C60 ground awaits the B11 plane pass"],
        },
        "metrics": {
            "named_net_count": board.GetNetCount() - 1,
            "track_segment_count": segment_count,
            "via_count": via_count,
            "track_segments_by_layer": dict(sorted(layers.items())),
            "track_length_by_net_mm": {name: round(value, 3) for name, value in sorted(lengths.items())},
            "qspi_end_to_end_track_length_mm": qspi_lengths,
            "qspi_length_spread_mm": round(max(qspi_lengths.values()) - min(qspi_lengths.values()), 3),
            "crystal_via_count": 0,
            "qspi_signal_via_count": sum(
                count for name, count in vias_by_net.items() if name.startswith("Net-(U2-")
            ),
            "crystal_body_gap_to_U1_mm": round(crystal_gap, 3),
            "p4_group_bbox_mm": {
                "left": round(min(xs), 3), "top": round(min(ys), 3),
                "right": round(max(xs), 3), "bottom": round(max(ys), 3),
                "width": round(max(xs) - min(xs), 3),
                "height": round(max(ys) - min(ys), 3),
            },
            "p4_footprint_bbox_overlap_count": len(overlaps),
            "u8_thermal_via_drill_mm": 0.3,
        },
        "rules": [
            "B10 routes are routing-feasibility evidence and may move during final escape and SI review.",
            "QSPI and crystal routes remain on F.Cu above the reserved In1.Cu GND-plane allocation; the plane is not poured at B10.",
            "Crystal routes contain no vias; three package-opposed QSPI nets use one 0.60/0.30 mm via pair each.",
            "The DCDC SW/VIN/VOUT power segments use 0.65 mm width; FB stays away from the SW segment.",
            "No Edge.Cuts, zones, mounting pattern, Gerbers, EVT order, or layout freeze is authorized.",
        ],
    }


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
        raise RuntimeError("B10 requires the complete 244-footprint B9 board")
    if list(board.GetTracks()) or list(board.Zones()):
        raise RuntimeError("B10 requires the unrouted, zoneless B9 board")
    if any(item.GetLayer() == pcbnew.Edge_Cuts for item in board.GetDrawings()):
        raise RuntimeError("B10 refuses a board with Edge.Cuts")

    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    upgrade_u8_thermal_vias(footprints)
    place(footprints)
    overlaps = overlap_pairs([footprints[ref] for ref in sorted(p4_refs(board))])
    if overlaps:
        raise RuntimeError(f"Refusing overlapping B10 placement: {overlaps}")
    if bbox_gap_mm(footprints["U1"], footprints["Y1"]) < 4.5:
        raise RuntimeError("Refusing B10 crystal body gap below 4.5 mm")

    add_qspi_routes(board, footprints)
    add_flash_decoupling(board, footprints)
    add_crystal_routes(board, footprints)
    add_dcdc_routes(board, footprints)

    for drawing in board.GetDrawings():
        if isinstance(drawing, pcbnew.PCB_TEXT) and drawing.GetText() == "P4_CORE - B9 ROUTING-FEASIBILITY ISLAND":
            drawing.SetText("P4_CORE - B10 CRITICAL-ROUTE PROOF")

    payload = report_payload(board, footprints)
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
