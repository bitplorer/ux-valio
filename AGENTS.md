# AGENTS.md

Door A only: `field: T = SomeValidator(...)`.

Layout (core at the root, validate door inherits, named facades are parallel):

- `ux_valio/descriptor.py` — `Property` (store). Imports `errors`, never
  `validators`.
- `ux_valio/errors.py` — `ValidationErrors` (shared collect-all type).
- `ux_valio/pattern/` — pattern algebra (independent).
- `ux_valio/validators/` — validate door (`ValidateProperty` : `Property`):
  `base` → `ValidateProperty`; `hooks` → `HookHost` mixin (parallel);
  `leaves` / `length` / `value` → concern leaves (parallel, compose with
  `&` / `|`, no leaf MI); `compose` → `AllOf` / `AnyOf`; `facade` →
  `Validator`; `typed` + `payment` / `expiry` / `phone` / `aadhaar` /
  `pan` → named facades : `Validator` (parallel). Facade unit list is
  `validation_path.py`, not `PathValidator` (`typed.py`, pathlib).
  Primitive typed facades (`IntegerValidator` / `StringValidator` /
  `BooleanValidator`) live in `typed.py` with the rest.
  `Validator[T]` is the stored-type subscript (one argument). It fills
  `annotation` when the class did not declare one. Named facades
  specialize it (`IntegerValidator` is `Validator[int]`). Unconstrained
  `TypeVar` owner/subscript is typing-only (one descriptor cannot
  specialize per `Box[int]` / `Box[str]`). Bound/constrained TypeVars
  still copy into the type door.

- Python floor is ≥ 3.14 (same as ux-compose). Do not teach 3.10–3.12.

- Frozen reference: `bitplorer/valio` @ `3415c03`. Do not edit valio.
- No Cap Host, `mount_channel`, Field twin, Schema twin, `rule/`,
  Result type, RGB/HSL, or star-import barrel.
- No `asyncio.run` in `__set__`. Nested loops use the nest-safe worker
  bridge only.
