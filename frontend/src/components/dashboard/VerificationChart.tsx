import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { VerificationSummary } from '../../types/api';

export function VerificationChart({ summary }: { summary?: VerificationSummary | null }) {
  const data = [
    { name: 'OK', value: summary?.ok_count ?? 0 },
    { name: 'Mismatch', value: summary?.mismatch_count ?? 0 },
    { name: 'Missing', value: summary?.missing_count ?? 0 },
  ];
  return <div className="h-72 rounded-lg border border-audit-line bg-white p-4"><ResponsiveContainer width="100%" height="100%"><BarChart data={data}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" /><YAxis allowDecimals={false} /><Tooltip /><Bar dataKey="value" fill="#0f766e" /></BarChart></ResponsiveContainer></div>;
}
