# SPDX-License-Identifier: MIT
"""Optional ``ux-valio[native]`` peer: Integer bound units, host soul.

Without the extra, stdlib apply stays the default (CI). With the extra,
closed ``IntegerValidator`` bound plans (min/max/gt/lt/eq, including
range) compile once and one FFI ``apply`` per set. Cap Door B / Ops /
JSON / ``cek-peer-*`` stay off the field path.

No ``from __future__ import annotations`` — postponed ``int`` TypeErrors
at bind (KEEP).
"""

import ast
import re
from dataclasses import dataclass
from pathlib import Path

import pytest

from ux_valio import (
    FloatValidator,
    IntegerValidator,
    StringValidator,
    ValidationErrors,
    Validator,
)

ROOT = Path(__file__).resolve().parents[1]
FIELD_PATH_GLOBS = (
    "ux_valio/**/*.py",
    "native/src/**/*.rs",
    "native/Cargo.toml",
    "native/pyproject.toml",
)
_HOLD = (
    "cek-peer",
    "cek_peer",
    "cek-runtime",
    "cek_runtime",
    "serde_json",
    "serde-json",
)


def _peer_available() -> bool:
    try:
        import ux_valio_native  # noqa: F401
    except ImportError:
        return False
    return True


needs_native = pytest.mark.skipif(
    not _peer_available(),
    reason="ux-valio[native] extra not built (CI without Rust skips)",
)


def _force_host(field: IntegerValidator) -> IntegerValidator:
    from ux_valio.validators._native import _clear_native

    _clear_native(field)
    return field


def _assign(field, value):
    class Box:
        pass

    obj = Box()
    try:
        field.__set__(obj, value)
    except Exception as err:
        return ("err", type(err), str(err), getattr(obj, "n", None))
    return ("ok", None, None, obj.__dict__.get("n"))


def test_native_is_not_a_taught_import():
    import ux_valio

    assert "ux_valio_native" not in ux_valio.__all__
    assert not hasattr(ux_valio, "ux_valio_native")
    assert not hasattr(ux_valio, "compile")
    assert not hasattr(ux_valio, "Plan")


def test_integer_min_value_works_on_stdlib_path():
    @dataclass
    class Box:
        n: int = IntegerValidator(min_value=0, debug=True)

    assert Box(n=0).n == 0
    with pytest.raises(ValueError, match="minimum value of 0"):
        Box(n=-1)
    with pytest.raises((TypeError, ValidationErrors), match="expect"):
        Box(n="0")  # type: ignore[arg-type]


def test_field_path_has_no_cap_door_b_or_json_plan():
    hits = []
    for glob in FIELD_PATH_GLOBS:
        for path in ROOT.glob(glob):
            if not path.is_file():
                continue
            text = path.read_text()
            for token in _HOLD:
                if token in text:
                    hits.append(f"{path.relative_to(ROOT)}: {token}")
    assert hits == []

    native_py = ROOT / "ux_valio" / "validators" / "_native.py"
    tree = ast.parse(native_py.read_text(), filename=str(native_py))
    json_imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "json" or alias.name.startswith("json."):
                    json_imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module == "json" or node.module.startswith("json."):
                json_imports.append(node.module)
    assert json_imports == []


def test_unclosed_plans_stay_on_host():
    required = IntegerValidator(min_value=0, required=True, debug=True)
    assert required._native_plan is None
    multiple = IntegerValidator(min_value=0, multiple_of=2, debug=True)
    assert multiple._native_plan is None
    watched = IntegerValidator(min_value=0, reassign=False, debug=True)
    assert watched._native_plan is None
    choice = IntegerValidator(min_value=0, in_choice=(0, 1), debug=True)
    assert choice._native_plan is None
    float_bound = IntegerValidator(min_value=0.5, debug=True)
    assert float_bound._native_plan is None
    plain = IntegerValidator(debug=True)
    assert plain._native_plan is None
    floating = FloatValidator(min_value=0.0, debug=True)
    assert getattr(floating, "_native_plan", None) is None
    text = StringValidator(min_length=1, debug=True)
    assert getattr(text, "_native_plan", None) is None


