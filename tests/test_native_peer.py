# SPDX-License-Identifier: MIT
"""Optional ``ux-valio[native]`` peer: Integer/Float bounds + String/Bytes length.

Without the extra, stdlib apply stays the default (CI). With the extra,
closed ``IntegerValidator`` / ``FloatValidator`` bound plans
(min/max/gt/lt/eq, including range) and closed ``StringValidator`` /
``BytesValidator`` length plans (min/max/exact) compile once and one
FFI apply per set. Float Door A is IEEE compare (NaN unordered on
min/max/gt/lt; ``eq`` uses ``!=`` so NaN never matches). String Door A
is ``len(str)`` codepoints, not UTF-8 bytes or graphemes. Bytes Door A
is ``len(bytes)`` (byte count), not Unicode codepoints or graphemes.
Cap Door B / Ops / JSON / ``cek-peer-*`` stay off the field path.

No ``from __future__ import annotations`` — postponed ``int`` TypeErrors
at bind (KEEP).
"""

import ast
import math
import re
from dataclasses import dataclass
from pathlib import Path

import pytest

from ux_valio import (
    BytesValidator,
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


def _force_host(field):
    from ux_valio.validators._native import _clear_native

    _clear_native(field)
    return field


def _stored_eq(left, right):
    if (
        isinstance(left, float)
        and isinstance(right, float)
        and math.isnan(left)
        and math.isnan(right)
    ):
        return True
    return left == right


def _assign_eq(left, right):
    return left[:3] == right[:3] and _stored_eq(left[3], right[3])


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
    float_int_bound = FloatValidator(min_value=0, debug=True)
    assert float_int_bound._native_plan is None
    float_required = FloatValidator(min_value=0.0, required=True, debug=True)
    assert float_required._native_plan is None
    float_plain = FloatValidator(debug=True)
    assert float_plain._native_plan is None
    patterned = StringValidator(min_length=1, pattern="a+", debug=True)
    assert patterned._native_plan is None
    string_required = StringValidator(min_length=1, required=True, debug=True)
    assert string_required._native_plan is None
    string_value = StringValidator(min_length=1, min_value="a", debug=True)
    assert string_value._native_plan is None
    blob_pattern = BytesValidator(min_length=1, pattern=b"ab", debug=True)
    assert blob_pattern._native_plan is None
    blob_required = BytesValidator(min_length=1, required=True, debug=True)
    assert blob_required._native_plan is None
    blob_value = BytesValidator(min_length=1, min_value=b"a", debug=True)
    assert blob_value._native_plan is None
    listed = Validator[list](min_length=1, debug=True, name="items")
    assert listed._native_plan is None
    plain_string = StringValidator(debug=True)
    assert plain_string._native_plan is None
    plain_bytes = BytesValidator(debug=True)
    assert plain_bytes._native_plan is None


def test_plan_shape_is_owned_unit_list():
    rust = (ROOT / "native" / "src" / "lib.rs").read_text()
    assert "units: [Unit; 2]" not in rust
    assert "Vec<Unit>" in rust


def test_native_unit_names_are_full_words():
    """Rust variants are parallel full words; host kwargs stay min_value/gt/…."""
    rust = (ROOT / "native" / "src" / "lib.rs").read_text()
    assert re.search(r"\bMinValue\(Bound\)", rust)
    assert re.search(r"\bMaxValue\(Bound\)", rust)
    assert re.search(r"\bGreaterThan\(Bound\)", rust)
    assert re.search(r"\bLessThan\(Bound\)", rust)
    assert re.search(r"\bEqual\(Bound\)", rust)
    assert re.search(r"Integer\(i64\)", rust)
    assert re.search(r"Float\(f64\)", rust)
    assert re.search(r"\bMinLength\(usize\)", rust)
    assert re.search(r"\bMaxLength\(usize\)", rust)
    assert re.search(r"\bLength\(usize\)", rust)
    assert "total_cmp(" not in rust
    assert ".total_cmp" not in rust
    assert not re.search(r"\bGt\(i64\)", rust)
    assert not re.search(r"\bLt\(i64\)", rust)
    assert not re.search(r"\bEq\(i64\)", rust)
    assert not re.search(r"\bGt\(f64\)", rust)
    assert not re.search(r"\bLt\(f64\)", rust)
    assert not re.search(r"\bEq\(f64\)", rust)
    assert re.search(r"^\s+GreaterThan =", rust, re.M)
    assert re.search(r"^\s+LessThan =", rust, re.M)
    assert re.search(r"^\s+Equal =", rust, re.M)
    assert re.search(r"^\s+MinLength =", rust, re.M)
    assert re.search(r"^\s+MaxLength =", rust, re.M)
    assert re.search(r"^\s+Length =", rust, re.M)
    assert not re.search(r"^\s+Gt =", rust, re.M)
    assert not re.search(r"^\s+Lt =", rust, re.M)
    assert not re.search(r"^\s+Eq =", rust, re.M)
    assert not re.search(r"\bMinLen\b", rust)
    assert not re.search(r"\bMaxLen\b", rust)
    native_py = (ROOT / "ux_valio" / "validators" / "_native.py").read_text()
    assert re.search(r"\bkinds\.GreaterThan\b", native_py)
    assert re.search(r"\bkinds\.LessThan\b", native_py)
    assert re.search(r"\bkinds\.Equal\b", native_py)
    assert re.search(r"\bkinds\.MinLength\b", native_py)
    assert re.search(r"\bkinds\.MaxLength\b", native_py)
    assert re.search(r"\bkinds\.Length\b", native_py)
    assert not re.search(r"\bkinds\.Gt\b", native_py)
    assert not re.search(r"\bkinds\.Lt\b", native_py)
    assert not re.search(r"\bkinds\.Eq\b", native_py)
    assert not re.search(r"\bkinds\.MinLen\b", native_py)
    assert not re.search(r"\bkinds\.MaxLen\b", native_py)


def test_closed_integer_type_door_is_ffi_extract():
    """Integer type is i64 extract. Open TypeValidator stays on the host."""
    rust = (ROOT / "native" / "src" / "lib.rs").read_text()
    native_py = (ROOT / "ux_valio" / "validators" / "_native.py").read_text()
    assert re.search(r"value: i64", rust)
    assert "NotInteger" not in rust
    assert "NotFloat" not in rust
    for token in (
        "TypeValidator",
        "TypedDict",
        "Annotated",
        "is_instance_of",
        "typing::",
        "PyType",
    ):
        assert token not in rust, token
    assert "_raise_host_integer_type_miss" in native_py
    assert "isinstance(value, expected)" in native_py
    assert "if value is None:" in native_py


def test_closed_float_type_door_is_f64_extract():
    """Float type is f64 extract. IEEE compare; no total_cmp / NotFloat."""
    rust = (ROOT / "native" / "src" / "lib.rs").read_text()
    native_py = (ROOT / "ux_valio" / "validators" / "_native.py").read_text()
    assert re.search(r"value: f64", rust)
    assert "fn apply_float" in rust
    assert "fn compile_float" in rust
    assert "total_cmp(" not in rust
    assert ".total_cmp" not in rust
    assert "NotFloat" not in rust
    assert "_closed_float_bounds" in native_py
    assert "apply_native_float_bounds" in native_py
    assert "isinstance(value, expected)" in native_py
    assert "_apply_host_value_after_f64_overflow" in native_py
    assert 'raise ValueError("overflow' not in native_py
    assert "PyO3 float Overflow" not in native_py
    assert "public overflow" not in native_py


def test_closed_string_type_door_is_str_extract():
    """String type is UTF-8 extract. Length is codepoints (chars), not bytes."""
    rust = (ROOT / "native" / "src" / "lib.rs").read_text()
    native_py = (ROOT / "ux_valio" / "validators" / "_native.py").read_text()
    assert "fn compile_string" in rust
    assert "fn apply_string" in rust
    assert "value: &str" in rust
    assert "chars().count()" in rust
    assert "grapheme" not in rust.lower()
    assert "_closed_string_length" in native_py
    assert "apply_native_string_length" in native_py
    assert "_apply_host_length_after_str_extract" in native_py
    assert 'raise ValueError("overflow' not in native_py
    assert "PyO3 str Overflow" not in native_py
    assert "public overflow" not in native_py


def test_closed_bytes_type_door_is_bytes_extract():
    """Bytes type is ``&[u8]`` extract. Length is ``len()``, not codepoints."""
    rust = (ROOT / "native" / "src" / "lib.rs").read_text()
    native_py = (ROOT / "ux_valio" / "validators" / "_native.py").read_text()
    assert "fn compile_bytes" in rust
    assert "fn apply_bytes" in rust
    assert "value: &[u8]" in rust
    assert "let byte_len = value.len();" in rust
    assert "Unit::Bytes" in rust
    assert "grapheme" not in rust.lower()
    assert "_closed_bytes_length" in native_py
    assert "apply_native_bytes_length" in native_py
    assert "_apply_host_length_after_bytes_extract" in native_py
    assert 'raise ValueError("overflow' not in native_py
    assert "PyO3 bytes Overflow" not in native_py
    assert "public overflow" not in native_py


def test_open_type_stays_on_host():
    union = Validator[int | str](min_value=0, debug=True, name="n")
    assert union.annotation is not int
    assert union._native_plan is None
    union_float = Validator[float | str](min_value=0.0, debug=True, name="n")
    assert union_float.annotation is not float
    assert union_float._native_plan is None


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
        assert _assign_eq(_assign(native, value), _assign(host, value)), (kwargs, value)
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
    """Python True is int — host-first isinstance, then i64 extract."""
    native = IntegerValidator(min_value=0, debug=True, name="n")
    host = _force_host(IntegerValidator(min_value=0, debug=True, name="n"))
    assert native._native_plan is not None
    for value in (True, False):
        assert _assign(native, value) == _assign(host, value), value
    assert _assign(native, True) == ("ok", None, None, True)
    assert _assign(native, False) == ("ok", None, None, False)


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
    import ux_valio_native as peer

    field = FloatValidator(min_value=0.0, debug=True, name="n")
    assert field._native_apply is peer.apply_float
    integer = IntegerValidator(min_value=0, debug=True, name="n")
    assert integer._native_apply is peer.apply


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
def test_unexpected_float_peer_bind_raises_runtime_error(monkeypatch):
    import ux_valio_native

    def boom(**kwargs):
        raise ValueError("peer exploded")

    monkeypatch.setattr(ux_valio_native, "compile_float", boom)
    with pytest.raises(RuntimeError, match="ux_valio_native") as caught:
        FloatValidator(min_value=0.0, debug=True, name="n")
    assert isinstance(caught.value.__cause__, ValueError)
    assert "Overflow" not in str(caught.value)
    assert "expect" not in str(caught.value)


@needs_native
def test_unexpected_float_peer_apply_raises_runtime_error():
    field = FloatValidator(min_value=0.0, debug=True, name="n")
    assert field._native_plan is not None

    def boom(plan, value):
        raise ValueError("peer exploded")

    field._native_apply = boom
    with pytest.raises(RuntimeError, match="ux_valio_native") as caught:
        field.validate(None, 1.0)
    assert isinstance(caught.value.__cause__, ValueError)


# Door A: Python len(str) is Unicode codepoints, not UTF-8 bytes or graphemes.
_ACCENT_NFC = "é"  # U+00E9 — 1 codepoint, 2 UTF-8 bytes
_ACCENT_NFD = "e\u0301"  # 2 codepoints, 1 grapheme
_EMOJI = "\U0001F600"  # 1 codepoint, 4 UTF-8 bytes
_FAMILY = "👨‍👩‍👧‍👦"  # ZWJ sequence: many codepoints, 1 grapheme
_NULL = "\x00"
_SURROGATE = "\ud800"

_STRING_LENGTH_CASES = (
    pytest.param(
        {"min_length": 1},
        (("", "minimum length 1"), ("a", None), ("ab", None)),
        id="min_length",
    ),
    pytest.param(
        {"max_length": 3},
        (("", None), ("abc", None), ("abcd", "maximum length 3")),
        id="max_length",
    ),
    pytest.param(
        {"length": 2},
        (("ab", None), ("a", "expect the value of length 2"), ("abc", "expect the value of length 2")),
        id="exact_length",
    ),
    pytest.param(
        {"min_length": 1, "max_length": 3},
        (
            ("", "minimum length 1"),
            ("a", None),
            ("abc", None),
            ("abcd", "maximum length 3"),
        ),
        id="range_min_max",
    ),
    pytest.param(
        {"min_length": 0},
        (("", None), ("a", None)),
        id="min_length_zero",
    ),
    pytest.param(
        {"max_length": 0},
        (("", None), ("a", "maximum length 0")),
        id="max_length_zero",
    ),
    pytest.param(
        {"length": 0},
        (("", None), ("a", "expect the value of length 0")),
        id="exact_length_zero",
    ),
    pytest.param(
        {"min_length": 1, "length": 2, "max_length": 3},
        (
            ("", "minimum length 1"),
            ("a", "expect the value of length 2"),
            ("ab", None),
            ("abc", "expect the value of length 2"),
        ),
        id="min_exact_max",
    ),
)

_STRING_UNICODE_CASES = (
    pytest.param(
        {"max_length": 1},
        (
            (_ACCENT_NFC, None),  # 1 codepoint; would miss if UTF-8 bytes
            (_ACCENT_NFD, "maximum length 1"),  # 2 codepoints; would pass if graphemes
            (_EMOJI, None),  # 1 codepoint; 4 UTF-8 bytes
            (_NULL, None),
            ("", None),
        ),
        id="max_unicode_codepoints",
    ),
    pytest.param(
        {"min_length": 1},
        (
            ("", "minimum length 1"),
            (_ACCENT_NFC, None),
            (_ACCENT_NFD, None),
            (_EMOJI, None),
            (_FAMILY, None),
            (_NULL, None),
        ),
        id="min_unicode_codepoints",
    ),
    pytest.param(
        {"length": 1},
        (
            (_ACCENT_NFC, None),
            (_ACCENT_NFD, "expect the value of length 1"),
            (_EMOJI, None),
            ("", "expect the value of length 1"),
            ("ab", "expect the value of length 1"),
        ),
        id="exact_unicode_codepoints",
    ),
    pytest.param(
        {"length": len(_FAMILY)},
        ((_FAMILY, None), (_EMOJI, "expect the value of length")),
        id="family_zwj_codepoints",
    ),
)

_STRING_TYPE_SAMPLES = (1, True, False, None, b"ab", object(), 1.5)


def test_string_min_length_works_on_stdlib_path():
    @dataclass
    class Box:
        n: str = StringValidator(min_length=1, debug=True)

    assert Box(n="a").n == "a"
    assert Box(n=_ACCENT_NFC).n == _ACCENT_NFC
    with pytest.raises(ValueError, match="minimum length 1"):
        Box(n="")
    with pytest.raises((TypeError, ValidationErrors), match="expect"):
        Box(n=1)  # type: ignore[arg-type]


def test_host_string_length_is_codepoints_not_bytes_or_graphemes():
    """Door A lock: len(str) codepoints. NFC é is 1; NFD e+acute is 2."""
    assert len(_ACCENT_NFC) == 1
    assert len(_ACCENT_NFC.encode()) == 2
    assert len(_ACCENT_NFD) == 2
    assert len(_EMOJI) == 1
    assert len(_EMOJI.encode()) == 4
    assert len(_FAMILY) > 1
    field = _force_host(StringValidator(max_length=1, debug=True, name="n"))
    assert _assign(field, _ACCENT_NFC) == ("ok", None, None, _ACCENT_NFC)
    nfd = _assign(field, _ACCENT_NFD)
    assert nfd[0] == "err"
    assert nfd[1] is ValueError
    assert "maximum length 1" in nfd[2]
    assert _assign(field, _EMOJI) == ("ok", None, None, _EMOJI)
    assert _assign(field, "") == ("ok", None, None, "")
    assert _assign(field, _NULL) == ("ok", None, None, _NULL)


@pytest.mark.parametrize("kwargs,samples", (*_STRING_LENGTH_CASES, *_STRING_UNICODE_CASES))
def test_string_length_door_a_wording_on_host(kwargs, samples):
    field = _force_host(StringValidator(debug=True, name="n", **kwargs))
    for value, fragment in samples:
        got = _assign(field, value)
        if fragment is None:
            assert got == ("ok", None, None, value), (kwargs, value, got)
        else:
            assert got[0] == "err", (kwargs, value, got)
            assert got[1] is ValueError, (kwargs, value, got)
            assert fragment in got[2], (kwargs, value, got[2])


@needs_native
def test_string_min_length_compiles_once_at_bind():
    field = StringValidator(min_length=1, debug=True, name="n")
    plan = field._native_plan
    apply = field._native_apply
    assert plan is not None
    assert apply is not None

    @dataclass
    class Box:
        n: str = field

    assert field._native_plan is plan
    box = Box(n="a")
    box.n = "ab"
    box.n = "abc"
    assert field._native_plan is plan
    assert field._native_apply is apply


@needs_native
def test_one_ffi_apply_string_per_set():
    field = StringValidator(min_length=1, debug=True, name="n")

    @dataclass
    class Box:
        n: str = field

    assert field._native_plan is not None
    calls: list[str] = []
    orig = field._native_apply

    def counted(plan, value):
        calls.append(value)
        return orig(plan, value)

    field._native_apply = counted
    box = Box(n="a")
    box.n = "b"
    box.n = "c"
    assert calls == ["a", "b", "c"]


@needs_native
def test_validator_str_subscript_binds_at_set_name():
    field = Validator[str](min_length=1, debug=True)

    @dataclass
    class Box:
        n: str = field

    assert field.annotation is str
    assert field._native_plan is not None
    assert Box(n="ab").n == "ab"
    with pytest.raises(ValueError, match="minimum length"):
        Box(n="")


@needs_native
@pytest.mark.parametrize("kwargs,samples", (*_STRING_LENGTH_CASES, *_STRING_UNICODE_CASES))
def test_closed_string_length_compiles_once(kwargs, samples):
    field = StringValidator(debug=True, name="n", **kwargs)
    plan = field._native_plan
    apply = field._native_apply
    assert plan is not None
    assert apply is not None
    passing = next(value for value, fragment in samples if fragment is None)
    field.validate(None, passing)
    assert field._native_plan is plan
    assert field._native_apply is apply


@needs_native
@pytest.mark.parametrize("kwargs,samples", (*_STRING_LENGTH_CASES, *_STRING_UNICODE_CASES))
def test_native_string_parity_with_host_path(kwargs, samples):
    native = StringValidator(debug=True, name="n", **kwargs)
    host = _force_host(StringValidator(debug=True, name="n", **kwargs))
    assert native._native_plan is not None
    assert host._native_plan is None
    seen = [value for value, _fragment in samples]
    for value in (*seen, *_STRING_TYPE_SAMPLES, _SURROGATE):
        assert _assign_eq(_assign(native, value), _assign(host, value)), (kwargs, value)
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
            assert "utf-8" not in got[2].lower()
            assert "PyO3" not in got[2]


@needs_native
def test_native_string_uses_apply_string_not_numeric_apply():
    import ux_valio_native as peer

    field = StringValidator(min_length=1, debug=True, name="n")
    assert field._native_apply is peer.apply_string
    integer = IntegerValidator(min_value=0, debug=True, name="n")
    assert integer._native_apply is peer.apply
    floating = FloatValidator(min_value=0.0, debug=True, name="n")
    assert floating._native_apply is peer.apply_float


@needs_native
def test_native_string_none_skips_and_debug_false_swallows():
    @dataclass
    class Box:
        n: str = StringValidator(min_length=1, debug=True)

    assert Box(n=None).n is None  # type: ignore[arg-type]

    field = StringValidator(min_length=1, debug=False, name="n")
    assert field._native_plan is not None

    @dataclass
    class Quiet:
        n: str = field

    assert Quiet(n="").n is None
    assert field.errors
    assert any("minimum length" in str(err) for err in field.errors)


@needs_native
def test_native_string_collect_all_type_miss_matches_host():
    native = StringValidator(min_length=1, debug=True, name="n")
    host = _force_host(StringValidator(min_length=1, debug=True, name="n"))
    with pytest.raises(ValidationErrors) as native_caught:
        native.validate(None, 1)
    with pytest.raises(ValidationErrors) as host_caught:
        host.validate(None, 1)
    assert [str(err) for err in native_caught.value.errors] == [
        str(err) for err in host_caught.value.errors
    ]


@needs_native
def test_native_string_pre_validate_and_custom_still_run():
    @dataclass
    class Box:
        n: str = StringValidator(min_length=2, debug=True)

        @n.pre_validate
        def bump(self, value):
            return value + "x"

        @n.validator
        def no_z(self, value):
            if value is not None and "z" in value:
                raise ValueError("z")

    assert Box.__dict__["n"]._native_plan is not None
    assert Box(n="a").n == "ax"
    with pytest.raises(ValueError, match="minimum length"):
        Box(n="")
    with pytest.raises(ValueError, match="z"):
        Box(n="az")


@needs_native
def test_native_string_bytes_and_int_type_miss_match_host():
    native = StringValidator(min_length=1, debug=True, name="n")
    host = _force_host(StringValidator(min_length=1, debug=True, name="n"))
    assert native._native_plan is not None
    for value in (1, True, False, b"ab", bytearray(b"ab")):
        assert _assign_eq(_assign(native, value), _assign(host, value)), value
        got = _assign(native, value)
        assert got[0] == "err"
        assert got[1] in (TypeError, ValidationErrors)


@needs_native
def test_str_extract_overflow_falls_through_to_host():
    """Extract failure is a bridge signal, not an L1 miss."""
    native = StringValidator(min_length=1, debug=True, name="n")
    host = _force_host(StringValidator(min_length=1, debug=True, name="n"))
    assert native._native_plan is not None

    def boom(plan, value):
        raise OverflowError("str extract")

    native._native_apply = boom
    assert _assign(native, "a") == ("ok", None, None, "a")
    assert _assign_eq(_assign(native, "a"), _assign(host, "a"))
    miss = _assign(native, "")
    host_miss = _assign(host, "")
    assert miss == host_miss
    assert miss[1] is ValueError
    assert "minimum length 1" in miss[2]
    assert "Overflow" not in miss[2]
    assert "PyO3" not in miss[2]


@needs_native
def test_surrogate_extract_falls_through_to_host_len():
    """Lone surrogates are not UTF-8; host len(str) still owns Door A."""
    native = StringValidator(min_length=1, debug=True, name="n")
    host = _force_host(StringValidator(min_length=1, debug=True, name="n"))
    assert native._native_plan is not None
    assert _assign(native, _SURROGATE) == _assign(host, _SURROGATE)
    assert _assign(native, _SURROGATE) == ("ok", None, None, _SURROGATE)
    too_short = StringValidator(min_length=2, debug=True, name="n")
    host_short = _force_host(StringValidator(min_length=2, debug=True, name="n"))
    native_miss = _assign(too_short, _SURROGATE)
    host_miss = _assign(host_short, _SURROGATE)
    assert native_miss == host_miss
    assert native_miss[1] is ValueError
    assert "minimum length 2" in native_miss[2]
    assert "Overflow" not in native_miss[2]
    assert "utf-8" not in native_miss[2].lower()
    assert "encode" not in native_miss[2].lower()


@needs_native
def test_negative_and_huge_length_bind_stays_on_host():
    negative = StringValidator(min_length=-1, debug=True, name="n")
    assert negative._native_plan is None
    assert _assign(negative, "") == ("ok", None, None, "")
    huge = 2**70
    too_big = StringValidator(min_length=huge, debug=True, name="n")
    assert too_big._native_plan is None
    miss = _assign(too_big, "a")
    assert miss[0] == "err"
    assert miss[1] is ValueError
    assert "minimum length" in miss[2]
    assert "Overflow" not in miss[2]


@needs_native
def test_non_int_length_bound_stays_on_host():
    field = StringValidator(min_length=True, debug=True, name="n")
    assert field._native_plan is None
    floated = StringValidator(max_length=3.0, debug=True, name="n")
    assert floated._native_plan is None


@needs_native
def test_integer_float_string_paths_unchanged_with_bytes_plans():
    integer = IntegerValidator(min_value=0, debug=True, name="n")
    floating = FloatValidator(min_value=0.0, debug=True, name="n")
    text = StringValidator(min_length=1, debug=True, name="n")
    blob = BytesValidator(min_length=1, debug=True, name="n")
    assert integer._native_plan is not None
    assert floating._native_plan is not None
    assert text._native_plan is not None
    assert blob._native_plan is not None
    assert integer._native_apply is not blob._native_apply
    assert floating._native_apply is not blob._native_apply
    assert text._native_apply is not blob._native_apply
    assert _assign(integer, 1) == ("ok", None, None, 1)
    assert _assign(floating, 1.0) == ("ok", None, None, 1.0)
    assert _assign(text, "a") == ("ok", None, None, "a")
    assert _assign(blob, b"a") == ("ok", None, None, b"a")


@needs_native
def test_unexpected_string_peer_bind_raises_runtime_error(monkeypatch):
    import ux_valio_native

    def boom(**kwargs):
        raise ValueError("peer exploded")

    monkeypatch.setattr(ux_valio_native, "compile_string", boom)
    with pytest.raises(RuntimeError, match="ux_valio_native") as caught:
        StringValidator(min_length=1, debug=True, name="n")
    assert isinstance(caught.value.__cause__, ValueError)
    assert "Overflow" not in str(caught.value)
    assert "expect" not in str(caught.value)


@needs_native
def test_unexpected_string_peer_apply_raises_runtime_error():
    field = StringValidator(min_length=1, debug=True, name="n")
    assert field._native_plan is not None

    def boom(plan, value):
        raise ValueError("peer exploded")

    field._native_apply = boom
    with pytest.raises(RuntimeError, match="ux_valio_native") as caught:
        field.validate(None, "a")
    assert isinstance(caught.value.__cause__, ValueError)


@needs_native
def test_failkind_exposes_string_full_word_names():
    import ux_valio_native as peer

    assert hasattr(peer.FailKind, "MinLength")
    assert hasattr(peer.FailKind, "MaxLength")
    assert hasattr(peer.FailKind, "Length")
    assert not hasattr(peer.FailKind, "MinLen")
    assert not hasattr(peer.FailKind, "MaxLen")
    assert not hasattr(peer.FailKind, "Len")


# Door A: Python len(bytes) is byte count, not Unicode codepoints or graphemes.
_EMPTY = b""
_HIGH = b"\xff\xfe"
_NULL_B = b"\x00"
_UTF8_E_ACUTE = "é".encode()  # 2 bytes; 1 Unicode codepoint as str
_EMOJI_B = "\U0001f600".encode()  # 4 bytes; 1 Unicode codepoint as str

_BYTES_LENGTH_CASES = (
    pytest.param(
        {"min_length": 1},
        ((_EMPTY, "minimum length 1"), (b"a", None), (b"ab", None)),
        id="min_length",
    ),
    pytest.param(
        {"max_length": 3},
        ((_EMPTY, None), (b"abc", None), (b"abcd", "maximum length 3")),
        id="max_length",
    ),
    pytest.param(
        {"length": 2},
        (
            (b"ab", None),
            (b"a", "expect the value of length 2"),
            (b"abc", "expect the value of length 2"),
        ),
        id="exact_length",
    ),
    pytest.param(
        {"min_length": 1, "max_length": 3},
        (
            (_EMPTY, "minimum length 1"),
            (b"a", None),
            (b"abc", None),
            (b"abcd", "maximum length 3"),
        ),
        id="range_min_max",
    ),
    pytest.param(
        {"min_length": 0},
        ((_EMPTY, None), (b"a", None)),
        id="min_length_zero",
    ),
    pytest.param(
        {"max_length": 0},
        ((_EMPTY, None), (b"a", "maximum length 0")),
        id="max_length_zero",
    ),
    pytest.param(
        {"length": 0},
        ((_EMPTY, None), (b"a", "expect the value of length 0")),
        id="exact_length_zero",
    ),
    pytest.param(
        {"min_length": 1, "length": 2, "max_length": 3},
        (
            (_EMPTY, "minimum length 1"),
            (b"a", "expect the value of length 2"),
            (b"ab", None),
            (b"abc", "expect the value of length 2"),
        ),
        id="min_exact_max",
    ),
)

_BYTES_BINARY_CASES = (
    pytest.param(
        {"max_length": 1},
        (
            (b"\xff", None),
            (_HIGH, "maximum length 1"),
            (
                _UTF8_E_ACUTE,
                "maximum length 1",
            ),  # 2 UTF-8 bytes; would pass if codepoints
            (_EMOJI_B, "maximum length 1"),  # 4 UTF-8 bytes
            (_NULL_B, None),
            (_EMPTY, None),
        ),
        id="max_byte_count",
    ),
    pytest.param(
        {"min_length": 1},
        (
            (_EMPTY, "minimum length 1"),
            (b"\xff", None),
            (_HIGH, None),
            (_UTF8_E_ACUTE, None),
            (_EMOJI_B, None),
            (_NULL_B, None),
        ),
        id="min_byte_count",
    ),
    pytest.param(
        {"length": 2},
        (
            (_HIGH, None),
            (_UTF8_E_ACUTE, None),
            (b"\xff", "expect the value of length 2"),
            (_EMPTY, "expect the value of length 2"),
            (_EMOJI_B, "expect the value of length 2"),
        ),
        id="exact_byte_count",
    ),
    pytest.param(
        {"length": len(_EMOJI_B)},
        ((_EMOJI_B, None), (_HIGH, "expect the value of length")),
        id="emoji_utf8_byte_count",
    ),
)

_BYTES_TYPE_SAMPLES = (
    1,
    True,
    False,
    None,
    "ab",
    bytearray(b"ab"),
    memoryview(b"ab"),
    object(),
    1.5,
)


def test_bytes_min_length_works_on_stdlib_path():
    @dataclass
    class Box:
        n: bytes = BytesValidator(min_length=1, debug=True)

    assert Box(n=b"a").n == b"a"
    assert Box(n=_HIGH).n == _HIGH
    with pytest.raises(ValueError, match="minimum length 1"):
        Box(n=_EMPTY)
    with pytest.raises((TypeError, ValidationErrors), match="expect"):
        Box(n="ab")  # type: ignore[arg-type]


def test_host_bytes_length_is_byte_count_not_codepoints():
    """Door A lock: len(bytes) is byte count. UTF-8 é is 2; 0xFF is 1."""
    assert len(_EMPTY) == 0
    assert len(b"\xff") == 1
    assert len(_HIGH) == 2
    assert len(_UTF8_E_ACUTE) == 2
    assert len("é") == 1
    assert len(_EMOJI_B) == 4
    assert len("\U0001f600") == 1
    field = _force_host(BytesValidator(max_length=1, debug=True, name="n"))
    assert _assign(field, b"\xff") == ("ok", None, None, b"\xff")
    high = _assign(field, _HIGH)
    assert high[0] == "err"
    assert high[1] is ValueError
    assert "maximum length 1" in high[2]
    encoded = _assign(field, _UTF8_E_ACUTE)
    assert encoded[0] == "err"
    assert "maximum length 1" in encoded[2]
    assert _assign(field, _EMPTY) == ("ok", None, None, _EMPTY)
    assert _assign(field, _NULL_B) == ("ok", None, None, _NULL_B)


@pytest.mark.parametrize("kwargs,samples", (*_BYTES_LENGTH_CASES, *_BYTES_BINARY_CASES))
def test_bytes_length_door_a_wording_on_host(kwargs, samples):
    field = _force_host(BytesValidator(debug=True, name="n", **kwargs))
    for value, fragment in samples:
        got = _assign(field, value)
        if fragment is None:
            assert got == ("ok", None, None, value), (kwargs, value, got)
        else:
            assert got[0] == "err", (kwargs, value, got)
            assert got[1] is ValueError, (kwargs, value, got)
            assert fragment in got[2], (kwargs, value, got[2])


@needs_native
def test_bytes_min_length_compiles_once_at_bind():
    field = BytesValidator(min_length=1, debug=True, name="n")
    plan = field._native_plan
    apply = field._native_apply
    assert plan is not None
    assert apply is not None

    @dataclass
    class Box:
        n: bytes = field

    assert field._native_plan is plan
    box = Box(n=b"a")
    box.n = b"ab"
    box.n = b"abc"
    assert field._native_plan is plan
    assert field._native_apply is apply


@needs_native
def test_one_ffi_apply_bytes_per_set():
    field = BytesValidator(min_length=1, debug=True, name="n")

    @dataclass
    class Box:
        n: bytes = field

    assert field._native_plan is not None
    calls: list[bytes] = []
    orig = field._native_apply

    def counted(plan, value):
        calls.append(value)
        return orig(plan, value)

    field._native_apply = counted
    box = Box(n=b"a")
    box.n = b"b"
    box.n = b"c"
    assert calls == [b"a", b"b", b"c"]


@needs_native
def test_validator_bytes_subscript_binds_at_set_name():
    field = Validator[bytes](min_length=1, debug=True)

    @dataclass
    class Box:
        n: bytes = field

    assert field.annotation is bytes
    assert field._native_plan is not None
    assert Box(n=b"ab").n == b"ab"
    with pytest.raises(ValueError, match="minimum length"):
        Box(n=_EMPTY)


@needs_native
@pytest.mark.parametrize("kwargs,samples", (*_BYTES_LENGTH_CASES, *_BYTES_BINARY_CASES))
def test_closed_bytes_length_compiles_once(kwargs, samples):
    field = BytesValidator(debug=True, name="n", **kwargs)
    plan = field._native_plan
    apply = field._native_apply
    assert plan is not None
    assert apply is not None
    passing = next(value for value, fragment in samples if fragment is None)
    field.validate(None, passing)
    assert field._native_plan is plan
    assert field._native_apply is apply


@needs_native
@pytest.mark.parametrize("kwargs,samples", (*_BYTES_LENGTH_CASES, *_BYTES_BINARY_CASES))
def test_native_bytes_parity_with_host_path(kwargs, samples):
    native = BytesValidator(debug=True, name="n", **kwargs)
    host = _force_host(BytesValidator(debug=True, name="n", **kwargs))
    assert native._native_plan is not None
    assert host._native_plan is None
    seen = [value for value, _fragment in samples]
    for value in (*seen, *_BYTES_TYPE_SAMPLES):
        assert _assign_eq(_assign(native, value), _assign(host, value)), (kwargs, value)
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
            assert "utf-8" not in got[2].lower()
            assert "codepoint" not in got[2].lower()
            assert "PyO3" not in got[2]


@needs_native
def test_native_bytes_uses_apply_bytes_not_string_apply():
    import ux_valio_native as peer

    field = BytesValidator(min_length=1, debug=True, name="n")
    assert field._native_apply is peer.apply_bytes
    text = StringValidator(min_length=1, debug=True, name="n")
    assert text._native_apply is peer.apply_string
    integer = IntegerValidator(min_value=0, debug=True, name="n")
    assert integer._native_apply is peer.apply
    floating = FloatValidator(min_value=0.0, debug=True, name="n")
    assert floating._native_apply is peer.apply_float


@needs_native
def test_native_bytes_none_skips_and_debug_false_swallows():
    @dataclass
    class Box:
        n: bytes = BytesValidator(min_length=1, debug=True)

    assert Box(n=None).n is None  # type: ignore[arg-type]

    field = BytesValidator(min_length=1, debug=False, name="n")
    assert field._native_plan is not None

    @dataclass
    class Quiet:
        n: bytes = field

    assert Quiet(n=_EMPTY).n is None
    assert field.errors
    assert any("minimum length" in str(err) for err in field.errors)


@needs_native
def test_native_bytes_collect_all_type_miss_matches_host():
    native = BytesValidator(min_length=1, debug=True, name="n")
    host = _force_host(BytesValidator(min_length=1, debug=True, name="n"))
    with pytest.raises(ValidationErrors) as native_caught:
        native.validate(None, 1)
    with pytest.raises(ValidationErrors) as host_caught:
        host.validate(None, 1)
    assert [str(err) for err in native_caught.value.errors] == [
        str(err) for err in host_caught.value.errors
    ]


@needs_native
def test_native_bytes_pre_validate_and_custom_still_run():
    @dataclass
    class Box:
        n: bytes = BytesValidator(min_length=2, debug=True)

        @n.pre_validate
        def bump(self, value):
            return value + b"x"

        @n.validator
        def no_z(self, value):
            if value is not None and b"z" in value:
                raise ValueError("z")

    assert Box.__dict__["n"]._native_plan is not None
    assert Box(n=b"a").n == b"ax"
    with pytest.raises(ValueError, match="minimum length"):
        Box(n=_EMPTY)
    with pytest.raises(ValueError, match="z"):
        Box(n=b"az")


@needs_native
def test_native_bytes_str_and_bytearray_type_miss_match_host():
    native = BytesValidator(min_length=1, debug=True, name="n")
    host = _force_host(BytesValidator(min_length=1, debug=True, name="n"))
    assert native._native_plan is not None
    for value in (1, True, False, "ab", bytearray(b"ab"), memoryview(b"ab")):
        assert _assign_eq(_assign(native, value), _assign(host, value)), value
        got = _assign(native, value)
        assert got[0] == "err"
        assert got[1] in (TypeError, ValidationErrors)


@needs_native
def test_bytes_extract_overflow_falls_through_to_host():
    """Extract failure is a bridge signal, not an L1 miss."""
    native = BytesValidator(min_length=1, debug=True, name="n")
    host = _force_host(BytesValidator(min_length=1, debug=True, name="n"))
    assert native._native_plan is not None

    def boom(plan, value):
        raise OverflowError("bytes extract")

    native._native_apply = boom
    assert _assign(native, b"a") == ("ok", None, None, b"a")
    assert _assign_eq(_assign(native, b"a"), _assign(host, b"a"))
    miss = _assign(native, _EMPTY)
    host_miss = _assign(host, _EMPTY)
    assert miss == host_miss
    assert miss[1] is ValueError
    assert "minimum length 1" in miss[2]
    assert "Overflow" not in miss[2]
    assert "PyO3" not in miss[2]


@needs_native
def test_bytes_extract_type_miss_falls_through_to_host():
    """TypeError at extract is a bridge signal, not an L1 miss."""
    native = BytesValidator(min_length=1, debug=True, name="n")
    host = _force_host(BytesValidator(min_length=1, debug=True, name="n"))
    assert native._native_plan is not None

    def boom(plan, value):
        raise TypeError("bytes extract")

    native._native_apply = boom
    assert _assign(native, b"a") == ("ok", None, None, b"a")
    miss = _assign(native, _EMPTY)
    host_miss = _assign(host, _EMPTY)
    assert miss == host_miss
    assert miss[1] is ValueError
    assert "minimum length 1" in miss[2]
    assert "Overflow" not in miss[2]
    assert "extract" not in miss[2].lower()


@needs_native
def test_negative_and_huge_bytes_length_bind_stays_on_host():
    negative = BytesValidator(min_length=-1, debug=True, name="n")
    assert negative._native_plan is None
    assert _assign(negative, _EMPTY) == ("ok", None, None, _EMPTY)
    huge = 2**70
    too_big = BytesValidator(min_length=huge, debug=True, name="n")
    assert too_big._native_plan is None
    miss = _assign(too_big, b"a")
    assert miss[0] == "err"
    assert miss[1] is ValueError
    assert "minimum length" in miss[2]
    assert "Overflow" not in miss[2]


@needs_native
def test_non_int_bytes_length_bound_stays_on_host():
    field = BytesValidator(min_length=True, debug=True, name="n")
    assert field._native_plan is None
    floated = BytesValidator(max_length=3.0, debug=True, name="n")
    assert floated._native_plan is None


@needs_native
def test_unexpected_bytes_peer_bind_raises_runtime_error(monkeypatch):
    import ux_valio_native

    def boom(**kwargs):
        raise ValueError("peer exploded")

    monkeypatch.setattr(ux_valio_native, "compile_bytes", boom)
    with pytest.raises(RuntimeError, match="ux_valio_native") as caught:
        BytesValidator(min_length=1, debug=True, name="n")
    assert isinstance(caught.value.__cause__, ValueError)
    assert "Overflow" not in str(caught.value)
    assert "expect" not in str(caught.value)


@needs_native
def test_unexpected_bytes_peer_apply_raises_runtime_error():
    field = BytesValidator(min_length=1, debug=True, name="n")
    assert field._native_plan is not None

    def boom(plan, value):
        raise ValueError("peer exploded")

    field._native_apply = boom
    with pytest.raises(RuntimeError, match="ux_valio_native") as caught:
        field.validate(None, b"a")
    assert isinstance(caught.value.__cause__, ValueError)
