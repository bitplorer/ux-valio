# Changelog

## Unreleased

- Set-phase hangs (`pre_validate`, `post_validate`, `post_set`,
  `validator`, and their `task_*`) compile to a per-owner closed list
  (`_closed`) when the hang is registered, when the class is bound,
  and when a native plan binds or clears. `__set__` runs that list.
  Open owner-key buckets stay the source of truth. A missing entry is
  fail-closed. Get and delete still walk the MRO. The no-hang straight
  line is unchanged. Hangs stay Python. Cap Door B stays off.

- Host ``_native.py`` drops ``apply_native_string_enum``.
  ``_FamilyDoor.extract`` defaults to identity; StringEnum sets
  ``attrgetter("value")`` and ``_run_closed`` passes that payload
  to the FFI apply. Decimal, Date, DateTime, Uuid, IP, and Path
  share ``_raise_host_type_door_miss`` (the
  ``TypeValidator._validate_type`` forward). Boolean and enum
  type-miss raises stay. IP ``NotIp`` and the string store stay.
  Cap Door B stays off. Closed-plan behaviour is unchanged.

- Host ``_native.py`` drops thin ``apply_native_*`` shells that only
  forwarded to ``_FamilyDoor._run_closed``. ``bind_native_plan`` stores
  that bound method on ``_native_run``. Constant closed detectors are
  ``functools.partial`` of ``_closed_value_bounds`` /
  ``_closed_length`` / ``_closed_type_door``. StringEnum still applies
  ``value.value`` via ``apply_native_string_enum``. IP ``NotIp`` and
  the string store stay. Decimal / date annotation helpers stay.
  Cap Door B stays off. Closed-plan behaviour is unchanged.

- Host ``_native.py`` drops per-family ``_select_*`` passthroughs.
  ``bind_native_plan`` calls ``_FamilyDoor._select`` on the row.
  Isinstance families apply through ``_FamilyDoor._run_closed``
  (``expected`` / ``type_miss`` / ``bridge`` / ``extract_errors``).
  Empty type-door compile kwargs share ``_closed_type_door``.
  Integer and Float share ``_raise_host_value_type_miss``. String
  and Bytes share ``_raise_host_length_type_miss``. StringEnum
  still applies ``value.value``. IP ``NotIp`` and decimal/date
  annotation checks stay. Living slots stay ``_native_plan`` /
  ``_native_apply`` / ``_native_run`` / ``_native_fail_kind``.
  Cap Door B stays off. Closed-plan behaviour is unchanged.

- Host ``_native.py`` groups each Door A family in one section and
  binds through private ``_FAMILY_DOORS`` (``_FamilyDoor`` row:
  ``closed`` / ``compile`` / ``apply`` / ``run``). Living slots
  stay ``_native_plan`` / ``_native_apply`` / ``_native_run`` /
  ``_native_fail_kind``. Cap Door B stays off. Closed-plan behaviour
  is unchanged.

- Native Path type door: closed ``ux-valio[native]`` plans now cover
  ``PathValidator`` when the annotation is ``pathlib.Path`` or the
  facade coerce union ``pathlib.Path | str``, and the only active
  unit is the type door. ``compile_path`` / ``apply_path`` stay a
  pair. Door A lock: stored type is ``pathlib.Path`` only after host
  ``_pre_validate`` (string coerce); the peer never sees a raw
  ``str``. Exact ``pathlib.Path`` passes, including a subclass
  (``PosixPath`` is a ``Path``). ``pathlib.PurePath`` misses.
  ``int`` / ``bool`` / ``bytes`` miss. No resolve, no absolute, no
  filesystem check. ``path_exists`` stays the named extra
  (``FileNotFoundError``). Bounds, length, choice, ``required``,
  and ``reassign=False`` stay host. Extract ``TypeError`` falls
  through to host ``TypeValidator``. ``None`` skips.
  ``pathlib.Path | None`` and other unions stay host. Cap Door B
  stays off. Plain EnumValidator / Pattern / named facades stay
  HOLD. No follow-up remains on this Path concern. UUID and IP
  closed-family HOLD stays cleared. Measure
  ``python benches/measure_host_peer.py`` (Path **79.92×**, host
  6744.9 ns/op, native 84.4 ns/op; CPython 3.14.7 / rustc 1.83 /
  Linux x86_64); do not claim 70× product setattr.

