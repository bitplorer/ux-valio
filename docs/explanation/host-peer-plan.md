# Host decides, peer applies

Performance map plus the optional product extra. Not a pydantic clone.
The taught API stays ``field: T = SomeValidator(...)``. Stdlib Python is
the default apply. ``pip install ux-valio[native]`` may bind a PyO3
peer for a **closed** plan. That is not a second door (no Field, no
Schema, no BaseModel). Cap Door B is a different stack and is **not**
on this field path.

## Essence

A Python object’s **soul stays on the host**. The instance, the
descriptor, hooks, and exception types are Python. What can leave is a
**compiled plan of specified concerns** plus a **scalar value**. The
peer applies that plan and returns a result. The host decides *whether*
to call, *which* plan, and *how* to raise.

```text
bind / __init__     host compiles specified theory → plan
set                 host hands (plan, value) once
                    peer applies  (i64 / f64 / &str / &[u8] / bool / Decimal extract; bound, length, or member units)
                    host stores on instance.__dict__
                    host runs hooks, named extras, debug-swallow
```

One crossing per set. A peer that calls back into Python **per unit**
is slower than today’s path — do not do that.

## Roles (CEK)

| | Host (Python) | Peer (PyO3 / Rust) |
|---|---|---|
| Role | decide | apply |
| Owns | instance, descriptor, hooks, messages | specified scalar plan |
| When | bind, set policy, collect_all, raise | the plan body |
| Lives | always (stdlib) | optional extra |

Host is authority. Peer has no policy: no debug-swallow, no logger, no
``collect_all`` orchestration, no hook dispatch.

This matches a CEK host/peer split: Python host, PyO3 as the apply
peer, communication is “here is the plan and the value; give me ok or a
typed failure.” Cap Ops / JSON / ``cek-peer-pyo3`` are not that
channel.

## What the plan is here

The host already compiles at construct:

- ``Validator._active_units`` — specified default-path concerns (type
  always; length/value/pattern/… only when bound)
- uniqueness of ``ValidationPath`` units at ``__init__`` (not per set)

That tuple **is** the plan. Without the extra, the interpreter applies
it. With ``ux-valio[native]``, a **closed** subset is the same tuple as
a native enum, built **once** at ``__init__`` / ``__set_name__``.

Shipped closed plans: ``Integer`` or ``Float`` plus specified bound units —
``MinValue`` / ``MaxValue`` / ``GreaterThan`` / ``LessThan`` / ``Equal``, including
min+max range and exclusive ``gt``+``lt`` as the host encodes them —
and ``String`` plus specified length units — ``MinLength`` /
``MaxLength`` / ``Length``, including min+max range — and ``Bytes``
plus the same length units (byte count, not codepoints) — and
``IntegerEnum`` plus ``Member`` ``i64`` values taken from the concrete
``enum.IntEnum`` on the field — and ``StringEnum`` plus the UTF-8
``.value`` strings taken from the concrete str-valued ``enum.Enum``
on the field — and ``Boolean`` as the exact ``bool`` type door
(no bound unit) — and ``Decimal`` as the exact ``decimal.Decimal``
type door (no bound unit, no scale unit).
``IntegerValidator(min_value=0)``, ``max_value=10``, ``gt=0``,
``eq=7``, and ``min_value=0, max_value=10`` compile when the
annotation is ``int`` and only those bound units are active.
``compile_integer`` / ``apply_integer`` stay a pair.
``FloatValidator(min_value=0.0)`` (and the same family of kwargs)
compile when the annotation is ``float`` and bounds are ``float``
(an int bound such as ``min_value=0`` stays on the host).
``StringValidator(min_length=1)``, ``max_length=50``, ``length=3``,
and ``min_length=1, max_length=10`` compile when the annotation is
``str`` and only those length units are active.
``BytesValidator(min_length=1)`` (and the same length kwargs)
compile when the annotation is ``bytes`` and only those length
units are active.
``IntegerEnumValidator()`` compiles when the owner annotation is a
concrete ``enum.IntEnum`` (not bare ``enum.IntEnum``) and the only
active unit is the type door. ``compile_integer_enum(members)`` /
``apply_integer_enum(plan, i64)`` stay a pair.
``StringEnumValidator()`` compiles when the owner annotation is a
concrete str-valued ``enum.Enum`` (not bare ``enum.Enum``) and the
only active unit is the type door. ``compile_string_enum(members)`` /
``apply_string_enum(plan, &str)`` stay a pair.
``BooleanValidator()`` compiles when the annotation is ``bool`` and the
only active unit is the type door. ``compile_boolean()`` /
``apply_boolean(plan, bool)`` stay a pair. ``1`` / ``0`` are not
coerced.
``DecimalValidator()`` compiles when the annotation is
``decimal.Decimal`` or the facade coerce union
``decimal.Decimal | str`` and the only active unit is the type door.
``compile_decimal()`` / ``apply_decimal(plan, Decimal)`` stay a pair.
``float`` / ``int`` / ``bool`` are not coerced. String coerce stays
host ``_pre_validate``. Unclosed
paths (``required``, ``multiple_of``, pattern, choice, named
identity, Email, a mixed bound type, Union / TypedDict /
Annotated) stay on the host. Email / named identity were already
competitive in Python — do not start there.

