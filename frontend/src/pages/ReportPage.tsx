import { useState } from 'react';
import { useCaseStore } from '../store/useCaseStore';

export function ReportPage() {
  const activeCase = useCaseStore(s => s.activeCase);
  const showToast = useCaseStore(s => s.showToast);
  const [exporting, setExporting] = useState(false);

  if (!activeCase) return null;

  const handleExport = async () => {
    setExporting(true);
    await new Promise(resolve => setTimeout(resolve, 2000));
    setExporting(false);
    showToast('Forensic report exported as PDF');
  };

  return (
    <div className="flex flex-col gap-3 px-[0.75rem] pt-3 pb-4">
      {/* Report Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-tertiary text-[20px]">description</span>
          <div>
            <span className="font-headline-sm text-on-surface font-semibold">Forensic Report</span>
            <p className="font-label-caps text-on-surface-variant tracking-wider">CASE #{activeCase.id} INVESTIGATION</p>
          </div>
        </div>
        <button
          onClick={handleExport}
          disabled={exporting}
          className="px-3 py-1.5 bg-primary text-on-primary rounded font-code-sm font-semibold flex items-center gap-1.5 active:scale-95 transition-all shadow-md disabled:opacity-50"
        >
          <span className="material-symbols-outlined text-[16px]">{exporting ? 'hourglass_empty' : 'download'}</span>
          {exporting ? 'EXPORTING...' : 'EXPORT PDF'}
        </button>
      </div>

      {/* Report Preview */}
      <div className="bg-surface-container-low rounded-xl p-4 shadow-md flex flex-col gap-4">
        {/* Title Block */}
        <div className="text-center border-b border-outline-variant pb-4">
          <div className="flex items-center justify-center gap-2 mb-2">
            <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center">
              <span className="material-symbols-outlined text-primary">shield</span>
            </div>
            <span className="font-headline-md text-on-surface font-bold">TraceMail</span>
          </div>
          <p className="font-label-caps text-outline tracking-wider">FORENSIC INVESTIGATION REPORT</p>
          <p className="font-headline-sm text-on-surface font-semibold mt-1">Case #{activeCase.id} — Executive Impersonation BEC</p>
          <p className="font-code-sm text-on-surface-variant mt-1">Generated: {new Date().toISOString().slice(0, 19)}Z</p>
        </div>

        {/* Case Summary */}
        <div className="flex flex-col gap-2">
          <span className="font-label-caps text-outline tracking-wider">CASE SUMMARY</span>
          <div className="grid grid-cols-2 gap-2">
            {[
              { label: 'Case ID', value: `#${activeCase.id}` },
              { label: 'Classification', value: activeCase.threatClass },
              { label: 'Risk Score', value: `${activeCase.riskScore}/100` },
              { label: 'Identity Consistency', value: `${activeCase.identityConsistency}/100` },
              { label: 'Model Confidence', value: `${activeCase.modelConfidence}%` },
              { label: 'Evidence Confidence', value: `${activeCase.evidenceConfidence}%` },
            ].map((item) => (
              <div key={item.label} className="bg-surface-container p-2 rounded flex flex-col">
                <span className="font-label-caps text-outline text-[9px]">{item.label}</span>
                <span className="font-code-sm text-on-surface font-semibold mt-0.5">{item.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Email Metadata */}
        <div className="flex flex-col gap-2">
          <span className="font-label-caps text-outline tracking-wider">EMAIL METADATA</span>
          <div className="bg-surface-container p-2.5 rounded flex flex-col gap-1.5">
            {[
              { label: 'Subject', value: activeCase.emailSubject },
              { label: 'From', value: activeCase.from },
              { label: 'To', value: activeCase.to },
              { label: 'Received', value: activeCase.receivedDate },
            ].map((item) => (
              <div key={item.label} className="flex flex-col gap-0.5">
                <span className="font-label-caps text-outline text-[9px]">{item.label}</span>
                <span className="font-code-sm text-on-surface">{item.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Authentication Analysis */}
        <div className="flex flex-col gap-2">
          <span className="font-label-caps text-outline tracking-wider">AUTHENTICATION ANALYSIS</span>
          <div className="grid grid-cols-3 gap-2">
            {activeCase.authentication.map((auth) => {
              const isPass = auth.result === 'PASS';
              return (
                <div key={auth.protocol} className="bg-surface-container p-2 rounded flex flex-col gap-1">
                  <span className="font-label-caps text-outline text-[9px]">{auth.protocol}</span>
                  <span className={`font-code-sm font-bold ${isPass ? 'text-tertiary' : 'text-error'}`}>{auth.result}</span>
                  <span className="font-body-xs text-on-surface-variant">{auth.detail}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Key Findings */}
        <div className="flex flex-col gap-2">
          <span className="font-label-caps text-outline tracking-wider">KEY FINDINGS</span>
          <div className="flex flex-col gap-1.5">
            {activeCase.anomalies.map((a) => (
              <div key={a.id} className="flex items-start gap-2 bg-surface-container p-2 rounded">
                <span className="material-symbols-outlined text-error text-[14px] shrink-0 mt-0.5">warning</span>
                <div className="flex flex-col">
                  <span className="font-body-sm text-on-surface font-semibold">{a.title}</span>
                  <span className="font-code-sm text-on-surface-variant">{a.description}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Attack Path */}
        <div className="flex flex-col gap-2">
          <span className="font-label-caps text-outline tracking-wider">ATTACK PATH RECONSTRUCTION</span>
          <div className="bg-surface-container p-2.5 rounded flex flex-wrap items-center gap-1">
            {activeCase.attackPath.map((step, i) => (
              <span key={i} className="flex items-center gap-1">
                {i > 0 && <span className="material-symbols-outlined text-outline text-[14px]">arrow_forward</span>}
                <span className="font-code-sm text-on-surface bg-surface-container-high px-1.5 py-0.5 rounded">{step.label}</span>
              </span>
            ))}
          </div>
        </div>

        {/* Evidence Hash */}
        <div className="flex flex-col gap-2">
          <span className="font-label-caps text-outline tracking-wider">EVIDENCE INTEGRITY</span>
          <div className="bg-surface-container p-2.5 rounded flex flex-col gap-1">
            <div className="flex items-center justify-between">
              <span className="font-label-caps text-outline text-[9px]">SHA-256 HASH</span>
              <button onClick={() => showToast('Hash copied')} className="font-code-sm text-primary flex items-center gap-0.5">
                <span className="material-symbols-outlined text-[12px]">content_copy</span>
                COPY
              </button>
            </div>
            <span className="font-code-sm text-on-surface font-mono break-all">{activeCase.sha256}</span>
            <div className="flex items-center gap-1 text-tertiary mt-0.5">
              <span className="material-symbols-outlined text-[13px]">verified</span>
              <span className="font-code-sm">Integrity Verified {'\u2022'} Chain of Custody Maintained</span>
            </div>
          </div>
        </div>

        {/* Attribution Limitations */}
        <div className="flex flex-col gap-2">
          <span className="font-label-caps text-outline tracking-wider">ATTRIBUTION LIMITATIONS</span>
          <div className="bg-surface-container-low border border-outline-variant p-2.5 rounded flex flex-col gap-1">
            <div className="flex items-center gap-1.5">
              <span className="material-symbols-outlined text-[#f59e0b] text-[16px]">info</span>
              <span className="font-body-sm text-on-surface font-semibold">Important Caveat</span>
            </div>
            <p className="font-body-sm text-on-surface-variant leading-relaxed">
              This report identifies the observed sending infrastructure and probable attack vectors. The observed sending IP ({activeCase.intelData['IP-185-220-101-5']?.geo || 'Frankfurt, DE'})
              geolocates to the indicated region, but this does not necessarily identify the physical location of the attacker. Infrastructure may be proxied, compromised, or routed through intermediary systems.
            </p>
          </div>
        </div>

        {/* Analyst Conclusion */}
        <div className="flex flex-col gap-2">
          <span className="font-label-caps text-outline tracking-wider">ANALYST CONCLUSION</span>
          <div className="bg-surface-container p-2.5 rounded flex flex-col gap-1">
            <p className="font-body-sm text-on-surface leading-relaxed">
              The analyzed email exhibits strong indicators of a Business Email Compromise (BEC) attack involving executive impersonation. The identity consistency score of {activeCase.identityConsistency}/100 indicates severe contradiction across sender identity fields.
              The attack leverages a lookalike domain (acme-corp.co) with bulletproof hosting infrastructure (AS49453) and a Reply-To hijack to an external adversarial endpoint. The email is part of Campaign #{activeCase.id}, which has been correlated with {activeCase.anomalies.length} anomaly signals
              across the forensic analysis pipeline.
            </p>
          </div>
        </div>

        {/* Chain of Custody */}
        <div className="flex flex-col gap-2">
          <span className="font-label-caps text-outline tracking-wider">CHAIN OF CUSTODY</span>
          <div className="flex flex-col gap-2">
            {activeCase.chainOfCustody.map((event, i) => (
              <div key={i} className="flex items-start gap-2.5 bg-surface-container p-2 rounded">
                <span className={`material-symbols-outlined text-[16px] shrink-0 mt-0.5 ${event.colorClass}`}>{event.icon}</span>
                <div className="flex flex-col min-w-0">
                  <span className="font-body-sm text-on-surface font-semibold">{event.title}</span>
                  <span className="font-code-sm text-on-surface-variant">{event.detail}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="text-center pt-3 border-t border-outline-variant">
          <p className="font-label-caps text-outline">CONFIDENTIAL — FOR INVESTIGATION USE ONLY</p>
          <p className="font-code-sm text-on-surface-variant mt-1">TraceMail Forensic Intelligence Platform {'\u2022'} SIH26106</p>
        </div>
      </div>
    </div>
  );
}
