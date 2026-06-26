from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field


@dataclass
class CorrelationResult:
    request_id: str | None
    status: str


class BbuResponseCorrelator:
    def __init__(self) -> None:
        self.pending: dict[tuple[object, ...], deque[str]] = defaultdict(deque)

    def observe(self, message_id: str, summary: dict[str, object], direction: str) -> CorrelationResult:
        key = (
            summary.get("entity_operation_code"),
            summary.get("transaction_id1"),
            summary.get("transparent_cmd"),
        )
        entity_cmd = summary.get("entity_cmd")
        if direction == "client_to_hardware" or entity_cmd == "0xCC":
            self.pending[key].append(message_id)
            return CorrelationResult(None, "request_recorded")
        response_key = (summary.get("entity_operation_code"), summary.get("transaction_id1"), "0x0400")
        if self.pending.get(response_key):
            return CorrelationResult(self.pending[response_key][0], "response_correlated")
        return CorrelationResult(None, "orphan_response")
