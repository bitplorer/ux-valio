# SPDX-License-Identifier: MIT
"""Hook / namespace honesty. No add_pre_set. No asyncio.run in __set__."""

from dataclasses import dataclass
import inspect
from pathlib import Path
from types import ModuleType
import sys

import pytest

from ux_valio.descriptor import Property
from ux_valio.validators.hooks import HookHost
from ux_valio import StringValidator, Validator
from ux_valio.validators import Validator as Facade
from ux_valio.validators.async_bridge import resolve_coroutine
import ux_valio.validators as vmod

# Module-level host: method ``__qualname__`` is ``_NsHost.strip`` so the
# owner key is ``module.qualname`` of ``_NsHost``, matching lookup.
_ns_field = Validator(debug=True)


@dataclass
class _NsHost:
    x: str = _ns_field

    @_ns_field.add_process_pre_validate
    def strip(self, value):
        return value.strip() if isinstance(value, str) else value


_taken = {"taken"}
_username_field = StringValidator(debug=True, required=True, min_length=3)


@dataclass
class _Register:
    username: str = _username_field

    @_username_field.add_process_pre_validate
    def username_not_taken(self, value: str) -> str:
        if value in _taken:
            raise ValueError("username already registered")
        return value


def _package_sources() -> list[str]:
    root = Path(vmod.__file__).resolve().parent
    return [path.read_text() for path in root.glob("*.py")]


def test_no_add_pre_set_still_absent():
    assert not hasattr(Validator, "add_pre_set")
    assert not hasattr(Validator, "add_pre_set_task")
    assert not hasattr(Validator, "add_process_pre_set")
    assert not hasattr(Validator, "add_task_pre_set")
    assert "pre_set" not in Facade()._processors
    assert "pre_set" not in Facade()._tasks


def test_register_db_check_is_add_process_pre_validate_on_username_field():
    """Before-store uniqueness hangs on add_process_pre_validate.

    Taught Door A: hang on the field name in the class body
    (``@username.add_process_pre_validate``). No outer ``username_field`` twin.
    Method decorator keys by owning-class ``module.qualname``.
    Free functions on an unbound descriptor need ``namespace=``.
    """
    assert _Register(username="ada").username == "ada"
    with pytest.raises(ValueError, match="already registered"):
        _Register(username="taken")


def test_class_body_hangs_add_on_the_field_name():
    @dataclass
    class Register:
        username: str = StringValidator(debug=True, required=True, min_length=3)

        @username.add_process_pre_validate
        def username_not_taken(self, value: str) -> str:
            if value == "taken":
                raise ValueError("username already registered")
            return value.strip()

    assert Register.username is Register.__dict__["username"]
    assert Register(username="  ada  ").username == "ada"
    with pytest.raises(ValueError, match="already registered"):
        Register(username="taken")


def test_class_access_add_after_bind_uses_owner_for_free_function():
    @dataclass
    class Host:
        x: str = StringValidator(debug=True)

    @Host.x.add_process_pre_validate
    def strip(self, value):
        return value.strip() if isinstance(value, str) else value

    assert Host(x="  Ada  ").x == "Ada"


def test_shared_descriptor_class_access_uses_accessed_class():
    """Sharing one descriptor: Person.aadhaar.add_* must not bag under Vendor."""
    field = StringValidator(debug=True)

    @dataclass
    class Person:
        aadhaar: str = field

    @dataclass
    class Vendor:
        aadhaar: str = field

    @Person.aadhaar.add_process_pre_validate
    def person_tag(self, value):
        return f"p:{value.strip()}"

    @Vendor.aadhaar.add_process_pre_validate
    def vendor_tag(self, value):
        return f"v:{value.strip()}"

    assert Person(aadhaar="  ada  ").aadhaar == "p:ada"
    assert Vendor(aadhaar="  bob  ").aadhaar == "v:bob"


def test_child_instance_runs_parent_field_hooks():
    @dataclass
    class Parent:
        name: str = StringValidator(debug=True)

        @name.add_process_pre_validate
        def strip(self, value: str) -> str:
            return value.strip()

    @dataclass
    class Child(Parent):
        pass

    assert Child(name="  ada  ").name == "ada"
    assert Parent(name="  bob  ").name == "bob"


def test_no_asyncio_run_or_enable_async_in_door_a_tree():
    """valio `_processing` L1835–1846 and `_after_processing_run_tasks` L807–811
    called asyncio.run from the setter pipeline. That is retired.
    ``enable_async`` stays not a door. ``asyncio.run`` / ``run_until_complete``
    stay out of ``Property.__set__`` and the processor/task runners.
    """
    set_src = inspect.getsource(Property.__set__)
    assert "asyncio" not in set_src
    assert "asyncio.run" not in set_src
    assert "run_until_complete" not in set_src
    assert all("enable_async" not in src for src in _package_sources())
    assert "asyncio.run" not in inspect.getsource(Validator._run_processors)
    assert "asyncio.run" not in inspect.getsource(Validator._run_tasks)
    assert "run_until_complete" not in inspect.getsource(Validator._run_processors)
    assert "run_until_complete" not in inspect.getsource(Validator._run_tasks)
    assert "asyncio.run" not in inspect.getsource(resolve_coroutine)


