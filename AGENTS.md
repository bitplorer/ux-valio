# AGENTS.md

Handbook is `docs/` (Diátaxis: tutorial, how-to, reference, explanation).
README is the PyPI front door. Optional `mkdocs serve` (`ux-valio[docs]`).

Field default only: `field: T = SomeValidator(...)`.

Layout is an **import graph** (layers) plus **sibling packages** (parallel
subsystems). Lower layers never import higher. Parallel products sit in
a parallel folder, not inside the layer they depend on.

- `ux_valio/errors.py` — `ValidationErrors` (layer 0, shared).
- `ux_valio/descriptor.py` — `Property` (store). Imports `errors`, never
  `validators` or `facades`.
- `ux_valio/pattern/` — pattern algebra. Independent sibling of the store.
- `ux_valio/validators/` — validate door (`ValidateProperty` : `Property`):
  `base` → `ValidateProperty` (`HookHost` + `Property`) and `AllOf` /
  `AnyOf` (the operators); `hooks` → `HookHost` (inherited by
  `ValidateProperty`); `leaves` / `length` / `value` → concern leaves
  (parallel, compose with `&` / `|`, no leaf MI); `facade` →
  `Validator`. Does not import `facades`.
  Facade unit list is `ValidationPath` on `Validator` in `facade.py`,
  not `PathValidator` (`facades/typed.py`, pathlib).
