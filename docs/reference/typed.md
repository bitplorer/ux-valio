# Typed facades

Primitives and stdlib store types. Construction is `Any` to type
checkers, so `name: str = StringValidator()` assigns. `help(IntegerValidator)`
is the Usage contract.

| facade | stores | notes |
|---|---|---|
| `IntegerValidator` | `int` | |
| `StringValidator` | `str` | |
| `BooleanValidator` | `bool` | |
| `FloatValidator` | `float` | |
| `DecimalValidator` | `decimal.Decimal` | coerces Decimal strings; rejects float |
| `BytesValidator` | `bytes` | |
| `DateValidator` | `datetime.date` | EU `YYYY-MM-DD` / IND `DD-MM-YYYY` (`-` `/` `:`); `datetime.datetime` rejected; owner may be `date`, `str`, or `T \| str` |
| `DateTimeValidator` | `datetime.datetime` | ISO via `fromisoformat`; plain `date` rejected; owner may be `datetime`, `str`, or the union |
| `UUIDValidator` | `uuid.UUID` | coerces UUID strings; owner may be `uuid.UUID`, `str`, or `uuid.UUID \| str` |
| `PathValidator` | `pathlib.Path` | coerces `str`; owner may be `Path`, `str`, or the union; `path_exists=True` requires the path to exist |
| `IPv4Validator` | given string | stdlib `ipaddress` |
| `IPv6Validator` | given string | |
| `IPAddressValidator` | given string | v4 or v6 |
| `EnumValidator` | `enum.Enum` | |
| `IntegerEnumValidator` | `enum.IntEnum` | |
| `StringEnumValidator` | str Enum member | |

`DateValidator` stores `datetime.date`. Numeric EU (`YYYY-MM-DD`, also
`/` and `:`) and IND (`DD-MM-YYYY`, also `/` and `:`) strings parse on
assignment; the same delimiter must appear on both sides. `02/01/2020`
is 2 January 2020 (IND), not 1 February (US). Month names, ordinals,
dots, and pyparsing `scanString` from valio `relib/dates.py` are not
ported.

`UUIDValidator` (coerces UUID strings; stores `uuid.UUID`; owner
annotation may be `uuid.UUID`, `str`, or `uuid.UUID | str`).

RGB/HSL color validators are retired. `HexColorValidator` is not a
public facade.
