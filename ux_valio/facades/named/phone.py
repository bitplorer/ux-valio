# SPDX-License-Identifier: MIT
"""Phone-number. Region ∩ phonenumbers; no network."""

from __future__ import annotations

from typing import Any

from ux_valio.facades.typed import StringValidator


class PhoneNumberValidator(StringValidator):
    """Valid number for an explicit ``region=``.

    Usage::

        phone: str = PhoneNumberValidator(region="IN")

    ``region`` is required (ISO 3166-1 alpha-2 as ``phonenumbers``
    understands it). Leftover: valio defaulted to ``instance.region`` or
    ``"IN"`` — pass ``region=`` here. ``region`` is not a kwarg on
    ``Validator``. Engine: ``pip install ux-valio[phonenumbers]``. No
    carrier / geocoder network.
    """

    @staticmethod
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

    def __init__(self, *, region: str, **kwargs: Any) -> None:
        if not isinstance(region, str):
            raise TypeError(
                f"region expected type str value, got {type(region).__name__} type instead"
            )
        self._phonenumbers = type(self)._require_phonenumbers()
        if region not in self._phonenumbers.SUPPORTED_REGIONS:
            raise ValueError(
                f"region {region!r} is not a supported phonenumbers region"
            )
        self.region = region
        super().__init__(**kwargs)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        self._validate_phone_number(instance, value)

    def _validate_phone_number(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not isinstance(value, str):
            raise ValueError(f"{self.name} is not a valid {self.region} phone number")
        phonenumbers = self._phonenumbers
        try:
            parsed = phonenumbers.parse(value, self.region)
        except phonenumbers.NumberParseException as err:
            raise ValueError(
                f"{self.name} is not a valid {self.region} phone number"
            ) from err
        if not phonenumbers.is_valid_number_for_region(parsed, self.region):
            raise ValueError(f"{self.name} is not a valid {self.region} phone number")
