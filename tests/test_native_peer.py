# SPDX-License-Identifier: MIT
"""Optional ``ux-valio[native]`` peer: Integer + MinValue, host soul.

Without the extra, stdlib apply stays the default (CI). With the extra,
``IntegerValidator(min_value=0)`` compiles once and one FFI ``apply``
per set. Cap Door B / Ops / JSON / ``cek-peer-*`` stay off the field path.

No ``from __future__ import annotations`` — postponed ``int`` TypeErrors
at bind (KEEP).
"""

import ast
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
    field._native_plan = None
    field._native_apply = None
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
    extra = IntegerValidator(min_value=0, max_value=10, debug=True)
    assert extra._native_plan is None
    required = IntegerValidator(min_value=0, required=True, debug=True)
    assert required._native_plan is None
    gt = IntegerValidator(gt=0, debug=True)
    assert gt._native_plan is None
    plain = IntegerValidator(debug=True)
    assert plain._native_plan is None
    floating = FloatValidator(min_value=0.0, debug=True)
    assert getattr(floating, "_native_plan", None) is None
    text = StringValidator(min_length=1, debug=True)
    assert getattr(text, "_native_plan", None) is None


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
def test_native_parity_with_host_path():
    native = IntegerValidator(min_value=0, debug=True, name="n")
    host = _force_host(IntegerValidator(min_value=0, debug=True, name="n"))
    assert native._native_plan is not None
    assert host._native_plan is None
    samples = (0, 1, -1, "x", None, True, False, 2**70, -(2**70), 1.5, object())
    for value in samples:
        assert _assign(native, value) == _assign(host, value), value


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
