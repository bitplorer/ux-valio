# SPDX-License-Identifier: MIT
"""Door A honesty — generics, reuse, unknown kwargs. No add_pre_set."""

from dataclasses import dataclass

import pytest

from ux_valio import IntegerValidator, Property, Validator
from ux_valio.validators import Validator as Facade
from ux_valio.validators.hooks import HookHost


def test_no_add_pre_set_on_validator():
    """pre_set is the validate pipeline, not a processor bag."""
    assert not hasattr(Validator, "add_pre_set")
    assert not hasattr(Validator, "add_pre_set_task")
    assert "pre_set" not in Facade()._processors
    assert "pre_set" not in Facade()._tasks
    assert set(Facade()._processors) == {
        "pre_validate",
        "post_validate",
        "post_set",
        "pre_get",
        "post_get",
        "pre_delete",
        "post_delete",
    }


def test_add_pre_validator_is_the_pre_set_pipeline():
    v = Validator(debug=True)

    def strip(instance, value):
        return value.strip() if isinstance(value, str) else value

    @dataclass
    class Host:
        x: str = v

    v.add_pre_validator(strip, namespace=HookHost._owner_key(Host))

    assert Host(x="  Ada  ").x == "Ada"


def test_list_int_annotation_accepts_list_rejects_int():
    field = Validator(debug=True)

    @dataclass
    class Box:
        items: list[int] = field

    assert Box(items=[1, 2]).items == [1, 2]
    with pytest.raises(TypeError, match="list"):
        Box(items=1)
    with pytest.raises(TypeError):
        Box(items=["a"])


def test_dict_annotation_accepts_dict_rejects_str():
    field = Validator(debug=True)

    @dataclass
    class Map:
        m: dict[str, int] = field

    assert Map(m={"a": 1}).m == {"a": 1}
    with pytest.raises(TypeError):
        Map(m="a")
    with pytest.raises(TypeError):
        Map(m={1: "a"})


def test_list_int_or_none_accepts_list_and_none_rejects_int():
    field = Validator(debug=True)

    @dataclass
    class Box:
        items: list[int] | None = field

    assert Box(items=[1]).items == [1]
    assert Box(items=None).items is None
    with pytest.raises(TypeError):
        Box(items=1)
    with pytest.raises(TypeError):
        Box(items=["a"])


def test_union_int_str_still_rejects_float():
    field = Validator(debug=True)

    @dataclass
    class Either:
        n: int | str = field

    assert Either(n=1).n == 1
    assert Either(n="a").n == "a"
    with pytest.raises(TypeError):
        Either(n=1.5)


def test_reused_validator_different_name_raises_even_when_first_annotation_is_none():
    shared = Validator(debug=True)

    class First:
        x = shared

    assert shared.name == "x"
    with pytest.raises(AttributeError, match="did not match"):
        class Second:
            y: int = shared
    assert shared.name == "x"


def test_reused_validator_different_name_raises_when_annotations_disagree():
    shared = Validator(debug=True)

    @dataclass
    class First:
        a: str = shared

    with pytest.raises(AttributeError, match="did not match"):
        @dataclass
        class Second:
            b: int = shared


def test_same_field_name_may_be_reused_across_classes():
    shared = IntegerValidator(debug=True)

    @dataclass
    class First:
        n: int = shared

    @dataclass
    class Second:
        n: int = shared

    assert First(n=1).n == 1
    assert Second(n=2).n == 2


def test_unexpected_expire_before_kwarg_is_type_error():
    """expire_* belong on ExpiryValidator; the fat Validator facade stays closed."""
    with pytest.raises(TypeError, match="expire_before"):
        Validator(expire_before="2020-01-01", debug=True)


def test_property_annotation_kwarg_is_type_error_not_silent_kwargs():
    with pytest.raises(TypeError, match="annotation"):
        Property(annotation=str, debug=True)


def test_postponed_annotation_conflict_quotes_the_string_label():
    ns: dict = {}
    exec(
        """
from __future__ import annotations
from dataclasses import dataclass
from ux_valio import IntegerValidator
import pytest

field = IntegerValidator(debug=True)
with pytest.raises(TypeError, match=r"N.n: 'int'"):
    @dataclass
    class N:
        n: int = field
assert field.annotation is int
""",
        ns,
    )
