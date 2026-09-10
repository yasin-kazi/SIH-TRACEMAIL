import { useState, useCallback } from 'react';
import { useCaseStore } from '../store/useCaseStore';
import type { IntelData } from '../types';
import { NodeInspector } from '../components/common/NodeInspector';

const typeFilters = [
  { key: 'all', label: 'ALL', count: 14, color: '' },
  { key: 'email', label: 'EMAIL', count: 3, color: 'bg-primary' },
  { key: 'identity', label: 'IDENTITY', count: 2, color: 'bg-tertiary' },
  { key: 'domain', label: 'DOMAIN', count: 3, color: 'bg-secondary' },
  { key: 'ip', label: 'IP/ASN', count: 4, color: 'bg-error' },
  { key: 'campaign', label: 'CAMPAIGN', count: 1, color: 'bg-primary-fixed' },
];

const typeColors: Record<string, { bg: string; ring: string; text: string }> = {
  email: { bg: 'bg-primary/20', ring: 'bg-surface-container-high', text: 'text-primary' },
  identity: { bg: 'bg-tertiary-container/30', ring: 'bg-surface-container', text: 'text-tertiary' },
  domain: { bg: 'bg-secondary-container/40', ring: 'bg-surface-container', text: 'text-secondary' },
  ip: { bg: 'bg-error/20', ring: 'bg-error-container/40', text: 'text-error' },
  campaign: { bg: 'bg-primary-fixed/20', ring: 'bg-surface-container-high', text: 'text-primary' },
};

const nodePositions: Record<string, { x: number; y: number }> = {
  'EML-1042-A': { x: 50, y: 42 },
  'ID-R-STERLING': { x: 15, y: 22 },
  'DOM-ACME-CO': { x: 82, y: 22 },
  'IP-185-220-101-5': { x: 50, y: 68 },
  'URL-WIRE-VERIF': { x: 15, y: 78 },
  'CAMP-17': { x: 82, y: 78 },
  'EML-0988-B': { x: 10, y: 48 },
  'EML-1011-C': { x: 88, y: 55 },
  'DOM-ACME-GENUINE': { x: 50, y: 8 },
  'IP-MX-RELAY': { x: 88, y: 40 },
};

