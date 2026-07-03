import type { ReactNode } from 'react';
import { ArrowUpRight, Minus } from 'lucide-react';
import { Card } from './card';

export function PageHeader({ title, eyebrow, description, actions }: { title: string; eyebrow?: string; description?: string; actions?: ReactNode }) {
  return <div className="flex flex-col gap-4 border-b border-slate-200 pb-5 lg:flex-row lg:items-end lg:justify-between">
    <div className="space-y-1">{eyebrow && <div className="section-title">{eyebrow}</div>}<h1 className="text-2xl font-semibold tracking-tight text-slate-950">{title}</h1>{description && <p className="max-w-3xl text-sm leading-6 text-slate-500">{description}</p>}</div>
    {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
  </div>;
}
export function StatCard({ label, value, detail, icon, tone = 'slate', trend }: { label: string; value: ReactNode; detail?: string; icon?: ReactNode; tone?: 'slate' | 'blue' | 'emerald' | 'amber' | 'red'; trend?: string }) {
  const accents = { slate: 'bg-slate-100 text-slate-700', blue: 'bg-blue-50 text-blue-700', emerald: 'bg-emerald-50 text-emerald-700', amber: 'bg-amber-50 text-amber-800', red: 'bg-red-50 text-red-700' };
  return <Card className="p-4"><div className="flex items-start justify-between gap-3"><div className="space-y-2"><div className="metric-label">{label}</div><div className="metric-value">{value}</div></div>{icon && <div className={'rounded-md p-2 ' + accents[tone]}>{icon}</div>}</div><div className="mt-3 flex items-center gap-2 text-xs text-slate-500">{trend ? <ArrowUpRight size={13} className="text-emerald-600" /> : <Minus size={13} />}<span>{trend || detail || 'No change recorded'}</span></div></Card>;
}
export function EmptyState({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return <Card className="flex min-h-44 flex-col items-center justify-center gap-3 p-8 text-center"><div className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-500">No data</div><div><h3 className="text-sm font-semibold text-slate-950">{title}</h3><p className="mt-1 max-w-md text-sm text-slate-500">{description}</p></div>{action}</Card>;
}
export function ProgressBar({ value }: { value: number }) { const safe = Math.max(0, Math.min(100, value)); return <div className="h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-slate-900 transition-all" style={{ width: safe + '%' }} /></div>; }
