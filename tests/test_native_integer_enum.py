# SPDX-License-Identifier: MIT
"""Native peer: IntegerEnum member-set plans (``Plan::IntegerEnum``).

No ``from __future__ import annotations`` — postponed ``int`` TypeErrors at bind (KEEP).
"""

import enum
import re
from dataclasses import dataclass

import pytest

from tests.native_support import (
    _assign,
    _bind_enum_field,
    _enum_door,
    _force_host,
    _peer_rust,
    host_native_source,
    needs_native,
)
from ux_valio import (
    BooleanValidator,
    EnumValidator,
    IntegerEnumValidator,
    IntegerValidator,
    StringEnumValidator,
    ValidationErrors,
    Validator,
)

class _Rank(enum.IntEnum):
    LOW = 1
    HIGH = 2
    ZERO = 0
    NEG = -3
    ALSO = 1


class _Other(enum.IntEnum):
    NOPE = 9
    LOW = 1


class _Color(enum.Enum):
    RED = "red"


class _Shade(enum.Enum):
    PALE = "pale"


class _HugeRank(enum.IntEnum):
    BIG = 2**70
    SMALL = 1


class _EdgeRank(enum.IntEnum):
    MAX = 2**63 - 1
    MIN = -(2**63)


class _OverRank(enum.IntEnum):
    OVER = 2**63


def test_integer_enum_works_on_stdlib_path():
    @dataclass
    class Grade:
        r: _Rank = IntegerEnumValidator(debug=True)

    assert Grade(r=_Rank.LOW).r is _Rank.LOW
    assert Grade(r=_Rank.ZERO).r is _Rank.ZERO
    assert Grade(r=_Rank.ALSO).r is _Rank.LOW
    with pytest.raises(TypeError, match="expect <enum '_Rank'> type, got _Other type instead"):
        Grade(r=_Other.NOPE)
    with pytest.raises(ValidationErrors, match="expect <enum '_Rank'> type"):
        Grade(r=1)


def test_integer_enum_l1_has_no_members_kwarg():
    with pytest.raises(TypeError):
        IntegerEnumValidator(members=(1, 2))


def test_closed_integer_enum_type_door_is_i64_extract():
    """IntegerEnum type is i64 extract. Compile and apply stay a pair."""
    rust = _peer_rust()
    native_py = host_native_source()
    assert "fn compile_integer_enum" in rust
    assert "fn apply_integer_enum" in rust
    assert "Plan::IntegerEnum" in rust
    assert "IntegerEnum(Arc<Vec<i64>>)" in rust
    assert "FailKind::NotMember" in rust
    assert "fn compile_and_apply" not in rust
    assert "_closed_integer_enum_members" in native_py
    assert "apply_native_integer_enum" in native_py
    assert "_raise_host_integer_enum_type_miss" in native_py
    assert "_apply_host_integer_enum_after_i64_overflow" in native_py
    assert "kinds.NotMember" in native_py
    assert not re.search(r"if fail == kinds\.", native_py)


@needs_native
def test_integer_enum_compiles_once_at_bind():
    field = IntegerEnumValidator(debug=True)

    @dataclass
    class Box:
        n: _Rank = field

    plan = field._native_plan
    apply = field._native_ffi
    assert plan is not None
    assert apply is not None
    assert field.annotation is _Rank
    box = Box(n=_Rank.LOW)
    box.n = _Rank.HIGH
    box.n = _Rank.ZERO
    assert box.n is _Rank.ZERO
    assert field._native_plan is plan
    assert field._native_ffi is apply


@needs_native
def test_one_ffi_apply_integer_enum_per_set():
    field = _bind_enum_field(_Rank)
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
    field.__set__(obj, _Rank.LOW)
    field.__set__(obj, _Rank.HIGH)
    field.__set__(obj, _Rank.NEG)
    assert calls == [_Rank.LOW, _Rank.HIGH, _Rank.NEG]
    calls.clear()
    with pytest.raises(ValidationErrors):
        field.__set__(obj, 1)
    with pytest.raises(TypeError):
        field.__set__(obj, _Other.NOPE)
    with pytest.raises(TypeError):
        field.__set__(obj, _Other.LOW)
    assert calls == []


