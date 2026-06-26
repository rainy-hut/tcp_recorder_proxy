from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class FramedMessage:
    data: bytes
    classification: str
    parse_status: str
    decoded_summary: dict[str, Any] = field(default_factory=dict)
    parse_error: str | None = None
