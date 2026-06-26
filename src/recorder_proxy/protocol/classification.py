from __future__ import annotations

from enum import Enum


class MessageClassification(str, Enum):
    BBU_MML_FRAMED = "BBU_MML_FRAMED"
    BBU_BINARY = "BBU_BINARY"
    BBU_MML_PLAIN = "BBU_MML_PLAIN"
    BBU_CONTROL = "BBU_CONTROL"
    BBU_TERMINAL = "BBU_TERMINAL"
    TEXT_COMMAND = "TEXT_COMMAND"
    TEXT_RESPONSE = "TEXT_RESPONSE"
    UNKNOWN_BINARY = "UNKNOWN_BINARY"
    UNKNOWN_TEXT = "UNKNOWN_TEXT"
    PARTIAL = "PARTIAL"
