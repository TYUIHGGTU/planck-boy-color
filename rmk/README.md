# PlanckBoy Color RMK firmware

RMK 0.9.0 firmware for the nRF52840 PlanckBoy Color split keyboard. The left
half is the BLE central and USB device; the right half is BLE peripheral 0.

## Implemented

- 44 active-low direct-pin keys plus both encoder push switches
- BLE split, USB/BLE host transport, three host profiles
- VDDH battery reporting on both halves
- two EC11 encoders
- four ZMK-derived layers and nine base-layer combos
- Vial dynamic keymap support
- 60-minute idle sleep with interrupt-driven matrix wakeup
- per-half, three-channel PWM RGB layer status
- UF2, Intel HEX, and ELF outputs

The encoder push switches are separate inputs in RMK. Their actions duplicate
the ZMK composite positions that they previously shared.

## Prerequisites

Install Rust through rustup. The repository pins the target and LLVM tools in
`rust-toolchain.toml`. UF2 packaging additionally needs `cargo-make`; its tasks
install `cargo-binutils`, `flip-link`, and `cargo-hex-to-uf2` when missing.
RMK's nRF BLE crypto dependency also requires `arm-none-eabi-gcc`.

```sh
# macOS
brew tap osx-cross/arm
brew trust --formula osx-cross/arm/arm-gcc-bin@14
brew install osx-cross/arm/arm-gcc-bin@14
export PATH="$(brew --prefix arm-gcc-bin@14)/bin:$PATH"
cargo install cargo-make
```

## Validate and build

From this directory:

```sh
python3 tests/validate_config.py
cargo fmt --check
cargo build --release --bin central --bin peripheral
cargo make uf2
python3 tests/validate_artifacts.py
```

Generated files:

- `target/thumbv7em-none-eabihf/release/central`
- `target/thumbv7em-none-eabihf/release/peripheral`
- `planck-boy-color-central.hex`
- `planck-boy-color-central.uf2`
- `planck-boy-color-peripheral.hex`
- `planck-boy-color-peripheral.uf2`

## Flashing

1. Keep a known-good ZMK UF2 and an SWD probe available for first bring-up.
2. Put only the target half into its UF2 bootloader.
3. Flash `planck-boy-color-central.uf2` to the left half and
   `planck-boy-color-peripheral.uf2` to the right half.
4. Reboot both halves. Clear stored split peers if they do not discover each
   other after a firmware change.
5. Clear RMK storage after changing the compiled default keymap, otherwise a
   Vial-saved keymap can override it.

Both halves define bootmagic at their local matrix `(0,0)`. Hold that switch
while resetting to request the Adafruit-compatible bootloader.

The linker and storage boundaries intentionally match the ZMK
`nrf52840-nosd` layout. If the installed bootloader is not the one represented
by `config/boards/arm/planck/planck.dtsi`, stop and update `memory.x` before
flashing.

## BLE layer

RMK uses `User` actions for wireless management:

- `User0` to `User2`: select profile; hold five seconds to clear and pair it
- `User3`: next profile
- `User4`: previous profile
- `User5`: clear current profile
- `User6`: switch preferred USB/BLE output
- `User7`: hold to clear the split peer

The old ZMK discovery keys map to the corresponding profile key because RMK
performs clear-and-pair through a long hold. RGB and external-power positions
are `No` because the original repository does not define that hardware.

## Current compatibility differences

- ZMK Studio is replaced by Vial.
- RMK TOML combos match actions rather than raw physical positions, so the nine
  migrated desktop/layer combos are explicitly limited to layer 0.
- The three tap-dance definitions are retained as RMK Morse definitions, but
  remain unbound because the ZMK keymap also never references them.
- Underglow and dynamic external-power control are not implemented.

See `HARDWARE.md` for the pin-by-pin translation and `VALIDATION.md` for the
bring-up checklist.
