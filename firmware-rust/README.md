# Pajoniiir-M1 native Rust firmware

This directory is the new native Rust software workspace for Pajoniiir-M1.

The released Pajoniiir M2.2 product is the functional golden reference. The custom M1 hardware contracts in `../docs/` remain the electrical authority.

## Current phase

The initial workspace is intentionally host-first:

- `desktop-simulator` proves the Slint UI development path without ESP32-P4 hardware.
- `pajoniiir-core` contains shared product identifiers/state primitives.
- `pajoniiir-controller-core` establishes semantic controller events.
- `pajoniiir-ui-model` establishes immutable UI snapshot boundaries.
- `pajoniiir-waveform` establishes a no_std RGB565 waveform rasterizer.

The P4 firmware/BSP crates are deliberately not created as pretending-to-work hardware implementations. They are added after their boundary contracts are reviewed and will remain COMPILE_VERIFIED/HARDWARE_PENDING until M1 hardware exists.

## Toolchain

Starting baseline:

- Rust 1.95.0
- Slint 1.18.1
- embedded-graphics 0.8.2
- esp-hal 1.2.2 for the ESP32-P4 target integration
- target `riscv32imafc-unknown-none-elf`

The host workspace and standalone ESP32-P4 firmware `Cargo.lock` files are committed. CI resolves both graphs with `--locked`; dependency changes therefore require an explicit reviewed lockfile update.

## Host commands

From this directory:

```bash
cargo fmt --all --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
cargo run -p desktop-simulator
```

The simulator window is fixed at the product's initial 800x480 UI size.

## Verification rule

Host success must not be reported as hardware success.

Use these states in development evidence:

`HOST_VERIFIED -> SIMULATOR_VERIFIED -> COMPILE_VERIFIED -> HARDWARE_PENDING -> HARDWARE_VERIFIED`

See:

- `../docs/M1_RUST_PRODUCT_REQUIREMENTS.md`
- `../docs/M1_RUST_ARCHITECTURE.md`
- `../docs/adr/`
