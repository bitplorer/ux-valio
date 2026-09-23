# SPDX-License-Identifier: MIT
"""Native module: IP string identity (``Plan::Ip``, given ``str``).

No ``from __future__ import annotations`` — postponed ``int`` TypeErrors at bind (KEEP).
"""

import ipaddress
import re
from dataclasses import dataclass

import pytest

from tests.native_support import (
    _assign,
    _force_host,
    _native_rust,
    host_native_source,
    needs_native,
)
from ux_valio.validators._native import _IP_DOOR, _STRING_DOOR
from ux_valio import (
    AllOf,
    IPAddressValidator,
    IPv4Validator,
    IPv6Validator,
    MinLengthValidator,
    StringValidator,
    ValidationErrors,
)

_V4 = "127.0.0.1"
_V6 = "::1"
_MAPPED = "::ffff:192.0.2.1"
_SCOPE = "fe80::1%eth0"
_LONG_V6 = "0:0:0:0:0:0:0:1"

_STRINGS = (
    "",
    _V4,
    "0.0.0.0",
    "255.255.255.255",
    "127.0.0.01",
    "127.0.0.256",
    "127.0.0",
    "127.0.0.1.2",
    "127.0.0.1/32",
    " 127.0.0.1",
    "127.0.0.1 ",
    _V6,
    "::",
    "1::",
    _SCOPE,
    "fe80::1%",
    "fe80::1%a%b",
    "fe80::1%1",
    _MAPPED,
    "::ffff:192.0.2.256",
    "1:2:3:4:5:6:7:8",
    "1:2:3:4:5:6:7",
    "2001:db8::",
    "2001:DB8::1",
    "127.0.0.1%1",
    ":",
    ":::1",
    "1::2::3",
    _LONG_V6,
    "192.168.001.1",
    "1.2.3.4",
    "2001:db8:85a3::8a2e:370:7334",
    "not-an-ip",
    "localhost",
)


class _ChildStr(str):
    """Subclass still a ``str``. Same door as host ``isinstance``."""


def test_ip_works_on_stdlib_path():
    @dataclass
    class V4:
        ip: str = IPv4Validator(debug=True)

    assert V4(ip=_V4).ip == _V4
    assert V4(ip=None).ip is None  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="IPv4"):
        V4(ip="999.0.0.1")
    with pytest.raises(ValueError, match="IPv4"):
        V4(ip=_V6)

    @dataclass
    class V6:
        ip: str = IPv6Validator(debug=True)

    assert V6(ip=_V6).ip == _V6
    assert V6(ip=_SCOPE).ip == _SCOPE
    assert V6(ip=_LONG_V6).ip == _LONG_V6
    assert V6(ip=_MAPPED).ip == _MAPPED
    with pytest.raises(ValueError, match="IPv6"):
        V6(ip=_V4)

    @dataclass
    class AnyIP:
        ip: str = IPAddressValidator(debug=True)

    assert AnyIP(ip=_V4).ip == _V4
    assert AnyIP(ip=_V6).ip == _V6
    with pytest.raises(ValueError, match="IP address"):
        AnyIP(ip="not-an-ip")


def test_closed_ip_door_is_string_identity():
    """IP is a str extract plus the stdlib parser. Compile and apply stay a pair."""
    rust = _native_rust()
    native_py = host_native_source()
    assert "fn compile_ip" in rust
    assert "fn apply_ip" in rust
    assert "Plan::Ip" in rust
    assert "FailKind::NotIp" in rust or "NotIp" in rust
    assert "fn compile_and_apply" not in rust
    assert not re.search(r"\bfn compile\(", rust)
    assert not re.search(r"\bfn apply\(", rust)
    assert "_closed_ip" in native_py
    assert "_IP_DOOR" in native_py
    assert "def _select_ip(" not in native_py
    assert "def apply_native_ip(" not in native_py
    assert "type_miss=_raise_host_type_door_miss" in native_py
    assert "def _raise_host_ip_type_miss(" not in native_py
    assert "_bridge_to_ip" in native_py
    assert "_read_ip_facade" in native_py


@needs_native
def test_ip_compiles_once_at_bind():
    import ux_valio_native as native

    field = IPv4Validator(debug=True)

    @dataclass
    class Box:
        ip: str = field

    plan = field._native_plan
    assert plan is not None
    assert field._native_apply is native.apply_ip
    assert field._native_apply is not native.apply_string
    assert field._native_run is not field._native_apply
    assert field._native_run is not None
    assert field._native_run.__self__ is _IP_DOOR
    assert field._native_run.__func__.__name__ == "_run_closed"
    assert field._native_run == _IP_DOOR._run_closed
    assert field.annotation is str
    box = Box(ip=_V4)
    box.ip = "10.0.0.1"
    assert box.ip == "10.0.0.1"
    assert field._native_plan is plan
    assert field._native_apply is native.apply_ip
    assert IPv6Validator(debug=True, name="n")._native_apply is native.apply_ip
    assert IPAddressValidator(debug=True, name="n")._native_apply is native.apply_ip


