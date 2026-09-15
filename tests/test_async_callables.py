# SPDX-License-Identifier: MIT
"""async add_*/tasks register; sync-path run rules; no asyncio.run in __set__.

No add_pre_set. asyncio.run in __set__ stays retired.
"""

from dataclasses import dataclass
import asyncio
import inspect

import pytest

from ux_valio.descriptor import Property
from ux_valio import Validator
from ux_valio.validators import Validator as Facade
from ux_valio.validators.hooks import _bag_key
import ux_valio.validators as vmod


def test_no_add_pre_set_still_absent():
    assert not hasattr(Validator, "add_pre_set")
    assert not hasattr(Validator, "add_pre_set_task")
    assert "pre_set" not in Facade()._processors
    assert "pre_set" not in Facade()._tasks
    assert not hasattr(vmod, "_require_sync_callable")
    assert not hasattr(vmod, "_reject_coroutine_result")


def test_no_asyncio_run_in_set():
    src = inspect.getsource(Property.__set__)
    assert "asyncio.run" not in src
    assert "run_until_complete" not in src
    assert "asyncio" not in src


def test_async_decorator_registers_pre_post_and_task():
    v = Validator(debug=True)

    async def before(instance, value):
        return value

    async def after_validate(instance, value):
        return value

    async def after_set(instance, value):
        return value

    async def side(instance, value):
        return value

    v.add_pre_validator(before, namespace="async.Host")
    v.add_post_validator(after_validate, namespace="async.Host")
    v.add_post_set(after_set, namespace="async.Host")
    v.add_pre_validator_task(side, namespace="async.Host")

    assert inspect.iscoroutinefunction(before)
    assert inspect.iscoroutinefunction(after_validate)
    assert inspect.iscoroutinefunction(after_set)
    assert inspect.iscoroutinefunction(side)


def test_sync_path_without_loop_fail_closed_named_error():
    v = Validator(debug=True)

    async def upper(instance, value):
        return value.upper()

    @dataclass
    class Host:
        x: str = v

    v.add_pre_validator(upper, namespace=_bag_key(Host))

    with pytest.raises(TypeError, match="running event loop"):
        Host(x="ada")


def test_sync_path_without_loop_does_not_store_coroutine():
    v = Validator(debug=True)

    async def upper(instance, value):
        return value.upper()

    @dataclass
    class Host:
        x: str = v

    v.add_pre_validator(upper, namespace=_bag_key(Host))

    with pytest.raises(TypeError, match="await from async context"):
        Host(x="ada")


def test_sync_path_without_loop_debug_falsy_swallows_unset():
    field = Validator(debug=False)

    async def upper(instance, value):
        return value.upper()

    @dataclass
    class Host:
        x: str = field

    field.add_pre_validator(upper, namespace=_bag_key(Host))

    assert Host(x="ada").x is None
    assert field.errors
    assert any(
        isinstance(err, TypeError) and "running event loop" in str(err)
        for err in field.errors
    )


def test_async_task_sync_path_without_loop_fail_closed():
    v = Validator(debug=True)
    seen = []

    async def note(instance, value):
        seen.append(value)

    @dataclass
    class Host:
        x: str = v

    v.add_pre_validator_task(note, namespace=_bag_key(Host))

    with pytest.raises(TypeError, match="running event loop"):
        Host(x="ada")
    assert seen == []


def _assign_on_running_loop(factory):
    """Nest-free harness: run factory() while a loop is running.

    ``asyncio.run`` lives in the *test*, not in ``Property.__set__``.
    """

    async def body():
        return factory()

    return asyncio.run(body())


def test_sync_path_with_running_loop_runs_async_processor():
    v = Validator(debug=True)

    async def upper(instance, value):
        await asyncio.sleep(0)
        return value.upper()

    @dataclass
    class Host:
        x: str = v

    v.add_pre_validator(upper, namespace=_bag_key(Host))

    host = _assign_on_running_loop(lambda: Host(x="ada"))
    assert host.x == "ADA"


def test_sync_path_with_running_loop_runs_async_task():
    log = []
    v = Validator(debug=True)

    async def note(instance, value):
        await asyncio.sleep(0)
        log.append(value)
        return "MUST_NOT_STORE"

    @dataclass
    class Host:
        x: str = v

    v.add_pre_validator_task(note, namespace=_bag_key(Host))

    host = _assign_on_running_loop(lambda: Host(x="ada"))
    assert host.x == "ada"
    assert log == ["ada"]


def test_sync_path_with_running_loop_processors_then_tasks_once():
    log = []
    v = Validator(debug=True)

    async def proc(instance, value):
        await asyncio.sleep(0)
        log.append(("proc", value))
        return f"{value}-p"

    async def task(instance, value):
        await asyncio.sleep(0)
        log.append(("task", value))

    @dataclass
    class Host:
        x: str = v

    v.add_pre_validator(proc, namespace=_bag_key(Host))
    v.add_pre_validator_task(task, namespace=_bag_key(Host))

    host = _assign_on_running_loop(lambda: Host(x="raw"))
    assert host.x == "raw-p"
    assert log == [("proc", "raw"), ("task", "raw-p")]


def test_async_post_set_runs_with_running_loop_return_ignored():
    v = Validator(debug=True)

    async def rewrite(instance, value):
        await asyncio.sleep(0)
        return "SHOULD_NOT_STORE"

    @dataclass
    class Host:
        x: str = v

    v.add_post_set(rewrite, namespace=_bag_key(Host))

    host = _assign_on_running_loop(lambda: Host(x="kept"))
    assert host.x == "kept"


def test_sync_wrap_returning_coroutine_registers_and_runs_with_loop():
    """Coroutine objects are driven by the nest-safe bridge when a loop runs."""
    v = Validator(debug=True)

    async def upper(instance, value):
        await asyncio.sleep(0)
        return value.upper()

    def wrap(instance, value):
        return upper(instance, value)

    @dataclass
    class Host:
        x: str = v

    v.add_pre_validator(wrap, namespace=_bag_key(Host))

    host = _assign_on_running_loop(lambda: Host(x="ada"))
    assert host.x == "ADA"


def test_sync_wrap_returning_coroutine_no_loop_needs_helper_not_class_reject():
    v = Validator(debug=True)

    async def upper(instance, value):
        return value.upper()

    def wrap(instance, value):
        return upper(instance, value)

    @dataclass
    class Host:
        x: str = v

    v.add_pre_validator(wrap, namespace=_bag_key(Host))

    with pytest.raises(TypeError, match="running event loop"):
        Host(x="ada")
