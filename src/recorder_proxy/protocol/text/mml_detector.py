from __future__ import annotations

import re

from recorder_proxy.utils.encoding_utils import decode_text_lossy

MML_PATTERN = re.compile(
    r"\b(SHK\s+HAND|LGI(?:\s+REQUEST)?|LST|DSP|SET|ADD|RMV|MOD|ACT|DEA|RST)\b|neg\s+opt:",
    re.IGNORECASE,
)


def is_probably_text(data: bytes) -> bool:
    if not data:
        return False
    printable = sum(1 for byte in data if byte in (9, 10, 13) or 32 <= byte <= 126 or byte >= 0x80)
    return printable / len(data) > 0.80


def extract_text(data: bytes) -> tuple[str, str]:
    return decode_text_lossy(data)


def is_mml_text(data: bytes) -> bool:
    text, _ = extract_text(data)
    return bool(MML_PATTERN.search(text))


def is_response_end(text: str) -> bool:
    return "---    END" in text or text.rstrip().endswith((">", "#", "$"))
