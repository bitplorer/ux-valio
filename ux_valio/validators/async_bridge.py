# SPDX-License-Identifier: MIT
"""Nest-safe sync bridge for async processors and tasks.

``add_*`` / ``add_*_task`` accept sync or async callables. Coroutine
functions register. Coroutine objects follow run rules. On the sync
descriptor path: no running loop → TypeError naming the missing loop /
helper; running loop → nest-safe worker private loop. No ``asyncio.run``
in the setter.
"""

from __future__ import annotations

import atexit
import asyncio
import concurrent.futures
import inspect
from typing import Any, Callable

_NEST_SAFE_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=1)
atexit.register(_NEST_SAFE_EXECUTOR.shutdown, wait=False)

ASYNC_NEEDS_LOOP = (
    "async callable needs a running event loop / helper "
    "(await from async context; asyncio.run in the setter is retired)"
)


def nest_safe_bridge(coro: Any) -> Any:
    """Drive ``coro`` on a private loop in a worker thread.

    Same-thread ``run_until_complete`` on the *running* loop is a
    nested-loop hazard. This helper never touches the caller's loop.
    The worker pool is process-held and reused; it is not a public dial.
    """

    def worker() -> Any:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            asyncio.set_event_loop(None)
            loop.close()

    return _NEST_SAFE_EXECUTOR.submit(worker).result()


def resolve_coroutine(result: Any) -> Any:
    """Apply run rules to a processor/task/validator return.

    Coroutine objects are not rejected as a class. Sync values pass
    through. Coroutine: if ``get_running_loop()`` exists, nest-safe
    bridge; if not, TypeError (do not store the coroutine, do not drive
    it from the setter with a nested loop).
    """
    if inspect.isasyncgen(result):
        raise TypeError(f"callable returned an async generator; {ASYNC_NEEDS_LOOP}")
    if not inspect.iscoroutine(result):
        return result
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        result.close()
        raise TypeError(ASYNC_NEEDS_LOOP) from None
    return nest_safe_bridge(result)


def invoke_callable(func: Callable[..., Any], instance: Any, value: Any) -> Any:
    return resolve_coroutine(func(instance, value))
