# SPDX-License-Identifier: MIT
"""Native module: DateTime type door (``Plan::DateTime``, ``datetime.datetime``).

No ``from __future__ import annotations`` — postponed ``int`` TypeErrors at bind (KEEP).
"""

import datetime
import re
from dataclasses import dataclass

import pytest

from tests.native_support import (
    _assign,
    _force_host,
    _native_rust,
    host_native_source,
    needs_native,
)
from ux_valio import (
    DateTimeValidator,
    DateValidator,
    ValidationErrors,
    Validator,
)


def test_datetime_works_on_stdlib_path():
    @dataclass
    class Box:
        stamped: datetime.datetime = DateTimeValidator(debug=True)

    stamped = datetime.datetime(2020, 1, 2, 3, 4, 5)
    assert Box(stamped=stamped).stamped == stamped
    assert Box(stamped="2020-01-02T03:04:05").stamped == stamped
    assert Box(stamped="2020-01-02").stamped == datetime.datetime(2020, 1, 2)
    assert Box(stamped=None).stamped is None  # type: ignore[arg-type]
    with pytest.raises((TypeError, ValidationErrors), match="expect"):
        Box(stamped=datetime.date(2020, 1, 2))  # type: ignore[arg-type]
    with pytest.raises((TypeError, ValidationErrors), match="expect"):
        Box(stamped=1)  # type: ignore[arg-type]


def test_closed_datetime_type_door_is_datetime_extract():
    """DateTime type is datetime.datetime extract. Compile and apply stay a pair."""
    rust = _native_rust()
    native_py = host_native_source()
    assert "fn compile_datetime" in rust
    assert "fn apply_datetime" in rust
    assert "Plan::DateTime" in rust
    assert "fn compile_and_apply" not in rust
    assert not re.search(r"\bfn compile\(", rust)
    assert not re.search(r"\bfn apply\(", rust)
    assert "partial(_closed_type_door, annotation_matches=_is_datetime_type_annotation)" in native_py
    assert "def _closed_datetime(" not in native_py
    assert "_DATETIME_DOOR" in native_py
    assert "def _select_datetime(" not in native_py
    assert "def apply_native_datetime(" not in native_py
    assert "type_miss=_raise_host_type_door_miss" in native_py
    assert "def _raise_host_datetime_type_miss(" not in native_py
    assert "_is_datetime_type_annotation" in native_py


@needs_native
def test_datetime_compiles_once_at_bind():
    import ux_valio_native as native

    field = DateTimeValidator(debug=True)

    @dataclass
    class Box:
        stamped: datetime.datetime = field

    plan = field._native_plan
    assert plan is not None
    assert field._native_apply is native.apply_datetime
    assert field._native_apply is not native.apply_date
    assert field._native_run is not field._native_apply
    assert field.annotation == datetime.datetime | str
    stamped = datetime.datetime(2020, 1, 2, 3, 4, 5)
    box = Box(stamped=stamped)
    box.stamped = datetime.datetime(2020, 2, 3, 4, 5, 6)
    assert box.stamped == datetime.datetime(2020, 2, 3, 4, 5, 6)
    assert field._native_plan is plan
    assert field._native_apply is native.apply_datetime


@needs_native
def test_one_ffi_apply_datetime_per_set():
    field = DateTimeValidator(debug=True, name="n")
    assert field._native_plan is not None
    calls: list[object] = []
    orig = field._native_apply

    def counted(plan, value):
        calls.append(value)
        return orig(plan, value)

    field._native_apply = counted

    class Box:
        pass

    obj = Box()
    one = datetime.datetime(2020, 1, 2, 3, 4, 5)
    field.__set__(obj, one)
    field.__set__(obj, "2020-01-02T03:04:05")
    assert calls == [one, one]
    assert obj.n == one
    calls.clear()
    with pytest.raises((TypeError, ValidationErrors)):
        field.__set__(obj, datetime.date(2020, 1, 2))
    with pytest.raises((TypeError, ValidationErrors)):
        field.__set__(obj, 1)
    assert calls == []


