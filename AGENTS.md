# AGENTS.md

Door A only: `field: T = SomeValidator(...)`.

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
  never-set `__get__` / `__delete__` with `debug=True` is named
  `AttributeError`, not bare `KeyError`;
  Pattern `findall` (empty-match `a*` is a match; Email extra is fullmatch);
  facades do not multiple-inherit concern leaves;
  path fail-closed; processors then tasks once;
  `pre_set` hook IS the validate pipeline (no processor bag named `pre_set`);
  before-store hangs on `add_pre_validator` / `add_validator` /
  `add_pre_validator_task`; `add_*` accepts async def and coroutine
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
  once via `_register_annotation_checker`.
  `not_in_choice` skips `None`, same as `in_choice`.
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
  Pattern `&` / `|` is fail-closed on missing or mixed
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
`_record_error`, `_store_on_instance`, `_match_one_alternative`.
Leftover aliases when a private name was taught (`_named_extra`,
`bound`, `_namespace`). Noun-only names that hide the action are not
added. Names should fit any Door A caller library — not a one-app
nickname, not a slogan.
