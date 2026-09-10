# Gmail Acquisition Architecture Design

**Status:** Architecture audit only — no application code, models, OAuth flow,
Google credentials, or secrets were created. This document is the design
baseline for Phase 3 (first direct mailbox acquisition source).

**Scope:** TraceMail connects a user's Gmail via OAuth, lets the analyst pick
one suspicious message, retrieves the **original raw RFC-822 representation**
from the provider, preserves it byte-for-byte as evidence, and feeds the
**existing** forensic pipeline. No mailbox contents other than the selected
message are ingested. Gmail message IDs carry provider provenance only; they
never prove sender authenticity.

---

## 1. Architecture

```
Browser (tracemail-app)
   │  Connect Gmail → Pick message → Analyze
   ▼
TraceMail backend (FastAPI, port 8000)
   ├─ OAuth endpoints      (start / callback / status / disconnect)
   ├─ Gmail picker endpoints (list / metadata / analyze-by-id)
   ├─ GmailSource adapter   (AcquiredEmail contract)     ← NEW
   ├─ Gmail API client      (read-only, "me" mailbox)     ← NEW
   └─ existing ingest_acquired_email()  (unchanged) ──► evidence engine
   ▼
Google Gmail API (users.messages, read-only scope) + Google OAuth endpoints
   ▼
Evidence DB ──► EvidenceRecord (raw bytes, sha256) ──► forensic analysis
```

The forensic engine (parser, identity/risk analysis, forensic records, report,
copilot, read APIs) consumes only the normalized `AcquiredEmail`. It never
depends on Gmail fields. Gmail specific concerns (OAuth, token storage,
client) live behind one `GmailSource` adapter and one read-only Gmail API
client.

Provider adapters remain additive:
`EMLSource (eml_upload) ─ current` │ `GmailSource (gmail) ─ Phase 3` │
`Microsoft365Source (microsoft365) ─ future`

## 2. OAuth flow

OAuth 2.0 **Authorization Code** flow with a confidential backend client.
The browser never sees the client secret and users are never asked for a
Gmail password.

```
Browser ── GET /api/gmail/auth/start ──► backend
   backend generates state (crypto-random, single-use, expiring)
   backend redirects browser ──► Google /o/oauth2/v2/auth
   (response_type=code, client_id, redirect_uri, scope, state [, PKCE])
Browser ── Google redirect ──► GET /api/gmail/oauth/callback?code&state
   backend validates state (constant-time, single-use, expiry)
   backend exchanges code ──► Google /oauth2/v2/token  (client_secret used only here)
   backend stores access + refresh token (server-side only, encrypted)
Browser ── backend redirects ──► /investigation?connect=success
```

- **Redirect architecture:** the callback must live on the backend origin that
  owns the client secret (`http://localhost:8000/api/gmail/oauth/callback` for
  dev). Google's redirect URI is registered and matched exactly. After success
  the backend redirects the browser to the frontend origin with only a success
  signal (`/investigation?connect=success`); no code, token, or ticket value is
  placed in the frontend URL. The frontend then polls a backend connect-status
  endpoint.
- **state/CSRF protection:** `state` is a fresh CSPRNG value bound to the
  originating browser (short-lived in-memory single-user store today; signed
  HTTP-only cookie/session once auth exists). It is verified with a
  constant-time comparison, is single-use, and expires (e.g. 10 min). PKCE is
  used even for the confidential client as defense-in-depth.
- **Token handling:** the authorization `code` is exchanged server-side
  immediately and never logged, never returned to the browser, and never stored
  as plaintext. Access tokens are used only in the `Authorization: Bearer`
  header toward Google's API.
- **Refresh-token requirements:** Gmail provides a long-lived refresh token
  (rotation behavior — verify; Google does not rotate on refresh by default).
  The refresh token is required to mint short-lived access tokens after the
  first hour. Without it, the user must re-authenticate after expiry.
- **Scopes (minimum):** `["https://www.googleapis.com/auth/gmail.readonly"]`
  is the only mail scope needed — reading headers, listing/searching, and
  fetching the raw message all require only `readonly`. No `modify`, `send`,
  `metadata`-only (insufficient for raw), or `compose` scope. `openid` and
  `email` are added **only** to obtain the account email address for
  provenance; if account identity is not required, these two can be dropped.
  See §Open questions for verification.
