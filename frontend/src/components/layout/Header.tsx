import { Bell, Menu, Moon, Search, Server, Sparkles, UserCircle2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { api } from '../../api/client';
import type { Health } from '../../types/api';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { useLayout } from './LayoutContext';

export function Header() {
  const [health, setHealth] = useState<Health | null>(null);
  const { setMobileNavOpen } = useLayout();

  useEffect(() => {
    api.get<Health>('/health').then(({ data }) => setHealth(data)).catch(() => setHealth(null));
  }, []);

  return (
    <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 backdrop-blur">
      <div className="flex h-16 items-center gap-3 px-4 sm:gap-4 sm:px-6">
        <Button variant="ghost" size="sm" className="h-9 w-9 p-0 lg:hidden" onClick={() => setMobileNavOpen(true)} aria-label="Open navigation">
          <Menu size={18} />
        </Button>
        <div className="relative max-w-xl flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
          <Input className="w-full pl-9" aria-label="Global search" placeholder="Search projects, statements, labels, rules, runs, reports..." />
        </div>
        <Select defaultValue="maxula">
          <SelectTrigger className="hidden w-56 sm:inline-flex" aria-label="Project selector">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="maxula">MAXULA SICAV workspace</SelectItem>
            <SelectItem value="all">All projects</SelectItem>
          </SelectContent>
        </Select>
        <div className="hidden items-center gap-2 xl:flex">
          <Badge tone={health?.status === 'ok' ? 'success' : 'warning'}>
            <Server size={12} /> Backend {health?.status || 'offline'}
          </Badge>
          <Badge tone="success">Storage local</Badge>
          <Badge tone="neutral">
            <Sparkles size={12} /> AI standby
          </Badge>
        </div>
        <Button variant="secondary" size="sm" className="h-9 w-9 p-0" aria-label="Notifications">
          <Bell size={16} />
        </Button>
        <Button variant="secondary" size="sm" className="hidden h-9 w-9 p-0 sm:inline-flex" aria-label="Theme switch">
          <Moon size={16} />
        </Button>
        <div className="hidden items-center gap-2 rounded-md border border-slate-200 px-2 py-1.5 sm:flex">
          <UserCircle2 size={18} className="text-slate-500" />
          <span className="text-sm font-medium text-slate-700">Auditor</span>
        </div>
      </div>
    </header>
  );
}
