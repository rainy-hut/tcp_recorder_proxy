from __future__ import annotations

from recorder_proxy.protocol.base import FramedMessage
from recorder_proxy.protocol.classification import MessageClassification
from recorder_proxy.protocol.text.mml_detector import extract_text, is_mml_text, is_probably_text


class TextFramer:
    def __init__(self, bbu_mml_mode: bool = False) -> None:
        self.bbu_mml_mode = bbu_mml_mode

    def feed(self, data: bytes) -> list[FramedMessage]:
        if not data:
            return []
        text, encoding = extract_text(data)
        if self.bbu_mml_mode and is_mml_text(data):
            classification = MessageClassification.BBU_MML_PLAIN
        elif is_probably_text(data):
            classification = MessageClassification.TEXT_COMMAND
        else:
            classification = MessageClassification.UNKNOWN_BINARY
        return [
            FramedMessage(
                data=data,
                classification=str(classification),
                parse_status="SUCCESS" if classification != MessageClassification.UNKNOWN_BINARY else "FAILED",
                decoded_summary={"encoding": encoding, "text_preview": text[:200]},
            )
        ]
