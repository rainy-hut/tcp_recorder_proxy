from __future__ import annotations

import asyncio
from contextlib import suppress
from collections.abc import Awaitable


async def cancel_and_wait(tasks: list[asyncio.Task[object] | asyncio.Task[None]]) -> None:
    for task in tasks:
        task.cancel()
    for task in tasks:
        with suppress(asyncio.CancelledError):
            await task
