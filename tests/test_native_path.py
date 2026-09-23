# SPDX-License-Identifier: MIT
"""Native module: Path type door (``Plan::Path``, ``pathlib.Path``).

No ``from __future__ import annotations`` — postponed ``int`` TypeErrors at bind (KEEP).
"""

import pathlib
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
    EnumValidator,
    PathValidator,
    UUIDValidator,
    ValidationErrors,
    Validator,
)

_SAMPLE = pathlib.Path("/tmp/ux-valio-path")
_REL = pathlib.Path("folder/file")
_EMPTY = pathlib.Path("")
_DOT = pathlib.Path(".")


class _ChildPath(pathlib.Path):
    """Subclass still a ``pathlib.Path``. Same door as host ``isinstance``."""


def test_path_works_on_stdlib_path(tmp_path):
    existing = tmp_path / "here"
    existing.mkdir()

    @dataclass
    class Box:
        folder: pathlib.Path = PathValidator(debug=True)

    assert Box(folder=_SAMPLE).folder == _SAMPLE
    assert Box(folder=str(_SAMPLE)).folder == _SAMPLE
    assert Box(folder=_REL).folder == _REL
    assert Box(folder=str(_REL)).folder == _REL
    assert Box(folder=_EMPTY).folder == _EMPTY
    assert Box(folder="").folder == _EMPTY
    assert Box(folder=_DOT).folder == _DOT
    assert Box(folder=pathlib.PosixPath("/tmp/ux-valio-posix")).folder == pathlib.Path(
        "/tmp/ux-valio-posix"
    )
    child = _ChildPath("/tmp/ux-valio-child")
    assert Box(folder=child).folder == child
    assert Box(folder=None).folder is None  # type: ignore[arg-type]
    with pytest.raises((TypeError, ValidationErrors), match="expect"):
        Box(folder=1)  # type: ignore[arg-type]
    with pytest.raises((TypeError, ValidationErrors), match="expect"):
        Box(folder=pathlib.PurePath("/tmp/pure"))  # type: ignore[arg-type]
    with pytest.raises((TypeError, ValidationErrors), match="expect"):
        Box(folder=b"/tmp/bytes")  # type: ignore[arg-type]

    @dataclass
    class MustExist:
        folder: pathlib.Path = PathValidator(path_exists=True, debug=True)

    assert MustExist(folder=existing).folder == existing
    assert MustExist(folder=str(existing)).folder == existing
    with pytest.raises(FileNotFoundError, match="existing path"):
        MustExist(folder=tmp_path / "missing")


def test_closed_path_type_door_is_path_extract():
    """Path type is pathlib.Path extract. Compile and apply stay a pair."""
    rust = _native_rust()
    native_py = host_native_source()
    assert "fn compile_path" in rust
    assert "fn apply_path" in rust
    assert "Plan::Path" in rust
    assert "fn compile_and_apply" not in rust
    assert not re.search(r"\bfn compile\(", rust)
    assert not re.search(r"\bfn apply\(", rust)
    assert "fn compile_enum" not in rust
    assert "fn compile_pattern" not in rust
    assert "_closed_path" in native_py
    assert "_select_path" in native_py
    assert "apply_native_path" in native_py
    assert "_raise_host_path_type_miss" in native_py
    assert "_bridge_to_type" in native_py
    assert "_is_path_type_annotation" in native_py


@needs_native
def test_path_compiles_once_at_bind():
    import ux_valio_native as native

    field = PathValidator(debug=True)

    @dataclass
    class Box:
        folder: pathlib.Path = field

    plan = field._native_plan
    assert plan is not None
    assert field._native_apply is native.apply_path
    assert field._native_apply is not native.apply_uuid
    assert field._native_apply is not native.apply_string
    assert field._native_run is not field._native_apply
    assert field.annotation == pathlib.Path | str
    box = Box(folder=_SAMPLE)
    box.folder = _REL
    assert box.folder == _REL
    assert field._native_plan is plan
    assert field._native_apply is native.apply_path


