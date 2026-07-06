import { Outlet } from 'react-router-dom';
import { ErrorBoundary } from '../ErrorBoundary';
import { Header } from './Header';
import { LayoutProvider } from './LayoutContext';
import { Sidebar } from './Sidebar';

function AppLayoutShell() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-950">
      <Sidebar />
      <div className="min-w-0 pl-0 lg:pl-[248px]">
        <Header />
        <main className="mx-auto max-w-6xl px-4 py-6 sm:px-6">
          <ErrorBoundary>
            <Outlet />
          </ErrorBoundary>
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
