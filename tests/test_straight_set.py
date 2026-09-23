# SPDX-License-Identifier: MIT
"""Closed native setattr stays on the straight line only with no set-phase hangs.

Get/delete hangs do not walk set. Registered pre/post_validate still run.
Failure messages stay on the full descriptor path.
"""

from dataclasses import dataclass

import pytest

from ux_valio import IntegerValidator
from ux_valio.errors import ValidationErrors
from ux_valio.validators.hooks import _SET_PHASE_MASK

from tests.native_support import needs_native


def test_int_field_stores_and_rejects_without_requiring_native():
    """Host path when the optional peer is absent. Straight line is not required."""

    @dataclass
    class Box:
        n: int = IntegerValidator(min_value=0, debug=True)

    field = Box.__dict__["n"]
    row = Box(n=4)
    assert row.n == 4
    assert row.__dict__["n"] == 4
    with pytest.raises(ValueError, match="minimum value of 0, got -1"):
        row.n = -1
    assert row.n == 4
    with pytest.raises(ValidationErrors, match="expect"):
        row.n = "x"
    assert row.n == 4
    if field._native_plan is None:
        assert field._native_run is None


@needs_native
def test_closed_int_straight_set_when_plan_bound():
    @dataclass
    class Box:
        n: int = IntegerValidator(min_value=0, debug=True)

    field = Box.__dict__["n"]
    assert field._native_plan is not None
    assert field._native_run is not None
    assert field._straight_eligible
    assert (field._phase_mask & _SET_PHASE_MASK) == 0

    row = Box(n=4)
    assert row.n == 4
    assert row.__dict__["n"] == 4
    with pytest.raises(ValueError, match="minimum value of 0, got -1"):
        row.n = -1
    assert row.n == 4
    with pytest.raises(ValidationErrors, match="expect"):
        row.n = "x"
    assert row.n == 4


def test_get_only_hang_does_not_skip_bounds_and_runs_on_get():
    seen: list[str] = []

    @dataclass
    class Box:
        n: int = IntegerValidator(min_value=0, debug=True)

        @n.pre_get
        def watch(self, value):
            seen.append("get")
            return value

    row = Box(n=2)
    assert seen == []
    assert row.n == 2
    assert seen == ["get"]
    with pytest.raises(ValueError, match="minimum value"):
        row.n = -1
    assert row.__dict__["n"] == 2


def test_empty_pre_and_post_validate_still_run():
    calls: list[str] = []

    @dataclass
    class Box:
        n: int = IntegerValidator(min_value=0, debug=True)

        @n.pre_validate
        def pre(self, value):
            calls.append("pre")
            return value

        @n.post_validate
        def post(self, value):
            calls.append("post")
            return value

    row = Box(n=3)
    assert calls == ["pre", "post"]
    assert row.__dict__["n"] == 3
    row.n = 5
    assert calls == ["pre", "post", "pre", "post"]
    assert row.__dict__["n"] == 5


def test_thin_pre_validate_return_is_stored():
    @dataclass
    class Box:
        n: int = IntegerValidator(min_value=0, debug=True)

        @n.pre_validate
        def bump(self, value):
            if value is None:
                return value
            return value + 1

    assert Box(n=1).n == 2
    with pytest.raises(ValueError, match="minimum value"):
        Box(n=-2)


def test_post_set_return_is_not_stored():
    @dataclass
    class Box:
        n: int = IntegerValidator(min_value=0, debug=True)

        @n.post_set
        def after(self, value):
            return value + 10

    row = Box(n=3)
    assert row.__dict__["n"] == 3
    assert row.n == 3


def test_post_validate_replaced_value_still_type_checks():
    @dataclass
    class Box:
        n: int = IntegerValidator(min_value=0, debug=True)

    def smash(instance, value):
        return "nope"

    Box.__dict__["n"].post_validate(smash, namespace=Box)
    with pytest.raises(TypeError, match="expect"):
        Box(n=1)


def test_straight_miss_records_one_error_when_debug_swallows():
    field = IntegerValidator(min_value=0, debug=False, name="n")

    @dataclass
    class Box:
        n: int = field

    row = Box(n=-1)
    assert row.__dict__.get("n") is None
    assert len(field.errors) == 1
    assert "minimum value" in str(field.errors[0])


def test_none_skips_straight_line_and_stores():
    @dataclass
    class Box:
        n: int = IntegerValidator(min_value=0, debug=True)

    assert Box(n=None).n is None
