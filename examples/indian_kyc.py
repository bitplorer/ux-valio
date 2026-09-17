# SPDX-License-Identifier: MIT
"""India KYC intake: Aadhaar ∩ Verhoeff, PAN ∩ Luhn mod 26, IN phone.

``region=`` is required on ``PhoneNumberValidator`` (leftover: valio defaulted
to ``instance.region`` or ``"IN"``). ``collect_all=True`` continues each field's
inherited path into the named facade check. The engine is optional extra
``phonenumbers``; there is no network lookup.
"""

from dataclasses import dataclass

from phonenumbers import PhoneNumberFormat, example_number, format_number

from ux_valio import (
    AadhaarCardValidator,
    PANCardValidator,
    PhoneNumberValidator,
    ValidationErrors,
)

IN_NATIONAL = format_number(example_number("IN"), PhoneNumberFormat.NATIONAL)
VALID_AADHAAR = "234567890124"
VALID_PAN = "AAAPA1111F"


@dataclass
class KycRecord:
    aadhaar: str = AadhaarCardValidator(
        debug=True, required=True, collect_all=True
    )
    pan: str = PANCardValidator(debug=True, required=True, collect_all=True)
    phone: str = PhoneNumberValidator(
        region="IN", debug=True, required=True, collect_all=True
    )


def submit_kyc(aadhaar: str, pan: str, phone: str) -> KycRecord:
    """Accept a KYC row. Identity or phone failures raise."""
    return KycRecord(aadhaar=aadhaar, pan=pan, phone=phone)


def main() -> KycRecord:
    row = submit_kyc(VALID_AADHAAR, VALID_PAN, IN_NATIONAL)
    try:
        submit_kyc("123456789012", VALID_PAN, IN_NATIONAL)
    except (ValueError, ValidationErrors):
        pass
    try:
        submit_kyc(VALID_AADHAAR, "AAAPA1111G", IN_NATIONAL)
    except (ValueError, ValidationErrors):
        pass
    return row


if __name__ == "__main__":
    accepted = main()
    print(f"kyc pan={accepted.pan} phone={accepted.phone}")