@needs_native
def test_native_datetime_parity_with_host():
    native = DateTimeValidator(debug=True, name="n")
    host = _force_host(DateTimeValidator(debug=True, name="n"))
    assert native._native_plan is not None
    assert host._native_plan is None
    aware = datetime.datetime(2020, 1, 2, 3, 4, tzinfo=datetime.timezone.utc)
    samples = (
        datetime.datetime(2020, 1, 2, 3, 4, 5),
        datetime.datetime.min,
        aware,
        "2020-01-02T03:04:05",
        "2020-01-02",
        "2020-01-02T03:04:05+00:00",
        "not-a-datetime",
        datetime.date(2020, 1, 2),
        1,
        True,
        False,
        None,
        b"2020-01-02",
        object(),
    )
    for value in samples:
        got = _assign(native, value)
        host_got = _assign(host, value)
        assert got[:3] == host_got[:3], (value, got, host_got)
        if got[0] == "ok":
            assert got[3] == host_got[3]
        else:
            assert "Overflow" not in got[2]
            assert "PyO3" not in got[2]


@needs_native
def test_native_datetime_uses_apply_datetime_not_date_apply():
    import ux_valio_native as native

    field = DateTimeValidator(debug=True, name="n")
    assert field._native_apply is native.apply_datetime
    assert field._native_apply is not native.apply_date
    plan = native.compile_datetime()
    stamped = datetime.datetime(2020, 1, 2, 3, 4, 5)
    assert native.apply_datetime(plan, stamped) is None
    aware = datetime.datetime(2020, 1, 2, tzinfo=datetime.timezone.utc)
    assert native.apply_datetime(plan, aware) is None
    with pytest.raises(TypeError):
        native.apply_datetime(plan, datetime.date(2020, 1, 2))
    with pytest.raises(TypeError):
        native.apply_datetime(plan, "2020-01-02T03:04:05")
    with pytest.raises(TypeError):
        native.apply_datetime(plan, 1)
    with pytest.raises(TypeError):
        native.apply_datetime(plan, True)


@needs_native
def test_datetime_unclosed_stays_on_host():
    stamped = datetime.datetime(2020, 1, 2)
    assert DateTimeValidator(min_value=stamped, debug=True, name="n")._native_plan is None
    assert DateTimeValidator(required=True, debug=True, name="n")._native_plan is None
    assert DateTimeValidator(reassign=False, debug=True, name="n")._native_plan is None
    assert DateTimeValidator(in_choice=(stamped,), debug=True, name="n")._native_plan is None
    open_union = Validator[datetime.datetime | int](debug=True, name="n")
    assert open_union._native_plan is None
    optional = Validator[datetime.datetime | None](debug=True, name="n")
    assert optional._native_plan is None
    assert DateValidator(debug=True, name="n")._native_apply.__name__ == "apply_date"


@needs_native
def test_validator_datetime_subscript_compiles_at_set_name():
    import ux_valio_native as native

    field = Validator[datetime.datetime](debug=True, name="n")

    class Owner:
        pass

    Owner.__annotations__ = {"n": datetime.datetime}
    field.__set_name__(Owner, "n")
    assert field.annotation is datetime.datetime
    assert field._native_plan is not None
    assert field._native_apply is native.apply_datetime
    stamped = datetime.datetime(2020, 1, 2, 3, 4)
    assert _assign(field, stamped)[3] == stamped
    assert _assign(field, datetime.date(2020, 1, 2))[1] is TypeError
    assert _assign(field, "2020-01-02T03:04:05")[1] is TypeError


