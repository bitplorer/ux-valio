# Changelog

## Unreleased

## 0.2.0

- Python floor matches ux-compose: `requires-python >=3.14`, classifier 3.14,
  CI `python-version: "3.14"`. 3.10–3.12 classifiers retired.
- Policy is one specified-theory (`_Opt`). Compose merge reads `_opts` only.
- Facade `validate()` and AnyOf post-win custom bag use `run_steps`.
- Compose processing phases are one order table, not seven copied methods.
- Type door is an origin table. Hook `add_*` names stay; bodies are one table.
- `PatternValidator` compiles per source identity. Engine stays `findall`.
- Assignment counts drop when the instance is collected (weakref).
- Successful `__set__` clears descriptor `errors`.
- `ExpiryValidator.expire_on` is valid only on that calendar day.
- `EmailValidator` requires the whole string to be an addr-spec.
  PatternValidator findall is unchanged.
- `PaymentCardValidator` Mastercard IIN includes 2221–2720.
- `examples/` are copyable production skeletons: Protocol ports, in-memory
  fakes, Door A dataclasses, and a service that injects ports in the
  constructor. Signup (`collect_all_form.py`) is complete auth. Hasher stays
  in the example (`Pbkdf2PasswordHasher`). Examples do not ship a DB driver.
- Pattern atom names KEEP the valio@3415c03 PatternType surface.
  `Contained` / `IfContained` are KEEP-absent.
- CI: pytest on push/PR (Python 3.14).
- Taught Door A path is a facade or `Validator` (not bare `Property`);
  leaf `&` is advanced; `Chain` is `AllOf`.

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
