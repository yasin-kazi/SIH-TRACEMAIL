"""Builders that normalize parsed email structures into persisted forensic records.

These builders are pure: they take parsed data plus an evidence id and return a
flat list of ORM objects. The caller adds them to the session and commits.
Nothing here opens, decodes, renders or executes email content.
"""
from __future__ import annotations

import uuid
from typing import Any

from models import (
    MimePartRecord,
    ReceivedHopRecord,
    AttachmentRecord,
    IOCRecord,
    EvidenceRelationshipRecord,
)
from services.ioc_extraction import extract_iocs


def build_forensic_records(evidence_id: str, parsed: dict[str, Any]) -> list[object]:
    """Build MIME, hop, attachment, IOC and relationship records for an evidence id.

    Relationships are created only for children that actually exist; an email
    with no MIME parts, hops, attachments or IOCs produces no fabricated rows.
    """
    records: list[object] = []

    for part in parsed.get("mime_parts") or []:
        mime = MimePartRecord(
            id=uuid.uuid4().hex,
            evidence_id=evidence_id,
            part_index=part["part_index"],
            parent_index=part.get("parent_index"),
            depth=part.get("depth", 0),
            content_type=part.get("content_type", ""),
            disposition=part.get("disposition", ""),
            filename=part.get("filename", ""),
            content_id=part.get("content_id", ""),
            size=part.get("size", 0),
            transfer_encoding=part.get("transfer_encoding", ""),
            is_attachment=bool(part.get("is_attachment")),
        )
        records.append(mime)
        records.append(_relationship(evidence_id, "mime_part", mime.id))

    for hop in parsed.get("received_hops") or []:
        h = ReceivedHopRecord(
            id=uuid.uuid4().hex,
            evidence_id=evidence_id,
            sequence=hop.get("sequence", 0),
            label=hop.get("label", ""),
            hop_type=hop.get("hop_type", ""),
            from_host=hop.get("from_host", ""),
            by_host=hop.get("by_host", ""),
            source_ip=hop.get("source_ip", ""),
            protocol=hop.get("protocol", ""),
            timestamp=hop.get("timestamp", ""),
            raw_header=hop.get("raw_header", ""),
            description=hop.get("description", ""),
        )
        records.append(h)
        records.append(_relationship(evidence_id, "received_hop", h.id))

    for attachment in parsed.get("attachments") or []:
        att = AttachmentRecord(
            id=uuid.uuid4().hex,
            evidence_id=evidence_id,
            filename=attachment.get("filename", ""),
            mime_type=attachment.get("mime_type", ""),
            size=attachment.get("size", 0),
            sha256=attachment.get("sha256", ""),
            disposition=attachment.get("disposition", ""),
            content_id=attachment.get("content_id", ""),
        )
        records.append(att)
        records.append(_relationship(evidence_id, "attachment", att.id))

    for ioc in extract_iocs(parsed):
        ioc_rec = IOCRecord(
            id=uuid.uuid4().hex,
            evidence_id=evidence_id,
            ioc_type=ioc["ioc_type"],
            value=ioc["value"],
            source=ioc["source"],
        )
        records.append(ioc_rec)
        records.append(_relationship(evidence_id, "ioc", ioc_rec.id))

    return records


def _relationship(evidence_id: str, target_type: str, target_id: str) -> EvidenceRelationshipRecord:
    return EvidenceRelationshipRecord(
        id=uuid.uuid4().hex,
        evidence_id=evidence_id,
        relation_type="contains",
        target_type=target_type,
        target_id=target_id,
    )