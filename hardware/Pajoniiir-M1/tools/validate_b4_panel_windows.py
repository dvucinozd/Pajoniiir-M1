#!/usr/bin/env python3
"""Fail-closed arithmetic validator for M1-MECH-B4 panel/FFC placement windows."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
WINDOWS = BASE / "m1_mech_b4_panel_windows.json"
B3 = BASE / "m1_mech_b3_mainboard_io_envelope.json"
ENC = BASE / "m1_mech_b3_enclosure_candidate.json"


def load(path: Path, errors: list[str]) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{path.name}: invalid/missing JSON: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{path.name}: root must be an object")
        return {}
    return value


def close(value, expected: float, tol: float = 1e-4) -> bool:
    return isinstance(value, (int, float)) and math.isclose(float(value), expected, abs_tol=tol)


def span(obj: dict) -> float:
    return float(obj.get("max", 0)) - float(obj.get("min", 0))


def main() -> int:
    errors: list[str] = []
    windows = load(WINDOWS, errors)
    b3 = load(B3, errors)
    enc = load(ENC, errors)

    if windows.get("milestone") != "M1-MECH-B4":
        errors.append("panel-window authority is not M1-MECH-B4")
    if "EXACT_CONNECTOR_CENTERS_STILL_OPEN" not in str(windows.get("status", "")):
        errors.append("B4 windows must not claim exact connector centers are closed")

    # Cross-check enclosure/core inputs rather than accepting duplicated numbers.
    ee = enc.get("external_envelope_candidate_mm", {})
    if not all((close(ee.get("width_x"), 128.0), close(ee.get("height_y"), 84.0))):
        errors.append("B4 window screen no longer matches 128 x 84 enclosure candidate")
    core = b3.get("core_mainboard_envelope_candidate", {})
    if not all((close(core.get("width_mm"), 104.0), close(core.get("height_mm"), 62.0))):
        errors.append("B4 window screen no longer matches 104 x 62 core board")

    assembly = windows.get("assembly_screen", {})
    gaps = assembly.get("core_to_inner_wall_gap_mm", {})
    expected_gaps = {
        "top": 2.3335,
        "left": 9.9455,
        "right": 10.0545,
        "bottom": 15.6665,
    }
    for name, expected in expected_gaps.items():
        if not close(gaps.get(name), expected):
            errors.append(f"B4 core-to-inner-wall {name} gap drift: {gaps.get(name)}")

    top = windows.get("primary_long_io_wall", {})
    if top.get("wall") != "Y_NEG_TOP":
        errors.append("primary B4 I/O window is not on Y_NEG_TOP")
    whole = top.get("reserved_cluster_local_x_mm", {})
    usb = top.get("USB_HOST_PAIR_window_local_x_mm", {})
    reserve = top.get("INTERCLUSTER_RESERVE_local_x_mm", {})
    rca = top.get("RCA_MAIN_PAIR_window_local_x_mm", {})
    expected_bounds = [
        (whole, 8.21, 95.79, "whole top cluster"),
        (usb, 8.21, 56.71, "USB pair"),
        (reserve, 56.71, 64.71, "intercluster reserve"),
        (rca, 64.71, 95.79, "RCA pair"),
    ]
    for obj, minimum, maximum, name in expected_bounds:
        if not close(obj.get("min"), minimum) or not close(obj.get("max"), maximum):
            errors.append(f"B4 {name} bounds drift: {obj}")
    if not close(span(whole), 87.58) or not close(span(usb), 48.50) or not close(span(reserve), 8.0) or not close(span(rca), 31.08):
        errors.append("B4 top-wall packing arithmetic drift")

    power = windows.get("power_wall", {})
    if power.get("wall") != "X_NEG_LEFT" or power.get("wing_required_or_connector_overhang_required") is not True:
        errors.append("B4 power-wall wing/overhang policy drift")
    pregion = power.get("preferred_vertical_region_board_local_y_mm", {})
    if not close(pregion.get("min"), 20.0) or not close(pregion.get("max"), 48.0) or not close(power.get("preferred_center_screen_board_local_y_mm"), 31.0):
        errors.append("B4 power-wall vertical screening region drift")

    media = windows.get("media_service_wall", {})
    if media.get("wall") != "X_POS_RIGHT" or media.get("wing_required_or_connector_overhang_required") is not True:
        errors.append("B4 media/service wall wing/overhang policy drift")
    ffc = media.get("dsi_ffc_screen", {})
    raw = ffc.get("raw_cable_band_board_local_y_mm", {})
    corridor = ffc.get("reserved_mechanical_corridor_board_local_y_mm", {})
    if not close(ffc.get("ffc_center_board_local_y_mm"), 32.07) or not close(ffc.get("ffc_width_mm"), 15.0):
        errors.append("B4 FFC center/width drift")
    if not close(raw.get("min"), 24.57) or not close(raw.get("max"), 39.57) or not close(span(raw), 15.0):
        errors.append("B4 raw FFC band arithmetic drift")
    if not close(ffc.get("screening_guard_each_side_mm"), 2.5):
        errors.append("B4 FFC guard value drift")
    if not close(corridor.get("min"), 22.07) or not close(corridor.get("max"), 42.07) or not close(span(corridor), 20.0):
        errors.append("B4 guarded FFC corridor arithmetic drift")

    recovery = media.get("upper_recovery_zone", {})
    rzone = recovery.get("board_local_y_mm", {})
    if recovery.get("functions") != ["SW1_RESET", "SW2_BOOT"]:
        errors.append("B4 recovery-zone function assignment drift")
    if not close(rzone.get("min"), 7.5) or not close(rzone.get("max"), 21.0):
        errors.append("B4 recovery-zone bounds drift")
    if float(rzone.get("max", 999)) >= float(corridor.get("min", -999)):
        errors.append("B4 recovery zone overlaps guarded FFC corridor")

    media_zone = media.get("lower_media_zone", {})
    mzone = media_zone.get("board_local_y_mm", {})
    if media_zone.get("functions") != ["J7_MICROSD"]:
        errors.append("B4 lower media-zone function assignment drift")
    if not close(mzone.get("min"), 43.0) or not close(mzone.get("max"), 61.0):
        errors.append("B4 lower media-zone bounds drift")
    if float(mzone.get("min", -999)) <= float(corridor.get("max", 999)):
        errors.append("B4 microSD zone overlaps guarded FFC corridor")

    clear = windows.get("clear_long_wall", {})
    if clear.get("wall") != "Y_POS_BOTTOM" or clear.get("reserved_for_connectors") is not False:
        errors.append("B4 clear bottom-wall policy drift")

    # The screen must remain a screen: no final centers/cutouts/Edge.Cuts may be claimed here.
    still_open = set(windows.get("still_open", []))
    required_open_fragments = {
        "exact host DSI connector center/orientation and 60 mm FFC U-bend path",
        "display-side pin-1 continuity proof",
        "exact panel cutout centers and dimensions",
        "final side-wing/notch Edge.Cuts",
    }
    missing = required_open_fragments - still_open
    if missing:
        errors.append(f"B4 window file prematurely closed required items: {sorted(missing)}")

    print("Pajoniiir-M1 M1-MECH-B4 panel-window validation")
    print("  core board: 104 x 62 mm")
    print("  top cluster: 87.58 mm reserved")
    print("  FFC guarded corridor: Y 22.07 .. 42.07 mm")
    print("  recovery zone: Y 7.5 .. 21.0 mm")
    print("  microSD zone: Y 43.0 .. 61.0 mm")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("PASS: B4 panel/FFC placement windows are internally consistent and remain non-final.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
