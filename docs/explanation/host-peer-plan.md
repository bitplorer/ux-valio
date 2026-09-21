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
                    peer applies  (i64 / f64 / &str / &[u8] extract; bound, length, or member units)
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
``IntegerEnum`` plus ``Member(i64)`` values taken from the concrete
``enum.IntEnum`` on the field.
``IntegerValidator(min_value=0)``, ``max_value=10``, ``gt=0``,
``eq=7``, and ``min_value=0, max_value=10`` compile when the
annotation is ``int`` and only those bound units are active.
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
concrete ``IntEnum`` subclass (not ``enum.IntEnum`` itself, not
``IntFlag``) and only the type unit is active. Member values are that
enum's ``i64`` set (aliases that share a value are one member).
Unclosed paths (``required``, ``multiple_of``, pattern, choice, named
identity, Email, a mixed bound type, Union / TypedDict /
Annotated, plain ``EnumValidator``, ``StringEnumValidator``, open
``Validator[SomeIntEnum]``) stay on the host. Email / named identity
were already competitive in Python — do not start there.

Closed Integer **type door** is the FFI ``i64`` extract. Closed Float
**type door** is the FFI ``f64`` extract (``apply_float``). Bound units
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
accepts a member of the concrete ``IntEnum`` on the field and rejects
everything else with the type-door ``TypeError``:

- In-set members store, including aliases that share an integer.
- A different ``IntEnum`` misses even when ``.value`` is the same
  integer (``Other.LOW`` is not ``Rank.LOW``).
- Plain ``int`` / ``bool`` / ``str`` / a non-int ``Enum`` miss. With
  ``collect_all`` the named extra adds the ``IntEnum`` type error.
- ``None`` skips.
- ``FailKind.Member`` is the set miss. Host wording is that same
  type-door ``TypeError``, not a second sentence.
- A member outside ``i64`` keeps the enum on the host. ``OverflowError``
  at extract is a **bridge** (fall through to host ``TypeValidator``),
  not an L1 "overflow" message.

HOLD this tip: StringEnum. Boolean (only if later measure ≥3×), Decimal
(scale/coerce unlocked), Date/DateTime, UUID/Path/IP/plain
EnumValidator, Pattern / custom callables, named facades, Cap Door B.

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
   L1 stays ``from ux_valio import IntegerValidator, StringValidator, BytesValidator, IntegerEnumValidator``.
3. Compile at bind, not at set. Missing peer → host apply (no import
   error on the hot path after a failed extra install: bind-time
   choice).
4. One FFI call per set for the specified scalar plan. Not eight.
5. ``self`` is a ``PyObject*`` handle. Do not migrate the instance into
   a Rust struct. Extract scalars (``i64`` / ``f64`` / ``&str`` / ``&[u8]``), apply, box back.
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
   "overflow" message). ``compile_integer_enum`` and
   ``apply_integer_enum`` stay separate doors. Unexpected
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
``IntegerEnumValidator`` member set. Hot path B is ``compile(...)``
/ ``compile_float(...)`` / ``compile_string(...)`` / ``compile_bytes(...)``
/ ``compile_integer_enum(...)``
once then ``apply`` /
``apply_float`` / ``apply_string`` / ``apply_bytes`` /
``apply_integer_enum`` on the
product peer (``native/``: owned unit list of ``Integer`` or ``Float``
plus ``MinValue`` / ``MaxValue`` / ``GreaterThan`` / ``LessThan`` /
``Equal``, or ``String`` / ``Bytes`` plus ``MinLength`` / ``MaxLength`` /
``Length``, or ``IntegerEnum`` plus ``Member(i64)``). B is **not** product setattr (no store, no
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
| B native ``apply(Integer, MinValue(0))`` | 0.0185 s / 0.0186 s | 46.2 / 46.5 |
| host / native | | **73× / 76×** |

Honesty: A is the taught descriptor (``__set__``, specified units, store
on ``instance.__dict__``). B is plan apply only (one FFI, no store, no
hooks). That is the switch the map asked for, **not** a claim that
product setattr is 70× end-to-end after host raise/store. Product
``apply`` releases the GIL (``Python::detach``; PyO3 0.29 name for
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

HOLD after IntegerEnum: StringEnum. Boolean only if later measure ≥3×.
Decimal, Date/DateTime, UUID/Path, Pattern, named facades, Cap Door B
stay off this path.

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
