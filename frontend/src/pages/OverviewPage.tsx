import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCaseStore } from '../store/useCaseStore';
import { ThreatGauge } from '../components/common/ThreatGauge';
import { EvidenceDrawer } from '../components/common/EvidenceDrawer';

export function OverviewPage() {
  const activeCase = useCaseStore(s => s.activeCase);
  const frozen = useCaseStore(s => s.frozen);
  const toggleFreeze = useCaseStore(s => s.toggleFreeze);
  const showToast = useCaseStore(s => s.showToast);
  const navigate = useNavigate();
  const [drawerOpen, setDrawerOpen] = useState(false);

  if (!activeCase) return null;

  const now = new Date();
  const utcTime = `${now.getUTCHours().toString().padStart(2, '0')}:${now.getUTCMinutes().toString().padStart(2, '0')}:${now.getUTCSeconds().toString().padStart(2, '0')}`;

  return (
    <div className="flex flex-col gap-2 pb-4">
      {/* Live Evidence Feed Banner */}
      <div className="px-[0.75rem] py-1">
        <div className="w-full bg-surface-container-low rounded-xl p-3 flex items-center justify-between shadow-sm">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className={`w-2.5 h-2.5 rounded-full ${frozen ? 'bg-[#f59e0b]' : 'bg-error animate-ping'}`} />
            <div className="flex flex-col min-w-0">
              <div className="flex items-center gap-1.5">
                <span className="font-label-caps text-primary tracking-widest">LIVE EVIDENCE FEED</span>
                <span className="font-code-sm text-on-surface-variant">{'\u2022'} UTC {utcTime}</span>
              </div>
              <span className="font-body-xs text-on-surface truncate">Tactical packet inspection ongoing on MX cluster</span>
            </div>
          </div>
          <button
            onClick={toggleFreeze}
            className={`shrink-0 px-2 py-1 rounded font-code-sm text-code-sm active:scale-95 transition-all ${
              frozen ? 'bg-primary text-on-primary' : 'bg-surface-container-high text-primary'
            }`}
          >
            {frozen ? 'FROZEN' : 'FREEZE'}
          </button>
        </div>
      </div>

      {/* Threat Matrix Card */}
      <div className="px-[0.75rem] py-1">
        <div className="w-full bg-surface-container rounded-xl p-3.5 shadow-md flex flex-col gap-3 relative overflow-hidden">
          <div className="absolute -right-8 -top-8 w-32 h-32 rounded-full bg-primary/5 pointer-events-none flex items-center justify-center">
            <div className="w-20 h-20 rounded-full border border-dashed border-primary/20 animate-spin" style={{ animationDuration: '20s' }} />
          </div>
          <div className="flex items-start justify-between gap-2 z-10">
            <div className="flex flex-col min-w-0">
              <div className="flex items-center gap-1.5 flex-wrap">
                <span className="font-label-caps px-1.5 py-0.5 bg-error-container text-on-error-container rounded font-bold">CRITICAL SEVERITY</span>
                <span className="font-code-sm text-outline tracking-wider">REF #{activeCase.id}-BEC</span>
              </div>
              <h2 className="font-headline-md text-on-surface mt-0.5 truncate">Executive Impersonation</h2>
            </div>
            <div className="flex items-center gap-1 shrink-0 bg-surface-container-highest px-2 py-1 rounded">
              <span className="material-symbols-outlined text-[16px] text-tertiary">lock_reset</span>
              <span className="font-code-sm text-tertiary-fixed font-bold">SHA-OK</span>
            </div>
          </div>
          <div className="grid grid-cols-12 gap-2 items-center bg-surface-container-lowest/70 p-3 rounded-lg z-10">
            <div className="col-span-5 flex flex-col items-center justify-center">
              <ThreatGauge score={activeCase.riskScore} />
            </div>
            <div className="col-span-7 flex flex-col justify-center gap-1.5 pl-1">
              <div className="flex items-center justify-between">
                <span className="font-body-xs text-on-surface-variant">Model Confidence</span>
                <span className="font-code-sm text-primary font-semibold">{activeCase.modelConfidence}%</span>
              </div>
              <div className="w-full bg-surface-container-high h-1.5 rounded-full overflow-hidden">
                <div className="bg-primary h-full rounded-full" style={{ width: `${activeCase.modelConfidence}%` }} />
              </div>
              <div className="flex items-center justify-between mt-1">
                <span className="font-body-xs text-on-surface-variant">Evidence Confidence</span>
                <span className="font-code-sm text-tertiary font-semibold">{activeCase.evidenceConfidence}%</span>
              </div>
              <div className="w-full bg-surface-container-high h-1.5 rounded-full overflow-hidden">
                <div className="bg-tertiary h-full rounded-full" style={{ width: `${activeCase.evidenceConfidence}%` }} />
              </div>
              <div className="flex items-center gap-1 mt-1 text-on-surface-variant">
                <span className="material-symbols-outlined text-[13px] text-error">gavel</span>
                <span className="font-code-sm">Non-Repudiation {activeCase.nonRepudiation}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Metric Summary Matrix */}
      <div className="px-[0.75rem] py-1">
        <div className="grid grid-cols-2 gap-2">
          <div className="bg-surface-container-low p-2.5 rounded-lg flex flex-col justify-between shadow-xs">
            <div className="flex items-center justify-between">
              <span className="font-label-caps text-outline">IDENTITY SYNC</span>
              <span className="material-symbols-outlined text-error text-[16px]">priority_high</span>
            </div>
            <div className="mt-2 flex items-baseline gap-1.5">
              <span className="font-headline-md text-error font-bold">{activeCase.identityConsistency}</span>
              <span className="font-code-sm text-on-surface-variant">/ 100</span>
            </div>
            <span className="font-code-sm text-error/90 truncate mt-0.5">High Contradiction</span>
          </div>
          <div className="bg-surface-container-low p-2.5 rounded-lg flex flex-col justify-between shadow-xs">
            <div className="flex items-center justify-between">
              <span className="font-label-caps text-outline">RELATED EMAILS</span>
              <span className="material-symbols-outlined text-secondary text-[16px]">mark_email_unread</span>
            </div>
            <div className="mt-2 flex items-baseline gap-1.5">
              <span className="font-headline-md text-on-surface font-bold">03</span>
              <span className="font-code-sm text-on-surface-variant">Detected</span>
            </div>
            <span className="font-code-sm text-secondary truncate mt-0.5">Cluster #17 Group</span>
          </div>
          <div className="bg-surface-container-low p-2.5 rounded-lg flex flex-col justify-between shadow-xs">
            <div className="flex items-center justify-between">
              <span className="font-label-caps text-outline">INFRA NODES</span>
              <span className="material-symbols-outlined text-primary text-[16px]">router</span>
            </div>
            <div className="mt-2 flex items-baseline gap-1.5">
              <span className="font-headline-md text-primary font-bold">04</span>
              <span className="font-code-sm text-on-surface-variant">Flagged</span>
            </div>
            <span className="font-code-sm text-primary truncate mt-0.5">2 Datacenter {'\u2022'} 1 Lookalike</span>
          </div>
          <div className="bg-surface-container-low p-2.5 rounded-lg flex flex-col justify-between shadow-xs">
            <div className="flex items-center justify-between">
              <span className="font-label-caps text-outline">VAULT ARCHIVE</span>
              <span className="material-symbols-outlined text-tertiary text-[16px]">verified_user</span>
            </div>
            <div className="mt-2 flex items-baseline gap-1.5">
              <span className="font-code-lg text-on-surface font-semibold truncate">{activeCase.vaultId}</span>
            </div>
            <span className="font-code-sm text-tertiary truncate mt-0.5">Merkle Tree Linked</span>
          </div>
        </div>
      </div>

      {/* Flagged Anomalies */}
      <div className="px-[0.75rem] py-1">
        <div className="bg-surface-container rounded-xl p-3.5 shadow-sm flex flex-col gap-2.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-error text-[18px]">warning</span>
              <h3 className="font-headline-sm text-on-surface font-semibold">Flagged Anomalies</h3>
            </div>
            <span className="font-code-sm px-1.5 py-0.5 rounded bg-surface-container-highest text-primary">{activeCase.anomalies.length} Signals</span>
          </div>
          <div className="flex flex-col gap-1.5">
            {activeCase.anomalies.map((a) => (
              <div key={a.id} className="p-2 rounded bg-surface-container-low flex items-start gap-2.5">
                <span className={`material-symbols-outlined text-[16px] shrink-0 mt-0.5 ${a.severity === 'error' ? 'text-error' : 'text-[#f59e0b]'}`}>{a.icon}</span>
                <div className="flex flex-col min-w-0 flex-1">
                  <div className="flex items-center justify-between">
                    <span className="font-body-sm text-on-surface font-semibold truncate">{a.title}</span>
                    <span className="font-code-sm text-error font-bold">+{a.weight} wt</span>
                  </div>
                  <p className="font-code-sm text-on-surface-variant truncate">{a.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Identity Routing Vector */}
      <div className="px-[0.75rem] py-1">
        <div className="bg-surface-container rounded-xl p-3.5 shadow-sm flex flex-col gap-2.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-[18px]">forward_to_inbox</span>
              <h3 className="font-headline-sm text-on-surface font-semibold">Identity Routing Vector</h3>
            </div>
            <button
              onClick={() => showToast('Copied to Forensic Clipboard')}
              className="font-code-sm text-primary flex items-center gap-0.5 active:scale-95 transition-transform"
            >
              <span className="material-symbols-outlined text-[14px]">content_copy</span>
              <span>COPY</span>
            </button>
          </div>
          <div className="flex flex-col gap-2 bg-surface-container-lowest p-2.5 rounded-lg">
            {Object.entries(activeCase.identityVector).map(([key, v]) => {
              const labels: Record<string, string> = {
                envelopeFrom: 'Envelope From',
                replyTo: 'Tactical Reply-To',
                returnPath: 'Origin Return-Path',
              };
              const statusColors: Record<string, string> = {
                SPOOFED: 'text-error bg-error-container/40',
                REDIRECT: 'text-error bg-error-container/40',
                'MX-DROP': 'text-outline',
              };
              return (
                <div key={key} className="flex flex-col gap-0.5">
                  <span className="font-label-caps text-outline">{labels[key]}</span>
                  <div className="flex items-center justify-between gap-1 bg-surface-container-low px-2 py-1 rounded">
                    <span className="font-code-sm text-on-surface truncate">{v.value}</span>
                    <span className={`font-code-sm px-1 rounded shrink-0 ${statusColors[v.status] || 'text-on-surface-variant'}`}>{v.status}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Attack Path Pipeline */}
      <div className="px-[0.75rem] py-1">
        <div className="bg-surface-container rounded-xl p-3.5 shadow-sm flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-secondary text-[18px]">alt_route</span>
              <h3 className="font-headline-sm text-on-surface font-semibold">Attack Path Pipeline</h3>
            </div>
            <span className="font-code-sm text-outline">{activeCase.attackPath.length} Step Hop</span>
          </div>
          <div className="flex items-center gap-2 overflow-x-auto pb-1 no-scrollbar">
            {activeCase.attackPath.map((step, i) => {
              const severityBg: Record<string, string> = {
                error: 'bg-error-container text-on-error-container',
                primary: 'bg-surface-container-highest text-primary',
                info: 'bg-surface-container-highest text-secondary',
                warning: 'bg-surface-container-highest text-[#f59e0b]',
              };
              const severityLabel: Record<string, string> = {
                error: 'text-error',
                primary: 'text-on-surface-variant',
                info: 'text-secondary',
                warning: 'text-[#f59e0b]',
              };
              return (
                <div key={i} className="flex items-center gap-2">
                  {i > 0 && <span className="material-symbols-outlined text-outline shrink-0 text-[16px]">arrow_forward</span>}
                  <div className="shrink-0 w-28 bg-surface-container-low p-2 rounded-lg flex flex-col gap-1 items-center text-center">
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center ${severityBg[step.severity]}`}>
                      <span className="material-symbols-outlined text-[14px]">{step.icon}</span>
                    </div>
                    <span className="font-code-sm text-on-surface font-semibold leading-tight">{step.label}</span>
                    <span className={`font-label-caps ${severityLabel[step.severity]}`}>{step.status}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Auth Protocol Status */}
      <div className="px-[0.75rem] py-1">
        <div className="bg-surface-container rounded-xl p-3.5 shadow-sm flex flex-col gap-2.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-[18px]">verified</span>
              <h3 className="font-headline-sm text-on-surface font-semibold">Authentication Protocol Status</h3>
            </div>
            <span className="font-label-caps text-tertiary font-bold">RFC-SPEC</span>
          </div>
          <div className="grid grid-cols-3 gap-2">
            {activeCase.authentication.map((auth) => {
              const isPass = auth.result === 'PASS';
              const isNone = auth.result === 'NONE';
              const iconColor = isPass ? 'text-tertiary' : isNone ? 'text-error' : 'text-error';
              const icon = isPass ? 'check_circle' : 'report';
              const textColor = isPass ? 'text-tertiary' : 'text-error';
              return (
                <div key={auth.protocol} className="bg-surface-container-low p-2 rounded flex flex-col gap-1">
                  <div className="flex items-center justify-between">
                    <span className="font-label-caps text-outline">{auth.protocol}</span>
                    <span className={`material-symbols-outlined text-[14px] ${iconColor}`}>{icon}</span>
                  </div>
                  <span className={`font-code-sm ${textColor} font-bold`}>{auth.result}</span>
                  <span className="font-body-xs text-on-surface-variant truncate">{auth.detail}</span>
                </div>
              );
            })}
          </div>
          <p className="font-body-xs text-on-surface-variant bg-surface-container-lowest p-2 rounded">
            Security Note: Attacker exploited relaxed <span className="text-on-surface font-semibold">p=none</span> policy on the target recipient gateway.
          </p>
        </div>
      </div>

      {/* Drilldown Grid */}
      <div className="px-[0.75rem] py-1">
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <span className="font-label-caps text-outline tracking-wider">INVESTIGATIVE DRILLDOWNS</span>
            <span className="font-code-sm text-primary">Case #{activeCase.id}</span>
          </div>
          <div className="grid grid-cols-2 gap-2">
            {[
              { icon: 'badge', label: 'Examine Identity', sub: 'Contradiction map', color: 'text-error', action: () => navigate(`/case/${activeCase.id}/identity`) },
              { icon: 'hub', label: 'View Attack Graph', sub: 'C2 node topology', color: 'text-primary', action: () => navigate(`/case/${activeCase.id}/graph`) },
              { icon: 'crisis_alert', label: 'Campaign Correl.', sub: '3 active matches', color: 'text-secondary', action: () => navigate(`/case/${activeCase.id}/campaign`) },
              { icon: 'description', label: 'Export Audit', sub: 'Defensible PDF', color: 'text-tertiary', action: () => navigate(`/case/${activeCase.id}/report`) },
            ].map((d) => (
              <button
                key={d.label}
                onClick={d.action}
                className="p-3 bg-surface-container hover:bg-surface-container-high rounded-xl flex flex-col justify-between text-left active:scale-[0.98] transition-all shadow-xs min-h-[44px]"
              >
                <div className="flex items-center justify-between w-full">
                  <span className={`material-symbols-outlined text-[20px] ${d.color}`}>{d.icon}</span>
                  <span className="material-symbols-outlined text-on-surface-variant text-[16px]">chevron_right</span>
                </div>
                <div className="mt-2 flex flex-col">
                  <span className="font-body-sm text-on-surface font-semibold">{d.label}</span>
                  <span className="font-code-sm text-on-surface-variant">{d.sub}</span>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Evidence Peek */}
      <div className="px-[0.75rem] pt-1 pb-4">
        <button
          onClick={() => setDrawerOpen(true)}
          className="w-full bg-surface-container-low hover:bg-surface-container p-3 rounded-xl flex items-center justify-between shadow-md cursor-pointer transition-colors active:scale-[0.99]"
        >
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-8 h-8 rounded-lg bg-error-container flex items-center justify-center text-on-error-container shrink-0">
              <span className="material-symbols-outlined text-[18px]">fingerprint</span>
            </div>
            <div className="flex flex-col min-w-0">
              <div className="flex items-center gap-1.5">
                <span className="font-label-caps text-error font-bold tracking-wider">PRIMARY IOC FINDING</span>
                <span className="font-code-sm text-on-surface-variant">F-019</span>
              </div>
              <span className="font-body-sm text-on-surface font-semibold truncate">Reply-To Domain Discrepancy</span>
            </div>
          </div>
          <div className="flex items-center gap-1 shrink-0">
            <span className="font-code-sm px-1.5 py-0.5 bg-error/20 text-error rounded font-bold">94% CONF</span>
            <span className="material-symbols-outlined text-on-surface-variant text-[20px]">expand_less</span>
          </div>
        </button>
      </div>

      <EvidenceDrawer
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        title="FINDING F-019 DETAILS"
        value="r.sterling.wire@fin-gate.net"
        description="Reply-To header points to an external adversarial endpoint. Inbound replies would be hijacked to a credential harvesting portal hosted on the same infrastructure as the sending IP."
        sha256={activeCase.sha256}
        chainOfCustody={activeCase.chainOfCustody}
      />
    </div>
  );
}
