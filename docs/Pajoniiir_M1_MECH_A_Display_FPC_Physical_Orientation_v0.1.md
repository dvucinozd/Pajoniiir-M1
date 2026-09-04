# Pajoniiir-M1 — M1-MECH-A Display FPC Physical Orientation v0.1

> **SUPERSEDED DISPLAY FORENSICS.** This orientation result belongs to the retired 30-pin display path and must not be applied to active J6. Use the B5 status and DSI15 connector-lock documents.

**Datum:** 2026-09-03  
**Revision:** M1-MECH-A10  
**Status:** Original insertion architecture confirmed; contact-side and exact height remain open

## Confirmed from manufacturer photo

The official Guition specification page 5 shows the original JC4880 PCB with the LCD flex installed.

Safely confirmed:

- connector is on the PCB component side,
- connector is right-angle / side-entry,
- flex approaches laterally, approximately parallel to the PCB plane.

## Not confirmed

The photo is not a dimensional connector drawing. It does not justify a production lock for:

- top-contact vs bottom-contact,
- housing height,
- mated FPC Z height,
- exact land pattern,
- final purchased panel-tail dimensions.

The JLC component record confirms only SOFNG `0.5TBQP-30P-1`, 30 contacts and 0.5 mm pitch; it does not publish the missing mechanical fields.

## Gate consequence

The former generic “FPC insertion geometry” unknown is narrowed to:

~~~text
known:    component-side right-angle side-entry
unknown:  top/bottom contact-side
unknown:  exact housing/mated height
unknown:  final panel tail geometry
~~~

J_LCD remains intentionally uninstantiated.

## Sources

- Guition manufacturer specification, page 5: https://www.guition.com/icms/upload/fb081940d6fc11f09850077a33e1404f/FTPData/UEditor/file/2026121/1768961095795/JC4880P443C_I_W%20Specifications-EN-V1.0.pdf
- JLCPCB SOFNG component record: https://jlcpcb.com/partdetail/SOFNG-0_5TBQP_30P1/C3975120
