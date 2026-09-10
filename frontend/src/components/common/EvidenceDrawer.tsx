import type { ChainEvent } from '../../types';
import { useCaseStore } from '../../store/useCaseStore';

interface EvidenceDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  value: string;
  description: string;
  sha256: string;
  chainOfCustody: ChainEvent[];
}

export function EvidenceDrawer({ isOpen, onClose, title, value, description, sha256, chainOfCustody }: EvidenceDrawerProps) {
  const showToast = useCaseStore(s => s.showToast);

  if (!isOpen) return null;

  return (
    <>
      <div className="fixed inset-0 bg-surface-container-lowest/70 backdrop-blur-xs z-40" onClick={onClose} />
      <div className="fixed inset-x-0 bottom-0 z-50 bg-surface-container-low shadow-xl rounded-t-xl max-h-[75vh] flex flex-col animate-slide-up overflow-hidden">
        <div className="w-12 h-1 bg-surface-container-highest rounded-full mx-auto mt-2 shrink-0 cursor-pointer" onClick={onClose} />
        <div className="px-3 pb-2 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-primary text-[20px]">troubleshoot</span>
            <span className="font-headline-sm text-on-surface truncate max-w-[200px]">{title}</span>
          </div>
          <button onClick={onClose} className="min-w-[44px] min-h-[44px] flex items-center justify-center text-on-surface-variant hover:text-on-surface">
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>
        <div className="px-3 overflow-y-auto flex flex-col gap-3 pb-6 no-scrollbar">
          <div className="bg-surface-container p-3 rounded-lg flex flex-col gap-1">
            <span className="font-label-caps text-outline">OBSERVED VALUE</span>
            <span className="font-code-md text-error font-medium break-all">{value}</span>
          </div>
          <div className="bg-surface-container p-3 rounded-lg flex flex-col gap-1">
            <span className="font-label-caps text-outline">FORENSIC TELEMETRY</span>
            <p className="font-body-sm text-on-surface-variant">{description}</p>
          </div>
          <div className="bg-surface-container p-2.5 rounded-lg flex flex-col gap-1">
            <span className="font-label-caps text-outline">SHA-256 INTEGRITY HASH</span>
            <span className="font-code-sm text-on-surface font-mono select-all break-all">{sha256}</span>
            <div className="flex items-center gap-1 text-tertiary mt-0.5">
              <span className="material-symbols-outlined text-[13px]">verified</span>
              <span className="font-code-sm">HMAC Verified by Investigator #810</span>
            </div>
          </div>
          {chainOfCustody.length > 0 && (
            <div className="flex flex-col gap-2">
              <span className="font-label-caps text-outline tracking-wider">CHAIN OF CUSTODY EVENTS</span>
              {chainOfCustody.map((event, i) => (
                <div key={i} className="flex items-start gap-2.5 bg-surface-container p-2 rounded">
                  <span className={`material-symbols-outlined text-[16px] shrink-0 mt-0.5 ${event.colorClass}`}>{event.icon}</span>
                  <div className="flex flex-col min-w-0">
                    <span className="font-body-sm text-on-surface font-semibold">{event.title}</span>
                    <span className="font-code-sm text-on-surface-variant">{event.detail}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
          <div className="grid grid-cols-2 gap-2 pt-2">
            <button onClick={onClose} className="h-11 bg-surface-container-high text-on-surface rounded font-body-sm font-semibold flex items-center justify-center gap-1 active:scale-95 transition-transform">
              <span className="material-symbols-outlined text-[16px]">close</span>
              <span>Dismiss</span>
            </button>
            <button
              onClick={() => { showToast('Domain isolated: acme-corp.co sinkholed'); onClose(); }}
              className="h-11 bg-primary text-on-primary rounded font-body-sm font-semibold flex items-center justify-center gap-1 shadow-md active:scale-95 transition-transform"
            >
              <span className="material-symbols-outlined text-[16px]">security</span>
              <span>Isolate Domain</span>
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
