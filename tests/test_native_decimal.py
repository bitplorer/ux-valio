# SPDX-License-Identifier: MIT
"""Native module: Decimal type door (``Plan::Decimal``, exact ``Decimal``).

No ``from __future__ import annotations`` — postponed ``int`` TypeErrors at bind (KEEP).
"""

import decimal
import re
from dataclasses import dataclass

import pytest

from tests.native_support import (
    ROOT,
    _assign,
    _force_host,
    _native_rust,
    host_native_source,
    needs_native,
)
from ux_valio import (
    DecimalValidator,
    EnumValidator,
    PathValidator,
    UUIDValidator,
    ValidationErrors,
    Validator,
)

def test_decimal_works_on_stdlib_path():
    @dataclass
    class Box:
        amount: decimal.Decimal = DecimalValidator(debug=True)

    assert Box(amount=decimal.Decimal("1.23")).amount == decimal.Decimal("1.23")
    assert Box(amount=decimal.Decimal("0")).amount == decimal.Decimal("0")
    assert Box(amount="1.50").amount == decimal.Decimal("1.50")
    assert Box(amount=None).amount is None  # type: ignore[arg-type]
    with pytest.raises((TypeError, ValidationErrors), match="expect"):
        Box(amount=1.23)  # type: ignore[arg-type]
    with pytest.raises((TypeError, ValidationErrors), match="expect"):
        Box(amount=1)  # type: ignore[arg-type]
    with pytest.raises((TypeError, ValidationErrors), match="expect"):
        Box(amount=True)  # type: ignore[arg-type]


def test_closed_decimal_type_door_is_decimal_extract():
    """Decimal type is exact Decimal extract. Compile and apply stay a pair."""
    rust = _native_rust()
    cargo = (ROOT / "native" / "Cargo.toml").read_text()
    native_py = host_native_source()
    assert "fn compile_decimal" in rust
    assert "fn apply_decimal" in rust
    assert "Plan::Decimal" in rust
    assert "fn compile_and_apply" not in rust
    assert not re.search(r"\bfn compile\(", rust)
    assert not re.search(r"\bfn apply\(", rust)
    assert "max_digits" not in rust
    assert "decimal_places" not in rust
    assert "quantize" not in rust
    assert "rust_decimal" not in rust
    assert "rust_decimal" not in cargo
    assert "_closed_decimal" in native_py
    assert "_select_decimal" in native_py
    assert "apply_native_decimal" in native_py
    assert "_raise_host_decimal_type_miss" in native_py
    assert "_bridge_to_type" in native_py
    assert "_is_decimal_type_annotation" in native_py


@needs_native
def test_decimal_compiles_once_at_bind():
    import ux_valio_native as native

    field = DecimalValidator(debug=True)

    @dataclass
    class Box:
        amount: decimal.Decimal = field

    plan = field._native_plan
    assert plan is not None
    assert field._native_apply is native.apply_decimal
    assert field._native_apply is not native.apply_float
    assert field.annotation == decimal.Decimal | str
    box = Box(amount=decimal.Decimal("0"))
    box.amount = decimal.Decimal("1.23")
    assert box.amount == decimal.Decimal("1.23")
    assert field._native_plan is plan
    assert field._native_apply is native.apply_decimal


@needs_native
def test_one_ffi_apply_decimal_per_set():
    field = DecimalValidator(debug=True, name="n")
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
    one = decimal.Decimal("1.23")
    zero = decimal.Decimal("0")
    field.__set__(obj, one)
    field.__set__(obj, zero)
    assert calls == [one, zero]
    assert obj.n == zero
    calls.clear()
    field.__set__(obj, "4.00")
    assert calls == [decimal.Decimal("4.00")]
    assert obj.n == decimal.Decimal("4.00")
    calls.clear()
    with pytest.raises((TypeError, ValidationErrors)):
        field.__set__(obj, 1.23)
    with pytest.raises((TypeError, ValidationErrors)):
        field.__set__(obj, 1)
    with pytest.raises((TypeError, ValidationErrors)):
        field.__set__(obj, True)
    assert calls == []