Closed Integer **type door** is the FFI ``i64`` extract
(``apply_integer``). Closed Float **type door** is the FFI ``f64``
extract (``apply_float``). Bound units
run after extract. Host ``isinstance`` is first so Python ``True`` is
``int`` (load-bearing) and Python ``int`` is **not** ``float`` (KEEP);
``None`` and ``collect_all`` type miss stay host-first. KEEP
``TypeError`` wording is host-formatted (not a ``FailKind.NotInteger``
/ ``NotFloat``; open TypeValidator is not reflected into Rust). Bound
misses use the ``FailKind`` map.

Closed String **type door** is the FFI ``&str`` extract
(``apply_string``). Length units run after extract.

Closed Bytes **type door** is the FFI ``&[u8]`` extract
(``apply_bytes``). Length units run after extract.

Closed IntegerEnum **type door** is host ``isinstance`` of the concrete
``enum.IntEnum``, then the FFI ``i64`` extract (``apply_integer_enum``).
``Member`` units run after extract. Membership is exact ``i64``
equality with ``member.value``.

Closed StringEnum **type door** is host ``isinstance`` of the concrete
str-valued ``enum.Enum``, then the FFI ``&str`` extract of
``member.value`` (``apply_string_enum``). Membership is exact UTF-8
equality (no casefold, no NFC).

**Float NaN / ±inf (Door A lock).** Host ``ValueValidator`` uses Python
IEEE compares. Native must match; do not invent a second policy
(``total_cmp``, NaN-reject, inf-reject):

- Type: ``float('nan')`` / ``±inf`` are ``float`` and pass the type door.
- min/max/gt/lt: NaN is unordered (``nan < bound`` is false), so those
  bounds **pass** NaN. ``+inf`` fails a finite ``max_value`` / ``lt``;
  ``-inf`` fails a finite ``min_value`` / ``gt``.
- ``eq``: ``!=`` so NaN **never** matches, including ``eq=nan``
  (``nan != nan``). Signed zero: ``-0.0 == 0.0``.
- Extract overflow is a **bridge** (fall through to host
  ``ValueValidator``), not an L1 "overflow" message.

**String length (Door A lock).** Host ``LengthValidator`` uses Python
``len(str)`` — Unicode codepoints (scalar values), not UTF-8 bytes and
not grapheme clusters:

- Type: only ``str`` (``bytes`` / ``int`` miss). ``None`` skips.
- Count: NFC ``é`` is 1; NFD ``e`` + combining acute is 2; a single
  emoji codepoint is 1. Empty ``""`` is 0 (``min_length=1`` misses;
  ``max_length=0`` / ``length=0`` accept it).
- Extract overflow / lone surrogates that are not UTF-8 is a **bridge**
  (fall through to host ``LengthValidator``), not an L1 "overflow"
  message.

**Bytes length (Door A lock).** Host ``LengthValidator`` uses Python
``len(bytes)`` — byte count, not Unicode codepoints and not grapheme
clusters:

- Type: only ``bytes`` (``str`` / ``bytearray`` / ``memoryview`` /
  ``int`` miss). ``None`` skips.
- Count: empty ``b""`` is 0 (``min_length=1`` misses; ``max_length=0``
  / ``length=0`` accept it). High bytes such as ``b"\xff"`` are 1.
  UTF-8 ``é`` encoded as bytes is 2 (would be 1 as ``str``).
