# Typed facades

A typed facade is a `Validator` whose stored type is already filled in.
You use `IntegerValidator` when the field is an `int`, not `Validator()`
plus a hope. Construction is `Any` to type checkers, so
`name: str = StringValidator()` assigns. `help(IntegerValidator)` is the
Usage contract.

**Where:** dataclass columns, TypedDict keys, plain-class attributes.
Pick the facade that matches what you want **on the instance after
assignment** (a `date`, not the string you typed).

| facade | stores | when you use it |
|---|---|---|
| `IntegerValidator` | `int` | seats, quantity, age, reputation |

`IntegerValidator(min_value=0)` is the taught field default. Optional
`ux-valio[native]` may compile that closed path once and apply in one
FFI; without the extra the same units run in Python. Call sites do not
change. See [host / peer](../explanation/host-peer-plan.md).
| `StringValidator` | `str` | names, slugs (without a named identity) |
| `BooleanValidator` | `bool` | flags; `False` is kept (not replaced by default) |
| `FloatValidator` | `float` | measurements that are allowed to be binary float |
| `DecimalValidator` | `decimal.Decimal` | money; coerces Decimal strings; **rejects float** |
| `BytesValidator` | `bytes` | raw tokens, digests |
| `DateValidator` | `datetime.date` | EU `YYYY-MM-DD` / IND `DD-MM-YYYY` (`-` `/` `:`); `datetime.datetime` rejected; owner may be `date`, `str`, or `T \| str` |
| `DateTimeValidator` | `datetime.datetime` | ISO via `fromisoformat`; plain `date` rejected; owner may be `datetime`, `str`, or the union |
| `UUIDValidator` | `uuid.UUID` | coerces UUID strings; owner may be `uuid.UUID`, `str`, or `uuid.UUID \| str` |
| `PathValidator` | `pathlib.Path` | coerces `str`; owner may be `Path`, `str`, or the union; `path_exists=True` requires the path to exist |
| `IPv4Validator` | given string | host literals, allow-lists |
| `IPv6Validator` | given string | |
| `IPAddressValidator` | given string | v4 or v6 |
| `EnumValidator` | `enum.Enum` | closed sets you already modelled as Enum |
| `IntegerEnumValidator` | `enum.IntEnum` | |
| `StringEnumValidator` | str Enum member | |

Money: use `DecimalValidator`, not `FloatValidator`.
`DecimalValidator(min_value=Decimal("0.01"))` on a checkout `amount`.
A Python `float` is rejected so `19.99` from JSON should arrive as a
string or a `Decimal`.

## Dates

`DateValidator` stores `datetime.date`. Numeric EU (`YYYY-MM-DD`, also
`/` and `:`) and IND (`DD-MM-YYYY`, also `/` and `:`) strings parse on
assignment; the same delimiter must appear on both sides. `02/01/2020`
is 2 January 2020 (IND), not 1 February (US). Month names, ordinals,
dots, and pyparsing `scanString` from valio `relib/dates.py` are not
ported.

Pass a `datetime.datetime` and you get `TypeError` — that is
`DateTimeValidator`. Filing both calendars: `examples/filing.py`.

`UUIDValidator` (coerces UUID strings; stores `uuid.UUID`; owner
annotation may be `uuid.UUID`, `str`, or `uuid.UUID | str`).

RGB/HSL color validators are retired. `HexColorValidator` is not a
public facade. For a hex tint use `StringValidator(pattern=SetOf(...))`
as in `examples/catalog.py`.