export function GraphPage() {
  const activeCase = useCaseStore(s => s.activeCase);
  const showToast = useCaseStore(s => s.showToast);
  const [activeFilter, setActiveFilter] = useState('all');
  const [selectedNode, setSelectedNode] = useState<string | null>('IP-185-220-101-5');
  const [searchTerm, setSearchTerm] = useState('');
  const [inspectorOpen, setInspectorOpen] = useState(false);
  const [inspectorData, setInspectorData] = useState({ title: '', value: '', desc: '', severity: '' });

  if (!activeCase) return null;

  const filteredNodes = activeCase.graphNodes.filter(n => {
    if (activeFilter !== 'all' && n.type !== activeFilter) return false;
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      return n.label.toLowerCase().includes(term) || n.sublabel.toLowerCase().includes(term) || n.id.toLowerCase().includes(term);
    }
    return true;
  });

  const selectedIntel: IntelData = activeCase.intelData[selectedNode || ''] || {
    category: 'FORENSIC ENTITY',
    title: selectedNode || '',
    score: '75',
    geo: 'Resolved in Case',
    asn: 'Telemetry Recorded',
    desc: 'Correlated node within active investigation topology.',
    icon: 'hub',
    colorClass: 'text-primary',
  };

  const handleNodeClick = useCallback((nodeId: string) => {
    setSelectedNode(nodeId);
  }, []);

  return (
    <div className="flex flex-col">
      {/* Graph Header */}
      <div className="px-[0.75rem] py-2 bg-surface-container-low shadow-sm">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <span className="material-symbols-outlined text-primary text-[20px]">hub</span>
            <div className="flex flex-col min-w-0">
              <div className="flex items-center gap-1.5">
                <span className="font-headline-sm text-on-surface truncate">Correlation Topology</span>
                <span className="px-1.5 py-0.5 rounded bg-surface-container-highest text-primary font-code-sm">{activeCase.graphNodes.length} NODES</span>
              </div>
              <span className="font-label-caps text-on-surface-variant tracking-wider">Multi-Vector Threat Nexus</span>
            </div>
          </div>
        </div>

        {/* Search */}
        <div className="relative w-full mt-2">
          <span className="material-symbols-outlined absolute left-2.5 top-2 text-on-surface-variant text-[18px]">search</span>
          <input
            className="w-full h-9 pl-9 pr-8 bg-surface-container rounded font-code-sm text-on-surface placeholder:text-outline focus:outline-none focus:bg-surface-container-high"
            placeholder="Filter entities (e.g. 185.220, Sterling, acme)..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          {searchTerm && (
            <button className="absolute right-2 top-2 text-outline hover:text-on-surface" onClick={() => setSearchTerm('')}>
              <span className="material-symbols-outlined text-[18px]">cancel</span>
            </button>
          )}
        </div>

        {/* Filter Chips */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 mt-2 no-scrollbar">
          {typeFilters.map((f) => {
            const isActive = activeFilter === f.key;
            return (
              <button
                key={f.key}
                onClick={() => setActiveFilter(f.key)}
                className={`shrink-0 px-2.5 py-1 rounded font-code-sm flex items-center gap-1 transition-transform active:scale-95 ${
                  isActive ? 'bg-primary text-on-primary shadow-sm' : 'bg-surface-container text-on-surface-variant'
                }`}
              >
                {f.color && <span className={`w-2 h-2 rounded-full ${f.color}`} />}
                <span>{f.label}</span>
                <span className={`text-[9px] ${isActive ? 'text-on-primary/70' : 'text-outline'}`}>{f.count}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Graph Canvas */}
      <div className="relative w-full overflow-hidden select-none bg-surface-container-lowest" style={{ height: '420px' }}>
        <div className="absolute inset-0 opacity-25" style={{ backgroundImage: 'radial-gradient(circle, #4cd7f6 1px, transparent 1px)', backgroundSize: '24px 24px' }} />

        {/* Status Indicators */}
        <div className="absolute top-2 left-2 z-10 flex flex-col gap-1 pointer-events-none">
          <div className="px-2 py-0.5 rounded bg-surface-container-low/90 backdrop-blur-md flex items-center gap-1.5 shadow-sm">
            <span className="w-1.5 h-1.5 rounded-full bg-tertiary animate-ping" />
            <span className="font-code-sm text-[10px] text-tertiary">SYNCED WITH LIVE SINKHOLE</span>
          </div>
          <div className="px-2 py-0.5 rounded bg-surface-container-low/90 backdrop-blur-md flex items-center gap-1 text-on-surface-variant font-label-caps text-[9px]">
            <span>CLUSTER:</span>
            <span className="text-primary font-bold">APEX-WIRE-FIN9</span>
          </div>
        </div>

        {/* Nodes */}
        <div className="absolute inset-0">
          {filteredNodes.map((node) => {
            const pos = nodePositions[node.id];
            if (!pos) return null;
            const tc = typeColors[node.type] || typeColors.email;
            const isSelected = selectedNode === node.id;
            const isIP = node.type === 'ip' && node.sublabel.includes('BULLETPROOF');

            return (
              <button
                key={node.id}
                onClick={() => handleNodeClick(node.id)}
                className={`absolute transform -translate-x-1/2 -translate-y-1/2 group transition-all ${isSelected ? 'scale-110 z-20' : 'z-10 hover:scale-105'}`}
                style={{ left: `${pos.x}%`, top: `${pos.y}%` }}
              >
                <div className="relative flex flex-col items-center">
                  {isIP && <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-error animate-ping" />}
                  <div className={`rounded-full flex items-center justify-center shadow-lg ${tc.ring} ${isSelected ? 'ring-2 ring-primary' : ''}`}
                    style={{ width: isSelected ? 44 : 36, height: isSelected ? 44 : 36 }}>
                    <div className={`rounded-full flex items-center justify-center ${tc.bg}`} style={{ width: isSelected ? 32 : 28, height: isSelected ? 32 : 28 }}>
                      <span className={`material-symbols-outlined ${tc.text}`} style={{ fontSize: isSelected ? 20 : 16 }}>
                        {node.type === 'email' ? 'mail' : node.type === 'identity' ? 'fingerprint' : node.type === 'domain' ? 'language' : node.type === 'ip' ? 'dns' : 'crisis_alert'}
                      </span>
                    </div>
                  </div>
                  <div className="mt-1 px-2 py-0.5 rounded bg-surface-container-lowest/90 backdrop-blur-md flex flex-col items-center max-w-[120px] shadow-sm">
                    <span className={`font-code-sm text-[9px] font-medium truncate ${tc.text}`}>{node.label}</span>
                    {node.sublabel && <span className="font-body-xs text-[8px] text-on-surface-variant truncate">{node.sublabel}</span>}
                  </div>
                </div>
              </button>
            );
          })}
        </div>

        {/* Legend */}
        <div className="absolute bottom-2 left-2 z-10 flex items-center gap-1.5 px-2 py-1 rounded bg-surface-container-lowest/90 backdrop-blur-md shadow-md text-[9px] font-label-caps text-on-surface-variant">
          <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-error" /> HOSTILE</span>
          <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-primary" /> CORE</span>
          <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-tertiary" /> VERIFIED</span>
        </div>
      </div>

      {/* Entity Intel Panel */}
      {selectedNode && (
        <div className="p-[0.75rem] flex flex-col gap-2 bg-surface-container-low shadow-lg">
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-center gap-2 min-w-0">
              <div className={`w-10 h-10 rounded flex items-center justify-center shrink-0 ${selectedIntel.colorClass === 'text-error' ? 'bg-error-container/30' : 'bg-surface-container-highest'}`}>
                <span className={`material-symbols-outlined text-[24px] ${selectedIntel.colorClass}`}>{selectedIntel.icon}</span>
              </div>
              <div className="flex flex-col min-w-0">
                <div className="flex items-center gap-1.5">
                  <span className="font-label-caps text-[9px] px-1 rounded bg-surface-container-highest text-outline tracking-wider">{selectedIntel.category}</span>
                  <span className="font-label-caps text-[9px] text-error font-bold flex items-center gap-0.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-error" /> HIGH RISK
                  </span>
                </div>
                <span className="font-code-lg text-on-surface font-semibold truncate">{selectedIntel.title}</span>
              </div>
            </div>
            <div className="flex flex-col items-end shrink-0">
              <span className="font-label-caps text-outline">REPUTATION</span>
              <div className="flex items-baseline gap-0.5">
                <span className="font-headline-md text-error font-bold leading-none">{selectedIntel.score}</span>
                <span className="font-code-sm text-outline">/100</span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-1 p-2 rounded bg-surface-container">
            <div className="flex flex-col">
              <span className="font-label-caps text-[9px] text-outline">GEOLOCATION</span>
              <div className="flex items-center gap-1 mt-0.5">
                <span className="material-symbols-outlined text-on-surface-variant text-[14px]">public</span>
                <span className="font-code-sm text-on-surface truncate">{selectedIntel.geo}</span>
              </div>
            </div>
            <div className="flex flex-col">
              <span className="font-label-caps text-[9px] text-outline">AUTONOMOUS SYSTEM</span>
              <div className="flex items-center gap-1 mt-0.5">
                <span className="material-symbols-outlined text-on-surface-variant text-[14px]">router</span>
                <span className="font-code-sm text-on-surface truncate">{selectedIntel.asn}</span>
              </div>
            </div>
            <div className="flex flex-col col-span-2 pt-1">
              <span className="font-label-caps text-[9px] text-outline">CROSS-CASE CORRELATION</span>
              <p className="font-body-sm text-on-surface-variant mt-0.5 leading-snug">{selectedIntel.desc}</p>
            </div>
          </div>

          <div className="px-2 py-1.5 rounded bg-surface-container flex items-center justify-between gap-1">
            <div className="flex items-center gap-1.5 min-w-0">
              <span className="material-symbols-outlined text-tertiary text-[16px]">verified</span>
              <span className="font-code-sm text-[10px] text-on-surface-variant truncate">SHA256: 7f83b1657ff1fc53...</span>
            </div>
            <button
              onClick={() => showToast('Hash copied')}
              className="px-1.5 py-0.5 rounded bg-surface-container-highest text-primary font-code-sm text-[9px] active:scale-95"
            >
              COPY
            </button>
          </div>

          <div className="grid grid-cols-3 gap-1 pt-1">
            {[
              { icon: 'dns', label: 'INFRA VIEW' },
              { icon: 'gavel', label: 'IOC DETAILS', errorIcon: true },
              { icon: 'schedule', label: 'TIMELINE', tertiaryIcon: true },
            ].map((a) => (
              <button key={a.label} className="flex flex-col items-center justify-center p-2 rounded bg-surface-container hover:bg-surface-container-high text-on-surface active:scale-95 transition-all text-center">
                <span className={`material-symbols-outlined text-[18px] ${a.errorIcon ? 'text-error' : a.tertiaryIcon ? 'text-tertiary' : 'text-primary'}`}>{a.icon}</span>
                <span className="font-label-caps mt-1 tracking-tight">{a.label}</span>
              </button>
            ))}
          </div>

          <button
            onClick={() => {
              setInspectorData({
                title: selectedIntel.title,
                value: selectedIntel.desc,
                desc: `Geolocation: ${selectedIntel.geo}\nASN: ${selectedIntel.asn}\nReputation: ${selectedIntel.score}/100`,
                severity: 'CRITICAL',
              });
              setInspectorOpen(true);
            }}
            className="w-full h-10 rounded bg-primary text-on-primary font-headline-sm flex items-center justify-center gap-1.5 shadow active:scale-95 transition-all"
          >
            <span className="material-symbols-outlined text-[18px]">lock</span>
            <span>SEAL ARTIFACT INTO EVIDENCE VAULT</span>
          </button>
        </div>
      )}

      <NodeInspector
        isOpen={inspectorOpen}
        onClose={() => setInspectorOpen(false)}
        title={inspectorData.title}
        value={inspectorData.value}
        description={inspectorData.desc}
        severity={inspectorData.severity}
      />
    </div>
  );
}
