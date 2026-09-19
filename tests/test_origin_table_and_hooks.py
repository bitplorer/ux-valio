# SPDX-License-Identifier: MIT
"""Locks for origin table, hook adder table, and Pattern compile-at-bind."""

from dataclasses import dataclass
from pathlib import Path

from ux_valio import Validator
from ux_valio.validators.hooks import HookHost
from ux_valio.validators.leaves import (
    PatternValidator,
    TypeValidator,
    _ORIGIN_CHECKERS,
    _ORIGIN_GROUPS,
    is_instance_of,
)

ROOT = Path(__file__).resolve().parents[1]


def test_origin_table_owns_stdlib_generics():
    assert is_instance_of([1, 2], list[int]) is True
    assert is_instance_of([1, "a"], list[int]) is False
    assert is_instance_of({"a": 1}, dict[str, int]) is True
    assert is_instance_of((1, 2), tuple[int, ...]) is True
    assert list in _ORIGIN_CHECKERS
    assert dict in _ORIGIN_CHECKERS
    assert _ORIGIN_GROUPS


def test_add_hooks_are_declared_on_the_class():
    """Public process_*/task_* are real methods, not setattr from a table. No process_pre_set."""
    import inspect

    src = inspect.getsource(HookHost.process_pre_validate)
    assert "def process_pre_validate" in src
    assert "pre_validate" in src
    assert hasattr(HookHost, "process_pre_validate")
    assert hasattr(HookHost, "task_pre_validate")
    assert hasattr(HookHost, "process_post_set")
    assert hasattr(HookHost, "task_post_set")
    assert hasattr(HookHost, "add_validator")
    assert hasattr(HookHost, "wait_tasks")
    assert hasattr(HookHost, "_register")
    assert hasattr(HookHost, "_pre_validate")
    assert hasattr(HookHost, "_has_hooks")
    assert not hasattr(HookHost, "has_hooks")
    assert not hasattr(HookHost, "pre_validation_processing")
    assert not hasattr(HookHost, "post_set_processing")
    assert not hasattr(HookHost, "notify_pre_set")
    assert not hasattr(HookHost, "add_pre_validate_process")
    assert not hasattr(HookHost, "on_pre_set")
    assert not hasattr(HookHost, "on_pre_validate")
    assert not hasattr(HookHost, "add_pre_validator")
    assert not hasattr(HookHost, "add_pre_validator_task")
    assert not hasattr(HookHost, "add_post_set")
    assert not hasattr(HookHost, "add_post_set_task")
    assert not hasattr(HookHost, "_add")
    assert not hasattr(HookHost, "_init_hooks")
    assert not hasattr(HookHost, "add_pre_set")
    assert not hasattr(HookHost, "add_process_pre_validate")
    assert not hasattr(HookHost, "add_task_post_set")
    assert not hasattr(HookHost, "process_pre_set")
    assert not hasattr(HookHost, "task_pre_set")
    assert not hasattr(HookHost, "_HOOK_ADDERS")
    assert not hasattr(HookHost, "_PROCESSOR_PHASES")
    assert not hasattr(HookHost, "_install_adders")
    assert not hasattr(HookHost, "_hook_adder")


