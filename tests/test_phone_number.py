# SPDX-License-Identifier: MIT
"""PhoneNumberValidator: region door ∩ phonenumbers. No network, no Matcher."""

from dataclasses import dataclass
from pathlib import Path

import pytest

import phonenumbers
from phonenumbers import PhoneNumberFormat, example_number, format_number

from ux_valio import PhoneNumberValidator, Validator
from ux_valio.validators import phone as phone_mod

IN_EXAMPLE = example_number("IN")
IN_NATIONAL = format_number(IN_EXAMPLE, PhoneNumberFormat.NATIONAL)
IN_E164 = format_number(IN_EXAMPLE, PhoneNumberFormat.E164)
US_E164 = format_number(example_number("US"), PhoneNumberFormat.E164)
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def Phone():
    @dataclass
    class Phone:
        n: str = PhoneNumberValidator(region="IN", debug=True, logger=False)

    return Phone


def test_region_is_required():
    with pytest.raises(TypeError, match="region"):
        PhoneNumberValidator(debug=True)


def test_region_is_not_a_validator_kwarg():
    with pytest.raises(TypeError):
        Validator(region="IN")


def test_region_must_be_str():
    with pytest.raises(TypeError, match="region"):
        PhoneNumberValidator(region=91, debug=True)


def test_unsupported_region_is_value_error():
    with pytest.raises(ValueError, match="region"):
        PhoneNumberValidator(region="XX", debug=True)


def test_indian_national_and_e164_are_accepted(Phone):
    assert Phone(n=IN_NATIONAL).n == IN_NATIONAL
    assert Phone(n=IN_E164).n == IN_E164


def test_foreign_e164_is_rejected_for_indian_region(Phone):
    with pytest.raises(ValueError, match="IN"):
        Phone(n=US_E164)


def test_garbage_and_substring_are_rejected(Phone):
    with pytest.raises(ValueError):
        Phone(n="123")
    with pytest.raises(ValueError):
        Phone(n=f"call {IN_E164} now")


def test_instance_region_is_not_a_second_door():
    field = PhoneNumberValidator(region="IN", debug=True, logger=False)

    class Host:
        region = "US"

    with pytest.raises(ValueError, match="IN"):
        field.validate(Host(), US_E164)
    field.validate(Host(), IN_E164)


def test_missing_engine_teaches_phonenumbers_extra(monkeypatch):
    import builtins
    import sys

    monkeypatch.delitem(sys.modules, "phonenumbers", raising=False)
    real_import = builtins.__import__

    def guarded(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "phonenumbers" or name.startswith("phonenumbers."):
            raise ImportError("hidden")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded)
    with pytest.raises(ImportError, match=r"ux-valio\[phonenumbers\]"):
        phone_mod._require_phonenumbers()


def test_phone_module_has_no_network_or_matcher():
    source = (ROOT / "ux_valio" / "validators" / "phone.py").read_text()
    assert "urllib" not in source
    assert "requests" not in source
    assert "carrier" not in source
    assert "geocoder" not in source
    assert "PhoneNumberMatcher" not in source
    assert phonenumbers.__name__ == "phonenumbers"
