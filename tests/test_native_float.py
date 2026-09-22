# SPDX-License-Identifier: MIT
"""Native module: Float bound plans (``Plan::Float`` / ``BoundUnit<f64>``).

No ``from __future__ import annotations`` — postponed ``int`` TypeErrors at bind (KEEP).
"""

import re
from dataclasses import dataclass

import pytest

from tests.native_support import (
    _assign,
    _assign_eq,
    _force_host,
    _native_rust,
    _stored_eq,
    host_native_source,
    needs_native,
)
from ux_valio import (
    FloatValidator,
    IntegerValidator,
    ValidationErrors,
    Validator,
)

def test_closed_float_type_door_is_f64_extract():
    """Float type is f64 extract. IEEE compare; no total_cmp / NotFloat."""
    rust = _native_rust()
    native_py = host_native_source()
    assert re.search(r"value: f64", rust)
    assert "fn apply_float" in rust
    assert "fn compile_float" in rust
    assert "total_cmp(" not in rust
    assert ".total_cmp" not in rust
    assert "NotFloat" not in rust
    assert "_closed_float_bounds" in native_py
    assert "apply_native_float_bounds" in native_py
    assert "isinstance(value, expected)" in native_py
    assert "_bridge_to_value" in native_py
    assert 'raise ValueError("overflow' not in native_py
    assert "PyO3 float Overflow" not in native_py
    assert "public overflow" not in native_py


NAN = float("nan")
INF = float("inf")
NEG_INF = float("-inf")

_FLOAT_BOUND_CASES = (
    pytest.param(
        {"min_value": 0.0},
        ((-1.0, "minimum value of 0.0"), (0.0, None), (1.0, None), (-0.0, None)),
        id="min_value",
    ),
    pytest.param(
        {"max_value": 10.0},
        ((9.0, None), (10.0, None), (11.0, "maximum value of 10.0")),
        id="max_value",
    ),
    pytest.param(
        {"gt": 0.0},
        ((-1.0, "greater than 0.0"), (0.0, "greater than 0.0"), (1.0, None), (-0.0, "greater than 0.0")),
        id="gt",
    ),
    pytest.param(
        {"lt": 10.0},
        ((9.0, None), (10.0, "less than 10.0"), (11.0, "less than 10.0")),
        id="lt",
    ),
    pytest.param(
        {"eq": 7.0},
        ((6.0, "expect the value 7.0"), (7.0, None), (8.0, "expect the value 7.0")),
        id="eq",
    ),
    pytest.param(
        {"value": 7.0},
        ((6.0, "expect the value 7.0"), (7.0, None), (8.0, "expect the value 7.0")),
        id="value_alias",
    ),
    pytest.param(
        {"min_value": 0.0, "max_value": 10.0},
        (
            (-1.0, "minimum value of 0.0"),
            (0.0, None),
            (10.0, None),
            (11.0, "maximum value of 10.0"),
        ),
        id="range_min_max",
    ),
    pytest.param(
        {"gt": 0.0, "lt": 10.0},
        ((0.0, "greater than 0.0"), (1.0, None), (9.0, None), (10.0, "less than 10.0")),
        id="range_gt_lt",
    ),
    pytest.param(
        {"max_value": -1.0},
        ((-2.0, None), (-1.0, None), (0.0, "maximum value of -1.0")),
        id="negative_max",
    ),
    pytest.param(
        {"gt": -5.0},
        ((-6.0, "greater than -5.0"), (-5.0, "greater than -5.0"), (-4.0, None)),
        id="negative_gt",
    ),
    pytest.param(
        {"lt": -1.0},
        ((-2.0, None), (-1.0, "less than -1.0"), (0.0, "less than -1.0")),
        id="negative_lt",
    ),
    pytest.param(
        {"eq": -3.0},
        ((-4.0, "expect the value -3.0"), (-3.0, None), (-2.0, "expect the value -3.0")),
        id="negative_eq",
    ),
    pytest.param(
        {"min_value": -273.15},
        ((-273.15, None), (-273.16, "minimum value of -273.15"), (0.0, None)),
        id="negative_min",
    ),
    pytest.param(
        {"eq": 0.0},
        ((-0.0, None), (0.0, None), (1.0, "expect the value 0.0")),
        id="signed_zero_eq",
    ),
)

