"""Report generation service."""
from __future__ import annotations
import json
from typing import Any
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import (
    Case, IdentityRecord, EvidenceFindingRecord,
    InfrastructureRecord, CampaignRecord, TimelineEventRecord,
    ReportRecord,
)
from services.evidence_queries import (
    get_latest_evidence as get_preserved_evidence,
    get_mime_parts,
    get_received_hops,
    get_attachments,
    get_iocs,
    get_evidence_summary,
)


async def generate_report(db: AsyncSession, case_id: str) -> dict[str, Any]:
    """Generate a full forensic report for a case."""
    case = await _get_case(db, case_id)
    if not case:
        raise ValueError("Case not found")

    identity = await _get_identity(db, case_id)
    findings = await _get_evidence(db, case_id)
    infra = await _get_infrastructure(db, case_id)
    campaign = await _get_campaign(db, case_id)
    timeline = await _get_timeline(db, case_id)

    preserved = await get_preserved_evidence(db, case_id)
    summary = await get_evidence_summary(db, case_id)
    mime_parts = await get_mime_parts(db, case_id)
    hops = await get_received_hops(db, case_id)
    attachments = await get_attachments(db, case_id)
    iocs = await get_iocs(db, case_id)

    report_data = {
        "case_id": case_id,
        "executive_summary": _build_executive_summary(case, findings, infra, campaign, summary),
        "evidence_analysis": _build_evidence_analysis(findings, preserved, summary, mime_parts, hops, attachments, iocs),
        "identity_analysis": _build_identity_analysis(identity),
        "infrastructure_analysis": _build_infrastructure_analysis(infra, hops),
        "campaign_correlation": _build_campaign_analysis(campaign),
        "attack_path": _build_attack_path(case),
        "confidence_and_limitations": _build_confidence(case, findings),
        "conclusion": _build_conclusion(case),
        "generated_at": datetime.utcnow().strftime("%b %d, %Y · %I:%M %p UTC"),
    }

    existing = await db.execute(select(ReportRecord).where(ReportRecord.case_id == case_id))
    existing_report = existing.scalar_one_or_none()
    if existing_report:
        for k, v in report_data.items():
            setattr(existing_report, k, v)
    else:
        db.add(ReportRecord(**report_data))

    await db.commit()
    return report_data


async def get_report(db: AsyncSession, case_id: str) -> dict[str, Any] | None:
    result = await db.execute(select(ReportRecord).where(ReportRecord.case_id == case_id))
    report = result.scalar_one_or_none()
    if not report:
        return None
    return {
        "case_id": report.case_id,
        "executive_summary": report.executive_summary,
        "evidence_analysis": report.evidence_analysis,
        "identity_analysis": report.identity_analysis,
        "infrastructure_analysis": report.infrastructure_analysis,
        "campaign_correlation": report.campaign_correlation,
        "attack_path": report.attack_path,
        "confidence_and_limitations": report.confidence_and_limitations,
        "conclusion": report.conclusion,
        "generated_at": report.generated_at,
    }


def _build_executive_summary(case, evidence, infra, campaign, summary) -> str:
    findings_count = len(evidence)
    critical = sum(1 for f in evidence if f.severity == "Critical")
    campaign_text = ""
    if campaign:
        campaign_text = f" The email is linked to active campaign {campaign.name} affecting {campaign.related_cases} organizations."
    reply_text = f" The Reply-To header directs responses to {case.reply_to}." if case.reply_to else ""
    preserved_text = ""
    if summary and summary.get("evidence_id"):
        preserved_text = (
            f" Evidence contains {summary['mime_parts']} MIME part(s), "
            f"{summary['attachments']} attachment(s), {summary['received_hops']} observed "
            f"transmission hop(s), and {summary['iocs']} extracted observable(s)."
        )
    return (
        f"On {case.received_date}, a suspicious email was received by {case.to_email} "
        f"claiming to be from \"{case.sender_name}\" with subject \"{case.subject}\". "
        f"Forensic analysis reveals this is a {case.risk_level.lower().replace(' risk', '-confidence')} "
        f"{case.threat_type} attack with a composite threat score of {case.risk_score}/100. "
        f"Sender domain {case.sender_domain} was observed in the From header."
        f"{reply_text} "
        f"{findings_count} evidence findings were identified ({critical} critical)."
        f"{preserved_text}"
        f"{campaign_text}"
    )