@needs_native
def test_one_ffi_apply_ip_per_set():
    field = IPv4Validator(debug=True, name="n")
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
    field.__set__(obj, _V4)
    field.__set__(obj, "10.0.0.1")
    assert calls == [_V4, "10.0.0.1"]
    assert obj.n == "10.0.0.1"
    calls.clear()
    with pytest.raises((TypeError, ValidationErrors)):
        field.__set__(obj, 1)
    assert calls == []
    calls.clear()
    with pytest.raises(ValueError):
        field.__set__(obj, "999.0.0.1")
    assert calls == ["999.0.0.1"]


@needs_native
@pytest.mark.parametrize(
    "facade",
    [IPv4Validator, IPv6Validator, IPAddressValidator],
)
def test_native_ip_parity_with_host(facade):
    native = facade(debug=True, name="n")
    host = _force_host(facade(debug=True, name="n"))
    assert native._native_plan is not None
    assert host._native_plan is None
    samples = _STRINGS + (
        _ChildStr(_V4),
        _ChildStr(_V6),
        1,
        True,
        False,
        None,
        b"\x7f\x00\x00\x01",
        ipaddress.IPv4Address(_V4),
        ipaddress.IPv6Address(_V6),
        object(),
    )
    for value in samples:
        got = _assign(native, value)
        host_got = _assign(host, value)
        assert got[:3] == host_got[:3], (facade, value, got, host_got)
        if got[0] == "ok":
            assert got[3] == host_got[3]
            if isinstance(value, str):
                assert got[3] == value
        else:
            assert "Overflow" not in got[2]
            assert "PyO3" not in got[2]


@needs_native
def test_native_ip_uses_apply_ip_not_string_apply():
    import ux_valio_native as native

    v4 = IPv4Validator(debug=True, name="n")
    v6 = IPv6Validator(debug=True, name="n")
    either = IPAddressValidator(debug=True, name="n")
    assert v4._native_apply is native.apply_ip
    assert v4._native_apply is not native.apply_string
    plan_v4 = native.compile_ip("ipv4")
    plan_v6 = native.compile_ip(kind="ipv6")
    plan_ip = native.compile_ip("ip")
    assert native.apply_ip(plan_v4, _V4) is None
    assert native.apply_ip(plan_v4, "0.0.0.0") is None
    assert native.apply_ip(plan_v6, _V6) is None
    assert native.apply_ip(plan_v6, _SCOPE) is None
    assert native.apply_ip(plan_v6, _MAPPED) is None
    assert native.apply_ip(plan_v6, _LONG_V6) is None
    assert native.apply_ip(plan_ip, _V4) is None
    assert native.apply_ip(plan_ip, _V6) is None
    assert native.apply_ip(plan_v4, "999.0.0.1") is native.FailKind.NotIp
    assert native.apply_ip(plan_v4, _V6) is native.FailKind.NotIp
    assert native.apply_ip(plan_v6, _V4) is native.FailKind.NotIp
    assert native.apply_ip(plan_ip, "not-an-ip") is native.FailKind.NotIp
    with pytest.raises(TypeError):
        native.apply_ip(plan_v4, 1)
    with pytest.raises(TypeError):
        native.apply_ip(plan_v4, b"\x7f\x00\x00\x01")
    with pytest.raises(TypeError):
        native.apply_ip(plan_v4, True)
    with pytest.raises(ValueError, match="kind"):
        native.compile_ip("path")
    with pytest.raises(RuntimeError, match="apply_string plan family mismatch"):
        native.apply_string(plan_v4, _V4)
    with pytest.raises(RuntimeError, match="apply_ip plan family mismatch"):
        native.apply_ip(native.compile_uuid(), _V4)
    assert v6._native_plan is not None
    assert either._native_plan is not None


@needs_native
def test_ip_unclosed_stays_on_host():
    """Length on an IP facade is the string door. Other extras stay host."""
    length_bound = IPv4Validator(max_length=3, debug=True, name="n")
    assert length_bound._native_run.__self__ is _STRING_DOOR
    assert length_bound._native_run.__func__.__name__ == "_run_closed"
    assert IPv4Validator(min_length=1, debug=True, name="n")._native_run.__self__ is (
        _STRING_DOOR
    )
    assert IPv4Validator(required=True, debug=True, name="n")._native_plan is None
    assert IPv4Validator(reassign=False, debug=True, name="n")._native_plan is None
    assert IPv4Validator(in_choice=(_V4,), debug=True, name="n")._native_plan is None
    assert IPv4Validator(pattern=r"127", debug=True, name="n")._native_plan is None
    assert IPv6Validator(max_length=2, debug=True, name="n")._native_run.__self__ is (
        _STRING_DOOR
    )
    assert IPAddressValidator(length=4, debug=True, name="n")._native_run.__self__ is (
        _STRING_DOOR
    )
    assert StringValidator(debug=True, name="n")._native_plan is None
    length = StringValidator(min_length=1, debug=True, name="n")
    assert length._native_plan is not None
    assert length._native_apply.__name__ == "apply_string"


