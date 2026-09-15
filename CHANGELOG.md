# Changelog

## Unreleased

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
