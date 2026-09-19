# Layering

Layout is an **import graph** plus **sibling packages**. Lower layers
never import higher. Parallel products sit in a parallel folder, not
inside the layer they depend on.

```text
errors.py          layer 0 — ValidationErrors
descriptor.py      Property (store); never imports validators or facades
pattern/           sibling of the store
validators/        validate door (ValidateProperty : Property)
  base.py          ValidateProperty, AllOf, AnyOf
  hooks.py         HookHost (inherited)
  leaves/length/value   concern leaves (compose with & / |, no leaf MI)
  facade.py        Validator, ValidationPath
facades/           field-default products
  typed.py         IntegerValidator, StringValidator, …
  named/           identity products, sibling domains
```

`named` does not import sibling named modules. `typed` does not import
`named`. Construction is `Any` to type checkers so any store type works —
no `AsStr` / `AsUser` mixin.

Public names re-export from `ux_valio`. Domain imports are navigation:

```python
from ux_valio.facades.named.india.gst import GSTINValidator
```

The taught import is still `from ux_valio import GSTINValidator`.
