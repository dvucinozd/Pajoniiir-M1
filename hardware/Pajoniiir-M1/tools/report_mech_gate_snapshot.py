#!/usr/bin/env python3
"""Report the current M1-MECH-A13 gate snapshot from mechanical_gates.json.

This is intentionally read-only. It is useful before/after physical-CAD or EVT
closure work and gives a deterministic count of layout blockers and BOM blank
footprint gates without duplicating policy in documentation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
GATES = BASE / "mechanical_gates.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="emit the snapshot as machine-readable JSON",
    )
    args = parser.parse_args()

    data = json.loads(GATES.read_text(encoding="utf-8"))
    gates = data.get("gates", [])

    open_blockers = [
        gate["id"]
        for gate in gates
        if gate.get("blocks_layout_freeze") and gate.get("status") != "closed"
    ]
    closed = [gate["id"] for gate in gates if gate.get("status") == "closed"]
    blank_bom = [
        gate["refdes"]
        for gate in gates
        if gate.get("allow_blank_footprint") and gate.get("bom_scope")
    ]

    inconsistent_closed = [
        gate["id"]
        for gate in gates
        if gate.get("status") == "closed" and gate.get("blocks_layout_freeze")
    ]
    if inconsistent_closed:
        raise SystemExit(
            "closed gates still block layout freeze: " + ", ".join(inconsistent_closed)
        )

    if data.get("layout_freeze_allowed") and open_blockers:
        raise SystemExit(
            "layout_freeze_allowed=true while blockers remain: "
            + ", ".join(open_blockers)
        )

    snapshot = {
        "layout_freeze_allowed": bool(data.get("layout_freeze_allowed")),
        "open_layout_blocker_count": len(open_blockers),
        "closed_gate_count": len(closed),
        "intentional_blank_bom_gate_count": len(blank_bom),
        "open_layout_blockers": open_blockers,
        "closed_gates": closed,
        "blank_bom_refdes": blank_bom,
    }

    if args.as_json:
        print(json.dumps(snapshot, indent=2))
        return 0

    print("M1-MECH-A13 gate snapshot")
    print(f"  layout freeze allowed: {snapshot['layout_freeze_allowed']}")
    print(f"  open layout blockers: {len(open_blockers)}")
    print(f"  closed gates: {len(closed)}")
    print(f"  intentional blank BOM gates: {len(blank_bom)}")
    print("  blockers:")
    for gate_id in open_blockers:
        print(f"    - {gate_id}")
    print("  closed:")
    for gate_id in closed:
        print(f"    - {gate_id}")
    print("  blank BOM RefDes:")
    for refdes in blank_bom:
        print(f"    - {refdes}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