_FLOAT_NAN_INF_CASES = (
    pytest.param(
        {"min_value": 0.0},
        ((NAN, None), (INF, None), (NEG_INF, "minimum value of 0.0")),
        id="min_nan_inf",
    ),
    pytest.param(
        {"max_value": 10.0},
        ((NAN, None), (INF, "maximum value of 10.0"), (NEG_INF, None)),
        id="max_nan_inf",
    ),
    pytest.param(
        {"gt": 0.0},
        ((NAN, None), (INF, None), (NEG_INF, "greater than 0.0")),
        id="gt_nan_inf",
    ),
    pytest.param(
        {"lt": 10.0},
        ((NAN, None), (INF, "less than 10.0"), (NEG_INF, None)),
        id="lt_nan_inf",
    ),
    pytest.param(
        {"eq": 7.0},
        (
            (NAN, "expect the value 7.0"),
            (INF, "expect the value 7.0"),
            (NEG_INF, "expect the value 7.0"),
        ),
        id="eq_nan_inf",
    ),
    pytest.param(
        {"min_value": 0.0, "max_value": 10.0},
        (
            (NAN, None),
            (INF, "maximum value of 10.0"),
            (NEG_INF, "minimum value of 0.0"),
        ),
        id="range_nan_inf",
    ),
    pytest.param(
        {"min_value": NAN},
        ((NAN, None), (NEG_INF, None), (INF, None), (0.0, None)),
        id="min_bound_nan",
    ),
    pytest.param(
        {"max_value": NAN},
        ((NAN, None), (NEG_INF, None), (INF, None), (0.0, None)),
        id="max_bound_nan",
    ),
    pytest.param(
        {"eq": NAN},
        ((NAN, "expect the value nan"), (0.0, "expect the value nan"), (INF, "expect the value nan")),
        id="eq_bound_nan",
    ),
    pytest.param(
        {"min_value": INF},
        ((NAN, None), (INF, None), (0.0, "minimum value of inf"), (NEG_INF, "minimum value of inf")),
        id="min_bound_inf",
    ),
    pytest.param(
        {"max_value": NEG_INF},
        ((NAN, None), (NEG_INF, None), (0.0, "maximum value of -inf"), (INF, "maximum value of -inf")),
        id="max_bound_neg_inf",
    ),
)

_FLOAT_TYPE_SAMPLES = ("x", None, True, False, 1, object(), 2**70)


def test_float_min_value_works_on_stdlib_path():
    @dataclass
    class Box:
        n: float = FloatValidator(min_value=0.0, debug=True)

    assert Box(n=0.0).n == 0.0
    with pytest.raises(ValueError, match="minimum value of 0.0"):
        Box(n=-1.0)
    with pytest.raises((TypeError, ValidationErrors), match="expect"):
        Box(n=0)  # type: ignore[arg-type]


@pytest.mark.parametrize("kwargs,samples", (*_FLOAT_BOUND_CASES, *_FLOAT_NAN_INF_CASES))
def test_float_bound_door_a_wording_on_host(kwargs, samples):
    """Door A lock: IEEE compare. NaN unordered on min/max/gt/lt; eq uses !=."""
    field = _force_host(FloatValidator(debug=True, name="n", **kwargs))
    for value, fragment in samples:
        got = _assign(field, value)
        if fragment is None:
            assert got[0] == "ok", (kwargs, value, got)
            assert _stored_eq(got[3], value), (kwargs, value, got)
        else:
            assert got[0] == "err", (kwargs, value, got)
            assert got[1] is ValueError, (kwargs, value, got)
            assert fragment in got[2], (kwargs, value, got[2])


