from __future__ import annotations

from dataclasses import dataclass


START_TAG = b"\xF6\x34"


@dataclass(frozen=True)
class FrameResult:
    frame: bytes
    error: str | None = None


class F634Framer:
    def __init__(self, max_frame_bytes: int = 10 * 1024 * 1024) -> None:
        self.max_frame_bytes = max_frame_bytes
        self.buffer = bytearray()

    def feed(self, data: bytes) -> list[FrameResult]:
        self.buffer.extend(data)
        frames: list[FrameResult] = []
        while self.buffer:
            if len(self.buffer) < 4:
                break
            if not self.buffer.startswith(START_TAG):
                index = self.buffer.find(START_TAG, 1)
                if index == -1:
                    frames.append(FrameResult(bytes(self.buffer), "missing F634 start tag"))
                    self.buffer.clear()
                    break
                frames.append(FrameResult(bytes(self.buffer[:index]), "bytes before F634 start tag"))
                del self.buffer[:index]
                continue
            data_size = int.from_bytes(self.buffer[2:4], "big")
            frame_length = data_size + 4
            if frame_length < 4 or frame_length > self.max_frame_bytes:
                frames.append(FrameResult(bytes(self.buffer[:4]), f"invalid DataSize {data_size}"))
                del self.buffer[:4]
                continue
            if len(self.buffer) < frame_length:
                break
            frames.append(FrameResult(bytes(self.buffer[:frame_length])))
            del self.buffer[:frame_length]
        return frames

    def flush_unknown(self) -> bytes:
        data = bytes(self.buffer)
        self.buffer.clear()
        return data
