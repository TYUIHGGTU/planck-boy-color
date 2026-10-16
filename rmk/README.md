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

## Hardware revisions

The matrix, encoders, keymap, battery input, and flash layout are shared by r1
and r2. Only the RGB PWM channel order differs in the repository.

- `hw-r1`: mirrors `config/boards/arm/planck/revisions/r1`
- `hw-r2`: mirrors `config/boards/arm/planck/revisions/r2` and is the default

Select exactly one feature for explicit builds. The build fails if both or
neither are selected.

The RMK central names follow the hardware revision:

- r1: `PBC R1`
- r2: `PBC R2`

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
python3 tests/validate_hardware_revisions.py
cargo fmt --check

cargo build --release --bin central --bin peripheral \
  --no-default-features --features hw-r1
RMK_REVISION=r1 cargo make uf2
python3 tests/validate_artifacts.py --revision r1

cargo build --release --bin central --bin peripheral \
  --no-default-features --features hw-r2
RMK_REVISION=r2 cargo make uf2
python3 tests/validate_artifacts.py --revision r2
```

Generated files:

- `target/thumbv7em-none-eabihf/release/central`
- `target/thumbv7em-none-eabihf/release/peripheral`
- `planck-boy-color-rmk-r1-central.{hex,uf2}`
- `planck-boy-color-rmk-r1-peripheral.{hex,uf2}`
- `planck-boy-color-rmk-r2-central.{hex,uf2}`
- `planck-boy-color-rmk-r2-peripheral.{hex,uf2}`

GitHub Actions also publishes `planck-boy-color-zmk-r1`,
`planck-boy-color-zmk-r2`, `planck-boy-color-rmk-r1`, and
`planck-boy-color-rmk-r2` artifacts in one workflow run.

## Flashing

1. Keep a known-good ZMK UF2 and an SWD probe available for first bring-up.
2. Put only the target half into its UF2 bootloader.
3. Choose the artifact matching the PCB revision. Flash its `central` image to
   the left half and its `peripheral` image to the right half.
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

## Bluetooth discovery troubleshooting

- RMK 0.9's legacy host advertisement has room for at most 16 name bytes after
  its required fields. A longer product name prevents advertising entirely.
- Only the RMK `central` image advertises to phones and computers. The
  `peripheral` image only searches for its central half and will never appear
  in the host's Bluetooth device list.
- Flashing UF2 does not erase the storage partition. Remove the old keyboard
  from the host, activate the BLE layer, then hold the desired `User0` to
  `User2` profile key for five seconds to clear that bond and advertise again.
- Ensure both halves use the same framework and hardware revision. Power-cycle
  both halves after flashing.
- If r2 advertises on the same physical board but r1 does not, capture a defmt
  log or erase RMK storage before changing radio settings; r1/r2 currently use
  identical BLE, DCDC, TX-power, PHY, matrix, and battery configuration.

## Current compatibility differences

- ZMK Studio is replaced by Vial.
- RMK TOML combos match actions rather than raw physical positions, so the nine
  migrated desktop/layer combos are explicitly limited to layer 0.
- The three tap-dance definitions are retained as RMK Morse definitions, but
  remain unbound because the ZMK keymap also never references them.
- Underglow and dynamic external-power control are not implemented.

See `HARDWARE.md` for the pin-by-pin translation and `VALIDATION.md` for the
bring-up checklist.
