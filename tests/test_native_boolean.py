# SPDX-License-Identifier: MIT
"""Native peer: Boolean type door (``Plan::Boolean``, exact ``bool``).

No ``from __future__ import annotations`` — postponed ``int`` TypeErrors at bind (KEEP).
"""

import re
from dataclasses import dataclass

import pytest

from tests.native_support import (
    _assign,
    _force_host,
    _peer_rust,
    host_native_source,
    needs_native,
)
from ux_valio import (
    BooleanValidator,
    IntegerValidator,
    ValidationErrors,
    Validator,
)

def test_boolean_works_on_stdlib_path():
    @dataclass
    class Box:
        flag: bool = BooleanValidator(debug=True)

    assert Box(flag=True).flag is True
    assert Box(flag=False).flag is False
    with pytest.raises(TypeError, match="expect <class 'bool'> type, got int type instead"):
        Box(flag=1)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="expect <class 'bool'> type, got int type instead"):
        Box(flag=0)  # type: ignore[arg-type]


def test_closed_boolean_type_door_is_bool_extract():
    """Boolean type is exact bool extract. Compile and apply stay a pair."""
    rust = _peer_rust()
    native_py = host_native_source()
    assert "fn compile_boolean" in rust
    assert "fn apply_boolean" in rust
    assert "value: bool" in rust
    assert "Plan::Boolean" in rust
    assert "fn compile_and_apply" not in rust
    assert not re.search(r"\bfn compile\(", rust)
    assert not re.search(r"\bfn apply\(", rust)
    assert "_closed_boolean" in native_py
    assert "apply_native_boolean" in native_py
    assert "_raise_host_boolean_type_miss" in native_py
    assert "_apply_host_boolean_after_extract" in native_py
    assert "PyType" not in rust


@needs_native
def test_boolean_compiles_once_at_bind():
    import ux_valio_native as peer

    field = BooleanValidator(debug=True)

    @dataclass
    class Box:
        flag: bool = field

    plan = field._native_plan
    assert plan is not None
    assert field._native_ffi is peer.apply_boolean
    assert field._native_ffi is not peer.apply_integer
    assert field.annotation is bool
    box = Box(flag=False)
    box.flag = True
    box.flag = False
    assert box.flag is False
    assert field._native_plan is plan
    assert field._native_ffi is peer.apply_boolean


@needs_native
def test_one_ffi_apply_boolean_per_set():
    field = BooleanValidator(debug=True, name="n")
    assert field._native_plan is not None
    calls: list[object] = []
    orig = field._native_ffi

    def counted(plan, value):
        calls.append(value)
        return orig(plan, value)

    field._native_ffi = counted

    class Box:
        pass

    obj = Box()
    field.__set__(obj, True)
    field.__set__(obj, False)
    assert calls == [True, False]
    assert obj.n is False
    calls.clear()
    with pytest.raises(TypeError):
        field.__set__(obj, 1)
    with pytest.raises(TypeError):
        field.__set__(obj, 0)
    assert calls == []


@needs_native
def test_native_boolean_parity_with_host():
    native = BooleanValidator(debug=True, name="n")
    host = _force_host(BooleanValidator(debug=True, name="n"))
    assert native._native_plan is not None
    assert host._native_plan is None
    samples = (True, False, 1, 0, "true", "false", b"1", 1.0, None, object())
    for value in samples:
        got = _assign(native, value)
        host_got = _assign(host, value)
        assert got[:3] == host_got[:3], (value, got, host_got)
        if got[0] == "ok":
            assert got[3] is host_got[3]
        else:
            assert "Overflow" not in got[2]
            assert "PyO3" not in got[2]
            assert "coerce" not in got[2].lower()


@needs_native
def test_native_boolean_uses_apply_boolean_not_integer_apply():
    import ux_valio_native as peer

    field = BooleanValidator(debug=True, name="n")
    assert field._native_ffi is peer.apply_boolean
    assert field._native_ffi is not peer.apply_integer
    integer = IntegerValidator(min_value=0, debug=True, name="n")
    assert integer._native_ffi is peer.apply_integer
    assert _assign(integer, True)[3] is True
    plan = peer.compile_boolean()
    assert peer.apply_boolean(plan, True) is None
    assert peer.apply_boolean(plan, False) is None
    with pytest.raises(TypeError):
        peer.apply_boolean(plan, 1)
    with pytest.raises(TypeError):
        peer.apply_boolean(plan, 0)


