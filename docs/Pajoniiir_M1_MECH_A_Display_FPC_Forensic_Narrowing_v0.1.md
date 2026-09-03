# Pajoniiir-M1 — M1-MECH-A Display FPC Forensic Narrowing v0.1

**Datum:** 2026-09-03  
**Revision:** M1-MECH-A9  
**Status:** Two J_LCD sub-gates CLOSED; physical mating and 3V3-domain gate remain open

## Resolved

### 30 contacts vs symbol refs 31/32

JLCPCB identifies SOFNG `0.5TBQP-30P-1` / `C3975120` as `FPC0.5mm-30pin`.

The original Guition LCD schematic raster shows:

- electrical contacts `1..30`
- separate auxiliary refs `31` and `32`
- both 31/32 tied to GND

Therefore the earlier 30-vs-32 discrepancy is not a 32-contact FPC. It is **30 contacts + two GND shell/mount references**.

### Pins 15/16/18/19

The same original raster shows explicit NC markers on:

~~~text
15
16
18
19
~~~

These are recorded as NC for the original JC4880 electrical variant.

## Still open

J_LCD remains intentionally uninstantiated until all of these are authoritative:

1. exact final purchased panel MPN / electrical variant,
2. FPC contact-side orientation,
3. connector mating height and insertion/mechanical geometry,
4. whether panel-side 3V3 contacts 4/21/29 are internally common.

The original board drives 4/21/29 from one `ESP_3V3` net. That proves only the board-side connection; it does **not** prove the panel internally shorts those contacts. M1 must not split them between `3V3_LCD` and `3V3_TOUCH` until this is known.

## Sources

- Guition LCD/CSI schematic raster: https://github.com/wegi1/ESP32P4-JC4880P443C-I-W/blob/main/5-Schematic/2_LCD%26CSI.png
- JLCPCB SOFNG component record: https://jlcpcb.com/partdetail/SOFNG-0_5TBQP_30P1/C3975120