@needs_native
def test_one_ffi_apply_path_per_set(tmp_path):
    field = PathValidator(debug=True, name="n")
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
    field.__set__(obj, str(_REL))
    assert calls == [_SAMPLE, _REL]
    assert obj.n == _REL
    calls.clear()
    with pytest.raises((TypeError, ValidationErrors)):
        field.__set__(obj, 1)
    assert calls == []
    calls.clear()
    with pytest.raises((TypeError, ValidationErrors)):
        field.__set__(obj, pathlib.PurePath("/tmp/pure"))
    assert calls == []
    calls.clear()
    must = PathValidator(path_exists=True, debug=True, name="n")
    assert must._native_plan is not None
    must._native_apply = counted
    existing = tmp_path / "here"
    existing.mkdir()
    must.__set__(obj, str(existing))
    assert calls == [existing]
    calls.clear()
    with pytest.raises(FileNotFoundError):
        must.__set__(obj, tmp_path / "missing")
    assert calls == [tmp_path / "missing"]


@needs_native
def test_native_path_parity_with_host(tmp_path):
    native = PathValidator(debug=True, name="n")
    host = _force_host(PathValidator(debug=True, name="n"))
    assert native._native_plan is not None
    assert host._native_plan is None
    existing = tmp_path / "here"
    existing.mkdir()
    child = _ChildPath(str(existing))
    samples = (
        _SAMPLE,
        _REL,
        _EMPTY,
        _DOT,
        pathlib.PosixPath("/tmp/ux-valio-posix"),
        child,
        str(_SAMPLE),
        str(_REL),
        "",
        ".",
        pathlib.PurePath("/tmp/pure"),
        pathlib.PurePosixPath("pure-posix"),
        1,
        True,
        False,
        None,
        b"/tmp/bytes",
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

    native_exists = PathValidator(path_exists=True, debug=True, name="n")
    host_exists = _force_host(PathValidator(path_exists=True, debug=True, name="n"))
    assert native_exists._native_plan is not None
    for value in (existing, str(existing), tmp_path / "missing", str(tmp_path / "missing"), 1):
        got = _assign(native_exists, value)
        host_got = _assign(host_exists, value)
        assert got[:3] == host_got[:3], (value, got, host_got)
        if got[0] == "ok":
            assert got[3] == host_got[3]


@needs_native
def test_native_path_uses_apply_path_not_string_apply():
    import ux_valio_native as native

    field = PathValidator(debug=True, name="n")
    assert field._native_apply is native.apply_path
    assert field._native_apply is not native.apply_string
    assert field._native_apply is not native.apply_uuid
    plan = native.compile_path()
    assert native.apply_path(plan, _SAMPLE) is None
    assert native.apply_path(plan, _EMPTY) is None
    assert native.apply_path(plan, pathlib.PosixPath("/tmp/ux")) is None
    assert native.apply_path(plan, _ChildPath("/tmp/child")) is None
    with pytest.raises(TypeError):
        native.apply_path(plan, str(_SAMPLE))
    with pytest.raises(TypeError):
        native.apply_path(plan, pathlib.PurePath("/tmp/pure"))
    with pytest.raises(TypeError):
        native.apply_path(plan, 1)
    with pytest.raises(TypeError):
        native.apply_path(plan, True)
    with pytest.raises(TypeError):
        native.apply_path(plan, b"/tmp")
    with pytest.raises(RuntimeError, match="apply_uuid plan family mismatch"):
        native.apply_uuid(plan, uuid.UUID(int=0))
    with pytest.raises(RuntimeError, match="apply_path plan family mismatch"):
        native.apply_path(native.compile_uuid(), _SAMPLE)
    with pytest.raises(RuntimeError, match="apply_ip plan family mismatch"):
        native.apply_ip(plan, "127.0.0.1")


@needs_native
def test_path_unclosed_stays_on_host():
    assert PathValidator(min_value=_SAMPLE, debug=True, name="n")._native_plan is None
    assert PathValidator(required=True, debug=True, name="n")._native_plan is None
    assert PathValidator(reassign=False, debug=True, name="n")._native_plan is None
    assert PathValidator(in_choice=(_SAMPLE,), debug=True, name="n")._native_plan is None
    assert PathValidator(min_length=1, debug=True, name="n")._native_plan is None
    assert EnumValidator(debug=True, name="n")._native_plan is None
    open_union = Validator[pathlib.Path | int](debug=True, name="n")
    assert open_union._native_plan is None
    optional = Validator[pathlib.Path | None](debug=True, name="n")
    assert optional._native_plan is None
    pure = Validator[pathlib.PurePath](debug=True, name="n")
    assert pure._native_plan is None
    assert UUIDValidator(debug=True, name="n")._native_apply.__name__ == "apply_uuid"


@needs_native
def test_validator_path_subscript_compiles_at_set_name():
    import ux_valio_native as native

    field = Validator[pathlib.Path](debug=True, name="n")

    class Owner:
        pass

    Owner.__annotations__ = {"n": pathlib.Path}
    field.__set_name__(Owner, "n")
    assert field.annotation is pathlib.Path
    assert field._native_plan is not None
    assert field._native_apply is native.apply_path
    assert _assign(field, _SAMPLE)[3] == _SAMPLE
    assert _assign(field, _EMPTY)[3] == _EMPTY
    assert _assign(field, str(_SAMPLE))[1] is TypeError
    assert _assign(field, pathlib.PurePath("/tmp/pure"))[1] is TypeError
    assert _assign(field, 1)[1] is TypeError


@needs_native
def test_path_none_skips_and_debug_false_swallows():
    @dataclass
    class Box:
        folder: pathlib.Path = PathValidator(debug=True)

    assert Box(folder=None).folder is None  # type: ignore[arg-type]
    field = PathValidator(debug=True, name="n")
    field.debug = False
    assert field._native_plan is not None

    class Quiet:
        pass

    obj = Quiet()
    field.__set__(obj, 1)
    assert obj.__dict__.get("n") is None
    assert field.errors
    assert any("expect pathlib.Path | str type" in str(err) for err in field.errors)
    field.errors.clear()
    field.__set__(obj, _SAMPLE)
    assert obj.n == _SAMPLE


@needs_native
def test_native_path_collect_all_matches_host():
    native = PathValidator(debug=True, name="n")
    host = _force_host(PathValidator(debug=True, name="n"))
    samples = (
        _SAMPLE,
        str(_SAMPLE),
        pathlib.PurePath("/tmp/pure"),
        1,
        True,
        None,
        b"/tmp",
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
def test_native_path_pre_validate_and_custom_still_run(tmp_path):
    lifted = tmp_path / "lifted"

    @dataclass
    class Box:
        folder: pathlib.Path = PathValidator(debug=True)

        @folder.pre_validate
        def lift(self, value):
            if value == 1:
                return lifted
            return value

        @folder.validator
        def not_dot(self, value):
            if value == _DOT:
                raise ValueError("dot")

    assert Box.__dict__["folder"]._native_plan is not None
    assert Box(folder=1).folder == lifted  # type: ignore[arg-type]
    assert Box(folder=str(_REL)).folder == _REL
    with pytest.raises(ValueError, match="dot"):
        Box(folder=_DOT)


@needs_native
def test_path_extract_type_error_falls_through_to_host():
    native = PathValidator(debug=True, name="n")
    host = _force_host(PathValidator(debug=True, name="n"))
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
def test_unexpected_path_native_bind_raises_runtime_error(monkeypatch):
    import ux_valio_native

    def boom():
        raise ValueError("native exploded")

    monkeypatch.setattr(ux_valio_native, "compile_path", boom)
    with pytest.raises(RuntimeError, match="ux_valio_native") as caught:
        PathValidator(debug=True, name="n")
    assert isinstance(caught.value.__cause__, ValueError)
    assert "Overflow" not in str(caught.value)
    assert "expect" not in str(caught.value)


@needs_native
def test_unexpected_path_native_apply_raises_runtime_error():
    field = PathValidator(debug=True, name="n")
    assert field._native_plan is not None

    def boom(plan, value):
        raise ValueError("native exploded")

    field._native_apply = boom
    with pytest.raises(RuntimeError, match="ux_valio_native") as caught:
        field.validate(None, _SAMPLE)
    assert isinstance(caught.value.__cause__, ValueError)
