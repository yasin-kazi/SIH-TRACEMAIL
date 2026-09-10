import { request, upload } from './client';
import type { CampaignData, Case, CopilotMessage, EvidenceFinding, EvidenceRelationship, ForensicAttachment, ForensicSummary, IdentityAnalysis, InfrastructureData, IOC, MimePart, ReportData, TimelineEvent, TransitHop } from '../types';

type WireCase = {
  id: string; number: number; title: string; subject: string; threat_type: Case['threatType']; risk_score: number;
  risk_level: Case['riskLevel']; identity_consistency: number; model_confidence: number; evidence_confidence: number;
  status: Case['status']; received_date: string; sender_name: string; sender_email: string; sender_domain: string;
  to_email: string; reply_to: string; return_path: string; received_ip: string; spf_result: Case['spfResult'];
  dkim_result: Case['dkimResult']; dmarc_result: Case['dmarcResult']; sha256: string; file_name: string; file_size: number;
};
const caseFromWire = (c: WireCase): Case => ({
  id: c.id, number: c.number, title: c.title, subject: c.subject, threatType: c.threat_type, riskScore: c.risk_score,
  riskLevel: c.risk_level, identityConsistency: c.identity_consistency, modelConfidence: c.model_confidence,
  evidenceConfidence: c.evidence_confidence, status: c.status, receivedDate: c.received_date, senderName: c.sender_name,
  senderEmail: c.sender_email, senderDomain: c.sender_domain, toEmail: c.to_email, replyTo: c.reply_to,
  returnPath: c.return_path, receivedIp: c.received_ip, spfResult: c.spf_result, dkimResult: c.dkim_result,
  dmarcResult: c.dmarc_result, sha256: c.sha256, fileName: c.file_name, fileSize: c.file_size, sourceType: (c as any).source_type, analysisStatus: (c as any).analysis_status,
});

