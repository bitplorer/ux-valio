# SPDX-License-Identifier: MIT
"""Descriptor that validates in ``pre_set`` before store.

``ValidateProperty`` is the Door A unit. Concern leaves and facades subclass
it once — they do not multiple-inherit each other. Validator objects compose
with ``&`` / ``|`` (AllOf / AnyOf) or explicit ``AllOf`` / ``AnyOf`` / ``Chain``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

from ux_valio.descriptor import Property

if TYPE_CHECKING:
    from ux_valio.validators.compose import AllOf, AnyOf


class ValidateProperty(Property, ABC):
    """Descriptor that validates in ``pre_set`` before store."""

    def pre_set(self, obj: Any, value: Any) -> Any:
        self.notify_pre_set(obj)
        value = self.pre_validation_processing(obj, value)
        self.validate(instance=obj, value=value)
        return self.post_validation_processing(obj, value)

    def post_set(self, obj: Any, value: Any) -> Any:
        self.notify_post_set(obj)
        return self.post_set_processing(obj, value)

    def pre_get(self, obj: Any, value: Any) -> Any:
        return self.pre_get_processing(obj, value)

    def post_get(self, obj: Any, value: Any) -> Any:
        return self.post_get_processing(obj, value)

    def pre_delete(self, obj: Any, value: Any) -> Any:
        return self.pre_delete_processing(obj, value)

    def post_delete(self, obj: Any, value: Any) -> Any:
        return self.post_delete_processing(obj, value)

    def pre_validation_processing(self, instance: Any, value: Any) -> Any:
        return value

    def post_validation_processing(self, instance: Any, value: Any) -> Any:
        return value

    def post_set_processing(self, instance: Any, value: Any) -> Any:
        return value

    def pre_get_processing(self, instance: Any, value: Any) -> Any:
        return value

    def post_get_processing(self, instance: Any, value: Any) -> Any:
        return value

    def pre_delete_processing(self, instance: Any, value: Any) -> Any:
        return value

    def post_delete_processing(self, instance: Any, value: Any) -> Any:
        return value

    def notify_pre_set(self, obj: Any) -> None:
        """Lifecycle hook for composition; default no-op."""

    def notify_post_set(self, obj: Any) -> None:
        """Lifecycle hook for composition; default no-op."""

    def __and__(self, other: object) -> AllOf:
        if not isinstance(other, ValidateProperty):
            return NotImplemented
        from ux_valio.validators.compose import AllOf

        return AllOf(self, other)

    def __or__(self, other: object) -> AnyOf:
        if not isinstance(other, ValidateProperty):
            return NotImplemented
        from ux_valio.validators.compose import AnyOf

        return AnyOf(self, other)

    @abstractmethod
    def validate(self, instance: Any = None, value: Any = None) -> None:
        raise NotImplementedError
