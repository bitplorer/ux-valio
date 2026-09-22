# SPDX-License-Identifier: MIT
"""Native peer layout: public doors, bare names, cross-family, Cap OFF.

``Plan`` is one variant per family (``BoundUnit`` / ``LengthUnit`` /
member set / Boolean and Decimal type-door markers). No shared unit
bag. Date* stays HOLD. Cap Door B stays off.

No ``from __future__ import annotations`` — postponed ``int`` TypeErrors at bind (KEEP).
"""

import ast
import decimal
import re

import pytest

from tests.native_support import (
    FIELD_PATH_GLOBS,
    HOST_NATIVE_PATHS,
    ROOT,
    _HOLD,
    _peer_rust,
    host_native_source,
    needs_native,
)
from ux_valio import (
    BooleanValidator,
    BytesValidator,
    FloatValidator,
    IntegerValidator,
    StringValidator,
    Validator,
)

def test_native_is_not_a_taught_import():
    import ux_valio

    assert "ux_valio_native" not in ux_valio.__all__
    assert not hasattr(ux_valio, "ux_valio_native")
    assert not hasattr(ux_valio, "compile")
    assert not hasattr(ux_valio, "Plan")


_PUBLIC_DOORS = (
    "compile_integer",
    "apply_integer",
    "compile_float",
    "apply_float",
    "compile_string",
    "apply_string",
    "compile_bytes",
    "apply_bytes",
    "compile_integer_enum",
    "apply_integer_enum",
    "compile_string_enum",
    "apply_string_enum",
    "compile_boolean",
    "apply_boolean",
    "compile_decimal",
    "apply_decimal",
)

_ABSENT_DOORS = (
    "compile",
    "apply",
    "compile_date",
    "apply_date",
    "compile_datetime",
    "apply_datetime",
    "compile_cap",
    "apply_cap",
)


@needs_native
def test_bare_compile_and_apply_are_absent_on_the_peer():
    """Hard cut: doors are family-named. No alias remains.

    Date* stays HOLD. Cap Door B stays off this peer.
    """
    import ux_valio_native as peer

    assert not hasattr(peer, "compile")
    assert not hasattr(peer, "apply")
    with pytest.raises(AttributeError):
        getattr(peer, "compile")
    with pytest.raises(AttributeError):
        getattr(peer, "apply")
    for name in _ABSENT_DOORS:
        assert not hasattr(peer, name), name
        with pytest.raises(AttributeError):
            getattr(peer, name)
    for name in _PUBLIC_DOORS:
        assert callable(getattr(peer, name)), name
    assert {name for name in dir(peer) if name.startswith("compile")} == {
        name for name in _PUBLIC_DOORS if name.startswith("compile")
    }
    assert {name for name in dir(peer) if name.startswith("apply")} == {
        name for name in _PUBLIC_DOORS if name.startswith("apply")
    }
    assert callable(getattr(peer, "compile_integer"))
    assert callable(getattr(peer, "apply_integer"))
    assert not hasattr(peer, "PyPlan")
    plan = peer.compile_integer(min_value=0)
    assert type(plan).__name__ == "Plan"
    rust = _peer_rust()
    assert "fn compile_date" not in rust
    assert "fn apply_date" not in rust
    assert "Plan::Date" not in rust
    assert "fn compile_datetime" not in rust
    assert "fn apply_datetime" not in rust


