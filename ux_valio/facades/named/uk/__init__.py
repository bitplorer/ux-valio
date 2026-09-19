# SPDX-License-Identifier: MIT
"""United Kingdom statutory identity. Folder of domain layers.

Sibling layers (do not import each other)::

    postal — Royal Mail postcode
    bank   — sort code

Parallel to ``named.india`` / ``named.us``. Public names re-export
from ``ux_valio``.
"""

from ux_valio.facades.named.uk.bank import UKSortCodeValidator
from ux_valio.facades.named.uk.postal import UKPostcodeValidator

__all__ = [
    "UKPostcodeValidator",
    "UKSortCodeValidator",
]
