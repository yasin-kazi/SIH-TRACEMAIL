"""Read-only Gmail API client.

Implements the minimal surface the picker and the raw-message acquisition need:

- ``list_messages`` — provider-side search (``q``, paging, capped), returns
  only message identifiers, never bodies.
- ``get_message_summary`` — the metadata headers shown by the picker
  (``format=metadata``).
- ``get_message_raw`` — **the only evidence retrieval form**: ``format=raw``,
  whose ``raw`` field is the base64url-encoded RFC-822 representation. The
  message is never reconstructed from headers/body.
- ``get_profile`` — the authorized account's ``emailAddress`` for provenance.

``userId`` is always the literal ``me`` (the mailbox the access token belongs
to). No provider field ever instructs analysis; the adapter only maps bytes and
provenance into the normalized ``AcquiredEmail`` contract.
"""
from __future__ import annotations

import asyncio
import base64
import binascii
import re
from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from .errors import (
    GmailAuthError,
    GmailError,
    GmailMalformedRawError,
    GmailMessageNotFoundError,
    GmailNetworkError,
    GmailPermissionError,
    GmailRateLimitError,
    GmailServerError,
)

_RAW_B64_RE = re.compile(r"[A-Za-z0-9\-_]*={0,2}")


@dataclass(frozen=True)
class GmailMessageSummary:
    """Picker row: identifier + display metadata only. No body, no payload."""

    id: str
    thread_id: str
    snippet: str = ""
    from_address: str = ""
    subject: str = ""
    date: str = ""
    internal_date_ms: int | None = None
    size_estimate: int | None = None


@dataclass(frozen=True)
class GmailRawMessage:
    """The raw message envelope returned by ``format=raw``."""

    id: str
    thread_id: str
    raw_b64: str
    internal_date_ms: int | None = None
    size_estimate: int | None = None


@dataclass(frozen=True)
class GmailProfile:
    email_address: str


class GmailApiClient(Protocol):
    """Structural contract for the Gmail provider client.

    Tests substitute a ``FakeGmailClient`` implementing the same surface.
    """

    async def list_messages(
        self,
        access_token: str,
        query: str = "",
        page_token: str | None = None,
        max_results: int = 10,
    ) -> tuple[list[GmailMessageSummary], str | None, int]:
        ...

    async def get_message_summary(
        self, access_token: str, message_id: str
    ) -> GmailMessageSummary:
        ...

    async def get_message_raw(
        self, access_token: str, message_id: str
    ) -> GmailRawMessage:
        ...

    async def get_profile(self, access_token: str) -> GmailProfile:
        ...


def decode_gmail_raw(raw_b64: str) -> bytes:
    """Decode the ``raw`` field of a Gmail ``format=raw`` response.

    Gmail encodes the RFC-822 representation as base64url and may omit padding;
    this pads to a multiple of four and decodes strictly. Any character outside
    the base64url alphabet, or a decoding failure, is a malformed-raw error —
    the message is never partially ingested or truncated.
    """
    if not raw_b64:
        raise GmailMalformedRawError("Gmail returned an empty raw message")
    cleaned = raw_b64.strip()
    if not _RAW_B64_RE.fullmatch(cleaned):
        raise GmailMalformedRawError(
            "Gmail raw message contains characters outside the base64url alphabet"
        )
    padded = cleaned + "=" * (-len(cleaned) % 4)
    try:
        return base64.urlsafe_b64decode(padded)
    except (binascii.Error, ValueError) as exc:
        raise GmailMalformedRawError(
            "Gmail raw message could not be base64-decoded"
        ) from exc


