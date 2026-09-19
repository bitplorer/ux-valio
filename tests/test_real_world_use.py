# SPDX-License-Identifier: MIT
"""Real-environment field-default paths: dataclass, pickle, inherit, KYC, checkout.

No ``from __future__ import annotations`` — unresolved string annotations
TypeError at bind (KEEP).
"""

import copy
import pickle
import threading
import uuid
from dataclasses import asdict, dataclass, replace
from decimal import Decimal
from pathlib import Path

import pytest

from ux_valio import (
    AadhaarCardValidator,
    DecimalValidator,
    EmailValidator,
    IntegerValidator,
    PANCardValidator,
    PathValidator,
    PaymentCardValidator,
    StringValidator,
    UUIDValidator,
    ValidationErrors,
    Validator,
)

VALID_AADHAAR = "234567890124"
VALID_PAN = "AAAPA1111F"


@dataclass
class Account:
    name: str = StringValidator(debug=True, min_length=1, max_length=50, required=True)
    email: str = EmailValidator(debug=True, required=True)
    age: int = IntegerValidator(min_value=0, max_value=120, debug=True)


def test_account_asdict_replace_eq_pickle_copy():
    user = Account(name="Ada", email="ada@example.com", age=36)
    assert asdict(user) == {"name": "Ada", "email": "ada@example.com", "age": 36}
    assert replace(user, age=37).age == 37
    assert user == Account(name="Ada", email="ada@example.com", age=36)
    assert "Ada" in repr(user)
    loaded = pickle.loads(pickle.dumps(user))
    assert loaded == user
    assert copy.deepcopy(user) == user


def test_child_dataclass_inherits_parent_fields():
    @dataclass
    class Person:
        age: int = IntegerValidator(min_value=0, debug=True)

    @dataclass
    class Employee(Person):
        name: str = StringValidator(debug=True, required=True)

    row = Employee(age=30, name="Ada")
    assert row.age == 30 and row.name == "Ada"


def test_kyc_print_forms_store_canonical_identity():
    @dataclass
    class Kyc:
        aadhaar: str = AadhaarCardValidator(debug=True, required=True)
        pan: str = PANCardValidator(debug=True, required=True)

    row = Kyc(aadhaar="2345 6789 0124", pan="aaapa1111f")
    assert row.aadhaar == VALID_AADHAAR
    assert row.pan == VALID_PAN
    with pytest.raises(ValueError):
        Kyc(aadhaar="2345 6789 0125", pan=VALID_PAN)


def test_checkout_printed_card_and_decimal_money():
    @dataclass
    class Order:
        card: str = PaymentCardValidator(debug=True, required=True)
        total: Decimal = DecimalValidator(debug=True, min_value=Decimal("0.01"))
        sku: str = StringValidator(debug=True, min_length=3, required=True)

    order = Order(card="4111 1111 1111 1111", total="19.99", sku="SKU-1")
    assert order.card == "4111111111111111"
    assert order.total == Decimal("19.99")
    payload = asdict(order)
    payload["total"] = str(payload["total"])
    assert payload["card"] == "4111111111111111"


def test_uuid_path_roundtrip_is_json_ready():
    @dataclass
    class Asset:
        id: uuid.UUID = UUIDValidator(debug=True)
        home: Path = PathValidator(debug=True)

    row = Asset(id="12345678-1234-5678-1234-567812345678", home="/tmp")
    assert row.id == uuid.UUID("12345678-1234-5678-1234-567812345678")
    assert isinstance(row.home, Path)
    assert str(row.id)
    assert str(row.home)


def test_list_int_box_and_collect_all():
    @dataclass
    class Box:
        items: list[int] = Validator[list[int]](debug=True, min_length=1, collect_all=True)

    assert Box(items=[1, 2]).items == [1, 2]
    with pytest.raises((TypeError, ValidationErrors)):
        Box(items=["a"])
    with pytest.raises((ValueError, ValidationErrors)):
        Box(items=[])


def test_threaded_assigns_do_not_raise():
    @dataclass
    class Gauge:
        n: int = IntegerValidator(min_value=0, debug=True)

    g = Gauge(n=0)
    errors: list[BaseException] = []

    def bump(i: int) -> None:
        try:
            g.n = i
        except Exception as err:
            errors.append(err)

    threads = [threading.Thread(target=bump, args=(i,)) for i in range(16)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert errors == []
    assert isinstance(g.n, int)


def test_default_factory_list_is_per_instance():
    @dataclass
    class Tags:
        labels: list[str] = Validator(debug=True, default_factory=list)

    left, right = Tags(), Tags()
    left.labels.append("x")
    assert right.labels == []