- **Disconnect / revoke:** `POST /api/gmail/revoke` calls
  `https://oauth2.googleapis.com/revoke` with the refresh token (best-effort,
  network-dependent) and deletes the stored token + connection rows. The UI
  exposes "Disconnect Gmail" in the picker and settings.
- **Authorization failures:** `invalid_grant` / revoked access never fall
  back to any fake or cached path — the UI is told the connection is severed
  and must re-connect.

## 3. Gmail acquisition flow

```
Connect (OAuth above)
   └─ picker: users.messages.list(q=<user query>, maxResults ≤ 50)
        │  returns only id / threadId / snippet (no bodies)
        ├─ per page: users.messages.get(format=metadata, metadataHeaders=From,Subject,Date)
        └─ rows: From · Subject · Date · snippet
   [Select] one row
   [Analyze with TraceMail]
        └─ users.messages.get(messages.get, format=raw)
             │ returns { id, ... , raw }  (raw = base64url RFC 822 message)
             └─ base64url-decode ─► bytes ─► AcquiredEmail.raw_bytes
```

- The picker **never downloads mailbox contents in bulk**: the list request
  returns provider-side results only (`q`, `maxResults`, `pageToken`), and only
  the analyst-selected message is retrieved as raw bytes.
- **Resource:** `users.messages` (Gmail REST API v1).
- **Retrieval method:** `GET ~/gmail/v1/users/{userId}/messages/{id}` with
  `userId=me` (the authorized mailbox; never a client-supplied account) and
  `format=raw`.
- **Required format:** `format=raw`. The response's `raw` field is the
  base64url-encoded RFC 822 representation of the message for byte-preserving
  capture. `format=full`/`minimal`/`metadata` are NOT used for evidence because
  they are reconstructed/partial and lose bytes.
- **Byte preservation:** `format=raw` + base64url decode is the only API form
  that yields a faithful RFC 822 octet stream. **Verification item:** confirm
  whether Gmail's `raw` output is byte-identical to the originally delivered
  wire message for all cases (Gmail-normalized or re-serialized sections are a
  risk). The system hashes exactly the bytes Gmail returned at acquisition time
  and records the acquisition context; it does not claim wire-exactness until
  verified.
- **Normalization/encoding:** decode with URL-safe base64
  (`base64.urlsafe_b64decode`) and pad to a multiple of 4 if Gmail omits
  padding (verify current padding behavior). No other normalization is applied
  — bytes are passed to the pipeline untouched.
- **SHA-256:** computed from the exact decoded `raw_bytes` **before** any
  parsing, matching the EML path (`parse_eml` hashes the original bytes). The
  hash is stored on `EvidenceRecord.sha256` and `Case.sha256`.
- **Filename/content-type:** Gmail has no original filename. Set
  `original_filename=""` (the column requires non-null string) and
  `content_type="message/rfc822"`. A deterministic display name like
  `gmail-<id>.eml` may be derived in the UI from source metadata, never stored
  as the "original filename".

## 4. Required EmailSource behavior

`GmailSource` must implement the existing protocol and produce the existing
`AcquiredEmail` dataclass. Nothing in the pipeline changes.

| Field | GmailSource value / behavior |
| --- | --- |
| `source_type` | `"gmail"` (stable; recorded on `Case`, `SourceRecord`, `UploadResponse`) |
| `source_identifier` | Provider message identifier = Gmail `message.id` (opaque provider id) |
| `original_filename` | `""` (Gmail has no source filename) |
| `content_type` | `"message/rfc822"` |
| `raw_bytes` | base64url-decoded bytes from `format=raw`; never normalized/rewritten |
| `acquisition_method` | `"gmail_oauth"` (canonical for this adapter) |
| `metadata` | Provider provenance only (see §5); never treated as instructions |
| `acquire()` | Async-lived: fetch → decode → return `AcquiredEmail`; raise typed acquisition errors (see §9) |

Notable contract gaps handled at acquisition time (documented only, contract
consumers unchanged):
- The current `EmailSource.acquire()` is sync; Gmail is network-bound, so the
  adapter will fetch bytes before calling `acquire()` (or the router will do
  the fetch) and hand the ready bytes in. Whether the contract evolves to an
  async `acquire()` is a Phase 3 implementation decision — the pipeline
  function signature does not change.
