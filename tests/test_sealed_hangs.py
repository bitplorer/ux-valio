# SPDX-License-Identifier: MIT
"""Sealed set-phase hangs: compile per owner, run that list on assignment.

Open buckets stay the source of truth. ``__set__`` does not walk MRO,
merge owner keys, or rebuild the list. A missing ``_closed[type(obj)]``
is fail-closed when any set-phase hang exists. No set-phase hang keeps
the straight line.
"""

from dataclasses import dataclass
from datetime import date
import inspect

import pytest

from ux_valio import (
    DateValidator,
    EmailValidator,
    IntegerValidator,
    LengthValidator,
    RequiredValidator,
    StringValidator,
    Validator,
)
from ux_valio.errors import ValidationErrors
from ux_valio.validators.base import ValidateProperty
from ux_valio.validators.hooks import HookHost
from ux_valio.validators._native import _clear_native, bind_native_plan


def test_open_buckets_remain_and_assignment_does_not_read_them():
    """Compile copies; it does not replace the field-side owner buckets."""
    seen: list[str] = []
    field = StringValidator(debug=True)

    @dataclass
    class Host:
        x: str = field

        @field.pre_validate
        def strip(self, value):
            seen.append("strip")
            return value.strip() if isinstance(value, str) else value

    key = HookHost._owner_key(Host)
    assert Host.strip in field._processors["pre_validate"][key]
    assert not hasattr(field, "_closed_set")
    assert field._closed[Host].pre_validate == (Host.strip,)

    def extra(instance, value):
        seen.append("extra")
        return value

    field._processors["pre_validate"][key].append(extra)
    assert Host(x="  a  ").x == "a"
    assert seen == ["strip"]
    field._recompile_closed((Host,))
    assert Host(x="  b  ").x == "b"
    assert seen == ["strip", "strip", "extra"]


def test_post_bind_recompile_updates_closed_before_next_set():
    """B: a hang added after the class exists is on the closed list before set."""
    field = StringValidator(debug=True)

    @dataclass
    class Host:
        x: str = field

    def tag(instance, value):
        return f"{value}!"

    Host.x.pre_validate(tag)
    assert tag in field._closed[Host].pre_validate
    assert Host(x="b").x == "b!"


def test_shared_descriptor_closed_lists_are_per_owner():
    """C: one field shared by two classes does not share one closed list."""
    field = StringValidator(debug=True)

    @dataclass
    class Person:
        aadhaar: str = field

    @dataclass
    class Vendor:
        aadhaar: str = field

    def person_tag(instance, value):
        return f"p:{value.strip()}"

    def vendor_tag(instance, value):
        return f"v:{value.strip()}"

    Person.aadhaar.pre_validate(person_tag)
    Vendor.aadhaar.pre_validate(vendor_tag)
    assert field._closed[Person] is not field._closed[Vendor]
    assert field._closed[Person].pre_validate == (person_tag,)
    assert field._closed[Vendor].pre_validate == (vendor_tag,)
    assert Person(aadhaar="  ada  ").aadhaar == "p:ada"
    assert Vendor(aadhaar="  bob  ").aadhaar == "v:bob"


def test_mro_order_is_base_then_derived_on_the_closed_list():
    """D: closed order matches owner-key order (base first), including a grandchild."""
    field = StringValidator(debug=True)
    log: list[str] = []

    @dataclass
    class Parent:
        name: str = field

        @field.pre_validate
        def strip(self, value):
            log.append("parent")
            return value.strip() if isinstance(value, str) else value

    @dataclass
    class Child(Parent):
        @Parent.name.pre_validate
        def shout(self, value):
            log.append("child")
            return value.upper() if isinstance(value, str) else value

    @dataclass
    class Grand(Child):
        pass

    assert field._closed[Child].pre_validate == (Parent.strip, Child.shout)
    assert field._closed[Grand].pre_validate == (Parent.strip, Child.shout)
    assert field._closed[Parent].pre_validate == (Parent.strip,)
    assert Child(name="  ada  ").name == "ADA"
    assert log == ["parent", "child"]
    assert Grand(name="  bob  ").name == "BOB"
    assert Parent(name="  cy  ").name == "cy"


