# Pattern

`PatternValidator` matches with `re.findall` (findall substring), not
`fullmatch`. Empty-match patterns (`a*`, `?`) still count as a match —
that is the findall engine, not a fullmatch. `EmailValidator` keeps that
engine for its `pattern=` path and then requires the whole string to be
an addr-spec: `"prefix user@example.com suffix"` is rejected. Pattern
`&` / `|` is fail-closed on a missing fragment or mixed `str`/`bytes`;
same-kind bytes fragments concatenate as bytes. `count_min > count_max`
is constructor `ValueError`. A bytes pattern matches bytes (it is not
`str()`-coerced).

Pattern lives in the `ux_valio.pattern` package. The taught import is
still the package root (`from ux_valio import Pattern, Digit, StartsWith, SetOf`).

```python
from ux_valio import Digit, Pattern, PatternValidator, SetOf, StartsWith
```

`from ux_valio.pattern import Pattern` is the same objects — a package
re-home, not a second API. `WordBoundary` stays an atom `\b`.

Thin PatternTypes evidenced in valio@3415c03 `valio/regexer/regexps.py`.
Those names are the taught PatternType atoms (KEEP; not `DigitAtom` /
`CharacterClass` / `Lookbehind`):

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
