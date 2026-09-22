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
  _native.py       bind door: load, _select_*, bind_native_plan
  _native_closed.py  closed Plan detectors (_closed_*)
  _native_apply.py   apply helpers, FailKind map, extract bridges
facades/           field-default products
  typed.py         IntegerValidator, StringValidator, …
  named/           identity products, sibling domains
native/            optional ux-valio[native] wheel (PyO3; sibling crate)
```

`named` does not import sibling named modules. `typed` does not import
`named`. Construction is `Any` to type checkers so any store type works —
no `AsStr` / `AsUser` mixin.

Public names re-export from `ux_valio`. Domain imports are navigation:

```python
from ux_valio.facades.named.india.gst import GSTINValidator
```

The taught import is still `from ux_valio import GSTINValidator`.