def test_same_name_descriptor_and_field_is_nameerror():
    """Door A cannot bind ``username: str = username``.

    Assignment of ``username`` in the class body makes that name local, so the
    RHS does not see the outer descriptor. valio README avoided this via Door B
    (``user_field`` vs ``user: User = user_field.validator``, README L65–127).
    """
    username = StringValidator(debug=True)
    with pytest.raises(NameError, match="username"):
        @dataclass
        class Register:
            username: str = username


def test_async_def_add_process_pre_validate_registers():
    v = Validator(debug=True)

    async def before(instance, value):
        return value

    v.add_process_pre_validate(before, namespace="async.Host")
    assert inspect.iscoroutinefunction(before)
    bagged = [fn for fns in v._processors["pre_validate"].values() for fn in fns]
    assert before in bagged
    assert "async.Host" in v._processors["pre_validate"]


def test_async_def_add_validator_registers():
    v = Validator(debug=True)

    async def check(instance, value):
        return value

    v.add_validator(check, namespace="async.Host")
    assert inspect.iscoroutinefunction(check)
    bagged = [fn for fns in v._custom_validators.values() for fn in fns]
    assert check in bagged


def test_async_def_add_task_pre_validate_registers():
    v = Validator(debug=True)

    async def side(instance, value):
        return value

    v.add_task_pre_validate(side, namespace="async.Host")
    assert inspect.iscoroutinefunction(side)
    bagged = [fn for fns in v._tasks["pre_validate"].values() for fn in fns]
    assert side in bagged


def test_async_def_add_process_post_set_registers():
    v = Validator(debug=True)

    async def after(instance, value):
        return value

    v.add_process_post_set(after, namespace="async.Host")
    assert inspect.iscoroutinefunction(after)
    bagged = [fn for fns in v._processors["post_set"].values() for fn in fns]
    assert after in bagged


async def _coro(instance, value):
    return value


def test_sync_processor_returning_coroutine_no_loop_needs_running_loop():
    """valio `_processing` L1844–1846 asyncio.run'd a coroutine return.

    Coroutine objects are not rejected as a class — no loop TypeErrors
    (not asyncio.run, not store).
    """
    v = Validator(debug=True)

    def wrap(instance, value):
        return _coro(instance, value)

    @dataclass
    class Host:
        x: str = v

    v.add_process_pre_validate(wrap, namespace=HookHost._owner_key(Host))

    with pytest.raises(TypeError, match="running event loop"):
        Host(x="ada")


def test_sync_processor_returning_coroutine_debug_falsy_swallows_unset():
    field = Validator(debug=False)

    def wrap(instance, value):
        return _coro(instance, value)

    @dataclass
    class Host:
        x: str = field

    field.add_process_pre_validate(wrap, namespace=HookHost._owner_key(Host))

    assert Host(x="ada").x is None
    assert field.errors
    assert any(isinstance(err, TypeError) for err in field.errors)


def test_free_function_without_namespace_is_type_error():
    """A free function has no owning class; namespace= is required."""
    field = Validator(debug=True)

    def strip(instance, value):
        return value.strip()

    with pytest.raises(TypeError, match="namespace="):
        field.add_process_pre_validate(strip)

    with pytest.raises(TypeError, match="namespace="):
        @field.add_task_pre_validate
        def note(instance, value):
            return value


def test_explicit_namespace_override_matches_class_owner_key():
    """namespace= is the bag key as-is; lookup uses the same module.qualname."""
    field = Validator(debug=True)

    @dataclass
    class Host:
        x: str = field

    def strip(instance, value):
        return value.strip() if isinstance(value, str) else value

    key = f"{Host.__module__}.{Host.__qualname__}"
    field.add_process_pre_validate(strip, namespace=key)
    assert list(field._processors["pre_validate"]) == [key]
    assert Host(x="  Ada  ").x == "Ada"


def test_bare_name_namespace_does_not_match_module_qualname_lookup():
    """leftover teaching: the old __name__ key is not rewritten to match.

    namespace="Host" stays "Host". Lookup is module.qualname, so the
    processor does not fire. Pass the class's module.qualname to override.
    """
    field = Validator(debug=True)
    fired = []

    def strip(instance, value):
        fired.append(value)
        return value.strip()

    field.add_process_pre_validate(strip, namespace="Host")

    @dataclass
    class Host:
        x: str = field

    assert Host(x="  Ada  ").x == "  Ada  "
    assert fired == []
    assert "Host" in field._processors["pre_validate"]
    assert f"{Host.__module__}.{Host.__qualname__}" not in field._processors[
        "pre_validate"
    ]


