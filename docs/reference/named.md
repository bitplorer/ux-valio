# Named identity facades

Same field-default pattern as `StringValidator`. Use a named facade when
the string **is** an identity in the world (a GSTIN, an IBAN, a card
number), not free text. Print grouping strips; the **stored value is the
compact identity**. `None` skips. Stdlib only — no portal, no DNS, no
BIN lookup. `help(GSTINValidator)` is the per-facade contract.

**Where:** KYC forms, vendor onboarding, checkout, storefront publish,
device inventory. Copy-paste: `examples/kyc.py`, `examples/vendor.py`,
`examples/checkout.py`.

Source lives in sibling domain modules under `facades/named/`
(`india/` `{kyc,gst,registry,bank,postal}`, `us/` `{postal,bank,market,kyc}`,
`uk/` `{postal,bank,kyc}`, `canada/` `{postal,kyc}`, `mexico/` `{bank,kyc}`,
`finance/` `{rail,market,card,currency}` — ISO/international only,
`catalog`, `contact`, `device`, `portal`, `expiry`) —
`from ux_valio.facades.named.india.gst import GSTINValidator` is
navigation; the taught import is still `from ux_valio import GSTINValidator`.
`named.us.postal` and `named.uk.postal` are the ZIP / postcode modules.

They run that extra from `validate()` after the inherited path. They do
not register that check with `validator` on each assignment. That extra
check joins collected errors (`collect_all=False` restores fail-fast).

```python
from dataclasses import dataclass
from ux_valio import BICValidator, GSTINValidator, IBANValidator, ISBNValidator

@dataclass
class Counterparty:
    gstin: str = GSTINValidator()
    iban: str = IBANValidator()
    bic: str = BICValidator()
    isbn: str = ISBNValidator()
```

`Counterparty(gstin="09 AAAPA1111F 1Z P", iban="GB82 WEST 1234 5698 7654 32", …)`
stores compact forms. A Luhn/mod-97 miss raises `ValueError` before any
hang you add.

## How to pick one

| I am collecting… | facade | example |
|---|---|---|
| Indian tax / KYC | `AadhaarCardValidator`, `PANCardValidator`, `GSTINValidator` | `examples/kyc.py` |
| Indian bank rails | `IFSCValidator`, `UPIIdValidator` | payout form |
| US / UK / CA / MX address or tax | ZIP, NINO, SIN, RFC, CLABE | shipping / W-8 |
| International pay-in | `IBANValidator`, `BICValidator`, `PaymentCardValidator` | `examples/checkout.py` |
| Catalog codes | `ISBNValidator`, `GTINValidator`, `EANValidator` | `examples/storefront.py` |
| Login / contact | `EmailValidator`, `PhoneNumberValidator`, `HostnameValidator` | `examples/signup.py` |

Uniqueness (“is this Aadhaar already registered?”) is **not** in the
facade. Hang `post_validate` on a port, same as username.

## India

| facade | stores | identity |
|---|---|---|
| `AadhaarCardValidator` | 12 digits | Verhoeff; first digit 2–9 |
| `PANCardValidator` | 10 A–Z/digits | Luhn mod 26 |
| `GSTINValidator` | 15 A–Z/digits | Luhn mod 36, state 01–38 / 97 / 99 |
| `TANValidator` | 10 chars | ITD format |
| `CINValidator` | 21 chars | MCA `L`/`U` + ROC + state + year |
| `DINValidator` | 8 digits | MCA director id; leading zeros stay |
| `LLPINValidator` | 7 chars | MCA `AAA1234` |
| `UdyamValidator` | `UDYAM-XX-00-0000000` | MSME registration |
| `FSSAIValidator` | 14 digits | licence `1` / registration `2` |
| `VoterIdValidator` | 3 letters + 7 digits | EPIC |
| `IndianPassportValidator` | 1 letter + 7 digits | MEA passport number |
| `IFSCValidator` | 11 chars | `ABCD0XXXXXX` |
| `PinCodeValidator` | 6 digits | India Post, first 1–9 |
| `IndiaStateCodeValidator` | 2 letters | Udyam/RTO (``CG`` not ISO ``CT``) |
| `UPIIdValidator` | lowercase VPA | `local@handle` |
| `HSNCodeValidator` | 4, 6, or 8 digits | GST HSN/SAC |

