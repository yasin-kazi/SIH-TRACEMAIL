import { useCaseStore } from '../../store/useCaseStore';

interface NodeInspectorProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  value: string;
  description: string;
  severity: string;
}

export function NodeInspector({ isOpen, onClose, title, value, description, severity }: NodeInspectorProps) {
  const showToast = useCaseStore(s => s.showToast);

  if (!isOpen) return null;

  return (
    <>
      <div className="fixed inset-0 bg-surface-container-lowest/70 backdrop-blur-xs z-40 transition-opacity" onClick={onClose} />
      <div className="fixed inset-x-0 bottom-0 z-50 bg-surface-container-low shadow-xl rounded-t-xl max-h-[70vh] flex flex-col animate-slide-up overflow-hidden">
        <div className="w-12 h-1 bg-surface-container-highest rounded-full mx-auto my-2 shrink-0" />
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
          <div className="grid grid-cols-2 gap-2">
            <div className="bg-surface-container p-2.5 rounded-lg flex flex-col">
              <span className="font-label-caps text-outline">CHAIN VERIFICATION</span>
              <span className="font-code-sm text-tertiary mt-0.5 flex items-center gap-1">
                <span className="material-symbols-outlined text-[14px]">check_circle</span> VERIFIED OK
              </span>
            </div>
            <div className="bg-surface-container p-2.5 rounded-lg flex flex-col">
              <span className="font-label-caps text-outline">HASH DIGEST</span>
              <span className="font-code-sm text-on-surface mt-0.5 truncate">sha256:4a09c2...</span>
            </div>
          </div>
          <div className="bg-surface-container p-2.5 rounded-lg flex flex-col gap-1">
            <span className="font-label-caps text-outline">SEVERITY</span>
            <span className={`font-code-sm font-bold ${severity === 'CRITICAL' ? 'text-error' : severity === 'HIGH' ? 'text-[#f59e0b]' : 'text-on-surface'}`}>
              {severity}
            </span>
          </div>
          <button
            onClick={() => { showToast('Node artifact pinned to report session'); onClose(); }}
            className="w-full h-11 bg-primary text-on-primary font-semibold rounded-lg flex items-center justify-center gap-2 mt-2 active:scale-95 transition-all"
          >
            <span className="material-symbols-outlined text-[18px]">bookmark</span>
            <span>Pin to Investigation Report</span>
          </button>
        </div>
      </div>
    </>
  );
}
