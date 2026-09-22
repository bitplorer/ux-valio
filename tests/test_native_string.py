# SPDX-License-Identifier: MIT
"""Native peer: String length plans (``Plan::String`` / ``LengthUnit``).

No ``from __future__ import annotations`` — postponed ``int`` TypeErrors at bind (KEEP).
"""

from dataclasses import dataclass

import pytest

from tests.native_support import (
    _assign,
    _assign_eq,
    _force_host,
    _peer_rust,
    host_native_source,
    needs_native,
)
from ux_valio import (
    BytesValidator,
    FloatValidator,
    IntegerValidator,
    StringValidator,
    ValidationErrors,
    Validator,
)

def test_closed_string_type_door_is_str_extract():
    """String type is UTF-8 extract. Length is codepoints (chars), not bytes."""
    rust = _peer_rust()
    native_py = host_native_source()
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
    assert integer._native_apply is peer.apply_integer
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
