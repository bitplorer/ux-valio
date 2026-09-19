# SPDX-License-Identifier: MIT
"""ISO 4217 alpha currency.

Sibling of the other ``finance`` layers — does not import them.
Depends on typed. Public names re-export from ``ux_valio`` /
``ux_valio.facades.named.finance``.
"""

from __future__ import annotations

from typing import Any

from ux_valio.facades.typed import StringValidator

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
