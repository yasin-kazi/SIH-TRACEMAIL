import { useCaseStore } from '../../store/useCaseStore';
import { useLocation, useNavigate } from 'react-router-dom';

export function Header() {
  const activeCase = useCaseStore(s => s.activeCase);
  const navigate = useNavigate();
  const location = useLocation();
  const isLanding = location.pathname === '/';

  return (
    <header className="fixed top-0 w-full z-50 bg-surface-container-lowest/80 backdrop-blur-xl shadow-[0_1px_8px_rgba(0,0,0,0.4)]">
      <div className="h-16 px-[0.75rem] flex items-center justify-between gap-1">
        <div className="flex items-center gap-1 shrink-0">
          {!isLanding && (
            <button
              onClick={() => navigate('/')}
              className="min-w-[44px] min-h-[44px] flex items-center justify-center text-primary active:scale-95 transition-transform"
            >
              <span className="material-symbols-outlined text-[24px]">arrow_back</span>
            </button>
          )}
          <div
            className="flex items-center gap-1 cursor-pointer"
            onClick={() => navigate('/')}
          >
            <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center">
              <span className="material-symbols-outlined text-[20px] text-primary">shield</span>
            </div>
            <span className="font-label-caps tracking-widest text-primary hidden min-[360px]:inline-block">TRACEMAIL</span>
          </div>
        </div>

        {activeCase && (
          <div className="flex items-center justify-center px-2 overflow-hidden">
            <div className="flex items-center gap-1.5 px-2 py-1 bg-surface-container-low rounded-lg shadow-inner max-w-[160px] truncate">
              <span className="w-1.5 h-1.5 rounded-full bg-error animate-pulse shrink-0" />
              <span className="font-code-sm text-code-sm text-on-surface font-semibold truncate">#{activeCase.id}</span>
              <span className="font-label-caps text-error truncate">{activeCase.threatClass} HIGH</span>
            </div>
          </div>
        )}

        <div className="flex items-center gap-0.5 shrink-0">
          <button className="min-w-[44px] min-h-[44px] flex items-center justify-center text-on-surface-variant hover:text-primary transition-colors">
            <span className="material-symbols-outlined text-[20px]">travel_explore</span>
          </button>
          <button className="min-w-[44px] min-h-[44px] flex items-center justify-center text-on-surface-variant hover:text-primary transition-colors">
            <span className="material-symbols-outlined text-[20px]">notifications</span>
          </button>
        </div>
      </div>
    </header>
  );
}
