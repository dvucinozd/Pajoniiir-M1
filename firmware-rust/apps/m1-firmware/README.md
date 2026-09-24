# m1-firmware

Reserved for the native ESP32-P4 Pajoniiir-M1 production firmware binary.

This target is intentionally not a Cargo workspace member in the foundation commit. The BSP/platform contract and esp-hal integration will be introduced separately so a host-only skeleton cannot be mistaken for verified hardware support.

Planned target: `riscv32imafc-unknown-none-elf`.

Initial platform dependency baseline: `esp-hal 1.2.0`, with all required unstable P4 APIs isolated behind M1 platform crates.
