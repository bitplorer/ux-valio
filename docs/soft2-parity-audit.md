# Soft 2 parity audit — Door A vs valio@3415c03

Frozen reference: [`bitplorer/valio@3415c03`](https://github.com/bitplorer/valio/commit/3415c03e37085adda4040671a91eb19aa4fe4ac4).
Soft 1 tip: `ee7a725` (Door A bones). Soft-patch valio is **untouched**.

Public door stays `field: T = SomeValidator(...)`. No Field / Schema / Cap / Result
invented here.

## Intent (descriptor assignment)

`__set_name__` is the assignment seam. Soft #2 (falsy defaults) is adjacent KEEP.
Annotation bind is fail-closed: quiet overwrite is a lie.

## Exact raise (Soft 2) + valio cite

**ux-valio Soft 2** (`ux_valio/descriptor.py` `__set_name__` / `_bind_owner_annotation`):

- If `validator.annotation is None` and the owner class has an annotation → **owner wins** (copy onto the validator).
- If the owner has **no** annotation → **keep** the validator annotation.
- If **both** are set and they **disagree** (stdlib union identity, not `is`) → **`TypeError`**, append to `errors`, **always re-raise**. Not debug-swallow.
- If both are set and they **agree** → keep the validator annotation (no quiet overwrite).
- Reused descriptor, name already set, new name differs, annotations agree → **`AttributeError`** (`{old} != {new}, attribute names did not match`).

**valio@3415c03** `valio/descriptor/descriptors.py`:

```134:155:valio/descriptor/descriptors.py
    def _set_name(self, owner, name, logger):
        ...
            elif name != self.name and self.annotation == owner.__annotations__.get(name, None):
                raise AttributeError(
                    f"{self.name} != {name}, attribute names did not match"
                )
```

```157:202:valio/descriptor/descriptors.py
    def _may_set_or_ensure_annotation_match(self, owner, name, logger):
        ...
            if name in owner.__annotations__:
                if self.annotation is None:
                    self.annotation = owner.__annotations__[name]
                else:
                    ...
                    if not issubclassx(owner_annotation, self_annotation):
                        raise TypeError(
                            f"{owner.__name__}.{self.name}: {owner_annotation_name}"
                            f" annotation did not match {type(self).__qualname__}: "
                            f"{self_annotation_name}"
                        )
                    if owner_annotation != self.annotation:
                        self.annotation = owner_annotation
            else:
                if self.annotation:
                    owner.__annotations__[name] = self.annotation
        ...
            self.errors.append(annotation_err)
            raise annotation_err
```

Called from `__set_name__` at **L232**. typingx `issubclassx` is **HOLD** (dual-schema
`INT = Union[int, Validator, None]` is why valio needed it). Soft 1 already stores
plain `int` / `str` / `bool` on the typed facades. Soft 2 compares with stdlib
`typing.get_origin` / `get_args` so `Union[X, Y]` and `X | Y` agree. No
`typing_extensions` / `typingx` dependency.

Soft 2 does **not** write back onto `owner.__annotations__` and does **not** mutate
`owner.__doc__` (valio `_set_docs`). Those are not Door A caller surface.

## KEEP (already Soft 1)

| Surface | Lock |
| --- | --- |
| Door A `field: T = SomeValidator(...)` | README + `tests/test_door_a_readme.py` |
| Exported validators as field defaults | `Validator`, `StringValidator`, `IntegerValidator`, `BooleanValidator`, `TypeValidator`, `RequiredValidator`, `PatternValidator`, `LengthValidator`, `ValueValidator`, `MultipleValidator`, `ChoiceValidator`, `ReassignValidator` |
| Descriptor lifecycle | `__set_name__` / `__set__` / `__get__` / `__delete__`; class `__get__` returns `None`; only `pre_set` return stored; get/delete hooks see `self.name` |
| Soft #2 falsy defaults | `0` / `False` / `""` kept; `None` takes `default` |
| Soft #7 path fail-closed | unique units; aggregate owns leaves; second `validate()` is a new pass |
| Soft #8 bound honesty | `None` ≠ `0`; `min`/`max` inclusive; `gt`/`lt` exclusive; `multiple_of` remainder; `multiple_of=0` accepts only `0` |
| Soft #9 compose-not-inherit | facades compose concern leaves; no MI diamond |
| Soft #10 processors then tasks once | no `asyncio.run` in `__set__` |
| Pattern `findall` | substring, not `fullmatch` |
| debug-swallow | falsy `debug` swallows set/get/delete; `debug=True` re-raises. **Not flipped.** |
| Logger default OFF | `logger is False`; valio `logger=None` file logging retired |
| stdlib typing for isinstance | `check_type` uses `get_origin` / `get_args` (Union / `X \| Y` / `Optional`). Parametrized generics that are not `isinstance`-safe stay permissive (`TypeError` → accept). That is Soft 1, not typingx `isinstancex`. |
| Explicit `__all__` | no Field / Schema / Cap on the package |

## SOFT 2 DO (this PR)

- Fail-closed annotation conflict at `__set_name__` (cite above).
- Owner wins **only** when validator annotation was `None`; keep validator annotation when owner has none.
- Reused-validator name collision when annotations agree (valio `_set_name`).
- Stdlib union identity (`Optional[int]` ≡ `int \| None`, `Union[int, str]` ≡ `int \| str`) without typing_extensions.
- Behavior tests: `tests/test_annotation_conflict.py`.
- This audit doc.

## DEFER (named leaves / other doors — do not invent)

- Soft #3 `PaymentCard`
- Soft #4 named-once (`named_validate_once`)
- Soft #6 `Expiry`
- `Schema` twin, `Field` twin / Door B, `Cap` Host, `mount_channel`, `Result` type
- Dual-schema `Union[T, Validator]` annotations + typingx `isinstancex` / `issubclassx`
- pyparsing, phonenumbers, `rule/`
- compose #30 park
- valio write-back to `owner.__annotations__` and `_set_docs` class-doc mutation
- PEP 563 postponed annotations on **caller** modules (valio: do not `from __future__ import annotations` in validators; Soft 2 still reads raw `__annotations__`)

## RETIRE

- Star-import barrel (306 names)
- Multiple inheritance of concern leaves
- RGB / HSL crash leaves
- Door B `*Field` factory then `.validator`
- `asyncio.run` inside `__set__`
- Logger-on-by-`None` file logging
- typingx / typing_extensions as a runtime dep (not required by any Soft 1/2 LOCK; valio used typingx for dual-schema)

## typing_extensions residual

**None.** `pyproject.toml` has no typing extra. Soft 1 type checks and Soft 2
annotation identity use stdlib `typing` + `types.UnionType` (Python 3.10+ / forward to 3.14).
