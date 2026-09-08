#!/usr/bin/env python3
"""Fail-closed validator for the board-first Pajoniiir-M1 authority."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
BOARD = BASE / "board_first_mechanical_contract.json"
MECH = BASE / "mech_a.json"
GATES = BASE / "mechanical_gates.json"
PCB_CONSTRAINTS = BASE / "pcb_constraints.json"
PROFILE = BASE / "display_compatibility_dsi506.json"
LEGACY_FINAL_DISPLAY = BASE / "final_display_module.json"
CONNECTOR = BASE / "display_connector_b1.json"
B4 = BASE / "m1_mech_b4_connector_source_lock.json"
PCB = BASE / "Pajoniiir-M1.kicad_pcb"
DISPLAY_SCH = BASE / "10_DISPLAY_MIPI.kicad_sch"

EXPECTED_BLOCKERS = {
    "C3_INPUT_BULK", "C8_PROTECTED_BULK", "J1_POWER_INPUT",
    "SW1_RESET", "SW2_BOOT", "J2_USB0", "J3_USB1", "J4_RCA_L",
    "J5_RCA_R", "J_LCD_DISPLAY_FPC", "J7_MICROSD", "PCB_OUTLINE",
}
SUPERSEDED_SCREENS = (
    "dsi506_inner_posts_lock_b2.json",
    "dsi506_mainboard_mount_candidate_b2.json",
    "dsi506_mainboard_mount_lock_b2.json",
    "m1_mech_b3_mainboard_io_envelope.json",
    "m1_mech_b3_enclosure_candidate.json",
    "m1_mech_b4_panel_windows.json",
    "m1_mech_b5_placement_skeleton.json",
)


def load(path: Path, errors: list[str]) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{path.name}: invalid/missing JSON: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{path.name}: root is not an object")
        return {}
    return value


def main() -> int:
    errors: list[str] = []
    board = load(BOARD, errors)
    mech = load(MECH, errors)
    gates = load(GATES, errors)
    pcb = load(PCB_CONSTRAINTS, errors)
    profile = load(PROFILE, errors)
    legacy_final_display = load(LEGACY_FINAL_DISPLAY, errors)
    connector = load(CONNECTOR, errors)
    b4 = load(B4, errors)

    if board.get("milestone") != "M1-MECH-B7":
        errors.append("board-first authority is not M1-MECH-B7")
    arch = board.get("architecture", {})
    for key in ("mainboard_is_standalone_assembly", "mainboard_mounts_to_own_chassis_or_enclosure"):
        if arch.get(key) is not True:
            errors.append(f"board-first architecture flag must be true: {key}")
    for key in (
        "display_model_defines_board_outline", "display_model_defines_mainboard_mount_pattern",
        "display_model_defines_external_connector_walls", "display_mounting_hardware_is_mainboard_authority",
    ):
        if arch.get(key) is not False:
            errors.append(f"board-first architecture flag must be false: {key}")

    iface = board.get("display_interface", {})
    expected_j6 = (
        "J6", "SFW15R-2STE1LF", "Pajoniiir-M1:Amphenol_SFW15R-2STE1LF",
        15, 1.0, "top",
    )
    observed_j6 = (
        iface.get("refdes"), iface.get("connector_mpn"), iface.get("connector_footprint"),
        iface.get("contacts"), iface.get("pitch_mm"), iface.get("contact_location"),
    )
    if observed_j6 != expected_j6:
        errors.append(f"generic J6 interface drift: {observed_j6} != {expected_j6}")
    if len(iface.get("electrical_pin_map", [])) != 15:
        errors.append("generic J6 interface must retain all 15 pin assignments")
    if "Type-B" not in iface.get("cable_policy", "") or "not a universal" not in iface.get("cable_policy", ""):
        errors.append("J6 cable policy must keep Type-B display-specific")

    release = board.get("board_release_boundary", {})
    for key in ("board_outline_locked", "edge_cuts_allowed", "layout_freeze_allowed"):
        if release.get(key) is not False:
            errors.append(f"board release flag must remain false: {key}")
    forbidden = " ".join(release.get("forbidden_as_outline_authority", []))
    for token in ("58 x 49", "104 x 62", "128 x 84", "right-edge FFC", "JC4880"):
        if token not in forbidden:
            errors.append(f"board authority does not explicitly demote screen: {token}")

    if mech.get("milestone") != "M1-MECH-B7":
        errors.append("mech_a.json is not rebased to M1-MECH-B7")
    ma = mech.get("board_first_architecture", {})
    if ma.get("mainboard_is_primary_product") is not True or ma.get("display_model_defines_board_geometry") is not False:
        errors.append("mech_a board-first boundary drift")
    compat = mech.get("validated_display_compatibility_profile", {})
    if compat.get("family") != "EYOYO DSI506 / DYL0023" or compat.get("production_board_geometry_authority") is not False:
        errors.append("mech_a DSI506 evidence is not constrained to a compatibility profile")
    if "authoritative_display_reference" in mech:
        errors.append("mech_a still exposes a display as main mechanical authority")

    if profile.get("profile_id") != "DSI506_DYL0023":
        errors.append("DSI506 compatibility profile identity drift")
    if legacy_final_display.get("status") != "SUPERSEDED_NAME__DO_NOT_USE_AS_ACTIVE_AUTHORITY":
        errors.append("final_display_module.json must remain a superseded-name tombstone")
    if legacy_final_display.get("superseded_by") != PROFILE.name:
        errors.append("final_display_module.json does not point to the DSI506 compatibility profile")
    pa = profile.get("mainboard_authority", {})
    for key in ("defines_board_outline", "defines_mainboard_mount_pattern", "defines_connector_wall_assignment", "defines_enclosure"):
        if pa.get(key) is not False:
            errors.append(f"DSI506 profile incorrectly owns mainboard geometry: {key}")
    if "DSI506" not in profile.get("validated_display_profile", {}).get("identity", ""):
        errors.append("DSI506 validated profile data missing")

    conn = connector.get("connector", {})
    fp = connector.get("footprint", {})
    if (conn.get("mpn"), conn.get("contacts"), conn.get("pitch_mm"), conn.get("contact_location")) != (
        "SFW15R-2STE1LF", 15, 1.0, "top"
    ):
        errors.append("display_connector_b1 J6 identity/contact geometry drift")
    if fp.get("library_id") != "Pajoniiir-M1:Amphenol_SFW15R-2STE1LF":
        errors.append("display_connector_b1 footprint authority drift")
    if connector.get("board_scope", {}).get("display_model_defines_board_geometry") is not False:
        errors.append("display_connector_b1 does not preserve board-first scope")

    for name in SUPERSEDED_SCREENS:
        screen = load(BASE / name, errors)
        if screen.get("production_authority") is not False or screen.get("superseded_by") != BOARD.name:
            errors.append(f"{name} is still eligible as production authority")

    gate_list = gates.get("gates", [])
    blockers = {
        gate.get("id") for gate in gate_list
        if isinstance(gate, dict) and gate.get("blocks_layout_freeze") and gate.get("status") != "closed"
    }
    if blockers != EXPECTED_BLOCKERS:
        errors.append(f"unexpected open blocker set: {sorted(blockers)}")
    if gates.get("milestone") != "M1-MECH-B7" or gates.get("layout_freeze_allowed") is not False:
        errors.append("mechanical gates are not fail-closed at M1-MECH-B7")
    ga = gates.get("mechanical_authority", {})
    if ga.get("primary") != BOARD.name or ga.get("display_profiles_define_board_geometry") is not False:
        errors.append("mechanical_gates primary authority is not board-first")

    by_id = {g.get("id"): g for g in gate_list if isinstance(g, dict)}
    j6 = by_id.get("J_LCD_DISPLAY_FPC", {})
    if j6.get("status") != "open" or j6.get("blocks_layout_freeze") is not True:
        errors.append("J6 service/placement/power gate must remain open")
    if (j6.get("exact_mpn"), j6.get("contact_count"), j6.get("pitch_mm"), j6.get("contact_location")) != (
        "SFW15R-2STE1LF", 15, 1.0, "top"
    ):
        errors.append("J6 gate does not match generic interface authority")
    j6_active = json.dumps({"known": j6.get("known"), "required": j6.get("required_evidence")}, ensure_ascii=False)
    for forbidden_token in ("final product display", "128 mm", "1.4455", "relative to final DSI506"):
        if forbidden_token in j6_active:
            errors.append(f"J6 active gate contains display-specific board geometry: {forbidden_token}")

    outline = by_id.get("PCB_OUTLINE", {})
    if outline.get("status") != "open" or outline.get("blocks_layout_freeze") is not True:
        errors.append("PCB_OUTLINE must remain open")
    if outline.get("legacy_enclosure_decision") != "NOT_MAINBOARD_AUTHORITY__DISPLAY_SPECIFIC_HISTORY_ONLY":
        errors.append("PCB_OUTLINE does not demote display-specific enclosure history")

    if pcb.get("board_outline_locked") is not False or pcb.get("controlled_impedance_locked") is not False:
        errors.append("PCB outline/impedance must remain unlocked")
    if pcb.get("stackup_locked") is not True:
        errors.append("JLC fabrication stackup must remain locked")
    mr = pcb.get("mechanical_reference", {})
    if mr.get("authority") != BOARD.name or mr.get("product_priority") != "standalone mainboard":
        errors.append("pcb_constraints mechanical reference is not board-first")
    if mr.get("display_model_defines_board_outline") is not False or mr.get("display_model_defines_mainboard_mount_pattern") is not False:
        errors.append("pcb_constraints lets display geometry govern the mainboard")
    if pcb.get("component_height_zones", {}).get("production_limit_locked") is not False:
        errors.append("component height zones were locked without board/chassis evidence")
    if pcb.get("packing_inventory") != "m1_board_packing_inventory_b7.json":
        errors.append("pcb_constraints does not reference the B7 board packing inventory")
    if pcb.get("layout_state") != "M1_PRELAYOUT_B10__P4_CRITICAL_ROUTES":
        errors.append("pcb_constraints is not synchronized to the B10 critical-route state")
    if pcb.get("ecad_toolchain") != "KiCad 10.x only":
        errors.append("pcb_constraints must keep KiCad 10.x as the sole ECAD toolchain")
    prelayout = pcb.get("current_prelayout", {})
    expected_prelayout = {
        "milestone": "M1-PRELAYOUT-B10",
        "board": "Pajoniiir-M1.kicad_pcb",
        "source_canvas": "m1_board_placement_seed_b8.json",
        "placement_authority": "m1_prelayout_b9_core_island.json",
        "routing_authority": "m1_prelayout_b10_core_routes.json",
        "default_clearance_mm": 0.15,
        "u8_thermal_via_drill_mm": 0.3,
        "route_geometry_drc_violations": 0,
        "remaining_unconnected_items": 499,
        "production_layout": False,
        "layout_freeze_allowed": False,
        "edge_cuts_allowed": False,
    }
    if prelayout != expected_prelayout:
        errors.append("pcb_constraints current_prelayout authority drift")
    active_routing = json.dumps(pcb.get("routing_targets", {}), ensure_ascii=False)
    if "DSI506 enclosure datum" in active_routing:
        errors.append("active routing constraints still depend on the DSI506 enclosure")

    selections = {tuple(s.get("refdes", [])): s for s in b4.get("selections", []) if isinstance(s, dict)}
    expected_mpns = {
        ("J1",): "722RAHLP", ("J2", "J3"): "87520-1010ALF",
        ("J4",): "KLPX-0848A-2-W-G", ("J5",): "KLPX-0848A-2-R-G",
        ("J7",): "503398-1892", ("SW1", "SW2"): "B3U-3000P-B",
    }
    for refs, mpn in expected_mpns.items():
        if selections.get(refs, {}).get("mpn") != mpn:
            errors.append(f"B4 exact-part intent drift for {refs}")

    try:
        pcb_text = PCB.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"PCB shell unreadable: {exc}")
        pcb_text = ""
    if '(layer "Edge.Cuts")' in pcb_text:
        errors.append("Edge.Cuts exist while PCB_OUTLINE gate is open")

    try:
        sch = DISPLAY_SCH.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"display schematic unreadable: {exc}")
        sch = ""
    for token in ("DSI15_HOST", "SFW15R-2STE1LF", "Pajoniiir-M1:Amphenol_SFW15R-2STE1LF"):
        if token not in sch:
            errors.append(f"generic J6 schematic token missing: {token}")
    if "FINAL DISPLAY:" in sch:
        errors.append("10_DISPLAY_MIPI still designates one final display model")
    if re.search(r'\(reference "(?:U9|L3|D4)"\)', sch):
        errors.append("legacy discrete backlight instance survived in 10_DISPLAY_MIPI")

    print("Pajoniiir-M1 board-first mechanical validation at M1-MECH-B7")
    print("  product authority: standalone mainboard")
    print("  display interface: generic 15-pin Raspberry-Pi-style MIPI DSI")
    print("  validated display profiles: DSI506/DYL0023")
    print(f"  exact external-part groups retained: {len(expected_mpns)}")
    print(f"  open layout blockers: {len(blockers)}")
    print(f"  final board outline locked: {pcb.get('board_outline_locked')}")
    print(f"  layout freeze allowed: {gates.get('layout_freeze_allowed')}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("PASS: display profiles are isolated from mainboard geometry and layout remains fail-closed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
