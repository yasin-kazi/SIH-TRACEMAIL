# TraceMail API Contract (Phase 1 baseline + Phase 2 forensic records + Phase 3 Gmail)

Base URL defaults to `http://localhost:8000` (the frontend reads `VITE_API_BASE_URL` when set). All responses are JSON except multipart upload requests. Error responses use FastAPI's `{ "detail": "..." }` shape.

## Email source acquisition

Uploads are captured through an `EmailSource` abstraction. The pipeline only ever consumes a normalized `AcquiredEmail` (`source_type`, `source_identifier`, `original_filename`, `content_type`, `raw_bytes`, `acquisition_method`, `metadata`) and never inspects the transport it arrived on. Two functional adapters exist: `EMLSource` (`source_type: "eml_upload"`, `acquisition_method: "upload"`) and `GmailSource` (`source_type: "gmail"`, `acquisition_method: "gmail_oauth"`, `content_type: "message/rfc822"`, `original_filename: ""`). Microsoft 365 is future work. The `source_type` value is stable in `UploadResponse`, `Case`, `SourceRecord`, `EvidenceRecord`, and the forensic read APIs. For a Gmail case, `source_identifier` is the provider message id — provenance of the message, not proof of sender authenticity.

## Cases

| Endpoint | Request | Success response | Errors | Database objects | Frontend consumer |
| --- | --- | --- | --- | --- | --- |
| `GET /api/cases` | Optional `status` query | `CaseResponse[]` | none explicitly raised | `Case` | Cases list |
| `GET /api/cases/{case_id}` | path ID | `CaseResponse` | 404 | `Case` | Overview/context |
| `POST /api/cases/upload` | `multipart/form-data`, required `file` ending `.eml` | `UploadResponse`: case ID/number, active status, `eml_upload` source, evidence ID and completed analysis state | 400 invalid extension/size, 422 malformed message | `Case`, `SourceRecord`, `EvidenceRecord`, `IdentityRecord`, `EvidenceFindingRecord`, `InfrastructureRecord`, `TimelineEventRecord`, `CampaignRecord`, `MimePartRecord`, `ReceivedHopRecord`, `AttachmentRecord`, `IOCRecord`, `EvidenceRelationshipRecord` | New Investigation |
| `GET /api/cases/{case_id}/identity` | path ID | `IdentityResponse` | 404 | `IdentityRecord` | Identity |
| `GET /api/cases/{case_id}/evidence` | path ID | `EvidenceFindingResponse[]` | none (empty list allowed) | `EvidenceFindingRecord` | Evidence/overview |
| `GET /api/cases/{case_id}/mime-parts` | path ID | `MimePartOut[]` | 404 if case absent | `MimePartRecord` (latest evidence) | Evidence |
| `GET /api/cases/{case_id}/attachments` | path ID | `AttachmentOut[]` | 404 if case absent | `AttachmentRecord` (latest evidence) | Evidence |
| `GET /api/cases/{case_id}/iocs` | path ID | `IocOut[]` | 404 if case absent | `IOCRecord` (latest evidence) | Evidence |
| `GET /api/cases/{case_id}/relationships` | path ID | `EvidenceRelationshipOut[]` | 404 if case absent | `EvidenceRelationshipRecord`, `EvidenceRecord` | Evidence |
| `GET /api/cases/{case_id}/forensic-summary` | path ID | `ForensicSummary` | 404 if case absent, empty summary if no preserved evidence | `SourceRecord`, `EvidenceRecord`, persisted counts | Evidence, Overview |
| `GET /api/cases/{case_id}/headers` | path ID | `{headers, raw}` | 404 | `Case.raw_headers` | Evidence |
| `GET /api/cases/{case_id}/transit-hops` | path ID | `{hops}` | 404 | `ReceivedHopRecord` (Phase-2 uploads), falls back to `EvidenceRecord`/`Case` for pre-Phase-2 cases | Evidence |
| `GET /api/cases/{case_id}/infrastructure` | path ID | `InfrastructureResponse` | 404 | `InfrastructureRecord` | Infrastructure |
| `GET /api/cases/{case_id}/graph` | path ID | `{nodes, edges}` | 404 | `Case`, `InfrastructureRecord` | Graph |
| `GET /api/cases/{case_id}/campaign` | path ID | `CampaignResponse` or `null` | none | `Case`, `CampaignRecord` | Campaign |
| `GET /api/cases/{case_id}/timeline` | path ID | `TimelineEventResponse[]` | none (empty list allowed) | `TimelineEventRecord` | Timeline |

`CaseResponse` contains the stored case summary, sender/authentication/risk fields and source/evidence metadata. It deliberately does not return raw email bytes.

### Transit hops (Phase 2 behavior)

For cases ingested in Phase 2 the endpoint now serves persisted `ReceivedHopRecord` rows ordered by `sequence`, each carrying `label`, `ip`, `description`, `hop_type` plus richer observed fields (`raw_header`, `from_host`, `by_host`, `source_ip`, `protocol`, `timestamp`). The four legacy fields remain present so the frontend contract is unchanged. Pre-existing cases fall back to deriving hops live from their preserved EML; empty hop lists are returned when no `Received` headers exist.

The transit-hops endpoint is also the read-only "received hops" API — it exposes the persisted received-hop records, so no duplicate `received-hops` route was added.

### Forensic evidence read APIs (Phase 2 Milestone 2)

All are read-only, query the **latest** preserved evidence record for the case, and return `[]` (never 404) when no forensic records were persisted for the case. Case not found returns 404. These endpoints return observables and metadata as *data*, never as instructions, and never return attachment payload bytes.

