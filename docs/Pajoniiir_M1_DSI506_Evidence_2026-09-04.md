# DSI506 rear reference and measurement handoff

> **M1-MECH-B7 NOTE (2026-09-06):** This is display-specific historical evidence. DSI506 is a validated compatibility profile and does not define Pajoniiir-M1 board `Edge.Cuts`, mounting holes, connector coordinates or enclosure. Current authority: `board_first_mechanical_contract.json`.


Received from the user on 2026-09-04. The image is a dimensioned reference photograph; it is not a calibrated photograph of the user's individual module. The text reports physical measurements from another project. Those reports are retained as supplied evidence, not as measurements performed during this review.

Original artifacts are retained under [hardware evidence](../hardware/Pajoniiir-M1/evidence/):

- [Rear reference image](../hardware/Pajoniiir-M1/evidence/dsi506_rear_dimensioned_reference.jpg)
- [Measurement handoff, verbatim](../hardware/Pajoniiir-M1/evidence/dsi506_measurement_handoff.txt)
- [Provenance, hashes and discrepancy record](../hardware/Pajoniiir-M1/dsi506_source_review_2026-09-04.json)

## Dimension discrepancy: resolved by the user

| Quantity | Image | Text / existing model | Interpretation |
|---|---:|---:|---|
| Rear PCB width | 121.109 mm | 121.109 mm | agrees |
| Rear PCB height | **77.93 mm** | **77.193 mm** | **user confirms image: use 77.93 mm** |
| Inner post X spacing | 78 - 20 = 58 mm | 58 mm | agrees |
| Inner post Y spacing | 56.43 - 7.43 = 49 mm | 49 mm | agrees |
| Lower outer-hole Y | 72.93 mm | 72.93 mm | agrees |

The user explicitly confirmed that the image is correct. The nominal rear PCB is therefore **121.109 x 77.93 mm**. The previous 77.193 mm handoff/model value is superseded; the original text is retained verbatim for provenance. This is a user-confirmed source correction, not a new caliper measurement performed during this review.

At 77.93 mm total height, the lower outer-hole centers are 5.00 mm above the bottom edge. The centered 124 x 80 mm enclosure cavity now provides 1.4455 mm X and **1.035 mm Y clearance per side**. The rear PCB top-left is (3.4455, 3.035) mm from the outer enclosure corner, and the mainboard top-left becomes (11.9455, 3.965) mm. Mainboard-to-inner-wall Y gaps become 1.965 mm top and 16.035 mm bottom. The inner post pattern and display-relative board/connector locations do not change.

All active JSON geometry, validation expectations and dependent enclosure calculations were updated. The old enclosure remains rejected (display exceeds its outer height by 4.522 mm and inner height by 8.522 mm). Final assembly tolerances and production outline remain open.

The image's upper horizontal dimension is 116.110 mm from the left outer-hole center to the right PCB edge. Combining the separately marked 5 mm right-hole offset with the 121.109 mm width yields the existing nominal X centers of 5 and 116.109 mm, within the drawing's 0.001 mm rounding. These printed decimals do not establish manufacturing tolerances.

## Evidence that remains useful

Rear-view datum: top-left PCB corner, +X right and +Y down. Inner post centers remain (43.109, 7.430), (101.109, 7.430), (43.109, 56.430), (101.109, 56.430) mm.

The supplied text confirms the existing B2 lock: M2.5 threads, 5 mm post diameter and height, 3 mm usable thread depth, coplanar tops, Z=10 mm seating plane. A nominal 1.6 mm mainboard with an M2.5 x 4 mm screw gives 2.4 mm engagement and 0.6 mm bottoming margin before assembly tolerances. Final screw head/washer selection remains open.

The right-edge DSI connector and visible rear component clusters can guide preliminary obstruction planning. Its precise center (110.109, 33.000) mm comes from the measurement handoff and prior evidence, not dimension lines on this image. The supplied image has no external DSI FFC attached; the central orange ribbon is the internal display connection.

## Still needed

- Final dimensional tolerance/assembly-fit validation using the corrected nominal 121.109 x 77.93 mm envelope.
- Pin-1 and installed cable continuity verification; actual FFC and connector close-ups have now been received and reviewed below.
- Local component heights and cable bend/insertion/removal clearance in the proposed 5 mm inter-board gap. A planar photograph cannot prove these clearances.
- Final enclosure and connector datums, mounting hardware and PCB outline.

These remain part of the existing `PCB_OUTLINE` and `J_LCD_DISPLAY_FPC` gates. No mechanical gate closes solely from this image.

## Actual cable and connector photographs received

The user supplied four additional photographs on 2026-09-04. Originals and SHA-256 hashes are retained with the source review record.

