# SIH26106 — AI-Powered Email Threat Detection, Geolocation & Forensic Intelligence Platform

## 1. OBJECTIVE

Develop a serious, technically defensible solution for Smart India Hackathon problem SIH26106.

The solution must NOT look like a generic:

> React + FastAPI + ML + Neo4j + APIs + dashboard

project.

The main goal is to build an **evidence-driven email forensic investigation platform** that can detect threats, analyze email authenticity, investigate infrastructure, correlate related incidents, reconstruct probable attack paths, and preserve forensic evidence.

---

# 2. OFFICIAL PROBLEM REQUIREMENTS



The SIH26106 problem requires capabilities including:

- AI/NLP/ML-based email threat detection
- Phishing detection
- Spoofing detection
- Impersonation detection
- Business Email Compromise (BEC)
- Fraud detection
- Deep email-header analysis
- Return-Path analysis
- Received-chain analysis
- Message-ID analysis
- Reply-To analysis
- DKIM analysis
- SPF analysis
- DMARC analysis
- Origin traceability
- Earliest reliable sending IP
- IP geolocation
- ISP/hosting information
- VPN/TOR/proxy/open-relay/botnet/cloud indicators
- Domain intelligence
- WHOIS/RDAP
- DNS
- MX
- Registrar
- Hosting information
- Identity correlation
- Threat-intelligence correlation
- Previous incident correlation
- Domain clusters
- Graph relationships
- Alerting
- Investigation dashboard
- Maps
- Forensic reports
- Case management
- Privacy/legal/compliance
- Evidence preservation
- Chain of custody

IMPORTANT:

The platform should provide **probable/observed source infrastructure and investigative intelligence**, NOT claim guaranteed physical attacker location or exact attacker identity.

---

# 3. COMPETITIVE REALITY

Do NOT claim that the following are unique:

- AI phishing detection
- SPF/DKIM/DMARC analysis
- IP geolocation
- VirusTotal integration
- Neo4j graph
- Threat-intelligence APIs
- forensic PDF generation
- dashboards
- maps

Commercial products such as Microsoft Defender, Proofpoint and Google Workspace already provide sophisticated email-security capabilities.

Publicly visible projects also exist that combine email analysis, AI, graphs, geolocation and forensic investigation.

Therefore:

## The differentiation must be in the FORENSIC REASONING ENGINE.

The project should compete on:

1. How evidence is represented
2. How contradictory evidence is detected
3. How evidence reliability is calculated
4. How multiple emails are correlated
5. How campaigns are discovered
6. How attack paths are reconstructed
7. How uncertainty is communicated
8. How an analyst can reproduce the reasoning

---

# 4. CENTRAL PRODUCT CONCEPT

## Forensic Email Evidence Engine

Treat every email as a forensic evidence package rather than simply a classification input.

Concept:

RAW EMAIL\
↓\
Evidence extraction\
↓\
Evidence normalization\
↓\
Authentication analysis\
↓\
Identity consistency analysis\
↓\
Content/social-engineering analysis\
↓\
Infrastructure intelligence\
↓\
Cross-case correlation\
↓\
Campaign discovery\
↓\
Evidence reliability assessment\
↓\
Forensic decision\
↓\
Attack-path reconstruction\
↓\
Investigation case

The final output should answer:

> What happened?

> Why is this email suspicious?

> Which evidence supports that conclusion?

> Which evidence contradicts it?

> How reliable is each finding?

> What infrastructure is associated with the email?

> Are other emails connected to the same campaign?

> What can and cannot be concluded from the available evidence?

---

# 5. CORE ARCHITECTURE

