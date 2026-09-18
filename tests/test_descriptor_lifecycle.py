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


def test_never_set_get_is_named_attributeerror_when_debug():
    """Missing instance value is AttributeError, not bare KeyError."""

    @dataclass
    class Box:
        s: str = Validator(debug=True)

    box = Box.__new__(Box)
    with pytest.raises(AttributeError, match=r"Box\.s is not set") as exc:
        _ = box.s
    assert type(exc.value) is AttributeError


def test_delete_then_get_is_named_attributeerror_when_debug():
    @dataclass
    class Box:
        s: str = Validator(debug=True)

    box = Box(s="x")
    del box.s
    with pytest.raises(AttributeError, match=r"Box\.s is not set"):
        _ = box.s


def test_never_set_get_is_none_when_debug_falsy():
    """leftover: debug-falsy swallow still reads back None, not fail-closed."""

    @dataclass
    class Box:
        s: str = Validator(debug=False)

    box = Box.__new__(Box)
    assert box.s is None


def test_delete_never_set_is_named_attributeerror_when_debug():
    @dataclass
    class Box:
        s: str = Validator(debug=True)

    box = Box.__new__(Box)
    with pytest.raises(AttributeError, match=r"Box\.s is not set"):
        del box.s


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


def test_assignment_counts_drop_when_instance_is_collected():
    field = Validator(reassign=False, debug=True)

    @dataclass
    class Once:
        s: str = field

    once = Once(s="a")
    oid = id(once)
    assert field._assignment_counts.get(oid) == 1
    del once
    import gc

    gc.collect()
    assert oid not in field._assignment_counts
    assert oid not in field._assignment_alive


def test_post_get_does_not_replace_in_flight_never_set_error():
    field = Validator(debug=True)

    def boom(instance, value):
        raise RuntimeError("post_get boom")

    @dataclass
    class Box:
        s: str = field

    from ux_valio.validators.hooks import HookHost

    field.add_post_get(boom, namespace=HookHost._bag_key(Box))
    box = Box.__new__(Box)
    with pytest.raises(AttributeError, match=r"Box\.s is not set") as exc:
        _ = box.s
    assert type(exc.value) is AttributeError
    assert any(isinstance(err, RuntimeError) for err in field.errors)


def test_post_validate_cannot_store_type_mismatch():
    field = IntegerValidator(debug=True)

    def smash(instance, value):
        return "not-an-int"

    @dataclass
    class N:
        n: int = field

    from ux_valio.validators.hooks import HookHost

    field.add_post_validator(smash, namespace=HookHost._bag_key(N))
    with pytest.raises(TypeError, match="int"):
        N(n=2)


def test_post_validate_cannot_store_named_facade_lie():
    """Named-facade extra is a store invariant, same class as the type door."""
    from datetime import date, datetime

    from ux_valio import DateValidator, EmailValidator, PaymentCardValidator
    from ux_valio.validators.hooks import HookHost

    email = EmailValidator(debug=True)

    def not_email(instance, value):
        return "not-an-email"

    @dataclass
    class Contact:
        s: str = email

    email.add_post_validator(not_email, namespace=HookHost._bag_key(Contact))
    with pytest.raises(ValueError, match="email"):
        Contact(s="ada@example.com")

    card = PaymentCardValidator(debug=True)

    def not_card(instance, value):
        return "0000"

    @dataclass
    class Wallet:
        c: str = card

    card.add_post_validator(not_card, namespace=HookHost._bag_key(Wallet))
    with pytest.raises(ValueError, match="payment card"):
        Wallet(c="4111111111111111")

    when = DateValidator(debug=True)

    def to_datetime(instance, value):
        return datetime(2020, 1, 1, 12, 0)

    @dataclass
    class Day:
        d: date = when

    when.add_post_validator(to_datetime, namespace=HookHost._bag_key(Day))
    with pytest.raises(TypeError, match="datetime"):
        Day(d=date(2020, 1, 1))


def test_post_validate_may_transform_within_unnamed_str_door():
    """Path bounds are not re-run. Unnamed StringValidator identity is the type."""
    from ux_valio import StringValidator
    from ux_valio.validators.hooks import HookHost

    field = StringValidator(min_length=3, debug=True)

    def shorten(instance, value):
        return "x"

    @dataclass
    class Tag:
        s: str = field

    field.add_post_validator(shorten, namespace=HookHost._bag_key(Tag))
    assert Tag(s="abcd").s == "x"


def test_length_unsized_value_is_named_typeerror():
    from ux_valio import LengthValidator, Validator

    v = LengthValidator(min_length=1, debug=True, name="n")
    with pytest.raises(TypeError, match="sized value"):
        v.validate(None, 5)

    @dataclass
    class Box:
        n: int = Validator(min_length=1, debug=True)

    with pytest.raises(TypeError, match="sized value"):
        Box(n=5)


def test_logger_true_binds_stdlib_logger_and_logs(caplog):
    import logging

    from ux_valio import StringValidator

    unbound = StringValidator(logger=True, debug=True)
    assert unbound.logger is True

    @dataclass
    class User:
        name: str = StringValidator(logger=True, debug=True, max_length=8)

    desc = User.__dict__["name"]
    assert desc.logger is not True
    assert desc.logger.name.endswith(".User.name")
    assert desc._opts["logger"].value is True
    assert desc._opts["logger"].specified is True

    with caplog.at_level(logging.INFO, logger=desc.logger.name):
        user = User(name="Ada")
        assert user.name == "Ada"
        del user.name
    text = " ".join(record.getMessage() for record in caplog.records)
    assert "User.name: set" in text
    assert "User.name: get" in text
    assert "User.name: delete" in text

    with caplog.at_level(logging.ERROR, logger=desc.logger.name):
        with pytest.raises(ValueError):
            User(name="too-long-name")
    assert any("maximum length" in rec.getMessage() for rec in caplog.records)


def test_logger_false_stays_off_and_custom_logger_is_kept():
    import logging

    from ux_valio import StringValidator

    @dataclass
    class Quiet:
        s: str = StringValidator(debug=True)

    assert Quiet.__dict__["s"].logger is False

    custom = logging.getLogger("ux_valio.test.custom")

    @dataclass
    class Loud:
        s: str = StringValidator(logger=custom, debug=True)

    assert Loud.__dict__["s"].logger is custom


def test_annotation_checker_is_bound_once_on_leaves_import():
    from ux_valio.validators import base as base_mod
    from ux_valio.validators.leaves import is_instance_of

    assert base_mod._matches_annotation is is_instance_of
    assert base_mod._annotation_accepts(int, 1) is True
    assert base_mod._matches_annotation is is_instance_of


def test_dunder_version_matches_pyproject():
    import re
    from pathlib import Path

    import ux_valio

    text = Path(__file__).resolve().parents[1].joinpath("pyproject.toml").read_text()
    match = re.search(r'^version = "([^"]+)"', text, re.MULTILINE)
    assert match is not None
    assert ux_valio.__version__ == match.group(1)
