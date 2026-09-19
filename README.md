# ux-valio

The validator **is** the dataclass field default:

```python
name: str = StringValidator(max_length=50)
```

Greenfield reimplementation of
[`bitplorer/valio`](https://github.com/bitplorer/valio) frozen at
[`3415c03`](https://github.com/bitplorer/valio/commit/3415c03e37085adda4040671a91eb19aa4fe4ac4).
There is no Field twin and no Schema twin. Valio itself is not edited.
Do not use bare `Property` as the field default — it is the descriptor
base, not a product facade.

## Install

Python ≥ 3.14 (same floor as `ux-compose`).

```console
pip install -e .
pip install ux-valio[phonenumbers]   # PhoneNumberValidator
```

## Usage

```python
from dataclasses import dataclass
from ux_valio import IntegerValidator, StringValidator, Validator

@dataclass
class User:
    name: str = StringValidator(max_length=50, required=True)
    rank: str = Validator(in_choice=["Male", "Female", "Trans"], default="Female")
    n: int = IntegerValidator(min_value=0, max_value=10, multiple_of=2)
```

Hang `@username.pre_validate` / `@name.validator` on the field name.
Full hang table, TypedDict schema, named identities

(GSTIN, IBAN, ZIP, UnionPay, …), Pattern, KEEP honesty, and the
**why** of every default live in the handbook.

## Handbook

Markdown on GitHub; optional Material site (`pip install ux-valio[docs]`
then `mkdocs serve`).

| | |
|---|---|
| [docs/index.md](docs/index.md) | map |
| [Tutorial](docs/tutorial.md) | first field, hang, compose |
| [Hang API](docs/how-to/hang.md) | `pre_validate` / `task_*` / `wait_tasks` |
| [Field logging](docs/how-to/logging.md) | `logger=True` → `module.qualname.field` |
| [Workflows](docs/how-to/workflows.md) | one file per real-world case |
| [Typing](docs/how-to/typing.md) | `Validator[T]`, mypy plugin |
| [Validator kwargs](docs/reference/validator.md) | `doc`, `default`, `default_factory`, `reassign`, … |

| [Named identities](docs/reference/named.md) | compact identity catalog |
| [Choices](docs/explanation/choices.md) | why these defaults, how they affect usage |
| [Honesty](docs/explanation/honesty.md) | debug, logger `module.qualname.field`, slots |
| [Performance](docs/explanation/performance.md) | specified path, what is hot |
| [examples/](examples/) | production skeletons |

Runnable production skeletons live under `examples/`
(`python examples/<file>.py`). Each file is a service that injects
Protocol ports in the constructor. See [`examples/README.md`](examples/README.md).

## Public surface

`Validator`, typed facades, concern leaves, `AllOf` / `AnyOf`,
`ValidationErrors`, and `Pattern` / `PatternType`
combinators (`&` / `|`) plus stdlib atoms `Digit` / `Word` / `NonDigit` /
`NonWord` / `WhiteSpace` / `NonWhiteSpace` / `WordBoundary`, anchors
`StartsWith` / `EndsWith`, lookarounds `IfPrecededBy` / `IfFollowedBy` (and
the `IfNot*` pair), and `SetOf` character classes. The taught field default
is a facade or `Validator`, not bare `Property`. Hang hooks on the field
default (`ValidateProperty`). No Cap Host, no `rule/`. Import Pattern names
from `ux_valio`. There is no `ux_valio.regexer`.

A later optional native peer (host decides, peer applies) is mapped in
[`docs/explanation/host-peer-plan.md`](docs/explanation/host-peer-plan.md)
— not implemented.
