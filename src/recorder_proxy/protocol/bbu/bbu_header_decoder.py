from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BbuHeader:
    data_size: int
    service_tag: int | None
    frame_tag: int | None
    product_id: int | None
    transparent_cmd: int | None
    handle: int | None
    msg_len: int | None
    rru_cmd: int | None
    rru_cmd_len: int | None
    transaction_id1: int | None
    entity_operation_code: int | None
    entity_payload_offset: int


class BbuHeaderDecoder:
    COMMON_HEADER_BYTES = 42
    TRANSPARENT_HEADER_BYTES = 26
    ENTITY_HEADER_BYTES = 10
    COMMAND_PAYLOAD_OFFSET = 78

    def decode(self, frame: bytes) -> BbuHeader:
        if len(frame) < self.COMMAND_PAYLOAD_OFFSET:
            raise ValueError(f"frame too short: {len(frame)}")
        data_size = int.from_bytes(frame[2:4], "big")
        if data_size + 4 != len(frame):
            raise ValueError(f"DataSize mismatch: {data_size} vs frame {len(frame)}")
        transparent_offset = self.COMMON_HEADER_BYTES
        entity_offset = self.COMMON_HEADER_BYTES + self.TRANSPARENT_HEADER_BYTES
        return BbuHeader(
            data_size=data_size,
            service_tag=frame[4],
            frame_tag=frame[30],
            product_id=frame[31],
            transparent_cmd=int.from_bytes(frame[transparent_offset : transparent_offset + 2], "big"),
            handle=int.from_bytes(frame[transparent_offset + 2 : transparent_offset + 4], "big"),
            msg_len=int.from_bytes(frame[transparent_offset + 24 : transparent_offset + 26], "big"),
            rru_cmd=frame[entity_offset],
            rru_cmd_len=int.from_bytes(frame[entity_offset + 1 : entity_offset + 3], "big"),
            transaction_id1=int.from_bytes(frame[entity_offset + 3 : entity_offset + 5], "big"),
            entity_operation_code=frame[entity_offset + 5],
            entity_payload_offset=self.COMMAND_PAYLOAD_OFFSET,
        )
