# ux-valio handbook

The validator **is** the dataclass field default:

```python
name: str = StringValidator(max_length=50)
```

There is no Field twin and no Schema twin. Do not use bare `Property` as
the field default — it is the descriptor base, not a product facade.

This handbook follows [Diátaxis](https://diataxis.fr/): learn, solve,
look up, understand. Docstrings on the classes (`help(GSTINValidator)`)
are the per-name contract. Source layout matches
[`AGENTS.md`](../AGENTS.md).

**Read this if you are new.** The library is a descriptor you put on the
right-hand side of a dataclass field. It type-checks, bounds-checks,
runs your hangs, and stores on `instance.__dict__`. It is not a
BaseModel, not Pydantic, not valio with a new name. Valio itself is
not edited (frozen at `3415c03`). Python ≥ 3.14.

| If you want to… | Go here |
|---|---|
| Write the first field in five minutes | [Tutorial](tutorial.md) |
| Transform, uniqueness, persist, background | [Hang hooks](how-to/hang.md) |
| Combine length + required + pattern | [Compose](how-to/compose.md) |
| Schema without BaseModel | [TypedDict schema](how-to/typed-dict.md) |
| Copy a production workflow | [Workflows](how-to/workflows.md) |
| Keep mypy/Pylance quiet | [Typing](how-to/typing.md) |
| Know every kwarg / leaf | [Validator](reference/validator.md) |
| `int` / `str` / `date` / `UUID` / … | [Typed facades](reference/typed.md) |
| GSTIN, IBAN, ZIP, cards, … | [Named identities](reference/named.md) |
| `Digit` / `StartsWith` / `SetOf` | [Pattern](reference/pattern.md) |
| Package `__all__` | [Public API](reference/api.md) |
| Why these defaults exist | [Choices](explanation/choices.md) |
| debug, logger, slots, falsy `0` | [Honesty](explanation/honesty.md) |
| Import graph | [Layering](explanation/layering.md) |
| What is fast / what is not | [Performance](explanation/performance.md) |
| Future native apply | [Host / peer](explanation/host-peer-plan.md) |

Install: `pip install -e .`  
Phone extra: `pip install ux-valio[phonenumbers]`  
Runnable skeletons: [`examples/`](../examples/).
`python examples/signup.py` is a live check (happy path + failures).