| Artifact | What is established |
|---|---|
| [Flat cable](../hardware/Pajoniiir-M1/evidence/dsi506_ffc_flat.png) | Contacts at one end and blue stiffener at the other on the same face: opposite-side contacts, Type-B |
| [Both exposed ends](../hardware/Pajoniiir-M1/evidence/dsi506_ffc_both_ends.png) | 15 visible contact fingers; no dimensional scale |
| [Actual rear-board context](../hardware/Pajoniiir-M1/evidence/dsi506_actual_rear_connector_context.png) | DSI connector, nearby posts, GND/PWM pads and fan-header orientation |
| [DSI close-up](../hardware/Pajoniiir-M1/evidence/dsi506_actual_dsi_closeup.png) | 15 solder tails; cable entry toward the image's bottom edge |

The actual board is rotated relative to the nominal landscape drawing: downward in these connector photographs corresponds to +X in the established rear-PCB datum. Left along the contact row points toward the fan header. The light spot beside the other end of the row is not an unambiguous pin-1 marker. The overhead views do not establish the internal contact side. Cable printing is not a module pin-number reference.

The flat view establishes Type-B independently of how the cable is folded in the second picture. The folded picture does not qualify that bend for installation or repeated use. Prior 1.0 mm pitch and approximately 60 x 15 mm dimensions remain measurement-handoff data, not new measurements from these unscaled photographs.

### M3 reference rechecked: existing electrical acceptance

At user direction, the M3 repository was checked at `b3e2bee5ded0a836906ab6f689d79a6e6b49d541`. Local HEAD and the remote `master` SHA match. The M3 checkout was inspected without modification.

- [M3 BSP pin reference](https://github.com/dvucinozd/Pajoniiir-M3/blob/b3e2bee5ded0a836906ab6f689d79a6e6b49d541/firmware/main-deck-p4/components/bsp_p4_m3/include/bsp_p4_m3.h#L5-L14) specifies the 15-pin electrical map already adopted in M1.
- [M3 accepted wiring](https://github.com/dvucinozd/Pajoniiir-M3/blob/b3e2bee5ded0a836906ab6f689d79a6e6b49d541/docs/HARDWARE_WIRING.md#L48-L63) records physical FFC orientation/J2 acceptance and the fan-header 3.3 V measurement. The fan header is not an additional display power input.
- [M3 display acceptance](https://github.com/dvucinozd/Pajoniiir-M3/blob/b3e2bee5ded0a836906ab6f689d79a6e6b49d541/docs/DISPLAY_DSI506_BRINGUP.md) explicitly gives current acceptance precedence over the historical pre-arrival candidate notes. Those older notes must not reopen already accepted M3 operation.

The pin table, M1 `display_connector_b1.json` and M1 `display_compatibility_dsi506.json` agree for all 15 contacts. The electrical map and working M3 assembly are accepted evidence; repeating a full ground survey is not needed to establish them. The repository text reviewed does not identify which endpoint in the newly supplied close-up is pin 1. Translating the working connection to the new M1 connector's physical orientation remains a placement/assembly task, including FFC bend clearance. No photo-coordinate pin number is inferred from firmware alone.

### Optional physical orientation check for the new layout

The following ground survey is one way to resolve the close-up's physical numbering if the accepted M3 assembly cannot supply the needed orientation reference. It is not a prerequisite for continuing electrical/documentation work from the accepted M3 pin map.

The user clarified that the module is powered through DSI and the separate fan header outputs approximately 3.3 V while powered. This is a reported powered-voltage observation at the fan header, not a continuity measurement at the DSI contacts. It does not establish a direct connection from that fan output to DSI pins 14/15; the intervening circuitry has not been verified. No external supply should be connected to the fan header for this check.

Use the last close-up's orientation, without renaming any physical contact as electrical pin 1 yet. For recording measurements, call the 15 signal solder tails **A1 through A15 from left to right in that photograph**; exclude the two large mechanical anchors. These A labels are temporary photo coordinates.

Use the labeled round `GND` test pad beside `PWM` as the reference for the next check. Disconnect all power and remove the external DSI cable from the module. Verify zero voltage before changing the meter to continuity/resistance. First note the resistance with the meter leads touching each other. Then keep one probe on the `GND` test pad and probe each of A1..A15 individually. Record stable near-zero readings, comparable with shorted leads. A momentary charging beep is not a confirmed direct connection; record ambiguous readings as unresolved.

The project's intended interface assigns 3V3 to pins 14/15 and GND to pins 1/4/7/10/13. The two candidate ground patterns in photo coordinates are:

| Candidate orientation | Expected directly grounded photo positions |
|---|---|
| Electrical pin 1 at the left end (A1) | A1, A4, A7, A10, A13 |
| Electrical pin 1 at the right end (A15) | A3, A6, A9, A12, A15 |

These are predictions from `display_connector_b1.json`, not measured results. A matching complete pattern supports numbering orientation; unexpected additional low-resistance contacts or missing grounds require investigation before declaring a match. A single grounded contact is insufficient. Do not assign numbering merely from visible trace shapes.

After the module numbering/contact orientation is established, record continuity through the installed cable to the host connector in its intended orientation. This is still required before closing host-to-module pin-1 mapping. No measurement results have been supplied yet, and the KiCad pin map and placement remain unchanged by this photo review.