- `GET /api/cases/{case_id}/mime-parts` — persisted MIME part metadata: `{ id, part_index, parent_id, depth, content_type, disposition, filename, content_id, size, transfer_encoding, is_attachment }`.
- `GET /api/cases/{case_id}/attachments` — persisted attachment metadata only: `{ id, filename, content_type, size, disposition, content_id, sha256 }`. The SHA-256 covers the transfer-decoded payload; payload bytes are never returned.
- `GET /api/cases/{case_id}/iocs` — observable indicators: `{ id, type, value, source }` where `type` is ip / domain / url / email / message_id / hash. An IOC is an observable; the response carries no verdict (no `malicious` field).
- `GET /api/cases/{case_id}/relationships` — consists-of links: `{ id, relation_type, source_type, source_id, target_type, target_id }`, where `source_type` is the evidence record's `evidence_type` and `source_id` its id.
- `GET /api/cases/{case_id}/forensic-summary` — original evidence provenance plus counts from persisted records: `{ case_id, evidence_id, source_type, source_identifier, acquisition_method, acquisition_timestamp, content_type, original_filename, size, sha256, mime_parts, received_hops, attachments, iocs }`. Counts are always derived from persisted rows, never client-side.

## Gmail acquisition (Phase 3)

Connection and picker are served by `GET /api/gmail/*`; selected-message analysis reuses `POST /api/gmail/analyze`. The OAuth client secret and tokens are server-side only (tokens encrypted at rest as `v1:` AES-256-GCM blobs); no code, token, or secret ever appears in a response or a redirect URL. The auth URL carries only the public `client_id`, the least-privilege `gmail.readonly` scope, an expiring single-use `state`, and a PKCE `code_challenge`.

| Endpoint | Request | Success response | Errors | Notes |
| --- | --- | --- | --- | --- |
| `GET /api/gmail/status` | none | `{ connected, source, status, account }` | none | `status` = missing/valid/expired/revoked; `account` = connected authorized email or null |
| `GET /api/gmail/auth/start` | none | `{ auth_url }` | 503 unconfigured (`TRACEMAIL_GMAIL_CLIENT_ID`/`SECRET` missing) | Auth URL includes `gmail.readonly` scope, `state`, `code_challenge`, `code_challenge_method=S256`, `access_type=offline` |
| `GET /api/gmail/oauth/callback` | query `code`, `state`, optional `error` | `303` to `{frontend_origin}/investigation?connect=success|denied|invalid|expired|error` | state tampered/reused/expired → `?connect=invalid|expired`; no exchange | Server-side code exchange; persists encrypted tokens |
| `POST /api/gmail/revoke` | none | `{ status: "disconnected" }` | none | Best-effort Google revoke + delete all `gmail_connections` rows |
| `GET /api/gmail/search` | `q` (Gmail query syntax), `page_token`, `max_results` (≤50, default 10) | `{ messages: GmailMessageOut[] , next_page_token, result_size_estimate }` | 401 not connected/refresh failed, 429 rate limit, 502 provider error | Metadata rows only (id, threadId, snippet, From/Subject/Date, sizeEstimate); never bodies |
| `GET /api/gmail/messages/{message_id}/metadata` | path ID | `GmailMessageOut` | 404 not found | `format=metadata`; no raw/body/payload fields |
| `POST /api/gmail/analyze` | `{ "message_id": string }` | `UploadResponse` (`source_type: "gmail"`, `analysis_status: "completed"`) | 400 invalid, 401 reconnect required, 403 permission, 404 message no longer available, 409 already analyzed as case X, 413 oversized (≥25 MB default cap), 422 malformed base64/unparsable, 429 rate limit, 502 provider/server/network | Fetches `format=raw` only, strict base64url decode, SHA-256 pre-parse, exact bytes → `EvidenceRecord`, then the existing `ingest_acquired_email()` pipeline |

`GmailMessageOut` fields: `{ id, thread_id, snippet, from_address, subject, date, internal_date_ms, size_estimate }`. `POST /api/gmail/analyze` returns the standard `UploadResponse` shape through the server-side duplicate check (`409` keyed on `SourceRecord(source_type="gmail", source_id=message_id)`).

## Reports

| Endpoint | Request | Success response | Errors | Database objects | Frontend consumer |
| --- | --- | --- | --- | --- | --- |
| `GET /api/reports/{case_id}` | path ID | `ReportResponse` | 404 if not generated | `ReportRecord` | Report |
| `POST /api/reports/{case_id}/generate` | path ID | `ReportResponse` | 404 if case absent | `Case`, analysis records, `ReportRecord` | Report generate button |

## Copilot

| Endpoint | Request | Success response | Errors | Database objects | Frontend consumer |
| --- | --- | --- | --- | --- | --- |
| `GET /api/copilot/{case_id}/messages` | path ID | `CopilotMessageResponse[]`; first read writes a greeting | none | `CopilotMessageRecord` | Copilot |
| `POST /api/copilot/{case_id}/ask` | `{ "question": string }` | `CopilotMessageResponse` | case absence is returned as message content today | `CopilotMessageRecord`, analysis records | Copilot |
| `POST /api/copilot/{case_id}/suggested-questions` | path ID | `{questions: string[]}` | none | none | Copilot |

## Health

`GET /api/health` returns `{ "status": "ok", "service": "tracemail-ai" }`; the frontend may use it for diagnostics but does not use it as data fallback.

## Contract limitations

The analysis is synchronous in Phase 1. `analysis_status: "completed"` means the upload request returned only after the existing parser and heuristic pipeline completed; it does not imply a background job system. Transit hops and the graph remain limited by the existing backend model and are documented as observed/derived by their individual records. IOC records contain observables only (values, types, and the header/part they were seen in); no IOC is marked malicious or attributed based solely on being extracted.
