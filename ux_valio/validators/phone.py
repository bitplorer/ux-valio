# SPDX-License-Identifier: MIT
"""Phone-number Door A facade. Region ∩ phonenumbers; no network."""

from __future__ import annotations

from typing import Any

from ux_valio.validators.facade import StringValidator


def _require_phonenumbers():
    """Load the optional ``phonenumbers`` engine. No carrier / geocoder network."""
    try:
        import phonenumbers
    except ImportError as err:
        raise ImportError(
            "PhoneNumberValidator requires the phonenumbers extra: "
            "pip install ux-valio[phonenumbers]"
        ) from err
    return phonenumbers


class PhoneNumberValidator(StringValidator):
    """Door A string facade: valid number for an explicit ``region=`` door.

    Leftover: valio defaulted to ``instance.region`` or ``"IN"``. Pass
    ``region=`` on this facade (typically ``region="IN"`` to match that
    leftover). ``region`` is not a kwarg on ``Validator``.
    """

    def __init__(self, *, region: str, **kwargs: Any) -> None:
        phonenumbers = _require_phonenumbers()
        if not isinstance(region, str):
            raise TypeError(
                f"region expected type str value, got {type(region).__name__} type instead"
            )
        if region not in phonenumbers.SUPPORTED_REGIONS:
            raise ValueError(
                f"region {region!r} is not a supported phonenumbers region"
            )
        self.region = region
        super().__init__(**kwargs)

    def _named_extra(self, instance: Any = None, value: Any = None) -> None:
        self._validate_phone_number(instance, value)

    def _validate_phone_number(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not isinstance(value, str):
            raise ValueError(f"{self.name} is not a valid {self.region} phone number")
        phonenumbers = _require_phonenumbers()
        try:
            parsed = phonenumbers.parse(value, self.region)
        except phonenumbers.NumberParseException as err:
            raise ValueError(
                f"{self.name} is not a valid {self.region} phone number"
            ) from err
        if not phonenumbers.is_valid_number_for_region(parsed, self.region):
            raise ValueError(f"{self.name} is not a valid {self.region} phone number")
