from __future__ import annotations


def quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r") + '"'


def multiline(value: str) -> str:
    return '"""' + value.replace('"""', '\\"\\"\\"') + '"""'
