# Soft 11-WIDEN CARTGRAPH — Door A missing leaves + Regexer / Pattern pack

**CARTGRAPH ONLY.** No product tip. No implementation. Soft-patch valio is **read-only**.

Council can ACCEPT Soft LOCK Soft 11-widen from this pack alone.

This pack does **not** implement, reopen, or steal Soft LOCK Soft 11 **DO-1..4** (postponed-annotation bind, AnyOf AND-gate, compose `collect_all`/`logger` sentinel, `ValidationPath.run` `ValueError`). That tip stays on [PR #12](https://github.com/bitplorer/ux-valio/pull/12) (`docs/soft11-parity-holes-pack.md`). Soft 11-widen is the **feature-parity** sibling Soft 11 already named as DEFER.

---

## Identity

| Item | Value |
| --- | --- |
| Target | [`bitplorer/ux-valio`](https://github.com/bitplorer/ux-valio) `main` |
| `git log -1` HEAD | **`8c37d7fb4c1813b5dca468f582c15c1e3b9157ef`** |
| Subject | `Soft 10: origin+args type door; fail-closed unknown (#11)` |
| Soft 10 claimed merge | **`8c37d7f`** — **verified equal to HEAD** |
| Frozen valio | [`bitplorer/valio@3415c03`](https://github.com/bitplorer/valio/commit/3415c03e37085adda4040671a91eb19aa4fe4ac4) `3415c03e37085adda4040671a91eb19aa4fe4ac4` |
| Valio subject | `Soft 10: compose full validation path; fail-closed units (#10)` — **PARKED; not edited** |
| Experiment Python | 3.12.3 |
| Package floor | `requires-python = ">=3.10"` (`pyproject.toml` L11) |
| Suite at HEAD | **229 collected / passed**, `tests/*.py` = 21 files (`python3 -m pytest tests`) |
| ux-valio barrel | `from ux_valio import *` **40** names; `__all__` **41** including `__version__` (`ux_valio/__init__.py` L52–94) |

HEAD check (this run):

```
8c37d7fb4c1813b5dca468f582c15c1e3b9157ef Soft 10: origin+args type door; fail-closed unknown (#11)
```

Human ask: Feature parity gaps — give ux-valio the validations valio had that are missing (Aadhaar called out; may be 2–4 more). Also complete Regexer / pattern side of valio that was not fully brought into ux-valio. Soft 11 already DEFERred Phone / collections / Aadhaar·PAN to Soft 11-widen.

Name honesty: Soft 6 forbids `docs/soft*.md` on product `main` (`tests/test_product_surface.py` L94–96). **Do not merge this draft onto `main` as a product commit.**

---

## 0. Soft 11 base vs Soft 11-widen (do not mix)

| Soft | Vehicle | Owns |
| --- | --- | --- |
| Soft LOCK Soft 11 | [PR #12](https://github.com/bitplorer/ux-valio/pull/12) pack §4 | **DO-1..4** (and cheap P2 DO-5..7): harden **existing** doors. No new public validator names. |
| Soft LOCK Soft 11-widen | **this pack** | Missing **Door A happy-path validation leaves** + **one Pattern door** (not a second regex product). |

Soft 11 pack §4.5 already parked the widen bucket ([PR #12](https://github.com/bitplorer/ux-valio/pull/12) `docs/soft11-parity-holes-pack.md` L444–456):

| Item | Soft 11 status | This pack |
| --- | --- | --- |
| Phone | **DEFER** — valio `validators.py` L2230; ux `hasattr` False; README L173 | **confirm DEFER** (§1.3, §3.5) |
| Collections (`List`/`Dict`/`Set`/`Tuple`/`Mapping`/`Sequence`) | **DEFER** — valio L2424–2444; `tests/test_product_surface.py` L48–49 | **KEEP-absent** (annotation aliases; Soft 10 type door owns element honesty) |
| Aadhaar / PAN | **DEFER** (named with Phone) — valio L2360, L2392 | **DO** Door A facades (§3.1) |
| pyparsing + compose #30 regexer stack | **HOLD** | **HOLD** / **DEAD** scanString; Pattern `&`/`\|` KEEP; no `ux_valio/regexer/` package |

**MUST NOT in a Soft 11-widen product tip:** Cap / Field / Schema / public `check_*` / Soft ceremony on the product tree / Soft-patch valio / unpark typingx / implement Soft 11 DO-1..4.

---

## 1. Missing Door A validators (valio@3415c03 → ux-valio HEAD `8c37d7f`)

Legend:

| Mark | Meaning |
| --- | --- |
| **COVERED** | Door A analogue exists (name may differ) |
| **PARTIAL** | Same role, different contract (product KEEP unless a row reopens it) |
| **MISSING** | valio Door A extra-check leaf; no ux analogue |
| **KEEP-absent** | Named absence is the lock (do not ship) |
| **DEFER** | Real leaf; not this Soft |
| **HOLD** | Council park (dual-schema / typingx / Field / Schema) |
| **RETIRED-named** | valio had it; ux documents the retirement |
| **EXTRA** | ux-only; may stay |

Door A = `field: T = SomeValidator(...)`. Field twins (`*Field`) and Schema are **HOLD**, not MISSING Door A leaves. Dual-schema aliases (`INT = Union[int, V]`, `LIST = Union[list, V]`, …) are **HOLD** (`validators.py` L329–355).

### 1.1 Every public `*Validator` in valio `validators.__all__`

Source: `/tmp/valio/valio/validator/validators.py` L71–125. ux evidence: `ux_valio/__init__.py` L52–94; measured `hasattr` this run.

| valio name | valio def | ux-valio HEAD | Mark | Soft |
| --- | --- | --- | --- | --- |
| `ValidateProperty` | L171 | COVERED `validators/base.py` | COVERED | 1 |
| `TypeValidator` | L359 | COVERED `leaves.py`; unexported `is_instance_of` | COVERED | 1 / 10 |
| `RequiredValidator` | L417 | COVERED | COVERED | 1 |
| `PatternValidator` | L461, findall L506–508 | COVERED `leaves.py` L151–166 findall L164 | COVERED | 1 |
| `ReassignValidator` | L516 | COVERED | COVERED | 1 |
| `MultipleValidator` | L570 | COVERED | COVERED | 1 |
| `ValueValidator` | L984 | COVERED | COVERED | 1 |
| `LengthValidator` | L1173 | COVERED | COVERED | 1 |
| `ExpiryValidator` | L1265; also fat-`Validator` kwargs L1688–1690 | COVERED as **facade only**; `expire_*` not on `Validator`; no `"expiry"` path unit `path.py` L21–30 | COVERED (Soft 8 KEEP) | 8 |
| `ChoiceValidator` | L1347 | COVERED | COVERED | 1 |
| `TaskValidator` | L1476 | Hook bags only; no class | RETIRED-named | 5 |
| `Validator` | L1581 | COVERED `facade.py` L29 | COVERED | 1 |
| `IntegerValidator` | L1971 | COVERED `facade.py` | COVERED | 1 |
| `FloatValidator` | L1979 | COVERED `typed.py` L32–33 | COVERED | 6 |
| `DecimalValidator` | L1987 | COVERED `typed.py` L36–37 | COVERED | 6 |
| `BooleanValidator` | L1995 | COVERED | COVERED | 1 |
| `BytesValidator` | L1999 | COVERED `typed.py` L40–41 | COVERED | 6 |
| `StringValidator` | L2006 | COVERED | COVERED | 1 |
| `HexShortColorValidator` | L2030 | `hasattr` False; `typed.py` L2; `tests/test_product_surface.py` L71–74 | KEEP-absent | 6 / AGENTS L38 |
| `HexLongColorValidator` | L2041 | same | KEEP-absent | 6 |
| `HexColorValidator` | L2052 | same; valio named-once canary `test_named_validate_once.py` — ux canary is PaymentCard/Expiry `tests/test_named_validate_once.py` L13–38 | KEEP-absent | 8 |
| `RGBOrRGBAColorValidator` | L2063, **crash** L2070 `relib.r_rbga` (name is `r_rgba` `colors.py` L15, L54) | `hasattr` False; AGENTS L7; README L179 | KEEP-absent (retired for crash) | 6 |
| `HSLOrHSLAColorValidator` | L2075, **crash** L2082 compiles `r_rgb \| r_rbga` not `r_hsl \| r_hsla` | same | KEEP-absent (retired for crash) | 6 |
| `DateValidator` | L2087–2149 eu/ind **string** patterns + findall | PARTIAL: `datetime.date` only; strings rejected `typed.py` L44–47; `tests/test_typed_facades.py` `test_date_validator_accepts_date_not_string` | PARTIAL KEEP | 6 |
| `PathValidator` | L2268–2308 | PARTIAL: annotation `pathlib.Path`; coerce str; `path_exists=` opt-in `typed.py` L67–89 | PARTIAL KEEP | 6 |
| `EmailIDValidator` | L2169–2190 `pattern=relib.email_pattern` | COVERED as `EmailValidator` (rename); Pattern findall KEEP `typed.py` L17–29, L50–52 | COVERED | 6 |
| `PaymentCardValidator` | L2194–2226 `relib.is_valid_payment_card` | COVERED stdlib `re` brand ∩ Luhn `payment.py` L41–50; Luhn-only rejected `tests/test_payment_card.py` L24–28 | COVERED (Soft 8 KEEP) | 8 |
| `PhoneNumberValidator` | L2230–2265 `phonenumbers.PhoneNumberMatcher`; `getattr(instance, "region", "IN")` L2260–2261 | `hasattr` False; README L173 | **DEFER** | 6 named / 11-widen confirm |
| `AadhaarCardValidator` | L2360–2389 `relib.is_valid_aadhaar_card`; README L27, L40 | `hasattr` False; **zero** product-tree hits | **MISSING → DO-W1** | 11-widen |
| `PANCardValidator` | L2392–2421 `relib.is_valid_pan_number`; **no** `PANCardField` | `hasattr` False; **zero** product-tree hits | **MISSING → DO-W2** | 11-widen |
| `IP4AddressValidator` | L2311 | COVERED as `IPv4Validator` `typed.py` L92–102 | COVERED | 6 |
| `IP6AddressValidator` | L2326 | COVERED as `IPv6Validator` | COVERED | 6 |
| `IPAnyAddressValidator` | L2341 | COVERED as `IPAddressValidator` | COVERED | 6 |
| `SequenceValidator` | L2428 `annotation = typing.Sequence` | `hasattr` False | KEEP-absent | 10 type door |
| `MappingValidator` | L2424 `annotation = typing.Mapping` | `hasattr` False | KEEP-absent | 10 type door |
| `ListValidator` | L2432 `annotation = LIST` (`LIST = Union[list, V]` L348) | `hasattr` False; **lock** `tests/test_product_surface.py` L48–49 | KEEP-absent | 6 / 10 |
| `DictionaryValidator` | L2436 `annotation = DICT` | `hasattr` False | KEEP-absent | 10 type door |
| `SetValidator` | L2440 `annotation = SET` | `hasattr` False | KEEP-absent | 10 type door |
| `TupleValidator` | L2444 `annotation = TUPLE` | `hasattr` False | KEEP-absent | 10 type door |
| `UUIDValidator` | L2164 | COVERED + EXTRA string coerce on descriptor path `typed.py` L55–64 | COVERED | 6 |
| `EnumValidator` / `IntegerEnumValidator` / `StringEnumValidator` | L2152–2160 | COVERED `typed.py` L131–163 | COVERED | 6 |
| `INT` / `FLOAT` / `STR` / `PATTERN` / … aliases | L329–355 | not invented | HOLD dual-schema | Soft 2 |

**Defined in valio, not in `validators.__all__`:**

| Name | valio | ux-valio | Mark |
| --- | --- | --- | --- |
| `MinValueValidator` / `MaxValueValidator` | L868, L915 | COVERED **and exported** | EXTRA public building block (Soft 6) |
| `MinLengthValidator` / `MaxLengthValidator` | L1076, L1124 | COVERED **and exported** | EXTRA (Soft 6) |
| `AttributeValidator` | L1432–1472; path `"attribute"`; **not** in barrel | `hasattr` False; AGENTS L29–30; `ux_valio/__init__.py` L5–6; `tests/test_typed_facades.py` L181–183 | KEEP-absent |

**Field twins** (`field/fields.py` `__all__` L20–42): `Field`, `IntegerField`, … `AadhaarCardField` L793, `PaymentCardField`, `PhoneNumberField` — **HOLD** Door B. **No** `PANCardField`. Not Door A MISSING.

### 1.2 Explicit hunt (human list)

| Name | valio@3415c03 | ux-valio HEAD `8c37d7f` | Mark |
| --- | --- | --- | --- |
| **Aadhaar** | `AadhaarCardValidator` L2360; helper `regexer/relib/aadhaarcard.py` L9–11, L22–40 (Verhoeff tables L13–19; no regex; `ValueError`/`IndexError` → False); README L27, L40 | no symbol, no docs hit | **MISSING → DO-W1** |
| **PAN** | `PANCardValidator` L2392; helper `regexer/relib/pancard.py` L41, L115–117; docstring claims Luhn mod 26 L31–32; **`verify()` L89–112 is unused**; `is_valid_pan_number` is `re.findall` only L115–117 | no symbol | **MISSING → DO-W2** |
| **Phone** | `PhoneNumberValidator` L2230; `import phonenumbers as phn` L64; Matcher L2262; default region `"IN"` L2260–2261; `PhoneNumberField` `fields.py` L857; dep `pyproject.toml` L10 | README L173 “not shipped”; `hasattr` False | **DEFER** |
| **GSTIN** | **ABSENT** — repo-wide grep 0 hits under `/tmp/valio` | 0 hits | KEEP-absent (never in valio — do not invent) |
| **IFSC** | **ABSENT** | 0 hits | KEEP-absent |
| **Voter ID** | **ABSENT** | 0 hits | KEEP-absent |
| **Passport** | **ABSENT** | 0 hits | KEEP-absent |
| **Driving licence** | **ABSENT** | 0 hits | KEEP-absent |
| **Collections** | `ListValidator` etc. L2424–2444 — **type annotation only**, no element `validate()` | README L173; `ListValidator` absence lock L48–49; Soft 10 walks `list[T]` / `dict[K,V]` / `tuple` arity via `is_instance_of` | KEEP-absent |
| **AttributeValidator** | L1432; not exported | AGENTS L29–30; test L181–183 | KEEP-absent |
| **HexColor / RGB / HSL** | barrel L90–94; RGB/HSL **AttributeError** on `relib.r_rbga` L2070, L2082 | README L179–180; AGENTS L7, L38; product-surface L71–74 | KEEP-absent (RGB/HSL retired for crash — **confirmed**) |
| **PaymentCard / Expiry** | L2194, L1265 | `payment.py`; `expiry.py` L40–48 exclusive kwargs; named-once tests | **COVERED Soft 8 KEEP** |

**Human “Aadhaar + 2–4 more” measured:** valio Door A leaves with an **extra `validate()` check** and **no** ux analogue are exactly three: **Aadhaar, PAN, Phone**. GSTIN / IFSC / Voter / Passport / DL were never in valio. Collections have no extra check. Colors are crash-retired. That is Aadhaar + two more (PAN DO, Phone DEFER).

### 1.3 MISSING Door A happy-path leaves — proposed widen rows

Only extra-check leaves (not Field/Schema/Cap, not annotation aliases).

#### DO-W1 — `AadhaarCardValidator`

**Intent:** valio README teaches Door A `aadhaar: str = AadhaarCardValidator(...)` (`README.md` L27, L40). The leaf is `StringValidator` + Verhoeff checksum (`validators.py` L2360–2389 → `relib.is_valid_aadhaar_card` `aadhaarcard.py` L22–40). Stdlib-complete. No network (file comment L7 “verification api module” is leftover; implementation is tables + loop).

**Door A shape (Soft 8 named-once):**

```python
aadhaar: str = AadhaarCardValidator(debug=True)
```

- Subclass `StringValidator`.
- Extra check from `validate()` after `super()`; do **not** `add_validator` on each assign (`tests/test_named_validate_once.py` pattern; AGENTS L36–37).
- Inline Verhoeff helper next to the facade (like `payment.py` L20–51). **No** `ux_valio/regexer/` / relib package.
- Digits only; non-digit / bad length → reject (valio `ValueError`/`IndexError` → False).
- Identity of the assigned string, not `PatternValidator` findall.

#### DO-W2 — `PANCardValidator`

**Intent:** public valio leaf (`validators.py` L101, L2392–2421). Soft 8 PaymentCard honesty: brand ∩ Luhn; a generator is not enough (`AGENTS.md` L31–32; `tests/test_payment_card.py` L1–2, L24–28). valio PAN **claims** Luhn mod 26 (`pancard.py` L31–32) but `is_valid_pan_number` only `re.findall`s a 10-char token (`pancard.py` L115–117); `verify()` L89–112 is dead. Findall would accept a PAN as a **substring**. Named ID facades follow PaymentCard **identity** (`payment.py` L12–13 `fullmatch`), not the Pattern door’s findall KEEP.

**Door A shape:**

```python
pan: str = PANCardValidator(debug=True)
```

- Subclass `StringValidator` (valio uses bare `Validator` L2392; Door A typed-ID facades are `StringValidator` like PaymentCard `payment.py` L54).
- Pattern **fullmatch** of `[A-Z]{3}[ABCFGHLJPTK][A-Z][0-9]{4}[A-Z]` (valio `pancard.py` L116; fourth-char set includes **K** not listed in the docstring L11–20 — KEEP the regex set).
- **∩ Luhn mod 26** via a complete A–Z decoder. Do **not** copy `A_Z_MAP = dict(zip(A_Z, range(1, 26)))` (`pancard.py` L38–39): `range(1, 26)` is 25 values, **Z is dropped**.
- Named-once `validate()` extra check.
- Inline helper in the facade module (or `validators/pan.py` beside `payment.py`). No relib barrel.

#### Phone — not a DO this Soft

**Intent to DEFER (confirm Soft 11 §4.5):** the extra check is `phonenumbers.PhoneNumberMatcher` (`validators.py` L2262) plus `getattr(instance, "region", "IN")` (`L2260–2261`). That is three honesty cliffs:

1. **New runtime dep.** valio `pyproject.toml` L10 `phonenumbers`; ux-valio `pyproject.toml` has **no** runtime deps. pyparsing is already HOLD (`tests/test_product_surface.py` L77–91). phonenumbers is the same class of third-party engine.
2. **Matcher is a scan**, not identity — analogue of retired payment `scanString` (valio `CHANGELOG.md` L13 E13).
3. **`instance.region`** reads a sibling attribute — AttributeValidator-shaped; AttributeValidator is KEEP-absent (`AGENTS.md` L29–30).

A stdlib E.164 `fullmatch` would be a **different product**, not valio Phone. Do not ship a lying subset. Door A `region=` kwarg + phonenumbers is a later Soft if Council unparks that dep.

---

## 2. Regexer parity

### 2.1 valio `regexer/` @ 3415c03

Barrel: `valio/regexer/__init__.py` L6–7 `from .regexps import *` then `from .relib import *`. Relib barrel `relib/__init__.py` L6–15 star-imports aadhaar, colors, control_chars, dates, emails, ipaddresses, pancard, patterns, paymentcards, special_chars. Top-level `valio/__init__.py` L10 pulls the lot into the 306-name star import.

**`regexps.py` public combinators** (`__all__` L12–34):

| Name | Lines | Role |
| --- | --- | --- |
| `PatternType` | L37–102 | Base; `&` → `AND` L57–70; `\|` → `OR` L72–85; `__neg__` → `NOT` L87–88 |
| `Pattern` | L212–242 | Literal + quantifier |
| `All` / `Any` | L245–258 | N-ary `&` / `\|` |
| `SetOf` | L261–305 | `[...]`; `~` negate |
| `Escape` | L308–330 | `\` ; `__and__` on non-Escape calls `super().__or__` (bug) |
| Groups | L333–411 | capturing / non-capturing / named / comment |
| `StartsWith` / `EndsWith` | L414–425 | `^` / `$` **wrappers** |
| `StartOfString` / `EndOfString` | L428–439 | `\A` / `\Z` |
| **`WordBoundary`** | **L442–446** | **wrapper** `\b{inner}\b` — **requires** a `PatternType` |
| Lookaround / conditional | L449–490 | `(?<=)` `(?<!)` `(?=)` `(?!)` `(?(name)…\|…)` |

**NOT / crash:** `NOT` emits `!{pattern}` (`regexps.py` L136) — not valid Python `re`. KEEP-absent.

**Named libs (relib) — exhaustive; no GSTIN/IFSC/phone/passport/voter/DL modules:**

| Module | What | Engine at call site |
| --- | --- | --- |
| `aadhaarcard.py` | Verhoeff only L22–40 | Python ints; **no regex** |
| `pancard.py` | format + unused Luhn-mod-26 | `re.findall` L117 |
| `colors.py` | `r_hex_short/long`, `r_rgb/rgba`, `r_hsl/hsla` L11–18, L33–62 | compiled by color validators with **`fullmatch`** |
| `paymentcards.py` | brand `Pattern`s; Luhn; `is_valid_payment_card` L110–117; `PaymentCard.scanString` L136 | **pyparsing** `Regex.re_match` L85–107 |
| `emails.py` | `_email_regex` L9–18; `email_pattern`; `get_email` uses pyparsing L40–42 | PatternValidator findall via EmailID |
| `dates.py` | eu/ind mega-pattern; **`get_date` `scanString` L268, L274, L289** | pyparsing |
| `ipaddresses.py` | RFC3986 strings + `Pattern` wrappers L214–252; `path_empty = r""  # FIXME` L139 | `re.match` helpers L202–211 |
| `patterns.py` | `WhiteSpace` / `Digit` / lookaround facades; `a_z` L299–301 | string building |
| `control_chars.py` / `special_chars.py` | ASCII literals | string building |

**`scanString` live sites (not dead in valio; DEAD for ux-valio):** `dates.get_date` L268/274/289; `PaymentCard.__init__` L136; commented demo `dates.py` L345. E13 already stopped treating a Luhn-valid **generator** as a card (`CHANGELOG.md` L13). ux PaymentCard never used it (`payment.py` stdlib `re`).

**Tests:** `valio/regexer/tests/regex_test.py` — quantifier / `SetOf` / lookaround **string equality**, not Door A. No Aadhaar/PAN/color/email regexer tests. Payment/Expiry tests live under `valio/tests/validator/`.

**pyparsing vs stdlib:** dual-runtime. Pattern construction is strings; match is `re` *or* pyparsing depending on call site. ux-valio product tree **must not import pyparsing** (`tests/test_product_surface.py` L77–91).

### 2.2 ux-valio Pattern door today (HEAD `8c37d7f`)

One door. No `regexer/` package. Stdlib `re` only at the validator.

| Symbol | Path | Notes |
| --- | --- | --- |
| `PatternType` | `pattern.py` L15–54 | `&` concat L39–44; `\|` non-capturing alt L46–51; non-`PatternType` operand `TypeError` |
| `AndPattern` / `OrPattern` | L57–71 | |
| `Pattern` | L106–121 | `count` / `count_min` / `count_max` / `greedy` via `_quantifier` L74–103 |
| `WordBoundary` | L124–126 | **atom** `r"\b"` — **not** valio’s wrap constructor |
| Package export | `ux_valio/__init__.py` L10, L79–81, L92 | `Pattern`, `PatternType`, `WordBoundary` only — no `SetOf` / `StartsWith` / lookarounds (`hasattr` False this run) |
| `PatternValidator` | `leaves.py` L151–166 | `PatternType.pattern` or raw str; **`re.compile(source).findall` L164** KEEP |
| Facade path unit `"pattern"` | `path.py` L21–30; `facade.py` binds PatternValidator | |
| Email | `typed.py` L17–29, L50–52 | inlined RFC-ish `Pattern`; findall KEEP |
| Payment brands | `payment.py` L11–17, L37–38 | inlined stdlib `re` **fullmatch**, not PatternValidator findall |
| Honesty locks | `tests/test_pattern_findall.py` L14–99 | empty pattern; None skip; debug swallow; substring `"a string"` vs `\w+`; `&` concat `A\d{2}`; `\|` alt; `WordBoundary() & Pattern(r"hi") & WordBoundary()`; TypeError on `Pattern & "b"` |

**Named pattern libraries in ux-valio:** none. Callers compose `Pattern` fragments or pass a raw `str` into `PatternValidator`.

### 2.3 Gaps — LOCK (one Pattern door; no E14 second regex product)

| Gap | Mark | Why |
| --- | --- | --- |
| Pattern `&` / `\|` | **COVERED KEEP** | `pattern.py` L39–51; tests L55–81 |
| `findall` substring | **COVERED KEEP** | `leaves.py` L164; README L139; AGENTS L13 |
| `Pattern` quantifiers | **COVERED KEEP** | `pattern.py` L74–121; used in findall test L56 |
| `WordBoundary` wrap vs atom | **PARTIAL KEEP** | valio L442–446 wraps inner; ux L124–126 is `\b` atom; tests L84–92 lock **compose of three fragments**. Do not change the constructor (second shape). Named ID facades use `re.fullmatch`, not WordBoundary wrap. |
| `StartsWith` / `EndsWith` / `SetOf` / groups / lookarounds / `All` / `Any` / `NOT` | **HOLD / KEEP-absent** | Soft 6 / Soft 11 compose #30. Callers write `Pattern(r"^…")`. Porting the stack is a second regex product. |
| `__neg__` `!` prefix | **DEAD** | invalid `re` (`regexps.py` L87–88, L136) |
| `scanString` / pyparsing `Regex` | **DEAD** | E13; product-surface pyparsing lock |
| Color relib | **KEEP-absent** | RGB/HSL crash; HexColor not public |
| Date `get_date` / eu/ind scan | **KEEP-absent** | DateValidator PARTIAL KEEP `datetime.date` |
| Email relib module | **KEEP-absent** | already inlined on EmailValidator |
| Payment relib module | **KEEP-absent** | already inlined Soft 8 |
| IP RFC3986 relib | **KEEP-absent** | IP facades use stdlib `ipaddress` |
| aadhaar / pan **helpers** | **DO inline** | serve DO-W1/W2; not a public relib API |
| `ux_valio.regexer` package / star barrel | **DO NOT** | E14; 306-name barrel RETIRED |

**Harden existing Pattern door (no new public combinator names):**

- KEEP current combinators + findall + atom WordBoundary.
- Named facades that need identity match use stdlib `re.fullmatch` on the facade (PaymentCard precedent `payment.py` L12–13, L37–38), **not** a second Pattern product and **not** a change to `PatternValidator` findall.
- Do not add a compile cache (Soft 11 pack §2.4 already rejected it as fashion).

---

## 3. Soft LOCK Soft 11-widen (ACCEPT text)

Harden **one Door A** and **one Pattern door**. New public names only for the two stdlib-complete missing extra-check leaves. No Cap / `add_pre_set` / Field / Schema / typingx / pyparsing / phonenumbers / public `check_*` / Soft ceremony on the product tree. No product Soft tip in this cartograph run. Soft-patch valio stays PARKED @ `3415c03`. KEEP Soft 1–10. Soft 8 PaymentCard KEEP. Soft 11 **DO-1..4 stay a separate tip**.

### 3.1 DO

| ID | Change | Intent | Door |
| --- | --- | --- | --- |
| **DO-W1** | Public `AadhaarCardValidator` (`StringValidator` facade). Verhoeff checksum inlined. `validate()` → `super()` then extra check once. Export in package `__all__`. Named-once honesty test. | README-taught Door A leaf `validators.py` L2360–2389; `aadhaarcard.py` L22–40; README L40 | existing typed-facade door (Soft 8 named-once) |
| **DO-W2** | Public `PANCardValidator` (`StringValidator` facade). 10-char pattern **fullmatch** ∩ Luhn mod 26 (complete A–Z map; do not copy `zip` truncation `pancard.py` L38–39). `validate()` extra check once. Export in `__all__`. Named-once + generator-reject test (format-only must fail, analogue `tests/test_payment_card.py` L24–28). | valio leaf L2392–2421; docstring L31–32 vs unused `verify()` L89–112 vs findall L115–117; Soft 8 identity ∩ checksum | same |
| **DO-W3** | Inline those two helpers beside `payment.py` (or `validators/aadhaar.py` + `validators/pan.py`). **No** `regexer/` package, **no** public `is_valid_*` in package `__all__`. | one Pattern door; PaymentCard inlining KEEP | existing facade modules |

**Not DO this Soft:** Phone, collection facades, HexColor, RGB/HSL, AttributeValidator, GSTIN/IFSC/Voter/Passport/DL, compose #30 combinators, `scanString`, Date eu/ind parse, Soft 11 DO-1..4.

### 3.2 KEEP

- Soft 1 Door A bones; no `asyncio.run` in `__set__`; falsy defaults; debug-swallow; logger OFF; Pattern **`findall`**
- Soft 2 annotation conflict; postponed typed-facade TypeError
- Soft 3 no `add_pre_set`
- Soft 5 nest-safe async; `enable_async` unknown-kwarg; `cache_task` kwarg / cache RETIRE
- Soft 6 validators package; object compose; ceremony strip; `docs/soft*.md` not on product main
- Soft 7 compose-root hooks; `collect_all` default False; `Chain is AllOf`
- **Soft 8 PaymentCard brand ∩ Luhn; Expiry exclusive facade; named-once `validate()` extra check; HexColor not public**
- Soft 9 `module.qualname` bags
- Soft 10 origin+args `is_instance_of`; no public `check_instance`; collection **type** honesty on `list[T]` / `dict[K,V]` / `tuple`
- Pattern `&` / `\|`; atom `WordBoundary`; Pattern quantifiers
- DateValidator `datetime.date` (no string parse)
- Soft-patch valio PARKED @ `3415c03`
- Python ≥ 3.10; no runtime deps

### 3.3 DEAD

- Cap Host, `mount_channel`, Field twin, Schema twin, `rule/`, Result type
- `add_pre_set` / `_processors["pre_set"]`
- typingx / typing_extensions; public `check_*`
- Star-import 306-name barrel; `ux_valio.regexer` package
- pyparsing; `scanString`; payment `Regex.re_match`
- `NOT` `!` prefix combinator
- RGB/HSL facades (crash `r_rbga` L2070 / L2082)
- Dual-schema `INT = Union[int, Validator]`
- Soft ceremony tokens on the product tree
- Implementing Soft 11 DO-1..4 inside a widen tip

### 3.4 DO NOT

- Product Soft tip in this cartograph run; land this pack on `main`
- Soft-patch valio; unpark typingx
- Public `is_valid_aadhaar_card` / `is_valid_pan_number` as owned API (helpers stay private like `_is_valid_payment_card` `payment.py` L41)
- Change `PatternValidator` from findall to fullmatch
- Change `WordBoundary` into valio’s wrap constructor
- Add `StartsWith` / `SetOf` / lookarounds as public names (E14 second regex product)
- Invent GSTIN / IFSC / Voter / Passport / DL
- Ship `ListValidator` (would break `tests/test_product_surface.py` L48–49 without a Council KEEP flip that this pack does **not** request)
- Add `phonenumbers`
- Reopen Soft 8 PaymentCard / Expiry

### 3.5 DEFER / HOLD / KEEP-absent (confirm)

| Item | Status | Evidence |
| --- | --- | --- |
| Phone | **DEFER** | valio L2230–2265; phonenumbers dep; Matcher scan; `instance.region`; README L173 |
| Collections facades | **KEEP-absent** (was Soft 11 DEFER) | annotation-only L2424–2444 + dual-schema `LIST` L348; Soft 10 type door; product-surface L48–49; README L173 |
| GSTIN / IFSC / Voter / Passport / Driving licence | **KEEP-absent** | never in valio@3415c03 |
| AttributeValidator | **KEEP-absent** | AGENTS L29–30; test L181–183 |
| HexColor / RGB / HSL | **KEEP-absent** | crash RGB/HSL; HexColor not public AGENTS L38 |
| Date eu/ind strings | **PARTIAL KEEP** | `typed.py` L44–47 |
| compose #30 regexer stack | **HOLD** | Soft 6 / Soft 11; Pattern subset only |
| Field / Schema / typingx / pyparsing | **HOLD** | dual-schema park |
| Callable signature / Generic instance params | **DEFER** | Soft 10 locks |
| Soft 11 DO-1..4 | **separate tip** | PR #12 |

---

## 4. Risks if Council ACCEPTS this lock

- **Aadhaar Verhoeff without UIDAI:** valio never called an API. Tests should use a known-valid checksum vector and a one-digit mutation. Do not network.
- **PAN checksum vs frozen findall:** enforcing Luhn mod 26 **rejects** strings valio’s `findall` helper would accept (substring; no check digit). That is the Soft 8 PaymentCard move (E13), not a silent reread. Tests must name a format-valid / checksum-invalid reject.
- **PAN alphabet map:** copying `zip(..., range(1, 26))` silently drops `Z`. The widen tip must pick one complete mapping and lock it.
- **Named-once:** Aadhaar/PAN must not grow `_custom_validators` (`tests/test_named_validate_once.py`). Extra check lives on `validate()`, not `add_validator`.
- **Pattern findall KEEP:** ID facades must not teach `PatternValidator(pattern=aadhaar_regex)` as the product path — that would be substring Aadhaar. Identity is the facade’s `fullmatch` / checksum.
- Soft 6: implementing Soft 11-widen later must **not** land this pack on product `main`.

---

## 5. This PR vs Soft 6

`tests/test_product_surface.py` L94–96 forbids `docs/soft*.md` on product `main`. This draft is the pack vehicle (same contract as [PR #10](https://github.com/bitplorer/ux-valio/pull/10) and [PR #12](https://github.com/bitplorer/ux-valio/pull/12)).

**Do not merge onto `main` as a product commit.** ACCEPT the lock from the pack; a later Soft implements DO-W1..W3 with no ceremony docs.

No product code in this PR. Soft 11 DO-1..4 is not in this PR.
