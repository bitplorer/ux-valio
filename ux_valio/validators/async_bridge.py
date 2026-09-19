# SPDX-License-Identifier: MIT
"""Nest-safe processor bridge and background task spawn.

``process_*`` must finish before the next pipeline step. Async
processors on the sync path: no running loop → TypeError; running loop →
nest-safe worker. No ``asyncio.run`` in ``__set__``.

``task_*`` is a background side effect (email after username set).
The setter does not wait. Sync or async. Isolated worker — not the
nest-safe pool, not the caller's loop (so ``asyncio.run`` teardown cannot
cancel it). Errors are recorded on the host; they do not fail the set.
"""

from __future__ import annotations

import atexit
import asyncio
import concurrent.futures
import inspect
import threading
from typing import Any, Callable

# One worker is KEEP: one private loop, no nested-run races.
_NEST_SAFE_EXECUTOR = concurrent.futures.ThreadPoolExecutor(
    max_workers=1, thread_name_prefix="ux-valio-nest"
)
atexit.register(_NEST_SAFE_EXECUTOR.shutdown, wait=False)

_TASK_EXECUTOR = concurrent.futures.ThreadPoolExecutor(
    thread_name_prefix="ux-valio-task"
)
atexit.register(_TASK_EXECUTOR.shutdown, wait=False)

_outstanding: set[concurrent.futures.Future[Any]] = set()
_OUTSTANDING_LOCK = threading.Lock()

_nest_safe_worker_ident: int | None = None
_NEST_SAFE_IDENT_LOCK = threading.Lock()

ASYNC_NEEDS_LOOP = (
    "async callable needs a running event loop / helper "
    "(await from async context; asyncio.run in the setter is retired)"
)

NEST_SAFE_REENTERED = (
    "nest-safe bridge is already running on this worker; "
    "nested async assignment would deadlock"
)


def nest_safe_bridge(coro: Any) -> Any:
    """Drive ``coro`` on a private loop in a worker thread.

    Same-thread ``run_until_complete`` on the *running* loop is a
    nested-loop hazard. This helper never touches the caller's loop.
    The worker pool is process-held and reused; it is not a public dial.
    Re-entry from the worker thread is TypeError (would deadlock).
    """
    with _NEST_SAFE_IDENT_LOCK:
        already = _nest_safe_worker_ident
    if already is not None and threading.get_ident() == already:
        coro.close()
        raise TypeError(NEST_SAFE_REENTERED)

    def worker() -> Any:
        global _nest_safe_worker_ident
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        with _NEST_SAFE_IDENT_LOCK:
            _nest_safe_worker_ident = threading.get_ident()
        try:
            return loop.run_until_complete(coro)
        finally:
            with _NEST_SAFE_IDENT_LOCK:
                _nest_safe_worker_ident = None
            asyncio.set_event_loop(None)
            loop.close()

    return _NEST_SAFE_EXECUTOR.submit(worker).result()


def resolve_coroutine(result: Any) -> Any:
    """Apply run rules to a processor/validator return.

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


def _track(fut: concurrent.futures.Future[Any]) -> None:
    with _OUTSTANDING_LOCK:
        _outstanding.add(fut)
    fut.add_done_callback(_forget)


def _forget(fut: concurrent.futures.Future[Any]) -> None:
    with _OUTSTANDING_LOCK:
        _outstanding.discard(fut)


def _call_task(host: Any, func: Callable[..., Any], instance: Any, value: Any) -> None:
    try:
        result = func(instance, value)
        if inspect.iscoroutine(result):
            asyncio.run(result)
    except Exception as err:
        record = getattr(host, "_record_error", None)
        if callable(record):
            record(err)


def spawn_task(
    host: Any, func: Callable[..., Any], instance: Any, value: Any
) -> None:
    """Fire-and-forget. Setter does not wait. Return ignored."""
    _track(_TASK_EXECUTOR.submit(_call_task, host, func, instance, value))


def wait_tasks(timeout: float | None = None) -> None:
    """Wait for background ``task_*`` work. Tests and shutdown."""
    with _OUTSTANDING_LOCK:
        futs = list(_outstanding)
    if not futs:
        return
    done, not_done = concurrent.futures.wait(futs, timeout=timeout)
    if not_done:
        raise TimeoutError(
            f"{len(not_done)} background task(s) still running after {timeout!r}"
        )
