# Why it looks like this

Every KEEP below is a usage-facing choice, not a style preference.
If a later change fights one of these, the library becomes a second
door (Field, Schema, BaseModel, or a silent valio leftover).

## The field default *is* the validator

```python
name: str = StringValidator(max_length=50)
```

Pydantic’s `name: str = Field(max_length=50)` is two objects: a type
annotation and a Field twin. Valio@3415c03 already used a descriptor as
the default. ux-valio keeps that: one object owns identity, hooks, and
storage. There is no Field twin and no Schema twin.

**Usage.** You hang `@name.pre_validate` on the same object the dataclass
already assigned. You do not look up `User.__dataclass_fields__["name"]`.

**Performance.** Bind (`__set_name__`, specified-path compile) happens
once per class. Set is the hot path. A Field twin would add a second
object and a second lookup per set.

**Do not** use bare `Property` as the field default — it is the
descriptor base (store only), not a product facade.

## Descriptor, not a BaseModel

The instance is your dataclass (or plain class, or TypedDict mapping).
The library never subclasses your type. That is why ports are ordinary
fields (`users: UserStore = field(default=Validator[UserStore]())`)
and why `@dataclass(frozen=True)` works (`FrozenInstanceError` fires
before the descriptor mutates). `@dataclass(slots=True)` does **not**:
dataclass replaces the descriptor after bind, so validation would not
run. Store lives on `instance.__dict__`.

## Process vs task

| hang | waits | use |
|---|---|---|
| `pre_validate` / `validator` / `post_validate` / `post_set` | yes | identity, uniqueness, persist |
| `task_*` | no | welcome email, metrics |

Process is the pipeline. Tasks spawn; the setter does not wait.
`from ux_valio import wait_tasks` is for tests and shutdown. A persist
that must fail-closed is `post_set`, never `task_post_set`. There is no
hang named `pre_set` — `_run_pre_set` *is* the validate pipeline.

## Uniqueness after identity

`pre_validate` transforms. `validate()` is identity (length, checksum).
`post_validate` is the store lookup. An invalid name never hits the
database. Persist/reserve hangs on `post_set` of the **last** field so
a failed later field does not consume the name.

## Ports are fields, not InitVar

Generated `__init__` assigns in declaration order, then `__post_init__`.
`InitVar` is not stored and arrives in `__post_init__` **after** product
fields already ran uniqueness. Hand-written `init=False` `__init__`
duplicates every field. The organic pattern:

```python
users: UserStore = field(
    default=Validator[UserStore](required=True),
    repr=False,
    compare=False,
)
username: str = StringValidator(...)
```

`@runtime_checkable` is required for Protocol `isinstance`. See
[workflows](../how-to/workflows.md).

## Defaults that match how people actually call

| kwarg | omitted | why |
|---|---|---|
| `debug` | `True` | fail closed; `debug=False` is the swallow (KEEP) |
| `collect_all` | `True` | one field, several concerns, one `ValidationErrors` |
| `logger` | `False` | no surprise files; `logger=True` is `module.qualname.field` |
| `required` | `False` | `None` is optional unless you say otherwise |

Do not overload `debug` into collect-all. One failure re-raises as
itself; two or more become `ValidationErrors` (debug on) or `errors`
entries (debug off).

`logger=None` is OFF, not valio’s None=on.

## Specified path, compiled once

`min_value` / `pattern` / `reassign=False` bind at construct into
`_active_units`. Type always runs. Mutating those kwargs after
`__init__` does not rebuild the path. Unknown unit: `ValueError`, not
`KeyError`. That compile is why unconstrained `int` set is a short
Python loop, not a walk of every possible leaf.

## `AllOf` / `AnyOf` are objects, not mixins

Facades do not multiple-inherit leaves. `tag: str = LengthValidator(...) & RequiredValidator(...)`
is one descriptor. `|` is OR: the compose root does
not AND-run a type check before alternatives. Conflicting specified
`debug` / `default` / `default_factory` / `collect_all` / `logger` is
`TypeError` at compose, not a silent pick.