- `metadata` is free-form (`dict`) and JSON-serialized into
  `SourceRecord.provenance_json` — no model change required.

## 5. SourceRecord design

`SourceRecord` already exists and is filled from `AcquiredEmail` by
`ingest_acquired_email`. For Gmail:

| Column | Value |
| --- | --- |
| `source_type` | `"gmail"` |
| `source_id` | Gmail `message.id` (fits the existing `String(512)`) |
| `acquisition_timestamp` | `SourceRecord` default (ingest time) — this is the acquisition event time, distinct from Gmail `internalDate` (message date) |
| `acquisition_method` | `"gmail_oauth"` |
| `provenance_json` | `AcquiredEmail.metadata`, limited to: `provider="gmail"`, `account=<email>` (if token store knows it), `message_id`, `thread_id`, `internal_date_ms`, `size_estimate`, `raw_format="raw"` |

Do not store: search cursors, other messages' ids, snippets beyond the
selected message, label sets beyond what is needed for provenance, or any
credentials. The account email is the only personal-account identifier stored
and it exists to tie the acquisition to the authorized mailbox.

## 6. Evidence provenance

Chain recorded for every investigation:

```
Gmail message
   ↓  provider message identifier   = SourceRecord.source_id (message.id)
   ↓  acquisition event             = SourceRecord row (timestamp, method, metadata)
   ↓  raw bytes                     = format=raw → base64url decode
   ↓  SHA-256                        = hash of raw_bytes, pre-parse
   ↓  EvidenceRecord                 = original_bytes, sha256, size, status=preserved
   ↓  forensic analysis              = existing pipeline (unchanged)
```

- The **provider message ID is provenance, not authenticity.** It proves only
  "this object was stored by Gmail under this identifier at acquisition time".
  It does not authenticate the sender, the domain, or the content. Report and
  copilot already phrase attribution as "not established"; Gmail provenance
  additions must not introduce "this came from a real Gmail user so it is
  legitimate" or "the attacker is <account>" reasoning.
- The acquisition timestamp is TraceMail-side; `internalDate` (Gmail) may
  differ from the `Date:` header — provenance keeps them separate.
- Hash ties the preserved bytes to the acquisition: recomputing `sha256` from
  `EvidenceRecord.original_bytes` must always equal `EvidenceRecord.sha256`.

## 7. Security requirements

Gmail content is **untrusted data**. Production-required protections:

**OAuth / token layer**
- OAuth `state` (CSPRNG, single-use, expiring, constant-time check) + PKCE.
- Exact-match registered redirect URI; never accept arbitrary redirects.
- Client secret and refresh tokens exist only server-side; no secret is ever
  in the frontend bundle, logs, URLs, or API responses.
- Access tokens: bearer-only toward Gmail, never persisted in plaintext in
  logs/database, never presented back to the browser.
- Refresh tokens: encrypted at rest (AES-256-GCM with a key from env/KMS),
  stored in a dedicated table, destroyed on disconnect/revoke.
- Authorization failures are terminal (re-connect required), never degraded to
  cached/fabricated content.

**Mailbox authorization**
- `userId=me` only; the backend resolves the authorized mailbox itself.
- A client-supplied message id is always read through the connection's own
  token; Gmail enforces the mailbox boundary, and TraceMail never re-targets a
  different account.
- No cross-account read endpoint; token store is keyed by account.

**Evidence / content safety**
- Malicious email HTML: Evidence/header views render text and metadata only;
  no raw-HTML preview, no `<iframe>` body embed, no remote images. Any future
  preview must sanitize and run in a sandboxed, network-off context.
- Malicious URLs: extracted as IOCs, never fetched by the backend (no SSRF);
  any future enrichment goes through an allowlisted, async egress guard.
- Oversized messages: enforce a hard byte cap (e.g. 25 MB of decoded raw bytes;
  check `sizeEstimate` before download) and refuse rather than truncate.
- Malformed MIME: `parse_eml` errors map to `UnparsableEmail` → a clean
  acquisition failure; no ingest crash, payloads never executed.
- Attachment metadata: metadata + hashes only (existing attachment semantics);
  filenames are display strings only (no path usage).
