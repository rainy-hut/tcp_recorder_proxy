from __future__ import annotations

from recorder_proxy.protocol.bbu.bbu_header_decoder import BbuHeaderDecoder
from recorder_proxy.protocol.bbu.bbu_tlv_decoder import BbuTlvDecoder


class BbuBinaryDecoder:
    def __init__(self) -> None:
        self.header_decoder = BbuHeaderDecoder()
        self.tlv_decoder = BbuTlvDecoder()

    def decode(self, frame: bytes) -> dict[str, object]:
        header = self.header_decoder.decode(frame)
        is_binary = (
            (header.transparent_cmd == 0x0400 and header.rru_cmd == 0xCC)
            or (header.transparent_cmd == 0x0401 and header.rru_cmd == 0xCD)
        )
        if not is_binary:
            raise ValueError("not a BBU binary transparent/entity command")
        payload = frame[header.entity_payload_offset :]
        tlvs, warnings = self.tlv_decoder.decode_many(payload)
        return {
            "outer_start_tag": "F634",
            "transparent_cmd": f"0x{header.transparent_cmd:04X}",
            "entity_cmd": f"0x{header.rru_cmd:02X}",
            "entity_operation_code": f"0x{header.entity_operation_code:02X}" if header.entity_operation_code is not None else None,
            "transaction_id1": header.transaction_id1,
            "rru_cmd_len": header.rru_cmd_len,
            "msg_len": header.msg_len,
            "tlv_types": [tlv["type"] for tlv in tlvs],
            "tlvs": tlvs,
            "warnings": warnings,
        }
