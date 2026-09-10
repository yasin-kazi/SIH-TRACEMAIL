# TraceMail Phase 2 Status

## PHASE 2 — MILESTONE 1: EmailSource capture + forensic evidence records: COMPLETE

See the migration-friendly summary in this file under "MILESTONE 1 SHIPPED".

## PHASE 2 — MILESTONE 2: Expose normalized forensic evidence: COMPLETE

The normalized forensic records (MIME parts, received hops, attachments,
observable IOCs, evidence relationships) from Milestone 1 are now exposed
through read-only APIs and rendered from persisted records in the canonical
`tracemail-app` investigation workspace.

## PHASE 2 — MILESTONE 3: Report/Copilot evidence query migration: COMPLETE

Report and Copilot now read the persisted forensic records through a single
read-only, case-scoped **evidence query layer** (`backend/services/
evidence_queries.py`) and never invent forensic facts. See "MILESTONE 3
SHIPPED" below.

## PHASE 3 — Gmail acquisition: ARCHITECTURE AUDIT COMPLETE (design only)

The pre-implementation architecture and security audit for the first direct
mailbox source (Gmail OAuth + raw-message acquisition) is complete. The design
baseline is `docs/GMAIL_ACQUISITION_DESIGN.md`. **No application code, models,
OAuth flow, or credentials were created.** Implementation, when approved,
starts from that document's "Minimum implementation plan" (§12) and adds
`GmailSource` as a new `EmailSource` adapter against the unchanged forensic
pipeline.

## ARCHITECTURE

```
                  Evidence DB
                      │
          ┌───────────┼────────────┐
          ▼           ▼            ▼
   evidence query layer
          │  ▲        │            ▲
          ▼  │        ▼            │
         API ┐     Report       Copilot
          │  │        │            │
          ▼  └─────────┴────────────┘
      TraceMail UI
```

The normalized forensic records are the single source of truth. Report and
Copilot (and the read endpoints) resolve MimePart/Hop/Attachment/IOC/
Relationship/Summary records through the evidence query layer; derived
Phase-1 analysis records (Case, EvidenceFinding, Identity, Infrastructure,
Campaign, Timeline) are still read directly by those services.

## DONE

### Read-only forensic API (`backend/routers/cases.py`, `backend/schemas.py`)

- `GET /api/cases/{case_id}/mime-parts` → `MimePartOut[]` (id, part_index,
  parent_id, depth, content_type, disposition, filename, content_id, size,
  transfer_encoding, is_attachment).
- `GET /api/cases/{case_id}/attachments` → `AttachmentOut[]` (id, filename,
  content_type, size, disposition, content_id, sha256). Metadata only — no
  payload bytes are returned.
- `GET /api/cases/{case_id}/iocs` → `IocOut[]` (id, type, value, source).
  IOCs are observables; the response carries no `malicious`/verdict fields.
- `GET /api/cases/{case_id}/relationships` → `EvidenceRelationshipOut[]`
  (id, relation_type, source_type = evidence.evidence_type, source_id,
  target_type, target_id).
- `GET /api/cases/{case_id}/forensic-summary` → `ForensicSummary` (original
  evidence provenance from `SourceRecord`/`EvidenceRecord` plus counts:
  mime_parts, received_hops, attachments, iocs — always from persisted rows).
- Received hops are exposed by the existing `GET /api/cases/{case_id}/transit-hops`
  endpoint, which already returns the persisted `ReceivedHopRecord` fields
  (sequence, raw_header, from_host, by_host, source_ip, protocol, timestamp).
  No duplicate `received-hops` route was added.
- All endpoints are read-only, 404 on unknown case, return `[]`/zero summary
  when no forensic records were persisted, and query the **latest** evidence
  record for the case.

### Evidence query layer (`backend/services/evidence_queries.py`)

Read-only, case-scoped access to the normalized forensic records. Every query
is confined to the latest preserved `EvidenceRecord` for a case, returns
observables/metadata only, and never loads payload bytes, executes content, or
fetches URLs:

- `get_case`, `get_latest_evidence`, `get_source`
- `get_mime_parts`, `get_received_hops`, `get_attachments`, `get_iocs`,
  `get_relationships`
- `get_evidence_summary` (original provenance + persisted counts)

`routers/cases.py` forensic endpoints, `report_service.py`, and
`copilot_service.py` all resolve forensic data through this layer — there is no
parallel SQL path for the normalized forensic records.

### Report migration (`backend/services/report_service.py`)

- The report now cites persisted forensic rows with their record ids:
  "Preserved original evidence (record …)", "hop record …", "attachment
  record …", plus SHA-256 values, MIME structure, Received chain, attachments,
  and extracted observables.
- The executive summary includes persisted counts (MIME parts / attachments /
  observed transmission hops / extracted observables).
- Evidence vs inference is explicit: the attack path labels each step
  `[observed]` or `[inference]`, infrastructure analysis reports observed
  transmission hop IPs, and the conclusion states "attribution to any specific
  individual or group is not established".
- Forbidden inventions removed/qualified: no registration claims, no
  "intentional impersonation" as established fact, no threat-feed claim when
  none is recorded, no attacker identity.

### Copilot migration (`backend/services/copilot_service.py`)

Rule-based (no LLM). New/updated evidence-grounded answers using the query
layer, while the existing risk/identity/infra/campaign/uncertainty/auth/
timeline branches and response contract are preserved:

- `What attachments are present?` → persisted attachment metadata + SHA-256 +
  record ids ("payloads are never opened or executed").
- `Show me the Received chain` → persisted hops (from/by/via/protocol) with
  record ids.
- `What observables were extracted?` → grouped IOC values with an explicit
  "not verdicts" caveat.