- Prompt injection: bodies/headers are data, never concatenated into prompts
  or treated as instructions; report/copilot consume structured fields
  (copilot remains rule-based, no LLM).
- Cross-case evidence leakage: the Phase 2 evidence query layer is already
  case-scoped; Gmail metadata is per-case on `SourceRecord`; nothing exposes
  other cases or other accounts.

## 8. Privacy / data minimization

- Minimum scopes: `gmail.readonly` (+ `openid email` only if account identity
  is needed for provenance; verifiable and droppable).
- Retrieve only the analyst-selected message; picker paging returns metadata
  headers/snippets, never bodies.
- No mailbox contents unrelated to an investigation are stored: list results
  are transient; the only persisted Gmail-derived content is the selected
  message's raw bytes + its provenance fields.
- Credential minimization: only one refresh token + one access token per
  connection, encrypted; nothing else.
- Disconnect Gmail: revoke token (best-effort) + delete stored connection and
  token rows.
- Provider metadata associated with `SourceRecord` per §5; retention of the
  selected evidence follows the existing evidence lifecycle.

## 9. Failure handling

Explicit, no fake fallback. Each maps to a typed acquisition error surfaced as
a clear API response and (where recoverable) retried with bounded backoff.

| Case | Behavior |
| --- | --- |
| OAuth denied (user) | `access_denied` → "You denied access"; do not re-prompt automatically |
| OAuth cancelled | user left Google → no tokens stored; picker returns to idle |
| Expired token | refresh via refresh token; if refresh fails → re-connect |
| Revoked access | `invalid_grant`/401 → connection marked severed; UI re-connect; no cached data |
| Message deleted after selection | `messages.get` 404 → "Message is no longer available" |
| Message unavailable | same 404/`failedPrecondition` path → no partial ingestion |
| API rate limit | 429 → bounded retry + backoff, failed requests categorized; no queue fabrication |
| Gmail API failure | transport/5xx → typed error; nothing persisted; case not created |
| Malformed raw message | decode fails or `UnparsableEmail` → 422-style acquisition error |
| Oversized message | `sizeEstimate`/decoded size > cap → refuse; do not truncate |
| Duplicate acquisition | select-time check by `SourceRecord.source_id` (message id) + sha256 → warn "already analyzed" (see §12 decision) |

## 10. Pipeline compatibility

- `GmailSource → AcquiredEmail → ingest_acquired_email()` works **without any
  change to the forensic engine**, the parser, the models, or the read APIs.
  `ingest_acquired_email` is already source-agnostic and derives
  `SourceRecord`/`EvidenceRecord` from the `AcquiredEmail` fields above.
- **Minimum changes required:**
  1. `GmailSource` adapter (implements the existing contract).
  2. Read-only Gmail API client (list/metadata/raw) with a network-scoped
     interface for testing.
  3. OAuth endpoints (`start`, `callback`, `connect/status`, `revoke`) +
     encrypted token store service.
  4. Picker/analyze endpoints (`list`, `analyze`: fetch raw → `GmailSource`
     → `ingest_acquired_email`).
  5. Frontend "Connect Gmail / pick / analyze" in the New Investigation
     branch of `tracemail-app`.
- No schema change is required for v1 (all fields exist). If duplicate-acquisition
  "already ingested" must be enforced database-side, a unique index on
  `SourceRecord(source_type, source_id, sha256)` is the one candidate model
  change — deferred to implementation review.
- The existing `.eml` upload path is untouched.

## 11. Testing strategy

Deterministic — no real Gmail account. Pattern: an async `GmailApiClient`
protocol; a `FakeGmailClient` in tests returns canned messages/metadata and
raises typed errors (message-not-found, oversize, rate-limit,
revoked/expired). A fake token-store + stubbed OAuth token endpoint cover the
authorization code exchange.

Coverage:
- Successful acquisition: `GmailSource` output has `source_type="gmail"`,
  provider `message_id`, `acquisition_method="gmail_oauth"`,
  `content_type="message/rfc822"`.
- Raw-byte preservation: acquired bytes equal the fixture the fake returns
  (base64url-encoded → decoded), and `EvidenceRecord.original_bytes` equals
  them byte-for-byte.
