"""The EmailSource capture contract.

An ``EmailSource`` is anything that can acquire one raw email and normalize it
into an :class:`AcquiredEmail` for the forensic pipeline. Future adapters
(Gmail, Microsoft 365, raw-message, header-paste) implement the same structural
contract without changing the pipeline.
"""
from __future__ import annotations

import dataclasses
from typing import Any, Protocol


@dataclasses.dataclass(frozen=True)
class AcquiredEmail:
    """Normalized acquisition payload handed to the forensic pipeline.

    Attributes
    ----------
    source_type:
        Canonical source discriminator, one of ``eml_upload``, ``gmail``,
        ``microsoft365``, ``raw_message``, ``header_paste``.
    source_identifier:
        Stable identifier for the acquired message within its source, e.g. the
        provider message id, or the original filename for an EML.
    original_filename:
        Original filename when applicable (empty string otherwise).
    content_type:
        MIME content type of the raw message (default ``message/rfc822``).
    raw_bytes:
        The original acquired bytes, byte-for-byte. SHA-256 is computed from
        these exact bytes; nothing is normalized or rewritten.
    acquisition_method:
        How the bytes were acquired (``upload`` for Phase 1).
    metadata:
        Free-form, source-specific metadata (never treated as instructions).
    """

    source_type: str
    source_identifier: str
    original_filename: str
    content_type: str
    raw_bytes: bytes
    acquisition_method: str = "upload"
    metadata: dict[str, Any] = dataclasses.field(default_factory=dict)


class EmailSource(Protocol):
    """Structural contract for email acquisition adapters."""

    source_type: str

    def acquire(self) -> AcquiredEmail:
        """Return the normalized acquired email for the forensic pipeline."""
        ...