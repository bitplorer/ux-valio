# SPDX-License-Identifier: MIT
"""SaaS portal identity (slug, country, timezone, ULID). Parallel to contact.

Does not import sibling named domain modules. Depends on typed
(or the validate door). Public names still re-export from
``ux_valio`` / ``ux_valio.facades.named``.
"""

from __future__ import annotations

import re
from typing import Any
from ux_valio.facades.typed import StringValidator
from zoneinfo import available_timezones

_SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


class SlugValidator(StringValidator):
    """Product / tenant / page slug.

    Usage::

        slug: str = SlugValidator()

    Stores lowercase. ``Hello-World`` → ``hello-world``. Spaces and
    underscores are rejected — hang ``pre_validate`` to slugify. No
    uniqueness lookup.
    """

    @staticmethod
    def _is_valid_slug(value: Any) -> bool:
        return isinstance(value, str) and _SLUG.fullmatch(value) is not None

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip().lower()
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_slug(value):
            raise ValueError(f"{self.name} is not a valid slug")

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

_ZONES = available_timezones()


class TimezoneValidator(StringValidator):
    """IANA tz database key (``Asia/Kolkata``, ``UTC``).

    Usage::

        tz: str = TimezoneValidator()

    Stores the key as given (case-sensitive). ``available_timezones()``
    membership — not offsets like ``+05:30``. No geo lookup.
    """

    @staticmethod
    def _is_valid_timezone(value: Any) -> bool:
        return isinstance(value, str) and value in _ZONES

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_timezone(value):
            raise ValueError(f"{self.name} is not a valid IANA timezone")

_ULID = re.compile(r"[0-7][0-9A-HJKMNP-TV-Z]{25}")


class ULIDValidator(StringValidator):
    """ULID public id (26 chars). Complements ``UUIDValidator``.

    Usage::

        public_id: str = ULIDValidator()

    Stores uppercase. ``I`` / ``L`` / ``O`` / ``U`` rejected. No
    timestamp-range check beyond the first-char 0–7 rule.
    """

    @staticmethod
    def _is_valid_ulid(value: Any) -> bool:
        return isinstance(value, str) and _ULID.fullmatch(value) is not None

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(value.split()).upper()
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_ulid(value):
            raise ValueError(f"{self.name} is not a valid ULID")


# ISO 639-1 alpha-2 (living + common). Region is ISO 3166-1 via CountryCode.
_LANGUAGES = frozenset(
    """
    aa ab ae af ak am an ar as av ay az ba be bg bh bi bm bn bo br bs ca ce
    ch co cr cs cu cv cy da de dv dz ee el en eo es et eu fa ff fi fj fo fr
    fy ga gd gl gn gu gv ha he hi ho hr ht hu hy hz ia id ie ig ii ik io is
    it iu ja jv ka kg ki kj kk kl km kn ko kr ks ku kv kw ky la lb lg li ln
    lo lt lu lv mg mh mi mk ml mn mr ms mt my na nb nd ne ng nl nn no nr nv
    ny oc oj om or os pa pi pl ps pt qu rm rn ro ru rw sa sc sd se sg si sk
    sl sm sn so sq sr ss st su sv sw ta te tg th ti tk tl tn to tr ts tt tw
    ty ug uk ur uz ve vi vo wa wo xh yi yo za zh zu
    """.split()
)
_LOCALE = re.compile(r"[a-z]{2}(?:-[A-Z]{2})?")
_SEMVER = re.compile(
    r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?"
)


class LocaleValidator(StringValidator):
    """BCP 47 language (``hi``) or language-region (``en-IN``).

    Usage::

        locale: str = LocaleValidator()

    Language is ISO 639-1; region is ISO 3166-1 alpha-2. Stores
    ``ll`` or ``ll-RR``. No CLDR lookup.
    """

    @staticmethod
    def _is_valid_locale(value: Any) -> bool:
        if not isinstance(value, str) or _LOCALE.fullmatch(value) is None:
            return False
        language, _, region = value.partition("-")
        if language not in _LANGUAGES:
            return False
        if region:
            return CountryCodeValidator._is_valid_country(region)
        return True

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip().replace("_", "-")
            parts = value.split("-", 1)
            language = parts[0].lower()
            if len(parts) == 2:
                value = f"{language}-{parts[1].upper()}"
            else:
                value = language
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_locale(value):
            raise ValueError(f"{self.name} is not a valid locale")


class SemVerValidator(StringValidator):
    """Semantic version: ``MAJOR.MINOR.PATCH`` (+ optional pre/build).

    Usage::

        version: str = SemVerValidator()

    ``1.2.3``, ``1.0.0-rc.1``. Leading zeros rejected. No registry.
    """

    @staticmethod
    def _is_valid_semver(value: Any) -> bool:
        return isinstance(value, str) and _SEMVER.fullmatch(value) is not None

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_semver(value):
            raise ValueError(f"{self.name} is not a valid semantic version")
