# PlanckBoy Color hardware map

This document is the translation boundary between the original ZMK devicetree
and RMK. GPIO names use Embassy's nRF52 spelling.

## Platform

- MCU: one nRF52840 per half
- Split transport: BLE
- Central: left half
- Switch wiring: one GPIO per switch, active low, internal pull-up
- Power measurement: nRF VDDH
- USB: enabled on the central
- DCDC REG0 and REG1: enabled, matching the ZMK board configuration

The `origin/r1` and r2 sources use the same direct-pin GPIOs and the same
`GPIO_ACTIVE_LOW | GPIO_PULL_UP` flags. There is currently no source evidence
for a switch-polarity difference between revisions.

## Flash layout

- `0x00000000..0x00001000`: MBR/reserved
- `0x00001000..0x000D4000`: application, 844 KiB
- `0x000D4000..0x000F4000`: RMK storage, 128 KiB
- `0x000F4000..0x00100000`: existing UF2 bootloader, 48 KiB

These boundaries are the effective result of the ZMK `nrf52840-nosd` snippet
applied to the board devicetree. Do not flash an RMK image built for a different
origin until the installed bootloader has been checked over SWD.

## Direct-pin switches

The first four rows are the visible keyboard. The fifth row carries the encoder
push switch and is hidden from the rendered layout. `-` is an unused matrix
cell.

Left/central:

```text
P0_28 P0_05 P0_04 P0_21 P0_19 P0_16
P0_27 P0_25 P0_23 P0_14 P0_13 P0_15
P0_30 P0_03 P1_12 P1_11 P1_05 P1_13
-     -     P0_29 P0_02 P1_15 P1_10
P0_31 -     -     -     -     -
```

Right/peripheral:

```text
P1_10 P1_13 P1_15 P0_02 P0_29 P0_31
P1_11 P0_26 P0_04 P0_06 P0_08 P1_09
P1_04 P1_01 P0_20 P0_07 P1_08 P0_11
P1_02 P1_00 P0_17 P0_15 -     -
P0_13 -     -     -     -     -
```

The ZMK composite scanner aliases the left encoder push to its local position
18 and the right push to local position 21. RMK models the two physical inputs
separately and duplicates those actions on every layer.

## Rotary encoders

- Left A/B: `P1_02`, `P1_07`
- Right A/B: `P0_24`, `P0_22`
- Mechanical detents: 30
- Quadrature pulses: 15
- RMK resolution: 2 transitions per detent

The configured direction follows the original ZMK bindings. Reverse the
individual encoder in `keyboard.toml` if physical testing reports the opposite
direction.

## RGB status LED

Both halves use nRF PWM0 with inverted polarity.

- Left channels: blue `P0_09`, red `P1_06`, green `P1_04`
- Right channels: blue `P1_03`, red `P1_05`, green `P1_07`

The physical color pins are shared, but the ZMK PWM channel order differs:

- r1 left: blue, red, green; r1 right: blue, green, red
- r2 left: red, green, blue; r2 right: green, red, blue

ZMK stores these mappings under
`config/boards/arm/planck/revisions/{r1,r2}`. RMK mirrors them through the
mutually exclusive `hw-r1` and `hw-r2` Cargo features. The default feature is
`hw-r2` for compatibility with the previously validated firmware.

The RMK processor displays the active layer and turns the LED off for a sleep
event. It does not implement the ZMK `rgb_ug` actions: the repository contains
no underglow device, LED count, data/clock pins, or power-enable pin.

## Intentionally unsupported hardware

- `ext_power`: enabled in Kconfig but no GPIO/regulator node exists
- `rgb_ug`: keycodes exist but no underglow hardware node exists
- display: disabled and no display node exists

Add these only after confirming the schematic or PCB traces. Guessing any of
these pins can damage the board or increase sleep current.
