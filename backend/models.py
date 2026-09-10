from __future__ import annotations
import datetime as _dt
from sqlalchemy import String, Integer, Float, Text, DateTime, ForeignKey, LargeBinary, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    number: Mapped[int] = mapped_column(Integer, unique=True)
    title: Mapped[str] = mapped_column(String(256))
    subject: Mapped[str] = mapped_column(String(512))
    threat_type: Mapped[str] = mapped_column(String(32))
    risk_score: Mapped[int] = mapped_column(Integer, default=0)
    risk_level: Mapped[str] = mapped_column(String(32), default="Low Risk")
    identity_consistency: Mapped[int] = mapped_column(Integer, default=100)
    model_confidence: Mapped[int] = mapped_column(Integer, default=0)
    evidence_confidence: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default="Active")
    received_date: Mapped[str] = mapped_column(String(128))
    sender_name: Mapped[str] = mapped_column(String(256))
    sender_email: Mapped[str] = mapped_column(String(256))
    sender_domain: Mapped[str] = mapped_column(String(256))
    to_email: Mapped[str] = mapped_column(String(256))
    reply_to: Mapped[str] = mapped_column(String(256), default="")
    return_path: Mapped[str] = mapped_column(String(256), default="")
    received_ip: Mapped[str] = mapped_column(String(64), default="")
    spf_result: Mapped[str] = mapped_column(String(16), default="NONE")
    dkim_result: Mapped[str] = mapped_column(String(16), default="NONE")
    dmarc_result: Mapped[str] = mapped_column(String(16), default="NONE")
    sha256: Mapped[str] = mapped_column(String(128), default="")
    file_name: Mapped[str] = mapped_column(String(256), default="")
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    raw_headers: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_eml: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[_dt.datetime] = mapped_column(DateTime, default=_dt.datetime.utcnow)

    identity = relationship("IdentityRecord", back_populates="case", uselist=False)
    evidence = relationship("EvidenceFindingRecord", back_populates="case")
    infrastructure = relationship("InfrastructureRecord", back_populates="case", uselist=False)
    timeline = relationship("TimelineEventRecord", back_populates="case")
    campaign_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_type: Mapped[str] = mapped_column(String(32), default="eml_upload")
    analysis_status: Mapped[str] = mapped_column(String(32), default="completed")


class IdentityRecord(Base):
    __tablename__ = "identities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"))
    score: Mapped[int] = mapped_column(Integer, default=100)
    display_name: Mapped[str] = mapped_column(String(256), default="")
    from_address: Mapped[str] = mapped_column(String(256), default="")
    from_domain: Mapped[str] = mapped_column(String(256), default="")
    reply_to: Mapped[str] = mapped_column(String(256), default="")
    reply_to_domain: Mapped[str] = mapped_column(String(256), default="")
    return_path: Mapped[str] = mapped_column(String(256), default="")
    return_path_domain: Mapped[str] = mapped_column(String(256), default="")
    dkim_domain: Mapped[str] = mapped_column(String(256), default="")
    source_ip: Mapped[str] = mapped_column(String(64), default="")
    source_asn: Mapped[str] = mapped_column(String(64), default="")
    source_location: Mapped[str] = mapped_column(String(256), default="")
    source_provider: Mapped[str] = mapped_column(String(256), default="")
    contradictions_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    chain_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    case = relationship("Case", back_populates="identity")


class SourceRecord(Base):
    """Acquisition provenance.  Provider adapters will share this contract later."""
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), index=True)
    source_type: Mapped[str] = mapped_column(String(32))
    source_id: Mapped[str] = mapped_column(String(512), default="")
    acquisition_timestamp: Mapped[_dt.datetime] = mapped_column(DateTime, default=_dt.datetime.utcnow)
    acquisition_method: Mapped[str] = mapped_column(String(64), default="upload")
    provenance_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class EvidenceRecord(Base):
    """Immutable original bytes separate from parsed and derived case data."""
    __tablename__ = "evidence_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), index=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("sources.id"), index=True)
    evidence_type: Mapped[str] = mapped_column(String(32), default="original_email")
    status: Mapped[str] = mapped_column(String(32), default="preserved")
    original_filename: Mapped[str] = mapped_column(String(256))
    content_type: Mapped[str] = mapped_column(String(128), default="message/rfc822")
    size: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(128), index=True)
    original_bytes: Mapped[bytes] = mapped_column(LargeBinary)
    ingested_at: Mapped[_dt.datetime] = mapped_column(DateTime, default=_dt.datetime.utcnow)

    mime_parts = relationship("MimePartRecord", back_populates="evidence", cascade="all, delete-orphan")
    received_hops = relationship("ReceivedHopRecord", back_populates="evidence", cascade="all, delete-orphan")
    attachments = relationship("AttachmentRecord", back_populates="evidence", cascade="all, delete-orphan")
    iocs = relationship("IOCRecord", back_populates="evidence", cascade="all, delete-orphan")
    relationships = relationship("EvidenceRelationshipRecord", back_populates="evidence", cascade="all, delete-orphan")


