# Validation

## Automated checks

Run:

```sh
python3 tests/validate_config.py
cargo fmt --check
cargo build --release --bin central --bin peripheral
cargo make uf2
python3 tests/validate_artifacts.py
```

The static validator compares RMK's direct-pin order against the ZMK
devicetree, verifies split geometry and offsets, checks both encoders and RGB
pin ownership, and rejects accidental `rgb_ug` or `ext_power` claims. The
artifact validator checks UF2 framing, nRF52840 family IDs, block numbering,
and application address ranges.

## First hardware bring-up

These checks require the physical keyboard and cannot be inferred from source:

- Confirm the UF2 bootloader accepts an application beginning at `0x1000`.
- Confirm both halves can be recovered through UF2 or SWD before testing sleep.
- In Vial matrix test, press all 44 visible keys and both encoder push switches.
- Confirm the encoder pushes produce the same actions as the former ZMK
  composite positions.
- Turn both encoders one detent in each direction and verify volume direction.
- Pair all three host profiles; test profile selection, long-hold re-pair,
  next/previous profile, and current-profile clear.
- Unplug USB and verify central-to-host BLE input from both halves.
- Power-cycle one half at a time and verify automatic split reconnection.
- Verify left and right Battery Service values are plausible.
- Let the keyboard enter idle sleep, then wake it from every half and record
  latency and current.
- Verify RGB channel order, layer colors, and sleep-off behavior on each half.
- Exercise all four layers and nine combos after clearing persisted storage.

## Expected observations

- Base layer: cyan status
- CHAR layer: amber status
- ARROW layer: blue status
- BLE layer: magenta status
- Sleeping: status LED off
- Peripheral wake while BLE subrating is active may take noticeably longer
  than a central-side wake; RMK documents a worst case near 232 ms while the
  host is connected.

Record board revision, bootloader version, measured idle current, and any
reversed encoder/RGB channel in this file when physical validation is run.
