# m1-firmware

Reserved for the native ESP32-P4 Pajoniiir-M1 production firmware binary.

This target is intentionally not a Cargo workspace member yet. The BSP/platform
contract and `esp-hal` integration are introduced separately so a host-only
skeleton cannot be mistaken for verified hardware support.

## Embedded baseline

- Rust target: `riscv32imafc-unknown-none-elf`
- HAL baseline: `esp-hal = 1.2.2`
- Chip feature: `esp32p4`
- ESP32-P4 silicon baseline: revision v3.x or newer
- USB OTG host and MIPI-DSI are treated as platform-only unstable APIs.
- Product crates remain HAL-independent and `no_std`; only the M1 platform/BSP
  layer may enable `esp-hal`'s `unstable` feature.

The production binary becomes a real Cargo target only when the platform crate
has a dedicated cross-compile gate. Until then, host CI validates product logic,
controller semantics, UI models and waveform rendering without making a false
hardware-verification claim.
