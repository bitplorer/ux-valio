# Changelog

## Unreleased

- Every hang API (``pre_validate`` … ``post_delete``, ``task_*``,
  ``add_validator``) is sync and async. Process / ``add_validator``:
  no loop → TypeError; running loop → nest-safe. ``task_*``: isolated
  worker, setter does not wait.

- Descriptor lifecycle is private (``_run_pre_set`` / ``_run_post_set``).
  Hang API is the phase name: ``pre_validate``, ``post_set``, ``task_post_set``.
  Process is the default kind (no ``process_`` prefix). ``add_validator``
  unchanged.

- Hang API compact: ``pre_validate`` / ``task_post_set`` (the
  decorator *is* the add; ``post_set`` stays the descriptor lifecycle).
  ``add_validator`` / ``wait_tasks`` unchanged.

- Intentful names: ``ValidateStep`` (was ``Lookup``), ``_emit_log``,
  ``read_bound``. Test files drop leftover ``door_a`` filenames.

- Docs and module comments name the field default
  (``name: str = StringValidator()``), not "Door A".

- ``namespace=`` accepts the owning class (not only a ``module.qualname``
  str). ``wait_tasks`` is on the package root. ``TypeAliasType`` peels by
  identity.

- HookHost public hang API is ``process_*`` / ``task_*`` /
  ``add_validator`` / ``wait_tasks``. Pipeline runners and ``has_hooks``
  are private (``_pre_validate``, ``_has_hooks``, ``_notify_pre_set``).

- TypedDict hook lookup uses ``__set_name__`` ``_owner`` (no ``_hook_schema``
  sticky state). Qualifiers peel by identity. ``_validate_typed_dict``.

- TypedDict keys accept field-default assignment (``name: str = StringValidator()``)
  and ``@name.process_*`` / ``@name.add_validator`` in that class body.
  ``self`` is the mapping. ``pre_set`` write-back then ``post_set``.

- TypedDict presence is ``__required_keys__`` (``total=`` / ``Required`` /
  ``NotRequired``). ``ReadOnly`` peels with the other qualifiers. Extras on
  an omitted ``NotRequired`` key do not run.

- TypedDict is the schema on the type door (required keys, no extras).
  ``Annotated[T, SomeValidator()]`` on a key runs that field default validator.
  No ``TypedDictValidator`` / Schema twin.
- ``EmailValidator`` and ``URLValidator`` move to ``facades.named``
  (string identity, not primitive store types). ``ExpiryValidator`` stays
  named (timeline extra, not a type).

- Facades import layers: ``typed`` (primitives) under ``named`` (identity
  products). ``typed`` does not import ``named``; named modules do not
  import each other.

- Named identity facades: ``GSTINValidator``, ``IFSCValidator``,
  ``PinCodeValidator``, ``UPIIdValidator``, ``IBANValidator``,
  ``IMEIValidator``. Format ∩ checksum where one exists; no network.

- Package layers: ``errors`` / ``descriptor`` / ``pattern`` / ``validators``
  (the door) / ``facades`` (named products, sibling of the door). The door
  does not import facades.

- Bind uses ``is_subclass_of`` (owner annotation vs validator); set uses
  ``is_instance_of`` (value vs annotation). ``Account | None`` on both
  sides binds. A subclass owner (`Admin(Account)`) binds. Owner wider
  than the validator still TypeErrors.

- Construction is generic: `ValidateProperty.__new__ -> Any` (Pylance) and
  a mypy plugin. No `AsStr` / `AsInt` mixins. A custom store type is
  `class AccountValidator(Validator[Account]): annotation = Account`.

- Typed facades share one TYPE_CHECKING store mixin (`AsStr` / `AsInt` / …)
  in `typed.py`. `store_view.py` is gone. Identity extras use
  `Validator._reject_unless_instance` / `_coerce_str`.

- Omitted `collect_all` and `debug` are True. Pass `False` to opt out.
  Specified-theory is unchanged: omitted stays unspecified so compose with
  explicit `False` does not TypeError. One collected failure re-raises as
  itself; two or more are `ValidationErrors`. Logger stays OFF. `required`
  stays opt-in.

