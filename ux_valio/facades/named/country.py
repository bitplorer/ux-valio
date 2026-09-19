# SPDX-License-Identifier: MIT
"""ISO 3166-1 alpha-2 country. Closed set, no OSM / geo lookup."""

from __future__ import annotations

from typing import Any

from ux_valio.facades.typed import StringValidator

# Officially assigned alpha-2 plus XK (user-assigned, widely used).
_COUNTRIES = frozenset(
    """
    AD AE AF AG AI AL AM AO AQ AR AS AT AU AW AX AZ BA BB BD BE BF BG BH
    BI BJ BL BM BN BO BQ BR BS BT BV BW BY BZ CA CC CD CF CG CH CI CK CL
    CM CN CO CR CU CV CW CX CY CZ DE DJ DK DM DO DZ EC EE EG EH ER ES ET
    FI FJ FK FM FO FR GA GB GD GE GF GG GH GI GL GM GN GP GQ GR GS GT GU
    GW GY HK HM HN HR HT HU ID IE IL IM IN IO IQ IR IS IT JE JM JO JP KE
    KG KH KI KM KN KP KR KW KY KZ LA LB LC LI LK LR LS LT LU LV LY MA MC
    MD ME MF MG MH MK ML MM MN MO MP MQ MR MS MT MU MV MW MX MY MZ NA NC
    NE NF NG NI NL NO NP NR NU NZ OM PA PE PF PG PH PK PL PM PN PR PS PT
    PW PY QA RE RO RS RU RW SA SB SC SD SE SG SH SI SJ SK SL SM SN SO SR
    SS ST SV SX SY SZ TC TD TF TG TH TJ TK TL TM TN TO TR TT TV TW TZ UA
    UG UM US UY UZ VA VC VE VG VI VN VU WF WS XK YE YT ZA ZM ZW
    """.split()
)


class CountryCodeValidator(StringValidator):
    """ISO 3166-1 alpha-2 (``IN``, ``US``). Stores uppercase.

    Usage::

        country: str = CountryCodeValidator()

    ``in`` → ``IN``. Not a name (``India``) and not alpha-3 (``IND``).
    No geo lookup.
    """

    @staticmethod
    def _is_valid_country(value: Any) -> bool:
        return isinstance(value, str) and value in _COUNTRIES

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip().upper()
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_country(value):
            raise ValueError(f"{self.name} is not a valid ISO 3166-1 alpha-2 country code")
