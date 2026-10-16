#!/usr/bin/env python3
"""Cross-check ZMK revision DTSI files against RMK RGB profiles."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BOARD = ROOT / "config" / "boards" / "arm" / "planck"
RMK_REVISIONS = ROOT / "rmk" / "src" / "revisions"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def parse_zmk_leds(path: Path) -> tuple[list[str], dict[str, int]]:
    text = path.read_text()
    psel_matches = re.findall(
        r"NRF_PSEL\(PWM_OUT(\d),\s*(\d),\s*(\d+)\)", text
    )
    require(len(psel_matches) == 6, f"{path}: expected default and sleep PSELs")
    default_psels = psel_matches[:3]
    require(
        psel_matches[3:] == default_psels,
        f"{path}: sleep PWM mapping differs from default",
    )
    require(
        [int(channel) for channel, _, _ in default_psels] == [0, 1, 2],
        f"{path}: PWM channels must be ordered 0, 1, 2",
    )
    pwm_pins = [f"P{port}_{int(pin):02d}" for _, port, pin in default_psels]

    aliases = dict(
        re.findall(r"led-(red|green|blue)\s*=\s*&([A-Za-z0-9_]+);", text)
    )
    node_pins = {
        label: f"P{port}_{int(pin):02d}"
        for label, port, pin in re.findall(
            r"([A-Za-z0-9_]+):\s+led_\d+\s*\{\s*"
            r"gpios\s*=\s*<&gpio(\d)\s+(\d+)",
            text,
            flags=re.DOTALL,
        )
    }
    require(set(aliases) == {"red", "green", "blue"}, f"{path}: RGB aliases missing")
    color_channels = {
        color: pwm_pins.index(node_pins[label]) for color, label in aliases.items()
    }
    return pwm_pins, color_channels


def macro_body(text: str, name: str) -> str:
    match = re.search(
        rf"macro_rules!\s+{name}\s*\{{(.*?)\n\}}\n",
        text,
        flags=re.DOTALL,
    )
    require(match is not None, f"missing RMK macro {name}")
    return match.group(1)


def parse_rmk_profile(path: Path, half: str) -> tuple[list[str], dict[str, int]]:
    body = macro_body(path.read_text(), f"{half}_processor")
    pins = re.findall(r"\$p\.(P[01]_\d{2})", body)
    require(len(pins) == 3, f"{path}: {half} must configure three PWM pins")
    channels = {
        color: int(value)
        for color, value in re.findall(r"(red|green|blue):\s*(\d)", body)
    }
    require(
        set(channels) == {"red", "green", "blue"},
        f"{path}: {half} RGB channel map incomplete",
    )
    return pins, channels


def validate_revision(revision: str) -> None:
    profile = RMK_REVISIONS / f"{revision}.rs"
    for side, half in (("left", "central"), ("right", "peripheral")):
        zmk_pins, zmk_channels = parse_zmk_leds(
            BOARD / "revisions" / revision / f"leds_{side}.dtsi"
        )
        rmk_pins, rmk_channels = parse_rmk_profile(profile, half)
        require(
            rmk_pins == zmk_pins,
            f"{revision} {side}: RMK PWM pin order {rmk_pins} != ZMK {zmk_pins}",
        )
        require(
            rmk_channels == zmk_channels,
            f"{revision} {side}: RMK RGB channels {rmk_channels} != ZMK {zmk_channels}",
        )


def main() -> int:
    for common in ("planck_left_common.dtsi", "planck_right_common.dtsi"):
        text = (BOARD / common).read_text()
        require(
            text.count("GPIO_ACTIVE_LOW | GPIO_PULL_UP") == 23,
            f"{common}: expected 22 keys plus one encoder push, all active-low",
        )

    board_yml = (BOARD / "board.yml").read_text()
    for revision in ("r1", "r2"):
        validate_revision(revision)
        build_matrix = (ROOT / "build" / "zmk" / f"{revision}.yaml").read_text()
        for side in ("left", "right"):
            board_name = f"planck_{side}_{revision}"
            require(board_name in board_yml, f"board.yml missing {board_name}")
            require(
                f"board: {board_name}" in build_matrix,
                f"build/zmk/{revision}.yaml missing {board_name}",
            )
            wrapper = (BOARD / f"{board_name}.dts").read_text()
            require(
                f'revisions/{revision}/leds_{side}.dtsi' in wrapper,
                f"{board_name}.dts selects the wrong revision",
            )
            require(
                (BOARD / f"{board_name}_defconfig").is_file(),
                f"missing {board_name}_defconfig",
            )
            require(
                (BOARD / f"Kconfig.{board_name}").is_file(),
                f"missing Kconfig.{board_name}",
            )

    print("ZMK and RMK hardware revision profiles are consistent.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (AssertionError, ValueError) as error:
        print(f"revision validation failed: {error}", file=sys.stderr)
        sys.exit(1)
