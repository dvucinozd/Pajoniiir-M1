#!/usr/bin/env python3
"""Narrow M1-ELEC-B2 legacy checks to instantiated symbols, not embedded libraries."""
from pathlib import Path
import re

path = Path(__file__).with_name("migrate_display_dsi506_b2.py")
text = path.read_text()

if "active_body = \"\".join(body)" not in text:
    replacement = '''    active_body = "".join(body)
    for legacy_ref in (
        "U9", "L3", "D4", "C95", "C96", "C97", "C98",
        "R88", "R89", "R90", "R91", "R92", "R93", "R94",
        "TP3", "TP4", "TP5", "TP6",
    ):
        if f'(property "Reference" "{legacy_ref}"' in active_body:
            raise SystemExit(f"legacy 4.3-inch component remains instantiated in sheet10: {legacy_ref}")
    for required in ['''
    text, count = re.subn(
        r'    for forbidden in \[\n.*?    for required in \[',
        lambda _match: replacement,
        text,
        count=1,
        flags=re.S,
    )
    if count != 1:
        raise SystemExit(f"failed to patch sheet10 active-symbol guard: {count}")

# The replacement is raw on purpose. It must write two backslashes into the
# migrator source so the migrator's triple-quoted validator template emits one
# backslash and the final validator sees a normal "\n" string escape.
if 'active_p10 = "\\\\n".join(instantiated_symbol_blocks(p10))' not in text:
    replacement = r'''    active_p10 = "\\n".join(instantiated_symbol_blocks(p10))
    for legacy_ref in (
        "U9", "L3", "D4", "C95", "C96", "C97", "C98",
        "R88", "R89", "R90", "R91", "R92", "R93", "R94",
        "TP3", "TP4", "TP5", "TP6",
    ):
        if f'(property "Reference" "{legacy_ref}"' in active_p10:
            errors.append(f"legacy 4.3-inch display component remains instantiated: {legacy_ref}")
    if any(True for _ in instantiated_symbol_blocks'''
    text, count = re.subn(
        r'    for legacy in \(\n.*?    if any\(True for _ in instantiated_symbol_blocks',
        lambda _match: replacement,
        text,
        count=1,
        flags=re.S,
    )
    if count != 1:
        raise SystemExit(f"failed to patch generated validator active-symbol guard: {count}")

path.write_text(text)
print("PASS: DSI506 B2 migrator guards are scoped to instantiated symbols")
