#!/usr/bin/env python3
"""Static consistency checks for the ZMK-to-RMK hardware translation."""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LEFT_MAIN = [
    "P0_28",
    "P0_05",
    "P0_04",
    "P0_21",
    "P0_19",
    "P0_16",
    "P0_27",
    "P0_25",
    "P0_23",
    "P0_14",
    "P0_13",
    "P0_15",
    "P0_30",
    "P0_03",
    "P1_12",
    "P1_11",
    "P1_05",
    "P1_13",
    "P0_29",
    "P0_02",
    "P1_15",
    "P1_10",
]

RIGHT_MAIN = [
    "P1_10",
    "P1_13",
    "P1_15",
    "P0_02",
    "P0_29",
    "P0_31",
    "P1_11",
    "P0_26",
    "P0_04",
    "P0_06",
    "P0_08",
    "P1_09",
    "P1_04",
    "P1_01",
    "P0_20",
    "P0_07",
    "P1_08",
    "P0_11",
    "P1_02",
    "P1_00",
    "P0_17",
    "P0_15",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def populated_pins(matrix: dict) -> list[str]:
    return [
        pin
        for row in matrix["direct_pins"]
        for pin in row
        if pin not in {"_", "trns"}
    ]


def main() -> int:
    with (ROOT / "keyboard.toml").open("rb") as config_file:
        config = tomllib.load(config_file)

    require(config["keyboard"]["chip"] == "nrf52840", "MCU must be nRF52840")
    require(config["split"]["connection"] == "ble", "split transport must be BLE")

    central = config["split"]["central"]
    peripheral = config["split"]["peripheral"][0]
    require(
        (central["rows"], central["cols"], central["row_offset"], central["col_offset"])
        == (5, 6, 0, 0),
        "central split geometry changed",
    )
    require(
        (
            peripheral["rows"],
            peripheral["cols"],
            peripheral["row_offset"],
            peripheral["col_offset"],
        )
        == (5, 6, 0, 6),
        "peripheral split geometry changed",
    )

    for name, half in (("central", central), ("peripheral", peripheral)):
        matrix = half["matrix"]
        require(matrix["matrix_type"] == "direct_pin", f"{name} is not direct-pin")
        require(matrix["direct_pin_low_active"], f"{name} must remain active-low")
        require(matrix["bootmagic"] == [0, 0], f"{name} bootmagic changed")

    require(
        populated_pins(central["matrix"]) == LEFT_MAIN + ["P0_31"],
        "left direct-pin order no longer matches ZMK",
    )
    require(
        populated_pins(peripheral["matrix"]) == RIGHT_MAIN + ["P0_13"],
        "right direct-pin order no longer matches ZMK",
    )

    left_encoder = central["input_device"]["encoder"][0]
    right_encoder = peripheral["input_device"]["encoder"][0]
    require(
        (left_encoder["pin_a"], left_encoder["pin_b"]) == ("P1_02", "P1_07"),
        "left encoder pins changed",
    )
    require(
        (right_encoder["pin_a"], right_encoder["pin_b"]) == ("P0_24", "P0_22"),
        "right encoder pins changed",
    )
    require(
        left_encoder["resolution"] == {"detent": 30, "pulse": 15}
        and right_encoder["resolution"] == {"detent": 30, "pulse": 15},
        "encoder resolution no longer matches ZMK",
    )

    require(
        central["battery_adc_pin"] == "vddh"
        and peripheral["battery_adc_pin"] == "vddh",
        "both halves must use VDDH battery measurement",
    )
    require(config["storage"]["start_addr"] == 0xD4000, "storage start changed")
    require(config["storage"]["num_sectors"] == 32, "storage size changed")

    layers = config["keymap"]["layer"]
    require(len(layers) == 4, "expected four keymap layers")
    require(
        [layer["name"] for layer in layers] == ["LETTER", "CHAR", "ARROW", "BLE"],
        "keymap layer order changed",
    )
    require(len(config["behavior"]["combo"]["combos"]) == 9, "expected nine combos")
    require(
        len(config["behavior"]["morse"]["morses"]) == 3,
        "expected three retained tap-dance definitions",
    )

    with (ROOT / "Cargo.toml").open("rb") as cargo_file:
        cargo = tomllib.load(cargo_file)
    require(
        cargo["features"]["default"] == ["hw-r2"],
        "default hardware revision must remain r2",
    )
    require(
        {"hw-r1", "hw-r2"}.issubset(cargo["features"]),
        "Cargo hardware revision features are incomplete",
    )
    build_script = (ROOT / "build.rs").read_text()
    require(
        'name = "PlanckBoyColor R1 RMK"' in build_script
        and 'product_name = "PlanckBoyColor R1 RMK"' in build_script,
        "r1 Bluetooth product name override is missing",
    )
    require(
        "cargo:rustc-env=KEYBOARD_TOML_PATH=" in build_script,
        "generated revision keyboard config is not exported to RMK",
    )

    raw_config = (ROOT / "keyboard.toml").read_text().lower()
    require("rgb_ug" not in raw_config, "undocumented underglow must stay disabled")
    require("ext_power" not in raw_config, "undocumented ext-power must stay disabled")

    memory = (ROOT / "memory.x").read_text()
    require("ORIGIN = 0x00001000" in memory, "application origin changed")
    require("LENGTH = 844K" in memory, "application partition length changed")

    print("RMK configuration is consistent with the ZMK hardware map.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (AssertionError, KeyError, tomllib.TOMLDecodeError) as error:
        print(f"validation failed: {error}", file=sys.stderr)
        sys.exit(1)
