from __future__ import annotations


class BbuTlvDecoder:
    def decode_many(self, payload: bytes) -> tuple[list[dict[str, object]], list[str]]:
        tlvs: list[dict[str, object]] = []
        warnings: list[str] = []
        offset = 0
        while offset + 4 <= len(payload):
            tlv_type = int.from_bytes(payload[offset : offset + 2], "big")
            tlv_len = int.from_bytes(payload[offset + 2 : offset + 4], "big")
            value_start = offset + 4
            value_end = value_start + tlv_len
            if value_end > len(payload):
                warnings.append(f"TLV 0x{tlv_type:04X} length {tlv_len} exceeds payload")
                break
            tlvs.append(
                {
                    "type": f"0x{tlv_type:04X}",
                    "length": tlv_len,
                    "raw_value_hex": payload[value_start:value_end].hex(),
                }
            )
            offset = value_end
        if offset < len(payload):
            warnings.append(f"{len(payload) - offset} trailing bytes")
        return tlvs, warnings