- Extract overflow / extract TypeError is a **bridge** (fall through
  to host ``LengthValidator``), not an L1 "overflow" message.

**IntegerEnum member set (Door A lock).** Host ``IntegerEnumValidator``
checks the concrete annotation, then ``isinstance(value, enum.IntEnum)``:

- Type: only members of that enum. A plain ``int`` / ``bool`` / ``str``
  / plain ``Enum`` misses, including when the integer equals a member.
  Another ``IntEnum`` misses even when its value collides. ``None`` skips.
- In-set members store that member object (aliases are the same object).
  ``0`` is kept (falsy is not ``None``).
- ``FailKind.NotMember`` uses the type-door ``TypeError`` wording
  (``expect {annotation} type, got {type} type instead``).
- Extract ``OverflowError`` is a **bridge** (fall through to host
  ``TypeValidator``), not an L1 "overflow" message. A member outside
  ``i64`` does not compile; the field stays on the host.
- Bare ``enum.IntEnum``, extra bounds (``min_value``, ``required``,
  choice, ``reassign=False``), plain ``EnumValidator``, and open
  ``Validator`` stay on the host. ``StringEnumValidator`` is its own
  closed plan. ``BooleanValidator`` is its own closed exact-bool plan,
  not this member set.

**StringEnum member set (Door A lock).** Host ``StringEnumValidator``
checks the concrete annotation, then the named extra (an ``enum.Enum``
whose ``.value`` is ``str``):

- Type: only members of that enum. A plain ``str`` misses even when it
  equals a member value. ``bytes`` / ``int`` / ``bool`` / another enum
  miss, including a colliding string and an ``IntEnum``. ``None`` skips.
- In-set members store that member object (aliases are the same object).
  An empty-string value is kept (the member is stored; falsy ``""`` is
  not ``None``).
- ``FailKind.NotMember`` uses the type-door ``TypeError`` wording
  (``expect {annotation} type, got {type} type instead``), via
  ``match fail:``.
- Extract ``OverflowError`` / ``UnicodeError`` is a **bridge** (fall
  through to host ``TypeValidator``), not an L1 "overflow" message. A
  member that is not an exact ``str``, or that cannot encode as UTF-8
  (lone surrogate), does not compile; the field stays on the host.
- Bare ``enum.Enum`` / ``enum.StrEnum``, extra bounds, plain
  ``EnumValidator``, ``IntegerEnumValidator`` on a non-``IntEnum``, and
  open ``Validator`` stay on the host. ``BooleanValidator`` is its own
  closed exact-bool plan, not this member set. There is no ``members``
  kwarg on the facade. Cap Door B stays off.

**Boolean type door (Door A lock).** Host ``BooleanValidator`` checks
``bool``, then the FFI ``bool`` extract (``apply_boolean``):

- Type: exact ``bool``. ``True`` and ``False`` both pass and are stored
  as that object. ``False`` is kept (falsy is not ``None``).
- ``1`` / ``0`` / ``str`` / ``float`` miss. No coerce of ``int`` to
  ``bool``. ``None`` skips.
- Extract TypeError is a **bridge** (fall through to host
  ``TypeValidator``), not an L1 message. There is no bound
  ``FailKind`` on this plan.
- Extra bounds (``min_value``, ``required``, choice, ``reassign=False``)
  stay on the host. ``Validator[bool]`` with only the type door is the
  same closed plan. ``Validator[bool | None]`` and plain
  ``EnumValidator`` stay on the host. An owner annotation of
  ``bool | None`` does not match ``BooleanValidator`` (bind
  ``TypeError``). Integer still treats ``True`` as ``int`` (that door
  is unchanged).

**Decimal type door (Door A lock).** Stored type is ``decimal.Decimal``
only after host pre-validate. The scale/coerce rules below are locked.
The measure cleared 3×, so the closed type door ships. Scale does not:

- Host ``DecimalValidator._pre_validate`` coerces Decimal strings
  (existing ``_coerce_str``). The peer never sees a raw ``str``.
- **Reject float.** ``float`` / ``int`` / ``bool`` miss the type door.
  No silent float→Decimal. No ``Decimal(1.23)`` path from float on
  this door.
- Exact ``decimal.Decimal`` instances pass, including ``Decimal("0")``
  (falsy is kept, not replaced by ``None``).