def test_user_init_subclass_still_runs_when_subclasses_are_baked():
    field = StringValidator(debug=True)

    @dataclass
    class Parent:
        name: str = field

        def __init_subclass__(cls, mark=None, **kwargs):
            super().__init_subclass__(**kwargs)
            cls.mark = mark

        @field.pre_validate
        def strip(self, value):
            return value.strip() if isinstance(value, str) else value

    @dataclass
    class Child(Parent, mark=7):
        pass

    assert Child.mark == 7
    assert Child in field._closed
    assert Child(name="  ada  ").name == "ada"


def test_missing_closed_list_is_fail_closed_and_does_not_run_open_mro():
    called: list[int] = []
    field = StringValidator(debug=True)

    @dataclass
    class Host:
        x: str = field

        @field.pre_validate
        def strip(self, value):
            called.append(1)
            return value.strip() if isinstance(value, str) else value

    row = Host(x="  a  ")
    assert called == [1]
    del field._closed[Host]
    with pytest.raises(TypeError, match="not compiled"):
        row.x = "  b  "
    assert called == [1]
    assert row.x == "a"


def test_missing_closed_list_debug_false_records_and_leaves_the_value():
    field = StringValidator(debug=False)

    @dataclass
    class Host:
        x: str = field

        @field.pre_validate
        def strip(self, value):
            return value.strip() if isinstance(value, str) else value

    row = Host(x="a")
    del field._closed[Host]
    row.x = "b"
    assert row.x == "a"
    assert any(isinstance(err, TypeError) and "not compiled" in str(err) for err in field.errors)


def test_no_set_hang_ignores_a_cleared_closed_cache():
    """Empty set-phase mask stays the no-hang door, cache or not."""
    field = IntegerValidator(min_value=0, debug=True)

    @dataclass
    class Box:
        n: int = field

    row = Box(n=1)
    field._closed.clear()
    row.n = 4
    assert row.n == 4
    with pytest.raises(ValueError, match="minimum value"):
        row.n = -1


def test_plan_bind_and_clear_recompile_closed_lists(monkeypatch):
    field = IntegerValidator(min_value=0, debug=True)

    @dataclass
    class Box:
        n: int = field

        @field.pre_validate
        def keep(self, value):
            return value

    calls: list[int] = []
    original = HookHost._recompile_closed

    def wrapped(self, affected_owners):
        calls.append(1)
        return original(self, affected_owners)

    monkeypatch.setattr(HookHost, "_recompile_closed", wrapped)
    before = field._closed[Box]
    calls.clear()
    _clear_native(field)
    assert calls
    assert field._closed[Box] is not before
    assert field._native_plan is None
    calls.clear()
    mid = field._closed[Box]
    bind_native_plan(field)
    assert calls
    assert field._closed[Box] is not mid
    assert Box(n=2).n == 2


def test_set_does_not_rebuild_or_walk_owner_mro(monkeypatch):
    field = IntegerValidator(min_value=0, debug=True)

    @dataclass
    class Box:
        n: int = field

        @field.pre_validate
        def keep(self, value):
            return value

        @field.task_pre_validate
        def note(self, value):
            return value

    row = Box(n=1)

    def boom(*_args, **_kwargs):
        raise AssertionError("assignment rebuilt or walked owner keys")

    monkeypatch.setattr(HookHost, "_recompile_closed", boom)
    monkeypatch.setattr(HookHost, "_compile_closed", boom)
    monkeypatch.setattr(HookHost, "_collect_owner_keys", staticmethod(boom))
    monkeypatch.setattr(HookHost, "_read_owner_keys", staticmethod(boom))
    row.n = 3
    assert row.n == 3
    HookHost.wait_tasks(timeout=2)


def test_task_tuple_is_on_the_closed_list_and_does_not_replace_the_value():
    seen: list[str] = []
    field = StringValidator(debug=True)

    @dataclass
    class Host:
        x: str = field

        @field.task_post_set
        def note(self, value):
            seen.append(value)
            return "MUST_NOT_STORE"

    assert field._closed[Host].task_post_set == (Host.note,)
    assert Host(x="ada").x == "ada"
    HookHost.wait_tasks(timeout=2)
    assert seen == ["ada"]