export type UploadResult = { case_id: string; case_number: number; status: string; source_type: string; evidence_id: string; analysis_status: string; message: string };
export const listCases = async () => (await request<WireCase[]>('/api/cases')).map(caseFromWire);
export const getCase = async (id: string) => caseFromWire(await request<WireCase>(`/api/cases/${id}`));
export const uploadEmail = (file: File) => upload<UploadResult>('/api/cases/upload', file);
export const getIdentity = async (id: string): Promise<IdentityAnalysis> => {
  const value: any = await request(`/api/cases/${id}/identity`);
  return { caseId: value.case_id, score: value.score, displayName: value.display_name, fromAddress: value.from_address, fromDomain: value.from_domain, replyTo: value.reply_to, replyToDomain: value.reply_to_domain, returnPath: value.return_path, returnPathDomain: value.return_path_domain, dkimDomain: value.dkim_domain, sourceIp: value.source_ip, sourceAsn: value.source_asn, sourceLocation: value.source_location, sourceProvider: value.source_provider, contradictions: value.contradictions, chain: value.chain };
};
export const getEvidence = async (id: string): Promise<EvidenceFinding[]> => (await request<any[]>(`/api/cases/${id}/evidence`)).map(value => ({ id: value.id, title: value.title, description: value.description, severity: value.severity, riskBadge: value.risk_badge, code: value.code, evidenceState: value.evidence_state, confidence: value.confidence, source: value.source, tags: value.tags, colorAccent: value.color_accent }));
export const getHeaders = (id: string) => request<{ headers: Array<{key: string; value: string; is_anomalous?: boolean; badge?: string}>; raw: string }>(`/api/cases/${id}/headers`);
export const getTransitHops = async (id: string): Promise<TransitHop[]> => {
  const value: any = await request(`/api/cases/${id}/transit-hops`);
  return (value.hops ?? []).map((h: any) => ({
    label: h.label, ip: h.ip, description: h.description, type: h.hop_type,
    sequence: h.sequence, rawHeader: h.raw_header, fromHost: h.from_host,
    byHost: h.by_host, sourceIp: h.source_ip, protocol: h.protocol, timestamp: h.timestamp,
  }));
};
export const getMimeParts = async (id: string): Promise<MimePart[]> => (await request<any[]>(`/api/cases/${id}/mime-parts`)).map(v => ({ id: v.id, partIndex: v.part_index, parentId: v.parent_id, depth: v.depth, contentType: v.content_type, disposition: v.disposition, filename: v.filename, contentId: v.content_id, size: v.size, transferEncoding: v.transfer_encoding, isAttachment: v.is_attachment }));
export const getAttachments = async (id: string): Promise<ForensicAttachment[]> => (await request<any[]>(`/api/cases/${id}/attachments`)).map(v => ({ id: v.id, filename: v.filename, contentType: v.content_type, size: v.size, disposition: v.disposition, contentId: v.content_id, sha256: v.sha256 }));
export const getIOCs = async (id: string): Promise<IOC[]> => (await request<any[]>(`/api/cases/${id}/iocs`)).map(v => ({ id: v.id, type: v.type, value: v.value, source: v.source }));
export const getRelationships = async (id: string): Promise<EvidenceRelationship[]> => (await request<any[]>(`/api/cases/${id}/relationships`)).map(v => ({ id: v.id, relationType: v.relation_type, sourceType: v.source_type, sourceId: v.source_id, targetType: v.target_type, targetId: v.target_id }));
export const getForensicSummary = async (id: string): Promise<ForensicSummary> => { const v: any = await request(`/api/cases/${id}/forensic-summary`); return { caseId: v.case_id, evidenceId: v.evidence_id, sourceType: v.source_type, sourceIdentifier: v.source_identifier, acquisitionMethod: v.acquisition_method, acquisitionTimestamp: v.acquisition_timestamp, contentType: v.content_type, originalFilename: v.original_filename, size: v.size, sha256: v.sha256, mimeParts: v.mime_parts, receivedHops: v.received_hops, attachments: v.attachments, iocs: v.iocs }; };
export const getInfrastructure = async (id: string): Promise<InfrastructureData> => { const value: any = await request(`/api/cases/${id}/infrastructure`); return { caseId: value.case_id, sourceIp: value.source_ip, asn: value.asn, provider: value.provider, location: value.location, country: value.country, latitude: value.latitude, longitude: value.longitude, domain: value.domain, relatedDomains: value.related_domains, relatedCases: value.related_cases, threatScore: value.threat_score, infrastructureType: value.infrastructure_type, threatFeeds: value.threat_feeds }; };
export const getGraph = (id: string) => request<{ nodes: unknown[]; edges: unknown[] }>(`/api/cases/${id}/graph`);
export const getCampaign = async (id: string): Promise<CampaignData | null> => { const value: any = await request(`/api/cases/${id}/campaign`); return value && { id: value.id, name: value.name, relatedEmails: value.related_emails, sharedDomains: value.shared_domains, sharedInfrastructure: value.shared_infrastructure, relatedCases: value.related_cases, timeline: value.timeline.map((x: any) => ({date: x.date, title: x.title, type: x.event_type, description: x.description})), description: value.description }; };
export const getTimeline = async (id: string): Promise<TimelineEvent[]> => (await request<any[]>(`/api/cases/${id}/timeline`)).map(value => ({ id: value.id, time: value.time, title: value.title, description: value.description, type: value.event_type, icon: value.icon, details: value.details }));
const reportFromWire = (value: any): ReportData => ({caseId: value.case_id, executiveSummary: value.executive_summary, evidenceAnalysis: value.evidence_analysis, identityAnalysis: value.identity_analysis, infrastructureAnalysis: value.infrastructure_analysis, campaignCorrelation: value.campaign_correlation, attackPath: value.attack_path, confidenceAndLimitations: value.confidence_and_limitations, conclusion: value.conclusion, generatedAt: value.generated_at});
export const getReport = async (id: string) => reportFromWire(await request(`/api/reports/${id}`));
export const generateReport = async (id: string) => reportFromWire(await request(`/api/reports/${id}/generate`, { method: 'POST' }));
const messageFromWire = (value: any): CopilotMessage => ({id: value.id, role: value.role, content: value.content, timestamp: value.timestamp});
export const getCopilotMessages = async (id: string) => (await request<any[]>(`/api/copilot/${id}/messages`)).map(messageFromWire);
export const askCopilot = async (id: string, question: string) => messageFromWire(await request(`/api/copilot/${id}/ask`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({question}) }));
export const getSuggestedQuestions = (id: string) => request<{questions: string[]}>(`/api/copilot/${id}/suggested-questions`, { method: 'POST' });
