# SPDX-License-Identifier: MIT
"""IBANValidator: ISO 13616 identity ∩ mod-97."""

from dataclasses import dataclass

import pytest

from ux_valio import IBANValidator

VALID_IBAN = "GB82WEST12345698765432"
VALID_DE = "DE89370400440532013000"
FORMAT_ONLY = "GB82WEST12345698765433"


@pytest.fixture
def Account():
    @dataclass
    class Account:
        iban: str = IBANValidator()

    return Account


def test_mod97_valid_iban_is_accepted(Account):
    assert Account(iban=VALID_IBAN).iban == VALID_IBAN
    assert Account(iban=VALID_DE).iban == VALID_DE


def test_format_valid_checksum_invalid_iban_is_rejected(Account):
    with pytest.raises(ValueError):
        Account(iban=FORMAT_ONLY)


def test_grouped_iban_is_stored_compact(Account):
    assert Account(iban="GB82 WEST 1234 5698 7654 32").iban == VALID_IBAN


def test_lowercase_iban_is_stored_uppercase(Account):
    assert Account(iban=VALID_IBAN.lower()).iban == VALID_IBAN