- **Scale.** Host has no ``max_digits`` / ``decimal_places`` /
  ``quantize`` kwargs today. Door A does not add scale units. Native
  applies the Decimal as given. Bound units are in scope only if a
  later tip closes min/max/gt/lt/eq with Decimal bounds, same family
  shape as Float. Quantize / scale / context / rounding stay HOLD /
  host.
- Cap Door B stays off. One family only. Pattern / Date* / UUID /
  Path / plain Enum stay off this tip.
- Pair naming: ``compile_decimal`` / ``apply_decimal`` (intentional
  pair — do not merge). Host ``_select_decimal`` walks the one-family
  bind list, same shape as Boolean / Float.
- String coerce stays host. Peer extract is ``decimal.Decimal`` (or a
  Rust decimal that matches host compare for closed bounds). No float
  bridge. ``rust_decimal`` only if a later bound tip needs it for
  compares.
- ``FailKind`` / host ``TypeError`` wording matches the other Door A
  families. Extract miss is a bridge to host ``TypeValidator``, not an
  L1 overflow message.
- ``None`` skips. Optional / Union annotations stay host (same as
  Boolean): ``Decimal | None`` does not match ``DecimalValidator``
  (bind ``TypeError``). The facade's coerce annotation
  ``decimal.Decimal | str`` is that host coerce door, not an open
  union — ``str`` is coerced before apply. Any other union stays host.

HOLD after this tip: Date/DateTime, UUID/Path/IP/plain EnumValidator,
Pattern / custom callables, named facades, Cap Door B. Decimal scale
/ quantize / context / rounding stay HOLD. Decimal bounds
(min/max/gt/lt/eq) stay host until a later tip closes them with
Decimal bounds.

## What never leaves the host

- ``__set__`` / ``__get__`` / ``__delete__`` (descriptor protocol)
- ``HookHost`` / ``task_*`` / async bridge
- ``AllOf`` / ``AnyOf`` as Python objects (the graph decides; a member
  *may* apply via peer)
- named-facade extras (Luhn, Verhoeff, IBAN, …) until measured
- TypedDict walk, owner annotation honesty, debug-swallow, logger
- ``ValueError`` / ``TypeError`` **wording** — peer returns a small
  error kind; host formats KEEP messages so strings do not fork

## Contract (product extra)

1. Default install has **no** native extra. ``_active_units`` stays the
   apply. ``pip install ux-valio[native]`` installs the ``ux-valio-native``
   wheel (module ``ux_valio_native`` — not a taught import).
2. Same field default. Same ``annotation``. Same fail-closed errors.
   L1 stays ``from ux_valio import IntegerValidator, StringValidator, BytesValidator, IntegerEnumValidator, StringEnumValidator, BooleanValidator, DecimalValidator``.
3. Compile at bind, not at set. Host bind walks one family list.
   Each family keeps its ``compile_*`` / ``apply_*`` pair (those doors
   stay separate). Missing peer → host apply (no import
   error on the hot path after a failed extra install: bind-time
   choice). An unclosed path does not import the extra.
4. One FFI call per set for the specified scalar plan. Not eight.
5. ``self`` is a ``PyObject*`` handle. Do not migrate the instance into
   a Rust struct. Extract scalars (``i64`` / ``f64`` / ``&str`` / ``&[u8]``
   / ``bool`` / ``decimal.Decimal``; IntegerEnum is ``i64``; StringEnum
   is the member ``.value`` as ``&str``; Boolean is exact ``bool``;
   Decimal is exact ``decimal.Decimal``, not ``f64``), apply, box back.
6. Do not re-implement the library in Rust.
7. Do not quote the switch-test ratio as end-to-end product setattr.
   The measure compared full host setattr against **plan apply only**.
