# TraceMail - Implementation Plan

## Architecture

Single-page React application with client-side routing. No backend required for hackathon prototype. All forensic data is realistically mocked in a clean abstraction layer that mirrors the production data flow.

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Framework | React 18 + TypeScript |
| Build Tool | Vite |
| Routing | React Router v6 |
| Styling | Tailwind CSS (custom design system) |
| State | Zustand (lightweight) |
| Graph Viz | @xyflow/react (React Flow) |
| Icons | Material Symbols (Google Fonts) |
| Fonts | Geist + JetBrains Mono (Google Fonts) |

## Folder Structure

```
C:\SIH\frontend\
├── index.html
├── package.json
├── vite.config.ts
├── tailwind.config.js
├── postcss.config.js
├── tsconfig.json
├── public/
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── index.css (Tailwind + design system tokens)
│   ├── components/
│   │   ├── layout/
│   │   │   ├── AppShell.tsx (header + bottom nav + content)
│   │   │   ├── Header.tsx
│   │   │   └── BottomNav.tsx
│   │   ├── common/
│   │   │   ├── ThreatGauge.tsx (radial SVG gauge)
│   │   │   ├── Toast.tsx
│   │   │   ├── EvidenceDrawer.tsx
│   │   │   ├── NodeInspector.tsx
│   │   │   ├── Badge.tsx
│   │   │   └── Card.tsx
│   │   ├── overview/
│   │   │   ├── LiveFeedBanner.tsx
│   │   │   ├── ThreatMatrixCard.tsx
│   │   │   ├── MetricGrid.tsx
│   │   │   ├── FlaggedAnomalies.tsx
│   │   │   ├── IdentityRoutingVector.tsx
│   │   │   ├── AttackPathPipeline.tsx
│   │   │   ├── AuthProtocolStatus.tsx
│   │   │   └── DrilldownGrid.tsx
│   │   ├── identity/
│   │   │   ├── IdentityConsistencyCard.tsx
│   │   │   ├── DiscrepancyTree.tsx
│   │   │   ├── ContradictionAlertStack.tsx
│   │   │   └── EvidenceBreakdownTable.tsx
│   │   ├── graph/
│   │   │   ├── InvestigationGraph.tsx (React Flow)
│   │   │   ├── GraphControls.tsx
│   │   │   ├── FilterChips.tsx
│   │   │   └── EntityIntelPanel.tsx
│   │   ├── campaign/
│   │   │   ├── CampaignList.tsx
│   │   │   ├── CampaignDetail.tsx
│   │   │   └── CampaignTimeline.tsx
│   │   ├── report/
│   │   │   ├── ReportGenerator.tsx
│   │   │   └── ReportPreview.tsx
│   │   └── upload/
│   │       └── UploadWizard.tsx
│   ├── pages/
│   │   ├── LandingPage.tsx (case list + upload trigger)
│   │   ├── AnalysisProgress.tsx
│   │   ├── OverviewPage.tsx
│   │   ├── IdentityPage.tsx
│   │   ├── GraphPage.tsx
│   │   ├── CampaignPage.tsx
│   │   └── ReportPage.tsx
│   ├── data/
│   │   ├── mockCase1042.ts (complete case data)
│   │   ├── mockCampaigns.ts
│   │   └── mockCases.ts
│   ├── store/
│   │   └── useCaseStore.ts (Zustand)
│   ├── lib/
│   │   ├── mockAnalysis.ts (simulates forensic pipeline)
│   │   └── hashUtils.ts (SHA-256 demo)
│   └── types/
│       └── index.ts
```

## Pages/Screens

1. **Landing Page** - Case list, upload new email
2. **Analysis Progress** - Simulated forensic pipeline animation
3. **Investigation Overview** - Threat matrix, anomalies, auth status, attack path
4. **Identity Contradiction Engine** - Discrepancy tree, alerts, evidence table
5. **Investigation Graph** - Interactive node-link topology
6. **Campaign Correlation** - Related emails, campaign details
7. **Report** - Forensic report preview and export

## Data Models

```typescript
interface Case {
  id: string;
  emailSubject: string;
  receivedDate: string;
  threatClass: string;
  riskScore: number;
  identityConsistency: number;
  modelConfidence: number;
  evidenceConfidence: number;
  authentication: { spf: string; dkim: string; dmarc: string; };
  anomalies: Anomaly[];
  identityVector: IdentityVector;
  attackPath: AttackStep[];
  graphNodes: GraphNode[];
  graphEdges: GraphEdge[];
  contradictions: Contradiction[];
  evidenceTable: EvidenceRow[];
  campaignId: string;
  sha256: string;
}

interface Anomaly { id: string; title: string; weight: number; description: string; icon: string; }
interface Contradiction { id: string; title: string; severity: string; description: string; confidence: number; }
interface AttackStep { label: string; status: string; icon: string; }
interface GraphNode { id: string; type: string; label: string; sublabel: string; x: number; y: number; }
interface GraphEdge { id: string; source: string; target: string; label: string; style: string; }
```

## User Flow

1. User lands on case list -> sees Case #1042 (and optionally upload new)
2. User clicks Case #1042 -> brief analysis animation -> lands on Overview
3. Overview shows threat matrix, anomalies, auth, attack path
4. User navigates via bottom nav to Identity, Graph, Campaign, Report
5. Every screen has interactive elements (drawers, inspectors, actions)
6. Report page shows exportable forensic report

## Mock Data Approach

Complete Case #1042 data pre-built matching the Stitch UI references exactly. Mock analysis pipeline simulates the 7-stage forensic flow with a 3-second animation. All other cases are pre-analyzed. No external APIs called.

## Implementation Order

1. Project scaffolding (Vite + React + Tailwind)
2. Design system tokens (CSS)
3. Layout shell (header + nav)
4. Landing page + mock data
5. Overview page (highest value, most complex)
6. Identity page
7. Graph page
8. Campaign page
9. Report page
10. Analysis animation
11. Interactive elements (drawers, inspectors, toasts)
12. Visual polish
