# SPDX-License-Identifier: MIT
"""Soft 4: Register before-store teaching + Door A add_* sync honesty.

No add_pre_set. No asyncio.run in __set__. Soft 1–3 locks stay elsewhere.
"""

from dataclasses import dataclass

import pytest

from ux_valio import StringValidator, Validator
from ux_valio.validators import Validator as Facade


def test_no_asyncio_run_in_setter():
    import inspect

    from ux_valio.descriptor import Property

    assert "asyncio" not in inspect.getsource(Property.__set__)
    import ux_valio.validators as vmod

    assert not hasattr(vmod, "asyncio")


def test_no_add_pre_set_still_absent():
    assert not hasattr(Validator, "add_pre_set")
    assert not hasattr(Validator, "add_pre_set_task")
    assert "pre_set" not in Facade()._processors
    assert "pre_set" not in Facade()._tasks


def test_enable_async_kwarg_is_type_error_not_a_new_door():
    with pytest.raises(TypeError, match="enable_async"):
        Validator(enable_async=True, debug=True)


def test_register_username_db_check_via_add_pre_validator():
    """valio README RegisterUser: before-store check is add_pre_validator."""
    taken = {"taken"}
    username = StringValidator(debug=True, required=True, min_length=3)

    @dataclass
    class Register:
        username: str = username

        @username.add_pre_validator
        def username_not_taken(self, value: str) -> str:
            if value in taken:
                raise ValueError("username already registered")
            return value

    assert Register(username="ada").username == "ada"
    with pytest.raises(ValueError, match="already registered"):
        Register(username="taken")


def test_register_username_db_check_via_add_validator_return_ignored():
    taken = {"taken"}
    username = StringValidator(debug=True, required=True)

    @dataclass
    class Register:
        username: str = username

        @username.add_validator
        def username_not_taken(self, value: str):
            if value in taken:
                raise ValueError("username already registered")
            return "MUST_NOT_STORE"

    assert Register(username="ada").username == "ada"


def test_add_pre_validator_implicit_none_is_stored():
    """Processor return is the stored value — DB checks must return value."""
    username = StringValidator(debug=True)

    def forget_return(instance, value):
        if value == "taken":
            raise ValueError("taken")

    username.add_pre_validator(forget_return, namespace="Register")

    @dataclass
    class Register:
        username: str = username

    assert Register(username="ada").username is None


def test_add_pre_validator_task_does_not_rewrite_stored_value():
    username = StringValidator(debug=True)
    seen = []

    def note(instance, value):
        seen.append(value)
        return "MUST_NOT_STORE"

    username.add_pre_validator_task(note, namespace="Register")

    @dataclass
    class Register:
        username: str = username

    assert Register(username="ada").username == "ada"
    assert seen == ["ada"]


def test_add_pre_validator_task_raise_blocks_store_when_debug():
    username = StringValidator(debug=True)

    def reject(instance, value):
        raise ValueError("db down")

    username.add_pre_validator_task(reject, namespace="Register")

    @dataclass
    class Register:
        username: str = username

    with pytest.raises(ValueError, match="db down"):
        Register(username="ada")


def test_module_level_decorator_without_namespace_does_not_fire():
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


def test_async_def_add_pre_validator_type_errors_at_registration():
    v = Validator(debug=True)

    with pytest.raises(TypeError, match="async"):

        @v.add_pre_validator
        async def before(instance, value):
            return value


def test_async_def_add_validator_type_errors_at_registration():
    v = Validator(debug=True)

    with pytest.raises(TypeError, match="async"):

        @v.add_validator
        async def check(instance, value):
            return value


def test_async_def_add_pre_validator_task_type_errors_at_registration():
    v = Validator(debug=True)

    with pytest.raises(TypeError, match="async"):

        @v.add_pre_validator_task
        async def side(instance, value):
            return value


def test_async_def_add_post_set_type_errors_at_registration():
    v = Validator(debug=True)

    with pytest.raises(TypeError, match="async"):

        @v.add_post_set
        async def after(instance, value):
            return value


async def _coro(instance, value):
    return value


def test_sync_processor_returning_coroutine_type_errors_and_does_not_store():
    v = Validator(debug=True)

    def wrap(instance, value):
        return _coro(instance, value)

    v.add_pre_validator(wrap, namespace="Host")

    @dataclass
    class Host:
        x: str = v

    with pytest.raises(TypeError, match="coroutine"):
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