class MimePartRecord(Base):
    """Normalized metadata for one MIME part found in the evidence email.

    Only metadata is persisted; attachment payloads are never opened or executed.
    """
    __tablename__ = "mime_parts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    evidence_id: Mapped[str] = mapped_column(ForeignKey("evidence_records.id"), index=True)
    part_index: Mapped[int] = mapped_column(Integer)
    parent_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    depth: Mapped[int] = mapped_column(Integer, default=0)
    content_type: Mapped[str] = mapped_column(String(128), default="")
    disposition: Mapped[str] = mapped_column(String(64), default="")
    filename: Mapped[str] = mapped_column(String(256), default="")
    content_id: Mapped[str] = mapped_column(String(256), default="")
    size: Mapped[int] = mapped_column(Integer, default=0)
    transfer_encoding: Mapped[str] = mapped_column(String(64), default="")
    is_attachment: Mapped[bool] = mapped_column(Boolean, default=False)

    evidence = relationship("EvidenceRecord", back_populates="mime_parts")


class ReceivedHopRecord(Base):
    """One observed Received-header transit hop from the evidence email.

    Values are persisted only when present in the actual header; nothing is
    fabricated and no attacker identity is inferred.
    """
    __tablename__ = "received_hops"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    evidence_id: Mapped[str] = mapped_column(ForeignKey("evidence_records.id"), index=True)
    sequence: Mapped[int] = mapped_column(Integer)
    label: Mapped[str] = mapped_column(String(32))
    hop_type: Mapped[str] = mapped_column(String(32))
    from_host: Mapped[str] = mapped_column(String(256), default="")
    by_host: Mapped[str] = mapped_column(String(256), default="")
    source_ip: Mapped[str] = mapped_column(String(64), default="")
    protocol: Mapped[str] = mapped_column(String(64), default="")
    timestamp: Mapped[str] = mapped_column(String(128), default="")
    raw_header: Mapped[str] = mapped_column(Text, default="")
    description: Mapped[str] = mapped_column(Text, default="")

    evidence = relationship("EvidenceRecord", back_populates="received_hops")


class AttachmentRecord(Base):
    """Metadata-only record of an attachment found in the evidence email.

    No attachment payload is stored, opened or executed; only the SHA-256 of the
    (transfer-decoded) payload is recorded for integrity.
    """
    __tablename__ = "attachments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    evidence_id: Mapped[str] = mapped_column(ForeignKey("evidence_records.id"), index=True)
    filename: Mapped[str] = mapped_column(String(256), default="")
    mime_type: Mapped[str] = mapped_column(String(128), default="")
    size: Mapped[int] = mapped_column(Integer, default=0)
    sha256: Mapped[str] = mapped_column(String(128), default="")
    disposition: Mapped[str] = mapped_column(String(64), default="")
    content_id: Mapped[str] = mapped_column(String(256), default="")

    evidence = relationship("EvidenceRecord", back_populates="attachments")


class IOCRecord(Base):
    """One observable indicator found in the evidence email.

    Only observable values are stored. An IOC is never labelled malicious merely
    because it was extracted.
    """
    __tablename__ = "iocs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    evidence_id: Mapped[str] = mapped_column(ForeignKey("evidence_records.id"), index=True)
    ioc_type: Mapped[str] = mapped_column(String(32))
    value: Mapped[str] = mapped_column(String(1024))
    source: Mapped[str] = mapped_column(String(128), default="")
    created_at: Mapped[_dt.datetime] = mapped_column(DateTime, default=_dt.datetime.utcnow)

    evidence = relationship("EvidenceRecord", back_populates="iocs")


