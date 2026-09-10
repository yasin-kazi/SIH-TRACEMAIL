"""OAuth 2.0 Authorization Code + PKCE for Gmail.

Server-side only: the browser never sees the client secret or the
authorization code after callback. ``state`` is a CSPRNG value bound to the
originating connection attempt, single-use, expiring (≤10 minutes), verified
with a constant-time comparison. PKCE is used as defense-in-depth even though
this is a confidential client.

On callback success the browser is redirected to the frontend origin with only
a success signal — no code, token, or ticket value is placed in the frontend
URL.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import secrets
import time
from dataclasses import dataclass
from typing import Any, Protocol

import httpx
from urllib.parse import urlencode

from .errors import (
    GmailAuthError,
    GmailConfigError,
    GmailNetworkError,
    GmailRateLimitError,
    GmailServerError,
    GmailStateExpiredError,
    GmailStateInvalidError,
    GmailStateReusedError,
)

log = logging.getLogger(__name__)

STATE_MAX_AGE_SECONDS = 600  # ≤ 10 minutes


@dataclass(frozen=True)
class ExchangedTokens:
    access_token: str
    refresh_token: str = ""
    expires_in: int = 3600
    scope: str = ""
    token_type: str = "Bearer"


class OAuthProvider(Protocol):
    def build_auth_url(self, state: str, code_verifier: str) -> str: ...

    async def exchange_code(self, code: str, code_verifier: str) -> ExchangedTokens: ...

    async def refresh_access(self, refresh_token: str) -> ExchangedTokens: ...

    async def revoke(self, refresh_token: str) -> None: ...


class OAuthStateStore:
    """Short-lived, single-use ``state`` registry bound to a browser attempt."""

    def __init__(
        self,
        max_age_seconds: int = STATE_MAX_AGE_SECONDS,
        now: Any = None,
    ) -> None:
        self._max_age = max_age_seconds
        self._now = now or time.time
        self._pending: dict[str, dict[str, Any]] = {}
        self._spent: dict[str, float] = {}

    def create(self) -> tuple[str, str]:
        """Return (state, code_verifier). Both are CSPRNG-generated."""
        state = secrets.token_urlsafe(32)
        verifier = secrets.token_urlsafe(64)
        self._pending[state] = {"code_verifier": verifier, "created_at": self._now()}
        self._prune()
        return state, verifier

    def consume(self, state: str) -> str:
        """Return the code_verifier for a valid state (valid only once)."""
        if not state:
            raise GmailStateInvalidError("Missing OAuth state")
        entry = self._pending.pop(state, None)
        if entry is None:
            if state in self._spent:
                raise GmailStateReusedError("OAuth state was already used")
            raise GmailStateInvalidError("OAuth state is invalid or tampered")
        age = self._now() - entry["created_at"]
        if age > self._max_age:
            self._spent[state] = self._now()
            self._prune_spent()
            raise GmailStateExpiredError("OAuth state has expired")
        self._spent[state] = self._now()
        self._prune_spent()
        return entry["code_verifier"]

    def verify(self, state: str, expected: str) -> bool:
        """Constant-time comparison guard for callbacks carrying server state."""
        if not state or not expected:
            return False
        return hmac.compare_digest(state, expected)

    def _prune(self) -> None:
        cutoff = self._now() - self._max_age
        for state in [s for s, e in self._pending.items() if e["created_at"] < cutoff]:
            self._spent[state] = self._now()
            self._pending.pop(state, None)

    def _prune_spent(self) -> None:
        cutoff = self._now() - self._max_age
        for state in [s for s, ts in self._spent.items() if ts < cutoff]:
            self._spent.pop(state, None)

    def clear(self) -> None:
        self._pending.clear()
        self._spent.clear()


def _code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


class GoogleOAuthProvider:
    """Real Google OAuth endpoint provider (token exchange, refresh, revoke)."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        auth_endpoint: str = "https://accounts.google.com/o/oauth2/v2/auth",
        token_endpoint: str = "https://oauth2.googleapis.com/token",
        revoke_endpoint: str = "https://oauth2.googleapis.com/revoke",
        scopes: tuple[str, ...] = ("https://www.googleapis.com/auth/gmail.readonly",),
        http: httpx.AsyncClient | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri
        self._auth_endpoint = auth_endpoint
        self._token_endpoint = token_endpoint
        self._revoke_endpoint = revoke_endpoint
        self._scopes = scopes
        self._http = http or httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        await self._http.aclose()

    def _ensure_config(self) -> None:
        if not self._client_id or not self._client_secret:
            raise GmailConfigError(
                "Gmail OAuth is not configured: TRACEMAIL_GMAIL_CLIENT_ID / "
                "TRACEMAIL_GMAIL_CLIENT_SECRET must be set to connect Gmail"
            )

    def build_auth_url(self, state: str, code_verifier: str) -> str:
        self._ensure_config()
        params = {
            "response_type": "code",
            "client_id": self._client_id,
            "redirect_uri": self._redirect_uri,
            "scope": " ".join(self._scopes),
            "state": state,
            "code_challenge": _code_challenge(code_verifier),
            "code_challenge_method": "S256",
            "access_type": "offline",
            "prompt": "consent",
            "include_granted_scopes": "false",
        }
        return f"{self._auth_endpoint}?{urlencode(params)}"

    async def exchange_code(self, code: str, code_verifier: str) -> ExchangedTokens:
        self._ensure_config()
        if not code:
            raise GmailAuthError("Missing authorization code")
        return await self._token_request(
            {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self._redirect_uri,
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "code_verifier": code_verifier,
            }
        )

    async def refresh_access(self, refresh_token: str) -> ExchangedTokens:
        self._ensure_config()
        if not refresh_token:
            raise GmailAuthError("No refresh token is stored; reconnect required")
        return await self._token_request(
            {
                "grant_type": "refresh_token",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "refresh_token": refresh_token,
            }
        )

    async def revoke(self, refresh_token: str) -> None:
        try:
            async with self._http as client:
                response = await client.post(
                    self._revoke_endpoint,
                    data={"token": refresh_token},
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
            if response.status_code != 200:
                log.info("revoke endpoint returned HTTP %s", response.status_code)
        except httpx.HTTPError as exc:
            log.info("revoke call failed (best-effort): %s", type(exc).__name__)

    async def _token_request(self, data: dict[str, str]) -> ExchangedTokens:
        try:
            async with self._http as client:
                response = await client.post(
                    self._token_endpoint,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
        except httpx.HTTPError as exc:
            raise GmailNetworkError(
                f"OAuth token endpoint unreachable ({type(exc).__name__})"
            ) from exc
        if response.status_code >= 500:
            raise GmailServerError("OAuth token endpoint returned a server error")
        if response.status_code != 200:
            body = response.text[:200]
            if response.status_code == 429:
                raise GmailRateLimitError("OAuth token endpoint is rate-limiting")
            raise GmailAuthError(
                f"OAuth token exchange failed (HTTP {response.status_code})"
            )
        try:
            payload: dict[str, Any] = response.json()
        except ValueError as exc:
            raise GmailServerError("OAuth endpoint returned a non-JSON response") from exc
        access_token = payload.get("access_token")
        if not access_token:
            raise GmailAuthError("OAuth endpoint returned no access token")
        return ExchangedTokens(
            access_token=str(access_token),
            refresh_token=str(payload.get("refresh_token", "") or ""),
            expires_in=int(payload.get("expires_in", 3600) or 3600),
            scope=str(payload.get("scope", "") or ""),
            token_type=str(payload.get("token_type", "Bearer") or "Bearer"),
        )