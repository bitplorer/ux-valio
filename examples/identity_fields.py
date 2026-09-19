# SPDX-License-Identifier: MIT
"""Named identity facades as field defaults. Compact store, no portal.

Copy the dataclass. Production uniqueness / registry lookup stays in a
port (see ``indian_kyc.py``) — these facades only prove the identity
string. ``help(GSTINValidator)`` is the per-type contract.
"""

from dataclasses import dataclass

from ux_valio import (
    BICValidator,
    CINValidator,
    DINValidator,
    EANValidator,
    FSSAIValidator,
    GSTINValidator,
    IBANValidator,
    ISBNValidator,
    ISINValidator,
    IndianPassportValidator,
    LLPINValidator,
    MACAddressValidator,
    TANValidator,
    UdyamValidator,
    VINValidator,
    VoterIdValidator,
)


@dataclass
class Counterparty:
    gstin: str = GSTINValidator()
    tan: str = TANValidator()
    cin: str = CINValidator()
    din: str = DINValidator()
    llpin: str = LLPINValidator()
    udyam: str = UdyamValidator()
    fssai: str = FSSAIValidator()
    epic: str = VoterIdValidator()
    passport: str = IndianPassportValidator()
    iban: str = IBANValidator()
    bic: str = BICValidator()
    isin: str = ISINValidator()
    isbn: str = ISBNValidator()
    ean: str = EANValidator()
    vin: str = VINValidator()
    mac: str = MACAddressValidator()


def main() -> None:
    row = Counterparty(
        gstin="09 AAAPA1111F 1Z P",
        tan="dela12345a",
        cin="u12345mh2000ptc123456",
        din="00123456",
        llpin="aab-1234",
        udyam="udyam-mh-00-0000001",
        fssai="10012345678901",
        epic="abc1234567",
        passport="a1234567",
        iban="GB82 WEST 1234 5698 7654 32",
        bic="deutdeff",
        isin="us 0378331005",
        isbn="978-0-306-40615-7",
        ean="4006381333931",
        vin="1HGCM82633A004352",
        mac="aa:bb:cc:dd:ee:ff",
    )
    print(row.gstin, row.iban, row.bic, row.isbn, row.mac)


if __name__ == "__main__":
    main()
