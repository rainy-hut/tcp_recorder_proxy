from __future__ import annotations

import asyncio
from dataclasses import dataclass

from recorder_proxy.recording.models import ParsedMessage, RawCaptureEvent


@dataclass
class QueueStats:
    raw_dropped: int = 0
    parse_dropped: int = 0


class RecordingQueues:
    def __init__(self, raw_size: int, parse_size: int) -> None:
        self.raw: asyncio.Queue[RawCaptureEvent | None] = asyncio.Queue(maxsize=raw_size)
        self.parse: asyncio.Queue[RawCaptureEvent | None] = asyncio.Queue(maxsize=parse_size)
        self.parsed_messages: asyncio.Queue[ParsedMessage | None] = asyncio.Queue()
        self.stats = QueueStats()

    def offer_raw(self, event: RawCaptureEvent) -> bool:
        try:
            self.raw.put_nowait(event)
            return True
        except asyncio.QueueFull:
            self.stats.raw_dropped += 1
            return False

    def offer_parse(self, event: RawCaptureEvent) -> bool:
        try:
            self.parse.put_nowait(event)
            return True
        except asyncio.QueueFull:
            self.stats.parse_dropped += 1
            return False
