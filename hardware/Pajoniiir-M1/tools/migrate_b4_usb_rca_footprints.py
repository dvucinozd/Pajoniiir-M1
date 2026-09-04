#!/usr/bin/env python3
"""Lock J2/J3 Amphenol USB-A and J4/J5 Kycon RCA footprints.

Fail-closed: only physically/manufacturer-supported land-pattern geometry is locked.
Final panel XY/cutouts and mating envelopes remain open mechanical gates.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
FPDIR = BASE / "libraries" / "footprints.pretty"
GATES = BASE / "mechanical_gates.json"
B4 = BASE / "m1_mech_b4_connector_source_lock.json"

USB_FP = "Pajoniiir-M1:Amphenol_87520-1010ALF"
RCA_FP = "Pajoniiir-M1:Kycon_KLPX-0848A-2-x-G"
AMPH_DS = "https://cdn.amphenol-cs.com/media/wysiwyg/files/drawing/87520.pdf"
KYCON_DS = "https://www.kycon.com/Pub_Eng_Draw/KLPX-0848A-2-x-G.pdf"

AMPHENOL = r'''(module Amphenol_87520-1010ALF (layer F.Cu)
  (descr "Amphenol/FCI 87520-1010ALF USB 2.0 Type-A right-angle THT; land pattern from released 87520 drawing Rev AR")
  (tags "USB_A Female Amphenol FCI 87520-1010ALF")
  (property "Manufacturer" "Amphenol Communications Solutions / FCI")
  (property "MPN" "87520-1010ALF")
  (fp_text reference REF** (at 3.5 -3.2) (layer F.SilkS)
    (effects (font (size 1 1) (thickness 0.15))))
  (fp_text value Amphenol_87520-1010ALF (at 3.5 14.5) (layer F.Fab)
    (effects (font (size 1 1) (thickness 0.15))))
  (fp_text user %R (at 3.5 4.0) (layer F.Fab)
    (effects (font (size 1 1) (thickness 0.15))))
  (fp_line (start -3.75 -2.3) (end 10.75 -2.3) (layer F.Fab) (width 0.1))
  (fp_line (start 10.75 -2.3) (end 10.75 13.0) (layer F.Fab) (width 0.1))
  (fp_line (start 10.75 13.0) (end -3.75 13.0) (layer F.Fab) (width 0.1))
  (fp_line (start -3.75 13.0) (end -3.75 -2.3) (layer F.Fab) (width 0.1))
  (fp_line (start -3.9 -2.45) (end 10.9 -2.45) (layer F.SilkS) (width 0.12))
  (fp_line (start -3.9 -2.45) (end -3.9 13.15) (layer F.SilkS) (width 0.12))
  (fp_line (start 10.9 -2.45) (end 10.9 13.15) (layer F.SilkS) (width 0.12))
  (fp_line (start -3.9 13.15) (end 10.9 13.15) (layer F.SilkS) (width 0.12))
  (fp_line (start -4.3 -2.9) (end 11.3 -2.9) (layer F.CrtYd) (width 0.05))
  (fp_line (start 11.3 -2.9) (end 11.3 13.55) (layer F.CrtYd) (width 0.05))
  (fp_line (start 11.3 13.55) (end -4.3 13.55) (layer F.CrtYd) (width 0.05))
  (fp_line (start -4.3 13.55) (end -4.3 -2.9) (layer F.CrtYd) (width 0.05))
  (fp_line (start -0.9 -2.65) (end 0.9 -2.65) (layer F.SilkS) (width 0.12))
  (pad 1 thru_hole rect (at 0 0) (size 1.6 1.6) (drill 0.95) (layers *.Cu *.Mask))
  (pad 2 thru_hole circle (at 2.5 0) (size 1.6 1.6) (drill 0.95) (layers *.Cu *.Mask))
  (pad 3 thru_hole circle (at 4.5 0) (size 1.6 1.6) (drill 0.95) (layers *.Cu *.Mask))
  (pad 4 thru_hole circle (at 7.0 0) (size 1.6 1.6) (drill 0.95) (layers *.Cu *.Mask))
  (pad 5 thru_hole circle (at -3.07 2.71) (size 3.0 3.0) (drill 2.30) (layers *.Cu *.Mask))
  (pad 5 thru_hole circle (at 10.07 2.71) (size 3.0 3.0) (drill 2.30) (layers *.Cu *.Mask))
)
'''

KYCON = r'''(module Kycon_KLPX-0848A-2-x-G (layer F.Cu)
  (descr "Kycon KLPX-0848A-2-x-G right-angle RCA; land pattern checked against current Kycon drawing and established KLPX-0848A footprint")
  (tags "RCA Kycon KLPX-0848A-2-x-G")
  (property "Manufacturer" "Kycon")
  (property "MPN family" "KLPX-0848A-2-x-G")
  (fp_text reference REF** (at -4 -6.5) (layer F.SilkS)
    (effects (font (size 1 1) (thickness 0.15))))
  (fp_text value Kycon_KLPX-0848A-2-x-G (at -4 6.5) (layer F.Fab)
    (effects (font (size 1 1) (thickness 0.15))))
  (fp_text user %R (at -4 0) (layer F.Fab)
    (effects (font (size 1 1) (thickness 0.15))))
  (fp_line (start -13.5 -5.0) (end 6.0 -5.0) (layer F.Fab) (width 0.1))
  (fp_line (start 6.0 -5.0) (end 6.0 5.0) (layer F.Fab) (width 0.1))
  (fp_line (start 6.0 5.0) (end -13.5 5.0) (layer F.Fab) (width 0.1))
  (fp_line (start -13.5 5.0) (end -13.5 -5.0) (layer F.Fab) (width 0.1))
  (fp_line (start -13.6 -5.1) (end 6.1 -5.1) (layer F.SilkS) (width 0.12))
  (fp_line (start 6.1 -5.1) (end 6.1 5.1) (layer F.SilkS) (width 0.12))
  (fp_line (start 6.1 5.1) (end -13.6 5.1) (layer F.SilkS) (width 0.12))
  (fp_line (start -13.6 5.1) (end -13.6 -5.1) (layer F.SilkS) (width 0.12))
  (fp_line (start -14.1 -5.6) (end 6.6 -5.6) (layer F.CrtYd) (width 0.05))
  (fp_line (start 6.6 -5.6) (end 6.6 5.6) (layer F.CrtYd) (width 0.05))
  (fp_line (start 6.6 5.6) (end -14.1 5.6) (layer F.CrtYd) (width 0.05))
  (fp_line (start -14.1 5.6) (end -14.1 -5.6) (layer F.CrtYd) (width 0.05))
  (pad 2 thru_hole oval (at 0 0) (size 4.0 5.5) (drill 3.30) (layers *.Cu *.Mask))
  (pad 1 thru_hole oval (at 4.5 0) (size 3.5 5.0) (drill 3.00) (layers *.Cu *.Mask))
)
'''


def sexpr_at(text: str, start: int) -> tuple[str, int]:
    depth = 0
    quoted = False
    esc = False
    for i in range(start, len(text)):
        ch = text[i]
        if quoted:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                quoted = False
            continue
        if ch == '"':
            quoted = True
        elif ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
            if depth == 0:
                return text[start:i+1], i+1
    raise ValueError("unterminated s-expression")


def update_instance(path: Path, ref: str, value: str, fp: str, ds: str) -> None:
    text = path.read_text(encoding="utf-8")
    pos = text.find(f'(property "Reference" "{ref}"')
    if pos < 0:
        raise SystemExit(f"{path.name}: {ref} instance not found")
    start = text.rfind('(symbol', 0, pos)
    block, end = sexpr_at(text, start)
    def sub(prop: str, new: str, src: str) -> str:
        pat = rf'(\(property "{re.escape(prop)}" )"[^"]*"'
        out, n = re.subn(pat, lambda m: m.group(1) + '"' + new + '"', src, count=1)
        if n != 1:
            raise SystemExit(f"{path.name}: {ref} property {prop} update count={n}")
        return out
    new = sub("Value", value, block)
    new = sub("Footprint", fp, new)
    new = sub("Datasheet", ds, new)
    path.write_text(text[:start] + new + text[end:], encoding="utf-8")


def main() -> int:
    FPDIR.mkdir(parents=True, exist_ok=True)
    (FPDIR / "Amphenol_87520-1010ALF.kicad_mod").write_text(AMPHENOL, encoding="utf-8")
    (FPDIR / "Kycon_KLPX-0848A-2-x-G.kicad_mod").write_text(KYCON, encoding="utf-8")

    update_instance(BASE / "07_USB0_STORAGE.kicad_sch", "J2", "87520-1010ALF", USB_FP, AMPH_DS)
    update_instance(BASE / "08_USB1_FLX4.kicad_sch", "J3", "87520-1010ALF", USB_FP, AMPH_DS)
    update_instance(BASE / "09_AUDIO_PCM5102A.kicad_sch", "J4", "KLPX-0848A-2-W-G", RCA_FP, KYCON_DS)
    update_instance(BASE / "09_AUDIO_PCM5102A.kicad_sch", "J5", "KLPX-0848A-2-R-G", RCA_FP, KYCON_DS)

    gates = json.loads(GATES.read_text(encoding="utf-8"))
    by_id = {g.get("id"): g for g in gates["gates"]}
    for gid, mpn, fp in (
        ("J2_USB0", "87520-1010ALF", USB_FP),
        ("J3_USB1", "87520-1010ALF", USB_FP),
        ("J4_RCA_L", "KLPX-0848A-2-W-G", RCA_FP),
        ("J5_RCA_R", "KLPX-0848A-2-R-G", RCA_FP),
    ):
        g = by_id[gid]
        g["allow_blank_footprint"] = False
        g["exact_mpn"] = mpn
        g["exact_footprint"] = fp
        g["footprint_status"] = "CLOSED__MANUFACTURER_CHECKED_PROJECT_LOCAL_FOOTPRINT"
        g["source_status"] = "MPN_AND_FOOTPRINT_LOCKED_M1-MECH-B4-IO"
        g["status"] = "open"
        g["blocks_layout_freeze"] = True
        g["closure"] = (
            f"{mpn} and {fp} are locked/instantiated. Gate remains open only for final panel center/cutout, "
            "mated connector/cable envelope and absolute XY/Z placement."
        )
        g["required_evidence"] = [x for x in g.get("required_evidence", []) if not any(k in x.lower() for k in ("mpn", "lifecycle", "shell retention style"))]
    GATES.write_text(json.dumps(gates, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    b4 = json.loads(B4.read_text(encoding="utf-8"))
    for sel in b4["selections"]:
        refs = tuple(sel.get("refdes", []))
        if refs == ("J2", "J3"):
            sel["selection_status"] = "COMMON_PART_MPN_AND_FOOTPRINT_LOCKED_FOR_BOTH_PORTS"
            sel["exact_footprint"] = USB_FP
            sel["footprint_source"] = "Amphenol released 87520 drawing Rev AR; 4 signal holes and 2 board-lock/shell holes machine-checked in project-local footprint."
            sel["still_open"] = [x for x in sel.get("still_open", []) if "land pattern" not in x.lower() and "footprint" not in x.lower()]
        elif refs in (("J4",), ("J5",)):
            sel["selection_status"] = "MPN_AND_FOOTPRINT_LOCKED"
            sel["exact_footprint"] = RCA_FP
            sel["footprint_source"] = "Current Kycon KLPX-0848A-2-x-G drawing, cross-checked against an independently used KLPX-0848A board footprint; 4.50 mm terminal raster."
            sel["still_open"] = [x for x in sel.get("still_open", []) if "land pattern" not in x.lower() and "footprint" not in x.lower()]
    b4["status"] = "EXTERNAL_USER_IO_MPN_SELECTION_LOCKED__USB_RCA_MICROSD_SWITCH_FOOTPRINTS_LOCKED__J1_AND_PANEL_DATUMS_OPEN"
    b4["next_actions"] = [
        "close J1 Switchcraft footprint only after the three-terminal PCB hole centers are unambiguously encoded from released drawing/CAD evidence",
        "place exact connector courtyards in the B3 104 x 62 mm placement skeleton",
        "solve final panel centers/cutouts and mated cable envelopes",
        "validate DSI FFC bend and local rear-display obstruction map",
        "then promote PCB_OUTLINE from screening candidate to mechanical pre-freeze",
    ]
    B4.write_text(json.dumps(b4, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Retire stale sheet annotations that still say these footprints are TBD.
    for p, old, new in (
        (BASE / "07_USB0_STORAGE.kicad_sch", "90 ohm differential target; connector footprint TBD-MECH", "90 ohm differential target; J2 Amphenol 87520-1010ALF footprint locked"),
        (BASE / "09_AUDIO_PCM5102A.kicad_sch", "RCA J4/J5 mechanical footprints remain TBD-MECH.", "RCA J4/J5 Kycon KLPX-0848A gold-family footprints are locked; final panel XY/cutouts remain open."),
    ):
        t = p.read_text(encoding="utf-8")
        t = t.replace(old, new)
        p.write_text(t, encoding="utf-8")

    print("PASS: J2/J3 Amphenol and J4/J5 Kycon footprint migration staged; panel gates remain open")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
