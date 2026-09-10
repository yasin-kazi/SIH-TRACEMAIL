"""AI Copilot service — contextual investigation responses."""
from __future__ import annotations
import json
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import Case, IdentityRecord, EvidenceFindingRecord, InfrastructureRecord, CampaignRecord, TimelineEventRecord
from services.evidence_queries import (
    get_mime_parts,
    get_received_hops,
    get_attachments,
    get_iocs,
    get_evidence_summary,
)


async def get_copilot_response(
    db: AsyncSession,
    case_id: str,
    question: str,
) -> str:
    """Generate a contextual response based on the case data."""
    case = await _get_case(db, case_id)
    if not case:
        return "Case not found. Please check the case ID."

    q = question.lower()

    if any(w in q for w in ["attachment", "attach"]):
        return await _attachments_response(db, case_id)
    if any(w in q for w in ["ioc", "indicator", "observable", "extracted"]):
        return await _iocs_response(db, case_id)
    if any(w in q for w in ["received", "transit", "hops"]):
        return await _received_hops_response(db, case_id)
    if any(w in q for w in ["risk", "high risk", "score", "threat"]):
        return _risk_response(case)
    if any(w in q for w in ["evidence", "strongest", "best evidence"]):
        return await _evidence_response(db, case_id)
    if any(w in q for w in ["identity", "contradict", "impersonat"]):
        return await _identity_response(db, case_id)
    if any(w in q for w in ["infra", "ip", "network", "server"]):
        return await _infrastructure_response(db, case_id)
    if any(w in q for w in ["campaign", "related", "pattern"]):
        return await _campaign_response(db, case_id)
    if any(w in q for w in ["attack", "path", "how", "technique"]):
        return _attack_path_response(case)
    if any(w in q for w in ["uncertain", "inferred", "unknown", "confidence"]):
        return await _uncertainty_response(db, case_id)
    if any(w in q for w in ["auth", "spf", "dkim", "dmarc"]):
        return _auth_response(case)
    if any(w in q for w in ["domain", "whois", "register"]):
        return await _domain_response(db, case_id)
    if any(w in q for w in ["timeline", "when", "sequence"]):
        return await _timeline_response(db, case_id)
    if any(w in q for w in ["report", "summary", "executive"]):
        return _report_response(case)

    return _default_response(case)


def _risk_response(case: Case) -> str:
    return (
        f"This email scores {case.risk_score}/100 on our composite threat scale "
        f"(classified as {case.risk_level}). Key contributing factors:\n\n"
        f"1. Identity inconsistency score: {case.identity_consistency}/100 "
        f"({'severe contradictions' if case.identity_consistency < 50 else 'minor inconsistencies'})\n"
        f"2. Authentication: SPF={case.spf_result}, DKIM={case.dkim_result}, DMARC={case.dmarc_result}\n"
        f"3. Sender domain: {case.sender_domain}\n"
        f"4. Reply-To redirect: {case.reply_to}\n\n"
        f"The model confidence is {case.model_confidence}% and evidence confidence is {case.evidence_confidence}%."
    )


async def _evidence_response(db: AsyncSession, case_id: str) -> str:
    result = await db.execute(
        select(EvidenceFindingRecord).where(EvidenceFindingRecord.case_id == case_id)
        .order_by(EvidenceFindingRecord.confidence.desc())
    )
    findings = result.scalars().all()
    summary = await get_evidence_summary(db, case_id)
    lines = []
    if findings:
        top = findings[0]
        lines.append(f"The strongest evidence finding is **{top.title}** ({top.evidence_state}, {top.confidence}% confidence).\n")
        lines.append(f"Description: {top.description}")
        lines.append(f"Source: {top.source}")
        if len(findings) > 1:
            lines.append(f"\nOther findings ({len(findings) - 1} total):")
            for f in findings[1:4]:
                lines.append(f"  - {f.title} ({f.evidence_state}, {f.confidence}%)")
    else:
        lines.append("No evidence findings recorded for this case.")

    if summary and summary.get("evidence_id"):
        attachments = await get_attachments(db, case_id)
        hops = await get_received_hops(db, case_id)
        iocs = await get_iocs(db, case_id)
        lines.append("\nObserved facts from the preserved evidence:")
        lines.append(f"- MIME parts: {summary['mime_parts']}")
        lines.append(
            f"- Attachments: {summary['attachments']} "
            + (", ".join(a.filename for a in attachments) if attachments else "(none)")
        )
        lines.append(f"- Observed transmission hops: {summary['received_hops']}")
        lines.append(
            f"- Extracted observables: {summary['iocs']} "
            + (", ".join(i.value for i in iocs[:5]) + ("..." if len(iocs) > 5 else "") if iocs else "(none)")
        )
        lines.append("\nThese are persisted observations from the evidence record; "
                     "no indicator is treated as a verdict without independent confirmation.")
    else:
        lines.append("\nNo preserved original evidence is on record for this case.")

    return "\n".join(lines)