@needs_native
def test_float_min_value_compiles_once_at_bind():
    field = FloatValidator(min_value=0.0, debug=True, name="n")
    plan = field._native_plan
    apply = field._native_apply
    assert plan is not None
    assert apply is not None

    @dataclass
    class Box:
        n: float = field

    assert field._native_plan is plan
    box = Box(n=0.0)
    box.n = 3.0
    box.n = 7.0
    assert field._native_plan is plan
    assert field._native_apply is apply


@needs_native
def test_one_ffi_apply_float_per_set():
    field = FloatValidator(min_value=0.0, debug=True, name="n")

    @dataclass
    class Box:
        n: float = field

    assert field._native_plan is not None
    calls: list[float] = []
    orig = field._native_apply

    def counted(plan, value):
        calls.append(value)
        return orig(plan, value)

    field._native_apply = counted
    box = Box(n=1.0)
    box.n = 2.0
    box.n = 3.0
    assert calls == [1.0, 2.0, 3.0]


@needs_native
def test_validator_float_subscript_binds_at_set_name():
    field = Validator[float](min_value=0.0, debug=True)

    @dataclass
    class Box:
        n: float = field

    assert field.annotation is float
    assert field._native_plan is not None
    assert Box(n=2.0).n == 2.0
    with pytest.raises(ValueError, match="minimum value"):
        Box(n=-1.0)


@needs_native
@pytest.mark.parametrize("kwargs,samples", (*_FLOAT_BOUND_CASES, *_FLOAT_NAN_INF_CASES))
def test_closed_float_bounds_compile_once(kwargs, samples):
    field = FloatValidator(debug=True, name="n", **kwargs)
    plan = field._native_plan
    apply = field._native_apply
    assert plan is not None
    assert apply is not None
    passing = next((value for value, fragment in samples if fragment is None), None)
    if passing is not None:
        field.validate(None, passing)
    assert field._native_plan is plan
    assert field._native_apply is apply


@needs_native
@pytest.mark.parametrize("kwargs,samples", (*_FLOAT_BOUND_CASES, *_FLOAT_NAN_INF_CASES))
def test_native_float_parity_with_host_path(kwargs, samples):
    native = FloatValidator(debug=True, name="n", **kwargs)
    host = _force_host(FloatValidator(debug=True, name="n", **kwargs))
    assert native._native_plan is not None
    assert host._native_plan is None
    seen = [value for value, _fragment in samples]
    for value in (*seen, *_FLOAT_TYPE_SAMPLES):
        assert _assign_eq(_assign(native, value), _assign(host, value)), (kwargs, value)
    for value, fragment in samples:
        got = _assign(native, value)
        if fragment is None:
            assert got[0] == "ok", (kwargs, value, got)
            assert _stored_eq(got[3], value), (kwargs, value, got)
        else:
            assert got[0] == "err", (kwargs, value, got)
            assert got[1] is ValueError, (kwargs, value, got)
            assert fragment in got[2], (kwargs, value, got[2])
            assert "Overflow" not in got[2]
            assert "int64" not in got[2].lower()
            assert "float64" not in got[2].lower()
            assert "PyO3" not in got[2]


@needs_native
def test_native_float_uses_apply_float_not_integer_apply():
    import ux_valio_native as native

    field = FloatValidator(min_value=0.0, debug=True, name="n")
    assert field._native_apply is native.apply_float
    integer = IntegerValidator(min_value=0, debug=True, name="n")
    assert integer._native_apply is native.apply_integer