def test_hook_tables_on_host_origin_tables_beside_is_instance_of():
    """Hook adders stay on HookHost. Origin tables sit next to is_instance_of."""
    import ux_valio.validators.hooks as hooks_mod
    import ux_valio.validators.leaves as leaves_mod
    import ux_valio.validators.length as length_mod
    from ux_valio.validators.base import AllOf, _Of
    from ux_valio.validators.length import LengthValidator

    assert not hasattr(hooks_mod, "_HOOK_ADDERS")
    assert not hasattr(hooks_mod, "_PROCESSOR_PHASES")
    assert not hasattr(HookHost, "_HOOK_ADDERS")
    assert not hasattr(HookHost, "_PROCESSOR_PHASES")
    assert list in leaves_mod._ORIGIN_CHECKERS
    assert leaves_mod._ORIGIN_GROUPS
    assert not hasattr(TypeValidator, "_ORIGIN_CHECKERS")
    assert not hasattr(TypeValidator, "_ORIGIN_GROUPS")
    assert not hasattr(AllOf, "_bind_compose_kwargs")
    assert not hasattr(_Of, "_bind_kwargs")
    assert not hasattr(_Of, "_merged_attr")
    assert hasattr(_Of, "_flatten")
    assert hasattr(_Of, "_merged_annotation")
    assert not (ROOT / "ux_valio" / "validators" / "compose.py").exists()
    assert hasattr(LengthValidator, "_len_or_reject")
    assert not hasattr(length_mod, "_len_or_reject")
    assert hasattr(HookHost, "_collect_owner_keys")
    assert hasattr(HookHost, "_owner_key")
    assert not hasattr(HookHost, "_iter_owner_keys")
    assert not hasattr(HookHost, "_hook_schema")
    assert not hasattr(leaves_mod, "_apply_typed_dict_extras")
    assert hasattr(HookHost, "_resolve_owner_key")
    assert hasattr(HookHost, "_has_hooks")
    assert not hasattr(HookHost, "_bag_key")
    assert not hasattr(HookHost, "bags_used")
    from ux_valio.descriptor import Property
    from ux_valio.validators import bounds as bounds_mod
    from ux_valio.validators import facade as facade_mod

    assert hasattr(Property, "_emit_log")
    assert not hasattr(Property, "_log")
    assert hasattr(facade_mod, "ValidateStep")
    assert not hasattr(facade_mod, "Lookup")
    assert hasattr(bounds_mod, "read_bound")
    assert not hasattr(bounds_mod, "bound_value")
    assert not (ROOT / "tests" / "test_door_a_readme.py").exists()
    assert (ROOT / "tests" / "test_readme_shape.py").is_file()
    assert not hasattr(hooks_mod, "_collect_owner_keys")
    assert not hasattr(hooks_mod, "_owner_key")
    assert not hasattr(hooks_mod, "_resolve_owner_key")
    assert not hasattr(hooks_mod, "_hook_adder")
    from ux_valio.facades.typed import DateValidator
    import ux_valio.facades.typed as typed_mod

    assert hasattr(DateValidator, "_parse_eu_ind_date")
    assert not hasattr(typed_mod, "_parse_eu_ind_date")
    from ux_valio import (
        AadhaarCardValidator,
        ExpiryValidator,
        GSTINValidator,
        IBANValidator,
        IFSCValidator,
        IMEIValidator,
        PANCardValidator,
        PaymentCardValidator,
        PhoneNumberValidator,
        PinCodeValidator,
        Property,
        UPIIdValidator,
    )
    import ux_valio.facades.named.aadhaar as aadhaar_mod
    import ux_valio.facades.named.expiry as expiry_mod
    import ux_valio.facades.named.gstin as gstin_mod
    import ux_valio.facades.named.iban as iban_mod
    import ux_valio.facades.named.ifsc as ifsc_mod
    import ux_valio.facades.named.imei as imei_mod
    import ux_valio.facades.named.pan as pan_mod
    import ux_valio.facades.named.payment as payment_mod
    import ux_valio.facades.named.phone as phone_mod
    import ux_valio.facades.named.pincode as pincode_mod
    import ux_valio.facades.named.upi as upi_mod
    import ux_valio.descriptor as descriptor_mod

    assert hasattr(AadhaarCardValidator, "_is_valid_aadhaar")
    assert not hasattr(aadhaar_mod, "_is_valid_aadhaar")
    assert hasattr(PaymentCardValidator, "_is_valid_payment_card")
    assert not hasattr(payment_mod, "_is_valid_payment_card")
    assert hasattr(PANCardValidator, "_is_valid_pan")
    assert not hasattr(pan_mod, "_is_valid_pan")
    assert hasattr(GSTINValidator, "_is_valid_gstin")
    assert not hasattr(gstin_mod, "_is_valid_gstin")
    assert hasattr(IFSCValidator, "_is_valid_ifsc")
    assert not hasattr(ifsc_mod, "_is_valid_ifsc")
    assert hasattr(IBANValidator, "_is_valid_iban")
    assert not hasattr(iban_mod, "_is_valid_iban")
    assert hasattr(IMEIValidator, "_is_valid_imei")
    assert not hasattr(imei_mod, "_is_valid_imei")
    assert hasattr(PinCodeValidator, "_is_valid_pincode")
    assert not hasattr(pincode_mod, "_is_valid_pincode")
    assert hasattr(UPIIdValidator, "_is_valid_upi_id")
    assert not hasattr(upi_mod, "_is_valid_upi_id")
    assert hasattr(ExpiryValidator, "_parse_expiry_datetime")
    assert not hasattr(expiry_mod, "_parse_expiry_datetime")
    assert hasattr(PhoneNumberValidator, "_require_phonenumbers")
    assert not hasattr(phone_mod, "_require_phonenumbers")
    assert hasattr(Property, "_slot_names")
    assert not hasattr(descriptor_mod, "_slot_names")
    assert not hasattr(hooks_mod, "_namespace")
    assert not hasattr(hooks_mod, "hook_bags_used")


def test_pattern_compile_is_cached_on_owner():
    field = PatternValidator(pattern=r"ab+", name="code")
    field._validate_pattern(None, "abb")
    first = field._compiled
    field._validate_pattern(None, "abbb")
    assert field._compiled is first


def test_email_identity_reuses_compiled_finder():
    from ux_valio import EmailValidator

    field = EmailValidator(debug=True, name="email")
    field.validate(None, "user@example.com")
    first = field._compiled
    assert first is not None
    field.validate(None, "other@example.com")
    assert field._compiled is first
    assert first.fullmatch("user@example.com") is not None


def test_facade_pattern_path_uses_owner_cache():
    @dataclass
    class Row:
        sku: str = Validator(pattern=r"[A-Z]{3}", debug=True)

    Row(sku="ABC")
    desc = Row.__dict__["sku"]
    assert desc._compiled is not None
    compiled = desc._compiled
    Row(sku="XYZ")
    assert desc._compiled is compiled
