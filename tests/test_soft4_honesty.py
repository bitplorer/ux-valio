# SPDX-License-Identifier: MIT
"""Soft 4: named Door A honesty rows only.

Soft 3 KEEP: Register DB-check is add_pre_validator inside pre_set.
No add_pre_set. No asyncio.run in __set__. debug-swallow stays.
"""

from dataclasses import dataclass
import inspect

import pytest

from ux_valio.descriptor import Property
from ux_valio import StringValidator, Validator
from ux_valio.validators import Validator as Facade
import ux_valio.validators as vmod

# Module-level host: method ``__qualname__`` is ``_NsHost.strip`` so
# split(".")[0] == ``_NsHost`` (valio L1861). Nested classes in tests do not.
_ns_field = Validator(debug=True)


@dataclass
class _NsHost:
    x: str = _ns_field

    @_ns_field.add_pre_validator
    def strip(self, value):
        return value.strip() if isinstance(value, str) else value


_taken = {"taken"}
_username_field = StringValidator(debug=True, required=True, min_length=3)


@dataclass
class _Register:
    username: str = _username_field

    @_username_field.add_pre_validator
    def username_not_taken(self, value: str) -> str:
        if value in _taken:
            raise ValueError("username already registered")
        return value


# --- Soft 3 KEEP (absence lock) ------------------------------------------------

def test_no_add_pre_set_still_absent():
    assert not hasattr(Validator, "add_pre_set")
    assert not hasattr(Validator, "add_pre_set_task")
    assert "pre_set" not in Facade()._processors
    assert "pre_set" not in Facade()._tasks


def test_register_db_check_is_add_pre_validator_on_username_field():
    """Soft 3 KEEP: before-store uniqueness hangs on add_pre_validator.

    Class-body ``username: str = username`` is NameError (local bind). Door A
    matches valio Field's ``user_field`` / ``user`` split: hang on
    ``username_field``. Method decorator auto-namespace only for *module-level*
    classes (qualname ``_Register.fn``). Nested test classes need ``namespace=``.
    """
    assert _Register(username="ada").username == "ada"
    with pytest.raises(ValueError, match="already registered"):
        _Register(username="taken")


# --- Soft4-DO 1: cartograph Door A vs Soft 1 RETIRE asyncio.run in __set__ -----

def test_no_asyncio_run_or_enable_async_in_door_a_tree():
    """valio `_processing` L1835–1846 and `_after_processing_run_tasks` L807–811
    called asyncio.run from the setter pipeline. Soft 1 RETIRE. Soft 5 may
    import asyncio for get_running_loop / nest-safe bridge. ``enable_async``
    stays not a door. ``asyncio.run`` / ``run_until_complete`` stay out of
    ``Property.__set__`` and the processor/task runners.
    """
    set_src = inspect.getsource(Property.__set__)
    assert "asyncio" not in set_src
    assert "asyncio.run" not in set_src
    assert "run_until_complete" not in set_src
    src = inspect.getsource(vmod)
    assert "enable_async" not in src
    assert "asyncio.run" not in inspect.getsource(Validator._run_processors)
    assert "asyncio.run" not in inspect.getsource(Validator._run_tasks)
    assert "run_until_complete" not in inspect.getsource(Validator._run_processors)
    assert "run_until_complete" not in inspect.getsource(Validator._run_tasks)
    assert "asyncio.run" not in inspect.getsource(vmod._soft5_resolve)


def test_same_name_descriptor_and_field_is_nameerror():
    """Cartograph: Door A cannot bind ``username: str = username``.

    Assignment of ``username`` in the class body makes that name local, so the
    RHS does not see the outer descriptor. valio README avoided this via Door B
    (``user_field`` vs ``user: User = user_field.validator``, README L65–127).
    """
    username = StringValidator(debug=True)
    with pytest.raises(NameError, match="username"):
        @dataclass
        class Register:
            username: str = username


# --- Soft4-DO 2: sync vs async registration honesty ----------------------------

def test_async_def_add_pre_validator_registers():
    """Soft 5 supersedes Soft 4 TypeError-at-register."""
    v = Validator(debug=True)

    @v.add_pre_validator
    async def before(instance, value):
        return value

    assert inspect.iscoroutinefunction(before)
    bagged = [fn for fns in v._processors["pre_validate"].values() for fn in fns]
    assert before in bagged


def test_async_def_add_validator_registers():
    v = Validator(debug=True)

    @v.add_validator
    async def check(instance, value):
        return value

    assert inspect.iscoroutinefunction(check)
    bagged = [fn for fns in v._custom_validators.values() for fn in fns]
    assert check in bagged


def test_async_def_add_pre_validator_task_registers():
    v = Validator(debug=True)

    @v.add_pre_validator_task
    async def side(instance, value):
        return value

    assert inspect.iscoroutinefunction(side)
    bagged = [fn for fns in v._tasks["pre_validate"].values() for fn in fns]
    assert side in bagged


