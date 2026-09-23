# SPDX-License-Identifier: MIT
"""Native module: Date type door (``Plan::Date``, ``datetime.date``).

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
    EnumValidator,
    ExpiryValidator,
    ValidationErrors,
    Validator,
)


def test_date_works_on_stdlib_path():
    @dataclass
    class Box:
        opened: datetime.date = DateValidator(debug=True)

    assert Box(opened=datetime.date(2020, 1, 2)).opened == datetime.date(2020, 1, 2)
    assert Box(opened="2020-01-02").opened == datetime.date(2020, 1, 2)
    assert Box(opened="02/01/2020").opened == datetime.date(2020, 1, 2)
    assert Box(opened=None).opened is None  # type: ignore[arg-type]
    with pytest.raises((TypeError, ValidationErrors), match="expect"):
        Box(opened=datetime.datetime(2020, 1, 2))  # type: ignore[arg-type]
    with pytest.raises((TypeError, ValidationErrors), match="expect"):
        Box(opened=1)  # type: ignore[arg-type]


def test_closed_date_type_door_is_date_extract():
    """Date type is datetime.date extract. Compile and apply stay a pair."""
    rust = _native_rust()
    native_py = host_native_source()
    assert "fn compile_date" in rust
    assert "fn apply_date" in rust
    assert "Plan::Date" in rust
    assert "fn compile_and_apply" not in rust
    assert not re.search(r"\bfn compile\(", rust)
    assert not re.search(r"\bfn apply\(", rust)
    assert "_closed_date" in native_py
    assert "_select_date" in native_py
    assert "apply_native_date" in native_py
    assert "_raise_host_date_type_miss" in native_py
    assert "_bridge_to_type" in native_py
    assert "_is_date_type_annotation" in native_py


@needs_native
def test_date_compiles_once_at_bind():
    import ux_valio_native as native

    field = DateValidator(debug=True)

    @dataclass
    class Box:
        opened: datetime.date = field

    plan = field._native_plan
    assert plan is not None
    assert field._native_apply is native.apply_date
    assert field._native_apply is not native.apply_datetime
    assert field._native_run is not field._native_apply
    assert field.annotation == datetime.date | str
    box = Box(opened=datetime.date(2020, 1, 2))
    box.opened = datetime.date(2020, 2, 3)
    assert box.opened == datetime.date(2020, 2, 3)
    assert field._native_plan is plan
    assert field._native_apply is native.apply_date


@needs_native
def test_one_ffi_apply_date_per_set():
    field = DateValidator(debug=True, name="n")
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
    one = datetime.date(2020, 1, 2)
    field.__set__(obj, one)
    field.__set__(obj, "02-01-2020")
    assert calls == [one, datetime.date(2020, 1, 2)]
    assert obj.n == datetime.date(2020, 1, 2)
    calls.clear()
    with pytest.raises((TypeError, ValidationErrors)):
        field.__set__(obj, 1)
    assert calls == []
    calls.clear()
    stamped = datetime.datetime(2020, 1, 2, 3, 4)
    with pytest.raises((TypeError, ValidationErrors)):
        field.__set__(obj, stamped)
    assert calls == [stamped]


@needs_native
def test_native_date_parity_with_host():
    native = DateValidator(debug=True, name="n")
    host = _force_host(DateValidator(debug=True, name="n"))
    assert native._native_plan is not None
    assert host._native_plan is None
    samples = (
        datetime.date(2020, 1, 2),
        datetime.date.min,
        datetime.date.max,
        "2020-01-02",
        "02/01/2020",
        "2020/01/02",
        "02:01:2020",
        "2020-13-01",
        "not-a-date",
        datetime.datetime(2020, 1, 2, 3, 4),
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
def test_native_date_uses_apply_date_not_datetime_apply():
    import ux_valio_native as native

    field = DateValidator(debug=True, name="n")
    assert field._native_apply is native.apply_date
    assert field._native_apply is not native.apply_datetime
    plan = native.compile_date()
    opened = datetime.date(2020, 1, 2)
    assert native.apply_date(plan, opened) is None
    assert native.apply_date(plan, datetime.datetime(2020, 1, 2, 3, 4)) is None
    with pytest.raises(TypeError):
        native.apply_date(plan, "2020-01-02")
    with pytest.raises(TypeError):
        native.apply_date(plan, 1)
    with pytest.raises(TypeError):
        native.apply_date(plan, True)


@needs_native
def test_date_unclosed_stays_on_host():
    opened = datetime.date(2020, 1, 2)
    assert DateValidator(min_value=opened, debug=True, name="n")._native_plan is None
    assert DateValidator(required=True, debug=True, name="n")._native_plan is None
    assert DateValidator(reassign=False, debug=True, name="n")._native_plan is None
    assert DateValidator(in_choice=(opened,), debug=True, name="n")._native_plan is None
    assert EnumValidator(debug=True, name="n")._native_plan is None
    assert ExpiryValidator(expire_on="2020-01-02", debug=True, name="n")._native_plan is None
    open_union = Validator[datetime.date | int](debug=True, name="n")
    assert open_union._native_plan is None
    optional = Validator[datetime.date | None](debug=True, name="n")
    assert optional._native_plan is None
    assert DateTimeValidator(debug=True, name="n")._native_apply.__name__ == "apply_datetime"


@needs_native
def test_validator_date_subscript_compiles_at_set_name():
    import ux_valio_native as native

    field = Validator[datetime.date](debug=True, name="n")

    class Owner:
        pass

    Owner.__annotations__ = {"n": datetime.date}
    field.__set_name__(Owner, "n")
    assert field.annotation is datetime.date
    assert field._native_plan is not None
    assert field._native_apply is native.apply_date
    assert _assign(field, datetime.date(2020, 1, 2))[3] == datetime.date(2020, 1, 2)
    stamped = datetime.datetime(2020, 1, 2, 3, 4)
    assert _assign(field, stamped)[3] == stamped
    assert _assign(field, "2020-01-02")[1] is TypeError
    assert _assign(field, 1)[1] is TypeError


@needs_native
def test_date_none_skips_and_debug_false_swallows():
    @dataclass
    class Box:
        opened: datetime.date = DateValidator(debug=True)

    assert Box(opened=None).opened is None  # type: ignore[arg-type]
    field = DateValidator(debug=True, name="n")
    field.debug = False
    assert field._native_plan is not None

    class Quiet:
        pass

    obj = Quiet()
    field.__set__(obj, 1)
    assert obj.__dict__.get("n") is None
    assert field.errors
    assert any("expect datetime.date | str type" in str(err) for err in field.errors)
    field.errors.clear()
    field.__set__(obj, datetime.date(2020, 1, 2))
    assert obj.n == datetime.date(2020, 1, 2)


@needs_native
def test_native_date_collect_all_matches_host():
    native = DateValidator(debug=True, name="n")
    host = _force_host(DateValidator(debug=True, name="n"))
    samples = (
        datetime.date(2020, 1, 2),
        "2020-01-02",
        "02/01/2020",
        datetime.datetime(2020, 1, 2),
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
def test_native_date_pre_validate_and_custom_still_run():
    @dataclass
    class Box:
        opened: datetime.date = DateValidator(debug=True)

        @opened.pre_validate
        def lift(self, value):
            if value == 1:
                return datetime.date(2020, 1, 2)
            return value

        @opened.validator
        def not_epoch(self, value):
            if value == datetime.date(1970, 1, 1):
                raise ValueError("epoch")

    assert Box.__dict__["opened"]._native_plan is not None
    assert Box(opened=1).opened == datetime.date(2020, 1, 2)  # type: ignore[arg-type]
    assert Box(opened="02/01/2020").opened == datetime.date(2020, 1, 2)
    with pytest.raises(ValueError, match="epoch"):
        Box(opened=datetime.date(1970, 1, 1))


@needs_native
def test_date_extract_type_error_falls_through_to_host():
    native = DateValidator(debug=True, name="n")
    host = _force_host(DateValidator(debug=True, name="n"))
    assert native._native_plan is not None

    def boom(plan, value):
        raise TypeError("extract")

    native._native_apply = boom
    assert _assign(native, datetime.date(2020, 1, 2))[3] == datetime.date(2020, 1, 2)
    assert _assign(host, datetime.date(2020, 1, 2))[3] == datetime.date(2020, 1, 2)
    miss = _assign(native, 1)
    assert miss[1] is ValidationErrors
    assert "extract" not in miss[2]
    assert "Overflow" not in miss[2]


@needs_native
def test_unexpected_date_native_bind_raises_runtime_error(monkeypatch):
    import ux_valio_native

    def boom():
        raise ValueError("native exploded")

    monkeypatch.setattr(ux_valio_native, "compile_date", boom)
    with pytest.raises(RuntimeError, match="ux_valio_native") as caught:
        DateValidator(debug=True, name="n")
    assert isinstance(caught.value.__cause__, ValueError)
    assert "Overflow" not in str(caught.value)
    assert "expect" not in str(caught.value)


@needs_native
def test_unexpected_date_native_apply_raises_runtime_error():
    field = DateValidator(debug=True, name="n")
    assert field._native_plan is not None

    def boom(plan, value):
        raise ValueError("native exploded")

    field._native_apply = boom
    with pytest.raises(RuntimeError, match="ux_valio_native") as caught:
        field.validate(None, datetime.date(2020, 1, 2))
    assert isinstance(caught.value.__cause__, ValueError)
