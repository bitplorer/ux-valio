# SPDX-License-Identifier: MIT
"""Validation path fail-closed: unique units, second pass ok, no string lookup."""

import pytest

from ux_valio import Validator
from ux_valio.validators.facade import DEFAULT_PATH_UNITS, ValidationPath
from ux_valio.validators.leaves import TypeValidator
from ux_valio.validators.value import ValueValidator


def test_duplicate_unit_fails_closed():
    unit = TypeValidator._validate_type
    with pytest.raises(ValueError, match="double-call"):
        ValidationPath((unit, unit))


def test_default_validator_path_is_unique_and_ordered():
    assert Validator.validation_path.units == DEFAULT_PATH_UNITS
    units = Validator.validation_path.units
    assert len(units) == len(set(units))
    names = [unit.__name__ for unit in units]
    assert names == [
        "_validate_reassignment",
        "_validate_type",
        "_validate_required",
        "_validate_pattern",
        "_validate_multiple_of",
        "_validate_length",
        "_validate_value",
        "_validate_choice",
    ]
    assert "_validate_expiry" not in names


def test_value_unit_owns_min_max_eq():
    """min_value / max_value / eq are not separate path units."""
    names = {unit.__name__ for unit in Validator.validation_path.units}
    assert "_validate_value" in names
    assert names.isdisjoint({"_validate_min_value", "_validate_max_value", "_validate_eq"})


def test_path_run_is_per_pass_so_a_second_validate_is_allowed():
    calls = []

    def _once(owner, instance, value):
        calls.append(value)
        return value

    path = ValidationPath((_once,))
    path.run(None, None, 1)
    path.run(None, None, 2)
    assert calls == [1, 2]


def test_path_run_refuses_duplicate_units_inside_one_pass():
    def _once(owner, instance, value):
        return value

    path = ValidationPath((_once,))
    path.units = (_once, _once)
    with pytest.raises(ValueError, match="double-call"):
        path.run(None, None, 1)


def test_second_validate_on_validator_is_a_new_pass():
    v = Validator(min_value=0, debug=True)
    v.validate(None, 0)
    v.validate(None, 1)
    with pytest.raises(ValueError):
        v.validate(None, -1)


def test_subclass_can_narrow_the_path_to_real_callables():
    class Typed(Validator):
        annotation = int
        validation_path = ValidationPath((TypeValidator._validate_type,))

    Typed(debug=True).validate(None, 1)
    with pytest.raises(TypeError):
        Typed(debug=True).validate(None, "x")


def test_value_unit_still_gates_min_on_the_default_path():
    assert ValueValidator._validate_value in Validator.validation_path.units