- Native IP string identity: closed ``ux-valio[native]`` plans now
  cover ``IPv4Validator``, ``IPv6Validator``, and
  ``IPAddressValidator`` when the annotation is ``str`` and the only
  active unit is the type door. ``compile_ip`` / ``apply_ip`` stay a
  pair. ``kind`` is ``ipv4`` / ``ipv6`` / ``ip``. Door A lock: the
  stored value stays the given string. There is no
  ``_pre_validate`` coerce to ``ipaddress`` objects.
  ``IPv4Address`` / ``IPv6Address`` / ``ip_address`` are the parsers
  the kind mirrors, not a stored type. Exact strings those parsers
  accept pass, including ``::``, IPv4-mapped IPv6, and
  ``fe80::1%eth0``. The stored text is not rewritten. ``int`` /
  ``bytes`` / ``ipaddress`` objects miss the type door. Invalid
  strings are ``FailKind.NotIp``; the host keeps the existing
  ``ValueError`` sentence. Extract miss on a ``str`` bridges to
  that parser. ``None`` skips. Length, pattern, choice,
  ``required``, and ``reassign=False`` stay host.
  ``StringValidator`` is not this door. Cap Door B stays off. Path
  / plain EnumValidator / Pattern / named facades stay HOLD. No
  follow-up remains on this IP concern.
  Measure ``python benches/measure_host_peer.py`` (IPv4 **40.32×**,
  host 5743.4 ns/op, native 142.5 ns/op; IPv6 **37.39×**, host
  6653.4 ns/op, native 178.0 ns/op; IP **43.52×**, host 7336.2 ns/op,
  native 168.6 ns/op; CPython 3.14.7 / rustc 1.83 / Linux x86_64);
  do not claim 70× product setattr.

- Native Uuid type door: closed ``ux-valio[native]`` plans now cover
  ``UUIDValidator`` when the annotation is ``uuid.UUID`` or the facade
  coerce union ``uuid.UUID | str``, and the only active unit is the
  type door. ``compile_uuid`` / ``apply_uuid`` stay a pair. Door A
  lock: stored type is ``uuid.UUID`` only after host
  ``_pre_validate`` (string coerce); the peer never sees a raw
  ``str``. Exact ``uuid.UUID`` passes, including the nil UUID.
  ``int`` / ``bool`` / ``bytes`` miss. Bounds (min/max/gt/lt/eq) stay
  host. Extract ``TypeError`` falls through to host
  ``TypeValidator``. ``None`` skips. ``uuid.UUID | None`` and other
  unions stay host. Cap Door B stays off. Path / IP / plain
  EnumValidator / Pattern / named facades stay HOLD. No follow-up
  remains on this Uuid concern.
  Measure ``python benches/measure_host_peer.py`` (Uuid **77.02×**,
  host 7324.1 ns/op, native 95.1 ns/op; CPython 3.14.7 / rustc 1.83 /
  Linux x86_64); do not claim 70× product setattr.

- Host regex cache slot rename (internal only, no behavior change).
  ``Validator`` and ``PatternValidator`` keep the pair
  ``_pattern_compiled`` (cached ``re.Pattern``; was ``_compiled``) and
  ``_pattern_source`` (source string or unset sentinel; was
  ``_compiled_source``). That pair is the host regex cache only —
  unrelated to native ``compile_*`` / ``apply_*``. Public ``pattern``
  stays the source. ``_compiled_finder`` still fills the pair. Do not
  fold the cache into ``pattern`` or name it
  ``_pattern_compiled_source``. Native slots and public ``compile_*`` /
  ``apply_*`` are unchanged. Cap Door B stays off. UUID / Path / IP
  stay HOLD.

