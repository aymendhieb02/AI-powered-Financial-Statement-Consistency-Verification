import { Bell, Moon, Search, Server, Sparkles, UserCircle2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { api } from '../../api/client';
import type { Health } from '../../types/api';
import { Badge } from '../ui/Badge';

export function Header() {
  const [health, setHealth] = useState<Health | null>(null);
  useEffect(() => { api.get<Health>('/health').then(({ data }) => setHealth(data)).catch(() => setHealth(null)); }, []);
  return <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 backdrop-blur">
    <div className="flex h-16 items-center gap-4 px-6">
      <div className="relative max-w-xl flex-1"><Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} /><input className="input-control w-full pl-9" aria-label="Global search" placeholder="Search projects, statements, labels, rules, runs, reports..." /></div>
      <select className="input-control w-56" aria-label="Project selector"><option>MAXULA SICAV workspace</option><option>All projects</option></select>
      <div className="hidden items-center gap-2 xl:flex"><Badge tone={health?.status === 'ok' ? 'success' : 'warning'}><Server size={12} /> Backend {health?.status || 'offline'}</Badge><Badge tone="success">Storage local</Badge><Badge tone="neutral"><Sparkles size={12} /> AI standby</Badge></div>
      <button className="btn-secondary" aria-label="Notifications"><Bell size={16} /></button><button className="btn-secondary" aria-label="Theme switch"><Moon size={16} /></button>
      <div className="flex items-center gap-2 rounded-md border border-slate-200 px-2 py-1.5"><UserCircle2 size={18} className="text-slate-500" /><span className="text-sm font-medium text-slate-700">Auditor</span></div>
    </div>
  </header>;
}