@needs_native
def test_boolean_unclosed_stays_on_host():
    assert BooleanValidator(required=True, debug=True, name="n")._native_plan is None
    assert BooleanValidator(min_value=0, debug=True, name="n")._native_plan is None
    assert BooleanValidator(reassign=False, debug=True, name="n")._native_plan is None
    assert BooleanValidator(in_choice=(True,), debug=True, name="n")._native_plan is None
    plain = IntegerValidator(debug=True, name="n")
    assert plain._native_plan is None
    open_validator = Validator[int | bool](debug=True, name="n")
    assert open_validator._native_plan is None


@needs_native
def test_validator_bool_subscript_compiles_at_set_name():
    import ux_valio_native as peer

    field = Validator[bool](debug=True, name="n")

    class Owner:
        pass

    Owner.__annotations__ = {"n": bool}
    field.__set_name__(Owner, "n")
    assert field.annotation is bool
    assert field._native_plan is not None
    assert field._native_ffi is peer.apply_boolean
    assert _assign(field, False)[3] is False
    assert _assign(field, 1)[1] is TypeError


@needs_native
def test_boolean_none_skips_and_debug_false_swallows():
    @dataclass
    class Box:
        flag: bool = BooleanValidator(debug=True)

    assert Box(flag=None).flag is None  # type: ignore[arg-type]
    field = BooleanValidator(debug=True, name="n")
    field.debug = False
    assert field._native_plan is not None

    class Quiet:
        pass

    obj = Quiet()
    field.__set__(obj, 1)
    assert obj.__dict__.get("n") is None
    assert field.errors
    assert any("expect <class 'bool'> type" in str(err) for err in field.errors)
    field.errors.clear()
    field.__set__(obj, False)
    assert obj.n is False


@needs_native
def test_native_boolean_collect_all_matches_host():
    native = BooleanValidator(debug=True, name="n")
    host = _force_host(BooleanValidator(debug=True, name="n"))
    for value in (True, False, 1, 0, "x", None):
        native_err = None
        host_err = None
        try:
            native.validate(None, value)
        except (TypeError, ValidationErrors) as err:
            native_err = err
        try:
            host.validate(None, value)
        except (TypeError, ValidationErrors) as err:
            host_err = err
        assert type(native_err) is type(host_err)
        assert str(native_err) == str(host_err)


@needs_native
def test_native_boolean_pre_validate_and_custom_still_run():
    @dataclass
    class Box:
        flag: bool = BooleanValidator(debug=True)

        @flag.pre_validate
        def lift(self, value):
            if value == 1:
                return True
            return value

        @flag.validator
        def not_false(self, value):
            if value is False:
                raise ValueError("off")

    assert Box.__dict__["flag"]._native_plan is not None
    assert Box(flag=1).flag is True  # type: ignore[arg-type]
    assert Box(flag=True).flag is True
    with pytest.raises(ValueError, match="off"):
        Box(flag=False)


@needs_native
def test_boolean_extract_type_error_falls_through_to_host():
    native = BooleanValidator(debug=True, name="n")
    host = _force_host(BooleanValidator(debug=True, name="n"))
    assert native._native_plan is not None

    def boom(plan, value):
        raise TypeError("extract")

    native._native_ffi = boom
    assert _assign(native, True)[3] is True
    assert _assign(native, False)[3] is False
    assert _assign(host, False)[3] is False
    miss = _assign(native, 1)
    assert miss[1] is TypeError
    assert "extract" not in miss[2]
    assert "Overflow" not in miss[2]


@needs_native
def test_unexpected_boolean_peer_bind_raises_runtime_error(monkeypatch):
    import ux_valio_native

    def boom():
        raise ValueError("peer exploded")

    monkeypatch.setattr(ux_valio_native, "compile_boolean", boom)
    with pytest.raises(RuntimeError, match="ux_valio_native") as caught:
        BooleanValidator(debug=True, name="n")
    assert isinstance(caught.value.__cause__, ValueError)
    assert "Overflow" not in str(caught.value)
    assert "expect" not in str(caught.value)


@needs_native
def test_unexpected_boolean_peer_apply_raises_runtime_error():
    field = BooleanValidator(debug=True, name="n")
    assert field._native_plan is not None

    def boom(plan, value):
        raise ValueError("peer exploded")

    field._native_ffi = boom
    with pytest.raises(RuntimeError, match="ux_valio_native") as caught:
        field.validate(None, True)
    assert isinstance(caught.value.__cause__, ValueError)
