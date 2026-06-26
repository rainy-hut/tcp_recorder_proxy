from __future__ import annotations

import binascii
import struct
import zlib
from pathlib import Path


def _png_chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", binascii.crc32(kind + payload) & 0xFFFFFFFF)
    )


def _png_rgba(size: int) -> bytes:
    rows = []
    for y in range(size):
        row = bytearray([0])
        for x in range(size):
            nx = (x + 0.5) / size
            ny = (y + 0.5) / size
            radius = min(size * 0.23, 18)
            inside_round_rect = (
                radius <= x < size - radius
                or radius <= y < size - radius
                or min(
                    (x - radius) ** 2 + (y - radius) ** 2,
                    (x - (size - radius)) ** 2 + (y - radius) ** 2,
                    (x - radius) ** 2 + (y - (size - radius)) ** 2,
                    (x - (size - radius)) ** 2 + (y - (size - radius)) ** 2,
                )
                <= radius**2
            )
            if not inside_round_rect:
                row.extend((0, 0, 0, 0))
                continue
            blue = int(235 - 150 * ny)
            green = int(99 - 40 * nx)
            red = int(37 - 20 * ny)
            alpha = 255
            band = abs(y - (size * 0.54 + size * 0.12 * _zigzag(nx)))
            if band < max(1.5, size * 0.035):
                red, green, blue = 56, 189, 248
            if size * 0.18 < y < size * 0.27 and size * 0.18 < x < size * 0.58:
                dot = int((x - size * 0.18) // max(1, size * 0.12))
                cx = size * (0.23 + dot * 0.13)
                cy = size * 0.225
                if (x - cx) ** 2 + (y - cy) ** 2 < (size * 0.035) ** 2:
                    red, green, blue = (167, 243, 208) if dot == 0 else (255, 255, 255)
            row.extend((red, green, blue, alpha))
        rows.append(bytes(row))
    raw = b"".join(rows)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
        + _png_chunk(b"IDAT", zlib.compress(raw, 9))
        + _png_chunk(b"IEND", b"")
    )


def _zigzag(x: float) -> float:
    if x < 0.24:
        return 0.0
    if x < 0.36:
        return -1.0 + (x - 0.24) / 0.12 * 2.4
    if x < 0.52:
        return 1.4 - (x - 0.36) / 0.16 * 2.2
    if x < 0.66:
        return -0.8 + (x - 0.52) / 0.14 * 1.8
    return 0.0


def write_ico(path: Path) -> None:
    images = [(size, _png_rgba(size)) for size in (16, 32, 48, 256)]
    header = struct.pack("<HHH", 0, 1, len(images))
    directory = bytearray()
    offset = 6 + 16 * len(images)
    payloads = []
    for size, png in images:
        directory.extend(
            struct.pack(
                "<BBBBHHII",
                0 if size == 256 else size,
                0 if size == 256 else size,
                0,
                0,
                1,
                32,
                len(png),
                offset,
            )
        )
        payloads.append(png)
        offset += len(png)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(header + bytes(directory) + b"".join(payloads))


if __name__ == "__main__":
    write_ico(Path(__file__).resolve().parents[1] / "build" / "app_icon.ico")