## US / UK / Canada / Mexico

| facade | stores | identity |
|---|---|---|
| `USZipCodeValidator` | 5 or 9 digits | US ZIP / ZIP+4 |
| `USStateValidator` | 2 letters | USPS 50 + DC + AS/GU/MP/PR/VI |
| `SSNValidator` | 9 digits | SSA area/group/serial |
| `ITINValidator` | 9 digits | IRS ITIN (starts 9) |
| `EINValidator` | 9 digits | US EIN |
| `ABARoutingValidator` | 9 digits | ABA checksum |
| `CUSIPValidator` | 9 chars | US security check digit |
| `UKPostcodeValidator` | outward inward | Royal Mail |
| `UKSortCodeValidator` | 6 digits | UK sort code |
| `NINOValidator` | 9 chars | HMRC NINO |
| `CAPostalCodeValidator` | `A1A 1A1` | Canada Post |
| `CanadianSINValidator` | 9 digits | Luhn |
| `CLABEValidator` | 18 digits | Banxico check |
| `MexicoRFCValidator` | 12 or 13 | SAT check digit |

## Finance / catalog / contact / device / portal

| facade | stores | identity |
|---|---|---|
| `IBANValidator` | registry length | ISO 13616 length ∩ mod-97; check digits `02`–`98` |
| `BICValidator` | 8 or 11 A–Z/digits | ISO 9362 / SWIFT |
| `ISINValidator` | 12 chars | ISO 6166 ∩ Luhn |
| `LEIValidator` | 20 chars | ISO 17442 mod-97 |
| `PaymentCardValidator` | compact digits | brand ∩ Luhn (incl. UnionPay / JCB / Diners) |
| `CardExpiryValidator` | `MMYY` | card print form; not wall-clock |
| `CurrencyCodeValidator` | 3 letters | ISO 4217 |
| `ISBNValidator` | 10 or 13 | ISBN-10 mod 11 / ISBN-13 978\|979 |
| `EANValidator` | 13 digits | GS1 check |
| `GTINValidator` | 8/12/13/14 digits | GS1 (UPC-A / EAN-8 / GTIN-14) |
| `ISSNValidator` | 8 chars | mod-11, trailing X |
| `VINValidator` | 17 chars | ISO 3779 check digit, no I/O/Q |
| `EmailValidator` | lowercase | addr-spec **fullmatch** |
| `URLValidator` | given string | scheme + netloc |
| `HostnameValidator` | lowercase FQDN | RFC 1123; not a URL; not IPv4 |
| `PhoneNumberValidator` | given string | `region=` required; `phonenumbers` extra |
| `IMEIValidator` | 15 digits | Luhn |
| `MACAddressValidator` | 12 hex | 48-bit; colon/hyphen/Cisco ok |
| `SlugValidator` | lowercase `foo-bar` | does not slugify spaces |
| `CountryCodeValidator` | 2 letters | ISO 3166-1 alpha-2 |
| `TimezoneValidator` | IANA key | `zoneinfo.available_timezones()` |
| `ULIDValidator` | 26 chars | Crockford base32 |
| `LocaleValidator` | `en` / `en-IN` | ISO 639-1 + 3166-1 |
| `SemVerValidator` | `MAJOR.MINOR.PATCH` | SemVer 2 |
| `ExpiryValidator` | field's store type | exclusive `expire_*` wall-clock |

`PhoneNumberValidator` is a string facade. Pass `region="IN"` (required).
The extra is `pip install ux-valio[phonenumbers]`. Without it the
constructor still exists; assignment that needs the engine raises a
clear import error. KYC identity still runs in `examples/kyc.py`.

`ExpiryValidator(expire_before="2020-01-01")` — exactly one `expire_*`.
That is a **wall-clock** bound on whatever the field stores (a promo
code’s offer window), not card `MM/YY` (`CardExpiryValidator`).