class GmailHttpClient:
    """Minimal REST client for the Gmail v1 API.

    Bounded retry/backoff applies only to transient provider failures
    (429/5xx/transport). Authorization failures are raised immediately without
    retry. Credentials are used only in the ``Authorization: Bearer`` header and
    never logged.
    """

    def __init__(
        self,
        api_base: str = "https://gmail.googleapis.com/gmail/v1",
        retries: int = 2,
        retry_backoff: tuple[float, ...] = (0.5, 1.0),
        http: httpx.AsyncClient | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._api_base = api_base.rstrip("/")
        self._retries = max(0, retries)
        self._backoff = tuple(retry_backoff)
        self._http = http or httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        await self._http.aclose()

    async def list_messages(
        self,
        access_token: str,
        query: str = "",
        page_token: str | None = None,
        max_results: int = 10,
    ) -> tuple[list[GmailMessageSummary], str | None, int]:
        params: dict[str, Any] = {"maxResults": max(1, min(max_results, 50))}
        if query:
            params["q"] = query
        if page_token:
            params["pageToken"] = page_token
        body = await self._get("/users/me/messages", params, access_token)
        messages = body.get("messages", []) or []
        summaries = [
            GmailMessageSummary(
                id=msg["id"],
                thread_id=msg.get("threadId", msg["id"]),
            )
            for msg in messages
            if msg.get("id")
        ]
        return (
            summaries,
            body.get("nextPageToken"),
            int(body.get("resultSizeEstimate", 0) or 0),
        )

    async def get_message_summary(
        self, access_token: str, message_id: str
    ) -> GmailMessageSummary:
        body = await self._get(
            f"/users/me/messages/{_safe_id(message_id)}",
            params={
                "format": "metadata",
                "metadataHeaders": ["From", "Subject", "Date"],
            },
            access_token=access_token,
        )
        return self._summary_from_response(body)

    async def get_message_raw(
        self, access_token: str, message_id: str
    ) -> GmailRawMessage:
        body = await self._get(
            f"/users/me/messages/{_safe_id(message_id)}",
            params={"format": "raw"},
            access_token=access_token,
        )
        raw_b64 = body.get("raw") or ""
        return GmailRawMessage(
            id=body.get("id", message_id),
            thread_id=body.get("threadId", message_id),
            raw_b64=raw_b64,
            internal_date_ms=_as_int(body.get("internalDate")),
            size_estimate=_as_int(body.get("sizeEstimate")),
        )

    async def get_profile(self, access_token: str) -> GmailProfile:
        body = await self._get("/users/me/profile", params={}, access_token=access_token)
        return GmailProfile(email_address=body.get("emailAddress", ""))

    # ── internals ───────────────────────────────────────────────────────────

    @staticmethod
    def _summary_from_response(body: dict[str, Any]) -> GmailMessageSummary:
        headers: dict[str, str] = {}
        payload = body.get("payload") or {}
        for header in payload.get("headers", []) or []:
            name = str(header.get("name", "")).lower()
            if name in ("from", "subject", "date"):
                headers.setdefault(name, str(header.get("value", "")))
        return GmailMessageSummary(
            id=body.get("id", ""),
            thread_id=body.get("threadId", ""),
            snippet=body.get("snippet", "") or "",
            from_address=headers.get("from", ""),
            subject=headers.get("subject", ""),
            date=headers.get("date", ""),
            internal_date_ms=_as_int(body.get("internalDate")),
            size_estimate=_as_int(body.get("sizeEstimate")),
        )

    async def _get(
        self,
        path: str,
        params: dict[str, Any],
        access_token: str,
    ) -> dict[str, Any]:
        url = f"{self._api_base}{path}"
        headers = {"Authorization": f"Bearer {access_token}"}
        attempts = self._retries + 1
        last_error: GmailError | None = None
        for attempt in range(attempts):
            try:
                response = await self._http.get(url, params=params, headers=headers)
            except httpx.HTTPError as exc:
                last_error = GmailNetworkError(
                    f"Network failure reaching Gmail API ({type(exc).__name__})"
                )
            else:
                if response.status_code == 200:
                    try:
                        return response.json()
                    except ValueError as exc:
                        raise GmailServerError(
                            "Gmail API returned a non-JSON response"
                        ) from exc
                last_error = self._error_for_status(response.status_code, response.text)
            if attempt < attempts - 1 and _retriable(last_error):
                await asyncio.sleep(self._backoff[min(attempt, len(self._backoff) - 1)])
        raise last_error  # type: ignore[misc]

    @staticmethod
    def _error_for_status(status: int, body: str) -> GmailError:
        if status == 401:
            return GmailAuthError("Gmail access token was rejected; reconnect required")
        if status == 403:
            return GmailPermissionError(
                "The authorized account cannot read this resource"
            )
        if status == 404:
            return GmailMessageNotFoundError(
                "The selected message is no longer available"
            )
        if status == 429:
            return GmailRateLimitError("Gmail is rate-limiting requests")
        if status >= 500:
            return GmailServerError(f"Gmail API server error ({status})")
        return GmailServerError(f"Unexpected Gmail API response ({status})")


def _safe_id(message_id: str) -> str:
    """Message ids come from the picker; only allow safe characters."""
    if not message_id or not re.fullmatch(r"[A-Za-z0-9\-_.]+", message_id):
        raise GmailMessageNotFoundError("Invalid message identifier")
    return message_id


def _as_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _retriable(error: GmailError | None) -> bool:
    from .errors import GmailRateLimitError, GmailServerError, GmailNetworkError

    return isinstance(error, (GmailRateLimitError, GmailServerError, GmailNetworkError))