async def _attachments_response(db: AsyncSession, case_id: str) -> str:
    attachments = await get_attachments(db, case_id)
    if not attachments:
        return "No attachments were found in the preserved evidence for this case."
    lines = [f"{len(attachments)} attachment(s) were found in the evidence:\n"]
    for a in attachments:
        lines.append(
            f"- {a.filename} ({a.mime_type}, {a.size} bytes, sha256 {a.sha256}) "
            f"[attachment record {a.id}]"
        )
    lines.append("\nOnly metadata is stored; payloads are never opened or executed.")
    return "\n".join(lines)


async def _iocs_response(db: AsyncSession, case_id: str) -> str:
    iocs = await get_iocs(db, case_id)
    if not iocs:
        return "No observables were extracted from the preserved evidence for this case."
    grouped: dict[str, list[str]] = {}
    for i in iocs:
        grouped.setdefault(i.ioc_type, []).append(i.value)
    lines = [f"{len(iocs)} observable(s) were extracted from the evidence:\n"]
    for ioc_type in sorted(grouped):
        lines.append(f"{ioc_type}:")
        seen = []
        for value in grouped[ioc_type]:
            if value not in seen:
                seen.append(value)
                lines.append(f"  - {value}")
    lines.append("\nThese are observations taken from the email content and headers, "
                 "not verdicts on whether the targets are malicious.")
    return "\n".join(lines)


async def _received_hops_response(db: AsyncSession, case_id: str) -> str:
    hops = await get_received_hops(db, case_id)
    if not hops:
        return "No Received-header hops were observed in the preserved evidence for this case."
    lines = [f"{len(hops)} Received-header hop(s) were observed:\n"]
    for h in hops:
        hop = f"{h.sequence}. {h.label} ({h.hop_type})"
        if h.from_host:
            hop += f" from {h.from_host}"
        if h.by_host:
            hop += f" by {h.by_host}"
        if h.source_ip:
            hop += f" via {h.source_ip}"
        if h.protocol:
            hop += f" {h.protocol}"
        hop += f" [hop record {h.id}]"
        if h.timestamp:
            hop += f" ({h.timestamp})"
        lines.append(hop)
    return "\n".join(lines)


async def _identity_response(db: AsyncSession, case_id: str) -> str:
    result = await db.execute(
        select(IdentityRecord).where(IdentityRecord.case_id == case_id)
    )
    identity = result.scalar_one_or_none()
    if not identity:
        return "Identity analysis not available for this case."
    contradictions = json.loads(identity.contradictions_json or "[]")
    chain = json.loads(identity.chain_json or "[]")
    lines = [f"Identity consistency score: {identity.score}/100", ""]
    if contradictions:
        lines.append(f"Found {len(contradictions)} contradiction(s):")
        for c in contradictions:
            lines.append(f"  [{c.get('severity', 'Unknown')}] {c.get('title', 'Unknown')}")
            lines.append(f"    {c.get('description', '')}")
    else:
        lines.append("No contradictions detected.")
    return "\n".join(lines)