def test_set_order_is_pre_validate_validate_post_validate_store_post_set():
    log: list[object] = []

    class Counting(IntegerValidator):
        def validate(self, instance=None, value=None):
            log.append("validate")
            super().validate(instance, value)

    @dataclass
    class Box:
        n: int = Counting(min_value=0, debug=True)

        @n.pre_validate
        def pre(self, value):
            log.append("pre")
            return value

        @n.post_validate
        def post(self, value):
            log.append("post")
            return value

        @n.post_set
        def after(self, value):
            log.append(("post_set", self.__dict__.get("n")))
            return value + 10

    assert Box(n=1).n == 1
    assert log == ["pre", "validate", "post", ("post_set", 1)]


def test_collect_all_includes_sealed_validator_and_fail_fast_stops():
    @dataclass
    class Gather:
        n: int = IntegerValidator(min_value=0, debug=True, collect_all=True)

        @n.validator
        def nope(self, value):
            raise ValueError("nope")

    with pytest.raises(ValidationErrors, match="nope") as gathered:
        Gather(n=-1)
    assert "minimum value" in str(gathered.value)

    @dataclass
    class Fast:
        n: int = IntegerValidator(min_value=0, debug=True, collect_all=False)

        @n.validator
        def nope(self, value):
            raise ValueError("nope")

    with pytest.raises(ValueError, match="minimum value") as fast:
        Fast(n=-1)
    assert "nope" not in str(fast.value)


def test_reassign_false_still_blocks_a_second_set_when_a_hang_is_sealed():
    @dataclass
    class Once:
        s: str = StringValidator(reassign=False, debug=True)

        @s.pre_validate
        def strip(self, value):
            return value.strip() if isinstance(value, str) else value

    once = Once(s="  a  ")
    assert once.s == "a"
    with pytest.raises(AttributeError, match="only once"):
        once.s = "b"
    assert once.s == "a"


def test_logger_still_records_set_when_a_hang_is_sealed(caplog):
    import logging

    @dataclass
    class User:
        name: str = StringValidator(logger=True, debug=True, max_length=8)

        @name.pre_validate
        def strip(self, value):
            return value.strip() if isinstance(value, str) else value

    desc = User.__dict__["name"]
    with caplog.at_level(logging.INFO, logger=desc.logger.name):
        assert User(name="  Ada  ").name == "Ada"
    assert "User.name: set" in " ".join(record.getMessage() for record in caplog.records)


def test_coerce_runs_before_sealed_pre_validate():
    seen: list[type] = []

    @dataclass
    class Box:
        opened: date = DateValidator(debug=True)

        @opened.pre_validate
        def watch(self, value):
            seen.append(type(value))
            return value

    assert Box(opened="2020-01-02").opened == date(2020, 1, 2)
    assert seen == [date]


def test_post_validate_cannot_smuggle_past_store_identity():
    @dataclass
    class Box:
        email: str = EmailValidator(debug=True)

        @email.post_validate
        def smash(self, value):
            return "not-an-email"

    with pytest.raises(ValueError, match="not a valid email"):
        Box(email="ada@example.com")


def test_nested_of_runs_root_pre_then_member_pre():
    """A nested ``_Of`` kept because it has hooks runs after the root pre."""
    log: list[str] = []
    inner = StringValidator(debug=True) & RequiredValidator(required=True)

    def inner_pre(instance, value):
        log.append("inner")
        return value.strip() if isinstance(value, str) else value

    # Present before ``&`` so the inner AllOf is not flattened away.
    inner.pre_validate(inner_pre, namespace="sealed.User")
    outer = inner & LengthValidator(max_length=10, debug=True)
    assert type(outer.validators[0]) is type(inner)

    @dataclass
    class User:
        name: str = outer

    def outer_pre(instance, value):
        log.append("outer")
        return value

    outer.pre_validate(outer_pre, namespace=User)
    inner.pre_validate(inner_pre, namespace=User)
    assert User(name="  Ada  ").name == "Ada"
    assert log == ["outer", "inner"]


def test_no_new_public_hang_api_and_set_source_does_not_walk_mro():
    assert not hasattr(HookHost, "recompile_closed")
    assert not hasattr(HookHost, "closed_set")
    assert hasattr(HookHost, "_recompile_closed")
    for cls in (Validator, ValidateProperty):
        src = inspect.getsource(cls.__set__)
        assert "_collect_owner_keys" not in src
        assert "_recompile_closed" not in src
        assert "_require_closed" in src
    assert "_closed.get" in inspect.getsource(HookHost._require_closed)
