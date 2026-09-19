# SPDX-License-Identifier: MIT
"""India KYC intake: Aadhaar ∩ Verhoeff, PAN ∩ Luhn mod 26, IN phone.

``region=`` is required on ``PhoneNumberValidator`` (leftover: valio defaulted
to ``instance.region`` or ``"IN"``). ``collect_all=True`` continues each field's
inherited path into the named facade check. The engine is optional extra
``phonenumbers``; there is no network lookup. This module still imports and
runs identity checks when the extra is missing.

Inject ``IdentityRegistry`` on ``KycService``; ``main()`` only runs the demo.
``InMemoryIdentityRegistry`` is the runnable fake; production plugs a KYC
warehouse unique Aadhaar/PAN. This file does not ship a DB driver.
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


aadhaar_field = AadhaarCardValidator(debug=True, required=True, collect_all=True)
pan_field = PANCardValidator(debug=True, required=True, collect_all=True)


@dataclass
class KycIdentity:
    """Aadhaar ∩ Verhoeff, PAN ∩ Luhn mod 26. Always importable."""

    registry: IdentityRegistry
    aadhaar: str = aadhaar_field
    pan: str = pan_field

    @aadhaar.add_process_pre_validate
    def aadhaar_free(self, value: str) -> str:
        if self.registry.aadhaar_registered(value):
            raise ValueError(f"aadhaar {value!r} is already registered")
        return value

    @pan.add_process_pre_validate
    def pan_free(self, value: str) -> str:
        if self.registry.pan_registered(value):
            raise ValueError(f"PAN {value!r} is already registered")
        return value

    @pan.add_process_post_set
    def commit_identity(self, value: str) -> None:
        self.registry.commit(self.aadhaar, value)


if HAS_PHONENUMBERS and _PHONE is not None:

    @dataclass
    class KycRecord:
        """Production shape: identity plus ``PhoneNumberValidator(region='IN')``."""

        registry: IdentityRegistry
        aadhaar: str = aadhaar_field
        pan: str = pan_field
        phone: str = _PHONE

        @aadhaar.add_process_pre_validate
        def aadhaar_free(self, value: str) -> str:
            if self.registry.aadhaar_registered(value):
                raise ValueError(f"aadhaar {value!r} is already registered")
            return value

        @pan.add_process_pre_validate
        def pan_free(self, value: str) -> str:
            if self.registry.pan_registered(value):
                raise ValueError(f"PAN {value!r} is already registered")
            return value

        @pan.add_process_post_set
        def commit_identity(self, value: str) -> None:
            self.registry.commit(self.aadhaar, value)

else:
    KycRecord = KycIdentity


class KycService:
    """Composition root. Production: ``KycService(SqlKycStore(dsn))``."""

    def __init__(self, registry: IdentityRegistry) -> None:
        self.registry = registry

    def submit(
        self, aadhaar: str, pan: str, phone: str | None = None
    ) -> KycIdentity:
        """Accept a KYC row. Identity, registry, or phone failures raise."""
        if phone is not None and HAS_PHONENUMBERS and KycRecord is not KycIdentity:
            return KycRecord(
                registry=self.registry, aadhaar=aadhaar, pan=pan, phone=phone
            )
        return KycIdentity(registry=self.registry, aadhaar=aadhaar, pan=pan)


def main() -> KycIdentity:
    service = KycService(InMemoryIdentityRegistry())
    if HAS_PHONENUMBERS and IN_NATIONAL:
        row = service.submit(VALID_AADHAAR, VALID_PAN, IN_NATIONAL)
    else:
        row = service.submit(VALID_AADHAAR, VALID_PAN)
    try:
        KycService(
            InMemoryIdentityRegistry(aadhaars={VALID_AADHAAR}, pans=set())
        ).submit(VALID_AADHAAR, VALID_PAN, phone=None)
    except (ValueError, ValidationErrors):
        pass
    try:
        KycService(InMemoryIdentityRegistry()).submit("123456789012", VALID_PAN)
    except (ValueError, ValidationErrors):
        pass
    try:
        KycService(InMemoryIdentityRegistry()).submit(VALID_AADHAAR, "AAAPA1111G")
    except (ValueError, ValidationErrors):
        pass
    return row


if __name__ == "__main__":
    accepted = main()
    phone = getattr(accepted, "phone", None)
    extra = f" phone={phone}" if phone else ""
    print(f"kyc pan={accepted.pan}{extra}")
