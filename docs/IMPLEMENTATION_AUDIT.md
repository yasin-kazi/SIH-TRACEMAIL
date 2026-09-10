# TraceMail Implementation Audit

**Scope:** Phase 0 read-only audit of the existing SIH26106 repository on 2026-09-10.  No application code was changed and Gmail was not implemented.

## Executive conclusion

TraceMail is a partially integrated prototype with three distinct implementation strands:

1. `backend/` is the only runnable FastAPI application.  It accepts `.eml` uploads, creates SQLite-backed cases, runs a small synchronous analysis flow, and exposes case, investigation, report, and copilot endpoints.
2. `tracemail-app/` is the best UI base for the next milestone.  It has the broadest workstation coverage and its types/pages closely match the root backend API, but every page currently reads mock data.
3. `stitch_tracemail_ai_investigation_workstation/backend/app/` contains the strongest forensic domain model and reusable analysis utilities, but it is a library/prototype: it has neither FastAPI application entrypoint nor API routes or end-to-end orchestration.

The recommended canonical system is therefore **`backend/` + `tracemail-app/`**.  Incrementally port well-tested, security-reviewed components from the Stitch backend into the root backend rather than trying to run two backends or rewrite the UI.

## Repository map

| Location | Purpose | Status |
| --- | --- | --- |
| `backend/` | FastAPI, async SQLite storage, `.eml` intake, analysis services and routers | Functional prototype; canonical backend candidate |
| `tracemail-app/` | React/Vite workstation with cases, overview, identity, evidence, infrastructure, graph, campaign, timeline, copilot, report | Strongest UI structure; entirely mock-backed |
| `frontend/` | Separate React/Vite mobile-style investigation prototype | Mock-only and lower functional coverage |
| `stitch_tracemail_ai_investigation_workstation/` | Stitch HTML/screenshot design references plus a separate forensic Python codebase | Keep as design/reference and source of reusable modules |
| root research/PDF/PPT files | Product requirements, engineering brief, presentation material and implementation plan | Useful specification; implementation plan explicitly describes a mock-only prototype |

There is no repository-level README, `.git` metadata, Docker configuration, CI configuration, test framework configuration, or unified environment configuration.  `node_modules/` and built `dist/` assets are checked into the two frontend directories.

## Current architecture

```text
tracemail-app (React/Vite; mock data today)     frontend (separate mock React app)
                         |                                  |
                         +------------- no API calls --------+

backend/main.py (FastAPI, port 8000)
  ├─ /api/cases: upload and investigation reads
  ├─ /api/reports: persisted text report generation
  ├─ /api/copilot: persisted, keyword-routed response text
  ├─ SQLite database (`./tracemail.db` from backend process cwd)
  └─ synchronous .eml parsing → identity/risk/DNS/IP lookup → persistence

stitch_.../backend/app (unwired alternative modules; own SQLite model)
  ├─ ingestion, MIME/evidence helpers
  ├─ verification and intelligence helpers
  ├─ correlation and decision helpers
  └─ PDF report renderer
```

## Existing working functionality

### Root FastAPI backend

Static inspection confirms the root backend has a coherent executable application (`backend/main.py`), lifespan database initialization, CORS, three mounted routers, SQLAlchemy models, and matching Pydantic response schemas.  Its implemented path is:

`.eml upload` → SHA-256 → Python `email` parsing → header-derived SPF/DKIM/DMARC values → identity contradictions → DNS/ASN/geolocation lookups → heuristic risk/classification → case/evidence/infrastructure/timeline/campaign records → case API.

Implemented capabilities include:

- `.eml` extension validation and upload endpoint.
- Raw message text, raw header block, filename, size and SHA-256 persisted on `Case`.
- Parsing of basic From/To/Reply-To/Return-Path/Date/Message-ID/Received/Authentication-Results fields and simple body extraction.
- Basic identity, risk, threat-type, domain/IP/ASN/geolocation and campaign services.
- Read APIs for case list/detail, identity, evidence, headers, transit hops, infrastructure, graph, campaign and timeline.
- Persisted text report generation and persisted copilot messages.

### Stitch forensic library

The Stitch codebase has useful capabilities not yet connected to an application:

- MIME parsing with attachment metadata and hashes.
- More detailed header/Received-chain analysis, including earliest non-private IP selection.
- URL normalization and suspicious-pattern analysis.
- Domain/IP/reputation helper modules, with optional API-key configuration documented in `.env.example`.
- A considerably richer storage model for raw evidence, email parts, headers, hops, IOCs, signals, risk assessments, hypotheses, audit events and campaign joins.
- Explainability, risk, confidence, correlation and PDF-report helpers.

