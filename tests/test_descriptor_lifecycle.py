# SPDX-License-Identifier: MIT
"""Descriptor lifecycle + remaining Door A honesty."""

from dataclasses import dataclass

import pytest

from ux_valio import IntegerValidator, ReassignValidator, RequiredValidator, TypeValidator, Validator


def test_reassign_false_blocks_second_assign():
    @dataclass
    class Once:
        s: str = Validator(reassign=False, debug=True)

    once = Once(s="a")
    assert once.s == "a"
    with pytest.raises(AttributeError):
        once.s = "b"
    assert once.s == "a"


def test_reassign_true_allows_second_assign():
    @dataclass
    class Many:
        s: str = Validator(reassign=True, debug=True)

    many = Many(s="a")
    many.s = "b"
    assert many.s == "b"


def test_delete_drops_reassignment_count():
    @dataclass
    class Once:
        s: str = Validator(reassign=False, debug=True)

    once = Once(s="a")
    del once.s
    once.s = "b"
    assert once.s == "b"
    with pytest.raises(AttributeError):
        once.s = "c"


def test_delete_then_get_is_none_when_debug_falsy():
    @dataclass
    class Box:
        s: str = Validator(debug=False)

    box = Box(s="x")
    del box.s
    assert box.s is None


def test_required_false_allows_none():
    @dataclass
    class Opt:
        s: str = RequiredValidator(required=False, debug=True)

    assert Opt(s=None).s is None


def test_required_true_keeps_false_as_present():
    @dataclass
    class Flag:
        s: object = RequiredValidator(required=True, debug=True)

    assert Flag(s=False).s is False


def test_required_rejects_non_bool_flag():
    with pytest.raises(TypeError):
        RequiredValidator(required="True")


def test_type_validator_accepts_bool_as_int():
    @dataclass
    class N:
        n: int = TypeValidator(debug=True)

    assert N(n=True).n is True
    assert N(n=False).n is False


def test_integer_true_is_int():
    @dataclass
    class N:
        n: int = IntegerValidator(debug=True)

    assert N(n=True).n is True


def test_errors_collect_on_swallowed_set():
    field = IntegerValidator(debug=False)

    @dataclass
    class N:
        n: int = field

    N(n="bad")
    assert field.errors
    assert isinstance(field.errors[-1], TypeError)


def test_star_import_does_not_leak_field_or_schema():
    namespace = {}
    exec("from ux_valio import *", namespace)
    assert "Field" not in namespace
    assert "Schema" not in namespace
    assert "Validator" in namespace
    assert "Cap" not in namespace
