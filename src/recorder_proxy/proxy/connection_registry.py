from __future__ import annotations

import itertools


class ConnectionRegistry:
    def __init__(self) -> None:
        self._counter = itertools.count(1)

    def next_id(self) -> str:
        return f"conn_{next(self._counter):06d}"
