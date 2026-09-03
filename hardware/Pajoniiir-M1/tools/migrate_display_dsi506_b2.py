#!/usr/bin/env python3
"""One-time audited M1-ELEC-B2 migration from legacy 4.3in display capture to DSI506.

The script is intentionally fail-closed: it checks the pre-B2 source shape, rewrites only the
four affected schematics/contracts, and validates S-expression balance and required/forbidden
tokens before returning success.  It is idempotent after a successful B2 migration.
"""
from __future__ import annotations

from pathlib import Path
import json
import re
import uuid

B = Path(__file__).resolve().parents[1]
P10 = B / "10_DISPLAY_MIPI.kicad_sch"
P11 = B / "11_TOUCH_GT911.kicad_sch"
P03 = B / "03_P4_CORE.kicad_sch"
ROOT = B / "Pajoniiir-M1.kicad_sch"
VAL = B / "tools/validate_schematic_structure.py"
GATES = B / "mechanical_gates.json"
FD = B / "final_display_module.json"
DC = B / "display_connector_b1.json"
NS = uuid.UUID("8dce17f3-2fbe-4a6d-9c87-c154dc9f7a10")
SHEET10_PATH = "/2c8dd352-b7b8-4d9e-8f93-5dd43be2a100/3100000a-6b2a-4a3a-8c91-00000000000a"


def U(key: str) -> str:
    return str(uuid.uuid5(NS, key))


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


def top_blocks(text: str, token: str):
    needle = "\n  (" + token
    pos = 0
    while True:
        found = text.find(needle, pos)
        if found < 0:
            return
        start = found + 1
        block, end = sexpr_at(text, start)
        yield start, end, block
        pos = end


def extract_lib(text: str) -> tuple[str, str, int]:
    start = text.index("  (lib_symbols")
    block, end = sexpr_at(text, start)
    return text[:start], block, end


def balance(text: str) -> tuple[int, int]:
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


EFF = "(effects (font (size 1.27 1.27)))"
HIDE = "(effects (font (size 1.27 1.27)) (hide yes))"


def inst(
    lib: str,
    x: float,
    y: float,
    rot: int,
    ref: str,
    val: str,
    fp: str = "",
    ds: str = "~",
    pins: int = 2,
    dnp: bool = False,
    key: str | None = None,
) -> str:
    key = key or ref
    pin_s = " ".join(
        f'(pin "{i}" (uuid "{U(key + "-pin-" + str(i))}"))' for i in range(1, pins + 1)
    )
    return f'''  (symbol
    (lib_id "{lib}") (at {x} {y} {rot}) (unit 1)
    (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp {'yes' if dnp else 'no'}) (uuid "{U(key+'-sym')}")
    (property "Reference" "{ref}" (at {x+3} {y-2} 0) {EFF})
    (property "Value" "{val}" (at {x+3} {y+2} 0) {EFF})
    (property "Footprint" "{fp}" (at {x} {y} 0) {HIDE})
    (property "Datasheet" "{ds}" (at {x} {y} 0) {HIDE})
    {pin_s}
    (instances (project "Pajoniiir-M1" (path "{SHEET10_PATH}" (reference "{ref}") (unit 1))))
  )
'''


def wire(x1: float, y1: float, x2: float, y2: float, key: str) -> str:
    return f'  (wire (pts (xy {x1} {y1}) (xy {x2} {y2})) (stroke (width 0) (type default)) (uuid "{U(key)}"))\n'


def label(name: str, x: float, y: float, key: str) -> str:
    return f'  (label "{name}" (at {x} {y} 0) {EFF} (uuid "{U(key)}"))\n'


def hier(name: str, shape: str, x: float, y: float, key: str) -> str:
    return f'  (hierarchical_label "{name}" (shape {shape}) (at {x} {y} 0) {EFF} (uuid "{U(key)}"))\n'


def gnd(x: float, y: float, key: str) -> str:
    return inst("power:GND", x, y, 0, f"#PWRB2{key}", "GND", "", "", 1, False, "gnd-" + key)