- Native Date and DateTime type doors: closed ``ux-valio[native]``
  plans now cover ``DateValidator`` when the annotation is
  ``datetime.date`` or the facade coerce union ``datetime.date | str``,
  and ``DateTimeValidator`` when the annotation is
  ``datetime.datetime`` or ``datetime.datetime | str``, and the only
  active unit is the type door. ``compile_date`` / ``apply_date`` and
  ``compile_datetime`` / ``apply_datetime`` stay pairs. Door A lock:
  stored type is the calendar value only after host
  ``_pre_validate`` (EU / IND date strings, ISO datetimes); the peer
  never sees a raw ``str``. ``datetime.datetime`` extracts on the
  Date door because it subclasses ``date``; ``DateValidator`` still
  rejects it in the named extra. A plain ``date`` misses the
  DateTime door. Exact ``date`` and ``datetime`` pass. Bounds
  (min/max/gt/lt/eq) stay host. Extract ``TypeError`` falls through
  to host ``TypeValidator``. ``None`` skips. ``date | None``,
  ``datetime | None``, and other unions stay host. Cap Door B stays
  off. UUID / Path / IP / plain EnumValidator / Pattern / named
  facades stay HOLD. No follow-up remains on this Date* concern.
  Measure ``python benches/measure_host_peer.py`` (Date **79.33×**,
  host 6281.4 ns/op, native 79.2 ns/op; DateTime **78.55×**, host
  6315.0 ns/op, native 80.4 ns/op; CPython 3.14.7 / rustc 1.83 /
  Linux x86_64); do not claim 70× product setattr.

- Validator native slot pair (internal only, no behavior change).
  ``_native_plan`` and ``_native_fail_kind`` stay. The four slots are
  plan | apply (Rust FFI) | run (Python closed entry) | fail_kind:
  product-PyO3 Rust door is ``_native_apply`` (was ``_native_ffi``);
  closed-family Python door is ``_native_run`` (was ``_native_entry``).
  Both renames land together. Public ``compile_*`` / ``apply_*`` names
  are unchanged. Cap Door B stays off. Date* / UUID / Path / IP stay
  HOLD.

- Native path fold (internal only, no behavior change). Eight
  ``_apply_host_*_after_*`` bridges collapse to ``_bridge_to_value`` /
  ``_bridge_to_length`` / ``_bridge_to_type``. Enum type-miss thin
  aliases drop; call ``_raise_host_enum_type_miss`` directly. Product
  PyO3 load is ``_load_native`` / ``_native_mod`` / ``as native`` (was
  ``_load_native_peer`` / ``_peer`` / ``as peer``). Teaching names the
  native module, not Cap Host/Peer. Private Rust helpers
  ``apply_i64_members`` / ``apply_str_members`` (was ``apply_member_units``
  / ``apply_string_members``). Public ``compile_*`` / ``apply_*`` and
  family ``apply_native_*`` stay. Cap Door B stays off. Date* HOLD.

- Validator native slot rename (internal only, no behavior change).
  ``_native_plan`` stays. Product-PyO3 apply is ``_native_ffi`` (was
  ``_native_apply``). Host family entry is ``_native_entry`` (was
  ``_native_closed_apply``). Fail enum type is ``_native_fail_kind``
  (was ``_native_fail``). ``Closed`` stays only on detectors
  (``_closed_*``). Public ``compile_*`` / ``apply_*`` names are
  unchanged. Cap Door B stays off. Date* / UUID / Path / IP stay HOLD.

- Closed-host-apply slot name (internal only, no behavior change).
  The fourth Validator native slot is ``_native_closed_apply``: the
  closed-family host apply (``apply_native_integer_bounds``,
  ``apply_native_float_bounds``, and the other family doors). Peer
  FFI apply stays ``_native_apply``. The four slots stay
  ``_native_plan`` / ``_native_apply`` / ``_native_fail`` /
  ``_native_closed_apply``, seeded ``None`` on ``Validator.__init__``
  and cleared by ``_clear_native``. Writers stay ``bind_native_plan``
  / ``_clear_native``. ``apply_native_bounds`` reads the slot
  directly. ``ux_valio/validators/_native.py`` stays private. Cap Door
  B stays off. Date* / UUID / Path / IP / Enum / Pattern stay HOLD.

- Native-plan ownership clarity (internal only, no behavior change).
  ``Validator.__init__`` seeds ``_native_plan`` / ``_native_apply`` /
  ``_native_fail`` / ``_native_closed_apply`` as ``None`` before
  ``bind_native_plan(self)`` — the same four slots ``_clear_native``
  clears. Ownership stays on ``Validator`` once; typed facades inherit
  that ``__init__``. ``__set_name__`` rebinds when ``_native_plan is
  None`` (annotation-ready cases such as ``Validator[int]``) without
  ``getattr(..., None)``. ``bind_native_plan`` / ``_clear_native`` remain
  the writers. Cap Door B stays off. Date* stays HOLD.

