import { useCaseStore } from '../../store/useCaseStore';

export function Toast() {
  const toastMessage = useCaseStore(s => s.toastMessage);

  if (!toastMessage) return null;

  return (
    <div className="fixed top-20 left-1/2 -translate-x-1/2 z-[60] bg-surface-container-highest text-on-surface px-4 py-2 rounded-lg shadow-xl flex items-center gap-2 animate-fade-in">
      <span className="material-symbols-outlined text-[18px] text-primary">info</span>
      <span className="font-code-sm text-code-sm">{toastMessage}</span>
    </div>
  );
}
