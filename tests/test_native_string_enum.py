# SPDX-License-Identifier: MIT
"""Native peer: StringEnum UTF-8 member-set plans (``Plan::StringEnum``).

No ``from __future__ import annotations`` — postponed ``int`` TypeErrors at bind (KEEP).
"""

import enum
import re
from dataclasses import dataclass

import pytest

from tests.native_support import (
    ROOT,
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
    StringEnumValidator,
    StringValidator,
    ValidationErrors,
    Validator,
)

class _Rank(enum.IntEnum):
    LOW = 1
    HIGH = 2
    ZERO = 0
    NEG = -3
    ALSO = 1


class _Color(enum.Enum):
    RED = "red"


class _Tint(enum.Enum):
    PALE = "pale"
    DEEP = "deep"
    EMPTY = ""
    CAFE = "café"
    FLAG = "🇯🇵"
    ALSO = "pale"


class _OtherTint(enum.Enum):
    PALE = "pale"
    NOPE = "nope"


class _NfdTint(enum.Enum):
    CAFE = "cafe\u0301"


class _MixedTint(enum.Enum):
    OK = "ok"
    NUM = 1


class _BytesTint(enum.Enum):
    RAW = b"pale"


class _Mark(str):
    pass


class _SubTint(enum.Enum):
    A = _Mark("a")


class _LoneTint(enum.Enum):
    BAD = "\ud800"
    OK = "ok"


class _StrRank(enum.StrEnum):
    LOW = "low"
    HIGH = "high"


def test_string_enum_works_on_stdlib_path():
    @dataclass
    class Shade:
        c: _Tint = StringEnumValidator(debug=True)

    assert Shade(c=_Tint.PALE).c is _Tint.PALE
    assert Shade(c=_Tint.EMPTY).c is _Tint.EMPTY
    assert Shade(c=_Tint.ALSO).c is _Tint.PALE
    assert Shade(c=_Tint.CAFE).c is _Tint.CAFE
    with pytest.raises(TypeError, match="expect <enum '_Tint'> type, got _OtherTint type instead"):
        Shade(c=_OtherTint.NOPE)
    with pytest.raises(ValidationErrors, match="expect <enum '_Tint'> type"):
        Shade(c="pale")


def test_string_enum_l1_has_no_members_kwarg():
    with pytest.raises(TypeError):
        StringEnumValidator(members=("pale", "deep"))


def test_closed_string_enum_type_door_is_str_extract():
    """StringEnum type is UTF-8 extract. Compile and apply stay a pair."""
    rust = _peer_rust()
    native_py = host_native_source()
    assert "fn compile_string_enum" in rust
    assert "fn apply_string_enum" in rust
    assert "Plan::StringEnum" in rust
    assert "fn compile_and_apply" not in rust
    assert "_closed_string_enum_members" in native_py
    assert "apply_native_string_enum" in native_py
    assert "_raise_host_string_enum_type_miss" in native_py
    assert "_apply_host_string_enum_after_str_extract" in native_py
    assert "kinds.NotMember" in native_py
    assert not re.search(r"if fail == kinds\.", native_py)
    assert "members=" not in (ROOT / "ux_valio" / "facades" / "typed.py").read_text()


@needs_native
def test_string_enum_compiles_once_at_bind():
    field = StringEnumValidator(debug=True)

    @dataclass
    class Box:
        n: _Tint = field

    plan = field._native_plan
    apply = field._native_apply
    assert plan is not None
    assert apply is not None
    assert field.annotation is _Tint
    box = Box(n=_Tint.PALE)
    box.n = _Tint.DEEP
    box.n = _Tint.EMPTY
    assert box.n is _Tint.EMPTY
    assert field._native_plan is plan
    assert field._native_apply is apply