def test_plan_shape_is_owned_unit_list():
    rust = (ROOT / "native" / "src" / "lib.rs").read_text()
    assert "units: [Unit; 2]" not in rust
    assert "Vec<Unit>" in rust


def test_native_unit_names_are_full_words():
    """Rust variants are parallel full words; host kwargs stay min_value/gt/…."""
    rust = (ROOT / "native" / "src" / "lib.rs").read_text()
    assert re.search(r"\bMinValue\(i64\)", rust)
    assert re.search(r"\bMaxValue\(i64\)", rust)
    assert re.search(r"\bGreaterThan\(i64\)", rust)
    assert re.search(r"\bLessThan\(i64\)", rust)
    assert re.search(r"\bEqual\(i64\)", rust)
    assert not re.search(r"\bGt\(i64\)", rust)
    assert not re.search(r"\bLt\(i64\)", rust)
    assert not re.search(r"\bEq\(i64\)", rust)
    assert re.search(r"^\s+GreaterThan =", rust, re.M)
    assert re.search(r"^\s+LessThan =", rust, re.M)
    assert re.search(r"^\s+Equal =", rust, re.M)
    assert not re.search(r"^\s+Gt =", rust, re.M)
    assert not re.search(r"^\s+Lt =", rust, re.M)
    assert not re.search(r"^\s+Eq =", rust, re.M)
    native_py = (ROOT / "ux_valio" / "validators" / "_native.py").read_text()
    assert re.search(r"\bkinds\.GreaterThan\b", native_py)
    assert re.search(r"\bkinds\.LessThan\b", native_py)
    assert re.search(r"\bkinds\.Equal\b", native_py)
    assert not re.search(r"\bkinds\.Gt\b", native_py)
    assert not re.search(r"\bkinds\.Lt\b", native_py)
    assert not re.search(r"\bkinds\.Eq\b", native_py)


_BOUND_CASES = (
    pytest.param(
        {"min_value": 0},
        ((-1, "minimum value of 0"), (0, None), (1, None)),
        id="min_value",
    ),
    pytest.param(
        {"max_value": 10},
        ((9, None), (10, None), (11, "maximum value of 10")),
        id="max_value",
    ),
    pytest.param(
        {"gt": 0},
        ((-1, "greater than 0"), (0, "greater than 0"), (1, None)),
        id="gt",
    ),
    pytest.param(
        {"lt": 10},
        ((9, None), (10, "less than 10"), (11, "less than 10")),
        id="lt",
    ),
    pytest.param(
        {"eq": 7},
        ((6, "expect the value 7"), (7, None), (8, "expect the value 7")),
        id="eq",
    ),
    pytest.param(
        {"value": 7},
        ((6, "expect the value 7"), (7, None), (8, "expect the value 7")),
        id="value_alias",
    ),
    pytest.param(
        {"min_value": 0, "max_value": 10},
        (
            (-1, "minimum value of 0"),
            (0, None),
            (10, None),
            (11, "maximum value of 10"),
        ),
        id="range_min_max",
    ),
    pytest.param(
        {"gt": 0, "lt": 10},
        ((0, "greater than 0"), (1, None), (9, None), (10, "less than 10")),
        id="range_gt_lt",
    ),
    pytest.param(
        {"min_value": 0, "lt": 10},
        ((-1, "minimum value of 0"), (0, None), (9, None), (10, "less than 10")),
        id="min_lt",
    ),
    pytest.param(
        {"gt": 0, "max_value": 10},
        ((0, "greater than 0"), (1, None), (10, None), (11, "maximum value of 10")),
        id="gt_max",
    ),
    pytest.param(
        {"max_value": -1},
        ((-2, None), (-1, None), (0, "maximum value of -1")),
        id="negative_max",
    ),
    pytest.param(
        {"gt": -5},
        ((-6, "greater than -5"), (-5, "greater than -5"), (-4, None)),
        id="negative_gt",
    ),
    pytest.param(
        {"lt": -1},
        ((-2, None), (-1, "less than -1"), (0, "less than -1")),
        id="negative_lt",
    ),
    pytest.param(
        {"eq": -3},
        ((-4, "expect the value -3"), (-3, None), (-2, "expect the value -3")),
        id="negative_eq",
    ),
    pytest.param(
        {"min_value": 0, "eq": 5},
        ((-1, "minimum value of 0"), (5, None), (6, "expect the value 5")),
        id="min_eq",
    ),
)