async def _infrastructure_response(db: AsyncSession, case_id: str) -> str:
    result = await db.execute(
        select(InfrastructureRecord).where(InfrastructureRecord.case_id == case_id)
    )
    infra = result.scalar_one_or_none()
    hops = await get_received_hops(db, case_id)
    iocs = await get_iocs(db, case_id)

    observed_ips = [h.source_ip for h in hops if h.source_ip]
    for i in iocs:
        if i.ioc_type == "IP":
            observed_ips.append(i.value)
    observed_ips = list(dict.fromkeys(observed_ips))

    lines = []
    if infra and infra.source_ip:
        lines.append(
            f"Observed sending infrastructure:\n"
            f"- IP: {infra.source_ip}\n"
            f"- ASN: {infra.asn}\n"
            f"- Provider: {infra.provider}\n"
            f"- Location: {infra.location}\n"
            f"- Threat score: {infra.threat_score}/100\n"
            f"- Threat feed hits: {infra.threat_feeds}\n\n"
            f"Note: The IP belongs to {infra.provider} ({infra.infrastructure_type}). "
            f"This is shared hosting infrastructure and cannot be attributed to a specific "
            f"individual without additional evidence."
        )
    else:
        lines.append("No originating sending IP was observed in the email headers.")

    if observed_ips:
        lines.append(
            "\nObserved IPs in the preserved evidence "
            f"(headers and extracted observables): {', '.join(observed_ips)}."
        )
    else:
        lines.append("\nNo IPs were observed in the preserved evidence.")

    if infra and infra.threat_feeds > 0:
        lines.append(
            f"\nThe IP was flagged in {infra.threat_feeds} threat intelligence feed(s); "
            f"threat-feed hits are recorded intel, not proof of a specific attacker."
        )
    elif infra:
        lines.append("\nNo threat intelligence feed matches are recorded for the observed IP.")

    return "\n".join(lines)