@needs_native
def test_native_decimal_parity_with_host():
    native = DecimalValidator(debug=True, name="n")
    host = _force_host(DecimalValidator(debug=True, name="n"))
    assert native._native_plan is not None
    assert host._native_plan is None
    samples = (
        decimal.Decimal("1.23"),
        decimal.Decimal("0"),
        decimal.Decimal("-1"),
        "1.50",
        "not-a-decimal",
        1.5,
        1,
        True,
        False,
        None,
        b"1",
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
def test_native_decimal_uses_apply_decimal_not_float_apply():
    import ux_valio_native as native

    field = DecimalValidator(debug=True, name="n")
    assert field._native_apply is native.apply_decimal
    assert field._native_apply is not native.apply_float
    plan = native.compile_decimal()
    assert native.apply_decimal(plan, decimal.Decimal("1.23")) is None
    assert native.apply_decimal(plan, decimal.Decimal("0")) is None
    with pytest.raises(TypeError):
        native.apply_decimal(plan, 1.23)
    with pytest.raises(TypeError):
        native.apply_decimal(plan, 1)
    with pytest.raises(TypeError):
        native.apply_decimal(plan, True)
    with pytest.raises(TypeError):
        native.apply_decimal(plan, "1.23")


@needs_native
def test_decimal_unclosed_stays_on_host():
    assert DecimalValidator(
        min_value=decimal.Decimal("0.01"), debug=True, name="n"
    )._native_plan is None
    assert DecimalValidator(required=True, debug=True, name="n")._native_plan is None
    assert DecimalValidator(reassign=False, debug=True, name="n")._native_plan is None
    assert DecimalValidator(
        in_choice=(decimal.Decimal("1"),), debug=True, name="n"
    )._native_plan is None
    with pytest.raises(TypeError):
        DecimalValidator(max_digits=4)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        DecimalValidator(decimal_places=2)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        DecimalValidator(quantize=decimal.Decimal("0.01"))  # type: ignore[call-arg]
    assert UUIDValidator(debug=True, name="n")._native_plan is None
    assert PathValidator(debug=True, name="n")._native_plan is None
    assert EnumValidator(debug=True, name="n")._native_plan is None
    open_union = Validator[decimal.Decimal | int](debug=True, name="n")
    assert open_union._native_plan is None
    optional = Validator[decimal.Decimal | None](debug=True, name="n")
    assert optional._native_plan is None


@needs_native
def test_validator_decimal_subscript_compiles_at_set_name():
    import ux_valio_native as native

    field = Validator[decimal.Decimal](debug=True, name="n")

    class Owner:
        pass

    Owner.__annotations__ = {"n": decimal.Decimal}
    field.__set_name__(Owner, "n")
    assert field.annotation is decimal.Decimal
    assert field._native_plan is not None
    assert field._native_apply is native.apply_decimal
    assert _assign(field, decimal.Decimal("0"))[3] == decimal.Decimal("0")
    assert _assign(field, 1.23)[1] is TypeError
    assert _assign(field, "1.23")[1] is TypeError


@needs_native
def test_decimal_none_skips_and_debug_false_swallows():
    @dataclass
    class Box:
        amount: decimal.Decimal = DecimalValidator(debug=True)

    assert Box(amount=None).amount is None  # type: ignore[arg-type]
    field = DecimalValidator(debug=True, name="n")
    field.debug = False
    assert field._native_plan is not None

    class Quiet:
        pass

    obj = Quiet()
    field.__set__(obj, 1.23)
    assert obj.__dict__.get("n") is None
    assert field.errors
    assert any("expect decimal.Decimal | str type" in str(err) for err in field.errors)
    field.errors.clear()
    field.__set__(obj, decimal.Decimal("0"))
    assert obj.n == decimal.Decimal("0")


@needs_native
def test_native_decimal_collect_all_matches_host():
    native = DecimalValidator(debug=True, name="n")
    host = _force_host(DecimalValidator(debug=True, name="n"))
    samples = (
        decimal.Decimal("1.23"),
        decimal.Decimal("0"),
        "1.23",
        1.5,
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
def test_native_decimal_pre_validate_and_custom_still_run():
    @dataclass
    class Box:
        amount: decimal.Decimal = DecimalValidator(debug=True)

        @amount.pre_validate
        def lift(self, value):
            if value == 1.5:
                return decimal.Decimal("1.50")
            return value

        @amount.validator
        def not_zero(self, value):
            if value == decimal.Decimal("0"):
                raise ValueError("zero")

    assert Box.__dict__["amount"]._native_plan is not None
    assert Box(amount=1.5).amount == decimal.Decimal("1.50")  # type: ignore[arg-type]
    assert Box(amount="2.00").amount == decimal.Decimal("2.00")
    with pytest.raises(ValueError, match="zero"):
        Box(amount=decimal.Decimal("0"))


@needs_native
def test_decimal_extract_type_error_falls_through_to_host():
    native = DecimalValidator(debug=True, name="n")
    host = _force_host(DecimalValidator(debug=True, name="n"))
    assert native._native_plan is not None

    def boom(plan, value):
        raise TypeError("extract")

    native._native_apply = boom
    assert _assign(native, decimal.Decimal("1.23"))[3] == decimal.Decimal("1.23")
    assert _assign(native, decimal.Decimal("0"))[3] == decimal.Decimal("0")
    assert _assign(host, decimal.Decimal("0"))[3] == decimal.Decimal("0")
    miss = _assign(native, 1.23)
    assert miss[1] is ValidationErrors
    assert "extract" not in miss[2]
    assert "Overflow" not in miss[2]


@needs_native
def test_unexpected_decimal_native_bind_raises_runtime_error(monkeypatch):
    import ux_valio_native

    def boom():
        raise ValueError("native exploded")

    monkeypatch.setattr(ux_valio_native, "compile_decimal", boom)
    with pytest.raises(RuntimeError, match="ux_valio_native") as caught:
        DecimalValidator(debug=True, name="n")
    assert isinstance(caught.value.__cause__, ValueError)
    assert "Overflow" not in str(caught.value)
    assert "expect" not in str(caught.value)


@needs_native
def test_unexpected_decimal_native_apply_raises_runtime_error():
    field = DecimalValidator(debug=True, name="n")
    assert field._native_plan is not None

    def boom(plan, value):
        raise ValueError("native exploded")

    field._native_apply = boom
    with pytest.raises(RuntimeError, match="ux_valio_native") as caught:
        field.validate(None, decimal.Decimal("1.23"))
    assert isinstance(caught.value.__cause__, ValueError)