@needs_native
def test_one_ffi_apply_string_enum_per_set():
    field = _bind_enum_field(_Tint, cls=StringEnumValidator)
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
    field.__set__(obj, _Tint.PALE)
    field.__set__(obj, _Tint.DEEP)
    field.__set__(obj, _Tint.FLAG)
    assert calls == ["pale", "deep", "🇯🇵"]
    calls.clear()
    with pytest.raises(ValidationErrors):
        field.__set__(obj, "pale")
    with pytest.raises(TypeError):
        field.__set__(obj, _OtherTint.NOPE)
    with pytest.raises(TypeError):
        field.__set__(obj, _OtherTint.PALE)
    assert calls == []


@needs_native
def test_native_string_enum_parity_with_host():
    native = _bind_enum_field(_Tint, cls=StringEnumValidator)
    host = _bind_enum_field(_Tint, cls=StringEnumValidator)
    _force_host(host)
    assert native._native_plan is not None
    assert host._native_plan is None
    samples = (
        _Tint.PALE,
        _Tint.DEEP,
        _Tint.EMPTY,
        _Tint.CAFE,
        _Tint.FLAG,
        _Tint.ALSO,
        _OtherTint.PALE,
        _OtherTint.NOPE,
        _NfdTint.CAFE,
        _Rank.LOW,
        _Color.RED,
        "pale",
        "",
        "café",
        "cafe\u0301",
        "PALE",
        b"pale",
        1,
        0,
        True,
        False,
        1.5,
        object(),
        None,
    )
    members = (
        _Tint.PALE,
        _Tint.DEEP,
        _Tint.EMPTY,
        _Tint.CAFE,
        _Tint.FLAG,
        _Tint.ALSO,
    )
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
            assert "PyO3" not in got[2]
            assert "NotMember" not in got[2]
            assert "utf-8" not in got[2].lower()
    collide = _assign(native, _OtherTint.PALE)
    assert collide[1] is TypeError
    assert collide[2] == "n expect <enum '_Tint'> type, got _OtherTint type instead"
    plain = _assign(native, "pale")
    assert plain[1] is ValidationErrors
    assert "n expect <enum '_Tint'> type, got str type instead" in plain[2]
    assert "n expect a str Enum member, got str type instead" in plain[2]


@needs_native
def test_native_string_enum_uses_apply_string_enum_not_string_apply():
    import ux_valio_native as peer

    field = _bind_enum_field(_Tint, cls=StringEnumValidator)
    assert field._native_apply is peer.apply_string_enum
    assert field._native_apply is not peer.apply_string
    assert field._native_apply is not peer.apply_integer_enum
    text = StringValidator(min_length=1, debug=True, name="n")
    assert text._native_apply is peer.apply_string
    integer_enum = _bind_enum_field(_Rank)
    assert integer_enum._native_apply is peer.apply_integer_enum
    assert hasattr(peer.FailKind, "NotMember")
    plan = peer.compile_string_enum(members=["pale", "deep", "", "café", "cafe\u0301"])
    assert peer.apply_string_enum(plan, "pale") is None
    assert peer.apply_string_enum(plan, "") is None
    assert peer.apply_string_enum(plan, "café") is None
    assert peer.apply_string_enum(plan, "cafe\u0301") is None
    assert peer.apply_string_enum(plan, "cafe") is peer.FailKind.NotMember
    assert peer.apply_string_enum(plan, "PALE") is peer.FailKind.NotMember
    assert peer.apply_string_enum(plan, "pale ") is peer.FailKind.NotMember
    assert peer.apply_string_enum(plan, _Tint.PALE.value) is None
    empty = peer.compile_string_enum(members=[])
    assert peer.apply_string_enum(empty, "pale") is peer.FailKind.NotMember


@needs_native
def test_string_enum_not_member_failkind_uses_type_door_wording():
    import ux_valio_native as peer

    field = _bind_enum_field(_Tint, cls=StringEnumValidator)

    def always_miss(plan, value):
        return peer.FailKind.NotMember

    field._native_apply = always_miss
    got = _assign(field, _Tint.PALE)
    assert got[1] is TypeError
    assert got[2] == "n expect <enum '_Tint'> type, got _Tint type instead"