@pytest.mark.parametrize("kwargs,samples", _BOUND_CASES)
def test_integer_bound_door_a_wording_on_host(kwargs, samples):
    field = _force_host(IntegerValidator(debug=True, name="n", **kwargs))
    for value, fragment in samples:
        got = _assign(field, value)
        if fragment is None:
            assert got == ("ok", None, None, value), (kwargs, value, got)
        else:
            assert got[0] == "err", (kwargs, value, got)
            assert got[1] is ValueError, (kwargs, value, got)
            assert fragment in got[2], (kwargs, value, got[2])


_TYPE_AND_OVERFLOW_SAMPLES = ("x", None, True, False, 1.5, object(), 2**70, -(2**70))


@needs_native
def test_integer_min_value_compiles_once_at_bind():
    field = IntegerValidator(min_value=0, debug=True, name="n")
    plan = field._native_plan
    apply = field._native_apply
    assert plan is not None
    assert apply is not None

    @dataclass
    class Box:
        n: int = field

    assert field._native_plan is plan
    box = Box(n=0)
    box.n = 3
    box.n = 7
    assert field._native_plan is plan
    assert field._native_apply is apply


@needs_native
def test_one_ffi_apply_per_set():
    field = IntegerValidator(min_value=0, debug=True, name="n")

    @dataclass
    class Box:
        n: int = field

    assert field._native_plan is not None
    calls: list[int] = []
    orig = field._native_apply

    def counted(plan, value):
        calls.append(value)
        return orig(plan, value)

    field._native_apply = counted
    box = Box(n=1)
    box.n = 2
    box.n = 3
    assert calls == [1, 2, 3]


@needs_native
def test_validator_int_subscript_binds_at_set_name():
    field = Validator[int](min_value=0, debug=True)

    @dataclass
    class Box:
        n: int = field

    assert field.annotation is int
    assert field._native_plan is not None
    assert Box(n=2).n == 2
    with pytest.raises(ValueError, match="minimum value"):
        Box(n=-1)


@needs_native
@pytest.mark.parametrize("kwargs,samples", _BOUND_CASES)
def test_closed_integer_bounds_compile_once(kwargs, samples):
    field = IntegerValidator(debug=True, name="n", **kwargs)
    plan = field._native_plan
    apply = field._native_apply
    assert plan is not None
    assert apply is not None
    passing = next(value for value, fragment in samples if fragment is None)
    field.validate(None, passing)
    assert field._native_plan is plan
    assert field._native_apply is apply


@needs_native
@pytest.mark.parametrize("kwargs,samples", _BOUND_CASES)
def test_native_parity_with_host_path(kwargs, samples):
    native = IntegerValidator(debug=True, name="n", **kwargs)
    host = _force_host(IntegerValidator(debug=True, name="n", **kwargs))
    assert native._native_plan is not None
    assert host._native_plan is None
    seen = [value for value, _fragment in samples]
    for value in (*seen, *_TYPE_AND_OVERFLOW_SAMPLES):
        assert _assign(native, value) == _assign(host, value), (kwargs, value)
    for value, fragment in samples:
        got = _assign(native, value)
        if fragment is None:
            assert got == ("ok", None, None, value), (kwargs, value, got)
        else:
            assert got[0] == "err", (kwargs, value, got)
            assert got[1] is ValueError, (kwargs, value, got)
            assert fragment in got[2], (kwargs, value, got[2])
            assert "Overflow" not in got[2]
            assert "int64" not in got[2].lower()
            assert "PyO3" not in got[2]


@needs_native
def test_native_min_value_wording_and_store():
    @dataclass
    class Box:
        n: int = IntegerValidator(min_value=0, debug=True)

    assert Box(n=0).n == 0
    row = Box(n=4)
    assert row.n == 4
    assert row.__dict__["n"] == 4
    with pytest.raises(ValueError, match="n expect the minimum value of 0, got -1 instead"):
        Box(n=-1)
    with pytest.raises((TypeError, ValidationErrors), match="expect"):
        Box(n="1")  # type: ignore[arg-type]


