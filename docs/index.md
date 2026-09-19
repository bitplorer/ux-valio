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

| Start here | |
|---|---|
| [Tutorial](tutorial.md) | five-minute field default |
| [Hang hooks](how-to/hang.md) | `pre_validate` / `validator` / `task_*` |
| [Compose](how-to/compose.md) | `&` / `\|` / `AllOf` / `AnyOf` |
| [TypedDict schema](how-to/typed-dict.md) | stdlib schema, no BaseModel |
| [Validator](reference/validator.md) | kwargs, leaves, specified path |
| [Typed facades](reference/typed.md) | `int` / `str` / `date` / `UUID` / … |
| [Named identities](reference/named.md) | GSTIN, IBAN, ZIP, cards, … |
| [Pattern](reference/pattern.md) | `Digit` / `StartsWith` / `SetOf` |
| [Public API](reference/api.md) | `__all__` |
| [Honesty](explanation/honesty.md) | debug, logger, slots, falsy `0` |
| [Layering](explanation/layering.md) | import graph |
| [Host / peer](explanation/host-peer-plan.md) | future native apply; not implemented |

Python ≥ 3.14. Install: `pip install -e .`  
Phone extra: `pip install ux-valio[phonenumbers]`  
Runnable skeletons: [`examples/`](../examples/).