@needs_native
def test_native_integer_enum_parity_with_host():
    native = _bind_enum_field(_Rank)
    host = _bind_enum_field(_Rank)
    _force_host(host)
    assert native._native_plan is not None
    assert host._native_plan is None
    samples = (
        _Rank.LOW,
        _Rank.HIGH,
        _Rank.ZERO,
        _Rank.NEG,
        _Rank.ALSO,
        _Other.NOPE,
        _Other.LOW,
        1,
        0,
        -3,
        True,
        False,
        "1",
        _Color.RED,
        object(),
        1.5,
        None,
    )
    members = (_Rank.LOW, _Rank.HIGH, _Rank.ZERO, _Rank.NEG, _Rank.ALSO)
    for value in samples:
        got = _enum_door(native, host, value)
        if any(value is member for member in members):
            assert got[0] == "ok", (value, got)
            assert got[3] is value
        elif value is None:
            assert got == ("ok", None, None, None)
        else:
            assert got[0] == "err", (value, got)
            assert got[1] in (TypeError, ValidationErrors)
            assert "Overflow" not in got[2]
            assert "int64" not in got[2].lower()
            assert "PyO3" not in got[2]
            assert "NotMember" not in got[2]
    out = _assign(native, _Other.NOPE)
    assert out[1] is TypeError
    assert out[2] == "n expect <enum '_Rank'> type, got _Other type instead"
    collide = _assign(native, _Other.LOW)
    assert collide[1] is TypeError
    assert collide[2] == "n expect <enum '_Rank'> type, got _Other type instead"
    plain = _assign(native, 1)
    assert plain[1] is ValidationErrors
    assert "n expect <enum '_Rank'> type, got int type instead" in plain[2]
    assert "n expect <enum 'IntEnum'> type, got int type instead" in plain[2]


@needs_native
def test_native_integer_enum_uses_apply_integer_enum_not_integer_apply():
    import ux_valio_native as peer

    field = _bind_enum_field(_Rank)
    assert field._native_ffi is peer.apply_integer_enum
    assert field._native_ffi is not peer.apply_integer
    integer = IntegerValidator(min_value=0, debug=True, name="n")
    assert integer._native_ffi is peer.apply_integer
    assert hasattr(peer.FailKind, "NotMember")
    assert not hasattr(peer.FailKind, "NotMem")
    plan = peer.compile_integer_enum(members=[1, 2, 0, -3])
    assert peer.apply_integer_enum(plan, 1) is None
    assert peer.apply_integer_enum(plan, 0) is None
    assert peer.apply_integer_enum(plan, -3) is None
    assert peer.apply_integer_enum(plan, 9) is peer.FailKind.NotMember
    assert peer.apply_integer_enum(plan, _Rank.LOW) is None
    empty = peer.compile_integer_enum(members=[])
    assert peer.apply_integer_enum(empty, 0) is peer.FailKind.NotMember
    assert peer.apply_integer_enum(empty, 1) is peer.FailKind.NotMember


@needs_native
def test_integer_enum_not_member_failkind_uses_type_door_wording():
    import ux_valio_native as peer

    field = _bind_enum_field(_Rank)

    def always_miss(plan, value):
        return peer.FailKind.NotMember

    field._native_ffi = always_miss
    got = _assign(field, _Rank.LOW)
    assert got[1] is TypeError
    assert got[2] == "n expect <enum '_Rank'> type, got _Rank type instead"


@needs_native
def test_integer_enum_unclosed_and_other_facades_stay_on_host():
    bounded = _bind_enum_field(_Rank, min_value=0)
    assert bounded._native_plan is None
    required = _bind_enum_field(_Rank, required=True)
    assert required._native_plan is None
    watched = _bind_enum_field(_Rank, reassign=False)
    assert watched._native_plan is None
    choice = _bind_enum_field(_Rank, in_choice=(_Rank.LOW, _Rank.HIGH))
    assert choice._native_plan is None
    bare = _bind_enum_field(enum.IntEnum)
    assert bare._native_plan is None
    assert bare.annotation is enum.IntEnum
    plain_enum = _bind_enum_field(_Rank, cls=EnumValidator)
    assert plain_enum._native_plan is None
    assert plain_enum.annotation is _Rank
    string_on_int = _bind_enum_field(_Rank, cls=StringEnumValidator)
    assert string_on_int._native_plan is None
    assert string_on_int.annotation is _Rank
    import ux_valio_native as peer

    boolean = BooleanValidator(debug=True, name="n")
    assert boolean._native_plan is not None
    assert boolean._native_ffi is peer.apply_boolean
    assert boolean._native_ffi is not peer.apply_integer_enum
    open_validator = Validator[_Rank](debug=True, name="n")

    class OpenOwner:
        pass

    OpenOwner.__annotations__ = {"n": _Rank}
    open_validator.__set_name__(OpenOwner, "n")
    assert open_validator.annotation is _Rank
    assert open_validator._native_plan is None
    huge = _bind_enum_field(_HugeRank)
    assert huge._native_plan is None
    over = _bind_enum_field(_OverRank)
    assert over._native_plan is None
    edge = _bind_enum_field(_EdgeRank)
    assert edge._native_plan is not None

    class OptionalOwner:
        pass

    OptionalOwner.__annotations__ = {"n": _Rank | None}
    optional = IntegerEnumValidator(debug=True, name="n")
    optional.__set_name__(OptionalOwner, "n")
    assert optional._native_plan is None


@needs_native
def test_integer_enum_huge_member_stays_on_host_and_matches():
    native = _bind_enum_field(_HugeRank)
    host = _force_host(_bind_enum_field(_HugeRank))
    assert native._native_plan is None
    assert _enum_door(native, host, _HugeRank.BIG)[3] is _HugeRank.BIG
    assert _enum_door(native, host, _HugeRank.SMALL)[3] is _HugeRank.SMALL
    assert _enum_door(native, host, 1)[0] == "err"


