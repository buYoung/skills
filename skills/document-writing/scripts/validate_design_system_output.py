#!/usr/bin/env python3
"""Validate the structural owners of a saved Design System Document set."""

from __future__ import annotations

import argparse
import json
import struct
import sys
import zlib
from pathlib import Path
from typing import Any


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def inspect_png(path: Path) -> tuple[int, int, bool] | None:
    try:
        content = path.read_bytes()
    except OSError:
        return None
    if not content.startswith(PNG_SIGNATURE):
        return None
    position = len(PNG_SIGNATURE)
    chunks: list[tuple[bytes, bytes]] = []
    while position < len(content):
        if position + 12 > len(content):
            return None
        length = struct.unpack(">I", content[position:position + 4])[0]
        chunk_type = content[position + 4:position + 8]
        data_start = position + 8
        data_end = data_start + length
        crc_end = data_end + 4
        if crc_end > len(content):
            return None
        data = content[data_start:data_end]
        if struct.unpack(">I", content[data_end:crc_end])[0] != zlib.crc32(chunk_type + data) & 0xFFFFFFFF:
            return None
        chunks.append((chunk_type, data))
        position = crc_end
        if chunk_type == b"IEND":
            break
    if position != len(content) or not chunks or chunks[0][0] != b"IHDR" or len(chunks[0][1]) != 13 or chunks[-1] != (b"IEND", b""):
        return None
    width, height, bit_depth, color_type, compression, filter_method, interlace = struct.unpack(">IIBBBBB", chunks[0][1])
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(color_type)
    if width <= 0 or height <= 0 or channels is None or bit_depth not in {8, 16} or compression != 0 or filter_method != 0 or interlace != 0:
        return None
    compressed = b"".join(data for chunk_type, data in chunks if chunk_type == b"IDAT")
    try:
        decoded = zlib.decompress(compressed)
    except zlib.error:
        return None
    expected = height * (1 + ((width * channels * bit_depth + 7) // 8))
    if len(decoded) != expected:
        return None
    has_alpha = color_type in {4, 6} or any(chunk_type == b"tRNS" for chunk_type, _data in chunks)
    return width, height, has_alpha


def validate(
    root: Path,
    prebuilt: str,
    stores: list[str],
    platforms: list[str],
    png_count: int | None,
    png_width: int | None,
    png_height: int | None,
    png_alpha: bool | None,
) -> dict[str, Any]:
    checks: list[str] = []
    failures: list[str] = []

    def check(condition: bool, text: str) -> None:
        (checks if condition else failures).append(text)

    check(root.is_dir(), "document root exists")
    if not root.is_dir():
        return {"checks": checks, "failures": failures}
    check((root / "index.md").is_file(), "new saved set owns index.md")
    check(not ((root / "README.md").is_file() and not (root / "index.md").is_file()), "README.md does not replace index.md")
    if prebuilt == "app-store-page":
        for store in stores:
            check((root / "stores" / f"{store}.md").is_file(), f"store owner exists: stores/{store}.md")
    elif prebuilt == "default":
        for platform in platforms:
            check((root / "platforms" / f"{platform}.md").is_file(), f"platform owner exists: platforms/{platform}.md")
    else:
        failures.append(f"unsupported prebuilt: {prebuilt}")
    if png_count is not None:
        png_files = sorted(root.glob("*.png"))
        check(len(png_files) == png_count, f"document root contains exactly {png_count} PNG file(s)")
        if len(png_files) == png_count == 1:
            inspected = inspect_png(png_files[0])
            check(inspected is not None, "PNG is structurally complete")
            if inspected is not None:
                width, height, has_alpha = inspected
                if png_width is not None:
                    check(width == png_width, f"PNG width is {png_width}")
                if png_height is not None:
                    check(height == png_height, f"PNG height is {png_height}")
                if png_alpha is not None:
                    check(has_alpha is png_alpha, f"PNG alpha is {png_alpha}")
    return {"checks": checks, "failures": failures}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root")
    parser.add_argument("--prebuilt", choices=("default", "app-store-page"), required=True)
    parser.add_argument("--store", action="append", default=[])
    parser.add_argument("--platform", action="append", default=[])
    parser.add_argument("--png-count", type=int)
    parser.add_argument("--png-width", type=int)
    parser.add_argument("--png-height", type=int)
    parser.add_argument("--png-alpha", choices=("true", "false"))
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args()
    result = validate(
        Path(args.root),
        args.prebuilt,
        args.store,
        args.platform,
        args.png_count,
        args.png_width,
        args.png_height,
        None if args.png_alpha is None else args.png_alpha == "true",
    )
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for item in result["checks"]:
            print(f"PASS: {item}")
        for item in result["failures"]:
            print(f"FAIL: {item}")
    return 1 if result["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
