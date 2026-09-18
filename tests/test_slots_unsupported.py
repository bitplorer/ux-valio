# SPDX-License-Identifier: MIT
"""Door A stores on instance __dict__. slots drop the descriptor."""

from dataclasses import dataclass

import pytest

from ux_valio import IntegerValidator, ValidateProperty


def test_explicit_slots_fail_closed_at_bind():
    """CPython rejects a slot name that is also a class variable (ValueError).

    Door A TypeErrors if bind still runs. Either path is fail-closed.
    """
    with pytest.raises((TypeError, ValueError), match="slots"):

        class Box:
            __slots__ = ("n",)
            n = IntegerValidator(debug=True)


def test_explicit_slots_other_name_is_not_this_field():
    class Box:
        __slots__ = ("other",)
        n = IntegerValidator(debug=True)

    assert isinstance(Box.__dict__["n"], IntegerValidator)


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
