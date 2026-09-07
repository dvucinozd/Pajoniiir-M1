# Pajoniiir-M1 M1-MECH-B7 board-first rebase

**Date:** 2026-09-06

**Decision:** the mainboard is the mechanical authority; displays are qualified peripherals.

The prior B2 through B6 path treated the DSI506 rear PCB and mounting posts as the parent datum for the custom mainboard. That creates a product-level dependency on one screen model and prevents the same board from serving variants with other DSI displays.

M1-MECH-B7 removes that dependency. J6 remains a standard 15-pin Raspberry-Pi-style MIPI DSI host interface with its locked connector, footprint and signal map. Display identity moves into compatibility profiles. DSI506/DYL0023 is the first accepted profile because its electrical behavior is already proven on Pajoniiir-M3.

This rebase changes mechanical authority only. It does not discard the supplied DSI506 measurements or photos. They remain evidence for that model's cable, adapter, bracket and enclosure work.

The following values may no longer drive M1 `Edge.Cuts` or board mounts: DSI506 58 x 49 mm posts, the 104 x 62 mm board screen, the 128 x 84 x 30 mm enclosure screen and the right-edge FFC corridor. J6 receives board-local coordinates only after component packing and MIPI route feasibility establish a viable board edge.

Compatibility with a 15-pin connector is not assumed from connector shape alone. Each model needs electrical map, power, DSI timing, controller/touch and cable-orientation qualification. A small adapter or model-specific cable is acceptable; changing the mainboard outline for each screen is not.

Machine-readable authority: `hardware/Pajoniiir-M1/board_first_mechanical_contract.json`.
