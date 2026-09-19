# SPDX-License-Identifier: MIT
"""Money, securities, cards, ISO currency. Parallel to india/catalog.

Does not import sibling named domain modules. Depends on typed
(or the validate door). Public names still re-export from
``ux_valio`` / ``ux_valio.facades.named``.
"""

from __future__ import annotations

import re
from typing import Any
from ux_valio.facades.typed import StringValidator

_IBAN = re.compile(r"[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}")


class IBANValidator(StringValidator):
    """IBAN: ISO 13616, length 15–34 ∩ rearrange-and-mod-97 == 1.

    Usage::

        iban: str = IBANValidator()

    Print groups (``GB82 WEST …``) strip; stores uppercase compact.
    Format-only is rejected. No bank lookup. Pair with ``BICValidator``.
    """

    @staticmethod
    def _mod97(text: str) -> bool:
        rearranged = text[4:] + text[:4]
        digits = "".join(
            str(ord(char) - 55) if char.isalpha() else char for char in rearranged
        )
        return int(digits) % 97 == 1

    @staticmethod
    def _is_valid_iban(value: Any) -> bool:
        if not isinstance(value, str) or not (15 <= len(value) <= 34):
            return False
        if _IBAN.fullmatch(value) is None:
            return False
        return IBANValidator._mod97(value)

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(value.split()).upper()
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_iban(value):
            raise ValueError(f"{self.name} is not a valid IBAN")

_BIC = re.compile(r"[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}(?:[A-Z0-9]{3})?")


class BICValidator(StringValidator):
    """SWIFT/BIC bank identifier (ISO 9362).

    Usage::

        swift: str = BICValidator()

    8 characters (``DEUTDEFF``) or 11 (``DEUTDEFF500``). Spaces/hyphens
    strip; stores uppercase. No SWIFT directory. Pair with ``IBANValidator``.
    """

    @staticmethod
    def _is_valid_bic(value: Any) -> bool:
        return isinstance(value, str) and _BIC.fullmatch(value) is not None

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(value.split()).replace("-", "").upper()
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_bic(value):
            raise ValueError(f"{self.name} is not a valid BIC")

_ISIN = re.compile(r"[A-Z]{2}[A-Z0-9]{9}[0-9]")


class ISINValidator(StringValidator):
    """ISIN: ISO 6166, 12 chars ∩ Luhn after A=10…Z=35 expansion.

    Usage::

        isin: str = ISINValidator()

    Print groups strip; stores uppercase compact (``US0378331005``).
    Format-only is rejected. No exchange lookup.
    """

    @staticmethod
    def _luhn_check_digit(body: str) -> str:
        expanded = []
        for char in body:
            if char.isdigit():
                expanded.append(char)
            else:
                expanded.append(str(ord(char) - 55))
        digits = "".join(expanded)
        total = 0
        for index, char in enumerate(reversed(digits)):
            number = int(char)
            if index % 2 == 0:
                number *= 2
                number = number // 10 + number % 10
            total += number
        return str((10 - total % 10) % 10)

    @staticmethod
    def _is_valid_isin(value: Any) -> bool:
        if not isinstance(value, str) or _ISIN.fullmatch(value) is None:
            return False
        return ISINValidator._luhn_check_digit(value[:11]) == value[11]

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(value.split()).replace("-", "").upper()
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_isin(value):
            raise ValueError(f"{self.name} is not a valid ISIN")

_LEI = re.compile(r"[A-Z0-9]{18}[0-9]{2}")


class LEIValidator(StringValidator):
    """Legal Entity Identifier: 20 chars ∩ ISO 17442 mod-97.

    Usage::

        lei: str = LEIValidator()

    Spaces/hyphens strip; stores uppercase. Format-only is rejected.
    No GLEIF lookup.
    """

    @staticmethod
    def _mod97(text: str) -> bool:
        digits = "".join(
            str(ord(char) - 55) if char.isalpha() else char for char in text
        )
        return int(digits) % 97 == 1

    @staticmethod
    def _is_valid_lei(value: Any) -> bool:
        if not isinstance(value, str) or _LEI.fullmatch(value) is None:
            return False
        return LEIValidator._mod97(value)

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(value.split()).replace("-", "").upper()
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_lei(value):
            raise ValueError(f"{self.name} is not a valid LEI")

_WEIGHTS = (3, 7, 1, 3, 7, 1, 3, 7, 1)


class ABARoutingValidator(StringValidator):
    """US ABA routing number. Complements ``IFSCValidator``.

    Usage::

        routing: str = ABARoutingValidator()

    Non-digits strip; stores 9 digits. Format-only is rejected. No Fed
    directory lookup.
    """

    @staticmethod
    def _is_valid_aba(value: Any) -> bool:
        if not isinstance(value, str) or len(value) != 9 or not value.isdigit():
            return False
        total = sum(int(char) * weight for char, weight in zip(value, _WEIGHTS))
        return total % 10 == 0

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(char for char in value if char.isdigit())
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_aba(value):
            raise ValueError(f"{self.name} is not a valid ABA routing number")

