# SPDX-License-Identifier: MIT
"""Native module layout: public doors, bare names, cross-family, Cap OFF.

``Plan`` is one variant per family (``BoundUnit`` / ``LengthUnit`` /
member set / Boolean, Decimal, Date, DateTime, Uuid, and Path
type-door markers / an IP string-identity kind). No shared unit bag.
Plain Enum / Pattern stay HOLD. Cap Door B stays off.

No ``from __future__ import annotations`` — postponed ``int`` TypeErrors at bind (KEEP).
"""

import ast
import datetime
import decimal
import pathlib
import re
import uuid

import pytest

from tests.native_support import (
    FIELD_PATH_GLOBS,
    HOST_NATIVE_PATHS,
    ROOT,
    _HOLD,
    _native_rust,
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
    "compile_date",
    "apply_date",
    "compile_datetime",
    "apply_datetime",
    "compile_uuid",
    "apply_uuid",
    "compile_ip",
    "apply_ip",
    "compile_path",
    "apply_path",
)

_ABSENT_DOORS = (
    "compile",
    "apply",
    "compile_cap",
    "apply_cap",
)


@needs_native
def test_bare_compile_and_apply_are_absent_on_the_native_module():
    """Hard cut: doors are family-named. No alias remains.

    Plain Enum / Pattern stay HOLD. Cap Door B stays off this native module.
    """
    import ux_valio_native as native

    assert not hasattr(native, "compile")
    assert not hasattr(native, "apply")
    with pytest.raises(AttributeError):
        getattr(native, "compile")
    with pytest.raises(AttributeError):
        getattr(native, "apply")
    for name in _ABSENT_DOORS:
        assert not hasattr(native, name), name
        with pytest.raises(AttributeError):
            getattr(native, name)
    for name in _PUBLIC_DOORS:
        assert callable(getattr(native, name)), name
    assert {name for name in dir(native) if name.startswith("compile")} == {
        name for name in _PUBLIC_DOORS if name.startswith("compile")
    }
    assert {name for name in dir(native) if name.startswith("apply")} == {
        name for name in _PUBLIC_DOORS if name.startswith("apply")
    }
    assert callable(getattr(native, "compile_integer"))
    assert callable(getattr(native, "apply_integer"))
    assert not hasattr(native, "PyPlan")
    plan = native.compile_integer(min_value=0)
    assert type(plan).__name__ == "Plan"
    rust = _native_rust()
    assert "fn compile_date" in rust
    assert "fn apply_date" in rust
    assert "Plan::Date" in rust
    assert "fn compile_datetime" in rust
    assert "fn apply_datetime" in rust
    assert "fn compile_uuid" in rust
    assert "fn apply_uuid" in rust
    assert "Plan::Uuid" in rust
    assert "fn compile_ip" in rust
    assert "fn apply_ip" in rust
    assert "Plan::Ip" in rust
    assert "fn compile_path" in rust
    assert "fn apply_path" in rust
    assert "Plan::Path" in rust


