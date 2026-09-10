# TraceMail Phase 1 Status

## PHASE 1: COMPLETE

Phase 1 scope is the real `.EML → real investigation` vertical slice. All of the
following are shipped and verified by `backend/tests/test_eml_vertical_slice.py`:

- New Investigation UI exists (`tracemail-app`, canonical frontend).
- `.eml` upload works and creates a real backend case with a real case ID.
- Original uploaded bytes are preserved byte-for-byte in `EvidenceRecord.original_bytes`.
- SHA-256 is calculated from the original uploaded bytes before any parsing.
- Source type is recorded as `eml_upload` on both `Case` and `SourceRecord`.
- Existing deterministic forensic analysis runs on the uploaded EML (identity chain,
  typosquatting, Reply-To mismatch, auth results, source IP, risk scoring, findings,
  timeline, campaign correlation).
- Canonical `tracemail-app` uses backend APIs only (centralized typed client in
  `src/api/`), and every investigation page loads real backend data with
  loading/error/empty states.
- Report and Copilot are evidence-referenced: they read real case, evidence, identity,
  infrastructure, campaign and timeline records, and no longer emit assertions
  unsupported by observed data.
- Transit hops are derived strictly from the Received headers present in the EML.
  No hostname, IP, organization or location is invented; hops that the EML does not
  establish are omitted rather than fabricated.
- No mock data is required for the investigation workflow. `mockData.ts` has been
  removed; production routes never import it and there is no API fallback to mocks.
- Backend vertical-slice tests pass (`unittest`, 3 tests, endpoint reachability,
  byte preservation, SHA-256 correctness, and data honesty).

## WORKFLOW STATUS

Canonical frontend: `tracemail-app/`
Legacy frontend: `frontend/` — **deprecated mock implementation** (hardcoded
case-1042 data, Zustand-based `useCaseStore` always selects `mockCase1042`, mock
analysis animation). It is not the canonical UI, does not call the backend, and is
kept only for reference until removal is approved.

Backend flow: upload → case created → evidence preserved → analysis records
persisted → investigation pages read live API data → report/copilot respond from
database records.

## KNOWN LIMITATIONS (accepted for Phase 1)

- Analysis is synchronous. `analysis_status: completed` means the upload request
  completed, not that a background job ran.
- Original evidence bytes are preserved in SQLite for this Phase 1 slice; there is
  no object-store WORM policy yet.
- The transit-hop endpoint reports only hops present in the EML's Received headers;
  Emails without Received headers show an empty transit chain by design.
- Report/copilot describe only what the current heuristics observed; WHOIS/RDAP
  registration data, live DNS authentication checks and threat-intel feed lookups
  are not performed in this phase, and output avoids claiming them.

## FUTURE PHASES (out of Phase 1 scope)

- Gmail OAuth / message picker / raw-message adapter.
- Microsoft 365 OAuth / message adapter.
- Header-paste ingestion adapter.
- `EmailSource` abstraction expansion (shared source contract across providers).
- Persisted parsed MIME, attachment, IOC and relationship records.
- Database migration strategy for existing databases.
- Authentication / authorization / RBAC and complete analyst identity.
- Full audit trail.
- Background analysis jobs and progress state.
- Object storage / WORM / production-scale evidence storage and retention policy.
- AI model router and multi-model analysis.
- Blockchain.
- Production deployment.