RAW .EML\
↓\
┌─────────────────────────────┐\
│ 1. EVIDENCE ACQUISITION     │\
│                             │\
│ MIME structure              │\
│ Headers                     │\
│ Body                        │\
│ URLs                        │\
│ Attachments                 │\
│ Metadata                    │\
│ Original SHA-256            │\
└──────────────┬──────────────┘\
↓\
┌─────────────────────────────┐\
│ 2. EVIDENCE NORMALIZATION   │\
│                             │\
│ RFC-aware parsing           │\
│ Header canonicalization     │\
│ Received-hop ordering       │\
│ URL normalization           │\
│ Domain normalization        │\
└──────────────┬──────────────┘\
↓\
┌─────────────────────────────┐\
│ 3. FORENSIC ENGINES         │\
│                             │\
│ Identity Contradiction      │\
│ Infrastructure Fingerprint  │\
│ Campaign Similarity         │\
│ Evidence Reliability        │\
└──────────────┬──────────────┘\
↓\
┌─────────────────────────────┐\
│ 4. INTELLIGENCE + AI        │\
│                             │\
│ NLP                         │\
│ Structured ML               │\
│ DNS/RDAP                    │\
│ IP/ASN/GeoIP                │\
│ Threat intelligence        │\
└──────────────┬──────────────┘\
↓\
┌─────────────────────────────┐\
│ 5. CORRELATION              │\
│                             │\
│ Email                       │\
│ Domain                      │\
│ IP                          │\
│ ASN                         │\
│ URL                         │\
│ Identity                    │\
│ Related emails              │\
└──────────────┬──────────────┘\
↓\
┌─────────────────────────────┐\
│ 6. FORENSIC DECISION        │\
│                             │\
│ Threat class                │\
│ Risk                        │\
│ Confidence                  │\
│ Evidence contribution       │\
│ Probable infrastructure     │\
│ Attribution hypothesis      │\
└──────────────┬──────────────┘\
↓\
┌─────────────────────────────┐\
│ 7. INVESTIGATION CASE       │\
│                             │\
│ Timeline                    │\
│ Graph                       │\
│ Map                         │\
│ Evidence                    │\
│ Related campaigns           │\
│ Forensic report             │\
└─────────────────────────────┘

---

# 6. MOST IMPORTANT CUSTOM COMPONENTS

## A. Identity Contradiction Engine

This should be one of the project's signature components.

Compare:

Display Name\
↕\
From\
↕\
Reply-To\
↕\
Return-Path\
↕\
DKIM Domain\
↕\
DMARC Alignment\
↕\
Sending Infrastructure

Example:

Display Name:\
CFO — ABC Technologies

From:\
[cfo@abc.com](mailto\:cfo@abc.com)

Reply-To:\
[cfo.abc@gmail.com](mailto\:cfo.abc@gmail.com)

Return-Path:\
[bounce@suspicious-domain.com](mailto\:bounce@suspicious-domain.com)

DKIM:\
abc.com

SPF:\
PASS

DKIM:\
PASS

DMARC:\
PASS

The system should NOT simply say:

> DMARC PASS = safe

Instead:

Identity Consistency = 34/100

Reasons:

- Reply-To mismatch
- Return-Path inconsistency
- Infrastructure unrelated to expected organization
- Lookalike domain detected
- Executive impersonation pattern

This is much more valuable than a basic authentication checker.

---

# 7. EVIDENCE RELIABILITY ENGINE

Every finding should have:

- Evidence
- Evidence source
- Evidence type
- Reliability
- Confidence
- Timestamp
- Supporting relationships
- Contradicting evidence

Example:

FINDING:\
Sending IP belongs to cloud-hosting provider.

Reliability:\
HIGH

Source:\
IP/ASN lookup

Confidence:\
0.98

Another finding:

FINDING:\
Probable geographic origin = location X.

Reliability:\
MEDIUM

Reason:\
IP geolocation identifies infrastructure location, not necessarily attacker location.

This distinction is essential.

---

# 8. INFRASTRUCTURE FINGERPRINTING ENGINE

Build an infrastructure profile around:

IP\
↓\
ASN\
↓\
ISP/provider\
↓\
Hosting organization\
↓\
DNS\
↓\
Domain\
↓\
MX\
↓\
Registrar\
↓\
URLs\
↓\
Other observed emails