@needs_native
def test_string_enum_unclosed_and_other_facades_stay_on_host():
    bounded = _bind_enum_field(_Tint, cls=StringEnumValidator, min_length=1)
    assert bounded._native_plan is None
    required = _bind_enum_field(_Tint, cls=StringEnumValidator, required=True)
    assert required._native_plan is None
    watched = _bind_enum_field(_Tint, cls=StringEnumValidator, reassign=False)
    assert watched._native_plan is None
    choice = _bind_enum_field(_Tint, cls=StringEnumValidator, in_choice=(_Tint.PALE,))
    assert choice._native_plan is None
    bare = _bind_enum_field(enum.Enum, cls=StringEnumValidator)
    assert bare._native_plan is None
    assert bare.annotation is enum.Enum
    bare_str = _bind_enum_field(enum.StrEnum, cls=StringEnumValidator)
    assert bare_str._native_plan is None
    plain_enum = _bind_enum_field(_Tint, cls=EnumValidator)
    assert plain_enum._native_plan is None
    assert plain_enum.annotation is _Tint
    int_enum_on_str = _bind_enum_field(_Tint, cls=IntegerEnumValidator)
    assert int_enum_on_str._native_plan is None
    mixed = _bind_enum_field(_MixedTint, cls=StringEnumValidator)
    assert mixed._native_plan is None
    blob = _bind_enum_field(_BytesTint, cls=StringEnumValidator)
    assert blob._native_plan is None
    subclass = _bind_enum_field(_SubTint, cls=StringEnumValidator)
    assert subclass._native_plan is None
    lone = _bind_enum_field(_LoneTint, cls=StringEnumValidator)
    assert lone._native_plan is None
    import ux_valio_native as peer

    boolean = BooleanValidator(debug=True, name="n")
    assert boolean._native_plan is not None
    assert boolean._native_apply is peer.apply_boolean
    assert boolean._native_apply is not peer.apply_string_enum
    open_validator = Validator[_Tint](debug=True, name="n")

    class OpenOwner:
        pass

    OpenOwner.__annotations__ = {"n": _Tint}
    open_validator.__set_name__(OpenOwner, "n")
    assert open_validator.annotation is _Tint
    assert open_validator._native_plan is None

    class OptionalOwner:
        pass

    OptionalOwner.__annotations__ = {"n": _Tint | None}
    optional = StringEnumValidator(debug=True, name="n")
    optional.__set_name__(OptionalOwner, "n")
    assert optional._native_plan is None


@needs_native
def test_string_enum_non_utf8_and_mixed_stay_on_host_and_match():
    native = _bind_enum_field(_LoneTint, cls=StringEnumValidator)
    host = _force_host(_bind_enum_field(_LoneTint, cls=StringEnumValidator))
    assert native._native_plan is None
    assert _enum_door(native, host, _LoneTint.BAD)[3] is _LoneTint.BAD
    assert _enum_door(native, host, _LoneTint.OK)[3] is _LoneTint.OK
    assert _enum_door(native, host, "ok")[0] == "err"
    mixed = _bind_enum_field(_MixedTint, cls=StringEnumValidator)
    host_mixed = _force_host(_bind_enum_field(_MixedTint, cls=StringEnumValidator))
    assert mixed._native_plan is None
    assert _enum_door(mixed, host_mixed, _MixedTint.OK)[3] is _MixedTint.OK
    # Int-valued member fails the str-Enum extra on the host path.
    assert _enum_door(mixed, host_mixed, _MixedTint.NUM)[0] == "err"


@needs_native
def test_string_enum_strenum_compiles_and_matches_host():
    native = _bind_enum_field(_StrRank, cls=StringEnumValidator)
    host = _force_host(_bind_enum_field(_StrRank, cls=StringEnumValidator))
    assert native._native_plan is not None
    assert _enum_door(native, host, _StrRank.LOW)[3] is _StrRank.LOW
    assert _enum_door(native, host, _StrRank.HIGH)[3] is _StrRank.HIGH
    assert _enum_door(native, host, "low")[0] == "err"
    assert _enum_door(native, host, _Tint.PALE)[0] == "err"