def tp(ref: str, val: str, x: float, y: float, key: str) -> str:
    return inst(
        "Connector:TestPoint",
        x,
        y,
        0,
        ref,
        val,
        "TestPoint:TestPoint_Pad_D1.5mm",
        "~",
        1,
        False,
        key,
    )


def rebuild_sheet10() -> None:
    old = P10.read_text()
    if 'rev "B / M1-ELEC-B2"' in old and '(property "Reference" "J6"' in old:
        print("sheet10 already migrated")
        return
    if "MP3202DJ-LF-Z" not in old or "SOFNG 0.5TBQP-30P-1" not in old:
        raise SystemExit("sheet10 is neither expected legacy capture nor completed B2 capture")

    prefix, lib, _ = extract_lib(old)
    prefix = re.sub(r'\(title "[^"]*"\)', '(title "Pajoniiir-M1 Rev A — 10_DISPLAY_DSI506")', prefix, count=1)
    prefix = re.sub(r'\(date "[^"]*"\)', '(date "2026-09-04")', prefix, count=1)
    prefix = re.sub(r'\(rev "[^"]*"\)', '(rev "B / M1-ELEC-B2")', prefix, count=1)
    prefix = re.sub(
        r'\(comment 1 "[^"]*"\)',
        '(comment 1 "DSI506/DYL0023 5in module; M3 bench-proven 15-pin interface")',
        prefix,
        count=1,
    )
    prefix = re.sub(
        r'\(comment 2 "[^"]*"\)',
        '(comment 2 "1-lane firmware baseline; route both DSI data lanes; module handles touch/backlight")',
        prefix,
        count=1,
    )

    pin_inventory = [
        (1, "GND"),
        (2, "DSI_D1_N"),
        (3, "DSI_D1_P"),
        (4, "GND"),
        (5, "DSI_CLK_N"),
        (6, "DSI_CLK_P"),
        (7, "GND"),
        (8, "DSI_D0_N"),
        (9, "DSI_D0_P"),
        (10, "GND"),
        (11, "I2C_SCL"),
        (12, "I2C_SDA"),
        (13, "GND"),
        (14, "3V3"),
        (15, "3V3"),
    ]
    pin_defs = []
    for i, (num, name) in enumerate(pin_inventory):
        ly = 17.78 - i * 2.54
        pin_defs.append(
            f'''        (pin passive line (at -7.62 {ly:.2f} 0) (length 2.54)
          (name "{name}" {EFF}) (number "{num}" {EFF}))'''
        )
    custom = f'''
    (symbol "Pajoniiir-M1:DSI506_15PIN"
      (pin_names (offset 1.016))
      (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "J" (at 0 22.86 0) {EFF})
      (property "Value" "DSI506_15PIN" (at 0 20.32 0) {EFF})
      (property "Footprint" "Pajoniiir-M1:Amphenol_SFW15R-2STE1LF" (at 0 0 0) {HIDE})
      (property "Datasheet" "https://cdn.amphenol-cs.com/media/wysiwyg/files/drawing/10172241.pdf" (at 0 0 0) {HIDE})
      (symbol "DSI506_15PIN_0_1"
        (rectangle (start -5.08 19.05) (end 5.08 -19.05) (stroke (width 0.254) (type default)) (fill (type background)))
      )
      (symbol "DSI506_15PIN_1_1"
{chr(10).join(pin_defs)}
      )
      (embedded_fonts no)
    )
'''
    lib = lib[:-1] + custom + "  )"

    body: list[str] = []
    body.append(hier("3V3_SYS", "input", 30, 30, "h-3v3"))
    body.append(inst("Device:R_US", 60, 30, 90, "FB3", "0R / ferrite option", "Resistor_SMD:R_0603_1608Metric", "~", 2, False, "FB3"))
    body.append(wire(30, 30, 56.19, 30, "w-3v3-in"))
    body.append(wire(63.81, 30, 120, 30, "w-3v3-out"))
    body.append(label("3V3_DISPLAY_MODULE", 90, 30, "l-3v3-module"))
    for ref, x, val, fp in [
        ("C93", 75, "100nF", "Capacitor_SMD:C_0603_1608Metric"),
        ("C94", 90, "10uF", "Capacitor_SMD:C_0805_2012Metric"),
    ]:
        cy = 33.81
        body.append(inst("Device:C", x, cy, 0, ref, val, fp, "~", 2, False, ref))
        body.append(label("3V3_DISPLAY_MODULE", x, 30, "l-" + ref + "-v"))
        body.append(gnd(x, 37.62, ref))
    body.append(tp("TP1", "3V3_DISPLAY_MODULE", 120, 30, "TP1"))
    body.append(label("3V3_DISPLAY_MODULE", 120, 30, "l-tp1"))

    body.append(hier("P4_LDO_MIPI_2V5", "input", 30, 40, "h-mipi25"))
    body.append(tp("TP2", "P4_LDO_MIPI_2V5", 120, 40, "TP2"))
    body.append(label("P4_LDO_MIPI_2V5", 120, 40, "l-tp2"))

    dsi = [
        ("DSI_D0_P", "R82", "J6_DSI_D0_P", 50),
        ("DSI_D0_N", "R83", "J6_DSI_D0_N", 58),
        ("DSI_D1_P", "R84", "J6_DSI_D1_P", 66),
        ("DSI_D1_N", "R85", "J6_DSI_D1_N", 74),
        ("DSI_CLK_P", "R86", "J6_DSI_CLK_P", 82),
        ("DSI_CLK_N", "R87", "J6_DSI_CLK_N", 90),
    ]
    for net, ref, out, y in dsi:
        body.append(hier(net, "bidirectional", 30, y, "h-" + net))
        body.append(inst("Device:R_US", 65, y, 90, ref, "0R", "Resistor_SMD:R_0201_0603Metric", "~", 2, False, ref))
        body.append(wire(30, y, 61.19, y, "w-" + ref + "-in"))
        body.append(wire(68.81, y, 100, y, "w-" + ref + "-out"))
        body.append(label(out, 100, y, "l-" + out))

    for net, ref, out, y in [
        ("DISPLAY_I2C_SDA", "R95", "J6_I2C_SDA", 108),
        ("DISPLAY_I2C_SCL", "R96", "J6_I2C_SCL", 118),
    ]:
        body.append(hier(net, "bidirectional", 30, y, "h-" + net))
        body.append(inst("Device:R_US", 65, y, 90, ref, "22R", "Resistor_SMD:R_0402_1005Metric", "~", 2, False, ref))
        body.append(wire(30, y, 61.19, y, "w-" + ref + "-in"))
        body.append(wire(68.81, y, 100, y, "w-" + ref + "-out"))
        body.append(label(out, 100, y, "l-" + out))

    for ref, x, y, out, dnp in [
        ("R97", 110, 104.19, "J6_I2C_SDA", False),
        ("R99", 120, 104.19, "J6_I2C_SDA", True),
        ("R98", 110, 114.19, "J6_I2C_SCL", False),
        ("R100", 120, 114.19, "J6_I2C_SCL", True),
    ]:
        body.append(
            inst(
                "Device:R_US",
                x,
                y,
                0,
                ref,
                "4.7k DNP" if dnp else "4.7k",
                "Resistor_SMD:R_0603_1608Metric",
                "~",
                2,
                dnp,
                ref,
            )
        )
        body.append(label("3V3_DISPLAY_MODULE", x, y - 3.81, "l-" + ref + "-v"))
        body.append(label(out, x, y + 3.81, "l-" + ref + "-bus"))
    body.append(tp("TP9", "J6_I2C_SDA", 135, 108, "TP9"))
    body.append(label("J6_I2C_SDA", 135, 108, "l-tp9"))
    body.append(tp("TP10", "J6_I2C_SCL", 145, 118, "TP10"))
    body.append(label("J6_I2C_SCL", 145, 118, "l-tp10"))

    body.append(
        inst(
            "Pajoniiir-M1:DSI506_15PIN",
            210,
            90,
            0,
            "J6",
            "DSI506 / DYL0023 15-pin DSI",
            "Pajoniiir-M1:Amphenol_SFW15R-2STE1LF",
            "https://cdn.amphenol-cs.com/media/wysiwyg/files/drawing/10172241.pdf",
            15,
            False,
            "J6",
        )
    )
    jmap = {
        1: "GND",
        2: "J6_DSI_D1_N",
        3: "J6_DSI_D1_P",
        4: "GND",
        5: "J6_DSI_CLK_N",
        6: "J6_DSI_CLK_P",
        7: "GND",
        8: "J6_DSI_D0_N",
        9: "J6_DSI_D0_P",
        10: "GND",
        11: "J6_I2C_SCL",
        12: "J6_I2C_SDA",
        13: "GND",
        14: "3V3_DISPLAY_MODULE",
        15: "3V3_DISPLAY_MODULE",
    }
    for i in range(1, 16):
        ly = 17.78 - (i - 1) * 2.54
        gx = 202.38
        gy = 90 - ly
        net = jmap[i]
        body.append(gnd(gx, gy, "j8-" + str(i)) if net == "GND" else label(net, gx, gy, "j8-pin-" + str(i)))

    notes = [
        "FINAL DISPLAY: EYOYO DSI506 / DYL0023, 5in 800x480; interface bench-accepted in Pajoniiir-M3.",
        "J6 = Amphenol SFW15R-2STE1LF, 15P 1.0mm TOP contact. Pin map follows M3 accepted J2: GND/D1/CLK/D0/I2C/3V3.",
        "Backlight/panel power are controlled inside the module over I2C 0x45; touch is 0x38 at 100kHz. No MP3202, LEDA/LEDK, LCD_RST, TE or external BL PWM on M1.",
        "Initial firmware: 1 data lane @ 800Mbps, RGB888, 27.777MHz, H 59/2/45, V 109/2/22; both physical data lanes are routed.",
        "DSI routing target 100R differential; MIPI DPHY 2.5V LDO and 4.02k DSI_REXT remain in 03_P4_CORE.",
    ]
    for i, text in enumerate(notes):
        body.append(
            f'  (text "{text}" (exclude_from_sim no) (at 145 {135+i*5} 0) (effects (font (size 1.27 1.27)) (justify left)) (uuid "{U("note-"+str(i))}"))\n'
        )
    body.append('  (sheet_instances (path "/" (page "11")))\n  (embedded_fonts no)\n)\n')

    new = prefix + lib + "\n" + "".join(body)
    if balance(new) != (0, 0):
        raise SystemExit(f"10 balance {balance(new)}")
    active_body = "".join(body)
    for legacy_ref in (
        "U9", "L3", "D4", "C95", "C96", "C97", "C98",
        "R88", "R89", "R90", "R91", "R92", "R93", "R94",
        "TP3", "TP4", "TP5", "TP6",
    ):
        if f'(property "Reference" "{legacy_ref}"' in active_body:
            raise SystemExit(f"legacy 4.3-inch component remains instantiated in sheet10: {legacy_ref}")
    for required in [
        '(property "Reference" "J6"',
        "SFW15R-2STE1LF",
        "DSI506 / DYL0023",
        "DISPLAY_I2C_SDA",
        "DISPLAY_I2C_SCL",
    ]:
        if required not in new:
            raise SystemExit(f"missing new display token {required}")
    P10.write_text(new)


