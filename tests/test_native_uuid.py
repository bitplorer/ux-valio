# SPDX-License-Identifier: MIT
"""Native module: Uuid type door (``Plan::Uuid``, ``uuid.UUID``).

No ``from __future__ import annotations`` — postponed ``int`` TypeErrors at bind (KEEP).
"""

import datetime
import re
import uuid
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
    DateValidator,
    EnumValidator,
    IPAddressValidator,
    IPv4Validator,
    IPv6Validator,
    PathValidator,
    UUIDValidator,
    ValidationErrors,
    Validator,
)

_TEXT = "12345678-1234-5678-1234-567812345678"
_SAMPLE = uuid.UUID(_TEXT)
_NIL = uuid.UUID(int=0)


class _ChildUUID(uuid.UUID):
    """Subclass still a ``uuid.UUID``. Same door as host ``isinstance``."""


def test_uuid_works_on_stdlib_path():
    @dataclass
    class Box:
        public_id: uuid.UUID = UUIDValidator(debug=True)

    assert Box(public_id=_SAMPLE).public_id == _SAMPLE
    assert Box(public_id=_TEXT).public_id == _SAMPLE
    assert Box(public_id=_TEXT.replace("-", "")).public_id == _SAMPLE
    assert Box(public_id="urn:uuid:" + _TEXT).public_id == _SAMPLE
    assert Box(public_id="{" + _TEXT + "}").public_id == _SAMPLE
    assert Box(public_id=_NIL).public_id == _NIL
    assert Box(public_id=None).public_id is None  # type: ignore[arg-type]
    with pytest.raises((TypeError, ValidationErrors), match="expect"):
        Box(public_id=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="UUID"):
        Box(public_id="not-a-uuid")


def test_closed_uuid_type_door_is_uuid_extract():
    """Uuid type is uuid.UUID extract. Compile and apply stay a pair."""
    rust = _native_rust()
    native_py = host_native_source()
    assert "fn compile_uuid" in rust
    assert "fn apply_uuid" in rust
    assert "Plan::Uuid" in rust
    assert "fn compile_and_apply" not in rust
    assert not re.search(r"\bfn compile\(", rust)
    assert not re.search(r"\bfn apply\(", rust)
    assert "fn compile_path" not in rust
    assert "fn compile_ip" not in rust
    assert "_closed_uuid" in native_py
    assert "_select_uuid" in native_py
    assert "apply_native_uuid" in native_py
    assert "_raise_host_uuid_type_miss" in native_py
    assert "_bridge_to_type" in native_py
    assert "_is_uuid_type_annotation" in native_py


@needs_native
def test_uuid_compiles_once_at_bind():
    import ux_valio_native as native

    field = UUIDValidator(debug=True)

    @dataclass
    class Box:
        public_id: uuid.UUID = field

    plan = field._native_plan
    assert plan is not None
    assert field._native_apply is native.apply_uuid
    assert field._native_apply is not native.apply_date
    assert field._native_run is not field._native_apply
    assert field.annotation == uuid.UUID | str
    box = Box(public_id=_SAMPLE)
    box.public_id = _NIL
    assert box.public_id == _NIL
    assert field._native_plan is plan
    assert field._native_apply is native.apply_uuid


@needs_native
def test_one_ffi_apply_uuid_per_set():
    field = UUIDValidator(debug=True, name="n")
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
    field.__set__(obj, _SAMPLE)
    field.__set__(obj, _TEXT)
    assert calls == [_SAMPLE, _SAMPLE]
    assert obj.n == _SAMPLE
    calls.clear()
    with pytest.raises((TypeError, ValidationErrors)):
        field.__set__(obj, 1)
    assert calls == []
    calls.clear()
    with pytest.raises(ValueError):
        field.__set__(obj, "not-a-uuid")
    assert calls == []


