"""Gmail acquisition tests (Phase 3).

Deterministic — no real Google account. A ``FakeGmailClient`` serves canned
messages/metadata and raises typed errors; token/OAuth behavior is injected via
fake stores/providers. Pipeline parity: the exact bytes of
``forensic_mixed.eml`` are served through the fake ``format=raw`` path and must
produce the same forensic records as the EML path.
"""
import asyncio
import base64
import hashlib
import sqlite3
import sys
import unittest
from pathlib import Path

from .isolation import set_test_database_env, test_db_path, teardown_database


class FakeGmailClient:
    """Canned Gmail provider with typed failure injection."""

    def __init__(self, messages=None, account="analyst@example.test"):
        from services.gmail.client import GmailMessageSummary, GmailProfile
        from services.gmail.errors import GmailMessageNotFoundError

        self.account = account
        self.messages = dict(messages or {})  # id -> raw bytes
        self.summaries = {}
        for msg_id, _raw in self.messages.items():
            self.summaries[msg_id] = GmailMessageSummary(
                id=msg_id,
                thread_id=msg_id,
                snippet=f"snippet for {msg_id}",
                from_address="sender@evil-quest.example.net",
                subject=f"Subject {msg_id}",
                date="Wed, 01 Jan 2025 09:00:00 -0000",
                internal_date_ms=1735707600000,
                size_estimate=len(_raw),
            )
        self.size_overrides = {}       # id -> int
        self.raw_b64_overrides = {}    # id -> str (raw field)
        self.raw_errors = {}           # id -> Exception
        self.global_error = None
        self.profile_calls = 0
        self.raw_calls = []
        self.NotFound = GmailMessageNotFoundError

    async def list_messages(self, access_token, query="", page_token=None, max_results=10):
        ids = [i for i in self.messages if not query or query in i][:max_results]
        return [self.summaries[i] for i in ids], ("tok-page-2" if False else None), len(self.messages)

    async def get_message_summary(self, access_token, message_id):
        if self.global_error is not None:
            raise self.global_error
        if message_id not in self.summaries:
            raise self.NotFound(f"The selected message is no longer available")
        return self.summaries[message_id]

    async def get_message_raw(self, access_token, message_id):
        self.raw_calls.append(message_id)
        if self.global_error is not None:
            raise self.global_error
        if message_id in self.raw_errors:
            raise self.raw_errors[message_id]
        if message_id not in self.messages:
            raise self.NotFound("The selected message is no longer available")
        raw_b64 = self.raw_b64_overrides.get(message_id)
        if raw_b64 is None:
            raw_b64 = base64.urlsafe_b64encode(self.messages[message_id]).decode("ascii").rstrip("=")
        from services.gmail.client import GmailRawMessage
        return GmailRawMessage(
            id=message_id,
            thread_id=message_id,
            raw_b64=raw_b64,
            internal_date_ms=1735707600000,
            size_estimate=self.size_overrides.get(message_id, len(self.messages[message_id])),
        )

    async def get_profile(self, access_token):
        self.profile_calls += 1
        from services.gmail.client import GmailProfile
        return GmailProfile(email_address=self.account)


class FakeOAuthProvider:
    def __init__(self, auth_url="https://accounts.google.com/o/oauth2/v2/auth?resp=1"):
        from services.gmail.oauth import ExchangedTokens

        self.auth_url = auth_url
        self.exchange_calls = 0
        self.refresh_calls = 0
        self.revoke_calls = 0
        self.exchange_result = ExchangedTokens(
            access_token="exchanged-access", refresh_token="refresh-token-1",
            expires_in=3600, scope="https://www.googleapis.com/auth/gmail.readonly openid",
        )
        self.refresh_result = ExchangedTokens(
            access_token="refreshed-access", refresh_token="refresh-token-1",
            expires_in=3600, scope="https://www.googleapis.com/auth/gmail.readonly",
        )

    def build_auth_url(self, state, code_verifier):
        return f"{self.auth_url}&state={state}&challenge={hashlib.sha256(code_verifier.encode()).hexdigest()[:8]}"

    async def exchange_code(self, code, code_verifier):
        self.exchange_calls += 1
        return self.exchange_result

    async def refresh_access(self, refresh_token):
        self.refresh_calls += 1
        return self.refresh_result

    async def revoke(self, refresh_token):
        self.revoke_calls += 1


