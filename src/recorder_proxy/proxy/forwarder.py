from __future__ import annotations

import asyncio
import uuid

from recorder_proxy.recording.event_queue import RecordingQueues
from recorder_proxy.recording.models import ConnectionInfo, Direction, RawCaptureEvent
from recorder_proxy.utils.time_utils import monotonic_ns, timestamp_ns, utc_now_iso


class Forwarder:
    def __init__(self, queues: RecordingQueues, chunk_size: int) -> None:
        self.queues = queues
        self.chunk_size = chunk_size

    async def pipe(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        connection: ConnectionInfo,
        direction: Direction,
    ) -> None:
        sequence = 0
        try:
            while True:
                data = await reader.read(self.chunk_size)
                if not data:
                    break
                sequence += 1
                start = monotonic_ns()
                writer.write(data)
                await writer.drain()
                latency_us = max(0, (monotonic_ns() - start) // 1000)
                self.queues.offer_raw(
                    RawCaptureEvent(
                        event_id=f"evt_{uuid.uuid4().hex}",
                        connection=connection,
                        timestamp_utc=utc_now_iso(),
                        timestamp_ns=timestamp_ns(),
                        monotonic_ns=monotonic_ns(),
                        direction=direction,
                        chunk_sequence=sequence,
                        data=bytes(data),
                        forward_latency_us=latency_us,
                    )
                )
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except OSError:
                pass
