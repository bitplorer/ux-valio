# Door A examples

Runnable dataclasses that use the taught door: `field: T = SomeValidator(...)`.
Import names from `ux_valio`. There is no Field twin, Schema twin, Cap Host,
or list/dict/set/tuple collection facade.

| File | What it shows |
| --- | --- |
| `user_account.py` | `StringValidator`, `IntegerValidator`, `EmailValidator`, `UUIDValidator`, choice |
| `registration.py` | `add_pre_validator` uniqueness check (return the value) |
| `checkout.py` | `PaymentCardValidator`, `ExpiryValidator`, `DecimalValidator` |
| `indian_kyc.py` | `AadhaarCardValidator`, `PANCardValidator`, `PhoneNumberValidator` |
| `dates_paths.py` | `DateValidator` EU/IND parse, `PathValidator`, IP |
| `sku_codes.py` | `Pattern`, `StartsWith`, `EndsWith`, `SetOf`, stdlib atoms |
| `lookaround_units.py` | `IfPrecededBy` / `IfFollowedBy` on Door A fields |
| `compose_hooks.py` | `&` / `|`, `AllOf` / `AnyOf`, compose-root `add_*` |
| `collect_all_form.py` | `collect_all=True` surfaces every concern |

Run one file:

```console
python examples/user_account.py
```