@needs_native
def test_apply_door_rejects_a_different_family():
    """Wrong family is an error at the door. The walk does not run."""
    import ux_valio_native as peer

    integer = peer.compile_integer(min_value=0)
    text = peer.compile_string(min_length=1)
    with pytest.raises(RuntimeError, match="apply_integer plan family mismatch"):
        peer.apply_integer(text, 1)
    with pytest.raises(RuntimeError, match="apply_string plan family mismatch"):
        peer.apply_string(integer, "ab")
    assert peer.apply_integer(integer, 1) is None
    assert peer.apply_string(text, "ab") is None

    doors = (
        ("apply_integer", peer.compile_integer(min_value=0), 1),
        ("apply_float", peer.compile_float(min_value=0.0), 1.0),
        ("apply_string", peer.compile_string(min_length=1), "ab"),
        ("apply_bytes", peer.compile_bytes(min_length=1), b"ab"),
        ("apply_integer_enum", peer.compile_integer_enum([1]), 1),
        ("apply_string_enum", peer.compile_string_enum(["ab"]), "ab"),
        ("apply_boolean", peer.compile_boolean(), True),
        ("apply_decimal", peer.compile_decimal(), decimal.Decimal("1")),
    )
    for door, plan, sample in doors:
        assert getattr(peer, door)(plan, sample) is None
        for other, _other_plan, other_sample in doors:
            if other == door:
                continue
            with pytest.raises(RuntimeError, match=f"{other} plan family mismatch"):
                getattr(peer, other)(plan, other_sample)


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

    assert HOST_NATIVE_PATHS
    json_imports = []
    for native_py in HOST_NATIVE_PATHS:
        assert native_py.is_file()
        tree = ast.parse(native_py.read_text(), filename=str(native_py))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "json" or alias.name.startswith("json."):
                        json_imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                if node.module == "json" or node.module.startswith("json."):
                    json_imports.append(node.module)
    assert json_imports == []


def test_host_native_is_one_file():
    """Private modules only when one file is one family walk.

    Closed / apply / select siblings mix every family. That split
    stays out. ``_native.py`` is the host door.
    """
    validators = ROOT / "ux_valio" / "validators"
    assert (validators / "_native.py").is_file()
    extra = sorted(path.name for path in validators.glob("_native_*.py"))
    assert extra == []


def test_closed_apply_slot_is_seeded_on_validator():
    """Fourth slot is the closed host apply.

    ``Validator.__init__`` seeds it ``None``. Peer FFI apply stays
    ``_native_apply``. ``bind_native_plan`` writes ``apply_native_*``
    onto ``_native_closed_apply``. ``apply_native_bounds`` reads the
    attribute directly.
    """
    plain = IntegerValidator(debug=True, name="n")
    assert plain._native_plan is None
    assert plain._native_apply is None
    assert plain._native_fail is None
    assert plain._native_closed_apply is None
    native_py = host_native_source()
    facade = (ROOT / "ux_valio" / "validators" / "facade.py").read_text()
    assert "owner._native_closed_apply" in native_py
    assert "self._native_closed_apply = None" in facade
    assert 'getattr(owner, "_native_closed_apply"' not in native_py
    assert "closed_apply = owner._native_closed_apply" in native_py


@needs_native
def test_bind_writes_closed_host_apply():
    """Closed bind stores ``apply_native_*`` on ``_native_closed_apply``.

    Peer FFI apply stays ``_native_apply``.
    """
    import ux_valio_native as peer
    from ux_valio.validators._native import (
        apply_native_float_bounds,
        apply_native_integer_bounds,
    )

    field = IntegerValidator(min_value=0, debug=True, name="n")
    assert field._native_plan is not None
    assert field._native_apply is peer.apply_integer
    assert field._native_closed_apply is apply_native_integer_bounds
    assert field._native_closed_apply is not field._native_apply
    floating = FloatValidator(min_value=0.0, debug=True, name="n")
    assert floating._native_apply is peer.apply_float
    assert floating._native_closed_apply is apply_native_float_bounds
    assert floating._native_closed_apply is not floating._native_apply


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
    boolean_required = BooleanValidator(required=True, debug=True, name="n")
    assert boolean_required._native_plan is None
    boolean_choice = BooleanValidator(in_choice=(True, False), debug=True, name="n")
    assert boolean_choice._native_plan is None
    boolean_bound = BooleanValidator(min_value=0, debug=True, name="n")
    assert boolean_bound._native_plan is None
    boolean_watched = BooleanValidator(reassign=False, debug=True, name="n")
    assert boolean_watched._native_plan is None