- `What IPs were observed?` → observed IPs from Received hops + IOC IP records.
- Domain/WiOS answers list all observed domains (From, Reply-To, Return-Path,
  IOC domains) and state WHOIS/RDAP "was not queried … NOT established".
- The evidence answer now includes observed facts from the preserved evidence.

### Evidence page (`tracemail-app/src/pages/EvidencePage.tsx`)

Rebuilt onto persisted records using the existing visual language:
- **Original evidence** — source type, method, identifier, filename, content
  type, size, acquisition time, SHA-256 (from `forensic-summary`).
- **Forensic counts** — MIME parts, received hops, attachments, observables.
- **Derived findings**, **Headers** (existing sections preserved).
- **MIME structure**, **Received chain**, **Attachments**, **Observables / IOCs**,
  **Evidence relationships** (new sections, all from persisted records).
- No forensic value is hardcoded; every number and value comes from the API.

### Case overview (`tracemail-app/src/pages/OverviewPage.tsx`)

Added a compact evidence summary block rendered only from the backend
`forensic-summary` response (MIME parts / received hops / attachments /
observables counts). No client-side forensic computation.

### Frontend API client (`tracemail-app/src/api/cases.ts`)

Centralized typed functions added: `getMimeParts`, `getAttachments`, `getIOCs`,
`getRelationships`, `getForensicSummary`; `getTransitHops` now returns a richer
typed `TransitHop[]`. No `fetch()` calls were added to components; the existing
conventions were reused. Report/Copilot response contracts are unchanged, so no
frontend change was needed for Milestone 3.

### Tests (`backend/tests/test_eml_vertical_slice.py`)

- Milestone 2 test: `test_forensic_apis_expose_persisted_records` — MIME,
  transit-hops, attachments, IOCs, relationships, summary, and 404 behavior.
- Milestone 3 test: `test_report_and_copilot_are_evidence_grounded` —
  1. Report reflects persisted evidence (counts, filenames, observed IPs,
     observables, SHA-256, record ids).
  2. Report contains no unsupported claims ("registered", "has been flagged in",
     "privacy proxy registration", "the attacker", "intentional impersonation").
  3. Copilot answers attachment / Received-chain / observable / IP / domain
     questions from persisted rows.
  4. A domain question states registration "was not queried … not established".
  5. Case-scoping: another case never leaks this case's records.
  6. Deleting persisted rows changes attachments/summary/report/copilot output.
- Full suite: **6/6 pass**.

### Frontend verification

- `npm run build` (tsc + vite) passes.
- `grep` for `mockData|mockCase|mockCases|mockAnalysis|1042` in `tracemail-app/src`
  returns **no references**; the canonical app contains no mock or hardcoded
  forensic values.

### API documentation (`docs/API_CONTRACT.md`)

Documented the new endpoints with method, path, purpose, response shape, and
error behavior, plus the "transit-hops doubles as the received-hops API"
decision and the ICD security contract (observables only, no payload bytes).
Milestone 3 (Steps 4-7) did not change any API contract; the report/copilot
request/response shapes are unchanged.

## IN PROGRESS

- Nothing. Milestone 3 is complete.

## NOT STARTED

- Gmail OAuth / message picker / raw-message adapter.
- Microsoft 365 OAuth / message adapter.
- Header-paste ingestion adapter.
- AI model router / multi-model reasoning.
- Authentication / RBAC.
- Audit trail / activity log.
- Background jobs (async analysis).
- Object storage / WORM policy.
- Blockchain / integrity anchoring.
- Production deployment / Alembic-managed migrations.

## MILESTONE 3 SHIPPED

**Before (Milestone 2 ended):** report/copilot read only derived Phase-1
records (Case, Identity, EvidenceFinding, Infrastructure, Campaign, Timeline)
and had no access to the normalized forensic records.

**Now:**

```
persisted forensic records (mime_parts, received_hops,
   attachments, iocs, relationships)
        ↓
evidence query layer (read-only, observable-first, case-scoped)
        ↓
router read APIs / report_service / copilot_service
```

- `backend/services/evidence_queries.py` added; owned by all three consumers.
- Report and Copilot cite persisted forensic rows (with record ids) and label
  observation vs inference; unsupported forensic facts are not asserted.
- No LLM, no external provider; Copilot remains fully rule-based.
- Response contracts unchanged; the frontend required no changes.

## MILESTONE 1 SHIPPED (recap)

- `EmailSource` contract + `EMLSource` (only functional adapter).
- `ingest_acquired_email` source-agnostic pipeline.
- 5 additive forensic tables: `mime_parts`, `received_hops`, `attachments`,
  `iocs`, `evidence_relationships`, plus a `contains` relationship per child.
- Transit-hops endpoint backed by persisted `ReceivedHopRecord` with legacy
  fallback. Migration is additive-only (verified against the existing dev DB).

## KNOWN LIMITATIONS (accepted for Milestone 3)

- Forensic records are snapshotted at ingestion; reads serve the latest
  preserved evidence record for a case.
- Only `EMLSource` is functional; other acquisition adapters are future work.
- Report output text is plain strings (existing `ReportRecord` schema); record
  ids are embedded in the text rather than structured fields. If structured
  traceability is required later, it is a response-contract change and would be
  done in a dedicated milestone.
- Derived Phase-1 records (EvidenceFinding, Identity, Infrastructure, Campaign,
  Timeline) are still read directly by report/copilot rather than through the
  query layer; the query layer owns the *normalized forensic* records.
- IOC `hash` type is reserved by the schema but no hash extraction is wired yet
  (attachment SHA-256 lives on `attachments`).
- No Alembic; additive-only migration relies on `create_all`.