from __future__ import annotations

from recorder_proxy.protocol.text.mml_detector import is_response_end


class ResponseBoundaryDetector:
    def is_complete(self, text: str) -> bool:
        return is_response_end(text)
