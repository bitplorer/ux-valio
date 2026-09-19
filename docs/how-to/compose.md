# Compose

You compose when **one field** has several independent rules, or when
the value may be one of two types. The result is still **one**
descriptor — one dataclass default, one hang target.

Concern leaves (`LengthValidator`, `RequiredValidator`, …) are the
**advanced** path: compose validator objects with `&` (AllOf) / `|`
(AnyOf), or explicit `AllOf` / `AnyOf`, as **one** descriptor. Facades
do not multiple-inherit leaves. You do not write
`class Password(StringValidator, DigitMixin)`.

## When to use which

| I need… | Write | Not |
|---|---|---|
| Long **and** has a digit **and** has a letter | `AllOf(StringValidator(min_length=8), StringValidator(pattern=Digit(count_min=1)), …)` | `Digit(count_min=1) & SetOf(...)` — that concatenates into one regex |
| A SKU that is `INV-` then 4 digits then `Z` | `StartsWith(Pattern(r"INV-")) & Digit(count=4) & EndsWith(Pattern(r"Z"))` | `AllOf` of three StringValidators — order in the string is Pattern `&` |
| int **or** str | `IntegerValidator() \| StringValidator()` | `Validator()` with no annotation — that accepts anything |
| Present **and** at least 3 chars | `StringValidator(required=True, min_length=3)` | a hang `if not value` on top of `required` |

`required=True` rejects `None`. `min_length=1` rejects `""`. Do not hang
`if not value` on top of either — that repeats the door. Hang a rule the
leaves do not already own (reserved name, uniqueness, strip).

```python
from dataclasses import dataclass
from ux_valio import LengthValidator, RequiredValidator, StringValidator

# Two leaves, one descriptor. None vs empty string are different doors.
tag: str = LengthValidator(min_length=3) & RequiredValidator(required=True)

RESERVED = {"admin", "root", "system"}

@dataclass
class Handle:
    handle: str = StringValidator(min_length=3, max_length=20, required=True)

    @handle.pre_validate
    def fold(self, value: str) -> str:
        return value.strip().casefold()

    @handle.post_validate
    def not_reserved(self, value: str) -> str:
        if value in RESERVED:
            raise ValueError("reserved handle")
        return value
```

`Handle(handle=None)` fails `required`. `Handle(handle="")` fails
`min_length`. `Handle(handle="Admin")` folds to `"admin"` and then the
reserved hang raises. That reserved set is not a leaf — it is policy.

## Pattern `&` vs `AllOf`

Pattern types (`Digit`, `StartsWith`, `SetOf`) combine with `&` into
**one** finder. `"INV-" & Digit(count=4)` means the substring `INV-`
immediately followed by four digits (findall substring, not fullmatch).
See [Pattern](../reference/pattern.md).

`AllOf` combines **validators**. Each member runs on the same value.
Password strength is three validators, not one concatenated regex,
because a digit may appear anywhere.

```python
from ux_valio import AllOf, Digit, Pattern, SetOf, StringValidator

password = AllOf(
    StringValidator(required=True, min_length=8, max_length=128),
    StringValidator(pattern=Digit(count_min=1)),
    StringValidator(pattern=SetOf(Pattern(r"A-Za-z"), count_min=1)),
)
```

## OR (`|` / `AnyOf`)

`|` is OR: `IntegerValidator | StringValidator` is AnyOf. Conflicting
member annotations do not TypeError. The compose root does not AND-run a
type check before alternatives. `&` / `AllOf` still TypeErrors on
conflicting member annotations.

Use this for a field that is honestly two types (a note that is an int
id **or** a free-text label). Do not use it to smuggle `None` — that is
`annotation = T | None` and `default=None`.

`&` / `|` return `AllOf` / `AnyOf` from `ValidateProperty` — same
module as the operators, no per-use import.

## Compose-time conflicts

Composing members that specify different `debug`, `default`, or
`default_factory` values raises `TypeError`. Explicit
`collect_all=False` / `logger=False` is specified: it TypeErrors against
explicit `True`. An omitted `collect_all` / `logger` / `debug` stays
unspecified (resolved True / OFF / True) so it still collapses to a
specified `True`.

That TypeError is at **class body**, not at first assignment — you find
the conflict when you write the field, not in production.