def _build_evidence_analysis(findings, preserved, summary, mime_parts, hops, attachments, iocs) -> str:
    lines: list[str] = []
    if not findings:
        lines.append("No evidence findings available.")
    else:
        lines.append(f"{len(findings)} evidence findings were identified:\n")
        for i, f in enumerate(findings, 1):
            lines.append(f"{i}. {f.title} ({f.evidence_state}, {f.confidence}% confidence)")
            lines.append(f"   {f.description}")
            lines.append(f"   Source: {f.source}\n")

    if preserved is None:
        lines.append("No preserved original evidence is on record for this case.")
        return "\n".join(lines)

    if summary and summary.get("evidence_id"):
        lines.append(
            f"Preserved original evidence (record {preserved.id}): "
            f"{preserved.original_filename}, {preserved.content_type}, "
            f"{preserved.size} bytes, sha256 {preserved.sha256}."
        )
        lines.append(
            f"Persisted records: {summary['mime_parts']} MIME part(s), "
            f"{summary['received_hops']} transmission hop(s), "
            f"{summary['attachments']} attachment(s), {summary['iocs']} observable(s)."
        )

    if mime_parts:
        lines.append("\nMIME structure:")
        for p in mime_parts:
            lines.append(
                f"- part {p.part_index}: {p.content_type or 'unknown'}"
                + (f" (\"{p.filename}\")" if p.filename else "")
                + (f" [{p.disposition}]" if p.disposition else "")
                + (f" {p.size} bytes" if p.size else "")
            )

    if hops:
        lines.append("\nObserved Received chain (transmission path):")
        for h in hops:
            description = (
                f" from {h.from_host}" if h.from_host else ""
            ) + (
                f" by {h.by_host}" if h.by_host else ""
            ) + (
                f" via {h.source_ip}" if h.source_ip else ""
            ) + (
                f" {h.protocol}" if h.protocol else ""
            )
            lines.append(f"- {h.label} ({h.hop_type}):{description} [hop record {h.id}]")
    else:
        lines.append("\nNo Received-header hops were observed in the evidence.")

    if attachments:
        lines.append("\nAttachments:")
        for a in attachments:
            lines.append(
                f"- {a.filename} ({a.mime_type}, {a.size} bytes, sha256 {a.sha256}) "
                f"[attachment record {a.id}]"
            )
    else:
        lines.append("\nNo attachments were found in the evidence.")

    if iocs:
        lines.append("\nExtracted observables (values are observations, not verdicts):")
        for i in iocs:
            lines.append(f"- {i.ioc_type}: {i.value} (found in {i.source})")
    else:
        lines.append("\nNo observables were extracted from the evidence.")

    return "\n".join(lines)


def _build_identity_analysis(identity) -> str:
    if not identity:
        return "Identity analysis not available."
    contradictions = json.loads(identity.contradictions_json or "[]")
    lines = [f"Identity consistency score: {identity.score}/100\n"]
    if contradictions:
        lines.append(f"{len(contradictions)} contradiction(s) detected:")
        for c in contradictions:
            lines.append(f"- [{c.get('severity', 'Unknown')}] {c.get('title', 'Unknown')}")
    else:
        lines.append("No contradictions detected.")
    return "\n".join(lines)


def _build_infrastructure_analysis(infra, hops) -> str:
    hop_text = ""
    if hops:
        observed_ips = [h.source_ip for h in hops if h.source_ip]
        hop_text = (
            f" Observed transmission hops: {len(hops)}; observed IPs: "
            f"{', '.join(dict.fromkeys(observed_ips)) or 'none'}."
        )
    if not infra or not infra.source_ip:
        return (
            "No originating sending IP was observed in the email headers, so "
            "infrastructure enrichment and geolocation were not performed. "
            "Transit path analysis is limited to the headers present in the EML."
            f"{hop_text}"
        )
    feed_text = (
        f"The IP was flagged in {infra.threat_feeds} threat intelligence feed(s)."
        if infra.threat_feeds > 0 else
        "No threat intelligence feed matches are recorded for this IP."
    )
    return (
        f"Observed sending infrastructure geolocates to {infra.location}. "
        f"Source IP {infra.source_ip} belongs to {infra.provider} ({infra.asn}). "
        f"Provider type: {infra.infrastructure_type}. "
        f"Note: This infrastructure is shared hosting and cannot be attributed to a specific "
        f"individual without additional evidence. {feed_text}"
        f"{hop_text}"
    )


