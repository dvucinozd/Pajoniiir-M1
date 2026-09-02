#!/usr/bin/env python3
"""Lightweight structural validator for Pajoniiir-M1 KiCad schematic sources.

This is intentionally NOT a replacement for native KiCad ERC.
It catches hierarchy/source-control regressions without requiring kicad-cli.
"""

from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE / "Pajoniiir-M1.kicad_sch"
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

# Blank footprints intentionally blocked by mechanics/sourcing, not accidental omissions.
ALLOWED_BLANK_FOOTPRINTS = {
    ("01_POWER_INPUT", "J1"),
    ("01_POWER_INPUT", "C3"),
    ("01_POWER_INPUT", "D1"),
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
            if not ref.startswith("#PWR"):
                refs[ref].append(
                    (
                        name,
                        lib_m.group(1) if lib_m else "",
                        int(unit_m.group(1)) if unit_m else 1,
                    )
                )
            if (
                not ref.startswith("#PWR")
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
    if '(property "Reference" "J_LCD"' in p10:
        errors.append("J_LCD must remain uninstantiated until authoritative FPC gate closes")
    if "PHYSICAL J_LCD IS INTENTIONALLY NOT INSTANTIATED" not in p10:
        errors.append("display FPC hard-gate annotation missing")


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
                "TOUCH_RST": "GPIO3",
                "TOUCH_INT": "GPIO4",
                "LCD_RST": "GPIO5",
                "LCD_TE": "GPIO6",
                "I2C_SDA": "GPIO7",
                "I2C_SCL": "GPIO8",
                "C6_SDIO_D0": "GPIO14",
                "C6_SDIO_D1": "GPIO15",
                "C6_SDIO_D2": "GPIO16/ADC1_CHANNEL0",
                "C6_SDIO_D3": "GPIO17/ADC1_CHANNEL1",
                "C6_SDIO_CLK": "GPIO18/ADC1_CHANNEL2",
                "C6_SDIO_CMD": "GPIO19/ADC1_CHANNEL3",
                "USB0_PWR_EN": "GPIO20/ADC1_CHANNEL4",
                "USB0_FAULT_N": "GPIO21/ADC1_CHANNEL5",
                "USB1_PWR_EN": "GPIO22/ADC1_CHANNEL6",
                "LCD_BL_PWM": "GPIO23/ADC1_CHANNEL7",
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
                    target = (ux + pin[1], uy + pin[2])
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
                    "GPIO9", "GPIO10", "GPIO11", "GPIO12", "GPIO13",
                    "CSI_DATAN0", "CSI_DATAP0", "CSI_CLKP", "CSI_CLKN",
                    "CSI_DATAN1", "CSI_DATAP1", "CSI_REXT",
                    "GPIO28", "GPIO29", "GPIO30", "GPIO31",
                    "GPIO33", "GPIO34", "GPIO47", "GPIO48",
                }
                for pin_name in unused_unit2:
                    pin = unit2_pins.get(pin_name)
                    if not pin:
                        continue
                    target = (ux + pin[1], uy + pin[2])
                    if not any(close_xy(point, target) for point in nc_points):
                        errors.append(
                            f"03_P4_CORE: unused U1/2 {pin_name} lacks explicit NC"
                        )

                dsi_rext = unit2_pins.get("DSI_REXT")
                if dsi_rext:
                    dsi_target = (ux + dsi_rext[1], uy + dsi_rext[2])
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
                if "R_DSI_REXT" not in p03 or "4.02k 1%" not in p03:
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
                    pin_name: (ux + pin[1], uy + pin[2])
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
    print("Native KiCad ERC is still required separately before M1-SCH-A is fully signed off.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
