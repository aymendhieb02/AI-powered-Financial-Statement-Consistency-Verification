import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { Sidebar } from './Sidebar';

export function AppLayout() {
  return <div className="min-h-screen bg-slate-50 text-slate-950">
    <Sidebar />
    <div className="min-w-0 pl-[264px]">
      <Header />
      <main className="mx-auto max-w-[1600px] px-6 py-6"><Outlet /></main>
    </div>
  </div>;
}