@needs_native
def test_datetime_none_skips_and_debug_false_swallows():
    @dataclass
    class Box:
        stamped: datetime.datetime = DateTimeValidator(debug=True)

    assert Box(stamped=None).stamped is None  # type: ignore[arg-type]
    field = DateTimeValidator(debug=True, name="n")
    field.debug = False
    assert field._native_plan is not None

    class Quiet:
        pass

    obj = Quiet()
    field.__set__(obj, datetime.date(2020, 1, 2))
    assert obj.__dict__.get("n") is None
    assert field.errors
    assert any("expect datetime.datetime | str type" in str(err) for err in field.errors)
    field.errors.clear()
    stamped = datetime.datetime(2020, 1, 2, 3, 4)
    field.__set__(obj, stamped)
    assert obj.n == stamped


@needs_native
def test_native_datetime_collect_all_matches_host():
    native = DateTimeValidator(debug=True, name="n")
    host = _force_host(DateTimeValidator(debug=True, name="n"))
    samples = (
        datetime.datetime(2020, 1, 2, 3, 4),
        "2020-01-02T03:04:05",
        "2020-01-02",
        datetime.date(2020, 1, 2),
        1,
        True,
        None,
    )
    for value in samples:
        native_err = None
        host_err = None
        try:
            native.validate(None, value)
        except (TypeError, ValueError, ValidationErrors) as err:
            native_err = err
        try:
            host.validate(None, value)
        except (TypeError, ValueError, ValidationErrors) as err:
            host_err = err
        assert type(native_err) is type(host_err)
        assert str(native_err) == str(host_err)


@needs_native
def test_native_datetime_pre_validate_and_custom_still_run():
    stamped = datetime.datetime(2020, 1, 2, 3, 4)

    @dataclass
    class Box:
        when: datetime.datetime = DateTimeValidator(debug=True)

        @when.pre_validate
        def lift(self, value):
            if value == 1:
                return stamped
            return value

        @when.validator
        def not_epoch(self, value):
            if value == datetime.datetime(1970, 1, 1):
                raise ValueError("epoch")

    assert Box.__dict__["when"]._native_plan is not None
    assert Box(when=1).when == stamped  # type: ignore[arg-type]
    assert Box(when="2020-01-02T03:04:00").when == datetime.datetime(2020, 1, 2, 3, 4)
    with pytest.raises(ValueError, match="epoch"):
        Box(when=datetime.datetime(1970, 1, 1))


@needs_native
def test_datetime_extract_type_error_falls_through_to_host():
    native = DateTimeValidator(debug=True, name="n")
    host = _force_host(DateTimeValidator(debug=True, name="n"))
    assert native._native_plan is not None

    def boom(plan, value):
        raise TypeError("extract")

    native._native_apply = boom
    stamped = datetime.datetime(2020, 1, 2, 3, 4)
    assert _assign(native, stamped)[3] == stamped
    assert _assign(host, stamped)[3] == stamped
    miss = _assign(native, datetime.date(2020, 1, 2))
    assert miss[1] is ValidationErrors
    assert "extract" not in miss[2]
    assert "Overflow" not in miss[2]


@needs_native
def test_unexpected_datetime_native_bind_raises_runtime_error(monkeypatch):
    import ux_valio_native

    def boom():
        raise ValueError("native exploded")

    monkeypatch.setattr(ux_valio_native, "compile_datetime", boom)
    with pytest.raises(RuntimeError, match="ux_valio_native") as caught:
        DateTimeValidator(debug=True, name="n")
    assert isinstance(caught.value.__cause__, ValueError)
    assert "Overflow" not in str(caught.value)
    assert "expect" not in str(caught.value)


@needs_native
def test_unexpected_datetime_native_apply_raises_runtime_error():
    field = DateTimeValidator(debug=True, name="n")
    assert field._native_plan is not None

    def boom(plan, value):
        raise ValueError("native exploded")

    field._native_apply = boom
    with pytest.raises(RuntimeError, match="ux_valio_native") as caught:
        field.validate(None, datetime.datetime(2020, 1, 2, 3, 4))
    assert isinstance(caught.value.__cause__, ValueError)
