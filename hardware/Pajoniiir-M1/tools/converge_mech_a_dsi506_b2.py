#!/usr/bin/env python3
"""Converge M1-MECH-A machine authority onto the final DSI506/B2 display contract.

This intentionally does *not* close physical/EVT gates.  It removes stale pre-B0
Guition assumptions from active mechanical authority, preserves them as explicit
legacy evidence, rebases PCB/mechanical constraints, and updates the physical
handoff documentation.  The migration is fail-closed and idempotent.
"""
from __future__ import annotations

import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
REPO = BASE.parents[1]
DOCS = REPO / "docs"
MECH = BASE / "mech_a.json"
GATES = BASE / "mechanical_gates.json"
PCB_CONSTRAINTS = BASE / "pcb_constraints.json"
FINAL_DISPLAY = BASE / "final_display_module.json"
CONNECTOR = BASE / "display_connector_b1.json"
STRUCTURAL = BASE / "tools" / "validate_schematic_structure.py"
OLD_BASELINE_DOC = DOCS / "Pajoniiir_M1_MECH_A_Baseline_v0.1.md"
BOUNDARY_DOC = DOCS / "Pajoniiir_M1_MECH_A_Physical_Evidence_Boundary_v0.1.md"
B0_DOC = DOCS / "Pajoniiir_M1_MECH_B0_Final_5in_DSI_Display_Baseline_v0.1.md"
A13_DOC = DOCS / "Pajoniiir_M1_MECH_A13_B2_Convergence_Physical_Handoff_v0.1.md"

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
PERIMETER_GATES = {
    "J1_POWER_INPUT", "SW1_RESET", "SW2_BOOT", "J2_USB0", "J3_USB1",
    "J4_RCA_L", "J5_RCA_R", "J7_MICROSD",
}


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"{path.name}: invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"{path.name}: root must be an object")
    return value


