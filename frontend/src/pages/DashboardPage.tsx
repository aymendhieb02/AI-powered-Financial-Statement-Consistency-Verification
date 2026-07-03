import { useEffect, useState } from 'react';
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { AlertTriangle, BarChart3, CheckCircle2, FileText, FolderKanban, ShieldCheck } from 'lucide-react';
import { listProjects } from '../api/projects';
import { PageHeader, StatCard } from '../components/ui/Cards';
import { ActivityList, ReportCard, RiskScoreCard } from '../components/ui/Enterprise';

const history = [{ m: 'Jan', confidence: 98, risk: 18 }, { m: 'Feb', confidence: 97, risk: 22 }, { m: 'Mar', confidence: 99, risk: 12 }, { m: 'Apr', confidence: 96, risk: 28 }, { m: 'May', confidence: 99, risk: 10 }, { m: 'Jun', confidence: 98, risk: 14 }];
const severity = [{ name: 'Critical', value: 2, color: '#dc2626' }, { name: 'Medium', value: 7, color: '#d97706' }, { name: 'Low', value: 13, color: '#2563eb' }];
const coverage = [{ name: 'Balance sheet', values: 94 }, { name: 'Income', values: 88 }, { name: 'Net assets', values: 91 }, { name: 'Notes', values: 72 }];

export function DashboardPage() {
  const [count, setCount] = useState(0);
  useEffect(() => { listProjects().then((projects) => setCount(projects.length)).catch(() => undefined); }, []);
  return <section className="space-y-6">
    <PageHeader eyebrow="Command center" title="Financial verification dashboard" description="A dense operational view for accountants reviewing annual SICAV carry-forward consistency, evidence quality, and verification risk." />
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4"><StatCard label="Projects" value={count} detail="Active verification workspaces" icon={<FolderKanban size={18} />} /><StatCard label="Documents" value="18" detail="Annual PDFs indexed" icon={<FileText size={18} />} tone="blue" /><StatCard label="Critical anomalies" value="2" detail="Require accountant review" icon={<AlertTriangle size={18} />} tone="red" /><StatCard label="Overall confidence" value="98.4%" trend="+1.2% vs last run" icon={<ShieldCheck size={18} />} tone="emerald" /></div>
    <div className="grid gap-4 xl:grid-cols-[1.7fr_1fr]"><div className="panel p-5"><div className="mb-4 flex items-center justify-between"><div><div className="section-title">Verification history</div><h2 className="text-sm font-semibold text-slate-950">Confidence and risk evolution</h2></div><BarChart3 size={18} className="text-slate-400" /></div><div className="h-72"><ResponsiveContainer><AreaChart data={history}><CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" /><XAxis dataKey="m" fontSize={12} /><YAxis fontSize={12} /><Tooltip /><Area type="monotone" dataKey="confidence" stroke="#059669" fill="#d1fae5" /><Area type="monotone" dataKey="risk" stroke="#dc2626" fill="#fee2e2" /></AreaChart></ResponsiveContainer></div></div><div className="space-y-4"><RiskScoreCard score={18} /><div className="panel p-5"><div className="section-title mb-3">Anomalies by severity</div><div className="h-44"><ResponsiveContainer><PieChart><Pie data={severity} dataKey="value" innerRadius={42} outerRadius={72}>{severity.map((s) => <Cell key={s.name} fill={s.color} />)}</Pie><Tooltip /></PieChart></ResponsiveContainer></div></div></div></div>
    <div className="grid gap-4 xl:grid-cols-3"><div className="panel p-5 xl:col-span-2"><div className="section-title mb-4">Comparison coverage</div><div className="h-56"><ResponsiveContainer><BarChart data={coverage}><CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" /><XAxis dataKey="name" fontSize={12} /><YAxis fontSize={12} /><Tooltip /><Bar dataKey="values" fill="#2563eb" radius={[4,4,0,0]} /></BarChart></ResponsiveContainer></div></div><ActivityList items={[{ title: 'MAXULA 2024 verification completed', meta: '2 critical anomalies, confidence 98.4%' }, { title: 'Rule BS001 executed', meta: 'Total assets equality passed' }, { title: 'Excel report generated', meta: 'Available in reports workspace' }]} /></div>
    <div className="grid gap-4 md:grid-cols-2"><ReportCard title="Latest Excel audit workbook" meta="Rule results, evidence trace, confidence summary" action={<button className="btn-secondary">Open</button>} /><ReportCard title="Latest JSON verification payload" meta="Machine-readable comparison report" action={<button className="btn-secondary">Open</button>} /></div>
  </section>;
}
