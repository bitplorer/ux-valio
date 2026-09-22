# SPDX-License-Identifier: MIT
"""Native module: Bytes length plans (``Plan::Bytes`` / ``LengthUnit``).

No ``from __future__ import annotations`` — postponed ``int`` TypeErrors at bind (KEEP).
"""

from dataclasses import dataclass

import pytest

from tests.native_support import (
    _assign,
    _assign_eq,
    _force_host,
    _native_rust,
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

def test_closed_bytes_type_door_is_bytes_extract():
    """Bytes type is ``&[u8]`` extract. Length is ``len()``, not codepoints."""
    rust = _native_rust()
    native_py = host_native_source()
    assert "fn compile_bytes" in rust
    assert "fn apply_bytes" in rust
    assert "value: &[u8]" in rust
    assert "let byte_len = value.len();" in rust
    assert "Plan::Bytes" in rust
    assert "grapheme" not in rust.lower()
    assert "_closed_bytes_length" in native_py
    assert "apply_native_bytes_length" in native_py
    assert "_bridge_to_length" in native_py
    assert 'raise ValueError("overflow' not in native_py
    assert "PyO3 bytes Overflow" not in native_py
    assert "public overflow" not in native_py


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
    apply = field._native_ffi
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
    assert field._native_ffi is apply


@needs_native
def test_one_ffi_apply_bytes_per_set():
    field = BytesValidator(min_length=1, debug=True, name="n")

    @dataclass
    class Box:
        n: bytes = field

    assert field._native_plan is not None
    calls: list[bytes] = []
    orig = field._native_ffi

    def counted(plan, value):
        calls.append(value)
        return orig(plan, value)

    field._native_ffi = counted
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
    apply = field._native_ffi
    assert plan is not None
    assert apply is not None
    passing = next(value for value, fragment in samples if fragment is None)
    field.validate(None, passing)
    assert field._native_plan is plan
    assert field._native_ffi is apply


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
    import ux_valio_native as native

    field = BytesValidator(min_length=1, debug=True, name="n")
    assert field._native_ffi is native.apply_bytes
    text = StringValidator(min_length=1, debug=True, name="n")
    assert text._native_ffi is native.apply_string
    integer = IntegerValidator(min_value=0, debug=True, name="n")
    assert integer._native_ffi is native.apply_integer
    floating = FloatValidator(min_value=0.0, debug=True, name="n")
    assert floating._native_ffi is native.apply_float


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

    native._native_ffi = boom
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

    native._native_ffi = boom
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
def test_unexpected_bytes_native_bind_raises_runtime_error(monkeypatch):
    import ux_valio_native

    def boom(**kwargs):
        raise ValueError("native exploded")

    monkeypatch.setattr(ux_valio_native, "compile_bytes", boom)
    with pytest.raises(RuntimeError, match="ux_valio_native") as caught:
        BytesValidator(min_length=1, debug=True, name="n")
    assert isinstance(caught.value.__cause__, ValueError)
    assert "Overflow" not in str(caught.value)
    assert "expect" not in str(caught.value)


@needs_native
def test_unexpected_bytes_native_apply_raises_runtime_error():
    field = BytesValidator(min_length=1, debug=True, name="n")
    assert field._native_plan is not None

    def boom(plan, value):
        raise ValueError("native exploded")

    field._native_ffi = boom
    with pytest.raises(RuntimeError, match="ux_valio_native") as caught:
        field.validate(None, b"a")
    assert isinstance(caught.value.__cause__, ValueError)
