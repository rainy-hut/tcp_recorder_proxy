from __future__ import annotations

import re

from recorder_proxy.utils.encoding_utils import decode_text_lossy


class BbuMmlExtractor:
    _pattern = re.compile(rb"(SHK\s+HAND|LGI(?:\s+REQUEST)?|LST|DSP|SET|ADD|RMV|MOD|neg\s+opt:)", re.IGNORECASE)

    def extract(self, frame: bytes) -> tuple[str | None, str | None]:
        if not self._pattern.search(frame):
            return None, None
        text, encoding = decode_text_lossy(frame)
        matches = re.findall(r"([A-Z]{2,4}(?:\s+[A-Z]+)?\s*:[^;\r\n]*;|neg\s+opt:[^;\r\n]*;)", text, re.IGNORECASE)
        if matches:
            return "\n".join(matches), encoding
        return text, encoding
