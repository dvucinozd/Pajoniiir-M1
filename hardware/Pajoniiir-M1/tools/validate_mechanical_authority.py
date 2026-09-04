#!/usr/bin/env python3
"""Fail-closed validator for the current Pajoniiir-M1 mechanical authority.

This validates repository consistency, not final physical fit.  B2 direct display
mounting, B3 screening envelopes/wall assignments and B4 connector MPN choices are
now machine-checked, while final Edge.Cuts/layout freeze remain deliberately blocked
until the remaining physical placement/EVT gates close.
"""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
MECH = BASE / "mech_a.json"
GATES = BASE / "mechanical_gates.json"
PCB_CONSTRAINTS = BASE / "pcb_constraints.json"
FINAL_DISPLAY = BASE / "final_display_module.json"
CONNECTOR = BASE / "display_connector_b1.json"
MOUNT_LOCK = BASE / "dsi506_inner_posts_lock_b2.json"
B3 = BASE / "m1_mech_b3_mainboard_io_envelope.json"
ENC = BASE / "m1_mech_b3_enclosure_candidate.json"
B4 = BASE / "m1_mech_b4_connector_source_lock.json"
PCB = BASE / "Pajoniiir-M1.kicad_pcb"
DISPLAY_SCH = BASE / "10_DISPLAY_MIPI.kicad_sch"

EXPECTED_BLOCKERS = {
    "C3_INPUT_BULK",
    "C8_PROTECTED_BULK",
    "J1_POWER_INPUT",
    "SW1_RESET",
    "SW2_BOOT",
    "J2_USB0",
    "J3_USB1",
    "J4_RCA_L",
    "J5_RCA_R",
    "J_LCD_DISPLAY_FPC",
    "J7_MICROSD",
    "PCB_OUTLINE",
}


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


def close(a: float | None, b: float, tol: float = 1e-6) -> bool:
    return isinstance(a, (int, float)) and math.isclose(float(a), b, abs_tol=tol)


