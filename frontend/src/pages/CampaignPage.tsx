import { useCaseStore } from '../store/useCaseStore';
import { mockCampaigns } from '../data/mockCases';
import { useState } from 'react';

export function CampaignPage() {
  const activeCase = useCaseStore(s => s.activeCase);
  const showToast = useCaseStore(s => s.showToast);
  const [expandedCampaign, setExpandedCampaign] = useState<string | null>('CAMP-17');

  if (!activeCase) return null;

  const riskColor = (score: number) => {
    if (score >= 80) return 'text-error';
    if (score >= 50) return 'text-[#f59e0b]';
    return 'text-tertiary';
  };

  const threatBadge = (tc: string) => {
    const map: Record<string, string> = {
      BEC: 'bg-error-container text-on-error-container',
      PHISHING: 'bg-[#f59e0b]/20 text-[#f59e0b]',
      FRAUD: 'bg-[#f59e0b]/20 text-[#f59e0b]',
    };
    return map[tc] || 'bg-surface-container-highest text-on-surface-variant';
  };

  return (
    <div className="flex flex-col gap-3 px-[0.75rem] pt-3 pb-4">
      {/* Campaign Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-secondary text-[20px]">crisis_alert</span>
          <div>
            <span className="font-headline-sm text-on-surface font-semibold">Campaign Correlation</span>
            <p className="font-label-caps text-on-surface-variant tracking-wider">CROSS-INCIDENT ANALYSIS</p>
          </div>
        </div>
        <span className="font-code-sm text-secondary">{mockCampaigns.length} Campaigns</span>
      </div>

      {/* Current Case Campaign */}
      <div className="bg-surface-container-low rounded-xl p-3 shadow-md">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-error animate-pulse" />
            <span className="font-label-caps text-error tracking-wider">LINKED TO CASE #{activeCase.id}</span>
          </div>
          <span className={`font-headline-md font-bold ${riskColor(activeCase.riskScore)}`}>{activeCase.riskScore}</span>
        </div>
        <p className="font-body-sm text-on-surface-variant mb-3">
          This email is part of a coordinated attack cluster. Multiple indicators link it to {mockCampaigns.length - 1} other active campaigns.
        </p>

        {/* Related Emails */}
        <div className="flex flex-col gap-1.5">
          <span className="font-label-caps text-outline tracking-wider">RELATED EMAILS IN CLUSTER</span>
          {[
            { id: 'EML-1042-A', subject: 'URGENT: Wire Transfer Authorization', from: 'r.sterling@acme-corp.co', date: '2023-11-04', risk: 91, isCurrent: true },
            { id: 'EML-0988-B', subject: 'Re: Q4 Financial Review — Updated', from: 'cfo-office@acme-corp.co', date: '2023-11-02', risk: 87, isCurrent: false },
            { id: 'EML-1011-C', subject: 'Invoice #INV-2023-4892', from: 'billing@acme-corp.co', date: '2023-11-03', risk: 72, isCurrent: false },
          ].map((e) => (
            <div
              key={e.id}
              className={`p-2 rounded-lg flex items-center gap-2 ${e.isCurrent ? 'bg-surface-container border border-primary/30' : 'bg-surface-container'}`}
            >
              <span className="material-symbols-outlined text-primary text-[16px]">mail</span>
              <div className="flex flex-col min-w-0 flex-1">
                <div className="flex items-center gap-1.5">
                  <span className="font-code-sm text-primary font-bold">{e.id}</span>
                  {e.isCurrent && <span className="font-label-caps text-[8px] bg-primary/20 text-primary px-1 rounded">CURRENT</span>}
                </div>
                <span className="font-body-sm text-on-surface truncate">{e.subject}</span>
                <span className="font-code-sm text-on-surface-variant truncate">{e.from}</span>
              </div>
              <div className="flex flex-col items-end shrink-0">
                <span className={`font-code-sm font-bold ${riskColor(e.risk)}`}>{e.risk}</span>
                <span className="font-code-sm text-on-surface-variant">{e.date}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Active Campaigns */}
      <div className="flex items-center justify-between px-1">
        <span className="font-label-caps text-outline tracking-wider">ACTIVE CAMPAIGNS</span>
        <span className="font-code-sm text-on-surface-variant">{mockCampaigns.length} Detected</span>
      </div>

      {mockCampaigns.map((campaign) => {
        const isExpanded = expandedCampaign === campaign.id;
        const isLinked = campaign.id === activeCase.campaignId;

        return (
          <div
            key={campaign.id}
            className={`bg-surface-container rounded-xl shadow-sm overflow-hidden transition-all ${
              isLinked ? 'ring-1 ring-primary/30' : ''
            }`}
          >
            <button
              onClick={() => setExpandedCampaign(isExpanded ? null : campaign.id)}
              className="w-full p-3 text-left flex flex-col gap-2"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex flex-col min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-code-sm text-primary font-bold">{campaign.id}</span>
                    <span className={`font-label-caps px-1.5 py-0.5 rounded ${threatBadge(campaign.threatClass)}`}>{campaign.threatClass}</span>
                    {isLinked && <span className="font-label-caps text-[8px] bg-primary/20 text-primary px-1 rounded">LINKED</span>}
                  </div>
                  <span className="font-headline-sm text-on-surface font-semibold mt-1">{campaign.name}</span>
                </div>
                <div className="flex flex-col items-end shrink-0">
                  <span className="font-label-caps text-outline">RISK</span>
                  <span className={`font-headline-md font-bold ${riskColor(campaign.riskScore)}`}>{campaign.riskScore}</span>
                </div>
              </div>

              <div className="flex items-center justify-between text-on-surface-variant">
                <span className="font-code-sm flex items-center gap-1">
                  <span className="material-symbols-outlined text-[14px]">mail</span>
                  {campaign.emailCount} emails
                </span>
                <span className="font-code-sm">{campaign.firstSeen.slice(0, 10)}</span>
              </div>

              {isExpanded && (
                <div className="flex flex-col gap-2 pt-2 border-t border-outline-variant">
                  <p className="font-body-sm text-on-surface-variant">{campaign.description}</p>

                  <div className="flex flex-col gap-1">
                    <span className="font-label-caps text-outline text-[9px]">RELATED DOMAINS</span>
                    <div className="flex flex-wrap gap-1">
                      {campaign.relatedDomains.map((d) => (
                        <span key={d} className="font-code-sm text-on-surface bg-surface-container-high px-1.5 py-0.5 rounded">{d}</span>
                      ))}
                    </div>
                  </div>

                  <div className="flex flex-col gap-1">
                    <span className="font-label-caps text-outline text-[9px]">RELATED IPs</span>
                    <div className="flex flex-wrap gap-1">
                      {campaign.relatedIps.map((ip) => (
                        <span key={ip} className="font-code-sm text-error bg-error/10 px-1.5 py-0.5 rounded">{ip}</span>
                      ))}
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-1">
                    <span className="font-code-sm text-on-surface-variant">
                      {campaign.firstSeen.slice(0, 10)} {'\u2192'} {campaign.lastSeen.slice(0, 10)}
                    </span>
                    <button
                      onClick={(e) => { e.stopPropagation(); showToast(`Sealed ${campaign.id} into evidence vault`); }}
                      className="font-code-sm text-primary flex items-center gap-1 active:scale-95"
                    >
                      <span className="material-symbols-outlined text-[14px]">lock</span>
                      SEAL
                    </button>
                  </div>
                </div>
              )}
            </button>
          </div>
        );
      })}

      {/* Correlation Matrix */}
      <div className="flex items-center justify-between px-1 mt-1">
        <span className="font-label-caps text-outline tracking-wider">SHARED INDICATOR MATRIX</span>
      </div>

      <div className="bg-surface-container-low rounded-xl p-3 shadow-sm">
        <table className="w-full text-left font-body-xs">
          <thead>
            <tr className="text-outline font-label-caps bg-surface-container-lowest">
              <th className="py-2 px-2">INDICATOR</th>
              <th className="py-2 px-2 text-center">CAMP-17</th>
              <th className="py-2 px-2 text-center">CAMP-23</th>
              <th className="py-2 px-2 text-center">CAMP-31</th>
            </tr>
          </thead>
          <tbody>
            {[
              { indicator: 'Shared IP', c17: true, c23: false, c31: false },
              { indicator: 'Shared Domain', c17: true, c23: false, c31: false },
              { indicator: 'Similar Language', c17: true, c23: false, c31: true },
              { indicator: 'Same Hosting', c17: true, c23: true, c31: false },
              { indicator: 'Same ASN', c17: true, c23: false, c31: false },
            ].map((row, i) => (
              <tr key={i} className={i % 2 === 0 ? 'bg-surface-container-low' : 'bg-surface-container-lowest'}>
                <td className="py-2 px-2 font-code-sm text-on-surface">{row.indicator}</td>
                <td className="py-2 px-2 text-center">
                  <span className={`material-symbols-outlined text-[16px] ${row.c17 ? 'text-error' : 'text-outline-variant'}`}>
                    {row.c17 ? 'check_circle' : 'cancel'}
                  </span>
                </td>
                <td className="py-2 px-2 text-center">
                  <span className={`material-symbols-outlined text-[16px] ${row.c23 ? 'text-[#f59e0b]' : 'text-outline-variant'}`}>
                    {row.c23 ? 'check_circle' : 'cancel'}
                  </span>
                </td>
                <td className="py-2 px-2 text-center">
                  <span className={`material-symbols-outlined text-[16px] ${row.c31 ? 'text-[#f59e0b]' : 'text-outline-variant'}`}>
                    {row.c31 ? 'check_circle' : 'cancel'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
