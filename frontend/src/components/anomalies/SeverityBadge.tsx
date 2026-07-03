export function SeverityBadge({ severity }: { severity: string }) {
  const cls = severity === 'CRITICAL' ? 'bg-red-100 text-red-700' : severity === 'MEDIUM' ? 'bg-amber-100 text-amber-700' : 'bg-slate-100 text-slate-700';
  return <span className={'rounded px-2 py-1 text-xs font-medium ' + cls}>{severity}</span>;
}