def retire_sheet11() -> None:
    old = P11.read_text()
    if 'rev "B / M1-ELEC-B2"' in old and "separate GT911 support retired" in old:
        print("sheet11 already retired")
        return
    if '(property "Reference" "R101"' not in old:
        raise SystemExit("sheet11 is not expected legacy touch capture")
    prefix, lib, _ = extract_lib(old)
    prefix = re.sub(r'\(title "[^"]*"\)', '(title "Pajoniiir-M1 Rev A — 11_TOUCH_GT911 RETIRED")', prefix, count=1)
    prefix = re.sub(r'\(date "[^"]*"\)', '(date "2026-09-04")', prefix, count=1)
    prefix = re.sub(r'\(rev "[^"]*"\)', '(rev "B / M1-ELEC-B2")', prefix, count=1)
    prefix = re.sub(
        r'\(comment 1 "[^"]*"\)',
        '(comment 1 "Retired: final DSI506 touch is integrated through J6 shared I2C")',
        prefix,
        count=1,
    )
    prefix = re.sub(
        r'\(comment 2 "[^"]*"\)',
        '(comment 2 "No GT911 RST/INT/address-select network on final M1")',
        prefix,
        count=1,
    )
    stub = f'''
  (text "M1-ELEC-B2: separate GT911 support retired. Final DSI506/DYL0023 touch is module-integrated at I2C 0x38." (exclude_from_sim no) (at 35 55 0) (effects (font (size 1.27 1.27)) (justify left)) (uuid "{U('stub1')}"))
  (text "GPIO7/8 I2C conditioning, pull-ups and test points moved into 10_DISPLAY_MIPI next to final J6 connector." (exclude_from_sim no) (at 35 60 0) (effects (font (size 1.27 1.27)) (justify left)) (uuid "{U('stub2')}"))
  (text "GPIO3 TOUCH_RST and GPIO4 TOUCH_INT are released/NC in final M1 architecture." (exclude_from_sim no) (at 35 65 0) (effects (font (size 1.27 1.27)) (justify left)) (uuid "{U('stub3')}"))
  (sheet_instances (path "/" (page "12")))
  (embedded_fonts no)
)
'''
    new = prefix + lib + stub
    if balance(new) != (0, 0):
        raise SystemExit(f"11 balance {balance(new)}")
    for token in [
        '(property "Reference" "R95"',
        '(property "Reference" "R101"',
        '(property "Reference" "TP11"',
        "hierarchical_label",
    ]:
        if token in new:
            raise SystemExit(f"active legacy touch content remains: {token}")
    P11.write_text(new)


