# SPDX-License-Identifier: MIT
"""India statutory identity. Folder of domain layers.

Sibling layers (do not import each other)::

    kyc       — person documents (Aadhaar, PAN, Voter, passport)
    gst       — GST invoice (GSTIN, HSN)
    registry  — TAN, CIN, Udyam, DIN, LLPIN, FSSAI
    bank      — IFSC, PIN, UPI

Parallel to ``named.finance`` / ``named.catalog``. Public names
still re-export from ``ux_valio``; navigation is
``from ux_valio.facades.named.india.gst import GSTINValidator``.
"""

from ux_valio.facades.named.india.bank import (
    IFSCValidator,
    PinCodeValidator,
    UPIIdValidator,
)
from ux_valio.facades.named.india.gst import GSTINValidator, HSNCodeValidator
from ux_valio.facades.named.india.kyc import (
    AadhaarCardValidator,
    IndianPassportValidator,
    PANCardValidator,
    VoterIdValidator,
)
from ux_valio.facades.named.india.registry import (
    CINValidator,
    DINValidator,
    FSSAIValidator,
    LLPINValidator,
    TANValidator,
    UdyamValidator,
)

__all__ = [
    "AadhaarCardValidator",
    "CINValidator",
    "DINValidator",
    "FSSAIValidator",
    "GSTINValidator",
    "HSNCodeValidator",
    "IFSCValidator",
    "IndianPassportValidator",
    "LLPINValidator",
    "PANCardValidator",
    "PinCodeValidator",
    "TANValidator",
    "UPIIdValidator",
    "UdyamValidator",
    "VoterIdValidator",
]