def _build_campaign_analysis(campaign) -> str:
    if not campaign:
        return "No campaign correlation found."
    domains = json.loads(campaign.shared_domains_json or "[]")
    return (
        f"This email correlates with active campaign {campaign.name}, "
        f"linking {campaign.related_cases} related cases and {campaign.related_emails} observed emails. "
        f"Shared domains: {', '.join(domains)}. "
        f"{campaign.description}"
    )


def _build_attack_path(case) -> str:
    reply_text = case.reply_to if case.reply_to else "an address different from the From address"
    return (
        "Probable attack path (observations followed by inference):\n"
        f"1. Sender observation: {case.sender_domain} observed in the From header; "
        f"display name \"{case.sender_name}\" used [observed]\n"
        f"2. Routing observation: Reply-To header is set to {reply_text} "
        "[observed]\n"
        f"3. Delivery observation: Sent to {case.to_email} with subject \"{case.subject}\" [observed]\n"
        "4. Routing inference: any reply would be directed to the Reply-To address "
        "rather than the From address [inference]\n"
        "5. Follow-up inference: the pattern is consistent with impersonation of the "
        "sender for data or payment extraction [inference]\n\n"
        "This pattern is consistent with a BEC-style redirection attempt; "
        "attribution to any specific individual or group is not established."
    )


def _build_conclusion(case) -> str:
    return (
        f"Based on the observed evidence, this email is consistent with a "
        f"{case.risk_level.lower().replace(' risk', '-confidence')} {case.threat_type} attempt "
        f"(composite threat score {case.risk_score}/100). Observed behaviors include a "
        f"Reply-To redirect away from the From address and authentication results that do not "
        f"prove the sender controls the claimed domain. Sender identity and domain registration "
        f"were not established from the preserved evidence. "
        f"Recommended actions include quarantining the message, blocking the observed domains, "
        f"IPs and infrastructure, and alerting affected personnel."
    )


def _build_confidence(case, evidence) -> str:
    inferred = sum(1 for f in evidence if f.evidence_state == "INFERRED")
    observed = sum(1 for f in evidence if f.evidence_state == "OBSERVED")
    return (
        f"Model Confidence: {case.model_confidence}% | Evidence Confidence: {case.evidence_confidence}%\n\n"
        f"Evidence breakdown: {observed} observed (deterministic), {inferred} inferred (requires verification)\n\n"
        "Limitations:\n"
        "- Physical attacker location cannot be determined from email headers alone\n"
        "- Campaign attribution relies on automated pattern matching\n"
        "- WHOIS data may be obscured by privacy proxies\n"
        "- IP-based geolocation represents infrastructure location, not operator location"
    )


async def _get_identity(db, case_id):
    result = await db.execute(select(IdentityRecord).where(IdentityRecord.case_id == case_id))
    return result.scalar_one_or_none()

async def _get_evidence(db, case_id):
    result = await db.execute(select(EvidenceFindingRecord).where(EvidenceFindingRecord.case_id == case_id))
    return result.scalars().all()

async def _get_infrastructure(db, case_id):
    result = await db.execute(select(InfrastructureRecord).where(InfrastructureRecord.case_id == case_id))
    return result.scalar_one_or_none()

async def _get_campaign(db, case_id):
    case = await _get_case(db, case_id)
    if not case or not case.campaign_id:
        return None
    result = await db.execute(select(CampaignRecord).where(CampaignRecord.id == case.campaign_id))
    return result.scalar_one_or_none()

async def _get_timeline(db, case_id):
    result = await db.execute(select(TimelineEventRecord).where(TimelineEventRecord.case_id == case_id))
    return result.scalars().all()

async def _get_case(db, case_id):
    result = await db.execute(select(Case).where(Case.id == case_id))
    return result.scalar_one_or_none()
