# SPDX-License-Identifier: MIT
"""ExpiryValidator: exclusive expire_* kwargs; expire_before is its own bound."""

from dataclasses import dataclass
from datetime import date, timedelta

import pytest

from ux_valio import ExpiryValidator, Validator
from ux_valio.validators.path import DEFAULT_PATH_NAMES


def test_expire_before_string_sets_timeline():
    e = ExpiryValidator(expire_before="2020-01-01", debug=True)
    assert e.timeline == "before"
    assert e.expiry == "2020-01-01"


def test_expire_before_bad_string_is_rejected():
    with pytest.raises(ValueError):
        ExpiryValidator(expire_before="not-a-date", debug=True)


def test_expire_after_only_still_sets_timeline():
    e = ExpiryValidator(expire_after="2020-01-01", debug=True)
    assert e.timeline == "after"


def test_expire_before_does_not_pattern_check_expire_after():
    """expire_before is its own bound. Unset expire_after is not consulted."""
    e = ExpiryValidator(expire_before="2020-01-01", debug=True)
    assert e.expiry == "2020-01-01"
    assert e.timeline == "before"


def test_exclusive_expire_kwargs_are_rejected():
    with pytest.raises(TypeError, match="exclusive"):
        ExpiryValidator(
            expire_after="2020-01-01",
            expire_before="2021-01-01",
            debug=True,
        )


def test_generic_validator_still_rejects_expire_before():
    """expire_* belong on ExpiryValidator, not the fat Validator facade."""
    with pytest.raises(TypeError, match="expire_before"):
        Validator(expire_before="2020-01-01", debug=True)


def test_expiry_is_not_a_path_unit():
    assert "expiry" not in DEFAULT_PATH_NAMES


def test_expire_before_past_bound_allows_assignment():
    @dataclass
    class License:
        key: str = ExpiryValidator(expire_before="2020-01-01", debug=True)

    assert License(key="ok").key == "ok"


def test_expire_after_past_bound_rejects_assignment():
    @dataclass
    class License:
        key: str = ExpiryValidator(expire_after="2020-01-01", debug=True)

    with pytest.raises(ValueError, match="expired"):
        License(key="ok")


def test_expire_after_future_bound_allows_assignment():
    future = (date.today() + timedelta(days=365)).isoformat()

    @dataclass
    class License:
        key: str = ExpiryValidator(expire_after=future, debug=True)

    assert License(key="ok").key == "ok"


def test_expire_on_is_valid_only_on_that_calendar_day():
    today = date.today().isoformat()
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    @dataclass
    class TodayOnly:
        key: str = ExpiryValidator(expire_on=today, debug=True)

    assert TodayOnly(key="ok").key == "ok"

    @dataclass
    class TomorrowOnly:
        key: str = ExpiryValidator(expire_on=tomorrow, debug=True)

    with pytest.raises(ValueError, match="expired on"):
        TomorrowOnly(key="ok")
