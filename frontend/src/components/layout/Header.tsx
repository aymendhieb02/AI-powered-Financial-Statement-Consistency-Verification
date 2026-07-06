import { Bell, Menu, Server, UserCircle2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { api } from '../../api/client';
import type { Health } from '../../types/api';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/button';
import { useLayout } from './LayoutContext';

export function Header() {
  const [health, setHealth] = useState<Health | null>(null);
  const { setMobileNavOpen } = useLayout();

  useEffect(() => {
    api.get<Health>('/health').then(({ data }) => setHealth(data)).catch(() => setHealth(null));
  }, []);

  return (
    <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 backdrop-blur">
      <div className="flex h-16 items-center justify-between gap-3 px-4 sm:px-6">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" className="h-9 w-9 p-0 lg:hidden" onClick={() => setMobileNavOpen(true)} aria-label="Open navigation"><Menu size={18} /></Button>
          <div><div className="text-sm font-semibold text-slate-950">SICAV carry-forward comparison</div><div className="text-xs text-slate-500">Upload old report, upload new report, compare.</div></div>
        </div>
        <div className="flex items-center gap-2">
          <Badge tone={health?.status === 'ok' ? 'success' : 'warning'}><Server size={12} /> Backend {health?.status || 'offline'}</Badge>
          <Button variant="secondary" size="sm" className="hidden h-9 w-9 p-0 sm:inline-flex" disabled title="Coming soon" aria-label="Notifications"><Bell size={16} /></Button>
          <div className="hidden items-center gap-2 rounded-md border border-slate-200 px-2 py-1.5 sm:flex"><UserCircle2 size={18} className="text-slate-500" /><span className="text-sm font-medium text-slate-700">Accountant</span></div>
        </div>
      </div>
    </header>
  );
}
