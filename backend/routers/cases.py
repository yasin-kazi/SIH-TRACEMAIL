"""Cases CRUD + .eml upload + full analysis orchestration."""
from __future__ import annotations
import json
from typing import Optional
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import (
    Case, IdentityRecord, EvidenceFindingRecord, EvidenceRecord,
    InfrastructureRecord, TimelineEventRecord,
)
from schemas import (
    CaseResponse, UploadResponse, IdentityResponse,
    EvidenceFindingResponse, EmailHeaderOut, TransitHopOut,
    InfrastructureResponse, GraphNodeOut, GraphEdgeOut,
    CampaignResponse, CampaignTimelineEventOut,
    TimelineEventResponse, MimePartOut, AttachmentOut, IocOut,
    EvidenceRelationshipOut, ForensicSummary,
)
from services import evidence_queries
from services.sources import EMLSource
from services.email_parser import extract_received_hops_from_text
from services.ingest_email import ingest_acquired_email, UnparsableEmail
import json as _json

router = APIRouter(prefix="/api/cases", tags=["cases"])
MAX_EML_SIZE_BYTES = 10 * 1024 * 1024


@router.get("", response_model=list[CaseResponse])
async def list_cases(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(Case).order_by(Case.number.desc())
    if status:
        q = q.where(Case.status == status)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(case_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "Case not found")
    return case


@router.post("/upload", response_model=UploadResponse)
async def upload_eml(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".eml"):
        raise HTTPException(400, "Please upload a valid .eml file")

    raw_bytes = await file.read()
    if not raw_bytes:
        raise HTTPException(400, "The uploaded .eml file is empty")
    if len(raw_bytes) > MAX_EML_SIZE_BYTES:
        raise HTTPException(400, "The uploaded .eml exceeds the 10 MB limit")

    # Source capture: wrap the raw bytes + file metadata in the normalized
    # EmailSource contract, then hand the normalized acquisition to the
    # source-agnostic forensic pipeline.
    acquired = EMLSource(
        filename=file.filename,
        raw_bytes=raw_bytes,
        content_type=file.content_type or "message/rfc822",
    ).acquire()

    try:
        result = await ingest_acquired_email(db, acquired)
    except UnparsableEmail as exc:
        raise HTTPException(422, str(exc)) from exc

    return UploadResponse(
        case_id=result["case_id"],
        case_number=result["case_number"],
        status="active",
        source_type=acquired.source_type,
        evidence_id=result["evidence_id"],
        analysis_status="completed",
        message=(
            f"Analysis complete. Threat: {result['threat_type']}, "
            f"Risk: {result['risk_level']} ({result['risk_score']}/100)"
        ),
    )


# ─── Analysis Endpoints ───────────────────────────────────────

@router.get("/{case_id}/identity", response_model=IdentityResponse)
async def get_identity(case_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(IdentityRecord).where(IdentityRecord.case_id == case_id))
    identity = result.scalar_one_or_none()
    if not identity:
        raise HTTPException(404, "Identity analysis not found")
    return IdentityResponse(
        case_id=identity.case_id,
        score=identity.score,
        display_name=identity.display_name,
        from_address=identity.from_address,
        from_domain=identity.from_domain,
        reply_to=identity.reply_to,
        reply_to_domain=identity.reply_to_domain,
        return_path=identity.return_path,
        return_path_domain=identity.return_path_domain,
        dkim_domain=identity.dkim_domain,
        source_ip=identity.source_ip,
        source_asn=identity.source_asn,
        source_location=identity.source_location,
        source_provider=identity.source_provider,
        contradictions=[
            IdentityResponse.__annotations__["contradictions"]  # type: ignore
        ] if False else _parse_json_list(identity.contradictions_json),
        chain=_parse_json_list(identity.chain_json),
    )


@router.get("/{case_id}/evidence", response_model=list[EvidenceFindingResponse])
async def get_evidence(case_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(EvidenceFindingRecord).where(EvidenceFindingRecord.case_id == case_id)
    )
    findings = result.scalars().all()
    return [
        EvidenceFindingResponse(
            id=f.finding_id,
            title=f.title,
            description=f.description,
            severity=f.severity,
            risk_badge=f.risk_badge,
            code=f.code,
            evidence_state=f.evidence_state,
            confidence=f.confidence,
            source=f.source,
            tags=_json.loads(f.tags_json or "[]"),
            color_accent=f.color_accent,
        )
        for f in findings
    ]


# ─── Forensic evidence read APIs ───────────────────────────────
# Read-only views over the persisted normalized forensic records.
# These values are observables and metadata; none of it implies a verdict.

@router.get("/{case_id}/mime-parts", response_model=list[MimePartOut])
async def get_mime_parts(case_id: str, db: AsyncSession = Depends(get_db)):
    evidence = await _require_evidence(db, case_id)
    if evidence is None:
        return []
    parts = await evidence_queries.get_mime_parts(db, case_id)
    return [
        MimePartOut(
            id=p.id,
            part_index=p.part_index,
            parent_id=p.parent_index,
            depth=p.depth,
            content_type=p.content_type,
            disposition=p.disposition,
            filename=p.filename,
            content_id=p.content_id,
            size=p.size,
            transfer_encoding=p.transfer_encoding,
            is_attachment=p.is_attachment,
        )
        for p in parts
    ]


@router.get("/{case_id}/attachments", response_model=list[AttachmentOut])
async def get_attachments(case_id: str, db: AsyncSession = Depends(get_db)):
    evidence = await _require_evidence(db, case_id)
    if evidence is None:
        return []
    attachments = await evidence_queries.get_attachments(db, case_id)
    return [
        AttachmentOut(
            id=a.id,
            filename=a.filename,
            content_type=a.mime_type,
            size=a.size,
            disposition=a.disposition,
            content_id=a.content_id,
            sha256=a.sha256,
        )
        for a in attachments
    ]


@router.get("/{case_id}/iocs", response_model=list[IocOut])
async def get_iocs(case_id: str, db: AsyncSession = Depends(get_db)):
    evidence = await _require_evidence(db, case_id)
    if evidence is None:
        return []
    iocs = await evidence_queries.get_iocs(db, case_id)
    # An IOC is an observable: type, value and where it was seen. No IOC is
    # labelled malicious by the extraction process.
    return [IocOut(id=i.id, type=i.ioc_type, value=i.value, source=i.source) for i in iocs]


@router.get("/{case_id}/relationships", response_model=list[EvidenceRelationshipOut])
async def get_relationships(case_id: str, db: AsyncSession = Depends(get_db)):
    evidence = await _require_evidence(db, case_id)
    if evidence is None:
        return []
    relationships = await evidence_queries.get_relationships(db, case_id)
    return [
        EvidenceRelationshipOut(
            id=r.id,
            relation_type=r.relation_type,
            source_type=evidence.evidence_type,
            source_id=evidence.id,
            target_type=r.target_type,
            target_id=r.target_id,
        )
        for r in relationships
    ]


@router.get("/{case_id}/forensic-summary", response_model=ForensicSummary)
async def get_forensic_summary(case_id: str, db: AsyncSession = Depends(get_db)):
    summary = await evidence_queries.get_evidence_summary(db, case_id)
    if not summary.get("evidence_id"):
        return ForensicSummary(
            case_id=case_id, evidence_id="", source_type="", source_identifier="",
            acquisition_method="", acquisition_timestamp=None, content_type="",
            original_filename="", size=0, sha256="",
            mime_parts=0, received_hops=0, attachments=0, iocs=0,
        )
    return ForensicSummary(
        case_id=case_id,
        evidence_id=summary["evidence_id"],
        source_type=summary["source_type"],
        source_identifier=summary["source_identifier"],
        acquisition_method=summary["acquisition_method"],
        acquisition_timestamp=summary["acquisition_timestamp"],
        content_type=summary["content_type"],
        original_filename=summary["original_filename"],
        size=summary["size"],
        sha256=summary["sha256"],
        mime_parts=summary["mime_parts"],
        received_hops=summary["received_hops"],
        attachments=summary["attachments"],
        iocs=summary["iocs"],
    )


@router.get("/{case_id}/headers")
async def get_headers(case_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "Case not found")

    raw_headers = case.raw_headers or ""
    headers = []
    for line in raw_headers.split("\n"):
        line = line.strip()
        if not line:
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            is_anomalous = key.strip() in ("Reply-To", "X-Mailer")
            badge = None
            if key.strip() == "Reply-To" and case.reply_to:
                badge = "Mismatch Detected"
            elif key.strip() == "From":
                badge = "Spoofed Brand" if case.sender_domain != "company.com" else None
            headers.append({
                "key": f"{key.strip()}:",
                "value": value.strip(),
                "is_anomalous": is_anomalous,
                "badge": badge,
            })
    return {"headers": headers, "raw": raw_headers}


@router.get("/{case_id}/transit-hops")
async def get_transit_hops(case_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "Case not found")

    # Phase-2+: return persisted forensic hop records (evidence-derived).
    persisted = await evidence_queries.get_received_hops(db, case_id)
    if persisted:
        return {"hops": [
            {
                "label": h.label,
                "ip": h.source_ip or h.by_host,
                "description": h.description,
                "hop_type": h.hop_type,
                "sequence": h.sequence,
                "raw_header": h.raw_header,
                "from_host": h.from_host,
                "by_host": h.by_host,
                "source_ip": h.source_ip,
                "protocol": h.protocol,
                "timestamp": h.timestamp,
            }
            for h in persisted
        ]}

    # Fallback for cases ingested before forensic records were persisted.
    # Hops are derived strictly from the Received headers in the actual EML.
    # No hostnames, IPs, organizations, or locations are invented; if the EML
    # contains no Received headers, the hop list is empty rather than fabricated.
    ev_result = await db.execute(
        select(EvidenceRecord).where(EvidenceRecord.case_id == case_id)
    )
    evidence = ev_result.scalars().first()
    eml_text = ""
    if evidence is not None and evidence.original_bytes:
        eml_text = evidence.original_bytes.decode("utf-8", errors="replace")
    if not eml_text:
        eml_text = case.raw_eml or ""
    return {"hops": extract_received_hops_from_text(eml_text)}


@router.get("/{case_id}/infrastructure", response_model=InfrastructureResponse)
async def get_infrastructure(case_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(InfrastructureRecord).where(InfrastructureRecord.case_id == case_id))
    infra = result.scalar_one_or_none()
    if not infra:
        raise HTTPException(404, "Infrastructure data not found")
    return InfrastructureResponse(
        case_id=infra.case_id,
        source_ip=infra.source_ip,
        asn=infra.asn,
        provider=infra.provider,
        location=infra.location,
        country=infra.country,
        latitude=infra.latitude,
        longitude=infra.longitude,
        domain=infra.domain,
        related_domains=_json.loads(infra.related_domains_json or "[]"),
        related_cases=infra.related_cases,
        threat_score=infra.threat_score,
        infrastructure_type=infra.infrastructure_type,
        threat_feeds=infra.threat_feeds,
    )


@router.get("/{case_id}/graph")
async def get_graph(case_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "Case not found")

    infra_result = await db.execute(select(InfrastructureRecord).where(InfrastructureRecord.case_id == case_id))
    infra = infra_result.scalar_one_or_none()

    nodes = [
        {
            "id": "case", "node_type": "email", "label": f"Case #{case.number}",
            "sublabel": case.subject[:50], "x": 295, "y": 290,
            "risk_score": case.risk_score, "icon_class": "mail",
            "node_class": "bg-primary text-on-primary shadow-md",
        },
    ]

    if case.sender_domain:
        nodes.append({
            "id": "sender_domain", "node_type": "domain", "label": case.sender_domain,
            "sublabel": "Sender Domain", "x": 100, "y": 120,
            "risk_score": 54, "icon_class": "domain",
            "node_class": "bg-secondary-fixed text-secondary shadow-sm",
        })

    if case.received_ip:
        nodes.append({
            "id": "source_ip", "node_type": "ip", "label": case.received_ip,
            "sublabel": "Origin IP", "x": 480, "y": 110,
            "risk_score": infra.threat_score if infra else 50,
            "location": infra.location if infra else "",
            "provider": infra.provider if infra else "",
            "asn_value": infra.asn if infra else "",
            "icon_class": "router", "badge": "Suspicious" if case.risk_score > 70 else None,
            "node_class": "bg-error-container text-error shadow-md",
        })

    if case.reply_to:
        reply_domain = case.reply_to.split("@")[-1] if "@" in case.reply_to else ""
        if reply_domain:
            nodes.append({
                "id": "reply_domain", "node_type": "domain", "label": reply_domain,
                "sublabel": "Reply-To Target", "x": 100, "y": 410,
                "risk_score": 80, "icon_class": "link_off",
                "node_class": "bg-surface-container-highest text-secondary shadow-sm",
            })

    if case.campaign_id:
        nodes.append({
            "id": "campaign", "node_type": "campaign", "label": "Related Cases",
            "sublabel": f"Campaign {case.campaign_id}", "x": 295, "y": 500,
            "risk_score": 89, "icon_class": "workspaces",
            "node_class": "bg-tertiary-fixed text-tertiary shadow-sm", "badge": "Related",
        })

    edges = []
    if case.sender_domain:
        edges.append({"edge_from": "case", "edge_to": "sender_domain", "label": "header_from", "color": "#6750A4", "edge_type": "dashed"})
    if case.received_ip and case.sender_domain:
        edges.append({"edge_from": "sender_domain", "edge_to": "source_ip", "label": "resolves_to", "color": "#B3261E", "edge_type": "solid"})
    if case.reply_to:
        edges.append({"edge_from": "case", "edge_to": "reply_domain", "label": "reply_to", "color": "#c7c4d8", "edge_type": "dashed"})
    if case.campaign_id:
        edges.append({"edge_from": "case", "edge_to": "campaign", "label": "correlated", "color": "#006e4b", "edge_type": "solid"})

    return {"nodes": nodes, "edges": edges}


@router.get("/{case_id}/campaign", response_model=Optional[CampaignResponse])
async def get_campaign(case_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case or not case.campaign_id:
        return None
    from models import CampaignRecord
    camp_result = await db.execute(select(CampaignRecord).where(CampaignRecord.id == case.campaign_id))
    campaign = camp_result.scalar_one_or_none()
    if not campaign:
        return None
    timeline = _json.loads(campaign.timeline_json or "[]")
    return CampaignResponse(
        id=campaign.id,
        name=campaign.name,
        related_emails=campaign.related_emails,
        shared_domains=_json.loads(campaign.shared_domains_json or "[]"),
        shared_infrastructure=_json.loads(campaign.shared_infra_json or "[]"),
        related_cases=campaign.related_cases,
        timeline=[CampaignTimelineEventOut(**t) for t in timeline],
        description=campaign.description,
    )


@router.get("/{case_id}/timeline", response_model=list[TimelineEventResponse])
async def get_timeline(case_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TimelineEventRecord).where(TimelineEventRecord.case_id == case_id)
        .order_by(TimelineEventRecord.id)
    )
    events = result.scalars().all()
    return [
        TimelineEventResponse(
            id=e.event_id, time=e.time, title=e.title,
            description=e.description, event_type=e.event_type,
            icon=e.icon, details=e.details,
        )
        for e in events
    ]


# ─── Helpers ───────────────────────────────────────────────────

async def _require_evidence(db: AsyncSession, case_id: str) -> EvidenceRecord | None:
    """Return the most recent evidence record for a case, after 404-checking the case."""
    if await evidence_queries.get_case(db, case_id) is None:
        raise HTTPException(404, "Case not found")
    return await evidence_queries.get_latest_evidence(db, case_id)


def _parse_json_list(json_str: str | None) -> list:
    if not json_str:
        return []
    try:
        return json.loads(json_str)
    except Exception:
        return []