It is not currently an operational backend: `app/api/` is empty and searches find no `FastAPI`, `APIRouter`, route decorators, or server entrypoint under that backend.

## Mock and placeholder functionality

### `tracemail-app/`

All visual data comes from `src/data/mockData.ts`; there are no `fetch`, Axios, or API client calls.  The following pages are mock-backed: Cases, Overview, Identity, Evidence (including raw headers and hops), Infrastructure, Graph, Campaign, Timeline, Copilot, and Report.  The case-create interaction is a timeout rather than an upload.  The copilot is a local mock responder.  The route parameter does not select server data.

### `frontend/`

This is also mock-only.  The Zustand store imports `mockCase1042` and `mockCases`; `selectCase` ignores its supplied ID and always selects Case 1042.  Upload/drop does not submit a file.  `runMockAnalysis` animates a fabricated analysis.  Campaigns, graph topology/positions, risk values, evidence, chain of custody, reports and all overview/identity content are hardcoded.

### Root backend placeholders that must not be presented as forensic conclusions

- SPF/DKIM/DMARC results are read only from existing `Authentication-Results`; the separate DNS-auth module is not invoked by the upload pipeline and does not verify a message signature.
- The upload flow passes `from_domain` as the DKIM domain, which makes the identity analysis report an apparent DKIM alignment even when no DKIM `d=` value was parsed.
- `known_domains=[from_domain]` makes the root typosquatting comparison self-referential, so it cannot detect a lookalike of a protected/expected organization.
- `get_transit_hops` fabricates corporate relay and inbox entries instead of returning parsed Received hops.
- The graph is generated from a small fixed layout and simple header fields; it is not a persisted evidence graph.
- Campaign creation treats the first case for a sender domain as a campaign and links later cases using only sender/reply domains or IP; it does not establish a robust multi-signal campaign conclusion.
- Report and copilot text include unsupported assertions such as recent registration, privacy proxy use, third-party relay, attacker's actions, or campaign scope, even when no evidence stores those facts.
- “Model confidence” is a deterministic heuristic value, not ML-model confidence.  The copilot is keyword routing, not an AI model.
- `threat_feeds` is always zero in the root upload flow; no reputation feed is invoked.
- The root `get_ip_geolocation` calls a public HTTP IP API synchronously from an async request handler and has no allowlist/private-address guard, controlled egress policy, timeout/retry policy beyond a single timeout, provenance record, or caching.

## Duplicate implementations

| Capability | Root backend | Stitch backend | Recommendation |
| --- | --- | --- | --- |
| EML/MIME parsing | `services/email_parser.py` | `app/ingestion/eml_parser.py`, `mime_parser.py` | Keep root endpoint; merge Stitch attachment/MIME/decoded-header capabilities into one parser |
| Evidence hashing/storage | SHA-256/raw text fields on `Case` | `Evidence` entity and `save_evidence` helper | Replace root raw-text-only storage with an immutable evidence object; retain one implementation |
| Identity analysis | `services/identity_analysis.py` | `app/verification/identity.py` | Consolidate around Stitch's richer evidence-state output after tests |
| Authentication analysis | `services/auth_analysis.py` | `app/verification/authentication.py` | Merge into one message-result/alignment analyser; do not equate DNS record presence with signature verification |
| Domain/IP intelligence | `services/domain_analysis.py` | `app/intelligence/domain_intel.py`, `ip_intel.py`, `threat_intel.py` | Retain only a controlled, async enrichment layer with provenance and safe egress |
| Risk/explainability | `risk_scoring.py`, report/copilot text | `risk_engine.py`, `confidence.py`, `explainability.py` | Port and harden structured evidence-backed decision output; remove unsupported prose |
| Correlation/graph | simple campaign service and dynamic UI graph | multi-signal campaign/graph/infrastructure helpers | Build one persisted relation model using the Stitch design as a reference |
| Reporting | text fields in database | PDF renderer | Use one report service backed by persisted data; add a download endpoint later |
| Frontend | `frontend/` and `tracemail-app/` | static Stitch HTML screen references | Canonicalize `tracemail-app/`; retain the others as reference until a deliberate archive step |

## Recommended canonical architecture

```text
tracemail-app/ (one React/Vite workbench)
  └─ typed API client and server-state layer
       └─ backend/ (one FastAPI service)
            ├─ case management
            ├─ ingestion adapters
            │    ├─ EMLSource (first)
            │    ├─ RawHeaderSource
            │    ├─ GmailSource (future OAuth)
            │    └─ Microsoft365Source (future OAuth)
            ├─ immutable original evidence store + chain-of-custody events
            ├─ normalized MIME/header/indicator extraction
            ├─ analysis + controlled enrichment
            ├─ evidence-backed decision/correlation
            └─ reports
```

