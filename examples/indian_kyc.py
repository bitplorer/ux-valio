# SPDX-License-Identifier: MIT
"""India KYC intake: Aadhaar ∩ Verhoeff, PAN ∩ Luhn mod 26, IN phone.

``region=`` is required on ``PhoneNumberValidator`` (leftover: valio defaulted
to ``instance.region`` or ``"IN"``). ``collect_all=True`` continues each field's
inherited path into the named facade check. The engine is optional extra
``phonenumbers``; there is no network lookup. This module still imports and
runs identity checks when the extra is missing.

``IdentityRegistry`` is the already-registered port. ``InMemoryIdentityRegistry``
is the runnable fake; production plugs a KYC warehouse unique Aadhaar/PAN.
This file does not ship a DB driver.
"""

from dataclasses import dataclass
from typing import Protocol

from ux_valio import (
    AadhaarCardValidator,
    PANCardValidator,
    PhoneNumberValidator,
    ValidationErrors,
)

HAS_PHONENUMBERS = False
IN_NATIONAL = ""
_PHONE = None
try:
    from phonenumbers import PhoneNumberFormat, example_number, format_number

    _PHONE = PhoneNumberValidator(
        region="IN", debug=True, required=True, collect_all=True
    )
except ImportError:
    pass
else:
    HAS_PHONENUMBERS = True
    IN_NATIONAL = format_number(example_number("IN"), PhoneNumberFormat.NATIONAL)

VALID_AADHAAR = "234567890124"
VALID_PAN = "AAAPA1111F"


class IdentityRegistry(Protocol):
    """Already-registered identity. Production: unique Aadhaar/PAN in the KYC store."""

    def aadhaar_registered(self, aadhaar: str) -> bool:
        """True when this Aadhaar is already on file."""
        ...

    def pan_registered(self, pan: str) -> bool:
        """True when this PAN is already on file."""
        ...

    def commit(self, aadhaar: str, pan: str) -> None:
        """Persist after a successful set."""
        ...


class InMemoryIdentityRegistry:
    """Runnable fake. Plug in the KYC warehouse that satisfies ``IdentityRegistry``."""

    def __init__(
        self,
        aadhaars: set[str] | None = None,
        pans: set[str] | None = None,
    ) -> None:
        self.aadhaars = set(aadhaars or ())
        self.pans = set(pans or ())

    def aadhaar_registered(self, aadhaar: str) -> bool:
        return aadhaar in self.aadhaars

    def pan_registered(self, pan: str) -> bool:
        return pan in self.pans

    def commit(self, aadhaar: str, pan: str) -> None:
        self.aadhaars.add(aadhaar)
        self.pans.add(pan)


REGISTRY: IdentityRegistry = InMemoryIdentityRegistry()

aadhaar_field = AadhaarCardValidator(debug=True, required=True, collect_all=True)
pan_field = PANCardValidator(debug=True, required=True, collect_all=True)


@dataclass
class KycIdentity:
    """Aadhaar ∩ Verhoeff, PAN ∩ Luhn mod 26. Always importable."""

    aadhaar: str = aadhaar_field
    pan: str = pan_field

    @aadhaar_field.add_validator
    def aadhaar_free(self, value: str) -> None:
        if REGISTRY.aadhaar_registered(value):
            raise ValueError(f"aadhaar {value!r} is already registered")

    @pan_field.add_validator
    def pan_free(self, value: str) -> None:
        if REGISTRY.pan_registered(value):
            raise ValueError(f"PAN {value!r} is already registered")

    @pan_field.add_post_set
    def commit_identity(self, value: str) -> None:
        REGISTRY.commit(self.aadhaar, value)


if HAS_PHONENUMBERS and _PHONE is not None:

    @dataclass
    class KycRecord:
        """Production shape: identity plus ``PhoneNumberValidator(region='IN')``."""

        aadhaar: str = aadhaar_field
        pan: str = pan_field
        phone: str = _PHONE

        @aadhaar_field.add_validator
        def aadhaar_free(self, value: str) -> None:
            if REGISTRY.aadhaar_registered(value):
                raise ValueError(f"aadhaar {value!r} is already registered")

        @pan_field.add_validator
        def pan_free(self, value: str) -> None:
            if REGISTRY.pan_registered(value):
                raise ValueError(f"PAN {value!r} is already registered")

        @pan_field.add_post_set
        def commit_identity(self, value: str) -> None:
            REGISTRY.commit(self.aadhaar, value)

else:
    KycRecord = KycIdentity


def bind_identity_registry(registry: IdentityRegistry) -> None:
    """Process composition root. Production: ``bind_identity_registry(SqlKycStore(dsn))``."""
    global REGISTRY
    REGISTRY = registry


def submit_kyc(
    aadhaar: str,
    pan: str,
    phone: str | None = None,
    *,
    registry: IdentityRegistry | None = None,
) -> KycIdentity:
    """Accept a KYC row. Identity, registry, or phone failures raise."""
    if registry is not None:
        bind_identity_registry(registry)
    if (
        phone is not None
        and HAS_PHONENUMBERS
        and KycRecord is not KycIdentity
    ):
        return KycRecord(aadhaar=aadhaar, pan=pan, phone=phone)
    return KycIdentity(aadhaar=aadhaar, pan=pan)


def main() -> KycIdentity:
    registry = InMemoryIdentityRegistry()
    if HAS_PHONENUMBERS and IN_NATIONAL:
        row = submit_kyc(VALID_AADHAAR, VALID_PAN, IN_NATIONAL, registry=registry)
    else:
        row = submit_kyc(VALID_AADHAAR, VALID_PAN, registry=registry)
    taken = InMemoryIdentityRegistry(aadhaars={VALID_AADHAAR}, pans=set())
    try:
        submit_kyc(VALID_AADHAAR, VALID_PAN, registry=taken, phone=None)
    except (ValueError, ValidationErrors):
        pass
    try:
        submit_kyc("123456789012", VALID_PAN, registry=InMemoryIdentityRegistry())
    except (ValueError, ValidationErrors):
        pass
    try:
        submit_kyc(VALID_AADHAAR, "AAAPA1111G", registry=InMemoryIdentityRegistry())
    except (ValueError, ValidationErrors):
        pass
    return row


if __name__ == "__main__":
    accepted = main()
    phone = getattr(accepted, "phone", None)
    extra = f" phone={phone}" if phone else ""
    print(f"kyc pan={accepted.pan}{extra}")
