#!/usr/bin/env python3
"""Lightweight structural validator for Pajoniiir-M1 KiCad schematic sources.

This is intentionally NOT a replacement for native KiCad ERC.
It catches hierarchy/source-control regressions without requiring kicad-cli.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE / "Pajoniiir-M1.kicad_sch"
PROJECT = BASE / "Pajoniiir-M1.kicad_pro"
RPW0010A_FOOTPRINT = BASE / "libraries" / "footprints.pretty" / "Texas_RPW0010A_VQFN-HR-10_2x2mm.kicad_mod"
CHILDREN = [
    "01_POWER_INPUT",
    "02_POWER_3V3",
    "03_P4_CORE",
    "04_P4_FLASH_CLOCK_RESET",
    "05_C6_WIFI",
    "06_USB_POWER",
    "07_USB0_STORAGE",
    "08_USB1_FLX4",
    "09_AUDIO_PCM5102A",
    "10_DISPLAY_MIPI",
    "11_TOUCH_GT911",
    "12_MICROSD",
    "13_DEBUG_SERVICE",
    "14_TEST_MONITORING",
    "15_DNP_OPTIONS",
]

MECHANICAL_GATES = BASE / "mechanical_gates.json"
PCB_CONSTRAINTS = BASE / "pcb_constraints.json"
PCB = BASE / "Pajoniiir-M1.kicad_pcb"
MECH_A = BASE / "mech_a.json"

BANNED_LEGACY_VALUE_PATTERNS = (
    "ESP32-S3",
    "ES8311",
    "MAX485",
    "NS4150",
)

def balanced_sexpr(text: str) -> tuple[int, int]:
    depth = 0
    minimum = 0
    in_string = False
    escaped = False
    for ch in text:
        if in_string:
            if escaped:
                escaped = False
                continue
            if ch == "\\":
                escaped = True
                continue
            if ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            minimum = min(minimum, depth)
    return depth, minimum

def sexpr_at(text: str, start: int) -> tuple[str, int]:
    depth = 0
    in_string = False
    escaped = False
    begun = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escaped:
                escaped = False
                continue
            if ch == "\\":
                escaped = True
                continue
            if ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
            continue
        if ch == "(":
            depth += 1
            begun = True
        elif ch == ")":
            depth -= 1
            if begun and depth == 0:
                return text[start : i + 1], i + 1
    raise ValueError(f"unterminated S-expression at offset {start}")

def sheet_blocks(root_text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    pos = 0
    while True:
        pos = root_text.find("  (sheet", pos)
        if pos < 0:
            break
        block, end = sexpr_at(root_text, pos)
        m = re.search(r'\(property "Sheetname" "([^"]+)"', block)
        if m:
            out[m.group(1)] = block
        pos = end
    return out

def top_level_blocks(text: str, token: str):
    """Yield top-level schematic S-expressions with the requested token."""
    needle = f"\n  ({token}"
    pos = 0
    while True:
        found = text.find(needle, pos)
        if found < 0:
            return
        start = found + 1
        block, end = sexpr_at(text, start)
        yield block
        pos = end

def instantiated_symbol_blocks(text: str):
    pos = 0
    while True:
        pos = text.find("  (symbol", pos)
        if pos < 0:
            return
        block, end = sexpr_at(text, pos)
        if '(lib_id "' in block:
            yield block
        pos = end

def main() -> int:
    errors: list[str] = []
    notes: list[str] = []

    if not ROOT.exists():
        print(f"ERROR: missing root schematic: {ROOT}", file=sys.stderr)
        return 2

    root_text = ROOT.read_text(encoding="utf-8")
    child_text: dict[str, str] = {}

    allowed_blank_footprints: set[tuple[str, str]] = set()
    if not MECHANICAL_GATES.exists():
        errors.append(f"missing mechanical gate manifest {MECHANICAL_GATES.name}")
    else:
        try:
            mechanical = json.loads(MECHANICAL_GATES.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{MECHANICAL_GATES.name}: invalid JSON: {exc}")
            mechanical = {}
        gates = mechanical.get("gates", []) if isinstance(mechanical, dict) else []
        for gate in gates:
            if not isinstance(gate, dict):
                errors.append(f"{MECHANICAL_GATES.name}: malformed gate entry {gate!r}")
                continue
            if gate.get("allow_blank_footprint"):
                sheet = gate.get("sheet")
                refdes = gate.get("refdes")
                if not isinstance(sheet, str) or not isinstance(refdes, str):
                    errors.append(
                        f"{MECHANICAL_GATES.name}: blank-footprint gate lacks sheet/refdes: "
                        f"{gate.get('id', '<unknown>')}"
                    )
                else:
                    allowed_blank_footprints.add((sheet, refdes))
        open_blockers = [
            gate.get("id", "<unknown>")
            for gate in gates
            if isinstance(gate, dict)
            and gate.get("blocks_layout_freeze")
            and gate.get("status") != "closed"
        ]
        if mechanical.get("layout_freeze_allowed") and open_blockers:
            errors.append(
                f"{MECHANICAL_GATES.name}: layout_freeze_allowed=true with open blockers: "
                + ", ".join(open_blockers)
            )
        if open_blockers:
            notes.append(
                f"layout freeze remains blocked by {len(open_blockers)} mechanical/sourcing gates"
            )

    if not MECH_A.exists():
        errors.append(f"missing M1-MECH-A authority {MECH_A.name}")
    else:
        try:
            mech_a = json.loads(MECH_A.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{MECH_A.name}: invalid JSON: {exc}")
            mech_a = {}
        if mech_a.get("milestone") != "M1-MECH-A":
            errors.append(f"{MECH_A.name}: milestone must remain M1-MECH-A")
        if mech_a.get("final_board_outline_locked") and any(
            isinstance(gate, dict)
            and gate.get("id") == "PCB_OUTLINE"
            and gate.get("status") != "closed"
            for gate in gates
        ):
            errors.append(
                f"{MECH_A.name}: final_board_outline_locked=true while PCB_OUTLINE gate is open"
            )
        display = mech_a.get("authoritative_display_reference", {})
        bare = display.get("bare_display_front_envelope", {})
        active = display.get("active_display_area", {})
        expected_display = {
            "bare_x": 114.40,
            "bare_y": 66.80,
            "active_x": 93.60,
            "active_y": 56.16,
        }
        rear_shell = display.get("rear_shell_reference", {})
        mount = display.get("legacy_mounting_pattern", {})
        expected_rear_mount = {
            "rear_x": 108.0,
            "rear_y": 65.06,
            "mount_x": 102.6,
            "mount_y": 60.0,
            "hole_diameter": 2.0,
        }
        observed_rear_mount = {
            "rear_x": rear_shell.get("x"),
            "rear_y": rear_shell.get("y"),
            "mount_x": mount.get("center_spacing_x"),
            "mount_y": mount.get("center_spacing_y"),
            "hole_diameter": mount.get("hole_diameter"),
        }
        if observed_rear_mount != expected_rear_mount:
            errors.append(
                f"{MECH_A.name}: rear-shell/mount geometry drift: "
                f"{observed_rear_mount} != {expected_rear_mount}"
            )
        z_stack = mech_a.get("m1_enclosure_baseline", {}).get("z_stack_candidate", {})
        expected_z = {
            "rear_inner_surface_z": 28.0,
            "pcb_rear_face_z": 22.0,
            "pcb_front_face_z": 20.4,
            "gross_front_component_clearance_under_module": 6.5,
            "gross_back_component_clearance_to_rear_inner": 6.0,
        }
        observed_z = {key: z_stack.get(key) for key in expected_z}
        if observed_z != expected_z:
            errors.append(
                f"{MECH_A.name}: candidate Z-stack drift: "
                f"{observed_z} != {expected_z}"
            )
        pcb_candidate = mech_a.get("m1_enclosure_baseline", {}).get(
            "pcb_envelope_candidate", {}
        )
        expected_pcb_candidate = {
            "width": 108.0,
            "height": 65.06,
            "area_mm2": 7026.48,
        }
        observed_pcb_candidate = {
            key: pcb_candidate.get(key) for key in expected_pcb_candidate
        }
        if observed_pcb_candidate != expected_pcb_candidate:
            errors.append(
                f"{MECH_A.name}: M1-MECH-A0 PCB envelope drift: "
                f"{observed_pcb_candidate} != {expected_pcb_candidate}"
            )
        connector_baseline = mech_a.get("connector_cluster_baseline", {})
        surfaces = connector_baseline.get("panel_surfaces", {})
        if surfaces.get("FRONT_Z0", {}).get("usable_for_user_io") is not False:
            errors.append(
                f"{MECH_A.name}: FRONT_Z0 must remain reserved for display/touch"
            )
        expected_cluster_refs = {
            "AUDIO_OUT": {"J4", "J5"},
            "USB_HOST_PAIR": {"J2", "J3"},
            "POWER_IN": {"J1"},
            "REMOVABLE_STORAGE": {"J7"},
            "RECOVERY_BUTTONS": {"SW1", "SW2"},
            "FACTORY_SERVICE": {"J9"},
        }
        observed_cluster_refs = {
            cluster.get("id"): set(cluster.get("refs", []))
            for cluster in connector_baseline.get("clusters", [])
            if isinstance(cluster, dict) and isinstance(cluster.get("id"), str)
        }
        if observed_cluster_refs != expected_cluster_refs:
            errors.append(
                f"{MECH_A.name}: connector cluster membership drift: "
                f"{observed_cluster_refs} != {expected_cluster_refs}"
            )
        height_audit = mech_a.get("mechanical_height_audit", {})
        if height_audit.get("gross_under_display_clearance_mm") != 6.5:
            errors.append(
                f"{MECH_A.name}: under-display gross clearance must remain 6.5 mm "
                "until the Z-stack is intentionally revised"
            )
        expected_height_max = {
            "ESP32-P4NRW32X": 0.90,
            "ESP32-C6-WROOM-1-N4": 3.25,
            "XGL4030-222MEC": 3.10,
            "XGL4030-103MEC": 3.10,
        }
        observed_height_max = {}
        for entry in height_audit.get("verified_critical_fixed_parts", []):
            if isinstance(entry, dict) and isinstance(entry.get("part"), str):
                observed_height_max[entry["part"]] = entry.get("height_max_mm")
        if observed_height_max != expected_height_max:
            errors.append(
                f"{MECH_A.name}: verified critical height baseline drift: "
                f"{observed_height_max} != {expected_height_max}"
            )
        if height_audit.get("production_allowable_component_height_mm") is not None:
            errors.append(
                f"{MECH_A.name}: production allowable height must remain unlocked "
                "until tolerance/safety clearance is defined"
            )
        observed_display = {
            "bare_x": bare.get("x"),
            "bare_y": bare.get("y"),
            "active_x": active.get("x"),
            "active_y": active.get("y"),
        }
        if observed_display != expected_display:
            errors.append(
                f"{MECH_A.name}: manufacturer display geometry drift: "
                f"{observed_display} != {expected_display}"
            )

    if not PCB_CONSTRAINTS.exists():
        errors.append(f"missing PCB constraint authority {PCB_CONSTRAINTS.name}")
    else:
        try:
            pcb_constraints = json.loads(PCB_CONSTRAINTS.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{PCB_CONSTRAINTS.name}: invalid JSON: {exc}")
            pcb_constraints = {}
        if pcb_constraints.get("board_outline_locked") and any(
            isinstance(gate, dict)
            and gate.get("id") == "PCB_OUTLINE"
            and gate.get("status") != "closed"
            for gate in gates
        ):
            errors.append(
                f"{PCB_CONSTRAINTS.name}: board_outline_locked=true while PCB_OUTLINE gate is open"
            )
        if pcb_constraints.get("stackup_locked") and any(
            isinstance(gate, dict)
            and gate.get("id") == "FAB_STACKUP"
            and gate.get("status") != "closed"
            for gate in gates
        ):
            errors.append(
                f"{PCB_CONSTRAINTS.name}: stackup_locked=true while FAB_STACKUP gate is open"
            )
        if pcb_constraints.get("controlled_impedance_locked") and not pcb_constraints.get(
            "stackup_locked"
        ):
            errors.append(
                f"{PCB_CONSTRAINTS.name}: controlled_impedance_locked requires stackup_locked"
            )

    if not PCB.exists():
        errors.append(f"missing PCB shell {PCB.name}")
    else:
        pcb_text = PCB.read_text(encoding="utf-8")
        copper_layers = re.findall(r'\(\d+ "[^"]+\.Cu" (?:signal|power|mixed|jumper)', pcb_text)
        expected_layers = (
            pcb_constraints.get("logical_copper_layers")
            if isinstance(pcb_constraints, dict)
            else None
        )
        if isinstance(expected_layers, int) and len(copper_layers) != expected_layers:
            errors.append(
                f"{PCB.name}: copper layer count={len(copper_layers)}; "
                f"pcb_constraints expects {expected_layers}"
            )
        outline_locked = bool(
            mech_a.get("final_board_outline_locked")
            if isinstance(mech_a, dict)
            else False
        )
        edge_graphics_present = '(layer "Edge.Cuts")' in pcb_text
        if not outline_locked and edge_graphics_present:
            errors.append(
                f"{PCB.name}: Edge.Cuts geometry present while "
                f"{MECH_A.name} final_board_outline_locked=false"
            )
        if outline_locked and not edge_graphics_present:
            errors.append(
                f"{PCB.name}: final board outline is locked but no Edge.Cuts geometry exists"
            )

    # ERC exclusions are allowed only for explicitly documented hard gates.
    # Any extra exclusion, UUID drift, or global severity downgrade is a CI error.
    expected_erc_exclusions = {
        ("label_dangling", "0a000023-a000-4a00-8a00-000000000024"),
        ("label_dangling", "0a00002a-a000-4a00-8a00-00000000002b"),
        ("label_dangling", "0a000031-a000-4a00-8a00-000000000032"),
        ("label_dangling", "0a000038-a000-4a00-8a00-000000000039"),
        ("label_dangling", "0a00003f-a000-4a00-8a00-000000000040"),
        ("label_dangling", "0a000046-a000-4a00-8a00-000000000047"),
    }
    if not PROJECT.exists():
        errors.append(f"missing KiCad project file {PROJECT.name}")
    else:
        try:
            project = json.loads(PROJECT.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{PROJECT.name}: invalid JSON: {exc}")
        else:
            erc = project.get("erc", {})
            exclusions = erc.get("erc_exclusions", [])
            observed_erc_exclusions: set[tuple[str, str]] = set()
            malformed_exclusions: list[str] = []
            for entry in exclusions:
                if (
                    not isinstance(entry, list)
                    or len(entry) != 2
                    or not isinstance(entry[0], str)
                    or not isinstance(entry[1], str)
                ):
                    malformed_exclusions.append(repr(entry))
                    continue
                key, comment = entry
                fields = key.split("|")
                if len(fields) < 4:
                    malformed_exclusions.append(key)
                    continue
                observed_erc_exclusions.add((fields[0], fields[3]))
                if "HARD GATE" not in comment:
                    errors.append(
                        f"{PROJECT.name}: ERC exclusion lacks HARD GATE rationale: "
                        f"{fields[0]} {fields[3]}"
                    )
            if malformed_exclusions:
                errors.append(
                    f"{PROJECT.name}: malformed ERC exclusions: "
                    + "; ".join(malformed_exclusions)
                )
            if len(exclusions) != len(expected_erc_exclusions):
                errors.append(
                    f"{PROJECT.name}: ERC exclusion count={len(exclusions)}; "
                    f"expected exactly {len(expected_erc_exclusions)}"
                )
            missing = expected_erc_exclusions - observed_erc_exclusions
            extra = observed_erc_exclusions - expected_erc_exclusions
            if missing:
                errors.append(
                    f"{PROJECT.name}: missing approved ERC hard-gate exclusions: "
                    + ", ".join(f"{kind}:{uuid}" for kind, uuid in sorted(missing))
                )
            if extra:
                errors.append(
                    f"{PROJECT.name}: unapproved ERC exclusions present: "
                    + ", ".join(f"{kind}:{uuid}" for kind, uuid in sorted(extra))
                )

            severities = erc.get("rule_severities", {})
            for rule in ("label_dangling", "pin_not_driven"):
                # Missing entry means KiCad's built-in default severity. Both
                # rules are error-level by default in KiCad 9; only an explicit
                # non-error override is forbidden here.
                if severities.get(rule, "error") != "error":
                    errors.append(
                        f"{PROJECT.name}: {rule} severity must remain error; "
                        "use only UUID-scoped hard-gate exclusions"
                    )

    for name in CHILDREN:
        path = BASE / f"{name}.kicad_sch"
        if not path.exists():
            errors.append(f"missing child schematic {path.name}")
            continue
        child_text[name] = path.read_text(encoding="utf-8")

    # 1. Parenthesis / source syntax sanity.
    for label, text in [("ROOT", root_text), *child_text.items()]:
        depth, minimum = balanced_sexpr(text)
        if depth != 0 or minimum < 0:
            errors.append(f"{label}: unbalanced S-expression depth={depth}, min={minimum}")

    # 1b. Review-layout invariants. These do not change connectivity, but keep
    # CI-generated schematic PDFs legible enough for human sign-off.
    for name, text in child_text.items():
        for index, block in enumerate(top_level_blocks(text, "text"), start=1):
            if "(justify left)" not in block:
                errors.append(
                    f"{name}: top-level engineering note {index} must be left-justified"
                )
        if name == "03_P4_CORE" and '(paper "A2")' not in text:
            errors.append(
                "03_P4_CORE: paper must remain A2 so U1B clears the title block"
            )

    # 2. Child hierarchical labels must match root sheet pins by name AND shape.
    blocks = sheet_blocks(root_text)

    # Root-level sheet instance metadata points to the parent root instance.
    # Symbols inside each child use /<root_uuid>/<sheet_uuid>, but the sheet
    # object's own instance record uses only /<root_uuid>.
    root_uuid_m = re.search(r'\(uuid "([0-9a-fA-F-]{36})"\)', root_text)
    if not root_uuid_m:
        errors.append("ROOT: schematic UUID missing")
        expected_sheet_parent_path = ""
    else:
        expected_sheet_parent_path = "/" + root_uuid_m.group(1)

    for name, block in blocks.items():
        instance_m = re.search(
            r'\(instances\s+\(project "[^"]+"\s+\(path "([^"]+)"',
            block,
        )
        if not instance_m:
            errors.append(f"{name}: hierarchical sheet instance path missing")
        elif instance_m.group(1) != expected_sheet_parent_path:
            errors.append(
                f"{name}: sheet instance path={instance_m.group(1)}; "
                f"expected parent path={expected_sheet_parent_path}"
            )

        required_sheet_flags = (
            "(exclude_from_sim no)",
            "(in_bom yes)",
            "(on_board yes)",
            "(dnp no)",
        )
        for flag in required_sheet_flags:
            if flag not in block:
                errors.append(f"{name}: KiCad-9 hierarchical sheet flag missing: {flag}")
    for name, text in child_text.items():
        if name not in blocks:
            errors.append(f"{name}: sheet symbol missing in root")
            continue
        child = {
            net: shape
            for net, shape in re.findall(
                r'\(hierarchical_label "([^"]+)"\s+\(shape ([a-z_]+)', text
            )
        }
        parent = {
            net: shape
            for net, shape in re.findall(r'\(pin "([^"]+)" ([a-z_]+)', blocks[name])
        }
        for net, shape in child.items():
            if net not in parent:
                errors.append(f"{name}: child label {net} missing root pin")
            elif parent[net] != shape:
                errors.append(
                    f"{name}: shape mismatch {net}: child={shape}, root={parent[net]}"
                )
        for net in sorted(parent.keys() - child.keys()):
            errors.append(f"{name}: root pin {net} missing child label")

    # Embedded symbol cache keys must match instantiated local library IDs.
    # KiCad resolves lib_id references through the cached lib_symbols map during ERC.
    for name, text in child_text.items():
        lib_start = text.find("(lib_symbols")
        if lib_start < 0:
            errors.append(f"{name}: lib_symbols block missing")
            continue
        lib_block, _ = sexpr_at(text, lib_start)
        outer_cached_symbols: set[str] = set()
        pos = len("(lib_symbols")
        while pos < len(lib_block):
            while pos < len(lib_block) and lib_block[pos].isspace():
                pos += 1
            if pos >= len(lib_block) or lib_block[pos] == ")":
                break
            if lib_block[pos] != "(":
                pos += 1
                continue
            block, end = sexpr_at(lib_block, pos)
            symbol_m = re.match(r'\(symbol "([^"]+)"', block)
            if symbol_m:
                outer_cached_symbols.add(symbol_m.group(1))
            pos = end

        local_ids = {
            lib_id
            for lib_id in re.findall(r'\(lib_id "([^"]+)"\)', text)
            if lib_id.startswith("Pajoniiir-M1:")
        }
        for lib_id in sorted(local_ids):
            if lib_id not in outer_cached_symbols:
                errors.append(
                    f"{name}: local lib_id {lib_id} lacks exact embedded cache key"
                )

    # 3. RefDes uniqueness across hierarchy.
    # Multi-unit symbols legitimately repeat a RefDes on the same sheet/library,
    # but each unit number must be unique. Cross-sheet/library repeats are errors.
    refs: dict[str, list[tuple[str, str, int]]] = defaultdict(list)
    blank_footprints: list[tuple[str, str, str]] = []
    for name, text in child_text.items():
        for block in instantiated_symbol_blocks(text):
            ref_m = re.search(r'\(property "Reference" "([^"]+)"', block)
            val_m = re.search(r'\(property "Value" "([^"]*)"', block)
            fp_m = re.search(r'\(property "Footprint" "([^"]*)"', block)
            on_m = re.search(r'\(on_board (yes|no)\)', block)
            lib_m = re.search(r'\(lib_id "([^"]+)"', block)
            unit_m = re.search(r'\(unit (\d+)\)', block)
            if not ref_m:
                continue
            ref = ref_m.group(1)
            value = val_m.group(1) if val_m else ""
            if not ref.startswith(("#PWR", "#FLG")):
                refs[ref].append(
                    (
                        name,
                        lib_m.group(1) if lib_m else "",
                        int(unit_m.group(1)) if unit_m else 1,
                    )
                )
            if (
                not ref.startswith(("#PWR", "#FLG"))
                and on_m
                and on_m.group(1) == "yes"
                and fp_m
                and fp_m.group(1) == ""
            ):
                blank_footprints.append((name, ref, value))

            # No legacy functional IC blocks in Rev A.
            searchable = " ".join(
                x for x in [value, lib_m.group(1) if lib_m else ""] if x
            ).upper()
            for banned in BANNED_LEGACY_VALUE_PATTERNS:
                if banned.upper() in searchable:
                    errors.append(f"{name}:{ref}: prohibited legacy block {banned}")

    for ref, owners in refs.items():
        sheet_lib = {(sheet, lib_id) for sheet, lib_id, _ in owners}
        units = [unit for _, _, unit in owners]
        if len(sheet_lib) > 1:
            locations = ", ".join(
                f"{sheet}:{lib_id or '<unknown>'}/unit{unit}"
                for sheet, lib_id, unit in owners
            )
            errors.append(f"duplicate RefDes {ref}: {locations}")
        elif len(units) != len(set(units)):
            sheet, lib_id = next(iter(sheet_lib))
            errors.append(
                f"duplicate RefDes/unit {ref} on {sheet}:{lib_id}: "
                + ", ".join(f"unit{unit}" for unit in units)
            )

    for name, ref, value in blank_footprints:
        if (name, ref) not in allowed_blank_footprints:
            errors.append(f"{name}:{ref}: unexpected blank footprint ({value})")

    missing_allowlisted = sorted(
        allowed_blank_footprints
        - {(name, ref) for name, ref, _ in blank_footprints}
    )
    if missing_allowlisted:
        notes.append(
            "allowlist entries no longer blank (review/remove allowlist if intentionally locked): "
            + ", ".join(f"{s}:{r}" for s, r in missing_allowlisted)
        )

    # 4. Root local labels may repeat, but never with different names at same coordinate.
    coords: dict[tuple[str, str], set[str]] = defaultdict(set)
    for name, x, y in re.findall(
        r'\(label "([^"]+)" \(at ([\-\d.]+) ([\-\d.]+) [\-\d.]+\)', root_text
    ):
        coords[(x, y)].add(name)
    for coord, names in coords.items():
        if len(names) > 1:
            errors.append(
                f"root label collision at {coord[0]},{coord[1]}: {', '.join(sorted(names))}"
            )

    # 5. Root sheet symbols must not overlap.
    rects: list[tuple[str, float, float, float, float]] = []
    for name, block in blocks.items():
        at = re.search(r'\(at ([\d.]+) ([\d.]+)\)', block)
        size = re.search(r'\(size ([\d.]+) ([\d.]+)\)', block)
        if at and size:
            rects.append(
                (name, float(at.group(1)), float(at.group(2)), float(size.group(1)), float(size.group(2)))
            )
    for i, a in enumerate(rects):
        for b in rects[i + 1 :]:
            if (
                a[1] < b[1] + b[3]
                and a[1] + a[3] > b[1]
                and a[2] < b[2] + b[4]
                and a[2] + a[4] > b[2]
            ):
                errors.append(f"root sheet overlap: {a[0]} vs {b[0]}")

    # Root sheet pins must lie on their sheet border. A local root label may
    # share a sheet-pin coordinate only when an explicit wire endpoint is present.
    root_wire_endpoints: set[tuple[str, str]] = set()
    for wire_block in re.findall(r'\(wire \(pts \(xy [^)]+\) \(xy [^)]+\)\)[\s\S]*?\(uuid "[^"]+"\)\)', root_text):
        for wx, wy in re.findall(r'\(xy ([\-\d.]+) ([\-\d.]+)\)', wire_block):
            root_wire_endpoints.add((wx, wy))

    root_pin_coords: dict[tuple[str, str], set[str]] = defaultdict(set)
    for sheet_name, block in blocks.items():
        at = re.search(r'\(at ([\-\d.]+) ([\-\d.]+)\)', block)
        size = re.search(r'\(size ([\-\d.]+) ([\-\d.]+)\)', block)
        if not at or not size:
            continue
        sx, sy = float(at.group(1)), float(at.group(2))
        sw, sh = float(size.group(1)), float(size.group(2))
        right, bottom = sx + sw, sy + sh
        for pin_name, px_s, py_s in re.findall(
            r'\(pin "([^"]+)" [a-z_]+ \(at ([\-\d.]+) ([\-\d.]+) [\-\d.]+\)',
            block,
        ):
            px, py = float(px_s), float(py_s)
            tol = 1e-6
            on_border = (
                (abs(px - sx) <= tol and sy - tol <= py <= bottom + tol)
                or (abs(px - right) <= tol and sy - tol <= py <= bottom + tol)
                or (abs(py - sy) <= tol and sx - tol <= px <= right + tol)
                or (abs(py - bottom) <= tol and sx - tol <= px <= right + tol)
            )
            if not on_border:
                errors.append(
                    f"{sheet_name}: root sheet pin {pin_name} is off sheet border at {px_s},{py_s}"
                )
            root_pin_coords[(px_s, py_s)].add(pin_name)

    root_label_seen: set[tuple[str, str, str]] = set()
    for label_name, lx, ly in re.findall(
        r'\(label "([^"]+)" \(at ([\-\d.]+) ([\-\d.]+) [\-\d.]+\)',
        root_text,
    ):
        label_key = (label_name, lx, ly)
        if label_key in root_label_seen:
            errors.append(f"duplicate root label {label_name} at {lx},{ly}")
        root_label_seen.add(label_key)
        if (
            label_name in root_pin_coords.get((lx, ly), set())
            and (lx, ly) not in root_wire_endpoints
        ):
            errors.append(
                f"root label {label_name} sits directly on hierarchical sheet pin at {lx},{ly} "
                "without an explicit wire endpoint"
            )

    # 6. Critical architecture invariants.
    p01 = child_text.get("01_POWER_INPUT", "")
    p14 = child_text.get("14_TEST_MONITORING", "")
    p10 = child_text.get("10_DISPLAY_MIPI", "")

    if 'hierarchical_label "5V_PROTECTED"' not in p01:
        errors.append("01_POWER_INPUT must export 5V_PROTECTED")
    if 'hierarchical_label "5V_PROTECTED"' not in p14:
        errors.append("14_TEST_MONITORING must receive 5V_PROTECTED")
    if 'hierarchical_label "5V_SYS"' not in p14:
        errors.append("14_TEST_MONITORING must generate 5V_SYS after system shunt")
    if re.search(r'\(label "5V_SYS" \(at 65 25 0\)', root_text):
        errors.append("stale pre-shunt 5V_SYS root label detected at 65,25")
    if "R120" not in p14 or "5mR" not in p14:
        errors.append("system 5mR shunt invariant missing")
    if "INA238AIDGSR" not in p14:
        errors.append("INA238 monitoring candidate missing")
    if "MP3202DJ-LF-Z" not in p10:
        errors.append("display backlight MP3202 baseline missing")

    # U7 uses the exact project-local TI RPW0010A HotRod land pattern.
    expected_rpw = "Pajoniiir-M1:Texas_RPW0010A_VQFN-HR-10_2x2mm"
    u7_block = next(
        (
            block
            for block in instantiated_symbol_blocks(p01)
            if '(property "Reference" "U7"' in block
        ),
        "",
    )
    if not u7_block:
        errors.append("01_POWER_INPUT: U7 eFuse instance missing")
    elif f'(property "Footprint" "{expected_rpw}"' not in u7_block:
        errors.append("01_POWER_INPUT: U7 must use exact project-local RPW0010A footprint")

    if not RPW0010A_FOOTPRINT.exists():
        errors.append(f"missing RPW0010A footprint: {RPW0010A_FOOTPRINT}")
    else:
        rpw_text = RPW0010A_FOOTPRINT.read_text(encoding="utf-8")
        depth, minimum = balanced_sexpr(rpw_text)
        if depth != 0 or minimum < 0:
            errors.append(
                f"RPW0010A footprint: unbalanced S-expression depth={depth}, min={minimum}"
            )
        expected_pad_counts = Counter(
            {"1": 2, "2": 1, "3": 1, "4": 2, "5": 1, "6": 1,
             "7": 2, "8": 1, "9": 1, "10": 2}
        )
        observed_pad_counts = Counter(re.findall(r'\(pad "(\d+)" smd', rpw_text))
        if observed_pad_counts != expected_pad_counts:
            errors.append(
                "RPW0010A footprint copper primitive count/pin mapping changed: "
                f"{dict(observed_pad_counts)}"
            )
        if rpw_text.count('"F.Paste"') != 16:
            errors.append("RPW0010A footprint must retain 16 TI stencil paste primitives")
        if rpw_text.count("(solder_mask_margin 0.05)") != 14:
            errors.append("RPW0010A footprint must retain +0.05 mm NSMD mask expansion")
    # M1-ELEC-B2 final DSI506 display contract.
    if '(property "Reference" "J6"' not in p10:
        errors.append("final DSI506 J6 connector missing")
    for token in (
        "DSI506 / DYL0023",
        "SFW15R-2STE1LF",
        "Pajoniiir-M1:Amphenol_SFW15R-2STE1LF",
        "DISPLAY_I2C_SDA",
        "DISPLAY_I2C_SCL",
    ):
        if token not in p10:
            errors.append(f"final DSI506 display contract token missing: {token}")
    active_p10 = "\n".join(instantiated_symbol_blocks(p10))
    for legacy_ref in (
        "U9", "L3", "D4", "C95", "C96", "C97", "C98",
        "R88", "R89", "R90", "R91", "R92", "R93", "R94",
        "TP3", "TP4", "TP5", "TP6",
    ):
        if f'(property "Reference" "{legacy_ref}"' in active_p10:
            errors.append(f"legacy 4.3-inch display component remains instantiated: {legacy_ref}")
    if any(True for _ in instantiated_symbol_blocks(child_text.get("11_TOUCH_GT911", ""))):
        errors.append("retired 11_TOUCH_GT911 sheet must contain no instantiated components")
    if "separate GT911 support retired" not in child_text.get("11_TOUCH_GT911", ""):
        errors.append("retired GT911 sheet migration annotation missing")
    p03 = child_text.get("03_P4_CORE", "")
    for legacy_hier in ("TOUCH_RST", "TOUCH_INT", "LCD_RST", "LCD_TE", "LCD_BL_PWM"):
        if f'hierarchical_label "{legacy_hier}"' in p03:
            errors.append(f"released display GPIO still exported by P4 core: {legacy_hier}")
    if "DISPLAY_I2C_SDA" not in p03 or "DISPLAY_I2C_SCL" not in p03:
        errors.append("P4 final display I2C hierarchy missing")


    # 7. ESP32-P4 multi-unit GPIO connectivity contract.
    p03 = child_text.get("03_P4_CORE", "")
    if p03:
        p4_instances: dict[int, str] = {}
        for block in instantiated_symbol_blocks(p03):
            if '(lib_id "Pajoniiir-M1:ESP32-P4X")' not in block:
                continue
            ref_m = re.search(r'\(property "Reference" "([^"]+)"', block)
            unit_m = re.search(r'\(unit (\d+)\)', block)
            if not ref_m or ref_m.group(1) != "U1" or not unit_m:
                continue
            unit = int(unit_m.group(1))
            if unit in p4_instances:
                errors.append(f"03_P4_CORE: duplicate U1 unit {unit} instance")
            p4_instances[unit] = block

        if set(p4_instances) != {1, 2}:
            errors.append(
                "03_P4_CORE: U1 ESP32-P4X must instantiate exactly units 1 and 2"
            )
        else:
            def embedded_p4_pins(unit: int) -> dict[str, tuple[str, float, float]]:
                names = (
                    (f"ESP32-P4X_{unit}_0", f"ESP32-P4X_{unit}_1")
                )
                out: dict[str, tuple[str, float, float]] = {}
                for symbol_name in names:
                    start = p03.find(f'(symbol "{symbol_name}"')
                    if start < 0:
                        errors.append(
                            f"03_P4_CORE: embedded symbol {symbol_name} missing"
                        )
                        continue
                    symbol_block, _ = sexpr_at(p03, start)
                    pos = 0
                    while True:
                        pin_start = symbol_block.find("(pin ", pos)
                        if pin_start < 0:
                            break
                        pin_block, pin_end = sexpr_at(symbol_block, pin_start)
                        name_m = re.search(r'\(name "([^"]+)"', pin_block)
                        num_m = re.search(r'\(number "([^"]+)"', pin_block)
                        at_m = re.search(
                            r'\(at ([\-\d.]+) ([\-\d.]+) ([\-\d.]+)\)',
                            pin_block,
                        )
                        if name_m and num_m and at_m:
                            out[name_m.group(1)] = (
                                num_m.group(1),
                                float(at_m.group(1)),
                                float(at_m.group(2)),
                            )
                        pos = pin_end
                return out

            unit1_pins = embedded_p4_pins(1)
            unit2_pins = embedded_p4_pins(2)

            instance_data: dict[int, tuple[float, float, set[str]]] = {}
            for unit, block in p4_instances.items():
                at_m = re.search(
                    r'\(at ([\-\d.]+) ([\-\d.]+) ([\-\d.]+)\)', block
                )
                if not at_m:
                    errors.append(f"03_P4_CORE: U1 unit {unit} placement missing")
                    continue
                if abs(float(at_m.group(3))) > 1e-9:
                    errors.append(
                        f"03_P4_CORE: U1 unit {unit} rotation must remain 0 degrees"
                    )
                pin_numbers = set(
                    re.findall(r'\(pin "([^"]+)" \(uuid "[0-9a-fA-F-]{36}"\)\)', block)
                )
                instance_data[unit] = (
                    float(at_m.group(1)),
                    float(at_m.group(2)),
                    pin_numbers,
                )

            expected_u1_numbers = {value[0] for value in unit1_pins.values()}
            expected_u2_numbers = {value[0] for value in unit2_pins.values()}
            if 1 in instance_data and instance_data[1][2] != expected_u1_numbers:
                errors.append(
                    "03_P4_CORE: U1 unit 1 instance pin UUID partition does not match "
                    "embedded unit-1 pins"
                )
            if 2 in instance_data and instance_data[2][2] != expected_u2_numbers:
                errors.append(
                    "03_P4_CORE: U1 unit 2 instance pin UUID partition does not match "
                    "embedded unit-2 pins"
                )
            if 1 in instance_data and 2 in instance_data:
                if instance_data[1][:2] == instance_data[2][:2]:
                    errors.append(
                        "03_P4_CORE: U1 units 1 and 2 must not overlap geometrically"
                    )

            # KiCad symbol-local +Y maps to decreasing schematic-world Y for these
            # unrotated U1 instances; use world_y = instance_y - local_y.
            hlabel_points: dict[str, list[tuple[float, float]]] = defaultdict(list)
            for match in re.finditer(
                r'\(hierarchical_label "([^"]+)".*?'
                r'\(at ([\-\d.]+) ([\-\d.]+) ([\-\d.]+)\)',
                p03,
            ):
                hlabel_points[match.group(1)].append(
                    (float(match.group(2)), float(match.group(3)))
                )

            expected_unit2 = {
                "DISPLAY_I2C_SDA": "GPIO7",
                "DISPLAY_I2C_SCL": "GPIO8",
                "C6_SDIO_D0": "GPIO14",
                "C6_SDIO_D1": "GPIO15",
                "C6_SDIO_D2": "GPIO16/ADC1_CHANNEL0",
                "C6_SDIO_D3": "GPIO17/ADC1_CHANNEL1",
                "C6_SDIO_CLK": "GPIO18/ADC1_CHANNEL2",
                "C6_SDIO_CMD": "GPIO19/ADC1_CHANNEL3",
                "USB0_PWR_EN": "GPIO20/ADC1_CHANNEL4",
                "USB0_FAULT_N": "GPIO21/ADC1_CHANNEL5",
                "USB1_PWR_EN": "GPIO22/ADC1_CHANNEL6",
                "FLASH_CS": "FLASH_CS",
                "FLASH_Q": "FLASH_Q",
                "FLASH_WP": "FLASH_WP",
                "FLASH_HOLD": "FLASH_HOLD",
                "FLASH_CK": "FLASH_CK",
                "FLASH_D": "FLASH_D",
                "DSI_D1_P": "DSI_DATAP1",
                "DSI_D1_N": "DSI_DATAN1",
                "DSI_CLK_N": "DSI_CLKN",
                "DSI_CLK_P": "DSI_CLKP",
                "DSI_D0_P": "DSI_DATAP0",
                "DSI_D0_N": "DSI_DATAN0",
                "USB0_HS_DM": "USB-DM",
                "USB0_HS_DP": "USB-DP",
                "P4_USBJTAG_DM": "GPIO24/USB1P1_N0",
                "P4_USBJTAG_DP": "GPIO25/USB1P1_P0",
                "USB1_FS_DM": "GPIO26/USB1P1_N1",
                "USB1_FS_DP": "GPIO27/USB1P1_P1",
                "USB1_FAULT_N": "GPIO32",
                "BOOT_GPIO35": "GPIO35",
                "BOOT_GPIO36": "GPIO36",
                "UART0_TX": "GPIO37",
                "UART0_RX": "GPIO38",
                "SDMMC_D0": "GPIO39",
                "SDMMC_D1": "GPIO40",
                "SDMMC_D2": "GPIO41",
                "SDMMC_D3": "GPIO42",
                "SDMMC_CLK": "GPIO43",
                "SDMMC_CMD": "GPIO44",
                "SD_PWR_EN": "GPIO45",
                "SD_CARD_DETECT": "GPIO46",
                "DAC_XSMT": "GPIO49/ADC2_CHANNEL0",
                "DAC_BCLK": "GPIO50/ADC2_CHANNEL1",
                "DAC_DATA": "GPIO51/ADC2_CHANNEL2",
                "DAC_LRCK": "GPIO52/ADC2_CHANNEL3",
                "SYS_POWER_ALERT_N": "GPIO53/ADC2_CHANNEL4",
                "C6_RESET": "GPIO54/ADC2_CHANNEL5",
            }

            def close_xy(
                point: tuple[float, float], target: tuple[float, float]
            ) -> bool:
                return (
                    abs(point[0] - target[0]) < 0.001
                    and abs(point[1] - target[1]) < 0.001
                )

            if 2 in instance_data:
                ux, uy, _ = instance_data[2]
                for net, pin_name in expected_unit2.items():
                    pin = unit2_pins.get(pin_name)
                    if not pin:
                        errors.append(
                            f"03_P4_CORE: unit-2 pin definition missing for {pin_name}"
                        )
                        continue
                    target = (ux + pin[1], uy - pin[2])
                    points = hlabel_points.get(net, [])
                    if len(points) != 1 or not close_xy(points[0], target):
                        errors.append(
                            f"03_P4_CORE: {net} is not attached to U1/2 {pin_name} "
                            f"(physical pin {pin[0]})"
                        )

                nc_points = [
                    (float(match.group(1)), float(match.group(2)))
                    for match in re.finditer(
                        r'\(no_connect \(at ([\-\d.]+) ([\-\d.]+)\)', p03
                    )
                ]
                unused_unit2 = {
                    "GPIO0", "GPIO1", "GPIO2",
                    "GPIO3", "GPIO4", "GPIO5", "GPIO6",
                    "GPIO9", "GPIO10", "GPIO11", "GPIO12", "GPIO13",
                    "GPIO23/ADC1_CHANNEL7",
                    "CSI_DATAN0", "CSI_DATAP0", "CSI_CLKP", "CSI_CLKN",
                    "CSI_DATAN1", "CSI_DATAP1", "CSI_REXT",
                    "GPIO28", "GPIO29", "GPIO30", "GPIO31",
                    "GPIO33", "GPIO34", "GPIO47", "GPIO48",
                }
                for pin_name in unused_unit2:
                    pin = unit2_pins.get(pin_name)
                    if not pin:
                        continue
                    target = (ux + pin[1], uy - pin[2])
                    if not any(close_xy(point, target) for point in nc_points):
                        errors.append(
                            f"03_P4_CORE: unused U1/2 {pin_name} lacks explicit NC"
                        )

                dsi_rext = unit2_pins.get("DSI_REXT")
                if dsi_rext:
                    dsi_target = (ux + dsi_rext[1], uy - dsi_rext[2])
                    xy_points = [
                        (float(match.group(1)), float(match.group(2)))
                        for match in re.finditer(
                            r'\(xy ([\-\d.]+) ([\-\d.]+)\)', p03
                        )
                    ]
                    if not any(close_xy(point, dsi_target) for point in xy_points):
                        errors.append(
                            "03_P4_CORE: DSI_REXT physical pin is not wired"
                        )
                if "R24" not in p03 or "4.02k 1%" not in p03:
                    errors.append(
                        "03_P4_CORE: DSI_REXT 4.02k 1% pull-down invariant missing"
                    )

            allowed_unit1 = {
                "XTAL_N": "XTAL_N",
                "XTAL_P": "XTAL_P",
                "CHIP_PU": "CHIP_PU",
            }
            if 1 in instance_data:
                ux, uy, _ = instance_data[1]
                unit1_targets = {
                    pin_name: (ux + pin[1], uy - pin[2])
                    for pin_name, pin in unit1_pins.items()
                }
                for net, points in hlabel_points.items():
                    for point in points:
                        hit = next(
                            (
                                pin_name
                                for pin_name, target in unit1_targets.items()
                                if close_xy(point, target)
                            ),
                            None,
                        )
                        if hit and allowed_unit1.get(net) != hit:
                            errors.append(
                                f"03_P4_CORE: hierarchical net {net} collides with "
                                f"U1/1 {hit}"
                            )
                for net, pin_name in allowed_unit1.items():
                    target = unit1_targets.get(pin_name)
                    points = hlabel_points.get(net, [])
                    if target is None or len(points) != 1 or not close_xy(
                        points[0], target
                    ):
                        errors.append(
                            f"03_P4_CORE: {net} is not attached to U1/1 {pin_name}"
                        )


    print("Pajoniiir-M1 schematic structural validation")
    print(f"  root: {ROOT.name}")
    print(f"  child sheets: {len(child_text)}/{len(CHILDREN)}")
    print(f"  instantiated RefDes: {len(refs)}")
    print(f"  intentional blank footprints observed: {len(blank_footprints)}")

    for note in notes:
        print(f"NOTE: {note}")

    if errors:
        print("\nFAIL:")
        for err in errors:
            print(f"  - {err}")
        print("\nNative KiCad ERC is still required separately.")
        return 1

    print("\nPASS: structural contracts are clean.")
    print("Native KiCad ERC is enforced separately by the KiCad 9 CI workflow.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