Each adapter should emit a single `RawEmailSource`/acquisition contract with `source_type`, provider/source identifier, acquisition timestamp, raw bytes where available, immutable metadata and provenance.  The forensic pipeline must consume that contract, never provider-specific Gmail fields.  Gmail and Microsoft 365 therefore remain future adapters, not dependencies of the analysis engine.

### Canonical frontend: `tracemail-app/`

Choose `tracemail-app/` because it already exposes all core investigation screens that the root API already or naturally can serve: cases, overview, evidence, identity, infrastructure, graph, campaign, timeline, copilot and report.  Its TypeScript models use the same conceptual shape and naming conventions as root backend Pydantic responses.  It needs a typed API client and data-loading/error/empty/progress states, not a visual rewrite.

`frontend/` has polished mobile interactions and React Flow/Zustand dependencies that may be reused selectively, but it lacks evidence, infrastructure, timeline and copilot pages; its case model is incompatible and mock-centric.  It should not become a competing application.

### Canonical backend: `backend/`

Choose `backend/` because it is the only mounted and runnable FastAPI service with database initialization and end-to-end routes.  Preserve its API shell and incrementally evolve its model and pipeline.  Do not activate the Stitch backend as a second server.  Port individual Stitch modules only after adapting imports, database API style (sync vs async), security controls, test coverage and response contract.

## Existing API map

| Method | Path | Current behavior |
| --- | --- | --- |
| GET | `/api/health` | Liveness response |
| GET | `/api/cases` | Lists stored cases; optional exact `status` filter |
| GET | `/api/cases/{case_id}` | Gets case summary/detail fields |
| POST | `/api/cases/upload` | Accepts `.eml`, synchronously analyzes and creates a case |
| GET | `/api/cases/{case_id}/identity` | Stored identity contradictions and chain |
| GET | `/api/cases/{case_id}/evidence` | Stored findings |
| GET | `/api/cases/{case_id}/headers` | Parsed header display rows plus raw header string |
| GET | `/api/cases/{case_id}/transit-hops` | Partly fabricated transit display data |
| GET | `/api/cases/{case_id}/infrastructure` | Stored one-record IP/infrastructure summary |
| GET | `/api/cases/{case_id}/graph` | On-demand simple graph from case fields |
| GET | `/api/cases/{case_id}/campaign` | One campaign or `null` |
| GET | `/api/cases/{case_id}/timeline` | Stored timeline events |
| GET | `/api/reports/{case_id}` | Retrieves generated text report, otherwise 404 |
| POST | `/api/reports/{case_id}/generate` | Generates/updates text report |
| GET | `/api/copilot/{case_id}/messages` | Retrieves messages; writes greeting on first call |
| POST | `/api/copilot/{case_id}/ask` | Persists question and deterministic keyword response |
| POST | `/api/copilot/{case_id}/suggested-questions` | Returns fixed question list (should be GET) |

## Missing APIs and contracts

The API has no versioning or formal OpenAPI-derived frontend client.  Required next contracts include:

- `POST /api/cases` or `POST /api/ingestions` accepting the normalized source/acquisition contract; keep `.eml` upload as one adapter implementation.
- Case lifecycle endpoints: create, list/filter/paginate, detail, analysis status/progress, retry/failure state and analyst status transition.
- Immutable evidence APIs: evidence metadata/list, original download only with authorization, derived artifacts, hash verification and chain-of-custody events.
- An investigation/overview aggregate endpoint so the UI does not compose inconsistent ad-hoc calls.
- Real parsed Received-chain endpoint; attachments, URLs, IOCs and normalized MIME structure endpoints.
- Persisted, evidence-linked graph/timeline/campaign endpoints with relationship reasons, evidence IDs and confidence.
- Domain/IP enrichment endpoints or asynchronous job resources that identify provider, timestamp, source and limitations.
- Report-download endpoint once PDF generation is integrated.
- Authentication/authorization, user/analyst identity and audit endpoints.
- Ingestion-provider capability, Gmail OAuth start/callback/connection/message-list/select/revoke endpoints **later**, after the common ingestion contract exists.  No Gmail endpoint belongs in the current milestone.

## Database model map

### Root backend (currently used)

