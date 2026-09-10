"""Forensic ingestion pipeline.

``ingest_acquired_email`` runs the whole analysis pipeline on a normalized
:class:`AcquiredEmail`. It is source-agnostic: the pipeline does not care
whether the email came from an EML file, Gmail, Microsoft 365, a raw message,
or a header paste.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    Case,
    IdentityRecord,
    EvidenceFindingRecord,
    SourceRecord,
    EvidenceRecord,
    InfrastructureRecord,
    TimelineEventRecord,
)
from services.email_parser import parse_eml
from services.sources import AcquiredEmail
from services.identity_analysis import analyze_identity, _extract_domain
from services.risk_scoring import calculate_risk_score, classify_threat_type
from services.domain_analysis import get_asn_for_ip, get_ip_geolocation
from services.campaign_correlation import find_or_create_campaign
from services.forensic_records import build_forensic_records


class UnparsableEmail(Exception):
    """Raised when an acquired email cannot be parsed as an RFC-822 message."""


async def ingest_acquired_email(db: AsyncSession, acquired: AcquiredEmail) -> dict[str, object]:
    """Ingest a normalized acquired email and return upload result metadata.

    Raises
    ------
    UnparsableEmail
        When the raw bytes cannot be parsed as a message.
    """
    raw_bytes = acquired.raw_bytes

    try:
        parsed = parse_eml(raw_bytes)
    except Exception as exc:
        raise UnparsableEmail("The uploaded file could not be parsed as an email") from exc

    # Case numbering.
    result = await db.execute(select(func.max(Case.number)))
    max_num = result.scalar() or 1000
    case_number = max_num + 1
    case_id = f"case-{case_number}"
    source_id = f"source-{uuid.uuid4().hex}"
    evidence_id = f"evidence-{uuid.uuid4().hex}"

    from_domain = parsed["from_domain"]
    reply_to_domain = parsed["reply_to_domain"]
    source_ip = parsed["source_ip"]

    # Identity analysis.
    identity_result = analyze_identity(
        display_name=parsed["from_name"],
        from_email=parsed["from_email"],
        from_domain=from_domain,
        reply_to=parsed["reply_to"],
        return_path=parsed["return_path"],
        dkim_domain=from_domain,
        source_ip=source_ip,
        source_asn="",
        source_location="",
        source_provider="",
        known_domains=[from_domain],
    )

    # Optional IP enrichment (degrades gracefully with no network).
    asn_info = get_asn_for_ip(source_ip) if source_ip else {}
    geo_info = get_ip_geolocation(source_ip) if source_ip else {}

    identity_result["chain"] = [
        {**c} if c["label"] != "Hop Zero" else {
            **c,
            "value": source_ip or "Unknown",
            "status": asn_info.get("provider", "Unknown"),
            "subtitle": f"{geo_info.get('location', 'Unknown')} ({asn_info.get('asn', '')})",
        }
        for c in identity_result["chain"]
    ]

    # Risk scoring.
    has_reply_to_mismatch = bool(reply_to_domain and reply_to_domain != from_domain)
    is_typosquat = any(
        c["title"] == "Lookalike Typosquatting Domain"
        for c in identity_result["contradictions"]
    )
    risk = calculate_risk_score(
        identity_score=identity_result["score"],
        spf_result=parsed["spf_result"],
        dkim_result=parsed["dkim_result"],
        dmarc_result=parsed["dmarc_result"],
        has_reply_to_mismatch=has_reply_to_mismatch,
        is_typosquat=is_typosquat,
    )
    threat_type = classify_threat_type(
        parsed["spf_result"], parsed["dkim_result"], parsed["dmarc_result"],
        has_reply_to_mismatch, is_typosquat, parsed.get("body", ""),
    )

    # Case.
    case = Case(
        id=case_id,
        number=case_number,
        title=f"Case #{case_number}",
        subject=parsed["subject"],
        threat_type=threat_type,
        risk_score=risk["risk_score"],
        risk_level=risk["risk_level"],
        identity_consistency=identity_result["score"],
        model_confidence=risk["model_confidence"],
        evidence_confidence=risk["evidence_confidence"],
        status="Active",
        received_date=parsed["date"] or datetime.utcnow().strftime("%b %d, %Y · %I:%M %p UTC"),
        sender_name=parsed["from_name"],
        sender_email=parsed["from_email"],
        sender_domain=from_domain,
        to_email=parsed["to_email"],
        reply_to=parsed["reply_to"],
        return_path=parsed["return_path"],
        received_ip=source_ip,
        spf_result=parsed["spf_result"],
        dkim_result=parsed["dkim_result"],
        dmarc_result=parsed["dmarc_result"],
        sha256=parsed["sha256"],
        file_name=acquired.original_filename,
        file_size=len(raw_bytes),
        raw_headers=parsed.get("all_raw_headers", ""),
        raw_eml=raw_bytes.decode("utf-8", errors="replace"),
        source_type=acquired.source_type,
        analysis_status="completed",
    )
    db.add(case)
    await db.flush()

    # Preserve exact acquired bytes before persisting derived analysis records.
    # These bytes are never normalized or rewritten by the analysis pipeline.
    db.add(SourceRecord(
        id=source_id,
        case_id=case_id,
        source_type=acquired.source_type,
        source_id=acquired.source_identifier,
        acquisition_method=acquired.acquisition_method,
        provenance_json=json.dumps(acquired.metadata),
    ))
    db.add(EvidenceRecord(
        id=evidence_id,
        case_id=case_id,
        source_id=source_id,
        original_filename=acquired.original_filename,
        content_type=acquired.content_type or "message/rfc822",
        size=len(raw_bytes),
        sha256=parsed["sha256"],
        original_bytes=raw_bytes,
    ))

    # Identity record.
    db.add(IdentityRecord(
        case_id=case_id,
        score=identity_result["score"],
        display_name=parsed["from_name"],
        from_address=parsed["from_email"],
        from_domain=from_domain,
        reply_to=parsed["reply_to"],
        reply_to_domain=reply_to_domain,
        return_path=parsed["return_path"],
        return_path_domain=parsed["return_path_domain"],
        dkim_domain=from_domain,
        source_ip=source_ip,
        source_asn=asn_info.get("asn", ""),
        source_location=geo_info.get("location", ""),
        source_provider=asn_info.get("provider", ""),
        contradictions_json=json.dumps(identity_result["contradictions"]),
        chain_json=json.dumps(identity_result["chain"]),
    ))

    # Evidence findings.
    findings = _build_evidence_findings(
        case_id, parsed, identity_result, has_reply_to_mismatch, is_typosquat
    )
    for f in findings:
        db.add(f)

    # Infrastructure record.
    db.add(InfrastructureRecord(
        case_id=case_id,
        source_ip=source_ip,
        asn=asn_info.get("asn", ""),
        provider=asn_info.get("provider", ""),
        location=geo_info.get("location", ""),
        country=geo_info.get("country", ""),
        latitude=geo_info.get("lat", 0.0),
        longitude=geo_info.get("lon", 0.0),
        domain=from_domain,
        related_domains_json=json.dumps([d for d in [reply_to_domain, parsed["return_path_domain"]] if d]),
        related_cases=0,
        threat_score=risk["risk_score"],
        infrastructure_type=asn_info.get("provider", "Unknown"),
        threat_feeds=0,
    ))

    # Timeline.
    for t in _build_timeline_events(case_id, case_number, parsed, risk):
        db.add(t)

    # Normalized forensic records (MIME, hops, attachments, IOCs, relationships).
    for record in build_forensic_records(evidence_id, parsed):
        db.add(record)

    # Campaign correlation.
    campaign_id = await find_or_create_campaign(db, case, from_domain, reply_to_domain, source_ip)
    if campaign_id:
        case.campaign_id = campaign_id

    await db.commit()

    return {
        "case_id": case_id,
        "case_number": case_number,
        "evidence_id": evidence_id,
        "source_type": acquired.source_type,
        "threat_type": threat_type,
        "risk_level": risk["risk_level"],
        "risk_score": risk["risk_score"],
        "analysis_status": "completed",
        "status": "active",
    }


def _build_evidence_findings(case_id, parsed, identity_result, has_mismatch, is_typosquat):
    findings = []
    if has_mismatch:
        findings.append(EvidenceFindingRecord(
            case_id=case_id, finding_id="CRIT-01", title="Reply-To Mismatch",
            description=f"Observed Reply-To address ({parsed['reply_to']}) diverges from sender From address ({parsed['from_email']}). This indicates active mail diversion.",
            severity="Critical", risk_badge="High Risk", code="Reply-To",
            evidence_state="OBSERVED", confidence=99, source="RFC-822 Header",
            tags_json=json.dumps(["RFC-5322 Violation", "Entity: Reply-To"]),
            color_accent="error",
        ))
    if is_typosquat:
        findings.append(EvidenceFindingRecord(
            case_id=case_id, finding_id="CRIT-02", title="Lookalike Typosquatting Domain",
            description=f"Domain {parsed['from_domain']} has low Levenshtein distance from known domains, indicating potential typosquatting.",
            severity="Critical", risk_badge="High Risk", code=parsed["from_domain"],
            evidence_state="INFERRED", confidence=96, source="WHOIS / DNS",
            tags_json=json.dumps(["Domain Age: Recent", "Levenshtein Distance: Low"]),
            color_accent="error",
        ))

    if parsed["reply_to"] and _extract_domain(parsed["reply_to"]) != parsed["from_domain"]:
        findings.append(EvidenceFindingRecord(
            case_id=case_id, finding_id="WARN-03", title="Suspicious Reply-To Domain",
            description=f"Reply-To resolves to {_extract_domain(parsed['reply_to'])} which is different from the From domain.",
            severity="Medium", risk_badge="Medium Risk", code=parsed["reply_to"],
            evidence_state="OBSERVED", confidence=95, source="Header Analysis",
            tags_json=json.dumps(["Reply-To Mismatch", "Exfiltration Risk"]),
            color_accent="secondary-container",
        ))

    if parsed["source_ip"]:
        findings.append(EvidenceFindingRecord(
            case_id=case_id, finding_id="INFO-04", title="Origin IP Analysis",
            description=f"Origin sender IP {parsed['source_ip']} was used to send this email.",
            severity="Informational", risk_badge="Informational", code=parsed["source_ip"],
            evidence_state="OBSERVED", confidence=100, source="IP Intelligence",
            tags_json=json.dumps(["Source IP", "Received Header"]),
            color_accent="primary-container",
        ))

    if parsed["dmarc_result"] == "FAIL":
        findings.append(EvidenceFindingRecord(
            case_id=case_id, finding_id="CRIT-05", title="DMARC Alignment Failure",
            description=f"DMARC authentication failed for {parsed['from_domain']}. The sender cannot prove domain ownership.",
            severity="Critical", risk_badge="High Risk", code="DMARC",
            evidence_state="OBSERVED", confidence=98, source="Authentication Results",
            tags_json=json.dumps(["DMARC FAIL", "Policy Enforcement"]),
            color_accent="error",
        ))

    return findings


def _build_timeline_events(case_id, case_number, parsed, risk):
    events = [
        TimelineEventRecord(
            case_id=case_id, event_id="t1", time="Initial",
            title="Received headers evaluated",
            description=(
                f"Email destined for {parsed['to_email']} with "
                f"{len(parsed['received_hops'])} observed transit hop(s) in the Received headers."
                if parsed['received_hops'] else
                f"Email destined for {parsed['to_email']}; no Received headers were present."
            ),
            event_type="OBSERVED", icon="mail",
        ),
        TimelineEventRecord(
            case_id=case_id, event_id="t2", time="Authentication",
            title="Authentication results evaluated",
            description=f"SPF: {parsed['spf_result']}, DKIM: {parsed['dkim_result']}, DMARC: {parsed['dmarc_result']}.",
            event_type="OBSERVED", icon="verified_user",
        ),
    ]

    if parsed["reply_to"] and _extract_domain(parsed["reply_to"]) != parsed["from_domain"]:
        events.append(TimelineEventRecord(
            case_id=case_id, event_id="t3", time="Analysis",
            title="Reply-To mismatch detected",
            description=f"Reply-To header redirects replies to {parsed['reply_to']} instead of the From domain.",
            event_type="OBSERVED", icon="warning",
        ))

    events.append(TimelineEventRecord(
        case_id=case_id, event_id="t4", time="Risk Scoring",
        title="Risk score calculated",
        description=f"Composite threat score: {risk['risk_score']}/100 ({risk['risk_level']}).",
        event_type="OBSERVED", icon="analytics",
    ))
    return events