- Bound miss comments (internal clarity only, no behavior change).
  Integer and Float miss arms stay fail-when predicates: ``min_value``
  passes when ``value >= min`` (miss ``<``); ``gt`` passes when
  ``value > gt`` (miss ``<=``, exclusive); ``max_value`` passes when
  ``value <= max`` (miss ``>``); ``lt`` passes when ``value < lt``
  (miss ``>=``, exclusive); ``eq`` misses on ``!=`` (IEEE NaN never
  equals). Inclusive stays ``min_value`` / ``max_value``; exclusive
  stays ``gt`` / ``lt``. No new L1 kwarg. Public ``compile_*`` /
  ``apply_*`` names are unchanged. Cap Door B stays off. Date* stays
  HOLD.

- Test and host-native layout (internal only, no L1 break). Native
  peer tests are one module per family
  (``tests/test_native_<family>.py``) plus
  ``tests/test_native_layout.py`` (public ``compile_*`` / ``apply_*``
  presence, bare ``compile`` / ``apply`` absence, cross-family
  ``RuntimeError``, Cap OFF, Date* HOLD). Shared helpers are
  ``tests/native_support.py``. Host ``_native.py`` stays one file:
  closed detectors, apply, and the bind list are the same walk for
  every family, so a closed/apply split is not one family walk.
  Public ``compile_*`` / ``apply_*`` names and signatures are
  unchanged. Cap Door B stays off. Date* stays HOLD.

- Native peer layout (internal only, no L1 break). The private ``Plan``
  enum is one variant per family; each variant owns only that family's
  checks (Integer / Float bounds, String / Bytes length, IntegerEnum /
  StringEnum member sets, Boolean and Decimal type-door markers).
  ``apply_integer`` walks ``BoundUnit<i64>`` only, so a length unit
  cannot be passed into that walk. A plan handed to another family's
  ``apply_*`` raises ``RuntimeError`` before the walk. Public
  ``compile_*`` / ``apply_*`` names and signatures are unchanged. Cap
  Door B stays off. Date* / UUID / Path / Pattern stay HOLD.

- Native Decimal type door: closed ``ux-valio[native]`` plans now cover
  ``DecimalValidator`` when the annotation is ``decimal.Decimal`` or
  the facade coerce union ``decimal.Decimal | str`` and the only
  active unit is the type door. ``compile_decimal`` / ``apply_decimal``
  stay a pair. Door A lock: stored type is ``decimal.Decimal`` only
  after host ``_pre_validate``; string coerce stays
  ``DecimalValidator._coerce_str`` (the peer never sees a raw ``str``);
  ``float`` / ``int`` / ``bool`` miss (no silent float→Decimal, no
  ``Decimal(float)`` on this door); exact ``Decimal`` instances pass,
  including ``Decimal("0")``. No ``max_digits`` / ``decimal_places`` /
  ``quantize`` scale units. Quantize / scale / context / rounding stay
  HOLD / host. Bounds (min/max/gt/lt/eq) stay host. Extract
  ``TypeError`` falls through to host ``TypeValidator``. ``None``
  skips. ``Decimal | None`` and other unions stay host. Measure
  ``python benches/measure_host_peer.py`` (Decimal **77.09×**, host
  6155.1 ns/op, native 79.8 ns/op, CPython 3.14.7 / rustc 1.83 / Linux
  x86_64); do not claim 70× product setattr. Cap Door B stays off.
  Date* / UUID / Path / plain EnumValidator / Pattern / named facades
  stay HOLD.

