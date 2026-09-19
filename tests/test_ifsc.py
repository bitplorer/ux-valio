# SPDX-License-Identifier: MIT
"""IFSCValidator: 11-char RBI identity. Not a directory lookup."""

from dataclasses import dataclass

import pytest

from ux_valio import IFSCValidator

VALID_IFSC = "SBIN0005943"


@pytest.fixture
def Branch():
    @dataclass
    class Branch:
        ifsc: str = IFSCValidator()

    return Branch


def test_valid_ifsc_is_accepted(Branch):
    assert Branch(ifsc=VALID_IFSC).ifsc == VALID_IFSC


def test_lowercase_ifsc_is_stored_uppercase(Branch):
    assert Branch(ifsc="sbin0005943").ifsc == VALID_IFSC


def test_grouped_ifsc_is_stored_compact(Branch):
    assert Branch(ifsc="SBIN 0005943").ifsc == VALID_IFSC


def test_fifth_char_not_zero_is_rejected(Branch):
    with pytest.raises(ValueError):
        Branch(ifsc="SBIN1005943")


def test_short_ifsc_is_rejected(Branch):
    with pytest.raises(ValueError):
        Branch(ifsc="SBIN00059")
