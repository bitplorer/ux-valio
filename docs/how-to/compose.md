# Compose

Concern leaves (`LengthValidator`, `RequiredValidator`, …) are the
**advanced** path: compose validator objects with `&` (AllOf) / `|`
(AnyOf), or explicit `AllOf` / `AnyOf`, as **one** descriptor. `Chain`
is `AllOf` — an alias, not a third AND. Facades do not multiple-inherit
leaves.

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

    @handle.validator
    def not_reserved(self, value: str) -> None:
        if value in RESERVED:
            raise ValueError("reserved handle")
```

`&` / `|` return `AllOf` / `AnyOf` from `ValidateProperty` — same
module as the operators, no per-use import.

`|` is OR: `IntegerValidator | StringValidator` is AnyOf. Conflicting
member annotations do not TypeError. The compose root does not AND-run a
type check before alternatives. `&` / `AllOf` still TypeErrors on
conflicting member annotations.

Composing members that specify different `debug`, `default`, or
`default_factory` values raises `TypeError`. Explicit
`collect_all=False` / `logger=False` is specified: it TypeErrors against
explicit `True`. An omitted `collect_all` / `logger` / `debug` stays
unspecified (resolved True / OFF / True) so it still collapses to a
specified `True`.
