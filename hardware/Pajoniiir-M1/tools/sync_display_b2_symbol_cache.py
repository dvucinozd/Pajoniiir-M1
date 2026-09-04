#!/usr/bin/env python3
"""Synchronize M1-ELEC-B2 cached symbols with their authoritative KiCad libraries.

Run after KiCad 9 is installed. This keeps standard Device/Connector library IDs intact
while replacing the sheet-local cached definitions with byte-equivalent current library
symbols. It also removes the final two audited orphan labels left at the retired touch
sheet's former I2C pins.
"""
from __future__ import annotations

from pathlib import Path
import re

B = Path(__file__).resolve().parents[1]
P10 = B / "10_DISPLAY_MIPI.kicad_sch"
ROOT = B / "Pajoniiir-M1.kicad_sch"
PROJECT_LIB = B / "libraries/Pajoniiir-M1.kicad_sym"
FINAL_ORPHAN_UUIDS = {
    "0b100007-b100-4b10-8b10-000000000008",  # retired touch-sheet DISPLAY_I2C_SDA label
    "0b100008-b100-4b10-8b10-000000000009",  # retired touch-sheet DISPLAY_I2C_SCL label
}


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


def system_symbol_dir() -> Path:
    candidates = [
        Path("/usr/share/kicad/symbols"),
        Path("/usr/local/share/kicad/symbols"),
    ]
    for candidate in candidates:
        if (candidate / "Device.kicad_sym").is_file():
            return candidate
    raise SystemExit("KiCad 9 system symbol directory not found")


def extract_symbol(lib_text: str, name: str) -> str:
    needle = f'(symbol "{name}"'
    start = lib_text.find(needle)
    if start < 0:
        raise SystemExit(f"library symbol not found: {name}")
    block, _ = sexpr_at(lib_text, start)
    return block


def qualify_cached(block: str, source_name: str, qualified_name: str) -> str:
    prefix = f'(symbol "{source_name}"'
    if not block.startswith(prefix):
        raise SystemExit(f"unexpected symbol block header for {source_name}")
    return block.replace(prefix, f'(symbol "{qualified_name}"', 1)


def replace_cached(sheet: str, qualified_name: str, cached_block: str) -> str:
    needle = f'(symbol "{qualified_name}"'
    start = sheet.find(needle)
    if start < 0:
        raise SystemExit(f"cached symbol missing from display sheet: {qualified_name}")
    _, end = sexpr_at(sheet, start)
    return sheet[:start] + cached_block + sheet[end:]


def sync_cached_symbols() -> None:
    symdir = system_symbol_dir()
    device = (symdir / "Device.kicad_sym").read_text()
    connector = (symdir / "Connector.kicad_sym").read_text()
    project = PROJECT_LIB.read_text()
    sheet = P10.read_text()

    authorities = [
        (device, "R_US", "Device:R_US"),
        (device, "C", "Device:C"),
        (connector, "TestPoint", "Connector:TestPoint"),
        (project, "DSI506_15PIN", "Pajoniiir-M1:DSI506_15PIN"),
    ]
    for lib_text, source_name, qualified_name in authorities:
        canonical = extract_symbol(lib_text, source_name)
        cached = qualify_cached(canonical, source_name, qualified_name)
        sheet = replace_cached(sheet, qualified_name, cached)
        print(f"SYNC: {qualified_name}")

    P10.write_text(sheet)


def remove_final_root_orphans() -> None:
    text = ROOT.read_text()
    removals: list[tuple[int, int, str]] = []
    pos = 0
    while True:
        found = text.find("\n  (label", pos)
        if found < 0:
            break
        start = found + 1
        block, end = sexpr_at(text, start)
        um = re.search(r'\(uuid "([0-9a-fA-F-]{36})"\)', block)
        if um and um.group(1) in FINAL_ORPHAN_UUIDS:
            removals.append((start, end, um.group(1)))
        pos = end

    for start, end, uid in reversed(removals):
        print(f"REMOVE ROOT ORPHAN: {uid}")
        text = text[:start] + text[end:]

    for uid in FINAL_ORPHAN_UUIDS:
        if uid in text:
            raise SystemExit(f"retired touch-sheet orphan label still present: {uid}")
    ROOT.write_text(text)


def main() -> None:
    sync_cached_symbols()
    remove_final_root_orphans()
    print("PASS: B2 cached symbol synchronization complete")


if __name__ == "__main__":
    main()

# Standard-CI verification marker for the closed M1-ELEC-B2 state.