@needs_native
def test_native_uuid_parity_with_host():
    native = UUIDValidator(debug=True, name="n")
    host = _force_host(UUIDValidator(debug=True, name="n"))
    assert native._native_plan is not None
    assert host._native_plan is None
    child = _ChildUUID(_TEXT)
    samples = (
        _SAMPLE,
        _NIL,
        uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff"),
        child,
        _TEXT,
        _TEXT.upper(),
        _TEXT.replace("-", ""),
        "urn:uuid:" + _TEXT,
        "{" + _TEXT + "}",
        "not-a-uuid",
        "",
        1,
        True,
        False,
        None,
        b"\x12\x34\x56\x78" * 4,
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
def test_native_uuid_uses_apply_uuid_not_date_apply():
    import ux_valio_native as native

    field = UUIDValidator(debug=True, name="n")
    assert field._native_apply is native.apply_uuid
    assert field._native_apply is not native.apply_date
    plan = native.compile_uuid()
    assert native.apply_uuid(plan, _SAMPLE) is None
    assert native.apply_uuid(plan, _NIL) is None
    assert native.apply_uuid(plan, _ChildUUID(_TEXT)) is None
    with pytest.raises(TypeError):
        native.apply_uuid(plan, _TEXT)
    with pytest.raises(TypeError):
        native.apply_uuid(plan, 1)
    with pytest.raises(TypeError):
        native.apply_uuid(plan, True)
    with pytest.raises(TypeError):
        native.apply_uuid(plan, b"\x00" * 16)
    with pytest.raises(RuntimeError, match="apply_date plan family mismatch"):
        native.apply_date(plan, datetime.date(2020, 1, 2))


@needs_native
def test_uuid_unclosed_stays_on_host():
    assert UUIDValidator(min_value=_SAMPLE, debug=True, name="n")._native_plan is None
    assert UUIDValidator(required=True, debug=True, name="n")._native_plan is None
    assert UUIDValidator(reassign=False, debug=True, name="n")._native_plan is None
    assert UUIDValidator(in_choice=(_SAMPLE,), debug=True, name="n")._native_plan is None
    assert PathValidator(debug=True, name="n")._native_plan is None
    assert IPv4Validator(debug=True, name="n")._native_plan is None
    assert IPv6Validator(debug=True, name="n")._native_plan is None
    assert IPAddressValidator(debug=True, name="n")._native_plan is None
    assert EnumValidator(debug=True, name="n")._native_plan is None
    open_union = Validator[uuid.UUID | int](debug=True, name="n")
    assert open_union._native_plan is None
    optional = Validator[uuid.UUID | None](debug=True, name="n")
    assert optional._native_plan is None
    assert DateValidator(debug=True, name="n")._native_apply.__name__ == "apply_date"


@needs_native
def test_validator_uuid_subscript_compiles_at_set_name():
    import ux_valio_native as native

    field = Validator[uuid.UUID](debug=True, name="n")

    class Owner:
        pass

    Owner.__annotations__ = {"n": uuid.UUID}
    field.__set_name__(Owner, "n")
    assert field.annotation is uuid.UUID
    assert field._native_plan is not None
    assert field._native_apply is native.apply_uuid
    assert _assign(field, _SAMPLE)[3] == _SAMPLE
    assert _assign(field, _NIL)[3] == _NIL
    assert _assign(field, _TEXT)[1] is TypeError
    assert _assign(field, 1)[1] is TypeError


@needs_native
def test_uuid_none_skips_and_debug_false_swallows():
    @dataclass
    class Box:
        public_id: uuid.UUID = UUIDValidator(debug=True)

    assert Box(public_id=None).public_id is None  # type: ignore[arg-type]
    field = UUIDValidator(debug=True, name="n")
    field.debug = False
    assert field._native_plan is not None

    class Quiet:
        pass

    obj = Quiet()
    field.__set__(obj, 1)
    assert obj.__dict__.get("n") is None
    assert field.errors
    assert any("expect uuid.UUID | str type" in str(err) for err in field.errors)
    field.errors.clear()
    field.__set__(obj, _SAMPLE)
    assert obj.n == _SAMPLE


@needs_native
def test_native_uuid_collect_all_matches_host():
    native = UUIDValidator(debug=True, name="n")
    host = _force_host(UUIDValidator(debug=True, name="n"))
    samples = (
        _SAMPLE,
        _TEXT,
        "not-a-uuid",
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
def test_native_uuid_pre_validate_and_custom_still_run():
    @dataclass
    class Box:
        public_id: uuid.UUID = UUIDValidator(debug=True)

        @public_id.pre_validate
        def lift(self, value):
            if value == 1:
                return _SAMPLE
            return value

        @public_id.validator
        def not_nil(self, value):
            if value == _NIL:
                raise ValueError("nil")

    assert Box.__dict__["public_id"]._native_plan is not None
    assert Box(public_id=1).public_id == _SAMPLE  # type: ignore[arg-type]
    assert Box(public_id=_TEXT).public_id == _SAMPLE
    with pytest.raises(ValueError, match="nil"):
        Box(public_id=_NIL)


@needs_native
def test_uuid_extract_type_error_falls_through_to_host():
    native = UUIDValidator(debug=True, name="n")
    host = _force_host(UUIDValidator(debug=True, name="n"))
    assert native._native_plan is not None

    def boom(plan, value):
        raise TypeError("extract")

    native._native_apply = boom
    assert _assign(native, _SAMPLE)[3] == _SAMPLE
    assert _assign(host, _SAMPLE)[3] == _SAMPLE
    miss = _assign(native, 1)
    assert miss[1] is ValidationErrors
    assert "extract" not in miss[2]
    assert "Overflow" not in miss[2]


@needs_native
def test_unexpected_uuid_native_bind_raises_runtime_error(monkeypatch):
    import ux_valio_native

    def boom():
        raise ValueError("native exploded")

    monkeypatch.setattr(ux_valio_native, "compile_uuid", boom)
    with pytest.raises(RuntimeError, match="ux_valio_native") as caught:
        UUIDValidator(debug=True, name="n")
    assert isinstance(caught.value.__cause__, ValueError)
    assert "Overflow" not in str(caught.value)
    assert "expect" not in str(caught.value)


@needs_native
def test_unexpected_uuid_native_apply_raises_runtime_error():
    field = UUIDValidator(debug=True, name="n")
    assert field._native_plan is not None

    def boom(plan, value):
        raise ValueError("native exploded")

    field._native_apply = boom
    with pytest.raises(RuntimeError, match="ux_valio_native") as caught:
        field.validate(None, _SAMPLE)
    assert isinstance(caught.value.__cause__, ValueError)
