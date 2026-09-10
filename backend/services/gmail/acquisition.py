"""Gmail acquisition orchestration service.

Binds the provider client, OAuth provider, token store, and the existing
:func:`ingest_acquired_email` pipeline into the picker/acquisition endpoints.
The forensic engine is untouched: this service only produces a normalized
``AcquiredEmail`` from the exact bytes returned by Gmail ``format=raw``.
"""
from __future__ import annotations

import hashlib
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import async_session
from models import EvidenceRecord, SourceRecord
from services.ingest_email import UnparsableEmail, ingest_acquired_email

from .client import GmailApiClient, GmailHttpClient, GmailMessageSummary, decode_gmail_raw
from .config import GmailConfig, encryption_key_from_env, load_config
from .errors import (
    GmailAuthError,
    GmailAuthRequiredError,
    GmailDuplicateError,
    GmailMalformedRawError,
    GmailMessageNotFoundError,
    GmailStateError,
    GmailStateExpiredError,
    GmailStateInvalidError,
    GmailStateReusedError,
    GmailTooLargeError,
)
from .gmail_source import GmailSource
from .oauth import GoogleOAuthProvider, OAuthProvider, OAuthStateStore, STATE_MAX_AGE_SECONDS
from .token_store import CredentialStatus, SecretCipher, SqlTokenStore, TokenStore, StoredConnection

TokenStoreFactory = Callable[[AsyncSession], TokenStore]


def _summary_to_dict(summary: GmailMessageSummary) -> dict[str, Any]:
    return {
        "id": summary.id,
        "thread_id": summary.thread_id,
        "snippet": summary.snippet,
        "from_address": summary.from_address,
        "subject": summary.subject,
        "date": summary.date,
        "internal_date_ms": summary.internal_date_ms,
        "size_estimate": summary.size_estimate,
    }


