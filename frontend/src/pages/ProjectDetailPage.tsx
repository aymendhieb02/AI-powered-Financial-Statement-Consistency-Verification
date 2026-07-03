import { FileText, GitCompareArrows, History, ShieldCheck, UploadCloud } from 'lucide-react';
import { PageHeader, StatCard } from '../components/ui/Cards';
import { PipelineProgress, ReportCard } from '../components/ui/Enterprise';
import { StatusBadge } from '../components/ui/Badge';

const tabs = ['Overview', 'Documents', 'Extraction', 'Validation', 'Comparison', 'Evidence', 'Reports', 'History'];
export function ProjectDetailPage() {
  return <section className="space-y-6"><PageHeader eyebrow="Workspace" title="MAXULA annual verification" description="Repository-style workspace for canonical documents, validation evidence, comparison results, and reports." actions={<button className="btn-primary"><UploadCloud size={15} /> Upload PDFs</button>} />
    <div className="flex gap-1 overflow-x-auto border-b border-slate-200">{tabs.map((tab, i) => <button key={tab} className={'px-3 py-2 text-sm font-medium ' + (i === 0 ? 'border-b-2 border-slate-950 text-slate-950' : 'text-slate-500 hover:text-slate-900')}>{tab}</button>)}</div>
    <div className="grid gap-4 md:grid-cols-4"><StatCard label="Documents" value="4" icon={<FileText size={18} />} /><StatCard label="Fields compared" value="1,284" icon={<GitCompareArrows size={18} />} tone="blue" /><StatCard label="Confidence" value="98.4%" icon={<ShieldCheck size={18} />} tone="emerald" /><StatCard label="Runs" value="12" icon={<History size={18} />} /></div>
    <PipelineProgress />
    <div className="grid gap-4 xl:grid-cols-[1.4fr_1fr]"><div className="panel overflow-hidden"><div className="border-b border-slate-200 p-4"><div className="section-title">Latest comparisons</div></div><table className="data-table"><thead><tr><th>Statement</th><th>Canonical account</th><th>Status</th><th>Confidence</th></tr></thead><tbody>{['total_actif','actif_net','total_passif','resultat_exercice'].map((label, i) => <tr key={label}><td>Balance Sheet</td><td>{label}</td><td><StatusBadge status={i === 1 ? 'MISMATCH' : 'OK'} /></td><td>{98 - i}%</td></tr>)}</tbody></table></div><div className="space-y-3"><ReportCard title="Excel workbook" meta="Created for latest verification run" action={<button className="btn-secondary">Download</button>} /><ReportCard title="Evidence trace" meta="Line-level extraction provenance" action={<button className="btn-secondary">Review</button>} /></div></div>
  </section>;
}