def migrate_p4() -> None:
    text = P03.read_text()
    if 'hierarchical_label "DISPLAY_I2C_SDA"' in text and 'hierarchical_label "TOUCH_RST"' not in text:
        print("P4 already migrated")
        return
    text = text.replace('"I2C_SDA"', '"DISPLAY_I2C_SDA"').replace('"I2C_SCL"', '"DISPLAY_I2C_SCL"')
    release = {"TOUCH_RST", "TOUCH_INT", "LCD_RST", "LCD_TE", "LCD_BL_PWM"}
    replacements = []
    for start, end, block in list(top_blocks(text, "hierarchical_label")):
        match = re.search(
            r'\(hierarchical_label "([^"]+)".*?\(at\s+([-0-9.]+)\s+([-0-9.]+)',
            block,
            re.S,
        )
        if match and match.group(1) in release:
            name, x, y = match.group(1), match.group(2), match.group(3)
            uid = re.search(r'\(uuid "([^"]+)"\)', block).group(1)
            replacements.append((start, end, f'  (no_connect (at {x} {y}) (uuid "{uid}"))', name))
    if len(replacements) != 5:
        raise SystemExit(f"expected five released P4 labels, got {[(x[3]) for x in replacements]}")
    for start, end, new, _ in reversed(replacements):
        text = text[:start] + new + text[end:]
    if balance(text) != (0, 0):
        raise SystemExit(f"03 balance {balance(text)}")
    for name in release:
        if f'hierarchical_label "{name}"' in text:
            raise SystemExit(f"P4 old hierarchy remains {name}")
    P03.write_text(text)


