# SPDX-License-Identifier: MIT
"""0 is a bound; gt/lt exclusive; remainder means multiple-of."""

import pytest

from ux_valio import (
    IntegerValidator,
    LengthValidator,
    MaxLengthValidator,
    MaxValueValidator,
    MinLengthValidator,
    MinValueValidator,
    MultipleValidator,
    Validator,
    ValueValidator,
)


def test_min_value_zero_enforces_inclusive_floor():
    v = MinValueValidator(min_value=0, debug=True)
    assert v.min_value == 0
    v.validate(None, 0)
    v.validate(None, 1)
    with pytest.raises(ValueError):
        v.validate(None, -1)


def test_max_value_zero_enforces_inclusive_ceiling():
    v = MaxValueValidator(max_value=0, debug=True)
    assert v.max_value == 0
    v.validate(None, 0)
    v.validate(None, -1)
    with pytest.raises(ValueError):
        v.validate(None, 1)


def test_min_length_zero_is_a_bound_not_unset():
    v = MinLengthValidator(min_length=0, debug=True)
    assert v.min_length == 0
    v.validate(None, "")
    v.validate(None, "x")


def test_max_length_zero_enforces():
    v = MaxLengthValidator(max_length=0, debug=True)
    assert v.max_length == 0
    v.validate(None, "")
    with pytest.raises(ValueError):
        v.validate(None, "x")


def test_length_zero_enforces_exact():
    v = LengthValidator(length=0, debug=True)
    assert v.length == 0
    v.validate(None, "")
    with pytest.raises(ValueError):
        v.validate(None, "x")


def test_gt_zero_rejects_zero_accepts_one():
    v = MinValueValidator(gt=0, debug=True)
    with pytest.raises(ValueError):
        v.validate(None, 0)
    v.validate(None, 1)


def test_lt_zero_rejects_zero_accepts_minus_one():
    v = MaxValueValidator(lt=0, debug=True)
    with pytest.raises(ValueError):
        v.validate(None, 0)
    v.validate(None, -1)


def test_value_validator_gt_lt_exclusive():
    gt = ValueValidator(gt=0, debug=True)
    with pytest.raises(ValueError):
        gt.validate(None, 0)
    gt.validate(None, 1)

    lt = ValueValidator(lt=0, debug=True)
    with pytest.raises(ValueError):
        lt.validate(None, 0)
    lt.validate(None, -1)


def test_min_value_zero_with_gt_none_does_not_collapse():
    v = MinValueValidator(min_value=0, gt=None, debug=True)
    assert v.min_value == 0
    v.validate(None, 0)
    with pytest.raises(ValueError):
        v.validate(None, -1)


def test_max_value_zero_with_lt_none_does_not_collapse():
    v = MaxValueValidator(max_value=0, lt=None, debug=True)
    assert v.max_value == 0
    v.validate(None, 0)
    with pytest.raises(ValueError):
        v.validate(None, 1)


def test_value_validator_min_value_zero_gt_none_does_not_collapse():
    v = ValueValidator(min_value=0, gt=None, debug=True)
    assert v.min_value == 0
    v.validate(None, 0)
    with pytest.raises(ValueError):
        v.validate(None, -1)


def test_value_zero_is_kept_and_enforced():
    v = ValueValidator(value=0, debug=True)
    assert v.value == 0
    v.validate(None, 0)
    with pytest.raises(ValueError):
        v.validate(None, 1)


def test_eq_zero_is_kept_and_enforced():
    v = ValueValidator(eq=0, debug=True)
    assert v.value == 0
    v.validate(None, 0)
    with pytest.raises(ValueError):
        v.validate(None, 1)


def test_multiple_of_two_accepts_multiples_rejects_remainder():
    v = MultipleValidator(multiple_of=2, debug=True)
    v.validate(None, 0)
    v.validate(None, 2)
    v.validate(None, 4)
    with pytest.raises(ValueError):
        v.validate(None, 1)
    with pytest.raises(ValueError):
        v.validate(None, 3)


def test_multiple_of_zero_is_kept_and_safe():
    v = MultipleValidator(multiple_of=0, debug=True)
    assert v.multiple_of == 0
    v.validate(None, 0)
    with pytest.raises(ValueError):
        v.validate(None, 1)


def test_min_value_zero_and_gt_zero_conflict():
    with pytest.raises(ValueError):
        ValueValidator(min_value=0, gt=0, debug=True)
    with pytest.raises(ValueError):
        MinValueValidator(min_value=0, gt=0, debug=True)
    with pytest.raises(ValueError):
        Validator(min_value=0, gt=0, debug=True)


def test_max_value_zero_and_lt_zero_conflict():
    with pytest.raises(ValueError):
        ValueValidator(max_value=0, lt=0, debug=True)
    with pytest.raises(ValueError):
        MaxValueValidator(max_value=0, lt=0, debug=True)
    with pytest.raises(ValueError):
        Validator(max_value=0, lt=0, debug=True)


def test_value_and_eq_zero_conflict():
    with pytest.raises(ValueError):
        ValueValidator(value=0, eq=0, debug=True)


def test_equal_zero_range_is_allowed():
    v = ValueValidator(min_value=0, max_value=0, debug=True)
    v.validate(None, 0)
    with pytest.raises(ValueError):
        v.validate(None, 1)
    length = LengthValidator(min_length=0, max_length=0, debug=True)
    length.validate(None, "")
    with pytest.raises(ValueError):
        length.validate(None, "x")


def test_facade_min_value_zero_enforces():
    v = Validator(min_value=0, debug=True)
    assert v.min_value == 0
    v.validate(None, 0)
    with pytest.raises(ValueError):
        v.validate(None, -1)


def test_facade_length_zero_enforces():
    v = Validator(length=0, debug=True)
    v.validate(None, "")
    with pytest.raises(ValueError):
        v.validate(None, "x")


def test_facade_multiple_of_zero_still_safe():
    v = Validator(multiple_of=0, debug=True)
    assert v.multiple_of == 0
    v.validate(None, 0)
    with pytest.raises(ValueError):
        v.validate(None, 1)


def test_integer_validator_zero_bounds_on_assign():
    from dataclasses import dataclass

    @dataclass
    class Count:
        n: int = IntegerValidator(min_value=0, max_value=10, multiple_of=2, debug=True)

    assert Count(n=0).n == 0
    assert Count(n=10).n == 10
    with pytest.raises(ValueError):
        Count(n=-2)
    with pytest.raises(ValueError):
        Count(n=3)


def test_bound_value_leftover_alias():
    from ux_valio.validators.bounds import bound, bound_value

    assert bound is bound_value
    owner = type("O", (), {"min_value": 0, "missing": None})()
    assert bound_value(owner, "min_value") == 0
    assert bound_value(owner, "missing") is None
