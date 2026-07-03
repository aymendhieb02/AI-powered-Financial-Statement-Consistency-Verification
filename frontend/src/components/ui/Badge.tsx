import type { ReactNode } from 'react';

const tones: Record<string, string> = {
  neutral: 'border-slate-200 bg-slate-50 text-slate-700',
  success: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  warning: 'border-amber-200 bg-amber-50 text-amber-800',
  danger: 'border-red-200 bg-red-50 text-red-700',
  info: 'border-blue-200 bg-blue-50 text-blue-700',
  dark: 'border-slate-300 bg-slate-900 text-white',
};

export function Badge({ children, tone = 'neutral' }: { children: ReactNode; tone?: keyof typeof tones }) {
  return <span className={'inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium ' + tones[tone]}>{children}</span>;
}

export function SeverityBadge({ severity }: { severity?: string }) {
  const tone = severity === 'CRITICAL' ? 'danger' : severity === 'MEDIUM' ? 'warning' : severity === 'LOW' ? 'info' : 'neutral';
  return <Badge tone={tone}>{severity || 'NONE'}</Badge>;
}

export function StatusBadge({ status }: { status?: string }) {
  const tone = status === 'OK' || status === 'completed' ? 'success' : status?.includes('MISSING') || status === 'failed' ? 'danger' : status?.includes('MISMATCH') ? 'warning' : 'neutral';
  return <Badge tone={tone}>{status || 'PENDING'}</Badge>;
}
