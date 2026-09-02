#!/usr/bin/env python3
"""Lightweight structural validator for Pajoniiir-M1 KiCad schematic sources.

This is intentionally NOT a replacement for native KiCad ERC.
It catches hierarchy/source-control regressions without requiring kicad-cli.
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE / "Pajoniiir-M1.kicad_sch"
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

# Blank footprints intentionally blocked by mechanics/sourcing, not accidental omissions.
ALLOWED_BLANK_FOOTPRINTS = {
    ("01_POWER_INPUT", "J1"),
    ("01_POWER_INPUT", "C3"),
    ("01_POWER_INPUT", "D1"),
    ("01_POWER_INPUT", "U7"),  # TI RPW0010A exact package; KiCad-9 land pattern still to be formally frozen.
    ("01_POWER_INPUT", "C8"),
    ("04_P4_FLASH_CLOCK_RESET", "SW_RESET"),
    ("04_P4_FLASH_CLOCK_RESET", "SW_BOOT"),
    ("07_USB0_STORAGE", "J_USB0"),
    ("08_USB1_FLX4", "J_USB1"),
    ("09_AUDIO_PCM5102A", "J_RCA_L"),
    ("09_AUDIO_PCM5102A", "J_RCA_R"),
    ("09_AUDIO_PCM5102A", "J_LINE_35"),
    ("12_MICROSD", "J_SD"),
    ("13_DEBUG_SERVICE", "JDBG_USB"),
}

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

    # 2. Child hierarchical labels must match root sheet pins by name AND shape.
    blocks = sheet_blocks(root_text)
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

    # 3. RefDes uniqueness across hierarchy.
    refs: dict[str, list[str]] = defaultdict(list)
    blank_footprints: list[tuple[str, str, str]] = []
    for name, text in child_text.items():
        for block in instantiated_symbol_blocks(text):
            ref_m = re.search(r'\(property "Reference" "([^"]+)"', block)
            val_m = re.search(r'\(property "Value" "([^"]*)"', block)
            fp_m = re.search(r'\(property "Footprint" "([^"]*)"', block)
            on_m = re.search(r'\(on_board (yes|no)\)', block)
            if not ref_m:
                continue
            ref = ref_m.group(1)
            value = val_m.group(1) if val_m else ""
            if not ref.startswith("#PWR"):
                refs[ref].append(name)
            if (
                not ref.startswith("#PWR")
                and on_m
                and on_m.group(1) == "yes"
                and fp_m
                and fp_m.group(1) == ""
            ):
                blank_footprints.append((name, ref, value))

            # No legacy functional IC blocks in Rev A.
            lib_m = re.search(r'\(lib_id "([^"]+)"', block)
            searchable = " ".join(
                x for x in [value, lib_m.group(1) if lib_m else ""] if x
            ).upper()
            for banned in BANNED_LEGACY_VALUE_PATTERNS:
                if banned.upper() in searchable:
                    errors.append(f"{name}:{ref}: prohibited legacy block {banned}")

    for ref, owners in refs.items():
        if len(owners) > 1:
            errors.append(f"duplicate RefDes {ref}: {', '.join(owners)}")

    for name, ref, value in blank_footprints:
        if (name, ref) not in ALLOWED_BLANK_FOOTPRINTS:
            errors.append(f"{name}:{ref}: unexpected blank footprint ({value})")

    missing_allowlisted = sorted(
        ALLOWED_BLANK_FOOTPRINTS
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
    if "R_SYS_SHUNT" not in p14 or "5mR" not in p14:
        errors.append("system 5mR shunt invariant missing")
    if "INA238AIDGSR" not in p14:
        errors.append("INA238 monitoring candidate missing")
    if "MP3202DJ-LF-Z" not in p10:
        errors.append("display backlight MP3202 baseline missing")
    if '(property "Reference" "J_LCD"' in p10:
        errors.append("J_LCD must remain uninstantiated until authoritative FPC gate closes")
    if "PHYSICAL J_LCD IS INTENTIONALLY NOT INSTANTIATED" not in p10:
        errors.append("display FPC hard-gate annotation missing")

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
    print("Native KiCad ERC is still required separately before M1-SCH-A is fully signed off.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
