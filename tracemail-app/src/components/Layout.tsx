import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';

export function Layout() {
  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <div className="ml-sidebar-width">
        <main className="p-space-xl">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