Identify indicators such as:

- Cloud hosting
- VPN
- TOR
- Proxy
- Open relay
- Residential IP
- Datacenter IP
- Suspicious hosting
- Shared infrastructure
- Reused infrastructure

The output should describe the infrastructure, not falsely identify the human attacker.

---

# 9. CAMPAIGN DISCOVERY ENGINE

This is more important than simply classifying individual emails.

Suppose the system receives:

Email A\
Email B\
Email C

All have:

- Same suspicious domain
- Same IP
- Same URL infrastructure
- Similar language
- Similar sender identity
- Similar timing
- Same hosting provider

The system should discover:

> These emails are potentially part of the same campaign.

Graph:

EMAIL A\
↓\
DOMAIN X\
↓\
IP X\
↓\
ASN X

EMAIL B\
↓\
DOMAIN X\
↓\
IP X

EMAIL C\
↓\
URL X\
↓\
IP X

Therefore:

CAMPAIGN #17

This changes the system from an email classifier into an investigation platform.

---

# 10. ATTACK-PATH RECONSTRUCTION

The system should reconstruct the observed chain:

Sender identity\
↓\
Email infrastructure\
↓\
Received hops\
↓\
Sending IP\
↓\
Domain\
↓\
URL\
↓\
Hosting/ASN\
↓\
Related infrastructure\
↓\
Related cases

The analyst should see:

- What is directly observed
- What is inferred
- What is externally enriched
- What is uncertain

---

# 11. MULTI-EVIDENCE DECISION ENGINE

Do not depend on one ML model.

Combine:

### Technical evidence

- SPF
- DKIM
- DMARC
- headers
- Received chain
- Message-ID
- Return-Path
- Reply-To

### Identity evidence

- Display-name mismatch
- sender mismatch
- domain mismatch
- lookalike domain
- executive impersonation

### Linguistic evidence

- urgency
- payment requests
- credential requests
- social engineering
- impersonation
- unusual language patterns

### Infrastructure evidence

- IP reputation
- ASN
- hosting
- DNS
- domain age/context
- proxy/VPN/TOR indicators

### Historical evidence

- previously observed IP
- previously observed domain
- previous campaign
- previous incident

### Relationship evidence

- graph connections
- shared infrastructure
- shared URLs
- related emails

Output:

THREAT CLASS\
+\
RISK\
+\
CONFIDENCE\
+\
EVIDENCE CONTRIBUTIONS\
+\
INVESTIGATION HYPOTHESIS

---

# 12. AI/ML ROLE

AI should support forensic reasoning rather than replace it.

## NLP model

Detect:

- phishing language
- BEC
- impersonation
- urgency
- payment fraud
- credential harvesting
- social engineering

## Structured ML

Use technical features such as:

- authentication results
- domain features
- IP features
- URL features
- header inconsistencies
- infrastructure signals

XGBoost is suitable for structured features.

## Explainability

SHAP can expose which structured features influenced the prediction.

But SHAP itself is NOT the innovation.

The innovation is how model evidence is combined with forensic evidence.

---

# 13. GRAPH MODEL

Suggested entities:

EMAIL\
PERSON/IDENTITY\
DOMAIN\
IP\
URL\
ASN\
ORGANIZATION\
CAMPAIGN\
CASE\
ATTACHMENT\
INCIDENT

Relationships:

EMAIL → SENT\_BY → IDENTITY

EMAIL → USES → DOMAIN

EMAIL → CONTAINS → URL

EMAIL → ORIGINATED\_FROM → IP

IP → BELONGS\_TO → ASN

DOMAIN → RESOLVES\_TO → IP

EMAIL → PART\_OF → CAMPAIGN

EMAIL → RELATED\_TO → EMAIL

DOMAIN → RELATED\_TO → DOMAIN

IP → RELATED\_TO → IP

