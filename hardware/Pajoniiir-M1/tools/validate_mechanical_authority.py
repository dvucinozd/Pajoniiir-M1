#!/usr/bin/env python3
"""Fail-closed validator for the B2-converged M1-MECH-A13 authority.

This validates consistency, not physical fit.  It deliberately requires the layout
freeze to remain blocked until real DSI506/enclosure/connector/EVT evidence closes
all mechanical gates.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
MECH = BASE / "mech_a.json"
GATES = BASE / "mechanical_gates.json"
PCB_CONSTRAINTS = BASE / "pcb_constraints.json"
FINAL_DISPLAY = BASE / "final_display_module.json"
CONNECTOR = BASE / "display_connector_b1.json"
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


def main() -> int:
    errors: list[str] = []
    mech = load(MECH, errors)
    gates = load(GATES, errors)
    pcb = load(PCB_CONSTRAINTS, errors)
    display = load(FINAL_DISPLAY, errors)
    connector = load(CONNECTOR, errors)

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
    stale_remaining = {
        "exact production 15-pin 1.0 mm FFC receptacle MPN",
        "top/bottom contact orientation and cable inversion for the selected receptacle",
    }
    if stale_remaining.intersection(display.get("remaining_gates", [])):
        errors.append("final_display_module still lists connector-selection work already closed by B1/B2")

    conn = connector.get("connector", {})
    fp = connector.get("footprint", {})
    if (conn.get("mpn"), conn.get("contacts"), conn.get("pitch_mm"), conn.get("contact_location")) != (
        "SFW15R-2STE1LF", 15, 1.0, "top"
    ):
        errors.append("display_connector_b1 J6 identity/contact geometry drift")
    if fp.get("library_id") != "Pajoniiir-M1:Amphenol_SFW15R-2STE1LF":
        errors.append("display_connector_b1 footprint authority drift")

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
    required_physical = {
        "actual DSI506 FFC conductor-side / host-to-module pin-1 continuity check",
        "FFC bend/insertion/mating keepout in final enclosure",
        "absolute J6 XY/Z placement relative to final DSI506 and custom mainboard",
    }
    if set(j6.get("required_evidence", [])) != required_physical:
        errors.append("J_LCD_DISPLAY_FPC required evidence drift")

    outline = by_id.get("PCB_OUTLINE", {})
    if outline.get("status") != "open" or outline.get("blocks_layout_freeze") is not True:
        errors.append("PCB_OUTLINE must remain open until new enclosure/mainboard datums exist")
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
    # Match actual instance references, not cached library symbol reference prefixes.
    if re.search(r'\(reference "(?:U9|L3|D4)"\)', sch):
        errors.append("legacy discrete backlight instance survived in 10_DISPLAY_MIPI")

    print("Pajoniiir-M1 M1-MECH-A13 mechanical authority validation")
    print(f"  active display: {authority.get('family', '?')}")
    print(f"  preliminary rear PCB: {rear.get('x', '?')} x {rear.get('y', '?')} mm")
    print(f"  J6: {host.get('mpn', '?')} / {host.get('contacts', '?')}P / {host.get('pitch_mm', '?')} mm / {host.get('contact_location', '?')} contact")
    print(f"  open layout blockers: {len(blockers)}")
    print(f"  board outline locked: {pcb.get('board_outline_locked')}")
    print(f"  layout freeze allowed: {gates.get('layout_freeze_allowed')}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("PASS: B2-converged mechanical authority is internally consistent and fail-closed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
