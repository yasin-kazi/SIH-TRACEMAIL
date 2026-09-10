import { useNavigate, useLocation, useParams } from 'react-router-dom';

const navItems = [
  { path: 'overview', icon: 'grid_view', label: 'Overview', badge: null },
  { path: 'identity', icon: 'fingerprint', label: 'Identity', badge: null },
  { path: 'evidence', icon: 'biotech', label: 'Evidence', badge: null },
  { path: 'infrastructure', icon: 'dns', label: 'Infrastructure', badge: null },
  { path: 'graph', icon: 'account_tree', label: 'Graph', badge: null },
  { path: 'campaign', icon: 'workspaces', label: 'Campaign', badge: null },
  { path: 'timeline', icon: 'timeline', label: 'Timeline', badge: null },
  { path: 'copilot', icon: 'smart_toy', label: 'AI Copilot', badge: null },
  { path: 'report', icon: 'description', label: 'Report', badge: null },
];

export function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  const { caseId } = useParams();
  const currentPath = location.pathname.split('/').pop() || 'overview';

  return (
    <aside className="fixed left-0 top-0 h-full w-sidebar-width bg-surface-container-lowest shadow-[0_1px_8px_rgba(0,0,0,0.04)] z-50 flex flex-col justify-between pt-space-md pb-space-lg">
      <div className="flex flex-col">
        <div className="h-header-height px-space-md flex items-center justify-between">
          <div className="flex items-center gap-space-xs">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <span className="material-symbols-outlined text-[20px] text-on-primary">mail</span>
            </div>
            <span className="font-title-sm text-title-sm text-on-surface tracking-tight">TraceMail AI</span>
          </div>
          <span className="font-badge-label text-badge-label px-space-xs py-space-2xs rounded-full bg-surface-container-low text-primary">v2.4</span>
        </div>
        <nav className="flex flex-col gap-space-2xs px-space-xs mt-space-xs">
          {navItems.map((item) => {
            const isActive = currentPath === item.path;
            return (
              <button
                key={item.path}
                onClick={() => navigate(`/case/${caseId}/${item.path}`)}
                className={`flex items-center justify-between px-space-sm py-space-xs rounded-xl transition-colors ${
                  isActive
                    ? 'bg-primary-container text-on-primary font-title-sm'
                    : 'text-on-surface-variant hover:bg-surface-container-low hover:text-on-surface'
                }`}
              >
                <div className="flex items-center gap-space-sm">
                  <span className="material-symbols-outlined text-[20px]">{item.icon}</span>
                  <span className="font-body-md text-body-md">{item.label}</span>
                </div>
                {item.badge && (
                  <span className={`font-label-mono-sm text-label-mono-sm px-space-xs py-space-2xs rounded-full ${
                    isActive ? 'bg-on-primary/20 text-on-primary' : 'bg-surface-container-high text-on-surface-variant'
                  }`}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>
      <div className="px-space-md">
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-space-sm w-full px-space-sm py-space-xs rounded-xl text-on-surface-variant hover:bg-surface-container-low hover:text-on-surface transition-colors"
        >
          <span className="material-symbols-outlined text-[20px]">add_circle</span>
          <span className="font-body-md text-body-md">New Investigation</span>
        </button>
      </div>
    </aside>
  );
}
