"""Typed errors for Gmail acquisition.

Each failure mode maps to exactly one error type so the router can surface a
clear API response. There is no fake/cached fallback path: authorization
failures are terminal and require a fresh OAuth connection.
"""
from __future__ import annotations


class GmailError(Exception):
    """Base class for all Gmail acquisition errors."""


class GmailConfigError(GmailError):
    """Server-side Gmail configuration is missing (OAuth client not set up)."""


class GmailAuthRequiredError(GmailError):
    """No usable Gmail connection exists; the analyst must connect OAuth first."""


class GmailAuthError(GmailError):
    """Access was revoked or the refresh token is no longer valid — reconnect."""


class GmailPermissionError(GmailError):
    """403 — the authorized account may not read the requested resource."""


class GmailMessageNotFoundError(GmailError):
    """404 — the selected provider message is no longer available."""


class GmailRateLimitError(GmailError):
    """429 — Gmail is rate-limiting; the request can be retried later."""


class GmailServerError(GmailError):
    """5xx — Gmail API returned a server-side failure."""


class GmailNetworkError(GmailError):
    """Transport-level failure talking to Gmail."""


class GmailTooLargeError(GmailError):
    """Decoded raw-message size exceeds the hard cap; refused, never truncated."""


class GmailMalformedRawError(GmailError):
    """The provider raw message could not be base64-decoded or parsed."""


class GmailStateError(GmailError):
    """OAuth state validation failed (invalid, reused, or expired)."""


class GmailStateInvalidError(GmailStateError):
    """The OAuth state is missing/tampered (never issued or already consumed)."""


class GmailStateExpiredError(GmailStateInvalidError):
    """The OAuth state is older than the allowed window."""


class GmailStateReusedError(GmailStateError):
    """The OAuth state was already consumed for a previous exchange."""


class GmailDuplicateError(GmailError):
    """The selected message was already acquired into a TraceMail case."""

    def __init__(self, message: str, case_id: str = "") -> None:
        super().__init__(message)
        self.case_id = case_id


class GmailDuplicateMissing(GmailError):
    """Internal: duplicate check failed unexpectedly."""