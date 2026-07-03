import { NavLink } from 'react-router-dom';
import { AlertTriangle, BarChart3, BookOpen, ClipboardCheck, Database, FileText, FolderKanban, History, Layers3, Search, Settings, ShieldCheck, UploadCloud } from 'lucide-react';

const items = [
  { to: '/', label: 'Dashboard', icon: BarChart3, key: 'D' },
  { to: '/projects', label: 'Projects', icon: FolderKanban, key: 'P' },
  { to: '/upload', label: 'Documents', icon: UploadCloud, key: 'U' },
  { to: '/verification', label: 'Verification Runs', icon: ClipboardCheck, key: 'V' },
  { to: '/anomalies', label: 'Anomalies', icon: AlertTriangle, key: 'A' },
  { to: '/reports', label: 'Reports', icon: FileText, key: 'R' },
  { to: '/rules', label: 'Rule Engine', icon: BookOpen, key: 'E' },
  { to: '/evidence', label: 'Evidence', icon: Search, key: 'F' },
  { to: '/history', label: 'Verification History', icon: History, key: 'H' },
  { to: '/confidence', label: 'Confidence', icon: ShieldCheck, key: 'C' },
  { to: '/settings', label: 'Settings', icon: Settings, key: 'S' },
];

export function Sidebar() {
  return <aside className="fixed inset-y-0 left-0 z-30 flex w-[264px] flex-col border-r border-slate-200 bg-white">
    <div className="border-b border-slate-200 px-5 py-4">
      <div className="flex items-center gap-3"><div className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-950 text-white"><Layers3 size={18} /></div><div><div className="text-sm font-semibold tracking-tight text-slate-950">FinVerify</div><div className="text-xs text-slate-500">Financial verification engine</div></div></div>
    </div>
    <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4" aria-label="Primary navigation">
      {items.map((item) => { const Icon = item.icon; return <NavLink key={item.to} to={item.to} className={({ isActive }) => 'group flex items-center justify-between rounded-md px-3 py-2 text-sm transition ' + (isActive ? 'bg-slate-950 text-white shadow-sm' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-950')}><span className="flex min-w-0 items-center gap-3"><Icon size={16} /><span className="truncate">{item.label}</span></span><kbd className="rounded border border-current/20 px-1.5 py-0.5 text-[10px] opacity-60">{item.key}</kbd></NavLink>; })}
    </nav>
    <div className="border-t border-slate-200 p-4"><div className="rounded-lg border border-slate-200 bg-slate-50 p-3"><div className="flex items-center gap-2 text-xs font-medium text-slate-700"><Database size={14} /> Local Storage</div><div className="mt-2 h-1.5 rounded-full bg-slate-200"><div className="h-full w-2/3 rounded-full bg-emerald-500" /></div><div className="mt-2 text-[11px] text-slate-500">Canonical JSON and reports ready</div></div></div>
  </aside>;
}
