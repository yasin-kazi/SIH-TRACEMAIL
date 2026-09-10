"""Encrypted, server-side token storage for Gmail connections.

Credentials never leave the backend: the database holds only AES-256-GCM
ciphertext (nonce-prefixed, ``key`` from configuration), and every returned
token is decrypted in memory for the lifetime of one request. The store
distinguishes missing, expired (access token past freshness), and revoked
credentials so the acquisition service can refresh or demand a re-connect.

The surface is a small protocol so a KMS-backed store can be added later
without touching the acquisition or OAuth services.
"""
from __future__ import annotations

import base64
import json
import logging
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import GmailConnection

log = logging.getLogger(__name__)


class CredentialStatus:
    MISSING = "missing"
    EXPIRED = "expired"
    REVOKED = "revoked"
    VALID = "valid"


@dataclass(frozen=True)
class OAuthTokens:
    """Short-lived decrypted token material for one acquisition flow."""

    access_token: str
    refresh_token: str
    expires_at: datetime | None
    account_email: str = ""
    scopes: tuple[str, ...] = ()


@dataclass(frozen=True)
class StoredConnection:
    """A retrieved connection view (tokens decrypted, status resolved)."""

    connection_id: str
    account_email: str
    access_token: str
    refresh_token: str
    expires_at: datetime | None
    status: str


class TokenStore(Protocol):
    """Storage lifecycle for Gmail OAuth credentials.

    Concurrency note: the current application is a single-analyst workstation,
    so the store resolves one "current" connected account.
    """

    async def save_connection(
        self,
        *,
        account_email: str,
        access_token: str,
        refresh_token: str,
        expires_at: datetime | None,
        scopes: tuple[str, ...],
        status: str = "connected",
    ) -> str: ...

    async def get_current(self, now: datetime | None = None) -> StoredConnection | None: ...

    async def mark_revoked(self, now: datetime | None = None) -> None: ...

    async def delete_all(self) -> None: ...


class SecretCipher:
    """AES-256-GCM envelope for the sensitive token fields."""

    VERSION = "v1"

    def __init__(self, key: bytes) -> None:
        if len(key) != 32:
            raise ValueError("AES-256 requires a 32-byte key")
        self._aead = AESGCM(key)

    def encrypt(self, plaintext: str) -> str:
        nonce = secrets.token_bytes(12)
        ciphertext = self._aead.encrypt(nonce, plaintext.encode("utf-8"), None)
        blob = base64.urlsafe_b64encode(nonce + ciphertext).decode("ascii")
        return f"{self.VERSION}:{blob}"

    def decrypt(self, blob: str | None) -> str:
        if not blob:
            return ""
        version, _, payload = blob.partition(":")
        if version != self.VERSION:
            raise ValueError(f"Unsupported ciphertext version: {version!r}")
        raw = base64.urlsafe_b64decode(payload)
        nonce, ciphertext = raw[:12], raw[12:]
        return self._aead.decrypt(nonce, ciphertext, None).decode("utf-8")


class SqlTokenStore:
    """SQLAlchemy-backed token store over :class:`GmailConnection`."""

    def __init__(self, db: AsyncSession, cipher: SecretCipher) -> None:
        self._db = db
        self._cipher = cipher

    async def save_connection(
        self,
        *,
        account_email: str,
        access_token: str,
        refresh_token: str,
        expires_at: datetime | None,
        scopes: tuple[str, ...],
        status: str = "connected",
    ) -> str:
        # Single active connection: replace any previous connected row so a
        # new OAuth connection supersedes the old one.
        result = await self._db.execute(
            select(GmailConnection).where(GmailConnection.status == "connected")
        )
        for old in result.scalars().all():
            await self._db.delete(old)
        await self._db.flush()

        connection_id = f"gmail-conn-{uuid.uuid4().hex[:12]}"
        self._db.add(GmailConnection(
            id=connection_id,
            account_email=account_email,
            access_token_enc=self._cipher.encrypt(access_token),
            refresh_token_enc=self._cipher.encrypt(refresh_token) if refresh_token else "",
            access_token_expires_at=expires_at,
            scopes_json=json.dumps(list(scopes)),
            status=status,
        ))
        await self._db.commit()
        return connection_id

    async def get_current(self, now: datetime | None = None) -> StoredConnection | None:
        now = now or datetime.utcnow()
        result = await self._db.execute(
            select(GmailConnection)
            .where(GmailConnection.status == "connected")
            .order_by(GmailConnection.created_at.desc())
        )
        row = result.scalars().first()
        if row is None:
            # A revoked row exists: surface it so the service can report
            # "reconnect required" instead of silently treating it as new.
            revoked = await self._db.execute(
                select(GmailConnection).where(GmailConnection.status == "revoked")
            )
            rev = revoked.scalars().first()
            if rev is not None:
                return StoredConnection(
                    connection_id=rev.id,
                    account_email=rev.account_email,
                    access_token="",
                    refresh_token=self._cipher.decrypt(rev.refresh_token_enc),
                    expires_at=None,
                    status=CredentialStatus.REVOKED,
                )
            return None

        expires_at = row.access_token_expires_at
        if expires_at is not None and expires_at <= now:
            status = CredentialStatus.EXPIRED
        else:
            status = CredentialStatus.VALID
        return StoredConnection(
            connection_id=row.id,
            account_email=row.account_email,
            access_token=self._cipher.decrypt(row.access_token_enc),
            refresh_token=self._cipher.decrypt(row.refresh_token_enc),
            expires_at=expires_at,
            status=status,
        )

    async def mark_revoked(self, now: datetime | None = None) -> None:
        result = await self._db.execute(
            select(GmailConnection).where(GmailConnection.status == "connected")
        )
        for row in result.scalars().all():
            row.status = "revoked"
        await self._db.commit()

    async def delete_all(self) -> None:
        await self._db.execute(delete(GmailConnection))
        await self._db.commit()