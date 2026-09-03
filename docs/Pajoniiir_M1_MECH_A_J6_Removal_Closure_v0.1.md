# Pajoniiir-M1 — M1-MECH-A J6 Rev A Removal Closure v0.1

**Datum:** 2026-09-03  
**Revision:** M1-MECH-A8  
**Status:** J6 mechanical/product gate CLOSED by removal  
**Authority:** `hardware/Pajoniiir-M1/mechanical_gates.json`

## Decision

The optional J6 3.5 mm stereo line output is **not part of Pajoniiir-M1 Rev A**. J6 and its direct MAIN_L / MAIN_R / GND branch are removed from `09_AUDIO_PCM5102A.kicad_sch`. No footprint, courtyard, panel aperture or placement budget is reserved.

## Why

Rev A already defines MAIN as PCM5102A -> RCA J4/J5 and CUE/headphones through the DDJ-FLX4 USB Audio headphone output. J6 was production-default DNP, line-level only, and never a headphone driver.

M1-MECH-A4 also showed that adding the legacy Ø6.97 mm J6 aperture to the primary USB+RCA edge row leaves only **0.525 mm** to the candidate Ø2 mounting-hole edge before boss/courtyard allowance.

## Manufacturing effect

~~~text
in_bom=yes RefDes        270 -> 269
DNP RefDes                17 -> 16
blank-footprint BOM gates 12 -> 11
~~~

The legacy Ø6.97 mm hole remains historical enclosure evidence only.

## Reintroduction

A future 3.5 mm output is a deliberate board/product revision requiring new combined-load, ESD, connector, panel and enclosure validation. It is no longer a simple DNP population choice.
