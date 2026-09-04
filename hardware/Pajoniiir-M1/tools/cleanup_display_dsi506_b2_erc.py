#!/usr/bin/env python3
"""Remove the final M1-ELEC-B2 ERC deltas without exclusions.

Actions:
- snap generated 10_DISPLAY_MIPI connection geometry to KiCad's 1.27 mm grid;
- connect the P4_LDO_MIPI_2V5 hierarchical label to TP2;
- remove three root orphan labels proven by the full ERC JSON report;
- register DSI506_15PIN in the project symbol library.

The script is fail-closed and idempotent.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import re
import uuid

B = Path(__file__).resolve().parents[1]
P10 = B / "10_DISPLAY_MIPI.kicad_sch"
ROOT = B / "Pajoniiir-M1.kicad_sch"
SYMLIB = B / "libraries/Pajoniiir-M1.kicad_sym"
GRID = Decimal("1.27")
WIRE_UUID = "62ec64b1-c924-58dd-bb1f-9804ea28dcc2"
ORPHAN_ROOT_UUIDS = {
    "0a10000f-a100-4a10-8a10-000000000010",  # stale 5V_SYS at retired display pin
    "0a10001e-a100-4a10-8a10-00000000001f",  # stale DISPLAY_I2C_SDA label
    "0a10001f-a100-4a10-8a10-000000000020",  # stale DISPLAY_I2C_SCL label
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


def fmt_grid(value: str) -> str:
    d = Decimal(value)
    n = (d / GRID).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    snapped = n * GRID
    out = format(snapped.normalize(), "f")
    return "0" if out in ("-0", "") else out


def snap_display_sheet() -> None:
    text = P10.read_text()

    # Connection-bearing absolute coordinates. This also snaps symbol/text property
    # positions; local symbol graphics already use 1.27/2.54 multiples and remain stable.
    at_re = re.compile(r'\(at\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)(?=\s|\))')
    xy_re = re.compile(r'\(xy\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\)')
    text = at_re.sub(lambda m: f"(at {fmt_grid(m.group(1))} {fmt_grid(m.group(2))}", text)
    text = xy_re.sub(lambda m: f"(xy {fmt_grid(m.group(1))} {fmt_grid(m.group(2))})", text)

    # Resolve post-snap endpoints directly from the source rather than hardcoding them.
    hm = re.search(
        r'\(hierarchical_label "P4_LDO_MIPI_2V5".*?\(at\s+(-?[\d.]+)\s+(-?[\d.]+)',
        text,
        re.S,
    )
    if not hm:
        raise SystemExit("P4_LDO_MIPI_2V5 hierarchical label missing")
    hx, hy = hm.group(1), hm.group(2)

    tp2 = None
    pos = 0
    while True:
        start = text.find("\n  (symbol", pos)
        if start < 0:
            break
        block, end = sexpr_at(text, start + 1)
        if '(property "Reference" "TP2"' in block:
            am = re.search(r'\(at\s+(-?[\d.]+)\s+(-?[\d.]+)', block)
            if not am:
                raise SystemExit("TP2 placement missing")
            tp2 = (am.group(1), am.group(2))
            break
        pos = end
    if tp2 is None:
        raise SystemExit("TP2 symbol missing")
    tx, ty = tp2
    if hy != ty:
        raise SystemExit(f"P4_LDO_MIPI_2V5 and TP2 not horizontally aligned after snap: {hy} vs {ty}")

    if WIRE_UUID not in text:
        wire = (
            f'  (wire (pts (xy {hx} {hy}) (xy {tx} {ty})) '
            f'(stroke (width 0) (type default)) (uuid "{WIRE_UUID}"))\n'
        )
        marker = "  (sheet_instances"
        if marker not in text:
            raise SystemExit("sheet_instances marker missing from display sheet")
        text = text.replace(marker, wire + marker, 1)

    # Strip whitespace introduced by prior one-shot generators.
    text = "\n".join(line.rstrip() for line in text.splitlines()) + "\n"
    P10.write_text(text)


def remove_root_orphans() -> None:
    text = ROOT.read_text()
    removed: set[str] = set()
    pos = 0
    blocks: list[tuple[int, int, str]] = []
    while True:
        found = text.find("\n  (label", pos)
        if found < 0:
            break
        start = found + 1
        block, end = sexpr_at(text, start)
        um = re.search(r'\(uuid "([0-9a-fA-F-]{36})"\)', block)
        if um and um.group(1) in ORPHAN_ROOT_UUIDS:
            blocks.append((start, end, um.group(1)))
            removed.add(um.group(1))
        pos = end

    missing = ORPHAN_ROOT_UUIDS - removed
    if missing:
        # Idempotence: already-removed UUIDs are fine, but if any still occur elsewhere,
        # fail because the source shape differs from the audited report.
        still_present = {u for u in missing if u in text}
        if still_present:
            raise SystemExit(f"audited root orphan UUIDs not found as label blocks: {sorted(still_present)}")

    for start, end, _ in reversed(blocks):
        text = text[:start] + text[end:]
    ROOT.write_text(text)


def ensure_project_symbol() -> None:
    text = SYMLIB.read_text()
    if '(symbol "DSI506_15PIN"' in text:
        return
    if not text.rstrip().endswith(")"):
        raise SystemExit("project symbol library has unexpected outer syntax")

    eff = "(effects (font (size 1.27 1.27)))"
    hide = "(effects (font (size 1.27 1.27)) (hide yes))"
    pins = [
        (1, "GND"), (2, "DSI_D1_N"), (3, "DSI_D1_P"), (4, "GND"),
        (5, "DSI_CLK_N"), (6, "DSI_CLK_P"), (7, "GND"), (8, "DSI_D0_N"),
        (9, "DSI_D0_P"), (10, "GND"), (11, "I2C_SCL"), (12, "I2C_SDA"),
        (13, "GND"), (14, "3V3"), (15, "3V3"),
    ]
    pin_defs = []
    for i, (num, name) in enumerate(pins):
        y = Decimal("17.78") - Decimal(i) * Decimal("2.54")
        pin_defs.append(
            f'''      (pin passive line (at -7.62 {format(y.normalize(), "f")} 0) (length 2.54)
        (name "{name}" {eff})
        (number "{num}" {eff})
      )'''
        )

    symbol = f'''  (symbol "DSI506_15PIN"
    (pin_names (offset 1.016))
    (exclude_from_sim no)
    (in_bom yes)
    (on_board yes)
    (property "Reference" "J" (at 0 22.86 0) {eff})
    (property "Value" "DSI506_15PIN" (at 0 20.32 0) {eff})
    (property "Footprint" "Pajoniiir-M1:Amphenol_SFW15R-2STE1LF" (at 0 0 0) {hide})
    (property "Datasheet" "https://cdn.amphenol-cs.com/media/wysiwyg/files/drawing/10172241.pdf" (at 0 0 0) {hide})
    (property "Description" "Pajoniiir-M1 final DSI506/DYL0023 15-pin Raspberry-Pi-style DSI module interface" (at 0 0 0) {hide})
    (symbol "DSI506_15PIN_0_1"
      (rectangle (start -5.08 19.05) (end 5.08 -19.05)
        (stroke (width 0.254) (type default))
        (fill (type background))
      )
    )
    (symbol "DSI506_15PIN_1_1"
{chr(10).join(pin_defs)}
    )
    (embedded_fonts no)
  )
'''
    stripped = text.rstrip()
    text = stripped[:-1] + symbol + ")\n"
    SYMLIB.write_text(text)


def assert_cleanup() -> None:
    p10 = P10.read_text()
    root = ROOT.read_text()
    symlib = SYMLIB.read_text()
    for uid in ORPHAN_ROOT_UUIDS:
        if uid in root:
            raise SystemExit(f"root orphan UUID still present: {uid}")
    if WIRE_UUID not in p10:
        raise SystemExit("P4_LDO_MIPI_2V5 to TP2 wire missing")
    if '(symbol "DSI506_15PIN"' not in symlib:
        raise SystemExit("project DSI506_15PIN library symbol missing")

    # Every generated absolute connection coordinate must now be on the 1.27 mm grid.
    for pattern in (
        re.compile(r'\(at\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)(?=\s|\))'),
        re.compile(r'\(xy\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\)'),
    ):
        for m in pattern.finditer(p10):
            for raw in (m.group(1), m.group(2)):
                d = Decimal(raw)
                if d % GRID != 0:
                    raise SystemExit(f"display coordinate remains off 1.27 mm grid: {raw}")


def main() -> None:
    snap_display_sheet()
    remove_root_orphans()
    ensure_project_symbol()
    assert_cleanup()
    print("PASS: M1-ELEC-B2 ERC cleanup applied")
    print("PASS: display geometry on 1.27 mm grid; audited root orphans removed; project symbol registered")


if __name__ == "__main__":
    main()
