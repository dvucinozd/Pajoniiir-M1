#!/usr/bin/env python3
"""Finalize deterministic M1-ELEC-B2 outputs before structural/KiCad validation.

This script applies only contract-normalization fixes discovered by full post-migration
structural audits. It is intentionally fail-closed and idempotent.
"""
from __future__ import annotations

from pathlib import Path
import json
import re

B = Path(__file__).resolve().parents[1]
P10 = B / "10_DISPLAY_MIPI.kicad_sch"
P11 = B / "11_TOUCH_GT911.kicad_sch"
P14 = B / "14_TEST_MONITORING.kicad_sch"
VAL = B / "tools/validate_schematic_structure.py"
MIG = B / "tools/migrate_display_dsi506_b2.py"
GATES = B / "mechanical_gates.json"
FD = B / "final_display_module.json"
DC = B / "display_connector_b1.json"


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
    raise ValueError(f"unterminated S-expression at {start}")


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


def left_justify_top_text(path: Path) -> None:
    text = path.read_text()
    needle = "\n  (text "
    pos = 0
    replacements: list[tuple[int, int, str]] = []
    while True:
        found = text.find(needle, pos)
        if found < 0:
            break
        start = found + 1
        block, end = sexpr_at(text, start)
        if "(justify left)" not in block:
            old = "(effects (font (size 1.27 1.27)))"
            if old not in block:
                raise SystemExit(f"{path.name}: top-level note has unexpected effects syntax")
            block = block.replace(
                old,
                "(effects (font (size 1.27 1.27)) (justify left))",
                1,
            )
            replacements.append((start, end, block))
        pos = end
    for start, end, block in reversed(replacements):
        text = text[:start] + block + text[end:]
    path.write_text(text)


def recursive_replace(value, old: str, new: str):
    if isinstance(value, str):
        return value.replace(old, new)
    if isinstance(value, list):
        return [recursive_replace(v, old, new) for v in value]
    if isinstance(value, dict):
        return {k: recursive_replace(v, old, new) for k, v in value.items()}
    return value


def used_connector_refs_excluding_display() -> set[str]:
    refs: set[str] = set()
    for path in sorted(B.glob("[0-9][0-9]_*.kicad_sch")):
        if path == P10:
            continue
        text = path.read_text()
        for block in instantiated_symbol_blocks(text):
            match = re.search(r'\(property "Reference" "(J\d+)"', block)
            if match:
                refs.add(match.group(1))
    return refs


def allocate_display_ref() -> tuple[str, str]:
    p10 = P10.read_text()
    display_block = None
    for block in instantiated_symbol_blocks(p10):
        if "DSI506 / DYL0023 15-pin DSI" in block:
            display_block = block
            break
    if not display_block:
        raise SystemExit("10_DISPLAY_MIPI: DSI506 production connector instance missing")
    match = re.search(r'\(property "Reference" "(J\d+)"', display_block)
    if not match:
        raise SystemExit("10_DISPLAY_MIPI: DSI506 connector RefDes missing")
    old_ref = match.group(1)

    used = used_connector_refs_excluding_display()
    free_ref = next((f"J{i}" for i in range(1, 100) if f"J{i}" not in used), None)
    if free_ref is None:
        raise SystemExit("no free J1..J99 RefDes available for final display connector")

    # Internal connector-side net names intentionally share the RefDes prefix.
    p10 = p10.replace(old_ref, free_ref)
    P10.write_text(p10)

    for path in (GATES, FD, DC):
        data = json.loads(path.read_text())
        data = recursive_replace(data, old_ref, free_ref)
        path.write_text(json.dumps(data, indent=2) + "\n")

    print(f"PASS: display connector RefDes {old_ref} -> {free_ref}; occupied={sorted(used)}")
    return old_ref, free_ref


def normalize_test_monitoring_i2c() -> None:
    text = P14.read_text()
    text = text.replace('"I2C_SDA"', '"DISPLAY_I2C_SDA"')
    text = text.replace('"I2C_SCL"', '"DISPLAY_I2C_SCL"')
    P14.write_text(text)


