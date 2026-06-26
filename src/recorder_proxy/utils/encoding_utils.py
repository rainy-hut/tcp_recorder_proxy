from __future__ import annotations


def decode_text_lossy(data: bytes) -> tuple[str, str]:
    for encoding in ("utf-8", "gb18030", "latin-1"):
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace"), "utf-8-replace"