async def _campaign_response(db: AsyncSession, case_id: str) -> str:
    case = await _get_case(db, case_id)
    if not case or not case.campaign_id:
        return "No campaign correlation found for this case."
    result = await db.execute(
        select(CampaignRecord).where(CampaignRecord.id == case.campaign_id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        return "Campaign data not found."
    domains = json.loads(campaign.shared_domains_json or "[]")
    infra = json.loads(campaign.shared_infra_json or "[]")
    return (
        f"This email is linked to campaign {campaign.name}.\n\n"
        f"- Related cases: {campaign.related_cases}\n"
        f"- Related emails: {campaign.related_emails}\n"
        f"- Shared domains: {', '.join(domains)}\n"
        f"- Shared infrastructure: {', '.join(infra)}\n\n"
        f"{campaign.description}"
    )


def _attack_path_response(case: Case) -> str:
    reply_text = case.reply_to if case.reply_to else "an address different from the From address"
    return (
        "Based on available evidence, the likely attack path is (observations followed by inference):\n\n"
        f"1. Sender observation: {case.sender_domain} observed in the From header; "
        f"display name \"{case.sender_name}\" used [observed]\n"
        f"2. Routing observation: Reply-To header is set to {reply_text} [observed]\n"
        f"3. Delivery observation: Sent to {case.to_email} with subject: {case.subject} [observed]\n"
        f"4. Routing inference: any reply would be directed to the Reply-To address "
        f"rather than the From address [inference]\n"
        f"5. Follow-up inference: this is consistent with impersonation of the sender "
        f"for data or payment extraction [inference]\n\n"
        "This follows a BEC (Business Email Compromise) invoice redirection pattern; "
        "attribution to a specific individual or group is not established."
    )


async def _uncertainty_response(db: AsyncSession, case_id: str) -> str:
    result = await db.execute(
        select(EvidenceFindingRecord).where(EvidenceFindingRecord.case_id == case_id)
    )
    findings = result.scalars().all()
    inferred = [f for f in findings if f.evidence_state == "INFERRED"]
    enriched = [f for f in findings if f.evidence_state == "ENRICHED"]
    observed = [f for f in findings if f.evidence_state == "OBSERVED"]

    lines = ["Evidence certainty breakdown:\n"]
    lines.append(f"OBSERVED (deterministic): {len(observed)} finding(s)")
    for f in observed:
        lines.append(f"  - {f.title} ({f.confidence}% confidence)")
    lines.append(f"\nINFERRED (requires verification): {len(inferred)} finding(s)")
    for f in inferred:
        lines.append(f"  - {f.title} ({f.confidence}% confidence)")
    lines.append(f"\nENRICHED (external data): {len(enriched)} finding(s)")
    for f in enriched:
        lines.append(f"  - {f.title} ({f.confidence}% confidence)")
    lines.append(
        "\nPhysical attacker location cannot be determined from email infrastructure alone."
    )
    return "\n".join(lines)


def _auth_response(case: Case) -> str:
    return (
        f"Authentication results for {case.sender_domain}:\n\n"
        f"SPF: {case.spf_result}\n"
        f"DKIM: {case.dkim_result}\n"
        f"DMARC: {case.dmarc_result}\n\n"
        f"DMARC alignment with From domain: {'PASS' if case.dmarc_result == 'PASS' else 'FAIL'}\n"
        f"The sender cannot cryptographically prove ownership of {case.sender_domain}."
    )


async def _domain_response(db: AsyncSession, case_id: str) -> str:
    case = await _get_case(db, case_id)
    if not case:
        return "Case not found."
    observed_domains: list[str] = []
    for header_value in (case.sender_domain,
                         case.reply_to.split("@")[-1] if "@" in case.reply_to else "",
                         case.return_path.split("@")[-1] if "@" in case.return_path else ""):
        if header_value and header_value not in observed_domains:
            observed_domains.append(header_value)
    iocs = await get_iocs(db, case_id)
    for i in iocs:
        if i.ioc_type == "Domain" and i.value not in observed_domains:
            observed_domains.append(i.value)

    lines = [f"Domain analysis for {case.sender_domain}:", ""]
    if observed_domains:
        lines.append(f"Observed domains in the evidence: {', '.join(observed_domains)}")
    else:
        lines.append("No domains were observed in the evidence.")
    lines.append("")
    lines.append("WHOIS/RDAP registration data was not queried, so domain age, ownership, "
                 "and registration attribution were NOT established. Observed domains are "
                 "facts taken from the email headers and content; they are not proof that "
                 "the sender controls them. Levenshtein edit distance analysis can help "
                 "identify typosquatting candidates for further investigation.")
    return "\n".join(lines)


async def _timeline_response(db: AsyncSession, case_id: str) -> str:
    result = await db.execute(
        select(TimelineEventRecord).where(TimelineEventRecord.case_id == case_id)
        .order_by(TimelineEventRecord.id)
    )
    events = result.scalars().all()
    if not events:
        return "No timeline events recorded."
    lines = ["Investigation timeline:\n"]
    for e in events:
        lines.append(f"[{e.time}] {e.title}")
        lines.append(f"  {e.description} ({e.event_type})\n")
    return "\n".join(lines)


def _report_response(case: Case) -> str:
    return (
        f"Incident Report Summary for Case #{case.number}:\n\n"
        f"Threat: {case.threat_type} | Risk: {case.risk_level} ({case.risk_score}/100)\n"
        f"Subject: {case.subject}\n"
        f"Sender: {case.sender_name} <{case.sender_email}>\n\n"
        f"To view the full report, navigate to the Report section."
    )


def _default_response(case: Case) -> str:
    return (
        f"I can help you analyze Case #{case.number} ({case.threat_type}, {case.risk_level}).\n\n"
        f"Ask me about:\n"
        f"- Risk score and threat assessment\n"
        f"- Evidence findings and confidence levels\n"
        f"- Identity contradictions and analysis\n"
        f"- Infrastructure and sending IPs\n"
        f"- Attachments found in the evidence\n"
        f"- Extracted observables / indicators\n"
        f"- Received transmission chain\n"
        f"- Campaign correlation and related cases\n"
        f"- Attack path reconstruction\n"
        f"- Authentication (SPF/DKIM/DMARC)\n"
        f"- Domain analysis\n"
        f"- Investigation timeline\n"
        f"- Report summary"
    )


async def _get_case(db: AsyncSession, case_id: str) -> Case | None:
    result = await db.execute(select(Case).where(Case.id == case_id))
    return result.scalar_one_or_none()
