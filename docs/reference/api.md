# Public API

Taught import: `from ux_valio import …`. Path helpers and async-bridge
names other than `wait_tasks` are not in the package `__all__`. There is
no `ux_valio.regexer`. No star-import barrel, no Field, no Schema, no Cap.

## Descriptor / compose

`Property`, `ValidateProperty`, `Validator`, `AllOf`, `AnyOf`, `Chain`,
`ValidationErrors`, `wait_tasks`

## Concern leaves

`TypeValidator`, `RequiredValidator`, `LengthValidator`,
`MinLengthValidator`, `MaxLengthValidator`, `ValueValidator`,
`MinValueValidator`, `MaxValueValidator`, `ChoiceValidator`,
`PatternValidator`, `ReassignValidator`, `MultipleValidator`

## Typed facades

`IntegerValidator`, `StringValidator`, `BooleanValidator`,
`FloatValidator`, `DecimalValidator`, `BytesValidator`, `DateValidator`,
`DateTimeValidator`, `UUIDValidator`, `PathValidator`, `IPv4Validator`,
`IPv6Validator`, `IPAddressValidator`, `EnumValidator`,
`IntegerEnumValidator`, `StringEnumValidator`

## Named identities

See [named facades](named.md). Every identity name in `__all__` is listed
there (Aadhaar through VoterId, IBAN, PaymentCard, Locale, SemVer, …).

## Pattern

`Pattern`, `PatternType`, `Digit`, `NonDigit`, `Word`, `NonWord`,
`WhiteSpace`, `NonWhiteSpace`, `WordBoundary`, `StartsWith`, `EndsWith`,
`IfPrecededBy`, `IfNotPrecededBy`, `IfFollowedBy`, `IfNotFollowedBy`,
`SetOf`

`__version__` is exported. Hang methods live on the descriptor instance,
not as package names.