def main() -> int:
    errors: list[str] = []
    mech = load(MECH, errors)
    gates = load(GATES, errors)
    pcb = load(PCB_CONSTRAINTS, errors)
    display = load(FINAL_DISPLAY, errors)
    connector = load(CONNECTOR, errors)
    mount = load(MOUNT_LOCK, errors)
    b3 = load(B3, errors)
    enc = load(ENC, errors)
    b4 = load(B4, errors)

    # ------------------------------------------------------------------
    # A13/B2 display authority remains the parent fail-closed baseline.
    # ------------------------------------------------------------------
    authority = mech.get("authoritative_display_reference", {})
    if authority.get("family") != "EYOYO DSI506 / DYL0023":
        errors.append("mech_a active display authority is not DSI506/DYL0023")
    rear = authority.get("rear_pcb_envelope", {})
    if (rear.get("x"), rear.get("y")) != (121.109, 77.193):
        errors.append(f"final display rear-PCB evidence drift: {(rear.get('x'), rear.get('y'))}")
    host = authority.get("host_connector", {})
    expected_host = (
        "SFW15R-2STE1LF", 15, 1.0, "top",
        "Pajoniiir-M1:Amphenol_SFW15R-2STE1LF",
    )
    observed_host = (
        host.get("mpn"), host.get("contacts"), host.get("pitch_mm"),
        host.get("contact_location"), host.get("footprint"),
    )
    if observed_host != expected_host:
        errors.append(f"mech_a J6 authority drift: {observed_host} != {expected_host}")
    legacy = mech.get("legacy_guition_display_reference", {})
    if "JC4880" not in str(legacy.get("family", "")):
        errors.append("legacy JC4880 reference was not preserved explicitly")
    if mech.get("final_board_outline_locked") is not False:
        errors.append("final_board_outline_locked must remain false")
    if "A13" not in str(mech.get("repo_only_analysis_boundary", {}).get("revision", "")):
        errors.append("repo-only boundary is not M1-MECH-A13")

    rebase = mech.get("m1_enclosure_baseline", {}).get("final_display_rebase", {})
    if rebase.get("old_enclosure_verdict") != "HARD_FAIL__ENCLOSURE_REDIMENSION_REQUIRED":
        errors.append("old enclosure is not locked as HARD_FAIL for DSI506")
    if rebase.get("new_enclosure_required") is not True:
        errors.append("new DSI506 enclosure must be required")
    for key in ("external_envelope_candidate", "rear_mechanical_envelope_candidate", "pcb_envelope_candidate"):
        obj = mech.get("m1_enclosure_baseline", {}).get(key, {})
        if isinstance(obj, dict) and obj.get("production_authority") is not False:
            errors.append(f"legacy {key} is still eligible as production authority")
    z = mech.get("m1_enclosure_baseline", {}).get("z_stack_candidate", {})
    if isinstance(z, dict) and z.get("production_authority") is not False:
        errors.append("legacy JC4880 Z stack is still eligible as production authority")

    freeze = display.get("freeze", {})
    for key in (
        "final_display_selected", "production_connector_mpn_locked",
        "production_connector_contact_side_locked", "production_connector_footprint_locked",
        "schematic_migrated_to_final_display",
    ):
        if freeze.get(key) is not True:
            errors.append(f"final_display_module freeze flag must be true: {key}")
    if freeze.get("placement_routing_freeze_allowed") is not False:
        errors.append("final_display_module placement/routing freeze must remain false")

    conn = connector.get("connector", {})
    fp = connector.get("footprint", {})
    if (conn.get("mpn"), conn.get("contacts"), conn.get("pitch_mm"), conn.get("contact_location")) != (
        "SFW15R-2STE1LF", 15, 1.0, "top"
    ):
        errors.append("display_connector_b1 J6 identity/contact geometry drift")
    if fp.get("library_id") != "Pajoniiir-M1:Amphenol_SFW15R-2STE1LF":
        errors.append("display_connector_b1 footprint authority drift")

    # ---------------------------------------------------------------
    # B2 direct-mount lock: physical user measurements, now authoritative.
    # ---------------------------------------------------------------
    if mount.get("status") != "LOCKED_FOR_M1_MAINBOARD_DIRECT_DISPLAY_MOUNT":
        errors.append("B2 direct display mount is not locked")
    post = mount.get("post", {})
    if post.get("count") != 4 or post.get("thread") != "M2.5" or post.get("thread_status") != "PHYSICALLY_CONFIRMED":
        errors.append("B2 four-post M2.5 thread authority drift")
    if not close(post.get("outer_diameter_mm"), 5.0) or not close(post.get("height_above_display_rear_pcb_mm"), 5.0):
        errors.append("B2 post OD/height drift")
    if not close(post.get("usable_thread_depth_mm"), 3.0) or post.get("coplanarity") != "PHYSICALLY_CONFIRMED":
        errors.append("B2 post depth/coplanarity drift")
    pattern = mount.get("mount_pattern", {})
    if not close(pattern.get("spacing_x_mm"), 58.0) or not close(pattern.get("spacing_y_mm"), 49.0):
        errors.append("B2 58 x 49 mm mount pattern drift")
    zlock = mount.get("z_lock", {})
    if not close(zlock.get("mainboard_display_facing_surface_z_mm"), 10.0) or not close(zlock.get("mainboard_rear_surface_z_mm_for_1p6mm_pcb"), 11.6):
        errors.append("B2 mainboard Z authority drift")
    screw = mount.get("rev_a_screw_baseline", {})
    if screw.get("thread") != "M2.5" or not close(screw.get("nominal_length_mm"), 4.0):
        errors.append("B2 Rev-A screw baseline is not M2.5 x 4.0 mm")
    if not close(screw.get("nominal_thread_engagement_mm_without_washer"), 2.4) or not close(screw.get("nominal_bottoming_margin_mm"), 0.6):
        errors.append("B2 screw engagement arithmetic drift")

    # ------------------------------------------------------------------
    # B3 104 x 62 placement-screening envelope and absolute wall topology.
    # ------------------------------------------------------------------
    if b3.get("milestone") != "M1-MECH-B3":
        errors.append("B3 mainboard authority missing")
    core = b3.get("core_mainboard_envelope_candidate", {})
    ext = core.get("display_relative_extents_mm", {})
    if not (close(core.get("width_mm"), 104.0) and close(core.get("height_mm"), 62.0)):
        errors.append("B3 core mainboard envelope drift")
    if not all((
        close(ext.get("x_min"), 8.5), close(ext.get("x_max"), 112.5),
        close(ext.get("y_min"), 0.93), close(ext.get("y_max"), 62.93),
    )):
        errors.append("B3 display-relative core extents drift")
    if not close(float(ext.get("x_max", 0)) - float(ext.get("x_min", 0)), 104.0):
        errors.append("B3 X extent arithmetic does not equal 104 mm")
    if not close(float(ext.get("y_max", 0)) - float(ext.get("y_min", 0)), 62.0):
        errors.append("B3 Y extent arithmetic does not equal 62 mm")
    holes = b3.get("mainboard_mount_holes_local_mm", [])
    expected_holes = {(34.609, 6.5), (92.609, 6.5), (34.609, 55.5), (92.609, 55.5)}
    observed_holes = {(round(float(h.get("x", -999)), 3), round(float(h.get("y", -999)), 3)) for h in holes if isinstance(h, dict)}
    if observed_holes != expected_holes:
        errors.append(f"B3 local mounting-hole coordinates drift: {sorted(observed_holes)}")
    hp = b3.get("mount_hole_policy", {})
    if hp.get("type") != "NPTH clearance holes" or hp.get("production_diameter_locked") is not False:
        errors.append("B3 NPTH policy must remain an unlocked 3.0-3.2 mm engineering range")
    if hp.get("engineering_diameter_range_mm") != [3.0, 3.2]:
        errors.append("B3 mounting-hole engineering range drift")

    walls = b3.get("absolute_io_wall_assignment", {})
    expected_walls = {
        "PRIMARY_LONG_IO_WALL": ("Y_NEG", ["J2_USB0", "J3_USB1", "J4_RCA_L", "J5_RCA_R"]),
        "POWER_WALL": ("X_NEG", ["J1_POWER_INPUT"]),
        "MEDIA_SERVICE_WALL": ("X_POS", ["J7_MICROSD", "SW1_RESET", "SW2_BOOT"]),
        "CLEAR_LONG_WALL": ("Y_POS", []),
    }
    for name, (axis, funcs) in expected_walls.items():
        w = walls.get(name, {})
        if w.get("axis") != axis or w.get("functions") != funcs:
            errors.append(f"B3 wall assignment drift for {name}: {w}")
    if b3.get("freeze", {}).get("final_board_outline_locked") is not False or b3.get("freeze", {}).get("layout_freeze_allowed") is not False:
        errors.append("B3 must not final-lock board outline/layout")

    # ------------------------------------------------------------------
    # B3 compact enclosure screening candidate, deliberately non-production.
    # ------------------------------------------------------------------
    ee = enc.get("external_envelope_candidate_mm", {})
    if not (close(ee.get("width_x"), 128.0) and close(ee.get("height_y"), 84.0) and close(ee.get("depth_z"), 30.0)):
        errors.append("B3 enclosure screening envelope drift")
    if not close(enc.get("wall_thickness_candidate_mm"), 2.0):
        errors.append("B3 enclosure wall screening thickness drift")
    inner = enc.get("inner_cavity_candidate_mm", {})
    if not (close(inner.get("width_x"), 124.0) and close(inner.get("height_y"), 80.0) and close(inner.get("rear_inner_plane_z"), 28.0)):
        errors.append("B3 inner cavity arithmetic drift")
    dfit = enc.get("display_fit_screen", {}).get("nominal_clearance_each_side_mm", {})
    if not close(dfit.get("x"), 1.4455, 1e-4) or not close(dfit.get("y"), 1.4035, 1e-4):
        errors.append("B3 display/cavity clearance arithmetic drift")
    zscreen = enc.get("z_stack_screen", {})
    if not close(zscreen.get("gross_mainboard_rear_to_rear_inner_clearance_mm"), 16.4):
        errors.append("B3 rear cavity Z arithmetic drift")
    efreeze = enc.get("freeze", {})
    if efreeze.get("production_enclosure_dimensions_locked") is not False or efreeze.get("layout_freeze_allowed") is not False:
        errors.append("B3 enclosure candidate was incorrectly promoted to production/layout freeze")

    # ------------------------------------------------------------------
    # B4 exact MPN intent is locked while mechanical placement remains open.
    # ------------------------------------------------------------------
    selections = b4.get("selections", [])
    by_refs: dict[tuple[str, ...], dict] = {}
    for sel in selections:
        if isinstance(sel, dict):
            by_refs[tuple(sel.get("refdes", []))] = sel
    expected_mpns = {
        ("J1",): ("Switchcraft", "722RAHLP"),
        ("J2", "J3"): ("Amphenol Communications Solutions / FCI", "87520-1010ALF"),
        ("J4",): ("Kycon", "KLPX-0848A-2-W-G"),
        ("J5",): ("Kycon", "KLPX-0848A-2-R-G"),
        ("J7",): ("Molex", "503398-1892"),
        ("SW1", "SW2"): ("Aratas (formerly Omron Components)", "B3U-3000P-B"),
    }
    for refs, expected in expected_mpns.items():
        sel = by_refs.get(refs, {})
        observed = (sel.get("manufacturer"), sel.get("mpn"))
        if observed != expected:
            errors.append(f"B4 MPN drift for {refs}: {observed} != {expected}")
        if "LOCKED" not in str(sel.get("selection_status", "")):
            errors.append(f"B4 selection not locked for {refs}")
    if b4.get("gates_closed_by_this_milestone") != []:
        errors.append("B4 MPN lock must not claim connector mechanical gates closed")

    # ------------------------------------------------------------------
    # Existing open-gate / PCB constraints remain fail-closed.
    # ------------------------------------------------------------------
    gate_list = gates.get("gates", [])
    blockers = {
        gate.get("id") for gate in gate_list
        if isinstance(gate, dict) and gate.get("blocks_layout_freeze") and gate.get("status") != "closed"
    }
    if blockers != EXPECTED_BLOCKERS:
        errors.append(f"unexpected open blocker set: {sorted(blockers)}")
    if gates.get("layout_freeze_allowed") is not False:
        errors.append("mechanical_gates layout_freeze_allowed must remain false")

    by_id = {gate.get("id"): gate for gate in gate_list if isinstance(gate, dict)}
    j6 = by_id.get("J_LCD_DISPLAY_FPC", {})
    if j6.get("status") != "open" or j6.get("blocks_layout_freeze") is not True:
        errors.append("J_LCD_DISPLAY_FPC must remain an open mechanical placement/cable gate")
    if (j6.get("exact_mpn"), j6.get("contact_count"), j6.get("pitch_mm"), j6.get("contact_location")) != (
        "SFW15R-2STE1LF", 15, 1.0, "top"
    ):
        errors.append("J_LCD_DISPLAY_FPC gate does not match B2 connector authority")
    active_j6_text = json.dumps({"known": j6.get("known"), "required": j6.get("required_evidence")}, ensure_ascii=False)
    if "0.5TBQP-30P-1" in active_j6_text or "30 contacts" in active_j6_text:
        errors.append("J_LCD_DISPLAY_FPC active gate still contains legacy 30-pin Guition assumptions")

    outline = by_id.get("PCB_OUTLINE", {})
    if outline.get("status") != "open" or outline.get("blocks_layout_freeze") is not True:
        errors.append("PCB_OUTLINE must remain open while B3 is only a screening envelope")
    if outline.get("legacy_enclosure_decision") != "REJECTED__HARD_FAIL_FOR_DSI506":
        errors.append("PCB_OUTLINE does not record rejection of the old enclosure")

    if pcb.get("board_outline_locked") is not False:
        errors.append("pcb_constraints board_outline_locked must remain false")
    if pcb.get("stackup_locked") is not True:
        errors.append("JLC fabrication stackup must remain locked")
    if pcb.get("controlled_impedance_locked") is not False:
        errors.append("controlled impedance geometry must remain unlocked before exact calculator output")
    routing = pcb.get("routing_targets", {})
    if "BACKLIGHT" in routing:
        errors.append("legacy host-side BACKLIGHT routing target survived B2 convergence")
    domains = [d for d in pcb.get("placement_domains", []) if isinstance(d, dict) and d.get("id") == "DISPLAY"]
    if len(domains) != 1 or set(domains[0].get("members", [])) != {"J6", "FB3", "C93", "C94"}:
        errors.append(f"DISPLAY placement domain is not the B2 module-power/J6 domain: {domains}")
    mr = pcb.get("mechanical_reference", {})
    if mr.get("final_display") != "EYOYO DSI506 / DYL0023" or mr.get("new_enclosure_required") is not True:
        errors.append("pcb_constraints mechanical reference not rebased to DSI506/new enclosure")
    if pcb.get("candidate_board_envelope", {}).get("production_authority") is not False:
        errors.append("legacy candidate board envelope is still production-authoritative")

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
    if 'SFW15R-2STE1LF' not in sch or 'Pajoniiir-M1:Amphenol_SFW15R-2STE1LF' not in sch:
        errors.append("10_DISPLAY_MIPI does not carry the locked J6 identity/footprint")
    if re.search(r'\(reference "(?:U9|L3|D4)"\)', sch):
        errors.append("legacy discrete backlight instance survived in 10_DISPLAY_MIPI")

    print("Pajoniiir-M1 mechanical authority validation through M1-MECH-B4")
    print(f"  active display: {authority.get('family', '?')}")
    print("  direct mount: 4x M2.5 / 58 x 49 mm / seating Z=10.0 mm")
    print("  B3 core board screen: 104 x 62 mm")
    print("  B3 enclosure screen: 128 x 84 x 30 mm")
    print("  walls: Y- USB/RCA; X- power; X+ media/service; Y+ clear")
    print(f"  B4 locked MPN groups: {len(expected_mpns)}")
    print(f"  open layout blockers: {len(blockers)}")
    print(f"  final board outline locked: {pcb.get('board_outline_locked')}")
    print(f"  layout freeze allowed: {gates.get('layout_freeze_allowed')}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("PASS: B2/B3/B4 mechanical authority is internally consistent and remains fail-closed for final layout.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
