"""Campaign correlation engine — links cases sharing infrastructure."""
from __future__ import annotations
import json
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import Case, CampaignRecord


async def find_or_create_campaign(
    db: AsyncSession,
    case: Case,
    sender_domain: str,
    reply_to_domain: str,
    source_ip: str,
) -> str | None:
    """Find existing campaign or create new one. Returns campaign ID."""
    existing = await _find_matching_campaign(db, sender_domain, reply_to_domain, source_ip)
    if existing:
        await _add_case_to_campaign(db, existing, case)
        return existing

    campaign_id = _generate_campaign_id(sender_domain)
    campaign = CampaignRecord(
        id=campaign_id,
        name=f"#{campaign_id}",
        related_emails=1,
        shared_domains_json=json.dumps([d for d in [sender_domain, reply_to_domain] if d]),
        shared_infra_json=json.dumps([ip for ip in [source_ip] if ip]),
        related_cases=1,
        timeline_json=json.dumps([{
            "date": case.received_date,
            "title": f"Case #{case.number}: Email received",
            "event_type": "OBSERVED",
            "description": f"Subject: {case.subject}",
        }]),
        description=f"Automated campaign linked to domain {sender_domain} and infrastructure {source_ip}.",
    )
    db.add(campaign)
    await db.commit()
    return campaign_id


async def _find_matching_campaign(
    db: AsyncSession,
    sender_domain: str,
    reply_to_domain: str,
    source_ip: str,
) -> str | None:
    """Find a campaign that shares infrastructure with this case."""
    result = await db.execute(select(CampaignRecord))
    campaigns = result.scalars().all()

    for c in campaigns:
        shared_domains = json.loads(c.shared_domains_json or "[]")
        shared_infra = json.loads(c.shared_infra_json or "[]")

        if (sender_domain in shared_domains or reply_to_domain in shared_domains or
                source_ip in shared_infra):
            return c.id
    return None


async def _add_case_to_campaign(db: AsyncSession, campaign_id: str, case: Case):
    result = await db.execute(select(CampaignRecord).where(CampaignRecord.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        return

    shared_domains = json.loads(campaign.shared_domains_json or "[]")
    shared_infra = json.loads(campaign.shared_infra_json or "[]")
    timeline = json.loads(campaign.timeline_json or "[]")

    if case.sender_domain and case.sender_domain not in shared_domains:
        shared_domains.append(case.sender_domain)
    if case.reply_to:
        reply_domain = case.reply_to.split("@")[-1] if "@" in case.reply_to else ""
        if reply_domain and reply_domain not in shared_domains:
            shared_domains.append(reply_domain)
    if case.received_ip and case.received_ip not in shared_infra:
        shared_infra.append(case.received_ip)

    timeline.append({
        "date": case.received_date,
        "title": f"Case #{case.number}: Email received",
        "event_type": "OBSERVED",
        "description": f"Subject: {case.subject}",
    })

    campaign.shared_domains_json = json.dumps(shared_domains)
    campaign.shared_infra_json = json.dumps(shared_infra)
    campaign.related_cases += 1
    campaign.related_emails += 1
    campaign.timeline_json = json.dumps(timeline)
    await db.commit()


def _generate_campaign_id(domain: str) -> str:
    prefix = domain.split(".")[0][:4].upper() if domain else "UNK"
    import hashlib
    h = hashlib.md5(domain.encode()).hexdigest()[:6].upper()
    return f"CR-{prefix}-{h}"