- Native Boolean type door: closed ``ux-valio[native]`` plans now cover
  ``BooleanValidator`` when the annotation is ``bool`` and the only
  active unit is the type door. ``compile_boolean`` / ``apply_boolean``
  stay a pair. Door A is exact ``bool``: ``True`` and ``False`` pass
  and are stored as that object (``False`` is kept); ``1`` / ``0`` are
  not coerced and raise the host type-door ``TypeError``. Extract
  ``TypeError`` falls through to host ``TypeValidator``. Extra bounds,
  ``bool | None``, plain ``EnumValidator``, and open ``Validator`` stay
  on the host. Integer still treats ``True`` as ``int``. Measure
  ``python benches/measure_host_peer.py`` (Boolean **37.40×**, host
  2991.4 ns/op, native 80.0 ns/op, CPython 3.14.7 / rustc 1.83 / Linux
  x86_64); do not claim 70× product setattr. Cap Door B stays off.
  Decimal / Date* / UUID / Path / plain EnumValidator / Pattern / named
  facades stay HOLD.

- Peer-surface break: bare ``compile`` / ``apply`` on
  ``ux_valio_native`` are retired. Closed Integer doors are
  ``compile_integer`` / ``apply_integer`` (still a pair, still
  separate). Host L1 (``IntegerValidator``, kwargs ``min_value`` /
  ``gt`` / ``max_value`` / ``lt`` / ``eq``) is unchanged. Cap Door B
  stays off. Float / String / Bytes / IntegerEnum / StringEnum door
  names are unchanged.

- Native Door A polish (no new family). Integer and Float share one
  scalar compare (Door A IEEE: NaN unordered on min/max/gt/lt, ``!=``
  so NaN never matches). The unit list is an ``Arc`` so apply clones
  the plan, not the units; plans that are not StringEnum share one
  empty member set. Host bind walks one family list. Each family still
  names its own ``compile_*`` / ``apply_*`` pair; those doors stay
  separate. Cap Door B stays off. Boolean stays HOLD until a later
  measure is ≥3× alone. Closed families remain Integer, Float, String,
  Bytes, IntegerEnum, and StringEnum.

- Native StringEnum member set: closed ``ux-valio[native]`` plans now
  cover ``StringEnumValidator`` when the field annotation is a concrete
  str-valued ``enum.Enum`` and the only active unit is the type door.
  Member values are UTF-8 ``&str`` (``compile_string_enum`` /
  ``apply_string_enum``, kept as a pair). Door A matches host: in-set
  members store the member; another enum (including a colliding string)
  and non-members (``str`` / ``bytes`` / ``int`` / ``bool`` / ``IntEnum``)
  raise the host type-door ``TypeError``. ``FailKind.NotMember`` uses
  that same wording via ``match fail:``. ``OverflowError`` /
  ``UnicodeError`` at ``&str`` extract falls through to host
  ``TypeValidator``. A member that is not exact ``str`` or not UTF-8
  (lone surrogate, ``str`` subclass) keeps the whole field on the host.
  Bare ``enum.Enum`` / ``enum.StrEnum``, extra bounds, plain
  ``EnumValidator``, ``BooleanValidator``, ``IntegerEnumValidator``, and
  open ``Validator`` stay on the host. No ``members`` kwarg on the
  facade. Integer / Float / String / Bytes / IntegerEnum plans are
  unchanged. Cap Door B stays off. Measure
  ``python benches/measure_host_peer.py``; do not claim 70× product
  setattr. Next HOLD: Boolean only if a later measure is ≥3× alone.
  Decimal / Date* / UUID / Path / plain EnumValidator / Pattern / named
  facades stay HOLD.

- Native IntegerEnum member set: closed ``ux-valio[native]`` plans now
  cover ``IntegerEnumValidator`` when the field annotation is a concrete
  ``enum.IntEnum`` and the only active unit is the type door. Member
  values are ``i64`` (``compile_integer_enum`` / ``apply_integer_enum``,
  kept as a pair). Door A matches host: in-set members store the member;
  another ``IntEnum`` (including a colliding integer) and non-members
  (``int`` / ``bool`` / ``str`` / plain ``Enum``) raise the host type-door
  ``TypeError``. ``FailKind.NotMember`` uses that same wording.
  ``OverflowError`` at ``i64`` extract falls through to host
  ``TypeValidator``. A member outside ``i64`` keeps the whole field on
  the host. Bare ``enum.IntEnum``, extra bounds, plain ``EnumValidator``,
  ``StringEnumValidator``, ``BooleanValidator``, and open ``Validator``
  stay on the host. Integer / Float / String / Bytes plans are unchanged.
  Measure ``python benches/measure_host_peer.py``; do not claim 70×
  product setattr. Next HOLD: StringEnum. Boolean only if a later
  measure is ≥3× alone. Decimal / Date* / UUID / Path / plain
  EnumValidator / Pattern / named facades / Cap Door B stay HOLD.

