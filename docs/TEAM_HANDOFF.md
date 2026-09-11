# TraceMail — Team Handoff / Continuation Document

**Written for a developer who has NOT followed the prior session.**
**Date:** 2026-09-11
**Status:** This is a *checkpoint* document. It describes verified repository state and the exact remaining work. It is NOT an implementation plan to execute blindly — see [Section 16 — Handoff Rule](#16-handoff-rule).

All claims in this document were verified by reading the repository and running the documented commands. Nothing here was invented; where a claim could not be verified it is marked **UNVERIFIED** or **DEFERRED** (see [Section 13](#13-known-risks--open-questions)).

---

## 1 — Project Identity

| Item | Value (verified) |
| --- | --- |
| Project name | **TraceMail** (TraceMail AI) |
| SIH problem statement | **SIH26106** |
| Problem title | **AI-Powered Email Threat Detection, Geolocation & Forensic Intelligence Platform** (verified verbatim as the title of `SIH26106 - Complete Research & Engineering Brief.md` at the repository root) |
| Repository (local) | `C:\study\projects\SIH` |
| Repository (GitHub) | `https://github.com/yasin-kazi/SIH-TRACEMAIL.git` |
| Canonical backend | `backend/` — the only runnable FastAPI service (port 8000), SQLite via SQLAlchemy async (`database.py`) |
| Canonical frontend | `tracemail-app/` — React/Vite workstation, fully API-backed, no mock data in the investigation workflow (verified in `docs/PHASE_1_STATUS.md` and `docs/IMPLEMENTATION_AUDIT.md`) |
| Legacy frontend | `frontend/` — deprecated mock-only React app (Case 1042 hardcoded, Zustand store, mock analysis). Kept only for reference until removal is approved. Do NOT build on it. |
| Stitch export | `stitch_tracemail_ai_investigation_workstation/` — a **separate git repository** (own remote `gayasansari49-lab/SIH`) containing Stitch design screenshots plus an un-wired forensic Python library. Ignored by the outer repo. Do NOT activate it as a second backend. |
| Current development phase | **Phase 3 — Gmail acquisition.** Backend **and frontend** implemented; full suite green (**30/30**); live-account OAuth verification still [NEEDS TESTING]. |
| Evidence DB | SQLite; default `backend/tracemail.db` (gitignored). Overridable via `TRACEMAIL_DATABASE_URL`. |

### Current architecture (real, implemented)

```
tracemail-app (React/Vite, port 5173)              frontend (LEGACY mock, reference only)
      │  typed API client (src/api/)                        (not wired to backend)
      ▼
backend (FastAPI, port 8000)  ← routers: cases, gmail, reports, copilot
      │  SQLAlchemy async + SQLite (tracemail.db)
      ├─ EmailSource contract   → AcquiredEmail   → ingest_acquired_email()
      │      ├─ EMLSource (eml_upload)     [working, Phase 1]
      │      └─ GmailSource (gmail)        [Phase 3 backend — implemented]
      ├─ evidence engine: parser → auth → identity → MIME → hops → attachments → IOCs
      │                    → relationships → risk → campaign   (all persisted)
      ├─ evidence query layer (evidence_queries.py)  ← read APIs / report / copilot
      └─ read APIs: cases/*, reports/*, copilot/*, gmail/*
```

The forensic engine is **provider-independent**. Gmail is one acquisition adapter feeding the same normalized `AcquiredEmail → ingest_acquired_email()` pipeline used for `.eml` uploads.

---

## 2 — Current Project Status

| AREA | STATUS | DETAILS |
| --- | --- | --- |
| Phase 1 (EML vertical slice) | [COMPLETE] | `.eml` upload → case → evidence bytes+SHA-256 → deterministic analysis → investigation pages read live APIs. Verified: `docs/PHASE_1_STATUS.md`, EML suite passes. |
| Phase 2.1 (EmailSource capture + forensic evidence records) | [COMPLETE] | `EmailSource` contract, `AcquiredEmail`, `ingest_acquired_email`, 5 additive forensic tables (mime_parts, received_hops, attachments, iocs, evidence_relationships). `docs/PHASE_2_STATUS.md` M1. |
| Phase 2.2 (Expose normalized forensic evidence) | [COMPLETE] | Read-only forensic APIs (mime-parts, attachments, iocs, relationships, forensic-summary) resolved from persisted rows. M2. |
| Phase 2.3 (Report/Copilot evidence query migration) | [COMPLETE] | `evidence_queries.py` single case-scoped query layer; report & copilot cite persisted record ids; emission/copy claims removed. M3. |
| Phase 3 Gmail acquisition | [COMPLETE-ISH] | **Backend AND frontend implemented** (client, OAuth+PKCE, encrypted token store, GmailSource, endpoints, connect→pick→analyze UI). Tests: **24/24 gmail tests pass** (incl. new explicit PKCE test). Only live-account OAuth remains [NEEDS TESTING]. |
| EML acquisition | [COMPLETE] | `EMLSource` + upload endpoint; byte preservation + SHA-256 verified by test. |
| Forensic ingestion | [COMPLETE] | `ingest_acquired_email()` source-agnostic; feeds parser + analysis + persistence. |
| Evidence persistence | [COMPLETE] | `EvidenceRecord` (immutable original bytes, sha256, status=preserved) + normalized records + `SourceRecord` provenance. |
| Forensic read APIs | [COMPLETE] | mime-parts, attachments (metadata only), iocs (observables, no verdicts), relationships, forensic-summary, transit-hops. |
| Report generation | [COMPLETE] | `report_service.py` evidence-cited, observed vs inference labelled; no unsupported attribution. |
| Copilot | [COMPLETE] | `copilot_service.py` rule-based (no LLM), evidence-grounded answers. |
| Frontend (existing phases) | [COMPLETE] | Canonical `tracemail-app` API-backed: cases, overview, identity, evidence, infrastructure, graph, campaign, timeline, report, copilot, New Investigation (EML upload). No mocks in the investigation workflow. |
| Frontend (Gmail) | [COMPLETE] | `CasesPage` New Investigation dialog: Connect Gmail → OAuth in new tab → `/investigation?connect=` status page → picker/search → "Analyze" → existing `/case/{id}/analyzing` route. |
| Tests | [COMPLETE] | EML 6/6 OK; **full discovery 30/30 OK** (was 29 with 1 known test-only failure — fixed; new explicit PKCE test added). Frontend `npm run build` + `oxlint` pass. |
| Git / GitHub | [CHECKPOINT] (uncommitted work) | Local `main` = commit `8068e41`. **Untracked working changes:** the test fix, PKCE test, Gmail frontend, and doc updates are NOT yet committed. |
| Documentation | [COMPLETE] | `API_CONTRACT.md` Gmail section added; `GMAIL_ACQUISITION_DESIGN.md` marked implemented; `PHASE_2_STATUS.md` Phase 3 section updated to IMPLEMENTED; this handoff updated throughout. |

---

## 3 — What Has Already Been Built

The implemented, working data path (all steps persist records and are read back by the APIs):

```
EML acquisition (.eml upload)
  └─ EMLSource (services/sources/eml_source.py)  → AcquiredEmail
Gmail acquisition (Phase 3 backend)
  └─ GmailSource (services/gmail/gmail_source.py) → AcquiredEmail
        ▼
ingest_acquired_email()   (services/ingest_email.py)  — source-agnostic
        ▼
email_parser (services/email_parser.py)   — MIME parse, raw bytes hashed pre-parse
        ├─ auth_analysis (services/auth_analysis.py)        — SPF/DKIM/DMARC from Authentication-Results
        ├─ identity_analysis (services/identity_analysis.py) — chain/contradictions (verification of msg objects)
        ├─ MIME records (models.py MimePartRecord)
        ├─ Received hops (models.py ReceivedHopRecord)        — derived from Received headers only
        ├─ attachments (models.py AttachmentRecord)           — metadata + SHA-256 of payload, never bytes
        ├─ IOCs (models.py IOCRecord)                         — observables only, never verdicts
        ├─ evidence relationships (models.py EvidenceRelationshipRecord)
        ├─ risk_scoring (services/risk_scoring.py)            — heuristic score/level (deterministic, not ML)
        └─ campaign_correlation (services/campaign_correlation.py)
        ▼
persisted: SourceRecord + EvidenceRecord (raw bytes + sha256) + 5 forensic tables
        ▼
evidence query layer (services/evidence_queries.py)  — read-only, case-scoped, latest evidence
        ├─ report_service (services/report_service.py)       — evidence-cited text report
        ├─ copilot_service (services/copilot_service.py)     — rule-based answers, no LLM
        └─ routers/cases.py  forensic read APIs
```

### What each major component does

- **`services/sources/email_source.py`** — the `EmailSource` protocol and the frozen `AcquiredEmail` dataclass (`source_type`, `source_identifier`, `original_filename`, `content_type`, `raw_bytes`, `acquisition_method`, `metadata`). The forensic pipeline consumes **only** this contract; it never inspects the transport.
- **`services/sources/eml_source.py` / `services/sources/email_source.py` interplay** — EML upload maps to `source_type="eml_upload"`, `acquisition_method="upload"`.
- **`services/ingest_email.py`** — `ingest_acquired_email(db, acquired)`: creates `Case`, `SourceRecord`, `EvidenceRecord` (the exact `raw_bytes` + pre-parse SHA-256), runs the parser and all analysis services, persists the forensic tables, returns `{case_id, case_number, evidence_id, threat_type, risk_level, risk_score}`. Raises `UnparsableEmail` on failure.
- **`services/email_parser.py`** — `parse_eml` returns a parsed structure used across analysis services; hashes the original bytes before parsing. Lenient by design (accepts arbitrary byte streams — this is why the "malformed message" test injects `UnparsableEmail` via mock instead).
- **Analysis services** (`auth_analysis.py`, `identity_analysis.py`, `domain_analysis.py`, `ioc_extraction.py`, `risk_scoring.py`, `campaign_correlation.py`) — deterministic heuristics over parsed headers; every claim is labelled observed/derived/inference; nothing unsupported is asserted (report/copilot text was deliberately cleansed of "the attacker", "registered", "intentional impersonation" claims).
- **`services/evidence_queries.py`** — single read-only access path for the normalized forensic records. `get_case`, `get_latest_evidence`, `get_source`, `get_mime_parts`, `get_received_hops`, `get_attachments`, `get_iocs`, `get_relationships`, `get_evidence_summary`. Never loads payload bytes; every query is case-scoped to the latest preserved `EvidenceRecord`.
- **`services/report_service.py` / `services/copilot_service.py`** — both resolve forensic data exclusively through `evidence_queries`. Report cites record ids ("Preserved original evidence (record …)", "hop record …", "attachment record …"), labels `[observed]`/`[inference]`, and ends with "attribution … not established". Copilot is keyword-routed, rule-based text.
- **Read APIs** — see [Section 10 — API Map](#10-api-map).

---

## 4 — Phase 3 Gmail Status (inspection-based)

Legend: `[COMPLETE]` implemented + exercised by a passing test · `[PARTIAL]` implemented but a gap remains · `[NOT IMPLEMENTED]` absent · `[NEEDS TESTING]` implemented but not verifiable without a live Gmail account.

| # | Component | Status | Where implemented |
| --- | --- | --- | --- |
| 1 | Gmail API client | [COMPLETE] | `backend/services/gmail/client.py` — `GmailApiClient` protocol + `GmailHttpClient` (read-only, `userId=me`, bounded retry/backoff, typed error mapping) |
| 2 | Gmail raw message acquisition | [COMPLETE] | `client.get_message_raw` uses `format=raw` only (never `full`/`minimal`); `routers/gmail.py POST /api/gmail/analyze` |
| 3 | base64url decoding | [COMPLETE] | `client.decode_gmail_raw` — strict, pads `=`/`==` when omitted, rejects characters outside the base64url alphabet |
| 4 | raw-byte preservation | [COMPLETE] | `GmailSource.raw_bytes` passed through untouched → `EvidenceRecord.original_bytes` (test asserts byte equality). Wire-exactness vs live Gmail [NEEDS TESTING] (see §13) |
| 5 | SHA-256 hashing | [COMPLETE] | computed pre-parse in `acquisition.analyze` and again in `GmailSource.acquire`; equality asserted against `hashlib.sha256(fixture)` in test |
| 6 | GmailSource | [COMPLETE] | `backend/services/gmail/gmail_source.py` — maps message id + raw bytes → `AcquiredEmail` (`source_type="gmail"`, `acquisition_method="gmail_oauth"`, `content_type="message/rfc822"`, `original_filename=""`) |
| 7 | AcquiredEmail integration | [COMPLETE] | uses the same `AcquiredEmail` from `services/sources/email_source.py`; pipeline unchanged |
| 8 | token store | [COMPLETE] | `backend/services/gmail/token_store.py` — `SqlTokenStore` over `GmailConnection` (`models.py:310`); single active connected row; status missing/expired/revoked/valid |
| 9 | encryption | [COMPLETE] | `SecretCipher` AES-256-GCM, nonce-prefixed `v1:` + urlsafe-b64 blob; key from `TRACEMAIL_ENCRYPTION_KEY` (32 bytes, hex or urlsafe b64) with dev-only fallback + warning. Test asserts plaintext never in DB |
| 10 | OAuth state | [COMPLETE] | `backend/services/gmail/oauth.py` `OAuthStateStore` — CSPRNG `state`, single-use, 600 s expiry, constant-time verify (`hmac.compare_digest`) |
| 11 | CSRF protection | [COMPLETE] | state bound to the originating browser attempt; tampered / reused / expired → redirect `?connect=invalid|expired`, no exchange |
| 12 | PKCE | [COMPLETE] | S256 `code_challenge`/`code_challenge_method=S256` in auth URL; server keeps `code_verifier` in state store. **Note:** end-to-end PKCE verifier use is only implicitly tested (fake provider ignores verifier) — add an explicit test (see §7). |
| 13 | OAuth callback | [COMPLETE] | `GET /api/gmail/oauth/callback` — validates state, exchanges code server-side, persists encrypted tokens, redirects to `frontend_origin/investigation?connect=<signal>`; `secure`/`expired/invalid/denied/error` outcomes all tested |
| 14 | connection status | [COMPLETE] | `GET /api/gmail/status` → `{connected, source, status, account}`; missing/revoked/expired/valid tested |
| 15 | revoke / disconnect | [COMPLETE] | `POST /api/gmail/revoke` → best-effort Google revoke + mark revoked + delete all `gmail_connections`; tested |
| 16 | Gmail message search/list | [COMPLETE] | `GET /api/gmail/search` — provider-side `q`, `pageToken`, `maxResults` (≤50); returns id/threadId/snippet + metadata headers, never bodies; tested |
| 17 | message metadata | [COMPLETE] | `GET /api/gmail/messages/{id}/metadata` (`format=metadata`, From/Subject/Date); tested |
| 18 | selected-message analysis | [COMPLETE] | `POST /api/gmail/analyze` → fetch raw → decode → cap check → duplicate check → `GmailSource` → `ingest_acquired_email`; full pipeline (mime/hops/attachments/IOCs) asserted in parity test |
| 19 | frontend Gmail connection | [COMPLETE] | `CasesPage` New Investigation dialog toggles `GmailPane`: "Connect Gmail" opens `/api/gmail/auth/start` in a new tab (`noopener,noreferrer`) and polls `/api/gmail/status` until connected; disconnect with confirm → `POST /api/gmail/revoke`. |
| 20 | frontend Gmail picker | [COMPLETE] | `GmailPane` search via `GET /api/gmail/search` (paged: prev/next), metadata-only rows; never fetches bodies client-side. |
| 21 | frontend analyze flow | [COMPLETE] | "Analyze" per row → `POST /api/gmail/analyze` → `onAnalyzed(caseId)` → navigate to existing `/case/{id}/analyzing`; `?connect=success|denied|invalid|expired|error` handled on `/investigation` (`ConnectStatus`), then redirect to `/`. |
| 22 | size limits | [COMPLETE] | `max_raw_bytes` default 25 MB (`config.py`), overridable via `TRACEMAIL_GMAIL_MAX_RAW_BYTES`; `sizeEstimate` precheck + decoded-length check, refuse (`413`) never truncate; both tested |
| 23 | malformed-message handling | [COMPLETE] | bad base64 → `GmailMalformedRawError` → `422`; unparsable parsed message → `GmailMalformedRawError` → `422` (test injects `UnparsableEmail` because `parse_eml` is lenient) |
| 24 | 404 handling | [COMPLETE] | message deleted/missing → `GmailMessageNotFoundError` → `404` "no longer available"; tested |
| 25 | rate-limit handling | [COMPLETE] | `429` → `GmailRateLimitError` → `429` API; transient 429/5xx/network auto-retry with bounded backoff; tested |
| 26 | token-expiry handling | [COMPLETE] | expired access → refresh via refresh token (test asserts exactly one refresh + saved new access); revoked → `401` reconnect required (tested) |
| 27 | duplicate handling | [COMPLETE] | `409` "This Gmail message was already analyzed as <case_id>"; app-level check on `SourceRecord.source_type + source_id`; tested. DB-side unique index **DEFERRED** (see §13) |
| 28 | security tests | [COMPLETE] | Covered: state valid/tampered/reused/expired, encrypted-at-rest (ciphertext ≠ plaintext), no code/token in redirect URL, metadata responses exclude raw/body/payload, revoked→no cached fallback, **and `test_pkce_url_and_verifier_reach_exchange`** (auth URL `code_challenge` + `S256`, scope exactly `gmail.readonly`, stored verifier reaches `exchange_code`). Manual "no secrets in logs/API" grep also performed. |
| 29 | privacy controls | [COMPLETE] | `gmail.readonly` only scope; picker metadata only; only the analyst-selected message is retrieved; no cross-account path (`userId=me`); provenance limited to provider + account email; revoke destroys rows. Tested (metadata-only, case-scoping). |
| 30 | pipeline parity tests | [COMPLETE] | `test_pipeline_parity_with_eml_fixture` — the same `forensic_mixed.eml` bytes served as Gmail `format=raw` produce identical MIME parts (5), hops, attachment SHA-256s, and IOC set as the EML path; `test_case_scoping_between_sources` proves a Gmail case and an EML case cannot see each other's provenance/attachments. |

### What is LEFT for every incomplete item

- **#12 PKCE** — [COMPLETE] explicit test added (`test_pkce_url_and_verifier_reach_exchange`): auth URL carries `code_challenge` + `code_challenge_method=S256` with the `gmail.readonly` scope only, and the exact stored verifier reaches `exchange_code` end-to-end through the callback.
- **#28 security tests** — [COMPLETE] the PKCE test above closes the last named gap. Live "no secrets in logs" is a documented manual check (§13); backend grep confirms only HTTP status codes / exception type names are ever logged by the OAuth layer.
- **#19/#20/#21 frontend** — [COMPLETE] `src/api/gmail.ts` client, `GmailPane` component (connect → status poll → search/paged picker → Analyze), connect-status page at `/investigation?connect=…`, wired into `CasesPage` New Investigation dialog; analyze navigates to the existing `/case/{id}/analyzing` route.

---

## 5 — Known Test Status (verified 2026-09-11, updated after Phase 3 completion work)

### EML vertical slice — PASS

```
Command (workdir C:\study\projects\SIH\backend):
  python -m unittest tests.test_eml_vertical_slice -v
Result: Ran 6 tests — OK
Tests: test_upload_creates_case_and_preserves_original_bytes,
       test_forensic_records_are_persisted_from_mixed_mime_email,
       test_forensic_apis_expose_persisted_records,
       test_transit_hops_are_derived_from_received_headers,
       test_invalid_upload_returns_useful_error,
       test_report_and_copilot_are_evidence_grounded
```

### Gmail acquisition — 24/24 PASS (was 22/23)

```
Command (workdir C:\study\projects\SIH\backend):
  python -m unittest tests.test_gmail_acquisition -v
Result: Ran 24 tests — OK
```

The one known failure (`test_successful_raw_acquisition_fields_and_provenance`, `'msg-success' != 'msg-parity'` at the old line 274) was a test-only copy/paste assertion mismatch: the test analyzes `message_id="msg-success"` and every other assertion in it already used `"msg-success"`, but the final `forensic-summary` assertion still expected `"msg-parity"`. Fixed to assert `"msg-success"`. No application code changed. A new test, `test_pkce_url_and_verifier_reach_exchange`, was also added (24th test): it proves PKCE `code_challenge`/`S256` in the auth URL with only the `gmail.readonly` scope, and that the exact stored verifier reaches `exchange_code`.

### Full unittest discovery — 30/30 PASS (was 29 tests, 1 failure)

```
Command (workdir C:\study\projects\SIH\backend):
  python -m unittest discover -v
Result: Ran 30 tests — OK
```

Note on discovery: the correct command is `python -m unittest discover -v` run from `backend/` (this is what resolves `tests/` as a package so the relative imports in the test modules work). The variant `python -m unittest discover -s tests -p "test_*.py"` is NOT correct — it imports the test modules as top-level `test_*` and their `from .isolation import …` relative imports then fail with "attempted relative import with no known parent package".

### Frontend production build — PASS

```
Command (workdir C:\study\projects\SIH\tracemail-app):
  npm run build        → tsc -b && vite build ✓ (40 modules transformed)
  npm run lint         → oxlint ✓ (warnings only, pre-existing in useApiResource.ts)
```

### Backend launch

```
Command (workdir C:\study\projects\SIH\backend):
  uvicorn main:app --reload      (or python -m uvicorn main:app --reload)
Result: GET /api/health → {"status":"ok","service":"tracemail-ai"}
        GET /api/gmail/status → {"connected":false,"source":"gmail","status":"missing","account":null}
```

This is the **intended** launch shape: `backend/` is the working directory and `main.py` uses top-level imports (`from database import init_db`). Running `python -m uvicorn backend.main:app --reload` from the repo root is NOT a supported invocation in this layout.

### Notes
- Non-fatal `PydanticDeprecatedSince20` warning at import time (`backend/schemas.py:18`, class-based `config`). It does not fail anything; clean it up in a dedicated refactor if desired.
- Tests run against an **isolated throwaway SQLite DB** created by `backend/tests/isolation.py` (`tracemail_test_<uuid>.db` in the OS temp dir) via the `TRACEMAIL_DATABASE_URL` mechanism in `backend/database.py`. They never touch `backend/tracemail.db`.

---

## 6 — Current Git State

Verified read-only on 2026-09-11 (`git status`, `git branch -a`, `git log`, `git remote -v`, `git ls-remote`):

```
$ git status --short --branch
## main...origin/phase-3-gmail-wip
# NOTE (2026-09-11): working tree is NO LONGER clean — it holds the Phase 3
# completion work (test fix, PKCE test, frontend Gmail surface, docs): all
# uncommitted. See §8 checklist #12/#13 and the `git status` output at the end
# of this session. Commit it once the live-account P0 decision is made.

$ git branch -a
* main
  remotes/origin/HEAD -> origin/main
  remotes/origin/main
  remotes/origin/phase-3-gmail-wip

$ git log --oneline --decorate --graph --all -20
* 8068e41 (HEAD -> main, origin/phase-3-gmail-wip, origin/main, origin/HEAD)
  wip: phase 3 gmail acquisition

$ git remote -v
origin  https://github.com/yasin-kazi/SIH-TRACEMAIL.git (fetch)
origin  https://github.com/yasin-kazi/SIH-TRACEMAIL.git (push)

$ git ls-remote --heads https://github.com/yasin-kazi/SIH-TRACEMAIL.git
8068e417c912b9f80863e8e77228d9a5b6251023  refs/heads/main
8068e417c912b9f80863e8e77228d9a5b6251023  refs/heads/phase-3-gmail-wip
```

Key facts:

- **LOCAL COMMIT:** `8068e41` — `wip: phase 3 gmail acquisition`, on local branch `main`.
- **REMOTE WIP:** `origin/phase-3-gmail-wip` → `8068e41` (exists on GitHub, verified live).
- **REMOTE MAIN:** `origin/main` → `8068e41` (verified live).
- **Upstream:** local `main` tracks `origin/phase-3-gmail-wip`, and is **0 ahead / 0 behind** both remote branches.
- Working tree is clean; nothing is staged or modified.

### Important historical note (history reconciliation)

The handoff briefing stated the remote main held an **unrelated old commit `e8bf38f`** (the same commit as the headline of the nested `stitch_tracemail_ai_investigation_workstation` export), and that local and remote histories were unrelated. **The current live remote no longer matches that description.** Read-only verification shows both `refs/heads/main` and `refs/heads/phase-3-gmail-wip` now point at **`8068e41`** — the real TraceMail project commit — and `e8bf38f` is **no longer reachable on the remote**. Local and remote histories are now **identical** (same commit `8068e41`). This document records the verified state; no Git change was made to create it.

### DO NOT (checkpoint guardrails)

- **DO NOT** force-push `main` or `phase-3-gmail-wip` (`--force` / `--force-with-lease`) without explicit team-lead approval.
- **DO NOT** merge or rebase unrelated histories without approval (the unrelated-history situation no longer exists on the remote, but never assume).
- **DO NOT** `git reset --hard` or otherwise discard local work.
- **DO NOT** delete the `phase-3-gmail-wip` branch — it is the current home of Phase 3 work.
- The current real TraceMail project (all Phase 3 backend + tests) is safely preserved in commit **`8068e41`**, reachable from both local `main` and remote `phase-3-gmail-wip`.

---

## 7 — What Is Left to Do (prioritized)

### P0 — MUST DO before calling Phase 3 complete

- [x] **Fix `test_successful_raw_acquisition_fields_and_provenance`** — the last provenance assertion now matches the fixture (`"msg-success"`). Test hygiene only; no app logic changed.
- [x] **Run the full verification gate after any change** — EML 6/6, discovery 30/30, `npm run build` green (see [Section 5](#5--known-test-status-verified-2026-09-11-updated-after-phase-3-completion-work)).
- [x] **Write the Phase 3 Gmail documentation** — `docs/GMAIL_ACQUISITION_DESIGN.md` marked IMPLEMENTED, `docs/API_CONTRACT.md` has the full Gmail endpoint table, this handoff updated.
- [ ] **Real-account readiness review** — the only remaining P0 (external credentials; see `backend/services/gmail/config.py` for `TRACEMAIL_GMAIL_CLIENT_ID/SECRET/REDIRECT_URI`). Requires a configured Google Cloud OAuth client, the Gmail API enabled, consent screen ready, and redirect URI registered. Verify once: `GET /api/gmail/auth/start`, complete the flow, confirm status `connected` + a real `analyze` round-trip.

### P1 — done in this session

- [x] **Add explicit PKCE assertion test** — `test_pkce_url_and_verifier_reach_exchange` closes §4 #28: auth URL carries `code_challenge`/`code_challenge_method=S256`, scope is exactly `gmail.readonly`, and the stored verifier reaches `exchange_code`.
- [x] **Frontend: Gmail connect (button no longer "Coming soon")** — `CasesPage.tsx` toggles a `GmailPane`; "Connect Gmail" opens `/api/gmail/auth/start` in a new tab and polls `/api/gmail/status`.
- [x] **Frontend: Gmail picker + analyze flow** — `GmailPane` search with paged metadata rows; "Analyze" → `POST /api/gmail/analyze` → navigate to `/case/{id}/analyzing`. Metadata only; never fetches bodies client-side.
- [x] **Update `docs/API_CONTRACT.md` with the Gmail endpoints** — new "Gmail acquisition (Phase 3)" section; `source_identifier` = provider message id noted.
- [x] **Security sweep** — reviewed scope (only `gmail.readonly`), state (CSPRNG/single-use/600s/constant-time), PKCE S256, encrypted-at-rest tokens, no secrets in responses/redirects/logs, revoke/disconnect, case scoping.

### P2 — LATER / OPTIONAL (unchanged)

- [ ] **DB-side duplicate uniqueness** — add a unique index on `SourceRecord(source_type, source_id)` (or `(source_type, source_id, sha256)`) behind a migration. Currently the 409 duplicate check is app-level. *(Deferred by design doc §10/§12.)*
- [ ] **KMS-backed token store** — the `TokenStore` protocol already allows it (`token_store.py`); implementation is future work.
- [ ] **Multi-account connections** — today the store resolves one "current" connected account (single-analyst workstation; see `token_store.py` protocol docstring).
- [ ] **Clean up the Pydantic v2 deprecation warning** (`schemas.py:18` class-based `config` → `ConfigDict`).
- [ ] **State-store persistence** — `OAuthStateStore` is in-memory and per-process; fine for `uvicorn --reload` single worker, breaks under multiple workers/restarts mid-flow. Future hardening once auth is added.
- [ ] **Out of scope entirely:** Microsoft 365, header-paste, LLM/model routing, blockchain/WORM, Kafka/Redis/Elasticsearch/K8s, background jobs (see [Section 12](#12-architecture-rules--scope-lock)).

### P2 — LATER / OPTIONAL

- [ ] **DB-side duplicate uniqueness** — add a unique index on `SourceRecord(source_type, source_id)` (or `(source_type, source_id, sha256)`) behind a migration. Currently the 409 duplicate check is app-level. *(Deferred by design doc §10/§12.)*
- [ ] **KMS-backed token store** — the `TokenStore` protocol already allows it (`token_store.py`); implementation is future work.
- [ ] **Multi-account connections** — today the store resolves one "current" connected account (single-analyst workstation; see `token_store.py` protocol docstring).
- [ ] **Clean up the Pydantic v2 deprecation warning** (`schemas.py:18` class-based `config` → `ConfigDict`).
- [ ] **State-store persistence** — `OAuthStateStore` is in-memory and per-process; fine for `uvicorn --reload` single worker, breaks under multiple workers/restarts mid-flow. Future hardening once auth is added.
- [ ] **Out of scope entirely:** Microsoft 365, header-paste, LLM/model routing, blockchain/WORM, Kafka/Redis/Elasticsearch/K8s, background jobs (see [Section 12](#12-architecture-rules--scope-lock)).

---

## 8 — Exact Next Implementation Sequence

Steps 1–11 below are **DONE** in this session (sequencing recorded for replication):

1. Confirm test state: `cd backend; python -m unittest discover -v` (found the 1 known failure).
2. Fix the known failing assertion (`backend/tests/test_gmail_acquisition.py` → `"msg-success"`). Test code only.
3. Re-run the gate: `python -m unittest tests.test_eml_vertical_slice -v`, `python -m unittest discover -v`, `cd ..\tracemail-app; npm run build`.
4. Verify raw-byte preservation + SHA-256 end-to-end via read APIs — proven by `test_pipeline_parity_with_eml_fixture` (DB-level) and the forensic read API tests.
5. Verify token security manually — DB shows only `v1:` ciphertext blobs for `access_token_enc`/`refresh_token_enc`; no token in any response or redirect URL; revoke empties `gmail_connections`.
6. Verify the OAuth/PKCE flow — added `test_pkce_url_and_verifier_reach_exchange` (closes §4 #28) and confirmed `GET /api/gmail/auth/start`'s auth URL shape.
7. Verify picker + failure matrix via the fake-client tests (404/413/422/429/409/expiry/revoke all covered).
8. Implement the frontend Gmail surface (`tracemail-app`): `src/api/gmail.ts`, `GmailPane.tsx`, `ConnectStatus.tsx` at `/investigation`, wired into `CasesPage.tsx`; consume `?connect=…`; picker (paged `/api/gmail/search` + metadata); "Analyze" → `POST /api/gmail/analyze` → navigate to `/case/{id}/analyzing`.
9. Run complete backend tests (30/30) + frontend build + lint again.
10. Security review: no external `fetch()` in `tracemail-app/src`, no secrets/plaintext tokens anywhere, scope/state/PKCE verified.
11. Update documentation — design doc status, API contract Gmail section, this handoff (§2/§4/§5/§7).

12. **Remaining:** live-account verification (`GET /api/gmail/auth/start` → consent → analyze) needs a configured OAuth app (P0).
13. **Create a stable, non-WIP Phase 3 commit** on `phase-3-gmail-wip` (message like `feat(gmail): phase 3 gmail acquisition`) once green. **IMPORTANT:** the current working-tree changes (test fix, PKCE test, frontend, docs) are **not committed yet** — review `git status`/`git diff` first.
14. **GitHub integration** — push `phase-3-gmail-wip` (plain push, never force). Only merge into `main` with explicit team-lead approval; the remote histories are already reconciled at `8068e41`.

---

## 9 — File Map

### `backend/` — CANONICAL BACKEND (FastAPI)

| File | Purpose | Modify? |
| --- | --- | --- |
| `main.py` | App factory; CORS (dev origins 5173/3000/5174); mounts `cases`, `copilot`, `reports`, `gmail` routers; lifespan `init_db`; `GET /api/health`. | Yes (add routers/CORS) |
| `database.py` | Async engine + session; `DATABASE_URL` from `TRACEMAIL_DATABASE_URL` (default `sqlite+aiosqlite:///./tracemail.db`); `Base`, `get_db`, `init_db` (`create_all` — no Alembic). | Yes |
| `models.py` | `Case`, `IdentityRecord`, `SourceRecord`, `EvidenceRecord`, `MimePartRecord`, `ReceivedHopRecord`, `AttachmentRecord`, `IOCRecord`, `EvidenceRelationshipRecord`, `EvidenceFindingRecord`, `InfrastructureRecord`, `TimelineEventRecord`, `CampaignRecord`, `CopilotMessageRecord`, `ReportRecord`, `GmailConnection`. | Yes — additive only |
| `schemas.py` | Pydantic v1-style (deprecation warning) response/request models incl. `Gmail*` and `UploadResponse`. | Yes |
| `routers/cases.py` | Case list/detail, upload, identity, evidence, mime-parts, attachments, iocs, relationships, forensic-summary, headers, transit-hops, infrastructure, graph, campaign, timeline. | Yes |
| `routers/gmail.py` | Gmail endpoints (see §10, "GMAIL APIs"). | Yes |
| `routers/reports.py` | report get/generate. | Yes |
| `routers/copilot.py` | messages/ask/suggested-questions. | Yes |
| `services/sources/email_source.py` | `AcquiredEmail` + `EmailSource` protocol — **the pipeline contract**; treated as frozen. | Only by deliberate design |
| `services/sources/eml_source.py` | EML adapter. | Yes |
| `services/ingest_email.py` | `ingest_acquired_email()` + `UnparsableEmail`. | Only by deliberate design |
| `services/email_parser.py` | MIME parsing; hashes bytes pre-parse. | Yes |
| `services/auth_analysis.py`, `identity_analysis.py`, `domain_analysis.py`, `ioc_extraction.py`, `risk_scoring.py`, `campaign_correlation.py` | Deterministic analysis services. | Yes |
| `services/evidence_queries.py` | Read-only, case-scoped evidence query layer (owned by read APIs/report/copilot). | Yes |
| `services/report_service.py`, `copilot_service.py` | Evidence-grounded report and rule-based copilot. | Yes |
| `services/gmail/__init__.py` | Exports `GmailSource`. | Yes |
| `services/gmail/client.py` | `GmailApiClient` protocol, `GmailHttpClient`, `decode_gmail_raw`. | Yes |
| `services/gmail/oauth.py` | `OAuthStateStore`, PKCE, `GoogleOAuthProvider` (exchange/refresh/revoke). | Yes |
| `services/gmail/token_store.py` | `TokenStore` protocol, `SecretCipher` (AES-256-GCM), `SqlTokenStore`, `CredentialStatus`. | Yes |
| `services/gmail/config.py` | `GmailConfig` + env loading (`TRACEMAIL_GMAIL_*`, `TRACEMAIL_ENCRYPTION_KEY`). | Yes |
| `services/gmail/errors.py` | Typed `GmailError` hierarchy → HTTP mapping. | Yes |
| `services/gmail/gmail_source.py` | `GmailSource` → `AcquiredEmail`. | Yes |
| `services/gmail/acquisition.py` | `GmailService` orchestration + `build_gmail_service`. | Yes |

### `backend/tests/` — test suite (standard-library `unittest`)

| File | Purpose | Modify? |
| --- | --- | --- |
| `isolation.py` | `set_test_database_env()/test_db_path()/teardown_database()` — shared per-run throwaway DB via `TRACEMAIL_DATABASE_URL`. | Yes |
| `__init__.py` | Package marker (enables `tests.test_x` imports). | Yes |
| `test_eml_vertical_slice.py` | 6 tests: upload/bytes/hash, MIME persistence, forensic APIs, hops, invalid upload, report/copilot grounding. | Yes |
| `test_gmail_acquisition.py` | **24 tests**: acquisition fields/provenance, pipeline parity, duplicates, 404/413/422/429/5xx, OAuth state/callback, **PKCE url+verifier**, expiry/revoke, case scoping, picker metadata, revoke. | No — green |
| `fixtures/forensic_mixed.eml`, `valid.eml` | Canonical test fixtures (also used as Gmail `format=raw` source for parity). | Yes (additive) |

### `tracemail-app/` — CANONICAL FRONTEND (React/Vite)

| File / area | Purpose | Modify? |
| --- | --- | --- |
| `src/api/client.ts` | Base API client (reads `VITE_API_BASE_URL`). | Optional |
| `src/api/cases.ts`, `reports.ts`, `copilot.ts`, `useApiResource.ts` | Typed server-state layer for existing endpoints. | No |
| `src/api/gmail.ts` | **New:** typed Gmail client — `getGmailStatus`, `getGmailAuthUrl`, `searchGmail`, `analyzeGmailMessage`, `revokeGmail`. | Yes (additive) |
| `src/components/GmailPane.tsx` | **New:** connect button + OAuth-tab flow + status polling, disconnect, search/paged picker, per-row Analyze → callback. | Yes (additive) |
| `src/pages/ConnectStatus.tsx` | **New:** `/investigation` route that renders `?connect=success|denied|invalid|expired|error`, then redirects to `/`. | Yes (additive) |
| `src/pages/CasesPage.tsx` | Cases list + New Investigation dialog. Gmail card now toggles `GmailPane`; analyze navigates to `/case/{id}/analyzing`. | No |
| `src/App.tsx` | Added `/investigation` route. | No |
| `src/types/index.ts` | Added `GmailStatus`, `GmailMessageRow`, `GmailSearchResult`. | No |
| `src/pages/*` | Overview, Identity, Evidence, Infrastructure, Graph, Campaign, Timeline, Report, Copilot, AnalysisProgress. | Yes |
| `vite.config.ts`, `tsconfig*.json` | Toolchain. | Yes |

### `frontend/` — LEGACY / DEPRECATED (do not build on)

`src/data/mockCase1042.ts`, `mockCases.ts`, `mockAnalysis.ts`, Zustand `useCaseStore`, mock-only pages. **Canonical state: `tracemail-app/` is the canonical frontend** (verified in `docs/PHASE_1_STATUS.md` and `docs/IMPLEMENTATION_AUDIT.md`). Keep as reference until removal is approved.

### `docs/` — reference and status

| File | Purpose |
| --- | --- |
| `IMPLEMENTATION_AUDIT.md` | Phase-0 audit (dated 2026-09-10) + Phase-1 update; forensic principles, canonical-app decisions, risks. Read this first for context. |
| `PHASE_1_STATUS.md`, `PHASE_2_STATUS.md` | Phase status. Phase 2 status now records Gmail as **IMPLEMENTED**, live-account check pending. |
| `GMAIL_ACQUISITION_DESIGN.md` | Gmail architecture/security design baseline (§1–§14) — marked **IMPLEMENTED** at top, original design-time header preserved. |
| `API_CONTRACT.md` | Phase 1+2 contract + new **"Gmail acquisition (Phase 3)"** section (status, auth/start, callback, revoke, search, metadata, analyze). |
| `TEAM_HANDOFF.md` | **This document.** |

### Root-level

`IMPLEMENTATION_PLAN.md`, research brief + spec PDFs, `SIH_Hackathon_Presentation*.pptx`, `template_pages/*.png`, root helper scripts (`create_ppt*.py`, `extract_*.py`). `stitch_tracemail_ai_investigation_workstation/` is a **separate git repo**, ignored here.

---

## 10 — API Map

Base URL `http://localhost:8000`. Errors use `{"detail": "..."}`.

### EXISTING FORENSIC APIs (`backend/routers/cases.py`) — all read-only, case-scoped

| METHOD | PATH | PURPOSE | STATUS |
| --- | --- | --- | --- |
| GET | `/api/cases` | List cases (optional `status` filter) | [COMPLETE] |
| GET | `/api/cases/{case_id}` | Case detail (no raw bytes) | [COMPLETE] |
| POST | `/api/cases/upload` | `.eml` upload → ingest pipeline → case | [COMPLETE] |
| GET | `/api/cases/{case_id}/identity` | Identity contradictions/chain | [COMPLETE] |
| GET | `/api/cases/{case_id}/evidence` | Derived evidence findings | [COMPLETE] |
| GET | `/api/cases/{case_id}/mime-parts` | Persisted MIME part metadata | [COMPLETE] |
| GET | `/api/cases/{case_id}/attachments` | Attachment metadata + SHA-256 (never payload bytes) | [COMPLETE] |
| GET | `/api/cases/{case_id}/iocs` | Observables (no verdicts) | [COMPLETE] |
| GET | `/api/cases/{case_id}/relationships` | Evidence relationship links | [COMPLETE] |
| GET | `/api/cases/{case_id}/forensic-summary` | Provenance + persisted counts | [COMPLETE] |
| GET | `/api/cases/{case_id}/headers` | Parsed headers + raw header block | [COMPLETE] |
| GET | `/api/cases/{case_id}/transit-hops` | Received-chain records (persisted) | [COMPLETE] |
| GET | `/api/cases/{case_id}/infrastructure` | IP/infrastructure summary | [COMPLETE] |
| GET | `/api/cases/{case_id}/graph` | Simple relation graph | [COMPLETE] |
| GET | `/api/cases/{case_id}/campaign` | Campaign or `null` | [COMPLETE] |
| GET | `/api/cases/{case_id}/timeline` | Timeline events | [COMPLETE] |

### GMAIL APIs (`backend/routers/gmail.py`) — ALL BACKEND-DONE; FRONTEND CONSUMERS MISSING

| METHOD | PATH | PURPOSE | STATUS |
| --- | --- | --- | --- |
| GET | `/api/gmail/auth/start` | Return Google auth URL (state+PKCE) | [COMPLETE] backend |
| GET | `/api/gmail/oauth/callback` | OAuth code exchange → 303 to frontend `?connect=` | [COMPLETE] backend |
| GET | `/api/gmail/status` | Connection status / account | [COMPLETE] backend |
| POST | `/api/gmail/revoke` | Revoke + delete server credentials | [COMPLETE] backend |
| GET | `/api/gmail/search` | Provider-side search → metadata rows (paged, ≤50) | [COMPLETE] backend |
| GET | `/api/gmail/messages/{message_id}/metadata` | Picker row metadata (`format=metadata`) | [COMPLETE] backend |
| POST | `/api/gmail/analyze` | Fetch `format=raw` → decode → cap/dup checks → `ingest_acquired_email` → `UploadResponse` | [COMPLETE] backend |
| (none) | — | Any frontend call to the above | [NOT STARTED] |

### COPILOT APIs (`backend/routers/copilot.py`)

| METHOD | PATH | PURPOSE | STATUS |
| --- | --- | --- | --- |
| GET | `/api/copilot/{case_id}/messages` | List messages; first read writes greeting | [COMPLETE] |
| POST | `/api/copilot/{case_id}/ask` | Rule-based, evidence-grounded answer | [COMPLETE] |
| POST | `/api/copilot/{case_id}/suggested-questions` | Fixed suggestion list | [COMPLETE] |

### REPORT APIs (`backend/routers/reports.py`)

| METHOD | PATH | PURPOSE | STATUS |
| --- | --- | --- | --- |
| GET | `/api/reports/{case_id}` | Retrieve generated report (404 if absent) | [COMPLETE] |
| POST | `/api/reports/{case_id}/generate` | Generate/regenerate evidence-cited report | [COMPLETE] |

### HEALTH

| METHOD | PATH | PURPOSE | STATUS |
| --- | --- | --- | --- |
| GET | `/api/health` | `{"status":"ok","service":"tracemail-ai"}` | [COMPLETE] |

---

## 11 — Forensic Rules That Must NOT Be Broken

These are guardrails. Each is currently honored by the code (verified) unless marked.

- **Evidence first.** Every case is grounded in preserved original evidence; derived claims are labelled. Verified in `ingest_email.py`, `evidence_queries.py`, report/copilot.
- **Raw bytes preserved byte-for-byte.** `EvidenceRecord.original_bytes` = the exact acquired bytes (EML upload or Gmail `format=raw` decoded). No normalization. Verified by tests.
- **SHA-256 integrity.** Hash computed **before** parsing, from the exact bytes; `EvidenceRecord.sha256` must always equal `hashlib.sha256(original_bytes)`. Verified by tests; recomputable via read APIs.
- **Observed vs derived vs inferred vs unknown.** Report labels `[observed]`/`[inference]`; unestablished facts are stated "not established". Verified.
- **No unsupported attacker attribution.** "Attribution to any specific individual or group is not established." Verified in report/copilot wording.
- **IP geolocation is infrastructure indication, not exact attacker location.** Verified in design/audit docs; display treats locations as provider/ASN indications.
- **Gmail account ownership does not prove sender authenticity.** Provider message id is provenance only. The Gmail adapter records provenance; it never authenticates the sender. Verified (`docs/GMAIL_ACQUISITION_DESIGN.md §6`, `gmail_source.py`).
- **No reconstruction when raw evidence is available.** Gmail uses `format=raw` only; never `full`/`minimal` reconstruction. Verified (`client.py`).
- **Case-scoped evidence access.** Every evidence query is confined to a case; a Gmail-derived case cannot see an EML case's attachments/provenance. Verified by `test_case_scoping_between_sources`.
- **No unsafe HTML rendering.** Evidence is text/meta-based; Gmail picker returns metadata only; no raw HTML preview, no `<iframe>` body embed, no remote images (design §7; no such code exists).
- **No automatic URL fetching.** IOCs are observables; the backend never fetches extracted URLs (no SSRF). Verified (no client code does this).
- **No secrets in logs/frontend.** OAuth client secret and tokens are server-side only, encrypted at rest; never in responses, redirect URLs, or the frontend bundle. Verified (token store, callback redirect uses only a status flag, tests assert).
- **No cross-case evidence leakage.** Combined case-scoping + per-case provenance. Verified.
- **No fake fallback.** Authorization failures are terminal (reconnect), never degraded to cached/fabricated content. Verified (errors.py, acquisition.py).

---

## 12 — Architecture Rules / Scope Lock

Future developers MUST NOT introduce the following without explicit team-lead approval:

- **Microsoft 365** OAuth/adapter (future adapter, out of Phase 3 scope).
- **Header-paste ingestion adapter**.
- **LLM / AI model router / multi-model reasoning** — Copilot is deliberately rule-based.
- **Blockchain** / integrity anchoring.
- **WORM / object-storage MANDATORY-flattened** evidence store (SQLite BLOB is accepted for now; object store is a future milestone).
- **Kafka / Redis / Elasticsearch** (not needed; SQLite + sync analysis).
- **Kubernetes** and **production infrastructure** (no deployment work until milestones stabilize).
- **Unnecessary microservices** — the single FastAPI backend is canonical.
- **Background jobs / async analysis** — analysis is synchronous by design in this phase.

**Gmail must remain an acquisition adapter**, feeding exactly:

```
GmailSource → AcquiredEmail → ingest_acquired_email() → existing forensic pipeline
```

The forensic engine is **provider-independent**: it consumes only `AcquiredEmail`, never `GmailConnection` fields or Gmail API responses. Any future adapter (Microsoft 365, header-paste) must follow the same rule. Do not make the pipeline depend on Gmail-specific concerns (OAuth/tokens/client stay behind `GmailSource` + the Gmail service layer).

---

## 13 — Known Risks / Open Questions

Legend: **VERIFIED** = confirmed from repo/commands · **UNVERIFIED** = cannot be proven without a live account/config · **DEFERRED** = consciously postponed.

- **Gmail raw-byte fidelity (wire-exactness)** — UNVERIFIED. Verified only that the decoded fake-returned bytes are preserved byte-for-byte and hashed. Whether Gmail's `format=raw` output is byte-identical to the originally delivered message for all cases is unknown; the code correctly records provenance as "bytes returned by Gmail format=raw at acquisition time" and never claims wire-exactness (`docs/GMAIL_ACQUISITION_DESIGN.md §13/§14`). Verify against a controlled account before claiming wire-exactness.
- **Gmail API enablement + OAuth client configuration** — UNVERIFIED. Requires `TRACEMAIL_GMAIL_CLIENT_ID`, `TRACEMAIL_GMAIL_CLIENT_SECRET`, registered exact redirect URI (`http://localhost:8000/api/gmail/oauth/callback` default), Gmail API enabled, and a Google consent screen with the tester/team account in "Testing". The server will return `503` via `GmailConfigError` when unconfigured.
- **Encryption key configuration** — UNVERIFIED in production. `TRACEMAIL_ENCRYPTION_KEY` must decode to **exactly 32 bytes** (64 hex chars, or urlsafe-base64; optional `hex:`/`b64:` prefixes). When unset, a deterministic **development-only** key is used and a warning is logged — never deploy that (design threat: refresh-token exposure reads the mailbox).
- **Scope set decision** — DEFERRED/UNVERIFIED. Code requests only `gmail.readonly`; the account email is obtained via `users/me/profile` (works with the readonly scope). The design doc's optional `openid`/`email` scopes were intentionally not added — confirm the profile call works that way against a real account.
- **Refresh-token behavior** — UNVERIFIED. Gmail access tokens live ~1 hour; refresh tokens do not rotate by default. If the refresh token is invalidated (password change, user revokes), the flow demands a fresh connect (implemented; not live-tested).
- **Duplicate policy** — DEFERRED at the DB layer. Implemented as an app-level `409` keyed on `SourceRecord(source_type, source_id)` at analyze time; no unique index, so two concurrent analyses could race. Add the unique index when schema migrations are introduced.
- **Size-limit uncertainty** — UNVERIFIED. Default 25 MB cap (`TRACEMAIL_GMAIL_MAX_RAW_BYTES`). Whether `sizeEstimate` approximates the base64url or decoded size is undocumented; both a `sizeEstimate` precheck and a post-decode check exist, so even if the heuristic is off the post-decode check is authoritative.
- **Test limitation (PKCE end-to-end)** — DEFERRED/UNVERIFIED. Fake provider ignores the verifier; add an explicit assertion (P1).
- **Test isolation** — VERIFIED. `backend/tests/isolation.py` redirects the SQLite DB via `TRACEMAIL_DATABASE_URL` to a per-run throwaway file; tests never touch `backend/tracemail.db`.
- **State store is in-memory & process-local** — DEFERRED. `OAuthStateStore` + the module-global `_service` in `routers/gmail.py` work single-process (`uvicorn --reload`). Multiple workers/restarts mid-flow invalidate pending states. Acceptable for the workstation; harden with auth/sessions later.
- **Pydantic v2 deprecation warning** — VERIFIED (non-blocking). `schemas.py:18` class-based `config`. Clean up in a P2 refactor.
- **No Alembic migrations** — DEFERRED. `init_db` uses `create_all`; additive-only model changes keep dev DBs working.
- **No authentication/RBAC** — DEFERRED. Single-analyst workstation; CORS allowlist is dev-only (`main.py`).
- **Frontend Gmail work is entirely absent** — VERIFIED. See §7 P1.

---

## 14 — How to Start Tomorrow (START HERE)

```powershell
cd C:\study\projects\SIH

# 1. Confirm you are on the right branch and clean.
git status
git branch -a
git fetch origin
git switch main          # local main == origin/main == origin/phase-3-gmail-wip == 8068e41
git log --oneline --decorate --graph --all -20

# 2. INSPECT BEFORE CHANGING — read these in order:
#    docs/TEAM_HANDOFF.md        (this document)
#    docs/IMPLEMENTATION_AUDIT.md (background, forensic principles)
#    docs/GMAIL_ACQUISITION_DESIGN.md (the Phase 3 design baseline)
#    backend/services/gmail/     (the implemented Phase 3 backend)
#    backend/tests/test_gmail_acquisition.py (line 274 = the one known failure)

# 3. Confirm the current (expected) test state:
cd backend
$env:PYTHONIOENCODING='utf-8'
python -m unittest tests.test_eml_vertical_slice -v    # expected: OK (6 tests)
python -m unittest discover -v                          # expected: 1 failure ('msg-success' != 'msg-parity')

# 4. Verify the frontend still builds:
cd ..\tracemail-app
npm run build

# 5. Fix the one known test-only failure, re-run discovery, then proceed with §8.
cd ..\backend
python -m unittest discover -v
```

When you later want to run the app (not the tests):

```powershell
cd C:\study\projects\SIH\backend
uvicorn main:app --reload          # serves :8000; DB = ./tracemail.db (gitignored)
cd ..\tracemail-app
npm run dev                        # serves :5173
```

Guardrails before making changes: never force-push/rewrite history without team-lead approval; never `git add .` blindly (root `.gitignore` already excludes `.env*`, `*.db`, `__pycache__/`, `venv/`, `node_modules/`, `dist/`, `build/`, and the nested Stitch repo); never commit or create secrets.

---

## 15 — Definition of Done for Phase 3

A concrete checklist — phase 3 Gmail acquisition is COMPLETE only when **all** of:

- [ ] `test_successful_raw_acquisition_fields_and_provenance` passes (line 274 fixed) and `python -m unittest discover -v` is fully green.
- [ ] OAuth works against a **real** configured app (auth/start → Google → callback → connected), with least-privilege scope confirmed (`gmail.readonly` only).
- [ ] Tokens never reach the frontend: encrypted `v1:` blobs at rest only; nothing but a status flag in redirect URLs; revoke empties `gmail_connections`.
- [ ] Raw message retrieved with `format=raw`; decoded with padding-tolerant strict base64url (`decode_gmail_raw`).
- [ ] Exact acquired bytes hashed pre-parse and preserved in `EvidenceRecord` (SHA-256 reproducible via `forensic-summary`).
- [ ] `GmailSource` produces `AcquiredEmail` with `source_type="gmail"`, `acquisition_method="gmail_oauth"`, `content_type="message/rfc822"`, `original_filename=""`.
- [ ] Ingestion uses the **existing** pipeline (`ingest_acquired_email`) — no forensic-engine change.
- [ ] Forensic records persisted (mime/hops/attachments/iocs/relationships) and readable through the read APIs for a Gmail case.
- [ ] Selected-message workflow works in the canonical frontend (`tracemail-app`): connect UI, picker, analyze → navigate to the new case. *(Currently NOT implemented.)*
- [ ] Malformed/oversized/404/rate-limit/expired/revoked/message-not-found cases handled with the documented HTTP mapping (409/413/422/401/404/429/5xx).
- [ ] Verify Gmail raw-byte fidelity on a controlled account, or explicitly document "bytes as returned by Gmail" (no wire-exactness claim).
- [ ] EML regression suite passes (`test_eml_vertical_slice` 6/6) and `npm run build` passes in `tracemail-app`.
- [ ] Security review passes (PKCE explicit test; no secrets in logs/frontend; mocks grep clean; no URL fetching).
- [ ] Documentation complete (`docs/GMAIL_ACQUISITION_DESIGN.md` gains an implemented-status section; `docs/API_CONTRACT.md` documents the Gmail endpoints; phase status docs updated; this handoff updated).
- [ ] Git checkpoint created: a stable, non-WIP Phase 3 commit on `phase-3-gmail-wip`, pushed with a **plain** push (no force).

---

## 16 — Handoff Rule

> Before implementing anything not listed in this document, inspect the existing architecture and update this checklist/status. Do not silently redesign the forensic pipeline.

> Never force-push or rewrite Git history without explicit team-lead approval.