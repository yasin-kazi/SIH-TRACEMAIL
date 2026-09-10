"""Read-only, case-scoped queries over persisted forensic records.

Owns all case-scoped database access for the normalized forensic records so
that report generation, copilot answers, and the read APIs share one source of
truth. Every query is confined to a single case, returns observables/metadata
only, and never loads attachment payloads, executes content, or fetches URLs.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    EvidenceRecord,
    SourceRecord,
    MimePartRecord,
    ReceivedHopRecord,
    AttachmentRecord,
    IOCRecord,
    EvidenceRelationshipRecord,
)


async def get_case(db: AsyncSession, case_id: str):
    """Return the Case row for ``case_id`` or None (used for 404 checks)."""
    from models import Case
    result = await db.execute(select(Case).where(Case.id == case_id))
    return result.scalar_one_or_none()


async def get_latest_evidence(db: AsyncSession, case_id: str) -> EvidenceRecord | None:
    """Return the most recently ingested preserved evidence for a case."""
    result = await db.execute(
        select(EvidenceRecord)
        .where(EvidenceRecord.case_id == case_id)
        .order_by(EvidenceRecord.ingested_at.desc())
    )
    return result.scalars().first()


async def get_source(db: AsyncSession, evidence_id: str) -> SourceRecord | None:
    """Return the acquisition provenance for an evidence record, if any."""
    if not evidence_id:
        return None
    result = await db.execute(select(SourceRecord).where(SourceRecord.id == evidence_id))
    return result.scalar_one_or_none()


async def get_mime_parts(db: AsyncSession, case_id: str) -> list[MimePartRecord]:
    """Persisted MIME part records for a case, in part order."""
    evidence = await get_latest_evidence(db, case_id)
    if evidence is None:
        return []
    result = await db.execute(
        select(MimePartRecord)
        .where(MimePartRecord.evidence_id == evidence.id)
        .order_by(MimePartRecord.part_index)
    )
    return list(result.scalars().all())


async def get_received_hops(db: AsyncSession, case_id: str) -> list[ReceivedHopRecord]:
    """Persisted Received-header hop records for a case, in sequence order."""
    evidence = await get_latest_evidence(db, case_id)
    if evidence is None:
        return []
    result = await db.execute(
        select(ReceivedHopRecord)
        .where(ReceivedHopRecord.evidence_id == evidence.id)
        .order_by(ReceivedHopRecord.sequence)
    )
    return list(result.scalars().all())


async def get_attachments(db: AsyncSession, case_id: str) -> list[AttachmentRecord]:
    """Persisted attachment metadata records for a case."""
    evidence = await get_latest_evidence(db, case_id)
    if evidence is None:
        return []
    result = await db.execute(
        select(AttachmentRecord)
        .where(AttachmentRecord.evidence_id == evidence.id)
        .order_by(AttachmentRecord.filename)
    )
    return list(result.scalars().all())


async def get_iocs(db: AsyncSession, case_id: str) -> list[IOCRecord]:
    """Persisted observable IOC records for a case."""
    evidence = await get_latest_evidence(db, case_id)
    if evidence is None:
        return []
    result = await db.execute(
        select(IOCRecord)
        .where(IOCRecord.evidence_id == evidence.id)
        .order_by(IOCRecord.ioc_type, IOCRecord.value)
    )
    return list(result.scalars().all())


async def get_relationships(db: AsyncSession, case_id: str) -> list[EvidenceRelationshipRecord]:
    """Persisted evidence relationship records for a case."""
    evidence = await get_latest_evidence(db, case_id)
    if evidence is None:
        return []
    result = await db.execute(
        select(EvidenceRelationshipRecord)
        .where(EvidenceRelationshipRecord.evidence_id == evidence.id)
        .order_by(EvidenceRelationshipRecord.target_type, EvidenceRelationshipRecord.target_id)
    )
    return list(result.scalars().all())


async def get_evidence_summary(db: AsyncSession, case_id: str) -> dict[str, Any]:
    """Original evidence provenance plus persisted counts for a case.

    Counts always come from the persisted rows; nothing is computed client-side.
    """
    evidence = await get_latest_evidence(db, case_id)
    if evidence is None:
        return {
            "case_id": case_id, "evidence_id": "", "source_type": "",
            "source_identifier": "", "acquisition_method": "",
            "acquisition_timestamp": None, "content_type": "",
            "original_filename": "", "size": 0, "sha256": "",
            "mime_parts": 0, "received_hops": 0, "attachments": 0, "iocs": 0,
        }

    source = await get_source(db, evidence.source_id)
    return {
        "case_id": case_id,
        "evidence_id": evidence.id,
        "source_type": source.source_type if source else "",
        "source_identifier": source.source_id if source else "",
        "acquisition_method": source.acquisition_method if source else "",
        "acquisition_timestamp": (
            source.acquisition_timestamp.isoformat()
            if source and source.acquisition_timestamp else None
        ),
        "content_type": evidence.content_type,
        "original_filename": evidence.original_filename,
        "size": evidence.size,
        "sha256": evidence.sha256,
        "mime_parts": await _count(db, MimePartRecord, evidence.id),
        "received_hops": await _count(db, ReceivedHopRecord, evidence.id),
        "attachments": await _count(db, AttachmentRecord, evidence.id),
        "iocs": await _count(db, IOCRecord, evidence.id),
    }


async def _count(db: AsyncSession, model, evidence_id: str) -> int:
    result = await db.execute(
        select(func.count()).select_from(model).where(model.evidence_id == evidence_id)
    )
    return int(result.scalar() or 0)