@needs_native
def test_ip_none_skips_and_debug_false_swallows():
    @dataclass
    class Box:
        ip: str = IPv4Validator(debug=True)

    assert Box(ip=None).ip is None  # type: ignore[arg-type]
    field = IPv4Validator(debug=True, name="n")
    field.debug = False
    assert field._native_plan is not None

    class Quiet:
        pass

    obj = Quiet()
    field.__set__(obj, 1)
    assert obj.__dict__.get("n") is None
    assert field.errors
    assert any("expect" in str(err) and "int" in str(err) for err in field.errors)
    field.errors.clear()
    field.__set__(obj, _V4)
    assert obj.n == _V4


@needs_native
def test_native_ip_collect_all_matches_host():
    native = IPv4Validator(debug=True, name="n")
    host = _force_host(IPv4Validator(debug=True, name="n"))
    samples = (
        _V4,
        "999.0.0.1",
        _V6,
        1,
        True,
        None,
        b"\x7f\x00\x00\x01",
        object(),
        ipaddress.IPv4Address(_V4),
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
        assert type(native_err) is type(host_err), (value, native_err, host_err)
        assert str(native_err) == str(host_err), (value, native_err, host_err)


@needs_native
def test_native_ip_pre_validate_and_custom_still_run():
    @dataclass
    class Box:
        ip: str = IPv4Validator(debug=True)

        @ip.pre_validate
        def lift(self, value):
            if value == 1:
                return _V4
            return value

        @ip.validator
        def not_loopback(self, value):
            if value == _V4:
                raise ValueError("loopback")

    assert Box.__dict__["ip"]._native_plan is not None
    with pytest.raises(ValueError, match="loopback"):
        Box(ip=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="loopback"):
        Box(ip=_V4)
    assert Box(ip="10.0.0.1").ip == "10.0.0.1"


@needs_native
def test_post_validate_cannot_smuggle_a_bad_ip():
    @dataclass
    class Box:
        ip: str = IPv4Validator(debug=True)

        @ip.post_validate
        def smash(self, value):
            return "999.0.0.1"

    with pytest.raises(ValueError, match="IPv4 address"):
        Box(ip=_V4)


@needs_native
def test_allof_store_identity_still_rejects_a_bad_ip():
    field = IPv4Validator(debug=True, name="ip") & MinLengthValidator(min_length=1)
    assert isinstance(field, AllOf)
    member = field.validators[0]
    assert member._native_plan is not None
    with pytest.raises(ValueError, match="IPv4 address"):
        field._reject_store_identity("nope")
    field._reject_store_identity(_V4)


@needs_native
def test_ip_extract_type_error_falls_through_to_host():
    native = IPv4Validator(debug=True, name="n")
    host = _force_host(IPv4Validator(debug=True, name="n"))
    assert native._native_plan is not None

    def boom(plan, value):
        raise TypeError("extract")

    native._native_apply = boom
    assert _assign(native, _V4)[3] == _V4
    assert _assign(host, _V4)[3] == _V4
    miss = _assign(native, 1)
    assert miss[1] is ValidationErrors or miss[1] is TypeError
    assert "extract" not in miss[2]
    assert "Overflow" not in miss[2]


@needs_native
def test_unexpected_ip_native_bind_raises_runtime_error(monkeypatch):
    import ux_valio_native

    def boom(*args, **kwargs):
        raise ValueError("native exploded")

    monkeypatch.setattr(ux_valio_native, "compile_ip", boom)
    with pytest.raises(RuntimeError, match="ux_valio_native") as caught:
        IPv4Validator(debug=True, name="n")
    assert isinstance(caught.value.__cause__, ValueError)
    assert "Overflow" not in str(caught.value)
    assert "expect" not in str(caught.value)


@needs_native
def test_unexpected_ip_native_apply_raises_runtime_error():
    field = IPv4Validator(debug=True, name="n")
    assert field._native_plan is not None

    def boom(plan, value):
        raise ValueError("native exploded")

    field._native_apply = boom
    with pytest.raises(RuntimeError, match="ux_valio_native") as caught:
        field.validate(None, _V4)
    assert isinstance(caught.value.__cause__, ValueError)


def test_ip_error_text_stays_the_host_sentence():
    field = IPv4Validator(debug=True, name="n")
    with pytest.raises(ValueError, match="n expects a valid IPv4 address, got 999.0.0.1 as value instead"):
        field.validate(None, "999.0.0.1")
    v6 = IPv6Validator(debug=True, name="n")
    with pytest.raises(ValueError, match="n expects a valid IPv6 address, got 127.0.0.1 as value instead"):
        v6.validate(None, _V4)
    either = IPAddressValidator(debug=True, name="n")
    with pytest.raises(ValueError, match="n expects a valid IP address, got not-an-ip as value instead"):
        either.validate(None, "not-an-ip")
