# SPDX-License-Identifier: MIT
"""Facades compose concern leaves; they do not inherit them."""

from ux_valio import (
    ChoiceValidator,
    IntegerValidator,
    LengthValidator,
    MultipleValidator,
    PatternValidator,
    ReassignValidator,
    RequiredValidator,
    StringValidator,
    TypeValidator,
    ValidateProperty,
    Validator,
    ValueValidator,
)
from ux_valio.validators import (
    MaxLengthValidator,
    MaxValueValidator,
    MinLengthValidator,
    MinValueValidator,
)


CONCERN_LEAVES = (
    TypeValidator,
    RequiredValidator,
    PatternValidator,
    ReassignValidator,
    MultipleValidator,
    ValueValidator,
    LengthValidator,
    ChoiceValidator,
    MinValueValidator,
    MaxValueValidator,
    MinLengthValidator,
    MaxLengthValidator,
)


def test_validator_does_not_inherit_concern_leaves():
    for leaf in CONCERN_LEAVES:
        assert not issubclass(Validator, leaf), leaf.__name__
    assert issubclass(Validator, ValidateProperty)


def test_typed_aliases_still_subclass_validator():
    assert issubclass(IntegerValidator, Validator)
    assert issubclass(StringValidator, Validator)


def test_value_length_compose_min_max_leaves():
    assert not issubclass(ValueValidator, MinValueValidator)
    assert not issubclass(ValueValidator, MaxValueValidator)
    assert not issubclass(LengthValidator, MinLengthValidator)
    assert not issubclass(LengthValidator, MaxLengthValidator)
    assert issubclass(ValueValidator, ValidateProperty)
    assert issubclass(LengthValidator, ValidateProperty)


def test_value_validator_does_not_inherit_type_or_required():
    assert not issubclass(ValueValidator, TypeValidator)
    assert not issubclass(ValueValidator, RequiredValidator)
    assert not issubclass(LengthValidator, TypeValidator)


def test_mro_validator_is_validate_property_only():
    bases = Validator.__bases__
    assert bases == (ValidateProperty,)
    assert ValueValidator.__bases__ == (ValidateProperty,)
    assert LengthValidator.__bases__ == (ValidateProperty,)
