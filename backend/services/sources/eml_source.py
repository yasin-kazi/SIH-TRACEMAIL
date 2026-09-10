"""EML file acquisition adapter (Phase 1 source).

Wraps raw ``.eml`` bytes plus their file metadata into the normalized
:class:`AcquiredEmail` understood by the forensic pipeline.
"""
from __future__ import annotations

from typing import Any
from .email_source import EmailSource, AcquiredEmail


class EMLSource:
    """Acquires an email from raw ``.eml`` bytes."""

    source_type = "eml_upload"

    def __init__(
        self,
        filename: str,
        raw_bytes: bytes,
        content_type: str = "message/rfc822",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.filename = filename
        self.raw_bytes = raw_bytes
        self.content_type = content_type
        self.metadata = dict(metadata or {})

    def acquire(self) -> AcquiredEmail:
        return AcquiredEmail(
            source_type=self.source_type,
            source_identifier=self.filename,
            original_filename=self.filename,
            content_type=self.content_type,
            raw_bytes=self.raw_bytes,
            acquisition_method="upload",
            metadata=self.metadata,
        )