- Native Bytes length units: closed ``ux-valio[native]`` plans now
  cover ``BytesValidator`` ``MinLength`` / ``MaxLength`` / ``Length``
  (usize) and min+max range. Type door is FFI ``&[u8]`` extract
  (``apply_bytes``). Door A length is host ``len(bytes)`` (byte count),
  not Unicode codepoints and not graphemes. Empty ``b""`` and high-byte
  edges match host. ``OverflowError`` / extract TypeError falls through
  to host ``LengthValidator`` (bridge, not an L1 "overflow" message).
  Annotation must be ``bytes`` and only those length units active;
  pattern / custom / String stay on the host. Integer i64, Float f64,
  and String codepoint length paths are unchanged. Measure each Bytes
  family (``python benches/measure_host_peer.py``); do not claim 70×
  product setattr. Next HOLD: IntegerEnum, then StringEnum. Boolean
  only if later measure ≥3×. Decimal / Date* / UUID / Path / plain
  EnumValidator / Pattern / named facades / Cap Door B stay HOLD.

- Native String length units: closed ``ux-valio[native]`` plans now
  cover ``StringValidator`` ``MinLength`` / ``MaxLength`` / ``Length``
  (usize) and min+max range. Type door is FFI ``&str`` extract
  (``apply_string``). Door A length is host ``len(str)`` Unicode
  codepoints (``chars().count()``), not UTF-8 bytes and not graphemes.
  Empty string and NFC/NFD/emoji edges match host. Lone-surrogate /
  ``OverflowError`` extract falls through to host ``LengthValidator``
  (bridge, not an L1 "overflow" message). Annotation must be ``str``
  and only those length units active; pattern / custom / Bytes /
  required stay on the host. Integer i64 and Float f64 paths are
  unchanged. Measure each String family
  (``python benches/measure_host_peer.py``); do not claim 70× product
  setattr. Next HOLD: Bytes length. IntegerEnum / StringEnum after.
  Boolean only if later measure ≥3×. Decimal / Date* / UUID / Path /
  plain EnumValidator / Pattern / named facades / Cap Door B stay HOLD.

- Native Integer bound units: closed ``ux-valio[native]`` plans now
  cover ``MinValue`` / ``MaxValue`` / ``GreaterThan`` / ``LessThan`` /
  ``Equal`` (i64) and min+max / exclusive pairs. Rust variants are
  full words; compile maps host kwargs (``min_value`` / ``gt`` /
  ``max_value`` / ``lt`` / ``eq``). Plan shape is an owned unit list
  (not a fixed two-slot array). Unclosed paths (``required``,
  ``multiple_of``, length, pattern, choice, named identity)
  stay on the host. OverflowError at i64 extract still falls through
  to host ``ValueValidator``. Measure each family
  (``python benches/measure_host_peer.py``); do not claim 70× product
  setattr. Closed
  Integer type door is FFI ``i64`` extract; ``bool`` / ``None`` /
  ``collect_all`` stay host-first.

- Native tip polish after the ``[native]`` extra: PyO3 ``i64`` extract is
  the range oracle (no host ``bit_length`` / ``_I64_BITS`` gate).
  ``OverflowError`` at extract falls through to host ``ValueValidator``
  (``2**70`` + ``min_value=0`` still PASSes). That is a bridge signal,
  not a public overflow miss. Unexpected peer/infra raises
  ``RuntimeError`` naming ``ux_valio_native``. Dead
  ``FailKind.NotInteger`` dropped; type misses stay on the host
  ``isinstance`` gate.

- Optional ``ux-valio[native]`` extra: sibling maturin wheel
  (``native/``, module ``ux_valio_native``) compiles
  ``IntegerValidator(min_value=…)`` once to ``Integer`` +
  ``MinValue(i64)`` and applies in one FFI per set. Host keeps
  descriptor, hooks, KEEP wording, and store. Without the extra,
  stdlib Python apply stays the default. Cap Door B / Ops / JSON /
  ``cek-peer-*`` stay off the field path. Measure harness retargets
  to the product peer (``python benches/measure_host_peer.py``;
  CI ``--ci`` skips without Rust). Do not quote the switch-test
  70× as end-to-end product setattr.