- SHA-256: equals `hashlib.sha256(raw_bytes).hexdigest()` on the evidence row.
- OAuth state: valid state accepted, tampered/reused/expired state rejected,
  constant-time path exercised.
- Token failures: expired access → refresh attempted; revoked → re-connect.
- Message not found; oversized; malformed→`UnparsableEmail`; rate-limited.
- Duplicate acquisition behavior per chosen policy.
- Pipeline parity: a `forensic_mixed.eml`-derived fixture fed through the fake
  Gmail path produces identical forensic records/IOC/attachments as the EML path.
- Case-scoping: another case/account cannot read this case's Gmail provenance.

Tests extend `backend/tests/` (standard-library `unittest`, existing style),
require no network, and can reuse the `forensic_mixed.eml` fixture bytes.

## 12. Minimum implementation plan

1. **Gmail API client** (protocol + minimal REST client; `me` mailbox;
   `list`/`metadata`/`raw`) with typed errors. Tests: fake client.
2. **Token store service** (encrypted refresh/access tokens keyed by account;
   env-based AES key). Tests: encrypt/decrypt, destroy-on-revoke.
3. **OAuth endpoints** (`start`, `callback`, `status`, `revoke`; state store,
   PKCE, code exchange). Tests via stubbed token endpoint + fake client.
4. **GmailSource adapter** mapping raw bytes to `AcquiredEmail` (§4). Tests:
   base64url decoding, sha256, fields.
5. **Analyze endpoint** (`analyze-by-message-id`): fetch → `GmailSource`
   → `ingest_acquired_email`; picker `list`/`metadata` endpoints. Tests:
   end-to-end fake-provider ingest; failure matrix (§9).
6. **Frontend picker** (Connect Gmail → search/paged metadata rows → select →
   Analyze). Reuses existing New Investigation + Evidence UI; no mock fallback.
7. **Security pass + full test run** (backend suite, `npm run build`, mocks
   grep) and documentation update.
8. **Out-of-scope in this milestone:** Microsoft 365, header-paste, LLM/router,
   blockchain/WORM, background jobs, production infrastructure.

## 13. Open questions (mark for verification)

- Does Gmail `format=raw` return bytes **byte-identical** to the originally
  delivered wire message in all cases (missing/rewritten headers, re-encoded
  sections)? Verified against a controlled account before claiming
  wire-exactness.
- Precisely how Gmail pads (`=`) its base64url `raw` field today; confirm the
  decode routine tolerates both padded and unpadded forms.
- Does the selected OAuth app type (confidential web) with `gmail.readonly`
  require the Gmail API to be enabled + a consent screen with app
  verification/testing status? (Dev: "Test" user set; production: verification.)
- Refresh-token rotation/expiry behavior for Gmail (e.g., revoke on password
  change, re-auth policy).
- Whether `internalDate` is reliable as a "first received" timestamp and how it
  relates to the `Date:` header for display.
- `OpenID: openid email` — confirm this is the lightest way to get the account
  email for provenance, and whether it can be omitted cleanly.
- Gmail size limits: default stored-message cap and whether `sizeEstimate`
  approximates the `raw` (base64url) size or the decoded size; set the refusal
  cap accordingly.
- Concurrency: sync `EmailSource.acquire()` vs async fetch — decide before
  implementing (affects only the adapter, not the pipeline).
- Duplicate-acquisition policy: refuse-by-message-id (needs the deferred unique
  index) vs per-acquisition new case vs warn-dedupe at the picker.

## 14. Risks

- **Byte-fidelity assumption:** if Gmail's `raw` is not wire-identical,
  forensic hash values differ from the sender's original message. Mitigation:
  document provenance as "bytes as returned by Gmail at acquisition time" and
  never claim wire-exactness until verified.
- **Token security:** refresh-token exposure would grant mailbox read access.
  Mitigation: server-only, encrypted at rest, revoke/disconnect, no logging.
- **Phishing of the analyst:** a malicious email's HTML/URLs are never auto
  rendered or fetched. The picker shows only metadata; Evidence is
  text/meta-based.
- **Over-consuming the mailbox:** unbounded search is capped and paged; only
  the selected message is retrieved.
- **Scope creep:** Microsoft 365/header-paste/LLM/blockchain/worm stay out.

---

*End of architecture audit.* No application code or models were modified.