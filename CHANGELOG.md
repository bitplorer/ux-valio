# Changelog

## Unreleased

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
- Compose merge fail-closed: conflicting specified `debug` / `default`
  is `TypeError`. A right-hand `debug=True` is kept.
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