def migrate_root() -> None:
    root = ROOT.read_text()
    if '(pin "DISPLAY_I2C_SDA"' in root and '(pin "TOUCH_RST"' not in root and '(pin "LCD_BL_PWM"' not in root:
        print("root already migrated")
        return
    root = root.replace('"I2C_SDA"', '"DISPLAY_I2C_SDA"').replace('"I2C_SCL"', '"DISPLAY_I2C_SCL"')
    sheets = {}
    for start, end, block in top_blocks(root, "sheet"):
        match = re.search(r'\(property "Sheetname" "([^"]+)"', block)
        if match:
            sheets[match.group(1)] = (start, end, block)
    for name in ["03_P4_CORE", "10_DISPLAY_MIPI", "11_TOUCH_GT911"]:
        if name not in sheets:
            raise SystemExit(f"missing root sheet {name}")

    def pin_coords(block: str, names: set[str] | None = None):
        out = []
        for match in re.finditer(r'\(pin "([^"]+)"[^\n]*?\(at\s+([-0-9.]+)\s+([-0-9.]+)', block):
            if names is None or match.group(1) in names:
                out.append((match.group(1), float(match.group(2)), float(match.group(3))))
        return out

    prune_coords: set[tuple[float, float]] = set()
    p4s, p4e, p4b = sheets["03_P4_CORE"]
    obsolete = {"TOUCH_RST", "TOUCH_INT", "LCD_RST", "LCD_TE", "LCD_BL_PWM"}
    prune_coords.update((x, y) for _, x, y in pin_coords(p4b, obsolete))
    p4b = re.sub(r'\n    \(pin "(?:TOUCH_RST|TOUCH_INT|LCD_RST|LCD_TE|LCD_BL_PWM)"[^\n]+\)', "", p4b)

    d10s, d10e, d10b = sheets["10_DISPLAY_MIPI"]
    prune_coords.update((x, y) for _, x, y in pin_coords(d10b, {"5V_SYS", "3V3_LCD", "LCD_BL_PWM"}))
    d10b = re.sub(r'\n    \(pin "(?:5V_SYS|3V3_LCD|LCD_BL_PWM)"[^\n]+\)', "", d10b)
    d10b = d10b.replace('(pin "LCD_RST" input', '(pin "DISPLAY_I2C_SDA" bidirectional')
    d10b = d10b.replace('(pin "LCD_TE" bidirectional', '(pin "DISPLAY_I2C_SCL" bidirectional')

    t11s, t11e, t11b = sheets["11_TOUCH_GT911"]
    prune_coords.update((x, y) for _, x, y in pin_coords(t11b, None))
    t11b = re.sub(r'\n    \(pin "[^"]+"[^\n]+\)', "", t11b)

    for start, end, block in sorted(
        [(p4s, p4e, p4b), (d10s, d10e, d10b), (t11s, t11e, t11b)], reverse=True
    ):
        root = root[:start] + block + root[end:]

    kill_names = {"TOUCH_RST", "TOUCH_INT", "LCD_BL_PWM", "3V3_LCD"}
    removals = []
    for start, end, block in top_blocks(root, "label"):
        match = re.search(r'\(label "([^"]+)".*?\(at\s+([-0-9.]+)\s+([-0-9.]+)', block, re.S)
        if match and (
            match.group(1) in kill_names
            or (float(match.group(2)), float(match.group(3))) in prune_coords
        ):
            removals.append((start, end))
    for start, end, block in top_blocks(root, "wire"):
        points = [(float(x), float(y)) for x, y in re.findall(r'\(xy\s+([-0-9.]+)\s+([-0-9.]+)\)', block)]
        if any(point in prune_coords for point in points):
            removals.append((start, end))
    for start, end in sorted(set(removals), reverse=True):
        root = root[:start] + root[end:]

    root = root.replace('(label "LCD_RST"', '(label "DISPLAY_I2C_SDA"')
    root = root.replace('(label "LCD_TE"', '(label "DISPLAY_I2C_SCL"')
    if balance(root) != (0, 0):
        raise SystemExit(f"root balance {balance(root)}")
    for name in obsolete:
        if f'(pin "{name}"' in root or f'(label "{name}"' in root:
            raise SystemExit(f"root legacy control remains {name}")
    if root.count("DISPLAY_I2C_SDA") < 2 or root.count("DISPLAY_I2C_SCL") < 2:
        raise SystemExit("root display I2C continuity markers missing")
    ROOT.write_text(root)