def test_async_def_add_post_set_registers():
    v = Validator(debug=True)

    @v.add_post_set
    async def after(instance, value):
        return value

    assert inspect.iscoroutinefunction(after)
    bagged = [fn for fns in v._processors["post_set"].values() for fn in fns]
    assert after in bagged


async def _coro(instance, value):
    return value


def test_sync_processor_returning_coroutine_type_errors_and_does_not_store():
    """valio `_processing` L1844–1846 asyncio.run'd a coroutine return.

    Soft 1 RETIRE of asyncio.run must not store the coroutine object instead.
    """
    v = Validator(debug=True)

    def wrap(instance, value):
        return _coro(instance, value)

    v.add_pre_validator(wrap, namespace="Host")

    @dataclass
    class Host:
        x: str = v

    with pytest.raises(TypeError, match="Soft 5 Door"):
        Host(x="ada")


def test_sync_processor_returning_coroutine_debug_falsy_swallows_unset():
    field = Validator(debug=False)

    def wrap(instance, value):
        return _coro(instance, value)

    field.add_pre_validator(wrap, namespace="Host")

    @dataclass
    class Host:
        x: str = field

    assert Host(x="ada").x is None
    assert field.errors
    assert any(isinstance(err, TypeError) for err in field.errors)


# --- Soft4-DO 3: decorator / namespace footguns --------------------------------

def test_module_level_decorator_without_namespace_does_not_fire():
    """valio add_pre_validator L1861: namespace or qualname.split('.')[0].

    Module-level ``strip`` keys the bag as ``strip``, not ``Host``.
    """
    field = Validator(debug=True)
    fired = []

    def strip(instance, value):
        fired.append(value)
        return value.strip()

    field.add_pre_validator(strip)

    @dataclass
    class Host:
        x: str = field

    assert Host(x="  Ada  ").x == "  Ada  "
    assert fired == []


def test_module_level_decorator_with_namespace_fires():
    field = Validator(debug=True)

    def strip(instance, value):
        return value.strip() if isinstance(value, str) else value

    field.add_pre_validator(strip, namespace="Host")

    @dataclass
    class Host:
        x: str = field

    assert Host(x="  Ada  ").x == "Ada"


def test_method_decorator_namespace_matches_module_level_class():
    """Module-level ``_NsHost.strip`` → namespace ``_NsHost`` (valio L1861)."""
    assert _NsHost(x="  Ada  ").x == "Ada"


def test_nested_class_method_decorator_qualname_does_not_match():
    """``test_fn.<locals>.Host.strip`` splits to the test name, not ``Host``."""
    field = Validator(debug=True)
    fired = []

    @dataclass
    class Host:
        x: str = field

        @field.add_pre_validator
        def strip(self, value):
            fired.append(value)
            return value.strip()

    assert Host(x="  Ada  ").x == "  Ada  "
    assert fired == []


def test_add_pre_validator_implicit_none_is_stored():
    """Processor return is stored — a DB check must return the value."""
    username_field = StringValidator(debug=True)

    def forget_return(instance, value):
        if value == "taken":
            raise ValueError("taken")

    username_field.add_pre_validator(forget_return, namespace="Register")

    @dataclass
    class Register:
        username: str = username_field

    assert Register(username="ada").username is None


def test_add_pre_validator_task_does_not_rewrite_stored_value():
    username_field = StringValidator(debug=True)
    seen = []

    def note(instance, value):
        seen.append(value)
        return "MUST_NOT_STORE"

    username_field.add_pre_validator_task(note, namespace="Register")

    @dataclass
    class Register:
        username: str = username_field

    assert Register(username="ada").username == "ada"
    assert seen == ["ada"]


# --- Soft4-DO 4: claim vs tree enable_async / cache_task -----------------------

def test_enable_async_kwarg_is_type_error_not_a_new_door():
    """valio claimed enable_async (validators.py L1698, L1756, L1782–1785).
    ux-valio Soft 1 tree has 0 enable_async. Unknown kwargs stay TypeError.
    """
    assert not hasattr(Validator(), "enable_async")
    with pytest.raises(TypeError, match="enable_async"):
        Validator(enable_async=True, debug=True)


def test_cache_task_true_does_not_cache_tasks():
    """valio cache_task=True (L780–789, L1495–1500) keyed by id(tasks).

    ux-valio keeps the kwarg; tasks still run every phase (Soft 1 RETIRE cache).
    """
    log = []
    v = Validator(debug=True, cache_task=True)

    def task(instance, value):
        log.append(value)

    v.add_pre_validator_task(task, namespace="Host")

    @dataclass
    class Host:
        x: str = v

    host = Host(x="a")
    host.x = "b"
    assert log == ["a", "b"]
    assert v.cache_task is True