@needs_native
def test_native_none_skips_and_optional_stores():
    @dataclass
    class Box:
        n: int = IntegerValidator(min_value=0, debug=True)

    assert Box(n=None).n is None  # type: ignore[arg-type]


@needs_native
def test_native_debug_false_swallows():
    field = IntegerValidator(min_value=0, debug=False, name="n")
    assert field._native_plan is not None

    @dataclass
    class Box:
        n: int = field

    assert Box(n=-1).n is None
    assert field.errors
    assert any("minimum value" in str(err) for err in field.errors)


@needs_native
def test_native_collect_all_type_miss_matches_host():
    native = IntegerValidator(min_value=0, debug=True, name="n")
    host = _force_host(IntegerValidator(min_value=0, debug=True, name="n"))
    with pytest.raises(ValidationErrors) as native_caught:
        native.validate(None, "x")
    with pytest.raises(ValidationErrors) as host_caught:
        host.validate(None, "x")
    assert [str(err) for err in native_caught.value.errors] == [
        str(err) for err in host_caught.value.errors
    ]


@needs_native
def test_native_pre_validate_still_runs_on_host():
    @dataclass
    class Box:
        n: int = IntegerValidator(min_value=0, debug=True)

        @n.pre_validate
        def bump(self, value):
            return value + 1

    assert Box.__dict__["n"]._native_plan is not None
    assert Box(n=0).n == 1
    with pytest.raises(ValueError, match="minimum value"):
        Box(n=-2)


@needs_native
def test_native_custom_validator_still_runs():
    @dataclass
    class Box:
        n: int = IntegerValidator(min_value=0, debug=True)

        @n.validator
        def even(self, value):
            if value is not None and value % 2:
                raise ValueError("odd")

    assert Box.__dict__["n"]._native_plan is not None
    assert Box(n=2).n == 2
    with pytest.raises(ValueError, match="odd"):
        Box(n=1)


@needs_native
def test_failkind_exposes_full_word_names():
    import ux_valio_native as peer

    assert hasattr(peer.FailKind, "GreaterThan")
    assert hasattr(peer.FailKind, "LessThan")
    assert hasattr(peer.FailKind, "Equal")
    assert not hasattr(peer.FailKind, "Gt")
    assert not hasattr(peer.FailKind, "Lt")
    assert not hasattr(peer.FailKind, "Eq")


def test_host_bridge_drops_i64_bit_length_precheck():
    """PyO3 i64 extract is the range oracle. No host bit_length gate."""
    native_py = (ROOT / "ux_valio" / "validators" / "_native.py").read_text()
    rust = (ROOT / "native" / "src" / "lib.rs").read_text()
    assert "_I64_BITS" not in native_py
    assert "bit_length" not in native_py
    assert "_native_fail_type" not in native_py
    assert "NotInteger" not in native_py
    assert "NotInteger" not in rust
    assert "PyO3 int64 Overflow" not in native_py


def test_negative_min_value_door_a_parity_on_host():
    """Door A KEEP: MinValue is ``value < min`` including a negative bound."""

    @dataclass
    class Box:
        n: int = IntegerValidator(min_value=-273, debug=True)

    assert Box(n=-273).n == -273
    assert Box(n=0).n == 0
    with pytest.raises(ValueError, match="minimum value of -273"):
        Box(n=-274)


@needs_native
def test_native_negative_min_value_parity_with_host():
    native = IntegerValidator(min_value=-273, debug=True, name="n")
    host = _force_host(IntegerValidator(min_value=-273, debug=True, name="n"))
    assert native._native_plan is not None
    assert host._native_plan is None
    for value in (-274, -273, 0, 1):
        assert _assign(native, value) == _assign(host, value), value
    below = _assign(native, -274)
    assert below[0] == "err"
    assert below[1] is ValueError
    assert "minimum value of -273" in below[2]


