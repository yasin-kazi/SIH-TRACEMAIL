"""Gmail acquisition adapter against the existing ``EmailSource`` contract.

Maps the decoded ``format=raw`` bytes plus provider provenance into the same
normalized :class:`AcquiredEmail` the forensic pipeline already consumes. The
raw bytes are passed through untouched; the SHA-256 is computed from these
exact bytes (identical result to the hash the pipeline derives from the same
bytes during parsing).
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from services.sources.email_source import AcquiredEmail

ACQUISITION_METHOD = "gmail_oauth"
RAW_NOTE = "SHA-256 of bytes returned by Gmail format=raw at acquisition time."


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class GmailSource:
    """One acquired Gmail message (provider message id + raw bytes)."""

    source_type = "gmail"

    def __init__(
        self,
        message_id: str,
        raw_bytes: bytes,
        thread_id: str = "",
        internal_date_ms: int | None = None,
        size_estimate: int | None = None,
        account: str = "",
    ) -> None:
        self.message_id = message_id
        self.raw_bytes = raw_bytes
        self.thread_id = thread_id or message_id
        self.internal_date_ms = internal_date_ms
        self.size_estimate = size_estimate
        self.account = account or ""

    def acquire(self) -> AcquiredEmail:
        message_id = self.message_id
        sha256 = hashlib.sha256(self.raw_bytes).hexdigest()
        metadata: dict[str, Any] = {
            "provider": "gmail",
            "message_id": message_id,
            "thread_id": self.thread_id,
            "internal_date_ms": self.internal_date_ms,
            "size_estimate": self.size_estimate,
            "raw_format": "raw",
            "acquisition_time_utc": _iso_now(),
            "sha256": sha256,
            "size_bytes": len(self.raw_bytes),
            "acquisition_note": RAW_NOTE,
        }
        if self.account:
            metadata["account"] = self.account
        return AcquiredEmail(
            source_type=self.source_type,
            source_identifier=message_id,
            original_filename="",
            content_type="message/rfc822",
            raw_bytes=self.raw_bytes,
            acquisition_method=ACQUISITION_METHOD,
            metadata=metadata,
        )