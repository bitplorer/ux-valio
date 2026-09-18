# SPDX-License-Identifier: MIT
"""Door A stores on instance __dict__. slots drop the descriptor."""

from dataclasses import dataclass

import pytest

from ux_valio import IntegerValidator, ValidateProperty


def _cause_or_self(err: BaseException) -> BaseException:
    """3.10 wraps ``__set_name__`` in RuntimeError; 3.14 raises the cause."""
    return err.__cause__ if err.__cause__ is not None else err


def test_explicit_slots_fail_closed_at_bind():
    """CPython rejects a slot name that is also a class variable (ValueError).

    Door A TypeErrors if bind still runs. Either path is fail-closed.
    """
    with pytest.raises((TypeError, ValueError), match="slots"):

        class Box:
            __slots__ = ("n",)
            n = IntegerValidator(debug=True)


def test_slots_without_dict_fail_closed_at_bind():
    """A slots-only class cannot store any Door A field, even under another name."""
    with pytest.raises((TypeError, RuntimeError)) as caught:

        class Box:
            __slots__ = ("other",)
            n = IntegerValidator(debug=True)

    err = _cause_or_self(caught.value)
    assert isinstance(err, TypeError)
    assert "__dict__" in str(err) or "slots" in str(err)


def test_slots_with_dict_member_stores():
    class Box:
        __slots__ = ("other", "__dict__")
        n = IntegerValidator(debug=True)

    box = Box()
    box.n = 3
    assert box.n == 3
    assert box.__dict__["n"] == 3


def test_child_without_own_slots_keeps_dict():
    """Inherited ``getattr(cls, "__slots__")`` must not false-positive a child."""

    class Parent:
        __slots__ = ("x",)

    class Child(Parent):
        n = IntegerValidator(debug=True)

    child = Child()
    child.n = 4
    assert child.n == 4
    assert child.__dict__["n"] == 4


def test_parent_slot_same_name_does_not_block_child_with_dict():
    """Parent slot ``n`` is not this class's ``__slots__``; child has ``__dict__``."""

    class Parent:
        __slots__ = ("n",)

    class Child(Parent):
        n = IntegerValidator(debug=True)

    assert isinstance(Child.__dict__["n"], IntegerValidator)
    child = Child()
    child.n = 5
    assert child.n == 5


def test_dataclass_slots_replaces_descriptor():
    """@dataclass(slots=True) runs after __set_name__ and drops Door A.

    Unsupported: assignment does not validate. Lock the drop so a future
    accidental restore of the descriptor is visible.
    """

    @dataclass(slots=True)
    class S:
        n: int = IntegerValidator(debug=True)

    n = S.__dict__.get("n")
    assert not isinstance(n, ValidateProperty)
    stored = S(n="nope")
    assert stored.n == "nope"


def test_dataclass_frozen_validates_and_rejects_mutation():
    """@dataclass(frozen=True) keeps the descriptor. Dataclass intercepts set/delete."""
    from dataclasses import FrozenInstanceError

    @dataclass(frozen=True)
    class F:
        n: int = IntegerValidator(min_value=0, debug=True)

    assert F(n=3).n == 3
    with pytest.raises(TypeError):
        F(n="nope")
    frozen = F(n=4)
    with pytest.raises(FrozenInstanceError):
        frozen.n = 5
    with pytest.raises(FrozenInstanceError):
        del frozen.n
    assert frozen.n == 4
