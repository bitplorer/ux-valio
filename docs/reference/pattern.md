# Pattern

Use Pattern when the **shape of the string** is the identity: a SKU
`INV-0042Z`, a hex tint `aF`, a mass `12kg`. You do not use it for
“must contain a digit somewhere **and** a letter somewhere” — that is
`AllOf` of two `StringValidator(pattern=…)` ([compose](../how-to/compose.md)).

`PatternValidator` matches with `re.findall` (findall substring), not
`fullmatch`. Empty-match patterns (`a*`, `?`) still count as a match —
that is the findall engine, not a fullmatch. So `Digit(count_min=1)`
succeeds on `"abc1def"` because a digit appears. To require the **whole**
string, wrap with `StartsWith` / `EndsWith` (anchors) or use a named
facade that fullmatches (email, GSTIN).

`EmailValidator` keeps that engine for its `pattern=` path and then
requires the whole string to be an addr-spec:
`"prefix user@example.com suffix"` is rejected.

Pattern `&` / `|` is fail-closed on a missing fragment or mixed
`str`/`bytes`; same-kind bytes fragments concatenate as bytes.
`count_min > count_max` is constructor `ValueError`. A bytes pattern
matches bytes (it is not `str()`-coerced).

Pattern lives in the `ux_valio.pattern` package. The taught import is
still the package root (`from ux_valio import Pattern, Digit, StartsWith, SetOf`).

```python
from ux_valio import Digit, Pattern, PatternValidator, SetOf, StartsWith
```

`from ux_valio.pattern import Pattern` is the same objects — a package
re-home, not a second API. `WordBoundary` stays an atom `\b`.

## Atoms you actually write

Thin PatternTypes evidenced in valio@3415c03 `valio/regexer/regexps.py`.
Those names are the taught PatternType atoms (KEEP; not `DigitAtom` /
`CharacterClass` / `Lookbehind`):

| atom | what it matches | typical field |
|---|---|---|
| `Digit(count=4)` | four digits | OTP fragment, SKU run |
| `Word(count_min=3)` | `[A-Za-z0-9_]` run | slug fragment |
| `NonWhiteSpace(count_min=4)` | a token with no space | lot code |
| `StartsWith(Pattern(r"INV-"))` | prefix | SKU, invoice |
| `EndsWith(Pattern(r"Z"))` | suffix | SKU check letter |
| `SetOf(Pattern(r"0-9a-f"), count=2)` | character-class `[raw]` | hex pair |
| `~SetOf(...)` | `[^raw]` | negated class |
| `IfFollowedBy(Pattern(r"kg"))` | lookahead | `12kg` not `12lb` |
| `IfPrecededBy(Pattern(r"USD"))` | lookbehind | `USD40` |

- `StartsWith` / `EndsWith` (`^` / `$`)
- lookarounds `IfPrecededBy` / `IfNotPrecededBy` / `IfFollowedBy` /
  `IfNotFollowedBy`
- `SetOf` character-class `[raw]` / `[^raw]` (`~SetOf(...)` negates)

`Contained` / `IfContained` are KEEP-absent: they do not exist in
valio@3415c03. Capturing groups, `WordGroups`, `scanString`, pyparsing,
and a second `regexer` package are not ported.

```python
from dataclasses import dataclass
from ux_valio import Digit, Pattern, PatternValidator, SetOf, StartsWith

sku = StartsWith(Pattern(r"INV-")) & Digit(count=4)
hex_pair = SetOf(Pattern(r"0-9a-f"), count=2)

@dataclass
class Part:
    sku: str = PatternValidator(pattern=sku)
    tint: str = PatternValidator(pattern=hex_pair)
```

`Part(sku="INV-0042", tint="aF")` succeeds. `Part(sku="xINV-0042")`
fails `StartsWith`. A warehouse line that also checks stock is
`examples/catalog.py`.