_VISA = re.compile(r"4[0-9]{12}(?:[0-9]{3})?")
_MASTERCARD = re.compile(
    r"(?:5[1-5][0-9]{14}|222[1-9][0-9]{12}|22[3-9][0-9]{13}|2[3-6][0-9]{14}|27[01][0-9]{13}|2720[0-9]{12})"
)
_AMEX = re.compile(r"3[47][0-9]{13}")
_DISCOVER = re.compile(r"(?:6011|644[0-9]|65[0-9]{2})[0-9]{12}")
_RUPAY = re.compile(r"6(?!(?:011|44[0-9]|5[0-9]{2}))0[0-9]{14}")


class PaymentCardValidator(StringValidator):
    """Visa / Mastercard / Amex / Discover / Rupay ∩ Luhn.

    Usage::

        number: str = PaymentCardValidator()

    Print grouping spaces/hyphens strip; stores compact digits. A
    Luhn-valid non-brand number is rejected. No network / BIN lookup.
    """

    @staticmethod
    def _luhn_correctness(card_number: str) -> bool:
        if not card_number.isdigit():
            return False
        digits = list(card_number)
        digits.reverse()
        total = 0
        odd = True
        for digit in digits:
            n = int(digit)
            if odd := not odd:
                n *= 2
                if n > 9:
                    n -= 9
            total += n
        return total % 10 == 0

    @staticmethod
    def _is_card_of(pattern: re.Pattern[str], card_number: str) -> bool:
        return (
            PaymentCardValidator._luhn_correctness(card_number)
            and pattern.fullmatch(card_number) is not None
        )

    @staticmethod
    def _is_valid_payment_card(card_number: str) -> bool:
        """True only when Luhn holds **and** the number matches a known brand."""
        if not isinstance(card_number, str):
            return False
        is_card = PaymentCardValidator._is_card_of
        return (
            is_card(_VISA, card_number)
            or is_card(_MASTERCARD, card_number)
            or is_card(_AMEX, card_number)
            or is_card(_DISCOVER, card_number)
            or is_card(_RUPAY, card_number)
        )

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        """Printed cards group digits. Store the compact brand∩Luhn identity."""
        if isinstance(value, str):
            value = "".join(value.split()).replace("-", "")
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        self._validate_payment_card(instance, value)

    def _validate_payment_card(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_payment_card(value):
            raise ValueError(f"{self.name} is not a valid payment card number")

_MMYY = re.compile(r"(0[1-9]|1[0-2])[0-9]{2}")


class CardExpiryValidator(StringValidator):
    """Payment-card month/year as printed. Stores ``MMYY``.

    Usage::

        exp: str = CardExpiryValidator()

    Accepts ``12/25``, ``12-25``, ``1225``. Does **not** reject a past
    month — hang ``ExpiryValidator`` / a ``pre_validate`` for that.
    ``expire_*`` stay on ``ExpiryValidator``, not here.
    """

    @staticmethod
    def _is_valid_card_expiry(value: Any) -> bool:
        return isinstance(value, str) and _MMYY.fullmatch(value) is not None

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(char for char in value if char.isdigit())
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_card_expiry(value):
            raise ValueError(f"{self.name} is not a valid card expiry (MMYY)")

_CURRENCIES = frozenset(
    """
    AED AFN ALL AMD ANG AOA ARS AUD AWG AZN BAM BBD BDT BGN BHD BIF BMD
    BND BOB BOV BRL BSD BTN BWP BYN BZD CAD CDF CHE CHF CHW CLF CLP CNY
    COP COU CRC CUP CVE CZK DJF DKK DOP DZD EGP ERN ETB EUR FJD FKP GBP
    GEL GHS GIP GMD GNF GTQ GYD HKD HNL HTG HUF IDR ILS INR IQD IRR ISK
    JMD JOD JPY KES KGS KHR KMF KPW KRW KWD KYD KZT LAK LBP LKR LRD LSL
    LYD MAD MDL MGA MKD MMK MNT MOP MRU MUR MVR MWK MXN MXV MYR MZN NAD
    NGN NIO NOK NPR NZD OMR PAB PEN PGK PHP PKR PLN PYG QAR RON RSD RUB
    RWF SAR SBD SCR SDG SEK SGD SHP SLE SOS SRD SSP STN SVC SYP SZL THB
    TJS TMT TND TOP TRY TTD TWD TZS UAH UGX USD USN UYI UYU UYW UZS VED
    VES VND VUV WST XAF XAG XAU XBA XBB XBC XBD XCD XDR XOF XPD XPF XPT
    XSU XTS XUA XXX YER ZAR ZMW ZWG
    """.split()
)


class CurrencyCodeValidator(StringValidator):
    """ISO 4217 alpha (``INR``, ``USD``). Stores uppercase.

    Usage::

        currency: str = CurrencyCodeValidator()

    ``inr`` → ``INR``. Not a symbol (``₹``) and not numeric (``356``).
    No FX lookup.
    """

    @staticmethod
    def _is_valid_currency(value: Any) -> bool:
        return isinstance(value, str) and value in _CURRENCIES

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip().upper()
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_currency(value):
            raise ValueError(f"{self.name} is not a valid ISO 4217 currency code")
