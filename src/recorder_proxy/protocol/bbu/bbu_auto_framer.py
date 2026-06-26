from __future__ import annotations

from recorder_proxy.protocol.base import FramedMessage
from recorder_proxy.protocol.bbu.bbu_binary_decoder import BbuBinaryDecoder
from recorder_proxy.protocol.bbu.bbu_mml_extractor import BbuMmlExtractor
from recorder_proxy.protocol.bbu.f634_framer import F634Framer
from recorder_proxy.protocol.classification import MessageClassification
from recorder_proxy.protocol.text.text_framer import TextFramer


class BbuAutoFramer:
    def __init__(self, max_frame_bytes: int) -> None:
        self.f634 = F634Framer(max_frame_bytes=max_frame_bytes)
        self.text = TextFramer(bbu_mml_mode=True)
        self.mml = BbuMmlExtractor()
        self.binary = BbuBinaryDecoder()

    def feed(self, data: bytes) -> list[FramedMessage]:
        if data.startswith(b"\xF6\x34") or self.f634.buffer:
            return [self._classify_frame(result.frame, result.error) for result in self.f634.feed(data)]
        return self.text.feed(data)

    def _classify_frame(self, frame: bytes, framing_error: str | None) -> FramedMessage:
        if framing_error is not None:
            return FramedMessage(frame, MessageClassification.UNKNOWN_BINARY.value, "FAILED", {}, framing_error)
        mml_text, encoding = self.mml.extract(frame)
        if mml_text:
            return FramedMessage(
                frame,
                MessageClassification.BBU_MML_FRAMED.value,
                "SUCCESS",
                {"mml_text": mml_text, "encoding": encoding, "outer_start_tag": "F634"},
            )
        try:
            summary = self.binary.decode(frame)
            return FramedMessage(frame, MessageClassification.BBU_BINARY.value, "PARTIAL_SUCCESS", summary)
        except Exception as exc:
            return FramedMessage(frame, MessageClassification.UNKNOWN_BINARY.value, "FAILED", {"outer_start_tag": "F634"}, str(exc))
