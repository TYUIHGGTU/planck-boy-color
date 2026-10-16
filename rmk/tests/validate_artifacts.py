#!/usr/bin/env python3
"""Validate generated UF2 block structure and flash address boundaries."""

from __future__ import annotations

import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UF2_MAGIC_START0 = 0x0A324655
UF2_MAGIC_START1 = 0x9E5D5157
UF2_MAGIC_END = 0x0AB16F30
UF2_FLAG_FAMILY_ID = 0x00002000
NRF52840_FAMILY_ID = 0xADA52840
APP_START = 0x00001000
APP_END = 0x000D4000


def validate_uf2(path: Path) -> tuple[int, int, int]:
    data = path.read_bytes()
    if not data or len(data) % 512:
        raise ValueError(f"{path.name}: size is not a non-zero multiple of 512")

    starts: list[int] = []
    ends: list[int] = []
    expected_blocks = len(data) // 512

    for index in range(expected_blocks):
        block = data[index * 512 : (index + 1) * 512]
        magic0, magic1, flags, target, payload_size, block_no, block_count, family = (
            struct.unpack_from("<IIIIIIII", block)
        )
        magic_end = struct.unpack_from("<I", block, 508)[0]

        if (magic0, magic1, magic_end) != (
            UF2_MAGIC_START0,
            UF2_MAGIC_START1,
            UF2_MAGIC_END,
        ):
            raise ValueError(f"{path.name}: invalid UF2 magic in block {index}")
        if block_no != index or block_count != expected_blocks:
            raise ValueError(f"{path.name}: inconsistent block numbering")
        if not flags & UF2_FLAG_FAMILY_ID or family != NRF52840_FAMILY_ID:
            raise ValueError(f"{path.name}: incorrect nRF52840 family ID")
        if payload_size > 476:
            raise ValueError(f"{path.name}: oversized payload in block {index}")

        starts.append(target)
        ends.append(target + payload_size)

    image_start = min(starts)
    image_end = max(ends)
    if image_start < APP_START or image_end > APP_END:
        raise ValueError(
            f"{path.name}: image range 0x{image_start:X}..0x{image_end:X} "
            f"escapes 0x{APP_START:X}..0x{APP_END:X}"
        )

    return expected_blocks, image_start, image_end


def main() -> int:
    for half in ("central", "peripheral"):
        stem = f"planck-boy-color-{half}"
        hex_path = ROOT / f"{stem}.hex"
        uf2_path = ROOT / f"{stem}.uf2"
        if not hex_path.is_file():
            raise FileNotFoundError(hex_path)
        blocks, start, end = validate_uf2(uf2_path)
        print(f"{uf2_path.name}: {blocks} blocks, 0x{start:X}..0x{end:X}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (FileNotFoundError, ValueError) as error:
        print(f"artifact validation failed: {error}", file=sys.stderr)
        sys.exit(1)
