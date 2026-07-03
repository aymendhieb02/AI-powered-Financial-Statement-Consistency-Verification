import { NavLink } from 'react-router-dom';
import { AlertTriangle, BarChart3, FileText, FolderKanban, Settings, UploadCloud } from 'lucide-react';

const items = [
  { to: '/', label: 'Dashboard', icon: BarChart3 },
  { to: '/projects', label: 'Projects', icon: FolderKanban },
  { to: '/upload', label: 'Upload', icon: UploadCloud },
  { to: '/verification', label: 'Verification', icon: FileText },
  { to: '/anomalies', label: 'Anomalies', icon: AlertTriangle },
  { to: '/reports', label: 'Reports', icon: FileText },
  { to: '/settings', label: 'Settings', icon: Settings },
];

export function Sidebar() {
  return <aside className="w-64 border-r border-audit-line bg-white px-4 py-5">
    <div className="mb-8">
      <div className="text-xl font-semibold text-audit-ink">FinVerify</div>
      <div className="text-sm text-audit-muted">SICAV verification</div>
    </div>
    <nav className="space-y-1">
      {items.map((item) => {
        const Icon = item.icon;
        return <NavLink key={item.to} to={item.to} className={({ isActive }) => 'flex items-center gap-3 rounded-md px-3 py-2 text-sm ' + (isActive ? 'bg-audit-accent text-white' : 'text-audit-ink hover:bg-audit-panel')}>
          <Icon size={17} />
          {item.label}
        </NavLink>;
      })}
    </nav>
  </aside>;
}
