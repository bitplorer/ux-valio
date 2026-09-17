# Changelog

## Unreleased

- Pattern combinators live in the `ux_valio.pattern` package. Taught
  imports stay on the package root (`from ux_valio import Pattern`);
  `ux_valio.pattern.Pattern` is the same object.
- Thin PatternTypes from valio@3415c03 `regexer/regexps.py`: `StartsWith`
  / `EndsWith` (L414 / L421), lookarounds `IfPrecededBy` /
  `IfNotPrecededBy` / `IfFollowedBy` / `IfNotFollowedBy` (L449–L470),
  `SetOf` character class (L261). `Contained` / `IfContained` are
  KEEP-absent (not in valio). CapturingGroup / WordGroups / scanString /
  pyparsing / `ux_valio.regexer` stay unported.
- `examples/` Door A cases for public facades, Pattern, hooks, compose,
  and `collect_all`.

- Nest-safe async bridge reuses a process-held worker pool (private; no
  public dial). It does not build a `ThreadPoolExecutor` per invoke.
- CI: pytest on push/PR (Python 3.12).
- `cache_task=` leftover teaching: kwarg kept, stored, never consulted
  (cache retired). Does not skip re-checks.
- Optional extra `phonenumbers>=9.0.0` (lower bound only; also on `dev`).

- `PhoneNumberValidator`: Door A string facade with required `region=`
  (ISO 3166-1 alpha-2 via `phonenumbers`). Leftover: valio defaulted to
  `instance.region` or `"IN"`. Optional extra `phonenumbers`; no network.
  `region` is not a kwarg on `Validator`.
- Pattern atoms `WhiteSpace` / `NonWhiteSpace` (`\s` / `\S`) on the
  existing Pattern algebra, same count kwargs as `Digit` / `Word`.
- `DateValidator` parses numeric EU (`YYYY-MM-DD`) and IND (`DD-MM-YYYY`)
  strings (`-` `/` `:`, same delimiter both sides) and stores
  `datetime.date`. Slash dates are IND day-month-year, not US. Month names
  / ordinals / pyparsing `scanString` are not ported. `datetime.datetime`
  is still rejected after the inherited path.

- `DateValidator` rejects `datetime.datetime` after the inherited path
  (`datetime.datetime` is a `date` subclass). Plain `datetime.date`
  subclasses that are not datetimes still assign.
- Pattern `&` / `|` is TypeError on a missing fragment or mixed
  `str`/`bytes`. Same-kind bytes fragments concatenate as bytes.
- Inverted Pattern `count_min > count_max` is constructor `ValueError`.
- `PatternValidator` matches `str` against `str` and `bytes` against
  `bytes`. Mixed kinds are TypeError; bytes are not `str()`-coerced.
- Named-facade extra checks participate in `collect_all` after the
  inherited path. They still do not `add_validator` themselves.

- Never-set `__get__` / `__delete__` with `debug=True` raise a named
  `AttributeError` (`Cls.field is not set`), not a bare `KeyError`.
  Debug-falsy still swallows and reads back `None`.
- `default_factory=` is a zero-arg callable invoked per None assignment.
  `default=[]` stays shared. Setting both `default` and `default_factory`
  is `TypeError`. Callable `default=` is still invoked (valio leftover).

- `AadhaarCardValidator`: 12-digit identity ∩ Verhoeff checksum (stdlib
  tables; no network). A substring or wrong-length value is rejected.
- `PANCardValidator`: 10-character identity `fullmatch` ∩ Luhn mod 26
  (complete A–Z map). A format-only generator is rejected.
- Pattern atoms `Digit` / `Word` / `NonDigit` / `NonWord` on the existing
  Pattern algebra (`findall` and `WordBoundary` unchanged).
- List / dict / set / tuple collection facades stay
  unshipped (`list[T]` / `dict` membership remains the type door).

- Unresolved owner annotations (`str` / `ForwardRef`, including postponed
  `from __future__ import annotations`) raise `TypeError` at bind and are
  not copied into the type door. They are not evaluated.
- `AnyOf` / `|` is OR: the compose root does not AND-run a type check
  before alternatives, and conflicting member annotations do not TypeError.
  `AllOf` / `&` still TypeErrors on conflicting member annotations.
- Compose merge treats explicit `collect_all=False` / `logger=False` as
  specified (conflict with `True` is `TypeError`). Omitted False still
  collapses to a specified True. `debug` stays fail-closed.
- Unknown `ValidationPath` units raise `ValueError`, not `KeyError`.
- PEP 695 aliases unwrap `__value__` on the private type helper (3.10
  `getattr`; no typing_extensions). TypedDict stays fail-closed. Callable
  origin is checked; signature is not.
- `cache_task=` is accepted on compose roots and `Validator`; stored,
  never consulted (cache retired).
- Reassignment counts drop on delete so `reassign=False` can assign again.
- Taught Door A path is a facade or `Validator` (not bare `Property`);
  leaf `&` is advanced; `Chain` is `AllOf`. `EmailValidator` findall is
  substring (not fullmatch).

- Type membership walks parametrized args with stdlib `get_origin` /
  `get_args`: `list[T]` / `dict[K, V]` / `set[T]` / `tuple` arity and
  `tuple[T, ...]`, including nested forms. `typing.List[T]` agrees with
  `list[T]` at bind time. `Literal` membership, `Annotated` strip, and
  `NewType` unwrap. `isinstance` `TypeError` is fail-closed (`False`);
  `typing.Any` and an unset annotation still accept. No public
  `check_instance`.
- Hook bags key by `module.qualname` on register and lookup. Free functions
  require `namespace=`. Class-object keys are rejected. Two same-named
  classes in different modules no longer collide.
- `PaymentCardValidator`: Visa / Mastercard / Amex / Discover / Rupay, each
  Luhn and brand via stdlib `re`. A Luhn-valid non-brand number is rejected.
- `ExpiryValidator`: exclusive `expire_after` / `expire_on` /
  `expire_before`. A bad `expire_before` string is checked on that bound.
  `expire_*` stay off the fat `Validator` facade; no `expiry` path unit.
- Named typed facades call their extra check from `validate()` after the
  inherited path and do not `add_validator` themselves on each assignment.
- Opt-in `collect_all=True` continues remaining concerns and surfaces
  `ValidationErrors`. Default stays fail-fast. `debug` is not collect-all.
- Compose roots (`AllOf` / `AnyOf`) carry `add_*` bags. Hang hooks on the
  root after `&`, or on a `Validator` facade. Concern leaves stay bag-free.
- Compose merge fail-closed: conflicting specified `debug` / `default` /
  `default_factory` is `TypeError`. A right-hand `debug=True` is kept.
- `Chain` is `AllOf`. Package `__all__` no longer advertises path/async
  internals.

## 0.1.0

- Door A descriptor-on-dataclass validation.
- Validators live in `ux_valio/validators/` with leaf-owned length/value
  methods (not a free-function owned API).
- Validator objects compose with `&` / `|` and `AllOf` / `AnyOf` / `Chain`.
- Public Min/Max length and value leaves; typed facades for float, Decimal,
  bytes, date, email, UUID, path, IP, and enum.
- `AttributeValidator` is not shipped.
- Async `add_*` registers; nest-safe worker bridge; no `asyncio.run` in
  `__set__`.
