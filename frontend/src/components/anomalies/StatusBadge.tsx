export function StatusBadge({ status }: { status: string }) {
  const cls = status === 'OK' ? 'bg-emerald-100 text-emerald-700' : status.includes('MISSING') ? 'bg-orange-100 text-orange-700' : 'bg-red-100 text-red-700';
  return <span className={'rounded px-2 py-1 text-xs font-medium ' + cls}>{status}</span>;
}
