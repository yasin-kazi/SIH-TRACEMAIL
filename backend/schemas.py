from __future__ import annotations
from pydantic import BaseModel
from typing import Optional


class CaseBase(BaseModel):
    subject: str
    threat_type: str
    sender_name: str
    sender_email: str
    to_email: str


class CaseCreate(CaseBase):
    pass


class CaseResponse(BaseModel):
    id: str
    number: int
    title: str
    subject: str
    threat_type: str
    risk_score: int
    risk_level: str
    identity_consistency: int
    model_confidence: int
    evidence_confidence: int
    status: str
    received_date: str
    sender_name: str
    sender_email: str
    sender_domain: str
    to_email: str
    reply_to: str
    return_path: str
    received_ip: str
    spf_result: str
    dkim_result: str
    dmarc_result: str
    sha256: str
    file_name: str
    file_size: int
    campaign_id: Optional[str] = None
    source_type: str = "eml_upload"
    analysis_status: str = "completed"

    class Config:
        from_attributes = True


class IdentityContradictionOut(BaseModel):
    id: str
    title: str
    description: str
    severity: str
    risk_level: str
    tags: list[str]


class IdentityChainNodeOut(BaseModel):
    step: int
    label: str
    value: str
    status: str
    status_type: str
    subtitle: str
    meta: str
    meta_type: str


class IdentityResponse(BaseModel):
    case_id: str
    score: int
    display_name: str
    from_address: str
    from_domain: str
    reply_to: str
    reply_to_domain: str
    return_path: str
    return_path_domain: str
    dkim_domain: str
    source_ip: str
    source_asn: str
    source_location: str
    source_provider: str
    contradictions: list[IdentityContradictionOut]
    chain: list[IdentityChainNodeOut]


class EvidenceFindingResponse(BaseModel):
    id: str
    title: str
    description: str
    severity: str
    risk_badge: str
    code: str
    evidence_state: str
    confidence: int
    source: str
    tags: list[str]
    color_accent: str


class EmailHeaderOut(BaseModel):
    key: str
    value: str
    is_anomalous: bool = False
    badge: Optional[str] = None


class TransitHopOut(BaseModel):
    label: str
    ip: str
    description: str
    hop_type: str


class InfrastructureResponse(BaseModel):
    case_id: str
    source_ip: str
    asn: str
    provider: str
    location: str
    country: str
    latitude: float
    longitude: float
    domain: str
    related_domains: list[str]
    related_cases: int
    threat_score: int
    infrastructure_type: str
    threat_feeds: int


class GraphNodeOut(BaseModel):
    id: str
    node_type: str
    label: str
    sublabel: str
    badge: Optional[str] = None
    x: int
    y: int
    risk_score: int
    location: Optional[str] = None
    provider: Optional[str] = None
    asn_value: Optional[str] = None
    icon_class: str
    node_class: str
    badge_class: Optional[str] = None


class GraphEdgeOut(BaseModel):
    edge_from: str
    edge_to: str
    label: str
    color: str
    edge_type: str


class CampaignTimelineEventOut(BaseModel):
    date: str
    title: str
    event_type: str
    description: str


class CampaignResponse(BaseModel):
    id: str
    name: str
    related_emails: int
    shared_domains: list[str]
    shared_infrastructure: list[str]
    related_cases: int
    timeline: list[CampaignTimelineEventOut]
    description: str


class TimelineEventResponse(BaseModel):
    id: str
    time: str
    title: str
    description: str
    event_type: str
    icon: str
    details: Optional[str] = None


class CopilotMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    timestamp: str


class CopilotAskRequest(BaseModel):
    question: str


class ReportResponse(BaseModel):
    case_id: str
    executive_summary: str
    evidence_analysis: str
    identity_analysis: str
    infrastructure_analysis: str
    campaign_correlation: str
    attack_path: str
    confidence_and_limitations: str
    conclusion: str
    generated_at: str


class UploadResponse(BaseModel):
    case_id: str
    status: str
    message: str
    case_number: Optional[int] = None
    source_type: str = "eml_upload"
    evidence_id: Optional[str] = None
    analysis_status: str = "completed"


class MimePartOut(BaseModel):
    id: str
    part_index: int
    parent_id: Optional[int] = None
    depth: int
    content_type: str
    disposition: str
    filename: str
    content_id: str
    size: int
    transfer_encoding: str
    is_attachment: bool


class AttachmentOut(BaseModel):
    id: str
    filename: str
    content_type: str
    size: int
    disposition: str
    content_id: str
    sha256: str


class IocOut(BaseModel):
    id: str
    type: str
    value: str
    source: str


class EvidenceRelationshipOut(BaseModel):
    id: str
    relation_type: str
    source_type: str
    source_id: str
    target_type: str
    target_id: str


class ForensicSummary(BaseModel):
    case_id: str
    evidence_id: str
    source_type: str
    source_identifier: str
    acquisition_method: str
    acquisition_timestamp: Optional[str] = None
    content_type: str
    original_filename: str
    size: int
    sha256: str
    mime_parts: int
    received_hops: int
    attachments: int
    iocs: int


# ─── Gmail acquisition ────────────────────────────────────────

class GmailAuthStartResponse(BaseModel):
    auth_url: str


class GmailStatusResponse(BaseModel):
    connected: bool
    source: str = "gmail"
    status: str = "missing"
    account: Optional[str] = None


class GmailMessageOut(BaseModel):
    id: str
    thread_id: str
    snippet: str = ""
    from_address: str = ""
    subject: str = ""
    date: str = ""
    internal_date_ms: Optional[int] = None
    size_estimate: Optional[int] = None


class GmailSearchResponse(BaseModel):
    messages: list[GmailMessageOut]
    next_page_token: Optional[str] = None
    result_size_estimate: int = 0


class GmailAnalyzeRequest(BaseModel):
    message_id: str


class GmailRevokeResponse(BaseModel):
    status: str = "disconnected"