@dataclass
class GmailService:
    config: GmailConfig
    client: GmailApiClient
    oauth: OAuthProvider
    token_store_factory: TokenStoreFactory
    state_store: OAuthStateStore = field(default_factory=OAuthStateStore)

    @asynccontextmanager
    async def _session(self):
        async with async_session() as session:
            yield session

    def _store_for(self, db: AsyncSession) -> TokenStore:
        return self.token_store_factory(db)

    # ── connection / OAuth flow ─────────────────────────────────────────────

    async def status(self) -> dict[str, Any]:
        async with self._session() as db:
            stored = await self._store_for(db).get_current()
        if stored is None:
            return {
                "connected": False,
                "source": "gmail",
                "status": CredentialStatus.MISSING,
                "account": None,
            }
        if stored.status == CredentialStatus.REVOKED:
            return {
                "connected": False,
                "source": "gmail",
                "status": CredentialStatus.REVOKED,
                "account": stored.account_email or None,
            }
        connected = stored.status == CredentialStatus.VALID
        return {
            "connected": connected,
            "source": "gmail",
            "status": CredentialStatus.VALID if connected else CredentialStatus.EXPIRED,
            "account": stored.account_email or None,
        }

    async def auth_url(self) -> str:
        state, code_verifier = self.state_store.create()
        return self.oauth.build_auth_url(state, code_verifier)

    def _frontend(self, suffix: str) -> str:
        return f"{self.config.frontend_origin.rstrip('/')}{suffix}"

    async def complete_callback(
        self, state: str, code: str, error: Optional[str]
    ) -> str:
        """Validate state, exchange the code server-side, persist tokens.

        Returns the frontend redirect URL. No code/token material is included.
        """
        if error:
            return self._frontend("/investigation?connect=" + ("denied" if error == "access_denied" else "error"))
        try:
            verifier = self.state_store.consume(state)
        except GmailStateExpiredError:
            return self._frontend("/investigation?connect=expired")
        except (GmailStateInvalidError, GmailStateReusedError):
            return self._frontend("/investigation?connect=invalid")

        try:
            tokens = await self.oauth.exchange_code(code, verifier)
        except (GmailStateError, GmailAuthError):
            return self._frontend("/investigation?connect=error")

        # Account provenance (best-effort; scopes cover it via gmail.readonly).
        account = ""
        try:
            profile = await self.client.get_profile(tokens.access_token)
            account = profile.email_address or ""
        except Exception:
            account = ""

        expires_at = datetime.utcnow() + timedelta(seconds=tokens.expires_in)
        scope_set = tuple(tokens.scope.split()) if tokens.scope else tuple(self.config.scopes)
        async with self._session() as db:
            await self._store_for(db).save_connection(
                account_email=account,
                access_token=tokens.access_token,
                refresh_token=tokens.refresh_token or "",
                expires_at=expires_at,
                scopes=scope_set,
            )
        return self._frontend("/investigation?connect=success")

    async def revoke(self) -> dict[str, Any]:
        stored: Optional[StoredConnection] = None
        async with self._session() as db:
            stored = await self._store_for(db).get_current()
        if stored is not None and stored.refresh_token:
            try:
                await self.oauth.revoke(stored.refresh_token)
            except Exception:
                pass  # best-effort; local rows are still deleted below
        async with self._session() as db:
            await self._store_for(db).mark_revoked()
            await self._store_for(db).delete_all()
        return {"status": "disconnected"}

    async def _require_access_token(self) -> str:
        stored: Optional[StoredConnection] = None
        async with self._session() as db:
            stored = await self._store_for(db).get_current()
        if stored is None:
            raise GmailAuthRequiredError("Gmail is not connected")
        if stored.status == CredentialStatus.REVOKED:
            raise GmailAuthError("Gmail access was revoked; reconnect required")
        if stored.status == CredentialStatus.EXPIRED:
            refreshed = await self.oauth.refresh_access(stored.refresh_token)
            expires_at = datetime.utcnow() + timedelta(seconds=refreshed.expires_in)
            async with self._session() as db:
                await self._store_for(db).save_connection(
                    account_email=stored.account_email,
                    access_token=refreshed.access_token,
                    refresh_token=refreshed.refresh_token or stored.refresh_token,
                    expires_at=expires_at,
                    scopes=tuple(refreshed.scope.split()) if refreshed.scope else tuple(self.config.scopes),
                )
            return refreshed.access_token
        return stored.access_token

    # ── picker endpoints ────────────────────────────────────────────────────

    async def search(
        self, query: str, page_token: Optional[str], max_results: int = 10
    ) -> dict[str, Any]:
        access_token = await self._require_access_token()
        summaries, next_token, estimate = await self.client.list_messages(
            access_token,
            query=query or "",
            page_token=page_token,
            max_results=max(1, min(max_results, 50)),
        )
        rows: list[GmailMessageSummary] = []
        for summary in summaries:
            if not (summary.subject or summary.from_address):
                detail = await self.client.get_message_summary(access_token, summary.id)
                rows.append(detail)
            else:
                rows.append(summary)
        return {
            "messages": [_summary_to_dict(r) for r in rows],
            "next_page_token": next_token,
            "result_size_estimate": estimate,
        }

    async def get_metadata(self, message_id: str) -> dict[str, Any]:
        access_token = await self._require_access_token()
        summary = await self.client.get_message_summary(access_token, message_id)
        return _summary_to_dict(summary)

    # ── acquisition ─────────────────────────────────────────────────────────

    async def analyze(self, message_id: str) -> dict[str, Any]:
        """Fetch ``format=raw``, decode strictly, and ingest through the pipeline.

        The selected message id is always resolved through the authenticated
        connection's own access token (``userId=me``); there is no cross-account
        path. Nothing is persisted when retrieval or decoding fails.
        """
        if not message_id:
            raise GmailMessageNotFoundError("A message id is required")
        access_token = await self._require_access_token()

        raw_message = await self.client.get_message_raw(access_token, message_id)
        if raw_message.size_estimate is not None and raw_message.size_estimate > self.config.max_raw_bytes:
            raise GmailTooLargeError(
                f"Message exceeds the {self.config.max_raw_bytes} byte acquisition cap"
            )
        raw_bytes = decode_gmail_raw(raw_message.raw_b64)
        if len(raw_bytes) > self.config.max_raw_bytes:
            raise GmailTooLargeError(
                f"Decoded message exceeds the {self.config.max_raw_bytes} byte acquisition cap"
            )
        # SHA-256 of the exact decoded bytes, before any parsing. The pipeline
        # derives the same hash internally from these same untouched bytes.
        sha256 = hashlib.sha256(raw_bytes).hexdigest()

        async with self._session() as db:
            existing = await self._find_existing(db, message_id, sha256)
            if existing is not None:
                raise GmailDuplicateError(
                    "This Gmail message was already analyzed as " + existing,
                    case_id=existing,
                )
            stored = await self._store_for(db).get_current()
            account = stored.account_email if stored is not None else ""
            acquired = GmailSource(
                message_id=raw_message.id or message_id,
                raw_bytes=raw_bytes,
                thread_id=raw_message.thread_id,
                internal_date_ms=raw_message.internal_date_ms,
                size_estimate=raw_message.size_estimate,
                account=account,
            ).acquire()
            try:
                result = await ingest_acquired_email(db, acquired)
            except UnparsableEmail as exc:
                raise GmailMalformedRawError(
                    "The acquired message could not be parsed as an email"
                ) from exc
            return result

    async def _find_existing(
        self, db: AsyncSession, message_id: str, sha256: str
    ) -> Optional[str]:
        """Return the TraceMail case id if this message was already ingested.

        Consistent with the audit's duplicate policy: refuse to re-acquire the
        same provider message id (matches on message id; the body hash is kept
        for provenance consistency).
        """
        result = await db.execute(
            select(SourceRecord).where(
                SourceRecord.source_type == "gmail",
                SourceRecord.source_id == message_id,
            )
        )
        source = result.scalars().first()
        if source is None:
            return None
        ev = await db.execute(
            select(EvidenceRecord).where(EvidenceRecord.source_id == source.id)
        )
        evidence = ev.scalars().first()
        return evidence.case_id if evidence is not None else None


def build_gmail_service(
    config: GmailConfig | None = None,
    client: GmailApiClient | None = None,
    oauth: OAuthProvider | None = None,
    token_store_factory: TokenStoreFactory | None = None,
    state_store: OAuthStateStore | None = None,
) -> GmailService:
    """Assemble a service with real defaults; tests inject fakes here."""
    config = config or load_config()
    if oauth is None:
        oauth = GoogleOAuthProvider(
            client_id=config.client_id,
            client_secret=config.client_secret,
            redirect_uri=config.redirect_uri,
            auth_endpoint=config.auth_endpoint,
            token_endpoint=config.token_endpoint,
            revoke_endpoint=config.revoke_endpoint,
            scopes=tuple(config.scopes),
        )
    if client is None:
        client = GmailHttpClient(
            api_base=config.gmail_api_base,
            retries=config.retries,
            retry_backoff=config.retry_backoff,
        )
    if token_store_factory is None:
        cipher = SecretCipher(encryption_key_from_env())

        def store_factory(db: AsyncSession) -> TokenStore:
            return SqlTokenStore(db, cipher)

        token_store_factory = store_factory
    return GmailService(
        config=config,
        client=client,
        oauth=oauth,
        token_store_factory=token_store_factory,
        state_store=state_store or OAuthStateStore(max_age_seconds=STATE_MAX_AGE_SECONDS),
    )