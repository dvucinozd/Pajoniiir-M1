# Pajoniiir-M1 — M1-MECH-A Connector Clusters v0.1

**Datum:** 2026-09-03  
**Status:** Relative connector topology defined; absolute cutout datums open  
**Authority:** `hardware/Pajoniiir-M1/mech_a.json`

---

## Purpose

This document prevents connector placement from becoming arbitrary while the legacy Blender file is unavailable in the current session. It records what is known, what is deliberately unresolved, and which connector functions should remain grouped.

## Surface policy

- FRONT_Z0: display/touch only
- X_NEG / X_POS: side walls, 73.408 mm nominal wall length
- Y_NEG / Y_POS: long side walls, 121.008 mm nominal wall length
- REAR_Z30: rear face, 121.008 × 73.408 mm nominal

Every user-facing connector is forbidden from FRONT_Z0 in the current baseline.

## Relative legacy evidence

~~~text
RCA aperture diameter       11.88 mm
RCA center spacing          19.20 mm
two-RCA aperture span       31.08 mm
3.5 mm aperture diameter     6.97 mm
legacy dual-USB spacing     34.00 mm   (USB-C legacy reference only)
~~~

## What is still required

1. wall assignment for each cluster
2. absolute cutout center in M1_FRONT_CENTER
3. insertion axis
4. exact connector MPN and body/courtyard
5. mating-plug/card/finger clearance

Until those values exist, connector footprints and Edge.Cuts remain intentionally unfrozen.
