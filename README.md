# PlanckBoy Color firmware

This repository builds ZMK and RMK firmware for PlanckBoy Color hardware
revisions r1 and r2.

## Build outputs

One GitHub Actions run publishes four artifacts:

- `planck-boy-color-zmk-r1`
- `planck-boy-color-zmk-r2`
- `planck-boy-color-rmk-r1`
- `planck-boy-color-rmk-r2`

Each artifact contains separate left/right images. ZMK calls them `left` and
`right`; RMK calls them `central` and `peripheral`.

Do not mix revisions or firmware frameworks between halves.

## Source layout

- `config/`: shared ZMK keymap and board configuration
- `config/boards/arm/planck/revisions/r1`: r1 RGB PWM mapping
- `config/boards/arm/planck/revisions/r2`: r2 RGB PWM mapping
- `build/zmk/r1.yaml`, `build/zmk/r2.yaml`: ZMK build matrices
- `rmk/`: shared RMK firmware
- `rmk/src/revisions/r1.rs`, `rmk/src/revisions/r2.rs`: RMK RGB profiles

The two revisions share the same key matrix, active-low switch wiring,
encoders, battery measurement, keymap, and flash layout. The repository only
shows a difference in RGB PWM channel order. r2 ZMK additionally enables the
USB ZMK Studio transport on the left half.

For RMK build and flashing instructions, see `rmk/README.md`.