- Drop unused ``number_of_assignment`` counter (valio leftover; reassign
  uses ``_assignment_counts``). ``doc=`` is the descriptor ``__doc__``.
  Choice helper parameter is ``container``, not ``bag``.

- Drop unused ``Chain`` alias (it was ``AllOf``). Compose with ``AllOf``
  / ``&``. Not in ``__all__``.

- Validator constructor kwargs documented one-by-one with examples
  (``doc``, ``default``, ``default_factory``, ``reassign``, bounds, …).
  Live check: ``examples/validator_kwargs.py``.

- Field-level logging: how-to + ``examples/field_logging.py``
  (``logger=True`` / custom ``Logger`` / OFF).

- Handbook pages explain what / where / how with usage examples
  (tutorial, hang, compose, TypedDict, pattern, typed, named, honesty).

- Handbook: choices, performance, workflows, typing — every usage
  pattern and KEEP decision in Diátaxis, no second door.

- Examples: ``main()`` live-checks conflict/identity failures via
  ``_must_raise`` (no silent ``except: pass``).

- Examples: one file per workflow (``signup``, ``checkout``, ``kyc``,
  ``vendor``, ``storefront``, ``catalog``, ``invite``, ``filing``). Dropped
  overlapping registration / account / compose / sku / lookaround twins.

- Examples: ports are ``Validator[UserStore](required=True)`` (with
  ``@runtime_checkable`` Protocol) so the store is type-checked like
  every other field. ``field(repr=False, compare=False)`` still hides it
  from ``repr`` / ``eq``.

- Examples: restore dataclass ports (`field(repr=False, compare=False)`,
  first in declaration order). ``object.__new__`` and ``init=False``
  handwritten ``__init__`` were not Pythonic.

- Examples: store lookup hangs on ``post_validate`` (after identity);
  persist on ``post_set``.

- Examples are service+port workflows (uniqueness / stock), not blank
  checks on top of ``required``. Docs compose hang is reserved-handle,
  not ``if not value``.

- Handbook: ``docs/`` is Diátaxis (tutorial / how-to / reference /
  explanation). README is the PyPI front door. Optional
  ``mkdocs serve`` (``ux-valio[docs]``). Host-peer note lives under
  ``docs/explanation/``.

- Docs: typed facades ``Usage::``; specified-path construct bind;
  IBAN ``02``–``98`` in the named table; examples index complete;
  user-facing ``bag`` wording dropped from README.

- Note: ``docs/explanation/host-peer-plan.md`` — host decides / peer applies (optional
  native apply later; instance stays Python). Not implemented.

- Hot path: ``ValidationPath.run`` no longer allocates ``ran``/``results``
  per set (uniqueness is ``__init__``). Default-path fields run only
  specified units (type always). Concrete ``int``/``str`` skip the
  TypedDict walk. Assignment watch runs only when ``reassign=False``.

- Hot path: skip empty hook MRO walks; ``is_instance_of`` fast-path for
  concrete types (``int`` / ``str`` / Enum). Empty ``_process_then_tasks``
  is a no-op when nothing is hung. Flag is ``_hooks_hung`` (not
  ``HookHost._has_hooks``).

- ``EmailValidator`` stores stripped lowercase (login uniqueness).
  IBAN check digits must be ``02``–``98`` (ISO 13616).

- Address / bank workflow: ``USStateValidator``, ``IndiaStateCodeValidator``,
  IBAN ISO 13616 **national length** (unknown country fail-closed). PIN
  moved ``india/bank`` → ``india/postal``. Checkout uses
  ``CardExpiryValidator``.

- Payment card Luhn runs once, then brand match (Diners was 8× Luhn).
  IANA timezones load on first ``TimezoneValidator`` check, not import.
  ``portal.py`` stdlib imports first.

- ``ITINValidator`` (the SSN docstring hole). RFC check-digit ``ValueError``
  is fail-closed. README duplicate IBAN row dropped. CURP not added
  (published check digits disagree).

