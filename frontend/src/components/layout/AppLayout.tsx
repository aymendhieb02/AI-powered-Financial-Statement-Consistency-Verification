import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { LayoutProvider, useLayout } from './LayoutContext';
import { Sidebar } from './Sidebar';

function AppLayoutShell() {
  const { sidebarCollapsed } = useLayout();
  return (
    <div className="min-h-screen bg-slate-50 text-slate-950">
      <Sidebar />
      <div className={'min-w-0 pl-0 transition-[padding] duration-200 ' + (sidebarCollapsed ? 'lg:pl-[72px]' : 'lg:pl-[264px]')}>
        <Header />
        <main className="mx-auto max-w-[1600px] px-4 py-6 sm:px-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export function AppLayout() {
  return (
    <LayoutProvider>
      <AppLayoutShell />
    </LayoutProvider>
  );
}