@needs_native
def test_string_enum_none_skips_and_debug_false_swallows():
    @dataclass
    class Shade:
        c: _Tint = StringEnumValidator(debug=True)

    assert Shade(c=None).c is None  # type: ignore[arg-type]
    field = _bind_enum_field(_Tint, cls=StringEnumValidator)
    field.debug = False
    assert field._native_plan is not None

    class Quiet:
        pass

    obj = Quiet()
    field.__set__(obj, "pale")
    assert not hasattr(obj, "n") or obj.__dict__.get("n") is None
    assert field.errors
    assert any("expect <enum '_Tint'> type" in str(err) for err in field.errors)


@needs_native
def test_native_string_enum_collect_all_matches_host():
    native = _bind_enum_field(_Tint, cls=StringEnumValidator)
    host = _force_host(_bind_enum_field(_Tint, cls=StringEnumValidator))
    for value in ("pale", b"pale", True, _Color.RED, _OtherTint.NOPE, _Rank.LOW, ""):
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
def test_native_string_enum_collect_all_false_matches_host():
    native = _bind_enum_field(_Tint, cls=StringEnumValidator, collect_all=False)
    host = _force_host(_bind_enum_field(_Tint, cls=StringEnumValidator, collect_all=False))
    assert native._native_plan is not None
    got = _enum_door(native, host, "pale")
    assert got[1] is TypeError
    assert got[2] == "n expect <enum '_Tint'> type, got str type instead"
    other = _enum_door(native, host, _OtherTint.PALE)
    assert other[1] is TypeError
    assert "got _OtherTint type instead" in other[2]


@needs_native
def test_native_string_enum_pre_validate_and_custom_still_run():
    @dataclass
    class Shade:
        c: _Tint = StringEnumValidator(debug=True)

        @c.pre_validate
        def lift(self, value):
            if value == "pale":
                return _Tint.PALE
            return value

        @c.validator
        def not_deep(self, value):
            if value is _Tint.DEEP:
                raise ValueError("deep")

    assert Shade.__dict__["c"]._native_plan is not None
    assert Shade(c="pale").c is _Tint.PALE  # type: ignore[arg-type]
    assert Shade(c=_Tint.EMPTY).c is _Tint.EMPTY
    with pytest.raises(ValueError, match="deep"):
        Shade(c=_Tint.DEEP)


@needs_native
def test_string_enum_extract_unicode_error_falls_through_to_host():
    native = _bind_enum_field(_Tint, cls=StringEnumValidator)
    host = _force_host(_bind_enum_field(_Tint, cls=StringEnumValidator))
    assert native._native_plan is not None

    def boom(plan, value):
        raise UnicodeEncodeError("utf-8", "\ud800", 0, 1, "surrogates not allowed")

    native._native_apply = boom
    assert _enum_door(native, host, _Tint.PALE)[3] is _Tint.PALE
    miss = _enum_door(native, host, "pale")
    assert miss[1] is ValidationErrors
    assert "Overflow" not in miss[2]
    assert "PyO3" not in miss[2]
    assert "utf-8" not in miss[2].lower()


@needs_native
def test_unexpected_string_enum_peer_bind_raises_runtime_error(monkeypatch):
    import ux_valio_native

    def boom(**kwargs):
        raise ValueError("peer exploded")

    monkeypatch.setattr(ux_valio_native, "compile_string_enum", boom)
    with pytest.raises(RuntimeError, match="ux_valio_native") as caught:
        _bind_enum_field(_Tint, cls=StringEnumValidator)
    assert isinstance(caught.value.__cause__, ValueError)
    assert "Overflow" not in str(caught.value)
    assert "expect" not in str(caught.value)


@needs_native
def test_unexpected_string_enum_peer_apply_raises_runtime_error():
    field = _bind_enum_field(_Tint, cls=StringEnumValidator)
    assert field._native_plan is not None

    def boom(plan, value):
        raise ValueError("peer exploded")

    field._native_apply = boom
    with pytest.raises(RuntimeError, match="ux_valio_native") as caught:
        field.validate(None, _Tint.PALE)
    assert isinstance(caught.value.__cause__, ValueError)
