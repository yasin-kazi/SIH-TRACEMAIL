import { useLocation, useNavigate } from 'react-router-dom';
import { useCaseStore } from '../../store/useCaseStore';

const navItems = [
  { path: '/case/:id/overview', label: 'OVERVIEW', icon: 'radar', matchPattern: '/overview' },
  { path: '/case/:id/identity', label: 'IDENTITY', icon: 'fingerprint', matchPattern: '/identity' },
  { path: '/case/:id/graph', label: 'GRAPH', icon: 'hub', matchPattern: '/graph' },
  { path: '/case/:id/campaign', label: 'CAMPAIGN', icon: 'crisis_alert', matchPattern: '/campaign' },
  { path: '/case/:id/report', label: 'REPORT', icon: 'verified', matchPattern: '/report' },
];

export function BottomNav() {
  const location = useLocation();
  const navigate = useNavigate();
  const activeCase = useCaseStore(s => s.activeCase);

  if (!activeCase) return null;

  return (
    <nav className="fixed bottom-0 w-full z-50 bg-surface-container-lowest/90 backdrop-blur-xl shadow-[0_-2px_12px_rgba(0,0,0,0.6)]">
      <div className="h-16 px-2 flex justify-around items-center">
        {navItems.map((item) => {
          const isActive = location.pathname.includes(item.matchPattern);
          return (
            <button
              key={item.matchPattern}
              onClick={() => navigate(item.path.replace(':id', activeCase.id))}
              className={`min-w-[44px] min-h-[44px] flex flex-col items-center justify-center gap-0.5 transition-colors ${
                isActive ? 'text-primary font-semibold' : 'text-on-surface-variant hover:text-on-surface'
              }`}
            >
              <span className="material-symbols-outlined text-[20px]">{item.icon}</span>
              <span className="font-label-caps tracking-wider">{item.label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