- `ux_valio/facades/` — field-default products, two layers:
  `typed.py` — primitives (`IntegerValidator`, `StringValidator`, …) :
  `Validator`. `named/` — identity products, **sibling domain modules**
  (parallel, do not import each other): `india/` is a folder of layers
  (`kyc`, `gst`, `registry`, `bank`, `postal` — they do not import each other);
  `us/` (`postal`, `bank`, `market`, `kyc`); `uk/` (`postal`, `bank`, `kyc`);
  `canada/` (`postal`, `kyc`); `mexico/` (`bank`, `kyc`);
  `finance/` is international only (`rail` IBAN/BIC, `market` ISIN/LEI,
  `card`, `currency`);
  `catalog` (ISBN/ISSN/EAN/GTIN/VIN),
  `contact` (email/phone/URL/hostname), `device` (IMEI/MAC),
  `portal` (slug/country/timezone/ULID/locale/semver), `expiry` (wall-clock).
  Each domain module subclasses `StringValidator` (expiry : `Validator`).
  `named` does not import sibling named modules. `typed`
  does not import `named`.
  Construction is `Any` to type checkers (`ValidateProperty.__new__`;
  mypy plugin `ux_valio.mypy_plugin`) so any store type works — no
  `AsStr` / `AsUser` mixin. Set `annotation` on the facade.
  Bind: `is_subclass_of(owner, validator)`. Set: `is_instance_of(value,
  annotation)`. Optional is `| None` on both sides.
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
- Optional native apply (PyO3 peer, host decides / peer applies) is
  **not** a second door. Soul of the instance stays Python. See
  `docs/explanation/host-peer-plan.md`. Measure tip:
  `python benches/measure_host_peer.py` (CI ``--ci`` skips without Rust).
  The recorded switch test PASSed (host setattr several times slower
  than native Integer / Float bound apply, String / Bytes length apply,
  IntegerEnum member-set apply, StringEnum UTF-8 member-set apply,
  Boolean exact-bool type-door apply, Decimal exact-Decimal
  type-door apply, Date ``datetime.date`` type-door apply,
  DateTime ``datetime.datetime`` type-door apply,
  Uuid ``uuid.UUID`` type-door apply,
  IP string-identity apply, and
  Path ``pathlib.Path`` type-door apply).
  Optional extra
  ``ux-valio[native]`` (sibling crate ``native/``, module
  ``ux_valio_native``) binds closed Integer and Float bound plans,
  closed String and Bytes length plans, a closed IntegerEnum
  member-set plan, a closed StringEnum UTF-8 member-set plan, a
  closed Boolean type door, a closed Decimal type door, a closed
  Date type door, a closed DateTime type door, a closed
  Uuid type door, a closed IP string-identity plan, and a closed
  Path type door at
  construct. Private ``Plan`` is one variant per family (no mixed
  ``Unit`` bag): Integer / Float own ``BoundUnit`` (shared
  ``scalar_miss`` / ``compile_bound_plan``), String / Bytes own
  ``LengthUnit``, IntegerEnum / StringEnum own their member sets,
  Boolean / Decimal / Date / DateTime / Uuid / Path are type-door
  markers, IP owns an address kind (``ipv4`` / ``ipv6`` / ``ip``). Checks stay
  ``MinValue`` / ``MaxValue`` / ``GreaterThan`` / ``LessThan`` /
  ``Equal`` and min+max range, plus ``MinLength`` / ``MaxLength`` /
  ``Length``, plus the IntegerEnum ``i64`` set, plus StringEnum UTF-8
  members, plus Boolean exact ``bool``, plus Decimal exact
  ``decimal.Decimal``, plus Date ``datetime.date``, plus DateTime
  ``datetime.datetime``, plus Uuid exact ``uuid.UUID``,
  plus IP string identity (``IPv4Address`` / ``IPv6Address`` /
  ``ip_address`` on the given ``str``), plus Path exact
  ``pathlib.Path``,
  compile once, one FFI
  ``apply_integer`` / ``apply_float`` / ``apply_string`` / ``apply_bytes`` /
  ``apply_integer_enum`` / ``apply_string_enum`` / ``apply_boolean`` /
  ``apply_decimal`` / ``apply_date`` / ``apply_datetime`` /
  ``apply_uuid`` / ``apply_ip`` / ``apply_path`` per set. Integer type door is FFI
  ``i64`` extract; Float is FFI ``f64`` extract (IEEE Door A: NaN
  unordered on min/max/gt/lt, ``eq`` uses ``!=`` so NaN never
  matches). Bound miss arms are fail-when: ``min_value`` passes when
  ``value >= min`` (miss ``<``); ``gt`` passes when ``value > gt``
  (miss ``<=``, exclusive); ``max_value`` passes when ``value <= max``
  (miss ``>``); ``lt`` passes when ``value < lt`` (miss ``>=``,
  exclusive); ``eq`` misses on ``!=``. Inclusive is ``min_value`` /
  ``max_value``; exclusive is ``gt`` / ``lt``. String type door is FFI
  ``&str`` extract; length is
  ``len(str)`` codepoints. Bytes type door is FFI ``&[u8]`` extract;
  length is ``len(bytes)``. IntegerEnum type door is host
  ``isinstance`` of the concrete ``enum.IntEnum``, then FFI ``i64``
  extract; membership is exact equality with the compiled member
  values. StringEnum type door is host ``isinstance`` of the concrete
  str-valued ``enum.Enum``, then FFI ``&str`` extract of ``.value``;
  membership is exact UTF-8 equality (no casefold, no NFC).
  Boolean type door is host ``isinstance`` of ``bool``, then FFI
  ``bool`` extract (``compile_boolean`` / ``apply_boolean``). Exact
  ``bool`` only: ``1`` / ``0`` are not coerced. ``True`` and ``False``
  both pass. Extra units on ``BooleanValidator`` stay on the host.
  Decimal type door is host ``isinstance`` of ``decimal.Decimal``, then
  FFI Decimal extract (``compile_decimal`` / ``apply_decimal``, on
  ``_DECIMAL_DOOR``). Stored type is ``decimal.Decimal`` only after
  host ``_pre_validate``. ``_coerce_str`` stays host (peer never sees
  raw ``str``). Reject ``float`` / ``int`` / ``bool`` (no silent
  float→Decimal, no ``Decimal(float)`` on this door). Exact
  ``Decimal`` including ``Decimal("0")`` passes. No ``max_digits`` /
  ``decimal_places`` / ``quantize`` scale units. Quantize / scale /
  context / rounding stay HOLD / host. Bounds (min/max/gt/lt/eq) stay
  host. Extract miss is a bridge to host ``TypeValidator``. ``None``
  skips. ``Decimal | None`` and other unions stay host. The facade
  coerce annotation ``decimal.Decimal | str`` is the host coerce door.
  Extra units on ``DecimalValidator`` stay on the host.
  Date type door is host ``isinstance`` of ``datetime.date``, then
  FFI date extract (``compile_date`` / ``apply_date``, on
  ``_DATE_DOOR``). Stored type is ``datetime.date`` only after
  host ``_pre_validate`` (EU ``YYYY-MM-DD`` / IND ``DD-MM-YYYY``).
  The peer never sees a raw ``str``. ``datetime.datetime`` extracts
  on this door because it subclasses ``date``; ``DateValidator``
  still rejects it in the named extra. ``int`` / ``bool`` / raw
  ``str`` miss when the annotation is exact ``date``. Exact
  ``datetime.date`` passes. Bounds (min/max/gt/lt/eq) stay host.
  Extract miss is a bridge to host ``TypeValidator``. ``None``
  skips. ``date | None`` and other unions stay host. The facade
  coerce annotation ``datetime.date | str`` is the host coerce door.
  Extra units on ``DateValidator`` stay on the host.
  DateTime type door is host ``isinstance`` of ``datetime.datetime``,
  then FFI datetime extract (``compile_datetime`` /
  ``apply_datetime``, on ``_DATETIME_DOOR``). Stored type is
  ``datetime.datetime`` only after host ``_pre_validate`` (ISO
  ``fromisoformat``). The peer never sees a raw ``str``. A plain
  ``datetime.date`` misses. Exact ``datetime.datetime`` passes,
  including aware values. Bounds stay host. Extract miss is a
  bridge to host ``TypeValidator``. ``None`` skips.
  ``datetime | None`` and other unions stay host. The facade coerce
  annotation ``datetime.datetime | str`` is the host coerce door.
  Extra units on ``DateTimeValidator`` stay on the host.
  Uuid type door is host ``isinstance`` of ``uuid.UUID``, then
  FFI UUID extract (``compile_uuid`` / ``apply_uuid``, on
  ``_UUID_DOOR``). Stored type is ``uuid.UUID`` only after
  host ``_pre_validate`` (``uuid.UUID`` on a string). The peer
  never sees a raw ``str``. ``int`` / ``bool`` / ``bytes`` / raw
  ``str`` miss when the annotation is exact ``uuid.UUID``. Exact
  ``uuid.UUID`` passes, including the nil UUID. Bounds
  (min/max/gt/lt/eq) stay host. Extract miss is a bridge to host
  ``TypeValidator``. ``None`` skips. ``uuid.UUID | None`` and other
  unions stay host. The facade coerce annotation ``uuid.UUID | str``
  is the host coerce door. Extra units on ``UUIDValidator`` stay on
  the host.
  IP string identity is host ``isinstance`` of ``str``, then FFI
  ``&str`` extract (``compile_ip`` / ``apply_ip``, on
  ``_IP_DOOR``). Living facades are ``IPv4Validator`` /
  ``IPv6Validator`` / ``IPAddressValidator``. They store the given
  string. There is no ``_pre_validate`` coerce to ``ipaddress``
  objects. ``IPv4Address`` / ``IPv6Address`` / ``ip_address`` are
  the parsers the kind mirrors (``ipv4`` / ``ipv6`` / ``ip``).
  Exact strings those parsers accept pass, including ``::``,
  IPv4-mapped IPv6, and a scoped ``fe80::1%eth0``. The stored
  value is that string, not a compressed form. ``int`` / ``bytes``
  / ``ipaddress`` objects miss the type door. Invalid strings are
  ``FailKind.NotIp``; the host formats the KEEP ``ValueError``.
  Extract miss on a ``str`` bridges to that same parser. ``None``
  skips. Extra units (length, pattern, choice, ``required``,
  ``reassign=False``) stay on the host. ``StringValidator`` is not
  this door.
  Path type door is host ``isinstance`` of ``pathlib.Path``, then
  FFI Path extract (``compile_path`` / ``apply_path``, on
  ``_PATH_DOOR``). Stored type is ``pathlib.Path`` only after
  host ``_pre_validate`` (``pathlib.Path`` on a string). The peer
  never sees a raw ``str``. ``int`` / ``bool`` / ``bytes`` /
  ``pathlib.PurePath`` / raw ``str`` miss when the annotation is
  exact ``pathlib.Path``. Exact ``pathlib.Path`` passes, including
  a subclass (``PosixPath`` is a ``Path``). No resolve, no
  absolute, no filesystem check. ``path_exists`` stays the named
  extra (``FileNotFoundError``). Bounds (min/max/gt/lt/eq),
  length, choice, ``required``, and ``reassign=False`` stay host.
  Extract miss is a bridge to host ``TypeValidator``. ``None``
  skips. ``pathlib.Path | None`` and other unions stay host. The
  facade coerce annotation ``pathlib.Path | str`` is the host
  coerce door. Extra units on ``PathValidator`` stay on the host.
  Cap Door B off. Plain Enum / Pattern stay off.
  ``compile_*`` and ``apply_*`` stay separate doors. Host bind walks
  one family list (``_FAMILY_DOORS``; each row is a private
  ``_FamilyDoor`` of ``closed`` / ``compile`` / ``apply`` / ``run`` /
  ``extract``, plus ``expected`` / ``type_miss`` / ``bridge`` /
  ``extract_errors`` when apply is ``_run_closed``). Bind calls
  that row's ``_select``. There is no per-family ``_select_*``.
  Do not merge a pair into one door and do not restore a
  per-family copy of the bind steps.
  ``Validator.__init__`` seeds ``_native_plan`` / ``_native_apply`` /
  ``_native_fail_kind`` / ``_native_run`` as ``None`` before
  ``bind_native_plan`` (same four slots ``_clear_native`` clears).
  The four slots are plan | apply (Rust FFI) | run (Python closed
  entry) | fail_kind. Product-PyO3 Rust door stays ``_native_apply``.
  Closed-family Python door is ``_native_run`` bound to
  ``_FamilyDoor._run_closed``. StringEnum sets
  ``extract=attrgetter("value")`` so apply receives the member
  string. There is no ``apply_native_string_enum``.
  Reclaim ``_native_apply`` only together with ``_native_run``;
  alone it undoes the split.
  Ownership is on ``Validator`` once — do not scatter those assigns on
  typed facades. ``bind_native_plan`` / ``_clear_native`` remain the
  writers; ``__set_name__`` rebinds when ``_native_plan is None``. Host
  ``_native.py`` stays one file. Each Door A family is one contiguous
  section (closed detector — ``partial`` of a shared helper when the
  args are constants — family-only helpers, the ``_FamilyDoor`` row).
  No ``apply_native_*`` shell in front of ``_run_closed``.
  ``_closed_type_door`` and
  ``_run_closed`` are defined outside those sections, with the
  other shared detectors and bridges. ``_FAMILY_DOORS`` stays
  outside too. A private module is allowed only when
  opening that file shows one family's walk and nothing else.
  ``_FamilyDoor`` is the private frozen bind row, not a class-per-type
  product surface. Do not mirror
  Rust ``plan`` / ``bound`` / ``length`` into ``_native_closed.py`` /
  ``_native_apply.py``. Tests are ``tests/test_native_layout.py`` (public ``compile_*`` /
  ``apply_*`` presence, bare ``compile`` / ``apply`` absence,
  cross-family ``RuntimeError``, Cap OFF, plain Enum / Pattern HOLD) plus
  ``tests/test_native_<family>.py``. Helpers live in
  ``tests/native_support.py``. Do not recombine
  ``tests/test_native_peer.py``. Open
  TypeValidator / plain EnumValidator stay on the host.
  Stdlib Python apply stays the
  default without the extra. Do not add a Schema/Field twin to get it.
  Cap / cek-runtime / Cap Door B stay out of this repo. Do not claim
  the switch-test ratio as end-to-end product setattr.
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
  processors then tasks once (tasks spawn; setter does not wait);
  `_run_pre_set` IS the validate pipeline (no processor bag named `pre_set`);
  Hang `pre_validate` / `post_set` / `validator` / `task_*` on the field name (`@username.pre_validate` in the
  class body). Those methods live on `ValidateProperty` (facade, leaf, or
  AllOf / AnyOf). Class access returns the descriptor (`Cls.field.pre_validate`
  after bind) and records that class as `_owner`, so a shared
  descriptor's `Person.aadhaar.pre_validate` uses Person, not the last
  `__set_name__`. Dataclass default is that descriptor; `__set__`
  treats `value is self` as unset. No Field mixin, no outer
  `username_field` twin unless sharing one descriptor across classes.
  Lookup for get/delete walks the instance MRO (base first) so a child
  runs parent hooks. Set-phase hangs (`pre_validate`, `post_validate`,
  `post_set`, `validator`, and their `task_*`) compile to
  `_closed[owner]`: an MRO-flattened ordered tuple (base first) plus
  `task_*`. Open buckets stay the source of truth. `_register` and
  native plan bind/clear call `_recompile_closed`; `__set_name__` may
  warm-bake. `__set__` looks up `_closed[type(obj)]` and runs that list.
  A miss is fail-closed when any set-phase hang exists. With no
  set-phase hang the straight line is unchanged. Assignment does not
  walk open MRO. No new public hang API. Hangs stay Python.
  A free function on an unbound descriptor still needs `namespace=`
  (the owning class, or its `module.qualname` str);
  on a bound field the owner key is the bound owner.
  `pre_validate` / `task_*` accept async def and coroutine
  results (no `_reject_coroutine_result`);
  sync path with no running loop TypeError names the missing loop / helper;
  running loop uses the process-held nest-safe worker bridge.
  Re-entering that worker is TypeError (would deadlock), not a hang.
  `enable_async` is not a door (unknown-kwarg TypeError).
  `cache_task` is not a door (unknown-kwarg TypeError). valio's
  id(tasks) cache is retired, not stored.
  `collect_all` omitted is True (continue remaining concerns). One
  collected failure re-raises as itself; two or more are `ValidationErrors`.
  `collect_all=False` is fail-fast. Omitted `debug` is True (re-raise);
  `debug=False` swallows. Do not overload `debug` into
  collect-all. Specified default-path units bind at construct
  (`_active_units`; type always). Hang `pre_validate` on the field default. Compose merge fail-closed: conflicting
  specified `debug` / `default` / `default_factory` / `collect_all` /
  `logger` is TypeError.
  Explicit `False` is specified. Omitted `collect_all` / `logger` / `debug`
  still collapse to a specified `True`.
  Unresolved owner `str` / `ForwardRef` annotations TypeError at bind
  (not copied, not eval'd). Owner annotation that is a Property class
  (`StringValidator` / `Validator[str]`) peels to the store type.
  `name: str = StringValidator()` type-checks: construction is `Any`
  (`ValidateProperty.__new__`, mypy plugin). No per-type mixin.
  `AnyOf` does not AND-gate root type; `AllOf`
  keeps annotation-conflict TypeError. Unknown path unit is `ValueError`.
  TypedDict is the schema: ``__required_keys__`` (``total=`` / ``Required`` /
  ``NotRequired``), extra keys fail-closed, values via ``is_instance_of``.
  ``Annotated[T, SomeValidator()]`` or field-default assignment
  (`name: str = StringValidator()`) on a TypedDict key; hang
  ``@name.pre_validate`` / ``@name.validator`` in that class body (``self`` is the mapping).
  No Schema / Field / BaseModel twin. Omitted ``NotRequired``
  keys skip extras. ``ReadOnly`` peels like the other qualifiers.
  Callable
  origin is checked; signature is not. Generic subclass instance params
  are not inspected.
  `&` / `|` return `AllOf` / `AnyOf` from the same module
  (`ValidateProperty.__and__` / `__or__`). Do not reintroduce a compose
  module or `_register_compose_types` lazy cache. `leaves.py` binds `is_instance_of`
  once via `_register_annotation_checker`, and `_validate_typed_dict` once via
  `_register_typed_dict_checker` (`_validate_typed_dict_fn`). `_validate_type`
  does not import `leaves` on each call. The fallback import stays in
  `_run_typed_dict_check` / `_annotation_accepts` because `leaves` imports
  `base`. Origin tables `_ORIGIN_CHECKERS`
  / `_ORIGIN_GROUPS` live next to `is_instance_of`, not on `TypeValidator`.
  `not_in_choice` skips `None`, same as `in_choice`.
  `in_choice` / `not_in_choice` that are not a ``Container`` TypeError at
  construct, not at assignment.
  Unsized ``len()`` on a length bound is a named TypeError
  (``expect a sized value``), not the raw ``object of type 'int' has no len()``.
  `EmailValidator` identity fullmatch uses the same compiled pattern as
  the findall path (``PatternValidator._compiled_finder``).
  Host regex cache is the pair ``_pattern_source`` (source string or
  unset sentinel) and ``_pattern_compiled`` (cached ``re.Pattern``) on
  both ``Validator`` and ``PatternValidator``. That cache is unrelated
  to native ``compile_*`` / ``apply_*``. Do not fold it into public
  ``pattern``. Do not use ``_pattern_compiled_source``.
  `post_get` in `__get__` `finally` records a secondary error and does
  not replace an in-flight exception.
  Annotation is a store invariant: `post_validate` may transform,
  then `_reject_store_type_mismatch` TypeErrors a value that would not
  pass the type door. Named-facade extra is the same class of invariant
  (`_reject_store_identity` re-runs `_validate_named_facade` on the
  to-store value). `AllOf` walks member extras (AND). `AnyOf` still
  matches one alternative (`_match_one_alternative`; member custom
  skipped). Custom validators on the compose root and AllOf path bounds
  are not re-run.
  The descriptor stores on `instance.__dict__`. Explicit `__slots__` that include
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
  There is no `Chain` alias.
- `AttributeValidator` is not shipped. Object-attribute presence checks
  belong at the call site or on `validator`.
- `PaymentCardValidator` is brand ∩ Luhn (stdlib `re`; a Luhn-valid
  generator is not enough). Rupay identity is `60` + 14 digits except
  Discover overlap; do not resurrect a dead `6521` alternative.
  `AadhaarCardValidator` is 12-digit identity ∩
  Verhoeff. UIDAI 4-4-4 / hyphen print forms strip to 12 digits on
  assignment (stored value is the compact identity). `PANCardValidator`
  is identity `fullmatch` ∩ Luhn mod 26
  (complete A–Z; a format-only generator is not enough). Letters
  case-fold to A–Z; grouping spaces/hyphens strip. `PaymentCardValidator`
  is brand ∩ Luhn; printed grouping spaces/hyphens strip to the compact
  number. `ExpiryValidator`
  is a field-default facade with exclusive `expire_after` / `expire_on` /
  `expire_before`. `expire_on` is valid only on that calendar day.
  `expire_before` is its own bound. `expire_*` are not
  kwargs on `Validator`. No `expiry` path unit.
  `BICValidator` is ISO 9362 (8/11). `ISINValidator` is ISO 6166 ∩ Luhn.
  `ISBNValidator` is ISBN-10 (mod 11, ``X``) or ISBN-13 (978/979 ∩ EAN).
  `EANValidator` is 13-digit GS1. `VINValidator` is ISO 3779 (no I/O/Q).
  `MACAddressValidator` stores 12 uppercase hex digits. `TANValidator` /
  `CINValidator` / `VoterIdValidator` are format identities (no portal).
  E-commerce / SaaS: `GTINValidator` (8/12/13/14), `HostnameValidator`,
  `SlugValidator` (does not slugify), `CurrencyCodeValidator` (ISO 4217),
  `CountryCodeValidator` (ISO 3166-1 alpha-2), `TimezoneValidator`
  (IANA / ``zoneinfo``), `ULIDValidator`, `LEIValidator`,
  `CardExpiryValidator` (MMYY print form, not ``ExpiryValidator``),
  `HSNCodeValidator`, `ABARoutingValidator`, `UdyamValidator`,
  `DINValidator`, `LLPINValidator`, `FSSAIValidator`,
  `IndianPassportValidator`. Aadhaar first digit is 2–9 (UIDAI).
  `GSTINValidator` state is ``01–38`` plus ``97`` / ``99``.
  `PaymentCardValidator` includes UnionPay (``62`` + 14–17 digits) without
  resurrecting Rupay ``6521``.
  All stdlib, no network.
- Named typed facades call their extra check from `validate()` after the
  inherited path; they do not hang ``validator`` themselves on each assignment.
  `collect_all=True` continues into that extra check. No NamedOnce Cap.
  `HexColorValidator` is not a public facade. `DateValidator` stores
  `datetime.date`; numeric EU `YYYY-MM-DD` / IND `DD-MM-YYYY` strings parse
  on assignment (`-` `/` `:`, same delimiter both sides). Slash dates are
  IND day-month-year, not US. `DateValidator` rejects `datetime.datetime`.
  Coercing facades (`DateValidator`, `DateTimeValidator`, `UUIDValidator`,
  `PathValidator`, `DecimalValidator`) declare `annotation = T | str` so
  the owner field may be `T`, `str`, or `T | str`. Input `str` is coerced
  in `_pre_validate`; the stored value is `T` (named extra
  re-checks that). `IntegerValidator` / `FloatValidator` do not coerce
  `str` — owner `int | str` still TypeErrors at bind.
  `DateTimeValidator` stores `datetime.datetime`; ISO strings parse via
  `datetime.fromisoformat`; plain `datetime.date` is rejected.
  `URLValidator` is a string field default: scheme + netloc
  (stdlib `urllib.parse.urlparse`). Pattern `&` / `|` is fail-closed on missing or mixed
  `str`/`bytes` fragments; inverted `count_min` / `count_max` is
  constructor `ValueError`; bytes patterns keep bytes identity.
- `PhoneNumberValidator` is a field-default facade. Taught kwarg is `region=`
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

Public names KEEP (valio PatternTypes, `pre_validate` / `task_*` / `validator`, `AllOf`,
`Validator`, `Property`). Do not fashion-rename `Digit` / `SetOf` /
`IfPrecededBy`. Modules are snake_case (`async_bridge`).
Classes are CapWords. Methods/helpers are snake_case verbs. The public
stored-type param is `Validator[T]`; `Property` uses `_StoreT`.
`in_choice` / `not_in_choice` are valio names
on the facade — do not fashion-rename them.

New private helpers are verbs that name the action:
`_register_annotation_checker`, `_register_typed_dict_checker`,
`_run_typed_dict_check`, `_reject_store_type_mismatch`,
`_reject_store_identity`, `_reject_slots_without_dict`,
`_require_instance_dict`, `_read_from_instance`, `_drop_from_instance`,
`_record_error`, `_store_on_instance`, `_match_one_alternative`,
`_Of._flatten`, `_Opts.merge`, `_Opts.from_call`, `_Opts.overlay`,
`_Opt.merge`, `_Opt.keeps_nesting`,
`HookHost._has_hooks`, `HookHost.wait_tasks`, `HookHost._pre_validate`,
`Property._run_pre_set`, `Property._run_post_set`,
`HookHost._notify_pre_set`, `HookHost._collect_owner_keys`, `HookHost._register`,
`_bind_field_logger`, `_emit_log`, `_take_subscript_annotation`,
`_is_unconstrained_typevar`,
`HookHost._owner_key`, `HookHost._resolve_owner_key`,
`HookHost._owning_class_qualname`,
`Property._slot_names`, `Property._owner_omits_instance_dict`,
`DateValidator._parse_eu_ind_date`, `ExpiryValidator._parse_expiry_datetime`,
`AadhaarCardValidator._is_valid_aadhaar`,
`PaymentCardValidator._is_valid_payment_card`,
`PANCardValidator._is_valid_pan`,
`PhoneNumberValidator._require_phonenumbers`,
`LengthValidator._len_or_reject`, `ChoiceValidator._reject_non_container`,
`read_bound`, `ValidateStep`,
`bind_native_plan`, `apply_native_bounds`, `_extract_same`,
`_load_native`, `_closed_integer_enum_members`,
`_closed_string_enum_members`, `_closed_ip`,
`_read_ip_facade`, `_reject_ip_string`, `_bridge_to_ip`,
`_skip_native_ip_extra`, `_run_with_native_ip_extra_skip`,
`_is_decimal_type_annotation`,
`_is_date_type_annotation`, `_is_datetime_type_annotation`,
`_is_uuid_type_annotation`,
`_is_path_type_annotation`,
`_is_stored_or_str_annotation`,
`_closed_length`, `_closed_value_bounds`, `_closed_type_door`, `_bind_compiled_plan`,
`_clear_native`, `_bridge_to_value`, `_bridge_to_length`, `_bridge_to_type`,
`_raise_native_bound_miss`, `_raise_host_value_type_miss`,
`_raise_host_length_type_miss`,
`_raise_host_boolean_type_miss`, `_raise_host_type_door_miss`,
`_raise_host_enum_type_miss`, `_raise_host_closed_type_miss`,
`_read_owner_annotation`,
`_ClosedPair`,
`_FamilyDoor`, `_FamilyDoor._select`, `_FamilyDoor._run_closed`,
`Validator._apply_specified_path`.
Do not reintroduce leftover aliases (`_named_extra`, `bound`,
`_namespace`, `merge_opt`, `opt_of`, `hook_bags_used` as a module name,
`cache_task`, `_HOOK_ADDERS`, `_install_adders`, `_hook_adder`,
`add_pre_validator`, `add_post_set`, `add_pre_validator_task`,
`add_post_set_task`, `has_hooks`, `pre_validation_processing`,
`post_set_processing`, `notify_pre_set`, `on_pre_set`,
`add_pre_validate_process`, `add_pre_validate`, `add_validator`, `process_pre_validate`, `add_task_post_set`, `_init_hooks`, `_load_compose_types`,
`apply_native_integer_bounds`, `apply_native_float_bounds`,
`apply_native_string_length`, `apply_native_bytes_length`,
`apply_native_integer_enum`, `apply_native_boolean`,
`apply_native_decimal`, `apply_native_date`, `apply_native_datetime`,
`apply_native_uuid`, `apply_native_ip`, `apply_native_path`,
`apply_native_string_enum`,
`_raise_host_decimal_type_miss`, `_raise_host_date_type_miss`,
`_raise_host_datetime_type_miss`, `_raise_host_uuid_type_miss`,
`_raise_host_ip_type_miss`, `_raise_host_path_type_miss`,
`_closed_integer_bounds`, `_closed_float_bounds`,
`_closed_string_length`, `_closed_bytes_length`, `_closed_boolean`,
`_closed_decimal`, `_closed_date`, `_closed_datetime`, `_closed_uuid`,
`_closed_path`,
`apply_native_integer_min_value`, `_closed_integer_min_value`,
`_register_compose_types`, `_Opt.read`, `_Of._bind_kwargs`,
`_Of._merged_attr`, `Lookup`, `_log`, `bound_value`, `door_a`,
`_load_native_peer`, `_peer`, `_apply_host_value_after_i64_overflow`,
`_apply_host_value_after_f64_overflow`, `_apply_host_length_after_str_extract`,
`_apply_host_length_after_bytes_extract`,
`_apply_host_integer_enum_after_i64_overflow`,
`_apply_host_string_enum_after_str_extract`,
`_apply_host_boolean_after_extract`,
`_apply_host_decimal_after_extract`,
`_raise_host_integer_enum_type_miss`, `_raise_host_string_enum_type_miss`,
`_raise_host_integer_type_miss`, `_raise_host_float_type_miss`,
`_raise_host_string_type_miss`, `_raise_host_bytes_type_miss`,
`_apply_native_closed`,
`_select_integer_bounds`, `_select_float_bounds`, `_select_string_length`,
`_select_bytes_length`, `_select_integer_enum`, `_select_string_enum`,
`_select_boolean`, `_select_decimal`,
`_select_date`, `_select_datetime`, `_select_uuid`, `_select_ip`,
`_select_path`,
`_native_closed_apply`, `_native_fail`, `_compiled`, `_compiled_source`,
`_pattern_compiled_source`).
Noun-only names that hide the action are not
added. Names should fit any caller library — not a one-app
nickname, not a slogan.

AllOf / AnyOf live next to ``&`` / ``|`` on ``ValidateProperty``. Hook ``pre_validate`` / ``task_*``
methods live on `HookHost` (declared, not setattr from a table). Origin
tables live next to
`is_instance_of`. Specified-theory merge lives on `_Opts` (named fields, not string
keys). Errors live at
`ux_valio.errors`. Descriptor does not import `validators`. Do not
reintroduce leftover aliases, `validators/errors.py`, `validators/path.py`,
module `_bag_key` / `_owner_key` as a module function / `_resolve_bag_key` /
`_parse_eu_ind_date` /
`_parse_expiry_datetime` / `_is_valid_aadhaar` / `_is_valid_payment_card` /
`_is_valid_pan` / `_require_phonenumbers` / `_slot_names`,
or hang origin tables on `TypeValidator`, or a `validation_path.py` /
`compose.py` module.
