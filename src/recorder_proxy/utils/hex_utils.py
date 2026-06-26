from __future__ import annotations

import hashlib


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def raw_hex(data: bytes, limit: int | None = None) -> str:
    view = data if limit is None else data[:limit]
    suffix = "" if limit is None or len(data) <= limit else "...truncated"
    return view.hex() + suffix