| Entity | Purpose |
| --- | --- |
| `Case` | Case summary plus raw EML as decoded text, header block, risk/auth fields and campaign ID |
| `IdentityRecord` | One flattened identity assessment per case |
| `EvidenceFindingRecord` | Derived finding rows |
| `InfrastructureRecord` | One flattened infrastructure row per case |
| `TimelineEventRecord` | Derived events |
| `CampaignRecord` | Campaign summary with JSON arrays/timeline |
| `CopilotMessageRecord` | Conversation messages |
| `ReportRecord` | Generated report text sections |

### Stitch model (not wired to a service)

`Case`, `Evidence`, `Email`, `Header`, `ReceivedHop`, `IOC`, `Infrastructure`, `Campaign`, `CaseCampaign`, `AIFinding`, `AuditLog`, `IdentityAnalysis`, `RiskAssessment`, `AttackHypothesis`, `Signal`, and `TimelineEvent` provide a better long-term normalization direction.  Its `Evidence` model is closer to preservation requirements, but it still needs explicit acquisition source/type/metadata/provenance, processing version, original-message identifier and a non-mutating storage policy.

## Current ingestion and case lifecycle

Today the only user ingestion path is `POST /api/cases/upload` with a filename ending in `.eml`.  It reads the full upload in memory, parses it and stores a replacement-decoded string as `raw_eml` in SQLite.  It assigns the next numeric case number, runs analysis inline, creates related rows, performs campaign correlation, commits, and returns status `analyzed`.

There is no source abstraction, no raw-header-only path, no attachment object preservation, no acquisition metadata, no source identifier, no analyst identity, no processing version, no analysis job state, no immutable evidence vault, and no Gmail/Outlook integration.  Case status is created as `Active`; it does not move through an explicit `acquired → preserving → analyzing → ready/failed → reviewed` lifecycle.

## Exact changes to make the existing system backend-driven

1. Make `tracemail-app/` consume a single typed API client configured by `VITE_API_BASE_URL`; map snake_case responses at the boundary or standardize contracts once.  Remove runtime imports of `src/data/mockData.ts` from production pages.
2. Replace `CasesPage`'s simulated creation with an acquisition chooser.  For the first increment, enable only **Upload .EML** and mark Gmail/Microsoft 365/Header input as unavailable/coming soon; do not make deceptive buttons.
3. Submit the EML through the existing endpoint, display actual server analysis state, then navigate using the returned `case_id`.
4. Load each workstation route by `caseId`, using the existing case, identity, evidence, headers, infrastructure, graph, campaign, timeline, copilot and report endpoints.  Add loading, error, unavailable and empty states.  Do not substitute mock data on API errors.
5. Add a single overview aggregate response (or a frontend query composition layer) and eliminate the mock-only overview fields.  Drive graphs and campaigns from server relationships, not hardcoded nodes/positions/counts.
6. Change the root pipeline to persist raw bytes outside mutable derived analysis records and add `Evidence`, `Acquisition`, `ChainOfCustodyEvent`, `EmailMessage`, `ReceivedHop`, `Indicator`, `AnalysisRun` and relation entities/migrations.  Store hash and byte size before parsing; never rewrite original bytes.
7. Introduce the adapter contract and refactor the current upload endpoint into `EMLSource → RawEmailSource → create case/evidence → analysis run`.  Add `RawHeaderSource` later; Gmail and Microsoft 365 adapters remain out of scope until this passes tests.
8. Port selected Stitch parsing, MIME/attachment, URL, evidence, normalized correlation and PDF components into root `backend/` one at a time.  Do not copy its second database/entrypoint wholesale.
9. Correct unsafe/unsupported claims and introduce evidence provenance, observed/inferred/enriched states, contradictory evidence and attribution limitations in API responses, reports and copilot context.  Treat email bodies as untrusted data and never send them to a reasoning model as instructions.
10. Add migrations, configuration via environment variables, bounded uploads, MIME/parser error handling, safe async enrichment with SSRF/egress controls, authentication/authorization and tests before external provider integration.

## Technical risks

- Raw email is decoded and stored as text, so byte-exact original evidence and its verifiable hash relationship are not robustly preserved.
- Uploads are unbounded in memory and parsed directly; malformed/oversized MIME, attachment handling and content sanitization controls are absent.
- HTML body handling must never be rendered unsanitized, load remote content, fetch URLs, or act as prompt instructions.
- The synchronous public geolocation lookup can block requests and can query private/reserved addresses.  It has no audit provenance or controlled egress policy.
- SQLite relative database paths vary with process working directory; neither backend specifies migrations, retention, backups or production storage.
- Root and Stitch databases use incompatible schemas and database styles; attempting to run both will split case data and forensic truth.
- The CORS allowlist is development-only and authentication/authorization is absent.
- Some reports/copilot responses overclaim from missing evidence, which is incompatible with forensic requirements.
- No root automated tests exist.  The only test-like file is `stitch_.../backend/test_intel.py`; it is outside a configured test suite.
- There are no reproducible dependency/environment instructions, and frontends include both installed dependencies and build outputs in-tree.