def dump(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def gate_by_id(data: dict, gate_id: str) -> dict:
    for gate in data.get("gates", []):
        if isinstance(gate, dict) and gate.get("id") == gate_id:
            return gate
    raise SystemExit(f"mechanical gate missing: {gate_id}")


def assert_b2(display: dict, conn: dict) -> None:
    product = display.get("final_product_display", {})
    freeze = display.get("freeze", {})
    c = conn.get("connector", {})
    fp = conn.get("footprint", {})
    expected = {
        "identity": "EYOYO DSI506 / DYL0023 5-inch 800x480 IPS MIPI-DSI capacitive-touch module",
        "connector": "SFW15R-2STE1LF",
        "contacts": 15,
        "pitch": 1.0,
        "contact": "top",
        "footprint": "Pajoniiir-M1:Amphenol_SFW15R-2STE1LF",
    }
    observed = {
        "identity": product.get("identity"),
        "connector": c.get("mpn"),
        "contacts": c.get("contacts"),
        "pitch": c.get("pitch_mm"),
        "contact": c.get("contact_location"),
        "footprint": fp.get("library_id"),
    }
    if observed != expected:
        raise SystemExit(f"B2 display authority drift: {observed} != {expected}")
    required_freezes = (
        "final_display_selected",
        "production_connector_mpn_locked",
        "production_connector_contact_side_locked",
        "production_connector_footprint_locked",
        "schematic_migrated_to_final_display",
    )
    bad = [key for key in required_freezes if freeze.get(key) is not True]
    if bad:
        raise SystemExit("B2 freeze flags not locked: " + ", ".join(bad))


def converge_final_display(display: dict) -> None:
    display["updated"] = "2026-09-04"
    display["remaining_gates"] = [
        "actual DSI506 FFC conductor-side / host-to-module pin-1 continuity check",
        "FFC approach/bend/mating keepout in the final enclosure",
        "local 3V3 display branch all-on/startup/transient EVT",
        "full module Z envelope and all eight mounting-hole coordinates",
        "new enclosure XY/Z datums and custom-mainboard placement/outline",
    ]
    display.setdefault("freeze", {})["placement_routing_freeze_allowed"] = False


def converge_mech(mech: dict, display: dict, blockers: list[str]) -> None:
    old = mech.get("authoritative_display_reference")
    if not isinstance(old, dict):
        raise SystemExit("mech_a.json lacks prior authoritative_display_reference")
    if "legacy_guition_display_reference" not in mech:
        if "JC4880" not in str(old.get("family", "")):
            raise SystemExit("refusing to archive unknown prior display authority")
        mech["legacy_guition_display_reference"] = old
    elif "JC4880" not in str(mech["legacy_guition_display_reference"].get("family", "")):
        raise SystemExit("legacy_guition_display_reference is not the expected historical family")

    ev = display.get("user_dimensioned_image_evidence", {})
    old_conflict = display.get("old_enclosure_conflict", {})
    mech["authoritative_display_reference"] = {
        "family": "EYOYO DSI506 / DYL0023",
        "orientation_for_M1": "landscape",
        "authority": "final_display_module.json + display_connector_b1.json; supersedes JC4880/Guition for final-product mechanics",
        "status": "FINAL_PRODUCT_DISPLAY__PRELIMINARY_DIMENSIONED_IMAGE_EVIDENCE__PHYSICAL_CALIPER_OR_OFFICIAL_CAD_REQUIRED_FOR_PRODUCTION",
        "rear_pcb_envelope": {
            "x": ev.get("rear_pcb_envelope_mm", [None, None])[0],
            "y": ev.get("rear_pcb_envelope_mm", [None, None])[1],
            "status": ev.get("status"),
        },
        "mounting_evidence": {
            "visible_hole_count": ev.get("visible_mount_hole_count"),
            "outer_hole_diameter_mm": ev.get("mount_hole_diameter_mm"),
            "outer_hole_centers_from_rear_pcb_top_left_mm": ev.get("outer_hole_centers_from_rear_pcb_top_left_mm"),
            "outer_hole_center_spacing_mm": ev.get("outer_hole_center_spacing_mm"),
            "status": "preliminary image-derived evidence; all eight centers and full Z stack require physical/CAD confirmation",
        },
        "host_connector": {
            "refdes": "J6",
            "mpn": "SFW15R-2STE1LF",
            "manufacturer": "Amphenol Communications Solutions / FCI",
            "contacts": 15,
            "pitch_mm": 1.0,
            "contact_location": "top",
            "orientation": "right-angle / side-entry SMT ZIF",
            "housing_height_mm": 2.7,
            "footprint": "Pajoniiir-M1:Amphenol_SFW15R-2STE1LF",
            "status": "MPN/contact-side/footprint locked and instantiated M1-ELEC-B2",
        },
        "legacy_enclosure_compatibility": {
            "old_external_envelope_mm": old_conflict.get("old_external_envelope_mm"),
            "old_inner_cavity_mm": old_conflict.get("old_inner_cavity_mm"),
            "display_rear_pcb_mm": old_conflict.get("display_rear_pcb_mm"),
            "verdict": old_conflict.get("verdict"),
            "new_enclosure_required": True,
        },
        "unresolved": [
            "actual DSI506 FFC conductor-side / host-to-module pin-1 continuity check",
            "FFC approach/bend/mating keepout in final enclosure",
            "complete module Z envelope",
            "all eight mounting-hole coordinates confirmed from physical measurement or official CAD",
            "new enclosure and custom-mainboard absolute XY/Z datums",
        ],
    }

    enclosure = mech.setdefault("m1_enclosure_baseline", {})
    for key in ("external_envelope_candidate", "legacy_module_shell_reference", "rear_mechanical_envelope_candidate", "pcb_envelope_candidate"):
        obj = enclosure.get(key)
        if isinstance(obj, dict):
            obj["status"] = "SUPERSEDED_LEGACY_JC4880_REFERENCE__NOT_FINAL_DSI506_AUTHORITY"
            obj["production_authority"] = False
    z = enclosure.get("z_stack_candidate")
    if isinstance(z, dict):
        z["status"] = "SUPERSEDED_LEGACY_JC4880_Z_STACK__DO_NOT_USE_FOR_DSI506_PRODUCTION_CLEARANCE"
        z["production_authority"] = False
    enclosure["final_display_rebase"] = {
        "revision": "M1-MECH-A13",
        "display_rear_pcb_mm": ev.get("rear_pcb_envelope_mm"),
        "old_enclosure_verdict": old_conflict.get("verdict"),
        "old_external_envelope_mm": old_conflict.get("old_external_envelope_mm"),
        "old_inner_cavity_mm": old_conflict.get("old_inner_cavity_mm"),
        "new_enclosure_required": True,
        "new_enclosure_locked": False,
        "custom_mainboard_outline_locked": False,
        "production_z_stack_locked": False,
        "rule": "Do not derive DSI506 Edge.Cuts, standoffs or component-height limits from the old JC4880 enclosure/Z stack.",
    }

    mech["updated"] = "2026-09-04"
    mech["status"] = "repo_only_M1_MECH_A13_B2_convergence_complete__layout_freeze_blocked_by_physical_EVT_and_new_enclosure_evidence"
    mech["final_board_outline_locked"] = False
    boundary = mech.setdefault("repo_only_analysis_boundary", {})
    boundary["revision"] = "M1-MECH-A13"
    boundary["status"] = "B2-converged repo-only mechanical authority complete; remaining blockers require physical/EVT/new-enclosure evidence"
    boundary["remaining_open_blockers"] = blockers
    boundary["resume_inputs"] = [
        "DSI506 physical/caliper or official CAD package including full Z and all eight hole centers",
        "new enclosure interior/wall/boss datums in M1_FRONT_CENTER",
        "final side/rear connector cutout and mated-cable envelopes",
        "C3/C8 startup/inrush and protected-rail transient EVT sweep",
    ]


def converge_gates(gates: dict) -> list[str]:
    j6 = gate_by_id(gates, "J_LCD_DISPLAY_FPC")
    j6.update({
        "documentation_alias": "J_DISPLAY_DSI506 (legacy documents may use J_LCD)",
        "known": [
            "final product display = EYOYO DSI506 / DYL0023, 5-inch 800x480",
            "host receptacle = Amphenol SFW15R-2STE1LF",
            "15 contacts, 1.0 mm pitch, TOP contact",
            "right-angle / side-entry SMT ZIF",
            "housing height 2.7 mm",
            "project footprint Pajoniiir-M1:Amphenol_SFW15R-2STE1LF is drawing-verified and instantiated",
            "electrical map and initial operating profile are bench-derived from Pajoniiir-M3",
        ],
        "source": "hardware/Pajoniiir-M1/display_connector_b1.json",
        "required_evidence": [
            "actual DSI506 FFC conductor-side / host-to-module pin-1 continuity check",
            "FFC bend/insertion/mating keepout in final enclosure",
            "absolute J6 XY/Z placement relative to final DSI506 and custom mainboard",
        ],
        "closure": "Connector identity/contact side/footprint are closed electrically. Mechanical gate remains open only for actual cable orientation, FFC motion keepout and final absolute placement.",
        "evidence_file": "display_connector_b1.json + final_display_module.json + mech_a.json",
        "height_audit": "Connector housing height 2.7 mm locked; mated cable bend/Z envelope still open",
        "partial_closure_revision": "M1-MECH-A13 / M1-ELEC-B2",
        "resolved_evidence": [
            {
                "item": "production host receptacle",
                "resolution": "Amphenol SFW15R-2STE1LF, 15P 1.0 mm TOP-contact right-angle SMT ZIF; footprint verified and instantiated in M1-ELEC-B2.",
                "authority": "display_connector_b1.json",
            },
            {
                "item": "legacy 30-pin Guition path",
                "resolution": "Superseded by the final DSI506 module contract; retained only as historical evidence outside the active gate.",
                "authority": "final_display_module.json",
            },
        ],
        "exact_mpn": "SFW15R-2STE1LF",
        "manufacturer": "Amphenol Communications Solutions / FCI",
        "exact_footprint": "Pajoniiir-M1:Amphenol_SFW15R-2STE1LF",
        "contact_count": 15,
        "pitch_mm": 1.0,
        "contact_location": "top",
        "connector_orientation": "right-angle / side-entry SMT ZIF",
        "electrical_pin_map_status": "LOCKED_M1-ELEC-B0",
        "schematic_status": "INSTANTIATED_M1-ELEC-B2",
        "footprint_status": "DRAWING_VERIFIED_M1-ELEC-B2",
    })

    outline = gate_by_id(gates, "PCB_OUTLINE")
    outline["required_evidence"] = [
        "new enclosure XY/Z and wall/boss datums sized for the final DSI506 module",
        "final custom-mainboard X/Y dimensions and Edge.Cuts",
        "final mounting-hole coordinates / standoff and screw hardware",
        "edge clearances to the final DSI506 rear PCB and all enclosure bosses/ribs",
        "absolute J6 FFC approach/bend envelope",
        "all user connector body/cutout/mated-plug clearances",
        "final PCB Z plane after connector and display-envelope validation",
    ]
    outline["closure"] = "Design and validate a new DSI506-compatible enclosure/mainboard datum set, then commit authoritative Edge.Cuts and mounting datums. The old 108 x 65.06 mm JC4880 feasibility rectangle is superseded and is not Edge.Cuts authority."
    outline["known_evidence"] = [
        "final DSI506 rear PCB preliminary envelope = 121.109 x 77.193 mm",
        "eight mounting holes are visible; outer four preliminary centers imply 111.109 x 67.930 mm spacing with ~2.5 mm holes",
        "old external enclosure 121.008 x 73.408 mm and inner cavity 117.008 x 69.408 mm are a HARD FAIL for the final display",
        "old 108.00 x 65.06 mm mainboard envelope and +/-51.3 x +/-30.0 mounting candidate were JC4880-era feasibility data only",
        "final display connector is J6 Amphenol SFW15R-2STE1LF; cable/bend/absolute placement remains open",
        "JLCPCB JLC04161H-7628 4-layer 1.6 mm fabrication stackup remains locked",
    ]
    outline["evidence_file"] = "final_display_module.json + mech_a.json"
    outline["legacy_enclosure_decision"] = "REJECTED__HARD_FAIL_FOR_DSI506"

    for gate in gates.get("gates", []):
        if not isinstance(gate, dict):
            continue
        if gate.get("id") in PERIMETER_GATES:
            gate["post_b2_geometry_status"] = "REQUIRES_NEW_DSI506_ENCLOSURE_DATUM__PRE_B0_PANEL_PACKING_IS_SCREENING_ONLY"
            if "panel_packing_screen" in gate:
                gate["panel_packing_authority"] = "legacy_JC4880_enclosure_screen_only__must_revalidate_in_new_DSI506_enclosure"

    blockers = [
        gate.get("id") for gate in gates.get("gates", [])
        if isinstance(gate, dict) and gate.get("blocks_layout_freeze") and gate.get("status") != "closed"
    ]
    if set(blockers) != EXPECTED_BLOCKERS:
        raise SystemExit(f"unexpected blocker set before/after convergence: {blockers}")
    gates["updated"] = "2026-09-04"
    gates["layout_freeze_allowed"] = False
    gates["mechanical_authority"] = "mech_a.json / M1-MECH-A13 B2-converged"
    return blockers


def converge_pcb_constraints(pcb: dict, display: dict) -> None:
    pcb["updated"] = "2026-09-04"
    pcb["layout_state"] = "pre_mechanical_layout__DSI506_enclosure_rebase"
    pcb["board_outline_locked"] = False
    pcb["controlled_impedance_locked"] = False

    routing = pcb.setdefault("routing_targets", {})
    routing.pop("BACKLIGHT", None)
    mipi = routing.get("MIPI_DSI")
    if isinstance(mipi, dict):
        rules = mipi.get("rules", [])
        rules = [
            rule.replace("connector geometry not final until J_LCD gate closes", "J6 MPN/footprint locked; absolute J6/FFC placement remains open until the DSI506 enclosure datum closes")
            for rule in rules
        ]
        mipi["rules"] = rules

    domains = pcb.get("placement_domains", [])
    replaced = False
    for domain in domains:
        if isinstance(domain, dict) and domain.get("id") == "DISPLAY":
            domain.clear()
            domain.update({
                "id": "DISPLAY",
                "members": ["J6", "FB3", "C93", "C94"],
                "priority": "J6 at final DSI506 FFC approach edge; FB3/C93/C94 local to the 3V3 display-module branch while preserving the MIPI corridor",
                "z_note": "J6 housing height is 2.7 mm; final cable bend and absolute XY/Z placement remain mechanical gates",
            })
            replaced = True
    if not replaced:
        domains.append({
            "id": "DISPLAY", "members": ["J6", "FB3", "C93", "C94"],
            "priority": "final DSI506 host connector and local 3V3 branch", "z_note": "final cable/bend XY/Z open"
        })
    pcb["placement_domains"] = domains

    ev = display.get("user_dimensioned_image_evidence", {})
    conflict = display.get("old_enclosure_conflict", {})
    pcb["mechanical_reference"] = {
        "authority": "mech_a.json + final_display_module.json",
        "coordinate_system": "M1_FRONT_CENTER",
        "final_display": "EYOYO DSI506 / DYL0023",
        "display_rear_pcb_preliminary_mm": ev.get("rear_pcb_envelope_mm"),
        "old_enclosure_verdict": conflict.get("verdict"),
        "new_enclosure_required": True,
        "board_outline_locked": False,
        "note": "Do not use the JC4880-era 108 x 65.06 mm rectangle or +/-51.3 x +/-30 mm mount pattern as final Edge.Cuts authority.",
    }
    pcb["component_height_zones"] = {
        "status": "DSI506_PRODUCTION_Z_STACK_NOT_LOCKED",
        "production_limit_locked": False,
        "legacy_JC4880_screen": {
            "gross_front_mm": 6.5,
            "gross_rear_mm": 6.0,
            "authority": "historical screening only; superseded for final DSI506 enclosure design",
        },
        "current_rule": "No production component-height limit may be derived until the final DSI506 enclosure, PCB Z plane, bosses, FFC motion and mated connector envelopes are locked.",
    }
    candidate = pcb.get("candidate_board_envelope")
    if isinstance(candidate, dict):
        candidate["status"] = "SUPERSEDED_JC4880_PLACEMENT_FEASIBILITY_ONLY"
        candidate["edge_cuts_allowed"] = False
        candidate["production_authority"] = False
    pcb["freeze_requirements"] = [
        "mechanical_gates.json: all blocks_layout_freeze gates closed",
        "new DSI506-compatible enclosure and authoritative Edge.Cuts/mounting datums committed",
        "J6 FFC approach/bend and all mated user-connector envelopes validated in enclosure CAD/physical evidence",
        "C3/C8 EVT converted to exact production packages",
        "M1-MECH-A11 JLC04161H-7628 stackup remains selected",
        "controlled_impedance_locked=true only after exact 90 ohm USB / 100 ohm MIPI width-spacing is recorded from the current JLCPCB calculator for the locked stackup",
    ]


def patch_structural_validator() -> None:
    text = STRUCTURAL.read_text(encoding="utf-8")
    start_marker = '        display = mech_a.get("authoritative_display_reference", {})\n'
    end_marker = '    if not PCB_CONSTRAINTS.exists():\n'
    start = text.find(start_marker)
    end = text.find(end_marker, start)
    if start < 0 or end < 0:
        # idempotent success if the new B2 marker is already present
        if "M1-MECH-A13 final DSI506 mechanical authority" in text:
            return
        raise SystemExit("validate_schematic_structure.py: mechanical validation block markers not found")
    replacement = '''        # M1-MECH-A13 final DSI506 mechanical authority.\n        display = mech_a.get("authoritative_display_reference", {})\n        if display.get("family") != "EYOYO DSI506 / DYL0023":\n            errors.append(f"{MECH_A.name}: active display authority must be final DSI506/DYL0023")\n        rear = display.get("rear_pcb_envelope", {})\n        observed_rear = {"x": rear.get("x"), "y": rear.get("y")}\n        expected_rear = {"x": 121.109, "y": 77.193}\n        if observed_rear != expected_rear:\n            errors.append(f"{MECH_A.name}: final DSI506 rear-PCB evidence drift: {observed_rear} != {expected_rear}")\n        host = display.get("host_connector", {})\n        expected_host = {\n            "mpn": "SFW15R-2STE1LF",\n            "contacts": 15,\n            "pitch_mm": 1.0,\n            "contact_location": "top",\n            "footprint": "Pajoniiir-M1:Amphenol_SFW15R-2STE1LF",\n        }\n        observed_host = {key: host.get(key) for key in expected_host}\n        if observed_host != expected_host:\n            errors.append(f"{MECH_A.name}: final display host connector drift: {observed_host} != {expected_host}")\n        legacy = mech_a.get("legacy_guition_display_reference", {})\n        if "JC4880" not in str(legacy.get("family", "")):\n            errors.append(f"{MECH_A.name}: historical Guition reference must remain preserved under legacy_guition_display_reference")\n        rebase = mech_a.get("m1_enclosure_baseline", {}).get("final_display_rebase", {})\n        if rebase.get("old_enclosure_verdict") != "HARD_FAIL__ENCLOSURE_REDIMENSION_REQUIRED":\n            errors.append(f"{MECH_A.name}: old enclosure must remain a hard fail for DSI506")\n        if rebase.get("new_enclosure_required") is not True:\n            errors.append(f"{MECH_A.name}: DSI506 convergence requires a new enclosure")\n\n        final_display_path = BASE / "final_display_module.json"\n        display_connector_path = BASE / "display_connector_b1.json"\n        for authority_path in (final_display_path, display_connector_path):\n            if not authority_path.exists():\n                errors.append(f"missing display authority {authority_path.name}")\n        if final_display_path.exists():\n            try:\n                final_display = json.loads(final_display_path.read_text(encoding="utf-8"))\n            except (OSError, json.JSONDecodeError) as exc:\n                errors.append(f"{final_display_path.name}: invalid JSON: {exc}")\n                final_display = {}\n            freeze = final_display.get("freeze", {})\n            for key in ("final_display_selected", "production_connector_mpn_locked", "production_connector_contact_side_locked", "production_connector_footprint_locked", "schematic_migrated_to_final_display"):\n                if freeze.get(key) is not True:\n                    errors.append(f"{final_display_path.name}: {key} must remain true after B2")\n            if freeze.get("placement_routing_freeze_allowed") is not False:\n                errors.append(f"{final_display_path.name}: placement/routing freeze must remain false while mechanical blockers exist")\n        if display_connector_path.exists():\n            try:\n                dc = json.loads(display_connector_path.read_text(encoding="utf-8"))\n            except (OSError, json.JSONDecodeError) as exc:\n                errors.append(f"{display_connector_path.name}: invalid JSON: {exc}")\n                dc = {}\n            conn = dc.get("connector", {})\n            if (conn.get("mpn"), conn.get("contacts"), conn.get("pitch_mm"), conn.get("contact_location")) != ("SFW15R-2STE1LF", 15, 1.0, "top"):\n                errors.append(f"{display_connector_path.name}: production J6 identity/contact geometry drift")\n\n'''
    text = text[:start] + replacement + text[end:]
    STRUCTURAL.write_text(text, encoding="utf-8")


def prepend_legacy_notice() -> None:
    text = OLD_BASELINE_DOC.read_text(encoding="utf-8")
    notice = """> **SUPERSEDED FOR FINAL-PRODUCT DISPLAY MECHANICS — M1-MECH-A13 / M1-ELEC-B2 (2026-09-04)**  \n> The JC4880/Guition geometry below is retained only as historical enclosure evidence. The final M1 display is EYOYO DSI506 / DYL0023, and its 121.109 × 77.193 mm preliminary rear-PCB evidence makes the old enclosure a hard fail. Do not derive final Edge.Cuts, mounting or Z clearances from this document. Current authority: `final_display_module.json`, `display_connector_b1.json`, `mech_a.json`.\n\n"""
    if "SUPERSEDED FOR FINAL-PRODUCT DISPLAY MECHANICS" not in text:
        first_break = text.find("\n\n")
        if first_break < 0:
            raise SystemExit("legacy MECH-A baseline document malformed")
        text = text[: first_break + 2] + notice + text[first_break + 2 :]
        OLD_BASELINE_DOC.write_text(text, encoding="utf-8")


def update_b0_doc() -> None:
    text = B0_DOC.read_text(encoding="utf-8")
    replacements = {
        "# Pajoniiir-M1 — M1-MECH-B0 Final 5-inch DSI Display Baseline v0.2": "# Pajoniiir-M1 — M1-MECH-B0 Final 5-inch DSI Display Baseline v0.3",
        "production 15-pin receptacle MPN locked       NO": "production 15-pin receptacle MPN locked       YES — SFW15R-2STE1LF",
        "FFC contact-side/cable inversion locked       NO": "host receptacle TOP-contact geometry locked    YES\nactual FFC conductor-side/pin-1 continuity       NO — physical check required",
        "The next electrical step is no longer reverse-engineering the display pinout. It is selecting the production 15-pin connector and migrating `10_DISPLAY_MIPI` / touch support to this already bench-proven module contract.": "M1-ELEC-B1/B2 has now selected and instantiated Amphenol `SFW15R-2STE1LF`, verified its footprint, and migrated the final display path. The next remaining display work is mechanical: actual cable conductor-side/pin-1 continuity, FFC bend keepout, full module Z/mounting evidence, and the new enclosure/mainboard datum set.",
    }
    for old, new in replacements.items():
        if old in text:
            text = text.replace(old, new, 1)
        elif new not in text:
            raise SystemExit(f"B0 doc expected text missing: {old[:60]!r}")
    B0_DOC.write_text(text, encoding="utf-8")


def write_boundary(blockers: list[str]) -> None:
    blocker_lines = "\n".join(f"{idx}. `{gate}`" for idx, gate in enumerate(blockers, 1))
    text = f"""# Pajoniiir-M1 — M1-MECH-A Physical Evidence Boundary v0.2\n\n**Date:** 2026-09-04  \n**Revision:** M1-MECH-A13 / post M1-ELEC-B2 convergence  \n**Status:** Repository-only mechanical convergence complete; layout freeze intentionally blocked by physical/EVT/new-enclosure evidence\n\n## 1. Current final-display authority\n\nThe active final-product display is **EYOYO DSI506 / DYL0023, 5-inch 800×480**. The production host receptacle is **Amphenol SFW15R-2STE1LF**, 15 contacts, 1.0 mm pitch, TOP contact, right-angle/side-entry SMT ZIF. Its project footprint is drawing-verified and instantiated in `10_DISPLAY_MIPI`. The older 30-pin Guition/JC4880 FPC path is historical evidence only.\n\nPreliminary dimensioned-image evidence for the final display rear PCB is **121.109 × 77.193 mm**, with eight visible mounting holes. The outer four image-derived centers imply approximately **111.109 × 67.930 mm** spacing and ~2.5 mm holes. These dimensions are sufficient to reject the old enclosure, but not sufficient for production CAD release without physical caliper data or official CAD.\n\n## 2. Old enclosure decision is closed: REJECTED\n\nThe previous external enclosure was 121.008 × 73.408 mm with a 117.008 × 69.408 mm inner cavity. The final display rear PCB is larger than even the old external Y dimension. `final_display_module.json` therefore records `HARD_FAIL__ENCLOSURE_REDIMENSION_REQUIRED`.\n\nConsequences:\n\n- the old 108.00 × 65.06 mm mainboard feasibility rectangle is **not** final Edge.Cuts authority;\n- the old ±51.3 × ±30.0 mounting candidate is **not** final M1 mounting authority;\n- the old 6.5 mm / 6.0 mm front/rear gross Z-clearance screen is **not** a DSI506 production component-height limit;\n- a new enclosure/mainboard datum set is mandatory.\n\n## 3. Remaining layout blockers ({len(blockers)})\n\n{blocker_lines}\n\nThe blocker count is intentionally unchanged. B2 convergence removed stale assumptions; it did not invent enclosure measurements or EVT data.\n\n## 4. What is already closed\n\n- DSI506 identity and M3-derived signal/bring-up contract\n- production J6 MPN/contact count/pitch/TOP-contact geometry\n- drawing-verified J6 footprint and B2 schematic instantiation\n- legacy 30-pin display electrical/backlight architecture removal\n- D1 TVS production selection\n- J9 factory USB/JTAG pogo fixture footprint\n- optional legacy 3.5 mm line-out removal\n- JLCPCB JLC04161H-7628 4-layer / 1.6 mm stackup\n\n## 5. Physical/EVT package required to continue\n\n1. DSI506 caliper/official CAD package: full XY/Z, all eight mounting-hole centers and hole diameters.\n2. Actual FFC continuity/orientation check proving host pin 1 ↔ module pin 1 and conductor side with the selected TOP-contact receptacle.\n3. FFC approach, insertion and minimum-bend keepout in the proposed enclosure.\n4. New enclosure interior, wall, rib and boss datums in `M1_FRONT_CENTER`.\n5. Exact connector cutouts and full mated plug/cable envelopes for power, USB, RCA, microSD and service buttons.\n6. C3/C8 startup/inrush and worst-case USB-load transient sweep with ESR/ripple/current data.\n\n## 6. Freeze rule\n\n`layout_freeze_allowed` remains **false**. Production Edge.Cuts/routing freeze is allowed only after every `blocks_layout_freeze` gate is closed, the new DSI506-compatible enclosure/mainboard datums are authoritative, C3/C8 are converted from EVT variables to exact packages, and exact 90 Ω USB / 100 Ω MIPI width-spacing values are recorded for the locked JLC stackup.\n"""
    BOUNDARY_DOC.write_text(text, encoding="utf-8")


def write_a13_doc(blockers: list[str]) -> None:
    rows = "\n".join(f"| `{gate}` | OPEN | physical/EVT/new-enclosure evidence |" for gate in blockers)
    text = f"""# Pajoniiir-M1 — M1-MECH-A13 B2 Convergence & Physical Handoff v0.1\n\n**Date:** 2026-09-04  \n**Milestone:** M1-MECH-A13  \n**Result:** REPO/SOFTWARE CLOSURE PASS — production layout freeze remains intentionally blocked\n\n## Purpose\n\nM1-ELEC-B2 changed the final product from the legacy JC4880/Guition 4.3-inch display architecture to the bench-proven EYOYO DSI506 / DYL0023 5-inch module. This checkpoint converges every active mechanical machine contract onto that decision without fabricating dimensions that require physical evidence.\n\n## Current mechanical authority\n\n- Display: EYOYO DSI506 / DYL0023, 5-inch, 800×480.\n- Preliminary rear PCB evidence: 121.109 × 77.193 mm.\n- Visible holes: 8; outer four image-derived centers ~111.109 × 67.930 mm, ~Ø2.5 mm.\n- Host connector: J6 Amphenol SFW15R-2STE1LF, 15P, 1.0 mm, TOP contact, right-angle side-entry SMT ZIF, 2.7 mm housing height.\n- Old JC4880 geometry: preserved under `legacy_guition_display_reference`; not active authority.\n- Old 121.008 × 73.408 × 30 mm enclosure: rejected for DSI506.\n- Old 108 × 65.06 mm mainboard feasibility rectangle and old Z-stack: superseded; no Edge.Cuts authority.\n\n## Active blockers\n\n| Gate | State | Closure class |\n|---|---|---|\n{rows}\n\n**Total: {len(blockers)}.** This is the correct hard boundary without a physical/CAD/EVT evidence package.\n\n## Fail-closed policy\n\nThe repository must reject any attempt to set layout freeze true, add final Edge.Cuts, reactivate the old display/backlight mechanical model, or treat the old enclosure/Z-stack as production authority while these blockers remain.\n\n## Next evidence order\n\nDSI506 physical CAD/caliper + FFC orientation → new enclosure/boss/wall datums → user connector absolute datums and mated envelopes → PCB Z/standoffs and final outline → C3/C8 EVT packages → exact impedance width/spacing → placement/routing freeze.\n"""
    A13_DOC.write_text(text, encoding="utf-8")


def main() -> None:
    display = load(FINAL_DISPLAY)
    conn = load(CONNECTOR)
    mech = load(MECH)
    gates = load(GATES)
    pcb = load(PCB_CONSTRAINTS)
    assert_b2(display, conn)
    blockers = converge_gates(gates)
    converge_final_display(display)
    converge_mech(mech, display, blockers)
    converge_pcb_constraints(pcb, display)
    dump(FINAL_DISPLAY, display)
    dump(GATES, gates)
    dump(MECH, mech)
    dump(PCB_CONSTRAINTS, pcb)
    patch_structural_validator()
    prepend_legacy_notice()
    update_b0_doc()
    write_boundary(blockers)
    write_a13_doc(blockers)
    print("PASS: M1-MECH-A13 B2 convergence applied")
    print(f"PASS: active blockers preserved intentionally: {len(blockers)}")


if __name__ == "__main__":
    main()
