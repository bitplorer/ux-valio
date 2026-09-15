# SPDX-License-Identifier: MIT
"""Validation path fail-closed: unique units, aggregate owns leaves, second pass ok."""

import pytest

from ux_valio import Validator
from ux_valio.validators.path import DEFAULT_PATH_NAMES, ValidationPath


def test_duplicate_unit_fails_closed():
    with pytest.raises(ValueError, match="double-call"):
        ValidationPath(("value", "value"))


def test_aggregate_plus_owned_leaf_fails_closed():
    with pytest.raises(ValueError, match="conflict"):
        ValidationPath(("value", "min_value"))
    with pytest.raises(ValueError):
        ValidationPath(("length", "max_length"))
    with pytest.raises(ValueError, match="conflict"):
        ValidationPath(("value", "eq"))


def test_default_validator_path_is_unique_and_ordered():
    assert tuple(Validator.validation_path.names) == DEFAULT_PATH_NAMES
    names = Validator.validation_path.names
    assert len(names) == len(set(names))


def test_path_run_is_per_pass_so_a_second_validate_is_allowed():
    calls = []

    def _once(owner, instance, value):
        calls.append(value)
        return value

    path = ValidationPath(("type",))
    path.run(None, None, 1, {"type": _once})
    path.run(None, None, 2, {"type": _once})
    assert calls == [1, 2]


def test_path_run_refuses_duplicate_names_inside_one_pass():
    path = ValidationPath(("type",))
    path.names = ("type", "type")
    with pytest.raises(ValueError, match="double-call"):
        path.run(None, None, 1, {"type": lambda *args: None})


def test_second_validate_on_validator_is_a_new_pass():
    v = Validator(min_value=0, debug=True)
    v.validate(None, 0)
    v.validate(None, 1)
    with pytest.raises(ValueError):
        v.validate(None, -1)


def test_owned_leaf_without_aggregate_is_allowed():
    path = ValidationPath(("min_value", "max_value"))
    assert path.names == ("min_value", "max_value")
