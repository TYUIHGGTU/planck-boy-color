# Validation

## Automated checks

Run:

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

The static validator compares RMK's direct-pin order against the ZMK
devicetree, verifies split geometry and offsets, checks both encoders and RGB
pin ownership, and rejects accidental `rgb_ug` or `ext_power` claims. The
artifact validator checks UF2 framing, nRF52840 family IDs, block numbering,
and application address ranges.

The revision validator derives each color's PWM channel from the ZMK DTSI and
compares it with the corresponding RMK profile. It also confirms that all 46
switch inputs remain active-low with pull-ups in both revisions.

## First hardware bring-up

These checks require the physical keyboard and cannot be inferred from source:

- Confirm the UF2 bootloader accepts an application beginning at `0x1000`.
- Confirm both halves can be recovered through UF2 or SWD before testing sleep.
- Repeat the matrix test with both the r1 and r2 firmware for the matching PCB.
- In Vial matrix test, press all 44 visible keys and both encoder push switches.
- Confirm the encoder pushes produce the same actions as the former ZMK
  composite positions.
- Turn both encoders one detent in each direction and verify volume direction.
- Pair all three host profiles; test profile selection, long-hold re-pair,
  next/previous profile, and current-profile clear.
- Confirm only the central advertises to the host and that r1 appears as
  `PlanckBoyColor R1 RMK`.
- Unplug USB and verify central-to-host BLE input from both halves.
- Power-cycle one half at a time and verify automatic split reconnection.
- Verify left and right Battery Service values are plausible.
- Let the keyboard enter idle sleep, then wake it from every half and record
  latency and current.
- Verify RGB channel order, layer colors, and sleep-off behavior on each half
  for both revision-specific firmware packages.
- Exercise all four layers and nine combos after clearing persisted storage.

## Expected observations

- Base layer: status LED off
- CHAR layer: amber status
- ARROW layer: blue status
- BLE layer: magenta status
- Sleeping: status LED off
- Peripheral wake while BLE subrating is active may take noticeably longer
  than a central-side wake; RMK documents a worst case near 232 ms while the
  host is connected.

Record board revision, bootloader version, measured idle current, and any
reversed encoder/RGB channel in this file when physical validation is run.
