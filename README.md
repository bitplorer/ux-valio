# ux-valio

Door A descriptor-on-dataclass validation. Greenfield reimplementation of
[`bitplorer/valio`](https://github.com/bitplorer/valio) frozen at
[`3415c03`](https://github.com/bitplorer/valio/commit/3415c03e37085adda4040671a91eb19aa4fe4ac4)
(Soft 10). Valio itself is not edited.

## Install

```console
pip install -e .
```

## Door A

The public caller shape is a validator as the dataclass field default:

```python
from dataclasses import dataclass
from ux_valio import IntegerValidator, StringValidator, Validator

@dataclass
class User:
    name: str = StringValidator(debug=True, max_length=50, required=True)
    rank: str = Validator(in_choice=["Male", "Female", "Trans"], default="Female")
    n: int = IntegerValidator(min_value=0, max_value=10, multiple_of=2, debug=True)
```

There is no Field twin and no Schema twin. `field: T = SomeValidator(...)` is
the door.

## KEEP: debug swallow, logger OFF

- `debug=True` re-raises on a failed set/get/delete.
- `debug` falsy (including the default `None`) swallows the exception, appends
  it to `errors`, and leaves the attribute unset so later reads are `None`.
  This swallow is KEEP. Soft 1 does not flip the product to fail-closed-by-default.
- `logger` defaults **OFF** (`False`). Valio's `logger=None` enabled file
  logging; ux-valio does not.

Assigned `0` / `False` / `""` are not replaced by `default`. `None` is.
Bound `0` is specified: `min_value`/`max_value` inclusive, `gt`/`lt`
exclusive, `multiple_of` is remainder, `multiple_of=0` accepts only `0`.

`PatternValidator` matches with `re.findall` (substring), not `fullmatch`.

## Migration (Door B → Door A)

Valio README taught a second door: construct a `*Field`, hang decorators on
it, then assign `password: str = password_field.validator`. That Field factory
duplicated kwargs, dropped `gt`/`lt`/`eq`/`multiple_of`/`in_choice` from its
signature, and is untested. ux-valio retires Door B. Move the kwargs onto
`StringValidator` / `IntegerValidator` / `Validator` as the dataclass default,
and hang `add_pre_validator` / `add_validator` on that descriptor. Star-import
of valio's 306 names is gone; import the names in `__all__`.

## Soft 1 surface

`Validator`, `StringValidator`, `IntegerValidator`, `BooleanValidator`,
`TypeValidator`, `RequiredValidator`, `PatternValidator`, `LengthValidator`,
`ValueValidator`, `MultipleValidator`, `ChoiceValidator`, `ReassignValidator`,
and `Pattern` / `PatternType` combinators (`&` / `|`). Concern leaves compose
on an ordered path. No multiple inheritance, no Cap Host, no `rule/`.