## Pattern is findall

`PatternValidator` uses `re.findall` (findall substring), not
`fullmatch`. Empty-match `a*` still counts. `EmailValidator` keeps that
engine for `pattern=` and then requires the whole string to be an
addr-spec. `&` concatenates; independent “has a digit” / “has a letter”
are separate StringValidators under `AllOf`. `Contained` / `IfContained`
are KEEP-absent.

## Named identities store compact form

Print grouping strips. Stored value is the compact identity (GSTIN 15
chars, card digits, IBAN registry length). Stdlib only — no portal, no
DNS, no BIN lookup. Extra check runs from `validate()` after the
inherited path and joins `collect_all`.

## TypedDict is the schema

No BaseModel. Extra keys fail-closed. `total=False` / `Required` /
`NotRequired` are the metaclass. Hang extras with `Annotated` or
`name: str = StringValidator()`, then `@name.pre_validate` /
`@name.validator` in the TypedDict body. `self` is the mapping.

## Construction is `Any` to type checkers

`name: str = StringValidator()` must type-check. Runtime the instance
sees `str`. `ValidateProperty.__new__` plus `plugins = ["ux_valio.mypy_plugin"]`
is that contract. No `AsStr` / `AsUser` mixin. `Validator[int]` fills
`annotation` when the class did not declare one. Unconstrained `TypeVar`
is typing-only (one descriptor cannot specialize per `Box[int]`).

Owner `from __future__ import annotations` strings TypeError at bind —
drop postponed annotations on these fields.

## What is not shipped

No Cap Host, Cap Door B / Ops / JSON on the field path, `rule/`, Result
type, RGB/HSL, star-import barrel, `AttributeValidator`, list/dict/set/tuple
collection facades, `enable_async`, `cache_task`, `add_pre_set`. List
membership is `list[T]` on the type door. Object attributes: check at the
call site or hang `validator`. Optional `ux-valio[native]` is not a second
door: L1 stays `IntegerValidator` / `FloatValidator` / `StringValidator` /
`BytesValidator` / `IntegerEnumValidator` / `StringEnumValidator` /
`BooleanValidator` / `DecimalValidator` / `DateValidator` /
`DateTimeValidator`; the extra is compile-once + one FFI
apply for closed Integer and Float bound units (min/max/gt/lt/eq),
closed String / Bytes length units (min/max/exact), a closed
IntegerEnum member set (`compile_integer_enum` / `apply_integer_enum`),
a closed StringEnum UTF-8 member set (`compile_string_enum` /
`apply_string_enum`), and a closed Boolean exact-bool type door
(`compile_boolean` / `apply_boolean`; `1` / `0` are not coerced), and a
closed Decimal exact-Decimal type door (`compile_decimal` /
`apply_decimal`; `float` / `int` / `bool` are not coerced; no scale
unit), and a closed Date type door (`compile_date` / `apply_date`;
string coerce stays host), and a closed DateTime type door
(`compile_datetime` / `apply_datetime`; a plain `date` misses),
and a closed Uuid type door (`compile_uuid` / `apply_uuid`; string
coerce stays host), and a closed IP string-identity door
(`compile_ip` / `apply_ip`; `IPv4Validator` / `IPv6Validator` /
`IPAddressValidator` store the given string; no coerce to
`ipaddress` objects), and a closed Path type door
(`compile_path` / `apply_path`; string coerce stays host;
`path_exists` stays host; `PurePath` misses).
Pattern and named identity stay on the host. Next: Pattern and
plain EnumValidator stay off this path. Decimal scale /
quantize stays HOLD. Date and DateTime bounds stay host. Uuid
bounds stay host. IP length / pattern / choice stay host. Path
bounds and `path_exists` stay host. No follow-up remains on this
Path concern.
