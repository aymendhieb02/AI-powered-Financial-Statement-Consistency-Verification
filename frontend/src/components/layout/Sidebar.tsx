import { NavLink } from 'react-router-dom';
import { AlertTriangle, Download, Layers3, Settings, UploadCloud, ClipboardList } from 'lucide-react';
import { Sheet, SheetContent } from '../ui/sheet';
import { useLayout } from './LayoutContext';

const items = [
  { to: '/compare', label: 'Compare Documents', icon: UploadCloud },
  { to: '/results/' + (localStorage.getItem('finverify_run_id') || 'latest'), label: 'Results', icon: ClipboardList },
  { to: '/anomalies/' + (localStorage.getItem('finverify_run_id') || 'latest'), label: 'Anomalies', icon: AlertTriangle },
  { to: '/reports/' + (localStorage.getItem('finverify_run_id') || 'latest'), label: 'Reports', icon: Download },
  { to: '/advanced', label: 'Advanced', icon: Settings },
];

function NavItems({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <>
      {items.map((item) => {
        const Icon = item.icon;
        return (
          <NavLink
            key={item.label}
            to={item.to}
            onClick={onNavigate}
            className={({ isActive }) =>
              'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition ' +
              (isActive ? 'bg-slate-950 text-white shadow-sm' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-950')
            }
          >
            <Icon size={16} />
            <span>{item.label}</span>
          </NavLink>
        );
      })}
    </>
  );
}

function SidebarPanel({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-slate-200 px-5 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-950 text-white"><Layers3 size={18} /></div>
          <div><div className="text-sm font-semibold text-slate-950">FinVerify</div><div className="text-xs text-slate-500">Compare two annual PDFs</div></div>
        </div>
      </div>
      <nav className="flex-1 space-y-1 px-3 py-4" aria-label="Primary navigation"><NavItems onNavigate={onNavigate} /></nav>
      <div className="border-t border-slate-200 p-4 text-xs text-slate-500">Simple workflow: upload, compare, review, download.</div>
    </div>
  );
}

export function Sidebar() {
  const { mobileNavOpen, setMobileNavOpen } = useLayout();
  return (
    <>
      <aside data-sidebar-nav className="fixed inset-y-0 left-0 z-50 hidden w-[248px] flex-col border-r border-slate-200 bg-white lg:flex"><SidebarPanel /></aside>
      <Sheet open={mobileNavOpen} onOpenChange={setMobileNavOpen}>
        <SheetContent className="w-[280px] p-0 lg:hidden"><SidebarPanel onNavigate={() => setMobileNavOpen(false)} /></SheetContent>
      </Sheet>
    </>
  );
}
