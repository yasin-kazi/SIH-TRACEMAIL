# TraceMail API Contract (Phase 1 baseline + Phase 2 forensic records)

Base URL defaults to `http://localhost:8000` (the frontend reads `VITE_API_BASE_URL` when set). All responses are JSON except multipart upload requests. Error responses use FastAPI's `{ "detail": "..." }` shape.

## Email source acquisition

Uploads are captured through an `EmailSource` abstraction. The pipeline only ever consumes a normalized `AcquiredEmail` (`source_type`, `source_identifier`, `original_filename`, `content_type`, `raw_bytes`, `acquisition_method`, `metadata`) and never inspects the transport it arrived on. The only functional adapter today is `EMLSource` (`source_type: "eml_upload"`, `acquisition_method: "upload"`); Gmail/Microsoft 365 adapters are future work. The `source_type` value is stable in `UploadResponse`, `Case`, `SourceRecord`, and `EvidenceRecord`.

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