def migrate_authorities() -> None:
    gates = json.loads(GATES.read_text())
    gate = next(g for g in gates["gates"] if g["id"] == "J_LCD_DISPLAY_FPC")
    gate.update(
        {
            "sheet": "10_DISPLAY_MIPI",
            "refdes": "J6",
            "category": "display_module_connector_mechanical",
            "status": "open",
            "allow_blank_footprint": False,
            "bom_scope": True,
            "blocks_layout_freeze": True,
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
            "required_evidence": [
                "actual DSI506 FFC conductor-side / host-to-module pin-1 continuity check",
                "FFC bend/insertion keepout in final enclosure",
                "absolute J6 XY/Z placement relative to final display and custom mainboard",
            ],
            "closure": "Electrical connector, MPN and footprint are locked/instantiated. Gate remains open only for actual cable orientation and final enclosure placement evidence.",
        }
    )
    gates["updated"] = "2026-09-04"
    GATES.write_text(json.dumps(gates, indent=2) + "\n")

    fd = json.loads(FD.read_text())
    if "M1-ELEC-B2" not in fd["milestones"]:
        fd["milestones"].append("M1-ELEC-B2")
    fd["status"] = "final_DSI506_selected__M3_pinout_locked__J6_schematic_and_footprint_instantiated__cable_and_enclosure_open"
    fd["freeze"]["production_connector_mpn_locked"] = True
    fd["freeze"]["production_connector_contact_side_locked"] = True
    fd["freeze"]["production_connector_footprint_locked"] = True
    fd["freeze"]["schematic_migrated_to_final_display"] = True
    fd["updated"] = "2026-09-04"
    FD.write_text(json.dumps(fd, indent=2) + "\n")

    dc = json.loads(DC.read_text())
    dc["footprint"]["status"] = "DRAWING_VERIFIED_AND_COMMITTED_M1-ELEC-B2"
    dc["footprint"]["drawing_checks"] = [
        "15 contacts at 1.00 mm pitch / 14.00 mm centre span",
        "signal pads 0.60 x 2.00 mm",
        "two unnumbered mounting-plate solder pads 0.70 x 4.20 mm at +/-8.00 mm",
        "mounting plates bracket contact row",
        "temporary converter 3D path removed",
        "footprint attr normalized to SMD",
    ]
    stale = "final dimension-by-dimension pad/mounting-plate/courtyard audit against Amphenol drawing 10172241"
    if stale in dc["still_open"]:
        dc["still_open"].remove(stale)
    DC.write_text(json.dumps(dc, indent=2) + "\n")


def migrate_validator() -> None:
    val = VAL.read_text()
    if "M1-ELEC-B2 final DSI506 display contract" in val:
        return
    marker = '    if \'(property "Reference" "J_LCD"\' in p10:'
    if marker not in val:
        raise SystemExit("legacy display validator block start not found")
    start = val.index(marker)
    end = val.index("\n\n    # 7. ESP32-P4 multi-unit GPIO connectivity contract.", start)
    newcheck = '''    # M1-ELEC-B2 final DSI506 display contract.
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
    active_p10 = "\\n".join(instantiated_symbol_blocks(p10))
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
'''
    VAL.write_text(val[:start] + newcheck + val[end:])


def main() -> None:
    rebuild_sheet10()
    retire_sheet11()
    migrate_p4()
    migrate_root()
    migrate_authorities()
    migrate_validator()
    for path in [P10, P11, P03, ROOT]:
        if balance(path.read_text()) != (0, 0):
            raise SystemExit(f"post-write imbalance: {path}")
    print("PASS: M1-ELEC-B2 source migration complete")
    print("PASS: J6 instantiated; legacy MP3202/GT911 control paths removed")


if __name__ == "__main__":
    main()
