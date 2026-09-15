# SPDX-License-Identifier: MIT
"""Parametrized generic args are checked. isinstance TypeError is fail-closed.

The membership door is unexported ``is_instance_of``. No public
``check_instance``. Descriptor ``__set__`` and ``validate()`` share it.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Annotated, Any, Dict, List, Literal, NewType, Set, Tuple, TypeVar

import pytest

from ux_valio import Validator
from ux_valio.validators.leaves import is_instance_of

UserId = NewType("UserId", int)


def _bound(annotation):
    field = Validator(debug=True)
    field.annotation = annotation
    field.name = "x"
    return field


def test_list_int_rejects_wrong_element_on_set_and_validate():
    field = Validator(debug=True)

    @dataclass
    class Box:
        items: list[int] = field

    assert Box(items=[1, 2]).items == [1, 2]
    assert Box(items=[]).items == []
    with pytest.raises(TypeError):
        Box(items=["a"])

    field.validate(None, [1])
    with pytest.raises(TypeError):
        field.validate(None, ["a"])


def test_typing_list_matches_builtin_list_and_checks_elements():
    field = Validator(debug=True)
    field.annotation = List[int]

    @dataclass
    class Box:
        items: list[int] = field

    assert field.annotation is List[int]
    assert Box(items=[1]).items == [1]
    with pytest.raises(TypeError):
        Box(items=["a"])


def test_dict_str_int_rejects_wrong_key_or_value():
    field = Validator(debug=True)

    @dataclass
    class Map:
        m: dict[str, int] = field

    assert Map(m={"a": 1}).m == {"a": 1}
    assert Map(m={}).m == {}
    with pytest.raises(TypeError):
        Map(m={1: "a"})
    with pytest.raises(TypeError):
        field.validate(None, {1: 1})
    with pytest.raises(TypeError):
        field.validate(None, {"a": "a"})


def test_typing_dict_matches_builtin_dict():
    field = Validator(debug=True)
    field.annotation = Dict[str, int]

    @dataclass
    class Map:
        m: dict[str, int] = field

    assert Map(m={"a": 1}).m == {"a": 1}
    with pytest.raises(TypeError):
        Map(m={1: "a"})


def test_set_int_rejects_wrong_element():
    field = Validator(debug=True)

    @dataclass
    class Bag:
        items: set[int] = field

    assert Bag(items={1}).items == {1}
    assert Bag(items=set()).items == set()
    with pytest.raises(TypeError):
        Bag(items={"a"})
    with pytest.raises(TypeError):
        field.validate(None, {"a"})


def test_typing_set_matches_builtin_set():
    field = Validator(debug=True)
    field.annotation = Set[int]

    @dataclass
    class Bag:
        items: set[int] = field

    assert Bag(items={1}).items == {1}
    with pytest.raises(TypeError):
        Bag(items={"a"})


def test_nested_list_list_int_walks_inner_type():
    field = Validator(debug=True)

    @dataclass
    class Box:
        items: list[list[int]] = field

    assert Box(items=[[1]]).items == [[1]]
    with pytest.raises(TypeError):
        Box(items=[1])
    with pytest.raises(TypeError):
        Box(items=[[1, "a"]])
    with pytest.raises(TypeError):
        field.validate(None, [[1, "a"]])


def test_nested_dict_str_list_int():
    field = _bound(dict[str, list[int]])
    field.validate(None, {"a": [1, 2]})
    with pytest.raises(TypeError):
        field.validate(None, {"a": [1, "x"]})
    with pytest.raises(TypeError):
        field.validate(None, {1: [1]})


def test_tuple_hetero_checks_arity_and_positions():
    field = Validator(debug=True)

    @dataclass
    class Pair:
        item: tuple[int, str] = field

    assert Pair(item=(1, "a")).item == (1, "a")
    with pytest.raises(TypeError):
        Pair(item=(1,))
    with pytest.raises(TypeError):
        Pair(item=(1, 2, 3))
    with pytest.raises(TypeError):
        Pair(item=(1, 2))
    with pytest.raises(TypeError):
        Pair(item=[1, "a"])
    with pytest.raises(TypeError):
        field.validate(None, ("a", 1))


def test_tuple_homogeneous_rest_checks_every_element():
    field = Validator(debug=True)

    @dataclass
    class Ns:
        item: tuple[int, ...] = field

    assert Ns(item=(1, 2)).item == (1, 2)
    assert Ns(item=()).item == ()
    with pytest.raises(TypeError):
        Ns(item=("a",))
    with pytest.raises(TypeError):
        Ns(item=[1, 2])
    field.validate(None, (1, 2, 3))
    with pytest.raises(TypeError):
        field.validate(None, (1, "a"))


def test_typing_tuple_matches_builtin_tuple():
    field = Validator(debug=True)
    field.annotation = Tuple[int, str]

    @dataclass
    class Pair:
        item: tuple[int, str] = field

    assert Pair(item=(1, "a")).item == (1, "a")
    with pytest.raises(TypeError):
        Pair(item=(1,))


def test_literal_membership():
    field = Validator(debug=True)

    @dataclass
    class Flag:
        kind: Literal["a", "b"] = field

    assert Flag(kind="a").kind == "a"
    with pytest.raises(TypeError):
        Flag(kind="c")
    with pytest.raises(TypeError):
        Flag(kind=1)
    field.validate(None, "b")
    with pytest.raises(TypeError):
        field.validate(None, "c")


def test_annotated_strips_to_inner_type():
    field = _bound(Annotated[int, "meta"])
    field.validate(None, 1)
    with pytest.raises(TypeError):
        field.validate(None, "a")
    assert is_instance_of(1, Annotated[int, "meta"]) is True
    assert is_instance_of("a", Annotated[int, "meta"]) is False


def test_newtype_unwraps_to_supertype():
    field = _bound(UserId)
    field.validate(None, 1)
    with pytest.raises(TypeError):
        field.validate(None, "a")
    assert is_instance_of(1, UserId) is True
    assert is_instance_of("a", UserId) is False


def test_any_and_unset_annotation_accept():
    assert is_instance_of("x", Any) is True
    assert is_instance_of(1, Any) is True
    assert is_instance_of(None, None) is True
    field = Validator(debug=True)
    field.name = "x"
    field.validate(None, "anything")


def test_isinstance_typeerror_is_fail_closed_not_true():
    T = TypeVar("T")
    assert is_instance_of(1, T) is False
    assert is_instance_of(1, "list[int]") is False
    field = _bound("list[int]")
    with pytest.raises(TypeError):
        field.validate(None, 1)
    with pytest.raises(TypeError):
        field.validate(None, [1])


def test_typevar_bound_and_constraints():
    bound_t = TypeVar("bound_t", bound=int)
    constrained = TypeVar("constrained", int, str)
    assert is_instance_of(1, bound_t) is True
    assert is_instance_of("a", bound_t) is False
    assert is_instance_of("a", constrained) is True
    assert is_instance_of(1.5, constrained) is False


def test_list_int_or_none_rejects_wrong_elements():
    field = Validator(debug=True)

    @dataclass
    class Box:
        items: list[int] | None = field

    assert Box(items=[1]).items == [1]
    assert Box(items=None).items is None
    with pytest.raises(TypeError):
        Box(items=["a"])


def test_bool_as_int_still_accepted_inside_list():
    assert is_instance_of([True], list[int]) is True
    field = _bound(list[int])
    field.validate(None, [True, False])


def test_abc_sequence_and_mapping_walk_args():
    assert is_instance_of([1, 2], Sequence[int]) is True
    assert is_instance_of([1, "a"], Sequence[int]) is False
    assert is_instance_of({"a": 1}, Mapping[str, int]) is True
    assert is_instance_of({1: "a"}, Mapping[str, int]) is False


def test_callable_origin_is_checked_signature_is_not():
    from collections.abc import Callable

    assert is_instance_of(len, Callable[[int], str]) is True
    assert is_instance_of(1, Callable[[int], str]) is False


def test_generic_subclass_origin_does_not_inspect_instance_params():
    from typing import Generic

    T = TypeVar("T")

    class Box(Generic[T]):
        def __init__(self, item: T) -> None:
            self.item = item

    assert is_instance_of(Box("a"), Box[int]) is True
    assert is_instance_of("a", Box[int]) is False
    import ux_valio

    assert "is_instance_of" not in ux_valio.__all__
    assert "check_instance" not in ux_valio.__all__
    assert not hasattr(ux_valio, "check_instance")
    assert not hasattr(ux_valio, "is_instance_of")


def test_is_instance_of_docstring_does_not_teach_permissive_args():
    doc = is_instance_of.__doc__ or ""
    assert "permissive" not in doc.lower()
    assert "TypeError" not in doc or "False" in doc