def normalize_validator(old_ref: str, display_ref: str) -> None:
    text = VAL.read_text()
    # Generated B2 display contract follows the dynamically allocated RefDes.
    text = text.replace(f'final DSI506 {old_ref} connector missing', f'final DSI506 {display_ref} connector missing')
    text = text.replace(f'(property "Reference" "{old_ref}"', f'(property "Reference" "{display_ref}"')
    # Cover earlier failed-run literals if they appear in the generated contract text.
    for stale in ("J8", "J10"):
        if stale != display_ref:
            text = text.replace(f"final DSI506 {stale} connector missing", f"final DSI506 {display_ref} connector missing")

    old = '''            expected_unit2 = {
                "TOUCH_RST": "GPIO3",
                "TOUCH_INT": "GPIO4",
                "LCD_RST": "GPIO5",
                "LCD_TE": "GPIO6",
                "I2C_SDA": "GPIO7",
                "I2C_SCL": "GPIO8",'''
    new = '''            expected_unit2 = {
                "DISPLAY_I2C_SDA": "GPIO7",
                "DISPLAY_I2C_SCL": "GPIO8",'''
    if old in text:
        text = text.replace(old, new, 1)
    elif '"DISPLAY_I2C_SDA": "GPIO7"' not in text:
        raise SystemExit("validator: expected unit-2 mapping preamble not found")

    # GPIO23 is released with the other legacy dedicated panel-control pins.
    text = text.replace('                "LCD_BL_PWM": "GPIO23/ADC1_CHANNEL7",\n', "")

    old = '''                    "GPIO0", "GPIO1", "GPIO2",
                    "GPIO9", "GPIO10", "GPIO11", "GPIO12", "GPIO13",'''
    new = '''                    "GPIO0", "GPIO1", "GPIO2",
                    "GPIO3", "GPIO4", "GPIO5", "GPIO6",
                    "GPIO9", "GPIO10", "GPIO11", "GPIO12", "GPIO13",
                    "GPIO23/ADC1_CHANNEL7",'''
    if old in text:
        text = text.replace(old, new, 1)
    else:
        unused = text.split("unused_unit2 =", 1)[1].split("}", 1)[0]
        for required in ("GPIO3", "GPIO4", "GPIO5", "GPIO6", "GPIO23/ADC1_CHANNEL7"):
            if f'"{required}"' not in unused:
                raise SystemExit(f"validator: released {required} missing from unused unit-2 set")

    VAL.write_text(text)


def normalize_migrator_source_for_reproducibility(old_ref: str, display_ref: str) -> None:
    text = MIG.read_text()
    text = text.replace(old_ref, display_ref)

    # Future migrations must emit left-justified notes directly.
    note_expr = "(exclude_from_sim no) (at 145 {135+i*5} 0) {EFF}"
    note_repl = "(exclude_from_sim no) (at 145 {135+i*5} 0) (effects (font (size 1.27 1.27)) (justify left))"
    text = text.replace(note_expr, note_repl)
    for stub in ("stub1", "stub2", "stub3"):
        text = text.replace(
            f'{{EFF}} (uuid "{{U(\'{stub}\')}}")',
            f'(effects (font (size 1.27 1.27)) (justify left)) (uuid "{{U(\'{stub}\')}}")',
        )
    MIG.write_text(text)


def assert_contracts(display_ref: str) -> None:
    p10 = P10.read_text()
    p11 = P11.read_text()
    p14 = P14.read_text()
    val = VAL.read_text()
    used = used_connector_refs_excluding_display()

    if f'(property "Reference" "{display_ref}"' not in p10:
        raise SystemExit(f"final {display_ref} connector not instantiated")
    if display_ref in used:
        raise SystemExit(f"display RefDes collision remains: {display_ref}")
    if '"I2C_SDA"' in p14 or '"I2C_SCL"' in p14:
        raise SystemExit("14_TEST_MONITORING still exports legacy I2C names")
    for path, text in ((P10, p10), (P11, p11)):
        for match in re.finditer(r'\n  \(text ', text):
            block, _ = sexpr_at(text, match.start() + 1)
            if "(justify left)" not in block:
                raise SystemExit(f"{path.name}: non-left-justified engineering note remains")
    for required in (
        '"DISPLAY_I2C_SDA": "GPIO7"',
        '"DISPLAY_I2C_SCL": "GPIO8"',
        '"GPIO3", "GPIO4", "GPIO5", "GPIO6"',
        '"GPIO23/ADC1_CHANNEL7"',
    ):
        if required not in val:
            raise SystemExit(f"validator missing B2 GPIO contract token: {required}")
    if '"LCD_BL_PWM": "GPIO23/ADC1_CHANNEL7"' in val:
        raise SystemExit("validator still treats released GPIO23 as LCD_BL_PWM")


def main() -> None:
    old_ref, display_ref = allocate_display_ref()
    left_justify_top_text(P10)
    left_justify_top_text(P11)
    normalize_test_monitoring_i2c()
    normalize_validator(old_ref, display_ref)
    normalize_migrator_source_for_reproducibility(old_ref, display_ref)
    assert_contracts(display_ref)
    print("PASS: B2 output finalization complete")
    print(f"PASS: {display_ref} unique; display I2C aligned; GPIO3/4/5/6/23 explicit NC")


if __name__ == "__main__":
    main()
