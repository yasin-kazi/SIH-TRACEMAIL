export interface Anomaly {
  id: string;
  title: string;
  weight: number;
  description: string;
  icon: string;
  severity: 'error' | 'warning' | 'info';
}

export interface IdentityVector {
  envelopeFrom: { value: string; status: string; };
  replyTo: { value: string; status: string; };
  returnPath: { value: string; status: string; };
}

export interface AttackStep {
  label: string;
  status: string;
  icon: string;
  severity: 'error' | 'warning' | 'info' | 'primary';
}

export interface AuthResult {
  protocol: string;
  result: string;
  detail: string;
}

export interface Contradiction {
  id: string;
  title: string;
  severity: string;
  severityColor: string;
  description: string;
  confidence?: number;
  detail?: string;
  icon?: string;
  observedValue?: string;
  expectedValue?: string;
  treeNode?: string;
}

export interface EvidenceRow {
  field: string;
  observed: string;
  expected: string;
  status: string;
  ref: string;
}

export interface GraphNodeData {
  id: string;
  type: 'email' | 'identity' | 'domain' | 'ip' | 'campaign';
  label: string;
  sublabel: string;
  risk?: string;
}

export interface GraphEdgeData {
  id: string;
  source: string;
  target: string;
  label: string;
  variant?: 'hostile' | 'normal' | 'verified';
}

export interface IntelData {
  category: string;
  title: string;
  score: string;
  geo: string;
  asn: string;
  desc: string;
  icon: string;
  colorClass: string;
}

export interface ChainEvent {
  icon: string;
  title: string;
  detail: string;
  colorClass: string;
}

export interface Campaign {
  id: string;
  name: string;
  threatClass: string;
  emailCount: number;
  riskScore: number;
  firstSeen: string;
  lastSeen: string;
  description: string;
  relatedDomains: string[];
  relatedIps: string[];
}

export interface CaseData {
  id: string;
  emailSubject: string;
  from: string;
  to: string;
  receivedDate: string;
  threatClass: string;
  riskScore: number;
  identityConsistency: number;
  modelConfidence: number;
  evidenceConfidence: number;
  nonRepudiation: string;
  authentication: AuthResult[];
  anomalies: Anomaly[];
  identityVector: IdentityVector;
  attackPath: AttackStep[];
  graphNodes: GraphNodeData[];
  graphEdges: GraphEdgeData[];
  intelData: Record<string, IntelData>;
  contradictions: Contradiction[];
  evidenceTable: EvidenceRow[];
  chainOfCustody: ChainEvent[];
  sha256: string;
  vaultId: string;
  campaignId: string;
}
