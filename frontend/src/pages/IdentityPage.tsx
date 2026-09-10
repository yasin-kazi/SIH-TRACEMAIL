import { useState } from 'react';
import { useCaseStore } from '../store/useCaseStore';
import { NodeInspector } from '../components/common/NodeInspector';

export function IdentityPage() {
  const activeCase = useCaseStore(s => s.activeCase);
  const showToast = useCaseStore(s => s.showToast);
  const [inspector, setInspector] = useState<{ isOpen: boolean; title: string; value: string; desc: string; severity: string }>({
    isOpen: false, title: '', value: '', desc: '', severity: '',
  });

  if (!activeCase) return null;

  const openInspect = (title: string, value: string, desc: string, severity: string) => {
    setInspector({ isOpen: true, title, value, desc, severity });
  };

  const contradictionColors: Record<string, string> = {
    error: 'bg-error-container text-on-error-container',
    warning: 'bg-surface-container-highest text-on-surface-variant',
  };

  return (
    <div className="flex flex-col gap-3 px-[0.75rem] pt-3 pb-4">
      {/* Identity Consistency Score */}
      <section className="bg-surface-container-low rounded-xl p-3 shadow-md">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-primary text-[20px]">fingerprint</span>
            <span className="font-label-caps text-primary tracking-wider">IDENTITY CONSISTENCY</span>
          </div>
          <span className="px-2 py-0.5 rounded font-label-caps bg-error-container text-on-error-container font-semibold">CRITICAL ANOMALY</span>
        </div>
        <div className="mt-3 flex items-end justify-between">
          <div className="flex flex-col">
            <div className="flex items-baseline gap-1.5">
              <span className="font-headline-lg text-error font-bold tracking-tight">{activeCase.identityConsistency}</span>
              <span className="font-code-md text-on-surface-variant">/ 100</span>
            </div>
            <span className="font-body-xs text-on-surface-variant">{activeCase.contradictions.length} Severe Contradictions Injected</span>
          </div>
          <div className="flex items-center gap-1.5 text-error px-2 py-1 bg-surface-container rounded-lg">
            <span className="material-symbols-outlined text-[16px] animate-pulse">crisis_alert</span>
            <span className="font-code-sm font-medium">96% CONFIDENCE SPOOF</span>
          </div>
        </div>
        <div className="mt-3 w-full bg-surface-container-highest rounded-full h-1.5 overflow-hidden">
          <div className="bg-error h-full rounded-full transition-all duration-700 ease-out" style={{ width: `${activeCase.identityConsistency}%` }} />
        </div>
      </section>

      {/* Discrepancy Hierarchy Tree */}
      <div className="flex items-center justify-between px-1">
        <span className="font-label-caps text-outline tracking-wider">DISCREPANCY HIERARCHY TREE</span>
        <span className="font-code-sm text-primary flex items-center gap-1">
          <span className="material-symbols-outlined text-[14px]">touch_app</span> TAP NODE TO INSPECT
        </span>
      </div>

      <section className="bg-surface-container-lowest rounded-xl p-3 shadow-md flex flex-col gap-3">
        {/* Claimed Identity */}
        <button
          onClick={() => openInspect('Display Name', 'Robert Sterling (CFO)', 'Target high-privilege executive credential spoofing.', 'CRITICAL')}
          className="w-full bg-surface-container hover:bg-surface-container-high active:scale-95 transition-all text-left p-2.5 rounded-lg"
        >
          <div className="flex items-center justify-between">
            <span className="font-label-caps text-on-surface-variant">CLAIMED IDENTITY</span>
            <span className="font-label-caps text-error bg-surface-container-highest px-1.5 py-0.5 rounded">EXECUTIVE SPOOF</span>
          </div>
          <div className="font-code-lg text-on-surface font-semibold truncate mt-1">Robert Sterling (CFO)</div>
          <div className="font-body-xs text-on-surface-variant flex items-center gap-1 mt-0.5">
            <span className="material-symbols-outlined text-[12px] text-tertiary">verified_user</span> Legitimate: r.sterling@acme-corp.com
          </div>
        </button>
        <span className="material-symbols-outlined text-outline text-[16px] mx-auto">arrow_downward</span>

        {/* RFC 5322 From */}
        <button
          onClick={() => openInspect('Header From', 'r.sterling@acme-corp.co', 'Homoglyph top-level domain divergence (.co instead of .com). Levenshtein Distance = 1.', 'CRITICAL')}
          className="w-full bg-surface-container hover:bg-surface-container-high active:scale-95 transition-all text-left p-2.5 rounded-lg"
        >
          <div className="flex items-center justify-between">
            <span className="font-label-caps text-outline">RFC 5322 FROM</span>
            <span className="font-label-caps text-error bg-surface-container-highest px-1.5 py-0.5 rounded">LOOKALIKE DOMAIN</span>
          </div>
          <div className="font-code-lg text-error font-semibold truncate mt-1">r.sterling@acme-corp.co</div>
          <div className="font-body-xs text-on-surface-variant mt-0.5">TLD .co bypasses display heuristics</div>
        </button>

        <div className="flex items-center justify-around w-full px-8 text-outline my-0.5">
          <span className="material-symbols-outlined text-[16px]">south_west</span>
          <span className="material-symbols-outlined text-[16px]">south_east</span>
        </div>

        {/* Reply-To + DKIM Grid */}
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => openInspect('Reply-To Path', 'r.sterling.wire@fin-gate.net', 'External unauthenticated relay configured to hijack financial correspondence threads.', 'CRITICAL')}
            className="bg-surface-container hover:bg-surface-container-high active:scale-95 transition-all text-left p-2.5 rounded-lg flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between">
                <span className="font-label-caps text-outline">REPLY-TO</span>
                <span className="w-1.5 h-1.5 rounded-full bg-error animate-ping" />
              </div>
              <div className="font-code-sm text-error font-medium truncate mt-1">r.sterling.wire@fin-gate.net</div>
            </div>
            <span className="font-label-caps text-on-surface-variant mt-2 bg-surface-container-lowest p-1 rounded">ROGUE RECEIVER</span>
          </button>
          <button
            onClick={() => openInspect('DKIM Cryptographic Key', 'd=mail-bulkrelay.top', 'DKIM signature signed by third-party disposable campaign operator, failing strict domain alignment.', 'WARNING')}
            className="bg-surface-container hover:bg-surface-container-high active:scale-95 transition-all text-left p-2.5 rounded-lg flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between">
                <span className="font-label-caps text-outline">DKIM ALIGN</span>
                <span className="material-symbols-outlined text-[14px] text-error">gpp_bad</span>
              </div>
              <div className="font-code-sm text-on-surface font-medium truncate mt-1">d=mail-bulkrelay.top</div>
            </div>
            <span className="font-label-caps text-on-surface-variant mt-2 bg-surface-container-lowest p-1 rounded">MISALIGNED SIGNATURE</span>
          </button>
        </div>

        {/* DMARC Policy */}
        <div className="flex flex-col items-center">
          <div className="flex items-center justify-around w-full px-8 text-outline my-0.5">
            <span className="material-symbols-outlined text-[16px]">south_east</span>
            <span className="material-symbols-outlined text-[16px]">south_west</span>
          </div>
          <button
            onClick={() => openInspect('DMARC Enforcement Policy', 'p=none', 'Target organization uses relaxed non-quarantine policy allowing lookalike relay passing.', 'WARNING')}
            className="w-full bg-surface-container hover:bg-surface-container-high active:scale-95 transition-all text-left p-2 rounded-lg flex items-center justify-between"
          >
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-[18px]">policy</span>
              <div className="flex flex-col">
                <span className="font-label-caps text-outline">DMARC POLICY STATE</span>
                <span className="font-code-sm text-on-surface font-semibold">p=none (Softfail Allowed)</span>
              </div>
            </div>
            <span className="font-label-caps text-on-surface-variant px-1.5 py-0.5 rounded bg-surface-container-highest">BYPASS ACTIVE</span>
          </button>
          <span className="material-symbols-outlined text-outline text-[16px] my-0.5">arrow_downward</span>
        </div>

        {/* Return-Path */}
        <button
          onClick={() => openInspect('Return-Path Envelope', 'bounce@mal-infra-relay.ru', 'Envelope sender routes NDN and bounce receipts to known bulletproof mail host.', 'CRITICAL')}
          className="w-full bg-surface-container hover:bg-surface-container-high active:scale-95 transition-all text-left p-2.5 rounded-lg"
        >
          <div className="flex items-center justify-between">
            <span className="font-label-caps text-outline">ENVELOPE RETURN-PATH</span>
            <span className="font-label-caps text-error bg-surface-container-highest px-1.5 py-0.5 rounded">OFFSHORE RELAY</span>
          </div>
          <div className="font-code-md text-error font-semibold truncate mt-1">bounce@mal-infra-relay.ru</div>
        </button>
        <span className="material-symbols-outlined text-outline text-[16px] mx-auto">arrow_downward</span>

        {/* Sending IP */}
        <button
          onClick={() => openInspect('Sending Relay Infrastructure', '185.220.101.5 (AS49453)', 'Associated with CyberBunker bulletproof operations. Flagged in 4 past financial fraud campaigns.', 'CRITICAL')}
          className="w-full bg-surface-container hover:bg-surface-container-high active:scale-95 transition-all text-left p-2.5 rounded-lg flex items-center justify-between"
        >
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded bg-surface-container-highest flex items-center justify-center text-primary">
              <span className="material-symbols-outlined text-[18px]">dns</span>
            </div>
            <div className="flex flex-col">
              <span className="font-label-caps text-outline">PHYSICAL SENDING IP</span>
              <span className="font-code-sm text-on-surface font-semibold">185.220.101.5</span>
              <span className="font-body-xs text-on-surface-variant">AS49453 / CyberBunker Hosting</span>
            </div>
          </div>
          <span className="material-symbols-outlined text-[18px] text-outline">chevron_right</span>
        </button>
      </section>

      {/* Contradiction Alert Stack */}
      <div className="flex items-center justify-between px-1 mt-1">
        <span className="font-label-caps text-outline tracking-wider">CONTRADICTION ALERT STACK</span>
        <span className="font-code-sm text-error font-bold">{activeCase.contradictions.length} FLAGGED</span>
      </div>

      <section className="flex flex-col gap-2">
        {activeCase.contradictions.map((c) => (
          <div key={c.id} className="bg-surface-container-low p-3 rounded-xl shadow-sm flex flex-col gap-2">
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="font-code-sm px-1.5 py-0.5 bg-surface-container-highest text-primary font-bold rounded">{c.id}</span>
                <span className="font-headline-sm text-on-surface">{c.title}</span>
              </div>
              <span className={`font-label-caps px-1.5 py-0.5 rounded font-bold ${contradictionColors[c.severityColor]}`}>{c.severity}</span>
            </div>
            <p className="font-body-sm text-on-surface-variant">{c.description}</p>
            <div className="flex items-center justify-between pt-1">
              <span className="font-code-sm text-outline">
                {c.confidence ? `Conf: ${c.confidence}%` : c.detail?.split(' ').slice(0, 4).join(' ')}
              </span>
              <button
                onClick={() => openInspect(`Alert ${c.id} Evidence`, c.observedValue || c.title, c.detail || c.description, c.severity)}
                className="font-code-sm text-primary flex items-center gap-1 hover:underline"
              >
                <span>Inspect Evidence</span>
                <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
              </button>
            </div>
          </div>
        ))}
      </section>

      {/* Evidence & Source Breakdown */}
      <div className="flex items-center justify-between px-1 mt-1">
        <span className="font-label-caps text-outline tracking-wider">EVIDENCE & SOURCE BREAKDOWN</span>
        <span className="font-code-sm text-tertiary flex items-center gap-1">
          <span className="material-symbols-outlined text-[14px]">verified</span> SHA-256 LOCKED
        </span>
      </div>

      <section className="bg-surface-container-low rounded-xl p-2 shadow-md overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left font-body-xs">
            <thead>
              <tr className="text-outline font-label-caps bg-surface-container-lowest">
                <th className="py-2 px-2.5">FIELD</th>
                <th className="py-2 px-2">OBSERVED</th>
                <th className="py-2 px-2">EXPECTED</th>
                <th className="py-2 px-2 text-center">STATUS</th>
                <th className="py-2 px-2.5 text-right">REF</th>
              </tr>
            </thead>
            <tbody>
              {activeCase.evidenceTable.map((row, i) => (
                <tr key={i} className={i % 2 === 0 ? 'bg-surface-container-low' : 'bg-surface-container-lowest'}>
                  <td className="py-2 px-2.5 font-code-sm text-on-surface font-medium">{row.field}</td>
                  <td className="py-2 px-2 font-code-sm text-error truncate max-w-[110px]">{row.observed}</td>
                  <td className="py-2 px-2 font-code-sm text-on-surface-variant">{row.expected}</td>
                  <td className="py-2 px-2 text-center">
                    <span className="font-label-caps bg-error-container text-on-error-container px-1 py-0.5 rounded font-bold">{row.status}</span>
                  </td>
                  <td className="py-2 px-2.5 text-right font-code-sm text-primary">{row.ref}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="mt-2 pt-2 bg-surface-container p-2 rounded flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <span className="material-symbols-outlined text-[14px] text-tertiary">lock</span>
            <span className="font-code-sm text-on-surface-variant">IMMUTABLE LOG HASH:</span>
          </div>
          <button
            onClick={() => showToast('Hash copied to clipboard')}
            className="font-code-sm text-primary hover:underline flex items-center gap-1"
          >
            <span>e7f2...82c9</span>
            <span className="material-symbols-outlined text-[14px]">content_copy</span>
          </button>
        </div>
      </section>

      {/* Triage Actions */}
      <section className="flex flex-col gap-2 pb-2">
        <span className="font-label-caps text-outline px-1">TRIAGE ACTIONS</span>
        <div className="grid grid-cols-3 gap-1">
          <button className="min-h-[44px] bg-surface-container-low hover:bg-surface-container active:scale-95 transition-all text-on-surface rounded-lg flex flex-col items-center justify-center p-2 text-center gap-1 shadow-sm">
            <span className="material-symbols-outlined text-primary text-[18px]">code</span>
            <span className="font-label-caps leading-tight">HEADER RAW</span>
          </button>
          <button className="min-h-[44px] bg-surface-container-low hover:bg-surface-container active:scale-95 transition-all text-on-surface rounded-lg flex flex-col items-center justify-center p-2 text-center gap-1 shadow-sm">
            <span className="material-symbols-outlined text-primary text-[18px]">hub</span>
            <span className="font-label-caps leading-tight">GRAPH LINK</span>
          </button>
          <button
            onClick={() => showToast('Evidence sealed into vault')}
            className="min-h-[44px] bg-primary text-on-primary font-semibold active:scale-95 transition-all rounded-lg flex flex-col items-center justify-center p-2 text-center gap-1 shadow-md"
          >
            <span className="material-symbols-outlined text-[18px]">inventory_2</span>
            <span className="font-label-caps leading-tight">VAULT SEAL</span>
          </button>
        </div>
      </section>

      <NodeInspector
        isOpen={inspector.isOpen}
        onClose={() => setInspector({ ...inspector, isOpen: false })}
        title={inspector.title}
        value={inspector.value}
        description={inspector.desc}
        severity={inspector.severity}
      />
    </div>
  );
}