CASE → CONTAINS → EMAIL

Finding relationships should also be represented where useful.

---

# 14. STORAGE ARCHITECTURE

## PostgreSQL

Use for:

- users
- cases
- investigation metadata
- findings
- scores
- timestamps
- analyst actions
- report metadata

## MinIO

Use for:

- original .EML
- original attachments
- derived evidence
- forensic artifacts
- reports

Original evidence should be hashed.

## Neo4j

Use for:

- entity relationships
- infrastructure relationships
- campaign discovery
- cross-case correlation

---

# 15. FINAL TECH STACK

## Languages

- Python
- TypeScript
- SQL
- Cypher

## Backend

FastAPI

## Email Forensics

Python email/MIME processing\
+\
custom RFC-aware analysis

## AI

Transformer NLP\
+\
XGBoost\
+\
SHAP

## Correlation

Neo4j + Cypher

## Database

PostgreSQL

## Evidence Vault

MinIO

## Intelligence

VirusTotal\
AbuseIPDB\
RDAP\
DNS\
GeoIP/ASN data

## Frontend

React + TypeScript

## Visualization

Leaflet\
React Flow

## Reporting

ReportLab

## Deployment

Docker Compose

## Evidence Integrity

SHA-256

---

# 16. TECHNOLOGIES NOT TO ADD JUST FOR SHOW

Do NOT add:

- Kafka
- Kubernetes
- Redis
- Elasticsearch
- TensorFlow
- multiple blockchain systems
- unnecessary microservices
- dozens of APIs
- an AI chatbot
- blockchain without a clear chain-of-custody requirement

A smaller architecture with strong forensic logic is better than a huge architecture with no meaningful innovation.

---

# 17. BLOCKCHAIN POSITION

The SIH theme includes Blockchain & Cybersecurity.

That does NOT mean blockchain must be forced into the detection pipeline.

If blockchain is used, the defensible use case is:

Evidence Hash\
↓\
Evidence Record\
↓\
Timestamp\
↓\
Chain-of-Custody Event\
↓\
Tamper-Evident Audit Trail

Blockchain should be considered an optional/Phase-2 evidence-integrity component.

Do not use blockchain for:

- AI detection
- email classification
- geolocation
- ordinary database storage
- graph relationships

---

# 18. USER INTERFACE

The main screen should be an investigator workbench.

Example:

CASE #1042

Classification:\
BEC

Risk:\
91/100

Identity Consistency:\
34/100

Authentication:

SPF — PASS\
DKIM — PASS\
DMARC — PASS

Contradictions:

- Reply-To mismatch
- Lookalike domain
- Unrelated infrastructure
- Executive impersonation

Infrastructure:

Observed IP\
↓\
ASN\
↓\
Hosting provider\
↓\
Geographic region

Campaign:

3 related emails

Evidence:

HIGH CONFIDENCE\
Authentication observation

MEDIUM CONFIDENCE\
Infrastructure characterization

LOWER CONFIDENCE\
Attribution hypothesis

The UI should explain WHY the system reached its conclusion.

---

# 19. FORENSIC REPORT

Report should contain:

1. Case ID
2. Investigation timestamp
3. Original evidence hash
4. Email metadata
5. Header analysis
6. Authentication analysis
7. Identity consistency
8. URL/domain analysis
9. IP/ASN analysis
10. Infrastructure findings
11. Threat classification
12. Risk score
13. Evidence confidence
14. Related entities
15. Campaign relationships
16. Attack-path timeline
17. Attribution limitations
18. Analyst conclusion
19. Chain-of-custody information

---

# 20. FORENSIC ACCURACY RULES

NEVER say:

> “The attacker is located in Mumbai.”

Instead:

> “The observed sending infrastructure geolocates to Mumbai.”

NEVER say:

> “This IP identifies the attacker.”

Instead:

> “This IP is an observed/probable source infrastructure indicator.”

NEVER say:

