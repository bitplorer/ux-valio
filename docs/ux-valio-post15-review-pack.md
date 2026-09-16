# ux-valio post-#15 review pack

**Research only.** No product tip. Frozen valio is **read-only**.

Council can accept the product worklist in §5 from this pack alone.

This is a KEEP-HEAD cartograph vehicle (same role as earlier draft packs).
`tests/test_product_surface.py` L105–107 forbids `docs/soft*.md` on product
`main`. This file is named so it is not that glob. **Do not merge this draft
onto `main` as a product commit.** Accept the worklist here; a later product
change implements with no ceremony docs.

---

## Identity

| Item | Value |
| --- | --- |
| Target | [`bitplorer/ux-valio`](https://github.com/bitplorer/ux-valio) `main` |
| `git log -1` HEAD | **`98776217c31f28ecacf5a3d26ed3898fe2e73de7`** |
| Subject | `Add Aadhaar, PAN, and Pattern digit/word atoms (#15)` |
| Claimed #15 merge | **`9877621`** — **verified equal to HEAD** after `git fetch origin main` (`mergeCommit` of [PR #15](https://github.com/bitplorer/ux-valio/pull/15)) |
| Parent (#14 teaching) | **`6117b50fcc91747cb5a83456c7cffafc5868e87f`** `Soft 11: harden existing doors (bind/AnyOf/merge/path) (#14)` |
| Frozen valio | [`bitplorer/valio@3415c03`](https://github.com/bitplorer/valio/commit/3415c03e37085adda4040671a91eb19aa4fe4ac4) `3415c03e37085adda4040671a91eb19aa4fe4ac4` |
| Valio subject | `Soft 10: compose full validation path; fail-closed units (#10)` — **PARKED; not edited** |
| Experiment Python | 3.12.3 |
| Package floor | `requires-python = ">=3.10"` (`pyproject.toml` L11) |
| Suite at HEAD | **264 passed** / 23 files / 0.38s (`python3 -m pytest tests`) |
| Barrel | `ux_valio.__all__` **47** (incl. `__version__`); `ux_valio.validators.__all__` **38**; leaked ⊆ top: empty. valio star barrel **306** names (no `__all__`; `valio/__init__.py` L7–14) |

HEAD check (this run):

```
98776217c31f28ecacf5a3d26ed3898fe2e73de7
Add Aadhaar, PAN, and Pattern digit/word atoms (#15)
```

Human ask: check what features are still missing; review naming; optimize;
check best practices / architecture / design / naming end-to-end. Name only
real gaps with `path:line`. Prefer harden existing doors. No Cap / Field /
Schema. No patch of parked valio. No public `check_*`. Phone / collections
only if Intent is CLEAR with a named design.

---

## Legend

| Mark | Meaning |
| --- | --- |
| **COVERED** | Door A analogue exists (name may differ; cited) |
| **PARTIAL** | Same role, different contract (KEEP unless a worklist row reopens it) |
| **MISSING** | valio Door A extra-check leaf; no ux analogue **and** not already named KEEP-absent |
| **KEEP-absent** | Named absence is the lock (do not ship) |
| **DEFERRED** | Real capability; needs a named design before a tip |
| **EXTRA** | ux-only; may stay |

Door A = `field: T = SomeValidator(...)`. Field twins and Schema are
KEEP-absent, not missing Door A leaves.

---

## 1. Pass A — Remaining feature gaps

valio@3415c03 capabilities → ux-valio HEAD `9877621`.

### 1.1 Confirm #14 teaching still holds (not a gap)

Measured on this HEAD; not reopened.

| Teaching | Evidence | Status |
| --- | --- | --- |
| Unresolved owner `str` / `ForwardRef` TypeError at bind; not copied, not eval'd | `descriptor.py` L30–32, L185–190; probe: postponed `Validator()` → `N.n: 'int' annotation is unresolved (string / ForwardRef); not copied into the type door` | COVERED |
| `AnyOf` / `\|` does not AND-gate root type; conflicting member annotations do not TypeError | `compose.py` L237–241, L243–261; probe: `IntegerValidator \| StringValidator` accepts `1` and `"a"`; `AllOf` still TypeErrors `int` vs `str` | COVERED |
| Compose merge: explicit `collect_all=False` / `logger=False` is specified | `compose.py` L32–37, L40–54; probe: `True & False` → `TypeError: composed validators have conflicting collect_all`; omitted False still collapses to specified True (`A3_OMITTED_FALSE_COLLAPSE True`) | COVERED |
| Unknown path unit is `ValueError`, not `KeyError` | `path.py` L66–69; probe: `ValidationPath(('type',)).run(..., lookup={})` → `ValueError: validation path unknown unit: 'type'` | COVERED |
| PEP 695 aliases unwrap `__value__` | `leaves.py` L41–45; probe: `type IntList = list[int]` → `[1]` True, `["a"]` False | COVERED |
| `cache_task=` accepted on compose roots; cache behavior retired | `compose.py` L136–147; probe: `AllOf(..., cache_task=False)` stores False; `tests/test_hooks_namespace.py` L326–346 | COVERED |
| Reassignment counts drop on delete | `facade.py` L95–97; `leaves.py` L197–199; `tests/test_descriptor_lifecycle.py` L33–43 | COVERED |

### 1.2 Confirm Aadhaar / PAN / Digit atoms COVERED after #15

| Leaf | valio@3415c03 | ux-valio HEAD `9877621` | Mark |
| --- | --- | --- | --- |
| `AadhaarCardValidator` | `validators.py` L2360–2389 `relib.is_valid_aadhaar_card` | `validators/aadhaar.py` L55–66; 12-digit identity ∩ Verhoeff (`L10–52`); extra check from `validate()` after `super()`; named-once `tests/test_named_validate_once.py` L46–57; substring rejected `tests/test_aadhaar_card.py` L47–49 | **COVERED** |
| `PANCardValidator` | `validators.py` L2392–2421 `relib.is_valid_pan_number` (findall + unused verify in relib) | `validators/pan.py` L37–48; `fullmatch` ∩ Luhn mod 26 complete A–Z (`L12–34`); format-only generator rejected `tests/test_pan_card.py` L29–31 | **COVERED** |
| Pattern `Digit` / `Word` / `NonDigit` / `NonWord` | `regexer/relib/patterns.py` L8–21, L64–142 | `pattern.py` L6–7, L156–169; count kwargs via `_StdlibAtom` L131–153; `findall` KEEP `leaves.py` L171; `tests/test_pattern_findall.py` L111–153 | **COVERED** |

Helpers stay private, inlined beside the payment-card style facades. No
`ux_valio.regexer` package (`hasattr(ux_valio, "regexer")` False;
`tests/test_product_surface.py` L54).

### 1.3 Full parity table (valio `validators.__all__` + Door A hosts)

Source: `/tmp/valio/valio/validator/validators.py` L71–125. ux: `ux_valio/__init__.py` L54–102; measured `hasattr` this run.

| valio name | valio def | ux-valio HEAD | Mark |
| --- | --- | --- | --- |
| `ValidateProperty` | L171 | `validators/base.py` L21–28 | COVERED |
| `TypeValidator` | L359; `isinstancex` L65, L408 | `leaves.py` L129–138; unexported `is_instance_of` L30–92 | COVERED (stdlib `get_origin`/`get_args`; not typingx) |
| `RequiredValidator` | L417 | `leaves.py` L141–155 | COVERED |
| `PatternValidator` | L461, findall L506–508 | `leaves.py` L158–176 findall L171 | COVERED |
| `ReassignValidator` | L516 | `leaves.py` L179–212 | COVERED |
| `MultipleValidator` | L570 | `leaves.py` L215–234 | COVERED |
| `ValueValidator` | L984 | `validators/value.py` | COVERED |
| `LengthValidator` | L1173 | `validators/length.py` | COVERED |
| `ExpiryValidator` | L1265; also fat-`Validator` kwargs L1688–1690 | Facade only: `validators/expiry.py` L62–95; `expire_*` not on `Validator`; no `"expiry"` path unit `path.py` L21–30 | COVERED |
| `ChoiceValidator` | L1347 | `leaves.py` L237–262 | COVERED |
| `TaskValidator` | L1476 | Hook bags (`add_*_task`); no public class | KEEP-absent (retired class; hooks COVERED) |
| `Validator` | L1581 | `validators/facade.py` L30–123 | COVERED |
| `IntegerValidator` | L1971 | `facade.py` L126–127 | COVERED |
| `FloatValidator` | L1979 | `typed.py` L32–33 | COVERED |
| `DecimalValidator` | L1987 | `typed.py` L36–37 | COVERED |
| `BooleanValidator` | L1995 | `facade.py` L134–135 | COVERED |
| `BytesValidator` | L1999 | `typed.py` L40–41 | COVERED |
| `StringValidator` | L2006 | `facade.py` L130–131 | COVERED |
| `HexShortColorValidator` | L2030 | `hasattr` False; `typed.py` L2; `tests/test_product_surface.py` L82–85 | KEEP-absent |
| `HexLongColorValidator` | L2041 | same | KEEP-absent |
| `HexColorValidator` | L2052 | same; AGENTS.md L47 | KEEP-absent |
| `RGBOrRGBAColorValidator` | L2063, **crash** L2070 `relib.r_rbga` (export is `r_rgba`) | `hasattr` False; AGENTS.md L7 | KEEP-absent (retired for crash) |
| `HSLOrHSLAColorValidator` | L2075, compiles `r_rgb \| r_rbga` not HSL | same | KEEP-absent (retired for crash) |
| `DateValidator` | L2087–2149 eu/ind **string** patterns + findall; annotation `DATE_TIME_DELTA` L339–345 | PARTIAL: `datetime.date` only; strings rejected `typed.py` L44–47; probe `DATE_STR TypeError d expect <class 'datetime.date'> type, got str type instead` | PARTIAL KEEP |
| `PathValidator` | L2268–2308 `StringValidator`; annotation `PATH = Union[Path, str, V]` L326 | PARTIAL: annotation `pathlib.Path`; coerce `str` on descriptor path `typed.py` L67–89 | PARTIAL KEEP |
| `EmailIDValidator` | L2169–2190 | COVERED as **`EmailValidator`** (rename); findall substring `typed.py` L17–29, L50–52 | COVERED |
| `PaymentCardValidator` | L2194–2226 | `payment.py` L54–65 brand ∩ Luhn; Luhn-only rejected `tests/test_payment_card.py` | COVERED |
| `PhoneNumberValidator` | L2230–2265 `phonenumbers.PhoneNumberMatcher`; `getattr(instance, "region", "IN")` L2260–2261 | `hasattr` False; README.md L207–209; `tests/test_product_surface.py` L50–51 | **DEFERRED** |
| `AadhaarCardValidator` | L2360 | see §1.2 | COVERED |
| `PANCardValidator` | L2392 | see §1.2 | COVERED |
| `IP4AddressValidator` | L2311 | COVERED as **`IPv4Validator`** `typed.py` L92–102 | COVERED |
| `IP6AddressValidator` | L2326 | COVERED as **`IPv6Validator`** L105–115 | COVERED |
| `IPAnyAddressValidator` | L2341 | COVERED as **`IPAddressValidator`** L118–128 | COVERED |
| `SequenceValidator` / `MappingValidator` | L2424–2428 annotation only | `hasattr` False | KEEP-absent (type door) |
| `ListValidator` / `DictionaryValidator` / `SetValidator` / `TupleValidator` | L2432–2444 annotation aliases `LIST`/`DICT`/… L348–351 | `hasattr` False; lock `tests/test_product_surface.py` L48–53 | KEEP-absent |
| `UUIDValidator` | L2164 | COVERED + EXTRA string coerce on **descriptor** path `typed.py` L55–64 | COVERED |
| `EnumValidator` / `IntegerEnumValidator` / `StringEnumValidator` | L2152–2161 | `typed.py` L131–163 | COVERED |
| Dual-schema aliases `INT`/`STR`/`LIST`/… | L329–355 `Union[T, V]` | not exported | KEEP-absent |
| `AttributeValidator` | L1432–1472; path unit `attribute` L863 | not shipped; AGENTS.md L38–39; `tests/test_typed_facades.py` | KEEP-absent |
| `MinLengthValidator` / `MaxLengthValidator` / `MinValueValidator` / `MaxValueValidator` | exist; several not in valio `__all__` | public EXTRA `length.py` / `value.py`; `tests/test_product_surface.py` L57–65 | EXTRA (may stay) |

### 1.4 Field / Schema / Cap / typingx / pyparsing

| Capability | valio@3415c03 | ux-valio HEAD | Mark |
| --- | --- | --- | --- |
| `Field` / typed `*Field` | `field/fields.py` L20–42, L191+ (Door B host) | `hasattr` False; `tests/test_door_a_readme.py` L128–132 | KEEP-absent |
| `Schema` / `schemas_v2` | `schema/__init__.py` L8–9; `schemas_v2.py` L21–174 | `hasattr` False | KEEP-absent |
| Legacy `schemas.py` | present, **not** imported | n/a | KEEP-absent |
| Cap Host / `mount_channel` | absent in valio too | absent; AGENTS.md L6 | KEEP-absent |
| `typingx` (`isinstancex` / `issubclassx`) | `validators.py` L65; `descriptors.py` L13; `pyproject.toml` `typingx = ^0.6.0` | stdlib only; AGENTS.md L33–36 | KEEP-absent |
| `pyparsing` | relib dates/payment/email scanString | AST lock `tests/test_product_surface.py` L88–102 | KEEP-absent |
| Star-import barrel | `valio/__init__.py` L7–14; 306 names | explicit `__all__` 47; README.md L218–219 | KEEP-absent |
| `enable_async` | `validators.py` L1626 | unknown-kwarg TypeError `tests/test_hooks_namespace.py` L319–323 | KEEP-absent |
| `asyncio.run` in setter | `validators.py` L810, L1842, L1826 | nest-safe bridge `async_bridge.py` L18–61; no `asyncio.run` in `__set__` `descriptor.py` L22 | KEEP-absent (ux EXTRA nest-safe) |
| Logger default ON (`logger=None` enables files) | `descriptors.py` L233–236 | default OFF `descriptor.py` L24, L105–107; `tests/test_door_a_readme.py` L110–114 | KEEP (ux OFF) |
| `collect_all` | absent | EXTRA `descriptor.py` L8–11; default False | EXTRA (may stay) |
| `AllOf` / `AnyOf` / `Chain` | absent (path units only) | EXTRA `compose.py`; `Chain is AllOf` L234 | EXTRA (may stay) |

### 1.5 Pattern / regexer remainder (after #15 atoms)

ux-valio has **one Pattern door**: `Pattern` / `PatternType` / `WordBoundary` /
`Digit` / `Word` / `NonDigit` / `NonWord`, `&` / `|`, `findall` KEEP
(`pattern.py` L1–7, L108–169; `leaves.py` L171).

| valio regexer piece | valio | ux HEAD | Mark |
| --- | --- | --- | --- |
| `Digit`/`Word`/`NonDigit`/`NonWord` | `relib/patterns.py` L64–142 | COVERED §1.2 | COVERED |
| `WordBoundary` | `regexps.py` L442 | `pattern.py` L126–128 | COVERED |
| `WhiteSpace` / `NonWhiteSpace` | `relib/patterns.py` L8–10, L24–50 `\s`/`\S` | `hasattr` False | **DEFERRED** — same atom family as #15; callers can already `Pattern(r"\s")`. No named design after #15 chose four atoms. |
| `WordGroups` / `DigitGroups` / `*Groups` | `relib/patterns.py` L12–21 | `hasattr` False | KEEP-absent (regexer stack) |
| `SetOf`, lookarounds, `All`/`Any` Pattern reduce, capturing groups | `regexps.py` L12–34 | not shipped | KEEP-absent |
| `scanString` / pyparsing | `relib/dates.py`, `paymentcards.py` | DEAD | KEEP-absent |
| `AndPattern` / `OrPattern` | (valio AND/OR classes) | exist in `pattern.py` L59–73; **not** in `__all__`; `hasattr(ux_valio, "AndPattern")` False | KEEP (private; `&`/`\|` return them) |

### 1.6 Real remaining gaps (only)

After #14+#15 there is **no Door A extra-check leaf still MISSING**.

| ID | Mark | Gap | Evidence |
| --- | --- | --- | --- |
| G1 | DEFERRED | `PhoneNumberValidator` | valio L2230–2265 needs `phonenumbers` + `instance.region` (default `"IN"`). ux `hasattr` False. README.md L207–209 names the leftover: engine **and** a region door. |
| G2 | KEEP-absent | Collection facades `List`/`Dict`/`Set`/`Tuple`/`Mapping`/`Sequence` | valio L2424–2444 are annotation aliases, not element validators. ux type door already walks `list[T]` / `dict[K, V]` (`leaves.py` L71–90; `tests/test_generics_honesty.py` L27–41). Product lock forbids `ListValidator` (`tests/test_product_surface.py` L48–49). |
| G3 | DEFERRED | Pattern `WhiteSpace` / `NonWhiteSpace` atoms | valio `relib/patterns.py` L8–10. Not shipped. Not a second regex product. Only ship if Intent is CLEAR (named count-kwargs atoms, same `_StdlibAtom` door). |
| G4 | PARTIAL KEEP | `DateValidator` strings / EU+IND patterns | valio L2087–2149. ux `typed.py` L44–47 `datetime.date` only. Probe rejects `"2020-01-01"`. |
| G5 | PARTIAL KEEP | `PathValidator` annotation `Path` not `str\|Path` | valio L326, L2268. ux `typed.py` L67–68. Coerce on assignment COVERED. |
| G6 | KEEP-absent | Field / Schema / Cap / AttributeValidator / RGB-HSL / HexColor / typingx / pyparsing / public `check_*` | AGENTS.md L6–7, L33–39, L47; `tests/test_product_surface.py` L39–54, L82–102 |

**P0 missing features: 0.** Phone is the only remaining valio extra-check
facade without an analogue, and it is already named DEFERRED with a reason.

---

## 2. Pass B — Naming conventions

Clarity Test used below: propose a rename only when it is the **same idea**
and **ambiguity goes down**. Otherwise KEEP and document.

### 2.1 Public exports

| Surface | Names | Honesty |
| --- | --- | --- |
| `ux_valio.__all__` | 47 incl. `__version__` (`__init__.py` L54–102) | Explicit. No star barrel. |
| `ux_valio.validators.__all__` | 38 (`validators/__init__.py` L43–82) | Subset of top. Lock: `tests/test_product_surface.py` L110–112. |
| Top-only | `Digit`, `NonDigit`, `NonWord`, `Pattern`, `PatternType`, `Property`, `Word`, `WordBoundary`, `__version__` | Pattern algebra lives in `pattern.py`, not the validators subtree. Dual barrels are layered, not synonymous. |
| `dir(ux_valio)` without `_` | 49 | Extra are submodules (`validators`, `pattern`, `descriptor`), not leaked validators. |

Taught field default is a facade or `Validator`, not bare `Property`
(README.md L16–19; `tests/test_door_a_readme.py` L135–139). `Property` stays
exported because it is the descriptor base (`descriptor.py` L81). That is a
**dual name with a taught door**, not a synonym to collapse.

### 2.2 Validator vs facade vs leaf

| Name | Role | KEEP? |
| --- | --- | --- |
| `Property` | Storage descriptor | KEEP. Not the taught default. |
| `ValidateProperty` | `Property` + `pre_set` **is** validate (`base.py` L21–28) | KEEP. Advanced / compose bound. |
| `Validator` | Facade: binds leaf **methods** onto one path (`facade.py` L1–6, L99–109) | KEEP. Taught door. |
| Concern leaves (`LengthValidator`, …) | Advanced `&` / `|` building blocks | KEEP. README.md L32–35. |
| Typed facades (`IntegerValidator`, `AadhaarCardValidator`, …) | `annotation` + optional extra `validate()` | KEEP. Named-once: extra check in `validate()`, not `add_validator` on assign (`aadhaar.py` L58–60; `pan.py` L40–42). |

Facades do **not** multiple-inherit leaves (`tests/test_compose_not_inherit.py`).
No rename: the three layers are three ideas.

### 2.3 Pattern atoms vs `PatternValidator`

| Name | Idea |
| --- | --- |
| `Pattern` / `PatternType` | Regex fragment algebra (`pattern.py` L17–123) |
| `Digit` / `Word` / … | Stdlib `re` atoms on that algebra (`pattern.py` L156–169) |
| `PatternValidator` | Door A leaf: `re.findall` (`leaves.py` L158–176) |

Not synonyms. KEEP. Callers write `PatternValidator(pattern=Digit(count=2))`.

### 2.4 Dual names / synonym surfaces

| Pair | Same idea? | Clarity Test | Action |
| --- | --- | --- | --- |
| `Chain` = `AllOf` (`compose.py` L234) | Yes | `Chain` is the valio-ish word; `AllOf` is the algebra. README teaches `Chain is AllOf`. Dropping either raises ambiguity for one audience. | **KEEP both** (alias, not a third AND) |
| `EmailValidator` vs valio `EmailIDValidator` | Yes | ux name is already clearer | KEEP ux name; no alias |
| `IPv4Validator` vs valio `IP4AddressValidator` | Yes | ux name is already clearer | KEEP ux name; no alias |
| `IPAddressValidator` vs valio `IPAnyAddressValidator` | Yes | ux name is already clearer | KEEP ux name; no alias |
| `AadhaarCardValidator` / `PANCardValidator` (`Card` in identity names) | valio names | Renaming to `AadhaarValidator` would drop a shipped #15 public name for little gain | **KEEP** (parity with valio + already exported) |
| `PANCardValidator` vs `PaymentCardValidator` | **No** | India tax id vs card brands | KEEP both |
| `AndPattern` / `OrPattern` not in `__all__` | Implementation of `&`/`\|` | Exporting them would mint a second way to spell `&`/`\|` | KEEP private |
| `add_pre_validator` vs bag key `pre_validate` (`hooks.py` L18–20, L151–153) | Same phase | Hook name matches valio; bag key is the pipeline stage. Renaming the bag would be a second door. | KEEP |
| `ValidationErrors` (plural) vs a singular `ValidationError` | collect-all aggregate | Matches `collect_all` (many). A singular type would collide with “one failure”. | KEEP |
| `check_*` vs `is_instance_of` | membership helper | Public `check_*` forbidden (`tests/test_product_surface.py` L39–47). Private helper name is honest. | KEEP unexported |

### 2.5 Error message tone

Two grammars coexist:

- Kwarg config: `"X expected type bool value, got … type instead"` (`descriptor.py` L95, L103; `facade.py` L61–66).
- Runtime check: `"{name} expect {annotation} type, got {type} type instead"` (`leaves.py` L133–135; `length.py` L24–25; `value.py` L33).
- Named facades: `"{name} expects a UUID"` / `"is not a valid Aadhaar number"` (`typed.py` L63; `aadhaar.py` L66; `pan.py` L48; `payment.py` L65).

Clarity Test: unifying `expect` → `expects` is the **same idea**, slightly
less awkward, **but** it is a string-contract churn (tests and callers may
match text) and does not name a new capability. **KEEP** unless Council
wants a dedicated message-tone pass. Do not mix that pass with Phone or
new atoms.

`got {type(value).__name__} type instead` interpolating a string annotation
was the old postponed-copy bug; #14 bind TypeError closed it (`descriptor.py`
L185–190). Residual awkwardness on **runtime** type errors (`expect <class
'int'> type, got str type instead`) is valio-shaped. KEEP.

### 2.6 Module names

One primary facade per domain file: `aadhaar.py`, `pan.py`, `payment.py`,
`expiry.py`. Typed stack shares `typed.py`. Leaves grouped (`leaves.py`,
`length.py`, `value.py`). Infrastructure: `base.py`, `facade.py`,
`compose.py`, `hooks.py`, `path.py`, `async_bridge.py`, `errors.py`.

No module rename passes the Clarity Test. `validators/path.py` is the
**validation-path** unit list, not `pathlib` — adjacent to `PathValidator` in
`typed.py`. Documented by ownership, not a rename (a rename would collide
with pathlib in callers’ heads). KEEP.

---

## 3. Pass C — Architecture / design

### 3.1 One Door A, three stacking mechanisms

Taught path after #14+#15:

```
field: T = SomeValidator(...)
```

| Mechanism | What it stacks | Owner |
| --- | --- | --- |
| Path units | Ordered concerns on one `Validator` facade | `path.py` L21–30; lookup `facade.py` L99–109 |
| Object compose | `&` / `\|` / `AllOf` / `AnyOf` as **one** descriptor | `base.py` L73–85; `compose.py` L210–266 |
| Hook bags | `add_pre_validator` / `add_validator` / `add_*_task` | `hooks.py` L84–115; hang on `Validator` or compose **root**, not leaves |

`pre_set` **is** `pre_validate → validate → post_validate` (`base.py` L24–28).
There is no `_processors["pre_set"]` and no `add_pre_set` (`hooks.py` L4–5,
L17–19; `tests/test_door_a_honesty.py`).

`Chain` is `AllOf` — alias, not a fourth AND (`compose.py` L234).

### 3.2 Degrees of freedom / dual doors — do not add

| Temptation | Why it is a second door | Status |
| --- | --- | --- |
| `Field` / `*.validator` | Door B host | KEEP-absent |
| `Schema` | Dual schema + Field subclass | KEEP-absent |
| Cap / `mount_channel` | Extra host | KEEP-absent |
| `add_pre_set` | Second before-store bag beside `pre_set` hook | KEEP-absent |
| `enable_async` | Second async switch beside nest-safe bridge | unknown-kwarg TypeError |
| Public `check_instance` | Second type door beside descriptor/`validate()` | KEEP-absent |
| `ux_valio.regexer` | Second regex product beside `pattern.py` | KEEP-absent |
| Collection `*Validator` facades | Second element door beside `is_instance_of` args | KEEP-absent |
| `expire_*` on fat `Validator` | Second expiry home beside `ExpiryValidator` | KEEP-absent (`tests/test_door_a_honesty.py`) |
| `"expiry"` path unit | Third expiry home | KEEP-absent `path.py` L21–30 |

UUID/Path **string coerce** lives in `pre_validation_processing`
(`typed.py` L58–64, L78–81). Assignment runs coerce then `validate()`
(`base.py` L24–28). Direct `.validate(None, "<uuid-str>")` TypeErrors
(probe: `UUID_VALIDATE_STR TypeError … got str`). That is a **second call
shape**, not a second product door. KEEP: the taught door is assignment.
Do not add coerce inside `validate()` as a “fix” — that would make
`.validate()` a competing door.

### 3.3 Compose honesty (post-#14)

- **AllOf**: merge member annotations; conflict TypeError (`compose.py`
  L112–126, L216–221). AND-runs `TypeValidator._validate_type` then members.
- **AnyOf**: `_merge_member_annotations = False`, `_propagate_annotation =
  False` (L240–241). First member that validates wins (L243–261). Conflicting
  typed facades compose. Probe: `IntegerValidator | StringValidator` stores
  `1` and `"a"`.
- Merge sentinels: `debug` unspecified `None`; `collect_all` / `logger` use
  `_collect_all_specified` / `_logger_specified` (`compose.py` L32–37;
  `descriptor.py` L105–124). Explicit `False` conflicts with `True`.
  Omitted runtime False still collapses to a specified True.

### 3.4 Hooks / bags

- Phases: `pre_validate`, `post_validate`, `post_set`, `pre_get`, `post_get`,
  `pre_delete`, `post_delete` (`hooks.py` L17–27).
- Bag key: `module.qualname` register **and** lookup (`hooks.py` L30–32,
  L102–103). Free function requires `namespace=`. Class objects TypeError.
- Processors then tasks once (`hooks.py` L112–115;
  `tests/test_processors_then_tasks.py`).
- Get/delete hooks receive **name**, not stored value (`descriptor.py`
  L20–21, L214–235). KEEP.
- `cache_task` kwarg KEEP; does not skip re-checks
  (`tests/test_hooks_namespace.py` L326–346).
- Async: `async def` and coroutine results accepted; no loop → TypeError
  naming the helper (`async_bridge.py` L18–20, L56–60); running loop →
  nest-safe worker (`L24–41`). No `asyncio.run` in `__set__`.

### 3.5 `is_instance_of` Generics

Private helper `leaves.py` L30–92. Shared by bind/`validate()`.

| Case | Behavior | Evidence |
| --- | --- | --- |
| `list[T]` / `dict[K,V]` / `tuple` arity / `tuple[T, ...]` / set / frozenset | origin+args recurse | L71–80; tests |
| ABC Sequence/Mapping/Set/Collection | walk elements | L83–90 |
| Union / Optional / `X \| Y` | any | L63–66 |
| `Annotated`, `NewType`, `Literal`, TypeVar bound/constraints | unwrap / membership | L48–70 |
| PEP 695 `TypeAliasType` | `__value__` | L41–45 |
| `str` annotation | False | L46–47 |
| TypedDict | fail-closed | L37; `tests/test_generics_honesty.py` L315–325 |
| Callable | origin only, not signature | L81–82; tests L283–286 |
| Generic subclass instance params | not inspected | tests L298: `Box("a")` vs `Box[int]` True |
| `isinstance` TypeError | False | L95–99 |
| `Any` / unset annotation | True | L39–40 |

Not typingx. Not a public `check_*`.

### 3.6 Dual barrels / module ownership

```
ux_valio/                 # product door
  __init__.py             # 47 names
  descriptor.py           # Property
  pattern.py              # Pattern algebra + atoms
  validators/             # 38 names: leaves, facades, compose
```

`from ux_valio.validators import Digit` fails (Digit is top-only). That is
ownership, not a leak. KEEP.

---

## 4. Pass D — Optimization / standards

Hot-path numbers are from this run (CPython 3.12.3, `/workspace`,
`PYTHONPATH=.`). No speculative rewrite.

### 4.1 Measured hot paths

| Path | n | elapsed | per-call | Verdict |
| --- | --- | --- | --- | --- |
| `PatternValidator.validate` (`re.compile` each time, `leaves.py` L171) | 5000 | 0.003937s | 0.79 µs | Fine |
| Same `findall` with precompiled pattern | 5000 | 0.001254s | 0.25 µs | ~3× cheaper; **still sub-µs**. Caching would need invalidation if `pattern` mutates. **No rewrite.** |
| `Digit(count=2)` construct | 5000 | 0.005177s | 1.0 µs | Fine |
| `Pattern(r"A") & Digit(count=2)` | 5000 | 0.009190s | 1.8 µs | Fine |
| `is_instance_of(list(range(4000)), list[int])` | 20 | 0.048088s | 2.4 ms / 4000-walk | Expected O(n). Fail-fast `["a"]*4000` 200× = 0.000367s. **No rewrite.** |
| `is_instance_of(1, int)` | 20000 | 0.012262s | 0.61 µs | Fine |
| `_bag_key` | 100000 | 0.008524s | 85 ns | Fine |
| Verhoeff Aadhaar | 20000 | 0.023467s | 1.2 µs | Fine |
| PAN Luhn mod 26 | 20000 | 0.034847s | 1.7 µs | Fine |
| Payment brand ∩ Luhn | 5000 | 0.007620s | 1.5 µs | Fine |
| `IntegerValidator.validate(4)` | 20000 | 0.056666s | 2.8 µs | Fine |
| Dataclass assign `IntegerValidator` | 5000 | 0.027583s | 5.5 µs | Fine |

**No performance product DO.** A Pattern compile cache would be fashion at
0.5 µs saved, not a conserved simplification.

### 4.2 Typing / packaging / tests-as-locks

| Item | Evidence | Mark |
| --- | --- | --- |
| Floor 3.10 | `pyproject.toml` L11 | KEEP |
| `py.typed` present (empty PEP 561 marker) | `ux_valio/py.typed`; classifier `Typing :: Typed` L19 | KEEP |
| Hatchling wheel `packages = ["ux_valio"]` | `pyproject.toml` L26–27 | KEEP |
| No runtime deps | `pyproject.toml` (no `dependencies`) | KEEP (Phone would add `phonenumbers` — another reason it needs a named design) |
| Tests-as-locks | 23 files; 264 passed. Surface, Door A honesty, compose, generics, named-once, Aadhaar/PAN, Pattern atoms | KEEP |
| No ruff / mypy / coverage in-tree | `pyproject.toml` | P2 standards residual — optional tooling, not a door |
| SPDX MIT headers on product modules | e.g. `aadhaar.py` L1 | KEEP |

### 4.3 Fail-closed boundaries (healthy)

- Bind annotation conflict / unresolved (`descriptor.py` L185–202)
- Unknown path unit (`path.py` L66–69)
- Compose specified-sentinel (`compose.py` L40–54)
- TypedDict / unknown origin (`leaves.py` L37, L95–99)
- `multiple_of=0` only accepts `0` (`leaves.py` L224–227)
- Bound `None` ≠ `0` (`bounds.py`; `tests/test_bound_honesty.py`)
- Falsy assigned `0` / `False` / `""` not replaced by `default` (`descriptor.py` L3–5, L206–207)

### 4.4 P0 / P1 / P2 findings

**P0: 0.** Spine still locks. Suite green.

**P1: 0.** #14 closed the four honesty cliffs (bind / AnyOf / merge / path).
#15 closed Aadhaar / PAN / Digit atoms. No remaining P1 feature gap.

**P2 residuals** (not dual doors; not required tips):

| ID | Topic | Evidence | Worklist |
| --- | --- | --- | --- |
| P2-1 | `__get__` on never-set attribute with `debug=True` re-raises `KeyError` | `descriptor.py` L214–222; probe `GET_NEVER_SET KeyError 's'`; `debug=False` returns `None` (KEEP swallow) | Optional UX harden of the existing get door. Not a feature gap. |
| P2-2 | UUID/Path coerce only on descriptor path | `typed.py` L58–81; probe `UUID_VALIDATE_STR` TypeError vs `UUID_ASSIGN UUID` | KEEP — assignment is the door (§3.2) |
| P2-3 | `expire_on` is nanosecond equality | `expiry.py` L88–89 `now == parsed`; valio `validators.py` L1335–1336 same | KEEP (frozen-valio parity) |
| P2-4 | `expect` vs `expects` error grammar | §2.5 | KEEP unless a dedicated tone pass |
| P2-5 | `number_of_assignment` increments, never used for reassignment | `facade.py` L71, L93; check uses `_assignment_counts` L201–205 | KEEP leftover counter; do not mint a public API on it |
| P2-6 | No linter/typechecker in `pyproject.toml` | packaging | Optional tooling; not a product door |

S-tier Python practices already in tree: explicit `__all__`, `from __future__
import annotations` in library modules with runtime bind fail-closed on
**owner** postponed annotations, nest-safe async, fail-closed unknown path
units, tests that lock absences (`PhoneNumberValidator`, `ListValidator`,
`check_instance`, `HexColorValidator`, pyparsing, `docs/soft*.md`).

---

## 5. Proposed product worklist

Plain product language. Council can ACCEPT this section alone.

Prefer **harden existing doors**. No Cap / Field / Schema. No patch of
parked valio. No public `check_*`. Phone / collections / extra Pattern
atoms only with named design.

### 5.1 DO

| ID | Work | Why now | Why not a new door |
| --- | --- | --- | --- |
| — | **None required.** Feature parity for Door A extra-check leaves is complete after #15. #14 teaching still holds. | P0=0, P1=0 | — |

Optional, only if Council wants debug-path UX (not a missing feature):

| ID | Work | Notes |
| --- | --- | --- |
| OPT-1 | Never-set `__get__` with `debug=True`: raise `AttributeError` naming the field instead of bare `KeyError` | Same get door (`descriptor.py` L214–222). Swallow when `debug` is falsy stays. Needs a lock test. Skip if Council prefers KeyError-as-honest-dict. |

### 5.2 KEEP

| Item | Why |
| --- | --- |
| Door A only: `field: T = SomeValidator(...)` | Taught path |
| Falsy assigned `0` / `False` / `""` not replaced by `default` | Bound honesty |
| `None` ≠ `0` on min/max/gt/lt/`multiple_of` | Bound honesty |
| debug-swallow; logger default OFF | Product contract |
| Pattern `findall` substring (incl. `EmailValidator`) | Product KEEP |
| Facades do not multiple-inherit leaves; `&` / `\|` object compose | One compose door |
| `Chain is AllOf` | Alias, not a third AND |
| `pre_set` hook **is** the validate pipeline; no `add_pre_set` | Dual-door lock |
| Processors then tasks once; bag keys `module.qualname` | Hook honesty |
| `add_*` accepts async def and coroutine results; nest-safe bridge; no `asyncio.run` in `__set__` | Async honesty |
| `enable_async` unknown-kwarg TypeError | Not a door |
| `cache_task` kwarg; cache behavior retired | API cliff closed on compose roots |
| `collect_all` default False; not overloaded onto `debug` | Fail-fast default |
| Hang `add_*` on `Validator` or compose root, not leaves | Bag ownership |
| Compose merge fail-closed on specified `debug` / `default` / `collect_all` / `logger` | #14 |
| Unresolved owner `str` / `ForwardRef` TypeError at bind | #14 |
| AnyOf does not AND-gate root type; AllOf keeps annotation-conflict TypeError | #14 |
| Unknown path unit `ValueError` | #14 |
| TypedDict fail-closed; Callable origin only; Generic subclass params not inspected | Type door |
| PaymentCard brand ∩ Luhn; Expiry exclusive `expire_*`; no `expiry` path unit | Soft 8 KEEP |
| Named facades: extra check from `validate()` after inherited path; bags do not grow | named-once |
| Aadhaar 12-digit ∩ Verhoeff; PAN fullmatch ∩ Luhn mod 26 | #15 |
| `Digit` / `Word` / `NonDigit` / `NonWord` on existing Pattern algebra | #15 |
| `HexColorValidator` / RGB/HSL / `AttributeValidator` not public | AGENTS.md |
| Dual barrels (package vs `validators` vs `pattern`) | Ownership |
| `Property` exported, not taught as field default | Descriptor base |
| Error grammar `expect` / `expects` | Tone KEEP unless OPT tone pass |
| UUID/Path coerce on descriptor path only | Assignment is the door |
| `DateValidator` is `datetime.date`; strings not parsed | PARTIAL KEEP |
| `expire_on` nanosecond equality | valio parity |
| Python ≥ 3.10; no typingx; no pyparsing | Floor / deps |
| `collect_all`, `AllOf`/`AnyOf`, nest-safe async (ux extras) | May stay |
| Public Min/Max length and value leaves | EXTRA; may stay |

### 5.3 DEFER

| Item | What a later tip would still need (named design) |
| --- | --- |
| `PhoneNumberValidator` | A `phonenumbers` (or equivalent) engine **and** a region door. valio reads `instance.region` default `"IN"` (`validators.py` L2260–2261). That is a new kwarg/attribute contract, not a drop-in facade. Do not ship without Intent CLEAR. |
| Pattern `WhiteSpace` / `NonWhiteSpace` atoms | Same `_StdlibAtom` door as Digit/Word. Callers can `Pattern(r"\s")` today. Only if Council names those two atoms; do not reopen Groups / lookarounds / `SetOf`. |
| Callable **signature** checking | Origin is checked; signature is not (`leaves.py` L81–82). |
| Generic subclass instance params (`Box[int]` vs `Box("a")`) | Explicitly not inspected (`tests/test_generics_honesty.py` L298). |

### 5.4 DO NOT

| Item | Why |
| --- | --- |
| Cap Host / `mount_channel` | Extra host |
| Field twin / Schema twin / `rule/` / Result type | Dual schema / Door B |
| Patch parked valio @ `3415c03` | Frozen reference |
| Public `check_*` / `check_instance` | Second type door |
| `add_pre_set` / `_processors["pre_set"]` | Second before-store door |
| `enable_async` | Second async door |
| Collection facades (`ListValidator`, …) without named design | Type door already owns `list[T]` |
| `ux_valio.regexer` package / pyparsing / `scanString` / SetOf / lookarounds / Groups | Second regex product |
| Unpark typingx / typing_extensions on the type door | stdlib `get_origin`/`get_args` |
| RGB/HSL / public `HexColorValidator` | Retired (valio RGB crash) |
| `AttributeValidator` | Call site / `add_validator` |
| `expire_*` on fat `Validator`; `"expiry"` path unit | Expiry lives on the facade |
| NamedOnce Cap | Behavior lock is enough |
| Merge this pack onto product `main` as a docs product commit | Cartograph vehicle |
| Coerce UUID/Path inside `validate()` to “match” assignment | Would make `.validate()` a competing door |
| Rename `Chain`, `AadhaarCardValidator`, `PANCardValidator`, bag keys, or `Property` | Clarity Test fails or already-shipped names |

---

## 6. Risks if Council ACCEPTS this worklist

- **Empty required DO is the finding.** A later agent must not invent Phone,
  WhiteSpace, or collection facades to “have a tip.”
- OPT-1 (never-set get) changes the `debug=True` exception type from
  `KeyError` to `AttributeError` if accepted. Callers catching `KeyError`
  on a never-read field would need a lock update.
- Phone remains the only valio extra-check facade without an analogue.
  Shipping it without a region door would be a silent `IN` default (valio
  L2260–2261) — a hidden second annotation.
- Postponed `from __future__ import annotations` on **caller** dataclasses
  stays fail-closed at bind. That is KEEP, not a hole. Docs already say
  drop postponed annotations on Door A fields (README.md L158–161).

---

## 7. This PR vs product main

`tests/test_product_surface.py` L105–107:

```
assert not docs.exists() or not any(docs.glob("soft*.md"))
```

This pack is `docs/ux-valio-post15-review-pack.md`. It is still a KEEP-HEAD
vehicle: **do not squash-merge onto `main` as a product commit.** ACCEPT the
worklist from §5; product tips land later with no ceremony docs.

No product code in this PR.