@needs_native
def test_native_float_none_skips_and_debug_false_swallows():
    @dataclass
    class Box:
        n: float = FloatValidator(min_value=0.0, debug=True)

    assert Box(n=None).n is None  # type: ignore[arg-type]

    field = FloatValidator(min_value=0.0, debug=False, name="n")
    assert field._native_plan is not None

    @dataclass
    class Quiet:
        n: float = field

    assert Quiet(n=-1.0).n is None
    assert field.errors
    assert any("minimum value" in str(err) for err in field.errors)


@needs_native
def test_native_float_collect_all_type_miss_matches_host():
    native = FloatValidator(min_value=0.0, debug=True, name="n")
    host = _force_host(FloatValidator(min_value=0.0, debug=True, name="n"))
    with pytest.raises(ValidationErrors) as native_caught:
        native.validate(None, "x")
    with pytest.raises(ValidationErrors) as host_caught:
        host.validate(None, "x")
    assert [str(err) for err in native_caught.value.errors] == [
        str(err) for err in host_caught.value.errors
    ]


@needs_native
def test_native_float_pre_validate_and_custom_still_run():
    @dataclass
    class Box:
        n: float = FloatValidator(min_value=0.0, debug=True)

        @n.pre_validate
        def bump(self, value):
            return value + 1.0

        @n.validator
        def positive(self, value):
            if value is not None and value == 1.0:
                raise ValueError("one")

    assert Box.__dict__["n"]._native_plan is not None
    assert Box(n=1.5).n == 2.5
    with pytest.raises(ValueError, match="minimum value"):
        Box(n=-2.0)
    with pytest.raises(ValueError, match="one"):
        Box(n=0.0)


@needs_native
def test_native_float_bool_and_int_type_miss_match_host():
    native = FloatValidator(min_value=0.0, debug=True, name="n")
    host = _force_host(FloatValidator(min_value=0.0, debug=True, name="n"))
    assert native._native_plan is not None
    for value in (True, False, 0, 1, 2**70):
        assert _assign_eq(_assign(native, value), _assign(host, value)), value
        got = _assign(native, value)
        assert got[0] == "err"
        assert got[1] in (TypeError, ValidationErrors)


@needs_native
def test_f64_overflow_falls_through_to_host_and_passes():
    """OverflowError at f64 extract is a bridge signal, not an L1 miss."""
    native = FloatValidator(min_value=0.0, debug=True, name="n")
    host = _force_host(FloatValidator(min_value=0.0, debug=True, name="n"))
    assert native._native_plan is not None

    def boom(plan, value):
        raise OverflowError("f64 extract")

    native._native_apply = boom
    assert _assign(native, 1.0) == ("ok", None, None, 1.0)
    assert _assign_eq(_assign(native, 1.0), _assign(host, 1.0))
    miss = _assign(native, -1.0)
    host_miss = _assign(host, -1.0)
    assert miss == host_miss
    assert miss[1] is ValueError
    assert "minimum value of 0.0" in miss[2]
    assert "Overflow" not in miss[2]
    assert "float64" not in miss[2].lower()
    assert "PyO3" not in miss[2]


@needs_native
def test_unexpected_float_native_bind_raises_runtime_error(monkeypatch):
    import ux_valio_native

    def boom(**kwargs):
        raise ValueError("native exploded")

    monkeypatch.setattr(ux_valio_native, "compile_float", boom)
    with pytest.raises(RuntimeError, match="ux_valio_native") as caught:
        FloatValidator(min_value=0.0, debug=True, name="n")
    assert isinstance(caught.value.__cause__, ValueError)
    assert "Overflow" not in str(caught.value)
    assert "expect" not in str(caught.value)


@needs_native
def test_unexpected_float_native_apply_raises_runtime_error():
    field = FloatValidator(min_value=0.0, debug=True, name="n")
    assert field._native_plan is not None

    def boom(plan, value):
        raise ValueError("native exploded")

    field._native_apply = boom
    with pytest.raises(RuntimeError, match="ux_valio_native") as caught:
        field.validate(None, 1.0)
    assert isinstance(caught.value.__cause__, ValueError)