> “SPF/DKIM/DMARC passed, therefore the email is safe.”

Instead:

> “Authentication passed, but authentication alone does not establish legitimate intent.”

A legitimate account may be compromised.

---

# 21. RECOMMENDED PROJECT STRUCTURE

sih26106/

├── frontend/\
│   ├── pages/\
│   ├── components/\
│   ├── graphs/\
│   ├── maps/\
│   └── api/

├── backend/\
│   └── app/\
│       ├── api/\
│       ├── ingestion/\
│       ├── verification/\
│       ├── intelligence/\
│       ├── correlation/\
│       ├── decision/\
│       ├── storage/\
│       └── reporting/

├── ml/\
│   ├── datasets/\
│   ├── training/\
│   ├── models/\
│   └── evaluation/

├── docker-compose.yml

└── README.md

---

# 22. IMPLEMENTATION MODULES

### ingestion/

eml\_parser.py\
mime\_parser.py\
evidence.py

### verification/

header\_analyzer.py\
spf.py\
dkim.py\
dmarc.py\
identity.py

### intelligence/

nlp.py\
xgboost.py\
url\_intel.py\
domain\_intel.py\
ip\_intel.py\
threat\_intel.py

### correlation/

graph.py\
campaign.py\
infrastructure.py

### decision/

risk\_engine.py\
confidence.py\
explainability.py

### storage/

postgres.py\
neo4j.py\
object\_store.py

### reporting/

forensic\_report.py

---

# 23. SIH DEMO SCENARIO

Upload:

Suspicious CFO payment-request email.

System performs:

1. Preserve original .EML.
2. Calculate SHA-256.
3. Parse MIME.
4. Extract headers.
5. Reconstruct Received chain.
6. Analyze SPF/DKIM/DMARC.
7. Compare From/Reply-To/Return-Path.
8. Detect lookalike domain.
9. Extract URLs.
10. Analyze domain.
11. Analyze IP.
12. Identify hosting/ASN.
13. Run BEC/NLP analysis.
14. Build graph.
15. Search previous cases.
16. Discover related emails.
17. Create campaign relationship.
18. Calculate risk.
19. Calculate confidence.
20. Explain contributing evidence.
21. Reconstruct attack path.
22. Generate forensic report.

---

# 24. THE KEY DIFFERENTIATOR

The final project pitch should NOT be:

> “We use AI to detect phishing emails and show their location on a map.”

That is too common.

Instead:

> “We convert a suspicious email into a structured forensic evidence graph, detect contradictions across sender identity and infrastructure, correlate evidence across multiple incidents to discover campaigns, reconstruct probable attack paths, and show confidence and provenance for every investigative finding.”

---

# 25. FINAL ENGINEERING PRINCIPLE

The technology stack is NOT the innovation.

The innovation is the combination of:

EVIDENCE PROVENANCE\
+\
IDENTITY CONTRADICTION\
+\
INFRASTRUCTURE FINGERPRINTING\
+\
CAMPAIGN DISCOVERY\
+\
EVIDENCE RELIABILITY\
+\
ATTACK-PATH RECONSTRUCTION\
+\
EXPLAINABLE MULTI-EVIDENCE DECISION

The architecture should be judged by how well these engines work together, not by how many technologies are listed.

---

# 26. AGENT TASK

Before proposing the final architecture, the agent MUST:

1. Research SIH26106 requirements.
2. Research existing commercial email-security platforms.
3. Research publicly available projects solving similar problems.
4. Identify features that are already common.
5. Identify actual gaps.
6. Avoid claiming generic features as innovation.
7. Design custom forensic reasoning components around those gaps.
8. Keep the prototype realistically implementable by a student team.
9. Prefer technically meaningful components over unnecessary infrastructure.
10. Clearly distinguish:

- existing technology
- custom engineering
- external intelligence
- AI/ML
- future/optional features.

The final architecture must be **engineering-level**, not just a list of frameworks.
