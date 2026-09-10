import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { BottomNav } from './BottomNav';
import { Toast } from '../common/Toast';
import { useCaseStore } from '../../store/useCaseStore';

export function AppShell() {
  const activeCase = useCaseStore(s => s.activeCase);

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Header />
      <main className={`flex-1 ${activeCase ? 'pt-16 pb-16' : 'pt-16'}`}>
        <Outlet />
      </main>
      <BottomNav />
      <Toast />
    </div>
  );
}