8. PyO3 ``i64`` extract is the Integer range oracle. A Python int outside i64
   raises ``OverflowError`` at the FFI boundary; the host then runs
   ``ValueValidator`` (Door A KEEP wording). Overflow is a bridge
   signal, not a public validation miss and not a ``bit_length``
   pre-check. PyO3 ``f64`` extract is the Float door (``apply_float``).
   ``OverflowError`` at that extract is the same bridge (fall through
   to host ``ValueValidator``; no L1 "overflow" message). PyO3 ``&str``
   extract is the String door (``apply_string``). ``OverflowError`` /
   ``UnicodeEncodeError`` at that extract is the same bridge (fall
   through to host ``LengthValidator``; no L1 "overflow" message). PyO3
   ``&[u8]`` extract is the Bytes door (``apply_bytes``).
   ``OverflowError`` / extract TypeError at that extract is the same
   bridge (fall through to host ``LengthValidator``; no L1 "overflow"
   message). PyO3 ``i64`` extract is the IntegerEnum door
   (``apply_integer_enum``). ``OverflowError`` at that extract is the
   same bridge (fall through to host ``TypeValidator``; no L1
   "overflow" message). PyO3 ``&str`` extract is the StringEnum door
   (``apply_string_enum``, the member's ``.value``). ``OverflowError`` /
   ``UnicodeError`` at that extract is the same bridge (fall through to
   host ``TypeValidator``; no L1 "overflow" message). PyO3 ``bool``
   extract is the Boolean door (``apply_boolean``). A non-bool raises
   at that extract; host ``isinstance`` misses first, and an extract
   TypeError falls through to host ``TypeValidator`` (no coerce of
   ``1`` / ``0``, no L1 "overflow" message). PyO3 ``decimal.Decimal``
   extract is the Decimal door (``apply_decimal``). A non-Decimal
   raises at that extract; host ``isinstance`` misses first (``float``
   / ``int`` / ``bool``), and an extract TypeError falls through to
   host ``TypeValidator`` (no float bridge, no L1 "overflow" message).
   String coerce stays host ``_pre_validate``.
   ``FailKind.NotMember`` is the validation bucket
   (host type-door wording, ``match fail:``). Unexpected
   peer/infra is ``RuntimeError`` naming ``ux_valio_native``. Three
   buckets: validation (``FailKind``) / bridge (extract overflow) /
   peer-infra.

From a checkout (needs ``rustc`` / ``cargo``)::

```console
python -m pip install -e .
python -m pip install -e ./native
```

Published extra (when the native wheel is on the index)::

```console
pip install ux-valio[native]
```

Without the extra, every existing test stays on the stdlib path.

## Switch test (why this extra exists)

Build the product peer only if, on the same box, host apply of a
specified ``IntegerValidator(min_value=0)`` / ``FloatValidator(min_value=0.0)``
/ ``StringValidator(min_length=1)`` / ``BytesValidator(min_length=1)``
/ ``IntegerEnumValidator()`` on a concrete ``IntEnum``
/ ``StringEnumValidator()`` on a concrete str-valued ``Enum``
/ ``BooleanValidator()`` (exact ``bool``)
/ ``DecimalValidator()`` (exact ``decimal.Decimal``; no float bridge)
setattr stays several times slower than a one-shot native apply of that
same plan, and the Python compile (``_active_units``, skip TypedDict,
skip watch) is already in.

**Bar.** FAIL (KEEP Python) unless host ns/op is **≥ 3×** native ns/op.
Three times is “several”; below that, FFI + a later extra is not worth
the door risk.

### How to run

The harness lives in-tree. It installs/uses ``ux-valio`` from the repo
root. Hot path A is many ``setattr``s on a dataclass ``Box.n`` with a
closed ``IntegerValidator`` or ``FloatValidator`` bound plan, a closed
``StringValidator`` / ``BytesValidator`` length plan, or a closed
``IntegerEnumValidator`` member-set plan, or a closed
``StringEnumValidator`` UTF-8 member-set plan, or a closed
``BooleanValidator`` exact-bool type door, or a closed
``DecimalValidator`` exact-Decimal type door (values are ``Decimal``
instances, so string coerce is not in the apply-only comparison). Hot
path B is ``compile_integer(...)``
/ ``compile_float(...)`` / ``compile_string(...)`` / ``compile_bytes(...)``
/ ``compile_integer_enum(...)`` / ``compile_string_enum(...)`` /
``compile_boolean()`` / ``compile_decimal()``
once then ``apply_integer`` /
``apply_float`` / ``apply_string`` / ``apply_bytes`` /
``apply_integer_enum`` / ``apply_string_enum`` / ``apply_boolean`` /
``apply_decimal`` on the
product peer (``native/``: private ``Plan`` enum, one variant per
family — Integer / Float own bound units, String / Bytes own length
units, IntegerEnum / StringEnum own their member sets, Boolean and
Decimal are type-door markers; public ``compile_*`` / ``apply_*``
names unchanged). B is **not** product setattr (no store, no
hooks, no host raise). The harness prints one host-vs-apply ratio per
family; the bar is **≥ 3×** for each. A family below the bar is
KEEP host for that family (do not claim native).

```console
python -m pip install -e .
python benches/measure_host_peer.py
python benches/measure_host_peer.py --ci    # never builds Rust; SKIP or smoke
```

Local run needs ``rustc`` / ``cargo`` and will ``pip install maturin``
then ``maturin develop --release`` the peer into the current
interpreter if ``ux_valio_native`` is missing. GitHub Actions has no
Rust toolchain: ``--ci`` (and ``tests/test_host_peer_measure.py``) skip
with that reason, exit 0. Native parity tests
(``tests/test_native_peer.py``) skip without the extra; the rest of
the suite is the stdlib path.

Do not ``from __future__ import annotations`` on the measured ``Box``:
postponed ``int`` TypeErrors at bind (KEEP).

### Measured (2026-09-21)

Same box, two consecutive runs, 400000 iters after 20000 warmup,
values ``(0..7)``, CPython 3.14.7, rustc 1.83.0, Linux x86_64 (Intel
Xeon, 4 CPUs). Peer is a release cdylib. Host units were
``_validate_type`` then ``_validate_value``.

| path | wall (run 1 / 2) | ns/op |
|---|---|---|
| A ``setattr`` ``IntegerValidator(min_value=0)`` | 1.355 s / 1.406 s | 3389 / 3515 |
| B native ``apply_integer(plan, i64)`` MinValue(0) | 0.0185 s / 0.0186 s | 46.2 / 46.5 |
| host / native | | **73× / 76×** |

Honesty: A is the taught descriptor (``__set__``, specified units, store
on ``instance.__dict__``). B is plan apply only (one FFI, no store, no
hooks). That is the switch the map asked for, **not** a claim that
product setattr is 70× end-to-end after host raise/store. Product
``apply_integer`` releases the GIL (``Python::detach``; PyO3 0.29 name for
``allow_threads``), so a local re-run of B is slower than the stub’s
46 ns/op and still PASSes the 3× bar.

Rename-only re-run on the same box (plan units ``Integer`` +
``MinValue(0)``, same apply): host 3491–3672 ns/op, native 46.8–49.0
ns/op, ratio **75×**. Same PASS.

**Verdict: PASS (native extra shipped for closed Integer bound plans).** Host
stayed several times slower than the one-shot native apply (bar 3×).
This extra binds those plans at construct. Cap Door B, JSON-per-set,
migrating ``self`` into Rust, a Field/Schema twin, a mega shared plan
crate, and email/named identity as a first target stay rejected.

### Measured (2026-09-21) Integer bound families

Same class of box, one run, 400000 iters after 20000 warmup, values as
each family allows, CPython 3.14.7, rustc 1.83.0, Linux x86_64. Peer is
a release cdylib. Host units were ``_validate_type`` then
``_validate_value``. B is plan apply only (``Python::detach``).

| family | A setattr ns/op | B apply ns/op | host / native |
|---|---|---|---|
| MinValue(0) | 2341 | 95.0 | **24.6×** |
| MaxValue(10) | 2299 | 94.4 | **24.4×** |
| GreaterThan (host ``gt=0``) | 2303 | 94.7 | **24.3×** |
| LessThan (host ``lt=10``) | 2312 | 94.5 | **24.5×** |
| Equal (host ``eq=7``) | 2315 | 93.6 | **24.7×** |
| MinValue(0)+MaxValue(10) | 2415 | 99.4 | **24.3×** |

**Verdict: PASS.** Every family, including new ones besides MinValue,
cleared the 3× bar. Native apply here is ~95 ns/op (GIL released),
slower than the first stub’s 46 ns/op and still not a 70× product
setattr claim.

### Measured (2026-09-21) Float bound families

Same class of box, one run, 400000 iters after 20000 warmup, CPython 3.14.7,
rustc 1.83.0, Linux x86_64. Peer is a release cdylib. Host units were
``_validate_type`` then ``_validate_value``. B is
``apply_float(plan, f64)`` only (``Python::detach``). IEEE NaN/inf is
Door A (not part of the hot-path values). Bar 3× per family.

| family | A setattr ns/op | B apply ns/op | host / native |
|---|---|---|---|
| MinValue(0.0) | 2441 | 92.4 | **26.4×** |
| MaxValue(10.0) | 2451 | 93.2 | **26.3×** |
| GreaterThan (host ``gt=0.0``) | 2455 | 93.4 | **26.3×** |
| LessThan (host ``lt=10.0``) | 2515 | 93.8 | **26.8×** |
| Equal (host ``eq=7.0``) | 2515 | 93.5 | **26.9×** |
| MinValue(0.0)+MaxValue(10.0) | 2441 | 92.0 | **26.5×** |

**Verdict: PASS.** Every Float family cleared the 3× bar (~26×). Native
apply here is ~93 ns/op (GIL released), not a 70× product setattr
claim. Integer families on the same run stayed ~24× (still PASS).

### Measured (2026-09-21) String length families

Same class of box, one run, 400000 iters after 20000 warmup, CPython 3.14.7,
rustc 1.83.0, Linux x86_64. Peer is a release cdylib. Host units were
``_validate_type`` then ``_validate_length``. B is
``apply_string(plan, &str)`` only (``Python::detach``). Count is
codepoints (``chars().count()``), matching host ``len(str)``. Bar 3×
per family.

| family | A setattr ns/op | B apply ns/op | host / native |
|---|---|---|---|
| MinLength(1) | 2450 | 95.6 | **25.6×** |
| MaxLength(10) | 2424 | 94.6 | **25.6×** |
| Length (host ``length=3``) | 2445 | 96.7 | **25.3×** |
| MinLength(1)+MaxLength(10) | 2399 | 94.8 | **25.3×** |

**Verdict: PASS.** Every String family cleared the 3× bar (~25×). Native
apply here is ~95 ns/op (GIL released), not a 70× product setattr
claim. Integer families on the same run stayed ~24–26× and Float
~25–27× (still PASS).

### Measured (2026-09-21) Bytes length families

Same class of box, one run, 400000 iters after 20000 warmup, CPython 3.14.7,
rustc 1.83.0, Linux x86_64. Peer is a release cdylib. Host units were
``_validate_type`` then ``_validate_length``. B is
``apply_bytes(plan, &[u8])`` only (``Python::detach``). Count is
``len()`` of the extracted bytes, matching host ``len(bytes)``. Bar 3×
per family.

| family | A setattr ns/op | B apply ns/op | host / native |
|---|---|---|---|
| MinLength(1) | 2434 | 94.8 | **25.7×** |
| MaxLength(10) | 2390 | 94.2 | **25.4×** |
| Length (host ``length=3``) | 2417 | 95.7 | **25.3×** |
| MinLength(1)+MaxLength(10) | 2414 | 93.2 | **25.9×** |

**Verdict: PASS.** Every Bytes family cleared the 3× bar (~25×). Native
apply here is ~94 ns/op (GIL released), not a 70× product setattr
claim. Integer families on the same run stayed ~24–25×, Float
~25–26×, and String ~24–25× (still PASS).

### Measured (2026-09-21) IntegerEnum member set

Same class of box, one run, 400000 iters after 20000 warmup, CPython 3.14.7,
rustc 1.83.0, Linux x86_64. Peer is a release cdylib. Host units were
``_validate_type`` only. Path A clears the native plan after bind so
setattr is pure Python. B is ``apply_integer_enum(plan, i64)`` only
(``Python::detach``). Members are the concrete ``IntEnum`` values
``0..7``. Bar 3×.

| family | A setattr ns/op | B apply ns/op | host / native |
|---|---|---|---|
| Member(0..7) | 3264 | 94.6 | **34.5×** |

**Verdict: PASS.** The IntegerEnum member set cleared the 3× bar
(34.5×). Native apply here is ~95 ns/op (GIL released), not a 70×
product setattr claim. Integer / Float / String / Bytes families on
the same run stayed ~24–26× (still PASS).

HOLD at the end of the IntegerEnum measure was StringEnum (shipped in
the next section). Boolean only if a later measure is ≥3× alone.
Decimal, Date/DateTime, UUID/Path, Pattern, plain EnumValidator,
named facades, Cap Door B stay off this path.

### Measured (2026-09-21) StringEnum member set

Same class of box, one run, 400000 iters after 20000 warmup, CPython 3.14.7,
rustc 1.83.0, Linux x86_64. Peer is a release cdylib. Host units were
``_validate_type`` only. Path A clears the native plan after bind so
setattr is pure Python. B is ``apply_string_enum(plan, &str)`` only
(``Python::detach``). Members are the concrete enum values ``m0``..``m7``.
Bar 3×.

| family | A setattr ns/op | B apply ns/op | host / native |
|---|---|---|---|
| Member(m0..m7) | 3421 | 108.1 | **31.7×** |

**Verdict: PASS.** The StringEnum UTF-8 member set cleared the 3× bar
(31.7×). Native apply here is ~108 ns/op (GIL released; the query is
one owned ``String``), not a 70× product setattr claim. Integer /
Float / String / Bytes families on the same run stayed ~24–25× and
IntegerEnum stayed ~35× (still PASS).

HOLD after the StringEnum tip was Boolean, measured in the next
section.

### Measured (2026-09-21) Boolean type door

Same class of box, one run, 400000 iters after 20000 warmup, values
``(True, False)`` repeated, CPython 3.14.7, rustc 1.83.0, Linux x86_64
(Intel Xeon, 4 CPUs). Peer is a release cdylib
(``python -m pip install maturin`` then ``maturin develop --release``
via ``python benches/measure_host_peer.py``). Host units were
``_validate_type`` only. Path A clears the native plan after bind so
setattr is pure Python. B is ``apply_boolean(plan, bool)`` only
(``Python::detach``). The type door is exact ``bool`` (smoke:
``apply_boolean(plan, 1)`` raises ``TypeError``; ``0`` is not coerced).
Bar 3×.

| family | A setattr ns/op | B apply ns/op | host / native |
|---|---|---|---|
| exact bool | 2991.4 | 80.0 | **37.40×** |

**Verdict: PASS.** The Boolean exact-bool type door cleared the 3× bar
(37.40×). Native apply here is ~80 ns/op (GIL released), not a 70×
product setattr claim. Integer / Float / String / Bytes families on
the same run stayed ~27–29×, IntegerEnum ~38×, and StringEnum ~31×
(still PASS).

```console
python benches/measure_host_peer.py
```

HOLD after the Boolean tip was Decimal, measured in the next section.

### Measured (2026-09-22) Decimal type door

Same class of box, one run, 400000 iters after 20000 warmup, values
``Decimal("1.23")`` / ``Decimal("0")`` / ``Decimal("2.50")`` /
``Decimal("10")`` / ``Decimal("0.01")`` / ``Decimal("4")``, CPython
3.14.7, rustc 1.83.0, Linux x86_64 (Intel Xeon, 4 CPUs). Peer is a
release cdylib (``python -m pip install maturin`` then
``maturin develop --release`` via
``python benches/measure_host_peer.py``). Host units were
``_validate_type`` only. Path A clears the native plan after bind so
setattr is pure Python (``DecimalValidator`` still runs host string
coerce and the named Decimal extra; the measured values are already
``Decimal``, so coerce does not parse). B is ``apply_decimal(plan,
Decimal)`` only (``Python::detach``). The type door is exact
``decimal.Decimal`` (smoke: ``apply_decimal(plan, 1.23)`` raises
``TypeError``; ``float`` / ``int`` / ``bool`` / raw ``str`` are not
coerced; ``Decimal("0")`` passes). No scale unit. Bar 3×.

| family | A setattr ns/op | B apply ns/op | host / native |
|---|---|---|---|
| exact Decimal | 6155.1 | 79.8 | **77.09×** |

**Verdict: PASS.** The Decimal exact-Decimal type door cleared the 3×
bar (77.09×). Native apply here is ~80 ns/op (GIL released), not a 70×
product setattr claim. Host setattr is slower than the Boolean type
door because ``DecimalValidator`` still runs ``_pre_validate`` and the
named Decimal extra on the Python path. Integer / Float / String /
Bytes families on the same run stayed ~28–30×, IntegerEnum ~41×,
StringEnum ~33×, and Boolean ~38× (still PASS).

```console
python benches/measure_host_peer.py
```

HOLD after this tip: Date/DateTime, UUID/Path, Pattern, plain
EnumValidator, named facades, Cap Door B stay off this path. Decimal
scale / quantize / context / rounding stay HOLD. Decimal bounds
(min/max/gt/lt/eq) stay host.