@needs_native
def test_apply_door_rejects_a_different_family():
    """Wrong family is an error at the door. The walk does not run."""
    import ux_valio_native as native

    integer = native.compile_integer(min_value=0)
    text = native.compile_string(min_length=1)
    with pytest.raises(RuntimeError, match="apply_integer plan family mismatch"):
        native.apply_integer(text, 1)
    with pytest.raises(RuntimeError, match="apply_string plan family mismatch"):
        native.apply_string(integer, "ab")
    assert native.apply_integer(integer, 1) is None
    assert native.apply_string(text, "ab") is None

    doors = (
        ("apply_integer", native.compile_integer(min_value=0), 1),
        ("apply_float", native.compile_float(min_value=0.0), 1.0),
        ("apply_string", native.compile_string(min_length=1), "ab"),
        ("apply_bytes", native.compile_bytes(min_length=1), b"ab"),
        ("apply_integer_enum", native.compile_integer_enum([1]), 1),
        ("apply_string_enum", native.compile_string_enum(["ab"]), "ab"),
        ("apply_boolean", native.compile_boolean(), True),
        ("apply_decimal", native.compile_decimal(), decimal.Decimal("1")),
        ("apply_date", native.compile_date(), datetime.date(2020, 1, 2)),
        (
            "apply_datetime",
            native.compile_datetime(),
            datetime.datetime(2020, 1, 2, 3, 4),
        ),
        (
            "apply_uuid",
            native.compile_uuid(),
            uuid.UUID("12345678-1234-5678-1234-567812345678"),
        ),
        ("apply_ip", native.compile_ip("ipv4"), "127.0.0.1"),
        ("apply_path", native.compile_path(), pathlib.Path("/tmp/ux-valio-path")),
    )
    for door, plan, sample in doors:
        assert getattr(native, door)(plan, sample) is None
        for other, _other_plan, other_sample in doors:
            if other == door:
                continue
            with pytest.raises(RuntimeError, match=f"{other} plan family mismatch"):
                getattr(native, other)(plan, other_sample)


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

    Family sections share one bind table. That split stays out.
    ``_native.py`` is the host door.
    """
    validators = ROOT / "ux_valio" / "validators"
    assert (validators / "_native.py").is_file()
    extra = sorted(path.name for path in validators.glob("_native_*.py"))
    assert extra == []


_FAMILY_SECTIONS = (
    (
        "# --- Integer ---",
        (
            "def _closed_integer_bounds(",
            "def apply_native_integer_bounds(",
            "_INTEGER_DOOR",
            "_raise_host_value_type_miss",
        ),
    ),
    (
        "# --- Float ---",
        (
            "def _closed_float_bounds(",
            "def apply_native_float_bounds(",
            "_FLOAT_DOOR",
            "_raise_host_value_type_miss",
        ),
    ),
    (
        "# --- String ---",
        (
            "def _closed_string_length(",
            "def apply_native_string_length(",
            "_STRING_DOOR",
            "_raise_host_length_type_miss",
        ),
    ),
    (
        "# --- Bytes ---",
        (
            "def _closed_bytes_length(",
            "def apply_native_bytes_length(",
            "_BYTES_DOOR",
            "_raise_host_length_type_miss",
        ),
    ),
    (
        "# --- IntegerEnum ---",
        (
            "def _closed_integer_enum_members(",
            "def apply_native_integer_enum(",
            "_INTEGER_ENUM_DOOR",
            "_read_owner_annotation",
        ),
    ),
    (
        "# --- StringEnum ---",
        (
            "def _closed_string_enum_members(",
            "def apply_native_string_enum(",
            "_STRING_ENUM_DOOR",
            "value.value",
        ),
    ),
    (
        "# --- Boolean ---",
        (
            "def _closed_boolean(",
            "def _raise_host_boolean_type_miss(",
            "def apply_native_boolean(",
            "_BOOLEAN_DOOR",
        ),
    ),
    (
        "# --- Decimal ---",
        (
            "def _is_decimal_type_annotation(",
            "def _closed_decimal(",
            "def _raise_host_decimal_type_miss(",
            "def apply_native_decimal(",
            "_DECIMAL_DOOR",
        ),
    ),
    (
        "# --- Date ---",
        (
            "def _is_date_type_annotation(",
            "def _closed_date(",
            "def _raise_host_date_type_miss(",
            "def apply_native_date(",
            "_DATE_DOOR",
        ),
    ),
    (
        "# --- DateTime ---",
        (
            "def _is_datetime_type_annotation(",
            "def _closed_datetime(",
            "def _raise_host_datetime_type_miss(",
            "def apply_native_datetime(",
            "_DATETIME_DOOR",
        ),
    ),
    (
        "# --- UUID ---",
        (
            "def _is_uuid_type_annotation(",
            "def _closed_uuid(",
            "def _raise_host_uuid_type_miss(",
            "def apply_native_uuid(",
            "_UUID_DOOR",
        ),
    ),
    (
        "# --- IP ---",
        (
            "def _read_ip_facade(",
            "def _reject_ip_string(",
            "def _bridge_to_ip(",
            "def _closed_ip(",
            "def _raise_host_ip_type_miss(",
            "def apply_native_ip(",
            "_IP_DOOR",
            "NotIp",
        ),
    ),
    (
        "# --- Path ---",
        (
            "def _is_path_type_annotation(",
            "def _closed_path(",
            "def _raise_host_path_type_miss(",
            "def apply_native_path(",
            "_PATH_DOOR",
        ),
    ),
)


def test_native_families_are_contiguous_sections():
    """Each Door A family is one banner. Shared helpers stay outside.

    ``_FamilyDoor`` is the private bind row. Cap stays absent.
    No class-per-type product surface.
    """
    native_py = host_native_source()
    assert "class _FamilyDoor" in native_py
    assert "def _select(" in native_py
    assert "def _select_" not in native_py
    assert "def _run_closed(" in native_py
    assert "compile_attr" not in native_py
    assert "apply_attr" not in native_py
    assert "def _fill_door" not in native_py
    assert "def _pack_members" not in native_py
    assert "compile_cap" not in native_py
    assert "apply_cap" not in native_py
    assert "class IntegerNative" not in native_py
    assert "class FloatNative" not in native_py
    starts = [native_py.index(banner) for banner, _names in _FAMILY_SECTIONS]
    assert starts == sorted(starts)
    bind_at = native_py.index("# --- Bind walk ---")
    assert bind_at > starts[-1]
    for name in (
        "def _closed_value_bounds(",
        "def _closed_length(",
        "def _closed_type_door(",
        "def _is_stored_or_str_annotation(",
        "def _raise_native_bound_miss(",
        "def _raise_host_value_type_miss(",
        "def _raise_host_length_type_miss(",
        "def _raise_host_enum_type_miss(",
        "def _read_owner_annotation(",
        "def _run_closed(",
    ):
        assert native_py.index(name) < starts[0], name
    for gone in (
        "def _apply_native_closed(",
        "def _raise_host_integer_type_miss(",
        "def _raise_host_float_type_miss(",
        "def _raise_host_string_type_miss(",
        "def _raise_host_bytes_type_miss(",
    ):
        assert gone not in native_py, gone
    for index, (banner, names) in enumerate(_FAMILY_SECTIONS):
        end = starts[index + 1] if index + 1 < len(starts) else bind_at
        section = native_py[starts[index] : end]
        for name in names:
            assert name in section, (banner, name)
        if banner == "# --- StringEnum ---":
            assert "_run_closed" not in section
    table = native_py[native_py.index("_FAMILY_DOORS") : native_py.index("def apply_native_bounds(")]
    cursor = -1
    for door_name in (
        "_INTEGER_DOOR",
        "_FLOAT_DOOR",
        "_STRING_DOOR",
        "_BYTES_DOOR",
        "_INTEGER_ENUM_DOOR",
        "_STRING_ENUM_DOOR",
        "_BOOLEAN_DOOR",
        "_DECIMAL_DOOR",
        "_DATE_DOOR",
        "_DATETIME_DOOR",
        "_UUID_DOOR",
        "_IP_DOOR",
        "_PATH_DOOR",
    ):
        at = table.index(door_name)
        assert at > cursor
        cursor = at
    assert native_py.index("def bind_native_plan(") > bind_at


def test_closed_apply_slot_is_seeded_on_validator():
    """Fourth slot is the closed Python run.

    ``Validator.__init__`` seeds it ``None``. Product-PyO3 Rust FFI stays
    ``_native_apply``. ``bind_native_plan`` writes ``apply_native_*``
    onto ``_native_run``. ``apply_native_bounds`` reads the
    attribute directly.
    """
    plain = IntegerValidator(debug=True, name="n")
    assert plain._native_plan is None
    assert plain._native_apply is None
    assert plain._native_fail_kind is None
    assert plain._native_run is None
    native_py = host_native_source()
    facade = (ROOT / "ux_valio" / "validators" / "facade.py").read_text()
    assert "owner._native_run" in native_py
    assert "self._native_run = None" in facade
    assert 'getattr(owner, "_native_run"' not in native_py
    assert "run = owner._native_run" in native_py


@needs_native
def test_bind_writes_closed_host_apply():
    """Closed bind stores ``apply_native_*`` on ``_native_run``.

    Product-PyO3 Rust FFI stays ``_native_apply``.
    """
    import ux_valio_native as native
    from ux_valio.validators._native import (
        apply_native_float_bounds,
        apply_native_integer_bounds,
    )

    field = IntegerValidator(min_value=0, debug=True, name="n")
    assert field._native_plan is not None
    assert field._native_apply is native.apply_integer
    assert field._native_run is apply_native_integer_bounds
    assert field._native_run is not field._native_apply
    floating = FloatValidator(min_value=0.0, debug=True, name="n")
    assert floating._native_apply is native.apply_float
    assert floating._native_run is apply_native_float_bounds
    assert floating._native_run is not floating._native_apply


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
    rust = _native_rust()
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
    assert re.search(r"^\s+Date,$", rust, re.M)
    assert re.search(r"^\s+DateTime,$", rust, re.M)
    assert "fn apply_bound_units" in rust
    assert "units: &[BoundUnit<T>]" in rust
    assert "fn apply_length_units" in rust
    assert "units: &[LengthUnit]" in rust


def test_native_unit_names_are_full_words():
    """Rust variants are parallel full words; host kwargs stay min_value/gt/…."""
    rust = _native_rust()
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
