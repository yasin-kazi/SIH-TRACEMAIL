export type ThreatType = 'BEC' | 'Credential Phishing' | 'Spoofing' | 'Malware' | 'Spam';
export type RiskLevel = 'High Risk' | 'Medium Risk' | 'Low Risk';
export type EvidenceState = 'OBSERVED' | 'INFERRED' | 'ENRICHED' | 'UNKNOWN';
export type AuthResult = 'PASS' | 'FAIL' | 'NONE' | 'SOFTFAIL';
export type Severity = 'Critical' | 'High' | 'Medium' | 'Low' | 'Informational';
export type CaseStatus = 'Active' | 'Resolved' | 'Escalated';

export interface Case {
  id: string;
  number: number;
  title: string;
  subject: string;
  threatType: ThreatType;
  riskScore: number;
  riskLevel: RiskLevel;
  identityConsistency: number;
  modelConfidence: number;
  evidenceConfidence: number;
  status: CaseStatus;
  receivedDate: string;
  senderName: string;
  senderEmail: string;
  senderDomain: string;
  toEmail: string;
  replyTo: string;
  returnPath: string;
  receivedIp: string;
  spfResult: AuthResult;
  dkimResult: AuthResult;
  dmarcResult: AuthResult;
  sha256: string;
  fileName: string;
  fileSize: number;
  sourceType?: string;
  analysisStatus?: string;
}

export interface IdentityAnalysis {
  caseId: string;
  score: number;
  displayName: string;
  fromAddress: string;
  fromDomain: string;
  replyTo: string;
  replyToDomain: string;
  returnPath: string;
  returnPathDomain: string;
  dkimDomain: string;
  sourceIp: string;
  sourceAsn: string;
  sourceLocation: string;
  sourceProvider: string;
  contradictions: IdentityContradiction[];
  chain: IdentityChainNode[];
}

export interface IdentityContradiction {
  id: string;
  title: string;
  description: string;
  severity: Severity;
  riskLevel: string;
  tags: string[];
}

export interface IdentityChainNode {
  step: number;
  label: string;
  value: string;
  status: string;
  statusType: 'error' | 'warning' | 'success' | 'neutral';
  subtitle: string;
  meta: string;
  metaType: 'error' | 'warning' | 'success' | 'neutral';
}

export interface EvidenceFinding {
  id: string;
  title: string;
  description: string;
  severity: Severity;
  riskBadge: string;
  code: string;
  evidenceState: EvidenceState;
  confidence: number;
  source: string;
  tags: string[];
  colorAccent: 'error' | 'secondary-container' | 'primary-container';
}

export interface EmailHeader {
  key: string;
  value: string;
  isAnomalous?: boolean;
  badge?: string;
}

export interface TransitHop {
  label: string;
  ip: string;
  description: string;
  type: 'source' | 'relay' | 'destination';
  sequence?: number;
  rawHeader?: string;
  fromHost?: string;
  byHost?: string;
  sourceIp?: string;
  protocol?: string;
  timestamp?: string;
}

export interface MimePart {
  id: string;
  partIndex: number;
  parentId?: number | null;
  depth: number;
  contentType: string;
  disposition: string;
  filename: string;
  contentId: string;
  size: number;
  transferEncoding: string;
  isAttachment: boolean;
}

export interface ForensicAttachment {
  id: string;
  filename: string;
  contentType: string;
  size: number;
  disposition: string;
  contentId: string;
  sha256: string;
}

export interface IOC {
  id: string;
  type: string;
  value: string;
  source: string;
}

export interface EvidenceRelationship {
  id: string;
  relationType: string;
  sourceType: string;
  sourceId: string;
  targetType: string;
  targetId: string;
}

export interface ForensicSummary {
  caseId: string;
  evidenceId: string;
  sourceType: string;
  sourceIdentifier: string;
  acquisitionMethod: string;
  acquisitionTimestamp?: string;
  contentType: string;
  originalFilename: string;
  size: number;
  sha256: string;
  mimeParts: number;
  receivedHops: number;
  attachments: number;
  iocs: number;
}

export interface InfrastructureData {
  caseId: string;
  sourceIp: string;
  asn: string;
  provider: string;
  location: string;
  country: string;
  latitude: number;
  longitude: number;
  domain: string;
  relatedDomains: string[];
  relatedCases: number;
  threatScore: number;
  infrastructureType: string;
  threatFeeds: number;
}

export interface GraphNode {
  id: string;
  type: 'email' | 'domain' | 'ip' | 'asn' | 'campaign';
  label: string;
  sublabel: string;
  badge?: string;
  x: number;
  y: number;
  riskScore: number;
  location?: string;
  provider?: string;
  asnValue?: string;
  iconClass: string;
  nodeClass: string;
  badgeClass?: string;
}

export interface GraphEdge {
  from: string;
  to: string;
  label: string;
  color: string;
  type: 'solid' | 'dashed';
}

export interface CampaignData {
  id: string;
  name: string;
  relatedEmails: number;
  sharedDomains: string[];
  sharedInfrastructure: string[];
  relatedCases: number;
  timeline: CampaignTimelineEvent[];
  description: string;
}

export interface CampaignTimelineEvent {
  date: string;
  title: string;
  type: EvidenceState;
  description: string;
}

export interface TimelineEvent {
  id: string;
  time: string;
  title: string;
  description: string;
  type: EvidenceState;
  icon: string;
  details?: string;
}

export interface CopilotMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface ReportData {
  caseId: string;
  executiveSummary: string;
  evidenceAnalysis: string;
  identityAnalysis: string;
  infrastructureAnalysis: string;
  campaignCorrelation: string;
  attackPath: string;
  confidenceAndLimitations: string;
  conclusion: string;
  generatedAt: string;
}

export type NavPath = 'overview' | 'identity' | 'evidence' | 'infrastructure' | 'graph' | 'campaign' | 'timeline' | 'copilot' | 'report';
