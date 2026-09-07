#!/usr/bin/env python3
"""Populate the empty M1 PCB from a fresh KiCad XML netlist.

This creates a reversible board-first placement canvas.  It deliberately does
not create Edge.Cuts, mounting holes, tracks, zones, or a production outline.
Run it with KiCad's bundled Python so the pcbnew module is available.
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import pcbnew


MM = pcbnew.FromMM
SYSTEM_FOOTPRINT_ROOT = Path(r"C:\Program Files\KiCad\10.0\share\kicad\footprints")


DOMAIN_BY_SHEET = {
    "01_POWER_INPUT": "POWER_SPINE",
    "02_POWER_3V3": "POWER_SPINE",
    "06_USB_POWER": "POWER_SPINE",
    "14_TEST_MONITORING": "POWER_SPINE",
    "03_P4_CORE": "P4_CORE",
    "04_P4_FLASH_CLOCK_RESET": "P4_CORE",
    "05_C6_WIFI": "C6_RF",
    "07_USB0_STORAGE": "USB_EDGES",
    "08_USB1_FLX4": "USB_EDGES",
    "09_AUDIO_PCM5102A": "AUDIO",
    "10_DISPLAY_MIPI": "DSI_HOST",
    "12_MICROSD": "STORAGE",
    "13_DEBUG_SERVICE": "SERVICE",
}

DOMAIN_ROWS = (
    ("POWER_SPINE", "USB_EDGES", "AUDIO"),
    ("P4_CORE", "C6_RF", "DSI_HOST"),
    ("STORAGE", "SERVICE"),
)

TARGET_WIDTH_MM = {
    "POWER_SPINE": 58.0,
    "USB_EDGES": 45.0,
    "AUDIO": 48.0,
    "P4_CORE": 72.0,
    "C6_RF": 44.0,
    "DSI_HOST": 44.0,
    "STORAGE": 48.0,
    "SERVICE": 54.0,
}

ANCHOR_PRIORITY = {
    "POWER_SPINE": ("U7", "U8", "L2", "U6", "U12", "U14"),
    "USB_EDGES": ("J2", "D2", "J3", "D3"),
    "AUDIO": ("U5", "J4", "J5"),
    "P4_CORE": ("U1", "U2", "U3", "Y1", "L1"),
    "C6_RF": ("U4",),
    "DSI_HOST": ("J6", "FB3", "C93", "C94"),
    "STORAGE": ("J7", "U13"),
    "SERVICE": ("SW1", "SW2", "J8", "J9", "J10"),
}


@dataclass
class Component:
    ref: str
    value: str
    footprint_id: str
    sheetname: str
    sheetfile: str
    path: str
    dnp: bool
    exclude_from_bom: bool
    footprint: pcbnew.FOOTPRINT | None = None


def properties(element: ET.Element) -> dict[str, str]:
    return {
        prop.get("name", ""): prop.get("value", "")
        for prop in element.findall("property")
    }


def load_components(root: ET.Element) -> tuple[list[Component], list[str]]:
    result: list[Component] = []
    blanks: list[str] = []
    elements = root.find("components")
    if elements is None:
        raise RuntimeError("Netlist has no components section")
    for element in elements:
        props = properties(element)
        ref = element.get("ref", "")
        footprint_id = (element.findtext("footprint") or "").strip()
        sheetpath = element.find("sheetpath")
        sheet_tstamp = (sheetpath.get("tstamps", "/") if sheetpath is not None else "/").rstrip("/")
        component_tstamps = (element.findtext("tstamps") or "").strip("/").split()
        if not component_tstamps:
            raise RuntimeError(f"{ref}: component has no schematic timestamp")
        # Multi-unit symbols list one UUID per unit.  KiCad's netlist importer
        # associates the footprint with the first exported unit UUID.
        component_tstamp = component_tstamps[0]
        path = f"{sheet_tstamp}/{component_tstamp}" if sheet_tstamp else f"/{component_tstamp}"
        component = Component(
            ref=ref,
            value=element.findtext("value") or "",
            footprint_id=footprint_id,
            sheetname=props.get("Sheetname", ""),
            sheetfile=props.get("Sheetfile", ""),
            path=path,
            dnp="dnp" in props,
            exclude_from_bom="exclude_from_bom" in props,
        )
        result.append(component)
        if not footprint_id:
            blanks.append(ref)
    return result, blanks


def footprint_library_path(project_root: Path, nickname: str) -> Path:
    if nickname == "Pajoniiir-M1":
        return project_root / "libraries" / "footprints.pretty"
    return SYSTEM_FOOTPRINT_ROOT / f"{nickname}.pretty"


def instantiate_footprints(project_root: Path, components: list[Component]) -> None:
    errors: list[str] = []
    for component in components:
        if not component.footprint_id:
            continue
        nickname, footprint_name = component.footprint_id.split(":", 1)
        library_path = footprint_library_path(project_root, nickname)
        footprint = pcbnew.FootprintLoad(str(library_path), footprint_name)
        if footprint is None:
            errors.append(f"{component.ref}: cannot load {component.footprint_id} from {library_path}")
            continue
        footprint.SetFPIDAsString(component.footprint_id)
        footprint.SetReference(component.ref)
        footprint.SetValue(component.value)
        footprint.SetPath(pcbnew.KIID_PATH(component.path))
        footprint.SetSheetname(component.sheetname)
        footprint.SetSheetfile(component.sheetfile)
        footprint.SetDNP(component.dnp)
        footprint.SetExcludedFromBOM(component.exclude_from_bom)
        footprint.SetExcludedFromPosFiles(component.dnp)
        footprint.SetIsPlaced(True)
        component.footprint = footprint
    if errors:
        raise RuntimeError("\n".join(errors))


def bbox_mm(footprint: pcbnew.FOOTPRINT) -> tuple[float, float]:
    box = footprint.GetBoundingBox()
    return max(0.5, pcbnew.ToMM(box.GetWidth())), max(0.5, pcbnew.ToMM(box.GetHeight()))


def sort_domain(domain: str, components: list[Component]) -> list[Component]:
    priorities = {ref: index for index, ref in enumerate(ANCHOR_PRIORITY.get(domain, ()))}

    def key(component: Component) -> tuple[int, int, float, str]:
        assert component.footprint is not None
        width, height = bbox_mm(component.footprint)
        return (
            0 if component.ref in priorities else 1,
            priorities.get(component.ref, 999),
            -(width * height),
            component.ref,
        )

    return sorted(components, key=key)


def local_shelf_pack(domain: str, components: list[Component]) -> tuple[dict[str, tuple[float, float]], float, float]:
    """Return non-overlapping footprint anchor positions relative to a domain box."""
    margin = 1.0
    gap = 1.2
    label_band = 5.0
    target_width = TARGET_WIDTH_MM[domain]
    x = margin
    y = margin + label_band
    row_height = 0.0
    max_x = margin
    positions: dict[str, tuple[float, float]] = {}

    for component in sort_domain(domain, components):
        assert component.footprint is not None
        box = component.footprint.GetBoundingBox()
        width = max(0.5, pcbnew.ToMM(box.GetWidth()))
        height = max(0.5, pcbnew.ToMM(box.GetHeight()))
        if x > margin and x + width > target_width - margin:
            x = margin
            y += row_height + gap
            row_height = 0.0
        # The footprint anchor is not necessarily the bounding-box origin.
        anchor_x = x - pcbnew.ToMM(box.GetX())
        anchor_y = y - pcbnew.ToMM(box.GetY())
        positions[component.ref] = (anchor_x, anchor_y)
        x += width + gap
        row_height = max(row_height, height)
        max_x = max(max_x, x - gap + margin)

    total_height = y + row_height + margin
    return positions, max(target_width, max_x), total_height


def add_domain_graphics(board: pcbnew.BOARD, domain: str, x: float, y: float, width: float, height: float) -> None:
    shape = pcbnew.PCB_SHAPE(board)
    shape.SetShape(pcbnew.SHAPE_T_RECT)
    shape.SetStart(pcbnew.VECTOR2I(MM(x), MM(y)))
    shape.SetEnd(pcbnew.VECTOR2I(MM(x + width), MM(y + height)))
    shape.SetLayer(pcbnew.Dwgs_User)
    shape.SetWidth(MM(0.25))
    board.Add(shape)

    label = pcbnew.PCB_TEXT(board)
    label.SetText(f"{domain} - B8 WORKING GROUP")
    label.SetPosition(pcbnew.VECTOR2I(MM(x + 1.0), MM(y + 2.7)))
    label.SetLayer(pcbnew.Dwgs_User)
    label.SetTextSize(pcbnew.VECTOR2I(MM(1.5), MM(1.5)))
    label.SetTextThickness(MM(0.25))
    board.Add(label)


def place_domains(board: pcbnew.BOARD, components: list[Component]) -> dict[str, dict[str, object]]:
    grouped: dict[str, list[Component]] = defaultdict(list)
    for component in components:
        if component.footprint is None:
            continue
        try:
            grouped[DOMAIN_BY_SHEET[component.sheetname]].append(component)
        except KeyError as exc:
            raise RuntimeError(f"No B8 placement domain for sheet {component.sheetname!r}") from exc

    local: dict[str, tuple[dict[str, tuple[float, float]], float, float]] = {}
    for domain, members in grouped.items():
        local[domain] = local_shelf_pack(domain, members)

    report: dict[str, dict[str, object]] = {}
    start_x = 20.0
    current_y = 20.0
    horizontal_gap = 12.0
    vertical_gap = 15.0
    for row in DOMAIN_ROWS:
        current_x = start_x
        row_height = 0.0
        for domain in row:
            positions, width, height = local[domain]
            add_domain_graphics(board, domain, current_x, current_y, width, height)
            refs: list[str] = []
            for component in grouped[domain]:
                assert component.footprint is not None
                local_x, local_y = positions[component.ref]
                component.footprint.SetPosition(
                    pcbnew.VECTOR2I(MM(current_x + local_x), MM(current_y + local_y))
                )
                board.Add(component.footprint)
                refs.append(component.ref)
            report[domain] = {
                "origin_mm": [round(current_x, 3), round(current_y, 3)],
                "size_mm": [round(width, 3), round(height, 3)],
                "component_count": len(refs),
                "refs": sorted(refs),
            }
            current_x += width + horizontal_gap
            row_height = max(row_height, height)
        current_y += row_height + vertical_gap
    return report


def add_nets(board: pcbnew.BOARD, root: ET.Element) -> tuple[dict[str, pcbnew.NETINFO_ITEM], list[tuple[str, str, str]]]:
    nets: dict[str, pcbnew.NETINFO_ITEM] = {}
    assignments: list[tuple[str, str, str]] = []
    elements = root.find("nets")
    if elements is None:
        raise RuntimeError("Netlist has no nets section")
    for element in elements:
        name = element.get("name", "")
        code = int(element.get("code", "0"))
        net = pcbnew.NETINFO_ITEM(board, name, code)
        board.Add(net)
        nets[name] = net
        for node in element.findall("node"):
            assignments.append((node.get("ref", ""), node.get("pin", ""), name))
    return nets, assignments


def assign_nets(
    board: pcbnew.BOARD,
    nets: dict[str, pcbnew.NETINFO_ITEM],
    assignments: list[tuple[str, str, str]],
    blank_refs: set[str],
) -> int:
    missing: list[str] = []
    assigned_nodes = 0
    for ref, pin, net_name in assignments:
        footprint = board.FindFootprintByReference(ref)
        if footprint is None:
            if ref not in blank_refs:
                missing.append(f"{ref}.{pin}: footprint absent")
            continue
        pads = [pad for pad in footprint.Pads() if pad.GetNumber() == pin]
        if not pads:
            missing.append(f"{ref}.{pin}: pad absent in {footprint.GetFPIDAsString()}")
            continue
        for pad in pads:
            pad.SetNet(nets[net_name])
        assigned_nodes += 1
    if missing:
        raise RuntimeError("Net assignment failures:\n" + "\n".join(missing))
    board.BuildListOfNets()
    return assigned_nodes


def edge_cut_count(board: pcbnew.BOARD) -> int:
    return sum(1 for drawing in board.GetDrawings() if drawing.GetLayer() == pcbnew.Edge_Cuts)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, required=True)
    parser.add_argument("--netlist", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    project_root = args.board.resolve().parent
    board = pcbnew.LoadBoard(str(args.board.resolve()))
    if board is None:
        raise RuntimeError(f"Cannot load board: {args.board}")
    if list(board.GetFootprints()):
        raise RuntimeError("B8 seed only accepts an empty PCB; refusing to replace existing placement")
    if edge_cut_count(board):
        raise RuntimeError("B8 seed requires no Edge.Cuts; refusing to imply a production outline")

    root = ET.parse(args.netlist).getroot()
    components, blank_refs = load_components(root)
    if sorted(blank_refs) != ["C3", "C8", "J1"]:
        raise RuntimeError(f"Unexpected blank-footprint set: {sorted(blank_refs)}")
    instantiate_footprints(project_root, components)
    placement = place_domains(board, components)
    nets, assignments = add_nets(board, root)
    assigned_nodes = assign_nets(board, nets, assignments, set(blank_refs))

    footprint_count = len(list(board.GetFootprints()))
    if footprint_count != 244:
        raise RuntimeError(f"Expected 244 footprints, got {footprint_count}")
    if edge_cut_count(board):
        raise RuntimeError("B8 seed unexpectedly created Edge.Cuts")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    if not pcbnew.SaveBoard(str(args.output.resolve()), board):
        raise RuntimeError(f"Failed to save board: {args.output}")

    payload = {
        "schema_version": 1,
        "milestone": "M1-PRELAYOUT-B8",
        "status": "REVERSIBLE_DOMAIN_PLACEMENT_CANVAS_CREATED",
        "production_layout": False,
        "edge_cuts_present": False,
        "footprint_count": footprint_count,
        "net_count": len(nets),
        "assigned_netlist_node_count": assigned_nodes,
        "blank_footprint_refs": sorted(blank_refs),
        "placement_domains": placement,
        "rules": [
            "Domain rectangles are on Dwgs.User and are working groups only.",
            "No domain coordinate is a production connector, mounting, or enclosure datum.",
            "Do not add Edge.Cuts or release fabrication outputs while layout_freeze_allowed is false.",
        ],
    }
    if args.report:
        args.report.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
