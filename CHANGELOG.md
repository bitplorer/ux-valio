# Changelog

## Unreleased

- Locality of behavior: compose flatten / specified-theory bind / annotation
  merge live on `_Compose` (not free-floating helpers). Hook phase table and
  `add_*` install live on `HookHost`. Origin table lives on
  `TypeValidator._ORIGIN_CHECKERS`. Specified-theory merge is `_Opt.merge` /
  `_Opt.read` (leftover aliases `merge_opt` / `opt_of`). Homogeneous
  container origin checkers share `_exact_type`.
- `&` / `|` bind `AllOf` / `AnyOf` once at compose import. Operator methods
  do not import compose on each use (`_load_compose_types` is the fallback).
  Type-door `is_instance_of` binds once the same way
  (`_register_annotation_checker` at leaves import).
- `not_in_choice` skips `None`, same as `in_choice` (string bags no longer
  TypeError on optional unset).
- `__get__` `post_get` records a secondary error and does not replace an
  in-flight never-set `AttributeError`.
- Annotation is a store invariant after `add_post_validator`. Named-facade
  extra is the same class of invariant (`_reject_store_identity`):
  post_validate cannot smuggle `"not-an-email"` onto `EmailValidator` or
  a `datetime` onto `DateValidator`. `AllOf` walks member extras; `AnyOf`
  still matches one alternative. Path bounds on AllOf / unnamed facades
  and custom validators are not re-run.
- Explicit `__slots__` on a Door A field TypeError at bind. A slots-only
  class TypeErrors at bind even when the field name is not a slot.
  Get/delete use `_require_instance_dict`. Inherited `getattr(..., "__slots__")`
  no longer false-positives a child that still has `__dict__`.
  `@dataclass(slots=True)` stays unsupported (descriptor dropped).
- Nest-safe worker re-entry is TypeError, not a deadlock hang.
- Rupay identity is `60` + 14 digits except Discover overlap (dead `6521`
  alternative removed).
- `__version__` matches `pyproject.toml` (`0.2.0`).
- Locks: Mastercard 2-series, `expire_on` calendar day, assignment weakref
  drop, findall empty-match KEEP, compose bind-once.

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
