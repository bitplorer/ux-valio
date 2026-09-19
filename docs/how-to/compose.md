# Compose

Concern leaves (`LengthValidator`, `RequiredValidator`, …) are the
**advanced** path: compose validator objects with `&` (AllOf) / `|`
(AnyOf), or explicit `AllOf` / `AnyOf`, as **one** descriptor. `Chain`
is `AllOf` — an alias, not a third AND. Facades do not multiple-inherit
leaves.

```python
from dataclasses import dataclass
from ux_valio import LengthValidator, RequiredValidator, StringValidator

tag: str = LengthValidator(min_length=3) & RequiredValidator(required=True)

@dataclass
class User:
    name: str = StringValidator(max_length=50) & RequiredValidator(
        required=True
    )

    @name.pre_validate
    def strip(self, value: str) -> str:
        return value.strip()

    @name.validator
    def not_blank(self, value: str) -> None:
        if not value:
            raise ValueError("blank")
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