- No `add_pre_set` / `_processors["pre_set"]` (that would be a second door).
- KEEP: falsy assigned `0` / `False` / `""` are not replaced by `default`;
  `default=[]` is shared; `default_factory=` is per-instance; both set is
  TypeError; callable `default=` still invoked (valio leftover);
  bound honesty (`None` ≠ `0`); debug-swallow; logger default OFF;
  ``logger=True`` binds a stdlib ``logging.Logger`` at ``__set_name__``
  named ``module.qualname.field`` (no files, no ``logs/`` directory);
  ``logger=None`` is OFF (not valio's None=on); a ``logging.Logger`` is
  used as-is; get/set/delete log at info, failures at error;
  never-set `__get__` / `__delete__` with `debug=True` is named
  `AttributeError`, not bare `KeyError`;
  Pattern `findall` (empty-match `a*` is a match; Email extra is fullmatch);
  facades do not multiple-inherit concern leaves;
  path fail-closed; processors then tasks once;
  `pre_set` hook IS the validate pipeline (no processor bag named `pre_set`);
  Hang `add_*` on the field name (`@username.add_pre_validator` in the
  class body). Class access returns the descriptor (`Cls.field.add_*`
  after bind) and records that class as `_owner`, so a shared
  descriptor's `Person.aadhaar.add_*` uses Person, not the last
  `__set_name__`. Dataclass default is that descriptor; `__set__`
  treats `value is self` as unset. No Field mixin, no outer
  `username_field` twin unless sharing one descriptor across classes.
  Lookup walks the instance MRO (base first) so a child runs parent hooks.
  A free function on an unbound descriptor still needs `namespace=`;
  on a bound field the bag key is the bound owner.
  `add_*` accepts async def and coroutine
  results (no `_reject_coroutine_result`);
  sync path with no running loop TypeError names the missing loop / helper;
  running loop uses the process-held nest-safe worker bridge.
  Re-entering that worker is TypeError (would deadlock), not a hang.
  `enable_async` is not a door (unknown-kwarg TypeError).
  `cache_task` kwarg KEEP, cache behavior RETIRE. Accepted on `Validator`
  and on compose roots (`AllOf` / `AnyOf`); stored, never consulted;
  it does not skip re-checks.
  `collect_all` default False (fail-fast). Do not overload `debug` into
  collect-all. Hang `add_*` on `Validator` or the compose root (`AllOf` /
  `AnyOf`), not concern leaves. Compose merge fail-closed: conflicting
  specified `debug` / `default` / `default_factory` / `collect_all` /
  `logger` is TypeError.
  Explicit `False` is specified. Omitted `collect_all` / `logger` still
  collapse to a specified `True`. `Chain` is `AllOf`.
  Unresolved owner `str` / `ForwardRef` annotations TypeError at bind
  (not copied, not eval'd). `AnyOf` does not AND-gate root type; `AllOf`
  keeps annotation-conflict TypeError. Unknown path unit is `ValueError`.
  TypedDict membership stays fail-closed on the private helper. Callable
  origin is checked; signature is not. Generic subclass instance params
  are not inspected.
  `&` / `|` use AllOf / AnyOf bound once (`_register_compose_types` at
  compose import; `_load_compose_types` is the fallback). Do not import
  compose inside `__and__` / `__or__`. `leaves.py` binds `is_instance_of`
  once via `_register_annotation_checker`. Origin tables `_ORIGIN_CHECKERS`
  / `_ORIGIN_GROUPS` live next to `is_instance_of`, not on `TypeValidator`.
  `not_in_choice` skips `None`, same as `in_choice`.
  `in_choice` / `not_in_choice` that are not a ``Container`` TypeError at
  construct, not at assignment.
  Unsized ``len()`` on a length bound is a named TypeError
  (``expect a sized value``), not the raw ``object of type 'int' has no len()``.
  `EmailValidator` identity fullmatch uses the same compiled pattern as
  the findall path (``PatternValidator._compiled_finder``).
  `post_get` in `__get__` `finally` records a secondary error and does
  not replace an in-flight exception.
  Annotation is a store invariant: `add_post_validator` may transform,
  then `_reject_store_type_mismatch` TypeErrors a value that would not
  pass the type door. Named-facade extra is the same class of invariant
  (`_reject_store_identity` re-runs `_validate_named_facade` on the
  to-store value). `AllOf` walks member extras (AND). `AnyOf` still
  matches one alternative (`_match_one_alternative`; member custom
  skipped). Custom validators on the compose root and AllOf path bounds
  are not re-run.
  Door A stores on `instance.__dict__`. Explicit `__slots__` that include
  the field TypeError at bind. A slots-only class (no `__dict__` in the
  MRO) TypeErrors at bind even when the field name is not a slot.
  Look at `owner.__dict__["__slots__"]`, not inherited `getattr`.
  Get/delete use `_require_instance_dict` like store.
  `@dataclass(slots=True)` is unsupported
  (dataclass replaces the descriptor after bind).
  `@dataclass(frozen=True)` works: dataclass intercepts assign/delete
  with `FrozenInstanceError` before the descriptor mutates.
  `__version__` matches `pyproject.toml`.
- Validator objects compose with `&` / `|` or `AllOf` / `AnyOf`.
  That is object composition, not leaf multiple-inheritance.
- `AttributeValidator` is not shipped. Object-attribute presence checks
  belong at the call site or on `add_validator`.
- `PaymentCardValidator` is brand ∩ Luhn (stdlib `re`; a Luhn-valid
  generator is not enough). Rupay identity is `60` + 14 digits except
  Discover overlap; do not resurrect a dead `6521` alternative.
  `AadhaarCardValidator` is 12-digit identity ∩
  Verhoeff. `PANCardValidator` is identity `fullmatch` ∩ Luhn mod 26
  (complete A–Z; a format-only generator is not enough). `ExpiryValidator`
  is a Door A facade with exclusive `expire_after` / `expire_on` /
  `expire_before`. `expire_on` is valid only on that calendar day.
  `expire_before` is its own bound. `expire_*` are not
  kwargs on `Validator`. No `expiry` path unit.
- Named typed facades call their extra check from `validate()` after the
  inherited path; they do not `add_validator` themselves on each assignment.
  `collect_all=True` continues into that extra check. No NamedOnce Cap.
  `HexColorValidator` is not a public facade. `DateValidator` stores
  `datetime.date`; numeric EU `YYYY-MM-DD` / IND `DD-MM-YYYY` strings parse
  on assignment (`-` `/` `:`, same delimiter both sides). Slash dates are
  IND day-month-year, not US. `DateValidator` rejects `datetime.datetime`.
  Coercing facades (`DateValidator`, `DateTimeValidator`, `UUIDValidator`,
  `PathValidator`, `DecimalValidator`) declare `annotation = T | str` so
  the owner field may be `T`, `str`, or `T | str`. Input `str` is coerced
  in `pre_validation_processing`; the stored value is `T` (named extra
  re-checks that). `IntegerValidator` / `FloatValidator` do not coerce
  `str` — owner `int | str` still TypeErrors at bind.
  `DateTimeValidator` stores `datetime.datetime`; ISO strings parse via
  `datetime.fromisoformat`; plain `datetime.date` is rejected.
  `URLValidator` is a Door A string facade: scheme + netloc
  (stdlib `urllib.parse.urlparse`). Pattern `&` / `|` is fail-closed on missing or mixed
  `str`/`bytes` fragments; inverted `count_min` / `count_max` is
  constructor `ValueError`; bytes patterns keep bytes identity.
- `PhoneNumberValidator` is a Door A facade. Taught kwarg is `region=`
  (required; leftover: valio defaulted to `instance.region` or `"IN"`).
  Engine is optional extra `phonenumbers`; no network. `region` is not a
  kwarg on `Validator`.
- Pattern atoms `Digit` / `Word` / `NonDigit` / `NonWord` / `WhiteSpace`
  / `NonWhiteSpace` share the count-kwargs door on the existing algebra.
  `WordBoundary` stays an atom `\b`. Pattern lives in `ux_valio.pattern`;
  re-export from the package root (`from ux_valio import Pattern`). That is
  not a second door. Thin PatternTypes evidenced in valio@3415c03
  `regexer/regexps.py`: `StartsWith` / `EndsWith` (L414 / L421),
  lookarounds `IfPrecededBy` / `IfNotPrecededBy` / `IfFollowedBy` /
  `IfNotFollowedBy` (L449–L470), `SetOf` char-class (L261). `Contained` /
  `IfContained` are KEEP-absent (they do not exist in valio@3415c03).
  CapturingGroup / WordGroups / scanString / pyparsing / `regexer` package
  stay KEEP-absent.

## Naming

Public Door A names KEEP (valio PatternTypes, `add_*`, `AllOf`,
`Validator`, `Property`). Do not fashion-rename `Digit` / `SetOf` /
`IfPrecededBy`.

New private helpers are verbs that name the action:
`_load_compose_types`, `_register_compose_types`,
`_register_annotation_checker`, `_reject_store_type_mismatch`,
`_reject_store_identity`, `_reject_slots_without_dict`,
`_require_instance_dict`, `_read_from_instance`, `_drop_from_instance`,
`_record_error`, `_store_on_instance`, `_match_one_alternative`,
`_Compose._bind_kwargs`, `_Compose._flatten`, `_Opt.merge`, `_Opt.read`,
`HookHost.bags_used`, `HookHost._install_adders`, `HookHost._collect_bag_keys`,
`_bind_field_logger`, `_take_subscript_annotation`,
`_is_unconstrained_typevar`,
`HookHost._bag_key`, `HookHost._resolve_bag_key`,
`HookHost._owning_class_qualname`, `HookHost._hook_adder`,
`LengthValidator._len_or_reject`, `ChoiceValidator._reject_non_container`.
Do not reintroduce leftover aliases (`_named_extra`, `bound`,
`_namespace`, `merge_opt`, `opt_of`, `hook_bags_used` as a module name).
Noun-only names that hide the action are not
added. Names should fit any Door A caller library — not a one-app
nickname, not a slogan.

Compose bind / flatten / annotation live on `_Compose`. Hook phase table
and adders live on `HookHost`. Origin tables live next to
`is_instance_of`. Specified-theory merge lives on `_Opt`. Errors live at
`ux_valio.errors`. Descriptor does not import `validators`. Do not
reintroduce leftover aliases, `validators/errors.py`, `validators/path.py`,
module `_bag_key` / `_resolve_bag_key` / `_parse_eu_ind_date`,
or hang origin tables on `TypeValidator`.
