# SPDX-License-Identifier: MIT
"""India KYC: Aadhaar ∩ Verhoeff, PAN ∩ Luhn mod 26, phone region door."""

from dataclasses import dataclass

from phonenumbers import PhoneNumberFormat, example_number, format_number

from ux_valio import AadhaarCardValidator, PANCardValidator, PhoneNumberValidator

IN_NATIONAL = format_number(example_number("IN"), PhoneNumberFormat.NATIONAL)


@dataclass
class KycRecord:
    aadhaar: str = AadhaarCardValidator(debug=True, required=True)
    pan: str = PANCardValidator(debug=True, required=True)
    phone: str = PhoneNumberValidator(region="IN", debug=True, required=True)


def main() -> KycRecord:
    row = KycRecord(
        aadhaar="234567890124",
        pan="AAAPA1111F",
        phone=IN_NATIONAL,
    )
    assert row.pan == "AAAPA1111F"
    return row


if __name__ == "__main__":
    print(main())