class EvidenceRelationshipRecord(Base):
    """Lightweight consists-of links from an evidence record to its children.

    Store-and-forward graph queries can join on target_type/target_id later; no
    graph database is required for this phase.
    """
    __tablename__ = "evidence_relationships"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    evidence_id: Mapped[str] = mapped_column(ForeignKey("evidence_records.id"), index=True)
    relation_type: Mapped[str] = mapped_column(String(32), default="contains")
    target_type: Mapped[str] = mapped_column(String(32))
    target_id: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[_dt.datetime] = mapped_column(DateTime, default=_dt.datetime.utcnow)

    evidence = relationship("EvidenceRecord", back_populates="relationships")


class EvidenceFindingRecord(Base):
    __tablename__ = "evidence_findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"))
    finding_id: Mapped[str] = mapped_column(String(32))
    title: Mapped[str] = mapped_column(String(256))
    description: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(32))
    risk_badge: Mapped[str] = mapped_column(String(32))
    code: Mapped[str] = mapped_column(String(256))
    evidence_state: Mapped[str] = mapped_column(String(32))
    confidence: Mapped[int] = mapped_column(Integer, default=0)
    source: Mapped[str] = mapped_column(String(128))
    tags_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    color_accent: Mapped[str] = mapped_column(String(32), default="secondary-container")

    case = relationship("Case", back_populates="evidence")


class InfrastructureRecord(Base):
    __tablename__ = "infrastructure"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), unique=True)
    source_ip: Mapped[str] = mapped_column(String(64))
    asn: Mapped[str] = mapped_column(String(64))
    provider: Mapped[str] = mapped_column(String(256))
    location: Mapped[str] = mapped_column(String(256))
    country: Mapped[str] = mapped_column(String(128))
    latitude: Mapped[float] = mapped_column(Float, default=0.0)
    longitude: Mapped[float] = mapped_column(Float, default=0.0)
    domain: Mapped[str] = mapped_column(String(256))
    related_domains_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    related_cases: Mapped[int] = mapped_column(Integer, default=0)
    threat_score: Mapped[int] = mapped_column(Integer, default=0)
    infrastructure_type: Mapped[str] = mapped_column(String(256))
    threat_feeds: Mapped[int] = mapped_column(Integer, default=0)

    case = relationship("Case", back_populates="infrastructure")


class TimelineEventRecord(Base):
    __tablename__ = "timeline_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"))
    event_id: Mapped[str] = mapped_column(String(32))
    time: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(256))
    description: Mapped[str] = mapped_column(Text)
    event_type: Mapped[str] = mapped_column(String(32))
    icon: Mapped[str] = mapped_column(String(64))
    details: Mapped[str | None] = mapped_column(Text, nullable=True)

    case = relationship("Case", back_populates="timeline")


class CampaignRecord(Base):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    related_emails: Mapped[int] = mapped_column(Integer, default=0)
    shared_domains_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    shared_infra_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    related_cases: Mapped[int] = mapped_column(Integer, default=0)
    timeline_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")


class CopilotMessageRecord(Base):
    __tablename__ = "copilot_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"))
    msg_id: Mapped[str] = mapped_column(String(64))
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[str] = mapped_column(String(64))


class ReportRecord(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), unique=True)
    executive_summary: Mapped[str] = mapped_column(Text, default="")
    evidence_analysis: Mapped[str] = mapped_column(Text, default="")
    identity_analysis: Mapped[str] = mapped_column(Text, default="")
    infrastructure_analysis: Mapped[str] = mapped_column(Text, default="")
    campaign_correlation: Mapped[str] = mapped_column(Text, default="")
    attack_path: Mapped[str] = mapped_column(Text, default="")
    confidence_and_limitations: Mapped[str] = mapped_column(Text, default="")
    conclusion: Mapped[str] = mapped_column(Text, default="")
    generated_at: Mapped[str] = mapped_column(String(128), default="")


class GmailConnection(Base):
    """Server-side Gmail OAuth connection (single active connection today).

    Tokens are stored in encrypted form (AES-256-GCM, key from configuration)
    and only ever decrypted inside the backend token store. The status column
    distinguishes ``connected``, ``expired`` (access token), and ``revoked``
    (user/provider revoked access — reconnect required). No frontend code and no
    log may ever see plaintext token material.
    """

    __tablename__ = "gmail_connections"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    account_email: Mapped[str] = mapped_column(String(256), unique=True, default="")
    access_token_enc: Mapped[str] = mapped_column(Text, default="")
    refresh_token_enc: Mapped[str] = mapped_column(Text, default="")
    access_token_expires_at: Mapped[_dt.datetime | None] = mapped_column(DateTime, nullable=True)
    scopes_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="connected")
    created_at: Mapped[_dt.datetime] = mapped_column(DateTime, default=_dt.datetime.utcnow)
