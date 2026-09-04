#!/usr/bin/env python3
"""Lock SW1/SW2 to B3U-3000P-B and its exact standard KiCad footprint.

Idempotent, fail-closed one-time migration helper.  Mechanical panel/tool-hole gates remain open.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
SCH = BASE / "04_P4_FLASH_CLOCK_RESET.kicad_sch"
GATES = BASE / "mechanical_gates.json"
B4 = BASE / "m1_mech_b4_connector_source_lock.json"

MPN = "B3U-3000P-B"
FOOTPRINT = "Button_Switch_SMD:SW_SPST_B3U-3000P-B"
DATASHEET = "https://components.omron.com/us-en/system/files/2023-01/datasheet_pdf/A162-E1.pdf"


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
        elif ch == "(":
            depth += 1
            begun = True
        elif ch == ")":
            depth -= 1
            if begun and depth == 0:
                return text[start : i + 1], i + 1
    raise RuntimeError(f"unterminated S-expression at {start}")


def find_instance(text: str, ref: str) -> tuple[int, int, str]:
    needle = f'(property "Reference" "{ref}"'
    hit = text.find(needle)
    if hit < 0:
        raise RuntimeError(f"{ref}: instance not found")
    candidates = [m.start() for m in re.finditer(r'\n  \(symbol\n', text[:hit])]
    if not candidates:
        raise RuntimeError(f"{ref}: parent symbol block not found")
    start = candidates[-1] + 3
    block, end = sexpr_at(text, start)
    if needle not in block:
        raise RuntimeError(f"{ref}: wrong symbol block selected")
    return start, end, block


def replace_property(block: str, name: str, value: str) -> str:
    pattern = re.compile(rf'(\(property "{re.escape(name)}" ")[^"]*(")')
    new, count = pattern.subn(rf'\g<1>{value}\g<2>', block, count=1)
    if count != 1:
        raise RuntimeError(f"property {name}: expected one replacement, got {count}")
    return new


def migrate_schematic() -> None:
    text = SCH.read_text(encoding="utf-8")
    replacements = []
    for ref, function in (("SW1", "RESET"), ("SW2", "BOOT")):
        start, end, block = find_instance(text, ref)
        block = replace_property(block, "Value", MPN)
        block = replace_property(block, "Footprint", FOOTPRINT)
        block = replace_property(block, "Datasheet", DATASHEET)
        # Preserve function in a hidden custom property if it is not already present.
        if '(property "Function"' not in block:
            fp_start = block.find('(property "Footprint"')
            if fp_start < 0:
                raise RuntimeError(f"{ref}: Footprint property not found for Function insertion")
            insert = (
                f'    (property "Function" "{function}" (at 81.915 45.72 0) '
                f'(effects (font (size 1.27 1.27)) (hide yes)))\n    '
            )
            block = block[:fp_start] + insert + block[fp_start:]
        replacements.append((start, end, block))
    for start, end, block in sorted(replacements, reverse=True):
        text = text[:start] + block + text[end:]

    # Source invariants.
    for ref in ("SW1", "SW2"):
        _, _, block = find_instance(text, ref)
        for token in (MPN, FOOTPRINT, DATASHEET):
            if token not in block:
                raise RuntimeError(f"{ref}: missing locked token {token}")
        if '(property "Footprint" ""' in block:
            raise RuntimeError(f"{ref}: footprint remained blank")
    if text.count(f'(property "Footprint" "{FOOTPRINT}"') < 2:
        raise RuntimeError("expected both switch instances to use exact footprint")
    SCH.write_text(text, encoding="utf-8")


def migrate_gates() -> None:
    data = json.loads(GATES.read_text(encoding="utf-8"))
    by_id = {g.get("id"): g for g in data.get("gates", []) if isinstance(g, dict)}
    for gate_id in ("SW1_RESET", "SW2_BOOT"):
        gate = by_id.get(gate_id)
        if not gate:
            raise RuntimeError(f"missing gate {gate_id}")
        gate["exact_mpn"] = MPN
        gate["exact_footprint"] = FOOTPRINT
        gate["datasheet"] = DATASHEET
        gate["source_status"] = "MPN_AND_FOOTPRINT_LOCKED_M1-MECH-B4-SW"
        gate["allow_blank_footprint"] = False
        gate["status"] = "open"
        gate["blocks_layout_freeze"] = True
        gate["footprint_status"] = "CLOSED__STANDARD_KICAD_EXACT_PART_FOOTPRINT"
        gate["closure"] = (
            f"{MPN} and {FOOTPRINT} are locked/instantiated. Gate remains open only for "
            "recessed panel tool-hole center, actuator-to-wall gap, service access and final XY placement."
        )
        gate["required_evidence"] = [
            "separate recessed tool-hole center on the final X_POS media/service wall",
            "actuator-to-wall gap and tool diameter",
            "local courtyard/keepout versus J7, FFC corridor and mounting screw",
            "spacing preventing accidental simultaneous RESET/BOOT actuation",
        ]
    data["updated"] = "2026-09-04"
    GATES.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def migrate_b4() -> None:
    data = json.loads(B4.read_text(encoding="utf-8"))
    target = next(
        (s for s in data.get("selections", []) if s.get("refdes") == ["SW1", "SW2"]),
        None,
    )
    if not target:
        raise RuntimeError("B4 SW1/SW2 selection missing")
    target["selection_status"] = "MPN_AND_FOOTPRINT_LOCKED"
    target["exact_footprint"] = FOOTPRINT
    target["footprint_basis"] = (
        "Official KiCad Button_Switch_SMD library contains exact SW_SPST_B3U-3000P-B footprint; "
        "manufacturer B3U datasheet provides the boss/pad pattern for B3U-3000P-B."
    )
    target["still_open"] = [
        "two separate recessed right-wall tool-hole centers",
        "actuator-to-wall gap and tool diameter",
        "local courtyard/keepout versus J7, FFC corridor and mounting screw",
        "spacing preventing accidental simultaneous actuation",
    ]
    data["updated"] = "2026-09-04"
    B4.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    migrate_schematic()
    migrate_gates()
    migrate_b4()
    print(f"PASS: SW1/SW2 locked to {MPN} / {FOOTPRINT}; panel gates remain open")


if __name__ == "__main__":
    main()