@needs_native
def test_i64_overflow_falls_through_to_host_and_passes():
    """OverflowError at extract is a bridge signal, not an L1 miss."""
    native = IntegerValidator(min_value=0, debug=True, name="n")
    host = _force_host(IntegerValidator(min_value=0, debug=True, name="n"))
    assert native._native_plan is not None
    huge = 2**70
    assert _assign(native, huge) == ("ok", None, None, huge)
    assert _assign(native, huge) == _assign(host, huge)
    assert _assign(native, 2**63 - 1) == ("ok", None, None, 2**63 - 1)
    assert _assign(native, 2**63) == ("ok", None, None, 2**63)
    i64_min = _assign(native, -(2**63))
    assert i64_min == _assign(host, -(2**63))
    assert i64_min[1] is ValueError
    assert "minimum value of 0" in i64_min[2]
    too_small = -(2**70)
    native_miss = _assign(native, too_small)
    host_miss = _assign(host, too_small)
    assert native_miss == host_miss
    assert native_miss[1] is ValueError
    assert "minimum value of 0" in native_miss[2]
    assert "Overflow" not in native_miss[2]
    assert "int64" not in native_miss[2].lower()
    assert "PyO3" not in native_miss[2]


@needs_native
def test_out_of_i64_min_value_bind_stays_on_host():
    field = IntegerValidator(min_value=2**70, debug=True, name="n")
    assert field._native_plan is None
    assert _assign(field, 2**70) == ("ok", None, None, 2**70)
    miss = _assign(field, 0)
    assert miss[0] == "err"
    assert miss[1] is ValueError
    assert "minimum value of" in miss[2]
    assert "Overflow" not in miss[2]


@needs_native
def test_out_of_i64_max_and_eq_bind_stays_on_host():
    too_big = 2**70
    maximum = IntegerValidator(max_value=too_big, debug=True, name="n")
    assert maximum._native_plan is None
    assert _assign(maximum, too_big) == ("ok", None, None, too_big)
    exact = IntegerValidator(eq=too_big, debug=True, name="n")
    assert exact._native_plan is None
    assert _assign(exact, too_big) == ("ok", None, None, too_big)
    miss = _assign(exact, 0)
    assert miss[1] is ValueError
    assert "expect the value" in miss[2]
    assert "Overflow" not in miss[2]


@needs_native
def test_i64_overflow_gt_passes_max_misses():
    """Huge ints skip native extract; host ValueValidator still owns Door A."""
    gt = IntegerValidator(gt=0, debug=True, name="n")
    host_gt = _force_host(IntegerValidator(gt=0, debug=True, name="n"))
    assert gt._native_plan is not None
    huge = 2**70
    assert _assign(gt, huge) == ("ok", None, None, huge)
    assert _assign(gt, huge) == _assign(host_gt, huge)

    maximum = IntegerValidator(max_value=10, debug=True, name="n")
    host_max = _force_host(IntegerValidator(max_value=10, debug=True, name="n"))
    assert maximum._native_plan is not None
    native_miss = _assign(maximum, huge)
    host_miss = _assign(host_max, huge)
    assert native_miss == host_miss
    assert native_miss[1] is ValueError
    assert "maximum value of 10" in native_miss[2]
    assert "Overflow" not in native_miss[2]


@needs_native
def test_bool_as_int_matches_host_path():
    native = IntegerValidator(min_value=0, debug=True, name="n")
    host = _force_host(IntegerValidator(min_value=0, debug=True, name="n"))
    assert native._native_plan is not None
    for value in (True, False):
        assert _assign(native, value) == _assign(host, value), value


@needs_native
def test_unexpected_peer_bind_raises_runtime_error_with_ux_valio_native(monkeypatch):
    import ux_valio_native

    def boom(**kwargs):
        raise ValueError("peer exploded")

    monkeypatch.setattr(ux_valio_native, "compile", boom)
    with pytest.raises(RuntimeError, match="ux_valio_native") as caught:
        IntegerValidator(min_value=0, debug=True, name="n")
    assert isinstance(caught.value.__cause__, ValueError)
    assert "Overflow" not in str(caught.value)
    assert "expect" not in str(caught.value)


@needs_native
def test_unexpected_peer_apply_raises_runtime_error_with_ux_valio_native():
    field = IntegerValidator(min_value=0, debug=True, name="n")
    assert field._native_plan is not None

    def boom(plan, value):
        raise ValueError("peer exploded")

    field._native_apply = boom
    with pytest.raises(RuntimeError, match="ux_valio_native") as caught:
        field.validate(None, 1)
    assert isinstance(caught.value.__cause__, ValueError)
