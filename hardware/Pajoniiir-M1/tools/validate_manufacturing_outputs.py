#!/usr/bin/env python3
"""Validate KiCad-generated manufacturing outputs against Pajoniiir-M1 sources.

This script is intentionally downstream of kicad-cli. It does not synthesize a BOM;
it verifies that the BOM exported by KiCad contains exactly the source components that
are marked in_bom=yes and that Value/Footprint fields survived hierarchy loading.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
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


def allowed_bom_blank_footprints() -> set[str]:
    try:
        data = json.loads(MECHANICAL_GATES.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"cannot read {MECHANICAL_GATES.name}: {exc}")
    allowed: set[str] = set()
    for gate in data.get("gates", []):
        if gate.get("allow_blank_footprint") and gate.get("bom_scope"):
            refdes = gate.get("refdes")
            if not isinstance(refdes, str) or not refdes:
                raise SystemExit(
                    f"{MECHANICAL_GATES.name}: BOM blank gate lacks RefDes: "
                    f"{gate.get('id', '<unknown>')}"
                )
            allowed.add(refdes)
    return allowed


@dataclass(frozen=True)
class Component:
    reference: str
    value: str
    footprint: str
    dnp: bool
    sheet: str


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


def prop(block: str, name: str) -> str:
    match = re.search(rf'\(property "{re.escape(name)}" "([^"]*)"', block)
    return match.group(1) if match else ""


def source_components() -> dict[str, Component]:
    components: dict[str, Component] = {}
    for sheet in CHILDREN:
        path = BASE / f"{sheet}.kicad_sch"
        text = path.read_text(encoding="utf-8")
        for block in instantiated_symbol_blocks(text):
            reference = prop(block, "Reference")
            if not reference or reference.startswith(("#PWR", "#FLG")):
                continue
            if not re.fullmatch(r"[A-Za-z]+[0-9]+", reference):
                raise SystemExit(
                    f"invalid manufacturing RefDes {reference!r} in {sheet}; "
                    "reference must end in a numeric suffix"
                )
            in_bom = re.search(r'\(in_bom (yes|no)\)', block)
            if not in_bom or in_bom.group(1) != "yes":
                continue
            dnp_m = re.search(r'\(dnp (yes|no)\)', block)
            component = Component(
                reference=reference,
                value=prop(block, "Value"),
                footprint=prop(block, "Footprint"),
                dnp=bool(dnp_m and dnp_m.group(1) == "yes"),
                sheet=sheet,
            )
            previous = components.get(reference)
            if previous is None:
                components[reference] = component
            elif (
                previous.value != component.value
                or previous.footprint != component.footprint
                or previous.dnp != component.dnp
            ):
                raise SystemExit(
                    f"source metadata conflict for multi-unit {reference}: "
                    f"{previous} vs {component}"
                )
    return components


def load_kicad_bom(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"Refs", "Value", "Footprint", "Qty", "DNP"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise SystemExit(
                "manufacturing BOM is missing required columns: "
                + ", ".join(sorted(missing))
            )
        rows: dict[str, dict[str, str]] = {}
        for row in reader:
            ref = (row.get("Refs") or "").strip()
            if not ref:
                raise SystemExit("manufacturing BOM contains a row without Refs")
            if ref in rows:
                raise SystemExit(f"manufacturing BOM contains duplicate RefDes row: {ref}")
            rows[ref] = row
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bom_csv", type=Path)
    parser.add_argument("report_md", type=Path)
    args = parser.parse_args()

    expected = source_components()
    observed = load_kicad_bom(args.bom_csv)

    expected_refs = set(expected)
    observed_refs = set(observed)
    missing = sorted(expected_refs - observed_refs)
    extra = sorted(observed_refs - expected_refs)
    mismatches: list[str] = []

    for ref in sorted(expected_refs & observed_refs):
        src = expected[ref]
        row = observed[ref]
        bom_value = (row.get("Value") or "").strip()
        bom_footprint = (row.get("Footprint") or "").strip()
        if bom_value != src.value:
            mismatches.append(
                f"{ref}: Value source={src.value!r} bom={bom_value!r}"
            )
        if bom_footprint != src.footprint:
            mismatches.append(
                f"{ref}: Footprint source={src.footprint!r} bom={bom_footprint!r}"
            )

    blank_refs = {ref for ref, comp in expected.items() if not comp.footprint}
    allowed_blank = allowed_bom_blank_footprints()
    unexpected_blank = sorted(blank_refs - allowed_blank)
    stale_allowlist = sorted(allowed_blank - blank_refs)

    problems: list[str] = []
    if missing:
        problems.append("missing KiCad BOM refs: " + ", ".join(missing))
    if extra:
        problems.append("unexpected KiCad BOM refs: " + ", ".join(extra))
    if mismatches:
        problems.extend(mismatches)
    if unexpected_blank:
        problems.append(
            "unexpected blank footprints in manufacturing BOM source: "
            + ", ".join(unexpected_blank)
        )
    if stale_allowlist:
        problems.append(
            "manufacturing blank-footprint allowlist is stale; now populated: "
            + ", ".join(stale_allowlist)
        )

    dnp_refs = sorted(ref for ref, comp in expected.items() if comp.dnp)
    args.report_md.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Pajoniiir-M1 manufacturing BOM audit",
        "",
        f"- Source `in_bom=yes` RefDes: **{len(expected_refs)}**",
        f"- KiCad BOM RefDes: **{len(observed_refs)}**",
        f"- Source DNP RefDes: **{len(dnp_refs)}**",
        f"- Intentional blank-footprint BOM gates: **{len(blank_refs)}**",
        f"- Result: **{'PASS' if not problems else 'FAIL'}**",
        "",
        "## Intentional blank-footprint gates",
        "",
    ]
    lines.extend(f"- `{ref}`" for ref in sorted(blank_refs))
    lines.extend(["", "## DNP RefDes", ""])
    lines.extend(f"- `{ref}`" for ref in dnp_refs)
    if problems:
        lines.extend(["", "## Problems", ""])
        lines.extend(f"- {problem}" for problem in problems)
    args.report_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(
        "Manufacturing BOM parity: "
        f"source={len(expected_refs)} bom={len(observed_refs)} "
        f"dnp={len(dnp_refs)} blank_gates={len(blank_refs)} "
        f"result={'PASS' if not problems else 'FAIL'}"
    )
    if problems:
        for problem in problems:
            print(f"ERROR: {problem}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