class FakeTokenStore:
    def __init__(self, status="valid", access="access-token-1", refresh="refresh-token-1",
                 account="analyst@example.test", expires_at=None):
        self.status = status
        self.access = access
        self.refresh = refresh
        self.account = account
        self.expires_at = expires_at
        self.saved = []

    async def save_connection(self, **kw):
        self.saved.append(kw)
        self.access = kw.get("access_token", self.access)
        self.refresh = kw.get("refresh_token", self.refresh)
        self.account = kw.get("account_email", self.account)
        self.expires_at = kw.get("expires_at", self.expires_at)
        self.status = "valid"

    async def get_current(self, now=None):
        self.now = now
        if self.status == "missing":
            return None
        from services.gmail.token_store import CredentialStatus, StoredConnection
        return StoredConnection(
            connection_id="conn-test",
            account_email=self.account,
            access_token=self.access,
            refresh_token=self.refresh,
            expires_at=self.expires_at,
            status=self.status or CredentialStatus.VALID,
        )

    async def mark_revoked(self, now=None):
        self.status = "revoked"

    async def delete_all(self):
        self.status = "missing"
        self.saved.clear()


class GmailAcquisitionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        set_test_database_env()

        from fastapi.testclient import TestClient
        from main import app
        from routers.gmail import get_gmail_service
        from services.gmail.acquisition import build_gmail_service
        from services.gmail.config import GmailConfig
        from services.gmail.oauth import OAuthStateStore
        from services.gmail.token_store import SecretCipher

        cls.app = app
        cls.get_gmail_service = get_gmail_service
        cls.client = TestClient(app, follow_redirects=False)
        cls.client.__enter__()

        cls.cipher = SecretCipher(bytes(range(32)))
        cls.fixture = Path(__file__).parent / "fixtures" / "forensic_mixed.eml"
        cls.parity_raw = cls.fixture.read_bytes()
        cls.config = GmailConfig(
            client_id="test-client-id", client_secret="test-secret",
            redirect_uri="http://localhost:8000/api/gmail/oauth/callback",
            frontend_origin="http://localhost:5173",
        )

        cls.fake_client = FakeGmailClient(
            messages={
                "msg-parity": cls.parity_raw,
                "msg-pipeline": cls.parity_raw,
                "msg-success": cls.parity_raw,
                "msg-scoping": cls.parity_raw,
            }
        )
        cls.fake_oauth = FakeOAuthProvider()
        from services.gmail.token_store import SqlTokenStore
        cls.service = build_gmail_service(
            config=cls.config,
            client=cls.fake_client,
            oauth=cls.fake_oauth,
            token_store_factory=lambda db: SqlTokenStore(db, cls.cipher),
            state_store=OAuthStateStore(),
        )

        def override():
            return cls.service

        app.dependency_overrides[get_gmail_service] = override

        cls._seed_via_callback()

    @classmethod
    def _seed_via_callback(cls):
        """Persist a connected, encrypted connection through the real callback
        path so tokens are stored by the same event loop the TestClient uses."""
        state, _verifier = cls.service.state_store.create()
        response = cls.client.get(
            f"/api/gmail/oauth/callback?state={state}&code=seed-code"
        )
        assert response.status_code == 303, response.text
        assert response.headers["location"].endswith("?connect=success")

    @classmethod
    def tearDownClass(cls):
        cls.app.dependency_overrides.pop(cls.get_gmail_service, None)
        cls.client.__exit__(None, None, None)
        teardown_database()

    def _db(self):
        return sqlite3.connect(test_db_path())

    # ── A–F: successful acquisition ─────────────────────────────────────────

    def test_successful_raw_acquisition_fields_and_provenance(self):
        response = self.client.post("/api/gmail/analyze", json={"message_id": "msg-success"})
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["source_type"], "gmail")            # B
        self.assertNotEqual(payload["case_id"], "case-999999")
        self.assertTrue(payload["evidence_id"])

        case_id = payload["case_id"]
        evidence_id = payload["evidence_id"]

        db = self._db()
        source = db.execute(
            "SELECT s.source_type, s.source_id, s.acquisition_method, s.provenance_json "
            "FROM sources s JOIN evidence_records e ON e.source_id = s.id WHERE e.id = ?",
            (evidence_id,),
        ).fetchone()
        self.assertIsNotNone(source, "no source row joined to evidence")
        self.assertEqual(source[0], "gmail")
        self.assertEqual(source[1], "msg-success")                    # C message-id provenance
        self.assertEqual(source[2], "gmail_oauth")

        prov = source[3]
        for key in ["provider", "account", "message_id", "thread_id", "internal_date_ms", "size_estimate", "raw_format", "sha256", "acquisition_note"]:
            self.assertIn(key, prov, key)
        self.assertIn('"raw_format": "raw"', prov)
        self.assertIn("SHA-256 of bytes returned by Gmail format=raw", prov)

        evidence = db.execute(
            "SELECT sha256, size, original_bytes, content_type, original_filename FROM evidence_records WHERE id = ?",
            (evidence_id,),
        ).fetchone()
        self.assertEqual(evidence[0], hashlib.sha256(self.parity_raw).hexdigest())  # E
        self.assertEqual(evidence[1], len(self.parity_raw))
        self.assertEqual(evidence[2], self.parity_raw)                 # D exact bytes
        self.assertEqual(evidence[3], "message/rfc822")
        self.assertEqual(evidence[4], "")                              # B original_filename = ""
        db.close()

        summary = self.client.get(f"/api/cases/{case_id}/forensic-summary").json()
        self.assertEqual(summary["source_type"], "gmail")
        self.assertEqual(summary["source_identifier"], "msg-parity")
        self.assertEqual(summary["acquisition_method"], "gmail_oauth")
        self.assertEqual(summary["sha256"], hashlib.sha256(self.parity_raw).hexdigest())
        self.assertEqual(summary["size"], len(self.parity_raw))

    # ── T: pipeline parity ──────────────────────────────────────────────────

    def test_pipeline_parity_with_eml_fixture(self):
        response = self.client.post("/api/gmail/analyze", json={"message_id": "msg-pipeline"})
        self.assertEqual(response.status_code, 200, response.text)
        case_id = response.json()["case_id"]
        db = self._db()
        evidence_id = db.execute(
            "SELECT id FROM evidence_records WHERE case_id = ?", (case_id,)
        ).fetchone()[0]

        mime_parts = db.execute(
            "SELECT part_index, parent_index, depth, content_type, is_attachment FROM mime_parts "
            "WHERE evidence_id = ? ORDER BY part_index", (evidence_id,),
        ).fetchall()
        self.assertEqual(len(mime_parts), 5)
        self.assertEqual(mime_parts[0][3], "multipart/mixed")
        self.assertEqual([p[3] for p in mime_parts[1:]], ["text/plain", "text/html", "application/pdf", "text/csv"])

        hops = db.execute(
            "SELECT sequence, source_ip, protocol FROM received_hops WHERE evidence_id = ? ORDER BY sequence",
            (evidence_id,),
        ).fetchall()
        self.assertEqual(
            [(h[0], h[1], h[2]) for h in hops],
            [(1, "192.0.2.8", "ESMTPS"), (2, "192.0.2.7", "SMTP")],
        )

        atts = db.execute(
            "SELECT filename, mime_type, sha256 FROM attachments WHERE evidence_id = ? ORDER BY filename",
            (evidence_id,),
        ).fetchall()
        self.assertEqual(len(atts), 2)
        self.assertEqual(
            atts[0],
            ("invoice.pdf", "application/pdf", "56cd7a52d4dbc4af2f1e64a46b7fd199a4ec569b6dd86c20cd74b1bad746f5c1"),
        )
        self.assertEqual(
            atts[1],
            ("ledger.csv", "text/csv", "67506524668ef4b99583991cfee26b76363c9940a7969f18712f6fe3e42b79a2"),
        )

        iocs = db.execute("SELECT ioc_type, value FROM iocs WHERE evidence_id = ?", (evidence_id,)).fetchall()
        ioc_set = set((t, v) for t, v in iocs)
        for expected in [
            ("url", "http://evil-quest.example.net/pay"),
            ("email", "refund@paid-login.example.net"),
            ("domain", "paid-login.example.net"),
            ("domain", "evil-quest.example.net"),
            ("ip", "192.0.2.7"),
            ("ip", "192.0.2.8"),
        ]:
            self.assertIn(expected, ioc_set)
        db.close()

        # The gmail-derived case reads through the same read APIs.
        parts = self.client.get(f"/api/cases/{case_id}/mime-parts").json()
        self.assertEqual(len(parts), 5)
        hops_resp = self.client.get(f"/api/cases/{case_id}/transit-hops").json()["hops"]
        self.assertEqual([h["source_ip"] for h in hops_resp], ["192.0.2.8", "192.0.2.7"])

    # ── R: duplicate acquisition ────────────────────────────────────────────

    def test_duplicate_acquisition_is_refused(self):
        first = self.client.post("/api/gmail/analyze", json={"message_id": "msg-parity"})
        self.assertEqual(first.status_code, 200, first.text)
        first_case = first.json()["case_id"]
        second = self.client.post("/api/gmail/analyze", json={"message_id": "msg-parity"})
        self.assertEqual(second.status_code, 409, second.text)
        self.assertIn(first_case, second.json()["detail"])
        self.assertEqual(self.client.get("/api/gmail/analyze").status_code, 405)

    # ── M: message not found ────────────────────────────────────────────────

    def test_message_not_found(self):
        response = self.client.post("/api/gmail/analyze", json={"message_id": "msg-gone"})
        self.assertEqual(response.status_code, 404)
        self.assertIn("no longer available", response.json()["detail"])

    # ── N: oversized message ────────────────────────────────────────────────

    def test_oversized_message_precheck_refuses(self):
        self.fake_client.size_overrides["msg-parity"] = 30 * 1024 * 1024  # > 25 MB cap
        response = self.client.post("/api/gmail/analyze", json={"message_id": "msg-parity"})
        self.assertEqual(response.status_code, 413, response.text)
        self.assertIn("cap", response.json()["detail"].lower())
        del self.fake_client.size_overrides["msg-parity"]

    def test_decoded_size_cap_never_truncates(self):
        from services.gmail.acquisition import build_gmail_service
        from services.gmail.config import GmailConfig
        from services.gmail.errors import GmailTooLargeError

        tiny_raw = b"From: a@b\nTo: c@d\nSubject: x\n\n" + (b"y" * 500)
        client = FakeGmailClient(messages={"big": tiny_raw}, account="a@example.test")
        service = build_gmail_service(
            config=GmailConfig(max_raw_bytes=100),
            client=client,
            oauth=self.fake_oauth,
            token_store_factory=lambda db: FakeTokenStore("valid"),
        )
        with self.assertRaises(GmailTooLargeError):
            asyncio.run(service.analyze("big"))

    # ── O: malformed raw message ────────────────────────────────────────────

    def test_malformed_raw_base64_refused(self):
        self.fake_client.raw_b64_overrides["msg-parity"] = "!!!not-base64!!!"
        response = self.client.post("/api/gmail/analyze", json={"message_id": "msg-parity"})
        self.assertEqual(response.status_code, 422, response.text)
        self.assertIn("base64", response.json()["detail"].lower())
        del self.fake_client.raw_b64_overrides["msg-parity"]

    def test_unparsable_raw_message_refused(self):
        # ``parse_eml`` is intentionally lenient (it accepts any byte stream), so
        # the malformed-raw path is exercised by injecting the real pipeline
        # failure the acquisition service is required to map to 422.
        from unittest import mock

        import services.gmail.acquisition as acquisition_mod
        from services.gmail.errors import GmailMalformedRawError
        from services.ingest_email import UnparsableEmail

        self.fake_client.messages["msg-unparsable"] = self.parity_raw
        try:
            with mock.patch.object(
                acquisition_mod, "ingest_acquired_email",
                side_effect=UnparsableEmail("The acquired message could not be parsed"),
            ):
                with self.assertRaises(Exception) as ctx:
                    asyncio.run(self.service.analyze("msg-unparsable"))
                self.assertIsInstance(ctx.exception, GmailMalformedRawError)
                response = self.client.post(
                    "/api/gmail/analyze", json={"message_id": "msg-unparsable"}
                )
                self.assertEqual(response.status_code, 422, response.text)
                self.assertIn("could not be parsed", response.json()["detail"].lower())
        finally:
            del self.fake_client.messages["msg-unparsable"]

    # ── P/Q: rate limit / provider 5xx ──────────────────────────────────────

    def test_rate_limit_is_surfaced(self):
        from services.gmail.errors import GmailRateLimitError
        self.fake_client.raw_errors["msg-parity"] = GmailRateLimitError("Gmail is rate-limiting requests")
        response = self.client.post("/api/gmail/analyze", json={"message_id": "msg-parity"})
        self.assertEqual(response.status_code, 429, response.text)
        del self.fake_client.raw_errors["msg-parity"]

    def test_provider_server_error_is_surfaced(self):
        from services.gmail.errors import GmailServerError
        self.fake_client.raw_errors["msg-parity"] = GmailServerError("Gmail API server error (500)")
        response = self.client.post("/api/gmail/analyze", json={"message_id": "msg-parity"})
        self.assertEqual(response.status_code, 502, response.text)
        del self.fake_client.raw_errors["msg-parity"]

    # ── G–J: OAuth state handling ───────────────────────────────────────────

    def test_oauth_state_store_valid_tampered_reused_expired(self):
        from services.gmail.errors import (
            GmailStateExpiredError, GmailStateInvalidError, GmailStateReusedError,
        )
        from services.gmail.oauth import OAuthStateStore

        store = OAuthStateStore(max_age_seconds=600, now=lambda: 1000.0)
        state, verifier = store.create()
        self.assertEqual(store.consume(state), verifier)          # G valid

        with self.assertRaises(GmailStateReusedError):
            store.consume(state)                                  # I reused

        state2, _ = store.create()
        with self.assertRaises(GmailStateInvalidError):
            store.consume(state2 + "x")                           # H tampered

        clock = {"now": 1000.0}
        store2 = OAuthStateStore(max_age_seconds=600, now=lambda: clock["now"])
        s3, _ = store2.create()
        clock["now"] = 1000.0 + 601.0
        with self.assertRaises(GmailStateExpiredError):
            store2.consume(s3)                                    # J expired

    def test_oauth_callback_success_redirects_and_persists_encrypted_tokens(self):
        fake_oauth_calls_before = self.fake_oauth.exchange_calls
        state, _verifier = self.service.state_store.create()
        response = self.client.get(
            f"/api/gmail/oauth/callback?state={state}&code=server-side-code"
        )
        self.assertEqual(response.status_code, 303, response.text)
        self.assertEqual(response.headers["location"], "http://localhost:5173/investigation?connect=success")
        self.assertEqual(self.fake_oauth.exchange_calls, fake_oauth_calls_before + 1)

        db = self._db()
        row = db.execute("SELECT account_email, refresh_token_enc, access_token_enc FROM gmail_connections").fetchall()
        self.assertTrue(row)
        account, refresh_enc, access_enc = row[-1]
        self.assertEqual(account, "analyst@example.test")
        self.assertNotIn("exchanged-access", refresh_enc)
        self.assertNotIn("exchanged-access", access_enc)  # plaintext never persisted
        self.assertIn("v1:", refresh_enc)
        db.close()

    def test_oauth_callback_tampered_state_redirects_invalid(self):
        state, _verifier = self.service.state_store.create()
        before = self.fake_oauth.exchange_calls
        response = self.client.get(
            f"/api/gmail/oauth/callback?state={state}tampered&code=bad"
        )
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.headers["location"], "http://localhost:5173/investigation?connect=invalid")
        self.assertEqual(self.fake_oauth.exchange_calls, before)  # no code exchange

    def test_oauth_callback_reused_state_redirects_invalid(self):
        state, _verifier = self.service.state_store.create()
        ok = self.client.get(f"/api/gmail/oauth/callback?state={state}&code=one")
        self.assertEqual(ok.headers["location"], "http://localhost:5173/investigation?connect=success")
        reused = self.client.get(f"/api/gmail/oauth/callback?state={state}&code=two")
        self.assertEqual(reused.headers["location"], "http://localhost:5173/investigation?connect=invalid")

    def test_oauth_callback_expired_state_redirects_expired(self):
        state, _verifier = self.service.state_store.create()
        self.service.state_store._pending[state]["created_at"] -= 601.0
        response = self.client.get(f"/api/gmail/oauth/callback?state={state}&code=late")
        self.assertEqual(response.headers["location"], "http://localhost:5173/investigation?connect=expired")

    def test_oauth_callback_denied_redirects_denied(self):
        response = self.client.get("/api/gmail/oauth/callback?error=access_denied")
        self.assertEqual(response.headers["location"], "http://localhost:5173/investigation?connect=denied")

    # ── K: access-token expiry → refresh ────────────────────────────────────

    def test_expired_access_token_triggers_refresh(self):
        from services.gmail.acquisition import build_gmail_service

        client = FakeGmailClient(messages={"m1": self.parity_raw})
        oauth = FakeOAuthProvider()
        store = FakeTokenStore(status="expired", access="old-access", refresh="refresh-token-1")
        service = build_gmail_service(
            config=self.config, client=client, oauth=oauth,
            token_store_factory=lambda db: store,
        )
        token = asyncio.run(service._require_access_token())
        self.assertEqual(token, "refreshed-access")
        self.assertEqual(oauth.refresh_calls, 1)
        self.assertEqual(store.saved[-1]["access_token"], "refreshed-access")

    # ── L: revoked credential → reconnect required ───────────────────────

    def test_revoked_connection_requires_reconnect(self):
        from services.gmail.acquisition import build_gmail_service

        client = FakeGmailClient(messages={"m1": self.parity_raw})
        oauth = FakeOAuthProvider()
        store = FakeTokenStore(status="revoked")
        service = build_gmail_service(
            config=self.config, client=client, oauth=oauth,
            token_store_factory=lambda db: store,
        )
        with self.assertRaises(Exception) as ctx:
            asyncio.run(service._require_access_token())
        from services.gmail.errors import GmailAuthError
        self.assertIsInstance(ctx.exception, GmailAuthError)

        status = asyncio.run(service.status())
        self.assertFalse(status["connected"])
        self.assertEqual(status["status"], "revoked")

    def test_missing_connection_returns_connected_false(self):
        from services.gmail.acquisition import build_gmail_service
        service = build_gmail_service(
            config=self.config, client=self.fake_client, oauth=self.fake_oauth,
            token_store_factory=lambda db: FakeTokenStore(status="missing"),
        )
        status = asyncio.run(service.status())
        self.assertFalse(status["connected"])
        self.assertEqual(status["status"], "missing")

    # ── S: case-scoping ─────────────────────────────────────────────────────

    def test_case_scoping_between_sources(self):
        gmail_resp = self.client.post("/api/gmail/analyze", json={"message_id": "msg-scoping"})
        self.assertEqual(gmail_resp.status_code, 200, gmail_resp.text)
        gmail_case = gmail_resp.json()["case_id"]

        eml_raw = (Path(__file__).parent / "fixtures" / "valid.eml").read_bytes()
        eml_resp = self.client.post(
            "/api/cases/upload",
            files={"file": ("valid.eml", eml_raw, "message/rfc822")},
        )
        self.assertEqual(eml_resp.status_code, 200, eml_resp.text)
        eml_case = eml_resp.json()["case_id"]

        gmail_summary = self.client.get(f"/api/cases/{gmail_case}/forensic-summary").json()
        eml_summary = self.client.get(f"/api/cases/{eml_case}/forensic-summary").json()
        self.assertEqual(gmail_summary["source_type"], "gmail")
        self.assertEqual(gmail_summary["source_identifier"], "msg-scoping")
        self.assertEqual(eml_summary["source_type"], "eml_upload")
        self.assertNotEqual(eml_summary["evidence_id"], gmail_summary["evidence_id"])

        # The EML case must not see the gmail provenance or its attachments.
        self.assertNotIn("msg-scoping", self.client.get(f"/api/cases/{eml_case}/forensic-summary").json()["source_identifier"])
        eml_attachments = self.client.get(f"/api/cases/{eml_case}/attachments").json()
        self.assertEqual(eml_attachments, [])

    # ── picker endpoints (metadata only, bounded) ───────────────────────────

    def test_search_returns_metadata_only(self):
        response = self.client.get("/api/gmail/search", params={"q": "parity"})
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual(len(data["messages"]), 1)
        msg = data["messages"][0]
        self.assertEqual(msg["id"], "msg-parity")
        for key in ["subject", "from_address", "date", "snippet"]:
            self.assertNotEqual(msg.get(key, ""), "")
        self.assertNotIn("raw", msg)
        self.assertNotIn("body", msg)
        self.assertNotIn("payload", msg)

    def test_message_metadata_endpoint(self):
        response = self.client.get("/api/gmail/messages/msg-parity/metadata")
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual(data["id"], "msg-parity")
        self.assertIn("subject", data)
        self.assertNotIn("raw", data)

    def test_revoke_deletes_server_credentials(self):
        self.client.post("/api/gmail/revoke")
        db = self._db()
        rows = db.execute("SELECT COUNT(*) FROM gmail_connections").fetchone()[0]
        self.assertEqual(rows, 0)
        db.close()
        status = self.client.get("/api/gmail/status").json()
        self.assertFalse(status["connected"])
        self.assertEqual(status["status"], "missing")
        self._seed_via_callback()  # restore for subsequent tests


if __name__ == "__main__":
    unittest.main()