- Onboarding KYC: ``SSNValidator``, ``EINValidator``, ``NINOValidator``,
  ``CanadianSINValidator``, ``MexicoRFCValidator``. ``canada/`` and
  ``mexico/`` are country folders (same rule as ``us`` / ``india``).
  Cookie/password/SKU stay generic (``Enum`` / ``StringValidator`` +
  Pattern). Contact import order residual fixed.

- National identities sit under the country, not ``address`` / ``finance``.
  ``us/`` (ZIP, ABA, CUSIP), ``uk/`` (postcode, sort), ``canada``,
  ``mexico``. ``finance`` is ISO only (IBAN/BIC/ISIN/LEI/card/currency).

- Everyday identities every app reimplements: US/CA/UK postal, CLABE,
  UK sort, CUSIP, ISSN, locale, SemVer. Payment cards accept JCB and
  Diners. Unused ``re`` dropped from ``currency``.

- ``named/finance`` is a package: ``rail`` / ``market`` / ``card`` /
  ``currency``. Layers do not import each other.

- India layers: ``DINValidator``, ``LLPINValidator``, ``FSSAIValidator``,
  ``IndianPassportValidator``. Aadhaar rejects UIDAI-reserved first digit
  0/1 even when Verhoeff holds.

- ``named/india`` is a package: ``kyc`` / ``gst`` / ``registry`` / ``bank``.
  Layers do not import each other. ``from ux_valio import GSTINValidator``
  unchanged.

- GSTIN accepts jurisdiction ``97`` / ``99``. Payment cards accept UnionPay.
  ``UdyamValidator`` is the MSME identity.

- Named facades group by use: sibling modules ``india`` / ``finance`` /
  ``catalog`` / ``contact`` / ``device`` / ``portal`` / ``expiry``.
  Public ``from ux_valio import GSTINValidator`` unchanged. Domain
  modules do not import each other.

- E-commerce / SaaS named facades: ``GTINValidator``, ``HostnameValidator``,
  ``SlugValidator``, ``CurrencyCodeValidator``, ``CountryCodeValidator``,
  ``TimezoneValidator``, ``ULIDValidator``, ``LEIValidator``,
  ``CardExpiryValidator``, ``HSNCodeValidator``, ``ABARoutingValidator``.

- Named identity facades: class ``help()`` usage, README table (compact
  store, checksum vs format), ``examples/identity_fields.py``.

- Named identity facades: ``BICValidator`` (SWIFT), ``ISINValidator``,
  ``ISBNValidator``, ``EANValidator``, ``VINValidator``,
  ``MACAddressValidator``, ``TANValidator``, ``CINValidator``,
  ``VoterIdValidator``. Stdlib only, no network.

- Hang check is ``validator`` (attrs ``@x.validator``). ``add_validator``
  is leftover. ``validate()`` still runs the bag. README Hang API lists
  every public hook; ``namespace=`` is the owning class or its
  ``module.qualname`` str.

- Every hang API (``pre_validate`` … ``post_delete``, ``task_*``,
  ``validator``) is sync and async. Process / ``validator``:
  no loop → TypeError; running loop → nest-safe. ``task_*``: isolated
  worker, setter does not wait.

- Descriptor lifecycle is private (``_run_pre_set`` / ``_run_post_set``).
  Hang API is the phase name: ``pre_validate``, ``post_set``, ``task_post_set``.
  Process is the default kind (no ``process_`` prefix).

- Intentful names: ``ValidateStep`` (was ``Lookup``), ``_emit_log``,
  ``read_bound``. Test files drop leftover ``door_a`` filenames.

- Docs and module comments name the field default
  (``name: str = StringValidator()``), not "Door A".

- ``namespace=`` accepts the owning class (not only a ``module.qualname``
  str). ``wait_tasks`` is on the package root. ``TypeAliasType`` peels by
  identity.

- HookHost pipeline runners and ``has_hooks`` are private
  (``_pre_validate``, ``_has_hooks``, ``_notify_pre_set``).

- TypedDict hook lookup uses ``__set_name__`` ``_owner`` (no ``_hook_schema``
  sticky state). Qualifiers peel by identity. ``_validate_typed_dict``.

- TypedDict keys accept field-default assignment (``name: str = StringValidator()``)
  and ``@name.pre_validate`` / ``@name.validator`` in that class body.
  ``self`` is the mapping. ``_run_pre_set`` write-back then ``_run_post_set``.

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
