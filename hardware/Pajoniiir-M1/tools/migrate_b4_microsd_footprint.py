#!/usr/bin/env python3
"""Normalize and lock the Molex 503398-1892 microSD footprint for M1-MECH-B4.

Inputs are intentionally external to the repo source:
- EasyEDA/LCSC C428492 conversion for the exact part land pattern.
- Installed KiCad Connector library for the Micro_SD_Card_Det1 pin contract.

The manufacturer drawing remains the geometric authority.  This helper fails closed
unless the imported land-pattern primitives match the already reviewed C428492/Molex
recommended-layout values and the KiCad symbol contract is DET=9 / SHIELD=10.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
SCH = BASE / "12_MICROSD.kicad_sch"
GATES = BASE / "mechanical_gates.json"
B4 = BASE / "m1_mech_b4_connector_source_lock.json"
OUT = BASE / "libraries/footprints.pretty/Molex_503398-1892.kicad_mod"

MPN = "503398-1892"
FP_ID = "Pajoniiir-M1:Molex_503398-1892"
DATASHEET = "https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/503/503398/5033981892_sd.pdf"

EXPECTED_SIGNAL = {
    1: (-2.42, -6.27, 0.70, 1.10),
    2: (-1.32, -6.27, 0.70, 1.10),
    3: (-0.22, -6.27, 0.70, 1.10),
    4: (0.88, -6.27, 0.70, 1.10),
    5: (1.98, -6.27, 0.70, 1.10),
    6: (3.08, -6.27, 0.70, 1.10),
    7: (4.18, -6.27, 0.70, 1.10),
    8: (5.28, -6.27, 0.70, 1.10),
}
EXPECTED_DET = (0.10, 6.27, 1.05, 0.78)
EXPECTED_COMMON = [
    (-4.17, 6.21, 0.90, 0.90),
    (6.40, -5.77, 0.86, 2.80),
    (-6.26, -6.26, 1.14, 1.83),
    (6.48, 5.00, 0.70, 3.33),
    (-6.48, 5.00, 0.70, 3.33),
]


def close_tuple(a, b, tol=0.011):
    return len(a) == len(b) and all(abs(float(x) - float(y)) <= tol for x, y in zip(a, b))


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


def extract_kicad_symbol(connector_lib: str, name: str) -> str:
    needle = f'(symbol "{name}"'
    start = connector_lib.find(needle)
    if start < 0:
        raise RuntimeError(f"installed KiCad symbol {name} not found")
    block, _ = sexpr_at(connector_lib, start)
    return block


def verify_symbol_contract(connector_lib_path: Path) -> None:
    lib = connector_lib_path.read_text(encoding="utf-8")
    block = extract_kicad_symbol(lib, "Micro_SD_Card_Det1")
    pin_pairs = []
    pos = 0
    while True:
        start = block.find("(pin ", pos)
        if start < 0:
            break
        pin, end = sexpr_at(block, start)
        name_m = re.search(r'\(name "([^"]+)"', pin)
        num_m = re.search(r'\(number "([^"]+)"', pin)
        if name_m and num_m:
            pin_pairs.append((num_m.group(1), name_m.group(1)))
        pos = end
    by_num = {n: name for n, name in pin_pairs}
    if by_num.get("9") != "DET":
        raise RuntimeError(f"KiCad Micro_SD_Card_Det1 pin 9 changed: {by_num.get('9')!r}")
    if by_num.get("10") != "SHIELD":
        raise RuntimeError(f"KiCad Micro_SD_Card_Det1 pin 10 changed: {by_num.get('10')!r}")
    if set(str(i) for i in range(1, 11)) - set(by_num):
        raise RuntimeError(f"KiCad Micro_SD_Card_Det1 missing pins: {by_num}")
    print("PASS: installed KiCad symbol contract is pin9=DET, pin10=SHIELD")


def parse_pads(text: str):
    out = []
    pattern = re.compile(
        r'\(pad\s+"?([^"\s)]+)"?\s+([^\s)]+).*?'
        r'\(at\s+([-+0-9.]+)\s+([-+0-9.]+)(?:\s+[-+0-9.]+)?\).*?'
        r'\(size\s+([-+0-9.]+)\s+([-+0-9.]+)\)',
        re.S,
    )
    for m in pattern.finditer(text):
        out.append((m.group(1), m.group(2), float(m.group(3)), float(m.group(4)), float(m.group(5)), float(m.group(6))))
    return out


def verify_imported_footprint(text: str) -> None:
    pads = parse_pads(text)
    if len(pads) != 14:
        raise RuntimeError(f"C428492 import expected 14 pad records, got {len(pads)}")
    for number, expected in EXPECTED_SIGNAL.items():
        matches = [p for p in pads if p[0] == str(number)]
        if len(matches) != 1:
            raise RuntimeError(f"signal pad {number}: expected one primitive, got {matches}")
        observed = matches[0][2:]
        if not close_tuple(observed, expected):
            raise RuntimeError(f"signal pad {number} geometry drift: {observed} != {expected}")
    det = [p for p in pads if p[0] == "9"]
    if len(det) != 1 or not close_tuple(det[0][2:], EXPECTED_DET):
        raise RuntimeError(f"detect pad geometry drift: {det}")
    common = [p[2:] for p in pads if p[0] in {"10", "11"}]
    if len(common) != 5:
        raise RuntimeError(f"expected 5 common/shell solder areas from pads 10/11, got {common}")
    unmatched = list(common)
    for expected in EXPECTED_COMMON:
        hit = next((x for x in unmatched if close_tuple(x, expected)), None)
        if hit is None:
            raise RuntimeError(f"common/shell pad geometry missing: {expected}; observed={common}")
        unmatched.remove(hit)
    signal_x = [EXPECTED_SIGNAL[i][0] for i in range(1, 9)]
    steps = [round(signal_x[i + 1] - signal_x[i], 3) for i in range(7)]
    if steps != [1.1] * 7:
        raise RuntimeError(f"signal pitch no longer 1.1 mm: {steps}")
    print("PASS: C428492/Molex signal, DET and common/shell land-pattern geometry matches reviewed values")


def normalize_footprint(text: str) -> str:
    # Rename the footprint itself.
    text = re.sub(r'^\(module\s+[^\s]+', '(module Molex_503398-1892', text, count=1)
    text = re.sub(r'^\(footprint\s+"[^"]+"', '(footprint "Molex_503398-1892"', text, count=1)

    # KiCad symbol contract has one SHIELD pin (10).  Molex's detect-lever/common
    # solder area and all shell tabs are common ground/mechanical metal, so all
    # EasyEDA pad-10/pad-11 primitives intentionally collapse onto symbol pin 10.
    text = re.sub(r'\(pad\s+11\s+smd', '(pad 10 smd', text)
    text = re.sub(r'\(pad\s+"11"\s+smd', '(pad "10" smd', text)

    # Remove machine-local converter model reference.  A verified 3D model may be
    # added later; no fake path is preferable to a broken one.
    model_pos = text.find('\n\t(model "/tmp/')
    if model_pos >= 0:
        _, model_end = sexpr_at(text, model_pos + 2)
        text = text[:model_pos] + text[model_end:]

    # Add exact part metadata if the converter did not already provide it.
    if 'property "Manufacturer"' not in text:
        insert_at = text.find('\n\t(fp_text')
        meta = (
            '\n\t(property "Manufacturer" "Molex")'
            '\n\t(property "MPN" "503398-1892")'
            '\n\t(property "LCSC Part" "C428492")'
        )
        if '(property "LCSC Part" "C428492")' in text:
            meta = '\n\t(property "Manufacturer" "Molex")\n\t(property "MPN" "503398-1892")'
        text = text[:insert_at] + meta + text[insert_at:]

    # After normalization: pads 1..8 once, pad9 once, pad10 five times.
    pads = parse_pads(text)
    counts = {n: sum(1 for p in pads if p[0] == str(n)) for n in range(1, 11)}
    expected_counts = {**{i: 1 for i in range(1, 10)}, 10: 5}
    if counts != expected_counts:
        raise RuntimeError(f"normalized footprint pin primitive counts wrong: {counts}")
    if "/tmp/" in text or "11 smd" in text or '"11" smd' in text:
        raise RuntimeError("normalized footprint still contains temp model or unmapped shell pad 11")
    return text


def find_instance(text: str, ref: str) -> tuple[int, int, str]:
    needle = f'(property "Reference" "{ref}"'
    hit = text.find(needle)
    if hit < 0:
        raise RuntimeError(f"{ref}: instance missing")
    candidates = [m.start() for m in re.finditer(r'\n  \(symbol\n', text[:hit])]
    if not candidates:
        raise RuntimeError(f"{ref}: parent symbol block missing")
    start = candidates[-1] + 3
    block, end = sexpr_at(text, start)
    if needle not in block:
        raise RuntimeError(f"{ref}: wrong parent symbol selected")
    return start, end, block


def replace_property(block: str, name: str, value: str) -> str:
    pattern = re.compile(rf'(\(property "{re.escape(name)}" ")[^"]*(")')
    block, count = pattern.subn(lambda m: m.group(1) + value + m.group(2), block, count=1)
    if count != 1:
        raise RuntimeError(f"{name}: replacement count={count}")
    return block


def migrate_schematic() -> None:
    text = SCH.read_text(encoding="utf-8")
    start, end, block = find_instance(text, "J7")
    block = replace_property(block, "Value", MPN)
    block = replace_property(block, "Footprint", FP_ID)
    block = replace_property(block, "Datasheet", DATASHEET)
    text = text[:start] + block + text[end:]
    _, _, check = find_instance(text, "J7")
    for token in (MPN, FP_ID, DATASHEET):
        if token not in check:
            raise RuntimeError(f"J7 missing locked token {token}")
    SCH.write_text(text, encoding="utf-8")


def migrate_authorities() -> None:
    gates = json.loads(GATES.read_text(encoding="utf-8"))
    gate = next((g for g in gates.get("gates", []) if g.get("id") == "J7_MICROSD"), None)
    if not gate:
        raise RuntimeError("J7_MICROSD gate missing")
    gate.update({
        "exact_mpn": MPN,
        "manufacturer": "Molex",
        "exact_footprint": FP_ID,
        "datasheet": DATASHEET,
        "source_status": "MPN_AND_FOOTPRINT_LOCKED_M1-MECH-B4-J7",
        "allow_blank_footprint": False,
        "status": "open",
        "blocks_layout_freeze": True,
        "footprint_status": "CLOSED__MOLEX_DRAWING_CHECKED_PROJECT_FOOTPRINT",
        "closure": "503398-1892 and project footprint are locked/instantiated. Gate remains open for right-wall slot/center, card insertion/ejection access, FFC coexistence and final XY placement."
    })
    gate["required_evidence"] = [
        "right-wall card-slot center and opening geometry",
        "card insertion/ejection and finger access envelope",
        "local courtyard clearance to lower-right M2.5 mounting screw",
        "physical coexistence with the guarded DSI FFC corridor",
        "final enclosure-side card access validation",
    ]
    gates["updated"] = "2026-09-04"
    GATES.write_text(json.dumps(gates, indent=2) + "\n", encoding="utf-8")

    b4 = json.loads(B4.read_text(encoding="utf-8"))
    sel = next((s for s in b4.get("selections", []) if s.get("refdes") == ["J7"]), None)
    if not sel:
        raise RuntimeError("B4 J7 selection missing")
    sel["selection_status"] = "MPN_AND_FOOTPRINT_LOCKED"
    sel["exact_footprint"] = FP_ID
    sel["footprint_source"] = "LCSC/JLCPCB C428492 converted and normalized; geometry checked against Molex sales drawing 5033981892_sd.pdf"
    sel["pin_mapping"] = {
        "1_to_8": "microSD contacts 1..8 unchanged",
        "9": "DET switch signal",
        "10": "SHIELD/common ground: Molex detect-lever common plus four shell solder tabs share KiCad symbol pin 10",
    }
    sel["still_open"] = [
        "right-wall card-slot center and opening geometry",
        "card protrusion/insertion/ejection and finger access envelope",
        "local courtyard versus lower-right mounting screw",
        "physical coexistence with guarded DSI FFC corridor",
    ]
    b4["updated"] = "2026-09-04"
    B4.write_text(json.dumps(b4, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--imported-footprint", type=Path, required=True)
    ap.add_argument("--connector-lib", type=Path, required=True)
    args = ap.parse_args()

    verify_symbol_contract(args.connector_lib)
    raw = args.imported_footprint.read_text(encoding="utf-8")
    verify_imported_footprint(raw)
    OUT.write_text(normalize_footprint(raw), encoding="utf-8")
    migrate_schematic()
    migrate_authorities()
    print(f"PASS: J7 locked to {MPN} / {FP_ID}; panel/card-access gate remains open")


if __name__ == "__main__":
    main()