## Keep, merge, deprecate

**Keep now:** root FastAPI shell/routes/models as the execution base; `tracemail-app` page/layout/design system; research brief; Stitch design screenshots/HTML; selected Stitch forensic helpers as reference; existing mocks only as isolated fixture/design references.

**Merge incrementally:** Stitch MIME/attachment parsing, evidence storage ideas, Received-chain parsing, URL/IP/domain intelligence, correlation/risk/explainability output and PDF reporting into the root backend under one schema and one async persistence strategy.

**Deprecate after the real path is proven:** `frontend/` as a competing executable UI; `tracemail-app/src/data/mockData.ts` as runtime production input; `frontend/src/data/mockCase1042.ts`, `mockCases.ts` and `mockAnalysis.ts` as runtime production input; root fabricated transit/graph/report/copilot assertions; Stitch's standalone storage/runtime as a competing backend.  Do not delete these artifacts until the API-driven replacement has automated coverage and the team approves archival/removal.

## Recommended development sequence

1. **Backend-driven EML vertical slice:** canonicalize `tracemail-app` against the existing root API, with no mocks on the demo path.  Add the New Investigation chooser with EML as the working option.
2. **Forensic integrity foundation:** migrate to immutable original evidence bytes, acquisition/provenance/chain-of-custody records, parsed/derived separation and explicit case/analysis lifecycle.
3. **Analysis correctness and safety:** harden parser boundaries; persist real Received hops, MIME attachments, URLs/IOCs and evidence-backed findings; replace fabricated claims and unsafe enrichment.
4. **Investigation data model:** persist graph relations, timeline, infrastructure enrichment and campaign match reasons; upgrade report and copilot to cite only stored findings and limitations.
5. **Test suite and reproducibility:** fixtures for the required legitimate, phishing, spoofing, BEC, invoice, credential, URL, attachment and campaign cases; unit, API and frontend integration tests; documented clean startup.
6. **Provider abstraction:** finalize/test `RawEmailSource`, then add Gmail OAuth and raw-message retrieval as an adapter.  Add Microsoft 365 only after the Gmail path and shared contract are stable.

## Recommended next implementation step

Implement the first vertical slice: **make `tracemail-app` API-backed using the existing root FastAPI `.eml` workflow**, while adding a truthful New Investigation acquisition chooser.  This removes the most visible mock dependency, validates the canonical frontend/backend pairing, and creates a safe foundation for the evidence/ingestion refactor that must precede Gmail OAuth.

## Phase 1 update — 2026-09-11

Phase 1 implemented the canonical EML vertical slice without introducing Gmail or Microsoft 365 integration.

- `tracemail-app` now has one centralized API layer and its case, overview, identity, evidence, infrastructure, graph, campaign, timeline, report and copilot routes load backend data. The old mock module remains in the repository only as an isolated reference; it is not imported by the canonical investigation workflow.
- The New Investigation dialog offers Upload `.EML` as the only working acquisition route. Gmail, Microsoft 365 and header paste are explicitly marked coming soon.
- The backend now records `eml_upload` source provenance and stores byte-exact uploaded content in a separate `EvidenceRecord` BLOB with its SHA-256, filename, MIME type, size, ingestion timestamp and preserved status. Parsed and derived analysis remain in their existing records.
- The upload response now includes case number, source type, evidence ID and completed analysis status while retaining the legacy `case_id`, `status` and `message` fields.
- A 10 MB upload limit and useful empty/invalid/malformed upload errors were added. The analysis remains synchronous; the UI shows completed-request transition rather than a fabricated background job.
- The campaign timeline response mismatch found during integration testing was corrected.

Remaining gaps: existing installations need a proper migration path (Phase 1 relies on SQLAlchemy create-on-start for a clean database); original bytes are stored in SQLite rather than a dedicated immutable object store; Received-hop/graph quality and report/copilot evidence claims still need further hardening; no authorization, async job state, provider adapter, or full MIME/attachment/IOC persistence exists yet.

Tests: `python -m unittest tests.test_eml_vertical_slice -v` passed for valid EML upload, case creation, evidence byte/hash preservation, investigation endpoints, report generation and invalid-file rejection. `npm run build` in `tracemail-app` passed.
