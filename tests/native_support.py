# SPDX-License-Identifier: MIT
"""Shared helpers for native module tests. Not collected as tests."""

import math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _native_rust() -> str:
    """Private native-crate sources. Layout may span modules under ``native/src``."""
    native_src = ROOT / "native" / "src"
    return "\n".join(path.read_text() for path in sorted(native_src.rglob("*.rs")))


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

_VALIDATORS = ROOT / "ux_valio" / "validators"
HOST_NATIVE_PATHS = (_VALIDATORS / "_native.py",)


def host_native_source() -> str:
    """Host bind source. One file: ``_native.py``."""
    return "\n".join(path.read_text() for path in HOST_NATIVE_PATHS)


def _native_available() -> bool:
    try:
        import ux_valio_native  # noqa: F401
    except ImportError:
        return False
    return True


needs_native = pytest.mark.skipif(
    not _native_available(),
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


def _bind_enum_field(enum_type, cls=None, **kwargs):
    if cls is None:
        from ux_valio import IntegerEnumValidator

        cls = IntegerEnumValidator
    field = cls(debug=True, name="n", **kwargs)
    owner = type("Owner", (), {})
    owner.__annotations__ = {"n": enum_type}
    field.__set_name__(owner, "n")
    return field


def _enum_door(native, host, value):
    got_native = _assign(native, value)
    got_host = _assign(host, value)
    assert got_native[:3] == got_host[:3], (value, got_native, got_host)
    if got_native[0] == "ok":
        assert got_native[3] is got_host[3]
    return got_native


def _assign(field, value):
    class Box:
        pass

    obj = Box()
    try:
        field.__set__(obj, value)
    except Exception as err:
        return ("err", type(err), str(err), getattr(obj, "n", None))
    return ("ok", None, None, obj.__dict__.get("n"))