def test_plan_shape_is_owned_unit_list():
    """Each family variant owns its checks. No shared ``Unit`` bag."""
    rust = _peer_rust()
    assert "units: [Unit; 2]" not in rust
    assert "enum Unit" not in rust
    assert "Vec<Unit>" not in rust
    assert "enum Plan" in rust
    assert "Integer(Arc<Vec<BoundUnit<i64>>>)" in rust
    assert "Float(Arc<Vec<BoundUnit<f64>>>)" in rust
    assert "String(Arc<Vec<LengthUnit>>)" in rust
    assert "Bytes(Arc<Vec<LengthUnit>>)" in rust
    assert "IntegerEnum(Arc<Vec<i64>>)" in rust
    assert "StringEnum(Arc<Vec<String>>)" in rust
    assert "fn apply_bound_units" in rust
    assert "units: &[BoundUnit<T>]" in rust
    assert "fn apply_length_units" in rust
    assert "units: &[LengthUnit]" in rust


def test_native_unit_names_are_full_words():
    """Rust variants are parallel full words; host kwargs stay min_value/gt/…."""
    rust = _peer_rust()
    assert re.search(r"\bMinValue\(T\)", rust)
    assert re.search(r"\bMaxValue\(T\)", rust)
    assert re.search(r"\bGreaterThan\(T\)", rust)
    assert re.search(r"\bLessThan\(T\)", rust)
    assert re.search(r"\bEqual\(T\)", rust)
    assert re.search(r"BoundUnit<i64>", rust)
    assert re.search(r"BoundUnit<f64>", rust)
    assert re.search(r"\bMinLength\(usize\)", rust)
    assert re.search(r"\bMaxLength\(usize\)", rust)
    assert re.search(r"\bLength\(usize\)", rust)
    assert re.search(r"\bIntegerEnum\b", rust)
    assert re.search(r"\bStringEnum\b", rust)
    assert not re.search(r"\bMember\(i64\)", rust)
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
    assert re.search(r"^\s+NotMember =", rust, re.M)
    assert not re.search(r"^\s+Gt =", rust, re.M)
    assert not re.search(r"^\s+Lt =", rust, re.M)
    assert not re.search(r"^\s+Eq =", rust, re.M)
    assert not re.search(r"\bMinLen\b", rust)
    assert not re.search(r"\bMaxLen\b", rust)
    native_py = host_native_source()
    assert re.search(r"\bmatch fail:", native_py)
    assert not re.search(r"if fail == kinds\.", native_py)
    assert re.search(r"\bkinds\.GreaterThan\b", native_py)
    assert re.search(r"\bkinds\.LessThan\b", native_py)
    assert re.search(r"\bkinds\.Equal\b", native_py)
    assert re.search(r"\bkinds\.MinLength\b", native_py)
    assert re.search(r"\bkinds\.MaxLength\b", native_py)
    assert re.search(r"\bkinds\.Length\b", native_py)
    assert re.search(r"\bkinds\.NotMember\b", native_py)
    assert not re.search(r"\bkinds\.Gt\b", native_py)
    assert not re.search(r"\bkinds\.Lt\b", native_py)
    assert not re.search(r"\bkinds\.Eq\b", native_py)
    assert not re.search(r"\bkinds\.MinLen\b", native_py)
    assert not re.search(r"\bkinds\.MaxLen\b", native_py)


def test_open_type_stays_on_host():
    union = Validator[int | str](min_value=0, debug=True, name="n")
    assert union.annotation is not int
    assert union._native_plan is None
    union_float = Validator[float | str](min_value=0.0, debug=True, name="n")
    assert union_float.annotation is not float
    assert union_float._native_plan is None