def test_method_decorator_namespace_matches_module_level_class():
    """Module-level ``_NsHost.strip`` keys ``module.qualname`` of ``_NsHost``."""
    key = f"{_NsHost.__module__}.{_NsHost.__qualname__}"
    assert list(_ns_field._processors["pre_validate"]) == [key]
    assert _NsHost(x="  Ada  ").x == "Ada"


def test_nested_class_method_decorator_uses_module_qualname():
    """Nested ``Host.strip`` keys ``module.qualname``, not the test function name."""
    field = Validator(debug=True)
    fired = []

    @dataclass
    class Host:
        x: str = field

        @field.add_process_pre_validate
        def strip(self, value):
            fired.append(value)
            return value.strip()

    key = f"{Host.__module__}.{Host.__qualname__}"
    assert list(field._processors["pre_validate"]) == [key]
    assert Host(x="  Ada  ").x == "Ada"
    assert fired == ["  Ada  "]


def test_add_process_pre_validate_implicit_none_is_stored():
    """Processor return is stored — a DB check must return the value."""
    username_field = StringValidator(debug=True)

    def forget_return(instance, value):
        if value == "taken":
            raise ValueError("taken")

    @dataclass
    class Register:
        username: str = username_field

    username_field.add_process_pre_validate(forget_return, namespace=HookHost._owner_key(Register))

    assert Register(username="ada").username is None


def test_add_task_pre_validate_does_not_rewrite_stored_value():
    username_field = StringValidator(debug=True)
    seen = []

    def note(instance, value):
        seen.append(value)
        return "MUST_NOT_STORE"

    @dataclass
    class Register:
        username: str = username_field

    username_field.add_task_pre_validate(note, namespace=HookHost._owner_key(Register))

    assert Register(username="ada").username == "ada"
    assert seen == ["ada"]


def test_enable_async_kwarg_is_type_error_not_a_new_door():
    """valio claimed enable_async. Unknown kwargs stay TypeError."""
    assert not hasattr(Validator(), "enable_async")
    with pytest.raises(TypeError, match="enable_async"):
        Validator(enable_async=True, debug=True)


def test_cache_task_is_not_a_door():
    """valio leftover retired: cache_task used to key a task cache by id(tasks)."""
    with pytest.raises(TypeError, match="cache_task"):
        Validator(cache_task=True, debug=True)
    assert not hasattr(Validator(), "cache_task")


def test_same_class_name_different_modules_get_distinct_owner_keys():
    """Two User classes must not share a bag keyed by bare __name__."""
    field = Validator(debug=True)
    log = []

    def _user_in(modname: str, tag: str):
        ns = {
            "__name__": modname,
            "dataclass": dataclass,
            "field": field,
            "log": log,
            "tag": tag,
        }
        exec(
            "@dataclass\n"
            "class User:\n"
            "    x: str = field\n"
            "    @field.add_task_pre_validate\n"
            "    def note(self, value):\n"
            "        log.append(tag)\n"
            "        return value\n",
            ns,
        )
        user = ns["User"]
        mod = ModuleType(modname)
        sys.modules[modname] = mod
        mod.User = user
        return user

    UserA = _user_in("ux_valio_ns_a", "a")
    UserB = _user_in("ux_valio_ns_b", "b")
    assert UserA.__name__ == UserB.__name__ == "User"
    assert UserA.__module__ != UserB.__module__
    assert f"{UserA.__module__}.{UserA.__qualname__}" != (
        f"{UserB.__module__}.{UserB.__qualname__}"
    )

    UserA(x="x")
    assert log == ["a"]
    log.clear()
    UserB(x="x")
    assert log == ["b"]


def test_lookup_uses_same_key_helper_as_register():
    """No __name__-only lookup path; register and lookup share _owner_key."""
    for meth in ("_run_tasks", "_run_processors", "_run_custom_validators"):
        src = inspect.getsource(getattr(Validator, meth))
        assert "instance.__class__.__name__" not in src
        assert "_collect_owner_keys" in src
    assert "_owner_key" in inspect.getsource(HookHost._collect_owner_keys)
    ns_src = inspect.getsource(HookHost._resolve_owner_key)
    assert 'split(".")[0]' not in ns_src
    assert "_owner_key" in ns_src

    field = Validator(debug=True)

    @dataclass
    class Host:
        x: str = field

        @field.add_process_pre_validate
        def strip(self, value):
            return value.strip()

    key = HookHost._owner_key(Host)
    assert key == f"{Host.__module__}.{Host.__qualname__}"
    assert list(field._processors["pre_validate"]) == [key]
    assert HookHost._resolve_owner_key(Host.strip, None) == key
    assert Host(x="  Ada  ").x == "Ada"


def test_class_object_namespace_is_type_error():
    field = Validator(debug=True)

    def fn(instance, value):
        return value

    @dataclass
    class Host:
        x: str = field

    with pytest.raises(TypeError, match="namespace="):
        field.add_process_pre_validate(fn, namespace=Host)

    keys = list(field._processors["pre_validate"])
    assert Host not in keys
    assert all(isinstance(key, str) for key in keys)