- `name: str = StringValidator()` type-checks without a plugin. Named
  facades present as the store type (`StringValidator <: str`) under
  TYPE_CHECKING. Runtime bases are empty. `User(name=1)` still errors.
- `task_*` is background: setter does not wait. Sync or async. Isolated
  pool (not nest-safe, not the caller's loop). Errors record on the host;
  they do not fail the set. Persist/reserve hang on `post_set`.
  `HookHost.wait_tasks()` waits for tests/shutdown.
- Hook names are `process_{phase}` and `task_{phase}`. Process
  transforms (return is stored only inside `pre_set`). Task is background.
  Persist hangs on `post_set`. Retired: `add_pre_validator`,
  `add_post_set`, `add_*_task` suffix.
- `_Of.__init__` takes `debug=`, `default=`, `logger=` (same names as
  `Property`). No `kwargs.pop("debug")`. `_Opts` is a dataclass: `merge` /
  `overlay` / `keeps_nesting` follow its fields. `_Opts.from_call` is the
  constructor. `_Opt.merge` takes `what=` only for the error label.
- Specified-theory is `_Opts` with named fields (`debug`, `logger`, …),
  not a string-keyed dict. Compose merge / flatten-keep live there.
  `_Of` only walks members.
- `ValidateProperty` inherits `HookHost`. `Validator` and `_Of` no longer
  list it. `add_*` is on every validating descriptor. `_Of` stays — it is
  the member list, not a second HookHost.
- `AllOf` / `AnyOf` live next to `&` / `|` on `ValidateProperty`. No
  `compose.py`, no `_register_compose_types` cache. Validator is still
  not AllOf — two kinds of descriptor root, one pair of bases.
- `ValidationPath` lives on the facade (callables, not string unit names).
  No `validation_path.py`. Compose `pre_*` / `post_*` call member methods
  directly — no `getattr(item, method)`.
- Hook registries initialize in `HookHost.__init__` (cooperative
  `super()`). `_register` takes the phase dict, not a string `getattr`.
- `add_*` hooks are declared methods on `HookHost` (valio did the same).
  No `_HOOK_ADDERS` table / `_install_adders` setattr. Phases are the
  `_processors` dict keys.
- Owner key is `module.qualname` (`HookHost._owner_key`). Runtime errors
  name the field / `__dict__` / bind, not "field default". `has_hooks` replaces
  `bags_used`.
- Dropped `cache_task=` (valio leftover: id(tasks) cache, stored never
  consulted). Unknown-kwarg TypeError, same as `enable_async`.
- Aadhaar / PAN / payment-card print forms canonicalize on assignment:
  grouping spaces/hyphens strip; PAN letters upper-case. Stored value is
  the compact identity; extra checks still Verhoeff / Luhn mod 26 / brand∩Luhn.
- Named-facade identity helpers live on the facade (`AadhaarCardValidator`,
  `PaymentCardValidator`, `PANCardValidator`, `ExpiryValidator`,
  `PhoneNumberValidator`). Slot helpers live on `Property`. Brand /
  Verhoeff / PAN tables stay module data next to the class.
- `Validator[T]` is the stored-type subscript. `Validator[int]()` fills
  `annotation` (plain class, unbound `.validate`). Owner `n: int` must
  agree. Unconstrained TypeVars are typing-only; bound TypeVars still
  check. Named facades specialize (`IntegerValidator` is `Validator[int]`).
- Hook bag-key helpers (`_bag_key`, `_resolve_bag_key`, …) live on
  `HookHost`. Date parse lives on `DateValidator._parse_eu_ind_date`.
- `ValidationErrors` lives at `ux_valio.errors`. Descriptor no longer
  imports the validators package (store door does not depend on validate
  door).
- Primitive typed facades (`IntegerValidator`, `StringValidator`,
  `BooleanValidator`) live in `typed.py` with the rest. `facade.py` is
  only `Validator`.
- Facade unit list renamed `validators/path.py` → `validation_path.py`
  so it is not confused with `PathValidator`.
- Compose bind cache is `_AllOf` / `_AnyOf` only (dropped the third
  `_compose_types` store).
- Origin tables `_ORIGIN_CHECKERS` / `_ORIGIN_GROUPS` sit next to
  `is_instance_of`, not on `TypeValidator`.
- Coercing facades declare `T | str`: owner annotation may be `T`, `str`,
  or the union. Input `str` is coerced; stored value is `T` (named extra).
  `DecimalValidator` coerces Decimal strings (float still rejected).
- Dropped leftover aliases that were not the usage pattern:
  `_namespace`, `hook_bags_used`, `merge_opt`, `opt_of`, `bound`,
  `_named_extra`, module `_collect_bag_keys`, module `_len_or_reject`.
- Class access records `_owner`: a shared descriptor's
  `Person.aadhaar.add_*` bags under Person, not the last `__set_name__`.
- `@dataclass(frozen=True)` is supported (dataclass intercepts
  assign/delete). `@dataclass(slots=True)` stays unsupported.
- `LengthValidator._len_or_reject` and `HookHost._collect_bag_keys` live
  on the owning type.
- Email identity peels `PatternType` the same way as findall (no
  `hasattr` dance).
- Hang `add_*` on the field name: `@username.pre_validate` in the
  class body, no outer `username_field` twin, no Field mixin. Class
  access returns the descriptor so `Cls.field.add_*` works after bind.
  Dataclass default is that descriptor; `__set__` treats `value is self`
  as unset and applies `default` / `default_factory`.
- Hook lookup walks the instance MRO (base first). A child dataclass
  runs parent field hooks. A free function on a bound field uses the
  bound owner as the bag key.
- Field logger: `logger=True` binds a stdlib `logging.Logger` at
  `__set_name__` named `module.qualname.field`. No files. `logger=False`
  (default) stays OFF. `logger=None` is OFF. Get/set/delete log at info;
  failures at error. Specified-theory still sees `True` after bind.
- Length bounds TypeError a non-sized value with a named message
  (`expect a sized value`), not raw `len()`.
- `in_choice` / `not_in_choice` that are not a `Container` TypeError at
  construct (`ChoiceValidator._reject_non_container`).
- `EmailValidator` identity `fullmatch` reuses `PatternValidator._compiled_finder`.
- `DateTimeValidator` (ISO `datetime.datetime`) and `URLValidator`
  (scheme + netloc) named facades. `DateValidator` still rejects `datetime`.
- Origin groups live on `TypeValidator._ORIGIN_GROUPS` with the origin table.
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
- Annotation is a store invariant after `post_validate`. Named-facade
  extra is the same class of invariant (`_reject_store_identity`):
  post_validate cannot smuggle `"not-an-email"` onto `EmailValidator` or
  a `datetime` onto `DateValidator`. `AllOf` walks member extras; `AnyOf`
  still matches one alternative. Path bounds on AllOf / unnamed facades
  and custom validators are not re-run.
- Explicit `__slots__` on a descriptor field TypeError at bind. A slots-only
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
  fakes, validated dataclasses, and a service that injects ports in the
  constructor. Signup (`collect_all_form.py`) is complete auth. Hasher stays
  in the example (`Pbkdf2PasswordHasher`). Examples do not ship a DB driver.
- Pattern atom names KEEP the valio@3415c03 PatternType surface.
  `Contained` / `IfContained` are KEEP-absent.
- CI: pytest on push/PR (Python 3.14).
- Taught field-default path is a facade or `Validator` (not bare `Property`);
  leaf `&` is advanced; `Chain` is `AllOf`.

## 0.1.0

- field-default descriptor-on-dataclass validation.
- Validators live in `ux_valio/validators/` with leaf-owned length/value
  methods (not a free-function owned API).
- Validator objects compose with `&` / `|` and `AllOf` / `AnyOf` / `Chain`.
- Public Min/Max length and value leaves; typed facades for float, Decimal,
  bytes, date, email, UUID, path, IP, and enum.
- `AttributeValidator` is not shipped.
- Async `add_*` registers; nest-safe worker bridge; no `asyncio.run` in
  `__set__`.