@needs_native
def test_integer_enum_i64_edges_match_host():
    native = _bind_enum_field(_EdgeRank)
    host = _force_host(_bind_enum_field(_EdgeRank))
    assert native._native_plan is not None
    assert _enum_door(native, host, _EdgeRank.MAX)[3] is _EdgeRank.MAX
    assert _enum_door(native, host, _EdgeRank.MIN)[3] is _EdgeRank.MIN
    over = _bind_enum_field(_OverRank)
    host_over = _force_host(_bind_enum_field(_OverRank))
    assert over._native_plan is None
    assert _enum_door(over, host_over, _OverRank.OVER)[3] is _OverRank.OVER


@needs_native
def test_integer_enum_none_skips_and_debug_false_swallows():
    @dataclass
    class Grade:
        r: _Rank = IntegerEnumValidator(debug=True)

    assert Grade(r=None).r is None  # type: ignore[arg-type]
    field = _bind_enum_field(_Rank)
    field.debug = False
    assert field._native_plan is not None

    class Quiet:
        pass

    obj = Quiet()
    field.__set__(obj, 1)
    assert not hasattr(obj, "n") or obj.__dict__.get("n") is None
    assert field.errors
    assert any("expect <enum '_Rank'> type" in str(err) for err in field.errors)


@needs_native
def test_native_integer_enum_collect_all_matches_host():
    native = _bind_enum_field(_Rank)
    host = _force_host(_bind_enum_field(_Rank))
    for value in (1, "x", True, _Color.RED, _Other.NOPE):
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
        if isinstance(native_err, ValidationErrors):
            assert [str(item) for item in native_err.errors] == [
                str(item) for item in host_err.errors
            ]


@needs_native
def test_native_integer_enum_collect_all_false_matches_host():
    native = _bind_enum_field(_Rank, collect_all=False)
    host = _force_host(_bind_enum_field(_Rank, collect_all=False))
    assert native._native_plan is not None
    got = _enum_door(native, host, 1)
    assert got[1] is TypeError
    assert got[2] == "n expect <enum '_Rank'> type, got int type instead"
    other = _enum_door(native, host, _Other.LOW)
    assert other[1] is TypeError
    assert "got _Other type instead" in other[2]


@needs_native
def test_native_integer_enum_pre_validate_and_custom_still_run():
    @dataclass
    class Grade:
        r: _Rank = IntegerEnumValidator(debug=True)

        @r.pre_validate
        def lift(self, value):
            if value == 1:
                return _Rank.LOW
            return value

        @r.validator
        def not_high(self, value):
            if value is _Rank.HIGH:
                raise ValueError("high")

    assert Grade.__dict__["r"]._native_plan is not None
    assert Grade(r=1).r is _Rank.LOW  # type: ignore[arg-type]
    assert Grade(r=_Rank.ZERO).r is _Rank.ZERO
    with pytest.raises(ValueError, match="high"):
        Grade(r=_Rank.HIGH)


@needs_native
def test_integer_enum_extract_overflow_falls_through_to_host():
    native = _bind_enum_field(_Rank)
    host = _force_host(_bind_enum_field(_Rank))
    assert native._native_plan is not None

    def boom(plan, value):
        raise OverflowError("i64 extract")

    native._native_ffi = boom
    assert _enum_door(native, host, _Rank.LOW)[3] is _Rank.LOW
    miss = _enum_door(native, host, 1)
    assert miss[1] is ValidationErrors
    assert "Overflow" not in miss[2]
    assert "PyO3" not in miss[2]


@needs_native
def test_unexpected_integer_enum_peer_bind_raises_runtime_error(monkeypatch):
    import ux_valio_native

    def boom(**kwargs):
        raise ValueError("peer exploded")

    monkeypatch.setattr(ux_valio_native, "compile_integer_enum", boom)
    with pytest.raises(RuntimeError, match="ux_valio_native") as caught:
        _bind_enum_field(_Rank)
    assert isinstance(caught.value.__cause__, ValueError)
    assert "Overflow" not in str(caught.value)
    assert "expect" not in str(caught.value)


@needs_native
def test_unexpected_integer_enum_peer_apply_raises_runtime_error():
    field = _bind_enum_field(_Rank)
    assert field._native_plan is not None

    def boom(plan, value):
        raise ValueError("peer exploded")

    field._native_ffi = boom
    with pytest.raises(RuntimeError, match="ux_valio_native") as caught:
        field.validate(None, _Rank.LOW)
    assert isinstance(caught.value.__cause__, ValueError)


@needs_native
def test_bare_int_enum_annotation_accepts_any_int_enum_on_host():
    native = _bind_enum_field(enum.IntEnum)
    host = _force_host(_bind_enum_field(enum.IntEnum))
    assert native._native_plan is None
    assert _enum_door(native, host, _Rank.LOW)[3] is _Rank.LOW
    assert _enum_door(native, host, _Other.NOPE)[3] is _Other.NOPE
    assert _enum_door(native, host, 1)[0] == "err"
