"""Gmail acquisition configuration, loaded from the environment.

Every value has a safe development default or a clear "not configured" state.
The OAuth client secret and the encryption key are read from configuration only
and never logged, stored in plaintext, or returned to the browser.
"""
from __future__ import annotations

import base64
import os
from dataclasses import dataclass, field

from .errors import GmailConfigError

# Default byte cap for a decoded raw message returned by Gmail format=raw.
DEFAULT_MAX_RAW_BYTES = 25 * 1024 * 1024

# Development-only fallback encryption key (32 bytes). Never use in production.
_DEV_ONLY_KEY = bytes(range(32)).hex()


@dataclass(frozen=True)
class GmailConfig:
    client_id: str = ""
    client_secret: str = ""
    redirect_uri: str = "http://localhost:8000/api/gmail/oauth/callback"
    frontend_origin: str = "http://localhost:5173"
    token_endpoint: str = "https://oauth2.googleapis.com/token"
    revoke_endpoint: str = "https://oauth2.googleapis.com/revoke"
    auth_endpoint: str = "https://accounts.google.com/o/oauth2/v2/auth"
    gmail_api_base: str = "https://gmail.googleapis.com/gmail/v1"
    scopes: list[str] = field(
        default_factory=lambda: [
            "https://www.googleapis.com/auth/gmail.readonly",
        ]
    )
    max_raw_bytes: int = DEFAULT_MAX_RAW_BYTES
    access_token_skew_seconds: int = 60
    retries: int = 2
    retry_backoff: tuple[float, ...] = (0.5, 1.0)


def encryption_key_from_env(env=None) -> bytes:
    """Return the AES-256 key (32 bytes) for token encryption.

    ``TRACEMAIL_ENCRYPTION_KEY`` may be supplied as 64 hex characters or as
    URL-safe base64 of exactly 32 bytes. When absent a deterministic key that is
    explicitly development-only is used so the app and tests run without setup;
    the warning below makes it impossible to miss in production.
    """
    import logging

    env = env or os.environ
    raw = env.get("TRACEMAIL_ENCRYPTION_KEY") or ""
    if not raw:
        logging.getLogger(__name__).warning(
            "TRACEMAIL_ENCRYPTION_KEY is not set; using a DEVELOPMENT-ONLY "
            "fallback key for Gmail token encryption. Never deploy with it."
        )
        return bytes.fromhex(_DEV_ONLY_KEY)
    try:
        if raw.startswith(("hex:", "HEX:")):
            decoded = bytes.fromhex(raw[4:])
        elif raw.startswith(("b64:", "B64:")):
            decoded = base64.urlsafe_b64decode(raw[4:])
        elif len(raw) == 64 and all(c in "0123456789abcdefABCDEF" for c in raw):
            decoded = bytes.fromhex(raw)
        else:
            decoded = base64.urlsafe_b64decode(raw)
    except (ValueError, TypeError) as exc:
        raise GmailConfigError(
            "TRACEMAIL_ENCRYPTION_KEY must be 32 bytes (64 hex chars or URL-safe base64)"
        ) from exc
    if len(decoded) != 32:
        raise GmailConfigError(
            "TRACEMAIL_ENCRYPTION_KEY must decode to exactly 32 bytes"
        )
    return decoded


def load_config(env=None) -> GmailConfig:
    env = env or os.environ
    max_raw = int(env.get("TRACEMAIL_GMAIL_MAX_RAW_BYTES", DEFAULT_MAX_RAW_BYTES))
    return GmailConfig(
        client_id=env.get("TRACEMAIL_GMAIL_CLIENT_ID", ""),
        client_secret=env.get("TRACEMAIL_GMAIL_CLIENT_SECRET", ""),
        redirect_uri=env.get(
            "TRACEMAIL_GMAIL_REDIRECT_URI",
            "http://localhost:8000/api/gmail/oauth/callback",
        ),
        frontend_origin=env.get("TRACEMAIL_FRONTEND_ORIGIN", "http://localhost:5173"),
        token_endpoint=env.get("TRACEMAIL_GMAIL_TOKEN_ENDPOINT", "https://oauth2.googleapis.com/token"),
        revoke_endpoint=env.get("TRACEMAIL_GMAIL_REVOKE_ENDPOINT", "https://oauth2.googleapis.com/revoke"),
        auth_endpoint=env.get("TRACEMAIL_GMAIL_AUTH_ENDPOINT", "https://accounts.google.com/o/oauth2/v2/auth"),
        gmail_api_base=env.get("TRACEMAIL_GMAIL_API_BASE", "https://gmail.googleapis.com/gmail/v1"),
        max_raw_bytes=max(1, max_raw),
        retries=max(0, int(env.get("TRACEMAIL_GMAIL_RETRIES", "2"))),
    )