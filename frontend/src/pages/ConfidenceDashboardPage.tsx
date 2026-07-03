import { RadialBar, RadialBarChart, ResponsiveContainer } from 'recharts';
import { PageHeader, StatCard } from '../components/ui/Cards';
import { RiskScoreCard } from '../components/ui/Enterprise';

const scores = [{ name: 'Extraction', value: 99, fill: '#059669' }, { name: 'Normalization', value: 98, fill: '#2563eb' }, { name: 'Comparison', value: 100, fill: '#111827' }, { name: 'Rules', value: 97, fill: '#d97706' }];
export function ConfidenceDashboardPage() {
  return <section className="space-y-6"><PageHeader eyebrow="Confidence" title="Verification confidence" description="Confidence is aggregated from extraction quality, label matching, deterministic comparisons, and rule execution." />
    <div className="grid gap-4 md:grid-cols-4">{scores.map((s) => <StatCard key={s.name} label={s.name} value={s.value + '%'} detail="Stage contribution" />)}</div>
    <div className="grid gap-4 xl:grid-cols-[1.2fr_1fr]"><div className="panel p-5"><div className="section-title mb-4">Stage confidence</div><div className="h-80"><ResponsiveContainer><RadialBarChart innerRadius="20%" outerRadius="95%" data={scores} startAngle={180} endAngle={-180}><RadialBar dataKey="value" background /></RadialBarChart></ResponsiveContainer></div></div><RiskScoreCard score={18} /></div>
  </section>;
}
